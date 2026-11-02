"""Extract the completed general unittest segment, without executing tests.

Verbose unittest descriptions may put the method identity and its outcome on
different lines.  Fixture skips are outcome records but are not methods run.
Only the prefix through the first complete footer is bound by this evidence;
any subsequent make/native gate remains outside this summary's authority.
"""
import ast
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[3]
LOG = "artifacts/local/derivation-surface-full-check-attempt2/full_check.log"
FOOTER = re.compile(
    rb"\n-{10,}\r?\nRan (\d+) tests? in ([^\r\n]+)\r?\n\r?\n"
    rb"(OK(?: \([^\r\n]*\))?|FAILED(?: \([^\r\n]*\))?)\r?\n")
HEADER = re.compile(
    rb"^(test\S*|runTest|setUpClass|tearDownClass|setUpModule|tearDownModule) "
    rb"\(([^)\r\n]+)\)(?= \.\.\. |\r?$)", re.M)
OUTCOME = re.compile(
    rb"(?: \.\.\. |^)(ok|FAIL|ERROR|expected failure|unexpected success|skipped [^\r\n]+)"
    rb"[ \t]*\r?$", re.M)
FIXTURES = {"setUpClass", "tearDownClass", "setUpModule", "tearDownModule"}


def main():
    raw = (ROOT / LOG).read_bytes()
    footer = FOOTER.search(raw)
    if footer is None:
        raise ValueError("No completed unittest footer: no final summary may be written")
    prefix = raw[:footer.end()]
    body = raw[:footer.start()]
    if body.splitlines()[0] != b"python3 -m unittest discover -s tests -v":
        raise ValueError("The first completed segment is not the expected general discovery command")
    headers = list(HEADER.finditer(body))
    records = []
    for index, header in enumerate(headers):
        stop = headers[index + 1].start() if index + 1 < len(headers) else len(body)
        block = body[header.end():stop]
        outcomes = list(OUTCOME.finditer(block))
        if len(outcomes) != 1:
            raise ValueError("Ambiguous or missing outcome for " + header.group(2).decode("utf-8"))
        outcome = outcomes[0].group(1).decode("utf-8")
        name = header.group(1).decode("utf-8")
        row = {"name": name, "id": header.group(2).decode("utf-8"),
               "kind": "fixture" if name in FIXTURES else "method",
               "status": "skipped" if outcome.startswith("skipped ") else outcome,
               "header_byte_start": header.start(),
               "outcome_byte_end": header.end() + outcomes[0].end(),
               "multiline_description": block.startswith((b"\n", b"\r\n"))}
        if row["status"] == "skipped":
            row["reason"] = ast.literal_eval(outcome[len("skipped "):])
            if type(row["reason"]) is not str:
                raise ValueError("Unexpected skipped-reason representation")
        records.append(row)
    methods = [row for row in records if row["kind"] == "method"]
    fixtures = [row for row in records if row["kind"] == "fixture"]
    method_counts = Counter(row["status"] for row in methods)
    fixture_counts = Counter(row["status"] for row in fixtures)
    footer_text = footer.group(3).decode("ascii")
    declared_run = int(footer.group(1))
    skip_match = re.search(r"(?:\(|, )skipped=(\d+)(?:,|\))", footer_text)
    declared_skipped = int(skip_match.group(1)) if skip_match else 0
    checks = {
        "declared_run_equals_method_records": declared_run == len(methods),
        "declared_skipped_equals_methods_plus_fixtures": declared_skipped ==
            method_counts["skipped"] + fixture_counts["skipped"],
        "every_header_has_exactly_one_outcome": len(records) == len(headers),
        "completed_prefix_unchanged_during_extraction":
            (ROOT / LOG).read_bytes()[:footer.end()] == prefix,
    }
    if not all(checks.values()):
        raise ValueError("Unittest count or prefix integrity mismatch: " + repr(checks))
    skips = [row for row in records if row["status"] == "skipped"]
    method_ids = Counter(row["id"] for row in methods)
    report = {
        "schema": "nabt.derivation-surface.unittest-summary.v1",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "attempt": 2,
        "tested_head": subprocess.check_output(["git", "rev-parse", "e1e4a950"], cwd=ROOT, text=True).strip(),
        "scope": "Completed general unittest discovery segment only",
        "full_gate_success_established": False,
        "later_make_and_native_results": "OUTSIDE_THIS_SUMMARY",
        "command": "python3 -m unittest discover -s tests -v",
        "extraction_command": "python evidence/derivation_surface_v1/validation/extract_unittest_summary.py",
        "extractor_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_log": LOG,
        "source_log_claimed_final": False,
        "completed_prefix": {"byte_start": 0, "byte_end": footer.end(),
                             "bytes": len(prefix), "sha256": sha256(prefix).hexdigest(),
                             "ends_after": "First complete unittest result footer, including its LF"},
        "footer": {"declared_tests_run": declared_run,
                   "declared_skipped_outcomes": declared_skipped,
                   "elapsed": footer.group(2).decode("ascii"), "result": footer_text},
        "methods": {"observed": len(methods), "distinct_ids": len(method_ids),
                    "ok": method_counts["ok"], "skipped": method_counts["skipped"],
                    "failures": method_counts["FAIL"], "errors": method_counts["ERROR"],
                    "expected_failures": method_counts["expected failure"],
                    "unexpected_successes": method_counts["unexpected success"],
                    "duplicate_ids": {key: count for key, count in method_ids.items() if count > 1}},
        "fixtures": {"observed": len(fixtures), "skipped": fixture_counts["skipped"],
                     "skipped_setUpClass": sum(row["status"] == "skipped" and row["name"] == "setUpClass"
                                                for row in fixtures), "records": fixtures},
        "multiline_descriptions": {
            "method_count": sum(row["multiline_description"] for row in methods),
            "method_ids": [row["id"] for row in methods if row["multiline_description"]],
            "counting_note": "A one-line name/.../ok regex omits these completed methods; header blocks are counted instead."},
        "skip_reasons": dict(sorted(Counter(row["reason"] for row in skips).items())),
        "skipped_records": skips,
        "consistency_checks": checks,
        "counts_verified": True,
    }
    with Path(__file__).with_name("unittest_summary.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"footer": report["footer"], "methods": report["methods"],
                      "fixtures": report["fixtures"], "multiline_methods": report["multiline_descriptions"]["method_count"],
                      "completed_prefix": report["completed_prefix"], "counts_verified": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
