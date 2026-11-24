"""Mask scalar expectations in historical, public unit tests. No test code is executed."""

import ast
from functools import lru_cache

from .cumulative_history import ZERO, canonical, digest, git


def literal(node):
    try:
        x = ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return None
    return x if type(x) in (str, bool, int) and len(str(x)) <= 72 else None


def query(call):
    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
        return None
    kind = call.func.attr
    if kind in ("assertTrue", "assertFalse") and len(call.args) == 1:
        return call.args[0], kind == "assertTrue"
    if kind == "assertEqual" and len(call.args) == 2:
        left, right = call.args
        if literal(right) is None and literal(left) is not None:
            left, right = right, left
        gold = literal(right)
        if gold is not None and literal(left) is None:
            return left, gold
    return None


@lru_cache(maxsize=1024)
def records(blob):
    if blob == ZERO:
        return {}
    tree = ast.parse(git("cat-file", "blob", blob))
    rows = {}
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        for method in cls.body:
            if not isinstance(method, ast.FunctionDef) or not method.name.startswith("test_"):
                continue
            context = []
            for stmt in method.body:
                if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                    continue
                if isinstance(stmt, ast.Assign):
                    if any(
                        isinstance(
                            n,
                            (ast.Lambda, ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp),
                        )
                        for n in ast.walk(stmt)
                    ):
                        break
                    context.append(stmt)
                    continue
                if not isinstance(stmt, ast.Expr):
                    break
                if isinstance(stmt.value, ast.Constant):
                    continue
                if not (
                    isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Attribute)
                    and stmt.value.func.attr.startswith("assert")
                ):
                    break
                pair = query(stmt.value)
                if not pair:
                    continue
                expression, answer = pair
                if isinstance(expression, (ast.Dict, ast.List, ast.Tuple, ast.NameConstant)):
                    continue
                # Resolve only assignments transitively relevant to this query.
                used = {n.id for n in ast.walk(expression) if isinstance(n, ast.Name)}
                setup = []
                for assignment in reversed(context):
                    names = {
                        n.id
                        for t in assignment.targets
                        for n in ast.walk(t)
                        if isinstance(n, ast.Name)
                    }
                    if names & used:
                        setup.append(assignment)
                        used -= names
                        used.update(
                            n.id for n in ast.walk(assignment.value) if isinstance(n, ast.Name)
                        )
                sequence = [*reversed(setup), expression]
                if any(
                    type(n.value) is type(answer) and n.value == answer
                    for st in sequence
                    for n in ast.walk(st)
                    if isinstance(n, ast.Constant)
                ):
                    continue
                text = "\n".join(ast.unparse(st) for st in sequence)
                if (
                    len(text.encode()) > 1024
                    or len(text.strip()) < 5
                    or isinstance(expression, ast.Name)
                    and not setup
                ):
                    continue
                label = canonical(answer)
                if type(answer) is bool:
                    task = "contract_query:boolean"
                elif (
                    isinstance(expression, ast.Subscript)
                    and isinstance(expression.slice, ast.Constant)
                    and isinstance(expression.slice.value, str)
                ):
                    task = "contract_query:field:" + expression.slice.value
                elif isinstance(expression, ast.Attribute):
                    task = "contract_query:field:" + expression.attr
                else:
                    continue
                # The grouping key never enters the model. Keep every version of a
                # method together even when multiple PRs modify its setup.
                method_id = cls.name + "." + method.name
                rows[method_id, task, text, label] = stmt.lineno
    return rows


def episodes(history):
    for record in history["pull_requests"]:
        pr = record["pr"]
        for path, old, new, _ in history["changes"][str(pr)]:
            if not path.startswith("tests/") or not path.endswith(".py"):
                continue
            previous, current = records(old), records(new)
            for key in sorted(current.keys() - previous.keys()):
                method, task, text, gold = key
                group = path + "::" + method
                is_test = int(digest(group.encode()), 16) % 5 == 0
                yield {
                    "pr": pr,
                    "task": task,
                    "text": text,
                    "gold": gold,
                    "split": "test" if is_test else "train",
                    "source": new + ":" + group,
                    "lane": "masked_public_contract",
                }
