"""Eighteen overlapping RAG views derived from the existing owner registry.

These mappings do not allocate concept IDs or duplicate theorem declarations.
Unimplemented acquisition, audio alignment and free-text bridges stay open in
the owners' debts. A resolved path is not a successful execution.
"""
VIEWS = (
    ("trace", "الأثر والمصدر", ("aligned-acquisition", "sourced-acquisition", "evidence-lifecycle")),
    ("sound", "الصوت والمخارج", ("identity", "word-kinds")),
    ("orthography", "الرسم وUnicode", ("identity", "aligned-acquisition")),
    ("cells", "116 والمقاطع", ("identity", "transition-law", "closure-boundary")),
    ("graded", "الجبر المتدرج", ("progressive-units", "recursive-source", "unit-discovery")),
    ("lexicon", "المعجم والوضع", ("lexical-denotation", "lexical-completion", "lexical-graph")),
    ("morphology", "الصرف", ("morphology", "derivation-patterns", "productive-forms")),
    ("syntax", "النحو والأدوات", ("construction", "inflection", "arabic-governors", "person-reference")),
    ("genera", "الأجناس والأفراد", ("lexical-denotation", "properties-obligations", "meaning-preservation")),
    ("quantity", "العدد والزمان والمكان", ("numeric-program", "discourse", "epistemic-measurement")),
    ("indications", "المطابقة والتضمن والالتزام", ("lexical-denotation", "mantuq-mafhum")),
    ("usage", "الحقيقة والمجاز والعرف", ("linguistic-truth", "meaning-preservation")),
    ("understanding", "المنطوق وطرق الاستفادة", ("mantuq-mafhum", "licensed-inference")),
    ("restriction", "العموم والتقييد", ("classical-source-rules", "mantuq-mafhum", "rule-learning")),
    ("speech_act", "الخبر والإنشاء", ("discourse", "construction", "epistemic-measurement")),
    ("inference", "السبب والشرط والقياس", ("signed-inference", "mantuq-mafhum", "rational-inquiry")),
    ("world", "الواقع والمعلومات والحكم", ("epistemic-measurement", "rational-inquiry", "properties-obligations")),
    ("revision", "التعلم والمراجعة والتفسير", ("rule-learning", "evidence-lifecycle", "meaning-preservation")),
)


def inventory():
    from tools.entropy_framework.reuse import build_reuse_report
    existing = build_reuse_report()
    owners = {r["id"]: r for r in existing["families"]}
    return {"schema": "nabt.shared-rag-views.v1", "new_concept_registry": False,
            "runtime_execution_performed": False,
            "views": [{"id": name, "title_ar": title,
                       "owners": [{key: owners[f][key] for key in
                                   ("id", "formal_modules", "runtime_paths", "native_targets",
                                    "test_paths", "scope", "open_debts")} for f in families]}
                      for name,title,families in VIEWS]}
