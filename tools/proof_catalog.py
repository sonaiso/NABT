#!/usr/bin/env python3
"""Index compiled Lean statements and explicit proof dependencies, not Arabic truth.

Run after/beside the enforcing `tools/check_axioms.py` audit. A stored catalogue
is a review artefact; a caller-supplied name, digest or catalogue is never proof
authority. `build_catalog` builds current Lean sources before inspecting them.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
SCHEMA = "nabt.compiled-proof-catalog.v1"


def canonical_json(value: object) -> str:
    """Preserve JSON scalar types: true, 1, and 1.0 are distinct evidence."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def catalog_matches(candidate: object, expected: object) -> bool:
    # Python's container equality identifies False with 0 and True with 1.
    # Evidence replay compares the typed JSON encoding instead.
    return canonical_json(candidate) == canonical_json(expected)


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_export(log: str, manifest: list[str]) -> list[dict]:
    """Fail closed on omitted, repeated or additional compiled declarations."""
    if not manifest or len(set(manifest)) != len(manifest):
        raise ValueError("theorem manifest must be nonempty and unique")
    rows = [json.loads(line[len("NABT_PROOF "):]) for line in log.splitlines()
            if line.startswith("NABT_PROOF ")]
    counts = [line for line in log.splitlines() if line.startswith("NABT_PROOF_COUNT ")]
    if counts != [f"NABT_PROOF_COUNT {len(manifest)}"]:
        raise ValueError("compiled proof export did not finish exactly once")
    if [row.get("name") for row in rows] != manifest:
        raise ValueError("compiled declarations differ from the exact manifest")
    for row in rows:
        if not isinstance(row.get("statement_ast"), list) or not row["statement_ast"]:
            raise ValueError("missing compiled statement AST")
        for key in ("proof_dependencies", "type_dependencies", "axioms"):
            if (not isinstance(row.get(key), list)
                    or any(not isinstance(item, str) for item in row[key])):
                raise ValueError(f"malformed {key}")
        if not set(row["axioms"]) <= ALLOWED_AXIOMS:
            raise ValueError("unapproved axiom in compiled theorem")
        if type(row.get("universe_parameters")) is not int or row["universe_parameters"] < 0:
            raise ValueError("malformed universe parameter count")
    return rows


def summarize_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Canonicalize identical normalized ASTs; do not infer logical equivalence.

    A same-statement group uses a dependency sink as representative when one
    exists. Remaining ties use lexical name order, explicitly recorded. The
    public names and every proof edge are retained.
    """
    groups = defaultdict(list)
    entries = []
    for row in rows:
        entry = {key: value for key, value in row.items() if key != "statement_ast"}
        entry["statement_sha256"] = digest({
            "universe_parameters": row["universe_parameters"],
            "ast": row["statement_ast"],
        })
        for key in ("proof_dependencies", "type_dependencies", "axioms"):
            entry[key] = sorted(set(entry[key]))
        groups[entry["statement_sha256"]].append(entry)
        entries.append(entry)
    duplicates = []
    for fingerprint, group in sorted(groups.items()):
        names = {row["name"] for row in group}
        sinks = [row["name"] for row in group
                 if not (set(row["proof_dependencies"]) & names)]
        canonical = min(sinks or names)
        for row in group:
            row["canonical_name"] = canonical
            row["same_statement_dependencies"] = sorted(set(row["proof_dependencies"]) & names)
        if len(group) > 1:
            duplicates.append({
                "statement_sha256": fingerprint,
                "canonical_name": canonical,
                "members": sorted(names),
                "representative_policy": "unique_dependency_sink" if len(sinks) == 1
                                         else "lexical_tie_break",
            })
    return entries, duplicates


def build_catalog(root: Path = ROOT, lake: str = "lake") -> dict:
    root = Path(root).resolve()
    formal = root / "formal"
    subprocess.run([lake, "build", "Nabt"], cwd=formal, check=True,
                   capture_output=True, text=True)
    execution = subprocess.run([lake, "env", "lean", "ExportProofCatalog.lean"],
                               cwd=formal, check=True, capture_output=True, text=True)
    manifest = json.loads((formal / "theorems.json").read_text(encoding="utf-8"))["theorems"]
    entries, duplicates = summarize_rows(parse_export(execution.stdout, manifest))
    # Bind the catalogue to the current formal source and exporter, including
    # all imported NABT modules rather than only a theorem's immediate file.
    inputs = sorted(set(formal.rglob("*.lean")) - set((formal / ".lake").rglob("*.lean")))
    inputs.extend([formal / "theorems.json", formal / "lean-toolchain",
                   root / "tools" / "proof_catalog.py"])
    hashes = {str(path.relative_to(root)): file_sha(path) for path in sorted(inputs)}
    for entry in entries:
        module = entry["module"]
        if (not isinstance(module, str) or not module.startswith("Nabt.")
                or any(not part.isidentifier() for part in module.split("."))):
            raise ValueError("unexpected theorem module")
        source = f"formal/{module.replace('.', '/')}.lean"
        if source not in hashes:
            raise ValueError(f"missing source for compiled module {module}")
        entry["source_path"] = source
        entry["source_sha256"] = hashes[source]
    return {
        "schema": SCHEMA,
        "authority": "COMPILED_DECLARATION_INDEX_ONLY",
        "fingerprint_scope": "structural AST after binder-name/metadata erasure and positional universe renaming",
        "logical_equivalence_decided": False,
        "arabic_rule_equivalence_decided": False,
        "source_completeness_claim": False,
        "lean_toolchain": (formal / "lean-toolchain").read_text().strip(),
        "counts": {
            "advertised_declarations": len(entries),
            "normalized_statement_groups": len({entry["statement_sha256"] for entry in entries}),
            "same_statement_groups_with_multiple_names": len(duplicates),
            "redundant_statement_names": sum(len(group["members"]) - 1 for group in duplicates),
        },
        "inputs": hashes,
        "same_statement_groups": duplicates,
        "theorems": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    try:
        report = build_catalog(lake=args.lake)
        if args.check and not catalog_matches(
                json.loads(args.check.read_text(encoding="utf-8")), report):
            raise ValueError("stored proof catalogue differs from current compiled sources")
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, **report["counts"], "catalog_sha256": digest(report)}))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        if isinstance(exc, subprocess.CalledProcessError):
            print(exc.stdout or "")
            print(exc.stderr or "")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
