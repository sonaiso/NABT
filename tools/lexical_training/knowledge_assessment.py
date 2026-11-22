"""Bounded separation of received information, claim assessment, and link audit.

All measurement intervals and semantic bindings are author-supplied fixtures.
An interval is assumed to bound a quantity under an explicitly declared policy;
it is not a confidence interval estimated from hardware. No neurobiological,
Arabic parsing, causal discovery, or general analogy engine is implemented.
"""
from __future__ import annotations

from itertools import product

from .knowledge_records import Operation, Outcome, Record, Ref, closure

SCOPE_FIELDS = ("subject", "property", "unit", "event_time")
ASSESSMENT_STATES = frozenset({"SUPPORTED", "REFUTED", "CONFLICTED", "UNDETERMINED"})


def _licensed_output(store, record):
    return any(op_id in store.operations and store.operations[op_id].status == "LICENSED"
               and store.operations[op_id].domain == record.domain
               and record.ref in store.operations[op_id].outputs for op_id in record.trace)


def bound_relation(lower, upper, threshold):
    """Relation of a closed interval to the strict predicate x > threshold."""
    if lower > threshold:
        return "SUPPORTS"
    if upper <= threshold:
        return "COUNTERS"
    return "INCONCLUSIVE"


def _interval_relation(store, information, conception, claim, accepted_sources):
    if information.kind != "information":
        return None, None, "wrong_information_kind"
    if information.domain != claim.domain:
        return None, None, "domain_mismatch"
    if (conception is None or conception.kind != "conception" or conception.domain != information.domain
            or conception.dependencies != (information.ref,) or not _licensed_output(store, conception)):
        return None, None, "interval_interpretation_missing"
    data, proposition = conception.content, claim.content
    if any(type(data.get(k)) is not str or not data[k] for k in SCOPE_FIELDS):
        return None, None, "scope_field_missing"
    for key in SCOPE_FIELDS:
        if data[key] != proposition[key]:
            return None, None, key + "_mismatch"
    if type(data.get("lower")) is not int or type(data.get("upper")) is not int:
        return None, None, "integer_interval_required"
    if data["lower"] > data["upper"]:
        return None, None, "reversed_interval"
    if len(information.sources) != 1:
        return None, None, "one_original_occurrence_required"
    source_ref = information.sources[0]
    source = store.records.get(source_ref)
    if source_ref not in accepted_sources:
        return None, None, "occurrence_not_accepted_by_policy"
    if source is None or source.kind != "occurrence" or source.domain != information.domain:
        return None, None, "source_occurrence_missing_or_wrong"
    if any(source.content.get(k) != data.get(k) or information.content.get(k) != data.get(k)
           for k in SCOPE_FIELDS + ("lower", "upper", "channel", "source", "received_at")):
        return None, None, "information_differs_from_source"
    if closure(store, (information.ref,)).status != "LICENSED" or not all(_licensed_output(store, r) for r in (source, information)):
        return None, None, "reception_trace_incomplete"
    relation = bound_relation(data["lower"], data["upper"], proposition["threshold"])
    reason = "interval_crosses_predicate_boundary" if relation == "INCONCLUSIVE" else None
    return relation, source_ref, reason


def assess_threshold(store, claim_ref, information_refs, policy_ref, assessment_id, *, version, previous, at):
    """Assess x > k relative to one declared bounded-interval policy.

    The assessment is an independent immutable record. Information records and
    the claim are never changed. Sources are occurrence references, not devices.
    """
    if type(claim_ref) is not Ref or type(policy_ref) is not Ref or (previous is not None and type(previous) is not Ref):
        return Outcome("BLOCK", reasons=("wrong_claim_policy_or_previous_reference_type",))
    claim, policy = store.records.get(claim_ref), store.records.get(policy_ref)
    if claim is None or policy is None:
        return Outcome("DEFER", reasons=("claim_or_policy_missing",))
    if claim.kind != "claim" or policy.kind != "prior":
        return Outcome("BLOCK", reasons=("wrong_claim_or_policy_kind",))
    c, p = claim.content, policy.content
    if c.get("predicate") != "greater_than" or type(c.get("threshold")) is not int:
        return Outcome("BLOCK", reasons=("unsupported_claim_predicate",))
    if any(type(c.get(k)) is not str or not c[k] for k in SCOPE_FIELDS):
        return Outcome("DEFER", reasons=("claim_scope_incomplete",))
    if policy.domain != claim.domain or p.get("rule") != "trusted_bounded_interval/v1":
        return Outcome("BLOCK", reasons=("policy_domain_or_rule_mismatch",))
    if policy.provenance_mode != "declared_evaluation_policy" or not _licensed_output(store, policy):
        return Outcome("DEFER", reasons=("policy_declaration_missing",))
    try:
        accepted_sources = set(Ref.read(r) for r in p["accepted_occurrences"])
    except (KeyError, TypeError, ValueError):
        return Outcome("BLOCK", reasons=("malformed_policy_sources",))
    if not accepted_sources.issubset(set(policy.sources)) or closure(store, (policy.ref, claim.ref)).status != "LICENSED":
        return Outcome("DEFER", reasons=("policy_or_claim_provenance_incomplete",))
    information_refs = tuple(information_refs)
    if any(type(r) is not Ref for r in information_refs):
        return Outcome("BLOCK", reasons=("wrong_information_reference_type",))
    seen, supporting, countering, inconclusive, evaluations, residuals = {}, [], [], [], [], []
    matched_intervals = []
    known_refs = []
    for ref in information_refs:
        row = {"information": ref.data()}
        information = store.records.get(ref)
        if information is None:
            relation, source_ref, reason = None, None, "information_missing"
        else:
            known_refs.append(ref)
            concept_ref = Ref("interpret/" + information.ref.record_id, information.ref.version)
            conception = store.records.get(concept_ref)
            if conception is not None:
                known_refs.append(concept_ref)
            relation, source_ref, reason = _interval_relation(store, information, conception, claim, accepted_sources)
        if relation is None:
            row.update(relation="INAPPLICABLE", reason=reason)
            residuals.append(ref.record_id + ":" + reason)
        elif source_ref in seen:
            row.update(relation="DUPLICATE_OCCURRENCE", source=source_ref.data(), duplicate_of=seen[source_ref].data())
        else:
            seen[source_ref] = ref
            matched_intervals.append((information.content["lower"], information.content["upper"]))
            row.update(relation=relation, source=source_ref.data())
            {"SUPPORTS": supporting, "COUNTERS": countering, "INCONCLUSIVE": inconclusive}[relation].append(ref)
            if reason:
                row["reason"] = reason
                residuals.append(ref.record_id + ":" + reason)
        evaluations.append(row)
    intersection = ({"lower": max(x[0] for x in matched_intervals),
                     "upper": min(x[1] for x in matched_intervals)} if matched_intervals else None)
    intervals_consistent = intersection is None or intersection["lower"] <= intersection["upper"]
    state = ("CONFLICTED" if (supporting and countering) or not intervals_consistent else "SUPPORTED" if supporting
             else "REFUTED" if countering else "UNDETERMINED")
    if not information_refs:
        residuals.append("no_evidence_supplied")
    if state == "CONFLICTED":
        residuals.append("inconsistent_applicable_intervals_require_review")
    deps = tuple(dict.fromkeys((claim.ref, policy.ref) + tuple(known_refs) + ((previous,) if previous else ())))
    if previous and (previous not in store.records or store.records[previous].kind != "assessment"):
        return Outcome("DEFER", reasons=("previous_assessment_missing",))
    if previous:
        old = store.records[previous]
        if (old.ref.record_id != assessment_id or old.ref.version >= version
                or old.domain != claim.domain or claim.ref not in old.dependencies
                or old.content.get("claim") != claim.ref.data()
                or old.content.get("scope") != {k: c[k] for k in SCOPE_FIELDS}
                or old.content.get("predicate") != c["predicate"]
                or old.content.get("threshold") != c["threshold"]
                or old.provenance_mode != "computed_assessment" or not _licensed_output(store, old)):
            return Outcome("BLOCK", reasons=("previous_assessment_identity_scope_or_version_mismatch",))
    op_id = assessment_id + "@" + str(version) + ":assess"
    assessment = Record.make(assessment_id, version, "assessment", claim.domain,
        {"claim": claim.ref.data(), "policy": policy.ref.data(), "assessed_at": at, "status": state,
         "supporting_information": [r.data() for r in supporting],
         "countering_information": [r.data() for r in countering],
         "inconclusive_information": [r.data() for r in inconclusive], "evaluations": evaluations,
         "distinct_occurrence_count": len(seen), "scope": {k: c[k] for k in SCOPE_FIELDS},
         "evidence_consistency": "CONSISTENT" if intervals_consistent else "INCONSISTENT",
         "common_interval": intersection if intervals_consistent else None,
         "predicate": "greater_than", "threshold": c["threshold"],
         "qualification": "relative to declared interval policy; no statement of speaker dishonesty",
         "previous_assessment": previous.data() if previous else None},
        "computed_assessment", dependencies=deps, residuals=tuple(residuals), trace=(op_id,))
    store.log(Operation(op_id, "assess_bounded_interval", claim.domain, deps, (assessment.ref,),
                        "LICENSED", "lower > threshold supports; upper <= threshold counters; overlap is inconclusive"))
    store.add(assessment)
    return Outcome("LICENSED", assessment)


def _variables(expr, depth=0):
    if depth > 16:
        raise ValueError("formula_depth_limit")
    if type(expr) is bool:
        return set()
    if type(expr) is str and expr and len(expr) <= 32:
        return {expr}
    if type(expr) is not list or not expr:
        raise ValueError("unsupported_formula")
    arity = {"not": 1, "and": 2, "or": 2, "implies": 2}.get(expr[0]) if type(expr[0]) is str else None
    if arity is None or len(expr) != arity + 1:
        raise ValueError("unsupported_formula_operator_or_arity")
    return set().union(*(_variables(x, depth + 1) for x in expr[1:]))


def _evaluate(expr, assignment):
    if type(expr) is bool:
        return expr
    if type(expr) is str:
        return assignment[expr]
    op, first, *rest = expr
    a = _evaluate(first, assignment)
    if op == "not":
        return not a
    b = _evaluate(rest[0], assignment)
    return {"and": a and b, "or": a or b, "implies": (not a) or b}[op]


def truth_table(premises, conclusion):
    """Exhaustive only for the declared propositional language with <=3 atoms."""
    try:
        premises = tuple(premises)
        variables = sorted(set().union(*(_variables(p) for p in premises + (conclusion,))))
        if len(variables) > 3:
            raise ValueError("more_than_three_atoms")
        satisfying = 0
        for values in product((False, True), repeat=len(variables)):
            assignment = dict(zip(variables, values))
            if all(_evaluate(p, assignment) for p in premises):
                satisfying += 1
                if not _evaluate(conclusion, assignment):
                    return {"formal_status": "INVALID", "countermodel": assignment,
                            "atoms": variables, "premises_satisfiable": True}
        return {"formal_status": "VALID", "countermodel": None, "atoms": variables,
                "premises_satisfiable": bool(satisfying)}
    except (TypeError, ValueError) as error:
        return {"formal_status": "UNPROVED", "countermodel": None, "reason": str(error)}


def audit_link(store, premise_refs, conclusion_ref, assessment_refs, audit_id, *, at):
    premise_refs, assessment_refs = tuple(premise_refs), tuple(assessment_refs)
    if any(type(r) is not Ref for r in premise_refs + assessment_refs + (conclusion_ref,)):
        return Outcome("BLOCK", reasons=("wrong_audit_reference_type",))
    refs = tuple(dict.fromkeys(premise_refs + (conclusion_ref,) + assessment_refs))
    if closure(store, refs).status != "LICENSED":
        return Outcome("DEFER", reasons=("audit_provenance_incomplete",))
    premises = [store.records[r] for r in premise_refs]
    conclusion = store.records[conclusion_ref]
    if conclusion.kind != "claim" or any(r.kind not in ("claim", "prior") for r in premises):
        return Outcome("BLOCK", reasons=("wrong_premise_or_conclusion_kind",))
    formal = truth_table([r.content.get("formula") for r in premises], conclusion.content.get("formula"))
    by_claim = {}
    for ref in assessment_refs:
        assessment = store.records[ref]
        if assessment.kind != "assessment" or assessment.content.get("status") not in ASSESSMENT_STATES or assessment.provenance_mode != "computed_assessment":
            return Outcome("BLOCK", reasons=("invalid_assessment_record",))
        try:
            assessed_claim = Ref.read(assessment.content["claim"])
        except (ValueError, TypeError, KeyError):
            return Outcome("BLOCK", reasons=("invalid_assessment_claim_reference",))
        target = store.records.get(assessed_claim)
        if (target is None or target.kind != "claim" or target.domain != assessment.domain
                or assessed_claim not in assessment.dependencies
                or assessment.content.get("scope") != {k: target.content.get(k) for k in SCOPE_FIELDS}
                or assessment.content.get("predicate") != target.content.get("predicate")
                or assessment.content.get("threshold") != target.content.get("threshold")
                or not any(store.operations[op].name == "assess_bounded_interval"
                           and store.operations[op].status == "LICENSED"
                           and assessment.ref in store.operations[op].outputs
                           and store.operations[op].domain == assessment.domain
                           for op in assessment.trace if op in store.operations)):
            return Outcome("BLOCK", reasons=("assessment_claim_scope_or_trace_mismatch",))
        by_claim.setdefault(assessed_claim, []).append(assessment)
    reviews, defects, pending = [], [], []
    symbol_bindings, binding_conflicts = {}, []
    rule_claims = [store.records[ref] for rule in premises if rule.kind == "prior" for ref in rule.dependencies]
    for record in rule_claims + premises + [conclusion]:
        atom = record.content.get("formula")
        if record.kind == "claim" and type(atom) is str:
            signature = {"domain": record.domain, **{k: record.content.get(k) for k in
                         SCOPE_FIELDS + ("predicate", "threshold")}}
            if atom in symbol_bindings and symbol_bindings[atom]["signature"] != signature:
                binding_conflicts.append({"atom": atom, "first": symbol_bindings[atom]["claim"],
                                          "second": record.ref.data(), "second_signature": signature})
                defects.append("SYMBOL_BINDING_CONFLICT:" + atom)
            else:
                symbol_bindings[atom] = {"claim": record.ref.data(), "signature": signature}
    for record in premises:
        matches = by_claim.get(record.ref, [])
        if record.kind == "prior" and record.provenance_mode == "declared_model_rule" and record.content.get("rule_kind") == "stipulated_axiom" and _licensed_output(store, record):
            status, evidence = "STIPULATED_IN_MODEL", []
        elif len({a.ref for a in matches}) == 1:
            status, evidence = matches[0].content["status"], [matches[0].ref.data()]
        else:
            status, evidence = "UNASSESSED", [a.ref.data() for a in matches]
        reviews.append({"premise": record.ref.data(), "status": status, "assessments": evidence})
        if status == "REFUTED":
            defects.append("PREMISE_REFUTED:" + record.ref.record_id)
        elif status == "CONFLICTED":
            pending.append("PREMISE_CONFLICTED:" + record.ref.record_id)
        elif status in ("UNASSESSED", "UNDETERMINED"):
            pending.append("PREMISE_" + status + ":" + record.ref.record_id)
        if record.domain != conclusion.domain:
            pending.append("DOMAIN_BRIDGE_MISSING:" + record.ref.record_id)
    if formal["formal_status"] == "INVALID":
        defects.append("LINK_INVALID")
    elif formal["formal_status"] == "UNPROVED":
        pending.append("LINK_UNPROVED")
    elif not formal["premises_satisfiable"]:
        pending.append("INCONSISTENT_PREMISES_CLASSICAL_VALIDITY_IS_VACUOUS")
    route = "BLOCK" if defects else "DEFER" if pending else "LICENSED"
    independent = by_claim.get(conclusion_ref, [])
    op_id = audit_id + ":audit"
    result = Record.make(audit_id, 1, "link_audit", conclusion.domain,
        {"audited_at": at, "formal_check": formal, "premise_reviews": reviews, "route_status": route,
         "defects": defects, "pending": pending,
         "symbol_bindings": symbol_bindings, "binding_conflicts": binding_conflicts,
         "premise_formulas": [r.content.get("formula") for r in premises],
         "conclusion_formula": conclusion.content.get("formula"), "conclusion": conclusion.ref.data(),
         "independent_conclusion_assessments": [{"ref": a.ref.data(), "status": a.content["status"]} for a in independent],
         "conclusion_truth_from_failed_route": "NOT_INFERRED",
         "scope": "bounded propositional validity and declared semantic bindings; no brain-matching claim"},
        "computed_link_audit", dependencies=refs, residuals=tuple(defects + pending), trace=(op_id,))
    store.log(Operation(op_id, "audit_bounded_propositional_link", conclusion.domain, refs, (result.ref,),
                        "LICENSED", "truth table separated from premise assessment and route admission"))
    store.add(result)
    return Outcome("LICENSED", result)
