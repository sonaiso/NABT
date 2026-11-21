/-
  Madlul/AqsamAlmadlul.lean — المرحلة ٢ (المدلول وحده): أقسام اللفظ باعتبار المدلول وحده.

  السند (ج3 753–763): المدلول إمّا معنًى، وإمّا لفظ؛ واللفظ مفرد أو مركّب، وكلٌّ مستعمل أو مهمل؛
  «ومجموع ذلك خمسة أقسام». والمركّب المهمل (الهذيان) «غير موضوع» (763).

  القسمة هنا مبنيّة من محاورها كما بناها الكتاب، فالعدد خمسة نتيجةٌ لا إعلان.
-/
namespace Madlul

/-- المحوران: إفراد/تركيب، واستعمال/إهمال. -/
inductive Tarkib  | mufrad | murakkab  deriving DecidableEq, Repr
inductive Istimal | mustamal | muhmal  deriving DecidableEq, Repr

/-- مدلول اللفظ: معنًى، أو لفظٌ بمحوريه. -/
inductive QismMadlul
  | maana
  | lafz (t : Tarkib) (i : Istimal)
deriving DecidableEq, Repr

namespace QismMadlul
def kull : List QismMadlul :=
  [maana,
   lafz .mufrad .mustamal, lafz .mufrad .muhmal,
   lafz .murakkab .mustamal, lafz .murakkab .muhmal]

theorem kull_hasir (q : QismMadlul) : q ∈ kull := by
  rcases q with _ | ⟨t, i⟩
  · simp [kull]
  · cases t <;> cases i <;> simp [kull]

theorem kull_nodup : kull.Nodup := by decide

/-- «ومجموع ذلك خمسة» = 1 + 2×2 (ج3 753). -/
theorem khamsa : kull.length = 1 + 2 * 2 := rfl

/-- الموضوع: كلّ قسم إلّا المركّب المهمل (ج3 763). -/
def mawdu : QismMadlul → Bool
  | lafz .murakkab .muhmal => false
  | _ => true

theorem hadhayan_ghayr_mawdu : mawdu (lafz .murakkab .muhmal) = false := rfl
end QismMadlul

end Madlul
