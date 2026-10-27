"""Source-learned morphology and witnessed, deliberately closed attachments.

Raw input contains no case, role, class or segmentation answer. QAC supplies
independent training witnesses; a small declared grammar builds attachments at
new byte locations. Unresolved readings, missing witnesses and unsupported
frames remain visible. This is not a general Arabic dependency parser.
"""

from copy import deepcopy
from hashlib import sha256
import json

from .corpus_evidence import (VOWELS, lexical_index, lookup_clusters, lookup_key,
                              template_matches)
from .errors import NabtError, resource_limit
from .inflection import (LAW_ID, EXPECTED_TABLE_SHA256, installed_registry,
                         receipt_activated, relation_candidate, sign_candidates)
from .nominal import weak_root_profile
from .text_ir import span_dict
from .word_reader import _scan, _source, _span, replay_policy

LANGUAGE_ID = "nabt.arabic-inflection-frames.v1"
READER_VERSION = "nabt.inflection-reader.v2"
MAX_READINGS = 128
MAX_REPORT_BYTES = 8 * 1024 * 1024
_UNSET = object()
# Grammatical operators are a declared grammar, not answers for content words.
# A supplied conflicting mark rejects a template; the critical mark prevents
# unvocalized man/min or lima/lam from activating a selected interpretation.
_OPERATORS = (
    ("مِنْ", "preposition_object", "min_preposition", (0, "ِ")),
    ("إِلَى", "preposition_object", "min_preposition", None),
    ("عَنْ", "preposition_object", "min_preposition", (1, "ْ")),
    ("عَلَى", "preposition_object", "min_preposition", None),
    ("فِي", "preposition_object", "min_preposition", None),
    ("لَمْ", "imperfect_jussive", "lam_activation", (0, "َ")),
    ("لَنْ", "imperfect_subjunctive", "subjunctive_lan", None),
)


from nabt import foundation

def _wire(value):
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("utf-8", "strict")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise NabtError("INVALID_INFLECTION_REPORT", "Use bounded strict JSON") from error
    if len(raw) > MAX_REPORT_BYTES:
        raise resource_limit("Inflection report exceeds its byte budget")
    return raw


def _id(value):
    return sha256(_wire(value)).hexdigest()


def replay_inflection_policy():
    from importlib.resources import files
    EXPECTED_POLICY_SHA256 = "87d28b0d9a23ea3300f033aeef38884132d4863f4906e57dda1ee490c1365f09"
    base = replay_policy()
    try:
        directory = files("nabt").joinpath("data/source_evidence")
        raw = directory.joinpath("inflection_policy.json").read_bytes()
        if sha256(raw).hexdigest() != EXPECTED_POLICY_SHA256:
            raise ValueError("policy digest differs")
        extra = json.loads(raw)
        for passage in extra["passages"]:
            if passage["source_id"] not in base["sources"]:
                raise ValueError("unknown source identity")
            original = directory.joinpath(passage["source_id"] + ".txt").read_bytes()
            excerpt = original[passage["start"]:passage["end"]]
            if (sha256(original).hexdigest() != passage["source_sha256"] or
                    sha256(excerpt).hexdigest() != passage["span_sha256"] or
                    excerpt.decode("utf-8") != passage["raw_text"]):
                raise ValueError("source passage differs")
        rules = {r["id"]: {"source_id": r["source_id"], "start": r["start"], "end": r["end"],
                            "sha256": r["sha256"]} for r in base["rules"]}
        rules.update({p["rule"]: {k: p[k] for k in ("source_id", "start", "end", "span_sha256")}
                      for p in extra["passages"]})
        return {"policy_sha256": EXPECTED_POLICY_SHA256, "rules": rules}
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Inflection grammar sources cannot be replayed",
                        status="DEFER") from error


def _part(source, run, lo, hi, label):
    raw = run["surface"]
    start = run["span"]["start"] + len(raw[:lo].encode("utf-8"))
    end = run["span"]["start"] + len(raw[:hi].encode("utf-8"))
    return {"kind": label, "surface": raw[lo:hi], "span": span_dict(_span(source, start, end))}


def _annotated_parts(source, run, offset, clusters, entry):
    """Rebuild a source-annotated partition at the new input's byte positions.

    Cluster coordinates are from the declared Arabic lookup projection, never
    from the training record's transliteration or its source byte locations.
    Exact restoration alone does not license grammatical attachment.
    """
    specs = entry["source_parts"]
    kinds = {"verbal_stem", "feminine_subject", "annotated_subject_suffix",
             "annotated_pronominal_suffix", "annotated_emphasis"}
    if type(specs) is not list or not specs or entry.get("annotation_only") is not True:
        raise NabtError("INVALID_LEXICAL_PARTITION", "Annotated parts require an annotation-only entry")
    parts, cursor = [], 0
    for spec in specs:
        lo, hi, kind = spec["start_cluster"], spec["end_cluster"], spec["kind"]
        if (type(lo) is not int or type(hi) is not int or lo != cursor or
                not lo < hi <= len(clusters) or kind not in kinds):
            raise NabtError("INVALID_LEXICAL_PARTITION", "Annotated parts must partition the observed clusters")
        parts.append(_part(source, run, offset + clusters[lo][2], offset + clusters[hi - 1][3], kind))
        cursor = hi
    if cursor != len(clusters):
        raise NabtError("INVALID_LEXICAL_PARTITION", "Annotated parts lost observed clusters")
    return parts


def _nun_readings(source, run, offset, clusters, entry):
    """Bind each nun witness to this reading, without inventing deleted spans."""
    readings = []
    kinds = {"radical", "five_verb_raf", "nominal_dual_plural", "feminine_subject", "emphasis"}
    for spec in entry["nun_positions"]:
        index, realization = spec["cluster_index"], spec["realization"]
        if spec["kind"] not in kinds or realization not in ("present", "deleted", "unresolved"):
            raise NabtError("INVALID_NUN_WITNESS", "Use a declared source-qualified nun kind and realization")
        reading = {**spec, "span": None, "surface": None,
                   "support_ids": [s["record_id"] for s in entry["supports"]]}
        if realization == "present":
            if type(index) is not int or not 0 <= index < len(clusters) or clusters[index][0] != "ن":
                raise NabtError("INVALID_NUN_WITNESS", "A present nun must point to an observed nun cluster")
            part = _part(source, run, offset + clusters[index][2], offset + clusters[index][3], spec["kind"])
            reading.update(span=part["span"], surface=part["surface"])
        elif index is not None:
            raise NabtError("INVALID_NUN_WITNESS", "A deleted or unresolved nun has no observed position")
        readings.append(reading)
    return readings


def _prefix_options(surface):
    clusters = lookup_clusters(surface)
    if clusters is None:
        return []
    result = [(0, [], None, False)]
    key = "".join(c[0] for c in clusters)
    def plain_marks(cluster, allowed):
        return cluster[1] <= set(allowed)
    def article_ok(start):
        return plain_marks(clusters[start], "َ") and plain_marks(clusters[start + 1], "ْ")
    if key.startswith("ال") and len(clusters) > 2 and article_ok(0):
        result.append((clusters[2][2], [(0, clusters[1][3], "article")], None, True))
    if key[0] in "بكل" and len(clusters) > 1:
        vowel = "َ" if key[0] == "ك" else "ِ"
        # A prep prefix is an alternative contingent on a known nominal stem.
        # Contradictory explicit vowels never get silently stripped.
        if plain_marks(clusters[0], vowel):
            end = clusters[0][3]
            result.append((end, [(0, end, "preposition")], "preposition_object", False))
            if key[1:3] == "ال" and len(clusters) > 3 and article_ok(1):
                result.append((clusters[3][2], [(0, end, "preposition"), (end, clusters[2][3], "article")],
                               "preposition_object", True))
            # Lam + al contracts only the article's alif. The absent alif is
            # not a source span; the two actual lam spans remain disjoint.
            if key.startswith("لل") and len(clusters) > 2 and plain_marks(clusters[1], "ْ"):
                result.append((clusters[2][2], [(0, end, "preposition"), (end, clusters[1][3], "contracted_article")],
                               "preposition_object", True))
    return result


def _surface_accepts(row, stem, entry):
    clusters = lookup_clusters(stem)
    key = lookup_key(stem)
    last = clusters[-1][1] & VOWELS
    cls, case, sign = row["class"], row["case"], row["sign"]
    if cls in (2, 3):
        required = ("ان" if cls == 2 else "ون") if case == 1 else "ين"
        if not key.endswith(required):
            return False
        # Dual nun is kasra; sound-plural nun is fatha, not the case sign.
        return not last or last == ({"ِ"} if cls == 2 else {"َ"})
    if cls in (9, 10, 11):
        deleted = entry["variant"] == "nun_deleted_from_retained_base"
        if (sign == 8) != deleted:
            return False
        if not deleted:
            return not last or last == ({"ِ"} if cls == 9 else {"َ"})
        return True
    if cls in (12, 13, 14) and sign == 9:
        if entry["variant"] != "weak_deleted_from_full_base":
            return False
        residual = {12: "َ", 13: "ُ", 14: "ِ"}[cls]
        return not last or last == {residual}
    if entry["variant"] == "weak_deleted_from_full_base":
        return False
    if row["mode"] == 1:
        # An estimated damma is not a written damma on alif/yaa/waw.
        allowed = set("ً") if cls == 6 else set()
        return not last or bool(last & allowed)
    if sign <= 3:
        expected = (set("ٌُ"), set("ًَ"), set("ٍِ"), set("ْ"))[sign]
        return not last or bool(last & expected)
    return True


def _read_run(source, scope, run, index, model_summary, policy):
    occurrence = _id({"source": source.sha256, "source_id": source.source_id, "scope": scope, "span": run["span"]})
    result = {**run, "occurrence_id": occurrence, "readings": [], "status": "DEFER", "obligations": []}
    if run["kind"] == "quotation":
        result["status"] = "MENTION"
        result["obligations"] = ["MENTION_IS_NOT_USE"]
        return result
    observed = lookup_clusters(run["surface"])
    if observed is None:
        result["obligations"] = ["SUPPORTED_ARABIC_LOOKUP_PROFILE"]
        return result
    for template, relation, rule, critical in _OPERATORS:
        if not template_matches(run["surface"], template, mutable_last=False):
            continue
        qualified = critical is None or critical[1] in observed[critical[0]][1]
        key = {"source": source.sha256, "scope": scope, "occurrence": occurrence, "operator": template,
               "policy": policy["policy_sha256"]}
        rid = _id(key)
        result["readings"].append({"reading_id": rid, "kind": "particle", "construction": "built",
                                   "operator_relation": relation, "operator_rule": rule, "operator_qualified": qualified,
                                   "segmentation_id": _id([rid, run["span"]]),
                                   "segmentation": {"parts": [_part(source, run, 0, len(run["surface"]), "operator")],
                                                    "coverage_valid": True, "licensed": qualified,
                                                    "basis": "PINNED_OPERATOR_GRAMMAR"},
                                   "lexical_features": {}, "sign_candidates": [], "nun_readings": [],
                                   "actual_role": None, "actual_case": None, "local_case": None,
                                   "obligations": [] if qualified else ["OPERATOR_VOCALIZATION_EVIDENCE"]})
    for offset, prefix_specs, prefix_relation, article in _prefix_options(run["surface"]):
        stem_text = run["surface"][offset:]
        matching_text = stem_text
        stem_observed = lookup_clusters(stem_text)
        if article and stem_observed and stem_observed[0][0] in "تثدذرزسشصضطظلن":
            end = stem_observed[0][3]
            matching_text = stem_text[:end].replace("ّ", "") + stem_text[end:]
        for encoded in index.get(lookup_key(stem_text), ()):
            entry = json.loads(encoded)
            annotation_only = entry.get("annotation_only", False)
            if prefix_specs and (entry["kind"] != "noun" or entry["pos"] in ("PRON", "DEM", "REL")):
                continue
            if not template_matches(matching_text, entry["template"],
                                    mutable_last=not annotation_only and entry["construction"] != "built"
                                    and entry["nun"] != "five_verb_raf"):
                continue
            parts = [_part(source, run, lo, hi, label) for lo, hi, label in prefix_specs]
            stem_part = _part(source, run, offset, len(run["surface"]), "nominal_stem" if entry["kind"] == "noun" else "verbal_form")
            # Distinguish a grammatical nun from the stem without pretending
            # that reconstruction alone established its type.
            stem_clusters = lookup_clusters(stem_text)
            if "source_parts" in entry:
                parts.extend(_annotated_parts(source, run, offset, stem_clusters, entry))
            elif entry["nun"] in ("nominal_dual_plural", "five_verb_raf", "feminine_subject") and lookup_key(stem_text).endswith("ن"):
                cut = offset + stem_clusters[-1][2]
                if cut > offset:
                    parts.extend([_part(source, run, offset, cut, stem_part["kind"]),
                                  _part(source, run, cut, len(run["surface"]), entry["nun"])])
                else:
                    parts.append(stem_part)
            else:
                parts.append(stem_part)
            if (b"".join(p["surface"].encode("utf-8") for p in parts) != run["surface"].encode("utf-8") or
                    any(a["span"]["end"] != b["span"]["start"] for a, b in zip(parts, parts[1:]))):
                raise NabtError("INVALID_SEGMENTATION", "Proposed segmentation does not conserve the source")
            segmentation_id = _id({"occurrence": occurrence, "parts": parts, "rule": entry["form_rule"],
                                   "lexical": entry["lexical_id"], "model": model_summary["inventory_sha256"]})
            identity = {"source_id": source.source_id, "source_sha256": source.sha256, "scope": scope,
                        "occurrence_id": occurrence, "span": run["span"], "segmentation_id": segmentation_id,
                        "lexical_id": entry["lexical_id"], "law": LAW_ID}
            rid = _id(identity)
            # Absence of article is observable in this completed segmentation.
            # Absence of idafa is a separate contextual question, not default 2.
            al = 1 if article else 2
            candidates = sign_candidates(entry["class_candidates"], cases=entry["possible_cases"], al=al, idhafa=0)
            candidates = [r for r in candidates if _surface_accepts(r, stem_text, entry)]
            weakness = None
            if entry["root"] and len(entry["root"]) == 3:
                weakness = weak_root_profile(entry["root"])
            nuns = _nun_readings(source, run, offset, stem_clusters, entry)
            obligations = []
            if entry["construction"] is None:
                obligations.append("CONSTRUCTION_EVIDENCE")
            if entry.get("declension_boundary"):
                obligations.append(entry["declension_boundary"])
            if entry.get("suffix_boundary"):
                obligations.append(entry["suffix_boundary"])
            if entry["kind"] == "noun" and entry["gender"] is None:
                obligations.append("LEXICAL_GENDER_EVIDENCE")
            if entry["number"] == "plural" and not entry["singular_witnesses"]:
                obligations.append("SINGULAR_LINK_EVIDENCE")
            if not candidates and entry["construction"] == "inflected":
                obligations.append("OBSERVED_FORM_CONFLICTS_WITH_CONDITIONAL_SIGN_LAW")
            result["readings"].append({"reading_id": rid, "identity": identity, "kind": entry["kind"],
                "construction": entry["construction"], "segmentation_id": segmentation_id,
                "annotation_only": annotation_only, "suffix_boundary": entry.get("suffix_boundary"),
                "construction_basis": entry.get("construction_basis", "annotated_verbal_or_pronominal_paradigm" if entry["construction"] else None),
                "segmentation": {"parts": parts, "coverage_valid": True, "licensed": not annotation_only,
                                 "basis": "SOURCE_ANNOTATED_STEM_SUFFIX_PARTITION" if annotation_only else "TRAINING_LEXICAL_WITNESS_AND_DECLARED_FORM_RULE", "form_rule": entry["form_rule"],
                                 "support_ids": [s["record_id"] for s in entry["supports"]]},
                "stem_span": stem_part["span"], "stem_surface": stem_text,
                "lexical_features": {k: entry[k] for k in ("pos", "lemma", "root", "gender", "number", "person", "aspect", "voice", "nominal_form", "singular_witnesses")},
                "weak_root_profile": weakness, "class_candidates": entry["class_candidates"],
                "variant": entry["variant"], "base_form": entry.get("base_form"), "nun_readings": nuns,
                "support_records": entry["supports"], "construction_supports": entry.get("construction_supports", entry["supports"]),
                "al_evidence": al, "prefix_relation": prefix_relation, "sign_candidates": candidates,
                "actual_role": None, "actual_case": None, "local_case": None, "obligations": obligations})
            if len(result["readings"]) > MAX_READINGS:
                raise resource_limit("Lexical ambiguity exceeds the reading budget", maximum=MAX_READINGS)
    if result["readings"]:
        result["status"] = "SOURCE_QUALIFIED_ALTERNATIVES"
    else:
        result["obligations"].append("INDEPENDENT_LEXICAL_ATTESTATION")
    return result


def _closed(segments):
    bounded = list(segments)
    while bounded and bounded[0]["kind"] == "spacing":
        bounded.pop(0)
    while bounded and bounded[-1]["kind"] == "spacing":
        bounded.pop()
    content = [s for s in bounded if s["kind"] != "spacing"]
    if any(s["kind"] == "spacing" and any(c not in " \t" for c in s["surface"]) for s in bounded):
        return False
    if content and content[-1]["kind"] == "punctuation" and content[-1]["surface"] in (".", "؟", "!"):
        content = content[:-1]
    return bool(content) and all(s["kind"] == "written_run" for s in content)


def _relation(source, scope, head, reading, label, policy, *, blocked=False, closed_idafa=False):
    law = relation_candidate(label, kind=reading["kind"], construction=reading["construction"])
    target = {**reading["identity"], "span": reading["stem_span"],
              "occurrence_span": reading["identity"]["span"], "reading_id": reading["reading_id"]}
    head_binding = {"source_id": source.source_id, "source_sha256": source.sha256, "scope": scope,
                    "span": head["span"], "reading_id": head["reading_id"], "segmentation_id": head["segmentation_id"],
                    "occurrence_id": head["occurrence_id"], "rule_id": head["rule"]}
    same = all(head_binding[k] == target[k] for k in ("source_id", "source_sha256", "scope"))
    distinct = head["span"]["end"] <= target["span"]["start"]
    evidence = [{"kind": "source_grammar", "rule": head["rule"], "passage": policy["rules"][head["rule"]]},
                {"kind": "head_occurrence", **head_binding}, {"kind": "dependent_occurrence", **target},
                {"kind": "lexical_source", "records": reading["support_records"]}]
    rows = sign_candidates(reading["class_candidates"], cases=(law["case"],), al=reading["al_evidence"],
                           idhafa=2 if closed_idafa else 0)
    # Reuse the already checked observed variants, including deleted carriers.
    existing = {(r["class"], r["case"], r["sign"], r["mode"], r["origin"]) for r in reading["sign_candidates"]}
    rows = [r for r in rows if (r["class"], r["case"], r["sign"], r["mode"], r["origin"]) in existing]
    form_ok = reading["construction"] == "built" or bool(rows)
    rule_match = {"min_preposition": "preposition_object", "lam_activation": "imperfect_jussive",
                  "subjunctive_lan": "imperfect_subjunctive"}.get(head["rule"]) == label
    bits = (same and distinct, rule_match, True, blocked or not form_ok,
            bool(evidence), bool(reading["support_records"]), law["compatible"], reading["construction"] is not None)
    mask = sum((1 << i) for i, b in enumerate(bits) if b)
    activated = receipt_activated(mask)
    relation = {"relation_id": _id([head_binding, target, label, evidence]), "label": label,
                "head": head_binding, "dependent": target, "supports": evidence, "receipt_mask": mask,
                "activated": activated, "case": law["case"], "case_name": law["case_name"],
                "case_domain": law["case_domain"], "sign_candidates": rows,
                "status": "LICENSED_IN_DECLARED_FRAME" if activated else "DEFER",
                "authority": "SOURCE_RELATIVE_ATTACHMENT_NOT_WORLD_TRUTH"}
    if activated:
        reading["actual_role"] = label
        reading["actual_case"] = law["case_name"] if law["case_domain"] == "inflected_case" else None
        reading["local_case"] = law["case_name"] if law["case_domain"] == "local_case" else None
        reading["sign_candidates"] = rows
    return relation


def read_inflection(text, *, lexical_model=None, source_id="input", scope="default"):
    foundation.require_foundation('nabt.inflection_reader.read_inflection')
    installed_registry()
    policy = replay_inflection_policy()
    source = _source(text, source_id, scope)
    index, model_summary = ({}, None) if lexical_model is None else lexical_index(lexical_model)
    segments = _scan(source)
    occurrences = [_read_run(source, scope, s, index, model_summary, policy) for s in segments
                   if s["kind"] in ("written_run", "quotation")]
    relations = []
    closed = _closed(segments)
    if closed and len(occurrences) == 1:
        for reading in occurrences[0]["readings"]:
            if reading.get("prefix_relation") and not reading.get("annotation_only"):
                part = next(p for p in reading["segmentation"]["parts"] if p["kind"] == "preposition")
                head = {"span": part["span"], "reading_id": _id([reading["reading_id"], "prep"]),
                        "segmentation_id": reading["segmentation_id"], "rule": "min_preposition",
                        "occurrence_id": occurrences[0]["occurrence_id"]}
                relations.append(_relation(source, scope, head, reading, "preposition_object", policy, closed_idafa=True))
    elif closed and len(occurrences) == 2:
        governors = [r for r in occurrences[0]["readings"] if r.get("operator_relation")]
        for operator in governors:
            for reading in occurrences[1]["readings"]:
                if reading["kind"] == "particle" or reading.get("prefix_relation") or reading.get("annotation_only"):
                    continue
                if operator["operator_relation"].startswith("imperfect_") and reading["lexical_features"].get("aspect") != "IMPF":
                    continue
                head = {"span": occurrences[0]["span"], "reading_id": operator["reading_id"],
                        "segmentation_id": operator["segmentation_id"], "rule": operator["operator_rule"],
                        "occurrence_id": occurrences[0]["occurrence_id"]}
                relations.append(_relation(source, scope, head, reading, operator["operator_relation"], policy,
                                           blocked=not operator["operator_qualified"], closed_idafa=True))
    assignments = [{"reading_id": r["reading_id"], "occurrence_id": o["occurrence_id"],
                    "role": r["actual_role"], "inflected_case": r["actual_case"], "local_case": r["local_case"]}
                   for o in occurrences for r in o["readings"] if r["actual_role"] is not None]
    # Assignments belong to correlated readings. Do not collapse an unsupported
    # alternative into the successful alternative's actual role or case.
    report = {"schema_version": 1, "law_id": LAW_ID, "table_sha256": EXPECTED_TABLE_SHA256,
              "language_id": LANGUAGE_ID, "reader_version": READER_VERSION,
              "source_id": source.source_id, "source_sha256": source.sha256, "scope": scope,
              "raw_text": source.raw_bytes.decode("utf-8"), "lexical_source": model_summary,
              "policy_sha256": policy["policy_sha256"], "source_partition": segments,
              "occurrences": occurrences, "relations": relations, "assignments": assignments,
              "frame_status": "CLOSED_FRAME_LANGUAGE" if closed and len(occurrences) <= 2 else "OUTSIDE_CLOSED_FRAME_LANGUAGE",
              "status": "LICENSED_READINGS" if assignments else "DEFER", "semantic_facts": [],
              "authority": "CONDITIONAL_ON_TRAINING_ANNOTATIONS_AND_DECLARED_CLOSED_FRAME_LANGUAGE",
              "limitations": ["NO_GENERAL_DEPENDENCY_PARSE", "NO_TARGET_ANNOTATION_LABELS",
                              "NO_SINGULAR_WITHOUT_SEPARATE_ATTESTATION", "NO_WEAK_DELETION_WITHOUT_FULL_BASE",
                              "NO_EXTERNAL_REFERENT_OR_WORLD_JUDGMENT"]}
    _wire(report)
    return report


def verify_inflection(report, *, text=_UNSET, lexical_model=None, source_id=None, scope=None):
    """Replay against independently supplied corpus bytes; None withdraws them."""
    foundation.require_foundation('nabt.inflection_reader.verify_inflection')
    try:
        if type(report) is not dict:
            raise ValueError("report type")
        fresh = read_inflection(report["raw_text"] if text is _UNSET else text, lexical_model=lexical_model,
                                source_id=report["source_id"] if source_id is None else source_id,
                                scope=report["scope"] if scope is None else scope)
        if _wire(fresh) != _wire(report):
            raise ValueError("replay differs")
        return {"valid": True, "status": "VERIFIED", "source_sha256": fresh["source_sha256"],
                "authority": "SOURCE_AND_TRAINING_REPLAY_ONLY"}
    except (OSError, KeyError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, "status": "DEFER", "code": error.code}
        return {"valid": False, "status": "REJECT", "code": "INVALID_INFLECTION_REPORT"}
