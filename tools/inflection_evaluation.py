#!/usr/bin/env python3
"""Replay the independently frozen inflection transfer material.

The authored targets and verse exclusions predate the reviewer's first read of
the new implementation. QAC annotations remain training evidence, not an oracle
passed to the raw reader. This is a bounded transfer/abstention evaluation, not
an untouched natural corpus or unrestricted Arabic parsing accuracy.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import sys
import tarfile
import traceback
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "evidence/inflection"
VERSION = "nabt.inflection.independent-evaluation.v1"
FREEZE_SHA256 = "25b8b89e48c2403b1fa47055045d2bdd4d738dc86493398369da5749131d23db"
RUNTIME_FREEZE_SHA256 = "fe93f8ebebb21078113462244052da93c102f4d5a673c2636c0cab27e0ffa103"
PINNED_RUNTIME_FREEZES = {
    'eda208c3e092a8185a3223ba8f0848ff6d0232aca3b8c3e94645482233d7dcb9': {'snapshot_sha256': '5338e35cd0575996e5df0f8d00a6319add42c610764ece7f8bc898d79a30e797', 'archive_sha256': '614377594215e73cc2ecd0e3b2ce12e19da64d4dd6f8f4aa4e55e5604ef52d43', 'file_count': 83},
    '40e6e10d95f444c5a1e1e6c72b4ff997d25a9d1a9caac5c0ff910b1551df677b': {'snapshot_sha256': '36e1e17ace7e5ebaac7b4ef1bb66a1ae8c9212d87f3c60c93c9660cbb9381862', 'archive_sha256': '7e5cfc227fd280ab5052c9cb8937799cde28bd8bf6037e9cd73a32013c842cea', 'file_count': 83},
    '045d6b3d6d3c2f6744b3157a2bd3cbf025b401e2efd215d8a4200182685978dd': {
        'snapshot_sha256': 'adb248f5e22007d4155448f77fe9d845ec1780c1032bb158d8f6d3d50d65964f',
        'archive_sha256': 'c1056d20779c557fd060787d5018c503128778712b81eb669881c89e4e7a0e84',
        'file_count': 80,
    },
    'eeb9864b08e8ae25e841b18b0d25858d95268fce2435d51c340d69a41782f089': {
        'snapshot_sha256': 'fb14e51c7f7d751b13307ecf65573c1863c7f579252aa402231586aeda11412f',
        'archive_sha256': '8576765bdd5b9dbb93db76ec11b485634fa2f34691113a45d59dbf49238c0c87',
        'file_count': 80,
    },
    '1818fc27f076535734d9d9e90a857683f27d464f0a205637e7231cd6e870c40c': {
        'snapshot_sha256': '46070144ca2e2fe7bcfb73292498fceebf669c6a8756c9ec771c6f4dee528851',
        'archive_sha256': '8446ae35115ba9eb1b332ea7395a7be9b1d1be9285073918d711a7466237b163',
        'file_count': 77,
    },
    'a7194b9b52ab8a6db0c92d65c7dae76dc23c1f1c8777b4e10b2fb71efa01c89f': {
        'snapshot_sha256': '602fe4a4d81044adbbd01849284f14c699f2104a36595db2bd6f8e80facf7804',
        'archive_sha256': '54452a9f9375caf4837b00156a98a1be3076b6bd9e4afa2980e8f3d73755e289',
        'file_count': 77,
    },
    "49a9c891446e945b74b28489f4abda522473093ada40e503e1fcd5ce99905f4b": {
        "snapshot_sha256": "97bae287bf823be44033a9e3c174647ed3abb6a15a214e6f4542ba2bb4cc6d64",
        "archive_sha256": "fd1ed9ab3cc8b6b5f98c7b1e04f7bd9255cbc2abee0447cbf9a33f234e28a194",
        "file_count": 75,
    },
    "cefe19d399b19e30175579e427272b790d24eab0e07b54b152e0cd3a45dc5dc4": {
        "snapshot_sha256": "f4f56c8d8e5b8cf7260cb51fa5b87cd8952a2a746294e0050a072c5e3b17f79f",
        "archive_sha256": "19bc1ab5e1c78d3163cc0ff1af4c0acb85f71886ec8cc3973aeab23529ff5714",
        "file_count": 75,
    },
    "42476d67e30e7e86506c3e878552966ce9dc784ae1e5d98bec3af50e6f0a1aa5": {
        "snapshot_sha256": "3a6e9594cf6b094ca6bfce61a4969e854604f5fc4520db90c793aa7fda0b4e58",
        "archive_sha256": "62d395428f49785c005ceaf55d86ed1e66cce12453d8ed2a03146436b5ba0567",
        "file_count": 74,
    },
    "23d04d307c3e560c8198ee0700923673af001a8835d8e00d6c11d79534e6d611": {
        "snapshot_sha256": "2c1b6b30e22b5322046109b461f850974e356736f2aedb06c4911be82375188f",
        "archive_sha256": "b5363658881c8e265295ad727d346ea8925348e9342b89f50eb014be824a19f1",
        "file_count": 74,
    },
    "5d4bf3ec6331dab12ebc735f57203cf6bdbc86a563eae0311a66316eb8b820b1": {
        "snapshot_sha256": "1e9d906428ec3824c4ecbff8ef8fb3adc88d6cb6c9dbfa1819c53655b3206c7c",
        "archive_sha256": "9d5ec76ec904c3696d0e5a76e46fe435e9189322fe0578133c6816707b2fd2c5",
        "file_count": 74,
    },
    "96ffa98008bf1b6a6d1f5ab6b79a330fe4b8a9329887d9ac3f8ff9d31eb12e1e": {
        "snapshot_sha256": "87c7d5dc6c4aa5f46d42f7cd27a1595e2a2844af50da42a45a0f3b3bc09812b9",
        "archive_sha256": "edaff6bb63863e10734993bbaf5101160dab3308b22e763ba188d89fa28e3575",
        "file_count": 74,
    },
    "f1e035f7d20395abb82c2e87ac42f374630bef6bab71a22490873c7a08e8e519": {
        "snapshot_sha256": "2d79ea2227dda5169413eb314b9b65b5bc04fcacb447d00066ef56d3c7b69108",
        "archive_sha256": "af7b88818f8d46a4d810927df39f1eb839c28dd7862f3919c3ac52f66abdbf8e",
        "file_count": 67,
    },
    "c74b029c986fa3e1bb6a6ab3c5cbd423f77c902733626105ec95f5e366b71018": {
        "snapshot_sha256": "6b78f1c8e36058d350d1e572bf20737c3517d38a8498fc4a50ece6bf6725fd30",
        "archive_sha256": "4fbcadee8997087223cbf8ffc365dd7a1b6cac4eb0990350e8925098ec557b51",
        "file_count": 67,
    },
    "22350accf750741680f351b34cf97f95bf146b7389765cd74d937a8aa4291ae4": {
        "snapshot_sha256": "e82b9d72b45d8cbcd667708140b9f5b91a967822002a54a76bc87b097912a2f9",
        "archive_sha256": "0085bb7482ef89d20f0f8667ca015f0cf198ab283d9e439ecc814b9167b13775",
        "file_count": 67,
    },
    RUNTIME_FREEZE_SHA256: {
        "snapshot_sha256": "aaac387085d745b89f0260eb1905d66dade8a710e483034442e7957972243ede",
        "archive_sha256": "31cc7b08586e5c0fa235357d75b36ce23475f486addec6d6d465be4889346c7f",
        "file_count": 58,
    },
    "70e56488ae8a99aa0d52d7ebed53c039d10ed7de9a8c457952515e45277db96e": {
        "snapshot_sha256": "818a1a90e0710daf951bc8108b32f37978938361c0f8f92032840872640c52f3",
        "archive_sha256": "59a575c2f10bb07633d54515dad21b08b35ecde37ba3d909e4748eec82f9eb14",
        "file_count": 58,
    },
    "46b0bdaa68be83f1b62a1536ee3ad548863e90489e4be7e0cdf91b939b131641": {
        "snapshot_sha256": "cd6984487ea0c87ea97b64aa8f89124ac3d947e77e3cc9fda704d2e3668cfd7d",
        "archive_sha256": "7084f8c407ced8a2189872cd3291e4168e088e439549fb139540c7e527f69215",
        "file_count": 58,
    },
}
POST_REVIEW_FREEZE_SHA256 = "a7b39b6dd8011296ddae9aca3c8992169b6fbe452409a6d7d878266631d91656"
# Existing documentation/Git metadata omitted by both historical authoritative
# freezes. No arbitrary new extension or package file receives this exemption.
NON_RUNTIME_PATHS = frozenset({"src/nabt/data/source_evidence/README.md",
                               "src/nabt/data/source_evidence/LICENSE-DATA.md",
                               "src/nabt/data/source_evidence/.gitattributes"})
QAC_SHA256 = "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46"
TABLE_SHA256 = "f8bc2f04fc1225a4f495d71a4c283289a3e8e9c74b9949008eb51e6445e7deb5"
CLASSES = ("iSahih", "iSitta", "iMuthanna", "iJamM", "iJamF", "iMamnu", "iMaqsur", "iManqus",
           "fSahih", "fKhamsaA", "fKhamsaW", "fKhamsaY", "fMutalAlif", "fMutalW", "fMutalY")
CASES = ("nasb", "raf", "jarr", "jazm")
SIGNS = ("damma", "fatha", "kasra", "sukun", "waw", "alif", "ya", "nun_retained", "nun_deleted", "weak_deleted")
MODES = ("overt", "estimated", "deletion")
ORIGINS = ("original", "substitute")
# The unchanged first and corrected-adapter a1 runs expose these unavailable
# complete-base premises; see independent_review_v1.json. The default is still
# strict. CI may opt in only when every remaining miss is one of these IDs and
# no false activation, evidence-integrity or execution failure occurred.
DOCUMENTED_BOUNDARIES = frozenset({"INF-T15", "INF-K10"})
EXPECTED_KEYS = frozenset("""actual_case actual_role allowed_outcomes
attachment_requires_complete_segmentation class_case_contains construction_not_licensed
deletion_requires_retained_full_base_receipt distinct_nun_positions distinct_occurrences_not_interchangeable
emphasis_tag_alone_not_directness_proof forbidden_classes forbidden_licensed_classes forbidden_nun_evidence
forbidden_sign_modes input_occurrence_ids_change kind_contains no_hamza_seat_folding
no_licensed_declension_class no_silent_recitation_mark_stripping no_source_attested_root nun_evidence_contains
only_declared_wasl_lookup_projection raw_bytes_preserved reference_case same_semantic_content sign_contains
singular_origin_absent_without_actual_attestation singular_origin_must_not_cross_same_root_lemma
source_root_contains verification_accepts_original verification_rejects_explicit_model_none""".split())
POST_REVIEW_KEYS = frozenset("""singular_witnesses_empty nominal_semantic_form_not_in class_candidates_empty
present_nun_spans_restore_nun protective_nun_not_acquired deleted_nun_has_no_nonempty_span""".split())


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact_int(value, low, high, name):
    require(type(value) is int and low <= value <= high, "Noncanonical integer: " + name)
    return value


def require_fresh_runtime():
    require(not any(name == "nabt" or name.startswith("nabt.") for name in sys.modules),
            "Run evaluation in a fresh process: a nabt module is already loaded")


def verify_import_origins(runtime_root):
    source = (runtime_root.resolve() / "src").resolve()
    for name, module in sys.modules.items():
        if name == "nabt" or name.startswith("nabt."):
            filename = getattr(module, "__file__", None)
            require(filename is None or Path(filename).resolve().is_relative_to(source),
                    "Imported runtime originated outside the measured source root: " + name)


def load_material():
    freeze_bytes = (FOLDER / "independent_freeze_v1.json").read_bytes()
    require(sha256(freeze_bytes).hexdigest() == FREEZE_SHA256, "Independent freeze changed")
    freeze = json.loads(freeze_bytes)
    for item in freeze["files"]:
        raw = (ROOT / item["path"]).read_bytes()
        require(len(raw) == item["bytes"] and sha256(raw).hexdigest() == item["sha256"],
                "Frozen material changed: " + item["path"])
    material = json.loads((FOLDER / "independent_cases_v1.json").read_bytes())
    cases = material["cases"]
    require(len(cases) == len({c["id"] for c in cases}) == 74, "Case inventory changed")
    for case in cases:
        require(set(case["expected"]) <= EXPECTED_KEYS, "Unimplemented gold predicate")
        require(re.fullmatch(r"[a-z][a-z0-9_]{0,127}", case["input"]["source_id"]) is not None,
                "Invalid adapter source identity")
    return freeze, material, json.loads((FOLDER / "independent_split_v1.json").read_bytes()), \
        json.loads((FOLDER / "independent_sign_law_v1.json").read_bytes())


def pinned_runtime_manifest(manifest_path):
    raw = manifest_path.read_bytes()
    digest = sha256(raw).hexdigest()
    require(digest in PINNED_RUNTIME_FREEZES, "Runtime manifest is not independently pinned")
    manifest = json.loads(raw)
    pin = PINNED_RUNTIME_FREEZES[digest]
    require(len(manifest["files"]) == pin["file_count"], "Unexpected runtime freeze file count")
    require(manifest["snapshot_sha256"] == pin["snapshot_sha256"]
            and manifest["archive_sha256"] == pin["archive_sha256"], "Runtime freeze differs from explicit pins")
    require(sha256(wire(manifest["files"])).hexdigest() == manifest["snapshot_sha256"], "Bad freeze snapshot")
    return manifest, digest


def runtime_snapshot(manifest_path, runtime_root=ROOT):
    manifest_path = manifest_path.resolve()
    runtime_root = runtime_root.resolve()
    manifest, digest = pinned_runtime_manifest(manifest_path)
    actual_paths = {"pyproject.toml"}
    actual_paths.update(str(p.relative_to(runtime_root)) for p in (runtime_root / "src").rglob("*")
                        if p.is_file() and "__pycache__" not in p.parts
                        and not any(part.endswith((".egg-info", ".dist-info")) for part in p.parts))
    expected_paths = [item["path"] for item in manifest["files"]]
    documentation = sorted(actual_paths & NON_RUNTIME_PATHS)
    require(len(expected_paths) == len(set(expected_paths)) and actual_paths - NON_RUNTIME_PATHS == set(expected_paths),
            "Actual source/package inventory differs from the frozen inventory")
    for item in manifest["files"]:
        path = runtime_root / item["path"]
        data = path.read_bytes()
        require(len(data) == item["bytes"] and sha256(data).hexdigest() == item["sha256"],
                "Runtime differs from declared freeze: " + item["path"])
    archive = manifest_path.parent / manifest["archive_filename"]
    require(sha256(archive.read_bytes()).hexdigest() == manifest["archive_sha256"], "Runtime archive changed")
    by_path = {row["path"]: row for row in manifest["files"]}
    with tarfile.open(archive, "r:gz") as saved:
        members = saved.getmembers()
        require(len(members) == len(expected_paths) and {m.name for m in members} == set(expected_paths)
                and all(m.isfile() for m in members), "Runtime archive inventory differs from freeze")
        for member in members:
            payload = saved.extractfile(member).read()
            require(len(payload) == by_path[member.name]["bytes"]
                    and sha256(payload).hexdigest() == by_path[member.name]["sha256"], "Archived runtime bytes differ")
    measured = list(manifest["files"])
    for path in (Path(__file__), ROOT / "tests/test_inflection_review.py"):
        data = path.read_bytes()
        measured.append({"path": str(path.relative_to(ROOT)), "bytes": len(data), "sha256": sha256(data).hexdigest()})
    return {"runtime_freeze": str(manifest_path.relative_to(ROOT)), "runtime_freeze_sha256": digest,
            "runtime_root": str(runtime_root), "runtime_file_count": len(manifest["files"]),
            "non_runtime_documentation_and_git_metadata": documentation,
            "runtime_snapshot_sha256": manifest["snapshot_sha256"], "files": measured,
            "measured_snapshot_sha256": sha256(wire(measured)).hexdigest()}


def preserve_code(snapshot, output):
    path = output.with_suffix(".code.tar.gz")
    require(not path.exists(), "Refusing to overwrite measured code")
    with tarfile.open(path, "w:gz") as archive:
        for index, item in enumerate(snapshot["files"]):
            folder = Path(snapshot["runtime_root"]) if index < snapshot["runtime_file_count"] else ROOT
            data = (folder / item["path"]).read_bytes()
            require(sha256(data).hexdigest() == item["sha256"], "Code changed during measurement capture")
            member = tarfile.TarInfo(item["path"])
            member.size, member.mode, member.mtime = len(data), 0o644, 0
            archive.addfile(member, io.BytesIO(data))
    return {"filename": path.name, "sha256": sha256(path.read_bytes()).hexdigest()}


def source_variant(raw, profile):
    """Alter only prohibited annotation atoms; FORM and allowed fields survive."""
    if profile not in ("case_mood_erased", "case_mood_poisoned"):
        return raw
    output = []
    permutation = {b"NOM": b"ACC", b"ACC": b"GEN", b"GEN": b"NOM",
                   b"MOOD:SUBJ": b"MOOD:JUS", b"MOOD:JUS": b"MOOD:SUBJ"}
    for line in raw.splitlines(keepends=True):
        if not line.startswith(b"("):
            output.append(line)
            continue
        body = line.rstrip(b"\r\n")
        ending = line[len(body):]
        fields = body.split(b"\t")
        require(len(fields) == 4, "Unexpected source record width")
        atoms = fields[3].split(b"|")
        if profile == "case_mood_erased":
            atoms = [a for a in atoms if a not in (b"NOM", b"ACC", b"GEN") and not a.startswith(b"MOOD:")]
        else:
            atoms = [permutation.get(a, a) for a in atoms]
        fields[3] = b"|".join(atoms)
        output.append(b"\t".join(fields) + ending)
    return b"".join(output)


class SourceAudit:
    """Independent byte/annotation checks; never supplies predictions."""
    def __init__(self, raw, exclusions, mapping, source_id="qac"):
        self.raw, self.digest, self.source_id = raw, sha256(raw).hexdigest(), source_id
        self.exclusions, self.mapping = set(exclusions), mapping
        self.rows, cursor, ordinal = {}, 0, 0
        for line in raw.splitlines(keepends=True):
            end = cursor + len(line)
            if line.startswith(b"("):
                ordinal += 1
                fields = line.rstrip(b"\r\n").decode("utf-8").split("\t")
                match = re.fullmatch(r"\(([0-9]+):([0-9]+):([0-9]+):([0-9]+)\)", fields[0])
                require(len(fields) == 4 and match is not None, "Noncanonical QAC source")
                self.rows[(cursor, end)] = {"ordinal": ordinal, "locator": list(map(int, match.groups())),
                                           "form": fields[1], "tag": fields[2], "tokens": fields[3].split("|")}
            cursor = end

    def decode(self, form, *, root=False):
        return "".join("ء" if root and c == "A" else self.mapping.get(c, c) for c in form)

    def receipt(self, receipt):
        start = exact_int(receipt["byte_start"], 0, len(self.raw), "record start")
        end = exact_int(receipt["byte_end"], start + 1, len(self.raw), "record end")
        require((start, end) in self.rows, "Receipt is not a complete source record")
        row = self.rows[(start, end)]
        require(receipt["source_id"] == self.source_id and receipt["source_sha256"] == self.digest,
                "Receipt borrowed another source")
        require(receipt["locator"] == row["locator"] and type(receipt["ordinal"]) is int
                and receipt["ordinal"] == row["ordinal"], "Receipt coordinate differs from raw record")
        require(":".join(map(str, row["locator"][:2])) not in self.exclusions, "Excluded verse used as support")
        identity = ["nabt.corpus-source.v1", "qac", self.source_id, self.digest, start, end, row["ordinal"]]
        require(receipt["record_id"] == sha256(wire(identity)).hexdigest(), "Receipt identity differs")
        return row


def feature(row, name):
    values = [t[len(name) + 1:] for t in row["tokens"] if t.startswith(name + ":")]
    return values[0] if len(values) == 1 else None


def sign_view(row):
    values = {"class": CLASSES[exact_int(row["class"], 0, 14, "class")],
              "case": CASES[exact_int(row["case"], 0, 3, "case")],
              "sign": SIGNS[exact_int(row["sign"], 0, 9, "sign")],
              "mode": MODES[exact_int(row["mode"], 0, 2, "mode")],
              "origin": ORIGINS[exact_int(row["origin"], 0, 1, "origin")]}
    for name in ("case", "sign", "mode", "origin"):
        require(row[name + "_name"] == values[name], "Named sign field differs from numeric law")
    return values


def nun_name(nun):
    if nun["kind"] == "five_verb_raf":
        return "inflection_deleted" if nun["realization"] == "deleted" else "inflection_retained"
    return nun["kind"]


def present_nun_span(nun, reading, inputs):
    """A written nun cluster is an observed byte slice within this reading."""
    span, stem = nun.get("span"), reading.get("stem_span")
    if type(span) is not dict or type(stem) is not dict or nun.get("realization") != "present":
        return False
    raw = inputs["text"].encode("utf-8")
    a, b = span.get("start"), span.get("end")
    if type(a) is not int or type(b) is not int or not (stem["start"] <= a < b <= stem["end"] <= len(raw)):
        return False
    piece = raw[a:b]
    try:
        text = piece.decode("utf-8")
        following = raw[b:].decode("utf-8")
    except UnicodeDecodeError:
        return False
    return bool(text and text[0] == "ن" and all(unicodedata.combining(c) for c in text[1:])
                and (not following or not unicodedata.combining(following[0]))
                and span.get("source_id") == inputs["source_id"]
                and span.get("source_sha256") == sha256(raw).hexdigest()
                and span.get("span_sha256") == sha256(piece).hexdigest()
                and nun.get("surface", text) == text)


def correlated_nun_positions(readings, names, inputs):
    for reading in readings:
        witnessed = {}
        for nun in reading["nun_readings"]:
            name = nun_name(nun)
            if name in names and present_nun_span(nun, reading, inputs):
                witnessed.setdefault(name, []).append((nun["span"]["start"], nun["span"]["end"]))
        if all(name in witnessed for name in names):
            # The public requirement currently compares two nun roles. Test
            # their positions in this same reading, without pooling alternatives.
            for left in witnessed[names[0]]:
                for right in witnessed[names[1]]:
                    if left[1] <= right[0] or right[1] <= left[0]:
                        return True
    return False


def target_occurrences(case, report):
    raw, needle = case["input"]["text"].encode(), case["target_surface"].encode()
    spans, offset = [], 0
    while (start := raw.find(needle, offset)) >= 0:
        spans.append((start, start + len(needle)))
        offset = start + len(needle)
    require(bool(spans), "Gold target is absent from input")
    selected = [o for o in report["occurrences"] if any(o["span"]["start"] <= a < b <= o["span"]["end"]
                                                         for a, b in spans)]
    require(len(selected) == len(spans), "Target occurrence was lost or merged")
    return selected


def semantic_view(report):
    """Read-only projection: discard identities, never alter target text/features."""
    occurrences = []
    for occurrence in report["occurrences"]:
        readings = []
        for reading in occurrence["readings"]:
            lexical = dict(reading.get("lexical_features", {}))
            lexical["singular_witnesses"] = [{k: w[k] for k in ("form", "root")}
                                             for w in lexical.get("singular_witnesses", [])]
            view = {k: reading.get(k) for k in ("kind", "construction", "construction_basis", "class_candidates",
                    "variant", "base_form", "actual_role", "actual_case", "local_case", "obligations",
                    "operator_relation", "operator_qualified", "al_evidence", "prefix_relation")}
            view["lexical_features"] = lexical
            view["signs"] = sorted([sign_view(s) for s in reading["sign_candidates"]], key=wire)
            view["nun"] = sorted([{"kind": n["kind"], "realization": n.get("realization")}
                                  for n in reading.get("nun_readings", [])], key=wire)
            view["segmentation"] = [{"kind": p["kind"], "surface": p["surface"],
                                      "start": p["span"]["start"] - occurrence["span"]["start"],
                                      "end": p["span"]["end"] - occurrence["span"]["start"]}
                                     for p in reading["segmentation"]["parts"]]
            readings.append(view)
        occurrences.append({"surface": occurrence["surface"], "kind": occurrence["kind"],
                            "status": occurrence["status"], "obligations": occurrence["obligations"],
                            "readings": sorted(readings, key=wire)})
    relations = [{k: rel[k] for k in ("label", "activated", "case_name", "case_domain", "receipt_mask")}
                 for rel in report["relations"]]
    return {"occurrences": occurrences, "relations": sorted(relations, key=wire), "status": report["status"],
            "frame_status": report["frame_status"], "semantic_facts": report["semantic_facts"]}


def validate_relations(report, inputs):
    """Check law, endpoints and support references independently of receipt bits.

    A satisfiable mask is insufficient when a purported governor or case domain
    was borrowed from another reading. This checker also runs in mutation tests
    without reloading the external corpus; source-record checks remain separate.
    """
    raw = inputs["text"].encode("utf-8")
    digest = sha256(raw).hexdigest()
    occurrences = {o["occurrence_id"]: o for o in report["occurrences"]}
    readings = {r["reading_id"]: (o, r) for o in report["occurrences"] for r in o["readings"]}
    laws = {"min_preposition": ("preposition_object", "jarr", "noun"),
            "lam_activation": ("imperfect_jussive", "jazm", "verb"),
            "subjunctive_lan": ("imperfect_subjunctive", "nasb", "verb")}
    operators = {"من": "min_preposition", "إلى": "min_preposition", "عن": "min_preposition",
                 "على": "min_preposition", "في": "min_preposition", "لم": "lam_activation", "لن": "subjunctive_lan"}
    active_ids = set()
    for relation in report["relations"]:
        require(type(relation["activated"]) is bool, "Activation is not a strict boolean")
        mask = exact_int(relation["receipt_mask"], 0, 255, "receipt mask")
        require(relation["activated"] == (mask == 247), "Activation differs from independent receipt conjunction")
        head, dependent = relation["head"], relation["dependent"]
        require(dependent["reading_id"] in readings, "Unknown dependent reading")
        occurrence, reading = readings[dependent["reading_id"]]
        require(dependent["occurrence_id"] == occurrence["occurrence_id"]
                and dependent["occurrence_span"] == occurrence["span"]
                and dependent["span"] == reading["stem_span"], "Dependent endpoint borrowed another occurrence")
        for field in ("source_id", "source_sha256", "scope", "segmentation_id", "lexical_id", "law"):
            require(dependent[field] == reading["identity"][field], "Dependent identity field differs: " + field)
        for endpoint in (head, dependent):
            require(endpoint["source_id"] == inputs["source_id"] and endpoint["source_sha256"] == digest
                    and endpoint["scope"] == inputs["scope"], "Attachment borrowed source or scope")
        require(head["occurrence_id"] in occurrences, "Unknown head occurrence")
        head_occurrence = occurrences[head["occurrence_id"]]
        rule = head["rule_id"]
        require(rule in laws, "Unknown head grammar rule")
        if head["occurrence_id"] == dependent["occurrence_id"]:
            matching = [p for p in reading["segmentation"]["parts"]
                        if p["kind"] == "preposition" and p["span"] == head["span"]]
            require(len(matching) == 1 and reading["prefix_relation"] == "preposition_object",
                    "Attached governor lacks its own segmentation part")
            letters = "".join(c for c in matching[0]["surface"] if not unicodedata.combining(c))
            require(letters in ("ب", "ك", "ل") and rule == "min_preposition", "Attached head rule differs from letters")
            require(head["reading_id"] == sha256(wire([reading["reading_id"], "prep"])).hexdigest()
                    and head["segmentation_id"] == reading["segmentation_id"], "Attached head identity differs")
            qualified = reading["segmentation"]["licensed"] is True
        else:
            require(head["reading_id"] in readings, "Unknown head reading")
            registered_occurrence, operator = readings[head["reading_id"]]
            require(registered_occurrence["occurrence_id"] == head_occurrence["occurrence_id"]
                    and head["span"] == head_occurrence["span"]
                    and head["segmentation_id"] == operator["segmentation_id"], "Head endpoint borrowed another reading")
            letters = "".join(c for c in head_occurrence["surface"] if not unicodedata.combining(c))
            require(operators.get(letters) == rule and operator.get("operator_rule") == rule
                    and operator.get("operator_relation") == laws[rule][0] and operator["kind"] == "particle",
                    "Head grammar rule differs from written operator")
            qualified = operator.get("operator_qualified") is True and operator["segmentation"]["licensed"] is True
        require(head["span"]["end"] <= dependent["span"]["start"], "Attachment overlaps its governor")
        label, case, kind = laws[rule]
        domain = None if reading["construction"] is None else "local_case" if reading["construction"] == "built" else "inflected_case"
        require(relation["label"] == label and relation["case_name"] == case
                and exact_int(relation["case"], 0, 3, "relation case") == CASES.index(case)
                and relation["case_domain"] == domain, "Relation law/case/domain differs from governor and construction")
        supports = relation["supports"]
        require([s for s in supports if s.get("kind") == "head_occurrence"] == [{"kind": "head_occurrence", **head}],
                "Head support differs from head endpoint")
        require([s for s in supports if s.get("kind") == "dependent_occurrence"] == [{"kind": "dependent_occurrence", **dependent}],
                "Dependent support differs from dependent endpoint")
        require([s for s in supports if s.get("kind") == "lexical_source"]
                == [{"kind": "lexical_source", "records": reading["support_records"]}], "Lexical support differs from reading")
        grammar = [s for s in supports if s.get("kind") == "source_grammar"]
        require(len(grammar) == 1 and grammar[0]["rule"] == rule, "Grammar support differs from head rule")
        observed_signs = {wire(sign_view(s)) for s in reading["sign_candidates"]}
        require(all(s["case_name"] == case and wire(sign_view(s)) in observed_signs
                    for s in relation["sign_candidates"]), "Relation signs are not correlated reading signs")
        if relation["activated"]:
            require(qualified and reading["kind"] == kind and reading["construction"] in ("built", "inflected"),
                    "Active relation lacks a licensed governor, kind, or construction")
            require(reading["actual_role"] == label and reading["actual_case"] == (case if domain == "inflected_case" else None)
                    and reading["local_case"] == (case if domain == "local_case" else None),
                    "Active relation case/domain differs from its reading assignment")
            active_ids.add(reading["reading_id"])
    require(active_ids == {a["reading_id"] for a in report["assignments"]}, "Assignments and activated endpoints differ")


def validate_report(case, report, audit):
    inputs = case["input"]
    raw = inputs["text"].encode("utf-8")
    digest = sha256(raw).hexdigest()
    require(report["raw_text"].encode("utf-8") == raw, "Raw text was rewritten")
    require(report["source_id"] == inputs["source_id"] and report["source_sha256"] == digest
            and report["scope"] == inputs["scope"], "Report borrowed source identity")
    require(report["table_sha256"] == TABLE_SHA256, "Conditional law table changed")
    require(report["semantic_facts"] == [], "Inflection emitted world/semantic facts")

    def span(value, surface=None):
        a = exact_int(value["start"], 0, len(raw), "span start")
        b = exact_int(value["end"], a + 1, len(raw), "span end")
        part = raw[a:b]
        require(value["source_id"] == inputs["source_id"] and value["source_sha256"] == digest
                and value["span_sha256"] == sha256(part).hexdigest(), "Span source identity differs")
        require(surface is None or part.decode("utf-8") == surface, "Span does not restore surface")
        return a, b

    cursor = 0
    for item in report["source_partition"]:
        a, cursor_next = span(item["span"], item["surface"])
        require(a == cursor, "Raw partition has a gap or overlap")
        cursor = cursor_next
    require(cursor == len(raw), "Raw partition lost bytes")
    occurrence_ids, reading_index, expected_assignments = set(), {}, []
    for occurrence in report["occurrences"]:
        a, b = span(occurrence["span"], occurrence["surface"])
        oid = occurrence["occurrence_id"]
        require(oid not in occurrence_ids, "Distinct occurrences share an identity")
        occurrence_ids.add(oid)
        require(any(p["span"] == occurrence["span"] and p["kind"] == occurrence["kind"]
                    for p in report["source_partition"]), "Occurrence is not bound to raw partition")
        for reading in occurrence["readings"]:
            rid = reading["reading_id"]
            require(rid not in reading_index, "Reading identities merged")
            reading_index[rid] = reading
            for cls in reading.get("class_candidates", []):
                exact_int(cls, 0, 14, "class candidate")
            for sign in reading["sign_candidates"]:
                sign_view(sign)
            for nun in reading.get("nun_readings", []):
                if nun.get("realization") == "present" and nun.get("span") is not None:
                    require(present_nun_span(nun, reading, inputs), "Nun span is not a written nun in its reading")
            cursor = a
            for part in reading["segmentation"]["parts"]:
                lo, hi = span(part["span"], part["surface"])
                require(lo == cursor, "Segmentation has a gap or overlap")
                cursor = hi
            require(cursor == b and reading["segmentation"]["coverage_valid"] is True,
                    "Segmentation does not conserve its occurrence")
            if "identity" in reading:
                identity = reading["identity"]
                require(identity["occurrence_id"] == oid and identity["span"] == occurrence["span"]
                        and identity["source_id"] == inputs["source_id"] and identity["scope"] == inputs["scope"]
                        and identity["source_sha256"] == digest and sha256(wire(identity)).hexdigest() == rid,
                        "Content reading is not bound to occurrence/source/scope")
                span(reading["stem_span"], reading["stem_surface"])
            supports = reading.get("support_records", [])
            require(not supports or audit is not None, "Model-free reading invented source receipts")
            rows = [audit.receipt(s) for s in supports]
            for receipt in reading.get("construction_supports", []):
                audit.receipt(receipt)
            lexical = reading["lexical_features"]
            stems = [r for r in rows if r["tokens"][0] == "STEM"]
            if lexical.get("root"):
                require(any(feature(r, "ROOT") and audit.decode(feature(r, "ROOT"), root=True) == lexical["root"]
                            for r in stems), "Attested root lacks a matching source ROOT witness")
            if lexical.get("lemma"):
                require(any(feature(r, "LEM") and audit.decode(feature(r, "LEM")) == lexical["lemma"]
                            for r in stems), "Lemma lacks a matching source witness")
            for witness in lexical.get("singular_witnesses", []):
                singulars = [audit.receipt(s) for s in witness["supports"]]
                singulars = [s for s in singulars if s["tokens"][0] == "STEM"]
                require(any(any(re.fullmatch(r"[123]?[MF]?S", t) for t in s["tokens"])
                            and feature(s, "ROOT") and audit.decode(feature(s, "ROOT"), root=True) == lexical["root"]
                            and feature(s, "LEM") and audit.decode(feature(s, "LEM")) == lexical["lemma"]
                            and s["tag"] == lexical["pos"] for s in singulars),
                        "Singular origin lacks same-lemma/root/POS explicit singular attestation")
            if reading["actual_role"] is not None:
                require(reading["construction"] in ("built", "inflected") and bool(supports),
                        "Actual role has no construction or independent lexical evidence")
                require((reading["actual_case"] is None) == (reading["construction"] == "built"),
                        "Built local case and inflected case were collapsed")
                expected_assignments.append({"reading_id": rid, "occurrence_id": oid,
                                             "role": reading["actual_role"], "inflected_case": reading["actual_case"],
                                             "local_case": reading["local_case"]})
    require(sorted(report["assignments"], key=wire) == sorted(expected_assignments, key=wire),
            "Assignment list differs from correlated reading assignments")
    for relation in report["relations"]:
        span(relation["head"]["span"])
        span(relation["dependent"]["span"])
    validate_relations(report, inputs)
    return target_occurrences(case, report)


def full_base_witness(reading, audit):
    base = reading.get("base_form")
    if not base or audit is None:
        return False
    groups = defaultdict(list)
    for receipt in reading.get("support_records", []):
        row = audit.receipt(receipt)
        groups[tuple(row["locator"][:3])].append(row)
    for rows in groups.values():
        rows = sorted(rows, key=lambda r: r["locator"][3])
        stems = [i for i, row in enumerate(rows) if row["tokens"][0] == "STEM"]
        for first in stems:
            for last in range(first + 1, len(rows) + 1):
                restored = audit.decode("".join(r["form"] for r in rows[first:last]))
                if unicodedata.normalize("NFC", restored) == unicodedata.normalize("NFC", base):
                    return True
    return False


def score_case(case, report, audit, references, verification=None):
    failures, checks = [], []

    def check(name, condition, *, coverage=False, detail=None):
        require(type(condition) is bool, "Scorer predicate did not return bool: " + name)
        checks.append({"predicate": name, "passed": condition})
        if not condition:
            failures.append({"predicate": name, "category": "coverage_miss" if coverage else "false_accept",
                             "detail": detail})

    try:
        occurrences = validate_report(case, report, audit)
        check("source_and_reading_integrity", True)
    except ValueError as error:
        check("source_and_reading_integrity", False, detail=str(error))
        occurrences = target_occurrences(case, report)
    readings = [r for o in occurrences for r in o["readings"]]
    expected = case["expected"]
    eligible = [r for r in readings if (not expected.get("kind_contains") or r["kind"] in expected["kind_contains"])
                and (not expected.get("source_root_contains")
                     or r["lexical_features"].get("root") in expected["source_root_contains"])]
    signs = [sign_view(s) for r in eligible for s in r["sign_candidates"]]
    for kind in expected.get("kind_contains", []):
        check("kind:" + kind, any(r["kind"] == kind for r in readings), coverage=True)
    for root in expected.get("source_root_contains", []):
        check("source_root:" + root, any(r["lexical_features"].get("root") == root for r in eligible), coverage=True)
    for wanted in expected.get("class_case_contains", []):
        check("class_case:" + wanted["class"] + ":" + wanted["case"],
              any(all(s[k] == v for k, v in wanted.items()) for s in signs), coverage=True)
    for wanted in expected.get("sign_contains", []):
        check("sign:" + ":".join(wanted.values()),
              any(all(s[k] == v for k, v in wanted.items()) for s in signs), coverage=True)
    if "actual_case" in expected:
        wanted = expected["actual_case"]
        role = expected.get("actual_role")
        if role == "governed_imperfect":
            role = "imperfect_jussive" if wanted == "jazm" else "imperfect_subjunctive"
        if wanted is None:
            check("no_actual_assignment", all(r["actual_case"] is None and r["actual_role"] is None
                                               and r["local_case"] is None for r in readings))
        else:
            check("no_wrong_actual_assignment", all(r["actual_case"] in (None, wanted)
                  and r["actual_role"] in (None, role) and r["local_case"] is None for r in readings))
            correlated = [r for r in eligible if r["actual_case"] == wanted and r["actual_role"] == role
                          and all(any(all(sign_view(s)[k] == v for k, v in required.items())
                                      for s in r["sign_candidates"])
                                  for required in expected.get("class_case_contains", []))]
            check("correlated_actual_assignment", bool(correlated), coverage=True)
    classes = {CLASSES[c] for r in readings for c in r.get("class_candidates", [])}
    licensed = {CLASSES[c] for r in readings if r["construction"] == "inflected" for c in r.get("class_candidates", [])}
    for flag in ("construction_not_licensed", "no_licensed_declension_class"):
        if expected.get(flag):
            check(flag, not licensed and all(r["construction"] != "inflected" for r in readings))
    for name in expected.get("forbidden_classes", []):
        check("forbidden_class:" + name, name not in classes)
    for name in expected.get("forbidden_licensed_classes", []):
        check("forbidden_licensed_class:" + name, name not in licensed)
    for name in expected.get("forbidden_sign_modes", []):
        check("forbidden_sign_mode:" + name, all(s["mode"] != name for s in signs))
    if expected.get("no_source_attested_root"):
        check("no_source_attested_root", all(not r["lexical_features"].get("root") for r in readings))
    nuns = [n for r in readings for n in r["nun_readings"]]
    eligible_nuns = [n for r in eligible for n in r["nun_readings"]]
    for name in expected.get("nun_evidence_contains", []):
        check("nun_evidence:" + name, any(nun_name(n) == name for n in eligible_nuns), coverage=True)
    for name in expected.get("forbidden_nun_evidence", []):
        check("forbidden_nun:" + name, all(nun_name(n) != name for n in nuns))
    if expected.get("distinct_nun_positions"):
        check("distinct_nun_positions", correlated_nun_positions(eligible, expected["nun_evidence_contains"], case["input"]),
              coverage=True)
    if expected.get("deletion_requires_retained_full_base_receipt"):
        deleted = [r for r in eligible if any(s["mode_name"] == "deletion" for s in r["sign_candidates"])]
        check("deletion_full_base_receipt", all(full_base_witness(r, audit) for r in deleted))
    if expected.get("distinct_occurrences_not_interchangeable"):
        check("distinct_occurrences_not_interchangeable", len(occurrences) >= 2
              and len({o["occurrence_id"] for o in occurrences}) == len(occurrences))
    if expected.get("attachment_requires_complete_segmentation"):
        active = [r for r in readings if r["actual_role"] is not None]
        check("attachment_requires_complete_segmentation", all(r["segmentation"]["coverage_valid"] is True
              and r["segmentation"]["licensed"] is True and any(p["kind"] == "preposition"
              for p in r["segmentation"]["parts"]) for r in active))
    # These source/representation predicates are checked for every case above;
    # keep explicit result rows so that no frozen expectation disappears.
    for flag in ("singular_origin_absent_without_actual_attestation", "singular_origin_must_not_cross_same_root_lemma",
                 "raw_bytes_preserved"):
        if expected.get(flag):
            check(flag, not any(f["predicate"] == "source_and_reading_integrity" for f in failures))
    if expected.get("only_declared_wasl_lookup_projection"):
        check("only_declared_wasl_lookup_projection", report["lexical_source"]["lookup_id"]
              == "qac.lookup.wasl-equivalence.v1")
    if expected.get("no_hamza_seat_folding"):
        check("no_hamza_seat_folding", all(not r["lexical_features"].get("root") for r in readings))
    if expected.get("emphasis_tag_alone_not_directness_proof"):
        check("emphasis_tag_alone_not_directness_proof", all(n.get("directness") in (None, "unknown", "candidate")
              for n in nuns if nun_name(n) == "emphasis"))
    if expected.get("no_silent_recitation_mark_stripping"):
        # A bounded unsupported-profile deferral is explicitly allowed. A future
        # exact analysis must identify the retained ornament in its segmentation.
        exact = bool(readings) and all(any("۟" in p["surface"] and p["kind"] == "recitation_mark"
                    for p in r["segmentation"]["parts"]) for r in readings)
        deferred = not readings and all(o["status"] == "DEFER" for o in occurrences)
        check("no_silent_recitation_mark_stripping", exact or deferred)
        outcome = "source_supported_exact_analysis" if exact else "defer_unsupported_mark" if deferred else "other"
        check("allowed_outcomes", outcome in expected["allowed_outcomes"])
    if expected.get("same_semantic_content"):
        reference = references[expected["reference_case"]]
        check("same_semantic_content", wire(semantic_view(report)) == wire(semantic_view(reference)))
        if expected.get("input_occurrence_ids_change"):
            check("input_occurrence_ids_change", not ({o["occurrence_id"] for o in report["occurrences"]}
                  & {o["occurrence_id"] for o in reference["occurrences"]}))
    if expected.get("verification_accepts_original"):
        check("verification_accepts_original", verification["original"]["valid"] is True)
    if expected.get("verification_rejects_explicit_model_none"):
        check("verification_rejects_explicit_model_none", verification["withdrawn"]["valid"] is False)
    if expected.get("class_candidates_empty"):
        check("class_candidates_empty", all(r.get("class_candidates", []) == [] for r in readings))
    if expected.get("singular_witnesses_empty"):
        check("singular_witnesses_empty", all(r["lexical_features"].get("singular_witnesses", []) == [] for r in readings))
    if "nominal_semantic_form_not_in" in expected:
        check("nominal_semantic_form_not_in", all(r["lexical_features"].get("nominal_form")
              not in expected["nominal_semantic_form_not_in"] for r in readings))
    if expected.get("present_nun_spans_restore_nun"):
        present = [(r, n) for r in readings for n in r["nun_readings"] if n.get("realization") == "present"]
        check("present_nun_spans_restore_nun", bool(present)
              and all(present_nun_span(n, r, case["input"]) for r, n in present), coverage=True)
    if expected.get("deleted_nun_has_no_nonempty_span"):
        deleted = [n for n in nuns if n.get("realization") == "deleted"]
        check("deleted_nun_has_no_nonempty_span", all(n.get("span") is None or
              (type(n["span"]) is dict and type(n["span"].get("start")) is int
               and type(n["span"].get("end")) is int
               and n["span"]["start"] == n["span"].get("end")) for n in deleted))
    if expected.get("protective_nun_not_acquired"):
        check("protective_nun_not_acquired", all(nun_name(n) not in
              {"protective", "protective_nun", "protection", "wiqaya"} for n in nuns))
    return {"id": case["id"], "track": case["track"], "passed": not failures, "failures": failures,
            "checks": checks, "target_readings": len(readings), "target_licensed_readings": len(licensed),
            "report_status": report["status"], "observed": semantic_view(report)}


def load_post_review_material():
    path = FOLDER / "independent_post_review_freeze_v1.json"
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == POST_REVIEW_FREEZE_SHA256, "Post-review freeze changed")
    for row in json.loads(raw)["files"]:
        data = (ROOT / row["path"]).read_bytes()
        require(len(data) == row["bytes"] and sha256(data).hexdigest() == row["sha256"], "Post-review material changed")
    material = json.loads((FOLDER / "independent_post_review_cases_v1.json").read_bytes())
    require(len(material["cases"]) == len({c["id"] for c in material["cases"]}) == 22, "Post-review inventory changed")
    require(all(set(c["expected"]) <= EXPECTED_KEYS | POST_REVIEW_KEYS for c in material["cases"]),
            "Unimplemented post-review gold predicate")
    return material


def evaluate_post_review(output, manifest_path, runtime_root=ROOT):
    require_fresh_runtime()
    require(not output.exists(), "Refusing to overwrite a measurement")
    load_material()
    material = load_post_review_material()
    split = json.loads((FOLDER / "independent_split_v1.json").read_bytes())
    snapshot = runtime_snapshot(manifest_path, runtime_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    capture = preserve_code(snapshot, output)
    result = {"schema": VERSION + ".post-review", "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "freeze_sha256": POST_REVIEW_FREEZE_SHA256, "held_out_claim": False,
              "snapshot": snapshot, "code_archive": capture, "cases": []}
    sys.path.insert(0, str(runtime_root.resolve() / "src"))
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.inflection_reader import read_inflection
    verify_import_origins(runtime_root)
    raw_path = output.with_suffix(".raw.jsonl.gz")
    require(not raw_path.exists(), "Refusing to overwrite raw measurement")
    with gzip.open(raw_path, "wt", encoding="utf-8") as raw_log:
        for case in material["cases"]:
            raw = case["source_tsv"].encode("utf-8")
            inputs = case["input"]
            try:
                model = learn_qac_lexicon(raw, source_id=case["lexical_source_id"])
                report = read_inflection(inputs["text"], lexical_model=model,
                                         source_id=inputs["source_id"], scope=inputs["scope"])
                raw_log.write(wire({"case_id": case["id"], "report": report}).decode() + "\n")
                raw_log.flush()
                audit = SourceAudit(raw, (), split["mapping"], source_id=case["lexical_source_id"])
                entry = score_case(case, report, audit, {})
            except Exception as error:
                entry = {"id": case["id"], "track": case["track"], "passed": False,
                         "failures": [{"predicate": "post_review_execution", "category": "execution_error",
                                       "detail": repr(error)}], "traceback": traceback.format_exc()}
            result["cases"].append(entry)
            raw_log.write(wire({"case_id": case["id"], "score": entry}).decode() + "\n")
            raw_log.flush()
    categories = Counter(category for row in result["cases"] for category in {f["category"] for f in row["failures"]})
    passed = sum(c["passed"] for c in result["cases"])
    result.update({"completed_at_utc": datetime.now(timezone.utc).isoformat(), "passed": passed, "total": 22,
                   "failure_categories": dict(categories), "gate_pass": passed == 22,
                   "raw_log": {"filename": raw_path.name, "sha256": sha256(raw_path.read_bytes()).hexdigest()}})
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "passed": passed, "total": 22, "failure_categories": dict(categories)}, ensure_ascii=False))
    return result


def evaluate(qac_path, output, manifest_path, allow_boundaries=False, runtime_root=ROOT):
    require_fresh_runtime()
    require(not output.exists(), "Refusing to overwrite a measurement")
    freeze, material, split, law = load_material()
    snapshot = runtime_snapshot(manifest_path, runtime_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    capture = preserve_code(snapshot, output)
    source_bytes = qac_path.read_bytes()
    raw = gzip.decompress(source_bytes) if source_bytes.startswith(b"\x1f\x8b") else source_bytes
    require(sha256(raw).hexdigest() == QAC_SHA256, "QAC input differs from independently pinned decoded source")
    raw_path = output.with_suffix(".raw.jsonl.gz")
    require(not raw_path.exists(), "Refusing to overwrite raw measurement")
    result = {"schema": VERSION, "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "gold_freeze_sha256": FREEZE_SHA256, "frozen_case_count": 74, "snapshot": snapshot,
              "code_archive": capture, "qac_decoded_sha256": QAC_SHA256, "model_profiles": {},
              "source_scope": "QAC-annotated lexical evidence transferred to authored raw inputs; case/mood labels masked",
              "not_claimed": ["untouched external corpus", "unsupervised acquisition of lexical meanings or roots",
                              "general dependency parsing", "world-truth or broad semantic episode accuracy"],
              "cases": [], "conditional_sign_law": []}
    # All production imports/calls occur after gold and code capture.
    sys.path.insert(0, str(runtime_root.resolve() / "src"))
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.inflection_reader import read_inflection, verify_inflection
    from nabt.inflection import sign_candidates
    verify_import_origins(runtime_root)

    models, audits, references = {}, {}, {}
    with gzip.open(raw_path, "wt", encoding="utf-8") as raw_log:
        def log(value):
            raw_log.write(wire(value).decode("utf-8") + "\n")
            raw_log.flush()

        for wanted in law["admitted_rows"]:
            try:
                rows = sign_candidates([CLASSES.index(wanted["class"])], cases=[CASES.index(wanted["case"])], al=2, idhafa=2)
                observed = [sign_view(r) for r in rows]
                passed = observed == [wanted]
                entry = {"expected": wanted, "observed": observed, "passed": passed}
            except Exception as error:
                entry = {"expected": wanted, "passed": False, "exception": repr(error)}
            result["conditional_sign_law"].append(entry)
            log({"law": entry})
        for wanted in law["excluded_class_case"]:
            rows = sign_candidates([CLASSES.index(wanted["class"])], cases=[CASES.index(wanted["case"])], al=2, idhafa=2)
            entry = {"excluded": wanted, "observed": rows, "passed": rows == []}
            result["conditional_sign_law"].append(entry)
            log({"law": entry})
        for case in material["cases"]:
            inputs, profile = case["input"], case["input"]["model_profile"]
            report, verification = None, None
            try:
                if profile == "no_model":
                    model, audit = None, None
                else:
                    if profile not in models:
                        modified = source_variant(raw, profile)
                        exclusion_rows = split["additional_model_profiles"].get(profile, {}).get("excluded_verses", split["excluded_verses"])
                        exclusions = tuple(":".join(map(str, pair)) for pair in exclusion_rows)
                        models[profile] = learn_qac_lexicon(modified, excluded_verses=exclusions, source_id="qac")
                        audits[profile] = SourceAudit(modified, exclusions, split["mapping"])
                        result["model_profiles"][profile] = models[profile].summary()
                        log({"model_profile": profile, "summary": result["model_profiles"][profile]})
                        print("prepared model", profile, flush=True)
                    model, audit = models[profile], audits[profile]
                report = read_inflection(inputs["text"], lexical_model=model,
                                         source_id=inputs["source_id"], scope=inputs["scope"])
                if case["action"] == "verify_model_withdrawal":
                    verification = {"original": verify_inflection(report, lexical_model=model),
                                    "withdrawn": verify_inflection(report, lexical_model=None)}
                log({"case_id": case["id"], "report": report, "verification": verification})
            except Exception as error:
                entry = {"id": case["id"], "track": case["track"], "passed": False,
                         "failures": [{"predicate": "production_execution", "category": "execution_error",
                                       "detail": repr(error)}], "traceback": traceback.format_exc()}
                log({"case_id": case["id"], "execution_error": entry})
                result["cases"].append(entry)
                continue
            try:
                entry = score_case(case, report, audit, references, verification)
            except Exception as error:
                entry = {"id": case["id"], "track": case["track"], "passed": False,
                         "failures": [{"predicate": "scorer_execution", "category": "adapter_error",
                                       "detail": repr(error)}], "traceback": traceback.format_exc()}
            references[case["id"]] = report
            result["cases"].append(entry)
            log({"case_id": case["id"], "score": entry})
            if not entry["passed"]:
                print(case["id"], [(f["category"], f["predicate"]) for f in entry["failures"]], flush=True)
    totals, strata = Counter(), defaultdict(Counter)
    for row in result["cases"]:
        categories = {f["category"] for f in row["failures"]}
        totals["total"] += 1
        totals["passed"] += row["passed"]
        strata[row["track"]]["total"] += 1
        strata[row["track"]]["passed"] += row["passed"]
        for category in categories:
            totals[category + "_cases"] += 1
            strata[row["track"]][category + "_cases"] += 1
    for category in ("false_accept", "coverage_miss", "execution_error", "adapter_error"):
        totals.setdefault(category + "_cases", 0)
    failures = {c["id"] for c in result["cases"] if not c["passed"]}
    safe_only = not any(totals[k + "_cases"] for k in ("false_accept", "execution_error", "adapter_error"))
    law_passed = sum(r["passed"] for r in result["conditional_sign_law"])
    waived = failures if allow_boundaries and safe_only and failures <= DOCUMENTED_BOUNDARIES else set()
    result.update({"completed_at_utc": datetime.now(timezone.utc).isoformat(), "summary": dict(totals),
                   "strata": {k: dict(v) for k, v in strata.items()}, "conditional_law_score": [law_passed, 60],
                   "documented_boundary_mode": allow_boundaries, "waived_coverage_ids": sorted(waived),
                   "strict_pass": not failures and law_passed == 60,
                   "gate_pass": (not failures or bool(waived)) and safe_only and law_passed == 60,
                   "raw_log": {"filename": raw_path.name, "sha256": sha256(raw_path.read_bytes()).hexdigest()}})
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "summary": result["summary"], "conditional_law_score": result["conditional_law_score"],
                      "strict_pass": result["strict_pass"], "gate_pass": result["gate_pass"]}, ensure_ascii=False), flush=True)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qac", type=Path, help="Pinned original QAC .txt or .txt.gz (required for the original 74 cases)")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime-freeze", type=Path, default=ROOT / "evidence/arabic_completion_v4/code_freeze_v2.json")
    parser.add_argument("--runtime-root", type=Path, default=ROOT,
                        help="Measured source checkout or extracted pinned archive; verified against the selected freeze")
    parser.add_argument("--allow-documented-boundaries", action="store_true",
                        help="CI replay only; never waive false accepts, source failures, or execution errors")
    parser.add_argument("--post-review", action="store_true", help="Run the separately frozen authored 22-case regression set")
    args = parser.parse_args(argv)
    if args.post_review:
        require(not args.allow_documented_boundaries, "Post-review regression has no permitted failures")
        result = evaluate_post_review(args.output, args.runtime_freeze, args.runtime_root)
    else:
        require(args.qac is not None, "Supply --qac for the original 74 cases")
        result = evaluate(args.qac, args.output, args.runtime_freeze, args.allow_documented_boundaries, args.runtime_root)
    return 0 if result["gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
