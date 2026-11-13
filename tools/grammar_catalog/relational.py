"""Relational RAG views over existing owners, not an ontology truth engine.

Shape, lexical sense, grammatical role, property and causal explanation are
separate coordinates. Search supplies references; owners retain all decisions.
"""
from collections import Counter
from copy import deepcopy
from hashlib import sha256

from nabt.derivation import pattern_catalog, read_derivation
from nabt.errors import NabtError
from nabt.learning.source_evidence import SourceBlob, SourceSpan
from tools.evidence_lifecycle_v1 import _encoded
from tools.lexical_training.reasoning_curriculum import matrix as cognitive_matrix
from .catalog import build_catalog
from .operations import ROOT, digest, exact_terms
from .retrieval import SearchIndex, RetrievalError, tokens, _text, _limit

AUTHORITY = "RELATIONAL_OWNER_VIEW_NOT_ONTOLOGY_CERTIFICATION"
PAST_IDS = ("past.I.a", "past.I.i", "past.I.u")
FAMILIES = ("derivation-patterns", "inflection", "discourse", "classical-source-rules",
            "signed-inference", "mantuq-mafhum", "epistemic-measurement", "rule-learning")

# Fixed source windows in the already verified Qatr edition, not a new text.
WINDOWS = {"subject": (219, 226), "object": (267, 269), "masdar": (289, 292),
           "purpose": (293, 296), "adverb": (297, 300), "accompaniment": (301, 305),
           "masdar_work": (351, 357), "active_participle": (358, 363),
           "passive_participle": (365, 365), "sifa": (366, 369)}

# Typed explanatory projections. None certifies application to a sentence.
RELATIONS = (
    ("subject", "الفاعلية الفاعل النحوي", "event", "participant", ("subject", "active_participle"),
     "الإسناد وشاهد الدور والتعدية مستقلون عن الإرادة والتأثير السببي؛ لللازم والمتعدي فاعل."),
    ("object", "المفعولية المفعول به", "event", "argument", ("object", "passive_participle"),
     "يلزم تعيين معنى الفعل وإطاره ومعموله؛ لا يثبت النصب وحده المفعولية أو حدوث تغير مادي."),
    ("masdar", "المصدر الحدث وعمل المصدر", "expression", "event_concept", ("masdar", "masdar_work"),
     "المصدر يحتفظ بمخطط الحدث وروابطه بالجنس والخاصية والزمان والمكان؛ تعيين الوقوع وشواهده مرحلة مستقلة عن تجريد المتغيرات وعن الوزن."),
    ("accompaniment", "المصاحبة المفعول معه", "event", "accompaniment", ("accompaniment",),
     "المعية تحتاج قراءة الواو والتعلق؛ لا تتحول إلى علاقة سبب ونتيجة."),
    ("purpose", "التعليل الغرض المفعول لأجله", "event", "reported_reason", ("purpose",),
     "المصدر المعلل وشروط مشاركة الوقت والفاعل في هذا المصدر؛ لا إثبات لدافع خفي أو سبب تجريبي."),
    ("event_place", "المفعول فيه ظرف المكان", "event", "place", ("adverb",),
     "التعلق والمرجع المكاني مستقلان عن تجاور الكلمات وعن انتماء الفرد إلى الجنس."),
    ("event_time", "المفعول فيه ظرف الزمان", "event", "time", ("adverb",),
     "وقت الحدث ووقت القول والمرجع والسياق حقول مستقلة؛ لا زمن وقوع من وزن المصدر."),
    ("derived_property", "المشتق الصفة وحاملها اسم الفاعل اسم المفعول", "bearer", "property", ("active_participle", "passive_participle", "sifa"),
     "تصنيف الجامد والمشتق غير تصنيف الكيان والحدث والخاصية؛ حفظ البدائل قبل ربط الصفة بحاملها."),
)


def _anchors(grammar):
    source = next(s for s in grammar["sources"] if s["source_id"] == "qatr")
    blob = SourceBlob(source["source_id"], (ROOT / source["local_path"]).read_bytes())
    if blob.sha256 != source["sha256"]:
        raise ValueError("Qatr source changed after catalogue replay")
    lines = blob.raw_bytes.splitlines(keepends=True)
    result = {}
    for name, (first, last) in WINDOWS.items():
        start, end = sum(map(len, lines[:first-1])), sum(map(len, lines[:last]))
        raw = blob.raw_bytes[start:end]
        span = SourceSpan(blob.source_id, blob.sha256, start, end, sha256(raw).hexdigest())
        span.extract(blob)
        result[name] = {"id": "qatr:relation:"+name, "source": source,
            "lines_inclusive": [first, last], "start": start, "end": end,
            "sha256": span.span_sha256, "raw_text": raw.decode(),
            "authority": "RULE_SOURCE_NOT_SENTENCE_APPLICATION_CERTIFICATE"}
    return result


def catalog():
    grammar, patterns, cognitive = build_catalog(), pattern_catalog(), cognitive_matrix()
    anchors = _anchors(grammar)
    by_id = {p["id"]: p for p in patterns["patterns"]}
    past = [by_id[p] for p in PAST_IDS]
    if any(p["arity"] != 3 or p["augmentation"] != "mujarrad" or
           p["voice"] != "active" or p["endings"] != ["َ"] for p in past):
        raise ValueError("Installed bare past domain differs")
    cards = [{"id": "shape:"+p["id"], "kind": "past_shape", "label": p["label"]+"َ",
              "pattern": p, "description": "الماضي الثلاثي المجرد؛ فتح العين أو كسرها أو ضمها محفوظ.",
              "required_evidence": ["lexical_root", "sense_id", "attested_masdar", "present_stem", "valency_frame"],
              "related_proof_families": ["derivation-patterns"], "semantic_license": False} for p in past]
    for key, label, left, right, source_ids, boundary in RELATIONS:
        cards.append({"id": "relation:"+key, "kind": "grammatical_relation", "label": label,
            "edge_types": {"left": left, "right": right}, "description": boundary,
            "sources": [anchors[s] for s in source_ids],
            "related_proof_families": ["classical-source-rules", "derivation-patterns", "discourse"],
            "application_certified": False, "automatic_acquisition_complete": False})
    # Do not copy or reinterpret the established kind/property/space/time rules.
    for row in cognitive["shared_foundation"]["rows"]:
        cards.append({"id": "foundation:"+row["id"], "kind": "ontology_requirement",
            "label": row["label_ar"], "description": row["open_obligation_ar"],
            "existing_curriculum_row": row, "ontology_certified": False})
    cards.append({"id": "relation:effect", "kind": "causal_projection", "label": "المسببية النتيجة والأثر",
        "description": "السبب والنتيجة طرفان لعلاقة مثبتة في نطاقها؛ عرض الطرف الناتج لا يرخص عكس الاستدلال.",
        "same_relation_as": "foundation:causal_relation", "inverse_inference_licensed": False})
    from .relational_bridge import lexical_cards, contract_cards
    cards.extend(lexical_cards())
    cards.extend(contract_cards())
    return {"schema": "nabt.relational-rag.catalog.v1", "authority": AUTHORITY,
        "cards": cards, "past_patterns": past, "pattern_table_sha256": patterns["table_sha256"],
        "nominal_candidates": [p for p in patterns["patterns"] if p["form"] == "nominal"],
        "proof_families": list(FAMILIES), "proof_relation": "RELATED_OWNER_SCOPE_NOT_NEW_REFINEMENT",
        "cognitive_source_review": {k:cognitive["source_review"][k] for k in ("path", "sha256")},
        "past_to_nominal_link": {"status": "REQUIRES_LEXICAL_SENSE_AND_DERIVATION_WITNESSES",
            "cartesian_product_is_license": False, "shared_root_is_sufficient": False},
        "certificate_fields": ["source_id", "source_sha256", "source_span", "sense_id", "referent_id",
            "individual_or_kind", "relation_type", "direction", "scope", "time_frame", "spatial_frame",
            "conditions", "blockers", "counterevidence", "rule_reference", "owner_receipt"],
        "progression": ["source_occurrence", "shape_candidates", "lexical_sense_and_valency",
                        "grammatical_relation", "kind_property_or_disposition", "scoped_ontology_claim"],
        "world_truth_established": False}


class RelationalIndex(SearchIndex):
    def __init__(self):
        self._catalog = catalog()
        self.catalog_sha256 = digest(self._catalog)
        self._docs = {}
        for card in self._catalog["cards"]:
            body = " ".join(s["raw_text"] for s in card.get("sources", []))
            self._add("item", card["id"], card["id"]+" "+card["label"]+" "+card["description"]+" "+body, card)
        self._tf = {k:Counter(tokens(v["search_text"])) for k,v in self._docs.items()}

    def search(self, query, limit=5):
        if digest(catalog()) != self.catalog_sha256:
            raise RetrievalError("STALE_RELATIONAL_CATALOG")
        result = super().search(query, limit=limit)
        focus = [p["id"] for p in self._catalog["past_patterns"] if query.strip() == p["label"]+"َ"]
        result.update(raw_query=query, query_occurrences=exact_terms(query),
            lexical_review_matches=[r for r in self._catalog["cards"]
                if r["kind"] == "reviewed_relational_reading" and query.strip() in r["reading"]["spellings"]],
            vocalized_shape_focus=focus,
            exact_shape_records=[self.rehydrate("item", "shape:"+p) for p in focus],
            normalization_authority="SEARCH_ONLY_NO_SHAPE_OR_MEANING_EQUIVALENCE")
        return result


def search(query, limit=5):
    return RelationalIndex().search(query, limit)


def validate(request):
    if type(request) is not dict or "text" not in request or set(request)-{
            "text", "source_id", "query", "limit", "lexical_text", "context", "temporal", "inference", "bridge", "neural_continuity", "root_sense", "question", "question_chain"}:
        raise ValueError("Expected source text and existing owner inputs only")
    _encoded(request, 2*1048576)
    if not _text(request["text"], "text", maximum=8192).strip():
        raise ValueError("Nonempty original text required")
    if not _text(request.get("source_id", "input"), "source_id", maximum=128).strip():
        raise ValueError("Nonempty source identity required")
    _limit(request.get("limit", 5))
    if "neural_continuity" in request and type(request["neural_continuity"]) is not bool:
        raise ValueError("Optional neural continuity must be a boolean")
    _text(request.get("query", "الأجناس الخواص الفاعلية المفعولية المصدر المكان الزمان"), "query")
    if "question_chain" in request and (request["question_chain"] is not True or "question" in request):
        raise ValueError("Expected a chain without a separate question")
    if "question" in request:
        from .question_cognition import validate as validate_question
        validate_question(request["question"])
    if "root_sense" in request:
        from .root_sense import validate as validate_root_sense
        validate_root_sense(request["root_sense"])
    if "bridge" in request:
        from .relational_bridge import validate as validate_bridge
        validate_bridge(request["bridge"])
    if "inference" in request:
        p = request["inference"]
        if type(p) is not dict or not {"query", "plan"} <= p.keys() or set(p)-{
                "query", "plan", "revision", "scope", "context", "time"}:
            raise ValueError("Inference source and identity are bound by the outer request")
        from .gateway_routes import validate as route_validate
        route_validate("mantuq.source", {"source":request["text"], "source_id":request.get("source_id", "input"), **p})
    return deepcopy(request)


def analyze(request):
    p = validate(request)
    text, source_id = p["text"], p.get("source_id", "input")
    from .irab import analyze as irab_analyze
    from .temporal import evaluate as temporal_evaluate
    reports, failures = {}, {}
    calls = (("derivation", lambda: read_derivation(text, source_id=source_id, scope="relational", profile="surface_v1")),
             ("irab", lambda: irab_analyze({k:v for k,v in p.items() if k in {"text", "source_id", "lexical_text", "context"}})),
             ("temporal", lambda: temporal_evaluate({"text":text, "source_id":source_id, "temporal":p.get("temporal")})))
    for name, call in calls:
        try:
            reports[name] = call()
        except NabtError as error:
            failures[name] = error.as_dict()
    if "inference" in p:
        from .gateway_routes import execute
        reports["source_inference"] = execute("mantuq.source", {"source":text, "source_id":source_id, **p["inference"]})
    occurrences = reports.get("derivation", {}).get("occurrences", [])
    # Each occurrence retains its own source span, including repeated strings.
    shapes = [{"occurrence_id":r["occurrence_id"], "span":r["span"], "surface":r["surface"],
        "reading_context":r["reading_context"], "past_pattern_candidates":[c["pattern_id"] for c in r["candidates"] if c["pattern_id"] in PAST_IDS],
        "all_pattern_candidates":[c["pattern_id"] for c in r["candidates"]],
        "lexical_meaning_certified":False} for r in occurrences]
    roles = [{"owner_row_id":r["row_id"], "frame_id":r["frame_id"], "span":r["span"],
        "candidate_role":r["candidate_role"], "actual_role":r["actual_role"], "owner_licensed":r["licensed"],
        "ontology_role_certified":False} for r in reports.get("irab", {}).get("rows", [])]
    result = {"schema":"nabt.relational-rag.analysis.v1", "authority":AUTHORITY, "status":"OWNER_RESULTS",
        "source_id":source_id, "source_sha256":sha256(text.encode()).hexdigest(),
        "retrieval":search(p.get("query", "الأجناس الخواص الفاعلية المفعولية المصدر المكان الزمان"), p.get("limit", 5)),
        "shape_occurrences":shapes, "grammatical_roles":roles, "owner_reports":reports, "owner_failures":failures,
        "ontology_bridge":{"status":"DEFER", "ontology_assertions":[],
            "missing":["LEXICAL_SENSE_TO_KIND_OR_PROPERTY", "SCOPED_MEMBERSHIP_OR_PROPERTY_WITNESS",
                       "DISPOSITION_CONDITIONS_AND_BLOCKERS", "GRAMMATICAL_TO_ONTOLOGICAL_ROLE_ALIGNMENT"],
            "source_inference_role":"ORIGINAL_CONDITIONAL_RESULT_NOT_AUTOMATIC_ONTOLOGY_ASSERTION"},
        "retrieval_prunes_owner_candidates":False, "world_truth_established":False,
        "empirical_causality_established":False, "new_lean_proof":False}
    if "root_sense" in p:
        from .root_sense import analyze as analyze_root_sense
        result["root_sense"] = analyze_root_sense(text, source_id, p["root_sense"], reports.get("derivation", {}))
    if "bridge" in p:
        from .relational_bridge import evaluate as evaluate_bridge
        result["ontology_bridge"] = evaluate_bridge(text, p["bridge"])
        result["new_lean_proof"] = True
    from .relational_bridge import continuity
    result["semantic_continuity"] = continuity(text, result["ontology_bridge"])
    if p.get("neural_continuity"):
        from tools.lexical_training.relational_alignment import rank
        result["neural_continuity"] = rank({"text":text, "source_id":source_id})
    from . import definition_network
    if definition_network.QUERY.fullmatch(text):
        result["definition_network"] = definition_network.read(text, identity=source_id)
    from .interpretation_chains import analyze as analyze_chain
    chain = analyze_chain(text)
    if chain is not None:
        result["interpretation_chain"] = chain
    if "question" in p:
        from .question_cognition import analyze as answer_question
        result["question_cognition"] = answer_question(text, p["question"], source_id)
    if p.get("question_chain"):
        from . import graded_questions
        result["graded_questions"] = graded_questions.run(text, source_id, bridge=p.get("bridge"),
                                                          retained_bridge=result["ontology_bridge"] if "bridge" in p else None)
    _encoded(result, 8*1048576, floats=True)
    return result
