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

The optional `lexical_profile` selects only an installed profile:
`teaching_v1` (the historical default) or `attested_qac_v1`. The latter sends
`{"schema":"nabt.proof-lab-request.v1","mode":"semantic_axes","lexical_profile":"attested_qac_v1"}`.
The signed handle binds this selection; a report from another profile is
rejected. The `codex/attested-lexical-matrix` branch is allowed only when its
exact SHA is pinned by the deployment configuration.

The UI displays source/model counts and the lexical matrix separately from
the unchanged semantic-axis denominators. Token coverage is reconciled with
the same case's actual replay observations; it counts tokens with lexical
readings, not successful sentence interpretations. Source annotation and
cross-source alignment confer no sense, world-truth, or Lean-proof authority.

## المسار المرخّص وترحيل سلطة الواجهات — 27 أكتوبر 2026

التبويب 09 يرسل `mode=licensed_workflow` وطلبًا خامًا إلى
`tools.licensed_workflow.run_request`. العمليات المثبتة: مطابقة الصيغة،
المرشحون المعجميون، اكتساب النطاق، النقل المعجمي، والتحكم الصرفي.
لا يقبل الطلب إيصالًا جاهزًا أو محققًا يختاره المستخدم. اختيار عقد الاستعمال
اللغوي أو إطار التحكم مقدمة معلنة، وليس تحصيلًا آليًا لهذه المقدمة.

يحتفظ النقل ببصمة الطلب داخل المقبض الموقّع، وبالنتيجة الأصلية كاملة،
وبالبايتات المعيارية التي حُسبت عليها بصماتها. يطابق Worker والمتصفح كل
دعوى بمسارها في نتيجة المحول، ويعيدان حساب بصمات الطلب والنتيجة. لا يظهر
وسم «برهان» إلا داخل بطاقة الدعوى المسماة وشروطها. قد تبقى شهادة استخراج
المصدر مستقلةً عند تعذر فحص الصيغة اللاحق؛ لا تُرقّى إلى قبول الصيغة.

الجرد المعروض مشتق من سجل الواجهات المثبت. يجمع حالات الترحيل والتحصيل
الباقي، ولا يحسب السطح المحروس أو المحول المسجل دليلًا على اكتمال جميع
نتائجه. النقل الفردي المسمى لا يساوي حكمًا تاريخيًا بصحة خبر آحاد، وتعدد
المصادر لا يثبت استقلالها أو التواتر.

شُدّد عقد الاستدلال القديم أيضًا: تُطابق نتيجة Lean وقراءات المقترح
وإيصالات الإغلاق والنص والمقام وهوية الطلب، وتُحسب بصمتا النص والاستعلام
قبل العرض. تعرض البطاقة حدود الدعوى المصدرية؛ إيصال المسار القديم لا
يحمل دعوى اكتمال تحصيل A116. مصدر شهادة المعجم القديمة يُفحص بالعقد
نفسه في Worker والمتصفح. لا تتحول وثيقة مستوردة إلى تشغيل أصلي موثوق.

للتحقق من استجابة فعلية للبوابة:

```sh
node scripts/validate-workflow-report.mjs /absolute/path/to/report.json
npm test
npm run build
npm run validate
```

يلزم نشر حزمة الموقع المطابقة ثم تثبيت `NABT_REF` و`NABT_CODE_SHA` على
الفرع والالتزام اللذين اجتازا الفحوص. إضافة الفرع إلى قائمة السماح وحدها
لا تغيّر نشر الموقع ولا إعداداته. يجب بناء مشغلات العمليات الجديدة في
Actions، وإعادة تجربة طلب حي ومطابقة إيصال النقل قبل إعلان تفعيل هذه
النسخة. تُحفظ أسرار الاستضافة منفصلةً ولا تدخل الحزمة.
