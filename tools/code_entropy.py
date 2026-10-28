#!/usr/bin/env python3
"""Read-only, versioned static observations; entropy is not a quality score.

See docs/CODE_ENTROPY_CONTRACT.md. Inspected Python is parsed, never imported.
The graph_metrics helper also accepts other explicitly declared vertex sets.
"""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys


SCHEMA = "nabt.code-entropy.v1"
ROOT = Path(__file__).resolve().parents[1]
PREFIXES = ("src/nabt/", "tools/", "integrations/")


class AuditError(ValueError):
    """The declared measurement could not be completed."""


def graph_metrics(vertices, edges):
    """Measure a finite directed graph, retaining self edges in directed counts.

    Undirected cycle rank uses a simple projection: reciprocal edges collapse
    and self edges disappear. Unknown endpoints are errors, not extra vertices.
    """
    vertices = list(vertices)
    if any(type(vertex) is not str or not vertex for vertex in vertices):
        raise AuditError("graph vertices must be nonempty strings")
    vertices = sorted(set(vertices))
    edges = sorted(set(tuple(edge) for edge in edges))
    outgoing = {vertex: set() for vertex in vertices}
    incoming = {vertex: set() for vertex in vertices}
    for source, target in edges:
        if source not in outgoing or target not in outgoing:
            raise AuditError("edge endpoint outside the declared vertex population")
        outgoing[source].add(target)
        incoming[target].add(source)

    # Iterative Kosaraju: avoid a recursion limit on long synthetic chains.
    visited, finish = set(), []
    for start in vertices:
        if start in visited:
            continue
        visited.add(start)
        stack = [(start, iter(sorted(outgoing[start])))]
        while stack:
            vertex, children = stack[-1]
            child = next(children, None)
            if child is None:
                finish.append(vertex)
                stack.pop()
            elif child not in visited:
                visited.add(child)
                stack.append((child, iter(sorted(outgoing[child]))))

    def component(start, adjacency, seen):
        pending, members = [start], []
        seen.add(start)
        while pending:
            vertex = pending.pop()
            members.append(vertex)
            for child in sorted(adjacency[vertex], reverse=True):
                if child not in seen:
                    seen.add(child)
                    pending.append(child)
        return sorted(members)

    seen, strong = set(), []
    for vertex in reversed(finish):
        if vertex not in seen:
            strong.append(component(vertex, incoming, seen))
    undirected = {v: (outgoing[v] | incoming[v]) - {v} for v in vertices}
    seen, weak = set(), []
    for vertex in vertices:
        if vertex not in seen:
            weak.append(component(vertex, undirected, seen))
    simple_edges = {tuple(sorted((a, b))) for a, b in edges if a != b}
    edge_count = len(edges)
    degrees = [len(outgoing[v]) for v in vertices if outgoing[v]]
    probabilities = [degree / edge_count for degree in degrees]
    return {
        "vertex_count": len(vertices), "directed_edge_count": edge_count,
        "strong_components": sorted(strong), "strong_component_count": len(strong),
        "multi_node_strong_components": sorted(c for c in strong if len(c) > 1),
        "multi_node_strong_component_count": sum(len(c) > 1 for c in strong),
        "cyclic_components": sorted(c for c in strong
                                    if len(c) > 1 or c[0] in outgoing[c[0]]),
        "weak_components": sorted(weak), "weak_component_count": len(weak),
        "isolated_vertices": [v for v in vertices if not outgoing[v] and not incoming[v]],
        "isolated_vertex_count": sum(not outgoing[v] and not incoming[v] for v in vertices),
        "fan_in": {v: len(incoming[v]) for v in vertices},
        "fan_out": {v: len(outgoing[v]) for v in vertices},
        "max_in_degree": max((len(incoming[v]) for v in vertices), default=0),
        "max_out_degree": max(degrees, default=0),
        "max_in_edge_share": max((len(incoming[v]) for v in vertices), default=0) / edge_count
                             if edge_count else None,
        "max_out_edge_share": max(degrees, default=0) / edge_count if edge_count else None,
        "undirected_simple_edge_count": len(simple_edges),
        "undirected_cycle_rank": len(simple_edges) - len(vertices) + len(weak),
        "self_edge_count": sum(a == b for a, b in edges),
        "outdegree_entropy": {
            "distribution": "outgoing distinct directed edges / all distinct directed edges",
            "edge_denominator": edge_count, "positive_support": len(degrees),
            "bits": -math.fsum(p * math.log2(p) for p in probabilities) if edge_count else None,
            "interpretation": "descriptive only; neither direction implies better quality",
        },
    }


def _module(path):
    parts = list(PurePosixPath(path).with_suffix("").parts)
    if parts[0] == "src":
        parts.pop(0)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _location(path, node):
    return {"path": path, "line": node.lineno, "column": node.col_offset,
            "end_line": node.end_lineno, "end_column": node.end_col_offset}


def _call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return parent + "." + node.attr if parent else None
    return None


def audit_sources(sources, provenance=None):
    """Audit an explicit mapping of repository-relative source paths to bytes."""
    modules, trees, inventory = {}, {}, []
    for path, raw in sorted(sources.items()):
        if type(raw) is not bytes:
            raise AuditError("source contents must be bytes: " + path)
        if (not path.startswith(PREFIXES) or not path.endswith(".py")
                or "tests" in PurePosixPath(path).parts
                or PurePosixPath(path).as_posix() != path or ".." in PurePosixPath(path).parts):
            raise AuditError("path outside the declared production population: " + path)
        module = _module(path)
        if module in modules:
            raise AuditError("ambiguous module identity: " + module)
        modules[module] = path
        try:
            trees[module] = ast.parse(raw, filename=path)
        except (SyntaxError, UnicodeError, ValueError) as exc:
            raise AuditError("cannot parse " + path + ": " + str(exc)) from exc
        inventory.append({"path": path, "module": module,
                          "sha256": hashlib.sha256(raw).hexdigest(),
                          "bytes": len(raw), "physical_lines": len(raw.splitlines())})

    namespaces = {".".join(module.split(".")[:i]) for module in modules
                  for i in range(1, len(module.split(".")) + 1)}
    sites, unresolved, dynamic, clones = [], [], [], defaultdict(list)
    for module, path in sorted(modules.items()):
        tree = trees[module]
        body_ids = {id(node) for node in tree.body}
        aliases = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    aliases[alias.asname or alias.name.split(".")[0]] = (
                        alias.name if alias.asname else alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                for alias in node.names:
                    aliases[alias.asname or alias.name] = node.module + "." + alias.name

        for node in ast.walk(tree):
            location = _location(path, node) if hasattr(node, "lineno") else None
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                targets, missing = set(), []
                if isinstance(node, ast.Import):
                    requested = [alias.name for alias in node.names]
                    absolute_modules = requested
                    targets.update(name for name in requested if name in modules)
                    missing = [name for name in requested if name not in modules]
                else:
                    package = module.split(".") if path.endswith("/__init__.py") else module.split(".")[:-1]
                    requested = ["." * node.level + (node.module or "")]
                    absolute_modules = []
                    if node.level > len(package):
                        missing = requested
                    else:
                        prefix = package[:len(package) - node.level + 1] if node.level else []
                        base = ".".join(prefix + ([node.module] if node.module else []))
                        absolute_modules = [base]
                        if base in modules:
                            targets.add(base)
                        for alias in node.names:
                            candidate = base + "." + alias.name
                            if candidate in modules:
                                targets.add(candidate)
                            elif base not in modules:
                                missing.append(candidate if base in namespaces else base)
                site = {**location, "source": module,
                        "classification": "direct_module_body" if id(node) in body_ids else "nested",
                        "syntax": type(node).__name__, "requested": requested,
                        "absolute_modules": absolute_modules,
                        "imported_names": [alias.name for alias in node.names],
                        "targets": sorted(targets)}
                sites.append(site)
                for name in sorted(set(missing)):
                    unresolved.append({**location, "source": module, "name": name,
                                       "kind": "internal_or_namespace_unresolved" if
                                       name.split(".")[0] in namespaces else "external_or_unresolved"})
            elif isinstance(node, ast.Call):
                called = _call_name(node.func)
                if called:
                    first, *tail = called.split(".")
                    resolved = ".".join([aliases.get(first, first)] + tail)
                    if resolved in {"__import__", "builtins.__import__", "importlib.import_module",
                                    "importlib.util.spec_from_file_location", "importlib.util.spec_from_loader"}:
                        literal = node.args[0].value if node.args and isinstance(node.args[0], ast.Constant) else None
                        dynamic.append({**location, "source": module, "call": resolved,
                                        "literal_first_argument": literal if isinstance(literal, str) else None})
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.end_lineno - node.lineno + 1 >= 8:
                    signature = ast.dump(node, include_attributes=False)
                    clones[signature].append({**location, "name": node.name})

    sites.sort(key=lambda row: (row["path"], row["line"], row["column"]))
    all_edges = {(site["source"], target) for site in sites for target in site["targets"]}
    direct_edges = {(site["source"], target) for site in sites for target in site["targets"]
                    if site["classification"] == "direct_module_body"}
    violations = [{**site, "target": target, "target_in_population": target in modules}
                  for site in sites for target in sorted(set(site["targets"] + site["absolute_modules"]))
                  if site["path"].startswith("src/nabt/")
                  and target.split(".")[0] in {"tools", "integrations"}]
    groups = [{"ast_sha256": hashlib.sha256(signature.encode("utf-8")).hexdigest(),
               "occurrences": sorted(rows, key=lambda row: (row["path"], row["line"]))}
              for signature, rows in clones.items() if len(rows) > 1]
    groups.sort(key=lambda row: row["ast_sha256"])

    def projection(edges):
        layer = {module: "core" if path.startswith("src/nabt/") else path.split("/")[0]
                 for module, path in modules.items()}
        counts = {source + "->" + target: 0 for source in ("core", "tools", "integrations")
                  for target in ("core", "tools", "integrations")}
        for source, target in edges:
            counts[layer[source] + "->" + layer[target]] += 1
        return {"edges": [list(edge) for edge in sorted(edges)],
                "layer_edge_counts": counts, **graph_metrics(modules, edges)}

    return {
        "schema": SCHEMA, "provenance": provenance or {"kind": "explicit-source-mapping"},
        "method": {"source_path": "tools/code_entropy.py",
                   "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   "role": "measurement implementation provenance; not execution authority"},
        "parser": {"implementation": platform.python_implementation(),
                   "python_version": platform.python_version(), "method": "ast.parse; no imports"},
        "population": {"prefixes": list(PREFIXES), "suffix": ".py",
                       "excluded_path_component": "tests", "untracked_files": "excluded",
                       "file_count": len(inventory),
                       "physical_lines": sum(row["physical_lines"] for row in inventory)},
        "inventory": inventory, "import_sites": sites,
        "unresolved_or_external_imports": sorted(unresolved, key=lambda row: (row["path"], row["line"], row["name"])),
        "dynamic_import_sites": sorted(dynamic, key=lambda row: (row["path"], row["line"], row["column"])),
        "graphs": {
            "all_imports": projection(all_edges),
            "direct_module_body": projection(direct_edges),
        },
        "clone_candidates": {"method": "exact AST including names and docstrings; excluding locations",
                             "minimum_physical_span": 8, "group_count": len(groups),
                             "occurrence_count": sum(len(group["occurrences"]) for group in groups),
                             "groups": groups, "removable_lines": None},
        "boundary": {"rule": "core must not statically import tooling or integrations",
                     "unresolved_namespace_imports": "also prohibited; a missing target does not waive the boundary",
                     "passed": not violations, "violations": violations},
        "limitations": [
            "Static literal imports omit implicit package initialization, subprocess/native, data and dynamic execution dependencies.",
            "Direct module-body means an immediate AST child; imports inside conditionals, classes and functions are nested.",
            "ImportFrom adds an inventoried base module and inventoried member modules; attributes are not resolved.",
            "Dynamic-site detection recognizes named importlib loaders and __import__, including import aliases; alias scope/reassignment and arbitrary loaders are not analyzed.",
            "Source columns are zero-based UTF-8 byte offsets; line numbers are one-based.",
            "Self imports remain directed edges; undirected simple projections omit self edges.",
            "Clone spans may overlap; no removable-code total is inferred. Historical versions and independent oracles require separate review.",
            "Entropy and topology establish neither code quality, proof coverage, linguistic coverage nor execution authority.",
        ],
    }


def _git(root, *arguments):
    try:
        return subprocess.run(["git", "-C", str(root), *arguments], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise AuditError("Git inventory operation failed: " + str(exc)) from exc


def audit_repository(root=ROOT, ref=None):
    root = Path(root).resolve()
    commit = _git(root, "rev-parse", "--verify", "--end-of-options", (ref or "HEAD") + "^{commit}").decode().strip()
    if ref is None:
        names = _git(root, "ls-files", "-z").decode("utf-8").split("\0")[:-1]
    else:
        names = _git(root, "ls-tree", "-r", "-z", "--name-only", commit).decode("utf-8").split("\0")[:-1]
    selected = [name for name in names if name.startswith(PREFIXES) and name.endswith(".py")
                and "tests" not in PurePosixPath(name).parts]
    if len(set(selected)) != len(selected):
        raise AuditError("duplicate tracked paths, possibly an unresolved index conflict")
    sources = {}
    for name in sorted(selected):
        if ref is not None:
            mode = _git(root, "ls-tree", commit, "--", name).split(None, 1)[0]
            if mode not in {b"100644", b"100755"}:
                raise AuditError("source is not a regular Git blob: " + name)
            sources[name] = _git(root, "show", commit + ":" + name)
        else:
            path = root / name
            if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
                raise AuditError("tracked source is missing, nonregular or escaping: " + name)
            sources[name] = path.read_bytes()
    return audit_sources(sources, {
        "kind": "git-tree" if ref is not None else "working-tree-tracked", "commit": commit,
        "sources": "committed blobs" if ref is not None else "current working bytes",
        "consistency": "immutable blobs from one resolved commit" if ref is not None else
                       "sequential file reads; not an atomic working-tree snapshot",
    })


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", help="inspect committed Git-tree blobs instead of working tracked files")
    parser.add_argument("--output", type=Path, help="exclusively create the JSON report")
    parser.add_argument("--check", action="store_true", help="fail on static core-to-tooling/integration imports")
    args = parser.parse_args(argv)
    try:
        report = audit_repository(ref=args.ref)
        encoded = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(encoded)
            print(json.dumps({"schema": SCHEMA, "files": report["population"]["file_count"],
                              "boundary_passed": report["boundary"]["passed"], "output": str(args.output)}))
        else:
            print(encoded, end="")
        return 1 if args.check and not report["boundary"]["passed"] else 0
    except (AuditError, OSError, UnicodeError) as exc:
        print("code entropy audit failed: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
