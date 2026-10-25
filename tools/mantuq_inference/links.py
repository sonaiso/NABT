"""Resolve reviewed policy references against freshly compiled Lean declarations.

Resolution is a provenance link, not a proof of faithful Arabic interpretation.
Even structural policies without source passages retain their explicit gap.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from tools import proof_catalog
from .inventory import ROOT, build_inventory
from .retrieval import inventory_sha256

ADAPTER_DECLARATIONS = (
    "Nabt.QualifiedInference.supported_exact",
    "Nabt.QualifiedInference.blocker_requires_explicit_negative",
    "Nabt.QualifiedInference.supported_replays_existing_rule",
    "Nabt.QualifiedInference.supported_rule_derivable",
    "Nabt.QualifiedInference.checked_opposition_meaning",
)


def _compose(inventory, compiled):
    declarations = {r["name"]: r for r in compiled["theorems"]}
    if len(declarations) != len(compiled["theorems"]):
        raise ValueError("Duplicate compiled declaration identity")
    edges = []
    for rule in inventory["rules"]:
        for name in rule["theorem_names"]:
            if name not in declarations:
                raise ValueError(f"Unresolved theorem reference: {name}")
            row = declarations[name]
            canonical = declarations.get(row["canonical_name"])
            if (canonical is None or canonical["canonical_name"] != row["canonical_name"] or
                    canonical["statement_sha256"] != row["statement_sha256"]):
                raise ValueError("Invalid canonical theorem identity")
            for item in (row, canonical):
                if compiled["inputs"].get(item["source_path"]) != item["source_sha256"]:
                    raise ValueError("Unbound compiled source")
            edges.append({"policy_id": rule["rule_id"], "profile": rule["profile"],
                          "source_passage_ids": rule["source_passage_ids"],
                          "source_context_only": rule["source_context_only"],
                          "referenced_declaration": name, "canonical_name": row["canonical_name"],
                          "statement_sha256": row["statement_sha256"],
                          "source_path": row["source_path"], "source_sha256": row["source_sha256"],
                          "relation": "reviewed_reference_to_compiled_declaration"})
    contracts = []
    for name in ADAPTER_DECLARATIONS:
        if name not in declarations:
            raise ValueError(f"Unresolved adapter declaration: {name}")
        row = declarations[name]
        if compiled["inputs"].get(row["source_path"]) != row["source_sha256"]:
            raise ValueError("Unbound compiled adapter source")
        contracts.append({"referenced_declaration": name,
                          "statement_sha256": row["statement_sha256"],
                          "source_path": row["source_path"], "source_sha256": row["source_sha256"],
                          "relation": "compiled_adapter_contract_not_source_translation"})
    return {"schema": "nabt.inference-proof-links.v1", "authority": "EVIDENCE_LINK_INDEX_ONLY",
            "inventory_sha": inventory_sha256(inventory),
            "compiled_catalog_sha256": proof_catalog.digest(compiled),
            "edges": edges, "adapter_contracts": contracts,
            "supplement_context_associations": inventory.get("supplement_policy_associations", []),
            "counts": {"policies": len(inventory["rules"]), "reference_edges": len(edges),
                       "canonical_declarations": len({r["canonical_name"] for r in edges}),
                       "compiled_adapter_contracts": len(contracts), "unresolved_references": 0},
            "source_translation_fidelity_established": False,
            "occurrence_classification_proved": False, "world_truth_established": False,
            "whole_arabic_complete": False}


def build_links(*, root=ROOT, lake="lake"):
    root = Path(root).resolve()
    compiled = proof_catalog.build_catalog(root=root, lake=lake)
    inventory = build_inventory(root)
    for relative, expected in compiled["inputs"].items():
        if sha256((root / relative).read_bytes()).hexdigest() != expected:
            raise ValueError("Formal source changed during crosslink build")
    return _compose(inventory, compiled)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    result = build_links(lake=args.lake)
    if args.check and not proof_catalog.catalog_matches(json.loads(args.check.read_text()), result):
        raise ValueError("Stored inference proof links differ from current compiled sources")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": True, **result["counts"]}))


if __name__ == "__main__":
    main()
