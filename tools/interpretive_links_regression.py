#!/usr/bin/env python3
"""Exposed current-runtime replay of the unchanged 24+6 directed oracle.

The retained runners, inputs, scorers and mutation recipes remain immutable.
This orchestration replaces their historical runtime/dependency pins, not their
linguistic expectations. Fresh calls and saved-journal review walk the same
complete protocol; review imports no production parser and issues no API calls.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import gzip
from importlib.machinery import SourceFileLoader
import json
import os
from pathlib import Path
import sys
import tarfile
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "evidence/arabic_completion_v3/independent_oracle"
LEGACY = ORACLE / "continuation_v6_review2"
CURRENT = ROOT / "evidence/interpretive_links_v1"
RUNTIME = CURRENT / "code_freeze_v1.json"
RUNTIME_SHA = "1d709c94842776699056c63969d62e8b3bb9a58af339cb8676b8091b27a37eda"
DEPENDENCIES = CURRENT / "oracle_dependency_freeze_v1.json"
PREVIOUS_DEPENDENCIES_SHA = "6e8dde893aa919dec0dd23e37a7882b228d45d977743526ef2178483599fabb3"
BASELINE_SHA = "1ca1469c18749b3ba7160c54029bfd449621ffdb97782a832325bdbf6a885080"
VERSION = "nabt.interpretive-links-oracle-regression.v1"
FREEZE_VERSION = "nabt.interpretive-links-oracle-dependencies.v1"
_CHECKED_SOURCES = None
REPORT_KEYS = frozenset("authority claims clauses construction_law_id construction_law_sha256 construction_policy_sha256 "
    "context derived_readings language_id law_id law_sha256 lexical_model occurrences partition policy_sha256 "
    "reader_version report_id schema scope source_id source_sha256 source_text status world_truth "
    "claim_binding_schema nominal_morphology".split())
ANSWER_KEYS = frozenset("schema law_id law_sha256 language_id reader_version source_id scope source_text question_text "
    "source_sha256 question_sha256 document_report_id question_report_id context_sha256 lexical_model "
    "nominal_description_source status kind query bindings question_interpretations answer_basis "
    "predicate_interpretations proofs counterproofs missing_premises authority world_truth answer_id".split())


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def require(value, message):
    if not value:
        raise ValueError(message)


def pinned(path, expected):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected, "Pinned file changed: " + str(path.relative_to(ROOT)))
    return raw


def file_row(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


@contextmanager
def checked_helper_sources(rows):
    """Compile checked helper bytes, including retained dynamic file imports.

    Historical helper code uses explicit SourceFileLoader objects, which do
    not visit a meta-path finder. This scoped loader adapter binds those code
    bytes too; it changes no historical pin, validator or acceptance check.
    Standard-library imports remain outside this repository boundary.
    """
    global _CHECKED_SOURCES
    previous, previous_get_code = _CHECKED_SOURCES, SourceFileLoader.get_code
    sources, executed = {}, {}
    for row in rows:
        if row["path"].endswith(".py"):
            path = Path(os.path.abspath(ROOT / row["path"]))
            raw = path.read_bytes()
            require(len(raw) == row["bytes"] and sha256(raw).hexdigest() == row["sha256"],
                    "Helper changed before source import: " + row["path"])
            sources[path] = raw
    _CHECKED_SOURCES = sources, executed
    def get_code(loader, fullname):
        # Ownership follows the inventoried logical path. A temporary symlink
        # must not turn repository code into an ambient external import.
        path = Path(os.path.abspath(loader.path))
        if not path.is_relative_to(ROOT):
            return previous_get_code(loader, fullname)
        require(path in sources, "Unfrozen helper import: " + str(path.relative_to(ROOT)))
        raw = sources[path]
        executed[str(path.relative_to(ROOT))] = sha256(raw).hexdigest()
        return compile(raw, str(path), "exec", dont_inherit=True)
    SourceFileLoader.get_code = get_code
    try:
        yield executed
    finally:
        SourceFileLoader.get_code = previous_get_code
        _CHECKED_SOURCES = previous


def module(name, path):
    logical = Path(os.path.abspath(path))
    require(_CHECKED_SOURCES is not None and logical in _CHECKED_SOURCES[0], "Helper has no validated source bytes")
    raw = _CHECKED_SOURCES[0][logical]
    _CHECKED_SOURCES[1][str(path.relative_to(ROOT))] = sha256(raw).hexdigest()
    value = ModuleType(name)
    value.__file__ = str(path)
    exec(compile(raw, str(path), "exec", dont_inherit=True), value.__dict__)
    return value


def helpers():
    # Only their pure material/scoring/journal APIs are called. No old pin,
    # guard, frozen function or historical observation is patched in memory.
    runner = module("current_oracle_material", LEGACY / "run_oracle_v6.py")
    sources = module("current_oracle_source_cases", LEGACY / "run_source_counterexamples_v1.py")
    mutations = module("current_oracle_mutations", ORACLE / "oracle_mutations_v2.py")
    loader = module("current_oracle_frozen_imports", ROOT / "tools/evaluate_aligned_acquisition.py")
    return runner, sources, mutations, loader


def dependency_paths():
    old = json.loads(pinned(LEGACY / "runner_freeze_v6.json", PREVIOUS_DEPENDENCIES_SHA))
    material = json.loads((ORACLE / "freeze.json").read_bytes())
    paths = {row["path"] for row in old["files"]}
    for row in old["files"]:
        if row["path"].startswith("evidence/"):
            require(file_row(ROOT / row["path"]) == row, "Retained oracle evidence/helper changed: " + row["path"])
    paths.update(str((ORACLE / row["path"]).relative_to(ROOT)) for row in material["files"])
    paths.update({str((LEGACY / "runner_freeze_v6.json").relative_to(ROOT)),
        "tools/interpretive_links_regression.py", "tests/test_interpretive_links_regression.py",
        "tools/evaluate_aligned_acquisition.py", "evidence/interpretive_links_v1/regression_policy_v1.json"})
    return paths


def freeze_dependencies():
    require(not DEPENDENCIES.exists(), "Never overwrite an observed dependency freeze")
    pinned(RUNTIME, RUNTIME_SHA)
    initial = [file_row(ROOT / path) for path in sorted(dependency_paths())]
    with checked_helper_sources(initial):
        runner, _, _, _ = helpers()
        snapshot = runner.E.runtime_snapshot(RUNTIME, ROOT)
        runtime_paths = {row["path"] for row in json.loads(RUNTIME.read_bytes())["files"]}
        paths = dependency_paths() | {row["path"] for row in snapshot["files"] if row["path"] not in runtime_paths}
        value = {"schema": FREEZE_VERSION, "runtime_freeze_sha256": RUNTIME_SHA,
            "previous_dependency_freeze_sha256": PREVIOUS_DEPENDENCIES_SHA,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "phase": "EXPOSED_REGRESSION_NOT_A_NEW_BLIND_EXPERIMENT",
            "files": [file_row(ROOT / path) for path in sorted(paths)]}
        with DEPENDENCIES.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return {"dependency_freeze": str(DEPENDENCIES.relative_to(ROOT)),
            "sha256": sha256(DEPENDENCIES.read_bytes()).hexdigest(), "files": len(value["files"])}


def check_dependencies():
    raw = DEPENDENCIES.read_bytes()
    value = json.loads(raw)
    require(value["schema"] == FREEZE_VERSION and value["runtime_freeze_sha256"] == RUNTIME_SHA
            and value["previous_dependency_freeze_sha256"] == PREVIOUS_DEPENDENCIES_SHA
            and value["phase"] == "EXPOSED_REGRESSION_NOT_A_NEW_BLIND_EXPERIMENT",
            "Unapproved current oracle dependency profile")
    rows = value["files"]
    require(type(rows) is list and all(type(row) is dict and set(row) == {"path", "bytes", "sha256"}
                                     and type(row["path"]) is str for row in rows), "Invalid dependency inventory")
    paths = [row["path"] for row in rows]
    require(len(paths) == len(set(paths)) and dependency_paths() <= set(paths), "Incomplete dependency inventory")
    for row in rows:
        path = Path(row["path"])
        require(not path.is_absolute() and ".." not in path.parts, "Unsafe dependency path")
        require(file_row(ROOT / path) == row, "Oracle dependency changed: " + row["path"])
    return {"sha256": sha256(raw).hexdigest(), "files": rows}


def current_source_score(case, record, context, sources, evaluator):
    """Versioned exact-shape adapter for the one historical v1 schema gate.

    Every semantic/source/question check from the old scorer is retained.
    The original failed shape check is recorded; its replacement independently
    validates the complete v2 report, not a stripped or rehashed projection.
    """
    score = sources.score_case(case, record, context)
    positions = [i for i, check in enumerate(score["checks"]) if check["check"] == "independent_report_integrity"]
    require(len(positions) == 1, "Historical source scorer changed its report integrity gate")
    original = deepcopy(score["checks"][positions[0]])
    fixture = json.loads((sources.MATERIAL / "cases.json").read_bytes())["base_fixture"]
    old_keys = set(json.loads(pinned(ROOT / fixture["path"], fixture["sha256"]))["report"])
    report = record.get("report")
    error = None
    try:
        require(type(report) is dict and set(report) == old_keys | {"claim_binding_schema", "nominal_morphology"},
                "Current counterexample report added or omitted authority fields")
        require(report["schema"] == "nabt.discourse-report.v2"
                and report["reader_version"] == "nabt.discourse-reader.v8"
                and report["claim_binding_schema"] == "nabt.claim-predication-binding.v1"
                and report["nominal_morphology"] is None,
                "Current source counterexample changed its report/description contract")
        raw = (sources.MATERIAL / case["raw_file"]).read_bytes()
        evaluator.validate_report(report, record["inputs"], evaluator.SourceAudit(raw, source_id=case["source_id"]))
        targets = evaluator.question_validation._nominal_targets(report, {claim["claim_id"] for claim in report["claims"]})
        require(len(targets) == sum(len(claim["proofs"]) for claim in report["claims"]),
                "Current source counterexample lost a selected nominal binding")
        require(record["verification"].get("valid") is True, "Current source report replay failed")
    except (ValueError, KeyError, TypeError, IndexError) as failure:
        error = {"type": type(failure).__name__, "message": str(failure)}
    score["checks"][positions[0]] = {"check": "independent_report_integrity", "kind": "integrity",
                                      "passed": error is None, "detail": error}
    score["schema_adapter"] = {"schema": "nabt.current-source-report-shape-adapter.v1",
        "historical_check": original, "historical_keys": sorted(old_keys),
        "current_keys": sorted(old_keys | {"claim_binding_schema", "nominal_morphology"}),
        "payload_fields_removed": [], "complete_current_report_independently_validated": error is None}
    score["passed"] = all(check["passed"] for check in score["checks"])
    return score


def current_payload(name, value):
    """Require the current receipt contract before version-tolerant scorers."""
    require(type(value) is dict, "Public API did not return a report object")
    if name == "read_discourse":
        require(set(value) == REPORT_KEYS and value["schema"] == "nabt.discourse-report.v2"
                and value["reader_version"] == "nabt.discourse-reader.v8"
                and value["claim_binding_schema"] == "nabt.claim-predication-binding.v1"
                and value["nominal_morphology"] is None,
                "Directed oracle report changed or downgraded its current receipt contract")
        require(all(type(analysis.get("claim_bindings")) is list for clause in value["clauses"]
                    for analysis in clause["analyses"]), "Current analysis omitted its predication binding inventory")
    elif name == "ask_discourse":
        require(set(value) == ANSWER_KEYS and value["schema"] == "nabt.discourse-answer.v3"
                and value["reader_version"] == "nabt.discourse-reader.v8"
                and value["nominal_description_source"] is None,
                "Directed oracle answer changed or downgraded its current receipt contract")
    elif name.startswith("verify_"):
        require(value.get("valid") is ("changed_speaker" not in name), "Production replay changed its declared outcome")


class Calls:
    """One typed public-call journal; replay consumes it without calling APIs."""
    def __init__(self, *, log=None, saved=None, api=None):
        self.log, self.saved, self.api = log, saved, api
        self.cursor, self.call_count, self.models = 0, 0, {}
        self.types = Counter()

    def emit(self, value):
        if self.saved is None:
            self.log(value)
        else:
            require(self.cursor < len(self.saved) and wire(self.saved[self.cursor]) == wire(value),
                    "Stored journal changed its full call/observation at record " + str(self.cursor))
            self.cursor += 1

    def call(self, name, inputs, *, cid=None, qi=None, model_id=None, certificate=None):
        self.call_count += 1
        self.types[name] += 1
        row = {"kind": "public_api_call", "call_id": self.call_count, "name": name,
               "case_id": cid, "question_index": qi, "inputs": inputs}
        if self.saved is not None:
            require(self.cursor < len(self.saved), "Stored public call is missing")
            actual = self.saved[self.cursor]
            require(type(actual) is dict and set(actual) == set(row) | {"returned"}
                    and type(actual["call_id"]) is int
                    and wire({key: actual[key] for key in row}) == wire(row),
                    "Stored public call changed its type, order, complete input or execution outcome")
            returned = actual["returned"]
        else:
            try:
                if name == "learn_qac_lexicon":
                    model = self.api[name](bytes.fromhex(inputs["raw_hex"]), source_id=inputs["source_id"])
                    self.models[inputs["source_id"]] = model
                    returned = model.summary()
                else:
                    options = {"lexical_model": self.models[model_id], **{key: inputs[key]
                               for key in ("context", "source_id", "scope")}}
                    if name == "read_discourse":
                        returned = self.api[name](inputs["text"], **options)
                    elif name == "ask_discourse":
                        returned = self.api[name](inputs["text"], inputs["question"], **options)
                    elif name in ("verify_discourse", "verify_discourse_changed_speaker"):
                        returned = self.api["verify_discourse"](certificate, text=inputs["text"], **options)
                    else:
                        require(name in ("verify_discourse_answer", "verify_answer_changed_speaker"), "Unknown public operation")
                        returned = self.api["verify_discourse_answer"](certificate, text=inputs["text"],
                                                                     question=inputs["question"], **options)
            except Exception as error:
                self.log({**row, "error": {"type": type(error).__name__, "message": str(error)}})
                raise
        row["returned"] = returned
        self.emit(row)
        current_payload(name, returned)
        return returned

    def complete(self, count, types):
        require(self.call_count == count and self.types == types, "Public call inventory changed")
        if self.saved is not None:
            require(self.cursor == len(self.saved), "Unconsumed, duplicated or invented journal records")


def acquire(calls, raw, source_id, *, cid=None):
    summary = calls.call("learn_qac_lexicon", {"source_id": source_id, "raw_hex": raw.hex(),
        "raw_sha256": sha256(raw).hexdigest(), "excluded_verses": []}, cid=cid)
    require(summary["source"] == {"id": source_id, "byte_length": len(raw), "sha256": sha256(raw).hexdigest()},
            "Learning summary changed its original frozen source")
    return summary


def observe(calls, cid, inputs, questions, public, model_id):
    report = calls.call("read_discourse", public, cid=cid, model_id=model_id)
    require(wire(report["lexical_model"]) == wire(public["model_summary"]), "Report changed its acquired source model")
    verification = calls.call("verify_discourse", {**public, "certificate_report_id": report["report_id"]},
                              cid=cid, model_id=model_id, certificate=report)
    record = {"case_id": cid, "inputs": inputs, "report": report, "verification": verification, "questions": []}
    for qi, wanted in enumerate(questions):
        question = wanted["text"]
        answer = calls.call("ask_discourse", {**public, "question": question}, cid=cid, qi=qi, model_id=model_id)
        query_input = {**public, "text": question, "source_id": "question"}
        inquiry = calls.call("read_discourse", query_input, cid=cid, qi=qi, model_id=model_id)
        qverify = calls.call("verify_discourse", {**query_input, "certificate_report_id": inquiry["report_id"]},
                             cid=cid, qi=qi, model_id=model_id, certificate=inquiry)
        averify = calls.call("verify_discourse_answer", {**public, "question": question,
                            "certificate_answer_id": answer["answer_id"]}, cid=cid, qi=qi,
                            model_id=model_id, certificate=answer)
        record["questions"].append({"answer": answer, "inquiry": inquiry,
                                     "inquiry_verification": qverify, "verification": averify})
    return record


def walk(strict, source, runner, sources, mutations):
    """Shared operation schedule; all expected data stay outside runtime calls."""
    _, material, contexts, profiles = runner.load_material()
    source_material, source_context = sources.load_cases()
    evaluator, scorer = runner.E, runner.S
    summaries, audits, records, scores = {}, {}, {}, []
    for key, profile in profiles.items():
        raw, source_id = (ORACLE / profile["file"]).read_bytes(), "independent_oracle_lexical_" + key
        summaries[key] = acquire(strict, raw, source_id)
        audits[key] = evaluator.SourceAudit(raw, source_id=source_id)
    for case in material["cases"]:
        public = case["input"]
        profile = public["lexical_profile"]
        inputs = {**{key: public[key] for key in ("text", "source_id", "scope")},
                  "context": deepcopy(contexts[public["context_id"]])}
        record = observe(strict, case["id"], inputs, case["expected"]["questions"],
            {**inputs, "lexical_profile": profile, "model_summary": summaries[profile]},
            "independent_oracle_lexical_" + profile)
        record["profile"] = profile
        score = scorer.score_case(case, record, audits[profile])
        records[case["id"]] = record
        scores.append(score)
        strict.emit({"kind": "case_observation", "case_id": case["id"], "record": record, "score": score})
    changed = {}
    by_case = {case["id"]: case for case in material["cases"]}
    for cid, other in (("P04", "P05"), ("P05", "P04")):
        record = records[cid]
        inputs = {**record["inputs"], "context": records[other]["inputs"]["context"]}
        model_id = "independent_oracle_lexical_" + record["profile"]
        document = strict.call("verify_discourse_changed_speaker", {**inputs,
            "certificate_report_id": record["report"]["report_id"]}, cid=cid, model_id=model_id, certificate=record["report"])
        answer = record["questions"][0]["answer"]
        result = strict.call("verify_answer_changed_speaker", {**inputs,
            "question": by_case[cid]["expected"]["questions"][0]["text"], "certificate_answer_id": answer["answer_id"]},
            cid=cid, model_id=model_id, certificate=answer)
        require(document.get("valid") is False and result.get("valid") is False, "Changed-speaker replay accepted")
        changed[cid] = {"report": document, "answer": result}
    by_score = {score["id"]: score for score in scores}
    actor = records["P04"]["inputs"]["text"] == records["P05"]["inputs"]["text"]
    for cid, wanted in (("P04", "malik"), ("P05", "hind")):
        actor = actor and any(c["predicate_kind"] == "event" and c["predicate"] == "أَكْرَمَ"
            and c["args"] == [wanted, "khalid"] for c in records[cid]["report"]["claims"])
    cross = [{"id": "X01", "passed": all(by_score[key]["passed"] for key in ("G01", "G05", "G06"))},
        {"id": "X02", "passed": by_score["N01"]["passed"] and
            by_score["N03"]["provenance_outcome"] in ("correct_abstention", "checked_derivation")},
        {"id": "X03", "passed": bool(actor)}]
    strict.emit({"kind": "cross_case_observations", "case_id": None, "checks": cross, "changed_speaker": changed})
    mutation_results = mutations.run(records, audits, strict.emit)
    strict.complete(171, Counter(learn_qac_lexicon=3, read_discourse=53, verify_discourse=53,
        ask_discourse=29, verify_discourse_answer=29, verify_discourse_changed_speaker=2, verify_answer_changed_speaker=2))
    source_scores = []
    for case in source_material["cases"]:
        raw = (sources.MATERIAL / case["raw_file"]).read_bytes()
        summary = acquire(source, raw, case["source_id"], cid=case["id"])
        inputs = {**case["input"], "context": deepcopy(source_context)}
        record = observe(source, case["id"], inputs, case["expected"]["questions"],
                         {**inputs, "model_summary": summary}, case["source_id"])
        score = current_source_score(case, record, source_context, sources, evaluator)
        source_scores.append(score)
        source.emit({"kind": "case_observation", "case_id": case["id"], "record": record, "score": score})
    source.complete(34, Counter(learn_qac_lexicon=6, read_discourse=10, verify_discourse=10,
                               ask_discourse=4, verify_discourse_answer=4))
    return {"cases": scores, "cross_case_checks": cross, "mutation_checks": mutation_results,
            "source_counterexamples": {"cases": source_scores, "summary": sources.summarize(source_scores)}}


def gate(results):
    reference = json.loads(pinned(ORACLE / "postreview_run_v2/review.json", BASELINE_SHA))
    scores, mutations = results["cases"], results["mutation_checks"]
    require(all(type(score["passed"]) is bool and type(score["fixed_status_case"]) is bool
                and all(type(check["passed"]) is bool for check in score["checks"])
                and all(type(question["status_match"]) is bool and type(question["independently_validated"]) is bool
                        for question in score["questions"]) for score in scores), "Untyped case/check verdict")
    expected_ids = list(reference["regression_gate"]["actual_failure_inventory"])
    require([score["id"] for score in scores] == expected_ids and len(scores) == 24, "Directed case inventory changed")
    residuals = {score["id"]: sorted(c["check"] for c in score["checks"] if not c["passed"]) for score in scores}
    no_new_residuals = all(set(values) <= set(reference["regression_gate"]["actual_failure_inventory"][cid])
                           for cid, values in residuals.items())
    integrity = [dict(id=score["id"], **check) for score in scores for check in score["checks"]
                 if check["kind"] in ("integrity", "execution") and not check["passed"]]
    unsafe = [{"id": score["id"], "check": name} for score in scores for name in score["unsafe"]]
    require([m["id"] for m in mutations] == [m["id"] for m in reference["mutation_checks"]]
            and len(mutations) == 18, "Mutation inventory changed")
    mutation_ok = all(new["outcome"] == old["outcome"] and
                      (new["outcome"] != "PASS" or new.get("independent_mutation_accepted") is False)
                      for new, old in zip(mutations, reference["mutation_checks"]))
    cross = results["cross_case_checks"]
    cross_ok = len(cross) == 3 and all(new["id"] == old["id"] and (not old["passed"] or new["passed"])
                                     for new, old in zip(cross, reference["cross_case_checks"]))
    fixed = [score for score in scores if score["fixed_status_case"]]
    questions = [question for score in scores for question in score["questions"]]
    source = results["source_counterexamples"]["summary"]
    require([score["id"] for score in results["source_counterexamples"]["cases"]] ==
            ["H01", "H02", "H03", "H04", "H05", "H06"]
            and all(type(source[key]) is int for key in ("total", "positive_controls", "negative_cases", "questions"))
            and (source["total"], source["positive_controls"], source["negative_cases"], source["questions"]) == (6, 2, 4, 4),
            "Source counterexample inventory/denominator changed")
    require(len(fixed) == 22 and len(questions) == 29, "Fixed-case or question denominator changed")
    summary = {"fixed_cases": {"total": 22, "passed": sum(s["passed"] for s in fixed)},
        "questions": {"total": 29, "status_matches": sum(q["status_match"] for q in questions),
                      "independently_validated": sum(q["independently_validated"] for q in questions)},
        "conditional_provenance": {"total": 2, "outcomes": {s["id"]: s["provenance_outcome"]
                                    for s in scores if not s["fixed_status_case"]},
            "not_counted_as_language_coverage": True},
        "residuals": residuals, "unsafe_check_failures": unsafe, "independent_integrity_failures": integrity,
        "mutation_outcomes": {m["id"]: m["outcome"] for m in mutations},
        "source_counterexamples": source, "public_calls": {"directed": 171, "source_counterexamples": 34}}
    summary["measurement_valid"] = (not integrity and not source["independent_integrity_failures"]
                                      and not any(m["outcome"] == "ERROR" for m in mutations))
    summary["strict_pass"] = bool(summary["measurement_valid"] and all(s["passed"] for s in scores)
        and all(c["passed"] for c in cross) and all(m["outcome"] == "PASS" for m in mutations) and source["gate_pass"])
    summary["regression_gate_pass"] = bool(summary["measurement_valid"] and not unsafe and no_new_residuals
        and mutation_ok and cross_ok and summary["questions"]["independently_validated"] == 29 and source["gate_pass"])
    return summary


def read_journal(path):
    raw = gzip.decompress(path.read_bytes())
    require(raw.endswith(b"\n"), "Truncated current oracle journal")
    values = [json.loads(line) for line in raw.splitlines(keepends=True)]
    require(raw == b"".join(wire(value) + b"\n" for value in values), "Noncanonical current oracle journal")
    return values


def measured_snapshot(evaluator, dependencies):
    """Reconstruct the complete expected archive from checked local sources."""
    pinned(RUNTIME, RUNTIME_SHA)
    runtime = evaluator.runtime_snapshot(RUNTIME, ROOT)
    runtime_paths = {row["path"] for row in json.loads(RUNTIME.read_bytes())["files"]}
    require({row["path"] for row in runtime["files"]} <= runtime_paths | {row["path"] for row in dependencies["files"]},
            "Current checker snapshot contains an unfrozen dependency")
    rows = {row["path"]: row for row in runtime["files"]}
    rows.update({row["path"]: row for row in dependencies["files"]})
    for path in (RUNTIME, RUNTIME.parent / json.loads(RUNTIME.read_bytes())["archive_filename"], DEPENDENCIES):
        row = file_row(path)
        rows[row["path"]] = row
    snapshot = {**runtime, "files": list(rows.values())}
    snapshot["measured_snapshot_sha256"] = sha256(wire(snapshot["files"])).hexdigest()
    return runtime, snapshot


def review(output_dir, runner, sources, mutations, dependencies):
    result = json.loads((output_dir / "result.json").read_bytes())
    require(set(result) == {"schema", "runtime_freeze_sha256", "dependency_freeze_sha256", "snapshot", "runtime_snapshot",
        "phase", "exact_historical_payload_equality_claimed", "started_utc", "code_archive", "results", "raw_journals",
        "summary", "finished_utc", "executed_checker_sources"}, "Current oracle result added or omitted authority fields")
    require(wire(check_dependencies()) == wire(dependencies), "Current review checker dependency profile changed")
    runtime, snapshot = measured_snapshot(runner.E, dependencies)
    require(result["schema"] == VERSION and result["runtime_freeze_sha256"] == RUNTIME_SHA
            and result["dependency_freeze_sha256"] == dependencies["sha256"]
            and result["phase"] == "EXPOSED_REGRESSION_NOT_A_NEW_BLIND_EXPERIMENT"
            and result["exact_historical_payload_equality_claimed"] is False
            and wire(result["snapshot"]) == wire(snapshot)
            and wire(result["runtime_snapshot"]) == wire(runtime),
            "Current oracle review profile/snapshot changed")
    archive = output_dir / result["code_archive"]["filename"]
    require(archive.parent == output_dir and sha256(archive.read_bytes()).hexdigest() == result["code_archive"]["sha256"],
            "Current measured code archive changed")
    expected = {row["path"]: row for row in snapshot["files"]}
    with tarfile.open(archive, "r:gz") as saved:
        members = saved.getmembers()
        require(len(members) == len(expected) and {m.name for m in members} == set(expected)
                and all(m.isfile() for m in members), "Measured code archive inventory changed")
        for member in members:
            raw, row = saved.extractfile(member).read(), expected[member.name]
            require(len(raw) == row["bytes"] and sha256(raw).hexdigest() == row["sha256"], "Measured archive member changed")
    inventories = {}
    streams = []
    for name, count in (("strict", 214), ("source_counterexamples", 40)):
        path = output_dir / name / "raw.jsonl.gz"
        values = read_journal(path)
        require(len(values) == count, "Journal record inventory changed")
        inventory = [{"index": i, "bytes": len(wire(row) + b"\n"), "sha256": sha256(wire(row) + b"\n").hexdigest(),
                      "kind": row["kind"], "case_id": row.get("case_id"), "call_id": row.get("call_id")}
                     for i, row in enumerate(values)]
        inventories[name] = runner.finish_journal(path, inventory)
        streams.append(Calls(saved=values))
    require(wire(inventories) == wire(result["raw_journals"]), "Raw journal hash/inventory changed")
    checked = walk(*streams, runner, sources, mutations)
    summary = gate(checked)
    require(wire(result["executed_checker_sources"]) == wire(_CHECKED_SOURCES[1]),
            "Independently executed checker source inventory changed")
    require(wire(checked) == wire(result["results"]) and wire(summary) == wire(result["summary"]),
            "Stored results differ from independently rescored complete calls")
    require(wire(check_dependencies()) == wire(dependencies)
            and wire(runner.E.runtime_snapshot(RUNTIME, ROOT)) == wire(result["runtime_snapshot"]),
            "Runtime or checker changed during independent review")
    return {"schema": VERSION + ".review", "new_runtime_calls_in_review": 0,
        "all_public_calls_and_observations_bound": True, "independently_rescored": True,
        "runtime_freeze_sha256": RUNTIME_SHA, "dependency_freeze_sha256": dependencies["sha256"],
        "raw_journals": inventories, "summary": summary, "regression_gate_pass": summary["regression_gate_pass"]}


def execute(output_dir):
    require(not output_dir.exists() and output_dir.is_relative_to(ROOT), "Use a new repository-local oracle attempt")
    dependencies = check_dependencies()
    pinned(RUNTIME, RUNTIME_SHA)
    with checked_helper_sources(dependencies["files"]) as executed:
        runner, sources, mutations, loader = helpers()
        runtime, snapshot = measured_snapshot(runner.E, dependencies)
        output_dir.mkdir(parents=True)
        result = {"schema": VERSION, "runtime_freeze_sha256": RUNTIME_SHA,
            "dependency_freeze_sha256": dependencies["sha256"], "snapshot": snapshot, "runtime_snapshot": runtime,
            "phase": "EXPOSED_REGRESSION_NOT_A_NEW_BLIND_EXPERIMENT",
            "exact_historical_payload_equality_claimed": False, "started_utc": datetime.now(timezone.utc).isoformat()}
        result["code_archive"] = runner.E.capture_code(snapshot, output_dir / "result.json")
        streams, inventories, handles = [], {}, []
        try:
            with loader.frozen_runtime({"files": {row["path"]: row["sha256"] for row in snapshot["files"]}}):
                from nabt.corpus_evidence import learn_qac_lexicon
                from nabt.discourse import ask_discourse, read_discourse, verify_discourse, verify_discourse_answer
                api = {f.__name__: f for f in (learn_qac_lexicon, ask_discourse, read_discourse, verify_discourse, verify_discourse_answer)}
                for name in ("strict", "source_counterexamples"):
                    folder = output_dir / name
                    folder.mkdir()
                    handle = gzip.open(folder / "raw.jsonl.gz", "wb")
                    handles.append(handle)
                    inventory = inventories[name] = []
                    def log(value, stream=handle, items=inventory):
                        raw = wire(value) + b"\n"
                        items.append({"index": len(items), "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
                                      "kind": value["kind"], "case_id": value.get("case_id"), "call_id": value.get("call_id")})
                        stream.write(raw)
                        stream.flush()
                    streams.append(Calls(log=log, api=api))
                result["results"] = walk(*streams, runner, sources, mutations)
            for handle in handles:
                handle.close()
            result["raw_journals"] = {name: runner.finish_journal(output_dir / name / "raw.jsonl.gz", inventory)
                                      for name, inventory in inventories.items()}
            require(wire(check_dependencies()) == wire(dependencies)
                    and wire(runner.E.runtime_snapshot(RUNTIME, ROOT)) == wire(runtime),
                    "Runtime/checker changed during current oracle execution")
            result["summary"] = gate(result["results"])
            result["executed_checker_sources"] = dict(executed)
            result["finished_utc"] = datetime.now(timezone.utc).isoformat()
            (output_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            reviewed = review(output_dir, runner, sources, mutations, dependencies)
            (output_dir / "review.json").write_text(json.dumps(reviewed, ensure_ascii=False, indent=2) + "\n")
            return reviewed
        except Exception as error:
            for handle in handles:
                handle.close()
            (output_dir / "failure.json").write_text(json.dumps({"schema": VERSION + ".failure",
                "runtime_freeze_sha256": RUNTIME_SHA, "dependency_freeze_sha256": dependencies["sha256"],
                "error": {"type": type(error).__name__, "message": str(error)},
                "regression_gate_pass": False}, ensure_ascii=False, indent=2) + "\n")
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-dependencies", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.freeze_dependencies:
        require(args.output_dir is None, "Freeze preparation does not execute a measurement")
        print(json.dumps(freeze_dependencies(), ensure_ascii=False))
        return 0
    require(args.output_dir is not None, "An output directory is required")
    result = execute(args.output_dir.resolve())
    print(json.dumps({"output": str(args.output_dir), "summary": result["summary"]}, ensure_ascii=False))
    return 0 if result["regression_gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
