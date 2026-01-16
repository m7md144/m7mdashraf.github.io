"""
Sample Data Dictionary Generator
================================

Creates a sample Data Dictionary Excel file for testing.
Run this script to generate samples/data_dictionary.xlsx
"""

import pandas as pd
from pathlib import Path


def create_sample_data_dictionary():
    """Create a sample Data Dictionary for a Legal Case Management System"""
    
    data = [
        # Person Table
        {
            "Schema Name": "dbo",
            "Table Name": "Person",
            "Table Description": "جدول الأشخاص - يحتوي على بيانات جميع الأشخاص في النظام",
            "Column Name": "PersonId",
            "Column Description": "المعرف الفريد للشخص",
            "Data Type": "INT",
            "Is Nullable": "No",
            "Is Primary Key": "Yes",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Medium"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "Person",
            "Table Description": "جدول الأشخاص - يحتوي على بيانات جميع الأشخاص في النظام",
            "Column Name": "NationalId",
            "Column Description": "رقم الهوية الوطنية السعودية",
            "Data Type": "VARCHAR(10)",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "High"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "Person",
            "Table Description": "جدول الأشخاص - يحتوي على بيانات جميع الأشخاص في النظام",
            "Column Name": "FullName",
            "Column Description": "الاسم الكامل للشخص",
            "Data Type": "NVARCHAR(200)",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Medium"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "Person",
            "Table Description": "جدول الأشخاص - يحتوي على بيانات جميع الأشخاص في النظام",
            "Column Name": "BirthDate",
            "Column Description": "تاريخ الميلاد",
            "Data Type": "DATE",
            "Is Nullable": "Yes",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Medium"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "Person",
            "Table Description": "جدول الأشخاص - يحتوي على بيانات جميع الأشخاص في النظام",
            "Column Name": "Email",
            "Column Description": "البريد الإلكتروني",
            "Data Type": "VARCHAR(255)",
            "Is Nullable": "Yes",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Medium"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "Person",
            "Table Description": "جدول الأشخاص - يحتوي على بيانات جميع الأشخاص في النظام",
            "Column Name": "MobilePhone",
            "Column Description": "رقم الجوال",
            "Data Type": "VARCHAR(20)",
            "Is Nullable": "Yes",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Medium"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "Person",
            "Table Description": "جدول الأشخاص - يحتوي على بيانات جميع الأشخاص في النظام",
            "Column Name": "CreatedDate",
            "Column Description": "تاريخ إنشاء السجل",
            "Data Type": "DATETIME",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Low"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "Person",
            "Table Description": "جدول الأشخاص - يحتوي على بيانات جميع الأشخاص في النظام",
            "Column Name": "ModifiedDate",
            "Column Description": "تاريخ آخر تعديل",
            "Data Type": "DATETIME",
            "Is Nullable": "Yes",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Low"
        },
        
        # Case Table
        {
            "Schema Name": "dbo",
            "Table Name": "LegalCase",
            "Table Description": "جدول القضايا القانونية",
            "Column Name": "CaseId",
            "Column Description": "المعرف الفريد للقضية",
            "Data Type": "INT",
            "Is Nullable": "No",
            "Is Primary Key": "Yes",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "High"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "LegalCase",
            "Table Description": "جدول القضايا القانونية",
            "Column Name": "CaseNumber",
            "Column Description": "رقم القضية في المحكمة",
            "Data Type": "VARCHAR(50)",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "High"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "LegalCase",
            "Table Description": "جدول القضايا القانونية",
            "Column Name": "PersonId",
            "Column Description": "معرف الشخص صاحب القضية",
            "Data Type": "INT",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "Yes",
            "Reference Table": "Person",
            "Reference Column": "PersonId",
            "Sensitivity": "High"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "LegalCase",
            "Table Description": "جدول القضايا القانونية",
            "Column Name": "CaseTypeId",
            "Column Description": "نوع القضية",
            "Data Type": "INT",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "Yes",
            "Reference Table": "CaseType",
            "Reference Column": "CaseTypeId",
            "Sensitivity": "Medium"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "LegalCase",
            "Table Description": "جدول القضايا القانونية",
            "Column Name": "Status",
            "Column Description": "حالة القضية",
            "Data Type": "VARCHAR(20)",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Medium"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "LegalCase",
            "Table Description": "جدول القضايا القانونية",
            "Column Name": "FilingDate",
            "Column Description": "تاريخ تقديم القضية",
            "Data Type": "DATE",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Medium"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "LegalCase",
            "Table Description": "جدول القضايا القانونية",
            "Column Name": "ClosingDate",
            "Column Description": "تاريخ إغلاق القضية",
            "Data Type": "DATE",
            "Is Nullable": "Yes",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Medium"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "LegalCase",
            "Table Description": "جدول القضايا القانونية",
            "Column Name": "CourtId",
            "Column Description": "المحكمة المختصة",
            "Data Type": "INT",
            "Is Nullable": "Yes",
            "Is Primary Key": "No",
            "Is Foreign Key": "Yes",
            "Reference Table": "Court",
            "Reference Column": "CourtId",
            "Sensitivity": "Medium"
        },
        
        # ExternalRequest Table
        {
            "Schema Name": "dbo",
            "Table Name": "ExternalRequest",
            "Table Description": "جدول الطلبات الخارجية",
            "Column Name": "RequestId",
            "Column Description": "معرف الطلب",
            "Data Type": "INT",
            "Is Nullable": "No",
            "Is Primary Key": "Yes",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Medium"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "ExternalRequest",
            "Table Description": "جدول الطلبات الخارجية",
            "Column Name": "NationalId",
            "Column Description": "رقم هوية مقدم الطلب",
            "Data Type": "VARCHAR(10)",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "High"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "ExternalRequest",
            "Table Description": "جدول الطلبات الخارجية",
            "Column Name": "RequestType",
            "Column Description": "نوع الطلب",
            "Data Type": "VARCHAR(50)",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Low"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "ExternalRequest",
            "Table Description": "جدول الطلبات الخارجية",
            "Column Name": "RequestDate",
            "Column Description": "تاريخ تقديم الطلب",
            "Data Type": "DATETIME",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Low"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "ExternalRequest",
            "Table Description": "جدول الطلبات الخارجية",
            "Column Name": "Status",
            "Column Description": "حالة الطلب",
            "Data Type": "VARCHAR(20)",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Low"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "ExternalRequest",
            "Table Description": "جدول الطلبات الخارجية",
            "Column Name": "Amount",
            "Column Description": "المبلغ المطلوب",
            "Data Type": "DECIMAL(18,2)",
            "Is Nullable": "Yes",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Medium"
        },
        
        # Judgment Table
        {
            "Schema Name": "dbo",
            "Table Name": "Judgment",
            "Table Description": "جدول الأحكام القضائية",
            "Column Name": "JudgmentId",
            "Column Description": "معرف الحكم",
            "Data Type": "INT",
            "Is Nullable": "No",
            "Is Primary Key": "Yes",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "High"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "Judgment",
            "Table Description": "جدول الأحكام القضائية",
            "Column Name": "CaseId",
            "Column Description": "معرف القضية",
            "Data Type": "INT",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "Yes",
            "Reference Table": "LegalCase",
            "Reference Column": "CaseId",
            "Sensitivity": "High"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "Judgment",
            "Table Description": "جدول الأحكام القضائية",
            "Column Name": "JudgmentDate",
            "Column Description": "تاريخ صدور الحكم",
            "Data Type": "DATE",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "High"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "Judgment",
            "Table Description": "جدول الأحكام القضائية",
            "Column Name": "JudgmentText",
            "Column Description": "نص الحكم",
            "Data Type": "NVARCHAR(MAX)",
            "Is Nullable": "Yes",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "High"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "Judgment",
            "Table Description": "جدول الأحكام القضائية",
            "Column Name": "PenaltyAmount",
            "Column Description": "مبلغ الغرامة",
            "Data Type": "DECIMAL(18,2)",
            "Is Nullable": "Yes",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Medium"
        },
        
        # CaseType Lookup Table
        {
            "Schema Name": "dbo",
            "Table Name": "CaseType",
            "Table Description": "جدول أنواع القضايا (مرجعي)",
            "Column Name": "CaseTypeId",
            "Column Description": "معرف نوع القضية",
            "Data Type": "INT",
            "Is Nullable": "No",
            "Is Primary Key": "Yes",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Low"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "CaseType",
            "Table Description": "جدول أنواع القضايا (مرجعي)",
            "Column Name": "TypeName",
            "Column Description": "اسم نوع القضية",
            "Data Type": "NVARCHAR(100)",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Low"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "CaseType",
            "Table Description": "جدول أنواع القضايا (مرجعي)",
            "Column Name": "IsActive",
            "Column Description": "هل النوع فعال",
            "Data Type": "BIT",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Low"
        },
        
        # Court Lookup Table
        {
            "Schema Name": "dbo",
            "Table Name": "Court",
            "Table Description": "جدول المحاكم (مرجعي)",
            "Column Name": "CourtId",
            "Column Description": "معرف المحكمة",
            "Data Type": "INT",
            "Is Nullable": "No",
            "Is Primary Key": "Yes",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Low"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "Court",
            "Table Description": "جدول المحاكم (مرجعي)",
            "Column Name": "CourtName",
            "Column Description": "اسم المحكمة",
            "Data Type": "NVARCHAR(200)",
            "Is Nullable": "No",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Low"
        },
        {
            "Schema Name": "dbo",
            "Table Name": "Court",
            "Table Description": "جدول المحاكم (مرجعي)",
            "Column Name": "City",
            "Column Description": "المدينة",
            "Data Type": "NVARCHAR(100)",
            "Is Nullable": "Yes",
            "Is Primary Key": "No",
            "Is Foreign Key": "No",
            "Reference Table": "",
            "Reference Column": "",
            "Sensitivity": "Low"
        },
    ]
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to Excel
    output_path = Path(__file__).parent / "data_dictionary.xlsx"
    df.to_excel(output_path, index=False, sheet_name="Data Dictionary")
    
    print(f"Sample Data Dictionary created: {output_path}")
    print(f"Tables: {df['Table Name'].nunique()}")
    print(f"Columns: {len(df)}")
    
    return output_path


if __name__ == "__main__":
    create_sample_data_dictionary()
