import Nabt.RecursiveLicensedAlgebra
import Nabt.ArabicCoverage

/-!
# Explicit contracts for meaning preservation

The abstract results concern supplied partial algebras, independent observation
functions and independently specified reference relations. They do not establish
Arabic adequacy, a complete ontology, agreement of human minds, or world truth.

The finite instance checks whole joint readings after an executable adapter has
decoded an actual transported JSON payload. Parser refinement is an executable
conformance boundary, not a theorem asserted by this module. See the frozen
MEANING_PRESERVATION_V1 specifications for the wire domain and its limits.
-/

namespace Nabt.MeaningPreservation

set_option autoImplicit false

def lawId : String := "nabt.meaning-preservation.v1"
def queryId : String := "joint-readings.v1"
def codecId : String := "strict-json-packet.v1"

open RecursiveLicensedAlgebra in
/-- A single-carrier partial algebra over the existing ordered structural tree.
`none` means undefined by these operations, not meaningless in Arabic. A bridge
between definedness and a grammar's `Certified` predicate is a separate premise. -/
structure PartialAlgebra (α : Type) where
  seed : Seed → Option α
  unary : Nat → α → Option α
  binary : Nat → α → α → Option α

open RecursiveLicensedAlgebra in
def eval {α : Type} (algebra : PartialAlgebra α) : Tree → Option α
  | .leaf s => algebra.seed s
  | .unary rule child => (eval algebra child).bind (algebra.unary rule)
  | .binary rule left right => (eval algebra left).bind fun a =>
      (eval algebra right).bind (algebra.binary rule a)

open RecursiveLicensedAlgebra in
/-- Equalities of complete Option results preserve and reflect definedness on
the image of `h`. No injectivity or linguistic adequacy is assumed. -/
structure Hom {α β : Type} (source : PartialAlgebra α) (target : PartialAlgebra β)
    (h : α → β) : Prop where
  seed : ∀ s, (source.seed s).map h = target.seed s
  unary : ∀ rule a, (source.unary rule a).map h = target.unary rule (h a)
  binary : ∀ rule a b,
    (source.binary rule a b).map h = target.binary rule (h a) (h b)

open RecursiveLicensedAlgebra in
theorem eval_transport {α β : Type} (source : PartialAlgebra α)
    (target : PartialAlgebra β) (h : α → β) (hom : Hom source target h)
    (tree : Tree) : (eval source tree).map h = eval target tree := by
  induction tree with
  | leaf s => exact hom.seed s
  | unary rule child ih =>
      simp only [eval]
      rw [← ih]
      cases value : eval source child with
      | none => rfl
      | some a => exact hom.unary rule a
  | binary rule left right ihl ihr =>
      simp only [eval]
      rw [← ihl, ← ihr]
      cases first : eval source left with
      | none => rfl
      | some a =>
          cases second : eval source right with
          | none => rfl
          | some b => exact hom.binary rule a b

open RecursiveLicensedAlgebra in
theorem eval_definedness_iff {α β : Type} (source : PartialAlgebra α)
    (target : PartialAlgebra β) (h : α → β) (hom : Hom source target h)
    (tree : Tree) : eval source tree = none ↔ eval target tree = none := by
  rw [← eval_transport source target h hom tree]
  simp

/-- Algebraic preservation alone does not supply this independent equation. -/
def Faithful {α β Q O : Type} (h : α → β)
    (observeSource : α → Q → O) (observeTarget : β → Q → O) : Prop :=
  ∀ a q, observeTarget (h a) q = observeSource a q

open RecursiveLicensedAlgebra in
theorem observed_eval_preserved {α β Q O : Type} (source : PartialAlgebra α)
    (target : PartialAlgebra β) (h : α → β) (hom : Hom source target h)
    (observeSource : α → Q → O) (observeTarget : β → Q → O)
    (faithful : Faithful h observeSource observeTarget) (tree : Tree) (query : Q) :
    (eval target tree).map (fun b => observeTarget b query) =
      (eval source tree).map (fun a => observeSource a query) := by
  rw [← eval_transport source target h hom tree]
  cases value : eval source tree with
  | none => rfl
  | some a => exact congrArg some (faithful a query)

/-- Recoverability is relative to the distinctions expressed by `query`. -/
def FiberCompatible {X R Y : Type} (encode : X → R) (query : X → Y) : Prop :=
  ∀ x y, encode x = encode y → query x = query y

def Image {X R : Type} (encode : X → R) := {value : R // ∃ x, encode x = value}

def imagePoint {X R : Type} (encode : X → R) (x : X) : Image encode :=
  ⟨encode x, x, rfl⟩

def DecoderCorrect {X R Y : Type} (encode : X → R) (query : X → Y)
    (decode : Image encode → Y) : Prop :=
  ∀ x, decode (imagePoint encode x) = query x

/-- Existence and uniqueness are on the image only, including an empty source
domain. Classical witness selection here is not an executable decoder or a
claim about human cognition. The collision impossibility is already available
as `ArabicCoverage.no_single_interpreter_of_observation_collision`. -/
theorem unique_decoder_on_image_iff {X R Y : Type} (encode : X → R) (query : X → Y) :
    (∃ decode : Image encode → Y, DecoderCorrect encode query decode ∧
      ∀ other, DecoderCorrect encode query other → other = decode) ↔
      FiberCompatible encode query := by
  constructor
  · rintro ⟨decode, correct, _⟩ x y same
    calc
      query x = decode (imagePoint encode x) := (correct x).symm
      _ = decode (imagePoint encode y) := congrArg decode (Subtype.ext same)
      _ = query y := correct y
  · intro compatible
    classical
    let decode : Image encode → Y := fun value => query (Classical.choose value.property)
    have correct : DecoderCorrect encode query decode := by
      intro x
      exact compatible _ x (Classical.choose_spec (imagePoint encode x).property)
    refine ⟨decode, correct, ?_⟩
    intro other otherCorrect
    funext value
    obtain ⟨x, witness⟩ := value.property
    have same : imagePoint encode x = value := Subtype.ext witness
    calc
      other value = other (imagePoint encode x) := congrArg other same.symm
      _ = query x := otherCorrect x
      _ = decode (imagePoint encode x) := (correct x).symm
      _ = decode value := congrArg decode same

/-- Keep the whole observation function of one reading as a single result.
Taking separate existential projections for individual queries could lose
correlations, so that weaker operation is not used here. -/
def ObservationRelation {Input α Q O : Type} (readings : Input → α → Prop)
    (observe : α → Q → O) : Input → (Q → O) → Prop :=
  fun input result => ∃ reading, readings input reading ∧ observe reading = result

/-- Textual exactness is a premise, not a consequence of tree induction. The
target must be exactly the transported image of all source readings within
the stated domain, and observation fidelity is an independent premise. -/
theorem observations_exact_with_transport {Input α β Q O : Type}
    (domain : Input → Prop) (reference recognized : Input → α → Prop)
    (target : Input → β → Prop) (h : α → β)
    (observeSource : α → Q → O) (observeTarget : β → Q → O)
    (sourceExact : ArabicCoverage.ExactWithin domain reference recognized)
    (targetImage : ∀ input, domain input → ∀ b,
      target input b ↔ ∃ a, recognized input a ∧ h a = b)
    (faithful : Faithful h observeSource observeTarget) :
    ArabicCoverage.ExactWithin domain
      (ObservationRelation reference observeSource)
      (ObservationRelation target observeTarget) := by
  intro input covered result
  constructor
  · rintro ⟨b, accepted, observation⟩
    obtain ⟨a, recognizedA, mapped⟩ := (targetImage input covered b).mp accepted
    refine ⟨a, (sourceExact input covered a).mp recognizedA, ?_⟩
    have faithfulFunction : observeTarget (h a) = observeSource a := funext (faithful a)
    exact faithfulFunction.symm.trans ((congrArg observeTarget mapped).trans observation)
  · rintro ⟨a, licensed, observation⟩
    refine ⟨h a, (targetImage input covered (h a)).mpr
      ⟨a, (sourceExact input covered a).mpr licensed, rfl⟩, ?_⟩
    exact (funext (faithful a)).trans observation

/-! ## Finite installed joint-reading query

The adapter validates wire bounds and derives `decoded` from the actual JSON
payload. These typed records retain that payload in full; its equality, not a
label or hash, determines an encoding fiber. The following logical contract is
independent of the decision procedure and of its diagnostic scan order.
-/

inductive TermKind where
  | entity | speaker | addressee | time | place
  deriving DecidableEq, Repr

structure Term where
  kind : TermKind
  value : String
  deriving DecidableEq, Repr

structure Context where
  speaker : String
  addressee : String
  time : String
  place : String
  deriving DecidableEq, Repr

structure Binding where
  sourceId : String
  revision : String
  scope : String
  sourceText : String
  convention : String
  deriving DecidableEq, Repr

inductive Tense where
  | past | present | future | unspecified
  deriving DecidableEq, Repr

inductive Voice where
  | active | passive | unspecified
  deriving DecidableEq, Repr

inductive Force where
  | asserted | quoted | hypothetical | question
  deriving DecidableEq, Repr

structure Reading where
  predicate : String
  subject : Term
  object : Option Term
  positive : Bool
  tense : Tense
  voice : Voice
  force : Force
  deriving DecidableEq, Repr

structure Packet where
  binding : Binding
  sourceContext : Context
  alternatives : List Reading
  deriving DecidableEq, Repr

structure ResolvedTerm where
  kind : TermKind
  value : String
  deriving DecidableEq, Repr

/-- The tag survives resolution. Recipient context is intentionally absent. -/
def resolve (context : Context) (term : Term) : ResolvedTerm :=
  ⟨term.kind, match term.kind with
    | .entity => term.value
    | .speaker => context.speaker
    | .addressee => context.addressee
    | .time => context.time
    | .place => context.place⟩

structure Observation where
  predicate : String
  subject : ResolvedTerm
  object : Option ResolvedTerm
  positive : Bool
  tense : Tense
  voice : Voice
  force : Force
  scope : String
  convention : String
  time : String
  place : String
  deriving DecidableEq, Repr

def observeReading (packet : Packet) (reading : Reading) : Observation :=
  ⟨reading.predicate, resolve packet.sourceContext reading.subject,
    reading.object.map (resolve packet.sourceContext), reading.positive,
    reading.tense, reading.voice, reading.force, packet.binding.scope,
    packet.binding.convention, packet.sourceContext.time, packet.sourceContext.place⟩

def observations (packet : Packet) : List Observation :=
  packet.alternatives.map (observeReading packet)

def SameObservations (first second : Packet) : Prop :=
  (∀ value ∈ observations first, value ∈ observations second) ∧
    (∀ value ∈ observations second, value ∈ observations first)

instance (first second : Packet) : Decidable (SameObservations first second) := by
  unfold SameObservations
  infer_instance

/-- A set of whole tuples, rather than independently projected field sets. -/
def jointQuery (packet : Packet) : Observation → Prop :=
  fun value => value ∈ observations packet

theorem same_observations_iff_query_eq (first second : Packet) :
    SameObservations first second ↔ jointQuery first = jointQuery second := by
  constructor
  · rintro ⟨forward, backward⟩
    funext value
    exact propext ⟨forward value, backward value⟩
  · intro equal
    constructor
    · intro value member
      change jointQuery second value
      rw [← equal]
      exact member
    · intro value member
      change jointQuery first value
      rw [equal]
      exact member

/-- The adapter, not a caller-supplied reconstructed field, supplies decoded. -/
structure DecodedCase where
  caseId : String
  original : Packet
  transportedPayload : String
  decoded : Packet
  deriving DecidableEq, Repr

def CasePreserved (item : DecodedCase) : Prop :=
  item.original.binding = item.decoded.binding ∧
    item.original.sourceContext = item.decoded.sourceContext ∧
    SameObservations item.original item.decoded

def FiniteContract (cases : List DecodedCase) : Prop :=
  (∀ first ∈ cases, ∀ second ∈ cases,
    first.transportedPayload = second.transportedPayload →
      SameObservations first.original second.original) ∧
    (∀ item ∈ cases, CasePreserved item)

inductive Violation where
  | fiberCollision (first second : String)
  | sourceBindingChanged (caseId : String)
  | sourceContextChanged (caseId : String)
  | observationChanged (caseId : String)
  deriving DecidableEq, Repr

def Violation.reason : Violation → String
  | .fiberCollision _ _ => "FIBER_COLLISION"
  | .sourceBindingChanged _ => "SOURCE_BINDING_CHANGED"
  | .sourceContextChanged _ => "SOURCE_CONTEXT_CHANGED"
  | .observationChanged _ => "OBSERVATION_CHANGED"

def Violation.firstId : Violation → String
  | .fiberCollision first _ => first
  | .sourceBindingChanged id | .sourceContextChanged id | .observationChanged id => id

def Violation.otherId : Violation → Option String
  | .fiberCollision _ second => some second
  | _ => none

def localViolation (item : DecodedCase) : Option Violation :=
  if item.original.binding ≠ item.decoded.binding then
    some (.sourceBindingChanged item.caseId)
  else if item.original.sourceContext ≠ item.decoded.sourceContext then
    some (.sourceContextChanged item.caseId)
  else if ¬ SameObservations item.original item.decoded then
    some (.observationChanged item.caseId)
  else none

theorem local_violation_none_iff (item : DecodedCase) :
    localViolation item = none ↔ CasePreserved item := by
  by_cases binding : item.original.binding = item.decoded.binding
  · by_cases context : item.original.sourceContext = item.decoded.sourceContext
    · by_cases observed : SameObservations item.original item.decoded <;>
        simp [localViolation, CasePreserved, binding, context, observed]
    · simp [localViolation, CasePreserved, binding, context]
  · simp [localViolation, CasePreserved, binding]

def collisionFor (cases : List DecodedCase) (first : DecodedCase) : Option Violation :=
  cases.findSome? fun second =>
    if first.transportedPayload = second.transportedPayload ∧
        ¬ SameObservations first.original second.original then
      some (.fiberCollision first.caseId second.caseId)
    else none

theorem collision_for_none_iff (cases : List DecodedCase) (first : DecodedCase) :
    collisionFor cases first = none ↔
      ∀ second ∈ cases, first.transportedPayload = second.transportedPayload →
        SameObservations first.original second.original := by
  simp [collisionFor, List.findSome?_eq_none_iff]

/-- All parses finish before this scan. Fiber witnesses precede local witnesses;
each scan is in the supplied order and retains whole case IDs. -/
def firstViolation (cases : List DecodedCase) : Option Violation :=
  match cases.findSome? (collisionFor cases) with
  | some violation => some violation
  | none => cases.findSome? localViolation

theorem first_violation_none_iff (cases : List DecodedCase) :
    firstViolation cases = none ↔ FiniteContract cases := by
  have collisions : cases.findSome? (collisionFor cases) = none ↔
      ∀ first ∈ cases, ∀ second ∈ cases,
        first.transportedPayload = second.transportedPayload →
          SameObservations first.original second.original := by
    simp only [List.findSome?_eq_none_iff, collision_for_none_iff]
  have locals : cases.findSome? localViolation = none ↔
      ∀ item ∈ cases, CasePreserved item := by
    simp only [List.findSome?_eq_none_iff, local_violation_none_iff]
  unfold firstViolation FiniteContract
  cases found : cases.findSome? (collisionFor cases) with
  | none =>
      exact ⟨fun h => ⟨collisions.mp found, locals.mp h⟩, fun h => locals.mpr h.2⟩
  | some violation =>
      have absent : ¬ (∀ first ∈ cases, ∀ second ∈ cases,
          first.transportedPayload = second.transportedPayload →
            SameObservations first.original second.original) := by
        intro all
        have impossible := collisions.mpr all
        rw [found] at impossible
        contradiction
      simp [absent]

def check (cases : List DecodedCase) : Bool := (firstViolation cases).isNone

theorem finite_check_exact (cases : List DecodedCase) :
    check cases = true ↔ FiniteContract cases := by
  simpa only [check, Option.isNone_iff_eq_none] using first_violation_none_iff cases

theorem finite_check_preserves_each (cases : List DecodedCase)
    (accepted : check cases = true) (item : DecodedCase) (member : item ∈ cases) :
    item.original.binding = item.decoded.binding ∧
      item.original.sourceContext = item.decoded.sourceContext ∧
      SameObservations item.original item.decoded :=
  ((finite_check_exact cases).mp accepted).2 item member

abbrev CaseDomain (cases : List DecodedCase) := {item : DecodedCase // item ∈ cases}

def caseEncoding (cases : List DecodedCase) (item : CaseDomain cases) : String :=
  item.val.transportedPayload

def caseQuery (cases : List DecodedCase) (item : CaseDomain cases) : Observation → Prop :=
  jointQuery item.val.original

/-- The finite source domain is exactly the subtype of supplied cases. This
does not infer a universal fiber condition from a sample of an open domain. -/
theorem finite_check_fiber_compatible (cases : List DecodedCase)
    (accepted : check cases = true) :
    FiberCompatible (caseEncoding cases) (caseQuery cases) := by
  intro first second same
  apply (same_observations_iff_query_eq _ _).mp
  exact ((finite_check_exact cases).mp accepted).1 first.val first.property
    second.val second.property same

theorem finite_check_decoder_on_image (cases : List DecodedCase)
    (accepted : check cases = true) :
    ∃ decode : Image (caseEncoding cases) → (Observation → Prop),
      DecoderCorrect (caseEncoding cases) (caseQuery cases) decode ∧
      ∀ other, DecoderCorrect (caseEncoding cases) (caseQuery cases) other → other = decode :=
  (unique_decoder_on_image_iff _ _).mpr (finite_check_fiber_compatible cases accepted)

end Nabt.MeaningPreservation
