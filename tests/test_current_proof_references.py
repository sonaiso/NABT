"""Keep separately generated layer indices on one compiled proof snapshot."""
import json
from pathlib import Path
import unittest

from tools import proof_catalog

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "evidence/aligned_acquisition_v1/integration"


class CurrentProofReferencesTests(unittest.TestCase):
    def test_all_layer_indices_bind_the_same_current_compiled_snapshot(self):
        compiled = json.loads((CURRENT / "proof_catalog.json").read_text())
        fingerprint = proof_catalog.digest(compiled)
        fields = {"grammar_link_summary": "compiled_proof_catalog_sha256",
                  "mantuq_proof_links": "compiled_catalog_sha256",
                  "linguistic_proof_links": "compiled_catalog_sha256",
                  "licensed_proof_links": "compiled_catalog_sha256"}
        for name, field in fields.items():
            with self.subTest(index=name):
                report = json.loads((CURRENT / (name + ".json")).read_text())
                self.assertEqual(report[field], fingerprint)
        for name in ("formal/theorems.json", "formal/Nabt.lean", "formal/Nabt/AlignedAcquisition.lean",
                     "formal/Nabt/LicensedInference.lean"):
            self.assertEqual(compiled["inputs"][name], proof_catalog.file_sha(ROOT / name))

    def test_existing_inference_contracts_remain_resolvable_after_acquisition(self):
        compiled = json.loads((CURRENT / "proof_catalog.json").read_text())
        declarations = {row["name"]: row for row in compiled["theorems"]}
        links = json.loads((CURRENT / "licensed_proof_links.json").read_text())
        for reference in links["contracts"] + links["related_existing_contracts"]:
            row = declarations[reference["name"]]
            self.assertEqual(reference["statement_sha256"], row["statement_sha256"])
            self.assertEqual(reference["source_sha256"], compiled["inputs"][reference["source_path"]])
        self.assertIn("Nabt.LicensedInference.verified_execution", declarations)
        self.assertIn("Nabt.AlignedAcquisition.verified_binding", declarations)
