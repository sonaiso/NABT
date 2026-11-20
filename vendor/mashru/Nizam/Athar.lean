/-
  Nizam/Athar.lean — أثرُ كلّ عقدةٍ في المنطوق والمفهوم: الأداةُ والقسمُ والإطارُ والجملةُ والمنطوقُ والقوّةُ والدعوى والمفهوم.

  **القول.** رسالةُ المالك 2026-10-29 (ووقتُها 18:24 ولفظُها من ملخّص الجلسة بعد ضغطها)، وفيها: «… يجب ان يكون لكل عقدة أثر في المنطوق
  والمفهوم وانت لا تريد استنتاج أثر كل عقدة في الشيفرة وتهلوس كيف اطلب منك برهان وسلسلة قرار وانت لا تربط الشيفرة بالعقد والقواعد ولا تفتح
  الملفات …»، وآخرُها «نفذ وفق افضل الممارسات»؛ وقبلها (18:03): «… استنتج الربط والمخرج من الربط لبناء برهان الاكتمال». والتصميمُ وتعييناتُه قرارُ
  البنّاء.

  **ما كان.** السلسلةُ (`Nizam/Silsila.lean`) تقف عند حكم الجملة، فلا يصل منها شيءٌ إلى المنطوق ولا إلى المفهوم. والقراءةُ
  لا معجمَ لها، فما ليس حرفَ جرٍّ ولا اسمًا بعلامته فعلٌ بتعريف `Jisr.NassItar.itarat`: «إِنَّ زَيْدًا جَاءَ» و«هَلْ ذَهَبَ الْوَلَدُ» ممتنعتان لأنّ «إِنَّ»
  و«هَلْ» تُقرآن فعلين. وجدولُ العوامل المختوم (`Jisr.Awamil.table`) ومعجمُ أقسامه (`Jisr.AqsamAwamil.qismOf2`) قائمان لا تستدعيهما قراءةٌ ولا
  حكمٌ في القارئ ولا في السلسلة. وبنيةُ المنطوق في `Jisr/QaydMafhum.lean` مكتوبةٌ باليد لأمثلة ج3، وعمودُ الأسلوب (`Jisr.Awamil.uslub`) لا يصل
  بقوّة الجملة (`Jisr.SakkJumla.awwal`) ولا بقوّة نبت (`Nabt.DiscourseEvidence.Force`).

  **ما صار** — عُقَدٌ فوق السلسلة، لكلٍّ أثرٌ محسوبٌ في الشيفرة:
  * **الأداة** (`sufuf`، `sufufKalima`): صفوفُ الجدول التي يطابق نمطُ لفظها (`namat`، وتشكيلُ ستّةٍ منها `tashkilSaff`) خلايا الكلمة كما يقرؤها
    القارئ (`tatabaq`). والصفوفُ ذواتُ الصورة 82 والوصفيّةُ 18 بأرقامها (`sathiya_82`) — قسمةُ الصورة والوصف، غيرُ قسمة عمود الأسلوب (82 «الخبر»
    و18 إنشاءً)؛ ومن الثمانيةَ عشرَ إنشاءً ثلاثةٌ وصفيّة لا تُعرف بصورتها (60 لا الناهية، 61 لام الأمر، 84 الهمزة). وأثرُ المقطع فيها: «إِنْ» و«إِنَّ»
    يختلفان في مقطعٍ واحد، ولصفّ الأولى قيدُ الشرط (`adatQayd`) ولا قيدَ لصفّ الثانية (`maqta_adat`)؛ وقوّةُ «إِنْ ذَهَبَ الْوَلَدُ»
    تعليق (`athar_quwwa`)، ولا قيدَ شرطٍ في بنية الجملة (`la_shart_fi_majal`).
  * **القسم** (`muqDawr`): الكلمةُ في دورها على `qismOf2` — صفٌّ من أقسامه قسمُ الدور مدخلٌ مشهود، وصفوفٌ كلُّها بقسمٍ ليس منها قسمُ الدور مدخلٌ لم
    يُفحص، ولا شهادةَ بلا صفٍّ أو بصفٍّ بلا قسم (بتعريف `muqDawr` على `wifaq`)؛ فمقدّماتُها مدخلٌ مشهودٌ أو لم يُفحص (`muqDawr_hal`).
  * **الإطارُ والجملةُ بعد المعجم** (`uqdaItarM`، `jumlaM`): إذا كانت مقدّماتُ كلماته في أدوارها كلُّها مشهودةً فلا يتغيّر حكمُ الإطار (`itarM_sawa`، والجملةُ ذاتُ كلمات)، والمخالفُ يعلّقه
    باسمه (`itarM_muallaq`، بالربط والكلماتُ مرخَّصة)، ولا يُخرج المعجمُ في الإطار إلّا حكمَه قبله أو التعليق (`itarM_hukm`، لكلّ جملةٍ وإطار، على
    `hukm_idkhal_aw`)؛ فالجملةُ المرخَّصة أو الممتنعة بعده كذلك قبله (`jumlaM_murakhkhas`، `jumlaM_mumtani`، بالربط).
  * **المنطوق** (`adwarKalimat`، `mantuq`): كلماتُ الجملة بأدوارها في الإطار المرخَّص الأوّل (`adwarKalimat_itar`)، ولكلّ دورٍ نسبتُه بتعيين
    `Jisr.Nisab.nisbaOf` على علاقات المالك (`nisbaDawr_qiyam`)، ورموزُ الأدوار أدوارُ خانات إطار المالك (`ramz_itar`)؛ والمنطوقُ من إطارٍ مرخَّص
    (`mantuq_itar`)، والجملةُ المرخَّصة بالربط لها إطارٌ مرخَّص (`jumlaM_itar`)؛ والحكمُ المسنَد (`isnadMuq`) مقدّمةٌ للدعوى والمفهوم (بتعريفَي `uqdaDawa` و`muqMafhum`)، وحرفُ الجرّ لا
    يجتمع معه في إطارٍ من القراءة (`harfJarr_la_isnad`).
  * **القوّة** (`quwwaJumla`): بأداةٍ في الصدر فمن صفوفها ولو لم يُرخَّص للجملة إطار — أساليبُها كلُّها إنشاءٌ فإنشاء (`quwwaJumla_insha`)، و«إِنْ»
    تعليقٌ و«لَمْ» نفيٌ بـ`SakkJumla.awwal`، وما سواها «لا حكم» —؛ وبلا أداةٍ في الصدر فخبرٌ مثبت (`SakkJumla.awwal` بلا أداة) إن كانت كلمةُ الصدر
    بصورة الماضي في دور الفعل من الإطار المرخَّص (`madiSura`، `filMadi`) ولا أداةَ في الإطار (`khaliMinAdat`)، وإلّا «لا حكم». فالخبرُ المثبت لا يكون إلّا بهذه
    الشروط، والنفيُ إلّا من «لَمْ»، والتعليقُ إلّا من «إِنْ» (بتعريف `quwwaJumla`، ونصُّه `la_tarqiya`، تعريفيّة: استلزامٌ لا أكثر؛ وما تُخطئ فيه الشروطُ في الحدّ أدناه). والإنشاءُ لا يُخبر به في
    نبت (`insha_nabt` على `nonassertive_never_asserts`).
  * **الدعوى** (`uqdaDawa`، `waqiDawa`): مدخلُها الجملةُ بعد المعجم، وشرطاها الحكمُ المسنَدُ وقوّةُ الخبر؛ فترخيصُها، بالربط، إذا وفقط إذا رُخِّصت الجملة
    وكان في إطارها دورٌ إسناديّ وقوّتُها إثباتٌ أو نفي (`dawa_murakhkhas`)؛ ولا يُسأل إلّا عن واقع الدعوى المرخَّصة (`dawa_waqi`)، وقوّةُ الإنشاء لا دعوى
    لها (`insha_la_dawa`).
  * **المفهوم** (`unsurDawr`، `bunya`، `qaydJumla`، `mafahim`، `uqdaMafhum`): البنيةُ من الكلمات بأدوارها في الإطار المرخَّص — الصفُّ يعمل في دوره
    إن كان من أقسامه قسمُ الدور، ولا يعمل شرطًا، ولا غايةً إلّا حرفَ جرّ (بتعريف `saffFiDawr`)؛ وذو الأداة يشهد للاسم في دورٍ قسمُه الاسم؛ و«إنما» في الصدر
    (`innamaFi_bunya`). فالغايةُ لا تكون إلّا من صفٍّ في دور حرف الجرّ والاسمُ إلّا من ذي أداةٍ في دورٍ اسميّ (`unsurDawr_qayd`)، ولا قيدَ شرطٍ في
    المجال (`la_shart_fi_majal`)، وقيدُ المخالفة غايةٌ في دور حرف الجرّ (`qaydJumla_sinf`)، وكلُّ مفهومِ مخالفةٍ تحمله كلمةٌ في دورها (`mafhum_kalima`).
    وعقدةُ المفهوم: إذا كان انتقالُها مربوطًا وأُودعت الودائعُ الثلاث (الحمل، والأغلب، والمعطِّل) أيًّا كانت قيمُها، رخّصها الفاحصُ إذا وفقط إذا
    رُخِّصت الجملةُ بعد المعجم، وكان في إطارها دورٌ نسبتُه إسنادية، وأخرج `MantuqMafhum.jisr` على المودَع المربوط ببنية الجملة
    (`QaydMafhum.bilBunya`) مفهومَ مخالفة (`mafhum_jisr`)؛ وبلا ودائع لا تُرخَّص (`mafhum_bila_wada`)، وفي المجال لا تُرخَّص أصلًا
    (`la_mafhum_fi_majal`: الغايةُ في إطارٍ لا إسنادَ فيه)، فيسمّي المحرّكُ ما ينقصه.
  * **الأثرُ على الشاهد** (والودائعُ خالية، `wadaKhali`): كلمتا «الدَّارِ» و«الدَّارُ» تختلفان في آخر مقطعٍ وحده («رِ»، «رُ»)، و«إِلَى
    الدَّارِ» مرخَّصةٌ منطوقُها من كلمتين وعقدةُ مفهومها معلَّقة، و«إِلَى الدَّارُ» ممتنعةٌ لا منطوقَ لها وعقدةُ مفهومها مدخلٌ فاسد (`athar_maqta`)؛
    وقيدُ «إِلَى الدَّارِ» الغايةُ ولها مفهومٌ واحد، وقيدُ «فِي الدَّارِ» الاسمُ ولا مفهومَ لها وعقدةُ مفهومها «لا تنطبق» (`athar_adat`)؛ ومن صفوف «مَنْ»
    الصفُّ 71، وقيدُ «ضَرَبَ الْوَلَدُ مَنْ» الاسمُ من «الْوَلَدُ»، و«ذَهَبَ الْوَلَدُ إِلَى الدَّارِ» بلا إطارٍ مرخَّص ولا قيدٍ ولا مفهوم (`athar_dawr`؛ ولا
    قيدَ لعنصرٍ في دوره إلّا الغايةُ من صفٍّ في دور حرف الجرّ والاسمُ من ذي الأداة في دورٍ قسمُه الاسم: `unsurDawr_qayd`؛ ولا قيدَ شرطٍ في بنية
    الجملة: `la_shart_fi_majal`)؛ و«إِنَّ زَيْدًا جَاءَ» و«هَلْ ذَهَبَ الْوَلَدُ» و«لَمْ ذَهَبَ» ممتنعةٌ قبل المعجم ومعلَّقةٌ بعده، و«حَتَّى الْوَلَدُ»
    مرخَّصةٌ قبله ومعلَّقةٌ بعده (`athar_qism`)؛ ونِسَبُ أدوار ثلاث جمل (`athar_itar`)؛ وقوّةُ جملٍ بأعيانها ودعاوى بعضها (`athar_quwwa`؛ وشرطُ
    الدعوى المرخَّصة بالربط في `dawa_murakhkhas`)؛ و«إِنَّمَا» في صدر «إِنَّمَا ذَهَبَ الْوَلَدُ»، وأحدُ موانع مفهومها مشهود (`athar_innama`).

  **التعيينات** (البنّاء): نمطُ اللفظ كما كُتب في الجدول (الحرفُ بلا علامةٍ يقبل كلّ حالة، و«إ» مكسورة و«أ» غيرُ مكسورة، و«آ» همزةٌ فألف،
  و«ى» ألف، وما لم تُكتب شدّتُه لا يُضعَّف)، إلّا ستّةَ صفوفٍ كُتبت بلا شدّةٍ فشُكّلت بها (`tashkilSaff`)؛ والصفُّ الوصفيُّ ما لفظُه بفراغٍ أو اسمُ حرفٍ
  بأل؛ وقسمُ الدور (الفعلُ فعل، والجارُّ حرف، وما سواهما اسم)؛ والمخالفُ «لم يُفحص» لا «منفيّ» (القارئُ لا معجمَ له لغير الأدوات، فلا ينفي كلمةً
  أخرى بالصورة نفسِها)؛ والقوّةُ بأداةٍ من صفوف الكلمة الأولى وحدها، و«إن» و«لم» في `SakkJumla.awwal` صفّاهما وحدهما؛ وصورةُ الماضي قراءةٌ للخلايا
  (`madiSura` على `waznMadi` و`naqisQablaTa`: القطر L55–56 وL65، وفتحُ أوّله والأوزانُ تعيين) تحجب ما لا يطابقها، وكفايتُها مع الدور وخلوِّ الإطار من
  الأدوات لخبرٍ مثبت تعيين؛ والصفُّ لا يعمل شرطًا لأنّه لا إطارَ شرطٍ وجوابٍ في المجال، ولا غايةً إلّا في دور حرف الجرّ؛ ونسبةُ المضاف إليه الإضافية (ج3 س721 يسمّيها، و`Nisab` لا يعيّنها)؛
  وذو الأداة يشهد للاسم (`.marifa 4`) ولا عنصرَ للمنوَّن؛ و«إنما» في الصدر وحده؛ وقيدُ الجملة أوّلُ قيدٍ له صنفُ مخالفة وإلّا أوّلُ قيد (`qaydMin_shahid`؛
  ولا أثرَ للتقديم في المجال، فالغايةُ أوّلُ إطارها)؛ والحكمُ المسنَد والحملُ شرطان للمفهوم، والأغلبُ والمعطِّلُ مانعان (ج3 س584–586)، وما لم يُودَع منها
  لم يُفحص. وأرقامُ ج3 بترقيمين: س721 بترقيم `a2.txt` (كـ`Jisr/Nisab.lean`)، وس548–586 بترقيم التحويل `scripts/tahwil_docx.py`
  (كـ`Jisr/MantuqMafhum.lean`).

  **حدُّه** (وشواهدُه `athar_quwwa` و`athar_hadd` و`athar_hadd_sura` و`athar_hadd_itar`). الإطارُ يقرأ، بتعريف `Jisr.NassItar.itarat`، بهيكل حروف
  الجرّ الخمسة (`hurufJarr`) قبل المعجم: إطارُ «مَنْ ذَهَبَ» وإطارُ «عَلَا الْجَبَلُ» جارٌّ ومجرور، وفي إطار كلٍّ منهما مقدّمةُ كلمةٍ واحدة «مشهود»
  (`athar_hadd_itar`)؛ و«مَنْ» صفُّ «من» الجارّة أيضًا، و«عَلَا» صفُّ «على» (`sufuf_shawahid`). والإطارُ يقرأ الكلمةَ الأولى فعلًا إن لم يكن هيكلُها
  من هياكل حروف الجرّ الخمسة ولم تكن بأل، ولا آخرُ خلاياها نونٌ ساكنةٌ بعد متحرّك (`Jisr.NassItar.munawwan`؛ ومنها «إِنْ»، فلا إطارَ لـ«إِنْ ذَهَبَ
  الْوَلَدُ»: `tahaqquq/test_athar.py`)، ولا هيكلَ صورةٍ من الأسماء الستّة (`Jisr.NassItar.ismi`)، وكان بعدها ما يأخذه أحدُ أشكال الفعل
  (بتعريف `Jisr.NassItar.itarat`)، ولو كان لها صفّ («إِنَّ»، «هَلْ»)؛ ولا إطارَ لجملٍ صدورُها «حَمَى» و«أَبَى» و«حَمِيَ» (`Jisr.NassItar.haykal_fil_la_itar`)،
  و«حَمِيَ» بصورة الماضي (`athar_hadd_sura`). والمعجمُ يعلّق قراءتَها فعلًا، بالربط والكلماتُ مرخَّصة (`itarM_muallaq`)، إن كان لها صفٌّ
  وصفوفُها كلُّها ذواتُ قسمٍ ليس الفعلُ منه؛ وفي غير ذلك فمقدّمتُها في دور الفعل مشهودةٌ أو لا مقدّمةَ لها (بتعريف `muqDawr` على
  `wifaq`)، وإن كانت مقدّماتُ كلمات الإطار في أدوارها كلُّها مشهودةً والجملةُ ذاتُ كلمات فحكمُ الإطار بعده حكمُه قبله (`itarM_sawa`)؛ والجملةُ
  في `silsila` ممتنعةٌ إذا امتنعت إطاراتُها كلُّها ولم تخلُ، إن قُرئت كلماتُها كلُّها (`kullMaqrua`؛ فهي `uqdaJumla` بتعريف `jumla`) ورُبطت
  وكلماتُها مرخَّصةٌ غيرُ خالية (`Nizam.Silsila.jumla_natija`)، ولو صحّت خارجَ الأشكال الستّة («قَامَ أَبُو بَكْرٍ»): ردٌّ
  خاطئٌ معلَن. والوصفيّةُ (لا الناهية، لام الأمر، الهمزة…) لا تُعرف، فلا يُعرف بها إنشاء؛ ومن أمثلة الأمر والنهي والاستفهام بالهمزة
  (`athar_quwwa`، `athar_hadd`): «لِيَذْهَبْ زَيْدٌ» و«أَذَهَبَ الْوَلَدُ» قوّتُهما «لا حكم»، و«لَا تَذْهَبْ» قوّتُها «لا حكم» وجملتُها ممتنعة (ردٌّ خاطئ)،
  و«فَلْيَرَ زَيْدٌ» و«وَلْيَرَ زَيْدٌ» خبرٌ مثبتٌ خطأً. وفعلُ القول («أتقول») لا يُقرأ (بلا شاهد: لا دالّةَ في القطعة تقرأ القول)؛ ولا معجمَ لغير أفعال
  جدول العوامل. و«إِنْ» صدرًا تعليقٌ بتعريف `quwwaSufuf` (صفوفُها [70]: `sufuf_shawahid`)، فـ«إن» النافية (المغني س371–375) لا
  تُفرَّق منها («إِنْ أَدْرِي» تعليق: `athar_hadd_itar`).
  والخبرُ المثبت بتعريف `quwwaJumla` وحدها: جملةٌ لا أداةَ في صدرها ولا في إطارها المرخَّص، وكلمةُ صدرها في دور الفعل منه بصورة الماضي (`filMadi`).
  وصورةُ الماضي شرطٌ على الخلايا بتعريف `madiSura`، لا على صرف الكلمة ولا قسمها ولا معناها: أوّلُ خليّةٍ مفتوحةٌ حاملُها ليس من «نأيت»، والخلايا على وزنٍ
  من `waznMadi` (فَعَلَ وفَالَ وفَعَّ، وفَعْلَلَ وفَعَّلَ وفَوْعَلَ وفَاعَلَ وفَاعَّ)، أو على وزنٍ منه أو على خليّتين ثانيتُهما مفتوحة (`naqisQablaTa`)
  وبعدها تاءٌ ساكنةٌ أو مكسورة. ومن الكلمات بصورة الماضي: «سَكَتْ»، و«رَمَتْ»، و«زَارَكَ»، و«مَدَّكَ»، و«فَرَمَتْ»، و«فَلْيَرَ»، و«وَلْيَرَ»، و«كَانَتْ»،
  و«عَسَتْ»، و«جَعْفَرَ»، و«ذَلِكَ»، و«لَيْتَكَ»، و«مَعَكَ»، و«عَلَّ»، و«عَلَّكَ»، و«حَاشَ»، و«لَاتَ»؛ ومن الكلمات التي ليست بصورته: «ضَرَبْتُ»، و«ضَرَبْتَ»،
  و«سَكَتَّ»، و«ضَرَبْتُنَّ»، و«ضَرَبُوا»، و«ضَرَبَا»، و«ضَرَبْتُكَ»، و«ضَرَبُوكَ»، و«رَمَى»، و«دَعَا»، و«ضَرَبَكَ»، و«ضَرَبَكِ»، و«قَاتَلَكَ»، و«ضَرَبَتْكَ»،
  و«زَارَهُ»، و«زَارَكِ»، و«فَذَهَبَ»، و«ضُرِبَ»، و«بِئْسَ»، و«أَكْرَمَ»، و«فَلْيَذْهَبْ»، و«هَذَا»، و«لَيْسَتْ»، و«رَحِمَكَ»، و«مَاتْ»، و«لَمْ»، و«إِنْ»، و«هَلْ». والقائمتان أمثلةٌ لا
  أصناف، وشواهدُهما `athar_hadd_sura`؛ وفروقُ نسخ `madiSura` على صيغٍ مولَّدةٍ بأصنافها في `tahaqquq/dawabit/athar/madi_farq.md` (عدُّ أداة). ولا يفحص
  المحرّكُ أنّ كلمةَ الصدر التي لا صفَّ لها فعل؛ ومن الكلمات بصورة الماضي ما هو فعلٌ في اللسان: «مَعَكَ» (س191916 «معكه في التراب يمعكه»)، و«عَلَّكَ» (س209944 «وعله
  يعله ويعله إذا سقاه السقية الثانية»)، و«عَلَّ» (س209946 «عل الرجل يعل من المرض»)، و«حَاشَ» (س122916 «وحاش الذئب الغنم»)، و«لَاتَ» (س31016 «لاته
  حقه يليته»).
  فالجملةُ التي لا أداةَ في صدرها: إن كانت كلمةُ صدرها في دور الفعل من إطارها المرخَّص بصورة الماضي ولا أداةَ في الإطار فخبرٌ مثبتٌ أيًّا كان
  معناها وقسمُ كلمتها وصرفُها؛ ومنه عشرُ جملٍ بدعوى مرخَّصة (`athar_hadd`): «رَحِمَ اللَّهُ زَيْدًا»، و«جَعْفَرَ زَيْدٌ»، و«ذَلِكَ الْكِتَابُ»، و«مَعَكَ
  زَيْدٌ»، و«لَيْتَكَ قَائِمٌ»، و«عَلَّكَ قَائِمٌ»، و«كَانَتْ هِنْدٌ»، و«عَسَتْ هِنْدٌ»، و«فَلْيَرَ زَيْدٌ»، و«وَلْيَرَ زَيْدٌ». وفيها ما ليس خبرًا، فقوّتُه خطأ:
  الدعاءُ («رَحِمَ اللَّهُ زَيْدًا» إن كانت دعاءً؛ والكتاب س3291: «وكما أن رحمة الله عليه فيه معنى رحمه الله»، وس1486–1489: «واعلم أن الدعاء بمنزلة الأمر والنهى …»، و«زيدا قطع الله يده … لأن معناه معنى زيدا ليقطع الله
  يده»)، والتمنّي («لَيْتَكَ قَائِمٌ»)، والترجّي («عَلَّكَ قَائِمٌ» إن كان «عَلّ» فيها لغةً في «لعلّ»، المغني س3509–3510) — وأسلوبا «ليت» و«لعلّ» في
  `Jisr/AwamilUslub.lean` «التمني» و«الترجي» —، والأمرُ («فَلْيَرَ زَيْدٌ» و«وَلْيَرَ زَيْدٌ»). وكلمةُ صدر «جَعْفَرَ زَيْدٌ» اسم، و«ذَلِكَ الْكِتَابُ»
  اسمُ إشارة، و«مَعَكَ زَيْدٌ» ظرفٌ وضميرٌ إن لم يكن «مَعَكَ» فيها فعلًا، و«لَيْتَكَ قَائِمٌ» حرفٌ متّصلٌ به ضمير، و«عَلَّكَ قَائِمٌ» حرفٌ متّصلٌ به ضميرٌ
  إن كان «عَلّ» فيها لغةً في «لعلّ» (و«مَعَكَ» و«عَلَّكَ» فعلان في اللسان، أعلاه).
  وإلّا فـ«لا حكم» ولو كانت كلمةُ صدرها ماضيًا (ردٌّ لا خطأ). ومنه «أَكْرَمَ زَيْدٌ» و«فَلْيَذْهَبْ زَيْدٌ» و«هَذَا زَيْدٌ» و«لَيْسَتْ هِنْدٌ» و«رَحِمَكَ اللَّهُ»: جملٌ مرخَّصةٌ
  قوّتُها «لا حكم» (`athar_hadd_sura`). وقوّةُ «الْوَلَدُ ذَاهِبٌ» و«زَيْدٌ قَائِمٌ» «لا حكم» (`athar_hadd_sura`)، وقوّةُ «كَانَ الْوَلَدُ» «لا حكم»
  (`athar_quwwa`). والإنشاءُ لا يرخَّص في المجال استنتاجًا لا مبرهنة (وأداةُ الصدر وجملتُها بعدها — «هل» قبل الفعل، المغني س8095–8116 — لم
  تُبنَ). ومفهومُ المخالفة في
  المجال من غايةٍ في دور حرف الجرّ وحده (`mafahim_mukhalafa`، `qaydJumla_sinf`)، ولا يُرخَّص أبدًا (`la_mafhum_fi_majal`)؛ وأداةُ الشرط لا تقيّد (لا إطارَ شرط؛
  `la_shart_fi_majal`)؛ والصفةُ والعددُ لا يُحسبان قيدًا (`unsurDawr_qayd`)، والقيدُ واحدٌ في الجملة (بتعريف `qaydJumla` على `qaydMin`)؛ والودائعُ الثلاث لم تُودَع.
  ولا تستدعي هذه العُقَدَ قراءةٌ ولا حكمٌ في القارئ ولا في السلسلة؛ وتنفيذُها `Qari/Athar.lean` (التنفيذيّ `athar`)، ويحرس مخرجَه
  `tahaqquq/test_athar.py`.

  **العدّ** بالمعيار الموحَّد (`Nizam/Asas.lean`): 64 مبرهنة — 39 لكلّ (`muqDawr_hal`، `adawatItar_hal`، `hukm_idkhal`، `itarM_sawa`،
  `itarM_muallaq`، `abna_min_hukm`، `itarM_murakhkhas_imp`، `itarM_mumtani_imp`، `jumlaM_murakhkhas`، `jumlaM_mumtani`، `hukm_idkhal_aw`،
  `itarM_hukm`، `ramz_itar`، `harfJarr_la_isnad`، `itarMurakhkhas_spec`، `adwarKalimat_itar`، `mantuq_itar`، `jumlaM_itar`، `insha_nabt`،
  `quwwaSufuf_insha`، `quwwaJumla_insha`، `dawa_murakhkhas`، `dawa_waqi`، `insha_la_dawa`، `unsurDawr_qayd`، `la_shart_fi_majal`، `innamaFi_bunya`،
  `qaydJumla_mem`، `qaydJumla_dawr`، `mashud_qaydJumla`، `qaydJumla_anwa`، `qaydJumla_sinf`، `mafhum_kalima`، `mafahim_eq`، `mafhum_bila_wada`،
  `muqMafhum_matlub`، `mafahim_mukhalafa`، `mafhum_jisr`، `la_mafhum_fi_majal`)، و9 تعريفيّة (`mem_sufuf`، `hukm_muqaddimat`، `jumlaM_marbut`،
  `isnadMuq_matlub`، `la_tarqiya`، `forceOfUslub_assertive`، `shartQuwwa_matlub`، `adatQayd_anwa`، `qaydMuq_matlub`)، و16 على الشاهد (`sathiya_82`،
  `sufuf_shawahid`، `maqta_adat`، `nisbaDawr_qiyam`، `unsurQayd_innama`، `qaydMin_shahid`، `athar_maqta`، `athar_adat`، `athar_dawr`، `athar_qism`، `athar_itar`،
  `athar_quwwa`، `athar_hadd`، `athar_hadd_sura`، `athar_hadd_itar`، `athar_innama`). ومساعدٌ خاصٌّ واحد (`ite_mawani`، تعريفيّة). بلا sorry ولا axiom ولا native_decide.
-/
import Nizam.Silsila
import Jisr.AqsamAwamil
import Jisr.Nisab
import Jisr.QaydMafhum
import Jisr.SakkJumla
import Nabt.DiscourseEvidence

namespace Nizam.Athar

open Nizam.Shahada Nizam.Silsila
open SLGE.Cat (Kind)

/-! ## ١. عقدةُ الأداة: صورةُ الكلمة وصفوفُ جدول العوامل -/

/-- لفظُ الصفّ i في جدول العوامل المختوم، وصنفُه، وأسلوبُه. -/
def lafz (i : Nat) : String := (Jisr.Awamil.table[i]?.map (·.1)).getD ""
def sinf (i : Nat) : Nat := (Jisr.Awamil.table[i]?.map (·.2.1)).getD 0
def uslub (i : Nat) : String := (Jisr.Awamil.uslub[i]?.map (·.2)).getD ""

/-- صورةُ اللفظ: ما قبل القوس، بلا فراغٍ في آخره («حتى (جر)» ← «حتى»). -/
def suraLafz (s : String) : List Char :=
  ((s.toList.takeWhile (· != '(')).reverse.dropWhile (· == ' ')).reverse

/-- **الصفُّ ذو الصورة:** لفظُه كلمةٌ واحدة (بلا فراغ) ليست اسمَ حرفٍ («الباء»، «الهمزة»…). وما سواه وصفٌ لا صورة: 18 صفًّا. -/
def sathiya (i : Nat) : Bool :=
  let s := suraLafz (lafz i)
  !s.isEmpty && !s.contains ' ' && !(s.take 2 == ['ا', 'ل'])

/-- حرفٌ في صورة اللفظ: حاملُه، والحالاتُ التي تقبلها خليّتُه، وهل عليه شدّة. -/
structure Harf where
  h : Nat
  st : List Nat
  shadda : Bool
  deriving DecidableEq, Repr

/-- كلُّ الحالات. -/
def kull : List Nat := [0, 1, 2, 3]

/-- الحركةُ المكتوبة: الفتحة 0، والضمّة 1، والكسرة 2، والسكون 3. -/
def haraka? (c : Char) : Option Nat :=
  if c == 'َ' then some 0 else if c == 'ُ' then some 1 else if c == 'ِ' then some 2
  else if c == 'ْ' then some 3 else none

/-- خطوةُ قراءة اللفظ (والمقروءُ مقلوبٌ أوّلُه آخرُه): الحرفُ يُضاف بحاملِه من `Dal.hawamil` وكلِّ الحالات؛ والحركةُ تقيّد آخرَ
    حرف، والشدّةُ تُعلَّم عليه. ومقعدُ الهمزة يحمل حالتَها (إ مكسورة، أ غيرُ مكسورة)، و«آ» همزةٌ مفتوحةٌ فألفٌ ساكنة، و«ى» ألف — كما
    يقرؤها القارئ (`Dal.QiraaTahsil.qiraa`). -/
def khatwa (acc : List Harf) (c : Char) : List Harf :=
  match haraka? c with
  | some s => match acc with
    | x :: r => { x with st := [s] } :: r
    | [] => []
  | none =>
    if c == 'ّ' then
      match acc with
      | x :: r => { x with shadda := true } :: r
      | [] => []
    else if c == 'إ' then ⟨0, [2], false⟩ :: acc
    else if c == 'أ' then ⟨0, [0, 1, 3], false⟩ :: acc
    else if c == 'آ' then ⟨2, [3], false⟩ :: ⟨0, [0], false⟩ :: acc
    else if c == 'ى' then ⟨2, kull, false⟩ :: acc
    else match Dal.hawamil.idxOf? c with
      | some h => ⟨h, kull, false⟩ :: acc
      | none => acc

/-- **نمطُ اللفظ:** خليّةٌ لكلّ حرف، وللمشدَّد خليّتان أولاهما ساكنة. والحرفُ بلا علامةٍ يقبل كلَّ حالة، وما لم تُكتب شدّتُه لا يُضعَّف:
    اللفظُ كما كُتب في الجدول المختوم. -/
def namat (s : List Char) : List (Nat × List Nat) :=
  (s.foldl khatwa []).reverse.flatMap fun x => if x.shadda then [(x.h, [3]), (x.h, x.st)] else [(x.h, x.st)]

/-- خلايا الكلمة على النمط: حاملٌ بحامل، وحالُ كلّ خليّةٍ ممّا يقبله حرفُها. -/
def tatabaq : List Nat → List (Nat × List Nat) → Bool
  | [], [] => true
  | k :: ks, (h, st) :: ps => k / 4 == h && st.contains (k % 4) && tatabaq ks ps
  | _, _ => false

/-- **شدّةُ الصفوف الستّة** (تعيين البنّاء): لفظُها في الجدول المختوم بلا شدّة، وصورتُها بها — «حتّى» (43، 57، 67)، و«ثمّ» (52)، و«لمّا» (59)،
    و«أنّى» (77). -/
def tashkilSaff : Nat → Option String
  | 43 | 57 | 67 => some "حتّى"
  | 52 => some "ثمّ"
  | 59 => some "لمّا"
  | 77 => some "أنّى"
  | _ => none

/-- نمطُ الصفّ: لفظُه في الجدول، أو تشكيلُه في `tashkilSaff`. -/
def namatSaff (i : Nat) : List (Nat × List Nat) := namat (suraLafz ((tashkilSaff i).getD (lafz i)))

/-- **عقدةُ الأداة:** صفوفُ الجدول ذواتُ الصورة التي تطابق خلايا الكلمة. -/
def sufuf (k : List Nat) : List Nat :=
  (List.range 100).filter fun i => sathiya i && tatabaq k (namatSaff i)

/-- «إِنَّمَا»: خلايا «إنّ» (صفّ 0) ثمّ «مَا» الكافّة (ميمٌ مفتوحةٌ فألفٌ ساكنة)؛ القطر L189–190. -/
def innamaK (k : List Nat) : Bool := k.length == 5 && tatabaq (k.take 3) (namatSaff 0) && k.drop 3 == [108, 11]

/-- **صفوفُ الكلمة:** صفوفُ صورتها، و«إنّ» لـ«إِنَّمَا». -/
def sufufKalima (k : List Nat) : List Nat := sufuf k ++ (if innamaK k then [0] else [])

theorem mem_sufuf (k : List Nat) (i : Nat) :
    i ∈ sufuf k ↔ i < 100 ∧ sathiya i = true ∧ tatabaq k (namatSaff i) = true := by
  simp [sufuf]

/-- **عددُ الصفوف ذوات الصورة (`sathiya`)** 82، والتي ليست ذواتِ صورةٍ ثمانيةَ عشرَ صفًّا بأرقامها. -/
theorem sathiya_82 :
    ((List.range 100).filter sathiya).length = 82 ∧
    (List.range 100).filter (fun i => !sathiya i) = [14, 15, 16, 17, 18, 40, 41, 42, 50, 51, 60, 61, 66, 68, 69, 84, 98, 99] := by
  decide +kernel

/-- خلايا الكلمة كما يقرؤها القارئ في الوصل (`Dal.QiraaTahsil.qiraa`)؛ وما ردّه فلا خلايا. -/
def khalaya (w : List Char) : List Nat := khalayaQari (Dal.QiraaTahsil.qiraa w false)

/-- **صفوفُ كلماتٍ على خلايا القارئ:** صفوفُ «إِنْ» [70]، و«إِنَّ» [0]، و«أَنْ» [62]، و«مَنْ» [35، 71، 86]،
    و«مِنْ» [35]، و«هَلْ» [85]، و«عَلَا» [38]، و«حَتَّى» [43، 57، 67]، و«لَمَّا» [59]، و«ثُمَّ» [52]؛ ولا صفَّ لـ«ذَهَبَ» ولا لـ«لِمَا»؛ وصفوفُ «إِنَّمَا»
    (`sufufKalima`) [0]. -/
theorem sufuf_shawahid :
    sufuf (khalaya "إِنْ".toList) = [70] ∧ sufuf (khalaya "إِنَّ".toList) = [0] ∧ sufuf (khalaya "أَنْ".toList) = [62] ∧
    sufuf (khalaya "مَنْ".toList) = [35, 71, 86] ∧ sufuf (khalaya "مِنْ".toList) = [35] ∧
    sufuf (khalaya "هَلْ".toList) = [85] ∧ sufuf (khalaya "عَلَا".toList) = [38] ∧
    sufuf (khalaya "ذَهَبَ".toList) = [] ∧ sufuf (khalaya "حَتَّى".toList) = [43, 57, 67] ∧
    sufuf (khalaya "لَمَّا".toList) = [59] ∧ sufuf (khalaya "ثُمَّ".toList) = [52] ∧ sufuf (khalaya "لِمَا".toList) = [] ∧
    sufufKalima (khalaya "إِنَّمَا".toList) = [0] := by
  decide +kernel

/-- **مقاطعُ «إِنْ» و«إِنَّ» وقيدُ صفّيهما:** مقطعا «إِنْ» «إِ» و«نْ»، ومقطعا «إِنَّ» «إِ» و«نَّ»؛ ولـ«إِنْ» صفٌّ واحدٌ قيدُه الشرط
    (`QaydMafhum.adatQayd`)، ولـ«إِنَّ» صفٌّ واحدٌ لا قيدَ له. -/
theorem maqta_adat :
    (Dal.Tahsil.tahsil "إِنْ".toList).map (·.nass) = ["إِ".toList, "نْ".toList] ∧
    (Dal.Tahsil.tahsil "إِنَّ".toList).map (·.nass) = ["إِ".toList, "نَّ".toList] ∧
    (sufuf (khalaya "إِنْ".toList)).map Jisr.QaydMafhum.adatQayd = [some .shart] ∧
    (sufuf (khalaya "إِنَّ".toList)).map Jisr.QaydMafhum.adatQayd = [none] := by
  decide +kernel

/-! ## ٢. عقدةُ القسم: الكلمةُ في دورها على معجم أقسام العوامل -/

open Jisr.NassItar (Dawr)

/-- أقسامُ الصفّ من معجم أقسام العوامل (`Jisr.AqsamAwamil.qismOf2`: عائلاتُ المالك ثمّ النقلُ بأسطره). -/
def qism (i : Nat) : Option (List Kind) := Jisr.AqsamAwamil.qismOf2 (lafz i) (sinf i)

/-- القسمُ الذي يقتضيه الدورُ في الإطار: الفعلُ فعل، وحرفُ الجرّ حرف، وما سواهما اسم. -/
def dawrQism : Dawr → Kind
  | .fil => .fil
  | .harfJarr => .harf
  | _ => .ism

/-- من أقسام الصفّ قسمُ الدور. -/
def saffQism (r : Nat) (d : Dawr) : Bool := (qism r).any (·.contains (dawrQism d))

/-- شهادةُ المعجم للكلمة في دورها: صفٌّ من صفوفها من أقسامه قسمُ الدور (موافق)، أو صفوفُها كلُّها لها قسمٌ وليس فيها قسمُ الدور
    (مخالف)؛ وما سوى ذلك — لا صفّ، أو صفٌّ بلا قسم — لا شهادة. -/
inductive Wifaq | muwafiq | mukhalif
  deriving DecidableEq, Repr

def wifaq (rs : List Nat) (k : Kind) : Option Wifaq :=
  if rs.isEmpty then none
  else if rs.any (fun r => (qism r).any (·.contains k)) then some .muwafiq
  else if rs.all (fun r => (qism r).isSome) then some .mukhalif
  else none

def qismIsm : Kind → String
  | .ism => "اسم" | .fil => "فعل" | .harf => "حرف"

def asmaSufuf (rs : List Nat) : String :=
  ", ".intercalate (rs.map fun r => "«" ++ String.ofList (suraLafz (lafz r)) ++ "» صفّ " ++ toString r)

def sanadAqsam : String := "Jisr.AqsamAwamil.qismOf2"

/-- **مقدّمةُ الكلمة في دورها:** المعجمُ الموافقُ مدخلٌ مشهود؛ والمخالفُ مدخلٌ لم يُفحص — صورتُها صورةُ أداةٍ ليس قسمُ الدور من أقسامها،
    والقارئُ لا معجمَ له لغير الأدوات فلا ينفي أن تكون كلمةً أخرى بالصورة نفسِها («عَلَا»، و«أَنَّ» فعلًا)؛ ولا شهادةَ بلا صفّ. -/
def muqDawr (kw : KalimaM) (d : Dawr) : List Muqaddima :=
  let rs := sufufKalima (khalaya kw.w)
  match wifaq rs (dawrQism d) with
  | some .muwafiq =>
    [⟨ismKalima kw ++ " " ++ dawrIsm d ++ ": " ++ qismIsm (dawrQism d) ++ " بقسم صفّها (" ++ asmaSufuf rs ++ ")",
      .madkhal, .mashhud, sanadAqsam⟩]
  | some .mukhalif =>
    [⟨ismKalima kw ++ " في دور " ++ dawrIsm d ++ ": صورتُها صورةُ أداةٍ ليس «" ++ qismIsm (dawrQism d) ++ "» من أقسامها (" ++
      asmaSufuf rs ++ ")، فقراءتُها في الدور لم تُفحص", .madkhal, .ghayrMafhus, sanadAqsam⟩]
  | none => []

/-- مقدّماتُ الكلمات في أدوار إطارٍ، بترتيبها. -/
def adawatItar (t : List Char) (ds : List Dawr) : List Muqaddima :=
  ((kalimatM t).zip ds).flatMap fun p => muqDawr p.1 p.2

theorem muqDawr_hal (kw : KalimaM) (d : Dawr) :
    ∀ m ∈ muqDawr kw d, m.naw = .madkhal ∧ (m.halFiil = .mashhud ∨ m.halFiil = .ghayrMafhus) := by
  intro m hm
  cases h : wifaq (sufufKalima (khalaya kw.w)) (dawrQism d) with
  | none => simp [muqDawr, h] at hm
  | some w =>
    cases w <;> simp only [muqDawr, h, List.mem_singleton] at hm <;> subst hm <;> simp [Muqaddima.halFiil, sanadAqsam]

theorem adawatItar_hal (t : List Char) (ds : List Dawr) :
    ∀ m ∈ adawatItar t ds, m.naw = .madkhal ∧ (m.halFiil = .mashhud ∨ m.halFiil = .ghayrMafhus) := by
  intro m hm
  obtain ⟨p, _, hp⟩ := List.mem_flatMap.1 hm
  exact muqDawr_hal p.1 p.2 m hp

/-! ## ٣. الإطارُ والجملةُ بعد شهادة المعجم -/

/-- **عقدةُ الإطار بعد المعجم:** مقدّماتُ `uqdaItar` نفسُها، وبين كلماتها المرفوعة وشرطِ الحدّ مقدّماتُ الكلمات في أدوارها. -/
def uqdaItarM (t : List Char) (x : List Dawr × Jisr.Utur.Itar3) : Naqla String String :=
  { uqdaU t x with muqaddimat := rafaKull (abnaJumla t) ++ adawatItar t x.1 ++ baqiItar x.2 }

/-- حكمُ الفاحص لا يرى من الانتقال إلّا ربطَه ومقدّماتِه. -/
theorem hukm_muqaddimat {α β γ δ : Type} (n : Naqla α β) (n' : Naqla γ δ) (hb : n.marbut = n'.marbut)
    (hm : n.muqaddimat = n'.muqaddimat) : hukm n = hukm n' := by
  unfold hukm awwalNaqid naqisa naqisaMadkhal fihiMadkhal
  rw [hb, hm]

/-- **إدخالُ مدخلٍ مشهود لا يغيّر الحكم** حيث للمدخل مقدّمةٌ قبله. -/
theorem hukm_idkhal {α β : Type} (n : Naqla α β) (A X B : List Muqaddima) (hn : n.muqaddimat = A ++ B)
    (hX : ∀ m ∈ X, m.naw = .madkhal ∧ m.halFiil = .mashhud) (hA : ∃ m ∈ A, m.naw = .madkhal) :
    hukm { n with muqaddimat := A ++ X ++ B } = hukm n := by
  have hfind : ∀ k : Naw, X.find? (fun m => m.naw == k && m.halFiil == naqid k) = none := by
    intro k
    refine List.find?_eq_none.2 fun m hm => ?_
    obtain ⟨hk, hh⟩ := hX m hm
    cases k <;> simp [hh, hk, naqid]
  have hfil1 : X.filter (fun m => m.halFiil == .ghayrMafhus) = [] :=
    List.filter_eq_nil_iff.2 fun m hm => by simp [(hX m hm).2]
  have hfil2 : X.filter (fun m => m.naw == .madkhal && m.halFiil == .ghayrMafhus) = [] :=
    List.filter_eq_nil_iff.2 fun m hm => by simp [(hX m hm).2]
  have hfi1 : (A ++ X ++ B).any (fun m => m.naw == .madkhal) = true := by
    obtain ⟨m, hm, hk⟩ := hA
    exact List.any_eq_true.2 ⟨m, by simp [hm], by simp [hk]⟩
  have hfi2 : (A ++ B).any (fun m => m.naw == .madkhal) = true := by
    obtain ⟨m, hm, hk⟩ := hA
    exact List.any_eq_true.2 ⟨m, by simp [hm], by simp [hk]⟩
  simp only [hukm, awwalNaqid, naqisa, naqisaMadkhal, fihiMadkhal, hn, hfi1, hfi2, List.find?_append, hfind,
    List.filter_append, hfil1, hfil2, Option.or_none, List.append_nil, Naqla.marbut]

/-- **المعجمُ الموافقُ لا يغيّر حكمَ الإطار:** إن كانت مقدّماتُ كلمات الإطار في أدوارها كلُّها مشهودةً والجملةُ ذاتُ كلمات، فحكمُ الإطار بعده
    حكمُه قبله. -/
theorem itarM_sawa (t : List Char) (x : List Dawr × Jisr.Utur.Itar3) (hk : abnaJumla t ≠ [])
    (h : ∀ m ∈ adawatItar t x.1, m.halFiil = .mashhud) :
    hukm (uqdaItarM t x) = hukm (uqdaU t x) :=
  hukm_idkhal (uqdaU t x) (rafaKull (abnaJumla t)) (adawatItar t x.1) (baqiItar x.2) rfl
    (fun m hm => ⟨(adawatItar_hal t x.1 m hm).1, h m hm⟩) (rafaKull_madkhal hk)

/-- **والمخالفُ يعلِّقه باسمه:** بالربط وكلماتُ الجملة مرخَّصة، كلمةٌ في دورٍ صورتُها صورةُ أداةٍ ليس قسمُ الدور من أقسامها تُخرج التعليقَ وفيه اسمُها —
    لا ترخيصًا ولا امتناعًا، أيًّا كان حكمُ `hukmSitta`. -/
theorem itarM_muallaq (t : List Char) (x : List Dawr × Jisr.Utur.Itar3) (hb : (uqdaU t x).marbut = true)
    (hall : ∀ c ∈ abnaJumla t, c.2 = .murakhkhas) (m : Muqaddima) (hm : m ∈ adawatItar t x.1)
    (hg : m.halFiil = .ghayrMafhus) :
    ∃ l, hukm (uqdaItarM t x) = .muallaq l ∧ m.ism ∈ l := by
  have hrk := rafaKull_mashhud hall
  have hmem : m ∈ (uqdaItarM t x).muqaddimat := by
    simp only [uqdaItarM, List.mem_append]; exact Or.inl (Or.inr hm)
  have hk : m.naw = .madkhal := (adawatItar_hal t x.1 m hm).1
  have hd : awwalNaqid (uqdaItarM t x) .madkhal = none := by
    refine (awwalNaqid_none _ .madkhal).2 fun m' hm' hk' e => ?_
    simp only [uqdaItarM, List.mem_append] at hm'
    rcases hm' with (hm' | hm') | hm'
    · rw [(hrk m' hm').2] at e; cases e
    · rcases (adawatItar_hal t x.1 m' hm').2 with h | h <;> rw [h] at e <;> cases e
    · exact baqiItar_naw x.2 m' hm' hk'
  refine ⟨_, madkhal_ghayrMafhus_yuallaq _ hb hd m hmem hk hg, ?_⟩
  have hfi : fihiMadkhal (uqdaItarM t x) = true := List.any_eq_true.2 ⟨m, hmem, by simp [hk]⟩
  simp only [naqisaMadkhal, hfi, ite_true]
  exact List.mem_map.2 ⟨m, List.mem_filter.2 ⟨hmem, by simp [hk, hg]⟩, rfl⟩

/-- الإطاراتُ بأحكام الفاحص عليها بعد المعجم. -/
def uturNatijaM (t : List Char) : List (String × Natija) :=
  birraqm (utur t) fun i x => (ismItar i x.1, hukm (uqdaItarM t x))

/-- **عقدةُ الجملة بعد المعجم:** عقدةُ `jumla` بعينها، وإطاراتُها بأحكامها بعد المعجم. -/
def jumlaM (t : List Char) : Naqla String String :=
  let n := uqdaJumla (masdarJumla t) (spanJumla t) (String.ofList t) (abnaJumla t) (uturNatijaM t)
  if kullMaqrua t then n
  else { n with muqaddimat := rafaKull (abnaJumla t) ++ [⟨ismLamTuqra, .shart, .ghayrMafhus, ""⟩] }

theorem jumlaM_marbut (t : List Char) : (jumlaM t).marbut = (jumla t).marbut := by
  unfold jumlaM jumla; split <;> rfl

/-- الكلماتُ في جملةٍ مرخَّصةٍ أو ممتنعة مرخَّصةٌ كلُّها، ولها كلمة. -/
theorem abna_min_hukm (src : Nabt.UnitDiscovery.Source Char) (sp : Nabt.UnitDiscovery.Span) (md : String)
    (ks fs : List (String × Natija))
    (h : hukm (uqdaJumla src sp md ks fs) = .murakhkhas ∨ ∃ x, hukm (uqdaJumla src sp md ks fs) = .mumtani x) :
    ks ≠ [] ∧ ∀ c ∈ ks, c.2 = .murakhkhas := by
  obtain ⟨_, ⟨m, hm, hk⟩, hall⟩ := hukm_bi_madkhal_mashhud _ (by
    rcases h with h | h
    · exact Or.inl h
    · exact Or.inr (Or.inl h))
  have hmq : (uqdaJumla src sp md ks fs).muqaddimat = rafaKull ks ++ baqiJumla fs := rfl
  rw [hmq] at hm hall
  refine ⟨?_, (rafaKull_matlub ks).1 fun m' hm' => ?_⟩
  · rcases List.mem_append.1 hm with hm | hm
    · exact rafaKull_nil_madkhal ⟨m, hm, hk⟩
    · exact absurd hk (baqiJumla_naw fs m hm)
  · obtain ⟨c, _, hc⟩ := List.mem_flatMap.1 hm'
    have hn := rafa_naw c.1 c.2 m' hc
    rw [hall m' (List.mem_append_left _ hm') hn, hn]; rfl

theorem itarM_murakhkhas_imp (t : List Char) (x : List Dawr × Jisr.Utur.Itar3) (hk : abnaJumla t ≠ [])
    (h : hukm (uqdaItarM t x) = .murakhkhas) : hukm (uqdaU t x) = .murakhkhas := by
  by_cases ha : ∀ m ∈ adawatItar t x.1, m.halFiil = .mashhud
  · rwa [← itarM_sawa t x hk ha]
  · exfalso
    obtain ⟨m, hm, hne⟩ : ∃ m ∈ adawatItar t x.1, m.halFiil ≠ .mashhud :=
      Classical.byContradiction fun hno => ha fun m hm => Classical.byContradiction fun hne => hno ⟨m, hm, hne⟩
    have hg : m.halFiil = .ghayrMafhus := ((adawatItar_hal t x.1 m hm).2).resolve_left hne
    exact ghayrMafhus_la_yurakhkhis _ m (by simp only [uqdaItarM, List.mem_append]; exact Or.inl (Or.inr hm)) hg h

theorem itarM_mumtani_imp (t : List Char) (x : List Dawr × Jisr.Utur.Itar3) (hb : (jumla t).marbut = true)
    (hk : abnaJumla t ≠ []) (hall : ∀ c ∈ abnaJumla t, c.2 = .murakhkhas)
    (h : ∃ y, hukm (uqdaItarM t x) = .mumtani y) : ∃ y, hukm (uqdaU t x) = .mumtani y := by
  by_cases ha : ∀ m ∈ adawatItar t x.1, m.halFiil = .mashhud
  · rwa [← itarM_sawa t x hk ha]
  · exfalso
    obtain ⟨m, hm, hne⟩ : ∃ m ∈ adawatItar t x.1, m.halFiil ≠ .mashhud :=
      Classical.byContradiction fun hno => ha fun m hm => Classical.byContradiction fun hne => hno ⟨m, hm, hne⟩
    have hg : m.halFiil = .ghayrMafhus := ((adawatItar_hal t x.1 m hm).2).resolve_left hne
    obtain ⟨l, hl, _⟩ := itarM_muallaq t x (by rw [uqdaU_marbut]; exact hb) hall m hm hg
    obtain ⟨y, hy⟩ := h
    rw [hl] at hy; cases hy

/-- **المعجمُ لا يرخّص ما لم يُرخَّص:** بالربط، الجملةُ المرخَّصة بعد المعجم مرخَّصةٌ قبله. -/
theorem jumlaM_murakhkhas (t : List Char) (hb : (jumla t).marbut = true)
    (h : hukm (jumlaM t) = .murakhkhas) : hukm (jumla t) = .murakhkhas := by
  by_cases hkm : kullMaqrua t = true
  · have hj' : jumlaM t = uqdaJumla (masdarJumla t) (spanJumla t) (String.ofList t) (abnaJumla t) (uturNatijaM t) := by
      simp [jumlaM, hkm]
    have hj : jumla t = uqdaJumla (masdarJumla t) (spanJumla t) (String.ofList t) (abnaJumla t) (uturNatija t) := by
      simp [jumla, hkm]
    rw [hj'] at h
    obtain ⟨hk0, hall⟩ := abna_min_hukm _ _ _ _ _ (Or.inl h)
    have hb' := hb
    rw [hj] at hb'
    have hb'' : (uqdaJumla (masdarJumla t) (spanJumla t) (String.ofList t) (abnaJumla t) (uturNatijaM t)).marbut = true := hb'
    have h1 := ((jumla_natija _ _ _ _ _ hb'' hk0 hall).1).1 h
    rw [uturNatijaM, birraqm_snd] at h1
    obtain ⟨x, hx, hxe⟩ := List.mem_map.1 h1
    have h2 := itarM_murakhkhas_imp t x hk0 hxe
    rw [hj]
    refine ((jumla_natija _ _ _ _ _ hb' hk0 hall).1).2 ?_
    rw [uturNatija, birraqm_snd]
    exact List.mem_map.2 ⟨x, hx, h2⟩
  · have e : hukm (jumlaM t) = hukm (jumla t) := by
      refine hukm_muqaddimat _ _ (jumlaM_marbut t) ?_
      simp [jumlaM, jumla, hkm]
    rwa [← e]

/-- **ولا يمنع ما لم يُمنع:** بالربط، الجملةُ الممتنعة بعد المعجم ممتنعةٌ قبله. -/
theorem jumlaM_mumtani (t : List Char) (hb : (jumla t).marbut = true)
    (h : ∃ y, hukm (jumlaM t) = .mumtani y) : ∃ y, hukm (jumla t) = .mumtani y := by
  by_cases hkm : kullMaqrua t = true
  · have hj' : jumlaM t = uqdaJumla (masdarJumla t) (spanJumla t) (String.ofList t) (abnaJumla t) (uturNatijaM t) := by
      simp [jumlaM, hkm]
    have hj : jumla t = uqdaJumla (masdarJumla t) (spanJumla t) (String.ofList t) (abnaJumla t) (uturNatija t) := by
      simp [jumla, hkm]
    rw [hj'] at h
    obtain ⟨hk0, hall⟩ := abna_min_hukm _ _ _ _ _ (Or.inr h)
    have hb' := hb
    rw [hj] at hb'
    have hb'' : (uqdaJumla (masdarJumla t) (spanJumla t) (String.ofList t) (abnaJumla t) (uturNatijaM t)).marbut = true := hb'
    obtain ⟨hne, hallm⟩ := ((jumla_natija _ _ _ _ _ hb'' hk0 hall).2).1 h
    rw [uturNatijaM, birraqm_snd] at hne hallm
    rw [hj]
    refine ((jumla_natija _ _ _ _ _ hb' hk0 hall).2).2 ⟨?_, ?_⟩
    · rw [uturNatija, birraqm_snd]; simpa using hne
    · rw [uturNatija, birraqm_snd]
      intro v hv
      obtain ⟨x, hx, rfl⟩ := List.mem_map.1 hv
      have := hallm _ (List.mem_map.2 ⟨x, hx, rfl⟩)
      rw [mumtaniB_iff] at this ⊢
      exact itarM_mumtani_imp t x hb hk0 hall this
  · have e : hukm (jumlaM t) = hukm (jumla t) := by
      refine hukm_muqaddimat _ _ (jumlaM_marbut t) ?_
      simp [jumlaM, jumla, hkm]
    rwa [← e]


/-- **إدخالُ مدخلٍ مشهودٍ أو لم يُفحص لا يُخرج إلّا الحكمَ نفسَه أو التعليق** حيث للمدخل مقدّمةٌ قبله: المدخلُ المنقوضُ قبله أو بعده يُخرج
    الفسادَ نفسَه، وما لم يُفحص منه يعلِّق قبل أيّ حكمٍ آخر (`madkhal_ghayrMafhus_yuallaq`). -/
theorem hukm_idkhal_aw {α β : Type} (n : Naqla α β) (A X B : List Muqaddima) (hn : n.muqaddimat = A ++ B)
    (hX : ∀ m ∈ X, m.naw = .madkhal ∧ (m.halFiil = .mashhud ∨ m.halFiil = .ghayrMafhus))
    (hA : ∃ m ∈ A, m.naw = .madkhal) :
    hukm { n with muqaddimat := A ++ X ++ B } = hukm n ∨ ∃ l, hukm { n with muqaddimat := A ++ X ++ B } = .muallaq l := by
  by_cases hall : ∀ m ∈ X, m.halFiil = .mashhud
  · exact Or.inl (hukm_idkhal n A X B hn (fun m hm => ⟨(hX m hm).1, hall m hm⟩) hA)
  · obtain ⟨m, hm, hne⟩ : ∃ m ∈ X, m.halFiil ≠ .mashhud :=
      Classical.byContradiction fun hno => hall fun m hm => Classical.byContradiction fun hne => hno ⟨m, hm, hne⟩
    have hg : m.halFiil = .ghayrMafhus := ((hX m hm).2).resolve_left hne
    have hfind : X.find? (fun m => m.naw == .madkhal && m.halFiil == naqid .madkhal) = none := by
      refine List.find?_eq_none.2 fun m' hm' => ?_
      rcases (hX m' hm').2 with h | h <;> simp [h, naqid]
    have hd : awwalNaqid { n with muqaddimat := A ++ X ++ B } .madkhal = awwalNaqid n .madkhal := by
      simp only [awwalNaqid, hn, List.find?_append, hfind, Option.or_none]
    cases hb : n.marbut with
    | false =>
      left
      have hb' : ({ n with muqaddimat := A ++ X ++ B } : Naqla α β).marbut = false := hb
      rw [ghayrMarbut_awwalan _ hb', ghayrMarbut_awwalan _ hb]
    | true =>
      have hb' : ({ n with muqaddimat := A ++ X ++ B } : Naqla α β).marbut = true := hb
      cases hd0 : awwalNaqid n .madkhal with
      | some x =>
        left
        have e1 : hukm { n with muqaddimat := A ++ X ++ B } = .madkhalFasid x := by
          simp only [hukm, hb', ite_true, hd, hd0, hukmMarbut]
        have e2 : hukm n = .madkhalFasid x := by simp only [hukm, hb, ite_true, hd0, hukmMarbut]
        rw [e1, e2]
      | none =>
        right
        exact ⟨_, madkhal_ghayrMafhus_yuallaq _ hb' (hd.trans hd0) m (by simp [hm]) (hX m hm).1 hg⟩

/-- **المعجمُ لا يُخرج في الإطار إلّا حكمَه قبله أو التعليق:** لكلّ جملةٍ وإطار. -/
theorem itarM_hukm (t : List Char) (x : List Dawr × Jisr.Utur.Itar3) :
    hukm (uqdaItarM t x) = hukm (uqdaU t x) ∨ ∃ l, hukm (uqdaItarM t x) = .muallaq l := by
  by_cases hk : abnaJumla t = []
  · left
    have hkm : kalimatM t = [] := by simpa [abnaJumla] using hk
    refine hukm_muqaddimat _ _ rfl ?_
    show rafaKull (abnaJumla t) ++ adawatItar t x.1 ++ baqiItar x.2 = rafaKull (abnaJumla t) ++ baqiItar x.2
    simp [adawatItar, hkm]
  · exact hukm_idkhal_aw (uqdaU t x) (rafaKull (abnaJumla t)) (adawatItar t x.1) (baqiItar x.2) rfl
      (adawatItar_hal t x.1) (rafaKull_madkhal hk)

/-! ## ٤. عقدةُ المنطوق: الكلماتُ بأدوارها في الإطار المرخَّص ونسبُها -/

open Jisr.Nisab (Nisba nisbaOf)

/-- رمزُ الدور في أطر المالك: الفعلُ مسنَد (2)، والفاعلُ فاعليّة (3)، والمفعولُ مفعوليّة (4)، والجارُّ عامل (5)، والمجرورُ تعلّق (6)؛
    والمضافُ إليه ملحقٌ لا رمزَ له في أطر المالك. -/
def ramzDawr : Dawr → Option Nat
  | .fil => some 2 | .fail => some 3 | .maful => some 4 | .harfJarr => some 5 | .majrur => some 6 | .mudafIlayh => none

/-- **نسبةُ الدور** بتعيين `Jisr.Nisab.nisbaOf` على علاقات المالك (`SLGE.Simat.semOf`) الذي أمضاه المالك 2026-10-16؛ والمضافُ إليه الإضافيةُ
    (ج3 س721 بترقيم `a2.txt` يسمّيها، وتعيينُها هنا للبنّاء). -/
def nisbaDawr (d : Dawr) : Option Nisba :=
  match ramzDawr d with
  | some r => nisbaOf (SLGE.Simat.semOf r)
  | none => some .idafiyya

theorem nisbaDawr_qiyam :
    [Dawr.fil, .fail, .maful, .harfJarr, .majrur, .mudafIlayh].map nisbaDawr =
      [some .isnadiyya, some .isnadiyya, some .taqyidiyya, none, some .idafiyya, some .idafiyya] := by decide

/-- **رموزُ الأدوار هي أدوارُ خانات المالك في الإطار:** لكلّ إطارٍ من القراءة، رموزُ أدواره (بلا المضاف إليه) أوّلُ أدوار خانات إطار
    المالك فيه (`Mulhaqat.darabaZayd`، `Mulhaqat.daraba`، `Mulhaqat.bikam`؛ وفي الجارّ والمجرور بعدها خانةُ المتعلَّق المقدَّر). -/
theorem ramz_itar (ws : List Dal.Kalima) (x : List Dawr × Jisr.Utur.Itar3) (h : x ∈ Jisr.NassItar.itarat ws) :
    ∃ r, x.2.jisr.ud.f.2.2.map (·.1) = x.1.filterMap ramzDawr ++ r := by
  rcases Jisr.NassItar.itarat_mem ws x h with ⟨p, n, mi, -, rfl⟩ | ⟨v, s, mi, -, rfl⟩ | ⟨v, s, o, mi, -, rfl⟩
  · exact ⟨[8], by cases mi <;> rfl⟩
  · exact ⟨[], by cases mi <;> rfl⟩
  · exact ⟨[], by cases mi <;> rfl⟩

/-- **حرفُ الجرّ لا يجتمع مع نسبةٍ إسنادية في إطارٍ من القراءة:** حرفُ الجرّ في إطار الجارّ والمجرور وحده، ولا دورَ فيه نسبتُه إسنادية. -/
theorem harfJarr_la_isnad (ws : List Dal.Kalima) (x : List Dawr × Jisr.Utur.Itar3) (h : x ∈ Jisr.NassItar.itarat ws)
    (hj : Dawr.harfJarr ∈ x.1) : x.1.any (fun d => nisbaDawr d == some .isnadiyya) = false := by
  rcases Jisr.NassItar.itarat_mem ws x h with ⟨p, n, mi, -, rfl⟩ | ⟨v, s, mi, -, rfl⟩ | ⟨v, s, o, mi, -, rfl⟩
  · cases mi <;> rfl
  · cases mi <;> simp [Jisr.NassItar.itarFail] at hj
  · cases mi <;> simp [Jisr.NassItar.itarMaful] at hj

/-- الإطارُ المرخَّص الأوّل بعد المعجم. -/
def itarMurakhkhas (t : List Char) : Option (List Dawr × Jisr.Utur.Itar3) :=
  (utur t).find? fun x => hukm (uqdaItarM t x) == .murakhkhas

theorem itarMurakhkhas_spec (t : List Char) {x : List Dawr × Jisr.Utur.Itar3} (h : itarMurakhkhas t = some x) :
    x ∈ utur t ∧ hukm (uqdaItarM t x) = .murakhkhas := by
  have h' : (utur t).find? (fun x => hukm (uqdaItarM t x) == .murakhkhas) = some x := h
  exact ⟨List.mem_of_find?_eq_some h', by simpa using List.find?_some h'⟩

/-- **كلماتُ الجملة بأدوارها في الإطار المرخَّص الأوّل:** عليها يقوم المنطوقُ وبنيةُ المفهوم؛ ولا شيءَ بلا إطارٍ مرخَّص. -/
def adwarKalimat (t : List Char) : List (KalimaM × Dawr) :=
  match itarMurakhkhas t with
  | some x => (kalimatM t).zip x.1
  | none => []

/-- كلُّ كلمةٍ بدورها من إطارٍ رخّصه الفاحص بعد المعجم. -/
theorem adwarKalimat_itar (t : List Char) {p : KalimaM × Dawr} (h : p ∈ adwarKalimat t) :
    ∃ x ∈ utur t, hukm (uqdaItarM t x) = .murakhkhas ∧ p ∈ (kalimatM t).zip x.1 := by
  unfold adwarKalimat at h
  cases hx : itarMurakhkhas t with
  | none => simp [hx] at h
  | some x =>
    rw [hx] at h
    obtain ⟨hm, he⟩ := itarMurakhkhas_spec t hx
    exact ⟨x, hm, he, h⟩

/-- **المنطوق:** لكلّ كلمةٍ دورُها في الإطار المرخَّص ونسبتُه؛ ولا منطوقَ بلا إطارٍ مرخَّص. -/
def mantuq (t : List Char) : List (String × Dawr × Option Nisba) :=
  (adwarKalimat t).map fun p => (ismKalima p.1, p.2, nisbaDawr p.2)

/-- **المنطوقُ من إطارٍ مرخَّص:** كلُّ منطوقٍ أدوارُه أدوارُ إطارٍ رخّصه الفاحص بعد المعجم، على كلمات الجملة بترتيبها. -/
theorem mantuq_itar (t : List Char) (h : mantuq t ≠ []) :
    ∃ x ∈ utur t, hukm (uqdaItarM t x) = .murakhkhas ∧
      (mantuq t).map (·.2.1) = ((kalimatM t).zip x.1).map (·.2) := by
  unfold mantuq adwarKalimat at h ⊢
  cases hx : itarMurakhkhas t with
  | none => simp [hx] at h
  | some x =>
    obtain ⟨hm, he⟩ := itarMurakhkhas_spec t hx
    refine ⟨x, hm, he, ?_⟩
    simp [List.map_map, Function.comp_def]

/-- **والجملةُ المرخَّصة لها منطوق:** بالربط، ترخيصُ الجملة بعد المعجم يُخرج إطارًا مرخَّصًا. -/
theorem jumlaM_itar (t : List Char) (hb : (jumla t).marbut = true) (h : hukm (jumlaM t) = .murakhkhas) :
    ∃ x, itarMurakhkhas t = some x := by
  by_cases hkm : kullMaqrua t = true
  · have hj' : jumlaM t = uqdaJumla (masdarJumla t) (spanJumla t) (String.ofList t) (abnaJumla t) (uturNatijaM t) := by
      simp [jumlaM, hkm]
    rw [hj'] at h
    obtain ⟨hk0, hall⟩ := abna_min_hukm _ _ _ _ _ (Or.inl h)
    have hb'' : (uqdaJumla (masdarJumla t) (spanJumla t) (String.ofList t) (abnaJumla t) (uturNatijaM t)).marbut = true := by
      rw [← hj', jumlaM_marbut]; exact hb
    have h1 := ((jumla_natija _ _ _ _ _ hb'' hk0 hall).1).1 h
    rw [uturNatijaM, birraqm_snd] at h1
    obtain ⟨x, hx, hxe⟩ := List.mem_map.1 h1
    cases hf : itarMurakhkhas t with
    | some y => exact ⟨y, rfl⟩
    | none =>
      exfalso
      have := List.find?_eq_none.1 hf x hx
      simp [hxe] at this
  · exfalso
    have hmq : (jumlaM t).muqaddimat = rafaKull (abnaJumla t) ++ [⟨ismLamTuqra, .shart, .ghayrMafhus, ""⟩] := by
      simp [jumlaM, hkm]
    exact ghayrMafhus_la_yurakhkhis _ ⟨ismLamTuqra, .shart, .ghayrMafhus, ""⟩ (by rw [hmq]; simp)
      (by simp [Muqaddima.halFiil]) h

/-- في الإطار المرخَّص دورٌ نسبتُه إسنادية. -/
def isnadFi (t : List Char) : Bool :=
  match itarMurakhkhas t with
  | some x => x.1.any fun d => nisbaDawr d == some .isnadiyya
  | none => false

/-- اسمُ مقدّمة الحكم المسنَد: في الإطار المرخَّص، أو إطارٌ بلا نسبةٍ إسنادية (شبهُ جملة، والحكمُ مقدَّر)، أو لا إطار. -/
def isnadIsm (t : List Char) : String :=
  match itarMurakhkhas t with
  | none => "حكمٌ مسنَدٌ في المنطوق: لا إطارَ مرخَّص"
  | some x =>
    if x.1.any (fun d => nisbaDawr d == some .isnadiyya) then "حكمٌ مسنَدٌ في المنطوق"
    else "حكمٌ مسنَدٌ في المنطوق: الإطارُ بلا نسبةٍ إسنادية، والحكمُ مقدَّر (Jisr.Nisab.isnad_markaz)"

/-- **مقدّمةُ الحكم المسنَد** (للدعوى والمفهوم): شرطٌ مشهودٌ إن كان في الإطار المرخَّص دورٌ نسبتُه إسنادية، وإلّا لم يُفحص. -/
def isnadMuq (t : List Char) : Muqaddima :=
  ⟨isnadIsm t, .shart, if isnadFi t then .mashhud else .ghayrMafhus, "Jisr.Nisab.nisbaOf"⟩

theorem isnadMuq_matlub (t : List Char) : (isnadMuq t).halFiil = matlub (isnadMuq t).naw ↔ isnadFi t = true := by
  unfold isnadMuq
  cases isnadFi t <;> simp [Muqaddima.halFiil, matlub]

/-! ## ٥. عقدةُ القوّة: صدرُ الجملة على عمود الأسلوب وصورةِ الفعل، والدعوى بعدها -/

open Jisr.SakkJumla (Quwwa)

/-- أسلوبُ إنشاء: ما ليس «الخبر» في عمود الأسلوب (`Jisr.Awamil.uslub`). -/
def inshaU (u : String) : Bool := u != "الخبر"

/-- **القوّةُ من صفوف كلمة الصدر:** صفوفٌ أساليبُها كلُّها إنشاءٌ فإنشاء؛ و«إِنْ» (صفّ 70 وحده) و«لَمْ» (صفّ 58 وحده) بـ`SakkJumla.awwal` تعليقٌ
    ونفي؛ وما سوى ذلك «لا حكم»: أداةٌ لم يُبنَ أثرُها في القوّة (ليس، لن، لو، إذا، كان…) لا تُرقّى خبرًا مثبتًا. -/
def quwwaSufuf (rs : List Nat) : Quwwa :=
  if !rs.isEmpty && rs.all (fun r => inshaU (uslub r)) then .insha
  else if rs = [70] then Jisr.SakkJumla.awwal ⟨.in_, .laQawl, .laQawl, .amma⟩
  else if rs = [58] then Jisr.SakkJumla.awwal ⟨.lam, .laQawl, .laQawl, .amma⟩
  else .laHukm

/-- صفوفُ كلمة الصدر. -/
def sadr (t : List Char) : List Nat :=
  match kalimatM t with
  | [] => []
  | k :: _ => sufufKalima (khalaya k.w)

/-- **أوزانُ الماضي بلا لاحقة** (تعيين؛ وأوّلُها في `madiSura`): ثلاثُ خلايا آخرُها مفتوحة — فَعَلَ بحركات عينه الثلاث («ضَرَبَ»، «عَلِمَ»،
    «كَرُمَ»)، وفَالَ الأجوفُ بألف مدّ («مَاتَ»)، وفَعَّ المضعَّفُ بمثله («بَتَّ») —، وأربعٌ آخرُها مفتوحة: ثانيتُها ساكنةٌ (أو ألفُ مدّ) وثالثتُها مفتوحة —
    فَعْلَلَ وفَعَّلَ وفَوْعَلَ وفَاعَلَ («دَحْرَجَ»، «كَتَّبَ»، «حَوْقَلَ»، «قَاتَلَ») —، أو ثانيتُها ألفُ مدّ وثالثتُها ساكنةٌ مثلُ الرابعة: فَاعَّ («حَاجَّ»).
    الترخيصُ بنمطٍ موجبٍ لا بغياب مانع، كالمجهول في `Jisr.JisrDal` (`majhul_namat`). وهي أشكالُ خلايا: ما وقعت خلاياه عليها يُقرأ بها، فعلًا كان أو
    غيرَه، وأمثلتُه في رأس الملفّ («حدُّه»). -/
def waznMadi : List Nat → Bool
  | [_, b, c] => c % 4 == 0 && (b % 4 != 3 || b == 11 || (b % 4 == 3 && b / 4 == c / 4))
  | [_, b, c, d] => d % 4 == 0 && ((c % 4 == 0 && b % 4 == 3) || (b == 11 && c % 4 == 3 && c / 4 == d / 4))
  | _ => false

/-- **خليّتان قبل تاءٍ ساكنةٍ أو مكسورة** (تعيين): ثانيتُهما مفتوحة — الناقصُ بتاء التأنيث سقط منه حرفُ العلّة («رَمَتْ»، «دَعَتْ»، «رَأَتْ»،
    «عَسَتْ»)؛ ويقع عليه غيرُه بخلاياه («سَكَتْ» موقوفًا، والتاءُ من أصله). -/
def naqisQablaTa : List Nat → Bool
  | [_, b] => b % 4 == 0
  | _ => false

/-- **صورةُ الماضي:** أوّلُ خليّةٍ مفتوحةٌ (تعيين: مثالُ القطر «ضرب») حاملُها ليس من «نأيت» (القطر L65: المضارعُ «افتتاحه بحرف من نأيت»)، والكلمةُ
    على وزنٍ من `waznMadi` (القطر L55–56: «وبناؤه على الفتح كضرب، إلا مع واو الجماعة فيضم ك"ضربوا"، والضمير المرفوع المتحرك فيسكن ك"ضربت"»)، أو
    عليه أو على `naqisQablaTa` وبعده تاءٌ ساكنةٌ (75) أو مكسورة (74): وهي في الماضي تاءُ التأنيث (القطر L55: «ويعرف بتاء التأنيث الساكنة»)،
    والمكسورةُ في الوصل (الكتاب س17606–17607: «أن يكسروا إذا التقى الساكنان»)، ولا تفرّق الخلايا بينها وبين تاء الأصل («سَكَتْ»). وما يعدّه القطر بعدُ من الماضي (L56–57: «ومنه نعم وبئس وعسى وليس في الأصح») مكسورُ الأوّل («بِئْسَ») «لا حكم»،
    أو صفٌّ في الجدول («عَسَى»، «لَيْسَ»؛ و«عَسَتْ» مصرَّفٌ بلاحقةٍ لا يطابق صفَّه، و«لَيْسَتْ» لا يقع عليها). وما يقع عليها وما لا يقع، بأمثلته، في رأس الملفّ («حدُّه»). وهي لا
    تكفي في الكلمة وحدها (ما قد لا يكون فعلًا بصورتها: «جَعْفَرَ»)، فلا تُقرأ إلّا في دور الفعل (`filMadi`). -/
def madiSura (k : List Nat) : Bool :=
  match k.head?, k.getLast? with
  | some a, some z =>
    a % 4 == 0 && !([0, 14, 11, 18].contains (a / 4)) &&
      (waznMadi k || ((z == 75 || z == 74) && (waznMadi k.dropLast || naqisQablaTa k.dropLast)))
  | _, _ => false

/-- كلمةُ الصدر في دور الفعل من الإطار المرخَّص، بصورة الماضي. -/
def filMadi (t : List Char) : Bool :=
  match kalimatM t, itarMurakhkhas t with
  | k :: _, some x => x.1.head? == some .fil && madiSura (khalaya k.w)
  | _, _ => false

/-- **لا أداةَ في الإطار:** لا كلمةَ فيه لها صفٌّ في جدول العوامل — فلا أداةَ لم يُبنَ أثرُها في القوّة خارج الصدر («مَنْ» مفعولًا،
    و«شَرَعَ» مفعولًا وصفُّها بلا قسم). -/
def khaliMinAdat (t : List Char) : Bool :=
  (adwarKalimat t).all fun p => (sufufKalima (khalaya p.1.w)).isEmpty

/-- **قوّةُ الجملة:** بأداةٍ في الصدر فمن صفوفها (`quwwaSufuf`)؛ وبلا أداةٍ فخبرٌ مثبت (`SakkJumla.awwal` بلا أداة) إن كانت كلمةُ الصدر
    بصورة الماضي في دور الفعل من الإطار المرخَّص (`filMadi`) ولا أداةَ في الإطار (`khaliMinAdat`)، وإلّا «لا حكم». والأمثلةُ في رأس
    الملفّ («حدُّه»). -/
def quwwaJumla (t : List Char) : Quwwa :=
  if kalimatM t = [] then .laHukm
  else if sadr t = [] then
    (if filMadi t && khaliMinAdat t then Jisr.SakkJumla.awwal ⟨.laShay, .laQawl, .laQawl, .amma⟩ else .laHukm)
  else quwwaSufuf (sadr t)

def quwwaIsm : Quwwa → String
  | .ithbat => "خبرٌ مثبت" | .nafy => "خبرٌ منفيّ" | .taliq => "تعليق" | .insha => "إنشاء" | .hikaya => "حكاية"
  | .zann => "ظنّ" | .laThani => "لا ثانية" | .laHukm => "لا حكم"

/-- **شروطُ الخبر:** الخبرُ المثبت لا يكون إلّا بلا أداةٍ في الصدر، وكلمةُ الصدر بصورة الماضي في دور الفعل من الإطار المرخَّص، ولا أداةَ في الإطار؛
    والنفيُ لا يكون إلّا من «لَمْ» (صفّ 58) وحده، والتعليقُ إلّا من «إِنْ» (صفّ 70) وحده. استلزامٌ لا أكثر: ما تُخطئ فيه الشروطُ معلَنٌ في الرأس. -/
theorem la_tarqiya (t : List Char) :
    (quwwaJumla t = .ithbat → sadr t = [] ∧ filMadi t = true ∧ khaliMinAdat t = true) ∧
    (quwwaJumla t = .nafy → sadr t = [58]) ∧ (quwwaJumla t = .taliq → sadr t = [70]) := by
  refine ⟨fun h => ?_, fun h => ?_, fun h => ?_⟩ <;>
  · unfold quwwaJumla quwwaSufuf at h
    repeat' (split at h)
    all_goals simp_all [Jisr.SakkJumla.awwal]

/-- قوّةُ نبت من أسلوب الصفّ (`Nabt.DiscourseEvidence.Force`): «الطلب» بين الأمر والنهي فمحتمِلة. -/
def forceOfUslub (u : String) : Nabt.DiscourseEvidence.Force :=
  if u == "الاستفهام" then .question else if u == "النداء" then .vocative else if u == "التمني" then .wish
  else if u == "الترجي" then .hope else if u == "الخبر" then .assertive else .ambiguous

theorem forceOfUslub_assertive (u : String) (h : forceOfUslub u = .assertive) : u = "الخبر" := by
  unfold forceOfUslub at h
  repeat' (split at h)
  all_goals first | (rename_i hu; exact beq_iff_eq.1 hu) | cases h

/-- **الإنشاءُ لا يُخبر به في نبت:** صفُّ أسلوبٍ إنشائيّ قوّتُه في نبت غيرُ الإخبار، فلا إخبارَ بأيّ شاهد
    (`Nabt.DiscourseEvidence.nonassertive_never_asserts`). -/
theorem insha_nabt (r : Nat) (h : inshaU (uslub r) = true) (w : Nabt.DiscourseEvidence.AssertionWitness) :
    Nabt.DiscourseEvidence.assertionAllowed (forceOfUslub (uslub r)) w = false := by
  apply Nabt.DiscourseEvidence.nonassertive_never_asserts
  intro e
  have := forceOfUslub_assertive _ e
  simp [inshaU, this] at h

/-- القوّةُ من الصفوف إنشاءٌ إذا وفقط إذا كان للصدر صفٌّ وأساليبُ صفوفه كلُّها إنشاء. -/
theorem quwwaSufuf_insha (rs : List Nat) :
    quwwaSufuf rs = .insha ↔ rs ≠ [] ∧ ∀ r ∈ rs, inshaU (uslub r) = true := by
  unfold quwwaSufuf
  by_cases h1 : (!rs.isEmpty && rs.all (fun r => inshaU (uslub r))) = true
  · simp only [h1, ite_true, true_iff]
    simp only [Bool.and_eq_true, Bool.not_eq_true', List.isEmpty_eq_false_iff, List.all_eq_true] at h1
    exact h1
  · simp only [h1, Bool.false_eq_true, ite_false]
    have hn : ¬ (rs ≠ [] ∧ ∀ r ∈ rs, inshaU (uslub r) = true) := by
      rintro ⟨hne, ha⟩
      apply h1
      simp only [Bool.and_eq_true, Bool.not_eq_true', List.isEmpty_eq_false_iff, List.all_eq_true]
      exact ⟨hne, ha⟩
    simp only [hn, iff_false]
    split
    · simp [Jisr.SakkJumla.awwal]
    · split
      · simp [Jisr.SakkJumla.awwal]
      · simp

/-- قوّةُ الجملة إنشاءٌ إذا وفقط إذا كان للصدر صفٌّ وأساليبُ صفوفه كلُّها إنشاء. -/
theorem quwwaJumla_insha (t : List Char) :
    quwwaJumla t = .insha ↔ sadr t ≠ [] ∧ ∀ r ∈ sadr t, inshaU (uslub r) = true := by
  rw [← quwwaSufuf_insha]
  unfold quwwaJumla
  by_cases hk : kalimatM t = []
  · have : sadr t = [] := by simp [sadr, hk]
    simp [hk, this, quwwaSufuf]
  · simp only [hk, ite_false]
    by_cases hs : sadr t = []
    · simp only [hs, ite_true]
      split <;> simp [Jisr.SakkJumla.awwal, quwwaSufuf]
    · simp [hs]

def sanadQuwwa : String := "Jisr.SakkJumla.awwal"

/-- مقدّمةُ القوّة في الدعوى: الخبرُ شرطٌ مشهود، وما ليس خبرًا شرطٌ منفيّ باسم قوّته، و«لا حكم» لم يُفحص. -/
def shartQuwwa (t : List Char) : Muqaddima :=
  let q := quwwaJumla t
  let s := "قوّة الجملة: " ++ quwwaIsm q ++ " (صدرُها: " ++ (if sadr t = [] then "لا أداة" else asmaSufuf (sadr t)) ++
    (if sadr t = [] && !khaliMinAdat t then "؛ وفي الإطار أداة" else "") ++ ")"
  match q with
  | .ithbat | .nafy => ⟨s, .shart, .mashhud, sanadQuwwa⟩
  | .laHukm => ⟨s, .shart, .ghayrMafhus, sanadQuwwa⟩
  | _ => ⟨s, .shart, .manfi, sanadQuwwa⟩

theorem shartQuwwa_matlub (t : List Char) :
    (shartQuwwa t).halFiil = matlub (shartQuwwa t).naw ↔ quwwaJumla t = .ithbat ∨ quwwaJumla t = .nafy := by
  unfold shartQuwwa
  cases quwwaJumla t <;> simp [Muqaddima.halFiil, matlub, sanadQuwwa]

/-- **عقدةُ الدعوى:** مدخلُها الجملةُ بعد المعجم مرفوعةً، وشرطاها الحكمُ المسنَد في الإطار المرخَّص وقوّةُ الخبر؛ ومخرجُها مخرجُ الجملة. -/
def uqdaDawa (t : List Char) : Naqla String String :=
  ⟨masdarJumla t, spanJumla t, String.ofList t, (jumlaM t).makhraj, ⟨"Jisr.SakkJumla.waqiJumla", 1⟩,
    rafa "الجملة" (hukm (jumlaM t)) ++ [isnadMuq t, shartQuwwa t], [],
    "الدعوى ما تُخبر به جملةٌ مرخَّصةٌ لإطارها حكمٌ مسنَدٌ وقوّتُها الخبر؛ وواقعُها بعدها (waqiDawa)"⟩

/-- **لا دعوى إلّا من جملةٍ مرخَّصةٍ مسنَدةٍ قوّتُها الخبر:** بالربط، حكمُ الفاحص على الدعوى ترخيصٌ إذا وفقط إذا رُخِّصت الجملةُ بعد المعجم، وكان في
    إطارها المرخَّص دورٌ نسبتُه إسنادية، وكانت قوّتُها إثباتًا أو نفيًا. -/
theorem dawa_murakhkhas (t : List Char) (hb : (uqdaDawa t).marbut = true) :
    hukm (uqdaDawa t) = .murakhkhas ↔
      hukm (jumlaM t) = .murakhkhas ∧ isnadFi t = true ∧ (quwwaJumla t = .ithbat ∨ quwwaJumla t = .nafy) := by
  rw [murakhkhas_iff]
  have hmq : (uqdaDawa t).muqaddimat = rafa "الجملة" (hukm (jumlaM t)) ++ [isnadMuq t, shartQuwwa t] := rfl
  rw [hmq]
  constructor
  · rintro ⟨-, -, h⟩
    refine ⟨(rafa_matlub _ _).1 fun m hm => h m (List.mem_append_left _ hm), ?_, ?_⟩
    · exact (isnadMuq_matlub t).1 (h _ (by simp))
    · exact (shartQuwwa_matlub t).1 (h _ (by simp))
  · rintro ⟨h1, h2, h3⟩
    refine ⟨hb, ?_, ?_⟩
    · obtain ⟨m, hm⟩ := List.exists_mem_of_ne_nil _ (rafa_ne "الجملة" (hukm (jumlaM t)))
      exact ⟨m, List.mem_append_left _ hm, rafa_naw _ _ m hm⟩
    · intro m hm
      rcases List.mem_append.1 hm with hm | hm
      · exact (rafa_matlub _ _).2 h1 m hm
      · simp only [List.mem_cons, List.mem_nil_iff, or_false] at hm
        rcases hm with rfl | rfl
        · exact (isnadMuq_matlub t).2 h2
        · exact (shartQuwwa_matlub t).2 h3

/-- **واقعُ الدعوى:** يُسأل عنه (`SakkJumla.waqiJumla`) إن رُخِّصت الدعوى، وإلّا «لا حكم». -/
def waqiDawa (t : List Char) (w : Waqi.Hukm) : Waqi.Hukm :=
  if hukm (uqdaDawa t) = .murakhkhas then Jisr.SakkJumla.waqiJumla (quwwaJumla t) w else .laHukm

/-- **لا يُسأل إلّا عن واقع الدعوى المرخَّصة:** معها يمرّر `waqiDawa` حكمَ الواقع، وبغيرها «لا حكم». -/
theorem dawa_waqi (t : List Char) (w : Waqi.Hukm) :
    (hukm (uqdaDawa t) = .murakhkhas → waqiDawa t w = w) ∧
    (hukm (uqdaDawa t) ≠ .murakhkhas → waqiDawa t w = .laHukm) := by
  refine ⟨fun h => ?_, fun h => by simp [waqiDawa, h]⟩
  have hq : quwwaJumla t = .ithbat ∨ quwwaJumla t = .nafy := by
    have := ((murakhkhas_iff _).1 h).2.2 (shartQuwwa t) (by simp [uqdaDawa])
    exact (shartQuwwa_matlub t).1 this
  simp only [waqiDawa, h, ite_true]
  rcases hq with hq | hq <;> rw [hq] <;> rfl

/-- **الإنشاءُ في الصدر لا دعوى له:** قوّتُه إنشاء، فلا ترخيصَ للدعوى، ولا واقعَ يُسأل عنه، ولا إخبارَ في نبت لأيّ صفٍّ من صفوف صدره. -/
theorem insha_la_dawa (t : List Char) (h : quwwaJumla t = .insha) :
    hukm (uqdaDawa t) ≠ .murakhkhas ∧ (∀ w, waqiDawa t w = .laHukm) ∧
    ∀ r ∈ sadr t, ∀ w, Nabt.DiscourseEvidence.assertionAllowed (forceOfUslub (uslub r)) w = false := by
  have hd : hukm (uqdaDawa t) ≠ .murakhkhas := fun hd => by
    have := ((murakhkhas_iff _).1 hd).2.2 (shartQuwwa t) (by simp [uqdaDawa])
    rcases (shartQuwwa_matlub t).1 this with e | e <;> rw [h] at e <;> cases e
  exact ⟨hd, fun w => (dawa_waqi t w).2 hd, fun r hr w => insha_nabt r (((quwwaJumla_insha t).1 h).2 r hr) w⟩

/-! ## ٦. عقدةُ المفهوم: القيدُ من الكلمات بأدوارها في الإطار المرخَّص -/

open Jisr.MantuqMafhum (Qayd sinfOf Mudaa Mafhum NawMafhum jisr jisrMn mukhalafaOf mahmul mawani shartSinf muwafiqTabi)
open Jisr.QaydMafhum (Unsur unsurQayd adatQayd bilBunya mashud innamaFi innamaU)

def alOf : Except String Dal.QiraaTahsil.Qiraa → Bool
  | .ok q => q.al
  | .error _ => false

/-- **الصفُّ عاملًا في دوره:** من أقسامه قسمُ الدور (`qism`، `dawrQism`)، ولا يعمل شرطًا — لا إطارَ شرطٍ وجوابٍ في المجال (بتعريف `Jisr.NassItar.itarat`)،
    فصفُّ أداة الشرط في إطارٍ مرخَّصٍ لا يعمل فيه شرطًا —، ولا غايةً إلّا في دور حرف الجرّ. -/
def saffFiDawr (r : Nat) (d : Dawr) : Bool :=
  saffQism r d && adatQayd r != some .shart && (adatQayd r != some .ghaya || d == .harfJarr)

/-- **بنيةُ الكلمة في دورها** (`QaydMafhum.Unsur`): صفوفُها العاملةُ في الدور، وذو الأداة (الخامسةُ في `Wad.maarif`، القطر L144) إن كانت بأل
    في دورٍ قسمُه الاسم. ولا عنصرَ للمنوَّن: العلمُ والنكرةُ لا يفترقان في الخلايا. -/
def unsurDawr (kw : KalimaM) (d : Dawr) : List Unsur :=
  let q := Dal.QiraaTahsil.qiraa kw.w false
  ((sufufKalima (khalayaQari q)).filter (saffFiDawr · d)).map .adat ++
    (if alOf q && dawrQism d == .ism then [.marifa 4] else [])

/-- «إِنَّمَا» في صدر الجملة (القطر L189–190؛ ج3 س584 بترقيم التحويل `scripts/tahwil_docx.py`). -/
def innamaJumla (t : List Char) : Bool :=
  match kalimatM t with
  | k :: _ => innamaK (khalaya k.w)
  | [] => false

/-- **بنيةُ الجملة:** «إنما» في صدرها، ثمّ عناصرُ كلماتها بأدوارها في الإطار المرخَّص — محسوبةٌ من النصّ والإطار، لا مكتوبةٌ باليد. -/
def bunya (t : List Char) : List Unsur :=
  (if innamaJumla t then [.maHarfiyya 0] else []) ++ (adwarKalimat t).flatMap fun p => unsurDawr p.1 p.2

/-- القيودُ بكلماتها. -/
def qaydKalimat (t : List Char) : List (Qayd × KalimaM) :=
  (adwarKalimat t).flatMap fun p => (unsurDawr p.1 p.2).filterMap fun u => (unsurQayd u).map (·, p.1)

/-- **اختيارُ القيد:** أوّلُ قيدٍ له صنفُ مخالفة، وإلّا أوّلُ قيد. -/
def qaydMin {α : Type} (l : List (Qayd × α)) : Option (Qayd × α) :=
  match l.find? (fun p => (sinfOf p.1).isSome) with
  | some p => some p
  | none => l.head?

/-- **قيدُ الجملة** من قيودها بكلماتها (`qaydMin`). -/
def qaydJumla (t : List Char) : Option (Qayd × KalimaM) := qaydMin (qaydKalimat t)

/-- اختيارُ القيد: من الاسم ثمّ الغاية تُختار الغاية، ومن اسمين يُختار الأوّل. -/
theorem qaydMin_shahid :
    qaydMin [(Qayd.ism, 1), (.ghaya, 2)] = some (.ghaya, 2) ∧ qaydMin [(Qayd.ism, 1), (.ism, 2)] = some (.ism, 1) := by
  decide

theorem adatQayd_anwa (i : Nat) (q : Qayd) (h : adatQayd i = some q) : q = .shart ∨ q = .ghaya := by
  unfold adatQayd at h
  split at h
  · cases h
  · split at h
    · cases h; exact Or.inl rfl
    · split at h
      · cases h; exact Or.inr rfl
      · cases h

/-- **القيدُ بالدور:** الغايةُ لا تكون إلّا من صفٍّ في دور حرف الجرّ، والاسمُ إلّا من ذي أداةٍ في دورٍ قسمُه الاسم؛ ولا شرطَ. -/
theorem unsurDawr_qayd (kw : KalimaM) (d : Dawr) (u : Unsur) (hu : u ∈ unsurDawr kw d) (q : Qayd)
    (h : unsurQayd u = some q) :
    (q = .ghaya ∧ d = .harfJarr ∧ ∃ r, u = .adat r) ∨ (q = .ism ∧ dawrQism d = .ism ∧ u = .marifa 4) := by
  simp only [unsurDawr, List.mem_append, List.mem_map, List.mem_filter] at hu
  rcases hu with ⟨r, ⟨-, hs⟩, rfl⟩ | hu
  · have hq : adatQayd r = some q := h
    simp only [saffFiDawr, Bool.and_eq_true, bne_iff_ne, ne_eq, Bool.or_eq_true, beq_iff_eq] at hs
    obtain ⟨⟨-, hsh⟩, hgh⟩ := hs
    rcases adatQayd_anwa r q hq with rfl | rfl
    · exact absurd hq hsh
    · exact Or.inl ⟨rfl, hgh.resolve_left (fun e => e hq), r, rfl⟩
  · split at hu
    · rename_i hc
      rw [List.mem_singleton] at hu; subst hu
      have : unsurQayd (.marifa 4) = some .ism := by decide
      rw [this] at h; cases h
      simp only [Bool.and_eq_true, beq_iff_eq] at hc
      exact Or.inr ⟨rfl, hc.2, rfl⟩
    · cases hu

theorem unsurQayd_innama : unsurQayd (.maHarfiyya 0) = none ∧ innamaU (.maHarfiyya 0) = true := by decide

/-- **لا قيدَ شرطٍ في المجال:** لا عنصرَ في بنية الجملة قيدُه الشرط. -/
theorem la_shart_fi_majal (t : List Char) (u : Unsur) (hu : u ∈ bunya t) : unsurQayd u ≠ some .shart := by
  intro h
  simp only [bunya, List.mem_append, List.mem_flatMap] at hu
  rcases hu with hu | ⟨p, -, hu⟩
  · split at hu
    · rw [List.mem_singleton] at hu; subst hu; rw [unsurQayd_innama.1] at h; cases h
    · cases hu
  · rcases unsurDawr_qayd p.1 p.2 u hu .shart h with ⟨e, -, -⟩ | ⟨e, -, -⟩ <;> cases e

/-- «إنما» في البنية إذا وفقط إذا كانت في صدر الجملة. -/
theorem innamaFi_bunya (t : List Char) : innamaFi (bunya t) = innamaJumla t := by
  have hd : ∀ p : KalimaM × Dawr, ∀ u ∈ unsurDawr p.1 p.2, innamaU u = false := by
    intro p u hu
    simp only [unsurDawr, List.mem_append, List.mem_map, List.mem_filter] at hu
    rcases hu with ⟨r, -, rfl⟩ | hu
    · rfl
    · split at hu
      · rw [List.mem_singleton] at hu; subst hu; decide
      · cases hu
  have h2 : ((adwarKalimat t).flatMap fun p => unsurDawr p.1 p.2).any innamaU = false := by
    rw [List.any_eq_false]
    intro u hu
    obtain ⟨p, -, hp⟩ := List.mem_flatMap.1 hu
    simp [hd p u hp]
  unfold innamaFi bunya
  rw [List.any_append, h2, Bool.or_false]
  cases innamaJumla t <;> simp [unsurQayd_innama.2]

theorem qaydJumla_mem (t : List Char) {p : Qayd × KalimaM} (h : qaydJumla t = some p) : p ∈ qaydKalimat t := by
  unfold qaydJumla qaydMin at h
  split at h
  · rename_i p' hp; cases h; exact List.mem_of_find?_eq_some hp
  · exact List.mem_of_mem_head? h

/-- **قيدُ الجملة تحمله كلمةٌ في دورها من الإطار المرخَّص** بعنصرٍ من بنيتها. -/
theorem qaydJumla_dawr (t : List Char) {p : Qayd × KalimaM} (h : qaydJumla t = some p) :
    ∃ d, (p.2, d) ∈ adwarKalimat t ∧ ∃ u ∈ unsurDawr p.2 d, unsurQayd u = some p.1 := by
  obtain ⟨kd, hkd, hp⟩ := List.mem_flatMap.1 (qaydJumla_mem t h)
  obtain ⟨u, hu, he⟩ := List.mem_filterMap.1 hp
  cases hq : unsurQayd u with
  | none => simp [hq] at he
  | some q =>
    simp only [hq, Option.map_some, Option.some.injEq] at he
    subst he
    exact ⟨kd.2, hkd, u, hu, hq⟩

theorem mashud_qaydJumla (t : List Char) {p : Qayd × KalimaM} (h : qaydJumla t = some p) :
    mashud (bunya t) p.1 = true := by
  obtain ⟨d, hk, u, hu, hq⟩ := qaydJumla_dawr t h
  exact List.any_eq_true.2 ⟨u, List.mem_append_right _ (List.mem_flatMap.2 ⟨(p.2, d), hk, hu⟩), by simp [hq]⟩

theorem qaydJumla_anwa (t : List Char) {p : Qayd × KalimaM} (h : qaydJumla t = some p) :
    p.1 = .ghaya ∨ p.1 = .ism := by
  obtain ⟨d, -, u, hu, hq⟩ := qaydJumla_dawr t h
  rcases unsurDawr_qayd p.2 d u hu p.1 hq with ⟨e, -, -⟩ | ⟨e, -, -⟩
  · exact Or.inl e
  · exact Or.inr e

/-- **قيدُ المخالفة في المجال غايةٌ من حرف جرّ:** قيدُ الجملة الذي له صنفُ مخالفةٍ هو الغاية، وكلمتُه في دور حرف الجرّ من الإطار المرخَّص. -/
theorem qaydJumla_sinf (t : List Char) {p : Qayd × KalimaM} (h : qaydJumla t = some p) (hs : (sinfOf p.1).isSome = true) :
    p.1 = .ghaya ∧ (p.2, Dawr.harfJarr) ∈ adwarKalimat t := by
  obtain ⟨d, hk, u, hu, hq⟩ := qaydJumla_dawr t h
  rcases unsurDawr_qayd p.2 d u hu p.1 hq with ⟨e, hd, -⟩ | ⟨e, -, -⟩
  · subst hd; exact ⟨e, hk⟩
  · rw [e] at hs; cases hs

/-- ما يُودَع للمفهوم ولا يُقرأ من النصّ: حملُ الكلمات (`QawaninDalala.haml`)، والمانعان الأغلبُ والنصُّ المعطِّل؛ و`none` لم يُودَع. -/
structure Wada where
  haml : Option (List QawaninDalala.Mahmul)
  aghlab : Option Bool
  muattil : Option Bool

/-- المحرّكُ بلا ودائع. -/
def wadaKhali : Wada := ⟨none, none, none⟩

/-- لازمُ المخالفة: نفيُ الحكم عند انتفاء القيد الذي تحمله الكلمة. -/
structure Naqd where
  qayd : Qayd
  kalima : Nat
  deriving DecidableEq, Repr

/-- **المودَعُ لـ`MantuqMafhum` من الجملة:** القيدُ ولازمُه من بنيتها، وما يُودَع من `W` (وما لم يُودَع يُقرأ غائبًا هنا، وتسمّيه عقدةُ
    المفهوم «لم يُفحص»). والصفةُ والعددُ لا يُحسبان قيدًا (`unsurDawr_qayd`)، فلا إفهامَ ولا سياقَ عدد. -/
def mudaa (t : List Char) (W : Wada) : Mudaa Unit Naqd where
  kalimat := fun _ => W.haml.getD []
  qayd := fun _ => (qaydJumla t).map (·.1)
  mufhim := fun _ => false
  siyaqAdad := fun _ => false
  innama := fun _ => false
  aghlab := fun _ => W.aghlab.getD false
  muattil := fun _ => W.muattil.getD false
  naqid := fun _ => (qaydJumla t).map fun p => ⟨p.1, p.2.i⟩
  muwafiq := fun _ => []
  iqtida := fun _ => []
  tanbih := fun _ => []
  ishara := fun _ => []

/-- **المفهوم:** جسرُ `MantuqMafhum` على المودَع بعد ربطه ببنية الجملة (`QaydMafhum.bilBunya`). -/
def mafahim (t : List Char) (W : Wada) : List (Mafhum Unit Naqd) :=
  jisr (bilBunya (mudaa t W) (fun _ => bunya t)) [()]

/-- **كلُّ مفهومِ مخالفةٍ تحمله كلمةٌ في دورها من الإطار المرخَّص:** قيدُه يشهد له عنصرٌ من بنية تلك الكلمة في ذلك الدور
    (`QaydMafhum.mukhalafa_mashuda`). -/
theorem mafhum_kalima (t : List Char) (W : Wada) {f : Mafhum Unit Naqd} {k : SLGE.Madlul.Mukhalafa}
    (h : f ∈ mafahim t W) (hk : f.naw = .mukhalafa k) :
    ∃ p ∈ adwarKalimat t, ∃ u ∈ unsurDawr p.1 p.2, ∃ q, unsurQayd u = some q ∧ sinfOf q = some k := by
  obtain ⟨q, u, _, hs, hu, hq⟩ := Jisr.QaydMafhum.mukhalafa_mashuda (mudaa t W) (fun _ => bunya t) h hk
  simp only [bunya, List.mem_append, List.mem_flatMap] at hu
  rcases hu with hu | ⟨p, hp, hu⟩
  · split at hu
    · rw [List.mem_singleton] at hu; subst hu; rw [unsurQayd_innama.1] at hq; cases hq
    · cases hu
  · exact ⟨p, hp, u, hu, q, hq, hs⟩

private theorem ite_mawani {β : Type} (a b c : Bool) (x y : β) :
    (if (a = false ∧ b = false) ∧ c = false then x else y) = if (a = true ∨ b = true) ∨ c = true then y else x := by
  cases a <;> cases b <;> cases c <;> simp

/-- **صورةُ المفهوم مغلقة:** حملٌ لا «لا حكم» فيه، وقيدٌ له صنف، ولا مانعَ — فمفهومٌ واحد؛ وإلّا فلا شيء. -/
theorem mafahim_eq (t : List Char) (W : Wada) :
    mafahim t W =
      if (W.haml.getD []).all (· != .laHukm) then
        match qaydJumla t with
        | some p =>
          match sinfOf p.1 with
          | some k =>
            if innamaFi (bunya t) || W.aghlab.getD false || W.muattil.getD false then []
            else [⟨.mukhalafa k, (), ⟨p.1, p.2.i⟩⟩]
          | none => []
        | none => []
      else [] := by
  cases hq : qaydJumla t with
  | none =>
    simp [mafahim, jisr, jisrMn, mukhalafaOf, muwafiqTabi, mudaa, bilBunya, hq]
  | some p =>
    have hm := mashud_qaydJumla t hq
    rcases qaydJumla_anwa t hq with ha | ha <;>
    · simp only [ha] at hm
      simp [mafahim, jisr, jisrMn, mukhalafaOf, muwafiqTabi, mudaa, bilBunya, hq, ha, Option.filter_some, hm, sinfOf,
        shartSinf, mawani, mahmul, ite_mawani]

def qaydIsm : Qayd → String
  | .sifa => "الصفة" | .shart => "الشرط" | .ghaya => "الغاية" | .adad => "العدد" | .ism => "الاسم"

/-- حالُ مانعٍ مودَع: غائبٌ منفيّ، وحاضرٌ مشهود، وما لم يُودَع لم يُفحص. -/
def halB : Option Bool → Hal
  | none => .ghayrMafhus
  | some true => .mashhud
  | some false => .manfi

/-- حالُ الحمل المودَع: لا «لا حكم» في كلماته فمشهود، وإلّا منفيّ؛ وما لم يُودَع لم يُفحص. -/
def hamlHal : Option (List QawaninDalala.Mahmul) → Hal
  | none => .ghayrMafhus
  | some l => if l.all (· != .laHukm) then .mashhud else .manfi

def sanadUnsur : String := "Jisr.QaydMafhum.unsurQayd"

/-- مقدّمتا القيد: قيدٌ مشهودٌ بكلمته، وصنفُه في المخالفة — والاسمُ لا صنفَ له (`MantuqMafhum.sinfOf`؛ وج3 س582 بترقيم التحويل:
    «فلا يعمل بمفهوم الاسم مطلقاً»)؛ ولا قيدَ فشرطٌ منفيّ. -/
def qaydMuq (t : List Char) : List Muqaddima :=
  match qaydJumla t with
  | none => [⟨"قيدٌ في بنية الجملة (Jisr.QaydMafhum.mashud)", .shart, .manfi, sanadUnsur⟩]
  | some p =>
    [⟨"قيد " ++ qaydIsm p.1 ++ " من " ++ ismKalima p.2, .shart, .mashhud, sanadUnsur⟩,
     match sinfOf p.1 with
     | some _ => ⟨"صنفُ المخالفة: " ++ qaydIsm p.1 ++ " (ج3 س566)", .shart, .mashhud, "Jisr.MantuqMafhum.sinfOf"⟩
     | none => ⟨"الاسمُ لا صنفَ له في المخالفة (ج3 س582)", .shart, .manfi, "Jisr.MantuqMafhum.sinfOf"⟩]

/-- **مقدّماتُ المفهوم بعد الجملة:** القيدُ وصنفُه، والحكمُ المسنَد (`isnadMuq`)، والحملُ، والموانعُ الثلاثة (ج3 س584–586) بأحوالها. -/
def muqMafhum (t : List Char) (W : Wada) : List Muqaddima :=
  qaydMuq t ++
  [isnadMuq t,
   ⟨"حملُ كلمات المنطوق (QawaninDalala.haml؛ ج3 س548)", .shart, hamlHal W.haml, "QawaninDalala.haml"⟩,
   ⟨"«إنما» في البنية (ج3 س584)", .mani, if innamaFi (bunya t) then .mashhud else .manfi, "Jisr.QaydMafhum.innamaFi"⟩,
   ⟨"خروجُ المنطوق مخرجَ الأعمّ الأغلب (ج3 س585)", .mani, halB W.aghlab, "Jisr.MantuqMafhum.mawani"⟩,
   ⟨"نصٌّ يعطّل المفهوم (ج3 س586)", .mani, halB W.muattil, "Jisr.MantuqMafhum.mawani"⟩]

/-- مخرجُ عقدة المفهوم: لازمُ المخالفة لقيدٍ له صنف، وإلّا فلا مخرج. -/
def mafhumIsm (t : List Char) : String :=
  match qaydJumla t with
  | some p => if (sinfOf p.1).isSome then "نفيُ الحكم عند انتفاء " ++ qaydIsm p.1 ++ " (" ++ ismKalima p.2 ++ ")" else ""
  | none => ""

/-- **عقدةُ المفهوم:** مدخلُها الجملةُ بعد المعجم مرفوعةً، ثمّ مقدّماتُ المفهوم؛ ومخرجُها لازمُ المخالفة. -/
def uqdaMafhum (t : List Char) (W : Wada) : Naqla String String :=
  ⟨masdarJumla t, spanJumla t, String.ofList t, mafhumIsm t, ⟨"Jisr.MantuqMafhum.jisr", 1⟩,
    rafa "الجملة" (hukm (jumlaM t)) ++ muqMafhum t W, [],
    "مفهومُ المخالفة من قيدٍ تحمله كلمةٌ في دورها من الإطار المرخَّص (Jisr.QaydMafhum.bilBunya)؛ والودائعُ التي لم تُودَع لم تُفحص"⟩

/-- **بلا ودائع لا يرخَّص مفهوم:** المانعُ الذي لم يُودَع لم يُفحص، فعقدةُ المفهوم معلَّقةٌ أو أشدّ — والمحرّكُ يسمّي ما ينقصه. -/
theorem mafhum_bila_wada (t : List Char) : hukm (uqdaMafhum t wadaKhali) ≠ .murakhkhas := by
  apply ghayrMafhus_la_yurakhkhis _ ⟨"نصٌّ يعطّل المفهوم (ج3 س586)", .mani, halB none, "Jisr.MantuqMafhum.mawani"⟩
  · simp [uqdaMafhum, muqMafhum, wadaKhali]
  · simp [Muqaddima.halFiil, halB]

theorem qaydMuq_matlub (t : List Char) :
    (∀ x ∈ qaydMuq t, x.halFiil = matlub x.naw) ↔ ∃ p, qaydJumla t = some p ∧ (sinfOf p.1).isSome := by
  unfold qaydMuq
  cases hq : qaydJumla t with
  | none => simp [Muqaddima.halFiil, matlub, sanadUnsur]
  | some p =>
    cases hs : sinfOf p.1 <;> simp [Muqaddima.halFiil, matlub, sanadUnsur, hs]

theorem muqMafhum_matlub (t : List Char) (W : Wada) :
    (∀ x ∈ muqMafhum t W, x.halFiil = matlub x.naw) ↔
      (∃ p, qaydJumla t = some p ∧ (sinfOf p.1).isSome) ∧ isnadFi t = true ∧ hamlHal W.haml = .mashhud ∧
        innamaFi (bunya t) = false ∧ halB W.aghlab = .manfi ∧ halB W.muattil = .manfi := by
  unfold muqMafhum
  rw [← qaydMuq_matlub, ← isnadMuq_matlub]
  simp only [List.mem_append, List.mem_cons, List.mem_nil_iff, or_false]
  constructor
  · intro h
    refine ⟨fun x hx => h x (Or.inl hx), h _ (Or.inr (Or.inl rfl)), ?_, ?_, ?_, ?_⟩
    · have := h _ (Or.inr (Or.inr (Or.inl rfl))); simpa [Muqaddima.halFiil, matlub] using this
    · have := h _ (Or.inr (Or.inr (Or.inr (Or.inl rfl)))); cases hi : innamaFi (bunya t) <;> simp_all [Muqaddima.halFiil, matlub]
    · have := h _ (Or.inr (Or.inr (Or.inr (Or.inr (Or.inl rfl))))); simpa [Muqaddima.halFiil, matlub] using this
    · have := h _ (Or.inr (Or.inr (Or.inr (Or.inr (Or.inr rfl))))); simpa [Muqaddima.halFiil, matlub] using this
  · rintro ⟨hq, hi, hh, hn, ha, hm⟩ x (hx | hx | hx | hx | hx | hx)
    · exact hq x hx
    · subst hx; exact hi
    · subst hx; simp [Muqaddima.halFiil, matlub, hh]
    · subst hx; simp [Muqaddima.halFiil, matlub, hn]
    · subst hx; simp [Muqaddima.halFiil, matlub, ha]
    · subst hx; simp [Muqaddima.halFiil, matlub, hm]

theorem mafahim_mukhalafa (t : List Char) (W : Wada) :
    (∃ f ∈ mafahim t W, ∃ k, f.naw = .mukhalafa k) ↔
      (W.haml.getD []).all (· != .laHukm) = true ∧ (∃ p, qaydJumla t = some p ∧ (sinfOf p.1).isSome) ∧
        (innamaFi (bunya t) || W.aghlab.getD false || W.muattil.getD false) = false := by
  rw [mafahim_eq]
  by_cases hh : (W.haml.getD []).all (· != .laHukm) = true
  · simp only [hh, ite_true, true_and]
    cases hq : qaydJumla t with
    | none => simp
    | some p =>
      cases hs : sinfOf p.1 with
      | none => simp [hs]
      | some k =>
        by_cases hm : (innamaFi (bunya t) || W.aghlab.getD false || W.muattil.getD false) = true
        · simp [hs, hm]
        · simp only [Bool.not_eq_true] at hm
          simp [hs, hm]
  · simp [hh]

/-- **عقدةُ المفهوم وجسرُ `MantuqMafhum`:** لكلّ جملةٍ وودائع، إذا كان الانتقالُ مربوطًا وأُودعت الودائعُ الثلاث (الحمل، والأغلب، والمعطِّل، أيًّا
    كانت قيمُها)، رخّص الفاحصُ المفهومَ إذا وفقط إذا رُخِّصت الجملةُ بعد المعجم، وكان في إطارها المرخَّص دورٌ نسبتُه إسنادية، وأخرج
    `MantuqMafhum.jisr` على المودَع المربوط ببنية الجملة (`QaydMafhum.bilBunya`) مفهومَ مخالفة. -/
theorem mafhum_jisr (t : List Char) (W : Wada) (hb : (uqdaMafhum t W).marbut = true)
    (hh : W.haml.isSome = true) (ha : W.aghlab.isSome = true) (hm : W.muattil.isSome = true) :
    hukm (uqdaMafhum t W) = .murakhkhas ↔
      hukm (jumlaM t) = .murakhkhas ∧ isnadFi t = true ∧ ∃ f ∈ mafahim t W, ∃ k, f.naw = .mukhalafa k := by
  rw [murakhkhas_iff, mafahim_mukhalafa]
  have hmq : (uqdaMafhum t W).muqaddimat = rafa "الجملة" (hukm (jumlaM t)) ++ muqMafhum t W := rfl
  have hall : (∀ x ∈ (uqdaMafhum t W).muqaddimat, x.halFiil = matlub x.naw) ↔
      hukm (jumlaM t) = .murakhkhas ∧ ∀ x ∈ muqMafhum t W, x.halFiil = matlub x.naw := by
    rw [hmq, ← rafa_matlub "الجملة"]
    simp only [List.mem_append]
    exact ⟨fun h => ⟨fun x hx => h x (Or.inl hx), fun x hx => h x (Or.inr hx)⟩,
      fun ⟨h1, h2⟩ x hx => hx.elim (h1 x) (h2 x)⟩
  have hex : ∃ m ∈ (uqdaMafhum t W).muqaddimat, m.naw = .madkhal := by
    obtain ⟨m, hm'⟩ := List.exists_mem_of_ne_nil _ (rafa_ne "الجملة" (hukm (jumlaM t)))
    exact ⟨m, by rw [hmq]; exact List.mem_append_left _ hm', rafa_naw _ _ m hm'⟩
  rw [hall, muqMafhum_matlub]
  obtain ⟨wh, wa, wm⟩ := W
  cases wh with
  | none => simp at hh
  | some l =>
    cases wa with
    | none => simp at ha
    | some a =>
      cases wm with
      | none => simp at hm
      | some m =>
        have e1 : hamlHal (some l) = .mashhud ↔ l.all (· != .laHukm) = true := by
          simp only [hamlHal]; cases l.all (· != .laHukm) <;> simp
        have e2 : ∀ b : Bool, halB (some b) = .manfi ↔ b = false := by intro b; cases b <;> simp [halB]
        simp only [e1, e2, Option.getD_some, Bool.or_eq_false_iff]
        constructor
        · rintro ⟨-, -, hj, hq, hi, hl, hn, ha', hm'⟩
          exact ⟨hj, hi, hl, hq, ⟨hn, ha'⟩, hm'⟩
        · rintro ⟨hj, hi, hl, hq, ⟨hn, ha'⟩, hm'⟩
          exact ⟨hb, hex, hj, hq, hi, hl, hn, ha', hm'⟩

/-- **لا مفهومَ مخالفةٍ مرخَّصًا في المجال:** قيدُ المخالفة غايةٌ في دور حرف الجرّ (`qaydJumla_sinf`)، وإطارُ حرف الجرّ لا دورَ فيه نسبتُه إسنادية
    (`harfJarr_la_isnad`)، والمفهومُ يشترط الحكمَ المسنَد؛ فعقدةُ المفهوم لا تُرخَّص لأيّ جملةٍ وأيّ ودائع. -/
theorem la_mafhum_fi_majal (t : List Char) (W : Wada) : hukm (uqdaMafhum t W) ≠ .murakhkhas := by
  intro h
  have hall := ((murakhkhas_iff _).1 h).2.2
  have hm : ∀ x ∈ muqMafhum t W, x.halFiil = matlub x.naw := fun x hx => hall x (List.mem_append_right _ hx)
  obtain ⟨⟨p, hp, hs⟩, hi, -⟩ := (muqMafhum_matlub t W).1 hm
  obtain ⟨-, hj⟩ := qaydJumla_sinf t hp hs
  unfold isnadFi at hi
  unfold adwarKalimat at hj
  cases hx : itarMurakhkhas t with
  | none => rw [hx] at hi; cases hi
  | some x =>
    rw [hx] at hi hj
    obtain ⟨hmem, -⟩ := itarMurakhkhas_spec t hx
    have hd : Dawr.harfJarr ∈ x.1 := (List.of_mem_zip hj).2
    have hu : x ∈ Jisr.NassItar.itarat (kalimatDal t) := by
      unfold utur at hmem
      split at hmem
      · exact hmem
      · cases hmem
    simp only at hi
    rw [harfJarr_la_isnad _ x hu hd] at hi
    cases hi

/-! ## ٧. أثرُ كلّ عقدةٍ على الشاهد -/

def muallaqB : Natija → Bool
  | .muallaq _ => true
  | _ => false

def laTantabiqB : Natija → Bool
  | .laTantabiq _ => true
  | _ => false

def madkhalFasidB : Natija → Bool
  | .madkhalFasid _ => true
  | _ => false

/-- **«إِلَى الدَّارِ» و«إِلَى الدَّارُ»:** مقاطعُ «الدَّارِ» و«الدَّارُ» واحدةٌ إلّا آخرَها («رِ»، «رُ»)؛ و«إِلَى الدَّارِ» مرخَّصةٌ منطوقُها من كلمتين
    وعقدةُ مفهومها بلا ودائع (`wadaKhali`) معلَّقة، و«إِلَى الدَّارُ» ممتنعةٌ لا منطوقَ لها وعقدةُ مفهومها بلا ودائع مدخلٌ فاسد. -/
theorem athar_maqta :
    (Dal.Tahsil.tahsil "الدَّارِ".toList).map (·.nass) = ["ا".toList, "ل".toList, "دَّ".toList, "ا".toList, "رِ".toList] ∧
    (Dal.Tahsil.tahsil "الدَّارُ".toList).map (·.nass) = ["ا".toList, "ل".toList, "دَّ".toList, "ا".toList, "رُ".toList] ∧
    hukm (jumlaM "إِلَى الدَّارِ".toList) = .murakhkhas ∧ mumtaniB (hukm (jumlaM "إِلَى الدَّارُ".toList)) = true ∧
    (mantuq "إِلَى الدَّارِ".toList).length = 2 ∧ mantuq "إِلَى الدَّارُ".toList = [] ∧
    muallaqB (hukm (uqdaMafhum "إِلَى الدَّارِ".toList wadaKhali)) = true ∧
    madkhalFasidB (hukm (uqdaMafhum "إِلَى الدَّارُ".toList wadaKhali)) = true := by
  decide +kernel

/-- **«إِلَى الدَّارِ» و«فِي الدَّارِ»:** «فِي الدَّارِ» مرخَّصة؛ وقيدُ «إِلَى الدَّارِ» الغايةُ من كلمتها الأولى، ولها بلا ودائع (`wadaKhali`) مفهومٌ
    واحد وعقدةُ مفهومها معلَّقة؛ وقيدُ «فِي الدَّارِ» الاسمُ من كلمتها الثانية، ولا مفهومَ لها بلا ودائع وعقدةُ مفهومها «لا تنطبق». -/
theorem athar_adat :
    hukm (jumlaM "فِي الدَّارِ".toList) = .murakhkhas ∧
    ((qaydJumla "إِلَى الدَّارِ".toList).map fun p => (p.1, p.2.i)) = some (.ghaya, 0) ∧
    ((qaydJumla "فِي الدَّارِ".toList).map fun p => (p.1, p.2.i)) = some (.ism, 1) ∧
    (mafahim "إِلَى الدَّارِ".toList wadaKhali).length = 1 ∧ mafahim "فِي الدَّارِ".toList wadaKhali = [] ∧
    muallaqB (hukm (uqdaMafhum "إِلَى الدَّارِ".toList wadaKhali)) = true ∧
    laTantabiqB (hukm (uqdaMafhum "فِي الدَّارِ".toList wadaKhali)) = true := by
  decide +kernel

/-- **من صفوف «مَنْ»، وقيدُ «ضَرَبَ الْوَلَدُ مَنْ»، و«ذَهَبَ الْوَلَدُ إِلَى الدَّارِ»:** من صفوف «مَنْ» الصفُّ 71، وقيدُ «ضَرَبَ الْوَلَدُ مَنْ» الاسمُ من كلمتها
    الثانية «الْوَلَدُ»؛ و«ذَهَبَ الْوَلَدُ إِلَى الدَّارِ» لا إطارَ مرخَّصَ لها ولا قيد، ولا مفهومَ لها بلا ودائع (`wadaKhali`). -/
theorem athar_dawr :
    71 ∈ sufuf (khalaya "مَنْ".toList) ∧
    ((qaydJumla "ضَرَبَ الْوَلَدُ مَنْ".toList).map fun p => (p.1, p.2.i)) = some (.ism, 1) ∧
    (itarMurakhkhas "ذَهَبَ الْوَلَدُ إِلَى الدَّارِ".toList).isNone = true ∧
    (qaydJumla "ذَهَبَ الْوَلَدُ إِلَى الدَّارِ".toList).isNone = true ∧ mafahim "ذَهَبَ الْوَلَدُ إِلَى الدَّارِ".toList wadaKhali = [] := by
  decide +kernel

/-- **أحكامُ جملٍ قبل المعجم وبعده:** «إِنَّ زَيْدًا جَاءَ» و«هَلْ ذَهَبَ الْوَلَدُ» و«لَمْ ذَهَبَ» ممتنعةٌ قبل المعجم ومعلَّقةٌ بعده؛
    و«حَتَّى الْوَلَدُ» مرخَّصةٌ قبله ومعلَّقةٌ بعده؛ و«ذَهَبَ الْوَلَدُ» و«كَانَ الْوَلَدُ» مرخَّصتان بعده. -/
theorem athar_qism :
    mumtaniB (hukm (jumla "إِنَّ زَيْدًا جَاءَ".toList)) = true ∧ muallaqB (hukm (jumlaM "إِنَّ زَيْدًا جَاءَ".toList)) = true ∧
    mumtaniB (hukm (jumla "هَلْ ذَهَبَ الْوَلَدُ".toList)) = true ∧ muallaqB (hukm (jumlaM "هَلْ ذَهَبَ الْوَلَدُ".toList)) = true ∧
    mumtaniB (hukm (jumla "لَمْ ذَهَبَ".toList)) = true ∧ muallaqB (hukm (jumlaM "لَمْ ذَهَبَ".toList)) = true ∧
    hukm (jumla "حَتَّى الْوَلَدُ".toList) = .murakhkhas ∧ muallaqB (hukm (jumlaM "حَتَّى الْوَلَدُ".toList)) = true ∧
    hukm (jumlaM "ذَهَبَ الْوَلَدُ".toList) = .murakhkhas ∧ hukm (jumlaM "كَانَ الْوَلَدُ".toList) = .murakhkhas := by
  decide +kernel

/-- **نسبُ المنطوق:** نسبُ أدوار «ضَرَبَ الْوَلَدُ الرَّجُلَ» إسناديّةٌ فإسناديّةٌ فتقييديّة، و«ذَهَبَ أَبُو الْوَلَدِ» إسناديّةٌ
    فإسناديّةٌ فإضافيّة، و«فِي الدَّارِ» لا نسبةَ لدورها الأوّل ونسبةُ الثاني إضافيّة. -/
theorem athar_itar :
    (mantuq "ضَرَبَ الْوَلَدُ الرَّجُلَ".toList).map (·.2.2) = [some .isnadiyya, some .isnadiyya, some .taqyidiyya] ∧
    (mantuq "ذَهَبَ أَبُو الْوَلَدِ".toList).map (·.2.2) = [some .isnadiyya, some .isnadiyya, some .idafiyya] ∧
    (mantuq "فِي الدَّارِ".toList).map (·.2.2) = [none, some .idafiyya] := by
  decide +kernel

/-- **قوّةُ جملٍ ودعاوى بعضها، وحكمُ «لَا تَذْهَبْ»، وإسنادُ «فِي الدَّارِ»:** قوّةُ «هَلْ ذَهَبَ الْوَلَدُ» إنشاءٌ ومقدّمةُ القوّة فيها منفيّة (`shartQuwwa`)، وقوّةُ «إِنْ ذَهَبَ
    الْوَلَدُ» تعليق، و«لَمْ ذَهَبَ» نفي، و«مَنْ ذَهَبَ» «لا حكم»؛ وقوّةُ «ذَهَبَ الْوَلَدُ» خبرٌ مثبتٌ ودعواها مرخَّصة، وقوّةُ «ذَهَبَتِ الْبِنْتُ» خبرٌ مثبت؛
    وقوّةُ «يَذْهَبُ الْوَلَدُ» و«ضَرَبَ الْوَلَدُ مَنْ» و«ضَرَبَ الْوَلَدُ شَرَعَ» و«ثُمَّ الْوَلَدُ» و«بِئْسَ الرَّجُلُ» و«عُمَرَ الْوَلَدُ» و«أَذَهَبَ الْوَلَدُ»
    و«كَانَ الْوَلَدُ» و«لِيَذْهَبْ زَيْدٌ» و«لَا تَذْهَبْ» «لا حكم»، وجملةُ «لَا تَذْهَبْ» ممتنعة؛ و«فِي الدَّارِ» لا إسنادَ فيها ودعواها معلَّقة. -/
theorem athar_quwwa :
    quwwaJumla "هَلْ ذَهَبَ الْوَلَدُ".toList = .insha ∧ (shartQuwwa "هَلْ ذَهَبَ الْوَلَدُ".toList).hal = .manfi ∧
    quwwaJumla "إِنْ ذَهَبَ الْوَلَدُ".toList = .taliq ∧ quwwaJumla "لَمْ ذَهَبَ".toList = .nafy ∧
    quwwaJumla "مَنْ ذَهَبَ".toList = .laHukm ∧ quwwaJumla "ذَهَبَ الْوَلَدُ".toList = .ithbat ∧
    hukm (uqdaDawa "ذَهَبَ الْوَلَدُ".toList) = .murakhkhas ∧
    quwwaJumla "ذَهَبَتِ الْبِنْتُ".toList = .ithbat ∧ quwwaJumla "يَذْهَبُ الْوَلَدُ".toList = .laHukm ∧
    quwwaJumla "ضَرَبَ الْوَلَدُ مَنْ".toList = .laHukm ∧ quwwaJumla "ضَرَبَ الْوَلَدُ شَرَعَ".toList = .laHukm ∧
    quwwaJumla "ثُمَّ الْوَلَدُ".toList = .laHukm ∧ quwwaJumla "بِئْسَ الرَّجُلُ".toList = .laHukm ∧
    quwwaJumla "عُمَرَ الْوَلَدُ".toList = .laHukm ∧
    quwwaJumla "أَذَهَبَ الْوَلَدُ".toList = .laHukm ∧ quwwaJumla "كَانَ الْوَلَدُ".toList = .laHukm ∧
    quwwaJumla "لِيَذْهَبْ زَيْدٌ".toList = .laHukm ∧ quwwaJumla "لَا تَذْهَبْ".toList = .laHukm ∧
    mumtaniB (hukm (jumlaM "لَا تَذْهَبْ".toList)) = true ∧
    isnadFi "فِي الدَّارِ".toList = false ∧ muallaqB (hukm (uqdaDawa "فِي الدَّارِ".toList)) = true := by
  decide +kernel

/-- **قوّةُ عشر جملٍ ودعاواها:** قوّةُ «رَحِمَ اللَّهُ زَيْدًا» و«جَعْفَرَ زَيْدٌ» و«ذَلِكَ الْكِتَابُ» و«مَعَكَ زَيْدٌ»
    و«لَيْتَكَ قَائِمٌ» و«عَلَّكَ قَائِمٌ» و«كَانَتْ هِنْدٌ» و«عَسَتْ هِنْدٌ» و«فَلْيَرَ زَيْدٌ» و«وَلْيَرَ زَيْدٌ» خبرٌ مثبت، ودعوى كلٍّ منها مرخَّصة. -/
theorem athar_hadd :
    quwwaJumla "رَحِمَ اللَّهُ زَيْدًا".toList = .ithbat ∧ hukm (uqdaDawa "رَحِمَ اللَّهُ زَيْدًا".toList) = .murakhkhas ∧
    quwwaJumla "جَعْفَرَ زَيْدٌ".toList = .ithbat ∧ hukm (uqdaDawa "جَعْفَرَ زَيْدٌ".toList) = .murakhkhas ∧
    quwwaJumla "ذَلِكَ الْكِتَابُ".toList = .ithbat ∧ hukm (uqdaDawa "ذَلِكَ الْكِتَابُ".toList) = .murakhkhas ∧
    quwwaJumla "مَعَكَ زَيْدٌ".toList = .ithbat ∧ hukm (uqdaDawa "مَعَكَ زَيْدٌ".toList) = .murakhkhas ∧
    quwwaJumla "لَيْتَكَ قَائِمٌ".toList = .ithbat ∧ hukm (uqdaDawa "لَيْتَكَ قَائِمٌ".toList) = .murakhkhas ∧
    quwwaJumla "عَلَّكَ قَائِمٌ".toList = .ithbat ∧ hukm (uqdaDawa "عَلَّكَ قَائِمٌ".toList) = .murakhkhas ∧
    quwwaJumla "كَانَتْ هِنْدٌ".toList = .ithbat ∧ hukm (uqdaDawa "كَانَتْ هِنْدٌ".toList) = .murakhkhas ∧
    quwwaJumla "عَسَتْ هِنْدٌ".toList = .ithbat ∧ hukm (uqdaDawa "عَسَتْ هِنْدٌ".toList) = .murakhkhas ∧
    quwwaJumla "فَلْيَرَ زَيْدٌ".toList = .ithbat ∧ hukm (uqdaDawa "فَلْيَرَ زَيْدٌ".toList) = .murakhkhas ∧
    quwwaJumla "وَلْيَرَ زَيْدٌ".toList = .ithbat ∧ hukm (uqdaDawa "وَلْيَرَ زَيْدٌ".toList) = .murakhkhas := by
  decide +kernel

/-- **صورةُ الماضي (`madiSura`) في كلمات، وحكمُ جملٍ وقوّتُها:** كلماتُ القائمة الأولى بصورة الماضي، وكلماتُ الثانية ليست بصورته؛
    و«أَكْرَمَ زَيْدٌ» و«فَلْيَذْهَبْ زَيْدٌ» و«هَذَا زَيْدٌ» و«لَيْسَتْ هِنْدٌ» و«رَحِمَكَ اللَّهُ» مرخَّصةٌ قوّتُها «لا حكم»؛ وقوّةُ «ضَرَبْتَ الْوَلَدُ»
    و«ضَرَبْتُنَّ الْوَلَدُ» و«ضَرَبْتُكَ الْوَلَدُ» و«فَذَهَبَ الْوَلَدُ» و«الْوَلَدُ ذَاهِبٌ» و«زَيْدٌ قَائِمٌ» «لا حكم». -/
theorem athar_hadd_sura :
    (["ضَرَبَ", "عَلِمَ", "كَرُمَ", "بَقِيَ", "مَاتَ", "بَتَّ", "دَحْرَجَ", "كَتَّبَ", "حَوْقَلَ", "قَاتَلَ", "حَاجَّ", "ضَرَبَتْ",
       "ذَهَبَتِ", "مَدَّتْ", "رَمَتْ", "رَمَتِ", "دَعَتْ", "رَأَتْ", "زَارَكَ", "مَدَّكَ", "فَرَمَتْ", "سَكَتْ", "كَانَتْ", "عَسَتْ",
       "مَعَكَ", "عَلَّ", "حَاشَ", "لَاتَ", "جَعْفَرَ", "ذَلِكَ", "لَيْتَكَ", "عَلَّكَ", "فَلْيَرَ", "وَلْيَرَ", "حَمِيَ"]).all
      (fun w => madiSura (khalaya w.toList)) = true ∧
    (["ضَرَبْتُ", "ضَرَبْتِ", "ضَرَبْتُمْ", "ضَرَبْنَا", "ضَرَبْتَ", "ضَرَبْنَ", "رَمَيْتَ", "سَكَتَّ", "سَكَنَّ", "ضَرَبْتُنَّ",
       "ضَرَبُوا", "ضَرَبَا", "ضَرَبْتُكَ", "ضَرَبْنَاكَ", "ضَرَبْتُمُوكَ", "رَمَيْتُكَ", "ضَرَبُوكَ", "ضَرَبَاكَ", "رَمَى", "دَعَا",
       "ضَرَبَكَ", "ضَرَبَكِ", "قَاتَلَكَ", "ضَرَبَتْكَ", "زَارَهُ", "زَارَكِ", "فَذَهَبَ", "ضُرِبَ", "ضَرْبَ", "أَكْرَمَ", "بِئْسَ",
       "فَلْيَذْهَبْ", "هَذَا", "لَيْسَتْ", "رَحِمَكَ", "مَاتْ", "لَمْ", "إِنْ", "هَلْ"]).all (fun w => !madiSura (khalaya w.toList)) = true ∧
    hukm (jumlaM "أَكْرَمَ زَيْدٌ".toList) = .murakhkhas ∧ quwwaJumla "أَكْرَمَ زَيْدٌ".toList = .laHukm ∧
    quwwaJumla "ضَرَبْتَ الْوَلَدُ".toList = .laHukm ∧ quwwaJumla "ضَرَبْتُنَّ الْوَلَدُ".toList = .laHukm ∧
    quwwaJumla "ضَرَبْتُكَ الْوَلَدُ".toList = .laHukm ∧ quwwaJumla "فَذَهَبَ الْوَلَدُ".toList = .laHukm ∧
    quwwaJumla "الْوَلَدُ ذَاهِبٌ".toList = .laHukm ∧ quwwaJumla "زَيْدٌ قَائِمٌ".toList = .laHukm ∧
    hukm (jumlaM "فَلْيَذْهَبْ زَيْدٌ".toList) = .murakhkhas ∧ quwwaJumla "فَلْيَذْهَبْ زَيْدٌ".toList = .laHukm ∧
    hukm (jumlaM "هَذَا زَيْدٌ".toList) = .murakhkhas ∧ quwwaJumla "هَذَا زَيْدٌ".toList = .laHukm ∧
    hukm (jumlaM "لَيْسَتْ هِنْدٌ".toList) = .murakhkhas ∧ quwwaJumla "لَيْسَتْ هِنْدٌ".toList = .laHukm ∧
    hukm (jumlaM "رَحِمَكَ اللَّهُ".toList) = .murakhkhas ∧ quwwaJumla "رَحِمَكَ اللَّهُ".toList = .laHukm := by
  decide +kernel

/-- **إطارا «مَنْ ذَهَبَ» و«عَلَا الْجَبَلُ» ومقدّماتُهما، وحكما جملتين، وقوّةُ «إِنْ أَدْرِي»:** إطارُ «مَنْ ذَهَبَ» وإطارُ «عَلَا الْجَبَلُ» جارٌّ ومجرور، وفي إطار كلٍّ منهما
    مقدّمةُ كلمةٍ واحدة «مشهود»؛ و«عَلَا الْجَبَلُ» و«قَامَ أَبُو بَكْرٍ» ممتنعتان؛ وقوّةُ «إِنْ أَدْرِي» تعليق. -/
theorem athar_hadd_itar :
    (utur "مَنْ ذَهَبَ".toList).map (·.1) = [[.harfJarr, .majrur]] ∧
    (adawatItar "مَنْ ذَهَبَ".toList [.harfJarr, .majrur]).map (·.halFiil) = [.mashhud] ∧
    (utur "عَلَا الْجَبَلُ".toList).map (·.1) = [[.harfJarr, .majrur]] ∧
    (adawatItar "عَلَا الْجَبَلُ".toList [.harfJarr, .majrur]).map (·.halFiil) = [.mashhud] ∧
    mumtaniB (hukm (jumlaM "عَلَا الْجَبَلُ".toList)) = true ∧
    mumtaniB (hukm (jumlaM "قَامَ أَبُو بَكْرٍ".toList)) = true ∧
    quwwaJumla "إِنْ أَدْرِي".toList = .taliq := by
  decide +kernel

/-- **«إِنَّمَا» في الصدر وموانعُ المفهوم:** «إِنَّمَا» في صدر «إِنَّمَا ذَهَبَ الْوَلَدُ» (`innamaJumla`)، وأحوالُ موانع عقدة مفهومها بلا ودائع
    (`wadaKhali`): مشهود، ثمّ لم يُفحص مرّتين. -/
theorem athar_innama :
    innamaJumla "إِنَّمَا ذَهَبَ الْوَلَدُ".toList = true ∧
    ((muqMafhum "إِنَّمَا ذَهَبَ الْوَلَدُ".toList wadaKhali).filter (·.naw == .mani)).map (·.hal) =
      [.mashhud, .ghayrMafhus, .ghayrMafhus] := by
  decide +kernel

end Nizam.Athar
