"""Progressive agent views of the ONE learning framework and proof catalogue.

Curriculum prerequisites are not Lean proof dependencies. A resolved owner,
retrieved passage, checkpoint or teacher score cannot certify an occurrence.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from tools.evidence_lifecycle_v1 import _encoded, wire

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "nabt.progressive-agent-plan.v1"
PHASES = ("foundation", "reading", "word", "proposal", "composition", "postcomposition", "license", "revision")
CONTRACT_FIELDS = ("source_id", "source_sha256", "source_span", "law_id", "law_revision",
    "input_identity", "output_identity", "premise_receipts", "remaining_alternatives",
    "scope", "owner_receipt", "replay_inputs")


def digest(value):
    return sha256(wire(value).encode()).hexdigest()


def validate_plan(value, *, agents, objectives, research_ids=None):
    """Structure/reference validation only. Never accept completion booleans."""
    _encoded(value, 512 * 1024)
    if type(value) is not dict or set(value) != {"schema", "profiles", "topics", "contract_fields"} or value["schema"] != SCHEMA:
        raise ValueError("Unknown progressive agent plan")
    if value["contract_fields"] != list(CONTRACT_FIELDS):
        raise ValueError("Progressive handoff fields differ")
    rows, topics = value["profiles"], value["topics"]
    if type(rows) is not list or not 1 <= len(rows) <= 96 or type(topics) is not list or not 1 <= len(topics) <= 256:
        raise ValueError("Invalid profile/topic budget")
    indexed = {}
    def strings(xs):
        if type(xs) is not list or any(type(x) is not str or not x.strip() for x in xs) or len(set(xs)) != len(xs):
            raise ValueError("Expected unique string references")
        return xs
    fields = {"id", "label_ar", "parent_agent_id", "phase", "prerequisites", "objective_ids", "exit_obligation_ar"}
    for row in rows:
        if type(row) is not dict or set(row) != fields:
            raise ValueError("Invalid agent profile fields")
        for key in ("id", "label_ar", "exit_obligation_ar", "parent_agent_id", "phase"):
            if type(row[key]) is not str or not row[key].strip():
                raise ValueError("Empty profile identity/description")
        if row["id"] in indexed or row["parent_agent_id"] not in agents or row["phase"] not in PHASES:
            raise ValueError("Duplicate or unresolved agent profile")
        if not strings(row["objective_ids"]) or not set(row["objective_ids"]) <= set(objectives):
            raise ValueError("Unresolved objective in agent profile")
        strings(row["prerequisites"])
        indexed[row["id"]] = row
    ordered, pending = [], set(indexed)
    while pending:
        ready = [r["id"] for r in rows if r["id"] in pending and set(r["prerequisites"]) <= set(ordered)]
        if not ready:
            raise ValueError("Cyclic or unresolved progressive prerequisites")
        ordered.extend(ready)
        pending.difference_update(ready)
    for row in rows:
        if any(PHASES.index(indexed[p]["phase"]) > PHASES.index(row["phase"]) for p in row["prerequisites"]):
            raise ValueError("Later-phase dependency in progressive plan")
    topic_ids = set()
    for row in topics:
        if type(row) is not dict or set(row) != {"id", "label_ar", "profile_id", "research_ids", "obligation_ar"}:
            raise ValueError("Invalid topic fields")
        for k in ("id", "label_ar", "obligation_ar", "profile_id"):
            if type(row[k]) is not str or not row[k].strip():
                raise ValueError("Empty topic identity/description")
        if row["id"] in topic_ids or row["profile_id"] not in indexed:
            raise ValueError("Duplicate or unresolved topic")
        refs = strings(row["research_ids"])
        if research_ids is not None and not set(refs) <= set(research_ids):
            raise ValueError("Unresolved research reference")
        topic_ids.add(row["id"])
    return ordered


def build_report():
    from .curriculum import curriculum
    from tools.entropy_framework.reuse import current_catalog
    from tools.entropy_framework.reuse_run import describe_entries
    from tools.grammar_catalog.catalog import build_catalog, catalog_sha256
    from tools.arabic_training.sign_curriculum import SYLLABLE_TARGETS

    existing = curriculum()
    signs = existing["sign_matrix"]
    framework = existing["learning_framework"]
    plan = framework["neural_design"]["progressive_agents"]
    objectives = {r["id"]: r for r in framework["objectives"]}
    agents = {r["id"]: r for r in framework["agents"]}
    sources = {r["id"]: r for r in framework["sources"]}
    research = {r["local_id"]: r for r in existing["research_inventory"]["records"]}
    order = validate_plan(plan, agents=agents, objectives=objectives, research_ids=research)
    compiled, relative, _, inputs = current_catalog(ROOT)
    grammar = build_catalog()
    # Reuse existing routes; membership is navigation, not a proved call edge.
    import json
    registry = json.loads((ROOT / "tools/entropy_framework/registry.json").read_text())
    families = registry["reuse"]["families"]
    entries = describe_entries()
    profiles = []
    for row in plan["profiles"]:
        selected = [objectives[k] for k in row["objective_ids"]]
        modules = sorted({m for o in selected for m in o["owner_modules"]})
        declarations = [d for d in compiled["theorems"] if d["module"] in modules]
        routes = [f for f in families if set(f["formal_modules"]) & set(modules)]
        rules = [r for r in grammar["rules"] if any(
            name.rsplit(".", 1)[0] in modules for name in r["theorem_names"])]
        topics = [deepcopy(t) for t in plan["topics"] if t["profile_id"] == row["id"]]
        for topic in topics:
            topic["research_records"] = [{"id": research[k]["id"],
                "record_sha256": research[k]["record_sha256"]} for k in topic["research_ids"]]
            topic["coverage_status"] = "REQUEST_MAPPED_APPLICATION_UNMEASURED"
        profiles.append({**deepcopy(row), "topics": topics, "owner_modules": modules,
            "declaration_ids": [d["name"] for d in declarations],
            "runtime_paths": sorted({p for o in selected for p in o["runtime_refs"]}),
            "entrypoints": {key: entries[key] for f in routes for key in f["entrypoint_ids"]},
            "native_checks": [{"target": t, "available": (ROOT / "formal/.lake/build/bin" / t).is_file(),
                "executed_by_this_report": False} for t in sorted({t for f in routes for t in f["native_targets"]})],
            "related_source_rule_ids": [r["rule_key"] for r in rules],
            "curriculum_sources": [deepcopy(sources[k]) for k in sorted({s for o in selected for s in o["source_ids"]})],
            "source_mapping_scope": "RELATED_OWNER_MODULE_NOT_TOPIC_COMPLETENESS",
            "open_obligations": list(dict.fromkeys([o["acquisition_obligation_ar"] for o in selected] +
                                                   [d for f in routes for d in f["open_debts"]])),
            "assessment": {"train": "SOURCE_BOUND_EXAMPLES_WITH_INTERPRETED_PREMISES",
                "dev": "MINIMAL_CONTRASTS_AND_WITHDRAWAL",
                "test": "HELD_OUT_ROOT_CONTEXT_SOURCE_AND_TEMPLATE_WHERE_APPLICABLE",
                "scores_cannot_discharge_premises": True},
            "training_status": "SEE_AWAMIL_RETRIEVAL_RUN_NOT_APPLICATION_MASTERY" if row["id"] == "awamil.propose"
                               else "NOT_MEASURED_FOR_THIS_PROFILE",
            "application_license_granted": False})
    return {"schema": "nabt.progressive-agent-report.v1", "authority": "CURRICULUM_AND_PROOF_NAVIGATION_ONLY",
        "framework_sha256": framework["validation"]["source_sha256"],
        "plan_sha256": digest(plan), "profiles": profiles, "prerequisite_order": order,
        "counts": {"profiles": len(profiles), "requested_topics": len(plan["topics"]),
                   "compiled_declarations": len(compiled["theorems"])},
        "proof_catalog": {"path": relative, "sha256": inputs[relative], "compiled_this_run": False,
            "verification": "RECORDED_COMPILED_SNAPSHOT_WITH_CURRENT_SOURCE_MATCH"},
        "grammar_catalog_sha256": catalog_sha256(grammar),
        "syllable_targets": list(SYLLABLE_TARGETS),
        "foundation_facts": {"count_domains": deepcopy(signs["count_domains"]),
            "articulation_profile": "SOURCE_ATTRIBUTED_NOT_ACOUSTICALLY_ACQUIRED",
            "source_collation_open_carriers": sorted({c["carrier"] for c in signs["cells"]
                if c["articulation"]["source_collation"] != "ANCHORED"}),
            "acoustic_validation": signs["phonological_policy"]["acoustic_validation"],
            "sign_limitations": deepcopy(signs["limitations"]),
            "utf_transport_formal_refinement": "NOT_ESTABLISHED_BY_PYTHON_ROUNDTRIP"},
        "handoff_fields": list(CONTRACT_FIELDS),
        "dependencies_are": "AUTHORED_CURRICULUM_REQUIREMENTS_NOT_LEAN_PROOF_DEPENDENCIES",
        "agent_profiles_are": "SPECIALIZATIONS_OF_EXISTING_OWNERS_NOT_SEPARATELY_TRAINED_MODELS",
        "semantic_authority": "NONE", "automatic_ascension": False}


def plan_for(profile_id):
    report = build_report()
    indexed = {r["id"]: r for r in report["profiles"]}
    if type(profile_id) is not str or profile_id not in indexed:
        raise ValueError("Unknown progressive agent profile")
    needed = set()
    def visit(key):
        if key not in needed:
            needed.add(key)
            for p in indexed[key]["prerequisites"]:
                visit(p)
    visit(profile_id)
    report["goal"] = profile_id
    report["profiles"] = [indexed[k] for k in report["prerequisite_order"] if k in needed]
    report["selected_profile_count"] = len(report["profiles"])
    report["prerequisite_order"] = [k for k in report["prerequisite_order"] if k in needed]
    report["next_obligations"] = [{"profile_id": r["id"], "required": r["exit_obligation_ar"],
                                   "status": "REQUIRES_CURRENT_OCCURRENCE_EVIDENCE"} for r in report["profiles"]]
    return report


def proofs(profile_id):
    from tools.entropy_framework.reuse import current_catalog, _declaration_source
    report = plan_for(profile_id)
    profile = next(p for p in report["profiles"] if p["id"] == profile_id)
    compiled, _, _, _ = current_catalog(ROOT)
    selected = set(profile["declaration_ids"])
    return {"schema": "nabt.progressive-agent-proofs.v1", "profile_id": profile_id,
        "catalog": report["proof_catalog"], "authority": "CURRENT_COMPILED_REFERENCE_ONLY",
        "declarations": [{**deepcopy(row), "source_statement": _declaration_source(ROOT, row)}
                         for row in compiled["theorems"] if row["name"] in selected],
        "application_premises_required": profile["open_obligations"],
        "complete_topic_proof_claimed": False}


def search(query, *, limit=10):
    from tools.grammar_catalog.retrieval import SearchIndex, tokens
    report = build_report()
    class ProfileIndex(SearchIndex):
        def __init__(self):
            self._catalog = {"authority": "RETRIEVAL_ONLY", "items": report["profiles"]}
            self.catalog_sha256 = digest(report)
            self._docs = {}
            for profile in report["profiles"]:
                self._add("item", profile["id"], profile["label_ar"] + " " + " ".join(
                    t["label_ar"] for t in profile["topics"]) + " " + " ".join(profile["declaration_ids"]), profile)
                for topic in profile["topics"]:
                    self._add("item", "topic:" + topic["id"], topic["label_ar"] + " " + topic["obligation_ar"],
                        {**deepcopy(topic), "owner_modules": profile["owner_modules"],
                         "proof_view_profile_id": profile["id"],
                         "source_mapping_scope": profile["source_mapping_scope"],
                         "application_license_granted": False})
            self._tf = {key: Counter(tokens(doc["search_text"])) for key, doc in self._docs.items()}
    result = ProfileIndex().search(query, limit=limit)
    result["source_retrieval"] = SearchIndex().search(query, limit=limit)
    result["source_candidate_is_topic_certificate"] = False
    return result


def factor_gate(request):
    """Fresh existing-owner inquiry; no submitted progress flag can unlock it.

    Current inquiry provides source-relative analyses. It does not discharge
    RecursiveSourceBridge.CertifiedBridge; report that remaining contract intact.
    """
    from tools.grammar_catalog.awamil_cli import analyze
    from tools.grammar_catalog.operations import source_snapshot
    report = plan_for("awamil.license")
    actual = analyze(request)
    snapshot, _ = source_snapshot()
    return {"schema": "nabt.progressive-agent-factor-gate.v1", "source_result": actual,
        "framework_sha256": report["framework_sha256"], "owner_snapshot_sha256": digest(snapshot),
        "source_relative_status": actual["application"]["status"],
        "progressive_license_status": "DEFER", "application_license_granted": False,
        "missing_bridge": "Nabt.RecursiveSourceBridge.CertifiedBridge",
        "missing_obligations": ["sourceLicense", "hostInventory", "hostLicenses", "grammarLicense", "realizationAligned"],
        "proposal_and_training_allowed": True, "handoff_fields": list(CONTRACT_FIELDS)}


def verify_gate(receipt, *, expected_request):
    _encoded(receipt, 8 * 1048576, floats=True)
    return {"valid": wire(receipt) == wire(factor_gate(expected_request)),
            "verification": "FRESH_OWNER_AND_INPUT_REPLAY", "application_license_granted": False}


def summary(report):
    return {k: report[k] for k in ("schema", "authority", "counts", "proof_catalog",
        "foundation_facts", "syllable_targets", "prerequisite_order", "agent_profiles_are", "automatic_ascension")}
