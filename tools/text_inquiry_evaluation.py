#!/usr/bin/env python3
"""Replay the published text-inquiry evaluation against a pinned runtime.

The original episodes were hidden from builders before their recorded first
runs. They are now public regression fixtures. This tool never creates a new
heldout score, and it refuses changes to the frozen dataset or runtime pins.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

from text_evaluation import adversarial, baseline, boundaries, controlled, natural, plans
from text_evaluation.integrity import (digest, evaluator_identity, prepare_output_directory, verify_code_freeze,
                                      verify_published_inputs, write_report)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "evidence/text_inquiry"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA,
                        help="Directory containing an unchanged copy of the published frozen data")
    parser.add_argument("--code-freeze", type=Path,
                        help="Runtime checksum manifest; defaults to the portable source projection of the final snapshot")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="A separate output directory; historical evidence is never overwritten")
    parser.add_argument("--suite", choices=("all", "controlled", "natural", "attacks", "plans", "boundaries", "baseline"), default="all")
    parser.add_argument("--partition", choices=("all", "first40", "reserve20"), default="all")
    args = parser.parse_args()
    data = args.data_root.resolve()
    output = args.output_dir.resolve()
    freeze = (args.code_freeze or data / "code_freeze_reserve20_portable.json").resolve()
    try:
        inputs = verify_published_inputs(data)
        runtime = verify_code_freeze(freeze)
        output = prepare_output_directory(output, data=data, freeze=freeze)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    modules = {
        "controlled": controlled,
        "natural": natural,
        "attacks": adversarial,
        "plans": plans,
        "boundaries": boundaries,
        "baseline": baseline,
    }
    chosen = list(modules) if args.suite == "all" else [args.suite]
    summaries = {}
    passed = True
    for name in chosen:
        module = modules[name]
        if hasattr(module, "PRIVATE"):
            module.PRIVATE = data
        if hasattr(module, "DATASET"):
            module.DATASET = data / "controlled_text_benchmark.json"
        destination = output / f"{name}_rerun.json"
        argv = [f"text_evaluation.{name}", "--output", str(destination), "--code-freeze", str(freeze)]
        if name == "controlled":
            argv += ["--partition", args.partition]
        previous = sys.argv
        try:
            sys.argv = argv
            with contextlib.redirect_stdout(io.StringIO()):
                module.main()
        finally:
            sys.argv = previous
        report = json.loads(destination.read_text(encoding="utf-8"))
        summary = report["summary"]
        summaries[name] = summary
        if name == "controlled":
            passed &= summary["episodes_passed"] == summary["episodes"]
            passed &= summary["query_checkpoints_passed"] == summary["query_checkpoints"]
        elif name == "natural":
            passed &= summary["safety_passed"] == summary["raw_book_spans"]
        elif name in {"attacks", "boundaries"}:
            passed &= summary["passed"] == summary["probes"]
        elif name == "plans":
            passed &= summary["passed"] == summary["reviewer_regression_scenarios"]
            passed &= summary["invalid_returned_plans"] == 0
    result = {
        "schema": "nabt-published-text-evaluation-replay-v1",
        "evaluation_role": "post-publication regression",
        "passed": bool(passed),
        "data_root": str(data),
        "code_freeze": str(freeze),
        "code_freeze_sha256": digest(freeze),
        "runtime_snapshot_sha256": runtime["snapshot_sha256"],
        "published_input_integrity": inputs,
        "evaluator_sources": evaluator_identity(),
        "summaries": summaries,
    }
    write_report(output / "summary.json", result, data=data, freeze=freeze)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
