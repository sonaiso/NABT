"""Distinct written occurrences and bounded conditional cardinal phrases.

Source count, numeral value, grammatical number, and world cardinality are
different domains. Numeral spellings form a closed functional inventory, not a
content-word answer dictionary. Relations to a counted noun remain conditional
on its separately replayed reading and, for plurals, its singular-origin link.
"""

import re

from .derivation import _written_runs
from .errors import NabtError, resource_limit
from .nominal import (GENDERS, LAW_ID, EXPECTED_TABLE_SHA256, _UNSET, _id, _wire,
                      installed_registry, number_rule, read_nominal)
from .word_reader import _clusters, _scan, _source

COUNT_LANGUAGE_ID = "nabt.source-occurrence-count.v1"
PHRASE_LANGUAGE_ID = "nabt.cardinal-counted-sequence.v1"
CARDINAL_DOMAIN = "nabt.cardinal.nonnegative-integer.v1"
UNIT_DOMAIN = "nabt.source.supported-arabic-written-run-occurrence.v1"
NUMERAL_PROFILE = "nabt.unmarked-cardinal-spellings.v1"

# Gender here is the form of the numeral, not of the counted singular.
# Different spellings remain distinct exact source occurrences.
_UNITS = {
    "واحد": (1, "masculine"), "واحدة": (1, "feminine"),
    "اثنان": (2, "masculine"), "اثنين": (2, "masculine"),
    "اثنتان": (2, "feminine"), "اثنتين": (2, "feminine"),
    "ثلاث": (3, "masculine"), "ثلاثة": (3, "feminine"),
    "أربع": (4, "masculine"), "أربعة": (4, "feminine"),
    "خمس": (5, "masculine"), "خمسة": (5, "feminine"),
    "ست": (6, "masculine"), "ستة": (6, "feminine"),
    "سبع": (7, "masculine"), "سبعة": (7, "feminine"),
    "ثمان": (8, "masculine"), "ثماني": (8, "masculine"), "ثمانية": (8, "feminine"),
    "تسع": (9, "masculine"), "تسعة": (9, "feminine"),
    "عشر": (10, "masculine"), "عشرة": (10, "feminine"),
}
_TENS = {
    "عشرون": 20, "عشرين": 20, "ثلاثون": 30, "ثلاثين": 30,
    "أربعون": 40, "أربعين": 40, "خمسون": 50, "خمسين": 50,
    "ستون": 60, "ستين": 60, "سبعون": 70, "سبعين": 70,
    "ثمانون": 80, "ثمانين": 80, "تسعون": 90, "تسعين": 90,
}
_TEEN_UNITS = {
    "أحد": (1, "masculine"), "إحدى": (1, "feminine"),
    "اثنا": (2, "masculine"), "اثني": (2, "masculine"),
    "اثنتا": (2, "feminine"), "اثنتي": (2, "feminine"),
    **{k: v for k, v in _UNITS.items() if 3 <= v[0] <= 9},
}


def count_source_units(text, *, source_id="count", scope="default"):
    """Count distinct supported written-run occurrences, including mentions.

An excluded unsupported run is recorded. No lexical deduplication, morpheme
segmentation, entity resolution, or real-world existence claim takes place.
"""
    installed_registry()
    source = _source(text, source_id, scope)
    partition = _scan(source)
    included, excluded = [], []
    inspected = 0
    for index, run in _written_runs(source, partition, scope):
        inspected += 1
        if inspected > 128:
            raise resource_limit("Too many occurrence-count units", maximum=128)
        item = {**run, "partition_index": index,
                "occurrence_id": _id({"span": run["span"], "scope": scope})}
        try:
            clusters = _clusters(run["surface"])
        except NabtError as error:
            if error.status == "REJECT":
                raise
            excluded.append({**item, "reason": error.code})
            continue
        if clusters:
            included.append(item)
    # The scanner deliberately does not interpret nested quotation fragments.
    # Report their opacity rather than promising a count of unexamined bytes.
    opaque = [p for p in partition if p["kind"] == "quotation" and
              any(c in p["surface"][1:-1] for c in '«»“”"')]
    identities = [u["occurrence_id"] for u in included]
    report = {
        "language_id": COUNT_LANGUAGE_ID, "law_id": LAW_ID, "table_sha256": EXPECTED_TABLE_SHA256,
        "cardinal_domain": CARDINAL_DOMAIN, "unit_domain": UNIT_DOMAIN,
        "source_id": source.source_id, "source_sha256": source.sha256, "scope": scope,
        "raw_text": source.raw_bytes.decode("utf-8"), "partition": partition,
        "units": included, "excluded_runs": excluded, "opaque_quotations": opaque,
        "count": len(set(identities)), "unit_ids_unique": len(set(identities)) == len(identities),
        "status": "DEFER" if opaque else "READ",
        "source_restored": "".join(p["surface"] for p in partition).encode("utf-8") == source.raw_bytes,
        "count_scope": "DISTINCT_SUPPORTED_OCCURRENCES_IN_THE_REPLAYED_INVENTORY",
        "grammatical_number": None, "world_cardinality": None, "ordinal": None,
        "authority": "SOURCE_OCCURRENCE_CARDINALITY_ONLY",
    }
    _wire(report)
    return report


def _numeral_prefix(runs):
    """Read a closed prefix, preserving each source part and its exact spelling."""
    if not runs or len(runs) > 3:
        return None
    words = [r["surface"] for r in runs]
    value, unit, ten, basis = None, None, None, NUMERAL_PROFILE
    if len(words) == 1:
        word = words[0]
        if re.fullmatch(r"[0-9]+|[٠-٩]+", word):
            if len(word) > 4:
                return {"status": "DEFER", "missing": ["CARDINAL_OUTSIDE_BOUNDED_RULE"], "parts": runs}
            digits = "".join(str(ord(c) - ord("٠")) if "٠" <= c <= "٩" else c for c in word)
            if len(digits) > 1 and digits.startswith("0"):
                raise NabtError("NONCANONICAL_CARDINAL_LITERAL", "Leading zeroes need a separate declared numeric domain")
            value, basis = int(digits), "EXACT_DECIMAL_DIGITS"
        elif word in _UNITS:
            value, unit = _UNITS[word]
        elif word in _TENS:
            value = _TENS[word]
        elif word in ("مئة", "مائة", "ألف"):
            value = 1000 if word == "ألف" else 100
    elif len(words) == 2 and words[0] in _TEEN_UNITS and words[1] in ("عشر", "عشرة"):
        digit, unit = _TEEN_UNITS[words[0]]
        value, ten = 10 + digit, "masculine" if words[1] == "عشر" else "feminine"
    else:
        first = _UNITS.get(words[0])
        # The exact conjunction is part of this finite numeral grammar only.
        # It is never a general clitic-segmentation rule for content words.
        tens = (words[1][1:] if len(words) == 2 and words[1].startswith("و") else
                words[2] if len(words) == 3 and words[1] == "و" else None)
        if first and 1 <= first[0] <= 9 and tens in _TENS:
            value, unit = _TENS[tens] + first[0], first[1]
    if value is None:
        return None
    return {"value": value, "domain": CARDINAL_DOMAIN, "unit_gender": unit, "ten_gender": ten,
            "parts": runs, "basis": basis, "status": "READ_VALUE",
            "ordinal": None, "world_cardinality": None,
            "authority": "NUMERAL_VALUE_AND_OBSERVED_FORM_ONLY"}


def _check(observed, expected, *, licensed=True):
    if expected is None:
        return {"status": "UNCONSTRAINED", "observed": observed, "expected": None}
    if observed is None:
        return {"status": "NOT_OBSERVED", "observed": None, "expected": expected}
    values = observed if type(observed) is list else [observed]
    return {"status": ("DEFER" if not licensed else "MATCH" if values == [expected] else
                       "CONFLICT" if expected not in values else "DEFER"),
            "observed": observed, "expected": expected}


def _origins(reading):
    origins = []
    if (reading["kind"]["status"] == "LICENSED" and reading["kind"]["candidates"] == ["noun"]
            and reading["axes"]["number"]["status"] == "LICENSED"
            and reading["axes"]["number"]["candidates"] == ["singular"]
            and reading["axes"]["gender"]["status"] == "LICENSED"):
        origins.append({"singular_gender": reading["axes"]["gender"]["candidates"][0],
                        "basis": "THIS_LICENSED_SINGULAR_READING", "reading_id": reading["reading_id"]})
    for link in reading["singular_links"]:
        if link["status"] == "LICENSED":
            origins.append({**link, "basis": "EXPLICIT_SINGULAR_ORIGIN_LINK"})
    return origins


def read_count_phrase(text, *, lexical_text=None, source_id="count_phrase",
                      lexical_source_id="nominal_lexicon", scope="default"):
    """Check conditional features in one numeral-prefix + counted-run sequence.

This is not a general Arabic NP parser. In particular 1/2 rules do not license
the order of the two words. Raw digits have no observed grammatical gender.
Only the unmarked closed numeral spellings above are acquired in this version.
"""
    nominal = read_nominal(text, lexical_text=lexical_text, source_id=source_id,
                           lexical_source_id=lexical_source_id, scope=scope)
    partition = nominal["partition"]
    significant = [p for p in partition if p["kind"] != "spacing"]
    if significant and significant[-1]["kind"] == "punctuation" and significant[-1]["surface"] == ".":
        significant = significant[:-1]
    missing, alternatives, numeral, counted = [], [], None, None
    internal_spacing = [p for p in partition if p["kind"] == "spacing" and significant
                        and significant[0]["span"]["end"] <= p["span"]["start"]
                        and p["span"]["end"] <= significant[-1]["span"]["start"]]
    if (len(significant) < 2 or any(p["kind"] != "written_run" for p in significant)
            or any(any(c in p["surface"] for c in "\n\r\u2028\u2029") for p in internal_spacing)):
        missing.append("COMPLETE_SINGLE_CARDINAL_COUNTED_SEQUENCE")
    else:
        numeral = _numeral_prefix(significant[:-1])
        if numeral is None:
            missing.append("SUPPORTED_NUMERAL_READING")
        elif numeral["status"] == "DEFER":
            missing.extend(numeral["missing"])
        else:
            counted = next(o for o in nominal["occurrences"] if o["span"] == significant[-1]["span"])
            for reading in counted["readings"]:
                origins = _origins(reading)
                origin_missing = [] if origins else ["SINGULAR_GENDER_WITNESS"]
                choices = origins or [{"singular_gender": g, "basis": "UNRESOLVED_CONDITIONAL_PARAMETER"} for g in GENDERS]
                for origin in choices:
                    try:
                        rule = number_rule(numeral["value"], origin["singular_gender"])
                    except NabtError as error:
                        if error.status != "DEFER":
                            raise
                        missing.append(error.code)
                        continue
                    number_axis = reading["axes"]["number"]
                    checks = {
                        "unit_gender": _check(numeral["unit_gender"], rule["unit_gender"]),
                        "ten_gender": _check(numeral["ten_gender"], rule["ten_gender"]),
                        "counted_number": _check(number_axis["candidates"], rule["counted_number"],
                                                  licensed=number_axis["status"] == "LICENSED"),
                        "counted_case": _check(None, rule["counted_case"]),
                    }
                    local_missing = list(origin_missing)
                    if reading["kind"]["status"] != "LICENSED" or reading["kind"]["candidates"] != ["noun"]:
                        local_missing.append("COUNTED_NOUN_READING")
                    if reading["status"] == "CONFLICT":
                        local_missing.append("CONFLICTING_NOMINAL_READING")
                    is_conflict = any(c["status"] == "CONFLICT" for c in checks.values())
                    alternatives.append({"reading_id": reading["reading_id"],
                        "lexical_reading_id": reading["lexical_reading_id"], "singular_origin": origin,
                        "rule": rule, "checks": checks, "missing": local_missing,
                        "conditional_status": "CONFLICT" if is_conflict else
                                              "DEFER" if local_missing else "COMPATIBLE_OBSERVED_FEATURES",
                        "actual_case": None, "actual_role": None,
                        "authority": "CONDITIONAL_CHECK_NOT_A_COMPLETE_PARSE"})
    report = {
        "language_id": PHRASE_LANGUAGE_ID, "law_id": LAW_ID, "table_sha256": EXPECTED_TABLE_SHA256,
        "source_id": nominal["source_id"], "source_sha256": nominal["source_sha256"], "scope": scope,
        "raw_text": nominal["raw_text"], "lexical_raw_text": nominal["lexical_raw_text"],
        "lexical_source_id": lexical_source_id, "nominal_report": nominal,
        "numeral": numeral, "counted_occurrence_id": None if counted is None else counted["occurrence_id"],
        "alternatives": alternatives, "missing": sorted(set(missing)),
        "status": "DEFER", "frame": "ANNOTATED_CARDINAL_COUNTED_SEQUENCE",
        "construction_truth": "NOT_ESTABLISHED", "actual_case": None, "actual_role": None,
        "world_cardinality": None, "ordinal": None,
        "authority": "SOURCE_RELATIVE_CONDITIONAL_REQUIREMENTS_ONLY",
    }
    _wire(report)
    return report


def verify_source_count(report, *, text=_UNSET, source_id=None, scope=None):
    try:
        if type(report) is not dict:
            raise ValueError("not a report")
        fresh = count_source_units(report["raw_text"] if text is _UNSET else text,
            source_id=report["source_id"] if source_id is None else source_id,
            scope=report["scope"] if scope is None else scope)
        if _wire(fresh) != _wire(report):
            raise ValueError("source count differs")
        return {"valid": True, "status": "VERIFIED", "source_sha256": fresh["source_sha256"],
                "authority": "SOURCE_OCCURRENCE_COUNT_REPLAY_ONLY"}
    except (KeyError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, "status": "DEFER", "code": error.code}
        return {"valid": False, "status": "REJECT", "code": "INVALID_SOURCE_COUNT_REPORT"}


def verify_count_phrase(report, *, text=_UNSET, lexical_text=_UNSET,
                        source_id=None, lexical_source_id=None, scope=None):
    try:
        if type(report) is not dict:
            raise ValueError("not a report")
        fresh = read_count_phrase(report["raw_text"] if text is _UNSET else text,
            lexical_text=report["lexical_raw_text"] if lexical_text is _UNSET else lexical_text,
            source_id=report["source_id"] if source_id is None else source_id,
            lexical_source_id=report["lexical_source_id"] if lexical_source_id is None else lexical_source_id,
            scope=report["scope"] if scope is None else scope)
        if _wire(fresh) != _wire(report):
            raise ValueError("counted sequence differs from replay")
        return {"valid": True, "status": "VERIFIED", "source_sha256": fresh["source_sha256"],
                "authority": "CONDITIONAL_CARDINAL_RULE_REPLAY_ONLY"}
    except (KeyError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, "status": "DEFER", "code": error.code}
        return {"valid": False, "status": "REJECT", "code": "INVALID_COUNTED_SEQUENCE_REPORT"}
