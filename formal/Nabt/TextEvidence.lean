import Nabt.Morphology

/-!
# Identity-bound activation of text cues

This module specifies the conditional algebra *after* a source reader has
established the linguistic activation of a cue. It does not prove the reader,
the truth of a lexical source, or completeness of Arabic word classification.
The three cue constructors are witnessed noun signs, independently witnessed
verbs, and witnessed particles. In particular, an imperfect-looking prefix
next to a governor is only an observation: that governor cannot create its
missing lexical input. A noun sign does not establish inflection (compare
tanwin in a built اسم فعل such as صَهٍ).

Receipts are bound to source revision, scope, occurrence, byte interval,
segmentation and reading. Each receipt also requires a named installed rule,
activation, no blocker, and nonempty well-formed source support. These are
checkable structural preconditions, not a proof that an asserted rule or span
has the claimed linguistic meaning. The public Python boundary must rederive
them from the expected source; callers cannot grant authority with a Boolean.

Raw prefix, nun, article and pattern observations have no kind authority.
The output is a candidate list, never a grammatical role, contextual case,
root, lexical meaning, world fact or a claim of construction/declension.
-/

namespace Nabt.TextEvidence

open Words (Kind)

def lawId : String := "nabt.text-evidence.v1"
def maskNumberDomain : String := "nabt.text-evidence.kind-cue-mask.v1"
def activationNumberDomain : String := "nabt.text-evidence.activation-mask.v1"

inductive Cue where
  | nounSign | verbWitness | particleWitness
  deriving DecidableEq, Repr

def cues : List Cue := [.nounSign, .verbWitness, .particleWitness]

def Cue.code : Cue → Nat
  | .nounSign => 0 | .verbWitness => 1 | .particleWitness => 2

def Cue.label : Cue → String
  | .nounSign => "noun_sign"
  | .verbWitness => "independent_verb_witness"
  | .particleWitness => "particle_witness"

def Cue.kind : Cue → Kind
  | .nounSign => .noun | .verbWitness => .verb | .particleWitness => .particle

structure Binding where
  sourceId : Nat
  sourceRevision : Nat
  scopeId : Nat
  occurrenceId : Nat
  byteStart : Nat
  byteEnd : Nat
  segmentationId : Nat
  readingId : Nat
  deriving DecidableEq, Repr

structure SupportSpan where
  sourceId : Nat
  sourceRevision : Nat
  byteStart : Nat
  byteEnd : Nat
  deriving DecidableEq, Repr

def SupportSpan.validFor (span : SupportSpan) (target : Binding) : Bool :=
  decide (span.sourceId = target.sourceId ∧
    span.sourceRevision = target.sourceRevision ∧ span.byteStart < span.byteEnd)

structure Receipt where
  binding : Binding
  cue : Cue
  ruleId : Nat
  active : Bool
  blocked : Bool
  support : List SupportSpan
  deriving DecidableEq, Repr

/-- Bit order in the finite export is identity, rule, activation, blocker,
support-present, support-valid. The blocker has negative polarity. -/
def activation (identityMatch ruleMatch active blocked supportPresent supportValid : Bool) : Bool :=
  identityMatch && ruleMatch && active && !blocked && supportPresent && supportValid

def Receipt.admissible (target : Binding) (receipt : Receipt) : Bool :=
  activation (decide (receipt.binding = target))
    (decide (receipt.ruleId = receipt.cue.code)) receipt.active receipt.blocked
    (!receipt.support.isEmpty)
    (decide (target.byteStart < target.byteEnd) &&
      receipt.support.all (fun span => span.validFor target))

inductive Observation where
  | tanwinShape | articlePrefix | imperfectPrefix | nunSuffix | patternShape
  deriving DecidableEq, Repr

inductive Input where
  | observed (observation : Observation)
  | receipt (value : Receipt)
  deriving DecidableEq, Repr

def Input.acceptedCue (target : Binding) : Input → Option Cue
  | .observed _ => none
  | .receipt value => if value.admissible target then some value.cue else none

def acceptedCues (target : Binding) (inputs : List Input) : List Cue :=
  inputs.filterMap (Input.acceptedCue target)

def candidates (target : Binding) (inputs : List Input) : List Kind :=
  Words.kindCandidates ((acceptedCues target inputs).map fun cue => [cue.kind])

def select (values : List Kind) : Option Kind :=
  match values with
  | [kind] => some kind
  | _ => none

def classify (target : Binding) (inputs : List Input) : Option Kind :=
  select (candidates target inputs)

theorem activation_exact (i r a b p v : Bool) :
    activation i r a b p v = true ↔
      i = true ∧ r = true ∧ a = true ∧ b = false ∧ p = true ∧ v = true := by
  cases i <;> cases r <;> cases a <;> cases b <;> cases p <;> cases v <;>
    decide

theorem admitted_binding_exact (target : Binding) (receipt : Receipt)
    (accepted : receipt.admissible target = true) : receipt.binding = target := by
  have bits := (activation_exact _ _ _ _ _ _).mp accepted
  exact of_decide_eq_true bits.1

theorem admitted_support_present (target : Binding) (receipt : Receipt)
    (accepted : receipt.admissible target = true) : receipt.support ≠ [] := by
  have bits := (activation_exact _ _ _ _ _ _).mp accepted
  intro absent
  simp [absent] at bits

theorem admitted_support_bound (target : Binding) (receipt : Receipt)
    (accepted : receipt.admissible target = true) :
    target.byteStart < target.byteEnd ∧
      ∀ span ∈ receipt.support, span.sourceId = target.sourceId ∧
        span.sourceRevision = target.sourceRevision ∧ span.byteStart < span.byteEnd := by
  have bits := (activation_exact _ _ _ _ _ _).mp accepted
  have valid := Bool.and_eq_true_iff.mp bits.2.2.2.2.2
  refine ⟨of_decide_eq_true valid.1, ?_⟩
  intro span member
  have spanValid := (List.all_eq_true.mp valid.2) span member
  exact of_decide_eq_true spanValid

theorem foreign_identity_is_inert (target : Binding) (receipt : Receipt)
    (different : receipt.binding ≠ target) :
    Input.acceptedCue target (.receipt receipt) = none := by
  simp [Input.acceptedCue, Receipt.admissible, activation, different]

theorem inactive_receipt_is_inert (target : Binding) (receipt : Receipt)
    (inactive : receipt.active = false) :
    Input.acceptedCue target (.receipt receipt) = none := by
  simp [Input.acceptedCue, Receipt.admissible, activation, inactive]

theorem blocked_receipt_is_inert (target : Binding) (receipt : Receipt)
    (blocked : receipt.blocked = true) :
    Input.acceptedCue target (.receipt receipt) = none := by
  simp [Input.acceptedCue, Receipt.admissible, activation, blocked]

theorem unsupported_receipt_is_inert (target : Binding) (receipt : Receipt)
    (unsupported : receipt.support = []) :
    Input.acceptedCue target (.receipt receipt) = none := by
  simp [Input.acceptedCue, Receipt.admissible, activation, unsupported]

theorem invalid_rule_is_inert (target : Binding) (receipt : Receipt)
    (different : receipt.ruleId ≠ receipt.cue.code) :
    Input.acceptedCue target (.receipt receipt) = none := by
  simp [Input.acceptedCue, Receipt.admissible, activation, different]

theorem observed_shapes_are_inert (target : Binding) (observation : Observation)
    (inputs : List Input) :
    candidates target (.observed observation :: inputs) = candidates target inputs := rfl

theorem inert_input_preserves_candidates (target : Binding) (input : Input)
    (inputs : List Input) (inert : input.acceptedCue target = none) :
    candidates target (input :: inputs) = candidates target inputs := by
  simp [candidates, acceptedCues, inert]

theorem no_receipt_retains_all (target : Binding) :
    candidates target [] = [.noun, .verb, .particle] := rfl

theorem observations_do_not_classify (target : Binding) (observations : List Observation) :
    classify target (observations.map Input.observed) = none := by
  simp [classify, candidates, acceptedCues, Input.acceptedCue, Words.kindCandidates,
    Words.kinds, select, List.filterMap_map]

theorem candidates_exact (target : Binding) (inputs : List Input) (kind : Kind) :
    kind ∈ candidates target inputs ↔
      ∀ cue ∈ acceptedCues target inputs, kind = cue.kind := by
  simp [candidates, Words.mem_kindCandidates]

theorem accepted_cue_has_receipt (target : Binding) (inputs : List Input) (cue : Cue)
    (accepted : cue ∈ acceptedCues target inputs) :
    ∃ receipt, Input.receipt receipt ∈ inputs ∧ receipt.admissible target = true ∧
      receipt.cue = cue := by
  obtain ⟨input, member, someCue⟩ := List.mem_filterMap.mp accepted
  cases input with
  | observed observation => simp [Input.acceptedCue] at someCue
  | receipt receipt =>
    refine ⟨receipt, member, ?_⟩
    simp only [Input.acceptedCue] at someCue
    split at someCue <;> simp_all

theorem deleting_evidence_cannot_narrow (target : Binding) (old extra : List Input)
    (kind : Kind) (survives : kind ∈ candidates target (old ++ extra)) :
    kind ∈ candidates target old := by
  rw [candidates_exact] at survives ⊢
  intro cue member
  apply survives cue
  simp only [acceptedCues, List.filterMap_append, List.mem_append] at *
  exact Or.inl member

theorem duplicate_evidence_is_idempotent (target : Binding) (input : Input)
    (inputs : List Input) :
    candidates target (input :: input :: inputs) = candidates target (input :: inputs) := by
  cases h : input.acceptedCue target <;>
    simp [candidates, acceptedCues, h, Words.kindCandidates]

theorem distinct_accepted_cues_conflict (target : Binding) (inputs : List Input)
    (left right : Cue) (lmem : left ∈ acceptedCues target inputs)
    (rmem : right ∈ acceptedCues target inputs) (different : left.kind ≠ right.kind) :
    candidates target inputs = [] := by
  apply List.eq_nil_iff_forall_not_mem.mpr
  intro kind member
  have every := (candidates_exact target inputs kind).mp member
  exact different ((every left lmem).symm.trans (every right rmem))

theorem selection_exact (values : List Kind) (kind : Kind) :
    select values = some kind ↔ values = [kind] := by
  cases values with
  | nil => simp [select]
  | cons first rest =>
    cases rest with
    | nil => simp [select]
    | cons next tail => simp [select]

theorem conflict_never_classifies (target : Binding) (inputs : List Input)
    (conflict : candidates target inputs = []) : classify target inputs = none := by
  simp [classify, conflict, select]

theorem selected_kind_has_witness (target : Binding) (inputs : List Input) (kind : Kind)
    (selected : classify target inputs = some kind) :
    ∃ receipt, Input.receipt receipt ∈ inputs ∧ receipt.admissible target = true ∧
      receipt.binding = target ∧ receipt.cue.kind = kind := by
  have singleton := (selection_exact _ kind).mp selected
  have nonempty : acceptedCues target inputs ≠ [] := by
    intro empty
    simp [candidates, empty, Words.no_cue_retains_all] at singleton
  obtain ⟨cue, member⟩ := List.exists_mem_of_ne_nil _ nonempty
  obtain ⟨receipt, inInputs, admissible, receiptCue⟩ :=
    accepted_cue_has_receipt target inputs cue member
  refine ⟨receipt, inInputs, admissible, admitted_binding_exact target receipt admissible, ?_⟩
  have kindMember : kind ∈ candidates target inputs := by simp [singleton]
  rw [receiptCue]
  exact ((candidates_exact target inputs kind).mp kindMember cue member).symm

/-- Three presence bits; repeated receipts cannot increase their authority. -/
structure CueMask where
  noun : Bool
  verb : Bool
  particle : Bool
  deriving DecidableEq, Repr

def CueMask.code (mask : CueMask) : Nat :=
  (if mask.noun then 1 else 0) + (if mask.verb then 2 else 0) +
    (if mask.particle then 4 else 0)

def CueMask.ofCode (number : Nat) : Option CueMask :=
  if number < 8 then some ⟨number % 2 == 1, number / 2 % 2 == 1, number / 4 % 2 == 1⟩
  else none

def CueMask.ofCues (values : List Cue) : CueMask :=
  ⟨values.contains .nounSign, values.contains .verbWitness, values.contains .particleWitness⟩

def CueMask.asCues (mask : CueMask) : List Cue :=
  (if mask.noun then [.nounSign] else []) ++
  (if mask.verb then [.verbWitness] else []) ++
  (if mask.particle then [.particleWitness] else [])

def CueMask.candidates (mask : CueMask) : List Kind :=
  Words.kindCandidates (mask.asCues.map fun cue => [cue.kind])

theorem cue_mask_roundtrip (mask : CueMask) : CueMask.ofCode mask.code = some mask := by
  cases mask with
  | mk noun verb particle => cases noun <;> cases verb <;> cases particle <;> rfl

theorem cue_mask_outside_rejected (number : Nat) (outside : 8 ≤ number) :
    CueMask.ofCode number = none := by
  simp [CueMask.ofCode, Nat.not_lt.mpr outside]

theorem cue_mask_membership (values : List Cue) (cue : Cue) :
    cue ∈ (CueMask.ofCues values).asCues ↔ cue ∈ values := by
  cases cue <;>
    simp [CueMask.ofCues, CueMask.asCues, List.mem_append]

theorem cue_mask_matches_receipts (target : Binding) (inputs : List Input) :
    (CueMask.ofCues (acceptedCues target inputs)).candidates = candidates target inputs := by
  unfold CueMask.candidates candidates Words.kindCandidates
  apply List.filter_congr
  intro kind member
  apply Bool.eq_iff_iff.mpr
  simp only [List.all_eq_true, List.mem_map, forall_exists_index, and_imp,
    forall_apply_eq_imp_iff₂, List.contains_iff_mem, List.mem_singleton]
  constructor <;> intro h cue mem
  · exact h cue ((cue_mask_membership _ cue).mpr mem)
  · exact h cue ((cue_mask_membership _ cue).mp mem)

/-- A noun kind alone leaves both nominal construction hypotheses open.
The tanwin witness has no field authorizing a choice between them. -/
theorem noun_sign_does_not_determine_construction :
    Morphology.nounCandidates .unknown = [.built, .inflected] := by decide

end Nabt.TextEvidence
