# Data Quality Rules Generator - Technical Specification Document

## Executive Summary

This document provides a comprehensive technical design and operational specification for a lightweight Windows Desktop application that generates Data Quality (DQ) rules and Business Rules from Excel-based Data Dictionary files. The application transforms static Data Dictionary documentation into an active Operational Governance Tool, empowering data teams to discover quality issues, standardize rules, ensure regulatory compliance, and enhance decision-making.

**Compliance Standards:** DAMA-DMBOK, Sadaia/NDMO, ISO 8000

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [User Flow](#2-user-flow)
3. [Rule Generation Algorithm](#3-rule-generation-algorithm)
4. [Pseudocode](#4-pseudocode)
5. [Column Mapping Strategy](#5-column-mapping-strategy)
6. [Severity Logic](#6-severity-logic)
7. [Rule Examples](#7-rule-examples)
8. [Cross-Table Rule Example](#8-cross-table-rule-example)
9. [Future Improvement Suggestions](#9-future-improvement-suggestions)

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DQ RULES GENERATOR APPLICATION                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────┐   │
│  │   PRESENTATION   │    │   BUSINESS       │    │   DATA ACCESS        │   │
│  │      LAYER       │◄──►│     LAYER        │◄──►│      LAYER           │   │
│  │                  │    │                  │    │                      │   │
│  │  • Main Window   │    │  • Rule Engine   │    │  • Excel Reader      │   │
│  │  • File Selector │    │  • Semantic      │    │  • Excel Writer      │   │
│  │  • Column Mapper │    │    Analyzer      │    │  • Schema Parser     │   │
│  │  • Settings Panel│    │  • SQL Generator │    │  • Relationship      │   │
│  │  • Preview Grid  │    │  • Severity      │    │    Detector          │   │
│  │  • Log Viewer    │    │    Classifier    │    │                      │   │
│  │                  │    │  • Arabic        │    │                      │   │
│  │                  │    │    Content Gen   │    │                      │   │
│  └──────────────────┘    └──────────────────┘    └──────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        CORE SERVICES                                  │   │
│  │  • Configuration Manager  • Logging Service  • Validation Service    │   │
│  │  • Template Engine        • Export Manager   • Error Handler         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Architecture

#### 1.2.1 Presentation Layer
- **Technology:** WPF (Windows Presentation Foundation) with MVVM pattern
- **Components:**
  - Main Application Window
  - File Selection Module (Excel file browser, sheet selector)
  - Column Mapping Interface (drag-and-drop mapping)
  - Settings Configuration Panel
  - Rule Preview DataGrid
  - Export Progress Indicator
  - Log/Warning Viewer

#### 1.2.2 Business Logic Layer
- **Rule Engine Core:** Central orchestrator for rule generation
- **Semantic Analyzer:** Interprets column descriptions, table contexts, and sensitivity classifications
- **SQL Script Generator:** Produces SQL Server-compatible validation queries
- **Severity Classifier:** Assigns High/Medium/Low severity based on context
- **Arabic Content Generator:** Produces formal Arabic descriptions for designated fields
- **Cross-Table Analyzer:** Identifies relationships and generates JOIN-based rules

#### 1.2.3 Data Access Layer
- **Excel Reader:** Parses input Data Dictionary files using EPPlus/ClosedXML
- **Excel Writer:** Generates output files with strict column ordering
- **Schema Parser:** Extracts metadata (data types, keys, constraints)
- **Relationship Detector:** Identifies FK relationships and common fields

### 1.3 Data Flow Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   INPUT     │     │    PROCESSING   │     │    OUTPUT       │
│   PHASE     │────►│      PHASE      │────►│    PHASE        │
└─────────────┘     └─────────────────┘     └─────────────────┘
      │                     │                       │
      ▼                     ▼                       ▼
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Excel Data  │     │ Semantic        │     │ Excel Output    │
│ Dictionary  │     │ Analysis        │     │ (20 Columns)    │
├─────────────┤     ├─────────────────┤     ├─────────────────┤
│ • System    │     │ • Context       │     │ • DQ Rules      │
│ • Database  │     │   Extraction    │     │ • Business      │
│ • Schema    │     │ • Rule          │     │   Rules         │
│ • Tables    │     │   Generation    │     │ • SQL Scripts   │
│ • Columns   │     │ • SQL Creation  │     │ • Arabic        │
│ • Types     │     │ • Severity      │     │   Descriptions  │
│ • Keys      │     │   Assignment    │     │ • Metrics       │
│ • Sensitivity│    │ • Cross-Table   │     │   Placeholders  │
└─────────────┘     │   Analysis      │     └─────────────────┘
                    └─────────────────┘
```

### 1.4 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | .NET 6.0+ / .NET Framework 4.8 | Windows Desktop Runtime |
| UI Framework | WPF with MVVM | Enterprise-grade UI |
| Excel Processing | EPPlus / ClosedXML | Excel read/write operations |
| Logging | Serilog / NLog | Comprehensive logging |
| Dependency Injection | Microsoft.Extensions.DI | Service management |
| Configuration | JSON / XML Config | User settings persistence |

---

## 2. User Flow

### 2.1 Complete User Journey

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER WORKFLOW DIAGRAM                             │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────┐
    │  START  │
    └────┬────┘
         │
         ▼
┌─────────────────────┐
│ 1. Launch Application│
│    • Initialize UI   │
│    • Load settings   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐    ┌──────────────────┐
│ 2. Select Excel File │───►│ Validate File    │
│    • Browse files    │    │ Format           │
│    • Multi-sheet     │    └────────┬─────────┘
│      detection       │             │
└──────────────────────┘             │ Invalid
                                     ▼
                              ┌─────────────┐
                              │ Show Error  │
                              │ Message     │
                              └─────────────┘
           │ Valid
           ▼
┌─────────────────────┐
│ 3. Select Worksheet  │
│    • List available  │
│      sheets          │
│    • Preview data    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. Map Columns       │
│    • Auto-detect     │
│    • Manual mapping  │
│    • Validate        │
│      required fields │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 5. Configure Settings│
│    • DB Type (SQL    │
│      Server)         │
│    • Timeliness      │
│      threshold       │
│    • Critical fields │
│    • Output path     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 6. Generate Rules    │
│    • Process columns │
│    • Apply semantic  │
│      analysis        │
│    • Generate SQL    │
│    • Assign severity │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 7. Preview Results   │
│    • Review rules    │
│    • Check warnings  │
│    • Verify Arabic   │
│      content         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 8. Export to Excel   │
│    • Generate file   │
│    • Apply formatting│
│    • Save to path    │
└──────────┬──────────┘
           │
           ▼
    ┌─────────┐
    │   END   │
    └─────────┘
```

### 2.2 Step-by-Step User Actions

#### Step 1: Application Launch
- User launches the DQ Rules Generator application
- System initializes UI components and loads previous settings
- Welcome screen displays with quick-start options

#### Step 2: File Selection
- User clicks "Select File" button
- System opens file browser filtered to Excel files (.xlsx, .xls)
- User selects Data Dictionary Excel file
- System validates file structure and displays confirmation

#### Step 3: Worksheet Selection
- System displays list of available worksheets in the file
- User selects target worksheet containing Data Dictionary
- System loads preview of first 10 rows

#### Step 4: Column Mapping
- System attempts auto-detection of standard column names
- User reviews and adjusts mappings via drag-and-drop interface
- Required fields validated:
  - System Name
  - Database Name
  - Table Name
  - Column Name
  - Data Type
- Warning displayed for unmapped optional fields

#### Step 5: Settings Configuration
- **Database Type:** SQL Server (default)
- **Timeliness Threshold:** Days for timeliness check (default: 30)
- **Critical Fields:** User marks fields requiring High severity
- **Output Path:** Destination for generated Excel file

#### Step 6: Rule Generation
- User clicks "Generate Rules" button
- Progress bar displays processing status
- System processes each column and generates applicable rules
- Log panel shows generation activity

#### Step 7: Preview and Validation
- Generated rules displayed in sortable/filterable grid
- User can:
  - Filter by Dimension, Severity, Rule Type
  - Search rules by keyword
  - View full SQL scripts
  - Check Arabic content accuracy
- Warning panel highlights potential issues

#### Step 8: Export
- User clicks "Export to Excel" button
- System generates formatted Excel file with all 20 columns
- Success notification with file location
- Option to open file directly

---

## 3. Rule Generation Algorithm

### 3.1 Algorithm Overview

The Rule Generation Algorithm employs a multi-phase approach combining mandatory completeness checks with contextual rule inference based on data characteristics.

```
┌────────────────────────────────────────────────────────────────────────┐
│                    RULE GENERATION ALGORITHM FLOW                       │
└────────────────────────────────────────────────────────────────────────┘

    INPUT: Data Dictionary Column Record
                    │
                    ▼
    ┌───────────────────────────────┐
    │  PHASE 1: COMPLETENESS RULES  │  (Mandatory for ALL columns)
    │  • NULL Check                 │
    │  • Empty String Check         │
    │  • Whitespace-only Check      │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │  PHASE 2: DATA TYPE RULES     │  (Based on column data type)
    │  • Text: Length, Pattern      │
    │  • Numeric: Range, Format     │
    │  • Date: Range, Format        │
    │  • Boolean: Valid values      │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │  PHASE 3: CONSTRAINT RULES    │  (Based on key flags)
    │  • PK: Uniqueness             │
    │  • FK: Referential Integrity  │
    │  • Unique: Duplicate check    │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │  PHASE 4: SEMANTIC RULES      │  (Based on description/context)
    │  • Email validation           │
    │  • Phone format               │
    │  • ID patterns                │
    │  • Date logic                 │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │  PHASE 5: SENSITIVITY RULES   │  (Based on classification)
    │  • PDPL compliance            │
    │  • NDMO requirements          │
    │  • Encryption validation      │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │  PHASE 6: CROSS-TABLE RULES   │  (Based on relationships)
    │  • FK value existence         │
    │  • Data consistency           │
    │  • Business logic validation  │
    └───────────────┬───────────────┘
                    │
                    ▼
    OUTPUT: Collection of DQ Rules
```

### 3.2 Phase Details

#### Phase 1: Completeness Rules (Mandatory)

Every column receives the following completeness checks:

| Check Type | Dimension | Condition |
|------------|-----------|-----------|
| NULL Check | Completeness | Column IS NULL |
| Empty Check | Completeness | Column = '' |
| Whitespace Check | Completeness | LTRIM(RTRIM(Column)) = '' |

#### Phase 2: Data Type Rules

| Data Type | Rule Category | Dimension |
|-----------|---------------|-----------|
| VARCHAR/NVARCHAR | Length validation | Validity |
| VARCHAR/NVARCHAR | Pattern matching | Validity |
| INT/BIGINT/DECIMAL | Range validation | Validity |
| INT/BIGINT/DECIMAL | Numeric format | Validity |
| DATE/DATETIME | Date range | Validity |
| DATE/DATETIME | Future date check | Timeliness |
| BIT | Boolean values | Validity |

#### Phase 3: Constraint Rules

| Constraint | Rule Type | Dimension |
|------------|-----------|-----------|
| Primary Key | Uniqueness validation | Uniqueness |
| Foreign Key | Referential integrity | Consistency |
| Unique | Duplicate detection | Uniqueness |

#### Phase 4: Semantic Rules

Based on column name and description analysis:

| Pattern Detected | Rules Generated | Dimension |
|------------------|-----------------|-----------|
| Email | Format validation | Validity |
| Phone/Mobile | Format validation | Validity |
| National ID | Length + checksum | Validity |
| Date fields | Logical date rules | Validity/Timeliness |
| Status fields | Allowed values | Validity |
| Amount/Price | Positive value check | Validity |

#### Phase 5: Sensitivity Rules

| Classification | Rules Generated | Dimension |
|----------------|-----------------|-----------|
| PDPL-Sensitive | Data masking check | Accuracy |
| NDMO-Critical | Completeness enhanced | Completeness |
| High Sensitivity | Encryption validation | Accuracy |

#### Phase 6: Cross-Table Rules

| Relationship Type | Rules Generated | Dimension |
|-------------------|-----------------|-----------|
| FK Reference | Value existence in parent | Consistency |
| Common Fields | Value matching across tables | Consistency |
| Business Logic | Custom validation | Accuracy |

### 3.3 Rule Deduplication Logic

```
FOR each generated rule:
    IF rule.SQL_hash EXISTS in rule_collection:
        SKIP (avoid duplicate rules)
    ELSE IF rule.dimension + rule.column + rule.check_type EXISTS:
        SKIP (avoid semantic duplicates)
    ELSE:
        ADD rule to collection
```

---

## 4. Pseudocode

### 4.1 Main Processing Flow

```pseudocode
FUNCTION GenerateDQRules(inputFile, columnMapping, settings)
    
    // Initialize
    ruleCollection = new List<DQRule>()
    logService.Info("Starting rule generation process")
    
    // Load and parse Data Dictionary
    dataDictionary = ExcelReader.Load(inputFile)
    tables = ParseDataDictionary(dataDictionary, columnMapping)
    
    // Build relationship map
    relationshipMap = BuildRelationshipMap(tables)
    
    // Process each table
    FOR EACH table IN tables:
        logService.Info($"Processing table: {table.FullName}")
        
        // Process each column
        FOR EACH column IN table.Columns:
            columnRules = GenerateColumnRules(column, table, relationshipMap, settings)
            ruleCollection.AddRange(columnRules)
        END FOR
        
        // Generate cross-table rules
        crossTableRules = GenerateCrossTableRules(table, relationshipMap, settings)
        ruleCollection.AddRange(crossTableRules)
    END FOR
    
    // Post-processing
    ruleCollection = DeduplicateRules(ruleCollection)
    ruleCollection = AssignSeverity(ruleCollection, settings)
    ruleCollection = GenerateArabicContent(ruleCollection)
    
    RETURN ruleCollection
END FUNCTION
```

### 4.2 Column Rule Generation

```pseudocode
FUNCTION GenerateColumnRules(column, table, relationshipMap, settings)
    
    rules = new List<DQRule>()
    
    // PHASE 1: Mandatory Completeness Rules
    rules.Add(CreateCompletenessRule_NULL(column, table))
    rules.Add(CreateCompletenessRule_Empty(column, table))
    rules.Add(CreateCompletenessRule_Whitespace(column, table))
    
    // PHASE 2: Data Type Specific Rules
    SWITCH column.DataType:
        CASE "VARCHAR", "NVARCHAR", "CHAR", "NCHAR":
            rules.AddRange(GenerateTextRules(column, table))
            BREAK
        CASE "INT", "BIGINT", "DECIMAL", "NUMERIC", "FLOAT":
            rules.AddRange(GenerateNumericRules(column, table))
            BREAK
        CASE "DATE", "DATETIME", "DATETIME2":
            rules.AddRange(GenerateDateRules(column, table, settings))
            BREAK
        CASE "BIT":
            rules.AddRange(GenerateBooleanRules(column, table))
            BREAK
    END SWITCH
    
    // PHASE 3: Constraint-Based Rules
    IF column.IsPrimaryKey:
        rules.Add(CreateUniquenessRule(column, table))
    END IF
    
    IF column.IsForeignKey:
        rules.Add(CreateReferentialIntegrityRule(column, table, relationshipMap))
    END IF
    
    IF column.IsUnique:
        rules.Add(CreateDuplicateCheckRule(column, table))
    END IF
    
    // PHASE 4: Semantic Rules
    semanticContext = AnalyzeSemanticContext(column)
    rules.AddRange(GenerateSemanticRules(column, table, semanticContext))
    
    // PHASE 5: Sensitivity Rules
    IF column.SensitivityClassification != NULL:
        rules.AddRange(GenerateSensitivityRules(column, table))
    END IF
    
    RETURN rules
END FUNCTION
```

### 4.3 Semantic Context Analysis

```pseudocode
FUNCTION AnalyzeSemanticContext(column)
    
    context = new SemanticContext()
    
    // Analyze column name
    columnNameLower = column.Name.ToLower()
    descriptionLower = column.Description.ToLower()
    
    // Email detection
    IF columnNameLower CONTAINS "email" OR descriptionLower CONTAINS "بريد إلكتروني":
        context.IsEmail = TRUE
    END IF
    
    // Phone detection
    IF columnNameLower MATCHES "(phone|mobile|tel|fax)" 
       OR descriptionLower CONTAINS "هاتف" OR descriptionLower CONTAINS "جوال":
        context.IsPhone = TRUE
    END IF
    
    // National ID detection
    IF columnNameLower MATCHES "(national_id|citizen_id|iqama)" 
       OR descriptionLower CONTAINS "رقم الهوية":
        context.IsNationalID = TRUE
    END IF
    
    // Date context detection
    IF columnNameLower MATCHES "(birth|dob|created|modified|start|end)_date":
        context.DateContext = ExtractDateContext(columnNameLower)
    END IF
    
    // Status/Flag detection
    IF columnNameLower MATCHES "(status|state|flag|is_|has_)":
        context.IsStatusField = TRUE
        context.AllowedValues = InferAllowedValues(column)
    END IF
    
    // Amount/Financial detection
    IF columnNameLower MATCHES "(amount|price|cost|salary|balance|total)":
        context.IsFinancial = TRUE
    END IF
    
    RETURN context
END FUNCTION
```

### 4.4 SQL Script Generation

```pseudocode
FUNCTION GenerateSQLScript(rule)
    
    sql = new StringBuilder()
    
    // Build base validation query
    sql.Append("-- Rule: " + rule.RuleDescription)
    sql.AppendLine()
    sql.Append("SELECT ")
    
    // Select columns for invalid records
    sql.Append($"    [{rule.Column}],")
    sql.Append($"    '{rule.Dimension}' AS DQ_Dimension,")
    sql.Append($"    '{rule.RuleType}' AS Rule_Type")
    sql.AppendLine()
    
    // FROM clause
    sql.Append($"FROM [{rule.Database}].[{rule.Schema}].[{rule.Table}]")
    sql.AppendLine()
    
    // WHERE clause based on rule type
    sql.Append("WHERE ")
    sql.Append(BuildWhereClause(rule))
    sql.AppendLine()
    
    // Add metrics calculation wrapper
    metricsSQL = WrapWithMetricsCalculation(sql.ToString(), rule)
    
    RETURN metricsSQL
END FUNCTION

FUNCTION BuildWhereClause(rule)
    
    SWITCH rule.CheckType:
        CASE "NULL_CHECK":
            RETURN $"[{rule.Column}] IS NULL"
        
        CASE "EMPTY_CHECK":
            RETURN $"[{rule.Column}] = ''"
        
        CASE "WHITESPACE_CHECK":
            RETURN $"LTRIM(RTRIM([{rule.Column}])) = '' AND [{rule.Column}] IS NOT NULL"
        
        CASE "PATTERN_CHECK":
            RETURN $"[{rule.Column}] NOT LIKE '{rule.Pattern}'"
        
        CASE "RANGE_CHECK":
            RETURN $"[{rule.Column}] NOT BETWEEN {rule.MinValue} AND {rule.MaxValue}"
        
        CASE "UNIQUENESS_CHECK":
            RETURN $"[{rule.Column}] IN (SELECT [{rule.Column}] FROM [{rule.Table}] GROUP BY [{rule.Column}] HAVING COUNT(*) > 1)"
        
        CASE "FK_CHECK":
            RETURN $"[{rule.Column}] NOT IN (SELECT [{rule.ReferenceColumn}] FROM [{rule.ReferenceTable}])"
        
        CASE "FUTURE_DATE_CHECK":
            RETURN $"[{rule.Column}] > GETDATE()"
        
        DEFAULT:
            RETURN rule.CustomCondition
    END SWITCH
END FUNCTION
```

### 4.5 Arabic Content Generation

```pseudocode
FUNCTION GenerateArabicContent(rule)
    
    // Rule Description (وصف القاعدة)
    rule.RuleDescription_AR = GenerateRuleDescription(rule)
    
    // Issue Description (وصف المشكلة)
    rule.IssueDescription_AR = GenerateIssueDescription(rule)
    
    // Root Cause (السبب الجذري)
    rule.RootCause_AR = GenerateRootCause(rule)
    
    // Recommendation (التوصية)
    rule.Recommendation_AR = GenerateRecommendation(rule)
    
    RETURN rule
END FUNCTION

FUNCTION GenerateRuleDescription(rule)
    
    templates = LoadArabicTemplates()
    
    SWITCH rule.Dimension:
        CASE "Completeness":
            RETURN FormatTemplate(templates.Completeness.RuleDescription, 
                                  column: rule.Column, 
                                  table: rule.Table)
            // Example: "التحقق من اكتمال بيانات حقل {column} في جدول {table}"
        
        CASE "Validity":
            RETURN FormatTemplate(templates.Validity.RuleDescription,
                                  column: rule.Column,
                                  format: rule.ExpectedFormat)
            // Example: "التحقق من صحة تنسيق حقل {column} وفقاً للمعيار المحدد"
        
        CASE "Uniqueness":
            RETURN FormatTemplate(templates.Uniqueness.RuleDescription,
                                  column: rule.Column,
                                  table: rule.Table)
            // Example: "التحقق من تفرد قيم حقل {column} في جدول {table}"
        
        // ... other dimensions
    END SWITCH
END FUNCTION
```

### 4.6 Cross-Table Rule Generation

```pseudocode
FUNCTION GenerateCrossTableRules(table, relationshipMap, settings)
    
    rules = new List<DQRule>()
    
    // Get relationships for this table
    relationships = relationshipMap.GetRelationships(table)
    
    FOR EACH relationship IN relationships:
        
        // Referential Integrity Rule
        IF relationship.Type == "ForeignKey":
            rule = new DQRule()
            rule.Dimension = "Consistency"
            rule.Table = table.Name
            rule.Column = relationship.ForeignKeyColumn
            rule.RelatedTables = relationship.ReferencedTable
            rule.RelatedColumns = relationship.ReferencedColumn
            
            rule.SQLScript = GenerateFKValidationSQL(relationship)
            rules.Add(rule)
        END IF
        
        // Cross-table data consistency
        IF relationship.Type == "CommonField":
            rule = new DQRule()
            rule.Dimension = "Consistency"
            rule.Table = table.Name
            rule.Column = relationship.CommonColumn
            
            rule.SQLScript = GenerateCrossTableConsistencySQL(relationship)
            rules.Add(rule)
        END IF
        
        // Business logic validation
        IF relationship.HasBusinessLogic:
            businessRules = GenerateBusinessLogicRules(relationship, settings)
            rules.AddRange(businessRules)
        END IF
    END FOR
    
    RETURN rules
END FUNCTION
```

---

## 5. Column Mapping Strategy

### 5.1 Input Column Mapping

The application maps input Data Dictionary columns to internal processing fields:

| Input Column Name | Internal Field | Required | Auto-Detect Patterns |
|-------------------|----------------|----------|---------------------|
| System Name | SystemName | Yes | system, sys_name, application |
| Database Name | DatabaseName | Yes | database, db_name, catalog |
| Schema Name | SchemaName | No | schema, schema_name, owner |
| Table Name | TableName | Yes | table, table_name, entity |
| Table Description | TableDescription | No | table_desc, table_description |
| Column Name | ColumnName | Yes | column, column_name, field |
| Column Description | ColumnDescription | No | column_desc, description |
| Data Type | DataType | Yes | data_type, datatype, type |
| Nullable / Required | IsNullable | No | nullable, required, is_null |
| Key Flags (PK/FK/Unique) | KeyFlags | No | key, pk, fk, unique, constraint |
| Reference Table/Column | References | No | ref_table, reference, fk_ref |
| Allowed Values / Lookup | AllowedValues | No | allowed, lookup, values, domain |
| Sensitivity / PDPL / NDMO | Sensitivity | No | sensitivity, classification, pdpl |

### 5.2 Output Column Mapping

The output Excel file must contain exactly 20 columns in this order:

| # | Output Column | Source | Description |
|---|---------------|--------|-------------|
| 1 | System | Input.SystemName | Source system identifier |
| 2 | Database | Input.DatabaseName | Database name |
| 3 | Schema | Input.SchemaName | Schema/Owner name |
| 4 | Tables | Input.TableName | Table name |
| 5 | Columns | Input.ColumnName | Column name |
| 6 | Dimension | Generated | DQ Dimension (6 allowed values) |
| 7 | Rule Description | Generated (Arabic) | وصف القاعدة - Formal Arabic |
| 8 | Issue Description | Generated (Arabic) | وصف المشكلة - Formal Arabic |
| 9 | Rule SQL Script | Generated | SQL Server validation query |
| 10 | Related Tables | Generated | Referenced/joined tables |
| 11 | Related Columns | Generated | Referenced/joined columns |
| 12 | Total Invalid Records | Placeholder | To be filled after execution |
| 13 | Total Records | Placeholder | To be filled after execution |
| 14 | Invalid Records % | Placeholder | To be filled after execution |
| 15 | Root Cause | Generated (Arabic) | السبب الجذري - Formal Arabic |
| 16 | Severity | Generated | High / Medium / Low |
| 17 | Recommendation | Generated (Arabic) | التوصية - Formal Arabic |
| 18 | DQ Check Date | Generated | Rule generation timestamp |
| 19 | Workflows | Generated | Suggested workflow/process |
| 20 | Rule Type | Generated | Data Quality / Business Rule |

### 5.3 Column Mapping Algorithm

```pseudocode
FUNCTION AutoMapColumns(inputHeaders)
    
    mapping = new Dictionary<string, string>()
    
    FOR EACH header IN inputHeaders:
        normalizedHeader = NormalizeHeader(header)
        
        FOR EACH mappingPattern IN columnPatterns:
            IF normalizedHeader MATCHES mappingPattern.Pattern:
                mapping[mappingPattern.InternalField] = header
                BREAK
            END IF
        END FOR
    END FOR
    
    // Validate required fields
    requiredFields = ["SystemName", "DatabaseName", "TableName", "ColumnName", "DataType"]
    FOR EACH field IN requiredFields:
        IF NOT mapping.ContainsKey(field):
            THROW MissingRequiredFieldException(field)
        END IF
    END FOR
    
    RETURN mapping
END FUNCTION

FUNCTION NormalizeHeader(header)
    normalized = header.ToLower()
    normalized = RemoveSpecialCharacters(normalized)
    normalized = ReplaceSpacesWithUnderscore(normalized)
    RETURN normalized
END FUNCTION
```

### 5.4 Data Type Normalization

| Input Variations | Normalized Type | Category |
|------------------|-----------------|----------|
| varchar, varchar2, nvarchar, char, nchar, text | STRING | Text |
| int, integer, bigint, smallint, tinyint | INTEGER | Numeric |
| decimal, numeric, float, real, money | DECIMAL | Numeric |
| date, datetime, datetime2, smalldatetime | DATETIME | Date |
| bit, boolean, bool | BOOLEAN | Boolean |
| uniqueidentifier, guid | GUID | Identifier |
| binary, varbinary, image | BINARY | Binary |

---

## 6. Severity Logic

### 6.1 Severity Classification Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SEVERITY CLASSIFICATION MATRIX                      │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │           SEVERITY: HIGH            │
                    │                                     │
                    │  • Sensitive data (PDPL/NDMO)       │
                    │  • Primary Key violations           │
                    │  • Legal/Regulatory compliance      │
                    │  • Financial/Critical operations    │
                    │  • Customer-facing data             │
                    │  • Security-related fields          │
                    └─────────────────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────────┐
                    │          SEVERITY: MEDIUM           │
                    │                                     │
                    │  • Operational reporting impact     │
                    │  • Foreign Key violations           │
                    │  • Business process dependency      │
                    │  • Audit trail fields               │
                    │  • Integration data                 │
                    └─────────────────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────────────┐
                    │           SEVERITY: LOW             │
                    │                                     │
                    │  • Descriptive/Optional fields      │
                    │  • Non-critical metadata            │
                    │  • Limited operational impact       │
                    │  • Internal reference only          │
                    └─────────────────────────────────────┘
```

### 6.2 Severity Assignment Algorithm

```pseudocode
FUNCTION AssignSeverity(rule, settings)
    
    score = 0
    
    // Factor 1: Sensitivity Classification (Weight: 40%)
    IF rule.Column.Sensitivity IN ["High", "PDPL", "Confidential"]:
        score += 40
    ELSE IF rule.Column.Sensitivity IN ["Medium", "Internal"]:
        score += 20
    END IF
    
    // Factor 2: Key Constraints (Weight: 25%)
    IF rule.Column.IsPrimaryKey:
        score += 25
    ELSE IF rule.Column.IsForeignKey:
        score += 15
    ELSE IF rule.Column.IsUnique:
        score += 10
    END IF
    
    // Factor 3: DQ Dimension (Weight: 15%)
    SWITCH rule.Dimension:
        CASE "Accuracy":
            score += 15
        CASE "Consistency":
            score += 12
        CASE "Completeness":
            score += 10
        CASE "Uniqueness":
            score += 10
        CASE "Validity":
            score += 8
        CASE "Timeliness":
            score += 5
    END SWITCH
    
    // Factor 4: Semantic Context (Weight: 10%)
    IF rule.Column.Name MATCHES "(customer|client|citizen|national_id|financial)":
        score += 10
    ELSE IF rule.Column.Name MATCHES "(status|state|flag)":
        score += 5
    END IF
    
    // Factor 5: User-Defined Critical Fields (Weight: 10%)
    IF settings.CriticalFields CONTAINS rule.Column.Name:
        score += 10
    END IF
    
    // Classify based on score
    IF score >= 60:
        RETURN "High"
    ELSE IF score >= 30:
        RETURN "Medium"
    ELSE:
        RETURN "Low"
    END IF
END FUNCTION
```

### 6.3 Severity Rules Table

| Factor | Condition | Severity Impact |
|--------|-----------|-----------------|
| Sensitivity | PDPL/NDMO classified | High |
| Sensitivity | High classification | High |
| Sensitivity | Medium classification | Medium |
| Constraints | Primary Key | High |
| Constraints | Foreign Key | Medium |
| Constraints | Unique constraint | Medium |
| Dimension | Accuracy violations | High |
| Dimension | Consistency violations | Medium-High |
| Dimension | Completeness violations | Medium |
| Context | Financial data | High |
| Context | Customer data | High |
| Context | Status/State fields | Medium |
| Context | Descriptive fields | Low |
| User Config | Marked as critical | High |

### 6.4 Severity Override Logic

```pseudocode
FUNCTION ApplySeverityOverrides(rule, settings)
    
    // Mandatory High Severity
    IF rule.Column.Sensitivity == "PDPL":
        rule.Severity = "High"
        rule.SeverityReason = "حقل مصنف ضمن بيانات حماية البيانات الشخصية (PDPL)"
        RETURN rule
    END IF
    
    IF rule.Column.IsPrimaryKey AND rule.Dimension == "Uniqueness":
        rule.Severity = "High"
        rule.SeverityReason = "انتهاك تفرد المفتاح الأساسي يؤثر على سلامة البيانات"
        RETURN rule
    END IF
    
    // User-defined critical fields override
    IF settings.CriticalFields CONTAINS rule.Column.Name:
        IF rule.Severity != "High":
            rule.Severity = "High"
            rule.SeverityReason = "حقل محدد كحرج من قبل المستخدم"
        END IF
    END IF
    
    RETURN rule
END FUNCTION
```

---

## 7. Rule Examples

### 7.1 Text Field Rules

#### Example 1: Customer Name (VARCHAR)

**Input Data Dictionary Entry:**
```
Column: CustomerName
Data Type: NVARCHAR(100)
Description: Full name of the customer in Arabic or English
Nullable: No
Sensitivity: Medium
```

**Generated Rules:**

| # | Dimension | Rule Description | SQL Script |
|---|-----------|------------------|------------|
| 1 | Completeness | التحقق من اكتمال حقل اسم العميل وعدم احتوائه على قيم فارغة | `SELECT CustomerName FROM Customers WHERE CustomerName IS NULL` |
| 2 | Completeness | التحقق من عدم احتواء حقل اسم العميل على نص فارغ | `SELECT CustomerName FROM Customers WHERE CustomerName = ''` |
| 3 | Completeness | التحقق من عدم احتواء حقل اسم العميل على مسافات بيضاء فقط | `SELECT CustomerName FROM Customers WHERE LTRIM(RTRIM(CustomerName)) = '' AND CustomerName IS NOT NULL` |
| 4 | Validity | التحقق من أن طول اسم العميل لا يقل عن 3 أحرف | `SELECT CustomerName FROM Customers WHERE LEN(LTRIM(RTRIM(CustomerName))) < 3 AND CustomerName IS NOT NULL` |

#### Example 2: Email Address (VARCHAR)

**Input Data Dictionary Entry:**
```
Column: Email
Data Type: VARCHAR(255)
Description: Customer email address for communication
Nullable: Yes
Sensitivity: High (PDPL)
```

**Generated Rules:**

| # | Dimension | Rule Description | Issue Description | Severity |
|---|-----------|------------------|-------------------|----------|
| 1 | Completeness | التحقق من اكتمال حقل البريد الإلكتروني | عدم توفر بيانات البريد الإلكتروني يؤثر على إمكانية التواصل مع العميل | High |
| 2 | Validity | التحقق من صحة تنسيق البريد الإلكتروني وفقاً للمعيار الدولي | وجود عناوين بريد إلكتروني بتنسيق غير صحيح يؤدي إلى فشل عمليات الإرسال | High |

**SQL Script for Email Validation:**
```sql
-- Rule: التحقق من صحة تنسيق البريد الإلكتروني
SELECT 
    Email,
    'Validity' AS DQ_Dimension,
    'Data Quality' AS Rule_Type
FROM [CustomerDB].[dbo].[Customers]
WHERE Email IS NOT NULL 
  AND Email NOT LIKE '%_@_%.__%'
```

#### Example 3: National ID (VARCHAR)

**Input Data Dictionary Entry:**
```
Column: NationalID
Data Type: VARCHAR(10)
Description: Saudi National ID number (10 digits starting with 1 or 2)
Nullable: No
Sensitivity: High (PDPL/NDMO)
```

**Generated Rules:**

| # | Dimension | Rule Description | Root Cause | Recommendation |
|---|-----------|------------------|------------|----------------|
| 1 | Completeness | التحقق من اكتمال رقم الهوية الوطنية لجميع السجلات | عدم إدخال رقم الهوية أثناء عملية التسجيل أو خطأ في نقل البيانات | إلزام إدخال رقم الهوية في جميع نقاط الإدخال وتفعيل التحقق الآلي |
| 2 | Validity | التحقق من أن رقم الهوية يتكون من 10 أرقام | إدخال بيانات غير مكتملة أو وجود أحرف غير رقمية | تطبيق قواعد التحقق على واجهة المستخدم ومستوى قاعدة البيانات |
| 3 | Validity | التحقق من أن رقم الهوية يبدأ بالرقم 1 (للمواطنين) أو 2 (للمقيمين) | خطأ في إدخال البيانات أو عدم فهم تنسيق رقم الهوية | توفير قائمة منسدلة لنوع الهوية وتطبيق التنسيق المناسب آلياً |
| 4 | Uniqueness | التحقق من تفرد رقم الهوية الوطنية في النظام | تكرار إدخال نفس العميل أو خطأ في عملية الدمج | تفعيل التحقق من التكرار قبل الإدخال وإجراء تنظيف دوري للبيانات |

**SQL Scripts:**
```sql
-- Rule: التحقق من أن رقم الهوية يتكون من 10 أرقام
SELECT NationalID
FROM [CustomerDB].[dbo].[Customers]
WHERE NationalID IS NOT NULL 
  AND (LEN(NationalID) != 10 OR NationalID LIKE '%[^0-9]%')

-- Rule: التحقق من أن رقم الهوية يبدأ بالرقم 1 أو 2
SELECT NationalID
FROM [CustomerDB].[dbo].[Customers]
WHERE NationalID IS NOT NULL 
  AND LEFT(NationalID, 1) NOT IN ('1', '2')
```

### 7.2 Date Field Rules

#### Example 1: Birth Date (DATE)

**Input Data Dictionary Entry:**
```
Column: BirthDate
Data Type: DATE
Description: Customer date of birth
Nullable: Yes
```

**Generated Rules:**

| # | Dimension | Rule Description | SQL Script | Severity |
|---|-----------|------------------|------------|----------|
| 1 | Completeness | التحقق من توفر تاريخ الميلاد للعملاء | `SELECT * FROM Customers WHERE BirthDate IS NULL` | Medium |
| 2 | Validity | التحقق من أن تاريخ الميلاد ليس في المستقبل | `SELECT * FROM Customers WHERE BirthDate > GETDATE()` | High |
| 3 | Validity | التحقق من أن تاريخ الميلاد ضمن نطاق منطقي (لا يتجاوز 120 سنة) | `SELECT * FROM Customers WHERE BirthDate < DATEADD(YEAR, -120, GETDATE())` | Medium |
| 4 | Accuracy | التحقق من أن عمر العميل يتوافق مع الحد الأدنى للخدمة (18 سنة) | `SELECT * FROM Customers WHERE DATEDIFF(YEAR, BirthDate, GETDATE()) < 18` | High |

#### Example 2: Created Date (DATETIME)

**Input Data Dictionary Entry:**
```
Column: CreatedDate
Data Type: DATETIME
Description: Record creation timestamp
Nullable: No
```

**Generated Rules:**

| # | Dimension | Rule Description | Issue Description |
|---|-----------|------------------|-------------------|
| 1 | Completeness | التحقق من توفر تاريخ إنشاء السجل | عدم توفر تاريخ الإنشاء يؤثر على إمكانية تتبع دورة حياة البيانات |
| 2 | Timeliness | التحقق من أن تاريخ الإنشاء ليس في المستقبل | وجود تواريخ مستقبلية يدل على خطأ في ضبط وقت النظام أو التلاعب بالبيانات |
| 3 | Validity | التحقق من أن تاريخ الإنشاء بعد تاريخ إطلاق النظام | وجود تواريخ قبل إطلاق النظام يدل على خطأ في ترحيل البيانات |

#### Example 3: Expiry Date (DATE)

**Input Data Dictionary Entry:**
```
Column: ExpiryDate
Data Type: DATE
Description: Document or license expiry date
Nullable: Yes
Table: Documents
Related: IssueDate
```

**Generated Rules:**

| # | Dimension | Rule Description | SQL Script |
|---|-----------|------------------|------------|
| 1 | Validity | التحقق من أن تاريخ الانتهاء بعد تاريخ الإصدار | `SELECT * FROM Documents WHERE ExpiryDate < IssueDate` |
| 2 | Timeliness | تحديد الوثائق منتهية الصلاحية | `SELECT * FROM Documents WHERE ExpiryDate < GETDATE()` |
| 3 | Timeliness | تحديد الوثائق التي ستنتهي خلال 30 يوماً | `SELECT * FROM Documents WHERE ExpiryDate BETWEEN GETDATE() AND DATEADD(DAY, 30, GETDATE())` |

### 7.3 Numeric Field Rules

#### Example 1: Amount (DECIMAL)

**Input Data Dictionary Entry:**
```
Column: TransactionAmount
Data Type: DECIMAL(18,2)
Description: Transaction amount in SAR
Nullable: No
Sensitivity: High
```

**Generated Rules:**

| # | Dimension | Rule Description | SQL Script | Severity |
|---|-----------|------------------|------------|----------|
| 1 | Completeness | التحقق من توفر قيمة المعاملة المالية | `SELECT * FROM Transactions WHERE TransactionAmount IS NULL` | High |
| 2 | Validity | التحقق من أن قيمة المعاملة رقم موجب | `SELECT * FROM Transactions WHERE TransactionAmount <= 0` | High |
| 3 | Validity | التحقق من أن قيمة المعاملة ضمن الحد الأقصى المسموح | `SELECT * FROM Transactions WHERE TransactionAmount > 1000000` | High |
| 4 | Accuracy | التحقق من دقة الكسور العشرية (خانتين فقط) | `SELECT * FROM Transactions WHERE TransactionAmount != ROUND(TransactionAmount, 2)` | Medium |

#### Example 2: Quantity (INT)

**Input Data Dictionary Entry:**
```
Column: Quantity
Data Type: INT
Description: Number of items in order
Nullable: No
```

**Generated Rules:**

| # | Dimension | Rule Description | Issue Description | Root Cause |
|---|-----------|------------------|-------------------|------------|
| 1 | Completeness | التحقق من توفر كمية الطلب | عدم تحديد الكمية يمنع حساب قيمة الطلب الإجمالية | خطأ في عملية إدخال الطلب أو مشكلة في واجهة التطبيق |
| 2 | Validity | التحقق من أن الكمية عدد صحيح موجب | وجود كميات سالبة أو صفرية يدل على خطأ في منطق الأعمال | عدم وجود تحقق على مستوى التطبيق أو إدخال يدوي خاطئ |
| 3 | Validity | التحقق من أن الكمية لا تتجاوز الحد الأقصى للطلب الواحد | كميات غير واقعية قد تدل على محاولة احتيال أو خطأ إدخال | عدم تطبيق حدود الكمية في النظام |

#### Example 3: Percentage (DECIMAL)

**Input Data Dictionary Entry:**
```
Column: DiscountPercentage
Data Type: DECIMAL(5,2)
Description: Discount percentage applied to order
Nullable: Yes
```

**Generated Rules:**

| # | Dimension | Rule Description | SQL Script |
|---|-----------|------------------|------------|
| 1 | Validity | التحقق من أن نسبة الخصم بين 0 و 100 | `SELECT * FROM Orders WHERE DiscountPercentage < 0 OR DiscountPercentage > 100` |
| 2 | Accuracy | التحقق من أن نسبة الخصم تتوافق مع سياسة الخصومات المعتمدة | `SELECT * FROM Orders WHERE DiscountPercentage NOT IN (SELECT AllowedPercentage FROM DiscountPolicies)` |

---

## 8. Cross-Table Rule Example

### 8.1 Scenario: Customer-Order Relationship

**Table Structure:**

```
┌─────────────────────────┐         ┌─────────────────────────┐
│      CUSTOMERS          │         │       ORDERS            │
├─────────────────────────┤         ├─────────────────────────┤
│ CustomerID (PK)         │◄────────│ CustomerID (FK)         │
│ CustomerName            │         │ OrderID (PK)            │
│ NationalID              │         │ OrderDate               │
│ Email                   │         │ TotalAmount             │
│ Status                  │         │ Status                  │
│ CreatedDate             │         │ CreatedDate             │
└─────────────────────────┘         └─────────────────────────┘
```

### 8.2 Generated Cross-Table Rules

#### Rule 1: Referential Integrity

| Field | Value |
|-------|-------|
| **System** | SalesSystem |
| **Database** | SalesDB |
| **Schema** | dbo |
| **Tables** | Orders |
| **Columns** | CustomerID |
| **Dimension** | Consistency |
| **Rule Description** | التحقق من وجود رقم العميل في جدول الطلبات ضمن جدول العملاء الرئيسي |
| **Issue Description** | وجود طلبات مرتبطة بأرقام عملاء غير موجودة يدل على خلل في سلامة البيانات المرجعية ويؤثر على دقة التقارير المالية |
| **Related Tables** | Customers |
| **Related Columns** | CustomerID |
| **Root Cause** | حذف سجل العميل دون حذف الطلبات المرتبطة، أو إدخال طلبات يدوياً دون التحقق من وجود العميل |
| **Severity** | High |
| **Recommendation** | تفعيل قيود السلامة المرجعية على مستوى قاعدة البيانات وإجراء تنظيف دوري للبيانات اليتيمة |
| **Rule Type** | Data Quality |

**SQL Script:**
```sql
-- التحقق من السلامة المرجعية: Orders.CustomerID -> Customers.CustomerID
SELECT 
    o.OrderID,
    o.CustomerID,
    o.OrderDate,
    o.TotalAmount,
    'Consistency' AS DQ_Dimension,
    'Data Quality' AS Rule_Type
FROM [SalesDB].[dbo].[Orders] o
LEFT JOIN [SalesDB].[dbo].[Customers] c 
    ON o.CustomerID = c.CustomerID
WHERE c.CustomerID IS NULL
  AND o.CustomerID IS NOT NULL

-- Metrics Calculation
;WITH InvalidRecords AS (
    SELECT COUNT(*) AS InvalidCount
    FROM [SalesDB].[dbo].[Orders] o
    LEFT JOIN [SalesDB].[dbo].[Customers] c ON o.CustomerID = c.CustomerID
    WHERE c.CustomerID IS NULL AND o.CustomerID IS NOT NULL
),
TotalRecords AS (
    SELECT COUNT(*) AS TotalCount
    FROM [SalesDB].[dbo].[Orders]
    WHERE CustomerID IS NOT NULL
)
SELECT 
    i.InvalidCount AS [Total Invalid Records],
    t.TotalCount AS [Total Records],
    CAST(CAST(i.InvalidCount AS FLOAT) / NULLIF(t.TotalCount, 0) * 100 AS DECIMAL(5,2)) AS [Invalid Records %]
FROM InvalidRecords i, TotalRecords t
```

#### Rule 2: Data Consistency - Customer Name Matching

| Field | Value |
|-------|-------|
| **System** | SalesSystem |
| **Database** | SalesDB |
| **Schema** | dbo |
| **Tables** | Orders |
| **Columns** | CustomerName |
| **Dimension** | Consistency |
| **Rule Description** | التحقق من تطابق اسم العميل في جدول الطلبات مع الاسم المسجل في جدول العملاء |
| **Issue Description** | اختلاف اسم العميل بين الجداول يدل على عدم تزامن البيانات ويؤثر على دقة التقارير والفواتير |
| **Related Tables** | Customers |
| **Related Columns** | CustomerName |
| **Root Cause** | تحديث اسم العميل في أحد الجداول دون الآخر، أو عدم استخدام مرجع واحد للبيانات |
| **Severity** | Medium |
| **Recommendation** | إزالة حقل اسم العميل من جدول الطلبات والاعتماد على العلاقة مع جدول العملاء، أو تفعيل التحديث المتزامن |
| **Rule Type** | Business Rule |

**SQL Script:**
```sql
-- التحقق من تطابق اسم العميل عبر الجداول
SELECT 
    o.OrderID,
    o.CustomerID,
    o.CustomerName AS OrderCustomerName,
    c.CustomerName AS MasterCustomerName,
    'Consistency' AS DQ_Dimension,
    'Business Rule' AS Rule_Type
FROM [SalesDB].[dbo].[Orders] o
INNER JOIN [SalesDB].[dbo].[Customers] c 
    ON o.CustomerID = c.CustomerID
WHERE LTRIM(RTRIM(o.CustomerName)) != LTRIM(RTRIM(c.CustomerName))
```

#### Rule 3: Business Logic - Order Date After Customer Creation

| Field | Value |
|-------|-------|
| **System** | SalesSystem |
| **Database** | SalesDB |
| **Schema** | dbo |
| **Tables** | Orders |
| **Columns** | OrderDate |
| **Dimension** | Accuracy |
| **Rule Description** | التحقق من أن تاريخ الطلب لاحق لتاريخ تسجيل العميل في النظام |
| **Issue Description** | وجود طلبات بتاريخ سابق لتسجيل العميل يدل على خطأ في البيانات أو تلاعب في التواريخ |
| **Related Tables** | Customers |
| **Related Columns** | CreatedDate |
| **Root Cause** | خطأ في ترحيل البيانات التاريخية، أو تعديل يدوي للتواريخ، أو خطأ في إعدادات وقت النظام |
| **Severity** | High |
| **Recommendation** | مراجعة سجلات الترحيل وتصحيح التواريخ غير المنطقية، وتفعيل التحقق التلقائي عند إنشاء الطلبات |
| **Rule Type** | Business Rule |

**SQL Script:**
```sql
-- التحقق من منطقية التواريخ: تاريخ الطلب بعد تاريخ تسجيل العميل
SELECT 
    o.OrderID,
    o.CustomerID,
    o.OrderDate,
    c.CreatedDate AS CustomerCreatedDate,
    DATEDIFF(DAY, c.CreatedDate, o.OrderDate) AS DaysDifference,
    'Accuracy' AS DQ_Dimension,
    'Business Rule' AS Rule_Type
FROM [SalesDB].[dbo].[Orders] o
INNER JOIN [SalesDB].[dbo].[Customers] c 
    ON o.CustomerID = c.CustomerID
WHERE o.OrderDate < c.CreatedDate
```

#### Rule 4: Status Consistency

| Field | Value |
|-------|-------|
| **System** | SalesSystem |
| **Database** | SalesDB |
| **Schema** | dbo |
| **Tables** | Orders |
| **Columns** | Status |
| **Dimension** | Consistency |
| **Rule Description** | التحقق من عدم وجود طلبات نشطة لعملاء غير نشطين |
| **Issue Description** | وجود طلبات مفتوحة لعملاء متوقفين يدل على خلل في تطبيق قواعد الأعمال |
| **Related Tables** | Customers |
| **Related Columns** | Status |
| **Root Cause** | تعطيل حساب العميل دون إغلاق طلباته المعلقة |
| **Severity** | Medium |
| **Recommendation** | تفعيل إجراء تلقائي لإغلاق أو تعليق الطلبات عند تعطيل حساب العميل |
| **Rule Type** | Business Rule |

**SQL Script:**
```sql
-- التحقق من اتساق حالة الطلبات مع حالة العملاء
SELECT 
    o.OrderID,
    o.CustomerID,
    o.Status AS OrderStatus,
    c.Status AS CustomerStatus,
    'Consistency' AS DQ_Dimension,
    'Business Rule' AS Rule_Type
FROM [SalesDB].[dbo].[Orders] o
INNER JOIN [SalesDB].[dbo].[Customers] c 
    ON o.CustomerID = c.CustomerID
WHERE o.Status = 'Active'
  AND c.Status = 'Inactive'
```

### 8.3 Complex Cross-Table Scenario: Three-Table Validation

**Table Structure:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  CUSTOMERS   │     │   ORDERS     │     │ ORDER_ITEMS  │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ CustomerID   │◄────│ CustomerID   │     │ OrderID      │
│ CreditLimit  │     │ OrderID      │◄────│ ProductID    │
│              │     │ TotalAmount  │     │ Quantity     │
│              │     │              │     │ UnitPrice    │
│              │     │              │     │ LineTotal    │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Generated Business Rule: Order Total Validation**

| Field | Value |
|-------|-------|
| **Tables** | Orders |
| **Columns** | TotalAmount |
| **Dimension** | Accuracy |
| **Rule Description** | التحقق من تطابق إجمالي الطلب مع مجموع بنود الطلب |
| **Related Tables** | Order_Items |
| **Related Columns** | LineTotal |
| **Severity** | High |
| **Rule Type** | Business Rule |

**SQL Script:**
```sql
-- التحقق من دقة إجمالي الطلب مقارنة بمجموع البنود
SELECT 
    o.OrderID,
    o.TotalAmount AS OrderTotal,
    SUM(oi.LineTotal) AS CalculatedTotal,
    o.TotalAmount - SUM(oi.LineTotal) AS Difference,
    'Accuracy' AS DQ_Dimension,
    'Business Rule' AS Rule_Type
FROM [SalesDB].[dbo].[Orders] o
INNER JOIN [SalesDB].[dbo].[Order_Items] oi 
    ON o.OrderID = oi.OrderID
GROUP BY o.OrderID, o.TotalAmount
HAVING o.TotalAmount != SUM(oi.LineTotal)
```

---

## 9. Future Improvement Suggestions

### 9.1 Short-Term Enhancements (Phase 2)

#### 9.1.1 AI-Powered Semantic Analysis
- Integrate NLP models for enhanced column description understanding
- Support for Arabic text analysis in descriptions
- Automatic detection of business context from table/column names
- Machine learning-based rule suggestion engine

#### 9.1.2 Extended Database Support
- Oracle Database syntax generation
- PostgreSQL compatibility
- MySQL/MariaDB support
- Azure SQL Database optimizations

#### 9.1.3 Template Management
- User-defined rule templates
- Industry-specific template packs (Banking, Healthcare, Government)
- Import/Export template functionality
- Template versioning and sharing

#### 9.1.4 Enhanced Reporting
- Interactive dashboards for rule coverage
- Data quality scorecards by system/table
- Trend analysis for recurring issues
- Executive summary generation

### 9.2 Medium-Term Enhancements (Phase 3)

#### 9.2.1 Rule Execution Engine
- Direct database connectivity for rule execution
- Scheduled rule execution jobs
- Real-time metric calculation and storage
- Historical comparison and trending

#### 9.2.2 Workflow Integration
- Integration with JIRA for issue tracking
- ServiceNow incident creation
- Email notifications for critical findings
- Slack/Teams alerts

#### 9.2.3 Collaboration Features
- Multi-user rule review workflow
- Rule approval process
- Version control for rule definitions
- Audit trail for changes

#### 9.2.4 Advanced Cross-Table Analysis
- Automatic relationship discovery from data patterns
- Complex multi-table business rule builder
- Visual relationship mapping interface
- Join optimization recommendations

### 9.3 Long-Term Vision (Phase 4)

#### 9.3.1 Enterprise Data Catalog Integration
- Integration with Apache Atlas
- Collibra connector
- Alation synchronization
- Custom metadata repository support

#### 9.3.2 Data Profiling Engine
- Automatic data profiling before rule generation
- Pattern detection and anomaly identification
- Statistical analysis for threshold recommendations
- Data distribution visualization

#### 9.3.3 Regulatory Compliance Modules
- SAMA (Saudi Arabian Monetary Authority) compliance rules
- PDPL automated compliance checking
- GDPR data quality requirements
- ISO 8000 certification support

#### 9.3.4 Machine Learning Enhancements
- Predictive data quality scoring
- Anomaly detection for new data
- Automated rule refinement based on feedback
- Natural language rule generation

### 9.4 Technical Debt and Optimization

#### 9.4.1 Performance Improvements
- Parallel processing for large dictionaries
- Caching layer for repeated operations
- Lazy loading for UI components
- Memory optimization for large outputs

#### 9.4.2 Architecture Evolution
- Microservices architecture for scalability
- Cloud-native deployment options
- API-first design for integrations
- Containerization (Docker) support

#### 9.4.3 Quality Assurance
- Comprehensive unit test coverage
- Integration test automation
- Performance benchmarking suite
- Accessibility compliance (WCAG)

### 9.5 User Experience Improvements

#### 9.5.1 UI/UX Enhancements
- Dark mode support
- Customizable workspace layouts
- Keyboard shortcuts and accessibility
- Multi-language interface (Arabic/English)

#### 9.5.2 Documentation and Help
- In-app contextual help
- Interactive tutorials
- Video documentation
- Best practices knowledge base

#### 9.5.3 Feedback Loop
- In-app feedback mechanism
- Rule effectiveness rating
- Usage analytics for improvement prioritization
- Community forum integration

---

## Appendix A: Arabic Content Templates

### A.1 Rule Description Templates (وصف القاعدة)

| Dimension | Template |
|-----------|----------|
| Completeness | التحقق من اكتمال حقل {column} في جدول {table} وعدم احتوائه على قيم فارغة |
| Validity | التحقق من صحة تنسيق حقل {column} وتوافقه مع المعايير المحددة |
| Accuracy | التحقق من دقة قيم حقل {column} ومطابقتها للمصدر الموثوق |
| Consistency | التحقق من اتساق قيم حقل {column} مع البيانات المرتبطة في {related_table} |
| Uniqueness | التحقق من تفرد قيم حقل {column} وعدم وجود تكرارات |
| Timeliness | التحقق من حداثة بيانات حقل {column} وعدم تجاوزها للفترة المسموحة |

### A.2 Issue Description Templates (وصف المشكلة)

| Context | Template |
|---------|----------|
| Operational | وجود قيم غير مكتملة يؤثر على سير العمليات التشغيلية ويعيق اتخاذ القرارات |
| Reporting | البيانات غير الصحيحة تؤدي إلى تقارير غير دقيقة وتأثر على جودة المخرجات الإدارية |
| Compliance | عدم اكتمال البيانات قد يؤدي إلى مخالفة المتطلبات التنظيمية والقانونية |
| Financial | الأخطاء في البيانات المالية تؤثر على دقة الحسابات والقوائم المالية |

### A.3 Root Cause Templates (السبب الجذري)

| Category | Template |
|----------|----------|
| Input Error | خطأ في إدخال البيانات من المصدر الأساسي أو عبر واجهة المستخدم |
| Migration | مشكلة في عملية ترحيل البيانات من النظام القديم |
| Integration | خلل في تكامل البيانات بين الأنظمة المختلفة |
| Process | عدم وجود آلية تحقق أو مراجعة في العملية التشغيلية |

### A.4 Recommendation Templates (التوصية)

| Action | Template |
|--------|----------|
| Validation | تفعيل التحقق الآلي من البيانات عند نقطة الإدخال |
| Training | تدريب المستخدمين على إدخال البيانات وفق المعايير المحددة |
| Process | مراجعة وتحسين إجراءات العمل لضمان جودة البيانات |
| Technical | تطبيق قيود تقنية على مستوى قاعدة البيانات |

---

## Appendix B: Approved DQ Dimensions Reference

| Dimension | Arabic | Definition | Typical Rules |
|-----------|--------|------------|---------------|
| Completeness | الاكتمال | Data values are present where expected | NULL checks, Empty checks, Required field validation |
| Validity | الصحة | Data conforms to defined formats and business rules | Pattern matching, Range validation, Format checks |
| Accuracy | الدقة | Data correctly represents real-world values | Reference data matching, Business logic validation |
| Consistency | الاتساق | Data is consistent across systems and datasets | Cross-table validation, Referential integrity |
| Uniqueness | التفرد | No unintended duplicate records exist | Duplicate detection, Primary key validation |
| Timeliness | الحداثة | Data is current and available when needed | Date freshness, Update frequency validation |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-15 | DQ Rules Generator Team | Initial release |

---

*This document is compliant with DAMA-DMBOK, Sadaia/NDMO, and ISO 8000 standards.*
