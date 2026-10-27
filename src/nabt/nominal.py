"""Source-qualified nominal features and independent number/weakness domains.

The installed Lean table is a conditional law, not a content-word lexicon.
Written endings propose observations. Explicit descriptions and a small,
declared pronoun inventory can constrain readings, with their original source
identities retained. Neither a profile code nor a cardinal value denotes an
external individual, an ordinal position, a syntactic role, or actual case.
"""

from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
import json
import re

from .derivation import RADICALS, _written_runs, read_derivation
from .errors import NabtError, natural, resource_limit
from .text_ir import span_dict
from .text_morphology import _observations
from .word_reader import _clusters, _matches, _scan, _source, _span

LAW_ID = "nabt.nominal-evidence.v1"
LANGUAGE_ID = "nabt.arabic-nominal-evidence.v1"
FACT_LANGUAGE_ID = "nabt.arabic-nominal-assertions.v1"
READER_VERSION = "nabt.nominal-reader.v1"
NUMBER_DOMAIN = "nabt.nominal.canonical-json-utf8.sentinel256.v1"
EXPECTED_TABLE_SHA256 = "0b0218d75329e1b04302ebdf875a4a43db772d4650b3415bc767f2a6a96d07a8"
GENDERS = ("masculine", "feminine")
NUMBERS = ("singular", "dual", "plural")
FORMS = ("singular", "dual", "sound_masculine_plural", "sound_feminine_plural",
         "broken_plural", "other_plural")
DEFINITENESS = ("indefinite", "definite")
MAX_REPORT_BYTES = 4 * 1024 * 1024
MAX_READINGS = 32
MAX_CLAUSES = 64
_UNSET = object()
_HEADER = re.compile(r"قراءة «([A-Za-z][A-Za-z0-9_]{0,63})» للفظ «([^«»\r\n]{1,256})»:")
_ROOT = re.compile(r"جذره «([^«»\r\n]+)»\.")
_SINGULAR = re.compile(r"مفرده القراءة «([A-Za-z][A-Za-z0-9_]{0,63})»\.")

# This is a grammar of explicit source premises, not answers for lexemes.
# A plural formation claim and a separately cited singular origin are distinct.
_CLAUSES = {
    "هو اسم.": ("kind", "noun"),
    "هو فعل.": ("kind", "verb"),
    "هو حرف.": ("kind", "particle"),
    "هو مذكر.": ("constraint", 0),
    "هو مؤنث.": ("constraint", 1),
    "يدل على واحد.": ("constraint", 2),
    "يدل على اثنين أو اثنتين.": ("constraint", 3),
    "يدل على أكثر من اثنين.": ("constraint", 4),
    "هو جمع مذكر سالم.": ("constraint", 5),
    "هو جمع بألف وتاء زائدتين.": ("constraint", 6),
    "هو جمع بتغيير بناء مفرده.": ("constraint", 7),
    "هو جمع خارج الأنواع المدعومة.": ("constraint", 8),
    "هو علم.": ("definite_cause", "proper_name"),
    "هو ضمير.": ("definite_cause", "pronoun"),
    "هو اسم إشارة.": ("definite_cause", "demonstrative"),
    "هو اسم موصول.": ("definite_cause", "relative"),
    "أل فيه للتعريف.": ("definite_cause", "article"),
    "هو مضاف إضافة معنوية إلى معرفة.": ("definite_cause", "semantic_idafa_to_definite"),
    "هو نكرة.": ("constraint", 10),
    "هو معرب.": ("inflected", True),
    "هو مبني.": ("inflected", False),
    "آخره ياء لازمة.": ("necessary_final_yaa", True),
    "ياؤه الأخيرة غير لازمة.": ("necessary_final_yaa", False),
    "ما قبل الياء مكسور.": ("preceding_kasra", True),
    "ما قبل الياء غير مكسور.": ("preceding_kasra", False),
    "ياؤه الأخيرة غير مشددة.": ("final_yaa_unshaddad", True),
    "ياؤه الأخيرة مشددة.": ("final_yaa_unshaddad", False),
}


from nabt import foundation

def _wire(value):
    try:
        data = json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8", "strict")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise NabtError("INVALID_NOMINAL_REPORT", "Use bounded strict JSON") from error
    if len(data) > MAX_REPORT_BYTES:
        raise resource_limit("Nominal report exceeds its byte budget")
    return data


def _id(value):
    return sha256(_wire(value)).hexdigest()


def installed_registry():
    """Replay installed bytes on each public operation; no caller authority."""
    try:
        raw = files("nabt").joinpath("data/nominal_evidence.json").read_bytes()
        if sha256(raw).hexdigest() != EXPECTED_TABLE_SHA256:
            raise ValueError("nominal table pin differs")
        table = json.loads(raw)
        if table["law_id"] != LAW_ID:
            raise ValueError("nominal law domain differs")
        for key, size in (("profile_rows", 22), ("numeral_rows", 202),
                          ("weak_rows", 8), ("manqus_rows", 32),
                          ("receipt_rows", 128), ("pronoun_rows", 14)):
            if type(table[key]) is not list or len(table[key]) != size:
                raise ValueError("nominal finite inventory differs")
        return table
    except (OSError, KeyError, TypeError, ValueError, UnicodeError) as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Installed nominal law cannot be replayed",
                        status="DEFER") from error


def nominal_catalog():
    return {"law_id": LAW_ID, "table_sha256": EXPECTED_TABLE_SHA256,
            "table": installed_registry(), "genders": list(GENDERS),
            "numbers": list(NUMBERS), "forms": list(FORMS),
            "definiteness": list(DEFINITENESS),
            "authority": "CONDITIONAL_FEATURE_LAW_NOT_A_LEXICON"}


def _profiles(codes, table):
    for code in codes:
        natural(code, "nominal_constraint", maximum=10)
    return [row for row in table["profile_rows"] if all(row["accepts"][c] for c in codes)]


def nominal_candidates(constraints=()):
    if type(constraints) not in (list, tuple) or len(constraints) > MAX_CLAUSES:
        raise NabtError("INVALID_NOMINAL_CONSTRAINTS", "Use a bounded sequence of conditional premises")
    return deepcopy(_profiles(constraints, installed_registry()))


def _axis(values, *, active=True, conflict=False, outside=False, supports=()):
    values = sorted(set(values))
    status = ("CONFLICT" if conflict else "OUT_OF_DOMAIN" if outside else
              "LICENSED" if active and len(values) == 1 else "DEFER")
    return {"status": status, "candidates": values, "activated": active and not conflict and not outside,
            "support_ids": sorted(set(supports)), "authority": "SOURCE_RELATIVE_ONLY"}


def _axes(rows, *, active=True, conflict=False, outside=False, supports=()):
    domains = {"gender": GENDERS, "number": NUMBERS, "form": FORMS, "definiteness": DEFINITENESS}
    return {name: _axis([domain[r[name]] for r in rows], active=active, conflict=conflict,
                       outside=outside, supports=supports) for name, domain in domains.items()}


def number_rule(value, singular_gender):
    """Expected grammar under explicit cardinal and singular-gender premises."""
    natural(value, "cardinal_value")
    if not (1 <= value <= 99 or value in (100, 1000)):
        raise NabtError("NUMBER_RULE_OUTSIDE_DOMAIN", "Cardinal law covers 1..99, 100 and 1000 only",
                        status="DEFER")
    if type(singular_gender) is not str or singular_gender not in GENDERS:
        raise NabtError("INVALID_SINGULAR_GENDER", "Supply the grammatical gender of the singular noun")
    row = next(r for r in installed_registry()["numeral_rows"]
               if r["quantity"] == value and r["singular_gender"] == GENDERS.index(singular_gender))
    result = deepcopy(row)
    result["singular_gender"] = singular_gender
    result["counted_number"] = NUMBERS[row["counted_number"]]
    for key in ("unit_gender", "ten_gender"):
        result[key] = None if row[key] is None else GENDERS[row[key]]
    return {**result, "law_id": LAW_ID, "numeral_kind": "cardinal",
            "status": "CONDITIONAL_RULE", "actual_case": None, "actual_role": None,
            "ordinal": None, "world_cardinality": None,
            "authority": "CONDITIONAL_ON_CARDINAL_RELATION_AND_SINGULAR_GENDER"}


def weak_root_profile(root):
    """Classify positions in a supplied three-radical string, not its origin."""
    table = installed_registry()
    if type(root) is not str or len(root) != 3 or any(c not in RADICALS for c in root):
        raise NabtError("INVALID_ROOT_PROFILE", "Supply three canonical radicals; alif is not a radical here")
    mask = sum(1 << i for i, char in enumerate(root) if char in "وي")
    row = table["weak_rows"][mask]
    return {"law_id": LAW_ID, "root": root, "mask": mask, "class": row["class"],
            "weak_positions": [i for i in range(3) if mask & (1 << i)],
            "status": "RESIDUAL" if mask in (3, 7) else "CONDITIONAL_CLASSIFICATION",
            "basis": "SUPPLIED_CANONICAL_RADICALS", "attested_root": False,
            "hamzated": "ء" in root, "geminated": root[1] == root[2],
            "soundness_scope": "NO_WEAK_RADICALS_DOES_NOT_MEAN_NO_HAMZA_OR_GEMINATION",
            "nominal_manqus": None, "surface_realization": None,
            "authority": "WEAK_RADICAL_POSITIONS_ONLY"}


def _partial_manqus(properties, kinds, table, blocked=False):
    positive = negative = 0
    known = {"noun": set(k == "noun" for k in kinds)} if len(kinds) == 1 else {}
    for name in ("inflected", "necessary_final_yaa", "preceding_kasra", "final_yaa_unshaddad"):
        known[name] = {p["value"] for p in properties if p["property"] == name}
    for i, name in enumerate(("noun", "inflected", "necessary_final_yaa", "preceding_kasra", "final_yaa_unshaddad")):
        if True in known.get(name, set()):
            positive |= 1 << i
        if False in known.get(name, set()):
            negative |= 1 << i
    rows = [r for r in table["manqus_rows"] if r["mask"] & positive == positive and not r["mask"] & negative]
    values = sorted({r["accepted"] for r in rows})
    conflict = bool(positive & negative)
    if blocked and not conflict:
        values = [False, True]
    return {"status": "CONFLICT" if conflict else "LICENSED" if not blocked and len(values) == 1 else "DEFER",
            "candidates": values, "positive_mask": positive, "negative_mask": negative,
            "support_ids": [p["support_id"] for p in properties if p["property"] in known],
            "root_weakness_consumed": False, "authority": "CONDITIONAL_NOMINAL_ENDING_DEFINITION"}


def _scan_facts(source):
    blocks, outside, current, offset = [], [], None, 0
    for raw in source.raw_bytes.splitlines(keepends=True):
        line = raw.decode("utf-8")
        stripped = line.strip()
        start = offset + len(line[:len(line) - len(line.lstrip())].encode("utf-8"))
        offset += len(raw)
        if not stripped:
            continue
        support = {"surface": stripped, "span": span_dict(_span(source, start, start + len(stripped.encode("utf-8"))))}
        match = _HEADER.fullmatch(stripped)
        if match:
            if len(blocks) >= MAX_READINGS:
                raise resource_limit("Too many nominal source readings", maximum=MAX_READINGS)
            identifier, lexeme = match.groups()
            if any(b["reading_id"] == identifier for b in blocks):
                raise NabtError("DUPLICATE_READING_ID", "Nominal readings require unique source-local identifiers")
            _clusters(lexeme)
            lo = start + len(stripped[:match.start(2)].encode("utf-8"))
            current = {"reading_id": identifier, "lexeme": lexeme, "header": support,
                       "lexeme_span": span_dict(_span(source, lo, lo + len(lexeme.encode("utf-8")))),
                       "properties": [], "unparsed": []}
            blocks.append(current)
            continue
        if stripped.startswith("قراءة"):
            raise NabtError("MALFORMED_READING_HEADER", "An incomplete header cannot extend an earlier nominal scope")
        if current is None:
            outside.append(support)
            continue
        if len(current["properties"]) + len(current["unparsed"]) >= MAX_CLAUSES:
            raise resource_limit("Too many clauses in one nominal reading", maximum=MAX_CLAUSES)
        root, singular = _ROOT.fullmatch(stripped), _SINGULAR.fullmatch(stripped)
        prop = _CLAUSES.get(stripped)
        if root:
            weak_root_profile(root[1])
            prop = ("root", root[1])
        elif singular:
            prop = ("singular_reading", singular[1])
        if prop is None:
            current["unparsed"].append(support)
        else:
            item = {**support, "reading_id": current["reading_id"], "property": prop[0], "value": prop[1],
                    "basis": "EXPLICIT_SOURCE_PREMISE"}
            item["support_id"] = _id(item)
            current["properties"].append(item)
    return blocks, outside


def _finish_fact(block, table, outside):
    props = block["properties"]
    clusters = _clusters(block["lexeme"])
    if clusters and clusters[-1][0] == "ي" and "ّ" in clusters[-1][1]:
        observed = {"property": "final_yaa_unshaddad", "value": False,
                    "reading_id": block["reading_id"], "span": block["lexeme_span"],
                    "basis": "OBSERVED_FINAL_YAA_SHADDA"}
        observed["support_id"] = _id(observed)
        props.append(observed)
    kinds = sorted({p["value"] for p in props if p["property"] == "kind"})
    causes = [p for p in props if p["property"] == "definite_cause"]
    # These descriptions themselves explicitly assert a nominal category.
    if causes:
        kinds = sorted(set(kinds) | {"noun"})
    constraints = [p["value"] for p in props if p["property"] == "constraint"]
    if causes:
        constraints.append(9)
    known_kinds = kinds or ["noun", "verb", "particle"]
    property_ids = [p["support_id"] for p in props]
    conflict = len(kinds) > 1
    if kinds and kinds != ["noun"] and (constraints or any(p["property"] != "kind" and p["property"] != "root" for p in props)):
        conflict = True
    rows = _profiles(constraints, table)
    conflict |= not rows
    for name in ("inflected", "necessary_final_yaa", "preceding_kasra", "final_yaa_unshaddad", "root", "singular_reading"):
        conflict |= len({p["value"] for p in props if p["property"] == name}) > 1
    blocked = bool(block["unparsed"] or outside)
    active = kinds == ["noun"] and not blocked and not conflict
    if blocked or kinds != ["noun"]:
        rows = table["profile_rows"]
    if conflict:
        rows = []
    block.update(kind=_axis(known_kinds, active=not blocked, conflict=conflict, supports=property_ids),
                 axes=_axes(rows, active=active, conflict=conflict,
                            outside=bool(kinds and kinds != ["noun"]), supports=property_ids),
                 profile_codes=[r["code"] for r in rows], constraints=constraints,
                 definite_causes=[p["value"] for p in causes],
                 manqus=_partial_manqus(props, known_kinds, table, blocked or conflict),
                 weak_roots=[] if blocked or conflict else
                    [{**weak_root_profile(p["value"]), "support_id": p["support_id"]}
                     for p in props if p["property"] == "root"],
                 blocked=blocked, conflict=bool(conflict),
                 status="CONFLICT" if conflict else "DEFER" if blocked or kinds != ["noun"] else "READ",
                 actual_role=None, actual_case=None, facts=[],
                 authority="CONDITIONAL_ON_THIS_SOURCE_READING")
    return block


def read_nominal_facts(text, *, source_id="nominal_lexicon", scope="default"):
    foundation.require_foundation('nabt.nominal.read_nominal_facts')
    table = installed_registry()
    source = _source(text, source_id, scope)
    blocks, outside = _scan_facts(source)
    for block in blocks:
        _finish_fact(block, table, outside)
    indexed = {b["reading_id"]: b for b in blocks}
    def cyclic_origin(start):
        pending, visited = [start], set()
        while pending:
            identifier = pending.pop()
            target = indexed.get(identifier)
            if target is None or identifier in visited:
                continue
            visited.add(identifier)
            for item in target["properties"]:
                if item["property"] == "singular_reading":
                    if item["value"] == start:
                        return True
                    pending.append(item["value"])
        return False
    for block in blocks:
        links = []
        for prop in block["properties"]:
            if prop["property"] != "singular_reading":
                continue
            target = indexed.get(prop["value"])
            reasons = []
            if target is None:
                reasons.append("MISSING_SINGULAR_READING")
            elif target is block:
                reasons.append("SELF_ORIGIN_LINK")
            elif cyclic_origin(block["reading_id"]):
                reasons.append("CYCLIC_ORIGIN_LINK")
            elif target["conflict"] or target["blocked"] or block["conflict"] or block["blocked"]:
                reasons.append("BLOCKED_ORIGIN_READING")
            elif target["kind"]["candidates"] != ["noun"] or target["axes"]["number"]["candidates"] != ["singular"]:
                reasons.append("ORIGIN_NOT_LICENSED_SINGULAR_NOUN")
            elif target["axes"]["gender"]["status"] != "LICENSED":
                reasons.append("ORIGIN_GENDER_NOT_LICENSED")
            if block["kind"]["candidates"] != ["noun"]:
                reasons.append("TARGET_NOT_LICENSED_NOUN")
            links.append({"target_reading_id": prop["value"], "support_id": prop["support_id"],
                          "status": "DEFER" if reasons else "LICENSED", "missing": reasons,
                          "singular_gender": None if reasons else target["axes"]["gender"]["candidates"][0],
                          "source_id": source.source_id, "source_sha256": source.sha256, "scope": scope,
                          "authority": "ASSERTED_SOURCE_RELATION_NOT_INFERRED_ETYMOLOGY"})
        block["singular_links"] = links
    report = {"language_id": FACT_LANGUAGE_ID, "reader_version": READER_VERSION,
              "law_id": LAW_ID, "table_sha256": EXPECTED_TABLE_SHA256,
              "source_id": source.source_id, "source_sha256": source.sha256, "scope": scope,
              "raw_text": source.raw_bytes.decode("utf-8"), "readings": blocks, "unscoped_clauses": outside,
              "status": "CONFLICT" if any(b["conflict"] for b in blocks) else
                        "READ" if blocks and all(b["status"] == "READ" for b in blocks) else "DEFER",
              "content_word_answer_entries_used": 0, "facts": [], "world_truth": "NOT_ESTABLISHED",
              "authority": "REPLAYED_SOURCE_ASSERTIONS_NOT_INDEPENDENT_ATTESTATION"}
    _wire(report)
    return report


def _pronouns(clusters, table):
    return [p for p in table["pronoun_rows"] if _matches(clusters, _clusters(p["surface"]))]


def _surface_observations(source, run):
    observations, blockers, clusters = _observations(source, run)
    if not clusters:
        return observations, blockers, clusters
    letters = "".join(c[0] for c in clusters)
    proposals = []
    if letters.endswith("ة"):
        proposals.append(("taa_marbuta_carrier", "LEXICAL_GENDER_WITNESS"))
    for suffix, label in (("ان", "dual_suffix_candidate"), ("ين", "dual_or_sound_plural_suffix_candidate"),
                          ("ون", "sound_masculine_suffix_candidate"), ("ات", "alif_taa_suffix_candidate")):
        if len(letters) > len(suffix) and letters.endswith(suffix):
            proposals.append((label, "STEM_SEGMENTATION_AND_FORMATION_WITNESS"))
    if letters.endswith("ي"):
        proposals.append(("terminal_yaa_candidate", "NOUN_INFLECTION_NECESSARY_YAA_AND_KASRA_WITNESSES"))
    for label, missing in proposals:
        item = {"type": label, "surface": run["surface"], "span": run["span"],
                "missing": [missing], "authority": "OBSERVATION_ONLY"}
        item["observation_id"] = _id(item)
        observations.append(item)
    return observations, blockers, clusters


def _reading(source, run, scope, lexical, table, lexical_report):
    identity = {"source_id": source.source_id, "source_sha256": source.sha256, "scope": scope,
                "occurrence_id": run["occurrence_id"], "span": run["span"],
                "segmentation_id": run["segmentation_id"],
                "lexical_reading_id": None if lexical is None else lexical["reading_id"],
                "lexical_source_id": None if lexical_report is None else lexical_report["source_id"],
                "lexical_source_sha256": None if lexical_report is None else lexical_report["source_sha256"]}
    reading_id = _id(identity)
    observations, blockers, clusters = _surface_observations(source, run)
    pronoun_shapes = _pronouns(clusters, table) if clusters else []
    pronouns = pronoun_shapes if lexical is None or "pronoun" in lexical["definite_causes"] else []
    kinds = {"noun", "verb", "particle"}
    if pronouns:
        kinds = {"noun"}
    constraints, properties = [], []
    blocked, conflict = bool(blockers), False
    if lexical is not None:
        blocked |= lexical["blocked"]
        conflict |= lexical["conflict"]
        if not blocked and not conflict:
            kinds &= set(lexical["kind"]["candidates"])
            constraints.extend(lexical["constraints"])
            properties = lexical["properties"]
    if clusters and clusters[-1][0] == "ي" and "ّ" in clusters[-1][1]:
        properties = list(properties)
        observed = {"property": "final_yaa_unshaddad", "value": False,
                    "span": run["span"], "basis": "OBSERVED_FINAL_YAA_SHADDA"}
        observed["support_id"] = _id(observed)
        properties.append(observed)
        conflict |= any(p["property"] == "final_yaa_unshaddad" and p["value"] is True for p in properties)
    rows = _profiles(constraints, table)
    if pronouns:
        rows = [r for r in rows if r["definiteness"] == 1 and
                any(r["number"] == p["number"] and (p["gender"] == 2 or r["gender"] == p["gender"])
                    for p in pronouns)]
    conflict |= not kinds or not rows
    # Source-relative nominal properties cannot cross a known verb/particle boundary.
    if kinds and "noun" not in kinds and properties:
        conflict |= any(p["property"] not in ("kind", "root") for p in properties)
    noun = kinds == {"noun"}
    if blocked:
        rows = table["profile_rows"]
    if conflict:
        rows = []
    active = noun and not blocked and not conflict
    raw_span = source.raw_bytes[run["span"]["start"]:run["span"]["end"]]
    flags = [run["span"]["source_id"] == source.source_id and run["span"]["source_sha256"] == source.sha256
             and raw_span == run["surface"].encode("utf-8")
             and sha256(raw_span).hexdigest() == run["span"]["span_sha256"],
             identity["scope"] == scope,
             run["occurrence_id"] == _id({"span": run["span"], "scope": scope}) and
             run["segmentation_id"] == _id({"occurrence_id": run["occurrence_id"], "profile": "WRITTEN_RUN_UNSEGMENTED_V1"}),
             reading_id == _id(identity), bool(pronouns or properties), bool(blocked or conflict), noun]
    mask = sum(1 << i for i, flag in enumerate(flags) if flag)
    receipt = {"identity": identity, "reading_id": reading_id, "flags": flags, "mask": mask,
               "activated": table["receipt_rows"][mask]["activated"],
               "support_ids": [p["support_id"] for p in properties],
               "pronoun_surfaces": sorted({p["surface"] for p in pronouns})}
    receipt["receipt_id"] = _id(receipt)
    return {"reading_id": reading_id, "identity": identity, "kind": _axis(kinds, active=not blocked, conflict=conflict),
            "axes": _axes(rows, active=active, conflict=conflict, outside=bool(kinds and "noun" not in kinds),
                          supports=receipt["support_ids"]), "profile_codes": [r["code"] for r in rows],
            "observations": observations, "blockers": blockers, "pronoun_candidates": deepcopy(pronouns),
            "pronoun_shape_proposals": deepcopy(pronoun_shapes),
            "reading_basis": "CANDIDATE_PRONOUN_READING" if pronouns else
                             "SELECTED_SOURCE_ASSERTION" if lexical is not None else "UNRESOLVED_WRITTEN_RUN",
            "exhaustive_over_arabic_homographs": False,
            "qualified_profile_codes": [r["code"] for r in rows] if receipt["activated"] else [],
            "lexical_reading_id": None if lexical is None else lexical["reading_id"],
            "lexical_source_link": None if lexical is None else {"reading_id": lexical["reading_id"],
                "source_id": lexical_report["source_id"], "source_sha256": lexical_report["source_sha256"],
                "scope": scope, "lexeme_span": lexical["lexeme_span"], "match": "EXACT_UTF8_SURFACE",
                "application": "CONDITIONAL_ON_SELECTED_SOURCE_ASSERTION",
                "context_independently_verified": False},
            "manqus": _partial_manqus(properties, sorted(kinds), table, blocked or conflict),
            "weak_roots": [] if lexical is None or blocked or conflict else lexical["weak_roots"],
            "singular_links": [] if lexical is None or blocked or conflict else lexical["singular_links"],
            "receipt": receipt, "status": "CONFLICT" if conflict else "READ" if active else "DEFER",
            "actual_role": None, "actual_case": None, "declension_class": None,
            "grammatical_nun_type": None, "grammatical_segmentation": None,
            "semantic_jamid_mushtaq": "NOT_CONSUMED", "authority": "SOURCE_QUALIFIED_FEATURE_READING"}


def read_nominal(text, *, lexical_text=None, source_id="input", lexical_source_id="nominal_lexicon", scope="default"):
    foundation.require_foundation('nabt.nominal.read_nominal')
    table = installed_registry()
    source = _source(text, source_id, scope)
    lexical = None if lexical_text is None else read_nominal_facts(lexical_text, source_id=lexical_source_id, scope=scope)
    if lexical is not None and lexical["source_id"] == source.source_id:
        raise NabtError("SOURCE_ID_COLLISION", "Text and lexical evidence need distinct source identities")
    partition = _scan(source)
    shapes = read_derivation(text, source_id=source_id, scope=scope)
    by_occurrence = {o["occurrence_id"]: o for o in shapes["occurrences"]}
    occurrences = []
    for index, segment in _written_runs(source, partition, scope):
        if len(occurrences) >= 128:
            raise resource_limit("Too many nominal source occurrences", maximum=128)
        run = {**segment, "partition_index": index, "occurrence_id": _id({"span": segment["span"], "scope": scope})}
        run["segmentation_id"] = _id({"occurrence_id": run["occurrence_id"], "profile": "WRITTEN_RUN_UNSEGMENTED_V1"})
        matches = [] if lexical is None else [r for r in lexical["readings"] if r["lexeme"] == run["surface"]]
        run["readings"] = [_reading(source, run, scope, r, table, lexical) for r in matches or [None]]
        if matches and not any(r["pronoun_candidates"] for r in run["readings"]) and any(r["pronoun_shape_proposals"] for r in run["readings"]):
            run["readings"].append(_reading(source, run, scope, None, table, lexical))
        run["weak_root_candidates"] = [{**weak_root_profile(c["root"]),
            "status": "CANDIDATE", "basis": "EXACT_PATTERN_ROOT_CANDIDATE_NOT_ATTESTED",
            "pattern_id": c["pattern_id"], "derivation_candidate_id": c["candidate_id"],
            "root_alignment": c["alignment"], "authority": "FORMAL_ROOT_CANDIDATE_POSITIONS_ONLY"}
            for c in by_occurrence[run["occurrence_id"]]["candidates"] if len(c["root"]) == 3]
        occurrences.append(run)
    restored = "".join(p["surface"] for p in partition).encode("utf-8") == source.raw_bytes
    if not restored:
        raise NabtError("INTERNAL_CONTRACT_FAILED", "Nominal partition did not restore source")
    report = {"language_id": LANGUAGE_ID, "reader_version": READER_VERSION,
              "law_id": LAW_ID, "table_sha256": EXPECTED_TABLE_SHA256,
              "source_id": source.source_id, "source_sha256": source.sha256, "scope": scope,
              "raw_text": source.raw_bytes.decode("utf-8"),
              "lexical_raw_text": None if lexical is None else lexical["raw_text"],
              "lexical_source_id": lexical_source_id, "lexical_report": lexical,
              "partition": partition, "occurrences": occurrences, "source_restored": restored,
              "status": "CONFLICT" if any(r["status"] == "CONFLICT" for o in occurrences for r in o["readings"]) else "DEFER",
              "content_word_answer_entries_used": 0, "closed_pronoun_rows": len(table["pronoun_rows"]),
              "derivation_bridge": {"profile": shapes["profile"], "law_id": shapes["law_id"],
                  "table_sha256": shapes["table_sha256"], "attested_roots_activated": False},
              "unicode_normalization": "NONE", "facts": [], "world_truth": "NOT_ESTABLISHED",
              "authority": "SOURCE_QUALIFIED_NOMINAL_CANDIDATES"}
    _wire(report)
    return report


def verify_nominal_facts(report, *, text=_UNSET, source_id=None, scope=None):
    foundation.require_foundation('nabt.nominal.verify_nominal_facts')
    try:
        if type(report) is not dict:
            raise ValueError("not a report")
        fresh = read_nominal_facts(report["raw_text"] if text is _UNSET else text,
            source_id=report["source_id"] if source_id is None else source_id,
            scope=report["scope"] if scope is None else scope)
        if _wire(fresh) != _wire(report):
            raise ValueError("nominal assertions differ from source replay")
        return {"valid": True, "status": "VERIFIED", "source_sha256": fresh["source_sha256"],
                "authority": "SOURCE_ASSERTION_REPLAY_ONLY"}
    except (OSError, KeyError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, "status": "DEFER", "code": error.code}
        return {"valid": False, "status": "REJECT", "code": "INVALID_NOMINAL_FACT_REPORT"}


def verify_nominal(report, *, text=_UNSET, lexical_text=_UNSET, source_id=None, lexical_source_id=None, scope=None):
    foundation.require_foundation('nabt.nominal.verify_nominal')
    try:
        if type(report) is not dict:
            raise ValueError("not a report")
        fresh = read_nominal(report["raw_text"] if text is _UNSET else text,
            lexical_text=report["lexical_raw_text"] if lexical_text is _UNSET else lexical_text,
            source_id=report["source_id"] if source_id is None else source_id,
            lexical_source_id=report["lexical_source_id"] if lexical_source_id is None else lexical_source_id,
            scope=report["scope"] if scope is None else scope)
        if _wire(fresh) != _wire(report):
            raise ValueError("nominal report differs from replay")
        return {"valid": True, "status": "VERIFIED", "source_sha256": fresh["source_sha256"],
                "authority": "SOURCE_QUALIFIED_FEATURE_REPLAY_ONLY"}
    except (OSError, KeyError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, "status": "DEFER", "code": error.code}
        return {"valid": False, "status": "REJECT", "code": "INVALID_NOMINAL_REPORT"}


def nominal_number(report):
    check = verify_nominal(report)
    if not check["valid"]:
        raise NabtError(check["code"], "Nominal report cannot be encoded", status=check["status"])
    return int.from_bytes(b"\x01" + _wire(report), "big")


def decode_nominal(number):
    if type(number) is not int or number < 1:
        raise NabtError("INVALID_NOMINAL_NUMBER", "Use a positive canonical report number")
    size = (number.bit_length() + 7) // 8
    if size > MAX_REPORT_BYTES + 1:
        raise resource_limit("Nominal report number exceeds its byte budget")
    raw = number.to_bytes(size, "big")
    try:
        if raw[:1] != b"\x01":
            raise ValueError("sentinel")
        value = json.loads(raw[1:])
        if _wire(value) != raw[1:] or not verify_nominal(value)["valid"]:
            raise ValueError("noncanonical report")
        return value
    except (UnicodeError, ValueError, TypeError) as error:
        raise NabtError("INVALID_NOMINAL_NUMBER", "Number is not a canonical replayable nominal report") from error


def count_source_units(text, *, source_id="count", scope="default"):
    from .counting import count_source_units as execute
    return execute(text, source_id=source_id, scope=scope)


def read_count_phrase(text, *, lexical_text=None, source_id="count_phrase", lexical_source_id="nominal_lexicon", scope="default"):
    foundation.require_foundation('nabt.nominal.read_count_phrase')
    from .counting import read_count_phrase as execute
    return execute(text, lexical_text=lexical_text, source_id=source_id,
                   lexical_source_id=lexical_source_id, scope=scope)
