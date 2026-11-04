"""Source-only integration oracles; expected answers are never runtime inputs."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import source_learning_connection as c

ROOT = Path(__file__).resolve().parents[1]
NATIVE_READY = all((ROOT / "formal/.lake/build/bin" / n).is_file()
                   for n in ("verifiedReading", "evidenceLifecycleV1"))


def request(sources=None, query="هل نادر هو إنسان؟", events=()):
    if sources is None:
        sources = {"positive": "سالم هو عالم. سالم هو إنسان.",
                   "negative": "ليس حجر هو عالم. ليس حجر هو إنسان.",
                   "law": "كل عالم هو إنسان.", "case": "نادر هو عالم."}
    return {"schema": c.REQUEST_SCHEMA, "scope": "trial",
            "sources": [{"id": k, "text": v, "parents": []} for k, v in sources.items()],
            "query": query, "initial_active": list(sources), "events": list(events)}


def event(kind, target, identity=None):
    return {"id": identity or kind + "_" + target, "kind": kind, "target": target}


class InputTests(unittest.TestCase):
    def test_no_feature_label_or_answer_injection(self):
        for field in ("features", "label", "answer", "selected_reading", "rule"):
            value = request()
            value[field] = True
            with self.subTest(field=field):
                self.assertEqual(c.evaluate(value)["status"], "INVALID_INPUT")
        value = request()
        value["sources"][0]["label"] = True
        self.assertEqual(c.evaluate(value)["status"], "INVALID_INPUT")

    def test_duplicate_unknown_and_cyclic_sources(self):
        values = []
        duplicate = request(); duplicate["sources"].append(duplicate["sources"][0]); values.append(duplicate)
        unknown = request(); unknown["sources"][0]["parents"] = ["missing"]; values.append(unknown)
        cycle = request(); cycle["sources"][0]["parents"] = ["positive"]; values.append(cycle)
        initial = request(); initial["initial_active"] = ["missing"]; values.append(initial)
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(c.evaluate(value)["status"], "INVALID_INPUT")

    def test_event_validation_and_unknown_not_negative(self):
        for events in ([event("replace", "law")], [event("withdraw", "missing")],
                       [event("withdraw", "law"), event("withdraw", "law")]):
            self.assertEqual(c.evaluate(request(events=events))["status"], "INVALID_INPUT")
        bad = request({"source": "جملة حرة غير مفسرة."})
        result = c.evaluate(bad)
        self.assertEqual(result["status"], "DEFER")
        self.assertFalse(result["chain_complete"])
        self.assertTrue(result["source_failure"]["residuals"])

    def test_source_and_event_resource_limits(self):
        value = request({"s" + str(n): "نادر هو عالم." for n in range(9)})
        self.assertEqual(c.evaluate(value)["status"], "RESOURCE_LIMIT")
        value = request(); value["sources"][0]["text"] = "ع" * 8193
        self.assertEqual(c.evaluate(value)["status"], "RESOURCE_LIMIT")
        value = request(events=[event("withdraw", "law", str(i)) for i in range(17)])
        self.assertEqual(c.evaluate(value)["status"], "RESOURCE_LIMIT")

    def test_strict_transport_rejects_duplicate_json_keys(self):
        with self.assertRaises(ValueError):
            c.life.strict_loads('{"schema":"a","schema":"b"}')

    def test_source_parser_preserves_order_and_polarity(self):
        left = c._request(request({"s": "زيد فوق عمرو."}, "هل زيد فوق عمرو؟"))[1]
        right = c._request(request({"s": "عمرو فوق زيد."}, "هل عمرو فوق زيد؟"))[1]
        neg = c._request(request({"s": "ليس زيد فوق عمرو."}, "هل ليس زيد فوق عمرو؟"))[1]
        self.assertNotEqual(left, right)
        self.assertEqual(left, neg.opposite())


@unittest.skipUnless(NATIVE_READY, "build verifiedReading and evidenceLifecycleV1")
class NativeConnectionTests(unittest.TestCase):
    def evaluate(self, value):
        result = c.evaluate(value)
        self.assertTrue(result["chain_complete"], (result["status"], result.get("error")))
        self.assertTrue(result["lifecycle"]["native_checked"])
        return result

    def test_unseen_individual_acquires_conditions_and_applies_adopted_candidate(self):
        value = request()
        result = self.evaluate(value)
        last = result["history"][-1]
        self.assertEqual(last["status"], "SUPPORTED")
        learning = last["learning"]
        self.assertEqual(learning["survivor_count"], 1)
        self.assertTrue(learning["application_established"])
        self.assertEqual(learning["schema"]["predicates"], ["عالم"])
        self.assertEqual({r["entity"] for r in learning["observations"]}, {"حجر", "سالم"})
        self.assertEqual(learning["case_witnesses"]["عالم"][0]["source_id"], "case")
        self.assertTrue(all(v["accepted"] for v in last["certificate_checks"].values()))
        self.assertFalse(learning["sample_generalization_authorized"])

    def test_counterexample_changes_candidates_then_withdrawal_reopens_them(self):
        value = request(events=[event("activate", "negative"), event("withdraw", "negative")])
        value["initial_active"].remove("negative")
        history = self.evaluate(value)["history"]
        self.assertEqual([h["learning"]["survivor_count"] for h in history], [2, 1, 2])
        self.assertIn(0, [x["code"] for x in history[0]["learning"]["candidates"]])
        self.assertNotIn(0, [x["code"] for x in history[1]["learning"]["candidates"]])
        self.assertEqual(history[0]["learning"]["revision"], history[2]["learning"]["revision"])

    def test_examples_do_not_authorize_a_universal_rule(self):
        value = request(); value["initial_active"].remove("law")
        result = self.evaluate(value)["history"][-1]
        self.assertEqual(result["learning"]["prediction"]["possible"], [True])
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertFalse(result["learning"]["application_established"])
        self.assertTrue(all(r["adoption"] == "CANDIDATE_ONLY" for r in result["learning"]["candidates"]))

    def test_unknown_feature_does_not_become_false_training_label(self):
        value = request(); value["sources"][1]["text"] = "ليس حجر هو إنسان."
        learning = self.evaluate(value)["history"][-1]["learning"]
        row = next(r for r in learning["observations"] if r["entity"] == "حجر")
        self.assertEqual(row["case"]["known"], 0)
        self.assertFalse(row["ready"])
        self.assertEqual(learning["survivor_count"], 2)

    def test_conflicting_labels_remain_pending_with_both_witnesses(self):
        value = request(); value["sources"][1]["text"] += " حجر هو إنسان."
        learning = self.evaluate(value)["history"][-1]["learning"]
        row = next(r for r in learning["observations"] if r["entity"] == "حجر")
        self.assertTrue(row["conflicting_label"])
        self.assertIsNone(row["label"])
        self.assertEqual(len(row["label_witnesses"]), 2)

    def test_alternative_support_and_shared_premise_withdrawal(self):
        value = request({"rule_a": "كل عالم هو إنسان.",
                         "rule_b": "إذا كان ?ش هو عالم فإن ?ش هو إنسان.", "case": "نادر هو عالم."},
                        events=[event("withdraw", "rule_a"), event("withdraw", "case"), event("activate", "case")])
        result = self.evaluate(value)
        self.assertEqual({frozenset(r["sources"]) for r in result["minimal_source_supports"]},
                         {frozenset(("case", "rule_a")), frozenset(("case", "rule_b"))})
        self.assertEqual([h["status"] for h in result["history"]], ["SUPPORTED", "SUPPORTED", "UNKNOWN", "SUPPORTED"])
        self.assertEqual([len(h["support_ids"]) for h in result["history"]], [2, 1, 0, 1])
        self.assertTrue(all(not h["refutation_ids"] for h in result["history"]))

    def test_copy_depends_on_parent_and_independent_support_survives(self):
        value = request({"parent": "هذا_النص هو أصل.", "copy": "نادر هو عالم.",
                         "law": "كل عالم هو إنسان.", "independent": "نادر هو إنسان."},
                         events=[event("withdraw", "parent"), event("withdraw", "independent")])
        value["sources"][1]["parents"] = ["parent"]
        result = self.evaluate(value)
        self.assertEqual([h["status"] for h in result["history"]], ["SUPPORTED", "SUPPORTED", "UNKNOWN"])
        self.assertNotIn("copy", result["history"][1]["ready_sources"])
        self.assertEqual({frozenset(s["sources"]) for s in result["minimal_source_supports"]},
                         {frozenset(("independent",)), frozenset(("parent", "copy", "law"))})

    def test_source_cycles_create_no_support_without_an_initial_fact(self):
        value = request({"a": "كل عالم هو إنسان.", "b": "كل إنسان هو عالم."})
        result = self.evaluate(value)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["minimal_source_supports"], [])

    def test_conflicted_premise_is_not_a_clean_positive_answer(self):
        value = request({"law": "كل عالم هو إنسان.", "case": "نادر هو عالم.",
                         "opposition": "ليس نادر هو عالم."}, events=[event("withdraw", "opposition")])
        result = self.evaluate(value)
        self.assertEqual([h["status"] for h in result["history"]], ["DEFER", "SUPPORTED"])
        self.assertEqual(result["history"][0]["signed_support_status"], "SUPPORTED")
        self.assertFalse(result["history"][0]["learning"]["application_established"])

    def test_conclusion_conflict_then_withdrawal_preserves_negative_evidence(self):
        value = request({"yes": "نادر هو إنسان.", "no": "ليس نادر هو إنسان."},
                         events=[event("withdraw", "yes")])
        result = self.evaluate(value)
        self.assertEqual([h["status"] for h in result["history"]], ["CONFLICT", "REFUTED"])

    def test_order_and_negative_query_are_preserved_through_native_boundary(self):
        for query, expected in (("هل زيد فوق عمرو؟", "SUPPORTED"),
                                ("هل عمرو فوق زيد؟", "UNKNOWN"),
                                ("هل ليس زيد فوق عمرو؟", "REFUTED")):
            with self.subTest(query=query):
                result = self.evaluate(request({"s": "زيد فوق عمرو."}, query))
                self.assertEqual(result["status"], expected)

    def test_multi_condition_rule_acquires_all_premises(self):
        value = request({"law": "إذا كان ?ش هو عالم و ?ش هو أمين فإن ?ش هو مؤهل.",
                         "a": "نادر هو عالم.", "b": "نادر هو أمين."}, "هل نادر هو مؤهل؟",
                         [event("withdraw", "b")])
        result = self.evaluate(value)
        self.assertEqual([h["status"] for h in result["history"]], ["SUPPORTED", "UNKNOWN"])
        self.assertEqual(result["minimal_source_supports"][0]["sources"], ["a", "b", "law"])

    def test_learns_a_conjunction_from_separating_source_examples(self):
        value = request({"examples": "سالم هو عالم. سالم هو أمين. سالم هو مؤهل. "
                         "ليس حجر هو عالم. حجر هو أمين. ليس حجر هو مؤهل. "
                         "بكر هو عالم. ليس بكر هو أمين. ليس بكر هو مؤهل.",
                         "law": "إذا كان ?ش هو عالم و ?ش هو أمين فإن ?ش هو مؤهل.",
                         "case": "نادر هو عالم. نادر هو أمين."}, "هل نادر هو مؤهل؟")
        learning = self.evaluate(value)["history"][-1]["learning"]
        self.assertEqual(learning["survivor_count"], 1)
        self.assertEqual(learning["candidates"][0]["positive_mask"], 3)
        self.assertTrue(learning["application_established"])

    def test_grounding_preserves_shared_variables_and_argument_roles(self):
        value = request({"law": "إذا كان ?س فوق ?ص فإن ?ص تحت ?س.",
                         "case": "نادر فوق سالم."}, "هل سالم تحت نادر؟")
        result = self.evaluate(value)
        self.assertEqual(result["status"], "SUPPORTED")
        value["query"] = "هل نادر تحت سالم؟"
        self.assertEqual(self.evaluate(value)["status"], "UNKNOWN")

    def test_complete_receipt_replay_binds_sources_query_events_and_explanation(self):
        value = request()
        result = self.evaluate(value)
        self.assertTrue(c.verify(result, expected_request=value)["valid"])
        forged = deepcopy(result)
        forged["history"][0]["learning"]["case_witnesses"]["عالم"][0]["source_id"] = "law"
        self.assertFalse(c.verify(forged, expected_request=value)["valid"])
        for key in ("query", "events", "sources"):
            changed = deepcopy(value)
            if key == "query": changed[key] = "هل سالم هو إنسان؟"
            elif key == "events": changed[key] = [event("withdraw", "law")]
            else: changed[key][0]["text"] += " سالم هو إنسان."
            with self.subTest(key=key):
                self.assertFalse(c.verify(result, expected_request=changed)["valid"])

    def test_exact_utf8_spans_reconstruct_case_witness(self):
        value = request(); value["sources"][-1]["text"] = "  نادر هو عالم.\n"
        result = self.evaluate(value)
        witness = result["history"][0]["learning"]["case_witnesses"]["عالم"][0]
        span = witness["span"]
        raw = value["sources"][-1]["text"].encode()
        self.assertEqual(raw[span["start"]:span["end"]].decode(), "نادر هو عالم")

    def test_resource_exhaustion_does_not_issue_completed_answer(self):
        for name, limit in (("MAX_GROUND_CLAUSES", 1), ("MAX_SUPPORTS", 0), ("MAX_FEATURES", 0)):
            with self.subTest(name=name), patch.object(c, name, limit):
                result = c.evaluate(request())
                self.assertEqual(result["status"], "RESOURCE_LIMIT")
                self.assertFalse(result["chain_complete"])

    def test_native_unavailability_never_becomes_success(self):
        with patch.object(c.life, "NATIVE", ROOT / "absent-native"):
            result = c.evaluate(request())
        self.assertFalse(result["chain_complete"])
        self.assertFalse(result["lifecycle"]["native_checked"])

    def test_native_mismatch_fails_closed(self):
        with patch.object(c, "_native_ground", return_value={"native_checked": True, "status": "REFUTED"}):
            result = c.evaluate(request())
        self.assertEqual(result["status"], "VERIFICATION_FAILED")
        self.assertFalse(result["chain_complete"])

    def test_native_resource_limit_and_unsupported_alphabet_remain_distinct(self):
        with patch.object(c.pilot, "answer", side_effect=c.pilot.PilotError("RESOURCE_LIMIT", "native input limit")):
            result = c.evaluate(request())
        self.assertEqual(result["status"], "RESOURCE_LIMIT")
        result = c.evaluate(request({"text": "α هو عالم."}, "هل α هو عالم؟"))
        self.assertEqual(result["status"], "DEFER")
        self.assertFalse(result["chain_complete"])

    def test_empty_theory_reports_absence_without_claiming_native_ground_check(self):
        value = request({"case": "نادر هو إنسان."}, events=[event("withdraw", "case")])
        result = c.evaluate(value)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertFalse(result["chain_complete"])
        self.assertEqual(result["history"][-1]["support_ids"], [])
        self.assertFalse(result["history"][-1]["ground_inference"]["native_checked"])

    def test_original_request_is_immutable_and_repeated_withdrawal_is_idempotent(self):
        value = request(events=[event("withdraw", "law", "one"), event("withdraw", "law", "two")])
        original = deepcopy(value)
        result = self.evaluate(value)
        self.assertEqual(value, original)
        self.assertEqual([h["status"] for h in result["history"]], ["SUPPORTED", "UNKNOWN", "UNKNOWN"])

    def test_cli_and_replay_require_independent_request(self):
        with tempfile.TemporaryDirectory() as directory:
            source, receipt = Path(directory) / "request.json", Path(directory) / "receipt.json"
            source.write_text(json.dumps(request(), ensure_ascii=False), encoding="utf-8")
            cmd = [sys.executable, "-m", "tools.source_learning_connection", "--request", str(source)]
            env = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + str(ROOT)}
            run = subprocess.run([*cmd, "--output", str(receipt)], cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            run = subprocess.run([*cmd, "--verify", str(receipt)], cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            self.assertTrue(json.loads(run.stdout)["valid"])


if os.environ.get("NABT_REQUIRE_CONNECTION_NATIVE") == "1" and not NATIVE_READY:
    raise RuntimeError("Native connection checks are required, but executables are missing")


if __name__ == "__main__":
    unittest.main()
