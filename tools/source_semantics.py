#!/usr/bin/env python3
"""Replay the free reader and check its supplied alternatives in native Lean.

This adapter is NOT a proof of free-reader refinement, candidate enumeration,
classical interpretation, narration authenticity, or real-world truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import read_discourse, verify_discourse

CATALOG = ROOT / "evidence/source_semantics/passages.json"


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def executable():
    value = os.environ.get("NABT_CLASSICAL_SEMANTIC_PROBE")
    path = Path(value) if value else ROOT / "formal/.lake/build/bin/classicalSemanticProbe"
    if not path.is_file() or not os.access(path, os.X_OK):
        raise RuntimeError("native Lean classicalSemanticProbe is required")
    return path.resolve()


def native(requests, *, source=None, probe=None):
    args = [str(probe or executable())]
    if source:
        args += [str(ROOT / source["local_path"]), source["source_id"],
                 wire(source["edition"]), source["revision"], source["work"]]
    payload = "".join(wire(r) + "\n" for r in requests).encode()
    result = subprocess.run(args, input=payload, capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError(f"Lean adapter failed ({result.returncode}): {result.stdout[:500]!r}")
    rows = [json.loads(line) for line in result.stdout.splitlines()]
    if len(rows) != len(requests):
        raise RuntimeError("Lean response count differs from request count")
    for row in rows:
        if "error" in row:
            raise ValueError(f"{row['error']}: {row['message']}")
        if row.get("law_id") != "nabt.source-semantics.v1":
            raise RuntimeError("unexpected Lean law version")
    return rows


def attest_sources(*, probe=None):
    """File hashes pin digital editions; Lean independently checks quote slices."""
    catalog = json.loads(CATALOG.read_text())
    grouped = {}
    for passage in catalog["passages"]:
        grouped.setdefault(passage["source_id"], []).append(passage)
    rows = []
    for passages in grouped.values():
        source = passages[0]
        raw = (ROOT / source["local_path"]).read_bytes()
        if len(raw) != source["source_bytes"] or hashlib.sha256(raw).hexdigest() != source["source_sha256"]:
            raise ValueError("SOURCE_CHANGED: pinned edition differs")
        requests = [{"op": "source_rule", "law": p["law_id"], "offset": p["offset"],
                     "quote": p["quote"]} for p in passages]
        for p, result in zip(passages, native(requests, source=source, probe=probe), strict=True):
            if not result["attested"] or not result["interpretation_bound"]:
                raise ValueError(f"PASSAGE_CHANGED: {p['passage_id']}")
            rows.append({"passage_id": p["passage_id"], "selected_law_id": p["law_id"], **result})
    return rows


def audit_discourse(text, training: bytes, context, *, source_id="input", scope="default", report=None, probe=None):
    """Read original bytes afresh. A supplied report never defines the source.

    Whole semantic records (including time/place/restriction/sign/force) are
    compared. Every viable reading participates, including incomplete rivals.
    The Lean theorem applies to this supplied list; exhaustive Arabic parsing
    and the Python-to-JSON projection are explicitly outside its proof.
    """
    model = learn_qac_lexicon(training)
    fresh = read_discourse(text, lexical_model=model, context=context, source_id=source_id, scope=scope)
    if report is not None and report != fresh:
        raise ValueError("REPORT_CHANGED: differs from independently replayed source/context/lexicon")
    if not verify_discourse(fresh, lexical_model=model, context=context)["valid"]:
        raise ValueError("REPLAY_FAILED")
    binding = {"source": fresh["source_text"], "source_id": source_id, "scope": scope,
               "context": wire(context), "lexicon": training.decode("utf-8")}
    requests, clauses, references, unmeasured_references = [], [], [], []
    for clause in fresh["clauses"]:
        viable = [a for a in clause["analyses"] if not a["rejected_candidate"]]
        candidates = []
        for a in viable:
            complete = a["licensed_syntax"] and a["references_complete"]
            meaning = wire({"force": a["force"], "claims": sorted(a["claims"], key=wire),
                            "question_kind": a.get("question_kind")}) if complete else None
            candidates.append({"binding": binding, "meaning": meaning})
            for ref in a["references"]:
                # Apply the closed-singleton rule only to this supported
                # reference shape. Other reference mechanisms stay unmeasured.
                survivors = [c for c in ref.get("candidates", []) if c["allowed"]]
                compatible = (ref.get("origin") != "antecedent" or
                              all(c["compatibility"] == "confirmed" for c in survivors))
                if ref.get("closed_scope") is True and ref.get("candidate_entity_ids") and compatible:
                    references.append((ref, {"op": "reference", "closed": True,
                                            "candidates": ref["candidate_entity_ids"]}))
                else:
                    unmeasured_references.append({"reference_id": ref["reference_id"],
                        "status": "UNMEASURED", "reason": "outside this adapter's closed-reference contract"})
        requests.append({"op": "consensus", "expected": binding, "readings": candidates})
        clauses.append({"clause_id": clause["clause_id"], "status": clause["status"],
                        "viable_readings": len(viable),
                        "incomplete_readings": sum(c["meaning"] is None for c in candidates)})
    results = native(requests + [r for _, r in references], probe=probe)
    for clause, result in zip(clauses, results[:len(clauses)], strict=True):
        clause["lean"] = result
        clause["agrees_with_reader"] = result["contract_verified"] == (clause["status"] == "LICENSED")
    reference_results = []
    for (ref, _), result in zip(references, results[len(clauses):], strict=True):
        reference_results.append({"reference_id": ref["reference_id"], "lean": result,
                                  "agrees_with_reader": result["entity"] == ref["bound_entity_id"]})
    return {"schema": "nabt.free-reader-semantic-audit.v1", "source_id": source_id,
            "source_sha256": hashlib.sha256(fresh["source_text"].encode()).hexdigest(),
            "clauses": clauses, "references": reference_results,
            "unmeasured_references": unmeasured_references,
            "contract_checks_pass": all(c["agrees_with_reader"] for c in clauses + reference_results),
            "source_replay_pass": True, "reader_enumeration_proved": False,
            "all_arabic_complete": False, "world_truth_established": False,
            "classical_rule_interpretation_proved": False,
            "definition_parser_refinement_proved": False,
            "scope": "Lean consensus and closed-reference checks on the replayed free-reader candidate set"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--training", type=Path, required=True)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_discourse(args.source.read_bytes(), args.training.read_bytes(),
                            json.loads(args.context.read_text()))
    result["source_passages"] = attest_sources()
    result["selected_laws"] = native([{"op": "rules"}])[0]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0 if result["contract_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
