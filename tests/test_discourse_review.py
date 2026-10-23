"""Frozen, authored regression checks of seven identified discourse risks.

These cases were authored after a source/code review. They are not a blind
corpus evaluation and do not alter the independently authored v1 cases.
"""

from copy import deepcopy
from hashlib import sha256
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nabt.cli import main
from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import ask_discourse
from nabt.discourse_reader import read_discourse
from nabt.discourse_context import MAX_CONTEXT_BYTES, MAX_REPORT_BYTES
from nabt.word_reader import MAX_SOURCE_BYTES


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "discourse"
CASES = json.loads((EVIDENCE / "post_review_cases.json").read_text(encoding="utf-8"))["cases"]
OBSERVATIONS = {}


class DiscourseReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        freeze = json.loads((EVIDENCE / "post_review_freeze.json").read_text(encoding="utf-8"))
        for record in freeze["frozen_inputs"]:
            raw = (ROOT / record["path"]).read_bytes()
            if len(raw) != record["bytes"] or sha256(raw).hexdigest() != record["sha256"]:
                raise AssertionError("Frozen review input changed: " + record["path"])
        cls.training = (EVIDENCE / "post_review_training.tsv").read_bytes()
        cls.model = learn_qac_lexicon(cls.training, source_id="authored_post_review")
        cls.context = json.loads((EVIDENCE / "post_review_context.json").read_text(encoding="utf-8"))

    def _context(self, case):
        context = deepcopy(self.context)
        if case.get("context") == "unknown_zayd_gender":
            next(e for e in context["entities"] if e["id"] == "zayd")["gender"] = "unknown"
        return context

    def _cli(self, case):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source, report = directory / "text.txt", directory / "report.json"
            corpus, context = directory / "training.tsv", directory / "context.json"
            source.write_text("زَيْدٌ عَالِمٌ.", encoding="utf-8")
            report.write_bytes(b"{}")
            corpus.write_bytes(self.training)
            context.write_text(json.dumps(self.context, ensure_ascii=False), encoding="utf-8")
            scenario = case["scenario"]
            if scenario == "oversized_source":
                source.write_bytes(b"x" * (MAX_SOURCE_BYTES + 1))
            elif scenario == "oversized_report":
                report.write_bytes(b" " * (MAX_REPORT_BYTES + 1))
            elif scenario == "oversized_context":
                context.write_bytes(b" " * (MAX_CONTEXT_BYTES + 1))
            elif scenario != "valid_read":
                raise AssertionError("Unknown frozen CLI scenario")
            arguments = [case["command"]]
            if case["command"] == "verify-discourse":
                arguments += [str(report), "--source", str(source)]
            else:
                arguments += [str(source)]
            arguments += ["--context", str(context), "--qac", str(corpus)]
            path_open, builtin_open = Path.open, open
            source_reads, corpus_opens = [], []

            class ObservedSource(io.BytesIO):
                def read(self, size=-1):
                    source_reads.append(size)
                    return super().read(size)

            payload = source.read_bytes()

            def opening(path, *args, **kwargs):
                return ObservedSource(payload) if path == source else path_open(path, *args, **kwargs)

            def opening_builtin(path, *args, **kwargs):
                if path == corpus:
                    corpus_opens.append(True)
                return builtin_open(path, *args, **kwargs)

            out, err = io.StringIO(), io.StringIO()
            with patch.object(Path, "open", opening), patch("builtins.open", opening_builtin), \
                    patch("nabt.corpus_evidence.learn_qac_lexicon", wraps=learn_qac_lexicon) as learner, \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = main(arguments)
            if out.getvalue() and err.getvalue():
                raise AssertionError("CLI used two result channels")
            result = json.loads(out.getvalue() or err.getvalue())
            return {"exit_code": code, "status": result["status"], "code": result.get("code"),
                    "learner_calls": learner.call_count, "corpus_opens": len(corpus_opens),
                    "source_reads": source_reads,
                    "claim_count": len(result.get("claims", []))}

    def _observe(self, case):
        if case["api"] == "cli":
            return self._cli(case)
        arguments = {"lexical_model": self.model, "context": self._context(case)}
        if case["api"] == "ask":
            report = ask_discourse(case["text"], case["question"], **arguments)
            return {"status": report["status"], "proof_count": len(report.get("proofs", [])),
                    "query": report.get("query")}
        report = read_discourse(case["text"], **arguments)
        return {"status": report["status"], "claim_count": len(report["claims"]),
                "forces": [c["force"] for c in report["clauses"]],
                "claim_tenses": [c["tense"] for c in report["claims"]],
                "assertion_allowed_count": sum(a["assertion_allowed"]
                    for c in report["clauses"] for a in c["analyses"])}

    def _check(self, case):
        observed = self._observe(case)
        OBSERVATIONS[case["id"]] = observed
        expected = case["expect"]
        self.assertIn(observed["status"], expected["statuses"], observed)
        if expected.get("no_claims"):
            self.assertEqual(observed["claim_count"], 0, observed)
        if expected.get("claims_if_licensed"):
            if observed["status"] == "LICENSED_DISCOURSE":
                self.assertGreater(observed["claim_count"], 0, observed)
            else:
                self.assertEqual(observed["claim_count"], 0, observed)
        if "minimum_claims" in expected:
            self.assertGreaterEqual(observed["claim_count"], expected["minimum_claims"], observed)
        if expected.get("nonassertive"):
            self.assertNotIn("ASSERT", observed["forces"], observed)
            self.assertEqual(observed["assertion_allowed_count"], 0, observed)
        if "claim_tense" in expected:
            self.assertTrue(all(t == expected["claim_tense"] for t in observed["claim_tenses"]), observed)
        if expected.get("no_support"):
            self.assertEqual(observed["proof_count"], 0, observed)
        if expected.get("support"):
            self.assertGreater(observed["proof_count"], 0, observed)
        if case["api"] == "cli":
            self.assertEqual(observed["exit_code"], expected["exit_code"], observed)
            if expected.get("resource_before_corpus"):
                self.assertEqual(observed["code"], "RESOURCE_LIMIT", observed)
                self.assertEqual(observed["learner_calls"], 0, observed)
                self.assertEqual(observed["corpus_opens"], 0, observed)
            if case["scenario"] == "oversized_source":
                self.assertEqual(observed["source_reads"], [MAX_SOURCE_BYTES + 1], observed)
            elif case["scenario"] in ("oversized_report", "oversized_context"):
                self.assertEqual(observed["source_reads"], [], observed)


def _case_test(case):
    def test(self):
        self._check(case)
    test.__doc__ = case["rationale"]
    return test


for _case in CASES:
    setattr(DiscourseReviewTests, "test_" + _case["id"], _case_test(_case))


if __name__ == "__main__":
    unittest.main()
