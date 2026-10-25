"""Independent provenance boundary checks for the selected source review."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.mantuq_sources import (ROOT, INVENTORY_PATH, SUPPLEMENT_PATH,
                                 SourceInventoryError, build_inventory, build_supplement)


class SourceReviewTests(unittest.TestCase):
    def make_copy(self, path):
        inventory = json.loads((ROOT / INVENTORY_PATH).read_text())
        for relative in [INVENTORY_PATH, *[Path(s['local_path']) for s in inventory['sources']]]:
            target = path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        return inventory

    def test_source_ranges_agree_with_earlier_independent_extraction(self):
        reviewed = build_inventory()
        old = json.loads((ROOT / 'evidence/mantuq_mafhum/sources.json').read_text())
        original = {(s['source_id'], p['paragraph']): p for s in old['sources'] for p in s['spans']}
        self.assertEqual((len(reviewed['sources']), len(reviewed['passages']), len(reviewed['rules'])), (3, 16, 9))
        for p in reviewed['passages']:
            precedent = original[p['source_id'], p['paragraph']]
            self.assertEqual(p['raw_text'], precedent['quote'])
            self.assertEqual(p['start'], precedent['offset'])
            self.assertEqual(p['original_extraction_offset'], precedent['extraction_offset'])
            self.assertEqual(hashlib.sha256(p['raw_text'].encode()).hexdigest(), p['sha256'])

    def test_changed_source_and_self_reported_manifest_cannot_authorize(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = self.make_copy(root)
            source = root / inventory['sources'][0]['local_path']
            source.write_bytes(source.read_bytes() + b' ')
            with self.assertRaisesRegex(SourceInventoryError, 'SOURCE_CHANGED'):
                build_inventory(root)
            inventory['sources'][0]['bytes'] = source.stat().st_size
            inventory['sources'][0]['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
            (root / INVENTORY_PATH).write_text(json.dumps(inventory, ensure_ascii=False))
            with self.assertRaisesRegex(SourceInventoryError, 'SOURCE_REVIEW_CHANGED'):
                build_inventory(root)

    def test_missing_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = self.make_copy(root)
            (root / inventory['sources'][0]['local_path']).unlink()
            with self.assertRaisesRegex(SourceInventoryError, 'SOURCE_REPLAY_FAILED'):
                build_inventory(root)

    def test_public_result_is_fresh_and_research_is_not_authority(self):
        first = build_inventory()
        first['rules'][0]['linguistic_license_established'] = True
        second = build_inventory()
        self.assertTrue(all(not rule['linguistic_license_established'] for rule in second['rules']))
        self.assertTrue(all(not item['runtime_authority'] for item in second['external_research']))
        self.assertFalse(second['claims']['whole_arabic_complete'])
        analogy = next(r for r in second['rules'] if r['rule_id'] == 'analogy')
        self.assertEqual(analogy['source_passage_ids'], [])
        self.assertTrue(analogy['source_context_only'])


class SourceSupplementTests(unittest.TestCase):
    def test_original_recheck_and_policy_context_remain_distinct(self):
        supplement = build_supplement()
        self.assertEqual(len(supplement['passages']), 38)
        self.assertEqual(supplement['replay']['source_bytes_checked'], 32867)
        self.assertEqual(supplement['original_comparison']['previous_retained_paragraphs_rechecked'], 11)
        self.assertFalse(supplement['replay']['original_books_rechecked'])
        self.assertTrue(supplement['original_comparison']['canonical_extraction_matches_previous'])
        self.assertTrue(all(not a['executable_rule_changed'] and not a['linguistic_license_established']
                            for a in supplement['policy_associations']))
        self.assertEqual(next(r for r in build_inventory()['rules'] if r['rule_id'] == 'analogy')
                         ['source_passage_ids'], [])

    def test_supplement_tampering_cannot_update_its_own_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = json.loads((ROOT / SUPPLEMENT_PATH).read_text())
            for relative in [SUPPLEMENT_PATH, Path(config['sources'][0]['local_path'])]:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            self.assertEqual(build_supplement(root)['replay']['passages'], 38)
            source = root / config['sources'][0]['local_path']
            source.write_bytes(source.read_bytes()[:-1] + b'!')
            with self.assertRaisesRegex(SourceInventoryError, 'SOURCE_CHANGED'):
                build_supplement(root)
            config['sources'][0]['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
            (root / SUPPLEMENT_PATH).write_text(json.dumps(config))
            with self.assertRaisesRegex(SourceInventoryError, 'SOURCE_REVIEW_CHANGED'):
                build_supplement(root)


if __name__ == '__main__':
    unittest.main()
