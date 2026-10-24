# تدقيق الشواهد اللغوية والصياغات السابقة في Lean

تاريخ المراجعة: 2026-10-24. هذه مذكرة عمل داخلية، لا شهادة باكتمال الكتب أو بصدق كل تعميم لغوي فيها.

## 1. هوية المادة وطريقة الفحص

تحققت من رأسي `main` عبر GitHub API ثم قرأت ملفاتًا مثبتة عند:

- [Saleh1967/Mashru — e4c801ffe9171dadedcc3aae23051ea0953ae361](https://github.com/Saleh1967/Mashru/tree/e4c801ffe9171dadedcc3aae23051ea0953ae361): 120 ملف Lean.
- [Saleh1967/Alghanem — 9d8fa03a51f894416e0abaf3b6821c5ae6441dcd](https://github.com/Saleh1967/Alghanem/tree/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd): 165 ملف Lean.

طابقت Git blob SHA-1 لكل ملف من الملفات الـ285 مع شجرة الالتزام: لا اختلاف. وفحصت الرموز بعد استبعاد التعليقات المتداخلة والسلاسل النصية: لم أجد `sorry` أو `sorryAx` أو `admit` أو `axiom` أو `native_decide` أو `ofReduceBool` أو `unsafe` أو `opaque` كرموز فعلية. النتيجة محفوظة في `formal_source_scan.json` بجوار هذه المذكرة.

**هذا فحص مصدر، وليس إعادة بناء أو تدقيق axioms جديدًا للمستودعين.** نجاح التدقيق السابق المودع في تلك المستودعات لا أعيد نسبته إلى تنفيذ هذه الجلسة. أما ملف NABT الجديد `Nabt/ClassicalLanguageEvidence.lean` فقد قبلته Lean 4.34.1 مباشرة بلا أخطاء أو تحذيرات؛ البناء المتكامل والتصدير وفحوص المطابقة لدى الوكيل الرئيس.

## 2. العوامل: ما الذي كان مثبتًا، وما الذي أصبح له أصل أولي؟

### Mashru

ينص [Jisr/Awamil.lean، الأسطر4–27](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/Jisr/Awamil.lean#L4-L27) على أن المادة جدول XLSX للمالك، بلا عنوان أو مؤلف في الملف نفسه. تسمية «حسب الجرجاني» واردة عن المالك. ويصرح بأن كتاب الجرجاني غير مودع وأن مطابقة العد للجرجاني غير مثبتة.

تثبت [`jadwal_mia` و`alfaz_96`، الأسطر111–124](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/Jisr/Awamil.lean#L111-L124) 100 عمل، و96 لفظًا، و13 صنفًا بالأعداد `[13,6,10,7,4,6,17,8,1,10,4,10,4]`. وتثبت [`inghilaq` و`nawasikh_thalatha` و`istinfad`، الأسطر126–150](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/Jisr/Awamil.lean#L126-L150) خواص معادلات الآثار التي اختارها صاحب الجدول، لا مطابقة كل عامل بحكمه وسياقه في كتاب الجرجاني.

### Alghanem

يوضح [Awamil.lean، الأسطر4–27](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Awamil.lean#L4-L27) أن المصدر مرفق ذو أربعة أعمدة مقبولة، وأن الأعمدة المتولدة الأخرى رُفضت. إرساء الأصناف على **عناوين أبواب** شرح ابن عقيل، وليس مواضع تثبت كل صف. ويصرح بأن الجدول لا يحصر عوامل العربية وأن أمثلته لم تمر بالبوابة.

تثبت [AwamilCount.lean، الأسطر7–27](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/AwamilCount.lean#L7-L27) عدد الصفوف100، وعدد الأصناف، وتكرار أربعة أسماء، ووجود رقم باب مسموح لكل ذي أثر. لا يثبت رقم الباب وحده أن العبارة المعينة تدل على الحكم المفصل لذلك الصف.

### الأصل الجديد

وجد وكيل المصادر، وراجع الرئيس بصريًا، طبعة دار المنهاج1430هـ/2009م من «العوامل المئة» لعبد القاهر الجرجاني. أصل المسح هو [عنصر الأرشيف ali95_20161001_1731](https://archive.org/details/ali95_20161001_1731)، وبصمة PDF:

`0e589cd1c11d54337ce6db0fff7460540be1cc57ddabbc739d81a0e30fac4c9e`.

صفحة40 المطبوعة — صفحة PDF40 بحساب يبدأ من1 — تقسمها إلى91 سماعية، و7 قياسية، و2 معنوية. صفحة41 تذكر مثالَي الباء «مررت بزيد» و«كتبت بالقلم». أودع تفريغ محدود للمتن، مع حذف التشكيل وعلامات الحواشي وتوحيد الفصل؛ **التفريغ ليس بايتات PDF الأصلية**. بياناته في `evidence/classical_language/sources/awamil_jurjani_excerpt.metadata.json`.

الجسر المشروع الآن: إسناد التقسيم المحدد إلى هذا النص، والتحقق الحسابي من مجموعه. الجسر الباقي: مقابلة كل صف في جدول المالك بعامل ونوع وشرط في كتاب الجرجاني. اشتراك المجموع100 لا يكفي؛ المبرهنة الجديدة `hundred_does_not_determine_partition` تعرض تقسيمًا آخر90+8+2 له المجموع نفسه.

## 3. مقاييس اللغة: الجرد شيء والدلالة في كل استعمال شيء آخر

### جرد4506 جذرًا

في [Alghanem/Maqayis.lean، الأسطر7–14](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Maqayis.lean#L7-L14) وصف صريح لجدول متولد من CSV مثبت. تثبت [`nums_nodup` و`nums_in_range` و`roots_num` و`roots_nodup` و`count_is_maqayisCount` و`witness_share`، الأسطر48–90](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Maqayis.lean#L48-L90) التفرد، والوقوع في مجال28³، وصحة الترميز، والعدد4506، وحدًا دون21% من المجال.

العبارة الجانبية «أقل من خمسه بقليل» في السطر14 غير دقيقة حسابيًا:4506/21952 أكبر من20% وأقل من21%. المبرهنة نفسها صحيحة في مدلولها `<21%`؛ لا يجوز وصف هذا بأنه تناقض برهاني.

جسر CSV إلى الجدول في [tests/test_maqayis.py، الأسطر17–72](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/tests/test_maqayis.py#L17-L72): يثبت بصمة CSV، ويطوي كراسي الهمزة والمقصورة وفق تعيين معلن، ثم يقارن مجموعة الجذور وترتيبها. هذا جسر فحص قابل للإعادة؛ ليس برهانًا بأن استخراج CSV من جميع نسخ المقاييس كامل وسليم، ولا بأن كل سلسلة أخرى ممتنعة لغويًا.

### المضاد الأقوى: بلعم/البلعوم

تشرح [Mashru/Madlul/Naht.lean، الأسطر4–14](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/Madlul/Naht.lean#L4-L14) أن معيارN1 من اختيار البنّاء: الرباعي «منحوت» إذا كان بين حذف حرف واحد منه ثلاثيان مختلفان مشهودان. ثم تثبت [`bulum_yukhalif`، الأسطر78–80](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/Madlul/Naht.lean#L78-L80) قبول السلسلة «بلعم» في هذا المعيار، مع أن الأصل الذي قرأه وكيل المصادر يعنون **(البلعوم)** وينسبه إلى «بلع» بزيادة.

نجاح Lean هنا يثبت نتيجة معيارN1 على قائمته. المضاد يبين أن تفسير النتيجة «إذن ثبت النحت التاريخي عند ابن فارس» لا يصح. الملف القديم نفسه يعلن هذا الحد، فلا ينسب إليه ادعاء لم يقله.

في القانون الجديد، `lexicon_entry_bound` يربط المدخل بالجذر والشرح المعينين. `entry_does_not_license_every_use` و`support_excludes_every_use` يمنعان تحويل الشاهد المعجمي المحدود إلى معنى كل وقوع للكلمة.

### النقل ومراتب الشهادة

بنية [Alghanem/Naql.lean، الأسطر51–102](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Naql.lean#L51-L102) تحمل راويًا وقائلًا ونوع طريق ومودع ورقم سطر، ثم تعمل وفق معياري الكفاية والتواتر الممررين إليها. `mafhum_bishahid` يثبت قبول شاهد واستيفاء **المعيار المعطى**. [`kitab_hukm`، الأسطر348–369](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Naql.lean#L348-L369) يوضح عمدًا أن رفع الرتبة باختيار «ثلاثة قائلين» معيارًا للتواتر فرض يبين الآلية، وليس إثبات وقوع التواتر. لا تنقل تلك الرتبة إلى NABT باعتبارها تحققًا خارجيًا.

## 4. كتاب سيبويه: توجد صياغات محددة، لا تحويل للكتاب كله

### ما ثبت سابقًا

في [Alghanem/Makharij.lean، الأسطر9–33](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Makharij.lean#L9-L33) جدول مخارج وصفات مسند إلى مواضع من الكتاب. يفرق بين R ترتيبية اختارها المصمم وبين علاقة الإدغام المنقولة. وتكشف [`listed_vs_stated` و`lam_unplaced`، الأسطر95–107](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Makharij.lean#L95-L107) أن النسختين المودعتين تقولان16 مخرجًا لكن الجدول يسرد15 ولا يسند اللام. الإتمام في [`restored`، الأسطر109–123](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Makharij.lean#L109-L123) بإضافة صف من رواية السيرافي، بصفته شاهدًا آخر معلنًا.

في [Istiqama.lean، الأسطر21–29](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Istiqama.lean#L21-L29) أوصاف الكلمات مدخلات منقولة، لا نتائج مكتسبة من النص الخام. [`sinf`، الأسطر111–115](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Istiqama.lean#L111-L115) يتلقى قيمة الكذب من الخارج. وتثبت [`istiqama_amya`، الأسطر155–167](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Istiqama.lean#L155-L167) أن «حملت الجبل» تبقى سليمة بنيويًا بينما يتغير وصف الصدق/الكذب بتغير ذلك المدخل. هذا مثال مباشر على استقلال الحكم التركيبي عن حدوث الواقعة.

### القانون الجديد8→4

الأصل هو [نسخة الكتاب JK006989، الأسطر111–120 عند OpenITI/0200AH@599f22fe249871f602efe2e0ddc801d3742960a3](https://github.com/OpenITI/0200AH/blob/599f22fe249871f602efe2e0ddc801d3742960a3/data/0180Sibawayhi/0180Sibawayhi.KitabSibawayhi/0180Sibawayhi.KitabSibawayhi.JK006989-ara1#L111-L120). بصمة النسخة `a160f940bb194e6fe7e6655d2c7f28e41f1fc648c4c5e340cc4e42306d5cb625`.

| السطح | مجرى الإعراب | مجرى البناء |
|---|---|---|
| فتحة | نصب | فتح |
| كسرة | جر | كسر |
| ضمة | رفع | ضم |
| سكون | جزم | وقف |

`surface_not_injective` يثبت أن الشكل السطحي لا يسترد الوظيفة وحده. `surface_and_regime_determine_course` يسترد المجرى من السطح مع الإعراب/البناء **داخل هذا الجرد المحدود**. لم أعثر في البحث المستهدف على صياغة سابقة مستقلة لهذا الجدول8/4؛ هذا وصف لنتيجة البحث، لا برهان عدم وجود مطلق.

## 5. قطر الندى: المشدد وما الكافة وليت

في [Mashru/SLGE/Wad.lean، الأسطر81–84](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/SLGE/Wad.lean#L81-L84) جدول عائلة إنّ بأثر نصب/رفع مجرد. إثبات [جدول75 مدخلًا وانغلاقه واستنفاده، الأسطر105–117](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/SLGE/Wad.lean#L105-L117) يخص هذا الجدول المصنف. ويصرح [Jisr/TartibMamul.lean، الأسطر31–40](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/Jisr/TartibMamul.lean#L31-L40) بتأجيل الإعمال والإهمال، بما فيهما المخففات وما الكافة. ويسجل [KhulasaIkhbar.lean، الأسطر75–80](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/Jisr/KhulasaIkhbar.lean#L75-L80) ذلك ضمن الباقي.

الأصل المباشر لقانون NABT الجديد هو [متن قطر الندى Shamela0011376، الأسطر187–194 عند OpenITI/0775AH@61b0c7891699554aeff8dffdb8b1a2a59d2d22ab](https://github.com/OpenITI/0775AH/blob/61b0c7891699554aeff8dffdb8b1a2a59d2d22ab/data/0761JamalDinIbnHisham/0761JamalDinIbnHisham.MatnQatrNada/0761JamalDinIbnHisham.MatnQatrNada.Shamela0011376-ara1#L187-L194). بصمة النسخة `2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d`.

| الحالة المدخلة | ناتج القانون المحدود |
|---|---|
| واحدة من الست، غير مخففة، وما الكافة غائبة | عمل جائز؛ إذا عملت فالاسم نصب والخبر رفع |
| ما الكافة مع غير ليت، ضمن هذا النطاق | مكفوفة؛ لا ينتج القانون زوج حالات بديلًا |
| ليت مع ما الكافة | يبقي وجهي الإعمال والإهمال |
| صورة مخففة، أو حال ما غير معلومة | `[]`، أي خارج النطاق المحسوم/غير محلول؛ ليس حكمًا بالخطأ اللغوي |

أحكام المخففات مفصلة في المصدر لكنها لم تحول هنا. ووقف العامل عن العمل لا يثبت تلقائيًا رفعًا/رفعًا ولا يثبت أن ما يليه جملة اسمية؛ ولهذا `blocked_assigns_no_cases`.

## 6. خريطة module الجديد وحدود الربط

الملف `formal/Nabt/ClassicalLanguageEvidence.lean`، namespace `Nabt.ClassicalLanguageEvidence`، هوية القانون `nabt.classical-language-evidence.v1`.

| الموضع | declarations الأساسية | النطاق |
|---|---|---|
|88–115|`course_inventory`, `surface_pairs`, `surface_not_injective`, `surface_and_regime_determine_course`|جرد8/4 وخواص التمييز داخله|
|158–179|`governed_case_pair`, `blocked_assigns_no_cases`, `kaffa_blocks_except_layta`, `layta_preserves_both_readings`, `unknown_ma_is_unresolved`, `light_form_is_outside_rule`|قانون إنّ المحدود مع شروطه وبدائله|
|192–197|`jurjani_partition_total`, `hundred_does_not_determine_partition`|التقسيم المذكور ومضاد استنتاج الهوية من المجموع|
|218–251|`Attested`, `attested_iff`, `attested_source_exact`, `attested_nonempty`, `attested_bounds`, `attested_bytes_exact`, `changed_bytes_change_source`|مقطع غير فارغ مطابق بايتًا بايتًا لمصدر موجود في السجل|
|320–349|`lexicon_entry_bound`, `entry_does_not_license_every_use`, `no_general_language_conclusion`, `no_external_event_conclusion`, `owner_inventory_is_not_jurjani`|ربط نوع النتيجة بالقانون ومنع ترقيات بلا جسر|
|369–452|`Supported`, `support_requires_interpretation`, `support_requires_reading`, `support_requires_attested_passage`, `support_work_binding`, `support_target_binding`, `support_scope_binding`, `support_rule_application`|دعم شرطي يحتاج تفسيرًا وقراءة مسجلين، ومطابقة المصدر والعمل والهدف والنطاق والتطبيق|
|454–485|`hasSupport_iff`, `judgment_supported_iff`, `absence_leaves_unestablished`, `source_only_does_not_license`, `unread_target_does_not_license`|وجود الشاهد مقابل عدم الإثبات؛ الغياب ليس نفيًا|

تظل أصالة النسخة المختارة، وصحة التفسير، وصحة قراءة الهدف، ومدلول النطاق النصي مقدمات معلنة. مساواة scope strings ليست فهمًا آليًا للسياق. ولا يربط النموذج بمجرد Hash حقيقة لغوية أو تاريخية.

المصدر التنفيذي `formal/ExportClassicalLanguageEvidence.lean` يخرج49 صفًا:8 مجارٍ و4 أسطح و36 حالة إنّ وصف تقسيم العوامل. المقارنة مع Python تثبت مطابقة هذه الدوال المحدودة فقط. لا تصفها بأنها refinement proof لجميع عمليات قراءة المصادر أو تفسيرها أو تطبيقها على العربية الحرة.

## 7. مراجعة قراءة أداة Python الجديدة

قرأت `tools/classical_language_evidence.py` قراءة مستقلة قبل دمج catalog v2. لا يثبت `GRAMMAR_APPLICATION` قراءة `target_text`: يحسب القانون على المدخل المصنف الذي قدمه المستدعي، ويُبقي `target_parsed=false` و`application_established=false` و`premises_authority=CALLER_INTERPRETED`. تبديل النص الهدف مع ثبات المدخلات لا يبطل التحقق الشرطي، لأنه لم يثبت التطبيق ابتداء. هذا حد معلن لا يجوز إخفاؤه في عرض النتائج.

النفي `MISMATCH` هو اختلاف عن المقطع أو الإسقاط أو المخرج المحدد، لا نفي لغوية النص أو وقوع حدث. لا تسمح allowlist الخاصة بالسجل باستعمال مدخل المقاييس أو جدول المالك شاهدًا على قانون إنّ. ويظل `UNIVERSAL_LANGUAGE` و`EXTERNAL_EVENT` مؤجلين. لم أجد في هذه القراءة خللًا يعبر هذه الحدود إلى تصديق خارجي. لم أنفذ اختبارات الأداة هنا؛ الوكيل التجريبي يتولاها، والرئيس يتولى البناء العام.
