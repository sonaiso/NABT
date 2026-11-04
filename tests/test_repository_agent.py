"""Actual Git/process boundary tests; mini-repo reuse output is a test double.

The separate CI demo uses NABT's real compiled-catalogue/reuse implementation.
These cases test task control, not Arabic or formal theorem correctness.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.repo_agent import manager, policy, repository, state
from tools.entropy_framework.reuse_run import describe_entries, entry_command


def inputs(base, relative="docs/guide.md", original=b"before\n", content="after\n"):
    task = {"schema": "nabt.repo-agent.task.v1", "id": "repair-guide", "base_commit": base,
            "goal": "Clarify the documented operation", "allowed_paths": [relative],
            "acceptance": ["A reviewer can reproduce the operation."]}
    proposal = {"schema": "nabt.repo-agent.proposal.v1", "base_commit": base, "rationale": "Clarify the operation using its existing owner.",
                "changes": [{"path": relative, "before_sha256": policy.digest(original) if original is not None else None, "content": content}]}
    return task, proposal


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.task, self.proposal = inputs("a" * 40)

    def test_closed_schemas_reject_commands_and_claimed_success(self):
        for target, key, value in (("task", "command", ["sh"]), ("proposal", "passed", True),
                                   ("proposal", "checks", []), ("task", "skip_checks", True)):
            task, proposal = deepcopy(self.task), deepcopy(self.proposal)
            (task if target == "task" else proposal)[key] = value
            with self.subTest(key=key), self.assertRaises(policy.AgentError):
                policy.validate(task, proposal)

    def test_rejects_paths_escaping_or_reinterpreting_scope(self):
        for relative in ("../docs/a.md", "/docs/a.md", "docs/../a.md", "docs//a.md", "docs/.git/a", "docs/.gitattributes", "docs/a\nb", "docs\\a"):
            with self.subTest(path=relative), self.assertRaises(policy.AgentError):
                policy.validate(*inputs("a" * 40, relative))

    def test_protects_policy_witnesses_and_existing_tests(self):
        for relative in ("tools/repo_agent/policy.py", "tools/entropy_framework/registry.json", "tools/check_integrity.py",
                         "tools/meaning_preservation_v1.mk", "src/nabt/data/table.json", "tests/test_existing.py", "evidence/gold.json", "Makefile", "AGENTS.md", ".github/workflows/ci.yml"):
            with self.subTest(path=relative), self.assertRaises(policy.AgentError) as error:
                policy.validate(*inputs("a" * 40, relative))
            self.assertEqual(error.exception.code, "PROTECTED_PATH")

    def test_new_discoverable_tests_are_allowed_but_package_hooks_are_not(self):
        policy.validate(*inputs("a" * 40, "tests/test_new_boundary.py", None))
        with self.assertRaises(policy.AgentError):
            policy.validate(*inputs("a" * 40, "tests/__init__.py", None))

    def test_exact_scope_duplicates_and_ancestor_overlap(self):
        proposal = deepcopy(self.proposal)
        proposal["changes"][0]["path"] = "docs/other.md"
        with self.assertRaises(policy.AgentError):
            policy.validate(self.task, proposal)
        proposal["changes"] = self.proposal["changes"] * 2
        with self.assertRaises(policy.AgentError):
            policy.validate(self.task, proposal)
        task, proposal = inputs("a" * 40, "docs/a", None)
        task["allowed_paths"].append("docs/a/b")
        proposal["changes"].append({"path": "docs/a/b", "before_sha256": None, "content": "x"})
        with self.assertRaises(policy.AgentError):
            policy.validate(task, proposal)

    def test_scalar_types_and_byte_limits(self):
        for value in (True, 1, [], "\ud800", "a\x00b", "x" * (policy.MAX_TEXT + 1)):
            proposal = deepcopy(self.proposal)
            proposal["changes"][0]["content"] = value
            with self.subTest(value=type(value)), self.assertRaises(policy.AgentError):
                policy.validate(self.task, proposal)

    def test_documentation_and_unmapped_code_have_different_required_gates(self):
        docs = policy.checks(["docs/guide.md"], [], root=manager.ROOT)
        code = policy.checks(["tools/new.py"], [], root=manager.ROOT)
        self.assertEqual([c["id"] for c in docs], ["diff", "reuse"])
        self.assertEqual({c["id"] for c in code}, {"diff", "reuse", "runtime", "integrity", "learned-conformance", "formal", "conformance", "axioms"})
        self.assertIn("runtime", {c["id"] for c in policy.checks(["examples/source.json"], [], root=manager.ROOT)})

    def test_mapped_code_keeps_native_targets_and_general_runtime_checks(self):
        family = {"native_targets": ["installedChecker"], "runtime_paths": ["src/nabt/owner.py"], "checker_paths": [], "test_paths": []}
        checks = policy.checks(["src/nabt/owner.py"], [family], root=manager.ROOT)
        native = next(c for c in checks if c["id"] == "native-build")
        self.assertEqual(native["argv"], ["lake", "build", "installedChecker"])
        self.assertLess([c["id"] for c in checks].index("native-build"), [c["id"] for c in checks].index("runtime"))
        self.assertTrue({"runtime", "integrity", "learned-conformance"} <= {c["id"] for c in checks})

    def test_mapped_kernel_still_requires_formal_conformance_and_axiom_gates(self):
        family = {"id": "transition-law", "native_targets": ["exportTable"], "runtime_paths": ["src/nabt/machine.py"], "checker_paths": [], "test_paths": []}
        checks = policy.checks(["src/nabt/machine.py"], [family], root=manager.ROOT)
        self.assertTrue({"formal", "conformance", "axioms"} <= {c["id"] for c in checks})

    def test_productive_adapter_uses_installed_native_required_chain(self):
        for identity in ("meaning-preservation", "evidence-lifecycle", "licensed-inference"):
            family = {"id": identity, "native_targets": ["meaningPreservationV1"], "runtime_paths": ["tools/meaning_preservation_v1.py"], "checker_paths": [], "test_paths": []}
            checks = policy.checks(["tools/meaning_preservation_v1.py"], [family], root=manager.ROOT)
            integration = next(c for c in checks if c["id"] == "productive-native-integration")
            self.assertEqual(integration["argv"][:5], ["make", "-f", "tools/meaning_preservation_v1.mk", "meaning-preservation-conformance", "PYTHON=" + sys.executable])
        # Independent prerequisite oracle against the existing recipes, not a
        # second dependency graph manufactured by the controller.
        recipe = (manager.ROOT / "tools/meaning_preservation_v1.mk").read_text()
        self.assertIn("NABT_REQUIRE_MEANING_PRESERVATION_NATIVE=1", recipe)
        self.assertIn("meaning-preservation-native: evidence-lifecycle-evaluation", recipe)
        self.assertIn("include tools/evidence_lifecycle_v1.mk", recipe)

    def test_installed_entry_has_no_implicit_publication_authority(self):
        self.assertEqual(entry_command("repo-agent", ["inspect"])[-2:], ["tools.repo_agent", "inspect"])
        self.assertIn("no linguistic or publication authority", describe_entries()["repo-agent"]["scope"])

    def test_duplicate_json_keys_and_nonfinite_values_are_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            file = Path(name) / "request.json"
            for value in ('{"a":1,"a":2}', '{"x":NaN}'):
                file.write_text(value)
                with self.assertRaises(policy.AgentError):
                    policy.load(file)


@unittest.skipUnless(os.name == "posix", "POSIX process groups and Git worktrees")
class GitTaskTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        repository.git(self.root, "init", "-q")
        files = {"AGENTS.md": "Use existing owners.\n", ".gitignore": "artifacts/local/\n__pycache__/\n",
                 "docs/guide.md": "before\n", "tools/__init__.py": "", "tools/entropy_framework/__init__.py": "",
                 "tools/export_probe.py": "# registered checker\n",
                 "tools/entropy_framework/__main__.py": "from pathlib import Path\nimport sys\np=Path('docs/guide.md')\ns=p.read_text() if p.exists() else ''\nif s=='MUTATE': p.write_text('unexpected')\nprint('fixture reuse process, not a formal checker')\nsys.exit(9 if s=='FAIL' else 0)\n"}
        for relative, content in files.items():
            file = self.root / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(content)
        repository.git(self.root, "add", ".")
        repository.git(self.root, "-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-qm", "base")
        self.base = repository.git(self.root, "rev-parse", "HEAD").decode().strip()
        self.task, self.proposal = inputs(self.base)
        self.output = self.root / "artifacts/local/repo-agent/first"
        fixture = {"catalogue": {"verification": "TEST_FIXTURE_ONLY"}, "population": {}, "families": [], "open_bridge_debts": []}
        self.inventory_patch = patch.object(manager, "build_reuse_report", return_value=fixture)
        self.inventory_patch.start()
        self.addCleanup(self.inventory_patch.stop)

    def run_task(self):
        return manager.run(self.task, self.proposal, root=self.root, output_dir=self.output)

    def test_real_git_candidate_preserves_original_and_has_reviewable_parent(self):
        before = repository.snapshot(self.root)
        report = self.run_task()
        self.assertEqual(report["status"], "READY_FOR_REVIEW")
        self.assertEqual(repository.snapshot(self.root), before)
        self.assertEqual((self.root / "docs/guide.md").read_text(), "before\n")
        self.assertEqual((Path(report["worktree"]) / "docs/guide.md").read_text(), "after\n")
        self.assertEqual(repository.git(self.root, "show", report["candidate_commit"] + ":docs/guide.md"), b"after\n")
        self.assertEqual(repository.git(self.root, "rev-parse", report["candidate_commit"] + "^").decode().strip(), self.base)
        self.assertEqual(report["plan"]["acceptance_review"]["status"], "NOT_AUTOMATICALLY_ASSESSED")
        self.assertEqual(report["publication_authority"], "NONE")
        self.assertEqual([r["id"] for r in report["checks"]], ["diff", "reuse"])
        state.validate_journal(self.output, report["event_tail"])

    def test_new_utf8_file_and_deletion_are_source_bound(self):
        for relative, original, content in (("docs/new.md", None, "معنى جديد\n"), ("docs/guide.md", b"before\n", None)):
            self.task, self.proposal = inputs(self.base, relative, original, content)
            self.output = self.root / "artifacts/local/repo-agent" / ("new" if content else "delete")
            report = self.run_task()
            self.assertEqual(report["status"], "READY_FOR_REVIEW")
            self.assertTrue((self.root / "docs/guide.md").is_file())

    def test_file_scope_is_literal_even_for_brackets_in_filename(self):
        self.task, self.proposal = inputs(self.base, "docs/example[1].md", None, "literal path\n")
        report = self.run_task()
        self.assertEqual(report["status"], "READY_FOR_REVIEW")
        self.assertEqual((Path(report["worktree"]) / "docs/example[1].md").read_text(), "literal path\n")

    def test_empty_and_whitespace_replacements_preserve_files(self):
        for index, content in enumerate(("", " \n")):
            self.proposal["changes"][0]["content"] = content
            self.output = self.root / "artifacts/local/repo-agent" / ("empty-" + str(index))
            report = self.run_task()
            # Whitespace-only content is valid input; the existing diff gate
            # can still reject trailing whitespace as its own engineering rule.
            self.assertIn(report["status"], ("READY_FOR_REVIEW", "CHECKS_FAILED"))
            candidate = Path(report["worktree"]) / "docs/guide.md"
            self.assertTrue(candidate.is_file())
            self.assertEqual(candidate.read_text(), content)
        task, proposal = inputs(self.base, "docs/empty.md", None, "")
        result = manager.run(task, proposal, root=self.root, output_dir=self.output.parent / "empty-new")
        self.assertEqual(result["status"], "READY_FOR_REVIEW")
        self.assertEqual((Path(result["worktree"]) / "docs/empty.md").read_bytes(), b"")

    def test_rename_detection_does_not_hide_the_deleted_path(self):
        self.task, self.proposal = inputs(self.base, content=None)
        self.task["allowed_paths"].append("docs/moved.md")
        self.proposal["changes"].append({"path": "docs/moved.md", "before_sha256": None, "content": "before\n"})
        result = self.run_task()
        self.assertEqual(result["status"], "READY_FOR_REVIEW")
        self.assertFalse((Path(result["worktree"]) / "docs/guide.md").exists())
        self.assertEqual((Path(result["worktree"]) / "docs/moved.md").read_text(), "before\n")

    def test_registered_checker_is_protected_without_a_check_filename_prefix(self):
        self.task, self.proposal = inputs(self.base, "tools/export_probe.py", b"# registered checker\n", "print('passed')\n")
        manager.build_reuse_report.return_value["families"] = [{"checker_paths": ["tools/export_probe.py"]}]
        with self.assertRaises(policy.AgentError) as error:
            self.run_task()
        self.assertEqual(error.exception.code, "PROTECTED_PATH")
        self.assertFalse(self.output.exists())

    def test_stale_base_and_bytes_never_create_a_worktree(self):
        self.task["base_commit"] = self.proposal["base_commit"] = "a" * 40
        with self.assertRaises(policy.AgentError) as error:
            self.run_task()
        self.assertEqual(error.exception.code, "STALE_BASE")
        self.task["base_commit"] = self.proposal["base_commit"] = self.base
        self.proposal["changes"][0]["before_sha256"] = "b" * 64
        with self.assertRaises(policy.AgentError) as error:
            self.run_task()
        self.assertEqual(error.exception.code, "STALE_INPUT")
        self.assertFalse(self.output.exists())

    def test_dirty_checkout_is_not_repaired_or_overwritten(self):
        (self.root / "docs/guide.md").write_text("user change")
        with self.assertRaises(policy.AgentError) as error:
            self.run_task()
        self.assertEqual(error.exception.code, "DIRTY_CHECKOUT")
        self.assertEqual((self.root / "docs/guide.md").read_text(), "user change")

    def test_fake_absence_and_noop_are_not_accepted(self):
        self.proposal["changes"][0]["before_sha256"] = None
        with self.assertRaises(policy.AgentError):
            self.run_task()
        self.task, self.proposal = inputs(self.base, content="before\n")
        with self.assertRaises(policy.AgentError):
            self.run_task()

    def test_original_and_replacement_bytes_are_bounded(self):
        with patch.object(repository, "MAX_TEXT", 2):
            with self.assertRaises(policy.AgentError) as error:
                repository.validate_before(self.root, self.proposal)
        self.assertEqual(error.exception.code, "RESOURCE_LIMIT")
        with patch.object(repository, "MAX_INPUT", 6):
            with self.assertRaises(policy.AgentError) as error:
                repository.validate_before(self.root, self.proposal)
        self.assertEqual(error.exception.code, "RESOURCE_LIMIT")

    def test_symlink_in_file_or_state_path_is_rejected(self):
        (self.root / "docs/link").symlink_to(self.root / "docs", target_is_directory=True)
        with self.assertRaises(policy.AgentError):
            repository.safe_file(self.root, "docs/link/guide.md")
        (self.root / "docs/link").unlink()
        (self.root / "artifacts/local").mkdir(parents=True)
        (self.root / "artifacts/local/repo-agent").symlink_to(self.root / "docs", target_is_directory=True)
        with self.assertRaises(policy.AgentError):
            self.run_task()

    def test_failed_check_stops_without_success_or_candidate_commit(self):
        self.proposal["changes"][0]["content"] = "FAIL"
        report = self.run_task()
        self.assertEqual(report["status"], "CHECKS_FAILED")
        self.assertEqual(report["checks"][-1]["returncode"], 9)
        self.assertIsNone(report["candidate_commit"])
        self.assertTrue((self.output / "reuse.stdout").is_file())

    def test_check_that_mutates_candidate_cannot_certify_old_tree(self):
        self.proposal["changes"][0]["content"] = "MUTATE"
        report = self.run_task()
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["error"]["code"], "TREE_DRIFT")
        self.assertEqual(report["checks"][-1]["returncode"], 0)
        self.assertIsNone(report["candidate_commit"])

    def test_run_history_is_not_overwritten(self):
        self.run_task()
        before = (self.output / "state.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_task()
        self.assertEqual((self.output / "state.json").read_bytes(), before)

    def test_state_directory_traversal_cannot_create_outside_namespace(self):
        with self.assertRaises(policy.AgentError):
            state.create_directory(self.root, self.root / "artifacts/local/repo-agent/a/../../../escaped")
        self.assertFalse((self.root / "artifacts/escaped").exists())

    def test_controller_drift_blocks_even_passing_child(self):
        original = manager.identity()
        with patch.object(manager, "identity", side_effect=[original, {"changed": "policy"}]):
            report = self.run_task()
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["error"]["code"], "TREE_DRIFT")

    def test_first_failure_prevents_later_check_execution(self):
        self.proposal["changes"][0]["content"] = "trailing whitespace  \n"
        with patch.object(manager, "execute", wraps=manager.execute) as execute:
            report = self.run_task()
        self.assertEqual(report["status"], "CHECKS_FAILED")
        self.assertEqual(execute.call_count, 1)
        self.assertEqual(report["checks"][0]["id"], "diff")

    def test_fresh_verification_reexecutes_checks(self):
        old = self.run_task()
        with patch.object(manager, "execute", wraps=manager.execute) as execute:
            result = manager.verify(self.output, self.task, self.proposal, root=self.root, output_dir=self.output.parent / "fresh")
        self.assertTrue(result["valid"])
        self.assertEqual(result["candidate_tree"], old["candidate_tree"])
        self.assertEqual(execute.call_count, 2)
        self.assertEqual(result["historical_authenticity"], "NOT_ESTABLISHED")

    def test_changed_log_is_not_accepted_as_previous_execution(self):
        self.run_task()
        (self.output / "reuse.stdout").write_text("claimed success")
        with self.assertRaises(policy.AgentError) as error:
            manager.verify(self.output, self.task, self.proposal, root=self.root, output_dir=self.output.parent / "fresh")
        self.assertEqual(error.exception.code, "REPLAY_MISMATCH")

    def test_boolean_integer_substitution_in_execution_record_is_rejected(self):
        self.run_task()
        original = policy.load(self.output / "state.json")
        for field in ("returncode", "bytes", "truncated"):
            record = deepcopy(original)
            if field == "returncode":
                record["checks"][0][field] = False
            else:
                record["checks"][0]["logs"]["stdout"][field] = False if field == "bytes" else 0
            state.write_json(self.output / "state.json", record)
            with self.subTest(field=field), self.assertRaises(policy.AgentError) as error:
                manager.verify(self.output, self.task, self.proposal, root=self.root, output_dir=self.output.parent / field)
            self.assertEqual(error.exception.code, "REPLAY_MISMATCH")

    def test_malformed_check_rows_are_structured_rejections(self):
        self.run_task()
        record = policy.load(self.output / "state.json")
        record["checks"] = ["success", "success"]
        state.write_json(self.output / "state.json", record)
        with self.assertRaises(policy.AgentError) as error:
            manager.verify(self.output, self.task, self.proposal, root=self.root, output_dir=self.output.parent / "fresh")
        self.assertEqual(error.exception.code, "REPLAY_MISMATCH")

    def test_saved_record_cannot_add_authority_or_undeclared_claims(self):
        self.run_task()
        original = policy.load(self.output / "state.json")
        for field, value in (("publication_authority", "GRANTED"), ("semantic_authority", "PROVED"), ("arbitrary_claim", True)):
            record = deepcopy(original)
            record[field] = value
            state.write_json(self.output / "state.json", record)
            with self.subTest(field=field), self.assertRaises(policy.AgentError) as error:
                manager.verify(self.output, self.task, self.proposal, root=self.root, output_dir=self.output.parent / field)
            self.assertEqual(error.exception.code, "REPLAY_MISMATCH")

    def test_exported_patch_and_retained_inputs_are_checked(self):
        self.run_task()
        patch_file = self.output / "candidate.patch"
        original = patch_file.read_bytes()
        patch_file.write_text("unrelated change")
        with self.assertRaises(policy.AgentError):
            manager.verify(self.output, self.task, self.proposal, root=self.root, output_dir=self.output.parent / "fresh")
        patch_file.write_bytes(original)
        stored = deepcopy(self.task)
        stored["goal"] = "different history"
        state.write_json(self.output / "task.json", stored)
        with self.assertRaises(policy.AgentError):
            manager.verify(self.output, self.task, self.proposal, root=self.root, output_dir=self.output.parent / "fresh")

    def test_changed_independent_request_and_commit_are_rejected(self):
        self.run_task()
        changed = deepcopy(self.task)
        changed["goal"] = "A different task"
        with self.assertRaises(policy.AgentError):
            manager.verify(self.output, changed, self.proposal, root=self.root, output_dir=self.output.parent / "fresh")
        record = policy.load(self.output / "state.json")
        record["candidate_commit"] = self.base
        state.write_json(self.output / "state.json", record)
        with self.assertRaises(policy.AgentError):
            manager.verify(self.output, self.task, self.proposal, root=self.root, output_dir=self.output.parent / "fresh")

    def test_postcheck_edit_invalidates_previous_worktree(self):
        report = self.run_task()
        (Path(report["worktree"]) / "docs/guide.md").write_text("unverified edit")
        with self.assertRaises(policy.AgentError):
            manager.verify(self.output, self.task, self.proposal, root=self.root, output_dir=self.output.parent / "fresh")

    def test_event_chain_detects_deletion(self):
        report = self.run_task()
        file = self.output / "events.jsonl"
        file.write_bytes(b"\n".join(file.read_bytes().splitlines()[1:]) + b"\n")
        with self.assertRaises(policy.AgentError):
            state.validate_journal(self.output, report["event_tail"])


@unittest.skipUnless(os.name == "posix", "POSIX process supervision")
class ProcessTests(unittest.TestCase):
    def execute(self, argv, *, timeout=5):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            return manager.execute({"id": "probe", "argv": argv, "cwd": ".", "timeout": timeout}, root, root)

    def test_missing_executable_is_distinct_from_failed_check(self):
        self.assertEqual(self.execute(["/missing/nabt-command"])["status"], "UNAVAILABLE")
        result = self.execute([sys.executable, "-c", "raise SystemExit(7)"])
        self.assertEqual((result["status"], result["returncode"]), ("FAILED", 7))

    def test_timeout_and_terminating_signal_do_not_become_pass(self):
        result = self.execute([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.05)
        self.assertEqual(result["status"], "TIMEOUT")
        result = self.execute([sys.executable, "-c", "import os,signal; os.kill(os.getpid(),signal.SIGTERM)"])
        self.assertEqual((result["status"], result["returncode"]), ("FAILED", -signal.SIGTERM))

    def test_output_budget_is_checked_even_for_fast_successful_process(self):
        with patch.object(manager, "MAX_LOG_BYTES", 1024):
            result = self.execute([sys.executable, "-c", "print('x'*20000)"])
        self.assertEqual(result["status"], "RESOURCE_LIMIT")
        self.assertTrue(result["logs"]["stdout"]["truncated"])

    def test_credentials_and_git_overrides_are_not_child_environment(self):
        with patch.dict(os.environ, {"EXAMPLE_API_TOKEN": "not-a-real-secret", "GIT_INDEX_FILE": "/bad/index", "PYTHONPATH": "/bad/modules"}):
            env = manager.environment(manager.ROOT)
        self.assertNotIn("EXAMPLE_API_TOKEN", env)
        self.assertNotIn("GIT_INDEX_FILE", env)
        self.assertNotIn("/bad/modules", env["PYTHONPATH"])


if __name__ == "__main__":
    unittest.main()
