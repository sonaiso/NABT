#!/usr/bin/env python3
"""Compare two installed lexical profiles on the same frozen reference.

This performs source loading and Python replay, not model training. The full
QAC profile includes verbs; improvements cannot be attributed to matrix nouns
alone. Lexical counts cover occurrences emitted by the reader, not a complete
independent tokenization of all Arabic input.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path

from tools.attested_lexical_loader import load_attested_lexicon
from tools.benchmark_semantic_axes import REFERENCE, run


def summarize_report(report):
    coverage = [row["lexical_coverage"] for row in report["cases"]
                if row["lexical_coverage"] is not None]
    return {"profile": report["lexical_profile"], "axes": report["axes"],
        "lexical_occurrences": {key: sum(row[key] for row in coverage)
                                for key in ("tokens", "covered", "uncovered")},
        "lexical_cases_measured": len(coverage),
        "successful_cases": [{"id": row["id"], "text": row["input"]["text"],
            "axes": [axis for axis, value in row["axis_results"].items() if value["status"] == "PASS"]}
            for row in report["cases"] if any(value["status"] == "PASS" for value in row["axis_results"].values())],
        "remaining_gaps": [{"id": row["id"],
            "missing_lexical_occurrences": [item["surface"] for item in (row["lexical_coverage"] or {}).get("items", []) if item["reading_count"] == 0],
            "reader_obligations": (row["execution"].get("observed") or {}).get("missing_premises", []),
            "reader_status": (row["execution"].get("observed") or {}).get("reader_status")}
            for row in report["cases"]]}


def measure(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    reference_sha = sha256(REFERENCE.read_bytes()).hexdigest()
    loaded = load_attested_lexicon()
    profiles, files = {}, {}
    for profile in ("teaching_v1", "attested_qac_v1"):
        result = run(lexical_profile=profile)
        if result["reference_sha256"] != reference_sha:
            raise RuntimeError("Reference identity changed")
        raw = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
        name = profile + ".json.gz"
        (output / name).write_bytes(gzip.compress(raw, mtime=0))
        files[profile] = {"path": name, "decoded_sha256": sha256(raw).hexdigest(),
                          "archive_sha256": sha256((output / name).read_bytes()).hexdigest()}
        profiles[profile] = summarize_report(result)
    report = {"schema": "nabt.lexical-loading-measurement.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reference_sha256": reference_sha, "source_loading": loaded.report,
        "profiles": profiles, "reports": files,
        "selection": "ALL_PRE_EXISTING_CATALOGUE_SENSES_AND_FULL_PINNED_SOURCE_NOT_GOLD_FILTERING",
        "comparison": "TWO_SOURCE_PROFILES_SAME_READER_SAME_SCORER_SAME_REFERENCE",
        "lexical_denominator": "Reader-emitted lexical occurrences; repeats count, operator candidates do not. Not an independent full-input tokenization.",
        "scope": "The full external annotation profile includes verbs and names. Matrix candidates do not license contextual senses. Reference is diagnostic, not blind or held-out from the engineering team.",
        "training_performed": False, "whole_arabic_complete": False,
        "benchmark_lean_native_checked": False, "world_truth_established": False}
    (output / "measurement.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = measure(args.output_dir)
    print(json.dumps({"reference_sha256": report["reference_sha256"],
        "profiles": {name: {"axes": row["axes"], "lexical_occurrences": row["lexical_occurrences"]}
                     for name, row in report["profiles"].items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
