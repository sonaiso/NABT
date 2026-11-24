"""Replay a batch of dictionary queries against two installed source owners."""
from collections import Counter
from copy import deepcopy

from nabt.source_lexicon import SourceIdentityError, SourceLexicon, source_registry
from tools import evidence_lifecycle_v1 as wire
from tools.grammar_catalog import dictionary_reading as mukhtar

SCHEMA = "ntl.dictionary-deposit.v1"
RESULT = "ntl.dictionary-deposit-result.v1"
SOURCES = ("mukhtar", "maqayis")
MAX_QUERIES = 64
MAX_BLOCK_BYTES = 16384


def _reader(source):
    if source == "mukhtar":
        _, records = mukhtar.resources()
        lemmas = {record["lemma"] for record in records}

        def lookup(term):
            selected = mukhtar.indices_for(term, lemmas)
            return [deepcopy(mukhtar.mukhtar_reading(record, None)) for record in records
                    if record["lemma"] in selected]

        return lookup, {"work": "مختار الصحاح", "sha256": mukhtar.SOURCE_SHA,
                        "alignment_sha256": mukhtar.MEMBERS_SHA,
                        "path": mukhtar.SOURCE.relative_to(mukhtar.ROOT).as_posix(),
                        "evidence_kind": "SOURCE_BOUND_GLOSS"}

    spec = source_registry()["sources"]["maqayis"]
    index = SourceLexicon.load(source, mukhtar.ROOT / spec["checkout_default"])

    def lookup(term):
        return index.lookup_exact(term)["alternatives"]

    return lookup, {"work": spec["title"], "sha256": spec["sha256"],
                    "pinned_url": spec["pinned_url"], "path": spec["checkout_default"],
                    "evidence_kind": "EXACT_HEADING_BLOCK"}


def run(lesson):
    wire._fields(lesson, ("schema", "queries", "withdraw_sources"), "dictionary deposit")
    if lesson["schema"] != SCHEMA:
        raise ValueError("Unknown dictionary deposit schema")
    queries, withdrawn = lesson["queries"], lesson["withdraw_sources"]
    wire._array(queries, "queries", MAX_QUERIES)
    wire._array(withdrawn, "withdraw_sources", len(SOURCES))
    if not queries or any(source not in SOURCES for source in withdrawn) or len(set(withdrawn)) != len(withdrawn):
        raise ValueError("Supply queries and a unique subset of the installed sources to withdraw")

    rows, readers, manifest = [], {}, {}
    failures = {}
    for position, query in enumerate(queries):
        row = {"position": position, "status": "INVALID_QUERY", "evidence": []}
        rows.append(row)
        if type(query) is not dict or set(query) != {"source", "term"}:
            row["reason"] = "EXPECTED_SOURCE_AND_TERM"
            continue
        source, term = query["source"], query["term"]
        if (source not in SOURCES or type(term) is not str or not term.strip()
                or len(term) > 128 or any(ord(c) < 32 for c in term)):
            row["reason"] = "UNKNOWN_SOURCE_OR_INVALID_TERM"
            continue
        row.update(source=source, term=term)
        if source in withdrawn:
            row["status"] = "SOURCE_WITHDRAWN"
            continue
        if source not in readers and source not in failures:
            try:
                readers[source], manifest[source] = _reader(source)
            except OSError:
                failures[source] = "SOURCE_UNAVAILABLE"
            except (SourceIdentityError, ValueError):
                failures[source] = "SOURCE_VERIFICATION_FAILED"
        if source in failures:
            row["status"] = failures[source]
            continue
        matches = readers[source](term)
        # Keep duplicate headings and alternative senses together. Never drop a
        # branch to fit the output budget or count a partial row as admitted.
        if source == "maqayis" and sum(m["end_byte"] - m["start_byte"] for m in matches) > MAX_BLOCK_BYTES:
            row.update(status="ROW_RESOURCE_LIMIT", reason="COMBINED_BLOCK_BYTES", matched_blocks=len(matches))
            continue
        row.update(status="SOURCE_ATTESTED" if matches else "NOT_INDEXED",
                   evidence=matches)

    return {"schema": RESULT, "status": "EVALUATED", "execution_measured": True,
            "request": deepcopy(lesson), "sources": manifest, "source_failures": failures,
            "rows": rows, "counts": dict(sorted(Counter(r["status"] for r in rows).items())),
            "total_queries": len(queries), "authority": "SOURCE_TEXT_TESTIMONY_ONLY",
            "scope": "INSTALLED_MUKHTAR_ALIGNMENTS_AND_EXACT_MAQAYIS_HEADINGS",
            "world_truth_established": False, "intended_sense_established": False,
            "semantic_rank_promoted": False, "neural_training_performed": False}
