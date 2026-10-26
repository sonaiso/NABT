#!/usr/bin/env python3
"""Create an additional compiled catalogue without replacing published evidence.

Run only after the Lean declarations and their Python source-link readers are
stable. Every generator is replayed in check mode, with its raw log retained.
This records a declaration index, not language or whole-book completeness.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PREVIOUS = ROOT / "evidence/progressive_rule_audit_v1/catalog_references"
PREVIOUS_PINS = {
    "proof_catalog.json": "fc99e19bfb976deed7c3f7528d4ab20160a9a3ee7517196a2b66a05e4b76919f",
    "grammar_link_summary.json": "f9c496285ac7b9126ea8df414ac6f48bb3c062aea1e5ee711eae0bd9a9435fc1",
    "mantuq_proof_links.json": "87de15e5eba25b7873dc6a4919415c7af7b96b0a1dde101e41e48eb349696a5e",
    "linguistic_proof_links.json": "f8b33e16162824c0e1ecd134dd06d064343f370c45b4b07fdbb27bbeb7325216",
    "licensed_proof_links.json": "a8bff6221698b8348af9503a4a8bb84807386847ce9dd425411ed6702ef3e903",
}
MODULES = {
    "proof_catalog": "tools.proof_catalog",
    "grammar_link_summary": "tools.grammar_catalog.links",
    "mantuq_proof_links": "tools.mantuq_inference.links",
    "linguistic_proof_links": "tools.linguistic_truth.links",
    "licensed_proof_links": "tools.licensed_inference.links",
}


def checksum(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def write_new(path: Path, raw: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(raw)


def verify_previous() -> None:
    for name, expected in PREVIOUS_PINS.items():
        if checksum((PREVIOUS / name).read_bytes()) != expected:
            raise ValueError("Historical catalogue changed: " + name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    args = parser.parse_args()
    destination = HERE / "catalog_references"
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Never replace an observed catalogue; use a new explicit revision")
    verify_previous()
    destination.mkdir(exist_ok=True)
    (destination / "validation").mkdir()
    logs, commands, check_codes = {}, [], {}
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + str(ROOT)}

    def run(command: list[str], log_name: str) -> int:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, check=False)
        raw = result.stdout
        log_path = destination / "validation" / (log_name + ".log.gz")
        packed = gzip.compress(raw, mtime=0)
        write_new(log_path, packed)
        logs[str(log_path.relative_to(destination))] = {
            "sha256": checksum(packed), "uncompressed_sha256": checksum(raw),
            "uncompressed_bytes": len(raw),
        }
        commands.append({"command": command, "returncode": result.returncode,
                         "log": str(log_path.relative_to(ROOT))})
        if result.returncode:
            raise RuntimeError("Catalogue command failed; retained log: " + str(log_path))
        return result.returncode

    # A matching stale catalogue/JSON manifest is not evidence that this
    # release's new declarations were actually indexed. Check the kernel's
    # Audit.lean sequence against the JSON manifest before generating anything.
    audit_path = destination / "validation" / "axioms.json"
    run([sys.executable, "tools/check_axioms.py", "--lake", args.lake,
         "--output", str(audit_path)], "axiom_audit")
    before = json.loads((PREVIOUS / "proof_catalog.json").read_bytes())
    old_names = {row["name"] for row in before["theorems"]}
    advertised = set(json.loads((ROOT / "formal/theorems.json").read_bytes())["theorems"])
    additions = advertised - old_names
    required_counts = {"Nabt.LexicalSourceAcquisition.": 21,
                       "Nabt.QualifiedCueLicensing.": 11}
    if (old_names - advertised or len(additions) != 32
            or any(sum(name.startswith(prefix) for name in additions) != count
                   for prefix, count in required_counts.items())):
        raise ValueError("This release must retain every prior declaration and index its 32 new kernel-audited declarations")
    for name, module in MODULES.items():
        path = destination / (name + ".json")
        base = [sys.executable, "-m", module, "--lake", args.lake]
        run(base + ["--output", str(path)], name + ".generation")
        check_codes[name] = run(base + ["--check", str(path)], name + ".check")
    test_command = [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                    "-p", "test_proof_catalog.py", "-v"]
    test_code = run(test_command, "test_proof_catalog")
    verify_previous()
    after = json.loads((destination / "proof_catalog.json").read_bytes())
    new_names = {row["name"] for row in after["theorems"]}
    removed = sorted(old_names - new_names)
    if removed:
        raise ValueError("Additive source acquisition removed advertised declarations")
    migration = {
        "schema": "nabt.source-acquisition.proof-catalog-migration.v1",
        "scope": "Compiled declaration index and replayed source references; not whole-book or Arabic completeness.",
        "previous_directory": str(PREVIOUS.relative_to(ROOT)),
        "current_directory": str(destination.relative_to(ROOT)),
        "old_artifacts_unchanged": True,
        "previous_artifact_sha256": PREVIOUS_PINS,
        "current_artifact_sha256": {name: checksum((destination / name).read_bytes())
                                    for name in PREVIOUS_PINS},
        "previous_counts": before["counts"], "current_counts": after["counts"],
        "added_declarations": sorted(new_names - old_names), "removed_declarations": removed,
        "check_returncodes": check_codes,
        "kernel_audit": {"path": str(audit_path.relative_to(ROOT)),
                         "sha256": checksum(audit_path.read_bytes()),
                         "log_sha256": checksum(audit_path.with_suffix(".log").read_bytes())},
        "tests": {"file": "tests/test_proof_catalog.py", "returncode": test_code},
        "commands": commands, "logs": logs,
        "source_translation_fidelity_established": False,
        "whole_book_completeness_established": False,
        "whole_arabic_completeness_established": False,
    }
    write_new(destination / "catalog_migration.json",
              (json.dumps(migration, ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({"directory": str(destination.relative_to(ROOT)),
                      "added_declarations": len(migration["added_declarations"]),
                      "current_counts": after["counts"]}))


if __name__ == "__main__":
    main()
