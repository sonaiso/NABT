"""Count declared candidate identities; do not infer or verify their meanings."""
from __future__ import annotations

import math

from .registry import (enum_value, list_value, natural, nonempty_string, object_value,
                       require, sha)

SCHEMA = "nabt.candidate-ledger.v1"
FRAME_KEYS = {
    "domain_id", "element_type", "equivalence_version", "unit", "source_binding",
    "law_version", "grammar_version", "lexicon_version", "convention",
    "context_version", "evidence_revision", "enumeration_bounds",
}


def measure_candidates(payload):
    """Return exact descriptive counts over the supplied finite list.

    IDs must be distinct; equivalence of IDs to semantic readings is declared,
    not checked here. Missing licensing evidence must remain pending upstream.
    Neither a declared enumeration status nor a declared licensed/refuted state
    grants authority. The entropy is of this list, never of all Arabic readings.
    """
    object_value(payload, "candidate ledger")
    require(set(payload) == {"schema", "frame", "enumeration_status", "candidates"},
            "candidate ledger: unexpected or missing fields")
    require(payload["schema"] == SCHEMA, "unsupported candidate-ledger schema")
    frame = object_value(payload["frame"], "frame")
    require(set(frame) == FRAME_KEYS, "frame: unexpected or missing identity fields")
    for key in FRAME_KEYS - {"source_binding", "enumeration_bounds"}:
        nonempty_string(frame[key], f"frame.{key}")
    source = object_value(frame["source_binding"], "source_binding")
    require(set(source) == {"source_id", "sha256", "span_bytes"}, "source_binding: wrong fields")
    nonempty_string(source["source_id"], "source_binding.source_id")
    sha(source["sha256"], "source_binding.sha256", 64)
    span = list_value(source["span_bytes"], "source_binding.span_bytes")
    require(len(span) == 2, "source span needs start/end byte offsets")
    start, end = [natural(value, "source span") for value in span]
    require(start <= end, "source span end precedes start")
    bounds = object_value(frame["enumeration_bounds"], "enumeration_bounds")
    require(bool(bounds), "enumeration bounds must be explicit")
    for key, value in bounds.items():
        nonempty_string(key, "enumeration bound name")
        natural(value, f"enumeration bound {key}")
    status = payload["enumeration_status"]
    enum_value(status, {"DECLARED_COMPLETE", "PARTIAL", "RESOURCE_LIMIT"}, "enumeration_status")
    rows = list_value(payload["candidates"], "candidates")
    identities = set()
    counts = {"licensed": 0, "pending": 0, "refuted": 0}
    remaining = []
    for row in rows:
        object_value(row, "candidate")
        require(set(row) == {"id", "state"}, "candidate: only id and declared state are accepted")
        identity = nonempty_string(row["id"], "candidate.id")
        require(identity not in identities, f"duplicate candidate id: {identity}")
        identities.add(identity)
        require(type(row["state"]) is str and row["state"] in counts,
                "unknown declared candidate state")
        counts[row["state"]] += 1
        if row["state"] != "refuted":
            remaining.append(identity)
    total = len(remaining)
    return {
        "schema": "nabt.candidate-ledger-measurement.v1",
        "authority": "COUNTED_SUPPLIED_LEDGER", "semantic_authority": "NONE",
        "frame": frame, "declared_enumeration_status": status,
        "linguistic_completeness_verified": False, "candidate_states_verified": False,
        "source_binding_verified": False, "identity_contract_verified": False,
        "count_mode": "EXACT_FOR_SUPPLIED_LEDGER",
        "ledger_counts": {"total": len(rows), **counts, "remaining": total},
        "remaining_ids": remaining,
        "ledger_hartley_bits": math.log2(total) if total else None,
        "null_reason": "EMPTY_REMAINING_LEDGER" if not total else None,
        "probabilities_used": False,
        "interpretation": "descriptive ledger cardinality; not likelihood, language completeness or world truth",
    }
