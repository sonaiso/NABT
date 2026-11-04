"""Replay, deletion, transformation and out-of-language controls for passage v1."""
from copy import deepcopy
from itertools import combinations
import json
import os
import subprocess
import unittest
from unittest.mock import patch

from tools.lexical_training import grounded_passage as g, teaching as t

ROOT = g.ROOT
READY = all(p.is_file() for p in (g.NATIVE, ROOT / "formal/.lake/build/bin/connectedAcquisitionV3"))
if os.environ.get("NABT_REQUIRE_COGNITIVE_NATIVE") == "1" and not READY:
    raise RuntimeError("Passage gate requires both native owners")


def lesson():
    r = json.loads((ROOT / "examples/cognitive_teaching/passage.json").read_text())
    p = r["payload"]
    p["query"].update(gate="عَدَنَ", subject="زيد", day="2027-01-28")
    for row in p["sources"]:
        row["day"] = p["query"]["day"]
    m, f, log, notice = p["sources"]
    m.update(gate="عَدَنَ", x=-2)
    f.update(subject="زيد", samples=[{"minute": 481, "x": -230}])
    log.update(subject="زيد", unit="cm", samples=[
        {"minute": 450, "x": -300}, {"minute": 451, "x": -200}, {"minute": 452, "x": -100}])
    notice.update(addressee="زيد", text="قَبْلَ 08:00، لَكَ عُبُورُ بَابِ عَدَنَ.")
    return r


@unittest.skipUnless(READY, "build groundedPassage and connectedAcquisitionV3")
class GroundedPassageTests(unittest.TestCase):
    def result(self, request):
        result = t.run_lesson(request)
        self.assertTrue(result["execution_measured"], result.get("error", result["status"]))
        return result["owner_result"]["answers"]

    def test_unseen_gate_coordinates_clock_and_source_spans(self):
        request = lesson()
        report = t.run_lesson(request)
        self.assertTrue(report["execution_measured"])
        owner = report["owner_result"]
        def values(kind):
            return [p["value"] for p in owner["answers"][kind]["paths"]]
        self.assertEqual(values("position"), [{"minute": 481, "x_cm": -230}])
        self.assertEqual(values("direction"), [{"minute": 481, "side": "left"}])
        self.assertEqual(values("distance"), [{"minute": 481, "cm": 30}])
        self.assertEqual(values("crossing"), [451])
        self.assertEqual(values("permission_endpoint"), [{"minute": 480, "boundary": "exclusive"}])
        self.assertEqual(values("crossing_before_deadline"), [{"minute": 451, "limit": 480}])
        raw = request["payload"]["sources"][-1]["text"].encode()
        prefix, clause = owner["bindings"]["notice"]["parts"]
        self.assertEqual(raw[slice(*prefix["message_bytes"])].decode(), "قَبْلَ")
        reading = clause["reading"]
        self.assertEqual(raw[slice(*clause["message_bytes"])].decode(), reading["acquisition"]["text"])
        self.assertTrue(reading["shape_verified"])
        self.assertEqual(reading["phrase_shape"]["mode"], "waqf")
        self.assertEqual([j["span"]["raw"] for j in reading["realization"]["joins"]], [" "]*3)

    def test_all_support_subsets_match_independent_requirements(self):
        request = lesson()
        expected = {"position": {"fix"}, "direction": {"fix","plan"}, "distance": {"fix","plan"},
                    "crossing": {"log","plan"}, "permission_endpoint": {"notice"},
                    "crossing_before_deadline": {"log","plan","notice"}}
        keys = list(request["payload"]["active"])
        for size in range(len(keys)+1):
            for active in combinations(keys, size):
                request["payload"]["active"] = list(active)
                for kind, row in self.result(request).items():
                    with self.subTest(active=active, kind=kind):
                        self.assertEqual(row["status"] == "SUPPORTED", expected[kind] <= set(active))
                        for path in row["paths"]:
                            self.assertEqual(set(path["sources"]), expected[kind])

    def test_reverse_view_and_rescale_to_metres(self):
        r = lesson()
        f = r["payload"]["sources"][1]
        f["samples"][0]["x"] = -300
        baseline = self.result(r)
        r["payload"]["query"]["facing"] = "backward"
        f.update(unit="m", samples=[{"minute":481,"x":-3}])
        result = self.result(r)
        self.assertEqual(result["direction"]["paths"][0]["value"]["side"], "right")
        for k in ("distance","position","crossing","permission_endpoint","crossing_before_deadline"):
            self.assertEqual(result[k]["paths"][0]["value"], baseline[k]["paths"][0]["value"])
        self.assertEqual(result["distance"]["paths"][0]["value"]["cm"], 100)

    def test_two_recorded_paths_and_shared_map_withdrawal(self):
        r = lesson()
        p = r["payload"]
        other = deepcopy(p["sources"][2])
        other.update(id="other-log",samples=[{"x":-220,"minute":449},{"x":-200,"minute":451},
                                             {"x":-80,"minute":458}])
        p["sources"].append(other)
        p["active"].append(other["id"])
        for key in ("crossing","crossing_before_deadline"):
            self.assertEqual(len(self.result(r)[key]["paths"]), 2)
        p["active"].remove("log")
        self.assertEqual(self.result(r)["crossing"]["paths"][0]["sources"], ["plan","other-log"])
        p["active"].remove("plan")
        answers = self.result(r)
        self.assertEqual(answers["crossing"]["status"], "UNKNOWN")
        self.assertEqual(answers["permission_endpoint"]["status"], "SUPPORTED")

    def test_no_implicit_interpolation_or_boundary_inclusion(self):
        r = lesson()
        p = r["payload"]
        log = p["sources"][2]
        del log["samples"][1]
        self.assertEqual(self.result(r)["crossing"]["status"], "UNKNOWN")
        log["samples"] = [{"minute":479,"x":-201},{"minute":480,"x":-200},{"minute":481,"x":-199}]
        p["sources"][-1]["text"] = p["sources"][-1]["text"].replace("قَبْلَ","حَتَّى")
        answers = self.result(r)
        self.assertEqual(answers["crossing"]["status"], "SUPPORTED")
        self.assertEqual(answers["crossing_before_deadline"]["status"], "UNKNOWN")
        self.assertEqual(answers["permission_endpoint"]["paths"][0]["value"]["boundary"], "unspecified")

    def test_scope_binding_linguistic_separation_and_conflicting_spelling(self):
        for wrong in ("addressee","day","site","other_gate","merged_words","extra_clause","negation"):
            r = lesson()
            notice = r["payload"]["sources"][-1]
            if wrong in ("addressee","day","site"):
                notice[wrong] = "2027-01-29" if wrong == "day" else "other"
            else:
                notice["text"] = {"other_gate":notice["text"].replace("عَدَنَ","حَلَبَ"),
                    "merged_words":notice["text"].replace("عُبُورُ بَابِ","عُبُورُبَابِ"),
                    "extra_clause":notice["text"] + " انتهى.",
                    "negation":notice["text"].replace("لَكَ","لَيْسَ لَكَ")}[wrong]
            with self.subTest(wrong=wrong):
                answers = self.result(r)
                self.assertEqual(answers["permission_endpoint"]["status"], "UNKNOWN")
                self.assertEqual(answers["crossing"]["status"], "SUPPORTED")

    def test_tampering_replay_and_unavailable_source_owner(self):
        r = lesson()
        report = t.run_lesson(r)
        self.assertTrue(t.verify_lesson(report, expected_lesson=r)["valid"])
        report["owner_result"]["answers"]["distance"]["paths"][0]["value"]["cm"] = 42
        self.assertFalse(t.verify_lesson(report, expected_lesson=r)["valid"])
        with patch.object(g.acquisition, "read_acquired", return_value={
                "verified":False, "status":"VERIFICATION_UNAVAILABLE"}):
            full = t.run_lesson(r)
            self.assertFalse(full["execution_measured"])
            self.assertEqual(full["owner_result"]["answers"]["crossing"]["status"], "SUPPORTED")
            r["payload"]["active"].remove("notice")
            self.assertEqual(self.result(r)["crossing"]["status"], "SUPPORTED")

    def test_shape_checker_failure_is_not_a_measured_deferral(self):
        r = lesson()
        failure = {"verified": True, "shape_verified": False, "status": "SHAPE_CHECK_FAILED"}
        with patch.object(g.acquisition, "read_acquired", return_value=failure):
            report = t.run_lesson(r)
            self.assertFalse(report["execution_measured"])
            self.assertFalse(t.verify_lesson(report, expected_lesson=r)["valid"])
            answers = report["owner_result"]["answers"]
            self.assertEqual(answers["permission_endpoint"]["status"], "SHAPE_CHECK_FAILED")
            self.assertEqual(answers["crossing"]["status"], "SUPPORTED")

    def test_curriculum_drift_during_validation_rejects_measured_result(self):
        identities = [{"test_file":"before"}, {"test_file":"after"}, {"test_file":"after"}]
        with patch.object(t, "_identity", side_effect=identities):
            report = t.run_lesson(lesson())
        self.assertEqual(report["status"], "INVALID_INPUT")
        self.assertFalse(report["execution_measured"])
        self.assertIn("changed during execution", report["error"])

    def test_schema_and_internal_native_wire(self):
        for bad in (True, 2.5):
            r = lesson()
            r["payload"]["sources"][0]["x"] = bad
            self.assertEqual(t.run_lesson(r)["status"], "INVALID_INPUT")
        r = lesson()
        r["payload"]["sources"][2]["samples"].reverse()
        self.assertEqual(t.run_lesson(r)["status"], "INVALID_INPUT")
        r = lesson()
        r["payload"]["answer"] = True
        self.assertEqual(t.run_lesson(r)["status"], "INVALID_INPUT")
        raw = json.dumps('{"active":[],"active":[]}') + "\n"
        run = subprocess.run([str(g.NATIVE)],input=raw,text=True,capture_output=True,check=True)
        self.assertEqual(json.loads(run.stdout)["status"], "INVALID_INPUT")
