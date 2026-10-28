"""Installed 53-origin source lifecycle for the existing productive clause law.

The graph is rebuilt from reopened pinned files, never accepted from a caller.
Grammar readiness qualifies the original nine gates; it is not world evidence.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from tools import evidence_lifecycle_v1 as lifecycle
from tools import productive_clause_v1 as clause

ROOT = Path(__file__).resolve().parents[1]
LAW_ID = "nabt.productive-clause-lifecycle.v1"
SCOPE_PATH = "evidence/evidence_lifecycle_v1/source_scope.json"
SCOPE_SHA256 = "61eae397c316f29726acf64330039086802f18f6b2c1a3e149d910b27814b660"
ACQUISITION_PACKET = "evidence/sourced_acquisition_v3/source_evidence.json"
PRODUCTIVE_PACKET = "evidence/productive_clause_v1/source_scope.json"
INPUT_ID = "input:productive-clause-v1"
QUERY_ID = "query:productive-clause-v1"
DERIVED_ID = "derived:productive-clause-v1"
ROW_ID = "productive-clause-dependency"
PACKET_IDS = ("packet:sourced-acquisition-v3", "packet:productive-clause-v1")
DEPENDENCY_IDS = ("dependency:aligned-acquisition-v1", "dependency:article-acquisition-v2", "dependency:natural-sources-v3")
NATIVE_NAMES = ("alignedAcquisition", "licensedInference", "connectedAcquisitionV3", "productiveClauseV1", "evidenceLifecycleV1")
BYTE_ONLY_PASSAGES = frozenset(("natural_eye_senses", "natural_eye_definition", "natural_spring_definition"))
wire = lifecycle.wire
_store = clause.acquisition
_DEFAULT_EVENTS = object()


def _read(relative, maximum):
    return _store._read_bounded(_store._installed_path(relative), maximum)


def _source(identity, value, revision=None):
    content = wire(value)
    return {"identity": identity, "revision": revision or sha256(content.encode()).hexdigest(), "content": content}


def _origin(identity):
    return "origin:" + identity


def _quotation(row, data, namespace):
    start, end = row["byte_start_0based"], row["byte_end_0based_exclusive"]
    excerpt = data[start:end]
    if (excerpt.decode("utf-8", "strict") != row["raw_text"]
            or sha256(excerpt).hexdigest() != row["span_sha256"]
            or sha256(data).hexdigest() != row["source_sha256"]):
        raise ValueError("Retained source quotation differs")
    if namespace == "acquisition" and row["id"] in BYTE_ONLY_PASSAGES:
        # Explicit reviewed projection erratum: these original rows have only
        # byte coordinates. Do not invent line metadata or relax other rows.
        if "line_start_1based" in row or "line_end_1based_inclusive" in row:
            raise ValueError("Byte-only passage metadata changed")
        first = last = None
    else:
        first, last = row["line_start_1based"], row["line_end_1based_inclusive"]
        if type(first) is not int or type(last) is not int or not 1 <= first <= last:
            raise ValueError("Expected exact line coordinates")
        lines = data.splitlines(keepends=True)
        if sum(map(len, lines[:first - 1])) != start or sum(map(len, lines[:last])) != end:
            raise ValueError("Retained source line coordinates differ")
    return {"kind": "passage_quotation", "source_id": row["source_id"],
            "source_revision": row["source_sha256"], "byte_start": start, "byte_end": end,
            "line_start": first, "line_end": last, "raw_text": row["raw_text"]}


def _inventory():
    """Replay full retained files and all slices, then construct bounded values."""
    raw = _read(SCOPE_PATH, lifecycle.MAX_REQUEST_BYTES)
    if sha256(raw).hexdigest() != SCOPE_SHA256:
        raise ValueError("Installed lifecycle source profile changed")
    profile = lifecycle.strict_loads(raw)
    projection = profile["productive_dependency_profile"]
    # These routines additionally verify complete installed reading tables.
    clause.source_inventory()
    _store.source_inventory()
    pins = {row["path"]: row for row in profile["installed_packet_pins"]}
    packet_raw = {}
    for path, pin in pins.items():
        data = _read(path, pin["bytes"])
        if len(data) != pin["bytes"] or sha256(data).hexdigest() != pin["sha256"]:
            raise ValueError("Installed packet bytes changed")
        packet_raw[path] = data
    acquisition = lifecycle.strict_loads(packet_raw[ACQUISITION_PACKET])
    productive = lifecycle.strict_loads(packet_raw[PRODUCTIVE_PACKET])
    if ([s["source_id"] for s in acquisition["sources"]] != projection["source_order"]
            or [p["id"] for p in acquisition["passages"]] != projection["acquisition_passage_order"]
            or [p["id"] for p in productive["passages"]] != projection["productive_passage_order"]):
        raise ValueError("Installed source or passage order changed")
    book_rows = {row["source_id"]: row for row in acquisition["sources"]}
    for row in productive["sources"]:
        existing = book_rows[row["source_id"]]
        if any(row[key] != existing[key] for key in ("repository_path", "source_sha256", "bytes")):
            raise ValueError("Shared retained source identities differ")
    sources, ranks, parents, file_replays, passage_replays, books = {}, {}, {}, [], [], {}

    def add(identity, source, rank, dependencies=()):
        if identity in sources:
            raise ValueError("Duplicate installed source target")
        sources[identity], ranks[identity], parents[identity] = source, rank, list(dependencies)

    for row in acquisition["sources"]:
        identity, path = row["source_id"], row["repository_path"]
        data = _read(path, row["bytes"])
        if len(data) != row["bytes"] or sha256(data).hexdigest() != row["source_sha256"]:
            raise ValueError("Retained source bytes differ")
        books[identity] = data
        descriptor = {"kind": "retained_source_descriptor", "path": path,
                      "bytes": len(data), "sha256": row["source_sha256"]}
        add(identity, _source(identity, descriptor, row["source_sha256"]), 0)
        file_replays.append({"target": identity, **descriptor})
    if len(acquisition["upstream_dependencies"]) != 3:
        raise ValueError("Upstream dependency inventory differs")
    for identity, row in zip(DEPENDENCY_IDS, acquisition["upstream_dependencies"]):
        data = packet_raw[row["path"]]
        if sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("Upstream source identity differs")
        descriptor = {"kind": "upstream_packet_descriptor", "path": row["path"],
                      "bytes": len(data), "sha256": row["sha256"]}
        add(identity, _source(identity, descriptor, row["sha256"]), 0)
        file_replays.append({"target": identity, **descriptor})
    for namespace, packet in (("acquisition", acquisition), ("productive", productive)):
        for row in packet["passages"]:
            identity = namespace + "-passage:" + row["id"]
            data = books[row["source_id"]]
            quotation = _quotation(row, data, namespace)
            add(identity, _source(identity, quotation, row["span_sha256"]), 1, (row["source_id"],))
            passage_replays.append({"target": identity, "span_sha256": row["span_sha256"], **quotation})
    for identity, path, packet, namespace in (
            (PACKET_IDS[0], ACQUISITION_PACKET, acquisition, "acquisition"),
            (PACKET_IDS[1], PRODUCTIVE_PACKET, productive, "productive")):
        data = packet_raw[path]
        descriptor = {"kind": "source_packet_descriptor", "law_id": packet["law_id"],
                      "path": path, "bytes": len(data), "sha256": sha256(data).hexdigest()}
        dependencies = [namespace + "-passage:" + row["id"] for row in packet["passages"]]
        if namespace == "acquisition":
            dependencies += list(DEPENDENCY_IDS)
        add(identity, _source(identity, descriptor, descriptor["sha256"]), 2, dependencies)
        file_replays.append({"target": identity, **descriptor})
    if len(sources) != 50:
        raise ValueError("Installed target inventory is not fifty sources")
    return {"sources": sources, "ranks": ranks, "parents": parents,
            "source_replay": {"profile_sha256": SCOPE_SHA256, "files": file_replays,
                              "passages": passage_replays,
                              "authority": "FULL_FILE_REPLAY_AND_AUTHORED_PROJECTION"}}


def installed_targets():
    inventory = _inventory()
    return {"law_id": LAW_ID, "targets": [{"target": identity, "source": value,
            "rank": inventory["ranks"][identity], "parents": [_origin(n) for n in inventory["parents"][identity]]}
            for identity, value in inventory["sources"].items()], "source_replay": inventory["source_replay"]}


def _events(events, targets=None):
    lifecycle._encoded(events, lifecycle.MAX_REQUEST_BYTES)
    lifecycle._array(events, "events", 16)
    known = set()
    for event in events:
        lifecycle._fields(event, ("event_id", "kind", "target", "reason"), "clause event")
        lifecycle._text(event["event_id"], "event_id", 128)
        lifecycle._text(event["target"], "event.target")
        lifecycle._text(event["reason"], "event.reason")
        if event["event_id"] in known or event["kind"] not in ("withdraw", "activate"):
            raise lifecycle.InputError("Duplicate event ID or unsupported update")
        if targets is not None and event["target"] not in targets:
            raise lifecycle.InputError("Unknown installed event target")
        known.add(event["event_id"])
    return deepcopy(events)


def _episode(request, events, inventory):
    sources = dict(inventory["sources"])
    ranks, parents = dict(inventory["ranks"]), dict(inventory["parents"])
    sources[INPUT_ID] = _source(INPUT_ID, {"kind": "raw_clause_request", **request})
    sources[QUERY_ID] = _source(QUERY_ID, {"kind": "dependency_query", "adapter_law_id": LAW_ID})
    sources[DERIVED_ID] = _source(DERIVED_ID, {"kind": "clause_dependency", "adapter_law_id": LAW_ID,
        "clause_law_id": clause.LAW_ID, "syntax_law_id": clause.SYNTAX_LAW_ID,
        "input_revision": sources[INPUT_ID]["revision"]})
    ranks.update({INPUT_ID: 0, QUERY_ID: 0, DERIVED_ID: 3})
    parents.update({INPUT_ID: [], QUERY_ID: [], DERIVED_ID: [INPUT_ID, *PACKET_IDS]})
    ordered = list(inventory["sources"])
    ordered[10:10] = [INPUT_ID, QUERY_ID]
    ordered.append(DERIVED_ID)
    key = {"axis": "recorded_observation", "entity": "productive-clause-input",
           "predicate": "installed-clause-dependency", "value": "ready", "unit": "not-applicable",
           "context": sources[INPUT_ID]["revision"], "time": "0", "place": "not-applicable"}
    episode = {"schema": lifecycle.EPISODE_SCHEMA,
        "episode_id": "productive-clause:" + sha256(wire({"request": request, "events": events}).encode()).hexdigest(),
        "query": {"key": key, "positive": True, "origin": _origin(QUERY_ID)},
        "active_sources": [sources[n] for n in ordered],
        "origins": [{"id": _origin(n), "parents": [_origin(p) for p in parents[n]]} for n in ordered],
        "bindings": [{"origin_id": _origin(n), "source": sources[n], "rank": ranks[n]} for n in ordered],
        "interpretations": [{"id": ROW_ID, "source": sources[DERIVED_ID], "key": key,
                             "positive": True, "kind": "grammar", "origin": _origin(DERIVED_ID),
                             "ancestry": [_origin(n) for n in ordered if n != QUERY_ID]}],
        "budget": 1,
        "updates": [{"event_id": e["event_id"], "kind": e["kind"], "source": sources[e["target"]],
                     "replacement": None, "reason": e["reason"]} for e in events]}
    return lifecycle.validate_episode(episode)


def _run_identity():
    # The existing source reader imports these core modules and table resources.
    code = set(lifecycle.CODE_PATHS) | {"tools/productive_lifecycle_v1.py", "tools/productive_clause_v1.py",
        "tools/aligned_acquisition.py", "tools/connected_acquisition_v3.py", "src/nabt/data/law.json",
        "src/nabt/data/words.json", "src/nabt/data/source_evidence/word_policy.json"}
    code.update(p.relative_to(ROOT).as_posix() for p in (ROOT / "src/nabt").rglob("*.py"))
    return lifecycle.run_identity(code, [ROOT / "formal/.lake/build/bin" / name for name in NATIVE_NAMES])


def _base():
    return {"schema": "nabt.productive-clause-lifecycle-result.v1", "law_id": LAW_ID,
            "status": "UNMEASURED", "verified": False, "chain_complete": False,
            "request": None, "events": None, "source_replay": None, "original_clause": None,
            "lifecycle": None, "chain_history": [], "reading": None,
            "candidate_space": clause._candidate_space(), "blocked_by": [], "current_step": None,
            "run_identity": None, "error": None, "world_truth_established": False,
            "referents_established": False, "entails_exclusivity": False, "all_arabic_complete": False}


def _pending_space(original, obligation):
    space = deepcopy(original["candidate_space"])
    for candidate in space["candidates"]:
        candidate["state"] = "PENDING"
        if obligation not in candidate["obligations"]:
            candidate["obligations"].append(obligation)
    return space


def _history_row(original, step):
    ready = step["dependency_ready_ids"] == [ROW_ID]
    complete = ready and original["chain_complete"] is True and all(
        original["gates"].get(name) is True for name in clause.GATE_NAMES)
    status, blocked = original["status"], list(original["blocked_by"])
    space = deepcopy(original["candidate_space"])
    if not ready:
        blocked.append("SOURCE_DEPENDENCY_NOT_READY")
        space = _pending_space(original, "SOURCE_DEPENDENCY_NOT_READY")
        if status in ("LICENSED_CLAUSE", "REJECTED_IN_SCOPE"):
            status = "PENDING_DEPENDENCIES"
    return {"step": step["step"], "event_id": step["event_id"], "dependency_ready": ready,
            "chain_complete": complete, "status": status, "blocked_by": blocked, "candidate_space": space}


def evaluate_clause(text, *, source_id="input", revision="1", scope="default", ending="wasl",
                    onset="word_initial", events=_DEFAULT_EVENTS):
    result = _base()
    try:
        request = clause._request(text, source_id, revision, scope, ending, onset)
        events = _events([] if events is _DEFAULT_EVENTS else events)
        result.update(request=request, events=events)
    except (lifecycle.ResourceLimit, OverflowError):
        return {**result, "status": "RESOURCE_LIMIT", "error": "INPUT_RESOURCE_LIMIT"}
    except (lifecycle.InputError, ValueError, TypeError, UnicodeError, RecursionError):
        return {**result, "status": "INVALID_INPUT", "error": "INVALID_REQUEST_OR_EVENTS"}
    try:
        before = _run_identity()
        result["run_identity"] = before
        inventory = _inventory()
        _events(events, inventory["sources"])
        result["source_replay"] = inventory["source_replay"]
        episode = _episode(request, events, inventory)
    except lifecycle.ResourceLimit as error:
        return {**result, "status": "RESOURCE_LIMIT", "error": str(error)}
    except lifecycle.InputError as error:
        return {**result, "status": "INVALID_INPUT", "error": str(error)}
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
        return {**result, "status": "SOURCE_EVIDENCE_UNAVAILABLE", "error": str(error)}
    binding = {key: request[key] for key in ("source_id", "revision", "scope", "ending", "onset")}
    original = clause.evaluate(request["text"], **binding)
    result["original_clause"] = original
    result["candidate_space"] = _pending_space(original, "LIFECYCLE_NOT_VERIFIED")
    result["blocked_by"] = list(original["blocked_by"]) + ["LIFECYCLE_NOT_VERIFIED"]
    checked = lifecycle.evaluate_episode(episode)
    result["lifecycle"] = checked
    if not checked["native_checked"] or not checked["decision_complete"]:
        result.update(status=checked["status"], error=checked["execution"]["error"])
        return result
    try:
        if before != _run_identity() or wire(inventory) != wire(_inventory()):
            raise ValueError("CODE_NATIVE_OR_RETAINED_SOURCES_CHANGED_DURING_REPLAY")
        native = checked["observed"]
        if wire(native["binding"]) != wire(episode):
            raise ValueError("Lifecycle binding differs from installed projection")
        for step in native["steps"]:
            if step["receipt"] != {"status": "UNKNOWN", "support_ids": [], "refutation_ids": [], "selected_ids": []}:
                raise ValueError("Grammar dependency was promoted to an observation")
        history = [_history_row(original, step) for step in native["steps"]]
        last = history[-1]
        result.update(chain_history=history, status=last["status"], verified=last["chain_complete"],
            chain_complete=last["chain_complete"], current_step=last["step"],
            candidate_space=last["candidate_space"], blocked_by=last["blocked_by"],
            reading=original["reading"] if last["chain_complete"] else None)
        lifecycle._encoded(result, lifecycle.MAX_REPORT_BYTES, floats=True)
    except lifecycle.ResourceLimit as error:
        result = {**_base(), "status": "RESOURCE_LIMIT", "error": str(error)}
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
        result.update(status="VERIFICATION_FAILED", error=str(error), verified=False,
                      chain_complete=False, reading=None, chain_history=[], current_step=None,
                      candidate_space=_pending_space(original, "LIFECYCLE_NOT_VERIFIED"),
                      blocked_by=list(original["blocked_by"]) + ["LIFECYCLE_NOT_VERIFIED"])
    return result


def verify_clause(report, *, text, source_id, revision, scope, ending, onset, events):
    try:
        encoded = lifecycle._encoded(report, lifecycle.MAX_REPORT_BYTES, floats=True)
        expected = evaluate_clause(text, source_id=source_id, revision=revision, scope=scope,
                                   ending=ending, onset=onset, events=events)
        matches = encoded == lifecycle._encoded(expected, lifecycle.MAX_REPORT_BYTES, floats=True)
        return {"replay_matches": matches, "valid": matches and expected["chain_complete"],
                "status": expected["status"] if matches else "INVALID_RECEIPT"}
    except lifecycle.ResourceLimit:
        return {"replay_matches": False, "valid": False, "status": "RESOURCE_LIMIT"}
    except (lifecycle.InputError, ValueError, KeyError, TypeError, UnicodeError, RecursionError):
        return {"replay_matches": False, "valid": False, "status": "INVALID_RECEIPT"}
