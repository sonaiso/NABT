"""Recover PR-specific changed paths, tests and bounded literal behavioral questions."""
import ast
from collections import Counter
from functools import lru_cache
import gzip
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from tools.entropy_framework.reuse import build_reuse_report
from tools.repo_agent.manager import path_owners

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "evidence/cumulative_outcomes_v1"
ZERO = "0" * 40


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(data):
    return sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def field_name(expr, imports):
    if isinstance(expr, ast.Name):
        return imports.get(expr.id)
    if isinstance(expr, ast.Attribute):
        parent = field_name(expr.value, imports)
        if parent:
            return parent + "." + expr.attr
    return None


def literal(node, bindings):
    if isinstance(node, ast.Name) and node.id in bindings:
        node = bindings[node.id]
    return ast.literal_eval(node)


def example(expr, imports, bindings):
    fields = []
    while isinstance(expr, ast.Subscript):
        fields.append(literal(expr.slice, {}))
        expr = expr.value
    if isinstance(expr, ast.Name):
        expr = bindings.get(expr.id)
    if not isinstance(expr, ast.Call):
        return None
    fn = field_name(expr.func, imports)
    if not fn or not fn.startswith(("tools.", "nabt.")) or not (expr.args or expr.keywords):
        return None
    if any(k.arg is None for k in expr.keywords):
        return None
    args = [literal(a, bindings) for a in expr.args]
    kwargs = {k.arg: literal(k.value, bindings) for k in expr.keywords}
    text = canonical([args, kwargs])
    if len(text.encode()) > 512 or not all(type(f) in (str, int) for f in fields):
        return None
    return "call:" + fn + ":" + canonical(fields[::-1]), text


def imports_at(body):
    result = {}
    for n in body:
        if isinstance(n, ast.Import):
            for a in n.names:
                result[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
        if isinstance(n, ast.ImportFrom) and n.module and not n.level:
            for a in n.names:
                result[a.asname or a.name] = n.module + "." + a.name
    return result


@lru_cache(maxsize=1024)
def tests(blob):
    if blob == ZERO:
        return {}
    module = ast.parse(git("cat-file", "blob", blob))
    result = {}
    for cls in [n for n in module.body if isinstance(n, ast.ClassDef)]:
        for method in cls.body:
            if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) or not method.name.startswith("test_"):
                continue
            key = cls.name + "." + method.name
            probes = []
            result[key] = digest(ast.dump(method).encode()), probes
            if method.decorator_list or cls.decorator_list:
                continue
            imports = {**imports_at(module.body), **imports_at(method.body)}
            bindings = {}
            for stmt in method.body:
                # Branches, context managers and setup side effects are not closed examples.
                if isinstance(stmt, (ast.ImportFrom, ast.Import)):
                    continue
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                    bindings[stmt.targets[0].id] = stmt.value
                    continue
                if not isinstance(stmt, ast.Expr):
                    break
                call = stmt.value
                if not isinstance(call, ast.Call):
                    continue
                fn = call.func
                if not isinstance(fn, ast.Attribute) or not isinstance(fn.value, ast.Name) or fn.value.id != "self":
                    break
                try:
                    if fn.attr == "assertEqual" and len(call.args) == 2:
                        left, right = call.args
                        target = literal(right, bindings)
                    elif fn.attr in ("assertTrue", "assertFalse") and len(call.args) == 1:
                        left, target = call.args[0], fn.attr == "assertTrue"
                    else:
                        continue
                    if type(target) not in (int, str, bool) or len(str(target)) > 96:
                        continue
                    x = example(left, imports, bindings)
                    if x:
                        probes.append((*x, canonical(target)))
                except (ValueError, TypeError, KeyError, SyntaxError, OverflowError):
                    continue
    return result


def collect():
    pulls = json.loads((DATA / "pulls.json").read_bytes())
    if [p["number"] for p in pulls] != list(range(1, 144)):
        raise ValueError("Incomplete PR range")
    families = build_reuse_report(ROOT)["families"]
    paths, report, rows = {}, [], []
    for p in pulls:
        if git("merge-base", p["base"], p["head"]).decode().strip() != p["merge_base"]:
            raise ValueError(f"PR {p['number']} base changed")
        chunks = git("diff", "--raw", "--no-renames", "--no-abbrev", "-z", p["merge_base"], p["head"]).split(b"\0")
        changes, touched = [], []
        before_count = len(rows)
        for meta, path_bytes in zip(chunks[:-1:2], chunks[1::2], strict=True):
            path = path_bytes.decode()
            _, _, old, new, status = meta.decode().split()
            changes.append([path, old, new, status])
            if path.startswith("tests/") and path.endswith(".py"):
                old_tests, new_tests = tests(old), tests(new)
                for name in sorted(set(old_tests) | set(new_tests)):
                    prior, after = old_tests.get(name), new_tests.get(name)
                    if prior == after:
                        continue
                    touched.append(path + "::" + name)
                    if after:
                        prior_rows = set(prior[1]) if prior else set()
                        for task, text, target in sorted(set(after[1]) - prior_rows):
                            rows.append({"pr": p["number"], "task": task, "text": text, "gold": target,
                                "blob": new, "source": path + "::" + name})
        owners, _ = path_owners([r[0] for r in changes], families)
        report.append({"pr": p["number"], "files": len(changes), "touched_tests": touched,
                       "registered_families": sorted({f for fs in owners.values() for f in fs}),
                       "unmapped_paths": sum(not fs for fs in owners.values()), "new_literal_claims": len(rows)-before_count})
        paths[str(p["number"])] = changes
    return {"schema": "nabt.cumulative-history.v1", "rows": rows, "pull_requests": report, "changes": paths}


def snapshot():
    return json.loads(gzip.decompress((DATA / "history.json.gz").read_bytes()))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = collect()
    args.output.write_bytes(gzip.compress(canonical(data).encode(), mtime=0))
    print(len(data["pull_requests"]), len(data["rows"]), len({r["task"] for r in data["rows"]}))
