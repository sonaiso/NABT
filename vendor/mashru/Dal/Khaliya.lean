/-
  Dal/Khaliya.lean — الدال وحده، الطبقة الأولى: الخلية = حامل × حالة، ولكلّ خلية n فريد.

  29 حاملًا (الأحرف مع الألف) × 4 حالات = 116 خلية.
  الحامل هنا رقمُ موضعه في جدول المخارج (Fin 29)؛ والجدول نفسه وأسماء الحالات الأربع
  (فتحة 0، ضمّة 1، كسرة 2، سكون 3) في Dal/Makharij.lean، معلَنًا عن مرفق المالك (2026-10-15).

  بلا sorry ولا axiom ولا native_decide.
-/
namespace Dal

abbrev Hamil := Fin 29   -- الحامل: موضعه في جدول المخارج المودَع
abbrev Hala  := Fin 4    -- الحالة

structure Khaliya where
  hamil : Hamil
  hala  : Hala
deriving DecidableEq, Repr

/-- الرقم الفريد للخلية: n = 4·حامل + حالة. -/
def n (k : Khaliya) : Fin 116 :=
  ⟨4 * k.hamil.val + k.hala.val, by omega⟩

/-- الفكّ: من n إلى الخلية. -/
def fakk (m : Fin 116) : Khaliya :=
  ⟨⟨m.val / 4, by omega⟩, ⟨m.val % 4, by omega⟩⟩

/-- الطيّ ثم الفكّ يعيد الخلية. -/
theorem fakk_n (k : Khaliya) : fakk (n k) = k := by
  obtain ⟨⟨c, hc⟩, ⟨v, hv⟩⟩ := k
  simp only [fakk, n, Khaliya.mk.injEq, Fin.mk.injEq]
  omega

/-- الفكّ ثم الطيّ يعيد الرقم. -/
theorem n_fakk (m : Fin 116) : n (fakk m) = m := by
  obtain ⟨m, hm⟩ := m
  simp only [fakk, n, Fin.mk.injEq]
  omega

/-- الفرادة: خليتان بالرقم نفسه هما خلية واحدة. -/
theorem n_injective {a b : Khaliya} (h : n a = n b) : a = b := by
  rw [← fakk_n a, ← fakk_n b, h]

/-- الاستيفاء: كلّ رقم دون 116 رقمُ خليةٍ ما. -/
theorem n_surjective (m : Fin 116) : ∃ k, n k = m := ⟨fakk m, n_fakk m⟩

/-- العدد بالحساب لا بالإعلان. -/
theorem card_116 : 29 * 4 = 116 := rfl

end Dal

#print axioms Dal.fakk_n
#print axioms Dal.n_fakk
#print axioms Dal.n_injective
#print axioms Dal.n_surjective
