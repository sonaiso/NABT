"""Combine two independently pinned source reviews without promoting authority."""
from tools.mantuq_sources import ROOT, build_inventory as build_base, build_supplement


def build_inventory(root=ROOT):
    base, supplement = build_base(root), build_supplement(root)
    sources = base["sources"] + supplement["sources"]
    passages = base["passages"] + supplement["passages"]
    if len({s["source_id"] for s in sources}) != len(sources):
        raise ValueError("Duplicate source identity in combined inventory")
    pids = {p["passage_id"] for p in passages}
    if len(pids) != len(passages):
        raise ValueError("Duplicate passage identity in combined inventory")
    rules = {r["rule_id"]: r for r in base["rules"]}
    for rule in rules.values():
        rule["reviewed_context_passage_ids"] = []
    for association in supplement["policy_associations"]:
        if (association["rule_id"] not in rules or
                any(pid not in pids for pid in association["source_passage_ids"]) or
                association["linguistic_license_established"] is not False or
                association["executable_rule_changed"] is not False):
            raise ValueError("Invalid supplemental context association")
        rules[association["rule_id"]]["reviewed_context_passage_ids"].extend(association["source_passage_ids"])
    for identity in ("guarded_cause", "analogy"):
        rule = rules[identity]
        rule["base_review_claim"] = rule["claim"]
        rule["claim"] = (
            "قالب صوري بمقدمات وجسر معلنين. أضيفت مقاطع من الكتاب الأصلي للسبب والشرط والمانع والقياس؛ "
            "تبقى نسبة هذا التطبيق إلى النص وتحصيل مقدماته وترجمة الفصل كاملًا غير مثبتة."
        )
    return {**base, "schema": "nabt.mantuq-inference-inventory.v2",
            "sources": sources, "passages": passages, "rules": list(rules.values()),
            "supplement_review_sha256": supplement["review_sha256"],
            "supplement_policy_associations": supplement["policy_associations"],
            "supplement_original_comparison": supplement["original_comparison"],
            "supplement_chapter_audit": supplement["chapter_audit"],
            "replay": {"source_files": len(sources), "passages": len(passages),
                       "source_bytes_checked": sum(s["bytes"] for s in sources),
                       "retained_sources_checked": True, "original_books_rechecked": False,
                       "theorem_references_compiled_here": False},
            "supplement_scope": supplement["scope"]}
