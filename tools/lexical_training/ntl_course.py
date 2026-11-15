"""Public worksheets, owner-graded submissions and replayable NTL portfolios."""
import json

from nabt.learning.finite_guard import FeatureSchema, GuardLanguage, LearningSession, Observation
from tools import evidence_lifecycle_v1 as wire
from tools.grammar_catalog import interpretation_chains as records, scoped_composition
from . import ntl_curriculum as ntl

SCHEMA = "ntl.course-session.v1"
RESULT = "ntl.course-result.v1"
CASES = ntl.FRAMEWORK.with_name("ntl_cases_v1.json")
LANES = (*ntl.DOMAINS, "bridge")
BRIDGE_FEATURES = FeatureSchema("ntl_record_application", "1", ("endpoints_aligned", "program_agrees"))
PHASES = {"صلب": 0, "سائل": 1, "غاز": 2}
PHASE_PROGRAMS = {"different": lambda a, b: a != b, "always_changed": lambda a, b: True}
PROGRAM_TEXT = {
    "signed_delta": "return after - before", "magnitude": "return abs(after - before)",
    "different": "return before != after", "always_changed": "return True",
}
BRIDGE_REASONS = {
    "aligned_and_matches": "الرصدان يطابقان المدخلين والتنفيذ يوافق المواصفة على الحالة.",
    "implementation_disagrees": "الرصدان متطابقان مع المدخلين لكن خرج التنفيذ يخالف المواصفة.",
    "missing_endpoint": "ينقص رصد أحد الطرفين.",
    "observations_conflict": "تعارضت الأرصاد في أحد الطرفين.",
    "inputs_mismatch": "القيم المرصودة تخالف المدخلات المفترضة.",
}
PROMPTS = {
    "linguistic": "ما القيمة التي نسبها نص الخبر إلى المخبر عن اليوم الأخير؟",
    "physical": "هل تطابق أرصاد هذين اليومين مدخلي التمرين، في الوحدة نفسها؟",
    "formal": {"count": "ما قيمة العدد الأخير ناقص العدد الأول في التمرين؟",
               "phase": "هل اختلف رمزا الطورين في التمرين؟"},
    "programming": "هل يُرجع التنفيذ المعروض القيمة المطلوبة في المواصفة على هذين المدخلين؟",
    "bridge": "هل يصح تطبيق خرج التنفيذ على طرفي هذا السجل؟ اختر السبب وحدد أرقام جميع سطور الرصد المتاحة للمحور والوحدة واليومين، بما فيها الشواهد المتعارضة.",
}
FEEDBACK = {
    "linguistic": "ارجع إلى فعل الإخبار، وعيّن القائل واليوم والقيمة المذكورة.",
    "physical": "قابل المدخلين بأرصاد العينة. افحص الزمن والوحدة وتعدد القيم.",
    "formal": "أعِد الحساب أو المقارنة من مدخلي التمرين حسب تعريف العملية.",
    "programming": "تتبّع خرج التنفيذ، ثم قارنه بالمرجع على المدخلين نفسيهما.",
    "bridge": "افحص تطابق الأرصاد أولًا، ثم موافقة التنفيذ للمرجع، وعيّن سطور الرصد المعنيّة.",
}


def catalog():
    return {c["id"]: c for c in json.loads(CASES.read_text(encoding="utf-8"))}


def prompts(case, lanes):
    questions = {lane: PROMPTS["formal"][case["family"]] if lane == "formal" else PROMPTS[lane]
                 for lane in lanes}
    sheet = {"case": case["id"], "family": case["family"], "stage": case["stage"],
             "questions": questions}
    if any(k in lanes for k in ("linguistic", "physical", "bridge")):
        sheet["source_lines"] = case["record"].splitlines()
    if any(k != "linguistic" for k in lanes):
        sheet["exercise"] = case["exercise"]
    if "linguistic" in lanes:
        sheet["report_day"] = case["exercise"]["last_day"]
    if any(k in lanes for k in ("formal", "programming", "bridge")):
        sheet["specification"] = PROMPTS["formal"][case["family"]]
        if case["family"] == "phase":
            sheet["phase_symbols"] = PHASES
    if any(k in lanes for k in ("programming", "bridge")):
        sheet["program"] = PROGRAM_TEXT[case["implementation"]]
    if "physical" in lanes:
        sheet["observation_options"] = {"ALIGNED": "تطابق", "MISMATCH": "عدم تطابق",
                                          "OPEN": "رصد ناقص", "CONFLICT": "أرصاد متعارضة"}
    if "bridge" in lanes:
        sheet["reasons"] = BRIDGE_REASONS
        sheet["line_numbering_starts_at"] = 1
    return sheet


def phase_result(case):
    ex = case["exercise"]
    source = records.analyze(case["record"])
    readings, status, claims, checks = ntl.attributed_reading(source, ex, "الطور")
    empirical, row = ntl.observation_status(source, ex, "الطور")
    before, after = ex["before"], ex["after"]
    # Nominal identifiers only. Equality is invariant under an injective relabelling.
    expr = f"{PHASES[before]}={PHASES[after]}"
    maths = scoped_composition.evaluate({"schema": scoped_composition.SCHEMA,
                                         "profile": "arithmetic", "text": expr})
    checked = maths["chain_complete"] and maths["status"] == "COMPUTED" and (
        maths["native_check"] or {}).get("native_checked")
    prop = maths["projection"]["result"] if checked else {}
    changed = not prop["truth"] if prop.get("sort") == "proposition" and type(prop.get("truth")) is bool else None
    output = PHASE_PROGRAMS[case["implementation"]](before, after)
    agrees = None if changed is None else changed == output
    cards = {
        "linguistic": {"status": status, "answer": readings[0] if len(readings) == 1 else None,
                       "readings": readings, "witness_ids": claims},
        "physical": {"status": empirical, "answer": empirical if empirical in
                     ("ALIGNED", "MISMATCH", "OPEN", "CONFLICT") else None, "comparison": row},
        "formal": {"status": maths["status"], "answer": changed, "equality_expression": expr},
        "programming": {"status": "UNVERIFIED" if agrees is None else
                        "MATCH_ON_CASE" if agrees else "COUNTEREXAMPLE",
                        "answer": agrees, "output": output, "implementation": case["implementation"]},
    }
    return {"cards": cards, "owners": {"record": source, "arithmetic": maths},
            "reported_value_checks": checks}


def evidence(case):
    if case["family"] == "phase":
        return phase_result(case)
    return ntl.run({"schema": ntl.SCHEMA, "lesson_id": case["id"], "record": case["record"],
                    "exercise": case["exercise"], "implementation": case["implementation"], "examples": []})


def bridge_answer(case, report):
    ex = case["exercise"]
    state = report["cards"]["physical"]["answer"]
    match = report["cards"]["programming"]["answer"]
    if state == "ALIGNED" and match is not None:
        reason = "aligned_and_matches" if match else "implementation_disagrees"
    else:
        reason = {"OPEN": "missing_endpoint", "CONFLICT": "observations_conflict",
                  "MISMATCH": "inputs_mismatch"}.get(state)
    if reason is None:
        return None
    axis = "العدد" if case["family"] == "count" else "الطور"
    raw = case["record"].encode()
    lines = []
    for entry in report["owners"]["record"].get("records", []):
        if (entry["kind"] == "observation" and entry["axis"] == axis and entry["unit"] == ex["unit"]
                and entry["day"] in (ex["first_day"], ex["last_day"])):
            start = entry["witness"]["utf8_span"][0]
            lines.append(1 + raw[:start].count(b"\n"))
    return {"reason": reason, "lines": sorted(lines)}


def validate_answers(answers, lanes, case):
    if not isinstance(answers, dict) or not set(answers) <= set(lanes):
        raise ValueError("Answer outside selected focus")
    for lane, value in answers.items():
        if lane == "bridge":
            wire._fields(value, ("reason", "lines"), "bridge answer")
            lines = value["lines"]
            if (value["reason"] not in BRIDGE_REASONS or type(lines) is not list or
                    not all(type(n) is int and 1 <= n <= len(case["record"].splitlines()) for n in lines)
                    or len(set(lines)) != len(lines)):
                raise ValueError("Expected a bridge reason and distinct source lines")
        elif lane == "physical":
            if value not in ("ALIGNED", "MISMATCH", "OPEN", "CONFLICT"):
                raise ValueError("Unknown observation decision")
        elif lane == "linguistic" and case["family"] == "phase":
            if value not in PHASES:
                raise ValueError("Expected a phase label")
        elif lane == "programming" or (lane == "formal" and case["family"] == "phase"):
            if type(value) is not bool:
                raise ValueError("Expected a Boolean answer")
        else:
            ntl.integer(value, lane, minimum=-999999 if lane == "formal" else 0)


def grade(answers, reference, lanes):
    grades = {}
    for lane in lanes:
        gold = reference[lane]
        value = answers.get(lane)
        if lane == "bridge" and value is not None:
            value = dict(value, lines=sorted(value["lines"]))
        status = ("UNANSWERED" if value is None else "UNGRADABLE" if gold is None else
                  "CORRECT" if value == gold else "REVISE")
        grades[lane] = {"status": status}
        if status == "REVISE":
            grades[lane]["feedback"] = FEEDBACK[lane]
    return grades


def induce(lesson, cases):
    """Learn permission to apply a computed result to the record from labelled examples."""
    wire._fields(lesson, ("schema", "action", "focus", "examples", "probes"), "induction")
    if lesson["focus"] != "bridge":
        raise ValueError("Rule induction currently covers the application bridge")
    examples, probes = lesson["examples"], lesson["probes"]
    for ids in (examples, probes):
        if (type(ids) is not list or len(ids) > len(cases) or len(set(ids)) != len(ids)
                or not set(ids) <= cases.keys()):
            raise ValueError("Expected distinct installed case ids")
    if not probes or set(examples) & set(probes):
        raise ValueError("Probe cases must be disjoint from demonstrations")
    session = LearningSession(GuardLanguage(BRIDGE_FEATURES, 2))
    curve = [len(session.survivors)]
    trace, predictions = {}, {}
    training_patterns = set()
    for cid in [*examples, *probes]:
        case = cases[cid]
        verified = evidence(case)
        aligned = verified["cards"]["physical"]["answer"]
        agrees = verified["cards"]["programming"]["answer"]
        values = {"endpoints_aligned": None if aligned is None else aligned == "ALIGNED",
                  "program_agrees": agrees}
        example = BRIDGE_FEATURES.case(cid, "1", values)
        gold = bridge_answer(case, verified)
        if cid in examples:
            if gold is None or None in values.values():
                trace[cid] = {"status": "UNGRADABLE"}
            else:
                training_patterns.add((values["endpoints_aligned"], values["program_agrees"]))
                label = gold["reason"] == "aligned_and_matches"
                session = session.observe(Observation(cid, "ntl_examples", example, label))
                trace[cid] = {"status": "TAUGHT", "features": values, "label": label, "evidence": gold}
            curve.append(len(session.survivors))
        else:
            pred = session.predict(example)
            possible = list(pred.possible)
            truth = None if gold is None else gold["reason"] == "aligned_and_matches"
            verdict = ("UNGRADABLE" if truth is None or None in values.values() else
                       "UNDECIDED" if len(possible) != 1 else
                       "CORRECT" if possible == [truth] else "REVISE")
            predictions[cid] = {"features": values, "possible": possible, "assessment": verdict,
                                "feature_pattern_seen": (values["endpoints_aligned"], values["program_agrees"]) in training_patterns}
    return {"schema": RESULT, "status": "COURSE_SESSION", "action": "induce", "focus": "bridge",
            "execution_measured": True, "candidate_counts": curve, "examples": trace,
            "surviving_rules": [g.render(BRIDGE_FEATURES) for g in session.survivors],
            "probes": predictions, "scope": "FIXED_TWO_BOOLEAN_FEATURES"}


def run(lesson):
    wire._encoded(lesson, wire.MAX_REQUEST_BYTES)
    action = lesson.get("action")
    if action == "induce":
        return induce(lesson, catalog())
    common = {"schema", "action", "focus"}
    wire._fields(lesson, common | ({"submissions"} if action == "assess" else {"cases"}), "course")
    focus = lesson["focus"]
    if action not in ("worksheet", "teach", "assess") or focus not in (*LANES, "integrated"):
        raise ValueError("Unknown course action or focus")
    lanes = LANES if focus == "integrated" else (focus,)
    cases = catalog()
    selection = lesson["submissions"] if action == "assess" else lesson["cases"]
    if type(selection) is not (dict if action == "assess" else list):
        raise ValueError("Expected a case-to-answers map or a list of case ids")
    if not selection or len(selection) > len(cases) or len(set(selection)) != len(selection) or not set(selection) <= cases.keys():
        raise ValueError("Select distinct installed case ids")
    if action == "assess":
        for cid, answers in selection.items():
            validate_answers(answers, lanes, cases[cid])
    entries = {}
    for cid in selection:
        case = cases[cid]
        sheet = prompts(case, lanes)
        if action != "worksheet":
            report = evidence(case)
            reference = {lane: report["cards"][lane]["answer"] for lane in ntl.DOMAINS}
            reference["bridge"] = bridge_answer(case, report)
            if action == "assess":
                sheet["grades"] = grade(selection[cid], reference, lanes)
            else:
                sheet["solution"] = {lane: reference[lane] for lane in lanes}
                sheet["domain_trace"] = {lane: report["cards"][lane] for lane in lanes if lane != "bridge"}
                sheet["evidence"] = report["owners"]
                if focus in ("integrated", "bridge"):
                    sheet["report_checks"] = (report["reported_value_checks"] if case["family"] == "phase"
                                              else report["bridges"]["linguistic_to_physical"]["claims"])
        entries[cid] = sheet
    result = {"schema": RESULT, "status": "COURSE_SESSION", "action": action, "focus": focus,
              "execution_measured": True, "cases": entries}
    if action == "assess":
        result["progress"] = progress(cases, entries, lanes)
    return result


def progress(cases, entries, lanes):
    transfer = [cid for cid, case in cases.items() if case["stage"] == "transfer"]
    summary = {}
    for lane in lanes:
        correct = [cid for cid in transfer if cid in entries and
                   entries[cid]["grades"][lane]["status"] == "CORRECT"]
        remaining = [cid for cid in transfer if cid not in correct]
        summary[lane] = {"correct_transfer_cases": correct, "required_transfer_cases": len(transfer),
                         "demonstrated_on_bank": not remaining,
                         "next_practice": remaining[0] if remaining else None}
    return summary
