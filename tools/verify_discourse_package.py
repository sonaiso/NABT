#!/usr/bin/env python3
"""Build and verify the pinned discourse release in an isolated installation.

This is an explicit release action: invoking it builds a wheel. Use a new
output directory when the selected runtime freeze matches the checkout. It does not copy src,
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
VERSION = "0.13.0a1"
LAW_ID = "nabt.discourse-evidence.v1"
TABLE_SHA256 = "30d990bf93aa436d9452e5a0a4172349727c9e5bb2c6fd1491e53d518b546325"
DEFAULT_FREEZE = "evidence/discourse/code_freeze_v3.json"
# Historical v2 remains explicitly selectable. Selecting it still requires
# every current source byte to match v2; this is not a source-integrity bypass.
CODE_FREEZE_PINS = {
    "22350accf750741680f351b34cf97f95bf146b7389765cd74d937a8aa4291ae4": {
        "selection": "discourse_v2",
        "snapshot_sha256": "e82b9d72b45d8cbcd667708140b9f5b91a967822002a54a76bc87b097912a2f9",
        "archive_sha256": "0085bb7482ef89d20f0f8667ca015f0cf198ab283d9e439ecc814b9167b13775",
    },
    "c74b029c986fa3e1bb6a6ab3c5cbd423f77c902733626105ec95f5e366b71018": {
        "selection": "discourse_v3",
        "snapshot_sha256": "6b78f1c8e36058d350d1e572bf20737c3517d38a8498fc4a50ece6bf6725fd30",
        "archive_sha256": "4fbcadee8997087223cbf8ffc365dd7a1b6cac4eb0990350e8925098ec557b51",
    },
}
PERSON_LAW_ID = "nabt.person-evidence.v1"
PERSON_TABLE_SHA256 = "f77c9b65b3a7b638166b5807fff1218cb30079d2d301c815b1b512a665858d15"
POLICY_ID = "nabt.discourse-grammar-sources.v1"
POLICY_SHA256 = "cd1f4fcf970b62a7ac8882bdfffed72229c5b09cac9abb561d4a99452776aa31"
REQUIRED_PACKAGE_FILES = {
    "nabt/person_evidence.py", "nabt/discourse.py", "nabt/discourse_reader.py",
    "nabt/discourse_context.py", "nabt/discourse_adverbs.py", "nabt/discourse_laws.py",
    "nabt/data/person_evidence.json", "nabt/data/discourse_evidence.json",
    "nabt/data/source_evidence/discourse_policy.json",
    "nabt/data/source_evidence/qatr.txt", "nabt/data/source_evidence/alfiyya.txt",
    "nabt/data/source_evidence/sibawayhi.txt",
}
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
import nabt.person_evidence, nabt.discourse, nabt.discourse_reader
import nabt.discourse_context, nabt.discourse_adverbs, nabt.discourse_laws
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
                     for e in distribution.entry_points],
    "nabt_module_origins": {name: module.__file__ for name, module in sorted(sys.modules.items())
                            if name.startswith("nabt") and getattr(module, "__file__", None)}}, indent=2))
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
    freeze_sha256 = digest(freeze_raw)
    require(freeze_sha256 in CODE_FREEZE_PINS, "Unapproved discourse runtime freeze")
    freeze_pin = CODE_FREEZE_PINS[freeze_sha256]
    freeze = json.loads(freeze_raw)
    require(freeze["schema"] == "nabt-independent-evaluation-code-freeze-v1", "Wrong freeze schema")
    require(all(freeze[key] == freeze_pin[key] for key in ("snapshot_sha256", "archive_sha256")),
            "Frozen snapshot/archive identity differs from its approved pin")
    files = freeze["files"]
    require(type(files) is list and len(files) == 67, "Expected 67 frozen source/configuration files")
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
    require(len(package_rows) == 66 and "pyproject.toml" in rows, "Expected 66 package files plus pyproject")
    require(REQUIRED_PACKAGE_FILES <= set(package_rows), "Discourse/person modules or packaged source witnesses are missing")
    require(package_rows["nabt/data/discourse_evidence.json"]["sha256"] == TABLE_SHA256,
            "Frozen discourse law table differs")
    require(package_rows["nabt/data/person_evidence.json"]["sha256"] == PERSON_TABLE_SHA256,
            "Frozen person law table differs")
    require(package_rows["nabt/data/source_evidence/discourse_policy.json"]["sha256"] == POLICY_SHA256,
            "Frozen discourse grammar policy differs")
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
        require(len(members) == 67 and {m.name for m in members} == set(rows), "Archive inventory differs")
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
    (output / "inputs/verify_discourse_package.py").write_bytes(Path(__file__).read_bytes())
    (output / "inputs/inspect_install.py").write_text(INSPECT_INSTALL, encoding="utf-8")

    # No source tree is copied. The build reads the verified checkout; all
    # inspection and CLI execution use only the wheel installed under /tmp.
    work = Path(tempfile.mkdtemp(prefix="nabt-discourse-package-", dir="/tmp"))
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
        require(all(not PurePosixPath(n).is_absolute() and ".." not in PurePosixPath(n).parts
                    and (n.startswith("nabt/") or n.startswith(dist)) for n in names),
                "Wheel contains an unexpected top-level or escaping path")
        actual = {n for n in names if n.startswith("nabt/") and not n.endswith("/")}
        require(actual == set(all_package_rows), "Wheel runtime/document inventory differs")
        for name, row in all_package_rows.items():
            raw = archive.read(name)
            require(len(raw) == row["bytes"] and digest(raw) == row["sha256"], "Wheel file differs: " + name)
        metadata_raw = archive.read(dist + "METADATA")
        metadata = BytesParser().parsebytes(metadata_raw)
        require(metadata_raw.partition(b"\n\n")[2] == extras["README.md"], "Wheel description differs from captured README bytes")
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
    require(installed["nabt_module_origins"] and
            all(Path(origin).is_relative_to(venv) for origin in installed["nabt_module_origins"].values()),
            "A discourse dependency was imported from outside the isolated installation")
    require(all(not Path(p).is_relative_to(ROOT) for p in installed["sys_path"] if p),
            "Checkout path is visible in the isolated inspection process")
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
    for name in ("discourse.txt", "discourse_training.tsv", "discourse_context.json"):
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
    catalog, _ = smoke("discourse-catalog", ["discourse-catalog"])
    require(catalog["law_id"] == LAW_ID and catalog["law_sha256"] == TABLE_SHA256
            and catalog["law"]["law_id"] == LAW_ID, "Installed discourse catalog law differs")
    require(catalog["grammar_sources"]["policy_id"] == POLICY_ID and
            catalog["grammar_sources"]["policy_sha256"] == POLICY_SHA256 and
            len(catalog["grammar_sources"]["rules"]) == 22,
            "Installed discourse source policy did not replay")
    people, _ = smoke("person-catalog", ["person-catalog"])
    require(people["law_id"] == PERSON_LAW_ID and people["table_sha256"] == PERSON_TABLE_SHA256
            and people["table"]["law_id"] == PERSON_LAW_ID and people == catalog["person"],
            "Installed person catalogs differ")
    require({name: len(people["table"][name]) for name in
             ("profiles", "prefix_rows", "separate_pronouns", "attached_forms")} ==
            {"profiles": 14, "prefix_rows": 20, "separate_pronouns": 14, "attached_forms": 20},
            "Installed person inventory differs")
    audit, _ = smoke("audit-corpus", ["audit-corpus", "discourse_training.tsv", "--format", "qac"])
    require(audit["format"] == "qac" and audit["summary"]["record_count"] > 0
            and audit["summary"]["invalid_count"] == 0 and audit["summary"]["source_coverage_complete"] is True,
            "Authored source did not audit cleanly")
    require(audit["source"]["sha256"] == digest(examples["discourse_training.tsv"]), "Audited source identity differs")
    learned, _ = smoke("learn-qac-lexicon", ["learn-qac-lexicon", "discourse_training.tsv"])
    require(learned["source"]["sha256"] == digest(examples["discourse_training.tsv"])
            and learned["lexical_readings"] > 0 and learned["target_role_labels_available"] is False,
            "Learned source identity or label authority differs")
    require(set(learned["masked_features"]) == {"NOM", "ACC", "GEN", "MOOD:IND", "MOOD:SUBJ", "MOOD:JUS"},
            "Target case/mood labels were not masked")
    person, _ = smoke("read-person", ["read-person", "تكتب", "--qac", "discourse_training.tsv"],
                      status="SOURCE_QUALIFIED_ALTERNATIVES")
    profiles = {tuple(row["person_profile"][key] for key in ("person", "gender", "number"))
                for row in person["readings"] if row["person_profile"] is not None}
    require(profiles == {(2, 0, 0), (3, 1, 0)} and all(row["supports"] for row in person["readings"]),
            "Authored imperfect smoke did not retain source-backed second/third-feminine alternatives")
    absent_person, _ = smoke("person-without-qac", ["read-person", "تكتب"], expected=3, status="DEFER")
    require(absent_person["readings"] == [], "Missing source acquired a verbal person from the prefix")

    context_args = ["--context", "discourse_context.json"]
    qac_args = ["--qac", "discourse_training.tsv"]
    report, report_raw = smoke("read-discourse", ["read-discourse", "discourse.txt", *qac_args, *context_args],
                               status="LICENSED_DISCOURSE")
    require(report["source_text"].encode("utf-8") == examples["discourse.txt"]
            and report["source_sha256"] == digest(examples["discourse.txt"])
            and report["lexical_model"] == learned, "Read report lost source or training identity")
    require(report["world_truth"] == "NOT_ESTABLISHED" and report["claims"],
            "Read smoke did not preserve source-relative assertion scope")
    # The authored training token LEM:EAlim retains its lexical kasra.
    require(any(c["predicate"] == "عالِم" and c["args"] == ["zayd"] and c["positive"] is True
                for c in report["claims"]), "Authored speaker premise did not produce its bounded example claim")
    (cwd / "report.json").write_bytes(report_raw)
    smoke("verify-discourse", ["verify-discourse", "report.json", "--source", "discourse.txt",
                                *qac_args, *context_args], status="VERIFIED", valid=True)
    smoke("withdraw-report-qac", ["verify-discourse", "report.json", "--source", "discourse.txt", *context_args],
          expected=2, status="REJECT", valid=False)
    smoke("withdraw-report-context", ["verify-discourse", "report.json", "--source", "discourse.txt", *qac_args],
          expected=2, status="REJECT", valid=False)
    question = "هل زيد عالم؟"
    answer, answer_raw = smoke("ask-discourse", ["ask-discourse", "discourse.txt", question, *qac_args, *context_args],
                              status="SUPPORTED")
    require(answer["source_sha256"] == digest(examples["discourse.txt"]) and
            answer["question_sha256"] == digest(question.encode("utf-8")) and
            answer["context_sha256"] == report["context"]["sha256"] and
            answer["lexical_model"] == learned and answer["proofs"] and
            answer["world_truth"] == "NOT_ESTABLISHED", "Authored answer lost its independently supplied premises")
    (cwd / "answer.json").write_bytes(answer_raw)
    smoke("verify-discourse-answer", ["verify-discourse-answer", "answer.json", "--source", "discourse.txt",
                                      "--question", question, *qac_args, *context_args], status="VERIFIED", valid=True)
    smoke("withdraw-answer-qac", ["verify-discourse-answer", "answer.json", "--source", "discourse.txt",
                                  "--question", question, *context_args], expected=2, status="REJECT", valid=False)
    smoke("withdraw-answer-context", ["verify-discourse-answer", "answer.json", "--source", "discourse.txt",
                                      "--question", question, *qac_args], expected=2, status="REJECT", valid=False)
    absent, _ = smoke("read-without-qac", ["read-discourse", "discourse.txt", *context_args], expected=3, status="DEFER")
    require(absent["lexical_model"] is None, "Missing source retained a caller-supplied lexical model")

    check_source(rows)
    require(freeze_path.read_bytes() == freeze_raw and archive_path.read_bytes() == archive_raw, "Freeze changed during packaging")
    require(all((ROOT / name).read_bytes() == raw for name, raw in extras.items()), "Build documentation changed during packaging")
    require(all((ROOT / "src" / name).read_bytes() == raw for name, raw in documents.items()),
            "Non-runtime package documents changed during packaging")
    require(all((ROOT / "examples" / name).read_bytes() == raw for name, raw in examples.items()), "Smoke inputs changed during packaging")
    validation = {
        "schema": "nabt.discourse.package-validation.v1", "ok": True,
        "utc": datetime.now(timezone.utc).isoformat(), "version": VERSION,
        "freeze": {"path": str(freeze_path), "sha256": freeze_sha256,
                   "selection": freeze_pin["selection"],
                   "snapshot_sha256": freeze["snapshot_sha256"], "archive_sha256": freeze["archive_sha256"],
                   "source_files": 67, "baseline_head": freeze["repository_head"]},
        "wheel": file_record(wheel, output),
        "correspondence": {"current_source_files_before_and_after": 67, "archive_files": 67,
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
                           "wheel_and_installed_description_equal_captured_readme": True,
                           "law_table_sha256": TABLE_SHA256, "person_table_sha256": PERSON_TABLE_SHA256,
                           "discourse_policy_sha256": POLICY_SHA256,
                           "required_new_package_files": sorted(REQUIRED_PACKAGE_FILES)},
        "build_environment": {**build_environment, "no_build_isolation": True, "no_dependencies": True, "no_index": True},
        "isolation": {"temporary_root": str(work), "cwd": str(cwd), "venv": str(venv),
                      "installed_origin": installed["module_origin"], "pythonpath_removed": True,
                      "pythonhome_removed": True, "inspection_isolated_mode": True, "src_tree_copied": False,
                      "all_imported_nabt_modules_inside_venv": True},
        "input_files": [file_record(p, output) for p in sorted((output / "inputs").rglob("*")) if p.is_file()],
        "cli_version_checked": True, "smoke_check_count": len(smokes), "smoke_checks": smokes,
        "scope": ["Installed package correspondence and fifteen authored CLI smoke checks only.",
                  "Frozen runtime files and separately pinned package documents have distinct inventories.",
                  "Person and discourse examples are authored interface smokes, not a linguistic evaluation metric.",
                  "Replay uses independently supplied QAC bytes and explicit context; withdrawal rejects with exit 2; missing evidence defers with exit 3.",
                  "No independent gold, full repository gate or remote operation is part of this tool."]}
    write_json(output / "validation.json", validation)
    write_json(output / "manifest.json", {"schema": "nabt.discourse.packaging-artifacts.v1",
               "files": [file_record(p, output) for p in sorted(output.rglob("*"))
                         if p.is_file() and p.name != "manifest.json"]})
    return validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory for wheel, logs and validation")
    parser.add_argument("--code-freeze", type=Path, default=Path(DEFAULT_FREEZE),
                        help="Approved v2/v3 freeze manifest (default v3); relative paths are resolved from the repository")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    freeze_path = args.code_freeze if args.code_freeze.is_absolute() else ROOT / args.code_freeze
    created = False
    try:
        output.mkdir(parents=True, exist_ok=False)
        created = True
        validation = validate(output, freeze_path.resolve())
        print(json.dumps({"ok": True, "version": VERSION, "source_files": 67,
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
