#!/usr/bin/env python3
"""Build and verify the pinned inflection release in an isolated installation.

This is an explicit release action: invoking it builds a wheel. Use a new
output directory after the release README is final. It does not copy src,
install dependencies, read evaluation gold, or replace the full release gate.
Only standard-library modules are used by this verification script; the
existing pip/setuptools/wheel build tools must already be available.
"""

from __future__ import annotations

import argparse
import configparser
from datetime import datetime, timezone
from email.parser import BytesParser
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.12.0a2"
LAW_ID = "nabt.inflection-evidence.v1"
TABLE_SHA256 = "f8bc2f04fc1225a4f495d71a4c283289a3e8e9c74b9949008eb51e6445e7deb5"
DEFAULT_FREEZE = "evidence/inflection/code_freeze_v2.json"
# These package documents are outside the authoritative .py/.json/.txt runtime
# freeze. They have their own explicit byte identities; no arbitrary package
# extras or source-control files are admitted by this list.
PACKAGE_DOCUMENTS = {
    "nabt/data/source_evidence/LICENSE-DATA.md": {
        "bytes": 2571, "sha256": "ac2d62edd753190b9c0f8bd254beb245f3a199c5774a917c814c69e238360aae"},
    "nabt/data/source_evidence/README.md": {
        "bytes": 9864, "sha256": "83b0d8c4c2d8a3efebbed921c3675517b662ac7e386a1973354714bafdc8ee27"},
}


def digest(raw):
    return sha256(raw).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_record(path, relative_to):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(relative_to)), "bytes": len(raw), "sha256": digest(raw)}


def authoritative_paths():
    candidates = {ROOT / "pyproject.toml"}
    for suffix in ("py", "json", "txt"):
        candidates.update(ROOT.glob("src/**/*." + suffix))
    return {str(p.relative_to(ROOT)) for p in candidates
            if not any(part.endswith((".egg-info", ".dist-info"))
                       for part in p.relative_to(ROOT).parts[:-1])}


def check_source(rows):
    require(authoritative_paths() == set(rows), "Current source inventory differs from the freeze")
    for name, row in rows.items():
        path = ROOT / name
        require(path.resolve().is_relative_to(ROOT), "Frozen path leaves the repository")
        raw = path.read_bytes()
        require(len(raw) == row["bytes"] and digest(raw) == row["sha256"],
                "Current source differs from the freeze: " + name)


INSPECT_INSTALL = r'''
import hashlib, importlib.metadata as md, json, os, pathlib, sys
import nabt
distribution = md.distribution("nabt-machine")
root = pathlib.Path(nabt.__file__).parent
files = []
for path in sorted(root.rglob("*")):
    if path.is_file() and "__pycache__" not in path.parts:
        raw = path.read_bytes()
        files.append({"path": "nabt/" + str(path.relative_to(root)), "bytes": len(raw),
                      "sha256": hashlib.sha256(raw).hexdigest()})
metadata_path = next(p for p in distribution.files if str(p).endswith(".dist-info/METADATA"))
metadata = distribution.locate_file(metadata_path).read_bytes()
print(json.dumps({"distribution_version": distribution.version, "module_version": nabt.__version__,
    "module_origin": nabt.__file__, "python": sys.executable, "prefix": sys.prefix,
    "sys_path": sys.path, "pythonpath_present": "PYTHONPATH" in os.environ,
    "pythonhome_present": "PYTHONHOME" in os.environ, "files": files,
    "metadata_sha256": hashlib.sha256(metadata).hexdigest(),
    "readme_sha256": hashlib.sha256(metadata.partition(b"\n\n")[2]).hexdigest(),
    "requires_python": distribution.metadata["Requires-Python"],
    "requires_dist": distribution.requires or [],
    "entry_points": [{"name": e.name, "group": e.group, "value": e.value}
                     for e in distribution.entry_points]}, indent=2))
'''


class Commands:
    def __init__(self, output, cwd):
        self.output, self.cwd, self.rows = output, cwd, []
        self.env = dict(os.environ)
        for name in ("PYTHONPATH", "PYTHONHOME"):
            self.env.pop(name, None)
        self.env.update(PYTHONNOUSERSITE="1", PIP_CONFIG_FILE=os.devnull,
                        PIP_DISABLE_PIP_VERSION_CHECK="1")

    def run(self, name, argv, expected=0):
        command = [str(arg) for arg in argv]
        result = subprocess.run(command, cwd=self.cwd, env=self.env,
                                capture_output=True, timeout=300)
        row = {"name": name, "argv": command, "cwd": str(self.cwd),
               "expected_exit_code": expected, "exit_code": result.returncode}
        for stream in ("stdout", "stderr"):
            raw = getattr(result, stream)
            path = self.output / "logs" / (name + "." + stream)
            path.write_bytes(raw)
            row[stream] = file_record(path, self.output)
        self.rows.append(row)
        write_json(self.output / "commands.json", self.rows)
        require(result.returncode == expected,
                f"{name}: exit {result.returncode}, expected {expected}; inspect saved logs")
        return result


def validate(output, freeze_path):
    freeze_raw = freeze_path.read_bytes()
    freeze = json.loads(freeze_raw)
    require(freeze["schema"] == "nabt-independent-evaluation-code-freeze-v1", "Wrong freeze schema")
    files = freeze["files"]
    require(type(files) is list and len(files) == 58, "Expected 58 frozen source/configuration files")
    require(digest(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()) == freeze["snapshot_sha256"],
            "Freeze inventory digest differs")
    rows = {}
    for row in files:
        name = row["path"]
        require(type(name) is str and not PurePosixPath(name).is_absolute()
                and ".." not in PurePosixPath(name).parts and name not in rows,
                "Invalid or repeated freeze path")
        require(type(row["bytes"]) is int and row["bytes"] >= 0
                and type(row["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]),
                "Invalid freeze file identity")
        require(name == "pyproject.toml" or name.startswith("src/nabt/"), "Unexpected frozen package path")
        rows[name] = row
    package_rows = {name.removeprefix("src/"): row for name, row in rows.items() if name.startswith("src/")}
    require(len(package_rows) == 57 and "pyproject.toml" in rows, "Expected 57 package files plus pyproject")
    require(package_rows["nabt/data/inflection_evidence_table.json"]["sha256"] == TABLE_SHA256,
            "Frozen inflection law table differs")
    check_source(rows)
    documents = {}
    for name, row in PACKAGE_DOCUMENTS.items():
        path = ROOT / "src" / name
        require(path.resolve().is_relative_to(ROOT), "Package document leaves the repository")
        data = path.read_bytes()
        require(len(data) == row["bytes"] and digest(data) == row["sha256"],
                "Pinned non-runtime package document differs: " + name)
        documents[name] = data
    all_package_rows = {**package_rows, **PACKAGE_DOCUMENTS}

    archive_name = freeze["archive_filename"]
    require(Path(archive_name).name == archive_name, "Archive filename must be a sibling basename")
    archive_path = freeze_path.with_name(archive_name)
    archive_raw = archive_path.read_bytes()
    require(digest(archive_raw) == freeze["archive_sha256"], "Freeze archive digest differs")
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        require(len(members) == 58 and {m.name for m in members} == set(rows), "Archive inventory differs")
        for member in members:
            require(member.isfile(), "Archive contains a non-file")
            raw = archive.extractfile(member).read()
            row = rows[member.name]
            require(len(raw) == row["bytes"] and digest(raw) == row["sha256"],
                    "Archive member differs: " + member.name)

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    require(project["name"] == "nabt-machine" and project["version"] == VERSION, "Unexpected project identity")
    require(project["readme"] == "README.md" and project["scripts"] == {"nabt": "nabt.cli:main"},
            "Unexpected README or console entry point")
    build_environment = {"python": sys.version, "executable": sys.executable,
                         **{name: importlib.metadata.version(name) for name in ("pip", "setuptools", "wheel")}}
    for folder in ("inputs", "logs", "wheel"):
        (output / folder).mkdir()
    (output / "inputs/code_freeze.json").write_bytes(freeze_raw)
    extras = {}
    for name in ("README.md", "LICENSE"):
        extras[name] = (ROOT / name).read_bytes()
        (output / "inputs" / name).write_bytes(extras[name])
    for name, data in documents.items():
        path = output / "inputs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (output / "inputs/verify_inflection_package.py").write_bytes(Path(__file__).read_bytes())
    (output / "inputs/inspect_install.py").write_text(INSPECT_INSTALL, encoding="utf-8")

    # No source tree is copied. The build reads the verified checkout; all
    # inspection and CLI execution use only the wheel installed under /tmp.
    work = Path(tempfile.mkdtemp(prefix="nabt-inflection-package-", dir="/tmp"))
    cwd, venv = work / "smoke", work / "venv"
    cwd.mkdir()
    require(not work.is_relative_to(ROOT), "Isolation directory is inside the checkout")
    commands = Commands(output, cwd)
    commands.run("build-wheel", [sys.executable, "-m", "pip", "wheel", ROOT,
                                 "--no-deps", "--no-build-isolation", "--no-index", "--wheel-dir", output / "wheel"])
    wheels = list((output / "wheel").glob("*.whl"))
    require(len(wheels) == 1 and wheels[0].name == f"nabt_machine-{VERSION}-py3-none-any.whl", "Unexpected wheel inventory")
    wheel = wheels[0]
    dist = f"nabt_machine-{VERSION}.dist-info/"
    with ZipFile(wheel) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "Wheel contains duplicate entries")
        actual = {n for n in names if n.startswith("nabt/") and not n.endswith("/")}
        require(actual == set(all_package_rows), "Wheel runtime/document inventory differs")
        for name, row in all_package_rows.items():
            raw = archive.read(name)
            require(len(raw) == row["bytes"] and digest(raw) == row["sha256"], "Wheel file differs: " + name)
        metadata_raw = archive.read(dist + "METADATA")
        metadata = BytesParser().parsebytes(metadata_raw)
        require(metadata_raw.partition(b"\n\n")[2] == extras["README.md"], "Wheel description differs from final README bytes")
        for key, value in (("Name", project["name"]), ("Version", VERSION), ("Requires-Python", project["requires-python"])):
            require(metadata[key] == value, "Wheel metadata differs: " + key)
        require(metadata.get_all("Requires-Dist", []) == project["dependencies"], "Wheel dependency metadata differs")
        entrypoints = configparser.ConfigParser(interpolation=None)
        entrypoints.read_string(archive.read(dist + "entry_points.txt").decode())
        require(entrypoints.sections() == ["console_scripts"] and dict(entrypoints["console_scripts"]) == project["scripts"],
                "Wheel entry point differs")

    commands.run("create-venv", [sys.executable, "-m", "venv", venv])
    python, nabt = venv / "bin/python", venv / "bin/nabt"
    commands.run("install-wheel", [python, "-m", "pip", "install", "--no-index", "--no-deps", wheel])
    inspect_path = work / "inspect_install.py"
    inspect_path.write_text(INSPECT_INSTALL, encoding="utf-8")
    installed = json.loads(commands.run("inspect-install", [python, "-I", inspect_path]).stdout)
    require(installed["distribution_version"] == VERSION and installed["module_version"] == VERSION, "Installed version differs")
    require(Path(installed["module_origin"]).is_relative_to(venv)
            and Path(installed["prefix"]) == venv, "Python imported the checkout instead of the isolated wheel")
    require(not installed["pythonpath_present"] and not installed["pythonhome_present"], "Source injection environment was retained")
    require(installed["requires_python"] == project["requires-python"] and installed["requires_dist"] == project["dependencies"],
            "Installed project metadata differs")
    require(installed["entry_points"] == [{"name": "nabt", "group": "console_scripts", "value": "nabt.cli:main"}],
            "Installed console entry point differs")
    observed = {row["path"]: row for row in installed["files"]}
    require(len(installed["files"]) == len(all_package_rows) and set(observed) == set(all_package_rows),
            "Installed runtime/document inventory differs")
    for name, row in all_package_rows.items():
        require(observed[name]["bytes"] == row["bytes"] and observed[name]["sha256"] == row["sha256"],
                "Installed file differs: " + name)
    require(installed["metadata_sha256"] == digest(metadata_raw)
            and installed["readme_sha256"] == digest(extras["README.md"]), "Installed METADATA or README differs")
    write_json(output / "installed-files.json", installed)

    examples = {}
    for name in ("inflection.txt", "inflection_training.tsv"):
        examples[name] = (ROOT / "examples" / name).read_bytes()
        (output / "inputs" / name).write_bytes(examples[name])
        (cwd / name).write_bytes(examples[name])
    smokes = []

    def smoke(name, argv, expected=0, *, status=None, valid=None):
        result = commands.run(name, [nabt, *argv], expected)
        require(result.stderr == b"", name + ": unexpected CLI stderr")
        payload = json.loads(result.stdout)
        require(type(payload) is dict, name + ": expected a JSON object")
        if status is not None:
            require(payload.get("status") == status, name + ": unexpected status")
        if valid is not None:
            require(payload.get("valid") is valid, name + ": unexpected validity")
        smokes.append({"name": name, "expected_exit_code": expected, "exit_code": result.returncode,
                       "status": payload.get("status"), "valid": payload.get("valid"),
                       "stdout": "logs/" + name + ".stdout", "sha256": digest(result.stdout)})
        return payload, result.stdout

    version = commands.run("version", [nabt, "--version"])
    require(version.stdout.decode().strip() == VERSION and not version.stderr, "CLI version differs")
    catalog, _ = smoke("inflection-catalog", ["inflection-catalog"])
    require(catalog["law_id"] == LAW_ID and catalog["table_sha256"] == TABLE_SHA256
            and catalog["table"]["law_id"] == LAW_ID, "Installed catalog law differs")
    audit, _ = smoke("audit-corpus", ["audit-corpus", "inflection_training.tsv", "--format", "qac"])
    require(audit["format"] == "qac" and audit["summary"]["record_count"] > 0
            and audit["summary"]["invalid_count"] == 0 and audit["summary"]["source_coverage_complete"] is True,
            "Authored source did not audit cleanly")
    require(audit["source"]["sha256"] == digest(examples["inflection_training.tsv"]), "Audited source identity differs")
    learned, _ = smoke("learn-qac-lexicon", ["learn-qac-lexicon", "inflection_training.tsv"])
    require(learned["source"]["sha256"] == digest(examples["inflection_training.tsv"])
            and learned["lexical_readings"] > 0 and learned["target_role_labels_available"] is False,
            "Learned source identity or label authority differs")
    require(set(learned["masked_features"]) == {"NOM", "ACC", "GEN", "MOOD:IND", "MOOD:SUBJ", "MOOD:JUS"},
            "Target case/mood labels were not masked")
    report, report_raw = smoke("read-inflection", ["read-inflection", "inflection.txt", "--qac", "inflection_training.tsv"],
                               status="LICENSED_READINGS")
    require(report["raw_text"].encode("utf-8") == examples["inflection.txt"]
            and report["source_sha256"] == digest(examples["inflection.txt"])
            and report["lexical_source"] == learned, "Read report lost source or training identity")
    require(any(a["role"] == "imperfect_jussive" and a["inflected_case"] == "jazm" and a["local_case"] is None
                for a in report["assignments"]), "The authored example did not produce the expected jussive reading")
    require(any(r["activated"] is True and r["label"] == "imperfect_jussive" and r["case_name"] == "jazm"
                and any(s["sign_name"] == "nun_deleted" and s["mode_name"] == "deletion"
                        and s["origin_name"] == "substitute" for s in r["sign_candidates"])
                for r in report["relations"]), "Jussive reading did not retain its nun-deletion sign witness")
    require(report["semantic_facts"] == [], "A conditional example acquired world-fact authority")
    (cwd / "report.json").write_bytes(report_raw)
    smoke("verify-inflection", ["verify-inflection", "report.json", "--source", "inflection.txt",
                                 "--qac", "inflection_training.tsv"], status="VERIFIED", valid=True)
    smoke("withdraw-qac", ["verify-inflection", "report.json", "--source", "inflection.txt"],
          expected=2, status="REJECT", valid=False)
    absent, _ = smoke("read-without-qac", ["read-inflection", "inflection.txt"], expected=3, status="DEFER")
    require(absent["assignments"] == [] and absent["lexical_source"] is None,
            "Missing lexical source produced an assignment")

    check_source(rows)
    require(freeze_path.read_bytes() == freeze_raw and archive_path.read_bytes() == archive_raw, "Freeze changed during packaging")
    require(all((ROOT / name).read_bytes() == raw for name, raw in extras.items()), "Build documentation changed during packaging")
    require(all((ROOT / "src" / name).read_bytes() == raw for name, raw in documents.items()),
            "Non-runtime package documents changed during packaging")
    require(all((ROOT / "examples" / name).read_bytes() == raw for name, raw in examples.items()), "Smoke inputs changed during packaging")
    validation = {
        "schema": "nabt.inflection.package-validation.v1", "ok": True,
        "utc": datetime.now(timezone.utc).isoformat(), "version": VERSION,
        "freeze": {"path": str(freeze_path), "sha256": digest(freeze_raw),
                   "snapshot_sha256": freeze["snapshot_sha256"], "archive_sha256": freeze["archive_sha256"],
                   "source_files": 58, "baseline_head": freeze["repository_head"]},
        "wheel": file_record(wheel, output),
        "correspondence": {"current_source_files_before_and_after": 58, "archive_files": 58,
                           "frozen_runtime_package_files": len(package_rows),
                           "nonruntime_package_document_files": len(PACKAGE_DOCUMENTS),
                           "nonruntime_package_documents": [{"path": name, **row}
                                                            for name, row in PACKAGE_DOCUMENTS.items()],
                           "wheel_package_files": len(actual), "installed_package_files": len(observed),
                           "all_package_hashes_and_lengths_match": True, "unexpected_package_files": [],
                           "pyproject_installed_as_file": False,
                           "pyproject_sha256": rows["pyproject.toml"]["sha256"],
                           "metadata_fields_checked": ["Name", "Version", "Requires-Python", "Requires-Dist", "console_scripts:nabt"],
                           "metadata_sha256": digest(metadata_raw), "readme_sha256": digest(extras["README.md"]),
                           "wheel_and_installed_description_equal_final_readme": True, "law_table_sha256": TABLE_SHA256},
        "build_environment": {**build_environment, "no_build_isolation": True, "no_dependencies": True, "no_index": True},
        "isolation": {"temporary_root": str(work), "cwd": str(cwd), "venv": str(venv),
                      "installed_origin": installed["module_origin"], "pythonpath_removed": True,
                      "pythonhome_removed": True, "inspection_isolated_mode": True, "src_tree_copied": False},
        "input_files": [file_record(p, output) for p in sorted((output / "inputs").rglob("*")) if p.is_file()],
        "cli_version_checked": True, "smoke_check_count": len(smokes), "smoke_checks": smokes,
        "scope": ["Installed package correspondence and seven authored CLI smoke checks only.",
                  "Frozen runtime files and separately pinned package documents have distinct inventories.",
                  "Jussive/nun deletion is a source-relative reading, not proof of unrestricted Arabic or world truth.",
                  "Replay uses independently supplied QAC bytes; withdrawal rejects with exit 2; missing evidence defers with exit 3.",
                  "No independent gold, full repository gate or remote operation is part of this tool."]}
    write_json(output / "validation.json", validation)
    write_json(output / "manifest.json", {"schema": "nabt.inflection.packaging-artifacts.v1",
               "files": [file_record(p, output) for p in sorted(output.rglob("*"))
                         if p.is_file() and p.name != "manifest.json"]})
    return validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory for wheel, logs and validation")
    parser.add_argument("--code-freeze", type=Path, default=Path(DEFAULT_FREEZE),
                        help="Freeze manifest; relative paths are resolved from the repository")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    freeze_path = args.code_freeze if args.code_freeze.is_absolute() else ROOT / args.code_freeze
    created = False
    try:
        output.mkdir(parents=True, exist_ok=False)
        created = True
        validation = validate(output, freeze_path.resolve())
        print(json.dumps({"ok": True, "version": VERSION, "source_files": 58,
                          "frozen_runtime_package_files": validation["correspondence"]["frozen_runtime_package_files"],
                          "nonruntime_package_document_files": validation["correspondence"]["nonruntime_package_document_files"],
                          "package_files": validation["correspondence"]["wheel_package_files"],
                          "smoke_checks": validation["smoke_check_count"], "wheel_sha256": validation["wheel"]["sha256"],
                          "readme_sha256": validation["correspondence"]["readme_sha256"],
                          "validation": str(output / "validation.json"),
                          "validation_sha256": digest((output / "validation.json").read_bytes())}, indent=2))
        return 0
    except Exception as error:
        failure = {"ok": False, "type": type(error).__name__, "error": str(error), "output_dir": str(output),
                   "scope": "Packaging did not pass; inspect preserved command logs. No release success is asserted."}
        if created:
            write_json(output / "failure.json", failure)
        print(json.dumps(failure, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
