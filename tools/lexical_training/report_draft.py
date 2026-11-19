"""Pure, replayable report task. The local draft store belongs to the NTP host."""
from datetime import datetime
import re

from nabt.counting import _numeral_prefix
from nabt.errors import NabtError
from tools import evidence_lifecycle_v1 as wire
from tools.grammar_catalog.classical_roles import compatible
from tools.grammar_catalog.operations import digest, exact_terms
from . import ntl_curriculum

SCHEMA = "ntl.report-draft.v1"
RESULT = "ntl.report-draft-result.v1"
POLICY = "report-draft.same-unit-strictly-greater.v1"
REFERENCE = ("التَّقْرِيرَ الأَخِيرَ", "أَحْدَثَ تَقْرِيرٍ")
COUNT = ("وَاسْتَخْرِجْ عَدَدَ الطَّلَبَاتِ الْمُعَلَّقَةِ", "ثُمَّ احْسُبْ عَدَدَ الطَّلَبَاتِ الْمُعَلَّقَةِ",
         "وَاحْسُبْ عَدَدَ الطَّلَبَاتِ الْمُعَلَّقَةِ")
CONDITION = ("إِذَا زَادَ عَلَى", "وَإِذَا زَادَ عَلَى", "إِذَا زَادَ الْعَدَدُ عَلَى", "إِنْ تَجَاوَزَ الْعَدَدُ")
DRAFT = ("فَأَنْشِئْ مُسَوَّدَةَ تَنْبِيهٍ",)
PROHIBIT = ("لَا تُرْسِلْهَا", "وَلَا تُرْسِلْهَا")
PENDING = ("مُعَلَّق", "قَيْد الِانْتِظَار")
CLOSED = ("مُغْلَق", "مُكْتَمِل")
ID = re.compile(r"[^\W_][\w.-]{0,63}\Z")


def phrase(words, forms):
    return any(len(words) == len(form.split()) and
               all(compatible(w, f) for w, f in zip(words, form.split())) for form in forms)


def read_instruction(text):
    terms = exact_terms(text)
    cursor = 0
    witnesses = {}
    if not terms:
        return None

    def gap(start, end):
        return text[start:end].strip()

    def consume(role, forms):
        nonlocal cursor
        for form in forms:
            part = terms[cursor:cursor + len(form.split())]
            if not phrase([t["surface"] for t in part], (form,)):
                continue
            if any(gap(a["codepoint_span"][1], b["codepoint_span"][0]) for a, b in zip(part, part[1:])):
                continue
            previous = terms[cursor - 1]["codepoint_span"][1] if cursor else 0
            allowed = ("", "،", ",", ".", "؛", ";") if cursor else ("",)
            if gap(previous, part[0]["codepoint_span"][0]) not in allowed:
                continue
            witnesses[role] = [part[0]["utf8_span"][0], part[-1]["utf8_span"][1]]
            cursor += len(part)
            return True
        return False

    question = consume("count_question", ("كَمْ عَدَدُ الطَّلَبَاتِ الْمُعَلَّقَةِ فِي",))
    if question:
        if not consume("latest", ("التَّقْرِيرِ الأَخِيرِ", "أَحْدَثِ تَقْرِيرٍ")):
            return None
    elif not (consume("read", ("اِقْرَأْ",)) and consume("latest", REFERENCE) and consume("count", COUNT)):
        return None
    threshold = None
    if not question and cursor < len(terms):
        if not consume("if_strictly_greater", CONDITION):
            return None
        start = cursor
        while cursor < len(terms) and cursor - start < 3 and not compatible(terms[cursor]["surface"], "فَأَنْشِئْ"):
            cursor += 1
        part = terms[start:cursor]
        if not part or any(gap(a["codepoint_span"][1], b["codepoint_span"][0])
                           for a, b in zip(terms[start - 1:cursor], part)):
            return None
        try:
            number = _numeral_prefix(part)
        except NabtError:
            return None
        if not number or number["status"] != "READ_VALUE":
            return None
        threshold = number["value"]
        witnesses["threshold"] = [part[0]["utf8_span"][0], part[-1]["utf8_span"][1]]
        if not (consume("draft", DRAFT) and consume("prohibit_send", PROHIBIT)):
            return None
    ending = gap(terms[-1]["codepoint_span"][1], len(text))
    if cursor != len(terms) or ending not in (("", "؟", "?") if question else ("", ".")):
        return None
    return {"witnesses_utf8": witnesses, "threshold": threshold, "intent": "COUNT" if threshold is None else "CONDITIONAL_DRAFT"}


def validated(lesson):
    optional = {"prior_examples", "store_observation"}
    wire._fields(lesson, {"schema", "instruction", "task_id", "reports"} | (optional & lesson.keys()), "report task")
    if not isinstance(lesson["task_id"], str) or not ID.fullmatch(lesson["task_id"]):
        raise ValueError("Invalid logical task ID")
    wire._text(lesson["instruction"], "instruction", 2048, content=True)
    wire._array(lesson["reports"], "report snapshots", 32)
    ids = set()
    for report in lesson["reports"]:
        if not isinstance(report, dict):
            raise ValueError("Expected a report object")
        wire._fields(report, {"id", "issued_utc", "rows"} | ({"vocabulary"} & report.keys()),
                     "immutable report revision")
        if "vocabulary" in report:
            wire._text(report["vocabulary"], "versioned status vocabulary", 80)
        if not isinstance(report["id"], str) or not ID.fullmatch(report["id"]) or report["id"] in ids:
            raise ValueError("Expected distinct report revision IDs")
        ids.add(report["id"])
        stamp = report["issued_utc"]
        if type(stamp) is not str or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", stamp):
            raise ValueError("Expected UTC seconds in canonical format")
        datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
        wire._array(report["rows"], "request rows", 256)
        for row in report["rows"]:
            if not isinstance(row, dict):
                raise ValueError("Expected a request row object")
            wire._fields(row, {"id", "status"} | ({"state_code"} & row.keys()), "request row")
            if "state_code" in row and ("vocabulary" not in report or row["state_code"] not in ("PENDING", "CLOSED")):
                raise ValueError("A witnessed state code needs a named vocabulary and supported value")
            if not isinstance(row["id"], str) or not ID.fullmatch(row["id"]):
                raise ValueError("Invalid request ID")
            wire._text(row["status"], "reported status", 80)
    if sum(len(r["rows"]) for r in lesson["reports"]) > 1024:
        raise wire.ResourceLimit("Report portfolio row limit")


def train_guard(before, after, prior=None):
    """Actively select discriminating worked cases using the installed NTL learner."""
    examples = [] if prior is None else prior
    wire._array(examples, "prior examples", 4)
    for row in examples:
        wire._fields(row, ("before", "after", "before_unit", "after_unit"), "worked comparison")
        if (type(row["before"]) is not int or type(row["after"]) is not int or row["before"] != 2
                or row["after"] not in (1, 3) or row["before_unit"] != "فرد"
                or row["after_unit"] not in ("فرد", "قطعة")):
            raise ValueError("Invalid prior comparison")
    examples = list(examples)
    exercise = {"before": before, "after": after}
    while True:
        state = ntl_curriculum.learn(examples, exercise)
        query = state["next_query"]
        if query is None:
            break
        if len(examples) == 4:
            raise ValueError("Incomplete or repeated training evidence")
        examples.append({"before": 2, "after": 3 if query["second_larger"] else 1,
                         "before_unit": "فرد", "after_unit": "فرد" if query["same_unit"] else "قطعة"})
    return {"policy": POLICY, "examples": examples, "reused_examples": len(prior or []), "result": state}


def decide(lesson):
    reading = read_instruction(lesson["instruction"])
    answer = {"reading": reading}
    if reading is None:
        return dict(answer, status="DEFER_INSTRUCTION", answer_ar="لم أحسم الغرض والقيود من العبارة كاملة.")
    reports = lesson["reports"]
    latest = max((r["issued_utc"] for r in reports), default=None)
    candidates = [r for r in reports if r["issued_utc"] == latest]
    answer["latest_candidates"] = [r["id"] for r in candidates]
    if len(candidates) != 1:
        return dict(answer, status="DEFER_REFERENCE", answer_ar="أحتاج إلى تعيين نسخة التقرير.")
    report = candidates[0]
    answer["report"] = {**{k: report[k] for k in ("id", "issued_utc")}, "sha256": digest(report)}
    # Induce a source-scoped lexicon from older operational records; no model label
    # is put on an unseen target row. Conflicting witnesses remain visible.
    testimony = {}
    for previous in reports:
        if (previous["issued_utc"] < latest and report.get("vocabulary") is not None
                and previous.get("vocabulary") == report["vocabulary"]):
            for i, row in enumerate(previous["rows"]):
                if "state_code" in row:
                    testimony.setdefault(row["status"], []).append(
                        {"report_id": previous["id"], "row": i, "state_code": row["state_code"]})
    answer["learned_status_witnesses"] = {
        key: testimony[key] for key in sorted({r["status"] for r in report["rows"]} & testimony.keys())}
    states, positions, issues = {}, {}, []
    for i, row in enumerate(report["rows"]):
        key = row["id"]
        status = row["status"].split()
        choices = {w["state_code"] for w in testimony.get(row["status"], ())}
        if phrase(status, PENDING):
            choices.add("PENDING")
        if phrase(status, CLOSED):
            choices.add("CLOSED")
        if "state_code" in row:
            choices.add(row["state_code"])
        positions.setdefault(key, []).append(i)
        if not choices:
            issues.append({"row": i, "id": key, "reason": "UNKNOWN_STATUS"})
        elif len(choices) > 1 or (key in states and states[key] not in choices):
            issues.append({"row": i, "id": key, "reason": "CONFLICTING_STATUS"})
        else:
            states[key] = choices.pop()
    answer["row_indices_by_id"] = positions
    if issues:
        return dict(answer, status="DEFER_ROWS", issues=issues, answer_ar="أحتاج إلى حسم حالات الصفوف المبيّنة قبل العدّ.")
    ids = sorted(i for i, state in states.items() if state == "PENDING")
    count = len(ids)
    answer.update(count=count, pending_ids=ids)
    summary = f"في التقرير {report['id']} عدد الطلبات المعلّقة المتميزة {count}."
    threshold = reading["threshold"]
    if threshold is None:
        return dict(answer, status="COUNTED", answer_ar=summary)
    learning = train_guard(threshold, count, lesson.get("prior_examples"))
    answer["learning"] = learning
    prediction = learning["result"]["prediction"]
    if prediction != [count > threshold] or len(learning["result"]["candidate_rules"]) != 1:
        return dict(answer, status="DEFER_LEARNING", answer_ar="لم يتفق المتعلّم مع فحص العدد والشرط.")
    if not prediction[0]:
        return dict(answer, status="NO_DRAFT", answer_ar=f"{summary} لم يزد العدد على {threshold}، فلا تنشأ مسودة.")
    body = f"مسودة تنبيه — {report['id']}\n{summary}\nمعرّفات الطلبات: " + "، ".join(ids) + "\n"
    return dict(answer, status="DRAFT_PLANNED", draft_body=body,
                answer_ar=f"{summary} تجاوز العدد {threshold}، فتحقق شرط إعداد المسودة.")


def run(lesson):
    validated(lesson)
    core = {k: lesson[k] for k in ("schema", "instruction", "task_id", "reports")}
    result = dict(decide(lesson), schema=RESULT, execution_measured=True, task_id=lesson["task_id"],
                  input_sha256=digest(core), world_truth_established=False, action_authority="NONE")
    if "store_observation" in lesson:
        observed = lesson["store_observation"]
        result["observation_basis"] = "SUPPLIED_LOCAL_STORE_SNAPSHOT"
        result["draft_observation"] = "ABSENT_IN_SNAPSHOT"
        if observed is not None:
            wire._fields(observed, ("input_sha256", "body_sha256"), "draft observation")
            if (type(observed["input_sha256"]) is not str or not re.fullmatch("[0-9a-f]{64}", observed["input_sha256"])
                    or (observed["body_sha256"] is not None and (type(observed["body_sha256"]) is not str
                        or not re.fullmatch("[0-9a-f]{64}", observed["body_sha256"])))):
                raise ValueError("Invalid observed digest")
            if observed["input_sha256"] != result["input_sha256"]:
                result["draft_observation"] = "TASK_ID_CONFLICT"
                result["answer_ar"] = "هذه الهوية مستعملة لمهمة بمدخلات أخرى."
            elif observed["body_sha256"] is None and result["status"] == "NO_DRAFT":
                result["draft_observation"] = "MATCHED_NO_DRAFT"
            elif result["status"] == "DRAFT_PLANNED" and observed["body_sha256"] == digest(result["draft_body"]):
                result["draft_observation"] = "MATCHED_SNAPSHOT"
                result["answer_ar"] += " تطابق نص المسودة المحفوظة مع الخطة."
            else:
                result["draft_observation"] = "STORE_MISMATCH"
                result["answer_ar"] = "تختلف المسودة المحفوظة عن نتيجة الفحص."
    return result
