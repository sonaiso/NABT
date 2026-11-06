"""Optional CPU learning tests: real updates and persisted inference replay."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

HAS_TORCH = importlib.util.find_spec('torch') is not None and importlib.util.find_spec('numpy') is not None
ROOT = Path(__file__).resolve().parents[1]
if os.environ.get('NABT_REQUIRE_AWAMIL_TRAINING') == '1' and not HAS_TORCH:
    raise RuntimeError('The awamil learning gate requires CPU torch and numpy')


@unittest.skipUnless(HAS_TORCH, 'optional CPU torch/numpy training dependencies')
class AwamilLearningTests(unittest.TestCase):
    def test_actual_updates_and_no_overwrite_of_first_evaluation(self):
        from tools.lexical_training.awamil_agent import train, PROTOCOL, Learner
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'run'
            result = train(path, protocol={**PROTOCOL, 'epochs': 1})
            self.assertGreater(result['optimizer_updates'], 0)
            self.assertGreater(result['weight_delta_l2'], 0)
            learner = Learner(path/'model.json')
            self.assertEqual(len(learner.scores('كان وأخواتها')), 212)
            with self.assertRaisesRegex(ValueError, 'first-test'):
                train(path)

    def test_degraded_model_stays_out_of_ranking_and_reloads_identically(self):
        from tools.lexical_training.awamil_agent import Learner, train, PROTOCOL
        from tools.grammar_catalog.awamil import AwamilIndex
        # Bind fresh weights to the actual installed catalogue. Historical
        # first-test artifacts are immutable and must not be silently rebound.
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)/'run'
            train(run, protocol={**PROTOCOL, 'epochs': 1})
            obj = json.loads((run/'model.json').read_text())
            def zero(value):
                return [zero(v) for v in value] if isinstance(value, list) else 0.0
            obj['state_dict'] = {k: zero(v) for k, v in obj['state_dict'].items()}
            path = Path(folder)/'degraded.json'
            path.write_text(json.dumps(obj))
            learner = Learner(path)
            self.assertFalse(learner.ranking_admitted)
            index = AwamilIndex()
            q = 'إنّ وأخواتها'
            base = index.search(q)
            proposed = index.search(q, learned=learner)
            self.assertEqual(base['candidates'], proposed['candidates'])
            self.assertEqual(learner.scores(q), Learner(path).scores(q))

    def test_historical_weights_are_not_silently_rebound_after_catalogue_change(self):
        from tools.lexical_training.awamil_agent import Learner
        for historical in ('evidence/awamil_agent_v1/run_01/model.json',
                           'evidence/context_application_v1/awamil_retrain/model.json'):
            with self.subTest(path=historical), self.assertRaisesRegex(ValueError,'MODEL_CATALOG_MISMATCH'):
                Learner(ROOT/historical)

    def test_model_cannot_change_catalog_or_self_assert_admission(self):
        from tools.lexical_training.awamil_agent import Learner
        with tempfile.TemporaryDirectory() as folder:
            obj = json.loads((ROOT/'evidence/awamil_agent_v1/run_01/model.json').read_text())
            obj['catalog_sha256'] = '0'*64
            path = Path(folder)/'forged.json'
            path.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError, 'MODEL_CATALOG_MISMATCH'):
                Learner(path)


if __name__ == '__main__':
    unittest.main()
