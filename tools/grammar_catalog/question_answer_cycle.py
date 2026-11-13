"""Generate, parse and assess source-bound exercises over two existing NABT owners."""
from fractions import Fraction
from hashlib import sha256
import re

from . import question_cognition as cognition, question_frames as frames
from .operations import digest

LAW = "nabt.question-answer-cycle.v1"
TITLES = {"instrument": "استعمال الآلة", "condition": "شرط الوصول",
          "joint": "اجتماع الشرط والآلة", "occurrence": "وقوع الحدث في الخارج"}
ASPECT = {"instrument": "نسبة استعمال «{}» إلى الفعل", "condition": "اشتراط وصول «{}» للفعل",
          "joint": "اشتراط وصول «{0}» واستعماله آلةً للفعل", "occurrence": "وقوع الفعل في الخارج"}
PREFIX = "في العبارة «"
SEPARATOR = "»، هل يثبت النص "
SURFACES = {"SUPPORTED": "نعم", "REFUTED": "لا", "OPEN": "غير محسوم", "CONFLICT": "تعارضت الشواهد"}
BY_RESPONSE = {surface: state for state, surface in SURFACES.items()}
TWO = "الاحتمالان موافقان للنص"
EVIDENCE = re.compile(r"الشاهد «([^«»]+)»((?: و«[^«»]+»)*)")
ARITHMETIC = re.compile(r"[0-9٠-٩+*/()×÷^=\s\-]+")
NUMBER = re.compile(r"([+-]?[0-9٠-٩]{1,18})(?:/([0-9٠-٩]{1,18}))?")
FORMAL = {"quantity": "ما قيمة التعبير «{}»؟", "proposition": "هل تصح المساواة «{}»؟"}
VERDICTS = {"CORRECT": "صواب", "CONTRADICTED": "يخالف الدليل", "UNSUPPORTED": "جزم بلا دليل كافٍ",
            "CONTESTED": "تعارضت الشواهد", "WRONG_STATUS": "وصف حالة الدليل غير مطابق",
            "UNPARSED": "تعذّر تفكيك الجواب", "WRONG_TYPE": "نوع الجواب لا يوافق المطلوب",
            "UNDEFINED": "العملية الحسابية غير معرّفة"}


def validate(question, answer):
    validate_bound_question(question)
    if type(answer) is not str or not answer.strip() or len(answer.encode()) > 2048:
        raise ValueError("Expected a nonempty answer within 2048 UTF-8 bytes")


def validate_bound_question(question):
    if type(question) is not str:
        raise ValueError("Expected an Arabic question")
    validate_size = 3072 if any(question.startswith(t.split("{}")[0]) for t in FORMAL.values()) else 512
    if not question.strip() or len(question.encode()) > validate_size:
        raise ValueError("Question exceeds its source-bound grammar budget")


def question_text(event, op):
    return PREFIX + event["event"]["text"] + SEPARATOR + ASPECT[op].format(event["candidate_instrument"]) + "؟"


def parse_question(question, event):
    """Decompose the surface; bind both event and instrument to this occurrence."""
    if not question.startswith(PREFIX) or not question.endswith("؟"):
        return None
    head, boundary, clause = question[len(PREFIX):-1].partition(SEPARATOR)
    if not boundary or head != event["event"]["text"]:
        return None
    for op, aspect in ASPECT.items():
        if clause == aspect.format(event["candidate_instrument"]):
            return op
    return None


def parse_answer(answer):
    lead, sep, reason = answer.strip().removesuffix(".").partition("؛ ")
    stance = BY_RESPONSE.get(lead)
    if stance is None:
        return None
    if not sep:
        return {"stance": stance, "basis": "NONE", "quotes": []}
    if reason == TWO:
        return {"stance": stance, "basis": "MODELS", "quotes": []}
    match = EVIDENCE.fullmatch(reason)
    if match:
        return {"stance": stance, "basis": "CITATIONS", "quotes": re.findall(r"«([^«»]+)»", reason)}
    return None


def inspect_reason(parsed, decision):
    if parsed["basis"] == "NONE":
        return "NOT_GIVEN", []
    if parsed["basis"] == "MODELS":
        return ("COUNTERMODELS" if decision["status"] == "OPEN" else "INVALID_MODELS"), []
    matches = [[i for i, row in enumerate(decision["evidence"]) if row["witness"]["text"] == quote]
               for quote in parsed["quotes"]]
    if any(not ids for ids in matches):
        return "NOT_IN_SOURCE", matches
    cited = {i for ids in matches for i in ids}
    if cited.intersection(decision["irrelevant_evidence"]):
        return "IRRELEVANT", matches
    if any(set(p["evidence_ids"]) <= cited for p in decision["minimal_supports"]):
        return "SUFFICIENT", matches
    return "INSUFFICIENT", matches


def grade_event(answer, decision):
    parsed = parse_answer(answer)
    if parsed is None:
        return {"answer_parts": None, "claim": "UNPARSED", "reason": "NOT_ASSESSED", "complete": False}
    actual, given = decision["status"], parsed["stance"]
    if actual == given:
        claim = "CORRECT"
    elif given in ("OPEN", "CONFLICT"):
        claim = "WRONG_STATUS"
    else:
        claim = {"OPEN": "UNSUPPORTED", "CONFLICT": "CONTESTED"}.get(actual, "CONTRADICTED")
    reason, matches = inspect_reason(parsed, decision)
    return {"answer_parts": parsed, "claim": claim, "reason": reason, "quote_evidence_ids": matches,
            "complete": claim == "CORRECT" and reason in ("SUFFICIENT", "COUNTERMODELS")}


def event_item(text, event, question, source_id, submitted):
    op = parse_question(question, event)
    if op is None:
        return None
    owner = cognition.analyze(text, cognition.QUESTIONS[op][0], source_id)
    decision = owner["decision"]
    if decision["status"] not in SURFACES:
        return {"question": question, "operation": op, "status": decision["status"], "owner": owner}
    if decision["status"] == "OPEN":
        justification = TWO
    else:
        proof = decision["minimal_supports"][0]["evidence_ids"]
        quotes = [decision["evidence"][i]["witness"]["text"] for i in proof]
        justification = "الشاهد " + " و".join("«" + q + "»" for q in quotes)
    generated = SURFACES[decision["status"]] + "؛ " + justification + "."
    return {"question": question, "operation": op, "submitted_answer": submitted,
            "question_parts": {"force": "استفهام", "target": TITLES[op], "event": event,
                               "scope": "WORLD" if op == "occurrence" else "SOURCE",
                               "axes": decision["required_axes"]},
            "status": decision["status"], "answer": generated, "generated_grade": grade_event(generated, decision),
            "submitted_grade": grade_event(submitted, decision) if submitted is not None else None,
            "rubric": {"predicted_status": decision["status"], "minimal_supports": decision["minimal_supports"],
                       "countermodels": decision["alternatives"], "conflicting_axes": decision["conflicting_axes"]},
            "owner": owner}


def arithmetic_answer(result):
    if result["status"] == "BLOCKED":
        return "غير معرّف"
    if result["sort"] == "proposition":
        return "صحيحة" if result["truth"] else "غير صحيحة"
    v = result["value"]
    return str(Fraction(int(v["numerator"]), int(v["denominator"])))


def parse_fraction(surface):
    match = NUMBER.fullmatch(surface)
    if match and int(match[2] or 1):
        return str(Fraction(int(match[1]), int(match[2] or 1)))
    return None


def grade_arithmetic(answer, result):
    surface = answer.strip()
    number = parse_fraction(surface)
    value = None
    if surface in ("صحيحة", "غير صحيحة"):
        kind, value = "proposition", surface == "صحيحة"
    elif surface == "غير معرّف":
        kind = "undefined"
    elif number is not None:
        kind, value = "quantity", number
    else:
        return {"claim": "UNPARSED", "reason": "NOT_ASSESSED", "complete": False, "answer_parts": None}
    if result["status"] == "BLOCKED":
        claim = "CORRECT" if kind == "undefined" else "UNDEFINED"
    elif kind != result["sort"]:
        claim = "WRONG_TYPE"
    else:
        if kind == "proposition":
            correct = value == result["truth"]
        else:
            expected = result["value"]
            correct = Fraction(value) == Fraction(int(expected["numerator"]), int(expected["denominator"]))
        claim = "CORRECT" if correct else "CONTRADICTED"
    return {"claim": claim, "reason": "NATIVE_REPLAY", "complete": claim == "CORRECT",
            "answer_parts": {"sort": kind, "value": value}}


def run(text, source_id="input", *, question=None, answer=None):
    if question is not None:
        validate_bound_question(question)
    if answer is not None:
        validate(question, answer)
    report = {"law": LAW, "source_id": source_id, "source_sha256": sha256(text.encode()).hexdigest(),
              "items": [], "status": "OUTSIDE_SOURCE", "world_truth_established": False}
    event, _ = frames.clauses(text)
    if event is not None:
        questions = [question] if question is not None else [question_text(event, op) for op in TITLES]
        for q in questions:
            item = event_item(text, event, q, source_id, answer)
            if item is not None:
                report["items"].append(item)
    elif ARITHMETIC.fullmatch(text) and text.strip():
        owner = cognition.analyze(text, cognition.QUESTIONS["arithmetic"][0], source_id)
        decision = owner["decision"]
        if decision["status"] not in ("COMPUTED", "BLOCKED"):
            return {**report, "status": decision["status"], "owner": owner}
        result = decision["value"]
        sort = result["sort"]
        q = FORMAL[sort].format(text)
        if question is None or q == question:
            generated = arithmetic_answer(result)
            projection = decision["owner"]["projection"]
            report["items"].append({"question": q, "operation": "arithmetic", "status": decision["status"],
                  "submitted_answer": answer,
                  "question_parts": {"force": "استفهام", "target": sort, "scope": "FORMAL",
                                     "expression": text, "operation_tree": projection["operation_tree"]},
                  "answer": generated, "generated_grade": grade_arithmetic(generated, result),
                  "submitted_grade": grade_arithmetic(answer, result) if answer is not None else None,
                  "rubric": {"result": result, "trace": projection["trace"]}, "owner": owner})
    else:
        return report
    report["status"] = "ASSESSED" if report["items"] else "QUESTION_NOT_BOUND_TO_SOURCE"
    return report


REASONS = {"NOT_GIVEN": "لم يُذكر دليل.", "SUFFICIENT": "الشاهد يكفي لهذا الحكم.",
           "IRRELEVANT": "يتعلق أحد الشواهد بمحور آخر.", "INSUFFICIENT": "الشواهد المذكورة غير كافية.",
           "NOT_IN_SOURCE": "تعذرت مطابقة الاقتباس بشاهد في النص.", "COUNTERMODELS": "صورتان توافقان النص وتختلفان في الجواب.",
           "INVALID_MODELS": "لا تدعم الشواهد دعوى الاحتمالين.", "NATIVE_REPLAY": "أعيد حساب التعبير من الأصل.",
           "NOT_ASSESSED": "لم تُفحص حجة لصيغة جواب غير مقروءة."}


def cards(report):
    from .text_reading import card
    if not report["items"]:
        return [card("question_answer_cycle", report["status"], "تعذّر إتمام دورة السؤال والجواب.",
                     report["status"], "تُراجَع صيغة السؤال والنص الأصلي.")]
    results = []
    for item in report["items"]:
        if "generated_grade" not in item:
            results.append(card("question_answer_cycle", item["status"], item["question"],
                                item["status"], "بقي فحص الجواب مفتوحًا."))
            continue
        grade = item["submitted_grade"] or item["generated_grade"]
        assessed = "تقويم الجواب المقدّم «" + item["submitted_answer"] + "»: " if item["submitted_grade"] else ""
        results.append(card("question_answer_cycle", item["question"], item["answer"],
                            assessed + VERDICTS[grade["claim"]] + ". " + REASONS[grade["reason"]],
                            "الحكم في نطاق السؤال وشواهده.", criterion=grade, rubric_digest=digest(item["rubric"])))
    return results
