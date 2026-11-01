"""Isolated prechange timing of two existing-owner positive identity paths.

This process changes module bindings only. It is not production code or an
independent semantic oracle. All source/index/replay work remains in its owner.
"""
from datetime import datetime, timezone
import hashlib
import inspect
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from nabt.corpus_sources import _same_json
from tools.grammar_catalog import retrieval, routing

OUTPUT = Path(__file__).with_name("identity_removal_observation_prechange_1535ca8.json")
if OUTPUT.exists():
    raise SystemExit("Refusing to overwrite a performance observation")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def head():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                   text=True).strip()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def identities():
    paths = ["tools/grammar_catalog/routing.py", "tools/grammar_catalog/retrieval.py",
             "tools/grammar_catalog/catalog.py", "src/nabt/corpus_sources.py",
             "src/nabt/classical_laws.py", ".github/workflows/ci.yml", "Makefile"]
    return {p: sha((ROOT / p).read_bytes()) for p in paths}


started = stamp()
start_head = head()
before = identities()
original_fresh = routing._fresh_index
original_tokens = retrieval.tokens
original_canonical = routing.catalog_canonical
fresh_source = inspect.getsource(original_fresh)
tokens_source = inspect.getsource(original_tokens)
fresh_needle = "            try:\n                same = catalog_canonical(row) == catalog_canonical(expected_row)"
assert fresh_source.count(fresh_needle) == 1
candidate_fresh_source = fresh_source.replace(fresh_needle,
    "            if installed_same_json(row, expected_row):\n"
    "                continue\n" + fresh_needle)
token_needle = '    text = "".join(c for c in text if not _is_mark(c) and c != "ـ")'
assert tokens_source.count(token_needle) == 1
candidate_tokens_source = tokens_source.replace(token_needle,
    '    if type(text) is not str or any(_is_mark(c) or c == "ـ" for c in set(text)):\n'
    '    ' + token_needle)

counts = {"canonical_calls": 0, "structural_calls": 0}


def counted_canonical(value):
    counts["canonical_calls"] += 1
    return original_canonical(value)


def installed_same_json(actual, expected):
    counts["structural_calls"] += 1
    return _same_json(actual, expected)


fresh_namespace = dict(routing.__dict__)
fresh_namespace.update(catalog_canonical=counted_canonical,
                       installed_same_json=installed_same_json)
exec(compile(candidate_fresh_source, "<isolated-existing-owner-comparison>", "exec"),
     fresh_namespace)
candidate_fresh = fresh_namespace["_fresh_index"]
token_namespace = dict(retrieval.__dict__)
exec(compile(candidate_tokens_source, "<isolated-removal-identity>", "exec"),
     token_namespace)
candidate_tokens = token_namespace["tokens"]

# Complete ordered token-list comparison is outside the timed three-stage runs.
population_index = retrieval.SearchIndex(root=ROOT)
baseline_tokens = []
candidate_token_lists = []
identity_rows = identity_codepoints = removal_rows = removal_codepoints = 0
for key, doc in population_index._docs.items():
    text = doc["search_text"]
    baseline_tokens.append([*key, original_tokens(text)])
    candidate_token_lists.append([*key, candidate_tokens(text)])
    if type(text) is str and not any(retrieval._is_mark(c) or c == "ـ" for c in set(text)):
        identity_rows += 1
        identity_codepoints += len(text)
    else:
        removal_rows += 1
        removal_codepoints += len(text)
assert candidate_token_lists == baseline_tokens
token_bytes = canonical(baseline_tokens)
assert canonical(candidate_token_lists) == token_bytes
corpus_comparison = {
    "documents": len(baseline_tokens),
    "ordered_token_lists_equal": True,
    "canonical_ordered_token_lists_equal": True,
    "canonical_ordered_token_lists_sha256": sha(token_bytes),
    "canonical_ordered_token_lists_bytes": len(token_bytes),
    "identity_rows": identity_rows,
    "identity_codepoints": identity_codepoints,
    "original_removal_rows": removal_rows,
    "original_removal_codepoints": removal_codepoints,
}
del baseline_tokens, candidate_token_lists, token_bytes, population_index

query = "همزة الأمر"
frames = json.loads((ROOT / "examples/operator_context_frames.json").read_text())
rounds = []
baseline_report = baseline_verification = None
try:
    routing.catalog_canonical = counted_canonical
    for round_number, order in enumerate((("baseline", "candidate"),
                                          ("candidate", "baseline"),
                                          ("baseline", "candidate")), 1):
        row = {"round": round_number, "order": list(order)}
        for mode in order:
            routing._fresh_index = original_fresh if mode == "baseline" else candidate_fresh
            retrieval.tokens = original_tokens if mode == "baseline" else candidate_tokens
            retrieval._is_mark.cache_clear()
            counts.update(canonical_calls=0, structural_calls=0)
            begin = time.perf_counter()
            index = retrieval.SearchIndex(root=ROOT)
            setup = time.perf_counter()
            report = routing.build_routing_report(index, query, frames)
            built = time.perf_counter()
            verification = routing.verify_routing_report(report, query=query,
                                                         frames_by_rule=frames, root=ROOT)
            finished = time.perf_counter()
            report_bytes = canonical(report)
            verification_bytes = canonical(verification)
            if baseline_report is None:
                assert mode == "baseline"
                baseline_report, baseline_verification = report_bytes, verification_bytes
            assert report_bytes == baseline_report
            assert verification_bytes == baseline_verification
            row[mode] = {
                "setup_seconds": setup - begin,
                "build_seconds": built - setup,
                "verify_seconds": finished - built,
                "total_seconds": finished - begin,
                "report_sha256": sha(report_bytes),
                "verification_sha256": sha(verification_bytes),
                "mark_cache_info": retrieval._is_mark.cache_info()._asdict(),
                **counts,
            }
        rounds.append(row)
finally:
    routing._fresh_index = original_fresh
    routing.catalog_canonical = original_canonical
    retrieval.tokens = original_tokens

after = identities()
assert before == after
assert head() == start_head
summary = {}
for field in ("setup_seconds", "build_seconds", "verify_seconds", "total_seconds"):
    baseline = statistics.median(row["baseline"][field] for row in rounds)
    improved = statistics.median(row["candidate"][field] for row in rounds)
    summary[field] = {"baseline_median": baseline, "candidate_median": improved,
                      "reduction_fraction": 1 - improved / baseline}

record = {
    "schema": "nabt.operator-context.identity-path-performance.v1",
    "started_utc": started, "finished_utc": stamp(), "head": start_head,
    "python": sys.version, "platform": platform.platform(),
    "inputs_before": before, "inputs_after": after, "inputs_unchanged": before == after,
    "script_sha256": sha(Path(__file__).read_bytes()),
    "original_fresh_source_sha256": sha(fresh_source.encode("utf-8")),
    "original_tokens_source_sha256": sha(tokens_source.encode("utf-8")),
    "candidate_fresh_source": candidate_fresh_source,
    "candidate_tokens_source": candidate_tokens_source,
    "existing_comparator": "nabt.corpus_sources._same_json",
    "query": query, "frames": frames, "budget": None,
    "catalog_sha256": json.loads(baseline_report)["catalog_sha256"],
    "corpus_comparison": corpus_comparison,
    "rounds": rounds, "summary": summary,
    "full_report_bytes_equal": True, "full_verification_bytes_equal": True,
    "production_bindings_restored": routing._fresh_index is original_fresh and
                                    routing.catalog_canonical is original_canonical and
                                    retrieval.tokens is original_tokens,
    "limits": [
        "One isolated combined candidate; no production edits or new cache/table/parser.",
        "Three local alternating pairs; filesystem caches may be warm and other work may contend.",
        "The existing character-classification LRU is cleared before each timed three-stage run.",
        "Exact built-in strings without removable characters skip only an identity removal pass.",
        "All other input types and strings with deletion candidates retain the original removal generator.",
        "Alif translation, casefold and regex remain in their original order.",
        "Only positive owner-state comparisons use the existing structural comparator.",
        "All state mismatches retain the original canonical fallback and exception path.",
        "Fresh SearchIndex, source validation, receipt checks and source rechecks remain present.",
        "Differential observation; independent frozen semantic acceptance remains separate.",
        "No CI deadline guarantee or general Arabic interpretation claim.",
    ],
}
with OUTPUT.open("x", encoding="utf-8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"output": str(OUTPUT.relative_to(ROOT)), "summary": summary,
                  "corpus": corpus_comparison, "source_unchanged": True,
                  "full_outputs_equal": True}, ensure_ascii=False, indent=2))
