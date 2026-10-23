#!/usr/bin/env python3
"""Verify the bundled law and source guards; this does not replace `lake build`.

With --lean-export, compare every JSON field against a freshly executed Lean
exporter. A digest locks a declared artifact; it is not evidence that the source
linguistic assumptions exhaust Arabic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_keys)


def lean_code_without_comments_or_strings(source):
    """Keep token positions while stripping nested Lean comments and strings."""
    result = []
    i, depth = 0, 0
    in_string = False
    while i < len(source):
        pair = source[i:i + 2]
        char = source[i]
        if depth:
            if pair == "/-":
                depth += 1
                result.extend("  ")
                i += 2
            elif pair == "-/":
                depth -= 1
                result.extend("  ")
                i += 2
            else:
                result.append("\n" if char == "\n" else " ")
                i += 1
        elif in_string:
            if char == "\\":
                result.extend("  ")
                i += 2
            else:
                if char == '"':
                    in_string = False
                result.append("\n" if char == "\n" else " ")
                i += 1
        elif pair == "/-":
            depth = 1
            result.extend("  ")
            i += 2
        elif pair == "--":
            end = source.find("\n", i)
            end = len(source) if end < 0 else end
            result.extend(" " * (end - i))
            i = end
        elif char == '"':
            in_string = True
            result.append(" ")
            i += 1
        else:
            result.append(char)
            i += 1
    if depth or in_string:
        raise ValueError("Unterminated Lean comment/string in source guard")
    return "".join(result)


def inspect_lean_sources():
    files = sorted(path for path in (ROOT / "formal").rglob("*.lean")
                   if ".lake" not in path.parts)
    if not files:
        raise ValueError("No Lean sources found")
    blocked = re.compile(r"\b(?:sorry|sorryAx|admit|axiom|native_decide|unsafe)\b")
    findings = []
    for path in files:
        code = lean_code_without_comments_or_strings(path.read_text(encoding="utf-8"))
        for match in blocked.finditer(code):
            line = code.count("\n", 0, match.start()) + 1
            findings.append(f"{path.relative_to(ROOT)}:{line}: {match.group()}")
    if findings:
        raise ValueError("Forbidden proof-source tokens: " + "; ".join(findings))
    return len(files)


def check(lean_export=None):
    from nabt.machine import EXPECTED_TABLE_SHA256, Machine
    from nabt.governors import EXPECTED_TABLE_SHA256 as GOVERNOR_TABLE_SHA256, installed_table
    from nabt.governor_reader import replay_source_policy
    from nabt.words import EXPECTED_TABLE_SHA256 as WORD_TABLE_SHA256, installed_table as word_table
    from nabt.word_reader import EXPECTED_POLICY_SHA256 as WORD_POLICY_SHA256, replay_policy
    from nabt.morphology import installed_table as morphology_table
    from nabt.morphology_reader import replay_policy as morphology_policy
    from nabt.text_evidence import installed_table as text_evidence_table
    from nabt.derivation import installed_registry as derivation_registry
    from nabt.nominal import installed_registry as nominal_registry
    from nabt.inflection import installed_registry as inflection_registry
    from nabt.inflection_reader import replay_inflection_policy
    from nabt.person_evidence import installed_registry as person_registry
    from nabt.discourse_laws import installed_registry as discourse_registry, replay_discourse_policy

    table_path = ROOT / "src" / "nabt" / "data" / "law.json"
    actual_hash = hashlib.sha256(table_path.read_bytes()).hexdigest()
    if not re.fullmatch(r"[0-9a-f]{64}", EXPECTED_TABLE_SHA256):
        raise ValueError("The law digest has not been pinned")
    if actual_hash != EXPECTED_TABLE_SHA256:
        raise ValueError("Bundled law bytes disagree with the runtime digest")
    digest_file = table_path.with_suffix(".sha256")
    if digest_file.exists():
        if digest_file.read_text().split()[0] != actual_hash:
            raise ValueError("The law.sha256 record disagrees with law.json")
    bundled = read_json(table_path)
    # The runtime additionally checks schema, domains and field types.
    machine = Machine()
    primitive_count = 0
    for q in range(97):
        for a in range(116):
            target, weight = machine.transition(q, a)
            if not (type(target) is int and 0 <= target < 97 and type(weight) is int and weight in (0, 1)):
                raise ValueError(f"Invalid primitive transition at {q}, {a}")
            primitive_count += 1
    matched = False
    if lean_export is not None:
        exported = read_json(Path(lean_export))
        # Canonical JSON distinguishes booleans from numeric 0/1 aliases.
        canonical = lambda value: json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        if canonical(exported) != canonical(bundled):
            raise ValueError("Bundled table is not equal to the complete Lean export")
        matched = True
    source_count = inspect_lean_sources()
    governor_table = installed_table()
    governor_policy = replay_source_policy()
    word_classes, word_rows = word_table()
    word_policy = replay_policy()
    morphology = morphology_table()
    morphology_source = morphology_policy()
    text_evidence = text_evidence_table()
    derivation = derivation_registry()
    nominal = nominal_registry()
    inflection = inflection_registry()
    inflection_policy = replay_inflection_policy()
    person = person_registry()
    discourse = discourse_registry()
    discourse_policy = replay_discourse_policy()
    return {"ok": True, "table_sha256": actual_hash, "primitive_transitions_checked": primitive_count,
            "lean_sources_guarded": source_count, "fresh_lean_export_compared": matched,
            "governor_table_sha256": GOVERNOR_TABLE_SHA256,
            "governor_inventory_rows": len(governor_table.entries),
            "governor_source_policy_sha256": governor_policy["policy_sha256"],
            "word_table_sha256": WORD_TABLE_SHA256,
            "word_declension_classes": len(word_classes), "word_class_case_rows": len(word_rows),
            "word_source_policy_sha256": WORD_POLICY_SHA256,
            "word_lexical_entries": len(word_policy["entries"]),
            "morphology_qualified_cause_rows": len(morphology["cause_rows"]),
            "morphology_source_rules": len(morphology_source["rules"]),
            "text_evidence_kind_rows": len(text_evidence["kind_rows"]),
            "text_evidence_activation_rows": len(text_evidence["receipt_rows"]),
            "derivation_patterns": len(derivation["patterns"]),
            "verb_paradigm_rows": len(derivation["paradigm_rows"]),
            "nominal_profiles": len(nominal["profile_rows"]),
            "nominal_receipt_rows": len(nominal["receipt_rows"]),
            "cardinal_rules": len(nominal["numeral_rows"]),
            "weak_root_masks": len(nominal["weak_rows"]),
            "manqus_rows": len(nominal["manqus_rows"]),
            "pronoun_projection_rows": len(nominal["pronoun_rows"]),
            "inflection_sign_rows": len(inflection["rows"]),
            "inflection_conditional_relations": len(inflection["relation_rows"]),
            "inflection_grammar_sha256": inflection_policy["policy_sha256"],
            "person_law_id": person["law_id"],
            "discourse_law_id": discourse["law_id"],
            "discourse_reference_rows": len(discourse["reference_rows"]),
            "discourse_assertion_rows": len(discourse["assertion_rows"]),
            "discourse_grammar_rules": len(discourse_policy["rules"]),
            "discourse_grammar_sha256": discourse_policy["policy_sha256"],
            "scope": "artifact integrity and source guard; kernel build is a separate required gate"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean-export", type=Path, help="JSON output from a freshly run Lean exporter")
    args = parser.parse_args()
    try:
        result = check(args.lean_export)
    except (OSError, ValueError, ImportError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
