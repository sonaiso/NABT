#!/usr/bin/env python3
"""Replay the published independent Arabic-profile evaluation, without mutation.

This is regression on a small public reference. Passing preserves bounded
behavior; it does not establish general Arabic understanding or the roadmap's
300-episode gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

from arabic_syntax_evaluation_helpers.runner import EVALUATOR_VERSION,run
from arabic_syntax_evaluation_helpers.statement_oracle import ANNOTATION_PATH,ANNOTATION_SHA256
from text_evaluation.integrity import (
    prepare_output_directory,
    verify_code_freeze,
    write_report,
)


ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = ROOT / "evidence/arabic_syntax/independent"
DEFAULT_FREEZE = ROOT / "evidence/interpretive_links_v1/code_freeze_v1.json"
ARTIFACT_MANIFEST_SHA256 = "d42eab25417d1bac2659337c78769dfc9a299b808379752236bf016cfff50429"
FIRST_SNAPSHOT = "4662ac75ded649b9f1d5d4d0e152fa292e4b63e72e6ce55ec924bad9b65e6524"
PREVIOUSLY_COMPLETE = frozenset({"s01", "s02", "s04", "s05", "s06", "s07", "s09", "s12"})


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inputs(data: Path) -> dict:
    """A rewritten data/manifest pair cannot grant itself the published identity."""
    data = data.resolve()
    manifest = data / "artifact_manifest.json"
    if _digest(manifest) != ARTIFACT_MANIFEST_SHA256:
        raise ValueError("Published Arabic evaluation manifest checksum differs")
    records = json.loads(manifest.read_text(encoding="utf-8"))["files"]
    seen = set()
    for record in records:
        name = record["path"]
        parts = PurePosixPath(name)
        if (not isinstance(name, str) or "\\" in name or parts.is_absolute()
                or parts.as_posix() != name or any(p in {".", ".."} for p in parts.parts)
                or name in seen):
            raise ValueError("Invalid or repeated evaluation artifact path")
        seen.add(name)
        path = data / name
        if not path.is_file() or not path.resolve().is_relative_to(data):
            raise ValueError("Evaluation artifact is absent or escapes its root")
        if path.stat().st_size != record["bytes"] or _digest(path) != record["sha256"]:
            raise ValueError("Frozen Arabic evaluation artifact differs: " + name)
    return {"manifest_sha256": ARTIFACT_MANIFEST_SHA256, "files_checked": len(records)}


def regression_gate(result: dict, *, snapshot: str, reference: dict) -> dict:
    """No unsafe acceptance, no vacuous all-DEFER pass, no historical score rewrite."""
    episodes = result["episodes"]
    passed_ids = {row["id"] for row in episodes if row["complete_episode"]}
    safe = all(row["admitted_claims_licensed"] for row in episodes)
    restored = all(row["source_restoration"] for row in episodes)
    certs = all(row["independent_certificates_pass"] for row in episodes)
    budget = all(row["within_budget"] for row in episodes) and result["seconds"] <= 180
    real = result["real_excerpts"]
    real_safe = all(row.get("comparison", {}).get("admitted_claims_licensed", False) for row in real)
    real_restored = all(row.get("source_restored", False) for row in real)
    preserved = PREVIOUSLY_COMPLETE <= passed_ids
    exact_counts = result["summary"] == reference["summary"]
    frozen_counts = snapshot != FIRST_SNAPSHOT or exact_counts
    complete_inventory = (
        len(episodes) == 52 and len({row["id"] for row in episodes}) == 52
        and sum(row["queries"] for row in episodes) == 54 and len(real) == 8
    )
    passed = all((safe, restored, certs, budget, real_safe, real_restored,
                  preserved, frozen_counts, complete_inventory))
    return {
        "passed": passed,
        "scope": "published bounded-profile regression; not the 300-episode coverage gate",
        "no_incorrect_admitted_claim": safe and real_safe,
        "all_source_bytes_restored": restored and real_restored,
        "independent_certificate_checks_pass": certs,
        "previously_complete_cases_preserved": preserved,
        "same_frozen_runtime_reproduces_published_counts": frozen_counts,
        "exact_published_counts": exact_counts,
        "complete_case_inventory": complete_inventory,
        "within_recorded_budgets": budget,
        "standalone_complete": result["summary"]["standalone"]["complete_episodes"],
        "standalone_total": 40,
        "original_excerpt_semantic_read": result["summary"]["real_excerpts"]["semantic_read"],
        "original_excerpt_total": 8,
    }


def main() -> int:
    if not __debug__:
        raise ValueError("Run evaluation without Python -O; independent checks must remain enabled")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, default=PUBLISHED)
    parser.add_argument("--code-freeze", type=Path, default=DEFAULT_FREEZE)
    args = parser.parse_args()
    data = args.data_root.resolve()
    freeze_path = args.code_freeze.resolve()
    identity = verify_inputs(data)
    freeze = verify_code_freeze(freeze_path, ROOT)
    # Published history is protected even if an unchanged data copy is supplied.
    output = args.output_dir.resolve()
    for protected in (ROOT / "evidence", ROOT / "src", ROOT / "tools", ROOT / "formal"):
        if output == protected.resolve() or output.is_relative_to(protected.resolve()):
            raise ValueError("Evaluation output cannot be inside source or published history")
    output = prepare_output_directory(output, data=data, freeze=freeze_path)
    result = run(data, "arabic")
    reference = json.loads((data / "first_results.json").read_text(encoding="utf-8"))
    gate = regression_gate(result, snapshot=freeze["snapshot_sha256"], reference=reference)
    helpers = sorted((ROOT / "tools/arabic_syntax_evaluation_helpers").glob("*.py"))
    helpers.append(Path(__file__).resolve())
    helpers.append(ROOT / "tools/text_evaluation/integrity.py")
    receipt = {
        "schema": "nabt.arabic-syntax.public-regression-receipt.v2",
        "evaluator_version": EVALUATOR_VERSION,
        "evaluation_kind": "public_regression",
        "frozen_inputs": identity,
        "runtime_snapshot": freeze["snapshot_sha256"],
        "runtime_files_checked": len(freeze["files"]),
        "statement_oracle": {"path": ANNOTATION_PATH.relative_to(ROOT).as_posix(),
                             "sha256": ANNOTATION_SHA256,
                             "kind": "post-evaluation public-reference annotation, not new blinded gold"},
        "evaluator_files": [{"path": p.relative_to(ROOT).as_posix(), "sha256": _digest(p)} for p in helpers],
        "gate": gate,
        "summary": result["summary"],
    }
    write_report(output / "results.json", result, data=data, freeze=freeze_path)
    write_report(output / "receipt.json", receipt, data=data, freeze=freeze_path)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if gate["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
