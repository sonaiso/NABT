"""Reference failures and admission boundaries for curriculum metadata."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.lexical_training import learning_framework as f


def fixture():
    objective = {
        "id": "cells", "label_ar": "هوية الخلية", "stage": "representation",
        "prerequisites": [], "agent_id": "teacher", "domain_ids": ["communication"],
        "axis_ids": ["word_kind"], "matrix_ids": ["designation"], "method_ids": ["formal"],
        "owner_modules": ["Nabt.Cell"], "source_ids": ["grammar"],
        "knowledge_ar": "الحامل والحالة", "skill_ar": "استعادة الخلية",
        "disposition_ar": "حفظ الموضع", "inputs": ["خلية"], "outputs": ["ترميز"],
        "formative": {"task_ar": "مقابلة مستقلة", "feedback_ar": "راجع الشاهد", "contrast_ar": "غيّر المصدر"},
        "summative": {"task_ar": "وقوع جديد", "split_keys": ["source_lineage"],
                      "critical_failures": ["SOURCE_MISMATCH"], "metrics": ["false_accepts"]},
        "runtime_refs": ["tools/arabic_training/sign_curriculum.py"],
        "acquisition_obligation_ar": "محاذاة الرصد بالوقوع", "neural_status": "NOT_TRAINED",
        "legacy_card_ids": ["L0.1"],
    }
    second = deepcopy(objective)
    second.update(id="composition", prerequisites=["cells"], legacy_card_ids=["L1.1"])
    return {"schema": f.SCHEMA, "basis_commit": "a" * 40,
            "sources": [{"id": "grammar", "description": "معطيات مرجعية"}],
            "stages": [{"id": "representation", "prerequisites": []}], "methods": [{"id": "formal"}],
            "agents": [{"id": "teacher"}], "objectives": [objective, second],
            "assessment": {"formative": "ملاحظة الخطأ", "summative": "اختبار مستقل"},
            "neural_design": {"status": "PROPOSED"},
            "legacy_alignment": {"scope": "historical card links",
                                 "cards": [{"id": "L0.1"}, {"id": "L1.1"}]}}


CONTEXT = {"compiled": {"theorems": [{"module": "Nabt.Cell"}]},
           "axis_ids": {"word_kind"}, "matrix_ids": {"designation"},
           "domain_ids": {"communication"}}


class FrameworkValidationTests(unittest.TestCase):
    def test_exports_preserve_metadata_without_claiming_training_or_mastery(self):
        document = fixture()
        result = f.validate(document, **CONTEXT)
        self.assertEqual({k: v for k, v in result.items() if k != "validation"}, document)
        self.assertEqual(result["validation"]["prerequisite_order"], ["cells", "composition"])
        self.assertEqual(result["validation"]["authority"], "CURRICULUM_REFERENCE_VALIDATION_ONLY")
        for field in ("mastery_certified", "neural_training_performed", "runtime_execution_performed"):
            self.assertFalse(result["validation"][field])
        result["objectives"][0]["prerequisites"].append("forged")
        self.assertEqual(document["objectives"][0]["prerequisites"], [])

    def test_every_reference_namespace_rejects_missing_targets(self):
        for field in ("prerequisites", "domain_ids", "axis_ids", "matrix_ids",
                      "owner_modules", "source_ids", "legacy_card_ids", "method_ids"):
            with self.subTest(field=field):
                doc = fixture(); doc["objectives"][0][field] = ["missing"]
                with self.assertRaises(ValueError):
                    f.validate(doc, **CONTEXT)
        for field in ("stage", "agent_id"):
            doc = fixture(); doc["objectives"][0][field] = "missing"
            with self.assertRaises(ValueError):
                f.validate(doc, **CONTEXT)

    def test_record_ids_and_references_must_be_unique_typed_text(self):
        for collection in ("sources", "stages", "methods", "agents", "objectives"):
            doc = fixture(); doc[collection].append(deepcopy(doc[collection][0]))
            with self.subTest(collection=collection), self.assertRaises(ValueError):
                f.validate(doc, **CONTEXT)
        for field in ("source_ids", "owner_modules", "runtime_refs", "legacy_card_ids", "method_ids"):
            doc = fixture(); doc["objectives"][0][field] *= 2
            with self.subTest(field=field), self.assertRaises(ValueError):
                f.validate(doc, **CONTEXT)
        doc = fixture(); doc["stages"][0]["id"] = True
        with self.assertRaises(ValueError):
            f.validate(doc, **CONTEXT)

    def test_self_reference_and_multi_node_cycles_are_rejected(self):
        for prior in ("cells", "composition"):
            doc = fixture(); doc["objectives"][0]["prerequisites"] = [prior]
            with self.subTest(prior=prior), self.assertRaises(ValueError):
                f.validate(doc, **CONTEXT)

    def test_stage_dependencies_are_separate_reference_graphs(self):
        doc = fixture()
        doc["stages"].append({"id": "composition", "prerequisites": ["representation"]})
        result = f.validate(doc, **CONTEXT)
        self.assertEqual(result["validation"]["stage_prerequisite_order"],
                         ["representation", "composition"])
        for priors in (["missing"], ["representation"], ["composition"], ["composition", "composition"]):
            broken = deepcopy(doc); broken["stages"][0]["prerequisites"] = priors
            with self.subTest(priors=priors), self.assertRaises(ValueError):
                f.validate(broken, **CONTEXT)

    def test_all_retained_cards_are_mapped_without_dangling_or_duplicate_ids(self):
        for card in ({"id": "unmapped"}, {"id": "L0.1"}):
            doc = fixture(); doc["legacy_alignment"]["cards"].append(card)
            with self.subTest(card=card), self.assertRaises(ValueError):
                f.validate(doc, **CONTEXT)
        doc = fixture(); doc["objectives"][0]["legacy_card_ids"] = []
        with self.assertRaises(ValueError):
            f.validate(doc, **CONTEXT)
        result = f.validate(fixture(), **CONTEXT)["validation"]
        self.assertEqual(result["legacy_card_count"], 2)
        self.assertEqual(result["legacy_cards_mapped"], 2)

    def test_paths_must_be_existing_canonical_repository_files(self):
        for path in ("../AGENTS.md", "/etc/passwd", "tools/../AGENTS.md", "tools//x.py",
                     "tools\\x.py", ".git/config", "missing.py", "tools"):
            doc = fixture(); doc["objectives"][0]["runtime_refs"] = [path]
            with self.subTest(path=path), self.assertRaises(ValueError):
                f.validate(doc, **CONTEXT)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repository"; root.mkdir()
            outside = Path(temp) / "outside.py"; outside.write_text("external")
            (root / "escape.py").symlink_to(outside)
            doc = fixture()
            for row in doc["objectives"]:
                row["runtime_refs"] = ["escape.py"]
            with self.assertRaises(ValueError):
                f.validate(doc, root=root, **CONTEXT)

    def test_empty_objectives_and_assessment_fields_are_rejected(self):
        for field in ("knowledge_ar", "skill_ar", "disposition_ar", "inputs", "outputs",
                      "formative", "summative"):
            doc = fixture(); doc["objectives"][0][field] = " "
            with self.subTest(field=field), self.assertRaises(ValueError):
                f.validate(doc, **CONTEXT)
        for field in ("sources", "stages", "methods", "agents", "objectives", "assessment"):
            doc = fixture(); doc[field] = []
            with self.subTest(field=field), self.assertRaises(ValueError):
                f.validate(doc, **CONTEXT)

    def test_source_and_agent_paths_are_resolved_as_current_references(self):
        doc = fixture()
        doc["sources"][0]["path"] = "formal/Nabt/Cell.lean"
        doc["agents"][0]["existing_paths"] = ["tools/lexical_training/teaching.py"]
        self.assertEqual(f.validate(doc, **CONTEXT)["validation"]["referenced_file_count"], 3)
        for path in ("../AGENTS.md", "missing.py"):
            bad_source = deepcopy(doc); bad_source["sources"][0]["path"] = path
            bad_agent = deepcopy(doc); bad_agent["agents"][0]["existing_paths"] = [path]
            for invalid in (bad_source, bad_agent):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    f.validate(invalid, **CONTEXT)

    def test_structured_empty_inputs_outputs_and_assessments_are_rejected(self):
        for field in ("inputs", "outputs"):
            for value in ([" "], [None], [], ["usable", ""], {"text": "usable"}):
                doc = fixture(); doc["objectives"][0][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    f.validate(doc, **CONTEXT)
        for field in ("formative", "summative"):
            for value in ({"task_ar": ""}, {"task": ""}, {"task": "valid but wrong schema"}, ["task"]):
                doc = fixture(); doc["objectives"][0][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    f.validate(doc, **CONTEXT)
            for key, original in fixture()["objectives"][0][field].items():
                for invalid in ((" ", None) if isinstance(original, str) else ([" "], [None], [])):
                    doc = fixture(); doc["objectives"][0][field][key] = invalid
                    with self.subTest(field=field, key=key, invalid=invalid), self.assertRaises(ValueError):
                        f.validate(doc, **CONTEXT)

    def test_neural_and_assessment_paths_are_validated_and_counted(self):
        doc = fixture()
        doc["neural_design"]["current_paths"] = ["tools/lexical_training/senses.py"]
        doc["assessment"]["route_examples"] = {"learning": "examples/cognitive_teaching/learning.json"}
        report = f.validate(doc, **CONTEXT)["validation"]
        self.assertEqual(report["referenced_file_count"], 3)
        self.assertEqual(report["runtime_reference_count"], 3)
        for path in ("../AGENTS.md", "missing.py", None, " "):
            neural = deepcopy(doc); neural["neural_design"]["current_paths"] = [path]
            assessment = deepcopy(doc); assessment["assessment"]["route_examples"]["learning"] = path
            for invalid in (neural, assessment):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    f.validate(invalid, **CONTEXT)
        doc["assessment"]["route_examples"] = ["examples/cognitive_teaching/learning.json"]
        with self.assertRaises(ValueError):
            f.validate(doc, **CONTEXT)

    def test_forged_progress_cannot_create_a_mastery_certificate(self):
        for field in ("mastery_certified", "validation", "passed"):
            doc = fixture(); doc[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                f.validate(doc, **CONTEXT)
        doc = fixture(); doc["objectives"][0]["mastery_certified"] = True
        with self.assertRaises(ValueError):
            f.validate(doc, **CONTEXT)
        doc = fixture(); doc["assessment"]["claimed_success"] = True
        result = f.validate(doc, **CONTEXT)
        self.assertFalse(result["validation"]["mastery_certified"])

    def test_bounded_loader_rejects_duplicate_keys_and_oversized_documents(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "framework.json"
            with patch.object(f, "PATH", path):
                path.write_text(json.dumps(fixture(), ensure_ascii=False))
                self.assertIn("source_sha256", f.framework(**CONTEXT)["validation"])
                for raw in (b'{"schema":"first","schema":"second"}', b" " * (f.MAX_BYTES + 1)):
                    path.write_bytes(raw)
                    with self.assertRaises((ValueError, f.wire_owner.ResourceLimit)):
                        f.framework(**CONTEXT)


class InstalledFrameworkTests(unittest.TestCase):
    def test_installed_framework_resolves_against_existing_inventories(self):
        from tools.entropy_framework.reuse import current_catalog
        from tools.lexical_training.curriculum import AXES
        from tools.lexical_training.reasoning_curriculum import DOMAINS, MATRICES
        compiled, _, _, _ = current_catalog(f.ROOT)
        result = f.framework(compiled=compiled, axis_ids={r[0] for r in AXES},
                             matrix_ids={r[0] for r in MATRICES}, domain_ids={r[0] for r in DOMAINS})
        self.assertGreater(len(result["objectives"]), 0)
        for field, inventory, count in (("axis_ids", AXES, 30), ("matrix_ids", MATRICES, 19),
                                         ("domain_ids", DOMAINS, 8)):
            expected = {row[0] for row in inventory}
            self.assertEqual(len(expected), count)
            self.assertEqual({value for row in result["objectives"] for value in row[field]}, expected)
        cards = {row["id"] for row in result["legacy_alignment"]["cards"]}
        self.assertEqual(len(cards), 24)
        self.assertEqual({value for row in result["objectives"] for value in row["legacy_card_ids"]}, cards)
        for field in ("mastery_certified", "neural_training_performed", "runtime_execution_performed"):
            self.assertFalse(result["validation"][field])


if __name__ == "__main__":
    unittest.main()
