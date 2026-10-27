"""Post-development replay of three unchanged inherited scope examples.

This runner does not alter the thirty-case scorer or its historical denominator.
It measures the new envelope API alongside the still-unchanged diagnostic API.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from tools.benchmark_certified_natural_use import load_cases, _arguments
from tools.linguistic_truth.runtime import acquire
from tools.linguistic_truth.scopes import acquire_scope


def main():
    target = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(__file__).parent / "replay"
    target.mkdir(parents=True, exist_ok=False)
    cases, _ = load_cases()
    rows = []
    for case in cases:
        if case["id"] not in {"S03", "S04", "S05"}:
            continue
        text, options = case["input"]["text"], _arguments(case)
        old = acquire(text, **options)
        new = acquire_scope(text, source_id=options["source_id"], context=options["context"],
                            profile_id=options["profile_id"])
        wanted = case["target"]
        selected = [sense for row in new["selected_senses_scoped"]
                    if row["parent_start_byte"] == wanted["start_byte"]
                    and row["parent_end_byte"] == wanted["end_byte"]
                    for sense in row["sense_ids"]]
        old_selected = [sense for row in old["occurrences"]
                        if row["span"]["start_byte"] == wanted["start_byte"]
                        and row["span"]["end_byte"] == wanted["end_byte"]
                        for sense in row["selected_sense_ids"]]
        expected = ["ayn_spring"] if case["id"] == "S04" else []
        row = {"id": case["id"], "input_sha256": sha256(text.encode()).hexdigest(),
            "input": case["input"], "target": wanted,
            "old_diagnostic": old, "new_scope_receipt": new,
            "measurements": {
                "scope_matches_expected": new.get("envelope", {}).get("kind") == case["expected"]["scope"],
                "exact_envelope_native_checked": new["native_checked"] and any(
                    c["kind"] == "EXACT_SCOPE_ENVELOPE" for c in new["claims"]),
                "old_selected_ids": old_selected, "new_scoped_selected_ids": selected,
                "scoped_selection_matches_expected": selected == expected,
                "selected_sense_kernel_proved": new["intended_sense_kernel_proved"],
                "strict_language_accepted": new["strict_language_accepted"]}}
        path = target / (case["id"] + ".json")
        path.write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n")
        rows.append({"id": case["id"], "path": path.name,
                     "sha256": sha256(path.read_bytes()).hexdigest(), **row["measurements"]})
    summary = {"schema": "nabt.scope-inherited-replay.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_role": "POST_DEVELOPMENT_REPLAY_NOT_BLIND",
        "unchanged_corpus": {"path": "evidence/certified_natural_use_v1/independent_cases.json",
            "sha256": sha256((ROOT / "evidence/certified_natural_use_v1/independent_cases.json").read_bytes()).hexdigest()},
        "runtime_sha256": sha256((ROOT / "tools/linguistic_truth/runtime.py").read_bytes()).hexdigest(),
        "scope_api_sha256": sha256((ROOT / "tools/linguistic_truth/scopes.py").read_bytes()).hexdigest(),
        "native_binary_sha256": sha256((ROOT / "formal/.lake/build/bin/scopeAcquisition").read_bytes()).hexdigest(),
        "cases": rows,
        "scope_acquisition": {"numerator": sum(r["scope_matches_expected"] and r["exact_envelope_native_checked"] for r in rows), "denominator": 3},
        "quoted_target_selection_diagnostic": {"numerator": sum(r["id"] == "S04" and r["scoped_selection_matches_expected"] for r in rows), "denominator": 1},
        "strict_language_acceptance": {"numerator": sum(r["strict_language_accepted"] for r in rows), "denominator": 3},
        "legacy_thirty_case_scorer_changed": False,
        "limits": ["Exact envelope shape, not body syntax completeness.",
                   "Quoted sense selection still uses the diagnostic Python acquisition premises.",
                   "Two nonassertive scopes with empty selected senses are not positive intended-sense successes.",
                   "The historical 30-case and natural-use denominators are unchanged."]}
    (target / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: summary[key] for key in ("scope_acquisition", "quoted_target_selection_diagnostic", "strict_language_acceptance")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
