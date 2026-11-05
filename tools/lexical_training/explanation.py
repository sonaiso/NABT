"""Exact attribution and OntoLex views of the installed lexical learner.

The deletion game measures neural scores. Owner receipts remain the evidence
for linguistic judgments. Dictionary indexes without a witnessed headword
retain their original interpretation and are not promoted to lexical entries.
"""
from __future__ import annotations

from math import comb
from pathlib import Path
import re
from urllib.parse import quote

import numpy as np

from tools import attested_lexical_loader as loader
from tools import lexical_testimony as testimony
from . import acquisition
from .data import normalize
from .senses import encode, forward

SCHEMA = "nabt.lexical-explanation.v1"
MAX_GROUPS = 8
ARABIC = re.compile("[ء-غف-ي]")
CONTEXT = {
    "ontolex": "http://www.w3.org/ns/lemon/ontolex#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "prov": "http://www.w3.org/ns/prov#",
    "nabt": "https://github.com/sonaiso/NABT/vocab/lexical-explanation#",
}


def _id(kind, key):
    return "urn:nabt:lexical-explanation:" + kind + ":" + quote(key, safe="")


def dictionary_graph():
    """Export the pinned interpretation and alignment ledgers without merging senses."""
    cat = acquisition.catalogue()
    matrix, matrix_sha = loader._installed_matrix()
    aligned = {row["id"]: row for row in matrix["entries"]}
    nodes, entries, unresolved = [], {}, []
    for sense in cat["senses"]:
        row = aligned[sense["id"]]
        if row["dictionary_citation"] != sense["citation"] or row["components"] != sense["components"]:
            raise ValueError("Dictionary and headword alignment disagree")
        sid = _id("sense", sense["id"])
        concept = _id("concept", sense["id"])
        source = _id("source", acquisition.digest(acquisition.wire(sense["citation"])))
        headword = row["source_headword"]
        sense_node = {
            "@id": sid,
            "@type": "nabt:DictionaryInterpretation",
            "nabt:record": {"@value": sense, "@type": "@json"},
            "nabt:concept": {"@id": concept},
            "prov:wasDerivedFrom": {"@id": source},
        }
        if headword:
            if headword not in sense["citation"]["quotation"]:
                raise ValueError("Headword has no witness in its quotation")
            key = acquisition.digest(acquisition.wire([
                sense["citation"]["work"], sense["citation"]["revision"],
                sense["root"], headword,
            ]))
            entry, form = _id("entry", key), _id("form", key)
            if entry not in entries:
                entries[entry] = {
                    "@id": entry, "@type": "ontolex:LexicalEntry",
                    "ontolex:canonicalForm": {"@id": form}, "ontolex:sense": [],
                    "nabt:dictionaryIndex": sense["root"],
                }
                nodes.append({"@id": form, "@type": "ontolex:Form",
                              "ontolex:writtenRep": {"@value": headword, "@language": "ar"}})
            entries[entry]["ontolex:sense"].append({"@id": sid})
            sense_node.update({"@type": ["nabt:DictionaryInterpretation", "ontolex:LexicalSense"],
                               "ontolex:isSenseOf": {"@id": entry},
                               "ontolex:isLexicalizedSenseOf": {"@id": concept}})
        else:
            unresolved.append(sense["id"])
        nodes.extend([
            sense_node,
            {"@id": concept, "@type": "ontolex:LexicalConcept",
             "nabt:components": {"@value": sense["components"], "@type": "@json"},
             "nabt:interpretationStatus": sense["interpretation_status"]},
            {"@id": source, "@type": "prov:Entity",
             "nabt:receipt": {"@value": testimony._citation(sense["citation"], testimony.ROOT),
                              "@type": "@json"}},
        ])
    # A source may support more than one sense; retain one RDF node per identity.
    unique = {node["@id"]: node for node in nodes + list(entries.values())}
    return {"@context": dict(CONTEXT), "@graph": list(unique.values()),
            "nabt:catalogueSha256": testimony.CATALOG_SHA,
            "nabt:alignmentSha256": matrix_sha,
            "nabt:unresolvedLexicalEntries": unresolved,
            "nabt:necessities": {"@value": cat["necessities"], "@type": "@json"},
            "nabt:authority": "INSTALLED_INTERPRETATION_EXPORT",
            "nabt:worldTruthEstablished": False}


def score_attribution(text, directory):
    """All coalition outputs and all labels, with whole written words as groups.

    Clitics and combining marks stay attached to their written word. Deletion
    samples probe the scorer, without claiming they are licensed utterances.
    The empty-Arabic baseline is the zero feature vector of this MLP.
    """
    full = encode([text])  # Use the existing input contract before model I/O.
    groups = [match for match in re.finditer(r"\S+", text)
              if ARABIC.search(normalize(match[0]))]
    count = len(groups)
    if count > MAX_GROUPS:
        raise ValueError("Exact explanation supports at most eight written Arabic groups")
    models, meta, _ = acquisition.load_model(directory)
    views = []
    for mask in range(1 << count):
        chunks, position = [], 0
        for index, group in enumerate(groups):
            chunks.append(text[position:group.start()])
            chunks.append(group[0] if mask & (1 << index) else " ")
            position = group.end()
        chunks.append(text[position:])
        views.append("".join(chunks))
    vectors = np.zeros((len(views), full.shape[1]), dtype=np.float64)
    populated = [i for i, view in enumerate(views) if ARABIC.search(normalize(view))]
    vectors[populated] = encode([views[i] for i in populated])
    if not np.array_equal(vectors[-1], full[0]):
        raise ValueError("Explanation changed the original input representation")
    heads = {}
    for head, model in models.items():
        values = forward(model, vectors)
        contributions = np.zeros((count, values.shape[1]), dtype=np.float64)
        for index in range(count):
            for mask in range(1 << count):
                if not mask & (1 << index):
                    weight = 1 / (count * comb(count - 1, mask.bit_count()))
                    contributions[index] += weight * (values[mask | (1 << index)] - values[mask])
        residual = values[-1] - values[0] - contributions.sum(axis=0)
        if not np.isfinite(values).all() or np.max(np.abs(residual)) > 1e-10:
            raise ValueError("Attribution failed the additive accounting check")
        heads[head] = {"labels": meta["labels"][head], "baseline": values[0].tolist(),
                       "score": values[-1].tolist(), "contributions": contributions.tolist(),
                       "coalition_scores": values.tolist(), "residual": residual.tolist()}
    return {"schema": "nabt.lexical-score-attribution.v1", "authority": "SCORE_ACCOUNTING",
            "game": "WRITTEN_ARABIC_WORD_DELETION_ZERO_FEATURE_BASELINE",
            "model_sha256": meta["weights_sha256"], "features": meta["features"],
            "groups": [{"text": g[0], "chars": [g.start(), g.end()],
                        "bytes": [len(text[:g.start()].encode()), len(text[:g.end()].encode())]}
                       for g in groups],
            "evaluations": len(views), "heads": heads,
            "masked_texts_linguistically_licensed": False,
            "score_is_calibrated_probability": False,
            "linguistic_interpretation_from_attribution": False}


def _identity(directory):
    paths = [Path(directory) / name for name in ("model.json", "weights.npz")]
    paths += [Path(__file__), Path(acquisition.__file__), loader.MATRIX_PATH,
              Path(loader.__file__), Path(testimony.__file__),
              testimony.ROOT / testimony.CATALOG]
    paths += [Path(__file__).with_name(name) for name in ("senses.py", "data.py", "features.py")]
    identities = []
    for path in paths:
        with path.open("rb") as stream:
            raw = stream.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("Explanation input identity byte limit")
        identities.append(acquisition.digest(raw))
    return identities


def explain(text, directory, *, profile_id=None):
    """One existing connection, its learned scores, and its source-linked graph."""
    # The bound is checked before the more expensive native connection.
    before = _identity(directory)
    attribution = score_attribution(text, directory)
    connection = acquisition.connect(text, directory, profile_id=profile_id)
    graph = dictionary_graph()
    if before != _identity(directory):
        raise ValueError("Explanation inputs changed during execution")
    for head, rows in connection["proposal"]["ranking"].items():
        expected = dict(zip(attribution["heads"][head]["labels"],
                            attribution["heads"][head]["score"]))
        if any(abs(expected[row["id"]] - row["score"]) > 1e-12 for row in rows):
            raise ValueError("Attribution and proposal scores differ")
    return {"schema": SCHEMA, "authority": "CONNECTED_OWNER_REPORTS_WITH_SCORE_EXPLANATION",
            "input": text, "identity": before, "connection": connection,
            "score_explanation": attribution, "dictionary_graph": graph,
            "matrix_paths": {"dall": "connection.before_composition.owner_reports",
                             "madlul": "connection.before_composition.denotatum",
                             "dall_madlul": "connection.indication_application"},
            "accepted_sense_from_score": False,
            "semantic_accuracy_improvement_measured": False}


def verify(report, *, text, directory, profile_id=None):
    fresh = explain(text, directory, profile_id=profile_id)
    matches = acquisition.wire(report) == acquisition.wire(fresh)
    checked = acquisition.connection_checks_completed(fresh["connection"])
    return {"valid": matches and checked, "replay_matches": matches,
            "owner_checks_completed": checked,
            "authority": "FRESH_OWNER_AND_MODEL_REPLAY"}
