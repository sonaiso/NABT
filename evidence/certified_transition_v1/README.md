# هوية تشغيل إضافية لاكتساب الأسماء الستة

هذا الإصدار يضيف تسجيل المدخل `tools.linguistic_truth.six_noun.acquire_six_noun`
والقياس المستقل `tools.benchmark_six_noun_acquisition.main` والتصدير
`sixNounAcquisition`. التغيير الوحيد في الحزمة المجمّدة هو سجل
`src/nabt/data/framework_foundation.json`؛ لم يتغير عقد أي سطح سابق.

يحفظ `runtime_migration.json` هوية السلف المنشور في
`evidence/legacy_migration_v2`، وبصمات اللقطة والأرشيف والسياسة الجديدة.
تظل ملفات السلف وأرصدته الخام كما نُشرت. يحتوي الإصدار الجديد على 104 ملفات
حزمة، وتبقى حالات السياسة وعتباتها ومقاماتها وتوقيعات الإخفاق متطابقة مع السلف.
هوية الحزمة لا تغطي وحدها الأدوات وLean والواجهة؛ لهذه الملفات جرد تنفيذ مستقل.

ملفات `independent_oracle` امتداد صريح للمصحح السابق، مع تغيير هوية الإصدار
ومساراته فقط. تبقى مواد الحالات الـ24 والأسئلة الـ29 وضوابط المصدر الستة
مستقلة عن مرجع الأسماء الستة الجديد. لا تنتقل نتيجة قديمة إلى عدّاد تشغيل جديد،
ولا يُحسب تعليق الحكم الآمن نجاحًا في التحليل أو حسم المراد.

بُنيت الهوية بعد تطوير الشفرة؛ ليست ادعاءً باختبار أعمى. يرفض كلٌّ من مولّد
لقطة الحزمة ومولّد جرد التنفيذ استبدال ملف سبق إنشاؤه. عند تغيير مادة مؤثرة
بعد التجميد يلزم إصدار صريح آخر، لا إعادة ختم الأرشيف.

```bash
PYTHONPATH=src:. python tools/check_foundation_architecture.py
PYTHONPATH=src:.:tools python -m unittest tests.test_framework_foundation_freeze \
  tests.test_legacy_migration_runtime_freeze tests.test_certified_transition_runtime_freeze
```

التجميد وتسجيل المقيّمين لا يشغّلان Lean ولا يثبتان صحة تحليل عربي. أمر
`independent_oracle/freeze_runner_v1.py` يسجل تبعيات التنفيذ، ثم يُعاد تشغيل
`independent_oracle/run_regression_v1.py --output-dir <مسار-جديد-داخل-المستودع>`
في بيئة التنفيذ المكتملة. النتيجة الفعلية لذلك التشغيل تُقرأ من إيصالها؛
لا توجد هنا ترقية للتواتر أو صدق الواقع أو اكتمال العربية.
