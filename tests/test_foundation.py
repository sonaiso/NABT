"""Admission tampering and projection replay tests for the shared foundation."""
from copy import deepcopy
from dataclasses import replace
from importlib.resources import files
import unittest
from unittest.mock import patch

from nabt import alphabet, codec, foundation, machine
from nabt.errors import NabtError


class FoundationAdmissionTests(unittest.TestCase):
    def test_installed_identity_and_no_caller_manifest(self):
        identity = foundation.require_foundation("test.admission")
        self.assertEqual(identity["alphabet_id"], "nabt.a116.v1")
        self.assertEqual(identity["law_table_sha256"], machine.EXPECTED_TABLE_SHA256)
        self.assertEqual(identity["authority"], "REPRESENTATION_FOUNDATION_ONLY")
        with self.assertRaises(TypeError):
            foundation.require_foundation("test.admission", {"checked": True})

    def test_changed_installed_bytes_cannot_hide_behind_warm_machine_cache(self):
        machine._load_table()
        raw = files("nabt").joinpath("data/law.json").read_bytes()
        with patch("nabt.foundation.files") as resource:
            resource.return_value.joinpath.return_value.read_bytes.return_value = raw + b" "
            with self.assertRaises(NabtError) as error:
                foundation.require_foundation("test.cached_law")
        self.assertEqual(error.exception.code, "FOUNDATION_INTEGRITY")

    def test_cached_execution_is_rechecked_not_just_its_digest(self):
        original = machine._load_table()
        rows = [list(row) for row in original.transitions]
        state, cost = rows[0][0]
        rows[0][0] = (state, bool(cost))  # Python equality alone would accept it.
        forged = replace(original, transitions=tuple(tuple(row) for row in rows))
        with patch("nabt.machine._load_table", return_value=forged):
            with self.assertRaises(NabtError) as error:
                foundation.require_foundation("test.cached_types")
        self.assertEqual(error.exception.code, "FOUNDATION_INTEGRITY")

    def test_carrier_order_marks_and_radix_are_bound_to_installed_contract(self):
        for module, name, changed in (
                (alphabet, "CARRIERS", alphabet.CARRIERS[::-1]),
                (alphabet, "HARAKAT", ("َ", "ِ", "ُ", "ْ")),
                (codec, "BASE", True),
                (codec, "BASE", 117)):
            with self.subTest(name=name), patch.object(module, name, changed):
                with self.assertRaises(NabtError):
                    foundation.require_foundation("test.core_constants")

    def test_decorator_checks_before_call_and_uses_patchable_entrypoint(self):
        calls = []

        @foundation.foundation_guard("test.decorator")
        def operation(value):
            calls.append(value)
            return value

        self.assertEqual(operation(3), 3)
        with patch("nabt.foundation.require_foundation", side_effect=NabtError("DENIED", "test")):
            with self.assertRaises(NabtError):
                operation(4)
        self.assertEqual(calls, [3])


class FoundationReceiptTests(unittest.TestCase):
    def test_all_116_declared_pairs_restore_without_creating_readings(self):
        for carrier in alphabet.CARRIERS:
            for mark in alphabet.HARAKAT:
                raw = carrier + mark
                report = foundation.inspect_source(raw)
                self.assertEqual(report["status"], "COMPLETE")
                self.assertEqual(report["cells"], list(alphabet.parse_word(raw)))
                self.assertEqual(bytes(report["raw_utf8"]), raw.encode())
                self.assertTrue(foundation.verify_source_receipt(report, text=raw))
                self.assertNotIn("licensed", report)
                self.assertNotIn("world_truth_established", report)

    def test_typed_source_and_domain_mutations_do_not_replay(self):
        report = foundation.inspect_source("اَ بَ", source_id="source_a", revision="rev1")
        mutations = [
            ("law_id", "forged"), ("alphabet_id", "mashru.dal.cells.v1"),
            ("number_domain", "nabt.bijective116.v1"), ("number", "0" + report["number"]),
            ("status", "PARTIAL"), ("cells", [False, 4]),
            ("raw_utf8", [True] + report["raw_utf8"][1:]), ("padding", 0),
        ]
        for key, value in mutations:
            changed = deepcopy(report)
            changed[key] = value
            with self.subTest(field=key):
                self.assertFalse(foundation.verify_source_receipt(changed))
        self.assertFalse(foundation.verify_source_receipt(report, text="بَ اَ"))
        self.assertFalse(foundation.verify_source_receipt(report, source_id="source_b"))
        self.assertFalse(foundation.verify_source_receipt(report, revision="rev2"))

    def test_numeric_projection_is_not_full_source_identity(self):
        left = foundation.inspect_source("بَ")
        right = foundation.inspect_source("بَ ا")
        self.assertEqual(left["number"], right["number"])
        self.assertEqual(left["status"], "COMPLETE")
        self.assertEqual(right["status"], "PARTIAL")
        self.assertNotEqual(left["source"], right["source"])
        self.assertFalse(foundation.verify_source_receipt(right, text="بَ"))

    def test_partial_is_admitted_invalid_marks_are_not(self):
        for text in ("إِنْ جَاءَ خَلِيدٌ قُمْتُ", "بَّ", "بَّ", "رَجُلًا", "جَآءَ", "كتب"):
            with self.subTest(text=text):
                self.assertEqual(foundation.inspect_source(text)["status"], "PARTIAL")
                foundation.validate_source(text)
        for text in ("أَُعني", "بََ", "بّّ", "َبَ", ""):
            with self.subTest(text=text), self.assertRaises(NabtError) as error:
                foundation.validate_source(text)
            self.assertEqual(error.exception.code, "FOUNDATION_SOURCE_INVALID")

    def test_boundaries_remain_typed_not_unhandled_errors(self):
        for text in (True, 1, [], None):
            with self.subTest(text=text), self.assertRaises(NabtError):
                foundation.inspect_source(text)
        for text in (b"\xff", "\ud800"):
            with self.subTest(text=repr(text)), self.assertRaises(NabtError) as error:
                foundation.inspect_source(text)
            self.assertEqual(error.exception.code, "FOUNDATION_SOURCE_ENCODING")
        for text in ("بَ" * (alphabet.MAX_CELLS + 1), " " * (foundation.MAX_SOURCE_BYTES + 1)):
            with self.assertRaises(NabtError) as error:
                foundation.inspect_source(text)
            self.assertEqual(error.exception.code, "RESOURCE_LIMIT")
            self.assertEqual(error.exception.status, "DEFER")


class FoundationTransformTests(unittest.TestCase):
    def binding(self, surface="كَتَبَ"):
        text = "«" + surface + "»"
        return {"source": {"id": "book", "revision": "1", "text": text},
                "scope_id": "quote_1", "occurrence_id": "word_1", "reading_id": "active",
                "start_byte": 2, "end_byte": 2 + len(surface.encode()), "surface": surface}

    def test_operations_compute_cells_and_bind_their_reading(self):
        binding = self.binding()
        for operation, cells, number in (({"op": "keep"}, [84, 8, 4], 1144809),
                ({"op": "append", "suffix": [9]}, [84, 8, 4, 9], 1144809 * 116 + 10),
                ({"op": "replace", "index": 0, "cell": 85}, [85, 8, 4], 1144809 + 116 ** 2)):
            with self.subTest(operation=operation):
                receipt = foundation.make_transform(binding, operation)
                self.assertEqual(receipt["input_cells"], [84, 8, 4])
                self.assertEqual(receipt["output_cells"], cells)
                self.assertEqual(receipt["output_number"], str(number))
                self.assertTrue(foundation.check_transform(binding, operation, receipt))
                for field, value in (("reading_id", "passive"), ("scope_id", "quote_2"),
                                     ("occurrence_id", "word_2"), ("start_byte", 0)):
                    changed = deepcopy(receipt)
                    changed["binding"][field] = value
                    self.assertFalse(foundation.check_transform(binding, operation, changed))
                changed = deepcopy(receipt)
                changed["output_cells"] = [1]
                self.assertFalse(foundation.check_transform(binding, operation, changed))

    def test_partial_and_invalid_source_do_not_become_numeric_transforms(self):
        for surface, code in (("جَاءَ", "INCOMPLETE_PROJECTION"), ("كَُ", "INVALID_SOURCE")):
            with self.subTest(surface=surface), self.assertRaises(NabtError) as error:
                foundation.make_transform(self.binding(surface), {"op": "keep"})
            self.assertEqual(error.exception.code, code)

    def test_operations_reject_boolean_or_outside_cells_and_changed_source(self):
        binding = self.binding()
        for operation in ({"op": "replace", "index": True, "cell": 1},
                          {"op": "replace", "index": 3, "cell": 1},
                          {"op": "append", "suffix": [116]},
                          {"op": "append", "suffix": [True]},
                          {"op": "keep", "licensed": True}):
            with self.subTest(operation=operation), self.assertRaises(NabtError):
                foundation.make_transform(binding, operation)
        changed = deepcopy(binding)
        changed["source"]["text"] = "«كُتِبَ»"
        with self.assertRaises(NabtError):
            foundation.make_transform(changed, {"op": "keep"})

    def test_bound_occurrence_cannot_hide_remaining_source_marks(self):
        for source_text, surface, start in (("قُمْتُّ", "قُمْتُ", 0),
                ("قُمْتَُ", "قُمْتُ", 0), ("بََ", "بَ", 0),
                ("بَُ", "بَ", 0), ("بَتُ", "َتُ", 2)):
            binding = self.binding(surface)
            binding.update(source={"id": "book", "revision": "1", "text": source_text},
                           start_byte=start, end_byte=start + len(surface.encode()))
            with self.subTest(source=source_text), self.assertRaises(NabtError) as error:
                foundation.make_transform(binding, {"op": "keep"})
            self.assertEqual(error.exception.code, "INVALID_INPUT")
            self.assertFalse(foundation.check_transform(binding, {"op": "keep"}, {}))

    def test_source_cluster_boundaries_do_not_invent_word_or_global_projection_requirements(self):
        surface = "قُمْتُ"
        for prefix, suffix in (("إِ", "جَآءَ"), ("x" * 5000, "?"), ("وَ", "هُ")):
            binding = self.binding(surface)
            binding.update(source={"id": "book", "revision": "1", "text": prefix + surface + suffix},
                           start_byte=len(prefix.encode()), end_byte=len((prefix + surface).encode()))
            with self.subTest(prefix=prefix[:20]):
                receipt = foundation.make_transform(binding, {"op": "keep"})
                self.assertEqual(receipt["input_cells"], [81, 95, 9])
                self.assertTrue(foundation.check_transform(binding, {"op": "keep"}, receipt))


if __name__ == "__main__":
    unittest.main()
