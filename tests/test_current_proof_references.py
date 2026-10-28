"""Keep separately generated layer indices on one compiled proof snapshot."""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import unittest

from tools import proof_catalog

ROOT = Path(__file__).resolve().parents[1]
_selector = (ROOT / "integrations/current_proof_references.mk").read_text()
CURRENT = ROOT / re.search(r"^NABT_PROOF_REFERENCE_DIR \?= (\S+)$", _selector, re.M).group(1)


class CurrentProofReferencesTests(unittest.TestCase):
    def test_all_layer_indices_bind_the_same_current_compiled_snapshot(self):
        compiled = json.loads((CURRENT / "proof_catalog.json").read_text())
        fingerprint = proof_catalog.digest(compiled)
        fields = {"grammar_link_summary": "compiled_proof_catalog_sha256",
                  "mantuq_proof_links": "compiled_catalog_sha256",
                  "linguistic_proof_links": "compiled_catalog_sha256",
                  "licensed_proof_links": "compiled_catalog_sha256",
                  "article_proof_links": "compiled_proof_catalog_sha256",
                  "sourced_proof_links": "compiled_proof_catalog_sha256"}
        for name, field in fields.items():
            with self.subTest(index=name):
                report = json.loads((CURRENT / (name + ".json")).read_text())
                self.assertEqual(report[field], fingerprint)
        for name, expected_hash in compiled["inputs"].items():
            with self.subTest(source=name):
                self.assertEqual(expected_hash, proof_catalog.file_sha(ROOT / name))
        manifest = json.loads((ROOT / "formal/theorems.json").read_text())["theorems"]
        self.assertEqual([row["name"] for row in compiled["theorems"]], manifest)

    def test_existing_make_gates_select_current_snapshots(self):
        # Inspect actual standalone and combined gate commands. Merely checking
        # a hard-coded evidence directory would miss stale Makefile selectors.
        gates = {
            "grammar_catalog": ("proof-catalog", ["proof_catalog", "grammar_link_summary"]),
            "mantuq_inference": ("mantuq-inference", ["mantuq_proof_links"]),
            "linguistic_truth": ("linguistic-truth", ["linguistic_proof_links"]),
            "licensed_inference": ("licensed-inference", ["licensed_proof_links"]),
        }
        env = {key: value for key, value in os.environ.items()
               if key not in {"MAKEFLAGS", "MFLAGS", "MAKEFILES", "NABT_PROOF_REFERENCE_DIR",
                              "PROOF_CATALOG_REFERENCE", "GRAMMAR_LINK_REFERENCE",
                              "MANTUQ_LINK_REFERENCE", "LINGUISTIC_LINK_REFERENCE",
                              "LICENSED_LINK_REFERENCE"}}
        selections = [[name] for name in gates] + [list(gates)]
        for names in selections:
            with self.subTest(integrations=names):
                command = ["make", "--no-print-directory", "-n", "-f", "Makefile"]
                for name in names:
                    command.extend(["-f", "integrations/" + name + ".mk"])
                command.extend(gates[name][0] for name in names)
                result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                        text=True, check=True, timeout=30)
                references = []
                for line in result.stdout.splitlines():
                    tokens = shlex.split(line)
                    references.extend(tokens[i + 1] for i, token in enumerate(tokens[:-1])
                                      if token == "--check")
                for name in names:
                    for snapshot in gates[name][1]:
                        relative = (CURRENT / (snapshot + ".json")).relative_to(ROOT).as_posix()
                        self.assertIn(relative, references)

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
        self.assertIn("Nabt.AlignedAcquisitionV2.verified_binding", declarations)
        self.assertIn("Nabt.ConnectedAcquisitionV3.verified_phrase_sourceful", declarations)
        self.assertIn("Nabt.AcquiredSyntaxV3.parser_exact", declarations)
