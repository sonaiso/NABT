/-
  Madlul/Wiratha.lean — قانونُ التوريث والوراثة على شجرة الأجناس، وفق نظام التعيين والتمييز.

  قرارُ المالك (2026-10-16، 13:19): «… وقانون التوريث والوراثة وفق نظام التعيين والتمييز …»؛ وإمضاؤه (13:26) لقراءة البنّاء:
  (1) **التوريثُ نزولًا**: الجنسُ الأعلى يورّث تعيينَه (خواصَّه) كلَّ ما تحته؛ **والوراثةُ صعودًا**: النوعُ يرث ويزيد فصلَه (التمييز)؛
  **والفصلُ لا يبتّ إلّا فيما تركه الجنسُ «لا حكم» ولا يناقضه** — فالوراثةُ تحسينٌ (`Tayin.yuhassin`)، وعلى الخانات الخمس
  التحسينُ وراثةٌ بفصلٍ (`tahsin_wiratha`؛ والقابليّاتُ خارج `yuhassin` تُجمع).
  (2) **عُقَدُ الآباء**: صفُّ «حيوان» في القطعة الأولى نوعٌ (غيرُ العاقل، العقل «لا») لا جنس؛ فجنسُ الإنسان الأعلى «الحيوان» عقدةٌ بعقلٍ
  «لا حكم» يرثها الأخوان (الحيوان غير العاقل والإنسان)، وكذلك «الحيّ» (أبو النبات والحيوان) و«الموجود» (الجذر).

  **الصورة.** `battQ`: بتُّ الفصل في خانة — ما بتّه الجنسُ يبقى، وما تركه «لا حكم» يبتّه الفصل. `warrith ab fasl`: خواصُّ النوع من خواصّ
  جنسه وفصله خانةً خانة، والقابليّاتُ تُجمع (الموروثةُ ثمّ المزيدة). `Shajara N`: شجرةُ أجناسٍ على عُقَدٍ `N` (جنسٌ أعلى لكلّ عقدة أو
  لا شيء للجذر، وفصلٌ لكلّ عقدة)، و`Shajara.khawass k n`: خواصُّ العقدة بالتوريث نزولًا من الجذر (بوقودٍ `k` يحدّ العمق — فلا
  افتراضَ على انتهاء الشجرة).

  **المبرهنات (لكلّ جنسٍ وفصل):** `warrith_yuhassin` (الوراثةُ تحسين)، `tahsin_wiratha` (التحسينُ على الخانات الخمس وراثةٌ بفصل)،
  `warrith_la_yunaqid` (الفصلُ لا يناقض ما بتّه الجنس — على الخانات الخمس)، `warrith_yabutt` (الفصلُ يبتّ ما تُرك «لا حكم» — على
  الخمس)، `mawruth_yabqa` (ما صُنّف تحت جنسٍ يبقى تحته — بـ `tahsin_la_yughayyir`)،
  `warrith_farigh` (فصلٌ فارغ يعيد الجنسَ بعينه)، `yuhassin_refl`/`yuhassin_trans` (التحسينُ انعكاسيّ متعدٍّ: فالوراثةُ على
  السلسلة جدًّا فأبًا فابنًا تحسين)، `Shajara.wiratha` (على كلّ شجرة: خواصُّ العقدة تحسّن خواصَّ أبيها)، `Shajara.jidhr_thabit`
  (خواصُّ الجذر فصلُه مهما كان الوقود).
  **على الشاهد** (شجرةُ القطعتين `shajara` على `Uqda`: الموجود › الحيّ › {النبات، الحيوان-الجنس › {الحيوان، الإنسان}}، الموجود › الجماد):
  `fusul_min_wiratha` (الشجرةُ بفصولها المعيَّنة تعيد بالتوريث صفوفَ المودَع `Tayin.fusul` بعينها — مطابقةٌ على الشاهد: فصولُ الأوراق
  كتبها البنّاء بما يزيد على آبائها، فالمبرهنةُ تشهد اتّساقَ الشجرة مع القطعة الأولى لا اشتقاقَها منها)، `aba_bila_hukm` (عُقَدُ الآباء
  الثلاث «لا حكم» في التصنيف — لا قسمَ خامس: م5)، `ikhwan_bi_fasl` (الأخوان تحت الحيوان يفترقان في العقل وحده).

  الوسم: مبرهن (لكلّ): `battQ_yuhassin`، `warrith_yuhassin`، `battQ_yuhassinQ`، `tahsin_wiratha`، `battQ_la_yunaqid`، `warrith_la_yunaqid`،
  `battQ_yabutt`،
  `warrith_yabutt`، `mawruth_yabqa`، `battQ_laHukm`، `warrith_farigh`، `yuhassinQ_refl`، `yuhassinQ_trans`، `yuhassin_refl`،
  `yuhassin_trans`، `Shajara.wiratha`، `Shajara.jidhr_thabit`؛ مبرهن على الشاهد (decide على `shajara`): `fusul_min_wiratha`،
  `aba_bila_hukm`، `ikhwan_bi_fasl`. فصولُ عُقَد الآباء تعيينُ البنّاء (الحيّ = الحياةُ الثلاثيّة «نعم»؛ الحيوان-الجنس = الانتقالُ «نعم»؛
  الموجود = فصلٌ فارغ)، مودَعةٌ ومختومة في «جدول الأجناس — القطعة الثانية» (`ajnas_jamad.tsv`، `2e5477cd…`) بإذن المالك 2026-10-16،
  ومطابَقةٌ بـ `tahaqquq/test_jamad.py`.
-/
import Madlul.Tayin

set_option autoImplicit false

namespace Madlul
namespace Wiratha
open Tayin

/-- بتُّ الفصل في خانة: ما بتّه الجنسُ يبقى، وما تركه «لا حكم» يبتّه الفصل. -/
def battQ : Qima → Qima → Qima
  | .laHukm, f => f
  | a, _ => a

/-- **التوريث:** خواصُّ النوع من خواصّ جنسه الأعلى `ab` وفصله `fasl` — خانةً خانة بـ `battQ`، والقابليّاتُ تُجمع. -/
def warrith (ab fasl : Khawass) : Khawass :=
  { taghadhdhi := battQ ab.taghadhdhi fasl.taghadhdhi
    numuw := battQ ab.numuw fasl.numuw
    mawt := battQ ab.mawt fasl.mawt
    intiqal := battQ ab.intiqal fasl.intiqal
    aql := battQ ab.aql fasl.aql
    qab := ab.qab ++ fasl.qab }

theorem battQ_yuhassin (a f : Qima) : yuhassinQ a (battQ a f) := by
  cases a <;> simp [battQ, yuhassinQ]

/-- **الوراثةُ تحسين:** خواصُّ النوع تحسّن خواصَّ جنسه، لكلّ جنسٍ وفصل. -/
theorem warrith_yuhassin (ab fasl : Khawass) : yuhassin ab (warrith ab fasl) :=
  ⟨battQ_yuhassin _ _, battQ_yuhassin _ _, battQ_yuhassin _ _, battQ_yuhassin _ _, battQ_yuhassin _ _⟩

theorem battQ_la_yunaqid (a f : Qima) (h : a ≠ .laHukm) : battQ a f = a := by
  cases a <;> simp_all [battQ]

/-- **الفصلُ لا يناقض الجنس:** ما بتّه الجنسُ في خانة (غيرُ «لا حكم») يبقى بعينه في النوع — على الخانات الخمس. -/
theorem warrith_la_yunaqid (ab fasl : Khawass) :
    (ab.taghadhdhi ≠ .laHukm → (warrith ab fasl).taghadhdhi = ab.taghadhdhi) ∧
    (ab.numuw ≠ .laHukm → (warrith ab fasl).numuw = ab.numuw) ∧
    (ab.mawt ≠ .laHukm → (warrith ab fasl).mawt = ab.mawt) ∧
    (ab.intiqal ≠ .laHukm → (warrith ab fasl).intiqal = ab.intiqal) ∧
    (ab.aql ≠ .laHukm → (warrith ab fasl).aql = ab.aql) :=
  ⟨battQ_la_yunaqid _ _, battQ_la_yunaqid _ _, battQ_la_yunaqid _ _, battQ_la_yunaqid _ _, battQ_la_yunaqid _ _⟩

theorem battQ_yabutt (f : Qima) : battQ .laHukm f = f := rfl

/-- **الفصلُ يبتّ ما تُرك:** ما تركه الجنسُ «لا حكم» فقيمتُه في النوع قيمةُ الفصل — على الخانات الخمس. -/
theorem warrith_yabutt (ab fasl : Khawass) :
    (ab.taghadhdhi = .laHukm → (warrith ab fasl).taghadhdhi = fasl.taghadhdhi) ∧
    (ab.numuw = .laHukm → (warrith ab fasl).numuw = fasl.numuw) ∧
    (ab.mawt = .laHukm → (warrith ab fasl).mawt = fasl.mawt) ∧
    (ab.intiqal = .laHukm → (warrith ab fasl).intiqal = fasl.intiqal) ∧
    (ab.aql = .laHukm → (warrith ab fasl).aql = fasl.aql) := by
  refine ⟨fun h => ?_, fun h => ?_, fun h => ?_, fun h => ?_, fun h => ?_⟩ <;> simp [warrith, h, battQ]

theorem battQ_yuhassinQ {a b : Qima} (h : yuhassinQ a b) : battQ a b = b := by
  cases a <;> cases b <;> simp_all [battQ, yuhassinQ]

/-- **التحسينُ وراثة** (العكس، على الخانات الخمس): ما حسّن خواصَّ جنسٍ فهو وراثةٌ بفصلٍ هو المحسِّنُ نفسُه — فالوراثةُ والتحسينُ
سواءٌ على الخمس؛ والقابليّاتُ خارج `yuhassin` تُجمع في التوريث. -/
theorem tahsin_wiratha (ab k : Khawass) (h : yuhassin ab k) :
    let w := warrith ab { k with qab := [] }
    w.taghadhdhi = k.taghadhdhi ∧ w.numuw = k.numuw ∧ w.mawt = k.mawt ∧ w.intiqal = k.intiqal ∧ w.aql = k.aql := by
  obtain ⟨h1, h2, h3, h4, h5⟩ := h
  exact ⟨battQ_yuhassinQ h1, battQ_yuhassinQ h2, battQ_yuhassinQ h3, battQ_yuhassinQ h4, battQ_yuhassinQ h5⟩

/-- **ما صُنّف تحت جنسٍ يبقى تحته:** إن صُنّفت خواصُّ الجنس قسمًا فخواصُّ كلّ نوعٍ يرثه تُصنَّف القسمَ نفسه. -/
theorem mawruth_yabqa (ab fasl : Khawass) (q : Qism) (h : sannif ab = some q) :
    sannif (warrith ab fasl) = some q :=
  tahsin_la_yughayyir ab (warrith ab fasl) q h (warrith_yuhassin ab fasl)

theorem battQ_laHukm (a : Qima) : battQ a .laHukm = a := by cases a <;> rfl

/-- **فصلٌ فارغ** (كلُّه «لا حكم» بلا قابليّات) يعيد الجنسَ بعينه: التوريثُ لا يزيد شيئًا من عنده. -/
theorem warrith_farigh (ab : Khawass) : warrith ab {} = ab := by
  cases ab; simp [warrith, battQ_laHukm]

theorem yuhassinQ_refl (a : Qima) : yuhassinQ a a := by cases a <;> simp [yuhassinQ]

theorem yuhassinQ_trans {a b c : Qima} (h1 : yuhassinQ a b) (h2 : yuhassinQ b c) : yuhassinQ a c := by
  cases a <;> cases b <;> cases c <;> simp_all [yuhassinQ]

theorem yuhassin_refl (k : Khawass) : yuhassin k k :=
  ⟨yuhassinQ_refl _, yuhassinQ_refl _, yuhassinQ_refl _, yuhassinQ_refl _, yuhassinQ_refl _⟩

/-- التحسينُ متعدٍّ: فالوراثةُ على السلسلة (الجدّ فالأب فالابن) تحسين. -/
theorem yuhassin_trans {a b c : Khawass} (h1 : yuhassin a b) (h2 : yuhassin b c) : yuhassin a c := by
  obtain ⟨a1, a2, a3, a4, a5⟩ := h1
  obtain ⟨b1, b2, b3, b4, b5⟩ := h2
  exact ⟨yuhassinQ_trans a1 b1, yuhassinQ_trans a2 b2, yuhassinQ_trans a3 b3, yuhassinQ_trans a4 b4,
    yuhassinQ_trans a5 b5⟩

/-! ## الشجرة -/

/-- شجرةُ أجناس على عُقَدٍ `N`: لكلّ عقدةٍ جنسٌ أعلى (أو لا شيء للجذر) وفصلٌ تبتّه عن أبيها. -/
structure Shajara (N : Type) where
  ab : N → Option N
  fasl : N → Khawass

/-- خواصُّ العقدة بالتوريث نزولًا من الجذر؛ الوقودُ `k` يحدّ العمق (عقدةٌ أعمقُ من الوقود تُحسب من فصلها وما بلغه الوقود). -/
def Shajara.khawass {N : Type} (sh : Shajara N) : Nat → N → Khawass
  | 0, n => sh.fasl n
  | k + 1, n =>
    match sh.ab n with
    | none => sh.fasl n
    | some p => warrith (sh.khawass k p) (sh.fasl n)

/-- **قانونُ الوراثة على الشجرة:** خواصُّ كلّ عقدةٍ تحسّن خواصَّ أبيها — لكلّ شجرةٍ وكلّ وقود. -/
theorem Shajara.wiratha {N : Type} (sh : Shajara N) (k : Nat) (n p : N) (h : sh.ab n = some p) :
    yuhassin (sh.khawass k p) (sh.khawass (k + 1) n) := by
  simp only [Shajara.khawass, h]
  exact warrith_yuhassin _ _

/-- خواصُّ الجذر فصلُه مهما كان الوقود. -/
theorem Shajara.jidhr_thabit {N : Type} (sh : Shajara N) (k : Nat) (n : N) (h : sh.ab n = none) :
    sh.khawass k n = sh.fasl n := by
  cases k with
  | zero => rfl
  | succ k => simp only [Shajara.khawass, h]

/-! ## الشاهد: شجرةُ القطعتين -/

/-- عُقَدُ الشجرة: الجذرُ (الموجود)، وعُقَدُ الآباء (الحيّ، الحيوان-الجنس)، والأوراقُ الأربع (صفوفُ القطعة الأولى). -/
inductive Uqda | mawjud | hayy | jamad | nabat | hayawanJins | hayawan | insan
deriving DecidableEq, Repr

/-- قابليّاتُ الحركة الخمس (بقول المالك)، تُبتّ عند الحيوان-النوع والإنسان. -/
def qabHaraka : List QabHaraka := [.sayr, .rakd, .jary, .zahf, .qafz]

/-- شجرةُ القطعتين: الموجود › {الجماد، الحيّ › {النبات، الحيوان-الجنس › {الحيوان، الإنسان}}}. فصولُ عُقَد الآباء تعيينُ البنّاء
(الحيّ: الحياةُ الثلاثيّة «نعم»؛ الحيوان-الجنس: الانتقالُ «نعم»؛ الموجود: فصلٌ فارغ)؛ وفصولُ الأوراق ما تزيده على آبائها من
صفوف المودَع `ajnas.tsv`. -/
def shajara : Shajara Uqda :=
  { ab := fun
      | .mawjud => none
      | .hayy => some .mawjud
      | .jamad => some .mawjud
      | .nabat => some .hayy
      | .hayawanJins => some .hayy
      | .hayawan => some .hayawanJins
      | .insan => some .hayawanJins
    fasl := fun
      | .mawjud => {}
      | .hayy => { taghadhdhi := .naam, numuw := .naam, mawt := .naam }
      | .jamad => { taghadhdhi := .la, numuw := .la, intiqal := .la }
      | .nabat => { intiqal := .la }
      | .hayawanJins => { intiqal := .naam }
      | .hayawan => { aql := .la, qab := qabHaraka }
      | .insan => { aql := .naam, qab := qabHaraka } }

/-- عقدةُ كلّ قسمٍ من القطعة الأولى. -/
def uqdaOf : Qism → Uqda
  | .jamad => .jamad
  | .nabat => .nabat
  | .hayawan => .hayawan
  | .insan => .insan

/-- **القطعةُ الأولى مشتقّةٌ من الشجرة بالقانون:** خواصُّ الأوراق الأربع بالتوريث (بوقودٍ يبلغ الجذر) هي صفوفُ المودَع `fusul` بعينها. -/
theorem fusul_min_wiratha : ∀ q : Qism, shajara.khawass 3 (uqdaOf q) = fusul q := by
  intro q; cases q <;> decide

/-- **عُقَدُ الآباء «لا حكم» في التصنيف:** الموجودُ والحيُّ والحيوان-الجنس لا تُصنَّف قسمًا — لا قسمَ خامس، ولا يُستنتج قسمٌ من
غياب الفصل (م5). -/
theorem aba_bila_hukm :
    sannif (shajara.khawass 3 .mawjud) = none ∧ sannif (shajara.khawass 3 .hayy) = none ∧
    sannif (shajara.khawass 3 .hayawanJins) = none := by decide

/-- **الأخوان يفترقان بفصلٍ واحد** (المخصّص س252): الحيوانُ والإنسانُ تحت الحيوان-الجنس سواءٌ في الخواصّ الأربع والقابليّات،
ويفترقان في العقل وحده. -/
theorem ikhwan_bi_fasl :
    let h := shajara.khawass 3 .hayawan
    let i := shajara.khawass 3 .insan
    h.taghadhdhi = i.taghadhdhi ∧ h.numuw = i.numuw ∧ h.mawt = i.mawt ∧ h.intiqal = i.intiqal ∧ h.qab = i.qab ∧
    h.aql = .la ∧ i.aql = .naam := by decide

end Wiratha
end Madlul
