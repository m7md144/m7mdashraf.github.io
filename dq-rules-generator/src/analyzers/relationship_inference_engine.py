"""
Relationship Inference Engine
=============================

Infers relationships between tables even without explicit Foreign Keys.

Uses multiple strategies:
1. Explicit FK definitions
2. Column name similarity (e.g., Person.PersonId <- Order.PersonId)
3. Data type + naming pattern matching
4. Description analysis
5. Common business patterns

This is critical for generating cross-table validation rules.
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from loguru import logger

try:
    from rapidfuzz import fuzz
    HAS_FUZZY = True
except ImportError:
    HAS_FUZZY = False
    logger.warning("rapidfuzz not installed - fuzzy matching disabled")

from ..models.table_model import TableModel, ColumnModel, TableType
from ..models.relationship_model import (
    TableRelationship, RelationshipType, RelationshipStrength,
    RelationshipInferenceResult
)


class RelationshipInferenceEngine:
    """
    Infers relationships between tables using multiple strategies.
    
    Strategy Priority:
    1. Explicit Foreign Keys (100% confidence)
    2. Exact column name match with ID pattern (90% confidence)
    3. Column name similarity (80% confidence)
    4. Type + pattern matching (70% confidence)
    5. Description-based inference (60% confidence)
    """
    
    # Common ID suffixes that indicate relationships
    ID_SUFFIXES = ['_id', 'id', '_key', '_code', '_no', '_number', '_ref']
    
    # Common prefixes for foreign key columns
    FK_PREFIXES = ['fk_', 'ref_', 'parent_']
    
    # Patterns that indicate master table reference
    MASTER_TABLE_PATTERNS = [
        r'^(country|city|region|status|type|category|department|currency)$',
        r'^(mst_|ref_|lkp_|lookup_)',
        r'_(type|status|code|category)$'
    ]
    
    # Business relationship patterns (Arabic descriptions)
    RELATIONSHIP_MEANINGS = {
        ('person', 'request'): 'ربط بيانات الشخص بالطلبات المقدمة منه',
        ('person', 'case'): 'ربط بيانات الشخص بالقضايا المرتبطة به',
        ('person', 'judgment'): 'ربط بيانات الشخص بالأحكام الصادرة',
        ('customer', 'order'): 'ربط بيانات العميل بالطلبات المقدمة',
        ('customer', 'invoice'): 'ربط بيانات العميل بالفواتير',
        ('employee', 'request'): 'ربط الموظف بالطلبات التي قام بها',
        ('order', 'item'): 'ربط الطلب ببنوده التفصيلية',
        ('order', 'payment'): 'ربط الطلب بالمدفوعات',
        ('case', 'judgment'): 'ربط القضية بالأحكام الصادرة فيها',
        ('case', 'session'): 'ربط القضية بجلسات المحاكمة',
        ('request', 'document'): 'ربط الطلب بالمستندات المرفقة',
        ('request', 'approval'): 'ربط الطلب بسجل الموافقات'
    }
    
    def __init__(self, min_confidence: float = 0.6):
        """
        Initialize the inference engine.
        
        Args:
            min_confidence: Minimum confidence score to include relationship (0-1)
        """
        self.min_confidence = min_confidence
        self._table_dict: Dict[str, TableModel] = {}
        self._column_index: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    
    def infer_relationships(self, tables: List[TableModel]) -> RelationshipInferenceResult:
        """
        Infer all relationships between tables.
        
        Args:
            tables: List of TableModel objects to analyze
            
        Returns:
            RelationshipInferenceResult with all discovered relationships
        """
        logger.info(f"Inferring relationships for {len(tables)} tables")
        
        # Build indexes
        self._build_indexes(tables)
        
        relationships: List[TableRelationship] = []
        analyzed_pairs: Set[Tuple[str, str]] = set()
        
        for table in tables:
            # 1. Process explicit foreign keys
            for col_name, (ref_table, ref_col) in table.foreign_keys.items():
                rel = self._create_explicit_fk_relationship(table, col_name, ref_table, ref_col)
                if rel:
                    relationships.append(rel)
                    analyzed_pairs.add((table.full_name, ref_table))
            
            # 2. Infer relationships from column patterns
            for column in table.columns:
                if column.is_foreign_key:
                    continue  # Already handled
                
                inferred = self._infer_column_relationship(table, column)
                for rel in inferred:
                    pair = (table.full_name, rel.target_full_name)
                    reverse_pair = (rel.target_full_name, table.full_name)
                    
                    if pair not in analyzed_pairs and reverse_pair not in analyzed_pairs:
                        if rel.confidence_score >= self.min_confidence:
                            relationships.append(rel)
                            analyzed_pairs.add(pair)
        
        # Find orphan tables
        tables_with_relationships = set()
        for rel in relationships:
            tables_with_relationships.add(rel.source_full_name)
            tables_with_relationships.add(rel.target_full_name)
        
        orphan_tables = [t.full_name for t in tables 
                        if t.full_name not in tables_with_relationships]
        
        # Create result
        result = RelationshipInferenceResult(
            relationships=relationships,
            orphan_tables=orphan_tables,
            analysis_notes=[
                f"تم اكتشاف {len(relationships)} علاقة بين الجداول",
                f"عدد الجداول المعزولة (بدون علاقات): {len(orphan_tables)}"
            ]
        )
        
        logger.info(f"Found {len(relationships)} relationships, "
                   f"{len(orphan_tables)} orphan tables")
        
        return result
    
    def _build_indexes(self, tables: List[TableModel]):
        """Build lookup indexes for faster matching"""
        self._table_dict.clear()
        self._column_index.clear()
        
        for table in tables:
            # Index by full name and short name
            self._table_dict[table.full_name.lower()] = table
            self._table_dict[table.table_name.lower()] = table
            
            # Index columns by normalized name
            for column in table.columns:
                normalized = self._normalize_column_name(column.name)
                self._column_index[normalized].append((table.full_name, column.name))
    
    def _normalize_column_name(self, name: str) -> str:
        """Normalize column name for matching"""
        name = name.lower()
        
        # Remove common prefixes
        for prefix in self.FK_PREFIXES:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        
        # Remove common suffixes for base name
        for suffix in self.ID_SUFFIXES:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        
        return name
    
    def _create_explicit_fk_relationship(
        self,
        table: TableModel,
        column_name: str,
        ref_table: str,
        ref_column: str
    ) -> Optional[TableRelationship]:
        """Create relationship from explicit FK definition"""
        # Find target table
        target = self._find_table(ref_table)
        if not target:
            logger.warning(f"Referenced table not found: {ref_table}")
            return None
        
        # Get business meaning
        meaning = self._get_relationship_meaning(table.table_name, target.table_name)
        
        return TableRelationship(
            source_schema=table.schema_name,
            source_table=table.table_name,
            source_column=column_name,
            target_schema=target.schema_name,
            target_table=target.table_name,
            target_column=ref_column,
            relationship_type=RelationshipType.FOREIGN_KEY,
            strength=RelationshipStrength.DEFINITE,
            confidence_score=1.0,
            business_meaning=meaning,
            validation_impact="عدم وجود القيمة في الجدول المرجعي يدل على خلل في سلامة البيانات",
            inference_reasons=["علاقة مفتاح أجنبي صريحة"]
        )
    
    def _infer_column_relationship(
        self,
        table: TableModel,
        column: ColumnModel
    ) -> List[TableRelationship]:
        """Infer relationships from column characteristics"""
        relationships = []
        col_name_lower = column.name.lower()
        
        # Check if this looks like a foreign key column
        if not self._looks_like_fk(column):
            return relationships
        
        # Get base name (without ID suffix)
        base_name = self._normalize_column_name(column.name)
        
        # Strategy 1: Exact name match with another table's PK
        for other_table in self._table_dict.values():
            if other_table.full_name == table.full_name:
                continue
            
            # Check if column name matches table name + Id pattern
            other_name_lower = other_table.table_name.lower()
            
            # Pattern: PersonId -> Person table
            if base_name == other_name_lower or base_name == self._normalize_column_name(other_name_lower):
                pk_columns = other_table.primary_key_columns
                if pk_columns:
                    rel = self._create_inferred_relationship(
                        table, column, other_table, pk_columns[0],
                        RelationshipType.INFERRED_NAME,
                        0.90,
                        ["تطابق اسم العمود مع اسم الجدول المرجعي"]
                    )
                    relationships.append(rel)
                    continue
                
                # Try to find matching column
                for other_col in other_table.columns:
                    if other_col.is_primary_key or other_col.is_unique:
                        if self._columns_match(column, other_col):
                            rel = self._create_inferred_relationship(
                                table, column, other_table, other_col.name,
                                RelationshipType.INFERRED_NAME,
                                0.85,
                                ["تطابق اسم العمود مع معرف في الجدول المرجعي"]
                            )
                            relationships.append(rel)
                            break
        
        # Strategy 2: Same column name in different table
        normalized = self._normalize_column_name(column.name)
        if normalized in self._column_index:
            for target_table_name, target_col_name in self._column_index[normalized]:
                target_table = self._table_dict.get(target_table_name.lower())
                if not target_table or target_table.full_name == table.full_name:
                    continue
                
                target_col = target_table.get_column(target_col_name)
                if not target_col:
                    continue
                
                # Check if target is PK or unique
                if target_col.is_primary_key or target_col.is_unique:
                    if self._columns_compatible(column, target_col):
                        rel = self._create_inferred_relationship(
                            table, column, target_table, target_col_name,
                            RelationshipType.INFERRED_NAME,
                            0.80,
                            [
                                "تطابق في اسم العمود",
                                f"العمود المرجعي هو {'مفتاح أساسي' if target_col.is_primary_key else 'فريد'}"
                            ]
                        )
                        if rel not in relationships:
                            relationships.append(rel)
        
        # Strategy 3: National ID pattern (common in Saudi systems)
        if 'national' in col_name_lower or 'هوية' in column.description.lower():
            for other_table in self._table_dict.values():
                if other_table.full_name == table.full_name:
                    continue
                
                # Look for Person/Citizen tables
                if any(kw in other_table.table_name.lower() 
                       for kw in ['person', 'citizen', 'individual', 'customer']):
                    for other_col in other_table.columns:
                        if 'national' in other_col.name.lower():
                            rel = self._create_inferred_relationship(
                                table, column, other_table, other_col.name,
                                RelationshipType.BUSINESS_LOGIC,
                                0.85,
                                [
                                    "رقم الهوية الوطنية يربط بجدول الأشخاص",
                                    "علاقة بزنس أساسية للتحقق من هوية الأشخاص"
                                ]
                            )
                            relationships.append(rel)
                            break
        
        return relationships
    
    def _looks_like_fk(self, column: ColumnModel) -> bool:
        """Check if column looks like a foreign key"""
        name_lower = column.name.lower()
        
        # Check ID suffixes
        for suffix in self.ID_SUFFIXES:
            if name_lower.endswith(suffix):
                return True
        
        # Check FK prefixes
        for prefix in self.FK_PREFIXES:
            if name_lower.startswith(prefix):
                return True
        
        # Check if it's an identifier type
        if column.is_identifier:
            return True
        
        # Check data type (INT, BIGINT, GUID typically used for FKs)
        norm_type = column.get_normalized_type()
        if norm_type in ['INTEGER', 'GUID']:
            # Must have ID-like name
            return any(kw in name_lower for kw in ['id', 'key', 'code', 'ref', 'no'])
        
        return False
    
    def _columns_match(self, col1: ColumnModel, col2: ColumnModel) -> bool:
        """Check if two columns likely refer to the same data"""
        # Normalize names
        name1 = self._normalize_column_name(col1.name)
        name2 = self._normalize_column_name(col2.name)
        
        # Exact match
        if name1 == name2:
            return True
        
        # Fuzzy match (if available)
        if HAS_FUZZY:
            ratio = fuzz.ratio(name1, name2)
            if ratio >= 80:
                return True
        
        return False
    
    def _columns_compatible(self, col1: ColumnModel, col2: ColumnModel) -> bool:
        """Check if two columns have compatible data types"""
        type1 = col1.get_normalized_type()
        type2 = col2.get_normalized_type()
        
        # Same type
        if type1 == type2:
            return True
        
        # Compatible numeric types
        if type1 in ['INTEGER', 'DECIMAL'] and type2 in ['INTEGER', 'DECIMAL']:
            return True
        
        return False
    
    def _create_inferred_relationship(
        self,
        source_table: TableModel,
        source_column: ColumnModel,
        target_table: TableModel,
        target_column: str,
        rel_type: RelationshipType,
        confidence: float,
        reasons: List[str]
    ) -> TableRelationship:
        """Create an inferred relationship"""
        # Determine strength
        if confidence >= 0.9:
            strength = RelationshipStrength.HIGH
        elif confidence >= 0.7:
            strength = RelationshipStrength.MEDIUM
        else:
            strength = RelationshipStrength.LOW
        
        # Get business meaning
        meaning = self._get_relationship_meaning(
            source_table.table_name,
            target_table.table_name
        )
        
        return TableRelationship(
            source_schema=source_table.schema_name,
            source_table=source_table.table_name,
            source_column=source_column.name,
            target_schema=target_table.schema_name,
            target_table=target_table.table_name,
            target_column=target_column,
            relationship_type=rel_type,
            strength=strength,
            confidence_score=confidence,
            business_meaning=meaning,
            validation_impact=self._get_validation_impact(source_table, target_table),
            inference_reasons=reasons
        )
    
    def _find_table(self, name: str) -> Optional[TableModel]:
        """Find table by name (case-insensitive)"""
        name_lower = name.lower()
        
        # Try exact match
        if name_lower in self._table_dict:
            return self._table_dict[name_lower]
        
        # Try without schema
        for key, table in self._table_dict.items():
            if table.table_name.lower() == name_lower:
                return table
        
        return None
    
    def _get_relationship_meaning(self, source_table: str, target_table: str) -> str:
        """Get Arabic business meaning for relationship"""
        source_lower = source_table.lower()
        target_lower = target_table.lower()
        
        # Check predefined meanings
        for (t1, t2), meaning in self.RELATIONSHIP_MEANINGS.items():
            if t1 in source_lower and t2 in target_lower:
                return meaning
            if t2 in source_lower and t1 in target_lower:
                return meaning
        
        # Generate generic meaning
        return f"ربط جدول {source_table} بجدول {target_table} للتحقق من سلامة البيانات المرجعية"
    
    def _get_validation_impact(
        self,
        source_table: TableModel,
        target_table: TableModel
    ) -> str:
        """Get Arabic description of validation impact"""
        impacts = []
        
        if source_table.sensitivity.value in ['HIGH', 'عالية']:
            impacts.append("بيانات حساسة تتطلب التحقق الدقيق")
        
        if target_table.table_type == TableType.MASTER:
            impacts.append("التحقق من وجود القيم في الجدول المرجعي الأساسي")
        
        if not impacts:
            impacts.append("عدم وجود القيمة في الجدول المرجعي يدل على خلل في سلامة البيانات")
        
        return "، ".join(impacts)
