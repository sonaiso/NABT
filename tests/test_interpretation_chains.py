import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import chain_change_map
from tools.grammar_catalog import interpretation_chains as chains

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"evidence/interpretation_chains_v1/challenge.json"
NATIVE=all((ROOT/"formal/.lake/build/bin"/n).is_file() for n in ("temporalContextProbe","epistemicMeasurement"))


class MethodContracts(unittest.TestCase):
    def test_axes_have_explicit_obligations_and_a_real_owner_reference(self):
        registry={r[0] for r in (*chains.FOUNDATION,*chains.MATRICES)}
        for _,_,aliases,coordinate,treatment,obligation in chains.OPERATIONS:
            self.assertIn(coordinate,registry)
            for word in aliases.split("|"):
                r=chains.analyze(f"ما منهج «{word}»؟")
                self.assertEqual(r["method"]["treatment"],treatment)
                self.assertEqual(r["method"]["evidence_required"],obligation)
                self.assertEqual(r["method"]["question_path"][0],"الوجود والموجودات")
                self.assertFalse(r["method"]["application_established"])
        self.assertNotEqual(chains.method("المانع")["registry"],chains.method("الشرط")["registry"])
        self.assertIsNone(chains.method("مثال غير مراجع"))

    def test_pr_trace_preserves_unmapped_and_multiple_family_references(self):
        files=["unknown/file.py","tools/grammar_catalog/interpretation_chains.py","formal/Nabt/TemporalContext.lean"]
        out={r["path"]:r for r in chain_change_map.change_map(files)}
        self.assertEqual(out[files[0]]["status"],"UNMAPPED")
        self.assertIn(["epistemic-measurement","runtime_paths"],out[files[1]]["family_links"])
        self.assertIn(["discourse","formal_modules"],out[files[2]]["family_links"])


@unittest.skipUnless(NATIVE,"Build temporal and measurement owners")
class ChangeAndReport(unittest.TestCase):
    def test_frozen_interventions_and_local_spans(self):
        for case in json.loads(DATA.read_bytes()):
            with self.subTest(id=case["id"]):
                r=chains.analyze(case["text"])
                self.assertEqual(r["status"],case.get("status","SOURCE_RELATIVE_CHAIN"))
                self.assertEqual([c["status"] for c in r["changes"]],case.get("changes",[]))
                self.assertEqual([c["observation_check"] for c in r["reports"]],case.get("reports",[]))
                self.assertEqual([bool(c["receipt_evidence"]) for c in r["reports"]],case.get("receipt",[]))
                self.assertTrue(all(c["native_checked"] for c in r["reports"]))
                for row in r["records"]:
                    for w in [row["witness"],*row["fields"].values()]:
                        self.assertEqual(case["text"].encode()[slice(*w["utf8_span"])].decode(),w["text"])
                self.assertFalse(r["limits"]["cause_established"])
                self.assertFalse(r["limits"]["external_event_established"])

    def test_observer_and_time_mismatch_do_not_support_claim(self):
        text=json.loads(DATA.read_bytes())[0]["text"]
        r=chains.analyze(text.replace('عن اليوم ٢','عن اليوم ٧'))
        self.assertEqual(r["changes"][0]["status"],"CHANGED")
        self.assertEqual(r["reports"][0]["observation_check"],"UNKNOWN")
        self.assertTrue(r["reports"][0]["receipt_evidence"])

    def test_removing_observation_changes_only_dependent_claims(self):
        source=json.loads(DATA.read_bytes())[0]["text"]
        header,solid,liquid,report,reception=source.split("\n")
        base=chains.analyze(source)
        short=chains.analyze("\n".join((header,solid,report,reception)))
        self.assertEqual(short["changes"],[])
        self.assertEqual(short["reports"][0]["observation_check"],"UNKNOWN")
        self.assertEqual(short["reports"][0]["claim"],base["reports"][0]["claim"])
        self.assertEqual(short["reports"][0]["receipt_evidence"],base["reports"][0]["receipt_evidence"])
        self.assertEqual(base,chains.analyze(source))

    def test_failed_clock_preserves_testimony_and_originals(self):
        text=json.loads(DATA.read_bytes())[0]["text"]
        with patch.object(chains.temporal,"native",return_value={"available":False,"executed":False,"calls":[]}):
            r=chains.analyze(text)
            self.assertEqual(r["status"],"PARTIAL_VERIFICATION")
            self.assertEqual(r["reports"][0]["observation_check"],"SUPPORTED")
            self.assertEqual(r["changes"][0]["status"],"VERIFICATION_UNAVAILABLE")

    def test_two_observations_in_one_time_are_not_two_events(self):
        head="سلسلة «المادة» من نوع «مادة» في «البيت»."
        rows=["رصد «سالم» اليوم ١: الطور = صلب.","رصد «ليلى» اليوم ١: الطور = صلب.","رصد «هند» اليوم ٩: الطور = سائل."]
        r=chains.analyze("\n".join([head,*rows]))
        self.assertEqual(len(r["changes"]),1)
        self.assertEqual(r["changes"][0]["dependencies"],[v["id"] for v in r["records"]])

    def test_unsupported_type_and_budget(self):
        s=json.loads(DATA.read_bytes())[0]["text"]
        self.assertEqual(chains.analyze(s.replace("نوع «مادة»","نوع «جماعة»"))["status"],"OUTSIDE_PROFILE")
        self.assertEqual(chains.analyze(s.split("\n")[0]+"\n"+"\n".join([s.split("\n")[1]]*13))["status"],"RESOURCE_LIMIT")
