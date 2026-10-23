#!/usr/bin/env python3
"""Evaluate the pre-implementation word cases without altering their gold.

This is a property adapter over authored, source-justified cases, not another
Arabic parser. Positive lexical witnesses, complete syntactic frames, safety,
and lexical coverage limits are scored separately. A blanket DEFER cannot pass
the positive cases. The implementation and material pins are mandatory.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nabt import NabtError
from nabt.word_reader import (decode_word_reading, read_word_at, read_words,
                              verify_word_reading, word_reading_number)

VERSION = "nabt.words.independent-evaluator.v1.5"
CASES_SHA256 = "38dd236c752b7d2d982eb615aa557c0d4b2328d1e415b6ca23c71d8e8852bc78"
FREEZE_SHA256 = "493626c2bed79ba40a733e7c35995efbbf9d1190139d9e6783fee05a08ad0fc4"
SNAPSHOT_SHA256 = "96d7e5328966d41eaf0cb5fd012e52b0fd48f783ad5d170bd9eac76e3988fef4"
ARCHIVE_SHA256 = "fcd06e9eaa0c5edefed68684a96a1c5e78bb1a5e3a3e227c971458a00cce2d3d"
CODE_FREEZES = {
    "nominal_v1": ("9d9f71eb1b26caac6ea170fe839e7b7f2903eccf827c5bbf7b2c78d3a46a13cd",
                   "c00458629fcd08a6cefb616d0fb1caaec5958996b0532043d0fd1a92d922740a",
                   "6d86c0709c97a89375fc9ff498d1576585c3e432831c7ac17cfc1eb75c2f2724"),
    "derivation_v1": ("5cdea1a66bd92f3f014cc2f14ab2d502f43f630d03977cb111020e3370907eed",
                      "e8e31cdaa1cb56e3700befd4d8fb883e11f83cd684e6cd72b45e133410bf3cac",
                      "fd24793a4fb805425e4bba60219c70a0f1fbb4dda7a89b07d1c6a0ffc6c3b060"),
    "text_morphology_v1": ("b15dfab7ed6166aa5aae236c7c0b22ce48f805a6bc0d8f6c3b6f12bae2b951ee",
                           "82a5d9b283d403bf257a95e5c8a1eb9b2ea300a90ca1a2e881de478bf29f7496",
                           "d1661a0abef5f25d048b675270517e400f83c08a1a0b6b3f3c7c399514f94304"),
    "morphology_v1": ("8449c5c4bf32549c6147de006b0586d41cb4c6f656e2764c63e3437a35b7bffd", "4b5c8f4f7c2bb765791e0a9c94e1be279a1a3ad1e186e6346d77546f23a47d46", "f657df1db06f714789e8bbf64708770a5355b0f9542281798ba43735286a042a"),
    "v1": (FREEZE_SHA256, SNAPSHOT_SHA256, ARCHIVE_SHA256),
    "v2": ("304fddda0276053f8a6404a7d21ca7fb2019e9a0c0aa98b5718b52684efec2da",
           "41ad5f8719d838f3b039633ee69175fcbbceb079e4a786b7d34d2c920821c3ee",
           "fc01f062954a7153138501695953ea6a9cf8613da11ae78887ca6cd52b8674fd"),
    "v3": ("b9ffd279e093b30cadbb4c61a23eb3f0b314ae5ae0da1374907ae8b133333434",
           "33cb00870b810ddfef44d1c9c665c289223faf5164517fb1d0bdc803081a5066",
           "1753f8cc46e7176d013d7a7297b61e5e194e3c628828f83ec66be84f3480c026"),
}
CODE_FREEZE_PATHS = {
    "nominal_v1": ROOT / "evidence/nominal/code_freeze_v1.json",
    "derivation_v1": ROOT / "evidence/derivation/code_freeze_v1.json",
    "text_morphology_v1": ROOT / "evidence/text_morphology/code_freeze_v1.json",
    "morphology_v1": ROOT / "evidence/morphology/code_freeze_v1.json",
    "v1": ROOT / "evidence/words/code_freeze_v1.json",
    "v2": ROOT / "evidence/words/code_freeze_v2.json",
    "v3": ROOT / "evidence/words/code_freeze_v3.json",
}
DOCUMENTED_POSITIVE_MISSES = {"w15", "w16", "w17"}
DOCUMENTED_MISSING_PROPERTIES = {"complete_required_frame", "required_source_bound_role_and_case_bindings"}

# These are explicit interface mappings, not word-specific acceptance rules.
KINDS = {0: "noun", 1: "verb", 2: "particle"}
CASES = {0: "nasb", 1: "raf", 2: "jarr", 3: "jazm"}
ROLES = {"inna_subject": 0, "inna_predicate": 1, "governed_noun": 6, "imperfect": 2}
FRAME_CLASSES = {"inna_two_nouns": 2, "min_noun": 7, "lam_imperfect": 5}
OBLIGATION_ADAPTER = {
    "READING_OR_LEXICAL_SENSE": {"VOCALIZATION_OR_LEXICAL_SELECTION_EVIDENCE", "OPERATOR_READING_EVIDENCE"},
    "LEXICAL_ATTESTATION_OR_COVERAGE": {"LEXICAL_READING_EVIDENCE"},
    "CASE_ROLE_MISMATCH": {"CASE_ROLE_CONFLICT"},
    "INCOMPLETE_FRAME": {"COMPLETE_CONSTITUENT_BOUNDARIES"},
    "FRAME_BOUNDARY_OR_SCOPE": {"COMPLETE_CONSTITUENT_BOUNDARIES", "CONSTRUCTION_READING_EVIDENCE"},
    "CATEGORY_ROLE_MISMATCH": {"LEXICAL_KIND_ROLE_CONFLICT", "IMPERFECT_READING_REQUIRED"},
    "INFLECTION_REALIZATION_OR_FORM": {"LEXICAL_READING_EVIDENCE", "SURFACE_REALIZATION_EVIDENCE", "CASE_ROLE_CONFLICT"},
    "MENTION_USE_OR_FRAME_BOUNDARY": {"MENTION_USE_EVIDENCE", "CONSTRUCTION_READING_EVIDENCE"},
    "SEGMENTATION_OR_LEXICAL_COVERAGE": {"SEGMENTATION_EVIDENCE", "LEXICAL_READING_EVIDENCE"},
    "GOVERNOR_BLOCKER_OR_OUTSIDE_FRAME": {"CONSTRUCTION_READING_EVIDENCE", "LEXICAL_READING_EVIDENCE"},
    "CONFLICTING_MARKS": {"CONFLICTING_MARKS"},
    "INVALID_BYTE_BOUNDARY": {"INVALID_WORD_SPAN"},
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def runtime_source_id(material_identity):
    """Injectively transport labels into the pre-existing SourceBlob ID domain.

    The frozen material uses human labels containing hyphens. No text, case
    expectation, or equality of identities changes. See the recorded first-run
    interface erratum; this mapping applies to every identity, not test words.
    """
    require(type(material_identity) is str and bool(material_identity), "Invalid material identity")
    return "case_" + material_identity.encode("utf-8").hex()


def load_material():
    path = ROOT / "evidence/words/independent_cases_v1.json"
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == CASES_SHA256, "Independent cases differ from their pre-open freeze")
    data = json.loads(raw)
    require(len(data["cases"]) == len({c["id"] for c in data["cases"]}) == 30, "Wrong independent case inventory")
    for source in data["sources"]:
        raw_source = (ROOT / source["git_path"]).read_bytes()
        require(sha256(raw_source).hexdigest() == source["sha256"], "Pinned primary source differs")
        for passage in source["passages"]:
            part = raw_source[passage["byte_start"]:passage["byte_end"]]
            require(sha256(part).hexdigest() == passage["sha256"] and part.decode("utf-8") == passage["text"],
                    "Frozen source passage differs")
    return data


def verify_implementation_freeze(version="nominal_v1"):
    manifest_sha, snapshot_sha, archive_sha = CODE_FREEZES[version]
    manifest_path = CODE_FREEZE_PATHS[version]
    raw = manifest_path.read_bytes()
    require(sha256(raw).hexdigest() == manifest_sha, "Different implementation freeze")
    freeze = json.loads(raw)
    rows = freeze["files"]
    require(len(rows) == len({r["path"] for r in rows}), "Repeated frozen path")
    digest = sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    require(digest == freeze["snapshot_sha256"] == snapshot_sha, "Different implementation inventory")
    actual = {"pyproject.toml"} | {
        str(p.relative_to(ROOT)) for p in (ROOT / "src").rglob("*")
        if p.is_file() and p.suffix in {".py", ".json", ".txt"}
        and "__pycache__" not in p.parts
        and not any(v.endswith((".egg-info", ".dist-info")) for v in p.parts)
    }
    require(actual == {r["path"] for r in rows}, "Authoritative package files added or omitted")
    for row in rows:
        path = (ROOT / row["path"]).resolve()
        require(path.is_relative_to(ROOT), "Frozen path escapes repository")
        content = path.read_bytes()
        require(len(content) == row["bytes"] and sha256(content).hexdigest() == row["sha256"],
                "Implementation changed: " + row["path"])
    archive = manifest_path.parent / freeze["archive_filename"]
    require(sha256(archive.read_bytes()).hexdigest() == freeze["archive_sha256"] == archive_sha,
            "Different implementation archive")
    with tarfile.open(archive, "r:gz") as bundle:
        files = [m for m in bundle.getmembers() if m.isfile()]
        require({m.name for m in files} == actual and len(files) == len(actual), "Archive inventory differs")
        by_name = {r["path"]: r for r in rows}
        for member in files:
            data = bundle.extractfile(member).read()
            require(len(data) == by_name[member.name]["bytes"]
                    and sha256(data).hexdigest() == by_name[member.name]["sha256"], "Archive member differs")
    return {"version": version, "manifest_sha256": manifest_sha, "snapshot_sha256": snapshot_sha,
            "archive_sha256": archive_sha, "file_count": len(rows)}


def loaded_origins():
    result = []
    for name, module in sorted(sys.modules.items()):
        if name != "nabt" and not name.startswith("nabt."):
            continue
        filename = getattr(module, "__file__", None)
        if filename is None:
            continue
        path = Path(filename).resolve()
        expected = (ROOT / "src").joinpath(*name.split("."))
        require(path in {expected.with_suffix(".py"), expected / "__init__.py"},
                "Evaluated module is outside frozen source: " + name)
        result.append({"module": name, "path": str(path.relative_to(ROOT)),
                       "sha256": sha256(path.read_bytes()).hexdigest()})
    require(any(v["module"] == "nabt.word_reader" for v in result), "Reader module was not loaded")
    return result


def parts(report):
    return [p for run in report.get("occurrences", []) for alt in run["alternatives"] for p in alt["parts"]]


def contextual_bindings(report, *, checked_only=False):
    return [b for context in report.get("contexts", [])
            if not checked_only or context["status"] == "CHECKED"
            for alternative in context.get("bindings", []) for b in alternative["words"]]


def obligation_codes(report, error=None):
    found = set()
    if error:
        found.add(error["code"])
    for value in [report, *report.get("occurrences", []), *parts(report), *report.get("contexts", [])]:
        for field in ("obligations", "conflicts", "unresolved_alternative_obligations"):
            found.update(value.get(field, []))
    return found


def independent_structure_checks(report, expected_text, source_id, scope):
    """Check source arithmetic and witness linkage without reparsing Arabic."""
    raw = expected_text.encode("utf-8")
    digest = sha256(raw).hexdigest()
    require(report["raw_text"] == expected_text and report["source_id"] == source_id
            and report["scope"] == scope and report["source_sha256"] == digest, "Source identity differs")

    def span(span_value, surface):
        a, b = span_value["start"], span_value["end"]
        require(type(a) is int and type(b) is int and 0 <= a < b <= len(raw), "Invalid exact byte span")
        require(span_value["source_id"] == source_id and span_value["source_sha256"] == digest, "Foreign source span")
        piece = raw[a:b]
        require(piece.decode("utf-8") == surface and sha256(piece).hexdigest() == span_value["span_sha256"],
                "Byte span does not support surface")

    cursor = 0
    for segment in report["segments"]:
        span(segment["span"], segment["surface"])
        require(segment["span"]["start"] == cursor, "Source partition gap or overlap")
        cursor = segment["span"]["end"]
    require(cursor == len(raw), "Source suffix omitted")
    source_runs = {(s["span"]["start"], s["span"]["end"]): s
                   for s in report["segments"] if s["kind"] in {"written_run", "quotation"}}
    require(len(source_runs) == len(report["occurrences"]), "Occurrence inventory differs")
    identities, readings = set(), {}
    for run in report["occurrences"]:
        key = run["span"]["start"], run["span"]["end"]
        require(key in source_runs and run["surface"] == source_runs[key]["surface"], "Occurrence lacks source segment")
        require(run["occurrence_id"] not in identities, "Distinct occurrences share an identity")
        identities.add(run["occurrence_id"])
        for alternative in run["alternatives"]:
            cursor = key[0]
            for part in alternative["parts"]:
                span(part["span"], part["surface"])
                require(part["span"]["start"] == cursor, "Grammatical segmentation gap or overlap")
                cursor = part["span"]["end"]
                require(part["occurrence_id"] == run["occurrence_id"]
                        and part["segmentation_id"] == alternative["segmentation_id"], "Cross-reading witness splice")
                require(part["actual_case"] is None and part["actual_role"] is None and part["referent"] is None,
                        "Pre-composition witness claims a contextual role or referent")
                require(type(part["kind"]) is int and KINDS.get(part["kind"]) == part["kind_name"], "Unlicensed kind code")
                require(part["reading_id"] not in readings, "Duplicated lexical-reading identity")
                readings[part["reading_id"]] = part
            require(cursor == key[1], "Grammatical segmentation omits source suffix")
    for context in report["contexts"]:
        require(context["semantic_projection"] == "NONE" and context["authority"] == "SYNTAX_ONLY", "Context exceeds syntax authority")
        for alternative in context.get("bindings", []):
            for binding in alternative["words"]:
                analysis = binding["analysis"]
                require(readings.get(analysis["reading_id"]) == analysis, "Context imports a different lexical reading")
                require(binding["context_id"] == context["context_id"] and binding["referent"] is None,
                        "Context binding changes identity or invents reference")
    require(report["facts"] == [] and report["semantic_projection"] == "NONE"
            and report["world_truth"] == "NOT_ESTABLISHED", "Words-only report acquired semantic authority")


def subtype(part, wanted):
    feature = part.get("features", {})
    if wanted in {"past", "imperfect"}:
        return feature.get("tense") == wanted
    if wanted == "pronoun":
        return feature.get("pronoun") is True
    if wanted == "attached_pronoun":
        return feature.get("pronoun") is True and feature.get("attachment") == "suffix"
    return False


def matches_binding(binding, wanted):
    analysis = binding["analysis"]
    return (analysis["surface"] == wanted["surface"]
            and analysis["kind_name"] == wanted["kind"]
            and binding["role"] == ROLES[wanted["role"]]
            and CASES.get(binding["case"]) == wanted["case"]
            and ("lexical_subtype" not in wanted or subtype(analysis, wanted["lexical_subtype"])))


def evaluate_properties(case, report, error, replay):
    expected = case["expected"]
    family = expected["status_family"]
    result = []

    def check(name, condition, detail=None):
        result.append({"property": name, "passed": bool(condition), **({"detail": detail} if detail else {})})

    all_parts = parts(report)
    complete = [c for c in report.get("contexts", []) if c["status"] == "CHECKED"]
    codes = obligation_codes(report, error)
    status = error["status"] if error else report.get("status")
    if family == "LEXICAL_EVIDENCE":
        matches = [p for p in all_parts if p["kind_name"] == expected.get("required_kind")]
        if "required_kind" in expected:
            check("source_licensed_kind_witness", bool(matches))
        if "lexical_subtype" in expected:
            check("source_licensed_subtype", any(subtype(p, expected["lexical_subtype"]) for p in matches))
        if "required_grammatical_segments" in expected:
            wanted = expected["required_grammatical_segments"]
            found = any(len(alt["parts"]) == len(wanted)
                        and all(p["surface"] == w["surface"] and p["kind_name"] == w["kind"]
                                and ("lexical_subtype" not in w or subtype(p, w["lexical_subtype"]))
                                for p, w in zip(alt["parts"], wanted))
                        for run in report.get("occurrences", []) for alt in run["alternatives"])
            check("source_licensed_grammatical_segmentation", found)
        if expected.get("observed_tanwin"):
            check("observed_tanwin_preserved", any(any(ch in p["surface"] for ch in "ًٌٍ") for p in matches))
        if expected.get("reference_may_require_context"):
            check("reference_obligation_separate_from_kind", any("REFERENT_INTERPRETATION_EVIDENCE" in p["obligations"] for p in matches))
        if expected.get("requires_complement_in_context"):
            check("isolated_operator_does_not_fill_complement", not complete and any("ATTACHMENT_AND_ACTIVATION_EVIDENCE" in p["obligations"] for p in matches))
    elif family == "SYNTACTIC_EVIDENCE":
        fitting = [c for c in complete if c.get("class_code") == FRAME_CLASSES[expected["required_frame"]]]
        check("complete_required_frame", bool(fitting), {"runtime_status": status, "obligations": sorted(codes)})
        wanted = expected["required_bindings"]
        found = any(len(alt["words"]) == len(wanted)
                    and all(any(matches_binding(b, w) for b in alt["words"]) for w in wanted)
                    for context in fitting for alt in context["bindings"])
        check("required_source_bound_role_and_case_bindings", found)
        if expected.get("must_not_claim_general_weak_verb_morphology"):
            check("finite_explicit_stem_form_scope", any(p["features"].get("exact_stem_forms_only") is True for p in all_parts))
    elif family == "DEFER":
        check("named_deferral", status == "DEFER")
    elif family == "DEFER_OR_REJECT":
        check("structured_nonacceptance", status in {"DEFER", "REJECT"})
    elif family == "REPLAY_FAILURE":
        check("cross_source_replay_failed", replay is not None and replay.get("valid") is False)

    for missing in expected.get("required_obligation_families", []):
        check("named_obligation:" + missing, bool(codes & OBLIGATION_ADAPTER[missing]), {"observed": sorted(codes)})
    if "required_alternative_kinds" in expected:
        found = {p["kind_name"] for p in all_parts}
        check("preserved_required_kind_alternatives", set(expected["required_alternative_kinds"]) <= found)
    if expected.get("must_not_claim_unique_kind"):
        check("no_premature_unique_kind", len({p["kind_name"] for p in all_parts}) >= 2 and status == "DEFER")
    if expected.get("must_not_claim_complete_frame"):
        check("no_unlicensed_complete_frame", not complete)
    if expected.get("must_not_claim_lexical_attestation"):
        check("unknown_word_not_attested", not all_parts)
    if expected.get("must_not_force_waw_split"):
        check("no_forced_waw_segmentation", not any(p["surface"] in {"و", "وَ"} for p in all_parts))
    if expected.get("must_not_activate_unblocked_inna"):
        check("no_unblocked_inna_activation", not any(c.get("class_code") == 2 and c["status"] == "CHECKED" for c in complete))
    if expected.get("must_not_choose_last_mark"):
        check("conflicting_marks_do_not_select_a_template", not all_parts)
    if expected.get("must_not_infer_particle_from_no_positive_marker"):
        check("absence_of_signs_not_particle_proof", not any(p["kind_name"] == "particle" for p in all_parts))
    if "forbidden_binding" in expected:
        bad = expected["forbidden_binding"]
        check("forbidden_binding_absent", not any(b["analysis"]["surface"] == bad["surface"]
              and CASES.get(b["case"]) == bad["case"]
              and ("kind" not in bad or b["analysis"]["kind_name"] == bad["kind"])
              for b in contextual_bindings(report)))
    if expected.get("forbidden_active_governor_surface"):
        check("quoted_mention_not_activated", not complete)
    if expected.get("must_not_emit_licensed_word"):
        check("invalid_span_not_licensed", error is not None)
    if expected.get("requires_an_orthographic_single_run"):
        check("one_written_run_multiple_grammatical_words", len(report.get("occurrences", [])) == 1)
    if expected.get("referent_established") is False:
        check("no_invented_referent", all(p["referent"] is None for p in all_parts)
              and all(b["referent"] is None for b in contextual_bindings(report)))
    return result


def run_case(case):
    report, error, replay, checks = {}, None, None, []
    source = case["input"]["text"]
    sid = runtime_source_id(case["input"]["source_id"])
    scope = "word-independent-" + case["id"]
    started = time.perf_counter()
    try:
        if case["requested_layer"] == "replay":
            action = case["operation"]
            sid = runtime_source_id(action["original_source_id"])
            report = read_words(action["original_text"], source_id=sid, scope=scope)
            source = action["original_text"]
            replay = verify_word_reading(report, source=action["target_text"], source_id=runtime_source_id(action["target_source_id"]), scope=scope)
        elif "explicit_byte_span" in case:
            interval = case["explicit_byte_span"]
            selection = read_word_at(source, interval["start"], interval["end"], source_id=sid, scope=scope)
            checks.append({"property": "invalid_span_rejected", "passed": False, "detail": selection})
        else:
            report = read_words(source, source_id=sid, scope=scope)
    except NabtError as exc:
        error = exc.as_dict()
    except Exception as exc:
        return {"id": case["id"], "group": case["group"], "passed": False,
                "evaluator_failure": type(exc).__name__ + ": " + str(exc)}
    if report:
        try:
            independent_structure_checks(report, source, sid, scope)
            checks.append({"property": "independent_source_and_authority_checks", "passed": True})
        except (ValueError, KeyError, TypeError) as exc:
            checks.append({"property": "independent_source_and_authority_checks", "passed": False, "detail": str(exc)})
        try:
            number = word_reading_number(report)
            same = decode_word_reading(number) == report
            checks.append({"property": "numeric_roundtrip_replay", "passed": same,
                           "interpretation": "Encoding/replay check only; not a linguistic oracle."})
        except Exception as exc:
            checks.append({"property": "numeric_roundtrip_replay", "passed": False,
                           "detail": type(exc).__name__ + ": " + str(exc)})
    checks.extend(evaluate_properties(case, report, error, replay))
    return {"id": case["id"], "group": case["group"], "requested_layer": case["requested_layer"],
            "input": case["input"], "runtime_source_id": sid,
            "passed": bool(checks) and all(c["passed"] for c in checks),
            "checks": checks, "runtime_error": error, "replay_result": replay, "report": report,
            "elapsed_seconds_single_run": time.perf_counter() - started}


def regression_gate_passes(results):
    """Preserve safety and evidence even in the three documented coverage gaps."""
    for record in results:
        if "evaluator_failure" in record:
            return False
        if record["passed"]:
            continue
        if (record["id"] not in DOCUMENTED_POSITIVE_MISSES
                or record["group"] != "source_attested_positive"
                or record.get("runtime_error") is not None or not record.get("report")):
            return False
        checks = {c["property"]: c["passed"] for c in record["checks"]}
        failed = {name for name, passed in checks.items() if not passed}
        if (not failed or not failed <= DOCUMENTED_MISSING_PROPERTIES
                or checks.get("independent_source_and_authority_checks") is not True
                or checks.get("numeric_roundtrip_replay") is not True):
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--freeze-version", choices=tuple(CODE_FREEZES), default="nominal_v1")
    parser.add_argument("--require-regression-gates", action="store_true",
                        help="Allow only the documented frame-coverage misses w15/w16/w17; never mark them passed")
    args = parser.parse_args()
    try:
        material = load_material()
        freeze = verify_implementation_freeze(args.freeze_version)
        results = [run_case(c) for c in material["cases"]]
        origins = loaded_origins()
        groups = {}
        for group in sorted({r["group"] for r in results}):
            subset = [r for r in results if r["group"] == group]
            groups[group] = {"cases": len(subset), "passed": sum(r["passed"] for r in subset),
                             "failed_ids": [r["id"] for r in subset if not r["passed"]]}
        capability = groups["source_attested_positive"]
        failures = [{"id": r["id"], "group": r["group"],
                     "failed_properties": [c["property"] for c in r.get("checks", []) if not c["passed"]],
                     **({"evaluator_failure": r["evaluator_failure"]} if "evaluator_failure" in r else {})}
                    for r in results if not r["passed"]]
        finding_names = []
        if any(f["group"] == "source_attested_positive" for f in failures):
            finding_names.append("FROZEN_POSITIVE_CAPABILITY_GAP")
        if any(f["group"] != "source_attested_positive" for f in failures):
            finding_names.append("FROZEN_BOUNDARY_OR_SAFETY_GAP")
        regression_passed = regression_gate_passes(results)
        full_coverage_passed = all(r["passed"] for r in results)
        output = {"evaluator_version": VERSION, "utc": datetime.now(timezone.utc).isoformat(),
                  "evaluator_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                  "material_sha256": CASES_SHA256, "implementation_freeze": freeze,
                  "identity_adapter": "case_ followed by UTF-8 hexadecimal; injective over material labels",
                  "loaded_modules": origins, "scope": material["scope_contract"],
                  "claim_limit": material["purpose"], "groups": groups,
                  "summary": {"cases": len(results), "passed": sum(r["passed"] for r in results),
                              "positive_capability_passed": capability["passed"],
                              "positive_capability_cases": capability["cases"],
                              "all_cases_passed": full_coverage_passed,
                              "full_coverage_goal_passed": full_coverage_passed,
                              "release_regression_gates_passed": regression_passed},
                  "gate_contract": {"require_regression_gates": args.require_regression_gates,
                                    "allowed_documented_positive_misses": sorted(DOCUMENTED_POSITIVE_MISSES),
                                    "allowed_missing_properties": sorted(DOCUMENTED_MISSING_PROPERTIES),
                                    "full_coverage_scope": "The 30 frozen cases only, not all Arabic.",
                                    "meaning": "A regression pass preserves the known capability limit; it never changes a failed gold case into a pass."},
                  "named_findings": finding_names, "failures": failures, "results": results}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"output": str(args.output), "summary": output["summary"],
                          "groups": groups, "named_findings": finding_names, "failures": failures},
                         ensure_ascii=False, indent=2))
        passed_gate = regression_passed if args.require_regression_gates else full_coverage_passed
        return 0 if passed_gate else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"evaluator_contract_failure": type(exc).__name__, "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
