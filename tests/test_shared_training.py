"""Optional CPU training gate, mandatory in the dedicated workflow."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

READY = (importlib.util.find_spec("torch") is not None
         and importlib.util.find_spec("numpy") is not None
         and Path("formal/.lake/build/bin/lexicalDenotation").is_file())
if os.environ.get("NABT_REQUIRE_SHARED_TRAINING") == "1" and not READY:
    raise RuntimeError("Shared training gate needs torch, numpy and lexicalDenotation")


@unittest.skipUnless(READY, "optional CPU training dependencies")
class SharedTrainingTests(unittest.TestCase):
    def test_real_joint_updates_and_portable_replay(self):
        from tools.lexical_training import shared_training as train
        with tempfile.TemporaryDirectory() as directory:
            result=train.train_run(Path(directory)/"run")
        self.assertEqual(result["optimizer_steps"], train.PROTOCOL["epochs"])
        self.assertGreater(result["parameter_delta_l2"],0)
        self.assertLess(result["portable_max_abs_error"],1e-4)
        self.assertEqual(set(result["metrics"]["neural"]),set(train.runtime.HEADS))
        self.assertTrue(all(row["n"]>0 for row in result["metrics"]["neural"].values()))
        self.assertFalse(result["learned_predictions_grant_authority"])

    def test_morphology_partition_and_no_exact_text_leakage(self):
        from tools.lexical_training.shared_training import dataset,PROTOCOL
        train,test,_=dataset()
        self.assertFalse(set(PROTOCOL["train_roots"]) & set(PROTOCOL["test_roots"]))
        self.assertFalse({r["text"] for r in train} & {r["text"] for r in test})
        self.assertTrue(any(r["group"]=="قم" for r in test))


if __name__ == "__main__":
    unittest.main()
