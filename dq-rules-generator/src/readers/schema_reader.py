"""
Database Schema Reader
======================

Reads database schema from SQL scripts or backup files
to extract table structures and relationships.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from loguru import logger

from ..models.table_model import TableModel, ColumnModel


class SchemaReader:
    """
    Reads database schema from SQL DDL scripts.
    
    Supports:
    - CREATE TABLE statements
    - PRIMARY KEY constraints
    - FOREIGN KEY constraints
    - UNIQUE constraints
    """
    
    def __init__(self, file_path: str):
        """
        Initialize reader with SQL script path.
        
        Args:
            file_path: Path to SQL DDL script
        """
        self.file_path = Path(file_path)
        self._content: str = ""
        
    def read(self) -> List[TableModel]:
        """
        Read SQL schema and return list of TableModel objects.
        
        Returns:
            List of TableModel objects with their columns
        """
        logger.info(f"Reading schema from: {self.file_path}")
        
        # Read file content
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self._content = f.read()
        except UnicodeDecodeError:
            with open(self.file_path, 'r', encoding='latin-1') as f:
                self._content = f.read()
        
        # Parse CREATE TABLE statements
        tables = self._parse_create_tables()
        
        # Parse constraints (FK, etc.)
        self._parse_constraints(tables)
        
        logger.info(f"Loaded {len(tables)} tables from schema")
        return tables
    
    def _parse_create_tables(self) -> List[TableModel]:
        """Parse CREATE TABLE statements from SQL content"""
        tables = []
        
        # Regex pattern for CREATE TABLE
        # Handles: CREATE TABLE [schema].[table] or CREATE TABLE schema.table or CREATE TABLE table
        create_pattern = re.compile(
            r'CREATE\s+TABLE\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?\s*\((.*?)\)\s*;?',
            re.IGNORECASE | re.DOTALL
        )
        
        for match in create_pattern.finditer(self._content):
            schema_name = match.group(1) or 'dbo'
            table_name = match.group(2)
            columns_block = match.group(3)
            
            # Parse columns
            columns = self._parse_columns(columns_block)
            
            # Create table model
            table = TableModel(
                schema_name=schema_name,
                table_name=table_name,
                columns=columns
            )
            
            # Extract primary keys from columns
            for col in columns:
                if col.is_primary_key:
                    table.primary_key_columns.append(col.name)
            
            tables.append(table)
        
        return tables
    
    def _parse_columns(self, columns_block: str) -> List[ColumnModel]:
        """Parse column definitions from CREATE TABLE body"""
        columns = []
        
        # Split by comma, but be careful with nested parentheses
        lines = self._smart_split(columns_block)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip constraint definitions
            if any(kw in line.upper() for kw in ['CONSTRAINT', 'PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE', 'CHECK', 'INDEX']):
                continue
            
            # Parse column definition
            column = self._parse_column_line(line)
            if column:
                columns.append(column)
        
        return columns
    
    def _parse_column_line(self, line: str) -> Optional[ColumnModel]:
        """Parse a single column definition line"""
        # Pattern: [column_name] data_type(size) [NULL|NOT NULL] [PRIMARY KEY] [DEFAULT value]
        pattern = re.compile(
            r'^\[?(\w+)\]?\s+(\w+(?:\([^)]+\))?)\s*(.*?)$',
            re.IGNORECASE
        )
        
        match = pattern.match(line)
        if not match:
            return None
        
        col_name = match.group(1)
        data_type = match.group(2)
        modifiers = match.group(3).upper() if match.group(3) else ""
        
        # Parse modifiers
        is_nullable = 'NOT NULL' not in modifiers
        is_primary_key = 'PRIMARY KEY' in modifiers
        is_unique = 'UNIQUE' in modifiers
        
        # Extract length from data type
        max_length = None
        if '(' in data_type:
            try:
                length_str = data_type.split('(')[1].split(')')[0]
                if ',' not in length_str:
                    max_length = int(length_str)
            except:
                pass
        
        return ColumnModel(
            name=col_name,
            data_type=data_type,
            is_nullable=is_nullable,
            is_primary_key=is_primary_key,
            is_unique=is_unique,
            max_length=max_length
        )
    
    def _parse_constraints(self, tables: List[TableModel]):
        """Parse ALTER TABLE constraints and update table models"""
        # Dictionary for quick table lookup
        table_dict = {t.full_name.lower(): t for t in tables}
        table_dict.update({t.table_name.lower(): t for t in tables})
        
        # Pattern for ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY
        fk_pattern = re.compile(
            r'ALTER\s+TABLE\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?\s+.*?'
            r'FOREIGN\s+KEY\s*\(\s*\[?(\w+)\]?\s*\)\s*'
            r'REFERENCES\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?\s*\(\s*\[?(\w+)\]?\s*\)',
            re.IGNORECASE | re.DOTALL
        )
        
        for match in fk_pattern.finditer(self._content):
            schema = match.group(1) or 'dbo'
            table_name = match.group(2)
            column_name = match.group(3)
            ref_schema = match.group(4) or 'dbo'
            ref_table = match.group(5)
            ref_column = match.group(6)
            
            # Find source table
            table_key = f"{schema}.{table_name}".lower()
            if table_key in table_dict:
                table = table_dict[table_key]
                table.foreign_keys[column_name] = (
                    f"{ref_schema}.{ref_table}",
                    ref_column
                )
                
                # Update column
                col = table.get_column(column_name)
                if col:
                    col.is_foreign_key = True
                    col.references_table = f"{ref_schema}.{ref_table}"
                    col.references_column = ref_column
            elif table_name.lower() in table_dict:
                table = table_dict[table_name.lower()]
                table.foreign_keys[column_name] = (ref_table, ref_column)
    
    def _smart_split(self, text: str) -> List[str]:
        """Split by comma, respecting nested parentheses"""
        result = []
        current = ""
        depth = 0
        
        for char in text:
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
            elif char == ',' and depth == 0:
                result.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            result.append(current.strip())
        
        return result
