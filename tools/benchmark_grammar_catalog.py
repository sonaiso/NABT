#!/usr/bin/env python3
"""Measure retrieval against frozen minimum relevance judgments, not Arabic proof."""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
from time import perf_counter
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
GOLD_PATH = Path("evidence/grammar_catalog_v1/retrieval_gold.json")
GOLD_SHA256 = "329c26d918aa110aa9a6e4e777fff87539b45717badb2246bbdd3cc99b3a5d60"
INITIAL_REPORT_SHA256 = "cfd5908661e0567738b5df1707a7e384fd64ea1d1b081e2923a46a58773358c3"
CUTOFFS = (1, 3, 5, 10)


def load_gold(root: Path = ROOT, path: Path | None = None) -> dict:
    """Replay the frozen source judgments; a caller hash grants no authority."""
    raw = (path if path is not None else root / GOLD_PATH).read_bytes()
    if sha256(raw).hexdigest() != GOLD_SHA256:
        raise ValueError("Frozen retrieval gold changed; create a new benchmark version")
    gold = json.loads(raw)
    for entry in gold["corpus_inputs"]:
        if sha256((root / entry["path"]).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("Gold corpus input changed: " + entry["path"])
    counts = Counter(case["kind"] for case in gold["cases"])
    if dict(counts) != gold["expected_counts"]:
        raise ValueError("Gold category counts do not match the frozen protocol")
    if len({case["id"] for case in gold["cases"]}) != len(gold["cases"]):
        raise ValueError("Duplicate gold case identity")
    for case in gold["cases"]:
        refs = case["relevant_rule_ids"]
        if len(refs) != len(set(refs)):
            raise ValueError("Duplicate relevance identity")
        if bool(refs) == (case["kind"] == "outside_judged_catalog"):
            raise ValueError("Invalid judged relevance domain")
        replayed = []
        for witness in case["evidence"]:
            registry = json.loads((root / witness["registry_path"]).read_bytes())
            namespace = registry.get("policy_id", registry.get("schema"))
            replayed.append(namespace + "::" + witness["rule_id"])
            for span in witness["spans"]:
                # These frozen judgments use only the five named local books.
                if span["source_id"] not in {"qatr", "alfiyya", "sibawayhi", "ibn_aqil", "mughni"}:
                    raise ValueError("Source is outside this frozen benchmark")
                source = root / "src/nabt/data/source_evidence" / (span["source_id"] + ".txt")
                data = source.read_bytes()
                start, end = span["start"], span["end"]
                if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(data):
                    raise ValueError("Invalid source byte span")
                selected = data[start:end]
                if sha256(selected).hexdigest() != span["sha256"]:
                    raise ValueError("Gold source span changed")
                selected.decode("utf-8", errors="strict")
        if replayed != refs:
            raise ValueError("Gold identities and source witnesses disagree")
    return gold


def score_ranking(ranked: list[str], relevant: list[str], cutoffs=CUTOFFS) -> dict:
    """Recall of judged IDs only; unjudged IDs are not counted as false positives."""
    if type(ranked) is not list or type(relevant) is not list:
        raise ValueError("Rankings and relevance must be lists")
    if any(type(x) is not str or not x for x in ranked + relevant):
        raise ValueError("Rule identities must be nonempty strings")
    if len(ranked) != len(set(ranked)) or len(relevant) != len(set(relevant)):
        raise ValueError("Repeated rule identity would inflate retrieval metrics")
    if any(type(k) is not int or k <= 0 for k in cutoffs):
        raise ValueError("Cutoffs must be positive integers")
    wanted = set(relevant)
    hits = {str(k): len(wanted.intersection(ranked[:k])) for k in cutoffs}
    return {
        "judged_relevant_count": len(wanted),
        "judged_hits_at_k": hits,
        "recall_at_k": {k: value / len(wanted) if wanted else None for k, value in hits.items()},
        "reciprocal_rank": next((1 / i for i, key in enumerate(ranked, 1) if key in wanted), 0.0) if wanted else None,
    }


def _candidate_ids(result: dict) -> list[str]:
    if type(result) is not dict or result.get("authority") != "RETRIEVAL_ONLY" or result.get("exhaustive_language_claim") is not False:
        raise ValueError("Retriever returned an invalid authority claim")
    candidates = result.get("candidates")
    if type(candidates) is not list or any(type(c) is not dict or c.get("kind") != "rule" or "id" not in c for c in candidates):
        raise ValueError("Benchmark requires rule-scoped proposals")
    ids = [c["id"] for c in candidates]
    # Checking through the metric function rejects duplicate/non-string IDs.
    score_ranking(ids, [])
    return ids


def run_benchmark(catalog: dict, gold: dict, searcher: Callable) -> dict:
    """Execute a protocol without tuning; run CLI to enforce the installed gold pin."""
    installed = {row["rule_key"] for row in catalog["rules"]}
    judgments = [key for case in gold["cases"] for key in case["relevant_rule_ids"]]
    missing = sorted(set(judgments) - installed)
    rows = []
    began = perf_counter()
    for case in gold["cases"]:
        baseline_result = searcher(catalog, case["query"], limit=max(10, len(installed)), kind="rule")
        hinted_result = searcher(catalog, case["query"], limit=max(10, len(installed)),
                                 hints=case["adversarial_hints"], kind="rule")
        baseline, hinted = _candidate_ids(baseline_result), _candidate_ids(hinted_result)
        if set(baseline + hinted) - installed:
            raise ValueError("Retriever invented a rule identity")
        rows.append({
            "id": case["id"], "kind": case["kind"], "query": case["query"],
            "relevant_rule_ids": case["relevant_rule_ids"],
            "top_10": baseline[:10], "hinted_top_10": hinted[:10],
            "proposals_count": len(baseline),
            "ranking": baseline_result.get("ranking"), "hinted_ranking": hinted_result.get("ranking"),
            "metrics": score_ranking(baseline, case["relevant_rule_ids"]),
            "hinted_metrics": score_ranking(hinted, case["relevant_rule_ids"]),
            "hints_removed_baseline_candidates": sorted(set(baseline) - set(hinted)),
            "hints_preserved_ranking": baseline == hinted,
        })

    def aggregate(group):
        positive = [r for r in group if r["relevant_rule_ids"]]
        relevant_count = sum(len(r["relevant_rule_ids"]) for r in positive)
        def metrics(name):
            return {
                "macro_recall_at_k": {
                    str(k): sum(r[name]["recall_at_k"][str(k)] for r in positive) / len(positive) if positive else None
                    for k in CUTOFFS},
                "micro_recall_at_k": {
                    str(k): sum(r[name]["judged_hits_at_k"][str(k)] for r in positive) / relevant_count if relevant_count else None
                    for k in CUTOFFS},
                "mean_reciprocal_rank": sum(r[name]["reciprocal_rank"] for r in positive) / len(positive) if positive else None,
            }
        return {"queries": len(group), "positive_queries": len(positive), "judged_relevant_occurrences": relevant_count,
                "baseline": metrics("metrics"), "adversarial_hints": metrics("hinted_metrics")}

    return {
        "schema": "nabt.grammar-catalog.retrieval-benchmark.v1", "authority": "MEASURED_RETRIEVAL_ONLY",
        "gold_sha256": None,
        "gold_verified_by_cli": False,
        "retrieval_kind": "rule", "cutoffs": list(CUTOFFS),
        "ranking_limit": max(10, len(installed)),
        "mrr_scope": "Complete returned rule ranking, not truncated at ten",
        "protocol": gold["judgment_scope"], "independence": gold["independence"],
        "catalogue_relevant_ids_present": not missing, "missing_relevant_ids": missing,
        "soft_hint_nonfiltering_observed": all(not r["hints_removed_baseline_candidates"] for r in rows),
        "hint_ranking_invariant_observed": all(r["hints_preserved_ranking"] for r in rows),
        "aggregate": aggregate(rows),
        "by_kind": {kind: aggregate([r for r in rows if r["kind"] == kind]) for kind in sorted({r["kind"] for r in rows})},
        "outside_catalog": [{"id": r["id"], "proposals_count": r["proposals_count"], "top_10": r["top_10"]}
                            for r in rows if r["kind"] == "outside_judged_catalog"],
        "whole_arabic_complete": False, "semantic_retrieval_measured": False,
        "probability_calibration_measured": False, "language_license_granted": False,
        "elapsed_seconds": perf_counter() - began,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "src"))
    from tools.grammar_catalog.catalog import build_catalog, catalog_sha256
    from tools.grammar_catalog.retrieval import SearchIndex
    gold = load_gold()
    initial = ROOT / "evidence/grammar_catalog_v1/retrieval_benchmark_initial.json"
    if sha256(initial.read_bytes()).hexdigest() != INITIAL_REPORT_SHA256:
        raise ValueError("Initial benchmark evidence changed")
    began = perf_counter()
    catalog = build_catalog()
    index = SearchIndex(catalog)
    build_seconds = perf_counter() - began
    report = run_benchmark(catalog, gold, lambda _catalog, query, **kwargs: index.search(query, **kwargs))
    report["gold_sha256"] = GOLD_SHA256
    report["gold_verified_by_cli"] = True
    report["catalog_sha256"] = catalog_sha256(catalog)
    report["retrieval_code_sha256"] = sha256((ROOT / "tools/grammar_catalog/retrieval.py").read_bytes()).hexdigest()
    report["theorem_manifest_sha256"] = sha256((ROOT / "formal/theorems.json").read_bytes()).hexdigest()
    report["evaluation_phase"] = "POST_REVIEW_OF_INITIAL_RESULTS_NOT_BLIND"
    report["initial_report_sha256"] = INITIAL_REPORT_SHA256
    report["review_note"] = ("Initial untrusted hint fusion lowered macro Recall@10 from 1.0 to 0.35714285714285715. "
                             "After inspecting these scores, hints were removed from ranking and retained as diagnostics. "
                             "The same frozen gold is reused for a regression check, not a new held-out evaluation.")
    report["catalogue_and_index_build_seconds"] = build_seconds
    report["algorithm"] = {"baseline": "BM25 k1=1.2, b=0.75", "adversarial_hints": "diagnostic only; do not affect candidates or ranks",
                           "vector_stream": "absent", "index_reused_between_queries": True,
                           "search_projection": "Unicode marks and tatweel removed; alif variants unified; casefold; raw source unchanged"}
    rendered = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("schema", "aggregate", "catalogue_relevant_ids_present",
                     "soft_hint_nonfiltering_observed", "hint_ranking_invariant_observed", "whole_arabic_complete")}, ensure_ascii=False))
    return 0 if report["catalogue_relevant_ids_present"] and report["hint_ranking_invariant_observed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
