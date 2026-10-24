from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import train_certificate_ranker as training
from tools.training_readiness import components, intake


class IntakeContracts(unittest.TestCase):
    def test_joint_split_uses_transitive_components(self):
        rows = [dict(id='a', roots=['r1'], sources=['s1']),
                dict(id='b', roots=['r1'], sources=['s2']),
                dict(id='c', roots=['r2'], sources=['s2'])]
        result = components(rows, ['roots', 'sources'])
        self.assertEqual(result['groups'], [['a', 'b', 'c']])
        self.assertFalse(result['three_way_split_possible'])

    def test_missing_roots_do_not_become_disjoint_roots(self):
        self.assertEqual(components([dict(id='x', roots=[])], ['roots'])['status'], 'UNMEASURED')
        with self.assertRaises(ValueError):
            components([dict(id='x', roots=['a']), dict(id='x', roots=['b'])], ['roots'])

    def test_public_holdout_is_review_material_not_automatic_training_gold(self):
        queue = intake()
        self.assertEqual(len(queue['rows']), 36)
        self.assertEqual(queue['eligible_arabic_sft_examples'], 0)
        self.assertEqual(set(queue['counts']), {'positive', 'near_negative', 'alternative_readings', 'coverage_gap'})
        self.assertTrue(all(not r['hidden'] and not r['training_eligible'] for r in queue['rows']))
        self.assertEqual(queue['joint_source_root_template_split']['status'], 'UNMEASURED')

    def test_rank_order_keeps_ties_and_every_reading(self):
        vectors = [[1.0] * len(training.FEATURES)] * 4
        self.assertEqual(training.ranked_indices([0.0] * len(training.FEATURES), vectors), list(range(4)))
        with self.assertRaises(ValueError):
            training.ranked_indices([float('nan')] * len(training.FEATURES), vectors)

    def test_optimizer_rejects_unmeasured_and_boolean_labels(self):
        row = {'features': [1.0] * len(training.FEATURES), 'measurement': 'UNMEASURED', 'label': None}
        with self.assertRaises(ValueError):
            training.fit([row])
        for label in (True, False, 2, -1):
            with self.assertRaises(ValueError):
                training.fit([{**row, 'measurement': 'MEASURED', 'label': label}])
        with self.assertRaises(ValueError):
            training.fit([], epochs=True)

    def test_optimizer_really_updates_and_is_reproducible(self):
        # Independent separable vectors, not production certificates/labels.
        rows = [{'features': [1.0, float(y), *([0.0] * (len(training.FEATURES)-2))],
                 'label': y, 'measurement': 'MEASURED'} for y in (0, 1)]
        weights, curve = training.fit(rows)
        self.assertLess(curve[-1]['log_loss'], curve[0]['log_loss'])
        self.assertGreater(training.score(weights, rows[1]['features']), training.score(weights, rows[0]['features']))
        self.assertEqual((weights, curve), training.fit(rows))

    def test_receipt_noncanonical_json_is_not_a_label(self):
        for raw in (b'{"a":1,"a":2}', b'{"x":-0}', b'{"x":1.0}', b'{"x":1e0}', b'{"x":NaN}', b'[]', b'{"x":"\\ud800"}'):
            with self.assertRaises((ValueError, UnicodeError)):
                training.strict_receipt(raw)

    def test_first_run_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / 'keep'
            marker.write_text('first result')
            with self.assertRaises(FileExistsError):
                training.execute(Path(temp), None)
            self.assertEqual(marker.read_text(), 'first result')

    def test_no_checker_preserves_null_labels(self):
        row = training.check(b'a', b'b', {}, Path('/nonexistent/nabt-training-checker'))
        self.assertEqual(row['measurement'], 'UNMEASURED')
        self.assertIsNone(row['label'])


class NativeTrainingContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.checker = training.pilot.checker_path()
        except training.pilot.PilotError:
            if 'NABT_VERIFIED_READING' in os.environ:
                raise
            raise unittest.SkipTest('native verifiedReading not built')

    def setUp(self):
        self.raw = 'سالم هو حكيم.\n'.encode()
        self.query = 'هل سالم هو عالم؟\n'.encode()
        self.cert = training.ground.propose(self.raw, self.query)

    def test_unknown_is_valid_certificate_not_negative_language(self):
        row = training.check(self.raw, self.query, self.cert, self.checker)
        self.assertEqual((row['measurement'], row['label'], row['semantic_status']), ('MEASURED', 1, 'UNKNOWN'))

    def test_every_mutation_rejected_against_original_inputs(self):
        for kind, cert in training.candidates(self.cert):
            with self.subTest(kind=kind):
                row = training.check(self.raw, self.query, cert, self.checker)
                self.assertEqual(row['measurement'], 'MEASURED')
                self.assertEqual(row['label'], int(kind == 'original'))

    def test_forged_world_flag_and_deleted_trace_reject(self):
        a = deepcopy(self.cert)
        a['world_truth_established'] = True
        b = deepcopy(self.cert)
        b['steps'] = []
        for cert in (a, b):
            self.assertEqual(training.check(self.raw, self.query, cert, self.checker)['label'], 0)

    def test_crash_timeout_and_bad_receipt_never_become_training_negatives(self):
        crashed = subprocess.CompletedProcess([], -11, b'', b'')
        with patch.object(training.subprocess, 'run', return_value=crashed):
            self.assertIsNone(training.check(self.raw, self.query, self.cert, self.checker)['label'])
        with patch.object(training.subprocess, 'run', side_effect=subprocess.TimeoutExpired('checker', 1)):
            result = training.check(self.raw, self.query, self.cert, self.checker)
            self.assertIsNone(result['label'])
            self.assertEqual(result['error'], 'RESOURCE_LIMIT')
        forged = dict(law_id=training.ground.LAW_ID, scope='canonical_ground_source_entailment',
                      world_truth_established=False, all_arabic_complete=False, verified=True,
                      status='SUPPORTED', source_id='text', revision='1', source_scope='default',
                      source_text=self.raw.decode() + 'changed', query_text=self.query.decode())
        with patch.object(training.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(forged).encode(), b'')):
            self.assertIsNone(training.check(self.raw, self.query, self.cert, self.checker)['label'])

    def test_setup_failure_keeps_every_planned_attempt_and_stops_training(self):
        with tempfile.TemporaryDirectory() as temp:
            result = training.execute(Path(temp) / 'new-run', Path('/nonexistent/nabt-training-checker'))
            self.assertEqual(result['planned_examples'], 90)
            self.assertEqual(result['measurements'], {'UNMEASURED': 90})
            self.assertFalse(result['training_executed'])
            self.assertFalse(result['passed'])

    def test_ranker_false_positive_cannot_authorize_a_forged_proof(self):
        forged = deepcopy(self.cert)
        forged['known'][0]['predicate'] = 'مخترع'
        self.assertEqual(training.features(self.raw, self.query, forged),
                         training.features(self.raw, self.query, self.cert))
        model = dict(schema='nabt.certificate-ranker.v1', features=training.FEATURES,
                     weights=[1.0] * len(training.FEATURES), authority='proposal-order-only')
        result = training.rank_and_check(self.raw, self.query, [forged, self.cert], model, self.checker)
        self.assertEqual([a['label'] for a in result['attempts']], [0, 1])
        self.assertEqual(result['selected_original_index'], 1)
        self.assertEqual(result['semantic_status'], 'UNKNOWN')
        unavailable = training.rank_and_check(self.raw, self.query, [self.cert], model, Path('/nonexistent/checker'))
        self.assertIsNone(unavailable['selected_original_index'])
        self.assertIsNone(unavailable['semantic_status'])
        for value in (True, float('nan')):
            with self.assertRaises(ValueError):
                training.rank_and_check(self.raw, self.query, [self.cert], {**model, 'weights': [value] * len(training.FEATURES)}, self.checker)
