"""Authored adapter regressions, separate from the frozen independent material.

These exercise exact source replay, correlated alternatives, authority
withdrawal and the real Lean boundary. They are not Arabic discovery scores.
"""

from copy import deepcopy
from hashlib import sha256
import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.errors import NabtError


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nabt_recursive_source_bridge", ROOT / "tools/recursive_bridge.py")
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)
TRAINING = (ROOT / "examples/discourse_training.tsv").read_bytes()
CONTEXT = json.loads((ROOT / "examples/discourse_context.json").read_text())


def leaves(tree):
    if tree["op"] == "atom":
        return [tree]
    if tree["op"] == "join":
        return leaves(tree["left"]) + leaves(tree["right"])
    return leaves(tree["child"])


def rehash(report):
    for key in ("morphology_nodes", "syntax_frames"):
        for node in report[key]:
            node["node_id"] = bridge._identity({k: v for k, v in node.items() if k != "node_id"})
    report["report_id"] = bridge._identity({k: v for k, v in report.items() if k != "report_id"})
    return report


class RecursiveSourceBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon(TRAINING)

    def read(self, text, **options):
        return bridge.read_recursive_source(text, lexical_model=self.model,
                                            context=CONTEXT, **options)

    def verify(self, report, text, **options):
        return bridge.verify_recursive_source(report, text=text, lexical_model=self.model,
                                              context=CONTEXT, **options)

    def test_discontinuous_root_uses_complete_original_host(self):
        report = self.read("مَكْتُوبٌ")
        node, = report["morphology_nodes"]
        self.assertEqual(node["root"], ["ك", "ت", "ب"])
        self.assertEqual(node["radical_fibers"], [[2], [4], [7]])
        self.assertEqual(len(node["alignment"]), 8)
        self.assertEqual([a["byte_span"]["start"] for a in node["alignment"]], list(range(0, 16, 2)))
        atoms = leaves(node["host_tree"])
        self.assertEqual("".join(a["value"] for a in atoms), "مَكْتُوب")
        self.assertEqual(len(atoms), 8)
        self.assertEqual(node["boundary"]["start"], 8)
        self.assertEqual(node["source_after"], ["ٌ"])
        self.assertFalse(node["attested_root"])
        self.assertFalse(node["linguistic_license"])
        self.assertTrue(self.verify(report, "مَكْتُوبٌ")["valid"])

    def test_global_coordinates_keep_prefix_suffix_and_every_source_atom(self):
        text = "  مَكْتُوبٌ\n"
        report = self.read(text, source_id="sample", scope="passage")
        node, = report["morphology_nodes"]
        self.assertEqual(node["radical_fibers"], [[4], [6], [9]])
        self.assertEqual(node["source_before"], [" ", " "])
        self.assertEqual(node["source_after"], ["ٌ", "\n"])
        for atom in leaves(node["host_tree"]):
            self.assertEqual(atom["before"] + [atom["value"]] + atom["after"], list(text))
        self.assertTrue(self.verify(report, text, source_id="sample", scope="passage")["valid"])

    def test_same_shape_different_catalog_entries_are_not_collapsed(self):
        report = self.read("كَاتِبٌ")
        nodes = report["morphology_nodes"]
        self.assertEqual({n["catalog_id"] for n in nodes}, {"nominal.faail", "grammar.sifa.faa3il"})
        self.assertEqual(len({n["node_id"] for n in nodes}), 2)
        self.assertEqual(len({n["reading_id"] for n in nodes}), 2)
        self.assertEqual(nodes[0]["root"], nodes[1]["root"])
        self.assertEqual(nodes[0]["alignment"], nodes[1]["alignment"])
        self.assertNotEqual(bridge.morphology_request("كَاتِبٌ", 0)["node"]["rule"],
                            bridge.morphology_request("كَاتِبٌ", 1)["node"]["rule"])

    def test_correlated_root_template_pairs_remain_correlated(self):
        report = self.read("انْتَبَر")
        self.assertEqual({(n["catalog_id"], "".join(n["root"])) for n in report["morphology_nodes"]},
                         {("past.VII", "تبر"), ("past.VIII", "نبر")})
        first, second = report["morphology_nodes"]
        self.assertNotEqual(first["alignment"][1]["origin"], second["alignment"][1]["origin"])

    def test_quadriliteral_arity_is_preserved(self):
        report = self.read("دَحْرَجَة")
        node = next(n for n in report["morphology_nodes"] if n["catalog_id"] == "grammar.masdar.quad.fa3lala")
        self.assertEqual(node["arity"], 4)
        self.assertEqual(node["root"], list("دحرج"))
        self.assertEqual(node["radical_fibers"], [[0], [2], [4], [6]])

    def test_utf8_scalar_table_is_explicit_and_not_normalized(self):
        source = bridge.source_view("أ😀َ\n")
        self.assertEqual(source["byte_boundaries"], [0, 2, 6, 8, 9])
        self.assertEqual(source["atoms"], ["أ", "😀", "َ", "\n"])
        self.assertEqual(source["normalization"], "NONE")
        decomposed = bridge.source_view("ا\u0654😀َ\n")
        self.assertNotEqual(source["source_sha256"], decomposed["source_sha256"])
        self.assertNotEqual(source["lean_source"], decomposed["lean_source"])

    def test_source_span_cannot_split_utf8_or_claim_wrong_bytes(self):
        report = self.read("مَكْتُوبٌ")
        span = report["morphology_nodes"][0]["alignment"][0]["byte_span"]
        for change in ({"start": 1}, {"end": 100}, {"start": True},
                       {"span_sha256": "0" * 64}, {"source_id": "other"}):
            with self.subTest(change=change), self.assertRaises(NabtError):
                bridge._atom_span(report["source"], {**span, **change})

    def test_source_scope_and_revision_are_external_replay_authority(self):
        report = self.read("كَاتِبٌ", source_id="book", scope="chapter")
        for text, source_id, scope in (("كَاتِبٌ ", "book", "chapter"),
                                      ("كَاتِبٌ", "other", "chapter"),
                                      ("كَاتِبٌ", "book", "other")):
            with self.subTest(text=text, source_id=source_id, scope=scope):
                self.assertFalse(self.verify(report, text, source_id=source_id, scope=scope)["valid"])

    def test_rehashing_mutated_root_template_alignment_does_not_grant_authority(self):
        original = self.read("مَكْتُوبٌ")
        mutations = [lambda n: n["root"].__setitem__(0, "ق"),
                     lambda n: n.__setitem__("catalog_id", "nominal.faail"),
                     lambda n: n["alignment"][2].__setitem__("source_position", 0),
                     lambda n: n.__setitem__("section", "noun"),
                     lambda n: n.__setitem__("evidence_ids", [123]),
                     lambda n: n.__setitem__("attested_root", True)]
        for mutate in mutations:
            report = deepcopy(original)
            mutate(report["morphology_nodes"][0])
            self.assertFalse(self.verify(rehash(report), "مَكْتُوبٌ")["valid"])

    def test_false_success_and_forged_source_digest_are_rejected_on_replay(self):
        original = self.read("مَكْتُوبٌ")
        for change in ({"grammar_certified": True}, {"world_truth": "TRUE"},
                       {"acquisition_measured": True}):
            report = {**deepcopy(original), **change}
            self.assertFalse(self.verify(rehash(report), "مَكْتُوبٌ")["valid"])
        report = deepcopy(original)
        report["source"]["raw_text"] = "قَكْتُوبٌ"
        report["source"]["source_sha256"] = sha256("قَكْتُوبٌ".encode()).hexdigest()
        self.assertFalse(self.verify(rehash(report), "مَكْتُوبٌ")["valid"])

    def test_rejected_analyses_keep_diagnostics_but_never_transport_actual_roles(self):
        report = self.read("هل أنت عالم؟", with_discourse=True)
        rejected = [f for f in report["syntax_frames"] if f["upstream_analysis"]["rejected_candidate"]]
        qualified = [f for f in report["syntax_frames"] if f["qualified_analysis"]]
        self.assertTrue(rejected)
        self.assertTrue(qualified)
        self.assertTrue(all(not f["roles"] and f["section"] is None for f in rejected))
        self.assertTrue(all(f["roles"] for f in qualified))
        for frame in report["syntax_frames"]:
            self.assertEqual([c["reading_id"] for c in frame["ordered_reading_children"]],
                             frame["upstream_analysis"]["reading_ids"])
            self.assertEqual(frame["provenance"], "source_reconstruction")
            self.assertFalse(frame["original_syntax_children_recovered"])

    def test_case_domain_survives_governor_transport(self):
        report = self.read("إنَّ هذا عالم.", with_discourse=True)
        for frame in report["syntax_frames"]:
            if frame["qualified_analysis"]:
                self.assertEqual({(r["role"], r["case"], r["case_domain"]) for r in frame["roles"]},
                                 {("inna_subject", "nasb", "local_case"),
                                  ("inna_predicate", "raf", "inflected_case")})

    def test_role_child_and_support_mutations_fail_even_with_new_hashes(self):
        original = self.read("زيد كاتب.", with_discourse=True)
        for key in ("roles", "ordered_reading_children", "supports", "relations"):
            report = deepcopy(original)
            frame = report["syntax_frames"][0]
            if key == "roles":
                frame[key][0]["case"] = "nasb"
            elif key == "ordered_reading_children":
                frame[key].reverse()
            elif key == "supports":
                frame[key] = []
            else:
                frame[key].append({"fake": "attachment"})
            self.assertFalse(self.verify(rehash(report), "زيد كاتب.", with_discourse=True)["valid"])

    def test_withdrawn_corpus_or_context_invalidates_old_transport(self):
        text = "هذا عالم."
        report = self.read(text, with_discourse=True)
        self.assertTrue(any(f["roles"] for f in report["syntax_frames"]))
        self.assertFalse(bridge.verify_recursive_source(report, text=text, context=CONTEXT,
                                                       with_discourse=True)["valid"])
        context = deepcopy(CONTEXT)
        context["deixis"] = []
        self.assertFalse(bridge.verify_recursive_source(report, text=text, lexical_model=self.model,
                                                       context=context, with_discourse=True)["valid"])

    def test_upstream_reports_are_complete_and_requests_invent_no_receipts(self):
        report = self.read("زيد كاتب.", with_discourse=True)
        self.assertTrue(report["upstream_discourse"]["clauses"])
        self.assertTrue(report["upstream_morphology"]["occurrences"])
        for request in (bridge.morphology_request("مَكْتُوبٌ"),
                        bridge.frame_request("زيد كاتب.", lexical_model=self.model, context=CONTEXT)):
            self.assertEqual(request["offered"], [])
            self.assertEqual(request["interpreted"], [])
            self.assertEqual(request["node"]["metadata"]["provenance"], "source_reconstruction")
            self.assertTrue(request["node"]["metadata"]["unresolved"])

    def test_source_support_references_and_exact_frame_names_survive_lean_projection(self):
        text = "إنَّ هذا عالم."
        report = self.read(text, with_discourse=True)
        frame = report["syntax_frames"][0]
        self.assertTrue(frame["evidence_ids"])
        records = {record["id"]: record for record in report["evidence_records"]}
        self.assertEqual([records[i]["support"] for i in frame["evidence_ids"]], frame["supports"])
        request = bridge.frame_request(text, lexical_model=self.model, context=CONTEXT)
        self.assertEqual(request["node"]["metadata"]["evidence_ids"], frame["evidence_ids"])
        number = request["node"]["rule"]
        encoded = number.to_bytes((number.bit_length() + 7) // 8, "big")
        self.assertEqual(encoded, b"\x01" + b"inna_construction")
        self.assertEqual(request["interpreted"], [])

    def test_strict_json_rejects_nan_duplicate_keys_and_escaped_surrogates(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":"\\ud800"}', b'{}{}'):
            with self.subTest(raw=raw), self.assertRaises((ValueError, NabtError)):
                bridge._strict_json(raw)

    def test_unwitnessed_text_is_transported_without_invented_morphology(self):
        report = self.read("زلفخ")
        self.assertEqual(report["morphology_nodes"], [])
        self.assertFalse(report["grammar_certified"])
        self.assertTrue(self.verify(report, "زلفخ")["valid"])
        with self.assertRaises(NabtError) as caught:
            bridge.morphology_request("زلفخ")
        self.assertEqual(caught.exception.status, "DEFER")

    def test_invalid_source_types_identifiers_and_boolean_indices(self):
        for call in (lambda: bridge.source_view(None), lambda: bridge.source_view("\ud800"),
                     lambda: bridge.source_view("x", source_id=""),
                     lambda: bridge.read_recursive_source("x", with_discourse=1),
                     lambda: bridge.morphology_request("كَاتِبٌ", True)):
            with self.assertRaises(NabtError):
                call()

    def test_resource_limits_defer_before_host_tree_construction(self):
        for call in (lambda: bridge.source_view("ب" * 4097),
                     lambda: bridge.source_view("x", source_id="ب" * 49)):
            with self.assertRaises(NabtError) as caught:
                call()
            self.assertEqual((caught.exception.status, caught.exception.code), ("DEFER", "RESOURCE_LIMIT"))
        with patch.object(bridge, "MAX_REPORT_BYTES", 20000), patch.object(bridge, "host_tree") as host:
            with self.assertRaises(NabtError) as caught:
                self.read("مَكْتُوبٌ")
            self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")
            host.assert_not_called()

    def test_serialized_output_budget_includes_utf8_and_newline(self):
        exact = len(json.dumps({"text": "ب"}, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode()) + 1
        with patch.object(bridge, "MAX_REPORT_BYTES", exact):
            self.assertEqual(len(bridge.wire({"text": "ب"})) + 1, exact)
        with patch.object(bridge, "MAX_REPORT_BYTES", exact - 1), self.assertRaises(NabtError):
            bridge.wire({"text": "ب"})

    def test_missing_explicit_probe_does_not_skip_or_claim_success(self):
        with self.assertRaises(NabtError) as caught:
            bridge.check_with_lean({}, probe="/does/not/exist/recursiveBridgeProbe")
        self.assertEqual(caught.exception.code, "RECURSIVE_PROBE_UNAVAILABLE")
        self.assertEqual(caught.exception.status, "DEFER")

    def test_standalone_adapter_keeps_the_registered_runtime_inventory_exact(self):
        spec = importlib.util.spec_from_file_location("nabt_recursive_freeze_boundary",
                                                      ROOT / "tools/text_evaluation/integrity.py")
        integrity = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(integrity)
        # Inquiry is now part of the installed runtime; the recursive bridge
        # remains a standalone tool outside this approved exact inventory.
        freeze_path = ROOT / "evidence/attested_mark_recovery_v1/code_freeze_v1.json"
        self.assertEqual(sha256(freeze_path.read_bytes()).hexdigest(),
                         "1c47bfee3fa0baa190ec0e0455dfcb2528aec65a6280694956c1e00186948d30")
        frozen = integrity.verify_code_freeze(freeze_path, ROOT)
        self.assertEqual(frozen["snapshot_sha256"],
                         "8ea9f386852e40ae092ec9a0c9c37ae7a3c48d50468191038209511f156ac280")
        self.assertEqual(len(frozen["files"]), 101)
        authoritative = integrity.authoritative_paths(ROOT)
        self.assertEqual({row["path"] for row in frozen["files"]}, authoritative)
        self.assertIn("src/nabt/rational_inquiry.py", authoritative)
        self.assertNotIn("tools/recursive_bridge.py", authoritative)
        self.assertFalse((ROOT / "src/nabt/recursive_bridge.py").exists())

    def test_probe_response_requires_matching_domain_operation_and_exact_node(self):
        request = bridge.morphology_request("مَكْتُوبٌ")
        envelope = {"law_id": bridge.LEAN_LAW_ID, "scope": bridge.LEAN_SCOPE,
                    "conditional": True, "grammar_certified": False, "acquisition_measured": False,
                    "status": "OK", "op": "bridge_assess", "node": request["node"]}
        for mutation in ({"law_id": "foreign"}, {"grammar_certified": True},
                         {"op": "core_number"}, {"node": {"forged": True}}):
            result = subprocess.CompletedProcess([], 0, bridge.wire({**envelope, **mutation}), b"")
            with patch.object(bridge.subprocess, "run", return_value=result), self.assertRaises(NabtError):
                bridge.check_with_lean(request, probe=sys.executable)
        duplicate = b'{"status":"OK","status":"ERROR"}'
        with patch.object(bridge.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, duplicate, b"")):
            with self.assertRaises(NabtError):
                bridge.check_with_lean(request, probe=sys.executable)

    def test_probe_exactness_rejects_python_boolean_integer_float_aliases(self):
        request = bridge.morphology_request("مَكْتُوبٌ")
        for replacement in (True, 1.0):
            node = deepcopy(request["node"])
            node["metadata"]["source"]["atomization_id"] = replacement
            self.assertEqual(node, request["node"], "This is the Python equality counterexample")
            envelope = {"law_id": bridge.LEAN_LAW_ID, "scope": bridge.LEAN_SCOPE,
                        "conditional": True, "grammar_certified": False, "acquisition_measured": False,
                        "status": "OK", "op": "bridge_assess", "node": node}
            result = subprocess.CompletedProcess([], 0, bridge.wire(envelope), b"")
            with patch.object(bridge.subprocess, "run", return_value=result), self.assertRaises(NabtError):
                bridge.check_with_lean(request, probe=sys.executable)

    def test_cli_round_trip_duplicate_json_and_bounded_file_read(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.txt"
            report = Path(directory) / "report.json"
            source.write_text("مَكْتُوبٌ", encoding="utf-8")
            base = [sys.executable, str(ROOT / "tools/recursive_bridge.py")]
            execution = subprocess.run(base + ["read", str(source)], capture_output=True, check=True)
            report.write_bytes(execution.stdout)
            execution = subprocess.run(base + ["verify", str(source), "--report", str(report)], capture_output=True)
            self.assertEqual(execution.returncode, 0, execution.stderr)
            self.assertTrue(json.loads(execution.stdout)["valid"])
            report.write_text('{"schema":"one","schema":"two"}')
            execution = subprocess.run(base + ["verify", str(source), "--report", str(report)], capture_output=True)
            self.assertEqual(execution.returncode, 2)
            self.assertEqual(json.loads(execution.stdout)["status"], "REJECT")
            source.write_bytes(b"x" * (bridge.MAX_SOURCE_BYTES + 1))
            execution = subprocess.run(base + ["read", str(source)], capture_output=True)
            self.assertEqual(execution.returncode, 3)
            self.assertEqual(json.loads(execution.stdout)["code"], "RESOURCE_LIMIT")


class RecursiveSourceLeanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        explicit = os.environ.get("NABT_RECURSIVE_BRIDGE_PROBE")
        cls.probe = Path(explicit) if explicit else ROOT / "formal/.lake/build/bin/recursiveBridgeProbe"
        if not cls.probe.is_file():
            if explicit:
                raise AssertionError("Configured recursiveBridgeProbe does not exist")
            raise unittest.SkipTest("Build recursiveBridgeProbe for Lean adapter integration")

    def test_real_morphology_roundtrip_source_only_complete_alignment(self):
        request = bridge.morphology_request("  مَكْتُوبٌ  ")
        response = bridge.check_with_lean(request, probe=self.probe)
        self.assertEqual(response["verdict"], "SOURCE_ONLY")
        self.assertTrue(response["source_bound"])
        self.assertFalse(response["grammar_certified"])
        self.assertEqual(response["node"], request["node"])

    def test_actual_qualified_roles_roundtrip_without_synthetic_grammar_certificate(self):
        model = learn_qac_lexicon(TRAINING)
        request = bridge.frame_request("إنَّ هذا عالم.", lexical_model=model, context=CONTEXT)
        response = bridge.check_with_lean(request, probe=self.probe)
        self.assertEqual(response["verdict"], "SOURCE_ONLY")
        self.assertTrue(response["source_bound"])
        self.assertEqual(len(response["node"]["metadata"]["roles"]), 2)
        self.assertFalse(response["all_premises"])
        self.assertFalse(response["linguistic_ready"])

    def test_complete_assessment_retains_resolvable_evidence_namespace(self):
        text = "إنَّ هذا عالم."
        model = learn_qac_lexicon(TRAINING)
        envelope = bridge.assess_recursive_source(text, kind="frame", probe=self.probe,
                                                  lexical_model=model, context=CONTEXT)
        self.assertEqual(envelope["evidence_namespace"]["report_id"], envelope["transport"]["report_id"])
        self.assertEqual(envelope["assessment"]["node"], envelope["request"]["node"])
        self.assertTrue(envelope["transport"]["evidence_records"])
        self.assertTrue(envelope["transport"]["syntax_frames"][0]["ordered_reading_children"])
        self.assertTrue(bridge.verify_recursive_assessment(envelope, text=text, kind="frame", probe=self.probe,
                                                          lexical_model=model, context=CONTEXT)["valid"])
        for change in ("evidence_records", "ordered_reading_children", "references", "node"):
            altered = deepcopy(envelope)
            if change == "evidence_records":
                altered["transport"][change][0]["support"] = {"fake": "witness"}
            elif change == "node":
                altered["assessment"]["node"]["rule"] += 1
            else:
                altered["transport"]["syntax_frames"][0][change] = [{"fake": "lost_or_changed_child"}]
            rehash(altered["transport"])
            altered["evidence_namespace"]["report_id"] = altered["transport"]["report_id"]
            self.assertFalse(bridge.verify_recursive_assessment(altered, text=text, kind="frame", probe=self.probe,
                                                               lexical_model=model, context=CONTEXT)["valid"])

    def test_projection_limits_defer_before_expanding_a_source_spine(self):
        with patch.object(bridge, "_metadata") as construct:
            with self.assertRaises(NabtError) as caught:
                bridge.morphology_request(" " * 257 + "مَكْتُوبٌ")
            self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")
            construct.assert_not_called()

    def test_cli_assessment_and_complete_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.txt"
            report = Path(directory) / "report.json"
            source.write_text("مَكْتُوبٌ", encoding="utf-8")
            command = [sys.executable, str(ROOT / "tools/recursive_bridge.py")]
            result = subprocess.run(command + ["lean-morphology", str(source), "--probe", str(self.probe)],
                                    capture_output=True, check=True)
            envelope = json.loads(result.stdout)
            self.assertEqual(envelope["schema"], bridge.ASSESSMENT_ID)
            self.assertEqual(envelope["assessment"]["verdict"], "SOURCE_ONLY")
            report.write_bytes(result.stdout)
            result = subprocess.run(command + ["verify", str(source), "--report", str(report),
                                                "--probe", str(self.probe)], capture_output=True, check=True)
            self.assertTrue(json.loads(result.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
