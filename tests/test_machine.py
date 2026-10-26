from dataclasses import replace
from importlib.resources import files
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from nabt.alphabet import MAX_CELLS, parse_word
from nabt.errors import NabtError
from nabt.machine import MAX_WEIGHT, Machine, compose_effects
import nabt.machine as machine_module

from tests import oracle


class TransitionTests(unittest.TestCase):
    def test_every_primitive_transition_against_letter_phase_oracle(self):
        machine = Machine()
        for q in range(97):
            self.assertEqual(machine.pot(q), oracle.potential(q))
            for a in range(116):
                self.assertEqual(machine.transition(q, a), oracle.transition(q, a), (q, a))
        for mode in ("wasl", "waqf"):
            machine = Machine(mode)
            for q in range(97):
                self.assertEqual(machine.final(q), oracle.final(q, mode))

    def test_alif_counterexamples_and_mode_difference(self):
        for mode in ("wasl", "waqf"):
            machine = Machine(mode)
            for text in ("كُاْ", "كَاْاْ"):
                with self.assertRaises(NabtError):
                    machine.rank(parse_word(text))
            self.assertGreaterEqual(machine.rank(parse_word("كَاْ")), 0)
        # CVCC is a licensed end under this waqf model, not a free continuation.
        final_cluster = parse_word("كَتْبْ")
        self.assertGreaterEqual(Machine("waqf").rank(final_cluster), 0)
        with self.assertRaises(NabtError):
            Machine("wasl").rank(final_cluster)

    def test_mode_cannot_diverge_from_the_bound_final_states(self):
        machine = Machine("waqf")
        cells = parse_word("كَتْبْ")
        self.assertTrue(machine.analyse(cells).licensed)
        with self.assertRaises((AttributeError, NabtError)):
            machine.mode = "wasl"
        self.assertEqual(machine.mode, "waqf")
        self.assertTrue(machine.analyse(cells).licensed)
        self.assertFalse(Machine("wasl").analyse(cells).licensed)

    def test_boundary_symbol_cannot_enter_word_alphabet(self):
        for mode in ("wasl", "waqf"):
            machine = Machine(mode)
            for invalid in (116, 117, -1, True):
                with self.assertRaises(NabtError):
                    machine.transition(1, invalid)
                with self.assertRaises(NabtError):
                    machine.rank((4, invalid))
        with self.assertRaises(NabtError):
            Machine("other")

    def test_zero_weight_suffix_keeps_madd_and_uses_state_potential(self):
        for mode in ("wasl", "waqf"):
            machine = Machine(mode)
            self.assertEqual(machine.count(0), 0)
            for q, madd in ((1, "ا"), (2, "و"), (3, "ي")):
                self.assertEqual(machine.count(0, start_state=q), 2)
                self.assertEqual(machine.unrank(0, 0, start_state=q), ())
                tail = (oracle.cell(madd, 3),)
                self.assertEqual(machine.unrank(0, 1, start_state=q), tail)
                self.assertEqual(machine.rank(tail, start_state=q), 1)

    def test_budget_failure_is_explicit_and_not_linguistic_rejection(self):
        machine = Machine()
        for call in (lambda: machine.count(MAX_WEIGHT + 1),
                     lambda: machine.rank((4,) * (MAX_CELLS + 1))):
            with self.assertRaises(NabtError) as caught:
                call()
            self.assertEqual(caught.exception.status, "DEFER")
            self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")
        for invalid in (True, -1, "1", 0.5):
            with self.assertRaises(NabtError):
                machine.count(invalid)
        with self.assertRaises(NabtError):
            machine.unrank(1, 168)
        with self.assertRaises(NabtError):
            machine.unrank(1, True)
        with self.assertRaises(NabtError):
            machine.count(0, start_state=97)

    def test_modified_installed_table_cannot_become_authority(self):
        original = files("nabt").joinpath("data/law.json").read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "data").mkdir()
            # Even a semantically irrelevant byte change must violate the byte pin.
            (root / "data/law.json").write_bytes(original + b" ")
            machine_module._load_table.cache_clear()
            try:
                with patch.object(machine_module, "files", return_value=root):
                    with self.assertRaises(NabtError) as caught:
                        Machine()
                # The shared admission now wraps a mismatched execution table
                # before Machine can use it, including on its first load.
                self.assertEqual(caught.exception.code, "FOUNDATION_INTEGRITY")
            finally:
                machine_module._load_table.cache_clear()


class CountingTests(unittest.TestCase):
    def test_recursive_counts_against_forward_exact_length_dp(self):
        for mode in ("wasl", "waqf"):
            machine = Machine(mode)
            for start, weight in ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (4, 0), (4, 1), (35, 0)):
                with self.subTest(mode=mode, start=start, weight=weight):
                    self.assertEqual(machine.count(weight, start_state=start),
                                     oracle.forward_count(weight, mode, start))

    def test_all_grade_one_words_and_ranks_by_structural_enumeration(self):
        expected = oracle.grade_one_words()
        self.assertEqual(len(expected), 168)
        self.assertEqual(len(set(expected)), 168)
        for mode in ("wasl", "waqf"):
            machine = Machine(mode)
            self.assertEqual(machine.count(1), len(expected))
            for rank, word in enumerate(expected):
                self.assertEqual(machine.unrank(1, rank), word)
                self.assertEqual(machine.rank(word), rank)

    def test_grade_four_deterministic_samples_bounds_and_independent_run(self):
        expected_totals = {"waqf": 1_089_919_936, "wasl": 1_068_055_744}
        for mode, total in expected_totals.items():
            machine = Machine(mode)
            self.assertEqual(machine.count(4), total)
            rng = random.Random(20261022)
            ranks = {0, 1, total // 2, total - 2, total - 1}
            while len(ranks) < 100:
                ranks.add(rng.randrange(total))
            words = set()
            for rank in sorted(ranks):
                word = machine.unrank(4, rank)
                accepted, _q, weight = oracle.run(word, mode)
                self.assertTrue(accepted)
                self.assertEqual(weight, 4)
                self.assertLessEqual(len(word), 12)
                self.assertEqual(machine.rank(word), rank)
                words.add(word)
            self.assertEqual(len(words), 100)

    def test_effect_composition_keeps_context_dependent_weight(self):
        machine = Machine()
        pieces = [(), (84,), (3,), (84, 3), (8, 7), (4, 107)]
        for left in pieces:
            for right in pieces:
                composed = compose_effects(machine.effect(left), machine.effect(right))
                self.assertEqual(composed.as_dict(), machine.effect(left + right).as_dict())

    def test_effect_payload_and_numeric_action_cannot_disagree(self):
        effect = Machine().effect((84,))
        with self.assertRaises(NabtError):
            replace(effect, cells=(85,))
        with self.assertRaises(NabtError):
            replace(effect, weights=(effect.weights[0] + 1,) + effect.weights[1:])
        with self.assertRaises(NabtError):
            replace(effect, destinations=(False,) + effect.destinations[1:])


if __name__ == "__main__":
    unittest.main()
