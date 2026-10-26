# مختبر NABT للبرهان والتغطية

واجهة عربية خاصة لتجارب الاستدلال المرخص وإعادة قياس المجموعة المستقلة.
مصدر النواة والمشغّل: https://github.com/sonaiso/NABT/tree/codex/dynamic-proof-lab

## التشغيل والتحقق

- `npm test`: اختبارات الخادم والنقل المشفر؛ لا تتطلب أسرارًا أو شبكة.
- `npm run build && npm run validate`: إنتاج Worker ESM والتحقق منه.
- `npm run dev -- --port 4173`: معاينة محلية؛ التنفيذ البعيد معطّل دون إعداداته.

الواجهة في `web/`، وخادم النقل في `worker/server.mjs`؛ يولّد البناء
`worker/index.js` الذي يضم الأصول ذاتيًا. لا يحتاج المشروع اعتماديات Node.

## حدود السلطة

المدقق المثبت في NABT يفحص قانونًا لغويًا محدودًا. المقترح البرمجي لا يمنح
سلطة قبول الشهادة. نتيجة القياس تخص 38 حالة محددة؛ اكتمال العربية كلها
وصدق المقدمات في العالم غير مثبتين.

يشفّر الخادم نص الطلب قبل إرساله إلى Actions ويفك النتيجة المشفرة بعد
التحقق من هوية الالتزام والطلب وبصمة الأثر. لا يصل رمز GitHub إلى المتصفح.
تفك البيانات مؤقتًا داخل عامل GitHub لتشغيل Lean. حماية التشفير تعتمد أيضًا
على إدارة الأسرار وصلاحيات محرري المستودع والموقع.

## إعدادات نشر خاصة

تضبط الأسرار في منصة الاستضافة: `NABT_GITHUB_TOKEN`, `NABT_SIGNING_KEY`,
`NABT_TRANSPORT_KEY`. يطابق الأخير سر Actions المسمى
`NABT_LAB_TRANSPORT_KEY`. وتضبط `NABT_REF`, `NABT_CODE_SHA`.
تظل بوابة `NABT_EXECUTION_ENABLED` مغلقة حتى تضبط صراحةً `true` بعد
اكتمال الإذن والإعداد والتحقق من طلب حي. لا توضع القيم السرية في الملفات.

حالة النشر الأول: الصفحة الخاصة جاهزة للمراجعة، والتنفيذ الحي ينتظر إذنًا
مخصصًا لإعداد مفتاح النقل المشترك. رفضت مراجعة الموافقة الآلية إضافة هذا
السر إلى GitHub Actions؛ لا يدعي هذا الإصدار نجاح تشغيل الطلب من المتصفح.

تحديث 25 أكتوبر 2026: صدرت موافقة المالك الصريحة، وفُعّل المفتاح والتنفيذ
الحي. أُعيدت إجابة `SUPPORTED` من الموقع مع فحص Lean الأصلي. يحفظ
`docs/LEAN_LIVE_ACTIVATION_AR.md` في مستودع NABT الإيصال الحي وإصلاح تنزيل
الأثر وحدود التحقق. لا يُخلط هذا التحديث مع نطاق النشر الأول أعلاه.

إضافة شهادات المعجم: القسم 04 يشغّل `lexicalDenotation` فعليًا عبر الطلب
المشفر `mode=testimony`. يحفظ رتبة النقل غير المقيّمة، وهوية الاقتباس،
وفحص المكونات واللزوم كجهات منفصلة. مرجعه `docs/LEXICAL_TESTIMONY_AR.md`.
فرع التنفيذ المثبت لهذه الإضافة `codex/attested-testimony-live`، مع إلزام
`NABT_CODE_SHA` بمطابقة رأسه قبل أي إرسال. لا يقبل المتصفح فرعًا بديلًا
أو قواعد أو تعريفات أو أعلام تحقق من المستخدم.

## Semantic axes reference

The `semantic_axes` mode runs the pinned 25-case authored reference on
`codex/semantic-axes-reference`. It measures syntax, reading recovery, reference
resolution, motive understanding and external truth separately. The last two
are currently unmeasured. This route emits Python replay receipts, never Lean
proofs, and preserves the previous live Lean routes. Each measured comparison
binds its claim ID and exact input/context digest. Imported reports remain
unverified declarations. See `docs/SEMANTIC_AXES_AR.md` in the NABT repository.

Validate an actual output against both Worker and UI consumers with:

```sh
node scripts/validate-semantic-report.mjs /absolute/path/to/measurement.json
```
