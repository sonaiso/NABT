/-
# التوليد من النواة: العواملُ السبعةُ على الجذر، والعقدةُ وشروطُها الموروثة، والحكمُ على الجنس فيها

**الطلب.** رسالةُ المالك 2026-11-17 «لبناء المولّد المعجمي والمنطقي»: «يعمل الجذر الثلاثي كمتغير أساسي، وتعمل الأوزان الصرفية كـ دوال
رياضية (Operators) تُولّد الكلمة وتربطها تلقائياً بعقدها الأنطولوجية … مع توريث شروط وقابليات الجذر» (س11)؛ ثمّ «نفذ على أقوالي
المرقَّمة مصدرًا للنواة» (س27). وهي على ضابطٍ مجمَّد (`tahaqquq/dawabit/nawat_tawlid/wasf.md`): كُتبت هذه الشفرةُ قبل أن يقرأ البنّاءُ
الحالات. والأرقامُ (سN) أسطرُ `tahaqquq/dawabit/nawat_tawlid/masdar.md`.

**العوامل** (`Amil`، س14–س20): الفاعلية (فَاعِل)، والمفعولية (مَفْعُول)، والسببية (أَفْعَلَ)، والمطاوعة (انْفَعَلَ)، والزمان والمكان (مَفْعَل)،
والآلة (مِفْعَال)، والمبالغة (فَعَّال). **والصيغة** (`sigha`) بالهيكل وحدَه على صيغ شفرة المالك س20 (لا تشكيلَ إلّا شدّةَ فَعَّال)، ولجذرٍ
فيه حرفُ علّةٍ أو همزةٍ أو مضعَّفٍ لا صيغةَ (س25 توسعةٌ لاحقة؛ س29). **والعقدة** (`Uqda`، `wallid`) تحمل دورَها وشروطَها الموروثة وقيدَها
بقاعدة التوريث في شفرة المالك س21، وموانعَ جذرها.

**الحكمُ على الجنس في العقدة** (`hukmJins`، س33–س34): ممتنعٌ بمانعٍ ذي مفتاح (`Madlul.Nawat.maniMutahaqqiq`) أو بآلةٍ في غير الجماد
(س19، س32)؛ ومرخَّصٌ بآلةٍ في الجماد أو بتحقّق كلّ شروط العقدة ذوات المفتاح (`Madlul.Nawat.shartMutahaqqiq`)؛ ولا حكمَ فيما سوى ذلك (م13، س9).
**والحكمُ الكامل** (`hukm`): لا نواةَ لجذرٍ ليس فيها، ولا جنسَ لجنسٍ غائب (س28)، بترتيب س34.

**المبرهن:** الصيغةُ تحفظ حروفَ الجذر بترتيبها (`sigha_tahfaz_jadhr`)؛ والموروثُ من النواة لا من المعنى (`mawruth_min_nawat`)، والموانعُ موانعُ
الجذر (`mawani_min_jadhr`)؛ ولا حكمَ بلا نواة (`la_hukm_bila_nawat`)، ولا جنسَ بلا جنس (`la_jins_bila_jins`)؛ والآلةُ جمادٌ (`ala_ghayr_jamad_mumtani`)؛
ولا ترخيصَ إلّا بشاهد (`murakhkhas_bi_shahid`)، ولا امتناعَ إلّا بشاهد (`mumtani_bi_shahid`)؛ والترخيصُ لا يغيّر خواصَّ الجنس بالتوريث
(`murakhkhas_la_yughayyir`)؛ والشاهدُ على جذرَي النواة (`shahid_kasara`، `shahid_alima`).

**الحلقة** (التعلّمُ الذاتيّ بمعنى المالك س26: توسّعُ النواة بالبرهان لا بالتدريب): `satrMurashshah` يكتب صفَّ نواةٍ مرشَّحًا بصيغة المصدر
لجذرٍ شهده القارئ، ينتظر إمضاءَ المالك سطرًا مرقَّمًا؛ ولا يدخل النواةَ بلا إمضاء.
-/
import Madlul.Nawat

namespace Jisr
namespace Tawlid

open Madlul.Tayin Madlul.Nawat

/-- العواملُ السبعة بترتيب س14–س20. -/
inductive Amil
  | failiyya | mafuliyya | sababiyya | mutawaa | zamanMakan | ala | mubalagha
  deriving DecidableEq, Repr

def amilat : List Amil := [.failiyya, .mafuliyya, .sababiyya, .mutawaa, .zamanMakan, .ala, .mubalagha]

def ismAmil : Amil → String
  | .failiyya => "الفاعلية" | .mafuliyya => "المفعولية" | .sababiyya => "السببية" | .mutawaa => "المطاوعة"
  | .zamanMakan => "الزمان_والمكان" | .ala => "الآلة" | .mubalagha => "المبالغة"

/-- هيكلُ الصيغة حروفًا (س20): فَاعِل، مَفْعُول، أَفْعَلَ، انْفَعَلَ، مَفْعَل، مِفْعَال، فَعَّال. -/
def hurufSigha (a : Amil) (c1 c2 c3 : Char) : List Char :=
  match a with
  | .failiyya => [c1, 'ا', c2, c3]
  | .mafuliyya => ['م', c1, c2, 'و', c3]
  | .sababiyya => ['أ', c1, c2, c3]
  | .mutawaa => ['ا', 'ن', c1, c2, c3]
  | .zamanMakan => ['م', c1, c2, c3]
  | .ala => ['م', c1, c2, 'ا', c3]
  | .mubalagha => [c1, c2, 'ّ', 'ا', c3]

/-- حرفٌ صحيح: لا واو ولا ياء ولا همزة (س29). -/
def sahih (c : Char) : Bool := !['و', 'ي', 'ء', 'أ', 'إ', 'آ'].contains c

/-- الجذرُ تُصاغ منه: حروفُه صحيحة وعينُه غيرُ لامه (س29). -/
def yusagh (s : SaffJadhr) : Bool := sahih s.c1 && sahih s.c2 && sahih s.c3 && s.c2 != s.c3

/-- الصيغة: هيكلًا للجذر الصحيح، ولا صيغةَ لغيره (س25، س29). -/
def sigha (a : Amil) (s : SaffJadhr) : Option String :=
  if yusagh s then some (String.ofList (hurufSigha a s.c1 s.c2 s.c3)) else none

/-- العقدةُ المولَّدة (س13): صيغتُها ودورُها وشروطُها الموروثة وقيدُها وموانعُها. -/
structure Uqda where
  sigha : Option String
  dawr : Amil
  mawruth : List Shart
  qayd : Option Qayd
  mawani : List Mani
  deriving DecidableEq, Repr

/-- قاعدةُ التوريث (س21): الفاعليةُ والمبالغةُ والسببية ⇐ شروطُ الفاعل بلا قيد؛ والمفعوليةُ والمطاوعة ⇐ شروطُ المفعول وقيدُ الجذر؛
والآلة ⇐ المادية والصلابة النسبية وقيدُها صلب؛ والزمان والمكان ⇐ التحيّز بلا قيد. -/
def mawruthQayd (a : Amil) (s : SaffJadhr) : List Shart × Option Qayd :=
  match a with
  | .failiyya | .mubalagha | .sababiyya => (s.shurutFail, none)
  | .mafuliyya | .mutawaa => (s.shurutMafool, s.qayd)
  | .ala => ([.maddiyya, .salabaNisbiyya], some .sulb)
  | .zamanMakan => ([.tahayyuz], none)

/-- **المولّد** (س11، س13): عقدةُ العامل على صفّ الجذر. -/
def wallid (a : Amil) (s : SaffJadhr) : Uqda :=
  { sigha := sigha a s, dawr := a, mawruth := (mawruthQayd a s).1, qayd := (mawruthQayd a s).2, mawani := s.mawani }

/-- الحكمُ على الجنس في العقدة، والحكمُ الكامل. -/
inductive Hukm
  | murakhkhas | mumtani | laHukm | laNawat | laJins
  deriving DecidableEq, Repr

/-- س33–س34 بعد الجنس: الموانعُ ذاتُ المفتاح، ثمّ الآلة، ثمّ الشروطُ ذاتُ المفتاح. -/
def hukmJins (u : Uqda) (q : Qism) : Hukm :=
  if u.mawani.any (maniMutahaqqiq · q) then .mumtani
  else if u.dawr = .ala then (if q = .jamad then .murakhkhas else .mumtani)
  else if u.mawruth.all (shartMutahaqqiq · q) then .murakhkhas
  else .laHukm

/-- **الحكمُ الكامل** بترتيب س34: النواة، ثمّ الصيغةُ والموروث، ثمّ الجنس، ثمّ الحكمُ في العقدة. -/
def hukm (s : Option SaffJadhr) (a : Amil) (q : Option Qism) : Option Uqda × Hukm :=
  match s with
  | none => (none, .laNawat)
  | some s =>
    let u := wallid a s
    match q with
    | none => (some u, .laJins)
    | some q => (some u, hukmJins u q)

/-- بالمفتاح من النواة. -/
def hukmMiftah (k : String) (a : Amil) (q : Option Qism) : Option Uqda × Hukm := hukm (saff k) a q

/-! ## المبرهن -/

/-- **الصيغةُ تحفظ حروفَ الجذر بترتيبها** في كلّ عامل (س12، س20). -/
theorem sigha_tahfaz_jadhr (a : Amil) (c1 c2 c3 : Char) : [c1, c2, c3].Sublist (hurufSigha a c1 c2 c3) := by
  cases a <;> simp [hurufSigha] <;> first
    | exact (List.Sublist.refl _)
    | (repeat first | exact List.Sublist.cons₂ _ (by repeat first | exact List.Sublist.refl _ | exact List.Sublist.cons _ ‹_› | exact List.Sublist.cons₂ _ ‹_› | skip)
                    | exact List.Sublist.cons _ (by repeat first | exact List.Sublist.refl _ | exact List.Sublist.cons _ ‹_› | exact List.Sublist.cons₂ _ ‹_› | skip)
                    | skip)
    | (apply List.Sublist.cons₂; apply List.Sublist.cons₂; apply List.Sublist.cons; exact List.Sublist.refl _)

/-- **الموروثُ من النواة لا من المعنى** (س21): شروطُ الفاعل، أو شروطُ المفعول، أو ثابتا الآلة والوعاء. -/
theorem mawruth_min_nawat (a : Amil) (s : SaffJadhr) :
    (wallid a s).mawruth = s.shurutFail ∨ (wallid a s).mawruth = s.shurutMafool ∨
    (wallid a s).mawruth = [.maddiyya, .salabaNisbiyya] ∨ (wallid a s).mawruth = [.tahayyuz] := by
  cases a <;> simp [wallid, mawruthQayd]

/-- **الموانعُ موانعُ الجذر** في كلّ عقدة (س21: preventers=seed.preventers). -/
theorem mawani_min_jadhr (a : Amil) (s : SaffJadhr) : (wallid a s).mawani = s.mawani := rfl

/-- **القيدُ لا يُورَّث للفاعل** (س21: «الفاعل لا يُشترط فيه نفس الحالة الفيزيائية للمفعول»). -/
theorem fail_bila_qayd (s : SaffJadhr) :
    (wallid .failiyya s).qayd = none ∧ (wallid .mubalagha s).qayd = none ∧ (wallid .sababiyya s).qayd = none := by
  simp [wallid, mawruthQayd]

/-- **لا حكمَ بلا نواة** (س28): جذرٌ ليس في النواة لا عقدةَ له ولا حكم. -/
theorem la_hukm_bila_nawat (a : Amil) (q : Option Qism) : hukm none a q = (none, .laNawat) := rfl

/-- **لا جنسَ بلا جنس** (س28): العقدةُ تُولَّد والحكمُ «لا_جنس». -/
theorem la_jins_bila_jins (a : Amil) (s : SaffJadhr) : hukm (some s) a none = (some (wallid a s), .laJins) := rfl

/-- **الآلةُ جمادٌ** (س19، س32): في غير الجماد ممتنعةٌ أيًّا كان الجذر. -/
theorem ala_ghayr_jamad_mumtani (s : SaffJadhr) (q : Qism) (h : q ≠ .jamad) : hukmJins (wallid .ala s) q = .mumtani := by
  simp [hukmJins, wallid, h]

/-- **لا ترخيصَ إلّا بشاهد** (م13): المرخَّصُ إمّا آلةٌ في الجماد، وإمّا عقدةٌ كلُّ شروطها ذاتُ مفتاحٍ متحقّقةٌ في الجنس؛ ولا مانعَ فيها. -/
theorem murakhkhas_bi_shahid (u : Uqda) (q : Qism) (h : hukmJins u q = .murakhkhas) :
    u.mawani.any (maniMutahaqqiq · q) = false ∧
    ((u.dawr = .ala ∧ q = .jamad) ∨ (u.dawr ≠ .ala ∧ u.mawruth.all (shartMutahaqqiq · q) = true)) := by
  unfold hukmJins at h
  split at h
  · exact absurd h (by decide)
  · rename_i hm
    refine ⟨by simpa using hm, ?_⟩
    split at h
    · rename_i ha; split at h
      · exact Or.inl ⟨ha, ‹_›⟩
      · exact absurd h (by decide)
    · rename_i ha; split at h
      · exact Or.inr ⟨ha, ‹_›⟩
      · exact absurd h (by decide)

/-- **لا امتناعَ إلّا بشاهد** (م13، س9): الممتنعُ إمّا بمانعٍ ذي مفتاحٍ متحقّق، وإمّا آلةٌ في غير الجماد. -/
theorem mumtani_bi_shahid (u : Uqda) (q : Qism) (h : hukmJins u q = .mumtani) :
    u.mawani.any (maniMutahaqqiq · q) = true ∨ (u.dawr = .ala ∧ q ≠ .jamad) := by
  unfold hukmJins at h
  split at h
  · exact Or.inl ‹_›
  · split at h
    · rename_i ha; split at h
      · exact absurd h (by decide)
      · exact Or.inr ⟨ha, ‹_›⟩
    · split at h <;> exact absurd h (by decide)

/-- **الشرطُ بلا مفتاحٍ يمنع الترخيصَ** في غير الآلة (م13): عقدةٌ فيها شرطٌ بلا مفتاح لا تُرخَّص لجنس. -/
theorem bila_miftah_la_tarkhis (u : Uqda) (q : Qism) (hd : u.dawr ≠ .ala) (s : Shart) (hs : s ∈ u.mawruth)
    (hm : miftahShart s = none) : hukmJins u q ≠ .murakhkhas := by
  intro h
  rcases murakhkhas_bi_shahid u q h with ⟨_, hc | ⟨_, hall⟩⟩
  · exact hd hc.1
  · have := List.all_eq_true.1 hall s hs
    rw [bila_miftah_la_yatahaqqaq s q hm] at this
    exact Bool.false_ne_true this

/-- **الترخيصُ لا يغيّر خواصَّ الجنس بالتوريث:** لكلّ عقدةٍ من النواة مرخَّصةٍ لجنس، توريثُ فصول شروطها على خواصّ الجنس يعيدها
(`Madlul.Wiratha.warrith`؛ فالشروطُ «نعم» في الجنس أصلًا، `Madlul.Nawat.shart_mutahaqqiq_wiratha`). -/
theorem murakhkhas_la_yughayyir (u : Uqda) (q : Qism) (h : hukmJins u q = .murakhkhas) (hd : u.dawr ≠ .ala) :
    ∀ s ∈ u.mawruth, Madlul.Wiratha.warrith (fusul q) (faslShart s) = fusul q := by
  intro s hs
  rcases murakhkhas_bi_shahid u q h with ⟨_, hc | ⟨_, hall⟩⟩
  · exact absurd hc.1 hd
  · exact shart_mutahaqqiq_wiratha s q (List.all_eq_true.1 hall s hs)

/-! ## الشاهد على جذرَي النواة -/

/-- **ك-س-ر** (س22، س24): الصيغُ السبع بلفظ المالك «كاسر، مكسور، أكسر، انكسر، مكسر، مكسار، كسّار»؛ ولا ترخيصَ في عقدةٍ غيرِ الآلة
لجنس (قوة_مؤثرة والمادية والتحيّز بلا مفتاح)، والآلةُ مرخَّصةٌ للجماد وحدَه، ولا امتناعَ بمانع (موانعُه بلا مفتاح). -/
theorem shahid_kasara :
    amilat.map (fun a => (wallid a kasara).sigha) =
      [some "كاسر", some "مكسور", some "أكسر", some "انكسر", some "مكسر", some "مكسار", some "كسّار"] ∧
    (amilat.filter (· != .ala)).all (fun a => [Qism.jamad, .nabat, .hayawan, .insan].all (fun q => hukmJins (wallid a kasara) q == .laHukm)) = true ∧
    [Qism.jamad, .nabat, .hayawan, .insan].map (hukmJins (wallid .ala kasara)) = [.murakhkhas, .mumtani, .mumtani, .mumtani] := by
  decide +kernel

/-- **ع-ل-م** (س23): الصيغُ السبع على صيغ س20؛ والفاعليةُ والمبالغةُ والسببية مرخَّصةٌ للإنسان (الحياةُ والعقلُ والإدراك «نعم»، س6) ولا حكمَ
في النبات (العقلُ لا يُسأل عنه، س8) وممتنعةٌ في الحيوان (انعدام_العقل، س5) والجماد (الجمود_المطلق، س3)؛ والآلةُ في الجماد ممتنعةٌ بالمانع
قبل الرخصة (س34). -/
theorem shahid_alima :
    amilat.map (fun a => (wallid a alima).sigha) =
      [some "عالم", some "معلوم", some "أعلم", some "انعلم", some "معلم", some "معلام", some "علّام"] ∧
    [Amil.failiyya, .mubalagha, .sababiyya].all (fun a =>
      [Qism.jamad, .nabat, .hayawan, .insan].map (hukmJins (wallid a alima)) == [.mumtani, .laHukm, .mumtani, .murakhkhas]) = true ∧
    [Qism.jamad, .nabat, .hayawan, .insan].map (hukmJins (wallid .ala alima)) = [.mumtani, .mumtani, .mumtani, .mumtani] ∧
    [Qism.jamad, .nabat, .hayawan, .insan].map (hukmJins (wallid .mafuliyya alima)) = [.mumtani, .laHukm, .mumtani, .laHukm] := by
  decide +kernel

/-- جذرٌ خارج النواة: لا نواة (س28). -/
theorem shahid_kharij : hukmMiftah "ذ-ه-ب" .failiyya (some .insan) = (none, .laNawat) := by decide +kernel

/-! ## الحلقة: صفٌّ مرشَّحٌ للنواة -/

/-- **صفُّ نواةٍ مرشَّح** بصيغة المصدر لجذرٍ شهده القارئ لجنسٍ مودَع: ينتظر إمضاءَ المالك سطرًا مرقَّمًا، ولا يدخل النواةَ قبله (س26، س27).
لا شروطَ ولا موانعَ تُستنتج من المعنى: الصفُّ المرشَّحُ خالٍ منها حتى يملأه المالك. -/
def satrMurashshah (jadhr : String) (q : Qism) : String :=
  s!"N. [مرشَّح، ينتظر إمضاء المالك] نواةُ الجذر ({jadhr}) شُهد مسندًا إلى {ismQism q} (س{satrQism q})؛ agent_requirements=\{}، patient_requirements=\{}، required_physical_state=None، preventers=\{}."
where ismQism : Qism → String | .jamad => "جماد" | .nabat => "نبات" | .hayawan => "حيوان" | .insan => "إنسان"

/-- الصفُّ المرشَّح لا يدخل النواة: النواةُ ثابتةٌ على صفّيها (س22، س23) حتى يُزاد سطرٌ مرقَّم. -/
theorem murashshah_la_yadkhul : nawat.length = 2 := rfl

end Tawlid
end Jisr
