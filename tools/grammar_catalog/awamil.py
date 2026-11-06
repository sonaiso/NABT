"""Source-qualified governors and relation cards over the existing RAG owner.

Numbered identities, case-table arithmetic and occurrence licensing are three
different contracts. Search (including learned ranking) changes none of them.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256

from nabt.governors import installed_table
from tools.mantuq_mafhum import load_awamil_inventory
from .catalog import build_catalog, catalog_sha256, ROOT
from .operations import digest, exact_terms
from .retrieval import SearchIndex, RetrievalError, tokens, _limit

RECIPE = "nabt.awamil-source-cards.v1"
GROUPS = {
    1: "حروف الجر", 2: "الحروف المشبهة بالفعل إن وأخواتها",
    3: "ما ولا المشبهتان بليس", 4: "الحروف الناصبة اسما واحدا",
    5: "حروف نصب المضارع", 6: "حروف جزم المضارع", 7: "أسماء الشرط الجازمة",
    8: "أسماء التمييز", 9: "أسماء الأفعال", 10: "الأفعال الناقصة كان وأخواتها",
    11: "أفعال المقاربة", 12: "أفعال المدح والذم", 13: "أفعال القلوب",
    14: "العوامل القياسية", 15: "العوامل المعنوية",
}

# Pedagogical views of EXISTING owner rules. These are not additional laws.
# Head is the predicative anchor; an operator and an attachment host are separate.
RELATIONS = (
    ("nominal", "الجملة الاسمية المبتدأ والخبر", "predicative", "المبتدأ", "الخبر", "الخبر",
     "nominal_predication", "nominal_predication"),
    ("verbal", "الجملة الفعلية الفعل والفاعل ونائب الفاعل", "predicative", "الفاعل أو نائب الفاعل", "الفعل", "الفعل",
     "active_subject", "verbal_predication"),
    ("kana", "إسناد كان وأخواتها", "predicative", "اسم كان", "خبر كان", "الخبر مع حفظ الناسخ",
     "kana_sisters", "kana_construction"),
    ("inna", "إسناد إن وأخواتها", "predicative", "اسم إن", "خبر إن", "الخبر مع حفظ الناسخ",
     "inna_sisters", "inna_construction"),
    ("zanna", "تضمين الإسناد تحت ظن وأفعال القلوب", "embedding", "المفعول الأول", "المفعول الثاني", "المحمول داخل نطاق الظن",
     "zanna_sisters", "zanna_construction"),
    ("relative", "تضمين جملة الصلة والعائد", "embedding", "مرجع العائد داخل الصلة", "محمول الصلة", "رأس داخل نطاق الصلة",
     "relative_return", "relative_clause"),
    ("pp", "شبه الجملة الجار والمجرور وتعلق الظرف", "restrictive", "يحدده الإسناد الحاضن", "محل شبه الجملة يحتاج شاهدا", "متعلق بشاهد ولا يقدر آليا",
     "prepositional_attachment", "prepositional_attachment"),
    ("adjective", "التقييد بالنعت وحفظ المطابقة", "restrictive", "المنعوت", "صفة مقيدة لا خبر مستقل", "رأس المركب الاسمي",
     "naat_agreement", "naat"),
    ("idafa", "التقييد بالإضافة والمضاف إليه", "restrictive", "المضاف", "المضاف إليه ليس خبرا", "المضاف",
     "idafa_chain", "idafa"),
    ("hal", "التقييد بالحال وصاحب الحال", "restrictive", "صاحب الحال", "الحال في نطاق الحدث", "رأس الحدث",
     "hal_attachment", "hal"),
    ("tamyiz", "التقييد بالتمييز ورفع الإبهام", "restrictive", "المميز", "التمييز", "رأس النسبة أو المقدار",
     "tamyiz_measure", "tamyiz"),
    ("kada", "تضمين الفعل المضارع في خبر المقاربة", "embedding", "اسم فعل المقاربة", "الجملة الفعلية في الخبر", "رأس الجملة المضمنة مع حفظ المقاربة",
     "kada_complement", "kada_construction"),
)


def build_awamil_catalog():
    inventory = load_awamil_inventory()
    table = installed_table()
    grammar = build_catalog()
    rules = {r["rule_key"]: r for r in grammar["rules"]}
    passages = {p["passage_id"]: p for p in grammar["passages"]}
    cards = []
    for row in inventory["rows"]:
        cards.append({"id": f"jurjani:{row['id']:03d}", "collection": "jurjani",
            "label": row["name"], "family": row["family"], "group": row["group"],
            "description": GROUPS[row["group"]], "source": {
                "path": "evidence/mantuq_mafhum/sources/awamil_inventory.tsv",
                "sha256": inventory["inventory_sha256"], "row": row["id"], "scan_page": row["page"],
                "scan_sha256": inventory["source_scan_sha256"]},
            "owner": "tools.mantuq_mafhum.audit_inventory", "formal_module": "Nabt.AwamilInventory",
            "authority": "ENUMERATION_ONLY", "application_certified": False})
    for row in table.entries:
        cls = table.classes[row.class_code]
        cards.append({"id": f"nabt:{row.row_id:03d}", "collection": "nabt", "label": row.label,
            "family": str(row.class_code), "description": cls.name,
            "class_code": row.class_code, "implicit": row.implicit,
            "alternatives": [[list(pair) for pair in alt] for alt in cls.alternatives],
            "links": [list(pair) for pair in cls.links], "source": {
                "path": "src/nabt/data/governors.json",
                "sha256": sha256((ROOT / "src/nabt/data/governors.json").read_bytes()).hexdigest(),
                "row": row.row_id},
            "owner": "nabt.governors.check_assignment", "formal_module": "Nabt.Governors",
            "authority": "CONDITIONAL_CASE_TABLE", "application_certified": False})
    for key, label, relation, subject, predicate, head, rule, frame in RELATIONS:
        registry = ("nabt.discourse-grammar-sources.v2" if key in {"nominal", "verbal", "relative"}
                    else "nabt.construction-grammar-sources.v4")
        source = rules[registry + "::" + rule]
        cards.append({"id": "relation:" + key, "collection": "relations", "label": label,
            "description": " ".join([subject, predicate, head]), "family": relation,
            "musnad_ilayh": subject, "musnad": predicate, "predication_head": head,
            "owner_frame": frame, "source_rule": source["rule_key"],
            "source_passages": [deepcopy(passages[p]) for p in source["source_passage_ids"]],
            "owner": "nabt.discourse.read_discourse", "formal_module": "Nabt.DiscourseEvidence",
            "authority": "PEDAGOGICAL_OWNER_VIEW", "application_certified": False,
            "conditions": ["SOURCE_BOUND_READING", "CORRECT_ROLE_AND_SCOPE", "OWNER_OBLIGATIONS_DISCHARGED"],
            "counterexample": "سحب شاهد الدور أو تبديل الحركة أو نقل المحمول من الصلة أو الظن إلى دعوى مستقلة"})
    # Candidate correspondence only: neither stripped spelling nor identical
    # serial number establishes the SAME use/class. Expose unmatched rows.
    crosswalk = []
    for card in cards[:100]:
        lexical = [r["id"] for r in cards[100:200] if tokens(r["label"]) == tokens(card["label"])]
        crosswalk.append({"source_id": card["id"], "candidate_ids": lexical,
            "status": "SPELLING_CANDIDATES_REQUIRE_USE_ALIGNMENT" if lexical else "NO_SPELLING_ALIGNMENT",
            "equivalence_established": False})
    return {"schema": RECIPE, "authority": "RETRIEVAL_ONLY", "cards": cards,
        "counts": {"jurjani": 100, "nabt": 100, "relations": len(RELATIONS)},
        "grammar_catalog_sha256": catalog_sha256(grammar), "crosswalk": crosswalk,
        "partition": {"samai": 91, "qiyasi": 7, "manawi": 2},
        "embedding_definition": "STRUCTURAL_EMBEDDING_NOT_DALALA_TADAMMUN",
        "full_rule_semantics_complete": False, "native_inventory_checked": False}


def document(card):
    return card["label"] + " : " + card["description"]


class AwamilIndex(SearchIndex):
    """Shared BM25 plus exact spelling stream; raw marks stay in the receipt."""
    def __init__(self):
        self._catalog = build_awamil_catalog()
        self.catalog_sha256 = digest(self._catalog)
        self._docs = {}
        for card in self._catalog["cards"]:
            self._add("item", card["id"], document(card), card)
        self._tf = {k: Counter(tokens(v["search_text"])) for k, v in self._docs.items()}

    def catalog(self):
        return deepcopy(self._catalog)

    def search(self, query, limit=10, *, collection=None, learned=None):
        _limit(limit)
        if collection not in (None, "jurjani", "nabt", "relations"):
            raise RetrievalError("Unknown awamil collection")
        # Revalidate on a long-lived index; no stale source scores can execute.
        if digest(build_awamil_catalog()) != self.catalog_sha256:
            raise RetrievalError("STALE_AWAMIL_CATALOG")
        found = super().search(query, len(self._docs))
        keys = [k for k, v in self._docs.items() if collection is None or v["record"]["collection"] == collection]
        terms = {o["surface"] for o in exact_terms(query)}
        exact = [k for k in keys if self._docs[k]["record"]["label"] == query or
                 self._docs[k]["record"]["label"] in terms]
        lexical = [r["id"] for r in found["candidates"] if ("item", r["id"]) in keys]
        streams = [lexical, [k[1] for k in exact]]
        model = None
        admission = None
        if learned is not None:
            # A loaded learner binds its exact card identities and source digest.
            if learned.catalog_sha256 != self.catalog_sha256:
                raise RetrievalError("MODEL_CATALOG_MISMATCH")
            scores = learned.scores(query)
            if learned.ranking_admitted:
                streams.append(sorted((k[1] for k in keys), key=lambda k: (-scores[k], k)))
            model = learned.model_sha256
            admission = learned.ranking_admitted
        ranking = Counter()
        for stream in streams:
            for rank, identifier in enumerate(stream, 1):
                ranking[identifier] += 1 / (60 + rank)
        ordered = sorted(ranking, key=lambda k: (-ranking[k], k))
        return {"schema": "nabt.awamil-rag.retrieval.v1", "raw_query": query,
            "query_occurrences": exact_terms(query), "catalog_sha256": self.catalog_sha256,
            "model_sha256": model, "learned_ranking_admitted": admission,
            "collection": collection, "authority": "RETRIEVAL_ONLY",
            "candidates": [{"id": k, "rank": i + 1, "score": ranking[k],
                            "record": self.rehydrate("item", k)} for i, k in enumerate(ordered[:limit])],
            "status": "PROPOSALS" if ordered else "NO_CANDIDATES",
            "all_same_spelling_ids": [k[1] for k in exact], "application_certified": False}


def answer(query, *, limit=5, collection=None, learned=None):
    """Generate a bounded Arabic explanation from rehydrated source cards."""
    found = AwamilIndex().search(query, limit, collection=collection, learned=learned)
    lines = []
    role_names = {0: "الاسم أو المفعول الأول", 1: "الخبر أو المفعول الثاني", 2: "المضارع",
                  6: "المجرور", 9: "المعطوف عليه", 10: "المعطوف", 11: "فعل الشرط",
                  12: "جواب الشرط", 13: "المنادى"}
    mark_names = ("نصب", "رفع", "جر", "جزم")
    for candidate in found["candidates"]:
        c = candidate["record"]
        line = f"[{c['id']}] {c['label']}: {c['description']}"
        if c["collection"] == "nabt":
            work = ["، ".join(f"{role_names[role]}: {mark_names[mark]}" for role, mark in alt)
                    or "لا قيد إعراب مباشر في هذا البديل" for alt in c["alternatives"]]
            line += ". العمل المشروط: " + " / ".join(work)
            for left, right in c["links"]:
                line += f"؛ تطابق علامة {role_names[left]} و{role_names[right]}"
        elif c["collection"] == "jurjani":
            line += f". موضع الجرد: صفحة {c['source']['scan_page']}؛ جرد الهوية لا يستوفي شروط كل استعمال."
        else:
            line += f". المسند إليه: {c['musnad_ilayh']}؛ المسند: {c['musnad']}؛ الرأس: {c['predication_head']}."
        lines.append(line)
    return {"schema": "nabt.awamil-rag.answer.v1", "retrieval": found,
        "answer_ar": "\n".join(lines) if lines else "لم أجد بطاقة مطابقة؛ يلزم شاهد أو تحديد للاستعمال.",
        "citations": [c["id"] for c in found["candidates"]], "application_certified": False,
        "remaining": ["تطبيق العامل يحتاج شاهد وقوعه وشروطه وموانعه وفحص صاحب القاعدة"]}
