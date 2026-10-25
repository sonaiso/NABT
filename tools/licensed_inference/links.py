"""Resolve licensed-reading contracts against actual compiled declarations.

These are reviewable cross-references, not proofs of source interpretation.
Native execution, scholarly provenance and external-world adequacy stay apart.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools import proof_catalog
from .sources import ROOT, REVIEW_PATH, build_inventory

REUSED = (
    "Nabt.VerifiedReading.checked_closure_exact",
    "Nabt.SemanticInference.model_sound",
    "Nabt.BookCoverage.complete_readings_transfer",
    "Nabt.ArabicCoverage.exactness_transfers_with_reference_equivalence",
    "Nabt.MantuqMafhum.acquired_inference_grounded",
    "Nabt.QualifiedInference.checked_opposition_meaning",
    "Nabt.RationalInquiry.unbridged_world_is_deferred",
    "Nabt.Shakhsiyya3Rules.forward_condition_insufficient",
)


def compose(inventory, compiled):
    declarations = {row["name"]: row for row in compiled["theorems"]}
    if len(declarations) != len(compiled["theorems"]):
        raise ValueError("duplicate compiled declaration")
    new = [row for row in compiled["theorems"] if row["module"] == "Nabt.LicensedInference"]
    if not new or any(name not in declarations for name in REUSED):
        raise ValueError("missing compiled licensed-inference or reused contract")

    def contract(row):
        canonical = declarations.get(row["canonical_name"])
        if canonical is None or canonical["canonical_name"] != canonical["name"] or canonical["statement_sha256"] != row["statement_sha256"]:
            raise ValueError("unbound canonical declaration")
        for item in (row, canonical):
            if compiled["inputs"].get(item["source_path"]) != item["source_sha256"]:
                raise ValueError("unbound compiled contract source")
        return {key: row[key] for key in ("name", "canonical_name", "statement_sha256",
                "source_path", "source_sha256", "proof_dependencies", "axioms")}

    passages = {row["passage_id"] for row in inventory["passages"]}
    if len(passages) != len(inventory["passages"]):
        raise ValueError("duplicate source passage")
    for relation in inventory["relations"]:
        if not relation["passage_ids"] or not set(relation["passage_ids"]) <= passages:
            raise ValueError("unbound source motivation")
    return {
        "schema": "nabt.licensed-inference-proof-links.v1",
        "authority": "COMPILED_CONTRACT_AND_SOURCE_REFERENCE_INDEX_ONLY",
        "source_review_sha256": inventory["review_sha256"],
        "compiled_catalog_sha256": proof_catalog.digest(compiled),
        "contracts": [contract(row) for row in new],
        "related_existing_contracts": [contract(declarations[name]) for name in REUSED],
        "actual_existing_proof_dependencies": sorted({dep for row in new
            for dep in row["proof_dependencies"]
            if dep.startswith("Nabt.") and not dep.startswith("Nabt.LicensedInference.")}),
        "source_relations": inventory["relations"],
        "source_replay": inventory["source_replay"],
        "counts": {"new_module_declarations": len(new), "related_existing_contracts": len(REUSED),
                   "source_relations": len(inventory["relations"]),
                   "source_passages": len(passages), "unresolved_references": 0},
        "relationship_scope": "reviewed design motivations and actual theorem statements; not a proof of faithful translation",
        "source_translation_fidelity_proved": False,
        "all_arabic_complete": False, "world_truth_established": False,
    }


def build_links(*, root=ROOT, lake="lake"):
    root = Path(root).resolve()
    inventory = build_inventory(root)
    compiled = proof_catalog.build_catalog(root=root, lake=lake)
    for path, expected in compiled["inputs"].items():
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != expected:
            raise ValueError("compiled source changed during link construction")
    if hashlib.sha256((root / REVIEW_PATH).read_bytes()).hexdigest() != inventory["review_sha256"]:
        raise ValueError("source review changed during link construction")
    # Replay again so changes to a retained source during compilation also fail.
    if proof_catalog.canonical_json(build_inventory(root)) != proof_catalog.canonical_json(inventory):
        raise ValueError("retained source changed during link construction")
    return compose(inventory, compiled)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    report = build_links(lake=args.lake)
    if args.check and not proof_catalog.catalog_matches(json.loads(args.check.read_text()), report):
        raise ValueError("stored licensed-inference links differ")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": True, **report["counts"]}))


if __name__ == "__main__":
    main()
