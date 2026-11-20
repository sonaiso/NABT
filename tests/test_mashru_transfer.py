"""The Mashru archive, registered owner, original reader and advisory readout."""
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import mashru_transfer as transfer
from tools.grammar_catalog import gateway, ntp
from tools.lexical_training import mashru_lesson as owner, teaching


def lesson(op, **fields):
    return {"schema": owner.SCHEMA, "operation": op, **fields}


class MashruTransfer(unittest.TestCase):
    def test_manifest_binds_named_compiled_declarations(self):
        catalog, by_name = owner.checked_catalog(transfer.reference().read_bytes())
        expected = transfer.manifest()["libraries"]["mashru"]
        self.assertEqual(set(expected["theorems"]), set(by_name))
        self.assertEqual(sum(catalog["scope_counts"].values()), len(by_name))
        self.assertEqual(catalog["core_catalog_sha256"],
                         transfer.core.file_sha(transfer.reference().with_name("proof_catalog.json")))
        self.assertEqual(set(expected["research_countermodels"]),
                         {key for key, row in by_name.items() if row["scope"] == "research-countermodel"})
        self.assertNotIn("A116.Tayy.ofIntiqal", by_name)
        self.assertEqual("existing-a116", by_name["A116.run_nil"]["scope"])
        with self.assertRaises(ValueError):
            owner.checked_catalog(gzip.compress(b'{}'))

    def test_gateway_lookup_binds_the_exact_name(self):
        task = lesson("lookup", theorem="Nizam.Athar.la_tarqiya")
        request = ntp.request("cognitive.lesson", {"lesson": task})
        output = gateway.run(request)
        self.assertTrue(gateway.accept_output(output, expected_request=request)["valid"])
        self.assertEqual(teaching.run_lesson(task)["theorem"]["module"], "Nizam.Athar")
        other = ntp.request("cognitive.lesson", {"lesson": dict(task, theorem="A116.run_nil")})
        self.assertFalse(gateway.accept_output(output, expected_request=other)["valid"])
        self.assertEqual(teaching.run_lesson(dict(task, theorem="Unbound.proof"))["status"], "UNKNOWN_THEOREM")

    def test_dependency_proposals_never_set_compiled_membership(self):
        _, by_name = owner.checked_catalog(transfer.reference().read_bytes())
        source = next(row for row in by_name.values() if row["scope"] == "imported"
                      and any(target in by_name for target in row["proof_dependencies"]))
        target = next(n for n in source["proof_dependencies"] if n in by_name)
        task = lesson("dependency", theorem=source["name"], candidate=target)
        measured = teaching.run_lesson(task)
        self.assertTrue(measured["named_in_proof_term"])
        from tools.lexical_training import mashru_dependencies
        with patch.object(mashru_dependencies, "MODEL", Path("/nonexistent/mashru-model.json")):
            missing = teaching.run_lesson(task)
        self.assertEqual(missing["proposal_status"], "MODEL_UNAVAILABLE")
        self.assertTrue(missing["named_in_proof_term"])
        self.assertTrue(missing["execution_measured"])
        self.assertEqual(measured["proposal_authority"], "NONE")
        other = next(n for n in by_name if n not in source["proof_dependencies"])
        absent = teaching.run_lesson(dict(task, candidate=other))
        self.assertFalse(absent["named_in_proof_term"])
        self.assertTrue(teaching.verify_lesson(absent, expected_lesson=dict(task, candidate=other))["valid"])
        self.assertFalse(teaching.verify_lesson(measured, expected_lesson=dict(task, candidate=other))["valid"])

    def test_no_trace_when_native_missing_or_input_has_another_record(self):
        task = lesson("read", source_id="test", text="هَلْ ذَهَبَ الْوَلَدُ")
        with patch.object(owner, "NATIVE", Path("/nonexistent/mashruAthar")):
            self.assertFalse(teaching.run_lesson(task)["execution_measured"])
        self.assertEqual(teaching.run_lesson(dict(task, text="أ\n1\tب"))["status"], "INVALID_INPUT")
        self.assertEqual(teaching.run_lesson(dict(task, theorem="Nizam.Athar.la_tarqiya"))["status"], "INVALID_INPUT")

    @unittest.skipUnless(owner.NATIVE.is_file(), "compile mashruAthar for native replay")
    def test_source_contrasts_and_independent_replay(self):
        task = lesson("read", source_id="درس", text="ذَهَبَ الْوَلَدُ")
        actual = teaching.run_lesson(task)
        self.assertEqual(actual["trace"]["QUWWA"][0][0], "خبرٌ مثبت")
        self.assertEqual(actual["neural_proposal"]["authority"], "NONE")
        self.assertTrue(teaching.verify_lesson(actual, expected_lesson=task)["valid"])
        question = dict(task, text="هَلْ ذَهَبَ الْوَلَدُ")
        result = teaching.run_lesson(question)
        self.assertEqual(result["trace"]["QUWWA"][0][0], "إنشاء")
        self.assertFalse(result["world_truth_established"])
        self.assertIn("MAFHUM", result["trace"])
        self.assertFalse(teaching.verify_lesson(actual, expected_lesson=question)["valid"])
        request = ntp.request("cognitive.lesson", {"lesson": question})
        report = gateway.run(request)
        self.assertTrue(gateway.accept_output(report, expected_request=request)["valid"])

    def test_readout_beats_majority_on_separate_sentence_bodies(self):
        from tools.lexical_training import mashru_readout as head
        held = json.loads(head.MODEL.read_bytes())["heldout"]
        self.assertTrue(set(head.examples(head.TRAIN)).isdisjoint(head.examples(head.TEST)))
        self.assertGreater(held["correct"], held["majority_correct"])
