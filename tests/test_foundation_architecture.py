"""Admission denial and architecture mutations, not a language coverage score."""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nabt import foundation
from nabt.alphabet import parse_word
from nabt.certificates import issue_certificate, verify_certificate
from nabt.errors import NabtError
from nabt.machine import Machine
from nabt.semantics import SemanticKernel
from tools import check_foundation_architecture as architecture

ROOT = Path(__file__).resolve().parents[1]
DENIED = "FOUNDATION_TEST_DENIED"


def denial(*_args, **_kwargs):
    raise NabtError(DENIED, "Architecture test denies installed authority", status="DEFER")


class FoundationArchitectureTests(unittest.TestCase):
    def assert_denied(self, action):
        with patch.object(foundation, "require_foundation", side_effect=denial) as gate:
            with self.assertRaises(NabtError) as error:
                action()
            self.assertEqual(error.exception.code, DENIED)
            self.assertGreater(gate.call_count, 0)

    def test_real_registry_and_current_dispatch_inventory(self):
        result = architecture.check(ROOT)
        self.assertTrue(result["ok"])
        self.assertFalse(result["projection_completeness_established"])
        self.assertGreater(result["guarded_surfaces"], 100)

    def test_warm_machine_and_certificate_paths_are_denied(self):
        cells = parse_word("كَتَبَ")
        machine = Machine()
        self.assertTrue(machine.analyse(cells).licensed)
        certificate = issue_certificate(cells, source_text="كَتَبَ")
        self.assertTrue(verify_certificate(certificate).valid)
        for action in (lambda: machine.analyse(cells), lambda: issue_certificate(cells),
                       lambda: verify_certificate(certificate)):
            self.assert_denied(action)

    def test_warm_semantic_kernel_cannot_keep_granting_after_denial(self):
        kernel = SemanticKernel()
        self.assertTrue(kernel.add_source("نادر هو حاضر.").accepted)
        result = kernel.query("هل نادر هو حاضر؟")
        self.assertEqual(result.status, "SUPPORTED")
        certificate = result.proofs["query"]
        self.assertTrue(kernel.verify_certificate(certificate)["accepted"])
        for action in (lambda: kernel.query("هل نادر هو حاضر؟"),
                       lambda: kernel.verify_certificate(certificate),
                       lambda: kernel.add_source("جابر هو حاضر.", source_id="next")):
            self.assert_denied(action)

    def test_cli_reports_structured_denial(self):
        from nabt.cli import main
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["analyse", "كَتَبَ"]), 0)
        self.assertTrue(json.loads(output.getvalue())["licensed"])
        errors = io.StringIO()
        with patch.object(foundation, "require_foundation", side_effect=denial), redirect_stderr(errors):
            self.assertEqual(main(["analyse", "كَتَبَ"]), 3)
        self.assertEqual(json.loads(errors.getvalue())["code"], DENIED)

    def test_program_conditional_and_reader_admissions_are_guarded(self):
        from nabt.program import compile_request, execute_program, verify_execution
        from nabt import classical_laws
        from nabt.word_reader import read_words
        program = compile_request({"task": "word_shape", "text": "كَتَبَ"})
        receipt = execute_program(program)
        self.assertEqual(receipt["run_status"], "COMPLETED")
        verification = verify_execution(receipt)
        self.assertTrue(verification["valid"])
        frame = {"root": ["ء", "ك", "ل"], "profile": "all_attested"}
        conditional = classical_laws.evaluate("HAMZA-LEXICAL-COMMAND", frame)
        self.assertTrue(classical_laws.verify(conditional)["valid"])
        word = read_words("زَيْدٌ")
        self.assertEqual(word["raw_text"], "زَيْدٌ")
        self.assertTrue(word["occurrences"][0]["alternatives"])
        for action in (lambda: execute_program(program), lambda: verify_execution(receipt),
                       lambda: classical_laws.evaluate("HAMZA-LEXICAL-COMMAND", frame),
                       lambda: classical_laws.verify(conditional), lambda: read_words("زَيْدٌ")):
            self.assert_denied(action)

    def test_retrieval_and_model_rankings_do_not_escape_foundation(self):
        from tools.grammar_catalog.retrieval import SearchIndex
        from tools.qatr_training.proposal import project_ranking
        index = SearchIndex()
        found = index.search("همزة الوصل")
        self.assertTrue(found["candidates"])
        self.assertEqual(found["authority"], "RETRIEVAL_ONLY")
        reading = {"cases": ["raf"], "rows": [{"case": "raf"}]}
        ranked = project_ranking(reading, [0.0, 1.0, 0.0, 0.0])
        self.assertEqual(ranked["authority"], "NONE")
        self.assertFalse(ranked["reading_licensed"])
        self.assert_denied(lambda: index.search("همزة الوصل"))
        self.assert_denied(lambda: project_ranking(reading, [0.0, 1.0, 0.0, 0.0]))

    def test_certified_lexical_entry_cannot_bypass_foundation(self):
        from tools.linguistic_truth.certified import acquire_certified
        # A CLI-only guard would leave this direct admission path unprotected.
        # Denial must happen before lexical acquisition or native execution.
        self.assert_denied(lambda: acquire_certified("عَيْنٌ"))

    @unittest.skipUnless((ROOT / "formal/.lake/build/bin/licensedInference").is_file(), "native checker built in native CI")
    def test_native_inference_and_transport_positive_then_denied(self):
        from tools.licensed_inference.runtime import evaluate
        from tools import proof_lab
        source, query = "سَارَ زَيْدٌ.", "هَلْ سَارَ زَيْدٌ؟"
        result = evaluate(source, query)
        self.assertEqual(result["status"], "SUPPORTED")
        self.assertTrue(result["native_checked"])
        self.assert_denied(lambda: evaluate(source, query))
        request = json.dumps({"schema": proof_lab.REQUEST_SCHEMA, "mode": "inference",
                              "source_text": source, "query_text": query}, ensure_ascii=False)
        report = proof_lab.run_payload(proof_lab.SMOKE_ID, request)
        self.assertEqual(report["status"], "SUPPORTED")
        self.assertTrue(report["result"]["verified"])
        self.assert_denied(lambda: proof_lab.run_payload(proof_lab.SMOKE_ID, request))

    @unittest.skipUnless((ROOT / "formal/.lake/build/bin/lexicalDenotation").is_file(), "native checker built in native CI")
    def test_native_lexical_testimony_positive_then_denied(self):
        from tools.lexical_testimony import assess
        result = assess("فرس", ["واحد الخيل"])
        self.assertTrue(result["native_checked"])
        self.assertEqual(result["common_indications"], ["mutabaqa"])
        self.assert_denied(lambda: assess("فرس", ["واحد الخيل"]))

    def test_corrupt_installed_law_after_warm_cache_closes_admission(self):
        cells = parse_word("كَتَبَ")
        machine = Machine()
        self.assertTrue(machine.analyse(cells).licensed)
        kernel = SemanticKernel()
        self.assertTrue(kernel.add_source("نادر هو حاضر.").accepted)
        self.assertEqual(kernel.query("هل نادر هو حاضر؟").status, "SUPPORTED")
        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory)
            (installed / "data").mkdir()
            raw = (ROOT / "src/nabt/data/law.json").read_bytes()
            (installed / "data/law.json").write_bytes(raw + b" ")
            with patch.object(foundation, "files", return_value=installed):
                for action in (lambda: machine.analyse(cells), lambda: kernel.query("هل نادر هو حاضر؟")):
                    with self.assertRaises(NabtError) as error:
                        action()
                    self.assertEqual(error.exception.code, "FOUNDATION_INTEGRITY")

    def test_intrinsic_codecs_keep_exact_domain_without_recursive_guard(self):
        from nabt.codec import encode_cells, decode_number
        with patch.object(foundation, "require_foundation", side_effect=denial) as gate:
            # These are typed representation primitives, not acceptance decisions.
            self.assertEqual(decode_number(encode_cells([0, 115, 0])), (0, 115, 0))
            for cells in ([True], [116], [-1]):
                with self.assertRaises(NabtError):
                    encode_cells(cells)
            gate.assert_not_called()

    def test_import_only_or_conditional_guard_mutation_is_detected(self):
        registry = json.loads((ROOT / architecture.REGISTRY).read_text())
        row = next(r for r in registry["surfaces"] if r["id"] == "tools.qatr_training.proposal.project_ranking")
        original = (ROOT / row["path"]).read_text()
        guard = "    foundation.require_foundation('tools.qatr_training.proposal.project_ranking')\n"
        self.assertIn(guard, original)
        for replacement in ("", "    if False:\n    " + guard):
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                target = root / row["path"]
                target.parent.mkdir(parents=True)
                target.write_text(original.replace(guard, replacement))
                with self.assertRaises(architecture.ArchitectureError):
                    architecture.validate_surface(row, root)
        # Execute the removed-guard mutant: a real proposal bypass exists even
        # though the shared module remains imported. The architecture gate kills it.
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "mutant.py"
            target.write_text(original.replace(guard, ""))
            spec = importlib.util.spec_from_file_location("foundation_ranker_mutant", target)
            mutant = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mutant)
            with patch.object(foundation, "require_foundation", side_effect=denial) as gate:
                result = mutant.project_ranking({"cases": ["raf"], "rows": [{"case": "raf"}]}, [0, 1, 0, 0])
                self.assertEqual(result["ranked_cases"], ["raf"])
                gate.assert_not_called()

    def test_new_grant_function_and_new_cli_are_discovered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tools").mkdir()
            (root / "tools/new_backend.py").write_text(
                "def new_backend():\n    return {'native_checked': True, 'verified': True}\n")
            self.assertEqual(architecture.unregistered_grants(root, {
                "surfaces": [], "non_authority_grant_sites": []}), ["tools/new_backend.py:new_backend"])
            (root / "tools/new_backend.py").write_text(
                "def new_backend():\n    return {'strict_language_accepted': True, 'certified_from_a116': True}\n")
            self.assertEqual(architecture.unregistered_grants(root, {
                "surfaces": [], "non_authority_grant_sites": []}), ["tools/new_backend.py:new_backend"])
        source = (ROOT / "src/nabt/cli.py").read_text()
        changed = source.replace('sub.add_parser("law")', 'sub.add_parser("law")\n    sub.add_parser("unreviewed-backend")')
        self.assertIn("unreviewed-backend", architecture.cli_commands(changed))
        self.assertNotEqual(architecture.cli_commands(source), architecture.cli_commands(changed))

    def test_new_module_or_public_helper_with_computed_grant_requires_review(self):
        # Freeze a small, real discoverable repository skeleton before adding
        # the new adapter. Its computed grant intentionally evades the limited
        # literal-True scanner, so only the source-module inventory can catch it.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ("pyproject.toml", "formal/lakefile.lean", "src/nabt/cli.py",
                             "src/nabt/foundation.py", "tools/proof_lab.py",
                             "integrations/proof_lab/site/worker/server.mjs"):
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / relative).read_bytes())
            helper = root / "tools/existing_helper.py"
            helper.write_text("def identity(value):\n    return value\n")
            registry = {"schema": "nabt.framework-foundation.v1",
                        "foundation_law_id": "nabt.foundation.v1", "surfaces": [],
                        "non_authority_grant_sites": [], "discovery": architecture.discover(root, [])}
            destination = root / architecture.REGISTRY
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(registry))
            self.assertTrue(architecture.check(root)["ok"])
            dynamic = (
                "def answer(flag):\n    granted = bool(flag)\n"
                "    return {'native_checked': granted, 'verified': granted}\n")
            new_module = root / "tools/new_dynamic_backend.py"
            new_module.write_text(dynamic)
            self.assertEqual(architecture.unregistered_grants(root, registry), [])
            with self.assertRaisesRegex(architecture.ArchitectureError, "python_source_modules"):
                architecture.check(root)
            new_module.unlink()
            helper.write_text(helper.read_text() + "\n" + dynamic)
            self.assertEqual(architecture.unregistered_grants(root, registry), [])
            with self.assertRaisesRegex(architecture.ArchitectureError, "public_python_api"):
                architecture.check(root)

    def test_malformed_text_is_blocked_before_native_execution(self):
        from tools.licensed_inference import runtime
        with patch.object(runtime, "_native") as native:
            result = runtime.evaluate("سَارَُ زَيْدٌ.", "هَلْ سَارَ زَيْدٌ؟")
            self.assertEqual(result["status"], "INVALID_INPUT")
            self.assertFalse(result["native_checked"])
            native.assert_not_called()


if __name__ == "__main__":
    unittest.main()
