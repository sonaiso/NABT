"""Conditional program supervision, complete coverage, and replay boundaries."""
from collections import Counter
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.lexical_training import ifadah_programs as owner, ntp_recursive as base
from tools.lexical_training import ntp_ifadah as net, train_ntp_ifadah as training

TEXT = 'لَيْسَ الْكَاتِبُ حَاضِرًا'
COMPOSED = 'هَلْ لَيْسَ الْكَاتِبُ حَاضِرًا؟'


class ProgramSourceContract(unittest.TestCase):
    def test_every_retained_source_has_coverage_and_exclusions_are_visible(self):
        _, splits, eligible = training.inputs()
        rows = [row for values in splits.values() for row in values]
        self.assertEqual(len(rows), 324)
        self.assertEqual(Counter(row['status'] for row in rows),
                         {'ELIGIBLE': 144, 'DEFER_NO_OPERATOR': 36,
                          'DEFER_OPERATOR_REPRESENTATION': 144})
        self.assertEqual({key: len(value) for key, value in eligible.items()},
                         {'train': 36, 'dev': 12, 'lexical_test': 60, 'structure_test': 36})
        novelty = training.input_novelty(eligible)
        self.assertEqual(novelty['train']['distinct_operator_inputs'], 3)
        self.assertEqual(novelty['lexical_test']['new_operator_inputs'], 0)
        self.assertEqual(novelty['structure_test']['new_operator_inputs'], 1)
        self.assertFalse({row['text_sha256'] for row in splits['train']} &
                         {row['text_sha256'] for row in splits['structure_test']})

    def test_incomplete_and_unsupported_operators_never_load_model(self):
        examples = {'الْكَاتِبُ حَاضِرٌ': 'DEFER_NO_OPERATOR',
                    'هَلْ كَانَ الْكَاتِبُ حَاضِرًا؟': 'DEFER_OPERATOR_REPRESENTATION',
                    'إِنَّ الْكَاتِبَ حَاضِرٌ': 'DEFER_OPERATOR_REPRESENTATION',
                    'هَلْ لَيْسَ': 'DEFER_OUTSIDE_FRAGMENT',
                    'لَيْسَ هَلْ الْكَاتِبُ حَاضِرًا؟': 'DEFER_OUTSIDE_FRAGMENT'}
        with patch.object(net, 'load', side_effect=AssertionError('model reached')):
            for text, status in examples.items():
                with self.subTest(text=text):
                    report = net.observe(text, 'source')
                    self.assertEqual(report['status'], status)
                    self.assertFalse(report['neural_selection_permitted'])
        projected = net.project('هَلْ كَانَ الْكَاتِبُ حَاضِرًا؟', 'source')['observations'][0]
        self.assertEqual(projected['operator_occurrences'][0]['cells'], [100, 91])
        with self.assertRaises(ValueError):
            net.groups(projected)

    def test_source_operator_occurrences_and_missing_witness(self):
        projected = net.project(COMPOSED, 'source')
        observation = projected['observations'][0]
        self.assertEqual(net.groups(observation), [[100, 91], [88, 111, 44]])
        for word in observation['operator_occurrences']:
            self.assertEqual(COMPOSED.encode()[slice(*word['utf8_span'])].decode(), word['surface'])
        retained = owner.understand(COMPOSED, 'source')
        missing = deepcopy(retained)
        del missing['readings'][0]['bindings']['g']
        with patch.object(owner, 'understand', return_value=missing), patch.object(
                net, 'load', side_effect=AssertionError('model reached')):
            self.assertEqual(net.observe(COMPOSED, 'source')['status'], 'DEFER_OPERATOR_WITNESS')
        detached = deepcopy(retained)
        detached['readings'][0]['bindings']['g']['utf8_span'] = [0, 8]
        with patch.object(owner, 'understand', return_value=detached):
            with self.assertRaises(ValueError):
                net.project(COMPOSED, 'source')

    def test_all_candidates_scored_without_owner_label_filtering(self):
        model = net.load()
        projected = net.project(TEXT, 'source')['observations'][0]
        choices = net.scores(model, net.groups(projected))
        self.assertEqual([choice['name'] for choice in choices], list(net.CANDIDATES))
        self.assertAlmostEqual(sum(choice['score'] for choice in choices), 1.)
        changed_label = owner.understand(TEXT, 'source')
        changed_label['readings'][0]['name'] = 'ask'
        with patch.object(owner, 'understand', return_value=changed_label):
            other = net.project(TEXT, 'source')['observations'][0]
        self.assertEqual(net.groups(projected), net.groups(other))
        self.assertEqual(choices, net.scores(model, net.groups(other)))
        trimmed = deepcopy(model)
        trimmed['candidates'] = ['negation']
        with self.assertRaises(ValueError):
            net.scores(trimmed, net.groups(projected))

    def test_missing_model_preserves_exact_source_observations(self):
        with patch.object(net, 'MODEL', Path('/missing/program-model.json')):
            report = net.observe(TEXT, 'source')
        self.assertEqual(report['status'], 'MODEL_UNAVAILABLE')
        self.assertEqual(report['observations'][0]['operator_occurrences'][0]['cells'], [88, 111, 44])
        self.assertEqual(report['authority'], 'NONE')
        self.assertFalse(report['grammar_certified'])

    def test_tied_or_corrupt_model_has_no_program_admission(self):
        zero = deepcopy(net.load())
        for key, value in zero['parameters'].items():
            zero['parameters'][key] = [[0.] * len(row) for row in value] if isinstance(value[0], list) else [0.] * len(value)
        with patch.object(net, 'load', return_value=zero):
            report = net.observe(TEXT, 'source')
        self.assertEqual(report['status'], 'DEFER_TIED_PROPOSAL')
        self.assertIsNone(report['observations'][0]['proposed_program'])
        self.assertFalse(report['neural_selection_permitted'])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'changed.json'
            path.write_text(training.canonical(zero))
            with patch.object(net, 'MODEL', path):
                self.assertEqual(net.observe(TEXT, 'source')['status'], 'MODEL_UNAVAILABLE')

    def test_internal_realization_identity_is_preserved_at_boundary(self):
        identity = 'x' * 128 + ':realization'
        result = net.observe(TEXT, identity)
        self.assertEqual(result['source_id'], identity)
        self.assertEqual(result['status'], 'PROPOSED')
        with self.assertRaises(owner.wire.ResourceLimit):
            net.project(TEXT, identity + 'x')

    def test_portable_observation_never_imports_numpy_or_torch(self):
        code = """
import builtins
old_import = builtins.__import__
def restricted(name, *args, **kwargs):
    if name.split('.')[0] in ('numpy', 'torch'):
        raise AssertionError('training dependency imported at inference')
    return old_import(name, *args, **kwargs)
builtins.__import__ = restricted
from tools.lexical_training.ntp_ifadah import observe
result = observe('لَيْسَ الْكَاتِبُ حَاضِرًا', 'portable')
assert result['status'] == 'PROPOSED', result
assert result['neural_selection_permitted'] is False
"""
        result = subprocess.run([sys.executable, '-B', '-S', '-c', code], cwd=base.ROOT,
                                env=dict(os.environ, PYTHONPATH='src:.'), text=True,
                                capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_fit_rejects_heldout_or_relabelled_sources_before_initialization(self):
        protocol, _, eligible = training.inputs()
        changed = deepcopy(eligible['train'])
        changed[0]['target_program'] = 'wish'
        with patch.object(training, 'initialize', side_effect=AssertionError('fit began')):
            for rows in (eligible['dev'], eligible['lexical_test'], eligible['structure_test'],
                         eligible['train'][:-1], list(reversed(eligible['train'])), changed):
                with self.assertRaises(ValueError):
                    training.fit(protocol, rows)
            with self.assertRaises(ValueError):
                training.fit(dict(protocol, epochs=1), eligible['train'])


@unittest.skipUnless(importlib.util.find_spec('numpy'), 'training-only NumPy required')
class ProgramTrainingContract(unittest.TestCase):
    def test_retained_fit_and_all_group_updates(self):
        from tools.lexical_training.train_apprentice import _difference
        protocol, _, eligible = training.inputs()
        fitted, audit = training.fit(protocol, eligible['train'])
        self.assertLessEqual(_difference(net.load(), training.model(fitted, protocol)), 2e-9)
        for group in ('bits', 'carrier', 'mark', 'compose', 'bias', 'program_force', 'program_frame'):
            self.assertGreater(audit['initial_gradient_l2'][group], 0., group)
            self.assertGreater(audit['parameter_change_l2'][group], 0., group)
        retained = json.loads((net.DIRECTORY / 'evaluation.json').read_bytes())
        self.assertEqual(len(retained['excluded_rows']), 180)
        self.assertEqual(retained['trained']['structure_test']['eligible_rows'], 36)
        self.assertEqual(retained['trained']['structure_test']['deferred_rows'], 36)
        self.assertFalse(retained['general_ifadah_established'])
        self.assertFalse(retained['instruction_intent_learned'])


if __name__ == '__main__':
    unittest.main()
