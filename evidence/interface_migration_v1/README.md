# أدلة ترحيل الواجهات وتحويل النطاق إلى دعوى محددة

هذه الحزمة امتداد للرأس `e08809c4c654e0d8dd8eab224e476df4cc9b300c`، وليست
إعادة ختم لأدلته. يشرح [التقرير](../../docs/LICENSED_INTERFACE_MIGRATION_AR.md)
ما انتقل إلى Lean وما بقي من التزامات التحصيل والتفسير والنقل.

- `interface_inventory.json`: كل المدخلات المسجلة وحالة كل منها؛ الجرد ليس
  قياسًا لدقة اللغة أو إتاحة كل مشغّل.
- `code_freeze_v1.json` و`regression_policy_v1.json`: هوية الحزمة المثبتة
  الجديدة وسياسة استمرار المقامات السابقة. لا تغير الذهب أو العتبات.
- `independent_oracle/runner_freeze_v4.json`: الهوية النهائية لمصدر التنفيذ
  والمقيم والواجهة والمواد. الجرد بعد التطوير، وليس ادعاء عينة عمياء.
- `catalog_references/`: فهارس التصريحات وروابطها المعاد توليدها من النواة.
- `independent_review/`: مرجع تطويري مستقل التأليف،24 حالة ببصمة ثابتة، مع
  المحاولتين الخام ومجسات لاحقة منفصلة. تكرار المرجع لا يضاعف مقامه.
- `verification.json`: الأوامر الفعلية والعودة والأعداد والمقامات والبصمات
  وبيئة الفحص. لا يعني نجاح بوابة عدم التراجع نجاح جميع حالات اللغة.
- `verification_bundle/`: تقارير التشغيل النهائية كاملة، محفوظة مرة واحدة
  بمخزن محتوى قابل للاستعادة حرفيًا. حفظ البايتات ليس ترقية لسلطة محتواها.
- `validation_attempt_1/`: المحاولة الشاملة التي أوقفت بعد تصحيح مثال واجهة
  وتحديث هوية المقيم؛ لها خروج130، وليست بوابة ناجحة أو إخفاقًا لغويًا.
- `runner_attempts/` و`runner_migration_v2.json` و`runner_migration_v3.json`:
  المحاولتان السابقتان وأسباب تعديل الهوية. استعادة ملفات الواجهة الأولى
  صُرّح بأنها استعادة لاحقة مطابقة لبصماتها، لا لقطة أخذت قبل التغيير.
- `catalog_attempts/`: سجل توليد توقف عند تغير ملف Lean أثناء التطوير؛ بقي
  محفوظًا، ثم أُعيد التوليد بعد ثبات الوحدة.
- `baseline_ci.json`: إخفاق CI السابق بسبب المصدر غير المتاح. يحتفظ بسجله
  ولا يغير حالة فشل سابقة إلى نجاح محلي لاحق.

مصادر النطاق وشواهده وإعادة الحالات القديمة محفوظة منفصلة في
`evidence/scope_acquisition_v1/`. نقل المعجم يستخدم القراءات الثماني عشرة
المودعة أصلًا؛ لم يُختلق تقويم تاريخي للروايات أو استقلالها أو تواترها.

## إعادة البوابات

تحتاج Lean المحدد في `formal/lean-toolchain` واعتماديات Python لفحوص
المشروع. تبني البوابات المشغلات الأصلية قبل اختبارات سلطتها.

```bash
make check -o test
make test
make -f Makefile -f integrations/grammar_catalog.mk \
  -f integrations/mantuq_inference.mk -f integrations/linguistic_truth.mk \
  -f integrations/licensed_inference.mk grammar-catalog proof-catalog \
  routing-conformance mantuq-inference linguistic-truth licensed-inference
(cd integrations/proof_lab/site && npm test && npm run build && npm run validate)
```

أوامر استمرار المرجع المصدري عبر الهوية النهائية:

```bash
PYTHONPATH=src:. python evidence/interface_migration_v1/independent_oracle/run_regression_v4.py \
  --output-dir artifacts/local/interface-oracle-fresh
PYTHONPATH=src:. python evidence/interface_migration_v1/independent_review/run.py \
  --output artifacts/local/interface-review-fresh.json.gz
```

يجب أن تكون مجلدات النتائج جديدة؛ لا تستبدل نتيجة خامًا منشورة.

## استعادة التقارير

```bash
python evidence/source_acquisition_v1/pack_verification.py restore \
  evidence/interface_migration_v1/verification_bundle /tmp/nabt-interface-verification
python evidence/source_acquisition_v1/pack_verification.py restore \
  evidence/interface_migration_v1/validation_attempt_1 /tmp/nabt-interface-interrupted
```

يفحص المفكك المخزون والأحجام والبصمات قبل الكتابة، ويرفض المجلد الموجود.
أُعيدت مقابلة كل ملف مستعاد ببايتاته الأصلية عند إنشاء الحزمة.

النشر والتجربة الحية عمليتان لاحقتان مستقلتان؛ إيصال محلي يحمل HEAD السابق
لا يُوصف بتجربة منشورة للرأس الجديد. تبقى صحة النقل تاريخيًا، وتحصيل المراد
العام، وصدق الواقع، واكتمال العربية كلها خارج النتائج المثبتة هنا.

يحفظ `validation_attempt_2` مخرجات تحققv3 كاملًا حتى توقفه عند خطأ استيراد أداة التدقيق (رمز خروج2). التصحيح فيv4 يستخدم `python -m tools.interface_migration_audit`. محفوظة الهوية السابقة في `runner_migration_v4.json` وسجل المحاولة؛ لا تُنسب نتائجها إلى نجاح البوابات النهائية.
