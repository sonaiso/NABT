"""Boundary tests for an experimental head that cannot rewrite the owner."""
from copy import deepcopy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.lexical_training import relational_alignment as runtime, relational_training as training
from tools.grammar_catalog import relational, gateway
from tests.test_relational_bridge import NATIVE


class RelationalAlignmentInstallation(unittest.TestCase):
    def test_release_gate_requires_retained_model(self):
        if os.environ.get("NABT_REQUIRE_RELATIONAL_NATIVE"):
            self.assertTrue(runtime.MODEL.is_file())
            self.assertTrue(runtime.MODEL.with_name("FIRST_TEST.json").is_file())


@unittest.skipUnless(NATIVE.is_file() and runtime.MODEL.is_file(), "Build native and install retained experiment")
class RelationalAlignment(unittest.TestCase):
    def test_retained_first_test_has_actual_updates_and_failure_accounting(self):
        report=json.loads(runtime.MODEL.with_name("FIRST_TEST.json").read_text())
        self.assertGreater(report["parameter_delta_l2"], 0)
        self.assertEqual(report["encoder_parameter_delta_l2"], 0)
        self.assertLess(report["portable_max_abs_error"], 1e-9)
        self.assertFalse(report["protocol"]["test_used_for_selection"])
        self.assertGreater(report["metrics"]["test_context"]["background_false_positive"], 0)
        for name,rows in training.dataset().items():
            self.assertEqual(runtime.digest(rows),report["partition_sha256"][name])

    def test_all_canonical_graphs_survive_neural_ranking_without_bindings(self):
        result=runtime.rank({"text":"اصفرار مُصْفَرّ كبر"})
        self.assertEqual(result["status"], "PROPOSED", result)
        self.assertEqual(result["authority"], "NONE")
        self.assertFalse(result["bindings_generated"])
        for occurrence in result["occurrences"]:
            self.assertEqual({r["sense"] for r in occurrence["candidates"]}, {"اصفرار", "كبر_السن", "عظم"})
            for candidate in occurrence["candidates"]:
                self.assertEqual(candidate["ontological_signature"]["slots"],
                                 ["event", "bearer", "genus", "property", "time", "place"])

    def test_native_and_model_failures_do_not_create_claims(self):
        with patch.object(runtime, "schema_catalogue", side_effect=ValueError("missing")):
            result=runtime.rank({"text":"اصفرّ"})
        self.assertEqual(result["status"], "DEFER")
        self.assertEqual(result["occurrences"], [])
        self.assertEqual(runtime.rank({"text":"ا"*200})["status"], "DEFER")

    def test_shape_finite_identity_and_training_mutations_are_rejected(self):
        base,base_sha=runtime.shared.load_model()
        meanings=runtime.definitions(runtime.schema_catalogue())
        original=json.loads(runtime.MODEL.read_text())
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"model.json"
            (Path(td)/"train.json").write_bytes(runtime.MODEL.with_name("train.json").read_bytes())
            for field,value in [("schema_sha256", "0"*64), ("shared_model_sha256","0"*64),
                                ("weight",[]), ("labels",["invented"]), ("training_sha256","0"*64)]:
                bad=deepcopy(original); bad[field]=value; path.write_text(json.dumps(bad))
                with patch.object(runtime,"MODEL",path):
                    with self.assertRaises(ValueError):runtime.load_model(base_sha,meanings)

    def test_public_optional_head_does_not_change_symbolic_result(self):
        request={"schema":gateway.REQUEST_SCHEMA,"route":"relations.analyze",
                 "payload":{"text":"اصفرار", "neural_continuity":True}}
        result=gateway.run(request)
        self.assertEqual(result["status"],"EXECUTED",result)
        owner=result["execution"]["owner_result"]
        plain=relational.analyze({"text":"اصفرار"})
        self.assertEqual(owner["ontology_bridge"],plain["ontology_bridge"])
        self.assertEqual(owner["semantic_continuity"],plain["semantic_continuity"])
        self.assertEqual(owner["neural_continuity"]["authority"],"NONE")
        self.assertTrue(gateway.accept_output(result,expected_request=request)["valid"])

    def test_public_caller_cannot_inject_models_or_acceptance(self):
        for key,value in [("model_path","/tmp/model"),("schema_certified",True),("neural_continuity",1)]:
            with self.assertRaises(ValueError):relational.validate({"text":"اصفرار",key:value})

    def test_missing_optional_resources_preserve_owner_and_bind_absence(self):
        baseline=relational.analyze({"text":"اصفرار"})
        original=Path.read_bytes
        for missing in (runtime.MODEL, runtime.MODEL.with_name("train.json")):
            def read_bytes(path):
                if path == missing:raise FileNotFoundError(str(path))
                return original(path)
            with self.subTest(path=missing.name), patch.object(Path,"read_bytes",read_bytes):
                result=relational.analyze({"text":"اصفرار","neural_continuity":True})
                self.assertEqual(result["neural_continuity"]["status"],"DEFER")
                self.assertEqual(result["ontology_bridge"],baseline["ontology_bridge"])
                self.assertEqual(result["semantic_continuity"],baseline["semantic_continuity"])
                snapshot=gateway.snapshot()
                self.assertEqual(snapshot["files"][missing.relative_to(runtime.shared.ROOT).as_posix()],"UNAVAILABLE")
            self.assertNotEqual(snapshot,gateway.snapshot())


if __name__ == "__main__":unittest.main()
