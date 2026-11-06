"""Validate the curriculum's references, never learning or semantic mastery.

The document organizes existing owners and explicit acquisition obligations.
It cannot supply a passing assessment, run an adapter or authorize a reading.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from hashlib import sha256
from pathlib import Path, PurePosixPath
import re

from tools import evidence_lifecycle_v1 as wire_owner

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "evidence/cognitive_curriculum_v1/learning_framework.json"
SCHEMA = "nabt.learning-framework.v1"
MAX_BYTES = 1024 * 1024
FIELDS = ("schema", "basis_commit", "sources", "stages", "methods", "agents",
          "objectives", "assessment", "neural_design", "legacy_alignment")
OBJECTIVE_FIELDS = (
    "id", "label_ar", "stage", "prerequisites", "agent_id", "domain_ids", "axis_ids",
    "matrix_ids", "method_ids", "owner_modules", "source_ids", "knowledge_ar", "skill_ar",
    "disposition_ar", "inputs", "outputs", "formative", "summative", "runtime_refs",
    "acquisition_obligation_ar", "neural_status", "legacy_card_ids",
)


def _ids(value, label):
    if type(value) is not list:
        raise ValueError(label + " must be a list")
    for item in value:
        wire_owner._text(item, label, 1024)
    if len(set(value)) != len(value):
        raise ValueError("Duplicate reference in " + label)
    return set(value)


def _indexed(rows, label):
    if type(rows) is not list or not rows:
        raise ValueError(label + " must contain records")
    ids = []
    for row in rows:
        if type(row) is not dict or "id" not in row:
            raise ValueError(label + " record requires an id")
        ids.append(row["id"])
    _ids(ids, label)
    return {row["id"]: row for row in rows}


def _content(value, label):
    if type(value) is not dict or not value:
        raise ValueError(label + " requires a nonempty object")


def _text_list(value, label):
    if type(value) is not list or not value:
        raise ValueError(label + " requires a nonempty list of text")
    for item in value:
        wire_owner._text(item, label, MAX_BYTES, content=True)


def _assessment(value, label):
    _content(value, label)
    fields = (("task_ar", "feedback_ar", "contrast_ar") if label == "formative"
              else ("task_ar", "split_keys", "critical_failures", "metrics"))
    wire_owner._fields(value, fields, label)
    for key in fields:
        if key.endswith("_ar"):
            wire_owner._text(value[key], label + "." + key, MAX_BYTES, content=True)
        else:
            _text_list(value[key], label + "." + key)


def _path(value, root):
    wire_owner._text(value, "repository path", 1024)
    path = PurePosixPath(value)
    if (path.is_absolute() or value != path.as_posix() or "\\" in value
            or any(part in {".", "..", ".git"} for part in path.parts)):
        raise ValueError("Noncanonical repository path: " + value)
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        raise ValueError("Unresolved repository file: " + value)


def _order(records, label):
    incoming, children = {}, {key: [] for key in records}
    for identity, row in records.items():
        prerequisites = _ids(row.get("prerequisites", []), label + " prerequisites")
        if not prerequisites <= records.keys():
            raise ValueError("Unresolved " + label + " prerequisite: " + identity)
        if identity in prerequisites:
            raise ValueError("Self " + label + " prerequisite: " + identity)
        incoming[identity] = len(prerequisites)
        for prior in row.get("prerequisites", []):
            children[prior].append(identity)
    ready = deque(key for key, count in incoming.items() if count == 0)
    ordered = []
    while ready:
        key = ready.popleft()
        ordered.append(key)
        for child in children[key]:
            incoming[child] -= 1
            if incoming[child] == 0:
                ready.append(child)
    if len(ordered) != len(incoming):
        raise ValueError("Cyclic " + label + " prerequisites")
    return ordered


def validate(document, *, compiled, axis_ids, matrix_ids, domain_ids, root=ROOT):
    """Check identities, paths and prerequisite DAG; leave owner authority intact."""
    raw = wire_owner._encoded(document, MAX_BYTES, floats=True)
    wire_owner._fields(document, FIELDS, "learning framework")
    if document["schema"] != SCHEMA:
        raise ValueError("Unknown learning framework schema")
    if type(document["basis_commit"]) is not str or not re.fullmatch(r"[0-9a-f]{40}", document["basis_commit"]):
        raise ValueError("Framework basis requires a full commit identity")
    indexed = {key: _indexed(document[key], key)
               for key in ("sources", "stages", "methods", "agents", "objectives")}
    for key in ("assessment", "neural_design", "legacy_alignment"):
        _content(document[key], key)
    legacy = document["legacy_alignment"]
    if type(legacy) is not dict or "cards" not in legacy:
        raise ValueError("Legacy alignment requires its retained cards")
    cards = _indexed(legacy["cards"], "legacy cards")
    stage_order = _order(indexed["stages"], "stage")
    modules = {row["module"] for row in compiled["theorems"]}
    references = {"axis_ids": set(axis_ids), "matrix_ids": set(matrix_ids),
                  "domain_ids": set(domain_ids), "owner_modules": modules,
                  "source_ids": set(indexed["sources"]), "method_ids": set(indexed["methods"]),
                  "prerequisites": set(indexed["objectives"]),
                  "legacy_card_ids": set(cards)}
    paths, runtime_paths, mapped_cards = set(), set(), set()
    for relative in _ids(document["neural_design"].get("current_paths", []), "neural current_paths"):
        _path(relative, Path(root))
        paths.add(relative)
        runtime_paths.add(relative)
    routes = document["assessment"].get("route_examples", {})
    if type(routes) is not dict:
        raise ValueError("assessment route_examples requires an object")
    for name, relative in routes.items():
        wire_owner._text(name, "assessment route name", 1024)
        _path(relative, Path(root))
        paths.add(relative)
        runtime_paths.add(relative)
    for source in indexed["sources"].values():
        if "path" in source:
            _path(source["path"], Path(root))
            paths.add(source["path"])
    for agent in indexed["agents"].values():
        for relative in _ids(agent.get("existing_paths", []), "agent existing_paths"):
            _path(relative, Path(root))
            paths.add(relative)
    for identity, row in indexed["objectives"].items():
        wire_owner._fields(row, OBJECTIVE_FIELDS, "learning objective")
        for key in ("label_ar", "knowledge_ar", "skill_ar", "disposition_ar",
                    "acquisition_obligation_ar", "neural_status"):
            wire_owner._text(row[key], key, MAX_BYTES, content=True)
        for key, namespace in (("stage", "stages"), ("agent_id", "agents")):
            wire_owner._text(row[key], key, 1024)
            if row[key] not in indexed[namespace]:
                raise ValueError("Unresolved " + key + ": " + identity)
        for key, allowed in references.items():
            supplied = _ids(row[key], key)
            if not supplied <= allowed:
                raise ValueError("Unresolved " + key + ": " + identity)
        mapped_cards.update(row["legacy_card_ids"])
        for key in ("inputs", "outputs"):
            _text_list(row[key], key)
        for key in ("formative", "summative"):
            _assessment(row[key], key)
        for relative in _ids(row["runtime_refs"], "runtime_refs"):
            _path(relative, Path(root))
            paths.add(relative)
            runtime_paths.add(relative)
    if mapped_cards != cards.keys():
        raise ValueError("Retained legacy cards must all map to learning objectives")
    ordered = _order(indexed["objectives"], "objective")
    if "progressive_agents" in document["neural_design"]:
        from .agent_plan import validate_plan
        validate_plan(document["neural_design"]["progressive_agents"],
                      agents=indexed["agents"], objectives=indexed["objectives"])
    result = deepcopy(document)
    result["validation"] = {
        "authority": "CURRICULUM_REFERENCE_VALIDATION_ONLY",
        "neural_training_performed": False, "mastery_certified": False,
        "runtime_execution_performed": False,
        "counts": {key: len(rows) for key, rows in indexed.items()},
        "runtime_reference_count": len(runtime_paths), "referenced_file_count": len(paths),
        "legacy_card_count": len(cards), "legacy_cards_mapped": len(mapped_cards),
        "prerequisite_order": ordered, "stage_prerequisite_order": stage_order,
        "canonical_document_sha256": sha256(raw).hexdigest(),
        "scope": "References and prerequisite structure; no source interpretation, training or assessment certification.",
    }
    return result


def framework(*, compiled, axis_ids, matrix_ids, domain_ids):
    """Load the installed bounded document and validate its current references."""
    with PATH.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    document = wire_owner.strict_loads(raw, maximum_bytes=MAX_BYTES, report=True)
    result = validate(document, compiled=compiled, axis_ids=axis_ids,
                      matrix_ids=matrix_ids, domain_ids=domain_ids)
    result["validation"]["source_sha256"] = sha256(raw).hexdigest()
    return result
