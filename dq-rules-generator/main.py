"""
DQ Rules Generator - Main Application
=====================================

A local application that analyzes database schemas and data dictionaries
to generate comprehensive Data Quality and Business Rules.

This is NOT a chatbot or AI agent - it's a deterministic rule generator
that uses pattern matching and business context analysis.

Usage:
    python main.py --input data_dictionary.xlsx --output rules.xlsx
    python main.py --input data_dictionary.xlsx --config config.yaml
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
logger.add("dq_rules_generator.log", rotation="10 MB", level="DEBUG")

from src.readers.excel_reader import DataDictionaryReader
from src.readers.schema_reader import SchemaReader
from src.analyzers.business_context_analyzer import BusinessContextAnalyzer
from src.analyzers.relationship_inference_engine import RelationshipInferenceEngine
from src.engines.rule_generator import RuleGenerator
from src.exporters.excel_exporter import ExcelExporter
from src.utils.config import Config


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="DQ Rules Generator - Generate Data Quality and Business Rules from Data Dictionary",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --input data_dictionary.xlsx --output rules.xlsx
  python main.py --input data_dictionary.xlsx --system "HR System" --database "HRDB"
  python main.py --input data_dictionary.xlsx --config config.yaml

Output:
  - Excel file with DQ rules in the specified format
  - SQL scripts file for validation queries
  - Summary statistics
        """
    )
    
    # Input arguments
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to Data Dictionary Excel file"
    )
    parser.add_argument(
        "--sheet",
        help="Specific sheet name to read (optional)"
    )
    parser.add_argument(
        "--schema-file",
        help="Optional SQL schema file for additional FK information"
    )
    
    # Output arguments
    parser.add_argument(
        "--output", "-o",
        default="dq_rules_output.xlsx",
        help="Output Excel file path (default: dq_rules_output.xlsx)"
    )
    parser.add_argument(
        "--output-sql",
        help="Output SQL scripts file path (optional)"
    )
    
    # Configuration arguments
    parser.add_argument(
        "--config", "-c",
        help="Configuration file (YAML or JSON)"
    )
    parser.add_argument(
        "--system",
        default="System",
        help="System name for output"
    )
    parser.add_argument(
        "--database",
        default="Database",
        help="Database name for output"
    )
    parser.add_argument(
        "--timeliness-threshold",
        type=int,
        default=30,
        help="Days threshold for timeliness checks (default: 30)"
    )
    parser.add_argument(
        "--critical-fields",
        nargs="+",
        default=[],
        help="List of business-critical field names"
    )
    
    # Behavior flags
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Don't include summary sheet in output"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Adjust logging level
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
    
    # Load configuration
    config = Config()
    if args.config:
        config_path = Path(args.config)
        if config_path.suffix in ['.yaml', '.yml']:
            config = Config.from_yaml(args.config)
        elif config_path.suffix == '.json':
            config = Config.from_json(args.config)
        else:
            logger.error(f"Unsupported config format: {config_path.suffix}")
            sys.exit(1)
    
    # Override config with command line arguments
    config.system_name = args.system
    config.database_name = args.database
    config.timeliness_threshold_days = args.timeliness_threshold
    if args.critical_fields:
        config.critical_fields = args.critical_fields
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("DQ Rules Generator")
    logger.info("=" * 60)
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {args.output}")
    logger.info(f"System: {config.system_name}")
    logger.info(f"Database: {config.database_name}")
    logger.info("=" * 60)
    
    try:
        # Step 1: Read Data Dictionary
        logger.info("Step 1: Reading Data Dictionary...")
        reader = DataDictionaryReader(str(input_path), sheet_name=args.sheet)
        tables = reader.read()
        logger.info(f"  Loaded {len(tables)} tables with {sum(len(t.columns) for t in tables)} columns")
        
        # Step 1.5: Read schema file if provided
        if args.schema_file:
            logger.info("Step 1.5: Reading Schema file...")
            schema_reader = SchemaReader(args.schema_file)
            schema_tables = schema_reader.read()
            
            # Merge FK information from schema
            schema_dict = {t.table_name.lower(): t for t in schema_tables}
            for table in tables:
                if table.table_name.lower() in schema_dict:
                    schema_table = schema_dict[table.table_name.lower()]
                    for col_name, (ref_table, ref_col) in schema_table.foreign_keys.items():
                        if col_name not in table.foreign_keys:
                            table.foreign_keys[col_name] = (ref_table, ref_col)
                            col = table.get_column(col_name)
                            if col:
                                col.is_foreign_key = True
                                col.references_table = ref_table
                                col.references_column = ref_col
            
            logger.info(f"  Merged FK information from schema")
        
        # Step 2: Generate Rules
        logger.info("Step 2: Generating DQ Rules...")
        generator = RuleGenerator(
            system_name=config.system_name,
            database_name=config.database_name,
            timeliness_threshold_days=config.timeliness_threshold_days,
            critical_fields=config.critical_fields
        )
        rules = generator.generate(tables)
        logger.info(f"  Generated {len(rules)} rules")
        
        # Summary by dimension
        dimension_counts = {}
        for rule in rules:
            dim = rule.dimension.value
            dimension_counts[dim] = dimension_counts.get(dim, 0) + 1
        for dim, count in sorted(dimension_counts.items()):
            logger.info(f"    - {dim}: {count} rules")
        
        # Step 3: Export to Excel
        logger.info("Step 3: Exporting to Excel...")
        exporter = ExcelExporter(args.output)
        
        if args.output_sql:
            exporter.export_with_sql_scripts(rules, args.output_sql)
        else:
            exporter.export(rules, include_summary=not args.no_summary)
        
        logger.info("=" * 60)
        logger.info("✓ Rule generation completed successfully!")
        logger.info(f"  Output file: {args.output}")
        if args.output_sql:
            logger.info(f"  SQL file: {args.output_sql}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
