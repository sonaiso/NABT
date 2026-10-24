"""Source-bound composition for a declared subset of Arabic constructions.

This module proposes whole readings from the original tokens. The conditional
Lean law checks their roles, agreement, operator scope and evidence gates.
Unknown lexical features and competing attachments remain alternatives; no
case label, dependency or expected answer is accepted as an input premise.
"""

from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
import re

from .corpus_evidence import (ROOT_BW, _feature, _receipt, buckwalter_to_arabic,
    lookup_clusters, lookup_key, template_matches)
from .corpus_sources import read_corpus
from .discourse_context import identity, wire, profile_compatibility
from .discourse_reader import _profile, _synthetic_reading, _slice
from .construction_laws import (LAW_ID, EXPECTED_TABLE_SHA256, role_case,
    construction_allowed, agreement_status, idafa_head_status,
    complement_an_policy, scoped_projection_allowed, identity_preservation_allowed,
    operator_slots)
from .errors import NabtError, resource_limit
from .text_ir import span_dict
from .word_reader import _span

MAX_NP_TOKENS = 8
MAX_OPTIONS = 128
CASES = ("nasb", "raf", "jarr", "jazm")


def _support(reader, rule):
    return {"kind": "source_construction_grammar", "rule": rule,
            "law_id": LAW_ID, "law_sha256": EXPECTED_TABLE_SHA256,
            "policy_sha256": reader.construction_policy["policy_sha256"],
            "passage": reader.construction_policy["rules"][rule]}


def _limit(rows):
    if len(rows) > MAX_OPTIONS:
        raise resource_limit("Construction alternatives exceed their budget", maximum=MAX_OPTIONS)
    return rows


def _definite(reading, *, complement=None):
    pos = reading["lexical_features"].get("pos")
    if pos in ("PN", "PRON", "DEM", "REL") or reading.get("al_evidence") == 1:
        return "definite"
    if complement is not None:
        return complement
    if (pos in ("N", "ADJ") and reading.get("al_evidence") == 2 and
            reading.get("segmentation", {}).get("licensed") and
            not reading.get("person_evidence", {}).get("attached_pronouns")):
        return "indefinite"
    return None


def _axis(left, right):
    if left is None or right is None or left == "unknown" or right == "unknown":
        return "possible"
    return "confirmed" if left == right else "conflict"


def _agreement(left, right, left_definite, right_definite):
    lp, rp = _profile(left), _profile(right)
    return agreement_status(case="confirmed", definiteness=_axis(left_definite, right_definite),
                            gender=_axis(lp.get("gender"), rp.get("gender")),
                            number=_axis(lp.get("number"), rp.get("number")))


def _reading_obligations(reading):
    result = []
    if reading.get("construction") not in ("built", "inflected"):
        result.append("CONSTRUCTION_EVIDENCE_REQUIRED")
    if not reading.get("segmentation", {}).get("licensed"):
        result.append("COMPLETE_NOMINAL_SEGMENTATION_REQUIRED")
    return result


def _np_atom(reader, token, role, head):
    rows = []
    for option in reader.referents(token, role, head=head):
        reading = option["reading"]
        if reading.get("prefix_relation"):
            continue
        rows.append({"root": token, "reading": reading, "entity": option["entity"],
            "reference": option["reference"], "assignment": option["assignment"],
            "refs": [option["reference"]], "assignments": [option["assignment"]],
            "readings": [reading], "relations": [], "restriction": [],
            "obligations": _reading_obligations(reading), "supports": [],
            "definiteness": _definite(reading)})
    return rows


def _relation(kind, head, dependent, **extra):
    return {"kind": kind, "head_span": head["span"], "dependent_span": dependent["span"], **extra}


def _append_np(base, *, reading, assignment, relation, support, reference=None,
               restriction=None, obligations=()):
    result = deepcopy(base)
    result["readings"].append(reading)
    result["assignments"].append(assignment)
    result["relations"].append(relation)
    result["supports"].append(support)
    result["obligations"].extend(obligations)
    if reference is not None:
        result["refs"].append(reference)
    if restriction is not None:
        result["restriction"].append(restriction)
    return result


def noun_phrases(reader, tokens, role, *, head=None, depth=0, _root_options=None):
    """Enumerate bounded NPs, retaining distinct heads and qualifier scopes.

    The internal preposition producer may supply already replayed root rows
    for a prefix-bearing token. Their source segmentation and genitive role
    stay intact while the same adjective/idafa/emphasis rules compose its NP.
    No external report or proposed grammatical label supplies these rows.
    """
    if not tokens or len(tokens) > MAX_NP_TOKENS or depth > 6:
        return []
    if len(tokens) == 1:
        return (_np_atom(reader, tokens[0], role, head) if _root_options is None
                else deepcopy(_root_options))
    results = []
    # A semantic idafa has a separately qualified, independently referenced
    # head. No ownership or new individual is manufactured from the phrase.
    roots = (_np_atom(reader, tokens[0], role, head) if _root_options is None else deepcopy(_root_options))
    for base in roots:
        reading = base["reading"]
        if reading["lexical_features"].get("pos") != "N":
            continue
        clusters = lookup_clusters(reading["stem_surface"])
        tanwin = any(c in reading["stem_surface"] for c in "ًٌٍ")
        # Unwritten short vowels are not negative observations. This new
        # composed NP production requires an overt non-tanwin terminal mark;
        # the earlier simple idafa reader retains its separately declared
        # conditional profile. No missing receipt is called observed absence.
        terminal_marks = clusters[-1][1] & set("ًٌٍَُِْ")
        if not tanwin and not terminal_marks:
            continue
        nun = any(n["kind"] == "nominal_dual_plural" and n["realization"] == "present"
                  for n in reading.get("nun_readings", []))
        nun_state = ("affirmed" if nun else "denied" if
            reading.get("class_candidates") and not any(c in (2, 3) for c in reading["class_candidates"]) else "unknown")
        state = idafa_head_status("semantic", "affirmed" if tanwin else "denied",
            nun_state, "affirmed" if reading.get("al_evidence") == 1 else
            "denied" if reading.get("al_evidence") == 2 else "unknown")
        if state == "conflict":
            continue
        for complement in noun_phrases(reader, tokens[1:], "idafa_complement", head=tokens[0], depth=depth + 1):
            assigned = reader.assignment(base.get("assignment_token", tokens[0]), reading, role, head=head, idhafa=True)
            relation = _relation("idafa", tokens[0], complement["root"],
                complement_span=complement["root"]["span"],
                complement_reference=complement["reference"]["reference_id"],
                head_referent=base["entity"], ownership_asserted=False,
                head_reading_id=reading["reading_id"], dependent_reading_id=complement["reading"]["reading_id"])
            qualifier = {"kind": "idafa", "complement": complement["entity"]}
            if complement["restriction"]:
                qualifier["qualifiers"] = complement["restriction"]
            row = {**deepcopy(base), "assignment": assigned,
                "assignments": [assigned] + complement["assignments"],
                "refs": base["refs"] + complement["refs"], "readings": base["readings"] + complement["readings"],
                "relations": [relation] + complement["relations"], "restriction": [qualifier],
                "supports": [_support(reader, "idafa_chain")] + complement["supports"],
                "obligations": base["obligations"] + complement["obligations"] +
                    ([] if state == "confirmed" else ["IDFA_HEAD_RESTRICTIONS_NOT_WITNESSED"]),
                "definiteness": _definite(reading, complement=complement["definiteness"])}
            if complement.get("substitution_unresolved"):
                row["substitution_unresolved"] = True
            results.append(row)
            _limit(results)
    # Restrictive true adjectives. Causal adjectives and nonhuman-plural
    # agreement require a different witnessed regime, not an equality guess.
    for base in noun_phrases(reader, tokens[:-1], role, head=head, depth=depth + 1,
                             _root_options=_root_options):
        token = tokens[-1]
        inherited = CASES.index(base["assignment"]["required_case"])
        for reading in reader.readings(token):
            if (reading["kind"] != "noun" or reading.get("annotation_only") or
                    reading.get("prefix_relation") or reading.get("person_evidence", {}).get("attached_pronouns")):
                continue
            pos = reading["lexical_features"].get("pos")
            if pos == "ADJ":
                agreement = _agreement(base["reading"], reading, base["definiteness"], _definite(reading))
                assigned = reader.assignment(token, reading, "naat", head=base["root"], inherited_case=inherited)
                obligations = _reading_obligations(reading)
                if agreement != "confirmed":
                    obligations.append("CONSTRUCTION_CONFLICT" if agreement == "conflict" else "NAAT_AGREEMENT_EVIDENCE_REQUIRED")
                relation = _relation("naat", base["root"], token, agreement=agreement,
                    head_reading_id=base["reading"]["reading_id"], dependent_reading_id=reading["reading_id"],
                    modified_role=role, regime="true_direct_agreement")
                results.append(_append_np(base, reading=reading, assignment=assigned, relation=relation,
                    support=_support(reader, "naat_agreement"), obligations=obligations,
                    restriction={"kind": "naat", "target": base["entity"], "role": role,
                                 "predicate": reading["lexical_features"]["lemma"]}))
                _limit(results)
        # Total apposition is bounded to DEM + independently co-referential
        # proper name. Adjacency never creates the identity premise.
        if base["reading"]["lexical_features"].get("pos") == "DEM":
            for dep in _np_atom(reader, token, role, head):
                if dep["reading"]["lexical_features"].get("pos") != "PN":
                    continue
                same = base["entity"] is not None and base["entity"] == dep["entity"]
                allowed = identity_preservation_allowed("badal_total", relation_licensed=True, identity_licensed=same)
                obligations = dep["obligations"] + ([] if allowed else
                    ["CONSTRUCTION_CONFLICT" if base["entity"] and dep["entity"] else "BADAL_INDEPENDENT_IDENTITY_REQUIRED"])
                assigned = reader.assignment(token, dep["reading"], "badal", head=base["root"], inherited_case=inherited)
                results.append(_append_np(base, reading=dep["reading"], assignment=assigned,
                    reference=dep["reference"], support=_support(reader, "badal_identity"), obligations=obligations,
                    relation=_relation("badal", base["root"], token, subtype="total",
                        identity_basis="independent_named_and_deictic_references", identity_preserved=allowed,
                        head_reading_id=base["reading"]["reading_id"], dependent_reading_id=dep["reading"]["reading_id"])))
                _limit(results)
        if lookup_key(token["surface"]) == lookup_key(base["root"]["surface"]):
            for dep in _np_atom(reader, token, role, head):
                if (dep["reading"]["lexical_features"].get("lemma") != base["reading"]["lexical_features"].get("lemma") or
                        dep["entity"] is None or dep["entity"] != base["entity"]):
                    continue
                assigned = reader.assignment(token, dep["reading"], "tawkeed", head=base["root"], inherited_case=inherited)
                results.append(_append_np(base, reading=dep["reading"], assignment=assigned,
                    reference=dep["reference"], support=_support(reader, "tawkeed_reference"), obligations=dep["obligations"],
                    relation=_relation("tawkeed", base["root"], token, subtype="lexical_repetition",
                        identity_preserved=True, head_reading_id=base["reading"]["reading_id"],
                        dependent_reading_id=dep["reading"]["reading_id"])))
                _limit(results)
        results.extend(_semantic_emphasis(reader, base, token, inherited))
        results.extend(_apposition_candidates(reader, base, token, inherited))
        results.extend(_part_substitution_candidates(reader, base, token, inherited))
        _limit(results)
    return results


def _semantic_emphasis(reader, base, token, inherited):
    """Full host/suffix evidence plus a local, same-entity pronominal return."""
    if base["entity"] is None or base["definiteness"] != "definite":
        return []
    results = []
    for reading in reader.readings(token):
        if lookup_key(reading["lexical_features"].get("lemma") or "") not in ("نفس", "عين"):
            continue
        suffixes = reading.get("person_evidence", {}).get("attached_pronouns", [])
        if len(suffixes) != 1 or not suffixes[0]["licensed"] or suffixes[0]["attachment_candidates"] != ["possessive"]:
            continue
        suffix = suffixes[0]
        raw = suffix["person_profile"]
        if raw is None or raw["person"] != 3:
            continue
        profile = {"person": 3, "gender": ("masculine", "feminine", None)[raw["gender"]],
                   "number": ("singular", "dual", "plural")[raw["number"]]}
        clusters = lookup_clusters(token["surface"])
        part = _slice(reader.source, token, clusters[suffix["start_cluster"]][2],
                      clusters[suffix["end_cluster"] - 1][3], "emphasis_pronominal_return")
        reference = reader.reference(part["surface"], origin="relative_return", profile=profile,
            context=reader.context, mentions=reader.mentions, span=part["span"], scope=reader.scope,
            return_entity=base["entity"])
        same = reference["bound_entity_id"] == base["entity"]
        obligations = _reading_obligations(reading)
        if not identity_preservation_allowed("tawkeed", relation_licensed=True, identity_licensed=same):
            obligations.append("TAWKEED_SAME_REFERENT_PRONOUN_REQUIRED")
        if profile_compatibility(profile, _profile(base["reading"])) == "conflict":
            obligations.append("CONSTRUCTION_CONFLICT")
        assigned = reader.assignment(token, reading, "tawkeed", head=base["root"], inherited_case=inherited, idhafa=True)
        pronoun = _synthetic_reading(part, pos="PRON", profile=profile, rule="tawkeed_reference")
        pronoun["support_records"] = reading["support_records"]
        row = _append_np(base, reading=reading, assignment=assigned, reference=reference,
            support=_support(reader, "tawkeed_reference"), obligations=obligations,
            restriction={"kind": "tawkeed", "subtype": "semantic_self", "owner": base["entity"],
                         "predicate": reading["lexical_features"]["lemma"]},
            relation=_relation("tawkeed", base["root"], token, subtype="semantic_self",
                identity_preserved=same, pronoun_span=part["span"],
                head_reading_id=base["reading"]["reading_id"], dependent_reading_id=reading["reading_id"]))
        row["readings"].append(pronoun)
        row["assignments"].append(reader.assignment(part, pronoun, "idafa_complement", head=token))
        results.append(row)
    return results


def _apposition_candidates(reader, base, token, inherited):
    """Retain explanatory/substitution proposals without acquiring identity.

    A definite common noun followed by a proper name can propose either
    construction. Their independent references, intended attachment and
    substitution conditions are still needed. This never merges two names
    in the context or turns same-case adjacency into an accepted judgment.
    """
    if ("explanatory_apposition" not in reader.construction_policy["rules"] or
            base["reading"]["lexical_features"].get("pos") != "N" or
            base["definiteness"] != "definite"):
        return []
    results = []
    for dep in _np_atom(reader, token, base["assignment"]["role"], None):
        if dep["reading"]["lexical_features"].get("pos") != "PN":
            continue
        obligations = dep["obligations"] + ["APPOSITION_ATTACHMENT_AND_INTENTION_REQUIRED",
                                             "APPOSITION_INDEPENDENT_IDENTITY_REQUIRED"]
        alternative_group = identity([base["root"]["token_id"], token["token_id"], "apposition"])
        for kind in ("badal", "bayan"):
            row = deepcopy(base)
            row["readings"].append(dep["reading"])
            row["refs"].append(dep["reference"])
            row["obligations"].extend(obligations)
            row["supports"].append(_support(reader, "explanatory_apposition"))
            row["relations"].append(_relation(kind, base["root"], token,
                subtype="unresolved_apposition", evidence_status="CANDIDATE_ONLY",
                alternative_group=alternative_group, identity_preserved=False,
                head_entity=base["entity"], dependent_entity=dep["entity"],
                required_case=CASES[inherited],
                head_reading_id=base["reading"]["reading_id"], dependent_reading_id=dep["reading"]["reading_id"]))
            if kind == "badal":
                row["assignments"].append(reader.assignment(token, dep["reading"], "badal",
                    head=base["root"], inherited_case=inherited))
            # Bayan is not an installed activated role. Its proposed case
            # agreement is recorded above; it is not relabeled as badal.
            row["substitution_unresolved"] = True
            results.append(row)
    return results


def _part_substitution_candidates(reader, base, token, inherited):
    """Preserve possible part/association readings with no part denotation.

    A licensed possessive return is evidence of the suffix's referent only.
    The noun's relation to the whole and the speaker's substitution intent
    remain open. Both alternatives block event projection about the whole.
    """
    if base["entity"] is None or base["definiteness"] != "definite":
        return []
    results = []
    for reading in reader.readings(token):
        if (reading["kind"] != "noun" or reading["lexical_features"].get("pos") != "N" or
                reading.get("annotation_only") or reading.get("prefix_relation") or
                lookup_key(reading["lexical_features"].get("lemma") or "") in ("نفس", "عين")):
            continue
        suffixes = reading.get("person_evidence", {}).get("attached_pronouns", [])
        if (len(suffixes) != 1 or not suffixes[0]["licensed"] or
                suffixes[0]["attachment_candidates"] != ["possessive"]):
            continue
        suffix = suffixes[0]
        raw = suffix["person_profile"]
        if raw is None or raw["person"] != 3:
            continue
        profile = {"person": 3, "gender": ("masculine", "feminine", None)[raw["gender"]],
                   "number": ("singular", "dual", "plural")[raw["number"]]}
        clusters = lookup_clusters(token["surface"])
        part = _slice(reader.source, token, clusters[suffix["start_cluster"]][2],
                      clusters[suffix["end_cluster"] - 1][3], "candidate_substitution_return")
        reference = reader.reference(part["surface"], origin="relative_return", profile=profile,
            context=reader.context, mentions=reader.mentions, span=part["span"], scope=reader.scope,
            return_entity=base["entity"])
        obligations = _reading_obligations(reading) + ["APPOSITION_ATTACHMENT_AND_INTENTION_REQUIRED",
            "PART_OR_ASSOCIATION_RELATION_REQUIRES_INDEPENDENT_SEMANTIC_WITNESS"]
        if reference["bound_entity_id"] != base["entity"]:
            obligations.append("SUBSTITUTION_SAME_REFERENT_PRONOUN_REQUIRED")
        if profile_compatibility(profile, _profile(base["reading"])) == "conflict":
            obligations.append("CONSTRUCTION_CONFLICT")
        pronoun = _synthetic_reading(part, pos="PRON", profile=profile, rule="badal_identity")
        pronoun["support_records"] = reading["support_records"]
        for kind in ("badal_part", "badal_association"):
            row = _append_np(base, reading=reading,
                assignment=reader.assignment(token, reading, "badal", head=base["root"],
                    inherited_case=inherited, idhafa=True), reference=reference,
                support=_support(reader, "badal_identity"), obligations=obligations,
                relation=_relation(kind, base["root"], token, evidence_status="CANDIDATE_ONLY",
                    whole_entity=base["entity"], part_entity=None, identity_preserved=False,
                    whole_event_projection=False, pronoun_span=part["span"],
                    head_reading_id=base["reading"]["reading_id"], dependent_reading_id=reading["reading_id"]))
            row["readings"].append(pronoun)
            row["assignments"].append(reader.assignment(part, pronoun, "idafa_complement", head=token))
            row["substitution_unresolved"] = True
            results.append(row)
    return results


def _operator_gate(reader, tokens, operator, head, readings, assignments, obligations, supports):
    """Bind computed frame premises to exact occurrences before activation.

    This is a Python replay check of the conditional law, not a Lean proof of
    the parser. Identity here is occurrence/reading identity; resolving the
    referent is a separate, necessary discourse gate.
    """
    family = operator["family"]
    rule = "kada_complement" if family == "kada" else family + "_sisters"
    by_id = {r["reading_id"]: r for r in readings}
    slots = operator_slots(family)
    targets = [a for a in assignments if a["role"] in {s["role"] for s in slots}]

    def witnessed(span, surface):
        lo, hi = span["start"], span["end"]
        return (0 <= lo < hi <= len(reader.source.raw_bytes) and
                span == span_dict(_span(reader.source, lo, hi)) and
                reader.source.raw_bytes[lo:hi].decode("utf-8") == surface)

    def binding(reading, occurrence):
        return {"scope": reader.scope, "occurrence_span": occurrence,
                "reading_id": reading["reading_id"], "reading_span": reading["stem_span"]}

    head_binding = binding(operator["reading"], head["span"])
    edges = [{"head": head_binding, "target": binding(by_id[a["reading_id"]], a["span"]),
              "role": a["role"], "required_case": a["required_case"]}
             for a in targets if a["reading_id"] in by_id]
    identity_bound = (witnessed(head["span"], head["surface"]) and len(edges) == len(targets) and
        all(witnessed(r["stem_span"], r["stem_surface"]) for r in readings) and
        all(witnessed(a["span"], a["surface"]) and
            (head["span"]["end"] <= a["span"]["start"] or a["span"]["end"] <= head["span"]["start"])
            for a in targets))
    attachment_licensed = (len(targets) == len(slots) and
        all(sum(a["role"] == slot["role"] and a["required_case"] == CASES[slot["case"]] and
                a["head_span"] == head["span"] for a in targets) == 1 for slot in slots))
    covered = [r["stem_span"] for r in readings] + [a["span"] for a in assignments]
    covered += [a["head_span"] for a in assignments if a["head_span"] is not None]
    # These particles were consumed by the corresponding explicit production.
    grammar_tokens = [t for t in tokens if
        (t["span"]["end"] <= head["span"]["start"] and lookup_key(t["surface"]) in ("ما", "لا")
         and operator["scope"] in ("continuation", "duration")) or
        (operator.get("future_marker_span") == t["span"] and lookup_key(t["surface"]) == "سوف"
         and operator["aspect"] == "IMPF") or
        (operator.get("negation_marker_span") == t["span"] and lookup_key(t["surface"]) == "ما"
         and operator["family"] == "zanna" and operator["aspect"] == "PERF"
         and operator.get("matrix_negative") is True) or
        (operator["lemma"] == "ليس" and len(tokens) == 4 and t == tokens[2]
         and lookup_key(t["surface"]) == "إلا")]
    covered += [t["span"] for t in grammar_tokens]
    complete = attachment_licensed and all(any(s["start"] <= t["span"]["start"] and
        t["span"]["end"] <= s["end"] for s in covered) for t in tokens)
    flags = {
        "identity_bound": identity_bound,
        "source_supported": (any(s.get("rule") == rule and
            s.get("policy_sha256") == reader.construction_policy["policy_sha256"] for s in supports) and
            (not operator.get("matrix_negative") or any(s.get("rule") == "matrix_ma_negation" and
                s.get("policy_sha256") == reader.construction_policy["policy_sha256"] for s in supports)) and
            (operator["lemma"] != "شرع" or any(s.get("rule") == "inception_sharaa" and
                s.get("policy_sha256") == reader.construction_policy["policy_sha256"] for s in supports)) and
            all(bool(r.get("support_records")) and not r.get("annotation_only") for r in readings)),
        "attachment_licensed": attachment_licensed,
        "frame_complete": complete,
        "sense_licensed": not obligations,
        "unblocked": (all(a["compatible"] and not a.get("obligations") for a in assignments) and
                       not any(o.endswith("CONFLICT") for o in obligations)),
    }
    return {"kind": "construction_gate", "family": family, "law_id": LAW_ID,
        "law_sha256": EXPECTED_TABLE_SHA256, "policy_sha256": reader.construction_policy["policy_sha256"],
        "rule": rule, "edges": edges, "consumed_grammar_spans": [t["span"] for t in grammar_tokens],
        "premises": flags, "allowed": construction_allowed(family, **flags),
        "authority": "RECOMPUTED_SOURCE_BOUND_CONDITIONAL_GATE"}


def _build(reader, tokens, *, frame, force, parts, claims, readings=(), assignments=(),
           relations=(), obligations=(), supports=(), operator=None, operator_head=None):
    if any(p.get("substitution_unresolved") for p in parts):
        # The proposed substitute's denotation has not been acquired. Even
        # diagnostic candidate claims must not restate its judgment about
        # the whole/head merely because that earlier reference is known.
        claims = []
    refs = [r for p in parts for r in p["refs"]]
    all_assignments = [a for p in parts for a in p["assignments"]] + list(assignments)
    all_readings = [r for p in parts for r in p["readings"]] + list(readings)
    all_relations = [r for p in parts for r in p["relations"]] + list(relations)
    all_obligations = [o for p in parts for o in p["obligations"]] + list(obligations)
    all_supports = [s for p in parts for s in p["supports"]] + list(supports)
    agreement_obligations, agreement_relations, agreement_supports = reader.predicate_agreement(
        all_readings, all_assignments, refs, force=force)
    all_obligations.extend(agreement_obligations)
    all_relations.extend(agreement_relations)
    all_supports.extend(agreement_supports)
    if operator is not None:
        # The operator's own imperfect mood is independent of the cases it
        # requires of its subject and predicate. A future marker never
        # licenses a contrary visible terminal mark on that operator.
        if operator["aspect"] == "IMPF":
            future_head = next((t for t in tokens if t["span"] == operator.get("future_marker_span")), None)
            all_assignments.append(reader.assignment(operator_head, operator["reading"],
                "imperfect_indicative", head=future_head))
            all_supports.append(reader.support("imperfect_indicative"))
            if future_head is not None:
                all_supports.append(reader.support("deictic_adverbs"))
        gate = _operator_gate(reader, tokens, operator, operator_head, all_readings,
                              all_assignments, all_obligations, all_supports)
        all_relations.append(gate)
        if not gate["allowed"]:
            all_obligations.append("CONSTRUCTION_LAW_GATE")
    return reader.analysis(tokens, frame=frame, force=force, refs=refs, assignments=all_assignments,
        readings=all_readings, claims=claims, relations=all_relations,
        obligations=all_obligations, supports=all_supports)


def _qualifiers(parts):
    return [q for part in parts for q in part["restriction"]]


def _with_question(row, wh=None):
    row["question_kind"] = (wh or "polar") if row["force"] == "QUESTION" else None
    row["analysis_id"] = identity({k: v for k, v in row.items() if k != "analysis_id"})
    return row


# These are grammatical operator paradigms, with primary-source scope. Content
# nouns and predicates are still acquired from the independent lexical source.
# A complete two-place mental construction is required for a zanna reading;
# e.g. seeing with the eyes is not silently converted into believing.
_OPERATOR_ROWS = (
    ("كَانَ", "kana", None), ("لَيْسَ", "kana", None),
    ("صَارَ", "kana", "transformation"),
    ("أَصْبَحَ", "kana", "time_transition"), ("أَمْسَى", "kana", "time_transition"),
    ("أَضْحَى", "kana", "time_transition"), ("ظَلَّ", "kana", "time_transition"),
    ("بَاتَ", "kana", "time_transition"),
    ("زَالَ", "kana", "continuation"), ("فَتِئَ", "kana", "continuation"),
    ("بَرِحَ", "kana", "continuation"), ("انْفَكَّ", "kana", "continuation"),
    ("دَامَ", "kana", "duration"),
    ("إِنَّ", "inna", None), ("أَنَّ", "inna", None),
    ("كَأَنَّ", "inna", "similitude"), ("لَكِنَّ", "inna", None),
    ("لَيْتَ", "inna", "wish"), ("لَعَلَّ", "inna", "hope"),
    ("ظَنَّ", "zanna", "belief"), ("حَسِبَ", "zanna", "belief"),
    ("خَالَ", "zanna", "belief"), ("زَعَمَ", "zanna", "belief"),
    ("عَدَّ", "zanna", "belief"), ("حَجَا", "zanna", "belief"),
    ("عَلِمَ", "zanna", "certainty"), ("رَأَى", "zanna", "certainty"),
    ("وَجَدَ", "zanna", "certainty"), ("دَرَى", "zanna", "certainty"),
    ("أَلْفَى", "zanna", "certainty"), ("تَخِذَ", "zanna", "transformation"),
    ("اتَّخَذَ", "zanna", "transformation"), ("صَيَّرَ", "zanna", "transformation"),
    ("جَعَلَ", "zanna", "transformation"), ("وَهَبَ", "zanna", "transformation"),
    ("تَرَكَ", "zanna", "transformation"),
    ("كَادَ", "kada", "proximity"), ("كَرَبَ", "kada", "proximity"),
    ("أَوْشَكَ", "kada", "proximity"), ("عَسَى", "kada", "hope"),
    ("حَرَى", "kada", "hope"), ("اخْلَوْلَقَ", "kada", "hope"),
    ("أَخَذَ", "kada", "inception"), ("طَفِقَ", "kada", "inception"),
    ("جَعَلَ", "kada", "inception"), ("عَلِقَ", "kada", "inception"),
    ("أَنْشَأَ", "kada", "inception"), ("شَرَعَ", "kada", "inception"),
)


def operator_catalog():
    return [{"form": form, "lemma": lookup_key(form), "family": family, "scope": scope,
             "authority": "GRAMMATICAL_CANDIDATE_REQUIRING_COMPLETE_SENSE_AND_FRAME"}
            for form, family, scope in _OPERATOR_ROWS]


def _operator_candidates(reader, token):
    results = []
    source_verbs = reader.verbs(token)
    for form, family, scope in _OPERATOR_ROWS:
        lemma = lookup_key(form)
        if lemma == "شرع" and "inception_sharaa" not in reader.construction_policy["rules"]:
            continue
        matching = [r for r in source_verbs if lookup_key(r["lexical_features"].get("lemma") or "") == lemma
                    and r["lexical_features"].get("aspect") in ("PERF", "IMPF")]
        direct = template_matches(token["surface"], form, mutable_last=False)
        if not matching and not direct:
            continue
        if matching:
            for reading in matching:
                results.append({"lemma": lemma, "family": family, "scope": scope, "reading": reading,
                                "aspect": reading["lexical_features"]["aspect"], "profile": _profile(reading)})
        elif direct:
            profile = {"person": 3, "gender": "masculine", "number": "singular"}
            rule = ("inception_sharaa" if lemma == "شرع" else
                    family + "_sisters" if family != "kada" else "kada_complement")
            reading = _synthetic_reading(token, pos="PART" if family == "inna" else "V", profile=profile, rule=rule)
            if family != "inna":
                reading["kind"] = "verb"
                reading["lexical_features"].update(aspect="PERF", lemma=form, voice="active")
            results.append({"lemma": lemma, "family": family, "scope": scope, "reading": reading,
                            "aspect": None if family == "inna" else "PERF", "profile": profile})
    return results


def _operator_spelling_proposed(reader, token):
    """Recognize a route without licensing its vowels, sense, or frame.

    A rejected operator form must not return to a less constrained parser.
    The lexical inventory also covers witnessed inflected spellings such as
    an imperfect copula; this lookup never supplies an accepted reading.
    """
    lemmas = {lookup_key(form) for form, _, _ in _OPERATOR_ROWS}
    key = lookup_key(token["surface"])
    if key in lemmas:
        return True
    return any(entry.get("kind") == "verb" and
               entry.get("aspect") in ("PERF", "IMPF") and
               lookup_key(entry.get("lemma") or "") in lemmas
               for encoded in reader.index.get(key, ())
               for entry in (json.loads(encoded),))


def _operator_obligations(reader, operator, token, subject, prefix):
    obligations = []
    family, lemma = operator["family"], operator["lemma"]
    if family == "inna":
        if lemma in ("إن", "أن", "كأن", "لكن") and "ّ" not in lookup_clusters(token["surface"])[-1][1]:
            obligations.append("INNA_DISTINCT_FROM_LIGHT_OR_CONDITIONAL_READING_REQUIRES_SHADDA")
        if lemma == "أن":
            obligations.append("ANNA_SUBORDINATE_GOVERNING_CLAUSE_REQUIRED")
    else:
        entity = subject["entity"]
        sp = _profile(subject["reading"])
        op = operator["profile"]
        if entity is not None and not entity.startswith("?"):
            if sp.get("person") not in (None, 3) or op.get("person") != 3:
                obligations.append("CONSTRUCTION_CONFLICT")
            # This bounded operator-before-subject frame has singular verbal
            # agreement. Noncanonical agreement is retained as an unmet gate.
            if op.get("number") != "singular":
                obligations.append("OPERATOR_AGREEMENT_REGIME_REQUIRED")
            if _axis(op.get("gender"), sp.get("gender")) == "conflict":
                obligations.append("CONSTRUCTION_CONFLICT")
        if operator["reading"]["lexical_features"].get("voice") == "passive":
            obligations.append("PASSIVE_OPERATOR_REQUIRES_DIFFERENT_ARGUMENT_FRAME")
        if operator["reading"].get("person_evidence", {}).get("attached_pronouns"):
            obligations.append("ATTACHED_OPERATOR_ARGUMENT_FRAME_REQUIRED")
    if operator["scope"] == "continuation" and prefix not in ("ما", "لا"):
        obligations.append("CONTINUATIVE_OPERATOR_REQUIRES_NEGATIVE_OR_QUASI_NEGATIVE_CONTEXT")
    if operator["scope"] == "continuation" and prefix == "لا" and operator["aspect"] == "PERF":
        obligations.append("CONTINUATIVE_LA_PERF_PRAYER_OR_ASSERTION_REQUIRES_CONTEXT")
    if operator["scope"] == "duration":
        obligations.append("DURATION_MA_DAM_REQUIRES_COMPLETE_GOVERNING_CLAUSE")
    return obligations


def _scoped(reader, operator, embedded, args, *, positive=True, tense=None, time=(), place=()):
    scope = operator["scope"]
    allowed = scoped_projection_allowed(scope, metadata_preserved=True, source_supported=True, frame_complete=True)
    if not allowed:
        return []
    claim = reader.claim("@operator:" + operator["lemma"], args, positive,
        tense or operator.get("tense") or ("past" if operator["aspect"] == "PERF" else "nonpast"), list(time), list(place),
        [{"kind": "operator_scope", "family": operator["family"], "lemma": operator["lemma"],
          "sense": scope, "aspect": operator["aspect"], "embedded": embedded,
          "embedded_fact_projection": False}])
    claim["predicate_kind"] = "scoped"
    return [claim]


def _operator_relation(operator, token, subject, predicate_span):
    return {"kind": "operator", "family": operator["family"], "lemma": operator["lemma"],
            "sense": operator["scope"], "aspect": operator["aspect"],
            "tense": operator.get("tense") or ("unspecified" if operator["family"] == "inna" or operator["lemma"] == "ليس"
                else "past" if operator["aspect"] == "PERF" else "nonpast"),
            "head_span": token["span"], "subject_span": subject["root"]["span"],
            "complement_span": predicate_span, "scope_preserved": True,
            "embedded_fact_projection": operator["scope"] is None,
            "operator_reading_id": operator["reading"]["reading_id"]}


def operator_frames(reader, tokens, *, force, wh=None, depth=0):
    """Return None only when this position proposes no operator route.

    An empty result means that an operator spelling was recognized but no
    complete licensed reading was constructed. Both assertions and questions
    must keep that outcome instead of retrying a spelling-only legacy rule.
    """
    prefix, offset = None, 0
    if lookup_key(tokens[0]["surface"]) in ("ما", "لا", "سوف") and len(tokens) > 1:
        prefix, offset = lookup_key(tokens[0]["surface"]), 1
    head = tokens[offset]
    candidates = _operator_candidates(reader, head)
    proposed = bool(candidates) or _operator_spelling_proposed(reader, head)
    if not proposed:
        return None
    if wh not in (None, "time", "place"):
        return []
    if prefix == "سوف":
        if not template_matches(tokens[0]["surface"], "سَوْفَ", mutable_last=False):
            return []
        # Recognition precedes filtering, so an incompatible perfect cannot
        # fall through into a generic event + modifier reading.
        candidates = [{**o, "tense": "future", "future_marker_span": tokens[0]["span"]}
                      for o in candidates if o["aspect"] == "IMPF"]
        if not candidates:
            return []
    elif prefix is not None:
        template = "مَا" if prefix == "ما" else "لَا"
        if not template_matches(tokens[0]["surface"], template, mutable_last=False):
            return []
        negative_matrices = [{**o, "matrix_negative": True, "negation_marker_span": tokens[0]["span"]}
            for o in candidates if prefix == "ما" and o["family"] == "zanna" and
            o["scope"] in ("belief", "certainty") and o["aspect"] == "PERF" and
            "matrix_ma_negation" in reader.construction_policy["rules"]]
        candidates = [o for o in candidates if o["scope"] in ("continuation", "duration")] + negative_matrices
    if not candidates:
        return []
    body, results = tokens[offset + 1:], []
    for operator in candidates:
        if operator["family"] in ("kana", "inna"):
            results.extend(_nominal_operator(reader, tokens, body, operator, head, prefix, force, wh))
        elif operator["family"] == "zanna" and wh is None:
            results.extend(_zanna(reader, tokens, body, operator, head, prefix, force))
        elif operator["family"] == "kada" and wh is None:
            results.extend(_kada(reader, tokens, body, operator, head, prefix, force))
        _limit(results)
    return results


def _nominal_operator(reader, tokens, body, operator, head, prefix, force, wh=None):
    results = []
    family, lemma = operator["family"], operator["lemma"]
    local_force = ("WISH" if lemma == "ليت" else "HOPE" if lemma == "لعل" else force)
    if prefix == "لا" and operator["scope"] == "continuation" and operator["aspect"] == "PERF" and force != "QUESTION":
        local_force = "AMBIGUOUS"
    positive = lemma != "ليس"
    restriction = []
    if lemma == "ليس" and len(body) == 3 and lookup_key(body[1]["surface"]) == "إلا":
        if not template_matches(body[1]["surface"], "إِلَّا", mutable_last=False):
            return []
        body = [body[0], body[2]]
        positive, restriction = True, ["negation_exception_predicate"]
    for complement in reader.complements(body):
        if complement.get("requires_event"):
            # A primary example of an N used temporally with a verbal event
            # is not a license to attach that N to a nominal predicate.
            continue
        reduced = complement["tokens"]
        qtime = ["?time"] if wh == "time" else complement["time"]
        qplace = ["?place"] if wh == "place" else complement["place"]
        if len(reduced) < 2:
            continue
        for subject, predicate in product(noun_phrases(reader, reduced[:-1], family + "_subject", head=head),
                                           reader.predicates(reduced[-1])):
            predicate_token = reduced[-1]
            assigned = reader.assignment(predicate_token, predicate, family + "_predicate", head=head)
            obligations = (_operator_obligations(reader, operator, head, subject, prefix) +
                           _reading_obligations(predicate) + complement["obligations"])
            tense = (operator.get("tense") or ("past" if operator["aspect"] == "PERF" else "nonpast")) if family == "kana" and lemma != "ليس" else "unspecified"
            embedded = reader.claim(predicate["lexical_features"]["lemma"], [subject["entity"]], positive,
                tense, qtime, qplace, restriction + subject["restriction"])
            claims = [embedded]
            if operator["scope"] not in (None, "wish", "hope"):
                claims = _scoped(reader, operator, [embedded], [subject["entity"]], tense=tense,
                                  time=qtime, place=qplace)
            extra_part = {"refs": complement["refs"], "assignments": complement["assignments"],
                "readings": complement["readings"], "relations": [], "restriction": [],
                "obligations": [], "supports": complement["supports"]}
            row = _build(reader, tokens, frame=family + "_construction", force=local_force,
                parts=[subject, extra_part], readings=[operator["reading"], predicate], assignments=[assigned],
                claims=claims, obligations=obligations,
                relations=[_operator_relation(operator, head, subject, predicate_token["span"])],
                supports=[_support(reader, family + "_sisters"), _support(reader, "tense_aspect")],
                operator=operator, operator_head=head)
            results.append(_with_question(row, wh))
            _limit(results)
    return results


@lru_cache(maxsize=2)
def _hasiba_source_receipts(raw, excluded_verses, source_id):
    """Replay the lexical premises from source bytes, independently of target vowels.

    The immutable cache contains complete source receipts, not caller-proposed
    record IDs. Missing source vowels and derived-form annotations cannot be
    repaired by the fully vocalized target. Form I and ACT may be implicit in
    this QAC profile; contrary annotations, ambiguous features and exclusions
    never qualify.
    """
    corpus = read_corpus(raw, format="qac", source_id=source_id)
    qualified = set()
    for record in corpus["records"]:
        loc = record["locator"]
        if (not record["valid"] or loc is None or
                f"{loc[0]}:{loc[1]}" in excluded_verses):
            continue
        fields, tokens = record["fields"], record["feature_tokens"]
        profiles = [t for t in tokens if re.fullmatch(r"[123]?[MF]?[SDP]|[MF]", t)]
        if (not tokens or tokens[0] != "STEM" or fields["TAG"] != "V" or
                _feature(tokens, "POS:") != "V" or "PERF" not in tokens or
                any(t in tokens for t in ("IMPF", "IMPV", "PASS")) or
                profiles != ["3MS"] or
                any(re.fullmatch(r"\([IVX]+\)", t) and t != "(I)" for t in tokens)):
            continue
        root, lemma_bw = _feature(tokens, "ROOT:"), _feature(tokens, "LEM:")
        if not root or not lemma_bw:
            continue
        try:
            form = buckwalter_to_arabic(fields["FORM"])
            lemma = buckwalter_to_arabic(lemma_bw)
            root = "".join(ROOT_BW[c] for c in root)
        except (KeyError, NabtError):
            continue
        if (root != "حسب" or lookup_key(lemma) != "حسب" or
                lookup_clusters(form) != lookup_clusters("حَسِبَ")):
            continue
        qualified.add((wire(_receipt(record, corpus["source"])), lemma))
    return frozenset(qualified)


def _hasiba_sense_witness(reader, operator, head):
    """An observed lexical vowel, not the expected target role, selects sense.

    Mukhtar al-Sihah distinguishes hasiba (thought) from hasaba (counted).
    The unvocalized spelling and alima retain their independent obligations.
    """
    clusters = lookup_clusters(head["surface"])
    reading = operator["reading"]
    profile = operator["profile"]
    proofs = [s for s in reading.get("support_records", ()) if "record_id" in s]
    if (operator["lemma"] != "حسب" or operator["family"] != "zanna" or
            operator["scope"] != "belief" or not clusters or len(clusters) != 3 or
            reading.get("variant") != "attested" or
            not proofs or reader.model is None or
            reading.get("kind") != "verb" or reading.get("annotation_only") or
            reading["lexical_features"].get("pos") != "V" or
            lookup_key(reading["lexical_features"].get("root") or "") != "حسب" or
            lookup_key(head["surface"]) != "حسب" or
            [c[1] & set("ًٌٍَُِْ") for c in clusters] != [{"َ"}, {"ِ"}, {"َ"}] or
            any(c[1] & set("ّٰ") for c in clusters) or
            not template_matches(head["surface"], "حَسِبَ", mutable_last=False) or
            reading["lexical_features"].get("aspect") != "PERF" or
            reading["lexical_features"].get("voice") == "passive" or
            profile != {"person": 3, "gender": "masculine", "number": "singular"}):
        return None
    qualified = _hasiba_source_receipts(reader.model.raw, reader.model.excluded_verses,
                                        reader.model.source_id)
    lemma = reading["lexical_features"].get("lemma")
    if any((wire(proof), lemma) not in qualified for proof in proofs):
        return None
    return {"kind": "observed_medial_vowel_lexical_sense", "rule": "vocalized_hasiba_sense",
        "operator_span": deepcopy(head["span"]), "operator_surface": head["surface"],
        "operator_reading_id": reading["reading_id"], "required_medial_vowel": "ِ",
        "required_written_active_form": "حَسِبَ",
        "sense": "belief", "source": _support(reader, "vocalized_hasiba_sense"),
        "target_role_used_as_sense_evidence": False, "embedded_fact_projection": False}


def _zanna(reader, tokens, body, operator, head, prefix, force):
    results = []
    if len(body) < 3:
        return results
    # Only the initial, overt, unsuspended two-object construction is covered.
    # Elimination, suspension, reversed order and perceptual readings are not
    # inferred from the spelling of the verb.
    for split in range(1, len(body) - 1):
        matrix = noun_phrases(reader, body[:split], "zanna_subject", head=head)
        objects = noun_phrases(reader, body[split:-1], "zanna_object1", head=head)
        for subject, obj, predicate in product(matrix, objects, reader.predicates(body[-1])):
            assigned = reader.assignment(body[-1], predicate, "zanna_object2", head=head)
            obligations = _operator_obligations(reader, operator, head, subject, prefix) + _reading_obligations(predicate)
            sense_witness = _hasiba_sense_witness(reader, operator, head)
            if operator["lemma"] in ("رأى", "علم", "وجد", "ألفى", "جعل", "ترك", "وهب", "عد", "حسب", "حجا") and sense_witness is None:
                obligations.append("POLYSEMOUS_OPERATOR_SENSE_REQUIRES_INDEPENDENT_CONTEXT")
            embedded = reader.claim(predicate["lexical_features"]["lemma"], [obj["entity"]], True,
                "relative_to_operator", [], [], obj["restriction"])
            claims = _scoped(reader, operator, [embedded], [subject["entity"]],
                              positive=not operator.get("matrix_negative", False))
            for claim in claims:
                claim["restriction"].extend(subject["restriction"])
            relation = _operator_relation(operator, head, subject, body[-1]["span"])
            relation.update(object1_span=obj["root"]["span"], object2_span=body[-1]["span"],
                            two_object_sense="nominal_proposition", suspension="absent_in_declared_frame")
            relations = [relation]
            supports = [_support(reader, "zanna_sisters"), _support(reader, "tense_aspect")]
            if sense_witness is not None:
                relation["independent_sense_witness"] = sense_witness
                supports.append(_support(reader, "vocalized_hasiba_sense"))
            if operator.get("matrix_negative"):
                relations.append(_relation("matrix_negation", tokens[0], head,
                    scope="epistemic_matrix", embedded_polarity_preserved=True,
                    embedded_negation_projected=False))
                supports.append(_support(reader, "matrix_ma_negation"))
            row = _build(reader, tokens, frame="zanna_two_object_construction", force=force,
                parts=[subject, obj], readings=[operator["reading"], predicate], assignments=[assigned],
                claims=claims, obligations=obligations, relations=relations, supports=supports,
                operator=operator, operator_head=head)
            results.append(_with_question(row))
            _limit(results)
    return results


def _clause_token(reader, tokens):
    lo, hi = tokens[0]["span"]["start"], tokens[-1]["span"]["end"]
    span = span_dict(_span(reader.source, lo, hi))
    return {"token_id": identity([reader.source.sha256, "subordinate_clause", span]),
            "surface": reader.source.raw_bytes[lo:hi].decode("utf-8"), "span": span, "kind": "clause"}


def _kada(reader, tokens, body, operator, head, prefix, force):
    """Compose a bounded final temporal adjunct inside the verbal clause.

    This profile licenses an embedded-event attachment. It does not assert
    that all Arabic matrix/embedded attachment alternatives were enumerated.
    The existing unconsumed lexical variant is still examined separately.
    """
    results = []
    for complement in reader.complements(body):
        if complement["place"]:
            continue
        reduced = complement["tokens"]
        retained = {t["token_id"] for t in reduced}
        adjuncts = [t for t in body if t["token_id"] not in retained]
        if complement["time"]:
            if len(adjuncts) != 1 or adjuncts[0] != body[-1]:
                continue
        elif adjuncts:
            continue
        results.extend(_kada_core(reader, tokens, reduced, operator, head, prefix, force,
                                   complement=complement, adjuncts=adjuncts))
        _limit(results)
    return results


def _kada_core(reader, tokens, body, operator, head, prefix, force, *, complement, adjuncts):
    results = []
    for split in range(1, len(body)):
        tail = body[split:]
        an = lookup_key(tail[0]["surface"]) == "أن"
        verb_tokens = tail[1:] if an else tail
        if not verb_tokens:
            continue
        for subject, verb in product(noun_phrases(reader, body[:split], "kada_subject", head=head),
                                      reader.verbs(verb_tokens[0])):
            if verb["lexical_features"].get("aspect") != "IMPF":
                continue
            label = "inception" if operator["scope"] == "inception" else operator["lemma"]
            policy = complement_an_policy(label)
            obligations = _operator_obligations(reader, operator, head, subject, prefix)
            if policy == "required" and not an or policy == "forbidden" and an:
                obligations.append("CONSTRUCTION_CONFLICT")
            if an and ("ّ" in tail[0]["surface"] or not template_matches(tail[0]["surface"], "أَنْ", mutable_last=False)):
                obligations.append("CONSTRUCTION_CONFLICT")
            obligations.extend(reader._agreement(verb, subject, before_subject=False))
            if verb.get("person_evidence", {}).get("attached_pronouns"):
                obligations.append("KADA_COMPLEMENT_ATTACHED_ARGUMENT_FRAME_REQUIRED")
            object_tokens = verb_tokens[1:]
            witnesses = verb.get("person_evidence", {}).get("valency_witnesses", [])
            if object_tokens:
                # A source-qualified nominal argument is a real competing
                # use of a token that may also have a temporal T reading.
                # This profile has no complete operator-argument contract;
                # retain that rival as pending rather than licensing the
                # temporal reading by silently discarding the nominal one.
                if ((verb["lexical_features"].get("voice") or "active") != "active" or
                        not witnesses or verb.get("person_evidence", {}).get("attached_pronouns")):
                    continue
                objects = [obj for obj in noun_phrases(reader, object_tokens, "direct_object", head=verb_tokens[0])
                    if obj["reading"]["lexical_features"].get("pos") in ("N", "PN", "PRON", "DEM")
                    and obj["reading"].get("variant") != "declared_grammatical_paradigm"]
                if not objects:
                    continue
            else:
                objects = [None]
            vrole = "imperfect_subjunctive" if an else "imperfect_indicative"
            vassign = reader.assignment(verb_tokens[0], verb, vrole, head=tail[0] if an else head)
            clause_token = _clause_token(reader, tail + adjuncts)
            clause_reading = _synthetic_reading(clause_token, pos="CLAUSE", rule="kada_complement")
            cassign = reader.assignment(clause_token, clause_reading, "kada_predicate", head=head)
            cassign["case_domain"] = "clause_local_case"
            embedded = reader.claim(verb["lexical_features"]["lemma"], [subject["entity"]], True,
                                    "relative_nonpast", deepcopy(complement["time"]), [], subject["restriction"])
            embedded.update(predicate_kind="event", voice=verb["lexical_features"].get("voice") or "active")
            claims = _scoped(reader, operator, [embedded], [subject["entity"]])
            relation = _operator_relation(operator, head, subject, clause_token["span"])
            relation.update(complement_kind="imperfect_clause", local_case="nasb",
                case_domain="clause_local_case", an_present=an, an_policy=policy,
                internal_verb_span=verb_tokens[0]["span"], internal_verb_required_case=vassign["required_case"],
                internal_subject_reference=subject["reference"]["reference_id"])
            extra = {"refs": complement["refs"], "readings": complement["readings"],
                     "assignments": [], "relations": [], "supports": complement["supports"],
                     "obligations": complement["obligations"], "restriction": []}
            by_id = {r["reading_id"]: r for r in complement["readings"]}
            for assignment in complement["assignments"]:
                adjunct = next(t for t in adjuncts if t["span"] == assignment["span"])
                reading = by_id[assignment["reading_id"]]
                extra["assignments"].append(reader.assignment(adjunct, reading, "time_adverb", head=verb_tokens[0]))
                extra["relations"].append(_relation("time_adverb", verb_tokens[0], adjunct,
                    dependent_reading_id=reading["reading_id"], scope="embedded_event",
                    attachment_profile="bounded_embedded_temporal", exhaustive_attachment_claimed=False,
                    embedded_fact_projection=False))
            supports = [_support(reader, "kada_complement"), _support(reader, "tense_aspect")]
            if adjuncts:
                supports.append(_support(reader, "temporal_spatial_attachment"))
            if operator["lemma"] == "شرع":
                supports.append(_support(reader, "inception_sharaa"))
            for obj in objects:
                pending = ["KADA_COMPLEMENT_ARGUMENT_FRAME_REQUIRED"] if obj else []
                relations = [relation]
                argument_supports = []
                if obj:
                    relations.append(_relation("kada_complement_argument_candidate", verb_tokens[0], obj["root"],
                        dependent_reading_id=obj["reading"]["reading_id"],
                        evidence_status="CANDIDATE_ONLY", proposed_role="direct_object",
                        operator_argument_contract_established=False, embedded_fact_projection=False))
                    argument_supports = [reader.support("active_subject"),
                                         {"kind": "valency_source", "witnesses": witnesses}]
                row = _build(reader, tokens,
                    frame="kada_unresolved_argument_construction" if obj else "kada_clausal_construction",
                    force=force, parts=[subject, extra] + ([obj] if obj else []),
                    readings=[operator["reading"], verb, clause_reading], assignments=[cassign, vassign],
                    claims=[] if obj else claims, obligations=obligations + pending,
                    relations=relations, supports=supports + argument_supports,
                    operator=operator, operator_head=head)
                results.append(_with_question(row))
                _limit(results)
    return results


def nominal_frames(reader, tokens, *, force):
    """A composed, independently referenced subject and one lexical predicate."""
    if len(tokens) < 3:
        return []
    results = []
    for subject, predicate in product(noun_phrases(reader, tokens[:-1], "nominal_subject"),
                                       reader.predicates(tokens[-1])):
        assigned = reader.assignment(tokens[-1], predicate, "nominal_predicate", head=subject["root"])
        claim = reader.claim(predicate["lexical_features"]["lemma"], [subject["entity"]], True,
                              "unspecified", [], [], subject["restriction"])
        row = _build(reader, tokens, frame="composed_nominal_predication", force=force,
            parts=[subject], readings=[predicate], assignments=[assigned], claims=[claim],
            obligations=_reading_obligations(predicate), supports=[reader.support("nominal_predication")])
        results.append(_with_question(row))
        _limit(results)
    return results


def verbal_frames(reader, tokens, *, force):
    """Bounded VSO/SVO with compositional NPs and independent valency evidence."""
    results = []
    if len(tokens) < 3:
        return results
    for vpos, vtoken in enumerate(tokens):
        for verb in reader.verbs(vtoken):
            if verb.get("person_evidence", {}).get("attached_pronouns"):
                continue
            features = verb["lexical_features"]
            aspect, voice = features.get("aspect"), features.get("voice") or "active"
            if aspect not in ("PERF", "IMPF", "IMPV"):
                continue
            role = "active_subject" if voice == "active" else "passive_subject"
            partitions = []
            if vpos == 0:
                partitions = [(tokens[1:cut], tokens[cut:]) for cut in range(2, len(tokens) + 1)]
            else:
                partitions = [(tokens[:vpos], tokens[vpos + 1:])]
            for subject_tokens, object_tokens in partitions:
                if len(subject_tokens) <= 1 and len(object_tokens) <= 1:
                    continue
                witnesses = verb.get("person_evidence", {}).get("valency_witnesses", [])
                if object_tokens and (voice != "active" or not witnesses):
                    continue
                subjects = noun_phrases(reader, subject_tokens, role, head=vtoken)
                objects = noun_phrases(reader, object_tokens, "direct_object", head=vtoken) if object_tokens else [None]
                for subject, obj in product(subjects, objects):
                    obligations = reader._agreement(verb, subject, before_subject=vpos == 0)
                    if vpos == 0 and _profile(verb).get("person") != 3:
                        obligations.append("CONSTRUCTION_CONFLICT")
                    obligations += list(verb.get("obligations", []))
                    parts = [subject] + ([obj] if obj else [])
                    args = [p["entity"] for p in parts]
                    claim = reader.claim(features["lemma"], args, True, "past" if aspect == "PERF" else "nonpast",
                                          [], [], _qualifiers(parts))
                    claim.update(predicate_kind="event", voice=voice)
                    assignments = [reader.assignment(vtoken, verb, "imperfect_indicative")] if aspect == "IMPF" else []
                    supports = [reader.support("active_subject")]
                    if obj:
                        supports.append({"kind": "valency_source", "witnesses": witnesses})
                    row = _build(reader, tokens, frame="composed_verbal_predication",
                        force="COMMAND" if aspect == "IMPV" else force, parts=parts, readings=[verb],
                        assignments=assignments, claims=[claim], obligations=obligations, supports=supports)
                    results.append(_with_question(row))
                    _limit(results)
    return results


def _extend(reader, tokens, base, *, readings=(), assignments=(), refs=(), relations=(),
            obligations=(), supports=(), claims=None, frame=None):
    selected = [reader._reading_by_id(rid) for rid in base["reading_ids"]]
    return _with_question(reader.analysis(tokens, frame=frame or base["frame"], force=base["force"],
        refs=base["references"] + list(refs), assignments=base["assignments"] + list(assignments),
        readings=[r for r in selected if r is not None] + list(readings),
        claims=deepcopy(base["claims"] if claims is None else claims),
        relations=base["relations"] + list(relations), obligations=base["obligations"] + list(obligations),
        supports=base["supports"] + list(supports)), base.get("question_kind"))


def event_modifiers(reader, tokens, *, force, depth):
    """A final hal or witnessed nisba specification, with every possible owner.

    The source examples license only the named nisba frames below. An arbitrary
    final accusative noun is never promoted to a tamyiz from its ending alone.
    """
    if len(tokens) < 3:
        return []
    dependents = [r for r in reader.readings(tokens[-1]) if r["kind"] == "noun" and
        r["lexical_features"].get("pos") in ("N", "ADJ") and not r.get("annotation_only") and
        not r.get("prefix_relation") and _definite(r) == "indefinite"]
    if not dependents:
        return []
    bases = reader.parse(tokens[:-1], inherited_force=force, depth=depth + 1)
    results = []
    for base in bases:
        if len(base["claims"]) != 1 or base["claims"][0]["predicate_kind"] != "event":
            continue
        # Incomplete core readings remain incomplete. They do not acquire a
        # missing argument merely because a following adjective can be a hal.
        if not base["licensed_syntax"] or not base["references_complete"] or base["rejected_candidate"]:
            continue
        verb = next((reader._reading_by_id(rid) for rid in base["reading_ids"]
                     if reader._reading_by_id(rid) and reader._reading_by_id(rid)["kind"] == "verb"), None)
        if verb is None:
            continue
        vtoken = next((t for t in tokens[:-1] if t["span"] == verb["stem_span"]), tokens[0])
        for dependent in dependents:
            pos = dependent["lexical_features"]["pos"]
            if pos == "ADJ":
                owners = [a for a in base["assignments"] if a["role"] in
                          ("active_subject", "passive_subject", "direct_object")]
                for owner in owners:
                    oreading = reader._reading_by_id(owner["reading_id"])
                    reference = next((r for r in base["references"] if r["span"] == owner["span"]), None)
                    if oreading is None or reference is None or _definite(oreading) != "definite":
                        continue
                    agreement = _agreement(oreading, dependent, "indefinite", "indefinite")
                    obligations = _reading_obligations(dependent)
                    if agreement != "confirmed":
                        obligations.append("CONSTRUCTION_CONFLICT" if agreement == "conflict" else "HAL_OWNER_AGREEMENT_REQUIRED")
                    assigned = reader.assignment(tokens[-1], dependent, "hal", head=vtoken)
                    assigned["owner_span"] = owner["span"]
                    claims = deepcopy(base["claims"])
                    claims[0]["restriction"].append({"kind": "hal", "owner": reference["bound_entity_id"],
                        "predicate": dependent["lexical_features"]["lemma"], "scope": "event_occurrence"})
                    relation = _relation("hal", vtoken, tokens[-1], owner_span=owner["span"],
                        owner_reference=reference["reference_id"], owner_reading_id=owner["reading_id"],
                        dependent_reading_id=dependent["reading_id"], agreement=agreement,
                        timeless_property_projected=False)
                    results.append(_extend(reader, tokens, base, readings=[dependent], assignments=[assigned],
                        relations=[relation], obligations=obligations, claims=claims,
                        supports=[_support(reader, "hal_attachment")], frame="event_with_hal"))
                    _limit(results)
            elif lookup_key(verb["lexical_features"].get("lemma") or "") in {
                    lookup_key(m["verb"]) for m in reader.construction_policy["examples"]["nisba_frames"]}:
                # Only independently replay-extracted verb/unit examples can
                # discharge the frame. A new noun after a known frame verb
                # remains pending; its N tag is not a semantic-use witness.
                obligations = _reading_obligations(dependent)
                models = reader.construction_policy["examples"]["nisba_frames"]
                frame_models = [m for m in models if lookup_key(m["verb"]) ==
                                lookup_key(verb["lexical_features"]["lemma"])]
                witness = next((m for m in frame_models if
                    lookup_key(m["unit_form"]) == lookup_key(tokens[-1]["surface"])), None)
                if witness is None:
                    obligations.append("TAMYIZ_VERSUS_OTHER_NOMINAL_USE_REQUIRES_SOURCE_FRAME")
                if _profile(dependent).get("number") != "singular":
                    obligations.append("TAMYIZ_SINGULAR_NOMINAL_USE_REQUIRED")
                assigned = reader.assignment(tokens[-1], dependent, "tamyiz", head=vtoken)
                claims = deepcopy(base["claims"])
                claims[0]["restriction"].append({"kind": "tamyiz", "subtype": "nisba",
                    "predicate": dependent["lexical_features"]["lemma"], "scope": "event_relation"})
                relation = _relation("tamyiz", vtoken, tokens[-1], subtype="nisba",
                    frame_lemma=lookup_key(verb["lexical_features"]["lemma"]),
                    dependent_reading_id=dependent["reading_id"], lexical_use="source_noun_not_adjective",
                    source_construction_example=witness)
                source_rules = {"tamyiz_nisba", (witness or frame_models[0])["source_rule"]}
                results.append(_extend(reader, tokens, base, readings=[dependent], assignments=[assigned],
                    relations=[relation], obligations=obligations, claims=claims,
                    supports=[_support(reader, rule) for rule in sorted(source_rules)], frame="event_with_tamyiz"))
                _limit(results)
    return results
