"""Counterexamples for source identity, leakage, scoring and learned composition."""
from collections import Counter
from copy import deepcopy
import gzip
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

from tools.lexical_training import comparison_simulation as experiment
from tools.lexical_training import train_comparison_simulation as training
from tools.lexical_training import ntp_recursive as cells


class ComparisonContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = experiment.dataset()
        cls.language = [r for r in cls.rows if r['task'] in ('cell_reading', 'program_composition')]

    def test_populations_and_original_root_partition_are_retained(self):
        self.assertEqual(Counter(r['task'] for r in self.rows), {
            'cell_reading': 30, 'program_composition': 324,
            'memory_primitive': 8, 'memory_update': 3872, 'memory_alternatives': 4372})
        self.assertEqual(Counter(r['split'] for r in self.rows if r['task'] == 'cell_reading'),
                         {'train': 15, 'dev': 5, 'root_test': 10})
        self.assertEqual(sum(r['eligible'] for r in self.rows if r['task'] == 'program_composition'), 144)
        train = {r['input']['text'] for r in self.language if r['split'] == 'train'}
        self.assertFalse(train & {r['input']['text'] for r in self.language if r['split'] != 'train'})

    def test_source_features_exclude_owner_program_and_preserve_diacritics(self):
        for r in self.language:
            self.assertEqual(r['input_sha256'], experiment.digest(r['input']))
            if r['task'] == 'program_composition':
                self.assertEqual(set(r['input']), {'text', 'operator_groups', 'operator_count', 'bindings'})
                for g in r['input']['operator_groups']:
                    self.assertEqual(set(g), {'surface', 'cells', 'utf8_span'})
                    self.assertEqual(r['input']['text'].encode()[slice(*g['utf8_span'])].decode(), g['surface'])
                    self.assertEqual(list(cells.parse_word(g['surface'])), g['cells'])
            else:
                self.assertEqual(list(cells.parse_word(r['input']['text'])), r['input']['cells'])

    def test_atomic_training_excludes_held_out_composition(self):
        examples = experiment.operator_training(self.rows)
        self.assertEqual(len(examples), 3)
        self.assertEqual({r['target'] for r in examples}, {'ask', 'wish', 'negation'})
        poisoned = deepcopy(self.rows)
        for r in poisoned:
            if r['split'] != 'train':
                r['target'] = 'poisoned-test-answer'
        self.assertEqual(experiment.operator_training(poisoned), examples)

    def test_operator_order_is_not_commutative_or_a_bag(self):
        bindings = {'subject': 0, 'predicate': 1}
        self.assertEqual(experiment.compose(['ask', 'negation'], bindings), 'ask_negation')
        self.assertIsNone(experiment.compose(['negation', 'ask'], bindings))
        self.assertIsNone(experiment.compose(['ask', 'ask'], bindings))
        self.assertIsNone(experiment.compose([], bindings))
        self.assertEqual(experiment.compose(['wish'], bindings), 'wish')

    def test_all_correct_counts_each_word_once_not_once_per_head(self):
        prediction = experiment.envelope(self.language, 'independent-oracle', [r['target'] for r in self.language])
        report = experiment.score(self.language, prediction)
        self.assertEqual(report['metrics']['cell_reading/root_test']['count'], 10)
        self.assertEqual(report['metrics']['cell_head_reading/root_test']['count'], 10)
        for metric in report['metrics'].values():
            self.assertEqual(metric['accuracy'], 1.)
        self.assertEqual(report['metrics']['program_composition/structure_test']['count'], 72)
        self.assertEqual(report['metrics']['program_composition_eligible/structure_test']['count'], 36)

    def test_missing_invalid_and_deferred_do_not_shrink_denominator(self):
        rows = [r for r in self.language if r['task'] == 'cell_reading'][:3]
        predictions = experiment.envelope(rows, 'partial', [None, {'reading': 'wrong'}, rows[2]['target']])
        predictions['rows'].pop()
        metric = experiment.score(rows, predictions)['metrics']['cell_reading/train']
        self.assertEqual({k: metric[k] for k in ('count', 'correct', 'missing', 'invalid', 'answered')},
                         {'count': 3, 'correct': 0, 'missing': 1, 'invalid': 1, 'answered': 0})

    def test_duplicate_unknown_stale_and_detached_predictions_rejected(self):
        rows = self.language[:1]
        valid = experiment.envelope(rows, 'candidate', [rows[0]['target']])
        mutations = []
        bad = deepcopy(valid); bad['rows'] *= 2; mutations.append(bad)
        bad = deepcopy(valid); bad['rows'][0]['id'] = 'unknown'; mutations.append(bad)
        bad = deepcopy(valid); bad['rows'][0]['input_sha256'] = '0' * 64; mutations.append(bad)
        bad = deepcopy(valid); bad['dataset_sha256'] = '0' * 64; mutations.append(bad)
        bad = deepcopy(valid); bad['protocol_sha256'] = '0' * 64; mutations.append(bad)
        for bad in mutations:
            with self.assertRaises(ValueError):
                experiment.score(rows, bad)

    def test_boolean_scores_are_not_evidence_bits(self):
        self.assertFalse(experiment.valid_value('memory_primitive', True))
        self.assertFalse(experiment.valid_value('memory_update', [True, 0, 0, 0]))
        self.assertFalse(experiment.valid_value('memory_update', [1., 0, 0, 0]))

    def test_bert_not_run_is_absent_measurement_not_zero_accuracy(self):
        template = experiment.envelope(self.language, 'BERT')
        self.assertEqual(experiment.score(self.language, template)['metrics'], None)
        template['rows'] = [{'invented': 'result'}]
        with self.assertRaises(ValueError):
            experiment.score(self.language, template)

    def test_exported_test_inputs_have_no_target_or_label_bearing_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'export'
            experiment.export(out, self.rows)
            for split in ('root_test', 'lexical_test', 'structure_test', 'update_test', 'alternative_test'):
                rows = [json.loads(line) for line in gzip.decompress((out / (split + '.jsonl.gz')).read_bytes()).splitlines()]
                self.assertTrue(rows)
                for r in rows:
                    self.assertEqual(set(r), {'id', 'task', 'split', 'input', 'input_sha256'})
                    self.assertRegex(r['id'], '^[0-9a-f]{24}$')


@unittest.skipUnless(importlib.util.find_spec('numpy'), 'training-only NumPy required')
class LearnedSimulation(unittest.TestCase):
    def test_operator_gradients_match_portable_existing_encoder(self):
        import numpy as np
        p = training.initialize(116)
        row = {'cells': cells.parse_word('لَيْسَ'), 'target': 'negation'}
        loss, gradient = training.operator_loss_gradient(p, row)
        def portable_loss():
            hidden = cells.encode_state({k: v.tolist() for k, v in p.items()}, row['cells'])
            logits = [sum(a * b for a, b in zip(weights, hidden, strict=True)) for weights in p['head_operator']]
            top = max(logits)
            return math.log(sum(math.exp(v - top) for v in logits)) + top - logits[0]
        self.assertAlmostEqual(loss, portable_loss(), places=12)
        for key in (*cells.shared_shapes(), 'head_operator'):
            index = np.unravel_index(np.abs(gradient[key]).argmax(), gradient[key].shape)
            old = p[key][index]
            p[key][index] = old + 1e-5; plus = portable_loss()
            p[key][index] = old - 1e-5; minus = portable_loss()
            p[key][index] = old
            self.assertLess(abs(gradient[key][index] - (plus - minus) / 2e-5), 1e-7)

    def test_prediction_has_no_access_to_target_and_returns_raw_candidates(self):
        p = training.initialize(116)
        row = next(r for r in experiment.dataset() if r['task'] == 'program_composition' and r['eligible'])
        first = experiment.predict_language(p, row['task'], row['input'])
        row['target'] = 'other'; row['split'] = 'other'; row['source'] = 'other'
        self.assertEqual(experiment.predict_language(p, row['task'], row['input']), first)

    def test_retained_models_have_real_shared_updates_and_frozen_control(self):
        report = json.loads((experiment.DIRECTORY / 'run/evaluation.json').read_bytes())
        for seed in experiment.protocol()['seeds']:
            modes = report['language'][str(seed)]
            for change in modes['joint_encoder']['training']['parameter_change_l2'].values():
                self.assertGreater(change, 0.)
            frozen = modes['frozen_encoder']['training']['parameter_change_l2']
            self.assertTrue(all(frozen[key] == 0. for key in cells.shared_shapes()))
            self.assertTrue(all(value > 0 for key, value in frozen.items() if key.startswith('head_')))
            self.assertEqual(modes['joint_encoder']['training']['training_words'], 15)
            self.assertEqual(modes['joint_encoder']['training']['parameter_count'], 1440)

    def test_retained_outputs_are_recomputed_from_each_model(self):
        import numpy as np
        rows = [r for r in experiment.dataset() if r['task'] in ('cell_reading', 'program_composition')]
        report = json.loads((experiment.DIRECTORY / 'run/evaluation.json').read_bytes())
        for seed in experiment.protocol()['seeds']:
            for mode in experiment.protocol()['ablations']:
                path = experiment.DIRECTORY / 'run/models' / f'{seed}-{mode}.json'
                model = json.loads(path.read_bytes())
                p = {key: np.array(value) for key, value in model['parameters'].items()}
                values = [experiment.predict_language(p, r['task'], r['input']) for r in rows]
                prediction = experiment.envelope(rows, f'NABT/{mode}/{seed}', values)
                retained = json.loads((experiment.DIRECTORY / 'run/predictions' / f'{seed}-{mode}.json').read_bytes())
                self.assertEqual(prediction, retained)
                self.assertEqual(experiment.score(rows, prediction)['metrics'], report['language'][str(seed)][mode]['metrics'])


if __name__ == '__main__':
    unittest.main()
