import copy
import unittest

from nabt.alphabet import parse_word
from nabt.certificates import issue_certificate, verify_certificate
from nabt.errors import NabtError


def report(certificate):
    return verify_certificate(certificate).as_dict()


class CertificateTests(unittest.TestCase):
    def setUp(self):
        self.text = "كَتَبَ"
        self.cells = parse_word(self.text)

    def test_generated_and_source_bound_certificates_verify(self):
        for mode in ("wasl", "waqf"):
            generated = issue_certificate(self.cells, mode=mode)
            bound = issue_certificate(self.cells, mode=mode, source_text=self.text)
            self.assertTrue(report(generated)["valid"])
            self.assertTrue(report(bound)["valid"])
            self.assertEqual(generated["status"], "GENERATED_BY_LAW")
            self.assertEqual(bound["status"], "LICENSED_SHAPE")
            self.assertEqual(generated["certificate_type"], "WORD_SHAPE")
            self.assertIsNone(generated["source_text"])
            self.assertIsNone(generated["source_sha256"])

    def test_every_top_level_field_is_checked_not_just_carried(self):
        original = issue_certificate(self.cells, source_text=self.text)
        for field, value in original.items():
            changed = copy.deepcopy(original)
            if type(value) is str:
                changed[field] = value + "!"
            elif type(value) is int:
                changed[field] = value + 1
            elif type(value) is list:
                changed[field] = value[:-1] if value else [0]
            elif value is None:
                changed[field] = "forged"
            elif type(value) is dict:
                changed[field]["injected"] = True
            else:
                self.fail(f"Uncovered certificate field type: {field}: {type(value)}")
            with self.subTest(field=field):
                self.assertFalse(report(changed)["valid"])

    def test_missing_or_extra_fields_rejected(self):
        original = issue_certificate(self.cells)
        for field in original:
            changed = copy.deepcopy(original)
            del changed[field]
            with self.subTest(missing=field):
                self.assertFalse(report(changed)["valid"])
        changed = dict(original, invented_authority="ATTESTED")
        self.assertFalse(report(changed)["valid"])

    def test_bool_cannot_impersonate_integer_even_when_equal_in_python(self):
        original = issue_certificate(self.cells, source_text=self.text)
        changed = copy.deepcopy(original)
        changed["start_state"] = False
        self.assertFalse(report(changed)["valid"])
        # Find every nested numeric 0/1, the values with bool equality aliases.
        def paths(value, path=()):
            if type(value) is dict:
                for key, child in value.items():
                    yield from paths(child, path + (key,))
            elif type(value) is list:
                for key, child in enumerate(value):
                    yield from paths(child, path + (key,))
            elif type(value) is int and value in (0, 1):
                yield path, value
        tested = 0
        for path, value in paths(original):
            changed = copy.deepcopy(original)
            target = changed
            for part in path[:-1]:
                target = target[part]
            target[path[-1]] = bool(value)
            with self.subTest(path=path):
                self.assertFalse(report(changed)["valid"])
            tested += 1
        self.assertGreater(tested, 0)

    def test_source_binding_and_numeric_representation_are_canonical(self):
        with self.assertRaises(NabtError):
            issue_certificate(self.cells, source_text="كُتِبَ")
        original = issue_certificate(self.cells, source_text=self.text)
        changed = copy.deepcopy(original)
        changed["source_text"] = "كُتِبَ"
        self.assertFalse(report(changed)["valid"])
        for field in ("numeric_code", "rank"):
            for representation in ("0" + original[field], "+" + original[field], int(original[field]), "1" * 100_000):
                changed = copy.deepcopy(original)
                changed[field] = representation
                with self.subTest(field=field, kind=type(representation).__name__):
                    self.assertFalse(report(changed)["valid"])

    def test_malformed_inputs_return_a_rejection_report(self):
        for value in (None, [], "certificate", 1, True, {}):
            with self.subTest(value=value):
                self.assertFalse(report(value)["valid"])

    def test_unlicensed_sequence_cannot_receive_shape_certificate(self):
        for cells in ((), parse_word("كُاْ"), (116,), (True,)):
            with self.subTest(cells=cells):
                with self.assertRaises(NabtError):
                    issue_certificate(cells)


if __name__ == "__main__":
    unittest.main()
