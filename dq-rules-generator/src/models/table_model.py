"""
Table and Column Data Models
============================

Models representing database tables and columns with their
business context and metadata.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class TableType(Enum):
    """Classification of table types based on business function"""
    MASTER = "Master"           # Reference/lookup data (e.g., Countries, Status codes)
    TRANSACTION = "Transaction" # Business transactions (e.g., Orders, Payments)
    LOG = "Log"                 # Audit/history logs
    LOOKUP = "Lookup"           # Small reference tables
    BRIDGE = "Bridge"           # Many-to-many relationship tables
    STAGING = "Staging"         # ETL staging tables
    ARCHIVE = "Archive"         # Historical archived data
    UNKNOWN = "Unknown"


class BusinessDomain(Enum):
    """Business domain classification"""
    LEGAL = "قضايا وأحكام"          # Cases and judgments
    PERSON = "أشخاص وهويات"         # Persons and identities
    FINANCIAL = "مالية ومحاسبة"      # Financial and accounting
    REQUESTS = "طلبات وإجراءات"      # Requests and procedures
    DOCUMENTS = "وثائق ومستندات"     # Documents
    EMPLOYEES = "موظفين وموارد بشرية" # HR
    INVENTORY = "مخزون وأصول"        # Inventory and assets
    CUSTOMERS = "عملاء"             # Customers
    GENERAL = "عام"                 # General


class DataSensitivity(Enum):
    """Data sensitivity classification"""
    HIGH = "عالية"          # PII, financial, legal
    MEDIUM = "متوسطة"       # Operational data
    LOW = "منخفضة"          # Reference data
    CONFIDENTIAL = "سرية"   # Highly restricted


@dataclass
class ColumnModel:
    """Represents a database column with its metadata and business context"""
    
    name: str
    data_type: str
    description: str = ""
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_unique: bool = False
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    default_value: Optional[str] = None
    
    # Business Context (derived)
    is_identifier: bool = False          # Is it an ID field
    is_legal_field: bool = False         # Legal/compliance impact
    is_decision_field: bool = False      # Affects business decisions
    is_operational_field: bool = False   # Operational impact
    is_date_field: bool = False          # Date/time field
    is_status_field: bool = False        # Status/state field
    is_amount_field: bool = False        # Financial amount
    is_name_field: bool = False          # Name/text identifier
    sensitivity: DataSensitivity = DataSensitivity.LOW
    
    # Relationship hints
    references_table: Optional[str] = None
    references_column: Optional[str] = None
    
    # Statistics (if available)
    null_count: Optional[int] = None
    distinct_count: Optional[int] = None
    sample_values: List[Any] = field(default_factory=list)
    
    def get_normalized_type(self) -> str:
        """Get normalized data type category"""
        type_lower = self.data_type.lower()
        
        if any(t in type_lower for t in ['varchar', 'nvarchar', 'char', 'text', 'string']):
            return 'STRING'
        elif any(t in type_lower for t in ['int', 'bigint', 'smallint', 'tinyint']):
            return 'INTEGER'
        elif any(t in type_lower for t in ['decimal', 'numeric', 'float', 'real', 'money']):
            return 'DECIMAL'
        elif any(t in type_lower for t in ['date', 'datetime', 'time', 'timestamp']):
            return 'DATETIME'
        elif any(t in type_lower for t in ['bit', 'bool']):
            return 'BOOLEAN'
        elif any(t in type_lower for t in ['uniqueidentifier', 'guid', 'uuid']):
            return 'GUID'
        elif any(t in type_lower for t in ['binary', 'varbinary', 'image', 'blob']):
            return 'BINARY'
        else:
            return 'UNKNOWN'


@dataclass
class TableModel:
    """Represents a database table with its metadata and business context"""
    
    schema_name: str
    table_name: str
    description: str = ""
    columns: List[ColumnModel] = field(default_factory=list)
    
    # Business Context (derived)
    table_type: TableType = TableType.UNKNOWN
    business_domain: BusinessDomain = BusinessDomain.GENERAL
    sensitivity: DataSensitivity = DataSensitivity.LOW
    
    # Relationships
    primary_key_columns: List[str] = field(default_factory=list)
    foreign_keys: Dict[str, tuple] = field(default_factory=dict)  # col -> (ref_table, ref_col)
    
    # Metadata
    row_count: Optional[int] = None
    
    @property
    def full_name(self) -> str:
        """Get fully qualified table name"""
        if self.schema_name:
            return f"{self.schema_name}.{self.table_name}"
        return self.table_name
    
    def get_column(self, name: str) -> Optional[ColumnModel]:
        """Get column by name (case-insensitive)"""
        name_lower = name.lower()
        for col in self.columns:
            if col.name.lower() == name_lower:
                return col
        return None
    
    def get_identifier_columns(self) -> List[ColumnModel]:
        """Get columns that are identifiers"""
        return [c for c in self.columns if c.is_identifier or c.is_primary_key]
    
    def get_date_columns(self) -> List[ColumnModel]:
        """Get date/datetime columns"""
        return [c for c in self.columns if c.is_date_field]
    
    def get_status_columns(self) -> List[ColumnModel]:
        """Get status/state columns"""
        return [c for c in self.columns if c.is_status_field]
    
    def get_amount_columns(self) -> List[ColumnModel]:
        """Get financial amount columns"""
        return [c for c in self.columns if c.is_amount_field]
