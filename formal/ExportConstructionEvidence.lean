import Nabt.ConstructionEvidence
import Lean

open Lean Nabt.ConstructionEvidence
open Nabt.DiscourseEvidence (Compatibility compatibilities)
open Nabt.Morphology (Evidence evidenceStates)
open Nabt.Governors (Case)

def bit (mask position : Nat) : Bool := mask / 2 ^ position % 2 == 1
def inheritedCases : List (Option Case) := [none, some .nasb, some .raf, some .jarr]
def caseJson : Option Case → Json | none => Json.null | some c => toJson c.code
def activationFromMask (mask : Nat) : Activation :=
  ⟨bit mask 0, bit mask 1, bit mask 2, bit mask 3, bit mask 4, bit mask 5⟩

def constructionEvidenceJson : Json := Json.mkObj [
  ("schema_version", toJson (1 : Nat)),
  ("law_id", toJson lawId),
  ("scope", toJson "CONDITIONAL_LICENSED_CONSTITUENTS_AND_EXACT_SCOPED_PROJECTION_NOT_ACQUISITION_OR_WORLD_TRUTH"),
  ("source_policy_id", toJson "nabt.construction-grammar-sources.v2"),
  ("families", toJson (families.map Family.label)),
  ("roles", toJson (roles.map Role.label)),
  ("inherited_cases", toJson (inheritedCases.map caseJson)),
  ("operator_rows", toJson (families.map fun family => Json.mkObj [
    ("family", toJson family.label),
    ("slots", toJson (family.roles.map fun role => Json.mkObj [
      ("role", toJson role.label), ("case", caseJson (role.caseRequirement none))]))])),
  ("role_rows", toJson (roles.flatMap fun role => inheritedCases.map fun inherited => Json.mkObj [
    ("label", toJson role.label), ("inherited_case", caseJson inherited),
    ("case", caseJson (role.caseRequirement inherited)), ("inherits", toJson role.inherits),
    ("target", toJson (if role = .kadaPredicate then "clause_local_case" else "licensed_constituent"))])),
  ("case_scope", toJson "REQUIREMENTS_ONLY;KADA_PREDICATE_LOCAL_CASE_DOES_NOT_GOVERN_INTERNAL_VERB;UNKNOWN_WORD_CONSTRUCTION_HAS_NO_ACTUAL_ASSIGNMENT"),
  ("compatibilities", toJson (compatibilities.map Compatibility.label)),
  ("agreement_axes", toJson ["case", "definiteness", "gender", "number"]),
  ("agreement_scope", toJson "LICENSED_REAL_ADJECTIVE_DIRECT_AGREEMENT_REGIME;CAUSAL_AND_EXCEPTIONAL_REGIMES_REQUIRE_SEPARATE_LICENSE"),
  ("agreement_rows", toJson (compatibilities.flatMap fun c => compatibilities.flatMap fun d =>
    compatibilities.flatMap fun g => compatibilities.map fun n => Json.mkObj [
      ("case", toJson c.label), ("definiteness", toJson d.label), ("gender", toJson g.label),
      ("number", toJson n.label), ("status", toJson (agreementStatus c d g n).label)])),
  ("predicate_agreement_axes", toJson ["gender", "number"]),
  ("predicate_agreement_rows", toJson ([false, true].flatMap fun regime =>
    compatibilities.flatMap fun g => compatibilities.map fun n => Json.mkObj [
      ("regime_licensed", toJson regime), ("gender", toJson g.label),
      ("number", toJson n.label), ("status", toJson (predicateAgreementStatus regime g n).label)])),
  ("predicate_agreement_scope", toJson "SOURCE_DECLARED_SIMPLE_DIRECT_ADJECTIVAL_PREDICATION_ONLY;REGIME_NOT_FROM_ADJ_TAG_GENDER_DERIVATION_OR_SHAPE_ALONE;UNKNOWN_REGIME_POSSIBLE;NO_CASE_OR_DEFINITENESS_AGREEMENT;PRESERVE_PREDICATION_REFERENCE_AND_OPERATOR_SCOPE"),
  ("evidence_states", toJson (evidenceStates.map Evidence.label)),
  ("idafa_modes", toJson (idafaModes.map IdafaMode.label)),
  ("idafa_rows", toJson (idafaModes.flatMap fun mode => evidenceStates.flatMap fun t =>
    evidenceStates.flatMap fun n => evidenceStates.flatMap fun a => [false, true].map fun exception => Json.mkObj [
      ("mode", toJson mode.label), ("tanwin", toJson t.label), ("nun", toJson n.label),
      ("article", toJson a.label), ("article_exception", toJson exception),
      ("status", toJson (idafaHeadStatus mode t n a exception).label)])),
  ("idafa_scope", toJson "CANONICAL_SEMANTIC_OR_LICENSED_VERBAL_IDAFA;NUN_IS_INFLECTION_NUN;ABSENCE_REQUIRES_EVIDENCE;ARTICLE_EXCEPTION_ONLY_VERBAL"),
  ("an_rows", toJson (anHeads.map fun head => Json.mkObj [
    ("label", toJson head.label), ("policy", toJson head.policy.label),
    ("preferred_present", toJson head.preferredPresent),
    ("allows_absent", toJson (head.allows false)), ("allows_present", toJson (head.allows true))])),
  ("an_scope", toJson "SUPPLIED_OPERATOR_SENSE;INCEPTION_IS_A_FAMILY_NOT_EXHAUSTIVE_WORD_LIST;PREFERENCE_NEVER_FORBIDS_PERMISSIBLE_RARE_FORM"),
  ("activation_bits", toJson ["identity_bound", "source_supported", "attachment_licensed",
    "frame_complete", "sense_licensed", "unblocked"]),
  ("activation_rows", toJson (families.flatMap fun family => (List.range 64).map fun mask => Json.mkObj [
    ("family", toJson family.label), ("mask", toJson mask),
    ("allowed", toJson (constructionAllowed family (activationFromMask mask)))])),
  ("receipt_scope", toJson "ACTIVATION_ROWS_ARE_CONDITIONAL;GENERAL_RECEIPTS_ALSO_BIND_GRAPH_INDICES_SOURCE_REVISION_SCOPE_OCCURRENCE_SEGMENTATION_READING_RULE_AND_NONEMPTY_SUPPORT"),
  ("identity_relations", toJson (identityRelations.map IdentityRelation.label)),
  ("identity_bits", toJson ["relation_licensed", "identity_licensed"]),
  ("identity_rows", toJson (identityRelations.flatMap fun relation => (List.range 4).map fun mask => Json.mkObj [
    ("label", toJson relation.label), ("mask", toJson mask),
    ("allowed", toJson (identityPreservationAllowed relation (bit mask 0) (bit mask 1)))])),
  ("scopes", toJson (scopes.map Scope.label)),
  ("scope_bits", toJson ["metadata_preserved", "source_supported", "frame_complete"]),
  ("scope_metadata", toJson ["family", "sense", "tense", "time", "place", "polarity", "restriction", "operator_binding"]),
  ("scope_rows", toJson (scopes.flatMap fun scope => (List.range 8).map fun mask => Json.mkObj [
    ("scope", toJson scope.label), ("mask", toJson mask),
    ("allowed", toJson (scopedProjectionAllowed scope (bit mask 0) (bit mask 1) (bit mask 2))),
    ("bare_projection", toJson (bareProjectionAllowed scope))])),
  ("projection_scope", toJson "EXACT_OUTER_SCOPED_RECORD_ONLY;NO_BARE_EMBEDDED_ASSERTION_FOR_ANY_LISTED_SENSE;NO_CLAIM_THAT_ALL_LEXICAL_CERTAINTY_READINGS_ARE_NONFACTIVE")
]

def main : IO Unit := IO.println constructionEvidenceJson.compress
