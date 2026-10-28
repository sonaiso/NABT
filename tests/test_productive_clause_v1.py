"""Independent development examples and trust-boundary counterexamples.

These are not the frozen 200-case acceptance matrix. Controlled dependency
doubles exercise failure propagation; native tests require the real executables.
"""
from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import productive_clause_v1 as clause

ROOT = Path(__file__).resolve().parents[1]
BINDING = dict(source_id="clause-test", revision="1", scope="utterance",
               ending="wasl", onset="word_initial")
TEXT = "ضَرَبَ زَيْدٌ عَمْرًا."
NATIVE = clause._NATIVE_PATH.is_file()
COMPOSITE = NATIVE and (ROOT / "formal/.lake/build/bin/connectedAcquisitionV3").is_file()


def controlled_acquisition(text=TEXT, binding=None):
    """A dependency double for gates only; never an acceptance oracle."""
    binding = BINDING if binding is None else binding
    proposal = clause.propose_clause(text, **binding)
    words = [{key: token[key] for key in clause._COORDS} for token in proposal["tokens"]]
    return {"status": "ACQUIRED", "verified": True, "shape_verified": True,
            "acquisition": {"text": text, **binding, "words": words}}


class ProposalTests(unittest.TestCase):
    def test_roles_follow_case_in_both_orders_and_keep_occurrences(self):
        examples = ((TEXT, "ZAYD", "AMR", 1, 2, "VSO"),
                    ("ضَرَبَ عَمْرًا زَيْدٌ.", "ZAYD", "AMR", 2, 1, "VOS"),
                    ("ضَرَبَ بَكْرًا سَعِيدٌ", "SAID", "BAKR", 2, 1, "VOS"),
                    ("ضَرَبَ زَيْدٌ زَيْدًا", "ZAYD", "ZAYD", 1, 2, "VSO"))
        for text, subject, obj, si, oi, order in examples:
            result = clause.propose_clause(text, **BINDING)
            reading = result["reading"]
            self.assertEqual(result["status"], "LICENSED_CLAUSE")
            self.assertEqual((reading["subject_lexeme"], reading["object_lexeme"],
                              reading["subject_index"], reading["object_index"], reading["order"]),
                             (subject, obj, si, oi, order))
            self.assertEqual(reading["subject_case"], "nom")
            self.assertEqual(reading["object_case"], "acc")
            self.assertEqual(reading["subject_source"], result["tokens"][si])
            self.assertEqual(reading["object_source"], result["tokens"][oi])
            self.assertIsNone(reading["referents"])
            self.assertIsNone(reading["world_truth"])
        duplicate = clause.propose_clause("ضَرَبَ زَيْدٌ زَيْدًا")["reading"]
        self.assertNotEqual(duplicate["subject_source"]["start"], duplicate["object_source"]["start"])

    def test_known_case_conflicts_reject_only_the_scoped_frame(self):
        for text in ("ضَرَبَ زَيْدٌ بَكْرٌ.", "ضَرَبَ عَمْرًا زَيْدًا."):
            result = clause.propose_clause(text)
            self.assertEqual(result["status"], "REJECTED_IN_SCOPE")
            self.assertEqual(result["reason"], "ROLE_CASE_CONFLICT")
            self.assertIsNone(result["reading"])

    def test_unknown_forms_other_structures_boundaries_and_modes_defer(self):
        examples = ("ضَرَبَ قَيْسًا زَيْدٌ.", "ضَرَبَ عَمْرٌو زَيْدًا.",
                    "ضرب زيد عمرا", "ضُرِبَ زَيْدٌ عَمْرًا.", "زَيْدٌ ضَرَبَ عَمْرًا.",
                    "ضَرَبَ زَيْدٌ عَمْرًا الْيَوْمَ", "ضَرَبَ زَيْدٌ، عَمْرًا.",
                    "ضَرَبَ\nزَيْدٌ عَمْرًا.", "«ضَرَبَ زَيْدٌ عَمْرًا»", TEXT + ".", "")
        for text in examples:
            result = clause.propose_clause(text)
            self.assertEqual(result["status"], "DEFER", text)
            self.assertIsNone(result["reading"])
        for change in ({"ending": "waqf"}, {"onset": "connected"}):
            result = clause.propose_clause(TEXT, **change)
            self.assertEqual(result["reason"], "MODE_OUTSIDE_DECLARED_SCOPE")

    def test_source_pieces_and_role_spans_restore_original_bytes(self):
        text = " \tضَرَبَ\tخَالِدًا  قَيْسٌ.\t "
        result = clause.propose_clause(text)
        self.assertEqual("".join(p["raw"] for p in result["source_pieces"]), text)
        for span in result["source_pieces"] + result["tokens"]:
            self.assertEqual(text[span["start"]:span["end"]], span["raw"])
            self.assertEqual(text.encode()[span["byte_start"]:span["byte_end"]].decode(), span["raw"])
        self.assertEqual(result["reading"]["subject_source"]["raw"], "قَيْسٌ")
        self.assertEqual(result["reading"]["object_source"]["raw"], "خَالِدًا")

    def test_invalid_request_fails_before_any_dependency(self):
        with patch.object(clause.acquisition, "read_acquired") as dependency:
            for field in BINDING:
                for value in (True, 3, [], None, "", "x\x85"):
                    args = {**BINDING, field: value}
                    self.assertEqual(clause.evaluate(TEXT, **args)["status"], "INVALID_INPUT")
            for text in (True, {}, 1, b"\xff", "\ud800"):
                self.assertEqual(clause.evaluate(text)["status"], "INVALID_INPUT")
            for text in ("ق" * 4097, b"a" * 8193):
                self.assertEqual(clause.evaluate(text)["status"], "RESOURCE_EXHAUSTED")
        dependency.assert_not_called()


class ScopeAndGateTests(unittest.TestCase):
    def run_controlled(self, *, acquired=None, native=None, evidence=None, text=TEXT):
        acq = controlled_acquisition(text) if acquired is None else acquired
        proposed = clause.propose_clause(text, **BINDING) if native is None else native
        evidence = {"authority": "TEST_DOUBLE_NOT_SOURCE_EVIDENCE"} if evidence is None else evidence
        with patch.object(clause, "source_inventory", return_value=evidence), \
             patch.object(clause.acquisition, "read_acquired", return_value=acq), \
             patch.object(clause, "_native", return_value=proposed):
            return clause.evaluate(text, **BINDING)

    def test_source_packet_opens_retained_bytes_not_only_excerpt_hashes(self):
        inventory = clause.source_inventory()
        self.assertEqual(inventory["authority"], "SOURCE_IDENTITY_AND_AUTHORED_SCOPE")
        self.assertEqual(inventory["sources"], 2)
        self.assertEqual(inventory["passages"], 8)
        original = clause.acquisition._read_bounded
        def changed(path, limit):
            raw = original(path, limit)
            return raw + b" " if path.name == "qatr.txt" else raw
        with patch.object(clause.acquisition, "_read_bounded", side_effect=changed):
            with self.assertRaises(ValueError):
                clause.source_inventory()
        with patch.object(clause, "SOURCE_SCOPE_SHA256", "0" * 64):
            with self.assertRaises(ValueError):
                clause.source_inventory()

    def test_acquisition_shape_binding_and_span_debt_block_root_reading(self):
        for mutation in (lambda a: a.update(status="DEFER"),
                         lambda a: a.update(verified=False),
                         lambda a: a.update(shape_verified=False),
                         lambda a: a["acquisition"].update(scope="another"),
                         lambda a: a["acquisition"]["words"][1].update(start=0)):
            acquired = controlled_acquisition()
            mutation(acquired)
            result = self.run_controlled(acquired=acquired)
            self.assertFalse(result["verified"])
            self.assertFalse(result["chain_complete"])
            self.assertIsNone(result["reading"])
            self.assertEqual(result["candidate_space"]["count"], 1)
            self.assertEqual(result["candidate_space"]["candidates"][0]["state"], "PENDING")
            self.assertTrue(result["candidate_space"]["candidates"][0]["obligations"])

    def test_own_source_failure_preserves_only_the_structural_diagnostic(self):
        with patch.object(clause, "source_inventory", side_effect=FileNotFoundError()), \
             patch.object(clause.acquisition, "read_acquired", return_value=controlled_acquisition()), \
             patch.object(clause, "_native", return_value=clause.propose_clause(TEXT, **BINDING)):
            result = clause.evaluate(TEXT, **BINDING)
        self.assertEqual(result["status"], "SOURCE_EVIDENCE_UNAVAILABLE")
        self.assertFalse(result["gates"]["source_evidence_checked"])
        self.assertEqual(result["candidate_space"]["count_mode"], "EXACT")
        self.assertEqual(result["candidate_space"]["candidates"][0]["state"], "PENDING")
        self.assertIsNone(result["reading"])

    def test_missing_native_and_changed_native_output_have_no_count_or_claim(self):
        for error, status in ((FileNotFoundError(), "VERIFICATION_UNAVAILABLE"),
                              (ValueError(), "VERIFICATION_FAILED"),
                              (OverflowError(), "RESOURCE_EXHAUSTED")):
            with patch.object(clause, "source_inventory", return_value={"test": True}), \
                 patch.object(clause.acquisition, "read_acquired", return_value=controlled_acquisition()), \
                 patch.object(clause, "_native", side_effect=error):
                result = clause.evaluate(TEXT, **BINDING)
            self.assertEqual(result["status"], status)
            self.assertIsNone(result["candidate_space"]["count"])
            self.assertIsNone(result["reading"])
        forged = clause.propose_clause(TEXT, **BINDING)
        forged["reading"]["subject_index"] = True
        result = self.run_controlled(native=forged)
        self.assertEqual(result["status"], "VERIFICATION_FAILED")
        self.assertIsNone(result["syntax"]["native_result"])

    def test_empty_and_unknown_candidate_spaces_are_not_false_certainty(self):
        rejected = self.run_controlled(text="ضَرَبَ زَيْدٌ بَكْرٌ")
        self.assertEqual(rejected["candidate_space"]["count"], 0)
        self.assertIsNone(rejected["candidate_space"]["hartley_bits"])
        self.assertFalse(rejected["chain_complete"])
        unknown = self.run_controlled(text="ضَرَبَ قَيْسًا زَيْدٌ")
        self.assertIsNone(unknown["candidate_space"]["count"])
        self.assertEqual(unknown["candidate_space"]["count_mode"], "UNMEASURED")
        self.assertFalse(unknown["chain_complete"])

    def test_receipt_byte_budget_stops_before_replay_and_preserves_invalidity(self):
        with patch.object(clause, "evaluate") as replay:
            oversized = {"payload": "x" * clause.MAX_REPORT_BYTES}
            self.assertEqual(clause.verify(oversized, text=TEXT, **BINDING),
                             {"valid": False, "replay_matches": False, "status": "RESOURCE_EXHAUSTED"})
            for malformed in ([], {0: "key"}, {"payload": float("nan")}):
                self.assertEqual(clause.verify(malformed, text=TEXT, **BINDING)["status"], "INVALID_RECEIPT")
            replay.assert_not_called()


@unittest.skipUnless(NATIVE, "build productiveClauseV1")
class NativeClauseTests(unittest.TestCase):
    def test_native_replay_statuses_and_source_projection(self):
        cases = (TEXT, "ضَرَبَ عَمْرًا زَيْدٌ", "ضَرَبَ زَيْدٌ بَكْرٌ", "ضَرَبَ زَيْدًا عَمْرًا",
                 "ضَرَبَ قَيْسًا زَيْدٌ", " \tضَرَبَ خَالِدًا سَعِيدٌ. ", "", "ضَرَبَ\nزَيْدٌ عَمْرًا.")
        for text in cases:
            for change in ({}, {"ending": "waqf"}, {"onset": "connected"}):
                binding = {**BINDING, **change}
                proposal = clause.propose_clause(text, **binding)
                self.assertEqual(clause._wire(clause._native({"text": text, **binding})), clause._wire(proposal))

    def test_native_transport_rejects_malformed_request_without_linguistic_claim(self):
        raw = json.dumps({"text": TEXT, **BINDING}, ensure_ascii=False).encode()
        payloads = (b"\xff", raw[:-1] + b',"scope":"other"}',
                    json.dumps({"text": TEXT, **BINDING, "source_id": True}).encode(),
                    raw[:-1] + b',"extra":1}')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            for payload in payloads:
                path.write_bytes(payload)
                result = subprocess.run([str(clause._NATIVE_PATH), str(path)], capture_output=True, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stdout)["status"], "INVALID_INPUT")


@unittest.skipUnless(COMPOSITE, "build connectedAcquisitionV3 and productiveClauseV1")
class CheckedChainTests(unittest.TestCase):
    def test_central_sentence_and_vos_have_all_checked_gates_and_no_extra_authority(self):
        for text, si, oi in ((TEXT, 1, 2), ("ضَرَبَ عَمْرًا زَيْدٌ.", 2, 1)):
            result = clause.evaluate(text.encode(), **BINDING)
            self.assertEqual(result["status"], "LICENSED_CLAUSE", result["blocked_by"])
            self.assertTrue(result["verified"] and result["chain_complete"])
            self.assertEqual(set(result["gates"]), set(clause.GATE_NAMES))
            self.assertTrue(all(result["gates"].values()))
            self.assertEqual((result["reading"]["subject_index"], result["reading"]["object_index"]), (si, oi))
            self.assertEqual([w["cells"] for w in result["acquisition"]["acquisition"]["words"]],
                             [[56, 36, 4], [40, 111, 29, 99], [68, 95, 36, 99]] if si == 1 else
                             [[56, 36, 4], [68, 95, 36, 99], [40, 111, 29, 99]])
            for flag in ("world_truth_established", "referents_established", "entails_exclusivity", "all_arabic_complete"):
                self.assertIs(result[flag], False)
            self.assertEqual(result["candidate_space"]["candidates"][0]["state"], "LICENSED")

    def test_receipt_replay_checks_all_binding_fields_and_typed_projection(self):
        report = clause.evaluate(TEXT, **BINDING)
        self.assertTrue(clause.verify(report, text=TEXT, **BINDING)["valid"])
        for key, value in (("source_id", "another"), ("revision", "next"), ("scope", "another"),
                           ("ending", "waqf"), ("onset", "connected")):
            self.assertFalse(clause.verify(report, text=TEXT, **{**BINDING, key: value})["valid"])
        for mutation in (lambda r: r["reading"].update(subject_index=True),
                         lambda r: r["reading"]["subject_source"].update(start=14),
                         lambda r: r.update(entails_exclusivity=True),
                         lambda r: r["candidate_space"].update(count=True)):
            changed = deepcopy(report)
            mutation(changed)
            verified = clause.verify(changed, text=TEXT, **BINDING)
            self.assertFalse(verified["valid"])
            self.assertFalse(verified["replay_matches"])
        for invalid in ([], True, {0: "key"}, {"x": float("nan")}, {"x": ()}):
            self.assertEqual(clause.verify(invalid, text=TEXT, **BINDING)["status"], "INVALID_RECEIPT")

    def test_exact_negative_receipt_replay_does_not_authorize_a_reading(self):
        text = "ضَرَبَ زَيْدٌ بَكْرٌ"
        report = clause.evaluate(text, **BINDING)
        self.assertEqual(report["status"], "REJECTED_IN_SCOPE")
        result = clause.verify(report, text=text, **BINDING)
        self.assertTrue(result["replay_matches"])
        self.assertFalse(result["valid"])

    def test_cli_receipt_roundtrip_and_nonzero_failed_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            document, receipt = Path(directory) / "input.txt", Path(directory) / "receipt.json"
            document.write_text(TEXT)
            base = [sys.executable, "-B", "-m", "tools.productive_clause_cli"]
            read = subprocess.run(base + ["read", str(document)], cwd=ROOT, capture_output=True, check=False)
            self.assertEqual(read.returncode, 0, read.stderr.decode())
            receipt.write_bytes(read.stdout)
            checked = subprocess.run(base + ["verify", str(receipt), "--source", str(document)],
                                     cwd=ROOT, capture_output=True, check=False)
            self.assertEqual(checked.returncode, 0, checked.stderr.decode())
            document.write_text("ضَرَبَ زَيْدٌ بَكْرٌ")
            denied = subprocess.run(base + ["read", str(document)], cwd=ROOT, capture_output=True, check=False)
            self.assertEqual(denied.returncode, 2)
            self.assertFalse(json.loads(denied.stdout)["chain_complete"])


if __name__ == "__main__":
    unittest.main()
