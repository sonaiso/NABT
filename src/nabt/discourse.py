"""Source-replayed questions over signed, qualified discourse claims.

This deliberately small query layer does no Horn inference or tense erasure.
It recomputes lexical evidence, scope, reference and force before every answer;
removing or replacing any premise invalidates an old answer's replay.
"""

from copy import deepcopy
from dataclasses import asdict

from .discourse_context import identity, read_context, wire
from .discourse_laws import (LAW_ID, EXPECTED_TABLE_SHA256, claim_projection_allowed,
                             installed_registry, replay_discourse_policy)
from .discourse_reader import (LANGUAGE_ID, READER_VERSION, PREDICATION_BINDING_SCHEMA, _OPERATORS,
                               read_discourse, verify_discourse)
from .errors import NabtError

_UNSET = object()
_FIELDS = ("predicate", "predicate_kind", "voice", "args", "positive", "tense", "time", "place", "restriction")


def discourse_catalog():
    from .governors import installed_table
    from .person_evidence import person_catalog
    from .construction_laws import installed_registry as construction_registry
    from .construction_reader import operator_catalog
    from .construction_sources import replay_construction_policy
    governors = installed_table()
    return {"law_id": LAW_ID, "law_sha256": EXPECTED_TABLE_SHA256,
            "language_id": LANGUAGE_ID, "reader_version": READER_VERSION,
            "claim_binding_schema": PREDICATION_BINDING_SCHEMA,
            "law": installed_registry(), "grammar_sources": replay_discourse_policy(),
            "constructions": {"law": construction_registry(),
                "grammar_sources": replay_construction_policy(), "operators": operator_catalog(),
                "scope": "SOURCE_WITNESSED_BOUNDED_COMPOSITION_WITH_PRESERVED_OPERATOR_SCOPE"},
            "person": person_catalog(), "governors": {"entries": [asdict(e) for e in governors.entries],
                "classes": [asdict(c) for c in governors.classes.values()]},
            "operator_candidates": [{"form": form, "rule": row[0], "interpretation": row[1]}
                                    for form, row in _OPERATORS.items()],
            "scope": "BOUNDED_SOURCE_REPLAYED_CLAUSES_AND_EXPLICIT_CONTEXT",
            "boundaries": ["UNKNOWN_NOUN_GENDER_IS_NOT_ACQUIRED_BY_SHAPE",
                           "BROKEN_PLURAL_SINGULAR_LINK_NEEDS_INDEPENDENT_SOURCE",
                           "WEAK_ORIGIN_TRANSFORMS_REQUIRE_WITNESSED_BASE",
                           "NO_NEAREST_ANTECEDENT_HEURISTIC",
                           "CLOSED_REFERENCE_UNIVERSE_IS_AN_EXPLICIT_PREMISE",
                           "NO_UNRESTRICTED_CAUSE_ELLIPSIS_OR_PRAGMATIC_INFERENCE",
                           "NO_TENSE_TIME_PLACE_OR_RESTRICTION_ERASURE"],
            "authority": "CONDITIONAL_LAWS_AND_CANDIDATES_NOT_ARABIC_COMPLETENESS"}


def _status(supports, refutations):
    return "CONFLICT" if supports and refutations else "SUPPORTED" if supports else "REFUTED" if refutations else "UNKNOWN"


def _constrained_person(value):
    """The one declared typed query domain; arbitrary dictionaries are not variables."""
    return (type(value) is dict and set(value) == {"kind", "name", "gender", "number"} and
            value["kind"] == "question_variable" and value["name"] == "?person" and
            value["gender"] in ("masculine", "feminine") and value["number"] == "singular")


def _match(pattern, claim, entities):
    """Instantiate explicit question variables, then compare every claim field."""
    instantiated, bindings = deepcopy(pattern), {}
    for field in ("args", "time", "place"):
        left, right = pattern[field], claim[field]
        if len(left) != len(right):
            return None
        for index, (wanted, actual) in enumerate(zip(left, right)):
            if _constrained_person(wanted):
                entity = entities.get(actual, {}) if type(actual) is str else {}
                if (field != "args" or entity.get("kind") != "person" or
                        any(entity.get(axis) != wanted[axis] for axis in ("gender", "number"))):
                    return None
                variable = wanted["name"]
                if variable in bindings and bindings[variable] != actual:
                    return None
                bindings[variable] = actual
                instantiated[field][index] = actual
                continue
            if type(wanted) is str and wanted.startswith("?"):
                if wanted in bindings and bindings[wanted] != actual:
                    return None
                if wanted == "?person" and (type(actual) is not str or
                        entities.get(actual, {}).get("kind") != "person"):
                    return None
                if wanted == "?place" and (type(actual) is not str or
                        entities.get(actual, {}).get("kind") != "place"):
                    return None
                bindings[wanted] = actual
                instantiated[field][index] = actual
    allowed = claim_projection_allowed(
        predicate_equal=all(instantiated[k] == claim[k] for k in ("predicate", "predicate_kind", "voice")),
        arguments_equal=instantiated["args"] == claim["args"],
        polarity_equal=instantiated["positive"] == claim["positive"],
        tense_equal=instantiated["tense"] == claim["tense"],
        time_equal=instantiated["time"] == claim["time"],
        place_equal=instantiated["place"] == claim["place"],
        restriction_equal=instantiated["restriction"] == claim["restriction"])
    return bindings if allowed else None


def _query_agreement_witnesses(pattern, claim, bindings, document):
    """Discharge typed person constraints on that claim's own licensed edges.

    Context compatibility alone cannot turn an ordinary noun predicate or a
    different source analysis into evidence of adjectival agreement. A
    witness must belong to this exact claim and its selected subject edge.
    """
    constraints = [(i, value) for i, value in enumerate(pattern["args"]) if _constrained_person(value)]
    if not constraints:
        return []
    if pattern["predicate_kind"] != "property" or len(pattern["args"]) != 1:
        return None
    analyses = {(c["clause_id"], a["analysis_id"]): a for c in document["clauses"]
                if c["status"] == "LICENSED" for a in c["analyses"]}
    readings = {row["reading_id"]: row for occurrence in document["occurrences"]
                for row in occurrence["readings"]}
    readings.update({row["reading_id"]: row for row in document["derived_readings"]})
    pairs = {"nominal_predicate": "nominal_subject", "kana_predicate": "kana_subject",
             "inna_predicate": "inna_subject"}
    receipts = []
    for index, constraint in constraints:
        entity_id = bindings[constraint["name"]]
        required = {axis: constraint[axis] for axis in ("gender", "number")}
        witnesses = []
        for proof in claim["proofs"]:
            analysis = analyses.get((proof["clause_id"], proof["analysis_id"]))
            claim_index = proof.get("claim_index")
            if (analysis is None or analysis["rejected_candidate"] or not analysis["licensed_syntax"] or
                    not analysis["references_complete"] or not analysis["assertion_allowed"] or
                    analysis["force"] != "ASSERT" or type(claim_index) is not int or
                    not 0 <= claim_index < len(analysis["claims"]) or
                    any(analysis["claims"][claim_index][k] != claim[k] for k in _FIELDS)):
                continue
            # Only the producer's explicit direct-claim selector may connect
            # an agreement edge to this proposition. A hash is checked against
            # the selected objects; it never replaces those checks or replay.
            for binding in analysis.get("claim_bindings", []):
                if (type(binding) is not dict or binding.get("schema") != PREDICATION_BINDING_SCHEMA or
                        type(binding.get("claim_index")) is not int or binding["claim_index"] != claim_index or
                        binding.get("claim_path") != [] or binding.get("force") != "ASSERT" or
                        binding.get("source_id") != document["source_id"] or
                        binding.get("source_sha256") != document["source_sha256"] or
                        binding.get("scope") != document["scope"] or
                        binding.get("claim_key") != identity(analysis["claims"][claim_index]) or
                        binding.get("owner_claim_key") != identity(analysis["claims"][claim_index]) or
                        binding.get("binding_id") != identity({k: v for k, v in binding.items() if k != "binding_id"}) or
                        binding["binding_id"] not in proof.get("predication_binding_ids", [])):
                    continue
                relations = [relation for relation in analysis["relations"]
                             if identity(relation) == binding.get("agreement_relation_id")]
                if len(relations) != 1:
                    continue
                relation = relations[0]
                if (relation.get("kind") != "predicate_agreement" or relation.get("status") != "confirmed" or
                        relation.get("regime_licensed") is not True or
                        relation.get("predicate_lemma") != claim["predicate"] or
                        relation.get("head_reading_id") != binding.get("subject_reading_id") or
                        relation.get("dependent_reading_id") != binding.get("predicate_reading_id") or
                        relation.get("head_span") != binding.get("subject_span") or
                        relation.get("dependent_span") != binding.get("predicate_span") or
                        relation.get("subject_role") != binding.get("subject_role") or
                        relation.get("predicate_role") != binding.get("predicate_role") or
                        relation.get("predicate_role") not in pairs or
                        pairs[relation["predicate_role"]] != relation.get("subject_role") or
                        type(binding.get("subject_reference_ids")) is not list or
                        len(binding["subject_reference_ids"]) != 1 or
                        any(type(value) is not str or value not in relation.get("subject_reference_ids", [])
                            for value in binding["subject_reference_ids"]) or
                        any(relation.get("axes", {}).get(axis) != "confirmed" for axis in required) or
                        any(relation.get("subject_profile", {}).get(axis) != value
                            for axis, value in required.items()) or
                        any(relation.get("predicate_profile", {}).get(axis) != value
                            for axis, value in required.items())):
                    continue
                predicate = readings.get(binding["predicate_reading_id"])
                if (predicate is None or predicate.get("kind") != "noun" or
                        predicate.get("lexical_features", {}).get("pos") != "ADJ" or
                        predicate["lexical_features"].get("lemma") != claim["predicate"] or
                        any(binding[key] not in analysis["reading_ids"] for key in
                            ("subject_reading_id", "predicate_reading_id"))):
                    continue
                assigned = [[a for a in analysis["assignments"] if a.get("activated") is True and
                             a.get("compatible") is True and a.get("reading_id") == binding[side + "_reading_id"] and
                             a.get("span") == binding[side + "_span"] and a.get("role") == binding[side + "_role"]]
                            for side in ("subject", "predicate")]
                if not any((p.get("head_span") == s["span"] if p["role"] == "nominal_predicate" else
                            p.get("head_span") is not None and p["head_span"] == s.get("head_span"))
                           for s in assigned[0] for p in assigned[1]):
                    continue
                if any(scoped.get("kind") == "relative_clause"
                       and scoped.get("inner_predicate_reading_id") == relation.get("dependent_reading_id")
                       and scoped.get("inner_predicate_span") == relation.get("dependent_span")
                       for scoped in analysis["relations"]):
                    # The resumptive clause is a description inside the
                    # relative. Its adjective cannot certify the distinct
                    # outer assertion, even if lemma and individual coincide.
                    continue
                for reference in analysis["references"]:
                    if (reference.get("status") == "RESOLVED" and reference["bound_entity_id"] == entity_id and
                            reference["span"] == relation["head_span"] and
                            reference.get("context_sha256") == document["context"]["sha256"] and
                            reference["reference_id"] in binding.get("subject_reference_ids", []) and
                            reference["reference_id"] in relation["subject_reference_ids"]):
                        witness = {"clause_id": proof["clause_id"], "analysis_id": proof["analysis_id"],
                            "predication_binding_id": binding["binding_id"],
                            "head_reading_id": relation["head_reading_id"],
                            "dependent_reading_id": relation["dependent_reading_id"],
                            "reference_id": reference["reference_id"]}
                        if witness not in witnesses:
                            witnesses.append(witness)
        if not witnesses:
            return None
        receipts.append({"argument_index": index, "variable": constraint["name"], "entity_id": entity_id,
            "required_profile": required, "context_sha256": document["context"]["sha256"],
            "source_witnesses": witnesses})
    return receipts


def _predicate_interpretations(claim, document):
    """Explain each selected nominal predicate using its own replayed sources.

    Corpus derivation tags belong to the selected lexical reading. Descriptive
    morphology readings only share an exact source occurrence: they remain
    conditional alternatives until a separate sense correspondence is known.
    Neither axis changes a grammatical claim into a real-world judgment.
    """
    analyses = {(c["clause_id"], a["analysis_id"]): a for c in document["clauses"]
                if c["status"] == "LICENSED" for a in c["analyses"]}
    readings = {r["reading_id"]: r for o in document["occurrences"] for r in o["readings"]}
    readings.update({r["reading_id"]: r for r in document["derived_readings"]})
    morphology = document.get("nominal_morphology")
    occurrences = [] if morphology is None else morphology["occurrences"]
    explanations = []
    for proof in claim["proofs"]:
        analysis = analyses.get((proof["clause_id"], proof["analysis_id"]))
        if (analysis is None or analysis["rejected_candidate"] or not analysis["licensed_syntax"]
                or not analysis["references_complete"] or not analysis["assertion_allowed"]):
            continue
        index = proof.get("claim_index")
        if (type(index) is not int or not 0 <= index < len(analysis["claims"])
                or any(analysis["claims"][index][k] != claim[k] for k in _FIELDS)):
            continue
        for binding in analysis.get("claim_bindings", []):
            if (binding["binding_id"] not in proof.get("predication_binding_ids", [])
                    or binding["claim_index"] != index):
                continue
            selected = analysis["claims"][index]
            path = binding["claim_path"]
            if path:
                if (len(path) != 4 or path[0] != "restriction" or path[2] != "embedded"
                        or type(path[1]) is not int or type(path[3]) is not int
                        or not 0 <= path[1] < len(selected["restriction"])):
                    continue
                scoped = selected["restriction"][path[1]]
                if (type(scoped) is not dict or scoped.get("kind") != "operator_scope"
                        or not 0 <= path[3] < len(scoped.get("embedded", []))):
                    continue
                selected = scoped["embedded"][path[3]]
            if selected["predicate_kind"] != "property":
                continue
            reading = readings.get(binding["predicate_reading_id"])
            if reading is None or reading["kind"] != "noun":
                continue
            features = reading["lexical_features"]
            if features.get("lemma") != selected["predicate"]:
                continue
            candidates = [o for o in occurrences if o["span"] == binding["predicate_span"]]
            alternatives = []
            for occurrence in candidates:
                for row in occurrence["readings"]:
                    if row["lexical_link"] is None:
                        continue
                    alternatives.append({"reading_id": row["reading_id"],
                        "identity": deepcopy(row["identity"]),
                        "lexical_link": deepcopy(row["lexical_link"]),
                        "kind": deepcopy(row["axes"]["kind"]),
                        "nominal_semantics": deepcopy(row["axes"]["nominal_semantics"]),
                        "premises": deepcopy([p for p in row["linked_properties"]
                            if p["property"] in ("independent", "time_in_form", "universal", "property_bearing")]),
                        "blockers": deepcopy(row["blockers"]),
                        "condition": "IF_THIS_DESCRIPTIVE_READING_IS_THE_SELECTED_PREDICATE_SENSE"})
            tags = deepcopy(features.get("nominal_derivation_features") or [])
            missing = (["LEXICAL_UNIVERSAL_AND_PROPERTY_BEARING_WITNESS"] if not alternatives
                       else ["DESCRIPTIVE_READING_TO_LEXICAL_SENSE_CORRESPONDENCE"])
            explanation = {"schema": "nabt.nominal-predicate-interpretation.v1",
                "clause_id": proof["clause_id"], "analysis_id": proof["analysis_id"],
                "predication_binding_id": binding["binding_id"],
                "owner_claim_id": claim["claim_id"], "claim_path": deepcopy(path),
                "predicate_claim": deepcopy(selected),
                "assertion_scope": "EMBEDDED_IN_OWNER_CLAIM_NOT_ASSERTED_SEPARATELY" if path else
                    "ASSERTED_SOURCE_CLAIM",
                "predicate_reading_id": reading["reading_id"],
                "predicate_span": deepcopy(binding["predicate_span"]),
                "predicate": selected["predicate"],
                "source_lexical_id": reading.get("identity", {}).get("lexical_id") or
                    reading.get("person_evidence", {}).get("source_lexical_id"),
                "grammatical_kind": reading["kind"],
                "grammatical_profile": {k: features.get(k) for k in ("gender", "number", "person")},
                "derivation": {"status": "SOURCE_QUALIFIED" if tags else "DEFER",
                    "features": tags, "support_records": deepcopy(reading["support_records"]),
                    "missing": [] if tags else ["NOMINAL_DERIVATION_SOURCE_FEATURES"],
                    "authority": "ANNOTATED_LEXICAL_READING_NOT_WEIGHT_INFERENCE"},
                "nominal_denotation": {"status": "SOURCE_READING_CANDIDATES" if alternatives else "DEFER",
                    "alternatives": alternatives, "missing": missing,
                    "sense_equivalence_established": False,
                    "authority": "EXACT_OCCURRENCE_DESCRIPTIVE_ALTERNATIVES_NOT_CORPUS_SENSE_IDENTITY"},
                "world_truth": "NOT_ESTABLISHED"}
            explanation["interpretation_id"] = identity(explanation)
            explanations.append(explanation)
    return explanations


def _evaluate_interpretation(interpretation, document, inquiry, entities, nominal_cache, nominal_used):
    """Evaluate one complete question reading against the same full source."""
    positive, negative, grouped = [], [], {}
    missing = []
    pattern = interpretation["query"]
    opposite = {**deepcopy(pattern), "positive": not pattern["positive"]}
    for claim in document["claims"]:
        for desired, target, sign in ((pattern, positive, "proofs"), (opposite, negative, "counterproofs")):
            bindings = _match(desired, claim, entities)
            if bindings is None:
                continue
            agreement = _query_agreement_witnesses(desired, claim, bindings, document)
            if agreement is None:
                missing.append("CLAIM_PREDICATION_AGREEMENT_WITNESS_REQUIRED")
                continue
            proof = {"claim_id": claim["claim_id"], "document_report_id": document["report_id"],
                     "question_report_id": inquiry["report_id"],
                     "question_analysis_id": interpretation["analysis_id"], "bindings": bindings,
                     "source_proofs": deepcopy(claim["proofs"]),
                     "rule": "EXACT_SIGNED_QUALIFIED_CLAIM_WITH_EXPLICIT_VARIABLE_SUBSTITUTION"}
            if agreement:
                proof["predicate_agreement_bindings"] = agreement
            if claim["claim_id"] not in nominal_cache:
                nominal_cache[claim["claim_id"]] = _predicate_interpretations(claim, document)
            nominal = nominal_cache[claim["claim_id"]]
            if nominal:
                proof["predicate_interpretation_ids"] = [row["interpretation_id"] for row in nominal]
                nominal_used.update({row["interpretation_id"]: row for row in nominal})
            target.append(proof)
            key = wire(bindings)
            grouped.setdefault(key, {"values": bindings, "proofs": [], "counterproofs": []})[sign].append(proof)
    interpretation["proofs"], interpretation["counterproofs"] = positive, negative
    interpretation["missing_premises"] = sorted(set(missing))
    if interpretation["kind"] == "polar":
        interpretation["status"] = _status(positive, negative)
    else:
        interpretation["bindings"] = [
            {**grouped[key], "status": _status(grouped[key]["proofs"], grouped[key]["counterproofs"])}
            for key in sorted(grouped) if grouped[key]["proofs"]]
        interpretation["status"] = (
            "CONFLICT" if any(b["status"] == "CONFLICT" for b in interpretation["bindings"]) else
            "SUPPORTED" if interpretation["bindings"] else "UNKNOWN")


def _interpretation_outcome(interpretation):
    """Compare whole outcomes, including the bound signed source-claim sets.

    Agreement is not a union of whichever bindings each reading can prove.
    Separate typed/untyped proof receipts may justify the same source claim;
    different source claims or missing opposition remain different outcomes.
    """
    return wire({"kind": interpretation["kind"], "status": interpretation["status"],
        "bindings": sorted(({"values": b["values"], "status": b["status"]}
                            for b in interpretation["bindings"]), key=wire),
        "signs": {sign: sorted({wire([p["bindings"], p["claim_id"]]).decode("utf-8")
                               for p in interpretation[sign]})
                  for sign in ("proofs", "counterproofs")}})


def ask_discourse(text, question, *, lexical_model=None, context=None,
                  source_id="input", scope="default", lexical_text=None, lexical_source_id="lexical"):
    document = read_discourse(text, lexical_model=lexical_model, context=context,
                              source_id=source_id, scope=scope, lexical_text=lexical_text,
                              lexical_source_id=lexical_source_id)
    inquiry = read_discourse(question, lexical_model=lexical_model, context=context,
                             source_id="question", scope=scope, lexical_text=lexical_text,
                             lexical_source_id=lexical_source_id)
    result = {"schema": "nabt.discourse-answer.v3", "law_id": LAW_ID,
              "law_sha256": EXPECTED_TABLE_SHA256, "language_id": LANGUAGE_ID,
              "reader_version": READER_VERSION, "source_id": source_id, "scope": scope,
              "source_text": document["source_text"], "question_text": inquiry["source_text"],
              "source_sha256": document["source_sha256"], "question_sha256": inquiry["source_sha256"],
              "document_report_id": document["report_id"], "question_report_id": inquiry["report_id"],
              "context_sha256": document["context"]["sha256"], "lexical_model": document["lexical_model"],
              "nominal_description_source": None if document["nominal_morphology"] is None else
                  deepcopy(document["nominal_morphology"]["lexical_source"]),
              "status": "DEFER", "kind": None, "query": None, "bindings": [],
              "question_interpretations": [], "answer_basis": None,
              "predicate_interpretations": [],
              "proofs": [], "counterproofs": [], "missing_premises": [],
              "authority": "SOURCE_RELATIVE_ANSWER_REPLAY_NOT_WORLD_TRUTH", "world_truth": "NOT_ESTABLISHED"}
    if document["status"] != "LICENSED_DISCOURSE":
        result["missing_premises"].append("COMPLETE_SOURCE_DISCOURSE_READING")
    if len(inquiry["clauses"]) != 1:
        result["missing_premises"].append("ONE_COMPLETE_QUESTION_READING")
    else:
        clause = inquiry["clauses"][0]
        viable = [a for a in clause["analyses"] if not a["rejected_candidate"]]
        analyses = [a for a in viable if a["licensed_syntax"] and a["references_complete"]]
        # A DEFER report may retain several complete semantic readings. Those
        # can be answered only by evaluating every one; an incomplete viable
        # alternative still blocks any accepted answer.
        if not analyses or len(analyses) != len(viable):
            result["missing_premises"].append("ONE_COMPLETE_QUESTION_READING")
        elif any(a["force"] != "QUESTION" or len(a["claims"]) != 1 for a in analyses):
            result["missing_premises"].append("EXPLICIT_SINGLE_QUESTION_FORCE")
        else:
            result["question_interpretations"] = [
                {"clause_id": clause["clause_id"], "analysis_id": a["analysis_id"],
                 "kind": a.get("question_kind") or "polar", "query": deepcopy(a["claims"][0]),
                 "status": "DEFER", "bindings": [], "proofs": [], "counterproofs": [], "missing_premises": []}
                for a in analyses]
            kinds = {a["kind"] for a in result["question_interpretations"]}
            queries = {wire(a["query"]) for a in result["question_interpretations"]}
            if len(kinds) == 1:
                result["kind"] = next(iter(kinds))
            if len(queries) == 1:
                result["query"] = deepcopy(result["question_interpretations"][0]["query"])
    if not result["missing_premises"]:
        entities = {e["id"]: e for e in read_context(context)["value"]["entities"]}
        interpretations = result["question_interpretations"]
        nominal_cache, nominal_used = {}, {}
        for interpretation in interpretations:
            _evaluate_interpretation(interpretation, document, inquiry, entities, nominal_cache, nominal_used)
        result["predicate_interpretations"] = [nominal_used[key] for key in sorted(nominal_used)]
        result["missing_premises"].extend(sorted({premise for interpretation in interpretations
                                                 for premise in interpretation["missing_premises"]}))
        if len({_interpretation_outcome(a) for a in interpretations}) != 1:
            result["missing_premises"].append("QUESTION_INTERPRETATION_OUTCOMES_DISAGREE")
        else:
            result["status"] = interpretations[0]["status"]
            result["answer_basis"] = "ALL_COMPLETE_QUERY_INTERPRETATIONS_AGREE"
            for sign in ("proofs", "counterproofs"):
                result[sign] = [deepcopy(proof) for a in interpretations for proof in a[sign]]
            if result["kind"] != "polar":
                # The set is already identical in every interpretation. Merge
                # only its proof receipts, never add a binding from a subset.
                for binding in interpretations[0]["bindings"]:
                    merged = {"values": deepcopy(binding["values"]), "status": binding["status"]}
                    for sign in ("proofs", "counterproofs"):
                        merged[sign] = [p for p in result[sign] if p["bindings"] == binding["values"]]
                    result["bindings"].append(merged)
    result["answer_id"] = identity(result)
    wire(result)
    return result


def verify_discourse_answer(report, *, text=_UNSET, question=_UNSET, lexical_model=None,
                            context=None, source_id=None, scope=None, lexical_text=None,
                            lexical_source_id="lexical"):
    try:
        if type(report) is not dict:
            return {"valid": False, "status": "REJECT", "code": "INVALID_DISCOURSE_ANSWER"}
        fresh = ask_discourse(report["source_text"] if text is _UNSET else text,
                             report["question_text"] if question is _UNSET else question,
                             lexical_model=lexical_model, context=context,
                             source_id=report["source_id"] if source_id is None else source_id,
                             scope=report["scope"] if scope is None else scope,
                             lexical_text=lexical_text, lexical_source_id=lexical_source_id)
        if wire(report) != wire(fresh):
            return {"valid": False, "status": "REJECT", "code": "DISCOURSE_ANSWER_REPLAY_MISMATCH"}
        return {"valid": True, "status": "VERIFIED", "answer_id": fresh["answer_id"],
                "authority": "COMPLETE_SOURCE_CONTEXT_AND_QUESTION_REPLAY_ONLY"}
    except (KeyError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, "status": "DEFER", "code": error.code}
        return {"valid": False, "status": "REJECT", "code": "INVALID_DISCOURSE_ANSWER"}


__all__ = ["read_discourse", "verify_discourse", "ask_discourse", "verify_discourse_answer", "discourse_catalog"]
