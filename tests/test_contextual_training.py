import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

READY=(importlib.util.find_spec('torch') is not None and importlib.util.find_spec('numpy') is not None
       and Path('formal/.lake/build/bin/lexicalDenotation').is_file())
if os.environ.get('NABT_REQUIRE_SHARED_TRAINING')=='1' and not READY:
    raise RuntimeError('Contextual training requires native definitions and CPU torch')


@unittest.skipUnless(READY,'optional CPU training dependencies')
class ContextualTraining(unittest.TestCase):
    def test_real_shared_updates_and_all_token_portable_parity(self):
        from tools.lexical_training import contextual_training as train
        with tempfile.TemporaryDirectory() as root, patch.dict(train.PROTOCOL,epochs=2):
            result=train.train_run(Path(root)/'run')
        self.assertEqual(result['optimizer_steps'],2)
        self.assertGreater(result['shared_encoder_delta_l2'],0)
        self.assertLess(result['portable_max_abs_error'],1e-4)
        self.assertEqual(result['metrics']['tokens'],result['partition_counts']['test']['tokens'])
        self.assertEqual(result['portable_metrics']['true_positive'],result['metrics']['true_positive'])
        self.assertFalse(result['protocol']['test_selection'])


if __name__=='__main__':unittest.main()
