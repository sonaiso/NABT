#!/usr/bin/env python3
"""Replay traceability observations without rebuilding or executing native Lean.

This evidence script imports trusted measurement/catalogue APIs. It is separate
from the static Python analyzer's no-import population and grants no static
analysis, runtime, linguistic or proof authority. Hashes identify sampled source
bytes; they do not attest loaded bytecode or provide atomic execution isolation.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Intentionally trusted measurement APIs, never arbitrary inspected modules.
from tools import code_entropy, proof_catalog
from tools.grammar_catalog import catalog as source_catalog

SCHEMA = "nabt.strategic-traceability-observations.v1"
REGISTRY = "evidence/aligned_acquisition_v1/source_evidence.json"
PIN_HOLDER = "tools/aligned_acquisition.py"


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _local(root, relative):
    if (type(relative) is not str or not relative or
            PurePosixPath(relative).is_absolute() or
            PurePosixPath(relative).as_posix() != relative or
            ".." in PurePosixPath(relative).parts):
        raise ValueError("expected canonical repository-relative path")
    path = root / relative
    if path.resolve() != path:
        raise ValueError("symlinked or nonlocal input: " + relative)
    return path


def _check_hashes(root, expected):
    stale = [relative for relative, fingerprint in expected.items()
             if _sha(_local(root, relative).read_bytes()) != fingerprint]
    if stale:
        raise ValueError("source files changed or differ from snapshot: " + repr(stale))


def formal_observations(root, selected_proof_reference):
    """Inspect a source-matching stored snapshot, not fresh compiled evidence."""
    root = Path(root).resolve()
    path = _local(root, selected_proof_reference)
    snapshot_bytes = path.read_bytes()
    compiled = json.loads(snapshot_bytes)
    if compiled["schema"] != "nabt.compiled-proof-catalog.v1":
        raise ValueError("unexpected compiled catalogue schema")

    def check_snapshot():
        _check_hashes(root, compiled["inputs"])
        if path.read_bytes() != snapshot_bytes:
            raise ValueError("stored formal snapshot changed during replay")

    check_snapshot()
    manifest = json.loads((root / "formal/theorems.json").read_text())["theorems"]
    rows = compiled["theorems"]
    if [row["name"] for row in rows] != manifest or len(set(manifest)) != len(manifest):
        raise ValueError("compiled snapshot differs from unique theorem manifest")
    names = set(manifest)
    source = source_catalog.build_catalog(root=root)
    check_snapshot()
    source_inputs = {row["path"]: row["sha256"] for row in source["inputs"]}
    _check_hashes(root, source_inputs)
    if source_inputs["formal/theorems.json"] != compiled["inputs"]["formal/theorems.json"]:
        raise ValueError("source and proof catalogues use different manifests")
    projections = {}
    for field in ("proof_dependencies", "type_dependencies"):
        vertices = sorted(names)
        edges = sorted({(row["name"], dep) for row in rows for dep in row[field]
                        if dep in names})
        outside = sorted({dep for row in rows for dep in row[field]
                          if dep.startswith("Nabt.") and dep not in names})
        projections[field] = {
            "vertices": vertices, "edges": edges,
            "outside_nabt_constants": outside,
            "outside_nabt_constant_count": len(outside),
            "scope": "DIRECT_CONSTANT_REFERENCES_BETWEEN_ADVERTISED_THEOREMS_ONLY",
            "metrics": code_entropy.graph_metrics(vertices, edges),
        }
    rules = source["rules"]
    operators = [row for row in rules if row["runtime_rule_id"] is not None]
    supplied = [name for row in rules + source["items"] for name in row["theorem_names"]]
    return {
        "authority": "SOURCE_MATCHING_STORED_INDEX_AND_REPLAYED_SOURCE_METADATA_ONLY",
        "native_rebuilt": False, "atomic_snapshot_guaranteed": False,
        "snapshot": selected_proof_reference,
        "snapshot_sha256": _sha(snapshot_bytes),
        "compiled_catalog_sha256": proof_catalog.digest(compiled),
        "compiled_counts": compiled["counts"],
        "source_catalog_sha256": source_catalog.catalog_sha256(source),
        "source_catalog_inputs": source_inputs,
        "projections": projections,
        "source_linkage": {
            "scope": "AUTHORED_SOURCE_CATALOGUE_LINKS_NOT_RUNTIME_REFINEMENT",
            "source_policy_rules": len(rules),
            "source_policy_rules_with_supplied_theorem_links": sum(bool(r["theorem_names"]) for r in rules),
            "runtime_operator_records": len(operators),
            "runtime_operator_records_with_supplied_theorem_links": sum(bool(r["theorem_names"]) for r in operators),
            "runtime_operator_ids_without_supplied_theorem_links": sorted(r["runtime_rule_id"] for r in operators if not r["theorem_names"]),
            "runtime_operator_ids_without_implemented_scope": sorted(r["runtime_rule_id"] for r in operators if not isinstance(r.get("implemented_scope"), str) or not r["implemented_scope"].strip()),
            "unresolved_supplied_names": sorted(set(supplied) - names),
            "missing_link_implies_missing_theorem": False,
        },
    }


def acquisition_source_observations(root):
    """Replay the registry's full-file identities and exact original spans."""
    root = Path(root).resolve()
    pin_source = _local(root, PIN_HOLDER).read_bytes()
    tree = ast.parse(pin_source, filename=PIN_HOLDER)
    assignments = [node for node in tree.body if isinstance(node, ast.Assign) and
                   any(isinstance(t, ast.Name) and t.id == "SOURCE_MANIFEST_SHA256"
                       for t in node.targets)]
    if (len(assignments) != 1 or not isinstance(assignments[0].value, ast.Constant) or
            type(assignments[0].value.value) is not str):
        raise ValueError("acquisition manifest pin is not one literal assignment")
    pin = assignments[0].value.value
    registry_raw = _local(root, REGISTRY).read_bytes()
    if _sha(registry_raw) != pin:
        raise ValueError("acquisition registry differs from installed source pin")
    registry = json.loads(registry_raw)
    if registry["schema"] != "nabt.aligned-acquisition-sources.v1":
        raise ValueError("unexpected acquisition registry schema")
    if len(registry["sources"]) != 5 or len(registry["passages"]) != 23:
        raise ValueError("declared acquisition source/span population changed")
    inputs = {PIN_HOLDER: _sha(pin_source), REGISTRY: _sha(registry_raw)}
    originals, sources = {}, []
    for row in registry["sources"]:
        identity = row["source_id"]
        filename = row["research_filename"]
        if type(identity) is not str or identity in originals:
            raise ValueError("duplicate or malformed acquisition source identity")
        if type(filename) is not str or PurePosixPath(filename).name != filename:
            raise ValueError("acquisition research filename must be a basename")
        relative = "src/nabt/data/source_evidence/" + filename
        raw = _local(root, relative).read_bytes()
        raw.decode("utf-8", "strict")
        if _sha(raw) != row["source_sha256"]:
            raise ValueError("acquisition original source hash mismatch: " + identity)
        inputs[relative] = row["source_sha256"]
        originals[identity] = (raw, row["source_sha256"])
        sources.append({"source_id": identity, "path": relative,
                        "sha256": row["source_sha256"], "bytes": len(raw)})
    seen, passages = set(), []
    for row in registry["passages"]:
        identity = row["id"]
        if type(identity) is not str or identity in seen:
            raise ValueError("duplicate or malformed acquisition passage identity")
        seen.add(identity)
        raw, fingerprint = originals[row["source_id"]]
        start, end = row["start"], row["end"]
        line_start, line_end = row["line_start"], row["line_end"]
        if (any(type(n) is not int for n in (start, end, line_start, line_end)) or
                not 0 <= start < end <= len(raw) or not 1 <= line_start <= line_end):
            raise ValueError("invalid acquisition span coordinates: " + identity)
        excerpt = raw[start:end]
        if (row["source_sha256"] != fingerprint or
                _sha(excerpt) != row["span_sha256"] or
                excerpt.decode("utf-8", "strict") != row["raw_text"] or
                raw[:start].count(b"\n") + 1 != line_start or
                raw[:end - 1].count(b"\n") + 1 != line_end):
            raise ValueError("acquisition original span differs: " + identity)
        passages.append({key: row[key] for key in
                         ("id", "source_id", "source_sha256", "start", "end",
                          "line_start", "line_end", "span_sha256")})
    _check_hashes(root, inputs)
    return {
        "scope": "FULL_FILE_IDENTITY_AND_EXACT_ORIGINAL_BYTES_NOT_INTERPRETATION_FIDELITY",
        "source_file_count": len(sources), "verified_passage_count": len(passages),
        "sources": sources, "passages": passages, "inputs": inputs,
        "coordinate_system": "zero-based half-open UTF-8 bytes; one-based inclusive source lines",
        "source_authenticity_established": False,
        "interpretation_fidelity_established": False,
    }


def build_report(root, proof_reference):
    root = Path(root).resolve()
    trusted = {
        "tools/code_entropy.py": code_entropy,
        "tools/proof_catalog.py": proof_catalog,
        "tools/grammar_catalog/catalog.py": source_catalog,
    }
    for relative, module in trusted.items():
        if Path(module.__file__).resolve() != _local(root, relative):
            raise ValueError("trusted measurement import has unexpected origin: " + relative)
    provenance_paths = list(trusted) + ["tools/grammar_catalog/__init__.py",
                                       "evidence/strategic_entropy_v1/reproduce_traceability.py"]
    hashes = {relative: _sha(_local(root, relative).read_bytes()) for relative in provenance_paths}
    report = {
        "schema": SCHEMA, "native_rebuilt": False,
        "authority": "EVIDENCE_REPRODUCTION_ONLY_NOT_STATIC_ANALYZER_OR_PROOF_AUTHORITY",
        "atomic_snapshot_guaranteed": False,
        "provenance": {
            "python_version": platform.python_version(),
            "trusted_source_hashes": hashes,
            "trusted_imported_apis": ["tools.code_entropy.graph_metrics",
                                      "tools.proof_catalog.digest",
                                      "tools.grammar_catalog.catalog.build_catalog",
                                      "tools.grammar_catalog.catalog.catalog_sha256"],
            "inspected_runtime_modules_imported": False,
            "loaded_bytecode_attested": False,
        },
        "formal": formal_observations(root, proof_reference),
        "acquisition_sources": acquisition_source_observations(root),
    }
    _check_hashes(root, hashes)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-reference", required=True,
                        help="repository-relative stored catalogue selected by current proof references")
    parser.add_argument("--output", type=Path, required=True,
                        help="new output path; existing files are never replaced")
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise FileExistsError("output already exists: " + str(args.output))
        report = build_report(ROOT, args.proof_reference)
        encoded = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(encoded)
        print(json.dumps({"ok": True, "schema": SCHEMA, "output": str(args.output),
                          "native_rebuilt": False,
                          "source_files": report["acquisition_sources"]["source_file_count"],
                          "passages": report["acquisition_sources"]["verified_passage_count"]}))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
