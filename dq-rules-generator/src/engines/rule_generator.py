"""
Rule Generator
==============

Main engine that orchestrates rule generation.

Combines:
- Business Context Analyzer
- Relationship Inference Engine
- Rule Template Engine
- SQL Generator

To produce comprehensive DQ and Business Rules.
"""

from typing import List, Dict, Optional, Set
from datetime import datetime
from loguru import logger

from ..models.table_model import TableModel, ColumnModel, TableType, DataSensitivity
from ..models.rule_model import DQRule, Dimension, RuleType, Severity
from ..models.relationship_model import TableRelationship, RelationshipInferenceResult

from ..analyzers.business_context_analyzer import BusinessContextAnalyzer
from ..analyzers.relationship_inference_engine import RelationshipInferenceEngine
from .rule_template_engine import RuleTemplateEngine
from .sql_generator import SQLGenerator


class RuleGenerator:
    """
    Main rule generation engine.
    
    Generates rules in phases:
    1. Completeness rules (mandatory for all columns)
    2. Validity rules (based on data type and semantics)
    3. Uniqueness rules (for keys and identifiers)
    4. Consistency rules (cross-table validation)
    5. Timeliness rules (for date fields)
    6. Accuracy rules (business logic validation)
    """
    
    def __init__(
        self,
        system_name: str = "",
        database_name: str = "",
        timeliness_threshold_days: int = 30,
        critical_fields: Optional[List[str]] = None
    ):
        """
        Initialize the rule generator.
        
        Args:
            system_name: Source system name
            database_name: Database name
            timeliness_threshold_days: Days threshold for timeliness checks
            critical_fields: List of field names that are business-critical
        """
        self.system_name = system_name
        self.database_name = database_name
        self.timeliness_threshold = timeliness_threshold_days
        self.critical_fields = set(f.lower() for f in (critical_fields or []))
        
        # Initialize components
        self.context_analyzer = BusinessContextAnalyzer()
        self.relationship_engine = RelationshipInferenceEngine()
        self.template_engine = RuleTemplateEngine()
        self.sql_generator = SQLGenerator(database=database_name)
        
        # Track generated rules to avoid duplicates
        self._generated_rules: Set[str] = set()
    
    def generate(self, tables: List[TableModel]) -> List[DQRule]:
        """
        Generate all DQ and Business Rules for the given tables.
        
        Args:
            tables: List of TableModel objects
            
        Returns:
            List of DQRule objects
        """
        logger.info(f"Starting rule generation for {len(tables)} tables")
        
        # Phase 0: Analyze business context
        logger.info("Phase 0: Analyzing business context...")
        tables = self.context_analyzer.analyze(tables)
        
        # Phase 0.5: Infer relationships
        logger.info("Phase 0.5: Inferring table relationships...")
        relationships = self.relationship_engine.infer_relationships(tables)
        
        rules: List[DQRule] = []
        self._generated_rules.clear()
        
        # Process each table
        for table in tables:
            logger.debug(f"Processing table: {table.full_name}")
            
            # Phase 1: Completeness rules
            rules.extend(self._generate_completeness_rules(table))
            
            # Phase 2: Validity rules
            rules.extend(self._generate_validity_rules(table))
            
            # Phase 3: Uniqueness rules
            rules.extend(self._generate_uniqueness_rules(table))
            
            # Phase 4: Timeliness rules
            rules.extend(self._generate_timeliness_rules(table))
            
            # Phase 5: Accuracy rules
            rules.extend(self._generate_accuracy_rules(table))
        
        # Phase 6: Consistency rules (cross-table)
        rules.extend(self._generate_consistency_rules(tables, relationships))
        
        # Validate and assign severity
        valid_rules = []
        for rule in rules:
            rule.severity = self._calculate_severity(rule, tables)
            if rule.validate():
                valid_rules.append(rule)
            else:
                logger.warning(f"Invalid rule: {rule.validation_errors}")
        
        logger.info(f"Generated {len(valid_rules)} valid rules")
        return valid_rules
    
    def _rule_key(self, table: str, column: str, dimension: str, check_type: str) -> str:
        """Generate unique key for deduplication"""
        return f"{table}|{column}|{dimension}|{check_type}"
    
    def _add_rule_if_unique(self, rule: DQRule, check_type: str) -> bool:
        """Add rule only if not duplicate"""
        key = self._rule_key(rule.table, rule.column, rule.dimension.value, check_type)
        if key in self._generated_rules:
            return False
        self._generated_rules.add(key)
        return True
    
    # ==========================================================================
    # Phase 1: Completeness Rules
    # ==========================================================================
    
    def _generate_completeness_rules(self, table: TableModel) -> List[DQRule]:
        """Generate completeness rules for all columns"""
        rules = []
        
        for column in table.columns:
            # Skip nullable columns that are truly optional
            # But still generate rules to track completeness
            
            # Get Arabic content
            content = self.template_engine.generate_content(
                Dimension.COMPLETENESS,
                'null_check',
                table,
                column
            )
            
            # Generate SQL
            sql = self.sql_generator.completeness_check(table, column)
            
            rule = DQRule(
                system=self.system_name,
                database=self.database_name,
                schema=table.schema_name,
                table=table.table_name,
                column=column.name,
                dimension=Dimension.COMPLETENESS,
                rule_type=RuleType.DATA_QUALITY,
                rule_description=content.rule_description,
                issue_description=content.issue_description,
                root_cause=content.root_cause,
                recommendation=content.recommendation,
                workflows=content.workflows,
                sql_script=sql
            )
            
            if self._add_rule_if_unique(rule, 'completeness'):
                rules.append(rule)
        
        return rules
    
    # ==========================================================================
    # Phase 2: Validity Rules
    # ==========================================================================
    
    def _generate_validity_rules(self, table: TableModel) -> List[DQRule]:
        """Generate validity rules based on data types and semantics"""
        rules = []
        
        for column in table.columns:
            col_name_lower = column.name.lower()
            desc_lower = (column.description or '').lower()
            combined = f"{col_name_lower} {desc_lower}"
            
            # Email validation
            if 'email' in combined or 'بريد' in combined:
                rules.extend(self._create_email_rules(table, column))
            
            # Phone validation
            elif any(kw in combined for kw in ['phone', 'mobile', 'tel', 'fax', 'هاتف', 'جوال']):
                rules.extend(self._create_phone_rules(table, column))
            
            # National ID validation
            elif any(kw in combined for kw in ['national_id', 'citizen_id', 'iqama', 'هوية']):
                rules.extend(self._create_national_id_rules(table, column))
            
            # Date validation
            elif column.is_date_field or column.get_normalized_type() == 'DATETIME':
                rules.extend(self._create_date_rules(table, column))
            
            # Amount validation
            elif column.is_amount_field:
                rules.extend(self._create_amount_rules(table, column))
            
            # Status/Type validation
            elif column.is_status_field:
                rules.extend(self._create_status_rules(table, column))
            
            # String length validation
            elif column.get_normalized_type() == 'STRING' and column.max_length:
                rules.extend(self._create_length_rules(table, column))
        
        return rules
    
    def _create_email_rules(self, table: TableModel, column: ColumnModel) -> List[DQRule]:
        """Create email validation rules"""
        content = self.template_engine.generate_content(
            Dimension.VALIDITY, 'email', table, column
        )
        sql = self.sql_generator.email_format_check(table, column)
        
        return [DQRule(
            system=self.system_name,
            database=self.database_name,
            schema=table.schema_name,
            table=table.table_name,
            column=column.name,
            dimension=Dimension.VALIDITY,
            rule_type=RuleType.DATA_QUALITY,
            rule_description=content.rule_description,
            issue_description=content.issue_description,
            root_cause=content.root_cause,
            recommendation=content.recommendation,
            workflows=content.workflows,
            sql_script=sql
        )]
    
    def _create_phone_rules(self, table: TableModel, column: ColumnModel) -> List[DQRule]:
        """Create phone validation rules"""
        content = self.template_engine.generate_content(
            Dimension.VALIDITY, 'phone', table, column
        )
        sql = self.sql_generator.phone_format_check(table, column)
        
        return [DQRule(
            system=self.system_name,
            database=self.database_name,
            schema=table.schema_name,
            table=table.table_name,
            column=column.name,
            dimension=Dimension.VALIDITY,
            rule_type=RuleType.DATA_QUALITY,
            rule_description=content.rule_description,
            issue_description=content.issue_description,
            root_cause=content.root_cause,
            recommendation=content.recommendation,
            workflows=content.workflows,
            sql_script=sql
        )]
    
    def _create_national_id_rules(self, table: TableModel, column: ColumnModel) -> List[DQRule]:
        """Create Saudi National ID validation rules"""
        content = self.template_engine.generate_content(
            Dimension.VALIDITY, 'national_id', table, column
        )
        sql = self.sql_generator.national_id_check(table, column)
        
        return [DQRule(
            system=self.system_name,
            database=self.database_name,
            schema=table.schema_name,
            table=table.table_name,
            column=column.name,
            dimension=Dimension.VALIDITY,
            rule_type=RuleType.DATA_QUALITY,
            rule_description=content.rule_description,
            issue_description=content.issue_description,
            root_cause=content.root_cause,
            recommendation=content.recommendation,
            workflows=content.workflows,
            sql_script=sql
        )]
    
    def _create_date_rules(self, table: TableModel, column: ColumnModel) -> List[DQRule]:
        """Create date validation rules"""
        rules = []
        col_name_lower = column.name.lower()
        
        # Check for historical dates that shouldn't be in future
        historical_keywords = ['birth', 'created', 'registered', 'start', 'begin', 'ميلاد', 'إنشاء', 'تسجيل']
        if any(kw in col_name_lower for kw in historical_keywords):
            content = self.template_engine.generate_content(
                Dimension.VALIDITY, 'date', table, column
            )
            sql = self.sql_generator.future_date_check(table, column)
            
            rules.append(DQRule(
                system=self.system_name,
                database=self.database_name,
                schema=table.schema_name,
                table=table.table_name,
                column=column.name,
                dimension=Dimension.VALIDITY,
                rule_type=RuleType.DATA_QUALITY,
                rule_description=content.rule_description,
                issue_description=content.issue_description,
                root_cause=content.root_cause,
                recommendation=content.recommendation,
                workflows=content.workflows,
                sql_script=sql
            ))
        
        return rules
    
    def _create_amount_rules(self, table: TableModel, column: ColumnModel) -> List[DQRule]:
        """Create amount validation rules"""
        content = self.template_engine.generate_content(
            Dimension.VALIDITY, 'amount', table, column
        )
        sql = self.sql_generator.amount_range_check(table, column, min_value=0)
        
        return [DQRule(
            system=self.system_name,
            database=self.database_name,
            schema=table.schema_name,
            table=table.table_name,
            column=column.name,
            dimension=Dimension.VALIDITY,
            rule_type=RuleType.DATA_QUALITY,
            rule_description=content.rule_description,
            issue_description=content.issue_description,
            root_cause=content.root_cause,
            recommendation=content.recommendation,
            workflows=content.workflows,
            sql_script=sql
        )]
    
    def _create_status_rules(self, table: TableModel, column: ColumnModel) -> List[DQRule]:
        """Create status field validation rules"""
        content = self.template_engine.generate_content(
            Dimension.VALIDITY, 'status', table, column
        )
        
        # Note: In real implementation, allowed values would come from lookup tables
        # Here we generate a template SQL that can be customized
        sql = f"""-- التحقق من صحة الحالة في {column.name}
-- ملاحظة: يجب تحديد القيم المسموحة من جدول الحالات المرجعي
SELECT 
    [{column.name}],
    *
FROM [{table.schema_name}].[{table.table_name}]
WHERE [{column.name}] IS NOT NULL
  AND [{column.name}] NOT IN (
    SELECT StatusCode FROM StatusLookup 
    WHERE EntityType = '{table.table_name}'
  )"""
        
        return [DQRule(
            system=self.system_name,
            database=self.database_name,
            schema=table.schema_name,
            table=table.table_name,
            column=column.name,
            dimension=Dimension.VALIDITY,
            rule_type=RuleType.BUSINESS_RULE,
            rule_description=content.rule_description,
            issue_description=content.issue_description,
            root_cause=content.root_cause,
            recommendation=content.recommendation,
            workflows=content.workflows,
            sql_script=sql
        )]
    
    def _create_length_rules(self, table: TableModel, column: ColumnModel) -> List[DQRule]:
        """Create string length validation rules"""
        if not column.max_length or column.max_length > 1000:
            return []  # Skip very large text fields
        
        content = self.template_engine.generate_content(
            Dimension.VALIDITY, 'default', table, column,
            max_length=column.max_length
        )
        sql = self.sql_generator.length_check(table, column, max_length=column.max_length)
        
        return [DQRule(
            system=self.system_name,
            database=self.database_name,
            schema=table.schema_name,
            table=table.table_name,
            column=column.name,
            dimension=Dimension.VALIDITY,
            rule_type=RuleType.DATA_QUALITY,
            rule_description=content.rule_description,
            issue_description=content.issue_description,
            root_cause=content.root_cause,
            recommendation=content.recommendation,
            workflows=content.workflows,
            sql_script=sql
        )]
    
    # ==========================================================================
    # Phase 3: Uniqueness Rules
    # ==========================================================================
    
    def _generate_uniqueness_rules(self, table: TableModel) -> List[DQRule]:
        """Generate uniqueness rules for keys and identifiers"""
        rules = []
        
        for column in table.columns:
            if column.is_primary_key or column.is_unique or column.is_identifier:
                content = self.template_engine.generate_content(
                    Dimension.UNIQUENESS, 'uniqueness', table, column
                )
                sql = self.sql_generator.uniqueness_check(table, column)
                
                rule = DQRule(
                    system=self.system_name,
                    database=self.database_name,
                    schema=table.schema_name,
                    table=table.table_name,
                    column=column.name,
                    dimension=Dimension.UNIQUENESS,
                    rule_type=RuleType.DATA_QUALITY,
                    rule_description=content.rule_description,
                    issue_description=content.issue_description,
                    root_cause=content.root_cause,
                    recommendation=content.recommendation,
                    workflows=content.workflows,
                    sql_script=sql
                )
                
                if self._add_rule_if_unique(rule, 'uniqueness'):
                    rules.append(rule)
        
        return rules
    
    # ==========================================================================
    # Phase 4: Timeliness Rules
    # ==========================================================================
    
    def _generate_timeliness_rules(self, table: TableModel) -> List[DQRule]:
        """Generate timeliness rules for date fields"""
        rules = []
        
        for column in table.columns:
            if not column.is_date_field and column.get_normalized_type() != 'DATETIME':
                continue
            
            col_name_lower = column.name.lower()
            
            # Expiry date check
            if any(kw in col_name_lower for kw in ['expir', 'valid_until', 'end_date', 'انتهاء']):
                content = self.template_engine.generate_content(
                    Dimension.TIMELINESS, 'expiry', table, column
                )
                sql = self.sql_generator.expiry_check(table, column)
                
                rule = DQRule(
                    system=self.system_name,
                    database=self.database_name,
                    schema=table.schema_name,
                    table=table.table_name,
                    column=column.name,
                    dimension=Dimension.TIMELINESS,
                    rule_type=RuleType.DATA_QUALITY,
                    rule_description=content.rule_description,
                    issue_description=content.issue_description,
                    root_cause=content.root_cause,
                    recommendation=content.recommendation,
                    workflows=content.workflows,
                    sql_script=sql
                )
                
                if self._add_rule_if_unique(rule, 'expiry'):
                    rules.append(rule)
            
            # Freshness check for update dates
            elif any(kw in col_name_lower for kw in ['modified', 'updated', 'last_', 'تحديث', 'تعديل']):
                content = self.template_engine.generate_content(
                    Dimension.TIMELINESS, 'freshness', table, column,
                    threshold=self.timeliness_threshold
                )
                sql = self.sql_generator.freshness_check(
                    table, column, threshold_days=self.timeliness_threshold
                )
                
                rule = DQRule(
                    system=self.system_name,
                    database=self.database_name,
                    schema=table.schema_name,
                    table=table.table_name,
                    column=column.name,
                    dimension=Dimension.TIMELINESS,
                    rule_type=RuleType.DATA_QUALITY,
                    rule_description=content.rule_description,
                    issue_description=content.issue_description,
                    root_cause=content.root_cause,
                    recommendation=content.recommendation,
                    workflows=content.workflows,
                    sql_script=sql
                )
                
                if self._add_rule_if_unique(rule, 'freshness'):
                    rules.append(rule)
        
        return rules
    
    # ==========================================================================
    # Phase 5: Accuracy Rules
    # ==========================================================================
    
    def _generate_accuracy_rules(self, table: TableModel) -> List[DQRule]:
        """Generate accuracy rules based on business logic"""
        rules = []
        
        # Look for date pairs that should be in sequence
        date_columns = table.get_date_columns()
        if len(date_columns) >= 2:
            # Find start/end date pairs
            start_cols = [c for c in date_columns 
                         if any(kw in c.name.lower() for kw in ['start', 'begin', 'from', 'بداية'])]
            end_cols = [c for c in date_columns 
                       if any(kw in c.name.lower() for kw in ['end', 'finish', 'to', 'until', 'نهاية', 'انتهاء'])]
            
            for start_col in start_cols:
                for end_col in end_cols:
                    content = self.template_engine.generate_content(
                        Dimension.ACCURACY, 'date_sequence', table, start_col,
                        column1=start_col.name, column2=end_col.name
                    )
                    sql = self.sql_generator.date_sequence_check(table, start_col, end_col)
                    
                    rule = DQRule(
                        system=self.system_name,
                        database=self.database_name,
                        schema=table.schema_name,
                        table=table.table_name,
                        column=f"{start_col.name}, {end_col.name}",
                        dimension=Dimension.ACCURACY,
                        rule_type=RuleType.BUSINESS_RULE,
                        rule_description=f"التحقق من أن {start_col.name} سابق لـ {end_col.name} زمنياً",
                        issue_description="وجود تسلسل زمني غير منطقي يدل على خطأ في البيانات",
                        root_cause=content.root_cause,
                        recommendation=content.recommendation,
                        workflows=content.workflows,
                        sql_script=sql
                    )
                    
                    if self._add_rule_if_unique(rule, 'date_sequence'):
                        rules.append(rule)
        
        return rules
    
    # ==========================================================================
    # Phase 6: Consistency Rules (Cross-Table)
    # ==========================================================================
    
    def _generate_consistency_rules(
        self,
        tables: List[TableModel],
        relationships: RelationshipInferenceResult
    ) -> List[DQRule]:
        """Generate consistency rules for cross-table validation"""
        rules = []
        table_dict = {t.full_name.lower(): t for t in tables}
        table_dict.update({t.table_name.lower(): t for t in tables})
        
        for rel in relationships.relationships:
            # Get source table
            source_table = table_dict.get(rel.source_table.lower())
            target_table = table_dict.get(rel.target_table.lower())
            
            if not source_table or not target_table:
                continue
            
            source_col = source_table.get_column(rel.source_column)
            if not source_col:
                continue
            
            # Generate referential integrity rule
            content = self.template_engine.generate_content(
                Dimension.CONSISTENCY, 'referential', source_table, source_col,
                ref_table=rel.target_table
            )
            sql = self.sql_generator.referential_integrity_check(rel)
            
            rule = DQRule(
                system=self.system_name,
                database=self.database_name,
                schema=source_table.schema_name,
                table=source_table.table_name,
                column=rel.source_column,
                dimension=Dimension.CONSISTENCY,
                rule_type=RuleType.BUSINESS_RULE,
                rule_description=rel.business_meaning or content.rule_description,
                issue_description=content.issue_description,
                root_cause=content.root_cause,
                recommendation=content.recommendation,
                workflows=content.workflows,
                sql_script=sql,
                related_tables=rel.target_table,
                related_columns=rel.target_column
            )
            
            key = f"consistency|{rel.source_table}|{rel.source_column}|{rel.target_table}"
            if key not in self._generated_rules:
                self._generated_rules.add(key)
                rules.append(rule)
        
        return rules
    
    # ==========================================================================
    # Severity Calculation
    # ==========================================================================
    
    def _calculate_severity(self, rule: DQRule, tables: List[TableModel]) -> Severity:
        """Calculate severity based on multiple factors"""
        score = 0
        
        # Find the table and column
        table = next((t for t in tables if t.table_name == rule.table), None)
        column = table.get_column(rule.column) if table else None
        
        # Factor 1: Data sensitivity (40%)
        if column and column.sensitivity == DataSensitivity.HIGH:
            score += 40
        elif column and column.sensitivity == DataSensitivity.CONFIDENTIAL:
            score += 45
        elif table and table.sensitivity == DataSensitivity.HIGH:
            score += 30
        
        # Factor 2: Key constraints (25%)
        if column:
            if column.is_primary_key:
                score += 25
            elif column.is_foreign_key:
                score += 20
            elif column.is_unique:
                score += 15
        
        # Factor 3: Dimension (15%)
        dimension_scores = {
            Dimension.ACCURACY: 15,
            Dimension.CONSISTENCY: 12,
            Dimension.COMPLETENESS: 10,
            Dimension.UNIQUENESS: 10,
            Dimension.VALIDITY: 8,
            Dimension.TIMELINESS: 5
        }
        score += dimension_scores.get(rule.dimension, 5)
        
        # Factor 4: Business context (10%)
        if column:
            if column.is_legal_field:
                score += 10
            elif column.is_decision_field:
                score += 8
            elif column.is_amount_field:
                score += 8
        
        # Factor 5: Critical field designation (10%)
        if rule.column.lower() in self.critical_fields:
            score += 10
        
        # Classify
        if score >= 55:
            return Severity.HIGH
        elif score >= 30:
            return Severity.MEDIUM
        else:
            return Severity.LOW
