"""Compiler counterexamples, plus mandatory native replay in the integration gate."""
from copy import deepcopy
from hashlib import sha256
from itertools import combinations, product
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.grammar_catalog import opencyc_slice as oc


def row(identifier, formula, mt="#$TestMt", strength="monotonic"):
    return dict(id=identifier, mt=mt, strength=strength, formula=formula)


def request(rows=None, query=None, **kw):
    if rows is None:
        rows = [row("f1", "(isa #$Fido #$Dog)"), row("g1", "(genls #$Dog #$Animal)")]
    ledger = "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows)
    out = {"schema": oc.SCHEMA,
           "source": {"id": "authored_fixture", "revision": "1", "uri": "urn:nabt:test-fixture:v1",
                      "license": "original test fixture; not a copied OpenCyc distribution",
                      "sha256": sha256(ledger.encode()).hexdigest()},
           "ledger": ledger, "context": "#$TestMt",
           "query": query or {"predicate": "isa", "arguments": ["#$Fido", "#$Animal"], "positive": True},
           "withdrawn": [], "bindings": [], "application": None}
    out.update(kw)
    return out


def diagnostic_closure(clauses):
    """Test-only, non-authoritative generic ground-clause interpreter."""
    def key(a):
        return a["predicate"], tuple(a["arguments"]), a["positive"]
    seen = {key(c["atom"]) for c in clauses if c["kind"] == "fact"}
    while True:
        next_seen = seen | {key(c["head"]) for c in clauses if c["kind"] == "rule"
                           and {key(a) for a in c["body"]} <= seen}
        if next_seen == seen:
            return seen
        seen = next_seen


def contains(compiled, kind, a, b, positive=True):
    return (oc.PRED[kind], (compiled["symbols"][a], compiled["symbols"][b]), positive) in diagnostic_closure(compiled["clauses"])


class SyntaxTests(unittest.TestCase):
    def test_four_families(self):
        for formula, pred in (("(#$isa #$Fido #$Dog)", "isa"),
                              ("(genls #$Dog #$Animal)", "genls"),
                              ("(disjointWith #$Dog #$Stone)", "disjointWith"),
                              ("(argIsa #$owns 2 #$Animal)", "argIsa")):
            with self.subTest(formula=formula):
                self.assertEqual(oc.parse_formula(formula)["predicate"], pred)

    def test_arg_alias_normalizes_without_losing_source(self):
        self.assertEqual(oc.parse_formula("(arg2Isa #$owns #$Animal)"),
                         oc.parse_formula("(argIsa #$owns 2 #$Animal)"))
        r = request([row("a", "(arg2Isa #$owns #$Animal)")])
        self.assertEqual(oc.compile_slice(r)["records"][0]["formula"], "(arg2Isa #$owns #$Animal)")

    def test_negation_retained(self):
        self.assertFalse(oc.parse_formula("(not (isa #$Fido #$Dog))")["positive"])

    def test_unsupported_not_silently_accepted(self):
        for f in ("(exists (?X) (isa ?X #$Dog))", "(genlMt #$A #$B)",
                  "(isa (#$Fn #$X) #$Dog)", "(not (genls #$A #$B))",
                  "(not (argIsa #$P 1 #$A))", '(comment #$Dog "text")'):
            with self.subTest(formula=f):
                c = oc.compile_slice(request([row("unsupported", f)]))
                self.assertEqual(c["status"], "DEFER")
                self.assertEqual(c["clauses"], [])
                self.assertTrue(c["residuals"])

    def test_malformed_rejected(self):
        for f in ("(isa #$A", ")", "(isa #$A)", "(isa #$A #$B) (isa #$C #$D)", "()"):
            with self.subTest(formula=f), self.assertRaises(oc.SliceError):
                oc.parse_formula(f)

    def test_variable_or_code_not_executed(self):
        for f in ("(isa ?x #$Dog)", "__import__('os').system('false')"):
            with self.subTest(formula=f), self.assertRaises(oc.SliceError):
                oc.parse_formula(f)

    def test_duplicate_json_key_rejected(self):
        r = request()
        r["ledger"] = '{"id":"a","id":"b","mt":"#$TestMt","strength":"monotonic","formula":"(isa #$A #$B)"}\n'
        r["source"]["sha256"] = sha256(r["ledger"].encode()).hexdigest()
        with self.assertRaises(oc.SliceError): oc.validate(r)

    def test_missing_context_rejected(self):
        r = request(); del r["context"]
        with self.assertRaises(oc.SliceError): oc.validate(r)

    def test_record_context_cannot_be_omitted(self):
        a = row("a", "(isa #$A #$B)"); del a["mt"]
        with self.assertRaises(oc.SliceError): oc.validate(request([a]))

    def test_digest_checked(self):
        r = request(); r["ledger"] += " "
        with self.assertRaisesRegex(oc.SliceError, "digest"): oc.validate(r)

    def test_no_caller_authority(self):
        for k in ("rank", "approved", "native_checked", "checker", "python_path"):
            r = request(); r[k] = True
            with self.subTest(field=k), self.assertRaises(oc.SliceError): oc.validate(r)

    def test_boolean_span_rejected(self):
        r = request(bindings=[dict(constant="#$Dog", byte_span=[False, 4])])
        with self.assertRaises(oc.SliceError): oc.validate(r)

    def test_withdrawal_names_known_id(self):
        with self.assertRaises(oc.SliceError): oc.validate(request(withdrawn=["missing"]))

    def test_duplicate_id_not_a_new_witness(self):
        with self.assertRaises(oc.SliceError):
            oc.validate(request([row("a", "(isa #$A #$B)"), row("a", "(isa #$A #$C)")]))

    def test_preserve_line_bytes(self):
        r = request(); c = oc.compile_slice(r)
        raw = r["ledger"].encode()
        for x in c["records"]:
            a, b = x["byte_span"]
            self.assertEqual(raw[a:b].decode(), x["raw_line"])
            self.assertEqual(sha256(raw[a:b]).hexdigest(), x["line_sha256"])
        self.assertEqual(c["request"], r)
        self.assertEqual(json.loads(oc.wire(c["request"])), r)


class AlgebraTests(unittest.TestCase):
    def test_isa_follows_genls(self):
        c = oc.compile_slice(request())
        self.assertTrue(contains(c, "isa", "#$Fido", "#$Animal"))
        self.assertFalse(contains(c, "isa", "#$Animal", "#$Fido"))

    def test_isa_is_not_transitive(self):
        c = oc.compile_slice(request([row("a", "(isa #$Fido #$Dog)"),
                                      row("b", "(isa #$Dog #$Animal)")]))
        self.assertFalse(contains(c, "isa", "#$Fido", "#$Animal"))

    def test_genls_transitive_and_cycles_finite(self):
        c = oc.compile_slice(request([row("a", "(genls #$A #$B)"), row("b", "(genls #$B #$C)"),
                                      row("c", "(genls #$C #$A)")],
                                     query=dict(predicate="genls", arguments=["#$A", "#$C"], positive=True)))
        self.assertTrue(contains(c, "genls", "#$A", "#$C"))
        self.assertLess(len(diagnostic_closure(c["clauses"])), 513)

    def test_disjoint_is_symmetric_and_negative(self):
        c = oc.compile_slice(request([row("a", "(isa #$Fido #$Dog)"),
            row("d", "(disjointWith #$Stone #$Dog)")],
            query=dict(predicate="isa", arguments=["#$Fido", "#$Stone"], positive=True)))
        self.assertTrue(contains(c, "isa", "#$Fido", "#$Stone", False))
        self.assertTrue(contains(c, "disjointWith", "#$Dog", "#$Stone"))
        self.assertFalse(contains(c, "isa", "#$Fido", "#$Stone", True))

    def test_unknown_not_false(self):
        c = oc.compile_slice(request(query=dict(predicate="isa", arguments=["#$Fido", "#$Stone"], positive=True)))
        self.assertFalse(contains(c, "isa", "#$Fido", "#$Stone"))
        self.assertFalse(contains(c, "isa", "#$Fido", "#$Stone", False))

    def test_negative_membership_moves_down_not_up(self):
        rows = [row("n", "(not (isa #$Fido #$Animal))"), row("g", "(genls #$Dog #$Animal)")]
        c = oc.compile_slice(request(rows))
        self.assertTrue(contains(c, "isa", "#$Fido", "#$Dog", False))
        c = oc.compile_slice(request([row("n", "(not (isa #$Fido #$Dog))"), rows[1]]))
        self.assertFalse(contains(c, "isa", "#$Fido", "#$Animal", False))

    def test_no_context_mix(self):
        c = oc.compile_slice(request([row("a", "(isa #$Fido #$Dog)"),
                                      row("b", "(genls #$Dog #$Animal)", mt="#$OtherMt")]))
        self.assertFalse(contains(c, "isa", "#$Fido", "#$Animal"))
        self.assertEqual(c["excluded"], [dict(id="b", reason="OTHER_CONTEXT")])

    def test_default_defers_entire_selected_slice(self):
        c = oc.compile_slice(request([row("a", "(isa #$Fido #$Dog)"),
                                      row("b", "(genls #$Dog #$Animal)", strength="default")]))
        self.assertEqual(c["status"], "DEFER")
        self.assertEqual(c["clauses"], [])

    def test_withdrawal_recomputes_not_mutates(self):
        r = request(); previous = oc.compile_slice(r)
        now = oc.compile_slice({**r, "withdrawn": ["g1"]})
        self.assertTrue(contains(previous, "isa", "#$Fido", "#$Animal"))
        self.assertFalse(contains(now, "isa", "#$Fido", "#$Animal"))
        self.assertNotEqual(previous["request_sha256"], now["request_sha256"])
        self.assertEqual(r["withdrawn"], [])
        self.assertEqual(previous["records"], now["records"])

    def test_unsupported_withdrawn_record_still_visible(self):
        r = request([row("f1", "(isa #$Fido #$Dog)"), row("e", "(exists (?x) (isa ?x #$Dog))")], withdrawn=["e"])
        c = oc.compile_slice(r)
        self.assertEqual(c["status"], "COMPILED")
        self.assertEqual(len(c["records"]), 2)

    def test_argument_constraints_do_not_invent_membership_or_occurrence(self):
        r = request([row("r", "(argIsa #$owns 1 #$Human)")],
                    query=dict(predicate="isa", arguments=["#$Fido", "#$Human"], positive=True),
                    application=dict(predicate="#$owns", arguments=["#$Fido", "#$Dog"]))
        c = oc.compile_slice(r)
        self.assertFalse(contains(c, "isa", "#$Fido", "#$Human"))
        self.assertEqual(c["argument_constraints"][0]["position"], 1)
        self.assertFalse(any(a[0] == "owns" for a in diagnostic_closure(c["clauses"])))

    def test_projection_back_to_source_for_every_clause(self):
        c = oc.compile_slice(request())
        self.assertEqual(len(c["clauses"]), len(c["clause_origins"]))
        known = {r["id"] for r in c["records"]}
        for o in c["clause_origins"]:
            self.assertTrue(o.get("record_id") in known or o["operation"] == "METADATA_ONLY")

    def test_reject_resource_escape(self):
        rows = [row(str(i), f"(isa #$F{i} #$Dog)") for i in range(17)]
        with self.assertRaisesRegex(oc.SliceError, "budget"): oc.compile_slice(request(rows))

    def test_finite_reachability_oracle_512_cases(self):
        # Independent set-of-reachable-nodes oracle, not the compiler recurrence.
        nodes = ("#$A", "#$B", "#$C")
        edges = [(a, b) for a in nodes for b in nodes if a != b]
        for mask in range(64):
            chosen = [edge for i, edge in enumerate(edges) if mask & (1 << i)]
            for members in range(8):
                initial = {g for i, g in enumerate(nodes) if members & (1 << i)}
                reached, todo = set(initial), list(initial)
                while todo:
                    node = todo.pop()
                    for a, b in chosen:
                        if a == node and b not in reached:
                            reached.add(b); todo.append(b)
                rows = [row(f"g{i}", f"(genls {a} {b})") for i, (a, b) in enumerate(chosen)]
                rows += [row(f"i{i}", f"(isa #$Fido {g})") for i, g in enumerate(sorted(initial))]
                rows += [row("ignored", "(isa #$Fido #$A)", mt="#$OtherMt")]
                c = oc.compile_slice(request(rows))
                # All three class names must be allocated, including absent targets.
                for target in nodes:
                    if target not in c["symbols"]:
                        c2 = oc.compile_slice(request(rows, query=dict(predicate="isa", arguments=["#$Fido", target], positive=True)))
                    else:
                        c2 = c
                    self.assertEqual(contains(c2, "isa", "#$Fido", target), target in reached)


class NativeOwnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        checker = oc.ROOT / "formal/.lake/build/bin/verifiedReading"
        required = os.environ.get("NABT_REQUIRE_OPENCYC_NATIVE") == "1"
        if not checker.is_file():
            if required:
                raise AssertionError("Original verifiedReading is required by the release gate")
            raise unittest.SkipTest("Original Lean checker not available locally")

    def run_owner(self, req):
        result = oc.analyze("كَلْبُ", "arabic_fixture", req)
        self.assertTrue(result["native_checked"], result.get("reason"))
        self.assertFalse(result["limits"]["world_truth_established"])
        return result

    def test_support_and_withdrawal(self):
        r = request()
        self.assertEqual(self.run_owner(r)["status"], "SUPPORTED")
        self.assertEqual(self.run_owner({**r, "withdrawn": ["g1"]})["status"], "UNKNOWN")

    def test_conflict_and_tainted_consequence(self):
        rows = [row("a", "(isa #$Fido #$Dog)"), row("b", "(not (isa #$Fido #$Dog))"),
                row("c", "(genls #$Dog #$Animal)")]
        self.assertEqual(self.run_owner(request(rows))["status"], "DEFER")
        self.assertEqual(self.run_owner(request(rows, query=dict(predicate="isa", arguments=["#$Fido", "#$Dog"], positive=True)))["status"], "CONFLICT")

    def test_negative_disjoint(self):
        r = request([row("a", "(isa #$Fido #$Dog)"), row("b", "(disjointWith #$Dog #$Stone)")],
                    query=dict(predicate="isa", arguments=["#$Fido", "#$Stone"], positive=True))
        self.assertEqual(self.run_owner(r)["status"], "REFUTED")

    def test_argument_obligation_and_no_occurrence(self):
        r = request([row("a", "(isa #$Fido #$Dog)"), row("b", "(genls #$Dog #$Animal)"),
                     row("c", "(arg1Isa #$touches #$Animal)")],
                    application=dict(predicate="#$touches", arguments=["#$Fido"]))
        checked = self.run_owner(r)["argument_check"]
        self.assertEqual(checked["status"], "DECLARED_CONSTRAINTS_SUPPORTED")
        self.assertFalse(checked["application_asserted"])
        self.assertFalse(checked["arity_completeness_established"])

    def test_a116_is_not_lexical_alignment(self):
        r = request(bindings=[dict(constant="#$Dog", byte_span=[0, len("كَلْبُ".encode())])])
        b = self.run_owner(r)["bindings"][0]
        self.assertEqual(b["status"], "DALI_IDENTITY_ONLY")
        self.assertEqual(b["restored"], "كَلْبُ")
        self.assertFalse(b["semantic_alignment_established"])

    def test_default_never_calls_native(self):
        r = request([row("a", "(isa #$Fido #$Dog)", strength="default")])
        with patch("tools.explainable_pilot.native", side_effect=AssertionError("must not run")):
            result = oc.analyze("كَلْبُ", "arabic_fixture", r)
        self.assertEqual(result["status"], "DEFER")
        self.assertFalse(result["native_checked"])


class GatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (oc.ROOT / "formal/.lake/build/bin/verifiedReading").is_file():
            if os.environ.get("NABT_REQUIRE_OPENCYC_NATIVE") == "1":
                raise AssertionError("Required original gateway checker missing")
            raise unittest.SkipTest("Full NABT build unavailable locally")

    def test_existing_route_validation_and_independent_replay(self):
        from tools.grammar_catalog import gateway
        req = {"schema": gateway.REQUEST_SCHEMA, "route": "relations.analyze",
               "payload": {"text": "كَلْبُ", "source_id": "arabic_fixture", "opencyc_slice": request()}}
        report = gateway.run(req)
        accepted = gateway.accept_output(report, expected_request=req)
        self.assertTrue(accepted["valid"], accepted)
        owner = report["execution"]["owner_result"]["opencyc_slice"]
        self.assertTrue(owner["native_checked"], owner)
        tampered = deepcopy(report)
        tampered["execution"]["owner_result"]["opencyc_slice"]["status"] = "UNKNOWN"
        self.assertFalse(gateway.accept_output(tampered, expected_request=req)["valid"])
        other = deepcopy(req); other["payload"]["opencyc_slice"]["withdrawn"] = ["g1"]
        self.assertFalse(gateway.accept_output(report, expected_request=other)["valid"])


if __name__ == "__main__":
    unittest.main()
