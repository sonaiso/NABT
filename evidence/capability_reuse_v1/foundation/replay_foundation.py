"""Record authored demonstrations through NABT's existing native entry points.

This is an evidence recorder, not a new language or inference implementation.
Existing result files are never overwritten. The demonstrations do not measure
unseen Arabic coverage or prove that a binary was rebuilt from its source.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")


def progressive_cases():
    source = {"source_id": 1, "revision": 1, "scope_id": 1,
              "atomization_id": 1, "atoms": ["C", "V", "C"]}
    support = {"source_id": 2, "revision": 1, "scope_id": 1,
               "atomization_id": 1, "atoms": ["authored interpreted premise"]}
    tag = {"rule_id": 8, "reading_id": 4, "class_id": 10, "requirements": []}

    def atom(index):
        return {"op": "atom", "source": deepcopy(source),
                "before": source["atoms"][:index], "value": source["atoms"][index],
                "after": source["atoms"][index + 1:]}

    joined = {"op": "join", "tag": tag, "left": atom(0), "right": atom(1)}

    def receipt(target, number, positive=True):
        return {"target": deepcopy(target), "requirement": 0,
                "positive": positive, "witness_id": number,
                "supports": [{"source": deepcopy(support), "span": {
                    "source_id": 2, "revision": 1, "scope_id": 1,
                    "atomization_id": 1, "start": 0, "stop": 1}}]}

    positive = receipt(joined, 100)
    negative = receipt(joined, 101, False)
    lift = {"op": "lift", "tag": {**tag, "class_id": 11}, "child": deepcopy(joined)}
    substitution = {"op": "substitute", "tag": {**tag, "rule_id": 9},
                    "replacement": ["X"], "child": deepcopy(joined)}

    def derive(tree, interpreted=(), offered=(), **extra):
        return {"op": "derive", "tree": tree, "inventory": [source, support],
                "interpreted": list(interpreted), "offered": list(offered), **extra}

    foreign = deepcopy(positive)
    foreign["target"]["tag"]["reading_id"] = 5
    lift_receipt = receipt(lift, 102)
    substitute_receipt = receipt(substitution, 103)
    return [
        ("a116", {"op": "alphabet"}, {"carriers": 29, "cells": 116,
            "non_sukun_cells": 87, "sukun_cells": 29, "all_cells_are_phonetic_cv": False}),
        ("left_alone", {"op": "cell_effect", "cells": [84, 11, 11], "mode": "waqf", "entry": 0},
            {"sound_shape_accepted": True, "exit": 35}),
        ("right_alone", {"op": "cell_effect", "cells": [84], "mode": "waqf", "entry": 0},
            {"sound_shape_accepted": True, "exit": 1}),
        ("concatenation", {"op": "cell_effect", "cells": [84, 11, 11, 84], "mode": "waqf", "entry": 0},
            {"sound_shape_accepted": False, "exit": 96}),
        ("complete_but_pending", {"op": "forest_assess", "source": source, "tag": tag,
            "start": 0, "length": 3, "max_atoms": 3, "inventory": [source],
            "interpreted": [], "offered": []}, {"candidate_count": 2, "enumeration": "COMPLETE",
            "determination": "UNRESOLVED", "pending_count": 2, "necessary_within_domain": False}),
        ("join_missing_premise", derive(joined), {"verdict": "UNKNOWN", "reconstruction_matches": True}),
        ("join_exact_premise", derive(joined, [positive], [positive]),
            {"verdict": "LICENSED", "reconstruction_matches": True}),
        ("negative_not_hidden", derive(joined, [positive, negative], [positive]),
            {"verdict": "REJECTED", "conflict": True}),
        ("foreign_reading", derive(joined, [foreign], [foreign]), {"verdict": "UNKNOWN"}),
        ("lift_missing_child_premise", derive(lift, [lift_receipt], [lift_receipt]),
            {"verdict": "UNKNOWN"}),
        ("lift_complete_chain", derive(lift, [positive, lift_receipt], [positive, lift_receipt]),
            {"verdict": "LICENSED", "class_id": 11, "rank": 2, "undo_source": ["C", "V", "C"]}),
        ("substitute_restores_original", derive(substitution, [positive, substitute_receipt],
            [positive, substitute_receipt]), {"verdict": "LICENSED", "output": ["X"],
            "raw": ["C", "V"], "undo_source": ["C", "V", "C"]}),
        ("substitute_altered_output", derive(substitution, [positive, substitute_receipt],
            [positive, substitute_receipt], seen=["wrong"]),
            {"verdict": "LICENSED", "undo_raw": None, "undo_source": None}),
    ]


def execute(output, name, binary, cases):
    requests = b"".join((json.dumps(request, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
                        for _, request, _ in cases)
    (output / (name + ".requests.jsonl")).write_bytes(requests)
    run = subprocess.run([str(binary)], input=requests, capture_output=True, timeout=30)
    (output / (name + ".responses.jsonl")).write_bytes(run.stdout)
    (output / (name + ".stderr.txt")).write_bytes(run.stderr)
    rows = [json.loads(line) for line in run.stdout.splitlines()]
    measured = []
    if len(rows) != len(cases):
        raise RuntimeError("native response count changed; raw output retained")
    for (case_id, request, expected), response in zip(cases, rows, strict=True):
        actual = {key: response.get(key) for key in expected}
        equal = json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True)
        measured.append({"id": case_id, "op": request["op"], "expected_projection": expected,
                         "observed_projection": actual,
                         "pass": run.returncode == 0 and not run.stderr and response.get("status") == "OK" and equal})
    return {"binary": binary.relative_to(ROOT).as_posix(), "binary_sha256": sha(binary),
            "exit_code": run.returncode, "case_count": len(cases), "cases": measured,
            "passed": sum(item["pass"] for item in measured)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    from tools.recursive_bridge import morphology_request

    original = ROOT / "evidence/recursive_algebra/imported_v1/bundle/RecursiveLicensedAlgebra.lean"
    native = ROOT / "formal/Nabt/RecursiveLicensedAlgebra.lean"
    original_bytes = original.read_bytes()
    renamed = original_bytes.replace(b"namespace RecursiveLicensedAlgebra", b"namespace Nabt.RecursiveLicensedAlgebra").replace(
        b"end RecursiveLicensedAlgebra", b"end Nabt.RecursiveLicensedAlgebra")
    inputs = ["formal/Nabt/" + name + ".lean" for name in (
        "Cell", "Sequence", "Bridges", "Transition", "Law", "Count", "UnitCarrier",
        "UnitDiscovery", "LicensedDerivation", "ProsodicUnits", "BinaryUnitDomain",
        "RecursiveLicensedAlgebra", "RecursiveSourceBridge", "SemanticInference", "MeaningPreservation")]
    inputs += ["formal/ProgressiveUnitProbe.lean", "formal/RecursiveBridgeProbe.lean",
               "src/nabt/data/law.json", "src/nabt/machine.py", "src/nabt/codec.py",
               "src/nabt/bridges.py", "tools/recursive_bridge.py", "formal/theorems.json",
               "formal/lean-toolchain", "evidence/recursive_algebra/imported_v1/IMPORT.json",
               original.relative_to(ROOT).as_posix(),
               "evidence/recursive_algebra/imported_v1/Root_to_Sentence_Algebra_Evidence_2026-10-24.zip",
               Path(__file__).resolve().relative_to(ROOT).as_posix()]
    manifest = [{"path": path, "sha256": sha(ROOT / path), "bytes": (ROOT / path).stat().st_size} for path in inputs]
    dump(output / "source_inventory.json", manifest)
    request = morphology_request("كَاتِبٌ", source_id="authored_foundation", scope="foundation_demo")
    dump(output / "authored_cases.json", {"scope": "EXPOSED_AUTHORED_CONTRACT_DEMONSTRATIONS_NOT_ARABIC_COVERAGE",
         "progressive": [{"id": name, "request": value, "expected_projection": expected}
                         for name, value, expected in progressive_cases()],
         "recursive_source": {"text": "كَاتِبٌ", "source_id": "authored_foundation", "scope": "foundation_demo"}})
    result = {
        "schema": "nabt.foundation-reuse-demonstration.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "scope": "EXPOSED_AUTHORED_CONTRACT_DEMONSTRATIONS_NOT_ARABIC_COVERAGE",
        "new_native_build_performed": False,
        "original_kernel_sha256": sha(original), "native_kernel_sha256": sha(native),
        "namespace_only_equivalence": renamed == native.read_bytes(),
        "progressive": execute(output, "progressive", ROOT / "formal/.lake/build/bin/progressiveUnitProbe", progressive_cases()),
        "recursive": execute(output, "recursive", ROOT / "formal/.lake/build/bin/recursiveBridgeProbe", [
            ("actual_source_morphology_projection", request,
             {"verdict": "SOURCE_ONLY", "source_bound": True, "linguistic_ready": False, "grammar_certified": False})]),
        "limits": ["No new theorem or language law", "Binary hashes identify executed programs, not a fresh compiler provenance proof",
                   "Structural source projection does not instantiate CertifiedBridge",
                   "Supplied interpreted premises are authored; not acquired from independent Arabic observations"],
    }
    result["all_demonstrations_pass"] = (result["namespace_only_equivalence"] and all(
        result[name]["passed"] == result[name]["case_count"] for name in ("progressive", "recursive")))
    dump(output / "result.json", result)
    print(json.dumps({"path": str(output / "result.json"), "all_demonstrations_pass": result["all_demonstrations_pass"],
                      "progressive": result["progressive"]["passed"], "recursive": result["recursive"]["passed"]}))


if __name__ == "__main__":
    main()
