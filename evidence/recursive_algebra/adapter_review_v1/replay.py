#!/usr/bin/env python3
"""Replay the authored source-transport audit; print observations as strict JSON.

This is a development audit of current supported sources, not a held-out
Arabic acquisition experiment. Run after building recursiveBridgeProbe.
It does not overwrite the frozen observations or example envelope.
"""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from nabt import recursive_bridge as bridge
from nabt.corpus_evidence import learn_qac_lexicon
from nabt.errors import NabtError


def run():
    training = (ROOT / "examples/discourse_training.tsv").read_bytes()
    context_bytes = (ROOT / "examples/discourse_context.json").read_bytes()
    model = learn_qac_lexicon(training)
    context = json.loads(context_bytes)
    options = {"lexical_model": model, "context": context}
    observations = []
    inna_example = None
    for text, kind in (("مَكْتُوبٌ", "morphology"), ("كَاتِبٌ", "morphology"),
                       ("انْتَبَر", "morphology"), ("إنَّ هذا عالم.", "frame"),
                       ("هل أنت عالم؟", "frame")):
        discourse = kind == "frame"
        report = bridge.read_recursive_source(text, with_discourse=discourse, **options)
        records = report["syntax_frames"] if discourse else report["morphology_nodes"]
        for index, record in enumerate(records):
            envelope = bridge.assess_recursive_source(text, index, kind=kind, **options)
            request, assessment = envelope["request"], envelope["assessment"]
            verification = bridge.verify_recursive_assessment(
                envelope, text=text, index=index, kind=kind, **options)
            item = {
                "text": text, "kind": kind, "proposal_index": index,
                "source_sha256": report["source"]["source_sha256"],
                "report_id": report["report_id"],
                "transport_complete_exact_replay": verification["valid"],
                "source_bound": assessment["source_bound"],
                "verdict": assessment["verdict"],
                "exact_typed_node_roundtrip": bridge.wire(request["node"]) == bridge.wire(assessment["node"]),
                "root": record.get("root"), "catalog_id": record.get("catalog_id"),
                "radical_fibers": record.get("radical_fibers"),
                "qualified_analysis": record.get("qualified_analysis"),
                "upstream_frame": record.get("upstream_analysis", {}).get("frame"),
                "projected_section": request["node"]["metadata"]["section"],
                "roles": [{key: role[key] for key in ("role", "case", "case_domain")}
                          for role in request["node"]["metadata"]["roles"]],
                "retained_evidence_count": len(request["node"]["metadata"]["evidence_ids"]),
                "full_evidence_namespace": envelope["evidence_namespace"],
                "grammar_certified": envelope["grammar_certified"],
                "acquisition_measured": envelope["acquisition_measured"],
            }
            assert item["transport_complete_exact_replay"]
            assert item["source_bound"] and item["exact_typed_node_roundtrip"]
            assert item["verdict"] == "SOURCE_ONLY"
            if discourse and not item["qualified_analysis"]:
                assert item["roles"] == [] and item["projected_section"] is None
            observations.append(item)
            if text == "إنَّ هذا عالم." and index == 0:
                inna_example = envelope

    assert inna_example is not None
    request, response = inna_example["request"], inna_example["assessment"]
    guard_results = []
    for alias in (True, 1.0):
        forged = deepcopy(response)
        forged["node"]["metadata"]["source"]["atomization_id"] = alias
        assert forged["node"] == request["node"]  # Python's weak numeric equality.
        output = subprocess.CompletedProcess([], 0, bridge.wire(forged) + b"\n", b"")
        rejected = False
        with patch.object(bridge.subprocess, "run", return_value=output):
            try:
                bridge.check_with_lean(request, probe=sys.executable)
            except NabtError as error:
                rejected = error.code == "RECURSIVE_PROBE_FAILED" and error.status == "DEFER"
        assert rejected
        guard_results.append({"mutation": "atomization_id_1_to_" + type(alias).__name__,
                              "rejected": rejected})

    changed = deepcopy(inna_example)
    changed["transport"]["evidence_records"][0]["support"]["rule"] = "another_rule"
    verified = bridge.verify_recursive_assessment(changed, text="إنَّ هذا عالم.",
                                                  kind="frame", **options)
    assert verified["valid"] is False
    guard_results.append({"mutation": "retained_upstream_support_rule", "rejected": True})

    result = {
        "schema": "nabt.recursive-adapter-development-review.v1",
        "scope": "AUTHORED_CURRENT_SOURCE_TRANSPORT_AUDIT_NOT_ACQUISITION",
        "input_count": 5, "projected_proposal_count": len(observations),
        "all_passed": True, "observations": observations,
        "adversarial_guard_results": guard_results,
        "source_files": {
            "examples/discourse_training.tsv": sha256(training).hexdigest(),
            "examples/discourse_context.json": sha256(context_bytes).hexdigest(),
            "src/nabt/recursive_bridge.py": sha256((ROOT / "src/nabt/recursive_bridge.py").read_bytes()).hexdigest(),
            "formal/Nabt/RecursiveSourceBridge.lean": sha256((ROOT / "formal/Nabt/RecursiveSourceBridge.lean").read_bytes()).hexdigest(),
            "formal/RecursiveBridgeProbe.lean": sha256((ROOT / "formal/RecursiveBridgeProbe.lean").read_bytes()).hexdigest(),
        },
    }
    assert len(observations) == 11
    return result, inna_example


if __name__ == "__main__":
    result, _ = run()
    sys.stdout.buffer.write(bridge.wire(result) + b"\n")
