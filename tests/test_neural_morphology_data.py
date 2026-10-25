"""Independent intake/counterexample oracles; no neural dependency required."""
import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.arabic_training.data import FIELDS, ROOT, book_evidence, read_source, source_constraints, split_for_sura


class NeuralMorphologyDataTests(unittest.TestCase):
    def fixture(self, rows):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / 'source.csv'
        with path.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            for updates in rows:
                row = dict.fromkeys(FIELDS, '')
                row.update(ID='1', Sura_No='1', Verse_No='1', Column5='1', Word_No='1',
                           Word='كَتَبَ', Morph_tag='PV', Morph_type='Stem',
                           Invariable_Declinable='مبني', Case_Mood='مبني')
                row.update(updates)
                writer.writerow(row)
        return path

    def test_exact_bytes_and_external_annotations_never_override_pin(self):
        p = self.fixture([{}])
        with self.assertRaisesRegex(ValueError, 'identity'):
            read_source(p)
        examples, _, _ = read_source(p, verify=False)
        word = examples[0]['words'][0]
        self.assertEqual(word['text'], 'كَتَبَ')
        self.assertEqual(word['text_sha256'], hashlib.sha256('كَتَبَ'.encode()).hexdigest())
        self.assertEqual(word['csv_rows'], [2])

    def test_declared_rules_and_valid_built_case_position(self):
        self.assertEqual(source_constraints('PV', 'معرب', 'مجرور'),
                         ['VERB_HAS_NO_GENITIVE', 'PAST_AND_IMPERATIVE_ARE_BUILT'])
        self.assertEqual(source_constraints('NOUN_CONCRETE', 'معرب', 'مجزوم'), ['NOUN_HAS_NO_JUSSIVE'])
        self.assertEqual(source_constraints('REL_PRON', 'مبني', 'مرفوع'), [])
        self.assertEqual(source_constraints('IV', 'معرب', 'مجزوم'), [])

    def test_conflict_is_obligation_not_silent_gold_repair(self):
        p = self.fixture([{'Case_Mood':'مجرور'}])
        examples, _, conflicts = read_source(p, verify=False)
        word = examples[0]['words'][0]
        self.assertEqual(conflicts[0]['raw_labels']['case_mood'], 'مجرور')
        self.assertTrue(all(v is None for v in word['labels'].values()))
        self.assertIsNone(word['affixes'])
        self.assertEqual(word['text'], 'كَتَبَ')

    def test_joined_multiple_stems_are_not_flattened_to_first(self):
        p = self.fixture([{'Word':'يَاآدَمُ'}, {'ID':'2','Word':'يَاآدَمُ','Morph_tag':'NOUN_PROP'}])
        examples, _, _ = read_source(p, verify=False)
        word = examples[0]['words'][0]
        self.assertIn('MULTIPLE_ANNOTATION_IDS', word['excluded_reasons'])
        self.assertIn('MULTIPLE_OR_MISSING_STEMS', word['excluded_reasons'])
        self.assertEqual(word['csv_rows'], [2,3])

    def test_cross_sura_duplicate_quarantine_does_not_normalize_model_input(self):
        p = self.fixture([{}, {'Sura_No':'2','Word':'كُتِبَ'},
                          {'Sura_No':'3','Word':'رَجَعَ'}])
        examples, manifest, _ = read_source(p, verify=False)
        self.assertEqual([e['id'] for e in examples], ['3:1'])
        self.assertEqual(manifest['duplicate_verses_quarantined'], [[1,1],[2,1]])
        self.assertEqual(examples[0]['words'][0]['text'], 'رَجَعَ')

    def test_multiple_annotations_do_not_multiply_observations(self):
        p = self.fixture([{}, {'Morph_type':'Other_i3rab','Morph_tag':'NOT_A_READING'}])
        examples, manifest, _ = read_source(p, verify=False)
        self.assertEqual(manifest['csv_rows'], 2)
        self.assertEqual(manifest['word_occurrences'], 1)
        self.assertEqual(examples[0]['words'][0]['labels']['tag'], 'PV')
        self.assertEqual(examples[0]['words'][0]['affixes'], [])

    def test_unknown_vowels_and_competing_bytes_are_distinct(self):
        examples, _, _ = read_source(self.fixture([{'Word':'كتب'}]), verify=False)
        self.assertEqual(examples[0]['words'][0]['excluded_reasons'], ['NO_VOWEL_MARK_OBSERVED'])
        with self.assertRaisesRegex(ValueError, 'competing word bytes'):
            read_source(self.fixture([{}, {'Word':'كَتَبُ'}]), verify=False)

    def test_split_is_source_grouped_and_rejects_bool(self):
        self.assertEqual(split_for_sura(5), 'test')
        self.assertEqual(split_for_sura(18), 'dev')
        self.assertEqual(split_for_sura(2), 'train')
        for value in (True, 0, 115, '2'):
            with self.assertRaises(ValueError):
                split_for_sura(value)

    def test_book_evidence_restores_exact_bytes(self):
        evidence = book_evidence()
        self.assertEqual(len(evidence), 7)
        for item in evidence:
            raw = (ROOT / item['source_path']).read_bytes()
            quote = raw[item['start_byte']:item['end_byte']]
            self.assertEqual(quote.decode(), item['quote'])
            self.assertEqual(hashlib.sha256(quote).hexdigest(), item['quote_sha256'])
        self.assertIn('وليس في الأسماء جزم', evidence[1]['quote'])
        self.assertIn('ماض: ويعرف بتاء التأنيث', evidence[2]['quote'])


if __name__ == '__main__':
    unittest.main()
