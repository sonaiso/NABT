"""Source trust and scope tests, independent of reader outcomes or benchmark gold."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.linguistic_truth import sources


class NaturalUseSourceTests(unittest.TestCase):
    def test_three_attested_meanings_not_a_false_binary(self):
        inventory = sources.build_inventory()
        rows = [row for row in inventory['designations'] if row['expression'] == 'العين']
        self.assertEqual({row['sense_id'] for row in rows}, {'ayn_eye', 'ayn_spring', 'ayn_gold'})
        self.assertTrue(all(row['evidence_kind'] == 'author_explicit_designation_report' for row in rows))
        self.assertTrue(inventory['extension_scope']['omitted_ayn_uses'])
        self.assertFalse(inventory['extension_scope']['all_ayn_senses_exhausted'])
        self.assertFalse(inventory['extension_scope']['tawatur_assessed'])

    def test_retrieval_aliases_do_not_enter_cue_head_or_intended_sense(self):
        inventory = sources.build_inventory()
        forms = {form for row in inventory['designations'] for form in row['forms']}
        self.assertFalse({'أسداً', 'أسدا', 'عيناً', 'عينا'} & forms)
        rows = inventory['acquisition_extension']['retrieval_forms']
        self.assertEqual({row['form'] for row in rows}, {'أسداً', 'أسدا', 'عيناً', 'عينا'})
        self.assertTrue(all(row['selected_sense'] is None and row['authority'] == 'LEXICAL_RETRIEVAL_PROPOSAL'
                            for row in rows))

    def test_unproved_alias_and_conjunction_remain_unavailable(self):
        inventory = sources.build_inventory()
        self.assertIsNone(inventory['acquisition_extension']['initial_conjunction'])
        self.assertFalse(any('الحيوان المعروف' in row['sense_forms'] for row in inventory['designations']))
        cue = inventory['acquisition_extension']['cue_verbs'][0]
        self.assertEqual(cue['normal'], 'أقصد')
        self.assertEqual(cue['forms'], ['أَقْصِدُ'])
        self.assertEqual(cue['evidence_kind'], 'editorial_first_person_present_derivation')
        self.assertFalse(inventory['extension_scope']['native_acquisition_proof'])

    def test_unchanged_hash_is_not_enough_when_source_bytes_change(self):
        review = json.loads((sources.ROOT / sources.SUPPLEMENT_PATH).read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / sources.SUPPLEMENT_PATH
            target.parent.mkdir(parents=True)
            target.write_bytes((sources.ROOT / sources.SUPPLEMENT_PATH).read_bytes())
            for source in review['sources']:
                path = root / source['local_path']
                path.parent.mkdir(parents=True, exist_ok=True)
                data = (sources.ROOT / source['local_path']).read_bytes()
                path.write_bytes(data + (b'!' if source['source_id'] == 'natural_mukhtar' else b''))
            with self.assertRaisesRegex(sources.SourceInventoryError, 'SOURCE_CHANGED'):
                sources._merge_supplement({'sources': [], 'passages': [], 'designations': [], 'relations': []}, root)

    def test_rehashed_replacement_review_is_not_trusted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / sources.SUPPLEMENT_PATH
            target.parent.mkdir(parents=True)
            review = json.loads((sources.ROOT / sources.SUPPLEMENT_PATH).read_bytes())
            review['designations'][0]['gloss'] = 'substituted meaning'
            target.write_text(json.dumps(review, ensure_ascii=False))
            with self.assertRaisesRegex(sources.SourceInventoryError, 'SOURCE_REVIEW_CHANGED'):
                sources._merge_supplement({}, root)

    def test_rebuild_exactly_matches_installed_review(self):
        from evidence.natural_use_sources_v1.build_review import build
        rebuilt = (json.dumps(build(), ensure_ascii=False, indent=2)+'\n').encode()
        self.assertEqual(hashlib.sha256(rebuilt).hexdigest(), sources.SUPPLEMENT_SHA256)

    def test_trusted_replay_still_checks_invalid_extension_structure(self):
        original = sources._replay(sources.INVENTORY_PATH, sources.INVENTORY_SHA256, sources.ROOT)
        review = sources._replay(sources.SUPPLEMENT_PATH, sources.SUPPLEMENT_SHA256, sources.ROOT)
        mutations = [
            lambda r: r['acquisition_extension']['cue_verbs'][0].update(passage_ids=[]),
            lambda r: r['acquisition_extension']['retrieval_forms'][0].update(expression='uninstalled'),
            lambda r: r['acquisition_extension']['retrieval_forms'][0].update(selected_sense='ayn_eye'),
            lambda r: r['acquisition_extension'].update(initial_conjunction={}),
        ]
        for mutation in mutations:
            changed = deepcopy(review)
            mutation(changed)
            with self.subTest(mutation=mutation), patch.object(sources, '_replay', return_value=changed):
                with self.assertRaises(sources.SourceInventoryError):
                    sources._merge_supplement(deepcopy(original), sources.ROOT)


if __name__ == '__main__':
    unittest.main()
