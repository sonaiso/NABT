#!/usr/bin/env python3
"""Reproduce the bounded foundation experiment; no corpus or API is required."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nabt.acquisition import acquire_transition_model
from nabt.ambiguity import AmbiguityForest
from nabt.alphabet import render_word


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    started = perf_counter()
    result = acquire_transition_model()
    elapsed = perf_counter() - started
    if result.model is None:
        raise SystemExit(result.residual)
    ambiguity = []
    for source in ("كتب", "كا", "كَتْبْ"):
        for mode in ("wasl", "waqf"):
            forest = AmbiguityForest(source, mode)
            row = forest.as_dict()
            row["example_completions"] = [render_word(forest.witness(i)) for i in range(min(3, forest.total))]
            ambiguity.append(row)
    data = {
        "schema_version": 1,
        "experiment": "fixed-law transition acquisition and ambiguity-preserving word queries",
        "python": sys.version, "platform": platform.platform(),
        "source_revisions": {"NABT_base": "f48012ec15aa30746c38c706512fc1403101df3d",
                             "Taaqol-GPT_audited": "91dad107a7d56e6e05cce4ab54c3d63e5bdf5482"},
        "acquisition_status": result.status, "rounds": [asdict(r) for r in result.rounds],
        "verification": asdict(result.model.verification),
        "elapsed_seconds_single_run": elapsed,
        "timing_scope": "one end-to-end process-local acquisition run; not a performance benchmark",
        "ambiguity": ambiguity,
        "limits": ["fixed installed law, not new linguistic rule discovery",
                   "source hash identifies bytes, not authority or independent testimony",
                   "this JSON does not itself establish that Lean was run",
                   "Python implementation refinement is separate from the Lean artifact proof"],
    }
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
        print(args.output)
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
