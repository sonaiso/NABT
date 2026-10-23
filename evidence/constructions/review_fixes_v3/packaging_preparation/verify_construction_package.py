#!/usr/bin/env python3
"""Build and verify the pinned construction release in an isolated installation.

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
VERSION = "0.14.0a2"
LAW_ID = "nabt.discourse-evidence.v1"
TABLE_SHA256 = "30d990bf93aa436d9452e5a0a4172349727c9e5bb2c6fd1491e53d518b546325"
DEFAULT_FREEZE = "evidence/constructions/code_freeze_v3.json"
# Every source byte must match this approved freeze, including the exact
# inventory. The expected count belongs to the pin, not to the verifier code.
CODE_FREEZE_PINS = {
    "96ffa98008bf1b6a6d1f5ab6b79a330fe4b8a9329887d9ac3f8ff9d31eb12e1e": {
        "selection": "constructions_v1",
        "version": "0.14.0a1",
        "profile": "construction_v1",
        "source_file_count": 74,
        "future_operator_support": False,
        "snapshot_sha256": "87c7d5dc6c4aa5f46d42f7cd27a1595e2a2844af50da42a45a0f3b3bc09812b9",
        "archive_sha256": "edaff6bb63863e10734993bbaf5101160dab3308b22e763ba188d89fa28e3575",
    },
    "5d4bf3ec6331dab12ebc735f57203cf6bdbc86a563eae0311a66316eb8b820b1": {
        "selection": "constructions_v2",
        "version": "0.14.0a1",
        "profile": "construction_v1",
        "source_file_count": 74,
        "future_operator_support": True,
        "snapshot_sha256": "1e9d906428ec3824c4ecbff8ef8fb3adc88d6cb6c9dbfa1819c53655b3206c7c",
        "archive_sha256": "9d5ec76ec904c3696d0e5a76e46fe435e9189322fe0578133c6816707b2fd2c5",
    },
    "23d04d307c3e560c8198ee0700923673af001a8835d8e00d6c11d79534e6d611": {
        "selection": "constructions_v3",
        "version": "0.14.0a2",
        "profile": "construction_v2",
        "source_file_count": 74,
        "future_operator_support": True,
        "snapshot_sha256": "2c1b6b30e22b5322046109b461f850974e356736f2aedb06c4911be82375188f",
        "archive_sha256": "b5363658881c8e265295ad727d346ea8925348e9342b89f50eb014be824a19f1",
    },
}
PERSON_LAW_ID = "nabt.person-evidence.v1"
PERSON_TABLE_SHA256 = "f77c9b65b3a7b638166b5807fff1218cb30079d2d301c815b1b512a665858d15"
POLICY_ID = "nabt.discourse-grammar-sources.v1"
POLICY_SHA256 = "cd1f4fcf970b62a7ac8882bdfffed72229c5b09cac9abb561d4a99452776aa31"
CONSTRUCTION_RULES_V1 = {
    "kana_sisters", "inna_sisters", "zanna_sisters", "kada_complement",
    "tense_aspect", "naat_agreement", "hal_attachment", "tamyiz_measure",
    "tamyiz_nisba", "badal_identity", "tawkeed_reference", "idafa_chain",
    "temporal_spatial_attachment", "counted_tens_forms", "counted_tens_specification",
    "counted_tens_paradigm", "attested_accusative_alif",
}
CONSTRUCTION_TABLE_ROWS_V1 = {"operator_rows": 4, "role_rows": 68, "agreement_rows": 81,
    "idafa_rows": 256, "an_rows": 7, "activation_rows": 256, "identity_rows": 16, "scope_rows": 88}
RELEASE_PROFILES = {
    "construction_v1": {
        "language_id": "nabt.arabic-discourse-frames.v2",
        "reader_version": "nabt.discourse-reader.v2",
        "law_id": "nabt.construction-evidence.v1",
        "table_sha256": "7499b2b3d1179d02b4c9a8990ae45a2e60f047cd4ad47b525975fea752f57263",
        "policy_id": "nabt.construction-grammar-sources.v1",
        "policy_sha256": "51cd562baefd50a3de493fb88cb39f5b9442c648acdeedd02cdd3a75de378bb4",
        "rules": CONSTRUCTION_RULES_V1,
        "table_rows": CONSTRUCTION_TABLE_ROWS_V1,
        "review_fix_smokes": False,
    },
    "construction_v2": {
        "language_id": "nabt.arabic-discourse-frames.v3",
        "reader_version": "nabt.discourse-reader.v3",
        "law_id": "nabt.construction-evidence.v2",
        "table_sha256": "7cda6fd3736cbd5935bc9a9c3ab0e6510abbacc2f234bd752ab6846ba32e9595",
        "policy_id": "nabt.construction-grammar-sources.v2",
        "policy_sha256": "d1c3a775f30d503bd1d43f7e570808c6b1c1ca554ca36b2a94302a3fbc8146ed",
        "rules": CONSTRUCTION_RULES_V1 | {"predicate_adjectival_agreement"},
        "table_rows": {**CONSTRUCTION_TABLE_ROWS_V1, "predicate_agreement_rows": 18},
        "review_fix_smokes": True,
    },
}
REQUIRED_PACKAGE_FILES = {
    "nabt/person_evidence.py", "nabt/discourse.py", "nabt/discourse_reader.py",
    "nabt/discourse_context.py", "nabt/discourse_adverbs.py", "nabt/discourse_laws.py",
    "nabt/data/person_evidence.json", "nabt/data/discourse_evidence.json",
    "nabt/data/source_evidence/discourse_policy.json",
    "nabt/data/source_evidence/qatr.txt", "nabt/data/source_evidence/alfiyya.txt",
    "nabt/data/source_evidence/sibawayhi.txt",
    "nabt/construction_reader.py", "nabt/construction_complements.py",
    "nabt/construction_nominals.py", "nabt/construction_sources.py", "nabt/construction_laws.py",
    "nabt/data/construction_evidence.json", "nabt/data/source_evidence/construction_policy.json",
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

# These examples are authored interface checks, not a held-out linguistic
# evaluation. Their exact text and independent teaching inputs are preserved.
READ_CASES = (
    ("read-kana", "كان زيدٌ حكيمًا.", {"kana_subject": "raf", "kana_predicate": "nasb"}),
    ("read-inna", "إنَّ زيدًا حكيمٌ.", {"inna_subject": "nasb", "inna_predicate": "raf"}),
    ("read-zanna", "ظن زيدٌ سالمًا حكيمًا.",
        {"zanna_subject": "raf", "zanna_object1": "nasb", "zanna_object2": "nasb"}),
    ("read-kada", "كاد زيدٌ يكتبُ.",
        {"kada_subject": "raf", "kada_predicate": "nasb", "imperfect_indicative": "raf"}),
    ("read-kada-an", "كاد زيدٌ أن يكتبَ.",
        {"kada_subject": "raf", "kada_predicate": "nasb", "imperfect_subjunctive": "nasb"}),
    ("read-naat", "كِتَابٌ جديدٌ واسعٌ.", {"naat": "raf"}),
    ("read-idafa", "كِتَابُ طالبِ زيدٍ جديدٌ.", {"idafa_complement": "jarr"}),
    ("read-hal", "جاء زيدٌ راكبًا.", {"hal": "nasb"}),
    ("read-tamyiz", "اشتعل الرأسُ شيبًا.", {"tamyiz": "nasb"}),
    ("read-badal", "هذا زيدٌ حكيمٌ.", {"badal": "raf"}),
    ("read-tawkeed", "زيدٌ نفسُه حكيمٌ.", {"tawkeed": "raf"}),
    ("read-spatial", "زيدٌ فوقَ المكتبِ.", {"place_adverb": "nasb"}),
    ("read-temporal", "كتب زيدٌ يومَ الخميسِ.", {"time_adverb": "nasb"}),
    ("read-counted-tens", "جاء عشرون رجلًا.", {"active_subject": "raf", "tamyiz": "nasb"}),
)
FUTURE_READ_CASE = ("read-kana-future", "سوف يكونُ زيدٌ حكيمًا.",
    {"kana_subject": "raf", "kana_predicate": "nasb", "imperfect_indicative": "raf"})
REVIEW_READ_CASES = (
    ("read-relative-spatial", "زيدٌ الذي يكتبُ حكيمٌ فوق سالمٍ.", {"place_adverb": "nasb"}),
    ("read-conjunction-control", "زيدٌ حكيمٌ وَ سالمٌ حكيمٌ.",
        {"nominal_subject": "raf", "nominal_predicate": "raf"}),
)
REVIEW_REJECT_CASES = (
    ("reject-operator-mark", "كَانُ زيدٌ حكيمًا."),
    ("reject-predicate-agreement", "كان زيدٌ حكيمةً."),
    ("reject-future-particle-mark", "سُوفَ يكتبُ زيدٌ."),
    ("reject-exception-particle-mark", "ليس زيدٌ إِلُّا حكيمًا."),
    ("reject-conjunction-mark", "زيدٌ حكيمٌ وُ سالمٌ حكيمٌ."),
)
REVIEW_FINAL_NAMES = ["ask-wh-control", "reject-wh-operator-mark", "reject-polar-particle-mark",
                      "read-alif-compatible", "reject-alif-source-template"]
# Authored source-consistency controls: the only changed source atom is the
# internal vowel sequence of the full form. These are packaging inputs, not
# a copy of independent evaluation gold or caller-provided lexical entries.
ALIF_SOURCE_PREFIX = (
    "LOCATION\tFORM\tTAG\tFEATURES\n"
    "(1:1:1:1)\tzayodN\tPN\tSTEM|POS:PN|LEM:zayod|ROOT:zyd|MS\n"
    "(1:2:1:1)\tzayodK\tPN\tSTEM|POS:PN|LEM:zayod|ROOT:zyd|MS\n"
    "(1:3:1:1)\tEalamN\tN\tSTEM|POS:N|LEM:Ealam|ROOT:Elm|MS\n"
    "(1:4:1:1)\tEalamK\tN\tSTEM|POS:N|LEM:Ealam|ROOT:Elm|MS\n"
)
ALIF_SOURCE_SUFFIX = "(1:6:1:1)\tkaAna\tV\tSTEM|POS:V|PERF|LEM:kaAna|ROOT:kwn|3MS\n"
INITIAL_SMOKE_NAMES = ["discourse-catalog", "audit-corpus", "learn-qac-lexicon"]
FINAL_SMOKE_NAMES = [
    "verify-report", "withdraw-report-qac", "withdraw-report-context", "ask-scoped",
    "verify-answer", "withdraw-answer-qac", "no-embedded-fact", "read-without-qac",
]
SETUP_COMMAND_NAMES = ["build-wheel", "create-venv", "install-wheel", "inspect-install", "version"]


def digest(raw):
    return sha256(raw).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_json_once(path, value):
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


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


def inspect_report_identity(name, text, report, profile, lexical_source_sha256):
    require(report["source_text"] == text and report["source_sha256"] == digest(text.encode("utf-8"))
            and report["lexical_model"] is not None
            and report["lexical_model"]["source"]["sha256"] == lexical_source_sha256,
            name + ": source identity differs")
    require(report["language_id"] == profile["language_id"]
            and report["reader_version"] == profile["reader_version"]
            and report["construction_law_id"] == profile["law_id"]
            and report["construction_law_sha256"] == profile["table_sha256"]
            and report["construction_policy_sha256"] == profile["policy_sha256"],
            name + ": installed construction identity differs")


def inspect_deferred_report(name, text, report, profile, lexical_source_sha256):
    inspect_report_identity(name, text, report, profile, lexical_source_sha256)
    require(report["status"] == "DEFER" and report["claims"] == [],
            name + ": unsupported source acquired a document claim")
    for clause in report["clauses"]:
        for analysis in clause["analyses"]:
            require(analysis["assertion_allowed"] is False and all(
                a["activated"] is False and a["actual_role"] is None and
                a["inflected_case"] is None and a["local_case"] is None
                for a in analysis["assignments"]),
                name + ": deferred source retained an actual assignment")


def inspect_deferred_answer(name, text, question, answer, lexical_source_sha256):
    require(answer["source_text"] == text and answer["source_sha256"] == digest(text.encode("utf-8"))
            and answer["question_text"] == question
            and answer["question_sha256"] == digest(question.encode("utf-8"))
            and answer["lexical_model"] is not None
            and answer["lexical_model"]["source"]["sha256"] == lexical_source_sha256,
            name + ": question or teaching-source identity differs")
    require(answer["status"] == "DEFER" and not answer["proofs"] and not answer["counterproofs"]
            and not answer["bindings"], name + ": rejected question retained answer authority")


def inspect_read_case(name, text, expected_roles, report, learned, profile):
    """Check a few declared interface outcomes; this is not a language scorer."""
    inspect_report_identity(name, text, report, profile, learned["source"]["sha256"])
    require(report["lexical_model"] == learned, name + ": learned model summary differs")
    require(report["world_truth"] == "NOT_ESTABLISHED" and report["claims"],
            name + ": source-relative claim scope differs")
    analyses = [row for clause in report["clauses"] for row in clause["analyses"]
                if not row["rejected_candidate"] and row["licensed_syntax"] and row["references_complete"]]
    require(analyses, name + ": no complete viable analysis")
    for analysis in analyses:
        require(all(a["reading_id"] in analysis["reading_ids"] and a["activated"]
                    and a["actual_role"] == a["role"] for a in analysis["assignments"]),
                name + ": assignment/reading identity is disconnected")
        for role, case in expected_roles.items():
            matching = [a for a in analysis["assignments"] if a["actual_role"] == role]
            require(matching and all((a["inflected_case"] or a["local_case"]) == case for a in matching),
                    name + ": expected constituent case differs: " + role)
        if name in ("read-kana", "read-inna", "read-zanna", "read-kada", "read-kada-an", "read-kana-future"):
            family = name.split("-")[1]
            gates = [r for r in analysis["relations"] if r["kind"] == "construction_gate"]
            require(len(gates) == 1 and gates[0]["family"] == family and gates[0]["allowed"] is True
                    and all(value is True for value in gates[0]["premises"].values())
                    and all(e[side]["reading_id"] in analysis["reading_ids"]
                            for e in gates[0]["edges"] for side in ("head", "target")),
                    name + ": source-bound conditional operator gate differs")
            if name == "read-kana-future":
                require(any(text.encode("utf-8")[span["start"]:span["end"]].decode("utf-8") == "سوف"
                            for span in gates[0]["consumed_grammar_spans"]),
                        name + ": future marker lost its original source span")
                require(not any(r["kind"] == "hal" for r in analysis["relations"]),
                        name + ": future copula fell through to an event with a hal")
        if name in ("read-kada", "read-kada-an"):
            clause = next(a for a in analysis["assignments"] if a["role"] == "kada_predicate")
            verb = next(a for a in analysis["assignments"] if a["role"].startswith("imperfect_"))
            require((clause["case_domain"], clause["local_case"], clause["inflected_case"]) ==
                    ("clause_local_case", "nasb", None)
                    and verb["inflected_case"] == ("nasb" if name.endswith("-an") else "raf"),
                    name + ": clause-local case was conflated with internal verb mood")
        if name == "read-idafa":
            edges = [r for r in analysis["relations"] if r["kind"] == "idafa"]
            require(len(edges) == 2 and edges[0]["head_span"] != edges[1]["head_span"]
                    and all(e["ownership_asserted"] is False for e in edges),
                    name + ": nested genitive edges or source-relative scope differ")
        if name in ("read-badal", "read-tawkeed"):
            kind = name.removeprefix("read-")
            require(any(r["kind"] == kind and r["identity_preserved"] is True
                        for r in analysis["relations"]), name + ": licensed identity is missing")
        if name == "read-spatial":
            phrase = next(a for a in analysis["assignments"] if a["role"] == "nominal_predicate")
            require(phrase["case_domain"] == "phrase_local_case" and phrase["local_case"] == "raf"
                    and phrase["inflected_case"] is None, name + ": phrase and adverb cases were conflated")
        if name == "read-temporal":
            head = next(a["head_span"] for a in analysis["assignments"] if a["role"] == "time_adverb")
            require(text.encode("utf-8")[head["start"]:head["end"]].decode("utf-8") == "كتب",
                    name + ": temporal assignment lost its actual predicate head")
        if name == "read-counted-tens":
            require(any(r["kind"] == "tamyiz" and r.get("cardinality_asserted_as_world_fact") is False
                        for r in analysis["relations"]), name + ": quantified term became a world count")
        if name == "read-relative-spatial":
            attachments = [a for a in analysis["assignments"] if a["actual_role"] == "place_adverb"]
            edges = [r for r in analysis["relations"] if r["kind"] == "place_adverb"]
            require(attachments and edges, name + ": spatial attachment is missing")
            for row in attachments + edges:
                head = row["head_span"]
                raw = text.encode("utf-8")
                require(head["source_sha256"] == digest(raw)
                        and raw[head["start"]:head["end"]].decode("utf-8") == "حكيمٌ"
                        and head["span_sha256"] == digest(raw[head["start"]:head["end"]]),
                        name + ": modifier attached to the relative verb instead of the matrix predicate")
    if name in ("read-zanna", "read-kada", "read-kada-an"):
        require(all(c["predicate_kind"] == "scoped" and any(
            q.get("kind") == "operator_scope" and q.get("embedded_fact_projection") is False
            and q.get("embedded") for q in c["restriction"]) for c in report["claims"]),
            name + ": embedded proposition escaped its operator scope")
    if name in ("read-naat", "read-hal", "read-tamyiz"):
        kind = name.removeprefix("read-")
        require(all(any(q.get("kind") == kind for q in c["restriction"]) for c in report["claims"]),
                name + ": construction qualification was erased")
    if name in ("read-spatial", "read-temporal"):
        field = "place" if name == "read-spatial" else "time"
        require(all(c[field] for c in report["claims"]), name + ": adverbial qualification was erased")
    if name == "read-counted-tens":
        require(all(type(c["args"][0]) is dict and c["args"][0].get("kind") == "quantified_nominal"
                    for c in report["claims"]), name + ": counted phrase lost its typed nominal term")
    if name == "read-kana-future":
        require(all(c["predicate_kind"] == "property" and c["tense"] == "future" for c in report["claims"]),
                name + ": future copula lost its property interpretation or future tense")
    if name == "read-relative-spatial":
        require(len(report["claims"]) == 1 and report["claims"][0]["predicate_kind"] == "property"
                and report["claims"][0]["predicate"] == "حَكِيم" and report["claims"][0]["place"],
                name + ": spatial modifier changed the matrix proposition")
    if name == "read-conjunction-control":
        require(len(report["claims"]) == 2 and {tuple(c["args"]) for c in report["claims"]} ==
                {("zayd",), ("salim",)}, name + ": canonical conjunction did not preserve both clauses")


INSPECT_INSTALL = r'''
import hashlib, importlib.metadata as md, json, os, pathlib, sys
import nabt
import nabt.person_evidence, nabt.discourse, nabt.discourse_reader
import nabt.discourse_context, nabt.discourse_adverbs, nabt.discourse_laws
import nabt.construction_reader, nabt.construction_complements, nabt.construction_nominals
import nabt.construction_sources, nabt.construction_laws
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
        self.finalized = False
        self.env = dict(os.environ)
        for name in ("PYTHONPATH", "PYTHONHOME"):
            self.env.pop(name, None)
        self.env.update(PYTHONNOUSERSITE="1", PIP_CONFIG_FILE=os.devnull,
                        PIP_DISABLE_PIP_VERSION_CHECK="1")

    def run(self, name, argv, expected=0):
        require(not self.finalized, "Command journal is already finalized")
        require(re.fullmatch(r"[a-z][a-z0-9-]*", name)
                and all(row["name"] != name for row in self.rows),
                "Invalid or repeated command name")
        command = [str(arg) for arg in argv]
        result = subprocess.run(command, cwd=self.cwd, env=self.env,
                                capture_output=True, timeout=300)
        row = {"name": name, "argv": command, "cwd": str(self.cwd),
               "expected_exit_code": expected, "exit_code": result.returncode}
        for stream in ("stdout", "stderr"):
            raw = getattr(result, stream)
            path = self.output / "logs" / (name + "." + stream)
            with path.open("xb") as record:
                record.write(raw)
            row[stream] = file_record(path, self.output)
        write_json_once(self.output / "logs" / (name + ".command.json"), row)
        self.rows.append(row)
        require(result.returncode == expected,
                f"{name}: exit {result.returncode}, expected {expected}; inspect saved logs")
        return result


    def finalize(self, expected_names):
        require(not self.finalized, "Command journal is already finalized")
        require([row["name"] for row in self.rows] == expected_names
                and len(expected_names) == len(set(expected_names)),
                "Incomplete or unexpected final command inventory")
        expected_files = {name + suffix for name in expected_names
                          for suffix in (".command.json", ".stdout", ".stderr")}
        require({path.name for path in (self.output / "logs").iterdir()} == expected_files,
                "Immutable command/log inventory differs")
        for row in self.rows:
            path = self.output / "logs" / (row["name"] + ".command.json")
            expected = (json.dumps(row, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            require(path.read_bytes() == expected, "Immutable command record differs: " + row["name"])
            require(type(row["exit_code"]) is int and row["exit_code"] == row["expected_exit_code"],
                    "Command exit differs from its expected outcome: " + row["name"])
            for stream in ("stdout", "stderr"):
                require(file_record(self.output / row[stream]["path"], self.output) == row[stream],
                        "Recorded command output differs: " + row["name"] + "." + stream)
        path = self.output / "commands.json"
        write_json_once(path, self.rows)
        require(path.read_bytes() == (json.dumps(self.rows, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
                "Final command inventory differs after writing")
        self.finalized = True
        return {"command_count": len(self.rows), "immutable_command_records": len(self.rows),
                "names": expected_names, "all_command_records_and_log_hashes_match": True,
                "commands_sha256": digest(path.read_bytes())}


def validate(output, freeze_path):
    verifier_raw = Path(__file__).read_bytes()
    freeze_raw = freeze_path.read_bytes()
    freeze_sha256 = digest(freeze_raw)
    require(freeze_sha256 in CODE_FREEZE_PINS, "Unapproved construction runtime freeze")
    freeze_pin = CODE_FREEZE_PINS[freeze_sha256]
    profile = RELEASE_PROFILES[freeze_pin["profile"]]
    expected_version = freeze_pin["version"]
    expected_source_count = freeze_pin["source_file_count"]
    read_cases = READ_CASES + ((FUTURE_READ_CASE,) if freeze_pin["future_operator_support"] else ())
    if profile["review_fix_smokes"]:
        read_cases += REVIEW_READ_CASES
    review_names = ([row[0] for row in REVIEW_REJECT_CASES] + REVIEW_FINAL_NAMES
                    if profile["review_fix_smokes"] else [])
    smoke_names = INITIAL_SMOKE_NAMES + [row[0] for row in read_cases] + review_names + FINAL_SMOKE_NAMES
    freeze = json.loads(freeze_raw)
    require(freeze["schema"] == "nabt-independent-evaluation-code-freeze-v1", "Wrong freeze schema")
    require(all(freeze[key] == freeze_pin[key] for key in ("snapshot_sha256", "archive_sha256")),
            "Frozen snapshot/archive identity differs from its approved pin")
    files = freeze["files"]
    require(type(files) is list and len(files) == expected_source_count,
            "Frozen source/configuration count differs from the approved pin")
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
    require(len(package_rows) == expected_source_count - 1 and "pyproject.toml" in rows,
            "Expected frozen package files plus exactly one pyproject configuration")
    require(REQUIRED_PACKAGE_FILES <= set(package_rows), "Construction/discourse/person modules or packaged witnesses are missing")
    require(package_rows["nabt/data/discourse_evidence.json"]["sha256"] == TABLE_SHA256,
            "Frozen discourse law table differs")
    require(package_rows["nabt/data/person_evidence.json"]["sha256"] == PERSON_TABLE_SHA256,
            "Frozen person law table differs")
    require(package_rows["nabt/data/source_evidence/discourse_policy.json"]["sha256"] == POLICY_SHA256,
            "Frozen discourse grammar policy differs")
    require(package_rows["nabt/data/construction_evidence.json"]["sha256"] == profile["table_sha256"],
            "Frozen construction law table differs")
    require(package_rows["nabt/data/source_evidence/construction_policy.json"]["sha256"] == profile["policy_sha256"],
            "Frozen construction grammar policy differs")
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
        require(len(members) == expected_source_count and {m.name for m in members} == set(rows), "Archive inventory differs")
        for member in members:
            require(member.isfile(), "Archive contains a non-file")
            raw = archive.extractfile(member).read()
            row = rows[member.name]
            require(len(raw) == row["bytes"] and digest(raw) == row["sha256"],
                    "Archive member differs: " + member.name)

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    require(project["name"] == "nabt-machine" and project["version"] == expected_version, "Unexpected project identity")
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
    (output / "inputs/verify_construction_package.py").write_bytes(verifier_raw)
    (output / "inputs/inspect_install.py").write_text(INSPECT_INSTALL, encoding="utf-8")

    # No source tree is copied. The build reads the verified checkout; all
    # inspection and CLI execution use only the wheel installed under /tmp.
    work = Path(tempfile.mkdtemp(prefix="nabt-construction-package-", dir="/tmp"))
    cwd, venv = work / "smoke", work / "venv"
    cwd.mkdir()
    require(not work.is_relative_to(ROOT), "Isolation directory is inside the checkout")
    commands = Commands(output, cwd)
    commands.run("build-wheel", [sys.executable, "-m", "pip", "wheel", ROOT,
                                 "--no-deps", "--no-build-isolation", "--no-index", "--wheel-dir", output / "wheel"])
    wheels = list((output / "wheel").glob("*.whl"))
    require(len(wheels) == 1 and wheels[0].name == f"nabt_machine-{expected_version}-py3-none-any.whl", "Unexpected wheel inventory")
    wheel = wheels[0]
    dist = f"nabt_machine-{expected_version}.dist-info/"
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
        wheel_construction_table = json.loads(archive.read("nabt/data/construction_evidence.json"))
        metadata_raw = archive.read(dist + "METADATA")
        metadata = BytesParser().parsebytes(metadata_raw)
        require(metadata_raw.partition(b"\n\n")[2] == extras["README.md"], "Wheel description differs from captured README bytes")
        for key, value in (("Name", project["name"]), ("Version", expected_version), ("Requires-Python", project["requires-python"])):
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
    require(installed["distribution_version"] == expected_version and installed["module_version"] == expected_version, "Installed version differs")
    require(Path(installed["module_origin"]).is_relative_to(venv)
            and Path(installed["prefix"]) == venv, "Python imported the checkout instead of the isolated wheel")
    require(installed["nabt_module_origins"] and
            all(Path(origin).is_relative_to(venv) for origin in installed["nabt_module_origins"].values()),
            "A construction/discourse dependency was imported from outside the isolated installation")
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
    for name in ("construction_training.tsv", "construction_context.json"):
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
    require(version.stdout.decode().strip() == expected_version and not version.stderr, "CLI version differs")
    catalog, _ = smoke("discourse-catalog", ["discourse-catalog"])
    require(catalog["law_id"] == LAW_ID and catalog["law_sha256"] == TABLE_SHA256
            and catalog["law"]["law_id"] == LAW_ID and catalog["language_id"] == profile["language_id"],
            "Installed discourse catalog law or language differs")
    require(catalog["grammar_sources"]["policy_id"] == POLICY_ID and
            catalog["grammar_sources"]["policy_sha256"] == POLICY_SHA256 and
            len(catalog["grammar_sources"]["rules"]) == 22,
            "Installed discourse source policy did not replay")
    people = catalog["person"]
    require(people["law_id"] == PERSON_LAW_ID and people["table_sha256"] == PERSON_TABLE_SHA256
            and people["table"]["law_id"] == PERSON_LAW_ID, "Installed person law differs")
    construction = catalog["constructions"]
    require(construction["law"]["law_id"] == profile["law_id"]
            and construction["law"]["source_policy_id"] == profile["policy_id"]
            and {name: len(construction["law"][name]) for name in profile["table_rows"]} == profile["table_rows"],
            "Installed construction finite-law inventory differs")
    require(json.dumps(construction["law"], sort_keys=True, separators=(",", ":")) ==
            json.dumps(wheel_construction_table, sort_keys=True, separators=(",", ":")),
            "CLI construction law differs from the exact frozen table installed from the wheel")
    require(construction["grammar_sources"]["policy_id"] == profile["policy_id"]
            and construction["grammar_sources"]["policy_sha256"] == profile["policy_sha256"]
            and set(construction["grammar_sources"]["rules"]) == profile["rules"]
            and {row["family"] for row in construction["operators"]} == {"kana", "inna", "zanna", "kada"},
            "Installed construction source policy or family inventory differs")
    audit, _ = smoke("audit-corpus", ["audit-corpus", "construction_training.tsv", "--format", "qac"])
    require(audit["format"] == "qac" and audit["summary"]["record_count"] > 0
            and audit["summary"]["invalid_count"] == 0 and audit["summary"]["source_coverage_complete"] is True,
            "Authored teaching source did not audit cleanly")
    training_sha256 = digest(examples["construction_training.tsv"])
    require(audit["source"]["sha256"] == training_sha256, "Audited teaching source identity differs")
    learned, _ = smoke("learn-qac-lexicon", ["learn-qac-lexicon", "construction_training.tsv"])
    require(learned["source"]["sha256"] == training_sha256 and learned["lexical_readings"] > 0
            and learned["target_role_labels_available"] is False, "Learned source identity or label authority differs")
    require(set(learned["masked_features"]) == {"NOM", "ACC", "GEN", "MOOD:IND", "MOOD:SUBJ", "MOOD:JUS"},
            "Target case/mood labels were not masked")

    context_args = ["--context", "construction_context.json"]
    qac_args = ["--qac", "construction_training.tsv"]
    reports, report_bytes = {}, {}
    for name, text, expected_roles in read_cases:
        raw = text.encode("utf-8")
        (cwd / (name + ".txt")).write_bytes(raw)
        (output / "inputs" / (name + ".txt")).write_bytes(raw)
        report, raw_report = smoke(name, ["read-discourse", name + ".txt", *qac_args, *context_args],
                                  status="LICENSED_DISCOURSE")
        inspect_read_case(name, text, expected_roles, report, learned, profile)
        reports[name], report_bytes[name] = report, raw_report

    if profile["review_fix_smokes"]:
        for name, text in REVIEW_REJECT_CASES:
            raw = text.encode("utf-8")
            (cwd / (name + ".txt")).write_bytes(raw)
            (output / "inputs" / (name + ".txt")).write_bytes(raw)
            report, _ = smoke(name, ["read-discourse", name + ".txt", *qac_args, *context_args],
                              expected=3, status="DEFER")
            inspect_deferred_report(name, text, report, profile, training_sha256)

        wh_text = "كان زيدٌ حكيمًا أمسِ."
        wh_source = "review-wh-source.txt"
        (cwd / wh_source).write_bytes(wh_text.encode("utf-8"))
        (output / "inputs" / wh_source).write_bytes(wh_text.encode("utf-8"))
        for name, question, expected_status in (
                ("ask-wh-control", "متى كَانَ زيدٌ حكيمًا؟", "SUPPORTED"),
                ("reject-wh-operator-mark", "متى كَانُ زيدٌ حكيمًا؟", "DEFER"),
                ("reject-polar-particle-mark", "هُلْ كان زيدٌ حكيمًا أمسِ؟", "DEFER")):
            (output / "inputs" / (name + ".txt")).write_bytes(question.encode("utf-8"))
            answer, _ = smoke(name, ["ask-discourse", wh_source, question, *qac_args, *context_args],
                              expected=3 if expected_status == "DEFER" else 0, status=expected_status)
            if expected_status == "DEFER":
                inspect_deferred_answer(name, wh_text, question, answer, training_sha256)
            else:
                require(answer["source_sha256"] == digest(wh_text.encode("utf-8"))
                        and answer["question_sha256"] == digest(question.encode("utf-8"))
                        and answer["lexical_model"] == learned and answer["proofs"] and answer["bindings"],
                        name + ": canonical wh control lost its source-qualified answer")

        for name, full_form, expected_status in (
                ("read-alif-compatible", "EalamFA", "LICENSED_DISCOURSE"),
                ("reject-alif-source-template", "EilomFA", "DEFER")):
            source_raw = (ALIF_SOURCE_PREFIX + "(1:5:1:1)\t" + full_form +
                "\tN\tSTEM|POS:N|LEM:Ealam|ROOT:Elm|MS\n" + ALIF_SOURCE_SUFFIX).encode("utf-8")
            source_name = name + ".tsv"
            text = "كان زيد علما."
            for target in (cwd, output / "inputs"):
                (target / source_name).write_bytes(source_raw)
                (target / (name + ".txt")).write_bytes(text.encode("utf-8"))
            report, _ = smoke(name, ["read-discourse", name + ".txt", "--qac", source_name, *context_args],
                              expected=3 if expected_status == "DEFER" else 0, status=expected_status)
            if expected_status == "DEFER":
                inspect_deferred_report(name, text, report, profile, digest(source_raw))
            else:
                inspect_report_identity(name, text, report, profile, digest(source_raw))
                require(len(report["claims"]) == 1 and report["claims"][0]["predicate"] == "عَلَم"
                        and report["claims"][0]["args"] == ["zayd"],
                        name + ": compatible full/base source control lost its predicate")

    # Recompute a scoped report from the independently supplied source/model/
    # context, then withdraw each required premise. A preserved JSON claim is
    # never used as replacement source authority.
    source_file = "read-zanna.txt"
    report, report_raw = reports["read-zanna"], report_bytes["read-zanna"]
    (cwd / "report.json").write_bytes(report_raw)
    smoke("verify-report", ["verify-discourse", "report.json", "--source", source_file,
                              *qac_args, *context_args], status="VERIFIED", valid=True)
    smoke("withdraw-report-qac", ["verify-discourse", "report.json", "--source", source_file, *context_args],
          expected=2, status="REJECT", valid=False)
    smoke("withdraw-report-context", ["verify-discourse", "report.json", "--source", source_file, *qac_args],
          expected=2, status="REJECT", valid=False)
    question = "هل ظن زيدٌ سالمًا حكيمًا؟"
    (output / "inputs/scoped-question.txt").write_bytes(question.encode("utf-8"))
    answer, answer_raw = smoke("ask-scoped", ["ask-discourse", source_file, question, *qac_args, *context_args],
                              status="SUPPORTED")
    require(answer["source_sha256"] == report["source_sha256"] and
            answer["question_sha256"] == digest(question.encode("utf-8")) and
            answer["context_sha256"] == report["context"]["sha256"] and
            answer["lexical_model"] == learned and answer["proofs"] and
            answer["world_truth"] == "NOT_ESTABLISHED", "Scoped answer lost its independent premises")
    (cwd / "answer.json").write_bytes(answer_raw)
    smoke("verify-answer", ["verify-discourse-answer", "answer.json", "--source", source_file,
                              "--question", question, *qac_args, *context_args], status="VERIFIED", valid=True)
    smoke("withdraw-answer-qac", ["verify-discourse-answer", "answer.json", "--source", source_file,
                                  "--question", question, *context_args], expected=2, status="REJECT", valid=False)
    embedded_question = "هل سالمٌ حكيمٌ؟"
    (output / "inputs/embedded-question.txt").write_bytes(embedded_question.encode("utf-8"))
    unprojected, _ = smoke("no-embedded-fact", ["ask-discourse", source_file, embedded_question, *qac_args, *context_args],
                           status="UNKNOWN")
    require(not unprojected["proofs"] and not unprojected["counterproofs"],
            "Embedded fact acquired support or refutation outside the preserved operator scope")
    absent, _ = smoke("read-without-qac", ["read-discourse", source_file, *context_args], expected=3, status="DEFER")
    require(absent["lexical_model"] is None and not absent["claims"],
            "Missing source retained an acquired lexical model or source assertion")

    check_source(rows)
    require(Path(__file__).read_bytes() == verifier_raw, "Packaging verifier changed during execution")
    require(freeze_path.read_bytes() == freeze_raw and archive_path.read_bytes() == archive_raw, "Freeze changed during packaging")
    require(all((ROOT / name).read_bytes() == raw for name, raw in extras.items()), "Build documentation changed during packaging")
    require(all((ROOT / "src" / name).read_bytes() == raw for name, raw in documents.items()),
            "Non-runtime package documents changed during packaging")
    require(all((ROOT / "examples" / name).read_bytes() == raw for name, raw in examples.items()), "Smoke inputs changed during packaging")
    require([row["name"] for row in smokes] == smoke_names, "Incomplete authored CLI smoke inventory")
    command_recording = commands.finalize(SETUP_COMMAND_NAMES + smoke_names)
    validation = {
        "schema": "nabt.construction.package-validation.v1", "ok": True,
        "utc": datetime.now(timezone.utc).isoformat(), "version": expected_version,
        "freeze": {"path": str(freeze_path), "sha256": freeze_sha256,
                   "selection": freeze_pin["selection"],
                   "snapshot_sha256": freeze["snapshot_sha256"], "archive_sha256": freeze["archive_sha256"],
                   "source_files": expected_source_count, "baseline_head": freeze["repository_head"]},
        "wheel": file_record(wheel, output),
        "correspondence": {"current_source_files_before_and_after": expected_source_count,
                           "archive_files": expected_source_count,
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
                           "construction_table_sha256": profile["table_sha256"],
                           "construction_policy_sha256": profile["policy_sha256"],
                           "construction_law_rows": profile["table_rows"],
                           "construction_source_rules": sorted(profile["rules"]),
                           "language_id": profile["language_id"], "reader_version": profile["reader_version"],
                           "required_new_package_files": sorted(REQUIRED_PACKAGE_FILES)},
        "build_environment": {**build_environment, "no_build_isolation": True, "no_dependencies": True, "no_index": True},
        "isolation": {"temporary_root": str(work), "cwd": str(cwd), "venv": str(venv),
                      "installed_origin": installed["module_origin"], "pythonpath_removed": True,
                      "pythonhome_removed": True, "inspection_isolated_mode": True, "src_tree_copied": False,
                      "all_imported_nabt_modules_inside_venv": True},
        "input_files": [file_record(p, output) for p in sorted((output / "inputs").rglob("*")) if p.is_file()],
        "command_recording": command_recording,
        "cli_version_checked": True, "smoke_check_count": len(smokes), "smoke_checks": smokes,
        "future_operator_check_included": freeze_pin["future_operator_support"],
        "review_fix_checks_included": profile["review_fix_smokes"],
        "scope": [f"Installed package correspondence and {len(smokes)} authored CLI smoke checks only.",
                  "Frozen runtime files and separately pinned package documents have distinct inventories.",
                  "Construction examples are authored interface smokes, not a linguistic evaluation metric.",
                  "The conditional law, source acquisition, graph identities and world truth remain distinct.",
                  "Replay uses independently supplied QAC bytes and explicit context; withdrawal rejects with exit 2; missing evidence defers with exit 3.",
                  "No independent gold, full repository gate or remote operation is part of this tool."]}
    write_json_once(output / "validation.json", validation)
    write_json_once(output / "manifest.json", {"schema": "nabt.construction.packaging-artifacts.v1",
               "files": [file_record(p, output) for p in sorted(output.rglob("*"))
                         if p.is_file() and p.name != "manifest.json"]})
    manifest = json.loads((output / "manifest.json").read_bytes())
    require({row["path"] for row in manifest["files"]} == {
        str(p.relative_to(output)) for p in output.rglob("*") if p.is_file() and p.name != "manifest.json"},
        "Final packaging manifest inventory differs")
    for row in manifest["files"]:
        require(file_record(output / row["path"], output) == row,
                "Final packaging artifact differs: " + row["path"])
    return validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory for wheel, logs and validation")
    parser.add_argument("--code-freeze", type=Path, default=Path(DEFAULT_FREEZE),
                        help="Approved construction v1/v2/v3 freeze manifest (default v3); relative paths are resolved from the repository")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    freeze_path = args.code_freeze if args.code_freeze.is_absolute() else ROOT / args.code_freeze
    created = False
    try:
        output.mkdir(parents=True, exist_ok=False)
        created = True
        validation = validate(output, freeze_path.resolve())
        print(json.dumps({"ok": True, "version": validation["version"],
                          "source_files": validation["freeze"]["source_files"],
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
