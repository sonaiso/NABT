"""Independent source, ledger, guard-learning and Arabic replay checks.

Ported from three stdlib test modules at Qeyas commit
0ac045125f3d4ed9a984ab2f78a787fe9d014cd9; native resource checks added.
"""

from __future__ import annotations

import itertools
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from dataclasses import fields, replace
from pathlib import Path
from unittest.mock import patch

from nabt.errors import NabtError
from nabt.learning import (
    APPROVED_SOURCE_PINS,
    CheckStatus,
    EvidenceBinding,
    EvidenceLedger,
    EvidenceProposal,
    FeatureCase,
    FeatureSchema,
    Guard,
    GuardLanguage,
    LearningSession,
    LearningStatus,
    LicenseStatus,
    Observation,
    SixNounPilot,
    SourceBlob,
    SourceSpan,
    SourceStore,
    content_digest,
    default_pilot,
    evaluate_license,
    observation_schema,
    prescription_schema,
)
from nabt.learning.arabic_six_nouns import (
    read_observed_cue,
    read_observed_ending,
    read_prescription_marker,
    read_prescription_operation,
)
from tools.check_property_evidence_table import compare as compare_lean_table

class TestOriginalSourceIdentity(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = "# أَب\n~~ ذو مال\n".encode()
        self.blob = SourceBlob("book", self.raw)
        self.store = SourceStore({"book": self.blob})

    def test_original_bytes_and_utf8_span_survive_exactly(self) -> None:
        start = len(b"# ")
        end = start + len("أَب".encode())
        span = self.store.span("book", start, end)
        self.assertEqual(self.store.text(span), "أَب")
        self.assertEqual(self.blob.raw_bytes, self.raw)
        self.assertEqual(span.source_sha256, content_digest(self.raw))
        self.assertEqual(span.span_sha256, content_digest("أَب".encode()))

    def test_wrong_source_hash_identity_span_and_bounds_are_rejected(self) -> None:
        span = self.store.span("book", 2, len("# أَب".encode()))
        attacks = (
            replace(span, source_sha256="0" * 64),
            replace(span, source_id="other"),
            replace(span, span_sha256="1" * 64),
            replace(span, end=len(self.raw) + 1),
        )
        for attack in attacks:
            with self.subTest(attack=attack), self.assertRaises(ValueError):
                attack.extract(self.blob)
        with self.assertRaises(ValueError):
            span.extract(SourceBlob("book", self.raw.replace(b"#", b"!")))

    def test_codepoint_boundary_and_invalid_utf8_are_not_normalized_away(self) -> None:
        with self.assertRaises(UnicodeDecodeError):
            self.store.span("book", 3, 4)
        with self.assertRaises(UnicodeDecodeError):
            SourceBlob("bad", b"\xff")
        marked = SourceBlob("marked", "أب".encode())
        different = SourceBlob("marked", "أب".encode())
        self.assertNotEqual(marked.sha256, different.sha256)

    def test_full_pins_and_mask_types_are_required(self) -> None:
        with self.assertRaises(ValueError):
            SourceSpan("book", self.blob.sha256[:12], 1, 2, "0" * 64)
        for start, end in ((True, 3), (-1, 2), (2, 2)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                self.store.span("book", start, end)

    def test_source_store_keeps_an_immutable_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "book.txt"
            path.write_bytes(self.raw)
            store = SourceStore.from_directory(Path(directory), {"book": self.blob.sha256})
            path.write_text("changed", encoding="utf-8")
            self.assertEqual(store.sources["book"].raw_bytes, self.raw)
            with self.assertRaisesRegex(ValueError, "source digest mismatch"):
                SourceStore.from_directory(Path(directory), {"book": self.blob.sha256})
        with self.assertRaises(TypeError):
            self.store.sources["new"] = self.blob  # type: ignore[index]



class TestEvidenceLedger(unittest.TestCase):
    def test_every_four_atom_state_matches_independent_set_reasoning(self) -> None:
        # Independent oracle uses sets of atom indices, not the implementation's
        # mask operations. Includes unknown, explicit false and contradiction.
        width = 4
        for required, positive, negative in itertools.product(range(16), repeat=3):
            required_atoms = {i for i in range(width) if (required // 2**i) % 2}
            positive_atoms = {i for i in range(width) if (positive // 2**i) % 2}
            negative_atoms = {i for i in range(width) if (negative // 2**i) % 2}
            conflicts = required_atoms.intersection(positive_atoms, negative_atoms)
            negatives = required_atoms.intersection(negative_atoms).difference(positive_atoms)
            missing = required_atoms.difference(positive_atoms.union(negative_atoms))
            if conflicts:
                status = LicenseStatus.CONFLICT
            elif negatives:
                status = LicenseStatus.REJECTED
            elif missing:
                status = LicenseStatus.PENDING
            else:
                status = LicenseStatus.LICENSED
            actual = evaluate_license(required, EvidenceLedger(width, positive, negative))
            self.assertEqual(actual.status, status, (required, positive, negative))
            self.assertEqual(actual.conflicts, sum(2**i for i in conflicts))
            self.assertEqual(actual.negative, sum(2**i for i in negatives))
            self.assertEqual(actual.missing, sum(2**i for i in missing))

    def test_conflict_precedes_negative_and_missing_only_on_required_atoms(self) -> None:
        decision = evaluate_license(7, EvidenceLedger(4, 1, 3))
        self.assertIs(decision.status, LicenseStatus.CONFLICT)
        self.assertEqual((decision.conflicts, decision.negative, decision.missing), (1, 2, 4))
        irrelevant = evaluate_license(1, EvidenceLedger(4, 9, 8))
        self.assertTrue(irrelevant.licensed)
        self.assertEqual(irrelevant.conflicts, 0)

    def test_unknown_differs_from_explicit_false(self) -> None:
        self.assertIs(evaluate_license(1, EvidenceLedger(1)).status, LicenseStatus.PENDING)
        self.assertIs(evaluate_license(1, EvidenceLedger(1, 0, 1)).status, LicenseStatus.REJECTED)
        self.assertTrue(evaluate_license(0, EvidenceLedger(1, 1, 1)).licensed)

    def test_illegal_or_coerced_masks_are_rejected_before_calculation(self) -> None:
        for args in ((0, 0, 0), (33, 0, 0), (True, 0, 0), (2, 4, 0), (2, 0, -1), (2, False, 0)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                EvidenceLedger(*args)
        for required in (-1, 4, True):
            with self.subTest(required=required), self.assertRaises(ValueError):
                evaluate_license(required, EvidenceLedger(2))



def _case(schema: FeatureSchema, values: tuple[bool | None, ...], name: str) -> FeatureCase:
    return schema.case(
        name, "interpretation-v1", dict(zip(schema.predicates, values, strict=True))
    )



def _oracle(rule: Guard, bits: tuple[bool, ...]) -> bool:
    # Deliberately evaluates per-feature signed requirements, not the mask expression.
    if rule.bottom:
        return False
    for index, bit in enumerate(bits):
        if (rule.positive // 2**index) % 2 and not bit:
            return False
        if (rule.negative // 2**index) % 2 and bit:
            return False
    return True



class TestGuardAlgebra(unittest.TestCase):
    def test_codes_are_bijective_on_small_declared_domains(self) -> None:
        for width in range(1, 6):
            schema = FeatureSchema("test", "v1", tuple(f"p{i}" for i in range(width)))
            guards = GuardLanguage(schema, width).enumerate()
            self.assertEqual(len(guards), 3**width + 1)
            self.assertEqual({g.code for g in guards}, set(range(3**width + 1)))
            for guard in guards:
                self.assertEqual(Guard.from_code(width, guard.code), guard)

    def test_degree_counts_match_independent_ternary_word_enumeration(self) -> None:
        for width in range(1, 6):
            schema = FeatureSchema("test", "v1", tuple(f"p{i}" for i in range(width)))
            for degree in range(width + 1):
                language = GuardLanguage(schema, degree)
                counts = [1] + [0] * degree  # explicit false
                for word in itertools.product((0, 1, 2), repeat=width):
                    grade = sum(item != 0 for item in word)
                    if grade <= degree:
                        counts[grade] += 1
                self.assertEqual(language.count_by_degree, tuple(counts))
                self.assertEqual(len(language.enumerate()), sum(counts))

    def test_partial_prediction_matches_all_concrete_completions(self) -> None:
        schema = FeatureSchema("test", "v1", ("a", "b", "c", "d"))
        rules = GuardLanguage(schema, 4).enumerate()
        complete = tuple(itertools.product((False, True), repeat=4))
        for partial in itertools.product((None, False, True), repeat=4):
            case = _case(schema, partial, "partial")
            completions = tuple(
                word
                for word in complete
                if all(p is None or p is b for p, b in zip(partial, word, strict=True))
            )
            for rule in rules:
                expected = tuple(sorted({_oracle(rule, word) for word in completions}))
                self.assertEqual(rule.possible(case), expected)

    def test_illegal_masks_and_integer_booleans_are_rejected(self) -> None:
        for args in ((2, 1, 1), (2, 4, 0), (2, -1, 0), (True, 0, 0)):
            with self.assertRaises(ValueError):
                Guard(*args)
        with self.assertRaises(ValueError):
            Guard(2, 1, bottom=True)
        with self.assertRaises(ValueError):
            Guard.from_code(2, 10)
        with self.assertRaises(ValueError):
            Guard(2).evaluate(True)
        with self.assertRaises(ValueError):
            FeatureCase("x", "v1", "schema", 2, 1, 2)

    def test_resource_bound_is_checked_before_enumeration(self) -> None:
        schema = FeatureSchema("test", "v1", tuple(f"p{i}" for i in range(32)))
        with self.assertRaisesRegex(ValueError, "resource budget"):
            GuardLanguage(schema, 32)



class TestVersionSpace(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = FeatureSchema("synthetic", "v1", ("same_class", "linked", "noise"))
        self.language = GuardLanguage(self.schema, 3)
        self.session = LearningSession(self.language)

    def test_all_target_rules_survive_correct_examples(self) -> None:
        words = tuple(itertools.product((False, True), repeat=3))
        for target in self.language.enumerate():
            session = self.session
            for index, word in enumerate(words):
                case = _case(self.schema, word, f"case-{index}")
                observation = Observation(f"e-{index}", "oracle", case, _oracle(target, word))
                session = session.observe(observation)
                self.assertIn(target, session.survivors)
                for survivor in session.survivors:
                    for item in session.observations:
                        bits = tuple(bool(item.case.value & (1 << i)) for i in range(3))
                        self.assertIs(_oracle(survivor, bits), item.label)
            self.assertEqual(session.survivors, (target,))

    def test_unknown_label_and_partial_labeled_case_remain_pending(self) -> None:
        complete = _case(self.schema, (True, False, False), "x")
        partial = _case(self.schema, (True, None, False), "y")
        session = self.session.observe(Observation("unknown", "source", complete, None))
        session = session.observe(Observation("partial", "source", partial, True))
        self.assertEqual(session.survivors, self.session.survivors)
        self.assertEqual(session.pending, ("unknown", "partial"))
        self.assertEqual(session.predict(partial).possible, (False, True))

    def test_empty_version_space_is_not_vacuous_consensus(self) -> None:
        case = _case(self.schema, (True, False, False), "x")
        session = self.session.observe(Observation("yes", "source-a", case, True))
        session = session.observe(Observation("no", "source-b", case, False))
        prediction = session.predict(case)
        self.assertIs(prediction.status, LearningStatus.EXHAUSTED_DECLARED_GRAMMAR)
        self.assertEqual(prediction.possible, ())
        self.assertEqual(prediction.reason, "conflicting_labels_for_same_interpretation")

    def test_evidence_correction_restores_previously_eliminated_rule(self) -> None:
        case = _case(self.schema, (True, False, False), "x")
        good = self.session.observe(Observation("yes", "source-a", case, True))
        bad = good.observe(Observation("bad", "source-b", case, False))
        corrected = bad.revise_evidence("bad", Observation("bad", "source-b-v2", case, True))
        self.assertEqual(corrected.survivors, good.survivors)
        self.assertNotEqual(corrected.revision, bad.revision)
        self.assertEqual(bad.survivors, ())  # previous revision remains immutable
        self.assertEqual(bad.revise_evidence("bad", None).survivors, good.survivors)

    def test_cross_identity_feature_collision_has_a_separate_reason(self) -> None:
        left = _case(self.schema, (True, False, False), "case-one")
        right = _case(self.schema, (True, False, False), "case-two")
        session = self.session.observe(Observation("left", "one", left, True))
        session = session.observe(Observation("right", "two", right, False))
        self.assertEqual(session.exhaustion_reason(), "feature_collision_or_conflicting_labels")

    def test_inadequate_grammar_is_not_relabelled_as_inconsistent_world(self) -> None:
        schema = FeatureSchema("xor", "v1", ("a", "b"))
        session = LearningSession(GuardLanguage(schema, 2))
        for i, bits in enumerate(itertools.product((False, True), repeat=2)):
            case = _case(schema, bits, f"case-{i}")
            session = session.observe(
                Observation(f"e-{i}", "xor-oracle", case, bits[0] != bits[1])
            )
        self.assertEqual(session.survivors, ())
        self.assertEqual(session.exhaustion_reason(), "no_consistent_rule_in_declared_grammar")

    def test_query_exhibits_two_surviving_rules_that_disagree(self) -> None:
        pool = tuple(
            _case(self.schema, word, str(i))
            for i, word in enumerate(itertools.product((False, True), repeat=3))
        )
        choice = self.session.choose_query(pool)
        self.assertIsNotNone(choice.case)
        assert (
            choice.case is not None
            and choice.true_rule is not None
            and choice.false_rule is not None
        )
        self.assertTrue(Guard.from_code(3, choice.true_rule).evaluate(choice.case.value))
        self.assertFalse(Guard.from_code(3, choice.false_rule).evaluate(choice.case.value))
        for label in (False, True):
            revised = self.session.observe(Observation("answer", "oracle", choice.case, label))
            self.assertGreater(len(revised.survivors), 0)
            self.assertLess(len(revised.survivors), len(self.session.survivors))

    def test_no_pool_disagreement_does_not_claim_global_identification(self) -> None:
        case = _case(self.schema, (True, False, False), "seen")
        session = self.session.observe(Observation("seen", "source", case, True))
        self.assertGreater(len(session.survivors), 1)
        choice = session.choose_query((case,))
        self.assertIsNone(choice.case)
        self.assertEqual(choice.reason, "no_disagreement_in_supplied_pool")

    def test_schema_and_case_identity_are_enforced(self) -> None:
        old = _case(self.schema, (True, False, False), "x")
        new = _case(self.schema, (False, False, False), "x")
        session = self.session.observe(Observation("e1", "s1", old, True))
        with self.assertRaisesRegex(ValueError, "analysis identity"):
            session.observe(Observation("e2", "s2", new, True))
        other_schema = FeatureSchema("synthetic", "v2", self.schema.predicates)
        with self.assertRaisesRegex(ValueError, "different predicate schema"):
            session.predict(_case(other_schema, (True, False, False), "z"))
        with self.assertRaisesRegex(ValueError, "evidence identity"):
            session.observe(Observation("e1", "s1", old, False))
        with self.assertRaisesRegex(ValueError, "new analysis identity"):
            session.revise_evidence("e1", Observation("e1", "s1", new, True))
        with self.assertRaisesRegex(ValueError, "new analysis identity"):
            session.predict(new)
        with self.assertRaisesRegex(ValueError, "new analysis identity"):
            session.choose_query((new,))
        self.assertEqual(session.predict(old).case, old)
        new_analysis = self.schema.case(
            "x", "interpretation-v2", {"same_class": False, "linked": False, "noise": False}
        )
        corrected = session.revise_evidence("e1", Observation("e1", "s1", new_analysis, True))
        self.assertNotEqual(corrected.revision, session.revision)

    def test_combined_work_limits_do_not_become_negative_evidence(self) -> None:
        first = _case(self.schema, (True, False, False), "x")
        second = _case(self.schema, (False, True, False), "y")
        session = self.session.observe(Observation("e1", "s1", first, True))
        before = session.revision
        with (
            patch("nabt.learning.finite_guard.MAX_LEARNING_CHECKS", 40),
            self.assertRaisesRegex(ValueError, "no evidence was refuted"),
        ):
            session.observe(Observation("e2", "s2", second, False))
        self.assertEqual(session.revision, before)
        with (
            patch("nabt.learning.finite_guard.MAX_QUERY_CHECKS", 30),
            self.assertRaisesRegex(ValueError, "no equivalence was established"),
        ):
            self.session.choose_query((first, second))

    def test_duplicate_evidence_is_idempotent_and_cannot_certify(self) -> None:
        case = _case(self.schema, (True, False, False), "x")
        witness = Observation("e", "s", case, True)
        once = self.session.observe(witness)
        twice = once.observe(witness)
        self.assertEqual(twice.revision, once.revision)
        self.assertEqual(twice.survivors, once.survivors)
        self.assertIs(twice.predict(case).status, LearningStatus.CONDITIONAL_CONSENSUS)
        self.assertFalse(hasattr(twice.predict(case), "rank"))

    def test_missing_keys_do_not_mean_negative_features(self) -> None:
        case = self.schema.case("x", "a", {"same_class": True})
        self.assertEqual(case.known, 1)
        self.assertFalse(case.complete)
        with self.assertRaises(ValueError):
            self.schema.case("x", "a", {"same_class": 1})  # type: ignore[dict-item]



DATA = Path(__file__).resolve().parents[1] / "src/nabt/data/source_evidence"



class TestArabicSourceBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pilot = SixNounPilot.from_directory(DATA)

    def test_all_nine_replays_match_independently_recorded_source_spans(self) -> None:
        fixtures = json.loads((DATA / "pilot_examples.json").read_text(encoding="utf-8"))
        by_id = {item["record_id"]: item for item in fixtures["records"]}
        records = (*self.pilot.prescription_records(), *self.pilot.observed_records())
        self.assertEqual(len(records), 9)
        for record in records:
            expected = by_id[record.record_id]
            with self.subTest(record=record.record_id):
                self.assertEqual(record.kind, expected["kind"])
                for name, span in (("target", record.target_span), ("marker", record.marker_span)):
                    self.assertEqual(
                        (span.start, span.end), (expected[name]["start"], expected[name]["end"])
                    )
                    self.assertEqual(self.pilot.sources.text(span), expected[name]["text"])
                cues = expected.get("cue_parts", [expected.get("cue")])
                self.assertEqual(len(record.cue_spans), len(cues))
                for actual, wanted in zip(record.cue_spans, cues, strict=True):
                    self.assertEqual((actual.start, actual.end), (wanted["start"], wanted["end"]))
                    self.assertEqual(self.pilot.sources.text(actual), wanted["text"])
                checked = self.pilot.check(record.proposal())
                self.assertTrue(checked.accepted)
                self.assertIsNotNone(checked.receipt_id)

    def test_every_binding_field_is_checked_against_replay(self) -> None:
        proposal = self.pilot.propose("qatr_raf")
        for item in fields(EvidenceBinding):
            replacement = (
                "0" * 64
                if item.name.endswith("sha256")
                else "forged:" + getattr(proposal.binding, item.name)
            )
            attack = replace(
                proposal, binding=replace(proposal.binding, **{item.name: replacement})
            )
            with self.subTest(field=item.name):
                result = self.pilot.check(attack)
                self.assertIs(result.status, CheckStatus.REJECTED)
                self.assertIn(f"binding_mismatch:{item.name}", result.reasons)
                self.assertIsNone(self.pilot.to_observation(attack))

    def test_source_or_record_alias_does_not_create_authority(self) -> None:
        proposal = self.pilot.propose("qatr_raf")
        self.assertIs(
            self.pilot.check(replace(proposal, record_id="self_issued")).status,
            CheckStatus.REJECTED,
        )
        self.assertIs(
            self.pilot.check(replace(proposal, record_id="qatr_nasb")).status, CheckStatus.REJECTED
        )
        blobs = dict(self.pilot.sources.sources)
        qatr = blobs["qatr"]
        blobs["qatr"] = SourceBlob(
            "qatr", qatr.raw_bytes.replace("بالواو".encode(), "بالزاي".encode(), 1)
        )
        self.assertNotEqual(blobs["qatr"].sha256, APPROVED_SOURCE_PINS["qatr"])
        # Even a caller-created generic SourceStore cannot replace the pilot pin.
        with self.assertRaisesRegex(ValueError, "source digest mismatch"):
            SixNounPilot(SourceStore(blobs))
        with self.assertRaises(ValueError):
            SixNounPilot(SourceStore({"renamed": SourceBlob("renamed", qatr.raw_bytes)}))

    def test_forged_label_features_and_receipt_record_are_not_admitted(self) -> None:
        record = self.pilot.observed_records()[0]
        proposal = record.proposal()
        attacks = (
            replace(proposal, label=False),
            replace(proposal, value=2),
            replace(proposal, known=15),
            replace(record, label=False).proposal(),
        )
        for attack in attacks:
            with self.subTest(attack=attack):
                self.assertIs(self.pilot.check(attack).status, CheckStatus.REJECTED)
                self.assertIsNone(self.pilot.to_observation(attack))
        for width in (0, 33, True):
            with self.subTest(width=width), self.assertRaises(ValueError):
                replace(record, width=width)

    def test_unknowns_are_named_pending_and_never_negative_observations(self) -> None:
        proposal = self.pilot.propose("qatr_raf")
        for unknown in (replace(proposal, label=None), replace(proposal, known=0, value=0)):
            with self.subTest(unknown=unknown):
                result = self.pilot.check(unknown)
                self.assertIs(result.status, CheckStatus.PENDING)
                self.assertIsNone(result.receipt_id)
                self.assertIsNone(self.pilot.to_observation(unknown))
        with self.assertRaises(ValueError):
            EvidenceProposal(proposal.record_id, proposal.binding, True, 0, True)
        with self.assertRaises(ValueError):
            EvidenceProposal(proposal.record_id, proposal.binding, 7, 1, 1)  # type: ignore[arg-type]

    def test_literal_feature_reader_and_observed_output_reader_are_independent(self) -> None:
        cues = (("هذا",), ("رأيت",), ("مررت", "ب"))
        targets = ("هنوك", "هناك", "هنيك")
        for (index, cue), (target, ending) in itertools.product(
            enumerate(cues), zip(targets, ("و", "ا", "ي"), strict=True)
        ):
            self.assertEqual(read_observed_cue(cue), index)
            self.assertEqual(read_observed_ending(target), ending)
        for raw in ("هنك", "هَنُوك", "هنـوك", "هنو", "هنوكك", "هنوك "):
            self.assertIsNone(read_observed_ending(raw))
        self.assertIsNone(read_observed_cue(("هذا هنوك",)))
        self.assertIsNone(read_observed_cue(("مررت ب",)))
        self.assertEqual(read_prescription_operation("تنصب"), 1)
        self.assertEqual(read_prescription_marker("واو"), "و")
        self.assertIsNone(read_prescription_marker("فترفع"))
        self.assertIsNone(read_prescription_operation("واو"))

    def test_observation_path_is_literal_and_has_no_case_schema(self) -> None:
        records = self.pilot.observed_records()
        self.assertEqual([record.cue for record in records], ["هذا", "رأيت", "مررت ب"])
        self.assertEqual([record.target for record in records], ["هنوك", "هناك", "هنيك"])
        self.assertEqual([record.marker for record in records], ["و", "ا", "ي"])
        self.assertEqual([record.label for record in records], [True, False, False])
        self.assertEqual(len(records[2].cue_spans), 2)
        self.assertEqual(self.pilot.sources.text(records[2].cue_spans[1]), "ب")
        self.assertEqual(
            observation_schema().predicates, ("cue_is_hadha", "cue_is_raaytu", "cue_is_marartu_ba")
        )
        self.assertNotEqual(observation_schema().fingerprint, prescription_schema().fingerprint)
        source_session = LearningSession(GuardLanguage(prescription_schema(), 1))
        with self.assertRaisesRegex(ValueError, "different predicate schema"):
            source_session.observe(self.pilot.observations("observed_example")[0])

    def test_three_actual_observations_refine_without_generating_labels(self) -> None:
        observations = self.pilot.observations("observed_example")
        session = LearningSession(GuardLanguage(observation_schema(), 1))
        counts = [len(session.survivors)]
        for observation in observations:
            session = session.observe(observation)
            counts.append(len(session.survivors))
        self.assertEqual(counts, [8, 4, 2, 1])
        self.assertEqual([rule.code for rule in session.survivors], [1])
        first_only = LearningSession(session.language, observations[:1])
        self.assertIn(0, [rule.code for rule in first_only.survivors])
        second_added = first_only.observe(observations[1])
        self.assertNotIn(0, [rule.code for rule in second_added.survivors])
        self.assertEqual(len({item.source_id for item in observations}), 1)

    def test_unique_degree_one_selector_does_not_claim_richer_grammar_identification(self) -> None:
        observations = self.pilot.observations("observed_example")
        schema = observation_schema()
        richer = LearningSession(GuardLanguage(schema, 3), observations)
        self.assertEqual(len(richer.survivors), 5)
        synthetic_query = schema.case(
            "declared-vector-only", "synthetic-v1", {name: True for name in schema.predicates}
        )
        self.assertIs(richer.predict(synthetic_query).status, LearningStatus.UNDERDETERMINED)

    def test_prescription_compilation_is_separate_and_second_book_adds_no_new_vectors(
        self,
    ) -> None:
        qatr = self.pilot.observations("prescription", "qatr")
        alfiyya = self.pilot.observations("prescription", "alfiyya")
        self.assertEqual(len(qatr), 3)
        self.assertEqual(len(alfiyya), 3)
        self.assertEqual(
            [(e.case.value, e.label) for e in qatr], [(e.case.value, e.label) for e in alfiyya]
        )
        initial = LearningSession(GuardLanguage(prescription_schema(), 1), qatr)
        final = LearningSession(initial.language, (*qatr, *alfiyya))
        self.assertEqual(initial.survivors, final.survivors)
        self.assertEqual(len({e.case.value for e in final.observations}), 3)

    def test_family_retains_alternatives_without_conjoining_them(self) -> None:
        proposal = self.pilot.propose("qatr_raf")
        unknown = replace(proposal, label=None)
        family = self.pilot.assess_family((proposal, unknown))
        self.assertIs(family.status, CheckStatus.AMBIGUOUS)
        self.assertEqual(family.alternatives, (proposal, unknown))
        self.assertEqual(family.observations, ())
        self.assertEqual(len(self.pilot.assess_family((proposal,)).observations), 1)
        unrelated = self.pilot.assess_family((proposal, self.pilot.propose("qatr_nasb")))
        self.assertIs(unrelated.status, CheckStatus.REJECTED)
        self.assertEqual(unrelated.observations, ())
        self.assertEqual(len(unrelated.alternatives), 2)
        with self.assertRaisesRegex(ValueError, "resource budget"):
            self.pilot.assess_family(itertools.repeat(proposal))

    def test_bare_forms_keep_named_missing_conditions_and_source_alternatives(self) -> None:
        for noun in ("أب", "أخ", "حم", "هن", "فم", "ذو"):
            assessment = self.pilot.application_assessment(noun)
            self.assertEqual(assessment.status, "pending")
            self.assertIsNotNone(assessment.decision)
            assert assessment.decision is not None
            self.assertIs(assessment.decision.status, LicenseStatus.PENDING)
            self.assertIn("idafa", assessment.missing_predicates)
            self.assertIn("not_first_person_ya", assessment.missing_predicates)
        dhu = self.pilot.application_assessment("ذو", alternatives=("caller_preferred",))
        self.assertIn("companionship", dhu.missing_predicates)
        self.assertIn("relative_pronoun", dhu.alternatives)
        self.assertIn("tamam", dhu.alternatives)
        self.assertIn("caller_preferred", dhu.alternatives)
        self.assertIn("mim_absent", self.pilot.application_assessment("فم").missing_predicates)
        self.assertIn("qasr", self.pilot.application_assessment("أب").alternatives)
        han = self.pilot.application_assessment("هن")
        self.assertIn("tamam", han.alternatives)
        self.assertIn("naqs_preferred_not_exclusive", han.alternatives)
        with self.assertRaises(TypeError):
            self.pilot.application_assessment("ذو", companionship=True)  # type: ignore[call-arg]

    def test_no_matching_rule_is_not_an_empty_success(self) -> None:
        unknown = self.pilot.application_assessment("كتاب")
        self.assertEqual(unknown.status, "no_matching_rule")
        self.assertIsNone(unknown.decision)
        self.assertEqual(unknown.required, 0)
        self.assertEqual(unknown.source_spans, ())

    def test_simulated_annotation_correction_preserves_source_and_old_snapshot(self) -> None:
        # Deliberately bad external annotation: not represented as a source fact.
        facts = self.pilot.observations("observed_example")
        good = LearningSession(GuardLanguage(observation_schema(), 1), facts)
        fake = Observation("test:bad-annotation", "test:untrusted", facts[0].case, False)
        poisoned = good.observe(fake)
        self.assertEqual(poisoned.survivors, ())
        corrected = poisoned.revise_evidence(fake.evidence_id, None)
        self.assertEqual(corrected.survivors, good.survivors)
        self.assertEqual(poisoned.survivors, ())
        self.assertEqual(corrected.observations, facts)
        source_attack = replace(self.pilot.propose("sibawayhi_han_hadha"), label=False)
        self.assertIsNone(self.pilot.to_observation(source_attack))

    def test_consumption_replays_again_after_a_prior_accepted_check(self) -> None:
        proposal = self.pilot.propose("sibawayhi_han_hadha")
        receipt = self.pilot.check(proposal)
        self.assertTrue(receipt.accepted)
        # A prior receipt cannot replace the source replay at consumption time.
        with patch.object(SixNounPilot, "_replay", side_effect=ValueError("source replay failed")):
            with self.assertRaisesRegex(ValueError, "source replay failed"):
                self.pilot.to_observation(proposal)

    def test_cue_and_target_bytes_are_disjoint_in_every_admitted_record(self) -> None:
        records = (*self.pilot.prescription_records(), *self.pilot.observed_records())
        for record in records:
            with self.subTest(record=record.record_id):
                self.assertGreaterEqual(record.marker_span.start, record.target_span.start)
                self.assertLessEqual(record.marker_span.end, record.target_span.end)
                for cue in record.cue_spans:
                    self.assertTrue(
                        cue.end <= record.target_span.start or record.target_span.end <= cue.start
                    )

    def test_a_modified_manifest_cannot_authorize_modified_original_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            location = Path(directory)
            for source_id, source in self.pilot.sources.sources.items():
                (location / f"{source_id}.txt").write_bytes(source.raw_bytes)
            # Descriptive JSON is deliberately outside the admission policy.
            (location / "source_manifest.json").write_text("{}", encoding="utf-8")
            self.assertEqual(
                SixNounPilot.from_directory(directory).observations("observed_example"),
                self.pilot.observations("observed_example"),
            )
            changed = location / "qatr.txt"
            changed.write_bytes(changed.read_bytes() + b"\n")
            (location / "source_manifest.json").write_text(
                json.dumps({"qatr": content_digest(changed.read_bytes())}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "source digest mismatch: qatr"):
                SixNounPilot.from_directory(location)


class TestInstalledSourceResources(unittest.TestCase):
    def test_default_pilot_has_exact_pins_and_both_separate_schemas(self) -> None:
        pilot = default_pilot()
        self.assertEqual(
            {name: blob.sha256 for name, blob in pilot.sources.sources.items()},
            dict(APPROVED_SOURCE_PINS),
        )
        self.assertEqual(len(pilot.observations("prescription")), 6)
        self.assertEqual(len(pilot.observations("observed_example")), 3)
        self.assertEqual(
            sum(len(blob.raw_bytes) for blob in pilot.sources.sources.values()), 2_777_361
        )

    def test_zip_package_loads_without_checkout_or_external_repository(self) -> None:
        # A fresh isolated interpreter imports the native module and all original
        # source bytes from a package archive. No extracted-directory assumption.
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "installed-nabt.zip"
            package_root = DATA.parents[1]
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
                zipped.writestr("nabt/__init__.py", "")
                zipped.write(package_root / "errors.py", "nabt/errors.py")
                for path in sorted((package_root / "learning").glob("*.py")):
                    zipped.write(path, str(Path("nabt/learning") / path.name))
                for path in sorted(DATA.iterdir()):
                    if path.is_file():
                        zipped.write(path, str(Path("nabt/data/source_evidence") / path.name))
            program = (
                "import json, sys; sys.path.insert(0, sys.argv[1]); "
                "from nabt.learning import default_pilot, SixNounPilot; "
                "import nabt.learning.arabic_six_nouns as module; "
                "pilot=default_pilot(); "
                "print(json.dumps({'module':module.__file__, "
                "'targets':[r.target for r in pilot.observed_records()], "
                "'facts':len(pilot.observations('observed_example'))}))"
            )
            completed = subprocess.run(
                [sys.executable, "-I", "-c", program, str(archive)],
                cwd=directory,
                check=True,
                text=True,
                capture_output=True,
            )
            report = json.loads(completed.stdout)
            self.assertIn("installed-nabt.zip", report["module"])
            self.assertEqual(report["targets"], ["هنوك", "هناك", "هنيك"])
            self.assertEqual(report["facts"], 3)

    def test_source_read_budget_is_enforced_before_blob_construction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "book.txt").write_bytes(b"12345")
            with patch("nabt.learning.source_evidence.MAX_SOURCE_BYTES", 3):
                with self.assertRaisesRegex(ValueError, "source byte budget exceeded"):
                    SourceStore.from_directory(directory, {"book": content_digest(b"12345")})

    def test_learning_resource_limits_are_deferred_and_bound_infinite_inputs(self) -> None:
        schema = FeatureSchema("budget-probe", "v1", ("p",))
        language = GuardLanguage(schema, 1)
        fact = Observation("repeat", "external-test", schema.case("x", "v1", {"p": True}), True)
        with patch("nabt.learning.finite_guard.MAX_OBSERVATIONS", 3):
            with self.assertRaises(NabtError) as error:
                LearningSession(language, itertools.repeat(fact))
        self.assertEqual(error.exception.code, "RESOURCE_LIMIT")
        self.assertEqual(error.exception.status, "DEFER")
        self.assertEqual(len(LearningSession(language).survivors), 4)


class TestEvidenceTableReader(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Fixture uses sets and arithmetic positions, independently of bit-mask
        # implementation and the Lean exporter being checked in the formal gate.
        lines = ["required\tpositive\tnegative\tstatus\tmissing\tconflicts\trefutations"]
        for r, p, n in itertools.product(range(16), repeat=3):
            required = {i for i in range(4) if (r // 2**i) % 2}
            positive = {i for i in range(4) if (p // 2**i) % 2}
            negative = {i for i in range(4) if (n // 2**i) % 2}
            conflicts = required & positive & negative
            refutations = (required & negative) - positive
            missing = required - (positive | negative)
            status = "conflict" if conflicts else "rejected" if refutations else "pending" if missing else "licensed"
            masks = [sum(2**i for i in items) for items in (missing, conflicts, refutations)]
            lines.append("\t".join(map(str, (r, p, n, status, *masks))))
        cls.lines = tuple(lines)

    def table(self, lines: tuple[str, ...]) -> bytes:
        return ("\n".join(lines) + "\n").encode("utf-8")

    def test_complete_table_covers_every_state_once(self) -> None:
        report = compare_lean_table(self.table(self.lines))
        self.assertEqual(report["states"], 4096)
        self.assertEqual(report["mismatches"], 0)
        self.assertFalse(report["linguistic_accuracy_measured"])

    def test_missing_duplicate_noncanonical_and_forged_rows_are_rejected(self) -> None:
        malformed = (
            self.lines[:-1],
            (*self.lines, self.lines[1]),
            (self.lines[0], self.lines[1].replace("0\t", "00\t", 1), *self.lines[2:]),
            (self.lines[0], self.lines[1] + "\textra", *self.lines[2:]),
            (self.lines[0], self.lines[1].replace("licensed", "pending"), *self.lines[2:]),
        )
        for lines in malformed:
            with self.subTest(first=lines[1], count=len(lines)), self.assertRaises(ValueError):
                compare_lean_table(self.table(lines))


if __name__ == "__main__":
    unittest.main()
