# سجل إعادة استعمال المقدرات الموجودة

هذا السجل مرتبط بالتوسعة المضافة إلى `tools.entropy_framework` فوق
الالتزام `12d08e8de24170ba00f487b10de9adacbc211d37` الذي يحفظ إصلاح
وصلتي الإسناد والاسم. لا يغير جرد Lean أو قوانين العربية أو شيفرة `src/`.
دليل التشغيل في `docs/NABT_CAPABILITY_REUSE_AR.md`، وتدقيق أصل الجبر
في `docs/NABT_FOUNDATION_REUSE_AR.md`.

## قراءة الأدلة

| الملف | ما يثبته ضمن مجاله |
| --- | --- |
| `capability_map.json` | خريطة مشتقة من الفهرس المترجم الحالي: التصريحات، عبارات المصدر، التبعيات، العائلات، مسارات الاستعمال والديون؛ لا يشغل المستهلكين |
| `capability_startup.json` | عرض البداية المختصر لنفس الخريطة |
| `validation/capability_map_build.json` | أمر البناء وبصمة الخريطة ومقاماتها ومصادرها |
| `validation/compiled_catalog_check.json` و`.log` | إعادة بناء فهرس Lean بالأداة المثبتة ومطابقته للمرجع الحالي |
| `foundation/run_01/result.json` | ١٣ تجربة للجبر التدريجي وتجربة لجسر المصدر، مع أصل الجبر المستورد والطلبات والردود والبصمات المجاورة |
| `validation/consumer_runs_v1/exposed_run_02/execution_summary.json` | ١٣ تشغيلًا من المداخل الموجودة، مع المخرجات الخام وثبات شيفرة التفويض |
| `validation/consumer_runs_v1/first_attempt/` | المحاولة الأولى محفوظة؛ تغير مصدر الواجهة أثناء التشغيل، فكررت على مصدر ثابت |
| `validation/independent_review.json` | مراجعة مستقلة لتمييز أنواع العلاقات واختيار الفهرس وحفظ إشارة إنهاء العملية |
| `validation/independent_historical_guidance_review.json` | مراجعة مستقلة لحفظ تعليمات التأليف التاريخية وبقاء قوانين المقياس وذهبه كما هي |
| `validation/clean_checkout_review_v1/summary.json` | تنفيذ أوامر بوابة CI الثلاثة محليًا في نسخة مستقلة بلا بيانات Git أو ملفات `.lake`، مع قائمة الملفات المنقولة وسجلات الأوامر |
| `validation/full_tests_first_attempt.log` وملف ملخصه | الفحص الأول وأخطاء مطابقة تعليمات التأليف التاريخية الـ١١ قبل فصلها عن التعليمات الحية |
| `validation/full_tests.log` وملف ملخصه | إعادة الفحص العام بعد الإصلاح، مع بصمة السجل وفحص ثبات مصادر التنفيذ والاختبار |
| `validation/prior_contract_preservation.json` | مطابقة ملفات التشغيل الـ٩٩ وتبعيات المرجع المستقل الـ٩٠، وحفظ بيانات سجل المشروع السابقة |
| `validation/verification_summary.json` | نتائج الدفعة النهائية ومقاماتها وحدودها وروابط أدلتها |
| `validation/publication_attempt.json` | مانع مصادقة Git ومنع تكامل GitHub كتابة الكائن؛ لا نشر فرع ولا إنشاء طلب دمج |

المصدر الوحيد لتصريحات البرهان هو الفهرس الذي يختاره
`integrations/current_proof_references.mk`. تتضمن الخريطة ٨٠ وحدة
تحوي تصريحات واثنتين للبيانات، و٣٩ عائلة، و٢٨ مدخلًا موجودًا.
مقاماتها وديونها منفصلة عن نجاح التشغيل وعن تغطية العربية.

## إعادة التشغيل

من جذر المستودع، مع بيئة المشروع المعتادة:

```sh
python -m tools.entropy_framework reuse
python -m tools.entropy_framework reuse --output artifacts/local/reuse-new.json
python -m unittest discover -s tests -p 'test_proof_reuse*.py' -v
python -B evidence/capability_reuse_v1/foundation/replay_foundation.py \
  --output-dir artifacts/local/foundation-new
```

تفترض أمثلة التنفيذ الأصلي بناء أهداف Lake الموجودة بالإصدار المثبت.
يعرض التقرير غياب المنفذ بوصفه عدم إتاحة؛ لا يصبح وجود المصدر تنفيذًا.
تحفظ سجلات المستهلكين معاملات التشغيل والمدخلات وبصماتها؛ تبقى المخرجات
السالبة والمعلقة والمحدودة بالموارد نتائج أصلية مستقلة عن نجاح التفويض.

كل إعادة قياس تكتب إلى مسار جديد. لا يستبدل نجاح لاحق نتيجةً أولى، ولا
تمنح بصمة الملف أو حالة `SUPPORTED` وحدها رتبة حقيقة خارج شروط مسارها.
