import Nabt.DiscourseEvidence
import Nabt.InflectionEvidence

/-!
# Conditional construction requirements and qualified operator scope

Native NABT law, informed by MIT-licensed Mashru at
e4c801ffe9171dadedcc3aae23051ea0953ae361, `Jisr/Mulhaqat.lean`, and
Alghanem at 9d8fa03a51f894416e0abaf3b6821c5ae6441dcd. The Arabic source
windows are replayable through `data/source_evidence/construction_policy.json`.

Roles, lexical senses, attachment, agreement regimes, and source licenses are
premises. This is not a free-text parser or a proof of their acquisition.
Case requirements concern a licensed constituent. In particular the nasb of
a kada predicate clause does not assign nasb to its internal imperfect verb.
Unknown construction cannot yield an inflected or local word-case assignment.

The four-axis adjective rule is scoped to a licensed direct-agreement regime
of the real adjective. Causal adjectives and exceptional agreement regimes
need other licenses. Hal/tamyiz here are already qualified nominal accusative
constructions; counted nouns remain governed by the separate numeral law.

Idafa checks require explicit negative evidence for tanwin and the *inflection*
nun; a radical nun is not such evidence. The head-article rule is scoped to
canonical semantic idafa or a licensed verbal-idafa exception. Unknown is not
absence. Total badal and nominal tawkeed preserve an independently licensed
identity; adjacency, inherited case, part and association do not supply it.

The an policy admits the rare permissible forms with kada/kariba. Inception
is a supplied sense family, not an exhaustive lexical list. All scoped senses
below conservatively retain their outer operator; even a lexical certainty
reading cannot yield a bare embedded assertion by this law. Full qualified
projection preserves the exact input. These checks do not establish external
truth, reference, source authenticity or the correctness of Python parsing.
-/

namespace Nabt.ConstructionEvidence

open Governors (Case)
open Morphology (Construction Evidence)
open TextEvidence (Binding SupportSpan)
open DiscourseEvidence (Compatibility combineCompatibility)

def lawId : String := "nabt.construction-evidence.v1"

inductive Family where
  | kana | inna | zanna | kada
  deriving DecidableEq, Repr
def families : List Family := [.kana, .inna, .zanna, .kada]
def Family.label : Family → String
  | .kana => "kana" | .inna => "inna" | .zanna => "zanna" | .kada => "kada"

inductive Role where
  | kanaSubject | kanaPredicate | innaSubject | innaPredicate
  | zannaSubject | zannaObject1 | zannaObject2 | kadaSubject | kadaPredicate
  | idafaComplement | naat | hal | tamyiz | badal | tawkeed | timeAdverb | placeAdverb
  deriving DecidableEq, Repr
def roles : List Role := [.kanaSubject, .kanaPredicate, .innaSubject, .innaPredicate,
  .zannaSubject, .zannaObject1, .zannaObject2, .kadaSubject, .kadaPredicate,
  .idafaComplement, .naat, .hal, .tamyiz, .badal, .tawkeed, .timeAdverb, .placeAdverb]
def Role.label : Role → String
  | .kanaSubject => "kana_subject" | .kanaPredicate => "kana_predicate"
  | .innaSubject => "inna_subject" | .innaPredicate => "inna_predicate"
  | .zannaSubject => "zanna_subject" | .zannaObject1 => "zanna_object1"
  | .zannaObject2 => "zanna_object2" | .kadaSubject => "kada_subject"
  | .kadaPredicate => "kada_predicate" | .idafaComplement => "idafa_complement"
  | .naat => "naat" | .hal => "hal" | .tamyiz => "tamyiz" | .badal => "badal"
  | .tawkeed => "tawkeed" | .timeAdverb => "time_adverb" | .placeAdverb => "place_adverb"
def Role.inherits : Role → Bool
  | .naat | .badal | .tawkeed => true | _ => false
def Role.caseRequirement (role : Role) (inherited : Option Case) : Option Case :=
  match role with
  | .kanaSubject | .innaPredicate | .zannaSubject | .kadaSubject => some .raf
  | .idafaComplement => some .jarr
  | .naat | .badal | .tawkeed =>
    match inherited with
    | some .jazm => none | value => value
  | _ => some .nasb
def Family.roles : Family → List Role
  | .kana => [.kanaSubject, .kanaPredicate]
  | .inna => [.innaSubject, .innaPredicate]
  | .zanna => [.zannaSubject, .zannaObject1, .zannaObject2]
  | .kada => [.kadaSubject, .kadaPredicate]

theorem operator_requirements_exact :
    (Family.kana.roles.map (fun r => r.caseRequirement none)) = [some .raf, some .nasb] ∧
    (Family.inna.roles.map (fun r => r.caseRequirement none)) = [some .nasb, some .raf] ∧
    (Family.zanna.roles.map (fun r => r.caseRequirement none)) = [some .raf, some .nasb, some .nasb] ∧
    (Family.kada.roles.map (fun r => r.caseRequirement none)) = [some .raf, some .nasb] := by decide
theorem role_requirement_not_jazm (role : Role) (inherited : Option Case) :
    role.caseRequirement inherited ≠ some .jazm := by
  cases role <;> cases inherited with
  | none => decide
  | some c => cases c <;> decide
theorem inherited_role_needs_case (role : Role) (h : role.inherits = true) :
    role.caseRequirement none = none := by cases role <;> simp_all [Role.inherits, Role.caseRequirement]
theorem same_case_does_not_choose_hal_tamyiz :
    Role.hal.caseRequirement none = Role.tamyiz.caseRequirement none ∧ Role.hal ≠ Role.tamyiz := by decide

def assignWordCase (role : Role) (inherited : Option Case) (construction : Option Construction) :
    Option InflectionEvidence.ContextualCase :=
  if role = .kadaPredicate then none else do
    let known ← construction
    let c ← role.caseRequirement inherited
    pure ⟨c, InflectionEvidence.constructionDomain known⟩
theorem unknown_word_construction_no_assignment (role : Role) (inherited : Option Case) :
    assignWordCase role inherited none = none := by simp [assignWordCase]
theorem kada_predicate_not_internal_word (inherited : Option Case) (construction : Option Construction) :
    assignWordCase .kadaPredicate inherited construction = none := by simp [assignWordCase]
theorem built_assignment_local (role : Role) (inherited : Option Case)
    (result : InflectionEvidence.ContextualCase)
    (h : assignWordCase role inherited (some .built) = some result) :
    result.domain = .localCase := by
  by_cases hk : role = .kadaPredicate
  · simp [assignWordCase, hk] at h
  simp only [assignWordCase, hk, ↓reduceIte] at h
  cases hc : role.caseRequirement inherited <;> simp [hc] at h
  subst result
  rfl

/-- An outer local requirement leaves every internal assignment untouched. -/
structure ClauseAssignment (α : Type) where
  localCase : Case
  internal : α
  deriving DecidableEq, Repr
def kadaClause (internal : α) : ClauseAssignment α := ⟨.nasb, internal⟩
theorem kada_clause_keeps_internal {α : Type} (internal : α) :
    (kadaClause internal).localCase = .nasb ∧ (kadaClause internal).internal = internal := ⟨rfl, rfl⟩

def agreementStatus (c definiteness gender number : Compatibility) : Compatibility :=
  combineCompatibility (combineCompatibility (combineCompatibility c definiteness) gender) number
theorem agreement_confirmed_exact (c d g n : Compatibility) :
    agreementStatus c d g n = .confirmed ↔
      c = .confirmed ∧ d = .confirmed ∧ g = .confirmed ∧ n = .confirmed := by
  simp [agreementStatus, DiscourseEvidence.combine_confirmed_iff, and_assoc]
theorem agreement_conflict_exact (c d g n : Compatibility) :
    agreementStatus c d g n = .conflict ↔
      c = .conflict ∨ d = .conflict ∨ g = .conflict ∨ n = .conflict := by
  cases c <;> cases d <;> cases g <;> cases n <;> decide
theorem unknown_agreement_not_confirmed (c d g : Compatibility) :
    agreementStatus c d g .possible ≠ .confirmed := by
  intro h
  have hh := (agreement_confirmed_exact _ _ _ _).mp h
  cases hh.2.2.2

inductive IdafaMode where
  | semantic | verbal
  deriving DecidableEq, Repr
def idafaModes : List IdafaMode := [.semantic, .verbal]
def IdafaMode.label : IdafaMode → String | .semantic => "semantic" | .verbal => "verbal"
def absentStatus : Evidence → Compatibility
  | .unknown => .possible | .denied => .confirmed | .affirmed | .conflict => .conflict
def articleStatus (mode : IdafaMode) (exceptionLicensed : Bool) (article : Evidence) : Compatibility :=
  match mode, exceptionLicensed, article with
  | .verbal, true, .affirmed => .confirmed
  | _, _, evidence => absentStatus evidence
def idafaHeadStatus (mode : IdafaMode) (tanwin nun article : Evidence)
    (exceptionLicensed : Bool) : Compatibility :=
  combineCompatibility (combineCompatibility (absentStatus tanwin) (absentStatus nun))
    (articleStatus mode exceptionLicensed article)
theorem idafa_confirmation_needs_absences (mode : IdafaMode) (t n a : Evidence) (exception : Bool)
    (h : idafaHeadStatus mode t n a exception = .confirmed) : t = .denied ∧ n = .denied := by
  have hh := (DiscourseEvidence.combine_confirmed_iff _ _).mp h
  have hn := (DiscourseEvidence.combine_confirmed_iff _ _).mp hh.1
  constructor
  · cases t <;> simp_all [absentStatus]
  · cases n <;> simp_all [absentStatus]
theorem unknown_tanwin_no_confirmation (mode : IdafaMode) (n a : Evidence) (exception : Bool) :
    idafaHeadStatus mode .unknown n a exception ≠ .confirmed := by
  intro h
  have hh := idafa_confirmation_needs_absences _ _ _ _ _ h
  cases hh.1
theorem semantic_article_blocks (t n : Evidence) (exception : Bool) :
    idafaHeadStatus .semantic t n .affirmed exception = .conflict := by
  cases t <;> cases n <;> cases exception <;> rfl
theorem verbal_article_requires_exception (t n : Evidence)
    (h : idafaHeadStatus .verbal t n .affirmed false = .confirmed) : False := by
  cases t <;> cases n <;> simp [idafaHeadStatus, articleStatus, absentStatus, combineCompatibility] at h

inductive AnHead where
  | kada | kariba | asa | awshaka | hara | ikhlaulaqa | inception
  deriving DecidableEq, Repr
def anHeads : List AnHead := [.kada, .kariba, .asa, .awshaka, .hara, .ikhlaulaqa, .inception]
def AnHead.label : AnHead → String
  | .kada => "كاد" | .kariba => "كرب" | .asa => "عسى" | .awshaka => "أوشك"
  | .hara => "حرى" | .ikhlaulaqa => "اخلولق" | .inception => "inception"
inductive AnPolicy where
  | required | permitted | forbidden
  deriving DecidableEq, Repr
def AnPolicy.label : AnPolicy → String
  | .required => "required" | .permitted => "permitted" | .forbidden => "forbidden"
def AnHead.policy : AnHead → AnPolicy
  | .hara | .ikhlaulaqa => .required
  | .inception => .forbidden
  | _ => .permitted
def AnHead.preferredPresent : AnHead → Bool
  | .kada | .kariba | .inception => false | _ => true
def AnHead.allows (head : AnHead) (present : Bool) : Bool :=
  match head.policy with
  | .required => present | .forbidden => !present | .permitted => true
theorem rare_an_forms_remain_permitted :
    AnHead.kada.allows true = true ∧ AnHead.kariba.allows true = true ∧
    AnHead.asa.allows false = true ∧ AnHead.awshaka.allows false = true := by decide
theorem required_and_inception_an_exact (present : Bool) :
    AnHead.hara.allows present = present ∧ AnHead.ikhlaulaqa.allows present = present ∧
    AnHead.inception.allows present = !present := by cases present <;> decide

structure Activation where
  identityBound : Bool
  sourceSupported : Bool
  attachmentLicensed : Bool
  frameComplete : Bool
  senseLicensed : Bool
  unblocked : Bool
  deriving DecidableEq, Repr
def constructionAllowed (_family : Family) (w : Activation) : Bool :=
  w.identityBound && w.sourceSupported && w.attachmentLicensed &&
    w.frameComplete && w.senseLicensed && w.unblocked
theorem construction_activation_exact (family : Family) (w : Activation) :
    constructionAllowed family w = true ↔ w.identityBound = true ∧
      w.sourceSupported = true ∧ w.attachmentLicensed = true ∧
      w.frameComplete = true ∧ w.senseLicensed = true ∧ w.unblocked = true := by
  simp [constructionAllowed, Bool.and_eq_true, and_assoc]

/-- Graph indices identify a particular selected edge; they cannot be replaced
by any adjacent equal-looking occurrence. Nodes carry full reading bindings. -/
structure Context (n : Nat) where
  nodes : Fin n → Binding
  head : Fin n
  target : Fin n
  ruleId : Nat
  family : Family
def Context.valid {n : Nat} (context : Context n) : Bool := decide (
  context.head ≠ context.target ∧
  (context.nodes context.head).sourceId = (context.nodes context.target).sourceId ∧
  (context.nodes context.head).sourceRevision = (context.nodes context.target).sourceRevision ∧
  (context.nodes context.head).scopeId = (context.nodes context.target).scopeId ∧
  (context.nodes context.head).byteStart < (context.nodes context.head).byteEnd ∧
  (context.nodes context.target).byteStart < (context.nodes context.target).byteEnd ∧
  ((context.nodes context.head).byteEnd ≤ (context.nodes context.target).byteStart ∨
   (context.nodes context.target).byteEnd ≤ (context.nodes context.head).byteStart))
structure Receipt (n : Nat) where
  head : Fin n
  target : Fin n
  headBinding : Binding
  targetBinding : Binding
  ruleId : Nat
  attachmentLicensed : Bool
  frameComplete : Bool
  senseLicensed : Bool
  active : Bool
  blocked : Bool
  support : List SupportSpan
  deriving DecidableEq, Repr
def Receipt.matches {n : Nat} (context : Context n) (receipt : Receipt n) : Bool := decide (
  receipt.head = context.head ∧ receipt.target = context.target ∧
  receipt.headBinding = context.nodes context.head ∧
  receipt.targetBinding = context.nodes context.target ∧ receipt.ruleId = context.ruleId)
def Receipt.activation {n : Nat} (context : Context n) (receipt : Receipt n) : Activation :=
  ⟨receipt.matches context && context.valid,
   !receipt.support.isEmpty && receipt.support.all (fun span => span.validFor (context.nodes context.target)),
   receipt.attachmentLicensed, receipt.frameComplete, receipt.senseLicensed,
   receipt.active && !receipt.blocked⟩
def Receipt.admissible {n : Nat} (context : Context n) (receipt : Receipt n) : Bool :=
  constructionAllowed context.family (receipt.activation context)
theorem admitted_edge_and_readings_exact {n : Nat} (context : Context n) (receipt : Receipt n)
    (h : receipt.admissible context = true) :
    receipt.head = context.head ∧ receipt.target = context.target ∧
    receipt.headBinding = context.nodes context.head ∧
    receipt.targetBinding = context.nodes context.target ∧ receipt.ruleId = context.ruleId := by
  have hh := (construction_activation_exact _ _).mp h
  have hi := hh.1
  simp only [Receipt.activation, Bool.and_eq_true, Receipt.matches, decide_eq_true_eq] at hi
  exact hi.1
theorem admitted_context_valid {n : Nat} (context : Context n) (receipt : Receipt n)
    (h : receipt.admissible context = true) : context.valid = true := by
  have hh := (construction_activation_exact _ _).mp h
  have hi := hh.1
  simp only [Receipt.activation, Bool.and_eq_true] at hi
  exact hi.2
theorem admitted_source_scope_and_distinct_nodes {n : Nat} (context : Context n) (receipt : Receipt n)
    (h : receipt.admissible context = true) :
    context.head ≠ context.target ∧
    (context.nodes context.head).sourceId = (context.nodes context.target).sourceId ∧
    (context.nodes context.head).sourceRevision = (context.nodes context.target).sourceRevision ∧
    (context.nodes context.head).scopeId = (context.nodes context.target).scopeId := by
  have valid := admitted_context_valid context receipt h
  simp only [Context.valid, decide_eq_true_eq] at valid
  exact ⟨valid.1, valid.2.1, valid.2.2.1, valid.2.2.2.1⟩
theorem admitted_support_nonempty {n : Nat} (context : Context n) (receipt : Receipt n)
    (h : receipt.admissible context = true) : receipt.support ≠ [] ∧
      ∀ span ∈ receipt.support, span.validFor (context.nodes context.target) = true := by
  have hh := (construction_activation_exact _ _).mp h
  have hs := hh.2.1
  simp only [Receipt.activation, Bool.and_eq_true, Bool.not_eq_true', List.all_eq_true] at hs
  constructor
  · intro empty
    simp [empty] at hs
  · exact hs.2
theorem foreign_graph_edge_rejected {n : Nat} (context : Context n) (receipt : Receipt n)
    (different : receipt.head ≠ context.head ∨ receipt.target ≠ context.target ∨
      receipt.headBinding ≠ context.nodes context.head ∨ receipt.targetBinding ≠ context.nodes context.target) :
    receipt.admissible context = false := by
  apply Bool.eq_false_iff.mpr
  intro accepted
  have same := admitted_edge_and_readings_exact context receipt accepted
  rcases different with hh | ht | hb | tb
  · exact hh same.1
  · exact ht same.2.1
  · exact hb same.2.2.1
  · exact tb same.2.2.2.1
theorem incomplete_frame_rejected {n : Nat} (context : Context n) (receipt : Receipt n)
    (incomplete : receipt.frameComplete = false) : receipt.admissible context = false := by
  simp [Receipt.admissible, Receipt.activation, constructionAllowed, incomplete]
theorem blocked_receipt_rejected {n : Nat} (context : Context n) (receipt : Receipt n)
    (blocked : receipt.blocked = true) : receipt.admissible context = false := by
  simp [Receipt.admissible, Receipt.activation, constructionAllowed, blocked]

inductive Input (n : Nat) where
  | observedAdjacency (head target : Fin n)
  | observedCase (node : Fin n) (value : Case)
  | licensed (receipt : Receipt n)
def Input.accepted {n : Nat} (context : Context n) : Input n → Option (Receipt n)
  | .observedAdjacency _ _ | .observedCase _ _ => none
  | .licensed receipt => if receipt.admissible context then some receipt else none
def accepted {n : Nat} (context : Context n) (inputs : List (Input n)) : List (Receipt n) :=
  inputs.filterMap (Input.accepted context)
theorem observations_do_not_license {n : Nat} (context : Context n) (head target : Fin n)
    (c : Case) (inputs : List (Input n)) :
    accepted context (.observedAdjacency head target :: .observedCase target c :: inputs) =
      accepted context inputs := rfl
theorem empty_input_no_construction {n : Nat} (context : Context n) : accepted context [] = [] := rfl
theorem every_accepted_edge_has_receipt {n : Nat} (context : Context n) (inputs : List (Input n))
    (receipt : Receipt n) (h : receipt ∈ accepted context inputs) :
    Input.licensed receipt ∈ inputs ∧ receipt.admissible context = true := by
  obtain ⟨input, member, someReceipt⟩ := List.mem_filterMap.mp h
  cases input with
  | observedAdjacency head target => simp [Input.accepted] at someReceipt
  | observedCase node value => simp [Input.accepted] at someReceipt
  | licensed value =>
    simp only [Input.accepted] at someReceipt
    split at someReceipt <;> simp_all

inductive IdentityRelation where
  | badalTotal | badalPart | badalAssociation | tawkeed
  deriving DecidableEq, Repr
def identityRelations : List IdentityRelation := [.badalTotal, .badalPart, .badalAssociation, .tawkeed]
def IdentityRelation.label : IdentityRelation → String
  | .badalTotal => "badal_total" | .badalPart => "badal_part"
  | .badalAssociation => "badal_association" | .tawkeed => "tawkeed"
def identityPreservationAllowed (relation : IdentityRelation) (relationLicensed identityLicensed : Bool) : Bool :=
  match relation with
  | .badalTotal | .tawkeed => relationLicensed && identityLicensed
  | _ => false
theorem identity_projection_requires_independent_identity (relation : IdentityRelation) (licensed identity : Bool)
    (h : identityPreservationAllowed relation licensed identity = true) :
    licensed = true ∧ identity = true := by
  cases relation <;> simp_all [identityPreservationAllowed]
theorem part_association_do_not_preserve_whole_identity (licensed identity : Bool) :
    identityPreservationAllowed .badalPart licensed identity = false ∧
    identityPreservationAllowed .badalAssociation licensed identity = false := ⟨rfl, rfl⟩

inductive Scope where
  | belief | certainty | transformation | proximity | hope | inception
  | wish | similitude | continuation | duration | timeTransition
  deriving DecidableEq, Repr
def scopes : List Scope := [.belief, .certainty, .transformation, .proximity, .hope, .inception,
  .wish, .similitude, .continuation, .duration, .timeTransition]
def Scope.label : Scope → String
  | .belief => "belief" | .certainty => "certainty" | .transformation => "transformation"
  | .proximity => "proximity" | .hope => "hope" | .inception => "inception"
  | .wish => "wish" | .similitude => "similitude" | .continuation => "continuation"
  | .duration => "duration" | .timeTransition => "time_transition"
def scopedProjectionAllowed (_scope : Scope) (metadataPreserved sourceSupported frameComplete : Bool) : Bool :=
  metadataPreserved && sourceSupported && frameComplete
def bareProjectionAllowed (_scope : Scope) : Bool := false
structure ScopeMetadata where
  family : Family
  sense : Scope
  tense : Option Morphology.Tense
  time : Option Nat
  place : Option Nat
  polarity : Bool
  restriction : Nat
  operatorBinding : Binding
  deriving DecidableEq, Repr
structure ScopedClaim (α : Type) where
  metadata : ScopeMetadata
  embedded : α
  deriving DecidableEq, Repr
/-- A proposed projection is checked for equality of the complete scoped
record. Its embedded value is never returned without the operator metadata. -/
def projectScoped {α : Type} [DecidableEq α] (sourceSupported frameComplete : Bool)
    (original proposed : ScopedClaim α) : Option (ScopedClaim α) :=
  if scopedProjectionAllowed original.metadata.sense (decide (original = proposed))
      sourceSupported frameComplete then some proposed else none
theorem scoped_projection_requires_complete_frame (scope : Scope) (m s f : Bool)
    (h : scopedProjectionAllowed scope m s f = true) : f = true := by
  simp_all [scopedProjectionAllowed]
theorem scoped_projection_exact {α : Type} [DecidableEq α] (s f : Bool)
    (original proposed result : ScopedClaim α)
    (h : projectScoped s f original proposed = some result) : result = original := by
  unfold projectScoped at h
  split at h
  next allowed =>
    simp only [scopedProjectionAllowed, Bool.and_eq_true, decide_eq_true_eq] at allowed
    simp only [Option.some.injEq] at h
    exact h.symm.trans allowed.1.1.symm
  next => simp at h
theorem scoped_projection_preserves_metadata {α : Type} [DecidableEq α] (s f : Bool)
    (original proposed result : ScopedClaim α)
    (h : projectScoped s f original proposed = some result) : result.metadata = original.metadata := by
  exact congrArg ScopedClaim.metadata (scoped_projection_exact s f original proposed result h)
theorem scoped_sense_never_projects_bare (scope : Scope) : bareProjectionAllowed scope = false := rfl

end Nabt.ConstructionEvidence
