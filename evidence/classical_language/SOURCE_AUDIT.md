# تدقيق مصادر الشاهد اللغوي الكلاسيكي

تاريخ المراجعة: **2026-10-24**. يغطي هذا السجل هوية النسخ، واقتناء البايتات، وحدود المقاطع، والمقابلة البصرية لتفريغ محدود من العوامل. شرح العقد والاستدلال وحدود Lean في [CLASSICAL_LANGUAGE_EVIDENCE.md](../../docs/CLASSICAL_LANGUAGE_EVIDENCE.md). السجل الآلي المختصر [source_audit_v1.json](source_audit_v1.json) قابل للمراجعة مقابل الملفات؛ لا يقوم مقام مراجعة فقه اللغة أو نتائج حواجز الإصدار.

## 1. الفهرس والهوية

الفهرس الجاري [catalog_v2.json](catalog_v2.json)، وبصمته SHA256:

`65c83b8a76c2532604f90949352caa6c2c3f03b2f0c958066a2cb20390edff3f`

تحققت هذه المراجعة من أحجام **المصادر الأربعة** وبصماتها، ومن إعادة بناء **المقاطع الثلاثة عشر** من حدود البايت والأسطر المسجلة، وصلاحية UTF-8، ووجود عنوان الجذر والوصف المقتبس في الإسقاطين المعجميين. حدود البايت تبدأ من الصفر ونهايتها مستبعدة؛ أرقام الأسطر تبدأ من 1 ونهايتها مشمولة. هذا عمل توثيق للمادة المختارة، ولا ينشئ نسبة نجاح في اكتساب اللغة.

| المصدر | البايتات | SHA256 |
|---|---:|---|
| `maqayis_shamela_21710` | 3768378 | `7f71af0dfe056cb84e7da24657fa13edc6e8061ca1980eed7f6c196bd18b5689` |
| `awamil_jurjani_minhaj_2009_excerpt` | 790 | `6fb3f23e891199facf6a4e2b7dbebbc75adaf203787583e899fa765a1943e4c7` |
| `qatr_shamela_11376` | 40168 | `2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d` |
| `sibawayhi_jk_6989` | 2639395 | `a160f940bb194e6fe7e6655d2c7f28e41f1fc648c4c5e340cc4e42306d5cb625` |

### روابط الطبعات الرقمية الثابتة

- **مقاييس اللغة**: OpenITI/0400AH عند `5bb6966d8df2ed22b1bff5cdbe29bb9c24f3ca29`، نسخة `0395IbnFarisQazwini.MucjamMaqayis.Shamela0021710-ara1`. [الملف](https://github.com/OpenITI/0400AH/blob/5bb6966d8df2ed22b1bff5cdbe29bb9c24f3ca29/data/0395IbnFarisQazwini/0395IbnFarisQazwini.MucjamMaqayis/0395IbnFarisQazwini.MucjamMaqayis.Shamela0021710-ara1). حُسب Git blob محليًا وطابق `6a8c57fd78f71f11a5dba22d479fb9dc35ea03ff`. المصدر كامل غير معدل في [maqayis.txt](sources/maqayis.txt).
- **متن قطر الندى**: OpenITI/0775AH عند `61b0c7891699554aeff8dffdb8b1a2a59d2d22ab`، نسخة `0761JamalDinIbnHisham.MatnQatrNada.Shamela0011376-ara1`. [الملف](https://github.com/OpenITI/0775AH/blob/61b0c7891699554aeff8dffdb8b1a2a59d2d22ab/data/0761JamalDinIbnHisham/0761JamalDinIbnHisham.MatnQatrNada/0761JamalDinIbnHisham.MatnQatrNada.Shamela0011376-ara1)، وGit blob `daccba5aea480c1b3676c17a86e5bde3231e3d4d`.
- **الكتاب**: OpenITI/0200AH عند `599f22fe249871f602efe2e0ddc801d3742960a3`، نسخة `0180Sibawayhi.KitabSibawayhi.JK006989-ara1`. [الملف](https://github.com/OpenITI/0200AH/blob/599f22fe249871f602efe2e0ddc801d3742960a3/data/0180Sibawayhi/0180Sibawayhi.KitabSibawayhi/0180Sibawayhi.KitabSibawayhi.JK006989-ara1)، وGit blob `5252a722c3ec1ebb6839911ae492d9c3912f948c`.

النصان الموجودان أصلًا في `src/nabt/data/source_evidence` أعيدت قراءتهما ولم يعدلا أو يكررا في هذا المجلد. يصف [بيان المصدر السابق](../../src/nabt/data/source_evidence/source_manifest.json) طريق اقتنائهما؛ نص الكتاب المستعاد من نسخة Alghanem المضغوطة يطابق بايتات OpenITI، فلا يعد وجود الملفين شاهدين تاريخيين مستقلين.

## 2. نتائج قراءة الرؤوس والسياقات

رأس مقاييس يذكر عبد السلام محمد هارون، دار الفكر، 1399هـ/1979م، وستة أجزاء. لا يعطي مكان النشر أو رقم الطبعة. رأس قطر يذكر **المتن** ودار العصيمي والطبعة الأولى، ويترك المحقق والسنة بلا بيانات. رأس الكتاب يذكر عبد السلام هارون ودار الجيل وبيروت والأولى، ويترك السنة بلا بيانات. حفظ هذه الفراغات يمنع إكمال النسخة من طبعة أخرى تحمل العنوان نفسه. [بيانات مقاييس](sources/maqayis.metadata.json) و[الرؤوس الأصلية لقطر](../../src/nabt/data/source_evidence/qatr.txt) و[الكتاب](../../src/nabt/data/source_evidence/sibawayhi.txt).

قُرئت مداخل كتب وعلم وسياق البلعوم مع ما يسبقها ويتلوها. المدخل المعجمي يجمع وصفًا وتعليلًا واستشهادًا وأقوالًا منسوبة؛ لا يختزل إلى دالة تعين معنى كل استعمال. ويعلن ابن فارس في المقدمة اعتماد خمسة كتب، فيلزم حفظ علاقة التلقي والاستنباط عند طلب استقلال الدليل. [المقدمة المثبتة](https://github.com/OpenITI/0400AH/blob/5bb6966d8df2ed22b1bff5cdbe29bb9c24f3ca29/data/0395IbnFarisQazwini/0395IbnFarisQazwini.MucjamMaqayis/0395IbnFarisQazwini.MucjamMaqayis.Shamela0021710-ara1#L45-L66).

ملف [YAML للنسخة نفسها](https://github.com/OpenITI/0400AH/blob/5bb6966d8df2ed22b1bff5cdbe29bb9c24f3ca29/data/0395IbnFarisQazwini/0395IbnFarisQazwini.MucjamMaqayis/0395IbnFarisQazwini.MucjamMaqayis.Shamela0021710-ara1.yml) يحمل حقولًا قالبية للمقابلة والروابط والمعلق والتاريخ. وجود الحقل `COLLATED` بقيمة غير مملوءة لا يثبت أن النسخة قوبلت. وكذلك [توثيق OpenITI](https://openiti.org/documentation/) يبين تفاوت جودة النصوص واحتمال أن تكون نسخ متعددة رقمنات متطابقة. علامات الصفحات في ملفات OpenITI ثبتت بوصفها علامات في النص الرقمي؛ لم تقابل جميعها بصور المطبوع.

## 3. صورة عوامل الجرجاني والتفريغ المحدود

الطبعة المقابلة هي **العوامل المئة** لعبد القاهر بن عبد الرحمن بن محمد الجرجاني الشافعي، عناية أنور بن أبي بكر الشيخي الداغستاني، دار المنهاج، الأولى، 1430هـ/2009م. صفحة العنوان تذكر الوفاة 471 أو474هـ؛ سجل النسخة يحفظ هذا التردد. ISBN: `978-9953-541-17-4`.

المصدر: [Internet Archive](https://archive.org/details/ali95_20161001_1731)، و[metadata المنشور](https://archive.org/metadata/ali95_20161001_1731). الصورة 160 صفحة، وحجمها 3,702,748 بايت، وSHA256:

`0e589cd1c11d54337ce6db0fff7460540be1cc57ddabbc739d81a0e30fac4c9e`

طابقت SHA1 للتحميل `323d361caf5a9d74e5283afb6a245f286e7ee7b0` قيمة الملف في بيانات الأرشيف. هذا تثبيت للمحتوى الذي راجعناه؛ عنوان URL في الأرشيف لا يقدم تاريخ commit مماثلًا لـGitHub. الصفحة 4 في PDF للعنوان، و5 للطبع. صفحتا المتن المطبوعة 40 و41 توافقان PDF 40 و41 بحساب يبدأ من 1، أو المؤشرين 39 و40 بحساب يبدأ من الصفر.

قرأنا الصور بصريًا وقابلنا بها التفريغ المودع. في `awamil_jurjani_excerpt.txt` تقابل الأسطر 1–7 قسمة العوامل في صفحة 40؛ وتقابل الأسطر 9–13 الباء ومثاليها في صفحة 41. استبعدنا الحركات وإشارات الحواشي، ووحدنا الوقف والمسافات والأسطر، واستبعدنا المقدمة والحواشي والعناوين التحريرية الحديثة. لم نستخدم OCR شاهدًا معتمدًا؛ النص المولد آليًا من الصورة كان كثير الأخطاء. [سياسة التفريغ](sources/awamil_jurjani_excerpt.metadata.json).

نوع الشاهد `MANUALLY_REVIEWED_TRANSCRIPTION` يقتضي بقاء وساطة هذه القراءة ظاهرة. لا يثبت تطابق التفريغ المحلي آليًا صحة التفريغ من الصورة أو نسبته التاريخية. ويقتصر نقل قسمة 91+7+2 على قول المتن في الموضع المحدد؛ لم نفرغ قائمة العوامل كاملة ولم نطابق جدول المالك عليها صفًا بصف.

[فهرس دار المنهاج](https://alminhaj.com/yOxBqz) يؤيد هوية المؤلف والمحقق والـISBN، لكنه يعرض إصدارًا أحدث و208 صفحات؛ لا يستبدل صفحة الطبع في الصورة الأولى. و[جامعة طوكيو](https://ricasdb.ioc.u-tokyo.ac.jp/daiber/daiber_contents_ms90.html) تفرق بين عوامل الجرجاني القديمة وعوامل البركوي الجديدة؛ [فهرس جامعة Dokuz Eylul](https://yazmaeserler.deu.edu.tr/el-avamilul-cedide-121-131/) يورد تقسيم البركوي المختلف إلى 60 عاملًا و30 معمولًا و10 أعمال/إعراب. هذه هوية كتاب آخر، لا قراءة بديلة للعدد نفسه في كتاب الجرجاني.

## 4. سجل المقاطع الجاري

| record_id | الأسطر في الملف المحلي | نوع الشاهد |
|---|---:|---|
| `maqayis_ktb_entry` | 36419–36438 | `LEXICAL_ENTRY` |
| `maqayis_ilm_entry` | 27039–27065 | `LEXICAL_ENTRY` |
| `maqayis_blum_context` | 5273–5288 | `LEXICOGRAPHIC_ENTRY_WITH_AUTHOR_INFERENCE` |
| `maqayis_compilation_basis` | 45–66 | `AUTHOR_SOURCE_PROVENANCE` |
| `qatr_six_nouns` | 75–80 | `PRESCRIPTIVE_GRAMMAR_WITH_AUTHORED_EXAMPLES` |
| `qatr_dhu_relative_tayy` | 137–141 | `PRESCRIPTIVE_GRAMMAR_DIALECT_SCOPE` |
| `sibawayhi_reported_imperative_usage` | 2520–2536 | `REPORTED_USAGE_WITH_TRANSMISSION_AND_SCOPE_LIMIT` |
| `awamil_jurjani_partition` | 1–7 | `MANUALLY_REVIEWED_TRANSCRIPTION` |
| `awamil_jurjani_ba_examples` | 9–13 | `MANUALLY_REVIEWED_TRANSCRIPTION` |
| `sibawayhi_eight_functions` | 111–120 | `RULE_STATEMENT` |
| `qatr_inna_conditions` | 187–201 | `RULE_STATEMENT` |
| `qatr_tamyiz_disagreement` | 313–325 | `RULE_STATEMENT_WITH_DISAGREEMENT` |
| `sibawayhi_han_examples` | 12349–12350 | `REPORTED_USAGE_WITH_UNNAMED_SPEAKERS` |

يحفظ الفهرس المقاطع بشروطها وسياقها. ورود مقطع ضمنه لا يعني وجود قانون تطبيق له؛ العلاقة المسموح بها تبينها `allowed_laws`. قسمة الجرجاني وفحص مجاري سيبويه وقانون إن المحدود لها قوانين معينة. أما مواضع الخلاف والنقل وغيرها فتظل شواهد يمكن فتحها ومقارنتها دون إسناد قانون لم ينفذ.

### تصحيح تصنيف شاهد هنوك

صُنف المقطع `sibawayhi_han_examples` أولًا `AUTHOR_EXAMPLE`. عند قراءة السياق تبين أنه يبدأ **«من العرب من يقول»**؛ هذه نسبة استعمال إلى بعض العرب، ولا تصرح بأسماء المتكلمين أو بسماع جديد لنا. صُحح إلى `REPORTED_USAGE_WITH_UNNAMED_SPEAKERS` في `catalog_v2.json`. بقيت البايتات والحدود وبصمة المقطع كما هي.

حُفظ [catalog_v1.json](catalog_v1.json) ببصمته `a6663cc7e94905e117895b1bf86fcc4795781b516717c0a414944c1c63d5a47f`، و[سجل التصحيح](catalog_review_v1/classification_correction.json)، دون كتابة الدليل السابق فوقه. هذه مراجعة لنوع الاستدلال، لا تعديل للشاهد كي يوافق التصنيف.

## 5. موضع Lean وحدود إعادة الاستخدام

تثبت [وحدة NABT الجديدة](../../formal/Nabt/ClassicalLanguageEvidence.lean) خواص نموذج الدعم المشروط وقوانين محدودة مرتبطة بالمقاطع. يتطلب `Supported` تفسيرًا وقراءة للهدف واتفاق المصدر والنطاق؛ لا تمنح `Attested` وحدها تلك القراءة. صحة التفسير أو التاريخ أو قناة اقتناء البايتات ليست مبرهنات في الوحدة. كما أن مطابقة جدول تصدير محدود بمخرجات Python تختلف عن برهان كامل على كل تفاصيل قارئ الملفات والواجهة.

المراجع السابقة المثبتة ذات الصلة: [Mashru/Awamil](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/Jisr/Awamil.lean) لجدول المالك، و[Alghanem/Maqayis](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Maqayis.lean) لفهرس الجذور وترميزه، و[Mashru/Naht](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/Madlul/Naht.lean) لمعيار النحت ومثاله المضاد. جدول 100 عمل/96 لفظًا لا يتطابق مع قسمة الجرجاني لمجرد الاسم والمجموع. وبرهان عضوية 4506 جذور في مجال `28^3` لا يثبت صلاحية كل تركيب في المجال أو معنى كل وقوع؛ `witness_share` يثبت حدًا أقل من21% تحديدًا.

هذه مراجعة للمصادر والملفات المحددة، ولا تدعي إعادة بناء المستودعين السابقين كاملين. أعداد نجاح اختبارات الحزمة الجديدة وحواجز إصدارها يسجلها مسار التحقق الخاص بها؛ ليست مستنتجة من هذا التدقيق أو من كثرة الكتب أو المبرهنات.

## 6. شروط البيانات وما بقي خارج النطاق

تسجل [LICENSE-DATA.md](sources/LICENSE-DATA.md) إعلان OpenITI عن رخصة CC-BY-NC-SA-4.0 ونسب النص إلى مؤلفه ونسخته. لا تعيد رخصة MIT للكود ترخيص مادة الكتب. الإعلان على مستوى المجموعة لا يعادل تدقيقًا مستقلًا لحقوق كل مادة تحريرية حديثة. صورة العوامل الكاملة ذات المقدمة والحواشي لم تدخل شجرة المستودع؛ المودع نص محدود من أصل المتن مع بيان التحويل.

لم تثبت هذه الحزمة استقلال كل سلسلة نقل، أو وقوع كل حادثة سماع، أو صحة كل تحليل للمؤلف، أو اكتساب قراءة أهداف جديدة، أو صوغ أي كتاب كامل في Lean. المقاطع المختارة لا ترفع درجات بناء التراكيب أو الخطاب تلقائيًا، ولا تستبدل قياسًا على أهداف محجوبة. يبقى لكل توسيع مطلوبه الخاص من التوثيق والقراءة والمطابقة والاختبار.
