#!/usr/bin/env python3
"""Replay a scoped source inventory; do not grant a language license.

This command checks identity and structure, not Arabic correctness. In particular,
``scoped_implemented`` is a baseline mapping, not a successful test result.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "src/nabt/data/source_evidence/classical_rule_inventory_v1.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _integer(value: object) -> bool:
    return type(value) is int


def validate_inventory(document: dict, source_directory: Path) -> dict:
    """Validate an inventory against original bytes in ``source_directory``.

    Hashes are integrity witnesses within the recorded corpus acquisition. This
    function does not authenticate a previously unknown source or implementation.
    """
    _require(document.get("schema") == "nabt.classical-rule-inventory.v1", "unknown schema")
    _require(document.get("authority") == "AUDIT_METADATA_NOT_RUNTIME_LICENSING_AUTHORITY",
             "inventory must not grant runtime authority")
    sources = {}
    for source in document["sources"]:
        sid = source["source_id"]
        _require(isinstance(sid, str) and sid not in sources, "duplicate/invalid source ID")
        name = source["local_file"]
        _require(isinstance(name, str) and Path(name).name == name and name.endswith(".txt"),
                 "source path must be a local text basename")
        _require(re.fullmatch(r"[0-9a-f]{40}", source["commit"]) is not None,
                 "source commit must be immutable")
        _require(source["commit"] in source["original_url"], "URL must contain source commit")
        _require(bool(source["license_evidence"]), "license provenance missing")
        raw = (source_directory / name).read_bytes()
        _require(sha256(raw).hexdigest() == source["raw_sha256"], f"source hash mismatch: {sid}")
        normalized = unicodedata.normalize("NFC", raw.decode("utf-8")).encode("utf-8")
        _require(sha256(normalized).hexdigest() == source["normalized_sha256"],
                 f"normalized source hash mismatch: {sid}")
        sources[sid] = (raw, raw.splitlines(keepends=True))

    checked_spans = 0

    def replay_span(span: dict) -> None:
        nonlocal checked_spans
        _require(span["source_id"] in sources, "unknown source")
        raw, lines = sources[span["source_id"]]
        first, last, start, end = (span[k] for k in ("line_start", "line_end", "start", "end"))
        _require(all(_integer(x) for x in (first, last, start, end)), "span indexes must be integers")
        _require(1 <= first <= last <= len(lines), "line range outside source")
        _require(0 <= start < end <= len(raw), "byte range outside source")
        _require(start == sum(map(len, lines[:first - 1])) and end == sum(map(len, lines[:last])),
                 "line and byte spans disagree")
        selected = raw[start:end]
        _require(selected.decode("utf-8") == span["raw_text"], "source text changed")
        _require(sha256(selected).hexdigest() == span["sha256"], "span hash mismatch")
        _require(re.findall(r"PageV\d+P\d+", selected.decode()) == span["page_markers_in_span"],
                 "page markers changed")
        checked_spans += 1

    rule_ids = set()
    categories, statuses, implementations = Counter(), Counter(), Counter()
    for rule in document["rules"]:
        rid = rule["rule_id"]
        _require(isinstance(rid, str) and rid and rid not in rule_ids, "duplicate/invalid rule ID")
        rule_ids.add(rid)
        _require(rule["status"] in {"reviewed", "textual_discrepancy"}, "unknown rule status")
        _require(rule["category"] in {"imperative", "affix", "hamza", "weak", "gemination", "construction"},
                 "unknown rule category")
        for field in ("scope", "blockers", "boundary_mode", "interpretation_note", "formal_obligation"):
            _require(isinstance(rule[field], str) and bool(rule[field].strip()), f"missing {field}: {rid}")
        _require(bool(rule["source_spans"]), "rule requires original source evidence")
        for span in rule["source_spans"]:
            replay_span(span)
        for name in ("positive_cases", "negative_cases"):
            _require(bool(rule[name]), f"missing diagnostics: {rid}")
            for case in rule[name]:
                _require(isinstance(case["surface"], str) and bool(case["surface"]), "empty diagnostic")
                _require(bool(case["scope"]), "diagnostic scope missing")
        implementation = rule["implementation"]
        _require(implementation["status"] in {"scoped_implemented", "not_evaluated"},
                 "unknown implementation status")
        if implementation["status"] == "scoped_implemented":
            _require(bool(implementation["paths"]) and bool(implementation["scope"]),
                     "implementation mapping requires evidence and scope")
        if rule["status"] == "textual_discrepancy":
            _require(len(rule["source_spans"]) >= 2, "discrepancy requires comparison evidence")
            _require(implementation["status"] != "scoped_implemented", "disputed text cannot grant a rule")
        categories[rule["category"]] += 1
        statuses[rule["status"]] += 1
        implementations[implementation["status"]] += 1

    case_ids = set()
    reading_count = 0
    for case in document["reference_constructions"]:
        _require(case["case_id"] not in case_ids, "duplicate construction ID")
        case_ids.add(case["case_id"])
        _require(case["evaluation_status"] == "not_run", "reference material must not claim a run")
        for field in ("input", "input_layer", "adjudication", "independence"):
            _require(bool(case[field]), f"construction requires {field}")
        _require(bool(case["source_spans"]) and bool(case["excluded_alternatives"]),
                 "construction requires source and negative boundary")
        for span in case["source_spans"]:
            replay_span(span)
        alternatives = case["expected_alternatives"]
        _require(bool(alternatives), "empty expected reading set")
        _require(len({a["id"] for a in alternatives}) == len(alternatives), "duplicate alternative ID")
        for alternative in alternatives:
            _require(all(isinstance(alternative[k], str) and alternative[k]
                         for k in ("id", "surface", "analysis")), "invalid reference reading")
        reading_count += len(alternatives)

    return {
        "schema": "nabt.classical-rule-inventory-validation.v1",
        "valid": True,
        "meaning": "Source-byte/metadata replay only; not Arabic completeness or parsing accuracy.",
        "source_count": len(sources),
        "rule_denominator": len(rule_ids),
        "rule_ids": sorted(rule_ids),
        "categories": dict(sorted(categories.items())),
        "source_review_statuses": dict(sorted(statuses.items())),
        "baseline_implementation_mapping": dict(sorted(implementations.items())),
        "replayed_span_count": checked_spans,
        "reference_construction_count": len(case_ids),
        "reference_reading_count": reading_count,
        "reference_evaluation_status": "not_run",
        "universal_completeness_claim": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=DEFAULT)
    parser.add_argument("--source-directory", type=Path)
    args = parser.parse_args()
    try:
        document = json.loads(args.inventory.read_text(encoding="utf-8"))
        result = validate_inventory(document, args.source_directory or args.inventory.parent)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
