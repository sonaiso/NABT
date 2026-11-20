/-
  Jisr/Utur.lean — أطرُ الطبقات الثلاث على القانون العامّ (ابتداء/وصل/وقف): الدالُّ وحده، والمدلولُ وحده، والدالُّ والمدلولُ معًا.
  قرار المالك (2026-10-16): «بناء أطر الدال وحده lean and slge وأطر المدلول وحده والأهم أطر الدال والمدلول معا lean slge وفق
  القانون العام».

  **القانون العامّ** عند المالك ثلاثةُ أحكام — الابتداءُ والوصلُ والوقف — نصُّه في الدالّ (`SLGE/Law.lean` رأس الملفّ: «القانونُ
  واحدٌ بثلاثة مواضع: الابتداء: لا يُبتدأ بساكن… الوصل: لا يلتقي ساكنان… الوقف: آخرُ السلسلة يُعفى فيه التقاءُ الساكنين»؛ وفي
  `SLGE/Necessity.lean` س25: «الحدُّ الأدنى المكتمل: يُبتدأ به (القانون من الحالة 0)، ويوصَل (الانتقالاتُ)، ويوقَف عليه بعد التسكين» =
  `complete'`)، وفي التركيب (`SLGE/Tarkib.lean`: «القانون في التركيب»)، وفي الإحالة والسمات (`Maqam`، `Simat`). وهنا يُستوفى على
  الطبقات الثلاث التي رتّبها ج3 (737: اللفظ باعتبار الدالّ وحده؛ 753: باعتبار المدلول وحده؛ 771: باعتبار الدالّ والمدلول معًا — كما
  في `Dal/AqsamAllafz.lean`، `Madlul/AqsamAlmadlul.lean`، `Jisr/AqsamDalMadlul.lean`): لكلّ طبقةٍ إطارٌ وثلاثةُ أحكامٍ مسمّاةٍ
  بموضعها، وشواهدُ بـ decide، ورقمٌ يُفكّ للمدلول وللطبقة الثالثة (والدالُّ برقم المالك `encS`). **أحكامُ الدالّ الثلاثة هنا قراءةٌ
  لتقسيم المالك في Necessity س25 (لا نقلٌ لـ`Fwasl`)؛
  وتعيينُها على المدلول وعلى الطبقة الثالثة قرارٌ معلَنٌ للبنّاء** على نهجه — لا نصَّ عنده يسمّي الثلاثةَ في المدلول (`MadlulAwwalan`،
  `Category`). **أمضى المالكُ التعييناتِ 2026-10-16:** `nisabMahmul`، وازدواجُ «التقييدية» (قيدٌ هنا / مفعوليةٌ في `Nisab`)، وخانتا
  المسند والمسند إليه، و`jinsMahmul`، و`qismDawr` (كان/ظنّ فعل)، و`halaIrab`، والحدُّ المعلَن `haddMuallan` (المستترُ والضميرُ المتّصل والمثنّى
  والمضارعُ خبرًا خارجَه)؛ وما أُضيف بعد 2026-10-16 (§٣ «أسبابُ لا حكم») ليس من هذا الإمضاء؛ ووافق على ما بعدها: معجمُ الأجناس وخواصّها مودَعًا، ثمّ الأسماءُ من المخصّص والسمات، وجسرُ `Maqam` والإعرابُ
  بالحروف والتنازع.

  **١. إطارُ الدالّ وحده** `ItarDal = List NawMaqta`: نمطُ مقاطع السلسلة من تقطيعنا المبرهَن (`Dal.qatta`: `qatta_sahih`، `qatta_wahid`،
  `anwa_sitta`)، ولا نمطَ للفارغ. الأحكامُ على آلة المالك `Msent`: **ابتداء** الانتقالُ الأوّل من الحالة 0 حيّ (`δ 0 a ≠ 96`: لا
  ساكنَ ولا ألفَ متحرّكةً أوّلًا)؛ **وصل** الانتقالاتُ كلُّها حيّة في السلسلة كما تُقرأ (`run 0 l ≠ 96`: قانونُ الوصل داخلَ السلسلة —
  **وهو غيرُ `Fwasl` المالك** الذي يسأل عن قبول متحرّكٍ بعد الآخر: «بِنْت» حيّةُ الانتقالات وقفًا بساكنين و`Fwasl` يردّها إن وُصلت،
  `wasl_ghayr_Fwasl`)؛ **وقف** «المكتمل» عند المالك بعينه `complete'` (وقفيّةٌ بعد تسكين الآخر) — **وهو يحوي الابتداءَ والوصلَ بعد
  التسكين**، فالفصلُ بين الثلاثة هنا فصلٌ بالتسمية والموضع (خللُ كلٍّ يُسمّى) لا تقسيمٌ إلى شروطٍ مستقلّة؛ وما يزيده الإطارُ على المكتمل
  هو الوصلُ كما تُقرأ. العلاقاتُ مبرهَنة: الوصلُ والوقفُ كلٌّ منهما يستلزم الابتداء (`wasl_yastalzim_ibtida`، `waqf_yastalzim_ibtida`)؛
  والوصلُ والوقفُ مستقلّان على الشاهد (`wasl_waqf_mustaqillan`: الخليةُ الواحدة توصَل ولا يوقَف عليها، و«لَا» بألفٍ متحرّكة آخرًا تكتمل
  بالتسكين وتموت كما تُقرأ)؛ وما استوفى الثلاثةَ فحالتُه كما تُقرأ وقفيّةٌ (`dal_waqf_kama_yuqra` على `mover_step` المالك). والإطارُ أضيقُ
  من `complete'`: على السلاسل من خليتين، 84 يكتملها التسكينُ وتموت كما تُقرأ، وآخرُها ألفٌ متحرّكة (`dal_vs_complete`).
  الاستنفاد: لا سلسلةَ من خلية (المالك `nec_second`)، وعلى الخليتين الإطارُ والتقطيعُ سواء (`itar_dal_istinfad_2`)؛ و9,436 سلسلةً
  من خليتين يرخّصها الإطار: CV·CV 7056، CVV 84، CVC 2296، ولا نمطَ رابع (`itar_dal_anmat_2`). السلسلةُ «يرخّصها الإطار» لا «كلمة»:
  الكلمةُ وضعٌ فوق الدالّ.

  **٢. إطارُ المدلول وحده** `ItarMadlul = (موضوع، محمول، نسبة)` على مدلول المالك (`SLGE.Awwalan.Madlul`: حقيقةٌ وخواصُّ وعلاقاتٌ
  وقابليّاتٌ وأفراد، ومعنًى في نفسه `ind` وزمانٌ بهيئته `tim` — ولا لفظ). المحمولُ من الحقول الأربعة، والنسبةُ من الثلاث (`Jisr/Nisab.lean`).
  الأحكام (تعيينُ البنّاء): **ابتداء** = صلاحيةُ الموضوع مسندًا إليه بقانون المالك `Cat.roles` (معنًى في نفسه لا زمانَ بهيئته:
  `harf_la_yubtada`، `fil_la_yubtada`)؛ **وصل** = حكمٌ **ثلاثيّ** على نهج م13 من دستور الوكيل (ثلاثيّتُه: حقيقة / مجازٌ برخصة / لا حكم؛
  وثلاثيّةُ هذه الطبقة: مرخَّص / لا حكم / ممتنع — والمجازُ برخصةٍ مؤجَّلٌ إلى طبقة الحكم فوقها): «ممتنع» إن كانت
  النسبةُ ممّا لا يحتمله المحمول (`nisabMahmul`: الخاصّةُ إسنادٌ أو تقييد، القابليّةُ والفردُ إسناد، العلاقةُ إضافة — تعيينٌ معلَن)، وإلّا
  «مرخَّص» إن كان المحمولُ في حقول الموضوع (الوضع: حقيقة)، وإلّا «لا حكم» (غيابُ الشاهد ليس امتناعًا؛ المجازُ برخصةٍ في طبقة الحكم —
  م10) — `wasl_thulathi`؛ **وقف** = الإفادةُ بالإسناد (المالك `Category`: الكلامُ إسنادٌ أو تعلُّقٌ بمسندٍ مقدَّر)، والقيدُ (تقييديةٌ أو
  إضافية) جزءٌ لا كلام. والضمُّ (`damm`) يرتّب: الممتنعُ ثمّ لا حكم ثمّ الترخيص، ولا يخترع امتناعًا (`damm_mumtani`). **«التقييدية»
  هنا للخاصّة قيدًا (النعت: «الولدُ الصغير»)، وفي `Jisr/Nisab.lean` للمفعولية من أدوار المالك** — النسبةُ واحدة (ج3 721: التقييد)
  والموضعان مختلفان، ولا تبلغ التقييديةُ الطبقةَ الثالثة من خانة المسند (فهو خبرٌ أو فعلٌ أو مجرور).

  **٣. إطارُ الدالّ والمدلول معًا** `Itar3 = (الإطارُ النحويّ الممدود `Mulhaqat.Itar`، كلماتُ الخانات الظاهرة — خانات المالك الظاهرة
  بترتيبها ثمّ الملحقات بترتيبها (النائبُ خانتُه خانةُ المالك، والعاملُ الاسميّ صفةٌ لا كلمة) — بخلاياها `Dal.Kalima`، مدلولاتُها، الإسنادُ
  الدلاليّ)`. **حدُّ الطبقة** (`fiHadd`؛ وما خرج عنه «لا حكم» لا «ممتنع»: `kharij_alhadd`) هو الحدُّ المعلَن (`haddMuallan`، أمضاه المالك
  2026-10-16) ومعه منذ 2026-10-20 ما يردّه `itarOK` (قولُ المالك في LC11 وقراءةُ البنّاء: §٣ «أسبابُ لا حكم»). والحدُّ المعلَن: لا إطارَ ثانٍ (التنازع)، ولا ملحقَ
  متقدّمًا (`qabl`) ولا عاملَ اسميًّا (معمولاتُه إطارٌ فرعيّ بلا كلماتٍ هنا) ولا نائبَ مجرورًا، وكلُّ ملحقٍ يرسو على آخر خانةٍ ظاهرة أو على
  ملحق — فترتيبُ الكلمات ترتيبُ النطق؛ والمسندُ والمسندُ إليه ظاهران (المستترُ والمقدَّرُ إحالةٌ في `Maqam` غيرُ مجسورة) أو شبهُ الجملة
  بلا مسندٍ إليه (موضوعُه من المقام، يُعطى في الإسناد ولا يُفحص على كلمة)؛ والأسماءُ المعربة مفردة (الإعرابُ بالحركة على الخلية الأخيرة؛
  المثنّى والجموعُ بالحروف غيرُ مجسورة؛ والأسماءُ الستّة (القطر L78) والمنقوصُ والمقصور لا يُميَّزون بلا معجم: فجوةٌ معلَنة، تُقرأ منها منذ
  2026-10-20 «لا حكم» في الوصل حيث تُقدَّر الحالةُ على حرف علّةٍ ساكنٍ آخرًا، أو يُعرب مضافٌ بالحرف — §٣ «القراءة»). **ابتداء**: الإطارُ
  النحويّ مرخَّص (`itarOK`)، والكلماتُ بعدد الظواهر، ولكلٍّ مدلول، وأوّلُ الكلمات يُبتدأ بها في صورة ابتدائها، والموضوعُ يصلح مسندًا إليه.
  **وصل**: التركيبُ بإصلاح همزة الوصل ثلاثيًّا (`Dal.rakkib`: ما لا إصلاحَ له عند المالك `Khalal.laHukm` لا حكم، والميّتُ ممتنع —
  `hukmTarkib`)، وكلُّ كلمةٍ مكتملةٌ دالًّا في صورة ابتدائها (`complete'` كما في `SentOK` المالك)، وحالةُ آخر كلّ كلمةٍ معربةٍ ما يطلبه
  موضعُها (`reqState` لخانات المالك، `Mulhaqat.halatAt` للملحقات) — إلّا ما لا تُقرأ حالتُه من الدالّ (`muqaddar`: حرفُ علّةٍ ساكنٌ تُقدَّر
  عليه الحالة `illaMuqaddara` بنصّ القطر L92–95، أو فتحةٌ في موضع الجرّ `laFathaJarr`، أو إعرابٌ بالحرف `laIrabBilHarf`؛ منذ 2026-10-20) فيُتجاوز ويُحكم عليه بالقراءة `hukmQiraa` «لا حكم»
  ثلاثيًّا يُضمّ فلا يُسقط امتناعًا قاطعًا في موضعٍ آخر —، والتنوينُ في الاسم المعرب نونٌ ساكنة بعد حركة الإعراب (قرار القارئ)
  فتُقرأ الحركةُ قبلَه (`halaIrab`) — **وهذان دون `SentOK` المالك: هو يفحص المبنيَّ أيضًا (فيطلب للماضي ضمّةً: `reqState 1 0 2`) ويقرأ
  آخرَ خليةٍ (`lastSt`) فيردّ «ذَهَبَ الْوَلَدُ» و«ذَهَبَ وَلَدٌ» كليهما**، معلَن؛ وقسمُ مدلول كلّ خانةٍ عند المالك (`Cat.kindOfMadlul`) قسمُ خانتها بدورها وأداة الإطار (فعلٌ لدور الفعل وللناسخ الفعليّ كان/ظنّ،
  حرفٌ للأداة في غيرهما وللجارّ، اسمٌ لسواهما — `qismDawr`؛ والملحقاتُ أسماء)؛ وموضوعُ الإسناد مدلولُ المسند إليه الظاهر (المبتدأُ وإلّا
  الفاعل)، ومحمولُه حقيقةُ مدلول المسند الظاهر بجنسه (الفعلُ قابليّة؛ الخبرُ خاصّةٌ أو فردٌ أو قابليّةٌ بوصفٍ مشتقّ؛ والمجرورُ في شبه
  الجملة علاقةٌ إليه — `jinsMahmul`)، ونسبةُ الإسناد نسبةُ خانة المسند بتعيين `Nisab.nisbaOf` على علاقة المالك `semOf` (الجسرُ بين
  التعيينين)، ووصلُ المدلول ثلاثيًّا. **وقف**: السلسلةُ المركَّبة إطارُ دالٍّ مرخَّص (ابتداءً ووصلًا ووقفًا)، والإسنادُ تامٌّ — أو تعلُّقٌ
  (إضافية) في شبه الجملة. **الترخيصُ والحكم** (م10: الحكمُ فوق الترخيص لا فيه): `tarkhis3` كلُّ ما سبق سوى وصل المدلول (والقراءةُ `qiraa` منه منذ
  2026-10-20، ولا تغيّر قيمتَه: يساوي نظيرَه على ca5ed3c لكلّ إطار — برهنه المراجعُ المستقلّ على 0f53900 و1f2aeb6 و982d98f في الجلسة، وأعاد البنّاءُ تشغيلَ برهانه على إيداع تصحيح المراجعة الخامسة بتكييف لمّتين ولمّةٍ جديدة `wbd_115` للمحمول `wawBadDamma`؛ ليس في المستودع)، و`hukm3` ثلاثيٌّ يضمّه إلى حكم الوضع — «لا حكم» خارجَ الحدّ، ويرثه من التركيب ومن القراءة ومن وصل المدلول؛ والحكمُ لا يُسقط ترخيصًا (`hukm_la_yusqit_tarkhis`:
  المرخَّصُ في الحدّ لا يكون ممتنعًا — مرخَّصٌ أو لا حكم؛ و`hukm3_murakhkhas`: المرخَّصُ حكمًا = ترخيصٌ في الحدّ مع حقيقة الوضع). **وما ردّه
  `itarOK` «لا حكم» بسببه** (2026-10-20؛ وكان ممتنعًا): قولُ المالك في LC11 من «سجل التزامات إغلاق الإخبار ثم الإنشاء» (مرفق المالك
  `CLOSURE_LEDGER_AR.md` على ca5ed3c، غيرُ مودَع): اختار خيارَ البنّاء «لا حكم بسببٍ مسمّى (موصى به)» لما ردّه «لعدم التمثيل»؛ وشمولُه كلَّ ما يردّه `itarOK` — لأنّ قانونه البوليّ لا يسمّي سببًا فلا يُميَّز عدمُ
  التمثيل من المنع — قراءةُ البنّاء (تعيينٌ معروض؛ §٣ «أسبابُ لا حكم»)، وكذلك تعميمُ «لكلّ لا حكم سببٌ مسمّى» (`laHukm_iff_sabab`).
  وما بقي معلَنًا هناك (`shahid_baqi`). وما ليس
  هنا (معلَن): قانونُ ابتداء الكلام بين الجمل (`Tarkib.discOK`)، والسماتُ فوق القسم (ومنها الزمنُ ماضيًا/مضارعًا/أمرًا: `Attr.1` لا
  يقابله شيءٌ في الكلمة ولا في المدلول البوليّ `tim`)، والمفاعيلُ الراسية على الفعل تتأخّر عن خانات المالك كلِّها (`yataakhkhar`).
  الاحتواء `itar3_yahtawi` على الترخيص (ومنه ترخيصُ آلة المالك `Msent` للسلسلة المركَّبة عبر `Dal.jumla_murakhkhasa`) و`itar3_yahtawi_hukm`
  على الحكم؛ الرقم `itar3_value`. الشواهد: «ذَهَبَ الْوَلَدُ»، «ذَهَبَ وَلَدٌ»، «فِي الدَّارِ»، «ذَهَبَ الْوَلَدُ مُسْرِعًا»، «كَانَ الْوَلَدُ ذَاهِبًا»، وشواهدُ الحدّ —
  بمدلولاتٍ مبنيّةٍ على نسق المالك (`insan`، `shams`): أمثلةٌ لا مودَع؛ ومعجمُ الأجناس وخواصّها وقابليّاتها مودَعٌ ينتظر.

  الوسم: مبرهن (الاستلزامات، `dal_waqf_kama_yuqra`، الاحتواء، الفكّ، ثلاثُ النِّسَب، ثلاثيّةُ الحكم، حدُّ الطبقة)، ومبرهن على الشاهد
  (decide/decide +kernel على الأمثلة والعدّ — ومنه الاستقلالُ `wasl_waqf_mustaqillan` و`wasl_ghayr_Fwasl`). وأسبابُ «لا حكم» (2026-10-20) بالمعيار الموحَّد (`Nizam/Asas.lean`): 6 لكلّ (`asbabHadd_nil`،
  `laHukm_iff_sabab`، `fiHadd_shurut`، `la_hukm_ma_radda_itar`، `la_tamthil_la_hukm`، `mumtani_itarOK`)، و2 تعريفيّتان (`ofBool_ne_laHukm`،
  `damm_laHukm`)، و4 على الشاهد (`shahid_asbab`، `shahid_hadd_asbab`، `shahid_qiraa`، `shahid_baqi`)؛ ومساعدتان خاصّتان: `all_and_bool`
  (لكلّ، بالاستقراء) و`ite_sabab_nil` (تعريفيّة). وتغيّر برهانُ `hukm3_murakhkhas` و`hukm_la_yusqit_tarkhis` و`itar3_yahtawi` و`itar3_yahtawi_hukm`
  دون نصّها عن ca5ed3c (و`fiHadd_shurut` و`laHukm_iff_sabab` جديدتان فيه، تغيّر برهانُهما بين إيداعات الفرع)؛
  ومعنى المبرهنات التي تفترض `fiHadd` أو تنتهي إليه تبعٌ لتعريفه الجديد (ما يردّه `itarOK` خارجَه). طفراتها P329–P332 وP335–P336 وP345–P358 وP361–P363 وP371–P373. موادُّ دستور الوكيل
  (AGENT_CONSTITUTION.md في Saleh1967/Alghanem — ليس في هذا المستودع؛ نصُّها من خلاصته في مهارة dustur-al-wakil): م10 «الحكمُ فوق
  الترخيص لا فيه»، م13 «الحكمُ ثلاثيٌّ … ولا يُسقط ترخيصًا … لا يُستنتج الامتناع من غياب الشاهد».
-/
import Dal.Jumla
import SLGE.MadlulAwwalan
import SLGE.Category
import Jisr.Mulhaqat
import Jisr.Nisab

set_option synthInstance.maxSize 8192
set_option synthInstance.maxHeartbeats 0
set_option maxRecDepth 100000
set_option autoImplicit false

namespace Jisr
namespace Utur
open SLGE SLGE.Law SLGE.Tarkib SLGE.Simat SLGE.Kull SLGE.Awwalan Dal

/-! ## ١. إطار الدال وحده -/

abbrev ItarDal := List NawMaqta

/-- نمطُ مقاطع السلسلة (خلاياها بأرقامها دون 116)؛ ولا نمطَ للفارغ. -/
def itarDal (l : List Nat) : Option ItarDal := if l.isEmpty then none else (qatta l).map (·.map nawMaqta)

/-- **ابتداء:** الانتقالُ الأوّل من الحالة 0 حيّ. -/
def ibtidaDal (l : List Nat) : Bool := match l with | a :: _ => δ 0 a != 96 | [] => false
/-- **وصل:** السلسلةُ غيرُ فارغة وانتقالاتُها كلُّها حيّة كما تُقرأ. -/
def waslDal (l : List Nat) : Bool := !l.isEmpty && run 0 l != 96
/-- **وقف:** `complete'` المالك — وقفيّةٌ بعد تسكين الآخر. -/
def waqfDal (l : List Nat) : Bool := complete' l

/-- إطارُ الدالّ المرخَّص: الأحكامُ الثلاثة. -/
def dalOK (l : List Nat) : Bool := ibtidaDal l && waslDal l && waqfDal l

/-- **ما يُوصَل ويُوقَف عليه بعد التسكين فحالتُه كما يُقرأ وقفيّة** (من أيّ حالة): بالاستقراء على السلسلة؛ والخليةُ الأخيرة إن كانت
متحرّكةً حيّةً فالحالةُ «بعد متحرّك» `1 + h` (المالك `mover_step`) وهي وقفيّة. -/
theorem waqf_kama_yuqra (l : List Nat) :
    ∀ q, run q l ≠ 96 → Fwaqf (run q (waqfForm l)) = true → Fwaqf (run q l) = true := by
  induction l with
  | nil => intro q _ h; simpa [waqfForm] using h
  | cons a l ih =>
    intro q hr hw
    cases l with
    | nil =>
      by_cases hv : a < 116 ∧ a % 4 < 3
      · simp only [run] at hr ⊢
        rw [mover_step q a hv.1 hv.2 hr]; simp only [Fwaqf, decide_eq_true_eq]; omega
      · simp only [waqfForm, hv, ite_false] at hw; exact hw
    | cons b l =>
      simp only [waqfForm, run] at hw hr ⊢
      exact ih (δ q a) hr hw

/-- **ما رخّصه إطارُ الدالّ فحالتُه كما يُقرأ وقفيّة** — وهو ما تطلبه مبرهنةُ المالك `jumla_murakhkhasa` للجملة. -/
theorem dal_waqf_kama_yuqra (l : List Nat) (h : dalOK l = true) : Fwaqf (run 0 l) = true := by
  unfold dalOK waslDal waqfDal complete' at h
  simp only [Bool.and_eq_true, bne_iff_ne, ne_eq] at h
  exact waqf_kama_yuqra l 0 h.1.2.2 h.2

/-- **الوصلُ يستلزم الابتداء:** ما مات انتقالُه الأوّل ماتت سلسلتُه (المالك `run_dead`). -/
theorem wasl_yastalzim_ibtida (l : List Nat) (h : waslDal l = true) : ibtidaDal l = true := by
  unfold waslDal at h
  cases l with
  | nil => simp at h
  | cons a l =>
    simp only [ibtidaDal, bne_iff_ne, ne_eq]
    intro hc
    simp [run, hc, run_dead] at h

/-- **والوقفُ يستلزم الابتداء:** التسكينُ لا يُحيي انتقالًا أوّلَ ميّتًا — الخليةُ الواحدة المتحرّكة تصير ساكنةً فلا يُبتدأ بها، وما
بعد خليةٍ ميّتةٍ ميّت. -/
theorem waqf_yastalzim_ibtida (l : List Nat) (h : waqfDal l = true) : ibtidaDal l = true := by
  unfold waqfDal complete' at h
  cases l with
  | nil => simp [waqfForm, run, Fwaqf] at h
  | cons a l =>
    simp only [ibtidaDal, bne_iff_ne, ne_eq]
    intro hc
    cases l with
    | nil =>
      by_cases hv : a < 116 ∧ a % 4 < 3
      · have hs : δ 0 (4 * (a / 4) + 3) = 96 := by
          have : ∀ b < 116, b % 4 = 3 → δ 0 b = 96 := by decide
          exact this _ (by omega) (by omega)
        simp [waqfForm, hv.1, hv.2, run, hs, Fwaqf] at h
      · simp [waqfForm, hv, run, hc, Fwaqf] at h
    | cons b l => simp [waqfForm, run, hc, run_dead, Fwaqf] at h

/-- **الوصلُ والوقفُ مستقلّان (على الشاهد):** «لَ» (خليةٌ واحدة) توصَل ولا يوقَف عليها؛ و«لَا» بألفٍ متحرّكةٍ آخرًا (8) يكتملها التسكينُ
(ألفُ مدٍّ بعد الفتحة) وتموت كما تُقرأ (الألفُ لا تتحرّك عند المالك). -/
theorem wasl_waqf_mustaqillan :
    waslDal [52] = true ∧ waqfDal [52] = false ∧ waqfDal [52, 8] = true ∧ waslDal [52, 8] = false := by decide

/-- **«الوصل» هنا غيرُ `Fwasl` المالك (قبولُ متحرّكٍ بعد الآخر):** «بِنْت» حيّةُ الانتقالات ووقفيّةٌ فيرخّصها الإطار، و`Fwasl` يردّها
إن وُصلت (المالك `bint`: «مرخَّصةٌ موقوفًا عليها، ممتنعةٌ إن وُصلت بمتحرّك»؛ حالتُها 35: ساكنان مُغلِقان). -/
theorem wasl_ghayr_Fwasl :
    waslDal [106, 59, 75] = true ∧ waqfDal [106, 59, 75] = true ∧ Fwasl (run 0 [106, 59, 75]) = false := by decide

/-- **لا يُبتدأ بساكن:** الخليةُ الساكنة أوّلًا تُميت الآلة (المالك `nec_vowel`)، فلا نمطَ (`qatta`) ولا ابتداءَ ولا إطار. -/
theorem la_itar_bisakin (a : Nat) (ha : a < 116) (hs : a % 4 = 3) (l : List Nat) :
    itarDal (a :: l) = none ∧ ibtidaDal (a :: l) = false ∧ dalOK (a :: l) = false := by
  have hd : δ 0 a = 96 := by
    have : ∀ b < 116, b % 4 = 3 → δ 0 b = 96 := by decide
    exact this a ha hs
  refine ⟨by simp [itarDal, qatta, qattaRaw, hs], by simp [ibtidaDal, hd], by simp [dalOK, ibtidaDal, hd]⟩

/-- **الإطارُ أضيقُ من `complete'` المالك بالألف المتحرّكة آخرًا:** على السلاسل من خليتين، ما اكتمل عنده ولم يرخّصه الإطارُ
آخرُه ألفٌ متحرّكة (8، 9، 10) — 84 سلسلة من 9,520 مكتملة. -/
theorem dal_vs_complete :
    (List.range 116).all (fun a => (List.range 116).all fun b =>
      !(complete' [a, b] && !dalOK [a, b]) || (b == 8 || b == 9 || b == 10)) = true ∧
    ((List.range 116).map fun a => ((List.range 116).filter fun b => complete' [a, b] && !dalOK [a, b]).length).sum = 84 ∧
    ((List.range 116).map fun a => ((List.range 116).filter fun b => complete' [a, b]).length).sum = 9520 := by decide +kernel

/-- وكلُّ ما رخّصه الإطارُ مكتملٌ عند المالك (بالتعريف: الوقفُ هو `complete'`). -/
theorem dal_yastalzim_complete (l : List Nat) (h : dalOK l = true) : complete' l = true := by
  unfold dalOK waqfDal at h; simp only [Bool.and_eq_true] at h; exact h.2

/-- **استنفادُ أطر الدالّ على الخلية والخليتين:** لا سلسلةَ من خليةٍ (المالك `nec_second`)؛ ومن خليتين الإطارُ والتقطيعُ سواء:
ما رخّصه الإطارُ له نمطٌ وما له نمطٌ رخّصه الإطار. -/
theorem itar_dal_istinfad_2 :
    ((List.range 116).filter fun a => dalOK [a]).length = 0 ∧
    (List.range 116).all (fun a => (List.range 116).all fun b => (itarDal [a, b]).isSome == dalOK [a, b]) = true := by
  decide +kernel

/-- **أنماطُ الخليتين:** كما تُقرأ CV·CV (7056) أو CVV (84) أو CVC (2296) ولا رابع — 9,436 سلسلةً يرخّصها الإطار. -/
theorem itar_dal_anmat_2 :
    (List.range 116).all (fun a => (List.range 116).all fun b =>
      match itarDal [a, b] with
      | none => true
      | some p => p == [.CV, .CV] || p == [.CVV] || p == [.CVC]) = true ∧
    ([[NawMaqta.CV, .CV], [.CVV], [.CVC]].map fun p =>
      ((List.range 116).map fun a => ((List.range 116).filter fun b => itarDal [a, b] == some p).length).sum) =
      [7056, 84, 2296] ∧ 7056 + 84 + 2296 = 9436 := by decide +kernel

/-- شواهدُ النمط: «كِتَاب» CV·CVVC، «بِنْت» CVCC، «ذَهَبَ» CV·CV·CV، «قَالَ» CVV·CV؛ والإطارُ يرخّص «ذَهَبَ» و«قَالَ» و«بِنْت» (وقفًا
بساكنين) ولا يرخّص ما أوّله ساكنٌ أو ألفٌ متحرّكة، ولا الفارغ؛ و«قَالَ» وقفًا CVVC. -/
theorem itar_dal_shawahid :
    itarDal [4 * 8 + 2, 4 * 18 + 0, 4 * 2 + 3, 4 * 26 + 3] = some [.CV, .CVVC] ∧
    itarDal [4 * 26 + 2, 4 * 14 + 3, 4 * 18 + 3] = some [.CVCC] ∧
    itarDal [92, 4, 104] = some [.CV, .CV, .CV] ∧ itarDal [28, 11, 52] = some [.CVV, .CV] ∧
    itarDal (waqfForm [28, 11, 52]) = some [.CVVC] ∧
    dalOK [92, 4, 104] = true ∧ dalOK [28, 11, 52] = true ∧ dalOK [4 * 26 + 2, 4 * 14 + 3, 4 * 18 + 3] = true ∧
    dalOK [11, 28] = false ∧ dalOK [8, 52] = false ∧ dalOK [] = false ∧ waslDal [] = false ∧ itarDal [] = none := by
  decide +kernel

/-! ## ٢. إطار المدلول وحده -/

/-- المحمول: من حقول مدلول المالك الأربعة (خاصّة، علاقة إلى مدلولٍ آخر، قابليّة، فرد). -/
inductive Mahmul
  | khassa (k : Nat) | alaqa (r ila : Nat) | qabiliyya (q : Nat) | fard (f : Nat)
deriving DecidableEq, Repr

structure ItarMadlul where
  mawdu : Madlul
  mahmul : Mahmul
  nisba : Nisab.Nisba
deriving DecidableEq, Repr

/-- الحكمُ الثلاثيّ: مرخَّص، أو لا حكم (غيابُ شاهدٍ لا امتناع)، أو ممتنع. -/
inductive Hukm | murakhkhas | laHukm | mumtani
deriving DecidableEq, Repr

/-- ضمُّ الأحكام: الممتنعُ يغلب، ثمّ لا حكم، ثمّ الترخيص. -/
def damm : Hukm → Hukm → Hukm
  | .mumtani, _ => .mumtani
  | _, .mumtani => .mumtani
  | .laHukm, _ => .laHukm
  | _, .laHukm => .laHukm
  | .murakhkhas, .murakhkhas => .murakhkhas

def ofBool (b : Bool) : Hukm := if b then .murakhkhas else .mumtani

theorem damm_murakhkhas (a b : Hukm) : damm a b = .murakhkhas ↔ a = .murakhkhas ∧ b = .murakhkhas := by
  cases a <;> cases b <;> simp [damm]

/-- **الضمُّ لا يخترع امتناعًا:** الممتنعُ من ممتنعٍ في أحد الطرفين لا غير — فلا يصير «لا حكم» ممتنعًا بالضمّ. -/
theorem damm_mumtani (a b : Hukm) : damm a b = .mumtani ↔ a = .mumtani ∨ b = .mumtani := by
  cases a <;> cases b <;> simp [damm]

theorem ofBool_murakhkhas (b : Bool) : ofBool b = .murakhkhas ↔ b = true := by cases b <;> simp [ofBool]

/-- **ابتداء** (صلاحيةُ المسند إليه): الموضوعُ معنًى في نفسه لا زمانَ بهيئته (المالك `Cat.roles`). -/
def ibtidaMadlul (u : ItarMadlul) : Bool := (SLGE.Cat.roles u.mawdu.ind u.mawdu.tim).1

/-- المحمولُ في حقول الموضوع (الوضع: «حقيقة»). -/
def fiHuqul (m : Madlul) : Mahmul → Bool
  | .khassa k => m.khawass.contains k
  | .alaqa r x => m.alaqat.contains (r, x)
  | .qabiliyya q => m.qabiliyyat.contains q
  | .fard f => m.afrad.contains f

/-- النِّسَبُ التي يحتملها المحمول (تعيينٌ معلَن): الخاصّةُ تُسند أو تقيّد، والقابليّةُ والفردُ يُسندان، والعلاقةُ إضافة. -/
def nisabMahmul : Mahmul → List Nisab.Nisba
  | .khassa _ => [.isnadiyya, .taqyidiyya]
  | .alaqa _ _ => [.idafiyya]
  | .qabiliyya _ => [.isnadiyya]
  | .fard _ => [.isnadiyya]

/-- **وصل** ثلاثيًّا: نسبةٌ لا يحتملها المحمول ← ممتنع؛ وإلّا فالمحمولُ في الحقول ← مرخَّص، وإلّا ← لا حكم. -/
def waslMadlul (u : ItarMadlul) : Hukm :=
  if !(nisabMahmul u.mahmul).contains u.nisba then .mumtani
  else if fiHuqul u.mawdu u.mahmul then .murakhkhas else .laHukm

/-- **وقف:** الإفادةُ بالإسناد (المالك `Category`: الكلامُ إسناد؛ وتعلُّقُ شبه الجملة بمسندٍ مقدَّر يُحكَم في الطبقة الثالثة حيث يُعرَف
نوعُ الإطار، لا هنا). -/
def waqfMadlul (u : ItarMadlul) : Bool := u.nisba == .isnadiyya

/-- القيدُ (تقييدٌ أو إضافة): ابتداءٌ ووصلٌ بلا وقف — جزءُ كلامٍ لا كلام. -/
def hukmQayd (u : ItarMadlul) : Hukm := damm (ofBool (ibtidaMadlul u)) (waslMadlul u)
/-- الإطارُ المدلوليّ التامّ: الأحكامُ الثلاثة. -/
def hukmMadlul (u : ItarMadlul) : Hukm := damm (hukmQayd u) (ofBool (waqfMadlul u))

/-- **لا يُبتدأ بحرف:** ما ليس معنًى في نفسه لا يصلح مسندًا إليه (المالك `Cat.roles`). -/
theorem harf_la_yubtada (u : ItarMadlul) (h : u.mawdu.ind = false) : ibtidaMadlul u = false := by
  simp [ibtidaMadlul, SLGE.Cat.roles, h]

/-- **ولا بفعل:** الزمانُ بهيئته لا يُسند إليه (المالك `Cat.roles`: الدورُ الأوّل `ind && !tim`). -/
theorem fil_la_yubtada (u : ItarMadlul) (h : u.mawdu.tim = true) : ibtidaMadlul u = false := by
  simp [ibtidaMadlul, SLGE.Cat.roles, h]

/-- **لكلّ محمولٍ نسبة؛ والإسنادُ لكلّ محمولٍ غيرِ العلاقة، والعلاقةُ إضافةٌ وحدها.** -/
theorem nisab_mahmul (m : Mahmul) :
    (nisabMahmul m) ≠ [] ∧
    ((nisabMahmul m).contains .isnadiyya ↔ (match m with | .alaqa _ _ => False | _ => True)) ∧
    ((nisabMahmul m).contains .idafiyya ↔ (match m with | .alaqa _ _ => True | _ => False)) := by
  cases m <;> simp [nisabMahmul]

/-- **الحكمُ ثلاثيٌّ لا يُسقط ترخيصًا ولا يخترع امتناعًا (م13):** الامتناعُ من النسبة وحدها، والترخيصُ من الحقول، ولا حكمَ إذا
وفقط إذا احتمل المحمولُ النسبةَ ولم يكن في الحقول — فغيابُ الشاهد ليس امتناعًا. -/
theorem wasl_thulathi (u : ItarMadlul) :
    (waslMadlul u = .mumtani ↔ (nisabMahmul u.mahmul).contains u.nisba = false) ∧
    (waslMadlul u = .murakhkhas ↔ (nisabMahmul u.mahmul).contains u.nisba = true ∧ fiHuqul u.mawdu u.mahmul = true) ∧
    (waslMadlul u = .laHukm ↔ (nisabMahmul u.mahmul).contains u.nisba = true ∧ fiHuqul u.mawdu u.mahmul = false) := by
  unfold waslMadlul
  cases hn : (nisabMahmul u.mahmul).contains u.nisba <;> cases hf : fiHuqul u.mawdu u.mahmul <;> simp

/-- مدلولاتٌ مبنيّة على نسق المالك (`insan`، `shams`): «الولد» (معنًى في نفسه، كلّيّ؛ خاصّتُه 21، وعلاقتُه 1 إلى «الدار» 30،
وقابليّتاه 10 و11)، «ذهب» (حدثٌ بزمانٍ بهيئته، حقيقتُه 10) و«طار» (12)، «الدار» (ذات، 30)، و«في» (أداةٌ لا معنى في نفسها). -/
def walad : Madlul := { haqiqa := 20, khawass := [21], alaqat := [(1, 30)], qabiliyyat := [10, 11], afrad := [1, 1] }
def dhahab : Madlul := { haqiqa := 10, khawass := [], alaqat := [], qabiliyyat := [], afrad := [], tim := true }
def tara : Madlul := { haqiqa := 12, khawass := [], alaqat := [], qabiliyyat := [], afrad := [], tim := true }
def dar : Madlul := { haqiqa := 30, khawass := [31], alaqat := [], qabiliyyat := [], afrad := [1] }
def fi : Madlul := { haqiqa := 40, khawass := [], alaqat := [], qabiliyyat := [], afrad := [], ind := false }

/-- **شواهد المدلول:** «الولدُ ذاهبٌ» (قابليّة 10) إسنادٌ مرخَّص؛ «الولدُ طائرٌ» (قابليّة 12 ليست في حقوله) لا حكم — لا ممتنع؛
«الولدُ الصغيرُ» (خاصّة 21) قيدٌ تقييديّ مرخَّص وليس كلامًا؛ «الولدُ في الدار» (علاقة 1 إلى 30) قيدٌ إضافيّ مرخَّص، وإسنادُ العلاقة
ممتنع؛ ولا يُسند إلى الفعل ولا إلى الحرف؛ و«الإنسانُ ناطقٌ» على مدلول المالك مرخَّص، و«الشمس» تصلح موضوعًا. -/
theorem madlul_shawahid :
    hukmMadlul ⟨walad, .qabiliyya 10, .isnadiyya⟩ = .murakhkhas ∧
    hukmMadlul ⟨walad, .qabiliyya 12, .isnadiyya⟩ = .laHukm ∧ waslMadlul ⟨walad, .qabiliyya 12, .isnadiyya⟩ = .laHukm ∧
    hukmQayd ⟨walad, .khassa 21, .taqyidiyya⟩ = .murakhkhas ∧ hukmMadlul ⟨walad, .khassa 21, .taqyidiyya⟩ = .mumtani ∧
    hukmQayd ⟨walad, .alaqa 1 30, .idafiyya⟩ = .murakhkhas ∧ waslMadlul ⟨walad, .alaqa 1 30, .isnadiyya⟩ = .mumtani ∧
    ibtidaMadlul ⟨dhahab, .khassa 1, .isnadiyya⟩ = false ∧ hukmMadlul ⟨fi, .khassa 1, .isnadiyya⟩ = .mumtani ∧
    hukmMadlul ⟨insan, .khassa 1, .isnadiyya⟩ = .murakhkhas ∧ ibtidaMadlul ⟨shams, .khassa 2, .isnadiyya⟩ = true := by decide

/-! ## ٣. إطار الدال والمدلول معًا -/

/-- الإطارُ الثلاثيّ: الإطارُ النحويّ الممدود، وكلماتُ خاناته الظاهرة بترتيبها (خاناتُ المالك الظاهرة ثمّ الملحقات؛ `Dal.Kalima`: خلايا
بلا همزة الوصل وعلامتُها)، ومدلولُ كلّ كلمة (تصوّرٌ: معلوماتٌ سابقة)، والإسنادُ الدلاليّ. -/
structure Itar3 where
  jisr : Mulhaqat.Itar
  kalimat : List Kalima
  maani : List Madlul
  isnad : ItarMadlul
deriving DecidableEq, Repr

def baseSlots (u : Itar3) : List Slot := u.jisr.ud.f.2.2
def nB (u : Itar3) : Nat := (baseSlots u).length
/-- خاناتُ المالك الظاهرة، ورتَبُ الملحقات الظاهرة في `ml`: كلُّها إلّا النائبَ (خانتُه خانةُ المالك) والعاملَ الاسميّ (صفةٌ على
خانةٍ اسمية لا كلمةٌ). -/
def zawahirBase (u : Itar3) : Nat := (overt (baseSlots u)).length
def zawahirMl (u : Itar3) : List Nat :=
  (List.range u.jisr.ml.length).filter fun j =>
    match u.jisr.ml[j]? with | some m => m.dawr != .naib && m.dawr != .amilIsmi | none => false
def zawahir (u : Itar3) : Nat := zawahirBase u + (zawahirMl u).length
/-- رتبةُ خانة المالك الظاهرة بين الظواهر. -/
def overtIdx (u : Itar3) (i : Nat) : Nat := (((baseSlots u).take i).filter (·.2.1 == 0)).length
/-- خانةُ المسند إليه: المبتدأُ (0) وإلّا الفاعلُ (3)؛ وخانةُ المسند: المجرورُ (6) في شبه الجملة، وإلّا الخبرُ (1) وإلّا الفعلُ (2). -/
def musnadIlayhIdx (u : Itar3) : Option Nat :=
  let rs := roles (baseSlots u)
  if rs.contains 0 then some (rs.idxOf 0) else if rs.contains 3 then some (rs.idxOf 3) else none
def musnadIdx (u : Itar3) : Option Nat :=
  let rs := roles (baseSlots u)
  if u.jisr.ud.f.1 == 2 then (if rs.contains 6 then some (rs.idxOf 6) else none)
  else if rs.contains 1 then some (rs.idxOf 1) else if rs.contains 2 then some (rs.idxOf 2) else none
def madlulOf (u : Itar3) (i : Nat) : Option Madlul :=
  if fillAt (baseSlots u) i == 0 then u.maani[overtIdx u i]? else none
def mahmulHaqiqa : Mahmul → Nat
  | .khassa k => k | .alaqa _ x => x | .qabiliyya q => q | .fard f => f
/-- جنسُ المحمول بخانة المسند: الفعلُ قابليّة؛ الخبرُ خاصّةٌ أو فردٌ أو قابليّة (بوصفٍ مشتقّ)؛ والمجرورُ علاقة. -/
def jinsMahmul : Mahmul → Nat → Bool
  | .qabiliyya _, 2 => true
  | .khassa _, 1 | .fard _, 1 | .qabiliyya _, 1 => true
  | .alaqa _ _, 6 => true
  | _, _ => false
/-- قسمُ الخانة عند المالك من دورها وأداة الإطار: الفعلُ لدور 2 وللأداة 7 إن كانت ناسخًا فعليًّا (كان 1، ظنّ 3: لها زمنٌ عند المالك
`Simat.slotAttrOK`)، والحرفُ للأداة في غيرهما وللجارّ 5، والاسمُ لسواهما. -/
def qismDawr (a r : Nat) : SLGE.Cat.Kind :=
  if r == 2 then .fil else if r == 7 then (if a == 1 || a == 3 then .fil else .harf) else if r == 5 then .harf else .ism
/-- حالةُ الإعراب في آخر الكلمة: التنوينُ في الاسم المعرب نونٌ ساكنة (59) بعد الحركة (قرارُ القارئ) فتُقرأ الحركةُ قبلَه. -/
def halaIrab (ismi : Bool) (w : List Nat) : Nat :=
  match w.reverse with
  | 59 :: a :: _ => if ismi && a % 4 < 3 then a % 4 else 3
  | a :: _ => a % 4
  | [] => 3

/-- **ابتداء:** الإطارُ النحويّ مرخَّص بلا إطارٍ ثانٍ، والكلماتُ بعدد الظواهر ولكلٍّ مدلول وخلاياها خلايا (دون حدّ الكلمة 116)،
وأوّلُ الكلمات يُبتدأ بها، والموضوعُ يصلح مسندًا إليه. -/
def ibtida3 (u : Itar3) : Bool :=
  Mulhaqat.itarOK u.jisr && u.jisr.thani.isNone && u.kalimat.length == zawahir u && u.maani.length == u.kalimat.length &&
  u.kalimat.all (fun w => w.khalaya.all (· < 116)) &&
  (match u.kalimat.head? with | some w => ibtidaDal (ibtida w) | none => false) && ibtidaMadlul u.isnad

/-- حالاتُ الملحق `j` من دوره (`Mulhaqat.halatAt` بوقودٍ يكفي سلسلةَ التوابع كلَّها؛ وفارغُها: لا حالةَ من الدور). -/
def halatMl (u : Itar3) (j : Nat) : List Nat :=
  Mulhaqat.halatAt u.jisr (u.jisr.ml.length + 1) (Mulhaqat.nBase u.jisr + j)

/-- آخرُ الخلايا حرفُ علّةٍ ساكن: الألف (`kh 2 3` = 11)، أو الياء (`kh 11 3` = 47)، أو الواو (`kh 28 3` = 115). والمنوَّنُ آخرُه
النونُ الساكنة (59) فليس منه. -/
def illaAkhir (w : List Nat) : Bool :=
  match w.reverse with
  | a :: _ => a == 11 || a == 47 || a == 115
  | [] => false

/-- آخرُ الخلايا فتحةٌ بلا تنوين. -/
def fathaAkhir (w : List Nat) : Bool :=
  match w.reverse with
  | a :: _ => a < 116 && a % 4 == 0
  | [] => false

/-- على الموضع `idx` (خانةٌ للمالك أو `nBase + j` للملحق) مضافٌ إليه راسٍ. -/
def mudafAlayh (u : Itar3) (idx : Nat) : Bool :=
  u.jisr.ml.any fun m => m.dawr == .mudafIlayhi && m.marsa == idx

/-- **حرفُ علّةٍ ساكنٌ آخرًا تُقدَّر عليه حالةٌ من `hs`** (القطر L92–95؛ `nom`: الخانةُ اسميّة، `al`: الكلمةُ بأل، `mudaf`: لها مضافٌ إليه ملحق):
- الألف: الرفعُ والنصبُ والجرّ — L92 «تقدر جميع الحركات في نحو "غلامي والفتى"»، وL93 «والضمة والفتحة في نحو "يخشى"».
- الياء: الرفع — L94 «والضمة في نحو "يدعو ويقضي"»؛ والجرُّ في الاسم — L92–93 «والكسرة في نحو "القاضي"»؛ والنصبُ في الاسم بلا أل
  ولا مضافٍ إليه ملحق وحده، لاحتمال المضاف إلى الياء «غلامي» (L92) — فالمنقوصُ بلا أل ولا مضافٍ إليه لا يُفرَّق منه بلا معجم، معلَن. أمّا
  الفعلُ والاسمُ بأل فالفتحةُ فيهما ظاهرةٌ نصبًا: L94–95 «وتظهر الفتحة في نحو "إن القاضي لن يقضي ولن يدعو"»؛ ومثلُهما الاسمُ بمضافٍ إليه
  ملحق بالاستدلال لا بالنصّ (شاهدُ السطر بأل وحده، وعلّةُ «غلامي» تزول مع المضاف إليه الملحق).
- الواو: الرفعُ في الفعل وحده — L94 «والضمة في نحو "يدعو …"»؛ والواوُ آخرَ الاسم علامةُ إعرابٍ لا محلُّ تقدير (L79 «فترفع بالواو»؛
  `laIrabBilHarf`).
- ولا تقديرَ في الجزم (L90–91 «والفعل المضارع المعتل الآخر فيجزم بحذف آخره»). -/
def illaMuqaddara (nom al mudaf : Bool) (hs : List Nat) (w : List Nat) : Bool :=
  illaAkhir w && !hs.contains 3 &&
  (match w.getLast? with
   | some 47 => hs.contains 1 || (nom && hs.contains 2) || (nom && !al && !mudaf && hs.contains 0)
   | some 115 => !nom && hs.contains 1
   | _ => true)

/-- لا حرفَ علّةٍ ساكنًا آخرًا تُقدَّر عليه الحالةُ المطلوبة. -/
def laIllaAkhir (nom : Bool) (hs : List Nat) (w : Kalima) (mudaf : Bool) : Bool := !illaMuqaddara nom w.al mudaf hs w.khalaya

/-- ولا فتحةَ آخرًا بلا تنوينٍ ولا أل ولا مضافٍ إليه ملحق حيث يُطلب الجرّ ولا تُقبل الفتحة: ممنوعٌ من الصرف محتمل (القطر L87 «وما لا ينصرف
فيجر بالفتحة»)، أو ضميرٌ متّصلٌ حركتُه فتحة («دَارِكَ»، «أَبِيكَ»: آخرُ الخلايا حركةُ الضمير لا حركةُ الإعراب) — لا يُفرَّق بينهما بلا معجم. -/
def laFathaJarr (_ : Bool) (hs : List Nat) (w : Kalima) (mudaf : Bool) : Bool :=
  !(hs.contains 2 && !hs.contains 0 && fathaAkhir w.khalaya && !w.al && !mudaf)

/-- آخرُ الخلايا واوٌ ساكنة (115) قبلها حرفٌ مضموم (`% 4 == 1`): صورةُ «أَبُوْ». -/
def wawBadDamma (w : List Nat) : Bool :=
  match w.reverse with
  | 115 :: d :: _ => d % 4 == 1
  | _ => false

/-- **ولا إعرابَ بالحرف لا يُجسَر:** اسمٌ مضافٌ إلى ملحقٍ آخرُه واوٌ ساكنةٌ بعد ضمّة (`wawBadDamma`) حيث يُطلب الرفع — صورةُ الأسماء الستّة،
القطر L78–79 «إلا الأسماء الستة، وهي أبوه وأخوه وحموها / وهنوه وفوه وذو مال، فترفع بالواو»، وشرطُها الإضافةُ بنصّ الألفية L79 «وشرط ذا
الاعراب إن يضفن لا ... للياكجا أخو أبيك ذا اعتلا» (وقيدُها «لا ... للياكجا» — أي لا إلى الياء — لا يقع هنا: المضافُ إليه كلمةٌ ملحقة، والمضافُ إلى الياء كلمةٌ واحدة
بلا ملحق). والإعرابُ بالحروف غيرُ مجسورٍ هنا، فـ«لا حكم» بسببٍ مسمّى (اختار المالك 2026-10-20، 16:46، خيارَ البنّاء «لا حكم بسببٍ مسمّى
(موصى به)»). واتّساعُ المحمول تعيينُ البنّاء، معلَن: لا يفحص أنّ الكلمةَ من الستّة، فكلُّ مضافٍ آخرُه واوٌ ساكنةٌ بعد ضمّةٍ رفعًا «لا حكم»
محتملًا — لا يُفرَّق من الستّة بلا معجم؛ وما قبل واوه غيرُ ضمّة («ذَهَبَ أَبَوْ الْوَلَدِ»، «ذَهَبَ دَلْوْ الْوَلَدِ») يُحكم عليه بالحالة فيمتنع
(`shahid_qiraa`). وبلا مضافٍ إليه، أو في غير الرفع، يبقى الحكمُ بالحالة. -/
def laIrabBilHarf (nom : Bool) (hs : List Nat) (w : Kalima) (mudaf : Bool) : Bool :=
  !(nom && mudaf && hs.contains 1 && wawBadDamma w.khalaya)

/-- **حالةٌ لا تُقرأ من الدالّ** في موضعٍ يطلب `hs`: حرفُ علّةٍ ساكنٌ تُقدَّر عليه، أو فتحةٌ في موضع الجرّ، أو إعرابٌ بالحرف. فلا يُقرأ ما فيه مخالفًا ولا موافقًا:
تتجاوزه قراءةُ الحالات (`waslBase`، `waslMl`)، وحكمُه «لا حكم» من `hukmQiraa` — فلا يُسقط امتناعًا قاطعًا في موضعٍ آخر. -/
def muqaddar (nom : Bool) (hs : List Nat) (w : Kalima) (mudaf : Bool) : Bool :=
  !laIllaAkhir nom hs w mudaf || !laFathaJarr nom hs w mudaf || !laIrabBilHarf nom hs w mudaf

/-- خاناتُ المالك الظاهرة: كلمتُها مكتملة، وحالتُها (إن كانت معربة) ما يطلبه موضعُها، وقسمُ مدلولها قسمُ دورها. -/
def waslBase (u : Itar3) : Bool :=
  (List.range (nB u)).all fun i =>
    fillAt (baseSlots u) i != 0 ||
    (let r := Mulhaqat.roleOf u.jisr.ud.f i
     let t := attrAt u.jisr.ud.ats i
     match u.kalimat[overtIdx u i]?, u.maani[overtIdx u i]? with
     | some w, some m =>
       complete' (ibtida w) &&
       (t.2.2.2 || (match reqState u.jisr.ud.f.1 u.jisr.ud.f.2.1 r with
                    | some h => halaIrab (isNom r) w.khalaya == h || muqaddar (isNom r) [h] w (mudafAlayh u i) | none => true)) &&
       SLGE.Cat.kindOfMadlul m == qismDawr u.jisr.ud.f.2.1 r
     | _, _ => false)

/-- الملحقاتُ الظاهرة: كلمتُها مكتملة، وحالتُها (إن كانت معربة) من حالات دورها، ومدلولُها اسم. -/
def waslMl (u : Itar3) : Bool :=
  (List.range (zawahirMl u).length).all fun k =>
    match (zawahirMl u)[k]? with
    | some j =>
      match u.jisr.ml[j]?, u.kalimat[zawahirBase u + k]?, u.maani[zawahirBase u + k]? with
      | some m, some w, some md =>
        complete' (ibtida w) &&
        (m.t.2.2.2 || (halatMl u j).isEmpty || (halatMl u j).contains (halaIrab true w.khalaya) ||
          muqaddar true (halatMl u j) w (mudafAlayh u (Mulhaqat.nBase u.jisr + j))) &&
        SLGE.Cat.kindOfMadlul md == .ism
      | _, _, _ => false
    | none => false

/-- كلُّ كلمةٍ تُطلب حالتُها من موضعها تستوفي `p` باسميّة موضعها وحالاتِه وبإضافتها: خاناتُ المالك الظاهرة غيرُ المبنيّة (`reqState`)، والملحقاتُ
الظاهرة غيرُ المبنيّة ذاتُ الحالات (`halatMl`) — المواضعُ نفسُها التي يفحصها `waslBase` و`waslMl`. -/
def kullMawdi (u : Itar3) (p : Bool → List Nat → Kalima → Bool → Bool) : Bool :=
  ((List.range (nB u)).all fun i =>
    fillAt (baseSlots u) i != 0 || (attrAt u.jisr.ud.ats i).2.2.2 ||
    (match reqState u.jisr.ud.f.1 u.jisr.ud.f.2.1 (Mulhaqat.roleOf u.jisr.ud.f i), u.kalimat[overtIdx u i]? with
     | some h, some w => p (isNom (Mulhaqat.roleOf u.jisr.ud.f i)) [h] w (mudafAlayh u i)
     | _, _ => true)) &&
  ((List.range (zawahirMl u).length).all fun k =>
    match (zawahirMl u)[k]? with
    | some j =>
      (match u.jisr.ml[j]?, u.kalimat[zawahirBase u + k]? with
       | some m, some w => m.t.2.2.2 || (halatMl u j).isEmpty || p true (halatMl u j) w (mudafAlayh u (Mulhaqat.nBase u.jisr + j))
       | _, _ => true)
    | none => true)

/-- **القراءة:** لا موضعَ حالتُه مقدَّرةٌ على حرف علّة، ولا فتحةَ في موضع الجرّ، ولا إعرابَ بالحرف. -/
def qiraa (u : Itar3) : Bool := kullMawdi u laIllaAkhir && kullMawdi u laFathaJarr && kullMawdi u laIrabBilHarf

/-- حكمُ القراءة ثلاثيًّا: ما لا يُقرأ «لا حكم» لا «ممتنع» (م13). -/
def hukmQiraa (u : Itar3) : Hukm := if qiraa u then .murakhkhas else .laHukm

/-- الجسرُ بين التعيينين: موضوعُ الإسناد مدلولُ المسند إليه الظاهر (ولا يخلو إطارٌ من مسندٍ إليه إلّا شبهُ الجملة: موضوعُه من
المقام)، ونسبتُه نسبةُ خانة المسند الظاهر بتعيين `Nisab.nisbaOf` على علاقة المالك `semOf`، ومحمولُه حقيقةُ مدلول المسند بجنسه. -/
def jisrMadlul (u : Itar3) : Bool :=
  (match musnadIlayhIdx u with
   | some i => (match madlulOf u i with | some m => m == u.isnad.mawdu | none => false)
   | none => u.jisr.ud.f.1 == 2) &&
  (match musnadIdx u with
   | some i =>
     Nisab.nisbaOf (semOf (Mulhaqat.roleOf u.jisr.ud.f i)) == some u.isnad.nisba &&
     (match madlulOf u i with
      | some m => mahmulHaqiqa u.isnad.mahmul == m.haqiqa && jinsMahmul u.isnad.mahmul (Mulhaqat.roleOf u.jisr.ud.f i)
      | none => false)
   | none => false)

/-- حكمُ التركيب ثلاثيًّا من خلل `Dal.rakkib`: همزةُ وصلٍ بعد حالةٍ ليس عند المالك إصلاحٌ لها «لا حكم» لا امتناع؛ والميّتةُ وما لا يوصَل
والفارغةُ ممتنعة. -/
def hukmTarkib (n : Natija) : Hukm :=
  match n.khalal with | none => .murakhkhas | some (.laHukm _) => .laHukm | some _ => .mumtani

/-- **وصل:** التركيبُ بإصلاح المالك (ثلاثيًّا)، وخاناتُ المالك وملحقاتُه بكلماتها وحالاتها وأقسامها، والجسرُ إلى المدلول، والقراءةُ
(ثلاثيًّا: ما لا يُقرأ «لا حكم» — 2026-10-20)، ووصلُ المدلول (ثلاثيًّا). -/
def wasl3 (u : Itar3) : Hukm :=
  damm (hukmTarkib (rakkib u.kalimat))
    (damm (ofBool (waslBase u && waslMl u && jisrMadlul u)) (damm (hukmQiraa u) (waslMadlul u.isnad)))

/-- **وقف:** السلسلةُ المركَّبة إطارُ دالٍّ مرخَّص، والإسنادُ تامٌّ — أو تعلُّقٌ (إضافية) في شبه الجملة (المالك `Category`). -/
def waqf3 (u : Itar3) : Bool :=
  dalOK (rakkib u.kalimat).silsila &&
  (if u.jisr.ud.f.1 == 2 then u.isnad.nisba == .idafiyya else waqfMadlul u.isnad)

/-- آخرُ خانةٍ ظاهرة في إطار المالك. -/
def akhirZahir (u : Itar3) : Option Nat := ((List.range (nB u)).filter fun i => fillAt (baseSlots u) i == 0).getLast?

/-- الملحقاتُ التي تتأخّر عن خانات المالك كلِّها أيًّا كان مرساها (المفاعيلُ على الفعل والحالُ على صاحبها)، فيصيب ترتيبَ النطق وضعُها
بعدها؛ وما سواها (التوابعُ والمضافُ إليه والتمييزُ والمعدود) يلي مرساه فلا يُقبل إلّا على آخر الظواهر أو على ملحق. -/
def yataakhkhar : Mulhaqat.Dawr → Bool
  | .mutlaq | .lahu | .fihi | .maahu | .hal => true
  | _ => false

/-- **الحدُّ المعلَن (أمضاه المالك 2026-10-16):** ما يحكم فيه الإطارُ الثلاثيّ، وما خرج عنه «لا حكم» لا «ممتنع»: لا إطارَ ثانٍ (التنازع)؛ ولا ملحقَ متقدّمًا
(`qabl`) ولا عاملَ اسميًّا (معمولاتُه إطارٌ فرعيّ بلا كلماتٍ هنا) ولا نائبَ مجرورًا (`naibDal 2` يخالف `reqState`)؛ وكلُّ ملحقٍ إمّا
متأخّرٌ بدوره (`yataakhkhar`) وإمّا راسٍ على آخر خانةٍ ظاهرة أو على ملحق — فترتيبُ الكلمات (خانات المالك ثمّ الملحقات بترتيبها) ترتيبُ
النطق؛ والمسندُ والمسندُ إليه ظاهران (المستترُ والمقدَّرُ والضميرُ المتّصل — ملءُ المالك 1 — إحالةٌ في `Maqam` غيرُ مجسورة هنا) أو شبهُ
الجملة بلا مسندٍ إليه؛ والفعلُ المعربُ الظاهر في الفعلية وحدها (في غيرها لا يعيّن إطارُ المالك حالتَه: `reqState … none`)؛ والأسماءُ
المعربة مفردةٌ (`n = 0`: الإعرابُ بالحركة على الخلية الأخيرة؛ المثنّى والجموعُ بالحروف غيرُ مجسورة — والأسماءُ الستّة (القطر L78) والمنقوصُ والمقصور
لا يُميَّزون بلا معجم: فجوةٌ معلَنة). -/
def haddMuallan (u : Itar3) : Bool :=
  u.jisr.thani.isNone &&
  u.jisr.ml.all (fun m => !m.qabl && m.dawr != .amilIsmi && !(m.dawr == .naib && m.naw == 2) &&
    (yataakhkhar m.dawr || some m.marsa == akhirZahir u || m.marsa ≥ nB u) && (m.t.2.2.2 || m.t.2.2.1.2.2 == 0)) &&
  (match musnadIdx u with | some i => fillAt (baseSlots u) i == 0 | none => false) &&
  (match musnadIlayhIdx u with | some i => fillAt (baseSlots u) i == 0 | none => u.jisr.ud.f.1 == 2) &&
  (List.range (nB u)).all (fun i =>
    fillAt (baseSlots u) i != 0 || (attrAt u.jisr.ud.ats i).2.2.2 ||
    (if Mulhaqat.roleOf u.jisr.ud.f i == 2 then u.jisr.ud.f.1 == 1
     else !isNom (Mulhaqat.roleOf u.jisr.ud.f i) || (attrAt u.jisr.ud.ats i).2.2.1.2.2 == 0))

/-! ### أسبابُ «لا حكم» المسمّاة (2026-10-20)

**قولُ المالك** في الجلسة (13:01 بتوقيت عمّان)، جوابًا عن LC11 («فصل عدم التمثيل عن الامتناع اللغوي») من «سجل التزامات إغلاق الإخبار ثم
الإنشاء» (مرفق المالك `CLOSURE_LEDGER_AR.md` على ca5ed3c، غيرُ مودَع): سُئل «ما ردّه إطارُ المالك itarOK لعدم التمثيل، أيبقى «ممتنعًا» كما
أمضيتَ في 2026-10-16، أم يصير «لا حكم» بسببٍ تقنيّ مسمّى؟» فاختار خيارَ البنّاء: «لا حكم بسببٍ مسمّى (موصى به)». وما سواه هنا قراءةُ البنّاء، معروضةً:

- **الشمول (يحتاج إمضاءك):** قانونُ المالك البوليّ (`uK`/`uOK`) وقواعدُ الملحقات (`Mulhaqat.itarOK`) لا تسمّي سببَ الردّ، وفيما تردّه
  عدمُ تمثيلٍ لا منعٌ بنصّ: الإطارُ خارج `framesL`، وتوكيدُ الفعل لفظيًّا («أتاك أتاك»، القطر L387)، وضميرُ المتكلّم في خانةٍ ظاهرة،
  والمفرَّغُ بعد «هل»، ومسوّغاتُ النكرة خارج رموزها، والمعدودُ فوق المئة (وجدها المراجعُ المستقلّ). فلا يُميَّز عدمُ التمثيل من المنع
  بالبوليّ وحده، وبم13 لا امتناعَ بلا مانعٍ مسمّى: **فكلُّ ما يردّه `itarOK` «لا حكم»** — `laTamthil` إن كان الإطارُ خارج `framesL`،
  وإلّا `itarYarudd`. فيصير «لا حكم» ما ردّه قانونٌ بنصٍّ لم يُسمَّ مانعُه (كتوكيد النكرة توكيدًا معنويًّا)؛ وإرجاعُه ممتنعًا بمانعٍ مسمّى
  عملُ م3 الباقي. وهذا يعكس جزءًا من إعلان البنّاء على ca5ed3c في رأس هذا الملفّ (س66 هناك: «فممتنعٌ هنا ولو كان لعدم التمثيل»)،
  لا من قائمة ما أمضيتَه 2026-10-16 (`CLAUDE.md:88` على ca5ed3c) — فقولي في السؤال «كما أمضيتَ» لم يكن مسنودًا.
- **التعميم:** «لكلّ «لا حكم» سببٌ مسمّى» على الطبقة كلّها (`laHukm_iff_sabab`) قراءتي لقرارٍ كان عن LC11.
- **الحدّ:** الحدُّ المعلَن (`haddMuallan`) بنصّه لم يتغيّر؛ وأسبابُ الخروج عنه عشرةٌ مفصّلة (`asbabHadd`) تطابقه بلا احتياط
  (`asbabHadd_nil`، برهانُ المراجع المستقلّ)، ولكلٍّ منها شاهد (`shahid_hadd_asbab`).
- **القراءة:** ما لا تُقرأ حالتُه من الدالّ لا يُقرأ مخالفًا ولا موافقًا، بل «لا حكم» يُضمّ في الوصل (`hukmQiraa`)، فيغلبه امتناعٌ قاطعٌ في
  موضعٍ آخر (`shahid_qiraa`):
  - حرفُ علّةٍ ساكنٌ آخرًا تُقدَّر عليه الحالةُ المطلوبة (`illaMuqaddara`، بنصّ القطر L92–95): الألفُ في غير الجزم؛ والياءُ رفعًا، وجرًّا في
    الاسم، ونصبًا في الاسم بلا أل ولا مضافٍ إليه ملحق وحده (لاحتمال «غلامي» L92؛ فالمنقوصُ بلا أل ولا مضافٍ إليه لا يُفرَّق منه بلا معجم،
    معلَن)؛ والواوُ رفعًا في الفعل وحده. والفتحةُ ظاهرةٌ نصبًا في الفعل وفي الاسم بأل — «وتظهر الفتحة في نحو "إن القاضي لن يقضي ولن
    يدعو"» (L94–95) — وفي الاسم بمضافٍ إليه ملحق بالاستدلال، فـ«لَنْ يَدْعُوْ» و«لَنْ يَقْضِيْ» و«ضَرَبَ الْوَلَدُ الْقَاضِيْ» و«ضَرَبَ الْوَلَدُ
    قَاضِيْ الْوَلَدِ» ممتنعة؛ والواوُ آخرَ الاسم علامةُ إعرابٍ لا محلُّ تقدير (L79 «فترفع بالواو»).
  - وفتحةٌ آخرًا بلا تنوينٍ ولا أل ولا مضافٍ إليه ملحق حيث يُطلب الجرّ ولا تُقبل الفتحة (`laFathaJarr`): ممنوعٌ من الصرف محتمل
    (كـ`JisrDal.mamnu_fatha`؛ ومع أل أو الإضافة جرُّه الكسرة بنصّ القطر L87–88، فالفتحةُ هناك ممتنعة)، أو ضميرٌ متّصلٌ حركتُه فتحة
    («فِي دَارِكَ»، «فِي أَبِيكَ»؛ و«فِي أَبُوكَ» — خطأٌ بنصّ L79 «وتجر بالياء» — «لا حكم» كذلك: يُقرأ آخرُ الخلايا لا ما قبل الضمير).
  - وإعرابٌ بالحرف (`laIrabBilHarf`؛ اخترتَ 16:46 خيارَ البنّاء «لا حكم بسببٍ مسمّى (موصى به)»): اسمٌ له مضافٌ إليه ملحق آخرُه واوٌ ساكنةٌ
    بعد ضمّة رفعًا — «ذَهَبَ أَبُو الْوَلَدِ» لا حكم (القطر L79 «فترفع بالواو»، وشرطُ الإضافة الألفية L79 «وشرط ذا الاعراب إن يضفن»)؛ ولا
    يُفرَّق من الستّة بلا معجم (اتّساعٌ معلَن، تعييني)؛ وما قبل واوه غيرُ ضمّة يُحكم عليه بالحالة: «ذَهَبَ أَبَوْ الْوَلَدِ» و«ذَهَبَ دَلْوْ الْوَلَدِ»
    ممتنعان؛ وفي غير الرفع كذلك: «ضَرَبَ الْوَلَدُ أَبُو الْوَلَدِ» ممتنع (L79 «وتنصب بالألف»).

**وما بقي** (معلَن؛ `shahid_baqi`، وكلُّه كما كان على ca5ed3c): «فِي أَفْضَلِ» (ممنوعٌ مجرورٌ بالكسرة) مرخَّص — الممنوعُ لا يُعرف بلا معجم؛
والمقصورُ والمنقوصُ المنوَّنان («ذَهَبَ فَتًى»، «ذَهَبَ قَاضٍ») ممتنعان — يُقرأ ما قبل التنوين؛ والاسمُ بضميرٍ متّصل يُقرأ آخرُ خليّته — حركةُ
الضمير — حركةَ إعراب: في الجرّ بفتحةٍ «لا حكم» (`fathaJarr`)، وفي الرفع والنصب يُقبل الخطأُ إذا وافقت حركةُ الضمير الحالةَ («ذَهَبَ أَبَاهُ»،
«ضَرَبَ الْوَلَدُ أَبُوكَ» L79، «ضَرَبَ الْوَلَدُ دَارُكَ» L77) ويُردّ الصوابُ إذا خالفتها («ضَرَبَ الْوَلَدُ أَبَاهُ»، «ذَهَبَ دَارُكَ») — الضميرُ المتّصل لا يُفصل
بلا معجم؛ والمضارعُ المعتلّ مجزومًا بإثبات حرف العلّة («لَمْ يَدْعُو») مرخَّص، و«لَمْ يَغْزُ»/«لَمْ يَخْشَ»/«لَمْ يَرْمِ» (القطر L91
«فيجزم بحذف آخره») ممتنعة — مقلوبٌ على شاهد القطر، والبابُ `mudariMutall` من المعجم (اقتراحُ سببٍ «لا حكم» للمجزوم المنتهي بحركة أو بحرف
علّةٍ ساكن معروضٌ عليك)؛ والتوكيدُ اللفظيّ والبدلُ بلا فحصٍ للّفظ ولا للعلاقة («ذَهَبَ الْوَلَدُ الدَّارُ»: LC08، LC09؛ بـ #eval في الجلسة)؛
و«ممتنع» هنا بلا سببٍ مسمّى (`Hukm` لا `Nizam.Asas.Hukm`: م3). -/

/-- أسبابُ «لا حكم» في الطبقة الثالثة: عشرةٌ من الحدّ المعلَن، واثنان لما يردّه `itarOK`، وخمسةٌ من داخل الحدّ (التركيب، والقراءةُ
بأسبابها الثلاثة، ووصلُ المدلول) — سبعة عشر. -/
inductive SababLaHukm
  /-- إطارٌ ثانٍ (التنازع). -/
  | itarThani
  /-- ملحقٌ متقدّم (`qabl`). -/
  | mulhaqMutaqaddim
  /-- عاملٌ اسميّ: معمولاتُه إطارٌ فرعيّ بلا كلماتٍ هنا. -/
  | amilIsmi
  /-- نائبٌ مجرور (`naibDal 2` يخالف `reqState`). -/
  | naibMajrur
  /-- ملحقٌ لا يتأخّر بدوره ولا يرسو على آخر الظواهر ولا على ملحق: ترتيبُ الكلمات غيرُ ترتيب النطق. -/
  | mawdiNutq
  /-- ملحقٌ معربٌ غيرُ مفرد. -/
  | mulhaqGhayrMufrad
  /-- المسندُ غيرُ ظاهر. -/
  | musnadGhayrZahir
  /-- المسندُ إليه غيرُ ظاهر (إحالةٌ في `Maqam`)، في غير شبه الجملة. -/
  | musnadIlayhGhayrZahir
  /-- فعلٌ معربٌ ظاهرٌ في غير الفعلية (لا يعيّن إطارُ المالك حالتَه). -/
  | filMurabKharij
  /-- اسمٌ معربٌ ظاهرٌ غيرُ مفرد (المثنّى والجموعُ بالحروف غيرُ مجسورة). -/
  | ismGhayrMufrad
  /-- الإطارُ ليس في جدول أطر المالك `framesL`: عدمُ تمثيلٍ (LC11). -/
  | laTamthil
  /-- قانونُ المالك البوليّ أو قواعدُ الملحقات تردّ الإطار ولا تسمّي سببًا. -/
  | itarYarudd
  /-- حرفُ علّةٍ ساكنٌ آخرَ كلمةٍ تُقدَّر عليه حالتُها المطلوبة (`illaMuqaddara`): لا تُقرأ من الدالّ بلا معجم. -/
  | illaAkhir
  /-- فتحةٌ آخرًا بلا تنوينٍ ولا أل ولا مضافٍ إليه ملحق حيث يُطلب الجرّ ولا تُقبل الفتحة (`laFathaJarr`): ممنوعٌ من الصرف محتمل، أو
  ضميرٌ متّصلٌ حركتُه فتحة — والفرقُ من المعجم. -/
  | fathaJarr
  /-- اسمٌ مضافٌ آخرُه واوٌ ساكنةٌ بعد ضمّة حيث يُطلب الرفع (`laIrabBilHarf`): إعرابٌ بالحرف بصورة الأسماء الستّة غيرُ مجسور — ولا يُفرَّق
  منها بلا معجم. -/
  | irabBilHarf
  /-- همزةُ وصلٍ بعد حالةٍ لا إصلاحَ لها عند المالك (`Khalal.laHukm` في `Dal.rakkib`). -/
  | tarkib
  /-- المحمولُ يحتمل النسبةَ وليس في حقول الموضوع: غيابُ الشاهد (`wasl_thulathi`). -/
  | madlul
deriving DecidableEq, Repr

/-- أسبابُ الخروج عن الحدّ المعلَن مفصّلةً، بشروطه بأعيانها مفرّقةً (ولا سببَ إذا وفقط إذا استوفاه: `asbabHadd_nil`). -/
def asbabHadd (u : Itar3) : List SababLaHukm :=
  (if u.jisr.thani.isNone then [] else [.itarThani]) ++
  (if u.jisr.ml.all (fun m => !m.qabl) then [] else [.mulhaqMutaqaddim]) ++
  (if u.jisr.ml.all (fun m => m.dawr != .amilIsmi) then [] else [.amilIsmi]) ++
  (if u.jisr.ml.all (fun m => !(m.dawr == .naib && m.naw == 2)) then [] else [.naibMajrur]) ++
  (if u.jisr.ml.all (fun m => yataakhkhar m.dawr || some m.marsa == akhirZahir u || m.marsa ≥ nB u) then []
   else [.mawdiNutq]) ++
  (if u.jisr.ml.all (fun m => m.t.2.2.2 || m.t.2.2.1.2.2 == 0) then [] else [.mulhaqGhayrMufrad]) ++
  (if (match musnadIdx u with | some i => fillAt (baseSlots u) i == 0 | none => false) then [] else [.musnadGhayrZahir]) ++
  (if (match musnadIlayhIdx u with | some i => fillAt (baseSlots u) i == 0 | none => u.jisr.ud.f.1 == 2) then []
   else [.musnadIlayhGhayrZahir]) ++
  (if (List.range (nB u)).all (fun i => fillAt (baseSlots u) i != 0 || (attrAt u.jisr.ud.ats i).2.2.2 ||
        Mulhaqat.roleOf u.jisr.ud.f i != 2 || u.jisr.ud.f.1 == 1) then [] else [.filMurabKharij]) ++
  (if (List.range (nB u)).all (fun i => fillAt (baseSlots u) i != 0 || (attrAt u.jisr.ud.ats i).2.2.2 ||
        Mulhaqat.roleOf u.jisr.ud.f i == 2 || !isNom (Mulhaqat.roleOf u.jisr.ud.f i) ||
        (attrAt u.jisr.ud.ats i).2.2.1.2.2 == 0) then [] else [.ismGhayrMufrad])

/-- أسبابُ الخروج عن الحدّ، بترتيبٍ ثابت. -/
def asbabKharij (u : Itar3) : List SababLaHukm :=
  asbabHadd u ++
  (if Mulhaqat.itarOK u.jisr then [] else if framesL.contains u.jisr.ud.f then [.itarYarudd] else [.laTamthil])

/-- **حدُّ الطبقة:** ما يحكم فيه الإطارُ الثلاثيّ — لا سببَ للخروج عنه. وما خرج عنه «لا حكم» لا «ممتنع» (`kharij_alhadd`). -/
def fiHadd (u : Itar3) : Bool := (asbabKharij u).isEmpty

/-- الإطارُ الثلاثيّ: حكمُه ثلاثيٌّ — «لا حكم» خارجَ الحدّ، ويرث «لا حكم» من التركيب ومن القراءة ومن وصل المدلول. -/
def hukm3 (u : Itar3) : Hukm :=
  if fiHadd u then damm (ofBool (ibtida3 u)) (damm (wasl3 u) (ofBool (waqf3 u))) else .laHukm

theorem ibtida3_of_hukm (u : Itar3) (h : hukm3 u ≠ .mumtani) (hf : fiHadd u = true) : ibtida3 u = true := by
  unfold hukm3 at h; simp only [hf, ite_true] at h
  cases hb : ibtida3 u
  · rw [hb] at h; exact absurd ((damm_mumtani _ _).2 (Or.inl rfl)) h
  · rfl

/-- **الترخيصُ دون حكم الوضع** (م10: الحكمُ فوق الترخيص لا فيه): الابتداءُ، والتركيبُ بلا خلل، وخاناتُ المالك وملحقاتُه، والجسرُ،
والوقف — كلُّ ما في الإطار سوى `waslMadlul`. -/
def tarkhis3 (u : Itar3) : Bool :=
  ibtida3 u && (rakkib u.kalimat).khalal.isNone && waslBase u && waslMl u && jisrMadlul u && waqf3 u && qiraa u

theorem hukmTarkib_murakhkhas (n : Natija) : hukmTarkib n = .murakhkhas ↔ n.khalal.isNone = true := by
  unfold hukmTarkib
  cases h : n.khalal with
  | none => simp
  | some k => cases k <;> simp

/-- **الحكمُ المرخَّص = الترخيصُ في الحدّ مع حقيقة الوضع.** -/
theorem hukm3_murakhkhas (u : Itar3) :
    hukm3 u = .murakhkhas ↔ fiHadd u = true ∧ tarkhis3 u = true ∧ waslMadlul u.isnad = .murakhkhas := by
  unfold hukm3 wasl3 tarkhis3 hukmTarkib hukmQiraa
  cases fiHadd u <;> cases ibtida3 u <;> cases waslBase u <;> cases waslMl u <;> cases jisrMadlul u <;> cases waqf3 u <;>
    cases qiraa u <;> cases waslMadlul u.isnad <;>
    (cases hk : (rakkib u.kalimat).khalal with
      | none => simp [damm, ofBool]
      | some k => cases k <;> simp [damm, ofBool])

/-- **الحكمُ لا يُسقط ترخيصًا (م13):** ما رُخِّص في الحدّ، ونسبتُه ممّا يحتمله محمولُه، لا يصير ممتنعًا بحكم الوضع — مرخَّصٌ إن كان
المحمولُ في حقول الموضوع، وإلّا لا حكم؛ فالامتناعُ من الترخيص (الدالّ والنحو والجسر) أو من النسبة، لا من غياب الشاهد. -/
theorem hukm_la_yusqit_tarkhis (u : Itar3) (hf : fiHadd u = true) (ht : tarkhis3 u = true)
    (hn : (nisabMahmul u.isnad.mahmul).contains u.isnad.nisba = true) : hukm3 u ≠ .mumtani := by
  unfold hukm3; simp only [hf, ite_true]
  unfold tarkhis3 at ht; simp only [Bool.and_eq_true] at ht
  obtain ⟨⟨⟨⟨⟨⟨hi, hk⟩, hb⟩, hm⟩, hj⟩, hq⟩, hr⟩ := ht
  have hT : hukmTarkib (rakkib u.kalimat) = .murakhkhas := (hukmTarkib_murakhkhas _).2 hk
  have hW : waslMadlul u.isnad ≠ .mumtani := fun hc => by
    have h0 := (wasl_thulathi u.isnad).1.1 hc; rw [h0] at hn; exact Bool.false_ne_true hn
  unfold wasl3 hukmQiraa; rw [hi, hT, hb, hm, hj, hq, hr]
  cases hw : waslMadlul u.isnad
  · decide
  · decide
  · exact absurd hw hW

theorem fiHadd_of_hukm (u : Itar3) (h : hukm3 u ≠ .laHukm) : fiHadd u = true := by
  unfold hukm3 at h
  cases hf : fiHadd u
  · rw [hf] at h; exact absurd rfl h
  · rfl

/-- **الحكمُ خارجَ الحدّ «لا حكم» لا «ممتنع»** — الغيابُ عن الطبقة ليس امتناعًا (م13). -/
theorem kharij_alhadd (u : Itar3) (h : fiHadd u = false) : hukm3 u = .laHukm := by
  unfold hukm3; rw [h]; rfl

/-- أسبابُ «لا حكم» من داخل الحدّ: التركيبُ، والقراءةُ (حرفُ العلّة المقدَّر، والفتحةُ في موضع الجرّ، والإعرابُ بالحرف)، ووصلُ المدلول. -/
def asbabDakhil (u : Itar3) : List SababLaHukm :=
  (if hukmTarkib (rakkib u.kalimat) == .laHukm then [.tarkib] else []) ++
  (if kullMawdi u laIllaAkhir then [] else [.illaAkhir]) ++
  (if kullMawdi u laFathaJarr then [] else [.fathaJarr]) ++
  (if kullMawdi u laIrabBilHarf then [] else [.irabBilHarf]) ++
  (if waslMadlul u.isnad == .laHukm then [.madlul] else [])

/-- **أسبابُ «لا حكم»** للإطار الثلاثيّ إن كان حكمُه «لا حكم»: أسبابُ الخروج إن خرج عن الحدّ، وإلّا أسبابُ داخله؛ ولغيره لا شيء. -/
def asbabLaHukm (u : Itar3) : List SababLaHukm :=
  if hukm3 u = .laHukm then (if fiHadd u then asbabDakhil u else asbabKharij u) else []

theorem ofBool_ne_laHukm (b : Bool) : ofBool b ≠ .laHukm := by cases b <;> simp [ofBool]

/-- **الضمُّ لا يخترع «لا حكم»:** لا حكمَ من الضمّ إلّا من «لا حكم» في أحد الطرفين. -/
theorem damm_laHukm (a b : Hukm) (h : damm a b = .laHukm) : a = .laHukm ∨ b = .laHukm := by
  cases a <;> cases b <;> simp_all [damm]

private theorem all_and_bool {α} (l : List α) (p q : α → Bool) : l.all (fun x => p x && q x) = (l.all p && l.all q) := by
  induction l with
  | nil => rfl
  | cons a t ih => simp only [List.all_cons, ih]; cases p a <;> cases q a <;> simp

private theorem ite_sabab_nil (c : Bool) (s : SababLaHukm) : ((if c = true then ([] : List SababLaHukm) else [s]) = []) = (c = true) := by
  cases c <;> simp

/-- **التفصيلُ يطابق الحدَّ المعلَن:** لا سببَ من الأسباب العشرة إذا وفقط إذا استوفى الإطارُ الحدَّ الذي أمضاه المالك 2026-10-16
(`haddMuallan` بنصّه) — فلكلّ خروجٍ عنه سببٌ من العشرة، ولا احتياطَ بلا اسم. (برهانُ المراجع المستقلّ في مراجعته، بتصرّفٍ في الأسماء.) -/
theorem asbabHadd_nil (u : Itar3) : asbabHadd u = [] ↔ haddMuallan u = true := by
  unfold asbabHadd haddMuallan
  have hr : ∀ i, (fillAt (baseSlots u) i != 0 || (attrAt u.jisr.ud.ats i).2.2.2 ||
      (if Mulhaqat.roleOf u.jisr.ud.f i == 2 then u.jisr.ud.f.1 == 1
       else !isNom (Mulhaqat.roleOf u.jisr.ud.f i) || (attrAt u.jisr.ud.ats i).2.2.1.2.2 == 0)) =
      ((fillAt (baseSlots u) i != 0 || (attrAt u.jisr.ud.ats i).2.2.2 ||
        Mulhaqat.roleOf u.jisr.ud.f i != 2 || u.jisr.ud.f.1 == 1) &&
       (fillAt (baseSlots u) i != 0 || (attrAt u.jisr.ud.ats i).2.2.2 ||
        Mulhaqat.roleOf u.jisr.ud.f i == 2 || !isNom (Mulhaqat.roleOf u.jisr.ud.f i) ||
        (attrAt u.jisr.ud.ats i).2.2.1.2.2 == 0)) := by
    intro i
    generalize Mulhaqat.roleOf u.jisr.ud.f i = r
    cases (fillAt (baseSlots u) i != 0) <;> cases (attrAt u.jisr.ud.ats i).2.2.2 <;>
      by_cases h2 : r = 2
    all_goals first
      | (subst h2; simp)
      | (have e1 : (r == 2) = false := by simp [h2]
         have e2 : (r != 2) = true := by simp [h2]
         simp [e1, e2])
  simp only [hr, all_and_bool, List.append_eq_nil_iff, ite_sabab_nil, Bool.and_eq_true]
  simp only [and_assoc]

/-- **لكلّ «لا حكم» سببٌ مسمّى، ولا أسبابَ لغيره:** حكمُ الإطار الثلاثيّ «لا حكم» إذا وفقط إذا كانت له أسبابٌ من `SababLaHukm`. -/
theorem laHukm_iff_sabab (u : Itar3) : hukm3 u = .laHukm ↔ asbabLaHukm u ≠ [] := by
  constructor
  · intro h
    unfold asbabLaHukm
    rw [if_pos h]
    cases hf : fiHadd u
    · simp only [Bool.false_eq_true, ite_false]
      intro he
      unfold fiHadd at hf
      rw [he] at hf
      exact absurd hf (by decide)
    · simp only [ite_true]
      unfold hukm3 at h
      rw [hf] at h
      simp only [ite_true] at h
      rcases damm_laHukm _ _ h with h1 | h1
      · exact absurd h1 (ofBool_ne_laHukm _)
      · rcases damm_laHukm _ _ h1 with h2 | h2
        · unfold wasl3 at h2
          rcases damm_laHukm _ _ h2 with h3 | h3
          · simp [asbabDakhil, h3]
          · rcases damm_laHukm _ _ h3 with h4 | h4
            · exact absurd h4 (ofBool_ne_laHukm _)
            · rcases damm_laHukm _ _ h4 with h5 | h5
              · unfold hukmQiraa qiraa at h5
                cases hi1 : kullMawdi u laIllaAkhir <;> cases hi2 : kullMawdi u laFathaJarr <;>
                  cases hi3 : kullMawdi u laIrabBilHarf <;> simp_all [asbabDakhil]
              · simp [asbabDakhil, h5]
        · exact absurd h2 (ofBool_ne_laHukm _)
  · intro hne
    by_cases hc : hukm3 u = .laHukm
    · exact hc
    · unfold asbabLaHukm at hne
      rw [if_neg hc] at hne
      exact absurd rfl hne

/-- ما في الحدّ يستوفي الحدَّ المعلَن، ويرخّصه `itarOK`. -/
theorem fiHadd_shurut (u : Itar3) (h : fiHadd u = true) : haddMuallan u = true ∧ Mulhaqat.itarOK u.jisr = true := by
  unfold fiHadd asbabKharij at h
  simp only [List.isEmpty_iff, List.append_eq_nil_iff] at h
  refine ⟨(asbabHadd_nil u).1 h.1, ?_⟩
  cases hi : Mulhaqat.itarOK u.jisr
  · exfalso
    have h2 := h.2
    simp only [hi, Bool.false_eq_true, ite_false] at h2
    split at h2 <;> simp at h2
  · rfl

/-- **لا امتناعَ ممّا يردّه `itarOK` (LC11):** إطارٌ يردّه قانونُ المالك البوليّ أو قواعدُ الملحقات حكمُه «لا حكم». -/
theorem la_hukm_ma_radda_itar (u : Itar3) (h : Mulhaqat.itarOK u.jisr = false) : hukm3 u = .laHukm := by
  apply kharij_alhadd
  cases hf : fiHadd u
  · rfl
  · have := (fiHadd_shurut u hf).2
    rw [h] at this
    exact absurd this (by decide)

/-- **وعدمُ التمثيل سببُه `laTamthil`:** إطارٌ ليس في جدول أطر المالك «لا حكم»، وسببُه بين أسبابه. -/
theorem la_tamthil_la_hukm (u : Itar3) (h : framesL.contains u.jisr.ud.f = false) :
    hukm3 u = .laHukm ∧ SababLaHukm.laTamthil ∈ asbabLaHukm u := by
  have hm : u.jisr.ud.f ∉ framesL := by simpa using h
  have hi : Mulhaqat.itarOK u.jisr = false := by
    simp [Mulhaqat.itarOK, SLGE.Kull.uK, hm]
  have hl := la_hukm_ma_radda_itar u hi
  have hf : fiHadd u = false := by
    cases hh : fiHadd u
    · rfl
    · have := (fiHadd_shurut u hh).2
      rw [hi] at this
      exact absurd this (by decide)
  refine ⟨hl, ?_⟩
  unfold asbabLaHukm asbabKharij
  simp [hl, hf, hi, hm]

/-- **ولا امتناعَ إلّا على إطارٍ يرخّصه `itarOK`.** -/
theorem mumtani_itarOK (u : Itar3) (h : hukm3 u = .mumtani) : Mulhaqat.itarOK u.jisr = true :=
  (fiHadd_shurut u (fiHadd_of_hukm u (by rw [h]; decide))).2

/-- **الاحتواء (على الترخيص):** الإطارُ الثلاثيّ المرخَّص يحتوي أطرَ طبقاته الدالّةَ والنحويّة: الإطارُ النحويّ مرخَّص، والتركيبُ بلا
خلل، وسلسلةُ الكلمات المركَّبة إطارُ دالٍّ مرخَّص، وتركيبُها مرخَّصٌ بآلة المالك `Msent` وله تقطيعٌ كلماتٍ ومقاطعَ (`jumla_murakhkhasa`؛
شرطُها — خلايا الكلمات دون 116 — من الابتداء). -/
theorem itar3_yahtawi (u : Itar3) (ht : tarkhis3 u = true) :
    Mulhaqat.itarOK u.jisr = true ∧ (rakkib u.kalimat).khalal = none ∧ dalOK (rakkib u.kalimat).silsila = true ∧
    Msent.Lic 0 (rakkib u.kalimat).silsila ∧ ∃ S, ValidS S ∧ sentChain S = (rakkib u.kalimat).silsila := by
  unfold tarkhis3 at ht; simp only [Bool.and_eq_true] at ht
  obtain ⟨⟨⟨⟨⟨⟨hi, hk⟩, -⟩, -⟩, -⟩, hq⟩, -⟩ := ht
  unfold ibtida3 at hi; simp only [Bool.and_eq_true] at hi
  have hws : ∀ w ∈ u.kalimat, ∀ a ∈ w.khalaya, a < 116 := by
    intro w hw a ha
    have h1 := List.all_eq_true.mp hi.1.1.2 w hw
    have h2 := List.all_eq_true.mp h1 a ha
    simpa using h2
  unfold waqf3 at hq; simp only [Bool.and_eq_true] at hq
  refine ⟨hi.1.1.1.1.1.1, Option.isNone_iff_eq_none.mp hk, hq.1,
    jumla_murakhkhasa u.kalimat hws (dal_waqf_kama_yuqra _ hq.1)⟩

/-- **والاحتواءُ على الحكم:** الإطارُ الثلاثيّ المحكومُ بالترخيص في الحدّ، والقيدُ الدلاليّ مرخَّص، والإسنادُ تامٌّ في غير شبه الجملة. -/
theorem itar3_yahtawi_hukm (u : Itar3) (h : hukm3 u = .murakhkhas) :
    fiHadd u = true ∧ tarkhis3 u = true ∧ hukmQayd u.isnad = .murakhkhas ∧
    (u.jisr.ud.f.1 ≠ 2 → hukmMadlul u.isnad = .murakhkhas) := by
  obtain ⟨hf, ht, hm⟩ := (hukm3_murakhkhas u).1 h
  have ht' := ht
  unfold tarkhis3 at ht'; simp only [Bool.and_eq_true] at ht'
  obtain ⟨⟨⟨⟨⟨⟨hi, -⟩, -⟩, -⟩, -⟩, hq⟩, -⟩ := ht'
  unfold ibtida3 at hi; simp only [Bool.and_eq_true] at hi
  unfold waqf3 at hq; simp only [Bool.and_eq_true] at hq
  refine ⟨hf, ht, ?_, ?_⟩
  · unfold hukmQayd; rw [hi.2, hm]; rfl
  · intro h2
    unfold hukmMadlul hukmQayd; rw [hi.2, hm]
    have hwq : waqfMadlul u.isnad = true := by
      have := hq.2
      cases hc : (u.jisr.ud.f.1 == 2)
      · rw [hc] at this; simpa using this
      · exact absurd (beq_iff_eq.mp hc) h2
    rw [hwq]; rfl

/-! ### الشواهد: «ذَهَبَ الْوَلَدُ»، «ذَهَبَ وَلَدٌ»، «فِي الدَّارِ» -/

def dhahaba : Kalima := ⟨[92, 4, 104], false, false⟩           -- ذَهَبَ (ذ=23 ه=1 ب=26)
def alWalad : Kalima := ⟨[55, 112, 52, 69], true, true⟩        -- الْوَلَدُ (ل=13 و=28 د=17؛ همزة الوصل تُزاد في الابتداء)
def waladun : Kalima := ⟨[112, 52, 69, 59], false, false⟩      -- وَلَدٌ (التنوين نونٌ ساكنة)
def fiK : Kalima := ⟨[4 * 25 + 2, 4 * 11 + 3], false, false⟩   -- فِي (ف=25 ي=11)
def adDar : Kalima := ⟨[4 * 17 + 3, 4 * 17 + 0, 4 * 2 + 3, 4 * 15 + 2], true, true⟩  -- الدَّارِ (اللامُ مدغمة: دْ دَ ا رِ؛ د=17 ر=15)

def dhahabaAlWalad : Itar3 :=
  { jisr := { ud := Mulhaqat.darabaZayd }, kalimat := [dhahaba, alWalad], maani := [dhahab, walad],
    isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ }

def dhahabaWaladun : Itar3 :=
  { jisr := { ud := Mulhaqat.jaaRajul }, kalimat := [dhahaba, waladun], maani := [dhahab, walad],
    isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ }

def fiDar : Itar3 :=
  { jisr := { ud := Mulhaqat.bikam }, kalimat := [fiK, adDar], maani := [fi, dar],
    isnad := ⟨walad, .alaqa 1 30, .idafiyya⟩ }

def kana : Kalima := ⟨[4 * 8 + 0, 4 * 2 + 3, 4 * 14 + 0], false, false⟩   -- كَانَ (ك=8 ن=14)
def dhahiban : Kalima := ⟨[92, 11, 4 * 1 + 2, 104, 59], false, false⟩     -- ذَاهِبًا (ه=1؛ التنوين نونٌ ساكنة)
def hajj : Kalima := ⟨[16, 11, 39], false, false⟩                        -- حَاجْ (شاهد المالك: مدٌّ ثمّ ساكنٌ معلَّق)
def taraK : Kalima := ⟨[4 * 16 + 0, 11, 4 * 15 + 0], false, false⟩       -- طَارَ (ط=16 ر=15)
def dhahaban : Kalima := ⟨[92, 4, 11, 104, 59], false, false⟩            -- ذَهَابًا
def yadhhaba : Kalima := ⟨[4 * 11 + 0, 95, 4, 104], false, false⟩         -- يَذْهَبَ (ي=11؛ بَ آخرًا نصبًا)
def qumtuK : Kalima := ⟨[29, 111, 73], false, false⟩                     -- قُمْتُ (ق=7 م=27 ت=18)
def dhahabM : Madlul := { haqiqa := 10, khawass := [], alaqat := [], qabiliyyat := [], afrad := [] }   -- الذهابُ مصدرًا (اسم)
/-- «الْوَلَدُ يَذْهَبُ»: إطارُ المالك الاسميّ بخبرٍ جملةٍ فعلية (المضارعُ معرب، فاعلُه مستتر). -/
def alWaladYadhhab : UD :=
  { pre := [], f := (0, 0, [(0, 0, 0), (2, 0, 0), (3, 1, 1)]), ats := [noun 1 0 0, mudari 0 0, pron 3 0 0], ex := [e0, e0, e0] }
def kawn : Madlul := { haqiqa := 60, khawass := [], alaqat := [], qabiliyyat := [], afrad := [], tim := true }
def dhahib : Madlul := { haqiqa := 10, khawass := [], alaqat := [], qabiliyyat := [], afrad := [] }

/-- «كَانَ الْوَلَدُ ذَاهِبًا»: إطارُ المالك الاسميّ بالناسخ كان (الأداة 1)، سماتُه كما في مبرهنة المالك `Simat.zaman` (كان ماضٍ مبنيّ). -/
def kanaUD : UD :=
  { pre := [], f := (0, 1, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]), ats := [(0, 9, (0, 0, 0), true), noun 1 0 0, noun 0 0 0],
    ex := [e0, e0, e0] }
def kanaAlWalad : Itar3 :=
  { jisr := { ud := kanaUD }, kalimat := [kana, alWalad, dhahiban], maani := [kawn, walad, dhahib],
    isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ }

/-- **«ذَهَبَ الْوَلَدُ» على الطبقات الثلاث:** الإطارُ النحويّ فعلٌ وفاعل، والكلمتان تركّبتا بسقوط همزة الوصل بلا إصلاح (بعد متحرّك)،
والفاعلُ مرفوعٌ بضمّته، وقسمُ «ذهب» فعلٌ وقسمُ «الولد» اسمٌ عند المالك، والذهابُ قابليّةٌ للولد حقيقةً؛ ونمطُ الجملة
CV·CV·CVC·CV·CV·CV. و«ذَهَبَ وَلَدٌ» بالتنوين كذلك (بحدّ الكلمة 116). **وما يُخلّ:** «ذَهَبَ الْوَلَدَ» (نصبُ الفاعل: ممتنع)، و«طَارَ الْوَلَدُ»
بمدلول «طار» (قابليّة 12 ليست في حقول الولد: لا حكم — لا ممتنع)، وموضوعٌ غيرُ مدلول الفاعل (ممتنع)، ومدلولُ الفعل بلا زمانٍ بهيئته
(ممتنع)، ومحمولٌ خاصّةً عن فعل (ممتنع)، وكلمةٌ واحدة (ممتنع). -/
theorem shahid_dhahaba_alwalad :
    hukm3 dhahabaAlWalad = .murakhkhas ∧ hukm3 dhahabaWaladun = .murakhkhas ∧
    (rakkib [dhahaba, alWalad]).silsila = [92, 4, 104, 55, 112, 52, 69] ∧ (rakkib [dhahaba, alWalad]).islahat = [(2, .la)] ∧
    (rakkib [dhahaba, waladun]).silsila = [92, 4, 104, 116, 112, 52, 69, 59] ∧
    (qattaJumla [92, 4, 104, 55, 112, 52, 69]).map (·.map (·.map nawMaqta)) = some [[.CV, .CV, .CVC, .CV, .CV, .CV]] ∧
    hukm3 { dhahabaAlWalad with kalimat := [dhahaba, ⟨[55, 112, 52, 68], true, true⟩] } = .mumtani ∧
    hukm3 { dhahabaAlWalad with kalimat := [taraK, alWalad], maani := [tara, walad], isnad := ⟨walad, .qabiliyya 12, .isnadiyya⟩ }
      = .laHukm ∧
    hukm3 { dhahabaAlWalad with isnad := ⟨insan, .qabiliyya 10, .isnadiyya⟩ } = .mumtani ∧
    hukm3 { dhahabaAlWalad with maani := [{ dhahab with tim := false }, walad] } = .mumtani ∧
    hukm3 { dhahabaAlWalad with isnad := ⟨walad, .khassa 10, .isnadiyya⟩ } = .mumtani ∧
    hukm3 { dhahabaAlWalad with kalimat := [dhahaba], maani := [dhahab] } = .mumtani := by decide +kernel

/-- **«فِي الدَّارِ» شبهُ جملة:** تعلُّقٌ بمسندٍ مقدَّر، علاقتُه عند المالك «تعلّق» (`semOf 6 = 5`) وتعيينُها إضافيةً قرارُ `Nisab.nisbaOf`،
ومحمولُه علاقةٌ إلى مدلول المجرور، وموضوعُه من المقام («الولدُ في الدار») — مرخَّص؛ والتركيبُ بحذف المدّ عند همزة الوصل، والمجرورُ
بكسرته؛ وبنسبةٍ إسنادية ممتنع (لا إسنادَ في شبه الجملة)؛ وبجرّ المجرور ضمّةً ممتنع. و«ذَهَبَ الْوَلَدُ» بنسبةٍ تقييدية ممتنع. -/
theorem shahid_fi_dar :
    hukm3 fiDar = .murakhkhas ∧
    (rakkib [fiK, adDar]).silsila = [102, 71, 68, 11, 62] ∧ (rakkib [fiK, adDar]).islahat = [(2, .hadhfMadd)] ∧
    hukm3 { fiDar with isnad := ⟨walad, .alaqa 1 30, .isnadiyya⟩ } = .mumtani ∧
    hukm3 { fiDar with kalimat := [fiK, ⟨[4 * 17 + 3, 4 * 17 + 0, 4 * 2 + 3, 4 * 15 + 1], true, true⟩] } = .mumtani ∧
    hukm3 { dhahabaAlWalad with isnad := ⟨walad, .qabiliyya 10, .taqyidiyya⟩ } = .mumtani := by decide +kernel

def musrian : Kalima := ⟨[4 * 27 + 1, 4 * 20 + 3, 4 * 15 + 2, 4 * 3 + 0, 59], false, false⟩  -- مُسْرِعًا (م=27 س=20 ر=15 ع=3؛ التنوين نونٌ ساكنة)
def musri : Madlul := { haqiqa := 50, khawass := [], alaqat := [], qabiliyyat := [], afrad := [] }

/-- «ذَهَبَ الْوَلَدُ مُسْرِعًا»: الحالُ ملحقٌ (`Mulhaqat.Dawr.hal`) يرسو على الفاعل، كلمتُه ثالثةُ الكلمات. -/
def dhahabaAlWaladMusrian : Itar3 :=
  { jisr := { ud := Mulhaqat.darabaZayd, ml := [{ dawr := .hal, marsa := 1, t := noun 0 0 0 }] },
    kalimat := [dhahaba, alWalad, musrian], maani := [dhahab, walad, musri], isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ }

/-- **الملحقُ بكلمته:** «ذَهَبَ الْوَلَدُ مُسْرِعًا» مرخَّص — الحالُ منصوبٌ بفتحته قبل التنوين (`Mulhaqat.halatAt`: [0])، ومدلولُه اسم؛
و«مُسْرِعٌ» مرفوعًا ممتنع، وبلا كلمةٍ للحال ممتنع (الكلماتُ بعدد الظواهر)، وبمدلولٍ ذي زمانٍ للحال ممتنع. و«ذَهَبَ الْوَلَدُ ذَهَابًا»
المفعولُ المطلق يرسو على الفعل ويتأخّر عن الفاعل (`yataakhkhar`) — مرخَّص. -/
theorem shahid_hal :
    hukm3 dhahabaAlWaladMusrian = .murakhkhas ∧
    (rakkib [dhahaba, alWalad, musrian]).silsila = [92, 4, 104, 55, 112, 52, 69, 116, 109, 83, 62, 12, 59] ∧
    hukm3 { dhahabaAlWaladMusrian with kalimat := [dhahaba, alWalad, ⟨[109, 83, 62, 13, 59], false, false⟩] } = .mumtani ∧
    hukm3 { dhahabaAlWaladMusrian with kalimat := [dhahaba, alWalad], maani := [dhahab, walad] } = .mumtani ∧
    hukm3 { dhahabaAlWaladMusrian with maani := [dhahab, walad, { musri with tim := true }] } = .mumtani ∧
    hukm3 { dhahabaAlWaladMusrian with
            jisr := { ud := Mulhaqat.darabaZayd, ml := [{ dawr := .mutlaq, marsa := 0, t := noun 0 0 0 }] },
            kalimat := [dhahaba, alWalad, dhahaban], maani := [dhahab, walad, dhahabM] } = .murakhkhas := by decide +kernel

/-- **الناسخُ الفعليّ فعلٌ:** «كَانَ الْوَلَدُ ذَاهِبًا» مرخَّص — الأداةُ كان بزمنٍ عند المالك فقسمُها فعل (`qismDawr`)، واسمُها مرفوع
وخبرُها منصوبٌ بفتحته قبل التنوين، ومحمولُه قابليّةُ الذهاب (الخبرُ وصفٌ مشتقّ: معلَنٌ بلا فحصٍ للاشتقاق في الكود)؛ وبمدلولٍ لكان بلا
زمان ممتنع. -/
theorem shahid_kana :
    hukm3 kanaAlWalad = .murakhkhas ∧
    (rakkib [kana, alWalad, dhahiban]).silsila = [32, 11, 56, 55, 112, 52, 69, 116, 92, 11, 6, 104, 59] ∧
    hukm3 { kanaAlWalad with maani := [{ kawn with tim := false }, walad, dhahib] } = .mumtani := by decide +kernel

/-- **خارجَ الحدّ «لا حكم» لا «ممتنع»:** «ذَهَبَ» بفاعلٍ مستتر و«قُمْتُ» بالضمير المتّصل (الموضوعُ إحالةٌ في المقام)، والحالُ المتقدّم
(`qabl`)، والفاعلُ المثنّى (الإعرابُ بالحروف)، و«الْوَلَدُ يَذْهَبَ» (المضارعُ خبرًا: لا يعيّن إطارُ المالك حالتَه) — كلُّها لا حكم؛ و«حَاجْ»
ثمّ همزةُ وصلٍ بعد مدٍّ وساكنٍ معلَّق لا إصلاحَ لها عند المالك (`Khalal.laHukm`) فلا حكم. -/
theorem shahid_hadd :
    hukm3 { jisr := { ud := Mulhaqat.darabaMudmar }, kalimat := [dhahaba], maani := [dhahab],
            isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ } = .laHukm ∧
    hukm3 { jisr := { ud := Mulhaqat.qumtu }, kalimat := [qumtuK], maani := [dhahab],
            isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ } = .laHukm ∧
    hukm3 { jisr := { ud := alWaladYadhhab }, kalimat := [alWalad, yadhhaba], maani := [walad, dhahab],
            isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ } = .laHukm ∧
    hukm3 { dhahabaAlWaladMusrian with
            jisr := { ud := Mulhaqat.darabaZayd, ml := [{ dawr := .hal, marsa := 1, t := noun 0 0 0, qabl := true }] } } = .laHukm ∧
    hukm3 { dhahabaAlWalad with jisr := { ud := { Mulhaqat.darabaZayd with ats := [past 0 0, noun 1 0 1] } } } = .laHukm ∧
    (rakkib [hajj, alWalad]).khalal = some (.laHukm 2) ∧
    hukm3 { dhahabaAlWalad with kalimat := [hajj, alWalad] } = .laHukm := by decide +kernel

def alFata : Kalima := ⟨[55, 4 * 25 + 0, 4 * 18 + 0, 4 * 2 + 3], true, true⟩                   -- الْفَتَى (ف=25 ت=18؛ ى ألفٌ ساكنة)
def alQadi : Kalima := ⟨[55, 4 * 7 + 0, 4 * 2 + 3, 4 * 12 + 2, 4 * 11 + 3], true, true⟩         -- الْقَاضِي (ق=7 ض=12 ي=11)
def afdala : Kalima := ⟨[4 * 0 + 0, 4 * 25 + 3, 4 * 12 + 0, 4 * 13 + 0], false, false⟩        -- أَفْضَلَ (ء=0 ل=13)
def afdali : Kalima := ⟨[4 * 0 + 0, 4 * 25 + 3, 4 * 12 + 0, 4 * 13 + 2], false, false⟩        -- أَفْضَلِ
def adDara : Kalima := ⟨[4 * 17 + 3, 4 * 17 + 0, 4 * 2 + 3, 4 * 15 + 0], true, true⟩          -- الدَّارَ (بأل وفتحة)
def alWaladaK : Kalima := ⟨[55, 112, 52, 68], true, true⟩                                    -- الْوَلَدَ
/-- فعلٌ وفاعلٌ ومفعولان: إطارٌ ليس في جدول أطر المالك `framesL`. -/
def mafulaynUD : UD := { pre := [], f := (1, 0, [(2, 0, 0), (3, 0, 0), (4, 0, 0), (4, 0, 0)]), ats := [past 0 0, noun 1 0 0, noun 1 0 0, noun 1 0 0], ex := [e0, e0, e0, e0] }
/-- «طَارَ الْوَلَدُ» (قابليّةُ الطيران ليست في حقول الولد)، و«ذَهَبَ» بفاعلٍ مستتر. -/
def taraAlWalad : Itar3 := { dhahabaAlWalad with kalimat := [taraK, alWalad], maani := [tara, walad], isnad := ⟨walad, .qabiliyya 12, .isnadiyya⟩ }
def dhahabaMudmar : Itar3 := { jisr := { ud := Mulhaqat.darabaMudmar }, kalimat := [dhahaba], maani := [dhahab], isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ }
def bimafulayn : Itar3 :=
  { jisr := { ud := mafulaynUD },
    kalimat := [dhahaba, alWalad, alWaladaK, alWaladaK], maani := [dhahab, walad, walad, walad],
    isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ }

def adDurK : Kalima := ⟨[4 * 17 + 3, 4 * 17 + 1, 4 * 28 + 3, 4 * 15 + 2], true, true⟩     -- الدُّورِ (د=17 و=28 ر=15)
/-- «فِي أَفْضَلِ الدُّورِ» و«فِي أَفْضَلَ الدُّورِ»: الممنوعُ مضافًا (القطر L87–88: جرُّه الكسرة). -/
def fiAfdalAdDur (w : Kalima) : Itar3 :=
  { fiDar with jisr := { ud := Mulhaqat.bikam, ml := [{ dawr := .mudafIlayhi, marsa := 1, naw := 0, t := noun 1 0 0, q := 2 }] },
               kalimat := [fiK, w, adDurK], maani := [fi, dar, dar] }
def alWaladDhahabaUD : UD := { pre := [], f := (0, 0, [(0, 0, 0), (2, 0, 0), (3, 1, 1)]), ats := [noun 1 0 0, past 0 0, pron 3 0 0], ex := [e0, e0, e0] }
/-- «الْوَلَدُ ذَهَبَ ذَهَبَ»: توكيدُ الفعل لفظيًّا («أتاك أتاك»، القطر L387) — لا يمثّله `tawkidOK` (`ismiAt`). -/
def alWaladDhahabaDhahaba : Itar3 :=
  { jisr := { ud := alWaladDhahabaUD, ml := [{ dawr := .tawkid, marsa := 1, naw := 0, t := past 0 0 }] },
    kalimat := [alWalad, dhahaba, dhahaba], maani := [walad, dhahab, dhahab], isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ }
def lamK : Kalima := ⟨[4 * 13 + 0, 4 * 27 + 3], false, false⟩                   -- لَمْ
def yaghzuK : Kalima := ⟨[4 * 11 + 0, 4 * 5 + 3, 4 * 19 + 1], false, false⟩       -- يَغْزُ (القطر L91)
def yaduuK : Kalima := ⟨[4 * 11 + 0, 4 * 17 + 3, 4 * 3 + 1, 4 * 28 + 3], false, false⟩  -- يَدْعُو
def lamYafalUD : UD := { pre := [], f := (1, 5, [(7, 0, 0), (2, 0, 0), (3, 0, 0)]), ats := [harfA, mudari 0 0, noun 0 0 0], ex := [e0, e0, e0] }
/-- «لَمْ يَفْعَلْ وَلَدٌ» بفعلٍ معطًى. -/
def lamYafal (v : Kalima) : Itar3 :=
  { jisr := { ud := lamYafalUD }, kalimat := [lamK, v, waladun], maani := [fi, dhahab, walad], isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ }
def yafalUD : UD := { pre := [], f := (1, 0, [(2, 0, 0), (3, 0, 0)]), ats := [mudari 0 0, noun 0 0 0], ex := [e0, e0] }
/-- «يَدْعُو وَلَدٌ»: المضارعُ المعتلّ مرفوعًا (الضمّةُ مقدَّرة). -/
def yaduuWaladun : Itar3 :=
  { jisr := { ud := yafalUD }, kalimat := [yaduuK, waladun], maani := [dhahab, walad], isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ }

/-- **«لا حكم» بسببه** (2026-10-20). كانت الستّةُ الأولى ممتنعةً على ca5ed3c (مخرجُ `#eval` في الجلسة، لا هذه المبرهنة):
- «ذَهَبَ الْفَتَى»، «ذَهَبَ الْقَاضِي» — `illaAkhir`؛ و«يَدْعُو وَلَدٌ» — `illaAkhir`.
- «فِي أَفْضَلَ» — `fathaJarr`.
- فعلٌ وفاعلٌ ومفعولان — `laTamthil`؛ و«الْوَلَدُ ذَهَبَ ذَهَبَ» — `itarYarudd`.
- وكانت «لا حكم» بلا سببٍ مسمّى: «طَارَ الْوَلَدُ» — `madlul`؛ «حَاجْ» ثمّ همزةُ الوصل — `tarkib`؛ والفاعلُ المستتر — `musnadIlayhGhayrZahir`.
- و«ذَهَبَ الْوَلَدُ» مرخَّصٌ بلا أسباب. -/
theorem shahid_asbab :
    hukm3 { dhahabaAlWalad with kalimat := [dhahaba, alFata] } = .laHukm ∧
    asbabLaHukm { dhahabaAlWalad with kalimat := [dhahaba, alFata] } = [.illaAkhir] ∧
    asbabLaHukm { dhahabaAlWalad with kalimat := [dhahaba, alQadi] } = [.illaAkhir] ∧
    asbabLaHukm yaduuWaladun = [.illaAkhir] ∧
    asbabLaHukm { fiDar with kalimat := [fiK, afdala] } = [.fathaJarr] ∧
    asbabLaHukm bimafulayn = [.laTamthil] ∧
    asbabLaHukm alWaladDhahabaDhahaba = [.itarYarudd] ∧
    asbabLaHukm taraAlWalad = [.madlul] ∧
    asbabLaHukm { dhahabaAlWalad with kalimat := [hajj, alWalad] } = [.tarkib] ∧
    asbabLaHukm dhahabaMudmar = [.musnadIlayhGhayrZahir] ∧
    hukm3 dhahabaAlWalad = .murakhkhas ∧ asbabLaHukm dhahabaAlWalad = [] := by decide +kernel

/-- إطارٌ بملحقٍ واحد على «ذَهَبَ الْوَلَدُ مُسْرِعًا». -/
def biMulhaq (m : Mulhaqat.Mulhaq) : Itar3 :=
  { dhahabaAlWaladMusrian with jisr := { ud := Mulhaqat.darabaZayd, ml := [m] } }

/-- **لكلّ سببٍ من أسباب الحدّ العشرة شاهد** (على الشاهد): إطارٌ ثانٍ؛ والحالُ متقدّمًا؛ وعاملٌ اسميّ؛ ونائبٌ مجرور؛ ونعتٌ يرسو على الفعل
(لا يتأخّر بدوره، ومرساه غيرُ آخر الظواهر)؛ والحالُ مثنًّى؛ والفعلُ غيرُ ظاهر؛ والفاعلُ مستتر؛ و«الْوَلَدُ يَذْهَبَ» (المضارعُ خبرًا)؛ والفاعلُ
مثنًّى — في كلٍّ منها سببُ الحدّ الوحيد (`asbabHadd`). وفي ستّةٍ منها يزيد `asbabLaHukm` ردَّ `itarOK` (`itarYarudd` أو
`laTamthil`)، فالشاهدُ يعزل سببَ الحدّ بين أسباب الحدّ، لا عن ردّ الإطار. -/
theorem shahid_hadd_asbab :
    asbabHadd { dhahabaAlWalad with jisr := { ud := Mulhaqat.darabaZayd, thani := some Mulhaqat.darabaZayd } } = [.itarThani] ∧
    asbabHadd (biMulhaq { dawr := .hal, marsa := 1, t := noun 0 0 0, qabl := true }) = [.mulhaqMutaqaddim] ∧
    asbabHadd (biMulhaq { dawr := .amilIsmi, marsa := 1, t := noun 0 0 0 }) = [.amilIsmi] ∧
    asbabHadd (biMulhaq { dawr := .naib, marsa := 1, naw := 2, t := noun 0 0 0 }) = [.naibMajrur] ∧
    asbabHadd (biMulhaq { dawr := .nat, marsa := 0, t := noun 0 0 0 }) = [.mawdiNutq] ∧
    asbabHadd (biMulhaq { dawr := .hal, marsa := 1, t := noun 0 0 1 }) = [.mulhaqGhayrMufrad] ∧
    asbabHadd { dhahabaAlWalad with jisr := { ud := { Mulhaqat.darabaZayd with f := (1, 0, [(2, 1, 1), (3, 0, 0)]) } } } = [.musnadGhayrZahir] ∧
    asbabHadd dhahabaMudmar = [.musnadIlayhGhayrZahir] ∧
    asbabHadd { jisr := { ud := alWaladYadhhab }, kalimat := [alWalad, yadhhaba], maani := [walad, dhahab], isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ } = [.filMurabKharij] ∧
    asbabHadd { dhahabaAlWalad with jisr := { ud := { Mulhaqat.darabaZayd with ats := [past 0 0, noun 1 0 1] } } } = [.ismGhayrMufrad] := by
  decide +kernel

def darabaK : Kalima := ⟨[4 * 12 + 0, 4 * 15 + 0, 4 * 26 + 0], false, false⟩                -- ضَرَبَ (ض=12 ر=15 ب=26)
def darab : Madlul := { haqiqa := 10, khawass := [], alaqat := [], qabiliyyat := [], afrad := [], tim := true }
/-- «ضَرَبَ الْفَتَى الْوَلَدَ»: فعلٌ وفاعلٌ مقصورٌ ومفعول. -/
def darabaFata (w : Kalima) : Itar3 :=
  { jisr := { ud := Mulhaqat.daraba }, kalimat := [darabaK, alFata, w], maani := [darab, walad, walad], isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ }
def lanK : Kalima := ⟨[4 * 13 + 0, 4 * 14 + 3], false, false⟩                           -- لَنْ
def lanYafalUD : UD := { pre := [], f := (1, 4, [(7, 0, 0), (2, 0, 0), (3, 0, 0)]), ats := [harfA, mudari 0 0, noun 0 0 0], ex := [e0, e0, e0] }
/-- «لَنْ يَفْعَلَ وَلَدٌ» بفعلٍ معطًى. -/
def lanYafal (v : Kalima) : Itar3 :=
  { jisr := { ud := lanYafalUD }, kalimat := [lanK, v, waladun], maani := [fi, dhahab, walad], isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ }
def yaduwaK : Kalima := ⟨[4 * 11 + 0, 4 * 17 + 3, 4 * 3 + 1, 4 * 28 + 0], false, false⟩  -- يَدْعُوَ
/-- «ذَهَبَ الْوَلَدُ الْفَتَى» بدلًا: الملحقُ بكلمةٍ آخرُها ألفٌ ساكنة. -/
def badalFata : Itar3 :=
  { dhahabaAlWalad with jisr := { ud := Mulhaqat.darabaZayd, ml := [{ dawr := .badal, marsa := 1, naw := 0, t := noun 1 0 0 }] }, kalimat := [dhahaba, alWalad, alFata], maani := [dhahab, walad, walad] }

def fatan : Kalima := ⟨[4 * 25 + 0, 4 * 18 + 0, 59], false, false⟩                             -- فَتًى (التنوين نونٌ ساكنة)
def qadin : Kalima := ⟨[4 * 7 + 0, 4 * 2 + 3, 4 * 12 + 2, 59], false, false⟩                  -- قَاضٍ
def abuka : Kalima := ⟨[4 * 0 + 0, 4 * 26 + 1, 4 * 28 + 3, 4 * 8 + 0], false, false⟩          -- أَبُوكَ (ك=8)
def yakhshaK : Kalima := ⟨[4 * 11 + 0, 4 * 6 + 3, 4 * 10 + 0], false, false⟩                  -- يَخْشَ (خ=6 ش=10)
def yarmiK : Kalima := ⟨[4 * 11 + 0, 4 * 15 + 3, 4 * 27 + 2], false, false⟩                   -- يَرْمِ (ر=15 م=27)
def abuK : Kalima := ⟨[4 * 0 + 0, 4 * 26 + 1, 4 * 28 + 3], false, false⟩                       -- أَبُوْ
def yakhshaAlif : Kalima := ⟨[4 * 11 + 0, 4 * 6 + 3, 4 * 10 + 0, 4 * 2 + 3], false, false⟩     -- يَخْشَى (ى ألفٌ ساكنة)
def qadiK : Kalima := ⟨[4 * 7 + 0, 4 * 2 + 3, 4 * 12 + 2, 4 * 11 + 3], false, false⟩          -- قَاضِيْ (بلا أل)
def yaqdiK : Kalima := ⟨[4 * 11 + 0, 4 * 7 + 3, 4 * 12 + 2, 4 * 11 + 3], false, false⟩         -- يَقْضِيْ (ق=7 ض=12)
def alWaladi : Kalima := ⟨[55, 112, 52, 4 * 17 + 2], true, true⟩                              -- الْوَلَدِ
def abahu : Kalima := ⟨[4 * 0 + 0, 4 * 26 + 0, 4 * 2 + 3, 4 * 1 + 1], false, false⟩          -- أَبَاهُ (ه=1)
def abawK : Kalima := ⟨[4 * 0 + 0, 4 * 26 + 0, 4 * 28 + 3], false, false⟩                       -- أَبَوْ (فتحةٌ قبل الواو)
def dalwK : Kalima := ⟨[4 * 17 + 0, 4 * 13 + 3, 4 * 28 + 3], false, false⟩                      -- دَلْوْ (سكونٌ قبل الواو)
def daruK : Kalima := ⟨[4 * 17 + 0, 4 * 2 + 3, 4 * 15 + 1, 4 * 8 + 0], false, false⟩            -- دَارُكَ
/-- «ذَهَبَ <فاعلٌ> الْوَلَدِ»: فاعلٌ له مضافٌ إليه ملحقٌ بأل (`q := 2`). -/
def dhahabaMudaf (w : Kalima) : Itar3 :=
  { dhahabaAlWalad with jisr := { ud := Mulhaqat.darabaZayd, ml := [{ dawr := .mudafIlayhi, marsa := 1, naw := 0, t := noun 1 0 0, q := 2 }] }, kalimat := [dhahaba, w, alWaladi], maani := [dhahab, walad, walad] }
/-- «ذَهَبَ أَبُو الْوَلَدِ». -/
def abuAlWalad : Itar3 := dhahabaMudaf abuK
/-- «ضَرَبَ الْوَلَدُ <مفعولٌ> الْوَلَدِ»: مفعولٌ له مضافٌ إليه ملحقٌ بأل (`q := 2`). -/
def darabaMudaf (w : Kalima) : Itar3 :=
  { darabaFata alQadi with jisr := { ud := Mulhaqat.daraba, ml := [{ dawr := .mudafIlayhi, marsa := 2, naw := 0, t := noun 1 0 0, q := 2 }] }, kalimat := [darabaK, alWalad, w, alWaladi], maani := [darab, walad, walad, walad] }
def dariK : Kalima := ⟨[4 * 17 + 0, 4 * 2 + 3, 4 * 15 + 2, 4 * 8 + 0], false, false⟩           -- دَارِكَ (ك=8)
def abikaK : Kalima := ⟨[4 * 0 + 0, 4 * 26 + 2, 4 * 11 + 3, 4 * 8 + 0], false, false⟩          -- أَبِيكَ

/-- **القراءةُ «لا حكم» لا تُسقط امتناعًا قاطعًا** (على الشاهد): «ضَرَبَ الْفَتَى الْوَلَدَ» لا حكم (`illaAkhir`)، و«ضَرَبَ الْفَتَى الْوَلَدُ» (المفعولُ
مرفوع) ممتنع؛ و«ذَهَبَ الْفَتَى الْوَلَدُ» (ثلاثُ كلماتٍ لخانتين) ممتنع؛ و«فِي أَفْضَلَ» بنسبةٍ إسنادية (لا إسنادَ في شبه الجملة) ممتنع؛
و«لَنْ يَدْعُوْ وَلَدٌ» بواوٍ ساكنة و«لَنْ يَقْضِيْ وَلَدٌ» بياءٍ ساكنة و«ضَرَبَ الْوَلَدُ الْقَاضِيْ» ممتنعة («وتظهر الفتحة في نحو "إن القاضي لن
يقضي ولن يدعو"»، القطر L94–95)، و«لَنْ يَدْعُوَ وَلَدٌ» مرخَّص، و«ضَرَبَ الْوَلَدُ قَاضِيْ» بلا أل لا حكم (`illaAkhir`: لاحتمال «غلامي»، L92)؛
و«فِي دَارِكَ» و«فِي أَبِيكَ» و«فِي أَبُوكَ» لا حكم (`fathaJarr`: آخرُ الخلايا حركةُ الضمير)؛ و«ذَهَبَ أَبُو الْوَلَدِ» لا حكم (`irabBilHarf`)،
و«ذَهَبَ أَبَوْ الْوَلَدِ» و«ذَهَبَ دَلْوْ الْوَلَدِ» (ما قبل الواو غيرُ ضمّة: `wawBadDamma`) ممتنعان، و«ضَرَبَ الْوَلَدُ أَبُو الْوَلَدِ» (L79 «وتنصب
بالألف») و«ضَرَبَ الْوَلَدُ قَاضِيْ الْوَلَدِ» (مضافًا تظهر الفتحة، بالاستدلال من L94–95) ممتنعان؛ والقراءةُ في الملحق كذلك: «ذَهَبَ الْوَلَدُ الْفَتَى»
بدلًا لا حكم (`illaAkhir`). -/
theorem shahid_qiraa :
    hukm3 (darabaFata alWaladaK) = .laHukm ∧ asbabLaHukm (darabaFata alWaladaK) = [.illaAkhir] ∧
    hukm3 (darabaFata alWalad) = .mumtani ∧
    hukm3 { dhahabaAlWalad with kalimat := [dhahaba, alFata, alWalad] } = .mumtani ∧
    hukm3 { fiDar with kalimat := [fiK, afdala], isnad := ⟨walad, .alaqa 1 30, .isnadiyya⟩ } = .mumtani ∧
    hukm3 (lanYafal yaduuK) = .mumtani ∧ hukm3 (lanYafal yaduwaK) = .murakhkhas ∧
    hukm3 (lanYafal yaqdiK) = .mumtani ∧
    hukm3 { darabaFata alQadi with kalimat := [darabaK, alWalad, alQadi] } = .mumtani ∧
    hukm3 { darabaFata alQadi with kalimat := [darabaK, alWalad, qadiK] } = .laHukm ∧
    asbabLaHukm { darabaFata alQadi with kalimat := [darabaK, alWalad, qadiK] } = [.illaAkhir] ∧
    asbabLaHukm { fiDar with kalimat := [fiK, dariK] } = [.fathaJarr] ∧
    asbabLaHukm { fiDar with kalimat := [fiK, abikaK] } = [.fathaJarr] ∧
    asbabLaHukm { fiDar with kalimat := [fiK, abuka] } = [.fathaJarr] ∧
    hukm3 abuAlWalad = .laHukm ∧ asbabLaHukm abuAlWalad = [.irabBilHarf] ∧
    hukm3 (dhahabaMudaf abawK) = .mumtani ∧ hukm3 (dhahabaMudaf dalwK) = .mumtani ∧
    hukm3 (darabaMudaf abuK) = .mumtani ∧ hukm3 (darabaMudaf qadiK) = .mumtani ∧
    hukm3 badalFata = .laHukm ∧ asbabLaHukm badalFata = [.illaAkhir] := by decide +kernel


/-- **وما بقي** (معلَن؛ كلُّه كما كان على ca5ed3c):
- «فِي أَفْضَلِ» (ممنوعٌ مجرورٌ بالكسرة بلا أل ولا إضافة) مرخَّص — الممنوعُ لا يُعرف بلا معجم؛ ومضافًا «فِي أَفْضَلِ الدُّورِ» مرخَّص
  و«فِي أَفْضَلَ الدُّورِ» ممتنع (القطر L87–88)؛ و«فِي الدَّارَ» بأل وفتحة ممتنع.
- «لَمْ يَدْعُو وَلَدٌ» (إثباتُ حرف العلّة مجزومًا) مرخَّص، و«لَمْ يَغْزُ»/«لَمْ يَخْشَ»/«لَمْ يَرْمِ» وَلَدٌ (القطر L91) ممتنعة — البابُ
  `mudariMutall` من المعجم.
- «ذَهَبَ فَتًى» و«ذَهَبَ قَاضٍ» (المنوَّنان) ممتنعان؛ والضميرُ المتّصل بحركته: «ذَهَبَ أَبُوكَ» ممتنع، و«ذَهَبَ أَبَاهُ» (خطأ، L79) مرخَّص،
  و«ضَرَبَ الْوَلَدُ أَبَاهُ» (صواب) ممتنع؛ و«ضَرَبَ الْوَلَدُ دَارُكَ» (خطأ، L77 «وينصب بفتحة») مرخَّص، و«ذَهَبَ دَارُكَ» (صواب) ممتنع؛ و«ذَهَبَ أَبُوْ» بلا مضافٍ إليه ممتنع
  (شرطُ إعراب الستّة بالحروف الإضافةُ: الألفية L79 «وشرط ذا الاعراب إن يضفن لا ... للياكجا أخو أبيك ذا اعتلا»).
- «لَمْ يَخْشَى وَلَدٌ» (إثباتُ الألف مجزومًا) مرخَّص كـ«لَمْ يَدْعُو» — مقلوبٌ على القطر L91؛ وهو وحده ما يقتل P336، والطفرةُ تنقله إلى
  «لا حكم» أي نحو القطر لا بعيدًا عنه.
- و«ممتنع» بلا أسباب: «طَارَ» كلمةً واحدة. -/
theorem shahid_baqi :
    hukm3 { fiDar with kalimat := [fiK, afdali] } = .murakhkhas ∧
    hukm3 (fiAfdalAdDur afdali) = .murakhkhas ∧ hukm3 (fiAfdalAdDur afdala) = .mumtani ∧
    hukm3 { fiDar with kalimat := [fiK, adDara] } = .mumtani ∧
    hukm3 (lamYafal yaduuK) = .murakhkhas ∧ hukm3 (lamYafal yaghzuK) = .mumtani ∧
    hukm3 (lamYafal yakhshaK) = .mumtani ∧ hukm3 (lamYafal yarmiK) = .mumtani ∧
    hukm3 { dhahabaWaladun with kalimat := [dhahaba, fatan] } = .mumtani ∧
    hukm3 { dhahabaWaladun with kalimat := [dhahaba, qadin] } = .mumtani ∧
    hukm3 { dhahabaAlWalad with kalimat := [dhahaba, abuka] } = .mumtani ∧
    hukm3 { dhahabaAlWalad with kalimat := [dhahaba, abuK] } = .mumtani ∧ hukm3 (lamYafal yakhshaAlif) = .murakhkhas ∧
    hukm3 { dhahabaAlWalad with kalimat := [dhahaba, abahu] } = .murakhkhas ∧
    hukm3 { darabaFata alQadi with kalimat := [darabaK, alWalad, abahu] } = .mumtani ∧
    hukm3 { darabaFata alQadi with kalimat := [darabaK, alWalad, abuka] } = .murakhkhas ∧
    hukm3 { darabaFata alQadi with kalimat := [darabaK, alWalad, daruK] } = .murakhkhas ∧
    hukm3 { dhahabaAlWalad with kalimat := [dhahaba, daruK] } = .mumtani ∧
    hukm3 { dhahabaAlWalad with kalimat := [taraK], maani := [tara] } = .mumtani ∧
    asbabLaHukm { dhahabaAlWalad with kalimat := [taraK], maani := [tara] } = [] := by decide +kernel

/-! ## الرقم: الطبقاتُ الثلاث في عددٍ واحد -/

def kalimaCode (w : Kalima) : Nat := pair (encS w.khalaya) (pair (Muwahhad.bCode w.wasl) (Muwahhad.bCode w.al))

theorem kalimaCode_inj (w v : Kalima) (h : kalimaCode w = kalimaCode v) : w = v := by
  obtain ⟨k, a, b⟩ := w; obtain ⟨k', a', b'⟩ := v
  unfold kalimaCode at h
  obtain ⟨h1, h⟩ := pair_injective h
  obtain ⟨h2, h3⟩ := pair_injective h
  simp only at h1 h2 h3
  rw [encS_inj _ _ h1, bCode_inj _ _ h2, bCode_inj _ _ h3]

def madlulCode (m : Madlul) : Nat :=
  pair m.haqiqa (pair (encS m.khawass) (pair (encS (m.alaqat.map fun p => pair p.1 p.2))
    (pair (encS m.qabiliyyat) (pair (encS m.afrad) (pair (Muwahhad.bCode m.yamnaShirka)
      (pair (Muwahhad.bCode m.ind) (Muwahhad.bCode m.tim)))))))

theorem madlulCode_inj (m n : Madlul) (h : madlulCode m = madlulCode n) : m = n := by
  obtain ⟨a, b, c, d, e, f, g, i⟩ := m; obtain ⟨a', b', c', d', e', f', g', i'⟩ := n
  unfold madlulCode at h
  obtain ⟨h1, h⟩ := pair_injective h
  obtain ⟨h2, h⟩ := pair_injective h
  obtain ⟨h3, h⟩ := pair_injective h
  obtain ⟨h4, h⟩ := pair_injective h
  obtain ⟨h5, h⟩ := pair_injective h
  obtain ⟨h6, h⟩ := pair_injective h
  obtain ⟨h7, h8⟩ := pair_injective h
  simp only at h1 h2 h3 h4 h5 h6 h7 h8
  have hc : c = c' := by
    apply map_inj (fun p : Nat × Nat => pair p.1 p.2) _ _ _ (encS_inj _ _ h3)
    intro x y hxy; obtain ⟨p, q⟩ := pair_injective hxy; exact Prod.ext p q
  rw [h1, encS_inj _ _ h2, hc, encS_inj _ _ h4, encS_inj _ _ h5, bCode_inj _ _ h6, bCode_inj _ _ h7, bCode_inj _ _ h8]

def mahmulCode : Mahmul → Nat
  | .khassa k => pair 0 k | .alaqa r x => pair 1 (pair r x) | .qabiliyya q => pair 2 q | .fard f => pair 3 f

theorem mahmulCode_inj (m n : Mahmul) (h : mahmulCode m = mahmulCode n) : m = n := by
  cases m <;> cases n <;> simp only [mahmulCode] at h <;>
    first
    | (exact absurd (pair_injective h).1 (by decide))
    | (rw [(pair_injective h).2])
    | (obtain ⟨h3, h4⟩ := pair_injective (pair_injective h).2; rw [h3, h4])

def nisbaCode : Nisab.Nisba → Nat | .isnadiyya => 0 | .taqyidiyya => 1 | .idafiyya => 2

theorem nisbaCode_inj (a b : Nisab.Nisba) (h : nisbaCode a = nisbaCode b) : a = b := by
  cases a <;> cases b <;> first | rfl | (simp [nisbaCode] at h)

def itarMadlulCode (u : ItarMadlul) : Nat := pair (madlulCode u.mawdu) (pair (mahmulCode u.mahmul) (nisbaCode u.nisba))

theorem itarMadlulCode_inj (u v : ItarMadlul) (h : itarMadlulCode u = itarMadlulCode v) : u = v := by
  obtain ⟨a, b, c⟩ := u; obtain ⟨a', b', c'⟩ := v
  unfold itarMadlulCode at h
  obtain ⟨h1, h⟩ := pair_injective h
  obtain ⟨h2, h3⟩ := pair_injective h
  simp only at h1 h2 h3
  rw [madlulCode_inj _ _ h1, mahmulCode_inj _ _ h2, nisbaCode_inj _ _ h3]

def itar3Enc (u : Itar3) : Nat :=
  pair (Mulhaqat.itarEnc u.jisr) (pair (encS (u.kalimat.map kalimaCode))
    (pair (encS (u.maani.map madlulCode)) (itarMadlulCode u.isnad)))

/-- **الرقمُ الواحد يُفكّ:** إطاران ثلاثيّان في الحدّ غيرُ ممتنعَين (مرخَّصان أو لا حكمَ لهما) برقمٍ واحد — إطارُهما النحويّ واحد
(بمبرهنة الملحقات)، وكلماتُهما واحدة، ومدلولاتُهما واحدة، وإسنادُهما واحد. -/
theorem itar3_value (u v : Itar3) (hu : hukm3 u ≠ .mumtani) (hv : hukm3 v ≠ .mumtani)
    (hfu : fiHadd u = true) (hfv : fiHadd v = true) (h : itar3Enc u = itar3Enc v) : u = v := by
  have hu' := ibtida3_of_hukm u hu hfu; have hv' := ibtida3_of_hukm v hv hfv
  unfold ibtida3 at hu' hv'; simp only [Bool.and_eq_true] at hu' hv'
  unfold itar3Enc at h
  obtain ⟨h1, h⟩ := pair_injective h
  obtain ⟨h2, h⟩ := pair_injective h
  obtain ⟨h3, h4⟩ := pair_injective h
  have e1 := Mulhaqat.itar_value _ _ hu'.1.1.1.1.1.1 hv'.1.1.1.1.1.1 h1
  have e2 := map_inj kalimaCode kalimaCode_inj _ _ (encS_inj _ _ h2)
  have e3 := map_inj madlulCode madlulCode_inj _ _ (encS_inj _ _ h3)
  have e4 := itarMadlulCode_inj _ _ h4
  cases u; cases v
  simp only at e1 e2 e3 e4
  subst e1 e2 e3 e4; rfl

end Utur
end Jisr
