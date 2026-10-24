"""Independent contract and counterexample probes for classical source witnesses.

The initial matrix predates the new adapter. These executable cases extend it
after the API and selected sources were available; they are not blinded language
gold. Raw source bytes, quoted prescriptions, supplied formal interpretations,
and applicability to a new sentence have deliberately different expectations.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools import classical_language_evidence as evidence


ROOT = Path(__file__).resolve().parents[1]
VERSION = "nabt.classical-language-evidence.v1"
CATALOG = ROOT / evidence.CATALOG_PATH


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def catalog_data():
    return json.loads(CATALOG.read_bytes())


def independent_passage(record_id):
    """Read selected raw bytes without calling the production source reader."""
    catalog = catalog_data()
    record = next(row for row in catalog["records"] if row["record_id"] == record_id)
    source = next(row for row in catalog["sources"] if row["source_id"] == record["source_id"])
    raw = (ROOT / source["local_path"]).read_bytes()
    return raw[record["start"]:record["end"]].decode("utf-8")


def request(record_id, kind, candidate):
    return {"version": VERSION, "record_id": record_id,
            "claim_kind": kind, "candidate": candidate}


def passage_request(record_id="sibawayhi_han_examples"):
    return request(record_id, "PASSAGE_ATTESTATION", {"text": independent_passage(record_id)})


def inna_request(operator="inna", form="full", ma="absent", options=None):
    return request("qatr_inna_conditions", "GRAMMAR_APPLICATION", {
        "law_id": "qatr-inna-v1", "inputs": {"operator": operator, "form": form, "ma": ma},
        "expected": {"options": ["governed"] if options is None else options},
        "target_text": "إن زيدا قائم",  # Supplied target; this adapter does not parse it.
    })


def large_mismatch_request():
    value = inna_request()
    value["candidate"]["target_text"] = "جملة للفحص"
    value["candidate"]["expected"] = {f"padding{i}": "x" * 65500 for i in range(7)}
    value["candidate"]["expected"]["padding7"] = ""
    fill = evidence.MAX_JSON_BYTES - 32 - len(canonical(value))
    if not 0 < fill <= 65536:
        raise AssertionError("The preserved report-budget counterexample no longer fits its request domain")
    value["candidate"]["expected"]["padding7"] = "x" * fill
    return value


class SourceAttestationTests(unittest.TestCase):
    def test_catalog_reopens_all_four_sources_and_thirteen_selected_passages(self):
        result = evidence.audit_catalog()
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(len(result["sources"]), 4)
        self.assertEqual(len(result["records"]), 13)
        self.assertTrue(all(row["status"] == "ATTESTED" for row in result["records"]))
        self.assertFalse(result["application_established"])
        self.assertFalse(result["external_event_established"])
        self.assertFalse(result["universal_language_certified"])
        self.assertEqual(result["catalog_sha256"], sha256(CATALOG.read_bytes()).hexdigest())

    def test_each_selected_passage_matches_independently_sliced_source_bytes(self):
        for record in catalog_data()["records"]:
            with self.subTest(record=record["record_id"]):
                proposed = passage_request(record["record_id"])
                result = evidence.assess(proposed)
                self.assertEqual(result["status"], "ATTESTED")
                self.assertEqual(result["actual"], proposed["candidate"])
                self.assertTrue(result["source_attested"])
                self.assertEqual(result["passage"]["sha256"],
                                 sha256(proposed["candidate"]["text"].encode("utf-8")).hexdigest())
                self.assertTrue(evidence.verify(result, proposed)["valid"])

    def test_han_passage_preserves_the_preimplementation_span_and_restricted_attribution(self):
        matrix = json.loads((ROOT / "evidence/classical_language/independent_case_matrix_v1.json").read_bytes())
        frozen = matrix["sources"]["sib_han"]
        result = evidence.assess(passage_request())
        self.assertEqual(result["passage"]["text"], frozen["raw_text"])
        self.assertEqual((result["passage"]["start"], result["passage"]["end"]),
                         (1460416, 1460684))
        self.assertIn("من العرب من يقول هذا هنوك ورأيت هناك ومررت بهنيك", result["passage"]["text"])
        self.assertEqual(result["source_evidence_kind"], "REPORTED_USAGE_WITH_UNNAMED_SPEAKERS")

    def test_changed_letter_or_punctuation_refutes_only_the_bounded_correspondence(self):
        proposed = passage_request()
        proposed["candidate"]["text"] = proposed["candidate"]["text"].replace("هنوك", "هنيك", 1)
        result = evidence.assess(proposed)
        self.assertEqual(result["status"], "MISMATCH")
        self.assertTrue(result["source_attested"])
        self.assertFalse(result["universal_language_certified"])
        self.assertFalse(result["external_event_established"])

    def test_omitted_blocker_or_disagreement_is_not_the_registered_full_passage(self):
        for record_id, omitted in (("qatr_inna_conditions", "إن لم تقترن بهن ما الحرفية"),
                                   ("qatr_tamyiz_disagreement", "خلافا لسيبويه")):
            with self.subTest(record=record_id):
                proposed = passage_request(record_id)
                self.assertIn(omitted, proposed["candidate"]["text"])
                proposed["candidate"]["text"] = proposed["candidate"]["text"].replace(omitted, "")
                self.assertEqual(evidence.assess(proposed)["status"], "MISMATCH")

    def test_prescription_and_reported_usage_are_not_promoted_to_new_events(self):
        for record_id in ("qatr_six_nouns", "sibawayhi_reported_imperative_usage",
                          "awamil_jurjani_ba_examples"):
            for kind in ("UNIVERSAL_LANGUAGE", "EXTERNAL_EVENT"):
                with self.subTest(record=record_id, kind=kind):
                    proposed = request(record_id, kind, {"statement": "ثبت هذا الاستعمال لكل متكلم وكل واقعة"})
                    result = evidence.assess(proposed)
                    self.assertEqual(result["status"], "DEFER")
                    self.assertTrue(result["source_attested"])
                    self.assertFalse(result["external_event_established"])
                    self.assertFalse(result["universal_language_certified"])

    def test_jurjani_is_labeled_as_reviewed_transcription_not_original_pdf_bytes(self):
        result = evidence.assess(passage_request("awamil_jurjani_partition"))
        self.assertEqual(result["status"], "ATTESTED")
        self.assertEqual(result["source"]["provenance_kind"], "MANUALLY_REVIEWED_TRANSCRIPTION")
        self.assertIn("أحد وتسعون", result["passage"]["text"])
        self.assertIn("سبعة", result["passage"]["text"])
        self.assertIn("عددان", result["passage"]["text"])
        self.assertFalse(result["application_established"])


class LexicalAttestationTests(unittest.TestCase):
    def test_two_root_entry_quotes_are_attested_with_their_distinct_glosses(self):
        for identity, root, gloss in (
            ("maqayis_ktb_entry", "كتب", "أصل صحيح واحد يدل على جمع شيء إلى شيء."),
            ("maqayis_ilm_entry", "علم", "العلم: نقيض الجهل"),
        ):
            with self.subTest(root=root):
                result = evidence.assess(request(identity, "LEXICAL_ATTESTATION", {"root": root, "gloss": gloss}))
                self.assertEqual(result["status"], "LEXICALLY_ATTESTED")
                self.assertEqual(result["actual"], {"root": root, "gloss": gloss})
                self.assertIn(f"({root})", result["passage"]["text"])
                self.assertIn(gloss, result["passage"]["text"])
                self.assertFalse(result["target_parsed"])
                self.assertFalse(result["application_established"])

    def test_gloss_from_one_entry_cannot_be_transferred_to_another_root(self):
        proposed = request("maqayis_ktb_entry", "LEXICAL_ATTESTATION",
                           {"root": "علم", "gloss": "العلم: نقيض الجهل"})
        result = evidence.assess(proposed)
        self.assertEqual(result["status"], "MISMATCH")
        self.assertEqual(result["actual"]["root"], "كتب")

    def test_root_entry_does_not_attest_every_derived_form_or_contextual_meaning(self):
        for value in ({"root": "كاتب", "gloss": "أصل صحيح واحد يدل على جمع شيء إلى شيء."},
                      {"root": "كتب", "gloss": "كل كاتب في كل سياق هو جامع الأشياء"}):
            with self.subTest(value=value):
                result = evidence.assess(request("maqayis_ktb_entry", "LEXICAL_ATTESTATION", value))
                self.assertEqual(result["status"], "MISMATCH")
                self.assertFalse(result["universal_language_certified"])

    def test_parenthetical_or_inferred_lexeme_does_not_become_a_registered_root_heading(self):
        proposed = request("maqayis_blum_context", "LEXICAL_ATTESTATION",
                           {"root": "بلعم", "gloss": "لفظ مذكور في السياق"})
        result = evidence.assess(proposed)
        self.assertEqual(result["status"], "DEFER")
        self.assertTrue(result["source_attested"])
        self.assertIsNone(result["actual"])
        self.assertIn("RECORD_HAS_NO_LICENSED_LEXICAL_PROJECTION", result["residuals"])

    def test_compilation_provenance_is_not_itself_a_lexical_entry(self):
        proposed = request("maqayis_compilation_basis", "LEXICAL_ATTESTATION",
                           {"root": "كتب", "gloss": "أصل صحيح واحد يدل على جمع شيء إلى شيء."})
        result = evidence.assess(proposed)
        self.assertEqual(result["status"], "DEFER")
        self.assertEqual(result["source_evidence_kind"], "AUTHOR_SOURCE_PROVENANCE")


class ConditionalGrammarTests(unittest.TestCase):
    def test_eight_supplied_courses_have_the_four_stated_surfaces(self):
        pairs = (("nasb", "fatha"), ("jarr", "kasra"), ("raf", "damma"), ("jazm", "sukun"),
                 ("fath", "fatha"), ("damm", "damma"), ("kasr", "kasra"), ("waqf", "sukun"))
        for course, surface in pairs:
            with self.subTest(course=course):
                proposed = request("sibawayhi_eight_functions", "GRAMMAR_APPLICATION", {
                    "law_id": "sibawayhi-course-v1", "inputs": {"course": course},
                    "expected": {"surface": surface}, "target_text": "لفظ لم يحلله هذا الفاحص"})
                result = evidence.assess(proposed)
                self.assertEqual(result["status"], "CONDITIONALLY_CHECKED")
                self.assertEqual(result["actual"], {"surface": surface})
                self.assertFalse(result["target_parsed"])
                self.assertFalse(result["application_established"])
                self.assertEqual(result["premises_authority"], "CALLER_INTERPRETED")

    def test_observed_surface_does_not_select_between_irab_and_bina_courses(self):
        proposed = request("sibawayhi_eight_functions", "GRAMMAR_APPLICATION", {
            "law_id": "sibawayhi-surface-v1", "inputs": {"surface": "fatha"},
            "expected": {"courses": ["nasb", "fath"]}, "target_text": "كتبَ"})
        full = evidence.assess(proposed)
        self.assertEqual(full["status"], "CONDITIONALLY_CHECKED")
        self.assertTrue(full["ambiguity_retained"])
        proposed["candidate"]["expected"] = {"courses": ["nasb"]}
        incomplete = evidence.assess(proposed)
        self.assertEqual(incomplete["status"], "MISMATCH")
        self.assertEqual(incomplete["actual"]["courses"], ["nasb", "fath"])
        self.assertTrue(incomplete["ambiguity_retained"])

    def test_full_inna_operates_with_absent_ma_and_is_blocked_by_kaffa(self):
        for operator in ("inna", "anna", "kaanna", "lakinna", "laalla"):
            for ma, expected in (("absent", ["governed"]), ("kaffa", ["blocked"])):
                with self.subTest(operator=operator, ma=ma):
                    result = evidence.assess(inna_request(operator=operator, ma=ma, options=expected))
                    self.assertEqual(result["status"], "CONDITIONALLY_CHECKED")
                    self.assertEqual(result["actual"], {"options": expected})
                    self.assertFalse(result["application_established"])

    def test_layta_with_ma_retains_both_explicit_source_options(self):
        proposed = inna_request(operator="layta", ma="kaffa", options=["governed", "blocked"])
        result = evidence.assess(proposed)
        self.assertEqual(result["status"], "CONDITIONALLY_CHECKED")
        self.assertTrue(result["ambiguity_retained"])
        for chosen in (["governed"], ["blocked"]):
            with self.subTest(chosen=chosen):
                proposed["candidate"]["expected"] = {"options": chosen}
                result = evidence.assess(proposed)
                self.assertEqual(result["status"], "MISMATCH")
                self.assertEqual(result["actual"], {"options": ["governed", "blocked"]})

    def test_light_or_unknown_conditions_defer_instead_of_certifying_empty_options(self):
        for form, ma in (("light", "absent"), ("light", "kaffa"), ("full", "unknown")):
            with self.subTest(form=form, ma=ma):
                result = evidence.assess(inna_request(form=form, ma=ma, options=[]))
                self.assertEqual(result["status"], "DEFER")
                self.assertEqual(result["actual"], {"options": []})
                self.assertIn("EMPTY_OPTIONS_IS_NOT_LINGUISTIC_REFUTATION", result["residuals"])

    def test_changing_expected_does_not_change_the_computed_law(self):
        proposed = inna_request()
        first = evidence.assess(proposed)
        proposed["candidate"]["expected"] = {"options": ["blocked"]}
        second = evidence.assess(proposed)
        self.assertEqual(first["status"], "CONDITIONALLY_CHECKED")
        self.assertEqual(second["status"], "MISMATCH")
        self.assertEqual(first["actual"], second["actual"])

    def test_target_text_is_replay_bound_but_not_silently_parsed(self):
        proposed = inna_request()
        first = evidence.assess(proposed)
        changed = deepcopy(proposed)
        changed["candidate"]["target_text"] = "ليت المعنى مخالف لما افترضه مقدم الطلب"
        second = evidence.assess(changed)
        self.assertEqual(first["actual"], second["actual"])
        self.assertEqual(second["status"], "CONDITIONALLY_CHECKED")
        self.assertFalse(second["target_parsed"])
        self.assertFalse(second["application_established"])
        self.assertNotEqual(first["request_sha256"], second["request_sha256"])
        self.assertFalse(evidence.verify(first, changed)["valid"])

    def test_law_cannot_be_borrowed_from_an_unrelated_attested_record(self):
        for identity in ("sibawayhi_han_examples", "maqayis_ktb_entry", "qatr_tamyiz_disagreement"):
            with self.subTest(identity=identity):
                proposed = inna_request()
                proposed["record_id"] = identity
                result = evidence.assess(proposed)
                self.assertEqual(result["status"], "DEFER")
                self.assertTrue(result["source_attested"])
                self.assertIsNone(result["actual"])
                self.assertIn("LAW_NOT_SUPPORTED_BY_THIS_PASSAGE", result["residuals"])

    def test_jurjani_partition_is_a_source_model_not_a_new_100_row_inventory(self):
        proposed = request("awamil_jurjani_partition", "FORMAL_MODEL_CHECK", {
            "law_id": "jurjani-awamil-partition-v1", "inputs": {},
            "expected": {"samai": 91, "qiyasi": 7, "manawi": 2, "total": 100}})
        result = evidence.assess(proposed)
        self.assertEqual(result["status"], "CONDITIONALLY_CHECKED")
        self.assertEqual(result["actual"], {"samai": 91, "qiyasi": 7, "manawi": 2, "total": 100})
        self.assertFalse(result["universal_language_certified"])
        self.assertFalse(result["application_established"])
        proposed["candidate"]["expected"]["qiyasi"] = 8
        self.assertEqual(evidence.assess(proposed)["status"], "MISMATCH")


class SourceIntegrityAndReplayTests(unittest.TestCase):
    def copied_root(self, identity="qatr_inna_conditions"):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        destination = Path(temporary.name)
        catalog = catalog_data()
        record = next(row for row in catalog["records"] if row["record_id"] == identity)
        source = next(row for row in catalog["sources"] if row["source_id"] == record["source_id"])
        for name in (evidence.CATALOG_PATH, source["local_path"]):
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        return destination, source

    def test_same_source_pin_cannot_survive_a_changed_byte(self):
        destination, source = self.copied_root()
        proposed = inna_request()
        previous = evidence.assess(proposed, root=destination)
        self.assertEqual(previous["status"], "CONDITIONALLY_CHECKED")
        path = destination / source["local_path"]
        raw = path.read_bytes()
        path.write_bytes(b"X" + raw[1:])
        current = evidence.assess(proposed, root=destination)
        self.assertEqual(current["status"], "DEFER")
        self.assertFalse(current["source_attested"])
        self.assertIn("INSTALLED_EVIDENCE_UNAVAILABLE", current["residuals"])
        self.assertFalse(evidence.verify(previous, proposed, root=destination)["valid"])

    def test_recomputed_caller_catalog_hash_does_not_replace_the_installed_pin(self):
        destination, source = self.copied_root()
        path = destination / source["local_path"]
        path.write_bytes(b"X" + path.read_bytes()[1:])
        changed = catalog_data()
        next(s for s in changed["sources"] if s["source_id"] == source["source_id"])["sha256"] = sha256(path.read_bytes()).hexdigest()
        (destination / evidence.CATALOG_PATH).write_bytes(canonical(changed))
        result = evidence.assess(inna_request(), root=destination)
        self.assertEqual(result["status"], "DEFER")
        self.assertFalse(result["source_attested"])
        self.assertEqual(result["catalog_sha256"], evidence.CATALOG_SHA256)

    def test_source_revocation_or_escape_is_unavailability_not_linguistic_negation(self):
        destination, source = self.copied_root()
        path = destination / source["local_path"]
        path.unlink()
        missing = evidence.assess(inna_request(), root=destination)
        self.assertEqual(missing["status"], "DEFER")
        path.symlink_to(ROOT / source["local_path"])
        escaped = evidence.assess(inna_request(), root=destination)
        self.assertEqual(escaped["status"], "DEFER")
        self.assertFalse(escaped["source_attested"])

    def test_changed_valid_span_metadata_does_not_retarget_a_fixed_record(self):
        destination, _ = self.copied_root()
        changed = catalog_data()
        record = next(r for r in changed["records"] if r["record_id"] == "qatr_inna_conditions")
        record["start"] += 1
        (destination / evidence.CATALOG_PATH).write_bytes(canonical(changed))
        self.assertEqual(evidence.assess(inna_request(), root=destination)["status"], "DEFER")

    def test_receipt_cannot_transfer_between_claims_or_claim_kinds(self):
        proposed = passage_request()
        result = evidence.assess(proposed)
        self.assertTrue(evidence.verify(result, proposed)["valid"])
        for changed in (passage_request("qatr_six_nouns"),
                        request("sibawayhi_han_examples", "EXTERNAL_EVENT", {"statement": "وقعت هذه الواقعة"})):
            with self.subTest(kind=changed["claim_kind"]):
                self.assertFalse(evidence.verify(result, changed)["valid"])

    def test_claimant_status_truth_or_integer_boolean_cannot_forge_a_report(self):
        proposed = passage_request()
        result = evidence.assess(proposed)
        for changes in ({"external_event_established": True}, {"universal_language_certified": True},
                        {"source_attested": 1}, {"application_established": True},
                        {"RealityWitness": True}, {"passage": None}):
            with self.subTest(changes=changes):
                forged = deepcopy(result)
                forged.update(changes)
                self.assertFalse(evidence.verify(forged, proposed)["valid"])

    def test_verified_mismatch_or_deferral_is_not_verification_of_the_claim(self):
        for proposed in (inna_request(options=["blocked"]), inna_request(form="light", options=[])):
            with self.subTest(proposed=proposed["candidate"]["inputs"]):
                result = evidence.assess(proposed)
                checked = evidence.verify(result, proposed)
                self.assertTrue(checked["valid"])
                self.assertIn(checked["claim_status"], ("MISMATCH", "DEFER"))
                self.assertFalse(checked["application_established"])


class StrictInputAndBudgetTests(unittest.TestCase):
    def test_unknown_installed_record_stays_unresolved(self):
        proposed = request("unregistered_record", "PASSAGE_ATTESTATION", {"text": "شاهد مزعوم"})
        result = evidence.assess(proposed)
        self.assertEqual(result["status"], "DEFER")
        self.assertFalse(result["source_attested"])

    def test_extra_flags_invalid_identity_and_unknown_versions_are_not_authority(self):
        changes = ({"trusted": True}, {"version": "uninstalled"}, {"record_id": "../../qatr"},
                   {"claim_kind": "WORLD_TRUE"})
        for change in changes:
            with self.subTest(change=change):
                proposed = inna_request()
                proposed.update(change)
                with self.assertRaises(ValueError):
                    evidence.assess(proposed)

    def test_interpreted_inputs_are_strict_not_truthy_or_guessed(self):
        for field, value in (("form", True), ("ma", 1), ("operator", "unknown")):
            with self.subTest(field=field):
                proposed = inna_request()
                proposed["candidate"]["inputs"][field] = value
                with self.assertRaises(ValueError):
                    evidence.assess(proposed)
        proposed = inna_request()
        proposed["candidate"]["inputs"]["trusted"] = True
        with self.assertRaises(ValueError):
            evidence.assess(proposed)

    def test_malformed_nonfinite_and_unbounded_values_do_not_become_evidence(self):
        for value in (float("nan"), float("inf"), object(), "\ud800", "x" * 65537):
            with self.subTest(type=type(value).__name__):
                proposed = inna_request()
                proposed["candidate"]["target_text"] = value
                with self.assertRaises(ValueError):
                    evidence.assess(proposed)

    def test_code_shaped_target_is_inert_and_still_not_parsed(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "must-not-exist"
            proposed = inna_request()
            proposed["candidate"]["target_text"] = f"__import__('pathlib').Path({str(marker)!r}).write_text('ran')"
            result = evidence.assess(proposed)
            self.assertEqual(result["status"], "CONDITIONALLY_CHECKED")
            self.assertFalse(result["target_parsed"])
            self.assertFalse(marker.exists())

    def test_large_valid_negative_report_replays_under_separate_report_budget(self):
        proposed = large_mismatch_request()
        self.assertEqual(len(canonical(proposed)), 524256)
        result = evidence.assess(proposed)
        self.assertEqual(result["status"], "MISMATCH")
        self.assertGreater(len(canonical(result)), evidence.MAX_JSON_BYTES)
        self.assertTrue(evidence.verify(result, proposed)["valid"])


class ClassicalEvidenceCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def cli(self, *args):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "tools/classical_language_evidence.py"),
                                 *map(str, args)], capture_output=True, check=False, timeout=30)
        self.assertFalse(result.stderr, result.stderr.decode("utf-8", errors="replace"))
        return result.returncode, json.loads(result.stdout), result.stdout

    def test_cli_preserves_mismatch_deferral_and_exact_verification(self):
        path = self.directory / "request.json"
        report_path = self.directory / "report.json"
        for proposed, expected_code, expected_status in (
            (inna_request(), 0, "CONDITIONALLY_CHECKED"),
            (inna_request(options=["blocked"]), 2, "MISMATCH"),
            (inna_request(form="light", options=[]), 3, "DEFER"),
        ):
            with self.subTest(status=expected_status):
                path.write_bytes(canonical(proposed) + b"\n")
                code, result, wire = self.cli("assess", path)
                self.assertEqual((code, result["status"]), (expected_code, expected_status))
                report_path.write_bytes(wire)
                code, verified, _ = self.cli("verify", report_path, "--request", path)
                self.assertEqual((code, verified["valid"], verified["claim_status"]),
                                 (0, True, expected_status))

    def test_large_negative_report_roundtrips_through_actual_cli_files(self):
        path = self.directory / "request.json"
        report_path = self.directory / "report.json"
        path.write_bytes(canonical(large_mismatch_request()) + b"\n")
        code, result, wire = self.cli("assess", path)
        self.assertEqual((code, result["status"]), (2, "MISMATCH"))
        self.assertGreater(len(wire), evidence.MAX_JSON_BYTES)
        report_path.write_bytes(wire)
        code, verified, _ = self.cli("verify", report_path, "--request", path)
        self.assertEqual((code, verified["valid"]), (0, True))

    def test_duplicate_json_keys_are_invalid_input(self):
        path = self.directory / "request.json"
        path.write_bytes(b'{"version":"one","version":"two"}')
        code, result, _ = self.cli("assess", path)
        self.assertEqual((code, result["status"]), (2, "INVALID_INPUT"))


class ClassicalConformanceCheckerTests(unittest.TestCase):
    """Checker mutation tests, not an independent oracle for all grammar rows."""

    def rows(self):
        return deepcopy(evidence.formal_rows())

    def export(self, rows):
        return "\n".join(canonical(row).decode("utf-8") for row in rows)

    def test_incomplete_or_duplicate_domain_is_rejected(self):
        from tools.check_classical_language_evidence import check_export
        rows = self.rows()
        with self.assertRaisesRegex(ValueError, "Expected 49"):
            check_export(self.export(rows[:-1]))
        rows[-1] = rows[0]
        with self.assertRaisesRegex(ValueError, "duplicate input tuple"):
            check_export(self.export(rows))

    def test_boolean_cannot_impersonate_a_source_partition_count(self):
        from tools.check_classical_language_evidence import check_export
        rows = self.rows()
        next(row for row in rows if row["kind"] == "awamil_partition")["samai"] = True
        with self.assertRaisesRegex(ValueError, "Invalid partition integer"):
            check_export(self.export(rows))

    def test_forged_well_typed_law_output_is_not_accepted(self):
        from tools.check_classical_language_evidence import check_export
        rows = self.rows()
        next(row for row in rows if row["kind"] == "course" and row["course"] == "nasb")["surface"] = "damma"
        with self.assertRaisesRegex(ValueError, "Python/Lean mismatch"):
            check_export(self.export(rows))

    def test_duplicate_json_key_is_rejected(self):
        from tools.check_classical_language_evidence import check_export
        raw = self.export(self.rows())
        raw = raw.replace('"course":"nasb"', '"course":"raf","course":"nasb"', 1)
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            check_export(raw)


if __name__ == "__main__":
    unittest.main()
