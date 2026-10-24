#!/usr/bin/env python3
"""Exercise the real Lean inna-fragment executable and preserve transport evidence.

These are independently stated operational examples and adversarial wire cases,
not a second implementation of recognize, a linguistic holdout, or a proof of
JSON/compiler/Python refinement. The author also implemented the Lean fragment.
The reused lexical material predates this target and is explicitly an authored
instructional fixture, not a quotation from QAC or acquired lexical authority.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LAW = "nabt.arabic-inna-case-fragment.v1"
REQUEST_SCHEMA = "nabt.arabic-inna-case-fragment.request.v1"
RESPONSE_SCHEMA = "nabt.arabic-inna-case-fragment.response.v1"
LEXICAL_SOURCE = "examples/construction_training.tsv"
LEXICAL_SOURCE_SHA = "06ff1e42fb60dfc45b49df9d029e197314a791f72c683ae8e692fc1e2e6f4e0e"
QATR_SOURCE = "src/nabt/data/source_evidence/qatr.txt"
QATR_SOURCE_SHA = "2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d"
QATR_PASSAGE_SHA = "6cab9860da9f0068855fa60715334acb28e33e83a5fe271138865a68f587dc11"
MAX_WIRE_OUTPUT = 2 * 1024 * 1024
COMPLETE = "COMPLETE_WITHIN_DECLARED_FRAGMENT"
DEFER = "DEFER_LEXICAL_PREMISES"
NONE = "NO_READING_IN_DECLARED_FRAGMENT"
ENVELOPE = {
    "schema": RESPONSE_SCHEMA, "law_id": LAW,
    "authority": "CONDITIONAL_ON_SUPPLIED_LEXICAL_PREMISES",
    "source_acquisition_established": False,
    "lexicon_exhaustiveness_established": False,
    "ordinary_arabic_completeness_established": False,
    "semantic_interpretation_established": False,
    "world_truth": "NOT_ESTABLISHED", "linguistic_rejection": False,
}
SUCCESS_FIELDS = {
    "status", "source_hex", "lexicon", "recognized", "pending", "case_assignment_complete",
    "reference_equivalence", "written_case_basis", "input_profile", "scope",
}
ERROR_FIELDS = {"status", "error", "message", "case_assignment_complete"}
PAIR_FIELDS = {
    "subject_id", "predicate_id", "subject_witness", "predicate_witness",
    "subject_span", "predicate_span", "required_subject_case", "required_predicate_case",
}
PROVENANCE_PATHS = (
    "formal/lean-toolchain", "formal/lakefile.lean", "formal/ProbeJson.lean",
    "formal/Nabt/ArabicCoverage.lean", "formal/Nabt/ArabicInnaFragment.lean",
    "formal/ArabicInnaFragmentProbe.lean", "tools/check_arabic_inna_fragment.py",
    LEXICAL_SOURCE, QATR_SOURCE,
)


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON response key: " + key)
        result[key] = value
    return result


def parse_json(raw: bytes):
    def reject(value):
        raise ValueError("non-JSON response constant: " + value)
    return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=unique_object,
                      parse_constant=reject)


def record(path: Path, root: Path = ROOT):
    raw = path.read_bytes()
    try:
        name = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        name = str(path.resolve())
    return {"path": name, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def checked_source(root: Path, name: str, expected: str) -> bytes:
    raw = (root / name).read_bytes()
    if sha256(raw).hexdigest() != expected:
        raise ValueError("pinned source changed: " + name)
    return raw


def source_material(root: Path = ROOT):
    """No target, role or expected answer enters this source-only function.

    Retain all three pre-existing written forms for both selected lexemes.
    The small Buckwalter projection is declared here, independently of NABT's
    learner. Category/number are annotations; triptote is a stated reading of
    the retained paradigm. Case is deliberately unknown in every input row.
    """
    raw = checked_source(root, LEXICAL_SOURCE, LEXICAL_SOURCE_SHA)
    qatr = checked_source(root, QATR_SOURCE, QATR_SOURCE_SHA)
    wanted = {"zayodN", "zayodK", "zayodFA", "kariymN", "kariymK", "kariymFA"}
    mapping = {"z": "ز", "a": "َ", "y": "ي", "o": "ْ", "d": "د", "N": "ٌ",
               "K": "ٍ", "F": "ً", "A": "ا", "k": "ك", "r": "ر", "i": "ِ", "m": "م"}
    ledger, records, offset = [], [], 0
    for line_number, line in enumerate(raw.splitlines(keepends=True), 1):
        start, offset = offset, offset + len(line)
        text = line.decode("utf-8")
        columns = text.rstrip("\r\n").split("\t")
        if len(columns) != 4 or columns[1] not in wanted:
            continue
        location, form, pos, features = columns
        if pos not in ("PN", "ADJ") or "MS" not in features.split("|"):
            raise ValueError("selected instructional annotation changed")
        if any(c not in mapping for c in form):
            raise ValueError("outside the declared small transliteration profile")
        surface = "".join(mapping[c] for c in form)
        identity = "lex_" + str(len(ledger) + 1)
        ledger.append({
            "id": identity, "witness": f"construction_training:line:{line_number}",
            "surface_hex": surface.encode("utf-8").hex(),
            "category": "proper_name" if pos == "PN" else "adjective",
            "number": "singular", "declension": "triptote", "case": "unknown",
        })
        records.append({"id": identity, "source": LEXICAL_SOURCE, "location": location,
                        "line_1based": line_number, "start": start, "end": offset,
                        "raw_text": text, "span_sha256": sha256(line).hexdigest(),
                        "retained_gender_annotation": "M", "retained_number_annotation": "S"})
    if len(ledger) != 6 or len({r["surface_hex"] for r in ledger}) != 6:
        raise ValueError("six distinct pre-existing lexical forms are required")
    lines = qatr.splitlines(keepends=True)
    excerpt = b"".join(lines[186:195])
    if sha256(excerpt).hexdigest() != QATR_PASSAGE_SHA:
        raise ValueError("pinned Qatr inna passage changed")
    material = {
        "schema": "nabt.inna-fragment-transport-material.v1",
        "law_id": LAW,
        "source_status": "PREEXISTING_AUTHORED_INSTRUCTIONAL_LEXICON_NOT_EXTERNAL_ACQUISITION",
        "source_is_qac_quotation": False, "source_acquisition_established": False,
        "lexicon_exhaustiveness_established": False,
        "target_used_to_build_lexicon": False,
        "selection": "Both selected lexemes retain all three written forms already in the fixture.",
        "interpretation": ("PN/ADJ and MS come from the explicitly authored annotations. Triptote is a "
                           "declared interpretation of the three retained tanwin forms, not proved acquisition. "
                           "The case field is unknown; Lean must inspect the written ending."),
        "source_files": [record(root / LEXICAL_SOURCE, root), record(root / QATR_SOURCE, root)],
        "lexicon": ledger, "lexical_source_records": records,
        "transliteration": {k: mapping[k] for k in sorted(mapping)},
        "rule_passage": {"source": QATR_SOURCE, "line_start_1based": 187,
                         "line_end_1based_inclusive": 195,
                         "start": sum(map(len, lines[:186])), "end": sum(map(len, lines[:195])),
                         "span_sha256": QATR_PASSAGE_SHA, "raw_text": excerpt.decode("utf-8"),
                         "scope": "The inna case rule, not a certificate for the lexical annotations."},
    }
    return material


@dataclass(frozen=True)
class WireCase:
    identity: str
    wire: bytes
    request: dict | None
    status: str
    recognized: tuple[tuple[str, str], ...] = ()
    pending: tuple[tuple[str, str], ...] = ()
    error: str | None = None


def make_cases(material: dict) -> list[WireCase]:
    """Stated examples and mutations; this does not compute a grammar oracle."""
    ledger = deepcopy(material["lexicon"])
    if [bytes.fromhex(x["surface_hex"]).decode() for x in ledger] != [
            "زَيْدٌ", "زَيْدٍ", "زَيْدًا", "كَرِيمٌ", "كَرِيمٍ", "كَرِيمًا"]:
        raise ValueError("the declared demonstration ledger differs")
    base = {"schema": REQUEST_SCHEMA, "op": "recognize", "lexicon": ledger,
            "source_hex": "إِنَّ زَيْدًا كَرِيمٌ".encode().hex()}
    cases = []

    def add(identity, request, status, recognized=(), pending=(), error=None):
        cases.append(WireCase(identity, canonical(request), request, status,
                              tuple(recognized), tuple(pending), error))

    pair = ("lex_3", "lex_4")
    add("source_fixture_written_case", deepcopy(base), COMPLETE, [pair])
    r = deepcopy(base)
    r["lexicon"][2]["case"], r["lexicon"][3]["case"] = "nasb", "raf"
    add("consistent_explicit_case_tags", r, COMPLETE, [pair])
    for feature in ("category", "number", "declension"):
        r = deepcopy(base)
        r["lexicon"][2][feature] = "unknown"
        add("unknown_" + feature, r, DEFER, pending=[pair])
    r = deepcopy(base)
    alternate = deepcopy(r["lexicon"][2])
    alternate.update(id="alternative", witness="authored:transport:alternative")
    r["lexicon"].append(alternate)
    add("all_registered_alternatives", r, COMPLETE, [pair, ("alternative", "lex_4")])
    r = deepcopy(r)
    r["lexicon"][-1]["declension"] = "unknown"
    add("pending_competitor_blocks_completion", r, DEFER, [pair], [("alternative", "lex_4")])
    r = deepcopy(base)
    r["lexicon"][0]["case"] = "nasb"
    add("nasb_tag_cannot_override_raf_surface", r, "ERROR", error="INVALID_INPUT")
    r = deepcopy(base)
    r["lexicon"][2]["surface_hex"] = "زَيْد".encode().hex()
    r["source_hex"] = "إِنَّ زَيْد كَرِيمٌ".encode().hex()
    add("missing_written_ending", r, DEFER, pending=[pair])
    for identity, text in (
        ("overt_wrong_subject_case", "إِنَّ زَيْدٌ كَرِيمٌ"),
        ("overt_wrong_predicate_case", "إِنَّ زَيْدًا كَرِيمًا"),
        ("unknown_lexeme", "إِنَّ أَوْسًا كَرِيمٌ"),
        ("no_operator_shadda", "إِنْ زَيْدًا كَرِيمٌ"),
        ("extra_space", "إِنَّ  زَيْدًا كَرِيمٌ"),
        ("trailing_punctuation", "إِنَّ زَيْدًا كَرِيمٌ."),
        ("reversed_roles", "إِنَّ كَرِيمٌ زَيْدًا"),
    ):
        r = deepcopy(base)
        r["source_hex"] = text.encode().hex()
        add(identity, r, NONE)
    r = deepcopy(base)
    r["lexicon"] = []
    add("empty_ledger", r, NONE)
    for identity, change in (
        ("uppercase_hex", lambda r: r.update(source_hex=r["source_hex"].upper())),
        ("odd_hex", lambda r: r.update(source_hex=r["source_hex"] + "a")),
        ("invalid_utf8_source", lambda r: r.update(source_hex="ff")),
        ("invalid_utf8_surface", lambda r: r["lexicon"][0].update(surface_hex="ff")),
        ("boolean_case_tag", lambda r: r["lexicon"][0].update(case=True)),
        ("undeclared_authority_field", lambda r: r.update(expected=True)),
        ("duplicate_lexical_identity", lambda r: r["lexicon"].append(deepcopy(r["lexicon"][0]))),
    ):
        r = deepcopy(base)
        change(r)
        add(identity, r, "ERROR", error="INVALID_INPUT")
    r = deepcopy(base)
    r["source_hex"] = "61" * 2049
    add("source_budget", r, "ERROR", error="RESOURCE_LIMIT")
    r = deepcopy(base)
    r["lexicon"] = [dict(deepcopy(ledger[0]), id=f"entry_{n}") for n in range(33)]
    add("ledger_budget", r, "ERROR", error="RESOURCE_LIMIT")
    cases.extend([
        WireCase("noncanonical_whitespace", json.dumps(base, sort_keys=True).encode(), None,
                 "ERROR", error="INVALID_INPUT"),
        WireCase("duplicate_json_key", canonical(base)[:-1] + b',"op":"recognize"}', None,
                 "ERROR", error="INVALID_INPUT"),
        WireCase("malformed_json", b'{"schema":', None, "ERROR", error="INVALID_INPUT"),
        WireCase("invalid_utf8_line", b'\xff', None, "ERROR", error="INVALID_INPUT"),
        WireCase("oversize_line", b" " * 65537, None, "ERROR", error="RESOURCE_LIMIT"),
    ])
    add("valid_request_after_overflow_at_eof", deepcopy(base), COMPLETE, [pair])
    return cases


def request_stream(cases: list[WireCase]) -> bytes:
    if not cases or any(b"\n" in case.wire for case in cases):
        raise ValueError("each case must be one complete wire record")
    # The last request deliberately ends at EOF without a newline.
    return b"\n".join(case.wire for case in cases)


def equal_typed(actual, expected) -> bool:
    return canonical(actual) == canonical(expected)


def check_response(case: WireCase, response: dict):
    if type(response) is not dict:
        raise ValueError(case.identity + ": response is not an object")
    fields = ERROR_FIELDS if case.status == "ERROR" else SUCCESS_FIELDS
    if set(response) != set(ENVELOPE) | fields:
        raise ValueError(case.identity + ": response schema differs")
    for key, value in ENVELOPE.items():
        if not equal_typed(response[key], value):
            raise ValueError(case.identity + ": authority boundary changed: " + key)
    if response["status"] != case.status:
        raise ValueError(case.identity + ": wrong status")
    if not equal_typed(response["case_assignment_complete"], case.status == COMPLETE):
        raise ValueError(case.identity + ": false or mistyped completeness flag")
    if case.status == "ERROR":
        if response["error"] != case.error or type(response["message"]) is not str or not response["message"]:
            raise ValueError(case.identity + ": error category/message differs")
        return
    request = case.request
    if request is None:
        raise ValueError("an accepted test requires an original request")
    if not equal_typed(response["source_hex"], request["source_hex"]):
        raise ValueError(case.identity + ": source bytes were changed")
    if not equal_typed(response["lexicon"], request["lexicon"]):
        raise ValueError(case.identity + ": supplied lexical ledger was changed")
    expected_labels = {
        "reference_equivalence": "Nabt.ArabicInnaFragment.recognize_iff_reference",
        "written_case_basis": "literal_utf8_tanwin_endings_with_explicit_accusative_alif.v1",
        "input_profile": "exact_inna_prefix_single_ascii_spaces_no_final_punctuation.v1",
        "scope": "all_case_assignments_in_declared_inna_fragment_relative_to_supplied_lexicon",
    }
    for key, expected in expected_labels.items():
        if response[key] != expected:
            raise ValueError(case.identity + ": changed scoped contract label")
    ledger = {x["id"]: x for x in request["lexicon"]}
    source = bytes.fromhex(request["source_hex"])
    for field, expected_pairs in (("recognized", case.recognized), ("pending", case.pending)):
        rows = response[field]
        if type(rows) is not list:
            raise ValueError(case.identity + ": reading list must be an array")
        pairs = []
        for row in rows:
            if type(row) is not dict or set(row) != PAIR_FIELDS:
                raise ValueError(case.identity + ": unexpected analysis shape")
            pair = row["subject_id"], row["predicate_id"]
            if any(type(x) is not str or x not in ledger for x in pair):
                raise ValueError(case.identity + ": analysis refers to an unbound lexical identity")
            if pair in pairs:
                raise ValueError(case.identity + ": duplicate analysis pair")
            pairs.append(pair)
            for role, identity in zip(("subject", "predicate"), pair):
                span = row[role + "_span"]
                if (type(span) is not list or len(span) != 2 or
                        any(type(v) is not int for v in span) or
                        not 0 <= span[0] < span[1] <= len(source)):
                    raise ValueError(case.identity + ": invalid byte span")
                if source[span[0]:span[1]] != bytes.fromhex(ledger[identity]["surface_hex"]):
                    raise ValueError(case.identity + ": span does not restore its literal source")
                if row[role + "_witness"] != ledger[identity]["witness"]:
                    raise ValueError(case.identity + ": witness identity changed")
            ss, ps = row["subject_span"], row["predicate_span"]
            if source[:ss[0]] != "إِنَّ ".encode() or source[ss[1]:ps[0]] != b" " or ps[1] != len(source):
                raise ValueError(case.identity + ": source partition is not the declared exact frame")
            if row["required_subject_case"] != "nasb" or row["required_predicate_case"] != "raf":
                raise ValueError(case.identity + ": operator case assignment differs")
        if set(pairs) != set(expected_pairs) or len(pairs) != len(expected_pairs):
            raise ValueError(case.identity + ": omitted or invented " + field + " alternatives")


def check_wire(cases: list[WireCase], stdout: bytes, stderr: bytes, returncode: int):
    if returncode != 0:
        raise ValueError("probe exited unsuccessfully: " + str(returncode))
    if stderr:
        raise ValueError("unexpected probe stderr")
    if not stdout.endswith(b"\n"):
        raise ValueError("every response must end with one framing newline")
    lines = stdout[:-1].split(b"\n")
    if len(lines) != len(cases):
        raise ValueError("one response per request is required, including recovery and final EOF")
    checked = []
    for case, line in zip(cases, lines):
        if len(line) + 1 > MAX_WIRE_OUTPUT:
            raise ValueError("response wire budget exceeded")
        response = parse_json(line)
        if canonical(response) != line:
            raise ValueError("response must use canonical compact JSON")
        check_response(case, response)
        checked.append({"id": case.identity, "status": response["status"], "pass": True,
                        "response_bytes_including_newline": len(line) + 1,
                        "response_sha256": sha256(line + b"\n").hexdigest()})
    return checked


def write_fixed(path: Path, raw: bytes):
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("refusing to rewrite a different existing artifact: " + str(path))
    else:
        with path.open("xb") as handle:
            handle.write(raw)


def prepare(directory: Path, root: Path = ROOT):
    directory.mkdir(parents=True, exist_ok=True)
    material = source_material(root)
    cases = make_cases(material)
    write_fixed(directory / "lexical_material.json", canonical(material) + b"\n")
    write_fixed(directory / "requests.jsonl", request_stream(cases))
    expected = {"schema": "nabt.inna-transport-expectations.v1", "cases": [
        {"id": c.identity, "status": c.status, "recognized": c.recognized, "pending": c.pending,
         "error": c.error, "request_bytes": len(c.wire), "request_sha256": sha256(c.wire).hexdigest()}
        for c in cases]}
    write_fixed(directory / "expectations.json", canonical(expected) + b"\n")
    return material, cases


def execute(probe: Path, directory: Path, *, timeout: int = 60):
    material, cases = prepare(directory)
    for name in ("responses.jsonl", "stderr.bin", "report.json"):
        if (directory / name).exists():
            raise ValueError("execution artifacts already exist; choose a new output directory")
    probe = probe.resolve(strict=True)
    paths = [ROOT / p for p in PROVENANCE_PATHS] + [probe]
    test = ROOT / "tests/test_arabic_inna_fragment_probe.py"
    if test.is_file():
        paths.append(test)
    before = [record(p) for p in paths]
    started = datetime.now(timezone.utc).isoformat()
    execution_error = None
    try:
        process = subprocess.run([str(probe)], input=request_stream(cases), capture_output=True,
                                 cwd=ROOT, timeout=timeout, check=False)
        stdout, stderr, returncode = process.stdout, process.stderr, process.returncode
    except subprocess.TimeoutExpired as failure:
        stdout, stderr, returncode = failure.stdout or b"", failure.stderr or b"", None
        execution_error = "probe exceeded its execution time budget"
    except OSError as failure:
        stdout, stderr, returncode = b"", str(failure).encode("utf-8"), None
        execution_error = "probe could not be executed"
    write_fixed(directory / "responses.jsonl", stdout)
    write_fixed(directory / "stderr.bin", stderr)
    after = [record(p) for p in paths]
    checked, error = [], None
    try:
        if execution_error is not None:
            raise ValueError(execution_error)
        if before != after:
            raise ValueError("program/source/checker inputs changed during execution")
        checked = check_wire(cases, stdout, stderr, returncode)
    except (ValueError, TypeError, KeyError, UnicodeError) as failure:
        error = str(failure)
    report = {
        "schema": "nabt.inna-fragment-transport-check.v1", "ok": error is None,
        "law_id": LAW, "started_utc": started, "completed_utc": datetime.now(timezone.utc).isoformat(),
        "command": [str(probe)], "returncode": returncode, "error": error,
        "case_count": len(cases), "checks": checked, "files_before": before, "files_after": after,
        "program_and_inputs_unchanged": before == after,
        "artifacts": [record(directory / name) for name in
                      ("lexical_material.json", "expectations.json", "requests.jsonl", "responses.jsonl", "stderr.bin")],
        "source_status": material["source_status"],
        "authorship": "Transport checker and Lean implementation share an author; operational expectations are stated separately.",
        "scope": "Actual Lean executable on preserved transport examples and boundary mutations; not general JSON/Python/compiler refinement.",
        "build_performed_by_this_tool": False, "compiler_correctness_proved": False,
        "lexical_acquisition_established": False, "lexicon_exhaustiveness_established": False,
        "independent_linguistic_holdout": False, "all_arabic_completeness_established": False,
        "world_truth": "NOT_ESTABLISHED",
    }
    write_fixed(directory / "report.json", json.dumps(report, ensure_ascii=False, indent=2).encode() + b"\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, default=ROOT / "formal/.lake/build/bin/arabicInnaFragmentProbe")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.prepare_only:
            _, cases = prepare(args.output_dir)
            report = {"ok": True, "execution_performed": False, "case_count": len(cases),
                      "output_dir": str(args.output_dir)}
        else:
            report = execute(args.probe, args.output_dir)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 1
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
