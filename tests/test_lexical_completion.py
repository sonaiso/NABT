"""Hand-authored semantic controls and hostile transport/provenance boundaries."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import lexical_completion as lc


def request(entry, *target):
    return {"slots": [{"entry": entry, "target": list(target)}]}


AVAILABLE = (lc.ROOT / "formal/.lake/build/bin/lexicalCompletion").is_file() and (
    lc.ROOT / "artifacts/local/lisan.txt").is_file()


class Boundaries(unittest.TestCase):
    def test_public_schema_cannot_supply_authority_or_lossy_numbers(self):
        values = [None, {}, {"slots": []}, {"slots": True}, request(True), request(1.0),
                  request("بيت", True), request("بيت", 1.5), request("بيت", "\ud800"),
                  request("\ud800"), request("بيت\x00"), request("بيت", " "),
                  {**request("بيت"), "verified": True},
                  {"slots": [{"entry": "بيت", "target": [], "meaning": "new"}]}]
        with patch.object(lc, "CompletionEngine") as factory:
            for value in values:
                with self.subTest(value=repr(value)):
                    self.assertEqual(lc.assess(value)["status"], "INVALID_INPUT")
            factory.assert_not_called()

    def test_public_resource_limit_is_not_linguistic_rejection(self):
        for value in [{"slots": request("عين")["slots"] * 9}, request("x" * 129),
                      request("بيت", *("x" for _ in range(65))), request("بيت", "x" * 4097),
                      {"slots": request("بيت", *(["x" * 4096] * 64))["slots"] * 8}]:
            self.assertEqual(lc.assess(value)["status"], "RESOURCE_LIMIT")

    def test_duplicate_json_key_is_not_accepted_by_cli_parser(self):
        with self.assertRaises(ValueError):
            lc._strict_json('{"slots":[],"slots":[{"entry":"بيت","target":[]}]}')

    def test_citation_offsets_are_exact_integers_and_bound_to_source(self):
        raw = "أرض".encode()
        good = {"work": "x", "source_sha256": lc.sha(raw), "start_byte": 0,
                "end_byte": len(raw), "quotation": "أرض"}
        lc.replay(good, {"x": raw})
        for field, value in [("start_byte", False), ("start_byte", 0.0), ("end_byte", 6.0),
                             ("end_byte", 7), ("quotation", "شمس"), ("source_sha256", "0" * 64)]:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                lc.replay({**good, field: value}, {"x": raw})

    def test_installed_catalogue_is_required_before_native(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p = root / lc.CATALOG
            p.parent.mkdir(parents=True)
            p.write_text('{"all_arabic_complete":true}')
            with self.assertRaisesRegex(ValueError, "CATALOGUE_IDENTITY_CHANGED"):
                lc.CompletionEngine(root)


@unittest.skipUnless(AVAILABLE, "requires pinned full Lisan and compiled lexicalCompletion; mandatory in dedicated CI")
class NativeCompletion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = lc.CompletionEngine()

    def run_request(self, value):
        result = lc.assess(value, engine=self.engine)
        self.assertTrue(result["native_checked"], result)
        self.assertFalse(result["all_arabic_complete"])
        self.assertFalse(result["world_truth_established"])
        self.assertEqual(result["transmission_type"], "UNASSESSED")
        return result

    def test_original_catalogue_is_preserved_without_reauthoring(self):
        base = json.loads((lc.ROOT / "evidence/lexical_denotation/catalog.json").read_text())
        self.assertEqual(self.engine.catalogue["senses"][:18], base["senses"])
        self.assertEqual(self.engine.catalogue["necessities"][:2], base["necessities"])
        self.assertEqual(len({s["id"] for s in self.engine.catalogue["senses"]}), 42)

    def test_source_change_cannot_be_certified_by_unchanged_catalogue(self):
        original = Path.read_bytes
        def altered(path):
            raw = original(path)
            if path == lc.ROOT / lc.SOURCE_PATHS["lisan"]:
                return raw[:-1] + bytes([raw[-1] ^ 1])
            return raw
        with patch.object(Path, "read_bytes", altered), patch.object(lc, "_native") as native:
            self.assertEqual(lc.assess(request("ولد", "ما ولد أيا كان"))["status"], "SOURCE_UNAVAILABLE")
            native.assert_not_called()

    def test_timeout_and_missing_native_have_no_positive_receipt(self):
        for error, status in [(subprocess.TimeoutExpired("lexicalCompletion", 20), "RESOURCE_EXHAUSTED"),
                              (ValueError("NATIVE_RESPONSE_LIMIT"), "RESOURCE_EXHAUSTED"),
                              (OSError("missing native"), "VERIFICATION_UNAVAILABLE")]:
            with patch.object(lc, "_native", side_effect=error):
                r = lc.assess(request("ولد", "ما ولد أيا كان"), engine=self.engine)
                self.assertEqual(r["status"], status)
                self.assertFalse(r["native_checked"])
                self.assertNotIn("native_result", r)

    def test_child_and_going_have_source_testimony_but_no_sentence_parse_claim(self):
        r = self.run_request({"slots": [request("ذهب", "السير والمرور")["slots"][0],
                                       request("ولد", "ما ولد أيا كان")["slots"][0]]})
        self.assertEqual(r["status"], "CONDITIONAL_ALL_READINGS")
        self.assertEqual(r["native_result"]["combination_count"], 1)
        self.assertEqual([s["sense_id"] for s in r["native_result"]["slots"][0]["readings"]], ["lisan:v2:going"])
        self.assertTrue(all(s["source_file_replayed"] for s in r["testimonies"]))
        self.assertFalse(r["free_text_parsing_established"])

    def test_atomic_gloss_does_not_promote_word_occurrence_to_semantic_part(self):
        for entry, target in [("ذهب", "السير"), ("عين", "البصر"), ("فهم", "القلب")]:
            self.assertEqual(self.run_request(request(entry, target))["status"], "NO_LICENSE_FOR_TARGETS")

    def test_same_word_five_senses_are_not_disambiguated_by_target(self):
        r = self.run_request(request("عين", "النقد"))["native_result"]
        self.assertEqual(r["combination_count"], 5)
        self.assertFalse(r["all_targets_licensed"])
        self.assertEqual([c["sense_ids"] for c in r["combinations"]],
                         [["lisan:v2:eye-" + s] for s in ("vision", "spy", "spring", "cash", "letter")])
        self.assertEqual([c["targets_licensed"] for c in r["combinations"]], [False, False, False, True, False])

    def test_multi_slot_product_keeps_all_fifteen_and_only_one_is_licensed(self):
        r = self.run_request({"slots": request("عين", "النقد")["slots"] +
                             request("قلم", "الذي يكتب به")["slots"]})["native_result"]
        self.assertEqual(len(r["combinations"]), 15)
        self.assertEqual(sum(c["targets_licensed"] for c in r["combinations"]), 1)
        self.assertTrue(r["all_installed_combinations_checked"])

    def test_necessity_is_sense_specific_and_not_reversible_or_legal(self):
        r = self.run_request(request("سرر", "الارتفاع"))["native_result"]
        self.assertEqual([s["indications"] for s in r["slots"][0]["readings"]], [["iltizam"], []])
        self.assertFalse(r["all_targets_licensed"])
        for entry, target in [("سرر", "وجود سرير في الخارج"), ("أسد", "العدالة")]:
            self.assertEqual(self.run_request(request(entry, target))["status"], "NO_LICENSE_FOR_TARGETS")

    def test_matching_inclusion_and_necessity_are_separate(self):
        for entry, target, kind in [("أرض", "التي عليها الناس", "mutabaqa"),
                                    ("بيت", "المأوى", "tadammun"), ("عمي", "البصر", "iltizam")]:
            r = self.run_request(request(entry, target))
            self.assertEqual(r["native_result"]["slots"][0]["readings"][0]["indications"], [kind])

    def test_sun_deictic_definition_never_creates_physical_daylight_fact(self):
        r = self.run_request(request("شمس", "النهار"))
        self.assertEqual(r["status"], "UNMEASURED_DEFINITION")
        self.assertEqual(len(r["testimonies"]), 1)
        self.assertEqual(r["testimonies"][0]["components"], [])

    def test_uninterpreted_retrieved_entry_is_not_ungrammatical(self):
        r = self.run_request(request("بحر", "ماء"))
        self.assertEqual(r["status"], "UNMEASURED_ENTRY")
        self.assertTrue(r["retrieval"][0]["blocks"])
        self.assertEqual(r["native_result"]["combinations"][0]["sense_ids"], ["UNMEASURED:بحر"])

    def test_unknown_and_unresolved_slots_cannot_be_silently_erased(self):
        for entry in ("شمس", "غيرمفهرس"):
            r = self.run_request({"slots": request("ولد", "ما ولد أيا كان")["slots"] + request(entry, "x")["slots"]})
            self.assertFalse(r["native_result"]["all_targets_licensed"])
            self.assertEqual(len(r["native_result"]["combinations"][0]["sense_ids"]), 2)

    def test_exhaustion_checks_no_prefix_and_has_no_boolean_verdict(self):
        r = self.run_request({"slots": request("عين", "النقد")["slots"] * 4})["native_result"]
        self.assertEqual(r["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(r["combination_count"], 625)
        self.assertIsNone(r["all_targets_licensed"])
        self.assertEqual(r["combinations"], [])
        self.assertFalse(r["all_installed_combinations_checked"])

    def test_empty_target_does_not_prove_vacuous_coverage(self):
        r = self.run_request(request("أرض"))
        self.assertEqual(r["status"], "NO_LICENSE_FOR_TARGETS")

    def test_altered_native_export_is_rejected(self):
        real = lc._native
        def fake(exe, request=None):
            result = real(exe, request)
            if request is None:
                result["senses"].pop()
            return result
        with patch.object(lc, "_native", side_effect=fake):
            r = lc.assess(request("أرض", "التي عليها الناس"), engine=self.engine)
        self.assertEqual(r["status"], "VERIFICATION_UNAVAILABLE")
        self.assertFalse(r["native_checked"])

    def test_native_receipt_forgery_cannot_erase_readings_or_change_numeric_types(self):
        real = lc._native
        for change in ("remove", "status", "boolean", "float", "entry", "reverse"):
            def fake(exe, request=None):
                r = real(exe, request)
                if request is not None:
                    if change == "remove": r["combinations"].pop()
                    if change == "status": r["status"] = "CONDITIONAL_ALL_READINGS"
                    if change == "boolean": r["all_installed_combinations_checked"] = 1
                    if change == "float": r["combination_count"] = 5.0
                    if change == "entry": r["slots"][0]["entry"] = "فهم"
                    if change == "reverse": r["combinations"].reverse()
                return r
            with self.subTest(change=change), patch.object(lc, "_native", side_effect=fake):
                self.assertEqual(lc.assess(request("عين", "النقد"), engine=self.engine)["status"],
                                 "VERIFICATION_UNAVAILABLE")

    def test_native_jsonl_resumes_after_bad_input(self):
        valid = json.dumps(request("أرض", "التي عليها الناس"), ensure_ascii=False).encode()
        run = subprocess.run([str(self.engine.exe)], input=b'{"slots":1.5}\n' + b'\xff\n' + valid + b'\n',
                             capture_output=True, check=True, timeout=20)
        rows = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual([r["status"] for r in rows], ["INVALID_INPUT", "INVALID_INPUT", "CONDITIONAL_ALL_READINGS"])


if __name__ == "__main__":
    unittest.main()
