#!/usr/bin/env python3
"""Evaluate source-fixed morphology cases without importing an answer parser.

V1 material predates implementation inspection. V2 makes the declared source
correction from event time to time indicated by form, and is consequently a
regression set rather than an untouched holdout. The adapter below only maps
public report fields to authored semantic expectations. It never repairs an
input, calls the runtime's clause table as an oracle, or changes case gold.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

VERSION = "nabt.morphology.independent-evaluator.v1.6"
MATERIAL_SHA256 = {
    "v1": "4425a249fe64b627c36671a39a88fec79ad8ac0c9f3ce710bab726045ccc2f81",
    "v2": "0f17e68a4d7a33d4afa64bb645ba88c55ac1d0e3248de241f1c1028442d37ea4",
}
MATERIAL_COUNTS = {"v1": 42, "v2": 43}
SCOPE = "independent_morphology_review"
DOCUMENTED_BOUNDARY_MISSES = {"m12", "m13", "m32", "m33"}
FREEZE_MANIFEST_SHA256 = "8449c5c4bf32549c6147de006b0586d41cb4c6f656e2764c63e3437a35b7bffd"
FROZEN_RUNTIME_SHA256 = "4b5c8f4f7c2bb765791e0a9c94e1be279a1a3ad1e186e6346d77546f23a47d46"
FROZEN_ARCHIVE_SHA256 = "f657df1db06f714789e8bbf64708770a5355b0f9542281798ba43735286a042a"
CODE_FREEZES = {
    'arabic_completion_v6': ('31bd37d919364742033a08ab4cb557e93b92280539dd7a55364763cae236dfec', '8d2e24747ee0a4ba454c1eaeb4936ba510945a24992653a47db9664348029d23', '15bfc5ffdd08667cb79bf530d3b5baecd49f1c0493b8bf252f934b5fea55a922'),
    'arabic_completion_v5': ('06f4f774c5637936b41be95360b07ad6cfe8aaeaa9fee1514396db501112ce57', '1ad20efd09752b7f66aae30ceeac1b442c5b520bcf494e528f8a9097bd5de68c', 'a377cba60bfd1491351322b6543678e023ac83b18ec0cb2543f181f046d318ed'),
    "arabic_completion_v4_review2": ('eda208c3e092a8185a3223ba8f0848ff6d0232aca3b8c3e94645482233d7dcb9', '5338e35cd0575996e5df0f8d00a6319add42c610764ece7f8bc898d79a30e797', '614377594215e73cc2ecd0e3b2ce12e19da64d4dd6f8f4aa4e55e5604ef52d43'),
    "arabic_completion_v4": ('40e6e10d95f444c5a1e1e6c72b4ff997d25a9d1a9caac5c0ff910b1551df677b', '36e1e17ace7e5ebaac7b4ef1bb66a1ae8c9212d87f3c60c93c9660cbb9381862', '7e5cfc227fd280ab5052c9cb8937799cde28bd8bf6037e9cd73a32013c842cea'),
    "arabic_completion_v3_review2": ("045d6b3d6d3c2f6744b3157a2bd3cbf025b401e2efd215d8a4200182685978dd",
                                     "adb248f5e22007d4155448f77fe9d845ec1780c1032bb158d8f6d3d50d65964f",
                                     "c1056d20779c557fd060787d5018c503128778712b81eb669881c89e4e7a0e84"),
    "arabic_completion_v3": ("eeb9864b08e8ae25e841b18b0d25858d95268fce2435d51c340d69a41782f089",
                             "fb14e51c7f7d751b13307ecf65573c1863c7f579252aa402231586aeda11412f",
                             "8576765bdd5b9dbb93db76ec11b485634fa2f34691113a45d59dbf49238c0c87"),
    "arabic_coverage_v2": ("1818fc27f076535734d9d9e90a857683f27d464f0a205637e7231cd6e870c40c",
                          "46070144ca2e2fe7bcfb73292498fceebf669c6a8756c9ec771c6f4dee528851",
                          "8446ae35115ba9eb1b332ea7395a7be9b1d1be9285073918d711a7466237b163"),
    "arabic_coverage_v1": ("a7194b9b52ab8a6db0c92d65c7dae76dc23c1f1c8777b4e10b2fb71efa01c89f",
                          "602fe4a4d81044adbbd01849284f14c699f2104a36595db2bd6f8e80facf7804",
                          "54452a9f9375caf4837b00156a98a1be3076b6bd9e4afa2980e8f3d73755e289"),
    "rational_inquiry_v2": ("49a9c891446e945b74b28489f4abda522473093ada40e503e1fcd5ce99905f4b",
                            "97bae287bf823be44033a9e3c174647ed3abb6a15a214e6f4542ba2bb4cc6d64",
                            "fd1ed9ab3cc8b6b5f98c7b1e04f7bd9255cbc2abee0447cbf9a33f234e28a194"),
    "rational_inquiry_v1": ("cefe19d399b19e30175579e427272b790d24eab0e07b54b152e0cd3a45dc5dc4",
                            "f4f56c8d8e5b8cf7260cb51fa5b87cd8952a2a746294e0050a072c5e3b17f79f",
                            "19bc1ab5e1c78d3163cc0ff1af4c0acb85f71886ec8cc3973aeab23529ff5714"),
    "constructions_v4": ("42476d67e30e7e86506c3e878552966ce9dc784ae1e5d98bec3af50e6f0a1aa5",
                         "3a6e9594cf6b094ca6bfce61a4969e854604f5fc4520db90c793aa7fda0b4e58",
                         "62d395428f49785c005ceaf55d86ed1e66cce12453d8ed2a03146436b5ba0567"),
    "constructions_v3": ("23d04d307c3e560c8198ee0700923673af001a8835d8e00d6c11d79534e6d611",
                         "2c1b6b30e22b5322046109b461f850974e356736f2aedb06c4911be82375188f",
                         "b5363658881c8e265295ad727d346ea8925348e9342b89f50eb014be824a19f1"),
    "constructions_v2": ("5d4bf3ec6331dab12ebc735f57203cf6bdbc86a563eae0311a66316eb8b820b1",
                         "1e9d906428ec3824c4ecbff8ef8fb3adc88d6cb6c9dbfa1819c53655b3206c7c",
                         "9d5ec76ec904c3696d0e5a76e46fe435e9189322fe0578133c6816707b2fd2c5"),
    "constructions_v1": ("96ffa98008bf1b6a6d1f5ab6b79a330fe4b8a9329887d9ac3f8ff9d31eb12e1e",
                         "87c7d5dc6c4aa5f46d42f7cd27a1595e2a2844af50da42a45a0f3b3bc09812b9",
                         "edaff6bb63863e10734993bbaf5101160dab3308b22e763ba188d89fa28e3575"),
    "discourse_v4": ("f1e035f7d20395abb82c2e87ac42f374630bef6bab71a22490873c7a08e8e519",
                     "2d79ea2227dda5169413eb314b9b65b5bc04fcacb447d00066ef56d3c7b69108",
                     "af7b88818f8d46a4d810927df39f1eb839c28dd7862f3919c3ac52f66abdbf8e"),
    "discourse_v3": ("c74b029c986fa3e1bb6a6ab3c5cbd423f77c902733626105ec95f5e366b71018",
                     "6b78f1c8e36058d350d1e572bf20737c3517d38a8498fc4a50ece6bf6725fd30",
                     "4fbcadee8997087223cbf8ffc365dd7a1b6cac4eb0990350e8925098ec557b51"),
    "discourse_v2": ("22350accf750741680f351b34cf97f95bf146b7389765cd74d937a8aa4291ae4",
                     "e82b9d72b45d8cbcd667708140b9f5b91a967822002a54a76bc87b097912a2f9",
                     "0085bb7482ef89d20f0f8667ca015f0cf198ab283d9e439ecc814b9167b13775"),
    "inflection_v3": ("46b0bdaa68be83f1b62a1536ee3ad548863e90489e4be7e0cdf91b939b131641",
                      "cd6984487ea0c87ea97b64aa8f89124ac3d947e77e3cc9fda704d2e3668cfd7d",
                      "7084f8c407ced8a2189872cd3291e4168e088e439549fb139540c7e527f69215"),
    "inflection_v2": ("70e56488ae8a99aa0d52d7ebed53c039d10ed7de9a8c457952515e45277db96e",
                      "818a1a90e0710daf951bc8108b32f37978938361c0f8f92032840872640c52f3",
                      "59a575c2f10bb07633d54515dad21b08b35ecde37ba3d909e4748eec82f9eb14"),
    "inflection_v1": ("fe93f8ebebb21078113462244052da93c102f4d5a673c2636c0cab27e0ffa103",
                      "aaac387085d745b89f0260eb1905d66dade8a710e483034442e7957972243ede",
                      "31cc7b08586e5c0fa235357d75b36ce23475f486addec6d6d465be4889346c7f"),
    "nominal_v2": ("d904702b8633f8102c6795f3beeff0d5584e908ee7b0d1c605c168103ab87f94",
                   "814ec3f4ea340b09b594ff162e65e49be8e4110088da5feae02fe41eb8a71d6c",
                   "c7ab0b42159ba60d5a39b65b2adb980ed92df6e6e71eb1dc355bbfb43d838071"),
    "nominal_v1": ("9d9f71eb1b26caac6ea170fe839e7b7f2903eccf827c5bbf7b2c78d3a46a13cd",
                   "c00458629fcd08a6cefb616d0fb1caaec5958996b0532043d0fd1a92d922740a",
                   "6d86c0709c97a89375fc9ff498d1576585c3e432831c7ac17cfc1eb75c2f2724"),
    "derivation_v1": ("5cdea1a66bd92f3f014cc2f14ab2d502f43f630d03977cb111020e3370907eed",
                      "e8e31cdaa1cb56e3700befd4d8fb883e11f83cd684e6cd72b45e133410bf3cac",
                      "fd24793a4fb805425e4bba60219c70a0f1fbb4dda7a89b07d1c6a0ffc6c3b060"),
    "v1": (FREEZE_MANIFEST_SHA256, FROZEN_RUNTIME_SHA256, FROZEN_ARCHIVE_SHA256),
    "text_morphology_v1": ("b15dfab7ed6166aa5aae236c7c0b22ce48f805a6bc0d8f6c3b6f12bae2b951ee",
                           "82a5d9b283d403bf257a95e5c8a1eb9b2ea300a90ca1a2e881de478bf29f7496",
                           "d1661a0abef5f25d048b675270517e400f83c08a1a0b6b3f3c7c399514f94304"),
}
CODE_FREEZE_PATHS = {
    'arabic_completion_v6': ROOT / 'evidence/arabic_completion_v6/code_freeze_v1.json',
    'arabic_completion_v5': ROOT / 'evidence/arabic_completion_v5/code_freeze_v1.json',
    "arabic_completion_v4_review2": ROOT / "evidence/arabic_completion_v4/code_freeze_v2.json",
    "arabic_completion_v4": ROOT / "evidence/arabic_completion_v4/code_freeze_v1.json",
    "arabic_completion_v3_review2": ROOT / "evidence/arabic_completion_v3/code_freeze_v2.json",
    "arabic_completion_v3": ROOT / "evidence/arabic_completion_v3/code_freeze_v1.json",
    "arabic_coverage_v2": ROOT / "evidence/arabic_coverage/code_freeze_v2.json",
    "arabic_coverage_v1": ROOT / "evidence/arabic_coverage/code_freeze_v1.json",
    "rational_inquiry_v2": ROOT / "evidence/rational_inquiry/code_freeze_v2.json",
    "rational_inquiry_v1": ROOT / "evidence/rational_inquiry/code_freeze_v1.json",
    "constructions_v4": ROOT / "evidence/constructions/code_freeze_v4.json",
    "constructions_v3": ROOT / "evidence/constructions/code_freeze_v3.json",
    "constructions_v2": ROOT / "evidence/constructions/code_freeze_v2.json",
    "constructions_v1": ROOT / "evidence/constructions/code_freeze_v1.json",
    "discourse_v4": ROOT / "evidence/discourse/code_freeze_v4.json",
    "discourse_v3": ROOT / "evidence/discourse/code_freeze_v3.json",
    "discourse_v2": ROOT / "evidence/discourse/code_freeze_v2.json",
    "inflection_v3": ROOT / "evidence/inflection/code_freeze_v3.json",
    "inflection_v2": ROOT / "evidence/inflection/code_freeze_v2.json",
    "inflection_v1": ROOT / "evidence/inflection/code_freeze_v1.json",
    "nominal_v2": ROOT / "evidence/nominal/code_freeze_v2.json",
    "nominal_v1": ROOT / "evidence/nominal/code_freeze_v1.json",
    "derivation_v1": ROOT / "evidence/derivation/code_freeze_v1.json",
    "v1": ROOT / "evidence/morphology/code_freeze_v1.json",
    "text_morphology_v1": ROOT / "evidence/text_morphology/code_freeze_v1.json",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def load_material(version="v2"):
    raw = (ROOT / "evidence/morphology" / f"independent_cases_{version}.json").read_bytes()
    require(sha256(raw).hexdigest() == MATERIAL_SHA256[version], "Frozen case bytes changed")
    material = json.loads(raw)
    cases = material["cases"]
    require(len(cases) == len({c["id"] for c in cases}) == MATERIAL_COUNTS[version],
            "Independent case inventory changed")
    passages = set()
    for source in material["sources"]:
        content = None
        if "path" in source:
            content = (ROOT / source["path"]).read_bytes()
            require(sha256(content).hexdigest() == source["sha256"], "Primary source changed")
        for passage in source["passages"]:
            require(passage["id"] not in passages, "Repeated primary passage identity")
            passages.add(passage["id"])
            embedded = passage["text"].encode("utf-8")
            require(sha256(embedded).hexdigest() == passage["sha256"], "Embedded passage changed")
            if content is not None:
                require(content[passage["byte_start"]:passage["byte_end"]] == embedded,
                        "Primary passage does not match its byte range")
    for case in cases:
        require(set(case["source_passages"]) <= passages, "Case refers to an absent primary passage")
    return material


def snapshot():
    """Record the actual package and formal inputs; never scan other checkouts."""
    paths = {ROOT / "pyproject.toml"}
    paths.update(p for p in (ROOT / "src").rglob("*") if p.is_file()
                 and p.suffix in {".py", ".json", ".txt"}
                 and "__pycache__" not in p.parts
                 and not any(v.endswith((".egg-info", ".dist-info")) for v in p.parts))
    paths.update(ROOT / p for p in ("formal/Nabt/Morphology.lean", "formal/ExportMorphology.lean"))
    rows = []
    for path in sorted(paths):
        require(path.resolve().is_relative_to(ROOT), "Package file resolves outside NABT")
        data = path.read_bytes()
        rows.append({"path": str(path.relative_to(ROOT)), "bytes": len(data),
                     "sha256": sha256(data).hexdigest()})
    return {"files": rows, "sha256": sha256(wire(rows)).hexdigest()}


def loaded_origins():
    rows = []
    for name, module in sorted(sys.modules.items()):
        if name != "nabt" and not name.startswith("nabt."):
            continue
        filename = getattr(module, "__file__", None)
        if filename is None:
            continue
        path = Path(filename).resolve()
        expected = (ROOT / "src").joinpath(*name.split("."))
        require(path in {expected.with_suffix(".py"), expected / "__init__.py"},
                "Loaded a NABT module outside the measured package: " + name)
        rows.append({"module": name, "path": str(path.relative_to(ROOT)),
                     "sha256": sha256(path.read_bytes()).hexdigest()})
    require(any(row["module"] == "nabt.morphology_reader" for row in rows),
            "Morphology reader was not loaded")
    return rows


def verify_runtime_freeze(actual_snapshot, version="arabic_completion_v6"):
    manifest_sha, snapshot_sha, archive_sha = CODE_FREEZES[version]
    manifest_path = CODE_FREEZE_PATHS[version]
    raw = manifest_path.read_bytes()
    require(sha256(raw).hexdigest() == manifest_sha, "Runtime freeze manifest differs")
    freeze = json.loads(raw)
    rows = freeze["files"]
    require(len(rows) == len({r["path"] for r in rows}), "Runtime freeze repeats a path")
    require(sha256(wire(rows)).hexdigest() == freeze["snapshot_sha256"] == snapshot_sha,
            "Runtime freeze inventory differs")
    package_rows = [r for r in actual_snapshot["files"] if not r["path"].startswith("formal/")]
    require(package_rows == rows, "Measured package is not the frozen runtime")
    archive = manifest_path.parent / freeze["archive_filename"]
    require(sha256(archive.read_bytes()).hexdigest() == freeze["archive_sha256"] == archive_sha,
            "Runtime archive differs")
    by_name = {r["path"]: r for r in rows}
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        require(all(m.isfile() for m in members)
                and len(members) == len(rows) and {m.name for m in members} == set(by_name),
                "Runtime archive member inventory differs")
        for member in members:
            content = bundle.extractfile(member).read()
            wanted = by_name[member.name]
            require(len(content) == wanted["bytes"] and sha256(content).hexdigest() == wanted["sha256"],
                    "Runtime archive bytes differ: " + member.name)
    return {"version": version, "manifest_sha256": manifest_sha, "snapshot_sha256": snapshot_sha,
            "archive_sha256": archive_sha, "files": len(rows)}


def structure_checks(report, text, source_id, scope=SCOPE):
    """Check byte identity and links independently of Arabic property parsing."""
    raw = text.encode("utf-8")
    digest = sha256(raw).hexdigest()
    require(report["source_id"] == source_id and report["source_sha256"] == digest
            and report["raw_text"] == text and report["scope"] == scope,
            "Report changed its source or scope")

    def span(value, exact_text=None):
        a, b = value["start"], value["end"]
        require(type(a) is int and type(b) is int and 0 <= a < b <= len(raw), "Invalid byte interval")
        part = raw[a:b]
        require(value["source_id"] == source_id and value["source_sha256"] == digest,
                "Span belongs to another source")
        require(value["span_sha256"] == sha256(part).hexdigest(), "Wrong span digest")
        require(exact_text is None or part.decode("utf-8", "strict") == exact_text,
                "Span does not contain its claimed text")
        part.decode("utf-8", "strict")

    # This inventory checks explicitly delimited identities; it is not a
    # second implementation of the property-clause language or inference.
    headers = re.findall(r"^قراءة «([^»]+)» للفظ «([^»]+)»:$", text, re.MULTILINE)
    readings = report["readings"]
    require(len(headers) == len(readings), "Reading inventory omitted or invented a header")
    require(len({r["occurrence_id"] for r in readings}) == len(readings), "Occurrence identities collapsed")
    for reading, (label, lexeme) in zip(readings, headers):
        require(reading["reading_id"] == label and reading["lexeme"] == lexeme,
                "Reading identity or lexical bytes changed")
        require(reading["source_id"] == source_id and reading["source_sha256"] == digest
                and reading["scope"] == scope, "Reading escaped source/scope")
        span(reading["header_span"])
        span(reading["lexeme_span"], lexeme)
        for clause in reading["clauses"]:
            span(clause["span"], clause["text"])
        evidence = reading["evidence"]
        support_ids = {e["support_id"] for e in evidence}
        require(len(support_ids) == len(evidence), "Evidence identity collapsed")
        for item in evidence:
            require(item["reading_id"] == label and item["source_id"] == source_id
                    and item["source_sha256"] == digest and item["scope"] == scope
                    and item["occurrence_id"] == reading["occurrence_id"],
                    "Evidence spliced across readings, occurrences, source, or scope")
            span(item["span"], item["text"])
            unsigned = {k: v for k, v in item.items() if k != "support_id"}
            require(sha256(wire(unsigned)).hexdigest() == item["support_id"], "Evidence hash is not canonical")
        for axis in [*reading["axes"].values(), reading["axes"]["diptote"]["genitive"]]:
            require(set(axis["support_ids"]) <= support_ids, "Axis borrows foreign evidence")
        for item in reading["unparsed"]:
            span(item["span"], item["text"])
        genitive = reading["axes"]["diptote"]["genitive"]
        require(genitive["applied_to_occurrence"] is False
                and genitive["application"] == "IF_THIS_IS_AN_INFLECTED_DIPTOTE_IN_GENITIVE_CASE"
                and "INDEPENDENT_GENITIVE_CASE_WITNESS" in genitive["prerequisites"],
                "Conditional sign acquired an actual syntactic role")
    for clause in report["unscoped_clauses"]:
        span(clause["span"], clause["text"])
    require(report["facts"] == [] and report["semantic_projection"] == "NONE"
            and report["world_truth"] == "NOT_ESTABLISHED", "Morphology acquired world-truth authority")


def public_axis(reading, name):
    if name == "diptote_intrinsic":
        parent = reading["axes"]["diptote"]
        prediction = parent["cause_prediction"]
        require(prediction["domain"] == "QUALIFIED_INTRINSIC_CAUSE_FORMULA_ONLY",
                "Intrinsic cause prediction lost its conditional domain")
        return {**parent, **prediction}
    if name == "genitive":
        return reading["axes"]["diptote"]["genitive"]
    return reading["axes"][name]


def expected_axis(axis, expected):
    # Fixed interface names only. No lexeme or case identifier occurs here.
    if expected == "pending":
        return axis["status"] == "DEFER" and bool(axis["missing"] or axis.get("prerequisites"))
    if expected == "conflict":
        return axis["status"] == "CONFLICT" and bool(axis["conflicts"])
    if expected == "out_of_domain":
        return axis["status"] == "OUT_OF_DOMAIN"
    if expected == "affirmed":
        expected = "diptote"
    return axis["status"] == "LICENSED" and axis["candidates"] == [expected]


def properties(expected, report):
    result = []

    def add(name, passed, observed=None):
        result.append({"property": name, "passed": bool(passed), "observed": observed})

    by_id = {reading["reading_id"]: reading for reading in report["readings"]}
    for label, axes in expected.get("readings", {}).items():
        add(label + ":reading_present", label in by_id)
        if label not in by_id:
            continue
        for name, wanted in axes.items():
            actual = public_axis(by_id[label], name)
            add(label + ":" + name, expected_axis(actual, wanted),
                {"expected": wanted, "status": actual["status"],
                 "candidates": actual["candidates"], "missing": actual["missing"],
                 "conflicts": actual["conflicts"],
                 "blocked_by_unparsed_source": actual.get("blocked_by_unparsed_source", False)})
    if expected.get("distinct_reading_ids"):
        add("distinct_reading_identities", len(by_id) == len(expected["readings"])
            and len({r["occurrence_id"] for r in by_id.values()}) == len(by_id))
    for unknown in expected.get("unknown_clauses", []):
        found = any(u["text"] == unknown and u["code"] == "UNPARSED_PROPERTY_CLAUSE"
                    for r in report["readings"] for u in r["unparsed"])
        add("unknown_clause_retained:" + unknown, found)
        add("unknown_clause_blocks_complete_report", report["status"] == "DEFER")
    return result


def summarize_report(report):
    return {"sha256": sha256(wire(report)).hexdigest(), "source_sha256": report["source_sha256"],
            "status": report["status"], "readings": [
                {"reading_id": r["reading_id"], "lexeme": r["lexeme"],
                 "occurrence_id": r["occurrence_id"],
                 "axes": {name: {k: value[k] for k in ("status", "candidates", "missing", "conflicts")}
                          for name, value in r["axes"].items()},
                 "genitive": {k: r["axes"]["diptote"]["genitive"][k]
                              for k in ("status", "candidates", "missing", "conflicts")},
                 "intrinsic_cause_prediction": r["axes"]["diptote"]["cause_prediction"],
                 "unparsed": r["unparsed"]} for r in report["readings"]]}


def structured_failure(result):
    return type(result) is dict and result.get("valid") is False and result.get("status") in {"REJECT", "DEFER"}


def attack_reports(kind, report):
    altered = deepcopy(report)
    if kind == "reading_identity_mutation":
        altered["readings"][0]["reading_id"] = "foreign_reading"
    elif kind == "conclusion_mutation":
        altered["readings"][0]["axes"]["nominal_semantics"]["candidates"] = ["jins_jamid"]
    elif kind == "support_span_mutation":
        reading = altered["readings"][0]
        item = next(e for e in reading["evidence"] if e["property"] == "property_bearing")
        previous_id = item["support_id"]
        unrelated = reading["clauses"][0]
        item["span"], item["text"] = deepcopy(unrelated["span"]), unrelated["text"]
        item["support_id"] = sha256(wire({k: v for k, v in item.items() if k != "support_id"})).hexdigest()
        for axis in reading["axes"].values():
            axis["support_ids"] = [item["support_id"] if s == previous_id else s for s in axis["support_ids"]]
    elif kind == "malformed_certificate":
        bad_nested = deepcopy(report)
        bad_nested["readings"] = None
        return [None, [], {}, {"raw_text": True}, bad_nested]
    else:
        raise ValueError("Unknown review attack")
    return [altered]


def _run_case(case):
    from nabt.errors import NabtError
    from nabt.morphology_reader import (decode_morphology, morphology_number,
                                        read_morphology, verify_morphology)

    text, source_id = case["input"]["text"], case["input"]["source_id"]
    expected, checks, summaries = case["expected"], [], {}

    def add(name, passed, detail=None):
        checks.append({"property": name, "passed": bool(passed), "observed": detail})

    try:
        report = read_morphology(text, source_id=source_id, scope=SCOPE)
    except NabtError as error:
        add("declared_input_rejection", expected.get("must_reject_duplicate_reading_identity") is True
            and error.code == "DUPLICATE_READING_ID" and error.status == "REJECT", error.as_dict())
        return {"id": case["id"], "group": case["group"], "passed": all(c["passed"] for c in checks),
                "checks": checks, "error": error.as_dict()}
    except Exception as error:
        return {"id": case["id"], "group": case["group"], "passed": False,
                "checks": [{"property": "structured_execution", "passed": False,
                            "observed": {"type": type(error).__name__, "message": str(error)}}]}

    try:
        structure_checks(report, text, source_id)
        add("source_identity_and_support_links", True)
    except (ValueError, TypeError, KeyError, UnicodeError) as error:
        add("source_identity_and_support_links", False, str(error))
    seed = verify_morphology(report, text=text, source_id=source_id, scope=SCOPE)
    add("original_certificate_replays", type(seed) is dict and seed.get("valid") is True, seed)
    summaries["before"] = summarize_report(report)
    operation = case.get("operation", {})
    kind = operation.get("kind")
    if expected.get("must_reject_duplicate_reading_identity"):
        add("duplicate_reading_identity_rejected", False)
    elif kind == "retract_source_clause":
        checks.extend(properties(expected["before"], report))
        after_text = operation["after_text"]
        after = read_morphology(after_text, source_id=source_id, scope=SCOPE)
        structure_checks(after, after_text, source_id)
        after_checks = properties(expected["after"], after)
        for check in after_checks:
            check["property"] = "after_retraction:" + check["property"]
        checks.extend(after_checks)
        replay = verify_morphology(report, text=after_text, source_id=source_id, scope=SCOPE)
        add("old_certificate_invalid_after_source_change", structured_failure(replay), replay)
        add("changed_source_changes_occurrence_identity",
            report["readings"][0]["occurrence_id"] != after["readings"][0]["occurrence_id"])
        summaries["after"] = summarize_report(after)
    elif expected.get("must_fail_replay"):
        if kind == "source_identity_transplant":
            results = [verify_morphology(report, text=text, source_id=source_id + "_other", scope=SCOPE)]
        else:
            results = [verify_morphology(changed, text=text, source_id=source_id, scope=SCOPE)
                       for changed in attack_reports(kind, report)]
        add("tampered_certificate_is_structured_failure", all(structured_failure(r) for r in results), results)
    else:
        checks.extend(properties(expected, report))

    # This checks encoding's boundary, not an independent semantic theorem.
    encoded = morphology_number(report)
    add("canonical_report_numeric_roundtrip", decode_morphology(encoded) == report,
        {"bit_length": encoded.bit_length(),
         "encoded_bytes_sha256": sha256(encoded.to_bytes((encoded.bit_length() + 7) // 8, "big")).hexdigest()})
    return {"id": case["id"], "group": case["group"], "passed": all(c["passed"] for c in checks),
            "checks": checks, "observed": summaries}


def run_case(case):
    try:
        return _run_case(case)
    except Exception as error:
        # A reviewer/adapter error is not silently converted into a linguistic
        # result. Preserve it as a failed evaluation contract with its type.
        return {"id": case["id"], "group": case["group"], "passed": False,
                "checks": [{"property": "evaluation_contract_completed", "passed": False,
                            "observed": {"type": type(error).__name__, "message": str(error)}}]}


def documented_boundary(case_result):
    """One narrow, visible coverage debt; no other failed property is allowed."""
    if case_result["id"] not in DOCUMENTED_BOUNDARY_MISSES:
        return False
    failed = [c for c in case_result["checks"] if not c["passed"]]
    if len(failed) != 1 or failed[0]["property"] != "r1:kind":
        return False
    actual = failed[0]["observed"]
    readings = case_result.get("observed", {}).get("before", {}).get("readings", [])
    return (actual["status"] == "DEFER"
            and actual["candidates"] == [actual["expected"]]
            and actual["blocked_by_unparsed_source"] is True
            and bool(readings) and bool(readings[0].get("unparsed")))


def regression_gate(results):
    return all(case["passed"] or documented_boundary(case) for case in results)


def evaluate(version="v2", *, freeze_version="arabic_completion_v6"):
    material = load_material(version)
    before = snapshot()
    freeze = verify_runtime_freeze(before, freeze_version)
    started = time.perf_counter()
    results = [run_case(case) for case in material["cases"]]
    elapsed = time.perf_counter() - started
    after = snapshot()
    require(before == after, "Measured package changed during evaluation; rerun on a stable snapshot")
    groups = {}
    for case in results:
        group = groups.setdefault(case["group"], {"passed": 0, "total": 0})
        group["total"] += 1
        group["passed"] += int(case["passed"])
    return {"evaluator_version": VERSION, "evaluator_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "recorded_utc": datetime.now(timezone.utc).isoformat(),
            "material_version": version, "material_sha256": MATERIAL_SHA256[version],
            "measurement_scope": material["freeze_boundary"],
            "claim_boundary": material["claim_boundary"],
            "runtime_snapshot": before, "frozen_runtime": freeze, "loaded_module_origins": loaded_origins(),
            "execution_seconds_one_run": elapsed,
            "summary": {"passed": sum(r["passed"] for r in results), "total": len(results),
                        "groups": groups, "failed_ids": [r["id"] for r in results if not r["passed"]],
                        "documented_boundary_ids": [r["id"] for r in results if not r["passed"] and documented_boundary(r)],
                        "regression_gate_with_declared_boundaries": regression_gate(results)},
            "cases": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--material", choices=tuple(MATERIAL_SHA256), default="v2")
    parser.add_argument("--freeze-version", choices=tuple(CODE_FREEZES), default="arabic_completion_v6")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--diagnostic", action="store_true",
                        help="Preserve failures in a diagnostic report without using them as a release gate")
    parser.add_argument("--allow-documented-boundaries", action="store_true",
                        help="Permit only the four named conservative kind-approval coverage misses; raw score is unchanged")
    args = parser.parse_args()
    result = evaluate(args.material, freeze_version=args.freeze_version)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"material_version": args.material, **result["summary"]}, ensure_ascii=False, indent=2))
    passed = result["summary"]["passed"] == result["summary"]["total"]
    return 0 if args.diagnostic or passed or (args.allow_documented_boundaries and regression_gate(result["cases"])) else 1


if __name__ == "__main__":
    raise SystemExit(main())
