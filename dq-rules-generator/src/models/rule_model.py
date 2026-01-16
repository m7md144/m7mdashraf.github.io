"""
Rule Data Models
================

Models representing Data Quality and Business Rules
with Arabic content support.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class Dimension(Enum):
    """Approved DQ Dimensions - Only these 6 are allowed"""
    COMPLETENESS = "Completeness"
    VALIDITY = "Validity"
    CONSISTENCY = "Consistency"
    UNIQUENESS = "Uniqueness"
    TIMELINESS = "Timeliness"
    ACCURACY = "Accuracy"
    
    @property
    def arabic_name(self) -> str:
        """Get Arabic name for dimension"""
        names = {
            "Completeness": "الاكتمال",
            "Validity": "الصحة",
            "Consistency": "الاتساق",
            "Uniqueness": "التفرد",
            "Timeliness": "الحداثة",
            "Accuracy": "الدقة"
        }
        return names.get(self.value, self.value)


class RuleType(Enum):
    """Classification of rule types"""
    DATA_QUALITY = "Data Quality"
    BUSINESS_RULE = "Business Rule"


class Severity(Enum):
    """Rule severity classification"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    
    @property
    def arabic_name(self) -> str:
        names = {
            "High": "عالية",
            "Medium": "متوسطة",
            "Low": "منخفضة"
        }
        return names.get(self.value, self.value)


@dataclass
class DQRule:
    """
    Represents a Data Quality or Business Rule
    
    All rules must have:
    - SQL Script (executable validation)
    - Business context (Arabic descriptions)
    - Clear impact and recommendations
    """
    
    # Identification
    rule_id: str = ""
    
    # Source Location
    system: str = ""
    database: str = ""
    schema: str = ""
    table: str = ""
    column: str = ""
    
    # Rule Classification
    dimension: Dimension = Dimension.COMPLETENESS
    rule_type: RuleType = RuleType.DATA_QUALITY
    severity: Severity = Severity.MEDIUM
    
    # Arabic Business Descriptions (Required)
    rule_description: str = ""      # وصف القاعدة - Business impact
    issue_description: str = ""     # وصف المشكلة - Clear problem statement
    root_cause: str = ""            # السبب الجذري - Operational/technical cause
    recommendation: str = ""        # التوصية - Actionable solution
    
    # SQL Script (Required - No rule without SQL)
    sql_script: str = ""
    
    # Related Objects (for cross-table rules)
    related_tables: str = ""
    related_columns: str = ""
    
    # Metrics (placeholders - filled after execution)
    total_invalid_records: Optional[int] = None
    total_records: Optional[int] = None
    invalid_records_pct: Optional[float] = None
    
    # Metadata
    dq_check_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    workflows: str = ""
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    
    def validate(self) -> bool:
        """Validate that rule meets all requirements"""
        self.validation_errors = []
        
        # Must have SQL
        if not self.sql_script or self.sql_script.strip() == "":
            self.validation_errors.append("قاعدة بدون SQL Script غير مقبولة")
        
        # Must have business descriptions
        if not self.rule_description:
            self.validation_errors.append("يجب وجود وصف للقاعدة")
        
        if not self.issue_description:
            self.validation_errors.append("يجب وجود وصف للمشكلة")
        
        # Must have table/column reference
        if not self.table:
            self.validation_errors.append("يجب تحديد الجدول المستهدف")
        
        # SQL should not be generic
        if self.sql_script and "SELECT *" in self.sql_script and "WHERE" not in self.sql_script:
            self.validation_errors.append("SQL عام بدون شرط تحقق غير مقبول")
        
        self.is_valid = len(self.validation_errors) == 0
        return self.is_valid
    
    def to_excel_row(self) -> dict:
        """Convert to Excel row format with exact column order"""
        return {
            "System": self.system,
            "Database": self.database,
            "Schema": self.schema,
            "Tables": self.table,
            "Columns": self.column,
            "Dimension": self.dimension.value,
            "Rule Description": self.rule_description,
            "Issue Description": self.issue_description,
            "Rule SQL Script": self.sql_script,
            "Related Tables": self.related_tables,
            "Related Columns": self.related_columns,
            "Total Invalid Records": self.total_invalid_records or "",
            "Total Records": self.total_records or "",
            "Invalid Records %": f"{self.invalid_records_pct:.2f}%" if self.invalid_records_pct else "",
            "Root Cause": self.root_cause,
            "Severity": self.severity.value,
            "Recommendation": self.recommendation,
            "DQ Check Date": self.dq_check_date,
            "Workflows": self.workflows,
            "Rule Type": self.rule_type.value
        }
    
    @staticmethod
    def get_excel_columns() -> List[str]:
        """Get exact column order for Excel output"""
        return [
            "System",
            "Database", 
            "Schema",
            "Tables",
            "Columns",
            "Dimension",
            "Rule Description",
            "Issue Description",
            "Rule SQL Script",
            "Related Tables",
            "Related Columns",
            "Total Invalid Records",
            "Total Records",
            "Invalid Records %",
            "Root Cause",
            "Severity",
            "Recommendation",
            "DQ Check Date",
            "Workflows",
            "Rule Type"
        ]
