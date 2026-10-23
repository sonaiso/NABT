"""Source-relative verb paradigm availability, separate from noun semantics.

This small evidence language consumes availability assertions about a named
lexeme. It does not infer nonexistence from a missing corpus form, or infer
that two pattern matches are conjugations of the same lexical verb. Its
three-cell law has explicit scope: one available cell is jamid, two partial,
three full. The result is conditional on all source assertions being true
of the same verb. It is not unrestricted Arabic paradigm acquisition.
"""

from copy import deepcopy
import re

from .derivation import (_id, _wire, installed_registry, EXPECTED_TABLE_SHA256,
                         MAX_SOURCE_BYTES, MAX_REPORT_BYTES)
from .errors import NabtError, resource_limit
from .text_ir import span_dict
from .word_reader import _clusters, _source, _span

LAW_ID = "nabt.verb-paradigm-availability.v1"
LANGUAGE_ID = "nabt.arabic-verb-paradigm-assertions.v1"
READER_VERSION = "nabt.verb-paradigm-reader.v1"
FORMS = ("past", "imperfect", "imperative")
CATEGORIES = ("jamid", "partial", "full")
_NAMES = {"الماضي": 0, "المضارع": 1, "الأمر": 2}
_HEADER = re.compile(r"الفعل «([^»\n]+)»\.")
_POSITIVE = re.compile(r"(الماضي|المضارع|الأمر) مستعمل: «([^»\n]+)»\.")
_NEGATIVE = re.compile(r"(الماضي|المضارع|الأمر) غير مستعمل\.")


def availability_candidates(positive_mask, negative_mask):
    """Conditional finite algebra; these inputs are premises, not witnesses."""
    if (type(positive_mask) is not int or type(negative_mask) is not int
            or not 0 <= positive_mask < 8 or not 0 <= negative_mask < 8):
        raise NabtError("INVALID_PARADIGM_MASK", "Availability needs two three-bit natural masks")
    table = installed_registry()
    try:
        if table["paradigm_law_id"] != LAW_ID:
            raise ValueError("different paradigm law")
        row = table["paradigm_rows"][8 * positive_mask + negative_mask]
        if (type(row["positive_mask"]) is not int or type(row["negative_mask"]) is not int
                or row["positive_mask"] != positive_mask or row["negative_mask"] != negative_mask):
            raise ValueError("different row identity")
        return deepcopy(row)
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Installed paradigm law cannot be replayed", status="DEFER") from error


def _lexical_surface(text):
    if len(text) > 128 or not text:
        raise NabtError("INVALID_PARADIGM_SURFACE", "Use a bounded Arabic lexical surface")
    _clusters(text)


def _finish(block):
    positive = negative = 0
    for item in block["assertions"]:
        bit = 1 << FORMS.index(item["form"])
        if item["available"]:
            positive |= bit
        else:
            negative |= bit
    row = availability_candidates(positive, negative)
    categories, models = row["categories"], row["models"]
    # An unsupported clause might qualify, negate, or separate a preceding
    # assertion. Do not selectively ignore it to activate a convenient answer.
    blocked = bool(block["unparsed"])
    if blocked:
        status, categories, models = "DEFER", list(CATEGORIES), list(range(1, 8))
    elif positive & negative:
        status = "CONFLICT"
    elif not models:
        status = "OUT_OF_DOMAIN"
    else:
        status = "LICENSED" if len(categories) == 1 else "DEFER"
    block.update(positive_mask=positive, negative_mask=negative,
        conditional_constraint=row,
        axis={"name": "verb_paradigm_availability", "status": status,
              "candidates": categories, "models": models,
              "activated": bool(block["assertions"]) and not blocked,
              "support_ids": [a["assertion_id"] for a in block["assertions"]],
              "missing": ["PARSE_ALL_SOURCE_CLAUSES"] if blocked else
                         ["ADDITIONAL_AVAILABILITY_ASSERTIONS"] if len(categories) > 1 else []},
        status=status, actual_role=None, actual_case=None,
        nominal_jamid_mushtaq="NOT_CONSUMED",
        same_lexeme_basis="EXPLICIT_SOURCE_BLOCK_NOT_AUTOMATIC_PARADIGM_ALIGNMENT",
        availability_basis="SOURCE_ASSERTIONS_NOT_CORPUS_ABSENCE",
        authority="CONDITIONAL_ON_ASSERTED_SAME_VERB_AVAILABILITY")
    return block


def read_verb_paradigm(text, *, source_id="paradigm", scope="default"):
    # Even an entirely unparsed source must not issue a report for an
    # installed law whose bytes or domain have not been replayed.
    availability_candidates(0, 0)
    source = _source(text, source_id, scope)
    blocks, unscoped = [], []
    current = None
    offset, assertions = 0, 0
    for raw_line in source.raw_bytes.decode("utf-8").splitlines(keepends=True):
        line = raw_line.strip()
        left = len(raw_line) - len(raw_line.lstrip())
        start = offset + len(raw_line[:left].encode("utf-8"))
        offset += len(raw_line.encode("utf-8"))
        if not line:
            continue
        support = {"surface": line, "span": span_dict(_span(source, start, start + len(line.encode("utf-8"))))}
        header = _HEADER.fullmatch(line)
        if header:
            _lexical_surface(header[1])
            if current is not None:
                blocks.append(_finish(current))
            if len(blocks) >= 32:
                raise resource_limit("Too many independent paradigm blocks", maximum=32)
            identity = {"source_id": source.source_id, "source_sha256": source.sha256,
                        "scope": scope, "header_span": support["span"]}
            current = {"lexeme": header[1], "header": support, "identity": identity,
                       "reading_id": _id(identity), "assertions": [], "unparsed": []}
            continue
        positive, negative = _POSITIVE.fullmatch(line), _NEGATIVE.fullmatch(line)
        if current is None:
            unscoped.append(support)
            continue
        if positive or negative:
            match = positive or negative
            if positive:
                _lexical_surface(positive[2])
            assertions += 1
            if assertions > 128:
                raise resource_limit("Too many paradigm assertions", maximum=128)
            assertion = {**support, "reading_id": current["reading_id"],
                         "form": FORMS[_NAMES[match[1]]], "available": positive is not None,
                         "attested_form_claim": positive[2] if positive else None,
                         "basis": "EXPLICIT_SOURCE_ASSERTION_NOT_INFERRED_FACT"}
            assertion["assertion_id"] = _id(assertion)
            current["assertions"].append(assertion)
        else:
            current["unparsed"].append(support)
    if current is not None:
        blocks.append(_finish(current))
    # Unscoped qualifications may affect every following block. Keep all
    # candidate conclusions suspended rather than discarding those clauses.
    if unscoped:
        for block in blocks:
            block["axis"].update(status="DEFER", candidates=list(CATEGORIES), models=list(range(1, 8)),
                                 activated=False, missing=["PARSE_UNSCOPED_SOURCE_CLAUSES"])
            block["status"] = "DEFER"
    status = "CONFLICT" if any(b["status"] == "CONFLICT" for b in blocks) else (
        "OUT_OF_DOMAIN" if blocks and all(b["status"] == "OUT_OF_DOMAIN" for b in blocks) else
        "READ" if blocks and all(b["status"] == "LICENSED" for b in blocks) else "DEFER")
    report = {"language_id": LANGUAGE_ID, "reader_version": READER_VERSION,
              "law_id": LAW_ID, "table_sha256": EXPECTED_TABLE_SHA256,
              "source_id": source.source_id, "source_sha256": source.sha256,
              "scope": scope, "raw_text": source.raw_bytes.decode("utf-8"),
              "readings": blocks, "unscoped_clauses": unscoped, "status": status,
              "form_domain": list(FORMS), "classification_domain": list(CATEGORIES),
              "classification_rule": "1_AVAILABLE_CELL_JAMID;2_PARTIAL;3_FULL;0_OUTSIDE_VERB_DOMAIN",
              "content_word_answer_entries_used": 0, "absence_from_text_is_negative_evidence": False,
              "nominal_semantics_consumed": False, "facts": [], "world_truth": "NOT_ESTABLISHED",
              "authority": "REPLAYED_SOURCE_RELATIVE_VERB_AVAILABILITY_ONLY"}
    _wire(report)
    return report


def verify_verb_paradigm(report, *, text=None, source_id=None, scope=None):
    try:
        if type(report) is not dict:
            raise ValueError("not a report")
        fresh = read_verb_paradigm(report["raw_text"] if text is None else text,
            source_id=report["source_id"] if source_id is None else source_id,
            scope=report["scope"] if scope is None else scope)
        if _wire(report) != _wire(fresh):
            raise ValueError("source/availability report differs")
        return {"valid": True, "status": "VERIFIED", "source_sha256": fresh["source_sha256"],
                "authority": "SOURCE_RELATIVE_AVAILABILITY_REPLAY_ONLY"}
    except (OSError, KeyError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, "status": "DEFER", "code": error.code}
        return {"valid": False, "status": "REJECT", "code": "INVALID_VERB_PARADIGM_REPORT"}
