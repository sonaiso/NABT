import Nabt.Morphology
import Nabt.TextEvidence

/-!
# Signs, conditional case requirements, and source-bound relation receipts

This native extension preserves `Words.ending`: that older table records a
surface ending, which need not itself be the grammatical sign. For example,
the remaining damma in a weak-waw jussive is not its sign of jussive case.

The sign convention is `common_letter_substitution`, following the common
letter account of the six nouns, dual and sound masculine plural. It is an
explicit convention, not a claim of unanimity among grammatical accounts.
Every DeclensionClass is already qualified by its grammatical side conditions;
in particular a six-noun class is not inferred from a final waw/alif/ya.

Relevant primary implementation sources are MIT-licensed Mashru at
e4c801ffe9171dadedcc3aae23051ea0953ae361, Jisr/JisrDal.lean (Bab,
hukmKhaliya, asliyya_tuqabil, yayn_la_yufarriq, amthila_nun),
Jisr/JisrDalUtur.lean, SLGE/Bridge.lean and SLGE/Tarkib.lean. Their classes
and frames are supplied premises. We do not transfer the weak-verb inference
from mere absence of a final weak carrier, or the assumption that every
imperfect is inflected. Nun identity and deletion need separate evidence.

The finite relation law is conditional on an independently licensed relation.
The receipt checker verifies the declared identities, rule, activation and
nonempty support; it does not prove the linguistic truth of caller assertions,
source authenticity, Python/Unicode parsing, lexical classification, or that
concatenating a segmentation makes that segmentation grammatically correct.
The runtime must acquire and replay those premises from its bounded sources.

An observed sign or nun type cannot create a relation. A construction whose
status is unknown cannot produce an actual case assignment. A built target
can receive a local case, never an inflection sign from its building vowel.
The diptote-genitive projection reuses Morphology's four evidence states;
unobserved al/idhafa is not evidence of their absence.
-/

namespace Nabt.InflectionEvidence

open Words (Kind DeclensionClass Ending)
open Governors (Case)
open Morphology (Construction Evidence GenitiveContext)
open TextEvidence (Binding SupportSpan)

def lawId : String := "nabt.inflection-evidence.v1"
def convention : String := "common_letter_substitution"

inductive Sign where
  | damma | fatha | kasra | sukun | waw | alif | ya
  | nunRetained | nunDeleted | weakDeleted
  deriving DecidableEq, Repr

def signs : List Sign := [.damma, .fatha, .kasra, .sukun, .waw, .alif, .ya,
  .nunRetained, .nunDeleted, .weakDeleted]

def Sign.code : Sign → Nat
  | .damma => 0 | .fatha => 1 | .kasra => 2 | .sukun => 3
  | .waw => 4 | .alif => 5 | .ya => 6 | .nunRetained => 7
  | .nunDeleted => 8 | .weakDeleted => 9

def Sign.label : Sign → String
  | .damma => "damma" | .fatha => "fatha" | .kasra => "kasra" | .sukun => "sukun"
  | .waw => "waw" | .alif => "alif" | .ya => "ya" | .nunRetained => "nun_retained"
  | .nunDeleted => "nun_deleted" | .weakDeleted => "weak_deleted"

inductive Mode where
  | overt | estimated | deletion
  deriving DecidableEq, Repr

def modes : List Mode := [.overt, .estimated, .deletion]
def Mode.code : Mode → Nat | .overt => 0 | .estimated => 1 | .deletion => 2
def Mode.label : Mode → String
  | .overt => "overt" | .estimated => "estimated" | .deletion => "deletion"

inductive Origin where
  | original | substitute
  deriving DecidableEq, Repr

def origins : List Origin := [.original, .substitute]
def Origin.code : Origin → Nat | .original => 0 | .substitute => 1
def Origin.label : Origin → String | .original => "original" | .substitute => "substitute"

def originalSign : Case → Sign
  | .raf => .damma | .nasb => .fatha | .jarr => .kasra | .jazm => .sukun

/-- Origin is relative to the supplied grammatical case, not a property of
the glyph by itself. -/
def signOrigin (sign : Sign) (grammaticalCase : Case) : Origin :=
  if sign = originalSign grammaticalCase then .original else .substitute

def signFor (cls : DeclensionClass) (grammaticalCase : Case) : Sign :=
  match cls, grammaticalCase with
  | .iSitta, .raf | .iJamM, .raf => .waw
  | .iSitta, .nasb | .iMuthanna, .raf => .alif
  | .iSitta, .jarr | .iMuthanna, .nasb | .iMuthanna, .jarr
  | .iJamM, .nasb | .iJamM, .jarr => .ya
  | .iJamF, .nasb => .kasra
  | .iMamnu, .jarr => .fatha
  | .fKhamsaA, .raf | .fKhamsaW, .raf | .fKhamsaY, .raf => .nunRetained
  | .fKhamsaA, .nasb | .fKhamsaA, .jazm | .fKhamsaW, .nasb | .fKhamsaW, .jazm
  | .fKhamsaY, .nasb | .fKhamsaY, .jazm => .nunDeleted
  | .fMutalAlif, .jazm | .fMutalW, .jazm | .fMutalY, .jazm => .weakDeleted
  | _, _ => originalSign grammaticalCase

def modeFor (cls : DeclensionClass) (grammaticalCase : Case) : Mode :=
  match signFor cls grammaticalCase with
  | .nunDeleted | .weakDeleted => .deletion
  | _ =>
    match cls, grammaticalCase with
    | .iMaqsur, _ | .iManqus, .raf | .iManqus, .jarr
    | .fMutalAlif, .raf | .fMutalAlif, .nasb
    | .fMutalW, .raf | .fMutalY, .raf => .estimated
    | _, _ => .overt

structure Realization where
  sign : Sign
  mode : Mode
  origin : Origin
  surface : Ending
  deriving DecidableEq, Repr

/-- The base iMamnu row is the conditional bare-diptote convention. Actual
genitive prediction must use `diptoteRealizations` with qualified context. -/
def realize (cls : DeclensionClass) (grammaticalCase : Case) : Option Realization :=
  (Words.ending cls grammaticalCase).map fun surface =>
    ⟨signFor cls grammaticalCase, modeFor cls grammaticalCase,
      signOrigin (signFor cls grammaticalCase) grammaticalCase, surface⟩

structure Row where
  cls : DeclensionClass
  grammaticalCase : Case
  realization : Realization
  deriving DecidableEq, Repr

def rows : List Row := Words.declensionClasses.flatMap fun cls =>
  Words.allCases.filterMap fun grammaticalCase =>
    (realize cls grammaticalCase).map fun r => ⟨cls, grammaticalCase, r⟩

theorem row_count : rows.length = 45 := by decide

theorem realization_surface_exact (cls : DeclensionClass) (c : Case) (r : Realization)
    (h : realize cls c = some r) : Words.ending cls c = some r.surface := by
  unfold realize at h
  cases he : Words.ending cls c with
  | none => simp [he] at h
  | some surface =>
    simp [he] at h
    subst r
    rfl

theorem realization_domain_exact (cls : DeclensionClass) (c : Case) :
    (realize cls c).isSome = (Words.ending cls c).isSome := by
  simp [realize]

theorem mem_rows_exact (row : Row) :
    row ∈ rows ↔ realize row.cls row.grammaticalCase = some row.realization := by
  rcases row with ⟨cls, c, r⟩
  have hcls : cls ∈ Words.declensionClasses := by cases cls <;> decide
  simp [rows, List.mem_flatMap, List.mem_filterMap, Option.map_eq_some_iff,
    Row.mk.injEq, Words.mem_allCases]
  constructor
  · rintro ⟨a, _, b, value, h, rfl, rfl, rfl⟩
    exact h
  · intro h
    exact ⟨cls, hcls, c, r, h, rfl, rfl, rfl⟩

theorem original_relative_to_case (sign : Sign) (c : Case) :
    signOrigin sign c = .original ↔ sign = originalSign c := by
  simp [signOrigin]

theorem kasra_has_two_origins :
    signOrigin .kasra .jarr = .original ∧ signOrigin .kasra .nasb = .substitute := by decide

theorem weak_deletion_is_not_remaining_vowel :
    realize .fMutalW .jazm = some ⟨.weakDeleted, .deletion, .substitute, .damma⟩ ∧
    realize .fMutalY .jazm = some ⟨.weakDeleted, .deletion, .substitute, .kasra⟩ := by decide

theorem maqsur_signs_are_estimated :
    realize .iMaqsur .raf = some ⟨.damma, .estimated, .original, .alif⟩ ∧
    realize .iMaqsur .nasb = some ⟨.fatha, .estimated, .original, .alif⟩ ∧
    realize .iMaqsur .jarr = some ⟨.kasra, .estimated, .original, .alif⟩ := by decide

theorem five_verbs_deletion_keeps_case_ambiguity :
    (realize .fKhamsaW .nasb) = (realize .fKhamsaW .jazm) ∧
    (realize .fKhamsaW .raf) ≠ (realize .fKhamsaW .jazm) := by decide

/-- Exact ending data stays separate from the source-bound contextual case. -/
def filterRows (candidates : List Row) (evidence : List (Row → Bool)) : List Row :=
  candidates.filter fun row => evidence.all fun allows => allows row

theorem filtered_rows_exact (candidates : List Row) (evidence : List (Row → Bool)) (row : Row) :
    row ∈ filterRows candidates evidence ↔
      row ∈ candidates ∧ ∀ allows ∈ evidence, allows row = true := by
  simp [filterRows, List.all_eq_true]

theorem deletion_widens_rows (candidates : List Row) (old extra : List (Row → Bool)) (row : Row)
    (h : row ∈ filterRows candidates (old ++ extra)) : row ∈ filterRows candidates old := by
  rw [filtered_rows_exact] at h ⊢
  exact ⟨h.1, fun allows member => h.2 allows (List.mem_append_left _ member)⟩

theorem duplicate_row_constraint (candidates : List Row) (allows : Row → Bool)
    (evidence : List (Row → Bool)) :
    filterRows candidates (allows :: allows :: evidence) =
      filterRows candidates (allows :: evidence) := by
  simp [filterRows]

def diptoteRealization (ending : Ending) : Realization :=
  if ending = .kasra then ⟨.kasra, .overt, .original, .kasra⟩
  else ⟨.fatha, .overt, .substitute, .fatha⟩

def diptoteRealizations (context : GenitiveContext) : List Realization :=
  (Morphology.genitiveCandidates context).map diptoteRealization

theorem diptote_candidates_exact (context : GenitiveContext) (r : Realization) :
    r ∈ diptoteRealizations context ↔
      ∃ ending ∈ Morphology.genitiveCandidates context, diptoteRealization ending = r := by
  simp [diptoteRealizations]

theorem diptote_unknown_does_not_assert_absence :
    diptoteRealizations ⟨.unknown, .unknown⟩ =
      [⟨.fatha, .overt, .substitute, .fatha⟩, ⟨.kasra, .overt, .original, .kasra⟩] := by decide

theorem diptote_conflict_blocks (context : GenitiveContext)
    (h : context.al = .conflict ∨ context.idhafa = .conflict) :
    diptoteRealizations context = [] := by
  rcases context with ⟨al, idhafa⟩
  cases al <;> cases idhafa <;> simp_all [diptoteRealizations, Morphology.genitiveCandidates,
    Evidence.values, Evidence.allows]

inductive NunKind where
  | radical | nominalDualPlural | fiveVerbRaf | feminineSubject
  | emphaticDirect | emphaticSeparated | protective
  deriving DecidableEq, Repr

def nunKinds : List NunKind := [.radical, .nominalDualPlural, .fiveVerbRaf,
  .feminineSubject, .emphaticDirect, .emphaticSeparated, .protective]

def NunKind.code : NunKind → Nat
  | .radical => 0 | .nominalDualPlural => 1 | .fiveVerbRaf => 2 | .feminineSubject => 3
  | .emphaticDirect => 4 | .emphaticSeparated => 5 | .protective => 6

def NunKind.label : NunKind → String
  | .radical => "radical" | .nominalDualPlural => "nominal_dual_plural"
  | .fiveVerbRaf => "five_verb_raf" | .feminineSubject => "feminine_subject"
  | .emphaticDirect => "emphatic_direct" | .emphaticSeparated => "emphatic_separated"
  | .protective => "protective"

inductive Relation where
  | prepositionObject | idafaComplement | activeSubject | passiveSubject | directObject
  | innaSubject | innaPredicate | kanaSubject | kanaPredicate
  | imperfectSubjunctive | imperfectJussive
  deriving DecidableEq, Repr

def relations : List Relation := [.prepositionObject, .idafaComplement, .activeSubject,
  .passiveSubject, .directObject, .innaSubject, .innaPredicate, .kanaSubject, .kanaPredicate,
  .imperfectSubjunctive, .imperfectJussive]

def Relation.code : Relation → Nat
  | .prepositionObject => 0 | .idafaComplement => 1 | .activeSubject => 2
  | .passiveSubject => 3 | .directObject => 4 | .innaSubject => 5 | .innaPredicate => 6
  | .kanaSubject => 7 | .kanaPredicate => 8 | .imperfectSubjunctive => 9 | .imperfectJussive => 10

def Relation.label : Relation → String
  | .prepositionObject => "preposition_object" | .idafaComplement => "idafa_complement"
  | .activeSubject => "active_subject" | .passiveSubject => "passive_subject"
  | .directObject => "direct_object" | .innaSubject => "inna_subject"
  | .innaPredicate => "inna_predicate" | .kanaSubject => "kana_subject"
  | .kanaPredicate => "kana_predicate" | .imperfectSubjunctive => "imperfect_subjunctive"
  | .imperfectJussive => "imperfect_jussive"

def Relation.kind : Relation → Kind
  | .imperfectSubjunctive | .imperfectJussive => .verb | _ => .noun

def Relation.requiredCase : Relation → Case
  | .prepositionObject | .idafaComplement => .jarr
  | .activeSubject | .passiveSubject | .innaPredicate | .kanaSubject => .raf
  | .directObject | .innaSubject | .kanaPredicate | .imperfectSubjunctive => .nasb
  | .imperfectJussive => .jazm

theorem same_case_does_not_identify_relation :
    Relation.activeSubject.requiredCase = Relation.passiveSubject.requiredCase ∧
    Relation.activeSubject ≠ Relation.passiveSubject := by decide

inductive CaseDomain where
  | inflectedCase | localCase
  deriving DecidableEq, Repr

def caseDomains : List CaseDomain := [.inflectedCase, .localCase]
def CaseDomain.code : CaseDomain → Nat | .inflectedCase => 0 | .localCase => 1
def CaseDomain.label : CaseDomain → String
  | .inflectedCase => "inflected_case" | .localCase => "local_case"

def constructionDomain : Construction → CaseDomain
  | .built => .localCase | .inflected => .inflectedCase

theorem built_cannot_be_inflected_case : constructionDomain .built ≠ .inflectedCase := by decide

structure Context where
  head : Binding
  target : Binding
  targetKind : Kind
  construction : Option Construction
  deriving DecidableEq, Repr

/-- Different segments of one written occurrence can be related, but their
actual spans must be disjoint. Segmentation IDs alone do not prove a split. -/
def Context.valid (context : Context) : Bool := decide (
  context.head.sourceId = context.target.sourceId ∧
  context.head.sourceRevision = context.target.sourceRevision ∧
  context.head.scopeId = context.target.scopeId ∧
  context.head.byteStart < context.head.byteEnd ∧
  context.target.byteStart < context.target.byteEnd ∧
  (context.head.byteEnd ≤ context.target.byteStart ∨ context.target.byteEnd ≤ context.head.byteStart))

structure Receipt where
  head : Binding
  target : Binding
  relation : Relation
  ruleId : Nat
  active : Bool
  blocked : Bool
  support : List SupportSpan
  deriving DecidableEq, Repr

def activation (identityMatch ruleMatch active blocked supportPresent supportValid
    kindMatch constructionKnown : Bool) : Bool :=
  identityMatch && ruleMatch && active && !blocked && supportPresent &&
    supportValid && kindMatch && constructionKnown

def Receipt.admissible (context : Context) (receipt : Receipt) : Bool :=
  activation
    (decide (receipt.head = context.head ∧ receipt.target = context.target) && context.valid)
    (receipt.ruleId == receipt.relation.code) receipt.active receipt.blocked
    (!receipt.support.isEmpty)
    (receipt.support.all fun span => span.validFor context.target)
    (receipt.relation.kind == context.targetKind) context.construction.isSome

theorem activation_exact (i r a b p s k c : Bool) :
    activation i r a b p s k c = true ↔
      i = true ∧ r = true ∧ a = true ∧ b = false ∧ p = true ∧ s = true ∧ k = true ∧ c = true := by
  simp [activation, Bool.and_eq_true, and_assoc]

theorem admitted_identities_exact (context : Context) (receipt : Receipt)
    (h : receipt.admissible context = true) :
    receipt.head = context.head ∧ receipt.target = context.target := by
  have h' := (activation_exact _ _ _ _ _ _ _ _).mp h
  have identities := h'.1
  simp only [Bool.and_eq_true, decide_eq_true_eq] at identities
  exact identities.1

theorem admitted_relation_context_valid (context : Context) (receipt : Receipt)
    (h : receipt.admissible context = true) : context.valid = true := by
  have h' := (activation_exact _ _ _ _ _ _ _ _).mp h
  have identities := h'.1
  simp only [Bool.and_eq_true, decide_eq_true_eq] at identities
  exact identities.2

theorem admitted_support_nonempty (context : Context) (receipt : Receipt)
    (h : receipt.admissible context = true) : receipt.support ≠ [] := by
  have h' := (activation_exact _ _ _ _ _ _ _ _).mp h
  intro empty
  simp [empty] at h'

theorem foreign_endpoint_rejected (context : Context) (receipt : Receipt)
    (h : receipt.head ≠ context.head ∨ receipt.target ≠ context.target) :
    receipt.admissible context = false := by
  apply Bool.eq_false_iff.mpr
  intro accepted
  have same := admitted_identities_exact context receipt accepted
  rcases h with head | target
  · exact head same.1
  · exact target same.2

theorem blocked_relation_rejected (context : Context) (receipt : Receipt)
    (blocked : receipt.blocked = true) : receipt.admissible context = false := by
  simp [Receipt.admissible, activation, blocked]

theorem unknown_construction_rejected (context : Context) (receipt : Receipt)
    (unknown : context.construction = none) : receipt.admissible context = false := by
  simp [Receipt.admissible, activation, unknown]

theorem wrong_kind_rejected (context : Context) (receipt : Receipt)
    (different : receipt.relation.kind ≠ context.targetKind) : receipt.admissible context = false := by
  simp [Receipt.admissible, activation, different]

inductive Input where
  | observedSign (sign : Sign)
  | observedNun (kind : NunKind)
  | relation (receipt : Receipt)
  deriving DecidableEq, Repr

def Input.accepted (context : Context) : Input → Option Receipt
  | .observedSign _ | .observedNun _ => none
  | .relation receipt => if receipt.admissible context then some receipt else none

def accepted (context : Context) (inputs : List Input) : List Receipt :=
  inputs.filterMap (Input.accepted context)

def caseCandidates (context : Context) (inputs : List Input) : List Case :=
  Words.allCases.filter fun c => (accepted context inputs).all fun r => r.relation.requiredCase == c

theorem case_candidates_exact (context : Context) (inputs : List Input) (c : Case) :
    c ∈ caseCandidates context inputs ↔
      ∀ receipt ∈ accepted context inputs, receipt.relation.requiredCase = c := by
  simp [caseCandidates, List.mem_filter, Words.mem_allCases, List.all_eq_true]

theorem observations_do_not_refine (context : Context) (sign : Sign) (nun : NunKind) (inputs : List Input) :
    caseCandidates context (.observedSign sign :: .observedNun nun :: inputs) =
      caseCandidates context inputs := by rfl

theorem no_relation_retains_cases (context : Context) :
    caseCandidates context [] = [.nasb, .raf, .jarr, .jazm] := rfl

theorem accepted_has_witness (context : Context) (inputs : List Input) (receipt : Receipt)
    (h : receipt ∈ accepted context inputs) :
    Input.relation receipt ∈ inputs ∧ receipt.admissible context = true := by
  obtain ⟨input, member, someReceipt⟩ := List.mem_filterMap.mp h
  cases input with
  | observedSign sign => simp [Input.accepted] at someReceipt
  | observedNun nun => simp [Input.accepted] at someReceipt
  | relation value =>
    simp only [Input.accepted] at someReceipt
    split at someReceipt <;> simp_all

theorem deleting_relations_widens_cases (context : Context) (old extra : List Input) (c : Case)
    (h : c ∈ caseCandidates context (old ++ extra)) : c ∈ caseCandidates context old := by
  rw [case_candidates_exact] at h ⊢
  intro receipt member
  apply h receipt
  simp only [accepted, List.filterMap_append, List.mem_append] at *
  exact Or.inl member

theorem duplicate_relation_idempotent (context : Context) (input : Input) (inputs : List Input) :
    caseCandidates context (input :: input :: inputs) = caseCandidates context (input :: inputs) := by
  cases h : input.accepted context <;> simp [caseCandidates, accepted, h]

def selectCase : List Case → Option Case
  | [c] => some c | _ => none

theorem select_case_exact (values : List Case) (c : Case) :
    selectCase values = some c ↔ values = [c] := by
  cases values with
  | nil => simp [selectCase]
  | cons first rest => cases rest <;> simp [selectCase]

structure ContextualCase where
  grammaticalCase : Case
  domain : CaseDomain
  deriving DecidableEq, Repr

def contextualCase (context : Context) (inputs : List Input) : Option ContextualCase := do
  let construction ← context.construction
  let c ← selectCase (caseCandidates context inputs)
  pure ⟨c, constructionDomain construction⟩

theorem unknown_construction_no_contextual_case (context : Context) (inputs : List Input)
    (h : context.construction = none) : contextualCase context inputs = none := by
  simp [contextualCase, h]

theorem empty_evidence_no_contextual_case (context : Context) : contextualCase context [] = none := by
  cases h : context.construction <;> simp [contextualCase, h, no_relation_retains_cases, selectCase]

theorem conflicting_relations_empty (context : Context) (inputs : List Input) (left right : Receipt)
    (hl : left ∈ accepted context inputs) (hr : right ∈ accepted context inputs)
    (different : left.relation.requiredCase ≠ right.relation.requiredCase) :
    caseCandidates context inputs = [] := by
  apply List.eq_nil_iff_forall_not_mem.mpr
  intro c member
  have h := (case_candidates_exact context inputs c).mp member
  exact different ((h left hl).trans (h right hr).symm)

theorem conflict_never_assigns (context : Context) (inputs : List Input)
    (h : caseCandidates context inputs = []) : contextualCase context inputs = none := by
  cases hc : context.construction <;> simp [contextualCase, hc, h, selectCase]

theorem selected_case_has_relation_receipt (context : Context) (inputs : List Input) (c : Case)
    (h : selectCase (caseCandidates context inputs) = some c) :
    ∃ receipt, Input.relation receipt ∈ inputs ∧ receipt.admissible context = true ∧
      receipt.relation.requiredCase = c := by
  have singleton := (select_case_exact _ c).mp h
  have nonempty : accepted context inputs ≠ [] := by
    intro empty
    simp [caseCandidates, empty, Words.allCases] at singleton
  obtain ⟨receipt, member⟩ := List.exists_mem_of_ne_nil _ nonempty
  have cMember : c ∈ caseCandidates context inputs := by simp [singleton]
  exact ⟨receipt, (accepted_has_witness context inputs receipt member).1,
    (accepted_has_witness context inputs receipt member).2,
    (case_candidates_exact context inputs c).mp cMember receipt member⟩

theorem built_target_only_local (context : Context) (inputs : List Input) (output : ContextualCase)
    (built : context.construction = some .built) (h : contextualCase context inputs = some output) :
    output.domain = .localCase := by
  simp only [contextualCase, built] at h
  cases hc : selectCase (caseCandidates context inputs) <;> simp [hc] at h
  subst output
  rfl

/-! Byte-preserving segmentation is a structural prerequisite. The additional
grammatical `License` below is deliberately not inferred from concatenation. -/

structure Segmentation (α : Type) where
  source : List α
  parts : List (List α)

def Segmentation.Exact (segmentation : Segmentation α) : Prop :=
  segmentation.parts.flatten = segmentation.source ∧ ∀ part ∈ segmentation.parts, part ≠ []

structure LicensedSegmentation (α : Type) (License : Segmentation α → Prop) where
  segmentation : Segmentation α
  exact : segmentation.Exact
  licensed : License segmentation

theorem exact_segmentation_preserves_members (segmentation : Segmentation α)
    (h : segmentation.Exact) (part : List α) (member : part ∈ segmentation.parts)
    (value : α) (present : value ∈ part) : value ∈ segmentation.source := by
  rw [← h.1]
  exact List.mem_flatten.mpr ⟨part, member, present⟩

theorem exact_segmentation_preserves_length (segmentation : Segmentation α)
    (h : segmentation.Exact) :
    segmentation.source.length = (segmentation.parts.map List.length).sum := by
  rw [← h.1, List.length_flatten]

theorem unlicensed_segmentation_not_constructible (segmentation : Segmentation α)
    (License : Segmentation α → Prop) (notLicensed : ¬ License segmentation) :
    ¬ ∃ value : LicensedSegmentation α License, value.segmentation = segmentation := by
  rintro ⟨value, same⟩
  exact notLicensed (same ▸ value.licensed)

end Nabt.InflectionEvidence
