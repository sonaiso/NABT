"""Bounded exact arithmetic proposal; the native reader independently replays it.

The source tree, operation tree, formal value and world claim are distinct.
No Python expression is evaluated. Fractions and all byte spans stay exact.
"""
from fractions import Fraction

MAX_BYTES = 2048
MAX_TOKENS = 63
MAX_DEPTH = 12
MAX_EXACT = 2**53 - 1
OPS = {"+": (10, "add"), "-": (10, "sub"), "*": (20, "mul"),
       "/": (20, "div"), "^": (30, "pow")}
ALIASES = {"×": "*", "÷": "/"}
REGISTRY = {"pos": 1, "neg": 2, "group": 3, "add": 10, "sub": 11,
            "mul": 12, "div": 13, "pow": 14, "equals": 20}


class CompositionError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def fail(code, message):
    raise CompositionError(code, message)


def tokens(text):
    raw = text.encode("utf-8", "strict")
    if not raw or len(raw) > MAX_BYTES:
        fail("RESOURCE_LIMIT" if raw else "DEFER", "Arithmetic source byte bound")
    offsets = [0]
    for char in text:
        offsets.append(offsets[-1] + len(char.encode()))
    rows, i = [], 0
    while i < len(text):
        if text[i] in " \t\n\r":
            i += 1
            continue
        start = i
        if "0" <= text[i] <= "9":
            while i < len(text) and "0" <= text[i] <= "9":
                i += 1
            value = text[start:i]
            if len(value) > 9:
                fail("RESOURCE_LIMIT", "Literal exceeds nine digits")
            if len(value) > 1 and value[0] == "0":
                fail("DEFER", "Leading zero is outside the canonical arithmetic profile")
            kind = "number"
        else:
            i += 1
            value = text[start:i]
            kind = ALIASES.get(value, value)
            if kind not in "+-*/^()=":
                fail("DEFER", "Unsupported arithmetic character")
        rows.append({"raw": value, "kind": kind, "span": [offsets[start], offsets[i]]})
        if len(rows) > MAX_TOKENS:
            fail("RESOURCE_LIMIT", "Arithmetic token bound")
    if not rows:
        fail("DEFER", "No arithmetic tokens")
    return rows


def node(op, span, operator_span, children=(), value=None):
    return {"op": op, "span": span, "operator_span": operator_span,
            "value": value, "children": list(children)}


def parse(rows):
    def expression(position, minimum, depth):
        if depth > MAX_DEPTH:
            fail("RESOURCE_LIMIT", "Arithmetic nesting bound")
        if position >= len(rows):
            fail("DEFER", "Missing arithmetic operand")
        token = rows[position]
        position += 1
        kind = token["kind"]
        if kind == "number":
            left = node("number", token["span"], token["span"], value=token["raw"])
        elif kind in ("+", "-"):
            child, position = expression(position, 25, depth + 1)
            left = node("pos" if kind == "+" else "neg",
                        [token["span"][0], child["span"][1]], token["span"], [child])
        elif kind == "(":
            child, position = expression(position, 0, depth + 1)
            if position >= len(rows) or rows[position]["kind"] != ")":
                fail("DEFER", "Unclosed arithmetic group")
            left = node("group", [token["span"][0], rows[position]["span"][1]], token["span"], [child])
            position += 1
        else:
            fail("DEFER", "Expected arithmetic operand")
        while position < len(rows) and rows[position]["kind"] in OPS:
            token = rows[position]
            precedence, op = OPS[token["kind"]]
            if precedence < minimum:
                break
            right, position = expression(position + 1, precedence if op == "pow" else precedence + 1, depth + 1)
            left = node(op, [left["span"][0], right["span"][1]], token["span"], [left, right])
        return left, position

    tree, position = expression(0, 0, 0)
    if position < len(rows) and rows[position]["kind"] == "=":
        token = rows[position]
        right, position = expression(position + 1, 0, 0)
        tree = node("equals", [tree["span"][0], right["span"][1]], token["span"], [tree, right])
    if position != len(rows):
        fail("DEFER", "Unconsumed arithmetic source")
    def height(n):
        return 1 + max((height(c) for c in n["children"]), default=0)
    if height(tree) > MAX_DEPTH:
        fail("RESOURCE_LIMIT", "Arithmetic tree height bound")
    return tree


def rational(value):
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def core_tree(tree):
    """Existing recursive-algebra constructors, with a declared operator table."""
    if tree["op"] == "number":
        return {"kind": "leaf", "seed": {"kind": "lexical", "entry": int(tree["value"])}}
    children = [core_tree(c) for c in tree["children"]]
    if len(children) == 1:
        return {"kind": "unary", "rule": REGISTRY[tree["op"]], "child": children[0]}
    return {"kind": "binary", "rule": REGISTRY[tree["op"]], "left": children[0], "right": children[1]}


def operation_tree(tree):
    if tree["op"] == "group":
        return operation_tree(tree["children"][0])
    return [tree["op"], tree["value"]] if tree["op"] == "number" else [tree["op"], *map(operation_tree, tree["children"])]


def evaluate_tree(tree):
    trace = []

    def visit(n):
        values = [visit(c) for c in n["children"]]
        op = n["op"]
        status, reason, value, truth = "COMPUTED", None, None, None
        failed = next((v for v in values if v["status"] != "COMPUTED"), None)
        if failed:
            status, reason = failed["status"], failed["reason"]
        else:
            args = [v["fraction"] for v in values]
            if op == "number": value = Fraction(int(n["value"]))
            elif op in ("group", "pos"): value = args[0]
            elif op == "neg": value = -args[0]
            elif op == "add": value = args[0] + args[1]
            elif op == "sub": value = args[0] - args[1]
            elif op == "mul": value = args[0] * args[1]
            elif op == "div":
                if args[1] == 0: status, reason = "BLOCKED", "DIVISION_BY_ZERO"
                else: value = args[0] / args[1]
            elif op == "pow":
                if args[1].denominator != 1 or args[1] < 0:
                    status, reason = "OUTSIDE_SCOPE", "NON_NATURAL_EXPONENT"
                elif args[1] > 12:
                    status, reason = "RESOURCE_LIMIT", "EXPONENT_BOUND"
                elif args[0] == 0 and args[1] == 0:
                    status, reason = "BLOCKED", "ZERO_TO_ZERO_EXCLUDED"
                else: value = args[0] ** int(args[1])
            elif op == "equals": truth = args[0] == args[1]
            if value is not None and (abs(value.numerator) > MAX_EXACT or value.denominator > MAX_EXACT):
                status, reason, value = "RESOURCE_LIMIT", "EXACT_VALUE_BOUND", None
        row = {"span": n["span"], "op": op, "status": status, "reason": reason,
               "value": None if value is None else rational(value), "truth": truth}
        trace.append(row)
        return {**row, "fraction": value}

    root = visit(tree)
    return {"sort": "proposition" if tree["op"] == "equals" else "quantity",
            **{k: root[k] for k in ("status", "reason", "value", "truth")}}, trace


def project(text):
    rows = tokens(text)
    tree = parse(rows)
    result, trace = evaluate_tree(tree)
    return {"tokens": rows, "tree": tree, "operation_tree": operation_tree(tree),
            "recursive_tree": core_tree(tree), "result": result, "trace": trace}


def paraphrase(tree):
    labels = {"add": "جمع", "sub": "طرح", "mul": "ضرب", "div": "قسمة",
              "pow": "أس", "neg": "سالب", "pos": "موجب", "equals": "مساواة"}
    if tree["op"] == "number": return tree["value"]
    if tree["op"] == "group": return paraphrase(tree["children"][0])
    return labels[tree["op"]] + "(" + "، ".join(paraphrase(c) for c in tree["children"]) + ")"
