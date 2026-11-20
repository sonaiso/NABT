import A116.Fiber
import A116.Numbering
import A116.Hadd

/-!
# عددُ الشهادة n: الذرّاتُ ورتبةُ الليف معًا، والخاناتُ وحدَها تُسقط الرتبة

الشهادةُ في البوّابة (`gate.contextual.Codebook.encode`) عددٌ واحد ‎n = P(F(atoms), rank)‎: رقمُ الذرّات
بترتيب الجسر (`Numbering.atomNumber`) مقترنًا بكانتور (`Numbering.pair`) برتبة الكلمة في ليف ذرّاتها من
المجال المختوم (`Fiber.rank`). هنا يُبرهَن:

* `certNumber_injective`: كلمتان من المجال بعددٍ واحدٍ هما واحدة — لكلّ مجالٍ منتهٍ بلا تكرار ولكلّ إسقاط.
* `certNumber_decode`: العددُ يردّ الكلمةَ بعينها (ذرّاتُه ورتبتُه ← الليف ← الكلمة).
* `cells_forget_rank`: الإسقاطُ إلى الخانات وحدَها ليس تباينًا متى كان في المجال ليفٌ بحجمٍ ≥ 2 — فما يقرأ
  الخاناتِ وحدَها يرى كلمتين كلمةً واحدة.
* `ala_alaa`: الشاهد — «عَلَا» و«عَلَى» ذرّاتُهما واحدة (عَ لَ اْ) ورتبتاهما في الليف 0 و1 بترتيب UTF-8
  (ا U+0627 قبل ى U+0649)، فعدداهما مختلفان؛ مبرهَنٌ على الشاهد. وفرقُ العددين ‎u + 2‎ لكلّ رقم ذرّاتٍ
  ‎u‎ (`pair_rank_one`)؛ وقيمتُه على البوّابة (‎u = 938,904‎، فالفرقُ 938,906) مفحوصةٌ في
  `tests/test_certificates.py` — لا يُحسب العددُ الكبير في النواة.

ما ليس هنا — باسمه: الإسقاطُ نفسُه من الرسم إلى الذرّات (`gate.bridge`) مطابَقٌ للجداول لا مبرهَن، وترتيبُ
الليف UTF-8 تعريفٌ في البوّابة يُفحص في `tests/test_certificates.py`.
-/

namespace A116.Certificate

open A116.Fiber A116.Numbering

variable {α : Type} [DecidableEq α]

/-- عددُ الشهادة: ‎P(F(A x), rank D A x)‎. -/
def certNumber (D : List α) (A : α → List Cell) (x : α) : Nat :=
  pair (atomNumber (A x)) (rank D A x)

/-- **التباين:** لكلّ مجالٍ ولكلّ إسقاط، كلمتان من المجال بعددٍ واحدٍ هما واحدة. -/
theorem certNumber_injective {D : List α} {A : α → List Cell} {x y : α} (hx : x ∈ D) (hy : y ∈ D)
    (h : certNumber D A x = certNumber D A y) : x = y := by
  obtain ⟨h1, h2⟩ := pair_injective h
  have ha := atomNumber_injective h1
  exact encode_injective (D := D) (A := A) hx hy (by simp only [encode, ha, h2])

/-- **الاستعادة:** العددُ يردّ الكلمةَ بعينها من الليف. -/
theorem certNumber_decode {D : List α} {A : α → List Cell} {x : α} (hx : x ∈ D) :
    Fiber.decode D A (A x, rank D A x) = some x :=
  decode_encode hx

/-- **الخاناتُ وحدَها تُسقط الرتبة:** متى كان في المجال كلمتان مختلفتان بذرّاتٍ واحدة فلا دالّةَ على
الذرّات وحدَها تفرّقهما، والعددُ يفرّقهما. -/
theorem cells_forget_rank {D : List α} {A : α → List Cell} {x y : α} (hx : x ∈ D) (hy : y ∈ D)
    (hxy : x ≠ y) (hA : A x = A y) :
    (∀ f : List Cell → Nat, f (A x) = f (A y)) ∧ certNumber D A x ≠ certNumber D A y :=
  ⟨fun f => by rw [hA], fun h => hxy (certNumber_injective hx hy h)⟩

/-! ## الشاهد: عَلَا / عَلَى -/

/-- ذرّاتُ الكلمتين كما تطبعها البوّابة: عَ لَ اْ. -/
def alaAtoms : List Cell := [Ladder.atom 'ع' .fatha, Ladder.atom 'ل' .fatha, Ladder.atom 'ا' .sukun]

/-- مجالٌ من كلمتين بترتيب UTF-8: 0 = عَلَا (بالألف القائمة)، 1 = عَلَى (بالمقصورة). -/
def alaDomain : List Nat := [0, 1]

def alaProj : Nat → List Cell := fun _ => alaAtoms

/-- الرتبتان تفصلهما ‎u + 2‎ لكلّ رقم ذرّاتٍ ‎u‎: ‎P(u, 1) = P(u, 0) + u + 2‎. -/
theorem pair_rank_one (u : Nat) : pair u 1 = pair u 0 + u + 2 := by
  simp only [pair, Nat.add_zero, tri]

/-- رتبةُ عَلَا (بالألف القائمة) في ليفها صفر. -/
theorem rank_ala0 : rank alaDomain alaProj 0 = 0 := by decide
/-- رتبةُ عَلَى (بالألف المقصورة) في ليفها واحد. -/
theorem rank_ala1 : rank alaDomain alaProj 1 = 1 := by decide

/-- **الشاهد:** عَلَا وعَلَى ذرّاتٌ واحدة، ورتبتان 0 و1، وعددان مختلفان. -/
theorem ala_alaa :
    alaProj 0 = alaProj 1 ∧ rank alaDomain alaProj 0 = 0 ∧ rank alaDomain alaProj 1 = 1 ∧
    certNumber alaDomain alaProj 0 ≠ certNumber alaDomain alaProj 1 :=
  ⟨rfl, rank_ala0, rank_ala1,
    fun h => absurd (certNumber_injective (by decide) (by decide) h) (by decide)⟩

end A116.Certificate
