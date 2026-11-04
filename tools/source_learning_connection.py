"""Connect installed reading, finite learning, inference and source revision.

No caller supplies labels, features, rule roles or a desired answer. The new
adapter owns only the handoffs and bounded source-support enumeration. Reading,
learning, substitution, inference and lifecycle decisions retain their owners.
"""
from __future__ import annotations

from dataclasses import asdict
from itertools import combinations, product
import json
import re

from nabt.errors import NabtError
from nabt.learning.finite_guard import FeatureSchema, GuardLanguage, LearningSession, Observation
from nabt.learning.source_evidence import identity_digest
from nabt.semantics import SemanticKernel, _instantiate
from nabt.text_ir import Atom, LANGUAGE_ID
from tools import evidence_lifecycle_v1 as life
from tools import explainable_pilot as pilot
from tools import verified_reading as ground

LAW_ID = "nabt.acquired-knowledge-connection.v1"
REQUEST_SCHEMA = "nabt.acquired-knowledge.request.v1"
RESULT_SCHEMA = "nabt.acquired-knowledge.result.v1"
MAX_SOURCES, MAX_FEATURES, MAX_SUPPORTS, MAX_GROUND_CLAUSES = 8, 6, 40, 256
CODE_PATHS = ("tools/source_learning_connection.py",
              "src/nabt/text_reader.py", "src/nabt/text_ir.py", "src/nabt/semantics.py",
              "src/nabt/errors.py", "src/nabt/learning/source_evidence.py",
              "src/nabt/learning/finite_guard.py", "tools/verified_reading.py",
              "tools/explainable_pilot.py", "tools/explainable_contracts.py", *life.CODE_PATHS)


class SourceReadError(ValueError):
    def __init__(self, report):
        super().__init__("Source has unresolved reading obligations")
        self.report = asdict(report)


class ConnectionMismatch(ValueError):
    pass


class ProjectionScopeError(ValueError):
    pass


def _kernel(rows, active, scope):
    kernel = SemanticKernel()
    for row in rows:
        if row["id"] in active:
            admitted = kernel.add_source(row["text"], source_id=row["id"], scope=scope)
            if not admitted.accepted:
                raise SourceReadError(admitted)
    return kernel


def _request(request):
    life._encoded(request, life.MAX_REQUEST_BYTES)
    life._fields(request, ("schema", "sources", "query", "scope", "initial_active", "events"), "request")
    if request["schema"] != REQUEST_SCHEMA:
        raise life.InputError("Unknown connection schema")
    life._text(request["scope"], "scope", 128)
    life._text(request["query"], "query", 8192, content=True)
    life._array(request["sources"], "sources", MAX_SOURCES)
    if not request["sources"]:
        raise life.InputError("At least one source is required")
    ids = set()
    for row in request["sources"]:
        life._fields(row, ("id", "text", "parents"), "source")
        if type(row["id"]) is not str or re.fullmatch(r"[a-z][a-z0-9_]{0,63}", row["id"]) is None:
            raise life.InputError("Invalid source ID")
        if row["id"] in ids:
            raise life.InputError("Duplicate source ID")
        ids.add(row["id"])
        life._text(row["text"], "source text", 8192, content=True)
        life._names(row["parents"], "parents")
    parents = {r["id"]: set(r["parents"]) for r in request["sources"]}
    if any(not p <= ids for p in parents.values()):
        raise life.InputError("Unknown parent source")
    ancestors, ranks = {}, {}
    while len(ancestors) < len(ids):
        ready = [n for n in sorted(ids - ancestors.keys()) if parents[n] <= ancestors.keys()]
        if not ready:
            raise life.InputError("Cyclic source ancestry")
        for name in ready:
            ancestors[name] = {name}.union(*(ancestors[p] for p in parents[name]))
            ranks[name] = 1 + max((ranks[p] for p in parents[name]), default=-1)
    life._names(request["initial_active"], "initial_active")
    if not set(request["initial_active"]) <= ids:
        raise life.InputError("Unknown initial source")
    life._array(request["events"], "events", 16)
    events = set()
    for event in request["events"]:
        life._fields(event, ("id", "kind", "target"), "event")
        life._text(event["id"], "event ID", 128)
        if event["id"] in events or event["kind"] not in ("withdraw", "activate"):
            raise life.InputError("Duplicate event or unsupported event kind")
        if type(event["target"]) is not str or event["target"] not in ids:
            raise life.InputError("Unknown event target")
        events.add(event["id"])
    kernel = _kernel(request["sources"], ids, request["scope"])
    program = kernel._program()
    if any(d.declarations or d.definitions or d.queries for d in program.documents):
        raise life.InputError("Connection accepts explicit facts and rules only")
    query = kernel.read_query(request["query"], scope=request["scope"]).atom
    return kernel, query, ancestors, ranks


def _learning(kernel, query, vocabulary):
    """Labels and features are separate explicit source facts, never closures."""
    if len(query.args) != 1 or not vocabulary:
        return {"status": "OUTSIDE_UNARY_LEARNING_SCOPE", "application_established": False}
    schema = FeatureSchema("source-asserted-unary-properties", LAW_ID, vocabulary)
    program = kernel._program()
    facts = {}
    for clause in program.facts:
        atom = clause.record.atom
        if len(atom.args) == 1:
            facts.setdefault((atom.args[0], atom.predicate), []).append(clause)

    def property_of(entity, predicate):
        rows = facts.get((entity, predicate), [])
        signs = {c.record.atom.positive for c in rows}
        return (next(iter(signs)) if len(signs) == 1 else None), [c.identity() for c in rows]

    def case_of(entity):
        values, witnesses = {}, {}
        for predicate in vocabulary:
            values[predicate], witnesses[predicate] = property_of(entity, predicate)
        return schema.case(entity, identity_digest(witnesses), values), witnesses

    observations, records = [], []
    for entity in sorted({e for e, p in facts if p == query.predicate} - {query.args[0]}):
        label, label_witnesses = property_of(entity, query.predicate)
        case, witnesses = case_of(entity)
        record = {"entity": entity, "case": asdict(case), "feature_witnesses": witnesses,
                  "label": label, "label_witnesses": label_witnesses,
                  "conflicting_label": len({r["atom"]["positive"] for r in label_witnesses}) > 1}
        observation = Observation(identity_digest(record), "acquired-source-statements", case, label)
        observations.append(observation)
        records.append({**record, "evidence_id": observation.evidence_id, "ready": observation.ready})
    session = LearningSession(GuardLanguage(schema, degree=schema.width), tuple(observations))
    case, witnesses = case_of(query.args[0])
    prediction = session.predict(case)
    candidates = []
    for guard in session.survivors:
        matches = []
        if not guard.bottom and guard.positive | guard.negative:
            expected = {(name, bool(guard.positive & (1 << i))) for i, name in enumerate(vocabulary)
                        if (guard.positive | guard.negative) & (1 << i)}
            for clause in program.rules:
                rule = clause.record
                if (rule.head.predicate != query.predicate or not rule.head.positive
                        or len(rule.head.args) != 1 or len(rule.head.variables) != 1):
                    continue
                variable = rule.head.args
                if (all(a.args == variable for a in rule.body)
                        and {(a.predicate, a.positive) for a in rule.body} == expected):
                    matches.append(clause.identity())
        candidates.append({"code": guard.code, "positive_mask": guard.positive,
                           "negative_mask": guard.negative, "bottom": guard.bottom,
                           "adoption": "SOURCE_RULE_MATCH" if matches else "CANDIDATE_ONLY",
                           "source_rules": matches})
    result = kernel.query(query, scope=program.documents[0].scope if program.documents else "default")
    used = {step["clause"]["clause_id"] for step in result.proofs.get("query", {}).get("steps", [])}
    applied = [c["code"] for c in candidates if any(r["clause_id"] in used for r in c["source_rules"])]
    return {"status": prediction.status.value, "schema": asdict(schema), "degree": schema.width,
            "revision": session.revision, "observations": records, "pending": list(session.pending),
            "survivor_count": len(session.survivors), "candidates": candidates,
            "prediction": asdict(prediction), "case_witnesses": witnesses,
            "applied_candidate_codes": applied,
            "application_established": bool(applied) and prediction.possible == (True,)
                and query.positive and result.status == "SUPPORTED",
            "authority": "SOURCE_RELATIVE_ONLY", "sample_generalization_authorized": False}


def _supports(request, query, ancestors):
    """Exhaust source subsets using the installed kernel, not another closure.

    The result is all inclusion-minimal *source sets*, not all derivation trees.
    Both signs are monotone; clean inference is recomputed separately because
    a conflicting premise can be removed by a later withdrawal.
    """
    ids = sorted(ancestors)
    found, tested = {True: [], False: []}, 0
    for count in range(1, len(ids) + 1):
        for chosen in combinations(ids, count):
            active = set(chosen)
            if any(not ancestors[n] <= active for n in active):
                continue
            needed = [sign for sign in (True, False) if not any(set(r["sources"]) <= active for r in found[sign])]
            if not needed:
                continue
            kernel = _kernel(request["sources"], active, request["scope"])
            answer = kernel.query(query, scope=request["scope"])
            tested += 1
            if answer.reason == "RESOURCE_LIMIT":
                raise life.ResourceLimit("Source support search exhausted the semantic budget")
            for sign, supported, name in ((True, answer.positive_support, "query"),
                                          (False, answer.negative_support, "opposite")):
                if sign in needed and supported:
                    certificate = answer.proofs[name]
                    if not kernel.verify_certificate(certificate)["accepted"]:
                        raise ConnectionMismatch("Source support certificate failed replay")
                    found[sign].append({"id": "support_" + str(sum(map(len, found.values()))),
                                        "positive": sign, "sources": list(chosen), "certificate": certificate})
                    if sum(map(len, found.values())) > MAX_SUPPORTS:
                        raise life.ResourceLimit("Minimal source support limit")
    return [*found[True], *found[False]], tested


def _episode(request, query, supports, ancestors, ranks):
    sources, origins, bindings, interpretations = {}, [], [], []

    def add(name, content, parents, rank):
        source = {"identity": name, "revision": identity_digest(content), "content": content}
        sources[name] = source
        origins.append({"id": name, "parents": parents})
        bindings.append({"origin_id": name, "source": source, "rank": rank})

    add("connection_question", request["query"], [], 0)
    for row in request["sources"]:
        add("input_" + row["id"], row["text"], ["input_" + p for p in row["parents"]], ranks[row["id"]])
    key = {"axis": "recorded_observation", "entity": life.wire(list(query.args)),
           "predicate": query.predicate, "value": life.wire(query.as_dict()),
           "unit": "source_relative_signed_consequence", "context": request["scope"],
           "time": "0", "place": "symbolic"}
    for path in supports:
        name = "derived_" + path["id"]
        parents = ["input_" + n for n in path["sources"]]
        add(name, identity_digest(path["certificate"]), parents,
            1 + max(ranks[n] for n in path["sources"]))
        interpretations.append({"id": path["id"], "source": sources[name], "key": key,
            "positive": path["positive"], "kind": "observation", "origin": name,
            "ancestry": [*parents, name]})
    active = [s for name, s in sources.items() if not name.startswith("input_")
              or name[6:] in request["initial_active"]]
    return {"schema": life.EPISODE_SCHEMA, "episode_id": "acquired-knowledge-v1",
            "query": {"key": key, "positive": True, "origin": "connection_question"},
            "active_sources": active, "origins": origins, "bindings": bindings,
            "interpretations": interpretations, "budget": MAX_SUPPORTS,
            "updates": [{"event_id": e["id"], "kind": e["kind"], "source": sources["input_" + e["target"]],
                         "replacement": None, "reason": "Explicit source lifecycle event"} for e in request["events"]]}


def _native_ground(kernel, query, scope):
    """Retain every bounded grounding, its source clause and substitution.

    Lean checks this exact ground projection. Python owns the source-to-ground
    bridge; no general refinement theorem is claimed for this adapter.
    """
    program = kernel._program()
    constants = sorted(set(program.constants.get(scope, ())) | set(query.args))
    rows, provenance = [], []
    for clause in (*program.facts, *program.rules):
        if hasattr(clause.record, "atom"):
            choices = [({}, {"kind": "fact", "atom": ground.literal(clause.record.atom)})]
        else:
            rule = clause.record
            variables = sorted(set().union(*(a.variables for a in rule.body)))
            if len(constants) ** len(variables) + len(rows) > MAX_GROUND_CLAUSES:
                raise life.ResourceLimit("Ground projection limit")
            choices = []
            for terms in product(constants, repeat=len(variables)):
                binding = dict(zip(variables, terms))
                choices.append((binding, {"kind": "rule", "body": [ground.literal(_instantiate(a, binding)) for a in rule.body],
                                           "head": ground.literal(_instantiate(rule.head, binding))}))
        for binding, row in choices:
            if len(rows) >= MAX_GROUND_CLAUSES:
                raise life.ResourceLimit("Ground projection limit")
            rows.append(row)
            provenance.append({"ground_index": len(rows) - 1, "clause": clause.identity(), "binding": binding})
    if not rows:
        return {"native_checked": False, "status": "EMPTY_THEORY", "grounding": []}
    try:
        raw = "".join(ground.render_clause(row) for row in rows).encode()
        question = ("هل " + ground.render_atom(ground.literal(query)) + "؟\n").encode()
    except ValueError as error:
        raise ProjectionScopeError("Parsed names are outside the installed native ground alphabet") from error
    answer = pilot.answer(raw, question, identity="connection", revision=program.sha256, scope=scope)
    return {"native_checked": True, "status": answer["answer"]["status"],
            "grounding": provenance, "answer": answer}


def evaluate(request):
    result = {"schema": RESULT_SCHEMA, "law_id": LAW_ID, "status": "INVALID_INPUT", "chain_complete": False,
              "request": None, "acquisition": [], "minimal_source_supports": [], "history": [],
              "lifecycle": None, "limits": {"language": LANGUAGE_ID, "max_sources": MAX_SOURCES,
                  "max_features": MAX_FEATURES, "max_supports": MAX_SUPPORTS,
                  "max_ground_clauses": MAX_GROUND_CLAUSES, "support_granularity": "WHOLE_SOURCE",
                  "all_proof_trees_enumerated": False, "general_refinement_proved": False,
                  "world_truth_established": False, "free_arabic_acquisition_established": False}}
    try:
        kernel, query, ancestors, ranks = _request(request)
        result["request"] = life.strict_loads(life.wire(request))
        result["run_identity"] = life.run_identity(CODE_PATHS,
            [pilot.checker_path(), life.NATIVE])
        program = kernel._program()
        result["acquisition"] = [d.as_dict() for d in program.documents]
        vocabulary = tuple(sorted({a.predicate for c in (*program.facts, *program.rules)
            for a in ((c.record.atom,) if hasattr(c.record, "atom") else (*c.record.body, c.record.head))
            if len(a.args) == 1 and a.predicate != query.predicate}))
        if len(vocabulary) > MAX_FEATURES:
            raise life.ResourceLimit("Acquired feature vocabulary limit")
        supports, tested = _supports(request, query, ancestors)
        result.update(minimal_source_supports=supports, source_subsets_tested=tested,
                      source_support_enumeration_complete=True)
        lifecycle = life.evaluate_episode(_episode(request, query, supports, ancestors, ranks))
        result["lifecycle"] = lifecycle
        if not lifecycle["native_checked"] or not lifecycle["decision_complete"]:
            result["status"] = lifecycle["status"]
            return result
        active = set(request["initial_active"])
        for index in range(len(request["events"]) + 1):
            if index:
                event = request["events"][index - 1]
                (active.discard if event["kind"] == "withdraw" else active.add)(event["target"])
            ready = {n for n in active if ancestors[n] <= active}
            current = _kernel(request["sources"], ready, request["scope"])
            answer = current.query(query, scope=request["scope"])
            if answer.reason == "RESOURCE_LIMIT":
                raise life.ResourceLimit("Current inference budget")
            checked = {name: current.verify_certificate(cert) for name, cert in answer.proofs.items()}
            if any(not row["accepted"] for row in checked.values()):
                raise ConnectionMismatch("Current certificate did not replay")
            native = _native_ground(current, query, request["scope"])
            status = "UNKNOWN" if answer.status == "OUT_OF_SCOPE" else answer.status
            if native["native_checked"] and native["status"] != status:
                raise ConnectionMismatch("Native and source inference disagree")
            step = lifecycle["execution"]["native_result"]["steps"][index]
            support_ids, refutation_ids = step["receipt"]["support_ids"], step["receipt"]["refutation_ids"]
            if bool(support_ids) != answer.positive_support or bool(refutation_ids) != answer.negative_support:
                raise ConnectionMismatch("Lifecycle and source support disagree")
            result["history"].append({"step": index, "event_id": step["event_id"],
                "active_sources": sorted(active), "ready_sources": sorted(ready), "status": status,
                "learning": _learning(current, query, vocabulary), "inference": answer.as_dict(),
                "certificate_checks": checked, "ground_inference": native,
                "support_ids": support_ids, "refutation_ids": refutation_ids,
                "signed_support_status": step["receipt"]["status"]})
        if result["run_identity"] != life.run_identity(CODE_PATHS, [pilot.checker_path(), life.NATIVE]):
            raise ConnectionMismatch("Code or native identity changed during replay")
        result.update(status=result["history"][-1]["status"], chain_complete=all(
            h["ground_inference"]["native_checked"] for h in result["history"]))
        result = json.loads(json.dumps(result, ensure_ascii=False, allow_nan=False))
        life._encoded(result, life.MAX_REPORT_BYTES)
    except SourceReadError as error:
        result.update(status="DEFER", chain_complete=False, error=str(error), source_failure=error.report)
    except ProjectionScopeError as error:
        result.update(status="DEFER", chain_complete=False, error=str(error))
    except ConnectionMismatch as error:
        result.update(status="VERIFICATION_FAILED", chain_complete=False, error=str(error))
    except (life.ResourceLimit, OverflowError) as error:
        result.update(status="RESOURCE_LIMIT", chain_complete=False, error=str(error))
    except NabtError as error:
        result.update(status="RESOURCE_LIMIT" if error.code == "RESOURCE_LIMIT" else "INVALID_INPUT",
                      chain_complete=False, error=error.code)
    except pilot.PilotError as error:
        status = "RESOURCE_LIMIT" if error.code == "RESOURCE_LIMIT" else "VERIFICATION_UNAVAILABLE"
        result.update(status=status, chain_complete=False, error=str(error))
    except OSError as error:
        result.update(status="VERIFICATION_UNAVAILABLE", chain_complete=False, error=str(error))
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError) as error:
        result.update(status="INVALID_INPUT", chain_complete=False, error=str(error))
    try:
        result = json.loads(json.dumps(result, ensure_ascii=False, allow_nan=False))
        life._encoded(result, life.MAX_REPORT_BYTES)
    except life.ResourceLimit:
        return {"schema": RESULT_SCHEMA, "status": "RESOURCE_LIMIT", "chain_complete": False,
                "error": "Whole connection report exceeds byte limit"}
    return result


def verify(report, *, expected_request):
    """The receipt never supplies its own replay inputs."""
    try:
        encoded = life._encoded(report, life.MAX_REPORT_BYTES)
        expected = evaluate(expected_request)
        matches = encoded == life._encoded(expected, life.MAX_REPORT_BYTES)
        return {"valid": matches and expected["chain_complete"], "replay_matches": matches,
                "status": expected["status"] if matches else "INVALID_RECEIPT"}
    except (ValueError, TypeError, RecursionError):
        return {"valid": False, "replay_matches": False, "status": "INVALID_RECEIPT"}


def main():
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--verify", type=Path, help="receipt, replayed against the independent request")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        with args.request.open("rb") as stream:
            request = life.strict_loads(stream.read(life.MAX_REQUEST_BYTES + 1))
        if args.verify:
            with args.verify.open("rb") as stream:
                receipt = life.strict_loads(stream.read(life.MAX_REPORT_BYTES + 1),
                                           maximum_bytes=life.MAX_REPORT_BYTES, report=True)
            report = verify(receipt, expected_request=request)
        else:
            report = evaluate(request)
    except life.ResourceLimit as error:
        report = {"status": "RESOURCE_LIMIT", "chain_complete": False, "error": str(error)}
    except (ValueError, OSError) as error:
        report = {"status": "INVALID_INPUT", "chain_complete": False, "error": str(error)}
    encoded = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded if not args.output else json.dumps({"status": report["status"],
        "chain_complete": report.get("chain_complete", report.get("valid", False)),
        "report": str(args.output)}, ensure_ascii=False))
    return 0 if report.get("chain_complete", report.get("valid", False)) else 3


if __name__ == "__main__":
    raise SystemExit(main())
