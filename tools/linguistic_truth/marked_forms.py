"""Source-replayed vocalization premises for the existing bounded cue reader.

This is a reviewed acquisition bridge, not a native proof of source
interpretation. It supplies spellings only for readings already present in the
semantic inventory. It cannot introduce a designation or select its meaning.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from nabt import foundation


REVIEW_PATH = Path("evidence/attested_mark_recovery_v1/source_review.json")
REVIEW_SHA256 = "4b2411793136de0744a0a8cd39eeeecd44fb3ddd6bd9b59cd1481dd69f321484"
LAW_ID = "nabt.bounded-cue-vocalization.v1"


def _load_review(root: Path):
    """Reopen every installed byte source; no caller-controlled replacement."""
    raw = (root / REVIEW_PATH).read_bytes()
    if sha256(raw).hexdigest() != REVIEW_SHA256:
        raise ValueError("MARK_REVIEW_CHANGED")
    review = json.loads(raw)
    if review["schema"] != "nabt.attested-mark-review.v1":
        raise ValueError("MARK_REVIEW_SCHEMA")
    sources = {}
    for source in review["sources"]:
        source_path = (root / source["path"]).resolve()
        if not source_path.is_relative_to(root.resolve()):
            raise ValueError("MARK_SOURCE_OUTSIDE_ROOT")
        data = source_path.read_bytes()
        if source["id"] in sources or sha256(data).hexdigest() != source["sha256"]:
            raise ValueError("MARK_SOURCE_CHANGED")
        sources[source["id"]] = data
    passages = {}
    for passage in review["passages"]:
        start, end = passage["start_byte"], passage["end_byte"]
        data = sources[passage["source_id"]]
        if (passage["id"] in passages or type(start) is not int or type(end) is not int
                or not 0 <= start < end <= len(data)):
            raise ValueError("MARK_PASSAGE_BOUNDS")
        selected = data[start:end]
        if (sha256(selected).hexdigest() != passage["sha256"]
                or selected.decode("utf-8") != passage["quote"]):
            raise ValueError("MARK_PASSAGE_CHANGED")
        passages[passage["id"]] = passage
    for rows in (review["lexemes"], review["rules"]):
        seen = set()
        for row in rows:
            if (row["id"] in seen or not row["passage_ids"]
                    or not set(row["passage_ids"]) <= passages.keys()):
                raise ValueError("MARK_REVIEW_UNBOUND")
            seen.add(row["id"])
    for lexeme in review["lexemes"]:
        foundation.validate_source(lexeme["stem"])
    return review


def _license(form, lexemes, rules, role):
    return {"form": form, "role": role, "law_id": LAW_ID,
            "lexeme_ids": [row["id"] for row in lexemes],
            "rule_ids": [row["id"] for row in rules],
            "passage_ids": sorted({p for row in [*lexemes, *rules] for p in row["passage_ids"]}),
            "review_sha256": REVIEW_SHA256,
            "authority": "REVIEWED_VOCALIZATION_AND_BOUNDED_INFLECTION",
            "native_acquisition_proof": False}


def _definite(stem, article_type):
    # This bounded review covers these five initial carriers only. A future
    # ledger must not silently turn its own category label into an all-letter
    # phonological license.
    if article_type == "lunar" and stem[0] in "أحم":
        return "الْ" + stem
    if article_type == "solar" and stem[0] in "رش":
        return "ال" + stem[0] + "ّ" + stem[1:]
    raise ValueError("MARK_REVIEW_ARTICLE_TYPE")


def _reviewed_forms(review, normal, role):
    """Generate only the declared simple definite-noun inflections.

    The nominative lexical citation is not reused as an accusative or genitive
    surface. That final vowel is supplied by the separately reviewed role rule.
    Unknown words, bare/indefinite nouns, irregular inflection,
    and unrelated syntactic constructions remain outside this small bridge.
    """
    rules = {row["id"]: row for row in review["rules"]}
    lexemes = review["lexemes"]
    if role == "grammar":
        return [_license(row["stem"], [row], [], role) for row in lexemes
                if row["normal"] == normal and row["inflection"] == "fixed"]
    if role == "expression":
        required = ["ba_genitive", "regular_genitive"]
        if not all(key in rules for key in required):
            return []
        return [_license("بِ" + _definite(row["stem"], row["article_type"]) + "ِ", [row],
                         [rules[k] for k in [*required, row["article_type"] + "_article"]], role)
                for row in lexemes if row["normal"] == normal
                and row["kind"] == "noun" and row["inflection"] == "regular_definite"
                and row["article_type"] + "_article" in rules]
    if role != "sense":
        return []
    words = normal.split()
    required = ["object_accusative", "regular_accusative", "adjective_agreement"]
    if len(words) != 2 or not all(key in rules for key in required):
        return []
    nouns = [row for row in lexemes if row["normal"] == words[0]
             and row["kind"] == "noun" and row["inflection"] == "regular_definite"]
    adjectives = [row for row in lexemes if row["normal"] == words[1]
                  and row["kind"] == "adjective" and row["inflection"] == "regular_definite"]
    return [_license(_definite(noun["stem"], noun["article_type"]) + "َ "
                     + _definite(adjective["stem"], adjective["article_type"]) + "َ",
                     [noun, adjective], [rules[k] for k in dict.fromkeys([*required,
                         noun["article_type"] + "_article", adjective["article_type"] + "_article"])], role)
            for noun in nouns for adjective in adjectives
            if noun["article_type"] + "_article" in rules and adjective["article_type"] + "_article" in rules]
