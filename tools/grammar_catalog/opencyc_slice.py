"""Bounded Cyc-style source slice -> the existing signed ground-reading owner.

This is NOT a full CycL/OWL reader or an OpenCyc truth engine. A selected
microtheory must contain only the admitted, explicitly asserted fragment.
Unknown syntax/defaults defer the whole selected slice; they are never dropped.
An Arabic occurrence is an A116 identity candidate, NOT a lexical alignment.
All external use is through relations.analyze and gateway independent replay.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

SCHEMA = "nabt.opencyc-slice.v1"
RESULT = "nabt.opencyc-slice-result.v1"
LAW = "nabt.opencyc-signed-fragment.v1"
ROOT = Path(__file__).resolve().parents[2]
MAX_LEDGER_BYTES = 32768
MAX_RECORDS = 32
MAX_TERMS = 16
MAX_CLAUSES = 240
MAX_PROGRAM_BYTES = 60000
CONST = re.compile(r"#\$[A-Za-z][A-Za-z0-9_-]{0,62}\Z")
TOKEN = re.compile(r"\s+|[()]|#\$[A-Za-z][A-Za-z0-9_-]*|[A-Za-z][A-Za-z0-9_-]*|[0-9]+")
PRED = {"isa": "oc_isa", "genls": "oc_genls", "disjointWith": "oc_disjoint"}
PUBLIC_LIMITS = {
    "full_cycl_supported": False, "owl_export_parsed": False,
    "source_authenticated": False, "source_license_legally_admitted": False,
    "microtheory_inheritance_supported": False,
    "defaults_or_existentials_supported": False,
    "arabic_lexical_alignment_established": False,
    "world_truth_established": False, "neural_training_performed": False,
    "new_lean_theorem": False, "python_lean_refinement_proved": False,
    "action_authority": "NONE",
}


class SliceError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def digest(value):
    return sha256(wire(value).encode()).hexdigest()


def fields(value, keys, label):
    if type(value) is not dict or set(value) != set(keys):
        raise SliceError("INVALID_INPUT", "Unexpected fields: " + label)


def text(value, label, maximum=256):
    if type(value) is not str or not value or "\x00" in value:
        raise SliceError("INVALID_INPUT", "Expected nonempty text: " + label)
    try:
        raw = value.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise SliceError("INVALID_INPUT", "Invalid Unicode: " + label) from exc
    if len(raw) > maximum:
        raise SliceError("RESOURCE_LIMIT", "Text budget exceeded: " + label)
    return raw


def constant(value):
    if type(value) is not str or not CONST.fullmatch(value):
        raise SliceError("INVALID_INPUT", "Expected a bounded explicit Cyc constant")
    return value


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise SliceError("INVALID_INPUT", "Duplicate JSON key")
        result[key] = value
    return result


def records(ledger):
    raw = text(ledger, "ledger", MAX_LEDGER_BYTES)
    rows, seen, offset = [], set(), 0
    for line in raw.splitlines(keepends=True):
        end = offset + len(line)
        if line.strip():
            if len(rows) >= MAX_RECORDS:
                raise SliceError("RESOURCE_LIMIT", "Record count exceeded")
            try:
                item = json.loads(line, object_pairs_hook=_pairs)
            except (ValueError, UnicodeError, RecursionError) as exc:
                raise SliceError("INVALID_INPUT", "Malformed source record") from exc
            fields(item, ("id", "mt", "strength", "formula"), "record")
            text(item["id"], "record identity", 96)
            constant(item["mt"])
            if item["id"] in seen:
                raise SliceError("INVALID_INPUT", "Repeated record identity")
            seen.add(item["id"])
            if item["strength"] not in ("monotonic", "default", "unknown"):
                raise SliceError("INVALID_INPUT", "Unknown source assertion strength")
            text(item["formula"], "formula", 2048)
            rows.append({**item, "byte_span": [offset, end],
                         "raw_line": line.decode(), "line_sha256": sha256(line).hexdigest()})
        offset = end
    if not rows:
        raise SliceError("INVALID_INPUT", "An identified source slice is required")
    return rows


def parse_formula(formula):
    """Parse a safe, finite s-expression; unsupported expressions remain residuals."""
    tokens, cursor = [], 0
    while cursor < len(formula):
        match = TOKEN.match(formula, cursor)
        if match is None:
            raise SliceError("UNSUPPORTED_SEMANTICS", "Unsupported token in Cyc-style source")
        token = match.group()
        if not token.isspace():
            tokens.append(token)
        cursor = match.end()
        if len(tokens) > 96:
            raise SliceError("RESOURCE_LIMIT", "Formula token budget exceeded")
    def read(index, depth=0):
        if depth > 6:
            raise SliceError("RESOURCE_LIMIT", "Formula depth exceeded")
        if index >= len(tokens):
            raise SliceError("INVALID_INPUT", "Truncated formula")
        token = tokens[index]
        if token == ")":
            raise SliceError("INVALID_INPUT", "Unmatched closing parenthesis")
        if token != "(":
            return token, index + 1
        out, index = [], index + 1
        while index < len(tokens) and tokens[index] != ")":
            value, index = read(index, depth + 1)
            out.append(value)
        if index == len(tokens):
            raise SliceError("INVALID_INPUT", "Unclosed formula")
        return out, index + 1
    tree, index = read(0)
    if index != len(tokens) or type(tree) is not list or not tree:
        raise SliceError("INVALID_INPUT", "Exactly one nonempty formula is required")
    positive = True
    def name(s):
        return s.removeprefix("#$") if type(s) is str else None
    if name(tree[0]) == "not":
        if len(tree) != 2 or type(tree[1]) is not list or not tree[1]:
            raise SliceError("INVALID_INPUT", "Malformed explicit negation")
        positive, tree = False, tree[1]
    pred, args = name(tree[0]), tree[1:]
    if pred in PRED:
        if len(args) != 2:
            raise SliceError("INVALID_INPUT", "Wrong structural arity")
        if any(type(a) is not str or not CONST.fullmatch(a) for a in args):
            raise SliceError("UNSUPPORTED_SEMANTICS", "Non-atomic terms are not silently flattened")
        if not positive and pred != "isa":
            raise SliceError("UNSUPPORTED_SEMANTICS", "Only negative isa is admitted in v1")
        return {"predicate": pred, "arguments": args, "positive": positive}
    if pred in ("argIsa", "arg1Isa", "arg2Isa", "arg3Isa", "arg4Isa"):
        if not positive:
            raise SliceError("UNSUPPORTED_SEMANTICS", "Negative argument constraints unsupported")
        if pred == "argIsa":
            if len(args) != 3 or type(args[1]) is not str or not re.fullmatch(r"[1-4]", args[1]):
                raise SliceError("UNSUPPORTED_SEMANTICS", "argIsa supports positions one through four")
            relation, position, kind = args[0], int(args[1]), args[2]
        else:
            if len(args) != 2:
                raise SliceError("INVALID_INPUT", "Wrong argument-constraint arity")
            relation, kind = args
            position = int(pred[3])
        if not all(type(a) is str and CONST.fullmatch(a) for a in (relation, kind)):
            raise SliceError("UNSUPPORTED_SEMANTICS", "Non-atomic argument constraint")
        return {"predicate": "argIsa", "arguments": [relation, position, kind], "positive": True}
    raise SliceError("UNSUPPORTED_SEMANTICS", "Predicate or logical constructor is outside v1")


def validate(request):
    fields(request, ("schema", "source", "ledger", "context", "query", "withdrawn", "bindings", "application"), "slice")
    if request["schema"] != SCHEMA:
        raise SliceError("INVALID_INPUT", "Unknown slice schema")
    fields(request["source"], ("id", "revision", "uri", "license", "sha256"), "source")
    for k in ("id", "revision", "uri", "license"):
        text(request["source"][k], "source " + k, 1024 if k in ("uri", "license") else 128)
    raw = text(request["ledger"], "ledger", MAX_LEDGER_BYTES)
    if request["source"]["sha256"] != sha256(raw).hexdigest():
        raise SliceError("SOURCE_MISMATCH", "Source digest differs from independent request bytes")
    constant(request["context"])
    fields(request["query"], ("predicate", "arguments", "positive"), "query")
    q = request["query"]
    if type(q["predicate"]) is not str or q["predicate"] not in PRED or type(q["positive"]) is not bool:
        raise SliceError("INVALID_INPUT", "Unsupported query kind or polarity")
    if type(q["arguments"]) is not list or len(q["arguments"]) != 2:
        raise SliceError("INVALID_INPUT", "Query has two ordered arguments")
    for a in q["arguments"]:
        constant(a)
    rows = records(request["ledger"])
    withdrawn = request["withdrawn"]
    if (type(withdrawn) is not list or any(type(x) is not str for x in withdrawn)
            or len(withdrawn) != len(set(withdrawn)) or not set(withdrawn) <= {r["id"] for r in rows}):
        raise SliceError("INVALID_INPUT", "Withdrawal must name existing distinct record IDs")
    if type(request["bindings"]) is not list or len(request["bindings"]) > 16:
        raise SliceError("INVALID_INPUT", "At most sixteen occurrence candidates")
    for binding in request["bindings"]:
        fields(binding, ("constant", "byte_span"), "binding candidate")
        constant(binding["constant"])
        span = binding["byte_span"]
        if type(span) is not list or len(span) != 2 or any(type(n) is not int for n in span) or not 0 <= span[0] < span[1]:
            raise SliceError("INVALID_INPUT", "Invalid occurrence byte span")
    app = request["application"]
    if app is not None:
        fields(app, ("predicate", "arguments"), "proposed application")
        constant(app["predicate"])
        if type(app["arguments"]) is not list or not 1 <= len(app["arguments"]) <= 4:
            raise SliceError("INVALID_INPUT", "Proposed application has one through four arguments")
        for a in app["arguments"]:
            constant(a)
    return deepcopy(request)


def atom(pred, left, right=None, positive=True):
    return {"predicate": pred, "arguments": [left] if right is None else [left, right], "positive": positive}


def compile_slice(request):
    p = validate(request)
    rows = records(p["ledger"])
    admitted, residuals, excluded, all_terms = [], [], [], set(p["query"]["arguments"])
    if p["application"]:
        all_terms.update([p["application"]["predicate"], *p["application"]["arguments"]])
    all_terms.update(b["constant"] for b in p["bindings"])
    for row in rows:
        # Preserve names from withdrawn/other-context records without using their facts.
        all_terms.update(re.findall(r"#\$[A-Za-z][A-Za-z0-9_-]*", row["formula"]))
        if row["id"] in p["withdrawn"] or row["mt"] != p["context"]:
            excluded.append({"id": row["id"], "reason": "WITHDRAWN" if row["id"] in p["withdrawn"] else "OTHER_CONTEXT"})
            continue
        if row["strength"] != "monotonic":
            residuals.append({"id": row["id"], "code": "DEFAULT_OR_UNKNOWN_STRENGTH_UNSUPPORTED"})
            continue
        try:
            parsed = parse_formula(row["formula"])
        except SliceError as exc:
            if exc.code != "UNSUPPORTED_SEMANTICS":
                raise
            residuals.append({"id": row["id"], "code": exc.code, "detail": str(exc)})
            continue
        admitted.append((row, parsed))
    if len(all_terms) > MAX_TERMS:
        raise SliceError("RESOURCE_LIMIT", "Term budget exceeded; no negative result inferred")
    names = sorted(all_terms)
    symbols = {term: f"t{i}" for i, term in enumerate(names)}
    base = {"schema": "nabt.opencyc-compiled.v1", "law": LAW, "request": p,
            "request_sha256": digest(p), "records": rows, "excluded": excluded,
            "residuals": residuals, "symbols": symbols, "clauses": [], "clause_origins": [],
            "argument_constraints": [], "status": "DEFER" if residuals else "COMPILED"}
    if residuals:
        return base
    clauses, origins, constraints = [], [], []
    def add(clause, origin):
        if len(clauses) >= MAX_CLAUSES:
            raise SliceError("RESOURCE_LIMIT", "Grounding budget exceeded; no partial acceptance")
        clauses.append(clause); origins.append(origin)
    def rule(head, body, source_id, operation):
        add({"kind": "rule", "body": body, "head": head}, {"record_id": source_id, "operation": operation})
    # A metadata marker permits an empty active slice without inventing domain facts.
    add({"kind": "fact", "atom": atom("oc_scope", "s0")}, {"operation": "METADATA_ONLY"})
    for row, parsed in admitted:
        pred, args = parsed["predicate"], parsed["arguments"]
        if pred == "argIsa":
            relation, position, kind = args
            slot = f"slot{symbols[relation][1:]}_{position}"
            fact = atom("oc_argIsa", slot, symbols[kind])
            constraints.append({"record_id": row["id"], "predicate": relation, "position": position, "kind": kind, "slot": slot})
        else:
            fact = atom(PRED[pred], *(symbols[a] for a in args), positive=parsed["positive"])
        add({"kind": "fact", "atom": fact}, {"record_id": row["id"], "operation": "SOURCE_ASSERTION"})
    for row, parsed in admitted:
        pred, args = parsed["predicate"], parsed["arguments"]
        if pred == "genls":
            a, b = map(symbols.__getitem__, args)
            for x in symbols.values():
                premise = atom("oc_genls", a, b)
                rule(atom("oc_isa", x, b), [atom("oc_isa", x, a), premise], row["id"], "INSTANCE_UPWARD")
                rule(atom("oc_isa", x, a, False), [atom("oc_isa", x, b, False), premise], row["id"], "EXCLUSION_DOWNWARD")
                rule(atom("oc_genls", x, b), [atom("oc_genls", x, a), premise], row["id"], "SUBTYPE_TRANSITIVE")
        if pred == "disjointWith":
            a, b = map(symbols.__getitem__, args)
            premise = atom("oc_disjoint", a, b)
            rule(atom("oc_disjoint", b, a), [premise], row["id"], "DISJOINT_SYMMETRY")
            for x in symbols.values():
                rule(atom("oc_isa", x, b, False), [atom("oc_isa", x, a), premise], row["id"], "DISJOINT_EXCLUSION")
                rule(atom("oc_isa", x, a, False), [atom("oc_isa", x, b), premise], row["id"], "DISJOINT_EXCLUSION")
    q = p["query"]
    goal = atom(PRED[q["predicate"]], *(symbols[a] for a in q["arguments"]), positive=q["positive"])
    base.update(clauses=clauses, clause_origins=origins, argument_constraints=constraints, goal=goal)
    return base


def _arabic_bindings(outer_text, p):
    from nabt import alphabet, codec
    from nabt.errors import NabtError
    raw = text(outer_text, "outer Arabic source", 8192)
    result = []
    for b in p["bindings"]:
        lo, hi = b["byte_span"]
        if hi > len(raw):
            raise SliceError("INVALID_INPUT", "Binding outside independent Arabic source")
        try:
            surface = raw[lo:hi].decode("utf-8", "strict")
        except UnicodeError as exc:
            raise SliceError("INVALID_INPUT", "Binding splits a UTF-8 scalar") from exc
        row = {**b, "surface": surface, "source_sha256": sha256(raw).hexdigest(),
               "status": "DEFER", "semantic_alignment_established": False}
        try:
            cells = alphabet.parse_word(surface)
            number = codec.encode_cells(cells)
            if codec.decode_number(number) != cells or alphabet.render_word(cells) != surface:
                raise SliceError("IDENTITY_FAILURE", "A116 reconstruction mismatch")
            row.update(status="DALI_IDENTITY_ONLY", alphabet_id=alphabet.ALPHABET_ID,
                       cells=list(cells), number_hex=hex(number), restored=surface)
        except NabtError as exc:
            row.update(status=exc.status, residual=exc.as_dict())
        result.append(row)
    return result


def _classification(a, certificate):
    def key(x):
        return x["predicate"], tuple(x["arguments"]), x["positive"]
    full = {key(x) for x in certificate["known"]}
    clean = {key(x) for x in certificate["clean_known"]}
    k = key(a); opposite = (k[0], k[1], not k[2])
    return ("CONFLICT" if k in full and opposite in full else "SUPPORTED" if k in clean else
            "REFUTED" if opposite in clean else "DEFER" if k in full or opposite in full else "UNKNOWN")


def _argument_report(compiled, certificate):
    app = compiled["request"]["application"]
    if app is None:
        return None
    rows = []
    for constraint in compiled["argument_constraints"]:
        if constraint["predicate"] != app["predicate"]:
            continue
        pos = constraint["position"]
        if pos > len(app["arguments"]):
            status, a = "MISSING_ARGUMENT", None
        else:
            a = atom("oc_isa", compiled["symbols"][app["arguments"][pos-1]], compiled["symbols"][constraint["kind"]])
            status = _classification(a, certificate)
        rows.append({**constraint, "status": status, "required_membership": a})
    return {"application": app, "requirements": rows,
            "status": "DECLARED_CONSTRAINTS_SUPPORTED" if rows and all(r["status"] == "SUPPORTED" for r in rows)
                      else "DEFER_ARGUMENT_OBLIGATIONS",
            "arity_completeness_established": False, "application_asserted": False,
            "action_authority": "NONE"}


def analyze(outer_text, source_id, request):
    """Internal owner adapter; the external consumer still must use the gateway."""
    c = compile_slice(request)
    p = c["request"]
    report = {"schema": RESULT, "law": LAW, "status": "DEFER", "native_checked": False,
              "outer_source_id": source_id, "outer_text_sha256": sha256(text(outer_text, "text", 8192)).hexdigest(),
              "compiled": c, "bindings": _arabic_bindings(outer_text, p),
              "native_receipt": None, "argument_check": None,
              "limits": dict(PUBLIC_LIMITS), "obligations": ["SOURCE_TRUTH_AND_EXTRACTION", "ARABIC_LEXICAL_ALIGNMENT", "SOURCE_LICENSE_REVIEW"]}
    if c["status"] != "COMPILED":
        report["reason"] = "SELECTED_SLICE_HAS_UNSUPPORTED_SEMANTICS"
        return report
    from tools import verified_reading as ground
    from tools import explainable_pilot as pilot
    program = "".join(ground.render_clause(x) for x in c["clauses"]).encode()
    query = ("هل " + ground.render_atom(c["goal"]) + "؟\n").encode()
    if len(program) > MAX_PROGRAM_BYTES:
        raise SliceError("RESOURCE_LIMIT", "Rendered program budget exceeded")
    identity, revision, scope = p["source"]["id"], p["source"]["revision"], p["context"]
    report.update(program=program.decode(), query=query.decode(), program_sha256=sha256(program).hexdigest())
    try:
        certificate = ground.propose(program, query, identity, revision, scope)
        report["proposal"] = certificate
        receipt, fingerprint = pilot.native(program, query, certificate, identity, revision, scope,
            ROOT / "formal/.lake/build/bin/verifiedReading", 15)
    except pilot.PilotError as exc:
        report.update(reason=exc.code, status="DEFER")
        return report
    # Only the existing native receipt permits a source-relative status.
    report.update(status=receipt["status"], native_checked=True, native_receipt=receipt,
                  checker_sha256=fingerprint, argument_check=_argument_report(c, certificate))
    report["explanation_ar"] = ("النتيجة تخص الإغلاق الموقّع للشريحة والسياق المحددين: " + receipt["status"]
        + ". لا تثبت حقيقة خارجية أو اقتران اللفظ العربي بالمفهوم؛ وقيود الأطراف لا تنشئ الواقعة.")
    return report
