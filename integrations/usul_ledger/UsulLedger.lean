import Std

/-! The predicates are interpreted within one reading and one source frame.
Explicit negative evidence and absence of evidence are separate fields. -/
namespace UsulLedger

abbrev Concept (α : Type) := α → Prop

def Named {α} (a : α) : Concept α := fun x => x = a
def Universal {α} (g p : Concept α) := ∀ x, g x → p x
def Alternative {α} (g p : Concept α) := ∃ x, g x ∧ p x
def Except {α} (g excluded : Concept α) : Concept α := fun x => g x ∧ ¬ excluded x
def Restrict {α} (g q : Concept α) : Concept α := fun x => g x ∧ q x

theorem named_reads_one {α} (a : α) (p : Concept α) :
    Universal (Named a) p ↔ p a := by
  constructor
  · exact fun h => h a rfl
  · intro h x eq; change x = a at eq; exact eq ▸ h

theorem specifying_preserves_fulfillment {α} (g excluded p : Concept α)
    (h : Universal g p) : Universal (Except g excluded) p :=
  fun x hx => h x hx.1

theorem qualified_witness_is_unqualified {α} (g q p : Concept α)
    (h : Alternative (Restrict g q) p) : Alternative g p := by
  obtain ⟨x,hx,hp⟩ := h
  exact ⟨x,hx.1,hp⟩

theorem specialization_need_not_recover_original :
    Universal (Except (fun _ : Bool => True) (· = false)) (· = true) ∧
    ¬ Universal (fun _ : Bool => True) (· = true) := by
  constructor
  · intro x hx; cases x <;> simp_all [Except]
  · intro h; cases h false trivial

theorem unqualified_need_not_fulfill_qualified :
    Alternative (fun _ : Bool => True) (· = false) ∧
    ¬ Alternative (Restrict (fun _ : Bool => True) (· = true)) (· = false) := by
  refine ⟨⟨false,trivial,rfl⟩,?_⟩
  rintro ⟨x, hx, rfl⟩
  exact Bool.noConfusion hx.2

structure RowEvidence where
  admitted : Bool
  excluded : Bool
  doneYes : Bool
  doneNo : Bool
  deriving DecidableEq, Repr

def allYes (closed : Bool) (rows : List RowEvidence) :=
  closed && rows.all fun r => r.excluded || r.doneYes
def allNo (rows : List RowEvidence) := rows.any fun r => r.admitted && r.doneNo
def someYes (rows : List RowEvidence) := rows.any fun r => r.admitted && r.doneYes
def someNo (closed : Bool) (rows : List RowEvidence) :=
  closed && rows.all fun r => r.excluded || r.doneNo

theorem all_yes_exact (c rs) : allYes c rs = true ↔
    c = true ∧ ∀ r ∈ rs, r.excluded = true ∨ r.doneYes = true := by simp [allYes]
theorem all_no_exact (rs) : allNo rs = true ↔
    ∃ r ∈ rs, r.admitted = true ∧ r.doneNo = true := by simp [allNo]
theorem some_yes_exact (rs) : someYes rs = true ↔
    ∃ r ∈ rs, r.admitted = true ∧ r.doneYes = true := by simp [someYes]
theorem some_no_exact (c rs) : someNo c rs = true ↔
    c = true ∧ ∀ r ∈ rs, r.excluded = true ∨ r.doneNo = true := by simp [someNo]

/-- With complete consistent observations for each listed individual, the
four-sign evidence calculus agrees with the ordinary finite quantifiers. -/
def observed (eligible performed : α → Bool) (a : α) : RowEvidence :=
  ⟨eligible a, !(eligible a), performed a, !(performed a)⟩

theorem closed_all_agrees (xs : List α) (g p : α → Bool) :
    allYes true (xs.map (observed g p)) = true ↔
      ∀ x ∈ xs, g x = true → p x = true := by
  rw [all_yes_exact]
  simp only [true_and, List.mem_map, forall_exists_index, and_imp,
             forall_apply_eq_imp_iff₂, observed, Bool.not_eq_true']
  constructor
  · intro h x hx hg
    rcases h x hx with hn | hp
    · simp [hg] at hn
    · exact hp
  · intro h x hx
    cases hg : g x with
    | false => exact Or.inl rfl
    | true => exact Or.inr (h x hx hg)

theorem closed_some_agrees (xs : List α) (g p : α → Bool) :
    someYes (xs.map (observed g p)) = true ↔
      ∃ x ∈ xs, g x = true ∧ p x = true := by
  rw [some_yes_exact]
  constructor
  · rintro ⟨r,hr,he,hp⟩
    obtain ⟨x,hx,rfl⟩ := List.mem_map.mp hr
    exact ⟨x,hx,he,hp⟩
  · rintro ⟨x,hx,he,hp⟩
    exact ⟨observed g p x,List.mem_map.mpr ⟨x,hx,rfl⟩,he,hp⟩

theorem one_witness_not_every_one :
    let rs := [RowEvidence.mk true false true false, RowEvidence.mk true false false true]
    someYes rs = true ∧ allNo rs = true := by decide

theorem empty_scope_observations :
    allYes true [] = true ∧ someNo true [] = true ∧
    allYes false [] = false ∧ someNo false [] = false := by decide

inductive Mark where | yes | no | unknown | contested deriving DecidableEq, Repr
inductive Convention where | distinguished | merged deriving DecidableEq
inductive Judgment where | valid | void | defective | invalid deriving DecidableEq, Repr

def evaluate : Convention → Mark → Mark → Option Judgment
  | _, .yes, .yes => some .valid
  | .distinguished, .no, _ => some .void
  | .merged, .no, _ => some .invalid
  | .distinguished, .yes, .no => some .defective
  | .merged, .yes, .no => some .invalid
  | _, _, _ => none

theorem defective_exact (origin quality) :
    evaluate .distinguished origin quality = some .defective ↔
      origin = .yes ∧ quality = .no := by cases origin <;> cases quality <;> decide

theorem standard_changes_label :
    evaluate .distinguished .yes .no = some .defective ∧
    evaluate .merged .yes .no = some .invalid ∧
    evaluate .distinguished .yes .unknown = none := by decide

def applyEffect (valid cause condition blocker : Mark) : Prop :=
  valid = .yes ∧ cause = .yes ∧ condition = .yes ∧ blocker = .no

theorem permits_only_with_explicit_absence (v c s b)
    (h : applyEffect v c s b) : b = .no := h.2.2.2

theorem necessary_reading_needs_a_candidate {α} (need : Prop)
    (candidate bridge clue : α → Prop) (x : α)
    (h : need ∧ candidate x ∧ bridge x ∧ clue x) : bridge x ∧ clue x := h.2.2

end UsulLedger
#print axioms UsulLedger.all_yes_exact
#print axioms UsulLedger.some_no_exact
#print axioms UsulLedger.defective_exact
