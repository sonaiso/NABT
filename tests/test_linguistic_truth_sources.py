import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.linguistic_truth.sources import ROOT, INVENTORY_PATH, SourceInventoryError, build_inventory


class LinguisticSourceReplay(unittest.TestCase):
    def test_all_three_works_and_exact_designation_subquotes(self):
        inv = build_inventory()
        self.assertEqual({s['work'] for s in inv['sources']}, {'shakhsiyya1','shakhsiyya3','thinking',
                                                             'mukhtar_sihah','qatr','ibn_aqil','lisan'})
        self.assertEqual(len(inv['passages']), 104)
        self.assertEqual(inv['scope']['retained_units'], 113)
        self.assertEqual(len(inv['designations']), 12)
        self.assertEqual(inv['replay']['designation_subquotes_checked'], 15)
        self.assertEqual(inv['extension_scope']['new_designations'], 3)
        self.assertFalse(inv['extension_scope']['all_ayn_senses_exhausted'])
        self.assertFalse(inv['replay']['original_comparison_performed_here'])
        self.assertFalse(inv['scope']['world_truth_established'])

    def test_changed_excerpt_is_not_authorized_by_unchanged_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source_dir = INVENTORY_PATH.parent
            shutil.copytree(ROOT/source_dir, root/source_dir)
            inv = json.loads((root/INVENTORY_PATH).read_text())
            path = root/inv['sources'][0]['local_path']
            path.write_bytes(path.read_bytes()+b'\n')
            with self.assertRaises(SourceInventoryError):
                build_inventory(root)

    def test_rehashed_caller_review_cannot_install_new_designation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT/INVENTORY_PATH.parent, root/INVENTORY_PATH.parent)
            path = root/INVENTORY_PATH
            inv = json.loads(path.read_text())
            inv['designations'][0]['gloss'] = 'caller replacement'
            path.write_text(json.dumps(inv))
            with self.assertRaises(SourceInventoryError):
                build_inventory(root)


if __name__ == '__main__':
    unittest.main()
