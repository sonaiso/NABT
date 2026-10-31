"""Independent checks against the contract/oracle frozen at 50e3f51.

The literal oracle comes from the original inventory and separately authored
source diagnostics. Existing runtime equality is regression evidence; these
checks do not establish premise acquisition, source fidelity or Arabic coverage.
This test file was authored later. Supplemental review tests are separate from
the fourteen frozen acceptance groups and do not revise their gold.
"""
from __future__ import annotations

from contextlib import ExitStack, contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nabt import classical_laws
from nabt.errors import NabtError
from tools.grammar_catalog import catalog, routing
from tools.grammar_catalog.retrieval import RetrievalError, SearchIndex


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/operator_context_v1"
GOLD_SHA256 = "229ebcd32015207777a65fe5aa2d59f4c0397d4967bd70bc105111b3062bc2d3"
PREFIX = "nabt.classical-rule-inventory.v1::"
DIRECT_V1_KEYS = {
    "schema", "catalog_sha256", "authority", "schedule", "rows",
    "installed_rule_count", "examined_rule_count", "inventory_exhausted",
    "pending_rule_ids", "status", "conditional_evaluation_complete",
    "premises_established_from_free_text", "grants_language_license",
    "exhaustive_language_claim", "whole_book_completeness",
}


def wire(value):
    """Independent comparison/identity serialization, distinguishing false/0."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(wire(value)).hexdigest()


@contextmanager
def no_external_execution():
    """The existing Python conditional owners may run; no process may start."""
    with ExitStack() as stack:
        sentinels = [stack.enter_context(patch.object(owner, name,
                     side_effect=AssertionError("unexpected external execution: " + name)))
                     for owner, name in ((subprocess, "run"), (subprocess, "Popen"),
                                         (os, "system"))]
        yield
        for sentinel in sentinels:
            sentinel.assert_not_called()


class OperatorContextAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (EVIDENCE / "acceptance_cases.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != GOLD_SHA256:
            raise AssertionError("The frozen operator-context oracle changed")
        cls.gold = json.loads(raw)
        cls.groups = {row["id"]: row for row in cls.gold["cases"]}
        if set(cls.groups) != {f"OC{i:02d}" for i in range(1, 15)}:
            raise AssertionError("All fourteen frozen groups are required")
        cls.fixtures = cls.gold["fixtures"]
        cls.contexts = cls.fixtures["source_context_by_rule_id"]
        cls.query = cls.fixtures["query"]
        cls.frames = {"HAMZA-LEXICAL-COMMAND": cls.fixtures["lexical_frame"]}
        cls.original_catalogue = catalog.build_catalog(ROOT)
        cls.index = SearchIndex(cls.original_catalogue, root=ROOT)
        legacy_raw = (ROOT / cls.groups["OC14"]["legacy_baseline"]).read_bytes()
        if hashlib.sha256(legacy_raw).hexdigest() != cls.groups["OC14"]["legacy_raw_sha256"]:
            raise AssertionError("The archived preimplementation CLI report changed")
        cls.legacy_raw = legacy_raw
        cls.legacy_report = json.loads(legacy_raw)
        cls._whole_report = None

    def assert_exact(self, actual, expected):
        self.assertEqual(wire(actual), wire(expected))

    def assert_fields(self, actual, expected):
        for key, value in expected.items():
            with self.subTest(field=key):
                self.assertIn(key, actual)
                self.assert_exact(actual[key], value)

    def evaluate(self, frames, ranked=None, *, budget=None, version=2, index=None):
        with no_external_execution():
            return routing.evaluate_candidates(
                self.index if index is None else index,
                [] if ranked is None else ranked, frames,
                budget=budget, report_version=version)

    def build(self, *, query=None, frames=None, budget=None, version=2, index=None):
        with no_external_execution():
            return routing.build_routing_report(
                self.index if index is None else index,
                self.query if query is None else query,
                deepcopy(self.frames) if frames is None else frames,
                budget=budget, report_version=version)

    def verify(self, report, *, query=None, frames=None, budget=None, version=2):
        with no_external_execution():
            return routing.verify_routing_report(
                report, query=self.query if query is None else query,
                frames_by_rule=deepcopy(self.frames) if frames is None else frames,
                budget=budget, report_version=version, root=ROOT)

    def whole_report(self):
        # Cache observed input for mutation controls, never an expected oracle.
        if type(self)._whole_report is None:
            with no_external_execution():
                type(self)._whole_report = routing.build_routing_report(
                    self.index, self.query, deepcopy(self.frames))
        return deepcopy(type(self)._whole_report)

    def cli(self, arguments):
        environment = dict(os.environ)
        environment["PYTHONPATH"] = os.pathsep.join((str(ROOT / "src"), str(ROOT)))
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run([sys.executable, "-B", "-m", "tools.grammar_catalog", *arguments],
                              cwd=ROOT, env=environment, capture_output=True, timeout=45)

    def assert_contexts(self, report):
        self.assert_fields(report, self.fixtures["report_boundaries"])
        for row in report["rows"]:
            self.assertIn(row["rule_id"], self.contexts)
            self.assert_exact(row["source_context"], self.contexts[row["rule_id"]])
            if "receipt" in row:
                self.assert_fields(row["receipt"], {
                    "premises_established_from_free_text": False,
                    "grants_language_license": False,
                })
                self.assert_fields(row["verification"], {
                    "valid": True, "premises_established_from_free_text": False,
                    "grants_language_license": False,
                })

    def boundary_case(self, group, case):
        rid = case.get("rule_id", group.get("rule_id"))
        frame = deepcopy(case["frame"])
        before = wire(frame)
        report = self.evaluate({rid: frame}, [PREFIX + rid])
        self.assertEqual(wire(frame), before)
        self.assert_contexts(report)
        row = report["rows"][0]
        self.assertEqual(row["rule_id"], rid)
        self.assertEqual(row["status"], case["route_status"])
        if "receipt_present" in case:
            self.assertIs("receipt" in row, case["receipt_present"])
        if "error_code" in case:
            self.assert_fields(row["error"], {
                "code": case["error_code"], "status": case["error_status"],
            })
            self.assertNotIn("verification", row)
            return report, row
        result = row["receipt"]["result"]
        if "result_status" in case:
            self.assertEqual(result["status"], case["result_status"])
        alternatives = result["alternatives"]
        if "operations" in case:
            self.assert_exact([a["operation"] for a in alternatives], case["operations"])
        if "outputs" in case:
            field = ("morphophonemes" if rid.startswith("HAMZA") else
                     "segments" if rid.startswith("AFFIX") else "cells")
            self.assert_exact([a[field] for a in alternatives], case["outputs"])
        for field in ("segments", "surface_complete"):
            if field in case:
                self.assert_exact([a[field] for a in alternatives], case[field])
        for field in ("textual_discrepancy_retained", "unresolved_profiles",
                      "alternatives_complete_within_requested_profile"):
            if field in case:
                self.assert_exact(result[field], case[field])
        return report, row

    def test_oc01_exact_original_context_and_unchanged_population(self):
        expected = self.groups["OC01"]["expected"]
        self.assertEqual(self.original_catalogue["schema"], expected["catalogue_schema"])
        self.assertEqual(catalog.catalog_sha256(self.original_catalogue), expected["catalogue_sha256"])
        self.assertEqual(len(self.original_catalogue["rules"]), expected["catalogue_rule_count"])
        self.assertTrue(all("source_context" not in row for row in self.original_catalogue["rules"]))
        operators = [row["runtime_rule_id"] for row in self.original_catalogue["rules"]
                     if row["runtime_rule_id"] is not None]
        self.assertEqual(len(operators), expected["installed_operator_count"])
        self.assertEqual(set(operators), set(self.contexts))
        with no_external_execution():
            inventory = classical_laws.replay_inventory()
        self.assertEqual(len(inventory["rules"]), expected["inventory_rule_count"])
        with no_external_execution():
            report = routing.evaluate_candidates(self.index, [], {})
        self.assertEqual(set(report), DIRECT_V1_KEYS | {"request"})
        self.assert_exact(report["schedule"], self.fixtures["ordered_operator_ids"])
        self.assert_contexts(report)
        self.assertEqual(set(report["request"]), set(self.fixtures["request_keys_direct"]))
        self.assert_exact(report["request"], {
            "ranked_rule_keys": [], "frames_sha256": digest({}), "budget": None,
        })

    def test_oc02_unknown_hamza_is_not_a_scoped_blocker(self):
        group = self.groups["OC02"]
        for case in group["cases"]:
            with self.subTest(case=case["id"]):
                self.boundary_case(group, case)

    def test_oc03_dialect_alternatives_and_operations_stay_distinct(self):
        group = self.groups["OC03"]
        for case in group["cases"]:
            with self.subTest(case=case["id"]):
                self.boundary_case(group, case)

    def test_oc04_nun_discrepancy_and_two_source_owners_remain_visible(self):
        group = self.groups["OC04"]
        for case in group["cases"]:
            with self.subTest(case=case["id"]):
                _, row = self.boundary_case(group, case)
                context, receipt = row["source_context"], row["receipt"]
                self.assertEqual(context["source_text_status"], group["expected_context_status"])
                self.assertEqual(receipt["source_text_status"], group["expected_receipt_status"])
                self.assert_exact([s["source_id"] for s in context["source_spans"]],
                                  group["context_source_ids"])
                self.assertEqual({s["source_id"] for s in receipt["result"]["source_spans"]},
                                 set(group["runtime_source_ids"]))
                for span in context["source_spans"]:
                    self.assertIn(group["literal_source_fragments"][span["source_id"]],
                                  span["raw_text"])
                self.assertNotIn("implementation", context)

    def test_oc05_partial_bakr_surface_is_not_completed_by_context(self):
        group = self.groups["OC05"]
        for case in group["cases"]:
            with self.subTest(case=case["id"]):
                self.boundary_case(group, case)

    def test_oc06_light_nun_unresolved_profile_is_preserved(self):
        group = self.groups["OC06"]
        for case in group["cases"]:
            with self.subTest(case=case["id"]):
                self.boundary_case(group, case)

    def test_oc07_missing_frames_and_budget_do_not_fabricate_receipts(self):
        for case in self.groups["OC07"]["cases"]:
            with self.subTest(case=case["id"]), \
                 patch.object(classical_laws, "evaluate",
                              side_effect=AssertionError("metadata fabricated a frame")), \
                 patch.object(classical_laws, "verify",
                              side_effect=AssertionError("metadata fabricated a receipt")):
                report = self.evaluate(case["frames_by_rule"], case["ranked_rule_keys"],
                                       budget=case["budget"])
                self.assert_fields(report, {k: case[k] for k in (
                    "status", "examined_rule_count", "inventory_exhausted",
                    "conditional_evaluation_complete")})
                self.assert_contexts(report)
                self.assertEqual(sum("source_context" in r for r in report["rows"]),
                                 case["source_context_count"])
                self.assertEqual(sum("receipt" in r for r in report["rows"]), case["receipt_count"])
                self.assertEqual(len(report["pending_rule_ids"]), case["pending_rule_count"])
                self.assertTrue(all(type(r) is str for r in report["pending_rule_ids"]))
                if case["id"] == "zero_budget":
                    self.assert_exact(report["pending_rule_ids"], self.fixtures["ordered_operator_ids"])
                for row in report["rows"]:
                    self.assertEqual(row["status"], case["row_status"])
                    self.assertEqual(set(row), {"rule_id", "status", "source_context"})

    def test_oc08_frame_errors_keep_their_original_invalid_or_resource_kind(self):
        group = self.groups["OC08"]
        for case in group["cases"]:
            with self.subTest(case=case["id"]):
                report, _ = self.boundary_case(group, case)
                self.assertEqual(report["request"]["frames_sha256"],
                                 digest({case["rule_id"]: case["frame"]}))

    def test_oc09_embedded_receipts_and_rank_invariance_are_unchanged(self):
        group = self.groups["OC09"]
        rid = group["rule_id"]
        frames = {rid: deepcopy(group["frame"])}
        ranked = [PREFIX + rid, PREFIX + rid]
        v2 = self.evaluate(frames, ranked)
        v1 = self.evaluate(frames, ranked, version=1)
        legacy_projection = deepcopy(v2)
        legacy_projection.pop("request")
        legacy_projection["schema"] = "nabt.conditional-rule-routing.v1"
        for row in legacy_projection["rows"]:
            row.pop("source_context")
        self.assert_exact(legacy_projection, v1)
        self.assertEqual(set(v1), DIRECT_V1_KEYS)
        self.assert_exact(v2["request"]["ranked_rule_keys"], ranked)
        self.assertEqual(len(v2["schedule"]), 24)
        self.assertEqual(len(set(v2["schedule"])), 24)
        row = v2["rows"][0]
        with no_external_execution():
            native_receipt = classical_laws.evaluate(rid, deepcopy(group["frame"]))
            native_verification = classical_laws.verify(native_receipt)
        self.assert_exact(row["receipt"], native_receipt)
        self.assert_exact(row["verification"], native_verification)
        self.assertEqual(digest(row["receipt"]), group["receipt_sha256"])
        archived = next(r for r in self.legacy_report["rows"] if r["rule_id"] == rid)
        self.assert_exact(row["receipt"], archived["receipt"])
        self.assert_exact(row["verification"], archived["verification"])
        self.assert_exact([a["operation"] for a in row["receipt"]["result"]["alternatives"]],
                          group["operations"])
        self.assert_exact([a["morphophonemes"] for a in row["receipt"]["result"]["alternatives"]],
                          group["outputs"])
        reverse = self.evaluate(frames, [PREFIX + r for r in reversed(v2["schedule"])])
        self.assert_exact({r["rule_id"]: r for r in reverse["rows"]},
                          {r["rule_id"]: r for r in v2["rows"]})

    def test_oc10_wrong_rule_context_or_row_identity_fails_whole_replay(self):
        group = self.groups["OC10"]
        for mutation in group["mutations"]:
            with self.subTest(mutation=mutation):
                report = self.whole_report()
                row = next(r for r in report["rows"] if r["rule_id"] == group["report_rule_id"])
                other = group["substitute_context_rule_id"]
                if mutation == "replace_entire_source_context_with_other_valid_context":
                    row["source_context"] = deepcopy(self.contexts[other])
                elif mutation == "change_context_rule_id_only":
                    row["source_context"]["rule_id"] = other
                elif mutation == "change_context_rule_key_only":
                    row["source_context"]["rule_key"] = PREFIX + other
                elif mutation == "change_row_rule_id_only":
                    row["rule_id"] = other
                else:
                    self.fail("Unimplemented frozen mutation: " + mutation)
                with self.assertRaises(RetrievalError):
                    self.verify(report)

    def test_oc11_changed_context_and_rehashed_passage_cannot_supply_authority(self):
        group = self.groups["OC11"]
        for mutation in group["mutations"]:
            with self.subTest(path=mutation["path"]):
                report = self.whole_report()
                context = next(r["source_context"] for r in report["rows"]
                               if r["rule_id"] == group["rule_id"])
                parts = mutation["path"].split("/")
                parent = context
                for part in parts[:-1]:
                    parent = parent[int(part)] if type(parent) is list else parent[part]
                final = int(parts[-1]) if type(parent) is list else parts[-1]
                if "append" in mutation:
                    parent[final] += mutation["append"]
                    # A caller can rehash a forged quote; original bytes still win.
                    parent["sha256"] = hashlib.sha256(parent[final].encode()).hexdigest()
                else:
                    parent[final] = deepcopy(mutation["value"])
                digest(report)  # A well-formed caller digest cannot repair provenance.
                with self.assertRaises(RetrievalError):
                    self.verify(report)

    def test_oc12_whole_replay_binds_receipt_query_unused_frames_and_budget(self):
        group = self.groups["OC12"]
        report = self.whole_report()
        before = wire(report)
        with no_external_execution():
            verified = routing.verify_routing_report(
                report, query=self.query, frames_by_rule=deepcopy(self.frames), root=ROOT)
        self.assert_fields(verified, group["verification_equals"])
        self.assertEqual(set(verified), set(group["verification_equals"]) |
                         set(group["verification_identity_fields"]))
        self.assertEqual(verified["report_sha256"], digest(report))
        self.assertEqual(verified["catalog_sha256"], self.groups["OC01"]["expected"]["catalogue_sha256"])
        self.assertEqual(wire(report), before)
        self.assertEqual(set(report["request"]), set(self.fixtures["request_keys_whole"]))
        self.assert_exact(report["request"]["query"], self.query)

        damaged = deepcopy(report)
        row = next(r for r in damaged["rows"] if r["rule_id"] == "HAMZA-LEXICAL-COMMAND")
        row["receipt"]["result"]["alternatives"].pop()
        with no_external_execution(), self.assertRaises(NabtError) as caught:
            classical_laws.verify(row["receipt"])
        self.assertEqual(caught.exception.code, group["runtime_tamper_error_code"])
        with self.assertRaises(RetrievalError):
            self.verify(damaged)

        self.assert_exact(self.index.search(group["query"], kind="rule", limit=10),
                          self.index.search(group["equivalent_search_query"], kind="rule", limit=10))
        with self.assertRaises(RetrievalError):
            self.verify(report, query=group["equivalent_search_query"])

        unused = {group["unused_rule_id"]: deepcopy(group["unused_frame"])}
        zero = self.build(frames=unused, budget=0)
        self.assertEqual(zero["rows"], [])
        self.assertEqual(zero["request"]["frames_sha256"], digest(unused))
        self.assertTrue(self.verify(zero, frames=unused, budget=0)["valid"])
        changed = {group["unused_rule_id"]: deepcopy(group["changed_unused_frame"])}
        with self.assertRaises(RetrievalError):
            self.verify(zero, frames=changed, budget=0)

        with self.assertRaises(RetrievalError):
            self.verify(report, budget=24)
        explicit = self.build(budget=24)
        self.assertTrue(self.verify(explicit, budget=24)["valid"])
        with self.assertRaises(RetrievalError):
            self.verify(explicit, budget=None)
        changed = deepcopy(report)
        changed["request"]["ranked_rule_keys"].append(PREFIX + "HAMZA-LEXICAL-COMMAND")
        with self.assertRaises(RetrievalError):
            self.verify(changed)
        for version in (1, 2):
            with self.subTest(legacy_verification_version=version), self.assertRaises(RetrievalError):
                self.verify(self.legacy_report, version=version)

        # Failure of the existing generated-receipt owner is a global v2 failure.
        with patch.object(classical_laws, "verify", side_effect=NabtError(
                "CLASSICAL_RECEIPT_MISMATCH", "independent injected owner failure")), \
             self.assertRaises(NabtError) as caught:
            self.evaluate(deepcopy(self.frames))
        self.assertEqual(caught.exception.code, "CLASSICAL_RECEIPT_MISMATCH")

    def test_oc13_real_original_source_mutation_fails_current_owner_replay(self):
        group = self.groups["OC13"]
        source_path = ROOT / group["source_path"]
        original_raw = source_path.read_bytes()
        original_sha = hashlib.sha256(original_raw).hexdigest()
        inventory_path = ROOT / "src/nabt/data/source_evidence/classical_rule_inventory_v1.json"
        inventory = json.loads(inventory_path.read_bytes())
        original_read = catalog._read
        report = self.whole_report()
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary)
            directory = package / "data/source_evidence"
            directory.mkdir(parents=True)
            (directory / inventory_path.name).write_bytes(inventory_path.read_bytes())
            for source in inventory["sources"]:
                (directory / source["local_file"]).write_bytes(
                    (inventory_path.parent / source["local_file"]).read_bytes())
            copied = directory / source_path.name

            def redirected_read(root, relative):
                return copied.read_bytes() if relative == group["source_path"] else original_read(root, relative)

            with patch.object(catalog, "_read", side_effect=redirected_read), \
                 patch.object(classical_laws, "files", return_value=package):
                self.assertTrue(self.verify(report)["valid"])
                copied.write_bytes(b"X" + original_raw[1:])
                self.assertEqual(len(copied.read_bytes()), len(original_raw))
                with self.assertRaises(catalog.CatalogError):
                    self.verify(report)
                with self.assertRaises(catalog.CatalogError):
                    self.evaluate(deepcopy(self.frames), index=self.index)
            # The real runtime owner also rejects those bytes when the catalogue
            # is still current; it must not become a per-frame error row.
            with patch.object(classical_laws, "files", return_value=package), \
                 self.assertRaises(NabtError) as caught:
                self.evaluate(deepcopy(self.frames))
            self.assertEqual(caught.exception.code, group["runtime_source_error_code"])
            self.assertEqual(caught.exception.status, group["runtime_source_error_status"])
        self.assertEqual(hashlib.sha256(source_path.read_bytes()).hexdigest(), original_sha)

    def test_oc14_cli_default_legacy_replay_output_and_strict_file_parsing(self):
        group = self.groups["OC14"]
        frames_path = ROOT / group["frames_baseline"]
        self.assertEqual(hashlib.sha256(frames_path.read_bytes()).hexdigest(), group["frames_raw_sha256"])
        self.assertEqual(digest(self.legacy_report), group["legacy_canonical_sha256"])
        legacy = self.cli(["route", self.query, "--frames", str(frames_path), "--legacy"])
        self.assertEqual(legacy.returncode, 0, legacy.stderr.decode())
        self.assertEqual(legacy.stdout, self.legacy_raw)
        default = self.cli(["route", self.query, "--frames", str(frames_path)])
        self.assertEqual(default.returncode, 0, default.stderr.decode())
        report = json.loads(default.stdout)
        self.assert_contexts(report)
        self.assert_exact(report, self.whole_report())
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            output = directory / "route.json"
            arguments = ["route", self.query, "--frames", str(frames_path), "--output", str(output)]
            written = self.cli(arguments)
            self.assertEqual(written.returncode, 0, written.stderr.decode())
            self.assert_exact(json.loads(output.read_bytes()), report)
            saved = output.read_bytes()
            repeated = self.cli(arguments)
            self.assertEqual(repeated.returncode, group["expected_input_exit_code"])
            self.assertEqual(output.read_bytes(), saved)
            checked = self.cli(["verify-route", str(output), "--query", self.query,
                                "--frames", str(frames_path)])
            self.assertEqual(checked.returncode, 0, checked.stderr.decode())
            self.assert_fields(json.loads(checked.stdout), self.groups["OC12"]["verification_equals"])
            verification_path = directory / "verification.json"
            check_args = ["verify-route", str(output), "--query", self.query,
                          "--frames", str(frames_path), "--output", str(verification_path)]
            self.assertEqual(self.cli(check_args).returncode, 0)
            checked_bytes = verification_path.read_bytes()
            self.assertEqual(self.cli(check_args).returncode, group["expected_input_exit_code"])
            self.assertEqual(verification_path.read_bytes(), checked_bytes)

            tampered = deepcopy(report)
            tampered["rows"][0]["source_context"]["source_blockers"] = "none"
            output.write_bytes(wire(tampered))
            rejected = self.cli(["verify-route", str(output), "--query", self.query,
                                 "--frames", str(frames_path)])
            self.assertEqual(rejected.returncode, group["expected_input_exit_code"])
            self.assertEqual(json.loads(rejected.stdout)["status"], group["expected_input_status"])
            # Duplicate the correct schema in an otherwise valid report: a lax
            # last-wins parser would reconstruct the exact successful report.
            duplicated = b'{"schema":"nabt.conditional-rule-routing.v2",' + wire(report)[1:]
            output.write_bytes(duplicated)
            rejected = self.cli(["verify-route", str(output), "--query", self.query,
                                 "--frames", str(frames_path)])
            self.assertEqual(rejected.returncode, group["expected_input_exit_code"])
            duplicate_frames = directory / "duplicate_frames.json"
            entry = json.dumps("HAMZA-LEXICAL-COMMAND").encode() + b":" + wire(self.fixtures["lexical_frame"])
            duplicate_frames.write_bytes(b"{" + entry + b"," + entry + b"}")
            rejected = self.cli(["route", self.query, "--frames", str(duplicate_frames)])
            self.assertEqual(rejected.returncode, group["expected_input_exit_code"])

    def test_oc14_mutable_index_records_scores_and_source_identity_are_rejected(self):
        key = ("rule", PREFIX + "HAMZA-LEXICAL-COMMAND")
        for mutation in self.groups["OC14"]["changed_index_cases"]:
            with self.subTest(mutation=mutation):
                index = SearchIndex(self.original_catalogue, root=ROOT)
                if mutation == "forged _docs rule record":
                    index._docs[key]["record"]["scope"] = "all Arabic"
                elif mutation == "forged advertised catalog_sha256":
                    index.catalog_sha256 = "0" * 64
                elif mutation == "forged _docs search_text":
                    index._docs[key]["search_text"] += " forged query ranking"
                elif mutation == "forged _tf counter":
                    index._tf[key]["forged"] = 2000
                elif mutation == "mutated or stale _catalog rejected by current original-root owner replay":
                    index._catalog["rules"][0]["scope"] = "stale source selection"
                else:
                    self.fail("Unimplemented frozen index mutation: " + mutation)
                with self.assertRaises((RetrievalError, catalog.CatalogError)):
                    self.build(index=index)

    def test_oc14_strict_json_versions_and_document_resource_boundaries(self):
        group = self.groups["OC14"]
        for version in (True, False, 2.0, "2", 0, 3):
            with self.subTest(version=version), self.assertRaises(RetrievalError):
                self.evaluate({}, version=version)
        for budget in (True, False, 1.0, -1, 25):
            with self.subTest(budget=budget), self.assertRaises(RetrievalError):
                self.evaluate({}, budget=budget)
        report = self.whole_report()
        for kind in ("tuple", "false_as_zero", "nonfinite", "surrogate", "unknown_approval"):
            with self.subTest(kind=kind):
                changed = deepcopy(report)
                if kind == "tuple":
                    changed["schedule"] = tuple(changed["schedule"])
                elif kind == "false_as_zero":
                    changed["grants_language_license"] = 0
                elif kind == "nonfinite":
                    changed["retrieval"]["candidates"][0]["lexical_score"] = float("nan")
                elif kind == "surrogate":
                    changed["request"]["query"] = "\ud800"
                else:
                    changed["approved"] = True
                with self.assertRaises(RetrievalError):
                    self.verify(changed)
        self.assertTrue(any(type(row.get("lexical_score")) is float
                            for row in report["retrieval"]["candidates"]))
        self.assertTrue(self.verify(report)["valid"])
        oversized = deepcopy(report)
        oversized["request"]["query"] = "x" * (group["limits"]["routing_document_bytes"] + 1)
        with self.assertRaises(NabtError) as caught:
            self.verify(oversized)
        self.assertEqual((caught.exception.code, caught.exception.status), ("RESOURCE_LIMIT", "DEFER"))
        with tempfile.TemporaryDirectory() as temporary:
            # Valid JSON with leading whitespace exceeds the reader byte budget.
            # Only the temporary file is large; no source/manifest is changed.
            path = Path(temporary) / "large_frames.json"
            path.write_bytes(b" " * group["limits"]["routing_document_bytes"] + b"{}")
            result = self.cli(["route", self.query, "--frames", str(path)])
            self.assertEqual(result.returncode, group["expected_global_resource_exit_code"])
            self.assert_fields(json.loads(result.stdout), group["expected_global_resource_error"])

    def test_oc14_returned_context_request_and_receipt_are_detached(self):
        frames = deepcopy(self.frames)
        before = wire(frames)
        ranked = [PREFIX + "HAMZA-LEXICAL-COMMAND"]
        ranked_before = deepcopy(ranked)
        report = self.evaluate(frames, ranked)
        self.assertEqual(wire(frames), before)
        self.assert_exact(ranked, ranked_before)
        expected_frames_sha = hashlib.sha256(before).hexdigest()
        frames["HAMZA-LEXICAL-COMMAND"]["root"][0] = "ب"
        ranked.append(PREFIX + "HAMZA-FINAL-LONG")
        self.assertEqual(report["request"]["frames_sha256"], expected_frames_sha)
        self.assert_exact(report["request"]["ranked_rule_keys"], ranked_before)
        self.assert_exact(report["rows"][0]["receipt"]["input_frame"], self.fixtures["lexical_frame"])
        context = report["rows"][0]["source_context"]
        context["positive_cases"][0]["surface"] = "mutated caller view"
        context["source_spans"][0]["raw_text"] = "mutated caller quotation"
        context["owner"]["sha256"] = "0" * 64
        again = self.evaluate(deepcopy(self.frames), ranked_before)
        self.assert_contexts(again)
        self.assert_exact(again["rows"][0]["source_context"], self.contexts["HAMZA-LEXICAL-COMMAND"])
        self.assertEqual(catalog.catalog_sha256(self.original_catalogue),
                         self.groups["OC01"]["expected"]["catalogue_sha256"])

    def test_review_aggregate_byte_budget_precedes_whole_serialization(self):
        """Supplement: reject aggregate expansion before serializing it whole."""
        shared = "x" * 64
        payload = [shared, shared, shared]
        self.assertIs(payload[0], payload[1])
        self.assertEqual(len(wire(payload)), 202)
        limit = 128
        with patch.object(routing, "MAX_ROUTING_DOCUMENT_BYTES", limit):
            control, encoded = routing._snapshot_document([shared], "small aggregate control")
        self.assert_exact(control, [shared])
        self.assertEqual(encoded, b'["' + b"x" * 64 + b'"]')
        self.assertEqual(len(encoded), 68)

        actual_dumps = json.dumps
        aggregate_calls = []

        def observe_dumps(value, *args, **kwargs):
            if (type(value) is list and len(value) == 3 and
                    all(type(item) is str and item == shared for item in value)):
                aggregate_calls.append(dict(kwargs))
            return actual_dumps(value, *args, **kwargs)

        with patch.object(routing, "MAX_ROUTING_DOCUMENT_BYTES", limit), \
             patch.object(routing.json, "dumps", side_effect=observe_dumps):
            with self.assertRaises(NabtError) as caught:
                routing._snapshot_document(payload, "aggregate budget review")
        self.assertEqual((caught.exception.code, caught.exception.status),
                         ("RESOURCE_LIMIT", "DEFER"))
        self.assertEqual(aggregate_calls, [],
                         "A late error after serializing all 202 bytes does not enforce the 128-byte bound")

    def test_review_pretty_byte_budget_stops_before_complete_output(self):
        """Supplement: stop pretty output at the bound, before full materialization."""
        payload = "x" * 32
        for _ in range(8):
            payload = [payload]
        self.assertEqual(len(wire(payload)), 50)
        limit = 128
        with patch.object(routing, "MAX_ROUTING_DOCUMENT_BYTES", limit):
            control = routing.routing_document_text(["x" * 32])
        self.assert_exact(json.loads(control), ["x" * 32])
        self.assertTrue(control.endswith("\n"))
        self.assertLessEqual(len(control.encode("utf-8")), limit)

        actual_dumps = json.dumps
        actual_iterencode = json.JSONEncoder.iterencode
        oversized_complete_dumps = []
        pretty_streams = []

        def observe_dumps(value, *args, **kwargs):
            result = actual_dumps(value, *args, **kwargs)
            if kwargs.get("indent") == 2 and len(result.encode("utf-8")) > limit:
                oversized_complete_dumps.append(len(result.encode("utf-8")))
            return result

        def observe_iterencode(encoder, value, *args, **kwargs):
            stream = actual_iterencode(encoder, value, *args, **kwargs)
            if encoder.indent != 2:
                yield from stream
                return
            observation = {"utf8_bytes": 0, "completed": False}
            pretty_streams.append(observation)
            for chunk in stream:
                observation["utf8_bytes"] += len(chunk.encode("utf-8"))
                yield chunk
            observation["completed"] = True

        with patch.object(routing, "MAX_ROUTING_DOCUMENT_BYTES", limit), \
             patch.object(routing.json, "dumps", side_effect=observe_dumps), \
             patch.object(json.JSONEncoder, "iterencode", new=observe_iterencode):
            with self.assertRaises(NabtError) as caught:
                routing.routing_document_text(payload)
        self.assertEqual((caught.exception.code, caught.exception.status),
                         ("RESOURCE_LIMIT", "DEFER"))
        self.assertEqual(oversized_complete_dumps, [],
                         "The 194-byte pretty string must not be built before rejecting the 128-byte limit")
        self.assertTrue(all(not row["completed"] for row in pretty_streams),
                        "Replacing dumps with complete iterator consumption still exceeds the output budget")


if __name__ == "__main__":
    unittest.main()
