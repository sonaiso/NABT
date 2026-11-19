import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway, report_draft_host as host
from tools.grammar_catalog.ntp import request
from tools.lexical_training import report_draft as agent


TEXT = "اقرأ التقرير الأخير، واستخرج عدد الطلبات المعلّقة. إذا زاد على عشرة فأنشئ مسودة تنبيه. لا ترسلها."
ROOT = Path(__file__).resolve().parents[1]
def task():
    return {"schema": agent.SCHEMA, "task_id": "desk-001", "instruction": TEXT,
            "reports": json.loads((ROOT / "examples/report_draft/reports.json").read_text())}


def owner(receipt):
    return receipt["execution"]["owner_result"]["owner_result"]


class UnderstandingAndLearning(unittest.TestCase):
    def test_literal_spans_identity_count_and_source_inquiry(self):
        t = task()
        r = agent.run(t)
        self.assertEqual(r["status"], "DRAFT_PLANNED")
        self.assertEqual(r["report"]["id"], "nov-19")
        self.assertEqual(set(r["pending_ids"]), {"R-" + str(i) for i in range(1, 13)})
        self.assertEqual(r["row_indices_by_id"]["R-2"], [1, 12])
        self.assertEqual(r["count"], 12)
        witnesses = r["reading"]["witnesses_utf8"]
        self.assertEqual([TEXT.encode()[slice(*witnesses[s])].decode() for s in
                          ("if_strictly_greater", "threshold", "prohibit_send")],
                         ["إذا زاد على", "عشرة", "لا ترسلها"])
        self.assertEqual(r["learned_status_witnesses"]["بانتظار المراجعة"],
                         [{"report_id": "nov-17", "row": 0, "state_code": "PENDING"}])
        self.assertEqual(r["learning"]["result"]["candidate_counts"], [10,6,3,2,1])
        self.assertEqual(r["learning"]["reused_examples"], 0)

    def test_withdrawal_scope_and_conflict(self):
        for mode in ("withdraw", "different_scope", "opposing_witness"):
            t = task()
            if mode == "withdraw":
                t["reports"].pop(0)
            elif mode == "different_scope":
                t["reports"][0]["vocabulary"] = "unrelated"
            else:
                row = dict(t["reports"][0]["rows"][0], id="R-91", state_code="CLOSED")
                t["reports"][0]["rows"].append(row)
            with self.subTest(mode=mode):
                self.assertEqual(agent.run(t)["status"], "DEFER_ROWS")

    def test_thresholds_and_unseen_phrasings(self):
        for spelling, expected in (("١١", True), ("اثني عشر", False), ("13", False), ("صفر", None)):
            t = task()
            t["instruction"] = TEXT.replace("عشرة", spelling).replace("واستخرج", "ثم احسب").replace("التقرير الأخير", "أحدث تقرير")
            r = agent.run(t)
            with self.subTest(spelling=spelling):
                if expected is None:
                    self.assertEqual(r["status"], "DEFER_INSTRUCTION")
                else:
                    self.assertEqual(r["status"], "DRAFT_PLANNED" if expected else "NO_DRAFT")
        self.assertEqual(agent.train_guard(19, 28)["result"]["prediction"], [True])

    def test_scope_must_cover_every_character_and_conjunct(self):
        for text in ("قال المدير: " + TEXT, "«" + TEXT + "»", "هل " + TEXT,
                     TEXT.replace("لا ترسلها", "أرسلها"), TEXT.replace("زاد", "لم يزد"),
                     TEXT + " ثم أرسل نسخة", TEXT.replace("اقرأ", "أَقْرَأُ"),
                     TEXT.replace("فأنشئ", "فأنشئ؟"), TEXT.replace("عدد الطلبات", "عدد؟ الطلبات")):
            with self.subTest(text=text):
                self.assertEqual(agent.run(dict(task(), instruction=text))["status"], "DEFER_INSTRUCTION")

    def test_count_only_tie_empty_and_conflicting_rows(self):
        t = task()
        t["instruction"] = "كم عدد الطلبات المعلقة في التقرير الأخير؟"
        r = agent.run(t)
        self.assertEqual((r["status"],r["count"]), ("COUNTED",12))
        self.assertNotIn("draft_body", r)
        t["reports"].append(dict(t["reports"][-1], id="also-latest"))
        self.assertEqual(set(agent.run(t)["latest_candidates"]), {"nov-19","also-latest"})
        t["reports"] = []
        self.assertEqual(agent.run(t)["status"], "DEFER_REFERENCE")
        t = task()
        t["reports"][-1]["rows"] = []
        self.assertEqual(agent.run(t)["status"], "NO_DRAFT")
        t = task()
        t["reports"][-1]["rows"].append({"id":"R-1","status":"مغلق"})
        self.assertEqual(agent.run(t)["issues"][0]["reason"], "CONFLICTING_STATUS")

    def test_arabic_ids_and_transfer_on_new_task_sizes(self):
        for count in (0, 1, 5, 8, 13):
            for threshold in (0, 5, 13):
                t = task()
                t["task_id"] = "تقرير-١"
                t["instruction"] = TEXT.replace("عشرة", str(threshold))
                t["reports"][-1]["rows"] = [{"id": "طلب-" + str(i), "status": "معلق"}
                                            for i in range(count)]
                r = agent.run(t)
                with self.subTest(count=count, threshold=threshold):
                    self.assertEqual(r["count"],count)
                    self.assertEqual(r["status"] == "DRAFT_PLANNED", count > threshold)

    def test_invalid_input_and_cache(self):
        t = task()
        for bad in ("2026-03-51T00:00:00Z", True):
            t["reports"][0]["issued_utc"] = bad
            with self.assertRaises(ValueError):
                agent.run(t)
        with self.assertRaises(ValueError):
            agent.run(dict(task(), prior_examples=[{"grant":True}]))


class LocalExecution(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "drafts.sqlite3"

    def test_real_gateway_crash_resume_verify_and_skill_transfer(self):
        t = task()
        pure = request("cognitive.lesson", {"lesson":t})
        receipt = gateway.run(pure)
        self.assertTrue(gateway.accept_output(receipt, expected_request=pure)["valid"])
        self.assertEqual(receipt["execution"]["owner_result"]["observation_source_role"], "INSTRUCTION")
        self.assertFalse(self.path.exists())
        self.assertEqual(owner(host.run(t, self.path, apply=False))["draft_observation"], "ABSENT_IN_SNAPSHOT")
        self.assertFalse(self.path.exists())
        real_commit = host.commit_task
        def interrupt_after_commit(*args):
            real_commit(*args)
            raise ConnectionError("lost reply after durable commit")
        with patch.object(host, "commit_task", side_effect=interrupt_after_commit):
            with self.assertRaises(ConnectionError):
                host.run(t, self.path, apply=True)
        with patch.object(host, "commit_task", side_effect=AssertionError("duplicate write")):
            recovered = host.run(t, self.path, apply=True)
            self.assertEqual(owner(recovered)["draft_observation"], "MATCHED_SNAPSHOT")
            self.assertEqual(owner(host.run(t, self.path, apply=False))["draft_observation"], "MATCHED_SNAPSHOT")
        with sqlite3.connect(self.path) as db:
            rows = db.execute("select task_id, draft_body from report_tasks").fetchall()
            self.assertEqual(rows, [(t["task_id"],owner(recovered)["draft_body"])])
        self.assertTrue(gateway.accept_output(recovered, expected_request=copy.deepcopy(recovered["request"]))["valid"])
        forged = copy.deepcopy(recovered)
        owner(forged)["count"] = 999
        self.assertFalse(gateway.accept_output(forged, expected_request=recovered["request"])["valid"])
        second = dict(t, task_id="new-task", instruction=TEXT.replace("عشرة", "١٢"))
        result = owner(host.run(second, self.path, apply=True))
        self.assertEqual((result["status"],result["draft_observation"],result["learning"]["reused_examples"]),
                         ("NO_DRAFT","MATCHED_NO_DRAFT",4))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("select count(draft_body) from report_tasks").fetchone()[0],1)
        changed = dict(t, instruction=second["instruction"])
        self.assertEqual(owner(host.run(changed, self.path, apply=True))["draft_observation"], "TASK_ID_CONFLICT")

    def test_concurrent_commit_and_independent_body_readback(self):
        t = task()
        plan = agent.run(t)
        with ThreadPoolExecutor(max_workers=6) as workers:
            list(workers.map(lambda _: host.commit_task(self.path, plan), range(12)))
        observation, memory = host.read_store(self.path,t["task_id"])
        self.assertEqual(agent.run(dict(t, store_observation=observation))["draft_observation"], "MATCHED_SNAPSHOT")
        self.assertEqual(len(memory),4)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("select count(*) from report_tasks").fetchone()[0],1)
            db.execute("update report_tasks set draft_body='changed locally'")
        observed, _ = host.read_store(self.path,t["task_id"])
        self.assertEqual(agent.run(dict(t, store_observation=observed))["draft_observation"], "STORE_MISMATCH")

    def test_host_rejects_user_supplied_observations(self):
        with self.assertRaises(ValueError):
            host.run(dict(task(), store_observation=None), self.path, apply=True)
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
