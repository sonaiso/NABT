"""Acquire bounded morphological evidence from new, exactly preserved text.

Content words are not looked up in an answer policy. Terminal tanwin can
witness noun kind under this profile's ordinary-use reading, but not its
inflection class. Closed grammatical markers have explicitly cited source
attestations. Adjacency, an al-prefix, a nun or a putative pattern only proposes
a relation/observation: none supplies a missing lexical classification.

Optional lexical descriptions are a separate, replayed source of premises.
Matching is deliberately exact, reading alternatives remain separate, and
contextual al/idafa statements never transfer from that source to a new
occurrence. The existing conditional morphology algebra consumes only the
supported, linked intrinsic properties. This is not an unrestricted parser.
"""

from copy import deepcopy
from hashlib import sha256
from itertools import product
import json

from . import morphology as algebra
from . import morphology_reader as descriptions
from . import text_evidence
from .errors import NabtError, natural, resource_limit
from .text_ir import span_dict
from .word_reader import (_cell_encoding, _clusters, _scan, _source, _span,
                          replay_policy as replay_word_policy)

LANGUAGE_ID = "nabt.arabic-text-morphology.v1"
READER_VERSION = "nabt.text-morphology-reader.v1"
NUMBER_DOMAIN = "nabt.text-morphology.canonical-json-utf8.sentinel256.v1"
MAX_SOURCE_BYTES = 8192
MAX_REPORT_BYTES = 4 * 1024 * 1024
MAX_LINKED_READINGS = 32
_UNSET = object()
_TANWIN = frozenset("ًٌٍ")
_SHORT = frozenset("َُِْ")
_CONTEXT_PROPERTIES = frozenset(("al", "idhafa"))
# These are functional markers, not answers for content lexemes. Exact marks
# prevent conflating مِنْ/مَنْ and لَمْ/لِمَ. Unmarked homographs stay unknown.
# The canonical vocalizations are authored applications of the cited windows.
_MARKERS = {
    "لَمْ": ("imperfect", "imperfect_signs", "jazm"),
    "لَنْ": ("imperfect", "basic_case_endings", "nasb"),
    "سَوْفَ": ("imperfect", "sibawayhi_particles", None),
    "مِنْ": ("preposition", "min_preposition", "jarr"),
    "فِي": ("preposition", "alfiyya_particles", "jarr"),
    "إِلَى": ("preposition", "min_preposition", "jarr"),
    "عَنْ": ("preposition", "min_preposition", "jarr"),
    "عَلَى": ("preposition", "min_preposition", "jarr"),
    "هَلْ": ("interrogative", "particle_kinds", None),
    "بَلْ": ("discourse", "particle_kinds", None),
}


def _wire(value):
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("utf-8", "strict")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise NabtError("INVALID_TEXT_MORPHOLOGY_REPORT", "Use a bounded strict JSON report") from error
    if len(raw) > MAX_REPORT_BYTES:
        raise resource_limit("Text morphology report exceeds its byte budget")
    return raw


def _id(value):
    return sha256(_wire(value)).hexdigest()


def _axis(candidates, *, supports=(), missing=(), conflict=False, out=False):
    values = sorted(set(candidates))
    return {"status": "CONFLICT" if conflict or not values else "OUT_OF_DOMAIN" if out else
            "LICENSED" if len(values) == 1 else "DEFER", "candidates": values,
            "support_ids": sorted(set(supports)), "missing": sorted(set(missing))}


def _observations(source, run):
    """No observation changes source bytes or carries an implicit class label."""
    observations, blockers = [], []
    try:
        clusters = _clusters(run["surface"])
    except NabtError as error:
        if error.status == "REJECT":
            raise
        return [], [{"code": error.code, "status": error.status, "span": run["span"]}], []
    surface = run["surface"]
    letters = "".join(cluster[0] for cluster in clusters)

    def observe(kind, start, end, **data):
        lo = run["span"]["start"] + len(surface[:start].encode("utf-8"))
        hi = run["span"]["start"] + len(surface[:end].encode("utf-8"))
        item = {"type": kind, "span": span_dict(_span(source, lo, hi)),
                "surface": surface[start:end], "authority": "OBSERVATION_ONLY", **data}
        item["observation_id"] = _id(item)
        observations.append(item)

    tanwin = [(i, marks & _TANWIN) for i, (_, marks, _, _) in enumerate(clusters) if marks & _TANWIN]
    valid_tanwin = False
    if tanwin:
        index, marks = tanwin[0]
        # Both orthographic placements of accusative tanwin are retained:
        # رَجُلًا and رَجُلاً. A support alif cannot carry a conflicting mark.
        terminal = index == len(clusters) - 1
        support_alif = (index == len(clusters) - 2 and marks == {"ً"}
                        and clusters[-1][0] in "اى" and not clusters[-1][1])
        if clusters[index][0] in "اى" and (marks != {"ً"} or index == 0 or not terminal):
            raise NabtError("INVALID_ALIF_TANWIN", "An alif cannot carry damm/kasr tanwin or stand alone as its support",
                            details={"span": run["span"]})
        valid_tanwin = len(tanwin) == 1 and (terminal or support_alif)
        if valid_tanwin:
            observe("terminal_tanwin", clusters[index][2], clusters[-1][3],
                    mark=next(iter(marks)), rule_id="word_kinds")
        else:
            raise NabtError("NONTERMINAL_OR_MULTIPLE_TANWIN", "Tanwin has no licensed terminal position",
                            details={"span": run["span"]})
    if len(clusters) > 2 and letters.startswith("ال"):
        observe("al_prefix_candidate", 0, clusters[1][3],
                missing=["ARTICLE_SEGMENTATION_WITNESS"], rule_id="word_kinds")
        # An al-like carrier sequence is not automatically the article. Do not
        # erase noun evidence or assert an al/tanwin contradiction from it.
    if clusters[-1][0] == "ن":
        observe("final_nun", clusters[-1][2], clusters[-1][3],
                missing=["NUN_TYPE_AND_ATTACHMENT_WITNESS"], rule_id="imperfect_signs")
    if clusters[-1][0] in "اى":
        observe("final_alif", clusters[-1][2], clusters[-1][3],
                missing=["LEXICAL_FEMININITY_OR_RADICAL_WITNESS"])
    if clusters[0][0] in "نأيت" and len(clusters) >= 3:
        observe("imperfect_onset_candidate", 0, clusters[0][3],
                missing=["INDEPENDENT_VERB_READING_WITNESS"], rule_id="imperfect_signs")
    ending = clusters[-1][1] & (_SHORT | _TANWIN)
    if ending:
        observe("surface_ending", clusters[-1][2], clusters[-1][3], mark=next(iter(ending)))
    return observations, blockers, clusters


def _receipt(identity, code, rule_id, supports, sources, *, active=True, blocked=False,
             derivation_supports=()):
    """Issue only from extracted supports, then check the finite activation law."""
    valid = bool(supports)
    for support in supports:
        span = support["span"]
        source = sources.get(span["source_id"])
        valid &= (span["source_id"] == identity["source_id"]
                  and span["source_sha256"] == identity["source_sha256"]
                  and source is not None and source.sha256 == span["source_sha256"]
                  and type(span["start"]) is int and type(span["end"]) is int
                  and 0 <= span["start"] < span["end"] <= len(source.raw_bytes)
                  and sha256(source.raw_bytes[span["start"]:span["end"]]).hexdigest() == span["span_sha256"])
    flags = (True, True, active, blocked, bool(supports), bool(valid))
    value = {"identity": identity, "cue_code": code, "rule_code": code, "rule_id": rule_id,
             "supports": supports, "activation_flags": list(flags),
             "derivation_supports": list(derivation_supports),
             "activated": text_evidence.receipt_activated(flags)}
    value["receipt_id"] = _id(value)
    return value


def _lexical_properties(reading):
    return [item for item in reading["evidence"] if item["property"] not in _CONTEXT_PROPERTIES]


def _analyse_reading(source, scope, run, lexical, lexical_source, table, cause_cache):
    key = {"source_id": source.source_id, "source_sha256": source.sha256, "scope": scope,
           "occurrence_id": run["occurrence_id"], "span": run["span"],
           "lexical_source_sha256": None if lexical_source is None else lexical_source.sha256,
           "lexical_reading_id": None if lexical is None else lexical["reading_id"]}
    reading_id = _id(key)
    identity = {**key, "reading_id": reading_id, "segmentation_id": run["segmentation_id"]}
    receipts, properties = [], [] if lexical is None else _lexical_properties(lexical)
    sources = {source.source_id: source}
    if lexical_source is not None:
        sources[lexical_source.source_id] = lexical_source
    blockers = deepcopy(run["blockers"])
    if lexical is not None and (lexical["status"] == "CONFLICT" or lexical["unparsed"]):
        blockers.append({"code": "LEXICAL_SOURCE_CONFLICT" if lexical["status"] == "CONFLICT"
                         else "UNPARSED_LEXICAL_SOURCE", "source_reading_id": lexical["reading_id"]})
    blocked = bool(blockers)
    for observation in run["observations"]:
        if observation["type"] == "terminal_tanwin":
            receipts.append(_receipt(identity, 0, "word_kinds", [observation], sources,
                                     blocked=bool(run["blockers"])))
    marker = _MARKERS.get(run["surface"])
    if marker is not None:
        receipts.append(_receipt(identity, 2, marker[1],
                                 [{"span": run["span"], "surface": run["surface"],
                                   "basis": "EXACT_SOURCE_QUALIFIED_FUNCTION_MARKER"}], sources,
                                 blocked=bool(run["blockers"])))
    lexical_kind = None
    if lexical is not None and not blocked:
        axis = lexical["axes"]["kind"]
        if axis["status"] == "LICENSED":
            lexical_kind = axis["candidates"][0]
            supports = [item for item in properties if item["property"] in ("independent", "time_in_form")]
            receipts.append(_receipt(identity, text_evidence.KINDS.index(lexical_kind),
                                     "word_kind", [{"span": run["span"], "surface": run["surface"],
                                       "basis": "EXACT_SURFACE_LINK_TO_REPLAYED_LEXICAL_READING"}], sources,
                                     derivation_supports=supports))
    cues = tuple(r["cue_code"] for r in receipts if r["activated"])
    kinds = list(text_evidence.kind_candidates(cues))
    if lexical is not None and not blocked:
        kinds = [kind for kind in kinds if kind in lexical["axes"]["kind"]["candidates"]]
    # The text may narrow a formerly ambiguous lexical reading. Recheck the
    # typed property domains after refinement; a branch cannot erase a tense
    # assertion merely because terminal tanwin selected its noun alternative.
    if kinds and "verb" not in kinds and lexical is not None and not blocked:
        for name in ("tense", "nun"):
            witnesses = [p for p in properties if p["property"] == name
                         and (name == "tense" or p["value"] != "none")]
            if witnesses:
                blockers.append({"code": "PROPERTY_DOMAIN_MISMATCH", "property": name,
                    "expected_kind": "verb", "candidate_kinds": kinds,
                    "values": sorted({p["value"] for p in witnesses}),
                    "support_ids": [p["support_id"] for p in witnesses],
                    "kind_receipt_ids": [r["receipt_id"] for r in receipts if r["activated"]],
                    "identity": identity})
        blocked = bool(blockers)
    hard_conflict = any(b.get("status") == "REJECT" or b["code"] in
                       ("LEXICAL_SOURCE_CONFLICT", "PROPERTY_DOMAIN_MISMATCH")
                        for b in blockers)
    conflicts = hard_conflict or not kinds
    supports = [r["receipt_id"] for r in receipts if r["activated"]]
    kind = _axis(kinds, supports=supports, conflict=conflicts,
                 missing=[] if len(kinds) == 1 else ["INDEPENDENT_KIND_WITNESS"])

    def state(name):
        values = [e["value"] for e in properties if e["property"] == name]
        return int(any(value is True for value in values)) + 2 * int(any(value is False for value in values))

    def categorical(name, domain):
        known = sorted({e["value"] for e in properties if e["property"] == name})
        return list(domain) if not known else known if len(known) == 1 else []

    def property_support(names):
        return [e["support_id"] for e in properties if e["property"] in names]

    models = []
    for k in kinds:
        if k == "particle":
            models.append({"kind": k, "construction": "built"})
        elif k == "noun":
            for resemblance in algebra.possible_bools(state("particle_resemblance")):
                models.append({"kind": k, "construction": "built" if resemblance else "inflected",
                               "particle_resemblance": resemblance})
        else:
            for tense, nun in product(categorical("tense", algebra.TENSES), categorical("nun", algebra.NUNS)):
                row = table["verb_rows"][4 * algebra.TENSES.index(tense) + algebra.NUNS.index(nun)]
                models.append({"kind": k, "tense": tense, "nun": nun,
                               "construction": algebra.CONSTRUCTIONS[row["construction"]]})
    construction = _axis([m["construction"] for m in models], conflict=conflicts,
                         supports=supports + property_support(("particle_resemblance", "tense", "nun")))
    construction["models"] = models
    if construction["status"] == "DEFER":
        construction["missing"] = ["NOUN_CONSTRUCTION_OR_VERB_TENSE_AND_NUN_WITNESS"]
    nominal_values = []
    for k in kinds:
        if k != "noun":
            nominal_values.append("outside_universal_noun")
        else:
            for universal, bearing in product(algebra.possible_bools(state("universal")),
                                              algebra.possible_bools(state("property_bearing"))):
                nominal_values.append("outside_universal_noun" if not universal else
                                      "mushtaq" if bearing else "jins_jamid")
    nominal = _axis(nominal_values, conflict=conflicts,
                    supports=property_support(("universal", "property_bearing")),
                    out=set(nominal_values) == {"outside_universal_noun"})
    nominal["domain"] = "UNIVERSAL_NOMINAL_DENOTATION_NOT_ETYMOLOGY_OR_VERB_CONJUGATION"
    if nominal["status"] == "DEFER":
        nominal["missing"] = ["LEXICAL_UNIVERSAL_AND_PROPERTY_BEARING_WITNESS"]
    cause_states = tuple(state(name) for name in algebra.CAUSE_TRAITS)
    if cause_states not in cause_cache:
        cause_cache[cause_states] = algebra.cause_candidates(cause_states)
    cause = _axis(["diptote" if x else "ordinary" for x in cause_cache[cause_states]],
                  conflict=conflicts, supports=property_support(algebra.CAUSE_TRAITS))
    diptote = deepcopy(cause)
    diptote["cause_prediction"] = {**deepcopy(cause), "domain": "QUALIFIED_INTRINSIC_CAUSE_FORMULA_ONLY"}
    diptote["prerequisites"] = []
    if kinds != ["noun"]:
        diptote["prerequisites"].append("INDEPENDENT_NOUN_WITNESS")
    if construction["status"] != "LICENSED" or construction["candidates"] != ["inflected"]:
        diptote["prerequisites"].append("LICENSED_INFLECTED_NOUN")
    if not conflicts:
        if "noun" not in kinds or (kinds == ["noun"] and construction["candidates"] == ["built"]):
            diptote["status"] = "OUT_OF_DOMAIN"
        elif diptote["prerequisites"] or cause["status"] == "DEFER":
            diptote["status"] = "DEFER"
    # Even exact lexical-form reuse does not transfer the source occurrence's
    # al/idafa or grammatical government. These remain new-occurrence debts.
    diptote["genitive"] = {"status": "DEFER", "candidates": ["fatha", "kasra"],
        "application": "IF_THIS_OCCURRENCE_IS_AN_INFLECTED_DIPTOTE_IN_GENITIVE_CASE",
        "applied_to_occurrence": False, "support_ids": [],
        "prerequisites": ["INDEPENDENT_GENITIVE_CASE_WITNESS", "OCCURRENCE_AL_OR_IDAFA_WITNESS"],
        "context_properties_transferred": False}
    axes = {"kind": kind, "construction": construction, "nominal_semantics": nominal, "diptote": diptote}
    if blocked and not hard_conflict:
        for axis in axes.values():
            if axis["status"] == "LICENSED":
                axis["status"] = "DEFER"
            axis["blocked_by_incomplete_source"] = True
        if diptote["cause_prediction"]["status"] == "LICENSED":
            diptote["cause_prediction"]["status"] = "DEFER"
    return {"reading_id": reading_id, "identity": identity, "axes": axes, "receipts": receipts,
            "linked_properties": properties, "blockers": blockers,
            "lexical_link": None if lexical is None else {
                "source_id": lexical_source.source_id, "source_sha256": lexical_source.sha256,
                "source_reading_id": lexical["reading_id"], "source_occurrence_id": lexical["occurrence_id"],
                "lexeme_span": lexical["lexeme_span"], "match": "EXACT_UTF8_SURFACE",
                "excluded_context_properties": sorted({e["property"] for e in lexical["evidence"]
                                                       if e["property"] in _CONTEXT_PROPERTIES}),
                "authority": "SOURCE_RELATIVE_READING_CANDIDATE"},
            "actual_role": None, "actual_case": None,
            "status": "CONFLICT" if conflicts else "DEFER" if blocked or any(a["status"] == "DEFER" for a in axes.values()) else "READ"}


def _aggregate(readings):
    survivors = [r for r in readings if r["status"] != "CONFLICT"]
    axes = {}
    for name in ("kind", "construction", "nominal_semantics", "diptote"):
        source = survivors or readings
        candidates = [c for r in source for c in r["axes"][name]["candidates"]]
        axis = _axis(candidates, supports=[s for r in source for s in r["axes"][name]["support_ids"]],
                     conflict=not survivors,
                     out=bool(source) and all(r["axes"][name]["status"] == "OUT_OF_DOMAIN" for r in source))
        if survivors and any(r["axes"][name]["status"] == "DEFER" for r in survivors) and axis["status"] == "LICENSED":
            axis["status"] = "DEFER"
        axis["missing"] = sorted({m for r in source for m in r["axes"][name]["missing"]})
        if survivors and any(r["axes"][name]["status"] == "OUT_OF_DOMAIN" for r in survivors) and not all(
                r["axes"][name]["status"] == "OUT_OF_DOMAIN" for r in survivors):
            axis["status"] = "DEFER"
            axis["missing"] = sorted(set(axis["missing"] + ["UNRESOLVED_READING_DOMAIN"]))
        if name == "nominal_semantics":
            axis["domain"] = source[0]["axes"][name]["domain"]
        if name == "diptote":
            axis["genitive"] = deepcopy(source[0]["axes"][name]["genitive"])
            axis["cause_candidates"] = sorted({c for r in source for c in r["axes"][name]["cause_prediction"]["candidates"]})
        axes[name] = axis
    return axes


def _attachments(partition, occurrences):
    by_index = {r["partition_index"]: r for r in occurrences}
    result = []
    for index, run in by_index.items():
        marker = _MARKERS.get(run["surface"])
        if marker is None or marker[0] not in ("imperfect", "preposition"):
            continue
        if index + 2 >= len(partition):
            continue
        gap, target_segment = partition[index + 1:index + 3]
        if gap["kind"] != "spacing" or any(c in gap["surface"] for c in "\n\r\u2028\u2029"):
            continue
        target = by_index.get(index + 2)
        if target is None or target_segment["kind"] != "written_run":
            continue
        expected = "verb" if marker[0] == "imperfect" else "noun"
        onset = any(o["type"] == "imperfect_onset_candidate" for o in target["observations"])
        compatible = (target["axes"]["kind"]["status"] == "LICENSED"
                      and target["axes"]["kind"]["candidates"] == [expected])
        missing = ["GOVERNOR_ACTIVATION_AND_RELATION_SCOPE_WITNESS"]
        if not compatible:
            missing.append("INDEPENDENT_" + expected.upper() + "_READING_WITNESS")
        candidate = {"marker_occurrence_id": run["occurrence_id"],
                     "target_occurrence_id": target["occurrence_id"],
                     "marker_span": run["span"], "target_span": target["span"],
                     "frame": marker[0], "expected_kind": expected, "expected_case": marker[2],
                     "rule_id": marker[1], "status": "CANDIDATE",
                     "proposal_basis": "AUTHORED_ADJACENCY_HEURISTIC; RULE_ATTESTS_MARKER_ONLY",
                     "independent_kind_compatible": compatible, "imperfect_onset_observed": onset,
                     "missing": missing, "kind_constraint_activated": False,
                     "actual_role": None, "actual_case": None,
                     "authority": "ADJACENCY_PROPOSAL_NOT_LEXICAL_CLASS_OR_GOVERNMENT"}
        candidate["candidate_id"] = _id(candidate)
        result.append(candidate)
    return result


def read_text_morphology(text, *, source_id="input", scope="default", lexical_text=None,
                         lexical_source_id="lexical"):
    source = _source(text, source_id, scope)
    if lexical_text is not None and source_id == lexical_source_id:
        raise NabtError("DUPLICATE_SOURCE_ID", "Text and lexical premises need distinct source identities")
    # Replays source windows, never reads word_policy entries for recognition.
    word_policy = replay_word_policy()
    description_policy = descriptions.replay_policy()
    text_evidence.installed_table()
    table = algebra.installed_table()
    rules = {r["id"]: r for r in word_policy["rules"]}
    lexical_source = None if lexical_text is None else descriptions._source(lexical_text, lexical_source_id, scope)
    lexical = None if lexical_source is None else descriptions.read_morphology(
        lexical_text, source_id=lexical_source_id, scope=scope)
    lookup = {}
    if lexical is not None:
        for reading in lexical["readings"]:
            lookup.setdefault(reading["lexeme"], []).append(reading)
    partition = _scan(source)
    occurrences, cause_cache = [], {}
    for index, segment in enumerate(partition):
        if segment["kind"] != "written_run":
            continue
        run = deepcopy(segment)
        run["partition_index"] = index
        run["occurrence_id"] = _id({"span": run["span"], "scope": scope})
        run["segmentation_id"] = _id({"occurrence": run["occurrence_id"], "profile": LANGUAGE_ID,
                                      "segmentation": "ONE_UNSPLIT_WRITTEN_RUN_CANDIDATE"})
        observations, blockers, _ = _observations(source, run)
        run.update(observations=observations, blockers=blockers, encoding=_cell_encoding(run["surface"]))
        matches = lookup.get(run["surface"], [None])
        if len(matches) > MAX_LINKED_READINGS:
            raise resource_limit("Too many lexical alternatives for one occurrence")
        run["readings"] = [_analyse_reading(source, scope, run, match, lexical_source,
                                             table, cause_cache) for match in matches]
        run["axes"] = _aggregate(run["readings"])
        run["actual_role"] = run["actual_case"] = None
        run["status"] = "CONFLICT" if all(r["status"] == "CONFLICT" for r in run["readings"]) else (
            "DEFER" if any(a["status"] == "DEFER" for a in run["axes"].values()) else "READ")
        occurrences.append(run)
    attachments = _attachments(partition, occurrences)
    unused = [] if lexical is None else [r["reading_id"] for r in lexical["readings"]
                                         if not any(r["lexeme"] == o["surface"] for o in occurrences)]
    unscoped = [] if lexical is None else lexical["unscoped_clauses"]
    report = {"language_id": LANGUAGE_ID, "reader_version": READER_VERSION,
              "law_id": text_evidence.LAW_ID, "table_sha256": text_evidence.EXPECTED_TABLE_SHA256,
              "source_id": source.source_id, "source_sha256": source.sha256, "scope": scope,
              "raw_text": source.raw_bytes.decode("utf-8"),
              "lexical_source": None if lexical_source is None else {
                  "source_id": lexical_source.source_id, "sha256": lexical_source.sha256,
                  "raw_text": lexical_source.raw_bytes.decode("utf-8"), "scope": scope,
                  "reader_version": descriptions.READER_VERSION},
              "partition": partition, "occurrences": occurrences, "attachments": attachments,
              "unused_lexical_readings": unused, "unscoped_lexical_clauses": unscoped,
              "status": "CONFLICT" if any(o["status"] == "CONFLICT" for o in occurrences) else
                        "DEFER" if not occurrences or unscoped or attachments or
                        any(o["status"] == "DEFER" for o in occurrences) else "READ",
              "rule_evidence": list(rules.values()), "morphology_rule_evidence": description_policy["rules"],
              "recognition_basis": {"content_word_answer_entries_used": 0,
                                    "functional_marker_forms": list(_MARKERS),
                                    "functional_marker_basis": "AUTHORED_VOCALIZATION_OF_PINNED_GRAMMAR_MARKERS",
                                    "lexical_matching": "EXACT_UTF8_SURFACE_ONLY"},
              "profile_scope": "ORDINARY_NONPOETIC_UNQUOTED_USE; UNSPLIT_RUN_CANDIDATES",
              "facts": [], "semantic_projection": "NONE", "world_truth": "NOT_ESTABLISHED",
              "unimplemented_axes": ["ETYMOLOGICAL_ROOT_DERIVATION", "VERB_CONJUGATION_JAMID_MUTASARRIF"],
              "authority": "REPLAYED_SOURCE_RELATIVE_PRECOMPOSITION_EVIDENCE"}
    _wire(report)
    return report


def verify_text_morphology(report, *, text=None, source_id=None, scope=None,
                           lexical_text=_UNSET, lexical_source_id=None):
    try:
        if type(report) is not dict:
            raise ValueError("not a report")
        premise = report["lexical_source"]
        fresh = read_text_morphology(report["raw_text"] if text is None else text,
            source_id=report["source_id"] if source_id is None else source_id,
            scope=report["scope"] if scope is None else scope,
            lexical_text=(None if premise is None else premise["raw_text"]) if lexical_text is _UNSET else lexical_text,
            lexical_source_id=("lexical" if premise is None else premise["source_id"])
                              if lexical_source_id is None else lexical_source_id)
        if _wire(report) != _wire(fresh):
            raise ValueError("source/receipt/reading mismatch")
        return {"valid": True, "status": "VERIFIED", "source_sha256": fresh["source_sha256"],
                "authority": "SOURCE_BOUND_REPORT_REPLAY_ONLY"}
    except (OSError, KeyError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, "status": "DEFER", "code": error.code}
        return {"valid": False, "status": "REJECT", "code": "INVALID_TEXT_MORPHOLOGY_REPORT"}


def text_morphology_number(report):
    check = verify_text_morphology(report)
    if not check["valid"]:
        raise NabtError(check["code"], "Text morphology report cannot be encoded", status=check["status"])
    return int.from_bytes(b"\x01" + _wire(report), "big")


def decode_text_morphology(number):
    natural(number, "text_morphology_number")
    if number.bit_length() > 8 * (MAX_REPORT_BYTES + 1):
        raise resource_limit("Text morphology number exceeds its byte budget")
    try:
        raw = number.to_bytes((number.bit_length() + 7) // 8, "big")
        if not raw.startswith(b"\x01"):
            raise ValueError("missing sentinel")
        report = json.loads(raw[1:].decode("utf-8"))
        if b"\x01" + _wire(report) != raw or not verify_text_morphology(report)["valid"]:
            raise ValueError("noncanonical or unreplayed report")
        return report
    except (ValueError, UnicodeError, RecursionError) as error:
        if isinstance(error, NabtError):
            raise
        raise NabtError("INVALID_TEXT_MORPHOLOGY_NUMBER", "Number is not a canonical replayed text morphology report") from error
