"""Independent minimal pairs for the predicate-comparison identity boundary."""
from copy import deepcopy
import unicodedata
from unittest import TestCase

from tools import benchmark_semantic_axes as benchmark


class SemanticAxesShaddaTests(TestCase):
    def test_v03_plain_marida_cannot_be_satisfied_by_geminated_marrada(self):
        # Copilot reproducer: V03 requires مَرِضَ, not the distinct مَرَّضَ.
        expected = {"required": [{"force": "ASSERT", "positive": True, "predicate": "مَرِضَ"}],
                    "forbidden": [], "selection": "unique"}
        observed = {"readings": [{"force": "ASSERT", "positive": True, "predicate": "مَرَّضَ"}],
                    "reading_selection": "unique", "semantic_alternative_counts": [1]}
        result = benchmark._readings(expected, observed)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["observed"]["required_found"], [False])

    def test_explicit_gemination_is_preserved(self):
        self.assertEqual(benchmark._lemma("عَلَّمَ"), "علّم")
        self.assertEqual(benchmark._lemma("عَلِمَ"), "علم")
        self.assertNotEqual(benchmark._lemma("عَلَّمَ"), benchmark._lemma("عَلِمَ"))

    def test_unvocalized_predicate_does_not_supply_missing_shadda(self):
        self.assertTrue(benchmark._matches({"predicate": "علّم"}, {"predicate": "عَلَّمَ"}))
        self.assertFalse(benchmark._matches({"predicate": "علم"}, {"predicate": "عَلَّمَ"}))
        self.assertFalse(benchmark._matches({"predicate": "عَلَّمَ"}, {"predicate": "علم"}))

    def test_canonical_mark_order_is_equivalent(self):
        # Two canonically equivalent orders on lam, without transliteration.
        first = "عَل\u0651\u064eمَ"
        second = "عَل\u064e\u0651مَ"
        self.assertNotEqual(first, second)
        self.assertEqual(unicodedata.normalize("NFC", first), unicodedata.normalize("NFC", second))
        self.assertEqual(benchmark._lemma(first), "علّم")
        self.assertEqual(benchmark._lemma(second), "علّم")

    def test_short_vowel_tanwin_and_sukun_variants_remain_supported(self):
        for value in ("شَمْسٌ", "شَمْسٍ", "شَمْسًا"):
            # Accusative orthographic alif is retained, not guessed away.
            expected = "شمسا" if value.endswith("ا") else "شمس"
            with self.subTest(value=value):
                self.assertEqual(benchmark._lemma(value), expected)
        self.assertEqual(benchmark._lemma("عَلِمَ"), benchmark._lemma("علم"))

    def test_hamza_and_long_vowel_signs_remain_identity_bearing(self):
        self.assertEqual(benchmark._lemma("أَكَلَ"), benchmark._lemma("ا\u0654َكَلَ"))
        for first, second in (("أَمَرَ", "امر"), ("عَلَى", "علي"), ("هٰذا", "هذا")):
            with self.subTest(first=first, second=second):
                self.assertNotEqual(benchmark._lemma(first), benchmark._lemma(second))

    def test_affixes_are_not_stripped_by_the_scorer(self):
        for first, second in (("الشَّمْس", "شَمْس"), ("كِتَابُهُ", "كِتَاب"), ("وَخَرَجَ", "خَرَجَ")):
            with self.subTest(first=first, second=second):
                self.assertNotEqual(benchmark._lemma(first), benchmark._lemma(second))

    def test_required_geminated_reading_cannot_be_satisfied_by_plain_predicate(self):
        expected = {"required": [{"predicate": "عَلَّمَ"}], "forbidden": [], "selection": "unique"}
        observed = {"readings": [{"predicate": "عَلِمَ"}], "reading_selection": "unique",
                    "semantic_alternative_counts": [1]}
        actual = benchmark._readings(expected, observed)
        self.assertEqual(actual["status"], "FAIL")
        self.assertEqual(actual["observed"]["required_found"], [False])

    def test_distinct_geminated_forbidden_reading_does_not_reject_plain_reading(self):
        expected = {"required": [{"predicate": "عَلِمَ"}],
                    "forbidden": [{"predicate": "عَلَّمَ"}], "selection": "unique"}
        observed = {"readings": [{"predicate": "علم"}], "reading_selection": "unique",
                    "semantic_alternative_counts": [1]}
        before = deepcopy((expected, observed))
        actual = benchmark._readings(expected, observed)
        self.assertEqual(actual["status"], "PASS")
        self.assertEqual(actual["observed"]["forbidden_absent"], [True])
        self.assertEqual((expected, observed), before)

    def test_only_predicate_field_is_normalized(self):
        self.assertFalse(benchmark._matches({"surface": "عَلِمَ", "role": "verbal_predicate"},
                                           {"surface": "علم", "role": "verbal_predicate"}))
        self.assertFalse(benchmark._matches({"predicate": True}, {"predicate": 1}))
        self.assertEqual(benchmark.LEMMA_COMPARISON_POLICY["id"],
                         "nabt.semantic-axes.predicate-comparison.v2")
