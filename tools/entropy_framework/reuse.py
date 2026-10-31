"""Resolve existing NABT capabilities from its current compiled proof catalogue.

This is a read-only use map, not a theorem registry or an inference engine.
Declaration identities come only from the existing current-proof selector.
Authored routes say where a contract is intended to be used; static imports,
compiled proof dependencies and a separately executed receipt are different
relations. Merely finding a binary or a test never reports that it was run.
"""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path, PurePosixPath
import re

from tools import code_entropy, proof_catalog
from .registry import FrameworkError, load_json


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "nabt.proof-reuse-report.v1"
ROUTE_SCHEMA = "nabt.proof-reuse.v1"
SELECTOR = "integrations/current_proof_references.mk"
REGISTRY = "tools/entropy_framework/registry.json"
MODULE_PATTERN = re.compile(r"Nabt(?:\.[A-Za-z_][A-Za-z0-9_]*)+")
FAMILY_FIELDS = {
    "id", "title_ar", "formal_modules", "runtime_paths", "native_targets",
    "entrypoint_ids", "checker_paths", "test_paths", "doc_paths", "scope", "open_debts",
}
PATH_FIELDS = ("runtime_paths", "checker_paths", "test_paths", "doc_paths")


def _require(condition, message):
    if not condition:
        raise FrameworkError("proof reuse: " + message)


def _text(value, label):
    _require(type(value) is str and bool(value.strip()), label + " needs nonempty text")
    return value


def _strings(value, label, *, nonempty=False):
    _require(type(value) is list, label + " needs a list")
    _require(not nonempty or bool(value), label + " must not be empty")
    for item in value:
        _text(item, label)
    _require(len(set(value)) == len(value), label + " has duplicate entries")
    return value


def _file(root, relative):
    _text(relative, "path")
    path = PurePosixPath(relative)
    _require(not path.is_absolute() and path.as_posix() == relative
             and all(part not in (".", "..") for part in path.parts)
             and "\\" not in relative, "noncanonical repository path: " + relative)
    full = root / relative
    _require(full.is_file() and full.resolve().is_relative_to(root),
             "missing or escaped file: " + relative)
    _require(not any(parent.is_symlink() for parent in [full, *full.parents]
                     if parent != root and parent.is_relative_to(root)),
             "symlink is not a source identity: " + relative)
    return full


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _read(root, relative, inputs):
    raw = _file(root, relative).read_bytes()
    inputs[relative] = _sha(raw)
    return raw


def current_catalog(root=ROOT):
    """Check the installed historical compiled snapshot against current inputs.

    This does not claim a new Lean compilation. The existing proof-catalogue
    and axiom-audit commands remain responsible for compiled verification.
    """
    root = Path(root).resolve()
    inputs = {}
    selector = _read(root, SELECTOR, inputs).decode("utf-8")
    assignments = re.findall(
        r"^\s*(?:(?:override|export|private|define|undefine)\s+)*NABT_PROOF_REFERENCE_DIR\b[^\n]*$",
        selector, re.M)
    selected = re.findall(r"^NABT_PROOF_REFERENCE_DIR\s*\?=\s*(\S+)\s*$", selector, re.M)
    _require(len(selected) == 1 and len(assignments) == 1,
             "current proof selector must have exactly one unoverridden literal default")
    relative = selected[0] + "/proof_catalog.json"
    _read(root, relative, inputs)
    catalog = load_json(_file(root, relative))
    _require(type(catalog) is dict and catalog.get("schema") == proof_catalog.SCHEMA,
             "unsupported compiled catalogue schema")
    _require(catalog.get("authority") == "COMPILED_DECLARATION_INDEX_ONLY",
             "compiled catalogue has an unexpected authority claim")
    references = catalog.get("inputs")
    _require(type(references) is dict and bool(references), "catalogue inputs missing")
    for path, expected in references.items():
        _require(type(expected) is str and re.fullmatch(r"[0-9a-f]{64}", expected),
                 "invalid source fingerprint: " + str(path))
        actual = _sha(_read(root, path, inputs))
        _require(actual == expected, "stale compiled catalogue input: " + path)
    formal_files = {path.relative_to(root).as_posix()
                    for path in (root / "formal").rglob("*.lean")
                    if ".lake" not in path.relative_to(root / "formal").parts}
    _require(formal_files == {path for path in references if path.endswith(".lean")},
             "compiled catalogue does not account for every current Lean source")
    for required in ("formal/theorems.json", "formal/lean-toolchain", "tools/proof_catalog.py"):
        _require(required in references, "compiled catalogue omits required input: " + required)
    manifest = load_json(_file(root, "formal/theorems.json"))
    _require(type(manifest) is dict, "malformed theorem manifest")
    names = _strings(manifest.get("theorems"), "theorem manifest", nonempty=True)
    declarations = catalog.get("theorems")
    _require(type(declarations) is list and all(type(row) is dict for row in declarations),
             "compiled declaration list missing")
    _require([row.get("name") for row in declarations] == names,
             "compiled declaration names differ from the exact current manifest")
    module_paths = {"Nabt." + path.relative_to(root / "formal/Nabt").with_suffix("").as_posix().replace("/", "."):
                    path.relative_to(root).as_posix()
                    for path in (root / "formal/Nabt").rglob("*.lean")}
    _require(bool(module_paths), "no formal NABT modules")
    # Reuse the source-link checker's exact manifest, canonical statement,
    # universe, axiom and current-input checks instead of inventing a second
    # definition of a valid recorded compiled catalogue.
    from tools.check_sourced_acquisition_links import LinkError, _validate_compiled
    try:
        _validate_compiled(root, catalog)
    except LinkError as error:
        raise FrameworkError("proof reuse: " + str(error)) from error
    _require(all(row["module"] in module_paths for row in declarations),
             "declaration module is not a current NABT source")
    observed = {
        "advertised_declarations": len(declarations),
        "normalized_statement_groups": len({row["statement_sha256"] for row in declarations}),
    }
    counts = catalog.get("counts")
    _require(type(counts) is dict, "catalogue counts missing")
    for field, value in observed.items():
        _require(type(counts.get(field)) is int and counts[field] == value,
                 "catalogue count differs from its declaration population: " + field)
    return catalog, relative, module_paths, inputs


def _native_targets(root, inputs):
    text = _read(root, "formal/lakefile.lean", inputs).decode("utf-8")
    rows = re.findall(r"^lean_exe\s+(\w+)\s+where\s*\n\s*root\s*:=\s*`([\w.]+)", text, re.M)
    _require(len(rows) == len(set(name for name, _ in rows)), "duplicate native target")
    _require(len(rows) == len(re.findall(r"^lean_exe\s+", text, re.M)),
             "unsupported native target declaration; update explicit parser")
    for _, module in rows:
        _read(root, "formal/" + module.replace(".", "/") + ".lean", inputs)
    return dict(rows)


def _entrypoints(root, native_targets, inputs):
    from .reuse_run import describe_entries

    entries = describe_entries()
    _require(type(entries) is dict and bool(entries), "installed entrypoint allowlist is empty")
    resolved = {}
    for identity, description in entries.items():
        _text(identity, "entrypoint identity")
        _require(type(description) is dict, "invalid installed entrypoint descriptor")
        module, native = description.get("module"), description.get("native_target")
        _require((module is None) != (native is None),
                 "entrypoint must select exactly one existing Python module or native target")
        if module is not None:
            _require(type(module) is str and re.fullmatch(r"[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*", module),
                     "invalid installed entrypoint module")
            _require(module == "nabt" or module.startswith(("nabt.", "tools.")),
                     "entrypoint module outside installed NABT/tooling namespaces")
            stem = ("src/" if module == "nabt" or module.startswith("nabt.") else "") + module.replace(".", "/")
            candidates = [path for path in (stem + ".py", stem + "/__main__.py") if (root / path).is_file()]
            _require(len(candidates) == 1, "missing or ambiguous local entrypoint module: " + module)
            source = candidates[0]
        else:
            _require(type(native) is str and native in native_targets,
                     "entrypoint selects an undeclared native target")
            source = "formal/" + native_targets[native].replace(".", "/") + ".lean"
        _read(root, source, inputs)
        resolved[identity] = {**description, "entry_source_path": source,
                              "entry_source_sha256": inputs[source]}
    return resolved


def validate_routes(reuse, module_paths, native_targets, entries, root=ROOT):
    """Validate authored availability metadata; it supplies no execution status."""
    root = Path(root).resolve()
    _require(type(reuse) is dict and set(reuse) == {"schema", "families"}
             and reuse.get("schema") == ROUTE_SCHEMA, "invalid reuse registry fields or schema")
    families = reuse["families"]
    _require(type(families) is list and bool(families), "no reuse families")
    seen_ids, assigned = set(), []
    for family in families:
        _require(type(family) is dict and set(family) == FAMILY_FIELDS,
                 "invalid family fields; status/authority are not route inputs")
        identity = _text(family["id"], "family id")
        _require(re.fullmatch(r"[a-z][a-z0-9-]*", identity) and identity not in seen_ids,
                 "invalid or duplicate family id: " + identity)
        seen_ids.add(identity)
        for field in ("title_ar", "scope"):
            _text(family[field], identity + "." + field)
        modules = _strings(family["formal_modules"], identity + ".formal_modules", nonempty=True)
        _require(all(MODULE_PATTERN.fullmatch(module) and module in module_paths for module in modules),
                 "unknown formal module in " + identity)
        assigned.extend(modules)
        for field in PATH_FIELDS:
            for path in _strings(family[field], identity + "." + field):
                _file(root, path)
        for field, available in (("native_targets", native_targets), ("entrypoint_ids", entries)):
            listed = _strings(family[field], identity + "." + field)
            _require(set(listed) <= set(available), "unknown " + field + " in " + identity)
        _strings(family["open_debts"], identity + ".open_debts")
        _require(bool(family["runtime_paths"] or family["native_targets"] or family["open_debts"]),
                 "unconsumed family needs an explicit open debt: " + identity)
    duplicates = sorted(module for module, count in Counter(assigned).items() if count != 1)
    _require(not duplicates, "formal modules assigned more than once: " + ", ".join(duplicates))
    missing = sorted(set(module_paths) - set(assigned))
    _require(not missing, "unmapped formal modules: " + ", ".join(missing))
    return families


def _lean_imports(root, module_paths, inputs):
    edges = []
    for module, path in sorted(module_paths.items()):
        text = _read(root, path, inputs).decode("utf-8")
        # NABT uses one literal import per line. Reject an unparsed import so a
        # syntax extension cannot silently remove a dependency from this view.
        lines = [line for line in text.splitlines() if line.startswith("import ")]
        for line in lines:
            match = re.fullmatch(r"import\s+([\w.]+)\s*(?:--.*)?", line)
            _require(match is not None, "unsupported import syntax in " + path)
            target = match.group(1)
            edges.append({"from": module, "to": target,
                          "kind": "LEAN_MODULE_IMPORT",
                          "target_in_nabt_module_population": target in module_paths})
    return edges


def _static_imports(root, families, inputs):
    paths = sorted({path for family in families
                    for field in ("runtime_paths", "checker_paths")
                    for path in family[field] if path.endswith(".py")})
    sources = {path: _read(root, path, inputs) for path in paths}
    try:
        audit = code_entropy.audit_sources(sources, provenance={
            "kind": "explicit-authored-reuse-path-population",
            "runtime_execution_performed": False,
        })
    except code_entropy.AuditError as error:
        raise FrameworkError("proof reuse static imports: " + str(error)) from error
    return {
        "method": audit["method"],
        "population": [row["path"] for row in audit["inventory"]],
        "edges": [{"from": source, "to": target, "kind": "STATIC_PYTHON_IMPORT"}
                  for source, target in audit["graphs"]["all_imports"]["edges"]],
        "sites": audit["import_sites"],
        "unresolved_or_external": audit["unresolved_or_external_imports"],
        "dynamic_sites": audit["dynamic_import_sites"],
        "limitations": audit["limitations"],
    }


def _declaration_source(root, row):
    # Reuse the existing source-link checker's reviewed header extractor.
    # It deliberately supports less than all Lean syntax. Unsupported headers
    # retain their exact compiled source range for inspection, without guessing.
    from tools.check_sourced_acquisition_links import LinkError, _statement_header

    try:
        return {"status": "EXACT_SOURCE_HEADER", **_statement_header(root, row),
                "scope": "Source header, not a new elaborated type; inherited section parameters remain in the linked module."}
    except LinkError:
        where = row.get("range")
        _require(type(where) is dict, "compiled source range missing: " + row["name"])
        first, last = where.get("line"), where.get("end_line")
        lines = _file(root, row["source_path"]).read_text(encoding="utf-8").splitlines(keepends=True)
        _require(type(first) is int and type(last) is int and 1 <= first <= last <= len(lines),
                 "invalid compiled declaration range: " + row["name"])
        excerpt = "".join(lines[first - 1:last])
        return {"status": "EXACT_SOURCE_RANGE_HEADER_EXTRACTOR_NOT_APPLICABLE",
                "source_excerpt": excerpt, "source_excerpt_sha256": _sha(excerpt.encode()),
                "scope": "Complete compiled line range, possibly including documentation and proof. No inferred premise list."}


def build_reuse_report(root=ROOT, *, registry=None, family=None, module=None):
    """Resolve all contracts before narrowing a view to a family or module."""
    root = Path(root).resolve()
    catalog, relative, module_paths, inputs = current_catalog(root)
    if registry is None:
        _read(root, REGISTRY, inputs)
        registry = load_json(_file(root, REGISTRY))
        route_origin = "INSTALLED_REGISTRY"
    else:
        route_origin = "EXPLICIT_METADATA_ONLY"
    _require(type(registry) is dict, "registry must be an object")
    native_targets = _native_targets(root, inputs)
    entries = _entrypoints(root, native_targets, inputs)
    families = validate_routes(registry.get("reuse"), module_paths, native_targets, entries, root)
    _require(family is None or module is None, "choose either a family or a module")
    if family is not None:
        _require(family in {row["id"] for row in families}, "unknown family: " + str(family))
    if module is not None:
        _require(module in module_paths, "unknown module: " + str(module))
    selected_families = [row for row in families if
                         (family is None or family == row["id"]) and
                         (module is None or module in row["formal_modules"])]
    selected_modules = ({module} if module is not None else
                        {name for row in selected_families for name in row["formal_modules"]})
    all_imports = _lean_imports(root, module_paths, inputs)
    static = _static_imports(root, families, inputs)
    for route in families:
        for field in PATH_FIELDS:
            for path in route[field]:
                _read(root, path, inputs)
    for own in ("tools/entropy_framework/reuse.py", "tools/entropy_framework/reuse_run.py",
                "tools/entropy_framework/__main__.py", "tools/code_entropy.py",
                "tools/check_sourced_acquisition_links.py"):
        _read(root, own, inputs)
    declared_edges, family_rows = [], []
    for route in selected_families:
        availability = []
        for target in route["native_targets"]:
            binary = root / "formal/.lake/build/bin" / target
            availability.append({"target": target, "root_module": native_targets[target],
                                 "binary_present": binary.is_file(),
                                 "execution_status": "NOT_RUN_BY_REUSE_REPORT"})
        family_rows.append({**route, "native_availability": availability,
                            "entrypoints": {key: entries[key] for key in route["entrypoint_ids"]},
                            "route_status": "AUTHORED_REFERENCES_RESOLVED",
                            "runtime_execution_performed": False})
        family_node = "family:" + route["id"]
        declared_edges.extend({"from": source, "to": family_node,
                               "kind": "AUTHORED_FAMILY_MEMBERSHIP"}
                              for source in route["formal_modules"] if source in selected_modules)
        for field, kind in (("runtime_paths", "AUTHORED_OPERATIONAL_ROUTE"),
                            ("checker_paths", "AUTHORED_CHECKER_REFERENCE"),
                            ("test_paths", "AUTHORED_TEST_REFERENCE"),
                            ("native_targets", "AUTHORED_NATIVE_ROUTE"),
                            ("entrypoint_ids", "AUTHORED_ENTRYPOINT_ROUTE")):
            declared_edges.extend({"from": family_node, "to": target, "kind": kind,
                                   "scope": "Shared family route; not a verified call from every member module."}
                                  for target in route[field])
    by_module = {name: [] for name in module_paths}
    for row in catalog["theorems"]:
        by_module[row["module"]].append(row)
    modules = []
    for name in sorted(selected_modules):
        declarations = by_module[name]
        owner = next(row["id"] for row in families if name in row["formal_modules"])
        modules.append({
            "module": name, "family": owner, "source_path": module_paths[name],
            "source_sha256": inputs[module_paths[name]],
            "role": "COMPILED_THEOREM_MODULE" if declarations else "FORMAL_DATA_OR_DEFINITION_MODULE",
            "declaration_count": len(declarations),
            "declarations": [{**{key: row[key] for key in
                              ("name", "canonical_name", "statement_sha256", "range", "axioms")},
                              "source_statement": _declaration_source(root, row)}
                             for row in declarations],
        })
    declarations = [row for row in catalog["theorems"] if row["module"] in selected_modules]
    return {
        "schema": SCHEMA,
        "authority": "REUSE_NAVIGATION_ONLY",
        "semantic_authority": "NONE",
        "catalogue": {
            "path": relative, "sha256": inputs[relative],
            "selector_policy": "INSTALLED_LITERAL_DEFAULT; Make/environment overrides are not inferred",
            "typed_content_sha256": proof_catalog.digest(catalog),
            "source_inputs_match": True,
            "verification": "RECORDED_COMPILED_SNAPSHOT_WITH_CURRENT_SOURCE_MATCH",
            "compiled_this_run": False,
        },
        "routing_origin": route_origin,
        "routing_metadata_sha256": proof_catalog.digest(registry["reuse"]),
        "population": {
            "formal_modules": len(module_paths),
            "theorem_bearing_modules": sum(bool(rows) for rows in by_module.values()),
            "data_or_definition_modules": sum(not rows for rows in by_module.values()),
            "advertised_declarations": len(catalog["theorems"]),
            "normalized_statement_groups": len({row["statement_sha256"] for row in catalog["theorems"]}),
            "families": len(families),
        },
        "selection": {"family": family, "module": module,
                      "formal_modules": len(modules), "declarations": len(declarations)},
        "families": family_rows,
        "modules": modules,
        "relations": {
            "compiled_proof_dependencies": [
                {"from": row["name"], "to": row["proof_dependencies"], "kind": "COMPILED_PROOF_DEPENDENCIES"}
                for row in declarations],
            "compiled_type_dependencies": [
                {"from": row["name"], "to": row["type_dependencies"], "kind": "COMPILED_TYPE_DEPENDENCIES"}
                for row in declarations],
            "lean_module_imports": [edge for edge in all_imports if edge["from"] in selected_modules],
            "authored_routes": declared_edges,
            "static_python_imports": static,
        },
        "open_bridge_debts": [{"family": row["id"], "debt": debt}
                              for row in selected_families for debt in row["open_debts"]],
        "execution_receipts": [],
        "runtime_execution_performed": False,
        "all_capabilities_executed": False,
        "inputs": dict(sorted(inputs.items())),
        "limits": [
            "The existing compiled catalogue is the sole declaration index; this report does not compile Lean.",
            "Proof and type dependencies may point to definitions outside the advertised theorem population.",
            "Authored routes express a reviewed intended use, not proof of a Python refinement or a dynamic call.",
            "Static imports reuse tools/code_entropy.py and cannot establish execution, source fidelity or semantic coverage.",
            "Binary presence and test references are availability observations; no check is counted as run here.",
            "Open bridge debts remain explicit even when every existing module has a resolved route.",
        ],
    }


def summary(report):
    """A compact startup view, without changing the scope of the full report."""
    return {key: report[key] for key in
            ("schema", "authority", "semantic_authority", "catalogue", "population", "selection",
             "runtime_execution_performed", "all_capabilities_executed")} | {
        "open_bridge_debt_count": len(report["open_bridge_debts"]),
        "detail_command": "python -m tools.entropy_framework reuse --family FAMILY_ID (or --module Nabt.Module)",
        "families": [{**{key: row[key] for key in
                      ("id", "title_ar", "formal_modules", "entrypoint_ids")},
                      "open_debt_count": len(row["open_debts"]),
                      "native_availability": {item["target"]: "PRESENT_NOT_RUN" if item["binary_present"] else "UNAVAILABLE"
                                              for item in row["native_availability"]}}
                     for row in report["families"]],
    }
