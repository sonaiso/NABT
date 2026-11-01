"""Isolated performance differential, not the independent semantic oracle.

The reference tokenizer is copied from retrieval.py at d3cfba9. The proposed
character predicate cache exists only in this script. Both end-to-end runs
retain the production source/index/receipt validation paths; only the module's
tokens binding is temporarily replaced inside this process.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from functools import lru_cache
from hashlib import sha256
import inspect
import json
from pathlib import Path
import platform
import re
import statistics
import subprocess
import time
import unicodedata

from tools.grammar_catalog.catalog import build_catalog, catalog_sha256
from tools.grammar_catalog import retrieval
from tools.grammar_catalog.routing import build_routing_report, verify_routing_report

ROOT = Path(__file__).resolve().parents[3]
REFERENCE_HEAD = "d3cfba90e9cdbdc75faaaaf3a09866d12a243b9f"
CACHE_SIZE = 4096


def baseline_tokens(text):
    """Search-only projection: marks/tatweel removed, alif variants unified."""
    text = "".join(c for c in text if not unicodedata.category(c).startswith("M") and c != "ـ")
    text = text.translate(str.maketrans("أإآٱ", "اااا")).casefold()
    return re.findall(r"[^\W_]+", text, re.UNICODE)


@lru_cache(maxsize=CACHE_SIZE)
def candidate_is_mark(char):
    return unicodedata.category(char).startswith("M")


def candidate_tokens(text):
    text = "".join(c for c in text if not candidate_is_mark(c) and c != "ـ")
    text = text.translate(str.maketrans("أإآٱ", "اااا")).casefold()
    return re.findall(r"[^\W_]+", text, re.UNICODE)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def head():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def timed_corpus(function, texts):
    total_tokens = 0
    function_seconds = 0.0
    digest = sha256()
    started = time.perf_counter()
    for text in texts:
        before = time.perf_counter()
        words = function(text)
        function_seconds += time.perf_counter() - before
        total_tokens += len(words)
        digest.update(canonical(words))
        digest.update(b"\n")
    return {"tokenization_seconds": function_seconds,
            "wall_including_output_digest_seconds": time.perf_counter() - started,
            "total_tokens": total_tokens, "output_sha256": digest.hexdigest()}


def timed_end_to_end(function, query, frames):
    original = retrieval.tokens
    retrieval.tokens = function
    try:
        started = time.perf_counter()
        index = retrieval.SearchIndex()
        setup = time.perf_counter() - started
        before = time.perf_counter()
        report = build_routing_report(index, query, frames)
        build = time.perf_counter() - before
        before = time.perf_counter()
        verification = verify_routing_report(report, query=query, frames_by_rule=frames)
        verify = time.perf_counter() - before
        timing = {"setup_seconds": setup, "build_seconds": build,
                  "verify_seconds": verify, "total_seconds": time.perf_counter() - started,
                  "report_sha256": sha256(canonical(report)).hexdigest(),
                  "verification_sha256": sha256(canonical(verification)).hexdigest()}
        return timing, report, verification
    finally:
        retrieval.tokens = original


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.rounds <= 10:
        parser.error("--rounds must be in 1..10")
    if args.output.exists():
        parser.error("--output must name a new observation")

    started = datetime.now(timezone.utc).isoformat()
    starting_head = head()
    source = ROOT / "tools/grammar_catalog/retrieval.py"
    source_before = sha256(source.read_bytes()).hexdigest()
    original_function = retrieval.tokens
    original_text = inspect.getsource(original_function)
    baseline_text = inspect.getsource(baseline_tokens).replace("def baseline_tokens(", "def tokens(", 1)

    catalog = build_catalog()
    documents = list(retrieval.iter_documents(catalog))
    texts = [row[2] for row in documents]
    codepoints = set()
    for text in texts:
        codepoints.update(text)

    # Direct per-document list equality is outside the timing loop. It is a
    # performance differential against the copied implementation, not gold.
    candidate_is_mark.cache_clear()
    mismatches = []
    for kind, identifier, text, _ in documents:
        if baseline_tokens(text) != candidate_tokens(text):
            mismatches.append({"kind": kind, "id": identifier})
    if mismatches:
        raise RuntimeError("Candidate tokenizer differs on installed corpus: " + repr(mismatches[:5]))

    rounds = []
    for number in range(args.rounds):
        order = ("baseline", "candidate") if number % 2 == 0 else ("candidate", "baseline")
        pair = {"round": number + 1, "order": list(order)}
        for name in order:
            if name == "candidate":
                candidate_is_mark.cache_clear()
            result = timed_corpus(baseline_tokens if name == "baseline" else candidate_tokens, texts)
            if name == "candidate":
                result["cache_after"] = candidate_is_mark.cache_info()._asdict()
            pair[name] = result
        if pair["baseline"]["output_sha256"] != pair["candidate"]["output_sha256"]:
            raise RuntimeError("Timed corpus outputs differ")
        rounds.append(pair)
        print(json.dumps({"stage": "corpus", **pair}, ensure_ascii=False), flush=True)

    warm = timed_corpus(candidate_tokens, texts)
    warm["cache_after"] = candidate_is_mark.cache_info()._asdict()
    query = "همزة الأمر"
    frames = json.loads((ROOT / "evidence/operator_context_v1/baseline/frames.json").read_text())
    baseline_e2e, baseline_report, baseline_verification = timed_end_to_end(baseline_tokens, query, frames)
    candidate_is_mark.cache_clear()
    candidate_e2e, candidate_report, candidate_verification = timed_end_to_end(candidate_tokens, query, frames)
    full_report_equal = canonical(baseline_report) == canonical(candidate_report)
    full_verification_equal = canonical(baseline_verification) == canonical(candidate_verification)
    if not full_report_equal or not full_verification_equal:
        raise RuntimeError("End-to-end report or replay differs")
    source_after = sha256(source.read_bytes()).hexdigest()
    if source_before != source_after or retrieval.tokens is not original_function:
        raise RuntimeError("Production reference changed during benchmark")

    baseline_median = statistics.median(r["baseline"]["tokenization_seconds"] for r in rounds)
    candidate_median = statistics.median(r["candidate"]["tokenization_seconds"] for r in rounds)
    result = {
        "schema": "nabt.operator-context.predicate-cache-performance.v1",
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "reference_head": REFERENCE_HEAD, "observed_start_head": starting_head, "observed_end_head": head(),
        "reference_retrieval_sha256": source_before, "final_retrieval_sha256": source_after,
        "production_files_changed": False, "production_tokens_binding_restored": True,
        "copied_baseline_source_matches_observed_production": baseline_text == original_text,
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(), "unicode_version": unicodedata.unidata_version,
        "platform": platform.platform(), "cache_maxsize": CACHE_SIZE,
        "corpus": {"catalog_sha256": catalog_sha256(catalog), "document_count": len(texts),
                   "input_codepoints": sum(map(len, texts)),
                   "input_utf8_bytes": sum(len(text.encode("utf-8")) for text in texts),
                   "distinct_codepoints": len(codepoints),
                   "byte_scope": "Exact strings supplied to tokens, including retrieval descriptions and repeated source excerpts; not unique book bytes."},
        "direct_document_list_equality": {"checked": len(texts), "mismatches": mismatches},
        "corpus_rounds": rounds, "candidate_warm_corpus": warm,
        "corpus_summary": {"baseline_median_tokenization_seconds": baseline_median,
                           "candidate_cold_median_tokenization_seconds": candidate_median,
                           "speedup_ratio": baseline_median / candidate_median,
                           "time_reduction_fraction": 1 - candidate_median / baseline_median},
        "end_to_end": {"query": query, "frames": frames, "budget": None,
                       "baseline": baseline_e2e, "candidate_cold": candidate_e2e,
                       "full_report_canonical_bytes_equal": full_report_equal,
                       "full_verification_canonical_bytes_equal": full_verification_equal,
                       "candidate_cache_after": candidate_is_mark.cache_info()._asdict(),
                       "speedup_ratio": baseline_e2e["total_seconds"] / candidate_e2e["total_seconds"],
                       "time_reduction_fraction": 1 - candidate_e2e["total_seconds"] / baseline_e2e["total_seconds"]},
        "limits": [
            "Differential performance observation only; independent semantic acceptance is a separately authored oracle.",
            "One local Python/Unicode version and installed corpus; no held-out language accuracy claim.",
            "Corpus rounds alternate order in one process; candidate cache is cleared before each cold run.",
            "Per-document tokenization timings exclude digest calculation; timer and scheduler noise remain.",
            "End-to-end baseline then candidate each run once; filesystem caches are already warm.",
            "No source, index, receipt, or authority cache is introduced; all existing production replay paths execute."
        ]
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "corpus_summary": result["corpus_summary"],
                      "end_to_end": result["end_to_end"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
