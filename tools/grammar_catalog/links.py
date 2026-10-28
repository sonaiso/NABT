"""Join installed source references to freshly compiled canonical Lean nodes.

A crosslink states that an authored reference names an installed, compiled
Lean declaration. It does not prove that the declaration translates the cited
Arabic passage faithfully, that its premises hold for a sentence, or that all
rules/readings have been inventoried. No public API accepts a caller's proof
catalogue as authority.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from tools import proof_catalog
from tools.grammar_catalog import catalog as source_catalog

ROOT = source_catalog.ROOT
SCHEMA = "nabt.grammar-proof-links.v1"


class LinkError(ValueError):
    """An explicit source reference cannot be joined to compiled evidence."""


def _index(rows: list[dict], key: str) -> dict[str, dict]:
    result = {}
    for row in rows:
        identity = row[key]
        if type(identity) is not str or identity in result:
            raise LinkError(f"invalid or repeated {key}")
        result[identity] = row
    return result


def _compose(source: dict, compiled: dict) -> dict:
    """Internal pure join, separately tested with synthetic fixtures.

    Calling this helper on arbitrary dictionaries establishes nothing. The
    public entry point below obtains both arguments by independent replay.
    """
    source_inputs = _index(source["inputs"], "path")
    manifest_path = "formal/theorems.json"
    if source_inputs[manifest_path]["sha256"] != compiled["inputs"][manifest_path]:
        raise LinkError("source references and compiled export use different theorem manifests")
    declarations = _index(compiled["theorems"], "name")
    passages = _index(source["passages"], "passage_id")
    source_editions = _index(source["sources"], "source_key")
    canonical_members: dict[str, list[str]] = {}
    for name, declaration in declarations.items():
        canonical = declaration["canonical_name"]
        target = declarations.get(canonical)
        if (target is None or target["canonical_name"] != canonical or
                target["statement_sha256"] != declaration["statement_sha256"]):
            raise LinkError(f"invalid compiled canonical identity: {name}")
        for row in (declaration, target):
            if compiled["inputs"].get(row["source_path"]) != row["source_sha256"]:
                raise LinkError(f"compiled declaration has unbound source: {name}")
        canonical_members.setdefault(canonical, []).append(name)

    nodes, edges = [], []
    linked_passages: set[str] = set()
    linked_theorems: set[str] = set()
    referenced_names: set[str] = set()
    for kind, collection, id_key in (("rule", source["rules"], "rule_key"),
                                      ("item", source["items"], "item_id")):
        for row_id, row in sorted(_index(collection, id_key).items()):
            references = row["theorem_names"]
            if not references:
                continue
            if len(references) != len(set(references)):
                raise LinkError(f"repeated explicit theorem reference: {row_id}")
            pids = sorted(set(row["source_passage_ids"]))
            if not pids or any(pid not in passages for pid in pids):
                raise LinkError(f"missing passage for explicit source reference: {row_id}")
            nodes.append({
                "source_node_id": f"{kind}:{row_id}", "kind": kind,
                "catalogue_id": row_id, "title": row["title"],
                "source_passage_ids": pids,
                "scope": row.get("scope", row.get("description", "")),
                "reference_scope": "authored_explicit_reference_not_source_fidelity_proof",
            })
            if "operator_traceability" in row:
                nodes[-1]["implemented_scope"] = row["implemented_scope"]
                nodes[-1]["operator_traceability"] = row["operator_traceability"]
            linked_passages.update(pids)
            for name in sorted(references):
                if name not in declarations:
                    raise LinkError(f"source reference missing from compiled export: {name}")
                declaration = declarations[name]
                canonical = declaration["canonical_name"]
                target = declarations[canonical]
                identity = [kind, row_id, name]
                edges.append({
                    "edge_id": "source-proof:" + proof_catalog.digest(identity),
                    "source_node_id": f"{kind}:{row_id}",
                    "referenced_declaration": name,
                    "canonical_name": canonical,
                    "statement_sha256": declaration["statement_sha256"],
                    "source_path": declaration["source_path"],
                    "source_sha256": declaration["source_sha256"],
                    "canonical_source_path": target["source_path"],
                    "canonical_source_sha256": target["source_sha256"],
                    "aliases": sorted(n for n in canonical_members[canonical] if n != canonical),
                    "source_passage_ids": pids,
                    "relation": "explicit_reference_to_compiled_declaration",
                })
                linked_theorems.add(canonical)
                referenced_names.add(name)

    passage_nodes = []
    linked_editions: set[str] = set()
    for pid in sorted(linked_passages):
        passage = passages[pid]
        if passage["source_key"] not in source_editions:
            raise LinkError(f"passage edition is unresolved: {pid}")
        linked_editions.add(passage["source_key"])
        passage_nodes.append({key: passage[key] for key in
                              ("passage_id", "source_key", "source_id", "start", "end", "sha256")})
    proof_nodes = []
    for name in sorted(linked_theorems):
        declaration = declarations[name]
        proof_nodes.append({
            "canonical_name": name, "statement_sha256": declaration["statement_sha256"],
            "source_path": declaration["source_path"],
            "source_sha256": declaration["source_sha256"],
            "aliases": sorted(n for n in canonical_members[name] if n != name),
            "canonicalization_scope": compiled["fingerprint_scope"],
        })
    return {
        "schema": SCHEMA, "authority": "EVIDENCE_LINK_INDEX_ONLY",
        "source_catalog_sha256": source_catalog.catalog_sha256(source),
        "compiled_proof_catalog_sha256": proof_catalog.digest(compiled),
        "theorem_manifest_sha256": compiled["inputs"][manifest_path],
        "lean_toolchain": compiled["lean_toolchain"],
        "counts": {
            "explicit_reference_edges": len(edges),
            "source_reference_nodes": len(nodes),
            "linked_passage_nodes": len(passage_nodes),
            "linked_source_editions": len(linked_editions),
            "referenced_declaration_names": len(referenced_names),
            "canonical_theorem_nodes": len(proof_nodes),
            "compiled_declarations_in_full_catalogue": len(declarations),
            "unresolved_references": 0,
        },
        "source_nodes": sorted(nodes, key=lambda n: n["source_node_id"]),
        "passages": passage_nodes, "proof_nodes": proof_nodes,
        "edges": sorted(edges, key=lambda e: e["edge_id"]),
        "claims": {
            "explicit_references_resolve_to_compiled_declarations": True,
            "source_translation_fidelity_established": False,
            "free_text_premises_established": False,
            "logical_equivalence_decided": False,
            "whole_book_complete": False,
            "whole_arabic_complete": False,
        },
    }


def build_links(root: Path = ROOT, lake: str = "lake") -> dict:
    """Compile Lean, rebuild pinned sources, then join exact installed names.

    A stored JSON export is deliberately not an input. Compilation failures,
    missing declarations and differing snapshots are errors, never partial
    certificates of completeness.
    """
    root = Path(root).resolve()
    compiled = proof_catalog.build_catalog(root=root, lake=lake)
    source = source_catalog.build_catalog(root=root)
    # Detect files changing between the compiled export and the source replay.
    for relative, expected in compiled["inputs"].items():
        if sha256((root / relative).read_bytes()).hexdigest() != expected:
            raise LinkError(f"formal input changed during crosslink build: {relative}")
    return _compose(source, compiled)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    try:
        report = build_links(lake=args.lake)
        if args.check and not proof_catalog.catalog_matches(
                json.loads(args.check.read_text(encoding="utf-8")), report):
            raise LinkError("stored links differ from replayed sources and compiled proofs")
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, **report["counts"],
                          "link_catalog_sha256": proof_catalog.digest(report)}))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
