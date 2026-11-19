"""Pure, replayable report task. The local draft store belongs to the NTP host."""
from datetime import datetime
from functools import lru_cache
import re

from nabt.counting import _numeral_prefix
from nabt.errors import NabtError
from nabt.learning.finite_guard import FeatureSchema, GuardLanguage, LearningSession, Observation
from tools import evidence_lifecycle_v1 as wire
from tools.grammar_catalog.classical_roles import compatible
from tools.grammar_catalog.operations import digest, exact_terms
from . import ntl_curriculum

SCHEMA = "ntl.report-draft.v1"
RESULT = "ntl.report-draft-result.v1"
POLICY = "report-draft.same-unit-strictly-greater.v1"
REFERENCE = ("التَّقْرِيرَ الأَخِيرَ", "أَحْدَثَ تَقْرِيرٍ")
COUNTED = ("الطَّلَبَاتِ الْمُعَلَّقَةِ",)
PROHIBIT = ("لَا تُرْسِلْهَا", "وَلَا تُرْسِلْهَا")
PENDING = ("مُعَلَّق", "قَيْد الِانْتِظَار")
CLOSED = ("مُغْلَق", "مُكْتَمِل")
ID = re.compile(r"[^\W_][\w.-]{0,63}\Z")
# Surface agreement depends on the subject: العدد (m.) or الطلبات (f.).
COUNT_GUARDS = {
    "GT": ("إِذَا زَادَ عَلَى", "وَإِذَا زَادَ عَلَى", "إِذَا زَادَ الْعَدَدُ عَلَى",
           "إِنْ تَجَاوَزَ الْعَدَدُ", "إِذَا تَجَاوَزَ الْعَدَدُ"),
    "GE": ("إِذَا بَلَغَ الْعَدَدُ", "إِنْ بَلَغَ الْعَدَدُ"),
}
PENDING_GUARDS = {
    "GT": ("إِذَا تَجَاوَزَتِ", "إِنْ تَجَاوَزَتِ"),
    "GE": ("إِذَا بَلَغَتِ", "إِنْ بَلَغَتِ"),
}


def phrase(words, forms):
    return any(len(words) == len(form.split()) and
               all(compatible(w, f) for w, f in zip(words, form.split())) for form in forms)


class InstructionCursor:
    """Consume an entire instruction with byte witnesses for every semantic slot."""
    def __init__(self, text):
        self.text = text
        self.terms = exact_terms(text)
        self.index = 0
        self.spans = {}

    def gap(self, i):
        left = self.terms[i - 1]["codepoint_span"][1] if i else 0
        right = self.terms[i]["codepoint_span"][0] if i < len(self.terms) else len(self.text)
        return self.text[left:right].strip()

    def bind(self, role, start, stop):
        self.spans[role] = [self.terms[start]["utf8_span"][0], self.terms[stop - 1]["utf8_span"][1]]

    def take(self, role, forms, *, clause=False):
        start = self.index
        allowed = ("", "،", ",", ".", "؛", ";") if clause and start else ("",)
        if self.gap(start) not in allowed:
            return False
        for form in forms:
            part = self.terms[start:start + len(form.split())]
            if (phrase([t["surface"] for t in part], (form,))
                    and not any(self.gap(i) for i in range(start + 1, start + len(part)))):
                self.index += len(part)
                self.bind(role, start, self.index)
                return True
        return False

    def numeral(self):
        start = self.index
        for length in range(min(len(self.terms) - start, 3), 0, -1):
            if any(self.gap(i) for i in range(start, start + length)):
                continue
            try:
                number = _numeral_prefix(self.terms[start:start + length])
            except NabtError:
                return None
            if number and number["status"] == "READ_VALUE":
                self.index += length
                self.bind("threshold", start, self.index)
                return number["value"]
        return None

    def guard(self, forms):
        for operator, variants in forms.items():
            role = "if_strictly_greater" if operator == "GT" else "if_at_least"
            if self.take(role, variants, clause=True):
                return operator
        return None


def read_instruction(text):
    c = InstructionCursor(text)
    question = c.take("count_question", ("كَمْ عَدَدُ",))
    operator = threshold = None
    if question:
        if not (c.take("counted", COUNTED) and c.take("in", ("فِي",))
                and c.take("latest", ("التَّقْرِيرِ الأَخِيرِ", "أَحْدَثِ تَقْرِيرٍ"))):
            return None
        c.spans["count_question"][1] = c.spans["in"][1]
    else:
        if not (c.take("read", ("اِقْرَأْ", "رَاجِعْ")) and c.take("latest", REFERENCE)):
            return None
        counted = c.take("count", ("وَاسْتَخْرِجْ عَدَدَ", "ثُمَّ احْسُبْ عَدَدَ", "وَاحْسُبْ عَدَدَ"), clause=True)
        if counted:
            if not c.take("counted", COUNTED):
                return None
            c.spans["count"][1] = c.spans["counted"][1]
        postposed = c.take("draft", ("وَأَعِدَّ مُسَوَّدَةَ تَنْبِيهٍ", "وَأَنْشِئْ مُسَوَّدَةَ تَنْبِيهٍ"), clause=True)
        if postposed or not counted or c.index < len(c.terms):
            operator = c.guard(PENDING_GUARDS)
            if operator:
                role = "counted_again" if counted else "counted"
                if not c.take(role, ("الطَّلَبَاتُ الْمُعَلَّقَةُ",)):
                    return None
            elif counted:
                operator = c.guard(COUNT_GUARDS)
            if operator is None:
                return None
            threshold = c.numeral()
            if threshold is None:
                return None
            if not postposed and not c.take("draft", ("فَأَنْشِئْ مُسَوَّدَةَ تَنْبِيهٍ", "فَأَعِدَّ مُسَوَّدَةَ تَنْبِيهٍ"), clause=True):
                return None
            if not c.take("prohibit_send", PROHIBIT, clause=True):
                return None
    if c.index != len(c.terms) or c.gap(c.index) not in (("", "؟", "?") if question else ("", ".")):
        return None
    frame = {"reference": "LATEST_REPORT", "counted": "DISTINCT_PENDING_REQUEST_IDS",
             "operator": operator, "threshold": threshold,
             "action": "LOCAL_DRAFT" if operator else "COUNT", "prohibited_action": "SEND_DRAFT" if operator else None}
    return {"witnesses_utf8": c.spans, "threshold": threshold, "frame": frame,
            "intent": "CONDITIONAL_DRAFT" if operator else "COUNT"}


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


# Independent worked judgments on one count unit. Equality separates the two
# operators even when their predictions agree on all below/above examples.
ORDER_FEATURES = FeatureSchema("report_threshold_order", "1", ("greater", "less"))
BOUNDARY_EXAMPLES = ((2, 1, False, False), (2, 2, False, True), (2, 3, True, True))


def order_case(label, limit, count):
    return ORDER_FEATURES.case(label, "1", {"greater": count > limit, "less": count < limit})


@lru_cache(maxsize=2)
def learned_comparison(operator):
    if operator not in COUNT_GUARDS:
        raise ValueError("Unknown report threshold comparison")
    session = LearningSession(GuardLanguage(ORDER_FEATURES, 1))
    curve = [len(session.survivors)]
    for limit, count, exceeds, reaches in BOUNDARY_EXAMPLES:
        case = order_case(str(count), limit, count)
        session = session.observe(Observation(str(count), "report-threshold.v1", case,
                                              exceeds if operator == "GT" else reaches))
        curve.append(len(session.survivors))
    return session, tuple(curve)



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
    operator = reading["frame"]["operator"]
    # For one count unit, count >= threshold iff threshold is not above count.
    # The persisted strict-comparison lesson remains usable for both surfaces.
    before, after = (threshold, count) if operator == "GT" else (count, threshold)
    learning = train_guard(before, after, lesson.get("prior_examples"))
    answer["learning"] = learning
    session, curve = learned_comparison(operator)
    prediction = list(session.predict(order_case("new", threshold, count)).possible)
    expected = count > threshold if operator == "GT" else count >= threshold
    answer["comparison"] = {"operator": operator, "count": count, "threshold": threshold,
                            "same_unit": "DISTINCT_PENDING_REQUEST_IDS",
                            "worked_examples": [[t, n, gt if operator == "GT" else ge]
                                                for t, n, gt, ge in BOUNDARY_EXAMPLES],
                            "survivor_counts": list(curve),
                            "learned_rules": [g.render(ORDER_FEATURES) for g in session.survivors],
                            "prediction": prediction, "strict_lesson_operands": [before, after]}
    strict = learning["result"]
    if (len(session.survivors) != 1 or prediction != [expected] or len(strict["candidate_rules"]) != 1
            or strict["prediction"] != [expected if operator == "GT" else not expected]):
        return dict(answer, status="DEFER_LEARNING", answer_ar="لم يتفق المتعلّم مع فحص العدد والشرط.")
    reason = (f"شرط التجاوز يتطلب عددًا أكبر من {threshold}." if operator == "GT"
              else f"شرط بلوغ الحدّ يتحقق عند {threshold} أو أكثر.")
    if not expected:
        return dict(answer, status="NO_DRAFT", answer_ar=f"{summary} {reason} لم يتحقق الشرط.")
    body = f"مسودة تنبيه — {report['id']}\n{summary}\nمعرّفات الطلبات: " + "، ".join(ids) + "\n"
    return dict(answer, status="DRAFT_PLANNED", draft_body=body,
                answer_ar=f"{summary} {reason} تحقق شرط إعداد المسودة.")


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
