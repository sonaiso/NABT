"""Native denotation controls, export fidelity and external replay attacks."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import lexical_testimony
from tools.evidence_lifecycle_v1 import wire
from tools.grammar_catalog import gateway, gateway_routes, gateway_links, lexical_ontolex as lexical

NATIVE = os.access(lexical_testimony.ROOT / "formal/.lake/build/bin/lexicalDenotation", os.X_OK)
if os.environ.get("NABT_REQUIRE_IO_GATEWAY_NATIVE") == "1" and not NATIVE:
    raise RuntimeError("The lexical gateway requires the installed lexicalDenotation owner")


def request(route="lexical.ontolex", entry="قلم", target=None):
    return {"schema": gateway.REQUEST_SCHEMA, "route": route,
            "payload": {"entry": entry, "target": ["الذي يكتب به"] if target is None else target}}


def typed(graph, kind):
    return [r for r in graph["@graph"] if r.get("@type") == kind]


class LexicalBoundary(unittest.TestCase):
    def test_retained_testimony_mutation_changes_gateway_identity(self):
        paths = ["AGENTS.md", "Makefile", "GNUmakefile", "pyproject.toml", str(lexical_testimony.CATALOG),
                 "evidence/shared_cognition_v1/model.json", "evidence/contextual_alignment_v1/model.json",
                 "evidence/contextual_alignment_v1/train.json"]
        paths += [p for _, _, p in lexical_testimony.SOURCES.values() if p is not None]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in paths:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"fixture")
            with patch.object(gateway, "ROOT", root), patch.object(gateway, "source_snapshot", return_value=({"files": {}}, {})):
                original = gateway.snapshot()
                path = root / str(lexical_testimony.CATALOG)
                path.write_bytes(b"changed")
                changed = gateway.snapshot()
                self.assertNotEqual(original["files"][str(lexical_testimony.CATALOG)], changed["files"][str(lexical_testimony.CATALOG)])
                self.assertTrue(set(paths) <= changed["files"].keys())
                path.unlink()
                path.symlink_to(root / "Makefile")
                with self.assertRaises(ValueError):
                    gateway.snapshot()

    def test_no_caller_definition_status_or_execution_path(self):
        for route in ("lexical.assess", "lexical.ontolex"):
            good = request(route)
            for key in ("root", "definition", "authority", "native_checked", "sense_id", "checker"):
                bad = deepcopy(good); bad["payload"][key] = True
                with self.subTest(route=route, field=key), self.assertRaises(ValueError):
                    gateway.validate_request(bad)

    def test_boundaries_and_bool_are_not_text(self):
        for entry, target in [(True, []), ("", []), ("قلم", True), ("قلم", [False]),
                              ("قلم", [""]), ("قلم", ["x"] * 65), ("قلم", ["x" * 4097])]:
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                gateway.validate_request(request(entry=entry, target=target))

    def test_missing_checker_keeps_failure_and_exports_no_graph(self):
        # Mock only resource unavailability, never positive semantic outcomes.
        with patch.object(lexical_testimony, "_native", side_effect=OSError("not available")):
            result = lexical.export({"entry": "قلم", "target": ["الذي يكتب به"]})
        self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
        self.assertIsNone(result["graph"])
        self.assertIsNone(result["graph_sha256"])
        self.assertFalse(result["native_checked"])

    def test_links_use_existing_catalogue_and_native_family(self):
        links = gateway_links.build("lexical.ontolex")
        declarations = {r["name"] for r in links["declarations"]}
        self.assertIn("Nabt.LexicalDenotation.check_exact", declarations)
        self.assertIn("Nabt.LexicalDenotation.definition_does_not_assert_world", declarations)
        self.assertIn("tests/test_lexical_ontolex.py", {r["path"] for r in links["tests"]})
        self.assertFalse(links["test_execution_performed"])
        self.assertFalse(links["formal_application_established"])


@unittest.skipUnless(NATIVE, "Build lexicalDenotation; native gate makes absence fatal")
class NativeOntolex(unittest.TestCase):
    def test_three_indications_are_computed_by_existing_owner(self):
        for entry, target, expected in [("فرس", ["واحد الخيل"], "mutabaqa"),
                                        ("بيت", ["المأوى"], "tadammun"),
                                        ("عمي", ["البصر"], "iltizam")]:
            with self.subTest(entry=entry):
                report = gateway_routes.execute("lexical.ontolex", {"entry": entry, "target": target})
                self.assertTrue(report["native_checked"])
                self.assertEqual(report["owner_result"]["common_indications"], [expected])
                for row in typed(report["graph"], "nabt:ConditionalIndication"):
                    self.assertTrue(row["nabt:" + expected])
                    self.assertFalse(row["nabt:worldTruthEstablished"])

    def test_qalam_alternatives_components_and_citations_survive(self):
        report = lexical.export(request()["payload"])
        owner = report["owner_result"]
        self.assertEqual([r["sense_id"] for r in owner["rows"]],
                         ["lisan:qalam-writing", "lisan:qalam-lot", "lisan:qalam-gambling"])
        self.assertEqual(owner["common_indications"], [])
        concepts = typed(report["graph"], "ontolex:LexicalConcept")
        citations = typed(report["graph"], "prov:Entity")
        indications = typed(report["graph"], "nabt:ConditionalIndication")
        self.assertEqual(len(concepts), 3)
        self.assertEqual(sum(r["nabt:mutabaqa"] for r in indications), 1)
        for index, (row, concept, citation, indication) in enumerate(zip(owner["rows"], concepts, citations, indications)):
            self.assertEqual(concept["nabt:sourceSenseID"], row["sense_id"])
            self.assertEqual([v["@value"] for v in concept["nabt:definitionComponents"]["@list"]], row["components"])
            self.assertEqual(citation["rdf:value"]["@value"], row["testimony"]["citation"]["quotation"])
            self.assertEqual(citation["nabt:sourceCheck"], "RETAINED_QUOTATION_ONLY")
            self.assertEqual(indication["nabt:ownerRowPointer"], "/owner_result/rows/" + str(index))
        self.assertFalse(owner["intended_sense_established"])
        self.assertFalse(report["semantic_rank_promoted"])

    def test_unknown_root_does_not_become_rejected_arabic(self):
        report = lexical.export({"entry": "شمس", "target": ["النهار"]})
        self.assertEqual(report["status"], "UNMEASURED_ROOT")
        self.assertTrue(report["native_checked"])
        self.assertEqual(typed(report["graph"], "ontolex:LexicalConcept"), [])
        self.assertFalse(report["owner_result"]["all_arabic_complete"])

    def test_commitment_premises_keep_separate_source_and_alignment_in_graph(self):
        for entry, target, quotation in [("عمي", "البصر", "كالعمى والبصر"),
                                          ("أسد", "الشجاعة", "كدلالة الأسد على الشجاعة")]:
            report = lexical.export({"entry": entry, "target": [target]})
            rows = report["owner_result"]["rows"]
            nodes = typed(report["graph"], "nabt:ConditionalIndication")
            self.assertTrue(nodes)
            for row, node in zip(rows, nodes):
                self.assertTrue(node["nabt:iltizam"])
                encoded = node["nabt:commitmentConditions"]
                self.assertEqual(encoded["@type"], "@json")
                self.assertEqual(encoded["@value"], row["commitment_conditions"])
                premise = encoded["@value"][0]
                self.assertEqual(premise["target"], target)
                self.assertEqual(premise["relation"], "MENTAL_NECESSITY_PREMISE")
                self.assertEqual(premise["alignment_status"], "AUTHORED_CROSS_SOURCE_SENSE_ALIGNMENT")
                citation = premise["source"]["citation"]
                self.assertEqual(citation["work"], "shakhsiyya3")
                self.assertEqual(citation["quotation"], quotation)
                self.assertEqual(citation["end_byte"] - citation["start_byte"], len(quotation.encode()))
                self.assertTrue(premise["source"]["source_file_replayed"])
                self.assertEqual(row["testimony"]["citation"]["work"], "lisan")

    def test_gateway_rejects_dropped_commitment_premise_after_rehash(self):
        expected = request(entry="عمي", target=["البصر"])
        report = gateway.run(expected)
        self.assertEqual(report["status"], "EXECUTED")
        self.assertTrue(gateway.accept_output(report, expected_request=expected)["valid"])
        altered = deepcopy(report)
        result = altered["execution"]["owner_result"]
        node = typed(result["graph"], "nabt:ConditionalIndication")[0]
        node["nabt:commitmentConditions"]["@value"] = []
        result["graph_sha256"] = sha256(wire(result["graph"]).encode()).hexdigest()
        self.assertFalse(gateway.accept_output(altered, expected_request=expected)["valid"])

    def test_indication_is_not_physical_part_or_reverse_association(self):
        for entry, target in [("فهم", ["القلب"]), ("بصر", ["ذهاب البصر كله"])]:
            report = lexical.export({"entry": entry, "target": target})
            self.assertTrue(report["native_checked"])
            self.assertEqual(report["owner_result"]["common_indications"], [])
            for row in typed(report["graph"], "nabt:ConditionalIndication"):
                self.assertFalse(any(row["nabt:" + k] for k in ("mutabaqa", "tadammun", "iltizam")))

    def test_dictionary_index_never_invents_lexical_form_or_external_reference(self):
        report = lexical.export({"entry": "عمي", "target": ["البصر"]})
        keys = {k for r in report["graph"]["@graph"] for k in r}
        self.assertFalse(keys & {"ontolex:canonicalForm", "ontolex:writtenRep", "ontolex:reference", "owl:sameAs"})
        self.assertIn("EXACT_OCCURRENCE_AND_INTENDED_SENSE", report["remaining_obligations"])

    def test_target_duplicates_are_retained_without_creating_new_components(self):
        target = ["واحد الخيل", "واحد الخيل"]
        report = lexical.export({"entry": "فرس", "target": target})
        assessment = typed(report["graph"], "nabt:ConditionalAssessment")[0]
        self.assertEqual([v["@value"] for v in assessment["nabt:targetComponents"]["@list"]], target)
        self.assertEqual(report["owner_result"]["common_indications"], ["mutabaqa"])

    def test_full_gateway_replay_rejects_alternative_loss_even_after_rehash(self):
        expected = request()
        report = gateway.run(expected)
        self.assertEqual(report["status"], "EXECUTED", report["execution"])
        self.assertTrue(gateway.accept_output(report, expected_request=expected)["valid"])
        altered = deepcopy(report)
        result = altered["execution"]["owner_result"]
        result["graph"]["@graph"] = result["graph"]["@graph"][:-3]
        result["graph_sha256"] = sha256(wire(result["graph"]).encode()).hexdigest()
        self.assertFalse(gateway.accept_output(altered, expected_request=expected)["valid"])
        self.assertFalse(gateway.accept_output(report, expected_request=request(entry="بيت"))["valid"])


if __name__ == "__main__":
    unittest.main()
