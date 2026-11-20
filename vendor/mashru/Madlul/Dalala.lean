/-
  Dalala.lean — الدلالات الثلاث: المطابقة والتضمّن والالتزام
  لا sorry، لا axiom، لا native_decide. Lean 4 core وحده (بلا Mathlib).

  التعريفات (من المنطق التراثي):
  * المطابقة: دلالة اللفظ على تمام ما وُضع له.
  * التضمّن:  دلالته على جزءٍ (حقيقيٍّ، غير فارغ) ممّا وُضع له.
  * الالتزام: دلالته على خارجٍ عمّا وُضع له لازمٍ له في الذهن.

  المعنى يُمثَّل بمحمولٍ على مقوّمات (α → Prop): "ما في الذهن" لا الخارج.
  الوضع خبرٌ يحمل شهوده (قائمة معرّفات مواضع في مودَع)؛ لا وضع بلا شاهد.
  اللزوم جدولٌ منفصل (معلومات سابقة) لا يُشتقّ من الوضع.
-/
namespace Dalala

/-- المعنى: مجموعة مقوّمات. -/
abbrev Maana (α : Type) := α → Prop

/-- تساوي معنيين تساويًا مقوّميًّا. -/
def Sawa {α} (p m : Maana α) : Prop := ∀ x, p x ↔ m x

/-- جزءٌ حقيقيّ غير فارغ. -/
def Juz {α} (p m : Maana α) : Prop :=
  (∃ x, p x) ∧ (∀ x, p x → m x) ∧ (∃ x, m x ∧ ¬ p x)

/-- خارجٌ عن المعنى: فيه مقوّمٌ ليس من المعنى. -/
def Kharij {α} (q m : Maana α) : Prop := ∃ x, q x ∧ ¬ m x

/-- الوضع: لكلّ لفظٍ معناه وشهوده. -/
structure Wad (L α : Type) where
  maana  : L → Maana α
  shuhud : L → List String

/-- جدول اللزوم الذهنيّ البيّن (مودَع معلومات سابقة، لا يُستنتج من الوضع). -/
abbrev Luzum (α : Type) := Maana α → Maana α → Prop

variable {L α : Type}

def Mutabaqa (W : Wad L α) (l : L) (p : Maana α) : Prop :=
  W.shuhud l ≠ [] ∧ Sawa p (W.maana l)

def Tadammun (W : Wad L α) (l : L) (p : Maana α) : Prop :=
  W.shuhud l ≠ [] ∧ Juz p (W.maana l)

def Iltizam (W : Wad L α) (Z : Luzum α) (l : L) (q : Maana α) : Prop :=
  W.shuhud l ≠ [] ∧ Kharij q (W.maana l) ∧ Z (W.maana l) q

/-! ## ١. التضمّن والالتزام فرعان على المطابقة -/

theorem tadammun_needs_mutabaqa {W : Wad L α} {l p} :
    Tadammun W l p → Mutabaqa W l (W.maana l) :=
  fun ⟨hs, _⟩ => ⟨hs, fun _ => Iff.rfl⟩

theorem iltizam_needs_mutabaqa {W : Wad L α} {Z l q} :
    Iltizam W Z l q → Mutabaqa W l (W.maana l) :=
  fun ⟨hs, _, _⟩ => ⟨hs, fun _ => Iff.rfl⟩

/-! ## ٢. التباين: لا يجتمع اثنان منها على مدلولٍ واحد -/

theorem mutabaqa_not_tadammun {W : Wad L α} {l p} :
    Mutabaqa W l p → ¬ Tadammun W l p := by
  intro ⟨_, hs⟩ ⟨_, _, _, x, hm, hp⟩
  exact hp ((hs x).mpr hm)

theorem mutabaqa_not_iltizam {W : Wad L α} {Z l p} :
    Mutabaqa W l p → ¬ Iltizam W Z l p := by
  intro ⟨_, hs⟩ ⟨_, ⟨x, hq, hm⟩, _⟩
  exact hm ((hs x).mp hq)

theorem tadammun_not_iltizam {W : Wad L α} {Z l p} :
    Tadammun W l p → ¬ Iltizam W Z l p := by
  intro ⟨_, _, hsub, _⟩ ⟨_, ⟨x, hq, hm⟩, _⟩
  exact hm (hsub x hq)

/-! ## ٣. القسمة داخل المعنى حاصرة: ما دخل في المعنى فهو مطابقة أو تضمّن -/

theorem dakhil_mutabaqa_or_tadammun {W : Wad L α} {l p}
    (hs : W.shuhud l ≠ []) (hne : ∃ x, p x) (hsub : ∀ x, p x → W.maana l x) :
    Mutabaqa W l p ∨ Tadammun W l p := by
  by_cases h : ∃ x, W.maana l x ∧ ¬ p x
  · exact Or.inr ⟨hs, hne, hsub, h⟩
  · refine Or.inl ⟨hs, fun x => ⟨hsub x, fun hm => ?_⟩⟩
    exact Classical.byContradiction fun hp => h ⟨x, hm, hp⟩

/-- وما خرج عن المعنى لا يكون مطابقة ولا تضمّنًا؛ فإن لم يشهد له جدول اللزوم فلا دلالة. -/
theorem kharij_only_iltizam {W : Wad L α} {Z l q} (hk : Kharij q (W.maana l)) :
    ¬ Mutabaqa W l q ∧ ¬ Tadammun W l q ∧ (¬ Z (W.maana l) q → ¬ Iltizam W Z l q) := by
  obtain ⟨x, hq, hm⟩ := hk
  refine ⟨fun ⟨_, hs⟩ => hm ((hs x).mp hq),
          fun ⟨_, _, hsub, _⟩ => hm (hsub x hq),
          fun hz ⟨_, _, h⟩ => hz h⟩

/-! ## ٤. لا دلالة بلا شاهد وضع -/

theorem no_witness_no_dalala {W : Wad L α} {Z l p} (h : W.shuhud l = []) :
    ¬ Mutabaqa W l p ∧ ¬ Tadammun W l p ∧ ¬ Iltizam W Z l p :=
  ⟨fun ⟨hs, _⟩ => hs h, fun ⟨hs, _⟩ => hs h, fun ⟨hs, _⟩ => hs h⟩

/-- الالتزام لا يُستخرج من الوضع وحده: بجدول لزومٍ فارغ لا التزام أصلًا. -/
theorem iltizam_needs_luzum_table {W : Wad L α} {l q} :
    ¬ Iltizam W (fun _ _ => False) l q :=
  fun ⟨_, _, h⟩ => h

/-! ## ٥. استقلال: المطابقة لا تستلزم التضمّن (المعنى البسيط لا جزء له)
    نموذجٌ مضادّ مبنيّ على الشاهد؛ يبرهن خاصّة التعريفات لا خاصّة اللغة. -/

/-- معنى بسيط: مقوّم واحد. -/
theorem basit_no_juz (p : Maana Nat) : ¬ Juz p (· = 0) := by
  intro ⟨⟨y, hy⟩, hsub, x, hx, hpx⟩
  have hy0 : y = 0 := hsub y hy
  subst hy0; subst hx
  exact hpx hy

def wBasit : Wad Unit Nat := { maana := fun _ => (· = 0), shuhud := fun _ => ["test:basit"] }

theorem mutabaqa_without_tadammun :
    Mutabaqa wBasit () (· = 0) ∧ ∀ p, ¬ Tadammun wBasit () p :=
  ⟨⟨by simp [wBasit], fun _ => Iff.rfl⟩, fun p ⟨_, hj⟩ => basit_no_juz p hj⟩

end Dalala

/-! ## التدقيق: المسلّمات المستعملة -/
#print axioms Dalala.tadammun_needs_mutabaqa
#print axioms Dalala.iltizam_needs_mutabaqa
#print axioms Dalala.mutabaqa_not_tadammun
#print axioms Dalala.mutabaqa_not_iltizam
#print axioms Dalala.tadammun_not_iltizam
#print axioms Dalala.dakhil_mutabaqa_or_tadammun
#print axioms Dalala.kharij_only_iltizam
#print axioms Dalala.no_witness_no_dalala
#print axioms Dalala.iltizam_needs_luzum_table
#print axioms Dalala.mutabaqa_without_tadammun
