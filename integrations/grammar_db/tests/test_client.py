"""Validation tests run without a PostgreSQL server or an embedding download."""
import unittest

from integrations.grammar_db.client import (
    embedding_metadata, search_projection, validate_vector,
)


class ValidationTests(unittest.TestCase):
    def test_normalization_is_search_only_and_removes_arabic_marks(self):
        original = "مُبْتَدَأٌ زَيْدٌ وَعَاذِرٌ خَبَرْ"
        self.assertEqual(search_projection(original), "مبتدا زيد وعاذر خبر")
        self.assertEqual(original, "مُبْتَدَأٌ زَيْدٌ وَعَاذِرٌ خَبَرْ")
        self.assertEqual(search_projection("NABT ـ وَصْل ' | :"), "nabt وصل")

    def test_model_identity_dimensions_and_recipe_bind_the_run(self):
        a = embedding_metadata("a" * 64, "example/model", "b" * 40, 768)
        for change in ({"dimensions": 384}, {"revision": "c" * 40}, {"snapshot_sha": "d" * 64}):
            args = dict(snapshot_sha="a" * 64, model_id="example/model", revision="b" * 40, dimensions=768)
            args.update(change)
            self.assertNotEqual(a["run_id"], embedding_metadata(**args)["run_id"])
        self.assertEqual(a, embedding_metadata("a" * 64, "example/model", "b" * 40, 768))

    def test_unpinned_or_malformed_metadata_rejected(self):
        for revision in ("main", "latest", "a" * 39, "A" * 40, 12):
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                embedding_metadata("a" * 64, "example/model", revision, 768)
        for dimension in (True, False, 0, -1, 16001, 768.0, "768"):
            with self.subTest(dimension=dimension), self.assertRaises(ValueError):
                embedding_metadata("a" * 64, "example/model", "b" * 40, dimension)
        with self.assertRaises(ValueError):
            embedding_metadata("a" * 64, "example/model", "b" * 40, 3, recipe="invented")

    def test_vector_validation_is_strict_before_database(self):
        self.assertEqual(validate_vector([1, 0, 0], 3).tolist(), [1, 0, 0])
        unit = validate_vector([1, -2, 0], 3)
        self.assertAlmostEqual(float(sum(unit * unit)), 1.0, places=6)
        self.assertAlmostEqual(float(unit[1] / unit[0]), -2.0)
        for vector in ([0, 0, 0], [True, 1, 2], [1, 2], [1, 2, 3, 4],
                       [1, float("inf"), 2], [1, float("nan"), 2], [1, 1e100, 2],
                       [1, 10**1000, 2], [1, 1j, 2], ["1", 2, 3], [1e-100, 0, 0]):
            with self.subTest(vector=str(vector)[:40]), self.assertRaises(ValueError):
                validate_vector(vector, 3)
        with self.assertRaises(ValueError):
            validate_vector([1], True)


if __name__ == "__main__":
    unittest.main()
