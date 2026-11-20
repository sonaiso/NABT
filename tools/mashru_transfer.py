"""Rebuild the Mashru extension of the current NABT compiled proof catalogue."""
import argparse
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import re
import subprocess

from tools import proof_catalog as core

ROOT = core.ROOT
LIB = ROOT / "vendor/mashru"
SELECTOR = ROOT / "integrations/current_proof_references.mk"


def reference():
    matches = re.findall(r"^NABT_PROOF_REFERENCE_DIR \?= (evidence/[\w/-]+)$",
                         SELECTOR.read_text(), re.M)
    if len(matches) != 1:
        raise ValueError("missing unique compiled reference directory")
    return ROOT / matches[0] / "mashru_proofs.json.gz"


def manifest():
    return json.loads((ROOT / "formal/theorems.json").read_bytes())


def upstream_digest():
    original = {}
    for package in ("vendor/mashru", "vendor/alghanem-a116"):
        root = ROOT / package
        for file in root.rglob("*.lean"):
            relative = file.relative_to(root)
            if relative.parts[0] in {"Aql", "Dal", "Faahis", "Jisr", "Madlul", "Nizam", "SLGE",
                                     "tahaqquq", "Qari", "A116", "Audit.lean", "AuditNabt.lean", "A116.lean"}:
                original[relative.as_posix()] = core.file_sha(file)
    for filename in ("LICENSE", "lean-toolchain"):
        original[filename] = core.file_sha(LIB / filename)
    return core.digest(original)


def validate_named_coverage(lake, registered, definitions):
    """Check source-named theorem declarations in every imported library module."""
    scanned = subprocess.run([lake, "env", "lean", "Discover.lean"], cwd=LIB,
                             stdout=subprocess.PIPE, check=True, text=True)
    lines = {}
    found = {}
    for line in scanned.stdout.splitlines():
        if not line.startswith("MASHRU_DECL "):
            continue
        name, module, kind, number, start, stop = json.loads(line[12:])
        found[name] = kind
        if name in registered or kind != "theorem":
            continue
        if module not in lines:
            package = module.split(".")[0]
            root = (ROOT / "formal" if package == "Nabt" else
                    ROOT / "vendor/alghanem-a116" if package == "A116" else LIB)
            lines[module] = (root / (module.replace(".", "/") + ".lean")).read_text().splitlines()
        source = lines[module][number - 1]
        if (source[start:stop].split(".")[-1] == name.split(".")[-1]
                and re.search(r"\b(?:theorem|lemma)\s*$", source[:start])):
            raise ValueError(f"unregistered named declaration {module}: {name}")
    if any(found.get(name) != "definition" for name in definitions):
        raise ValueError("upstream audited definitions changed kind")


def compile_reference(lake):
    config = manifest()
    transfer = config["libraries"]["mashru"]
    if upstream_digest() != transfer["source_tree_sha256"]:
        raise ValueError("vendored files differ from the pinned Mashru tree")
    for file, key in (("Audit.lean", "audit_sha256"), ("AuditNabt.lean", "kernel_audit_sha256")):
        if core.file_sha(LIB / file) != transfer[key]:
            raise ValueError(f"changed upstream audit {file}")
    release = set(re.findall(r"^#print axioms\s+(\S+)", (LIB / "Audit.lean").read_text(), re.M))
    inherited = set(re.findall(r"``(Nabt\.[\w.]+)", (LIB / "AuditNabt.lean").read_text()))
    reviews = set(transfer["research_countermodels"])
    definitions = set(transfer["audited_definitions"])
    extra = set(transfer.get("additional_named_theorems", []))
    names = transfer["theorems"]
    if (set(names) != (release - definitions) | reviews | extra or not definitions <= release
            or not inherited <= set(config["theorems"]) or not inherited):
        raise ValueError("source audits and selected theorem manifest disagree")
    for cwd, target in ((ROOT / "formal", "ProofCatalogExport"), (LIB, "MashruProofs")):
        subprocess.run([lake, "build", target], cwd=cwd, check=True, stdout=subprocess.DEVNULL)
    validate_named_coverage(lake, set(names) | set(config["theorems"]), definitions)
    execution = subprocess.run([lake, "env", "lean", "ExportTransfer.lean"], cwd=LIB,
                               stdout=subprocess.PIPE, text=True)
    if execution.returncode:
        errors = [line for line in execution.stdout.splitlines() if not line.startswith("NABT_PROOF")]
        raise ValueError("Lean declaration export failed: " + " ".join(errors)[-2000:])
    rows, _ = core.summarize_rows(core.parse_export(execution.stdout, names))
    base = reference().with_name("proof_catalog.json")
    existing = defaultdict(list)
    for row in json.loads(base.read_bytes())["theorems"]:
        existing[row["statement_sha256"]].append(row["name"])
    inputs = {}
    for directory in (LIB, ROOT / "vendor/alghanem-a116"):
        for path in directory.rglob("*"):
            if ".lake" not in path.parts and path.is_file() and (
                path.suffix == ".lean" or path.name in {"lakefile.toml", "lake-manifest.json", "lean-toolchain"}
            ):
                inputs[path.relative_to(ROOT).as_posix()] = core.file_sha(path)
    for row in rows:
        module = row["module"]
        rel = module.replace(".", "/") + ".lean"
        if module.split(".")[0] == "A116":
            scope, source = "existing-a116", ROOT / "vendor/alghanem-a116" / rel
            existing[row["statement_sha256"]].append(row["name"])
        elif module.startswith("Nabt."):
            scope, source = "existing-nabt", ROOT / "formal" / rel
        else:
            scope = "research-countermodel" if row["name"] in reviews else "imported"
            source = LIB / rel
        row["scope"] = scope
        row["source_path"] = source.relative_to(ROOT).as_posix()
        if row["source_path"] not in inputs:
            inputs[row["source_path"]] = core.file_sha(source)
    for row in rows:
        row["existing_same_statement"] = sorted(set(existing[row["statement_sha256"]]) - {row["name"]})
    return {"schema": "nabt.mashru-compiled-extension.v1", "authority": "COMPILED_DECLARATION_INDEX_ONLY",
            "repository": transfer["repository"], "commit": transfer["commit"],
            "existing_kernel_audit": len(inherited), "audited_definitions": sorted(definitions),
            "core_catalog_sha256": core.file_sha(base), "inputs": inputs,
            "scope_counts": dict(Counter(row["scope"] for row in rows)), "theorems": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    catalog = compile_reference(args.lake)
    encoded = core.canonical_json(catalog).encode()
    path = reference()
    if args.check:
        if gzip.decompress(path.read_bytes()) != encoded:
            raise SystemExit("stale Mashru proof reference")
    else:
        with path.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream:
            stream.write(encoded)
    print(json.dumps(catalog["scope_counts"], sort_keys=True))


if __name__ == "__main__":
    main()
