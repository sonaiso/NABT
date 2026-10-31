"""Explain an already accepted canonical ground-reading certificate.

This is a display adapter for ``tools.explainable_pilot``. Its caller must first
run the configured native ``verifiedReading`` checker on independent source and
query bytes, then construct the existing exact source spans and proof DAGs.
Calling this module directly does not verify a proposal or grant authority.

The adapter indexes the accepted clauses, complete closures and stored replay
steps. It never parses text, derives another closure, chooses a verdict, checks
an external case, or creates evidence for a premise. Backward traversal is a
finite source-dependency display: alternative rules remain alternatives, and
each rule retains its entire ordered conjunction of premises. Dependencies are
those of each retained replay root, without a claim to enumerate every proof.

The independent authored contract matrix was frozen before this implementation
with SHA-256 e5bdc1e1707ca5f610f56ac2e4e3f6af6c2f54f4e7f02842c1b6161d606f0b6a.
That finite regression scope does not prove this Python renderer or establish
general Arabic interpretation, source authenticity, premise truth, or physical
case applicability. No source-book contract is inferred from a rule's spelling.
"""

from __future__ import annotations

from copy import deepcopy

from tools import verified_reading as ground


SCHEMA = "nabt.explanation-contract.v1"


def _atom(value, *, positive=None):
    """Copy an accepted literal without retaining mutable certificate aliases."""
    return {"predicate": value["predicate"], "arguments": list(value["arguments"]),
            "positive": value["positive"] if positive is None else positive}


def _clause_atoms(clause):
    return ([clause["atom"]] if clause["kind"] == "fact"
            else [clause["head"], *clause["body"]])


def _first_witnesses(trace):
    # Repeated accepted steps are legal. An earlier witness avoids presenting a
    # later re-derivation as the prerequisite of its own earlier application.
    witnesses = {}
    for node in trace:
        witnesses.setdefault(ground.key(node["atom"]), node["id"])
    return witnesses


def _relevant_clauses(target, clauses):
    """Follow exact source heads backward; do not evaluate or repair the theory."""
    producers = {}
    for index, clause in enumerate(clauses):
        head = clause["atom"] if clause["kind"] == "fact" else clause["head"]
        producers.setdefault(ground.key(head), []).append(index)
    pending, visited, relevant = [ground.key(target)], set(), set()
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        for index in producers.get(current, []):
            relevant.add(index)
            clause = clauses[index]
            if clause["kind"] == "rule":
                pending.extend(ground.key(atom) for atom in clause["body"])
    return ([f"c{index}" for index in sorted(relevant)],
            [f"c{index}" for index in producers.get(ground.key(target), [])])


def _dependency(trace, root, clauses):
    """Keep exactly the stored DAG ancestors of one retained native proof root."""
    if root is None:
        return None
    by_id = {node["id"]: node for node in trace}
    pending, selected = [root], set()
    while pending:
        current = pending.pop()
        if current in selected:
            continue
        selected.add(current)
        pending.extend(by_id[current]["premises"])
    nodes = [node for node in trace if node["id"] in selected]
    clause_ids = list(dict.fromkeys(node["clause_id"] for node in nodes))
    kinds = {f"c{index}": clause["kind"] for index, clause in enumerate(clauses)}
    return {"root": root, "step_ids": [node["id"] for node in nodes],
            "clause_ids": clause_ids,
            "fact_clause_ids": [cid for cid in clause_ids if kinds[cid] == "fact"],
            "rule_clause_ids": [cid for cid in clause_ids if kinds[cid] == "rule"]}


def _target(atom, name, clauses, operations, roots):
    relevant, producers = _relevant_clauses(atom, clauses)
    by_id = {operation["clause_id"]: operation for operation in operations}
    full_root, clean_root = roots["full"][name], roots["clean"][name]
    residuals = []
    if full_root is None:
        residuals.append({"code": "TARGET_NOT_DERIVED_IN_FULL_CLOSURE"})
    if clean_root is None:
        residuals.append({"code": "TARGET_NOT_DERIVED_IN_CLEAN_CLOSURE"})
    if not producers:
        residuals.append({"code": "NO_SOURCE_PRODUCER"})
    for clause_id in relevant:
        operation = by_id[clause_id]
        if operation["missing_full_premises"] or operation["missing_clean_premises"]:
            residuals.append({
                "code": "MISSING_RULE_PREMISES", "clause_id": clause_id,
                "missing_full_premises": deepcopy(operation["missing_full_premises"]),
                "missing_clean_premises": deepcopy(operation["missing_clean_premises"]),
                "candidate_route_only": True,
            })
        if not operation["clean_retained"]:
            residuals.append({
                "code": "CONFLICT_EXCLUDES_SOURCE_CLAUSE", "clause_id": clause_id,
                "blocked_atoms": deepcopy(operation["blocked_atoms"]),
                "candidate_route_only": True,
            })
    return {"atom": _atom(atom), "full_root": full_root, "clean_root": clean_root,
            "producer_clause_ids": producers, "relevant_clause_ids": relevant,
            "rule_alternatives": "OR", "premises_within_rule": "AND",
            "residuals": residuals}


def explanation(certificate, evidence, receipt, binding):
    """Render only after native acceptance; this function is not an acceptor.

    ``evidence`` is the existing pilot analysis of this accepted certificate.
    Missing prerequisites are closure-membership observations, not assertions
    that they are false or that adding them suffices to obtain a new verdict.
    """
    clauses, traces, roots = certificate["clauses"], evidence["traces"], evidence["roots"]
    full = {ground.key(atom) for atom in certificate["known"]}
    clean = {ground.key(atom) for atom in certificate["clean_known"]}
    blocked = {key for key in full if ground.opposite(key) in full}
    full_witnesses = _first_witnesses(traces["full"])
    clean_witnesses = _first_witnesses(traces["clean"])
    steps_by_clause = {name: {} for name in ("full", "clean")}
    for name in steps_by_clause:
        for node in traces[name]:
            steps_by_clause[name].setdefault(node["clause_id"], []).append(node["id"])
    spans = {span["id"]: span for span in evidence["source_clauses"]}

    operations = []
    for index, clause in enumerate(clauses):
        clause_id, kind = f"c{index}", clause["kind"]
        premises = [] if kind == "fact" else clause["body"]
        clause_blocked, blocked_families = [], set()
        for atom in _clause_atoms(clause):
            key = ground.key(atom)
            family = (key[0], key[1])
            if key in blocked and family not in blocked_families:
                blocked_families.add(family)
                clause_blocked.extend((_atom(atom, positive=True), _atom(atom, positive=False)))
        span = spans[clause_id]
        operation = {
            "clause_id": clause_id, "kind": kind,
            "source_anchor": {field: span[field] for field in ("byte_start", "byte_end", "text")},
            "contract": {
                "operation": "SOURCE_FACT_ADMISSION" if kind == "fact" else "SIGNED_GROUND_RULE_APPLICATION",
                "law_id": receipt["law_id"],
                "premise_combination": None if kind == "fact" else "AND",
                "authority": "SOURCE_RELATIVE_ONLY",
            },
            "required_premises": [
                {"atom": _atom(atom), "full_witness": full_witnesses.get(ground.key(atom)),
                 "clean_witness": clean_witnesses.get(ground.key(atom)),
                 "opposite_full_witness": full_witnesses.get(ground.opposite(ground.key(atom)))}
                for atom in premises
            ],
            "missing_full_premises": [_atom(atom) for atom in premises if ground.key(atom) not in full],
            "missing_clean_premises": [_atom(atom) for atom in premises if ground.key(atom) not in clean],
            "blocked_atoms": clause_blocked,
            "clean_retained": not clause_blocked,
            "full_steps": list(steps_by_clause["full"].get(clause_id, [])),
            "clean_steps": list(steps_by_clause["clean"].get(clause_id, [])),
        }
        operation["atom" if kind == "fact" else "head"] = _atom(
            clause["atom"] if kind == "fact" else clause["head"])
        operations.append(operation)

    conflicts, conflict_families = [], set()
    for atom in certificate["known"]:
        key = ground.key(atom)
        family = (key[0], key[1])
        if key not in blocked or family in conflict_families:
            continue
        conflict_families.add(family)
        positive, negative = _atom(atom, positive=True), _atom(atom, positive=False)
        conflicts.append({
            "positive_atom": positive, "negative_atom": negative,
            "positive_full_witness": full_witnesses[ground.key(positive)],
            "negative_full_witness": full_witnesses[ground.key(negative)],
            "affected_clause_ids": [operation["clause_id"] for operation in operations
                                    if any(ground.key(a)[:2] == family for a in operation["blocked_atoms"])],
        })

    query = certificate["query"]
    opposite_query = _atom(query, positive=not query["positive"])
    targets = {name: _target(atom, name, clauses, operations, roots)
               for name, atom in (("query", query), ("opposite_query", opposite_query))}
    dependencies = {name: {target: _dependency(traces[name], roots[name][target], clauses)
                           for target in ("query", "opposite_query")}
                    for name in ("full", "clean")}

    return {
        "schema": SCHEMA, "law_id": receipt["law_id"],
        "basis": {"kind": "NATIVE_ACCEPTED_READING_AND_COMPLETE_CLOSURES",
                  "binding": deepcopy(binding), "span_unit": evidence["span_unit"]},
        "axes": {
            "reading_fidelity": {
                "status": "VERIFIED_CANONICAL_GROUND_READING",
                "authority": "EXACT_SOURCE_AND_QUERY_BYTES_UNDER_INSTALLED_READER",
                "source_clause_ids": [operation["clause_id"] for operation in operations],
                "source_authenticity": "NOT_ESTABLISHED",
                "author_intention": "NOT_ESTABLISHED",
            },
            "premise_support": {
                "status": "SOURCE_RELATIVE_ONLY",
                "authority": "SOURCE_FACTS_AND_CHECKED_SIGNED_DERIVATIONS",
                "external_truth": "NOT_ESTABLISHED",
                "external_rule_validity": "NOT_ESTABLISHED",
                "support_dependencies": "dependencies contains the exact retained proof ancestors",
            },
            "inference_validity": {
                "status": "VERIFIED_SOURCE_RELATIVE_CLOSURES",
                "status_from_native": receipt["status"],
                **{name: receipt[name] for name in
                   ("positive", "negative", "clean_positive", "clean_negative")},
            },
            "case_applicability": {
                "status": "SCOPED_GROUND_MATCHING_ONLY",
                "source_scope": binding["scope"],
                "matching": "EXACT_PREDICATE_ORDERED_ARGUMENTS_POLARITY_AND_BOUND_SCOPE",
                "external_referent_time_unit": "NOT_ESTABLISHED",
                "external_case_applicability": "NOT_ESTABLISHED",
                "action_authority": "NONE",
            },
        },
        "operations": operations, "conflicts": conflicts, "targets": targets,
        "dependencies": dependencies,
        "judgment_change": {
            "bound_inputs_requiring_replay": ["source_bytes", "query_bytes", "source_id",
                                             "revision", "scope", "native_checker"],
            "source_changes_requiring_replay": ["add_or_withdraw_a_source_fact",
                                                "add_remove_or_change_a_source_rule",
                                                "add_or_withdraw_counterevidence"],
            "procedure": "Rebuild and natively check both complete closures against the independent changed inputs",
            "route_obligations": "targets residuals and operations missing premises describe individual source routes",
            "missing_premises_are_not_false": True,
            "outcome_guaranteed": False,
            "external_case_action_requires_separate_evidence": True,
        },
        "limits": {
            "language": "canonical_ground_source_entailment",
            "all_arabic_complete": False, "world_truth_established": False,
            "renderer_formally_proved": False, "model_internal_causality_proved": False,
            "proof_minimality_proved": False, "all_derivations_enumerated": False,
            "minimal_or_necessary_repair_claimed": False,
            "candidate_route_residuals_can_coexist_with_a_supported_alternative": True,
            "operation_steps_refer_only_to_the_stored_replay": True,
            "premise_witness_policy": "FIRST_STORED_REPLAY_WITNESS",
            "source_book_rule_contracts_inferred": False,
        },
    }
