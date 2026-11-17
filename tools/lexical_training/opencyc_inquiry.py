"""Source-relative NTP inquiry over the existing OpenCyc and finite-guard owners.

One native replay supplies the whole signed closure. Only clean, known training
memberships become labels; withheld probe labels never enter the learner.
Events are replayed from the immutable request, not from caller-stored survivors.
This learns a guard in a declared language, NOT new semantics or source truth.
External access is only cognitive.lesson through gateway run/verify.
"""
from __future__ import annotations

from copy import deepcopy

from nabt.errors import NabtError
from nabt.learning.finite_guard import FeatureSchema, GuardLanguage, LearningSession, Observation
from tools.grammar_catalog import opencyc_slice as oc

SCHEMA = "nabt.opencyc-inquiry.v1"
RESULT = "nabt.opencyc-inquiry-result.v1"
POLICY = "nabt.opencyc-source-relative-guard-learning.v1"
MAX_SUBJECTS = 8
MAX_FEATURES = 3
MAX_EVENTS = 16
LIMITS = {
    "source_truth_established": False,
    "arabic_lexical_alignment_established": False,
    "world_truth_established": False,
    "neural_training_performed": False,
    "generalization_established": False,
    "rule_adoption_authorized": False,
    "law_mutation_authorized": False,
    "action_authority": "NONE",
    "feature_meanings": "CALLER_DECLARED_CLASSES_NOT_ACQUIRED_FROM_TEXT",
    "learning": "FINITE_GUARD_INDUCTION_FROM_NATIVE_SOURCE_RELATIVE_LABELS",
    "history_integrity": "REPLAY_AND_INDEPENDENT_GATEWAY_REQUEST_NOT_EXTERNAL_SIGNATURE",
}


def _constants(value, maximum, label, *, nonempty=False):
    if (type(value) is not list or len(value) > maximum or (nonempty and not value)
            or any(type(x) is not str for x in value) or len(value) != len(set(value))):
        raise oc.SliceError("INVALID_INPUT", "Invalid distinct bounded list: " + label)
    for x in value:
        oc.constant(x)


def validate(lesson):
    oc.fields(lesson, ("schema", "text", "source_id", "slice", "target_class",
                      "feature_classes", "training_subjects", "probe_subjects",
                      "degree", "events"), "inquiry lesson")
    if lesson["schema"] != SCHEMA:
        raise oc.SliceError("INVALID_INPUT", "Unknown inquiry schema")
    oc.text(lesson["text"], "Arabic source", 8192)
    oc.text(lesson["source_id"], "Arabic source identity", 128)
    oc.validate(lesson["slice"])
    oc.constant(lesson["target_class"])
    _constants(lesson["feature_classes"], MAX_FEATURES, "features", nonempty=True)
    _constants(lesson["training_subjects"], MAX_SUBJECTS, "training subjects")
    _constants(lesson["probe_subjects"], MAX_SUBJECTS, "probe subjects")
    subjects = lesson["training_subjects"] + lesson["probe_subjects"]
    if not subjects or len(subjects) > MAX_SUBJECTS or len(subjects) != len(set(subjects)):
        raise oc.SliceError("INVALID_INPUT", "Training and probe subjects must be disjoint and bounded")
    if lesson["target_class"] in lesson["feature_classes"]:
        raise oc.SliceError("TARGET_AS_FEATURE", "The target label cannot be a feature")
    degree = lesson["degree"]
    if type(degree) is not int or not 0 <= degree <= len(lesson["feature_classes"]):
        raise oc.SliceError("INVALID_INPUT", "Invalid finite guard degree")
    events = lesson["events"]
    if type(events) is not list or len(events) > MAX_EVENTS:
        raise oc.SliceError("RESOURCE_LIMIT", "Too many inquiry events")
    effective, _, _ = project_events(lesson)
    c = oc.compile_slice(effective)
    referenced = set(subjects + lesson["feature_classes"] + [lesson["target_class"]])
    # No source or logical fact is injected to create an out-of-slice example.
    if not referenced <= c["symbols"].keys():
        raise oc.SliceError("OUTSIDE_SLICE", "Learning references must belong to this source slice")
    if c["status"] == "COMPILED":
        _reject_target_derived_features(c, subjects, lesson["target_class"], lesson["feature_classes"])
    return deepcopy(lesson)


def _reject_target_derived_features(compiled, subjects, target, features):
    """Conservative syntactic dependency check; target labels must not create features."""
    def key(a):
        return a["predicate"], tuple(a["arguments"]), a["positive"]
    successors = {}
    for clause in compiled["clauses"]:
        if clause["kind"] == "rule":
            for premise in clause["body"]:
                successors.setdefault(key(premise), set()).add(key(clause["head"]))
    symbols = compiled["symbols"]
    for subject in subjects:
        reached = {key(oc.atom("oc_isa", symbols[subject], symbols[target], p)) for p in (True, False)}
        frontier = list(reached)
        while frontier:
            for nxt in successors.get(frontier.pop(), ()):
                if nxt not in reached:
                    reached.add(nxt)
                    frontier.append(nxt)
        if any(key(oc.atom("oc_isa", symbols[subject], symbols[f], p)) in reached
               for f in features for p in (True, False)):
            raise oc.SliceError("TARGET_DERIVED_FEATURE", "A declared feature can depend on the target label")


def project_events(lesson):
    """Project append-only review events without mutating source bytes or past requests."""
    source = lesson["slice"]
    known_records = {r["id"] for r in oc.records(source["ledger"])}
    withdrawn = set(source["withdrawn"])
    trained = list(lesson["training_subjects"])
    observed = set(trained)
    probes = set(lesson["probe_subjects"])
    anchor = {k: v for k, v in lesson.items() if k != "events"}
    parent = oc.digest(anchor)
    history, ids = [], set()
    for index, event in enumerate(lesson["events"]):
        oc.fields(event, ("id", "operation", "target"), "inquiry event")
        oc.text(event["id"], "event id", 96)
        oc.text(event["target"], "event target", 96)
        if event["id"] in ids:
            raise oc.SliceError("INVALID_INPUT", "Repeated event identity")
        ids.add(event["id"])
        op, target = event["operation"], event["target"]
        if op == "withdraw":
            if target not in known_records or target in withdrawn:
                raise oc.SliceError("INVALID_EVENT", "Withdrawal needs an active source record")
            withdrawn.add(target)
        elif op == "restore":
            if target not in withdrawn:
                raise oc.SliceError("INVALID_EVENT", "Restoration needs a withdrawn source record")
            withdrawn.remove(target)
        elif op == "observe":
            if target not in probes or target in observed:
                raise oc.SliceError("INVALID_EVENT", "Observation must reveal an unobserved declared probe")
            observed.add(target)
            trained.append(target)
        else:
            raise oc.SliceError("INVALID_INPUT", "Unknown event operation")
        entry = {"index": index + 1, "event": deepcopy(event), "parent": parent,
                 "withdrawn": sorted(withdrawn), "observed_subjects": list(trained),
                 "assessment": "NOT_ASSESSED_HERE_ONLY_CURRENT_STATE_REPLAYED"}
        parent = oc.digest(entry)
        history.append({**entry, "event_sha256": parent})
    effective = deepcopy(source)
    effective["withdrawn"] = sorted(withdrawn)
    return effective, trained, {"anchor_sha256": oc.digest(anchor),
                               "events": history, "head_sha256": parent}


def _class_status(owner, subject, kind):
    symbols = owner["compiled"]["symbols"]
    a = oc.atom("oc_isa", symbols[subject], symbols[kind])
    return oc._classification(a, owner["proposal"])


def _truth(status):
    return True if status == "SUPPORTED" else False if status == "REFUTED" else None


def _learn_checked(lesson, owner, trained):
    """Internal reducer. The production caller is run(), never an external receipt."""
    if owner.get("native_checked") is not True or owner.get("native_receipt") is None:
        raise ValueError("Native source replay is mandatory before induction")
    source = owner["compiled"]["request"]
    features = lesson["feature_classes"]
    # Semantic schema stays stable over withdrawal; evidence revision changes.
    schema_identity = {"source": source["source"], "context": source["context"],
                       "target_class": lesson["target_class"], "feature_classes": features}
    schema = FeatureSchema("opencyc-inquiry:" + oc.digest(schema_identity), "1", tuple(features))
    analysis_id = owner["compiled"]["request_sha256"]
    session = LearningSession(GuardLanguage(schema, lesson["degree"]))
    samples, counts = [], [len(session.survivors)]

    def case_for(subject):
        statuses = {f: _class_status(owner, subject, f) for f in features}
        return schema.case(subject, analysis_id, {f: _truth(s) for f, s in statuses.items()}), statuses

    for subject in trained:
        case, statuses = case_for(subject)
        target_status = _class_status(owner, subject, lesson["target_class"])
        observation = Observation("obs:" + oc.digest([analysis_id, subject]),
                                  source["source"]["id"], case, _truth(target_status))
        session = session.observe(observation)
        counts.append(len(session.survivors))
        samples.append({"subject": subject, "feature_statuses": statuses,
                        "target_status": target_status, "ready": observation.ready,
                        "evidence_id": observation.evidence_id})

    pool, predictions = [], []
    for subject in lesson["probe_subjects"]:
        if subject in trained:
            continue
        case, statuses = case_for(subject)
        # Deliberately do not read the target membership for withheld probes.
        p = session.predict(case)
        pool.append(case)
        predictions.append({"subject": subject, "feature_statuses": statuses,
                            "status": p.status.value, "possible": list(p.possible),
                            "missing_predicates": list(p.missing_predicates),
                            "witness_rules": list(p.witness_rules),
                            "evidence_revision": p.evidence_revision,
                            "authority": "CONDITIONAL_PREDICTION_NOT_ADOPTED_RULE"})
    choice = session.choose_query(pool)
    if not session.survivors:
        action = {"action": "REVIEW_EVIDENCE_OR_DECLARED_GRAMMAR", "reason": session.exhaustion_reason()}
    elif session.pending:
        action = {"action": "ACQUIRE_MISSING_OR_UNCONTESTED_PREMISES", "evidence_ids": list(session.pending)}
    elif choice.case is not None:
        action = {"action": "SEEK_DISCRIMINATING_LABEL", "subject": choice.case.case_id,
                  "query": {"predicate": "isa", "arguments": [choice.case.case_id, lesson["target_class"]],
                            "positive": True},
                  "disagreement": {"true_count": choice.true_count, "false_count": choice.false_count},
                  "candidate_guards": [choice.true_rule, choice.false_rule],
                  "execution_authorized": False}
    elif len(session.survivors) == 1:
        action = {"action": "TEST_INDEPENDENT_OCCURRENCE_BEFORE_ADOPTION",
                  "reason": "ONE_GUARD_IN_DECLARED_LANGUAGE_IS_NOT_A_UNIVERSAL_LAW"}
    else:
        action = {"action": "EXPAND_REVIEW_POOL", "reason": choice.reason}
    return {"schema_sha256": schema.fingerprint, "evidence_revision": session.revision,
            "hypothesis_count": session.language.count, "candidate_counts": counts,
            "survivor_codes": [g.code for g in session.survivors],
            "survivor_expressions": [g.render(schema) for g in session.survivors],
            "pending": list(session.pending), "training_samples": samples,
            "probe_predictions": predictions, "next_step": action,
            "new_rule_adopted": False, "withheld_probe_labels_used": False}


def _run(lesson):
    p = validate(lesson)
    effective, trained, history = project_events(p)
    result = {"schema": RESULT, "policy": POLICY, "status": "DEFER",
              "request": p, "request_sha256": oc.digest(p), "history": history,
              "effective_slice_sha256": oc.digest(effective), "limits": dict(LIMITS),
              "owner_result": None, "learning": None, "execution_measured": False}
    try:
        owner = oc.analyze(p["text"], p["source_id"], effective)
        result["owner_result"] = owner
        if not owner.get("native_checked") or owner.get("native_receipt") is None:
            result["next_step"] = {"action": "RESOLVE_ORIGINAL_OWNER_OBLIGATION",
                                   "reason": owner.get("reason", owner["status"])}
            return result
        # Bind the local owner result to this actual call, even before gateway replay.
        if owner["compiled"]["request_sha256"] != oc.digest(effective):
            raise oc.SliceError("SOURCE_MISMATCH", "Owner replay does not match the effective request")
        learning = _learn_checked(p, owner, trained)
    except NabtError:
        raise
    result.update(status="CONDITIONAL_LEARNING_REPORT", learning=learning,
                  next_step=learning["next_step"], execution_measured=True)
    result["explanation_ar"] = (
        "هذا تعلّم لشرط تصنيف داخل لغة فرضيات معلنة من أحكام مصدرية أعاد فاحص NABT فحصها. "
        "السحب والاستعادة يعيدان الحساب من الأصل؛ لا تعتمد القاعدة المتعلمة ولا حقيقة المصدر تلقائيًا. "
        "التعلم هنا خوارزمي، وليس تدريب أوزان عصبية أو اكتساب معاني الخواص من النص.")
    return result


def run(lesson):
    try:
        return _run(lesson)
    except (oc.SliceError, NabtError) as exc:
        if exc.code != "RESOURCE_LIMIT":
            raise
        return {"schema": RESULT, "policy": POLICY, "status": "RESOURCE_LIMIT",
                "execution_measured": False, "reason": str(exc), "learning": None,
                "limits": dict(LIMITS),
                "next_step": {"action": "REDUCE_DECLARED_RESOURCE_SCOPE"}}
