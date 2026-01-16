# DQ Rules Generator

مولّد قواعد جودة البيانات وقواعد الأعمال

---

## نظرة عامة

برنامج محلي لتحليل قواعد البيانات وتوليد قواعد جودة البيانات (Data Quality Rules) وقواعد الأعمال (Business Rules) تلقائياً من ملفات Data Dictionary.

### الهدف الأساسي

- **فهم البزنس**: يفهم وظيفة الجداول والحقول من السياق
- **فهم التقنية**: يحلل أنواع البيانات والقيود
- **استنتاج العلاقات**: يكتشف العلاقات حتى بدون Foreign Keys
- **توليد القواعد**: ينتج قواعد ذكية مع SQL قابل للتنفيذ
- **تصدير احترافي**: يخرج النتائج في Excel منظم

### ⚠️ ما ليس هذا البرنامج

- ❌ ليس Chatbot
- ❌ ليس AI Agent
- ❌ لا يفتح محادثات
- ❌ لا يجلب معلومات من الإنترنت

---

## 📁 هيكل المشروع

```
dq-rules-generator/
├── main.py                      # نقطة الدخول الرئيسية
├── requirements.txt             # المتطلبات
├── README.md                    # هذا الملف
├── src/
│   ├── models/                  # نماذج البيانات
│   │   ├── table_model.py       # نموذج الجداول والأعمدة
│   │   ├── rule_model.py        # نموذج القواعد
│   │   └── relationship_model.py # نموذج العلاقات
│   ├── readers/                 # قارئات الملفات
│   │   ├── excel_reader.py      # قارئ Data Dictionary
│   │   └── schema_reader.py     # قارئ SQL Schema
│   ├── analyzers/               # المحللات
│   │   ├── business_context_analyzer.py    # محلل السياق البزنس
│   │   └── relationship_inference_engine.py # محرك استنتاج العلاقات
│   ├── engines/                 # المحركات
│   │   ├── rule_generator.py    # مولّد القواعد الرئيسي
│   │   ├── rule_template_engine.py # محرك القوالب العربية
│   │   └── sql_generator.py     # مولّد SQL
│   ├── exporters/               # المُصدّرات
│   │   └── excel_exporter.py    # مُصدّر Excel
│   └── utils/                   # أدوات مساعدة
│       └── config.py            # إدارة الإعدادات
├── samples/                     # أمثلة
│   └── sample_data_dictionary.py
└── output/                      # مجلد المخرجات
```

---

## 🚀 التثبيت والتشغيل

### 1. تثبيت المتطلبات

```bash
cd dq-rules-generator
pip install -r requirements.txt
```

### 2. تشغيل البرنامج

```bash
# الاستخدام الأساسي
python main.py --input data_dictionary.xlsx --output rules.xlsx

# مع تحديد النظام وقاعدة البيانات
python main.py --input data_dictionary.xlsx \
               --system "Legal System" \
               --database "LegalDB" \
               --output dq_rules.xlsx

# مع ملف إعدادات
python main.py --input data_dictionary.xlsx --config config.yaml

# مع تصدير SQL
python main.py --input data_dictionary.xlsx \
               --output rules.xlsx \
               --output-sql validation_scripts.sql
```

### 3. إنشاء Data Dictionary نموذجي للاختبار

```bash
python samples/sample_data_dictionary.py
```

---

## 📥 المدخلات المدعومة

### 1. Data Dictionary (Excel)

يجب أن يحتوي على الأعمدة التالية (الأسماء مرنة):

| العمود | مطلوب | الوصف |
|--------|-------|-------|
| Schema Name | لا | اسم المخطط (dbo افتراضي) |
| Table Name | **نعم** | اسم الجدول |
| Table Description | لا | وصف الجدول |
| Column Name | **نعم** | اسم العمود |
| Column Description | لا | وصف العمود |
| Data Type | **نعم** | نوع البيانات |
| Is Nullable | لا | قابل للقيم الفارغة |
| Is Primary Key | لا | مفتاح أساسي |
| Is Foreign Key | لا | مفتاح أجنبي |
| Reference Table | لا | الجدول المرجعي |
| Reference Column | لا | العمود المرجعي |
| Sensitivity | لا | درجة الحساسية |

### 2. ملف Schema (اختياري)

```bash
python main.py --input data_dictionary.xlsx --schema-file schema.sql
```

---

## 📤 شكل المخرجات

### أعمدة ملف Excel (بالترتيب):

| # | العمود | الوصف |
|---|--------|-------|
| 1 | System | اسم النظام |
| 2 | Database | اسم قاعدة البيانات |
| 3 | Schema | اسم المخطط |
| 4 | Tables | اسم الجدول |
| 5 | Columns | اسم العمود |
| 6 | Dimension | بُعد الجودة |
| 7 | Rule Description | وصف القاعدة (عربي) |
| 8 | Issue Description | وصف المشكلة (عربي) |
| 9 | Rule SQL Script | سكربت SQL |
| 10 | Related Tables | الجداول المرتبطة |
| 11 | Related Columns | الأعمدة المرتبطة |
| 12 | Total Invalid Records | عدد السجلات غير الصالحة |
| 13 | Total Records | إجمالي السجلات |
| 14 | Invalid Records % | نسبة الخطأ |
| 15 | Root Cause | السبب الجذري (عربي) |
| 16 | Severity | درجة الأهمية |
| 17 | Recommendation | التوصية (عربي) |
| 18 | DQ Check Date | تاريخ الفحص |
| 19 | Workflows | الإجراءات المقترحة |
| 20 | Rule Type | نوع القاعدة |

---

## 🧠 أبعاد جودة البيانات المعتمدة

| البُعد | الوصف |
|--------|-------|
| **Completeness** | الاكتمال - التحقق من وجود القيم |
| **Validity** | الصحة - التحقق من صحة التنسيق |
| **Consistency** | الاتساق - التحقق من تطابق البيانات عبر الجداول |
| **Uniqueness** | التفرد - التحقق من عدم التكرار |
| **Timeliness** | الحداثة - التحقق من عمر البيانات |
| **Accuracy** | الدقة - التحقق من صحة القيم |

---

## 🔗 استنتاج العلاقات

البرنامج يستنتج العلاقات بين الجداول حتى بدون تعريف Foreign Keys صريح:

### آليات الاستنتاج:

1. **تطابق الأسماء**: `PersonId` في جدول `Order` يرتبط بـ `Person.PersonId`
2. **تطابق الأنماط**: أعمدة تنتهي بـ `_id` أو `Id`
3. **تحليل الوصف**: استخراج العلاقات من وصف الأعمدة
4. **أنماط الأعمال**: ربط `NationalId` بجدول الأشخاص تلقائياً

### مثال على قاعدة ربط:

```sql
-- التحقق من وجود مقدم الطلب في جدول الأشخاص
SELECT 
    er.NationalId,
    'ExternalRequest' AS SourceTable,
    'Person' AS ExpectedTarget
FROM [dbo].[ExternalRequest] er
LEFT JOIN [dbo].[Person] p
    ON er.NationalId = p.NationalId
WHERE er.NationalId IS NOT NULL
  AND p.NationalId IS NULL
```

---

## ✍️ أسلوب الصياغة العربية

### وصف القاعدة (Rule Description):
- صياغة بزنس واضحة
- تشرح الأثر التشغيلي/القانوني
- بدون تكرار لغوي

**مثال:**
> التحقق من وجود بيانات الشخص المرتبطة برقم الهوية في جدول الأشخاص

### وصف المشكلة (Issue Description):
- وصف واضح وبسيط للمشكلة

**مثال:**
> وجود طلبات مرتبطة بأشخاص غير مسجلين يخل بسلامة البيانات والمتابعة

### السبب الجذري (Root Cause):
- سبب تشغيلي/إداري/تقني

**مثال:**
> عدم تسجيل الشخص قبل إنشاء المعاملة أو خطأ في رقم الهوية

### التوصية (Recommendation):
- حل تقني قابل للتنفيذ

**مثال:**
> إلزام التحقق من وجود الشخص قبل إنشاء المعاملة وتصحيح السجلات الحالية

---

## ⚙️ ملف الإعدادات

### config.yaml

```yaml
system_name: "Legal System"
database_name: "LegalDB"
default_schema: "dbo"
timeliness_threshold_days: 30
critical_fields:
  - "NationalId"
  - "CaseNumber"
min_relationship_confidence: 0.6
output_directory: "./output"
include_sql_file: true
include_summary: true
```

---

## 📊 أمثلة على القواعد المولّدة

### 1. قاعدة اكتمال (Completeness)

| الحقل | القيمة |
|-------|--------|
| Table | Person |
| Column | NationalId |
| Dimension | Completeness |
| Rule Description | التحقق من توفر رقم الهوية الوطنية لجميع السجلات في جدول الأشخاص |
| SQL | `SELECT * FROM Person WHERE NationalId IS NULL OR LTRIM(RTRIM(NationalId)) = ''` |
| Severity | High |

### 2. قاعدة صحة (Validity)

| الحقل | القيمة |
|-------|--------|
| Table | Person |
| Column | Email |
| Dimension | Validity |
| Rule Description | التحقق من صحة تنسيق البريد الإلكتروني |
| SQL | `SELECT * FROM Person WHERE Email NOT LIKE '%_@_%.__%'` |
| Severity | Medium |

### 3. قاعدة اتساق (Consistency) - Cross-Table

| الحقل | القيمة |
|-------|--------|
| Table | ExternalRequest |
| Column | NationalId |
| Dimension | Consistency |
| Rule Description | التحقق من وجود بيانات الشخص المرتبطة برقم الهوية في جدول الأشخاص |
| Related Tables | Person |
| SQL | `SELECT er.* FROM ExternalRequest er LEFT JOIN Person p ON er.NationalId = p.NationalId WHERE er.NationalId IS NOT NULL AND p.NationalId IS NULL` |
| Severity | High |

---

## 🏗️ المعمارية

```
┌─────────────────────────────────────────────────────────────────┐
│                    DQ RULES GENERATOR                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐   ┌──────────────────┐   ┌────────────────┐  │
│   │   READERS    │──►│    ANALYZERS     │──►│    ENGINES     │  │
│   │              │   │                  │   │                │  │
│   │ Excel Reader │   │ Business Context │   │ Rule Generator │  │
│   │ Schema Reader│   │ Relationship     │   │ SQL Generator  │  │
│   │              │   │ Inference        │   │ Template Engine│  │
│   └──────────────┘   └──────────────────┘   └────────────────┘  │
│                                                      │           │
│                                                      ▼           │
│                                            ┌────────────────┐   │
│                                            │   EXPORTERS    │   │
│                                            │                │   │
│                                            │ Excel Exporter │   │
│                                            └────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📜 الترخيص

MIT License

---

## 👨‍💻 المساهمة

نرحب بالمساهمات! يرجى:

1. Fork المشروع
2. إنشاء فرع للميزة الجديدة
3. Commit التغييرات
4. فتح Pull Request
