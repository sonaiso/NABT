#!/usr/bin/env python3
"""Build Lean and compare independent source projection and receipt admission.

This is a finite implementation-conformance check, not a theorem that Python,
Unicode processing, every Arabic spelling, or a source's truth is verified.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nabt import alphabet, foundation
from nabt.errors import NabtError


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def native_many(executable: Path, requests: list[dict]) -> list[dict]:
    completed = subprocess.run([str(executable)],
        input=("\n".join(wire(value) for value in requests) + "\n").encode("utf-8"),
        capture_output=True, timeout=60, check=True)
    lines = completed.stdout.decode("utf-8", "strict").splitlines()
    if len(lines) != len(requests):
        raise ValueError("native JSONL response count differs from its requests")
    return [json.loads(line) for line in lines]


def check(executable: Path) -> dict:
    installed = foundation.require_foundation("tools.check_foundation")
    native_identity = native_many(executable, [{"op": "identity"}])[0]
    expected_identity = {"law_id": foundation.LAW_ID, "alphabet_id": alphabet.ALPHABET_ID,
        "number_domain": foundation.NUMBER_DOMAIN, "shape_law_id": alphabet.LAW_ID,
        "carriers": list(alphabet.CARRIERS), "marks": list(alphabet.HARAKAT),
        "alphabet_size": alphabet.ALPHABET_SIZE}
    if wire(native_identity) != wire(expected_identity):
        raise ValueError("native foundation identity differs from the installed Python core")

    # The independent test module supplies a separate Arabic oracle. Here the
    # purpose is cross-implementation comparison, including all declared cells.
    cases = [carrier + mark for carrier in alphabet.CARRIERS for mark in alphabet.HARAKAT]
    cases += ["".join(cases), "", " ", "\t\r\n", "كَتَبَ", "كُتِبَ", "قُمْتُ", "كتب",
        "إِنْ جَاءَ خَلِيدٌ قُمْتُ", "جَآءَ", "رَجُلًا", "بَّ", "بَّ", "بََ", "بَُ", "بّّ",
        "َكَ", "َُ", "أَُعني", "«بَ»", "xَُ", "Latin", "😀", "ب\u200d", "بَ\v", "بَ\f"]
    rng = random.Random(20261026)
    fragments = ["بَ", "اْ", "ءَ", "كَ", "x", "َ", "ّ", "ً", "ٓ", "إِ", "ا", " ", "؟", "\n"]
    cases += ["".join(rng.choice(fragments) for _ in range(rng.randrange(1, 30))) for _ in range(64)]
    sources = [{"id": "conformance", "revision": "1", "text": text} for text in cases]
    reports = [foundation.inspect_source(source["text"], source_id=source["id"], revision=source["revision"])
               for source in sources]
    observed = native_many(executable, [{"op": "project", "source": source} for source in sources])
    for index, (expected, actual) in enumerate(zip(reports, observed)):
        if wire(expected) != wire(actual):
            raise ValueError(f"projection differs at case {index}: {cases[index]!r}")
    replayed = native_many(executable, [{"op": "check", "source": source, "receipt": report}
                                      for source, report in zip(sources, reports)])
    for index, result in enumerate(replayed):
        if result.get("certificate_checked") is not True or wire(result.get("observed")) != wire(reports[index]):
            raise ValueError(f"native receipt replay failed at case {index}")

    base = foundation.inspect_source("كَتَبَ", source_id="tamper", revision="1")
    proposals = []
    for key, value in (("law_id", "uninstalled"), ("alphabet_id", "mashru.dal.cells.v1"),
                       ("number_domain", "nabt.bijective116.v1"), ("status", "PARTIAL"),
                       ("number", "01144809"), ("number", "0"), ("cells", [True, 8, 4]),
                       ("raw_utf8", [0]), ("padding", 0)):
        changed = deepcopy(base)
        changed[key] = value
        proposals.append(changed)
    for key, value in (("id", "foreign"), ("revision", "2"), ("text", "كُتِبَ")):
        changed = deepcopy(base)
        changed["source"][key] = value
        proposals.append(changed)
    for key, value in (("cell", 116), ("cell", True), ("start_byte", 1), ("end_byte", 3)):
        changed = deepcopy(base)
        changed["pieces"][0][key] = value
        proposals.append(changed)
    results = native_many(executable, [{"op": "check", "source": base["source"], "receipt": report}
                                      for report in proposals])
    for index, (proposal, result) in enumerate(zip(proposals, results)):
        if (result.get("certificate_checked") is not False or
                foundation.verify_source_receipt(proposal, text=base["source"]["text"],
                                                 source_id="tamper", revision="1")):
            raise ValueError(f"mutated source receipt was admitted: {index}")

    binding = {"source": {"id": "book", "revision": "1", "text": "«كَتَبَ»"},
               "scope_id": "quote_1", "occurrence_id": "word_1", "reading_id": "active",
               "start_byte": 2, "end_byte": 14, "surface": "كَتَبَ"}
    operations = [{"op": "keep"}, {"op": "append", "suffix": [9]},
                  {"op": "replace", "index": 0, "cell": 85}]
    transforms = [foundation.make_transform(binding, operation) for operation in operations]
    native_transforms = native_many(executable, [{"op": "transform", "binding": binding, "operation": op}
                                                 for op in operations])
    for index, (expected, actual) in enumerate(zip(transforms, native_transforms)):
        if wire(expected) != wire(actual):
            raise ValueError(f"source-bound numeric transform differs at operation {index}")
    transform_checks = native_many(executable, [{"op": "check_transform", "binding": binding,
        "operation": op, "receipt": receipt} for op, receipt in zip(operations, transforms)])
    if any(row.get("certificate_checked") is not True for row in transform_checks):
        raise ValueError("native numeric transform replay failed")
    changed_transforms = []
    for field, value in (("scope_id", "quote_2"), ("occurrence_id", "word_2"),
                         ("reading_id", "passive"), ("start_byte", 0), ("end_byte", 13)):
        changed = deepcopy(transforms[1])
        changed["binding"][field] = value
        changed_transforms.append(changed)
    for field, value in (("id", "foreign"), ("revision", "2"), ("text", "«كُتِبَ»")):
        changed = deepcopy(transforms[1])
        changed["binding"]["source"][field] = value
        changed_transforms.append(changed)
    for field, value in (("output_cells", [1]), ("input_cells", [True, 8, 4]),
                         ("output_number", "0"), ("operation", {"op": "keep"}),
                         ("number_domain", "uninstalled"), ("law_id", foundation.LAW_ID)):
        changed = deepcopy(transforms[1])
        changed[field] = value
        changed_transforms.append(changed)
    changed_results = native_many(executable, [{"op": "check_transform", "binding": binding,
        "operation": operations[1], "receipt": changed} for changed in changed_transforms])
    for index, (receipt, result) in enumerate(zip(changed_transforms, changed_results)):
        if result.get("certificate_checked") is not False or foundation.check_transform(binding, operations[1], receipt):
            raise ValueError(f"mutated numeric transform was admitted: {index}")

    cuts = [("قُمْتُّ", "قُمْتُ", 0), ("قُمْتَُ", "قُمْتُ", 0),
            ("بََ", "بَ", 0), ("بَُ", "بَ", 0), ("بَتُ", "َتُ", 2)]
    cut_requests = []
    for source_text, surface, start in cuts:
        cut = deepcopy(binding)
        cut.update(source={"id": "cut", "revision": "1", "text": source_text},
                   start_byte=start, end_byte=start + len(surface.encode()), surface=surface)
        try:
            foundation.make_transform(cut, {"op": "keep"})
        except NabtError as exc:
            if exc.code != "INVALID_INPUT":
                raise ValueError("cluster cut did not fail at the source boundary") from exc
        else:
            raise ValueError("source cluster suffix was hidden by a truncated occurrence")
        # For complete cut prefixes, forge the previously accepted kind of
        # receipt: correct arithmetic for the slice, but an incomplete cluster.
        fake = deepcopy(transforms[0])
        if foundation.inspect_source(surface)["status"] == "COMPLETE":
            plain = deepcopy(cut)
            plain.update(source={"id": "cut", "revision": "1", "text": surface},
                         start_byte=0, end_byte=len(surface.encode()))
            fake = foundation.make_transform(plain, {"op": "keep"})
        fake["binding"] = deepcopy(cut)
        if foundation.check_transform(cut, {"op": "keep"}, fake):
            raise ValueError("a cut cluster receipt replayed")
        cut_requests += [{"op": "transform", "binding": cut, "operation": {"op": "keep"}},
                         {"op": "check_transform", "binding": cut, "operation": {"op": "keep"}, "receipt": fake}]
    if any(row.get("status") != "INVALID_INPUT" or row.get("certificate_checked") is not False
           for row in native_many(executable, cut_requests)):
        raise ValueError("native source-cluster boundary rejection differs")
    outside_reports, outside_requests = [], []
    for prefix, suffix in (("إِ", "جَآءَ"), ("x" * 5000, "?"), ("وَ", "هُ")):
        local = deepcopy(binding)
        surface = "قُمْتُ"
        local.update(source={"id": "local", "revision": "1", "text": prefix + surface + suffix},
                     start_byte=len(prefix.encode()), end_byte=len((prefix + surface).encode()), surface=surface)
        report = foundation.make_transform(local, {"op": "keep"})
        outside_reports.append(report)
        outside_requests.append({"op": "transform", "binding": local, "operation": {"op": "keep"}})
    if [wire(row) for row in native_many(executable, outside_requests)] != [wire(row) for row in outside_reports]:
        raise ValueError("unrelated source residuals incorrectly blocked a complete local transform")
    return {"schema": "nabt.foundation-conformance.v1", "ok": True,
            "law_id": foundation.LAW_ID, "installed_law_table_sha256": installed["law_table_sha256"],
            "all_cells_checked": alphabet.ALPHABET_SIZE, "source_cases": len(cases),
            "status_counts": dict(Counter(report["status"] for report in reports)),
            "valid_receipts_replayed": len(replayed), "mutated_receipts_rejected": len(proposals),
            "source_bound_transforms_replayed": len(transforms),
            "mutated_transform_bindings_rejected": len(changed_transforms),
            "source_cluster_cuts_rejected": len(cuts),
            "local_transforms_with_surrounding_material_checked": len(outside_reports),
            "scope": "FINITE_PYTHON_LEAN_REPRESENTATION_CONFORMANCE",
            "linguistic_completeness_established": False, "world_truth_established": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--native", type=Path, default=ROOT / "formal/.lake/build/bin/foundationProbe")
    parser.add_argument("--skip-build", action="store_true", help="Replay an already built executable; do not claim a fresh kernel build")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if not args.skip_build:
            subprocess.run([args.lake, "build", "Nabt", "foundationProbe"], cwd=ROOT / "formal", check=True)
        report = check(args.native.resolve())
        report["kernel_build_checked"] = not args.skip_build
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        report = {"schema": "nabt.foundation-conformance.v1", "ok": False, "error": str(exc)}
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
