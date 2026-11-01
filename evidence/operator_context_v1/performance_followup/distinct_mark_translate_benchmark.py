"""One isolated distinct-character variant of the retained predicate benchmark.

This is a performance differential, not the independent semantic oracle. The
reference script/results are left unchanged. No production file is edited.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import inspect
import json
from pathlib import Path
import platform
import re
import statistics
import unicodedata

from evidence.operator_context_v1.performance_followup import predicate_cache_benchmark as reference
from tools.grammar_catalog.catalog import build_catalog, catalog_sha256
from tools.grammar_catalog import retrieval


def distinct_tokens(text):
    deletions = {ord(char): None for char in set(text)
                 if reference.candidate_is_mark(char) or char == "ـ"}
    text = text.translate(deletions)
    text = text.translate(str.maketrans("أإآٱ", "اااا")).casefold()
    return re.findall(r"[^\W_]+", text, re.UNICODE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must name a new observation")
    started = datetime.now(timezone.utc).isoformat()
    starting_head = reference.head()
    source = reference.ROOT / "tools/grammar_catalog/retrieval.py"
    source_before = sha256(source.read_bytes()).hexdigest()
    original_function = retrieval.tokens
    catalog = build_catalog()
    documents = list(retrieval.iter_documents(catalog))
    texts = [row[2] for row in documents]
    unique_counts = []
    deletion_counts = []
    all_characters = set()
    mismatches = []
    reference.candidate_is_mark.cache_clear()
    for kind, identifier, text, _ in documents:
        unique = set(text)
        all_characters.update(unique)
        unique_counts.append(len(unique))
        deletion_counts.append(sum(reference.candidate_is_mark(char) or char == "ـ" for char in unique))
        if reference.baseline_tokens(text) != distinct_tokens(text):
            mismatches.append({"kind": kind, "id": identifier})
    if mismatches:
        raise RuntimeError("Distinct-character candidate differs: " + repr(mismatches[:5]))

    rounds = []
    for number in range(3):
        order = ("baseline", "candidate") if number % 2 == 0 else ("candidate", "baseline")
        pair = {"round": number + 1, "order": list(order)}
        for name in order:
            if name == "candidate":
                reference.candidate_is_mark.cache_clear()
            result = reference.timed_corpus(reference.baseline_tokens if name == "baseline" else distinct_tokens, texts)
            if name == "candidate":
                result["cache_after"] = reference.candidate_is_mark.cache_info()._asdict()
            pair[name] = result
        if pair["baseline"]["output_sha256"] != pair["candidate"]["output_sha256"]:
            raise RuntimeError("Timed corpus outputs differ")
        rounds.append(pair)
        print(json.dumps({"stage": "corpus", **pair}, ensure_ascii=False), flush=True)

    query = "همزة الأمر"
    frames = json.loads((reference.ROOT / "evidence/operator_context_v1/baseline/frames.json").read_text())
    baseline_e2e, baseline_report, baseline_verification = reference.timed_end_to_end(reference.baseline_tokens, query, frames)
    reference.candidate_is_mark.cache_clear()
    candidate_e2e, candidate_report, candidate_verification = reference.timed_end_to_end(distinct_tokens, query, frames)
    full_report_equal = reference.canonical(baseline_report) == reference.canonical(candidate_report)
    full_verification_equal = reference.canonical(baseline_verification) == reference.canonical(candidate_verification)
    if not full_report_equal or not full_verification_equal:
        raise RuntimeError("End-to-end report or replay differs")
    source_after = sha256(source.read_bytes()).hexdigest()
    if source_before != source_after or retrieval.tokens is not original_function:
        raise RuntimeError("Production reference changed during benchmark")
    baseline_median = statistics.median(row["baseline"]["tokenization_seconds"] for row in rounds)
    candidate_median = statistics.median(row["candidate"]["tokenization_seconds"] for row in rounds)
    result = {
        "schema": "nabt.operator-context.distinct-mark-translate-performance.v1",
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "reference_head": reference.REFERENCE_HEAD,
        "observed_start_head": starting_head, "observed_end_head": reference.head(),
        "reference_retrieval_sha256": source_before, "final_retrieval_sha256": source_after,
        "production_files_changed": False, "production_tokens_binding_restored": True,
        "copied_baseline_source_matches_observed_production": inspect.getsource(reference.baseline_tokens).replace("def baseline_tokens(", "def tokens(", 1) == inspect.getsource(original_function),
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "reference_script_sha256": sha256(Path(reference.__file__).read_bytes()).hexdigest(),
        "candidate_source": inspect.getsource(distinct_tokens),
        "python": platform.python_version(), "unicode_version": unicodedata.unidata_version,
        "platform": platform.platform(), "cache_maxsize": reference.CACHE_SIZE,
        "corpus": {"catalog_sha256": catalog_sha256(catalog), "document_count": len(texts),
                   "input_codepoints": sum(map(len, texts)),
                   "input_utf8_bytes": sum(len(text.encode("utf-8")) for text in texts),
                   "distinct_codepoints": len(all_characters),
                   "byte_scope": "Exact strings supplied to tokens, including retrieval descriptions and repeated source excerpts; not unique book bytes."},
        "per_input_allocations": {"maximum_distinct_characters": max(unique_counts),
                                  "total_distinct_character_visits": sum(unique_counts),
                                  "maximum_deletion_map_entries": max(deletion_counts),
                                  "total_deletion_map_entries": sum(deletion_counts),
                                  "scope": "Ephemeral set/map per input; persistent predicate cache remains bounded by 4096 one-character keys."},
        "direct_document_list_equality": {"checked": len(texts), "mismatches": mismatches},
        "corpus_rounds": rounds,
        "corpus_summary": {"baseline_median_tokenization_seconds": baseline_median,
                           "candidate_cold_median_tokenization_seconds": candidate_median,
                           "speedup_ratio": baseline_median / candidate_median,
                           "time_reduction_fraction": 1 - candidate_median / baseline_median},
        "end_to_end": {"query": query, "frames": frames, "budget": None,
                       "baseline": baseline_e2e, "candidate_cold": candidate_e2e,
                       "full_report_canonical_bytes_equal": full_report_equal,
                       "full_verification_canonical_bytes_equal": full_verification_equal,
                       "candidate_cache_after": reference.candidate_is_mark.cache_info()._asdict(),
                       "speedup_ratio": baseline_e2e["total_seconds"] / candidate_e2e["total_seconds"],
                       "time_reduction_fraction": 1 - candidate_e2e["total_seconds"] / baseline_e2e["total_seconds"]},
        "limits": [
            "Differential performance observation only; independent semantic acceptance remains separate.",
            "Only one additional candidate was evaluated: per-input distinct-character deletion mapping.",
            "Three corpus rounds alternate order; candidate predicate cache is cleared before each cold run.",
            "One local Python/Unicode version; end-to-end baseline then candidate each run once with warm filesystem caches.",
            "Only retrieval.tokens is swapped during end-to-end runs; fresh indexes/source replay/receipt checks remain unchanged.",
            "No source, document, index, receipt, or approval cache is introduced."
        ]
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "corpus_summary": result["corpus_summary"],
                      "per_input_allocations": result["per_input_allocations"],
                      "end_to_end": result["end_to_end"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
