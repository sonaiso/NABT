"""Source-relative morphology from a bounded Arabic descriptive language.

Open lexemes occur in explicitly delimited readings. Rules recognize property
clauses, not a dictionary assigning the target class to each lexeme. Unparsed
clauses, absent properties, contradictions and out-of-domain axes stay visible.
This is not a free Arabic prose parser or an independent lexical attestation.
"""

from __future__ import annotations

from hashlib import sha256
from importlib.resources import files
from itertools import product
import json
import re

from . import morphology as algebra
from .errors import NabtError, natural, resource_limit
from .learning.source_evidence import SourceBlob, SourceSpan
from .text_ir import span_dict
from .word_reader import _cell_encoding

LANGUAGE_ID = "nabt.arabic-morphology.v1"
# v2 adds reading-local categorical and typed-domain conflict gates. The
# property-description grammar and the installed conditional Lean law do not
# change; reports from v1 must be recomputed before they can pass v2 replay.
READER_VERSION = "nabt.morphology-reader.v2"
NUMBER_DOMAIN = "nabt.morphology-reading.canonical-json-utf8.sentinel256.v1"
EXPECTED_POLICY_SHA256 = "14463f75b6cfa54ed2a9a5ad56b2a595ac87ee0ad97dab43ef6a376079cb3f1a"
MAX_SOURCE_BYTES = 32768
MAX_REPORT_BYTES = 4 * 1024 * 1024
MAX_READINGS = 32
MAX_CLAUSES = 64
_HEADER = re.compile(r"قراءة «([A-Za-z][A-Za-z0-9_]{0,63})» للفظ «([^«»\r\n]{1,256})»:")

# This is a versioned grammar of property descriptions, not lexical answers.
# A qualified compound clause supplies both prerequisites together. Raw an/afal
# shapes, a final nun or the absence of a dictionary entry supply no evidence.
CLAUSES = {
    "يدل على معنى مستقل غير مقترن بزمن": {"independent": True, "time_in_form": False},
    "يدل على معنى مستقل غير مقترن بزمن لهيئته": {"independent": True, "time_in_form": False},
    "يدل على حدث مقترن بزمن": {"independent": True, "event_time": True},
    "يدل على حدث مقترن بزمن بهيئته": {"independent": True, "time_in_form": True},
    "يدل على معنى غير مستقل": {"independent": False},
    "فعله ماض": {"tense": "past"},
    "فعله مضارع": {"tense": "imperfect"},
    "فعله أمر": {"tense": "imperative"},
    "فعلُه ماض": {"tense": "past"},
    "فعلُه مضارع": {"tense": "imperfect"},
    "فعلُه أمر": {"tense": "imperative"},
    "يشبه الحرف": {"particle_resemblance": True},
    "يسلم من شبه الحرف": {"particle_resemblance": False},
    "تتصل به نون الإناث": {"nun": "feminine_plural"},
    "تتصل به نون التوكيد مباشرة": {"nun": "direct_emphatic"},
    "تفصل بينه وبين نون التوكيد فاصل": {"nun": "separated_emphatic"},
    "لا تتصل به نون إناث ولا نون توكيد": {"nun": "none"},
    "لا يمنع تصوره الشركة": {"universal": True},
    "يمنع تصوره الشركة": {"universal": False},
    "يدل على ذات باعتبار صفة": {"property_bearing": True},
    "يدل على ذات دون اعتبار صفة": {"property_bearing": False},
    "دخلت عليه أل": {"al": True},
    "لم تدخل عليه أل": {"al": False},
    "هو مضاف": {"idhafa": True},
    "ليس مضافا": {"idhafa": False},
    "آخره ألف التأنيث": {"tanithAlif": True},
    "ليس آخره ألف التأنيث": {"tanithAlif": False},
    "على صيغة منتهى الجموع": {"muntaha": True},
    "ليس على صيغة منتهى الجموع": {"muntaha": False},
    "ليس علما": {"alam": False},
    "ليس وصفا": {"wasf": False},
    "صفة أصلية على فعلان لا تلحق مؤنثها تاء التأنيث": {"wasf": True, "falan": True},
    "صفة أصلية على أفعل لا تلحق مؤنثها تاء التأنيث": {"wasf": True, "afal": True},
    "علم مركب تركيبا مزجيا غير مختوم بويه": {"alam": True, "tarkib": True},
    "علم بألف ونون زائدتين": {"alam": True, "falan": True},
    "علم مؤنث بالتاء": {"alam": True, "tanith": True},
    "علم مؤنث معنوي زائد على ثلاثة أحرف": {"alam": True, "tanith": True},
    "علم أعجمي الوضع والتعريف زائد على ثلاثة أحرف": {"alam": True, "ajamiOver3": True},
    "علم على وزن يختص بالفعل أو يغلب فيه": {"alam": True, "waznFil": True},
}
BOOL_TRAITS = ("independent", "time_in_form", "event_time", "particle_resemblance", "universal",
               "property_bearing", *algebra.CAUSE_TRAITS, "al", "idhafa")


from nabt import foundation

def _wire(value) -> bytes:
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("utf-8", "strict")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise NabtError("INVALID_MORPHOLOGY_REPORT", "Use a bounded strict JSON report") from error
    if len(raw) > MAX_REPORT_BYTES:
        raise resource_limit("Morphology report exceeds its byte budget")
    return raw


def _hash(value) -> str:
    return sha256(_wire(value)).hexdigest()


def replay_policy() -> dict:
    """Installed pins and exact primary-source windows are checked on each read."""
    root = files("nabt").joinpath("data/source_evidence")
    try:
        raw = root.joinpath("morphology_policy.json").read_bytes()
        if sha256(raw).hexdigest() != EXPECTED_POLICY_SHA256:
            raise ValueError("policy pin differs")
        policy = json.loads(raw)
        for source in policy["sources"]:
            if re.fullmatch(r"[a-z][a-z0-9_]*\.txt", source["file"]) is None:
                raise ValueError("invalid installed source filename")
            content = root.joinpath(source["file"]).read_bytes()
            if sha256(content).hexdigest() != source["sha256"]:
                raise ValueError("source pin differs")
            for passage in source["passages"]:
                part = content[passage["start"]:passage["end"]]
                if sha256(part).hexdigest() != passage["sha256"] or part.decode("utf-8") != passage["text"]:
                    raise ValueError("source window differs")
        return policy
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Morphology source policy cannot be replayed", status="DEFER") from error


def _source(text, source_id, scope):
    if type(scope) is not str or not scope or len(scope) > 256 or any(ord(c) < 32 for c in scope):
        raise NabtError("INVALID_MORPHOLOGY_SCOPE", "Use a bounded nonempty scope")
    if type(text) is str:
        try:
            text = text.encode("utf-8", "strict")
        except UnicodeError as error:
            raise NabtError("INVALID_UTF8", "Source contains an invalid Unicode scalar") from error
    if type(text) is not bytes or not text:
        raise NabtError("INVALID_MORPHOLOGY_SOURCE", "Use nonempty UTF-8 source bytes")
    if len(text) > MAX_SOURCE_BYTES:
        raise resource_limit("Morphology source exceeds its byte budget")
    try:
        return SourceBlob(source_id, text)
    except (ValueError, TypeError, UnicodeError) as error:
        raise NabtError("INVALID_MORPHOLOGY_SOURCE", "Invalid source identity or UTF-8 bytes") from error


def _span(source, start, end):
    raw = source.raw_bytes[start:end]
    return span_dict(SourceSpan(source.source_id, source.sha256, start, end, sha256(raw).hexdigest()))


def _scan(source):
    readings, current, offset, outside = [], None, 0, []
    for raw_line in source.raw_bytes.splitlines(keepends=True):
        line = raw_line.decode("utf-8")
        stripped = line.strip()
        start = offset + len(line[:len(line) - len(line.lstrip())].encode("utf-8"))
        end = start + len(stripped.encode("utf-8"))
        offset += len(raw_line)
        if not stripped:
            continue
        header = _HEADER.fullmatch(stripped)
        if header:
            if len(readings) >= MAX_READINGS:
                raise resource_limit("Too many morphology readings")
            reading_id, lexeme = header.groups()
            if any(r["reading_id"] == reading_id for r in readings):
                raise NabtError("DUPLICATE_READING_ID", "Each reading needs a unique identity")
            lexeme_start = start + len(stripped[:header.start(2)].encode("utf-8"))
            current = {"reading_id": reading_id, "lexeme": lexeme,
                       "header_span": _span(source, start, end),
                       "lexeme_span": _span(source, lexeme_start, lexeme_start + len(lexeme.encode("utf-8"))),
                       "clauses": []}
            readings.append(current)
            continue
        if stripped.startswith("قراءة"):
            # A malformed header must never leak its clauses into the preceding
            # occurrence. Fail the document boundary before classifying it.
            raise NabtError("MALFORMED_READING_HEADER", "An incomplete reading header cannot open or extend a scope",
                            details={"span": _span(source, start, end)})
        if current is None:
            outside.append({"text": stripped, "span": _span(source, start, end)})
            continue
        if len(current["clauses"]) >= MAX_CLAUSES:
            raise resource_limit("Too many clauses in one morphology reading")
        # Only one optional full stop is grammar, never split/discard a suffix.
        clause = stripped[:-1] if stripped.endswith(".") else stripped
        values = CLAUSES.get(clause)
        current["clauses"].append({"text": stripped, "span": _span(source, start, end),
                                   "properties": dict(values) if values is not None else None})
        if values is None:
            current = None  # New recognized header is required to resume.
    return readings, outside


def _state(evidence, name):
    values = [item["value"] for item in evidence if item["property"] == name]
    return int(any(v is True for v in values)) + 2 * int(any(v is False for v in values))


def _categorical(evidence, name, universe):
    known = sorted({item["value"] for item in evidence if item["property"] == name})
    return tuple(universe) if not known else tuple(known) if len(known) == 1 else ()


def _axis(candidates, *, missing=(), conflicts=(), supports=(), rules=(), out=False):
    choices = sorted(set(candidates))
    return {"status": "CONFLICT" if conflicts else "OUT_OF_DOMAIN" if out else
            "LICENSED" if len(choices) == 1 else "DEFER",
            "candidates": choices, "missing": sorted(set(missing)),
            "conflicts": sorted(set(conflicts)), "support_ids": sorted(set(supports)),
            "source_rule_ids": list(rules)}


def _analyse(source, scope, reading, table):
    occurrence = _hash({"source_id": source.source_id, "sha256": source.sha256,
                        "scope": scope, "span": reading["lexeme_span"], "reading": reading["reading_id"]})
    evidence, unknown = [], []
    for clause in reading["clauses"]:
        if clause["properties"] is None:
            unknown.append({"text": clause["text"], "span": clause["span"], "code": "UNPARSED_PROPERTY_CLAUSE"})
            continue
        for name, value in clause["properties"].items():
            item = {"property": name, "value": value, "source_id": source.source_id,
                    "source_sha256": source.sha256, "scope": scope, "reading_id": reading["reading_id"],
                    "occurrence_id": occurrence, "span": clause["span"], "text": clause["text"]}
            item["support_id"] = _hash(item)
            evidence.append(item)
    state = lambda name: _state(evidence, name)
    support = lambda names: [e["support_id"] for e in evidence if e["property"] in names]
    conflict = lambda names: [n for n in names if state(n) == 3]
    unknowns = lambda names: [n for n in names if state(n) == 0]
    identity = {"source": source.source_id + ":" + source.sha256, "occurrence": occurrence,
                "reading": reading["reading_id"], "context": scope + ":" + occurrence,
                "policy": EXPECTED_POLICY_SHA256}

    kind_names = ("independent", "time_in_form")
    kinds = sorted({"particle" if not independent else "verb" if timed else "noun"
                    for independent, timed in product(*(algebra.possible_bools(state(n)) for n in kind_names))})
    kind = _axis(kinds, missing=unknowns(kind_names) if len(kinds) != 1 else (),
                 conflicts=conflict(kind_names), supports=support(kind_names), rules=("word_kind",))

    tense = _categorical(evidence, "tense", algebra.TENSES)
    nun = _categorical(evidence, "nun", algebra.NUNS)
    # Preserve contradictory source assignments even if the kind candidates
    # do not visit the verb branch. Branch selection cannot erase a witness.
    categorical_conflicts = [name for name, values in (("tense", tense), ("nun", nun)) if not values]
    source_conflicts = []
    for name in categorical_conflicts:
        item = {"code": "CATEGORICAL_PROPERTY_CONFLICT", "property": name,
                "values": sorted({e["value"] for e in evidence if e["property"] == name}),
                "support_ids": sorted(support((name,))), "occurrence_id": occurrence,
                "reading_id": reading["reading_id"]}
        item["conflict_id"] = _hash(item)
        source_conflicts.append(item)
    # These are consistency guards, not new word-kind classifiers. A tense or
    # nun description alone leaves the old kind alternatives unchanged. A
    # positive verbal connection conflicts only with an independently supplied
    # kind that excludes verbs. Mere absence of nun does not assert verbhood.
    if kinds and "verb" not in kinds:
        for name in ("tense", "nun"):
            witnesses = [e for e in evidence if e["property"] == name
                         and (name == "tense" or e["value"] != "none")]
            if witnesses:
                item = {"code": "PROPERTY_DOMAIN_MISMATCH", "property": name,
                        "expected_kind": "verb", "candidate_kinds": kinds,
                        "values": sorted({e["value"] for e in witnesses}),
                        "support_ids": sorted(set(support(kind_names) +
                                                   [e["support_id"] for e in witnesses])),
                        "occurrence_id": occurrence, "reading_id": reading["reading_id"]}
                item["conflict_id"] = _hash(item)
                source_conflicts.append(item)
    construction_models, construction_conflicts, construction_missing = [], list(categorical_conflicts), []
    for candidate in kinds:
        if candidate == "particle":
            construction_models.append({"kind": "particle", "construction": "built"})
        elif candidate == "noun":
            for resemblance in algebra.possible_bools(state("particle_resemblance")):
                construction_models.append({"kind": "noun", "particle_resemblance": resemblance,
                                            "construction": "built" if resemblance else "inflected"})
            construction_conflicts += conflict(("particle_resemblance",))
            construction_missing += unknowns(("particle_resemblance",))
        else:
            for t, n in product(tense, nun):
                row = table["verb_rows"][4 * algebra.TENSES.index(t) + algebra.NUNS.index(n)]
                construction_models.append({"kind": "verb", "tense": t, "nun": n,
                                            "construction": algebra.CONSTRUCTIONS[row["construction"]]})
            if len(tense) > 1:
                construction_missing.append("tense")
            if "imperfect" in tense and len(nun) > 1:
                construction_missing.append("nun")
    construction_values = [m["construction"] for m in construction_models]
    construction = _axis(construction_values, missing=construction_missing if len(set(construction_values)) != 1 else (),
                         conflicts=kind["conflicts"] + construction_conflicts,
                         supports=support((*kind_names, "particle_resemblance", "tense", "nun")),
                         rules=("noun_construction", "verb_construction", "particle_construction"))
    construction["models"] = construction_models

    semantic_values = []
    semantic_traits = ("universal", "property_bearing")
    for k in kinds:
        if k != "noun":
            semantic_values.append("outside_universal_noun")
        else:
            for universal, quality in product(*(algebra.possible_bools(state(n)) for n in semantic_traits)):
                semantic_values.append("outside_universal_noun" if not universal else "mushtaq" if quality else "jins_jamid")
    nominal = _axis(semantic_values,
                    missing=unknowns(semantic_traits) if len(set(semantic_values)) != 1 else (),
                    conflicts=kind["conflicts"] + (conflict(semantic_traits) if "noun" in kinds else []),
                    supports=support((*kind_names, *semantic_traits)), rules=("universal_nominal_denotation",),
                    out=set(semantic_values) == {"outside_universal_noun"})
    nominal["domain"] = "UNIVERSAL_NOMINAL_DENOTATION_NOT_ETYMOLOGY_OR_VERB_CONJUGATION"

    cause_states = tuple(state(n) for n in algebra.CAUSE_TRAITS)
    cause_values = algebra.cause_candidates(cause_states)
    residual = algebra.named_residual(algebra.CAUSE_TRAITS, cause_states, identity=identity, formula_kind="cause")
    diptote = _axis(["diptote" if x else "ordinary" for x in cause_values],
                    missing=[n for plan in residual["minimal_plans"] for n in plan] if len(cause_values) != 1 else (),
                    conflicts=conflict(algebra.CAUSE_TRAITS), supports=support(algebra.CAUSE_TRAITS),
                    rules=("qualified_diptote_causes",), out="noun" not in kinds and bool(kinds))
    diptote["residual"] = residual
    diptote["cause_prediction"] = {"status": "CONFLICT" if conflict(algebra.CAUSE_TRAITS) else
                                    "LICENSED" if len(cause_values) == 1 else "DEFER",
                                    "candidates": list(diptote["candidates"]),
                                    "domain": "QUALIFIED_INTRINSIC_CAUSE_FORMULA_ONLY"}
    diptote["prerequisites"] = ["SOURCE_ESTABLISHES_NOUN"] if kinds != ["noun"] else []
    if construction["status"] != "LICENSED" or construction["candidates"] != ["inflected"]:
        diptote["prerequisites"].append("LICENSED_INFLECTED_NOUN")
    if kinds == ["noun"] and construction["status"] == "LICENSED" and construction["candidates"] == ["built"]:
        diptote["status"] = "OUT_OF_DOMAIN"
    if diptote["prerequisites"] and diptote["status"] == "LICENSED":
        diptote["status"] = "DEFER"
    context_states = (state("al"), state("idhafa"))
    genitive_residual = algebra.named_residual(("al", "idhafa"), context_states, identity=identity, formula_kind="genitive")
    genitive_values = ["kasra" if al or idhafa else "fatha"
                      for al, idhafa in product(*(algebra.possible_bools(s) for s in context_states))]
    genitive = _axis(genitive_values, missing=unknowns(("al", "idhafa")) if len(set(genitive_values)) != 1 else (),
                     conflicts=conflict(("al", "idhafa")), supports=support(("al", "idhafa")),
                     rules=("diptote_genitive",))
    genitive["residual"] = genitive_residual
    genitive["application"] = "IF_THIS_IS_AN_INFLECTED_DIPTOTE_IN_GENITIVE_CASE"
    genitive["applied_to_occurrence"] = False
    genitive["prerequisites"] = ["INDEPENDENT_GENITIVE_CASE_WITNESS"]
    if diptote["status"] != "LICENSED" or diptote["candidates"] != ["diptote"]:
        genitive["prerequisites"].append("LICENSED_DIPTOTE_CAUSE")
    if construction["status"] != "LICENSED" or construction["candidates"] != ["inflected"]:
        genitive["prerequisites"].append("LICENSED_INFLECTED_NOUN")
    diptote["genitive"] = genitive

    axes = {"kind": kind, "construction": construction, "nominal_semantics": nominal, "diptote": diptote}
    if source_conflicts:
        # Keep conditional candidate calculations visible, but no positive
        # approval may be consumed from this inconsistent reading. Other
        # readings, including homographs in this document, are independent.
        conflict_ids = [item["conflict_id"] for item in source_conflicts]
        for axis in (*axes.values(), genitive, diptote["cause_prediction"]):
            if axis["status"] == "LICENSED":
                axis["status"] = "CONFLICT"
            axis["blocked_by_source_conflict"] = True
            axis["source_conflict_ids"] = conflict_ids
        diptote["prerequisites"] = sorted(set(diptote["prerequisites"] +
            ["CONSISTENT_SOURCE_READING", "LICENSED_INFLECTED_NOUN"]))
        genitive["prerequisites"] = sorted(set(genitive["prerequisites"] +
            ["CONSISTENT_SOURCE_READING", "LICENSED_INFLECTED_NOUN", "LICENSED_DIPTOTE_CAUSE"]))
    if unknown:
        for axis in axes.values():
            if axis["status"] == "LICENSED":
                axis["status"] = "DEFER"
            axis["blocked_by_unparsed_source"] = True
        if genitive["status"] == "LICENSED":
            genitive["status"] = "DEFER"
        genitive["blocked_by_unparsed_source"] = True
        genitive["prerequisites"] = sorted(set(genitive["prerequisites"] +
             ["COMPLETE_SOURCE_INTERPRETATION", "LICENSED_INFLECTED_NOUN", "LICENSED_DIPTOTE_CAUSE"]))
    conflicts = [n for n in BOOL_TRAITS if state(n) == 3] + construction_conflicts
    status = "CONFLICT" if conflicts or source_conflicts else "DEFER" if unknown or any(a["status"] == "DEFER" for a in axes.values()) else "READ"
    return {**reading, "occurrence_id": occurrence, "source_id": source.source_id,
            "source_sha256": source.sha256, "scope": scope, "status": status,
            "encoding": _cell_encoding(reading["lexeme"]), "evidence": evidence,
            "unparsed": unknown, "source_conflicts": source_conflicts, "axes": axes,
            "evidence_encoding": {"domain": algebra.EVIDENCE_DOMAIN, "traits": list(BOOL_TRAITS),
                                  "number": algebra.evidence_number(tuple(state(n) for n in BOOL_TRAITS))},
            "unimplemented_axes": ["ETYMOLOGICAL_ROOT_DERIVATION", "VERB_CONJUGATION_JAMID_MUTASARRIF"],
            "authority": "CONSEQUENCES_OF_THESE_SOURCE_DESCRIPTIONS_ONLY"}


def read_morphology(text, *, source_id="input", scope="default") -> dict:
    foundation.require_foundation('nabt.morphology_reader.read_morphology')
    source = _source(text, source_id, scope)
    policy = replay_policy()
    table = algebra.installed_table()
    readings, outside = _scan(source)
    analysed = [_analyse(source, scope, reading, table) for reading in readings]
    status = "CONFLICT" if any(r["status"] == "CONFLICT" for r in analysed) else "DEFER" if outside or not analysed or any(r["status"] == "DEFER" for r in analysed) else "READ"
    result = {"language_id": LANGUAGE_ID, "reader_version": READER_VERSION, "law_id": algebra.LAW_ID,
              "policy_sha256": EXPECTED_POLICY_SHA256, "table_sha256": algebra.EXPECTED_TABLE_SHA256,
              "source_id": source_id, "source_sha256": source.sha256, "scope": scope,
              "raw_text": source.raw_bytes.decode("utf-8"), "status": status,
              "readings": analysed, "unscoped_clauses": outside,
              "rules": policy["rules"], "facts": [], "semantic_projection": "NONE",
              "world_truth": "NOT_ESTABLISHED", "authority": "SOURCE_RELATIVE_MORPHOLOGY_ONLY"}
    _wire(result)
    return result


def verify_morphology(report, *, text=None, source_id=None, scope=None) -> dict:
    foundation.require_foundation('nabt.morphology_reader.verify_morphology')
    try:
        if type(report) is not dict:
            raise ValueError("not a report")
        fresh = read_morphology(report["raw_text"] if text is None else text,
                                source_id=report["source_id"] if source_id is None else source_id,
                                scope=report["scope"] if scope is None else scope)
        if _wire(fresh) != _wire(report):
            raise ValueError("source/reading/evidence mismatch")
        return {"valid": True, "status": "VERIFIED", "source_sha256": fresh["source_sha256"],
                "authority": "SOURCE_BOUND_REPORT_REPLAY_ONLY"}
    except (OSError, KeyError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, "status": "DEFER", "code": error.code}
        return {"valid": False, "status": "REJECT", "code": "INVALID_MORPHOLOGY_REPORT"}


def morphology_number(report: dict) -> int:
    check = verify_morphology(report)
    if not check["valid"]:
        raise NabtError(check["code"], "Morphology report cannot be encoded", status=check["status"])
    return int.from_bytes(b"\x01" + _wire(report), "big")


def decode_morphology(number: int) -> dict:
    natural(number, "morphology_number")
    if number.bit_length() > 8 * (MAX_REPORT_BYTES + 1):
        raise resource_limit("Morphology number exceeds its byte budget")
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big")
    try:
        if not raw or raw[0] != 1:
            raise ValueError("missing sentinel")
        value = json.loads(raw[1:].decode("utf-8", "strict"))
        if _wire(value) != raw[1:]:
            raise ValueError("noncanonical number")
        check = verify_morphology(value)
        if not check["valid"]:
            raise NabtError(check["code"], "Morphology number failed replay", status=check["status"])
        return value
    except (UnicodeError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            raise
        raise NabtError("INVALID_MORPHOLOGY_NUMBER", "Malformed or unlicensed morphology encoding") from error
