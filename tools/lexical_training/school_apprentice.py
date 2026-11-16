"""A bounded school inquiry lesson using installed NTL owners and a neural proposal.

No learned score grants an evidence premise, an official grade, access permission,
or authority to update a learner record. External clients use cognitive.lesson
through the existing gateway, retaining their original request for replay.
"""
from copy import deepcopy
from hashlib import sha256
import math

from tools import evidence_lifecycle_v1 as wire
from . import ntl_core as core, school_curriculum as curriculum

SCHEMA = "ntl.school-apprentice.v1"
RESULT = "ntl.school-apprentice-result.v1"
UNITS = ("measurement", "experiment", "passage", "reflection")
MAX_REQUEST_BYTES = 96 * 1024
NEURAL_RELEASE_POLICY = "REVIEW_ONLY"
METHODS = {
    "request_evidence": ("استكمال المشاهدة", "تحديد المعلومة الناقصة ومصدر الحصول عليها"),
    "compare_measurements": ("المقارنة", "فترات القياس المغلقة بعد توحيد الوحدات"),
    "inspect_causal_design": ("فحص الاستدلال السببي", "تصميم المقارنة واختبار العشوائية الدقيق للأزواج"),
    "inspect_source": ("نقد المصدر", "تعيين النص ومقدماته وحدود ما يسنده"),
    "compare_perspectives": ("مقارنة المنظورات", "سجل المنظورات ومبرراتها وأسئلة TOK المحلية"),
    "seek_counterexample": ("اختبار الحكم", "البحث عن حالة مخالفة أو تفسير بديل"),
    "independent_transfer": ("النقل والتأمل", "مسألة مستقلة لم تستخدم في التدريب أو المثال المحلول"),
}
PROMPTS = {
    "request_evidence": "ما الدليل الناقص؟ حدّد مصدره قبل أن تصدر الحكم.",
    "compare_measurements": "قارن فترتي القياس ووحدتيهما وهوية الشيء المقاس، ثم قيّد استنتاجك بالدقة المتاحة.",
    "inspect_causal_design": "كيف وُزّعت المعالجة؟ ما المقارنة وما النتيجة المحددة سلفًا؟ افصل الفرق المرصود عن تفسير سببه.",
    "inspect_source": "أي نص أو شاهد يسند الدعوى؟ ميّز بين قول المصدر وثبوت الأمر في الواقع.",
    "compare_perspectives": "اعرض منظورين ومبرر كل منهما. ما الذي قد يغيّر ترجيحك؟",
    "seek_counterexample": "اقترح حالة قد تنقض تعميمك أو تفسيرًا بديلًا، وبيّن كيف يمكن اختباره.",
    "independent_transfer": "اختبر الفكرة في مسألة جديدة مستقلة، ثم اشرح حدود انتقال الحكم إليها.",
}


def _nullable_text(value, label, limit):
    if value is not None:
        wire._text(value, label, limit, content=True)


def _integer(value, lower, upper, label):
    if value is not None and (type(value) is not int or not lower <= value <= upper):
        raise ValueError("Invalid " + label)


def _response(value):
    if value is None:
        return
    wire._fields(value, ("origin", "decision", "evidence_refs", "explanation", "counterexample",
                         "reflection", "transfer"), "learner response")
    if value["origin"] not in ("human_reported", "simulation"):
        raise ValueError("Declare response origin; it is not authenticated by the role field")
    _nullable_text(value["decision"], "response decision", 192)
    refs = value["evidence_refs"]
    if type(refs) is not list or len(refs) > 64:
        raise ValueError("Too many evidence references")
    for ref in refs:
        wire._text(ref, "evidence reference", 2048, content=True)
    if len(set(refs)) != len(refs):
        raise ValueError("Duplicate evidence reference")
    for key in ("explanation", "counterexample", "reflection", "transfer"):
        if type(value[key]) is not str or len(value[key].encode()) > 4096:
            raise ValueError("Response text must fit the UTF-8 budget")


def _validate_task(unit, task):
    """Validate types and collect missing premises; do not duplicate owner inference."""
    missing = []
    if unit == "measurement":
        wire._fields(task, ("readings",), "measurement task")
        rows = task["readings"]
        if type(rows) is not list or len(rows) > 2:
            raise ValueError("Expected at most two ordered length readings")
        if len(rows) < 2:
            missing.append("complete_observation")
        for row in rows:
            wire._fields(row, ("object", "day", "unit", "value", "error"), "reading")
            _nullable_text(row["object"], "object identity", 96)
            if row["object"] is None:
                missing.append("identity")
            for field, upper in (("day", 9999), ("value", 999999), ("error", 999999)):
                _integer(row[field], 0, upper, field)
                if row[field] is None:
                    missing.append("precision" if field == "error" else
                                   "time_and_unit" if field == "day" else "complete_observation")
            if row["unit"] is None:
                missing.append("time_and_unit")
            elif type(row["unit"]) is not str or row["unit"] not in core.SCALES:
                raise ValueError("Unsupported length unit")
            if row["value"] is not None and row["error"] is not None and row["error"] > row["value"]:
                raise ValueError("Measurement uncertainty exceeds the recorded value")
    elif unit == "experiment":
        wire._fields(task, ("assignment", "intervention", "control", "endpoint", "outcome_unit", "pairs"), "paired trial")
        if task["assignment"] is None:
            missing.append("causal_design")
        elif task["assignment"] not in ("fair_independent_within_pair", "observer_selected", "unreported"):
            raise ValueError("Unknown assignment design")
        for key in ("intervention", "control", "endpoint", "outcome_unit"):
            _nullable_text(task[key], key, 96 if key == "outcome_unit" else 192)
            if task[key] is None:
                missing.append("time_and_unit" if key == "outcome_unit" else "causal_design")
        rows = task["pairs"]
        if type(rows) is not list or len(rows) > 10:
            raise ValueError("Expected at most ten experimental pairs")
        if not rows:
            missing.append("complete_observation")
        seen = set()
        for row in rows:
            wire._fields(row, ("ids", "treated", "values"), "experimental pair")
            if (type(row["ids"]) is not list or len(row["ids"]) != 2
                    or type(row["values"]) is not list or len(row["values"]) != 2):
                raise ValueError("Each pair needs two identities and outcome slots")
            for identifier in row["ids"]:
                _nullable_text(identifier, "experimental unit identity", 48)
                if identifier is None:
                    missing.append("identity")
                elif identifier in seen:
                    raise ValueError("An experimental unit cannot occur twice")
                else:
                    seen.add(identifier)
            _integer(row["treated"], 0, 1, "treated index")
            if row["treated"] is None:
                missing.append("causal_design")
            for value in row["values"]:
                _integer(value, -999999, 999999, "outcome")
                if value is None:
                    missing.append("complete_observation")
    elif unit == "passage":
        wire._fields(task, ("text", "query"), "source passage")
        for key, limit in (("text", 2048), ("query", 192)):
            _nullable_text(task[key], key, limit)
            if task[key] is None:
                missing.append("source_support" if key == "text" else "scope")
    else:
        wire._fields(task, ("question", "sources", "perspectives"), "open reflection")
        wire._text(task["question"], "reflection question", 1024, content=True)
        if type(task["sources"]) is not list or len(task["sources"]) > 8:
            raise ValueError("Expected at most eight source records")
        seen = set()
        for source in task["sources"]:
            wire._fields(source, ("id", "text", "citation"), "reflection source")
            for key, limit in (("id", 96), ("text", 4096), ("citation", 1024)):
                wire._text(source[key], key, limit, content=True)
            if source["id"] in seen:
                raise ValueError("Duplicate reflection source identity")
            seen.add(source["id"])
        if type(task["perspectives"]) is not list or len(task["perspectives"]) > 8:
            raise ValueError("Expected at most eight perspective records")
        for perspective in task["perspectives"]:
            wire._text(perspective, "perspective", 1024, content=True)
        if len(set(task["perspectives"])) != len(task["perspectives"]):
            raise ValueError("Repeated text is not a second perspective record")
        if not task["sources"]:
            missing.append("source_support")
        if len(task["perspectives"]) < 2:
            missing.append("perspectives")
    return sorted(set(missing))


def _problem(value):
    wire._fields(value, ("case_id", "revision", "unit", "text", "task", "response"), "school inquiry")
    wire._text(value["case_id"], "case identity", 128)
    if type(value["revision"]) is not int or not 0 <= value["revision"] <= 9999:
        raise ValueError("Invalid evidence revision")
    if type(value["unit"]) is not str or value["unit"] not in UNITS:
        raise ValueError("No installed school owner for this domain")
    wire._text(value["text"], "learner inquiry", 2048, content=True)
    _response(value["response"])
    return _validate_task(value["unit"], value["task"])


def _eligible(unit, missing, owner):
    if missing:
        return ["request_evidence"]
    answer = None if owner is None else owner.get("answer")
    if unit == "reflection":
        return ["compare_perspectives", "inspect_source", "seek_counterexample"]
    if answer is None:
        return ["request_evidence"]
    decision = answer["decision"]
    if decision in ("UNALIGNED", "MISSING_READING", "MISSING_OUTCOME", "UNDEFINED_COMPARISON"):
        return ["request_evidence"]
    if unit == "measurement":
        return ["compare_measurements", "request_evidence"] if decision == "UNRESOLVED_PRECISION" else [
            "compare_measurements", "seek_counterexample", "independent_transfer"]
    if unit == "experiment":
        return ["inspect_causal_design", "request_evidence"] if decision == "DESIGN_INSUFFICIENT" else [
            "inspect_causal_design", "seek_counterexample", "independent_transfer"]
    return ["inspect_source", "seek_counterexample", "independent_transfer"] if decision in ("SUPPORTED", "REFUTED") else [
        "inspect_source", "request_evidence", "seek_counterexample"]


def _formative(response, owner):
    answer = None if owner is None else owner.get("answer")
    base = {"official_grade": None, "human_learning_measured": False,
            "semantic_quality_of_explanation": "HUMAN_REVIEW_REQUIRED",
            "scope": "local response observations, not an IB criterion level or national mark"}
    if response is None:
        return {**base, "status": "UNANSWERED", "observations": {}}
    return {**base, "status": "RESPONSE_RECORDED", "origin": response["origin"],
            "identity_authenticated": False, "observations": {
                "decision_matches_owner": None if answer is None or response["decision"] is None else
                    response["decision"] == answer["decision"],
                "references_match_owner": None if answer is None else
                    set(response["evidence_refs"]) == set(answer["witnesses"]),
                "missing_expected_refs": [] if answer is None else
                    sorted(set(answer["witnesses"]) - set(response["evidence_refs"])),
                "unrecognized_refs": [] if answer is None else
                    sorted(set(response["evidence_refs"]) - set(answer["witnesses"])),
                **{"has_" + field: bool(response[field].strip()) for field in (
                    "explanation", "counterexample", "reflection", "transfer")}}}


def _explain(unit, owner, missing):
    if missing:
        return {"claim": None, "evidence_refs": [], "basis": "MISSING_PREMISES",
                "open_obligations": missing, "world_truth_established": False}
    if owner is None:
        return {"claim": None, "evidence_refs": [], "basis": "OPEN_REFLECTION",
                "open_obligations": ["source_reliability", "argument_quality", "teacher_review"],
                "world_truth_established": False}
    answer = owner.get("answer")
    return {"claim": None if answer is None else answer["decision"],
            "evidence_refs": [] if answer is None else answer["witnesses"],
            "basis": "/owner_result", "complete_owner_trace_retained": True,
            "scope": {"measurement": "recorded identities, days, units and absolute error intervals",
                      "experiment": "recorded paired randomization design and its stated assumptions",
                      "passage": "installed source-language reading and conditional source entailment"}[unit],
            "open_obligations": ["accuracy_of_supplied_evidence", "independent_transfer", "teacher_review"],
            "world_truth_established": False}


def _role_view(role, action, alignment):
    purpose = {"student": "حل المسألة وتوثيق الدليل ومراجعة التفسير",
               "teacher": "مراجعة استجابة المتعلم واختيار تدخل تعليمي",
               "coordinator": "مراجعة مواءمة النواتج ومصادرها وفجوات تغطيتها",
               "manager": "مراجعة جاهزية التغطية والتقويم قبل التوسع",
               "parent": "طرح سؤال مساند ومتابعة تأمل المتعلم دون إنجاز المهمة عنه"}
    return {"role": role, "purpose_ar": purpose[role], "prompt_ar": PROMPTS[action],
            "coverage_status": alignment["status"], "presentation_only": True,
            "permissions_granted": [], "messages_sent": False, "school_records_updated": False}


def _inquire(problem, context, alignment):
    missing = _problem(problem)
    unit, task = problem["unit"], problem["task"]
    owner = None
    if not missing and unit != "reflection":
        # Fixed installed owners; no client-supplied dispatch, executable or status.
        owner = {"measurement": core.measurement, "experiment": core.paired_trial,
                 "passage": core.passage}[unit](deepcopy(task))
    from . import apprentice_readout
    proposal = apprentice_readout.propose(problem["text"])
    eligible = _eligible(unit, missing, owner)
    formative = _formative(problem["response"], owner)
    observations = formative["observations"]
    if any(observations.get(key) is False for key in ("decision_matches_owner", "references_match_owner")):
        eligible = [a for a in eligible if a != "independent_transfer"]
        if observations.get("references_match_owner") is False:
            eligible = ["request_evidence"] + [a for a in eligible if a != "request_evidence"]
    candidate = proposal.get("action") if proposal.get("status") == "PROPOSED" else None
    compatible = candidate in eligible
    # The first frozen evaluation failed useful action selection and OOD
    # abstention. A compatible proposal still cannot promote itself to active
    # selection, even if the model claims otherwise. Keep it for review.
    action = eligible[0]
    style, means = METHODS[action]
    explanation = _explain(unit, owner, missing)
    return {"case_id": problem["case_id"], "revision": problem["revision"],
            "status": "DEFER" if missing or (unit != "reflection" and (owner is None or owner.get("answer") is None))
                      else "OPEN_REFLECTION" if unit == "reflection" else "CHECKED_CONDITIONAL",
            "problem": deepcopy(problem), "evidence_sha256": sha256(wire.wire(task).encode("utf-8")).hexdigest(),
            "neural_proposal": proposal, "verified_obligations": {
                "input_schema_checked": True, "missing": missing,
                "owner_executed": owner is not None, "source_truth_verified": False,
                "interpretive_understanding_measured": False},
            "owner_result": owner, "pedagogical_action": {
                "proposed": candidate, "proposal_compatible": compatible,
                "proposal_admitted": False, "neural_release_policy": NEURAL_RELEASE_POLICY,
                "selected": action, "eligible": eligible,
                "selection_basis": "FIXED_OWNER_INPUT_AND_RESPONSE_CONTRACT",
                "method": "observation, source knowledge, conditional judgment, revision, transfer",
                "thinking_style_ar": style, "means_ar": means, "prompt_ar": PROMPTS[action],
                "grants_evidence_authority": False},
            "explanation": explanation, "formative_assessment": formative,
            "inquiry_cycle": {
                "problem": problem["text"], "observations": "/problem/task",
                "curriculum_target_refs": [r["id"] for r in alignment["selected_outcomes"]],
                "learner_prior_knowledge": "NOT_OBSERVED",
                "prior_knowledge_prompt_ar": "ما المعلومات السابقة التي تعتمد عليها، وما مصدر كل معلومة؟",
                "checked_analysis": "/owner_result", "conditional_judgment": explanation["claim"],
                "counterexample_prompt_ar": PROMPTS["seek_counterexample"],
                "revision": "REPLAY_FROM_ORIGINAL_CHANGED_EVIDENCE",
                "independent_transfer_prompt_ar": PROMPTS["independent_transfer"]},
            "role_view": _role_view(context["role"], action, alignment)}


def run(request):
    wire._encoded(request, MAX_REQUEST_BYTES)
    if type(request) is not dict or request.get("schema") != SCHEMA:
        raise ValueError("Unknown school apprentice schema")
    action = request.get("action")
    if action == "catalog":
        wire._fields(request, ("schema", "action"), "school catalog request")
        return {"schema": RESULT, "status": "CATALOG", "catalog": curriculum.catalog(),
                "execution_measured": True, "learning_measured": False}
    fields = {"schema", "action", "context"}
    if action in ("inquire", "revise"):
        fields.add("problem")
        if action == "revise":
            fields.add("previous")
    elif action == "induce":
        fields.update(("examples", "probes"))
    else:
        raise ValueError("Unknown school apprentice action")
    wire._fields(request, fields, "school apprentice request")
    context = curriculum.validate_context(request["context"])
    alignment = curriculum.align(context)
    base = {"schema": RESULT, "action": action, "curriculum_alignment": alignment,
            "execution_measured": True, "human_learning_measured": False,
            "official_grade_authority": False, "autonomous_weight_updates": False}
    if action == "induce":
        lesson = {"schema": core.SCHEMA, "action": "induce", "unit": "measurement",
                  "examples": request["examples"], "probes": request["probes"]}
        owner = core.learn_measurement(lesson)
        counts = owner["candidate_counts"]
        return {**base, "status": owner["status"], "owner_result": owner,
                "metacognition": {"hypothesis_count": counts,
                    "version_space_bits": [None if n == 0 else math.log2(n) for n in counts],
                    "meaning": "log2 surviving hypotheses in the installed finite guard language",
                    "next_probe_indices": [i for i, p in enumerate(owner["probes"]) if p["status"] == "UNDECIDED"],
                    "withdrawal_policy": "replay with retained training observations; never relabel missing as false",
                    "neural_weights_changed": False, "general_understanding_established": False}}
    # Validate every snapshot before executing either owner or optional neural proposal.
    _problem(request["problem"])
    if action == "revise":
        _problem(request["previous"])
        before, after = request["previous"], request["problem"]
        if (before["case_id"] != after["case_id"] or before["unit"] != after["unit"]
                or after["revision"] != before["revision"] + 1):
            raise ValueError("Revision must retain case and unit with the next version")
        previous = _inquire(before, context, alignment)
        current = _inquire(after, context, alignment)
        current["revision_comparison"] = {
            "previous_replayed": previous, "evidence_changed": previous["evidence_sha256"] != current["evidence_sha256"],
            "judgment_changed": previous["explanation"]["claim"] != current["explanation"]["claim"],
            "prior_judgment_carried_forward": False,
            "comparison_scope": "supplied snapshots; no authenticated persistent chronology"}
    else:
        current = _inquire(request["problem"], context, alignment)
    return {**base, **current}
