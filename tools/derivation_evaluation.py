#!/usr/bin/env python3
"""Evaluate the independently frozen derivation material without feeding gold to readers.

This is an authored, source-informed review set, not an untouched natural corpus.
Construction, parsing, semantic restraint, conditional paradigm availability and
source replay have distinct denominators. Production code never reads the fixture.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
VERSION = "nabt.derivation.independent-evaluation.v1"
MATERIAL_SHA256 = "e2374049ac135a290b4298e4ce0a4eef872a30a5e63fcdbc2c8a638e10059650"
PROTOCOL_SHA256 = "cfee675e121560761a6fbab87abd9f64d8e57d1191e04a8de4570ad4ee900992"
FREEZE_SHA256 = "ec494b27442e90e322c8e8d66a85aec05b924bdeafb0404ab2f37b658c680c5e"
FORMS = ("past", "imperfect", "imperative")
ARABIC_FORMS = dict(zip(FORMS, ("الماضي", "المضارع", "الأمر")))
CATEGORIES = {1: "jamid", 2: "partial", 3: "full"}


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_material():
    folder = ROOT / "evidence/derivation"
    raw = (folder / "independent_cases_v1.json").read_bytes()
    require(sha256(raw).hexdigest() == MATERIAL_SHA256, "Frozen case bytes changed")
    require(sha256((folder / "independent_protocol.md").read_bytes()).hexdigest()
            == PROTOCOL_SHA256, "Frozen protocol bytes changed")
    frozen = (folder / "independent_material_freeze_v1.json").read_bytes()
    require(sha256(frozen).hexdigest() == FREEZE_SHA256, "Material freeze changed")
    for row in json.loads(frozen)["materials"]:
        require(sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"],
                "A frozen supporting material changed: " + row["path"])
    material = json.loads(raw)
    require(len(material["cases"]) == len({c["id"] for c in material["cases"]}) == 96,
            "Frozen case inventory changed")
    return material


def runtime_snapshot():
    paths = {ROOT / "pyproject.toml", Path(__file__).resolve(), ROOT / "tests/test_derivation_review.py"}
    paths.update(p for p in (ROOT / "src").rglob("*") if p.is_file()
                 and p.suffix in {".py", ".json", ".txt"} and "__pycache__" not in p.parts
                 and not any(part.endswith((".egg-info", ".dist-info")) for part in p.parts))
    rows = []
    for path in sorted(paths):
        payload = path.read_bytes()
        rows.append({"path": str(path.relative_to(ROOT)), "bytes": len(payload),
                     "sha256": sha256(payload).hexdigest()})
    return {"snapshot_sha256": sha256(wire(rows)).hexdigest(), "files": rows}


def preserve_snapshot(snapshot, output):
    path = output.with_suffix(".code.tar.gz")
    require(not path.exists(), "Refusing to overwrite a measured code archive")
    with tarfile.open(path, "w:gz") as archive:
        for row in snapshot["files"]:
            payload = (ROOT / row["path"]).read_bytes()
            require(len(payload) == row["bytes"] and sha256(payload).hexdigest() == row["sha256"],
                    "Runtime changed before its measured archive was captured")
            member = tarfile.TarInfo(row["path"])
            member.size, member.mode, member.mtime = len(payload), 0o644, 0
            archive.addfile(member, io.BytesIO(payload))
    return {"filename": path.name, "sha256": sha256(path.read_bytes()).hexdigest()}


def span_checker(report, inputs):
    raw = inputs["text"].encode("utf-8") if isinstance(inputs["text"], str) else inputs["text"]
    require(report["raw_text"].encode("utf-8") == raw, "Raw input was rewritten")
    require(report["source_sha256"] == sha256(raw).hexdigest()
            and report["source_id"] == inputs["source_id"] and report["scope"] == inputs["scope"],
            "Source identity differs")

    def check(span, surface):
        require(type(span["start"]) is int and type(span["end"]) is int,
                "Span offsets are not actual integers")
        require(0 <= span["start"] < span["end"] <= len(raw), "Span bounds are invalid")
        part = raw[span["start"]:span["end"]]
        require(part.decode("utf-8", "strict") == surface, "Span does not contain its surface")
        require(span["source_id"] == inputs["source_id"]
                and span["source_sha256"] == sha256(raw).hexdigest()
                and span["span_sha256"] == sha256(part).hexdigest(), "Span digest/source differs")
    return raw, check


def independent_derivation_checks(report, inputs):
    """Byte arithmetic and authority checks; no inference of Arabic roots or categories."""
    raw, check_span = span_checker(report, inputs)
    cursor, written = 0, []
    for part in report["partition"]:
        check_span(part["span"], part["surface"])
        require(part["span"]["start"] == cursor, "Partition has a gap or overlap")
        cursor = part["span"]["end"]
        if part["kind"] == "written_run":
            written.append((part["span"]["start"], part["span"]["end"]))
    require(cursor == len(raw), "Source suffix disappeared")
    occurrences = report["occurrences"]
    require([(o["span"]["start"], o["span"]["end"]) for o in occurrences
             if o["reading_context"] == "UNQUOTED"] == written,
            "Unquoted occurrence inventory differs from the written partition")
    require(len({o["occurrence_id"] for o in occurrences}) == len(occurrences),
            "Distinct written occurrences merged")
    candidate_ids, previous_end = set(), 0
    for occurrence in occurrences:
        check_span(occurrence["span"], occurrence["surface"])
        require(occurrence["span"]["start"] >= previous_end,
                "Written observations overlap or change source order")
        previous_end = occurrence["span"]["end"]
        index = occurrence["partition_index"]
        require(type(index) is int and 0 <= index < len(report["partition"]),
                "Occurrence has an invalid partition reference")
        container = report["partition"][index]
        if occurrence["reading_context"] == "UNQUOTED":
            require(container["kind"] == "written_run" and container["span"] == occurrence["span"]
                    and occurrence["quotation_span"] is None, "Unquoted occurrence borrowed another segment")
        else:
            require(occurrence["reading_context"] == "MENTION" and container["kind"] == "quotation"
                    and occurrence["quotation_span"] == container["span"],
                    "Mention lacks its original quotation witness")
            require(container["span"]["start"] + len(container["surface"][0].encode("utf-8"))
                    <= occurrence["span"]["start"] < occurrence["span"]["end"]
                    <= container["span"]["end"] - len(container["surface"][-1].encode("utf-8")),
                    "Mention escapes the quoted interior")
        for candidate in occurrence["candidates"]:
            require(candidate["candidate_id"] not in candidate_ids, "Candidate identity was reused")
            candidate_ids.add(candidate["candidate_id"])
            require(candidate["occurrence_id"] == occurrence["occurrence_id"]
                    and candidate["scope"] == inputs["scope"], "Candidate borrowed an occurrence/scope")
            require(candidate["stem"] + candidate["boundary"] == occurrence["surface"]
                    == candidate["surface"], "Candidate does not restore the whole written occurrence")
            check_span(candidate["stem_span"], candidate["stem"])
            require(candidate["stem_span"]["start"] == occurrence["span"]["start"],
                    "Stem silently discarded an initial prefix")
            if candidate["boundary"]:
                check_span(candidate["boundary_span"], candidate["boundary"])
                require(candidate["boundary_span"]["start"] == candidate["stem_span"]["end"]
                        and candidate["boundary_span"]["end"] == occurrence["span"]["end"],
                        "Boundary does not exactly follow the stem")
            else:
                require(candidate["boundary_span"] is None
                        and candidate["stem_span"]["end"] == occurrence["span"]["end"],
                        "Empty boundary lost a source suffix")
            offset, reconstructed, bound = candidate["stem_span"]["start"], "", {}
            for index, alignment in enumerate(candidate["alignment"]):
                check_span(alignment["span"], alignment["surface"])
                require(alignment["pattern_position"] == index and alignment["span"]["start"] == offset,
                        "Pattern alignment has a gap or wrong ordinal")
                offset = alignment["span"]["end"]
                reconstructed += alignment["surface"]
                if alignment["type"] == "radical":
                    ri = alignment["root_index"]
                    require(type(ri) is int and 0 <= ri < len(candidate["root"]), "Invalid radical index")
                    require(candidate["root"][ri] == alignment["surface"], "Radical witness differs")
                    require(ri not in bound or bound[ri] == alignment["surface"],
                            "Repeated radical does not agree")
                    bound[ri] = alignment["surface"]
                else:
                    require(alignment["type"] == "literal" and alignment["literal"] == alignment["surface"],
                            "Literal witness differs")
            require(reconstructed == candidate["stem"] and offset == candidate["stem_span"]["end"],
                    "Alignment does not restore the stem")
            require(set(bound) == set(range(len(candidate["root"]))), "Root has an unwitnessed radical")
    by_id = {o["occurrence_id"]: o for o in occurrences}
    for proposal in report["future_proposals"]:
        marker, target = by_id[proposal["marker_occurrence_id"]], by_id[proposal["target_occurrence_id"]]
        require(proposal["marker_span"] == marker["span"] and proposal["target_span"] == target["span"],
                "Temporal proposal borrowed an occurrence")
        require(marker["reading_context"] == target["reading_context"] == "UNQUOTED",
                "A quoted mention acquired a temporal attachment proposal")
        gap = raw[marker["span"]["end"]:target["span"]["start"]].decode("utf-8", "strict")
        require(marker["surface"] == "سَوْفَ" and gap.isspace()
                and not any(char in gap for char in "\r\n\u2028\u2029"),
                "Temporal proposal crossed a source boundary")
    shape_authority_checks(report)
    return True


def shape_authority_checks(report):
    """A separate semantic-restraint denominator, with no Arabic class gold."""
    for occurrence in report["occurrences"]:
        require(occurrence["actual_role"] is None and occurrence["actual_case"] is None,
                "Shape acquired an actual role/case")
        for name in ("kind", "nominal_semantics", "verb_productivity", "attested_root"):
            require(occurrence["axes"][name]["status"] == "DEFER", "Shape licensed " + name)
        for candidate in occurrence["candidates"]:
            require(candidate["lexical_class_activated"] is False
                    and candidate["actual_role"] is None and candidate["actual_case"] is None
                    and candidate["root_status"] == "FORMAL_CANDIDATE_NOT_ATTESTED",
                    "Structural candidate gained linguistic authority")
    for proposal in report["future_proposals"]:
        require(proposal["future_weight"] is None and proposal["temporal_reading_activated"] is False
                and proposal["actual_tense"] is None and proposal["actual_role"] is None
                and proposal["actual_case"] is None, "Adjacency acquired temporal/grammatical authority")
    require(report["facts"] == [] and report["world_truth"] == "NOT_ESTABLISHED"
            and report["semantic_projection"] == "NONE", "Pattern report emitted semantic/world facts")
    basis = report["recognition_basis"]
    require(basis["content_word_answer_entries_used"] == 0 and basis["given_root_list_used"] is False
            and basis["given_class_used"] is False and basis["unicode_normalization"] == "NONE",
            "Reader used an undeclared answer/normalization input")
    return True


def conditional_models(positive, negative):
    """Independent enumeration of the agreed three-cell model, not another Arabic parser."""
    return [mask for mask in range(1, 8) if mask & positive == positive and not mask & negative]


def independent_paradigm_checks(report, inputs):
    _, check_span = span_checker(report, inputs)
    ids, assertion_ids = set(), set()
    for index, block in enumerate(report["readings"]):
        check_span(block["header"]["span"], block["header"]["surface"])
        require(block["header"]["surface"] == "الفعل «" + block["lexeme"] + "».",
                "Header does not support its lexeme identity")
        require(block["reading_id"] not in ids, "Independent source blocks merged")
        ids.add(block["reading_id"])
        identity = block["identity"]
        require(identity["source_id"] == inputs["source_id"] and identity["scope"] == inputs["scope"]
                and identity["source_sha256"] == report["source_sha256"]
                and identity["header_span"] == block["header"]["span"], "Block identity differs")
        block_end = (report["readings"][index + 1]["header"]["span"]["start"]
                     if index + 1 < len(report["readings"]) else len(report["raw_text"].encode("utf-8")))
        positive = negative = 0
        for assertion in block["assertions"]:
            check_span(assertion["span"], assertion["surface"])
            require(assertion["reading_id"] == block["reading_id"]
                    and block["header"]["span"]["end"] <= assertion["span"]["start"]
                    < assertion["span"]["end"] <= block_end, "Assertion crossed a lexical block")
            require(assertion["assertion_id"] not in assertion_ids, "Assertion identity reused")
            assertion_ids.add(assertion["assertion_id"])
            require(type(assertion["available"]) is bool and assertion["form"] in FORMS,
                    "Assertion is not a typed explicit availability claim")
            bit = 1 << FORMS.index(assertion["form"])
            if assertion["available"]:
                positive |= bit
                form = assertion["attested_form_claim"]
                require(type(form) is str and bool(form), "Empty positive witness")
                expected = ARABIC_FORMS[assertion["form"]] + " مستعمل: «" + form + "»."
            else:
                negative |= bit
                require(assertion["attested_form_claim"] is None, "Negative assertion has an invented form")
                expected = ARABIC_FORMS[assertion["form"]] + " غير مستعمل."
            require(assertion["surface"] == expected, "Assertion fields do not follow their exact source text")
        require(type(block["positive_mask"]) is int and type(block["negative_mask"]) is int
                and block["positive_mask"] == positive and block["negative_mask"] == negative,
                "Availability mask is not induced by the assertions")
        models = conditional_models(positive, negative)
        categories = sorted({CATEGORIES[m.bit_count()] for m in models})
        row = block["conditional_constraint"]
        require(sorted(row["models"]) == models and sorted(row["categories"]) == categories,
                "Finite law result differs from independent model enumeration")
        for clause in block["unparsed"]:
            check_span(clause["span"], clause["surface"])
        if block["unparsed"] or report["unscoped_clauses"]:
            require(block["axis"]["status"] == "DEFER" and block["axis"]["activated"] is False,
                    "An unsupported source clause was ignored to activate a classification")
        else:
            require(sorted(block["axis"]["models"]) == models
                    and sorted(block["axis"]["candidates"]) == categories,
                    "Availability axis differs from its explicit source constraints")
        require(block["actual_role"] is None and block["actual_case"] is None
                and block["nominal_jamid_mushtaq"] == "NOT_CONSUMED",
                "Verb availability acquired a role/case or consumed noun semantics")
    for clause in report["unscoped_clauses"]:
        check_span(clause["span"], clause["surface"])
    require(report["facts"] == [] and report["world_truth"] == "NOT_ESTABLISHED"
            and report["absence_from_text_is_negative_evidence"] is False
            and report["nominal_semantics_consumed"] is False
            and report["content_word_answer_entries_used"] == 0,
            "Source-relative availability gained unsupported factual authority")
    return True


def check_shape_expectations(expect, report):
    for wanted in expect.get("occurrences", []):
        selected = [o for o in report["occurrences"] if o["surface"] == wanted["surface"]]
        require(bool(selected), "Missing expected written occurrence: " + repr(wanted["surface"]))
        candidates = [c for o in selected for c in o["candidates"]]
        for required in wanted.get("candidate_contains", []):
            require(any(all(c.get(k) == v for k, v in required.items()) for c in candidates),
                    "Missing candidate: " + repr(required))
        for forbidden in wanted.get("candidate_excludes", []):
            require(not any(all(c.get(k) == v for k, v in forbidden.items()) for c in candidates),
                    "Forbidden candidate: " + repr(forbidden))
        if wanted.get("no_candidates"):
            require(not candidates, "Unsupported spelling acquired a pattern/root candidate")
    for prefix in expect.get("forbidden_pattern_prefixes", []):
        require(not any(c["pattern_id"].startswith(prefix) for o in report["occurrences"]
                        for c in o["candidates"]), "An undeclared future pattern was introduced")
    # Semantic, lexical and source separation requirements are checked on every
    # case by independent_derivation_checks, including category-gap fixtures.
    return True


def classification_activated(report):
    """Activation of a unique classification, not merely an active inconsistent constraint."""
    return any(b["axis"]["activated"] and b["axis"]["status"] == "LICENSED"
               and len(b["axis"]["candidates"]) == 1 for b in report["readings"])


def check_paradigm_expectations(expect, report):
    if expect.get("activated_classification") is False:
        require(not classification_activated(report), "A classification was activated")
    if expect.get("conflict"):
        require(report["status"] == "CONFLICT", "Contradictory assertions were not reported")
    if expect.get("out_of_domain"):
        require(report["status"] == "OUT_OF_DOMAIN", "Zero available forms did not remain outside domain")
    if expect.get("defer") or expect.get("invalid_or_deferred"):
        require(report["status"] == "DEFER", "Unsupported source syntax was not deferred")
    if expect.get("missing_is_not_absent"):
        require(all(b["positive_mask"] == b["negative_mask"] == 0 for b in report["readings"]),
                "A bare header acquired an availability assertion")
    if expect.get("forbidden_singleton_category"):
        require(not any(b["axis"]["candidates"] == [expect["forbidden_singleton_category"]]
                        for b in report["readings"]), "Missing forms became an asserted absence")
    for wanted in expect.get("blocks", []):
        selected = [b for b in report["readings"] if b["lexeme"] == wanted["lexeme"]]
        require(len(selected) == 1, "Expected one separate lexical block")
        block = selected[0]
        require(set(block["axis"]["candidates"]) == set(wanted["category_candidates"]),
                "Wrong conditional availability categories: " + repr(block["axis"]["candidates"]))
        for key, mask in (("positive", block["positive_mask"]), ("negative", block["negative_mask"]),
                          ("unknown", 7 & ~(block["positive_mask"] | block["negative_mask"]))):
            require({f for i, f in enumerate(FORMS) if mask & (1 << i)} == set(wanted[key]),
                    "Wrong source-relative " + key + " form inventory")
    return True


def run_case(case):
    from nabt.derivation import generate_derivation, read_derivation, verify_derivation
    from nabt.errors import NabtError
    from nabt.verb_paradigm import read_verb_paradigm, verify_verb_paradigm
    checks, observations = [], {}

    def perform(name, callback):
        try:
            callback()
            checks.append({"check": name, "passed": True})
        except (KeyError, IndexError, TypeError, ValueError, UnicodeError) as error:
            checks.append({"check": name, "passed": False, "error": str(error)})

    if "generation_request" in case:
        try:
            generated = generate_derivation(**case["generation_request"])
        except NabtError as error:
            accepted = case["expect"].get("must_reject", False) and error.status in case["expect"]["allowed_error_statuses"]
            checks.append({"check": "generation", "passed": bool(accepted), "error": error.as_dict()})
        else:
            observations["generated"] = generated
            def generated_check():
                require(not case["expect"].get("must_reject"), "Invalid construction input generated a surface")
                require(generated["surface"] == case["expect"]["generated_surface"], "Generated exact surface differs")
                require(generated["root"] == case["generation_request"]["root"]
                        and generated["pattern_id"] == case["generation_request"]["pattern_id"],
                        "Generation operands changed")
                require(generated["attested_word"] is False and generated["attested_root"] is False
                        and generated["semantic_projection"] == "NONE", "Generation became lexical evidence")
            perform("generation", generated_check)

    request_key = "read_request" if "read_request" in case else "paradigm_request" if "paradigm_request" in case else None
    if request_key:
        inputs = {**case[request_key], "source_id": "independent_" + case["id"].lower().replace("-", "_"),
                  "scope": "independent-derivation-v1"}
        reader, verifier, structure, expectations = (
            (read_derivation, verify_derivation, independent_derivation_checks, check_shape_expectations)
            if request_key == "read_request" else
            (read_verb_paradigm, verify_verb_paradigm, independent_paradigm_checks, check_paradigm_expectations))
        try:
            report = reader(**inputs)
        except NabtError as error:
            accepted = error.status in case["expect"].get("allowed_rejections", [])
            checks.append({"check": "reader_outcome", "passed": accepted, "error": error.as_dict()})
        else:
            observations["report_status"] = report["status"]
            observations["report_sha256"] = sha256(wire(report)).hexdigest()
            if "occurrences" in report:
                observations["occurrences"] = [{"surface": o["surface"], "shape_status": o["shape_status"],
                    "candidates": [{k: c[k] for k in ("pattern_id", "root", "stem", "boundary")}
                                   for c in o["candidates"]]} for o in report["occurrences"]]
            else:
                observations["readings"] = [{"lexeme": b["lexeme"], "positive_mask": b["positive_mask"],
                    "negative_mask": b["negative_mask"], "axis": b["axis"]} for b in report["readings"]]
            perform("independent_source_structure", lambda: structure(report, inputs))
            perform("frozen_expectations", lambda: expectations(case["expect"], report))
            if request_key == "read_request":
                perform("semantic_restraint", lambda: shape_authority_checks(report))
            perform("original_source_replay", lambda: require(verifier(report, **inputs)["valid"], "Original source did not replay"))
            if "replacement_text" in case:
                changed = {**inputs, "text": case["replacement_text"]}
                perform("changed_source_rejected", lambda: require(not verifier(report, **changed)["valid"],
                        "Replacement source validated an old report"))
    return {"id": case["id"], "group": case["group"], "mode": case["mode"],
            "passed": bool(checks) and all(c["passed"] for c in checks), "checks": checks, **observations}


def evaluate():
    material = load_material()
    snapshot = runtime_snapshot()
    results = [run_case(case) for case in material["cases"]]
    require(runtime_snapshot() == snapshot, "Runtime changed while evaluation was running")
    def score(rows):
        return {"passed": sum(r["passed"] for r in rows), "total": len(rows)}
    groups = {g: score([r for r in results if r["group"] == g]) for g in sorted({r["group"] for r in results})}
    tasks = {}
    for task, modes in {"parsing": {"derivation_roundtrip", "read_derivation"},
                        "availability": {"read_verb_paradigm"},
                        "source_replay": {"verify_derivation_source_swap", "verify_verb_paradigm_source_swap"}}.items():
        tasks[task] = score([{"passed": all(c["passed"] for c in r["checks"] if c["check"] != "generation")}
                             for r in results if r["mode"] in modes])
    generation = [c for r in results for c in r["checks"] if c["check"] == "generation"]
    tasks["generation"] = score(generation)
    tasks["semantic_restraint"] = score([c for r in results for c in r["checks"]
                                        if c["check"] == "semantic_restraint"])
    return {"schema": VERSION, "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
            "material_sha256": MATERIAL_SHA256, "protocol_sha256": PROTOCOL_SHA256,
            "material_freeze_sha256": FREEZE_SHA256, "code_snapshot": snapshot,
            "scope": material["independence"], "claim_limits": material["common_invariants"],
            "task_score_scope": {"generation": "Exact construction operation only; supplied operands are not discovered roots",
                "parsing": "Reader cases and reader half of paired roundtrips; generation checks excluded",
                "availability": "Controlled-source finite availability cases",
                "source_replay": "Dedicated changed-source cases",
                "semantic_restraint": "Reports returned by shape reading, including the dedicated replay report; malformed rejected inputs have no report and are excluded"},
            "raw_score": score(results), "group_scores": groups, "task_scores": tasks,
            "passed": all(r["passed"] for r in results), "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--capture-code", action="store_true")
    args = parser.parse_args()
    try:
        require(not args.output.exists(), "Refusing to overwrite a measured evaluation result")
        report = evaluate()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.capture_code:
            report["code_archive"] = preserve_snapshot(report["code_snapshot"], args.output)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: report[k] for k in ("schema", "raw_score", "group_scores", "task_scores", "passed")}, indent=2))
        return 0 if report["passed"] else 1
    except (OSError, KeyError, TypeError, ValueError) as error:
        print(json.dumps({"passed": False, "evaluation_error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
