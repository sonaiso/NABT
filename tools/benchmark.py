#!/usr/bin/env python3
"""Record reproducible local timing and Python allocation measurements.

Cold means a fresh counting memo, with the immutable law table already loaded.
Tracemalloc runs separately from timings. Results are observations, not a
general hardware performance guarantee or proof of language coverage.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import random
import statistics
import sys
import time
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nabt.machine import MAX_WEIGHT, EXPECTED_TABLE_SHA256, Machine


def summary(samples):
    ordered = sorted(samples)
    return {"samples_seconds": samples, "median_seconds": statistics.median(samples),
            "p95_nearest_rank_seconds": ordered[math.ceil(0.95 * len(ordered)) - 1]}


def cpu_name():
    path = Path("/proc/cpuinfo")
    if path.is_file():
        for line in path.read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[-1].strip()
    return platform.processor() or "unreported"


def measure(mode, weight, repeats, sample_count, seed):
    Machine(mode)  # warm only the immutable table loader, not count memoization
    cold = []
    for _ in range(repeats):
        machine = Machine(mode)
        start = time.perf_counter()
        total = machine.count(weight)
        cold.append(time.perf_counter() - start)
    machine = Machine(mode)
    total = machine.count(weight)
    chosen = set()
    if total:
        chosen.update((0, total - 1))
    rng = random.Random(seed)
    wanted = min(total, max(sample_count, len(chosen)))
    while len(chosen) < wanted:
        chosen.add(rng.randrange(total))
    ranks = sorted(chosen)
    hot = []
    for _ in range(repeats):
        start = time.perf_counter()
        for rank in ranks:
            word = machine.unrank(weight, rank)
            if machine.rank(word) != rank:
                raise RuntimeError("Roundtrip failed during measurement")
        hot.append(time.perf_counter() - start)
    memory_machine = Machine(mode)
    tracemalloc.start()
    memory_machine.count(weight)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"mode": mode, "consonant_weight": weight, "count": str(total),
            "sampled_ranks": len(ranks), "seed": seed,
            "count_with_cold_memo": summary(cold), "rank_unrank_batch_with_warm_memo": summary(hot),
            "count_peak_python_allocated_bytes": peak,
            "peak_memory_scope": "tracemalloc Python allocations; excludes already loaded law table; not process RSS"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weight", type=int, choices=range(MAX_WEIGHT + 1), default=4)
    parser.add_argument("--repeats", type=int, choices=range(1, 101), default=7)
    parser.add_argument("--samples", type=int, choices=range(1, 10001), default=100)
    parser.add_argument("--seed", type=int, default=20261022)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(),
              "python": sys.version, "platform": platform.platform(), "cpu": cpu_name(),
              "table_sha256": EXPECTED_TABLE_SHA256, "repeats": args.repeats,
              "scope": "local measurement; no full-language or hardware-general claim",
              "runs": [measure(mode, args.weight, args.repeats, args.samples, args.seed)
                       for mode in ("waqf", "wasl")]}
    content = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
