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
        self.root_inputs = {"root_source": self.roots, "expected_root_blob": blob(self.roots)}
        self.lexical = source("فتح: تعريف اصطناعي لا يعد شاهدًا معجميًا.")
        self.proposal = a.make_proposal(self.rows[0], self.lexical, "فتح", "fixture.opening.1", 0,
                                        len(self.lexical.body), "author", **self.root_inputs)

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
        self.assertTrue(a.check_proposal(self.proposal, self.rows[0], self.lexical, **self.root_inputs))
        self.assertEqual(self.proposal["authority"], "NONE")
        self.assertEqual(self.proposal["status"], "PROPOSED_ONLY")

    def test_modified_proposal_rejected_even_rehashed(self):
        p = copy.deepcopy(self.proposal)
        p["status"] = "ACCEPT"
        p["proposal_digest"] = a.digest({k: v for k, v in p.items() if k != "proposal_digest"})
        self.assertFalse(a.check_proposal(p, self.rows[0], self.lexical, **self.root_inputs))

    def test_modified_source_cannot_reuse_proposal(self):
        self.assertFalse(a.check_proposal(self.proposal, self.rows[0], source("فتح: شاهد آخر."),
                                          **self.root_inputs))

    def test_proposal_cannot_be_rebound_to_another_root(self):
        self.assertFalse(a.check_proposal(self.proposal, self.rows[1], self.lexical, **self.root_inputs))

    def assert_record_rejected(self, record, **overrides):
        inputs = {**self.root_inputs, **overrides}
        with self.assertRaises(ValueError):
            a.make_proposal(record, self.lexical, "فتح", "fixture.opening.1", 0,
                            len(self.lexical.body), "author", **inputs)
        proposal = copy.deepcopy(self.proposal)
        proposal["root_record_id"] = record.get("id")
        proposal["proposal_digest"] = a.digest({k: v for k, v in proposal.items()
                                                if k != "proposal_digest"})
        self.assertFalse(a.check_proposal(proposal, record, self.lexical, **inputs))
        with self.assertRaisesRegex(ValueError, "PROPOSAL_REPLAY_MISMATCH"):
            a.review_event(proposal, record, self.lexical, "reviewer", "DEFER", "why",
                           frozenset({"reviewer"}), **inputs)

    def test_independent_root_inputs_are_required(self):
        with self.assertRaises(TypeError):
            a.make_proposal(self.rows[0], self.lexical, "فتح", "s", 0,
                            len(self.lexical.body), "author")
        with self.assertRaises(TypeError):
            a.check_proposal(self.proposal, self.rows[0], self.lexical)
        with self.assertRaises(TypeError):
            a.review_event(self.proposal, self.rows[0], self.lexical, "reviewer", "DEFER", "why",
                           frozenset({"reviewer"}))

    def test_self_hashed_minimal_record_has_no_source_membership(self):
        self.assert_record_rejected({"status": "SOURCE_LISTED_ONLY", "id": a.digest(None)})

    def test_all_derived_record_fields_are_replayed(self):
        mutations = {"form": "كتب", "length": 4, "source_line": 5,
                     "numeric_identity_hex": "1", "outside_alphabet": ["ف"],
                     "status": "ACCEPT", "sense_ids": ["invented.sense"],
                     "residuals": [], "authority": "LICENSED", "extra": False}
        for key, value in mutations.items():
            with self.subTest(field=key):
                record = copy.deepcopy(self.rows[0])
                record[key] = value
                self.assert_record_rejected(record)
        record = copy.deepcopy(self.rows[0])
        del record["outside_alphabet"]
        self.assert_record_rejected(record)

    def test_rehashed_occurrence_forgery_still_fails_source_replay(self):
        record = copy.deepcopy(self.rows[0])
        record["identity"]["span"]["quote"] = "كتب"
        record["form"] = "كتب"
        record["id"] = a.digest(record["identity"])
        record["numeric_identity_hex"] = format(a.fold(record["identity"]), "x")
        self.assert_record_rejected(record)

    def test_root_blob_cannot_be_replaced_by_a_self_consistent_source(self):
        other = source(self.roots.body.decode() + "كتب\n", self.roots.source_id)
        other_rows, _ = a.inventory(other, blob(other))
        self.assert_record_rejected(other_rows[0], root_source=other)
        self.assert_record_rejected(self.rows[0], expected_root_blob="0" * 40)

    def test_same_root_bytes_cannot_substitute_source_metadata(self):
        for field in ("source_id", "revision", "domain"):
            with self.subTest(field=field):
                other = replace(self.roots, **{field: "another-source-value"})
                self.assert_record_rejected(self.rows[0], root_source=other)

    def test_repeated_roots_keep_exact_occurrence_identity(self):
        second = self.rows[3]
        proposal = a.make_proposal(second, self.lexical, "فتح", "fixture.opening.1", 0,
                                   len(self.lexical.body), "author", **self.root_inputs)
        self.assertTrue(a.check_proposal(proposal, second, self.lexical, **self.root_inputs))
        self.assertFalse(a.check_proposal(self.proposal, second, self.lexical, **self.root_inputs))
        self.assertNotEqual(proposal["root_record_id"], self.proposal["root_record_id"])
        mixed = copy.deepcopy(second)
        mixed["source_line"] = self.rows[0]["source_line"]
        self.assert_record_rejected(mixed)

    def test_record_canonical_comparison_rejects_boolean_numbers(self):
        roots = source("ب\n", "single-letter-fixture")
        rows, _ = a.inventory(roots, blob(roots))
        self.assertEqual(rows[0]["source_line"], 1)
        self.assertEqual(rows[0]["length"], 1)
        for field in ("source_line", "length"):
            with self.subTest(field=field):
                record = copy.deepcopy(rows[0])
                record[field] = True
                self.assert_record_rejected(record, root_source=roots, expected_root_blob=blob(roots))

    def test_lemma_requires_byte_anchored_quote(self):
        with self.assertRaisesRegex(ValueError, "LEMMA_NOT_PRESENT"):
            a.make_proposal(self.rows[0], self.lexical, "كتب", "s", 0, len(self.lexical.body), "a",
                            **self.root_inputs)

    def test_review_is_a_record_not_a_certificate(self):
        e = a.review_event(self.proposal, self.rows[0], self.lexical, "reviewer",
                           "REQUEST_OWNER_REPLAY", "fixture-only", frozenset({"reviewer"}),
                           **self.root_inputs)
        self.assertEqual(e["admission"], "NOT_ADMITTED")
        self.assertEqual(e["authority"], "NONE")

    def test_self_review_forbidden(self):
        with self.assertRaisesRegex(ValueError, "INDEPENDENT_REVIEWER"):
            a.review_event(self.proposal, self.rows[0], self.lexical, "author", "DEFER", "why",
                           frozenset({"author"}), **self.root_inputs)

    def test_unknown_reviewer_forbidden(self):
        with self.assertRaises(ValueError):
            a.review_event(self.proposal, self.rows[0], self.lexical, "unknown", "DEFER", "why",
                           frozenset(), **self.root_inputs)

    def test_review_cannot_issue_license(self):
        with self.assertRaisesRegex(ValueError, "CANNOT_GRANT"):
            a.review_event(self.proposal, self.rows[0], self.lexical, "reviewer", "ACCEPT", "why",
                           frozenset({"reviewer"}), **self.root_inputs)

    def test_gateway_plan_uses_only_existing_input_boundary(self):
        plan = a.gateway_plan(self.lexical, 0, len(self.lexical.body))
        self.assertTrue(a.check_plan(plan, self.lexical))
        self.assertEqual(set(plan["request"]), {"schema", "route", "payload"})
        self.assertEqual(plan["request"]["route"], "text.read")
        self.assertEqual(plan["execution"], "NOT_RUN")
        self.assertFalse(plan["verified"])

    def test_gateway_plan_rejects_inputs_outside_installed_reader_contract(self):
        invalid_texts = (" \t\n", "." * 8193, " ".join(["ب"] * 129), "ب" * 129)
        for text in invalid_texts:
            with self.subTest(byte_count=len(text.encode()), prefix=text[:20]):
                src = source(text)
                with self.assertRaises(ValueError):
                    a.gateway_plan(src, 0, len(src.body))
                # Rehash a legacy-shaped plan to show replay enforces input validity.
                plan = a.gateway_plan(self.lexical, 0, len(self.lexical.body))
                plan["span"] = src.span(0, len(src.body))
                plan["request"]["payload"]["text"] = text
                plan["request_sha256"] = a.digest(plan["request"])
                self.assertFalse(a.check_plan(plan, src))

    def test_gateway_plan_accepts_exact_reader_boundaries_without_truncation(self):
        texts = ("ب" * 128, " ".join(["ب"] * 128), "ب" * 128 + "." * (8192 - 256))
        for text in texts:
            with self.subTest(byte_count=len(text.encode())):
                src = source(text)
                plan = a.gateway_plan(src, 0, len(src.body))
                self.assertTrue(a.check_plan(plan, src))
                self.assertEqual(plan["request"]["payload"]["text"].encode(), src.body)
                self.assertEqual(plan["span"]["quote"].encode(), src.body)
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
        self.assertFalse(a.check_proposal(p, self.rows[0], self.lexical, **self.root_inputs))


if __name__ == "__main__":
    unittest.main()
