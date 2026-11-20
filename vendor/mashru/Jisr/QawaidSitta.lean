/-
  Jisr/QawaidSitta.lean — جدولُ القواعد، صفُّه الأوّل: الأسماءُ الستّة، قواعدَ بالمحتوى يقبلها فاحصٌ واحد، تُرفع بها «لا حكم» في
  الطبقة الثالثة (`Jisr.Utur`).

  **القرار.** خطّةُ «الجبر يقود» (`hawkama/خطة_الجبر_يقود.md`) §١٠ج-1: صفُّ الأسماء الستّة أوّلًا بموافقة المالك 2026-10-20 (19:03)، واعتمادُه
  الخطّةَ 23:00، واختيارُه «بإذنٍ منّي لكلّ جدول (موصى به)» من خياراتٍ صاغها البنّاء (و«موصى به» وسمُ البنّاء)؛ ثمّ رسالتُه في الجلسة
  2026-10-21، وهي نصُّ عرض البنّاء ثمّ «موافق»: «The first rules-table row (the six names): the first build step in plan §١٠, using content-keyed rules from (أ). It needs
  your permission to seal its table when it's ready. موافق». والجدولُ (`qawaid.tsv`) مختومٌ في `mudaat/sijill.json` بإذن المالك في الجلسة
  2026-10-22 (00:46 بتوقيت عمّان): «موافق ولك اذن الختم والايداع والتوثيق»؛ وكان مرشّحًا منذ 2026-10-21. والإصدارُ يحمل بصمتَه: `isdar_basma` (تعريفيّة)
  `isdar = "الأسماء الستّة @ " ++ QawaidJadwal.basma`؛ ومطابقةُ `basma` لبصمة السجلّ يفحصها `tahaqquq/test_qawaid.py` حين يحضر المودَع.

  **المرجع** (مودَعاتٌ مختومة، بأسطرها؛ تُطابَق اقتباساتُ الجدول بالاختبار `tahaqquq/test_qawaid.py`):
  قطر الندى L77–79 «فيرفع بضمة، وينصب بفتحة، / ويجر بكسرة، ويجزم بحذف حركة، إلا الأسماء الستة، وهي أبوه وأخوه وحموها / وهنوه وفوه وذو مال، فترفع بالواو
  وتنصب بالألف وتجر بالياء»، وL82–83 «وجمع المذكر السالم كالزيدون فيرفع / بالواو»، وL84–85 «وأولو وعشرون … وبنون وعليون وشبهه كالجمع»؛
  والألفية L76 «من ذاك ذو إن صحبة أبانا ... والفم حيث الميم منه بانا»، وL78 «وفي أب وتالييه يندر ... وقصرها من نقصهن أشهر»، وL79 «وشرط ذا
  الاعراب إن يضفن لا ... للياكجا أخو أبيك ذا اعتلا»؛ والقطر L140 «وذو في لغة طي، وذا بعد ما أو من الاستفهاميتين» (في باب الموصول: لـ«ذو» و«ذا»
  وضعٌ آخر؛ ولا يذكر السطرُ وقوعَ «ذو» الطائية مضافةً).

  **البناء.**
  ١. **القضايا** `Qadiyya` على خلايا الكلمة في موضعها: صورتُها، ولها مضافٌ إليه، وموضعُها اسميٌّ يطلب حالةً — هذه تُقرأ من الإطار (`aslMawdi`)؛
     و«ذو» بمعنى صاحب لا تُقرأ من الدالّ (`laYuqra`: تعيينُ البنّاء — الدالُّ وحده لا يقرّر المدلول، وشرطُ الألفية L76 على المعنى)؛ والنتيجةُ:
     معربٌ بالحرف بحالته.
  ٢. **القوانين** `qawanin` من صفوف الجدول (`Jisr.QawaidJadwal.sitta`، مولَّدٌ لا يُحرَّر): لكلّ اسمٍ ووجهٍ (التمامُ، والقصرُ حيث نصّت الألفية L78)
     وحالةٍ قانونٌ مقدّماتُه صورتُه والإضافةُ (L79) وطلبُ حالته، والصحبةُ لـ«ذو» (L76)؛ ونتيجتُه إعرابُه بالحرف. والقاعدةُ `qSitta` واحدةٌ إصدارُها
     بصمةُ الجدول، والفاحصُ `Qaida.maqbulM` (الخطوةُ بمحتوى القانون، المكافئةُ لـ`Qaida.fahs` في اللقطة: `Qaida.maqbul_takafu`).
  ٣. **الحكم** `hukmSitta`: حكمُ الطبقة الثالثة `Utur.hukm3` بعينه، والقراءةُ فيه `qiraaSitta` بدلَ `Utur.hukmQiraa`: موضعٌ لا يُقرأ بالحرف
     (`Utur.laIrabBilHarf`) أو بحرف علّةٍ آخرًا (`Utur.laIllaAkhir`) يُقرأ إن كانت له رخصةٌ بسلسلةٍ مقبولة (`rukhsa`)؛ وموضعُ الإعراب بالحرف بلا
     رخصة: «لا حكم» إن بقي شرطٌ لا يُقرأ (`mawquf`: «ذو» مضافًا في موضع الرفع)، وإلّا «ممتنع». **والامتناعُ مشروطٌ بإفراد الاسم المعلَن في الإطار**
     (`Utur.fiHadd`: غيرُ المفرد خارجَ الحدّ «لا حكم»): ما يُرفع بالواو في القطر الأسماءُ الستّة معدودةً (L78–79) وجمعُ المذكر السالم وملحقاتُه
     (L82–85)، والثاني خارجَ الحدّ بإعلان عدده؛ فالمفردُ المعلَن بواوٍ ساكنةٍ بعد ضمّةٍ رفعًا مضافًا، وليس من صور الجدول، ممتنعٌ بالقاعدة العامّة
     «فيرفع بضمة» (L77) — قراءةُ البنّاء (الخطّة §١٠ج-1)، وهي **تغييرٌ عن `Utur`**: كان فيه «لا حكم» (`irabBilHarf`) لأنّه «لا يُفرَّق من الستّة بلا
     معجم»، والجدولُ الآن يفرّقها، والعددُ معلَنٌ لا يُقرأ من الكلمة: «بَنُو الْوَلَدِ» (L85 «وبنون») و«مُسْلِمُو الْوَلَدِ» معلَنَين مفردَين ممتنعان، ومعلَنَين
     جمعًا «لا حكم» (`shawahid_sitta`). وموضعُ حرف العلّة بلا رخصة يبقى «لا حكم»
     (قد يكون مقصورًا أو منقوصًا: `Utur.illaMuqaddara`).

  **ما ثبت** (34 مبرهنة بالمعيار الموحَّد في `Nizam/Asas.lean`: 14 لكلّ، و10 تعريفيّة، و10 على الشاهد).
  * لكلّ: لا يغيّر الحكمَ المقطوع (`hukmSitta_murakhkhas_thabit`، `hukmSitta_mumtani_thabit`)؛ ولا يرفع «لا حكم» إلى الترخيص إلّا ما سببُه
    القراءةُ بحرف العلّة أو بالحرف (`raf_bi_qiraa`)، ولا امتناعَ جديدًا إلّا من قراءة الجدول (`mumtani_bi_qiraa`)؛ وفي موضعِ إعرابٍ بالحرف لا رخصةَ
    له ولا وقف ليست الكلمةُ صورةَ رفعٍ لصفٍّ من الجدول (`ghayr_sitta`) — والوصلُ بين الإطار ومواضعه بتعريف `kullMawdi` لا بمبرهنة؛ والرخصةُ سلسلةٌ
    مرخَّصةٌ في القاعدة (`rukhsa_murakhkhasa`)، والسلسلةُ مقبولةٌ إذا كانت مقدّماتُ قانونٍ أصولًا (`silsila_maqbula`)؛ والصحبةُ لا تثبت
    (`sahib_la_yathbut`) فلا رخصةَ لصور «ذو» في أيّ موضع (`dhu_la_rukhsa` — نفيُ الرخصة؛ و«لا حكم» لـ«ذُو» مضافةً في موضع الرفع من `mawquf`، ولـ«ذَا» مضافةً
    في موضع النصب وسببُه في `Utur` حرفُ العلّة `illaAkhir`، على الشاهد؛ و«ذَهَبَ ذُو» بلا مضافٍ إليه ممتنعٌ في `Utur` نفسِه كـ«ذَهَبَ أَبُوْ»، و«ضَرَبَ الْوَلَدُ ذَا» و«فِي ذِي» بلا مضافٍ إليه «لا حكم» فيه وهنا وسببُه في `Utur` حرفُ العلّة)؛ والقاعدةُ لا تُنتج إعرابًا بالحرف إلّا لصور قوانينها (`la_tamdid`؛ صادقةٌ
    بالبناء: النتيجةُ لا تكون أصلًا — فلا قياسَ في القاعدة على الستّة؛ وأنّ اللغة كذلك قراءةُ البنّاء)؛ و`natija_murab`، `qanun_raf_fi`،
    `kullMawdi_mono`، `qiraaSitta_min_qiraa`.
  * تعريفيّة: ما خرج عن الحدّ «لا حكم» (`hukmSitta_kharij`)؛ و`shakl` وثلاثُ مبرهناته وصورتا الحكمين عليه، و`hukmQiraa_ne_mumtani`؛ وإصدارُ
    القاعدة بصمةُ الجدول (`isdar_basma`)، وشرطُ موضع الشاهد بأجزائه الثلاثة (`shartMawdi_shurut`)، و`fiMawdi` بشرطيها لكلّ إطارٍ وكلمة
    (`fiMawdi_shartan`).
  * على الشاهد: الجدولُ وبابُ الستّة في `Jisr.JisrDal` سواءٌ في التمام، وصورةُ القصر في بابه المقصور (`.maqsur`) تحتمل الأحوال الثلاث
    (`jadwal_jisrdal`؛ وإعلانُ القصر بابَ المقصور تعيينُ البنّاء — `JisrDal` لا يذكر قصرَ الستّة، و`.maqsur` فيه «تقدر جميع الحركات» L92)، وشواهدُه
    في باب الستّة صورٌ في الجدول (`shawahid_jisrdal`)، و`abuK_jadwal`؛ وصورُ القوانين صورُ الصفوف (`suwar_sitta`)، وقوانينُ «ذو» فيها الصحبة
    (`sahib_muqaddima`)، وشواهدُ الإطار (`shawahid_sitta`) ومواضعُها (`mawadi_shawahid`)، و`fiMawdi` تشترط وجودَ الموضع (`fiMawdi_wujud`)، وأصولُ الموضع باسميّته وحالته (`asl_mawdi`)، وتعدّدُ
    الوجوه بدرجةٍ لا يغيّر الحكم (`daraja_wujuh`).

  **تعيينُ البنّاء** (معلَن، §١٠هـ: «ترميزُ نصّ القاعدة شروطًا مكتوبةً تأويل»): الصورُ بلا ضميرٍ متّصل (المضافُ إليه كلمةٌ ملحقة، فقيدُ «لا للياء»
  في L79 لا يقع؛ وشاهدُ القطر L385 «أخاك أخاك» بضميرٍ متّصل معلَّمٌ في الجدول «لم يُبنَ»)، وشرطُ «حيث الميم منه بانا» (L76) في الصورة نفسِها (فُو
  بلا ميم)، والقصرُ بالإضافة كالتمام، والقصرُ صورةُ النصب في الأحوال الثلاث؛ والإفرادُ من حدّ الطبقة (`Utur.fiHadd`)؛ والخلايا ملفوظة (فواوُ «عمرو»
  الرسميّة ليست خلية — لا يعالجها القارئ: لا ذكرَ لـ«عمرو» في `Qari/` ولا `Dal/`)؛ والدرجةُ (`Saff.daraja`) بلفظ مصدرها («أشهر» الألفية L78،
  «أحسن» L77، «الأفصح» القطر L79–80؛ و«كغد» نقصًا قراءةُ البنّاء) بيانٌ لا يدخل الحكم — قيمةُ ج3 ذاتُ الرتبة لم تُبنَ؛ وعمودا «العلّة»
  و«الاستعمال» في الجدول نقلٌ من الكتاب بأسطره (س12976–12978 في الباب س12974–12975 «هذا باب ما يتغير في الإضافة إلى الاسم إذا جعلته اسم رجل أو امرأة وما لا يتغير إذا كان اسم رجل أو
  امرأة» — وأب وأخ ممّا لا يتغيّر، س12976 «أما ما لا يتغير فأب وأخ» —، س12349–12350) لا يدخل القوانين،
  وتسميةُ الأوّل علّةً قراءةُ البنّاء.
  ولم يُبنَ: الضميرُ المتّصل («أبوه»: يُقرأ آخرُ خليّته في الطبقة الثالثة، `Utur.shahid_baqi`)، والنقصُ في غير ما تقرؤه القاعدة العامّة،
  وجسرُ `Utur.Hukm` إلى `Nizam.Hukm` (مطلوبٌ قبل تعميم الجدول، الخطّة §١٠ج-1).
  واختبارُ الجدول يفحص نصَّ Lean فحصًا كاشفًا لتغييرٍ عاديٍّ لا حارسًا من التحايل. وطفراتُ هذا الملفّ تقتلها Lean (`tafrat_juz.py` على 5702b1f:
  قُتلت كلُّها؛ وما بعده تعليقاتٌ لا تمسّ نصوصها)، وقتلُها نوعان:
  * **ما يغيّر الحكم:** P392–P394 وP396–P398 وP407 وP408 وP410 وP411 تُكذِّب كلٌّ منها `shawahid_sitta` (وشطورُها من `hukm3` و`asbabLaHukm`
    في `Utur` لا تمسّها الطفرة، وشطرا `sitta.find?` و`suwar` لم يكذبا في نسخةٍ منها — بتقسيم القضيّة شطورًا عند المراجع المستقلّ، في ملفّ مراجعةٍ مؤقّتٍ لم يُحفظ في المستودع —،
    فالذي كذب شطرٌ من `hukmSitta`) — بـ `lake env lean` على نسخٍ مطفورة، شغّله المراجعُ المستقلّ والبنّاءُ كلٌّ على حدة؛ و`shawahid_sitta` وحدها تقتل P393،
    وP397 معها `mawadi_shawahid`.
  * **تثبيتُ تعريفٍ لا حراسةُ حكم:** P400–P403 وP405–P406 تغيّر صيغَ تعريفات الشواهد (`mawadiShawahid`، `fiMawdi`، `shartMawdi`)، وهي مصرَّحٌ
    بها بعد `hukmSitta` فلا يرجع إليها؛ وP404 تغيّر إصدارَ القاعدة `qSitta` (قبل `hukmSitta`)، والإصدارُ لا يقرؤه `Qaida.maqbulM`؛ فقتلُها
    تثبيتٌ لتلك الصيغ: `mawadi_shawahid` تقتل P400 (بشرط الوجود في `fiMawdi` وحده) وP401، و`shartMawdi_shurut` تقتل P402 وP405،
    و`fiMawdi_wujud` و`fiMawdi_shartan` تقتلان P403، و`fiMawdi_shartan` تقتل P406، و`isdar_basma` تقتل P404. وP409 (حذفُ طلب الحالة من
    مقدّمات `qanun`) وP412 (حذفُ اسميّة الموضع من طلب الحالة في `aslMawdi`) وP413 (حذفُ الحالة منه) تقتلها `asl_mawdi` (وP409 بانكسار
    صيغة برهان `ghayr_sitta` أيضًا) تثبيتًا لتعريف `qanun` (P409) ولتعريف أصول الموضع (P412، P413). وأنّها لا تغيّر `hukmSitta` استنتاجٌ من
    التعريفات لم يُبرهَن في المستودع: P413 لا تغيّر الرخصةَ ولا الوقف (من مقدّمات كلّ قانونٍ `.matlub h` ونتيجتُه `.murab h` بالحالة نفسها،
    و`yuntij` يشترط `hs.contains h`)، وP409 وP412 تغيّران الرخصةَ والوقفَ في موضعٍ غيرِ اسميٍّ مضافٍ وحده، ولا يبلغه `hukmSitta` (`fiHadd` يشترط
    `Mulhaqat.itarOK`، وفيه `idafaOK` يُرسي المضافَ إليه على خانةٍ اسميّة `ismiAt`) ولا `shartMawdi` (تستدعي الرخصةَ والوقفَ في موضعٍ اسميّ)؛
    وبرهنه المراجعُ المستقلّ لـP404 وP409 وP412 وP413 (`p404_hukm`، `p409_hukm`، `p412_hukm`، `p413_hukm`) في ملفّات مراجعةٍ مؤقّتة
    لم تُحفظ في المستودع، فلا يُتحقّق منها منه.
-/
import Aql.Qaida
import Jisr.JisrDal
import Jisr.Utur
import Jisr.QawaidJadwal

namespace Jisr
namespace QawaidSitta
open Jisr.Utur Dal Jisr.QawaidJadwal

/-! ## ١. القضايا والقوانين من الجدول -/

/-- قضايا الموضع على خلايا كلمته. -/
inductive Qadiyya
  /-- الكلمةُ بخلاياها. -/
  | sura (c : List Nat)
  /-- لها مضافٌ إليه ملحق (الألفية L79 «إن يضفن»). -/
  | mudaf (c : List Nat)
  /-- موضعُها اسميٌّ يطلب الحالة `h`. -/
  | matlub (h : Nat) (c : List Nat)
  /-- «ذو» بمعنى صاحب (الألفية L76 «إن صحبة أبانا») — لا يُقرأ من الدالّ. -/
  | sahib (c : List Nat)
  /-- معربٌ بالحرف بالحالة `h`: النتيجة. -/
  | murab (h : Nat) (c : List Nat)
deriving DecidableEq, Repr

/-- الأحوالُ الثلاث: رفعٌ 1، نصبٌ 0، جرٌّ 2. -/
def halat : List Nat := [1, 0, 2]

def ismHala : Nat → String
  | 1 => "رفع" | 0 => "نصب" | _ => "جرّ"

def ismWajh : Wajh → String
  | .tamam => "تمام" | .qasr => "قصر" | .naqs => "نقص"

/-- صورةُ الوجه بالحالة: التمامُ بحرف حالته (L79 «فترفع بالواو وتنصب بالألف وتجر بالياء»)، والقصرُ بالألف في الأحوال كلّها (L78، تعيين
البنّاء: صورةُ النصب). -/
def suraBi (s : Saff) : Wajh → Nat → List Nat
  | .tamam, 1 => s.raf
  | .tamam, 0 => s.nasb
  | .tamam, _ => s.jarr
  | _, _ => s.nasb

/-- وجوهُ الصفّ التي لها قانون: التمام، والقصرُ حيث نصّ عليه. -/
def wujuh (s : Saff) : List Wajh := if s.qasr then [.tamam, .qasr] else [.tamam]

/-- قانونُ الاسم بوجهه وحالته. -/
def qanun (s : Saff) (w : Wajh) (h : Nat) : Qaida.Qanun Qadiyya :=
  ⟨s.ism ++ "/" ++ ismWajh w ++ "/" ++ ismHala h,
   [.sura (suraBi s w h), .mudaf (suraBi s w h), .matlub h (suraBi s w h)] ++
     (if s.sahib then [.sahib (suraBi s w h)] else []),
   .murab h (suraBi s w h)⟩

/-- القوانينُ كلُّها من الجدول. -/
def qawanin : List (Qaida.Qanun Qadiyya) :=
  sitta.flatMap fun s => (wujuh s).flatMap fun w => halat.map fun h => qanun s w h

/-- القاعدةُ الواحدة: إصدارُها بصمةُ الجدول. -/
def qSitta : Qaida.Qaida Qadiyya := ⟨"الأسماء الستّة @ " ++ basma, qawanin⟩

/-! ## ٢. الموضع: ما يُقرأ منه، والرخصة -/

/-- أصولُ الموضع: ما يقرؤه الإطار من الكلمة (اسميّةُ الموضع وحالاتُه وإضافتُه)؛ والصحبةُ والنتيجةُ لا تُقرآن. -/
def aslMawdi (nom : Bool) (hs : List Nat) (w : Kalima) (mudaf : Bool) : Qadiyya → Bool
  | .sura c => c == w.khalaya
  | .mudaf c => mudaf && c == w.khalaya
  | .matlub h c => nom && hs.contains h && c == w.khalaya
  | .sahib _ => false
  | .murab _ _ => false

/-- ما لا يُقرأ من الدالّ أصلًا. -/
def laYuqra : Qadiyya → Bool
  | .sahib _ => true
  | _ => false

/-- السلسلةُ بالمحتوى: المقدّماتُ أصولًا، ثمّ القانون. -/
def silsila (r : Qaida.Qanun Qadiyya) : List (Qaida.KhatwaM Qadiyya) := r.muqaddimat.map .asl ++ [.qanun r]

/-- القانونُ ينتج هذه الكلمةَ بحالةٍ يطلبها الموضع. -/
def yuntij (hs : List Nat) (w : Kalima) (r : Qaida.Qanun Qadiyya) : Bool :=
  match r.natija with
  | .murab h c => hs.contains h && c == w.khalaya
  | _ => false

/-- **الرخصة:** قانونٌ ينتج الكلمةَ بحالةٍ يطلبها موضعُها، وسلسلتُه مقبولةٌ عند الفاحص بالمحتوى. -/
def rukhsa (nom : Bool) (hs : List Nat) (w : Kalima) (mudaf : Bool) : Bool :=
  qSitta.qawanin.any fun r => yuntij hs w r && Qaida.maqbulM qSitta (aslMawdi nom hs w mudaf) ⟨r.natija, silsila r⟩

/-- **الموقوف:** قانونٌ ينتج الكلمة، مقدّماتُه المقروءةُ أصولٌ في الموضع، وفيها ما لا يُقرأ من الدالّ. -/
def mawquf (nom : Bool) (hs : List Nat) (w : Kalima) (mudaf : Bool) : Bool :=
  qSitta.qawanin.any fun r => yuntij hs w r && r.muqaddimat.any laYuqra &&
    r.muqaddimat.all (fun m => laYuqra m || aslMawdi nom hs w mudaf m)

/-! ## ٣. الحكم -/

/-- **القراءةُ بالجدول:** حرفُ العلّة آخرًا والإعرابُ بالحرف يُقرآن بالرخصة؛ والفتحةُ في موضع الجرّ كما في `Utur`. ثمّ: موضعُ الإعراب بالحرف بلا
رخصةٍ ولا وقفٍ ممتنع، وما سواه «لا حكم». -/
def qiraaSitta (u : Itar3) : Hukm :=
  if kullMawdi u (fun n hs w m => laIllaAkhir n hs w m || rukhsa n hs w m) && kullMawdi u laFathaJarr &&
     kullMawdi u (fun n hs w m => laIrabBilHarf n hs w m || rukhsa n hs w m) then .murakhkhas
  else if kullMawdi u (fun n hs w m => laIrabBilHarf n hs w m || rukhsa n hs w m || mawquf n hs w m) then .laHukm
  else .mumtani

/-- **حكمُ الطبقة الثالثة بصفّ الأسماء الستّة:** `Utur.hukm3` بعينه، والقراءةُ فيه `qiraaSitta`. -/
def hukmSitta (u : Itar3) : Hukm :=
  if fiHadd u then
    damm (ofBool (ibtida3 u))
      (damm (damm (hukmTarkib (rakkib u.kalimat))
        (damm (ofBool (waslBase u && waslMl u && jisrMadlul u)) (damm (qiraaSitta u) (waslMadlul u.isnad))))
        (ofBool (waqf3 u)))
  else .laHukm

/-- `kullMawdi` يحفظ اللزوم: ما يصدق عليه محمولٌ يصدق عليه ما يلزم عنه. -/
theorem kullMawdi_mono (u : Itar3) (p q : Bool → List Nat → Kalima → Bool → Bool)
    (h : ∀ n hs w m, p n hs w m = true → q n hs w m = true) (hp : kullMawdi u p = true) : kullMawdi u q = true := by
  unfold kullMawdi at hp ⊢
  simp only [Bool.and_eq_true, List.all_eq_true] at hp ⊢
  obtain ⟨h1, h2⟩ := hp
  refine ⟨fun i hi => ?_, fun k hk => ?_⟩
  · have hi' := h1 i hi
    revert hi'
    simp only [Bool.or_eq_true]
    split
    · intro hi'
      rcases hi' with (hi' | hi') | hi'
      · exact Or.inl (Or.inl hi')
      · exact Or.inl (Or.inr hi')
      · exact Or.inr (h _ _ _ _ hi')
    · intro hi'; exact hi'
  · have hk' := h2 k hk
    revert hk'
    split
    · split
      · simp only [Bool.or_eq_true]
        intro hk'
        rcases hk' with (hk' | hk') | hk'
        · exact Or.inl (Or.inl hk')
        · exact Or.inl (Or.inr hk')
        · exact Or.inr (h _ _ _ _ hk')
      · intro hk'; exact hk'
    · intro hk'; exact hk'

/-- القراءةُ المرخَّصة في `Utur` مرخَّصةٌ بالجدول. -/
theorem qiraaSitta_min_qiraa (u : Itar3) (h : qiraa u = true) : qiraaSitta u = .murakhkhas := by
  unfold qiraa at h
  simp only [Bool.and_eq_true] at h
  obtain ⟨⟨h1, h2⟩, h3⟩ := h
  have a := kullMawdi_mono u laIllaAkhir (fun n hs w m => laIllaAkhir n hs w m || rukhsa n hs w m)
    (fun n hs w m hp => by simp [hp]) h1
  have b := kullMawdi_mono u laIrabBilHarf (fun n hs w m => laIrabBilHarf n hs w m || rukhsa n hs w m)
    (fun n hs w m hp => by simp [hp]) h3
  unfold qiraaSitta
  rw [a, h2, b]; rfl

/-- **لا يغيّر الترخيصَ المقطوع.** -/
theorem hukmSitta_murakhkhas_thabit (u : Itar3) (h : hukm3 u = .murakhkhas) : hukmSitta u = .murakhkhas := by
  obtain ⟨hf, ht, hw⟩ := (hukm3_murakhkhas u).1 h
  unfold tarkhis3 at ht
  simp only [Bool.and_eq_true] at ht
  obtain ⟨⟨⟨⟨⟨⟨hi, hk⟩, hb⟩, hm⟩, hj⟩, hq⟩, hr⟩ := ht
  have hT : hukmTarkib (rakkib u.kalimat) = .murakhkhas := (hukmTarkib_murakhkhas _).2 hk
  unfold hukmSitta
  rw [hf, hi, hT, hb, hm, hj, qiraaSitta_min_qiraa u hr, hw, hq]; rfl

/-- صورةُ الحكم في الحدّ بمكوّناته: الابتداءُ، وخاناتُ المالك وملحقاتُه والجسر، والوقف، والتركيب، والقراءة، ووصلُ المدلول. -/
def shakl (a b c : Bool) (t q m : Hukm) : Hukm :=
  damm (ofBool a) (damm (damm t (damm (ofBool b) (damm q m))) (ofBool c))

theorem hukm3_shakl (u : Itar3) (hf : fiHadd u = true) :
    hukm3 u = shakl (ibtida3 u) (waslBase u && waslMl u && jisrMadlul u) (waqf3 u) (hukmTarkib (rakkib u.kalimat))
      (hukmQiraa u) (waslMadlul u.isnad) := by
  unfold hukm3 wasl3 shakl; rw [hf]; rfl

theorem hukmSitta_shakl (u : Itar3) (hf : fiHadd u = true) :
    hukmSitta u = shakl (ibtida3 u) (waslBase u && waslMl u && jisrMadlul u) (waqf3 u) (hukmTarkib (rakkib u.kalimat))
      (qiraaSitta u) (waslMadlul u.isnad) := by
  unfold hukmSitta shakl; rw [hf]; rfl

/-- الامتناعُ من غير القراءة يبقى بتبديلها. -/
theorem shakl_mumtani (a b c : Bool) (t q q' m : Hukm) (hq : q ≠ .mumtani) (h : shakl a b c t q m = .mumtani) :
    shakl a b c t q' m = .mumtani := by
  revert hq h
  cases a <;> cases b <;> cases c <;> cases t <;> cases q <;> cases q' <;> cases m <;> simp [shakl, damm, ofBool]

/-- ومن «لا حكم» لا يصير ممتنعًا إلّا بقراءةٍ ممتنعة. -/
theorem shakl_laHukm_mumtani (a b c : Bool) (t q q' m : Hukm) (h0 : shakl a b c t q m = .laHukm)
    (h : shakl a b c t q' m = .mumtani) (hq : q ≠ .mumtani) : q' = .mumtani := by
  revert hq h0 h
  cases a <;> cases b <;> cases c <;> cases t <;> cases q <;> cases q' <;> cases m <;> simp [shakl, damm, ofBool]

/-- والترخيصُ ترخيصُ المكوّنات كلِّها. -/
theorem shakl_murakhkhas (a b c : Bool) (t q m : Hukm) (h : shakl a b c t q m = .murakhkhas) :
    t = .murakhkhas ∧ q = .murakhkhas ∧ m = .murakhkhas := by
  revert h
  cases a <;> cases b <;> cases c <;> cases t <;> cases q <;> cases m <;> simp [shakl, damm, ofBool]

theorem hukmQiraa_ne_mumtani (u : Itar3) : hukmQiraa u ≠ .mumtani := by
  unfold hukmQiraa; split <;> simp

/-- **ولا الامتناعَ المقطوع:** الامتناعُ في `hukm3` من غير القراءة (القراءةُ فيه لا تمتنع)، فيبقى. -/
theorem hukmSitta_mumtani_thabit (u : Itar3) (h : hukm3 u = .mumtani) : hukmSitta u = .mumtani := by
  cases hf : fiHadd u
  · rw [kharij_alhadd u hf] at h; cases h
  · rw [hukm3_shakl u hf] at h
    rw [hukmSitta_shakl u hf]
    exact shakl_mumtani _ _ _ _ _ _ _ (hukmQiraa_ne_mumtani u) h

/-- **وما خرج عن الحدّ «لا حكم».** -/
theorem hukmSitta_kharij (u : Itar3) (h : fiHadd u = false) : hukmSitta u = .laHukm := by
  unfold hukmSitta; rw [h]; rfl

/-- **لا يرفع «لا حكم» إلى الترخيص إلّا ما سببُه القراءة** بحرف العلّة أو بالحرف: لا التركيب، ولا الفتحةُ في موضع الجرّ، ولا وصلُ المدلول،
ولا الخروجُ عن الحدّ. -/
theorem raf_bi_qiraa (u : Itar3) (h0 : hukm3 u = .laHukm) (h : hukmSitta u = .murakhkhas) :
    ∀ s ∈ asbabLaHukm u, s = .illaAkhir ∨ s = .irabBilHarf := by
  have hf : fiHadd u = true := by
    cases hf : fiHadd u
    · rw [hukmSitta_kharij u hf] at h; cases h
    · rfl
  have hq : hukmTarkib (rakkib u.kalimat) = .murakhkhas ∧ qiraaSitta u = .murakhkhas ∧ waslMadlul u.isnad = .murakhkhas := by
    rw [hukmSitta_shakl u hf] at h
    exact shakl_murakhkhas _ _ _ _ _ _ h
  obtain ⟨hT, hq, hW⟩ := hq
  have hfj : kullMawdi u laFathaJarr = true := by
    unfold qiraaSitta at hq
    split at hq
    · rename_i hc
      simp only [Bool.and_eq_true] at hc
      exact hc.1.2
    · split at hq <;> cases hq
  intro s hs
  unfold asbabLaHukm at hs
  simp only [h0, hf, ite_true] at hs
  unfold asbabDakhil at hs
  rw [hT, hfj, hW] at hs
  simp only [List.mem_append] at hs
  rcases hs with (((hs | hs) | hs) | hs) | hs
  · simp at hs
  · split at hs
    · simp at hs
    · simp at hs; exact Or.inl hs
  · simp at hs
  · split at hs
    · simp at hs
    · simp at hs; exact Or.inr hs
  · simp at hs

/-- **ولا امتناعَ جديدًا إلّا من القراءة بالجدول.** -/
theorem mumtani_bi_qiraa (u : Itar3) (h0 : hukm3 u = .laHukm) (h : hukmSitta u = .mumtani) : qiraaSitta u = .mumtani := by
  cases hf : fiHadd u
  · rw [hukmSitta_kharij u hf] at h; cases h
  · rw [hukm3_shakl u hf] at h0
    rw [hukmSitta_shakl u hf] at h
    exact shakl_laHukm_mumtani _ _ _ _ _ _ _ h0 h (hukmQiraa_ne_mumtani u)

/-! ## ٤. القوانين والفاحص -/

/-- كلُّ قانونٍ ينتج إعرابًا. -/
theorem natija_murab (r : Qaida.Qanun Qadiyya) (hr : r ∈ qSitta.qawanin) : ∃ h c, r.natija = .murab h c := by
  simp only [qSitta, qawanin, List.mem_flatMap, List.mem_map] at hr
  obtain ⟨s, _, w, _, h, _, rfl⟩ := hr
  exact ⟨h, suraBi s w h, rfl⟩

/-- **السلسلةُ مقبولة** إذا كانت مقدّماتُ قانونٍ من القاعدة أصولًا كلَّها. -/
theorem silsila_maqbula (q : Qaida.Qaida Qadiyya) (A : Qadiyya → Bool) (r : Qaida.Qanun Qadiyya) (hr : r ∈ q.qawanin)
    (hA : ∀ m ∈ r.muqaddimat, A m = true) : Qaida.maqbulM q A ⟨r.natija, silsila r⟩ = true := by
  have key : ∀ (ms : List Qadiyya) (t : List Qadiyya) (rest : List (Qaida.KhatwaM Qadiyya)), (∀ m ∈ ms, A m = true) →
      Qaida.fahsM q A t (ms.map .asl ++ rest) = Qaida.fahsM q A (t ++ ms) rest := by
    intro ms
    induction ms with
    | nil => intro t rest _; simp
    | cons m ms ih =>
      intro t rest hm
      simp only [List.map_cons, List.cons_append, Qaida.fahsM, Qaida.tatbiqM, hm m List.mem_cons_self, ite_true]
      rw [ih (t ++ [m]) rest (fun x hx => hm x (List.mem_cons_of_mem _ hx))]
      simp
  unfold Qaida.maqbulM silsila
  rw [key r.muqaddimat [] _ hA]
  simp [Qaida.fahsM, Qaida.tatbiqM, hr]

/-- **الرخصةُ سلسلةٌ مرخَّصةٌ في القاعدة:** ما رُخّص في موضعٍ معربٌ بالحرف بحالةٍ يطلبها، مرخَّصٌ في `qSitta` على أصول الموضع. -/
theorem rukhsa_murakhkhasa (n : Bool) (hs : List Nat) (w : Kalima) (m : Bool) (h : rukhsa n hs w m = true) :
    ∃ k, hs.contains k = true ∧ Qaida.Murakhkhas qSitta (fun p => aslMawdi n hs w m p = true) (.murab k w.khalaya) := by
  unfold rukhsa at h
  simp only [List.any_eq_true, Bool.and_eq_true] at h
  obtain ⟨r, hr, hy, hm⟩ := h
  have hM := Qaida.maqbulM_murakhkhas qSitta (aslMawdi n hs w m) ⟨r.natija, silsila r⟩ hm
  obtain ⟨k, c, hn⟩ := natija_murab r hr
  unfold yuntij at hy
  rw [hn] at hy hM
  simp only [Bool.and_eq_true, beq_iff_eq] at hy
  obtain ⟨hk, rfl⟩ := hy
  exact ⟨k, hk, hM⟩

/-- صورُ الإعراب بالحرف التي في الجدول. -/
def suwar : List (List Nat) := qawanin.filterMap fun r => match r.natija with | .murab _ c => some c | _ => none

/-- **القاعدةُ لا تُنتج إعرابًا بالحرف إلّا لصور قوانينها** — صادقةٌ بالبناء (النتيجةُ لا تكون أصلًا في `aslMawdi`)؛ وأنّ اللغةَ كذلك (مسموعٌ لا يُقاس
عليه) قراءةُ البنّاء. -/
theorem la_tamdid (n : Bool) (hs : List Nat) (w : Kalima) (m : Bool) (k : Nat) (c : List Nat)
    (h : Qaida.Murakhkhas qSitta (fun p => aslMawdi n hs w m p = true) (.murab k c)) : c ∈ suwar := by
  generalize hp : Qadiyya.murab k c = p at h
  cases h with
  | asl ha => subst hp; simp [aslMawdi] at ha
  | qanun r hr _ =>
    simp only [suwar, List.mem_filterMap]
    exact ⟨r, hr, by rw [← hp]⟩

/-- والصورُ صورُ الصفوف: كلُّ صورةٍ في قانونٍ صورةُ رفعٍ أو نصبٍ أو جرٍّ لاسمٍ من الستّة (على الجدول). -/
theorem suwar_sitta : suwar.all (fun c => sitta.any fun s => c == s.raf || c == s.nasb || c == s.jarr) = true := by decide

/-- **الصحبةُ لا تثبت** في القاعدة على أصول أيّ موضع: لا أصلٌ هي ولا نتيجةُ قانون. -/
theorem sahib_la_yathbut (n : Bool) (hs : List Nat) (w : Kalima) (m : Bool) (c : List Nat) :
    ¬ Qaida.Murakhkhas qSitta (fun p => aslMawdi n hs w m p = true) (.sahib c) := by
  intro h
  generalize hp : Qadiyya.sahib c = p at h
  cases h with
  | asl ha => subst hp; simp [aslMawdi] at ha
  | qanun r hr _ =>
    obtain ⟨k, c', hk⟩ := natija_murab r hr
    rw [hk] at hp; cases hp

/-- صورُ «ذو»، وكلُّ قانونٍ ينتج واحدةً منها مقدّماتُه فيها الصحبة (على الجدول). -/
def suwarSahib : List (List Nat) := (sitta.filter (·.sahib)).flatMap fun s => [s.raf, s.nasb, s.jarr]

theorem sahib_muqaddima : qSitta.qawanin.all (fun r => match r.natija with
    | .murab _ c => !suwarSahib.contains c || r.muqaddimat.contains (.sahib c)
    | _ => true) = true := by decide

/-- **لا رخصةَ لـ«ذو»** في أيّ موضع: شرطُ الصحبة لا يُقرأ من الدالّ. -/
theorem dhu_la_rukhsa (n : Bool) (hs : List Nat) (w : Kalima) (m : Bool) (hw : suwarSahib.contains w.khalaya = true) :
    rukhsa n hs w m = false := by
  cases hr : rukhsa n hs w m
  · rfl
  · obtain ⟨k, _, hM⟩ := rukhsa_murakhkhasa n hs w m hr
    exfalso
    generalize hp : Qadiyya.murab k w.khalaya = p at hM
    cases hM with
    | asl ha => subst hp; simp [aslMawdi] at ha
    | qanun r hrq hpre =>
      have hall := List.all_eq_true.mp sahib_muqaddima r hrq
      rw [← hp] at hall
      simp only [hw, Bool.not_true, Bool.false_or, List.contains_iff_mem] at hall
      exact sahib_la_yathbut n hs w m w.khalaya (hpre _ hall)

/-- قانونُ التمام رفعًا لكلّ صفٍّ في القاعدة. -/
theorem qanun_raf_fi (s : Saff) (hs : s ∈ sitta) : qanun s .tamam 1 ∈ qSitta.qawanin := by
  simp only [qSitta, qawanin, List.mem_flatMap, List.mem_map]
  refine ⟨s, hs, .tamam, ?_, 1, by simp [halat], rfl⟩
  unfold wujuh; split <;> simp

/-- **موضعُ الامتناع ليس صورةَ رفعٍ لاسمٍ من الجدول:** موضعُ إعرابٍ بالحرف بلا رخصةٍ ولا وقفٍ ليست كلمتُه صورةَ تمام رفعٍ لصفّ. -/
theorem ghayr_sitta (n : Bool) (hs : List Nat) (w : Kalima) (m : Bool) (h1 : laIrabBilHarf n hs w m = false)
    (h2 : rukhsa n hs w m = false) (h3 : mawquf n hs w m = false) : ∀ s ∈ sitta, s.raf ≠ w.khalaya := by
  intro s hsm heq
  unfold laIrabBilHarf at h1
  simp only [Bool.not_eq_false', Bool.and_eq_true] at h1
  obtain ⟨⟨⟨hn, hm⟩, hh⟩, _⟩ := h1
  have hh' : (1 : Nat) ∈ hs := by simpa using hh
  have hq := qanun_raf_fi s hsm
  have hA : ∀ x ∈ [Qadiyya.sura (suraBi s .tamam 1), .mudaf (suraBi s .tamam 1), .matlub 1 (suraBi s .tamam 1)],
      aslMawdi n hs w m x = true := by
    simp [aslMawdi, suraBi, heq, hn, hm, hh']
  have hy : yuntij hs w (qanun s .tamam 1) = true := by simp [yuntij, qanun, suraBi, heq, hh']
  cases hsb : s.sahib
  · have hmq := silsila_maqbula qSitta (aslMawdi n hs w m) (qanun s .tamam 1) hq
      (by intro x hx; simp only [qanun, hsb] at hx; exact hA x (by simpa using hx))
    have : rukhsa n hs w m = true := by
      unfold rukhsa
      exact List.any_eq_true.mpr ⟨_, hq, by rw [hy, hmq]; rfl⟩
    rw [h2] at this; cases this
  · have : mawquf n hs w m = true := by
      unfold mawquf
      refine List.any_eq_true.mpr ⟨_, hq, ?_⟩
      simp only [hy, Bool.true_and, Bool.and_eq_true, List.any_eq_true, List.all_eq_true]
      refine ⟨⟨.sahib (suraBi s .tamam 1), by simp [qanun, hsb], rfl⟩, fun x hx => ?_⟩
      simp only [qanun, hsb, ite_true, List.mem_append, List.mem_cons] at hx
      rcases hx with hx | hx
      · simp only [Bool.or_eq_true]; exact Or.inr (hA x (by simpa using hx))
      · rcases hx with hx | hx
        · subst hx; simp [laYuqra]
        · simp at hx
    rw [h3] at this; cases this

/-! ## ٥. الجدولُ وبابُ الستّة في الجسر إلى الدالّ (على الشاهد) -/

/-- **الجدولُ وبابُ الستّة في `JisrDal` سواءٌ في التمام:** صورةُ التمام بكلّ حالةٍ يعيّن لها `JisrDal.hukm .sitta` تلك الحالة (حواملُها حواملُ
`JisrDal.farIyaBab`)؛ **وصورةُ القصر (صورةُ النصب) في باب المقصور** يحتمل لها `JisrDal.hukm .maqsur` الأحوالَ الثلاث — فـ«أَبَا» في باب الستّة
نصبٌ معيَّن، وفي المقصور محتمِلة؛ وإعلانُ القصر بابَ المقصور تعيينُ البنّاء (`JisrDal` لا يذكر قصرَ الستّة)، والبابُ معلَنٌ لا يُقرأ من الدالّ
(`JisrDal.Bab`). -/
theorem jadwal_jisrdal : sitta.all (fun s =>
    JisrDal.hukm .sitta s.raf == .muayyan .raf && JisrDal.hukm .sitta s.nasb == .muayyan .nasb &&
    JisrDal.hukm .sitta s.jarr == .muayyan .jarr &&
    (!s.qasr || JisrDal.hukm .maqsur s.nasb == .muhtamal [.raf, .nasb, .jarr])) = true := by decide

/-- وشواهدُ `JisrDal` في باب الستّة («ذو» L79، «أخا» L385، «أبي» L130) صورٌ في الجدول. -/
theorem shawahid_jisrdal : (JisrDal.shawahid.filter (·.bab == .sitta)).all (fun x =>
    sitta.any fun s => x.khalaya == s.raf || x.khalaya == s.nasb || x.khalaya == s.jarr) = true ∧
    (JisrDal.shawahid.filter (·.bab == .sitta)).length = 3 := by decide

/-- وصورةُ «أَبُو» في `Utur` (`abuK`) صورةُ رفع «أب» في الجدول. -/
theorem abuK_jadwal : (sitta.head?).map (·.raf) = some abuK.khalaya := by decide

/-! ## ٦. الشواهد على الإطار -/

/-- خلايا بيد البنّاء، مستقلّةً عن الجدول (ء=0، ه=1، ا=2، ح=4، خ=6، ي=11، ن=14، ل=13، د=17، س=20، ذ=23، ف=25، ب=26، م=27، و=28). -/
def akhuK : Kalima := ⟨[4 * 0 + 0, 4 * 6 + 1, 4 * 28 + 3], false, false⟩    -- أَخُو
def hamuK : Kalima := ⟨[4 * 4 + 0, 4 * 27 + 1, 4 * 28 + 3], false, false⟩   -- حَمُو
def hanuK : Kalima := ⟨[4 * 1 + 0, 4 * 14 + 1, 4 * 28 + 3], false, false⟩   -- هَنُو
def fuK : Kalima := ⟨[4 * 25 + 1, 4 * 28 + 3], false, false⟩                -- فُو
def dhuK : Kalima := ⟨[4 * 23 + 1, 4 * 28 + 3], false, false⟩               -- ذُو
def daluK : Kalima := ⟨[4 * 17 + 0, 4 * 13 + 1, 4 * 28 + 3], false, false⟩  -- دَلُو (ليس من الستّة)
def bunuK : Kalima := ⟨[4 * 26 + 0, 4 * 14 + 1, 4 * 28 + 3], false, false⟩  -- بَنُو (القطر L85 «وبنون»: ملحقٌ بالجمع)
def muslimuK : Kalima := ⟨[4 * 27 + 1, 4 * 20 + 3, 4 * 13 + 2, 4 * 27 + 1, 4 * 28 + 3], false, false⟩  -- مُسْلِمُو (جمعُ مذكّرٍ سالمٌ مضافًا)
def abaK : Kalima := ⟨[4 * 0 + 0, 4 * 26 + 0, 4 * 2 + 3], false, false⟩     -- أَبَا
def abiK : Kalima := ⟨[4 * 0 + 0, 4 * 26 + 2, 4 * 11 + 3], false, false⟩    -- أَبِي
def hanaK : Kalima := ⟨[4 * 1 + 0, 4 * 14 + 0, 4 * 2 + 3], false, false⟩    -- هَنَا
def dhaK : Kalima := ⟨[4 * 23 + 0, 4 * 2 + 3], false, false⟩                -- ذَا
def dhiK : Kalima := ⟨[4 * 23 + 2, 4 * 11 + 3], false, false⟩               -- ذِي
def hanuDamma : Kalima := ⟨[4 * 1 + 0, 4 * 14 + 1], false, false⟩           -- هَنُ (النقص: كغد)
/-- «ذَهَبَ <فاعلٌ> الْوَلَدِ» والفاعلُ معلَنٌ بعدده `n` (0 مفرد؛ وغيرُه خارجَ الحدّ). -/
def dhahabaMudafAdad (w : Kalima) (n : Nat) : Itar3 :=
  { dhahabaMudaf w with jisr := { (dhahabaMudaf w).jisr with ud := { Mulhaqat.darabaZayd with ats := [SLGE.Simat.past 0 0, SLGE.Simat.noun 1 0 n] } } }

/-- **موضعُ الكلمة في إطارها:** للكلمة `w` في الإطار `u` موضعٌ تُطلب حالتُه (ليس كلُّ موضعٍ غيرَها)، وكلُّ موضعٍ لها اسميٌّ يطلب الحالة `h` وحدها
وإضافتُه `m` — على `kullMawdi` نفسِه. -/
def fiMawdi (u : Itar3) (w : Kalima) (h : Nat) (m : Bool) : Bool :=
  !kullMawdi u (fun _ _ v _ => !(v.khalaya == w.khalaya)) &&
  kullMawdi u (fun n hs v mm => !(v.khalaya == w.khalaya) || (n && hs == [h] && mm == m))

/-- **مواضعُ الشواهد** بإطاراتها: (الإطار، الكلمة، الحالة، الإضافة، الرخصة، الوقف) — قائمةٌ واحدة يُشترط عليها الموضعُ وسببُ الحكم بالجدول معًا. -/
def mawadiShawahid : List (Itar3 × Kalima × Nat × Bool × Bool × Bool) :=
  [(abuAlWalad, abuK, 1, true, true, false), (darabaMudaf abaK, abaK, 0, true, true, false),
   (fiAfdalAdDur abiK, abiK, 2, true, true, false), (dhahabaMudaf abaK, abaK, 1, true, true, false),
   (darabaMudaf hanaK, hanaK, 0, true, true, false),
   (dhahabaMudaf dhuK, dhuK, 1, true, false, true), (darabaMudaf dhaK, dhaK, 0, true, false, true),
   (fiAfdalAdDur dhiK, dhiK, 2, true, false, true),
   (dhahabaMudaf daluK, daluK, 1, true, false, false), (dhahabaMudafAdad bunuK 0, bunuK, 1, true, false, false),
   (dhahabaMudafAdad muslimuK 0, muslimuK, 1, true, false, false), (dhahabaMudaf hanaK, hanaK, 1, true, false, false),
   (fiAfdalAdDur hanaK, hanaK, 2, true, false, false),
   ({ darabaFata alQadi with kalimat := [darabaK, alWalad, abaK] }, abaK, 0, false, false, false),
   ({ darabaFata alQadi with kalimat := [darabaK, alWalad, dhaK] }, dhaK, 0, false, false, false),
   ({ fiDar with kalimat := [fiK, dhiK] }, dhiK, 2, false, false, false),
   (darabaFata alWaladaK, alFata, 1, false, false, false),
   ({ dhahabaAlWalad with kalimat := [dhahaba, dhuK] }, dhuK, 1, false, false, false)]

/-- شرطُ عنصرٍ من مواضع الشواهد: الموضعُ في إطاره (`fiMawdi`)، والرخصةُ والوقفُ بقيمتيهما. -/
def shartMawdi : Itar3 × Kalima × Nat × Bool × Bool × Bool → Bool
  | (u, w, h, m, r, q) => fiMawdi u w h m && rukhsa true [h] w m == r && mawquf true [h] w m == q

/-- **شرطُ العنصر بأجزائه الثلاثة:** موضعُه في إطاره، ورخصتُه، ووقفُه (حارسٌ في Lean لصيغة `shartMawdi`). -/
theorem shartMawdi_shurut (u : Itar3) (w : Kalima) (h : Nat) (m r q : Bool) (hs : shartMawdi (u, w, h, m, r, q) = true) :
    fiMawdi u w h m = true ∧ rukhsa true [h] w m = r ∧ mawquf true [h] w m = q := by
  simp only [shartMawdi, Bool.and_eq_true, beq_iff_eq] at hs
  exact ⟨hs.1.1, hs.1.2, hs.2⟩

/-- **`fiMawdi` بشرطيها** لكلّ إطارٍ وكلمة: للكلمة موضعٌ، وكلُّ موضعٍ لها بحالته وإضافته (حارسٌ في Lean لصيغة `fiMawdi`). -/
theorem fiMawdi_shartan (u : Itar3) (w : Kalima) (h : Nat) (m : Bool) (hf : fiMawdi u w h m = true) :
    kullMawdi u (fun _ _ v _ => !(v.khalaya == w.khalaya)) = false ∧
    kullMawdi u (fun n hs v mm => !(v.khalaya == w.khalaya) || (n && hs == [h] && mm == m)) = true := by
  unfold fiMawdi at hf
  revert hf
  cases kullMawdi u (fun _ _ v _ => !(v.khalaya == w.khalaya)) <;>
    cases kullMawdi u (fun n hs v mm => !(v.khalaya == w.khalaya) || (n && hs == [h] && mm == m)) <;> simp

/-- **مواضعُ الشواهد** (على الشاهد): ثمانيةَ عشرَ عنصرًا، كلٌّ بشرطه. -/
theorem mawadi_shawahid : mawadiShawahid.length = 18 ∧ mawadiShawahid.all shartMawdi = true := by decide +kernel

/-- **`fiMawdi` تشترط وجودَ الموضع** (على الشاهد): «هَنَا» ليست في «فِي أَبِي الدُّورِ»، فلا موضعَ لها فيه — ولو صدق شرطُ الحالة على كلّ موضعٍ
لها، لأنّه لا موضع. -/
theorem fiMawdi_wujud : fiMawdi (fiAfdalAdDur abiK) hanaK 2 true = false ∧
    kullMawdi (fiAfdalAdDur abiK) (fun n hs v mm => !(v.khalaya == hanaK.khalaya) || (n && hs == [2] && mm == true)) = true := by decide +kernel

/-- **أصولُ الموضع** (على الشاهد): «أَبُو» رفعًا مضافًا لها رخصةٌ في موضعٍ اسميٍّ يطلب الرفع، ولا رخصةَ لها في موضعٍ غيرِ اسميٍّ يطلبه؛ وفي
موضعٍ اسميٍّ مضافٍ يطلب الرفع، طلبُ الرفع لـ«أَبَا» من أصوله وطلبُ النصب ليس منها. -/
theorem asl_mawdi : rukhsa true [1] abuK true = true ∧ rukhsa false [1] abuK true = false ∧
    aslMawdi true [1] abaK true (.matlub 1 abaK.khalaya) = true ∧ aslMawdi true [1] abaK true (.matlub 0 abaK.khalaya) = false := by
  decide +kernel

/-- **إصدارُ القاعدة بصمةُ الجدول** (تعريفيّة). -/
theorem isdar_basma : qSitta.isdar = "الأسماء الستّة @ " ++ Jisr.QawaidJadwal.basma := rfl

/-- **الشواهد** (على الشاهد). الحكمُ السابق (`hukm3`) وسببُه (`asbabLaHukm`) والحكمُ بالجدول (`hukmSitta`) شروطٌ على الإطار، وسببُ الحكم بالجدول
شرطٌ على موضع الكلمة في إطارها في المبرهنة `mawadi_shawahid`: قائمةٌ واحدة `mawadiShawahid`، لكلّ عنصرٍ منها `shartMawdi` —
`fiMawdi` (للكلمة في الإطار موضعٌ، وكلُّ موضعٍ لها بحالته وإضافته) و`rukhsa` (رخصة) و`mawquf` (وقف) بقيمتيهما.
- «ذَهَبَ أَبُو الْوَلَدِ»، ومثلُه أخو وحمو وهنو وفو: كانت «لا حكم» (`irabBilHarf`) فصارت مرخَّصة؛ وموضعُ «أَبُو» رفعًا مضافًا له رخصة (القطر L79
  «فترفع بالواو»).
- «ذَهَبَ ذُو الْوَلَدِ» كان «لا حكم» (`irabBilHarf`) ويبقى: لا رخصةَ لموضعه وله وقف (الصحبةُ لا تُقرأ: الألفية L76؛ تعيينُ البنّاء)؛ و«ذَهَبَ ذُو» بلا
  مضافٍ إليه في موضع الرفع ممتنعٌ في `Utur` وهنا.
- «ذَهَبَ دَلُو الْوَلَدِ» و«ذَهَبَ بَنُو الْوَلَدِ» و«ذَهَبَ مُسْلِمُو الْوَلَدِ» معلَنةً مفردةً كانت «لا حكم» (`irabBilHarf`) فصارت ممتنعة: لا رخصةَ لمواضعها
  ولا وقف (القاعدةُ العامّة L77، والستّةُ معدودةً L78–79؛ قراءة البنّاء، تغييرٌ عن `Utur`)؛ و«بَنُو» و«مُسْلِمُو» معلَنَين جمعًا خارجَ الحدّ «لا حكم»
  (`ismGhayrMufrad`؛ L82–85).
- «ضَرَبَ الْوَلَدُ أَبَا الْوَلَدِ» و«فِي أَبِي الدُّورِ» كانا «لا حكم» (`illaAkhir`) فصارا مرخَّصين، ولموضعيهما رخصة (L79 «وتنصب بالألف وتجر بالياء»)؛
  و«ذَهَبَ أَبَا الْوَلَدِ» كان «لا حكم» فصار مرخَّصًا، ولموضع «أَبَا» رفعًا مضافًا رخصة (القصر، الألفية L78).
- «ذَهَبَ هَنَا الْوَلَدِ» كان «لا حكم» ويبقى: لا رخصةَ لموضعه رفعًا ولا وقف، ولا لـ«هَنَا» جرًّا مضافًا، ولـ«هَنَا» نصبًا مضافًا رخصة، ولا قصرَ لـ«هن»
  في الجدول (فالألفُ نصبٌ وحدَه)؛ و«ضَرَبَ الْوَلَدُ ذَا الْوَلَدِ» كان «لا حكم» (`illaAkhir`) ويبقى: لموضعه وقفٌ بلا رخصة (الصحبة)؛ ولموضع «ذِي» جرًّا
  مضافًا («فِي ذِي الدُّورِ») وقفٌ بلا رخصة.
- «ضَرَبَ الْوَلَدُ أَبَا» و«ضَرَبَ الْوَلَدُ ذَا» و«فِي ذِي» بلا مضافٍ إليه كانت «لا حكم» (`illaAkhir`) وتبقى: لا رخصةَ لمواضعها ولا وقف (شرطُ الإضافة،
  الألفية L79).
- وما كان ممتنعًا باقٍ: «ذَهَبَ أَبَوْ الْوَلَدِ» و«ذَهَبَ دَلْوْ الْوَلَدِ» و«ضَرَبَ الْوَلَدُ أَبُو الْوَلَدِ»؛ وما كان «لا حكم» بغير صور الجدول باقٍ: «ضَرَبَ
  الْفَتَى الْوَلَدَ» (`illaAkhir`؛ «الفتى» ليست من صور القوانين، ولا رخصةَ لموضعها ولا وقف). -/
theorem shawahid_sitta :
    hukm3 abuAlWalad = .laHukm ∧ asbabLaHukm abuAlWalad = [.irabBilHarf] ∧ hukmSitta abuAlWalad = .murakhkhas ∧
    [akhuK, hamuK, hanuK, fuK].all (fun w => hukm3 (dhahabaMudaf w) == .laHukm &&
      asbabLaHukm (dhahabaMudaf w) == [.irabBilHarf] && hukmSitta (dhahabaMudaf w) == .murakhkhas) ∧
    hukm3 (dhahabaMudaf dhuK) = .laHukm ∧ asbabLaHukm (dhahabaMudaf dhuK) = [.irabBilHarf] ∧ hukmSitta (dhahabaMudaf dhuK) = .laHukm ∧
    hukm3 { dhahabaAlWalad with kalimat := [dhahaba, dhuK] } = .mumtani ∧
    hukmSitta { dhahabaAlWalad with kalimat := [dhahaba, dhuK] } = .mumtani ∧
    [dhahabaMudaf daluK, dhahabaMudafAdad bunuK 0, dhahabaMudafAdad muslimuK 0].all (fun u =>
      hukm3 u == .laHukm && asbabLaHukm u == [.irabBilHarf] && hukmSitta u == .mumtani) ∧
    hukmSitta (dhahabaMudafAdad bunuK 2) = .laHukm ∧ asbabLaHukm (dhahabaMudafAdad bunuK 2) = [.ismGhayrMufrad] ∧
    hukmSitta (dhahabaMudafAdad muslimuK 2) = .laHukm ∧ asbabLaHukm (dhahabaMudafAdad muslimuK 2) = [.ismGhayrMufrad] ∧
    [darabaMudaf abaK, fiAfdalAdDur abiK].all (fun u =>
      hukm3 u == .laHukm && asbabLaHukm u == [.illaAkhir] && hukmSitta u == .murakhkhas) ∧
    hukm3 (dhahabaMudaf abaK) = .laHukm ∧ hukmSitta (dhahabaMudaf abaK) = .murakhkhas ∧
    hukm3 (dhahabaMudaf hanaK) = .laHukm ∧ hukmSitta (dhahabaMudaf hanaK) = .laHukm ∧
    hukm3 (darabaMudaf dhaK) = .laHukm ∧ asbabLaHukm (darabaMudaf dhaK) = [.illaAkhir] ∧ hukmSitta (darabaMudaf dhaK) = .laHukm ∧
    hukm3 (dhahabaMudaf abawK) = .mumtani ∧ hukmSitta (dhahabaMudaf abawK) = .mumtani ∧
    hukm3 (dhahabaMudaf dalwK) = .mumtani ∧ hukmSitta (dhahabaMudaf dalwK) = .mumtani ∧
    hukm3 (darabaMudaf abuK) = .mumtani ∧ hukmSitta (darabaMudaf abuK) = .mumtani ∧
    [darabaFata alWaladaK, { darabaFata alQadi with kalimat := [darabaK, alWalad, dhaK] }, { fiDar with kalimat := [fiK, dhiK] }].all (fun u =>
      hukm3 u == .laHukm && asbabLaHukm u == [.illaAkhir] && hukmSitta u == .laHukm) ∧
    (sitta.find? (·.ism == "هن")).map (·.qasr) = some false ∧ !suwar.contains alFata.khalaya ∧
    hukm3 { darabaFata alQadi with kalimat := [darabaK, alWalad, abaK] } = .laHukm ∧
    asbabLaHukm { darabaFata alQadi with kalimat := [darabaK, alWalad, abaK] } = [.illaAkhir] ∧
    hukmSitta { darabaFata alQadi with kalimat := [darabaK, alWalad, abaK] } = .laHukm := by decide +kernel

/-- مقارنةُ وجهين بنصّ الجدول: الأوّلُ أرجح (نعم)، أو الثاني (لا)، أو لا نصَّ (لا حكم). -/
def muqarana (s : Saff) (a b : Wajh) : Option Bool :=
  if s.daraja.any (fun x => x.1 == a && x.2.1 == b) then some true
  else if s.daraja.any (fun x => x.1 == b && x.2.1 == a) then some false else none

/-- **تعدّدُ الوجوه بدرجةٍ لا يغيّر الحكم** (على الشاهد): في «هن» النقصُ أرجحُ من التمام بلفظين («أحسن» الألفية L77، و«الأفصح» القطر L79–80)،
والوجهان مرخَّصان — «ذَهَبَ هَنُو الْوَلَدِ» بالجدول و«ذَهَبَ هَنُ الْوَلَدِ» بالقاعدة العامّة في `Utur` نفسِه («كغد»: بالحركات، قراءة البنّاء)؛
وفي «أب» القصرُ «أشهر» من النقص (L78)، والتمامُ والقصرُ لا نصَّ بينهما في الجدول: لا حكم. -/
theorem daraja_wujuh :
    (sitta.find? (·.ism == "هن")).map (fun s => (muqarana s .naqs .tamam, s.daraja.map (·.2.2))) =
      some (some true, ["أحسن", "الأفصح"]) ∧
    (sitta.find? (·.ism == "أب")).map (fun s => (muqarana s .qasr .naqs, muqarana s .tamam .qasr)) = some (some true, none) ∧
    hukmSitta (dhahabaMudaf hanuK) = .murakhkhas ∧ hukm3 (dhahabaMudaf hanuDamma) = .murakhkhas := by decide +kernel

end QawaidSitta
end Jisr
