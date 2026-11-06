"""Source-backed i'rab views over existing readers; no additional grammar law."""
from collections import Counter
from copy import deepcopy

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse_reader import read_discourse
from nabt.discourse_laws import CAUSAL_BITS, causal_allowed
from nabt.inflection_reader import read_inflection
from tools.evidence_lifecycle_v1 import _encoded
from .catalog import build_catalog, catalog_sha256
from .operations import digest, exact_terms
from .retrieval import SearchIndex, RetrievalError, tokens, _limit, _text

MAX_REQUEST = 2 * 1048576
MAX_REPORT = 8 * 1048576
CASE_NAMES = {"raf": "رفع", "nasb": "نصب", "jarr": "جر", "jazm": "جزم"}
ROLE_NAMES = {
    "nominal_subject": "مبتدأ", "nominal_predicate": "خبر",
    "active_subject": "فاعل", "passive_subject": "نائب فاعل", "direct_object": "مفعول به",
    "inna_subject": "اسم إن", "inna_predicate": "خبر إن",
    "kana_subject": "اسم كان", "kana_predicate": "خبر كان",
    "zanna_subject": "فاعل ظن", "zanna_object1": "المفعول الأول لظن",
    "zanna_object2": "المفعول الثاني لظن", "kada_subject": "اسم فعل المقاربة",
    "kada_predicate": "خبر فعل المقاربة",
    "preposition_object": "مجرور بحرف الجر", "idafa_complement": "مضاف إليه",
    "imperfect_indicative": "مضارع مرفوع", "imperfect_subjunctive": "مضارع منصوب",
    "imperfect_jussive": "مضارع مجزوم", "hal": "حال", "tamyiz": "تمييز",
    "time_adverb": "ظرف زمان", "place_adverb": "ظرف مكان", "naat": "نعت",
    "badal": "بدل", "tawkeed": "توكيد",
}
SIGN_NAMES = {"damma": "الضمة", "fatha": "الفتحة", "kasra": "الكسرة", "sukun": "السكون",
              "waw": "الواو", "alif": "الألف", "ya": "الياء", "nun_retained": "ثبوت النون",
              "nun_deleted": "حذف النون", "weak_deleted": "حذف حرف العلة"}
MODES = {"overt": "ظاهرة", "estimated": "مقدرة", "deletion": "حذف"}

# Navigation categories, not a second rule registry. Every rule reference is
# namespaced; all source quotations come from the existing verified catalogue.
W = "nabt.word-source-policy.v1::"
D = "nabt.discourse-grammar-sources.v2::"
C = "nabt.construction-grammar-sources.v4::"
I = "nabt.inflection-grammar-sources.v1::"
TOPICS = (
    ("raf", "المرفوعات الرفع", "الحالة والعلامة غير الدور: المبتدأ والخبر والفاعل ونائبه والمضارع المرفوع.",
     (I+"inflection_signs", D+"nominal_predication", D+"active_subject", D+"imperfect_indicative")),
    ("nasb", "المنصوبات النصب", "تمييز نصب الأسماء ونصب المضارع؛ لا تستنتج المفعولية من النصب وحده.",
     (I+"inflection_signs", I+"subjunctive_lan", C+"inna_sisters", C+"kana_sisters", C+"hal_attachment", C+"tamyiz_measure")),
    ("jarr", "المجرورات الجر", "حرف الجر والإضافة والتبعية؛ الحالة والعلامة والمحل حقول مستقلة.",
     (W+"min_preposition", D+"idafa", C+"naat_agreement")),
    ("jazm", "المجزومات الجزم", "جزم المضارع؛ السكون وحذف النون وحرف العلة والمبني في محل جزم بحسب مقدماته.",
     (W+"lam_activation", I+"inflection_signs", D+"five_verb_nun")),
    ("subject", "الفاعلية الفاعل", "دور نحوي يحتاج إسنادًا وشاهدًا؛ لا يثبت وحده إحداث السبب في الواقع.", (D+"active_subject",)),
    ("passive_subject", "النيابة عن الفاعل نائب الفاعل", "يحفظ البناء للمجهول؛ لا يعاد تصنيف نائب الفاعل فاعلًا أو مفعولًا منصوبًا.", (D+"active_subject",)),
    ("object", "المفعولية المفعول به", "الدور متعلق بالفعل وقراءته؛ لا يكفي وجود النصب لترخيص المفعول به.", (D+"active_subject", C+"zanna_sisters")),
    ("predication", "الإسناد المبتدأ الخبر الناسخ", "المسند والمسند إليه والعامل محفوظة بأدوارها ومقدماتها.", (D+"nominal_predication", C+"inna_sisters", C+"kana_sisters")),
    ("idafa", "الإضافة المضاف المضاف إليه", "تعلق إضافي؛ جر الطرف الثاني لا يثبت خبرًا مستقلًا.", (C+"idafa_chain",)),
    ("dependency", "التبعية النعت البدل التوكيد", "توريث الحالة يحتاج تعلقًا مرخصًا؛ المطابقة وحدها لا تثبت العلاقة.", (C+"naat_agreement", C+"badal_identity", C+"tawkeed_reference")),
    ("hal", "الحالية الحال صاحب الحال", "يربط الحال بصاحبه ونطاق الحدث وفق القارئ الحالي.", (C+"hal_attachment",)),
    ("tamyiz", "التمييز المميز", "رفع الإبهام في المقدار أو النسبة وفق الشاهد والنطاق المحددين.", (C+"tamyiz_measure", C+"tamyiz_nisba")),
    ("adverb", "الظرفية الزمان المكان", "يحفظ الظرف ومتعلقه؛ المجاورة الكتابية لا تثبت التعلق.", (C+"temporal_spatial_attachment", D+"place_time_complements")),
    ("cause", "السببية السبب التعليل", "الشاهد المنصب هنا لفاء السببية وشروطها النحوية؛ تعيين سبب واقعي أو علة أصولية أو مجاز يحتاج شاهدًا مستقلًا.", (D+"cause",)),
    ("effect", "المسببية المسبب النتيجة", "منظور الطرف الناتج للعلاقة المقصودة؛ لا يستنتج السبب من النتيجة. تفسير المجاز المرسل يحتاج شاهدًا مستقلًا.", (D+"cause",)),
)
DOMAINS = tuple(t[0] for t in TOPICS)
ROLE_DOMAINS = {
    "active_subject": "subject", "passive_subject": "passive_subject", "direct_object": "object",
    "idafa_complement": "idafa", "hal": "hal", "tamyiz": "tamyiz",
    "time_adverb": "adverb", "place_adverb": "adverb", "naat": "dependency",
    "badal": "dependency", "tawkeed": "dependency", "nominal_subject": "predication",
    "nominal_predicate": "predication", "inna_subject": "predication", "inna_predicate": "predication",
    "kana_subject": "predication", "kana_predicate": "predication",
    "zanna_subject": "subject", "zanna_object1": "object", "zanna_object2": "object",
    "kada_subject": "predication", "kada_predicate": "predication",
}


def catalog():
    grammar = build_catalog()
    rules = {r["rule_key"]: r for r in grammar["rules"]}
    passages = {p["passage_id"]: p for p in grammar["passages"]}
    cards = []
    for domain, label, description, keys in TOPICS:
        selected = [rules[k] for k in keys]
        ids = sorted({p for r in selected for p in r["source_passage_ids"]})
        cards.append({"id": "irab:"+domain, "domain": domain, "label": label,
            "description": description, "rule_keys": list(keys), "rules": selected,
            "sources": [passages[p] for p in ids], "authority": "AUTHORED_RETRIEVAL_VIEW",
            "application_certified": False, "full_domain_coverage": False})
    return {"schema": "nabt.irab-catalog.v1", "authority": "RETRIEVAL_ONLY",
            "grammar_catalog_sha256": catalog_sha256(grammar), "cards": cards,
            "case_domains": list(CASE_NAMES), "relation_domains": list(DOMAINS[4:])}


class IrabIndex(SearchIndex):
    def __init__(self, domain=None):
        if domain is not None and (type(domain) is not str or domain not in DOMAINS):
            raise RetrievalError("Unknown irab domain")
        self.domain = domain
        self._catalog = catalog()
        self.catalog_sha256 = digest(self._catalog)
        self._docs = {}
        for card in self._catalog["cards"]:
            if domain is None or card["domain"] == domain:
                body = " ".join(s["raw_text"] for s in card["sources"])
                self._add("item", card["id"], card["label"]+" "+card["description"]+" "+body, card)
        self._tf = {k: Counter(tokens(v["search_text"])) for k, v in self._docs.items()}

    def search(self, query, limit=5):
        if digest(catalog()) != self.catalog_sha256:
            raise RetrievalError("STALE_IRAB_CATALOG")
        found = super().search(query, limit=limit)
        found.update(raw_query=query, query_occurrences=exact_terms(query), domain=self.domain)
        return found


def answer(query, *, domain=None, limit=5):
    found = IrabIndex(domain).search(query, limit)
    lines = [f"[{r['id']}] {r['record']['label']}: {r['record']['description']}"
             for r in found["candidates"]]
    return {"schema": "nabt.irab-answer.v1", "retrieval": found,
        "answer_ar": "\n".join(lines) or "لم أجد بابًا مطابقًا؛ يلزم تحديد السؤال أو إضافة شاهد.",
        "citations": [r["id"] for r in found["candidates"]], "application_certified": False}


def _request(request):
    if type(request) is not dict or "text" not in request or set(request)-{
            "text", "lexical_text", "context", "query", "domain", "limit"}:
        raise ValueError("Supply text and optional lexical_text, context, query, domain, limit")
    _encoded(request, MAX_REQUEST, floats=False)
    text = _text(request["text"], "text", maximum=32768)
    if not text.strip():
        raise ValueError("Expected nonempty text")
    lexical = request.get("lexical_text")
    if lexical is not None:
        _text(lexical, "lexical_text", maximum=1048576)
    context = request.get("context")
    if context is not None and type(context) is not dict:
        raise ValueError("context must be an object")
    _encoded(context, 262144, floats=False)
    _limit(request.get("limit", 5))
    return text, lexical, context


def _row(owner, frame_id, assignment, *, licensed, supports):
    actual_role = assignment.get("actual_role") if licensed else None
    actual_case = assignment.get("inflected_case") if licensed else None
    local_case = assignment.get("local_case") if licensed else None
    domains = []
    if actual_case or local_case:
        domains.append(actual_case or local_case)
    if actual_role in ROLE_DOMAINS:
        domains.append(ROLE_DOMAINS[actual_role])
    row = {"owner": owner, "frame_id": frame_id, "reading_id": assignment["reading_id"],
           "surface": assignment["surface"], "span": deepcopy(assignment["span"]),
           "candidate_role": assignment.get("role"), "actual_role": actual_role,
           "inflected_case": actual_case, "local_case": local_case,
           "licensed": licensed, "domains": domains,
           "assignment": deepcopy(assignment), "supports": deepcopy(supports)}
    row["row_id"] = digest(row)
    return row


def _explain(rows):
    lines = []
    for row in rows:
        role = ROLE_NAMES.get(row["candidate_role"], row["candidate_role"])
        if not row["licensed"]:
            phrase = f"{row['surface']}: مرشح {role}؛ لم تكتمل شهادة هذا التحليل."
        else:
            case = row["inflected_case"] or row["local_case"]
            state = CASE_NAMES.get(case, "الحالة غير معينة")
            if row["local_case"]:
                state = "مبني في محل " + state
                if row["actual_role"].startswith("imperfect_"):
                    role = "فعل مضارع"
            signs = row["assignment"].get("sign_candidates", [])
            labels = sorted({SIGN_NAMES.get(s["sign_name"], s["sign_name"])+" ("+
                             MODES.get(s["mode_name"], s["mode_name"])+")" for s in signs})
            phrase = f"{row['surface']}: {role}؛ {state}"
            if labels and not row["local_case"]:
                phrase += "؛ العلامة: " + " / ".join(labels)
            phrase += "."
        # Each alternative retains its own frame and source identity in rows.
        if phrase not in lines:
            lines.append(phrase)
    return ("النتائج التالية مشروطة بمقدمات أصحابها، مع حفظ البدائل:\n"+"\n".join(lines)
            if lines else "لم تتوافر إسنادات إعرابية في الأطر الحالية؛ راجع نواقص تقريري القراءة.")


def analyze(request):
    text, lexical, context = _request(request)
    retrieved = answer(request.get("query", "المرفوعات المنصوبات المجرورات المجزومات"),
                       domain=request.get("domain"), limit=request.get("limit", 5))
    model = learn_qac_lexicon(lexical.encode(), source_id="irab_lexical_evidence") if lexical else None
    discourse = read_discourse(text, lexical_model=model, context=context)
    inflection = read_inflection(text, lexical_model=model)
    rows = []
    for clause in discourse["clauses"]:
        for analysis in clause["analyses"]:
            for assignment in analysis["assignments"]:
                licensed = bool(assignment.get("activated") and analysis["licensed_syntax"]
                                and not analysis["rejected_candidate"])
                rows.append(_row("discourse", analysis["analysis_id"], assignment,
                                 licensed=licensed, supports=analysis["supports"]))
    readings = {r["reading_id"]: r for o in inflection["occurrences"] for r in o["readings"]}
    raw = text.encode()
    for relation in inflection["relations"]:
        reading = readings[relation["dependent"]["reading_id"]]
        span = relation["dependent"]["span"]
        assignment = {"reading_id": reading["reading_id"], "span": span,
            "surface": raw[span["start"]:span["end"]].decode(), "role": relation["label"],
            "actual_role": reading["actual_role"], "inflected_case": reading["actual_case"],
            "local_case": reading["local_case"], "sign_candidates": relation["sign_candidates"],
            "case_domain": relation["case_domain"], "required_case": relation["case_name"],
            "status": relation["status"], "head_span": relation["head"]["span"]}
        rows.append(_row("inflection", relation["relation_id"], assignment,
                         licensed=relation["activated"], supports=relation["supports"]))
    # This front door does not yet acquire the four causal witnesses. Neither
    # an operator spelling nor a retrieved passage can fill those premises.
    causal_premises = {k: False for k in CAUSAL_BITS}
    result = {"schema": "nabt.irab-agent.v1", "request_sha256": digest(request),
        "source_sha256": discourse["source_sha256"], "status": "OWNER_RESULTS",
        "owner_statuses": {"discourse": discourse["status"], "inflection": inflection["status"]},
        "owner_reports": {"discourse": discourse, "inflection": inflection},
        "rows": rows, "views": {d: [r["row_id"] for r in rows if d in r["domains"]] for d in DOMAINS},
        "causal_projection": {"status": "DEFER", "owner": "nabt.discourse_laws.causal_allowed",
            "premises": causal_premises, "allowed": causal_allowed(**causal_premises),
            "premise_status": {k: "UNACQUIRED" for k in CAUSAL_BITS},
            "missing": list(CAUSAL_BITS), "cause": None, "effect": None,
            "reason": "NO_ACQUIRED_CAUSAL_RELATION_WITNESS",
            "inverse_inference_licensed": False, "world_truth_established": False},
        "answer_ar": _explain(rows), "retrieved_explanation": retrieved,
        "retrieval_prunes_owner_candidates": False, "world_truth_established": False,
        "authority": "EXISTING_OWNER_VIEWS_NOT_A_NEW_CERTIFICATE"}
    _encoded(result, MAX_REPORT, floats=True)
    return result


def verify(report, *, expected_request):
    _encoded(report, MAX_REPORT, floats=True)
    fresh = analyze(expected_request)
    return {"valid": _encoded(report, MAX_REPORT, floats=True) == _encoded(fresh, MAX_REPORT, floats=True),
            "verification": "FRESH_OWNER_AND_SOURCE_REPLAY",
            "authority": "SOURCE_RELATIVE_NOT_WORLD_TRUTH"}
