"""Independent finite-model and adversarial checks for native text semantics."""

from copy import deepcopy
from dataclasses import replace
from itertools import product
import unittest

from nabt.errors import NabtError
from nabt.semantics import (SemanticKernel, SemanticBudget, atom_number, decode_atom_number,
                            SUPPORTED, REFUTED, CONFLICT, UNKNOWN, OUT_OF_SCOPE, DEFER)
from nabt.text_ir import Atom, Fact
from nabt.text_reader import parse_document, parse_query


class SemanticTests(unittest.TestCase):
    def kernel(self, text, source_id="theory", scope="default", **limits):
        kernel = SemanticKernel(budget=SemanticBudget(**limits))
        admission = kernel.add_source(text, source_id=source_id, scope=scope)
        self.assertTrue(admission.accepted, admission.as_dict())
        return kernel

    def test_fresh_definitions_generalize_and_equivalence_is_explicit(self):
        for index in range(12):
            left, right, whole, name = (f"صفة{index}أ", f"صفة{index}ب", f"نوع{index}", f"فرد{index}")
            text = f"تعريف {whole} هو {left} و {right}. {name} هو {left}. {name} هو {right}."
            kernel = self.kernel(text)
            result = kernel.query(f"هل {name} هو {whole}؟")
            self.assertEqual(result.status, SUPPORTED)
            self.assertTrue(kernel.verify_certificate(result.proofs["query"])["accepted"])
            # A definition alone does not instantiate a new individual.
            self.assertEqual(kernel.query(f"هل جديد{index} هو {whole}؟").status, UNKNOWN)
            kernel = self.kernel(f"تعريف {whole} هو {left} و {right}. {name} هو {whole}.")
            self.assertEqual(kernel.query(Atom(left, (name,))).status, SUPPORTED)
            self.assertEqual(kernel.query(Atom(right, (name,))).status, SUPPORTED)

    def test_signatures_scope_and_same_scope_joint_definitions(self):
        kernel = self.kernel("تعريف معين هو أول. شخص هو معين.", scope="أ")
        self.assertTrue(kernel.add_source("تعريف معين هو ثان.", source_id="next", scope="أ").accepted)
        self.assertEqual(kernel.query("هل شخص هو ثان؟", scope="أ").status, SUPPORTED)
        self.assertEqual(kernel.query("هل شخص هو ثان؟", scope="ب").status, OUT_OF_SCOPE)
        self.assertTrue(kernel.add_source("مفهوم ثان.", source_id="other", scope="ب").accepted)
        self.assertEqual(kernel.query("هل شخص هو ثان؟", scope="ب").status, UNKNOWN)
        before = kernel.snapshot()
        bad = kernel.add_source("علاقة أول.", source_id="bad", scope="أ")
        self.assertFalse(bad.accepted)
        self.assertEqual(kernel.snapshot(), before)
        self.assertTrue(kernel.add_source("مفهوم أول.", source_id="duplicate", scope="أ").accepted)
        with self.assertRaises(NabtError):
            kernel.query(parse_query("هل شخص هو أول؟", scope="أ"), scope="ب")

    def test_relation_joins_repeated_variables_and_signed_antecedents(self):
        kernel = self.kernel(
            "آدم يعرف باسل. باسل يعرف جابر. آدم يعرف آدم. ليس جابر هو غائب. "
            "إذا ?س يعرف ?ص و ?ص يعرف ?ع فإن ?س يصل ?ع. "
            "إذا ?س يعرف ?س فإن ?س هو ذاتي. "
            "إذا ?س يصل ?ع و ليس ?ع هو غائب فإن ?س هو مستعد."
        )
        self.assertEqual(kernel.query("هل آدم يصل جابر؟").status, SUPPORTED)
        self.assertEqual(kernel.query("هل جابر يصل آدم؟").status, UNKNOWN)
        self.assertEqual(kernel.query("هل آدم هو ذاتي؟").status, SUPPORTED)
        self.assertEqual(kernel.query("هل باسل هو ذاتي؟").status, UNKNOWN)
        result = kernel.query("هل آدم هو مستعد؟")
        self.assertEqual(result.status, SUPPORTED)
        self.assertTrue(kernel.verify_certificate(result.proofs["query"])["accepted"])

    def test_negation_is_explicit_and_has_no_contraposition(self):
        kernel = self.kernel("كل حاضر هو معروف. ليس نادر هو معروف. مفهوم مجهول.")
        self.assertEqual(kernel.query("هل نادر هو حاضر؟").status, UNKNOWN)
        self.assertEqual(kernel.query("هل نادر هو معروف؟").status, REFUTED)
        self.assertEqual(kernel.query("هل ليس نادر هو معروف؟").status, SUPPORTED)
        self.assertEqual(kernel.query("هل نادر هو مجهول؟").status, UNKNOWN)
        self.assertEqual(kernel.query("هل نادر هو جديد؟").status, OUT_OF_SCOPE)

    def test_conflict_taints_descendants_but_clean_alternative_survives(self):
        kernel = self.kernel("اسم هو أصل. ليس اسم هو أصل. كل أصل هو تابع. كل تابع هو أخير.")
        self.assertEqual(kernel.query("هل اسم هو أصل؟").status, CONFLICT)
        tainted = kernel.query("هل اسم هو أخير؟")
        self.assertEqual((tainted.status, tainted.reason), (DEFER, "CONTESTED_PREMISES"))
        self.assertIn(Atom("أصل", ("اسم",)), tainted.contested_premises)
        self.assertTrue(kernel.add_source("اسم هو مستقل. كل مستقل هو تابع.", source_id="clean").accepted)
        answer = kernel.query("هل اسم هو أخير؟")
        self.assertEqual(answer.status, SUPPORTED)
        self.assertTrue(kernel.verify_certificate(answer.proofs["query"])["accepted"])
        # The independent clean branch also survives deleting the conflicted branch.
        self.assertTrue(kernel.remove_source("theory").accepted)
        self.assertEqual(kernel.query("هل اسم هو تابع؟").status, SUPPORTED)

    def test_clean_certificate_is_invalidated_by_new_conflict(self):
        kernel = self.kernel("نادر هو حاضر. كل حاضر هو مستعد.")
        cert = kernel.query("هل نادر هو مستعد؟").proofs["query"]
        kernel.add_source("ليس نادر هو حاضر.", source_id="opposition")
        report = kernel.verify_certificate(cert)
        self.assertFalse(report["accepted"])
        self.assertEqual(report["reason"], "CONTESTED_PREMISES")
        self.assertEqual(kernel.query("هل نادر هو مستعد؟").status, DEFER)
        kernel.remove_source("opposition")
        self.assertTrue(kernel.verify_certificate(cert)["accepted"])

    def test_missing_premises_are_grounded_and_do_not_propose_conflict(self):
        kernel = self.kernel("سمير هو مسجل. إذا ?س هو مسجل و ليس ?س هو غائب فإن ?س هو مؤهل.")
        result = kernel.query("هل سمير هو مؤهل؟")
        self.assertEqual(result.status, UNKNOWN)
        self.assertEqual(result.missing_premises[0]["atoms"], [Atom("غائب", ("سمير",), False).as_dict()])
        kernel.add_source("سمير هو غائب.", source_id="positive")
        result = kernel.query("هل سمير هو مؤهل؟")
        self.assertEqual(result.status, UNKNOWN)
        self.assertNotIn(Atom("غائب", ("سمير",), False).as_dict(),
                         [a for p in result.missing_premises for a in p["atoms"]])
        kernel.add_source("ليس سمير هو غائب.", source_id="negative")
        self.assertEqual(kernel.query("هل سمير هو مؤهل؟").reason, "CONTESTED_PREMISES")

    def test_definition_missing_components_and_recursive_cycles(self):
        kernel = self.kernel("تعريف كامل هو جزءأ و جزءب. فردأ هو جزءأ.")
        result = kernel.query("هل فردأ هو كامل؟")
        self.assertEqual(result.missing_premises[0]["atoms"], [Atom("جزءب", ("فردأ",)).as_dict()])
        kernel = self.kernel("كل أول هو ثان. كل ثان هو أول.")
        result = kernel.query("هل عابر هو أول؟")
        self.assertEqual(result.status, UNKNOWN)
        self.assertTrue(result.missing_premises)
        self.assertEqual(kernel.snapshot()["facts"], [])

    def test_missing_plans_are_counterfactually_clean_and_never_installed(self):
        kernel = self.kernel("إذا ?س هو أ و ليس ?س هو أ فإن ?س هو ب.")
        before = kernel.snapshot()
        result = kernel.query("هل سالم هو ب؟")
        self.assertEqual(result.status, UNKNOWN)
        # The contradictory antecedent pair cannot license a clean conclusion.
        self.assertEqual([p["atoms"] for p in result.missing_premises],
                         [[Atom("ب", ("سالم",)).as_dict()]])
        self.assertEqual(kernel.snapshot(), before)
        kernel = self.kernel(
            "سالم هو أ. إذا ?س هو أ و ?س هو ج فإن ?س هو ب. "
            "إذا ?س هو ج فإن ليس ?س هو أ. كل د هو ب."
        )
        before = kernel.snapshot()
        result = kernel.query("هل سالم هو ب؟")
        # Adding ج would indirectly create an أ/¬أ conflict; the independent
        # alternative د remains a sufficient completion.
        self.assertEqual([p["atoms"] for p in result.missing_premises],
                         [[Atom("د", ("سالم",)).as_dict()]])
        self.assertEqual(kernel.snapshot(), before)
        self.assertTrue(kernel.add_source("سالم هو د.", source_id="completion").accepted)
        self.assertEqual(kernel.query("هل سالم هو ب؟").status, SUPPORTED)
        kernel = self.kernel("إذا ?س هو أ فإن ليس ?س هو أ.")
        result = kernel.query("هل سالم هو أ؟")
        self.assertEqual(result.status, UNKNOWN)
        self.assertEqual(result.missing_premises, ())

    def test_source_admission_replays_raw_not_supplied_ir(self):
        original = parse_document("فارس هو شاهد.", source_id="source")
        forged = replace(original, facts=(replace(original.facts[0], atom=Atom("مكذوب", ("فارس",))),), residuals=())
        kernel = SemanticKernel()
        self.assertTrue(kernel.add_document(forged).accepted)
        self.assertEqual(kernel.query("هل فارس هو شاهد؟").status, SUPPORTED)
        self.assertEqual(kernel.query("هل فارس هو مكذوب؟").status, OUT_OF_SCOPE)
        unread = parse_document("ليلى هو شاهدة. هذه جملة", source_id="unread")
        before = kernel.snapshot()
        refused = kernel.add_document(replace(unread, residuals=()))
        self.assertFalse(refused.accepted)
        self.assertEqual(refused.status, DEFER)
        self.assertEqual(kernel.snapshot(), before)

    def test_retraction_replacement_and_alternate_sources(self):
        kernel = self.kernel("كل أول هو آخر.", source_id="rules")
        kernel.add_source("مروان هو أول.", source_id="one")
        kernel.add_source("مروان هو أول.", source_id="two")
        cert = kernel.query("هل مروان هو آخر؟").proofs["query"]
        chosen = cert["steps"][0]["clause"]["source_id"]
        self.assertFalse(kernel.add_source("مروان هو بديل.", source_id=chosen).accepted)
        self.assertTrue(kernel.remove_source(chosen).accepted)
        self.assertFalse(kernel.verify_certificate(cert)["accepted"])
        self.assertEqual(kernel.query("هل مروان هو آخر؟").status, SUPPORTED)
        other = "two" if chosen == "one" else "one"
        before = kernel.snapshot()
        self.assertFalse(kernel.replace_source("جملة ناقصة", source_id=other).accepted)
        self.assertEqual(kernel.snapshot(), before)
        revised = kernel.replace_source("ليس مروان هو أول.", source_id=other)
        self.assertTrue(revised.accepted)
        self.assertTrue(revised.removed_supports)
        self.assertEqual(kernel.query("هل مروان هو آخر؟").status, UNKNOWN)
        self.assertEqual(kernel.query("هل مروان هو أول؟").status, REFUTED)

    def test_certificate_forgery_and_unrelated_revision(self):
        kernel = self.kernel("أحمد هو ظاهر. كل ظاهر هو واضح.")
        cert = kernel.query("هل أحمد هو واضح؟").proofs["query"]
        mutations = []
        fake = deepcopy(cert); fake["passed"] = True; mutations.append(fake)
        fake = deepcopy(cert); fake["program_sha256"] = "0" * 64; mutations.append(fake)
        fake = deepcopy(cert); fake["conclusion"] = True; mutations.append(fake)
        fake = deepcopy(cert); fake["steps"][0]["atom"]["positive"] = False; mutations.append(fake)
        fake = deepcopy(cert); fake["steps"][-1]["binding"]["?x"] = "غيره"; mutations.append(fake)
        fake = deepcopy(cert); fake["steps"][-1]["premises"] = [99]; mutations.append(fake)
        fake = deepcopy(cert); fake["steps"][0]["clause"]["span"]["start"] = False; mutations.append(fake)
        fake = deepcopy(cert); fake["steps"][0]["clause"]["span"]["end"] += 1; mutations.append(fake)
        for candidate in mutations:
            self.assertFalse(kernel.verify_certificate(candidate)["accepted"])
        cycle = {}; cycle["self"] = cycle
        self.assertFalse(kernel.verify_certificate(cycle)["accepted"])
        deeply = []
        for _ in range(100):
            deeply = [deeply]
        self.assertFalse(kernel.verify_certificate(deeply)["accepted"])
        kernel.add_source("شخص هو بعيد.", source_id="unrelated")
        self.assertTrue(kernel.verify_certificate(cert)["accepted"])
        kernel.remove_source("unrelated")
        self.assertTrue(kernel.verify_certificate(cert)["accepted"])

    def test_numeric_identity_roundtrip_and_domain_guards(self):
        longest = "\U0001f600" * 512
        atom = Atom(longest, (longest, longest), False)
        encoded = atom_number(atom, longest)
        self.assertGreater(len(encoded["value_hex"]), 16384)
        self.assertEqual(decode_atom_number(encoded), (longest, atom))
        for key, value in (("version", True), ("namespace", "other"),
                           ("value_hex", "0" + encoded["value_hex"])):
            bad = {**encoded, key: value}
            with self.assertRaises(NabtError):
                decode_atom_number(bad)
        malicious = b"\x01" + b"[" * 1000 + b"]" * 1000
        with self.assertRaises(NabtError):
            decode_atom_number({**encoded, "value_hex": format(int.from_bytes(malicious, "big"), "x")})
        with self.assertRaises(NabtError):
            Atom("\ud800", ("شخص",))

    def test_budgets_and_read_only_queries(self):
        kernel = self.kernel("نادر هو أول. كل أول هو ثان.", max_join_steps=0)
        self.assertEqual(kernel.query("هل نادر هو ثان؟").reason, "RESOURCE_LIMIT")
        kernel = self.kernel("نادر هو أول.", max_output_bytes=256)
        self.assertEqual(kernel.query("هل نادر هو أول؟").reason, "RESOURCE_LIMIT")
        kernel = self.kernel("مفهوم غائب.")
        before = kernel.snapshot()
        self.assertEqual(kernel.query("هل جديد هو غائب؟").status, UNKNOWN)
        self.assertEqual(kernel.snapshot(), before)
        with self.assertRaises(NabtError):
            SemanticBudget(max_sources=True)

    def test_signed_ground_theories_against_independent_finite_models(self):
        # Six independent propositional variables represent positive/negative
        # supports for three predicates. Enumerating all models is independent
        # of the production unifier, joins, and fixed-point implementation.
        names = ("أصل", "تابع", "نتيجة")
        atoms = tuple(Atom(name, ("شخص",), sign) for name in names for sign in (True, False))
        rules = (((0,), 2), ((3,), 5), ((1, 4), 3))
        rule_text = ("كل أصل هو تابع. إذا ليس ?س هو تابع فإن ليس ?س هو نتيجة. "
                     "إذا ليس ?س هو أصل و ?س هو نتيجة فإن ليس ?س هو تابع.")

        def forced(facts, active_rules, blocked=frozenset()):
            models = []
            for values in product((False, True), repeat=6):
                if any(not values[i] for i in facts) or any(values[i] for i in blocked):
                    continue
                if all(not all(values[i] for i in body) or values[head] for body, head in active_rules):
                    models.append(values)
            self.assertTrue(models)
            return {i for i in range(6) if all(model[i] for model in models)}

        for mask in range(64):
            facts = {i for i in range(6) if mask & (1 << i)}
            signed = forced(facts, rules)
            blocked = {i for i in range(6) if i in signed and (i ^ 1) in signed}
            clean_rules = tuple((body, head) for body, head in rules
                                if head not in blocked and not set(body) & blocked)
            clean = forced(facts - blocked, clean_rules, blocked)
            source = rule_text + " ".join(("" if atoms[i].positive else "ليس ") +
                                          f"شخص هو {atoms[i].predicate}." for i in sorted(facts))
            kernel = self.kernel(source)
            for index in (0, 2, 4):
                if index in signed and (index ^ 1) in signed:
                    expected = CONFLICT
                elif index in clean:
                    expected = SUPPORTED
                elif (index ^ 1) in clean:
                    expected = REFUTED
                elif index in signed or (index ^ 1) in signed:
                    expected = DEFER
                else:
                    expected = UNKNOWN
                result = kernel.query(atoms[index])
                self.assertEqual(result.status, expected, (mask, index, result.as_dict()))


if __name__ == "__main__":
    unittest.main()
