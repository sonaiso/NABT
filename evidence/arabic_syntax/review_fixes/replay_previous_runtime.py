"""Replay the first frozen runtime with the current, corrected evaluator.

Run with python -I and an extracted baseline checkout. This does not overwrite
the first experiment, and is explicitly a public-reference re-evaluation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from arabic_syntax_evaluation import FIRST_SNAPSHOT, regression_gate, verify_inputs
from arabic_syntax_evaluation_helpers.runner import EVALUATOR_VERSION, run
from arabic_syntax_evaluation_helpers.statement_oracle import ANNOTATION_SHA256
from text_evaluation.integrity import prepare_output_directory, verify_code_freeze, write_report


def main() -> int:
    if not __debug__:
        raise ValueError("Run without Python -O")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    baseline = args.baseline_root.resolve()
    data = ROOT / "evidence/arabic_syntax/independent"
    freeze_path = ROOT / "evidence/arabic_syntax/code_freeze_first.json"
    identity = verify_inputs(data)
    freeze = verify_code_freeze(freeze_path, baseline)
    if freeze["snapshot_sha256"] != FIRST_SNAPSHOT:
        raise ValueError("This comparison requires the original runtime snapshot")
    output = args.output_dir.resolve()
    for checkout in (ROOT, baseline):
        for name in ("evidence", "src", "tools", "formal"):
            protected = (checkout / name).resolve()
            if output == protected or output.is_relative_to(protected):
                raise ValueError("Write re-evaluation outside sources and historical evidence")
    output = prepare_output_directory(output, data=data, freeze=freeze_path)
    # The evaluator imports NABT only inside run(); use the independently
    # verified old package, while retaining the current evaluator and annotation.
    sys.path.insert(0, str(baseline / "src"))
    import nabt
    if Path(nabt.__file__).resolve() != (baseline / "src/nabt/__init__.py").resolve():
        raise ValueError("The imported runtime is not the verified baseline")
    result = run(data, "arabic")
    reference = json.loads((data / "first_results.json").read_text(encoding="utf-8"))
    gate = regression_gate(result, snapshot=FIRST_SNAPSHOT, reference=reference)
    files = sorted((ROOT / "tools/arabic_syntax_evaluation_helpers").glob("*.py"))
    files += [ROOT / "tools/arabic_syntax_evaluation.py",
              ROOT / "tools/text_evaluation/integrity.py", Path(__file__).resolve()]
    receipt = {
        "schema": "nabt.arabic-syntax.previous-runtime-reevaluation.v1",
        "evaluation_kind": "public_reevaluation_of_original_runtime",
        "evaluator_version": EVALUATOR_VERSION,
        "runtime_version": nabt.__version__,
        "runtime_snapshot": FIRST_SNAPSHOT,
        "runtime_files_checked": len(freeze["files"]),
        "frozen_inputs": identity,
        "statement_oracle_sha256": ANNOTATION_SHA256,
        "evaluator_files": [{"path": p.relative_to(ROOT).as_posix(),
                             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],
        "gate": gate,
        "summary": result["summary"],
    }
    write_report(output / "results.json", result, data=data, freeze=freeze_path)
    write_report(output / "receipt.json", receipt, data=data, freeze=freeze_path)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if gate["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
