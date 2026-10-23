#!/usr/bin/env python3
"""Evaluate source-fixed morphology cases without importing an answer parser.

V1 material predates implementation inspection. V2 makes the declared source
correction from event time to time indicated by form, and is consequently a
regression set rather than an untouched holdout. The adapter below only maps
public report fields to authored semantic expectations. It never repairs an
input, calls the runtime's clause table as an oracle, or changes case gold.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

VERSION = "nabt.morphology.independent-evaluator.v1.5"
MATERIAL_SHA256 = {
    "v1": "4425a249fe64b627c36671a39a88fec79ad8ac0c9f3ce710bab726045ccc2f81",
    "v2": "0f17e68a4d7a33d4afa64bb645ba88c55ac1d0e3248de241f1c1028442d37ea4",
}
MATERIAL_COUNTS = {"v1": 42, "v2": 43}
SCOPE = "independent_morphology_review"
DOCUMENTED_BOUNDARY_MISSES = {"m12", "m13", "m32", "m33"}
FREEZE_MANIFEST_SHA256 = "8449c5c4bf32549c6147de006b0586d41cb4c6f656e2764c63e3437a35b7bffd"
FROZEN_RUNTIME_SHA256 = "4b5c8f4f7c2bb765791e0a9c94e1be279a1a3ad1e186e6346d77546f23a47d46"
FROZEN_ARCHIVE_SHA256 = "f657df1db06f714789e8bbf64708770a5355b0f9542281798ba43735286a042a"
CODE_FREEZES = {
    "nominal_v1": ("9d9f71eb1b26caac6ea170fe839e7b7f2903eccf827c5bbf7b2c78d3a46a13cd",
                   "c00458629fcd08a6cefb616d0fb1caaec5958996b0532043d0fd1a92d922740a",
                   "6d86c0709c97a89375fc9ff498d1576585c3e432831c7ac17cfc1eb75c2f2724"),
    "derivation_v1": ("5cdea1a66bd92f3f014cc2f14ab2d502f43f630d03977cb111020e3370907eed",
                      "e8e31cdaa1cb56e3700befd4d8fb883e11f83cd684e6cd72b45e133410bf3cac",
                      "fd24793a4fb805425e4bba60219c70a0f1fbb4dda7a89b07d1c6a0ffc6c3b060"),
    "v1": (FREEZE_MANIFEST_SHA256, FROZEN_RUNTIME_SHA256, FROZEN_ARCHIVE_SHA256),
    "text_morphology_v1": ("b15dfab7ed6166aa5aae236c7c0b22ce48f805a6bc0d8f6c3b6f12bae2b951ee",
                           "82a5d9b283d403bf257a95e5c8a1eb9b2ea300a90ca1a2e881de478bf29f7496",
                           "d1661a0abef5f25d048b675270517e400f83c08a1a0b6b3f3c7c399514f94304"),
}
CODE_FREEZE_PATHS = {
    "nominal_v1": ROOT / "evidence/nominal/code_freeze_v1.json",
    "derivation_v1": ROOT / "evidence/derivation/code_freeze_v1.json",
    "v1": ROOT / "evidence/morphology/code_freeze_v1.json",
    "text_morphology_v1": ROOT / "evidence/text_morphology/code_freeze_v1.json",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def load_material(version="v2"):
    raw = (ROOT / "evidence/morphology" / f"independent_cases_{version}.json").read_bytes()
    require(sha256(raw).hexdigest() == MATERIAL_SHA256[version], "Frozen case bytes changed")
    material = json.loads(raw)
    cases = material["cases"]
    require(len(cases) == len({c["id"] for c in cases}) == MATERIAL_COUNTS[version],
            "Independent case inventory changed")
    passages = set()
    for source in material["sources"]:
        content = None
        if "path" in source:
            content = (ROOT / source["path"]).read_bytes()
            require(sha256(content).hexdigest() == source["sha256"], "Primary source changed")
        for passage in source["passages"]:
            require(passage["id"] not in passages, "Repeated primary passage identity")
            passages.add(passage["id"])
            embedded = passage["text"].encode("utf-8")
            require(sha256(embedded).hexdigest() == passage["sha256"], "Embedded passage changed")
            if content is not None:
                require(content[passage["byte_start"]:passage["byte_end"]] == embedded,
                        "Primary passage does not match its byte range")
    for case in cases:
        require(set(case["source_passages"]) <= passages, "Case refers to an absent primary passage")
    return material


def snapshot():
    """Record the actual package and formal inputs; never scan other checkouts."""
    paths = {ROOT / "pyproject.toml"}
    paths.update(p for p in (ROOT / "src").rglob("*") if p.is_file()
                 and p.suffix in {".py", ".json", ".txt"}
                 and "__pycache__" not in p.parts
                 and not any(v.endswith((".egg-info", ".dist-info")) for v in p.parts))
    paths.update(ROOT / p for p in ("formal/Nabt/Morphology.lean", "formal/ExportMorphology.lean"))
    rows = []
    for path in sorted(paths):
        require(path.resolve().is_relative_to(ROOT), "Package file resolves outside NABT")
        data = path.read_bytes()
        rows.append({"path": str(path.relative_to(ROOT)), "bytes": len(data),
                     "sha256": sha256(data).hexdigest()})
    return {"files": rows, "sha256": sha256(wire(rows)).hexdigest()}


def loaded_origins():
    rows = []
    for name, module in sorted(sys.modules.items()):
        if name != "nabt" and not name.startswith("nabt."):
            continue
        filename = getattr(module, "__file__", None)
        if filename is None:
            continue
        path = Path(filename).resolve()
        expected = (ROOT / "src").joinpath(*name.split("."))
        require(path in {expected.with_suffix(".py"), expected / "__init__.py"},
                "Loaded a NABT module outside the measured package: " + name)
        rows.append({"module": name, "path": str(path.relative_to(ROOT)),
                     "sha256": sha256(path.read_bytes()).hexdigest()})
    require(any(row["module"] == "nabt.morphology_reader" for row in rows),
            "Morphology reader was not loaded")
    return rows


def verify_runtime_freeze(actual_snapshot, version="nominal_v1"):
    manifest_sha, snapshot_sha, archive_sha = CODE_FREEZES[version]
    manifest_path = CODE_FREEZE_PATHS[version]
    raw = manifest_path.read_bytes()
    require(sha256(raw).hexdigest() == manifest_sha, "Runtime freeze manifest differs")
    freeze = json.loads(raw)
    rows = freeze["files"]
    require(len(rows) == len({r["path"] for r in rows}), "Runtime freeze repeats a path")
    require(sha256(wire(rows)).hexdigest() == freeze["snapshot_sha256"] == snapshot_sha,
            "Runtime freeze inventory differs")
    package_rows = [r for r in actual_snapshot["files"] if not r["path"].startswith("formal/")]
    require(package_rows == rows, "Measured package is not the frozen runtime")
    archive = manifest_path.parent / freeze["archive_filename"]
    require(sha256(archive.read_bytes()).hexdigest() == freeze["archive_sha256"] == archive_sha,
            "Runtime archive differs")
    by_name = {r["path"]: r for r in rows}
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        require(all(m.isfile() for m in members)
                and len(members) == len(rows) and {m.name for m in members} == set(by_name),
                "Runtime archive member inventory differs")
        for member in members:
            content = bundle.extractfile(member).read()
            wanted = by_name[member.name]
            require(len(content) == wanted["bytes"] and sha256(content).hexdigest() == wanted["sha256"],
                    "Runtime archive bytes differ: " + member.name)
    return {"version": version, "manifest_sha256": manifest_sha, "snapshot_sha256": snapshot_sha,
            "archive_sha256": archive_sha, "files": len(rows)}


def structure_checks(report, text, source_id, scope=SCOPE):
    """Check byte identity and links independently of Arabic property parsing."""
    raw = text.encode("utf-8")
    digest = sha256(raw).hexdigest()
    require(report["source_id"] == source_id and report["source_sha256"] == digest
            and report["raw_text"] == text and report["scope"] == scope,
            "Report changed its source or scope")

    def span(value, exact_text=None):
        a, b = value["start"], value["end"]
        require(type(a) is int and type(b) is int and 0 <= a < b <= len(raw), "Invalid byte interval")
        part = raw[a:b]
        require(value["source_id"] == source_id and value["source_sha256"] == digest,
                "Span belongs to another source")
        require(value["span_sha256"] == sha256(part).hexdigest(), "Wrong span digest")
        require(exact_text is None or part.decode("utf-8", "strict") == exact_text,
                "Span does not contain its claimed text")
        part.decode("utf-8", "strict")

    # This inventory checks explicitly delimited identities; it is not a
    # second implementation of the property-clause language or inference.
    headers = re.findall(r"^قراءة «([^»]+)» للفظ «([^»]+)»:$", text, re.MULTILINE)
    readings = report["readings"]
    require(len(headers) == len(readings), "Reading inventory omitted or invented a header")
    require(len({r["occurrence_id"] for r in readings}) == len(readings), "Occurrence identities collapsed")
    for reading, (label, lexeme) in zip(readings, headers):
        require(reading["reading_id"] == label and reading["lexeme"] == lexeme,
                "Reading identity or lexical bytes changed")
        require(reading["source_id"] == source_id and reading["source_sha256"] == digest
                and reading["scope"] == scope, "Reading escaped source/scope")
        span(reading["header_span"])
        span(reading["lexeme_span"], lexeme)
        for clause in reading["clauses"]:
            span(clause["span"], clause["text"])
        evidence = reading["evidence"]
        support_ids = {e["support_id"] for e in evidence}
        require(len(support_ids) == len(evidence), "Evidence identity collapsed")
        for item in evidence:
            require(item["reading_id"] == label and item["source_id"] == source_id
                    and item["source_sha256"] == digest and item["scope"] == scope
                    and item["occurrence_id"] == reading["occurrence_id"],
                    "Evidence spliced across readings, occurrences, source, or scope")
            span(item["span"], item["text"])
            unsigned = {k: v for k, v in item.items() if k != "support_id"}
            require(sha256(wire(unsigned)).hexdigest() == item["support_id"], "Evidence hash is not canonical")
        for axis in [*reading["axes"].values(), reading["axes"]["diptote"]["genitive"]]:
            require(set(axis["support_ids"]) <= support_ids, "Axis borrows foreign evidence")
        for item in reading["unparsed"]:
            span(item["span"], item["text"])
        genitive = reading["axes"]["diptote"]["genitive"]
        require(genitive["applied_to_occurrence"] is False
                and genitive["application"] == "IF_THIS_IS_AN_INFLECTED_DIPTOTE_IN_GENITIVE_CASE"
                and "INDEPENDENT_GENITIVE_CASE_WITNESS" in genitive["prerequisites"],
                "Conditional sign acquired an actual syntactic role")
    for clause in report["unscoped_clauses"]:
        span(clause["span"], clause["text"])
    require(report["facts"] == [] and report["semantic_projection"] == "NONE"
            and report["world_truth"] == "NOT_ESTABLISHED", "Morphology acquired world-truth authority")


def public_axis(reading, name):
    if name == "diptote_intrinsic":
        parent = reading["axes"]["diptote"]
        prediction = parent["cause_prediction"]
        require(prediction["domain"] == "QUALIFIED_INTRINSIC_CAUSE_FORMULA_ONLY",
                "Intrinsic cause prediction lost its conditional domain")
        return {**parent, **prediction}
    if name == "genitive":
        return reading["axes"]["diptote"]["genitive"]
    return reading["axes"][name]


def expected_axis(axis, expected):
    # Fixed interface names only. No lexeme or case identifier occurs here.
    if expected == "pending":
        return axis["status"] == "DEFER" and bool(axis["missing"] or axis.get("prerequisites"))
    if expected == "conflict":
        return axis["status"] == "CONFLICT" and bool(axis["conflicts"])
    if expected == "out_of_domain":
        return axis["status"] == "OUT_OF_DOMAIN"
    if expected == "affirmed":
        expected = "diptote"
    return axis["status"] == "LICENSED" and axis["candidates"] == [expected]


def properties(expected, report):
    result = []

    def add(name, passed, observed=None):
        result.append({"property": name, "passed": bool(passed), "observed": observed})

    by_id = {reading["reading_id"]: reading for reading in report["readings"]}
    for label, axes in expected.get("readings", {}).items():
        add(label + ":reading_present", label in by_id)
        if label not in by_id:
            continue
        for name, wanted in axes.items():
            actual = public_axis(by_id[label], name)
            add(label + ":" + name, expected_axis(actual, wanted),
                {"expected": wanted, "status": actual["status"],
                 "candidates": actual["candidates"], "missing": actual["missing"],
                 "conflicts": actual["conflicts"],
                 "blocked_by_unparsed_source": actual.get("blocked_by_unparsed_source", False)})
    if expected.get("distinct_reading_ids"):
        add("distinct_reading_identities", len(by_id) == len(expected["readings"])
            and len({r["occurrence_id"] for r in by_id.values()}) == len(by_id))
    for unknown in expected.get("unknown_clauses", []):
        found = any(u["text"] == unknown and u["code"] == "UNPARSED_PROPERTY_CLAUSE"
                    for r in report["readings"] for u in r["unparsed"])
        add("unknown_clause_retained:" + unknown, found)
        add("unknown_clause_blocks_complete_report", report["status"] == "DEFER")
    return result


def summarize_report(report):
    return {"sha256": sha256(wire(report)).hexdigest(), "source_sha256": report["source_sha256"],
            "status": report["status"], "readings": [
                {"reading_id": r["reading_id"], "lexeme": r["lexeme"],
                 "occurrence_id": r["occurrence_id"],
                 "axes": {name: {k: value[k] for k in ("status", "candidates", "missing", "conflicts")}
                          for name, value in r["axes"].items()},
                 "genitive": {k: r["axes"]["diptote"]["genitive"][k]
                              for k in ("status", "candidates", "missing", "conflicts")},
                 "intrinsic_cause_prediction": r["axes"]["diptote"]["cause_prediction"],
                 "unparsed": r["unparsed"]} for r in report["readings"]]}


def structured_failure(result):
    return type(result) is dict and result.get("valid") is False and result.get("status") in {"REJECT", "DEFER"}


def attack_reports(kind, report):
    altered = deepcopy(report)
    if kind == "reading_identity_mutation":
        altered["readings"][0]["reading_id"] = "foreign_reading"
    elif kind == "conclusion_mutation":
        altered["readings"][0]["axes"]["nominal_semantics"]["candidates"] = ["jins_jamid"]
    elif kind == "support_span_mutation":
        reading = altered["readings"][0]
        item = next(e for e in reading["evidence"] if e["property"] == "property_bearing")
        previous_id = item["support_id"]
        unrelated = reading["clauses"][0]
        item["span"], item["text"] = deepcopy(unrelated["span"]), unrelated["text"]
        item["support_id"] = sha256(wire({k: v for k, v in item.items() if k != "support_id"})).hexdigest()
        for axis in reading["axes"].values():
            axis["support_ids"] = [item["support_id"] if s == previous_id else s for s in axis["support_ids"]]
    elif kind == "malformed_certificate":
        bad_nested = deepcopy(report)
        bad_nested["readings"] = None
        return [None, [], {}, {"raw_text": True}, bad_nested]
    else:
        raise ValueError("Unknown review attack")
    return [altered]


def _run_case(case):
    from nabt.errors import NabtError
    from nabt.morphology_reader import (decode_morphology, morphology_number,
                                        read_morphology, verify_morphology)

    text, source_id = case["input"]["text"], case["input"]["source_id"]
    expected, checks, summaries = case["expected"], [], {}

    def add(name, passed, detail=None):
        checks.append({"property": name, "passed": bool(passed), "observed": detail})

    try:
        report = read_morphology(text, source_id=source_id, scope=SCOPE)
    except NabtError as error:
        add("declared_input_rejection", expected.get("must_reject_duplicate_reading_identity") is True
            and error.code == "DUPLICATE_READING_ID" and error.status == "REJECT", error.as_dict())
        return {"id": case["id"], "group": case["group"], "passed": all(c["passed"] for c in checks),
                "checks": checks, "error": error.as_dict()}
    except Exception as error:
        return {"id": case["id"], "group": case["group"], "passed": False,
                "checks": [{"property": "structured_execution", "passed": False,
                            "observed": {"type": type(error).__name__, "message": str(error)}}]}

    try:
        structure_checks(report, text, source_id)
        add("source_identity_and_support_links", True)
    except (ValueError, TypeError, KeyError, UnicodeError) as error:
        add("source_identity_and_support_links", False, str(error))
    seed = verify_morphology(report, text=text, source_id=source_id, scope=SCOPE)
    add("original_certificate_replays", type(seed) is dict and seed.get("valid") is True, seed)
    summaries["before"] = summarize_report(report)
    operation = case.get("operation", {})
    kind = operation.get("kind")
    if expected.get("must_reject_duplicate_reading_identity"):
        add("duplicate_reading_identity_rejected", False)
    elif kind == "retract_source_clause":
        checks.extend(properties(expected["before"], report))
        after_text = operation["after_text"]
        after = read_morphology(after_text, source_id=source_id, scope=SCOPE)
        structure_checks(after, after_text, source_id)
        after_checks = properties(expected["after"], after)
        for check in after_checks:
            check["property"] = "after_retraction:" + check["property"]
        checks.extend(after_checks)
        replay = verify_morphology(report, text=after_text, source_id=source_id, scope=SCOPE)
        add("old_certificate_invalid_after_source_change", structured_failure(replay), replay)
        add("changed_source_changes_occurrence_identity",
            report["readings"][0]["occurrence_id"] != after["readings"][0]["occurrence_id"])
        summaries["after"] = summarize_report(after)
    elif expected.get("must_fail_replay"):
        if kind == "source_identity_transplant":
            results = [verify_morphology(report, text=text, source_id=source_id + "_other", scope=SCOPE)]
        else:
            results = [verify_morphology(changed, text=text, source_id=source_id, scope=SCOPE)
                       for changed in attack_reports(kind, report)]
        add("tampered_certificate_is_structured_failure", all(structured_failure(r) for r in results), results)
    else:
        checks.extend(properties(expected, report))

    # This checks encoding's boundary, not an independent semantic theorem.
    encoded = morphology_number(report)
    add("canonical_report_numeric_roundtrip", decode_morphology(encoded) == report,
        {"bit_length": encoded.bit_length(),
         "encoded_bytes_sha256": sha256(encoded.to_bytes((encoded.bit_length() + 7) // 8, "big")).hexdigest()})
    return {"id": case["id"], "group": case["group"], "passed": all(c["passed"] for c in checks),
            "checks": checks, "observed": summaries}


def run_case(case):
    try:
        return _run_case(case)
    except Exception as error:
        # A reviewer/adapter error is not silently converted into a linguistic
        # result. Preserve it as a failed evaluation contract with its type.
        return {"id": case["id"], "group": case["group"], "passed": False,
                "checks": [{"property": "evaluation_contract_completed", "passed": False,
                            "observed": {"type": type(error).__name__, "message": str(error)}}]}


def documented_boundary(case_result):
    """One narrow, visible coverage debt; no other failed property is allowed."""
    if case_result["id"] not in DOCUMENTED_BOUNDARY_MISSES:
        return False
    failed = [c for c in case_result["checks"] if not c["passed"]]
    if len(failed) != 1 or failed[0]["property"] != "r1:kind":
        return False
    actual = failed[0]["observed"]
    readings = case_result.get("observed", {}).get("before", {}).get("readings", [])
    return (actual["status"] == "DEFER"
            and actual["candidates"] == [actual["expected"]]
            and actual["blocked_by_unparsed_source"] is True
            and bool(readings) and bool(readings[0].get("unparsed")))


def regression_gate(results):
    return all(case["passed"] or documented_boundary(case) for case in results)


def evaluate(version="v2", *, freeze_version="nominal_v1"):
    material = load_material(version)
    before = snapshot()
    freeze = verify_runtime_freeze(before, freeze_version)
    started = time.perf_counter()
    results = [run_case(case) for case in material["cases"]]
    elapsed = time.perf_counter() - started
    after = snapshot()
    require(before == after, "Measured package changed during evaluation; rerun on a stable snapshot")
    groups = {}
    for case in results:
        group = groups.setdefault(case["group"], {"passed": 0, "total": 0})
        group["total"] += 1
        group["passed"] += int(case["passed"])
    return {"evaluator_version": VERSION, "evaluator_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "recorded_utc": datetime.now(timezone.utc).isoformat(),
            "material_version": version, "material_sha256": MATERIAL_SHA256[version],
            "measurement_scope": material["freeze_boundary"],
            "claim_boundary": material["claim_boundary"],
            "runtime_snapshot": before, "frozen_runtime": freeze, "loaded_module_origins": loaded_origins(),
            "execution_seconds_one_run": elapsed,
            "summary": {"passed": sum(r["passed"] for r in results), "total": len(results),
                        "groups": groups, "failed_ids": [r["id"] for r in results if not r["passed"]],
                        "documented_boundary_ids": [r["id"] for r in results if not r["passed"] and documented_boundary(r)],
                        "regression_gate_with_declared_boundaries": regression_gate(results)},
            "cases": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--material", choices=tuple(MATERIAL_SHA256), default="v2")
    parser.add_argument("--freeze-version", choices=tuple(CODE_FREEZES), default="nominal_v1")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--diagnostic", action="store_true",
                        help="Preserve failures in a diagnostic report without using them as a release gate")
    parser.add_argument("--allow-documented-boundaries", action="store_true",
                        help="Permit only the four named conservative kind-approval coverage misses; raw score is unchanged")
    args = parser.parse_args()
    result = evaluate(args.material, freeze_version=args.freeze_version)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"material_version": args.material, **result["summary"]}, ensure_ascii=False, indent=2))
    passed = result["summary"]["passed"] == result["summary"]["total"]
    return 0 if args.diagnostic or passed or (args.allow_documented_boundaries and regression_gate(result["cases"])) else 1


if __name__ == "__main__":
    raise SystemExit(main())
