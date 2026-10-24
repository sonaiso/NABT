#!/usr/bin/env python3
"""Independent, frozen, black-box adversarial Arabic API checks.

No production evaluator or private parser helper is imported. Expectations are
never production inputs. Output is append-only by exclusive creation.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import importlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]
MATERIAL = ROOT / "evidence/arabic_coverage/holdout_v1"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def verify_freeze():
    path = MATERIAL / "freeze.json"
    freeze = json.loads(path.read_text(encoding="utf-8"))
    if not freeze.get("predictions_executed_before_freeze") is False:
        raise ValueError("Missing explicit pre-execution independence declaration")
    for entry in freeze["files"]:
        target = ROOT / entry["path"]
        if digest(target) != entry["sha256"] or target.stat().st_size != entry["bytes"]:
            raise ValueError("Frozen material changed: " + entry["path"])
    own = str(Path(__file__).resolve().relative_to(ROOT))
    if own not in {entry["path"] for entry in freeze["files"]}:
        raise ValueError("The independent harness is not frozen")
    return freeze, digest(path)


def runtime_inventory():
    entries = []
    for path in sorted((ROOT / "src/nabt").rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            entries.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": digest(path)})
    return {"entries": entries, "sha256": sha256(dump(entries).encode()).hexdigest()}


def matches(claim, pattern):
    return isinstance(claim, dict) and all(key in claim and claim[key] == wanted for key, wanted in pattern.items())


def run(output):
    freeze, freeze_sha = verify_freeze()
    material = json.loads((MATERIAL / "cases.json").read_text(encoding="utf-8"))
    contexts = json.loads((MATERIAL / "contexts.json").read_text(encoding="utf-8"))
    before = runtime_inventory()
    output.parent.mkdir(parents=True, exist_ok=True)
    raw_path = output.with_suffix(".raw.jsonl")
    # Both names must be unused. Never overwrite the first failed experiment.
    if output.exists() or raw_path.exists():
        raise FileExistsError("Choose new report and raw-log paths")
    raw_handle = raw_path.open("x", encoding="utf-8")
    results, documents, answers, errors, raw_hashes = [], {}, {}, [], []
    totals = defaultdict(Counter)
    question_metrics = defaultdict(Counter)

    def raw(call, cid, value, **metadata):
        record = {"call": call, "case_id": cid, **metadata, "value": value}
        line = dump(record)
        raw_hashes.append(sha256(line.encode("utf-8")).hexdigest())
        raw_handle.write(line + "\n")
        raw_handle.flush()

    def check(checks, name, ok, observed=None, expected=None, unsafe=False):
        row = {"name": name, "pass": bool(ok)}
        if observed is not None:
            row["observed"] = observed
        if expected is not None:
            row["expected"] = expected
        if not ok and unsafe:
            row["unsafe_acceptance"] = True
        checks.append(row)

    try:
        sys.path.insert(0, str(ROOT / "src"))
        api = importlib.import_module("nabt.discourse")
        corpus = importlib.import_module("nabt.corpus_evidence")
        nabt = importlib.import_module("nabt")
        if not Path(api.__file__).resolve().is_relative_to((ROOT / "src/nabt").resolve()):
            raise RuntimeError("Runtime imported from an unexpected path")
        model = corpus.learn_qac_lexicon((MATERIAL / "lexical_premises.tsv").read_bytes(),
                                        source_id="independent_arabic_holdout_v1")
        model_summary = model.summary()
        raw("lexical_summary", None, model_summary)
        runtime_version = nabt.__version__
        for case in material["cases"]:
            cid, checks = case["id"], []
            ctx = deepcopy(contexts[case["context"]])
            source_id, scope = "holdout_" + cid.lower(), "independent_holdout_v1"
            try:
                document = api.read_discourse(case["text"], lexical_model=model, context=ctx,
                    source_id=source_id, scope=scope)
                documents[cid] = document
                raw("read_discourse", cid, document)
                claims = document.get("claims", [])
                check(checks, "document_status", document.get("status") == case["expected_document_status"],
                      document.get("status"), case["expected_document_status"],
                      unsafe=case["expected_document_status"] == "DEFER" and document.get("status") == "LICENSED_DISCOURSE")
                check(checks, "source_text", document.get("source_text") == case["text"])
                check(checks, "source_identity", document.get("source_id") == source_id and document.get("scope") == scope)
                check(checks, "source_hash", document.get("source_sha256") == sha256(case["text"].encode()).hexdigest())
                check(checks, "world_truth_not_established", document.get("world_truth") == "NOT_ESTABLISHED")
                if "claims_min" in case:
                    check(checks, "minimum_claims", len(claims) >= case["claims_min"], len(claims), case["claims_min"])
                if "claims_max" in case:
                    check(checks, "maximum_claims", len(claims) <= case["claims_max"], len(claims), case["claims_max"], unsafe=True)
                for i, pattern in enumerate(case["required_claims"]):
                    check(checks, f"required_claim:{i}", any(matches(c, pattern) for c in claims), expected=pattern)
                for i, pattern in enumerate(case["forbidden_claims"]):
                    check(checks, f"forbidden_claim:{i}", not any(matches(c, pattern) for c in claims), expected=pattern, unsafe=True)
                if "expected_clause_forces" in case:
                    actual_forces = [c.get("force") for c in document.get("clauses", [])]
                    check(checks, "clause_forces", actual_forces == case["expected_clause_forces"], actual_forces, case["expected_clause_forces"])
                replay = api.verify_discourse(document, text=case["text"], lexical_model=model,
                    context=ctx, source_id=source_id, scope=scope)
                raw("verify_discourse", cid, replay)
                check(checks, "document_replay", replay.get("valid") is True)
                available = {c["claim_id"] for c in claims}
                for qi, q in enumerate(case["questions"]):
                    answer = api.ask_discourse(case["text"], q["text"], lexical_model=model,
                        context=ctx, source_id=source_id, scope=scope)
                    answers[(cid, qi)] = answer
                    raw("ask_discourse", cid, answer, question_index=qi)
                    status = answer.get("status")
                    question_metrics[q["expected_status"]][status or "MISSING_STATUS"] += 1
                    check(checks, f"question:{qi}:status", status == q["expected_status"], status, q["expected_status"],
                          unsafe=q["expected_status"] in ("UNKNOWN", "DEFER") and status in ("SUPPORTED", "REFUTED", "CONFLICT"))
                    check(checks, f"question:{qi}:source_bytes", answer.get("source_text") == case["text"] and answer.get("question_text") == q["text"])
                    check(checks, f"question:{qi}:document_identity", answer.get("document_report_id") == document.get("report_id"))
                    check(checks, f"question:{qi}:world_truth", answer.get("world_truth") == "NOT_ESTABLISHED")
                    proofs, counters = answer.get("proofs", []), answer.get("counterproofs", [])
                    if status in ("SUPPORTED", "CONFLICT"):
                        check(checks, f"question:{qi}:support_exists", bool(proofs))
                    if status in ("REFUTED", "CONFLICT"):
                        check(checks, f"question:{qi}:counterproof_exists", bool(counters))
                    if status in ("UNKNOWN", "DEFER"):
                        check(checks, f"question:{qi}:no_grounded_evidence", not proofs and not counters, unsafe=True)
                    for pi, proof in enumerate(proofs + counters):
                        check(checks, f"question:{qi}:claim_binding:{pi}", proof.get("claim_id") in available and
                              proof.get("document_report_id") == document.get("report_id"))
                    verified = api.verify_discourse_answer(answer, text=case["text"], question=q["text"],
                        lexical_model=model, context=ctx, source_id=source_id, scope=scope)
                    raw("verify_discourse_answer", cid, verified, question_index=qi)
                    check(checks, f"question:{qi}:replay", verified.get("valid") is True)
            except Exception as exc:
                detail = {"case_id": cid, "type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
                errors.append(detail)
                raw("exception", cid, detail)
                check(checks, "runtime_exception", False, str(exc))
            passed = all(c["pass"] for c in checks)
            totals[case["category"]]["total"] += 1
            totals[case["category"]]["passed"] += passed
            results.append({"id": cid, "category": case["category"], "focus": case["focus"],
                            "passed": passed, "checks": checks})
            print(dump({"case": cid, "passed": passed, "failed_checks": [c["name"] for c in checks if not c["pass"]]}), flush=True)
        cross_checks = []
        for cross in material["cross_case_checks"]:
            by_id = {c["id"]: c for c in material["cases"]}
            check(cross_checks, cross["id"] + ":same_exact_input_bytes",
                  len({by_id[cid]["text"].encode() for cid in cross["cases"]}) == 1)
            for cid, owner in cross["required_positive_owners"].items():
                claims = documents.get(cid, {}).get("claims", [])
                pattern = {"predicate": "حَكِيم", "predicate_kind": "property", "args": [owner], "positive": True}
                check(cross_checks, cross["id"] + ":owner:" + cid, any(matches(c, pattern) for c in claims), expected=pattern)
            omitted = documents.get(cross["absent_speaker_case"], {})
            check(cross_checks, cross["id"] + ":no_speaker_no_grounding", omitted.get("status") == "DEFER" and omitted.get("claims") == [])
        replay_checks = []
        # Same utterance, different explicit speaker: old certificates must not
        # survive replacing their independently supplied context premise.
        for cid, changed_context in (("H21", "speaker_zayd"), ("H22", "speaker_nasser")):
            if cid not in documents or (cid, 0) not in answers:
                check(replay_checks, cid + ":context_replacement_available", False)
                continue
            case = next(c for c in material["cases"] if c["id"] == cid)
            changed = api.verify_discourse(documents[cid], text=case["text"], lexical_model=model,
                context=deepcopy(contexts[changed_context]), source_id="holdout_" + cid.lower(), scope="independent_holdout_v1")
            raw("verify_discourse_changed_context", cid, changed)
            check(replay_checks, cid + ":changed_context_report_rejected", changed.get("valid") is False)
            changed_answer = api.verify_discourse_answer(answers[(cid, 0)], text=case["text"],
                question=case["questions"][0]["text"], lexical_model=model,
                context=deepcopy(contexts[changed_context]), source_id="holdout_" + cid.lower(), scope="independent_holdout_v1")
            raw("verify_answer_changed_context", cid, changed_answer)
            check(replay_checks, cid + ":changed_context_answer_rejected", changed_answer.get("valid") is False)
    except Exception as exc:
        errors.append({"stage": "setup_or_cross_checks", "type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()})
        raw("exception", None, errors[-1])
        runtime_version = locals().get("runtime_version")
        cross_checks, replay_checks = locals().get("cross_checks", []), locals().get("replay_checks", [])
        # Preserve the denominator even if the lexical source cannot compile.
        seen = {r["id"] for r in results}
        for case in material["cases"]:
            if case["id"] not in seen:
                totals[case["category"]]["total"] += 1
                results.append({"id": case["id"], "category": case["category"], "focus": case["focus"], "passed": False,
                                "checks": [{"name": "not_executed_after_exception", "pass": False}]})
    finally:
        raw_handle.close()
    after = runtime_inventory()
    _, after_freeze_sha = verify_freeze()
    lines = raw_path.read_text(encoding="utf-8").splitlines()
    raw_valid = len(lines) == len(raw_hashes) and all(sha256(line.encode()).hexdigest() == h and dump(json.loads(line)) == line
                                                   for line, h in zip(lines, raw_hashes))
    unsafe = [{"case_id": row["id"], **c} for row in results for c in row["checks"] if c.get("unsafe_acceptance")]
    passed = sum(row["passed"] for row in results)
    strict = (passed == len(material["cases"]) and all(c["pass"] for c in cross_checks + replay_checks) and
              len(cross_checks) == 4 and len(replay_checks) == 4 and not errors and not unsafe and raw_valid and
              before == after and freeze_sha == after_freeze_sha)
    result = {"schema": "nabt.independent-arabic-holdout-result.v1", "created_utc": datetime.now(timezone.utc).isoformat(),
        "material_freeze_sha256": freeze_sha, "baseline_commit": material["baseline_commit"],
        "runtime_git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "runtime_version": runtime_version, "environment": {"python": sys.version, "platform": platform.platform()},
        "runtime_before": before, "runtime_after": after, "runtime_unchanged": before == after,
        "strict_pass": strict, "coverage_complete": strict,
        "case_score": {"passed": passed, "total": len(material["cases"])}, "category_scores": dict(totals),
        "question_total": sum(len(c["questions"]) for c in material["cases"]),
        "question_status_by_expectation": {k: dict(v) for k, v in question_metrics.items()},
        "cases": results, "cross_case_checks": cross_checks, "separate_replay_checks": replay_checks,
        "unsafe_acceptances": unsafe, "runtime_errors": errors, "measurement_valid": not errors and raw_valid and before == after,
        "raw_log": {"path": str(raw_path.relative_to(ROOT)), "sha256": digest(raw_path), "records": len(lines),
                    "complete_reparse_and_line_hashes": raw_valid, "line_sha256": raw_hashes},
        "claim_scope": "Finite authored composition coverage under explicit lexical/context premises; not unrestricted Arabic understanding or world truth."}
    with output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(dump({"report": str(output.relative_to(ROOT)), "score": result["case_score"], "strict_pass": strict,
                "unsafe_acceptances": len(unsafe), "runtime_errors": len(errors)}))
    return 0 if strict else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New JSON result path; raw JSONL uses the same stem")
    args = parser.parse_args()
    sys.exit(run(args.output.resolve()))
