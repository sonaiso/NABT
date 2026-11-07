"""Reviewed-by-author occurrence annotations, not independently adjudicated facts."""
from hashlib import sha256
import json
from pathlib import Path

from tools.evidence_lifecycle_v1 import wire
from tools.grammar_catalog.operations import exact_terms
from . import contextual_alignment as runtime

CORPUS = runtime.DIRECTORY / "corpus.json"


def dataset(path=CORPUS):
    data = json.loads(Path(path).read_text())
    if data.get("schema") != "nabt.contextual-alignment-corpus.v1":
        raise ValueError("Unknown occurrence corpus")
    original = json.loads((runtime.ROOT / "evidence/lexical_denotation/catalog.json").read_text())
    ids = {s["id"] for s in original["senses"]}
    splits = {name:[] for name in ("train","validation","test")}
    seen_texts, seen_ids, groups = set(), set(), {}
    for row in data["rows"]:
        if (row["split"] not in splits or row["id"] in seen_ids or row["text"] in seen_texts
                or row["provenance"] != "AUTHORED_CONTEXT_ANNOTATION_NOT_INDEPENDENT_ADJUDICATION"):
            raise ValueError("Corpus split, duplicate or provenance violation")
        runtime.validate_request({"text":row["text"]})
        if row["group"] in groups and groups[row["group"]] != row["split"]:
            raise ValueError("Context group leaks across splits")
        groups[row["group"]] = row["split"]
        terms = {tuple(r["codepoint_span"]):r for r in exact_terms(row["text"])}
        seen_spans=set()
        for annotation in row["annotations"]:
            span=tuple(annotation["codepoint_span"])
            if (span in seen_spans or span not in terms or not annotation["concept_ids"]
                    or len(set(annotation["concept_ids"])) != len(annotation["concept_ids"])
                    or not set(annotation["concept_ids"]) <= ids):
                raise ValueError("Invalid occurrence annotation")
            if annotation["surface"] != terms[span]["surface"] or annotation["utf8_span"] != terms[span]["utf8_span"]:
                raise ValueError("Gold occurrence differs from original UTF-8")
            seen_spans.add(span)
        splits[row["split"]].append(row)
        seen_texts.add(row["text"]);seen_ids.add(row["id"])
    if set(ids) != {i for r in splits["train"] for a in r["annotations"] for i in a["concept_ids"]}:
        raise ValueError("Training does not cover original definition IDs")
    if any(not rows for rows in splits.values()):
        raise ValueError("Missing held-out partition")
    return splits


def token_rows(rows):
    output=[]
    for row in rows:
        labels={tuple(a["codepoint_span"]):a["concept_ids"] for a in row["annotations"]}
        for term in exact_terms(row["text"]):
            output.append({"id":row["id"],"text":row["text"],"group":row["group"],
                           "category":row["category"],**term,
                           "gold":labels.get(tuple(term["codepoint_span"]),[runtime.NULL])})
    return output


def digest(rows):
    return sha256(wire(rows).encode()).hexdigest()
