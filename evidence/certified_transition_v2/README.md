# تصحيح عقد النقل بهوية مستقلة

يحفظ هذا الإصدار لقطة التطوير `certified_transition_v1` كما نُشرت. يضيف
إلى مصفوفة العقود العملية `six_noun_acquisition` ودعوى
`SOURCE_BOUND_SIX_NOUN_CONSTRUCTION` داخل نقل `licensed_workflow`.
تغيّر `src/nabt/data/transport_command_contracts.json` وحده بين اللقطتين؛
أما تسجيل السطح والتصدير والقياس في foundation فمحفوظ في v1.

عدد ملفات الحزمة 104، ولم تتغير المواد أو الأجوبة المرجعية أو العتبات أو
مقامات القياس التاريخية. سجل `runtime_migration.json` يثبت السلف المباشر؛
ويحتفظ المقيّمون بصفوف هويات legacy وv1 إلى جانب الهوية الجديدة. لا تعتمد
لقطة v1 مصفوفة v2 ولا يُعاد ختم أرشيفها.

امتداد `independent_oracle` يحفظ مواد الحالات الـ24 والأسئلة الـ29 وضوابط
المصدر الستة. جرد تنفيذه يضم المرجع المستقل للأسماء الستة ومقاطع مصادره أيضًا،
لكن نتائجه لا تُخلط بمقامات المقارن السابق. جرد التنفيذ يُثبَّت بعد اكتمال
الأدوات وLean والواجهة؛ تجميد الحزمة وتسجيل هويتها ليسا تشغيلًا للنواة.

```bash
PYTHONPATH=src:. python tools/check_foundation_architecture.py
PYTHONPATH=src:.:tools python -m unittest tests.test_framework_foundation_freeze \
  tests.test_legacy_migration_runtime_freeze tests.test_certified_transition_runtime_freeze
```

لا تدّعي هذه الهوية التواتر أو حسم المراد أو صدق الواقع أو اكتمال العربية.
المقياس اللغوي الجديد يُقرأ من تشغيله الفعلي المستقل، ويظل الإخفاق أو التعليق
ظاهرًا؛ لا يتحول نجاح سلامة النقل إلى نجاح تحليل عربي.
