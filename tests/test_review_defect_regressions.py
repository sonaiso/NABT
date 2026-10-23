"""Independent, local counterexamples for the five PR3 review defects.

The main witness is the published s07 certificate, frozen before these fixes.
Expected meanings are not obtained by rerunning the implementation under test.
These are public regression tests, not new held-out Arabic coverage evidence.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from nabt.arabic_reader import LANGUAGE_ID
from nabt.semantics import SemanticKernel


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "evidence/arabic_syntax/independent"
sys.path.insert(0, str(ROOT / "tools"))
try:
    from arabic_syntax_evaluation import regression_gate
    from arabic_syntax_evaluation_helpers.oracle_helpers import (
        independent_certificate, validate_answer_certificates,
    )
    from arabic_syntax_evaluation_helpers.runner import run
finally:
    sys.path.pop(0)


class ReviewDefectRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads((DATA / "first_results.json").read_text())
        cls.manual = {row["source_text_sha256"]: row["expected"] for row in
                      json.loads((DATA / "manual_oracle.json").read_text())["records"]}
        cls.sources = {
            row["id"]: {e["source_id"]: e["text"] for e in row["events"] if e["op"] == "add"}
            for row in json.loads((DATA / "scope_episodes.json").read_text())["cases"]
        }
        case = next(r for r in cls.reference["episodes"] if r["id"] == "s07")
        answer = next(e["result"] for e in case["events"] if e["op"] == "query")
        cls.certificate = answer["proofs"]["query"]

    def replay(self, certificate, *, active=None):
        return independent_certificate(certificate, active or self.sources["s07"],
                                       "eval_s07", self.manual)

    def assert_replay_rejected(self, certificate, *, active=None):
        # Malformed bytes/containers must cross a validation-error boundary,
        # not leak a KeyError that the old runner interpreted as ordinary deferral.
        with self.assertRaises(AssertionError):
            self.replay(certificate, active=active)

    def mutated_run(self, transform, *, scope="eval_s07"):
        original_query = SemanticKernel.query

        def changed_query(kernel, *args, **kwargs):
            answer = original_query(kernel, *args, **kwargs).as_dict()
            if kwargs.get("scope") == scope:
                transform(answer)
            return SimpleNamespace(as_dict=lambda: answer)

        with patch.object(SemanticKernel, "query", changed_query):
            result = run(DATA, "arabic")
        case = next(r for r in result["episodes"] if "eval_" + r["id"] == scope)
        return result, case

    def assert_runner_rejected(self, transform, *, scope="eval_s07"):
        result, case = self.mutated_run(transform, scope=scope)
        failure = {key: case[key] for key in ("id", "independent_certificates_pass",
                                              "admitted_claims_licensed", "complete_episode")}
        self.assertFalse(case["independent_certificates_pass"], failure)
        self.assertFalse(case["admitted_claims_licensed"], failure)
        self.assertFalse(case["complete_episode"], failure)
        gate = regression_gate(result, snapshot="local-review-test", reference=self.reference)
        self.assertFalse(gate["passed"], gate)

    def test_declared_relation_reaches_question_context(self):
        kernel = SemanticKernel(language_id=LANGUAGE_ID)
        self.assertTrue(kernel.add_source("علاقة يراجع. سالم يراجع تقرير.",
                                          source_id="relation", scope="review").accepted)
        answer = kernel.query("هل سالم يراجع تقرير؟", scope="review").as_dict()
        self.assertEqual(answer["status"], "SUPPORTED")
        self.assertEqual(answer["query"], {
            "predicate": "يراجع", "args": ["سالم", "تقرير"], "positive": True,
        })
        self.assertTrue(kernel.verify_certificate(answer["proofs"]["query"])["accepted"])

    def test_published_valid_witness_is_still_accepted(self):
        self.assertTrue(self.replay(deepcopy(self.certificate)))

    def test_rule_requires_complete_statement_not_a_correct_hash_fragment(self):
        certificate = deepcopy(self.certificate)
        clause = certificate["steps"][-1]["clause"]
        raw = self.sources["s07"]["r"].encode("utf-8")
        # U+0625 is a valid two-byte character and really occurs at this offset.
        # Both hashes are correct. It still does not state this implication.
        clause["span"].update(start=0, end=2, span_sha256=sha256(raw[:2]).hexdigest())
        clause["component_spans"] = []
        self.bind_clause_number(clause)
        self.assert_replay_rejected(certificate)

    def test_rule_role_components_cannot_be_dropped_reordered_or_duplicated(self):
        for name, transform in (
            ("omit", lambda parts: parts[1:]),
            ("reverse", lambda parts: list(reversed(parts))),
            ("duplicate", lambda parts: [parts[0], *parts]),
        ):
            with self.subTest(name=name):
                certificate = deepcopy(self.certificate)
                clause = certificate["steps"][-1]["clause"]
                clause["component_spans"] = transform(clause["component_spans"])
                self.assert_replay_rejected(certificate)

    @staticmethod
    def span(raw, source_id, start, end):
        """Hash explicit byte offsets; do not infer any meaning or parse roles."""
        data = raw.encode("utf-8")
        return {"source_id": source_id, "source_sha256": sha256(data).hexdigest(),
                "start": start, "end": end, "span_sha256": sha256(data[start:end]).hexdigest()}

    @staticmethod
    def bind_clause_number(clause):
        """Encode fixture metadata by the public format, never infer its meaning.

        Keeping this checksum correct isolates statement/binding validation
        from the easier check for an unchanged number on changed source bytes.
        """
        payload = {key: clause[key] for key in ("scope", "source_id", "source_sha256",
                                                "span", "analysis_id")}
        payload["semantic_version"] = "nabt.signed-horn.v1"
        if clause["kind"] == "fact":
            payload["atom"] = clause["atom"]
        else:
            payload.update(body=clause["body"], head=clause["head"], kind=clause["rule_kind"])
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        clause["clause_id"] = sha256(raw).hexdigest()

    def test_rule_cannot_cite_a_different_complete_statement_in_the_same_source(self):
        raw = "إذا ريان هو حاضر فإن ريان هو شاهد. ريان هو حاضر."
        checksum = sha256(raw.encode("utf-8")).hexdigest()
        fact = {"predicate": "حاضر", "args": ["ريان"], "positive": True}
        head = {"predicate": "شاهد", "args": ["ريان"], "positive": True}
        rule = {"body": [fact], "head": head}
        # Literal independently reviewed offsets and roles, without the reader
        # or the oracle's annotation constructor deriving the expected spans.
        rule_roles = [(0, 6, "conditional"), (7, 15, "body.0.args.0"),
                      (16, 20, "body.copula"), (21, 29, "body.0.predicate"),
                      (30, 36, "consequence"), (37, 45, "head.args.0"),
                      (46, 50, "head.copula"), (51, 59, "head.predicate")]
        fact_roles = [(61, 69, "facts.0.args.0"), (70, 74, "copula"),
                      (75, 83, "facts.0.predicate")]
        def annotation(start, end, roles, facts, rules):
            return {"start": start, "end": end, "facts": facts, "rules": rules,
                    "rule_kinds": ["explicit_rule"] * len(rules),
                    "components": [{"start": a, "end": b, "roles": [role]}
                                   for a, b, role in roles]}
        statements = [annotation(0, 59, rule_roles, [], [rule]),
                      annotation(61, 83, fact_roles, [fact], [])]
        oracle = {checksum: {"raw_text": raw, "source_text_sha256": checksum,
                             "statements": statements}}
        manual = {checksum: {"facts": [fact], "rules": [rule]}}
        active = {"combined": raw}
        certificate = deepcopy(self.certificate)
        for step, start, end, roles in ((certificate["steps"][0], 61, 83, fact_roles),
                                        (certificate["steps"][1], 0, 59, rule_roles)):
            clause = step["clause"]
            clause.update(source_id="combined", source_sha256=checksum,
                          span=self.span(raw, "combined", start, end),
                          component_spans=[self.span(raw, "combined", a, b) for a, b, _ in roles])
            self.bind_clause_number(clause)
        self.assertEqual(raw.encode()[61:83].decode(), "ريان هو حاضر")
        self.assertTrue(independent_certificate(certificate, active, "eval_s07", manual,
                                                statement_oracle=oracle))
        # This is a complete, correctly hashed source statement with valid
        # components. It licenses the fact, not the implication from sentence 1.
        certificate["steps"][1]["clause"]["span"] = self.span(raw, "combined", 61, 83)
        certificate["steps"][1]["clause"]["component_spans"] = [
            self.span(raw, "combined", a, b) for a, b, _ in fact_roles]
        self.bind_clause_number(certificate["steps"][1]["clause"])
        with self.assertRaises(AssertionError):
            independent_certificate(certificate, active, "eval_s07", manual, statement_oracle=oracle)

    def test_variable_rule_requires_exact_ground_binding_and_safe_head(self):
        # This is a proof-checker fixture for the manual s08 theory. The runtime
        # still defers its bare universal source; this is not a coverage result.
        active = self.sources["s08"]
        fact = {"predicate": "قارئ", "args": ["يامن"], "positive": True}
        head = {"predicate": "متفحص", "args": ["يامن"], "positive": True}
        certificate = deepcopy(self.certificate)
        certificate.update(scope="eval_s08", query=head, program_sha256="0" * 64)
        rule = {"body": [{**fact, "args": ["?x"]}], "head": {**head, "args": ["?x"]}}
        for index, (source_id, end, components, atom) in enumerate((
            ("a", 22, [(0, 8), (9, 13), (14, 22)], fact),
            ("r", 24, [(0, 4), (5, 13), (14, 24)], head),
        )):
            raw = active[source_id]
            step = certificate["steps"][index]
            step["atom"] = atom
            clause = step["clause"]
            clause.update(scope="eval_s08", source_id=source_id,
                          source_sha256=sha256(raw.encode()).hexdigest(),
                          span=self.span(raw, source_id, 0, end),
                          component_spans=[self.span(raw, source_id, a, b) for a, b in components],
                          clause_id=sha256(("manual-s08-clause-" + str(index)).encode()).hexdigest(),
                          analysis_id=sha256(("manual-s08-analysis-" + str(index)).encode()).hexdigest())
            if index == 0:
                clause["atom"] = fact
            else:
                clause.update(**rule, rule_kind="universal")
                step["binding"] = {"?x": "يامن"}
            self.bind_clause_number(clause)
        self.assertTrue(independent_certificate(certificate, active, "eval_s08", self.manual))
        for label, binding in (
            ("missing", {}), ("extra", {"?x": "يامن", "?extra": "يامن"}),
            ("variable-value", {"?x": "?other"}), ("empty-value", {"?x": ""}),
            ("boolean-value", {"?x": True}), ("constant-key", {"?x": "يامن", "يامن": "يامن"}),
        ):
            with self.subTest(binding=label):
                changed = deepcopy(certificate)
                changed["steps"][1]["binding"] = binding
                with self.assertRaises(AssertionError):
                    independent_certificate(changed, active, "eval_s08", self.manual)
        changed = deepcopy(certificate)
        changed["steps"][1]["clause"]["head"]["args"] = ["?unbound"]
        self.bind_clause_number(changed["steps"][1]["clause"])
        with self.assertRaises(AssertionError):
            independent_certificate(changed, active, "eval_s08", self.manual)

    def test_ground_rule_cannot_bind_a_constant_even_to_itself(self):
        certificate = deepcopy(self.certificate)
        certificate["steps"][-1]["binding"] = {"ريان": "ريان"}
        self.assert_replay_rejected(certificate)

    def test_bool_reference_and_conclusion_remain_invalid(self):
        # Already rejected at b6ba0c6; preserve the boundary without crediting
        # the new implementation for discovering or repairing it.
        certificate = deepcopy(self.certificate)
        certificate["steps"][-1]["premises"] = [False]
        self.assert_replay_rejected(certificate)
        certificate = deepcopy(self.certificate)
        certificate["conclusion"] = True
        self.assert_replay_rejected(certificate)

    def test_constant_retargeting_rejected_by_both_independent_and_production_checks(self):
        kernel = SemanticKernel(language_id=LANGUAGE_ID)
        active = dict(self.sources["s07"], b=self.sources["s02"]["a"])
        for source_id, text in active.items():
            self.assertTrue(kernel.add_source(text, source_id=source_id, scope="eval_s07").accepted)
        certificate = deepcopy(kernel.query("هل ريان هو شاهد؟", scope="eval_s07").as_dict()["proofs"]["query"])
        other = kernel.query("هل أثير هو حاضر؟", scope="eval_s07").as_dict()["proofs"]["query"]
        self.assertTrue(kernel.verify_certificate(certificate)["accepted"])
        self.assertTrue(kernel.verify_certificate(other)["accepted"])
        certificate["steps"][0] = deepcopy(other["steps"][0])
        certificate["steps"][-1]["binding"] = {"ريان": "أثير"}
        certificate["steps"][-1]["atom"]["args"] = ["أثير"]
        certificate["query"]["args"] = ["أثير"]
        self.assert_replay_rejected(certificate, active=active)
        verdict = kernel.verify_certificate(certificate)
        self.assertFalse(verdict["accepted"])
        self.assertEqual(verdict["reason"], "INVALID_CERTIFICATE")

    def test_production_clause_identity_already_rejects_partial_statement(self):
        kernel = SemanticKernel(language_id=LANGUAGE_ID)
        for source_id, text in self.sources["s07"].items():
            self.assertTrue(kernel.add_source(text, source_id=source_id, scope="eval_s07").accepted)
        certificate = deepcopy(kernel.query("هل ريان هو شاهد؟", scope="eval_s07").as_dict()["proofs"]["query"])
        clause = certificate["steps"][-1]["clause"]
        raw = self.sources["s07"]["r"].encode("utf-8")
        clause["span"].update(start=0, end=2, span_sha256=sha256(raw[:2]).hexdigest())
        clause["component_spans"] = []
        verdict = kernel.verify_certificate(certificate)
        self.assertFalse(verdict["accepted"])
        self.assertEqual(verdict["reason"], "STALE_OR_FORGED_CLAUSE")

    def test_supported_answer_requires_present_nonnull_query_certificate(self):
        for name, transform in (
            ("empty", lambda out: out.update(proofs={})),
            ("null", lambda out: out.update(proofs={"query": None})),
            ("missing", lambda out: out.pop("proofs")),
        ):
            with self.subTest(name=name):
                self.assert_runner_rejected(transform)

    def test_valid_premise_proof_is_not_an_answer_to_a_different_question(self):
        def replace_with_premise(out):
            certificate = out["proofs"]["query"]
            certificate["steps"] = certificate["steps"][:1]
            certificate["conclusion"] = 0
            certificate["query"] = deepcopy(certificate["steps"][0]["atom"])

        # The shortened certificate is independently valid for حاضر(ريان).
        # It is the outer answer contract that must reject it for شاهد(ريان).
        certificate = deepcopy(self.certificate)
        certificate["steps"] = certificate["steps"][:1]
        certificate["conclusion"] = 0
        certificate["query"] = deepcopy(certificate["steps"][0]["atom"])
        self.assertTrue(self.replay(certificate))
        self.assert_runner_rejected(replace_with_premise)

    def test_supported_status_does_not_accept_only_signed_evidence(self):
        def use_signed(out):
            out["proofs"]["query"]["proof_kind"] = "signed"
        self.assert_runner_rejected(use_signed)

    def test_clean_proof_checks_active_opposition_even_when_not_cited(self):
        negative_text = "ليس ريان هو حاضر."
        active = dict(self.sources["s07"], opposition=negative_text)
        manual = deepcopy(self.manual)
        manual[sha256(negative_text.encode()).hexdigest()] = {
            "facts": [{"predicate": "حاضر", "args": ["ريان"], "positive": False}],
            "rules": [],
        }
        certificate = deepcopy(self.certificate)
        with self.assertRaises(AssertionError):
            independent_certificate(certificate, active, "eval_s07", manual)
        # A signed derivation still describes the positive derivation. Its
        # existence must not be confused with an uncontested supported answer.
        certificate["proof_kind"] = "signed"
        self.assertTrue(independent_certificate(certificate, active, "eval_s07", manual))

    def test_answer_certificate_is_bound_to_external_query_polarity(self):
        case = next(r for r in self.reference["episodes"] if r["id"] == "s07")
        answer = deepcopy(next(e["result"] for e in case["events"] if e["op"] == "query"))
        target = {"predicate": "شاهد", "args": ["ريان"], "positive": False}
        answer["query"] = target
        # Every certificate field still describes the valid positive proof;
        # the externally supplied negative question requires another proof.
        with self.assertRaises(AssertionError):
            validate_answer_certificates(answer, self.sources["s07"], "eval_s07", self.manual,
                                         expected_query=target)

    def test_refuted_status_requires_opposite_certificate(self):
        self.assert_runner_rejected(lambda out: out.update(proofs={}), scope="eval_s05")

    def test_missing_fields_become_certificate_validation_failure(self):
        for path in (("steps",), ("steps", 0, "clause", "source_id")):
            with self.subTest(path=path):
                certificate = deepcopy(self.certificate)
                node = certificate
                for key in path[:-1]:
                    node = node[key]
                del node[path[-1]]
                self.assert_replay_rejected(certificate)

    def test_malformed_evidence_fails_safety_even_when_case_was_already_uncovered(self):
        original = next(r for r in self.reference["episodes"] if r["id"] == "s03")
        self.assertFalse(original["complete_episode"])
        for missing in ("steps", "clause_source_id"):
            def inject(out):
                bad = {"scope": "eval_s03", "world_truth": "NOT_ESTABLISHED"}
                if missing == "clause_source_id":
                    bad.update(steps=[{"clause": {}}], conclusion=0)
                out["proofs"] = {"query": bad}
            with self.subTest(missing=missing):
                self.assert_runner_rejected(inject, scope="eval_s03")

    def test_unexpected_checker_exception_is_not_ordinary_query_noncoverage(self):
        # Exercise the exception boundary itself, even if all known malformed
        # certificate shapes are now caught earlier by typed validation.
        for exception_type in (KeyError, TypeError, ValueError, RuntimeError):
            def broken_checker(*args, **kwargs):
                if args[2] == "eval_s03":
                    raise exception_type("local review fixture")
                return validate_answer_certificates(*args, **kwargs)
            with self.subTest(error=exception_type.__name__):
                with patch("arabic_syntax_evaluation_helpers.runner.validate_answer_certificates", broken_checker):
                    result = run(DATA, "arabic")
                case = next(row for row in result["episodes"] if row["id"] == "s03")
                self.assertFalse(case["independent_certificates_pass"])
                self.assertFalse(case["admitted_claims_licensed"])
                event = next(row for row in case["events"] if row["op"] == "query")
                self.assertEqual(event["error_type"], exception_type.__name__)
                self.assertEqual(event["failure_stage"], "returned_answer_validation")
                self.assertFalse(regression_gate(result, snapshot="local-review-test",
                                                 reference=self.reference)["passed"])


if __name__ == "__main__":
    unittest.main()
