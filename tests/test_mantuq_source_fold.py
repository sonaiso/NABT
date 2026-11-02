"""Adversarial transport/replay checks for the source-bound consequence packet.

Wire mutations recompute their hashes, so an old checksum is not the oracle.
Semantic cases use the real native owners; only execution-boundary assertions
use mocks. These tests grant no authority to successfully decoded data.
"""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import explainable_pilot as pilot
from tools.mantuq_inference import EvaluationBudget, source_bound, source_fold


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "evidence/mantuq_source_fold_v1/acceptance_contract.json").read_text())
CASES = {row["id"]: row for row in CONTRACT["cases"]}
QUERY = CONTRACT["query"].encode()
BINARY = Path(os.environ.get("NABT_VERIFIED_READING", ROOT / "formal/.lake/build/bin/verifiedReading"))
SEMANTIC = Path(os.environ.get("NABT_CLASSICAL_SEMANTIC_PROBE", ROOT / "formal/.lake/build/bin/classicalSemanticProbe"))
NATIVE_AVAILABLE = all(path.is_file() and os.access(path, os.X_OK) for path in (BINARY, SEMANTIC))
if os.environ.get("NABT_REQUIRE_MANTUQ_SOURCE_FOLD_NATIVE") == "1" and not NATIVE_AVAILABLE:
    raise RuntimeError("NABT_REQUIRE_MANTUQ_SOURCE_FOLD_NATIVE=1 requires executable verifiedReading and classicalSemanticProbe")
FOLD_SCHEMA = "nabt.mantuq-source-fold.v1"
FOLD_DOMAIN = "nabt.mantuq-source.canonical-json-utf8.sentinel256.v1"
PAYLOAD_SCHEMA = "nabt.mantuq-source-fold-payload.v1"
MAX_PAYLOAD_BYTES = 8 * 1048576


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def fixture(name="clean_explicit_requirements"):
    case = CASES[name]
    return case["source"].encode(), {"schema": "nabt.mantuq-source-plan.v1", "policy_id": "guarded_cause",
        "requirements": deepcopy(CONTRACT["requirements"]), "bridge_clause": case["bridge_clause"]}


def options(**changed):
    return dict({"source_id": "fixture", "revision": "1", "scope": "s", "context": "speaker=salim",
                 "time": "t1", "timeout": 20, "checker": BINARY, "semantic_probe": SEMANTIC}, **changed)


def envelope_for_bytes(raw):
    # This encoder is solely an adversarial fixture builder: it does not call
    # the production fold operation or decide whether a payload is valid.
    return {"schema": FOLD_SCHEMA, "domain": FOLD_DOMAIN,
            "number_hex": hex(int.from_bytes(b"\x01" + raw, "big")),
            "payload_sha256": sha256(raw).hexdigest(), "authority": "TRANSPORT_ONLY",
            "requires_source_replay": True}


def envelope_for_result(result, **wrapper_changes):
    wrapper = dict({"schema": PAYLOAD_SCHEMA, "domain": FOLD_DOMAIN, "result": result}, **wrapper_changes)
    return envelope_for_bytes(canonical(wrapper))


class FoldInputContract(unittest.TestCase):
    def test_malformed_envelope_has_no_implicit_domain_or_authority(self):
        base = {"schema": FOLD_SCHEMA, "domain": FOLD_DOMAIN, "number_hex": "0x1",
                "payload_sha256": "0" * 64, "authority": "TRANSPORT_ONLY", "requires_source_replay": True}
        for changed in (None, [], {}, dict(base, domain="nabt.program.canonical-json-utf8.sentinel256.v1"),
                        dict(base, schema=True), dict(base, authority="TRUTH"),
                        dict(base, requires_source_replay=1), dict(base, approved=True)):
            with self.subTest(envelope=changed), self.assertRaises(pilot.PilotError):
                source_fold.unfold_source(changed)

    def test_oversized_number_is_a_resource_failure(self):
        envelope = {"schema": FOLD_SCHEMA, "domain": FOLD_DOMAIN,
                    "number_hex": "0x1" + "00" * (MAX_PAYLOAD_BYTES + 1),
                    "payload_sha256": "0" * 64, "authority": "TRANSPORT_ONLY",
                    "requires_source_replay": True}
        with self.assertRaises(pilot.PilotError) as caught:
            source_fold.unfold_source(envelope)
        self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")


@unittest.skipUnless(NATIVE_AVAILABLE, "build both native checkers; native source-fold acceptance requires both")
class SourceFoldNativeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.plan = fixture()
        cls.envelope = source_fold.fold_source(cls.raw, QUERY, cls.plan, **options())
        cls.payload = source_fold.unfold_source(cls.envelope)

    def test_exact_full_packet_roundtrip_and_native_replay(self):
        self.assertEqual(set(self.envelope), {"schema", "domain", "number_hex", "payload_sha256",
                                             "authority", "requires_source_replay"})
        self.assertEqual(self.envelope["schema"], FOLD_SCHEMA)
        self.assertEqual(self.envelope["domain"], FOLD_DOMAIN)
        self.assertEqual(self.envelope["authority"], "TRANSPORT_ONLY")
        self.assertIs(self.envelope["requires_source_replay"], True)
        expected = source_bound.evaluate_source(self.raw, QUERY, self.plan, **options())
        self.assertEqual(canonical(self.payload), canonical(expected))
        wrapper = canonical({"schema": PAYLOAD_SCHEMA, "domain": FOLD_DOMAIN, "result": expected})
        self.assertEqual(self.envelope["payload_sha256"], sha256(wrapper).hexdigest())
        self.assertEqual(self.envelope["number_hex"], hex(int.from_bytes(b"\x01" + wrapper, "big")))
        replay = source_fold.verify_fold(self.raw, QUERY, self.plan, self.envelope, **options())
        self.assertEqual(replay["schema"], "nabt.mantuq-source-replay.v1")
        self.assertEqual(replay["status"], "VERIFIED_REPLAY")
        self.assertIs(replay["verified"], True)
        self.assertIs(replay["conditional_consequence"], True)
        self.assertIs(replay["world_truth_established"], False)
        self.assertIs(replay["all_arabic_complete"], False)
        self.assertEqual(replay["action_authority"], "NONE")

    def test_unfold_is_data_only_and_does_not_invoke_native(self):
        with patch("subprocess.run", side_effect=AssertionError("unfold executed native")):
            restored = source_fold.unfold_source(self.envelope)
        self.assertEqual(canonical(restored), canonical(self.payload))

    def test_all_checked_semantic_states_can_be_transported(self):
        cases = {"clean_explicit_requirements": "SUPPORTED", "absent_negative_blocker_witness": "UNKNOWN",
                 "blocker_present": "REFUTED", "blocker_conflict": "CONFLICT",
                 "derived_tainted_requirement": "DEFER"}
        for name, expected in cases.items():
            with self.subTest(case=name):
                raw, plan = fixture(name)
                envelope = source_fold.fold_source(raw, QUERY, plan, **options())
                result = source_fold.unfold_source(envelope)
                self.assertEqual(result["status"], expected)
                self.assertIs(result["conditional_consequence"], expected == "SUPPORTED")
                replay = source_fold.verify_fold(raw, QUERY, plan, envelope, **options())
                self.assertIs(replay["verified"], True)
                self.assertIs(replay["conditional_consequence"], expected == "SUPPORTED")

    def test_numeric_spelling_framing_and_booleans_are_not_aliases(self):
        good = self.envelope["number_hex"]
        invalid = (True, 1, None, "", "0x0", "0x0" + good[2:], "0X" + good[2:],
                   good.upper(), " " + good, good + " ", "-" + good,
                   hex(int.from_bytes(b"\x02" + canonical({"domain": FOLD_DOMAIN}), "big")))
        for value in invalid:
            with self.subTest(number=value if not isinstance(value, str) else value[:35]), self.assertRaises(pilot.PilotError):
                source_fold.unfold_source(dict(self.envelope, number_hex=value))

    def test_inner_domain_and_schema_cannot_be_relabelled(self):
        for changes in ({"domain": "nabt.program.canonical-json-utf8.sentinel256.v1"},
                        {"schema": "nabt.mantuq-source-fold-payload.v2"}, {"schema": True}):
            with self.subTest(changes=changes), self.assertRaises(pilot.PilotError):
                source_fold.unfold_source(envelope_for_result(self.payload, **changes))

    def test_noncanonical_payload_spellings_and_duplicate_decoded_keys_are_rejected(self):
        wrapper = {"schema": PAYLOAD_SCHEMA, "domain": FOLD_DOMAIN, "result": self.payload}
        good = canonical(wrapper)
        duplicate = good[:-1] + b',"\\u0073chema":"' + PAYLOAD_SCHEMA.encode() + b'"}'
        minus_zero = good.replace(b'"index":0', b'"index":-0', 1)
        self.assertNotEqual(minus_zero, good)
        mutations = (good + b" ", json.dumps(wrapper, ensure_ascii=False, indent=2).encode(),
                     json.dumps(wrapper, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode(),
                     duplicate, minus_zero, good.replace(b'"index":0', b'"index":0.0', 1),
                     good.replace(b'"index":0', b'"index":0e0', 1), b"\xff", b'{"bad":"\\ud800"}')
        for raw in mutations:
            with self.subTest(prefix=raw[:45]), self.assertRaises(pilot.PilotError):
                source_fold.unfold_source(envelope_for_bytes(raw))

    def test_deep_payload_is_a_resource_failure(self):
        deep = b"[" * 35 + b"0" + b"]" * 35
        with self.assertRaises(pilot.PilotError) as caught:
            source_fold.unfold_source(envelope_for_bytes(deep))
        self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")

    def test_self_consistent_payload_tampering_fails_against_native_replay(self):
        changed = []
        value = deepcopy(self.payload); value["conditional_consequence"] = 1; changed.append(value)
        value = deepcopy(self.payload); value["status"] = "WORLD_TRUE"; changed.append(value)
        value = deepcopy(self.payload); value["limits"]["world_truth_established"] = True; changed.append(value)
        value = deepcopy(self.payload); value["limits"]["rule_adoption_established"] = True; changed.append(value)
        value = deepcopy(self.payload); value["limits"]["action_authority"] = "GRANTED"; changed.append(value)
        value = deepcopy(self.payload)
        value["source_answer"]["verification"]["checker_sha256"] = "0" * 64
        changed.append(value)
        for value in changed:
            with self.subTest(status=value["status"]), self.assertRaises(pilot.PilotError) as caught:
                source_fold.verify_fold(self.raw, QUERY, self.plan, envelope_for_result(value), **options())
            self.assertEqual(caught.exception.code, "FOLD_REJECTED")

    def test_conflict_and_taint_cannot_be_edited_out_of_the_transported_certificate(self):
        for name in ("blocker_conflict", "derived_tainted_requirement"):
            raw, plan = fixture(name)
            payload = source_fold.unfold_source(source_fold.fold_source(raw, QUERY, plan, **options()))
            cert = payload["source_answer"]["analysis_certificate"]["kernel_certificate"]
            if name == "blocker_conflict":
                cert["known"] = [a for a in cert["known"] if not (a["predicate"] == "مانع" and a["positive"])]
            else:
                cert["clean_known"] = deepcopy(cert["known"])
            payload["conditional_consequence"] = True
            payload["status"] = "SUPPORTED"
            with self.subTest(case=name), self.assertRaises(pilot.PilotError) as caught:
                source_fold.verify_fold(raw, QUERY, plan, envelope_for_result(payload), **options())
            self.assertEqual(caught.exception.code, "FOLD_REJECTED")

    def test_consistent_request_substitution_is_rejected_by_independent_inputs(self):
        different_raw = self.raw.replace("سالم".encode(), "زيد".encode())
        different_query = QUERY.replace("سالم".encode(), "زيد".encode())
        different_plan = deepcopy(self.plan)
        for requirement in different_plan["requirements"]:
            requirement["atom"]["arguments"] = ["زيد"]
        replacement = source_fold.fold_source(different_raw, different_query, different_plan, **options())
        with self.assertRaises(pilot.PilotError) as caught:
            source_fold.verify_fold(self.raw, QUERY, self.plan, replacement, **options())
        self.assertEqual(caught.exception.code, "FOLD_REJECTED")
        missing_plan = dict(deepcopy(self.plan), bridge_clause=None)
        replacement = source_fold.fold_source(self.raw, QUERY, missing_plan, **options())
        with self.assertRaises(pilot.PilotError) as caught:
            source_fold.verify_fold(self.raw, QUERY, self.plan, replacement, **options())
        self.assertEqual(caught.exception.code, "FOLD_REJECTED")

    def test_binding_context_revision_and_time_are_independently_required(self):
        for field, value in (("source_id", "other"), ("revision", "2"), ("scope", "other"),
                             ("context", "speaker=other"), ("time", "t2")):
            with self.subTest(field=field), self.assertRaises(pilot.PilotError) as caught:
                source_fold.verify_fold(self.raw, QUERY, self.plan, self.envelope, **options(**{field: value}))
            self.assertEqual(caught.exception.code, "FOLD_REJECTED")

    def test_withdrawal_preserves_decodability_but_rejects_stale_authority(self):
        old_raw, old_plan = fixture("clean_alternative_to_tainted_requirement")
        old = source_fold.fold_source(old_raw, QUERY, old_plan, **options())
        new_raw, new_plan = fixture("derived_tainted_requirement")
        self.assertEqual(source_fold.unfold_source(old)["status"], "SUPPORTED")
        with self.assertRaises(pilot.PilotError) as caught:
            source_fold.verify_fold(new_raw, QUERY, new_plan, old, **options(revision="2"))
        self.assertEqual(caught.exception.code, "FOLD_REJECTED")
        fresh = source_fold.fold_source(new_raw, QUERY, new_plan, **options(revision="2"))
        self.assertEqual(source_fold.unfold_source(fresh)["status"], "DEFER")

    def test_changed_budget_is_not_hidden_by_an_identical_semantic_answer(self):
        seven = source_fold.fold_source(self.raw, QUERY, self.plan, **options(timeout=7))
        self.assertEqual(source_fold.unfold_source(seven)["budget"]["native_timeout_seconds"], 7)
        with self.assertRaises(pilot.PilotError) as caught:
            source_fold.verify_fold(self.raw, QUERY, self.plan, seven, **options(timeout=8))
        self.assertEqual(caught.exception.code, "FOLD_REJECTED")
        with self.assertRaises(pilot.PilotError):
            source_fold.verify_fold(self.raw, QUERY, self.plan, self.envelope,
                                    **options(budget=EvaluationBudget(max_readings=0)))

    def test_technical_failures_cannot_be_folded_or_verified_as_success(self):
        for changed in ({"checker": "/missing-native-checker"}, {"timeout": 7.5},
                        {"budget": EvaluationBudget(max_readings=0)}):
            with self.subTest(options=changed):
                with self.assertRaises(pilot.PilotError):
                    source_fold.fold_source(self.raw, QUERY, self.plan, **options(**changed))
                with self.assertRaises(pilot.PilotError):
                    source_fold.verify_fold(self.raw, QUERY, self.plan, self.envelope, **options(**changed))

    def cli(self, *arguments):
        return subprocess.run([sys.executable, "-m", "tools.mantuq_inference", *map(str, arguments)],
                              cwd=ROOT, capture_output=True, text=True, timeout=60)

    def cli_inputs(self, directory, *, raw=None, plan=None):
        paths = {name: Path(directory) / (name + ".json" if name in {"plan", "packet"} else name + ".txt")
                 for name in ("source", "query", "plan", "packet")}
        paths["source"].write_bytes(self.raw if raw is None else raw)
        paths["query"].write_bytes(QUERY)
        paths["plan"].write_bytes(canonical(self.plan if plan is None else plan))
        paths["packet"].write_bytes(canonical(self.envelope))
        return paths

    def cli_options(self, *, checker=None):
        return ["--source-id", "fixture", "--revision", "1", "--scope", "s", "--context", "speaker=salim",
                "--time", "t1", "--timeout", "20", "--checker", str(BINARY if checker is None else checker),
                "--semantic-probe", str(SEMANTIC)]

    def test_cli_existing_output_is_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.cli_inputs(temp)
            output = Path(temp) / "existing.json"
            original = b"keep existing user bytes\n"
            output.write_bytes(original)
            folded = self.cli("fold", paths["source"], paths["query"], "--plan", paths["plan"],
                              "--output", output, *self.cli_options())
            self.assertNotEqual(folded.returncode, 0)
            self.assertEqual(output.read_bytes(), original)
            decoded = self.cli("unfold", paths["packet"], "--output", output)
            self.assertNotEqual(decoded.returncode, 0)
            self.assertEqual(output.read_bytes(), original)

    def test_cli_zero_budget_is_resource_exhaustion_and_writes_no_fold(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.cli_inputs(temp)
            result = self.cli("source", paths["source"], paths["query"], "--plan", paths["plan"],
                              "--max-readings", "0", *self.cli_options())
            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "RESOURCE_EXHAUSTED")
            self.assertIs(report["conditional_consequence"], False)
            output = Path(temp) / "not_created.json"
            folded = self.cli("fold", paths["source"], paths["query"], "--plan", paths["plan"],
                              "--max-readings", "0", "--output", output, *self.cli_options())
            self.assertNotEqual(folded.returncode, 0)
            self.assertFalse(output.exists())

    def test_cli_unavailable_checker_is_distinct_from_checked_unknown(self):
        raw, plan = fixture("absent_negative_blocker_witness")
        with tempfile.TemporaryDirectory() as temp:
            paths = self.cli_inputs(temp, raw=raw, plan=plan)
            checked = self.cli("source", paths["source"], paths["query"], "--plan", paths["plan"],
                               *self.cli_options())
            self.assertEqual(checked.returncode, 0, checked.stderr + checked.stdout)
            report = json.loads(checked.stdout)
            self.assertEqual(report["status"], "UNKNOWN")
            self.assertIs(report["conditional_consequence"], False)
            missing = self.cli("source", paths["source"], paths["query"], "--plan", paths["plan"],
                               *self.cli_options(checker="/missing-native-checker"))
            self.assertNotEqual(missing.returncode, 0)
            report = json.loads(missing.stdout)
            self.assertEqual(report["status"], "VERIFICATION_UNAVAILABLE")
            self.assertIs(report["conditional_consequence"], False)

    def test_cli_verify_requires_independent_revision_plan_and_query(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.cli_inputs(temp)
            arguments = ["verify-fold", paths["source"], paths["query"], paths["packet"],
                         "--plan", paths["plan"], *self.cli_options()]
            checked = self.cli(*arguments)
            self.assertEqual(checked.returncode, 0, checked.stderr + checked.stdout)
            self.assertIs(json.loads(checked.stdout)["verified"], True)
            for kind in ("revision", "plan", "query"):
                paths["query"].write_bytes(QUERY)
                paths["plan"].write_bytes(canonical(self.plan))
                changed = list(arguments)
                if kind == "revision":
                    changed[changed.index("--revision") + 1] = "2"
                elif kind == "plan":
                    paths["plan"].write_bytes(canonical(dict(self.plan, bridge_clause=None)))
                else:
                    paths["query"].write_bytes("هل سالم هو مختلف؟\n".encode())
                result = self.cli(*changed)
                with self.subTest(change=kind):
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIsNot(json.loads(result.stdout).get("verified"), True)


if __name__ == "__main__":
    unittest.main()
