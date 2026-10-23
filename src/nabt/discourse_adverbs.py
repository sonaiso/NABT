"""Replay QAC's T/LOC lexical annotations without importing role/case labels."""

from collections import defaultdict
from copy import deepcopy
from functools import lru_cache
import json

from .corpus_evidence import (_receipt, buckwalter_to_arabic, lexical_index,
                              lookup_key, template_matches)
from .corpus_sources import read_corpus
from .discourse_context import identity, wire


@lru_cache(maxsize=2)
def _index(raw, exclusions, source_id):
    corpus = read_corpus(raw, format="qac", source_id=source_id)
    groups = defaultdict(list)
    for record in corpus["records"]:
        loc = record["locator"]
        if record["valid"] and loc and f"{loc[0]}:{loc[1]}" not in exclusions:
            groups[tuple(loc[:3])].append(record)
    result = defaultdict(list)
    for records in groups.values():
        records.sort(key=lambda row: row["locator"][3])
        if [r["locator"][3] for r in records] != list(range(1, len(records) + 1)):
            continue
        stems = [r for r in records if r["fields"]["FEATURES"].startswith("STEM|")]
        if len(stems) != 1:
            continue
        stem = stems[0]
        tag = stem["fields"]["TAG"]
        features = stem["fields"]["FEATURES"].split("|")
        if tag not in ("T", "LOC") or "POS:" + tag not in features:
            continue
        # Only a complete stem, optionally preceded by the article, is
        # licensed here. Attached pronouns and arbitrary prefixes need their
        # own full attachment and reference witnesses.
        before = records[:records.index(stem)]
        if records[-1] is not stem or any(r["fields"]["FEATURES"] != "PREFIX|Al+" for r in before):
            continue
        form = "".join(buckwalter_to_arabic(r["fields"]["FORM"]) for r in records)
        if lookup_key(form) is None:
            continue
        lemmas = [f[4:] for f in features if f.startswith("LEM:")]
        lemma = buckwalter_to_arabic(lemmas[0]) if len(lemmas) == 1 else form
        row = {"form": form, "lemma": lemma, "pos": tag, "source_article": bool(before),
               "supports": [_receipt(r, corpus["source"]) for r in records],
               "construction": None, "class_candidates": [],
               "authority": "SOURCE_LEXICAL_ADVERB_NOT_ATTACHMENT_OR_CASE"}
        row["id"] = identity(row)
        result[lookup_key(form)].append(wire(row))
    return {k: tuple(v) for k, v in result.items()}


def adverb_candidates(surface, *, lexical_model=None):
    if lexical_model is None:
        return []
    lexical_index(lexical_model)
    index = _index(lexical_model.raw, lexical_model.excluded_verses, lexical_model.source_id)
    result = []
    for encoded in index.get(lookup_key(surface), ()):
        row = json.loads(encoded)
        if template_matches(surface, row["form"], mutable_last=False):
            result.append(deepcopy(row))
    return result
