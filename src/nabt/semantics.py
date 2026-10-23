"""Source-replayed, scoped, signed Horn reasoning for controlled Arabic v1.

This is a conditional consequence engine, not a source-truth oracle. The native
contracts are adapted from Mashru's generic licensed-rule checker and from the
explicit epistemic/revision contracts in Alghanem; see docs/SEMANTICS.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import json
import re

from .errors import NabtError, natural, resource_limit
from .text_ir import (Atom, Fact, Rule, ParsedDocument, Query, content_id,
                      is_variable, require_name, span_dict, IR_VERSION, LANGUAGE_ID)

SEMANTIC_VERSION = "nabt.signed-horn.v1"
CERTIFICATE_VERSION = "nabt.semantic-certificate.v1"
NUMBER_NAMESPACE = "nabt.scoped-atom"
MAX_ATOM_NUMBER_HEX = 32768
SUPPORTED = "SUPPORTED"
REFUTED = "REFUTED"
CONFLICT = "CONFLICT"
UNKNOWN = "UNKNOWN"
OUT_OF_SCOPE = "OUT_OF_SCOPE"
DEFER = "DEFER"


def _key(atom: Atom) -> tuple:
    return atom.predicate, atom.args, atom.positive


def _unsigned(atom: Atom) -> tuple:
    return atom.predicate, atom.args


def _atom_copy(atom: Atom, *, ground: bool = False) -> Atom:
    if type(atom) is not Atom:
        raise NabtError("INVALID_ATOM", "An atom must use the installed inert Atom type")
    fresh = Atom(atom.predicate, atom.args, atom.positive)
    if ground and not fresh.ground:
        raise NabtError("NONGROUND_ATOM", "Facts and queries must have named ground arguments")
    return fresh


def _atom_from_dict(value: object) -> Atom:
    if type(value) is not dict or set(value) != {"predicate", "args", "positive"}:
        raise NabtError("INVALID_ATOM", "An atom dictionary has exactly predicate, args, positive")
    if type(value["args"]) is not list:
        raise NabtError("INVALID_ATOM", "Serialized arguments must be a list")
    return _atom_copy(Atom(value["predicate"], tuple(value["args"]), value["positive"]), ground=True)


def atom_number(atom: Atom, scope: str = "default") -> dict:
    """An exact reversible number of a scoped statement, with no truth authority."""
    atom = _atom_copy(atom, ground=True)
    require_name(scope, "scope")
    payload = json.dumps([IR_VERSION, scope, atom.predicate, list(atom.args), atom.positive],
                         ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    number = int.from_bytes(b"\x01" + payload, "big")
    encoded = format(number, "x")
    if len(encoded) > MAX_ATOM_NUMBER_HEX:
        raise resource_limit("Scoped atom encoding exceeds its byte budget")
    return {"namespace": NUMBER_NAMESPACE, "version": 1, "domain": "scoped-signed-atom",
            "encoding": "canonical-json-utf8-big-endian", "value_hex": encoded}


def decode_atom_number(record: dict) -> tuple[str, Atom]:
    expected = {"namespace", "version", "domain", "encoding", "value_hex"}
    if type(record) is not dict or set(record) != expected:
        raise NabtError("INVALID_SEMANTIC_NUMBER", "A scoped number requires its complete namespace")
    if (record["namespace"] != NUMBER_NAMESPACE or type(record["version"]) is not int
            or record["version"] != 1 or record["domain"] != "scoped-signed-atom"
            or record["encoding"] != "canonical-json-utf8-big-endian"):
        raise NabtError("INVALID_SEMANTIC_NUMBER", "Uninstalled semantic number namespace/version")
    value = record["value_hex"]
    if type(value) is not str or len(value) > MAX_ATOM_NUMBER_HEX or not re.fullmatch(r"[1-9a-f][0-9a-f]*", value):
        raise NabtError("INVALID_SEMANTIC_NUMBER", "The hexadecimal natural must be bounded and canonical")
    number = int(value, 16)
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big")
    try:
        if raw[:1] != b"\x01":
            raise ValueError("missing framing byte")
        _json_depth(raw[1:], 8)
        data = json.loads(raw[1:].decode("utf-8"))
        if type(data) is not list or len(data) != 5 or data[0] != IR_VERSION or type(data[3]) is not list:
            raise ValueError("incorrect identity payload")
        scope, atom = data[1], Atom(data[2], tuple(data[3]), data[4])
        if atom_number(atom, scope) != record:
            raise ValueError("noncanonical identity payload")
        return scope, atom
    except (ValueError, TypeError, UnicodeError, NabtError, RecursionError) as exc:
        raise NabtError("INVALID_SEMANTIC_NUMBER", "The number is not an exact installed atom encoding") from exc


@dataclass(frozen=True, slots=True)
class SemanticBudget:
    max_sources: int = 64
    max_total_source_bytes: int = 1048576
    max_facts: int = 4096
    max_rules: int = 2048
    max_atoms: int = 16384
    max_groundings: int = 100000
    max_join_steps: int = 500000
    max_rounds: int = 512
    max_proof_steps: int = 8192
    max_backward_depth: int = 12
    max_missing_plans: int = 128
    max_plan_atoms: int = 64
    max_output_bytes: int = 8388608
    max_certificate_nodes: int = 1000000
    max_certificate_depth: int = 64

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            natural(value, name, maximum=10000000)


@dataclass
class _Meter:
    budget: SemanticBudget
    join_steps: int = 0
    groundings: int = 0
    rounds: int = 0

    def tick(self, kind: str, count: int = 1) -> None:
        value = getattr(self, kind) + count
        setattr(self, kind, value)
        if value > getattr(self.budget, "max_" + kind):
            raise resource_limit("Semantic computation exhausted its declared budget", budget=kind,
                                 maximum=getattr(self.budget, "max_" + kind))

    def as_dict(self) -> dict:
        return {"join_steps": self.join_steps, "groundings": self.groundings, "rounds": self.rounds}


@dataclass(frozen=True, slots=True)
class AdmissionReport:
    accepted: bool
    status: str
    source_id: str
    scope: str
    source_sha256: str
    program_sha256: str
    residuals: tuple[dict, ...] = ()

    def as_dict(self) -> dict:
        return {"accepted": self.accepted, "status": self.status, "source_id": self.source_id,
                "scope": self.scope, "source_sha256": self.source_sha256,
                "program_sha256": self.program_sha256, "residuals": list(self.residuals),
                "world_truth": "NOT_ESTABLISHED"}


@dataclass(frozen=True, slots=True)
class RevisionReport:
    accepted: bool
    status: str
    source_id: str
    before_program_sha256: str
    program_sha256: str
    removed_supports: tuple[dict, ...] = ()
    residuals: tuple[dict, ...] = ()

    def as_dict(self) -> dict:
        return {"accepted": self.accepted, "status": self.status, "source_id": self.source_id,
                "before_program_sha256": self.before_program_sha256,
                "program_sha256": self.program_sha256,
                "removed_supports": list(self.removed_supports), "residuals": list(self.residuals),
                "world_truth": "NOT_ESTABLISHED"}


@dataclass(frozen=True, slots=True)
class QueryResult:
    status: str
    reason: str
    scope: str
    query: Atom
    positive_support: bool
    negative_support: bool
    proofs: dict
    missing_premises: tuple[dict, ...]
    contested_premises: tuple[Atom, ...]
    program_sha256: str
    missing_complete: bool = True
    stats: dict | None = None

    def as_dict(self) -> dict:
        return {"status": self.status, "reason": self.reason, "scope": self.scope,
                "query": self.query.as_dict(), "positive_support": self.positive_support,
                "negative_support": self.negative_support, "proofs": self.proofs,
                "missing_premises": list(self.missing_premises), "missing_complete": self.missing_complete,
                "missing_policy": "bounded_grounded_backward_plans_active_and_query_constants.v1",
                "contested_premises": [a.as_dict() for a in self.contested_premises],
                "world_truth": "NOT_ESTABLISHED",
                "interpretation_status": "OUT_OF_SCOPE" if self.status == OUT_OF_SCOPE else "READ",
                "semantic_version": SEMANTIC_VERSION, "program_sha256": self.program_sha256,
                "atom_number": atom_number(self.query, self.scope), "stats": self.stats or {}}


@dataclass(frozen=True, slots=True)
class _Clause:
    clause_id: str
    scope: str
    source_id: str
    source_sha256: str
    record: Fact | Rule

    def identity(self) -> dict:
        r = self.record
        common = {"clause_id": self.clause_id, "scope": self.scope, "source_id": self.source_id,
                  "source_sha256": self.source_sha256, "span": span_dict(r.span),
                  "component_spans": [span_dict(s) for s in r.component_spans],
                  "analysis_id": r.analysis_id}
        if type(r) is Fact:
            return {**common, "kind": "fact", "atom": r.atom.as_dict()}
        return {**common, "kind": "rule", "body": [a.as_dict() for a in r.body],
                "head": r.head.as_dict(), "rule_kind": r.kind}


@dataclass(frozen=True, slots=True)
class _Program:
    documents: tuple[ParsedDocument, ...]
    facts: tuple[_Clause, ...]
    rules: tuple[_Clause, ...]
    signatures: dict[tuple[str, str], int]
    constants: dict[str, frozenset[str]]
    sha256: str


@dataclass(frozen=True, slots=True)
class _Proof:
    # ``None`` is used only inside a discarded counterfactual completion run.
    # Such a node has no source evidence and can never become a certificate.
    clause: _Clause | None
    premises: tuple[Atom, ...] = ()
    binding: tuple[tuple[str, str], ...] = ()


def _reader(language_id: str):
    """Dispatch only installed reading laws; callers cannot inject a parser."""
    if type(language_id) is not str:
        raise NabtError("UNSUPPORTED_TEXT_LANGUAGE", "Select an installed exact language identifier")
    if language_id == LANGUAGE_ID:
        from . import text_reader
        return text_reader
    from . import arabic_reader
    if language_id == arabic_reader.LANGUAGE_ID:
        return arabic_reader
    raise NabtError("UNSUPPORTED_TEXT_LANGUAGE", "No installed reader has this language identifier")


def _parse(raw: str | bytes, source_id: str, scope: str, language_id: str = LANGUAGE_ID) -> ParsedDocument:
    return _reader(language_id).parse_document(raw, source_id=source_id, scope=scope)


def _compile(sources: dict[str, tuple[bytes, str]], budget: SemanticBudget,
             language_id: str = LANGUAGE_ID) -> _Program:
    _reader(language_id)
    if len(sources) > budget.max_sources or sum(len(raw) for raw, _ in sources.values()) > budget.max_total_source_bytes:
        raise resource_limit("Active source inventory exceeds its budget")
    documents = tuple(_parse(raw, source_id, scope, language_id) for source_id, (raw, scope) in sorted(sources.items()))
    signatures: dict[tuple[str, str], int] = {}
    constants: dict[str, set[str]] = {}
    facts, rules = [], []

    def signature(scope: str, predicate: str, arity: int) -> None:
        key = scope, predicate
        if key in signatures and signatures[key] != arity:
            raise NabtError("ARITY_CONFLICT", "A predicate has incompatible signatures in one scope",
                            details={"scope": scope, "predicate": predicate,
                                     "existing_arity": signatures[key], "new_arity": arity})
        signatures[key] = arity

    for doc in documents:
        require_name(doc.scope, "scope")
        if doc.residuals:
            raise NabtError("UNREAD_SOURCE", "A source with any residual cannot contribute facts or rules",
                            details={"source_id": doc.source.source_id,
                                     "residuals": [r.as_dict() for r in doc.residuals]})
        constants.setdefault(doc.scope, set())
        for declaration in doc.declarations:
            if declaration.kind == "individual":
                constants[doc.scope].add(declaration.name)
            elif declaration.kind in ("concept", "relation"):
                signature(doc.scope, declaration.name, 1 if declaration.kind == "concept" else 2)
            else:
                raise NabtError("INVALID_DECLARATION", "Uninstalled declaration kind")
        for record in (*doc.facts, *doc.rules):
            if type(record) is Fact:
                atoms = (_atom_copy(record.atom, ground=True),)
                payload = {"atom": record.atom.as_dict()}
            else:
                if type(record) is not Rule or not record.body or len(record.body) > 16:
                    raise NabtError("INVALID_RULE", "Rules require one to sixteen explicit premises")
                atoms = (*record.body, record.head)
                for atom in atoms:
                    _atom_copy(atom)
                variables = frozenset().union(*(a.variables for a in record.body))
                if not record.head.variables <= variables:
                    raise NabtError("UNSAFE_RULE", "Every head variable must occur in a body premise")
                payload = {"body": [a.as_dict() for a in record.body],
                           "head": record.head.as_dict(), "kind": record.kind}
            for atom in atoms:
                signature(doc.scope, atom.predicate, len(atom.args))
                constants[doc.scope].update(a for a in atom.args if not is_variable(a))
            payload.update({"semantic_version": SEMANTIC_VERSION, "scope": doc.scope,
                            "source_id": doc.source.source_id, "source_sha256": doc.source.sha256,
                            "span": span_dict(record.span), "analysis_id": record.analysis_id})
            clause = _Clause(content_id(payload), doc.scope, doc.source.source_id, doc.source.sha256, record)
            (facts if type(record) is Fact else rules).append(clause)
    if len(facts) > budget.max_facts or len(rules) > budget.max_rules:
        raise resource_limit("Active facts or rules exceed the semantic inventory budget")
    digest = content_id({"version": SEMANTIC_VERSION, "language": language_id,
                         "sources": [[d.source.source_id, d.source.sha256, d.scope] for d in documents]})
    return _Program(documents, tuple(facts), tuple(rules), signatures,
                    {scope: frozenset(items) for scope, items in constants.items()}, digest)


def _unify(pattern: Atom, ground: Atom, binding: dict[str, str]) -> dict[str, str] | None:
    if (pattern.predicate, pattern.positive, len(pattern.args)) != (ground.predicate, ground.positive, len(ground.args)):
        return None
    result = dict(binding)
    for term, value in zip(pattern.args, ground.args):
        if is_variable(term):
            if term in result and result[term] != value:
                return None
            result[term] = value
        elif term != value:
            return None
    return result


def _instantiate(atom: Atom, binding: dict[str, str]) -> Atom:
    return Atom(atom.predicate, tuple(binding[a] if is_variable(a) else a for a in atom.args), atom.positive)


def _closure(program: _Program, scope: str, meter: _Meter,
             blocked: frozenset[tuple] = frozenset(),
             hypotheses: tuple[Atom, ...] = ()) -> dict[Atom, _Proof]:
    result: dict[Atom, _Proof] = {}
    index: dict[tuple, list[Atom]] = {}

    def add(atom: Atom, proof: _Proof) -> bool:
        if atom in result or _unsigned(atom) in blocked:
            return False
        if len(result) >= meter.budget.max_atoms:
            raise resource_limit("Semantic closure exceeds its ground-atom budget")
        result[atom] = proof
        index.setdefault((atom.predicate, atom.positive, len(atom.args)), []).append(atom)
        return True

    for clause in program.facts:
        if clause.scope == scope:
            add(clause.record.atom, _Proof(clause))
    for hypothesis in hypotheses:
        add(hypothesis, _Proof(None))
    rules = tuple(r for r in program.rules if r.scope == scope)
    changed = True
    while changed:
        meter.tick("rounds")
        changed = False
        for clause in rules:
            rule = clause.record
            states: list[tuple[dict, tuple[Atom, ...]]] = [({}, ())]
            for pattern in rule.body:
                next_states = []
                for binding, premises in states:
                    for candidate in tuple(index.get((pattern.predicate, pattern.positive, len(pattern.args)), ())):
                        meter.tick("join_steps")
                        extended = _unify(pattern, candidate, binding)
                        if extended is not None:
                            next_states.append((extended, premises + (candidate,)))
                states = next_states
                if not states:
                    break
            for binding, premises in states:
                meter.tick("groundings")
                head = _instantiate(rule.head, binding)
                changed = add(head, _Proof(clause, premises, tuple(sorted(binding.items())))) or changed
    return result


def _conflicts(signed: dict[Atom, _Proof]) -> frozenset[tuple]:
    return frozenset(_unsigned(a) for a in signed if a.opposite() in signed)


def _certificate(atom: Atom, proofs: dict[Atom, _Proof], scope: str, program: _Program,
                 kind: str, budget: SemanticBudget) -> dict:
    steps, indices = [], {}
    # Iterative traversal avoids dependence on Python's recursion limit.
    pending = [(atom, False)]
    while pending:
        current, ready = pending.pop()
        if current in indices:
            continue
        proof = proofs[current]
        if proof.clause is None:
            raise NabtError("HYPOTHESIS_IS_NOT_EVIDENCE", "Counterfactual premises cannot become source certificates")
        if not ready:
            pending.append((current, True))
            pending.extend((p, False) for p in reversed(proof.premises) if p not in indices)
            continue
        if len(steps) >= budget.max_proof_steps:
            raise resource_limit("Semantic certificate exceeds its step budget")
        indices[current] = len(steps)
        steps.append({"atom": current.as_dict(), "clause": proof.clause.identity(),
                      "binding": dict(proof.binding), "premises": [indices[p] for p in proof.premises]})
    return {"version": CERTIFICATE_VERSION, "scope": scope, "query": atom.as_dict(),
            "proof_kind": kind, "program_sha256": program.sha256, "steps": steps,
            "conclusion": indices[atom], "world_truth": "NOT_ESTABLISHED"}


def _contested(atom: Atom, proofs: dict[Atom, _Proof], conflicts: frozenset[tuple]) -> tuple[Atom, ...]:
    pending, visited, found = [atom], set(), set()
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        if _unsigned(current) in conflicts:
            found.add(current)
        pending.extend(proofs[current].premises)
    return tuple(sorted(found, key=_key))


def _minimal(plans: list[tuple[frozenset[Atom], tuple[str, ...]]], budget: SemanticBudget) -> list:
    result = []
    for atoms, rules in sorted(plans, key=lambda p: (len(p[0]), tuple(sorted((_key(a) for a in p[0]))), p[1])):
        if len(atoms) > budget.max_plan_atoms:
            raise resource_limit("Missing-premise plan exceeds its atom budget")
        if any(existing <= atoms for existing, _ in result):
            continue
        result.append((atoms, rules))
        if len(result) > budget.max_missing_plans:
            raise resource_limit("Missing-premise alternatives exceed their plan budget")
    return result


def _missing(target: Atom, program: _Program, scope: str, clean: dict[Atom, _Proof],
             meter: _Meter, conflicts: frozenset[tuple]) -> tuple[dict, ...]:
    domain = tuple(sorted(program.constants.get(scope, frozenset()) | set(target.args)))
    rules = tuple(c for c in program.rules if c.scope == scope)

    def visit(goal: Atom, path: frozenset[Atom], depth: int) -> list:
        meter.tick("join_steps")
        if goal in clean:
            return [(frozenset(), ())]
        if goal.opposite() in clean or _unsigned(goal) in conflicts:
            return []
        if goal in path:
            return [(frozenset((goal,)), ())]
        if depth > meter.budget.max_backward_depth:
            raise resource_limit("Missing-premise search exhausted its depth budget")
        # An unsupported ground statement itself is always a possible new
        # premise. This escape leaf keeps recursive definitions from hiding
        # the useful option of supplying their missing components directly.
        alternatives = [(frozenset((goal,)), ())]
        for clause in rules:
            binding = _unify(clause.record.head, goal, {})
            if binding is None:
                continue
            variables = set().union(*(a.variables for a in clause.record.body)) - set(binding)
            remaining = tuple(sorted(variables))
            for values in product(domain, repeat=len(remaining)):
                meter.tick("groundings")
                full = {**binding, **dict(zip(remaining, values))}
                combined = [(frozenset(), (clause.clause_id,))]
                for pattern in clause.record.body:
                    children = visit(_instantiate(pattern, full), path | {goal}, depth + 1)
                    crossed = []
                    for left, lrules in combined:
                        for right, rrules in children:
                            meter.tick("join_steps")
                            crossed.append((left | right, tuple(dict.fromkeys(lrules + rrules))))
                    combined = _minimal(crossed, meter.budget)
                    if not combined:
                        break
                alternatives.extend(combined)
                alternatives = _minimal(alternatives, meter.budget)
        return alternatives or [(frozenset((goal,)), ())]

    candidates = visit(target, frozenset(), 0)
    validated = []
    for atoms, rules in candidates:
        if any(a.opposite() in atoms for a in atoms):
            continue
        hypotheses = tuple(sorted(atoms, key=_key))
        hypothetical_signed = _closure(program, scope, meter, hypotheses=hypotheses)
        hypothetical_clean = _closure(program, scope, meter, _conflicts(hypothetical_signed), hypotheses)
        if target in hypothetical_clean:
            validated.append((atoms, rules))
    plans = _minimal(validated, meter.budget)
    # Remove the direct-target alternative only after another sufficient,
    # conflict-clean completion has survived actual counterfactual replay.
    if any(target not in atoms for atoms, _ in plans):
        plans = [(atoms, rules) for atoms, rules in plans if target not in atoms]
    return tuple({"atoms": [a.as_dict() for a in sorted(atoms, key=_key)], "via_rules": list(rules),
                  "validation": "counterfactual_signed_and_clean_replay.v1"}
                 for atoms, rules in plans)


def _json_depth(raw: bytes, maximum: int) -> None:
    depth, quoted, escaped = 0, False, False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > maximum:
                raise NabtError("INVALID_JSON_DEPTH", "JSON nesting exceeds its installed domain")
        elif byte in (93, 125):
            depth -= 1


def _inert_json(value: object, budget: SemanticBudget) -> bytes:
    """Bound hostile input before recursive serialization or semantic replay."""
    stack, active, nodes, size = [(value, 0, False)], set(), 0, 0
    while stack:
        node, depth, leaving = stack.pop()
        if leaving:
            active.remove(id(node))
            continue
        nodes += 1
        if nodes > budget.max_certificate_nodes or depth > budget.max_certificate_depth:
            raise resource_limit("Inert semantic JSON exceeds its node or depth budget")
        kind = type(node)
        if kind is str:
            try:
                size += len(node.encode("utf-8")) + 2
            except UnicodeError as exc:
                raise NabtError("INVALID_CERTIFICATE", "JSON contains an invalid Unicode string") from exc
        elif kind is int:
            if node.bit_length() > 64:
                raise NabtError("INVALID_CERTIFICATE", "JSON integers exceed the installed certificate domain")
            size += 22
        elif kind is bool or node is None:
            size += 5
        elif kind in (dict, list):
            if id(node) in active:
                raise NabtError("INVALID_CERTIFICATE", "Cyclic objects are not inert JSON")
            if len(node) > budget.max_certificate_nodes - nodes:
                raise resource_limit("Inert semantic JSON container exceeds its node budget")
            active.add(id(node))
            stack.append((node, depth, True))
            size += 2 + 2 * len(node)
            if kind is dict:
                for key, item in node.items():
                    if type(key) is not str:
                        raise NabtError("INVALID_CERTIFICATE", "JSON object keys must be exact strings")
                    stack.append((key, depth + 1, False))
                    stack.append((item, depth + 1, False))
            else:
                stack.extend((item, depth + 1, False) for item in node)
        else:
            raise NabtError("INVALID_CERTIFICATE", "Only inert JSON containers and scalar values are admitted")
        if size > budget.max_output_bytes:
            raise resource_limit("Inert semantic JSON exceeds its byte budget")
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise NabtError("INVALID_CERTIFICATE", "Invalid inert JSON representation") from exc
    if len(encoded) > budget.max_output_bytes:
        raise resource_limit("Inert semantic JSON exceeds its serialized byte budget")
    return encoded


class SemanticKernel:
    """A finite source-relative theory. Every consumption reparses original bytes.

    Sources may be added, explicitly replaced, or removed. Failed admissions are
    atomic. The public snapshot is inert data, never an authority-bearing image.
    """

    def __init__(self, *, budget: SemanticBudget | None = None, language_id: str = LANGUAGE_ID) -> None:
        _reader(language_id)
        self._language_id = language_id
        self.budget = budget or SemanticBudget()
        if type(self.budget) is not SemanticBudget:
            raise NabtError("INVALID_BUDGET", "Use the installed semantic budget record")
        self.budget.__post_init__()
        self._sources: dict[str, tuple[bytes, str]] = {}
        self._known_programs: set[str] = {self._program().sha256}

    @property
    def language_id(self) -> str:
        return self._language_id

    def _program(self) -> _Program:
        return _compile(dict(self._sources), self.budget, self.language_id)

    def _admit(self, document: ParsedDocument, *, replacing: bool = False) -> AdmissionReport:
        if type(document) is not ParsedDocument:
            raise NabtError("INVALID_DOCUMENT", "Admission requires a parsed document with original bytes")
        # Ignore the supplied facts, rules, residual flags, source hash, and reader version.
        doc = _parse(document.source.raw_bytes, document.source.source_id, document.scope, self.language_id)
        before = self._program()
        if doc.source.source_id in self._sources and not replacing:
            return AdmissionReport(False, "REJECT", doc.source.source_id, doc.scope, doc.source.sha256,
                                   before.sha256, ({"code": "SOURCE_EXISTS", "message": "Use replace_source explicitly"},))
        if doc.residuals:
            status = "DEFER" if any(r.code.startswith("UNSUPPORTED_") for r in doc.residuals) else "REJECT"
            return AdmissionReport(False, status, doc.source.source_id, doc.scope, doc.source.sha256,
                                   before.sha256, tuple(r.as_dict() for r in doc.residuals))
        candidate = {**self._sources, doc.source.source_id: (doc.source.raw_bytes, doc.scope)}
        try:
            after = _compile(candidate, self.budget, self.language_id)
        except NabtError as exc:
            return AdmissionReport(False, exc.status, doc.source.source_id, doc.scope, doc.source.sha256,
                                   before.sha256, (exc.as_dict(),))
        self._sources = candidate
        self._known_programs.update((before.sha256, after.sha256))
        return AdmissionReport(True, "ADMITTED", doc.source.source_id, doc.scope, doc.source.sha256, after.sha256)

    def add_document(self, document: ParsedDocument) -> AdmissionReport:
        return self._admit(document)

    def add_source(self, raw: str | bytes, *, source_id: str = "text", scope: str = "default") -> AdmissionReport:
        return self._admit(_parse(raw, source_id, scope, self.language_id))

    def _removed(self, before: _Program, after: _Program, scopes: set[str]) -> tuple[dict, ...]:
        lost = []
        for scope in sorted(scopes):
            left = _closure(before, scope, _Meter(self.budget))
            right = _closure(after, scope, _Meter(self.budget))
            lost.extend({"scope": scope, "atom": a.as_dict()} for a in sorted(set(left) - set(right), key=_key))
        return tuple(lost)

    def remove_source(self, source_id: str) -> RevisionReport:
        before = self._program()
        if source_id not in self._sources:
            return RevisionReport(False, "REJECT", source_id, before.sha256, before.sha256,
                                  residuals=({"code": "UNKNOWN_SOURCE", "message": "No active source has that identity"},))
        scope = self._sources[source_id][1]
        candidate = {key: val for key, val in self._sources.items() if key != source_id}
        after = _compile(candidate, self.budget, self.language_id)
        # Removal itself always succeeds. A bounded change report may be incomplete.
        residuals = ()
        try:
            lost = self._removed(before, after, {scope})
        except NabtError as exc:
            lost, residuals = (), (exc.as_dict(),)
        self._sources = candidate
        self._known_programs.update((before.sha256, after.sha256))
        return RevisionReport(True, "REMOVED", source_id, before.sha256, after.sha256, lost, residuals)

    def replace_source(self, raw: str | bytes, *, source_id: str, scope: str | None = None) -> RevisionReport:
        before = self._program()
        if source_id not in self._sources:
            return RevisionReport(False, "REJECT", source_id, before.sha256, before.sha256,
                                  residuals=({"code": "UNKNOWN_SOURCE", "message": "Replace requires an active source"},))
        previous_scope = self._sources[source_id][1]
        report = self._admit(_parse(raw, source_id, previous_scope if scope is None else scope,
                                   self.language_id), replacing=True)
        if not report.accepted:
            return RevisionReport(False, report.status, source_id, before.sha256, before.sha256,
                                  residuals=report.residuals)
        after = self._program()
        residuals = ()
        try:
            lost = self._removed(before, after, {previous_scope, report.scope})
        except NabtError as exc:
            lost, residuals = (), (exc.as_dict(),)
        return RevisionReport(True, "REPLACED", source_id, before.sha256, after.sha256, lost, residuals)

    def query_text(self, text: str | bytes, *, scope: str = "default") -> QueryResult:
        return self.query(text, scope=scope)

    def read_query(self, text: str | bytes, *, scope: str = "default") -> Query:
        reader = _reader(self.language_id)
        if self.language_id == LANGUAGE_ID:
            return reader.parse_query(text, scope=scope)
        # A query can reuse subject identities witnessed in its active theory.
        # This licenses a target reading only, never a fact or source admission.
        program = self._program()
        subjects = set()
        for doc in program.documents:
            if doc.scope == scope:
                subjects.update(d.name for d in doc.declarations if d.kind == "individual")
                subjects.update(f.atom.args[0] for f in doc.facts)
        return reader.parse_query(text, scope=scope, known_individuals=frozenset(subjects))

    def query(self, query: Query | Atom | str | bytes, *, scope: str | None = None) -> QueryResult:
        if type(query) in (str, bytes):
            query = self.read_query(query, scope="default" if scope is None else scope)
        if type(query) is Query:
            if scope is not None and scope != query.scope:
                raise NabtError("QUERY_SCOPE_MISMATCH", "A parsed query cannot silently move to another scope")
            scope, atom = query.scope, _atom_copy(query.atom, ground=True)
        else:
            scope, atom = "default" if scope is None else scope, _atom_copy(query, ground=True)
        require_name(scope, "scope")
        program = self._program()
        if program.signatures.get((scope, atom.predicate)) != len(atom.args):
            return QueryResult(OUT_OF_SCOPE, "UNDECLARED_PREDICATE_OR_ARITY", scope, atom, False, False,
                               {}, (), (), program.sha256)
        meter = _Meter(self.budget)
        try:
            signed = _closure(program, scope, meter)
            conflicts = _conflicts(signed)
            clean = _closure(program, scope, meter, conflicts)
            positive, negative = atom in signed, atom.opposite() in signed
            proofs = {}
            for name, conclusion in (("query", atom), ("opposite", atom.opposite())):
                if conclusion in signed:
                    selected = clean if conclusion in clean else signed
                    proofs[name] = _certificate(conclusion, selected, scope, program,
                                                "clean" if conclusion in clean else "signed", self.budget)
            contested = set()
            for conclusion in (atom, atom.opposite()):
                if conclusion in signed and conclusion not in clean:
                    contested.update(_contested(conclusion, signed, conflicts))
            if positive and negative:
                status, reason, missing = CONFLICT, "BOTH_SIGNS_SUPPORTED", ()
            elif atom in clean:
                status, reason, missing = SUPPORTED, "CLEAN_DERIVATION", ()
            elif atom.opposite() in clean:
                status, reason, missing = REFUTED, "CLEAN_OPPOSITE_DERIVATION", ()
            elif positive or negative:
                status, reason, missing = DEFER, "CONTESTED_PREMISES", ()
            else:
                status, reason = UNKNOWN, "NO_SUPPORTED_SIGN"
                missing = _missing(atom, program, scope, clean, meter, conflicts)
            result = QueryResult(status, reason, scope, atom, positive, negative, proofs, missing,
                                 tuple(sorted(contested, key=_key)), program.sha256, True, meter.as_dict())
            _inert_json(result.as_dict(), self.budget)
            return result
        except NabtError as exc:
            if exc.code != "RESOURCE_LIMIT":
                raise
            return QueryResult(DEFER, "RESOURCE_LIMIT", scope, atom, False, False, {}, (), (),
                               program.sha256, False, {**meter.as_dict(), "limit": exc.details})

    def verify_certificate(self, certificate: object) -> dict:
        """Independent replay, against re-extracted current source clauses.

        A digest is an index, never an authority flag. Unrelated additions or
        removals need not invalidate a still-supported proof; changed or withdrawn
        dependencies do. Clean proofs are also rechecked for current conflicts.
        """
        checked = 0
        program = self._program()
        try:
            _inert_json(certificate, self.budget)
            fields = {"version", "scope", "query", "proof_kind", "program_sha256", "steps", "conclusion", "world_truth"}
            if type(certificate) is not dict or set(certificate) != fields or certificate.get("version") != CERTIFICATE_VERSION:
                raise NabtError("INVALID_CERTIFICATE", "Uninstalled semantic certificate")
            if (type(certificate.get("program_sha256")) is not str
                    or certificate["program_sha256"] not in self._known_programs):
                raise NabtError("UNKNOWN_CERTIFICATE_SNAPSHOT", "The claimed origin snapshot was never admitted in this session")
            scope = require_name(certificate.get("scope"), "scope")
            kind = certificate.get("proof_kind")
            if kind not in ("clean", "signed") or certificate.get("world_truth") != "NOT_ESTABLISHED":
                raise NabtError("INVALID_CERTIFICATE", "Invalid proof kind or unsupported world-truth claim")
            steps = certificate.get("steps")
            if type(steps) is not list or len(steps) > self.budget.max_proof_steps:
                raise NabtError("INVALID_CERTIFICATE", "Certificate steps must be a bounded list")
            clauses = {c.clause_id: c for c in (*program.facts, *program.rules) if c.scope == scope}
            conflicts = _conflicts(_closure(program, scope, _Meter(self.budget))) if kind == "clean" else frozenset()
            established = []
            for step in steps:
                if type(step) is not dict or set(step) != {"atom", "clause", "binding", "premises"}:
                    raise NabtError("INVALID_CERTIFICATE", "Malformed proof step")
                atom = _atom_from_dict(step["atom"])
                claim = step["clause"]
                if type(claim) is not dict or type(claim.get("clause_id")) is not str:
                    raise NabtError("INVALID_CERTIFICATE", "Missing live clause identity")
                clause = clauses.get(claim["clause_id"])
                if clause is None or _inert_json(claim, self.budget) != _inert_json(clause.identity(), self.budget):
                    raise NabtError("STALE_OR_FORGED_CLAUSE", "Clause differs from current source replay")
                if _unsigned(atom) in conflicts:
                    raise NabtError("CONTESTED_PREMISES", "A clean certificate cannot contain a conflicted atom")
                refs, binding = step["premises"], step["binding"]
                if type(refs) is not list or any(type(i) is not int or not 0 <= i < len(established) for i in refs):
                    raise NabtError("INVALID_CERTIFICATE", "Premises must refer to preceding checked steps")
                if type(binding) is not dict or any(type(k) is not str or type(v) is not str or is_variable(v)
                                                     for k, v in binding.items()):
                    raise NabtError("INVALID_CERTIFICATE", "Ground substitutions require exact string terms")
                record = clause.record
                if type(record) is Fact:
                    if refs or binding or atom != record.atom:
                        raise NabtError("INVALID_CERTIFICATE", "Fact step differs from its extracted fact")
                else:
                    variables = set().union(*(a.variables for a in record.body))
                    if set(binding) != variables:
                        raise NabtError("INVALID_CERTIFICATE", "Substitution does not bind exactly the rule variables")
                    expected = [_instantiate(a, binding) for a in record.body]
                    if expected != [established[i] for i in refs] or atom != _instantiate(record.head, binding):
                        raise NabtError("INVALID_CERTIFICATE", "Rule grounding or antecedent sequence does not match")
                established.append(atom)
                checked += 1
            conclusion = certificate.get("conclusion")
            if type(conclusion) is not int or not 0 <= conclusion < len(established):
                raise NabtError("INVALID_CERTIFICATE", "Missing checked conclusion")
            if established[conclusion] != _atom_from_dict(certificate.get("query")):
                raise NabtError("INVALID_CERTIFICATE", "Claim is not its checked conclusion")
            return {"accepted": True, "status": "VERIFIED", "checked_steps": checked,
                    "program_sha256": program.sha256, "world_truth": "NOT_ESTABLISHED"}
        except (NabtError, ValueError, TypeError, KeyError, IndexError) as exc:
            return {"accepted": False, "status": "DEFER" if isinstance(exc, NabtError) and exc.status == "DEFER" else "REJECT",
                    "reason": exc.code if isinstance(exc, NabtError) else "INVALID_CERTIFICATE",
                    "checked_steps": checked, "program_sha256": program.sha256,
                    "world_truth": "NOT_ESTABLISHED"}

    def snapshot(self) -> dict:
        program = self._program()
        result = {"semantic_version": SEMANTIC_VERSION, "language_id": self.language_id,
                "program_sha256": program.sha256, "world_truth": "NOT_ESTABLISHED",
                "sources": [{"source_id": d.source.source_id, "source_sha256": d.source.sha256,
                             "scope": d.scope, "raw_utf8_hex": d.source.raw_bytes.hex()}
                            for d in program.documents],
                "signatures": [{"scope": scope, "predicate": name, "arity": arity}
                               for (scope, name), arity in sorted(program.signatures.items())],
                "facts": [c.identity() for c in program.facts], "rules": [c.identity() for c in program.rules],
                "budget": {name: getattr(self.budget, name) for name in self.budget.__dataclass_fields__}}
        _inert_json(result, self.budget)
        return result

    def as_dict(self) -> dict:
        return self.snapshot()


Kernel = SemanticKernel
