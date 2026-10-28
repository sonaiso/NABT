"""Conditional source lifecycle replay; supplied premises do not become truth.

The independent protocol and authored scenarios precede this implementation.
Python proposes; the installed Lean executable replays the whole typed episode.
No caller receipt, source hash or status grants authority.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile

from tools import epistemic_measurement as em

ROOT = Path(__file__).resolve().parents[1]
LAW_ID = "nabt.evidence-lifecycle.v1"
EPISODE_SCHEMA = "nabt.evidence-lifecycle.episode.v1"
NATIVE = ROOT / "formal/.lake/build/bin/evidenceLifecycleV1"
MAX_REQUEST_BYTES = 1024 * 1024
MAX_REPORT_BYTES = 8 * 1024 * 1024
MAX_INTEGER = 2**53 - 1
FLAGS = {"world_truth_established": False, "source_authenticity_established": False,
         "referents_established": False, "all_arabic_complete": False}
InputError, ResourceLimit = em.InputError, em.ResourceLimit
CODE_PATHS = ("tools/evidence_lifecycle_v1.py", "tools/epistemic_measurement.py")
WHITESPACE_SCALARS = frozenset((*range(9, 14), *range(28, 33), 133, 160, 5760,
                              *range(8192, 8203), 8232, 8233, 8239, 8287, 12288))


def _json_shape(value, *, floats=False, depth=0):
    if depth > 32 or (depth == 32 and type(value) in (dict, list)):
        raise ResourceLimit("JSON nesting limit")
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise InputError("JSON keys must be strings")
        for key, item in value.items():
            _json_shape(key, floats=floats, depth=depth + 1)
            _json_shape(item, floats=floats, depth=depth + 1)
    elif type(value) is list:
        for item in value:
            _json_shape(item, floats=floats, depth=depth + 1)
    elif type(value) is str:
        try:
            value.encode("utf-8", "strict")
        except UnicodeError as error:
            raise InputError("Unpaired surrogate") from error
    elif type(value) is int:
        if abs(value) > MAX_INTEGER:
            raise ResourceLimit("Exact integer magnitude limit")
    elif type(value) is float:
        if not floats or not math.isfinite(value):
            raise InputError("Noncanonical JSON number")
    elif type(value) not in (bool, type(None)):
        raise InputError("Non-JSON value")


def wire(value):
    """Typed canonical serialization; floats are reserved for existing reports."""
    _json_shape(value, floats=True)
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _encoded(value, maximum, *, floats=False):
    _json_shape(value, floats=floats)
    raw = wire(value).encode("utf-8")
    if len(raw) > maximum:
        raise ResourceLimit("JSON byte limit")
    return raw


def _integer(value):
    if re.fullmatch(r"0|-?[1-9][0-9]*", value) is None:
        raise InputError("Noncanonical integer")
    if len(value.lstrip("-")) > 16:
        raise ResourceLimit("Integer digit limit")
    result = int(value)
    if abs(result) > MAX_INTEGER:
        raise ResourceLimit("Exact integer magnitude limit")
    return result


def _bad_number(_):
    raise InputError("Noncanonical JSON number")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("Duplicate decoded JSON key")
        result[key] = value
    return result


def strict_loads(raw, *, maximum_bytes=MAX_REQUEST_BYTES, report=False):
    if type(raw) not in (str, bytes):
        raise InputError("JSON text required")
    try:
        raw = raw.encode("utf-8", "strict") if type(raw) is str else raw
        if len(raw) > maximum_bytes:
            raise ResourceLimit("JSON byte limit")
        text = raw.decode("utf-8", "strict")
        # Reject deep transport before the parser can hit its recursion limit.
        depth, quoted, escaped = 0, False, False
        for char in text:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > 32:
                    raise ResourceLimit("JSON nesting limit")
            elif char in "]}":
                depth -= 1
        value = json.loads(text, object_pairs_hook=_pairs, parse_int=_integer,
                           parse_float=float if report else _bad_number,
                           parse_constant=_bad_number)
        _json_shape(value, floats=report)
        return value
    except (UnicodeError, json.JSONDecodeError) as error:
        raise InputError("Malformed UTF-8 JSON") from error
    except RecursionError as error:
        raise ResourceLimit("JSON nesting limit") from error


def _fields(value, names, label):
    if type(value) is not dict or set(value) != set(names):
        raise InputError(label + " has missing or unexpected fields")


def _text(value, label, maximum=4096, *, content=False):
    if type(value) is not str or not value or all(ord(c) in WHITESPACE_SCALARS for c in value):
        raise InputError(label + " requires nonempty text")
    if not content and any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise InputError(label + " contains an ASCII control")
    try:
        raw = value.encode("utf-8", "strict")
    except UnicodeError as error:
        raise InputError(label + " is not strict UTF-8") from error
    if len(raw) > maximum:
        raise ResourceLimit(label + " byte limit")


def _array(value, label, maximum=64):
    if type(value) is not list:
        raise InputError(label + " requires an array")
    if len(value) > maximum:
        raise ResourceLimit(label + " item limit")


def _natural(value, label, maximum=64):
    if type(value) is not int or value < 0:
        raise InputError(label + " requires a natural, not a Boolean")
    if value > maximum:
        raise ResourceLimit(label + " limit")


def _names(value, label):
    _array(value, label)
    for name in value:
        _text(name, label)
    if len(set(value)) != len(value):
        raise InputError(label + " contains duplicate IDs")


def _source(value):
    _fields(value, ("identity", "revision", "content"), "source")
    _text(value["identity"], "source.identity")
    _text(value["revision"], "source.revision")
    _text(value["content"], "source.content", 16 * 1024, content=True)


def _query(value):
    _fields(value, ("key", "positive", "origin"), "query")
    _key(value["key"])
    _text(value["origin"], "query.origin")
    if type(value["positive"]) is not bool:
        raise InputError("query.positive requires a Boolean")


def _key(value):
    _fields(value, em.KEY_FIELDS, "key")
    for key, text in value.items():
        _text(text, "key." + key, 32 if key == "time" else 4096)
    # Reuse the original exact axis/time/key contract; no time/unit conversion.
    em._key(value)


def _source_key(value):
    return value["identity"], value["revision"], value["content"]


def _states(episode):
    """Validate every transition before exposing any history."""
    active = deepcopy(episode["active_sources"])
    known = {_source_key(source) for source in active}
    known.update(_source_key(row["source"]) for row in episode["bindings"])
    known.update(_source_key(row["source"]) for row in episode["interpretations"])
    states = [deepcopy(active)]
    for event in episode["updates"]:
        source, kind = event["source"], event["kind"]
        if kind != "replace" and _source_key(source) not in known:
            raise InputError("Update target is not yet registered")
        if kind == "withdraw":
            active = [item for item in active if item != source]
        elif kind == "activate":
            if source not in active:
                if any(item["identity"] == source["identity"] for item in active):
                    raise InputError("Another source revision is active")
                active.append(deepcopy(source))
        else:
            replacement = event["replacement"]
            if (source not in active or replacement["identity"] != source["identity"]
                    or replacement["revision"] == source["revision"]):
                raise InputError("Invalid replacement transition")
            active = [item for item in active if item != source] + [deepcopy(replacement)]
            known.add(_source_key(replacement))
        _array(active, "active_sources")
        states.append(deepcopy(active))
    return states


def validate_episode(episode):
    _encoded(episode, MAX_REQUEST_BYTES)
    _fields(episode, ("schema", "episode_id", "query", "active_sources", "origins",
                     "interpretations", "bindings", "budget", "updates"), "episode")
    if episode["schema"] != EPISODE_SCHEMA:
        raise InputError("Unknown episode schema")
    _text(episode["episode_id"], "episode_id", 128)
    _query(episode["query"])
    _natural(episode["budget"], "budget")
    for key in ("active_sources", "origins", "interpretations", "bindings", "updates"):
        _array(episode[key], key, 16 if key == "updates" else 64)
    all_sources = []
    for source in episode["active_sources"]:
        _source(source)
        all_sources.append(source)
    if len({s["identity"] for s in episode["active_sources"]}) != len(episode["active_sources"]):
        raise InputError("Duplicate active source identity")
    origins = {}
    for node in episode["origins"]:
        _fields(node, ("id", "parents"), "origin")
        _text(node["id"], "origin.id")
        _names(node["parents"], "origin.parents")
        if node["id"] in origins:
            raise InputError("Duplicate origin ID")
        origins[node["id"]] = node
    if episode["query"]["origin"] not in origins:
        raise InputError("Unknown query origin")
    if any(parent not in origins for node in origins.values() for parent in node["parents"]):
        raise InputError("Unknown parent origin")
    bindings = {}
    for row in episode["bindings"]:
        _fields(row, ("origin_id", "source", "rank"), "binding")
        _text(row["origin_id"], "binding.origin_id")
        _source(row["source"])
        all_sources.append(row["source"])
        _natural(row["rank"], "binding.rank")
        if row["origin_id"] in bindings:
            raise InputError("Duplicate origin binding")
        bindings[row["origin_id"]] = row
    if set(bindings) != set(origins):
        raise InputError("Origin binding inventory differs")
    if any(bindings[parent]["rank"] >= bindings[node["id"]]["rank"]
           for node in origins.values() for parent in node["parents"]):
        raise InputError("Parent rank does not decrease")
    evidence_ids = set()
    for row in episode["interpretations"]:
        _fields(row, ("id", "source", "key", "positive", "kind", "origin", "ancestry"), "evidence")
        _text(row["id"], "evidence.id")
        _source(row["source"])
        all_sources.append(row["source"])
        _key(row["key"])
        if type(row["positive"]) is not bool:
            raise InputError("Evidence polarity requires a Boolean")
        if row["kind"] not in ("self_report", "observation", "lexical", "grammar", "hypothetical", "quotation"):
            raise InputError("Unknown evidence kind")
        _text(row["origin"], "evidence.origin")
        _names(row["ancestry"], "evidence.ancestry")
        if row["origin"] not in origins or any(n not in origins for n in row["ancestry"]):
            raise InputError("Unknown evidence origin")
        if row["id"] in evidence_ids:
            raise InputError("Duplicate evidence ID")
        evidence_ids.add(row["id"])
    events = set()
    for event in episode["updates"]:
        _fields(event, ("event_id", "kind", "source", "replacement", "reason"), "event")
        _text(event["event_id"], "event_id", 128)
        _text(event["reason"], "event.reason")
        if event["event_id"] in events:
            raise InputError("Duplicate event ID")
        events.add(event["event_id"])
        if event["kind"] not in ("withdraw", "activate", "replace"):
            raise InputError("Unknown update kind")
        _source(event["source"])
        all_sources.append(event["source"])
        if event["kind"] == "replace":
            _source(event["replacement"])
            all_sources.append(event["replacement"])
        elif event["replacement"] is not None:
            raise InputError("Replacement must be null")
    contents = {}
    for source in all_sources:
        identity = source["identity"], source["revision"]
        if identity in contents and contents[identity] != source["content"]:
            raise InputError("Source identity/revision content collision")
        contents[identity] = source["content"]
    _states(episode)
    return deepcopy(episode)


def propose_episode(episode):
    """Untrusted complete proposal; never an admission of authored premises."""
    episode = validate_episode(episode)
    bindings = {b["origin_id"]: b["source"] for b in episode["bindings"]}
    parents = {n["id"]: set(n["parents"]) for n in episode["origins"]}
    steps, previous = [], set()
    for index, active in enumerate(_states(episode)):
        ready, blocked, affected = [], [], []
        if len(episode["interpretations"]) > episode["budget"]:
            receipt = {"status": "RESOURCE_LIMIT", "support_ids": [], "refutation_ids": [], "selected_ids": []}
            ready = blocked = affected = None
        else:
            for row in episode["interpretations"]:
                ancestry = set(row["ancestry"])
                eligible = (row["source"] == bindings[row["origin"]] and row["origin"] in ancestry
                            and all(parents[n] <= ancestry for n in ancestry)
                            and all(bindings[n] in active for n in ancestry))
                (ready if eligible else blocked).append(row["id"])
            current = set(ready)
            affected = [r["id"] for r in episode["interpretations"]
                        if r["id"] in current ^ previous] if index else []
            # The original ledger budget was checked above, before filtering.
            receipt = em.propose({"query": episode["query"], "active_sources": active,
                "origins": episode["origins"], "interpretations": [r for r in episode["interpretations"] if r["id"] in current],
                "budget": episode["budget"], "certificate": None})
            previous = current
        steps.append({"step": index, "event_id": None if index == 0 else episode["updates"][index - 1]["event_id"],
                      "active_sources": active, "receipt": receipt, "dependency_ready_ids": ready,
                      "dependency_blocked_ids": blocked, "affected_ids": affected})
    result = {"law_id": LAW_ID, "binding": episode, "steps": steps, **FLAGS}
    _encoded(result, MAX_REPORT_BYTES)
    return result


def run_identity(code_paths=CODE_PATHS, native_paths=None):
    """Measured execution identity, not a caller-selected source of authority."""
    if native_paths is None:
        native_paths = (NATIVE,)
    code = {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in sorted(code_paths)}
    native = {(path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)):
              sha256(path.read_bytes()).hexdigest() if path.is_file() else None for path in sorted(native_paths)}
    return {"code": code, "native": native}


def _native(episode):
    raw = _encoded(episode, MAX_REQUEST_BYTES)
    with tempfile.TemporaryDirectory(prefix="nabt-evidence-lifecycle-") as directory:
        output_path = Path(directory) / "response.json"
        with output_path.open("wb") as output:
            result = subprocess.run([str(NATIVE)], input=raw + b"\n", stdout=output,
                                    stderr=subprocess.DEVNULL, timeout=30, check=False)
        with output_path.open("rb") as output:
            raw = output.read(MAX_REPORT_BYTES + 1)
    response = strict_loads(raw, maximum_bytes=MAX_REPORT_BYTES)
    if result.returncode not in (0, 2) or type(response) is not dict:
        raise InputError("Native transport failed")
    if result.returncode and "binding" in response:
        raise InputError("Native transport and accepted envelope disagree")
    return response


def _base():
    return {"schema": "nabt.evidence-lifecycle.result.v1", "law_id": LAW_ID,
            "status": "UNMEASURED", "native_checked": False, "decision_complete": False,
            "evidence_class": "AUTHORED_SCENARIO", "observed": None,
            "execution": {"input": None, "proposal": None, "native_result": None,
                          "input_sha256": None, "proposal_sha256": None, "native_result_sha256": None,
                          "run_identity": None, "error": None}, **FLAGS}


def evaluate_episode(episode):
    result = _base()
    execution = result["execution"]
    try:
        valid = validate_episode(episode)
        execution["input"] = valid
        execution["input_sha256"] = sha256(_encoded(valid, MAX_REQUEST_BYTES)).hexdigest()
        proposed = propose_episode(valid)
        execution["proposal"] = proposed
        execution["proposal_sha256"] = sha256(_encoded(proposed, MAX_REPORT_BYTES)).hexdigest()
        identity = run_identity()
        execution["run_identity"] = identity
        if not NATIVE.is_file():
            execution["error"] = "NATIVE_UNAVAILABLE"
        else:
            actual = _native(valid)
            execution["native_result"] = actual
            execution["native_result_sha256"] = sha256(_encoded(actual, MAX_REPORT_BYTES)).hexdigest()
            if identity != run_identity():
                result["status"] = "VERIFICATION_FAILED"
                execution["error"] = "CODE_OR_NATIVE_CHANGED_DURING_REPLAY"
            elif _encoded(actual, MAX_REPORT_BYTES) != _encoded(proposed, MAX_REPORT_BYTES):
                result["status"] = "VERIFICATION_FAILED"
                execution["error"] = "WHOLE_NATIVE_ENVELOPE_DIFFERS"
            else:
                status = actual["steps"][-1]["receipt"]["status"]
                result.update(status=status, native_checked=True, decision_complete=status != "RESOURCE_LIMIT", observed=actual)
    except ResourceLimit as error:
        result.update(status="RESOURCE_LIMIT", observed=None, native_checked=False, decision_complete=False)
        execution["error"] = str(error)
    except subprocess.TimeoutExpired:
        result["status"] = "RESOURCE_LIMIT"
        execution["error"] = "NATIVE_TIMEOUT"
    except (FileNotFoundError, PermissionError) as error:
        execution["error"] = "VERIFICATION_UNAVAILABLE: " + str(error)
    except (InputError, ValueError, TypeError, KeyError, UnicodeError, RecursionError) as error:
        result["status"] = "INVALID_INPUT" if execution["input"] is None else "VERIFICATION_FAILED"
        execution["error"] = str(error) or type(error).__name__
    except OSError as error:
        execution["error"] = "VERIFICATION_UNAVAILABLE: " + str(error)
    try:
        _encoded(result, MAX_REPORT_BYTES)
    except ResourceLimit:
        result = _base()
        result.update(status="RESOURCE_LIMIT")
        result["execution"]["error"] = "WHOLE_REPORT_BYTE_LIMIT"
    return result


def verify_episode(report, *, expected_episode):
    """Expected episode is independent input, never read from a submitted receipt."""
    try:
        encoded = _encoded(report, MAX_REPORT_BYTES)
        expected = evaluate_episode(expected_episode)
        matches = encoded == _encoded(expected, MAX_REPORT_BYTES)
        return {"replay_matches": matches,
                "valid": matches and expected["native_checked"] and expected["decision_complete"],
                "status": expected["status"] if matches else "INVALID_RECEIPT"}
    except ResourceLimit:
        return {"replay_matches": False, "valid": False, "status": "RESOURCE_LIMIT"}
    except (InputError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return {"replay_matches": False, "valid": False, "status": "INVALID_RECEIPT"}
