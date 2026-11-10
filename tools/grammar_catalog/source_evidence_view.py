"""Lossless display of the existing source owner's facts and native closure.

This module selects witnesses; it never infers an atom or an application verdict.
The complete owner receipt remains authoritative and is replayed by the gateway.
"""
from copy import deepcopy

from tools import verified_reading as ground


def ledger(owner):
    result = []
    for document in owner["acquisition"]:
        for fact in document["facts"]:
            span = fact["span"]
            text = document["raw_text"].encode()[span["start"]:span["end"]].decode()
            atom = fact["atom"]
            result.append({"source_id": document["source_id"], "source_sha256": document["source_sha256"],
                "span": deepcopy(span), "text": text, "component_spans": deepcopy(fact["component_spans"]),
                "atom": {"predicate": atom["predicate"], "arguments": atom["args"], "positive": atom["positive"]}})
    return result


def premises(atoms, source_ledger, ready, certificate):
    """Project signed, clean and opposing evidence without collapsing unknowns."""
    known = {ground.key(a) for a in certificate["known"]}
    clean = {ground.key(a) for a in certificate["clean_known"]}
    rows = []
    for atom in atoms:
        key = ground.key(atom)
        opposite = ground.opposite(key)
        rows.append({"atom": deepcopy(atom),
            "present_in_native_closure": key in known, "present_in_clean_closure": key in clean,
            "opposite_in_native_closure": opposite in known,
            "source_witnesses": [i for i, row in enumerate(source_ledger)
                if row["source_id"] in ready and ground.key(row["atom"]) == key],
            "opposing_source_witnesses": [i for i, row in enumerate(source_ledger)
                if row["source_id"] in ready and ground.key(row["atom"]) == opposite]})
    return rows
