"""Independent semantic truth-table oracle and adversarial certificate tests.

No checker result is obtained from the Python proposer. The Lean executable
must be built for the integration class; CI runs it explicitly without skips.
"""
from copy import deepcopy
from itertools import product
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.verified_reading import propose

ROOT = Path(__file__).resolve().parents[1]
BINARY = Path(os.environ.get("NABT_VERIFIED_READING", ROOT / "formal/.lake/build/bin/verifiedReading"))
if "NABT_VERIFIED_READING" in os.environ and not BINARY.is_file():
    raise RuntimeError("NABT_VERIFIED_READING must point to the built executable")
BASE = "سالم هو حكيم.\nإذا سالم هو حكيم فإن سالم هو عالم.\n"
QUESTION = "هل سالم هو عالم؟\n"


class ProposalBoundaries(unittest.TestCase):
    def test_proposal_has_no_authority_bit(self):
        c = propose(BASE.encode(), QUESTION.encode())
        self.assertNotIn("verified", c)
        self.assertEqual(c["source"]["text"], BASE)

    def test_not_a_general_reader_or_normalizer(self):
        for text in ["سالم حكيم.\n", "سالم هو حكيم. ", "كل حكيم هو عالم.\n",
                     "إذا ?x هو حكيم فإن ?x هو عالم.\n", "مفهوم حكيم.\n",
                     "سالم هو حكيم.\nهل سالم هو حكيم؟\n"]:
            with self.subTest(text=text), self.assertRaises(Exception):
                propose(text.encode(), QUESTION.encode())

    def test_limits_and_invalid_utf8(self):
        for raw in [b"x" * 65537, b"\xff"]:
            with self.assertRaises(Exception):
                propose(raw, QUESTION.encode())


@unittest.skipUnless(BINARY.is_file(), "build verifiedReading first")
class VerifiedExecution(unittest.TestCase):
    def run_certificate(self, text=BASE, question=QUESTION, certificate=None, **binding):
        c = certificate if certificate is not None else propose(text.encode(), question.encode())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source").write_bytes(text.encode() if isinstance(text, str) else text)
            (root / "query").write_bytes(question.encode() if isinstance(question, str) else question)
            (root / "cert").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
            p = subprocess.run([str(BINARY), str(root / "source"), str(root / "query"),
                                str(root / "cert"), binding.get("identity", "text"),
                                binding.get("revision", "1"), binding.get("scope", "default")],
                               text=True, capture_output=True, timeout=20)
            result = json.loads(p.stdout)
            self.assertEqual(p.returncode == 0, result["verified"], p.stderr)
            if not result["verified"]:
                self.assertNotIn("status", result)  # rejection is never UNKNOWN/DEFER
            return result

    def test_chain_and_exact_source_output(self):
        r = self.run_certificate()
        self.assertEqual(r["status"], "SUPPORTED")
        self.assertEqual(r["source_text"], BASE)
        self.assertEqual(r["query_text"], QUESTION)
        self.assertFalse(r["all_arabic_complete"])
        self.assertFalse(r["world_truth_established"])

    def test_all_five_verdicts(self):
        cases = [
            ("سالم هو عالم.\n", "SUPPORTED"),
            ("ليس سالم هو عالم.\n", "REFUTED"),
            ("سالم هو عالم.\nليس سالم هو عالم.\n", "CONFLICT"),
            ("سالم هو حكيم.\n", "UNKNOWN"),
            (BASE + "ليس سالم هو حكيم.\n", "DEFER"),
            (BASE + "ليس سالم هو حكيم.\nسالم هو عالم.\n", "SUPPORTED"),
        ]
        for text, expected in cases:
            with self.subTest(expected=expected, text=text):
                self.assertEqual(self.run_certificate(text)["status"], expected)

    def test_relation_order_negated_question_and_multi_premise(self):
        text = "سالم يحب سهيل.\nسالم هو حكيم.\nإذا سالم يحب سهيل و سالم هو حكيم فإن سهيل هو عالم.\n"
        for query, status in [("هل سهيل هو عالم؟\n", "SUPPORTED"),
                              ("هل سهيل يحب سالم؟\n", "UNKNOWN"),
                              ("هل ليس سالم يحب سهيل؟\n", "REFUTED")]:
            self.assertEqual(self.run_certificate(text, query)["status"], status)

    def test_changed_expected_binding_rejects_stale_certificate(self):
        c = propose(BASE.encode(), QUESTION.encode())
        for kwargs in [{"text": BASE + "ليس سالم هو عالم.\n"},
                       {"question": "هل سالم هو حكيم؟\n"}, {"identity": "other"},
                       {"revision": "2"}, {"scope": "other"}]:
            with self.subTest(kwargs=kwargs):
                self.assertFalse(self.run_certificate(certificate=c, **kwargs)["verified"])

    def test_attack_matrix(self):
        original = propose(BASE.encode(), QUESTION.encode())
        mutations = [
            lambda c: c["clauses"].pop(),
            lambda c: c["clauses"][0]["atom"].update(positive=False),
            lambda c: c["clauses"][1]["body"].clear(),
            lambda c: c["query"].update(predicate="حكيم"),
            lambda c: c["steps"].reverse(),
            lambda c: c["steps"][0].update(index=True),
            lambda c: c["steps"][0].update(index=999),
            lambda c: c["known"][0].update(predicate="مخترع"),
            lambda c: c["clean_steps"].clear(),
            lambda c: c["clean_known"].clear(),
            lambda c: c.update(law_id="caller-law"),
            lambda c: c.update(verified=True),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(attack=i):
                c = deepcopy(original)
                mutate(c)
                self.assertFalse(self.run_certificate(certificate=c)["verified"])

    def test_omitted_derivation_cannot_forge_unknown(self):
        c = propose(BASE.encode(), QUESTION.encode())
        # The shorter trace is individually sound, but is not closed.
        for known, steps in [("known", "steps"), ("clean_known", "clean_steps")]:
            c[known] = c[known][:1]
            c[steps] = c[steps][:1]
        self.assertFalse(self.run_certificate(certificate=c)["verified"])

    def test_omitted_conflict_cannot_forge_supported(self):
        text = BASE + "ليس سالم هو حكيم.\n"
        c = propose(text.encode(), QUESTION.encode())
        c["known"] = [a for a in c["known"] if a["positive"]]
        c["steps"] = [s for s in c["steps"] if s != {"kind": "fact", "index": 1}]
        self.assertFalse(self.run_certificate(text=text, certificate=c)["verified"])

    def test_rule_only_cycle_has_no_fact_ancestor(self):
        text = "إذا سالم هو حكيم فإن سالم هو عالم.\nإذا سالم هو عالم فإن سالم هو حكيم.\n"
        self.assertEqual(self.run_certificate(text)["status"], "UNKNOWN")

    def test_raw_byte_and_budget_failures_are_not_linguistic_results(self):
        c = propose(BASE.encode(), QUESTION.encode())
        for raw in [b"\xff", BASE.encode() + b"\x00"]:
            self.assertFalse(self.run_certificate(text=raw, certificate=c)["verified"])
        result = self.run_certificate(text=b"x" * 65537, certificate=c)
        self.assertEqual(result["error"], "RESOURCE_LIMIT")

    def test_exhaustive_model_oracle(self):
        # 31 nonempty source programs. Oracle enumerates every Boolean valuation; it
        # neither uses saturation nor production replay/renderer functions.
        # Positive and explicit-negative atoms are independent propositions.
        lines = ["سالم هو حكيم.\n", "ليس سالم هو حكيم.\n",
                 "سالم هو عالم.\n", "إذا سالم هو حكيم فإن سالم هو عالم.\n",
                 "إذا سالم هو عالم فإن ليس سالم هو حكيم.\n"]
        for enabled in product([False, True], repeat=5):
            if not any(enabled):
                continue
            text = "".join(line for line, use in zip(lines, enabled) if use)
            models = [v for v in product([False, True], repeat=3)
                      if (not enabled[0] or v[0]) and (not enabled[1] or v[1])
                      and (not enabled[2] or v[2])
                      and (not enabled[3] or not v[0] or v[2])
                      and (not enabled[4] or not v[2] or v[1])]
            entailed = [all(v[i] for v in models) for i in range(3)]
            # Separate model enumeration for the consistent subtheory.
            conflict = entailed[0] and entailed[1]
            clean_enabled = [enabled[0] and not conflict,
                             enabled[1] and not conflict, enabled[2],
                             enabled[3] and not conflict, enabled[4] and not conflict]
            clean_models = [v for v in product([False, True], repeat=3)
                            if (not clean_enabled[0] or v[0])
                            and (not clean_enabled[1] or v[1])
                            and (not clean_enabled[2] or v[2])
                            and (not clean_enabled[3] or not v[0] or v[2])
                            and (not clean_enabled[4] or not v[2] or v[1])]
            clean_entailed = [all(v[i] for v in clean_models) for i in range(3)]
            for query, pos, neg in [(QUESTION, 2, None),
                                    ("هل سالم هو حكيم؟\n", 0, 1),
                                    ("هل ليس سالم هو حكيم؟\n", 1, 0)]:
                bits = [entailed[pos], entailed[neg] if neg is not None else False,
                        clean_entailed[pos], clean_entailed[neg] if neg is not None else False]
                expected = ("CONFLICT" if bits[0] and bits[1] else "SUPPORTED" if bits[2]
                            else "REFUTED" if bits[3] else "DEFER" if bits[0] or bits[1]
                            else "UNKNOWN")
                with self.subTest(enabled=enabled, query=query):
                    result = self.run_certificate(text, query)
                    self.assertEqual([result[k] for k in
                        ["positive", "negative", "clean_positive", "clean_negative"]], bits)
                    self.assertEqual(result["status"], expected)


if __name__ == "__main__":
    unittest.main()
