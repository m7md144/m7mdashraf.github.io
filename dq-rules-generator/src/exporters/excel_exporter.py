"""
Excel Exporter
==============

Exports generated DQ rules to formatted Excel files.

Output format follows the exact column order:
System | Database | Schema | Tables | Columns | Dimension | Rule Description | 
Issue Description | Rule SQL Script | Related Tables | Related Columns | 
Total Invalid Records | Total Records | Invalid Records % | Root Cause | 
Severity | Recommendation | DQ Check Date | Workflows | Rule Type
"""

from typing import List, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd
from loguru import logger

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils.dataframe import dataframe_to_rows
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False
    logger.warning("openpyxl not installed - Excel formatting will be limited")

from ..models.rule_model import DQRule


class ExcelExporter:
    """
    Exports DQ rules to formatted Excel files.
    
    Features:
    - Exact column order as specified
    - Professional formatting (headers, alignment, etc.)
    - RTL support for Arabic text
    - Conditional formatting for severity
    - Summary statistics sheet
    """
    
    # Column widths for better readability
    COLUMN_WIDTHS = {
        "System": 15,
        "Database": 15,
        "Schema": 12,
        "Tables": 25,
        "Columns": 25,
        "Dimension": 15,
        "Rule Description": 60,
        "Issue Description": 50,
        "Rule SQL Script": 80,
        "Related Tables": 25,
        "Related Columns": 25,
        "Total Invalid Records": 18,
        "Total Records": 15,
        "Invalid Records %": 15,
        "Root Cause": 45,
        "Severity": 12,
        "Recommendation": 50,
        "DQ Check Date": 15,
        "Workflows": 30,
        "Rule Type": 15
    }
    
    # Severity colors
    SEVERITY_COLORS = {
        "High": "FF6B6B",      # Red
        "Medium": "FFD93D",    # Yellow
        "Low": "6BCB77"        # Green
    }
    
    # Dimension colors
    DIMENSION_COLORS = {
        "Completeness": "E8F4FD",
        "Validity": "FFF3E0",
        "Consistency": "F3E5F5",
        "Uniqueness": "E8F5E9",
        "Timeliness": "FFF8E1",
        "Accuracy": "FCE4EC"
    }
    
    def __init__(self, output_path: str):
        """
        Initialize the exporter.
        
        Args:
            output_path: Path for output Excel file
        """
        self.output_path = Path(output_path)
    
    def export(self, rules: List[DQRule], include_summary: bool = True) -> str:
        """
        Export rules to Excel file.
        
        Args:
            rules: List of DQRule objects
            include_summary: Whether to include summary statistics sheet
            
        Returns:
            Path to created Excel file
        """
        logger.info(f"Exporting {len(rules)} rules to Excel")
        
        # Convert rules to DataFrame
        df = self._rules_to_dataframe(rules)
        
        if HAS_OPENPYXL:
            self._export_formatted(df, rules, include_summary)
        else:
            self._export_simple(df)
        
        logger.info(f"Excel file created: {self.output_path}")
        return str(self.output_path)
    
    def _rules_to_dataframe(self, rules: List[DQRule]) -> pd.DataFrame:
        """Convert rules to DataFrame with exact column order"""
        rows = [rule.to_excel_row() for rule in rules]
        df = pd.DataFrame(rows)
        
        # Ensure exact column order
        columns = DQRule.get_excel_columns()
        
        # Add any missing columns
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        
        return df[columns]
    
    def _export_formatted(
        self, 
        df: pd.DataFrame, 
        rules: List[DQRule],
        include_summary: bool
    ):
        """Export with formatting using openpyxl"""
        wb = Workbook()
        
        # Create main rules sheet
        ws = wb.active
        ws.title = "DQ Rules"
        
        # Write headers
        headers = df.columns.tolist()
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="2E86AB", end_color="2E86AB", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Write data rows
        for row_idx, (_, row) in enumerate(df.iterrows(), 2):
            for col_idx, (header, value) in enumerate(row.items(), 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                
                # Apply Arabic text alignment (RTL)
                if header in ["Rule Description", "Issue Description", "Root Cause", "Recommendation"]:
                    cell.alignment = Alignment(
                        horizontal="right", 
                        vertical="top", 
                        wrap_text=True,
                        reading_order=2  # RTL
                    )
                elif header == "Rule SQL Script":
                    cell.alignment = Alignment(
                        horizontal="left",
                        vertical="top",
                        wrap_text=True
                    )
                    cell.font = Font(name="Consolas", size=9)
                else:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                
                # Apply severity coloring
                if header == "Severity" and value in self.SEVERITY_COLORS:
                    cell.fill = PatternFill(
                        start_color=self.SEVERITY_COLORS[value],
                        end_color=self.SEVERITY_COLORS[value],
                        fill_type="solid"
                    )
                
                # Apply dimension coloring
                if header == "Dimension" and value in self.DIMENSION_COLORS:
                    cell.fill = PatternFill(
                        start_color=self.DIMENSION_COLORS[value],
                        end_color=self.DIMENSION_COLORS[value],
                        fill_type="solid"
                    )
        
        # Set column widths
        for col_idx, header in enumerate(headers, 1):
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = \
                self.COLUMN_WIDTHS.get(header, 15)
        
        # Freeze header row
        ws.freeze_panes = "A2"
        
        # Add filters
        ws.auto_filter.ref = ws.dimensions
        
        # Add summary sheet if requested
        if include_summary:
            self._add_summary_sheet(wb, rules, df)
        
        # Save workbook
        wb.save(self.output_path)
    
    def _add_summary_sheet(self, wb: Workbook, rules: List[DQRule], df: pd.DataFrame):
        """Add summary statistics sheet"""
        ws = wb.create_sheet("Summary")
        
        # Title
        ws.merge_cells("A1:D1")
        title_cell = ws.cell(row=1, column=1, value="ملخص قواعد جودة البيانات")
        title_cell.font = Font(bold=True, size=16)
        title_cell.alignment = Alignment(horizontal="center")
        
        # Generation timestamp
        ws.cell(row=2, column=1, value=f"تاريخ التوليد: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        row = 4
        
        # Total rules
        ws.cell(row=row, column=1, value="إجمالي القواعد:")
        ws.cell(row=row, column=2, value=len(rules))
        row += 2
        
        # Rules by Dimension
        ws.cell(row=row, column=1, value="القواعد حسب البعد:")
        ws.cell(row=row, column=1).font = Font(bold=True)
        row += 1
        
        for dimension, count in df["Dimension"].value_counts().items():
            ws.cell(row=row, column=1, value=dimension)
            ws.cell(row=row, column=2, value=count)
            row += 1
        
        row += 1
        
        # Rules by Severity
        ws.cell(row=row, column=1, value="القواعد حسب الأهمية:")
        ws.cell(row=row, column=1).font = Font(bold=True)
        row += 1
        
        for severity, count in df["Severity"].value_counts().items():
            cell_sev = ws.cell(row=row, column=1, value=severity)
            if severity in self.SEVERITY_COLORS:
                cell_sev.fill = PatternFill(
                    start_color=self.SEVERITY_COLORS[severity],
                    end_color=self.SEVERITY_COLORS[severity],
                    fill_type="solid"
                )
            ws.cell(row=row, column=2, value=count)
            row += 1
        
        row += 1
        
        # Rules by Rule Type
        ws.cell(row=row, column=1, value="القواعد حسب النوع:")
        ws.cell(row=row, column=1).font = Font(bold=True)
        row += 1
        
        for rule_type, count in df["Rule Type"].value_counts().items():
            ws.cell(row=row, column=1, value=rule_type)
            ws.cell(row=row, column=2, value=count)
            row += 1
        
        row += 1
        
        # Rules by Table
        ws.cell(row=row, column=1, value="القواعد حسب الجدول:")
        ws.cell(row=row, column=1).font = Font(bold=True)
        row += 1
        
        for table, count in df["Tables"].value_counts().head(10).items():
            ws.cell(row=row, column=1, value=table)
            ws.cell(row=row, column=2, value=count)
            row += 1
        
        # Set column widths
        ws.column_dimensions["A"].width = 30
        ws.column_dimensions["B"].width = 15
    
    def _export_simple(self, df: pd.DataFrame):
        """Export without formatting (fallback when openpyxl not available)"""
        df.to_excel(self.output_path, index=False, engine='openpyxl')
    
    def export_with_sql_scripts(
        self, 
        rules: List[DQRule],
        output_sql_path: Optional[str] = None
    ) -> str:
        """
        Export rules to Excel and SQL scripts file.
        
        Args:
            rules: List of DQRule objects
            output_sql_path: Optional path for SQL scripts file
            
        Returns:
            Path to SQL scripts file
        """
        # Export Excel
        self.export(rules)
        
        # Generate SQL file
        if not output_sql_path:
            output_sql_path = self.output_path.with_suffix('.sql')
        
        with open(output_sql_path, 'w', encoding='utf-8') as f:
            f.write("-- ================================================\n")
            f.write("-- DQ Rules Validation SQL Scripts\n")
            f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"-- Total Rules: {len(rules)}\n")
            f.write("-- ================================================\n\n")
            
            for i, rule in enumerate(rules, 1):
                f.write(f"-- ------------------------------------------------\n")
                f.write(f"-- Rule {i}: {rule.table}.{rule.column} ({rule.dimension.value})\n")
                f.write(f"-- {rule.rule_description}\n")
                f.write(f"-- ------------------------------------------------\n")
                f.write(rule.sql_script)
                f.write("\n\n")
        
        logger.info(f"SQL scripts file created: {output_sql_path}")
        return str(output_sql_path)
