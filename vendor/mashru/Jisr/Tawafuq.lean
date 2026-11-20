/-
  Jisr/Tawafuq.lean — التوافق بين موضعَي الدلالات الثلاث.

  * الشخصية ج3 737 تجعل المطابقة والتضمّن والالتزام تقسيمًا للّفظ «باعتبار الدال وحده».
  * وتحقُّقُ أيٍّ منها في لفظٍ بعينه يحتاج ما وُضع له وجدول اللزوم الذهنيّ (مادّة المدلول).
  * وج3 1018 يرتّب: معرفة أقسام الألفاظ أوّلًا، ثم المنطوق والمفهوم (1028–1032).

  التوافق: «النوع» من الدال وحده (Dal.NawDalala، المرحلة ١)، و«المادّة» من المدلول (المرحلة ٢)،
  و«التحقّق» في الجسر (المرحلة ٣). المبرهنات هنا تثبت أنّ التحقّق يقع في نوعٍ واحد بالضبط من الأنواع
  الثلاثة لكلّ مادّةٍ كانت، وأنّ المنطوق والمفهوم يُحسبان من النوع وحده.
-/
import Madlul.Dalala
import Dal.AqsamAllafz

open Dalala

namespace Jisr

variable {L α : Type}

/-- تحقّق نوعِ الدلالة (من الدال وحده) على مادّة المدلول. -/
def Tahaqquq (W : Wad L α) (Z : Luzum α) (l : L) (p : Maana α) : Dal.NawDalala → Prop
  | .mutabaqa => Mutabaqa W l p
  | .tadammun => Tadammun W l p
  | .iltizam  => Iltizam W Z l p

/-- الفرادة: لا يتحقّق في مدلولٍ واحد نوعان، لأيّ وضعٍ وأيّ جدول لزوم. -/
theorem tahaqquq_wahid {W : Wad L α} {Z : Luzum α} {l : L} {p : Maana α}
    {k₁ k₂ : Dal.NawDalala} (h₁ : Tahaqquq W Z l p k₁) (h₂ : Tahaqquq W Z l p k₂) : k₁ = k₂ := by
  cases k₁ <;> cases k₂ <;> simp only [Tahaqquq] at h₁ h₂ <;> first
    | rfl
    | exact absurd h₂ (mutabaqa_not_tadammun h₁)
    | exact absurd h₁ (mutabaqa_not_tadammun h₂)
    | exact absurd h₂ (mutabaqa_not_iltizam h₁)
    | exact absurd h₁ (mutabaqa_not_iltizam h₂)
    | exact absurd h₂ (tadammun_not_iltizam h₁)
    | exact absurd h₁ (tadammun_not_iltizam h₂)

/-- الحصر: لمدلولٍ غير فارغ ولفظٍ مشهود، إمّا أن يتحقّق نوعٌ من الثلاثة،
    وإمّا أن يكون خارجًا بلا لزوم فلا دلالة. -/
theorem tahaqquq_hasir {W : Wad L α} {Z : Luzum α} {l : L} {p : Maana α}
    (hs : W.shuhud l ≠ []) (hne : ∃ x, p x) :
    (∃ k, Tahaqquq W Z l p k) ∨ (Kharij p (W.maana l) ∧ ¬ Z (W.maana l) p) := by
  by_cases hsub : ∀ x, p x → W.maana l x
  · rcases dakhil_mutabaqa_or_tadammun hs hne hsub with h | h
    · exact Or.inl ⟨.mutabaqa, h⟩
    · exact Or.inl ⟨.tadammun, h⟩
  · have hk : Kharij p (W.maana l) :=
      Classical.byContradiction fun hn =>
        hsub fun x hp => Classical.byContradiction fun hm => hn ⟨x, hp, hm⟩
    by_cases hz : Z (W.maana l) p
    · exact Or.inl ⟨.iltizam, hs, hk, hz⟩
    · exact Or.inr ⟨hk, hz⟩

/-- المنطوق من الأنواع: المطابقة والتضمّن (ج3 1028). -/
def mantuqNaw : Dal.NawDalala → Bool
  | .iltizam => false
  | _ => true

def Mantuq (W : Wad L α) (Z : Luzum α) (l : L) (p : Maana α) : Prop :=
  ∃ k, Tahaqquq W Z l p k ∧ mantuqNaw k = true

def Mafhum (W : Wad L α) (Z : Luzum α) (l : L) (p : Maana α) : Prop :=
  ∃ k, Tahaqquq W Z l p k ∧ mantuqNaw k = false

theorem mantuq_iff {W : Wad L α} {Z : Luzum α} {l : L} {p : Maana α} :
    Mantuq W Z l p ↔ Mutabaqa W l p ∨ Tadammun W l p := by
  constructor
  · rintro ⟨k, hk, hm⟩
    cases k
    · exact Or.inl hk
    · exact Or.inr hk
    · simp [mantuqNaw] at hm
  · rintro (h | h)
    · exact ⟨.mutabaqa, h, rfl⟩
    · exact ⟨.tadammun, h, rfl⟩

/-- المفهوم هو الالتزام (ج3 1032). -/
theorem mafhum_iff {W : Wad L α} {Z : Luzum α} {l : L} {p : Maana α} :
    Mafhum W Z l p ↔ Iltizam W Z l p := by
  constructor
  · rintro ⟨k, hk, hm⟩
    cases k
    · simp [mantuqNaw] at hm
    · simp [mantuqNaw] at hm
    · exact hk
  · intro h
    exact ⟨.iltizam, h, rfl⟩

/-- لا يجتمع المنطوق والمفهوم في مدلولٍ واحد. -/
theorem mantuq_mafhum_la_yajtamian {W : Wad L α} {Z : Luzum α} {l : L} {p : Maana α} :
    ¬ (Mantuq W Z l p ∧ Mafhum W Z l p) := by
  rintro ⟨⟨k₁, h₁, m₁⟩, ⟨k₂, h₂, m₂⟩⟩
  have := tahaqquq_wahid h₁ h₂
  subst this
  simp_all

/-- الدال وحده لا يكفي: بلا شاهد وضعٍ لا يتحقّق نوع، وبجدول لزومٍ فارغ لا التزام. -/
theorem la_tahaqquq_bila_madda {W : Wad L α} {l : L} {p : Maana α} (k : Dal.NawDalala)
    (h : W.shuhud l = []) (Z : Luzum α) : ¬ Tahaqquq W Z l p k := by
  have := no_witness_no_dalala (Z := Z) (p := p) h
  cases k
  · exact this.1
  · exact this.2.1
  · exact this.2.2

end Jisr
