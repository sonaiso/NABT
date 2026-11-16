"""NTP inquiry contracts; mocked reducer tests are NOT native admission tests."""
from copy import deepcopy
from hashlib import sha256
from itertools import product
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.grammar_catalog import opencyc_slice as oc
from tools.lexical_training import opencyc_inquiry as iq


def make_lesson():
    forms = [
        ("a-f", "(isa #$A #$Feature)"),
        ("a-t", "(isa #$A #$Target)"),
        ("b-f", "(not (isa #$B #$Feature))"),
        ("b-t", "(not (isa #$B #$Target))"),
        ("c-f", "(isa #$C #$Feature)"),
    ]
    rows = [dict(id=k, mt="#$FixtureMt", strength="monotonic", formula=f) for k, f in forms]
    ledger = "".join(json.dumps(r) + "\n" for r in rows)
    source = dict(id="inquiry_fixture", revision="1", uri="urn:nabt:authored-inquiry-fixture:1",
                  license="Original authored test data; not extracted OpenCyc", sha256=sha256(ledger.encode()).hexdigest())
    s = dict(schema=oc.SCHEMA, source=source, ledger=ledger, context="#$FixtureMt",
             query=dict(predicate="isa", arguments=["#$A", "#$Target"], positive=True),
             withdrawn=[], bindings=[], application=None)
    return dict(schema=iq.SCHEMA, text="كَلْبُ", source_id="arabic_fixture", slice=s,
                target_class="#$Target", feature_classes=["#$Feature"],
                training_subjects=["#$A"], probe_subjects=["#$B", "#$C"], degree=1, events=[])


def event(identifier, op, target):
    return dict(id=identifier, operation=op, target=target)


def mock_direct_fact_owner(lesson):
    """Hand-authored test double, only direct facts; never the production verifier."""
    effective, _, _ = iq.project_events(lesson)
    compiled = oc.compile_slice(effective)
    facts = [c["atom"] for c in compiled["clauses"] if c["kind"] == "fact"]
    return dict(compiled=compiled, proposal=dict(known=facts, clean_known=facts),
                native_checked=True, native_receipt={"fixture_only": True}, status="SUPPORTED")


def reducer(lesson):
    iq.validate(lesson)
    _, trained, _ = iq.project_events(lesson)
    return iq._learn_checked(lesson, mock_direct_fact_owner(lesson), trained)


class ParserHardening(unittest.TestCase):
    def test_missing_atom_delimiters_rejected(self):
        for s in ("(isa#$A #$B)", "(isa #$A#$B)", "(argIsa #$P 1#$B)", "(argIsa #$P 1x #$B)"):
            with self.subTest(source=s), self.assertRaisesRegex(oc.SliceError, "delimiter"):
                oc.parse_formula(s)

    def test_spacing_and_parentheses_retained(self):
        for s in ("(isa #$A #$B)", "(isa\t#$A\n#$B)", "(not(isa #$A #$B))"):
            with self.subTest(source=s):
                self.assertEqual(oc.parse_formula(s)["arguments"], ["#$A", "#$B"])

    def test_parser_has_own_byte_budget_and_type_check(self):
        for value in (None, True, [], "", " " * 2049):
            with self.subTest(value=str(value)[:20]), self.assertRaises(oc.SliceError):
                oc.parse_formula(value)

    def test_source_preserved_when_compile_succeeds(self):
        s = make_lesson()["slice"]
        c = oc.compile_slice(s)
        self.assertEqual(c["request"]["ledger"], s["ledger"])
        for row in c["records"]:
            lo, hi = row["byte_span"]
            self.assertEqual(s["ledger"].encode()[lo:hi], row["raw_line"].encode())

    def test_512_finite_membership_graphs(self):
        nodes = ["#$X", "#$Y", "#$Z"]
        edges = [(a, b) for a in nodes for b in nodes if a != b]
        for mask, members in product(range(64), range(8)):
            selected = [e for i, e in enumerate(edges) if mask & (1 << i)]
            reached = {n for i, n in enumerate(nodes) if members & (1 << i)}
            frontier = list(reached)
            while frontier:
                a = frontier.pop()
                for x, y in selected:
                    if x == a and y not in reached:
                        reached.add(y); frontier.append(y)
            forms = [f"(genls {a} {b})" for a, b in selected]
            forms += [f"(isa #$Subject {n})" for i, n in enumerate(nodes) if members & (1 << i)]
            forms += ["(isa #$Metadata #$Metadata)"]
            for target in nodes:
                s = make_lesson()["slice"]
                s["ledger"] = "".join(json.dumps(dict(id=str(i), mt=s["context"], strength="monotonic", formula=f))+"\n" for i,f in enumerate(forms))
                s["source"]["sha256"] = sha256(s["ledger"].encode()).hexdigest()
                s["query"] = dict(predicate="isa", arguments=["#$Subject", target], positive=True)
                c = oc.compile_slice(s)
                def key(a): return a["predicate"], tuple(a["arguments"]), a["positive"]
                known = {key(r["atom"]) for r in c["clauses"] if r["kind"] == "fact"}
                while True:
                    nxt = known | {key(r["head"]) for r in c["clauses"] if r["kind"] == "rule" and all(key(a) in known for a in r["body"])}
                    if nxt == known: break
                    known = nxt
                self.assertEqual(key(c["goal"]) in known, target in reached)


class InquiryContracts(unittest.TestCase):
    def test_initial_induction_and_discriminating_question(self):
        r = reducer(make_lesson())
        self.assertEqual(r["candidate_counts"], [4, 2])
        self.assertEqual(r["next_step"]["action"], "SEEK_DISCRIMINATING_LABEL")
        self.assertEqual(r["next_step"]["subject"], "#$B")
        self.assertFalse(r["new_rule_adopted"])

    def test_observe_probe_uses_owner_label(self):
        l = make_lesson(); l["events"] = [event("e1", "observe", "#$B")]
        r = reducer(l)
        self.assertEqual(r["candidate_counts"], [4, 2, 1])
        self.assertEqual(r["survivor_codes"], [1])
        self.assertEqual(r["probe_predictions"][0]["possible"], [True])
        self.assertEqual(r["next_step"]["action"], "TEST_INDEPENDENT_OCCURRENCE_BEFORE_ADOPTION")

    def test_withdraw_reopens_and_restore_recovers(self):
        l = make_lesson(); l["events"] = [event("e1", "observe", "#$B")]
        a = reducer(l)
        l["events"].append(event("e2", "withdraw", "b-t")); b = reducer(l)
        self.assertEqual(b["candidate_counts"], [4, 2, 2])
        self.assertTrue(b["pending"])
        l["events"].append(event("e3", "restore", "b-t")); c = reducer(l)
        self.assertEqual(a["survivor_codes"], c["survivor_codes"])
        self.assertEqual(a["evidence_revision"], c["evidence_revision"])
        self.assertNotEqual(b["evidence_revision"], c["evidence_revision"])

    def test_history_preserved_and_no_request_mutation(self):
        l = make_lesson(); before = deepcopy(l)
        effective, trained, h0 = iq.project_events(l)
        self.assertEqual(l, before)
        l["events"] = [event("e1", "observe", "#$B")]
        _, _, h1 = iq.project_events(l)
        l["events"].append(event("e2", "withdraw", "b-t"))
        _, _, h2 = iq.project_events(l)
        self.assertEqual(h2["events"][0], h1["events"][0])
        self.assertEqual(h2["events"][1]["parent"], h1["head_sha256"])
        self.assertEqual(l["slice"]["ledger"], before["slice"]["ledger"])
        self.assertEqual(l["slice"]["withdrawn"], [])

    def test_no_caller_label_or_authority(self):
        for k in ("labels", "survivors", "rank", "native_checked", "approved", "model_path"):
            l = make_lesson(); l[k] = True
            with self.subTest(field=k), self.assertRaises(oc.SliceError): iq.validate(l)
        l = make_lesson(); l["events"] = [{**event("e", "observe", "#$B"), "label": True}]
        with self.assertRaises(oc.SliceError): iq.validate(l)

    def test_target_cannot_be_feature(self):
        l = make_lesson(); l["feature_classes"] = [l["target_class"]]
        with self.assertRaisesRegex(oc.SliceError, "target label"): iq.validate(l)

    def test_target_derived_feature_rejected(self):
        l = make_lesson()
        l["slice"]["ledger"] += json.dumps(dict(id="leak", mt=l["slice"]["context"], strength="monotonic",
                                                formula="(genls #$Target #$Feature)"))+"\n"
        l["slice"]["source"]["sha256"] = sha256(l["slice"]["ledger"].encode()).hexdigest()
        with self.assertRaisesRegex(oc.SliceError, "depend on the target"):
            iq.validate(l)

    def test_resource_limit_is_not_invalid_or_refuted(self):
        l = make_lesson(); l["events"] = [{}] * 17
        r = iq.run(l)
        self.assertEqual(r["status"], "RESOURCE_LIMIT")
        self.assertFalse(r["execution_measured"])
        self.assertIsNone(r["learning"])

    def test_probe_labels_not_used(self):
        l = make_lesson(); a = reducer(l)
        extra = json.dumps(dict(id="extra", mt=l["slice"]["context"], strength="monotonic", formula="(isa #$C #$Target)"))+"\n"
        l["slice"]["ledger"] += extra
        l["slice"]["source"]["sha256"] = sha256(l["slice"]["ledger"].encode()).hexdigest()
        b = reducer(l)
        self.assertEqual(a["survivor_codes"], b["survivor_codes"])
        self.assertEqual(a["next_step"], b["next_step"])
        self.assertFalse(b["withheld_probe_labels_used"])

    def test_unknown_not_negative(self):
        l = make_lesson(); l["slice"]["withdrawn"] = ["a-t"]
        r = reducer(l)
        self.assertEqual(r["candidate_counts"], [4, 4])
        self.assertEqual(r["training_samples"][0]["target_status"], "UNKNOWN")
        self.assertTrue(r["pending"])

    def test_conflicting_target_not_training_label(self):
        l = make_lesson(); o = mock_direct_fact_owner(l)
        a = oc.atom("oc_isa", o["compiled"]["symbols"]["#$A"], o["compiled"]["symbols"]["#$Target"], False)
        o["proposal"]["known"].append(a)
        r = iq._learn_checked(l, o, ["#$A"])
        self.assertEqual(r["candidate_counts"], [4, 4])
        self.assertEqual(r["training_samples"][0]["target_status"], "CONFLICT")

    def test_tainted_feature_is_pending(self):
        l = make_lesson(); o = mock_direct_fact_owner(l)
        sym = o["compiled"]["symbols"]
        o["proposal"]["clean_known"] = [a for a in o["proposal"]["known"] if a["arguments"] != [sym["#$A"],sym["#$Feature"]]]
        r = iq._learn_checked(l, o, ["#$A"])
        self.assertEqual(r["candidate_counts"], [4, 4])
        self.assertEqual(r["training_samples"][0]["feature_statuses"]["#$Feature"], "DEFER")

    def test_missing_native_stops_induction(self):
        l = make_lesson(); o = mock_direct_fact_owner(l); o["native_checked"] = False
        o["native_receipt"] = None; o["reason"] = "CHECKER_UNAVAILABLE"
        with patch.object(oc, "analyze", return_value=o), patch.object(iq, "_learn_checked", side_effect=AssertionError("not allowed")):
            r = iq.run(l)
        self.assertEqual(r["status"], "DEFER"); self.assertIsNone(r["learning"])
        self.assertFalse(r["execution_measured"])

    def test_false_native_marker_is_not_enough(self):
        l = make_lesson(); o = mock_direct_fact_owner(l); o["native_receipt"] = None
        with self.assertRaises(ValueError): iq._learn_checked(l,o,["#$A"])

    def test_owner_mismatch_is_blocked(self):
        l = make_lesson(); o = mock_direct_fact_owner(l)
        o["compiled"]["request_sha256"] = "0"*64
        with patch.object(oc, "analyze", return_value=o), self.assertRaises(oc.SliceError): iq.run(l)

    def test_schema_bound_to_context(self):
        a = reducer(make_lesson()); l=make_lesson(); l["slice"]["context"]="#$OtherMt"
        b=reducer(l)
        self.assertNotEqual(a["schema_sha256"],b["schema_sha256"])
        self.assertEqual(b["candidate_counts"],[4,4])

    def test_schema_bound_to_target(self):
        a=reducer(make_lesson()); l=make_lesson(); l["target_class"]="#$A"
        b=reducer(l); self.assertNotEqual(a["schema_sha256"],b["schema_sha256"])

    def test_bad_events_rejected(self):
        for events in ([event("x","restore","a-t")], [event("x","withdraw","missing")],
                       [event("x","observe","#$A")], [event("x","grant","#$B")],
                       [event("x","withdraw","a-t"),event("y","withdraw","a-t")],
                       [event("x","observe","#$B"),event("x","withdraw","a-t")]):
            l=make_lesson();l["events"]=events
            with self.subTest(events=events),self.assertRaises(oc.SliceError):iq.validate(l)

    def test_limits_and_overlap(self):
        for key,value in (("degree",True),("degree",2),("feature_classes",[]),
                          ("training_subjects",["#$A","#$A"]),
                          ("probe_subjects",["#$A"]),("events",[{}]*17)):
            l=make_lesson();l[key]=value
            with self.subTest(field=key),self.assertRaises(oc.SliceError):iq.validate(l)

    def test_outside_slice(self):
        l=make_lesson();l["probe_subjects"]=["#$Absent"]
        with self.assertRaisesRegex(oc.SliceError,"source slice"):iq.validate(l)

    def test_default_cannot_be_induction_input(self):
        l=make_lesson();l["slice"]["ledger"]=l["slice"]["ledger"].replace('"monotonic"','"default"')
        l["slice"]["source"]["sha256"]=sha256(l["slice"]["ledger"].encode()).hexdigest()
        c=oc.compile_slice(l["slice"])
        self.assertEqual(c["status"],"DEFER");self.assertEqual(c["clauses"],[])

    def test_fixed_policy_has_no_self_mutation(self):
        self.assertFalse(iq.LIMITS["law_mutation_authorized"])
        self.assertFalse(iq.LIMITS["neural_training_performed"])
        self.assertEqual(iq.LIMITS["action_authority"],"NONE")

    def test_replay_is_deterministic_with_same_fixture(self):
        l=make_lesson();o=mock_direct_fact_owner(l)
        with patch.object(oc,"analyze",return_value=o):
            a=iq.run(l);b=iq.run(l)
        self.assertEqual(oc.wire(a),oc.wire(b))
        self.assertEqual(a["request"],l)


class NativeInquiry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (oc.ROOT / "formal/.lake/build/bin/verifiedReading").is_file():
            if os.environ.get("NABT_REQUIRE_OPENCYC_NATIVE")=="1":
                raise AssertionError("Original Lean owner required, not a test double")
            raise unittest.SkipTest("Original Lean/gateway unavailable locally")

    def test_native_learn_and_revise(self):
        l=make_lesson();a=iq.run(l)
        self.assertTrue(a["execution_measured"],a)
        self.assertEqual(a["learning"]["candidate_counts"],[4,2])
        l["events"]=[event("e1","observe","#$B")]
        b=iq.run(l);self.assertEqual(b["learning"]["survivor_codes"],[1])
        l["events"].append(event("e2","withdraw","b-t"))
        c=iq.run(l);self.assertEqual(c["learning"]["candidate_counts"],[4,2,2])
        l["events"].append(event("e3","restore","b-t"))
        d=iq.run(l);self.assertEqual(d["learning"]["survivor_codes"],[1])
        self.assertEqual(d["history"]["events"][:2],c["history"]["events"])

    def test_gateway_original_replay_and_tamper(self):
        from tools.grammar_catalog import gateway
        req={"schema":gateway.REQUEST_SCHEMA,"route":"cognitive.lesson","payload":{"lesson":make_lesson()}}
        r=gateway.run(req);a=gateway.accept_output(r,expected_request=req)
        self.assertTrue(a["valid"],a)
        self.assertTrue(r["execution"]["owner_result"]["execution_measured"],r)
        bad=deepcopy(r);bad["execution"]["owner_result"]["learning"]["survivor_codes"]=[0]
        self.assertFalse(gateway.accept_output(bad,expected_request=req)["valid"])
        other=deepcopy(req);other["payload"]["lesson"]["events"]=[event("e","observe","#$B")]
        self.assertFalse(gateway.accept_output(r,expected_request=other)["valid"])


if __name__=="__main__":
    unittest.main()
