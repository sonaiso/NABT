"""Views of existing native definitions, never a second lexical dictionary."""
from copy import deepcopy
from hashlib import sha256
import subprocess

from tools import lexical_testimony as owner
from tools.evidence_lifecycle_v1 import wire
from . import reasoning_curriculum as curriculum

LAW = "nabt.concept-continuity.v1"
NATIVE = owner.ROOT / "formal/.lake/build/bin/lexicalDenotation"
VIEWS = {r[0] for r in curriculum.MATRICES} | {"dal", "madlul", "dal_madlul"}


def reference(identity):
    """Definition changes version the reference; domain/view never do."""
    return {"id": identity["id"], "definition": deepcopy(identity["definition"]),
            "definition_sha256": sha256(wire(identity).encode()).hexdigest()}


def catalogue():
    raw = (owner.ROOT / owner.CATALOG).read_bytes()
    if owner._sha(raw) != owner.CATALOG_SHA:
        raise ValueError("CATALOGUE_IDENTITY_CHANGED")
    retained = owner._strict_json(raw)
    proc = subprocess.run([str(NATIVE), "--concepts"], capture_output=True,
                          check=True, timeout=20)
    if len(proc.stdout) > 1024 * 1024:
        raise ValueError("CONCEPT_RESPONSE_LIMIT")
    result = owner._strict_json(proc.stdout)
    if (result.get("schema") != "nabt.shared-concept-definitions.v1"
            or result.get("law_id") != LAW
            or [r["sense"] for r in result["concepts"]] !=
               [{k:s[k] for k in ("id", "root", "citation", "components")}
                for s in retained["senses"]]
            or any(r["identity"]["id"] != r["sense"]["id"] for r in result["concepts"])):
        raise ValueError("NATIVE_CONCEPT_CATALOGUE_DIFFERS")
    for row in result["concepts"]:
        row["reference"] = reference(row["identity"])
        row["testimony"] = owner._citation(row["sense"]["citation"], owner.ROOT)
    return result


def validate(request):
    if type(request) is not dict or set(request) != {"kind", "value", "view", "domain"}:
        raise ValueError("Expected kind, value, view and domain")
    if (type(request["view"]) is not str or request["view"] not in VIEWS
            or type(request["domain"]) is not str
            or request["domain"] not in {r[0] for r in curriculum.DOMAINS}):
        raise ValueError("Unknown concept view or curriculum domain")
    k, v = request["kind"], request["value"]
    if not ((k == "lexical" and type(v) is str and v.strip() and len(v.encode()) <= 128)
            or (k == "cardinal" and type(v) is int and 0 <= v <= 10**9)):
        raise ValueError("Expected installed dictionary index or bounded cardinal")
    return deepcopy(request)


def evaluate(request):
    p = validate(request)
    out = {"schema": "nabt.concept-view.v1", "law_id": LAW, "request": p,
           "status": "DEFER", "native_checked": False, "concepts": [],
           "world_truth_established": False, "intended_sense_established": False,
           "concept_identity_includes_view": False}
    try:
        if p["kind"] == "cardinal":
            native = owner._native(NATIVE, {"op": "cardinal_concept", "value": p["value"]})
            if native.get("schema") != "nabt.shared-cardinal-definition.v1" or native.get("value") != p["value"]:
                raise ValueError("CARDINAL_EXPORT_DIFFERS")
            rows = [{"identity": native["identity"], "reference": reference(native["identity"])}]
        else:
            native = catalogue()
            rows = [r for r in native["concepts"] if r["sense"]["root"] == p["value"]]
        out.update(status="DEFINITIONS_AVAILABLE" if rows else "UNMEASURED_ROOT",
                   native_checked=True, concepts=rows,
                   native_sha256=owner._sha(NATIVE.read_bytes()))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        out["reason"] = type(error).__name__
    return out
