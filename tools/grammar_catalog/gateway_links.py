"""Derived RAG -> existing compiled declarations -> existing family test links.

This view is not another theorem registry. Test references are not test runs,
and family associations are not per-theorem coverage or refinement proofs.
"""
import ast
from hashlib import sha256

from tools.entropy_framework.reuse import build_reuse_report, current_catalog, ROOT
from .catalog import build_catalog
from .gateway_routes import ROUTES, SHARED_FAMILIES
from .operations import digest


def test_nodes(root, relative):
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Test reference escapes repository")
    raw = path.read_bytes()
    tree = ast.parse(raw, filename=relative)
    tests = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test_"):
                    tests.append(relative[:-3].replace("/", ".") + "." + node.name + "." + child.name)
    if not tests:
        raise ValueError("Referenced test file has no statically discovered test methods: " + relative)
    return {"path": relative, "sha256": sha256(raw).hexdigest(), "test_ids": sorted(tests),
            "discovery": "DECLARED_METHODS_NOT_RUNTIME_PARAMETERIZED_CASES",
            "execution_status": "NOT_RUN_BY_GATEWAY"}


def build(route=None):
    root = ROOT
    if route is not None and route not in ROUTES:
        raise ValueError("Unknown gateway route")
    reuse = build_reuse_report(root)
    families = {r["id"]: r for r in reuse["families"]}
    selected = set(families) if route is None else set(ROUTES[route][0]) | set(SHARED_FAMILIES)
    if route in ("concept.matrix", "neural.graph", "cognitive.lesson"):
        from tools.lexical_training.rag_views import VIEWS
        selected.update(family for _, _, names in VIEWS for family in names)
    compiled, _, _, _ = current_catalog(root)
    curriculum_links = None
    if route in (None, "operation", "cognitive.lesson"):
        # The lesson operation delegates to several installed owners. Resolve
        # the existing curriculum instead of inventing a parallel concept map.
        from tools.lexical_training.reasoning_curriculum import matrix
        curriculum = matrix(compiled=compiled)
        rows = curriculum["matrices"] + curriculum["shared_foundation"]["rows"]
        owner_modules = {m for row in rows for m in row["owner_modules"]}
        owner_paths = {"tools/lexical_training/teaching.py", "tools/lexical_training/grounded_passage.py",
                       "tools/source_learning_connection.py", "tools/epistemic_measurement.py",
                       "tools/mantuq_inference/source_bound.py", "tools/grammar_catalog/temporal.py"}
        for f, family in families.items():
            if owner_modules.intersection(family["formal_modules"]) or owner_paths.intersection(family["runtime_paths"]):
                selected.add(f)
        curriculum_links = {"source_path": "tools/lexical_training/reasoning_curriculum.py",
            "schema": curriculum["schema"], "authority": curriculum["authority"],
            "matrices": curriculum["matrices"], "shared_foundation": curriculum["shared_foundation"],
            "methods": curriculum["methods"], "curriculum_sha256": digest(curriculum),
            "source_review": {k: curriculum["source_review"][k] for k in ("path", "sha256")}}
    if not selected <= families.keys():
        raise ValueError("Gateway references an unknown installed proof family")
    modules = [r for r in reuse["modules"] if r["family"] in selected]
    declarations = {d["name"]: {"name": d["name"], "module": m["module"],
                    "canonical_name": d["canonical_name"], "statement_sha256": d["statement_sha256"]}
                    for m in modules for d in m["declarations"]}
    tests = {p: test_nodes(root, p) for f in sorted(selected) for p in families[f]["test_paths"]}
    source = build_catalog(root)
    from .links import _compose as compose_source_links
    from tools.mantuq_inference.inventory import build_inventory
    from tools.mantuq_inference.links import _compose as compose_policy_links
    source_graph = compose_source_links(source, compiled)
    inventory = build_inventory(root)
    policy_graph = compose_policy_links(inventory, compiled)
    explicit = [r for r in source_graph["edges"] if r["referenced_declaration"] in declarations]
    policies = [r for r in policy_graph["edges"] if r["referenced_declaration"] in declarations]
    unresolved = []
    for kind, rows, key in (("rule", source["rules"], "rule_key"), ("item", source["items"], "item_id")):
        for row in rows:
            names = row["theorem_names"]
            if not names:
                unresolved.append({"kind": kind, "id": row[key], "status": "SOURCE_TO_THEOREM_LINK_OPEN"})
    family_edges = [{"family": f, "modules": families[f]["formal_modules"],
                     "test_paths": families[f]["test_paths"], "checker_paths": families[f]["checker_paths"],
                     "relation": "EXISTING_FAMILY_ASSOCIATION_NOT_PER_THEOREM_COVERAGE"} for f in sorted(selected)]
    value = {"schema": "nabt.io.proof-test-links.v1", "route": route,
        "authority": "DERIVED_NAVIGATION_ONLY", "catalogue": reuse["catalogue"],
        "population": reuse["population"], "declarations": list(declarations.values()),
        "curriculum_links": curriculum_links,
        "source_links": explicit, "policy_links": policies, "unlinked_source_records": unresolved,
        "family_test_links": family_edges, "tests": [tests[p] for p in sorted(tests)],
        "open_obligations": [r for r in reuse["open_bridge_debts"] if r["family"] in selected],
        "test_execution_performed": False, "formal_application_established": False,
        "source_catalog_sha256": digest(source), "policy_inventory_sha256": digest(inventory),
        "source_link_graph_sha256": digest(source_graph), "policy_link_graph_sha256": digest(policy_graph)}
    return {**value, "links_sha256": digest(value)}
