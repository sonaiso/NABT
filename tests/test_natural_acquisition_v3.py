"""Specification-derived controls for the additive natural lexical reader.

These implementation tests are separate from the preimplementation gold. The
native integration assertions use the installed checker and retained sources.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import natural_acquisition_v3 as natural


class NaturalSyntax(unittest.TestCase):
    def test_compositional_phrases_and_case_agreement(self):
        pairs = (("عين جارية", "ayn_spring"), ("العين الباصرة", "ayn_eye"),
                 ("عَيْنٌ جَارِيَةٌ", "ayn_spring"),
                 ("عَيْناً بَاصِرَةً", "ayn_eye"),
                 ("عَيْنٍ بَاصِرَةٍ", "ayn_eye"),
                 ("الْعَيْنِ الْجَارِيَةِ", "ayn_spring"))
        for raw, expected in pairs:
            with self.subTest(raw=raw):
                row = natural._parse(raw)
                self.assertEqual(row["sense"], expected)
                self.assertEqual(row["assertion_polarity"], "none")
        for raw in ("عَيْنٌ جَارِيَةً", "الْعَيْنُ الْجَارِيَةِ", "العين جارية",
                    "عين الجارية", "عين جَارِيَةٌ", "عَيْنٌ جارية", "عينًا جارية"):
            with self.subTest(raw=raw):
                self.assertIsNone(natural._parse(raw))

    def test_perception_negation_and_subject_substitution(self):
        for raw in ("رأيت عيناً جارية", "رأيت عينًا جارية", "رأيت العين الجارية",
                    "رَأَيْتُ عَيْنًا جَارِيَةً", "رَأَيْتُ الْعَيْنَ الْجَارِيَةَ"):
            self.assertEqual(natural._parse(raw)["assertion_polarity"], "positive")
        for raw in ("لم أر عيناً باصرة", "لم أر العين الباصرة", "لَمْ أَرَ عَيْنًا بَاصِرَةً"):
            self.assertEqual(natural._parse(raw)["assertion_polarity"], "negative")
        for subject in ("زيد", "عمرو", "المسافر"):
            self.assertEqual(natural._parse(f"شرب {subject} من عين جارية")["sense"], "ayn_spring")
        self.assertEqual(natural._parse("شَرِبَ زَيْدٌ مِنْ عَيْنٍ جَارِيَةٍ")["sense"], "ayn_spring")
        for raw in ("شرب هو من عين جارية", "شرب زيد من عين باصرة", "شرب زيد من عين",
                    "رأيت عين جارية", "رأيت عَيْنًا جَارِيَةً", "رَأَيْتُ عَيْنٌ جَارِيَةٌ",
                    "لم أر عيناً", "ما رأيت عينًا جارية", "شَرِبَ زَيْدٌ مِنْ عَيْنًا جَارِيَةً"):
            self.assertIsNone(natural._parse(raw))

    def test_whole_clause_barriers_and_exact_offsets(self):
        raw = " \tرأيت\t\tعينًا  جارية .\t"
        row = natural._parse(raw)
        self.assertEqual(raw.encode()[row["start_byte"]:row["end_byte"]].decode(), "عينًا")
        for text in ("«عين جارية»", "قال عين جارية", "عين جارية؟", "عين جارية ربما",
                     "عين جارية. عين باصرة", "عين\nجارية", "عين\u00a0جارية",
                     "عين، جارية", "عين\u0000 جارية", "عين جارية.."):
            self.assertIsNone(natural._parse(text))


class NaturalSourceBoundary(unittest.TestCase):
    def test_retained_sources_and_all_eight_spans_replay(self):
        packet = natural.source_inventory()
        self.assertEqual(len(packet["sources"]), 4)
        self.assertEqual(len(packet["passages"]), 8)
        self.assertEqual({row["sense_id"] for row in packet["added_senses"]},
                         {"ayn_eye", "ayn_spring", "ayn_gold"})

    def test_missing_or_modified_registry_has_no_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / natural.SOURCE_PATH
            path.parent.mkdir(parents=True)
            packet = json.loads((natural.ROOT / natural.SOURCE_PATH).read_bytes())
            packet["added_senses"][0]["sense_id"] = "forged"
            path.write_text(json.dumps(packet))
            with patch.object(natural, "ROOT", root):
                self.assertEqual(natural.evaluate("عين جارية")["status"], "SOURCE_UNAVAILABLE")

    def test_source_file_change_is_rejected_with_unchanged_registry(self):
        packet = natural.source_inventory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = [natural.SOURCE_PATH] + [Path(row["path"]) for row in packet["sources"]]
            for path in paths:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((natural.ROOT / path).read_bytes())
            target = root / packet["sources"][-1]["path"]
            data = target.read_bytes()
            target.write_bytes(b"!" + data[1:])
            with patch.object(natural, "ROOT", root):
                self.assertEqual(natural.evaluate("عين جارية")["status"], "SOURCE_UNAVAILABLE")

    def test_noncanonical_and_same_bytes_symlink_paths_are_rejected(self):
        for path in ("/tmp/source", "./source", "evidence//source", "evidence/../source"):
            with self.assertRaises(ValueError):
                natural._installed_path(path)
        original = natural.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / natural.SOURCE_PATH
            path.parent.mkdir(parents=True)
            path.symlink_to(original / natural.SOURCE_PATH)
            with patch.object(natural, "ROOT", root):
                self.assertEqual(natural.evaluate("عين جارية")["status"], "SOURCE_UNAVAILABLE")
            path.unlink()
            path.write_bytes((original / natural.SOURCE_PATH).read_bytes())
            packet = json.loads(path.read_bytes())
            source = root / packet["sources"][0]["path"]
            source.parent.mkdir(parents=True, exist_ok=True)
            source.symlink_to(original / packet["sources"][0]["path"])
            with patch.object(natural, "ROOT", root):
                self.assertEqual(natural.evaluate("عين جارية")["status"], "SOURCE_UNAVAILABLE")

    def test_input_and_resource_errors_remain_separate(self):
        for raw in (True, {}, [], 12, b"\xff", "\ud800", "", " \t"):
            self.assertEqual(natural.evaluate(raw)["status"], "INVALID_INPUT")
        for kwargs in ({"source_id": True}, {"revision": ""}, {"scope": "\ud800"},
                       {"ending": True}, {"onset": "CONNECTED"}):
            self.assertEqual(natural.evaluate("عين جارية", **kwargs)["status"], "INVALID_INPUT")
        self.assertEqual(natural.evaluate("ع" * natural.MAX_BYTES)["status"], "RESOURCE_EXHAUSTED")


class NaturalNativeIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (natural.ROOT / "formal/.lake/build/bin/linguisticTruth").is_file():
            raise unittest.SkipTest("build the existing linguisticTruth native target")

    def test_positive_reading_retains_every_installed_alternative(self):
        report = natural.evaluate("شرب المسافر من عين جارية")
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["selected_sense_ids"], ["ayn_spring"])
        self.assertEqual(report["candidate_sense_ids"], ["ayn_eye", "ayn_gold", "ayn_spring"])
        self.assertTrue(report["native_checked"])
        for key in ("author_intention_established", "reference_resolved", "grammar_certified",
                    "world_truth_established", "all_arabic_complete", "all_arabic_senses_enumerated",
                    "general_acquisition_refinement_proved"):
            self.assertIs(report[key], False)
        occurrence = report["occurrences"][0]
        statuses = {row["sense_id"]: row["support_status"] for row in occurrence["candidates"]}
        self.assertEqual(statuses, {"ayn_eye": "UNKNOWN_PREMISE", "ayn_spring": "SUPPORTED_PREMISES",
                                    "ayn_gold": "UNKNOWN_PREMISE"})

    def test_negation_does_not_negate_lexical_reading(self):
        positive = natural.evaluate("رأيت عينًا باصرة")
        negative = natural.evaluate("لم أر عينًا باصرة")
        self.assertEqual(positive["selected_sense_ids"], negative["selected_sense_ids"])
        self.assertEqual(negative["assertion_polarity"], "negative")
        self.assertFalse(negative["world_truth_established"])
        used = [atom for atom in negative["occurrences"][0]["native_request"]["known"]
                if atom["value"]["kind"] == "used"]
        self.assertEqual(len(used), 1)
        self.assertIs(used[0]["positive"], True)

    def test_ambiguity_and_tanwin_aliases_are_preserved_without_alif_stripping(self):
        for text in ("رأيت عيناً", "رأيت عينًا", "رأيت عَيْناً"):
            report = natural.evaluate(text)
            self.assertEqual(report["candidate_sense_ids"], ["ayn_eye", "ayn_gold", "ayn_spring"])
            self.assertEqual(report["selected_sense_ids"], [])
            self.assertEqual(report["status"], "UNKNOWN")
        report = natural.evaluate("رأيت أسداً يزأر في القفص")
        self.assertEqual(report["candidate_sense_ids"], ["asad_animal", "asad_brave"])
        self.assertEqual(report["selected_sense_ids"], [])
        self.assertEqual(natural.evaluate("رأيت عينا")["candidate_sense_ids"], [])

    def test_source_bytes_and_caller_binding_are_not_rewritten(self):
        raw = " \tلم أر عينًا  جارية.\t"
        report = natural.evaluate(raw.encode(), source_id="s-9", revision="opaque-7", scope="scope-4")
        self.assertEqual(report["source"], {"source_id": "s-9", "revision": "opaque-7",
            "raw_text": raw, "sha256": hashlib.sha256(raw.encode()).hexdigest(), "bytes": len(raw.encode())})
        frame = report["occurrences"][0]["native_request"]["frame"]["occurrence"]
        self.assertEqual(frame["raw"], raw)
        self.assertEqual(frame["revision"], "opaque-7")
        self.assertEqual(frame["source"], "s-9")
        self.assertEqual(frame["context"], "scope-4")
        self.assertEqual(raw.encode()[frame["start_byte"]:frame["end_byte"]].decode(), "عينًا")

    def test_native_forgery_cannot_supply_selected_sense(self):
        original = natural._verify_native
        def forged(request, root):
            result = original(request, root)
            result["rows"][0]["candidate"]["intended_sense"] = "forged"
            return result
        with patch.object(natural, "_verify_native", side_effect=forged):
            report = natural.evaluate("عين جارية")
        self.assertEqual(report["status"], "VERIFICATION_UNAVAILABLE")
        self.assertEqual(report["selected_sense_ids"], [])
        self.assertFalse(report["semantic_scope_complete"])
        self.assertFalse(report["chain_complete"])

    def test_native_exhaustion_is_not_linguistic_rejection(self):
        with patch.object(natural, "_verify_native", side_effect=OverflowError("native budget")):
            report = natural.evaluate("عين جارية")
        self.assertEqual(report["status"], "RESOURCE_EXHAUSTED")
        self.assertFalse(report["semantic_scope_complete"])
        self.assertFalse(report["chain_complete"])

    def test_external_receipt_requires_fresh_original_binding(self):
        text = "عين جارية"
        report = natural.evaluate(text)
        self.assertTrue(natural.verify(report, text=text)["replay_matches"])
        for mutation in ("selected", "revision", "span"):
            changed = deepcopy(report)
            if mutation == "selected":
                changed["selected_sense_ids"] = ["ayn_gold"]
            elif mutation == "revision":
                changed["source"]["revision"] = "caller-relabelled"
            else:
                changed["occurrences"][0]["span"]["end_byte"] += 1
            self.assertFalse(natural.verify(changed, text=text)["replay_matches"])
        self.assertFalse(natural.verify(report, text=text, scope="other")["replay_matches"])

    def test_json_equivalent_python_objects_do_not_bypass_receipt_types(self):
        report = natural.evaluate("عين جارية")
        changed = deepcopy(report)
        changed["candidate_sense_ids"] = tuple(changed["candidate_sense_ids"])
        self.assertFalse(natural.verify(changed, text="عين جارية")["replay_matches"])
        class DictionarySubclass(dict):
            pass
        changed = deepcopy(report)
        changed["source"] = DictionarySubclass(changed["source"])
        self.assertFalse(natural.verify(changed, text="عين جارية")["replay_matches"])
        changed = deepcopy(report)
        changed["source"][1] = "nonstring object key"
        self.assertFalse(natural.verify(changed, text="عين جارية")["replay_matches"])
        self.assertFalse(natural.verify({"bad": float("nan")}, text="عين جارية")["replay_matches"])

    def test_produced_receipt_limit_erases_partial_success(self):
        with patch.object(natural, "MAX_RECEIPT_BYTES", 2048):
            report = natural.evaluate("عين جارية")
        self.assertEqual(report["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(report["reason"], "MAX_RECEIPT_BYTES")
        self.assertEqual(report["selected_sense_ids"], [])
        self.assertEqual(report["occurrences"], [])
        self.assertFalse(report["semantic_scope_complete"])
        self.assertFalse(report["chain_complete"])
        self.assertLessEqual(len(natural._receipt_wire(report)), 2048)

    def test_occurrence_limit_returns_consistent_empty_diagnostics(self):
        with patch.object(natural, "MAX_OCCURRENCES", 1):
            report = natural.evaluate("عين عين")
        self.assertEqual(report["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(report["reason"], "MAX_OCCURRENCES")
        self.assertEqual(report["source"]["raw_text"], "عين عين")
        self.assertEqual(report["occurrences"], [])
        self.assertEqual(report["candidate_sense_ids"], [])
        self.assertEqual(report["selected_sense_ids"], [])
        self.assertFalse(report["native_checked"])
        self.assertFalse(report["semantic_scope_complete"])
        self.assertFalse(report["chain_complete"])


class NaturalConnectedIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        targets = ("linguisticTruth", "connectedAcquisitionV3")
        if any(not (natural.ROOT / "formal/.lake/build/bin" / name).is_file() for name in targets):
            raise unittest.SkipTest("build linguisticTruth and connectedAcquisitionV3")

    def test_actual_marked_source_to_native_meaning_chain_in_both_modes(self):
        for adjective, sense in (("الْجَارِيَةُ", "ayn_spring"), ("الْبَاصِرَةُ", "ayn_eye")):
            raw = "الْعَيْنُ " + adjective
            for onset in ("word_initial", "connected"):
                for ending in ("wasl", "waqf"):
                    with self.subTest(text=raw, onset=onset, ending=ending):
                        report = natural.evaluate(raw, onset=onset, ending=ending)
                        self.assertEqual(report["selected_sense_ids"], [sense])
                        self.assertTrue(report["chain_complete"])
                        acquired = report["acquisition"]
                        self.assertEqual(acquired["acquisition"]["text"], raw)
                        self.assertIs(acquired["verified"], True)
                        self.assertIs(acquired["shape_verified"], True)
                        if onset == "connected":
                            self.assertEqual(acquired["phrase_shape"]["status"], "SHAPE_LICENSED")
                            self.assertEqual(acquired["shape_handoffs"], [])
                            citation = acquired["acquisition"]["words"][1]["cells"]
                            realized = acquired["realization"]["words"][1]["cells"]
                            self.assertEqual(realized, citation[1:])
                        else:
                            self.assertIsNone(acquired["phrase_shape"])
                            self.assertEqual(len(acquired["shape_handoffs"]), 2)

    def test_unmarked_semantics_never_completes_missing_sound_acquisition(self):
        report = natural.evaluate("عين جارية", onset="connected")
        self.assertTrue(report["semantic_scope_complete"])
        self.assertFalse(report["chain_complete"])
        self.assertNotEqual(report["acquisition"]["status"], "ACQUIRED")

    def test_verified_chain_rejects_forged_acquisition_or_scope(self):
        text = "الْعَيْنُ الْجَارِيَةُ"
        report = natural.evaluate(text, onset="connected", scope="speech-1")
        self.assertTrue(natural.verify(report, text=text, onset="connected", scope="speech-1")["valid"])
        changed = deepcopy(report)
        changed["acquisition"]["realization"]["words"][1]["cells"][0] += 1
        self.assertFalse(natural.verify(changed, text=text, onset="connected", scope="speech-1")["valid"])
        self.assertFalse(natural.verify(report, text=text, onset="connected", scope="speech-2")["valid"])


if __name__ == "__main__":
    unittest.main()
