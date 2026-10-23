"""Independent positive and negative controls for the v2 replay contract.

Fixtures state their interpretation and source-token roles explicitly. They do
not ask the reader or production verifier to synthesize expected statements.
"""
from __future__ import annotations

import copy
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from arabic_syntax_evaluation_helpers import oracle_helpers as oracle
from arabic_syntax_evaluation_helpers import statement_oracle as statements
from arabic_syntax_evaluation_helpers.runner import run

DATA = ROOT / "evidence/arabic_syntax/independent"
LANGUAGE = "nabt.arabic-syntax.v1"
SCOPE = "test_independent_contract"


def atom(predicate, argument="سالم", positive=True):
    return {"predicate": predicate, "args": [argument], "positive": positive}


def identity(payload):
    return sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def reidentify(clause):
    payload = ({"atom": clause["atom"]} if clause["kind"] == "fact" else
               {"body": clause["body"], "head": clause["head"], "kind": clause["rule_kind"]})
    payload.update({k: clause[k] for k in ("scope", "source_id", "source_sha256", "span", "analysis_id")})
    payload["semantic_version"] = "nabt.signed-horn.v1"
    clause["clause_id"] = identity(payload)


class Fixture:
    def __init__(self):
        self.active, self.manual, self.annotations = {}, {}, {}
        self.clauses = {}

    def add(self, sid, text, *, facts=(), rules=(), roles, rule_kinds=None):
        raw = text.encode()
        checksum = sha256(raw).hexdigest()
        # Only literal complete statements supplied by this test author.
        statement = statements.annotate_statement(text, text[:-1], facts=list(facts),
                                                   rules=list(rules), component_roles=roles,
                                                   rule_kinds=rule_kinds)
        record = statements.fixture_source(text, [statement])
        self.annotations[checksum] = record
        self.manual[checksum] = {"facts": list(facts), "rules": list(rules)}
        self.active[sid] = text
        def span(start, end):
            return {"source_id": sid, "source_sha256": checksum, "start": start, "end": end,
                    "span_sha256": sha256(raw[start:end]).hexdigest()}
        common = {"scope": SCOPE, "source_id": sid, "source_sha256": checksum,
                  "span": span(statement["start"], statement["end"]),
                  "component_spans": [span(c["start"], c["end"]) for c in statement["components"]],
                  "analysis_id": "a" * 64}
        entries = [{**common, "kind": "fact", "atom": f} for f in facts]
        entries += [{**common, "kind": "rule", **r, "rule_kind": (rule_kinds or ["explicit_rule"])[i]}
                    for i, r in enumerate(rules)]
        for clause in entries:
            reidentify(clause)
        self.clauses[sid] = entries
        return self

    def step(self, sid, result, *, binding=None, premises=None, clause_index=0):
        return {"atom": result, "clause": copy.deepcopy(self.clauses[sid][clause_index]),
                "binding": binding or {}, "premises": premises or []}

    def certificate(self, query, steps, kind="clean"):
        return {"version": "nabt.semantic-certificate.v1", "scope": SCOPE, "query": query,
                "proof_kind": kind, "program_sha256": oracle.program_identity(self.active, SCOPE, LANGUAGE),
                "steps": steps, "conclusion": len(steps) - 1, "world_truth": "NOT_ESTABLISHED"}

    def answer(self, query, status, proofs, positive, negative, reason="CLEAN_DERIVATION"):
        return {"status": status, "reason": reason, "scope": SCOPE, "query": query,
                "positive_support": positive, "negative_support": negative, "proofs": proofs,
                "missing_premises": [], "missing_complete": True,
                "missing_policy": "bounded_grounded_backward_plans_active_and_query_constants.v1",
                "contested_premises": [], "world_truth": "NOT_ESTABLISHED",
                "interpretation_status": "READ", "semantic_version": "nabt.signed-horn.v1",
                "program_sha256": oracle.program_identity(self.active, SCOPE, LANGUAGE),
                "atom_number": 0, "stats": {}}

    def check_certificate(self, certificate, **kwargs):
        return oracle.independent_certificate(certificate, self.active, SCOPE, self.manual,
                                              statement_oracle=self.annotations, **kwargs)

    def check_answer(self, answer, target):
        return oracle.validate_answer_certificates(answer, self.active, SCOPE, self.manual,
                                                   expected_query=target,
                                                   expected_program_sha256=oracle.program_identity(self.active, SCOPE, LANGUAGE),
                                                   statement_oracle=self.annotations)


class ArabicReplayContractTests(unittest.TestCase):
    def plain_fixture(self):
        return Fixture().add("a", "سالم هو حاضر.", facts=[atom("حاضر")],
                             roles=[["subject"], ["copula"], ["predicate"]])

    def conflict_fixture(self):
        f = Fixture()
        f.add("p", "سالم هو باحث.", facts=[atom("باحث")], roles=[["subject"], ["copula"], ["predicate"]])
        f.add("np", "ليس سالم هو باحث.", facts=[atom("باحث", positive=False)],
              roles=[["negation"], ["subject"], ["copula"], ["predicate"]])
        return f

    def test_clean_proof_checks_opposition_derived_outside_its_steps(self):
        f = self.conflict_fixture()
        q, nq = atom("دقيق"), atom("دقيق", positive=False)
        f.add("q", "سالم هو دقيق.", facts=[q], roles=[["subject"], ["copula"], ["predicate"]])
        rule = {"body": [atom("باحث", "?س")], "head": atom("دقيق", "?س", False)}
        f.add("r", "إذا ?س هو باحث فإن ليس ?س هو دقيق.", rules=[rule],
              roles=[["if"], ["body.arg"], ["body.copula"], ["body.predicate"], ["then"],
                     ["head.negation"], ["head.arg"], ["head.copula"], ["head.predicate"]])
        positive = f.certificate(q, [f.step("q", q)], "signed")
        negative = f.certificate(nq, [f.step("p", atom("باحث")), f.step("r", nq, binding={"?س": "سالم"}, premises=[0])], "signed")
        result = f.answer(q, "CONFLICT", {"query": positive, "opposite": negative}, True, True, "BOTH_SIGNS")
        self.assertEqual(len(f.check_answer(result, q)), 2)
        forged = copy.deepcopy(positive)
        forged["proof_kind"] = "clean"
        with self.assertRaisesRegex(oracle.ReplayValidationError, "contested atom"):
            f.check_certificate(forged)

    def test_unrelated_contradiction_does_not_contaminate_clean_proof(self):
        f = self.conflict_fixture()
        q = atom("دقيق")
        f.add("q", "سالم هو دقيق.", facts=[q], roles=[["subject"], ["copula"], ["predicate"]])
        proof = f.certificate(q, [f.step("q", q)])
        self.assertTrue(f.check_certificate(proof))
        self.assertEqual(len(f.check_answer(f.answer(q, "SUPPORTED", {"query": proof}, True, False), q)), 1)

    def test_signed_contested_chain_defers_and_cannot_claim_clean_support(self):
        f = self.conflict_fixture()
        for sid, body, head in [("r1", "باحث", "دقيق"), ("r2", "دقيق", "موثوق")]:
            rule = {"body": [atom(body, "?س")], "head": atom(head, "?س")}
            f.add(sid, f"إذا ?س هو {body} فإن ?س هو {head}.", rules=[rule],
                  roles=[["if"], ["body.arg"], ["body.copula"], ["body.predicate"],
                         ["then"], ["head.arg"], ["head.copula"], ["head.predicate"]])
        q = atom("موثوق")
        proof = f.certificate(q, [f.step("p", atom("باحث")),
                                 f.step("r1", atom("دقيق"), binding={"?س": "سالم"}, premises=[0]),
                                 f.step("r2", q, binding={"?س": "سالم"}, premises=[1])], "signed")
        answer = f.answer(q, "DEFER", {"query": proof}, True, False, "CONTESTED_PREMISES")
        self.assertEqual(len(f.check_answer(answer, q)), 1)
        answer["status"] = "SUPPORTED"
        with self.assertRaisesRegex(oracle.ReplayValidationError, "proof kind"):
            f.check_answer(answer, q)
        proof["proof_kind"] = "clean"
        with self.assertRaisesRegex(oracle.ReplayValidationError, "contested atom"):
            f.check_certificate(proof)

    def test_negative_frozen_query_defines_slot_polarity(self):
        f = Fixture().add("n", "ليس سالم هو حاضر.", facts=[atom("حاضر", positive=False)],
                          roles=[["negation"], ["subject"], ["copula"], ["predicate"]])
        q = atom("حاضر", positive=False)
        cert = f.certificate(q, [f.step("n", q)])
        supported = f.answer(q, "SUPPORTED", {"query": cert}, True, False)
        self.assertEqual(len(f.check_answer(supported, q)), 1)
        refuted = f.answer(atom("حاضر"), "REFUTED", {"opposite": cert}, False, True, "CLEAN_OPPOSITE_DERIVATION")
        self.assertEqual(len(f.check_answer(refuted, atom("حاضر"))), 1)
        swapped = f.answer(q, "REFUTED", {"opposite": cert}, False, True)
        with self.assertRaisesRegex(oracle.ReplayValidationError, "different query or polarity"):
            f.check_answer(swapped, q)

    def test_active_program_inventory_and_retracted_sources_are_bound(self):
        f = self.plain_fixture()
        q = atom("حاضر")
        cert = f.certificate(q, [f.step("a", q)])
        answer = f.answer(q, "SUPPORTED", {"query": cert}, True, False)
        f.add("b", "ليث هو يقظ.", facts=[atom("يقظ", "ليث")], roles=[["subject"], ["copula"], ["predicate"]])
        with self.assertRaisesRegex(oracle.ReplayValidationError, "another program"):
            f.check_answer(answer, q)
        del f.active["a"]
        with self.assertRaisesRegex(oracle.ReplayValidationError, "absent or retracted"):
            f.check_certificate(cert)

    def test_exact_quoted_name_is_preserved_without_trimming(self):
        q = atom("حاضر", " سالم ")
        f = Fixture().add("q", "« سالم » هو حاضر.", facts=[q],
                          roles=[["quoted_subject"], ["copula"], ["predicate"]])
        cert = f.certificate(q, [f.step("q", q)])
        self.assertTrue(f.check_certificate(cert))
        changed = copy.deepcopy(cert)
        changed["query"]["args"] = ["سالم"]
        with self.assertRaises(oracle.ReplayValidationError):
            f.check_certificate(changed)

    def test_opaque_analysis_identity_is_self_consistent_not_parser_authentication(self):
        f = self.plain_fixture()
        q = atom("حاضر")
        cert = f.certificate(q, [f.step("a", q)])
        clause = cert["steps"][0]["clause"]
        clause["analysis_id"] = "b" * 64
        with self.assertRaisesRegex(oracle.ReplayValidationError, "Clause ID"):
            f.check_certificate(cert)
        reidentify(clause)
        # Independent semantic replay deliberately does not claim to authenticate
        # the parser's internal, version-dependent analysis identifier.
        self.assertTrue(f.check_certificate(cert))

    def test_variable_alpha_renaming_preserves_roles_and_safe_domain(self):
        f = Fixture()
        rule = {"body": [atom("قارئ", "?x")], "head": atom("متفحص", "?x")}
        f.add("r", "كل قارئ هو متفحص.", rules=[rule], rule_kinds=["universal"],
              roles=[["quantifier"], ["body.predicate"], ["copula"], ["head.predicate"]])
        f.add("a", "سالم هو قارئ.", facts=[atom("قارئ")], roles=[["subject"], ["copula"], ["predicate"]])
        q = atom("متفحص")
        cert = f.certificate(q, [f.step("a", atom("قارئ")), f.step("r", q, binding={"?x": "سالم"}, premises=[0])])
        self.assertTrue(f.check_certificate(cert))
        step = cert["steps"][1]
        step["clause"]["body"][0]["args"] = ["?اسم"]
        step["clause"]["head"]["args"] = ["?اسم"]
        step["binding"] = {"?اسم": "سالم"}
        reidentify(step["clause"])
        self.assertTrue(f.check_certificate(cert))
        step["binding"]["?extra"] = "سالم"
        with self.assertRaisesRegex(oracle.ReplayValidationError, "Binding domain"):
            f.check_certificate(cert)

    def test_malformed_certificate_fields_raise_typed_replay_failure(self):
        f = self.plain_fixture()
        cert = f.certificate(atom("حاضر"), [f.step("a", atom("حاضر"))])
        cases = []
        for key, bad in [("steps", None), ("steps", {}), ("conclusion", True), ("query", []), ("scope", []), ("proof_kind", []), ("program_sha256", 0)]:
            changed = copy.deepcopy(cert); changed[key] = bad; cases.append(changed)
        for key in cert:
            changed = copy.deepcopy(cert); del changed[key]; cases.append(changed)
        changed = copy.deepcopy(cert); del changed["steps"][0]["clause"]["source_id"]; cases.append(changed)
        for index, changed in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(oracle.ReplayValidationError):
                f.check_certificate(changed)

    def test_unrelated_statement_cannot_supply_fact_polarity(self):
        text = "سالم هو حاضر. ليس سالم هو حاضر."
        pos, neg = atom("حاضر"), atom("حاضر", positive=False)
        one = statements.annotate_statement(text, "سالم هو حاضر", facts=[pos],
                                            component_roles=[["subject"], ["copula"], ["predicate"]])
        two = statements.annotate_statement(text, "ليس سالم هو حاضر", facts=[neg],
                                            component_roles=[["negation"], ["subject"], ["copula"], ["predicate"]])
        f = self.plain_fixture()
        cert = f.certificate(pos, [f.step("a", pos)], "signed")
        checksum = sha256(text.encode()).hexdigest()
        f.active["a"] = text
        f.manual = {checksum: {"facts": [pos, neg], "rules": []}}
        f.annotations = {checksum: statements.fixture_source(text, [one, two])}
        clause = cert["steps"][0]["clause"]
        clause["source_sha256"] = checksum
        def span(c):
            return {"source_id": "a", "source_sha256": checksum, "start": c["start"], "end": c["end"],
                    "span_sha256": sha256(text.encode()[c["start"]:c["end"]]).hexdigest()}
        clause["span"] = span(two)
        clause["component_spans"] = [span(c) for c in two["components"]]
        reidentify(clause)
        with self.assertRaisesRegex(oracle.ReplayValidationError, "not licensed by this statement"):
            f.check_certificate(cert)

    def test_independent_annotation_digest_is_not_self_authorizing(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "statement_oracle.json"
            data = json.loads(statements.ANNOTATION_PATH.read_text())
            data["records"][0]["statements"][0]["facts"][0]["predicate"] = "مزور"
            path.write_text(json.dumps(data, ensure_ascii=False))
            with patch.object(statements, "ANNOTATION_PATH", path):
                with self.assertRaisesRegex(ValueError, "checksum differs"):
                    statements.load_statement_oracle()

    def test_post_result_unexpected_exception_fails_replay_before_status(self):
        from nabt.semantics import SemanticKernel
        original = SemanticKernel.query
        class BrokenResult:
            def as_dict(self):
                raise KeyError("malformed result serialization")
        def query(kernel, text, *, scope="default"):
            if scope == "eval_s03":
                return BrokenResult()
            return original(kernel, text, scope=scope)
        with patch.object(SemanticKernel, "query", query):
            result = run(DATA, "arabic")
        case = next(c for c in result["episodes"] if c["id"] == "s03")
        self.assertFalse(case["independent_certificates_pass"])
        self.assertFalse(case["admitted_claims_licensed"])
        self.assertEqual(case["query_matches"], 0)
        self.assertEqual(case["events"][-1]["failure_stage"], "returned_answer_validation")

    def test_pre_result_query_noncoverage_is_separate_from_replay_failure(self):
        from nabt.semantics import SemanticKernel
        original = SemanticKernel.query
        def query(kernel, text, *, scope="default"):
            if scope == "eval_s03":
                raise ValueError("query unavailable before a result exists")
            return original(kernel, text, scope=scope)
        with patch.object(SemanticKernel, "query", query):
            result = run(DATA, "arabic")
        case = next(c for c in result["episodes"] if c["id"] == "s03")
        self.assertTrue(case["independent_certificates_pass"])
        self.assertTrue(case["admitted_claims_licensed"])
        self.assertFalse(case["complete_episode"])
        self.assertEqual(case["events"][-1]["failure_stage"], "query_execution")


if __name__ == "__main__":
    unittest.main()
