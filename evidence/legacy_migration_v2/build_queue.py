"""Reproduce the legacy migration backlog without granting proof authority.

The immutable v1 inventory is the denominator. Families describe engineering
dependencies and review obligations, not completed acquisition or native laws.
The command-specific transport matrix is reviewed independently: migrating one
command must never upgrade the containing CLI/API wholesale.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path("evidence/legacy_migration_v2")
BASE_COMMIT = "8b948d8538373a9c69100c79253f58d7b5aa358f"
BASE_INVENTORY = Path("evidence/interface_migration_v1/interface_inventory.json")
BASE_SHA256 = "f98af54e803ac6db0ee369c1b253bc160a75426c1c812e5356aaba6f5ff2bd2e"
BASE_LAYERS_SHA256 = "e9e4b0eb7aa210d64eb153efd056bdd767bb806d834713f989d91ac1207afbab"
ACQUISITION = "ACQUISITION_AND_REFINEMENT_REVIEW_REQUIRED"
TRANSPORT = "CHILD_CONTRACT_REVIEW_REQUIRED"

# Explicit engineering ownership. A role here is a review responsibility,
# not an assertion that another agent has implemented the whole family.
FAMILIES = [
    ("machine_predictor", "آلة الانتقال والمقترح المتحقق", "core_runtime", [],
     ["transition_learning"], ["Acquisition", "Transition"], ["test_acquisition"],
     ["POINTWISE_SUCCESSOR_AND_COST_REFINEMENT", "IMMUTABLE_PREDICTOR_SNAPSHOT"],
     "Finite machine agreement; no Arabic source acquisition."),
    ("source_rows", "صفوف المصادر وحدودها", "source_acquisition", [],
     ["source_corpus"], ["LexicalSourceAcquisition"], ["test_corpus_sources", "test_lexical_source_acquisition"],
     ["COMPLETE_FORMAT_PARSER_REFINEMENT", "EXACT_ROW_FIELD_AND_UTF8_BOUNDARY_REPLAY", "ANNOTATION_INTERPRETATION_SEPARATE"],
     "Exact source occurrence and fields, without certifying the annotation meaning."),
    ("source_features", "سمات الشواهد والتعلم المحدود", "source_acquisition", ["source_rows"],
     ["source_learning", "evidence_learning"], ["PropertyEvidence", "RuleLearning"], ["test_source_learning", "test_source_witness_validation"],
     ["SOURCE_TO_FEATURE_EXTRACTION_REFINEMENT", "INDEPENDENT_FEATURE_LABEL_ORACLE", "WITHDRAWAL_RECOMPUTES_ALL_DEPENDENTS"],
     "Declared feature language and source premises; proposal is not observation."),
    ("word_boundary", "الكلمة والوصل والوقف", "source_acquisition", ["source_rows", "source_features"],
     ["word_reader", "phonological_boundary"], ["Words", "PhonologicalModes", "LexicalSurfaceBinding"], ["test_word_reader", "test_word_reader_review", "test_foundation_word_readings"],
     ["MARK_AND_SHADDA_PRESERVING_SEGMENTATION", "SOURCE_TO_WORD_READING_REFINEMENT", "WASL_WAQF_BRIDGE_PREMISES"],
     "A witnessed surface and its declared boundary mode, not a new intended sense."),
    ("classical_controls", "القوانين الكلاسيكية وإطار التحكم", "classical_laws", ["source_rows", "source_features"],
     ["conditional_law", "conditional_source_evidence", "conditional_reading_enumeration", "conditional_routing"],
     ["ClassicalWeak", "ClassicalHamza", "ClassicalGemination", "ClassicalBoundaryAffixes", "ClassicalLanguageEvidence", "ClassicalReferenceReadings", "RuleRouting", "BookCoverage"],
     ["test_classical_certified", "test_classical_laws_independent", "test_classical_reference_readings"],
     ["SOURCE_RULE_AND_EXCEPTION_INVENTORY", "SOURCE_TO_CONTROL_FLAG_REFINEMENT", "RESULT_RENDERING_REFINEMENT", "COMPLETE_FALLBACK_WITHIN_INSTALLED_RULE_SET"],
     "Conditional finite control equations; book coverage requires its separate premises."),
    ("morphology_derivation", "الصرف والاشتقاق وتصريف الفعل", "morphology", ["word_boundary", "classical_controls"],
     ["morphology", "text_morphology", "derivation", "verb_paradigm"], ["Morphology", "TextEvidence", "Derivation", "ImperativeParadigm", "ProductiveForms"],
     ["test_morphology_domain_review", "test_text_morphology_review", "test_derivation_review", "test_imperative_paradigm"],
     ["ROOT_PATTERN_AND_SOURCE_DOMAIN_SEPARATION", "FEATURE_EXTRACTION_AND_GENERATION_REFINEMENT", "LEXICAL_ATTESTATION_NOT_INFERRED_FROM_PATTERN"],
     "Licensed candidates under declared source features, preserving ambiguity."),
    ("nominal_count", "الاسم والعدد والمعدود", "nominal_morphology", ["word_boundary", "morphology_derivation"],
     ["nominal", "counting"], ["NominalEvidence", "NominalPatterns", "Count"], ["test_nominal_review", "test_counting_review_fixes", "test_source_bound_nominal_bridges"],
     ["COUNT_UNIT_DOMAIN_NOT_CELL_NUMBER", "ALL_NOMINAL_SIDE_CONDITIONS_ACQUIRED", "COUNTED_NOUN_FEATURE_AND_AGREEMENT_REFINEMENT"],
     "Declared source units and nominal features; numerical equality is not linguistic identity."),
    ("inflection_governor", "الإعراب والعامل", "syntax", ["word_boundary", "morphology_derivation", "nominal_count"],
     ["inflection", "governor_reader", "governor_checker"], ["InflectionEvidence", "Governors", "Words"],
     ["test_inflection_review", "test_governor_independent_review", "test_governor_boundary_review"],
     ["EXACT_ROLE_AND_GOVERNOR_ACQUISITION", "CASE_ENDING_IS_NOT_ROLE_OR_REFERENCE", "ENUMERATE_ALL_INSTALLED_READINGS"],
     "Case/role constraints of the declared grammar; no reference or world truth promotion."),
    ("controlled_readers", "القارئ النصي والنحو المحدود", "syntax", ["word_boundary", "inflection_governor"],
     ["source_reader", "arabic_reader"], ["ArabicReading", "ArabicCoverage", "VerifiedReading", "SourceSemantics"],
     ["test_text_reader", "test_arabic_query_context", "test_source_semantics"],
     ["GRAMMAR_RELATION_EXPLICIT_AND_VERSIONED", "PARSER_SOUNDNESS_AND_COMPLETENESS_FOR_DECLARED_GRAMMAR", "PRESERVE_QUOTATION_NEGATION_CONDITION_SCOPE"],
     "Exact declared fragment, not every grammatical Arabic string."),
    ("lexical_reports", "النقول المعجمية والتأليف والرسم", "lexical_transmission", ["source_rows"],
     ["native_lexical_testimony", "native_lexical_completion", "native_lexical_graph", "lexical_transmission"],
     ["LexicalDenotation", "LexicalCompletion", "LexicalGraph", "LexicalTransmission"],
     ["test_lexical_testimony", "test_lexical_completion", "test_lexical_graph", "test_lexical_transmission"],
     ["FIXED_INSTALLED_CHECKER_NO_CALLER_OVERRIDE", "BIND_EVERY_SENSE_TO_EXACT_SOURCE_OCCURRENCE", "SOURCE_DEPENDENCY_NOT_DUPLICATE_VOTES", "NO_CYCLE_CREATES_A_PREMISE"],
     "Source-relative inventory/conditional closure; transmission independence and tawatur remain separate."),
    ("occurrence_reference", "الوقوع والمقام والإحالة", "contextual_reference", ["source_rows", "word_boundary", "lexical_reports"],
     ["native_occurrence_sense", "native_contextual_reference"], ["OccurrenceSense", "ContextualReference", "PersonEvidence"],
     ["test_occurrence_sense_adversarial", "test_contextual_reference_adversarial", "test_contextual_semantics_reference"],
     ["CONTEXT_SOURCE_AND_SPEAKER_BINDING", "COMPLETE_CANDIDATE_SET_AND_ELIMINATION_EVIDENCE", "MISSING_FEATURES_PREVENT_SELECTION"],
     "Selection relative to explicit context and candidates, without assuming context truth."),
    ("discourse_scope", "تركيب الخطاب والنطاق", "scope_acquisition", ["controlled_readers", "occurrence_reference"],
     ["discourse_reader", "discourse_checker"], ["ScopeAcquisition", "DiscourseEvidence", "ConstructionEvidence"],
     ["test_discourse_reader", "test_discourse_prefix_scope", "test_discourse_negative_polar_boundary", "test_scope_acquisition"],
     ["PARSE_SPEECH_FORCE_AND_BODY_SPANS_FROM_RAW_SOURCE", "NESTING_AND_BRANCH_SCOPE_REFINEMENT", "BODY_PARSE_IS_NOT_EXTERNAL_ASSERTION"],
     "A checked scope envelope and separately checked body, with no inherited blanket authority."),
    ("semantic_kernel", "الاستدلال والانسحاب من المصدر", "semantic_inference", ["controlled_readers"],
     ["semantic_kernel"], ["SemanticInference", "SourceSemantics"], ["test_semantics", "test_source_semantics", "test_text_evaluation_safety"],
     ["VARIABLE_GROUNDING_REFINEMENT", "SOURCE_ADMISSION_AND_REVISION_REFINEMENT", "CONFLICT_CLEAN_CLOSURE_AND_REPLAY", "WORLD_MODEL_REMAINS_EXPLICIT_PREMISE"],
     "Conditional entailment of admitted finite clauses, not acquisition or external truth."),
    ("program_lifecycle", "البرنامج وتسلسل التنفيذ", "core_runtime", ["machine_predictor", "source_features", "controlled_readers", "semantic_kernel"],
     ["program"], ["Program"], ["test_program", "test_text_program"],
     ["COMPILER_AND_INTERPRETER_REFINEMENT", "OPCODE_SPECIFIC_CHILD_CONTRACTS", "EXACT_REEXECUTION_AND_SOURCE_WITHDRAWAL"],
     "Typed instruction/domain composition; a reversible program number is not a theorem."),
    ("ground_inference", "المنطوق والاستدلال المرخص", "semantic_inference", ["controlled_readers", "semantic_kernel", "classical_controls", "lexical_reports"],
     ["native_ground_reading", "native_inference", "native_qualified_inference", "native_linguistic_truth"],
     ["VerifiedReading", "LicensedInference", "QualifiedInference", "MantuqMafhum", "LinguisticTruth", "CertifiedLexical"],
     ["test_licensed_inference_security", "test_licensed_inference_runtime", "test_completion_semantic_integration"],
     ["FIXED_INSTALLED_NATIVE_AND_EXACT_INPUT_REOPEN", "CALLER_PREMISES_LABELLED_AND_NOT_ACQUIRED_BY_FLAG", "COMPLETE_ROW_AND_CLAIM_RESPONSE_REFINEMENT"],
     "Checked source-relative or explicitly conditional claims only."),
    ("recursive_bridge", "الجسر التركيبي التكراري", "morphology", ["morphology_derivation", "inflection_governor"],
     ["native_recursive_bridge"], ["RecursiveSourceBridge", "RecursiveLicensedAlgebra"],
     ["test_recursive_source_bridge", "test_recursive_bridge_checker", "test_recursive_bridge_probe"],
     ["SOURCE_SPINE_PRESERVES_EVERY_BOUNDARY", "NO_MODEL_ID_TO_ATOM_CAST", "FIXED_NATIVE_REFINEMENT_FOR_EACH_NODE_KIND"],
     "Licensed recursive constructors under supplied source-bound relations."),
    ("epistemic_inquiry", "قياس الدليل والدافع والواقع", "epistemic_measurement", ["semantic_kernel", "occurrence_reference"],
     ["inquiry", "native_epistemic"], ["RationalInquiry", "EpistemicMeasurement"],
     ["test_rational_inquiry_report_budget", "test_epistemic_measurement_adversarial", "test_epistemic_measurement_reference"],
     ["EVIDENCE_ROLE_AND_SOURCE_SCOPE_ACQUISITION", "MOTIVE_NEEDS_INDEPENDENT_EVIDENCE", "REALITY_EVIDENCE_NOT_INFERRED_FROM_SYNTAX", "UNMEASURED_DISTINCT_FROM_FALSE"],
     "Evidence adequacy under a declared measurement protocol, not direct access to hidden motive or reality."),
    ("certificate_rankers", "ترتيب مقترحات الشهادات", "proposal_training", ["ground_inference"],
     ["neural_certificate_ranker"], ["VerifiedReading"], ["test_certificate_ranker_v2"],
     ["RANKING_NEVER_GRANTS_A_CLAIM", "NATIVE_CHECKER_FIXED_AFTER_FOUNDATION_GUARD", "OUTAGE_IS_NOT_NEGATIVE_TRAINING_LABEL", "PROPOSAL_AND_CHECKED_CERTIFICATE_SEPARATED"],
     "Proposals and separately replayed certificates; a training metric is not Arabic coverage."),
]

COMMON_OBLIGATIONS = [
    "EXACT_RAW_BYTES_BOUNDARIES_CONTEXT_AND_IDENTIFIER_DOMAIN",
    "DECLARED_LAW_PREMISES_AND_UNRESOLVED_RESIDUALS",
    "NO_CALLER_SUPPLIED_PROOF_AUTHORITY",
    "INPUT_RESOURCE_OUTAGE_AND_LINGUISTIC_VERDICT_DISTINCT",
    "INDEPENDENT_POSITIVE_NEGATIVE_AND_TAMPER_ORACLES",
    "PROOF_LABEL_ONLY_FOR_EXACT_CHECKED_CLAIM",
]

LIFECYCLE = [
    {"stage": "inventory", "criterion": "Exact baseline surface assigned once to a reviewed family."},
    {"stage": "source_acquisition", "criterion": "Named raw-to-premise relation, scope, independent source inventory and residuals."},
    {"stage": "native_law", "criterion": "Versioned claim relation with checked theorem and declared assumptions."},
    {"stage": "implementation_refinement", "criterion": "Installed execution agrees with the complete request-bound native postcondition."},
    {"stage": "independent_replay", "criterion": "Separate positive, negative, tamper, missing-native and resource controls."},
    {"stage": "transport", "criterion": "Each command forwards exact child claims and preserves failure receipts."},
    {"stage": "release", "criterion": "New runtime/runner identity, full release gates and actual head-bound deployment."},
]


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _wire(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _topological(families):
    by_id = {family["id"]: family for family in families}
    if len(by_id) != len(families):
        raise ValueError("DUPLICATE_FAMILY")
    pending = set(by_id)
    ordered = []
    while pending:
        ready = sorted(name for name in pending if set(by_id[name]["depends_on"]) <= set(ordered))
        if not ready:
            raise ValueError("UNKNOWN_OR_CYCLIC_ENGINEERING_DEPENDENCY")
        ordered.extend(ready)
        pending.difference_update(ready)
    return ordered


def build(root=ROOT):
    raw = (root / BASE_INVENTORY).read_bytes()
    if _sha(raw) != BASE_SHA256:
        raise ValueError("HISTORICAL_INVENTORY_CHANGED")
    baseline = json.loads(raw)
    rows = baseline["surfaces"]
    if len({row["surface_id"] for row in rows}) != len(rows):
        raise ValueError("DUPLICATE_BASELINE_SURFACE")
    # Read the unchanged historical registry, not a growing live registry.
    # Inventory omits layer, so use a fixed reviewed path/layer map below.
    layer_raw = (root / FOLDER / "baseline_layers.json").read_bytes()
    if _sha(layer_raw) != BASE_LAYERS_SHA256:
        raise ValueError("HISTORICAL_LAYER_ASSIGNMENT_CHANGED")
    path_layers = json.loads(layer_raw)
    if path_layers["baseline_inventory_sha256"] != BASE_SHA256:
        raise ValueError("BASELINE_LAYER_IDENTITY_MISMATCH")
    layer_map = path_layers["surface_layers"]
    selected = [row for row in rows if row["migration_state"] == ACQUISITION]
    transport = [row for row in rows if row["migration_state"] == TRANSPORT]
    if len(selected) != 104 or len(transport) != 7 or set(layer_map) != {row["surface_id"] for row in selected}:
        raise ValueError("BASELINE_DENOMINATOR_MISMATCH")
    families, covered = [], set()
    for name, title, owner, depends, layers, laws, tests, obligations, scope in FAMILIES:
        members = [row for row in selected if layer_map[row["surface_id"]] in layers]
        if not members:
            raise ValueError("EMPTY_FAMILY:" + name)
        ids = {row["surface_id"] for row in members}
        if covered & ids:
            raise ValueError("OVERLAPPING_FAMILY:" + name)
        covered |= ids
        refs = ["formal/Nabt/" + law + ".lean" for law in laws]
        modules = ["tests." + test for test in tests]
        for path in refs + [module.replace(".", "/") + ".py" for module in modules]:
            if not (root / path).is_file():
                raise ValueError("MISSING_REVIEW_REFERENCE:" + path)
        families.append({"id": name, "title_ar": title, "owner_role": owner,
            "depends_on": depends, "dependency_kind": "ENGINEERING_REVIEW_PREREQUISITE_NOT_LOGICAL_ENTAILMENT",
            "baseline_surface_count": len(members), "baseline_layers": layers,
            "law_review_references": refs, "law_binding_status": "EXISTING_MODULES_TO_REVIEW_NOT_ACQUISITION_PROOF",
            "family_obligations": obligations, "authority_ceiling": scope,
            "replay_command": {"cwd": ".", "env": {"PYTHONPATH": "src:."},
                "argv": ["python", "-m", "unittest", *modules, "-v"],
                "execution_status": "NOT_EXECUTED_BY_PLAN_BUILDER",
                "prerequisite": "Build pinned Lean executables and acquire pinned source files where the referenced tests require them."}})
    if covered != {row["surface_id"] for row in selected}:
        raise ValueError("UNASSIGNED_BASELINE_SURFACE")
    order = _topological(families)
    by_layer = {layer: family for family in families for layer in family["baseline_layers"]}
    queue = []
    for row in selected:
        family = by_layer[layer_map[row["surface_id"]]]
        queue.append({"surface_id": row["surface_id"], "path": row["path"],
            "entrypoint": row["entrypoint"], "identifier_domain": row["identifier_domain"],
            "baseline_state": row["migration_state"], "family_id": family["id"],
            "owner_role": family["owner_role"], "law_review_references": family["law_review_references"],
            "obligations": COMMON_OBLIGATIONS + family["family_obligations"],
            "replay_command_family": family["id"],
            "lifecycle": {stage["stage"]: "INVENTORIED" if stage["stage"] == "inventory" else "NOT_ASSESSED_BY_QUEUE" for stage in LIFECYCLE},
            "accepted_claims": [], "whole_arabic_complete": False})
    queue.sort(key=lambda row: (order.index(row["family_id"]), row["surface_id"]))
    transports = [{"surface_id": row["surface_id"], "path": row["path"],
        "entrypoint": row["entrypoint"], "baseline_state": row["migration_state"],
        "owner_role": "interface_migration", "required_unit": "COMMAND_OR_OPERATION_NOT_WHOLE_SURFACE",
        "command_matrix": "src/nabt/data/transport_command_contracts.json",
        "lifecycle_policy": "Resolve each fixed child, bind raw request and complete response, forward only that child's checked named claims, retain native failure/resource/deferral states.",
        "migration_status": "SEE_COMMAND_SPECIFIC_RUNTIME_MATRIX_NOT_INFERRED_HERE",
        "accepted_claims": []} for row in transport]
    return {"schema": "nabt.legacy-migration-review-queue.v2", "kind": "ENGINEERING_PLAN_NOT_PROOF_RECEIPT",
        "baseline": {"commit": BASE_COMMIT, "inventory": str(BASE_INVENTORY), "inventory_sha256": BASE_SHA256,
            "previous_runner_identity": "evidence/interface_migration_v1/independent_oracle/runner_freeze_v5.json",
            "previous_runner_sha256": "0f7ae3bf2cab565b2976aa9b0cca39dc87a452f965dba7987ab95525ce890613"},
        "denominators": {"baseline_surfaces": len(rows), "acquisition_review": len(queue), "transport_surfaces": len(transports),
            "engineering_families": len(families), "proved_acquisition_count": None, "migrated_command_count": None},
        "counts_scope": "Interface counts and family partition only; not linguistic coverage or completed migration.",
        "lifecycle_stages": LIFECYCLE, "dependency_order": order, "families": families,
        "acquisition_queue": queue, "transport_queue": transports,
        "historical_policy": "Keep v5, all raw archives, reference cases and thresholds immutable. New implementation gets new runtime/runner identities only after production inputs stabilize.",
        "all_interfaces_migrated": False, "whole_arabic_complete": False,
        "tawatur_established": False, "source_acquisition_proved_by_this_plan": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build()
    target = ROOT / FOLDER / "migration_queue.json"
    expected = _wire(result)
    if args.check:
        if not target.is_file() or target.read_bytes() != expected:
            raise SystemExit("MIGRATION_QUEUE_DIFFERS_FROM_REVIEWED_BASELINE_AND_PLAN")
    else:
        target.write_bytes(expected)
    print(json.dumps({"schema": result["schema"], "check_only": args.check,
        "denominators": result["denominators"], "sha256": _sha(expected),
        "proof_authority": False}, sort_keys=True))


if __name__ == "__main__":
    main()
