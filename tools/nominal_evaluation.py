#!/usr/bin/env python3
"""Evaluate the frozen, authored nominal/number/weakness review material.

The cases were written before the reviewer opened the new implementation.
Source-assertion extraction, raw cues, conditional operands, phrase requirements
and source-occurrence cardinality have separate denominators. This is not an
untouched natural corpus or a claim of unrestricted Arabic accuracy.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import sys
import tarfile
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
VERSION = "nabt.nominal.independent-evaluation.v1"
MATERIAL_SHA256 = "1c865468207b2238118999f157fccda9aee9f260585f2b3c36ca9b556c3b52b9"
PROTOCOL_SHA256 = "d31c2a612e15f68ada1e7f8377a96998ccb8b3236d9870760492cb64945a9b8a"
FREEZE_SHA256 = "fb8caa81febae39762b42613802391c322ef3f0e1afc5c83472a92b964ff9f62"
TABLE_SHA256 = "0b0218d75329e1b04302ebdf875a4a43db772d4650b3415bc767f2a6a96d07a8"
TRAITS = ("gender", "number", "form", "definiteness")
MANQUS_FLAGS = ("noun", "inflected", "necessary_final_yaa", "preceding_kasra", "final_yaa_unshaddad")

# Independent assertion-witness grammar taken from the agreed pre-freeze
# contract. It checks a reported property against its source bytes; it does not
# provide expected answers to the production reader or reuse its clause table.
ASSERTIONS = {
    "هو اسم.": ("kind", "noun"), "هو فعل.": ("kind", "verb"), "هو حرف.": ("kind", "particle"),
    "هو مذكر.": ("constraint", 0), "هو مؤنث.": ("constraint", 1),
    "يدل على واحد.": ("constraint", 2), "يدل على اثنين أو اثنتين.": ("constraint", 3),
    "يدل على أكثر من اثنين.": ("constraint", 4),
    "هو جمع مذكر سالم.": ("constraint", 5), "هو جمع بألف وتاء زائدتين.": ("constraint", 6),
    "هو جمع بتغيير بناء مفرده.": ("constraint", 7), "هو جمع خارج الأنواع المدعومة.": ("constraint", 8),
    "هو نكرة.": ("constraint", 10),
    "هو علم.": ("definite_cause", "proper_name"), "هو ضمير.": ("definite_cause", "pronoun"),
    "هو اسم إشارة.": ("definite_cause", "demonstrative"), "هو اسم موصول.": ("definite_cause", "relative"),
    "أل فيه للتعريف.": ("definite_cause", "article"),
    "هو مضاف إضافة معنوية إلى معرفة.": ("definite_cause", "semantic_idafa_to_definite"),
    "هو معرب.": ("inflected", True), "هو مبني.": ("inflected", False),
    "آخره ياء لازمة.": ("necessary_final_yaa", True), "ياؤه الأخيرة غير لازمة.": ("necessary_final_yaa", False),
    "ما قبل الياء مكسور.": ("preceding_kasra", True), "ما قبل الياء غير مكسور.": ("preceding_kasra", False),
    "ياؤه الأخيرة غير مشددة.": ("final_yaa_unshaddad", True),
    "ياؤه الأخيرة مشددة.": ("final_yaa_unshaddad", False),
}


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_material():
    folder = ROOT / "evidence/nominal"
    raw = (folder / "independent_cases_v1.json").read_bytes()
    require(sha256(raw).hexdigest() == MATERIAL_SHA256, "Frozen case bytes changed")
    require(sha256((folder / "independent_protocol.md").read_bytes()).hexdigest() == PROTOCOL_SHA256,
            "Frozen protocol changed")
    frozen = (folder / "independent_material_freeze_v1.json").read_bytes()
    require(sha256(frozen).hexdigest() == FREEZE_SHA256, "Material freeze changed")
    for item in json.loads(frozen)["materials"]:
        payload = (ROOT / item["path"]).read_bytes()
        require(len(payload) == item["bytes"] and sha256(payload).hexdigest() == item["sha256"],
                "Frozen supporting material changed: " + item["path"])
    material = json.loads(raw)
    require(len(material["cases"]) == len({c["id"] for c in material["cases"]}) == 184,
            "Frozen case inventory changed")
    return material


def runtime_snapshot():
    paths = {ROOT / "pyproject.toml", Path(__file__).resolve(), ROOT / "tests/test_nominal_review.py"}
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
    require(not path.exists(), "Refusing to overwrite measured code")
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
    raw = inputs["text"].encode("utf-8") if type(inputs["text"]) is str else inputs["text"]
    require(report["raw_text"].encode("utf-8") == raw, "Raw source was rewritten")
    require(report["source_id"] == inputs["source_id"] and report["scope"] == inputs["scope"]
            and report["source_sha256"] == sha256(raw).hexdigest(), "Source identity differs")

    def check(span, surface):
        require(type(span["start"]) is int and type(span["end"]) is int, "Offsets are not strict integers")
        require(0 <= span["start"] < span["end"] <= len(raw), "Witness has invalid bounds")
        part = raw[span["start"]:span["end"]]
        require(part.decode("utf-8", "strict") == surface, "Witness span does not restore its surface")
        require(span["source_id"] == inputs["source_id"] and span["source_sha256"] == sha256(raw).hexdigest()
                and span["span_sha256"] == sha256(part).hexdigest(), "Witness source or digest differs")
    return raw, check


def partition_checks(report, inputs, occurrences):
    raw, check = span_checker(report, inputs)
    cursor = 0
    for part in report["partition"]:
        check(part["span"], part["surface"])
        require(part["span"]["start"] == cursor, "Partition has a gap or overlap")
        cursor = part["span"]["end"]
    require(cursor == len(raw) and report["source_restored"] is True, "Partition lost source bytes")
    ids, previous_end = set(), 0
    for item in sorted(occurrences, key=lambda o: o["span"]["start"]):
        check(item["span"], item["surface"])
        require(item["span"]["start"] >= previous_end, "Written occurrences overlap")
        previous_end = item["span"]["end"]
        require(item["occurrence_id"] not in ids, "Distinct source occurrences merged")
        ids.add(item["occurrence_id"])
        require(item["occurrence_id"] == sha256(wire({"span": item["span"], "scope": inputs["scope"]})).hexdigest(),
                "Occurrence identity does not bind its source span and scope")
        index = item["partition_index"]
        require(type(index) is int and 0 <= index < len(report["partition"]), "Invalid partition reference")
        container = report["partition"][index]
        if item["reading_context"] == "UNQUOTED":
            require(container["kind"] == "written_run" and item["span"] == container["span"]
                    and item["quotation_span"] is None, "Unquoted run borrowed another partition")
        else:
            require(item["reading_context"] == "MENTION" and container["kind"] == "quotation"
                    and item["quotation_span"] == container["span"], "Mention lost its quotation witness")
            require(container["span"]["start"] + len(container["surface"][0].encode("utf-8"))
                    <= item["span"]["start"] < item["span"]["end"]
                    <= container["span"]["end"] - len(container["surface"][-1].encode("utf-8")),
                    "Mention escaped its quoted interior")
    return raw, check


def final_yaa_shadda(surface):
    clusters = []
    for char in surface:
        if unicodedata.combining(char) and clusters:
            clusters[-1][1].add(char)
        else:
            clusters.append((char, set()))
    return bool(clusters and clusters[-1][0] == "ي" and "ّ" in clusters[-1][1])


def independent_manqus_checks(axis):
    positive, negative = axis["positive_mask"], axis["negative_mask"]
    require(type(positive) is int and type(negative) is int and 0 <= positive < 32 and 0 <= negative < 32,
            "Manqus masks are not five-bit strict integers")
    # Independent completion enumeration: only the all-true assignment meets
    # the definition. No table or production model helper is imported.
    completions = [m for m in range(32) if all(not (positive >> i & 1) or (m >> i & 1) for i in range(5))
                   and all(not (negative >> i & 1) or not (m >> i & 1) for i in range(5))]
    values = sorted({m == 31 for m in completions})
    if axis["status"] in {"LICENSED", "CONFLICT"}:
        require(axis["candidates"] == values, "Manqus result differs from witnessed Boolean completions")
    require(axis["root_weakness_consumed"] is False, "A weak root supplied nominal ending premises")
    if axis["status"] == "LICENSED" and axis["candidates"] == [True]:
        require(positive == 31 and negative == 0, "Positive manqus lacks one of five independent premises")


def weak_profile_checks(profile, root):
    require(profile["root"] == root, "Weak-root operand changed")
    expected_positions = [i for i, char in enumerate(root) if char in "وي"]
    require(profile["weak_positions"] == expected_positions, "Weak positions do not match supplied radicals")
    require(profile["attested_root"] is False and profile["nominal_manqus"] is None
            and profile["surface_realization"] is None, "Root positions acquired lexical or surface authority")


def semantic_restraint(report):
    def visit(value):
        if type(value) is list:
            for child in value:
                visit(child)
        elif type(value) is dict:
            for name in ("actual_case", "actual_role", "world_cardinality", "ordinal"):
                if name in value:
                    require(value[name] is None, "Report acquired " + name)
            if "attested_root" in value:
                require(value["attested_root"] is False, "A supplied/candidate root became attested")
            if "world_truth" in value:
                require(value["world_truth"] == "NOT_ESTABLISHED", "Source assertion became world truth")
            if "facts" in value:
                require(value["facts"] == [], "Conditional report emitted world facts")
            for child in value.values():
                visit(child)
    visit(report)
    return True


def independent_fact_checks(report, inputs):
    raw, check = span_checker(report, inputs)
    require(report["table_sha256"] == TABLE_SHA256, "Fact report names another installed law")
    readings = report["readings"]
    by_id = {b["reading_id"]: b for b in readings}
    require(len(by_id) == len(readings), "Independent source readings merged")
    covered_lines = []
    for outside in report["unscoped_clauses"]:
        check(outside["span"], outside["surface"])
        covered_lines.append((outside["span"]["start"], outside["span"]["end"]))
    support_ids = set()
    for index, block in enumerate(readings):
        header = block["header"]
        check(header["span"], header["surface"])
        require(header["surface"] == "قراءة «" + block["reading_id"] + "» للفظ «" + block["lexeme"] + "»:",
                "Header does not support its reading/lexeme identity")
        check(block["lexeme_span"], block["lexeme"])
        require(header["span"]["start"] < block["lexeme_span"]["start"] < block["lexeme_span"]["end"] < header["span"]["end"],
                "Lexeme escaped its own header")
        covered_lines.append((header["span"]["start"], header["span"]["end"]))
        end = readings[index + 1]["header"]["span"]["start"] if index + 1 < len(readings) else len(raw)
        for prop in block["properties"]:
            require(prop["reading_id"] == block["reading_id"], "Property borrowed another reading identity")
            require(prop["support_id"] == sha256(wire({k: v for k, v in prop.items() if k != "support_id"})).hexdigest(),
                    "Property digest differs")
            require(prop["support_id"] not in support_ids, "One witness was duplicated across source readings")
            support_ids.add(prop["support_id"])
            if prop["basis"] == "OBSERVED_FINAL_YAA_SHADDA":
                require(prop["property"] == "final_yaa_unshaddad" and prop["value"] is False
                        and prop["span"] == block["lexeme_span"] and final_yaa_shadda(block["lexeme"]),
                        "Geminated final ya has no written witness")
                continue
            require(prop["basis"] == "EXPLICIT_SOURCE_PREMISE", "Unknown property authority")
            check(prop["span"], prop["surface"])
            require(header["span"]["end"] <= prop["span"]["start"] < prop["span"]["end"] <= end,
                    "Property crossed its source block")
            expected = ASSERTIONS.get(prop["surface"])
            for prefix, name in (("جذره", "root"), ("مفرده القراءة", "singular_reading")):
                match = re.fullmatch(prefix + r" «([^«»]+)»\.", prop["surface"])
                if match:
                    expected = (name, match[1])
            require(expected is not None and expected == (prop["property"], prop["value"]),
                    "Reported property differs from its exact source assertion")
            covered_lines.append((prop["span"]["start"], prop["span"]["end"]))
        for item in block["unparsed"]:
            check(item["span"], item["surface"])
            require(header["span"]["end"] <= item["span"]["start"] < item["span"]["end"] <= end,
                    "Unparsed qualification crossed its block")
            covered_lines.append((item["span"]["start"], item["span"]["end"]))
        if block["unparsed"] or report["unscoped_clauses"]:
            require(block["blocked"] is True and not any(block["axes"][a]["activated"] for a in TRAITS),
                    "Unsupported qualification was silently discarded")
        independent_manqus_checks(block["manqus"])
        for root in block["weak_roots"]:
            prop = next((p for p in block["properties"] if p["support_id"] == root["support_id"]), None)
            require(prop is not None and prop["property"] == "root", "Root classification has no source premise")
            weak_profile_checks(root, prop["value"])
        for link in block["singular_links"]:
            require(link["source_id"] == inputs["source_id"] and link["scope"] == inputs["scope"]
                    and link["source_sha256"] == report["source_sha256"], "Origin link crossed source/scope")
            prop = next((p for p in block["properties"] if p["support_id"] == link["support_id"]), None)
            require(prop is not None and prop["property"] == "singular_reading"
                    and prop["value"] == link["target_reading_id"], "Origin link lacks its exact source assertion")
            if link["status"] == "LICENSED":
                target = by_id.get(link["target_reading_id"])
                require(target is not None and target is not block and not block["blocked"] and not block["conflict"]
                        and not target["blocked"] and not target["conflict"], "Origin used a missing/blocked/conflicting base")
                require(target["kind"]["status"] == target["axes"]["number"]["status"] == target["axes"]["gender"]["status"] == "LICENSED"
                        and target["kind"]["candidates"] == ["noun"] and target["axes"]["number"]["candidates"] == ["singular"]
                        and target["axes"]["gender"]["candidates"] == [link["singular_gender"]],
                        "Origin borrowed gender without a licensed singular noun")
    expected_lines, offset = [], 0
    for line in raw.splitlines(keepends=True):
        text = line.decode("utf-8")
        if text.strip():
            start = offset + len(text[:len(text) - len(text.lstrip())].encode("utf-8"))
            expected_lines.append((start, start + len(text.strip().encode("utf-8"))))
        offset += len(line)
    require(sorted(covered_lines) == expected_lines, "A nonempty source line disappeared or was duplicated")
    semantic_restraint(report)
    return True


def independent_nominal_checks(report, inputs):
    raw, check = partition_checks(report, inputs, report["occurrences"])
    require(report["table_sha256"] == TABLE_SHA256 and report["unicode_normalization"] == "NONE",
            "Nominal report changed law/Unicode profile")
    require(report["content_word_answer_entries_used"] == 0, "Raw reader used content-word answers")
    lexical = report["lexical_report"]
    if inputs.get("lexical_text") is None:
        require(lexical is None and report["lexical_raw_text"] is None, "Reader invented a lexical source")
    else:
        require(lexical is not None and report["lexical_raw_text"] == inputs["lexical_text"], "Lexical source was lost or rewritten")
        independent_fact_checks(lexical, {"text": inputs["lexical_text"], "source_id": inputs["lexical_source_id"], "scope": inputs["scope"]})
    lexical_index = {} if lexical is None else {b["reading_id"]: b for b in lexical["readings"]}
    ids = set()
    for occurrence in report["occurrences"]:
        expected_ids = {b["reading_id"] for b in lexical_index.values() if b["lexeme"] == occurrence["surface"]}
        matched_ids = {r["lexical_reading_id"] for r in occurrence["readings"] if r["lexical_reading_id"] is not None}
        require(matched_ids == expected_ids, "An exact lexical reading disappeared or an inexact one was linked")
        for reading in occurrence["readings"]:
            require(reading["reading_id"] not in ids, "Reading identity was reused across occurrences")
            ids.add(reading["reading_id"])
            identity = reading["identity"]
            require(identity["source_id"] == inputs["source_id"] and identity["source_sha256"] == sha256(raw).hexdigest()
                    and identity["scope"] == inputs["scope"] and identity["occurrence_id"] == occurrence["occurrence_id"]
                    and identity["span"] == occurrence["span"], "Reading borrowed source, scope or occurrence authority")
            require(reading["reading_id"] == sha256(wire(identity)).hexdigest(), "Reading digest differs")
            for observation in reading["observations"]:
                check(observation["span"], observation["surface"])
                require(occurrence["span"]["start"] <= observation["span"]["start"] < observation["span"]["end"] <= occurrence["span"]["end"],
                        "Raw observation crossed an occurrence boundary")
                require(observation["authority"] == "OBSERVATION_ONLY", "Raw cue acquired lexical authority")
            link = reading["lexical_source_link"]
            props = []
            if link is not None:
                block = lexical_index.get(link["reading_id"])
                require(block is not None and block["lexeme"] == occurrence["surface"], "Lexical match is not exact UTF-8")
                require(link["source_id"] == lexical["source_id"] and link["source_sha256"] == lexical["source_sha256"]
                        and link["scope"] == inputs["scope"] and link["lexeme_span"] == block["lexeme_span"]
                        and link["match"] == "EXACT_UTF8_SURFACE", "Lexical link borrowed another source witness")
                if not block["blocked"] and not block["conflict"] and not reading["blockers"]:
                    props = block["properties"]
            receipt = reading["receipt"]
            require(receipt["identity"] == identity and receipt["reading_id"] == reading["reading_id"], "Receipt crossed reading identity")
            require(receipt["receipt_id"] == sha256(wire({k: v for k, v in receipt.items() if k != "receipt_id"})).hexdigest(),
                    "Receipt digest differs")
            require(all(type(f) is bool for f in receipt["flags"]) and len(receipt["flags"]) == 7,
                    "Receipt flags are not seven booleans")
            require(receipt["activated"] is (all(receipt["flags"][:5]) and not receipt["flags"][5] and receipt["flags"][6]),
                    "Receipt activation violates its premise conjunction")
            independent_manqus_checks(reading["manqus"])
            if reading["manqus"]["status"] == "LICENSED" and reading["manqus"]["candidates"] == [True]:
                require(reading["kind"]["status"] == "LICENSED" and reading["kind"]["candidates"] == ["noun"],
                        "Positive manqus lacks a noun witness")
                require(all(any(p["property"] == flag and p["value"] is True for p in props) for flag in MANQUS_FLAGS[1:]),
                        "Positive manqus filled a missing descriptive premise")
                require(not final_yaa_shadda(occurrence["surface"]), "Geminated final ya became positive manqus")
            for profile in reading["weak_roots"]:
                require(any(p["property"] == "root" and p["value"] == profile["root"] and p["support_id"] == profile["support_id"] for p in props),
                        "Lexical weak-root classification has no linked premise")
                weak_profile_checks(profile, profile["root"])
            require(reading["semantic_jamid_mushtaq"] == "NOT_CONSUMED", "Nominal traits became derivational semantics")
        for candidate in occurrence.get("weak_root_candidates", []):
            require(candidate["status"] == "CANDIDATE", "Shape-derived root became an established operand")
            weak_profile_checks(candidate, candidate["root"])
            bound = {}
            for piece in candidate["root_alignment"]:
                check(piece["span"], piece["surface"])
                require(occurrence["span"]["start"] <= piece["span"]["start"] < piece["span"]["end"] <= occurrence["span"]["end"],
                        "Root candidate alignment crossed an occurrence")
                if piece["type"] == "radical":
                    slot = piece["root_index"]
                    require(type(slot) is int and 0 <= slot < 3 and candidate["root"][slot] == piece["surface"],
                            "Weak-root candidate lacks a radical witness")
                    require(slot not in bound or bound[slot] == piece["surface"], "Repeated radical slot disagrees")
                    bound[slot] = piece["surface"]
            require(set(bound) == {0, 1, 2}, "Weak-root candidate omitted a radical slot")
    semantic_restraint(report)
    return True


def independent_count_checks(report, inputs):
    items = report["units"] + report["excluded_runs"]
    partition_checks(report, inputs, items)
    require(type(report["count"]) is int and report["count"] == len({u["occurrence_id"] for u in report["units"]})
            == len(report["units"]), "Count is not distinct witnessed occurrence cardinality")
    require(report["unit_ids_unique"] is True and report["grammatical_number"] is None,
            "Source cardinality became grammatical number")
    semantic_restraint(report)
    return True


def qualified_origin(alternative):
    return alternative["singular_origin"]["basis"] in {"THIS_LICENSED_SINGULAR_READING", "EXPLICIT_SINGULAR_ORIGIN_LINK"}


def independent_phrase_checks(report, inputs):
    span_checker(report, inputs)
    nominal = report["nominal_report"]
    independent_nominal_checks(nominal, inputs)
    require(report["construction_truth"] == "NOT_ESTABLISHED", "Bounded feature comparison became a complete parse")
    numeral = report["numeral"]
    if numeral is not None:
        _, check = span_checker(report, inputs)
        for part in numeral["parts"]:
            check(part["span"], part["surface"])
        if numeral.get("basis") == "EXACT_DECIMAL_DIGITS":
            require(numeral["unit_gender"] is None and numeral["ten_gender"] is None,
                    "Digit string supplied observed grammatical gender")
    by_id = {o["occurrence_id"]: o for o in nominal["occurrences"]}
    for alternative in report["alternatives"]:
        require(report["counted_occurrence_id"] in by_id, "Count relation lacks its counted occurrence")
        occurrence = by_id[report["counted_occurrence_id"]]
        reading = next((r for r in occurrence["readings"] if r["reading_id"] == alternative["reading_id"]), None)
        require(reading is not None and reading["lexical_reading_id"] == alternative["lexical_reading_id"],
                "Count relation borrowed another reading")
        origin = alternative["singular_origin"]
        if origin["basis"] == "EXPLICIT_SINGULAR_ORIGIN_LINK":
            require(any(link["status"] == "LICENSED" and all(link[k] == origin[k] for k in link)
                        for link in reading["singular_links"]), "Counted gender borrowed an unlicensed base link")
        elif origin["basis"] == "THIS_LICENSED_SINGULAR_READING":
            require(origin["reading_id"] == reading["reading_id"] and reading["kind"]["candidates"] == ["noun"]
                    and reading["axes"]["number"]["status"] == "LICENSED" and reading["axes"]["number"]["candidates"] == ["singular"]
                    and reading["axes"]["gender"]["status"] == "LICENSED"
                    and reading["axes"]["gender"]["candidates"] == [origin["singular_gender"]],
                    "Counted gender lacks a licensed singular reading")
        else:
            require(origin["basis"] == "UNRESOLVED_CONDITIONAL_PARAMETER"
                    and "SINGULAR_GENDER_WITNESS" in alternative["missing"], "Unresolved gender acquired source authority")
        rule = alternative["rule"]
        require(rule["quantity"] == numeral["value"] and rule["singular_gender"] == origin["singular_gender"],
                "Rule changed its cardinal/gender operands")
        for name in ("unit_gender", "ten_gender"):
            check = alternative["checks"][name]
            require(check["observed"] == numeral[name] and check["expected"] == rule[name],
                    "Gender comparison confused observed and required traits")
            if numeral.get("basis") == "EXACT_DECIMAL_DIGITS":
                require(check["status"] in {"NOT_OBSERVED", "UNCONSTRAINED"}, "Digit gender was marked checked")
        require(alternative["checks"]["counted_case"]["observed"] is None,
                "A case requirement was reported as observed actual case")
    semantic_restraint(report)
    return True


def axis(reading, name):
    return reading["kind"] if name == "kind" else reading["axes"][name]


def check_reading_expectations(expect, readings):
    require(bool(readings), "No reading can satisfy the selected expectation")
    handled = {"surface", "reading_id"}
    if "axes" in expect:
        handled.add("axes")
        for name, expected in expect["axes"].items():
            actual = sorted({v for r in readings for v in axis(r, name)["candidates"]})
            require(actual == sorted(expected), name + " candidates differ: " + repr(actual))
            if len(expected) == 1:
                require(any(axis(r, name)["status"] == "LICENSED" and axis(r, name)["candidates"] == expected for r in readings),
                        "Required positive " + name + " was only deferred")
    if "forbid_licensed_axes" in expect:
        handled.add("forbid_licensed_axes")
        for name in expect["forbid_licensed_axes"]:
            require(all(axis(r, name)["status"] != "LICENSED" for r in readings), "Raw cue licensed " + name)
    if "manqus" in expect:
        handled.add("manqus")
        values = sorted({v for r in readings for v in r["manqus"]["candidates"]})
        require(values == expect["manqus"], "Manqus candidates differ: " + repr(values))
        if len(expect["manqus"]) == 1:
            require(any(r["manqus"]["status"] == "LICENSED" and r["manqus"]["candidates"] == expect["manqus"] for r in readings),
                    "Required manqus conclusion was only deferred")
    for flag in ("manqus_unlicensed", "manqus_not_true", "has_conflict", "no_closed_pronoun_license", "preserve_gender_ambiguity"):
        if flag not in expect:
            continue
        handled.add(flag)
        if flag == "manqus_unlicensed":
            require(all(r["manqus"]["status"] != "LICENSED" for r in readings), "Incomplete manqus premises were licensed")
        elif flag == "manqus_not_true":
            require(not any(r["manqus"]["status"] == "LICENSED" and r["manqus"]["candidates"] == [True] for r in readings),
                    "Unwitnessed positive manqus conclusion")
        elif flag == "has_conflict":
            require(any(r["status"] == "CONFLICT" or r["manqus"]["status"] == "CONFLICT" for r in readings), "Contradiction disappeared")
        elif flag == "no_closed_pronoun_license":
            require(not any(r["pronoun_candidates"] and r["kind"]["status"] == "LICENSED" for r in readings),
                    "Unsupported spelling acquired a closed-pronoun reading")
        else:
            values = {v for r in readings for v in r["axes"]["gender"]["candidates"]}
            require((len(values) > 1) is expect[flag], "Pronoun gender ambiguity differs")
    if "lexical_matches" in expect:
        handled.add("lexical_matches")
        require(sum(r["lexical_source_link"] is not None for r in readings) == expect["lexical_matches"], "Inexact lexical match was accepted")
    if "weak_profiles" in expect:
        handled.add("weak_profiles")
        actual = {(p["root"], p["class"], tuple(i + 1 for i in p["weak_positions"])) for r in readings for p in r["weak_roots"]}
        require(all((p["root"], p["class"], tuple(p["positions_one_based"])) in actual for p in expect["weak_profiles"]),
                "Explicit source root classification differs")
    require(set(expect) <= handled, "Unhandled nested expectation: " + repr(set(expect) - handled))


def check_nominal_expectations(expect, report, *, pronoun_reading=False):
    handled = set()
    if "occurrences" in expect:
        handled.add("occurrences")
        for wanted in expect["occurrences"]:
            matching = [o for o in report["occurrences"] if o["surface"] == wanted["surface"]]
            require(len(matching) == 1, "Expected written occurrence is missing or ambiguous")
            readings = matching[0]["readings"]
            if pronoun_reading:
                readings = [r for r in readings if r["pronoun_candidates"]]
            check_reading_expectations(wanted, readings)
    if "readings" in expect:
        handled.add("readings")
        for wanted in expect["readings"]:
            readings = [r for r in report["readings"] if r["reading_id"] == wanted["reading_id"]]
            require(len(readings) == 1, "Expected source reading was lost")
            if "surface" in wanted:
                require(readings[0]["lexeme"] == wanted["surface"], "Source reading changed its lexical surface")
            check_reading_expectations(wanted, readings)
    readings = report.get("readings", [r for o in report.get("occurrences", []) for r in o["readings"]])
    for flag in ("has_conflict", "no_nominal_classification", "defer", "not_conflict_across_readings", "no_attested_root"):
        if flag not in expect:
            continue
        handled.add(flag)
        if flag == "has_conflict":
            require(any(r["status"] == "CONFLICT" for r in readings), "Expected source contradiction disappeared")
        elif flag == "no_nominal_classification":
            require(not any(r["axes"][name]["activated"] or r["axes"][name]["status"] == "LICENSED" for r in readings for name in TRAITS),
                    "Insufficient/unsupported source activated nominal classification")
        elif flag == "defer":
            require(report["status"] == "DEFER", "Unsupported source was not deferred")
        elif flag == "not_conflict_across_readings":
            require(report["status"] != "CONFLICT" and all(r["status"] != "CONFLICT" for r in readings),
                    "Alternative source readings were conflated into one contradiction")
        else:
            require(not any(p["attested_root"] for r in readings for p in r["weak_roots"]), "Shape acquired an attested root")
    if "preserve_reading_ids" in expect:
        handled.add("preserve_reading_ids")
        require(set(expect["preserve_reading_ids"]) <= {r["reading_id"] for r in readings}, "An alternative source reading disappeared")
    if "base_links" in expect:
        handled.add("base_links")
        for wanted in expect["base_links"]:
            block = next((r for r in readings if r["reading_id"] == wanted["plural_id"]), None)
            require(block is not None, "Plural source reading disappeared")
            links = [link for link in block["singular_links"] if "base_id" not in wanted or link["target_reading_id"] == wanted["base_id"]]
            licensed = [link for link in links if link["status"] == "LICENSED"]
            require(bool(licensed) is wanted["licensed"], "Singular-origin authority differs")
            if "base_gender" in wanted:
                require({link["singular_gender"] for link in licensed} == {wanted["base_gender"]}, "Base gender differs")
    require(set(expect) == handled, "Unhandled nominal expectation: " + repr(set(expect) - handled))


def check_rule_expectations(expect, report):
    require(not expect.get("must_reject") and not expect.get("no_supported_rule"), "Invalid/out-of-domain operand returned a supported rule")
    mapping = {"required_case": "counted_case"}
    for name, wanted in expect.items():
        require(name in {"counted_number", "required_case", "unit_gender", "ten_gender", "actual_case", "actual_role"},
                "Unhandled cardinal expectation: " + name)
        require(report[mapping.get(name, name)] == wanted, "Cardinal requirement differs: " + name)


def check_weak_expectations(expect, report):
    require(not expect.get("must_reject"), "Invalid root operand returned a classification")
    for name, wanted in expect.items():
        if name == "positions_one_based":
            require([i + 1 for i in report["weak_positions"]] == wanted, "Root weak positions differ")
        else:
            require(name in {"root", "class", "attested_root"}, "Unhandled root expectation: " + name)
            require(report[name] == wanted, "Root expectation differs: " + name)


def check_count_expectations(expect, report):
    for name, wanted in expect.items():
        if name == "count":
            require(type(report["count"]) is int and report["count"] == wanted, "Written occurrence count differs")
        elif name == "contexts_in_order":
            require([u["reading_context"] for u in report["units"]] == wanted, "Mention/use contexts differ")
        elif name == "distinct_occurrence_ids":
            require((len({u["occurrence_id"] for u in report["units"]}) == len(report["units"])) is wanted, "Occurrence identities are not distinct")
        elif name == "world_count":
            require(report["world_cardinality"] is wanted, "Written count became world-object count")
        else:
            raise ValueError("Unhandled count expectation: " + name)


def check_phrase_expectations(expect, report):
    alternatives = report["alternatives"]
    qualified = [a for a in alternatives if qualified_origin(a)]
    selected = qualified
    if "singular_gender" in expect:
        require(qualified and {a["singular_origin"]["singular_gender"] for a in qualified} == {expect["singular_gender"]},
                "Counted noun lacks the required licensed singular gender")
    for name, wanted in expect.items():
        if name == "singular_gender":
            continue
        if name == "value":
            require(report["numeral"] is not None and type(report["numeral"].get("value")) is int and report["numeral"]["value"] == wanted,
                    "Cardinal value differs")
        elif name == "counted_surface":
            counted = next((o for o in report["nominal_report"]["occurrences"] if o["occurrence_id"] == report["counted_occurrence_id"]), None)
            require(counted is not None and counted["surface"] == wanted, "Count relation changed the counted occurrence")
        elif name in {"counted_number_required", "required_case", "unit_gender_required"}:
            key = {"counted_number_required": "counted_number", "required_case": "counted_case", "unit_gender_required": "unit_gender"}[name]
            require(selected and {a["rule"][key] for a in selected} == {wanted}, "Expected relation requirement differs: " + name)
        elif name == "digit_gender_not_observed":
            require(report["numeral"]["unit_gender"] is None and report["numeral"]["ten_gender"] is None
                    and all(a["checks"][g]["status"] in {"NOT_OBSERVED", "UNCONSTRAINED"} for a in alternatives for g in ("unit_gender", "ten_gender")),
                    "Digits provided checked observed gender")
        elif name == "gender_compatible":
            require(selected, "No qualified singular origin for a gender check")
            statuses = [a["checks"]["unit_gender"]["status"] for a in selected]
            require(all(s == ("MATCH" if wanted else "CONFLICT") for s in statuses), "Observed numeral gender compatibility differs")
        elif name == "no_licensed_singular_gender":
            require(not qualified, "Missing singular-base gender was silently supplied")
        elif name == "no_source_qualified_gender_check":
            require(not any(qualified_origin(a) and any(a["checks"][g]["status"] in {"MATCH", "CONFLICT"} for g in ("unit_gender", "ten_gender")) for a in alternatives),
                    "Conditional gender parameter became a source-qualified comparison")
        elif name == "no_complete_supported_relation":
            require(not any(qualified_origin(a) and not a["missing"] and not report["missing"] for a in alternatives),
                    "Unsupported phrase was accepted by discarding text")
        else:
            raise ValueError("Unhandled phrase expectation: " + name)


def inputs_for(case):
    inputs = dict(case["request"])
    if case["api"] not in {"number_rule", "weak_root_profile"}:
        inputs.update(source_id="independent_" + case["id"].lower().replace("-", "_"), scope="independent_nominal_v1")
        if case["api"] in {"read_nominal", "verify_nominal", "read_count_phrase"}:
            inputs["lexical_source_id"] = "independent_nominal_lexicon"
    return inputs


def report_observation(report):
    result = {"report_status": report.get("status"), "report_sha256": sha256(wire(report)).hexdigest()}
    if "occurrences" in report:
        result["occurrences"] = [{"surface": o["surface"], "context": o["reading_context"], "readings": [
            {"lexical_reading_id": r["lexical_reading_id"], "status": r["status"], "kind": r["kind"],
             "axes": r["axes"], "manqus": r["manqus"]} for r in o["readings"]]} for o in report["occurrences"]]
    elif "readings" in report:
        result["readings"] = [{k: r[k] for k in ("reading_id", "lexeme", "status", "kind", "axes", "manqus", "singular_links")} for r in report["readings"]]
    elif "alternatives" in report:
        result["numeral"] = report["numeral"]
        result["alternatives"] = report["alternatives"]
        result["missing"] = report["missing"]
    elif "units" in report:
        result["count"] = report["count"]
        result["units"] = [{k: u[k] for k in ("surface", "reading_context", "occurrence_id", "span")} for u in report["units"]]
    else:
        result["result"] = report
    return result


def run_case(case):
    from nabt import nominal
    from nabt.counting import verify_count_phrase, verify_source_count
    from nabt.errors import NabtError
    checks, observations = [], {}

    def perform(name, callback):
        try:
            callback()
            checks.append({"check": name, "passed": True})
        except (KeyError, IndexError, TypeError, ValueError, UnicodeError, StopIteration) as error:
            checks.append({"check": name, "passed": False, "error": type(error).__name__ + ": " + str(error)})

    api, inputs = case["api"], inputs_for(case)
    reader = getattr(nominal, "read_nominal" if api == "verify_nominal" else api)
    try:
        report = reader(**inputs)
    except NabtError as error:
        expect = case["expect"]
        accepted = (expect.get("must_reject") is True and error.status == "REJECT") or (
            expect.get("no_supported_rule") is True and error.status in {"REJECT", "DEFER"}) or (
            expect.get("no_complete_supported_relation") is True and error.status in {"REJECT", "DEFER"})
        checks.append({"check": "reader_outcome", "passed": accepted, "error": error.as_dict()})
    except (KeyError, IndexError, TypeError, ValueError, UnicodeError, StopIteration) as error:
        checks.append({"check": "reader_outcome", "passed": False, "error": type(error).__name__ + ": " + str(error)})
    else:
        observations = report_observation(report)
        if api == "number_rule":
            perform("frozen_expectations", lambda: check_rule_expectations(case["expect"], report))
        elif api == "weak_root_profile":
            perform("independent_operand_structure", lambda: weak_profile_checks(report, inputs["root"]))
            perform("frozen_expectations", lambda: check_weak_expectations(case["expect"], report))
        else:
            structures = {"read_nominal": independent_nominal_checks, "verify_nominal": independent_nominal_checks,
                "read_nominal_facts": independent_fact_checks, "count_source_units": independent_count_checks,
                "read_count_phrase": independent_phrase_checks}
            verifiers = {"read_nominal": nominal.verify_nominal, "verify_nominal": nominal.verify_nominal,
                "read_nominal_facts": nominal.verify_nominal_facts, "count_source_units": verify_source_count,
                "read_count_phrase": verify_count_phrase}
            perform("independent_source_structure", lambda: structures[api](report, inputs))
            if api == "verify_nominal":
                require(set(case["expect"]) == {"original_valid", "replacement_valid"}, "Unhandled replay expectation")
                perform("frozen_original_replay", lambda: require(nominal.verify_nominal(report)["valid"] is case["expect"]["original_valid"], "Original report did not self-replay"))
                perform("frozen_source_replacement", lambda: require(nominal.verify_nominal(report, **case["replacement"])["valid"] is case["expect"]["replacement_valid"], "Changed premises validated an old report"))
            elif api in {"read_nominal", "read_nominal_facts"}:
                perform("frozen_expectations", lambda: check_nominal_expectations(case["expect"], report,
                    pronoun_reading=case["group"] == "closed_pronoun_projection"))
            elif api == "count_source_units":
                perform("frozen_expectations", lambda: check_count_expectations(case["expect"], report))
            else:
                perform("frozen_expectations", lambda: check_phrase_expectations(case["expect"], report))
            perform("original_source_replay", lambda: require(verifiers[api](report, **inputs)["valid"], "Exact original source did not replay"))
        perform("semantic_restraint", lambda: semantic_restraint(report))
    return {"id": case["id"], "group": case["group"], "api": api,
            "passed": bool(checks) and all(c["passed"] for c in checks), "checks": checks, **observations}


def evaluate(snapshot=None):
    material = load_material()
    snapshot = runtime_snapshot() if snapshot is None else snapshot
    results = [run_case(case) for case in material["cases"]]
    unchanged = runtime_snapshot() == snapshot
    def score(rows):
        return {"passed": sum(r["passed"] for r in rows), "total": len(rows)}
    tasks = {name: score([r for r in results if r["api"] in apis]) for name, apis in {
        "raw_and_linked_nominal_reading": {"read_nominal"}, "controlled_source_assertions": {"read_nominal_facts"},
        "supplied_weak_root": {"weak_root_profile"}, "supplied_cardinal_rule": {"number_rule"},
        "bounded_count_phrase": {"read_count_phrase"}, "source_occurrence_cardinality": {"count_source_units"},
        "source_replacement": {"verify_nominal"}}.items()}
    tasks["source_structure"] = score([c for r in results for c in r["checks"] if c["check"] == "independent_source_structure"])
    tasks["semantic_restraint"] = score([c for r in results for c in r["checks"] if c["check"] == "semantic_restraint"])
    return {"schema": VERSION, "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "material_sha256": MATERIAL_SHA256, "protocol_sha256": PROTOCOL_SHA256,
        "material_freeze_sha256": FREEZE_SHA256, "table_sha256": TABLE_SHA256,
        "code_snapshot": snapshot, "runtime_unchanged_during_evaluation": unchanged,
        "scope": material["independence"], "claim_limits": material["common_invariants"],
        "pronoun_score_scope": "Specified candidate reading in a closed inventory, not exhaustive Arabic homograph resolution",
        "task_score_scope": "API case totals are disjoint; source-structure/restraint checks overlap and exclude rejected calls",
        "raw_score": score(results), "group_scores": {g: score([r for r in results if r["group"] == g]) for g in sorted({r["group"] for r in results})},
        "task_scores": tasks, "passed": unchanged and all(r["passed"] for r in results), "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--capture-code", action="store_true")
    args = parser.parse_args()
    try:
        require(not args.output.exists(), "Refusing to overwrite a measured result")
        load_material()
        snapshot = runtime_snapshot()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        archive = preserve_snapshot(snapshot, args.output) if args.capture_code else None
        report = evaluate(snapshot)
        if archive is not None:
            report["code_archive"] = archive
        with args.output.open("x", encoding="utf-8") as output:
            output.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({k: report[k] for k in ("schema", "raw_score", "group_scores", "task_scores", "passed")}, indent=2))
        return 0 if report["passed"] else 1
    except (OSError, KeyError, TypeError, ValueError) as error:
        print(json.dumps({"passed": False, "evaluation_error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
