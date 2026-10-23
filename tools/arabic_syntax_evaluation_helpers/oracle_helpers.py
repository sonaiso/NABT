"""Independent source-bound replay; imports no NABT implementation."""
from __future__ import annotations

from hashlib import sha256
from itertools import product
import json
import re
import unicodedata

from .statement_oracle import load_statement_oracle


class ReplayValidationError(AssertionError):
    """A returned answer/certificate failed the independent replay contract."""


def require(condition, message):
    if not condition:
        raise ReplayValidationError(message)


def closed(value, fields, label):
    require(type(value) is dict and set(value) == set(fields), label + " has an invalid closed schema")


def name(value, label):
    require(type(value) is str and bool(value.strip()) and len(value) <= 512, label + " must be a nonempty bounded exact string")
    require(not any(unicodedata.category(c).startswith("C") for c in value), label + " contains a control character")


def digest(value, label):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None, label + " must be a canonical SHA-256")


def atom_key(atom, *, variable_names=False):
    closed(atom, {"predicate", "args", "positive"}, "atom")
    name(atom["predicate"], "predicate")
    require(not atom["predicate"].startswith("?"), "A predicate cannot be a variable")
    require(type(atom["positive"]) is bool, "Atom polarity must be boolean")
    require(type(atom["args"]) is list and len(atom["args"]) in (1, 2), "Installed atoms require one or two arguments")
    for term in atom["args"]:
        name(term, "term")
        require(term != "?" and (not term.startswith("?") or not any(c.isspace() for c in term)), "A variable needs one nonempty token")
    args = tuple("?x" if variable_names and x.startswith("?") else x for x in atom["args"])
    return atom["predicate"], args, atom["positive"]


def variables(atom):
    atom_key(atom)
    return {x for x in atom["args"] if x.startswith("?")}


def _rule_parts(rule):
    closed(rule, {"body", "head"}, "rule")
    require(type(rule["body"]) is list and 1 <= len(rule["body"]) <= 16, "Rule body must contain one to sixteen atoms")
    body_variables = set().union(*(variables(a) for a in rule["body"]))
    require(variables(rule["head"]) <= body_variables, "Rule head has an unbound variable")
    return body_variables


def rule_key(rule):
    all_variables = _rule_parts(rule)
    # Original manual gold has at most one variable. Preserve a distinct marker
    # for multi-variable projections rather than collapsing their identities.
    if len(all_variables) > 1:
        return ("multi_variable_not_in_gold", str(rule))
    return tuple(sorted(atom_key(a, variable_names=True) for a in rule["body"])), atom_key(rule["head"], variable_names=True)


def ordered_rule_key(rule):
    _rule_parts(rule)
    renaming = {}
    def key(atom):
        pred, args, positive = atom_key(atom)
        renamed = tuple(renaming.setdefault(x, "?" + str(len(renaming))) if x.startswith("?") else x for x in args)
        return pred, renamed, positive
    return tuple(key(a) for a in rule["body"]), key(rule["head"])


def check_span(span, raw, source_id):
    closed(span, {"source_id", "source_sha256", "start", "end", "span_sha256"}, "source span")
    require(span["source_id"] == source_id, "Span refers to another source")
    require(span["source_sha256"] == sha256(raw).hexdigest(), "Span source bytes differ")
    start, end = span["start"], span["end"]
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(raw), "Invalid span bounds")
    try:
        part = raw[start:end]
        part.decode("utf-8")
    except UnicodeError as error:
        raise ReplayValidationError("Span splits a UTF-8 code point") from error
    require(span["span_sha256"] == sha256(part).hexdigest(), "Span bytes differ")
    return part


def restore_segments(parsed, raw, source_id):
    offset = 0
    restored = b""
    for segment in parsed["segments"]:
        require(segment["span"]["start"] == offset, "Source segments are not contiguous")
        restored += check_span(segment["span"], raw, source_id)
        offset = segment["span"]["end"]
    require(restored == raw, "Source restoration differs")
    return True


def substitute(atom, binding):
    atom_key(atom)
    require(type(binding) is dict, "Rule binding must be an object")
    for key, value in binding.items():
        name(key, "Binding key")
        name(value, "Binding value")
        require(key.startswith("?") and key != "?", "Only variables can be bound")
        require(not any(c.isspace() for c in key), "A binding variable must be one token")
        require(not value.startswith("?"), "Binding value must be ground")
    result = {"predicate": atom["predicate"], "positive": atom["positive"],
              "args": [binding[x] if x.startswith("?") and x in binding else x for x in atom["args"]]}
    require(not variables(result), "Rule substitution is incomplete")
    return result


def opposite(atom):
    atom_key(atom)
    return {**atom, "positive": not atom["positive"]}


def content_digest(value):
    """The public canonical JSON identity contract, independent of NABT code."""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return sha256(raw).hexdigest()


def program_identity(active_sources, scope, language_id):
    """Bind a result to the expected raw active inventory, not result metadata."""
    return content_digest({"version": "nabt.signed-horn.v1", "language": language_id,
                           "sources": [[sid, sha256(raw.encode()).hexdigest(), scope]
                                       for sid, raw in sorted(active_sources.items())]})


def _source_gold(active_sources, manual_oracle):
    require(type(active_sources) is dict and type(manual_oracle) is dict, "Expected active source and manual-oracle mappings")
    records = []
    for source_id, text in active_sources.items():
        name(source_id, "Active source ID")
        require(type(text) is str, "Active source bytes must be represented by text")
        checksum = sha256(text.encode()).hexdigest()
        require(checksum in manual_oracle, "Active source has no independent semantic oracle")
        records.append(manual_oracle[checksum])
    return records


def independent_closures(active_sources, manual_oracle):
    """Finite signed/clean closures from trusted gold, including unquoted sources.

    Exhaustively instantiate finite safe Horn rules, then compute two fixed
    points. This intentionally differs from the runtime's joins/proof search.
    The 100,000-instance bound fails the check; it never proves absence.
    """
    facts, rules = [], []
    for record in _source_gold(active_sources, manual_oracle):
        facts.extend(record["facts"])
        rules.extend(record["rules"])
    for fact in facts:
        require(not variables(fact), "Manual fact must be ground")
    all_atoms = facts + [a for r in rules for a in [*r["body"], r["head"]]]
    constants = sorted({x for a in all_atoms for x in atom_key(a)[1] if not x.startswith("?")})
    grounded = []
    for rule in rules:
        keys = sorted(_rule_parts(rule))
        require(len(grounded) + len(constants) ** len(keys) <= 100_000, "Independent closure instance budget exhausted")
        for values in product(constants, repeat=len(keys)):
            binding = dict(zip(keys, values))
            grounded.append((frozenset(atom_key(substitute(a, binding)) for a in rule["body"]), atom_key(substitute(rule["head"], binding))))
    def closure(blocked):
        known = {atom_key(a) for a in facts if atom_key(a)[:2] not in blocked}
        while True:
            extra = {head for body, head in grounded if body <= known and head[:2] not in blocked}
            if extra <= known:
                return known
            known |= extra
    signed = closure(set())
    conflicts = {a[:2] for a in signed if (a[0], a[1], not a[2]) in signed}
    return signed, closure(conflicts), conflicts


def _statement_for_clause(clause, raw, source_id, gold, statement_oracle):
    checksum = sha256(raw).hexdigest()
    require(checksum in statement_oracle, "Source has no independent statement-role annotation")
    annotation = statement_oracle[checksum]
    require(annotation["source_text_sha256"] == checksum and annotation["raw_text"].encode() == raw, "Statement annotation belongs to another source")
    check_span(clause["span"], raw, source_id)
    matches = [s for s in annotation["statements"] if (s["start"], s["end"]) == (clause["span"]["start"], clause["span"]["end"])]
    require(len(matches) == 1, "Clause must cite its complete independently annotated statement")
    statement = matches[0]
    require(type(clause["component_spans"]) is list, "Clause components must be a list")
    require(len(clause["component_spans"]) == len(statement["components"]) > 0, "Complete ordered statement components are required")
    for actual, component in zip(clause["component_spans"], statement["components"]):
        check_span(actual, raw, source_id)
        require(component["roles"] and (actual["start"], actual["end"]) == (component["start"], component["end"]), "Component does not match its independently annotated role")
    if clause["kind"] == "fact":
        require(atom_key(clause["atom"]) in {atom_key(a) for a in statement["facts"]}, "Fact is not licensed by this statement")
        require(atom_key(clause["atom"]) in {atom_key(a) for a in gold["facts"]}, "Fact is absent from the manual gold")
    else:
        rule = {"body": clause["body"], "head": clause["head"]}
        key = ordered_rule_key(rule)
        require(key in {ordered_rule_key(r) for r in statement["rules"]}, "Rule is not licensed by this statement and its component roles")
        require(len(statement["rule_kinds"]) == len(statement["rules"]), "Statement rule kinds are incomplete")
        require(any(key == ordered_rule_key(r) and clause["rule_kind"] == kind
                    for r, kind in zip(statement["rules"], statement["rule_kinds"])), "Rule kind differs from its annotated statement")
        require(key in {ordered_rule_key(r) for r in gold["rules"]}, "Rule is absent from the manual gold")


def independent_certificate(certificate, active_sources, scope, manual_oracle, *,
                            expected_query=None, expected_program_sha256=None,
                            expected_proof_kind=None, statement_oracle=None):
    """Validate a complete source-relative proof without a production checker.

    Optional expected values preserve the old helper API. The live evaluator
    always supplies the frozen target, current program, and required proof kind.
    A caller-provided fixture oracle is trusted test input, never certificate data.
    Analysis identifiers are opaque parser metadata: their clause-hash binding
    is checked, but the reader's version-dependent ID-generation is not rerun.
    Source statement meaning and component roles are checked independently.
    """
    closed(certificate, {"version", "scope", "query", "proof_kind", "program_sha256", "steps", "conclusion", "world_truth"}, "certificate")
    require(certificate["version"] == "nabt.semantic-certificate.v1", "Unknown certificate version")
    name(scope, "Expected scope")
    require(certificate["scope"] == scope, "Certificate is outside the query scope")
    require(certificate["world_truth"] == "NOT_ESTABLISHED", "Source evidence cannot establish external truth")
    require(certificate["proof_kind"] in ("clean", "signed"), "Unknown proof kind")
    if expected_proof_kind is not None:
        require(certificate["proof_kind"] == expected_proof_kind, "Wrong proof kind for returned status")
    digest(certificate["program_sha256"], "Certificate program")
    if expected_program_sha256 is not None:
        require(certificate["program_sha256"] == expected_program_sha256, "Certificate belongs to another program")
    require(not variables(certificate["query"]), "Certificate target must be ground")
    if expected_query is not None:
        require(atom_key(certificate["query"]) == atom_key(expected_query), "Certificate proves a different query or polarity")
    _source_gold(active_sources, manual_oracle)
    annotations = load_statement_oracle() if statement_oracle is None else statement_oracle
    require(type(annotations) is dict, "Statement oracle must be a trusted mapping")
    steps = certificate["steps"]
    require(type(steps) is list and bool(steps), "Certificate requires a nonempty step list")
    require(type(certificate["conclusion"]) is int, "Conclusion must be an integer index")
    derived = []
    common = {"clause_id", "scope", "source_id", "source_sha256", "span", "component_spans", "analysis_id", "kind"}
    for step in steps:
        closed(step, {"atom", "clause", "binding", "premises"}, "proof step")
        clause = step["clause"]
        require(type(clause) is dict and clause.get("kind") in ("fact", "rule"), "Unknown source clause kind")
        closed(clause, common | ({"atom"} if clause["kind"] == "fact" else {"body", "head", "rule_kind"}), "source clause")
        source_id = clause["source_id"]
        name(source_id, "Clause source ID")
        require(source_id in active_sources, "Clause source is absent or retracted")
        raw = active_sources[source_id].encode()
        checksum = sha256(raw).hexdigest()
        gold = manual_oracle[checksum]
        require(clause["scope"] == scope and clause["source_sha256"] == checksum, "Clause is outside the active source scope")
        digest(clause["clause_id"], "Clause ID")
        digest(clause["analysis_id"], "Analysis ID")
        _statement_for_clause(clause, raw, source_id, gold, annotations)
        payload = ({"atom": clause["atom"]} if clause["kind"] == "fact" else
                   {"body": clause["body"], "head": clause["head"], "kind": clause["rule_kind"]})
        payload.update({key: clause[key] for key in ("scope", "source_id", "source_sha256", "span", "analysis_id")})
        payload["semantic_version"] = "nabt.signed-horn.v1"
        require(clause["clause_id"] == content_digest(payload), "Clause ID does not bind its validated source payload")
        require(type(step["binding"]) is dict and type(step["premises"]) is list, "Binding and premise types are invalid")
        if clause["kind"] == "fact":
            require(step["premises"] == [] and step["binding"] == {}, "Facts have neither premises nor bindings")
            result = clause["atom"]
            require(not variables(result), "Fact is not ground")
        else:
            require(clause["rule_kind"] in ("explicit_rule", "universal", "definition_forward", "definition_reverse"), "Unknown rule kind")
            rule = {"body": clause["body"], "head": clause["head"]}
            body_variables = _rule_parts(rule)
            binding, premises = step["binding"], step["premises"]
            require(set(binding) == body_variables, "Binding domain must equal the rule body variables")
            require(len(premises) == len(rule["body"]), "Premises do not cover the rule body")
            for premise, idx in zip(rule["body"], premises):
                require(type(idx) is int and 0 <= idx < len(derived), "Premise must reference a previous proof step")
                require(atom_key(substitute(premise, binding)) == atom_key(derived[idx]), "Rule premise does not match its cited proof")
            result = substitute(rule["head"], binding)
        require(not variables(step["atom"]) and atom_key(result) == atom_key(step["atom"]), "Step result differs from the licensed instance")
        derived.append(result)
    idx = certificate["conclusion"]
    require(0 <= idx < len(derived), "Conclusion is outside the proof")
    require(atom_key(derived[idx]) == atom_key(certificate["query"]), "Proof conclusion differs from its target")
    if certificate["proof_kind"] == "clean":
        _, clean, conflicts = independent_closures(active_sources, manual_oracle)
        require(all(atom_key(a)[:2] not in conflicts for a in derived), "A clean proof contains an independently contested atom")
        require(atom_key(certificate["query"]) in clean, "Target has no independent clean derivation")
    return True


def validate_answer_certificates(answer, active_sources, scope, manual_oracle, *,
                                 expected_query, expected_program_sha256=None,
                                 statement_oracle=None):
    """Bind status, proof slots, source program and polarity to a frozen query."""
    fields = {"status", "reason", "scope", "query", "positive_support", "negative_support", "proofs", "missing_premises", "missing_complete", "missing_policy", "contested_premises", "world_truth", "interpretation_status", "semantic_version", "program_sha256", "atom_number", "stats"}
    closed(answer, fields, "query result")
    require(answer["scope"] == scope, "Returned answer is outside the query scope")
    require(answer["world_truth"] == "NOT_ESTABLISHED", "Source-relative answer claims external truth")
    require(atom_key(answer["query"]) == atom_key(expected_query), "Returned answer changed the frozen query")
    require(not variables(expected_query), "Frozen query must be ground")
    require(answer["semantic_version"] == "nabt.signed-horn.v1", "Unknown answer semantics")
    digest(answer["program_sha256"], "Result program")
    if expected_program_sha256 is not None:
        require(answer["program_sha256"] == expected_program_sha256, "Returned answer belongs to another program")
    require(type(answer["positive_support"]) is bool and type(answer["negative_support"]) is bool, "Support flags must be boolean")
    require(type(answer["proofs"]) is dict, "Proof slots must be an object")
    positive, negative = answer["positive_support"], answer["negative_support"]
    status, reason = answer["status"], answer["reason"]
    require(type(status) is str and type(reason) is str, "Status and reason must be strings")
    required, proof_kind = set(), None
    if status == "SUPPORTED":
        require(positive and not negative, "SUPPORTED has inconsistent support flags")
        required, proof_kind = {"query"}, "clean"
    elif status == "REFUTED":
        require(negative and not positive, "REFUTED has inconsistent support flags")
        required, proof_kind = {"opposite"}, "clean"
    elif status == "CONFLICT":
        require(positive and negative, "CONFLICT requires both support signs")
        required = {"query", "opposite"}
    elif status in ("UNKNOWN", "OUT_OF_SCOPE"):
        require(not positive and not negative, "An unsupported status cannot claim support")
    elif status == "DEFER" and reason == "RESOURCE_LIMIT":
        require(not positive and not negative, "An exhausted search cannot claim completed support")
    elif status == "DEFER" and reason == "CONTESTED_PREMISES":
        require(positive != negative, "Contested suspension requires exactly one signed conclusion")
        required = {"query" if positive else "opposite"}
        proof_kind = "signed"
    else:
        raise ReplayValidationError("Unknown answer status or suspension reason")
    require(set(answer["proofs"]) == required, "Proof slots are incomplete or inconsistent with the returned status")
    checked = []
    for slot in sorted(required):
        target = expected_query if slot == "query" else opposite(expected_query)
        independent_certificate(answer["proofs"][slot], active_sources, scope, manual_oracle,
                                expected_query=target, expected_program_sha256=answer["program_sha256"],
                                expected_proof_kind=proof_kind, statement_oracle=statement_oracle)
        checked.append({"side": slot, "independent_replay": True})
    return checked
