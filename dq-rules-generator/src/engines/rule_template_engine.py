"""
Rule Template Engine
====================

Generates Arabic business descriptions for DQ rules.

Provides templates for:
- Rule Description (وصف القاعدة)
- Issue Description (وصف المشكلة)
- Root Cause (السبب الجذري)
- Recommendation (التوصية)

All text is business-oriented, not technical/dry.
"""

from typing import Dict, Optional, List
from dataclasses import dataclass

from ..models.table_model import TableModel, ColumnModel, TableType, BusinessDomain, DataSensitivity
from ..models.rule_model import Dimension, RuleType, Severity


@dataclass
class RuleContent:
    """Container for all Arabic content of a rule"""
    rule_description: str
    issue_description: str
    root_cause: str
    recommendation: str
    workflows: str = ""


class RuleTemplateEngine:
    """
    Generates Arabic business descriptions for DQ rules.
    
    Templates are contextual based on:
    - DQ Dimension
    - Table type and domain
    - Column semantics
    - Data sensitivity
    """
    
    # ==========================================================================
    # Completeness Templates (الاكتمال)
    # ==========================================================================
    
    COMPLETENESS_TEMPLATES = {
        'null_check': {
            'default': {
                'rule_desc': 'التحقق من اكتمال بيانات حقل {column} في جدول {table} وعدم احتوائه على قيم فارغة',
                'issue_desc': 'وجود سجلات بدون قيمة في حقل {column} مما يؤثر على اكتمال البيانات واتخاذ القرارات',
                'root_cause': 'عدم إلزامية الحقل في واجهة الإدخال أو خطأ في عملية ترحيل البيانات',
                'recommendation': 'تفعيل قيد NOT NULL على مستوى قاعدة البيانات وإضافة التحقق في واجهة المستخدم'
            },
            'identifier': {
                'rule_desc': 'التحقق من توفر المعرف {column} لجميع السجلات في جدول {table}',
                'issue_desc': 'وجود سجلات بدون معرف يمنع إمكانية الربط مع الجداول الأخرى ويخل بسلامة البيانات',
                'root_cause': 'خلل في إجراءات الإدخال أو فشل في توليد المعرف تلقائياً',
                'recommendation': 'تفعيل توليد المعرف التلقائي وإضافة قيد NOT NULL مع تصحيح السجلات الحالية'
            },
            'legal': {
                'rule_desc': 'التحقق من اكتمال البيانات القانونية في حقل {column} لضمان الامتثال التنظيمي',
                'issue_desc': 'نقص البيانات القانونية يعرض المنشأة لمخاطر عدم الامتثال والمساءلة القانونية',
                'root_cause': 'عدم وجود آلية إلزامية لتوثيق البيانات القانونية المطلوبة',
                'recommendation': 'إلزام توثيق البيانات القانونية قبل حفظ السجل وإنشاء تقارير متابعة دورية'
            },
            'financial': {
                'rule_desc': 'التحقق من اكتمال البيانات المالية في حقل {column} لضمان دقة الحسابات',
                'issue_desc': 'نقص البيانات المالية يؤثر على دقة التقارير المالية وقرارات الإدارة',
                'root_cause': 'عدم إكمال جميع الحقول المالية المطلوبة أثناء إدخال المعاملات',
                'recommendation': 'إلزام إدخال جميع البيانات المالية وتفعيل التحقق قبل الحفظ'
            },
            'personal': {
                'rule_desc': 'التحقق من اكتمال البيانات الشخصية في حقل {column} للتعرف على الأفراد',
                'issue_desc': 'نقص البيانات الشخصية يعيق التحقق من الهوية ويؤثر على جودة الخدمات المقدمة',
                'root_cause': 'عدم جمع البيانات الشخصية المطلوبة من المصدر الأصلي',
                'recommendation': 'مراجعة نماذج جمع البيانات وإضافة الحقول المفقودة كحقول إلزامية'
            }
        },
        'empty_check': {
            'default': {
                'rule_desc': 'التحقق من عدم احتواء حقل {column} على نصوص فارغة',
                'issue_desc': 'وجود قيم نصية فارغة تعطي إيحاء كاذب باكتمال البيانات',
                'root_cause': 'إدخال مسافات فقط أو حفظ بدون إدخال قيمة فعلية',
                'recommendation': 'تطبيق دالة TRIM عند الإدخال ورفض القيم الفارغة'
            }
        }
    }
    
    # ==========================================================================
    # Validity Templates (الصحة)
    # ==========================================================================
    
    VALIDITY_TEMPLATES = {
        'format': {
            'email': {
                'rule_desc': 'التحقق من صحة تنسيق البريد الإلكتروني في حقل {column}',
                'issue_desc': 'وجود عناوين بريد إلكتروني بتنسيق غير صحيح يؤدي إلى فشل التواصل مع المعنيين',
                'root_cause': 'عدم وجود تحقق من تنسيق البريد الإلكتروني عند الإدخال',
                'recommendation': 'إضافة تحقق من تنسيق البريد الإلكتروني باستخدام Regular Expression'
            },
            'phone': {
                'rule_desc': 'التحقق من صحة تنسيق رقم الهاتف في حقل {column}',
                'issue_desc': 'وجود أرقام هواتف بتنسيق غير صحيح يعيق التواصل مع أصحاب العلاقة',
                'root_cause': 'عدم توحيد تنسيق إدخال أرقام الهواتف',
                'recommendation': 'تطبيق قالب موحد لأرقام الهواتف مع التحقق من عدد الخانات'
            },
            'national_id': {
                'rule_desc': 'التحقق من صحة تنسيق رقم الهوية الوطنية في حقل {column}',
                'issue_desc': 'وجود أرقام هوية بتنسيق غير صحيح يدل على خطأ في الإدخال أو بيانات مزيفة',
                'root_cause': 'عدم التحقق من رقم الهوية عند الإدخال أو قبول أرقام يدوية',
                'recommendation': 'تفعيل التحقق من صيغة رقم الهوية (10 أرقام تبدأ بـ 1 أو 2) والربط مع نظام أبشر'
            },
            'date': {
                'rule_desc': 'التحقق من صحة التاريخ في حقل {column} وأنه ضمن النطاق المنطقي',
                'issue_desc': 'وجود تواريخ غير منطقية يؤثر على التقارير الزمنية والتحليلات',
                'root_cause': 'إدخال تواريخ خاطئة يدوياً أو خطأ في تحويل التنسيقات',
                'recommendation': 'استخدام أداة تقويم للإدخال مع تحديد نطاق التواريخ المقبولة'
            }
        },
        'range': {
            'amount': {
                'rule_desc': 'التحقق من أن القيمة المالية في حقل {column} ضمن النطاق المقبول',
                'issue_desc': 'وجود قيم مالية خارج النطاق المنطقي يدل على خطأ إدخال أو تلاعب محتمل',
                'root_cause': 'عدم تحديد حدود دنيا وعليا للقيم المالية',
                'recommendation': 'تحديد الحد الأدنى والأقصى للقيم المالية بناءً على قواعد العمل'
            },
            'percentage': {
                'rule_desc': 'التحقق من أن النسبة المئوية في حقل {column} بين 0 و 100',
                'issue_desc': 'وجود نسب مئوية خارج النطاق المنطقي يخل بدقة الحسابات',
                'root_cause': 'عدم التحقق من نطاق النسبة المئوية عند الإدخال',
                'recommendation': 'إضافة قيد CHECK للتحقق من أن القيمة بين 0 و 100'
            },
            'age': {
                'rule_desc': 'التحقق من أن العمر المحسوب من حقل {column} ضمن النطاق المنطقي',
                'issue_desc': 'وجود أعمار غير منطقية يدل على خطأ في تاريخ الميلاد',
                'root_cause': 'إدخال تاريخ ميلاد خاطئ أو خطأ في حساب العمر',
                'recommendation': 'التحقق من أن العمر بين 0 و 120 سنة ومراجعة السجلات الشاذة'
            }
        },
        'allowed_values': {
            'status': {
                'rule_desc': 'التحقق من أن حالة {column} ضمن القيم المسموحة في النظام',
                'issue_desc': 'وجود حالات غير معرفة يعيق تتبع سير العمل وإعداد التقارير',
                'root_cause': 'إدخال قيم يدوية غير موجودة في قائمة الحالات المعتمدة',
                'recommendation': 'استخدام قائمة منسدلة للحالات المعتمدة فقط ومنع الإدخال الحر'
            },
            'type': {
                'rule_desc': 'التحقق من أن نوع {column} ضمن الأنواع المعتمدة في النظام',
                'issue_desc': 'وجود أنواع غير معرفة يخل بتصنيف البيانات وإعداد الإحصائيات',
                'root_cause': 'عدم ربط الحقل بجدول الأنواع المرجعي',
                'recommendation': 'ربط الحقل بجدول الأنواع المرجعي وتفعيل قيد Foreign Key'
            }
        },
        'length': {
            'default': {
                'rule_desc': 'التحقق من أن طول قيمة حقل {column} ضمن الحد المسموح ({max_length} حرف)',
                'issue_desc': 'وجود قيم بطول غير مناسب قد يدل على بيانات غير صحيحة أو قطع في النص',
                'root_cause': 'عدم تحديد طول الحقل المناسب أو قص البيانات عند الترحيل',
                'recommendation': 'مراجعة طول الحقل وتعديله إن لزم الأمر مع التحقق عند الإدخال'
            }
        }
    }
    
    # ==========================================================================
    # Consistency Templates (الاتساق)
    # ==========================================================================
    
    CONSISTENCY_TEMPLATES = {
        'referential': {
            'default': {
                'rule_desc': 'التحقق من وجود قيمة {column} في جدول {table} ضمن جدول {ref_table} المرجعي',
                'issue_desc': 'وجود قيم يتيمة غير موجودة في الجدول المرجعي يدل على خلل في سلامة البيانات',
                'root_cause': 'حذف سجلات من الجدول المرجعي أو إدخال قيم يدوية غير صحيحة',
                'recommendation': 'تفعيل قيد Foreign Key ومراجعة السجلات اليتيمة لتصحيحها أو حذفها'
            },
            'person': {
                'rule_desc': 'التحقق من وجود بيانات الشخص المرتبطة بـ {column} في جدول الأشخاص',
                'issue_desc': 'وجود طلبات أو معاملات مرتبطة بأشخاص غير مسجلين يخل بسلامة البيانات والمتابعة',
                'root_cause': 'عدم تسجيل الشخص قبل إنشاء المعاملة أو خطأ في رقم الهوية',
                'recommendation': 'إلزام التحقق من وجود الشخص قبل إنشاء المعاملة وتصحيح السجلات الحالية'
            },
            'master': {
                'rule_desc': 'التحقق من صحة الربط بين {table} وجدول {ref_table} المرجعي الأساسي',
                'issue_desc': 'فقدان الربط مع الجداول المرجعية يؤثر على التقارير والتحليلات',
                'root_cause': 'تعديل أو حذف بيانات الجدول المرجعي دون مراجعة الجداول المرتبطة',
                'recommendation': 'تفعيل قيود السلامة المرجعية مع خيار CASCADE أو RESTRICT حسب الحاجة'
            }
        },
        'cross_field': {
            'date_sequence': {
                'rule_desc': 'التحقق من أن {column1} سابق لـ {column2} زمنياً',
                'issue_desc': 'وجود تسلسل زمني غير منطقي (تاريخ انتهاء قبل تاريخ بداية) يدل على خطأ في البيانات',
                'root_cause': 'خطأ في إدخال التواريخ أو عدم وجود تحقق من التسلسل المنطقي',
                'recommendation': 'إضافة تحقق برمجي لضمان التسلسل الصحيح للتواريخ'
            },
            'amount_match': {
                'rule_desc': 'التحقق من تطابق إجمالي {column1} مع مجموع {column2}',
                'issue_desc': 'عدم تطابق الإجمالي مع تفاصيله يدل على خطأ حسابي أو بيانات مفقودة',
                'root_cause': 'خطأ في حساب الإجمالي أو تعديل التفاصيل دون تحديث الإجمالي',
                'recommendation': 'تفعيل حساب الإجمالي تلقائياً من التفاصيل ومنع التعديل اليدوي'
            }
        }
    }
    
    # ==========================================================================
    # Uniqueness Templates (التفرد)
    # ==========================================================================
    
    UNIQUENESS_TEMPLATES = {
        'primary_key': {
            'rule_desc': 'التحقق من تفرد المفتاح الأساسي {column} في جدول {table}',
            'issue_desc': 'وجود تكرار في المفتاح الأساسي يخل بسلامة البيانات ويمنع الربط الصحيح',
            'root_cause': 'خلل في آلية توليد المعرفات أو خطأ في ترحيل البيانات',
            'recommendation': 'تفعيل قيد Primary Key وإصلاح السجلات المكررة'
        },
        'business_key': {
            'rule_desc': 'التحقق من تفرد {column} كمعرف أعمال في جدول {table}',
            'issue_desc': 'تكرار معرف الأعمال يؤدي إلى التباس في التعامل مع السجلات وخطأ في التقارير',
            'root_cause': 'عدم التحقق من التفرد قبل الإدخال أو دمج بيانات من مصادر متعددة',
            'recommendation': 'إضافة قيد UNIQUE وتنظيف السجلات المكررة بالدمج أو الحذف'
        },
        'national_id': {
            'rule_desc': 'التحقق من عدم تكرار رقم الهوية الوطنية {column} لضمان تفرد الأشخاص',
            'issue_desc': 'تكرار رقم الهوية يدل على تسجيل نفس الشخص أكثر من مرة أو خطأ في البيانات',
            'root_cause': 'عدم التحقق من وجود الشخص مسبقاً أو إدخال أرقام هوية خاطئة',
            'recommendation': 'التحقق من عدم وجود الهوية قبل التسجيل ودمج السجلات المكررة'
        },
        'composite': {
            'rule_desc': 'التحقق من تفرد المفتاح المركب ({columns}) في جدول {table}',
            'issue_desc': 'تكرار المفتاح المركب يعني وجود سجلات مزدوجة تؤثر على سلامة البيانات',
            'root_cause': 'عدم تفعيل قيد التفرد المركب أو خطأ في منطق الإدخال',
            'recommendation': 'تفعيل قيد UNIQUE المركب وتنظيف السجلات المكررة'
        }
    }
    
    # ==========================================================================
    # Timeliness Templates (الحداثة)
    # ==========================================================================
    
    TIMELINESS_TEMPLATES = {
        'freshness': {
            'rule_desc': 'التحقق من حداثة البيانات في حقل {column} وعدم تجاوزها {threshold} يوم',
            'issue_desc': 'وجود بيانات قديمة قد تكون غير صالحة للاستخدام في القرارات الحالية',
            'root_cause': 'عدم تحديث البيانات بشكل دوري أو توقف مصدر البيانات',
            'recommendation': 'إنشاء جدولة لتحديث البيانات ومتابعة مصادرها'
        },
        'future_date': {
            'rule_desc': 'التحقق من أن تاريخ {column} ليس في المستقبل (للتواريخ التاريخية)',
            'issue_desc': 'وجود تواريخ مستقبلية في حقول تاريخية يدل على خطأ إدخال',
            'root_cause': 'خطأ في إدخال التاريخ أو مشكلة في ضبط وقت النظام',
            'recommendation': 'إضافة تحقق لمنع إدخال تواريخ مستقبلية للحقول التاريخية'
        },
        'expiry': {
            'rule_desc': 'التحقق من صلاحية {column} وتحديد السجلات منتهية الصلاحية',
            'issue_desc': 'وجود سجلات منتهية الصلاحية قد تؤثر على صحة العمليات الجارية',
            'root_cause': 'عدم وجود آلية متابعة تلقائية للصلاحيات',
            'recommendation': 'إنشاء تنبيهات تلقائية قبل انتهاء الصلاحية بفترة كافية'
        }
    }
    
    # ==========================================================================
    # Accuracy Templates (الدقة)
    # ==========================================================================
    
    ACCURACY_TEMPLATES = {
        'calculation': {
            'rule_desc': 'التحقق من دقة حساب {column} بناءً على القيم المصدرية',
            'issue_desc': 'وجود قيم محسوبة غير دقيقة يؤثر على صحة التقارير والقرارات',
            'root_cause': 'خطأ في معادلة الحساب أو تعديل القيم المصدرية دون إعادة الحساب',
            'recommendation': 'مراجعة معادلات الحساب وتفعيل إعادة الحساب التلقائي'
        },
        'reference_match': {
            'rule_desc': 'التحقق من تطابق {column} مع المصدر الموثوق في {ref_table}',
            'issue_desc': 'اختلاف البيانات عن المصدر الموثوق يدل على عدم تزامن أو خطأ في التحديث',
            'root_cause': 'عدم مزامنة البيانات مع المصدر الموثوق بشكل دوري',
            'recommendation': 'تفعيل المزامنة التلقائية مع المصدر الموثوق والتحقق الدوري'
        },
        'business_logic': {
            'rule_desc': 'التحقق من صحة {column} وفقاً لقواعد الأعمال المعتمدة',
            'issue_desc': 'مخالفة قواعد الأعمال تدل على خطأ في الإجراءات أو استثناء غير موثق',
            'root_cause': 'عدم تطبيق قواعد الأعمال برمجياً أو وجود استثناءات غير مضبوطة',
            'recommendation': 'توثيق قواعد الأعمال وتطبيقها برمجياً مع آلية للاستثناءات المعتمدة'
        }
    }
    
    # ==========================================================================
    # Workflow Suggestions
    # ==========================================================================
    
    WORKFLOW_TEMPLATES = {
        'data_entry': 'مراجعة إجراءات إدخال البيانات',
        'data_migration': 'مراجعة إجراءات ترحيل البيانات',
        'periodic_review': 'مراجعة دورية للبيانات',
        'validation_rule': 'تفعيل قواعد التحقق',
        'alert_notification': 'إنشاء تنبيهات تلقائية',
        'data_cleanup': 'تنظيف البيانات الحالية',
        'process_improvement': 'تحسين إجراءات العمل'
    }
    
    def __init__(self):
        """Initialize the template engine"""
        pass
    
    def generate_content(
        self,
        dimension: Dimension,
        rule_type: str,
        table: TableModel,
        column: ColumnModel,
        **kwargs
    ) -> RuleContent:
        """
        Generate Arabic content for a rule.
        
        Args:
            dimension: DQ dimension
            rule_type: Specific rule type (e.g., 'null_check', 'format')
            table: Source table
            column: Source column
            **kwargs: Additional context (ref_table, max_length, etc.)
            
        Returns:
            RuleContent with all Arabic descriptions
        """
        # Get template based on dimension
        template = self._get_template(dimension, rule_type, column)
        
        # Prepare substitution variables
        vars = {
            'table': table.table_name,
            'column': column.name,
            'schema': table.schema_name,
            **kwargs
        }
        
        # Format content
        return RuleContent(
            rule_description=self._format(template.get('rule_desc', ''), vars),
            issue_description=self._format(template.get('issue_desc', ''), vars),
            root_cause=self._format(template.get('root_cause', ''), vars),
            recommendation=self._format(template.get('recommendation', ''), vars),
            workflows=self._get_workflow(dimension, rule_type)
        )
    
    def _get_template(
        self,
        dimension: Dimension,
        rule_type: str,
        column: ColumnModel
    ) -> Dict[str, str]:
        """Get appropriate template based on dimension and context"""
        
        if dimension == Dimension.COMPLETENESS:
            templates = self.COMPLETENESS_TEMPLATES.get(rule_type, {})
            # Select sub-template based on column type
            if column.is_identifier:
                return templates.get('identifier', templates.get('default', {}))
            elif column.is_legal_field:
                return templates.get('legal', templates.get('default', {}))
            elif column.is_amount_field:
                return templates.get('financial', templates.get('default', {}))
            elif column.sensitivity == DataSensitivity.HIGH:
                return templates.get('personal', templates.get('default', {}))
            return templates.get('default', {})
        
        elif dimension == Dimension.VALIDITY:
            if rule_type in self.VALIDITY_TEMPLATES.get('format', {}):
                return self.VALIDITY_TEMPLATES['format'][rule_type]
            elif rule_type in self.VALIDITY_TEMPLATES.get('range', {}):
                return self.VALIDITY_TEMPLATES['range'][rule_type]
            elif rule_type in self.VALIDITY_TEMPLATES.get('allowed_values', {}):
                return self.VALIDITY_TEMPLATES['allowed_values'][rule_type]
            elif rule_type in self.VALIDITY_TEMPLATES.get('length', {}):
                return self.VALIDITY_TEMPLATES['length'][rule_type]
            return self.VALIDITY_TEMPLATES.get('format', {}).get('date', {})
        
        elif dimension == Dimension.CONSISTENCY:
            if 'referential' in rule_type:
                ref_templates = self.CONSISTENCY_TEMPLATES.get('referential', {})
                if 'person' in column.name.lower():
                    return ref_templates.get('person', ref_templates.get('default', {}))
                return ref_templates.get('default', {})
            elif 'cross' in rule_type:
                return self.CONSISTENCY_TEMPLATES.get('cross_field', {}).get(rule_type, {})
            return self.CONSISTENCY_TEMPLATES.get('referential', {}).get('default', {})
        
        elif dimension == Dimension.UNIQUENESS:
            if column.is_primary_key:
                return self.UNIQUENESS_TEMPLATES.get('primary_key', {})
            elif 'national' in column.name.lower():
                return self.UNIQUENESS_TEMPLATES.get('national_id', {})
            return self.UNIQUENESS_TEMPLATES.get('business_key', {})
        
        elif dimension == Dimension.TIMELINESS:
            if 'expir' in column.name.lower():
                return self.TIMELINESS_TEMPLATES.get('expiry', {})
            elif 'future' in rule_type:
                return self.TIMELINESS_TEMPLATES.get('future_date', {})
            return self.TIMELINESS_TEMPLATES.get('freshness', {})
        
        elif dimension == Dimension.ACCURACY:
            return self.ACCURACY_TEMPLATES.get(rule_type, 
                   self.ACCURACY_TEMPLATES.get('business_logic', {}))
        
        return {}
    
    def _format(self, template: str, vars: Dict) -> str:
        """Format template with variables"""
        try:
            return template.format(**vars)
        except KeyError:
            # Return template with available substitutions
            for key, value in vars.items():
                template = template.replace('{' + key + '}', str(value))
            return template
    
    def _get_workflow(self, dimension: Dimension, rule_type: str) -> str:
        """Get suggested workflow based on dimension"""
        workflows = []
        
        if dimension == Dimension.COMPLETENESS:
            workflows = ['validation_rule', 'data_entry']
        elif dimension == Dimension.VALIDITY:
            workflows = ['validation_rule', 'data_cleanup']
        elif dimension == Dimension.CONSISTENCY:
            workflows = ['validation_rule', 'data_cleanup', 'process_improvement']
        elif dimension == Dimension.UNIQUENESS:
            workflows = ['validation_rule', 'data_cleanup']
        elif dimension == Dimension.TIMELINESS:
            workflows = ['alert_notification', 'periodic_review']
        elif dimension == Dimension.ACCURACY:
            workflows = ['periodic_review', 'process_improvement']
        
        return '، '.join([self.WORKFLOW_TEMPLATES.get(w, w) for w in workflows])
