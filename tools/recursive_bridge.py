"""Replay-backed transport from exact morphology and discourse into recursive units.

The complete old reports remain in the envelope.  Source coordinates are
converted through an explicit UTF-8 boundary table; radical fibers are never
joined as though their members were adjacent.  Source reconstruction is a new
ordered audit tree, not a recovered original syntax tree.  Transport validation
does not certify an arbitrary grammar's realization functions or acquire a
lexical root, category, role, or meaning.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nabt.derivation import (ALPHABET_ID, EXPECTED_TABLE_SHA256, installed_registry,
                            read_derivation)
from nabt.discourse_reader import read_discourse
from nabt.errors import NabtError, natural, resource_limit


LAW_ID = "nabt.recursive-source-transport.v1"
ASSESSMENT_ID = "nabt.recursive-source-assessment.v1"
LEAN_LAW_ID = "nabt.recursive-source-bridge.v1"
LEAN_SCOPE = "structural_source_binding_and_conditional_interpretations"
ATOMIZATION_ID = "nabt.unicode-scalars.utf8-boundaries.v1"
SCOPE = "EXACT_SOURCE_TRANSPORT_WITH_EXPLICIT_GRAMMAR_OBLIGATIONS"
MAX_SOURCE_BYTES = 8192
MAX_REPORT_BYTES = 16 * 1024 * 1024
MAX_LABEL_BYTES = 96
MAX_TRANSPORT_NODES = 2048
MAX_PROBE_INPUT_BYTES = 1024 * 1024


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nabt import foundation

def wire(value):
    try:
        result = json.dumps(value, ensure_ascii=False, sort_keys=True,
                            separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise NabtError("INVALID_RECURSIVE_REPORT", "Use bounded strict JSON") from error
    if len(result) + 1 > MAX_REPORT_BYTES:
        raise resource_limit("Recursive report exceeds the serialized JSONL byte limit")
    return result


def _label(value, name):
    if type(value) is not str or not value:
        raise NabtError("INVALID_RECURSIVE_LABEL", name + " must be a nonempty string")
    try:
        raw = value.encode("utf-8")
    except UnicodeError as error:
        raise NabtError("INVALID_RECURSIVE_LABEL", "Labels must be valid UTF-8") from error
    if len(raw) > MAX_LABEL_BYTES:
        raise resource_limit("Recursive label exceeds its byte budget", field=name)
    return value


def _string_number(value):
    """An injective bounded string encoding, not a hash or linguistic class."""
    return int.from_bytes(b"\x01" + value.encode("utf-8"), "big")


def _identity(value):
    # The digest is a lookup/audit label. Acceptance always replays full data.
    return sha256(wire(value)).hexdigest()


def source_view(text, source_id="input", scope="default"):
    _label(source_id, "source_id")
    _label(scope, "scope")
    if type(text) is not str:
        raise NabtError("INVALID_RECURSIVE_SOURCE", "Source must be text")
    try:
        raw = text.encode("utf-8")
    except UnicodeError as error:
        raise NabtError("INVALID_RECURSIVE_SOURCE", "Source must be valid UTF-8") from error
    if len(raw) > MAX_SOURCE_BYTES:
        raise resource_limit("Recursive source exceeds its byte budget")
    foundation.validate_source(raw)
    boundaries = [0]
    for character in text:
        boundaries.append(boundaries[-1] + len(character.encode("utf-8")))
    digest = sha256(raw).hexdigest()
    return {
        "source_id": source_id, "source_sha256": digest, "scope": scope,
        "raw_text": text, "byte_length": len(raw), "atoms": list(text),
        "byte_boundaries": boundaries, "atomization": ATOMIZATION_ID,
        "normalization": "NONE",
        "lean_source": {"source_id": _string_number(source_id),
                        "revision": int(digest, 16),
                        "scope_id": _string_number(scope), "atomization_id": 1,
                        "atoms": list(text)},
    }


def _atom_span(source, byte_span):
    if (type(byte_span) is not dict or byte_span.get("source_id") != source["source_id"]
            or byte_span.get("source_sha256") != source["source_sha256"]):
        raise NabtError("FOREIGN_RECURSIVE_SPAN", "A span must refer to the exact original source")
    start = natural(byte_span.get("start"), "span.start")
    end = natural(byte_span.get("end"), "span.end")
    boundaries = source["byte_boundaries"]
    positions = {byte: index for index, byte in enumerate(boundaries)}
    if start >= end or start not in positions or end not in positions:
        raise NabtError("INVALID_RECURSIVE_SPAN", "Span endpoints must bound complete original UTF-8 scalars")
    raw = source["raw_text"].encode("utf-8")
    if byte_span.get("span_sha256") != sha256(raw[start:end]).hexdigest():
        raise NabtError("RECURSIVE_SPAN_BYTES_DIFFER", "Span bytes do not match the original source")
    origin = source["lean_source"]
    return {**{key: origin[key] for key in ("source_id", "revision", "scope_id", "atomization_id")},
            "start": positions[start], "stop": positions[end]}


def host_tree(source, start, stop):
    """Balanced PR14 proposal over EVERY atom in a contiguous source interval."""
    atoms = source["atoms"]
    natural(start, "host.start")
    natural(stop, "host.stop")
    if not 0 <= start < stop <= len(atoms):
        raise NabtError("INVALID_RECURSIVE_HOST", "Use a nonempty source interval")
    if stop - start > 256:
        raise resource_limit("A recursive host exceeds 256 scalar atoms")
    origin = source["lean_source"]
    if stop == start + 1:
        return {"op": "atom", "source": origin, "before": atoms[:start],
                "value": atoms[start], "after": atoms[stop:]}
    middle = (start + stop) // 2
    return {"op": "join", "tag": {"rule_id": 0, "reading_id": 0, "class_id": 0,
                                     "requirements": []},
            "left": host_tree(source, start, middle),
            "right": host_tree(source, middle, stop)}


def _shape_reading(source, candidate, pattern):
    host = _atom_span(source, candidate["stem_span"])
    boundary = None if candidate["boundary_span"] is None else _atom_span(source, candidate["boundary_span"])
    root = candidate["root"]
    tokens = pattern["tokens"]
    if len(tokens) != host["stop"] - host["start"] or len(root) != pattern["arity"]:
        raise NabtError("RECURSIVE_ALIGNMENT_MISMATCH", "Root arity, template and source host must agree")
    alignment = []
    fibers = [[] for _ in root]
    for position, (token, row) in enumerate(zip(tokens, candidate["alignment"], strict=True)):
        atom_span = _atom_span(source, row["span"])
        expected_position = host["start"] + position
        if (row["pattern_position"] != position or atom_span["start"] != expected_position
                or atom_span["stop"] != expected_position + 1):
            raise NabtError("RECURSIVE_ALIGNMENT_MISMATCH", "Every template position must retain its original scalar")
        expected = root[token] if type(token) is int else token
        if row["surface"] != expected or source["atoms"][expected_position] != expected:
            raise NabtError("RECURSIVE_ALIGNMENT_MISMATCH", "Template refill differs from original source")
        if type(token) is int:
            if row.get("type") != "radical" or row.get("root_index") != token:
                raise NabtError("RECURSIVE_ALIGNMENT_MISMATCH", "The radical occurrence belongs to another slot")
            origin = {"kind": "radical", "index": token}
            fibers[token].append(expected_position)
        else:
            if row.get("type") != "literal" or row.get("literal") != token:
                raise NabtError("RECURSIVE_ALIGNMENT_MISMATCH", "A literal template position was changed")
            origin = {"kind": "literal", "value": token}
        alignment.append({"pattern_position": position, "source_position": expected_position,
                          "origin": origin, "byte_span": deepcopy(row["span"]), "atom_span": atom_span})
    if not all(fibers):
        raise NabtError("INCOMPLETE_RECURSIVE_ROOT", "Every radical must occur in the complete template")
    result = {
        "reading_id": candidate["candidate_id"], "catalog_id": pattern["id"],
        "registry_id": EXPECTED_TABLE_SHA256, "root_alphabet": ALPHABET_ID,
        "root": list(root), "arity": len(root), "template": deepcopy(pattern),
        "alignment": alignment, "radical_fibers": fibers,
        "host": host, "boundary": boundary,
        "source_before": source["atoms"][:host["start"]],
        "source_after": source["atoms"][host["stop"]:],
        "host_tree": host_tree(source, host["start"], host["stop"]),
        "upstream_candidate": deepcopy(candidate),
        "section": None, "roles": [], "evidence_ids": [],
        "provenance": "source_reconstruction",
        "child_tree_authority": "NEW_ORDERED_SOURCE_TREE_NOT_RECOVERED_SYNTAX",
        "source_binding": "EXACT_ALL_POSITION_TEMPLATE_REPLAY",
        "linguistic_license": False, "attested_root": False,
        "unresolved": ["INDEPENDENT_LEXICAL_ROOT_WITNESS", "GRAMMAR_REALIZATION_CONTRACTS"],
    }
    result["node_id"] = _identity(result)
    return result


def _occurrence_for_span(report, byte_span):
    return [o for o in report["occurrences"]
            if o["span"]["start"] == byte_span["start"] and o["span"]["end"] == byte_span["end"]]


def _syntax_transport(source, report, morphology):
    """Retain all analyses; expose roles only through the reader's qualified set."""
    readings = {reading["reading_id"]: reading for occurrence in report["occurrences"]
                for reading in occurrence["readings"]}
    readings.update({r["reading_id"]: r for r in report["derived_readings"]})
    frames = []
    for clause in report["clauses"]:
        for analysis in clause["analyses"]:
            qualified = (clause["status"] == "LICENSED" and not analysis["rejected_candidate"]
                         and analysis["licensed_syntax"] and analysis["references_complete"])
            host = _atom_span(source, analysis["span"])
            children = []
            for reading_id in analysis["reading_ids"]:
                reading = readings.get(reading_id)
                if reading is None:
                    raise NabtError("MISSING_RECURSIVE_READING", "Analysis refers to an unavailable original reading")
                # Preserve reading identity and all correlated morphology alternatives;
                # matching a source extent does not choose a root or catalog family.
                candidate_spans = [a["span"] for a in analysis["assignments"] if a["reading_id"] == reading_id]
                candidates = []
                for span in candidate_spans:
                    for occurrence in _occurrence_for_span(morphology, span):
                        candidates.extend(c["candidate_id"] for c in occurrence["candidates"])
                children.append({"reading_id": reading_id, "reading": deepcopy(reading),
                                 "morphology_candidate_ids": list(dict.fromkeys(candidates)),
                                 "link_authority": "SAME_SOURCE_EXTENT_ONLY_NO_MORPHOLOGY_SELECTION"})
            roles = []
            for assignment in analysis["assignments"]:
                if not (qualified and assignment["activated"] and assignment["actual_role"] is not None):
                    continue
                target = _atom_span(source, assignment["span"])
                head = None if assignment["head_span"] is None else _atom_span(source, assignment["head_span"])
                roles.append({"role": assignment["actual_role"], "reading_id": assignment["reading_id"],
                              "target": target, "head": head,
                              "case": assignment.get("inflected_case") or assignment.get("local_case"),
                              "case_domain": assignment.get("case_domain"),
                              "upstream_assignment": deepcopy(assignment)})
            frame = {
                "clause_id": clause["clause_id"], "analysis_id": analysis["analysis_id"],
                "qualified_analysis": qualified, "host": host,
                "host_tree": host_tree(source, host["start"], host["stop"]),
                "section": analysis["frame"] if qualified else None,
                "roles": roles, "ordered_reading_children": children,
                "relations": deepcopy(analysis["relations"]),
                "references": deepcopy(analysis["references"]),
                "supports": deepcopy(analysis["supports"]),
                "upstream_analysis": deepcopy(analysis),
                "provenance": "source_reconstruction",
                "original_syntax_children_recovered": False,
                "unresolved": ["ORIGINAL_SYNTAX_CHILD_TREE_NOT_IN_UPSTREAM_REPORT",
                               "RECURSIVE_GRAMMAR_RULE_REALIZATION_CONTRACTS"],
                "authority": "REPLAYED_QUALIFIED_ASSIGNMENTS_WITH_NEW_SOURCE_TREE" if qualified
                             else "PRESERVED_UNQUALIFIED_ANALYSIS_NO_ACTUAL_ROLES",
            }
            frame["node_id"] = _identity(frame)
            frames.append(frame)
    return frames


def read_recursive_source(text, *, source_id="input", scope="default", profile="surface_v1",
                          lexical_model=None, context=None, with_discourse=False):
    foundation.require_foundation('tools.recursive_bridge.read_recursive_source')
    if type(with_discourse) is not bool:
        raise NabtError("INVALID_RECURSIVE_OPTION", "with_discourse must be Boolean")
    source = source_view(text, source_id, scope)
    morphology = read_derivation(text, source_id=source_id, scope=scope, profile=profile)
    patterns = {row["id"]: row for row in installed_registry()["patterns"]}
    candidates = [candidate for occurrence in morphology["occurrences"]
                  for candidate in occurrence["candidates"]]
    if len(candidates) > MAX_TRANSPORT_NODES:
        raise resource_limit("Too many source-bound morphology nodes")
    # Source and before/after contexts repeat at each leaf. Estimate BEFORE
    # constructing these trees, then enforce the actual serialized cap below.
    source_bytes = len(wire(source))
    estimate = source_bytes + 2 * len(wire(morphology)) + sum(
        4 * source_bytes * (len(candidate["alignment"]) + 1) + 16384
        for candidate in candidates)
    if estimate > MAX_REPORT_BYTES:
        raise resource_limit("Estimated recursive morphology transport exceeds its output budget")
    discourse = read_discourse(text, source_id=source_id, scope=scope,
                              lexical_model=lexical_model, context=context) if with_discourse else None
    if discourse is not None:
        analyses = [analysis for clause in discourse["clauses"] for analysis in clause["analyses"]]
        if len(candidates) + len(analyses) > MAX_TRANSPORT_NODES:
            raise resource_limit("Too many recursive source nodes")
        estimate += 8 * len(wire(discourse)) + sum(
            4 * source_bytes * (len(analysis["reading_ids"]) * 48 + 1) + 16384
            for analysis in analyses)
        if estimate > MAX_REPORT_BYTES:
            raise resource_limit("Estimated recursive discourse transport exceeds its output budget")
    nodes = [_shape_reading(source, candidate, patterns[candidate["pattern_id"]])
             for candidate in candidates]
    frames = [] if discourse is None else _syntax_transport(source, discourse, morphology)
    if len(nodes) + len(frames) > MAX_TRANSPORT_NODES:
        raise resource_limit("Too many recursive source nodes")
    # These are retained upstream records, not interpreted recursive gate
    # receipts. The complete replayed report supplies their numbered domain.
    evidence_records = []
    for frame in frames:
        frame["evidence_ids"] = []
        for position, support in enumerate(frame["supports"]):
            evidence_id = len(evidence_records) + 1
            evidence_records.append({"id": evidence_id, "analysis_id": frame["analysis_id"],
                                     "support_position": position, "support": deepcopy(support),
                                     "authority": "RETAINED_UPSTREAM_SUPPORT_NOT_RECURSIVE_GATE"})
            frame["evidence_ids"].append(evidence_id)
        frame["node_id"] = _identity({k: v for k, v in frame.items() if k != "node_id"})
    report = {"schema": LAW_ID, "scope": SCOPE, "source": source,
              "profile": profile, "with_discourse": with_discourse,
              "upstream_morphology": morphology, "morphology_nodes": nodes,
              "upstream_discourse": discourse, "syntax_frames": frames,
              "evidence_records": evidence_records,
              "evidence_number_domain": "report_local_upstream_supports.v1",
              "status": "SOURCE_TRANSPORT_COMPLETE",
              "grammar_certified": False, "acquisition_measured": False,
              "lexical_root_from_shape": False, "world_truth": "NOT_ESTABLISHED",
              "identity_authority": "FULL_REPLAY_NOT_DIGEST_ALONE"}
    report["report_id"] = _identity(report)
    wire(report)
    return report


def verify_recursive_source(report, *, text, source_id="input", scope="default",
                            profile="surface_v1", lexical_model=None, context=None,
                            with_discourse=False):
    """External source/context arguments are mandatory authority, not report flags."""
    foundation.require_foundation('tools.recursive_bridge.verify_recursive_source')
    try:
        fresh = read_recursive_source(text, source_id=source_id, scope=scope, profile=profile,
                                      lexical_model=lexical_model, context=context,
                                      with_discourse=with_discourse)
        if wire(report) != wire(fresh):
            return {"valid": False, "status": "REJECT", "code": "RECURSIVE_SOURCE_REPLAY_MISMATCH"}
        return {"valid": True, "status": "VERIFIED", "report_id": fresh["report_id"],
                "authority": SCOPE, "grammar_certified": False}
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, **error.as_dict()}
        return {"valid": False, "status": "REJECT", "code": "INVALID_RECURSIVE_SOURCE_REPORT"}


def _metadata(report, host, reading_id, *, morphology=None, section=None, roles=(),
              evidence_ids=(), unresolved=()):
    source = report["source"]
    return {"registry_id": LAW_ID, "reading_id": reading_id,
            "source": source["lean_source"], "host": host,
            "host_tree": host_tree(source, host["start"], host["stop"]),
            "morphology": morphology, "section": section, "roles": list(roles),
            "evidence_ids": list(evidence_ids), "required": [], "provenance": "source_reconstruction",
            "unresolved": list(unresolved)}


def _request(report, node):
    result = {"op": "bridge_assess", "node": node,
              "inventory": [report["source"]["lean_source"]], "interpreted": [], "offered": []}
    if len(wire(result)) + 1 > MAX_PROBE_INPUT_BYTES:
        raise resource_limit("Expanded recursive source request exceeds the Lean input budget")
    return result


def _projection_preflight(report, host, *, frame=False):
    if len(report["source"]["atoms"]) > 256:
        raise resource_limit("Lean source projection exceeds 256 scalar atoms")
    length = host["stop"] - host["start"]
    if 2 * length - 1 > 127 or (frame and 2 * length > 127):
        raise resource_limit("Lean source projection exceeds 127 nodes before construction")


def morphology_request(text, index=0, **options):
    """Build a source-only Lean request from the freshly replayed selected reading.

    The selector identifies a proposal; it does not certify that alternative
    readings were refuted. No interpreted linguistic receipts are synthesized.
    """
    report = read_recursive_source(text, **options)
    return _morphology_request_from_report(report, index)


def _morphology_request_from_report(report, index):
    natural(index, "reading index")
    if index >= len(report["morphology_nodes"]):
        raise NabtError("RECURSIVE_READING_UNAVAILABLE", "No reading at this index in the replayed source", status="DEFER")
    item = report["morphology_nodes"][index]
    _projection_preflight(report, item["host"])
    pattern = item["template"]
    morphology = {
        "catalog_id": item["catalog_id"], "registry_id": item["registry_id"],
        "reading_id": item["reading_id"],
        "reading": {"arity": item["arity"], "root": item["root"],
                    "pattern": [{"slot": t} if type(t) is int else {"literal": t}
                                for t in pattern["tokens"]]},
        "alignment": [{k: a[k] for k in ("pattern_position", "source_position", "origin")}
                      for a in item["alignment"]],
    }
    metadata = _metadata(report, item["host"], item["reading_id"], morphology=morphology,
                         unresolved=item["unresolved"])
    seed = {"kind": "root" + str(item["arity"]), "radicals": [ord(c) for c in item["root"]]}
    child = {"op": "leaf", "seed": seed, "metadata": deepcopy(metadata)}
    # The index is scoped to the complete, pinned catalog. Both its semantic
    # catalog ID and exact tokens remain in the fully bound metadata.
    catalog = installed_registry()["patterns"]
    rule = next(i for i, p in enumerate(catalog) if p["id"] == item["catalog_id"])
    node = {"op": "unary", "rule": rule, "metadata": metadata, "child": child}
    return _request(report, node)


def _source_spine(report, host, reading_id):
    metadata = _metadata(report, host, reading_id,
                         unresolved=["SOURCE_CONCATENATION_NOT_SYNTACTIC_ATTACHMENT"])
    if host["stop"] == host["start"] + 1:
        return {"op": "leaf", "seed": {"kind": "lexical", "entry": host["start"]},
                "metadata": metadata}
    middle = (host["start"] + host["stop"]) // 2
    return {"op": "binary", "rule": 0, "metadata": metadata,
            "left": _source_spine(report, {**host, "stop": middle}, reading_id),
            "right": _source_spine(report, {**host, "start": middle}, reading_id)}


def frame_request(text, index=0, **options):
    """Retain qualified roles on a NEW audit source tree, not an invented parse."""
    options = {**options, "with_discourse": True}
    report = read_recursive_source(text, **options)
    return _frame_request_from_report(report, index)


def _frame_request_from_report(report, index):
    natural(index, "frame index")
    if index >= len(report["syntax_frames"]):
        raise NabtError("RECURSIVE_FRAME_UNAVAILABLE", "No frame at this index in the replayed source", status="DEFER")
    frame = report["syntax_frames"][index]
    _projection_preflight(report, frame["host"], frame=True)
    roles = [{k: role[k] for k in ("role", "reading_id", "target", "head", "case", "case_domain")}
             for role in frame["roles"]]
    metadata = _metadata(report, frame["host"], frame["analysis_id"],
                         section="clause" if frame["qualified_analysis"] else None,
                         roles=roles, evidence_ids=frame["evidence_ids"], unresolved=frame["unresolved"])
    # Exact frame identity is retained as an injective UTF-8 number in this
    # transport law. The coarse Core section does not replace that identity.
    rule = _string_number(_label(frame["upstream_analysis"]["frame"], "frame"))
    node = {"op": "unary", "rule": rule, "metadata": metadata,
            "child": _source_spine(report, frame["host"], frame["analysis_id"])}
    return _request(report, node)


def assess_recursive_source(text, index=0, *, kind="morphology", probe=None, **options):
    """Return the complete transport beside its explicitly limited Lean projection.

    Report-local evidence IDs are interpretable only inside this complete
    envelope. The projection's source spine does not recover old parse children.
    """
    foundation.require_foundation('tools.recursive_bridge.assess_recursive_source')
    if kind not in ("morphology", "frame"):
        raise NabtError("INVALID_RECURSIVE_KIND", "Use morphology or frame")
    natural(index, "proposal index")
    if kind == "frame":
        options = {**options, "with_discourse": True}
    report = read_recursive_source(text, **options)
    builder = _morphology_request_from_report if kind == "morphology" else _frame_request_from_report
    request = builder(report, index)
    assessment = check_with_lean(request, probe=probe)
    envelope = {
        "schema": ASSESSMENT_ID, "kind": kind, "proposal_index": index,
        "evidence_namespace": {"transport_schema": LAW_ID, "report_id": report["report_id"],
                               "number_domain": report["evidence_number_domain"]},
        "transport": report, "request": request, "assessment": assessment,
        "projection_scope": "TYPED_SOURCE_PROJECTION_FULL_UPSTREAM_REPORT_RETAINED_ALONGSIDE",
        "grammar_certified": False, "acquisition_measured": False,
    }
    wire(envelope)
    return envelope


def verify_recursive_assessment(envelope, *, text, index=0, kind="morphology", probe=None, **options):
    """Replay full transport, rebuild its projection, and execute Lean again."""
    foundation.require_foundation('tools.recursive_bridge.verify_recursive_assessment')
    try:
        fresh = assess_recursive_source(text, index, kind=kind, probe=probe, **options)
        if wire(envelope) != wire(fresh):
            return {"valid": False, "status": "REJECT", "code": "RECURSIVE_ASSESSMENT_REPLAY_MISMATCH"}
        return {"valid": True, "status": "VERIFIED", "report_id": fresh["transport"]["report_id"],
                "grammar_certified": False, "assessment_status": fresh["assessment"]["status"],
                "verdict": fresh["assessment"].get("verdict")}
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, **error.as_dict()}
        return {"valid": False, "status": "REJECT", "code": "INVALID_RECURSIVE_ASSESSMENT"}


def check_with_lean(request, *, probe=None):
    """Execute the bounded repository probe; no shell or external runtime import."""
    foundation.require_foundation('tools.recursive_bridge.check_with_lean')
    executable = Path(probe or os.environ.get("NABT_RECURSIVE_BRIDGE_PROBE", "") or
                      ROOT / "formal/.lake/build/bin/recursiveBridgeProbe")
    if not executable.is_file():
        raise NabtError("RECURSIVE_PROBE_UNAVAILABLE", "Build recursiveBridgeProbe or supply its exact path", status="DEFER")
    encoded = wire(request) + b"\n"
    if len(encoded) > MAX_PROBE_INPUT_BYTES:
        raise resource_limit("Recursive Lean request exceeds 1 MiB")
    try:
        result = subprocess.run([str(executable)], input=encoded, capture_output=True,
                                check=False, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise NabtError("RECURSIVE_PROBE_FAILED", "Lean probe did not complete", status="DEFER") from error
    if result.returncode or result.stderr or len(result.stdout) > MAX_REPORT_BYTES:
        raise NabtError("RECURSIVE_PROBE_FAILED", "Lean probe output failed its execution envelope", status="DEFER")
    try:
        response = _strict_json(result.stdout)
        if (type(response) is not dict or response.get("law_id") != LEAN_LAW_ID
                or response.get("scope") != LEAN_SCOPE or response.get("conditional") is not True
                or response.get("grammar_certified") is not False
                or response.get("acquisition_measured") is not False):
            raise ValueError("wrong recursive response contract")
        if response.get("status") == "ERROR":
            if (not isinstance(response.get("error"), str)
                    or response.get("search_complete") is not False
                    or response.get("linguistic_rejection") is not False):
                raise ValueError("invalid recursive failure contract")
        elif response.get("status") == "OK" and response.get("op") == request.get("op"):
            if request["op"] == "bridge_assess" and wire(response.get("node")) != wire(request.get("node")):
                raise ValueError("recursive bridge returned another annotated node")
            if request["op"] == "core_number" and (
                    wire(response.get("tree")) != wire(request.get("tree"))
                    or response.get("registry_id") != request.get("registry_id")):
                raise ValueError("recursive number returned another tree or registry")
            if request["op"] == "core_enumerate" and (
                    response.get("registry_id") != request.get("registry_id")
                    or wire(response.get("height")) != wire(request.get("height"))):
                raise ValueError("recursive enumeration returned another registry or height")
        else:
            raise ValueError("wrong recursive response operation")
        return response
    except (ValueError, TypeError, AttributeError, UnicodeError, RecursionError) as error:
        raise NabtError("RECURSIVE_PROBE_FAILED", "Lean probe did not return one JSON response", status="DEFER") from error


def _strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    parsed = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                        parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    wire(parsed)  # Reject escaped unpaired surrogates as well as malformed UTF-8.
    return parsed


def _read_bounded(path, maximum):
    with Path(path).open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise resource_limit("File exceeds its recursive input byte budget", maximum_bytes=maximum)
    return raw


def _load_json(path):
    return _strict_json(_read_bounded(path, MAX_REPORT_BYTES))


def main(argv=None):
    foundation.require_foundation('tools.recursive_bridge.main')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("read", "verify", "lean-morphology", "lean-frame"))
    parser.add_argument("source")
    parser.add_argument("--report")
    parser.add_argument("--source-id", default="input")
    parser.add_argument("--scope", default="default")
    parser.add_argument("--profile", default="surface_v1")
    parser.add_argument("--discourse", action="store_true")
    parser.add_argument("--qac")
    parser.add_argument("--context")
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--kind", choices=("morphology", "frame"), default="morphology")
    parser.add_argument("--probe")
    args = parser.parse_args(argv)
    try:
        raw = _read_bounded(args.source, MAX_SOURCE_BYTES)
        text = raw.decode("utf-8")
        model = None
        if args.qac:
            from nabt.corpus_evidence import MAX_CORPUS_BYTES, learn_qac_lexicon
            model = learn_qac_lexicon(_read_bounded(args.qac, MAX_CORPUS_BYTES))
        context = _load_json(args.context) if args.context else None
        options = dict(source_id=args.source_id, scope=args.scope, profile=args.profile,
                       lexical_model=model, context=context, with_discourse=args.discourse)
        if args.operation == "read":
            result = read_recursive_source(text, **options)
        elif args.operation == "verify":
            if not args.report:
                parser.error("verify requires --report")
            previous = _load_json(args.report)
            if type(previous) is dict and previous.get("schema") == ASSESSMENT_ID:
                result = verify_recursive_assessment(previous, text=text, index=args.index,
                                                     kind=args.kind, probe=args.probe, **options)
            else:
                result = verify_recursive_source(previous, text=text, **options)
        else:
            kind = "morphology" if args.operation == "lean-morphology" else "frame"
            result = assess_recursive_source(text, args.index, kind=kind, probe=args.probe, **options)
        sys.stdout.buffer.write(wire(result) + b"\n")
        if args.operation.startswith("lean-"):
            assessment = result["assessment"]
            return 3 if assessment.get("error") == "RESOURCE_LIMIT" else 2 if assessment.get("status") == "ERROR" else 0
        return 0 if args.operation == "read" or result["valid"] else 3 if result["status"] == "DEFER" else 2
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError) as error:
        failure = error.as_dict() if isinstance(error, NabtError) else {
            "status": "REJECT", "code": "INVALID_RECURSIVE_INPUT", "message": "Input could not be replayed"}
        sys.stdout.buffer.write(wire(failure) + b"\n")
        return 3 if failure["status"] == "DEFER" else 2


if __name__ == "__main__":
    raise SystemExit(main())
