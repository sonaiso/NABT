"""Independent checker and evaluation-history boundary regression probes.

The source/payload attacks are not new held-out language cases. They address
an evaluator defect while keeping all historical scores and gold unchanged.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from nabt.semantics import SemanticKernel
from nabt.text_reader import parse_document, parse_query
from tools.text_evaluation.controlled import proof_errors
from tools.text_evaluation.integrity import (
    PUBLISHED, prepare_output_directory, require_output, verify_code_freeze,
    verify_published_inputs, write_report,
)
from tools.text_evaluation.source_oracle import clause_matches_source, source_clauses


def fixture(text: str, question: str):
    source = {"source_id": "seed", "scope": "default", "text": text}
    kernel = SemanticKernel()
    assert kernel.add_document(parse_document(text, source_id="seed")).accepted
    return kernel.query(parse_query(question)).as_dict(), {"seed": source}


class IndependentSourceReplay(unittest.TestCase):
    def test_valid_definition_conditional_and_quoted_tokens(self):
        text = ("تعريف «صنف و دقيق» هو نقي و محكم\n"
                "«سالم فإن سالم» هو نقي\n«سالم فإن سالم» هو محكم\n"
                "إذا كان ?س هو «صنف و دقيق» فإن ليس ?س هو معيب")
        question = "هل ليس «سالم فإن سالم» هو معيب؟"
        result, sources = fixture(text, question)
        self.assertEqual(proof_errors(result, question, sources), [])

    def test_forged_fact_payload_with_valid_source_hashes_is_rejected(self):
        result, sources = fixture("سالم هو نقي", "هل سالم هو نقي؟")
        result["query"]["predicate"] = "مخترع"
        cert = result["proofs"]["query"]
        cert["query"]["predicate"] = "مخترع"
        cert["steps"][0]["atom"]["predicate"] = "مخترع"
        cert["steps"][0]["clause"]["atom"]["predicate"] = "مخترع"
        self.assertIn("certificate_clause_not_licensed_by_source_text",
                      proof_errors(result, "هل سالم هو مخترع؟", sources))

    def test_forged_rule_payload_with_valid_source_hashes_is_rejected(self):
        result, sources = fixture("سالم هو نقي\nكل نقي هو محفوظ", "هل سالم هو محفوظ؟")
        result["query"]["predicate"] = "مخترع"
        cert = result["proofs"]["query"]
        cert["query"]["predicate"] = "مخترع"
        cert["steps"][-1]["atom"]["predicate"] = "مخترع"
        cert["steps"][-1]["clause"]["head"]["predicate"] = "مخترع"
        self.assertIn("certificate_clause_not_licensed_by_source_text",
                      proof_errors(result, "هل سالم هو مخترع؟", sources))

    def test_declared_or_question_text_cannot_authorize_a_fact(self):
        result, _ = fixture("سالم هو نقي", "هل سالم هو نقي؟")
        fact = result["proofs"]["query"]["steps"][0]["clause"]
        for text in ("هل سالم هو نقي؟", "مفهوم نقي", "ليس سالم هو نقي"):
            with self.subTest(text=text):
                source = {"source_id": "seed", "scope": "default", "text": text}
                self.assertFalse(clause_matches_source(fact, source))
        self.assertEqual(source_clauses({"source_id": "seed", "scope": "default",
                                         "text": "مفهوم نقي\nهل سالم هو نقي؟"}), [])

    def test_true_and_numeric_one_are_not_identical_evidence(self):
        result, sources = fixture("سالم هو نقي", "هل سالم هو نقي؟")
        result["proofs"]["query"]["steps"][0]["atom"]["positive"] = 1
        self.assertTrue(proof_errors(result, "هل سالم هو نقي؟", sources))

    def test_component_spans_must_belong_to_their_actual_roles(self):
        result, sources = fixture("سالم هو نقي", "هل سالم هو نقي؟")
        spans = result["proofs"]["query"]["steps"][0]["clause"]["component_spans"]
        spans[0], spans[-1] = spans[-1], spans[0]
        self.assertIn("certificate_clause_not_licensed_by_source_text",
                      proof_errors(result, "هل سالم هو نقي؟", sources))

    def test_unrelated_binding_cannot_be_smuggled_into_a_rule_step(self):
        result, sources = fixture("سالم هو نقي\nكل نقي هو محفوظ", "هل سالم هو محفوظ؟")
        result["proofs"]["query"]["steps"][-1]["binding"]["?زائد"] = "غائب"
        self.assertIn("certificate_binding_not_exact", proof_errors(result, "هل سالم هو محفوظ؟", sources))

    def test_malformed_certificate_is_a_named_failure_not_an_exception(self):
        result, sources = fixture("سالم هو نقي", "هل سالم هو نقي؟")
        result["proofs"] = {"unrecognized": None}
        self.assertTrue(proof_errors(result, "هل سالم هو نقي؟", sources))


class RuntimeFreezeIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "src/nabt").mkdir(parents=True)
        (self.root / "src/nabt/runtime.py").write_text("value = 1\n")
        (self.root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        self.path = self.root / "freeze.json"
        self.files = [{"path": name, "bytes": (self.root / name).stat().st_size,
                       "sha256": hashlib.sha256((self.root / name).read_bytes()).hexdigest()}
                      for name in ("pyproject.toml", "src/nabt/runtime.py")]

    def write(self, records):
        snapshot = hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.path.write_text(json.dumps({"files": records, "snapshot_sha256": snapshot}))

    def test_complete_exact_runtime_inventory_passes(self):
        self.write(self.files)
        self.assertEqual(len(verify_code_freeze(self.path, self.root)["files"]), 2)

    def test_empty_or_partial_freeze_is_not_a_bypass(self):
        for records in ([], self.files[:1]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                self.write(records)
                verify_code_freeze(self.path, self.root)

    def test_duplicate_inventory_entry_is_rejected(self):
        self.write(self.files + [self.files[0]])
        with self.assertRaises(ValueError):
            verify_code_freeze(self.path, self.root)

    def test_manifest_cannot_omit_a_new_runtime_file(self):
        self.write(self.files)
        (self.root / "src/nabt/new_module.py").write_text("new = 2\n")
        with self.assertRaises(ValueError):
            verify_code_freeze(self.path, self.root)

    def test_self_hash_and_boolean_lengths_are_checked(self):
        self.write(self.files)
        data = json.loads(self.path.read_text())
        data["snapshot_sha256"] = "0" * 64
        self.path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            verify_code_freeze(self.path, self.root)
        records = copy.deepcopy(self.files)
        records[0]["bytes"] = True
        self.write(records)
        with self.assertRaises(ValueError):
            verify_code_freeze(self.path, self.root)

    def test_noncanonical_path_cannot_escape_inventory(self):
        records = copy.deepcopy(self.files)
        records[1]["path"] = "src/../pyproject.toml"
        self.write(records)
        with self.assertRaises(ValueError):
            verify_code_freeze(self.path, self.root)


class PublishedDataAndOutputIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_protocol_and_manifest_cannot_be_changed_together(self):
        data = self.root / "copy"
        data.mkdir()
        manifest = json.loads((PUBLISHED / "artifact_manifest.json").read_text())
        protocol = b'{"source_manifest":"changed.json"}'
        (data / "natural_probe_protocol.json").write_bytes(protocol)
        for record in manifest["files"]:
            if record["path"] == "natural_probe_protocol.json":
                record["sha256"] = hashlib.sha256(protocol).hexdigest()
                record["bytes"] = len(protocol)
        (data / "artifact_manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "manifest checksum"):
            verify_published_inputs(data)

    def test_changed_gold_or_protocol_is_rejected_with_original_manifest(self):
        data = self.root / "copy"
        # Copy only the pinned artifacts, keeping release reports untouched.
        data.mkdir()
        manifest = json.loads((PUBLISHED / "artifact_manifest.json").read_text())
        shutil.copyfile(PUBLISHED / "artifact_manifest.json", data / "artifact_manifest.json")
        for entry in manifest["files"]:
            shutil.copyfile(PUBLISHED / entry["path"], data / entry["path"])
        self.assertEqual(verify_published_inputs(data)["artifacts_checked"], 27)
        target = data / "natural_probe_protocol.json"
        target.write_bytes(target.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "natural_probe_protocol"):
            verify_published_inputs(data)

    def test_history_subdirectory_is_protected_before_creation(self):
        target = PUBLISHED / "release/evaluator_must_not_create/report.json"
        with self.assertRaises(ValueError):
            require_output(target)
        self.assertFalse(target.exists())

    def test_input_copy_and_freeze_cannot_be_output_destinations(self):
        data = self.root / "data"
        data.mkdir()
        freeze = self.root / "freeze.json"
        freeze.write_text("{}")
        with self.assertRaises(ValueError):
            require_output(data / "report.json", data=data)
        with self.assertRaises(ValueError):
            prepare_output_directory(self.root, data=data, freeze=freeze)
        with self.assertRaises(ValueError):
            require_output(freeze, data=data, freeze=freeze)

    def test_symlink_to_history_and_existing_reports_are_protected(self):
        link = self.root / "history"
        link.symlink_to(PUBLISHED, target_is_directory=True)
        with self.assertRaises(ValueError):
            require_output(link / "new.json")
        target = self.root / "report.json"
        write_report(target, {"run": 1})
        before = target.read_bytes()
        with self.assertRaises(ValueError):
            write_report(target, {"run": 2})
        self.assertEqual(target.read_bytes(), before)

    def test_nonempty_output_directory_is_not_reused(self):
        output = self.root / "run"
        output.mkdir()
        (output / "unrelated.txt").write_text("preserve")
        with self.assertRaises(ValueError):
            prepare_output_directory(output, data=PUBLISHED, freeze=PUBLISHED / "code_freeze_reserve20_portable.json")


if __name__ == "__main__":
    unittest.main()
