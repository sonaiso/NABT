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
from .discourse_reader import (LANGUAGE_ID, READER_VERSION, _OPERATORS,
                               read_discourse, verify_discourse)
from .errors import NabtError

_UNSET = object()
_FIELDS = ("predicate", "predicate_kind", "voice", "args", "positive", "tense", "time", "place", "restriction")


def discourse_catalog():
    from .governors import installed_table
    from .person_evidence import person_catalog
    governors = installed_table()
    return {"law_id": LAW_ID, "law_sha256": EXPECTED_TABLE_SHA256,
            "language_id": LANGUAGE_ID, "reader_version": READER_VERSION,
            "law": installed_registry(), "grammar_sources": replay_discourse_policy(),
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


def _match(pattern, claim, entities):
    """Instantiate explicit question variables, then compare every claim field."""
    instantiated, bindings = deepcopy(pattern), {}
    for field in ("args", "time", "place"):
        left, right = pattern[field], claim[field]
        if len(left) != len(right):
            return None
        for index, (wanted, actual) in enumerate(zip(left, right)):
            if type(wanted) is str and wanted.startswith("?"):
                if wanted in bindings and bindings[wanted] != actual:
                    return None
                if wanted == "?person" and entities.get(actual, {}).get("kind") != "person":
                    return None
                if wanted == "?place" and entities.get(actual, {}).get("kind") != "place":
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


def ask_discourse(text, question, *, lexical_model=None, context=None,
                  source_id="input", scope="default"):
    document = read_discourse(text, lexical_model=lexical_model, context=context,
                              source_id=source_id, scope=scope)
    inquiry = read_discourse(question, lexical_model=lexical_model, context=context,
                             source_id="question", scope=scope)
    result = {"schema": "nabt.discourse-answer.v1", "law_id": LAW_ID,
              "law_sha256": EXPECTED_TABLE_SHA256, "language_id": LANGUAGE_ID,
              "reader_version": READER_VERSION, "source_id": source_id, "scope": scope,
              "source_text": document["source_text"], "question_text": inquiry["source_text"],
              "source_sha256": document["source_sha256"], "question_sha256": inquiry["source_sha256"],
              "document_report_id": document["report_id"], "question_report_id": inquiry["report_id"],
              "context_sha256": document["context"]["sha256"], "lexical_model": document["lexical_model"],
              "status": "DEFER", "kind": None, "query": None, "bindings": [],
              "proofs": [], "counterproofs": [], "missing_premises": [],
              "authority": "SOURCE_RELATIVE_ANSWER_REPLAY_NOT_WORLD_TRUTH", "world_truth": "NOT_ESTABLISHED"}
    if document["status"] != "LICENSED_DISCOURSE":
        result["missing_premises"].append("COMPLETE_SOURCE_DISCOURSE_READING")
    if inquiry["status"] != "LICENSED_DISCOURSE" or len(inquiry["clauses"]) != 1:
        result["missing_premises"].append("ONE_COMPLETE_QUESTION_READING")
    else:
        clause = inquiry["clauses"][0]
        if clause["force"] != "QUESTION" or not clause["analyses"] or len(clause["analyses"][0]["claims"]) != 1:
            result["missing_premises"].append("EXPLICIT_SINGLE_QUESTION_FORCE")
        else:
            analysis = clause["analyses"][0]
            result["kind"] = analysis.get("question_kind") or "polar"
            result["query"] = deepcopy(analysis["claims"][0])
    if not result["missing_premises"]:
        entities = {e["id"]: e for e in read_context(context)["value"]["entities"]}
        positive, negative, grouped = [], [], {}
        pattern = result["query"]
        opposite = {**deepcopy(pattern), "positive": not pattern["positive"]}
        for claim in document["claims"]:
            for desired, target, sign in ((pattern, positive, "proofs"), (opposite, negative, "counterproofs")):
                bindings = _match(desired, claim, entities)
                if bindings is None:
                    continue
                proof = {"claim_id": claim["claim_id"], "document_report_id": document["report_id"],
                         "question_report_id": inquiry["report_id"], "bindings": bindings,
                         "source_proofs": deepcopy(claim["proofs"]),
                         "rule": "EXACT_SIGNED_QUALIFIED_CLAIM_WITH_EXPLICIT_VARIABLE_SUBSTITUTION"}
                target.append(proof)
                key = wire(bindings)
                grouped.setdefault(key, {"values": bindings, "proofs": [], "counterproofs": []})[sign].append(proof)
        result["proofs"], result["counterproofs"] = positive, negative
        if result["kind"] == "polar":
            result["status"] = _status(positive, negative)
        else:
            result["bindings"] = [{**grouped[key], "status": _status(grouped[key]["proofs"], grouped[key]["counterproofs"])}
                                  for key in sorted(grouped) if grouped[key]["proofs"]]
            result["status"] = ("CONFLICT" if any(b["status"] == "CONFLICT" for b in result["bindings"]) else
                                "SUPPORTED" if result["bindings"] else "UNKNOWN")
    result["answer_id"] = identity(result)
    wire(result)
    return result


def verify_discourse_answer(report, *, text=_UNSET, question=_UNSET, lexical_model=None,
                            context=None, source_id=None, scope=None):
    try:
        if type(report) is not dict:
            return {"valid": False, "status": "REJECT", "code": "INVALID_DISCOURSE_ANSWER"}
        fresh = ask_discourse(report["source_text"] if text is _UNSET else text,
                             report["question_text"] if question is _UNSET else question,
                             lexical_model=lexical_model, context=context,
                             source_id=report["source_id"] if source_id is None else source_id,
                             scope=report["scope"] if scope is None else scope)
        if wire(report) != wire(fresh):
            return {"valid": False, "status": "REJECT", "code": "DISCOURSE_ANSWER_REPLAY_MISMATCH"}
        return {"valid": True, "status": "VERIFIED", "answer_id": fresh["answer_id"],
                "authority": "COMPLETE_SOURCE_CONTEXT_AND_QUESTION_REPLAY_ONLY"}
    except (KeyError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, "status": "DEFER", "code": error.code}
        return {"valid": False, "status": "REJECT", "code": "INVALID_DISCOURSE_ANSWER"}


__all__ = ["read_discourse", "verify_discourse", "ask_discourse", "verify_discourse_answer", "discourse_catalog"]
