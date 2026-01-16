"""
SQL Generator
=============

Generates SQL Server validation queries for DQ rules.

All SQL:
- Is executable (not pseudo-code)
- Identifies invalid records
- Supports TRIM for text fields
- Supports JOINs for cross-table validation
- Includes metrics calculation (total, invalid, percentage)
"""

from typing import Optional, List, Dict
from ..models.table_model import TableModel, ColumnModel
from ..models.relationship_model import TableRelationship


class SQLGenerator:
    """
    Generates SQL Server compatible validation queries.
    
    Query Structure:
    1. Main query to identify invalid records
    2. Wrapped with CTE for metrics calculation
    """
    
    def __init__(self, database: str = "", schema: str = "dbo"):
        """
        Initialize SQL generator.
        
        Args:
            database: Database name (optional)
            schema: Default schema name
        """
        self.database = database
        self.default_schema = schema
    
    def _get_full_table_name(self, table: TableModel) -> str:
        """Get fully qualified table name"""
        parts = []
        if self.database:
            parts.append(f"[{self.database}]")
        parts.append(f"[{table.schema_name or self.default_schema}]")
        parts.append(f"[{table.table_name}]")
        return ".".join(parts)
    
    def _get_table_alias(self, table_name: str) -> str:
        """Generate short alias for table"""
        # Take first letter of each word
        words = table_name.replace('_', ' ').split()
        if len(words) > 1:
            return ''.join(w[0].lower() for w in words)
        return table_name[:3].lower()
    
    # ==========================================================================
    # Completeness Checks
    # ==========================================================================
    
    def null_check(self, table: TableModel, column: ColumnModel) -> str:
        """Generate NULL check SQL"""
        full_table = self._get_full_table_name(table)
        
        return f"""-- التحقق من القيم الفارغة (NULL) في {column.name}
SELECT 
    [{column.name}],
    *
FROM {full_table}
WHERE [{column.name}] IS NULL"""
    
    def empty_string_check(self, table: TableModel, column: ColumnModel) -> str:
        """Generate empty string check SQL"""
        full_table = self._get_full_table_name(table)
        
        return f"""-- التحقق من النصوص الفارغة في {column.name}
SELECT 
    [{column.name}],
    *
FROM {full_table}
WHERE [{column.name}] = '' 
   OR LTRIM(RTRIM([{column.name}])) = ''"""
    
    def completeness_check(self, table: TableModel, column: ColumnModel) -> str:
        """Generate comprehensive completeness check SQL"""
        full_table = self._get_full_table_name(table)
        
        if column.get_normalized_type() == 'STRING':
            return f"""-- التحقق من اكتمال {column.name}
SELECT 
    [{column.name}],
    CASE 
        WHEN [{column.name}] IS NULL THEN 'NULL'
        WHEN [{column.name}] = '' THEN 'Empty'
        WHEN LTRIM(RTRIM([{column.name}])) = '' THEN 'Whitespace Only'
    END AS IssueType,
    *
FROM {full_table}
WHERE [{column.name}] IS NULL 
   OR [{column.name}] = ''
   OR LTRIM(RTRIM([{column.name}])) = ''"""
        else:
            return f"""-- التحقق من اكتمال {column.name}
SELECT 
    [{column.name}],
    *
FROM {full_table}
WHERE [{column.name}] IS NULL"""
    
    # ==========================================================================
    # Validity Checks
    # ==========================================================================
    
    def email_format_check(self, table: TableModel, column: ColumnModel) -> str:
        """Generate email format validation SQL"""
        full_table = self._get_full_table_name(table)
        
        return f"""-- التحقق من صحة تنسيق البريد الإلكتروني
SELECT 
    [{column.name}],
    *
FROM {full_table}
WHERE [{column.name}] IS NOT NULL
  AND [{column.name}] != ''
  AND (
    [{column.name}] NOT LIKE '%_@_%.__%'
    OR [{column.name}] LIKE '% %'
    OR [{column.name}] LIKE '%@%@%'
  )"""
    
    def phone_format_check(self, table: TableModel, column: ColumnModel) -> str:
        """Generate phone format validation SQL (Saudi format)"""
        full_table = self._get_full_table_name(table)
        
        return f"""-- التحقق من صحة تنسيق رقم الهاتف
SELECT 
    [{column.name}],
    LEN(REPLACE(REPLACE(REPLACE([{column.name}], '-', ''), ' ', ''), '+', '')) AS DigitCount,
    *
FROM {full_table}
WHERE [{column.name}] IS NOT NULL
  AND [{column.name}] != ''
  AND (
    -- أرقام أقل من 9 خانات أو أكثر من 15
    LEN(REPLACE(REPLACE(REPLACE([{column.name}], '-', ''), ' ', ''), '+', '')) < 9
    OR LEN(REPLACE(REPLACE(REPLACE([{column.name}], '-', ''), ' ', ''), '+', '')) > 15
    -- يحتوي على أحرف غير رقمية (عدا + و - والمسافة)
    OR [{column.name}] LIKE '%[^0-9+\- ]%'
  )"""
    
    def national_id_check(self, table: TableModel, column: ColumnModel) -> str:
        """Generate Saudi National ID validation SQL"""
        full_table = self._get_full_table_name(table)
        
        return f"""-- التحقق من صحة رقم الهوية الوطنية السعودية
SELECT 
    [{column.name}],
    LEN([{column.name}]) AS Length,
    LEFT([{column.name}], 1) AS FirstDigit,
    *
FROM {full_table}
WHERE [{column.name}] IS NOT NULL
  AND [{column.name}] != ''
  AND (
    -- الطول يجب أن يكون 10 أرقام
    LEN([{column.name}]) != 10
    -- يجب أن يبدأ بـ 1 (مواطن) أو 2 (مقيم)
    OR LEFT([{column.name}], 1) NOT IN ('1', '2')
    -- يجب أن يحتوي على أرقام فقط
    OR [{column.name}] LIKE '%[^0-9]%'
  )"""
    
    def date_range_check(
        self, 
        table: TableModel, 
        column: ColumnModel,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None
    ) -> str:
        """Generate date range validation SQL"""
        full_table = self._get_full_table_name(table)
        
        conditions = [f"[{column.name}] IS NOT NULL"]
        
        if min_date:
            conditions.append(f"[{column.name}] < '{min_date}'")
        
        if max_date:
            conditions.append(f"[{column.name}] > '{max_date}'")
        else:
            # Default: no future dates for historical fields
            conditions.append(f"[{column.name}] > GETDATE()")
        
        where_clause = " OR ".join(conditions[1:]) if len(conditions) > 1 else "1=1"
        
        return f"""-- التحقق من نطاق التاريخ في {column.name}
SELECT 
    [{column.name}],
    *
FROM {full_table}
WHERE [{column.name}] IS NOT NULL
  AND ({where_clause})"""
    
    def future_date_check(self, table: TableModel, column: ColumnModel) -> str:
        """Generate future date check for historical dates"""
        full_table = self._get_full_table_name(table)
        
        return f"""-- التحقق من عدم وجود تواريخ مستقبلية في {column.name}
SELECT 
    [{column.name}],
    DATEDIFF(DAY, GETDATE(), [{column.name}]) AS DaysInFuture,
    *
FROM {full_table}
WHERE [{column.name}] IS NOT NULL
  AND [{column.name}] > GETDATE()"""
    
    def amount_range_check(
        self, 
        table: TableModel, 
        column: ColumnModel,
        min_value: float = 0,
        max_value: Optional[float] = None
    ) -> str:
        """Generate amount range validation SQL"""
        full_table = self._get_full_table_name(table)
        
        conditions = [f"[{column.name}] < {min_value}"]
        if max_value:
            conditions.append(f"[{column.name}] > {max_value}")
        
        where_clause = " OR ".join(conditions)
        
        return f"""-- التحقق من نطاق القيمة المالية في {column.name}
SELECT 
    [{column.name}],
    *
FROM {full_table}
WHERE [{column.name}] IS NOT NULL
  AND ({where_clause})"""
    
    def allowed_values_check(
        self, 
        table: TableModel, 
        column: ColumnModel,
        allowed_values: List[str]
    ) -> str:
        """Generate allowed values validation SQL"""
        full_table = self._get_full_table_name(table)
        values_str = ", ".join([f"'{v}'" for v in allowed_values])
        
        return f"""-- التحقق من القيم المسموحة في {column.name}
SELECT 
    [{column.name}],
    *
FROM {full_table}
WHERE [{column.name}] IS NOT NULL
  AND [{column.name}] NOT IN ({values_str})"""
    
    def length_check(
        self, 
        table: TableModel, 
        column: ColumnModel,
        min_length: int = 1,
        max_length: Optional[int] = None
    ) -> str:
        """Generate string length validation SQL"""
        full_table = self._get_full_table_name(table)
        
        conditions = []
        if min_length > 0:
            conditions.append(f"LEN(LTRIM(RTRIM([{column.name}]))) < {min_length}")
        if max_length:
            conditions.append(f"LEN([{column.name}]) > {max_length}")
        
        where_clause = " OR ".join(conditions) if conditions else "1=0"
        
        return f"""-- التحقق من طول النص في {column.name}
SELECT 
    [{column.name}],
    LEN([{column.name}]) AS ActualLength,
    *
FROM {full_table}
WHERE [{column.name}] IS NOT NULL
  AND [{column.name}] != ''
  AND ({where_clause})"""
    
    # ==========================================================================
    # Uniqueness Checks
    # ==========================================================================
    
    def uniqueness_check(self, table: TableModel, column: ColumnModel) -> str:
        """Generate uniqueness/duplicate check SQL"""
        full_table = self._get_full_table_name(table)
        
        return f"""-- التحقق من تفرد {column.name}
SELECT 
    [{column.name}],
    COUNT(*) AS DuplicateCount
FROM {full_table}
WHERE [{column.name}] IS NOT NULL
GROUP BY [{column.name}]
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC"""
    
    def uniqueness_check_detailed(self, table: TableModel, column: ColumnModel) -> str:
        """Generate detailed uniqueness check showing all duplicate records"""
        full_table = self._get_full_table_name(table)
        alias = self._get_table_alias(table.table_name)
        
        return f"""-- عرض جميع السجلات المكررة في {column.name}
SELECT 
    {alias}.*,
    dup.DuplicateCount
FROM {full_table} {alias}
INNER JOIN (
    SELECT [{column.name}], COUNT(*) AS DuplicateCount
    FROM {full_table}
    WHERE [{column.name}] IS NOT NULL
    GROUP BY [{column.name}]
    HAVING COUNT(*) > 1
) dup ON {alias}.[{column.name}] = dup.[{column.name}]
ORDER BY {alias}.[{column.name}]"""
    
    def composite_uniqueness_check(
        self, 
        table: TableModel, 
        columns: List[ColumnModel]
    ) -> str:
        """Generate composite uniqueness check SQL"""
        full_table = self._get_full_table_name(table)
        col_names = ", ".join([f"[{c.name}]" for c in columns])
        col_list = ", ".join([c.name for c in columns])
        
        return f"""-- التحقق من تفرد المفتاح المركب ({col_list})
SELECT 
    {col_names},
    COUNT(*) AS DuplicateCount
FROM {full_table}
WHERE {" AND ".join([f"[{c.name}] IS NOT NULL" for c in columns])}
GROUP BY {col_names}
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC"""
    
    # ==========================================================================
    # Consistency Checks (Cross-Table)
    # ==========================================================================
    
    def referential_integrity_check(
        self, 
        relationship: TableRelationship
    ) -> str:
        """Generate referential integrity check SQL"""
        db_prefix = f"[{self.database}]." if self.database else ""
        
        source_table = f"{db_prefix}[{relationship.source_schema}].[{relationship.source_table}]"
        target_table = f"{db_prefix}[{relationship.target_schema}].[{relationship.target_table}]"
        
        src_alias = self._get_table_alias(relationship.source_table)
        tgt_alias = self._get_table_alias(relationship.target_table)
        
        return f"""-- التحقق من السلامة المرجعية: {relationship.source_table}.{relationship.source_column} -> {relationship.target_table}.{relationship.target_column}
SELECT 
    {src_alias}.[{relationship.source_column}],
    '{relationship.source_table}' AS SourceTable,
    '{relationship.target_table}' AS ExpectedTargetTable,
    {src_alias}.*
FROM {source_table} {src_alias}
LEFT JOIN {target_table} {tgt_alias}
    ON {src_alias}.[{relationship.source_column}] = {tgt_alias}.[{relationship.target_column}]
WHERE {src_alias}.[{relationship.source_column}] IS NOT NULL
  AND {tgt_alias}.[{relationship.target_column}] IS NULL"""
    
    def cross_table_consistency_check(
        self,
        table1: TableModel,
        column1: ColumnModel,
        table2: TableModel,
        column2: ColumnModel
    ) -> str:
        """Generate cross-table data consistency check SQL"""
        db_prefix = f"[{self.database}]." if self.database else ""
        
        full_table1 = f"{db_prefix}[{table1.schema_name}].[{table1.table_name}]"
        full_table2 = f"{db_prefix}[{table2.schema_name}].[{table2.table_name}]"
        
        alias1 = self._get_table_alias(table1.table_name)
        alias2 = self._get_table_alias(table2.table_name)
        
        return f"""-- التحقق من اتساق البيانات بين {table1.table_name} و {table2.table_name}
SELECT 
    {alias1}.[{column1.name}] AS [{table1.table_name}_{column1.name}],
    {alias2}.[{column2.name}] AS [{table2.table_name}_{column2.name}],
    {alias1}.*
FROM {full_table1} {alias1}
INNER JOIN {full_table2} {alias2}
    ON {alias1}.[{column1.name}] = {alias2}.[{column2.name}]
WHERE LTRIM(RTRIM(ISNULL({alias1}.[{column1.name}], ''))) != LTRIM(RTRIM(ISNULL({alias2}.[{column2.name}], '')))"""
    
    def date_sequence_check(
        self,
        table: TableModel,
        start_column: ColumnModel,
        end_column: ColumnModel
    ) -> str:
        """Generate date sequence validation (start < end)"""
        full_table = self._get_full_table_name(table)
        
        return f"""-- التحقق من التسلسل الزمني: {start_column.name} يجب أن يسبق {end_column.name}
SELECT 
    [{start_column.name}] AS StartDate,
    [{end_column.name}] AS EndDate,
    DATEDIFF(DAY, [{start_column.name}], [{end_column.name}]) AS DaysDifference,
    *
FROM {full_table}
WHERE [{start_column.name}] IS NOT NULL
  AND [{end_column.name}] IS NOT NULL
  AND [{start_column.name}] > [{end_column.name}]"""
    
    def total_match_check(
        self,
        header_table: TableModel,
        header_total_column: ColumnModel,
        detail_table: TableModel,
        detail_amount_column: ColumnModel,
        join_column: str
    ) -> str:
        """Generate header-detail total matching check"""
        db_prefix = f"[{self.database}]." if self.database else ""
        
        header_full = f"{db_prefix}[{header_table.schema_name}].[{header_table.table_name}]"
        detail_full = f"{db_prefix}[{detail_table.schema_name}].[{detail_table.table_name}]"
        
        return f"""-- التحقق من تطابق إجمالي {header_table.table_name} مع مجموع {detail_table.table_name}
SELECT 
    h.[{join_column}],
    h.[{header_total_column.name}] AS HeaderTotal,
    ISNULL(SUM(d.[{detail_amount_column.name}]), 0) AS CalculatedTotal,
    h.[{header_total_column.name}] - ISNULL(SUM(d.[{detail_amount_column.name}]), 0) AS Difference
FROM {header_full} h
LEFT JOIN {detail_full} d ON h.[{join_column}] = d.[{join_column}]
GROUP BY h.[{join_column}], h.[{header_total_column.name}]
HAVING h.[{header_total_column.name}] != ISNULL(SUM(d.[{detail_amount_column.name}]), 0)"""
    
    # ==========================================================================
    # Timeliness Checks
    # ==========================================================================
    
    def freshness_check(
        self, 
        table: TableModel, 
        column: ColumnModel,
        threshold_days: int = 30
    ) -> str:
        """Generate data freshness check SQL"""
        full_table = self._get_full_table_name(table)
        
        return f"""-- التحقق من حداثة البيانات في {column.name} (الحد: {threshold_days} يوم)
SELECT 
    [{column.name}],
    DATEDIFF(DAY, [{column.name}], GETDATE()) AS DaysSinceUpdate,
    *
FROM {full_table}
WHERE [{column.name}] IS NOT NULL
  AND DATEDIFF(DAY, [{column.name}], GETDATE()) > {threshold_days}"""
    
    def expiry_check(self, table: TableModel, column: ColumnModel) -> str:
        """Generate expiry date check SQL"""
        full_table = self._get_full_table_name(table)
        
        return f"""-- التحقق من انتهاء الصلاحية في {column.name}
SELECT 
    [{column.name}],
    DATEDIFF(DAY, GETDATE(), [{column.name}]) AS DaysUntilExpiry,
    CASE 
        WHEN [{column.name}] < GETDATE() THEN 'منتهي الصلاحية'
        WHEN [{column.name}] < DATEADD(DAY, 30, GETDATE()) THEN 'قريب الانتهاء (خلال 30 يوم)'
        ELSE 'صالح'
    END AS ExpiryStatus,
    *
FROM {full_table}
WHERE [{column.name}] IS NOT NULL
  AND [{column.name}] < GETDATE()"""
    
    # ==========================================================================
    # Metrics Wrapper
    # ==========================================================================
    
    def wrap_with_metrics(self, validation_sql: str, table: TableModel) -> str:
        """Wrap validation SQL with metrics calculation"""
        full_table = self._get_full_table_name(table)
        
        return f"""-- حساب مقاييس جودة البيانات
;WITH InvalidRecords AS (
{validation_sql}
),
Metrics AS (
    SELECT 
        (SELECT COUNT(*) FROM InvalidRecords) AS TotalInvalid,
        (SELECT COUNT(*) FROM {full_table}) AS TotalRecords
)
SELECT 
    TotalInvalid AS [Total Invalid Records],
    TotalRecords AS [Total Records],
    CASE 
        WHEN TotalRecords > 0 
        THEN CAST(CAST(TotalInvalid AS FLOAT) / TotalRecords * 100 AS DECIMAL(5,2))
        ELSE 0 
    END AS [Invalid Records %]
FROM Metrics"""
