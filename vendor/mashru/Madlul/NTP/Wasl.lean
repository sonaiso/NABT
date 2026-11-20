/-
  Madlul/NTP/Wasl.lean — وصلُ معالج NTP (`Madlul/NTP/Muallij.lean`) بقاضي «الحمل من الجنس» في Mashru (`Jisr/QabiliyyaJins.lean`).

  الفجوةُ التي يسدّها (مقروءةٌ في الجلسة، لا منقولة): `Muallij.lean` يبني شبكةَ أجناسٍ متعدّدةَ الآباء مقبولةً بالتواتر، لكنّه لا يستورد
  `Madlul.Tayin.sannif` ولا `Jisr.QabiliyyaJins.hukmMujarrad`؛ فما تقرّره الشبكةُ لا يصل إلى الحكم على جملةٍ عربيّة («ذهب الولد»،
  «سار الحجر»). وفي Mashru قانونان للوراثة: `Madlul.Wiratha.warrith` (أبٌ واحد، خمسُ خانات) و`NTP.qima` (آباءٌ كثيرون، خانةٌ بالرقم)،
  ولا مبرهنةَ تقول إنّهما قانونٌ واحد.

  ما هنا (كلّه مبرهنٌ لكلّ شبكة إلّا §٤):
  ١. `khawassOf`: خواصُّ عقدة NTP في خانات `Tayin.Khawass` الخمس (أرقامُ الخانات تعيينٌ معلَن هنا).
  ٢. `khawassOf_warrith`: **وراثةُ NTP بأبٍ واحد هي `Wiratha.warrith` بعينها** — فالقانونان قانونٌ واحد.
  ٣. `tasnif_yuwarrath`: ما صُنّف أبوه قسمًا صُنّف هو القسمَ نفسه؛ و`hukm_yuwarrath`: **حكمُ الحمل يُورَّث** — فـ«ذهب الولد» مرخَّصٌ
     لأنّ الولد تحت الإنسان، بمبرهنةٍ على كلّ شبكة لا بقائمة.
  ٤. `la_tawatur_la_jins`: **بوّابةُ التواتر موصولةٌ بالقاضي**: عقدةٌ لم تدخل الشبكة (شاهدٌ من مصدرٍ واحد، أو فرعان متناقضان) لا يُحمل
     عليها شيء («لا جنس»).
  ٥. على الشاهد: شبكة `Muallij.shabakaShahid` المرفوعة لا تصل إلى القاضي (`shahid_marfu_la_yasil`: الإنسانُ فيها «لا جنس» لأنّ
     خاناتِ الحياة فيها «لا حكم»)؛ وشبكةٌ بخانات Tayin تُخرج: الولدُ يسير «مرخَّص»، والزيتونُ والحجرُ يسيران «لا حكم» (لا امتناع:
     الغيابُ ليس امتناعًا)، والإضافةُ «ممتنع»، والهجينُ «لا جنس»، وعقدةٌ تُصنَّف إنسانًا بشهود OpenCyc وحده «لا جنس».

  حدود: أرقامُ الشهود وجذورُ الألفاظ في §٥ تعيينُ البنّاء كما في Muallij (لا مودَع)؛ وقابليّاتُ الحركة تُؤخذ من القسم (`fusul q`) لا من
  العقدة؛ ومبرهنةُ التوريث لأبٍ واحد (والآباءُ المتعدّدون مبرهنٌ قانونُهم في Muallij: `warith_la_yunqad`، `fasl_yabutt`).
  بلا sorry ولا axiom ولا native_decide.
-/
import Madlul.NTP.Muallij
import Jisr.QabiliyyaJins

set_option autoImplicit false

namespace NTP
namespace Wasl

open Madlul.Tayin (Khawass Qism QabHaraka sannif)
open Jisr.QabiliyyaJins (HukmMujarrad hukmMujarrad)

/-! ## ١. خانات Tayin الخمس في شبكة NTP -/

/-- أرقامُ الخانات (تعيينٌ معلَن): الانتقالُ هو `NTP.pIntiqal` نفسُه (1)، والبقيّةُ أرقامٌ لا تصادم أرقامَ Muallij. -/
def pTaghadhdhi : Nat := 10
def pNumuw : Nat := 11
def pMawt : Nat := 12
def pAql : Nat := 14

/-- خواصُّ العقدة n بالوراثة (وقود k) في خانات `Tayin.Khawass`. -/
def khawassOf (sh : Shabaka) (k n : Nat) : Khawass :=
  { taghadhdhi := qima sh k n pTaghadhdhi
    numuw := qima sh k n pNumuw
    mawt := qima sh k n pMawt
    intiqal := qima sh k n pIntiqal
    aql := qima sh k n pAql }

/-- فصلُ العقدة في الخانات الخمس. -/
def faslK (sh : Shabaka) (n : Nat) : Khawass :=
  { taghadhdhi := sh.fasl n pTaghadhdhi
    numuw := sh.fasl n pNumuw
    mawt := sh.fasl n pMawt
    intiqal := sh.fasl n pIntiqal
    aql := sh.fasl n pAql }

/-! ## ٢. القانونان قانونٌ واحد -/

theorem damj_wahid (x : Madlul.Tayin.Qima) : damj [x] = x := by
  cases x <;> rfl

/-- بأبٍ واحد: قيمةُ الخانة بتُّ الفصل فيما تركه الأب. -/
theorem qima_ab_wahid (sh : Shabaka) (k n a p : Nat) (h : sh.aba n = [a]) :
    qima sh (k + 1) n p = Madlul.Wiratha.battQ (qima sh k a p) (sh.fasl n p) := by
  simp only [qima, h, List.map_cons, List.map_nil, damj_wahid]

/-- **وراثةُ NTP بأبٍ واحد هي `Wiratha.warrith` بعينها** على الخانات الخمس. -/
theorem khawassOf_warrith (sh : Shabaka) (k n a : Nat) (h : sh.aba n = [a]) :
    khawassOf sh (k + 1) n = Madlul.Wiratha.warrith (khawassOf sh k a) (faslK sh n) := by
  simp only [khawassOf, faslK, Madlul.Wiratha.warrith, qima_ab_wahid sh k n a _ h, List.append_nil]

/-! ## ٣. التصنيفُ والحكمُ يُورَّثان -/

/-- ما صُنّف أبوه قسمًا صُنّف هو القسمَ نفسه (عبر `Wiratha.mawruth_yabqa`). -/
theorem tasnif_yuwarrath (sh : Shabaka) (k n a : Nat) (h : sh.aba n = [a]) (q : Qism)
    (hq : sannif (khawassOf sh k a) = some q) : sannif (khawassOf sh (k + 1) n) = some q := by
  rw [khawassOf_warrith sh k n a h]
  exact Madlul.Wiratha.mawruth_yabqa _ _ q hq

/-- **حكمُ الحمل على عقدة NTP:** لا جنسَ لما لم يدخل الشبكة بالتواتر؛ وإلّا فقاضي Mashru على قسمها. -/
def hukm (sh : Shabaka) (K k n : Nat) (c : QabHaraka) (ns : Jisr.Nisab.Nisba) : HukmMujarrad :=
  if yadkhul sh K k n then hukmMujarrad (sannif (khawassOf sh k n)) (some c) ns else .laJins

/-- **بوّابةُ التواتر موصولةٌ بالقاضي:** ما لم يدخل الشبكة لا يُحمل عليه شيء. -/
theorem la_tawatur_la_jins (sh : Shabaka) (K k n : Nat) (c : QabHaraka) (ns : Jisr.Nisab.Nisba)
    (h : yadkhul sh K k n = false) : hukm sh K k n c ns = .laJins := by
  simp [hukm, h]

/-- **مصدرٌ واحدٌ (OpenCyc أو غيره) لا يُنتج حملًا** متى كانت العتبة اثنين فأكثر. -/
theorem cyc_la_yahmil (sh : Shabaka) (K k n : Nat) (hK : 2 ≤ K) (h : ∀ s ∈ sh.shuhud n, s.masdar = cyc)
    (c : QabHaraka) (ns : Jisr.Nisab.Nisba) : hukm sh K k n c ns = .laJins := by
  apply la_tawatur_la_jins
  simp [yadkhul, cyc_wahdahu_la_yudkhil K hK _ h]

/-- **الحكمُ يُورَّث:** عقدةٌ دخلت الشبكة وأبوها الواحدُ مصنَّفٌ q فحكمُ الحمل عليها حكمُ القسم q. -/
theorem hukm_yuwarrath (sh : Shabaka) (K k n a : Nat) (h : sh.aba n = [a]) (hd : yadkhul sh K (k + 1) n = true)
    (q : Qism) (hq : sannif (khawassOf sh k a) = some q) (c : QabHaraka) (ns : Jisr.Nisab.Nisba) :
    hukm sh K (k + 1) n c ns = hukmMujarrad (some q) (some c) ns := by
  simp [hukm, hd, tasnif_yuwarrath sh k n a h q hq]

/-- بالنسبة الإسناديّة: مرخَّصٌ إن كانت القابليّةُ في فصول قسم الأب، وإلّا لا حكم — ولا امتناع. -/
theorem tarkhis_yuwarrath (sh : Shabaka) (K k n a : Nat) (h : sh.aba n = [a]) (hd : yadkhul sh K (k + 1) n = true)
    (q : Qism) (hq : sannif (khawassOf sh k a) = some q) (c : QabHaraka) :
    hukm sh K (k + 1) n c .isnadiyya =
      if c ∈ (Madlul.Tayin.fusul q).qab then .murakhkhas else .laHukm := by
  rw [hukm_yuwarrath sh K k n a h hd q hq, Jisr.QabiliyyaJins.hukmMujarrad_isnadiyya]

/-! ## ٤. الشبكةُ المرفوعة لا تصل -/

/-- في `shabakaShahid` خاناتُ الحياة «لا حكم»، فالإنسانُ لا يُصنَّف، والحملُ عليه «لا جنس»: المعالجُ والقاضي منفصلان. -/
theorem shahid_marfu_la_yasil : hukm shabakaShahid 2 4 nIns .sayr .isnadiyya = .laJins := by decide

/-! ## ٥. شبكةٌ بخانات Tayin (تعيينُ البنّاء، لا مودَع) -/

def jWalad : List Nat := [28, 13, 17]  -- و ل د
def jHajar : List Nat := [4, 9, 15]    -- ح ج ر

theorem judhur_wasl_murakhkhasa : [jWalad, jHajar].all (fun r => (raqmJins r).isSome) = true := by decide

def nWalad := Madlul.Fard116.ramz jWalad
def nHajar := Madlul.Fard116.ramz jHajar
/-- عقدةٌ مفترضةٌ تحت الإنسان شهودُها من OpenCyc وحده: فرعُها سليم، ولا تواتر — تفصل أثرَ بوّابة التواتر عن أثر التصنيف. -/
def nCycIns : Nat := 3

theorem arqam_wasl_mutamayyiza :
    [nWujud, nHayy, nJamad, nNabat, nZayt, nIns, nMa, nWalad, nHajar, nHajin, nCycIns].eraseDups.length = 11 := by decide

def shabakaWasl : Shabaka where
  aba n :=
    if n = nHayy ∨ n = nJamad then [nWujud]
    else if n = nNabat ∨ n = nIns then [nHayy]
    else if n = nZayt then [nNabat]
    else if n = nMa ∨ n = nHajar then [nJamad]
    else if n = nWalad ∨ n = nCycIns then [nIns]
    else if n = nHajin then [nZayt, nMa]
    else []
  ras n := if n = nHayy then some .hayy else if n = nJamad then some .jamad else none
  fasl n p :=
    if n = nHayy ∧ (p = pTaghadhdhi ∨ p = pNumuw ∨ p = pMawt) then .naam
    else if n = nJamad ∧ (p = pTaghadhdhi ∨ p = pNumuw ∨ p = pIntiqal) then .la
    else if n = nNabat ∧ p = pIntiqal then .la
    else if n = nIns ∧ (p = pIntiqal ∨ p = pAql) then .naam
    else .laHukm
  shuhud n :=
    if n = nHajin then [⟨cyc, "opencyc:Hajin"⟩, ⟨cyc, "opencyc:Hajin-2"⟩]
    else if n = nCycIns then [⟨cyc, "opencyc:CycIns"⟩, ⟨cyc, "opencyc:CycIns-2"⟩, ⟨cyc, "opencyc:CycIns-3"⟩]
    else [⟨1, "mukhassas"⟩, ⟨2, "lisan"⟩, ⟨3, "maqayis"⟩]

/-- التصنيف: الولدُ إنسان (ورثه من الإنسان فالحيّ)، والزيتونُ نبات، والحجرُ والماءُ جماد. -/
theorem wasl_tasnif :
    sannif (khawassOf shabakaWasl 4 nWalad) = some .insan ∧
    sannif (khawassOf shabakaWasl 4 nZayt) = some .nabat ∧
    sannif (khawassOf shabakaWasl 4 nHajar) = some .jamad ∧
    sannif (khawassOf shabakaWasl 4 nMa) = some .jamad ∧
    sannif (khawassOf shabakaWasl 4 nCycIns) = some .insan := by decide

/-- **من الشبكة إلى الجملة:** «سار الولد» مرخَّص، و«سار الزيتون» و«سار الحجر» لا حكم (لا امتناع، فبابُ المجاز مفتوحٌ لقاضيه)،
    والإضافةُ ممتنعة، والهجينُ (شاهدا OpenCyc وحدَه، وفرعاه متناقضان) لا جنس؛ وعقدةٌ تُصنَّف إنسانًا بشهود OpenCyc وحده
    لا جنس — فالحاجزُ هنا التواترُ لا التصنيف. -/
theorem wasl_hukm :
    hukm shabakaWasl 2 4 nWalad .sayr .isnadiyya = .murakhkhas ∧
    hukm shabakaWasl 2 4 nZayt .sayr .isnadiyya = .laHukm ∧
    hukm shabakaWasl 2 4 nHajar .sayr .isnadiyya = .laHukm ∧
    hukm shabakaWasl 2 4 nWalad .sayr .idafiyya = .mumtani ∧
    hukm shabakaWasl 2 4 nHajin .sayr .isnadiyya = .laJins ∧
    hukm shabakaWasl 2 4 nCycIns .sayr .isnadiyya = .laJins := by decide

end Wasl
end NTP
