"""Admission of the learned passive relation into the single text reader."""
from copy import deepcopy
from hashlib import sha256
from unittest import TestCase, mock, skipUnless

from tools.grammar_catalog import gateway, text_reading
from tools.lexical_training import passive_transfer

READY = all((text_reading.ROOT / "formal/.lake/build/bin" / name).is_file()
            for name in ("alignedAcquisition", "progressiveUnitProbe", "connectedAcquisitionV3",
                         "linguisticTruth", "lexicalDenotation"))


def read_slice(text, failures=()):
    source = {"id": "input", "sha256": sha256(text.encode()).hexdigest()}
    return text_reading.passive_reading(text, source, failures)


class SourceVersusProposal(TestCase):
    def test_withdrawal_of_model_preserves_independent_witness(self):
        text = "فُتِح الباب"
        unavailable = {"status": "MODEL_UNAVAILABLE"}
        with mock.patch.object(passive_transfer, "propose", return_value=unavailable):
            cards, transfer = read_slice(text)
        self.assertEqual(transfer["comparison"], "MODEL_UNAVAILABLE")
        self.assertEqual([c["evidence"]["relation"] for c in cards], ["ASSERT_PASSIVE"])

    def test_wrong_relation_or_span_cannot_authorize_a_reading(self):
        text = "فُتِح الباب"
        cards, _ = read_slice(text)
        ev = cards[0]["evidence"]
        good = {k: ev[k] for k in ("relation", "verb_span", "patient_span", "cue_span")}
        for correction in ({"relation": "DENY_PASSIVE"}, {"patient_span": ev["verb_span"]}):
            forged = {**good, **correction, "score": 1.0, "status": "PROPOSED",
                      "source_sha256": sha256(text.encode()).hexdigest()}
            with self.subTest(correction=correction), mock.patch.object(passive_transfer, "propose", return_value=forged):
                kept, transfer = read_slice(text)
                self.assertEqual(kept[0]["evidence"]["relation"], "ASSERT_PASSIVE")
                self.assertEqual(transfer["comparison"], "DIFFERS_FROM_SCOPED_READING")
                rejected, other = read_slice("هل فُتِح الباب؟")
                self.assertEqual(rejected, [])
                self.assertEqual(other["comparison"], "PROPOSAL_SOURCE_MISMATCH")

    def test_failed_source_check_is_distinct_from_ordinary_defer(self):
        location = {"span": {"source_id": "input"}, "observed": "الباب", "proposed": "الباب"}
        failures = [{"evidence": {"locations": [location]}}]
        self.assertEqual(read_slice("فُتِح الباب", failures)[0], [])
        self.assertEqual(read_slice("فُتِح الباب", failures)[1]["comparison"], "SOURCE_CHECK_UNAVAILABLE")
        location["proposed"] = "البابُ"
        self.assertTrue(read_slice("فُتِح الباب", failures)[0])


@skipUnless(READY, "Build the text.read native owners")
class GatewayReplay(TestCase):
    def test_genuine_pair_and_forged_witness(self):
        results = []
        for text in ("فُتِح الباب", "لم يُفتَح الباب"):
            req = {"schema": gateway.REQUEST_SCHEMA, "route": "text.read", "payload": {"text": text}}
            report = gateway.run(req)
            self.assertEqual(report["status"], "EXECUTED", report["execution"].get("code"))
            self.assertTrue(gateway.accept_output(report, expected_request=req)["valid"])
            owner = report["execution"]["owner_result"]
            row, = [c for c in owner["cards"] if c["scope"] == "source_event_relation"]
            ev = row["evidence"]
            start, end = ev["patient_span"]
            self.assertEqual(text.encode()[start:end].decode(), "الباب")
            self.assertFalse(owner["world_truth_established"])
            self.assertEqual(owner["passive_relation_transfer"]["neural_authority"], "NONE")
            results.append(ev)
        before, after = results
        self.assertEqual((before["event_sense_id"], before["patient_key"]),
                         (after["event_sense_id"], after["patient_key"]))
        self.assertEqual((before["relation"], after["relation"]), ("ASSERT_PASSIVE", "DENY_PASSIVE"))
        self.assertIsNone(before["cue_span"])
        a, b = after["cue_span"]
        self.assertEqual(text.encode()[a:b].decode(), "لم")
        tampered = deepcopy(report)
        card = next(c for c in tampered["execution"]["owner_result"]["cards"] if c["scope"] == "source_event_relation")
        card["evidence"]["patient_span"] = card["evidence"]["verb_span"]
        self.assertFalse(gateway.accept_output(tampered, expected_request=req)["valid"])
