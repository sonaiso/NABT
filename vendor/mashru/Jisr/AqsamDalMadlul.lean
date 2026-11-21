/-
  Jisr/AqsamDalMadlul.lean — المرحلة ٣ (الدال والمدلول معًا): الأقسام السبعة.

  السند (ج3 771): اللفظ والمعنى إمّا أن يتّحدا (المنفرد)، أو يتكثّرا (المتباين)، أو يتكثّر اللفظ
  ويتّحد المعنى (المترادف)، أو يتّحد اللفظ ويتكثّر المعنى؛ وهذا الأخير: إن وُضع لكلّ معنى فالمشترك،
  وإلّا فإن نُقل واشتهر في الثاني فالمنقول، وإن نُقل لعلاقة ولم يشتهر فهو حقيقة إذا أُطلق على
  الموضوع له، ومجاز إذا أُطلق على المنقول إليه.

  التصنيف هنا شجرة القرار نفسها، والعدد سبعة نتيجتها لا إعلان.
-/
namespace Jisr

inductive Adad | wahid | kathir deriving DecidableEq, Repr

inductive QismDalMadlul
  | munfarid | mutabayin | mutaradif | mushtarak | manqul | haqiqa | majaz
deriving DecidableEq, Repr

/-- شجرة ج3 771: عدد اللفظ، عدد المعنى، وُضع لكلّ معنى؟، اشتهر في المنقول إليه؟، أُطلق على الموضوع له؟ -/
def tasnif : Adad → Adad → Bool → Bool → Bool → QismDalMadlul
  | .wahid,  .wahid,  _, _, _ => .munfarid
  | .kathir, .kathir, _, _, _ => .mutabayin
  | .kathir, .wahid,  _, _, _ => .mutaradif
  | .wahid,  .kathir, true,  _,     _     => .mushtarak
  | .wahid,  .kathir, false, true,  _     => .manqul
  | .wahid,  .kathir, false, false, true  => .haqiqa
  | .wahid,  .kathir, false, false, false => .majaz

namespace QismDalMadlul
def kull : List QismDalMadlul := [munfarid, mutabayin, mutaradif, mushtarak, manqul, haqiqa, majaz]
theorem kull_nodup : kull.Nodup := by decide
theorem kull_length : kull.length = 7 := rfl
end QismDalMadlul

/-- كلّ مخرج للشجرة من الأقسام السبعة. -/
theorem tasnif_fi_kull (a b : Adad) (w s m : Bool) : tasnif a b w s m ∈ QismDalMadlul.kull := by
  cases a <;> cases b <;> cases w <;> cases s <;> cases m <;> simp [tasnif, QismDalMadlul.kull]

/-- وكلّ قسم من السبعة يخرج من الشجرة: القسمة مستوفاة. -/
theorem tasnif_mustawfa (q : QismDalMadlul) : ∃ a b w s m, tasnif a b w s m = q := by
  cases q
  · exact ⟨.wahid, .wahid, true, true, true, rfl⟩
  · exact ⟨.kathir, .kathir, true, true, true, rfl⟩
  · exact ⟨.kathir, .wahid, true, true, true, rfl⟩
  · exact ⟨.wahid, .kathir, true, true, true, rfl⟩
  · exact ⟨.wahid, .kathir, false, true, true, rfl⟩
  · exact ⟨.wahid, .kathir, false, false, true, rfl⟩
  · exact ⟨.wahid, .kathir, false, false, false, rfl⟩

/-- الحقيقة والمجاز لا يكونان إلّا في لفظ واحد لمعانٍ كثيرة، نُقل ولم يشتهر. -/
theorem haqiqa_majaz_shart (a b : Adad) (w s m : Bool)
    (h : tasnif a b w s m = .haqiqa ∨ tasnif a b w s m = .majaz) :
    a = .wahid ∧ b = .kathir ∧ w = false ∧ s = false := by
  cases a <;> cases b <;> cases w <;> cases s <;> cases m <;> simp_all [tasnif]

end Jisr
