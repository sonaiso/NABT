import Nabt.RationalInquiry

/-!
# Scoped observation and reported-intent evidence

The source registry, interpretation ledger, and origin graph are explicit
premises supplied by a source adapter. The law checks their exact qualified
bindings. It does not authenticate a collector, interpret unrestricted Arabic,
measure private mental states, or establish the fidelity of an outside sensor.

`reportedMotive` means a source records an agent's reported purpose. It is not
`hiddenMotive`. `recordedObservation` means an exact observation record supports
the qualified query. A different value is not automatically a negative record.
Both polarities are retained; conflict never licenses arbitrary consequences.
Completeness here is enumeration of the supplied ledger, not all Arabic or all
possible observations. Existing RationalInquiry source identities are reused.
-/

namespace Nabt.EpistemicMeasurement

abbrev Source := RationalInquiry.Source

def lawId : String := "nabt.epistemic-measurement.v1"

inductive Axis where
  | reportedMotive | recordedObservation | hiddenMotive
  deriving DecidableEq, Repr

def Axis.label : Axis → String
  | .reportedMotive => "reported_motive"
  | .recordedObservation => "recorded_observation"
  | .hiddenMotive => "hidden_motive"

inductive Kind where
  | selfReport | observation | lexical | grammar | hypothetical | quotation
  deriving DecidableEq, Repr

structure Key where
  axis : Axis
  entity : String
  predicate : String
  value : String
  unit : String
  context : String
  time : Int
  place : String
  deriving DecidableEq, Repr

structure Query where
  key : Key
  positive : Bool
  origin : String
  deriving DecidableEq, Repr

structure Origin where
  id : String
  parents : List String
  deriving DecidableEq, Repr

structure Evidence where
  id : String
  source : Source
  key : Key
  positive : Bool
  kind : Kind
  origin : String
  ancestry : List String
  deriving DecidableEq, Repr

structure Context where
  activeSources : List Source
  origins : List Origin
  interpretations : List Evidence
  deriving DecidableEq, Repr

/-- The graph is a declared source lineage. It is not inferred from grammar. -/
def Parent (graph : List Origin) (child parent : String) : Prop :=
  ∃ node ∈ graph, node.id = child ∧ parent ∈ node.parents

inductive Path (graph : List Origin) : String → String → Prop where
  | refl (origin : String) : Path graph origin origin
  | step {a b c : String} : Parent graph a b → Path graph b c → Path graph a c

/-- Oversets are safe: they may defer evidence but cannot conceal a parent. -/
def ClosedAncestry (graph : List Origin) (ancestry : List String) : Prop :=
  ∀ node ∈ graph, node.id ∈ ancestry → ∀ parent ∈ node.parents, parent ∈ ancestry

instance (graph : List Origin) (ancestry : List String) :
    Decidable (ClosedAncestry graph ancestry) :=
  inferInstanceAs (Decidable (∀ node ∈ graph, node.id ∈ ancestry →
    ∀ parent ∈ node.parents, parent ∈ ancestry))

/-- Excludes the query from the declared source lineage. This is not statistical
independence, source authenticity, or pairwise independence of all records. -/
def Independent (graph : List Origin) (queryOrigin : String) (evidence : Evidence) : Prop :=
  evidence.origin ∈ evidence.ancestry ∧ ClosedAncestry graph evidence.ancestry ∧
  queryOrigin ∉ evidence.ancestry

instance (graph : List Origin) (queryOrigin : String) (evidence : Evidence) :
    Decidable (Independent graph queryOrigin evidence) :=
  inferInstanceAs (Decidable (_ ∧ _ ∧ _))

theorem path_stays_in_closed_ancestry (graph : List Origin) (ancestry : List String)
    (closed : ClosedAncestry graph ancestry) {a b : String}
    (start : a ∈ ancestry) (path : Path graph a b) : b ∈ ancestry := by
  induction path with
  | refl => exact start
  | step edge tail ih =>
    obtain ⟨node, member, same, parent⟩ := edge
    exact ih (closed node member (by simpa [same] using start) _ parent)

theorem independent_excludes_transitive_query_origin (graph : List Origin)
    (queryOrigin : String) (evidence : Evidence)
    (independent : Independent graph queryOrigin evidence) :
    ¬ Path graph evidence.origin queryOrigin := by
  intro path
  exact independent.2.2
    (path_stays_in_closed_ancestry graph evidence.ancestry independent.2.1 independent.1 path)

def Kind.permits : Kind → Axis → Bool
  | .selfReport, .reportedMotive => true
  | .observation, .recordedObservation => true
  | _, _ => false

def Admissible (ctx : Context) (query : Query) (evidence : Evidence) : Prop :=
  evidence ∈ ctx.interpretations ∧ evidence.source ∈ ctx.activeSources ∧
  evidence.key = query.key ∧ evidence.kind.permits query.key.axis = true ∧
  Independent ctx.origins query.origin evidence

instance (ctx : Context) (query : Query) (evidence : Evidence) :
    Decidable (Admissible ctx query evidence) :=
  inferInstanceAs (Decidable (_ ∧ _ ∧ _ ∧ _ ∧ _))

def admits (ctx : Context) (query : Query) (evidence : Evidence) : Bool :=
  decide (Admissible ctx query evidence)

def selected (ctx : Context) (query : Query) : List Evidence :=
  ctx.interpretations.filter (admits ctx query)

theorem selected_exact (ctx : Context) (query : Query) (evidence : Evidence) :
    evidence ∈ selected ctx query ↔ Admissible ctx query evidence := by
  simp only [selected, List.mem_filter, admits, decide_eq_true_eq]
  exact ⟨fun h => h.2, fun h => ⟨h.1, h⟩⟩

theorem selected_has_no_query_dependency (ctx : Context) (query : Query)
    (evidence : Evidence) (member : evidence ∈ selected ctx query) :
    ¬ Path ctx.origins evidence.origin query.origin :=
  independent_excludes_transitive_query_origin ctx.origins query.origin evidence
    ((selected_exact ctx query evidence).mp member).2.2.2.2

theorem selected_preserves_complete_key (ctx : Context) (query : Query)
    (evidence : Evidence) (member : evidence ∈ selected ctx query) :
    evidence.key = query.key := ((selected_exact ctx query evidence).mp member).2.2.1

def Key.asInquiryClaim (key : Key) : RationalInquiry.Claim :=
  ⟨key.context, key.predicate,
    [key.axis.label, key.entity, key.value, key.unit, toString key.time, key.place]⟩

def Evidence.asInquirySupport (evidence : Evidence) : RationalInquiry.Support :=
  ⟨evidence.key.asInquiryClaim, evidence.source, evidence.key.asInquiryClaim.scope,
    evidence.positive, 0⟩

/-- A one-way projection for reusing the weaker source contract. It discards
kind and origin checks and must not be used to admit evidence in this law. -/
def Context.asInquiryContext (ctx : Context) : RationalInquiry.Context :=
  ⟨ctx.activeSources, ctx.interpretations.map Evidence.asInquirySupport⟩

/-- The extension retains the existing exact-source support contract. -/
theorem selected_refines_existing_inquiry_support (ctx : Context) (query : Query)
    (evidence : Evidence) (member : evidence ∈ selected ctx query) :
    RationalInquiry.Accepted ctx.asInquiryContext query.key.asInquiryClaim
      evidence.asInquirySupport := by
  obtain ⟨inLedger, active, same, _, _⟩ := (selected_exact ctx query evidence).mp member
  refine ⟨by simp [Evidence.asInquirySupport, same], ?_, active, ?_, ?_⟩
  · exact List.mem_map.mpr ⟨evidence, inLedger, rfl⟩
  · simp [Key.asInquiryClaim]
  · intro point present
    simpa [Evidence.asInquirySupport, same] using present

def polarity (ctx : Context) (query : Query) (positive : Bool) : List Evidence :=
  (selected ctx query).filter (fun evidence => evidence.positive == positive)

theorem polarity_exact (ctx : Context) (query : Query) (positive : Bool)
    (evidence : Evidence) : evidence ∈ polarity ctx query positive ↔
      Admissible ctx query evidence ∧ evidence.positive = positive := by
  simp [polarity, selected_exact]

def hasPolarity (ctx : Context) (query : Query) (positive : Bool) : Bool :=
  !(polarity ctx query positive).isEmpty

theorem hasPolarity_exact (ctx : Context) (query : Query) (positive : Bool) :
    hasPolarity ctx query positive = true ↔
      ∃ evidence, Admissible ctx query evidence ∧ evidence.positive = positive := by
  constructor
  · intro present
    cases h : polarity ctx query positive with
    | nil => simp [hasPolarity, h] at present
    | cons head tail =>
      exact ⟨head, (polarity_exact ctx query positive head).mp (by simp [h])⟩
  · rintro ⟨evidence, eligible⟩
    have member := (polarity_exact ctx query positive evidence).mpr eligible
    cases h : polarity ctx query positive with
    | nil => simp [h] at member
    | cons head tail => simp [hasPolarity, h]

inductive Verdict where
  | supported | refuted | conflict | unknown | resourceLimit
  deriving DecidableEq, Repr

def Verdict.label : Verdict → String
  | .supported => "SUPPORTED"
  | .refuted => "REFUTED"
  | .conflict => "CONFLICT"
  | .unknown => "UNKNOWN"
  | .resourceLimit => "RESOURCE_LIMIT"

def classify (support refutation : Bool) : Verdict :=
  match support, refutation with
  | true, false => .supported
  | false, true => .refuted
  | true, true => .conflict
  | false, false => .unknown

def assess (ctx : Context) (query : Query) (budget : Nat) : Verdict :=
  if ctx.interpretations.length ≤ budget then
    classify (hasPolarity ctx query query.positive) (hasPolarity ctx query (!query.positive))
  else .resourceLimit

theorem insufficient_budget_is_resource_limit (ctx : Context) (query : Query)
    (budget : Nat) (insufficient : budget < ctx.interpretations.length) :
    assess ctx query budget = .resourceLimit := by simp [assess, Nat.not_le.mpr insufficient]

theorem complete_budget_classification (ctx : Context) (query : Query)
    (budget : Nat) (enough : ctx.interpretations.length ≤ budget) :
    assess ctx query budget =
      classify (hasPolarity ctx query query.positive) (hasPolarity ctx query (!query.positive)) := by
  simp [assess, enough]

theorem supported_iff (ctx : Context) (query : Query) (budget : Nat) :
    assess ctx query budget = .supported ↔
      ctx.interpretations.length ≤ budget ∧
      hasPolarity ctx query query.positive = true ∧
      hasPolarity ctx query (!query.positive) = false := by
  by_cases enough : ctx.interpretations.length ≤ budget
  · simp only [assess, enough, ite_true, true_and]
    cases hasPolarity ctx query query.positive <;>
      cases hasPolarity ctx query (!query.positive) <;> simp [classify]
  · simp [assess, enough]

theorem conflict_retained (ctx : Context) (query : Query) (budget : Nat)
    (enough : ctx.interpretations.length ≤ budget)
    (support : hasPolarity ctx query query.positive = true)
    (refutation : hasPolarity ctx query (!query.positive) = true) :
    assess ctx query budget = .conflict := by simp [assess, enough, support, refutation, classify]

theorem absent_both_is_unknown (ctx : Context) (query : Query) (budget : Nat)
    (enough : ctx.interpretations.length ≤ budget)
    (support : hasPolarity ctx query query.positive = false)
    (refutation : hasPolarity ctx query (!query.positive) = false) :
    assess ctx query budget = .unknown := by simp [assess, enough, support, refutation, classify]

structure Receipt where
  status : Verdict
  supportIds : List String
  refutationIds : List String
  selectedIds : List String
  deriving DecidableEq, Repr

/-- The order is the supplied ledger order. Resource exhaustion never returns
a misleading partial certificate. -/
def receipt (ctx : Context) (query : Query) (budget : Nat) : Receipt :=
  if ctx.interpretations.length ≤ budget then
    ⟨assess ctx query budget,
      (polarity ctx query query.positive).map Evidence.id,
      (polarity ctx query (!query.positive)).map Evidence.id,
      (selected ctx query).map Evidence.id⟩
  else ⟨.resourceLimit, [], [], []⟩

def checkReceipt (ctx : Context) (query : Query) (budget : Nat) (proposed : Receipt) : Bool :=
  decide (proposed = receipt ctx query budget)

theorem certificate_checks_exact_receipt (ctx : Context) (query : Query) (budget : Nat)
    (proposed : Receipt) : checkReceipt ctx query budget proposed = true ↔
      proposed = receipt ctx query budget := by simp [checkReceipt]

theorem complete_certificate_enumerates_all_admissible_ids (ctx : Context) (query : Query)
    (budget : Nat) (proposed : Receipt) (enough : ctx.interpretations.length ≤ budget)
    (checked : checkReceipt ctx query budget proposed = true) (id : String) :
    id ∈ proposed.selectedIds ↔
      ∃ evidence, Admissible ctx query evidence ∧ evidence.id = id := by
  have same := (certificate_checks_exact_receipt ctx query budget proposed).mp checked
  simp only [same, receipt, enough, ite_true, List.mem_map]
  simp only [selected_exact]

theorem unlicensed_kinds_do_not_supply_evidence (ctx : Context) (query : Query)
    (evidence : Evidence)
    (unlicensed : evidence.kind = .lexical ∨ evidence.kind = .grammar ∨
      evidence.kind = .hypothetical ∨ evidence.kind = .quotation) :
    evidence ∉ selected ctx query := by
  intro present
  have permission := ((selected_exact ctx query evidence).mp present).2.2.2.1
  rcases unlicensed with h | h | h | h <;>
    cases axis : query.key.axis <;> simp [h, axis, Kind.permits] at permission

theorem hidden_motive_has_no_installed_license (ctx : Context) (query : Query)
    (hidden : query.key.axis = .hiddenMotive) : selected ctx query = [] := by
  apply List.eq_nil_iff_forall_not_mem.mpr
  intro evidence present
  have permission := ((selected_exact ctx query evidence).mp present).2.2.2.1
  cases kind : evidence.kind <;> simp [kind, hidden, Kind.permits] at permission

/-- Two latent interpretations can share every visible record. This refutes
identification from those records alone, not future empirical mind research. -/
structure LatentModel where
  observations : List Evidence
  hiddenMotive : String
  deriving DecidableEq, Repr

theorem observation_equivalent_hidden_motives (records : List Evidence) :
    ∃ left right : LatentModel,
      left.observations = records ∧ right.observations = records ∧
      left.hiddenMotive ≠ right.hiddenMotive := by
  exact ⟨⟨records, "purpose_a"⟩, ⟨records, "purpose_b"⟩, rfl, rfl,
    by change ("purpose_a" : String) ≠ "purpose_b"; decide⟩

/-- A decoder using only these observations cannot identify both distinct
latent purposes. Additional observation protocols remain an open extension. -/
theorem identical_observations_cannot_identify_both (decode : List Evidence → String)
    (left right : LatentModel) (same : left.observations = right.observations)
    (different : left.hiddenMotive ≠ right.hiddenMotive) :
    ¬ (decode left.observations = left.hiddenMotive ∧
       decode right.observations = right.hiddenMotive) := by
  rintro ⟨l, r⟩
  apply different
  calc
    left.hiddenMotive = decode left.observations := l.symm
    _ = decode right.observations := congrArg decode same
    _ = right.hiddenMotive := r

def relativeTime (event anchor : Int) : Int := event - anchor

theorem common_anchor_translation (event anchor shift : Int) :
    relativeTime (event + shift) (anchor + shift) = relativeTime event anchor := by
  unfold relativeTime
  omega

/-- Grammar, event type, volition, and causal evidence are separate coordinates.
These are models of missing entailments, not annotated Arabic corpus results. -/
structure OntologicalReading where
  nominal : Bool
  eventive : Bool
  verbal : Bool
  voluntary : Bool
  earlier : Int
  later : Int
  causalEvidence : Bool
  deriving DecidableEq, Repr

theorem nominal_eventive_countermodel :
    ∃ reading : OntologicalReading, reading.nominal = true ∧ reading.eventive = true := by
  exact ⟨⟨true, true, false, false, 0, 1, false⟩, rfl, rfl⟩

theorem nonvoluntary_verb_countermodel :
    ∃ reading : OntologicalReading, reading.verbal = true ∧ reading.voluntary = false := by
  exact ⟨⟨false, true, true, false, 0, 1, false⟩, rfl, rfl⟩

theorem succession_without_causal_evidence :
    ∃ reading : OntologicalReading,
      reading.earlier < reading.later ∧ reading.causalEvidence = false := by
  exact ⟨⟨false, true, true, false, 0, 1, false⟩, by decide, rfl⟩

end Nabt.EpistemicMeasurement
