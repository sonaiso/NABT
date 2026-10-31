"""Independent checks against the acceptance oracle frozen at 5dca9ad.

These tests exercise metadata and its existing owners. They do not turn the
organizational map into a semantic, action, or rule-adoption checker. Literal
expectations come from the pinned preimplementation oracle; source-row
preservation is additionally compared with the independent existing catalogue.
"""
from __future__ import annotations

from contextlib import ExitStack, contextmanager, redirect_stderr, redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.entropy_framework import organization, reuse, reuse_run
from tools.entropy_framework.__main__ import main
from tools.entropy_framework.registry import (
    DEFAULT_REGISTRY, FrameworkError, FrameworkResourceError, load_json,
    report_registry, validate_registry,
)
from tools.grammar_catalog import catalog as source_catalogue
from tests.test_proof_reuse import make_root


ROOT = Path(__file__).resolve().parents[1]
GOLD_PATH = ROOT / "evidence/rule_policy_organization_v1/acceptance_cases.json"
GOLD_SHA256 = "9a04a167259cd2f6993a81c4863fba16c298485b4110afc634c9d03ef9e4f82f"
REPORT_KEYS = {
    "schema", "status", "authority", "semantic_authority", "action_authority",
    "runtime_execution_performed", "scope_relation_established", "base_contracts",
    "organization_schema", "organization_sha256", "profiles", "relations",
    "prerequisite_order", "role_counts", "catalogue", "families", "inputs", "limits",
}
PROFILE_ADDITIONS = {
    "subject_owner", "resolved_phase_contract_refs", "capability_links",
    "scope_relation_established", "lifecycle_evidence",
}
CATALOGUE_ADDITIONS = {
    "profile_ids", "mapping_status", "owner_scope", "scope_relation_established",
}


def wire(value):
    """A test comparison that cannot equate false/0 or true/1."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def pointer(value, path):
    for encoded in path.lstrip("/").split("/") if path else ():
        key = encoded.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def apply_fixture_patch(value, operations):
    """Apply only the four frozen RFC 6902 fixture operations, without repair."""
    result = deepcopy(value)
    for operation in operations:
        path = operation["path"]
        parent_path, encoded = path.rsplit("/", 1)
        parent = pointer(result, parent_path)
        key = encoded.replace("~1", "/").replace("~0", "~")
        kind = operation["op"]
        if kind not in {"add", "remove", "replace", "copy"}:
            raise AssertionError("Unfrozen fixture mutation: " + kind)
        replacement = deepcopy(pointer(result, operation["from"]) if kind == "copy"
                               else operation.get("value"))
        if isinstance(parent, list):
            if kind in {"add", "copy"}:
                if key == "-":
                    parent.append(replacement)
                else:
                    parent.insert(int(key), replacement)
            elif kind == "remove":
                parent.pop(int(key))
            else:
                parent[int(key)] = replacement
        elif kind == "remove":
            del parent[key]
        else:
            parent[key] = replacement
    return result


@contextmanager
def no_execution():
    """A real report may read owners; it must not dispatch or start processes."""
    with ExitStack() as stack:
        sentinels = [
            stack.enter_context(patch.object(reuse_run, "run_entry",
                                             side_effect=AssertionError("metadata dispatched"))),
            stack.enter_context(patch.object(subprocess, "run",
                                             side_effect=AssertionError("metadata ran a process"))),
            stack.enter_context(patch.object(subprocess, "Popen",
                                             side_effect=AssertionError("metadata spawned a process"))),
            stack.enter_context(patch.object(os, "system",
                                             side_effect=AssertionError("metadata ran a shell"))),
        ]
        yield
        for sentinel in sentinels:
            sentinel.assert_not_called()


class RuleOrganizationAcceptance(unittest.TestCase):
    """One method per frozen RPO group; named variants remain visible subtests."""

    @classmethod
    def setUpClass(cls):
        raw = GOLD_PATH.read_bytes()
        if hashlib.sha256(raw).hexdigest() != GOLD_SHA256:
            raise AssertionError("The frozen organization acceptance oracle changed")
        cls.gold = load_json(GOLD_PATH)
        cls.cases = {row["id"]: row for row in cls.gold["cases"]}
        if set(cls.cases) != {f"RPO{number:02d}" for number in range(1, 15)}:
            raise AssertionError("The frozen acceptance population is incomplete")
        cls.fixtures = cls.gold["fixtures"]
        cls.original_catalogue = source_catalogue.build_catalog(ROOT)
        cls.original_rows = {row["rule_key"]: row for row in cls.original_catalogue["rules"]}
        if sorted(cls.original_rows) != cls.fixtures["baseline_catalogue_rule_keys"]:
            raise AssertionError("The source-owner population differs from the frozen 125 IDs")

    def setUp(self):
        self.maxDiff = 3000

    def assert_exact(self, actual, expected):
        self.assertEqual(wire(actual), wire(expected))

    def assert_fields(self, actual, expected):
        for key, value in expected.items():
            with self.subTest(field=key):
                self.assertIn(key, actual)
                self.assert_exact(actual[key], value)

    def fixture(self, name="prepared_registry"):
        # The maintained registry supplies its unchanged valid base. Only the
        # optional organization is removed/replaced; missing base fields are
        # never repaired with an expectation from the oracle.
        value = load_json(DEFAULT_REGISTRY)
        value["rule_contract"].pop("organization", None)
        if name == "prepared_registry":
            value["rule_contract"]["organization"] = deepcopy(self.fixtures["organization"])
        elif name != "legacy_registry":
            raise AssertionError("Unknown frozen fixture: " + name)
        return value

    def variant_input(self, case, variant):
        name = variant.get("fixture", case.get("fixture", "prepared_registry"))
        return apply_fixture_patch(self.fixture(name), variant.get("registry_patch", []))

    def build(self, value):
        return organization.build_organization_report(ROOT, registry=value)

    def invoke_target(self, target, value):
        if target == "validate_registry":
            return validate_registry(value)
        if target == "organization_report":
            return self.build(value)
        raise AssertionError("Unknown frozen target: " + target)

    def assert_rejections(self, case_id):
        case = self.cases[case_id]
        for variant in case["variants"]:
            expected = variant["expected"]
            if expected["result"] != "REJECT" or "workspace_patch" in variant:
                continue
            for target in variant["targets"]:
                with self.subTest(case=case_id, variant=variant["id"], target=target):
                    value = self.variant_input(case, variant)
                    before = wire(value)
                    with no_execution(), self.assertRaisesRegex(
                            FrameworkError, re.escape(expected["error_contains"])):
                        self.invoke_target(target, value)
                    self.assertEqual(wire(value), before)

    def assert_report_boundary(self, report, expected=None):
        self.assertEqual(set(report), REPORT_KEYS)
        self.assert_fields(report, expected or self.cases["RPO01"]["expected"]["report_equals"])
        self.assertIs(report["runtime_execution_performed"], False)
        self.assertIs(report["scope_relation_established"], False)
        self.assertEqual(report["semantic_authority"], "NONE")
        self.assertEqual(report["action_authority"], "NONE")
        self.assertIs(type(report["inputs"]), dict)
        for value in report["inputs"].values():
            self.assertRegex(value, r"^[0-9a-f]{64}$")

    def assert_owner_reference(self, actual, authored):
        self.assertEqual(set(actual), {"kind", "id", "owner_scope", "owner_identity"})
        self.assert_fields(actual, authored)
        self.assertIs(type(actual["owner_identity"]), dict)
        self.assertTrue(actual["owner_identity"])
        if authored["kind"] == "compiled_declaration":
            self.assertIs(actual["owner_identity"]["compiled_this_run"], False)

    def assert_profiles(self, report, authored):
        expected_ids = [row["id"] for row in authored]
        actual_ids = [row["id"] for row in report["profiles"]]
        self.assertEqual(len(actual_ids), len(set(actual_ids)))
        self.assertCountEqual(actual_ids, expected_ids)
        by_id = {row["id"]: row for row in report["profiles"]}
        phases = self.gold["contract"]["phases"]
        for original in authored:
            with self.subTest(profile=original["id"]):
                resolved = by_id[original["id"]]
                self.assertEqual(set(resolved), set(original) | PROFILE_ADDITIONS)
                self.assert_fields(resolved, original)
                self.assertIs(resolved["scope_relation_established"], False)
                self.assert_exact(resolved["lifecycle_evidence"],
                                  {phase: "NOT_OBSERVED" for phase in phases})
                self.assert_owner_reference(resolved["subject_owner"], original["subject"])
                self.assertEqual(len(resolved["capability_links"]), len(original["family_ids"]))
                if not original["family_ids"]:
                    self.assert_exact(resolved["capability_links"], [])
                actual_phases = resolved["resolved_phase_contract_refs"]
                self.assertEqual(set(actual_phases), set(phases))
                for phase in phases:
                    self.assertEqual(len(actual_phases[phase]), len(original["phase_contract_refs"][phase]))
                    for actual, reference in zip(actual_phases[phase], original["phase_contract_refs"][phase]):
                        self.assert_owner_reference(actual, reference)
        return by_id

    def assert_catalogue_partition(self, report, mapped_keys, mapped_count, unmapped_count):
        catalogue = report["catalogue"]
        expected_keys = self.fixtures["baseline_catalogue_rule_keys"]
        unmapped = sorted(set(expected_keys) - set(mapped_keys))
        self.assertEqual(catalogue["schema"], "nabt.grammar-retrieval-catalog.v2")
        self.assertEqual(catalogue["authority"], "RETRIEVAL_ONLY")
        self.assert_fields(catalogue, {"rule_count": 125, "mapped_rule_count": mapped_count,
                                      "unmapped_rule_count": unmapped_count})
        for field in ("rule_count", "mapped_rule_count", "unmapped_rule_count"):
            self.assertIs(type(catalogue[field]), int)
        self.assert_exact(sorted(catalogue["mapped_rule_keys"]), sorted(mapped_keys))
        self.assert_exact(sorted(catalogue["unmapped_rule_keys"]), unmapped)
        self.assertFalse(set(catalogue["mapped_rule_keys"]) & set(catalogue["unmapped_rule_keys"]))
        rows = catalogue["rules"]
        actual_ids = [row["rule_key"] for row in rows]
        self.assertEqual(len(actual_ids), len(set(actual_ids)))
        self.assert_exact(sorted(actual_ids), expected_keys)
        for row in rows:
            original = self.original_rows[row["rule_key"]]
            self.assertEqual(set(row), set(original) | CATALOGUE_ADDITIONS)
            self.assert_exact({key: row[key] for key in original}, original)
            self.assert_exact(row["owner_scope"], original["scope"])
            self.assertIs(row["scope_relation_established"], False)
            if row["rule_key"] not in mapped_keys:
                self.assert_fields(row, self.cases["RPO13"]["expected"]["every_unmapped_rule"])
        return {row["rule_key"]: row for row in rows}

    def cli(self, arguments):
        environment = os.environ | {"PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(ROOT)))}
        return subprocess.run([sys.executable, "-B", "-m", "tools.entropy_framework", *arguments],
                              cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30)

    def test_rpo01_exact_owner_references_base_contracts_and_nonexecution(self):
        case = self.cases["RPO01"]
        value = self.fixture()
        before = wire(value)
        validation = validate_registry(value)
        self.assert_fields(validation, case["validation_expected"])
        with no_execution():
            report = self.build(value)
        expected = case["expected"]
        self.assert_report_boundary(report, expected["report_equals"])
        self.assert_fields(report["base_contracts"], expected["base_contracts"])
        self.assertNotIn("organization", report["base_contracts"]["rule_contract"])
        self.assert_exact(report["relations"], expected["relations"])
        self.assertCountEqual(report["prerequisite_order"], expected["prerequisite_order_set"])
        profiles = self.assert_profiles(report, self.fixtures["organization"]["profiles"])
        for identity, scope in expected["owner_scopes_by_profile"].items():
            self.assert_exact(profiles[identity]["subject_owner"]["owner_scope"], scope)
        original = self.fixtures["baseline_owner_source"]
        self.assertEqual(report["inputs"][original["local_path"]], original["sha256"])
        self.assertEqual(wire(value), before)

    def test_rpo02_legacy_omission_is_explicit_and_every_rule_remains_visible(self):
        case = self.cases["RPO02"]
        value = self.fixture("legacy_registry")
        before = wire(value)
        self.assert_fields(validate_registry(value), case["validation_expected"])
        self.assertEqual(report_registry(value)["organization_state"], "NOT_DECLARED")
        with no_execution():
            report = self.build(value)
        self.assert_report_boundary(report, case["expected"]["report_equals"])
        for role in case["expected"]["role_counts_zero_for"]:
            self.assert_exact(report["role_counts"][role], 0)
        self.assert_catalogue_partition(report, [], 0, 125)
        self.assertEqual(wire(value), before)

    def test_rpo03_missing_or_weakened_base_rule_contract_always_rejects(self):
        self.assert_rejections("RPO03")
        case = self.cases["RPO03"]
        value = self.variant_input(case, case["variants"][0])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing_rule_contract.json"
            path.write_text(wire(value), encoding="utf-8")
            result = self.cli(["validate", "--registry", str(path)])
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assert_fields(json.loads(result.stdout),
                           {"status": "INVALID_INPUT", "semantic_authority": "NONE"})
        self.assertIn("rule_contract", json.loads(result.stdout)["reason"])

    def test_rpo04_operation_kind_is_not_a_caller_defined_execution_vocabulary(self):
        self.assert_rejections("RPO04")

    def test_rpo05_freshness_contract_cannot_omit_source_identity(self):
        self.assert_rejections("RPO05")

    def test_rpo06_duplicates_are_rejected_without_deduplication(self):
        self.assert_rejections("RPO06")

    def test_rpo07_exact_owner_resolution_is_distinct_from_structure_validation(self):
        self.assert_rejections("RPO07")
        case = self.cases["RPO07"]
        control = case["structure_only_control"]
        variant = next(row for row in case["variants"] if row["id"] == control["variant"])
        value = self.variant_input(case, variant)
        expected = {key: val for key, val in control["expected"].items() if key != "result"}
        with patch.object(source_catalogue, "build_catalog",
                          side_effect=AssertionError("structure validation loaded source owner")), \
             patch.object(reuse, "current_catalog",
                          side_effect=AssertionError("structure validation resolved proof owner")), no_execution():
            self.assert_fields(validate_registry(value), expected)
            self.assertEqual(report_registry(value)["organization_state"],
                             "DECLARED_REFERENCES_NOT_RESOLVED")

    def test_rpo08_authored_annotation_cannot_override_owner_scope(self):
        self.assert_rejections("RPO08")
        case = self.cases["RPO08"]
        variant = next(row for row in case["variants"] if row["expected"]["result"] == "ACCEPT")
        value = self.variant_input(case, variant)
        before = wire(value)
        with no_execution():
            report = self.build(value)
        expected = variant["expected"]
        profile = next(row for row in report["profiles"] if row["id"] == expected["profile_id"])
        self.assertEqual(profile["scope"], expected["scope"])
        self.assertEqual(profile["subject_owner"]["owner_scope"], expected["subject_owner.owner_scope"])
        self.assertNotEqual(profile["scope"], profile["subject_owner"]["owner_scope"])
        self.assertIs(profile["scope_relation_established"], False)
        self.assertIs(report["scope_relation_established"], False)
        self.assertEqual(wire(value), before)

    def test_rpo09_version_overrides_and_actual_source_loader_tampering_fail(self):
        self.assert_rejections("RPO09")
        case = self.cases["RPO09"]
        variant = next(row for row in case["variants"] if "workspace_patch" in row)
        relative = variant["workspace_patch"]["path"]
        suffix = variant["workspace_patch"]["utf8"].encode("utf-8")
        actual_read = source_catalogue._read
        observed = []
        def altered_read(root, path):
            raw = actual_read(root, path)
            if path == relative:
                observed.append(path)
                return raw + suffix
            return raw
        original_digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        with patch.object(source_catalogue, "_read", side_effect=altered_read), no_execution():
            with self.assertRaises(FrameworkError):
                self.build(self.fixture())
        self.assertTrue(observed, "Organization did not invoke the existing source loader")
        self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), original_digest)
        # A clean replay must still read the owner after the rejected attempt.
        observed.clear()
        def traced_read(root, path):
            if path == relative:
                observed.append(path)
            return actual_read(root, path)
        with patch.object(source_catalogue, "_read", side_effect=traced_read), no_execution():
            result = self.build(self.fixture())
        self.assertEqual(result["status"], "RESOLVED")
        self.assertTrue(observed)
        self.assertEqual(result["inputs"][relative], original_digest)

    def test_rpo10_combined_prerequisite_justification_cycles_are_rejected(self):
        self.assert_rejections("RPO10")

    def test_rpo11_reference_inference_and_conflict_cycles_remain_metadata(self):
        case = self.cases["RPO11"]
        value = apply_fixture_patch(self.fixture(), case["registry_patch"])
        self.assert_fields(validate_registry(value), case["validation_expected"])
        with no_execution():
            report = self.build(value)
        self.assert_report_boundary(report, case["expected"]["report_equals"])
        self.assert_exact(report["relations"], value["rule_contract"]["organization"]["relations"])
        self.assertEqual(len(report["relations"]), case["expected"]["relation_count"])
        self.assertCountEqual(report["prerequisite_order"], case["expected"]["prerequisite_order_set"])
        self.assert_profiles(report, value["rule_contract"]["organization"]["profiles"])

    def test_rpo12_closed_shapes_and_execution_sentinels_keep_authority_none(self):
        self.assert_rejections("RPO12")
        with no_execution():
            report = self.build(self.fixture())
        self.assert_report_boundary(report)
        self.assert_profiles(report, self.fixtures["organization"]["profiles"])

    def test_rpo13_exact_population_permutation_and_distinct_source_statuses(self):
        case = self.cases["RPO13"]
        expected = case["expected"]
        value = self.fixture()
        with no_execution():
            report = self.build(value)
        rows = self.assert_catalogue_partition(report, expected["mapped_rule_keys"],
                                              expected["mapped_rule_count"], expected["unmapped_rule_count"])
        self.assert_fields(rows[expected["mapped_rule"]["rule_key"]], expected["mapped_rule"])
        permuted = self.fixture()
        permuted["rule_contract"]["organization"]["profiles"] = deepcopy(self.fixtures["reversed_profiles"])
        before = wire(permuted)
        with no_execution():
            reversed_report = self.build(permuted)
        self.assertEqual(reversed_report["organization_sha256"],
                         case["permutation_control"]["organization_sha256"])
        self.assertNotEqual(report["organization_sha256"], reversed_report["organization_sha256"])
        self.assert_exact(report["catalogue"], reversed_report["catalogue"])
        self.assert_exact(report["role_counts"], reversed_report["role_counts"])
        self.assert_exact({p["id"]: p for p in report["profiles"]},
                          {p["id"]: p for p in reversed_report["profiles"]})
        self.assertEqual(wire(permuted), before)

        with no_execution():
            installed = organization.build_organization_report(ROOT)
        default = case["installed_slice"]["expected"]
        self.assertEqual(len(installed["profiles"]), default["profile_count"])
        current = self.assert_catalogue_partition(installed, default["mapped_rule_keys"],
                                                  default["mapped_rule_count"], default["unmapped_rule_count"])
        profiles = {p["id"]: p for p in installed["profiles"]}
        for identity, role in default["profile_role_by_id"].items():
            self.assertEqual(profiles[identity]["role"], role)
        for identity, original in self.fixtures["default_slice_original_catalogue_records"].items():
            self.assert_exact({key: current[identity][key] for key in original}, original)
        discrepancy = default["discrepancy_record"]
        self.assert_fields(current[discrepancy["rule_key"]],
                           {key: val for key, val in discrepancy.items() if key != "operator_claims"})
        self.assert_exact(current[discrepancy["rule_key"]]["operator_traceability"]["claims"],
                          discrepancy["operator_claims"])
        self.assert_fields(current[default["word_kind_record"]["rule_key"]], default["word_kind_record"])
        self.assert_fields(installed, {key: default[key] for key in (
            "semantic_authority", "action_authority", "runtime_execution_performed", "scope_relation_established")})

    def test_rpo14_actual_cli_views_conflicts_exclusive_output_and_legacy_reuse(self):
        case = self.cases["RPO14"]
        with tempfile.TemporaryDirectory() as temporary:
            for index, row in enumerate(case["cli_cases"]):
                with self.subTest(argv=row["argv"]):
                    output_path = Path(temporary) / f"organization_{index}.json"
                    arguments = [str(output_path) if token == "<fresh-temporary-report-path>" else token
                                 for token in row["argv"]]
                    result = self.cli(arguments)
                    expected = row["expected"]
                    if expected.get("nonzero_exit"):
                        self.assertNotEqual(result.returncode, 0)
                        # Also instrument the actual parser/front door in this
                        # process to establish that its conflicting --run path
                        # does not reach the installed dispatcher.
                        with no_execution(), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                            try:
                                status = main(arguments)
                            except SystemExit as error:
                                status = error.code
                        self.assertNotEqual(status, 0)
                        self.assertNotIn('"status": "RESOLVED"', result.stdout)
                        continue
                    self.assertEqual(result.returncode, expected["exit_code"], result.stderr)
                    display = json.loads(result.stdout)
                    for field in ("semantic_authority", "action_authority"):
                        self.assertEqual(display[field], "NONE")
                    self.assertIs(display["runtime_execution_performed"], False)
                    if "report_equals" in expected:
                        self.assert_report_boundary(display, expected["report_equals"])
                    if "schema" in expected:
                        self.assertEqual(display["schema"], expected["schema"])
                    if "display_schema" in expected:
                        self.assertEqual(display["schema"], expected["display_schema"])
                    if "--output" in arguments:
                        raw = output_path.read_bytes()
                        stored = json.loads(raw)
                        self.assertEqual(stored["schema"], "nabt.rule-organization.report.v1")
                        self.assertEqual(set(stored), REPORT_KEYS)
                        self.assertEqual(stored["catalogue"]["rule_count"], 125)
                        self.assertEqual(len(stored["catalogue"]["rules"]), 125)
                        repeated = self.cli(arguments)
                        self.assertNotEqual(repeated.returncode, 0)
                        self.assertEqual(output_path.read_bytes(), raw)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            small_registry, _, entries = make_root(root)
            self.assertEqual(set(small_registry), {"reuse"})
            with patch.object(reuse_run, "describe_entries", return_value=entries), \
                 patch.object(organization, "build_organization_report",
                              side_effect=AssertionError("ordinary reuse loaded organization")), \
                 patch.object(source_catalogue, "build_catalog",
                              side_effect=AssertionError("ordinary reuse loaded grammar catalogue")), no_execution():
                report = reuse.build_reuse_report(root, registry=small_registry)
            self.assertEqual(report["schema"], "nabt.proof-reuse-report.v1")
            self.assertEqual(report["authority"], "REUSE_NAVIGATION_ONLY")
            self.assertEqual(report["semantic_authority"], "NONE")
            self.assertIs(report["runtime_execution_performed"], False)

    def test_review_vocabulary_permutations_preserve_input_order_and_owner_identity(self):
        """Supplemental review case; the fourteen frozen groups stay unchanged."""
        baseline = {
            "rule_contract": self.fixtures["base_rule_contract"],
            "evidence_freshness": self.fixtures["base_evidence_freshness"],
        }
        for contract, field in (("rule_contract", "required"),
                                ("rule_contract", "operation_kinds"),
                                ("evidence_freshness", "identity")):
            with self.subTest(contract=contract, field=field):
                value = self.fixture()
                value[contract][field].reverse()
                before = wire(value)
                expected = deepcopy(baseline)
                expected[contract][field].reverse()
                validation = validate_registry(value)
                self.assertEqual(validation["organization_state"],
                                 "DECLARED_REFERENCES_NOT_RESOLVED")
                with no_execution():
                    report = self.build(value)
                self.assert_fields(report["base_contracts"], expected)
                self.assertEqual(report["organization_sha256"],
                                 self.fixtures["organization_sha256"])
                expected_digest = hashlib.sha256(wire(expected[contract]).encode("utf-8")).hexdigest()
                original_digest = hashlib.sha256(wire(baseline[contract]).encode("utf-8")).hexdigest()
                self.assertNotEqual(expected_digest, original_digest)
                references = []
                for profile in report["profiles"]:
                    references.append(profile["subject_owner"])
                    for items in profile["resolved_phase_contract_refs"].values():
                        references.extend(items)
                affected = [item for item in references
                            if item["kind"] == "framework_contract" and item["id"] == contract]
                self.assertTrue(affected, "The reordered contract must have an actual owner reference")
                for item in affected:
                    self.assertEqual(item["owner_identity"]["record_sha256"], expected_digest)
                self.assertEqual(wire(value), before)

    def test_review_empty_run_selector_cannot_bypass_organization_exclusion(self):
        arguments = ["reuse", "--organization", "--run", "", "--summary"]
        result = self.cli(arguments)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assert_fields(json.loads(result.stdout),
                           {"status": "INVALID_INPUT", "semantic_authority": "NONE"})
        output = io.StringIO()
        with no_execution(), redirect_stdout(output), \
             patch.object(organization, "build_organization_report",
                          side_effect=AssertionError("conflicting selector reached an owner")):
            self.assertEqual(main(arguments), 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "INVALID_INPUT")
        # With no organization flag, an explicitly empty selector must reach
        # the existing allowlist and fail there, never turn into a report.
        ordinary = self.cli(["reuse", "--run", ""])
        self.assertEqual(ordinary.returncode, 2, ordinary.stderr)
        self.assert_fields(json.loads(ordinary.stdout),
                           {"status": "INVALID_INPUT", "semantic_authority": "NONE"})
        self.assertIn("Unknown installed reuse entry point", json.loads(ordinary.stdout)["reason"])

    def test_review_installed_registry_byte_change_during_resolution_is_rejected(self):
        """Change only isolated bytes after parse; the JSON meaning is identical."""
        original_raw = DEFAULT_REGISTRY.read_bytes()
        original_digest = hashlib.sha256(original_raw).hexdigest()
        actual_file = reuse._file
        actual_catalogue = source_catalogue.build_catalog
        with tempfile.TemporaryDirectory() as temporary:
            captured = Path(temporary) / "registry.json"
            captured.write_bytes(original_raw)
            def redirected_file(root, relative):
                return captured if relative == reuse.REGISTRY else actual_file(root, relative)
            def replace_after_parse(root):
                result = actual_catalogue(root)
                captured.write_bytes(original_raw + b" \n")
                return result
            with patch.object(reuse, "_file", side_effect=redirected_file), \
                 patch.object(source_catalogue, "build_catalog", side_effect=replace_after_parse), no_execution():
                with self.assertRaisesRegex(FrameworkError, "registry changed during resolution"):
                    organization.build_organization_report(ROOT)
            changed = captured.read_bytes()
            self.assertNotEqual(hashlib.sha256(changed).hexdigest(), original_digest)
            self.assert_exact(json.loads(changed), json.loads(original_raw))
        self.assertEqual(hashlib.sha256(DEFAULT_REGISTRY.read_bytes()).hexdigest(), original_digest)

    def test_review_runtime_input_byte_change_cannot_replace_prior_owner_identity(self):
        """PR64 supplement: a later code read must agree with its real owner."""
        relative = "tools/entropy_framework/organization.py"
        installed = ROOT / relative
        original_raw = installed.read_bytes()
        original_digest = hashlib.sha256(original_raw).hexdigest()
        actual_file = reuse._file
        actual_reuse = reuse.build_reuse_report
        actual_catalogue = source_catalogue.build_catalog
        for mutate in (False, True):
            with self.subTest(mutate_temporary_copy=mutate), tempfile.TemporaryDirectory() as temporary:
                captured = Path(temporary) / "organization.py"
                captured.write_bytes(original_raw)
                prior = {}

                def redirected_file(root, path):
                    return captured if path == relative else actual_file(root, path)

                def capture_reuse(*args, **kwargs):
                    result = actual_reuse(*args, **kwargs)
                    prior["sha256"] = result["inputs"].get(relative)
                    return result

                def catalogue_then_change(*args, **kwargs):
                    result = actual_catalogue(*args, **kwargs)
                    if mutate:
                        captured.write_bytes(original_raw + b"\n# Isolated input-identity review mutation.\n")
                    return result

                with patch.object(reuse, "_file", side_effect=redirected_file), \
                     patch.object(reuse, "build_reuse_report", side_effect=capture_reuse), \
                     patch.object(source_catalogue, "build_catalog", side_effect=catalogue_then_change), \
                     no_execution():
                    if mutate:
                        with self.assertRaisesRegex(FrameworkError,
                                                    "input changed during resolution: " + re.escape(relative)):
                            organization.build_organization_report(ROOT)
                    else:
                        report = organization.build_organization_report(ROOT)
                        self.assertEqual(report["status"], "RESOLVED")
                        self.assertEqual(report["inputs"][relative], original_digest)
                self.assertEqual(prior["sha256"], original_digest,
                                 "The actual reuse owner must already have recorded this input")
                late_digest = hashlib.sha256(captured.read_bytes()).hexdigest()
                if mutate:
                    self.assertNotEqual(late_digest, original_digest)
                else:
                    self.assertEqual(late_digest, original_digest)
        self.assertEqual(hashlib.sha256(installed.read_bytes()).hexdigest(), original_digest)

    def test_review_scope_byte_budget_is_resource_exhaustion_not_invalid_or_unknown(self):
        value = self.fixture()
        value["rule_contract"]["organization"]["profiles"][0]["scope"] = "أ" * 4096
        self.assertEqual(len(value["rule_contract"]["organization"]["profiles"][0]["scope"].encode()), 8192)
        with no_execution():
            organization.validate_organization_structure(value["rule_contract"]["organization"])
        exceeded = deepcopy(value)
        exceeded["rule_contract"]["organization"]["profiles"][0]["scope"] += "أ"
        with no_execution(), self.assertRaises(FrameworkResourceError):
            validate_registry(exceeded)
        with patch.object(source_catalogue, "build_catalog",
                          side_effect=AssertionError("exhausted metadata loaded a source owner")), \
             patch.object(reuse, "build_reuse_report",
                          side_effect=AssertionError("exhausted metadata loaded a proof owner")), no_execution():
            with self.assertRaises(FrameworkResourceError):
                self.build(exceeded)
        malformed = self.fixture()
        malformed["rule_contract"]["organization"]["profiles"][0]["scope"] = 8193
        with self.assertRaises(FrameworkError) as caught:
            validate_registry(malformed)
        self.assertIs(type(caught.exception), FrameworkError)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "resource_limit.json"
            path.write_text(wire(exceeded), encoding="utf-8")
            result = self.cli(["validate", "--registry", str(path)])
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assert_fields(json.loads(result.stdout),
                           {"status": "RESOURCE_EXHAUSTED", "semantic_authority": "NONE"})


if __name__ == "__main__":
    unittest.main()
