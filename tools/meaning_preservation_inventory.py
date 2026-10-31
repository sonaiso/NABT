"""Replay the pinned research inventory without granting a language license.

The imported research package, the related existing records, and the actual
native transport law have different authority. This reader checks identities
and exact pointers. It does not authenticate a cited edition, prove translation
fidelity, or turn a family row into a grammar theorem.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = "evidence/meaning_preservation_v1/source_scope.json"
SCOPE_SHA256 = "5364e2bb2603a18950ded79d8b7d8787c3aba2d90c5617d6746c7a3b56ff18fe"
INVENTORY_PATH = "evidence/meaning_preservation_v1/research_inventory.json"
INVENTORY_SHA256 = "d1cbf80bb015f47325561584712e21bacff14d18ae6c9f2b26256632289865c0"
AUTHORITY = "RESEARCH_DESIGN_METADATA_NOT_RUNTIME_LICENSING_AUTHORITY"
BASELINE = "3dbe335a21ac838db3717f03ca2a5b5889e16e54"
MAX_FILE_BYTES = 8 * 1024 * 1024
DENOMINATORS = {"morphology_families": 51, "composition_groups": 34,
                "interpretation_contracts": 15, "nominal_templates": 20}
KINDS = {"morphology_family": 51, "composition_group": 34,
         "interpretation_contract": 15, "nominal_template": 20}
IMPORTS = {name: "evidence/meaning_preservation_v1/research/" + name + ".json"
           for name in ("morphology_inventory", "composition_inventory",
                        "interpretation_contracts")}


def _wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _digest(value):
    return sha256(_wire(value).encode("utf-8")).hexdigest()


def _same(left, right):
    # Do not identify Boolean true with integer one in evidence metadata.
    return _wire(left) == _wire(right)


def _path(name):
    if type(name) is not str or not name or Path(name).is_absolute():
        raise ValueError("Expected a repository-relative inventory path")
    root = ROOT.resolve()
    path = root / name
    if path.resolve() != path or path.relative_to(root).as_posix() != name:
        raise ValueError("Noncanonical or symlinked inventory path")
    if ".." in Path(name).parts:
        raise ValueError("Escaping inventory path")
    return path


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate inventory JSON key")
        result[key] = value
    return result


def _read(name, expected_hash, expected_bytes=None):
    if type(expected_hash) is not str or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise ValueError("Malformed installed inventory fingerprint")
    with _path(name).open("rb") as stream:
        raw = stream.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError("Inventory file exceeds its read budget")
    if expected_bytes is not None and (type(expected_bytes) is not int or
                                       len(raw) != expected_bytes):
        raise ValueError("Installed inventory byte count differs")
    if sha256(raw).hexdigest() != expected_hash:
        raise ValueError("Installed inventory bytes differ: " + name)
    return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs)


def _pointer(value, pointer):
    """Resolve an exact RFC 6901 pointer; array indices must be canonical."""
    if type(pointer) is not str or (pointer and not pointer.startswith("/")):
        raise ValueError("Malformed inventory JSON pointer")
    if pointer == "":
        return value
    for raw in pointer[1:].split("/"):
        if re.search(r"~(?![01])", raw):
            raise ValueError("Malformed JSON pointer escape")
        key = raw.replace("~1", "/").replace("~0", "~")
        if type(value) is dict:
            if key not in value:
                raise ValueError("Inventory object pointer is absent")
            value = value[key]
        elif type(value) is list:
            if not re.fullmatch(r"0|[1-9][0-9]*", key):
                raise ValueError("Noncanonical array pointer")
            index = int(key)
            if index >= len(value):
                raise ValueError("Inventory array pointer is absent")
            value = value[index]
        else:
            raise ValueError("Inventory pointer descends through a scalar")
    return value


def research_inventory():
    """Reopen all pinned inputs and return their scoped research crosswalk."""
    scope = _read(SCOPE_PATH, SCOPE_SHA256)
    inventory = _read(INVENTORY_PATH, INVENTORY_SHA256)
    if (scope.get("schema") != "nabt.meaning-preservation-source-scope.v1" or
            inventory.get("schema") != "nabt.meaning-foundation-research-inventory.v1" or
            inventory.get("source_scope_path") != SCOPE_PATH):
        raise ValueError("Unsupported installed research schema")
    for document in (scope, inventory):
        if (document.get("authority") != AUTHORITY or
                document.get("baseline_commit") != BASELINE or
                not _same(document.get("denominators"), DENOMINATORS)):
            raise ValueError("Research scope or separate denominators differ")
        if type(document.get("claims")) is not dict or not document["claims"] or any(
                flag is not False for flag in document["claims"].values()):
            raise ValueError("Research metadata attempted an unsupported authority claim")

    imported = {}
    for row in scope["imports"]:
        key = row["id"]
        if key in imported or IMPORTS.get(key) != row["path"]:
            raise ValueError("Installed research import set differs")
        imported[key] = _read(row["path"], row["sha256"], row["bytes"])
    if set(imported) != set(IMPORTS):
        raise ValueError("Missing installed research import")

    anchors, files = {}, {}
    for anchor in inventory["existing_record_anchors"]:
        key, name = anchor["id"], anchor["path"]
        if key in anchors or anchor["base_commit"] != BASELINE:
            raise ValueError("Duplicate or unbound existing research anchor")
        if (anchor["relation"] != "RELATED_SCOPED_SOURCE_RECORD_ONLY" or
                anchor["runtime_coverage_proved"] is not False or
                anchor["translation_fidelity_proved"] is not False):
            raise ValueError("Related source anchor overstates its authority")
        fingerprint = anchor["file_sha256"]
        if name not in files:
            files[name] = (fingerprint, _read(name, fingerprint))
        if files[name][0] != fingerprint:
            raise ValueError("One anchor path has conflicting file identities")
        record = _pointer(files[name][1], anchor["json_pointer"])
        if (type(record) is not dict or
                record.get(anchor["identity_field"]) != anchor["identity"] or
                _digest(record) != anchor["record_sha256"]):
            raise ValueError("Existing anchor record differs")
        anchors[key] = anchor
    if len(anchors) != 55:
        raise ValueError("Existing anchor denominator differs")

    seen, kinds, unmatched = set(), Counter(), []
    for row in inventory["records"]:
        key = row["id"]
        if (key in seen or row["kind"] not in KINDS or
                key != row["kind"] + ":" + row["local_id"]):
            raise ValueError("Duplicate or malformed research record identity")
        seen.add(key)
        kinds[row["kind"]] += 1
        if row["import_id"] not in imported:
            raise ValueError("Unbound research record import")
        record = _pointer(imported[row["import_id"]], row["json_pointer"])
        if _digest(record) != row["record_sha256"]:
            raise ValueError("Imported research record pointer differs")
        related = row["related_existing_records"]
        expected_mapping = ("RELATED_SCOPE_ONLY" if related else
                            "OPEN_NO_EXACT_SCOPE_REFERENCE_INSTALLED")
        if (row["mapping_status"] != expected_mapping or
                row["formal_status"] != "NO_PER_ROW_THEOREM_OR_FIDELITY_CERTIFICATE"):
            raise ValueError("Research row overstates its formal status")
        if len(set(related)) != len(related) or not set(related) <= set(anchors):
            raise ValueError("Missing or duplicate related source anchor")
        if not related:
            unmatched.append(key)
        if row["kind"] == "nominal_template" and row["display_example_newly_verified"] is not False:
            raise ValueError("Template collation does not authenticate all examples")
    if dict(kinds) != KINDS:
        raise ValueError("Exact separate research record denominators differ")

    return {"schema": "nabt.meaning-preservation.research-report.v1",
            "status": "RESEARCH_METADATA_VERIFIED", "metadata_verified": True,
            "authority": AUTHORITY, "baseline_commit": BASELINE,
            "denominators": dict(DENOMINATORS), "related_source_anchors": len(anchors),
            "records_without_exact_related_anchor": unmatched,
            "inputs": {SCOPE_PATH: SCOPE_SHA256, INVENTORY_PATH: INVENTORY_SHA256,
                       **{row["path"]: row["sha256"] for row in scope["imports"]},
                       **{name: entry[0] for name, entry in files.items()}},
            "claims": dict(scope["claims"]), "counting_rule": scope["counting_rule"],
            "source_identity_boundary": scope["source_identity_boundary"],
            "closure_status": scope["closure_status"],
            "closure_obligations": scope["closure_obligations"],
            "records": inventory["records"],
            "existing_record_anchors": inventory["existing_record_anchors"]}
