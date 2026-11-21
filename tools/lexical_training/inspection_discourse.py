"""One bounded reported-state/conditional-instruction lesson in a replayable local world."""
import re

from . import inspection_roles as roles
from .report_draft import ID, InstructionCursor
from tools.grammar_catalog import valency

SCHEMA = "ntl.inspection-discourse.v1"
RESULT = "ntl.inspection-discourse-result.v1"
LAW = "inspection.discourse.local-episode.v1"
OBJECTS = valency.DOMAIN["opened_entity"]
REGISTERS = ("الْمُعَايَنَةِ", "الْفَحْصِ")
ACTIONS = {"draft": "فَأَنْشِئْ مُسَوَّدَةً", "record_opening": "فَسَجِّلِ الْفَتْحَ"}
TAILS = {"forbid_send": "وَلَا تُرْسِلْهَا", "forbid_delete": "وَلَا تَحْذِفْهَا",
         "forbid_draft": "وَلَا تُنْشِئْهَا", "request_send": "وَأَرْسِلْهَا"}


def select(cursor, slot, choices, *, clause=False):
    for value, forms in choices.items():
        if cursor.take(slot, forms, clause=clause):
            return value
    return None


def entity(cursor, slot, stems, ending):
    return select(cursor, slot, {roles.bare(s): (s + ending,) for s in stems})


def read(text):
    c = InstructionCursor(text)
    frame = {"report_verb": None, "report": None, "content": None, "condition": None, "action": None, "tail": None}
    segments = {}

    def segment(key, start):
        segments[key] = [start, c.index]

    report = select(c, "report_verb", {"أن": ("أَفَادَ", "ذَكَرَ", "أَخْبَرَ"), "إن": ("قَالَ",)})
    if report:
        person = entity(c, "reporter", valency.PEOPLE, "ُ")
        if not person or not c.take("complement", ("إِنَّ" if report == "إن" else "أَنَّ",)):
            return None
        segment("report", 0)
        frame["report_verb"] = roles.bare(c.terms[0]["surface"])
        frame["report"] = person
    start = c.index
    bearer = entity(c, "described", OBJECTS, "َ" if report else "ُ")
    if bearer:
        state = select(c, "state", {"open": ("مَفْتُوحٌ",), "closed": ("مُغْلَقٌ",)})
        if not state:
            return None
        frame["content"] = {"bearer": bearer, "state": state}
        segment("content", start)
    elif report:
        return None
    if c.index < len(c.terms):
        # A new, independently uttered instruction must be outside the reported clause.
        if bearer and c.gap(c.index) not in (".", "؛", ";"):
            return None
        start = c.index
        if not c.take("if", ("إِذَا", "إِنْ"), clause=True):
            return None
        if c.take("established", ("ثَبَتَ",)):
            if not bearer or not c.take("opening_reference", ("فَتْحُهُ",)):
                return None
            if not c.take("register_cue", ("فِي سِجِلِّ",)):
                return None
            register = select(c, "register", {roles.bare(r): (r,) for r in REGISTERS})
            if not register:
                return None
            condition = {"kind": "registered_opening", "bearer": bearer, "register": register}
        elif c.take("opened", ("فَتَحَ",)):
            actor = entity(c, "opener", valency.PEOPLE, "ُ")
            opened = entity(c, "opened_entity", OBJECTS, "َ")
            if not actor or not opened:
                return None
            condition = {"kind": "actor_opening", "bearer": opened, "actor": actor}
        else:
            return None
        condition["operator"] = roles.bare(c.terms[start]["surface"])
        frame["condition"] = condition
        segment("condition", start)
        start = c.index
        if c.gap(start) not in ("", "،", ","):
            return None
        action = select(c, "consequence", {
            "draft": (ACTIONS["draft"], "فَأَعِدَّ مُسَوَّدَةً", "فَحَرِّرْ مُسَوَّدَةً", "فَاكْتُبْ مُسَوَّدَةً"),
            "record_opening": (ACTIONS["record_opening"], "فَدَوِّنِ الْفَتْحَ")}, clause=True)
        if not action:
            return None
        frame["action"] = action
        segment("request", start)
        if c.index < len(c.terms):
            start = c.index
            # This profile binds the feminine pronoun only to the just-requested draft.
            if action != "draft" or c.gap(start) not in ("", "،", ","):
                return None
            tail = select(c, "coordination", {k: (v,) for k, v in TAILS.items()}, clause=True)
            if not tail:
                return None
            frame["tail"] = tail
            segment("tail", start)
    if not (frame["content"] or frame["condition"]) or c.index != len(c.terms) or c.gap(c.index) not in ("", "."):
        return None
    return {"frame": frame, "witnesses_utf8": c.spans, "term_segments": segments}


def realize(frame):
    parts = []
    if frame["report"]:
        verb = frame["report_verb"]
        parts.append(verb + " " + frame["report"] + (" إن" if verb == "قال" else " أن"))
    content = frame["content"]
    if content:
        parts.append(content["bearer"] + (" مفتوح." if content["state"] == "open" else " مغلق."))
    condition = frame["condition"]
    if condition:
        if condition["kind"] == "registered_opening":
            parts.append(condition["operator"] + " ثبت فتحه في سجل " + condition["register"])
        else:
            parts.append(condition["operator"] + " فتح " + condition["actor"] + " " + condition["bearer"])
        parts.append(roles.bare(ACTIONS[frame["action"]]))
        if frame["tail"]:
            parts[-1] += "،"
            parts.append(roles.bare(TAILS[frame["tail"]]))
        parts[-1] += "."
    return " ".join(parts)


def keys(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError("Unexpected episode fields")


def identifier(value):
    if type(value) is not str or not ID.fullmatch(value):
        raise ValueError("Invalid episode identifier")


def validate(lesson):
    required = {"schema", "text", "scene_id", "objects", "steps"}
    if isinstance(lesson, dict) and "question" in lesson:
        required.add("question")
        if type(lesson["question"]) is not str or not (0 < len(lesson["question"].encode()) <= 256):
            raise ValueError("Invalid question")
    keys(lesson, required)
    if lesson["schema"] != SCHEMA or type(lesson["text"]) is not str or not (0 < len(lesson["text"].encode()) <= 2048):
        raise ValueError("Invalid source")
    identifier(lesson["scene_id"])
    objects = lesson["objects"]
    if type(objects) is not dict or len(objects) > 16:
        raise ValueError("Invalid scene inventory")
    for name, form in objects.items():
        identifier(name)
        if form not in tuple(roles.bare(s) for s in OBJECTS):
            raise ValueError("Unsupported object form")
    if type(lesson["steps"]) is not list or len(lesson["steps"]) > 24:
        raise ValueError("Invalid episode length")
    seen, active = set(), set()
    for step in lesson["steps"]:
        if type(step) is not dict:
            raise ValueError("Invalid step")
        op = step.get("op")
        if op == "observe":
            keys(step, ("op", "id", "scene_id", "source", "object_id", "actor", "kind", "polarity"))
            for field in ("id", "scene_id", "object_id", "source"):
                identifier(step[field])
            if step["actor"] is not None:
                identifier(step["actor"])
            if step["kind"] not in ("opening", "open_state") or step["polarity"] not in ("affirm", "deny"):
                raise ValueError("Invalid observation")
            if step["id"] in seen:
                raise ValueError("Observation identity reused")
            seen.add(step["id"])
            active.add(step["id"])
        elif op == "withdraw":
            keys(step, ("op", "id"))
            identifier(step["id"])
            if step["id"] not in active:
                raise ValueError("Withdrawal has no active source")
            active.remove(step["id"])
        elif op == "attempt":
            keys(step, ("op",))
        else:
            raise ValueError("Unsupported step")


def assess(condition, lesson, evidence):
    matches = sorted(key for key, form in lesson["objects"].items() if form == condition["bearer"])
    if len(matches) != 1:
        return {"status": "UNRESOLVED_REFERENCE", "candidates": matches, "witness_ids": []}
    source = condition.get("register", "المعاينة")
    relevant = [e for e in evidence.values() if e["scene_id"] == lesson["scene_id"]
                and e["object_id"] == matches[0] and e["source"] == source and e["kind"] == "opening"
                and ("actor" not in condition or e["actor"] == condition["actor"])]
    polarities = {e["polarity"] for e in relevant}
    status = {frozenset(): "MISSING", frozenset(["affirm"]): "SUPPORTED",
              frozenset(["deny"]): "DENIED", frozenset(["affirm", "deny"]): "CONFLICT"}[frozenset(polarities)]
    return {"status": status, "kind": "opening", "scene_id": lesson["scene_id"],
            "actor_required": condition.get("actor"), "object_id": matches[0], "source": source, "witness_ids": [e["id"] for e in relevant]}


def answers(frame, lesson, active, artifacts):
    condition = frame["condition"]
    support = assess(condition, lesson, active) if condition else {"status": "NOT_ASKED", "witness_ids": []}
    primary, tail = frame["action"], frame["tail"]
    allowed = []
    reason = support["status"]
    if primary == "draft" and tail == "forbid_draft":
        reason = "CONFLICTING_DIRECTIVES"
    elif primary and reason == "SUPPORTED":
        allowed = [primary]
    questions = {"MISSING": "ما قيد المعاينة الذي يشهد بحادثة الفتح المعينة؟",
                 "CONFLICT": "كيف نرجح بين قيدي المعاينة المتعارضين؟",
                 "UNRESOLVED_REFERENCE": "أي حامل بعينه تقصد؟",
                 "CONFLICTING_DIRECTIVES": "هل المطلوب إنشاء المسودة أم الامتناع عن إنشائها؟"}
    return {"reported": {"source": frame["report"], "content": frame["content"],
                         "force": "assert"} if frame["content"] else None,
            "inspection": support,
            "requested": {"source": "CURRENT_SPEAKER", "condition": condition, "then": primary, "tail": tail} if condition else None,
            "permitted": {"local": allowed, "send": "PROHIBITED" if tail == "forbid_send" else "NO_EXECUTOR",
                          "basis": reason, "question": questions.get(reason)},
            "performed": list(artifacts.values())}


QUESTIONS = {"ماذا أفاد القائل": "reported", "ما الذي ثبت في السجل": "inspection",
             "ماذا طلب المتكلم": "requested", "ماذا يجوز فعله الآن": "permitted",
             "ماذا فعلت الماكينة بالفعل": "performed"}
LOCAL_ACTIONS = {"draft": "إنشاء مسودة", "record_opening": "تسجيل الفتح"}
TAIL_AR = {"forbid_send": "ونهى عن إرسالها", "forbid_delete": "ونهى عن حذفها",
           "request_send": "وطلب إرسالها", "forbid_draft": "ونهى عن إنشائها"}


def present(result, lesson):
    answers = result["answers"]
    report, inspection, requested = answers["reported"], answers["inspection"], answers["requested"]
    permission, effects = answers["permitted"], answers["performed"]
    said = "لم يتعين خبر منسوب إلى قائل في القراءة."
    if report:
        content = report["content"]
        state = "مفتوح" if content["state"] == "open" else "مغلق"
        attribution = ("أفاد " + report["source"] + " أن ") if report["source"] else "ورد في النص أن "
        said = attribution + content["bearer"] + " " + state + "."
    register = {"NOT_ASKED": "لا تتضمن القراءة شرط معاينة.", "UNRESOLVED_QUESTION": "لم يتعين شرط المعاينة.",
                "UNRESOLVED_REFERENCE": "لم يتعين أي جسم يقصده الشرط.",
                "MISSING": "لا يوجد قيد مطابق يشهد بالفتح المطلوب في هذه المعاينة.",
                "DENIED": "ورد قيد ينفي حادثة الفتح المطلوبة.", "CONFLICT": "تعارض قيدان بشأن الفتح المطلوب.",
                "SUPPORTED": "يؤيد السجل حادثة الفتح المطلوبة."}[inspection["status"]]
    if inspection.get("witness_ids"):
        register += " الشاهد " + "، ".join(inspection["witness_ids"]) + "."
    order = "لم يتعين طلب قابل للقراءة في هذا النطاق."
    if requested:
        condition = requested["condition"]
        if condition["kind"] == "actor_opening":
            clause = condition["operator"] + " فتح " + condition["actor"] + " " + condition["bearer"]
        else:
            clause = condition["operator"] + " ثبت فتح " + condition["bearer"] + " في سجل " + condition["register"]
        order = "طلب المتكلم " + LOCAL_ACTIONS[requested["then"]] + " " + clause
        order += ("، " + TAIL_AR[requested["tail"]] if requested["tail"] else "") + "."
    may = ("يجوز داخل المحاكاة " + LOCAL_ACTIONS[permission["local"][0]] + "."
           if permission["local"] else "لا يوجد فعل مأذون به الآن في هذه المحاكاة.")
    if permission.get("question"):
        may += " " + permission["question"]
    if permission["send"] == "PROHIBITED":
        may += " الإرسال منهي عنه."
    elif requested and requested["tail"] == "request_send":
        may += " طلب الإرسال مفهوم، وصلاحية الإرسال غير متاحة."
    did = "لم تنفذ الماكينة فعلًا في المحاكاة."
    if effects:
        did = "الأثر المحفوظ داخل المحاكاة هو «" + effects[0]["body"] + "»."
    replies = {"reported": said, "inspection": register, "requested": order, "permitted": may, "performed": did}
    result["arabic_answers"] = replies
    if "question" in lesson:
        query = roles.bare(lesson["question"]).strip().rstrip("؟?").strip()
        key = QUESTIONS.get(query)
        person = next((roles.bare(p) for p in valency.PEOPLE if query == "ماذا أفاد " + roles.bare(p)), None)
        answer = None
        if person:
            key = "reported"
            if not report or report["source"] != person:
                answer = "لم تنسب القراءة خبرًا إلى " + person + ". " + said
        result["question_answer"] = {"slot": key, "text": answer or replies.get(key, "لم يتعين المطلوب من هذا السؤال.")}
    return result


def run(lesson):
    validate(lesson)
    text = lesson["text"]
    reading = read(text)
    try:
        proposal = roles.propose(text)
    except (OSError, ValueError, KeyError):
        proposal = {"authority": "NONE", "status": "MODEL_UNAVAILABLE"}
    result = {"schema": RESULT, "law": LAW, "request": lesson, "execution_measured": True,
              "scope": "LOCAL_SIMULATED_EPISODE", "role_proposal": proposal}
    if reading is None:
        # Keep a separately completed report even if a later instruction is outside the grammar.
        boundary = re.search(r"[.؛;]", text)
        first = read(text[:boundary.start()]) if boundary else None
        report = None
        if first and first["frame"]["report"] and first["frame"]["condition"] is None:
            report = answers(first["frame"], lesson, {}, {})["reported"]
        partial = {"reported": report, "inspection": {"status": "UNRESOLVED_QUESTION"},
                   "requested": None, "permitted": {"local": [], "send": "NO_EXECUTOR",
                   "basis": "DEFER_READING", "question": "ما حدود الشرط والطلب في هذه الصيغة؟"},
                   "performed": []}
        return present(dict(result, status="DEFER_READING", answers=partial,
                            report_witnesses_utf8=first["witnesses_utf8"] if report else {}), lesson)
    frame = reading["frame"]
    if "roles" in proposal:
        differences = []
        for slot, (left, right) in reading["term_segments"].items():
            expected = slot
            if slot == "tail":
                expected = "request" if frame["tail"] == "request_send" else "prohibit"
            differences.extend(i for i in range(left, right) if proposal["roles"][i] != expected)
        proposal["disagreement_term_indices"] = differences
    canonical = realize(frame)
    replay = read(canonical)
    if replay is None or replay["frame"] != frame:
        raise ValueError("Canonical frame does not replay")
    active, artifacts = {}, {}
    current = answers(frame, lesson, active, artifacts)
    history = [current]
    for step in lesson["steps"]:
        if step["op"] == "observe":
            active[step["id"]] = step
        elif step["op"] == "withdraw":
            del active[step["id"]]
        elif current["permitted"]["local"]:
            action = frame["action"]
            if action not in artifacts:
                # Each episode has one instruction. Store the actual local effect once.
                support = current["inspection"]
                artifacts[action] = {"action": action, "scene_id": lesson["scene_id"],
                                     "object_id": support["object_id"], "witness_ids": support["witness_ids"],
                                     "body": ("مسودة معاينة" if action == "draft" else "قيد فتح") + " " + support["object_id"]}
        current = answers(frame, lesson, active, artifacts)
        history.append(current)
    return present(dict(result, status="READ", reading=reading, canonical_text=canonical,
                        answers=current, history=history), lesson)
