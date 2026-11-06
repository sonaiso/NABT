"""Source-attributed learning objectives; not another law or proof catalogue.

Matrices are overlapping views of installed owners. A route covers only the
explicit adapter scope, never the entire Arabic or cognitive objective.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.entropy_framework.reuse import current_catalog

ROOT = Path(__file__).resolve().parents[2]
REVIEW = "evidence/cognitive_curriculum_v1/source_review.json"
ROUTING_POLICY = "nabt.cognitive-evidence-routing.v2"
SHARED_ADAPTERS = ("source_learning", "qualified_inference", "epistemic_ledger", "grounded_passage", "temporal_context")

# id, label, installed owner modules, adapters, open acquisition obligation.
MATRICES = (
    ("temporal_relation", "زمن القول والمرجع والحدث", ("TemporalContext", "DiscourseEvidence"), ("temporal_context",),
     "تفسير القرينة الزمنية مقدم صراحة؛ الفحص لأيام محددة ولا يثبت وقوع الحدث أو السببية"),
    ("mantuq", "المنطوق", ("MantuqMafhum", "Shakhsiyya3Rules"), ("qualified_inference",),
     "اكتساب المطابقة والتضمن وهوية المعنى ونطاق القول من النص"),
    ("mafhum", "مفهوم الخطاب", ("MantuqMafhum", "QualifiedInference"), ("qualified_inference",),
     "اكتساب جسر اللزوم وشروطه؛ وجود علاقة معرفية وحده لا يثبت الدلالة"),
    ("fahwa", "فحوى الخطاب: مفهوم الموافقة في المصدر", ("Shakhsiyya3Rules",), ("qualified_inference",),
     "تحصيل جهة الموافقة وجسر النقل من الاستعمال"),
    ("cognitive_concept", "المفهوم المعرفي", ("Shakhsiyya1Rules", "ThinkingRules", "RuleLearning"), ("source_learning", "epistemic_ledger", "grounded_passage"),
     "فصل التصور والتصديق ونسبة الاعتقاد وتحقيق الواقع"),
    ("lahn", "لحن الخطاب: مفهوم المخالفة في المصدر", ("Shakhsiyya3Rules", "QualifiedInference"), ("qualified_inference",),
     "تحصيل الضرورة والتأهيل وفحص المانع والغالب؛ لا قلب للشرطية"),
    ("generality", "العموم", ("SourceSemantics", "SemanticInference"), ("source_learning",),
     "اكتساب مجال الكم والاستغراق والاستثناء؛ المسار الحالي لقواعد Horn المضبوطة"),
    ("specificity", "الخصوص", ("SourceSemantics", "SemanticInference"), ("source_learning",),
     "التعيين والخصوص النسبي وشاهد التخصيص؛ لا تعميم للأفراد"),
    ("unrestricted", "المطلق", ("SourceSemantics", "QualifiedInference"), (),
     "قانون مصدري لاكتساب الإطلاق وحمله على المقيد في موضوعه؛ ليس forall تلقائيًا"),
    ("restricted", "المقيد", ("SourceSemantics", "QualifiedInference"), (),
     "هوية القيد ومتعلقه ووحدة الحكم والسبب حيث يشترط المصدر؛ لا نقل بين موضوعين"),
    ("cause", "السبب في المجال المحدد", ("QualifiedInference",), ("qualified_inference",),
     "تعيين معنى السبب وموضوعه وشاهد علاقته؛ صلاحية استعمال الدليل بمضمونه ونطاقه لا باسم مجال مصدره"),
    ("condition", "الشرط", ("QualifiedInference",), ("qualified_inference", "source_learning"),
     "تمييز اللازم والكافي والشرط اللغوي والشرط الأصولي مع شواهد التطبيق"),
    ("blocker", "المانع", ("QualifiedInference", "EvidenceLifecycleV1"), ("qualified_inference",),
     "تعيين ما يمنعه؛ عدم العثور على المانع ليس شاهد انتفائه"),
    ("origin", "الأصل في قياس محدد", ("QualifiedInference",), ("qualified_inference",),
     "تمييز أصل القياس عن الأصل المعجمي أو المسلمة أو الافتراض الافتراضي"),
    ("branch", "الفرع", ("QualifiedInference",), ("qualified_inference",),
     "تعيين الحالة الجديدة؛ حكم الفرع نتيجة لا مقدمة تثبت نفسها"),
    ("illah", "العلة الجامعة", ("QualifiedInference",), ("qualified_inference",),
     "شاهد العلة وتحققها بالأصل والفرع وجسر النقل؛ التشابه لا يكفي"),
    ("designation", "التعيين", ("UnitCarrier", "SourceSemantics", "PersonEvidence"), ("source_learning",),
     "هوية الوقوع والمعنى والمرجع؛ تشابه الاسم لا يوحد شخصين"),
    ("discrimination", "التمييز", ("SourceSemantics", "SemanticInference"), ("source_learning",),
     "حفظ اتجاه العلاقة والنفي والنطاق والفرد والنوع والمعنى واللفظ"),
    ("reason_primitives", "أوليات الاستدلال المصرح بها", ("SemanticInference", "ThinkingRules"), ("source_learning",),
     "تحديد المنطق والفرضيات والمجال؛ لا تُستحدث بديهيات فلسفية أو يُحوّل المجهول إلى نفي"),
)

DOMAINS = (
    ("communication", "التواصل والحقيقة اللغوية والعرفية", SHARED_ADAPTERS,
     "شاهد الوضع والاستعمال والمقام وهوية المعنى والمرجع"),
    ("personal_relations", "العلاقات الشخصية", SHARED_ADAPTERS,
     "فصل القول المنسوب والسلوك المشاهد والدافع الخفي؛ لا قراءة للنوايا"),
    ("social_relations", "العلاقات الاجتماعية", SHARED_ADAPTERS,
     "الأشخاص والعلاقات والأفكار المنسوبة والأعراف والمؤسسات والزمن؛ التفسير ليس اعتمادًا معياريًا"),
    ("world_knowledge", "الكون والإنسان والحياة ومعرفة العالم", SHARED_ADAPTERS,
     "مصدر الخبر أو الملاحظة وهوية الشيء ومكانه وزمنه وحدود الثبوت"),
    ("empirical_science", "العلم التجريبي", SHARED_ADAPTERS,
     "المتغيرات والقياس والوحدات والمعايرة وعدم اليقين والتدخل والتكرار؛ لا سببية من التتابع"),
    ("mathematics", "الرياضيات والتفكير الصوري", SHARED_ADAPTERS,
     "المسلمات والأنواع والكم والاشتقاق؛ المسار الموصول هنا استدلال نصي مشروط لا برهان رياضي عام"),
    ("epistemology", "نظرية المعرفة وتكوين الحكم", SHARED_ADAPTERS,
     "فصل التعريف والرأي والفرضية والدليل والتبني؛ تعريف العقل في المصدر ليس برهان وعي للآلة"),
    ("usul", "دلالة الخطاب والقياس في نطاق المصدر", SHARED_ADAPTERS,
     "قواعد المصدر وسلطته ومناط التطبيق؛ لا تتحول النتيجة إلى إذن فعل"),
)

# Shared learning obligations, not new facts or axioms. Owners retain admission.
FOUNDATION = (
    ("existence", "وجود الشيء المعين", ("ThinkingRules", "RationalInquiry", "EpistemicMeasurement"),
     ("referent", "existence_witness", "source", "scope"),
     "الحكم بوجود معين يحتاج شاهده؛ وجود اسم أو تعريف جنس لا يولد فردا"),
    ("designation", "التعيين والتمييز", ("UnitCarrier", "SourceSemantics", "PersonEvidence"),
     ("occurrence", "referent", "comparison_axis", "context"),
     "هوية الرمز وهوية المفهوم وهوية الشيء علاقات تحتاج ربطا؛ التجانس اللفظي لا يكفي"),
    ("kind_nature", "الجنس وحقيقة الشيء", ("SourceSemantics", "Shakhsiyya1Rules", "ThinkingRules"),
     ("kind", "definition", "instance", "membership_witness", "counterevidence"),
     "تحفظ شواهد أفراد الجنس وتصور حقيقته؛ التعريف وحده لا يثبت تحقق المصداق"),
    ("property", "الخواص والصفات والقابليات", ("SourceSemantics", "RuleLearning", "EpistemicMeasurement"),
     ("bearer", "property", "value", "conditions", "witness"),
     "تمييز خاصية الجنس من حالة الفرد ومن قابلية مشروطة؛ لا توريث بلا قاعدة مسندة"),
    ("spatial_relation", "التجاور المكاني", ("SourceSemantics", "EpistemicMeasurement"),
     ("left_referent", "right_referent", "spatial_frame", "relation", "time", "witness"),
     "التجاور علاقة بين معينين في مرجع مكاني؛ مجاورة الرموز في النص لا تثبتها"),
    ("temporal_relation", "التتابع الزماني", ("SourceSemantics", "DiscourseEvidence", "EpistemicMeasurement"),
     ("first_event", "second_event", "time_frame", "order", "witness"),
     "ترتيب الحدثين ومرجع الزمن يحتاجان شاهدا؛ ترتيب الجمل ليس ترتيب وقوع الأحداث"),
    ("change", "التحول في الصفة", ("SourceSemantics", "QualifiedInference", "EpistemicMeasurement"),
     ("bearer_identity", "property", "before_state", "after_state", "temporal_order", "comparison_bridge"),
     "ربط هوية الحامل والصفة والحالتين وترتيبهما؛ فحص السجل لا يستحدث قانون تغير عام"),
    ("causal_relation", "علاقة التأثير بشروطها", ("QualifiedInference", "ThinkingRules", "EpistemicMeasurement"),
     ("cause", "effect", "relation_witness", "conditions", "blockers", "scope"),
     "تستعمل العلاقة السابقة المسندة في المجالات الملائمة؛ التجاور أو التتابع وحده لا يمنح جسر التأثير"),
)

POLICY_MATRICES = {
    "matching": {"mantuq"}, "inclusion": {"mantuq"},
    "requirement": {"mafhum"}, "alert": {"mafhum"}, "allusion": {"mafhum"},
    "agreement": {"mafhum", "fahwa"}, "opposition": {"mafhum", "lahn", "condition"},
    "guarded_cause": {"cause", "condition", "blocker"},
    "analogy": {"origin", "branch", "illah", "condition", "blocker"},
}

# Learning record requirements, not premises silently supplied to any owner.
MATRIX_FIELDS = {
    "temporal_relation": ("source_occurrence", "speech_scope", "speech_time", "reference_time", "event_time", "relation_witness", "remaining_alternatives"),
    "mantuq": ("expression_occurrence", "sense", "part_alignment", "scope"),
    "mafhum": ("mantuq", "necessity_relation", "indication_kind", "application_witness"),
    "fahwa": ("mantuq", "agreement_direction", "transfer_bridge", "application_witness"),
    "cognitive_concept": ("conception", "attributed_belief", "grounding_evidence", "adoption_status"),
    "lahn": ("qualified_contrast", "necessary_relation", "countertext_absence", "usual_case_absence"),
    "generality": ("quantifier", "domain", "scope", "exceptions", "membership_witness"),
    "specificity": ("referent_or_subset", "relative_domain", "specification_evidence"),
    "unrestricted": ("base_description", "discourse_occurrence", "ruling_identity", "cause_identity"),
    "restricted": ("base_description", "qualifier", "attachment", "restriction_transfer_witness"),
    "cause": ("domain", "trigger_description", "ruling", "conditions", "blockers"),
    "condition": ("domain", "condition", "conditioned", "direction", "necessity_witness"),
    "blocker": ("domain", "blocker", "blocked_target", "presence_or_absence_evidence"),
    "origin": ("domain", "origin_case", "origin_ruling", "ruling_source"),
    "branch": ("branch_case", "case_properties", "shared_illah_witness", "counterevidence"),
    "illah": ("domain", "illah_source", "origin_instance", "branch_instance", "transfer_bridge"),
    "designation": ("source_occurrence", "sense_identity", "referent", "time", "place", "scope"),
    "discrimination": ("left", "right", "comparison_axis", "identity_or_difference_witness"),
    "reason_primitives": ("calculus", "types", "declared_premises", "inference_rule", "proof_scope"),
}


def matrix(*, compiled=None):
    if compiled is None:
        compiled, _, _, _ = current_catalog(ROOT)
    modules = {row["module"] for row in compiled["theorems"]}
    rows = []
    for identity, label, owners, adapters, debt in MATRICES:
        names = ["Nabt." + name for name in owners]
        if any(name not in modules for name in names):
            raise ValueError("Unresolved cognitive curriculum owner: " + identity)
        rows.append({"id": identity, "label_ar": label, "owner_modules": names,
                     "runtime_adapters": list(adapters), "open_obligation_ar": debt,
                     "learning_record_fields": list(MATRIX_FIELDS[identity]),
                     "mapping_authority": "RELATED_SCOPE_NOT_WHOLE_MATRIX_PROOF",
                     "learning_complete": False})
    foundation = []
    for identity, label, owners, fields, debt in FOUNDATION:
        names = ["Nabt." + name for name in owners]
        if any(name not in modules for name in names):
            raise ValueError("Unresolved shared knowledge owner: " + identity)
        foundation.append({"id": identity, "label_ar": label, "owner_modules": names,
                           "learning_record_fields": list(fields), "open_obligation_ar": debt,
                           "mapping_authority": "RELATED_SCOPE_NOT_WHOLE_MATRIX_PROOF"})
    raw = (ROOT / REVIEW).read_bytes()
    review = json.loads(raw)
    if review["schema"] != "nabt.cognitive-curriculum-source-review.v1":
        raise ValueError("Unsupported source review")
    return {"schema": "nabt.cognitive-curriculum.v1", "authority": "CURRICULUM_ONLY",
            "routing_policy_id": ROUTING_POLICY,
            "domain_role": "CURRICULUM_CONTEXT_NOT_EVIDENCE_AUTHORITY",
            "shared_foundation": {"authority": "PROJECT_METHOD_AND_LEARNING_OBLIGATIONS",
                "world_reference": "World judgments require a reality referent and applicable evidence.",
                "rows": foundation, "facts_or_axioms_created": False,
                "admission_owner": "Existing source, inference and observation owners retain their exact checks."},
            "matrices": rows, "matrix_count": len(rows),
            "domains": [{"id": i, "label_ar": label, "runtime_adapters": list(adapters),
                         "evidence_contract_ar": debt, "expertise_certified": False}
                        for i, label, adapters, debt in DOMAINS],
            "source_review": {"path": REVIEW, "sha256": hashlib.sha256(raw).hexdigest(),
                              "passages": review["passages"], "scope": review["review_scope"]},
            "methods": {"rational": "subject, information, interpretation, applicable evidence, judgment, revision",
                        "empirical": "observations and intervention under declared measurement assumptions",
                        "formal": "consequence of explicitly declared premises in an installed calculus"},
            "training_protocol": ["SOURCE_AND_INTERPRETATION_SEPARATION", "MINIMAL_CONTRASTS",
                "NO_TARGET_IN_LEARNER_INPUT", "NEW_OCCURRENCE", "COUNTEREXAMPLE",
                "WITHDRAW_SHARED_AND_INDEPENDENT_SUPPORT", "REPLAY_EXPLANATION"],
            "expert_agent_roles": [
                {"role": "source_acquirer", "output": "source bytes, location, provenance; interpretation separately"},
                {"role": "learner", "output": "candidate distinctions and relations; no acceptance authority"},
                {"role": "domain_teacher", "output": "contrast task selected from the observed missing obligation"},
                {"role": "native_checker", "output": "installed owner's scoped receipt"},
                {"role": "independent_evaluator", "output": "held-out acquisition, application, revision and explanation measurements"}],
            "limits": ["No whole-book formalization or domain expertise is certified.",
                       "Fahwa/agreement and lahn/opposition are attributed to this source's terminology.",
                       "Formal, empirical and normative authority do not transfer by a shared label.",
                       "An adapter route is bounded operational reuse, not a semantic coverage claim."]}
