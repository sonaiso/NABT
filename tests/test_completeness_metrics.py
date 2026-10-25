import copy
import unittest
from tools.completeness_metrics import evaluate, paired_comparison

def fixture():
    rows=[("p","positive",["p1"]),("a","ambiguity",["a1","a2"]),
          ("n","negative",[]),("c","needs_context",[])]
    return {"schema":"acb.reference.v1","version":"synthetic-metric-test-only",
            "scope":"Synthetic scorer fixtures; no Arabic engine result","required_families":["f"],
            "cases":[{"id":i,"kind":k,"family":"f","gold_readings":g,
                      "gold_complete":k!="needs_context","source_ref":"synthetic:test"}
                     for i,k,g in rows]}

def perfect():
    return [{"id":"p","status":"licensed","readings":["p1"]},
            {"id":"a","status":"licensed_multiple","readings":["a1","a2"]},
            {"id":"n","status":"rejected","readings":[]},
            {"id":"c","status":"defer","readings":[]}]

class ScorerSafetyTests(unittest.TestCase):
    def test_all_abstain_is_not_success(self):
        p=[{"id":c["id"],"status":"defer","readings":[]} for c in fixture()["cases"]]
        m=evaluate(fixture(),p)["metrics"]
        self.assertIsNone(m["selective_decision_accuracy"]["value"])
        self.assertEqual(m["positive_exact_set_coverage"]["value"],0)
        self.assertEqual(m["licensed_reading_recall"]["value"],0)
        self.assertEqual(m["justified_deferral_precision"]["value"],0.25)
    def test_perfect_reference_agreement_is_scoped(self):
        r=evaluate(fixture(),perfect())
        self.assertEqual(r["metrics"]["positive_exact_set_coverage"]["value"],1)
        self.assertEqual(r["universal_arabic_completeness"],"NOT_INFERRED")
    def test_dropped_alternative_hurts_recall_and_exactness(self):
        p=perfect();p[1].update(status="licensed",readings=["a1"])
        m=evaluate(fixture(),p)["metrics"]
        self.assertEqual(m["licensed_reading_recall"]["value"],2/3)
        self.assertEqual(m["positive_exact_set_coverage"]["value"],0.5)
    def test_extra_reading_hurts_precision(self):
        p=perfect();p[1]["readings"].append("invented")
        self.assertEqual(evaluate(fixture(),p)["metrics"]["licensed_reading_precision"]["value"],0.75)
    def test_missing_output_keeps_denominator(self):
        m=evaluate(fixture(),perfect()[1:])["metrics"]
        self.assertEqual(m["positive_exact_set_coverage"],{"numerator":1,"denominator":2,"value":0.5})
        self.assertEqual(m["execution_error_rate"]["value"],0.25)
    def test_duplicate_ids_are_invalid(self):
        with self.assertRaises(ValueError):evaluate(fixture(),perfect()+perfect()[:1])
    def test_unknown_prediction_is_invalid(self):
        with self.assertRaises(ValueError):evaluate(fixture(),[{"id":"ghost","status":"defer","readings":[]}])
    def test_empty_reference_is_invalid(self):
        r=fixture();r["cases"]=[]
        with self.assertRaises(ValueError):evaluate(r,[])
    def test_unclosed_gold_is_not_a_complete_reference(self):
        r=fixture();r["cases"][0]["gold_complete"]=False
        with self.assertRaises(ValueError):evaluate(r,perfect())
    def test_resource_error_is_not_linguistic_refusal(self):
        p=perfect();p[0].update(status="resource_error",readings=[])
        m=evaluate(fixture(),p)["metrics"]
        self.assertEqual(m["execution_error_rate"]["value"],0.25)
        self.assertEqual(m["positive_exact_set_coverage"]["value"],0.5)
    def test_all_reject_has_zero_positive_coverage(self):
        p=[{"id":c["id"],"status":"rejected","readings":[]} for c in fixture()["cases"]]
        m=evaluate(fixture(),p)["metrics"]
        self.assertEqual(m["positive_exact_set_coverage"]["value"],0)
        self.assertEqual(m["negative_rejection_rate"]["value"],1)
    def test_premature_answer_is_reported(self):
        p=perfect();p[-1].update(status="licensed",readings=["guessed"])
        self.assertEqual(evaluate(fixture(),p)["metrics"]["premature_finalization_on_context"]["value"],1)
    def test_empty_negative_stratum_is_undefined(self):
        r=fixture();r["cases"]=r["cases"][:2]
        m=evaluate(r,perfect()[:2])["metrics"]
        self.assertIsNone(m["false_accept_rate_on_negative"]["value"])
    def test_pairing_preserves_case_ids(self):
        first=evaluate(fixture(),perfect());p=perfect()[1:]
        comp=paired_comparison(first,evaluate(fixture(),p))
        self.assertEqual(comp["wins"],["p"])
        self.assertEqual(comp["delta_positive_exact_set"],0.5)
    def test_unmeasured_required_family_stays_visible(self):
        r=fixture();r["required_families"].append("unmeasured")
        score=evaluate(r,perfect())
        self.assertEqual(score["unmeasured_positive_families"],["unmeasured"])

if __name__=="__main__":unittest.main()
