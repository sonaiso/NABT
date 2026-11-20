/-
# أثرُ العُقَد على ضابطه المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن** (`Nizam/AtharDabit.lean`، بنصّ المواصفة `tahaqquq/dawabit/athar/wasf.md` §القياس): لكلّ حالةٍ من `Dabit.halat` (كتبها مؤلّفٌ
مستقلٌّ إجرائيًّا من المواصفة والمصادر الخمسة، وفي سياقه ما حُقن آليًّا — `taalif.md` —، وجُمّدت ببصمتها في `tahaqquq/dawabit/athar/tajmid.json`
في الإيداع `def3e90` قبل إيداع الشفرة `a721d74`) حقلُ نوعها: `quwwa` (`quwwaJumla` على نصّ الجملة) أو `qayd` (`qaydMuharrik`).

**الوسم.** سبعُ مبرهناتٍ على الشاهد: `majal` و`natayij_1` (يُحسب فيها المحرّكُ على الحالات الخمسين مرّةً واحدة) و`azwaj_1` بـ`decide` على
الحالات المجمَّدة؛ و`natija` و`natija_fia` و`akhta_1` بإعادة الكتابة بـ`natayij_1` ثمّ `decide` — خارجَ حرف المعيار (يستدعي برهانُها مبرهنةً من
الملفّ)، معلَن؛ و`rafd_shahid` على جملةٍ مبنيّة. ومعنى العدّ موافقةُ الشفرة لقراءةٍ مستقلّةٍ للنطاق في الحقل المسؤول، لا تغطيةُ اللغة: الحالاتُ مؤلَّفة
لا عيّنةٌ من استعمال. **والمواصفةُ كُتبت بعد الشفرة** (انحرافٌ عن المنهج §٤-أ؛ `tahaqquq/dawabit/athar/mulhaq_1.md`).

**التشغيلات.** المبرهناتُ هنا على الشفرة الحاليّة دائمًا. وسجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/athar/` (`natija_1.json` …).
- `natija_1.json`: التشغيلُ الأوّل على الشفرة المجمَّدة في `a721d74`، قبل أيّ تعديلٍ لها بعد قراءة الحالات: 7 صوابًا من 50، و43 نقصَ تغطية،
  ولا خطأ ولا تجاوز ولا اختيار ولا ردَّ من القارئ. وفي ملاحظته سببُ القيد «الأشكالُ الستّة لا تقرأ جملَها»، وأنّ ما بعد `natayij_1` بإعادة الكتابة،
  وكلاهما أوسعُ من سنده؛ يصحّحهما `natija_2.json`.
- `natija_2.json`: على مادّةٍ مكشوفة، بعد المراجعة الرابعة: زيدت في `Nizam/Athar.lean` شاهدتا حدٍّ (`athar_hadd_sura`، `athar_hadd_itar`)،
  وصُحّح رأسُه وسندٌ فيه (L56–57)، وصار برهانُ ما يُعاد كتابتُه بـ`<;>`، وزيدت في بصمة الشفرة (SHIFRA) ثمانيةُ ملفّاتٍ اختارها البنّاء (وبقي
  ممّا يبلغه الحسابُ ما زيد في `natija_3.json` و`natija_4.json`، وأحدُ الثمانية `Jisr/Awamil.lean` لا ثابتَ فيه يبلغه، خرج في `natija_4.json`)؛ ولم تتغيّر دوالُّ الحكم: الأعدادُ نفسُها.
- `natija_3.json`: على مادّةٍ مكشوفة، بعد المراجعة الخامسة: تغيّرت دالّةُ حكم — `madiSura` تردّ التاءَ أو النونَ المفتوحةَ بعد ساكنٍ ليس ألفًا ولا مثلَها
  («ضَرَبْتَ الْوَلَدُ» كانت خبرًا مثبتًا بدعوى مرخَّصة)، وبقي الخللُ في المثل («ضَرَبْتُنَّ الْوَلَدُ»، «سَكَتَّ الْوَلَدُ») —، ولم تمسّ حالة؛ وزيد في بصمة
  الشفرة ملفّا الأسماء الستّة. الأعدادُ نفسُها.
- `natija_4.json`: على مادّةٍ مكشوفة، بعد المراجعة السادسة: تغيّرت `madiSura` فصار المثلُ قبل التاء أو النون المفتوحة «لا حكم» (ومعه «بَتَّ»
  الماضي: ردٌّ لا خطأ)، ولم تمسّ حالة؛ وصارت بصمةُ الشفرة محسوبةً بـLean (`SHIFRA_LEAN` في `tahaqquq/test_athar_dabit.py`، الفحص ٣د): كلُّ ملفٍّ فيه
  ثابتٌ يبلغه حسابُ `natijaHala`، واحدٌ وأربعون (وخرج منها `Jisr/Awamil.lean`: لا ثابتَ فيه يبلغه الحساب). الأعدادُ نفسُها.
- `natija_5.json`: على مادّةٍ مكشوفة، بعد المراجعة السابعة: صارت `madiSura` أوزانًا موجبةً (`waznMadi`) بدل الردّ بموانع، لأنّ الضميرَ المرفوعَ المتحرّك
  ومعه ضميرٌ منصوب («ضَرَبْتُكَ الْوَلَدُ») كان خبرًا مثبتًا بدعوى مرخَّصة؛ فعاد «بَتَّ» بها، وصار «فَذَهَبَ الْوَلَدُ» «لا حكم» (كان خبرًا مثبتًا، حدًّا معلَنًا).
  ولم تمسّ حالة. الأعدادُ نفسُها.
- `natija_6.json`: على مادّةٍ مكشوفة، بعد المراجعة الثامنة: زيد في الأوزان الناقصُ قبل تاء التأنيث («رَمَتْ»، وكان قد رُدّ في `natija_5.json` ولم يُعلَن)
  وفَاعَّ («حَاجَّ»)، وأُعلن ما ليس فعلًا على الأوزان («ذَلِكَ»، «لَيْتَكَ»، «عَلَّكَ»، «لَاتَ»). وفروقُ نسخ `madiSura` على 2454 صيغةً مولَّدة في
  `tahaqquq/dawabit/athar/madi_farq.md`. ولم تمسّ حالة. الأعدادُ نفسُها. (وفَاعَّ رُدّ في `natija_5.json` كذلك، كما في ملاحظة `natija_6.json`؛
  و«عَلَّكَ» و«لَاتَ» فعلان في اللسان: `natija_8.json`؛ والصيغُ في `madi_farq.md` اليوم غيرُ 2454.)
- `natija_7.json`: على مادّةٍ مكشوفة، بعد المراجعة التاسعة: لم تتغيّر دوالُّ الحكم؛ صار وصفُ `madiSura` وصفًا لأشكال الخلايا بأمثلةٍ لها شواهد، وزيد في
  شاهدَي الحدّ (`athar_hadd`، `athar_hadd_sura`). الأعدادُ نفسُها.
- `natija_8.json`: على مادّةٍ مكشوفة، بعد المراجعة العاشرة: لم تتغيّر دوالُّ الحكم؛ أُعلن الأمرُ بلام الأمر الساكنة بعد الفاء أو الواو خبرًا مثبتًا خطأً
  («فَلْيَرَ زَيْدٌ»)، وصار ما يقع على الأوزان من غير الفعل «ما قد لا يكون فعلًا» (ومنه في اللسان أفعال)، وزيد في شاهدَي الحدّ وفي `athar_quwwa`.
  الأعدادُ نفسُها. (وأكثرُ صيغ لام الأمر بعد سابقة في `madi_farq.md` ليس بصورة الماضي، و«من غير الفعل» يناقض «ومنه في اللسان أفعال»: `natija_9.json`.)
- `natija_9.json`: على مادّةٍ مكشوفة، بعد المراجعة الحادية عشرة: لم تتغيّر دوالُّ الحكم؛ صار وصفُ ما يُقرأ خبرًا مثبتًا شرطًا على الخلايا بأمثلة
  (منها «فَلْيَرَ زَيْدٌ» خبرٌ مثبت و«فَلْيَذْهَبْ زَيْدٌ» «لا حكم»)، وزيد في شاهدَي `athar_hadd_sura` و`athar_quwwa`. الأعدادُ نفسُها.
- `natija_10.json`: على مادّةٍ مكشوفة، بعد المراجعة الثانية عشرة: لم تتغيّر دوالُّ الحكم؛ صار الحدُّ في رأس `Nizam/Athar.lean` شرطَ `quwwaJumla` و`madiSura`
  وقائمتين من الكلمات بلا أصناف، وزيد «مَاتْ» في `athar_hadd_sura`. الأعدادُ نفسُها.
- `natija_11.json`: على مادّةٍ مكشوفة، بعد المراجعة الثالثة عشرة: لم تتغيّر دوالُّ الحكم؛ قُيّد الحدُّ في رأس `Nizam/Athar.lean` بالجملة التي لا أداةَ في صدرها،
  و«من الإطار المرخَّص» في CLAUDE.md وREADME.md، ورُدّ بندُ `natija_6.json` هنا إلى لفظه في `25ff932` بتصحيحٍ بعده. الأعدادُ نفسُها. (وأُعيدت
  فيه كتابةُ التصحيح الملحق ببند `natija_8.json` هنا عدًّا على صيغ `madi_farq.md`: `natija_12.json`.)
- `natija_12.json`: على مادّةٍ مكشوفة، بعد المراجعة الرابعة عشرة: لم تتغيّر دوالُّ الحكم؛ صار كلُّ تعليلٍ لحكم `quwwaJumla` في توثيقات `Nizam/Athar.lean`
  وتعليقات `tahaqquq/test_athar.py` بشرطه كاملًا، وقراءةُ الإطار في الرأس بفرع هيكل الأسماء الستّة، وزيدت «لَمْ» و«إِنْ» و«هَلْ» في `athar_hadd_sura`.
  الأعدادُ نفسُها. (ولم يصِر كلُّ تعليلٍ بشرطه: بقي في توثيق `athar_quwwa` وتعليقين في `tahaqquq/test_athar.py` تعليلٌ بشطرٍ منه، وفي الرأس «و«كَانَ
  الْوَلَدُ» «لا حكم» بصفّه في الجدول»: `natija_13.json`.)
- `natija_13.json`: على مادّةٍ مكشوفة، بعد المراجعة الخامسة عشرة: لم تتغيّر دوالُّ الحكم؛ صارت توثيقاتُ `sufuf_shawahid` و`maqta_adat` و`qaydMin_shahid`
  و`athar_maqta` و`athar_adat` و`athar_dawr` و`athar_qism` و`athar_quwwa` و`athar_hadd` و`athar_hadd_sura` ما تقوله بنودُها بلا تعليل، وقراءةُ الإطار والمعجم في الرأس
  بشرطَي `Jisr.NassItar.itarat` و`wifaq`، وزيدت «حَمِيَ» في `athar_hadd_sura`. الأعدادُ نفسُها. (و«ما تقوله بنودُها» أعلى من سنده، وفات قائمةَ ما بقي
  في تصحيح بند `natija_12.json` أعلاه «بصفّه في `athar_quwwa`» في توثيق `athar_hadd` وتعليقٌ ثالث: `natija_14.json`.)
- `natija_14.json`: على مادّةٍ مكشوفة، بعد المراجعة السادسة عشرة: لم تتغيّر دوالُّ الحكم؛ صارت توثيقاتُ مبرهنات الشاهد في `Nizam/Athar.lean` بنودَها
  وحدها (وأوصافُ الكلمات وأسانيدُها في الرأس)، وحُذفت تعليقاتُ الحالات في `tahaqquq/test_athar.py`، وقراءةُ الإطار في الرأس بشرط `munawwan`، و«الأثرُ على
  الشاهد» فيه بالودائع الخالية. الأعدادُ نفسُها. (وبقيت في التوثيقات عناوينُ تحكم وإحالةٌ في `athar_hadd`، وفي «الأثرُ على الشاهد» عمومٌ ليس في
  المبرهنات المحال إليها: `natija_15.json`.)
- `natija_15.json`: على مادّةٍ مكشوفة، بعد المراجعة السابعة عشرة: لم تتغيّر دوالُّ الحكم؛ صار «الأثرُ على الشاهد» في الرأس قيمًا على جملٍ بأعيانها،
  وعناوينُ التوثيقات أسماءَ موضوع بنودها، وخطأُ القوّة وأوصافُ الكلمات في «حدُّه» بشروطها. الأعدادُ نفسُها. (والشرطُ زيد للدعاء ولوصفَي «مَعَكَ»
  و«عَلَّكَ» وحدها، وبقي في «الأثرُ على الشاهد» قانونان عامّان للمقطع والأداة، وفي ثلاثة عناوين ما لا يسمّي بنودَها: `natija_16.json`.)
- `natija_16.json`: على مادّةٍ مكشوفة، بعد المراجعة الثامنة عشرة: لم تتغيّر دوالُّ الحكم؛ صار «الأثرُ على الشاهد» في الرأس يسمّي جملَ `athar_maqta`
  و`athar_adat`، والعمومُ فيه مُسنَدًا إلى `unsurDawr_qayd` و`la_shart_fi_majal` (لكلّ) و`la_tarqiya` (تعريفيّة) و`dawa_murakhkhas` بالربط؛ وتعليقُ المعجم في
  «حدُّه» بشرطَي `itarM_muallaq`، و«إِنْ» صدرًا تعليقًا بتعريف `quwwaSufuf`؛ وزيد في أربعة عناوين ما يسمّي بنودَها. الأعدادُ نفسُها. (و`la_tarqiya`
  تعريفيّةٌ لا يُسند إليها عموم، وعنوانُ `athar_quwwa` لا يسمّي إسنادَ «فِي الدَّارِ»، و«ثلاثة عناوين» في التصحيح الملحق ببند `natija_15.json` أعلاه أربعة؛
  ولم يُذكر هنا «من أقسامه» ولا «قيدُ الشرط (`adatQayd`)» ولا «من غايةٍ» ولا رأسُ `tahaqquq/test_athar.py`: `natija_17.json`.)
- `natija_17.json`: على مادّةٍ مكشوفة، بعد المراجعة التاسعة عشرة: لم تتغيّر دوالُّ الحكم؛ صار عمومُ القوّة في الرأس «بتعريف `quwwaJumla`» ونصُّه
  `la_tarqiya` (تعريفيّة)، وحُذف من «الأثرُ على الشاهد»؛ و«في غير ذلك» من تعليق المعجم مقدّمةً «بتعريف `wifaq`» وحكمًا لا يتغيّر بـ`itarM_sawa`، ومفهومُ
  المخالفة في المجال بـ`mafahim_mukhalafa` و`qaydJumla_sinf`، والصفةُ والعددُ بـ`unsurDawr_qayd`؛ وتوثيقا `itarM_muallaq` و`athar_dawr` وعنوانُ
  `athar_quwwa` بما في بنودها. الأعدادُ نفسُها. (ولم يُذكر هنا «بتعريف `qaydJumla` على `qaydMin`» ولا «كلمتا «الدَّارِ» و«الدَّارُ»»، و`itarM_sawa` في
  «حدُّه» بلا فرضها، و«بتعريف `wifaq`» لما يُخرجه `muqDawr`: `natija_18.json`.)
- `natija_18.json`: على مادّةٍ مكشوفة، بعد المراجعة العشرين: لم تتغيّر دوالُّ الحكم؛ في رأس `Nizam/Athar.lean`: `itarM_sawa` في «حدُّه» وفي قسم «الإطارُ والجملةُ بعد المعجم» بفرضيها،
  والجملةُ الممتنعةُ إطاراتُها بفروض `Nizam.Silsila.jumla_natija` على `uqdaJumla` وبـ`kullMaqrua`، و«بتعريف `muqDawr` على `wifaq`» في موضعين، و«بتعريف `saffFiDawr`»، و«بتعريف
  `Jisr.NassItar.itarat`». الأعدادُ نفسُها. (ولم يُذكر هنا تغييرُ رأس `tahaqquq/test_athar.py` ولا ما ضبطه المراجع، وبقيت توثيقاتُ `itarM_sawa`
  و`jumlaM_murakhkhas` و`jumlaM_mumtani` و`jumlaM_itar` و`dawa_murakhkhas` بلا فروضها: `natija_19.json`.)
- `natija_19.json`: على مادّةٍ مكشوفة، بعد المراجعة الحادية والعشرين، وضبط فيها المراجعُ توثيقاتٍ بلا فروض مبرهناتها، وعمومًا من تعريفٍ في المتن بلا
  «بتعريف»، ووصفَ فروض `jumla_natija` في (١٦٣)، ونقصَ بند `natija_18.json`: لم تتغيّر دوالُّ الحكم؛ وفي `Nizam/Athar.lean`: توثيقُ `itarM_sawa` بفرضيها،
  وتوثيقاتُ `jumlaM_murakhkhas` و`jumlaM_mumtani` و`jumlaM_itar` و`dawa_murakhkhas` «بالربط»، وتوثيقُ `saffFiDawr` «بتعريف `Jisr.NassItar.itarat`»؛ وفي
  رأسه «الإطارُ يقرأ، بتعريف `Jisr.NassItar.itarat`»، و«والخبرُ المثبت بتعريف `quwwaJumla` وحدها»، و«فهي `uqdaJumla` بتعريف `jumla`»؛ وفي CLAUDE.md
  «فهي `uqdaJumla` بتعريف `jumla`» و«لا إطارَ شرطٍ في المجال، بتعريف `Jisr.NassItar.itarat`». الأعدادُ نفسُها. (وبقي نظيرا «بتعريف
  `Jisr.NassItar.itarat`» و«بتعريف `quwwaJumla`» في «حدُّه» من CLAUDE.md بلا «بتعريف»، وفي الرأس وCLAUDE.md مواضعُ أخرى من النمط نفسِه: `natija_20.json`.)
- `natija_20.json`: على مادّةٍ مكشوفة، بعد المراجعة الثانية والعشرين (وحكمُها «يُدمج» بأربع مشكلاتٍ خفيفة): لم تتغيّر دوالُّ الحكم؛ وفي رأس
  `Nizam/Athar.lean`: «فعلٌ بتعريف `Jisr.NassItar.itarat`» («ما كان»)، و«(بتعريفَي `uqdaDawa` و`muqMafhum`)» (المنطوق)، و«بتعريف `madiSura`» («حدُّه»)؛ وفي
  CLAUDE.md: «الإطارُ يقرأ، بتعريف `Jisr.NassItar.itarat`»، و«والخبرُ المثبت بتعريف `quwwaJumla` وحدها»، و«(بتعريف `madiSura`»، و«(بتعريف `muqDawr` على `wifaq`)»؛
  و«بالربط» في رأس `tahaqquq/test_athar.py` لـ`dawa_murakhkhas` وفي `خارطة_الطريق.md` لـ`mafhum_jisr`. الأعدادُ نفسُها.
- `natija_21.json`: على مادّةٍ مكشوفة، بعد دمج main في `jisr/qiraa-awamil` (#118 غيّر `Dal/Tahsil.lean`، وهو في SHIFRA، بلا سجلٍّ لهذا الضابط): لم تتغيّر
  دوالُّ الحكم ولا الأعداد.
- `natija_22.json`: على مادّةٍ مكشوفة، بعد الحساب الصنفيّ (`ef11cdd` غيّر `SLGE/Law.lean`، وهو في SHIFRA: أقسامٌ جديدة، ولم يتغيّر فيه δ ولا ω ولا القبول):
  لم تتغيّر دوالُّ الحكم ولا الأعداد. وأسقط حقلَ `iydaa`.
- `natija_23.json`: على مادّةٍ مكشوفة، بعد مراجعة طلب الحساب الصنفيّ الثانية، بلا تغييرٍ في بصمات الشفرة: حقلُ `iydaa` لـ `Dal/Tahsil.lean`
  و`SLGE/Law.lean`. لم تتغيّر دوالُّ الحكم ولا الأعداد.

**الإخفاقاتُ الثلاثة والأربعون كلُّها نقصُ تغطية** في الحقل المسؤول (`akhta_1`): قال المحرّكُ «لا حكم» حيث المتوقَّعُ حكم. وحكم في أربع حالاتٍ
موجبة فأصاب فيها، وامتنع في الخارجة الثلاث فأصاب. والأسبابُ قراءةُ البنّاء لمخرج الأداة `athar` على الحالات (`mulhaq_1.md` §٤–§٥)، لا مبرهنة:
- **القيد** (21 حالةً، ولا إطارَ مرخَّصًا لواحدةٍ منها، فـ«لا حكم»): الجملةُ بعد المعجم ممتنعةٌ في 11 (إطاراتُها كلُّها ممتنعة)، و«لا تنطبق» في 8 (لا إطارَ
  لها في المجال)، ومعلَّقةٌ في 2.
- **القوّة** (22 حالة): أداةٌ في الصدر صفوفُها بأساليبَ مختلفة («ما»، «متى»)، أو صفٌّ لم يُبنَ أثرُه في القوّة («لمّا»، «حيثما»)، أو أداةٌ لا صفَّ
  لها بصورتها («لا»)، أو متّصلةٌ أو مؤخَّرة، أو ما ليس ماضيًا مجرّدًا في دور الفعل من إطارٍ مرخَّص.
**وما لا يقيسه الضابط:** عُقَدُ الجملة والقسم والإطار والمنطوق والدعوى والمفهوم. والجملةُ بعد المعجم ممتنعةٌ في 18 حالةً من الخمسين كتبها
المؤلّف عربيّةً صحيحة (7 في القوّة و11 في القيد) — ردٌّ خاطئٌ معلَن في رأس `Nizam/Athar.lean` (`athar_hadd_itar`)، لا يعدّه هذا العدّ. **وما لم
تبلغه حالة** (مخرجُ `athar` على الخمسين): لا قيدَ في حالةٍ منها (QAYD «-» في كلّها)، ولا مفهومَ في الجسر، ولا خبرٌ مثبت، ولا دعوى مرخَّصة، ولا
مفهومٌ مرخَّص؛ فكلُّ مبرهنةٍ فرضُها شيءٌ من ذلك لا يشهد لها الضابط ولا عليها، منها `qaydJumla_mem` و`qaydJumla_dawr` و`qaydJumla_sinf` و`qaydJumla_anwa`
و`mashud_qaydJumla` (فرضُها قيد)، و`mafhum_kalima` (مفهومٌ في الجسر)، وشطرُ الخبر المثبت من `la_tarqiya`، وشطرُ الترخيص من `dawa_murakhkhas`
و`mafhum_jisr`.
-/
import Nizam.AtharDawabit

namespace Nizam.Athar
namespace Qiyas

open Dabit

/-- **المجالُ غيرُ فارغ ولا مائلٍ إلى «لا حكم»:** 50 حالة، 29 قوّةً و21 قيدًا. والقوّةُ المتوقَّعة: إثبات 6، نفي 5، تعليق 6، إنشاء 7، لا حكم 3،
    وبديلان 2؛ والقيدُ: صفة 3، شرط 2، غاية 2، عدد 4، لا قيد 7، لا حكم 0، وقائمةٌ من اثنين فأكثر 3؛ وذواتُ الزوج 16 (ثمانيةُ أزواج)؛ والفئات: موجب 25،
    وحدّ 10، وخارج 3، وعموم 9، وغموض 3. -/
theorem majal : majalAadad halat = [50, 29, 21, 6, 5, 6, 7, 3, 2, 3, 2, 2, 4, 7, 0, 3, 16, 25, 10, 3, 9, 3] := by
  decide +kernel

/-- **النتيجةُ حالةً حالة** (الحالة، الفئة، النوع، النتيجة): المحرّكُ على الحالات الخمسين. -/
theorem natayij_1 :
    natayij halat = [
      ("A01", .mujib, .quwwa, .sawab),
      ("A02", .mujib, .quwwa, .naqsTaghtiya),
      ("A03", .mujib, .quwwa, .naqsTaghtiya),
      ("A04", .umum, .quwwa, .naqsTaghtiya),
      ("A05", .mujib, .quwwa, .naqsTaghtiya),
      ("A06", .hadd, .quwwa, .naqsTaghtiya),
      ("A07", .hadd, .quwwa, .naqsTaghtiya),
      ("A08", .mujib, .quwwa, .sawab),
      ("A09", .mujib, .quwwa, .naqsTaghtiya),
      ("A10", .hadd, .quwwa, .naqsTaghtiya),
      ("A11", .mujib, .quwwa, .naqsTaghtiya),
      ("A12", .mujib, .quwwa, .sawab),
      ("A13", .mujib, .quwwa, .naqsTaghtiya),
      ("A14", .mujib, .quwwa, .naqsTaghtiya),
      ("A15", .mujib, .quwwa, .naqsTaghtiya),
      ("A16", .hadd, .quwwa, .naqsTaghtiya),
      ("A17", .hadd, .quwwa, .naqsTaghtiya),
      ("A18", .hadd, .quwwa, .naqsTaghtiya),
      ("A19", .hadd, .quwwa, .naqsTaghtiya),
      ("A20", .hadd, .quwwa, .naqsTaghtiya),
      ("A21", .umum, .quwwa, .naqsTaghtiya),
      ("A22", .umum, .quwwa, .naqsTaghtiya),
      ("A23", .umum, .quwwa, .naqsTaghtiya),
      ("A24", .ghumud, .quwwa, .naqsTaghtiya),
      ("A25", .ghumud, .quwwa, .naqsTaghtiya),
      ("A26", .kharij, .quwwa, .sawab),
      ("A27", .kharij, .quwwa, .sawab),
      ("A28", .kharij, .quwwa, .sawab),
      ("A29", .mujib, .quwwa, .sawab),
      ("A30", .mujib, .qayd, .naqsTaghtiya),
      ("A31", .hadd, .qayd, .naqsTaghtiya),
      ("A32", .mujib, .qayd, .naqsTaghtiya),
      ("A33", .mujib, .qayd, .naqsTaghtiya),
      ("A34", .umum, .qayd, .naqsTaghtiya),
      ("A35", .umum, .qayd, .naqsTaghtiya),
      ("A36", .mujib, .qayd, .naqsTaghtiya),
      ("A37", .umum, .qayd, .naqsTaghtiya),
      ("A38", .mujib, .qayd, .naqsTaghtiya),
      ("A39", .mujib, .qayd, .naqsTaghtiya),
      ("A40", .mujib, .qayd, .naqsTaghtiya),
      ("A41", .mujib, .qayd, .naqsTaghtiya),
      ("A42", .mujib, .qayd, .naqsTaghtiya),
      ("A43", .umum, .qayd, .naqsTaghtiya),
      ("A44", .hadd, .qayd, .naqsTaghtiya),
      ("A45", .ghumud, .qayd, .naqsTaghtiya),
      ("A46", .mujib, .qayd, .naqsTaghtiya),
      ("A47", .mujib, .qayd, .naqsTaghtiya),
      ("A48", .mujib, .qayd, .naqsTaghtiya),
      ("A49", .mujib, .qayd, .naqsTaghtiya),
      ("A50", .umum, .qayd, .naqsTaghtiya)] := by
  decide +kernel

/-- **النتيجة:** 7 صوابًا من 50، و43 نقصَ تغطية؛ ولا تجاوز، ولا اختيار، ولا خطأ، ولا ردَّ من القارئ. -/
theorem natija : ihsa (natayij halat) = ⟨7, 43, 0, 0, 0, 0⟩ := by
  rw [natayij_1] <;> decide

/-- **بالفئات:** موجب 4 من 25، حدّ 0 من 10، خارج 3 من 3، عموم 0 من 9، غموض 0 من 3؛ والباقي نقصُ تغطية. -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map (fun f => ihsa ((natayij halat).filter (·.2.1 == f))) =
      [⟨4, 21, 0, 0, 0, 0⟩, ⟨0, 10, 0, 0, 0, 0⟩, ⟨3, 0, 0, 0, 0, 0⟩, ⟨0, 9, 0, 0, 0, 0⟩, ⟨0, 3, 0, 0, 0, 0⟩] := by
  rw [natayij_1] <;> decide

/-- **والإخفاقاتُ الثلاثة والأربعون بأسمائها**، كلُّها نقصُ تغطية: 22 في القوّة، و21 في القيد (كلُّ حالات القيد). -/
theorem akhta_1 :
    akhta (natayij halat) = [
      ("A02", .quwwa, .naqsTaghtiya), ("A03", .quwwa, .naqsTaghtiya), ("A04", .quwwa, .naqsTaghtiya), ("A05", .quwwa, .naqsTaghtiya),
      ("A06", .quwwa, .naqsTaghtiya), ("A07", .quwwa, .naqsTaghtiya), ("A09", .quwwa, .naqsTaghtiya), ("A10", .quwwa, .naqsTaghtiya),
      ("A11", .quwwa, .naqsTaghtiya), ("A13", .quwwa, .naqsTaghtiya), ("A14", .quwwa, .naqsTaghtiya), ("A15", .quwwa, .naqsTaghtiya),
      ("A16", .quwwa, .naqsTaghtiya), ("A17", .quwwa, .naqsTaghtiya), ("A18", .quwwa, .naqsTaghtiya), ("A19", .quwwa, .naqsTaghtiya),
      ("A20", .quwwa, .naqsTaghtiya), ("A21", .quwwa, .naqsTaghtiya), ("A22", .quwwa, .naqsTaghtiya), ("A23", .quwwa, .naqsTaghtiya),
      ("A24", .quwwa, .naqsTaghtiya), ("A25", .quwwa, .naqsTaghtiya), ("A30", .qayd, .naqsTaghtiya), ("A31", .qayd, .naqsTaghtiya),
      ("A32", .qayd, .naqsTaghtiya), ("A33", .qayd, .naqsTaghtiya), ("A34", .qayd, .naqsTaghtiya), ("A35", .qayd, .naqsTaghtiya),
      ("A36", .qayd, .naqsTaghtiya), ("A37", .qayd, .naqsTaghtiya), ("A38", .qayd, .naqsTaghtiya), ("A39", .qayd, .naqsTaghtiya),
      ("A40", .qayd, .naqsTaghtiya), ("A41", .qayd, .naqsTaghtiya), ("A42", .qayd, .naqsTaghtiya), ("A43", .qayd, .naqsTaghtiya),
      ("A44", .qayd, .naqsTaghtiya), ("A45", .qayd, .naqsTaghtiya), ("A46", .qayd, .naqsTaghtiya), ("A47", .qayd, .naqsTaghtiya),
      ("A48", .qayd, .naqsTaghtiya), ("A49", .qayd, .naqsTaghtiya), ("A50", .qayd, .naqsTaghtiya)] := by
  rw [natayij_1] <;> decide

/-- **الأزواج الثمانية:** يختلف مخرجُ المحرّك بين طرفي زوجين («هَلْ»/«مَا» إنشاءٌ ولا حكم، و«أَلَمْ»/«لَمْ» لا حكمَ ونفي)، ولا يختلف في ستّة. -/
theorem azwaj_1 :
    azwaj halat = [("A01", "A02", true), ("A03", "A04", false), ("A05", "A06", false), ("A07", "A08", true),
      ("A09", "A10", false), ("A30", "A31", false), ("A32", "A33", false), ("A34", "A35", false)] := by
  decide +kernel

/-- **ردُّ القارئ في المقارنة:** جملةٌ لا يقرأ القارئُ كلماتها نتيجتُها `rafdQari` لا مقارنةُ حقلها — ولا حالةَ من الخمسين يردّها القارئ
    (`natija`)، فشاهدُ الفرع مبنيّ: «abc» مردودة، ولو كان متوقَّعُها «لا حكم» في `خارج`. -/
theorem rafd_shahid : natijaHala ⟨"X", .quwwa, .kharij, "abc", [.laHukm], [], none⟩ = .rafdQari := by
  decide +kernel

end Qiyas
end Nizam.Athar
