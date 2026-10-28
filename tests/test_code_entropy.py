"""Independent small examples for the declared static audit, not runtime imports."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import code_entropy as audit


class GraphMetricsTests(unittest.TestCase):
    def test_chain_triangle_and_isolated_vertex_have_hand_counted_invariants(self):
        chain = audit.graph_metrics("abcd", [("a", "b"), ("b", "c")])
        self.assertEqual(chain["directed_edge_count"], 2)
        self.assertEqual(chain["strong_components"], [["a"], ["b"], ["c"], ["d"]])
        self.assertEqual(chain["weak_components"], [["a", "b", "c"], ["d"]])
        self.assertEqual(chain["isolated_vertices"], ["d"])
        self.assertEqual(chain["undirected_cycle_rank"], 0)
        self.assertEqual(chain["outdegree_entropy"]["bits"], 1.0)
        triangle = audit.graph_metrics("abc", [("a", "b"), ("a", "c"), ("b", "c")])
        self.assertEqual(triangle["cyclic_components"], [])
        self.assertEqual(triangle["undirected_cycle_rank"], 1)
        self.assertAlmostEqual(triangle["outdegree_entropy"]["bits"], 0.9182958340544896)
        self.assertEqual(triangle["fan_out"], {"a": 2, "b": 1, "c": 0})

    def test_reciprocal_and_self_edges_have_explicit_projection_semantics(self):
        graph = audit.graph_metrics("abc", [("a", "b"), ("b", "a"), ("a", "b"), ("c", "c")])
        self.assertEqual(graph["directed_edge_count"], 3)
        self.assertEqual(graph["cyclic_components"], [["a", "b"], ["c"]])
        self.assertEqual(graph["multi_node_strong_components"], [["a", "b"]])
        self.assertEqual(graph["multi_node_strong_component_count"], 1)
        self.assertEqual(graph["self_edge_count"], 1)
        self.assertEqual(graph["undirected_simple_edge_count"], 1)
        self.assertEqual(graph["undirected_cycle_rank"], 0)
        self.assertEqual(graph["isolated_vertices"], [])

    def test_empty_and_singleton_populations_have_no_measured_distribution(self):
        for vertices in ([], ["a"]):
            result = audit.graph_metrics(vertices, [])
            self.assertIsNone(result["outdegree_entropy"]["bits"])
            self.assertEqual(result["outdegree_entropy"]["positive_support"], 0)
            self.assertEqual(result["undirected_cycle_rank"], 0)
        self.assertEqual(audit.graph_metrics(["a"], [])["isolated_vertices"], ["a"])
        with self.assertRaises(audit.AuditError):
            audit.graph_metrics(["a"], [("a", "outside")])
        with self.assertRaises(audit.AuditError):
            audit.graph_metrics([None], [])

    def test_long_chain_and_input_order_do_not_change_results(self):
        vertices = [str(i) for i in range(1500)]
        edges = list(zip(vertices, vertices[1:]))
        self.assertEqual(audit.graph_metrics(vertices, edges),
                         audit.graph_metrics(reversed(vertices), reversed(edges)))


class SourceAuditTests(unittest.TestCase):
    def test_relative_imports_and_direct_conditional_and_local_classification(self):
        report = audit.audit_sources({
            "src/nabt/__init__.py": b"",
            "src/nabt/a.py": b"from . import b\nif flag:\n    from .b import value\ndef f():\n    import nabt.b\n",
            "src/nabt/b.py": b"from .a import f\n",
            "src/nabt/pkg/__init__.py": b"",
            "src/nabt/pkg/c.py": b"from ..b import value\n",
        })
        sites = [site for site in report["import_sites"] if site["source"] == "nabt.a"]
        self.assertEqual([site["classification"] for site in sites],
                         ["direct_module_body", "nested", "nested"])
        self.assertEqual([site["line"] for site in sites], [1, 3, 5])
        self.assertEqual(sites[0]["targets"], ["nabt", "nabt.b"])
        self.assertIn(["nabt.pkg.c", "nabt.b"], report["graphs"]["all_imports"]["edges"])
        self.assertEqual(report["graphs"]["all_imports"]["cyclic_components"], [["nabt.a", "nabt.b"]])

    def test_local_backedge_is_absent_from_direct_projection(self):
        report = audit.audit_sources({"tools/a.py": b"import tools.b\n",
                                      "tools/b.py": b"def use():\n    import tools.a\n"})
        self.assertEqual(report["graphs"]["direct_module_body"]["cyclic_components"], [])
        self.assertEqual(report["graphs"]["all_imports"]["cyclic_components"], [["tools.a", "tools.b"]])

    def test_forbidden_backedge_mutation_is_a_concrete_gate_failure(self):
        sources = {"src/nabt/a.py": b"pass\n", "tools/helper.py": b"pass\n",
                   "integrations/client.py": b"pass\n"}
        self.assertTrue(audit.audit_sources(sources)["boundary"]["passed"])
        for imported in (b"tools.helper", b"integrations.client"):
            with self.subTest(imported=imported):
                sources["src/nabt/a.py"] = b"def f():\n    import " + imported + b"\n"
                boundary = audit.audit_sources(sources)["boundary"]
                self.assertFalse(boundary["passed"])
                self.assertEqual(boundary["violations"][0]["line"], 2)
                self.assertEqual(boundary["violations"][0]["target"], imported.decode())

    def test_layer_edge_counts_and_self_imports_remain_separate_observations(self):
        report = audit.audit_sources({"src/nabt/__init__.py": b"from . import member\n",
                                      "tools/a.py": b"import nabt\n"})
        graph = report["graphs"]["all_imports"]
        self.assertEqual(graph["layer_edge_counts"]["core->core"], 1)
        self.assertEqual(graph["layer_edge_counts"]["tools->core"], 1)
        self.assertEqual(graph["layer_edge_counts"]["core->tools"], 0)
        self.assertEqual(graph["self_edge_count"], 1)
        self.assertEqual(graph["multi_node_strong_component_count"], 0)
        self.assertEqual(graph["cyclic_components"], [["nabt"]])

    def test_dynamic_literal_is_reported_but_not_inferred_as_a_static_edge(self):
        report = audit.audit_sources({"src/nabt/a.py": b"__import__('tools.helper')\n",
                                      "tools/helper.py": b""})
        self.assertTrue(report["boundary"]["passed"])
        self.assertEqual(report["graphs"]["all_imports"]["directed_edge_count"], 0)
        self.assertEqual(report["dynamic_import_sites"][0]["literal_first_argument"], "tools.helper")

    def test_unresolved_tooling_namespaces_cannot_evade_the_boundary(self):
        for statement in (b"import tools.missing", b"from tools import missing",
                          b"import integrations", b"from integrations.missing import thing"):
            with self.subTest(statement=statement):
                report = audit.audit_sources({"src/nabt/a.py": statement + b"\n"})
                self.assertFalse(report["boundary"]["passed"])
                self.assertFalse(report["boundary"]["violations"][0]["target_in_population"])

    def test_external_missing_and_dynamic_imports_are_reported_without_execution(self):
        report = audit.audit_sources({"tools/a.py": b"""import os
import tools.missing
from importlib import import_module as load
import importlib.util as loader
load('tools.missing')
loader.spec_from_file_location('x', 'elsewhere.py')
__import__(runtime_name)
raise RuntimeError('must never execute')
"""})
        self.assertEqual(report["graphs"]["all_imports"]["directed_edge_count"], 0)
        self.assertEqual({row["call"] for row in report["dynamic_import_sites"]},
                         {"importlib.import_module", "importlib.util.spec_from_file_location", "__import__"})
        missing = {row["name"]: row["kind"] for row in report["unresolved_or_external_imports"]}
        self.assertEqual(missing["tools.missing"], "internal_or_namespace_unresolved")
        self.assertEqual(missing["os"], "external_or_unresolved")

    def test_exact_clone_candidates_keep_names_docstrings_and_nested_spans(self):
        function = b'def repeated():\n    "doc"\n    a = 1\n    b = 2\n    c = 3\n    d = 4\n    e = 5\n    return a + b + c + d + e\n'
        report = audit.audit_sources({"tools/a.py": function, "tools/b.py": b"\n" + function,
                                      "tools/c.py": function.replace(b'"doc"', b'"different"'),
                                      "tools/d.py": function.replace(b"repeated", b"renamed")})
        candidates = report["clone_candidates"]
        self.assertEqual(candidates["group_count"], 1)
        self.assertEqual(candidates["occurrence_count"], 2)
        self.assertEqual([row["line"] for row in candidates["groups"][0]["occurrences"]], [1, 2])
        self.assertIsNone(candidates["removable_lines"])
        nested = b"def outer():\n" + b"".join(b"    " + line + b"\n" for line in function.splitlines())
        result = audit.audit_sources({"tools/a.py": nested, "tools/b.py": nested})["clone_candidates"]
        self.assertEqual(result["group_count"], 2)
        self.assertIsNone(result["removable_lines"])

    def test_inventory_hash_determinism_and_explicit_failure(self):
        sources = {"tools/z.py": b"pass\n", "tools/a.py": b"# comment\n"}
        report = audit.audit_sources(sources)
        self.assertEqual(report, audit.audit_sources(dict(reversed(list(sources.items())))))
        self.assertEqual(report["inventory"][0]["sha256"], hashlib.sha256(b"# comment\n").hexdigest())
        self.assertEqual(report["method"]["source_sha256"],
                         hashlib.sha256(Path(audit.__file__).read_bytes()).hexdigest())
        for invalid in ({"tools/a.py": b"def broken("},
                        {"tools/a.py": b"", "tools/a/__init__.py": b""},
                        {"tools/tests/test_a.py": b""}):
            with self.subTest(paths=list(invalid)), self.assertRaises(audit.AuditError):
                audit.audit_sources(invalid)


class RepositoryAndCliTests(unittest.TestCase):
    def test_git_tree_and_working_tracked_populations_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(["git", "-C", str(root), *args], check=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
            git("init", "-q")
            (root / "tools/tests").mkdir(parents=True)
            (root / "tools/a.py").write_bytes(b"pass\n")
            (root / "tools/tests/test_a.py").write_bytes(b"bad syntax !!")
            git("add", ".")
            git("-c", "user.name=Audit fixture", "-c", "user.email=audit@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "-qm", "independent fixture")
            (root / "tools/a.py").write_bytes(b"import os\n")
            (root / "tools/untracked.py").write_bytes(b"bad syntax !!")
            baseline = audit.audit_repository(root, "HEAD")
            working = audit.audit_repository(root)
            self.assertEqual(baseline["population"]["file_count"], 1)
            self.assertEqual(working["population"]["file_count"], 1)
            self.assertNotEqual(baseline["inventory"], working["inventory"])
            self.assertEqual(baseline["provenance"]["kind"], "git-tree")
            self.assertEqual(working["provenance"]["kind"], "working-tree-tracked")
            self.assertEqual(baseline["inventory"][0]["sha256"], hashlib.sha256(b"pass\n").hexdigest())
            self.assertEqual(baseline["method"], working["method"])
            self.assertNotIn("tools/code_entropy.py", [row["path"] for row in baseline["inventory"]])
            self.assertIn("not an atomic", working["provenance"]["consistency"])

    def test_cli_exclusive_output_and_unresolved_boundary_failure_report(self):
        report = audit.audit_sources({"src/nabt/a.py": b"import tools.missing\n"})
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with patch.object(audit, "audit_repository", return_value=report), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(audit.main(["--output", str(output), "--check"]), 1)
                original = output.read_bytes()
                self.assertFalse(json.loads(original)["boundary"]["passed"])
                self.assertFalse(json.loads(original)["boundary"]["violations"][0]["target_in_population"])
                self.assertEqual(audit.main(["--output", str(output)]), 2)
                self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
