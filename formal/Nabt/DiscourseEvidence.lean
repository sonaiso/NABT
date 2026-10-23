import Nabt.ArabicReading
import Nabt.Governors

/-!
# Conditional reference and qualified discourse projection

Native NABT law informed by Alghanem@9d8fa03a51f894416e0abaf3b6821c5ae6441dcd
(`A116.Ihala`, `A116.IhalaHasr`, `A116.Istiqama`) and MIT-licensed
Mashru@e4c801ffe9171dadedcc3aae23051ea0953ae361 (`SLGE.Maqam`,
`Nizam.Talab`, `Aql.AdawatMaani`). See docs/DISCOURSE_SOURCE_AUDIT.md.

All features, reference identities, licenses, scope boundaries and force are
supplied premises here. A finite candidate set is not automatically complete.
Unknown features preserve a possibility, but do not confirm agreement. A
unique result is relative to a declared closed candidate universe. Neither a
case mark nor a syntactic role is an input to reference or speech-force laws.

The force codes 0..7 preserve ArabicReading.Mood; quotation is a separate ninth
barrier. Assertion is a source-attributed commitment, not external truth.
Projection preserves the entire signed claim, including tense/time/place and
restriction. A negative conjunction is not projected into two negative atoms.
Causal licensing is separate from a truth-functional implication value.

These proofs concern the algebra and its finite exporter. They do not prove
source authenticity, Unicode parsing, free-text reading, pragmatics, reference
to external entities, or the linguistic validity of a caller's premises.
-/

namespace Nabt.DiscourseEvidence

def lawId : String := "nabt.discourse-evidence.v1"

/-- These are requirements of already licensed roles, never roles inferred
from case. Qatr 152–166 and 297–300 supply the nominal premises.
The imperfect-indicative role additionally needs a known inflected imperfect
and witnessed absence of a governor inside a complete clause (Qatr 96–98). -/
inductive DiscourseRole where
  | subject | predicate | timeAdverb | placeAdverb | imperfectIndicative
  deriving DecidableEq, Repr
def discourseRoles : List DiscourseRole := [.subject, .predicate, .timeAdverb, .placeAdverb, .imperfectIndicative]
def DiscourseRole.label : DiscourseRole → String
  | .subject => "nominal_subject" | .predicate => "nominal_predicate"
  | .timeAdverb => "time_adverb" | .placeAdverb => "place_adverb"
  | .imperfectIndicative => "imperfect_indicative"
def DiscourseRole.requiredCase : DiscourseRole → Governors.Case
  | .subject | .predicate | .imperfectIndicative => .raf
  | .timeAdverb | .placeAdverb => .nasb
theorem same_case_does_not_choose_nominal_role :
    DiscourseRole.subject.requiredCase = DiscourseRole.predicate.requiredCase ∧
    DiscourseRole.subject ≠ DiscourseRole.predicate ∧
    DiscourseRole.timeAdverb.requiredCase = DiscourseRole.placeAdverb.requiredCase ∧
    DiscourseRole.timeAdverb ≠ DiscourseRole.placeAdverb := by decide

inductive Compatibility where
  | possible | confirmed | conflict
  deriving DecidableEq, Repr

def compatibilities : List Compatibility := [.possible, .confirmed, .conflict]
def Compatibility.code : Compatibility → Nat
  | .possible => 0 | .confirmed => 1 | .conflict => 2
def Compatibility.label : Compatibility → String
  | .possible => "possible" | .confirmed => "confirmed" | .conflict => "conflict"

def featureCompatibility (left right : Option Nat) : Compatibility :=
  match left, right with
  | some a, some b => if a = b then .confirmed else .conflict
  | _, _ => .possible

def combineCompatibility : Compatibility → Compatibility → Compatibility
  | .conflict, _ | _, .conflict => .conflict
  | .possible, _ | _, .possible => .possible
  | .confirmed, .confirmed => .confirmed

theorem unknown_left_possible (right : Option Nat) :
    featureCompatibility none right = .possible := by cases right <;> rfl
theorem unknown_right_possible (left : Option Nat) :
    featureCompatibility left none = .possible := by cases left <;> rfl
theorem known_confirmed_iff (a b : Nat) :
    featureCompatibility (some a) (some b) = .confirmed ↔ a = b := by
  simp [featureCompatibility]
theorem known_conflict_iff (a b : Nat) :
    featureCompatibility (some a) (some b) = .conflict ↔ a ≠ b := by
  simp [featureCompatibility]
theorem compatibility_symmetric (a b : Option Nat) :
    featureCompatibility a b = featureCompatibility b a := by
  cases a <;> cases b <;> simp [featureCompatibility, eq_comm]
theorem combine_commutative (a b : Compatibility) :
    combineCompatibility a b = combineCompatibility b a := by cases a <;> cases b <;> rfl
theorem combine_associative (a b c : Compatibility) :
    combineCompatibility (combineCompatibility a b) c =
      combineCompatibility a (combineCompatibility b c) := by
  cases a <;> cases b <;> cases c <;> rfl
theorem combine_confirmed_iff (a b : Compatibility) :
    combineCompatibility a b = .confirmed ↔ a = .confirmed ∧ b = .confirmed := by
  cases a <;> cases b <;> decide
theorem unknown_is_not_confirmation : featureCompatibility none none ≠ .confirmed := by decide

/-- Unknown constraints keep candidates; known conflict removes them. -/
def filterCandidates {α : Type} (candidates : List α)
    (evidence : List (α → Compatibility)) : List α :=
  candidates.filter fun candidate => evidence.all fun check => check candidate != .conflict

theorem candidate_filter_exact {α : Type} (candidates : List α)
    (evidence : List (α → Compatibility)) (candidate : α) :
    candidate ∈ filterCandidates candidates evidence ↔
      candidate ∈ candidates ∧ ∀ check ∈ evidence, check candidate ≠ .conflict := by
  simp [filterCandidates, List.all_eq_true]
theorem deleting_features_widens {α : Type} (candidates : List α)
    (old extra : List (α → Compatibility)) (candidate : α)
    (h : candidate ∈ filterCandidates candidates (old ++ extra)) :
    candidate ∈ filterCandidates candidates old := by
  rw [candidate_filter_exact] at h ⊢
  exact ⟨h.1, fun check member => h.2 check (List.mem_append_left _ member)⟩

inductive ReferenceOrigin where
  | named | antecedent | speaker | addressee | deictic | relativeReturn
  deriving DecidableEq, Repr

def referenceOrigins : List ReferenceOrigin :=
  [.named, .antecedent, .speaker, .addressee, .deictic, .relativeReturn]
def ReferenceOrigin.code : ReferenceOrigin → Nat
  | .named => 0 | .antecedent => 1 | .speaker => 2 | .addressee => 3
  | .deictic => 4 | .relativeReturn => 5
def ReferenceOrigin.label : ReferenceOrigin → String
  | .named => "named" | .antecedent => "antecedent" | .speaker => "speaker"
  | .addressee => "addressee" | .deictic => "deictic" | .relativeReturn => "relative_return"

structure ReferenceWitness where
  originLicensed : Bool
  identityBound : Bool
  sourceSupported : Bool
  scopeAllowed : Bool
  quoteAllowed : Bool
  orderLicensed : Bool
  returnLicensed : Bool
  deriving DecidableEq, Repr

def referenceAllowed (origin : ReferenceOrigin) (status : Compatibility)
    (w : ReferenceWitness) : Bool :=
  status != .conflict && w.originLicensed && w.identityBound && w.sourceSupported &&
  w.scopeAllowed && w.quoteAllowed &&
  (origin != .antecedent || w.orderLicensed) &&
  (origin != .relativeReturn || w.returnLicensed)

theorem reference_requires_identity (origin : ReferenceOrigin) (status : Compatibility)
    (w : ReferenceWitness) (h : referenceAllowed origin status w = true) :
    w.identityBound = true := by simp_all [referenceAllowed]
theorem reference_requires_scope (origin : ReferenceOrigin) (status : Compatibility)
    (w : ReferenceWitness) (h : referenceAllowed origin status w = true) :
    w.scopeAllowed = true ∧ w.quoteAllowed = true := by simp_all [referenceAllowed]
theorem reference_requires_source (origin : ReferenceOrigin) (status : Compatibility)
    (w : ReferenceWitness) (h : referenceAllowed origin status w = true) :
    w.originLicensed = true ∧ w.sourceSupported = true := by simp_all [referenceAllowed]
theorem reference_conflict_blocked (origin : ReferenceOrigin) (w : ReferenceWitness) :
    referenceAllowed origin .conflict w = false := by simp [referenceAllowed]
theorem antecedent_requires_order (status : Compatibility) (w : ReferenceWitness)
    (h : referenceAllowed .antecedent status w = true) : w.orderLicensed = true := by
  simp_all [referenceAllowed]
theorem relative_requires_return (status : Compatibility) (w : ReferenceWitness)
    (h : referenceAllowed .relativeReturn status w = true) : w.returnLicensed = true := by
  simp_all [referenceAllowed]

inductive SelectionStatus where
  | openScope | noCandidate | unresolvedFeatures | ambiguous | resolved
  deriving DecidableEq, Repr
def SelectionStatus.label : SelectionStatus → String
  | .openScope => "OPEN_SCOPE" | .noCandidate => "NO_CANDIDATE"
  | .unresolvedFeatures => "UNRESOLVED_FEATURES" | .ambiguous => "AMBIGUOUS"
  | .resolved => "RESOLVED"

/-- Count distinct surviving entity identities, not duplicate source receipts. -/
def selectionStatus (count : Nat) (closedScope allConfirmed : Bool) : SelectionStatus :=
  if !closedScope then .openScope
  else if count = 0 then .noCandidate
  else if count ≠ 1 then .ambiguous
  else if !allConfirmed then .unresolvedFeatures
  else .resolved

theorem resolved_exact (count : Nat) (closedScope allConfirmed : Bool) :
    selectionStatus count closedScope allConfirmed = .resolved ↔
      closedScope = true ∧ count = 1 ∧ allConfirmed = true := by
  cases count with
  | zero => cases closedScope <;> cases allConfirmed <;> decide
  | succ n =>
    cases n with
    | zero => cases closedScope <;> cases allConfirmed <;> decide
    | succ n => cases closedScope <;> cases allConfirmed <;> simp [selectionStatus]
theorem open_scope_never_resolved (count : Nat) (confirmed : Bool) :
    selectionStatus count false confirmed = .openScope := rfl
theorem multiple_candidates_no_guess (confirmed : Bool) :
    selectionStatus 2 true confirmed = .ambiguous := rfl
theorem unknown_singleton_unresolved :
    selectionStatus 1 true false = .unresolvedFeatures := rfl

inductive Force where
  | assertive | question | command | prohibition | wish | hope | vocative | ambiguous | quoted
  deriving DecidableEq, Repr
def forces : List Force :=
  [.assertive, .question, .command, .prohibition, .wish, .hope, .vocative, .ambiguous, .quoted]
def Force.code : Force → Nat
  | .assertive => 0 | .question => 1 | .command => 2 | .prohibition => 3
  | .wish => 4 | .hope => 5 | .vocative => 6 | .ambiguous => 7 | .quoted => 8
def Force.label : Force → String
  | .assertive => "ASSERT" | .question => "QUESTION" | .command => "COMMAND"
  | .prohibition => "PROHIBITION" | .wish => "WISH" | .hope => "HOPE"
  | .vocative => "VOCATIVE" | .ambiguous => "AMBIGUOUS" | .quoted => "QUOTED"
def forceOfMood : ArabicReading.Mood → Force
  | .assertive => .assertive | .question => .question | .command => .command
  | .prohibition => .prohibition | .wish => .wish | .hope => .hope
  | .vocative => .vocative | .ambiguous => .ambiguous
theorem legacy_mood_codes_preserved (mood : ArabicReading.Mood) :
    (forceOfMood mood).code = mood.code := by cases mood <;> rfl

structure AssertionWitness where
  licensedSyntax : Bool
  scopeComplete : Bool
  referencesComplete : Bool
  qualifiersPreserved : Bool
  nonquoted : Bool
  sourceSupported : Bool
  deriving DecidableEq, Repr
def assertionAllowed (force : Force) (w : AssertionWitness) : Bool :=
  force == .assertive && w.licensedSyntax && w.scopeComplete && w.referencesComplete &&
  w.qualifiersPreserved && w.nonquoted && w.sourceSupported

theorem assertion_requires_force (force : Force) (w : AssertionWitness)
    (h : assertionAllowed force w = true) : force = .assertive := by simp_all [assertionAllowed]
theorem assertion_requires_qualified_scope (force : Force) (w : AssertionWitness)
    (h : assertionAllowed force w = true) :
    w.scopeComplete = true ∧ w.referencesComplete = true ∧ w.qualifiersPreserved = true := by
  simp_all [assertionAllowed]
theorem assertion_requires_source (force : Force) (w : AssertionWitness)
    (h : assertionAllowed force w = true) : w.sourceSupported = true := by
  simp_all [assertionAllowed]
theorem quoted_never_asserts (w : AssertionWitness) : assertionAllowed .quoted w = false := rfl
theorem nonassertive_never_asserts (force : Force) (w : AssertionWitness)
    (h : force ≠ .assertive) : assertionAllowed force w = false := by
  simp [assertionAllowed, h]
theorem unlicensed_quote_never_asserts (force : Force) (w : AssertionWitness)
    (h : w.nonquoted = false) : assertionAllowed force w = false := by simp [assertionAllowed, h]

inductive Polarity where
  | positive | negative
  deriving DecidableEq, Repr
def polarities : List Polarity := [.positive, .negative]
def Polarity.label : Polarity → String | .positive => "positive" | .negative => "negative"
def negate : Polarity → Polarity | .positive => .negative | .negative => .positive
theorem double_negation (polarity : Polarity) : negate (negate polarity) = polarity := by cases polarity <;> rfl

inductive Connector where
  | conjunction | disjunction | exclusive | implication
  deriving DecidableEq, Repr
def connectors : List Connector := [.conjunction, .disjunction, .exclusive, .implication]
def Connector.label : Connector → String
  | .conjunction => "AND" | .disjunction => "OR" | .exclusive => "XOR" | .implication => "IMPLIES"
def truthValue (connector : Connector) (left right : Bool) : Bool :=
  match connector with
  | .conjunction => left && right
  | .disjunction => left || right
  | .exclusive => left != right
  | .implication => !left || right
def projectBranches (connector : Connector) (polarity : Polarity) : Bool :=
  connector == .conjunction && polarity == .positive
theorem branch_projection_exact (connector : Connector) (polarity : Polarity) :
    projectBranches connector polarity = true ↔
      connector = .conjunction ∧ polarity = .positive := by simp [projectBranches]
theorem negative_conjunction_no_branch : projectBranches .conjunction .negative = false := rfl
theorem disjunction_no_branch (polarity : Polarity) : projectBranches .disjunction polarity = false := rfl
theorem implication_no_branch (polarity : Polarity) : projectBranches .implication polarity = false := rfl

/-- Source-relative ground content. Absence of a qualifier is itself preserved. -/
structure QualifiedClaim where
  predicate : String
  arguments : List String
  polarity : Polarity
  tense : Option String
  time : Option String
  place : Option String
  restriction : Option String
  deriving DecidableEq, Repr

def projectClaim (force : Force) (w : AssertionWitness) (claim : QualifiedClaim) : Option QualifiedClaim :=
  if assertionAllowed force w then some claim else none
theorem projected_claim_exact (force : Force) (w : AssertionWitness) (claim result : QualifiedClaim)
    (h : projectClaim force w claim = some result) : result = claim := by
  unfold projectClaim at h
  split at h
  · exact (Option.some.inj h).symm
  · contradiction
theorem projected_claim_keeps_qualifiers (force : Force) (w : AssertionWitness)
    (claim result : QualifiedClaim) (h : projectClaim force w claim = some result) :
    result.polarity = claim.polarity ∧ result.tense = claim.tense ∧ result.time = claim.time ∧
    result.place = claim.place ∧ result.restriction = claim.restriction := by
  have same := projected_claim_exact force w claim result h
  subst result
  exact ⟨rfl, rfl, rfl, rfl, rfl⟩
theorem projected_claim_requires_gate (force : Force) (w : AssertionWitness)
    (claim result : QualifiedClaim) (h : projectClaim force w claim = some result) :
    assertionAllowed force w = true := by
  unfold projectClaim at h
  split at h
  · assumption
  · contradiction

def claimProjectionAllowed (predicate arguments polarity tense time place restriction : Bool) : Bool :=
  predicate && arguments && polarity && tense && time && place && restriction
theorem claim_projection_exact (predicate arguments polarity tense time place restriction : Bool) :
    claimProjectionAllowed predicate arguments polarity tense time place restriction = true ↔
    predicate = true ∧ arguments = true ∧ polarity = true ∧ tense = true ∧
      time = true ∧ place = true ∧ restriction = true := by
  simp [claimProjectionAllowed, and_assoc]

/-- A causal relation requires an independent qualified witness. Truth value
of implication is deliberately not an argument to this gate. -/
def causalAllowed (relationLicensed sourceSupported scopeComplete endpointsResolved : Bool) : Bool :=
  relationLicensed && sourceSupported && scopeComplete && endpointsResolved
theorem causal_requires_relation (relationLicensed sourceSupported scopeComplete endpointsResolved : Bool)
    (h : causalAllowed relationLicensed sourceSupported scopeComplete endpointsResolved = true) :
    relationLicensed = true := by simp_all [causalAllowed]
theorem implication_truth_not_causal_license :
    truthValue .implication false false = true ∧ causalAllowed false true true true = false := by decide

end Nabt.DiscourseEvidence
