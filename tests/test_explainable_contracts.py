"""Independent acceptance for explanation contracts over the existing pilot.

The nine source/query expectations were frozen before implementation. Literal
oracles below are authored data, not the production parser, closure, renderer,
or status recurrence. Native acceptance remains mandatory for every successful
answer. Mocked process receipts exercise only Python protocol rejection.
"""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import explainable_pilot as pilot


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "evidence/explanation_contracts_v1/acceptance_cases.json"
MATRIX_SHA256 = "e5bdc1e1707ca5f610f56ac2e4e3f6af6c2f54f4e7f02842c1b6161d606f0b6a"
BASELINE = ROOT / "evidence/explanation_contracts_v1/baseline_answer_v1.json"
BASELINE_SHA256 = "a1f9c0d84a68bf36e15bcb1e9e0eab77b0a077c74a52965052d5319f25d19cb3"
BINARY = Path(os.environ.get("NABT_VERIFIED_READING", ROOT / "formal/.lake/build/bin/verifiedReading"))
if ("NABT_VERIFIED_READING" in os.environ or os.environ.get("NABT_REQUIRE_EXPLANATION_CONTRACTS_NATIVE") == "1") and not BINARY.is_file():
    raise RuntimeError("Explanation-contract acceptance requires the built verifiedReading executable")

HISTORICAL_HASHES = {
    "example-answer.json": "3618f0b57e6435d894f9c55f8c3059fe4425940e6900bcb141e6bcf105c3e7fc",
    "cases.json": "7e1a2a58658d3a54a85446f02d3ff778e5bd8fca5d99d944fe94de94451dcaef",
    "goals.json": "56526dab92c7af38c28608a7df335e8f9fb132f09ae28e66a0e59101c192f09e",
}

# Explicit independent literal identities for the frozen engineering cases.
ATOMS = {
    "سالم هو حكيم": {"predicate": "حكيم", "arguments": ["سالم"], "positive": True},
    "ليس سالم هو حكيم": {"predicate": "حكيم", "arguments": ["سالم"], "positive": False},
    "سالم هو عادل": {"predicate": "عادل", "arguments": ["سالم"], "positive": True},
    "سالم هو عالم": {"predicate": "عالم", "arguments": ["سالم"], "positive": True},
    "ليس سالم هو عالم": {"predicate": "عالم", "arguments": ["سالم"], "positive": False},
    "سالم هو حاضر": {"predicate": "حاضر", "arguments": ["سالم"], "positive": True},
    "سهيل هو عالم": {"predicate": "عالم", "arguments": ["سهيل"], "positive": True},
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def atom_set(values):
    return {canonical(atom) for atom in values}


def cases():
    return json.loads(MATRIX.read_text(encoding="utf-8"))["cases"]


class FrozenContractInputs(unittest.TestCase):
    def test_acceptance_matrix_and_preimplementation_v1_are_unchanged(self):
        self.assertEqual(sha256(MATRIX.read_bytes()).hexdigest(), MATRIX_SHA256)
        self.assertEqual(sha256(BASELINE.read_bytes()).hexdigest(), BASELINE_SHA256)
        material = json.loads(MATRIX.read_text(encoding="utf-8"))
        self.assertEqual(material["base_commit"], "345713c2934333fe9c71e5e82212c46cae5a5213")
        self.assertEqual(len(material["cases"]), 9)
        self.assertEqual(len({row["id"] for row in material["cases"]}), 9)

    def test_historical_pilot_gold_and_answer_are_unchanged(self):
        for filename, digest in HISTORICAL_HASHES.items():
            with self.subTest(filename=filename):
                raw = (ROOT / "evidence/explainable_pilot" / filename).read_bytes()
                self.assertEqual(sha256(raw).hexdigest(), digest)

    def test_missing_native_never_returns_an_explanation_or_semantic_status(self):
        row = cases()[0]
        with self.assertRaises(pilot.PilotError) as caught:
            pilot.answer(row["source"].encode(), row["query"].encode(), checker="/missing/verifiedReading")
        self.assertEqual(caught.exception.code, "CHECKER_UNAVAILABLE")


@unittest.skipUnless(BINARY.is_file(), "build verifiedReading; dedicated acceptance requires native verification")
class ExplanationContractAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {row["id"]: row for row in cases()}

    def answer(self, case_id="EC01-direct-support", **options):
        row = self.rows[case_id]
        return pilot.answer(row["source"].encode(), row["query"].encode(), checker=BINARY, **options)

    def replay(self, case_id, bundle, **options):
        row = self.rows[case_id]
        return pilot.verify(row["source"].encode(), row["query"].encode(), bundle, checker=BINARY, **options)

    def assert_rejected(self, call, code=None):
        with self.assertRaises(pilot.PilotError) as caught:
            call()
        if code is not None:
            self.assertEqual(caught.exception.code, code)

    def test_nine_independent_source_grounded_cases(self):
        for case_id, row in self.rows.items():
            with self.subTest(case=case_id):
                expected = row["expected"]
                bundle = self.answer(case_id)
                self.assertEqual(bundle["schema"], "nabt.explainable-answer.v2")
                explanation = bundle["explanation"]
                self.assertEqual(explanation["schema"], "nabt.explanation-contract.v1")
                self.assertEqual(explanation["law_id"], "nabt.verified-ground-reading.v1")
                self.assertEqual(explanation["basis"]["binding"], bundle["binding"])
                self.assertEqual(bundle["answer"]["status"], expected["status"])
                native = bundle["verification"]["native_receipt"]
                axes = explanation["axes"]
                self.assertEqual(set(axes), {"reading_fidelity", "premise_support", "inference_validity", "case_applicability"})
                self.assertEqual(axes["inference_validity"]["status_from_native"], expected["status"])
                for field, oracle in (("positive", "full_positive"), ("negative", "full_negative"),
                                      ("clean_positive", "clean_positive"), ("clean_negative", "clean_negative")):
                    self.assertIs(native[field], expected[oracle])
                    self.assertIs(axes["inference_validity"][field], expected[oracle])

                operations = explanation["operations"]
                by_clause = {op["clause_id"]: op for op in operations}
                self.assertEqual(len(by_clause), len(operations))
                self.assertEqual(list(by_clause), [f"c{i}" for i in range(len(row["source"].splitlines()))])
                raw = row["source"].encode()
                restored = []
                for op in operations:
                    anchor = op["source_anchor"]
                    exact = raw[anchor["byte_start"]:anchor["byte_end"]]
                    self.assertEqual(exact, anchor["text"].encode())
                    restored.append(exact)
                self.assertEqual(b"".join(restored), raw)

                actual_premises = {op["clause_id"]: [p["atom"] for p in op["required_premises"]]
                                   for op in operations if op["kind"] == "rule"}
                expected_premises = {f"c{p['clause']}": [ATOMS[t] for t in p["atoms"]]
                                     for p in expected["required_rule_premises"]}
                self.assertEqual(actual_premises, expected_premises)
                for clause_id in expected_premises:
                    self.assertEqual(by_clause[clause_id]["contract"]["premise_combination"], "AND")
                actual_missing = {op["clause_id"]: op["missing_full_premises"]
                                  for op in operations if op["missing_full_premises"]}
                expected_missing = {f"c{p['clause']}": [ATOMS[t] for t in p["atoms"]]
                                    for p in expected["missing_premises"]}
                self.assertEqual(actual_missing, expected_missing)
                self.assertEqual([op["clause_id"] for op in operations if not op["clean_retained"]],
                                 [f"c{i}" for i in expected["blocked_clauses"]])
                contested = [c[field] for c in explanation["conflicts"]
                             for field in ("positive_atom", "negative_atom")]
                self.assertEqual(atom_set(contested), atom_set([ATOMS[t] for t in expected["contested_atoms"]]))

                evidence = bundle["analysis_certificate"]
                for theory in ("full", "clean"):
                    root = explanation["targets"]["query"][theory + "_root"]
                    expected_clause = expected[theory + "_query_clause"]
                    trace = {node["id"]: node for node in evidence["traces"][theory]}
                    self.assertEqual(None if root is None else trace[root]["clause_id"],
                                     None if expected_clause is None else f"c{expected_clause}")
                self.assertTrue(self.replay(case_id, bundle)["verified"])

    def test_conjunction_and_actual_dependencies_preserve_every_required_premise(self):
        bundle = self.answer("EC02-two-premise-chain")
        e = bundle["explanation"]
        operations = {op["clause_id"]: op for op in e["operations"]}
        self.assertEqual([p["full_witness"] for p in operations["c2"]["required_premises"]], ["f0", "f1"])
        self.assertEqual([p["clean_witness"] for p in operations["c2"]["required_premises"]], ["k0", "k1"])
        self.assertEqual([p["full_witness"] for p in operations["c3"]["required_premises"]], ["f2"])
        self.assertEqual([p["clean_witness"] for p in operations["c3"]["required_premises"]], ["k2"])
        for theory, prefix in (("full", "f"), ("clean", "k")):
            dependency = e["dependencies"][theory]["query"]
            self.assertEqual(dependency["root"], prefix + "3")
            self.assertEqual(dependency["step_ids"], [prefix + str(i) for i in range(4)])
            self.assertEqual(dependency["clause_ids"], ["c0", "c1", "c2", "c3"])
            self.assertEqual(dependency["fact_clause_ids"], ["c0", "c1"])
            self.assertEqual(dependency["rule_clause_ids"], ["c2", "c3"])
            self.assertIsNone(e["dependencies"][theory]["opposite_query"])

    def test_clean_alternate_proof_keeps_contested_rule_and_uses_its_actual_fact(self):
        bundle = self.answer("EC06-clean-alternate-support")
        e = bundle["explanation"]
        operations = {op["clause_id"]: op for op in e["operations"]}
        self.assertEqual(bundle["answer"]["status"], "SUPPORTED")
        self.assertIs(operations["c2"]["clean_retained"], False)
        self.assertEqual(atom_set(operations["c2"]["blocked_atoms"]),
                         atom_set([ATOMS["سالم هو حكيم"], ATOMS["ليس سالم هو حكيم"]]))
        self.assertEqual(operations["c2"]["clean_steps"], [])
        self.assertEqual(e["conflicts"][0]["affected_clause_ids"], ["c0", "c1", "c2"])
        self.assertIn("c2", e["targets"]["query"]["relevant_clause_ids"])
        self.assertIn("c3", e["targets"]["query"]["relevant_clause_ids"])
        self.assertEqual(e["targets"]["query"]["rule_alternatives"], "OR")
        self.assertEqual(e["targets"]["query"]["premises_within_rule"], "AND")
        self.assertEqual(e["dependencies"]["clean"]["query"]["clause_ids"], ["c3"])
        self.assertEqual(e["dependencies"]["clean"]["query"]["fact_clause_ids"], ["c3"])
        self.assertEqual(e["dependencies"]["clean"]["query"]["rule_clause_ids"], [])

    def test_unknown_and_cycles_explain_missing_premises_without_promising_a_repair(self):
        for case_id in ("EC03-one-missing-antecedent", "EC08-changed-rule-antecedent", "EC09-unsupported-rule-cycle"):
            with self.subTest(case=case_id):
                e = self.answer(case_id)["explanation"]
                self.assertIsNone(e["targets"]["query"]["full_root"])
                self.assertIsNone(e["targets"]["query"]["clean_root"])
                self.assertIs(e["judgment_change"]["missing_premises_are_not_false"], True)
                self.assertIs(e["judgment_change"]["outcome_guaranteed"], False)

    def test_four_axes_do_not_promote_source_support_to_world_or_action_authority(self):
        e = self.answer()["explanation"]
        axes = e["axes"]
        self.assertEqual(axes["reading_fidelity"]["status"], "VERIFIED_CANONICAL_GROUND_READING")
        self.assertEqual(axes["reading_fidelity"]["source_authenticity"], "NOT_ESTABLISHED")
        self.assertEqual(axes["reading_fidelity"]["author_intention"], "NOT_ESTABLISHED")
        self.assertEqual(axes["premise_support"]["status"], "SOURCE_RELATIVE_ONLY")
        self.assertEqual(axes["premise_support"]["external_truth"], "NOT_ESTABLISHED")
        self.assertEqual(axes["inference_validity"]["status"], "VERIFIED_SOURCE_RELATIVE_CLOSURES")
        self.assertEqual(axes["case_applicability"]["status"], "SCOPED_GROUND_MATCHING_ONLY")
        self.assertEqual(axes["case_applicability"]["external_case_applicability"], "NOT_ESTABLISHED")
        self.assertEqual(axes["case_applicability"]["action_authority"], "NONE")
        for limit in ("all_arabic_complete", "world_truth_established", "renderer_formally_proved",
                      "all_derivations_enumerated", "minimal_or_necessary_repair_claimed",
                      "source_book_rule_contracts_inferred"):
            self.assertIs(e["limits"][limit], False)
        unmatched = self.answer("EC07-same-predicate-wrong-entity")["explanation"]
        self.assertEqual(unmatched["axes"]["case_applicability"]["status"], "SCOPED_GROUND_MATCHING_ONLY")
        self.assertEqual(unmatched["targets"]["query"]["atom"], ATOMS["سهيل هو عالم"])
        self.assertEqual(unmatched["targets"]["query"]["producer_clause_ids"], [])
        self.assertIsNone(unmatched["targets"]["query"]["full_root"])
        self.assertIsNone(unmatched["targets"]["query"]["clean_root"])

    def test_omitted_premises_blockers_or_forged_explanation_fail_whole_bundle_replay(self):
        chain = self.answer("EC02-two-premise-chain")
        defer = self.answer("EC05-contested-only-support")
        mutations = [
            ("EC02-two-premise-chain", chain, lambda b: b["explanation"]["operations"][2]["required_premises"].pop()),
            ("EC02-two-premise-chain", chain, lambda b: b["explanation"]["dependencies"]["clean"]["query"]["clause_ids"].pop()),
            ("EC05-contested-only-support", defer, lambda b: b["explanation"]["operations"][2]["blocked_atoms"].clear()),
            ("EC05-contested-only-support", defer, lambda b: b["explanation"]["conflicts"].clear()),
            ("EC05-contested-only-support", defer, lambda b: b["explanation"]["operations"][2].update(clean_retained=True)),
            ("EC02-two-premise-chain", chain, lambda b: b["explanation"]["axes"]["case_applicability"].update(action_authority="AUTHORIZED")),
            ("EC02-two-premise-chain", chain, lambda b: b["explanation"]["axes"]["premise_support"].update(external_truth="ESTABLISHED")),
            ("EC02-two-premise-chain", chain, lambda b: b["explanation"].update(source_authenticity_established=True)),
            ("EC02-two-premise-chain", chain, lambda b: b["answer"].update(status="REFUTED")),
        ]
        for number, (case_id, original, mutate) in enumerate(mutations):
            with self.subTest(mutation=number):
                changed = deepcopy(original)
                mutate(changed)
                self.assert_rejected(lambda: self.replay(case_id, changed), "ANSWER_REJECTED")

    def test_substituted_source_certificate_query_and_revision_never_rebind_an_answer(self):
        case_id = "EC02-two-premise-chain"
        row = self.rows[case_id]
        bundle = self.answer(case_id)
        changed = deepcopy(bundle)
        changed["analysis_certificate"]["kernel_certificate"] = self.answer()["analysis_certificate"]["kernel_certificate"]
        self.assert_rejected(lambda: self.replay(case_id, changed), "CERTIFICATE_REJECTED")
        self.assert_rejected(lambda: pilot.verify(row["source"].encode() + b" ", row["query"].encode(), bundle,
                                                  checker=BINARY), "CERTIFICATE_REJECTED")
        other_query = self.rows["EC01-direct-support"]["query"].encode()
        self.assert_rejected(lambda: pilot.verify(row["source"].encode(), other_query, bundle,
                                                  checker=BINARY), "CERTIFICATE_REJECTED")
        for field, value in (("identity", "other-source"), ("revision", "2"), ("scope", "other-scope")):
            with self.subTest(binding=field):
                self.assert_rejected(lambda: self.replay(case_id, bundle, **{field: value}), "CERTIFICATE_REJECTED")

    def test_contract_and_binding_versions_and_hashes_are_replayed_not_trusted(self):
        bundle = self.answer()
        changes = [
            lambda b: b["explanation"].update(schema="nabt.explanation-contract.v999"),
            lambda b: b["explanation"].update(law_id="caller-law"),
            lambda b: b["explanation"]["basis"]["binding"].update(source_sha256="0" * 64),
            lambda b: b["binding"].update(query_sha256="0" * 64),
            lambda b: b["verification"].update(checker_sha256="0" * 64),
        ]
        for number, mutate in enumerate(changes):
            with self.subTest(mutation=number):
                changed = deepcopy(bundle)
                mutate(changed)
                self.assert_rejected(lambda: self.replay("EC01-direct-support", changed), "ANSWER_REJECTED")

    def test_v1_reconstruction_is_compatible_but_explicit_v2_prevents_downgrade(self):
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        receipt = baseline["verification"]["native_receipt"]
        raw, query = receipt["source_text"].encode(), receipt["query_text"].encode()
        current_v1 = pilot.answer(raw, query, checker=BINARY, answer_version="v1")
        actual_checker_sha256 = sha256(BINARY.read_bytes()).hexdigest()
        self.assertEqual(current_v1["verification"]["checker_sha256"], actual_checker_sha256)
        # Structural v1 compatibility must allow a verifier rebuilt elsewhere.
        # This in-memory projection is not a replay or endorsement of the
        # retained historical receipt; that file and its hash stay unchanged.
        compatible_baseline = deepcopy(baseline)
        compatible_baseline["verification"]["checker_sha256"] = actual_checker_sha256
        self.assertEqual(canonical(current_v1), canonical(compatible_baseline))
        self.assertNotIn("explanation", current_v1)
        self.assertTrue(pilot.verify(raw, query, current_v1, checker=BINARY)["verified"])
        self.assertTrue(pilot.verify(raw, query, current_v1, checker=BINARY, answer_version="v1")["verified"])
        self.assert_rejected(lambda: pilot.verify(raw, query, current_v1, checker=BINARY, answer_version="v2"), "ANSWER_REJECTED")
        current_v2 = pilot.answer(raw, query, checker=BINARY)
        self.assertEqual(current_v2["schema"], "nabt.explainable-answer.v2")
        self.assertTrue(pilot.verify(raw, query, current_v2, checker=BINARY, answer_version="v2")["verified"])
        self.assert_rejected(lambda: pilot.verify(raw, query, current_v2, checker=BINARY, answer_version="v1"), "ANSWER_REJECTED")

    def test_historical_v1_checker_identity_is_not_silently_rewritten(self):
        historical = json.loads((ROOT / "evidence/explainable_pilot/example-answer.json").read_text(encoding="utf-8"))
        receipt = historical["verification"]["native_receipt"]
        raw, query = receipt["source_text"].encode(), receipt["query_text"].encode()
        if historical["verification"]["checker_sha256"] == sha256(BINARY.read_bytes()).hexdigest():
            self.assertTrue(pilot.verify(raw, query, historical, checker=BINARY)["verified"])
        else:
            self.assert_rejected(lambda: pilot.verify(raw, query, historical, checker=BINARY), "ANSWER_REJECTED")

    def test_mocked_native_status_and_polarities_cannot_contradict_the_accepted_certificate(self):
        genuine = self.answer()["verification"]["native_receipt"]
        incoherent = deepcopy(genuine)
        incoherent["status"] = "REFUTED"
        coherent_but_false = deepcopy(genuine)
        coherent_but_false.update(status="REFUTED", positive=False, negative=True,
                                  clean_positive=False, clean_negative=True)
        for name, receipt in (("status-only", incoherent), ("coherent-but-false", coherent_but_false)):
            with self.subTest(mocked_receipt=name):
                process = SimpleNamespace(returncode=0, stdout=canonical(receipt).encode(), stderr=b"")
                with patch.object(pilot.subprocess, "run", return_value=process):
                    self.assert_rejected(lambda: self.answer(), "CHECKER_PROTOCOL_ERROR")

    def test_mocked_native_success_requires_exact_field_shape_and_boolean_types(self):
        genuine = self.answer()["verification"]["native_receipt"]
        mutations = [
            lambda r: r.update(positive=1),
            lambda r: r.update(clean_positive=1),
            lambda r: r.update(status=["SUPPORTED"]),
            lambda r: r.pop("scope"),
            lambda r: r.update(action_authority="AUTHORIZED"),
            lambda r: r.update(scope="all-external-worlds"),
        ]
        for number, mutate in enumerate(mutations):
            with self.subTest(mocked_receipt=number):
                receipt = deepcopy(genuine)
                mutate(receipt)
                process = SimpleNamespace(returncode=0, stdout=canonical(receipt).encode(), stderr=b"")
                with patch.object(pilot.subprocess, "run", return_value=process):
                    self.assert_rejected(lambda: self.answer(), "CHECKER_PROTOCOL_ERROR")

    def test_repeated_native_steps_keep_prior_witnesses_and_actual_derivation_edges(self):
        # Native replay admits repeated sound steps. This is an externally
        # supplied certificate control, not a new source-language feature.
        raw = "سالم هو عالم.\nإذا سالم هو عالم فإن سالم هو عالم.\n".encode()
        query = "هل سالم هو عالم؟\n".encode()
        certificate = pilot.propose_certificate(raw, query)
        for known, steps in (("known", "steps"), ("clean_known", "clean_steps")):
            certificate[known].extend([deepcopy(ATOMS["سالم هو عالم"]), deepcopy(ATOMS["سالم هو عالم"])])
            certificate[steps].extend([{"kind": "rule", "index": 0}, {"kind": "rule", "index": 0}])
        bundle = pilot.answer(raw, query, certificate=certificate, checker=BINARY)
        self.assertEqual(bundle["answer"]["status"], "SUPPORTED")
        operation = bundle["explanation"]["operations"][1]
        self.assertEqual(operation["required_premises"][0]["full_witness"], "f0")
        self.assertEqual(operation["required_premises"][0]["clean_witness"], "k0")
        self.assertEqual(operation["full_steps"], ["f1", "f2"])
        self.assertEqual(operation["clean_steps"], ["k1", "k2"])
        for theory, prefix in (("full", "f"), ("clean", "k")):
            trace = bundle["analysis_certificate"]["traces"][theory]
            self.assertEqual([node["premises"] for node in trace], [[], [prefix + "0"], [prefix + "1"]])
            self.assertEqual(bundle["explanation"]["targets"]["query"][theory + "_root"], prefix + "2")
            self.assertEqual(bundle["explanation"]["dependencies"][theory]["query"]["step_ids"],
                             [prefix + "0", prefix + "1", prefix + "2"])
        self.assertTrue(pilot.verify(raw, query, bundle, checker=BINARY)["verified"])

    def test_large_cli_answer_fits_its_own_reader_budget_and_replays(self):
        # Independent review reproduced the old pretty-JSON writer producing
        # 5,070,207 bytes from a valid 2,022,093-byte compact answer. Generate
        # the boundary input here; no multi-megabyte fixture is retained.
        atom = {"predicate": "p", "arguments": ["a"], "positive": True}
        clause = {"kind": "rule", "body": [deepcopy(atom) for _ in range(16)], "head": deepcopy(atom)}
        raw = ("إذا " + " و ".join(["a هو p"] * 16) + " فإن a هو p.\n").encode() * 256
        query = "هل a هو p؟\n".encode()
        self.assertEqual(len(raw), 54528)
        certificate = {
            "law_id": "nabt.verified-ground-reading.v1",
            "source": {"identity": "text", "revision": "1", "scope": "default", "text": raw.decode()},
            "query_text": query.decode(), "clauses": [deepcopy(clause) for _ in range(256)],
            "query": deepcopy(atom), "known": [], "steps": [], "clean_known": [], "clean_steps": [],
        }
        with tempfile.TemporaryDirectory() as temp:
            source_path, query_path, cert_path, answer_path = [Path(temp) / name for name in
                                                            ("source", "query", "certificate.json", "answer.json")]
            source_path.write_bytes(raw)
            query_path.write_bytes(query)
            cert_path.write_text(canonical(certificate), encoding="utf-8")
            process = subprocess.run([sys.executable, str(ROOT / "tools/explainable_pilot.py"), "answer",
                                      str(source_path), str(query_path), "--certificate", str(cert_path),
                                      "--output", str(answer_path), "--checker", str(BINARY),
                                      "--answer-version", "v2"], capture_output=True, text=True, timeout=60)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            output = answer_path.read_bytes()
            self.assertLessEqual(len(output), pilot.MAX_BUNDLE_BYTES)
            bundle = pilot.strict_json(output)
            self.assertEqual(bundle["answer"]["status"], "UNKNOWN")
            self.assertTrue(pilot.verify(raw, query, bundle, checker=BINARY, answer_version="v2")["verified"])


if __name__ == "__main__":
    unittest.main()
