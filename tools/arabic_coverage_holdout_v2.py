#!/usr/bin/env python3
"""Run the unchanged v1 evaluator on pre-execution-corrected v2 inputs."""
import argparse
from pathlib import Path
import sys

import arabic_coverage_holdout_v1 as evaluator


if __name__ == "__main__":
    evaluator.MATERIAL = evaluator.ROOT / "evidence/arabic_coverage/holdout_v2"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="New JSON result path; existing output is never replaced")
    args = parser.parse_args()
    sys.exit(evaluator.run(args.output.resolve()))
