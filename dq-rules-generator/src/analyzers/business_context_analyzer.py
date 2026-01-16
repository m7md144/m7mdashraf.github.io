"""
Business Context Analyzer
=========================

Analyzes tables and columns to extract business context,
including table types, business domains, and field semantics.

This is the "intelligence" layer that understands:
- What type of table this is (Master, Transaction, Log, etc.)
- What business domain it belongs to
- What each field means in business terms
- How sensitive the data is
"""

import re
from typing import List, Dict, Set, Tuple
from loguru import logger

from ..models.table_model import (
    TableModel, ColumnModel, TableType, BusinessDomain, DataSensitivity
)


class BusinessContextAnalyzer:
    """
    Analyzes database schema to extract business context.
    
    Uses pattern matching on names and descriptions to understand
    the business purpose of tables and columns.
    """
    
    # ==========================================================================
    # Table Type Detection Patterns
    # ==========================================================================
    
    TABLE_TYPE_PATTERNS = {
        TableType.MASTER: {
            'prefixes': ['mst_', 'master_', 'ref_', 'dim_'],
            'suffixes': ['_master', '_ref', '_reference', '_lookup'],
            'keywords': ['master', 'reference', 'lookup', 'مرجع', 'أساسي'],
            'patterns': [r'^(country|city|region|status|type|category|department)']
        },
        TableType.TRANSACTION: {
            'prefixes': ['trx_', 'trans_', 'fact_', 'txn_'],
            'suffixes': ['_trans', '_transaction', '_detail', '_line', '_item'],
            'keywords': ['transaction', 'order', 'invoice', 'payment', 'معاملة', 'طلب', 'فاتورة'],
            'patterns': [r'(order|invoice|payment|request|application|case)']
        },
        TableType.LOG: {
            'prefixes': ['log_', 'audit_', 'hist_', 'history_'],
            'suffixes': ['_log', '_audit', '_history', '_archive', '_tracking'],
            'keywords': ['log', 'audit', 'history', 'tracking', 'سجل', 'تدقيق', 'تاريخ'],
            'patterns': [r'(log|audit|history|tracking|archive)']
        },
        TableType.LOOKUP: {
            'prefixes': ['lkp_', 'lookup_', 'enum_', 'code_'],
            'suffixes': ['_lkp', '_lookup', '_type', '_status', '_code'],
            'keywords': ['lookup', 'enum', 'code', 'قائمة', 'رمز'],
            'patterns': [r'^(status|type|code|enum)_']
        },
        TableType.BRIDGE: {
            'prefixes': ['bridge_', 'map_', 'xref_', 'link_'],
            'suffixes': ['_map', '_mapping', '_link', '_xref', '_bridge'],
            'keywords': ['mapping', 'bridge', 'link', 'ربط', 'علاقة'],
            'patterns': [r'_to_|_x_|_map$']
        },
        TableType.STAGING: {
            'prefixes': ['stg_', 'staging_', 'tmp_', 'temp_', 'raw_'],
            'suffixes': ['_stg', '_staging', '_temp', '_raw'],
            'keywords': ['staging', 'temporary', 'raw', 'مؤقت'],
            'patterns': [r'^(stg|tmp|temp|raw)_']
        }
    }
    
    # ==========================================================================
    # Business Domain Detection Patterns
    # ==========================================================================
    
    DOMAIN_PATTERNS = {
        BusinessDomain.LEGAL: {
            'keywords': [
                'case', 'court', 'judgment', 'verdict', 'sentence', 'penalty',
                'law', 'legal', 'lawsuit', 'litigation', 'attorney', 'lawyer',
                'قضية', 'محكمة', 'حكم', 'عقوبة', 'قانون', 'دعوى', 'محامي',
                'نيابة', 'جلسة', 'استئناف', 'تنفيذ'
            ],
            'table_patterns': [r'(case|court|judgment|verdict|sentence|penalty|lawsuit)']
        },
        BusinessDomain.PERSON: {
            'keywords': [
                'person', 'citizen', 'individual', 'customer', 'client', 'user',
                'identity', 'national_id', 'passport', 'name', 'birth',
                'شخص', 'مواطن', 'عميل', 'هوية', 'جواز', 'مستخدم', 'فرد'
            ],
            'table_patterns': [r'(person|citizen|customer|client|user|individual|member)']
        },
        BusinessDomain.FINANCIAL: {
            'keywords': [
                'payment', 'invoice', 'account', 'balance', 'transaction', 'fee',
                'amount', 'price', 'cost', 'revenue', 'expense', 'budget',
                'دفع', 'فاتورة', 'حساب', 'رصيد', 'مبلغ', 'سعر', 'تكلفة', 'ميزانية'
            ],
            'table_patterns': [r'(payment|invoice|account|transaction|fee|finance|budget)']
        },
        BusinessDomain.REQUESTS: {
            'keywords': [
                'request', 'application', 'submission', 'approval', 'workflow',
                'task', 'ticket', 'order', 'procedure',
                'طلب', 'تقديم', 'موافقة', 'إجراء', 'مهمة', 'أمر'
            ],
            'table_patterns': [r'(request|application|submission|approval|ticket|order)']
        },
        BusinessDomain.DOCUMENTS: {
            'keywords': [
                'document', 'file', 'attachment', 'certificate', 'license',
                'contract', 'agreement', 'report',
                'وثيقة', 'ملف', 'مرفق', 'شهادة', 'رخصة', 'عقد', 'تقرير'
            ],
            'table_patterns': [r'(document|file|attachment|certificate|license|contract)']
        },
        BusinessDomain.EMPLOYEES: {
            'keywords': [
                'employee', 'staff', 'hr', 'human_resource', 'salary', 'leave',
                'attendance', 'department', 'position', 'job',
                'موظف', 'راتب', 'إجازة', 'حضور', 'قسم', 'وظيفة'
            ],
            'table_patterns': [r'(employee|staff|hr|salary|leave|attendance|department)']
        },
        BusinessDomain.INVENTORY: {
            'keywords': [
                'inventory', 'stock', 'warehouse', 'product', 'item', 'asset',
                'material', 'supply', 'equipment',
                'مخزون', 'مستودع', 'منتج', 'أصل', 'مادة', 'معدات'
            ],
            'table_patterns': [r'(inventory|stock|warehouse|product|item|asset|material)']
        },
        BusinessDomain.CUSTOMERS: {
            'keywords': [
                'customer', 'client', 'account', 'subscription', 'service',
                'عميل', 'زبون', 'اشتراك', 'خدمة'
            ],
            'table_patterns': [r'(customer|client|subscriber|account)']
        }
    }
    
    # ==========================================================================
    # Column Semantic Patterns
    # ==========================================================================
    
    COLUMN_PATTERNS = {
        'identifier': {
            'patterns': [r'_id$', r'^id$', r'_key$', r'_code$', r'_no$', r'_number$'],
            'keywords': ['id', 'identifier', 'key', 'code', 'number', 'معرف', 'رقم', 'رمز']
        },
        'legal': {
            'patterns': [r'(court|case|judgment|verdict|penalty|law|license|permit)'],
            'keywords': ['court', 'case', 'judgment', 'sentence', 'penalty', 'license',
                        'محكمة', 'قضية', 'حكم', 'عقوبة', 'رخصة', 'تصريح']
        },
        'date': {
            'patterns': [r'_date$', r'_dt$', r'^date_', r'_time$', r'_at$'],
            'keywords': ['date', 'time', 'timestamp', 'created', 'modified', 'birth',
                        'تاريخ', 'وقت', 'إنشاء', 'تعديل', 'ميلاد']
        },
        'status': {
            'patterns': [r'_status$', r'_state$', r'^status_', r'^is_', r'^has_', r'^flag_'],
            'keywords': ['status', 'state', 'active', 'enabled', 'flag', 'حالة', 'فعال']
        },
        'amount': {
            'patterns': [r'_amount$', r'_price$', r'_cost$', r'_fee$', r'_total$', r'_balance$'],
            'keywords': ['amount', 'price', 'cost', 'fee', 'total', 'balance', 'salary',
                        'مبلغ', 'سعر', 'تكلفة', 'رسوم', 'إجمالي', 'رصيد', 'راتب']
        },
        'name': {
            'patterns': [r'_name$', r'^name_', r'_title$', r'^full_name'],
            'keywords': ['name', 'title', 'label', 'description', 'اسم', 'عنوان', 'وصف']
        },
        'personal': {
            'patterns': [r'(national_id|citizen_id|passport|ssn|phone|mobile|email|address)'],
            'keywords': ['national', 'citizen', 'passport', 'phone', 'mobile', 'email', 'address',
                        'هوية', 'جواز', 'هاتف', 'جوال', 'بريد', 'عنوان']
        },
        'decision': {
            'patterns': [r'(approved|rejected|decision|verdict|result|outcome)'],
            'keywords': ['approved', 'rejected', 'decision', 'verdict', 'result', 'outcome',
                        'موافق', 'مرفوض', 'قرار', 'نتيجة']
        }
    }
    
    # ==========================================================================
    # High Sensitivity Keywords
    # ==========================================================================
    
    HIGH_SENSITIVITY_PATTERNS = [
        r'national_id', r'citizen_id', r'passport', r'ssn', r'social_security',
        r'credit_card', r'bank_account', r'salary', r'password', r'secret',
        r'medical', r'health', r'diagnosis', r'criminal', r'conviction',
        r'هوية', r'جواز', r'راتب', r'كلمة_سر', r'طبي', r'صحي', r'جنائي'
    ]
    
    def __init__(self):
        """Initialize the analyzer"""
        self._compiled_patterns: Dict = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        for category, patterns in self.COLUMN_PATTERNS.items():
            self._compiled_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns['patterns']
            ]
    
    def analyze(self, tables: List[TableModel]) -> List[TableModel]:
        """
        Analyze all tables and enrich them with business context.
        
        Args:
            tables: List of TableModel objects to analyze
            
        Returns:
            Enriched TableModel objects with business context
        """
        logger.info(f"Analyzing business context for {len(tables)} tables")
        
        for table in tables:
            self._analyze_table(table)
            
            for column in table.columns:
                self._analyze_column(column, table)
        
        return tables
    
    def _analyze_table(self, table: TableModel):
        """Analyze a single table for business context"""
        table_name_lower = table.table_name.lower()
        desc_lower = table.description.lower() if table.description else ""
        combined = f"{table_name_lower} {desc_lower}"
        
        # Detect table type
        table.table_type = self._detect_table_type(table_name_lower, desc_lower)
        
        # Detect business domain
        table.business_domain = self._detect_business_domain(combined)
        
        # Detect sensitivity (will be refined by columns)
        table.sensitivity = DataSensitivity.LOW
        
        logger.debug(f"Table {table.table_name}: Type={table.table_type.value}, "
                    f"Domain={table.business_domain.value}")
    
    def _detect_table_type(self, name: str, description: str) -> TableType:
        """Detect table type based on naming patterns and description"""
        combined = f"{name} {description}"
        
        for table_type, patterns in self.TABLE_TYPE_PATTERNS.items():
            # Check prefixes
            for prefix in patterns['prefixes']:
                if name.startswith(prefix):
                    return table_type
            
            # Check suffixes
            for suffix in patterns['suffixes']:
                if name.endswith(suffix):
                    return table_type
            
            # Check keywords
            for keyword in patterns['keywords']:
                if keyword in combined:
                    return table_type
            
            # Check regex patterns
            for pattern in patterns['patterns']:
                if re.search(pattern, name, re.IGNORECASE):
                    return table_type
        
        return TableType.UNKNOWN
    
    def _detect_business_domain(self, combined_text: str) -> BusinessDomain:
        """Detect business domain based on keywords and patterns"""
        max_score = 0
        best_domain = BusinessDomain.GENERAL
        
        for domain, patterns in self.DOMAIN_PATTERNS.items():
            score = 0
            
            # Count keyword matches
            for keyword in patterns['keywords']:
                if keyword in combined_text:
                    score += 1
            
            # Check table patterns
            for pattern in patterns['table_patterns']:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    score += 2  # Weight patterns higher
            
            if score > max_score:
                max_score = score
                best_domain = domain
        
        return best_domain
    
    def _analyze_column(self, column: ColumnModel, table: TableModel):
        """Analyze a single column for semantic context"""
        col_name_lower = column.name.lower()
        desc_lower = column.description.lower() if column.description else ""
        combined = f"{col_name_lower} {desc_lower}"
        
        # Check each semantic category
        for category, patterns in self.COLUMN_PATTERNS.items():
            is_match = self._check_column_category(combined, patterns)
            
            if is_match:
                if category == 'identifier':
                    column.is_identifier = True
                elif category == 'legal':
                    column.is_legal_field = True
                elif category == 'date':
                    column.is_date_field = True
                elif category == 'status':
                    column.is_status_field = True
                elif category == 'amount':
                    column.is_amount_field = True
                elif category == 'name':
                    column.is_name_field = True
                elif category == 'decision':
                    column.is_decision_field = True
                elif category == 'personal':
                    column.is_operational_field = True
                    column.sensitivity = DataSensitivity.HIGH
        
        # Auto-detect date fields by type
        if column.get_normalized_type() == 'DATETIME':
            column.is_date_field = True
        
        # Check high sensitivity patterns
        for pattern in self.HIGH_SENSITIVITY_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                column.sensitivity = DataSensitivity.HIGH
                break
        
        # Update table sensitivity if column is high
        if column.sensitivity == DataSensitivity.HIGH:
            if table.sensitivity != DataSensitivity.CONFIDENTIAL:
                table.sensitivity = DataSensitivity.HIGH
    
    def _check_column_category(self, text: str, category_config: Dict) -> bool:
        """Check if text matches a category's patterns and keywords"""
        # Check keywords
        for keyword in category_config.get('keywords', []):
            if keyword in text:
                return True
        
        # Check patterns
        for pattern in category_config.get('patterns', []):
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def get_table_summary(self, table: TableModel) -> Dict:
        """Get a summary of business context for a table"""
        return {
            'table_name': table.full_name,
            'table_type': table.table_type.value,
            'business_domain': table.business_domain.value,
            'sensitivity': table.sensitivity.value,
            'column_count': len(table.columns),
            'identifier_columns': [c.name for c in table.columns if c.is_identifier],
            'date_columns': [c.name for c in table.columns if c.is_date_field],
            'status_columns': [c.name for c in table.columns if c.is_status_field],
            'amount_columns': [c.name for c in table.columns if c.is_amount_field],
            'high_sensitivity_columns': [c.name for c in table.columns 
                                         if c.sensitivity == DataSensitivity.HIGH]
        }
