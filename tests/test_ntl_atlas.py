"""Boundary and mutation tests for staging, not linguistic truth tests."""
import copy
import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from tools import ntl_atlas as a


def source(text, sid="fixture-source", domain="synthetic-atlas-v1"):
    raw = text.encode("utf-8")
    return a.Source(sid, "fixture-v1", raw, hashlib.sha256(raw).hexdigest(), domain, "fixture-not-lexicon")


def blob(src):
    return hashlib.sha1(b"blob " + str(len(src.body)).encode() + b"\0" + src.body).hexdigest()


class AtlasTests(unittest.TestCase):
    def setUp(self):
        self.roots = source("# authored inventory\nفتح\nدحرج\nحتى\nفتح\n", "roots-fixture")
        self.rows, self.summary = a.inventory(self.roots, blob(self.roots))
        self.lexical = source("فتح: تعريف اصطناعي لا يعد شاهدًا معجميًا.")
        self.proposal = a.make_proposal(self.rows[0], self.lexical, "فتح", "fixture.opening.1", 0,
                                        len(self.lexical.body), "author")

    def test_enumeration_keeps_every_occurrence(self):
        self.assertEqual(self.summary["rows"], 4)
        self.assertEqual(self.summary["unique_forms"], 3)
        self.assertNotEqual(self.rows[0]["id"], self.rows[3]["id"])
        self.assertEqual(self.summary["character_review_rows"], 1)
        self.assertEqual(self.rows[2]["form"], "حتى")

    def test_root_inventory_never_selects_a_sense(self):
        for row in self.rows:
            self.assertEqual(row["sense_ids"], [])
            self.assertEqual(row["authority"], "NONE")
        self.assertEqual(self.summary["senses_reviewed"], 0)

    def test_root_identity_roundtrip(self):
        for row in self.rows:
            self.assertEqual(a.unfold(int(row["numeric_identity_hex"], 16)), row["identity"])

    def test_reject_wrong_blob(self):
        with self.assertRaisesRegex(ValueError, "INVENTORY_BLOB"):
            a.inventory(self.roots, "0" * 40)

    def test_reject_wrong_source_hash(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_HASH"):
            replace(self.lexical, body=b"changed")

    def test_reject_implicit_whitespace_normalization(self):
        src = source("فتح \n")
        with self.assertRaisesRegex(ValueError, "WHITESPACE"):
            a.inventory(src, blob(src))

    def test_utf8_span_rejects_partial_letter(self):
        with self.assertRaises(UnicodeError):
            self.lexical.span(1, 4)

    def test_span_rejects_bool_or_empty(self):
        for start, stop in ((True, 4), (0, False), (2, 2), (-1, 4)):
            with self.assertRaises(ValueError):
                self.lexical.span(start, stop)

    def test_proposal_preserves_source_and_no_authority(self):
        self.assertTrue(a.check_proposal(self.proposal, self.rows[0], self.lexical))
        self.assertEqual(self.proposal["authority"], "NONE")
        self.assertEqual(self.proposal["status"], "PROPOSED_ONLY")

    def test_modified_proposal_rejected_even_rehashed(self):
        p = copy.deepcopy(self.proposal)
        p["status"] = "ACCEPT"
        p["proposal_digest"] = a.digest({k: v for k, v in p.items() if k != "proposal_digest"})
        self.assertFalse(a.check_proposal(p, self.rows[0], self.lexical))

    def test_modified_source_cannot_reuse_proposal(self):
        self.assertFalse(a.check_proposal(self.proposal, self.rows[0], source("فتح: شاهد آخر.")))

    def test_proposal_cannot_be_rebound_to_another_root(self):
        self.assertFalse(a.check_proposal(self.proposal, self.rows[1], self.lexical))

    def test_lemma_requires_byte_anchored_quote(self):
        with self.assertRaisesRegex(ValueError, "LEMMA_NOT_PRESENT"):
            a.make_proposal(self.rows[0], self.lexical, "كتب", "s", 0, len(self.lexical.body), "a")

    def test_review_is_a_record_not_a_certificate(self):
        e = a.review_event(self.proposal, self.rows[0], self.lexical, "reviewer",
                           "REQUEST_OWNER_REPLAY", "fixture-only", frozenset({"reviewer"}))
        self.assertEqual(e["admission"], "NOT_ADMITTED")
        self.assertEqual(e["authority"], "NONE")

    def test_self_review_forbidden(self):
        with self.assertRaisesRegex(ValueError, "INDEPENDENT_REVIEWER"):
            a.review_event(self.proposal, self.rows[0], self.lexical, "author", "DEFER", "why", frozenset({"author"}))

    def test_unknown_reviewer_forbidden(self):
        with self.assertRaises(ValueError):
            a.review_event(self.proposal, self.rows[0], self.lexical, "unknown", "DEFER", "why", frozenset())

    def test_review_cannot_issue_license(self):
        with self.assertRaisesRegex(ValueError, "CANNOT_GRANT"):
            a.review_event(self.proposal, self.rows[0], self.lexical, "reviewer", "ACCEPT", "why", frozenset({"reviewer"}))

    def test_gateway_plan_uses_only_existing_input_boundary(self):
        plan = a.gateway_plan(self.lexical, 0, len(self.lexical.body))
        self.assertTrue(a.check_plan(plan, self.lexical))
        self.assertEqual(set(plan["request"]), {"schema", "route", "payload"})
        self.assertEqual(plan["request"]["route"], "text.read")
        self.assertEqual(plan["execution"], "NOT_RUN")
        self.assertFalse(plan["verified"])

    def test_fake_gateway_execution_is_rejected(self):
        plan = a.gateway_plan(self.lexical, 0, len(self.lexical.body))
        plan["execution"] = "EXECUTED"
        plan["verified"] = True
        self.assertFalse(a.check_plan(plan, self.lexical))

    def test_request_substitution_is_rejected(self):
        plan = a.gateway_plan(self.lexical, 0, len(self.lexical.body))
        plan["request"]["payload"]["text"] = "claim not in source"
        plan["request_sha256"] = a.digest(plan["request"])
        self.assertFalse(a.check_plan(plan, self.lexical))

    def test_freeze_refuses_history_replacement(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "history.json"
            a.freeze(p, {"n": 1})
            before = p.read_bytes()
            with self.assertRaises(FileExistsError):
                a.freeze(p, {"n": 2})
            self.assertEqual(p.read_bytes(), before)

    def test_noncanonical_json_and_float_refused(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1.5}'):
            with self.assertRaises(ValueError):
                a.decode_json(raw)

    def test_invalid_numbers_refused(self):
        for number in (True, 0, -1, 1.0):
            with self.assertRaises(ValueError):
                a.unfold(number)

    def test_forged_receipt_can_fold_but_not_pass_plan_check(self):
        plan = a.gateway_plan(self.lexical, 0, len(self.lexical.body))
        plan["authority"] = "ALL_KNOWLEDGE"
        self.assertEqual(a.unfold(a.fold(plan)), plan)
        self.assertFalse(a.check_plan(plan, self.lexical))

    def test_packet_depth_limit(self):
        packet = {}
        for _ in range(34):
            packet = {"x": packet}
        with self.assertRaisesRegex(ValueError, "DEPTH"):
            a.canonical(packet)

    def test_neural_score_does_not_change_review_authority(self):
        p = copy.deepcopy(self.proposal)
        p["neural_score"] = 1
        self.assertFalse(a.check_proposal(p, self.rows[0], self.lexical))


if __name__ == "__main__":
    unittest.main()
