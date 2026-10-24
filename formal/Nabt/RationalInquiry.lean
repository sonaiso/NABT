import Std

/-!
# Source-bound rational inquiry and conditional correspondence review

This versioned law separates formation of a candidate, review of its support,
and a correspondence license within a declared scope. The executable checks
are inputs from a source/evidence adapter. They are not user declarations of
truth: the theorems do not establish the authenticity of a source, the truth
of an interpretation, human cognition, a complete Python refinement, or the
soundness of a physical sensor. In particular, a world bridge is a separate
review obligation, not a consequence of formal derivability or prose depth.

The independent support calculus below retains complete source values and
claim bindings. Its interpretation ledger is an explicit premise. Revoking
one exact source removes its support without inventing negative evidence and
without discarding independent support from another still-active source.
-/

namespace Nabt.RationalInquiry

def lawId : String := "nabt.rational-inquiry.v1"

/-- The adapter must compute these facts from its retained evidence. -/
structure Checks where
  formed : Bool
  reviewed : Bool
  provenance : Bool
  scopeCovered : Bool
  supported : Bool
  counterevidence : Bool
  requiresWorldBridge : Bool
  worldBridge : Bool
  exhausted : Bool
  requestedRank : Nat
  evidenceRank : Nat
  deriving DecidableEq, Repr

def Preconditions (checks : Checks) : Prop :=
  checks.formed = true ∧ checks.reviewed = true ∧
  checks.provenance = true ∧ checks.scopeCovered = true ∧
  checks.supported = true ∧ checks.counterevidence = false ∧
  (checks.requiresWorldBridge = true → checks.worldBridge = true) ∧
  checks.exhausted = false ∧ checks.requestedRank ≤ checks.evidenceRank

instance (checks : Checks) : Decidable (Preconditions checks) :=
  inferInstanceAs (Decidable (_ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _))

def eligible (checks : Checks) : Bool := decide (Preconditions checks)

inductive Verdict where
  | unformed | resourceLimit | unreviewed | conflict | refuted | licensed | deferred
  deriving DecidableEq, Repr

def Verdict.label : Verdict → String
  | .unformed => "UNFORMED"
  | .resourceLimit => "RESOURCE_LIMIT"
  | .unreviewed => "UNREVIEWED"
  | .conflict => "CONFLICT"
  | .refuted => "REFUTED"
  | .licensed => "LICENSED"
  | .deferred => "DEFER"

structure Result where
  verdict : Verdict
  authorizedRank : Nat
  deriving DecidableEq, Repr

def assess (checks : Checks) : Result :=
  if checks.exhausted then ⟨.resourceLimit, 0⟩
  else if !checks.formed then ⟨.unformed, 0⟩
  else if checks.requiresWorldBridge && !checks.worldBridge then ⟨.deferred, 0⟩
  else if !checks.provenance || !checks.scopeCovered then ⟨.deferred, 0⟩
  else if checks.counterevidence then
    if checks.supported then ⟨.conflict, 0⟩ else ⟨.refuted, 0⟩
  else if !checks.reviewed then ⟨.unreviewed, 0⟩
  else if eligible checks then ⟨.licensed, checks.requestedRank⟩
  else ⟨.deferred, 0⟩

theorem eligible_iff (checks : Checks) :
    eligible checks = true ↔ Preconditions checks := by simp [eligible]

theorem assess_licensed_iff (checks : Checks) :
    (assess checks).verdict = .licensed ↔ eligible checks = true := by
  unfold assess
  split <;> simp_all [eligible, Preconditions]
  split <;> simp_all
  split <;> simp_all
  split <;> simp_all
  · rename_i unbound
    rcases unbound with provenance | scope <;> simp_all
  split <;> simp_all
  · split <;> simp_all
  split <;> simp_all
  split <;> simp_all

theorem licensed_requires_formation (checks : Checks)
    (licensed : (assess checks).verdict = .licensed) : checks.formed = true :=
  ((eligible_iff checks).mp ((assess_licensed_iff checks).mp licensed)).1

theorem licensed_requires_review (checks : Checks)
    (licensed : (assess checks).verdict = .licensed) : checks.reviewed = true :=
  ((eligible_iff checks).mp ((assess_licensed_iff checks).mp licensed)).2.1

theorem licensed_requires_provenance (checks : Checks)
    (licensed : (assess checks).verdict = .licensed) : checks.provenance = true :=
  ((eligible_iff checks).mp ((assess_licensed_iff checks).mp licensed)).2.2.1

theorem licensed_requires_scope (checks : Checks)
    (licensed : (assess checks).verdict = .licensed) : checks.scopeCovered = true :=
  ((eligible_iff checks).mp ((assess_licensed_iff checks).mp licensed)).2.2.2.1

theorem licensed_requires_support (checks : Checks)
    (licensed : (assess checks).verdict = .licensed) : checks.supported = true :=
  ((eligible_iff checks).mp ((assess_licensed_iff checks).mp licensed)).2.2.2.2.1

theorem licensed_has_no_counterevidence (checks : Checks)
    (licensed : (assess checks).verdict = .licensed) : checks.counterevidence = false :=
  ((eligible_iff checks).mp ((assess_licensed_iff checks).mp licensed)).2.2.2.2.2.1

theorem licensed_world_requires_bridge (checks : Checks)
    (licensed : (assess checks).verdict = .licensed)
    (worldClaim : checks.requiresWorldBridge = true) : checks.worldBridge = true :=
  ((eligible_iff checks).mp ((assess_licensed_iff checks).mp licensed)).2.2.2.2.2.2.1 worldClaim

theorem licensed_not_exhausted (checks : Checks)
    (licensed : (assess checks).verdict = .licensed) : checks.exhausted = false :=
  ((eligible_iff checks).mp ((assess_licensed_iff checks).mp licensed)).2.2.2.2.2.2.2.1

theorem licensed_rank_bounded (checks : Checks)
    (licensed : (assess checks).verdict = .licensed) :
    checks.requestedRank ≤ checks.evidenceRank :=
  ((eligible_iff checks).mp ((assess_licensed_iff checks).mp licensed)).2.2.2.2.2.2.2.2

theorem no_completion_from_exhaustion (checks : Checks)
    (exhausted : checks.exhausted = true) : (assess checks).verdict ≠ .licensed := by
  intro licensed
  have stopped := licensed_not_exhausted checks licensed
  simp_all

theorem counterevidence_blocks_license (checks : Checks)
    (counter : checks.counterevidence = true) : (assess checks).verdict ≠ .licensed := by
  intro licensed
  have absent := licensed_has_no_counterevidence checks licensed
  simp_all

theorem missing_world_bridge_blocks_license (checks : Checks)
    (worldClaim : checks.requiresWorldBridge = true) (missing : checks.worldBridge = false) :
    (assess checks).verdict ≠ .licensed := by
  intro licensed
  have bridge := licensed_world_requires_bridge checks licensed worldClaim
  simp_all

/-- Neither positive nor negative source reports establish an unbridged world claim. -/
theorem unbridged_world_is_deferred (checks : Checks)
    (formed : checks.formed = true) (available : checks.exhausted = false)
    (worldClaim : checks.requiresWorldBridge = true) (missing : checks.worldBridge = false) :
    assess checks = ⟨.deferred, 0⟩ := by
  simp [assess, formed, available, worldClaim, missing]

/-- Source binding and full scope are required for positive and negative decisions. -/
theorem unbound_evidence_is_deferred (checks : Checks)
    (formed : checks.formed = true) (available : checks.exhausted = false)
    (unbound : checks.provenance = false ∨ checks.scopeCovered = false) :
    assess checks = ⟨.deferred, 0⟩ := by
  rcases unbound with provenance | scope <;>
    cases worldClaim : checks.requiresWorldBridge <;> cases bridge : checks.worldBridge <;>
    simp_all [assess]

theorem unauthorized_rank_is_zero (checks : Checks)
    (unlicensed : (assess checks).verdict ≠ .licensed) :
    (assess checks).authorizedRank = 0 := by
  have ineligible : eligible checks ≠ true := by
    intro accepted
    exact unlicensed ((assess_licensed_iff checks).mpr accepted)
  cases exhausted : checks.exhausted <;> cases formed : checks.formed <;>
    cases worldClaim : checks.requiresWorldBridge <;> cases bridge : checks.worldBridge <;>
    cases provenance : checks.provenance <;> cases scope : checks.scopeCovered <;>
    cases counter : checks.counterevidence <;> cases reviewed : checks.reviewed <;>
    cases supported : checks.supported <;> simp_all [assess]

theorem authorized_rank_bounded (checks : Checks) :
    (assess checks).authorizedRank ≤ checks.evidenceRank := by
  by_cases accepted : eligible checks = true
  · obtain ⟨formed, reviewed, provenance, scope, supported, counter, bridge, exhausted, bound⟩ :=
      (eligible_iff checks).mp accepted
    have worldGuard : (checks.requiresWorldBridge && !checks.worldBridge) = false := by
      cases worldClaim : checks.requiresWorldBridge <;> simp_all
    simpa [assess, formed, reviewed, provenance, scope, counter, exhausted, worldGuard, accepted]
      using bound
  · have rejected : (assess checks).verdict ≠ .licensed := by
      intro licensed
      exact accepted ((assess_licensed_iff checks).mp licensed)
    rw [unauthorized_rank_is_zero checks rejected]
    exact Nat.zero_le _

inductive Depth where
  | initial | deep | contextual
  deriving DecidableEq, Repr

inductive Genre where
  | formal | empirical | linguistic | historical | literary | normative | political
  deriving DecidableEq, Repr

/-- Review style and text genre never discharge an evidential obligation. -/
def assessAnnotated (checks : Checks) (_depth : Depth) (_genre : Genre) : Result :=
  assess checks

theorem depth_does_not_change_authority (checks : Checks) (left right : Depth) (genre : Genre) :
    assessAnnotated checks left genre = assessAnnotated checks right genre := rfl

theorem genre_does_not_change_authority (checks : Checks) (depth : Depth) (left right : Genre) :
    assessAnnotated checks depth left = assessAnnotated checks depth right := rfl

/-- A complete identity includes the content, not only a caller-chosen name. -/
structure Source where
  identity : String
  revision : String
  content : String
  deriving DecidableEq, Repr

structure Claim where
  identity : String
  statement : String
  scope : List String
  deriving DecidableEq, Repr

structure Support where
  target : Claim
  source : Source
  coveredScope : List String
  positive : Bool
  rank : Nat
  deriving DecidableEq, Repr

structure Context where
  activeSources : List Source
  interpreted : List Support
  deriving DecidableEq, Repr

/-- Interpretation and source authenticity are premises, not conclusions. -/
def Accepted (ctx : Context) (claim : Claim) (support : Support) : Prop :=
  support.target = claim ∧ support ∈ ctx.interpreted ∧
  support.source ∈ ctx.activeSources ∧ claim.scope ≠ [] ∧
  ∀ point ∈ claim.scope, point ∈ support.coveredScope

instance (ctx : Context) (claim : Claim) (support : Support) :
    Decidable (Accepted ctx claim support) :=
  inferInstanceAs (Decidable (_ ∧ _ ∧ _ ∧ _ ∧ _))

def accepts (ctx : Context) (claim : Claim) (support : Support) : Bool :=
  decide (Accepted ctx claim support)

theorem accepts_iff (ctx : Context) (claim : Claim) (support : Support) :
    accepts ctx claim support = true ↔ Accepted ctx claim support := by simp [accepts]

theorem accepted_exact_claim (ctx : Context) (claim : Claim) (support : Support)
    (accepted : accepts ctx claim support = true) : support.target = claim :=
  ((accepts_iff ctx claim support).mp accepted).1

theorem accepted_source_active (ctx : Context) (claim : Claim) (support : Support)
    (accepted : accepts ctx claim support = true) : support.source ∈ ctx.activeSources :=
  ((accepts_iff ctx claim support).mp accepted).2.2.1

theorem accepted_scope_covered (ctx : Context) (claim : Claim) (support : Support)
    (accepted : accepts ctx claim support = true) :
    claim.scope ≠ [] ∧ ∀ point ∈ claim.scope, point ∈ support.coveredScope :=
  ((accepts_iff ctx claim support).mp accepted).2.2.2

theorem changed_source_content_not_equal (left right : Source)
    (changed : left.content ≠ right.content) : left ≠ right := by
  intro same
  exact changed (congrArg Source.content same)

def withdraw (ctx : Context) (source : Source) : Context :=
  { ctx with activeSources := ctx.activeSources.filter (fun current => decide (current ≠ source)) }

theorem accepted_after_withdrawal_iff (ctx : Context) (claim : Claim)
    (support : Support) (source : Source) :
    accepts (withdraw ctx source) claim support = true ↔
      accepts ctx claim support = true ∧ support.source ≠ source := by
  simp [accepts, Accepted, withdraw, and_assoc, and_left_comm, and_comm]

theorem withdrawn_source_cannot_support (ctx : Context) (claim : Claim)
    (support : Support) (source : Source) (same : support.source = source) :
    accepts (withdraw ctx source) claim support = false := by
  cases result : accepts (withdraw ctx source) claim support with
  | false => rfl
  | true =>
    have different := ((accepted_after_withdrawal_iff ctx claim support source).mp result).2
    exact False.elim (different same)

theorem independent_support_survives (ctx : Context) (claim : Claim)
    (support : Support) (source : Source)
    (accepted : accepts ctx claim support = true) (independent : support.source ≠ source) :
    accepts (withdraw ctx source) claim support = true :=
  (accepted_after_withdrawal_iff ctx claim support source).mpr ⟨accepted, independent⟩

def hasPolarity (ctx : Context) (claim : Claim) (positive : Bool) : Bool :=
  ctx.interpreted.any fun support => accepts ctx claim support && decide (support.positive = positive)

theorem hasPolarity_iff (ctx : Context) (claim : Claim) (positive : Bool) :
    hasPolarity ctx claim positive = true ↔
      ∃ support ∈ ctx.interpreted, accepts ctx claim support = true ∧ support.positive = positive := by
  simp [hasPolarity, List.any_eq_true]

theorem withdrawal_creates_no_polarity (ctx : Context) (claim : Claim)
    (source : Source) (positive : Bool)
    (after : hasPolarity (withdraw ctx source) claim positive = true) :
    hasPolarity ctx claim positive = true := by
  obtain ⟨support, member, accepted, polarity⟩ :=
    (hasPolarity_iff (withdraw ctx source) claim positive).mp after
  apply (hasPolarity_iff ctx claim positive).mpr
  exact ⟨support, member,
    ((accepted_after_withdrawal_iff ctx claim support source).mp accepted).1, polarity⟩

theorem withdrawal_does_not_invent_negation (ctx : Context) (claim : Claim)
    (source : Source) (absent : hasPolarity ctx claim false = false) :
    hasPolarity (withdraw ctx source) claim false = false := by
  cases after : hasPolarity (withdraw ctx source) claim false with
  | false => rfl
  | true =>
    have before := withdrawal_creates_no_polarity ctx claim source false after
    simp_all

theorem independently_supported_claim_survives (ctx : Context) (claim : Claim)
    (source : Source) (support : Support)
    (accepted : accepts ctx claim support = true)
    (independent : support.source ≠ source) (positive : support.positive = true) :
    hasPolarity (withdraw ctx source) claim true = true := by
  apply (hasPolarity_iff (withdraw ctx source) claim true).mpr
  exact ⟨support, ((accepts_iff ctx claim support).mp accepted).2.1,
    independent_support_survives ctx claim support source accepted independent, positive⟩

end Nabt.RationalInquiry
