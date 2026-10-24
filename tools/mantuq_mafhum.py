#!/usr/bin/env python3
"""Source replay and Lean-checked consequences, with explicit scope boundaries.

The free path preserves every viable reading and its qualified claims. The
controlled path additionally validates the reading and complete execution in
Lean. Neither path supplies evidence that source assertions are true in the
world, or that a logical consequence is a particular usuli indication.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import source_semantics as bridge
from tools import verified_reading as controlled

CATALOG = ROOT / "evidence/mantuq_mafhum/sources.json"
INVENTORY = ROOT / "evidence/mantuq_mafhum/awamil_inventory.json"
LAW_ID = "nabt.mantuq-mafhum-consequence.v1"


def attest_sources(*, probe=None):
    """Verify retained excerpts; original unpublished books are not a CI input."""
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    checked = []
    for source in catalog["sources"]:
        raw = (ROOT / source["local_path"]).read_bytes()
        if len(raw) != source["source_bytes"] or hashlib.sha256(raw).hexdigest() != source["source_sha256"]:
            raise ValueError("SOURCE_CHANGED: retained method excerpt differs")
        requests = [{"op": "method_source", "law": source["law_id"],
                     "offset": span["offset"], "quote": span["quote"]} for span in source["spans"]]
        results = bridge.native(requests, source=source, probe=probe)
        for span, result in zip(source["spans"], results, strict=True):
            if not result["attested"] or not result["work_matches"]:
                raise ValueError("PASSAGE_CHANGED: method excerpt or work differs")
            checked.append({"source_id": source["source_id"], "paragraph": span["paragraph"],
                            "method_law_id": source["law_id"], "source_sha256": source["source_sha256"], **result})
    return {"method_passages": checked, "grammar_passages": bridge.attest_sources(probe=probe),
            "original_books_rechecked_in_ci": False, "interpretation_adequacy_proved": False}


def audit_inventory(*, probe=None):
    catalog = json.loads(INVENTORY.read_text(encoding="utf-8"))
    raw = (INVENTORY.parent / "sources/awamil_inventory.tsv").read_bytes()
    if hashlib.sha256(raw).hexdigest() != catalog["inventory_sha256"]:
        raise ValueError("INVENTORY_CHANGED")
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines(), delimiter="\t"))
    for row in rows:
        for key in ("id", "page", "group"):
            row[key] = int(row[key])
    native = bridge.native([{"op": "awamil_inventory"}], probe=probe)[0]
    if rows != catalog["rows"] or rows != native["entries"] or [r["id"] for r in rows] != list(range(1, 101)):
        raise ValueError("INVENTORY_DIFFERS: transcription, manifest and Lean must agree")
    return {"entries_checked": len(rows), "inventory_sha256": catalog["inventory_sha256"],
            "scan_sha256": catalog["source_scan_sha256"], "numbered_inventory_exact": True,
            "scan_retranscribed_in_ci": False, "full_rule_semantics_complete": False,
            "occurrence_license_established": False}


def claim_formula(analysis, claim):
    # Keep the WHOLE claim, including unknown future qualifiers. Never project
    # just predicate/arguments or turn a question/command into an assertion.
    record = {"force": analysis["force"], "question_kind": analysis.get("question_kind"),
              "assertion_allowed": analysis["assertion_allowed"], "claim": claim}
    return {"kind": "atom", "concept": "nabt.qualified-claim.v1",
            "args": [{"kind": "name", "value": bridge.wire(record)}]}


def _clause_consequences(clause, binding, *, probe=None):
    viable = [a for a in clause["analyses"] if not a["rejected_candidate"]]
    premises, candidates = [], {}
    for analysis in viable:
        complete = analysis["licensed_syntax"] and analysis["references_complete"]
        fs = [claim_formula(analysis, c) for c in analysis["claims"]] if complete else None
        premises.append(fs)
        for f in fs or []:
            candidates[bridge.wire(f)] = f
    requests, proposed = [], []
    for key, formula in sorted(candidates.items()):
        readings = []
        for fs in premises:
            # An absent claim gets an invalid index; incomplete readings retain
            # None. Both prevent this candidate from being accepted as common.
            index = fs.index(formula) if fs is not None and formula in fs else len(fs or [])
            readings.append({"binding": binding, "premises": fs,
                             "proof": {"kind": "premise", "index": index}})
        requests.append({"op": "meaning_common", "expected": binding, "readings": readings})
        proposed.append({"formula": formula, "certificates": readings})
    outcomes = bridge.native(requests, probe=probe) if requests else []
    accepted = []
    for proposal, result in zip(proposed, outcomes, strict=True):
        if result["meaning_law_id"] != LAW_ID:
            raise ValueError("LAW_CHANGED")
        if result["checked"]:
            if result["conclusion"] != proposal["formula"]:
                raise ValueError("CONCLUSION_CHANGED")
            accepted.append({**proposal, "lean": result})
    return {"clause_id": clause["clause_id"], "reader_status": clause["status"],
            "reading_ids": [a["analysis_id"] for a in viable],
            "viable_readings": len(viable), "incomplete_readings": sum(p is None for p in premises),
            "proposals_checked": len(requests), "common_consequences": accepted,
            "status": "CHECKED_COMMON_CONSEQUENCE" if accepted else "UNMEASURED",
            "reason": None if accepted else "No common consequence certified; not a linguistic rejection or negation."}


def audit_discourse(text, training: bytes, context, *, source_id="input", scope="default", report=None, probe=None):
    model = bridge.learn_qac_lexicon(training)
    fresh = bridge.read_discourse(text, lexical_model=model, context=context, source_id=source_id, scope=scope)
    if report is not None and report != fresh:
        raise ValueError("REPORT_CHANGED: source, context, lexical evidence or candidate set differs")
    if not bridge.verify_discourse(fresh, lexical_model=model, context=context)["valid"]:
        raise ValueError("REPLAY_FAILED")
    binding = {"source": fresh["source_text"], "source_id": source_id, "scope": scope,
               "context": bridge.wire(context), "lexicon": training.decode("utf-8")}
    return {"schema": "nabt.mantuq-mafhum-free-audit.v1", "law_id": LAW_ID, "binding": binding,
            "source_replay_pass": True, "policy_catalog": str(CATALOG.relative_to(ROOT)),
            "clauses": [_clause_consequences(c, binding, probe=probe) for c in fresh["clauses"]],
            "reader_enumeration_proved": False, "python_projection_proved": False,
            "all_arabic_complete": False, "world_truth_established": False,
            "usuli_subtypes_acquired": False, "acquisition_measured": False,
            "held_out_arabic_discovery_measured": False}


def _pair(proofs):
    if len(proofs) == 1:
        return proofs[0]
    return {"kind": "pair", "left": proofs[0], "right": _pair(proofs[1:])}


def _trace_proofs(certificate):
    """Untrusted proposal only; native Lean reopens source and checks the tree."""
    cs = certificate["clauses"]
    indices = {kind: [i for i, c in enumerate(cs) if c["kind"] == kind] for kind in ("fact", "rule")}
    proofs = {}
    for step in certificate["steps"]:
        index = indices[step["kind"]][step["index"]]
        clause = cs[index]
        premise = {"kind": "premise", "index": index}
        if step["kind"] == "fact":
            proofs[controlled.key(clause["atom"])] = premise
        else:
            body = [proofs[controlled.key(a)] for a in clause["body"]]
            proofs[controlled.key(clause["head"])] = {"kind": "apply", "rule": premise, "argument": _pair(body)}
    return proofs


def derive_controlled(source_path, query_path, *, identity="text", revision="1", scope="default", probe=None,
                      verified_probe=None):
    source_path, query_path = Path(source_path).resolve(), Path(query_path).resolve()
    raw, query = source_path.read_bytes(), query_path.read_bytes()
    certificate = controlled.propose(raw, query, identity, revision, scope)
    verifier = Path(verified_probe or os.environ.get("NABT_VERIFIED_READING", ROOT / "formal/.lake/build/bin/verifiedReading"))
    if not verifier.is_file():
        raise RuntimeError("native Lean verifiedReading is required")
    with tempfile.TemporaryDirectory() as temp:
        cert = Path(temp) / "certificate.json"
        cert.write_text(bridge.wire(certificate), encoding="utf-8")
        run = subprocess.run([str(verifier), str(source_path), str(query_path), str(cert), identity, revision, scope],
                             capture_output=True, text=True, timeout=60)
    result = json.loads(run.stdout)
    if run.returncode or not result.get("verified"):
        raise ValueError("EXECUTION_REJECTED: " + bridge.wire(result))
    # Compare native receipts with the independently read bytes before using
    # this proposal; changing files during validation cannot relabel a result.
    if result["source_text"].encode() != raw or result["query_text"].encode() != query:
        raise ValueError("SOURCE_CHANGED: native execution receipt differs")
    proofs = _trace_proofs(certificate)
    requests, signed = [], []
    for positive in (True, False):
        atom = {**certificate["query"], "positive": positive}
        proof = proofs.get(controlled.key(atom))
        if proof is not None:
            signed.append({"atom": atom, "proof": proof})
            requests.append({"op": "meaning_from_source", "scope": scope, "proof": proof})
    source = {"local_path": str(source_path), "source_id": identity, "edition": "controlled input",
              "revision": revision, "work": "target"}
    for item, checked in zip(signed, bridge.native(requests, source=source, probe=probe) if requests else [], strict=True):
        expected = {"kind": "atom", "concept": item["atom"]["predicate"], "args":
                    [{"kind": "name", "value": s} for s in
                     [scope, "positive" if item["atom"]["positive"] else "negative", *item["atom"]["arguments"]]]}
        if not checked["checked"] or checked["conclusion"] != expected or checked["source_text"].encode() != raw:
            raise ValueError("MEANING_PROOF_REJECTED_OR_SOURCE_CHANGED")
        item["lean"] = checked
    return {"schema": "nabt.mantuq-mafhum-controlled-audit.v1", "law_id": LAW_ID,
            "execution": result, "signed_consequences": signed,
            "policy_catalog": str(CATALOG.relative_to(ROOT)),
            "source_sha256": hashlib.sha256(raw).hexdigest(), "all_arabic_complete": False,
            "world_truth_established": False, "usuli_subtypes_acquired": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="operation", required=True)
    sub.add_parser("sources")
    free = sub.add_parser("free")
    free.add_argument("source", type=Path)
    free.add_argument("--qac", type=Path, required=True)
    free.add_argument("--context", type=Path, required=True)
    ground = sub.add_parser("controlled")
    ground.add_argument("source", type=Path)
    ground.add_argument("query", type=Path)
    for parser in (free, ground):
        parser.add_argument("--source-id", default="input")
        parser.add_argument("--scope", default="default")
    args = p.parse_args()
    if args.operation == "sources":
        result = {"sources": attest_sources(), "inventory": audit_inventory()}
    elif args.operation == "free":
        result = audit_discourse(args.source.read_bytes(), args.qac.read_bytes(),
                                 json.loads(args.context.read_text()), source_id=args.source_id, scope=args.scope)
    else:
        result = derive_controlled(args.source, args.query, identity=args.source_id, scope=args.scope)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
