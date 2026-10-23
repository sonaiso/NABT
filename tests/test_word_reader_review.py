"""Independent boundary review, authored after the case matrix was frozen.

These are adversarial contract tests, not a held-out proficiency corpus and
not an implementation of the production parser. Expected Arabic distinctions
come from the separately frozen source evidence and the public layer contract.
"""

import copy
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

from nabt import NabtError, words
from nabt.word_reader import (MAX_REPORT_BYTES, MAX_SOURCE_BYTES,
                             decode_word_reading, read_word_at, read_words,
                             verify_word_reading, word_reading_number)


def all_parts(report):
    return [part for occurrence in report["occurrences"]
            for alternative in occurrence["alternatives"]
            for part in alternative["parts"]]


def mentioned_strings(value):
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        return set().union(*(mentioned_strings(v) for v in value.values()))
    if isinstance(value, (list, tuple)):
        return set().union(*(mentioned_strings(v) for v in value)) if value else set()
    return set()


class IndependentWordReaderReviewTests(unittest.TestCase):
    def test_attached_pronoun_is_source_bound_and_cannot_be_reused_as_a_free_word(self):
        source = "ضَرَبْتُ"
        start = len("ضَرَبْ".encode("utf-8"))
        selected = read_word_at(source, start, len(source.encode("utf-8")), source_id="attached")
        self.assertTrue(selected["analyses"])
        self.assertTrue(all(p["kind_name"] == "noun" and p["features"]["pronoun"]
                            and p["features"]["lexical_reuse"] == "ATTACHED_TEMPLATE_ONLY"
                            for p in selected["analyses"]))
        with self.assertRaises(NabtError) as caught:
            read_word_at("تُ", 0, len("تُ".encode("utf-8")), source_id="free")
        self.assertEqual(caught.exception.code, "UNLICENSED_WORD_BOUNDARY")

    def test_valid_utf8_cuts_do_not_strip_a_vowel_or_invent_a_suffix_word(self):
        source = "ضَرَبْتُ"
        for start, end in ((0, len("ضَرَب".encode())),
                           (len("ضَرَبْ".encode()), len("ضَرَبْت".encode())),
                           (len("ضَرَبْت".encode()), len(source.encode()))):
            with self.subTest(start=start, end=end), self.assertRaises(NabtError) as caught:
                read_word_at(source, start, end)
            self.assertEqual(caught.exception.code, "UNLICENSED_WORD_BOUNDARY")

    def test_selected_analysis_must_keep_parent_reading_ambiguity(self):
        source = "ضرب"
        report = read_words(source)
        self.assertEqual(report["status"], "DEFER")
        self.assertIn("VOCALIZATION_OR_LEXICAL_SELECTION_EVIDENCE",
                      report["occurrences"][0]["obligations"])
        selected = read_word_at(source, 0, len(source.encode()))
        self.assertIn("VOCALIZATION_OR_LEXICAL_SELECTION_EVIDENCE", mentioned_strings(selected),
                      "Selecting a span must not erase a condition on the source reading")
        self.assertIn(selected.get("status"), {"AMBIGUOUS", "DEFER"})
        self.assertFalse(verify_word_reading(selected, source=source)["valid"],
                         "A selected view must not masquerade as a full replay certificate")

    def test_identical_text_in_another_span_source_or_scope_does_not_share_authority(self):
        source = "زَيْدٌ زَيْدٌ"
        report = read_words(source, source_id="alpha", scope="one")
        a, b = report["occurrences"]
        wrong = copy.deepcopy(report)
        wrong["occurrences"][1]["alternatives"][0]["parts"][0] = copy.deepcopy(a["alternatives"][0]["parts"][0])
        self.assertFalse(verify_word_reading(wrong, source=source, source_id="alpha", scope="one")["valid"])
        for expected in ({"source_id": "beta"}, {"scope": "two"}, {"source": source + " "}):
            with self.subTest(expected=expected):
                self.assertFalse(verify_word_reading(report, **expected)["valid"])
        self.assertNotEqual(a["occurrence_id"], b["occurrence_id"])

    def test_missing_mark_stays_distinct_from_contextual_case(self):
        report = read_words("زَيْد")
        candidates = all_parts(report)
        self.assertTrue(candidates)
        self.assertTrue(all(p["observed_ending"] is None and p["actual_case"] is None for p in candidates))
        self.assertTrue(all({tuple(v) for v in p["case_candidates"]} == {(0, 0), (0, 1), (0, 2)} for p in candidates))
        past = all_parts(read_words("ضَرَبَ"))
        self.assertTrue(all(p["construction"] == "built" and p["actual_case"] is None
                            and p["case_candidates"] == [] for p in past))

    def test_arabic_nested_or_extra_constituents_are_not_a_next_token_assignment(self):
        for source in ("إِنَّ زَيْدًا مِنْ رَجُلٍ", "مِنْ رَجُلٍ قَائِمٌ",
                       "لَمْ يَقُمْ زَيْدٌ", "إِنَّ زَيْدًا قَائِمٌ رَجُلٌ",
                       "هَلْ إِنَّ زَيْدًا قَائِمٌ", "وَإِنَّ زَيْدًا قَائِمٌ"):
            with self.subTest(source=source):
                report = read_words(source)
                self.assertEqual(report["status"], "DEFER")
                self.assertFalse(any(c["status"] == "CHECKED" for c in report["contexts"]))
                self.assertEqual(report["facts"], [])

    def test_parenthesized_subframe_does_not_erase_unresolved_outer_scope(self):
        report = read_words("هَلْ (إِنَّ زَيْدًا قَائِمٌ)")
        self.assertEqual(report["status"], "DEFER",
                         "A checked inner clause is not evidence that the outer construction was read")
        self.assertTrue(any(c["status"] != "CHECKED" for c in report["contexts"])
                        or report.get("obligations"), "The unhandled outer scope needs a named obligation")

    def test_quotation_cannot_activate_an_operator_or_fill_a_complement(self):
        for source in ("«إِنَّ» زَيْدًا قَائِمٌ", '"إِنَّ" زَيْدًا قَائِمٌ',
                       "مِنْ «رَجُلٍ»", "لَمْ «يَقُمْ»", "«إِنَّ زَيْدًا قَائِمٌ»"):
            with self.subTest(source=source):
                report = read_words(source)
                self.assertEqual(report["status"], "DEFER")
                self.assertFalse(any(c["status"] == "CHECKED" for c in report["contexts"]))

    def test_source_mark_order_is_preserved_even_when_lexical_reading_matches(self):
        first, second = "إِنَّ زَيْدًا قَائِمٌ", "إِنَّ زَيْدًا قَائِمٌ"
        self.assertNotEqual(first.encode(), second.encode())
        a, b = read_words(first), read_words(second)
        self.assertEqual(a["status"], "READ")
        self.assertEqual(b["status"], "READ")
        self.assertEqual(a["raw_text"], first)
        self.assertEqual(b["raw_text"], second)
        self.assertFalse(verify_word_reading(a, source=second)["valid"])

    def test_case_conflict_or_unknown_surface_cannot_be_repaired_in_a_certificate(self):
        for source in ("إِنَّ زَيْدٌ قَائِمٌ", "لَمْ يَقُومْ", "مِنْ يَقُومُ"):
            with self.subTest(source=source):
                report = read_words(source)
                self.assertNotEqual(report["status"], "READ")
                self.assertFalse(any(c["status"] == "CHECKED" for c in report["contexts"]))
                wrong = copy.deepcopy(report)
                wrong["status"] = "READ"
                for context in wrong["contexts"]:
                    context["status"] = "CHECKED"
                    context["obligations"] = []
                    context["conflicts"] = []
                self.assertFalse(verify_word_reading(wrong)["valid"])

    def test_non_tanwin_noun_forms_do_not_complete_a_frame_without_construction_evidence(self):
        pairs = (("مِنْ رَجُلِ", "مِنْ رَجُلٍ"),
                 ("إِنَّ زَيْدَ قَائِمُ", "إِنَّ زَيْدًا قَائِمٌ"),
                 ("إِنَّ رَجُلَ قَائِمُ", "إِنَّ رَجُلًا قَائِمٌ"))
        for incomplete, licensed in pairs:
            with self.subTest(incomplete=incomplete):
                report = read_words(incomplete)
                self.assertEqual(report["status"], "DEFER")
                self.assertTrue(any(p["kind_name"] == "noun" for p in all_parts(report)),
                                "Do not discard lexical candidates merely to avoid the contextual condition")
                self.assertFalse(any(c["status"] == "CHECKED" for c in report["contexts"]))
                self.assertIn("CONSTRUCT_STATE_OR_TANWIN_EVIDENCE", mentioned_strings(report))
                positive = read_words(licensed)
                self.assertEqual(positive["status"], "READ")
                self.assertTrue(any(c["status"] == "CHECKED" for c in positive["contexts"]))

    def test_independent_mutations_of_complete_roles_classes_and_segmentation_fail_replay(self):
        original = read_words("إِنَّ زَيْدًا قَائِمٌ", source_id="review", scope="syntax")
        self.assertEqual(original["contexts"][0]["status"], "CHECKED")
        def mutated(change):
            value = copy.deepcopy(original)
            change(value)
            return value
        changes = [
            lambda r: r["occurrences"][1]["alternatives"][0]["parts"][0].update(declension_class=4),
            lambda r: r["occurrences"][1]["alternatives"][0].update(segmentation_id="other"),
            lambda r: r["contexts"][0]["bindings"][0]["words"][0].update(role=1),
            lambda r: r["contexts"][0]["bindings"][0]["words"][0].update(case=1),
            lambda r: r["contexts"][0]["bindings"][0].update(case_check={"complete": [999], "viable": [999]}),
            lambda r: r["contexts"][0].update(class_code=7),
            lambda r: r["contexts"][0]["bindings"][0]["words"][0]["analysis"].update(reading_id="other"),
            lambda r: r["occurrences"][1]["alternatives"][0]["parts"][0].update(kind=False),
            lambda r: r.update(schema_version=True),
            lambda r: r.update(facts=[{"unsupported": True}]),
        ]
        for number, change in enumerate(changes):
            with self.subTest(mutation=number):
                value = mutated(change)
                self.assertFalse(verify_word_reading(value, source=original["raw_text"],
                                                    source_id="review", scope="syntax")["valid"])
                with self.assertRaises(NabtError):
                    word_reading_number(value)

    def test_malformed_deep_cyclic_and_oversized_reports_are_structured_failures(self):
        original = read_words("زَيْدٌ")
        bads = [None, True, [], 7, "{}", {}, {"raw_text": "زيد"},
                {**original, "raw_text": "\ud800"}, {**original, "bad": float("nan")},
                {**original, "extra": "x" * (MAX_REPORT_BYTES + 1)}]
        cycle = copy.deepcopy(original)
        cycle["loop"] = cycle
        bads.append(cycle)
        deep = copy.deepcopy(original)
        cursor = deep
        for _ in range(1100):
            child = {}
            cursor["extra"] = child
            cursor = child
        bads.append(deep)
        for index, bad in enumerate(bads):
            with self.subTest(shape=index):
                answer = verify_word_reading(bad)
                self.assertIs(answer["valid"], False)
                self.assertIn(answer["status"], {"REJECT", "DEFER"})

    def test_canonical_number_rejects_duplicate_keys_whitespace_invalid_utf8_and_oversize(self):
        for raw in (b"{}", b"[]", b"true", b"NaN", b'{"x":1,"x":2}', b" { } ", b"\xff"):
            with self.subTest(raw=raw), self.assertRaises(NabtError):
                decode_word_reading(int.from_bytes(b"\x01" + raw, "big"))
        original = read_words("زَيْدٌ")
        noncanonical = json.dumps(original, ensure_ascii=False, indent=1).encode()
        with self.assertRaises(NabtError):
            decode_word_reading(int.from_bytes(b"\x01" + noncanonical, "big"))
        with self.assertRaises(NabtError) as caught:
            decode_word_reading(1 << (8 * (MAX_REPORT_BYTES + 1)))
        self.assertEqual((caught.exception.status, caught.exception.code), ("DEFER", "RESOURCE_LIMIT"))

    def test_boolean_values_never_enter_numeric_enum_domains(self):
        operations = [lambda: words.capacities(True), lambda: words.class_kind(False),
                      lambda: words.kind_candidates(((True,),)),
                      lambda: words.case_candidates((False,), None),
                      lambda: words.case_candidates((0,), True),
                      lambda: words.refine_cases(((0, 0),), role=False, required_case=0),
                      lambda: words.refine_cases(((0, 0),), role=0, required_case=False),
                      lambda: words.class_case_number(False, 0), lambda: words.class_case_number(0, True),
                      lambda: words.decode_class_case(True), lambda: decode_word_reading(True),
                      lambda: read_word_at("زيد", False, 6), lambda: read_word_at("زيد", 0, True)]
        for index, operation in enumerate(operations):
            with self.subTest(index=index), self.assertRaises(NabtError):
                operation()

    def test_resource_limits_are_deferral_not_a_linguistic_refutation(self):
        for source in ("x" * (MAX_SOURCE_BYTES + 1), "زيد " * 129):
            with self.subTest(size=len(source)), self.assertRaises(NabtError) as caught:
                read_words(source)
            self.assertEqual((caught.exception.status, caught.exception.code), ("DEFER", "RESOURCE_LIMIT"))

    def test_cli_binds_report_to_requested_source_and_scope(self):
        from nabt.cli import main

        def call(args):
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                status = main(args)
            return status, json.loads(out.getvalue() or err.getvalue())

        with tempfile.TemporaryDirectory(prefix="nabt_word_cli_review_") as directory:
            directory = Path(directory)
            source, certificate = directory / "source.txt", directory / "report.json"
            source.write_text("مِنْ رَجُلٍ", encoding="utf-8")
            status, packet = call(["read-words", str(source), "--scope", "review", "--with-number"])
            self.assertEqual(status, 0)
            self.assertEqual(packet["encoding"]["authority"], "ENCODING_ONLY")
            self.assertEqual(decode_word_reading(int(packet["encoding"]["number_hex"], 16)), packet["reading"])
            certificate.write_text(json.dumps(packet["reading"], ensure_ascii=False), encoding="utf-8")
            status, answer = call(["verify-words", str(certificate), "--source", str(source), "--scope", "review"])
            self.assertEqual((status, answer["valid"]), (0, True))
            status, answer = call(["verify-words", str(certificate), "--source", str(source), "--scope", "other"])
            self.assertEqual((status, answer["valid"]), (2, False))
            source.write_text("مِنْ زَيْدٍ", encoding="utf-8")
            status, answer = call(["verify-words", str(certificate), "--source", str(source), "--scope", "review"])
            self.assertEqual((status, answer["valid"]), (2, False))

    def test_cli_malformed_and_oversized_reports_fail_structurally(self):
        from nabt.cli import main

        with tempfile.TemporaryDirectory(prefix="nabt_word_json_review_") as directory:
            path = Path(directory) / "bad.json"
            for raw, expected_exit in ((b"{", 2), (b"\xff", 2), (b"true", 2),
                                       (b'{"raw_text":"x","raw_text":"y"}', 2),
                                       (b"[" * 1500 + b"]" * 1500, 2),
                                       (b" " * (MAX_REPORT_BYTES + 1), 3)):
                with self.subTest(length=len(raw)):
                    path.write_bytes(raw)
                    out, err = io.StringIO(), io.StringIO()
                    with redirect_stdout(out), redirect_stderr(err):
                        status = main(["verify-words", str(path)])
                    answer = json.loads(out.getvalue() or err.getvalue())
                    self.assertEqual(status, expected_exit)
                    self.assertIn(answer["status"], {"REJECT", "DEFER"})
                    self.assertIsNot(answer.get("valid"), True)

    def test_evaluator_identity_adapter_is_injective_and_blanket_defer_fails_positive_gold(self):
        path = Path(__file__).resolve().parents[1] / "tools/word_evaluation.py"
        spec = importlib.util.spec_from_file_location("independent_word_evaluator_review", path)
        evaluator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(evaluator)
        labels = ["independent-w01", "independent_w01", "word-original", "word-other", "هوية"]
        values = [evaluator.runtime_source_id(v) for v in labels]
        self.assertEqual(len(set(values)), len(labels))
        self.assertEqual([bytes.fromhex(v.removeprefix("case_")).decode() for v in values], labels)
        material = evaluator.load_material()
        positive = next(c for c in material["cases"] if c["id"] == "w01")
        checks = evaluator.evaluate_properties(positive, {"status": "DEFER"}, None, None)
        self.assertFalse(all(c["passed"] for c in checks))
        marker_error = next(c for c in material["cases"] if c["id"] == "w27")
        checks = evaluator.evaluate_properties(marker_error, {},
                                              {"status": "DEFER", "code": "RESOURCE_LIMIT"}, None)
        self.assertFalse(all(c["passed"] for c in checks))
        baseline = json.loads((path.parents[1] / "evidence/words/validated_run.json").read_text())
        self.assertTrue(evaluator.regression_gate_passes(baseline["results"]))
        for change in (lambda r: r.update(runtime_error={"status": "DEFER", "code": "RESOURCE_LIMIT"}),
                       lambda r: r.update(report={}),
                       lambda r: r["checks"].append({"property": "unexpected_safety_failure", "passed": False})):
            changed = copy.deepcopy(baseline["results"])
            target = next(r for r in changed if r["id"] == "w15")
            change(target)
            self.assertFalse(evaluator.regression_gate_passes(changed),
                             "A known capability gap cannot exempt new errors or missing evidence")


if __name__ == "__main__":
    unittest.main()
