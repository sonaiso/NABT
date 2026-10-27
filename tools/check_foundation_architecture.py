#!/usr/bin/env python3
"""Check registered admission boundaries and discover new public surfaces.

This checks executable guard placement, not just imports. Its static inventory
is complemented by sentinel/corruption tests: an import graph alone cannot
prove that a receipt passed a checker. Source projection completeness and
linguistic correctness remain separate obligations.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = Path("src/nabt/data/framework_foundation.json")
GRANT_FIELDS = frozenset({"native_checked", "certificate_checked", "verified",
    "grants_language_license", "reading_licensed", "readings_licensed",
    "language_certificate_granted", "world_truth_established",
    "strict_language_accepted", "certified_from_a116", "candidate_set_checked",
    "conditional_use_checked"})


class ArchitectureError(ValueError):
    pass


def definitions(tree, prefix=""):
    """Top-level functions and methods; nested implementation helpers excluded."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield prefix + node.name, node
        elif isinstance(node, ast.ClassDef):
            yield from definitions(node, prefix + node.name + ".")


def body_nodes(node):
    """Walk this function, without attributing a nested function's grants to it."""
    for item in node.body:
        yield item
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        yield from _children(item)


def _children(node):
    for child in ast.iter_child_nodes(node):
        yield child
        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield from _children(child)


def _constant_true(node):
    return isinstance(node, ast.Constant) and node.value is True


def grants_authority(node):
    """Detect literal-True grant writers, including dict.update calls.

    This is deliberately not a Python data-flow proof: computed Boolean grants
    and aliases may evade it. The separate source-module inventory forces review
    of every new module, including adapters with no main or literal-True grant.
    """
    for item in body_nodes(node):
        if isinstance(item, ast.keyword) and item.arg in GRANT_FIELDS and _constant_true(item.value):
            return True
        if isinstance(item, ast.Dict):
            if any(isinstance(k, ast.Constant) and k.value in GRANT_FIELDS and _constant_true(v)
                   for k, v in zip(item.keys, item.values)):
                return True
        if isinstance(item, ast.Assign) and _constant_true(item.value):
            if any(isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant)
                   and target.slice.value in GRANT_FIELDS for target in item.targets):
                return True
    return False


def _actual_guard(node, surface_id):
    statements = node.body
    if (statements and isinstance(statements[0], ast.Expr)
            and isinstance(statements[0].value, ast.Constant)
            and isinstance(statements[0].value.value, str)):
        statements = statements[1:]
    if not statements or not isinstance(statements[0], ast.Expr):
        return False
    call = statements[0].value
    return (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name) and call.func.value.id == "foundation"
            and call.func.attr == "require_foundation" and len(call.args) == 1
            and not call.keywords and isinstance(call.args[0], ast.Constant)
            and call.args[0].value == surface_id)


def validate_surface(row, root=ROOT):
    path = root / row["path"]
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    function = dict(definitions(tree)).get(row["entrypoint"])
    if function is None:
        raise ArchitectureError("Missing registered entry point: " + row["id"])
    kind = row["guard_kind"]
    if kind == "runtime_foundation":
        if not _actual_guard(function, row["id"]):
            raise ArchitectureError("Entry must begin with the live module guard: " + row["id"])
        imports_module = any(
            isinstance(n, ast.ImportFrom) and n.module == "nabt"
            and any(a.name == "foundation" and a.asname is None for a in n.names)
            for n in tree.body)
        if not imports_module:
            raise ArchitectureError("Guard must use the shared module, not a cached function alias: " + row["id"])
    elif kind == "intrinsic_domain_checks":
        if row["path"] != "src/nabt/codec.py":
            raise ArchitectureError("Unexpected intrinsic codec exception: " + row["id"])
        calls = {n.func.id for n in body_nodes(function) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name)}
        if not calls & {"validate_cells", "validate_cell", "natural", "decode_number"}:
            raise ArchitectureError("Intrinsic codec lost its domain check: " + row["id"])
    elif kind == "checked_snapshot_primitive":
        if row["path"] != "src/nabt/machine.py" or row["entrypoint"] not in {
                "Machine.transition", "Machine.final", "Machine.pot"}:
            raise ArchitectureError("Unexpected checked-snapshot exception: " + row["id"])
        calls = {n.func.id for n in body_nodes(function) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name)}
        if "_state" not in calls:
            raise ArchitectureError("Primitive lookup lost its state-domain check: " + row["id"])
        if not _actual_guard(dict(definitions(tree))["Machine.__init__"], "nabt.machine.machine.__init__"):
            raise ArchitectureError("Primitive snapshot has no checked constructor")
    else:
        raise ArchitectureError("Unknown guard classification: " + str(kind))
    if row["projection_completeness_established"] is not False:
        raise ArchitectureError("Identity registration cannot establish projection completeness")


def cli_commands(source):
    """Read argparse's actual calls, expanding literal command loops safely."""
    tree = ast.parse(source)
    parser = dict(definitions(tree))["parser"]
    found = []

    def walk(node, environment):
        if isinstance(node, ast.For):
            if not isinstance(node.target, ast.Name):
                raise ArchitectureError("CLI loop requires reviewed discovery support")
            try:
                values = ast.literal_eval(node.iter)
            except (ValueError, TypeError) as exc:
                raise ArchitectureError("Dynamic CLI registration is not inventoried") from exc
            for value in values:
                for child in node.body:
                    walk(child, {**environment, node.target.id: value})
            return
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_parser":
            if not node.args:
                raise ArchitectureError("CLI command lacks a name")
            value = node.args[0]
            name = value.value if isinstance(value, ast.Constant) else environment.get(value.id) if isinstance(value, ast.Name) else None
            if type(name) is not str:
                raise ArchitectureError("CLI command is not statically discoverable")
            found.append(name)
        for child in ast.iter_child_nodes(node):
            walk(child, environment)

    for node in parser.body:
        walk(node, {})
    if len(found) != len(set(found)):
        raise ArchitectureError("Duplicate CLI command")
    return sorted(found)


def python_sources(root):
    for folder in ("src/nabt", "tools", "integrations/grammar_db", "integrations/inference_db"):
        for path in sorted((root / folder).rglob("*.py")):
            if not any(part in {"tests", "__pycache__", "code_snapshot"} for part in path.parts):
                yield path


def discover(root, rows):
    source_modules, modules, public = [], [], []
    for path in python_sources(root):
        relative = path.relative_to(root).as_posix()
        source_modules.append(relative)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        funcs = dict(definitions(tree))
        if "main" in funcs or any(isinstance(n, ast.If) and "__name__" in ast.unparse(n.test) for n in tree.body):
            modules.append(relative)
        # Every public declaration is inventoried, including helpers in tools.
        # Inventory requires review; it does not classify every helper as an
        # admission or recursively guard Foundation's own bootstrap functions.
        public += [relative + ":" + name for name in funcs if not name.split(".")[-1].startswith("_")]
    workflow = (root / "tools/proof_lab.py").read_text(encoding="utf-8")
    modes = set()
    validate = dict(definitions(ast.parse(workflow)))["validate_payload"]
    for node in ast.walk(validate):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and node.left.id == "mode":
            for value in node.comparators:
                try:
                    value = ast.literal_eval(value)
                except (ValueError, TypeError):
                    continue
                modes.update([value] if type(value) is str else value)
    lake = (root / "formal/lakefile.lean").read_text(encoding="utf-8")
    worker = (root / "integrations/proof_lab/site/worker/server.mjs").read_text(encoding="utf-8")
    return {"cli_commands": cli_commands((root / "src/nabt/cli.py").read_text()),
        "console_scripts": tomllib.loads((root / "pyproject.toml").read_text())["project"]["scripts"],
        "lean_executables": sorted(re.findall(r"^lean_exe\s+(\w+)\s+where", lake, flags=re.M)),
        "proof_lab_modes": sorted(modes),
        "worker_api_routes": sorted(set(re.findall(r"url\.pathname\s*===\s*['\"]([^'\"]+)['\"]", worker))),
        "foundation_api": sorted(name for name, _ in definitions(ast.parse(
            (root / "src/nabt/foundation.py").read_text())) if not name.startswith("_")),
        "python_source_modules": sorted(source_modules),
        "python_entry_modules": sorted(modules), "public_python_api": sorted(public)}


def unregistered_grants(root, registry):
    registered = {(row["path"], row["entrypoint"]) for row in registry["surfaces"]}
    reviewed = {(row["path"], row["entrypoint"]) for row in registry["non_authority_grant_sites"]}
    failures = []
    for path in python_sources(root):
        relative = path.relative_to(root).as_posix()
        for name, node in definitions(ast.parse(path.read_text(encoding="utf-8"))):
            if grants_authority(node) and (relative, name) not in registered | reviewed:
                failures.append(relative + ":" + name)
    return sorted(failures)


def check(root=ROOT):
    registry = json.loads((root / REGISTRY).read_text(encoding="utf-8"))
    if registry.get("schema") != "nabt.framework-foundation.v1" or registry.get("foundation_law_id") != "nabt.foundation.v1":
        raise ArchitectureError("Unsupported foundation surface registry")
    rows = registry["surfaces"]
    if len({row["id"] for row in rows}) != len(rows):
        raise ArchitectureError("Duplicate surface ID")
    for row in rows:
        validate_surface(row, root)
    observed = discover(root, rows)
    for key, value in observed.items():
        if value != registry["discovery"].get(key):
            raise ArchitectureError("Public surface inventory changed; review and classify: " + key)
    unknown = unregistered_grants(root, registry)
    if unknown:
        raise ArchitectureError("Unregistered positive authority writer: " + ", ".join(unknown))
    return {"schema": "nabt.foundation-architecture-check.v1", "ok": True,
        "surfaces": len(rows), "guarded_surfaces": sum(row["guard_kind"] == "runtime_foundation" for row in rows),
        "cli_commands": len(observed["cli_commands"]), "lean_executables": len(observed["lean_executables"]),
        "projection_completeness_established": False, "whole_arabic_complete": False,
        "scope": "Installed identity boundaries and discovered entrypoints; dynamic denial tests remain required."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = check()
    except (ArchitectureError, OSError, ValueError, KeyError, SyntaxError) as exc:
        result = {"ok": False, "error": str(exc)}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
