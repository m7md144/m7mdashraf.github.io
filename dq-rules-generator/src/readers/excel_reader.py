"""
Excel Data Dictionary Reader
============================

Reads Data Dictionary from Excel files and converts
to internal TableModel/ColumnModel representations.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Any
from loguru import logger

from ..models.table_model import TableModel, ColumnModel, DataSensitivity


class DataDictionaryReader:
    """
    Reads Data Dictionary from Excel files.
    
    Expected columns (flexible mapping):
    - Schema Name
    - Table Name  
    - Table Description
    - Column Name
    - Column Description
    - Data Type
    - Is Nullable
    - Is Primary Key
    - Is Foreign Key
    - Reference Table
    - Reference Column
    """
    
    # Column name mappings (flexible detection)
    COLUMN_MAPPINGS = {
        'schema_name': ['schema', 'schema_name', 'schema name', 'owner', 'المخطط'],
        'table_name': ['table', 'table_name', 'table name', 'tablename', 'الجدول', 'اسم الجدول'],
        'table_description': ['table_description', 'table description', 'table_desc', 'tabledesc', 'وصف الجدول'],
        'column_name': ['column', 'column_name', 'column name', 'columnname', 'field', 'العمود', 'اسم العمود', 'الحقل'],
        'column_description': ['column_description', 'column description', 'column_desc', 'description', 'desc', 'وصف العمود', 'الوصف'],
        'data_type': ['data_type', 'datatype', 'data type', 'type', 'نوع البيانات'],
        'is_nullable': ['nullable', 'is_nullable', 'is nullable', 'null', 'allow null', 'قابل للفراغ'],
        'is_primary_key': ['pk', 'primary_key', 'is_pk', 'ispk', 'primary key', 'المفتاح الأساسي'],
        'is_foreign_key': ['fk', 'foreign_key', 'is_fk', 'isfk', 'foreign key', 'المفتاح الأجنبي'],
        'is_unique': ['unique', 'is_unique', 'isunique', 'فريد'],
        'reference_table': ['ref_table', 'reference_table', 'referenced_table', 'fk_table', 'جدول المرجع'],
        'reference_column': ['ref_column', 'reference_column', 'referenced_column', 'fk_column', 'عمود المرجع'],
        'max_length': ['length', 'max_length', 'maxlength', 'size', 'الطول'],
        'sensitivity': ['sensitivity', 'classification', 'data_classification', 'الحساسية', 'التصنيف']
    }
    
    def __init__(self, file_path: str, sheet_name: Optional[str] = None):
        """
        Initialize reader with Excel file path.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Specific sheet to read (optional)
        """
        self.file_path = Path(file_path)
        self.sheet_name = sheet_name
        self.column_map: Dict[str, str] = {}
        self._df: Optional[pd.DataFrame] = None
        
    def read(self) -> List[TableModel]:
        """
        Read Data Dictionary and return list of TableModel objects.
        
        Returns:
            List of TableModel objects with their columns
        """
        logger.info(f"Reading Data Dictionary from: {self.file_path}")
        
        # Read Excel file
        try:
            if self.sheet_name:
                self._df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
            else:
                # Try to read first sheet
                self._df = pd.read_excel(self.file_path)
        except Exception as e:
            logger.error(f"Failed to read Excel file: {e}")
            raise
        
        # Map columns
        self._detect_columns()
        
        # Parse into TableModel objects
        tables = self._parse_tables()
        
        logger.info(f"Loaded {len(tables)} tables with {sum(len(t.columns) for t in tables)} columns")
        return tables
    
    def _detect_columns(self):
        """Auto-detect column mappings from DataFrame headers"""
        if self._df is None:
            return
        
        df_columns = [str(c).lower().strip() for c in self._df.columns]
        
        for internal_name, patterns in self.COLUMN_MAPPINGS.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                for i, col in enumerate(df_columns):
                    if pattern_lower == col or pattern_lower in col:
                        self.column_map[internal_name] = self._df.columns[i]
                        break
                if internal_name in self.column_map:
                    break
        
        # Log detected mappings
        logger.debug(f"Detected column mappings: {self.column_map}")
        
        # Validate required columns
        required = ['table_name', 'column_name', 'data_type']
        missing = [r for r in required if r not in self.column_map]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
    
    def _get_value(self, row: pd.Series, internal_name: str, default: Any = "") -> Any:
        """Get value from row using mapped column name"""
        if internal_name not in self.column_map:
            return default
        
        col_name = self.column_map[internal_name]
        value = row.get(col_name, default)
        
        if pd.isna(value):
            return default
        return value
    
    def _parse_bool(self, value: Any) -> bool:
        """Parse boolean value from various formats"""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.lower() in ['yes', 'y', 'true', '1', 'نعم', 'صحيح']
        return False
    
    def _parse_tables(self) -> List[TableModel]:
        """Parse DataFrame rows into TableModel objects"""
        if self._df is None:
            return []
        
        tables_dict: Dict[str, TableModel] = {}
        
        for _, row in self._df.iterrows():
            schema_name = str(self._get_value(row, 'schema_name', 'dbo'))
            table_name = str(self._get_value(row, 'table_name'))
            
            if not table_name or table_name == 'nan':
                continue
            
            # Create table key
            table_key = f"{schema_name}.{table_name}"
            
            # Get or create table
            if table_key not in tables_dict:
                tables_dict[table_key] = TableModel(
                    schema_name=schema_name,
                    table_name=table_name,
                    description=str(self._get_value(row, 'table_description', ''))
                )
            
            table = tables_dict[table_key]
            
            # Create column
            column_name = str(self._get_value(row, 'column_name'))
            if not column_name or column_name == 'nan':
                continue
            
            # Parse data type and extract length
            data_type = str(self._get_value(row, 'data_type', 'varchar'))
            max_length = None
            if '(' in data_type:
                try:
                    length_str = data_type.split('(')[1].split(')')[0]
                    if ',' in length_str:  # decimal(18,2)
                        parts = length_str.split(',')
                        max_length = int(parts[0])
                    else:
                        max_length = int(length_str)
                except:
                    pass
            
            # Parse sensitivity
            sensitivity_str = str(self._get_value(row, 'sensitivity', 'low')).lower()
            if 'high' in sensitivity_str or 'عالية' in sensitivity_str or 'سري' in sensitivity_str:
                sensitivity = DataSensitivity.HIGH
            elif 'medium' in sensitivity_str or 'متوسط' in sensitivity_str:
                sensitivity = DataSensitivity.MEDIUM
            elif 'confidential' in sensitivity_str or 'سرية' in sensitivity_str:
                sensitivity = DataSensitivity.CONFIDENTIAL
            else:
                sensitivity = DataSensitivity.LOW
            
            column = ColumnModel(
                name=column_name,
                data_type=data_type,
                description=str(self._get_value(row, 'column_description', '')),
                is_nullable=self._parse_bool(self._get_value(row, 'is_nullable', True)),
                is_primary_key=self._parse_bool(self._get_value(row, 'is_primary_key', False)),
                is_foreign_key=self._parse_bool(self._get_value(row, 'is_foreign_key', False)),
                is_unique=self._parse_bool(self._get_value(row, 'is_unique', False)),
                max_length=max_length,
                references_table=str(self._get_value(row, 'reference_table', '')) or None,
                references_column=str(self._get_value(row, 'reference_column', '')) or None,
                sensitivity=sensitivity
            )
            
            # Update table's primary key list
            if column.is_primary_key:
                table.primary_key_columns.append(column.name)
            
            # Update table's foreign key dict
            if column.is_foreign_key and column.references_table:
                table.foreign_keys[column.name] = (
                    column.references_table,
                    column.references_column or column.name
                )
            
            table.columns.append(column)
        
        return list(tables_dict.values())
    
    def get_sheet_names(self) -> List[str]:
        """Get list of available sheet names in the Excel file"""
        xl = pd.ExcelFile(self.file_path)
        return xl.sheet_names
