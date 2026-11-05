"""Cross-matrix learning targets referencing the existing source inventories.

An axis is a required capability, not a new grammar rule or a trained head.
All 120 existing research records remain visible with their original authority.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.arabic_training import madlul_matrix, sign_curriculum
from tools.entropy_framework.reuse import current_catalog
from tools.meaning_preservation_inventory import research_inventory
from .reasoning_curriculum import matrix as reasoning_matrix, MATRICES, DOMAINS
from .learning_framework import framework as learning_framework

ROOT = Path(__file__).resolve().parents[2]

# Existing research IDs, not copied linguistic definitions or new theorem IDs.
AXES = (
    ("word_kind", "الاسم والفعل والحرف", ["M001"], ["Words", "QatrRules", "SibawayhiRules"]),
    ("morphological_derivation", "الجامد والمشتق الصرفي", ["M002"], ["Morphology", "Derivation"]),
    ("genus_quality", "الجنس والصفة وحامل الصفة", ["M003", "M004", "D011"], ["Morphology", "SourceSemantics"]),
    ("proper_name", "العلم الشخصي والجنسي والمنقول", ["M005", "M006", "M007"], ["NominalEvidence", "LinguisticTruth"]),
    ("definiteness", "المعرفة والنكرة", ["M008", "P28_definiteness"], ["NominalEvidence", "DiscourseEvidence"]),
    ("reference", "الإحالة والضمير والإشارة والموصول", ["M009", "P25_pronouns", "P26_deixis", "P27_relatives"], ["PersonEvidence", "DiscourseEvidence", "SourceSemantics"]),
    ("declension", "المبني والمعرب", ["M010", "P30_original_built", "P31_contextual_built", "P32_inflection_roles"], ["Words", "QatrRules", "InflectionEvidence"]),
    ("diptote", "الممنوع من الصرف وشروط تغير علامته", ["M010"], ["Words", "NominalEvidence", "InflectionEvidence"]),
    ("root_pattern", "الأصول والأوزان والزيادة", ["M011", "M012", "M013"], ["NominalPatterns", "ProductiveForms", "Derivation"]),
    ("gender", "التذكير والتأنيث وعلامتهما", ["G001", "G002", "G003"], ["NominalEvidence", "PersonEvidence"]),
    ("number", "المفرد والمثنى والجمع وأنواعه", ["N001", "N002", "N003", "N004", "N005", "N006", "N007", "N008"], ["NominalEvidence", "InflectionEvidence"]),
    ("counting", "العدد والعد والمعدود والترتيب", ["N009", "N010", "N011", "P29_quantifier_scope"], ["NominalEvidence", "ConstructionEvidence"]),
    ("masdar", "المصدر وأنواعه واسم المصدر", ["D001", "D002", "D003", "D004", "D005", "D006", "D007"], ["Morphology", "NominalPatterns", "ProductiveClauseV1"]),
    ("derived_nouns", "الفاعل والمفعول والمبالغة والتفضيل والآلة والزمان والمكان", ["D008", "D009", "D010", "D012", "D013", "D014"], ["NominalPatterns", "ProductiveForms", "ProductiveClauseV1"]),
    ("nisba_diminutive", "النسب والتصغير", ["D015", "D016", "P23_nisba"], ["NominalPatterns", "ClassicalWeak"]),
    ("weak_transform", "الإعلال والإبدال والإدغام", ["D017"], ["ClassicalWeak", "ClassicalGemination", "RecursiveSourceBridge"]),
    ("tense_form", "دلالة الزمن بالهيئة والماضي والمضارع والأمر", ["V001", "P33_time_place"], ["Words", "QatrRules", "ImperativeParadigm"]),
    ("future", "المستقبل وقرائن تخصيص المضارع", ["V001", "P17_lan"], ["QatrReading", "DiscourseEvidence"]),
    ("voice", "المعلوم والمجهول", ["V005"], ["Derivation", "InflectionEvidence", "MeaningPreservation"]),
    ("valency", "اللزوم والتعدي والأطراف", ["V002"], ["ConstructionEvidence", "ProductiveClauseV1"]),
    ("verb_augmentation", "الفعل المجرد والمزيد وهيئات التحويل", ["V003", "V004", "V006"], ["Derivation", "ProductiveForms", "ImperativeParadigm"]),
    ("nawasikh", "النواسخ وعملها وأثرها في الإسناد", ["P01_predication", "P18_laysa", "P20_emphasis"], ["Governors", "ArabicInnaFragment", "AwamilRules", "DiscourseEvidence"]),
    ("semantic_parts", "المفرد الدلالي والمزجي والإضافي والإسنادي", ["P01_predication", "P22_idafa", "M007"], ["SibawayhiRules", "RecursiveSourceBridge", "SourceSemantics"]),
    ("scope_composition", "النفي والشرط والربط والنطاق بعد التركيب", ["P02_waw", "P05_aw", "P10_in_conditional", "P15_negation_vs_prohibition", "P24_ellipsis"], ["DiscourseEvidence", "MantuqMafhum", "MeaningPreservation"]),
    ("mention_use", "القول والقول المنقول ومستوى الإشارة", ["P34_mention_quote"], ["LinguisticTruth", "SourceSemantics"]),
    ("dictionary_designation", "الوضع من المعاجم وهوية المعنى", [], ["LisanRules", "MaqayisDenotation", "LexicalDenotation", "LinguisticTruth"]),
    ("definition_parts", "المطابقة والتضمن ومكونات التعريف", [], ["LexicalDenotation", "LisanRules", "MaqayisDenotation"]),
    ("mental_condition", "الالتزام: اللزوم الذهني شرط وليس بموجب", [], ["LexicalDenotation", "LisanRules", "LinguisticTruth", "QualifiedInference"]),
    ("grounding", "فهم المعنى وتحقيقه في الواقع", ["X001"], ["Shakhsiyya1Rules", "SourceSemantics"]),
    ("revision", "المثال المضاد وسحب الشاهد وحفظ الدعم المستقل", [], ["RuleLearning", "EvidenceLifecycleV1"]),
)


def curriculum():
    research = research_inventory()
    signs, denotata = sign_curriculum.matrix(), madlul_matrix.matrix()
    compiled, _, _, _ = current_catalog(ROOT)
    modules = {r["module"] for r in compiled["theorems"]}
    records = {r["local_id"]: r for r in research["records"]}
    axes = []
    for key, label, refs, owners in AXES:
        if any(ref not in records for ref in refs):
            raise ValueError("unresolved research target: " + key)
        if any("Nabt." + owner not in modules for owner in owners):
            raise ValueError("unresolved formal owner: " + key)
        axes.append({"id": key, "label_ar": label,
                     "research_record_ids": [records[r]["id"] for r in refs],
                     "owner_modules": ["Nabt." + owner for owner in owners],
                     "mapping_authority": "RELATED_SCOPE_NOT_WHOLE_AXIS_PROOF",
                     "complete_learning_certified": False,
                     "required_measurements": ["SOURCE_BOUND_ACQUISITION", "NEW_OCCURRENCE_APPLICATION",
                                               "COMPOSITION_PRESERVATION", "EVIDENCE_REVISION"]})
    return {"schema": "nabt.cross-matrix-curriculum.v1", "authority": "CURRICULUM_AND_SOURCE_MAP",
            "sign_matrix": signs, "denotatum_matrix": denotata, "research_inventory": research,
            "requested_axes": axes, "requested_axis_count": len(axes),
            "reasoning_curriculum": reasoning_matrix(compiled=compiled),
            "learning_framework": learning_framework(
                compiled=compiled, axis_ids=[row[0] for row in AXES],
                matrix_ids=[row[0] for row in MATRICES], domain_ids=[row[0] for row in DOMAINS]),
            "current_training": {"input": "source quotation, no supplied root or target",
                "targets": ["installed sense identity", "definition component identity"],
                "trained_axes": ["dictionary_designation", "definition_parts"],
                "status": "BOUNDED_PROPOSAL_TRAINING_NOT_AXIS_COMPLETION"},
            "preexisting_morphology_model": {
                "path": "evidence/source_morphology_training/run_02",
                "targets": ["tag", "declension", "case_mood", "affixes"],
                "executed_by_this_command": False},
            "next_matrix_gate": {"passed": False,
                "requirements": ["EXACT_SIGN_READING_TO_LEXICAL_SENSE_ALIGNMENT",
                    "SOURCE_BOUND_USAGE_AND_CONVENTION", "SEMANTIC_PART_ALIGNMENT",
                    "HELD_OUT_AXIS_DENOMINATORS", "COUNTEREXAMPLE_AND_WITHDRAWAL_REPLAY"],
                "cannot_substitute": ["number of rows", "training loss", "highest neural score"]}}


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path)
    p.add_argument("--framework-only", action="store_true",
                   help="Export the validated learning framework without the other matrix views")
    args = p.parse_args()
    result = curriculum()
    if args.framework_only:
        result = result["learning_framework"]
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
