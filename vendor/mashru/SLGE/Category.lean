import SLGE.MadlulAwwalan

/-!
# الكلمةُ اسمٌ وفعلٌ وحرف، والتركيبُ اسميٌّ وفعليٌّ وشبهُ جملة — ثلاثةٌ لا رابع

**ما هو وسيطٌ معلَن (من المدلول لا من الدالّ):** خاصّتان لكلّ كلمة:
* ‎ind‎: تدلّ على معنًى في نفسها؛
* ‎tim‎: يقترن معناها بأحد الأزمنة الثلاثة.

**قانونُ الدور في الإسناد (معلَن):** المسنَدُ يقتضي معنًى في نفسه (‎canM = ind‎)، والمسنَدُ إليه يقتضي
معنًى في نفسه غيرَ مقترنٍ بزمان (‎canMI = ind ∧ ¬tim‎).

**ما يُبرهَن:**
* صورُ الدور الممكنة ثلاث: ‎(—,—)‎ الحرف، ‎(—,م)‎ الفعل، ‎(م إليه, م)‎ الاسم؛ والرابعة ‎(م إليه, —)‎ ممتنعة.
* التركيبُ التامّ إمّا فيه إسنادٌ — وصدرُه ذو دور، فهو اسمٌ (جملةٌ اسمية) أو فعلٌ (جملةٌ فعلية)، لأنّ الحرف
  لا دور له — وإمّا لا إسنادَ فيه ويتعلّق بمسنَدٍ مقدَّر (شبهُ جملة). فالتراكيبُ ثلاثةٌ لا رابع.

وقد أثبت الشاهدُ على المصحف (Exclusive، أربعُ كلماتٍ متجانسة) أنّ الدالَّ وحده لا يعيّن القسم؛
فالقسمُ دالٌّ مع وضعه، وهذا معنى أنّ ‎ind‎ و‎tim‎ من المدلول.
-/

namespace SLGE
namespace Cat

/-- الدورُ في الإسناد: (يصلح مسنَدًا إليه، يصلح مسنَدًا). -/
def roles (ind tim : Bool) : Bool × Bool := (ind && !tim, ind)

/-- **ثلاثٌ لا رابع:** الصورُ التي يبلغها قانونُ الدور هي هذه الثلاث بعينها. -/
theorem three_roles : ∀ x : Bool × Bool,
    (∃ ind tim, roles ind tim = x) ↔ x = (false, false) ∨ x = (false, true) ∨ x = (true, true) := by
  intro x; rcases x with ⟨a, b⟩
  cases a <;> cases b <;> simp [roles, Bool.exists_bool]

/-- **الرابعةُ ممتنعة:** ما صلح مسنَدًا إليه صلح مسنَدًا. -/
theorem no_fourth (ind tim : Bool) : roles ind tim ≠ (true, false) := by
  cases ind <;> cases tim <;> decide

inductive Kind | ism | fil | harf
  deriving DecidableEq, Repr

/-- القسمُ من الدور. -/
def kindOf : Bool × Bool → Kind
  | (true, _) => .ism
  | (false, true) => .fil
  | (false, false) => .harf

def rolesOf : Kind → Bool × Bool
  | .ism => (true, true)
  | .fil => (false, true)
  | .harf => (false, false)

/-- **القسمةُ تقابل:** الأقسامُ الثلاثة تقابل الصورَ الثلاث الممكنة. -/
theorem kind_bij : (∀ k, kindOf (rolesOf k) = k) ∧
    (∀ ind tim, rolesOf (kindOf (roles ind tim)) = roles ind tim) := by
  refine ⟨fun k => by cases k <;> rfl, fun ind tim => by cases ind <;> cases tim <;> rfl⟩

/-- التركيبُ التامّ: صدرُ إسنادٍ (‎some k‎)، أو لا إسنادَ مع تعلّق (‎none‎). -/
abbrev Struct := Option Kind

/-- مرخَّص: صدرُ الإسناد ذو دور. -/
def licensed : Struct → Bool
  | some k => (rolesOf k).1 || (rolesOf k).2
  | none => true

inductive Jumla | ismiyya | filiyya | shibh
  deriving DecidableEq, Repr

def jumlaOf : Struct → Option Jumla
  | some .ism => some .ismiyya
  | some .fil => some .filiyya
  | some .harf => none
  | none => some .shibh

/-- **ثلاثةُ تراكيب لا رابع:** كلُّ تركيبٍ مرخَّص اسميٌّ أو فعليٌّ أو شبهُ جملة، وكلٌّ منها يقع،
وما صدرُه حرفٌ غيرُ مرخَّص. -/
theorem three_structs :
    (∀ s : Struct, licensed s = true → ∃ j, jumlaOf s = some j) ∧
    (∀ j : Jumla, ∃ s : Struct, licensed s = true ∧ jumlaOf s = some j) ∧
    licensed (some .harf) = false := by
  refine ⟨fun s hs => ?_, fun j => ?_, rfl⟩
  · rcases s with _ | k
    · exact ⟨_, rfl⟩
    · cases k
      · exact ⟨_, rfl⟩
      · exact ⟨_, rfl⟩
      · simp [licensed, rolesOf] at hs
  · cases j
    · exact ⟨some .ism, rfl, rfl⟩
    · exact ⟨some .fil, rfl, rfl⟩
    · exact ⟨none, rfl, rfl⟩

/-! ## القسمُ دالّةٌ في المدلول (‎Awwalan.Madlul‎)

‎ind‎ و‎tim‎ حقلان في المدلول المجرّد نفسِه — فالقسمُ يُقرأ من المدلول قبل أيّ لفظ، وهذا ترتيبُ
«المدلول أوّلًا» داخلَ البرهان: ‎Category‎ يستورد ‎MadlulAwwalan‎ ولا يستورد شيئًا من الدالّ. -/

def kindOfMadlul (m : Awwalan.Madlul) : Kind := kindOf (roles m.ind m.tim)

/-- **القسمُ من المدلول:** اسمٌ ⇔ معنًى في نفسه بلا زمانٍ بهيئته؛ فعلٌ ⇔ معنًى في نفسه بزمان؛ حرفٌ ⇔ لا معنى في نفسه. -/
theorem kindOfMadlul_spec (m : Awwalan.Madlul) :
    (kindOfMadlul m = .ism ↔ m.ind = true ∧ m.tim = false) ∧
    (kindOfMadlul m = .fil ↔ m.ind = true ∧ m.tim = true) ∧
    (kindOfMadlul m = .harf ↔ m.ind = false) := by
  unfold kindOfMadlul
  rcases m with ⟨_, _, _, _, _, _, i, t⟩
  cases i <;> cases t <;> simp [roles, kindOf]

/-- **وكلُّ قسمٍ يقع من مدلولٍ ما.** -/
theorem kindOfMadlul_onto (k : Kind) : ∃ m : Awwalan.Madlul, kindOfMadlul m = k := by
  cases k
  · exact ⟨{ haqiqa := 0, khawass := [], alaqat := [], qabiliyyat := [], afrad := [] }, rfl⟩
  · exact ⟨{ haqiqa := 0, khawass := [], alaqat := [], qabiliyyat := [], afrad := [], tim := true }, rfl⟩
  · exact ⟨{ haqiqa := 0, khawass := [], alaqat := [], qabiliyyat := [], afrad := [], ind := false }, rfl⟩

end Cat
end SLGE
