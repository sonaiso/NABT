"""Independent lifecycle trust-boundary counterexamples, not acceptance gold.

All episodes below are synthetic protocol fixtures authored from the frozen
specification. This module never imports or reads the frozen forty scenarios.
The dedicated gate requires native tests; general Python-only discovery may
report their absence as a skip, without claiming native conformance.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from tools import evidence_lifecycle_v1 as lifecycle


LAW = "nabt.evidence-lifecycle.v1"
FLAGS = ("world_truth_established", "source_authenticity_established",
         "referents_established", "all_arabic_complete")


def episode():
    """One authored observation; the query is an unrelated declared origin."""
    query_source = {"identity": "question", "revision": "r1", "content": "Question."}
    record_source = {"identity": "record", "revision": "r1", "content": "Authored observation."}
    key = {"axis": "recorded_observation", "entity": "fixture", "predicate": "colour",
           "value": "blue", "unit": "category", "context": "synthetic", "time": "0",
           "place": "test"}
    return {"schema": "nabt.evidence-lifecycle.episode.v1", "episode_id": "boundary-example",
            "query": {"key": deepcopy(key), "positive": True, "origin": "q"},
            "active_sources": [deepcopy(query_source), deepcopy(record_source)],
            "origins": [{"id": "q", "parents": []}, {"id": "r", "parents": []}],
            "interpretations": [{"id": "w", "source": deepcopy(record_source),
                                 "key": deepcopy(key), "positive": True,
                                 "kind": "observation", "origin": "r", "ancestry": ["r"]}],
            "bindings": [{"origin_id": "q", "source": deepcopy(query_source), "rank": 0},
                         {"origin_id": "r", "source": deepcopy(record_source), "rank": 0}],
            "budget": 1, "updates": []}


def raw(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def change_record_content(value, content):
    for source in (value["active_sources"][1], value["bindings"][1]["source"],
                   value["interpretations"][0]["source"]):
        source["content"] = content


def whitespace_record(space, field, *, mixed=False):
    value = episode()
    text = space + "A" + space if mixed else space
    for source in (value["active_sources"][1], value["bindings"][1]["source"],
                   value["interpretations"][0]["source"]):
        source[field] = text
    return value


def update(value, event_id, kind, source=None):
    return {"event_id": event_id, "kind": kind,
            "source": deepcopy(source or value["active_sources"][1]),
            "replacement": None, "reason": "Synthetic boundary exercise."}


def supported_envelope(value):
    """Literal expected result for this one-record fixture without updates."""
    return {"law_id": LAW, "binding": deepcopy(value),
            "steps": [{"step": 0, "event_id": None,
                       "active_sources": deepcopy(value["active_sources"]),
                       "receipt": {"status": "SUPPORTED", "support_ids": ["w"],
                                   "refutation_ids": [], "selected_ids": ["w"]},
                       "dependency_ready_ids": ["w"], "dependency_blocked_ids": [],
                       "affected_ids": []}], **{field: False for field in FLAGS}}


def malformed_wire_cases():
    good = raw(episode())
    return [
        ("duplicate root decoded key", b'{"\\u0062udget":1,' + good[1:]),
        ("duplicate nested decoded key", good.replace(b'"rank":0', b'"rank":0,"\\u0072ank":0', 1)),
        ("float", good.replace(b'"budget":1', b'"budget":1.0')),
        ("exponent", good.replace(b'"budget":1', b'"budget":1e0')),
        ("negative zero", good.replace(b'"budget":1', b'"budget":-0')),
        ("NaN", good.replace(b'"budget":1', b'"budget":NaN')),
        ("trailing object", good + b'{}'),
        ("invalid UTF-8", good.replace(b'Question.', b'\xff')),
        ("UTF-8 encoded surrogate", good.replace(b'Question.', b'\xed\xa0\x80')),
        ("unpaired high surrogate", good.replace(b'Question.', b'\\ud800')),
        ("unpaired low surrogate", good.replace(b'Question.', b'\\udc00')),
    ]


def graph_counterexamples():
    """Mutations each violate a distinct declared graph invariant."""
    cases = []

    def add(label, mutate):
        value = episode()
        mutate(value)
        cases.append((label, value))

    add("unknown query", lambda x: x["query"].update(origin="missing"))
    add("unknown interpretation origin", lambda x: x["interpretations"][0].update(origin="missing"))
    add("unknown ancestor", lambda x: x["interpretations"][0]["ancestry"].append("missing"))
    add("unknown parent", lambda x: x["origins"][1]["parents"].append("missing"))
    add("duplicate origin", lambda x: x["origins"].append(deepcopy(x["origins"][1])))
    add("duplicate evidence", lambda x: x["interpretations"].append(deepcopy(x["interpretations"][0])))
    add("duplicate binding", lambda x: x["bindings"].append(deepcopy(x["bindings"][1])))
    add("missing binding", lambda x: x["bindings"].pop())
    add("extra binding", lambda x: x["bindings"].append(
        {"origin_id": "missing", "source": deepcopy(x["active_sources"][0]), "rank": 0}))
    add("duplicate ancestry", lambda x: x["interpretations"][0]["ancestry"].append("r"))
    add("self cycle", lambda x: x["origins"][1]["parents"].append("r"))
    add("equal parent rank", lambda x: x["origins"][1]["parents"].append("q"))
    value = episode()
    value["origins"][1]["parents"] = ["q", "q"]
    value["bindings"][1]["rank"] = 1
    cases.append(("duplicate parent", value))
    value = episode()
    for name, parent in (("cycle-a", "cycle-b"), ("cycle-b", "cycle-a")):
        value["origins"].append({"id": name, "parents": [parent]})
        value["bindings"].append({"origin_id": name,
                                  "source": {"identity": name, "revision": "1", "content": name},
                                  "rank": 2})
    cases.append(("disconnected closed cycle", value))
    return cases


class LifecycleWireBoundaryTests(unittest.TestCase):
    def test_strict_raw_wire_does_not_normalize_invalid_input(self):
        for label, encoded in malformed_wire_cases():
            with self.subTest(label=label), self.assertRaises(lifecycle.InputError) as error:
                lifecycle.strict_loads(encoded)
            self.assertNotIsInstance(error.exception, lifecycle.ResourceLimit)

    def test_transport_caps_are_distinct_from_malformed_numbers(self):
        good = raw(episode())
        too_large = (
            good.replace(b'"budget":1', b'"budget":9007199254740992'),
            good.replace(b'"budget":1', b'"budget":10000000000000000'),
            good.replace(b'"budget":1', b'"budget":-9007199254740992'),
            good.replace(b'"budget":1', b'"budget":-12345678901234567'),
            b'[' * 34 + b'0' + b']' * 34,
            b' ' * (1024 * 1024 + 1),
        )
        for encoded in too_large:
            with self.subTest(size=len(encoded)), self.assertRaises(lifecycle.ResourceLimit):
                lifecycle.strict_loads(encoded)

    def test_valid_supplementary_unicode_and_newlines_remain_exact(self):
        value = episode()
        change_record_content(value, "علامة 🙂\nSecond line.")
        escaped = json.dumps(value, ensure_ascii=True).encode()
        for encoded in (raw(value), escaped):
            decoded = lifecycle.strict_loads(encoded)
            self.assertEqual(decoded, value)
            lifecycle.validate_episode(decoded)
        with self.assertRaises(lifecycle.InputError):
            lifecycle.strict_loads('"\ud800"')

    def test_unicode_whitespace_alone_is_not_source_identity_or_content(self):
        for space in ("\u00a0", "\u2007", "\u3000"):
            for field in ("identity", "content"):
                value = whitespace_record(space, field)
                with self.subTest(codepoint=ord(space), field=field):
                    with self.assertRaises(lifecycle.InputError) as error:
                        lifecycle.validate_episode(value)
                    self.assertNotIsInstance(error.exception, lifecycle.ResourceLimit)

    def test_mixed_unicode_whitespace_is_preserved_not_trimmed(self):
        for space in ("\u00a0", "\u2007", "\u3000"):
            for field in ("identity", "content"):
                value = whitespace_record(space, field, mixed=True)
                with self.subTest(codepoint=ord(space), field=field):
                    self.assertEqual(lifecycle.strict_loads(raw(value)), value)
                    self.assertEqual(lifecycle.validate_episode(value), value)

    def test_naturals_and_polarities_keep_exact_types(self):
        for field in ("budget", "rank"):
            for bad in (True, False, 1.0, "1", -1, None):
                value = episode()
                target = value if field == "budget" else value["bindings"][1]
                target[field] = bad
                with self.subTest(field=field, bad=bad), self.assertRaises(lifecycle.InputError) as error:
                    lifecycle.validate_episode(value)
                self.assertNotIsInstance(error.exception, lifecycle.ResourceLimit)
        for target in ("query", "interpretation"):
            for bad in (0, 1, "true", None):
                value = episode()
                row = value["query"] if target == "query" else value["interpretations"][0]
                row["positive"] = bad
                with self.subTest(target=target, bad=bad), self.assertRaises(lifecycle.InputError):
                    lifecycle.validate_episode(value)

    def test_time_string_keeps_existing_em_domain(self):
        for bad in (0, False, "-0", "00", "+1", "1e0", "9007199254740992"):
            value = episode()
            value["query"]["key"]["time"] = bad
            with self.subTest(bad=bad), self.assertRaises(lifecycle.InputError) as error:
                lifecycle.validate_episode(value)
            self.assertNotIsInstance(error.exception, lifecycle.ResourceLimit)
        for valid in ("0", "-1", "9007199254740991", "-9007199254740991"):
            value = episode()
            value["query"]["key"]["time"] = valid
            lifecycle.validate_episode(value)

    def test_actual_utf8_bytes_control_source_content_limit(self):
        value = episode()
        change_record_content(value, "🙂" * 4096)
        lifecycle.validate_episode(value)  # Exactly 16 KiB, not 16K codepoints.
        change_record_content(value, "🙂" * 4096 + "x")
        with self.assertRaises(lifecycle.ResourceLimit):
            lifecycle.validate_episode(value)

    def test_rank_budget_event_and_collection_caps(self):
        for field in ("rank", "budget"):
            value = episode()
            target = value if field == "budget" else value["bindings"][1]
            target[field] = 64
            lifecycle.validate_episode(value)
            target[field] = 65
            with self.subTest(field=field), self.assertRaises(lifecycle.ResourceLimit):
                lifecycle.validate_episode(value)
        value = episode()
        value["updates"] = [update(value, str(i), "activate") for i in range(16)]
        lifecycle.validate_episode(value)
        value["updates"].append(update(value, "17", "activate"))
        with self.assertRaises(lifecycle.ResourceLimit):
            lifecycle.validate_episode(value)
        value = episode()
        value["interpretations"] = [dict(deepcopy(value["interpretations"][0]), id=f"w-{i}")
                                    for i in range(64)]
        value["budget"] = 64
        lifecycle.validate_episode(value)
        value["interpretations"].append(dict(deepcopy(value["interpretations"][0]), id="overflow"))
        with self.assertRaises(lifecycle.ResourceLimit):
            lifecycle.validate_episode(value)

    def test_extra_authority_fields_are_not_silently_ignored(self):
        for target in ("episode", "query", "key", "source", "binding", "origin", "evidence", "update"):
            value = episode()
            value["updates"] = [update(value, "e", "activate")]
            row = {"episode": value, "query": value["query"], "key": value["query"]["key"],
                   "source": value["active_sources"][0], "binding": value["bindings"][0],
                   "origin": value["origins"][0], "evidence": value["interpretations"][0],
                   "update": value["updates"][0]}[target]
            row["verified"] = True
            with self.subTest(target=target), self.assertRaises(lifecycle.InputError):
                lifecycle.validate_episode(value)

    def test_graph_invalidity_is_not_an_unknown_verdict(self):
        for label, value in graph_counterexamples():
            with self.subTest(label=label), self.assertRaises(lifecycle.InputError) as error:
                lifecycle.validate_episode(value)
            self.assertNotIsInstance(error.exception, lifecycle.ResourceLimit)

    def test_initial_inactive_binding_content_collision_is_rejected(self):
        value = episode()
        value["active_sources"] = []
        value["interpretations"] = []
        value["origins"].append({"id": "alias", "parents": []})
        forged = deepcopy(value["bindings"][1]["source"])
        forged["content"] = "Different bytes under the SAME identity and revision."
        value["bindings"].append({"origin_id": "alias", "source": forged, "rank": 0})
        with self.assertRaises(lifecycle.InputError):
            lifecycle.validate_episode(value)

    def test_missing_parent_closure_is_blocked_not_invalid(self):
        value = episode()
        value["origins"][1]["parents"] = ["q"]
        value["bindings"][1]["rank"] = 1
        lifecycle.validate_episode(value)
        result = lifecycle.propose_episode(value)
        self.assertEqual(result["steps"][0]["receipt"]["status"], "UNKNOWN")
        self.assertEqual(result["steps"][0]["dependency_blocked_ids"], ["w"])


class LifecycleNativeBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requirement = os.environ.get("NABT_REQUIRE_EVIDENCE_LIFECYCLE_NATIVE", "")
        if requirement not in ("", "1"):
            raise AssertionError("NABT_REQUIRE_EVIDENCE_LIFECYCLE_NATIVE must be unset or 1")
        if not lifecycle.NATIVE.is_file():
            if requirement == "1":
                raise AssertionError("Required evidenceLifecycleV1 executable is absent; this is not a passing skip")
            raise unittest.SkipTest("native lifecycle boundaries require the dedicated lifecycle conformance gate")

    def call_raw(self, encoded):
        completed = subprocess.run([str(lifecycle.NATIVE)], input=encoded + b"\n",
                                   capture_output=True, check=False, timeout=30)
        self.assertIn(completed.returncode, (0, 2), completed.stderr[:1000])
        self.assertEqual(completed.stderr, b"")
        self.assertLessEqual(len(completed.stdout), 8 * 1024 * 1024)
        result = json.loads(completed.stdout.decode("utf-8"))
        if "binding" in result:
            self.assertEqual(completed.returncode, 0)
        return result

    def assert_native_error(self, encoded, status):
        result = self.call_raw(encoded)
        self.assertEqual(set(result), {"law_id", "status", "reason", *FLAGS})
        self.assertEqual(result["law_id"], LAW)
        self.assertEqual(result["status"], status)
        self.assertIs(type(result["reason"]), str)
        self.assertTrue(result["reason"])
        for field in FLAGS:
            self.assertIs(result[field], False)

    def test_native_direct_wire_rejects_decoded_duplicates_numbers_and_bad_utf8(self):
        for label, encoded in malformed_wire_cases():
            with self.subTest(label=label):
                self.assert_native_error(encoded, "INVALID_INPUT")

    def test_native_direct_graph_counterexamples(self):
        for label, value in graph_counterexamples():
            with self.subTest(label=label):
                self.assert_native_error(raw(value), "INVALID_INPUT")

    def test_native_initial_bindings_cannot_hide_a_content_collision(self):
        value = episode()
        value["active_sources"] = []
        value["interpretations"] = []
        value["origins"].append({"id": "alias", "parents": []})
        source = deepcopy(value["bindings"][1]["source"])
        source["content"] = "Collision in initial inactive bindings only."
        value["bindings"].append({"origin_id": "alias", "source": source, "rank": 0})
        self.assert_native_error(raw(value), "INVALID_INPUT")

    def test_native_caps_and_time_domain_keep_distinct_error_classes(self):
        good = raw(episode())
        for encoded in (good.replace(b'"budget":1', b'"budget":9007199254740992'),
                        good.replace(b'"budget":1', b'"budget":10000000000000000'),
                        good.replace(b'"budget":1', b'"budget":-9007199254740992'),
                        good.replace(b'"budget":1', b'"budget":-12345678901234567'),
                        good.replace(b'"budget":1', b'"budget":65'),
                        b'[' * 34 + b'0' + b']' * 34,
                        b' ' * (1024 * 1024 + 1)):
            with self.subTest(size=len(encoded)):
                self.assert_native_error(encoded, "RESOURCE_LIMIT")
        for bad in (True, False, -1, "1"):
            value = episode()
            value["budget"] = bad
            with self.subTest(budget=bad):
                self.assert_native_error(raw(value), "INVALID_INPUT")
        value = episode()
        value["query"]["key"]["time"] = "9007199254740992"
        self.assert_native_error(raw(value), "INVALID_INPUT")

    def test_native_report_cap_rejects_whole_episode_without_partial_history(self):
        value = episode()
        # Under 1 MiB input, but 17 complete active-source snapshots exceed 8 MiB.
        value["active_sources"].extend(
            {"identity": f"payload-{i}", "revision": "1", "content": "x" * 16384}
            for i in range(32))
        value["updates"] = [update(value, str(i), "activate") for i in range(16)]
        self.assertLess(len(raw(value)), 1024 * 1024)
        lifecycle.validate_episode(value)
        self.assert_native_error(raw(value), "RESOURCE_LIMIT")

    def test_native_positive_control_checks_literal_single_record_expectation(self):
        value = episode()
        self.assertEqual(self.call_raw(raw(value)), supported_envelope(value))

    def test_native_preserves_supplementary_unicode_with_both_json_spellings(self):
        value = episode()
        change_record_content(value, "علامة 🙂\nSecond line.")
        for encoded in (raw(value), json.dumps(value, ensure_ascii=True).encode()):
            result = self.call_raw(encoded)
            self.assertEqual(result, supported_envelope(value))

    def test_native_unicode_whitespace_alone_is_invalid(self):
        for space in ("\u00a0", "\u2007", "\u3000"):
            for field in ("identity", "content"):
                with self.subTest(codepoint=ord(space), field=field):
                    self.assert_native_error(raw(whitespace_record(space, field)), "INVALID_INPUT")

    def test_native_mixed_unicode_whitespace_remains_exact(self):
        for space in ("\u00a0", "\u2007", "\u3000"):
            for field in ("identity", "content"):
                value = whitespace_record(space, field, mixed=True)
                with self.subTest(codepoint=ord(space), field=field):
                    self.assertEqual(self.call_raw(raw(value)), supported_envelope(value))

    def test_unavailable_or_disagreeing_native_cannot_authorize_a_receipt(self):
        value = episode()
        with patch.object(lifecycle, "NATIVE", Path("/missing-lifecycle-boundary-executable")):
            absent = lifecycle.evaluate_episode(value)
        self.assertEqual(absent["status"], "UNMEASURED")
        self.assertIs(absent["native_checked"], False)
        self.assertIs(absent["decision_complete"], False)
        self.assertIsNone(absent["observed"])
        fake = supported_envelope(value)
        fake["steps"][0]["receipt"]["selected_ids"] = []
        with patch.object(lifecycle, "_native", return_value=fake):
            mismatch = lifecycle.evaluate_episode(value)
        self.assertIs(mismatch["native_checked"], False)
        self.assertIs(mismatch["decision_complete"], False)
        self.assertIsNone(mismatch["observed"])
        self.assertTrue(mismatch["execution"]["error"])

    def test_native_bool_int_substitutions_are_disagreement_not_equal(self):
        for target in ("step", "rank", "flag"):
            value = episode()
            fake = supported_envelope(value)
            if target == "step":
                fake["steps"][0]["step"] = False
            elif target == "rank":
                fake["binding"]["bindings"][0]["rank"] = False
            else:
                fake[FLAGS[0]] = 0
            with self.subTest(target=target), patch.object(lifecycle, "_native", return_value=fake):
                result = lifecycle.evaluate_episode(value)
            self.assertIs(result["native_checked"], False)
            self.assertIsNone(result["observed"])

    def test_timeout_does_not_become_an_unknown_complete_decision(self):
        with patch.object(lifecycle, "_native", side_effect=subprocess.TimeoutExpired("fixture", 30)):
            result = lifecycle.evaluate_episode(episode())
        self.assertIs(result["native_checked"], False)
        self.assertIs(result["decision_complete"], False)
        self.assertIsNone(result["observed"])
        self.assertIn("TIMEOUT", str(result["execution"]["error"]).upper())

    def test_stale_receipt_fails_despite_same_episode_id_and_final_state(self):
        original = episode()
        later = deepcopy(original)
        later["updates"] = [update(later, "withdraw-record", "withdraw"),
                            update(later, "restore-record", "activate")]
        old = lifecycle.evaluate_episode(original)
        new = lifecycle.evaluate_episode(later)
        self.assertIs(old["native_checked"], True, old)
        self.assertIs(new["native_checked"], True, new)
        self.assertEqual(old["observed"]["steps"][-1]["active_sources"],
                         new["observed"]["steps"][-1]["active_sources"])
        self.assertEqual(old["observed"]["steps"][-1]["receipt"],
                         new["observed"]["steps"][-1]["receipt"])
        self.assertIs(lifecycle.verify_episode(old, expected_episode=original)["valid"], True)
        stale = lifecycle.verify_episode(old, expected_episode=later)
        self.assertIs(stale["valid"], False)
        self.assertIs(stale["replay_matches"], False)
        self.assertIs(lifecycle.verify_episode(new, expected_episode=later)["valid"], True)

    def test_receipt_verification_does_not_treat_false_as_step_zero(self):
        value = episode()
        report = lifecycle.evaluate_episode(value)
        self.assertIs(report["native_checked"], True, report)
        report["observed"]["steps"][0]["step"] = False
        checked = lifecycle.verify_episode(report, expected_episode=value)
        self.assertIs(checked["valid"], False)
        self.assertIs(checked["replay_matches"], False)


class NativeReadinessPolicyTests(unittest.TestCase):
    def test_python_only_discovery_reports_unavailable_native_without_authority(self):
        with patch.object(lifecycle, "NATIVE") as native, patch.dict(
                os.environ, {"NABT_REQUIRE_EVIDENCE_LIFECYCLE_NATIVE": ""}):
            native.is_file.return_value = False
            with self.assertRaises(unittest.SkipTest):
                LifecycleNativeBoundaryTests.setUpClass()

    def test_required_gate_cannot_skip_an_absent_native(self):
        with patch.object(lifecycle, "NATIVE") as native, patch.dict(
                os.environ, {"NABT_REQUIRE_EVIDENCE_LIFECYCLE_NATIVE": "1"}):
            native.is_file.return_value = False
            with self.assertRaisesRegex(AssertionError, "Required evidenceLifecycleV1"):
                LifecycleNativeBoundaryTests.setUpClass()

    def test_unknown_readiness_setting_is_not_a_soft_fallback(self):
        with patch.dict(os.environ, {"NABT_REQUIRE_EVIDENCE_LIFECYCLE_NATIVE": "typo"}):
            with self.assertRaisesRegex(AssertionError, "must be unset or 1"):
                LifecycleNativeBoundaryTests.setUpClass()


if __name__ == "__main__":
    unittest.main()
