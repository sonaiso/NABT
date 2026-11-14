"""The minimum NTL teaching cycle over six evidence families; one public lesson route."""
from fractions import Fraction
from itertools import product
import json
from pathlib import Path

from nabt import arabic_reader
from nabt.errors import NabtError
from nabt.learning.finite_guard import FeatureSchema, GuardLanguage, LearningSession, Observation
from nabt.semantics import SemanticKernel
from tools import evidence_lifecycle_v1 as wire, lexical_testimony
from tools.grammar_catalog import relational_bridge, scoped_composition

SCHEMA = "ntl.minimum-course.v2"
RESULT = "ntl.minimum-course-result.v2"
BANK = Path(__file__).with_name("data") / "ntl_minimum_v2.json"
STAGES = ("worked", "transfer", "contrast", "withdrawal")
SCALES = {"mm": 1, "cm": 10, "m": 1000}
PROGRAMS = {"signed_delta": lambda a, b: b-a, "magnitude": lambda a, b: abs(b-a),
            "reversed": lambda a, b: a-b}
PROGRAM_SOURCE = {"signed_delta": "return after - before", "magnitude": "return abs(after - before)",
                  "reversed": "return before - after"}


def curriculum():
    return json.loads(BANK.read_text(encoding="utf-8"))


def bounded_int(value, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"Expected an integer in [{lower}, {upper}]")
    return value


def outcome(decision, witnesses, trace):
    return {"answer": {"decision": decision, "witnesses": sorted(set(witnesses))}, "trace": trace}


def unavailable(trace):
    return {"answer": None, "trace": trace}


def sign(task):
    wire._fields(task, ("text",), "single utterance")
    wire._text(task["text"], "utterance", 512, content=True)
    reading = arabic_reader.read_arabic(task["text"])
    if len(reading.steps) != 1:
        raise ValueError("The sign exercise accepts one utterance")
    packet = reading.packet()
    restored = arabic_reader.decode_reading_number(int(packet["number_hex"], 16))
    if restored != reading.as_dict():
        return unavailable({"reason": "READING_REPLAY_MISMATCH"})
    step = reading.steps[0]
    trace = {"reading": restored, "folded": packet, "restored_exactly": True}
    if not reading.accepted:
        return outcome("UNRESOLVED", [], trace)
    quote = step.span.extract(reading.document.source).decode()
    return outcome(step.mood.name, [quote], trace)


def passage(task):
    wire._fields(task, ("text", "query"), "Arabic passage")
    wire._text(task["text"], "passage", 2048, content=True)
    wire._text(task["query"], "query", 192, content=True)
    kernel = SemanticKernel(language_id=arabic_reader.LANGUAGE_ID)
    admission = kernel.add_source(task["text"], source_id="passage")
    trace = {"admission": admission.as_dict()}
    if not admission.accepted:
        if any(r.get("code") == "RESOURCE_LIMIT" for r in admission.residuals):
            return unavailable(trace)
        return outcome("UNREAD", [], trace)
    try:
        claim = kernel.query_text(task["query"])
    except NabtError as exc:
        trace["query_error"] = exc.as_dict()
        return unavailable(trace) if exc.code == "RESOURCE_LIMIT" else outcome("UNREAD", [], trace)
    trace["query"] = claim.as_dict()
    checks = {side: kernel.verify_certificate(proof)["accepted"] for side, proof in claim.proofs.items()}
    trace["certificate_checks"] = checks
    status = "CONTESTED" if claim.reason == "CONTESTED_PREMISES" else claim.status
    if not all(checks.values()) or status not in ("SUPPORTED", "REFUTED", "CONFLICT", "UNKNOWN", "OUT_OF_SCOPE", "CONTESTED"):
        return unavailable(trace)
    # The original byte spans are preserved even when several steps cite the same sentence.
    raw = task["text"].encode()
    quotes = []
    for proof in claim.proofs.values():
        for step in proof["steps"]:
            span = step["clause"]["span"]
            text = raw[span["start"]:span["end"]].decode().strip()
            quotes.append(text)
    return outcome(status, quotes, trace)


def indication(task):
    wire._fields(task, ("root", "target"), "indication")
    wire._text(task["root"], "root", 32)
    if task["target"] is None:
        return outcome("MISSING_TARGET", [], {"root": task["root"], "missing": "target"})
    if type(task["target"]) is not list or not 1 <= len(task["target"]) <= 8:
        raise ValueError("Expected 1..8 target components")
    for component in task["target"]:
        wire._text(component, "component", 128)
    report = lexical_testimony.assess(task["root"], task["target"])
    if not report.get("native_checked"):
        return unavailable(report)
    rows = report["rows"]
    if not rows:
        return outcome("UNMEASURED", [], report)
    if not report["all_installed_readings_retained"]:
        return unavailable(report)
    common = report["common_indications"]
    matched = [row["sense_id"] for row in rows if any(row["indications"].values())]
    if len(common) == 1:
        return outcome(common[0], matched, report)
    if common:
        return unavailable(report)
    return outcome("SENSE_DEPENDENT" if matched else "NO_LICENSE", matched, report)


def ontology(task):
    wire._fields(task, ("text", "bridge"), "ontological reading")
    wire._text(task["text"], "occurrence", 256)
    report = relational_bridge.evaluate(task["text"], task["bridge"])
    receipt = report.get("native_receipt")
    if not receipt:
        return unavailable(report)
    if report["licensed"]:
        return outcome("SCOPED_SOURCE_LICENSE", [row["predicate"] for row in receipt["requirements"]], report)
    return outcome(receipt["qualified_verdict"], [row["predicate"] for row in report["missing"]], report)


def measurement(task):
    wire._fields(task, ("readings",), "length comparison")
    rows = task["readings"]
    if type(rows) is not list or not 1 <= len(rows) <= 2:
        raise ValueError("Expected one or two ordered length readings")
    intervals = []
    references = []
    for i, row in enumerate(rows, 1):
        wire._fields(row, ("object", "day", "unit", "value", "error"), "reading")
        wire._text(row["object"], "object", 96)
        bounded_int(row["day"], 0, 9999)
        v = bounded_int(row["value"], 0, 999999)
        error = bounded_int(row["error"], 0, v)
        if row["unit"] not in SCALES:
            raise ValueError("Unsupported length unit")
        scale = SCALES[row["unit"]]
        intervals.append([(v-error)*scale, (v+error)*scale])
        references.append("R"+str(i))
    trace = {"intervals_mm": intervals, "error_model": "closed_absolute_bounds"}
    if len(rows) < 2:
        return outcome("MISSING_READING", references, trace)
    if rows[0]["object"] != rows[1]["object"] or rows[0]["day"] >= rows[1]["day"]:
        return outcome("UNALIGNED", references, trace)
    (a, b), (c, d) = intervals
    if b < c:
        status = "INCREASE"
    elif d < a:
        status = "DECREASE"
    elif a == b == c == d:
        status = "SAME"
    else:
        status = "UNRESOLVED_PRECISION"
    return outcome(status, references, trace)


def paired_trial(task):
    wire._fields(task, ("assignment", "intervention", "control", "endpoint", "outcome_unit", "pairs"), "matched-pair experiment")
    if task["assignment"] not in ("fair_independent_within_pair", "observer_selected", "unreported"):
        raise ValueError("Unknown assignment design")
    wire._text(task["outcome_unit"], "common outcome unit", 96)
    for key in ("intervention", "control", "endpoint"):
        if task[key] is not None:
            wire._text(task[key], key, 192)
    pairs = task["pairs"]
    if type(pairs) is not list or not 1 <= len(pairs) <= 10:
        raise ValueError("Expected 1..10 pairs")
    differences, refs = [], ["design"]
    units = set()
    trace = {"assignment": task["assignment"], "outcome_unit": task["outcome_unit"],
             "assumptions": ["as_recorded_assignment", "no_interference", "common_measurement",
                             "prespecified_two_sided_test"], "alpha": "1/20",
             "null": "zero_effect_for_every_unit", "world_truth_established": False}
    for i, row in enumerate(pairs, 1):
        wire._fields(row, ("ids", "treated", "values"), "pair")
        ids, values = row["ids"], row["values"]
        if type(ids) is not list or len(ids) != 2 or type(values) is not list or len(values) != 2:
            raise ValueError("Each pair needs two unit identities and two outcome slots")
        for uid in ids:
            wire._text(uid, "unit identity", 48)
            if uid in units:
                raise ValueError("An experimental unit cannot occur twice")
            units.add(uid)
        treated = bounded_int(row["treated"], 0, 1)
        for v in values:
            if v is not None:
                bounded_int(v, -999999, 999999)
        refs.append("P"+str(i))
        differences.append(None if None in values else values[treated]-values[1-treated])
    trace["treated_minus_control"] = differences
    trace["comparison"] = {key: task[key] for key in ("intervention", "control", "endpoint")}
    if any(task[key] is None for key in trace["comparison"]) or task["intervention"] == task["control"]:
        return outcome("UNDEFINED_COMPARISON", ["design"], trace)
    if task["assignment"] != "fair_independent_within_pair":
        return outcome("DESIGN_INSUFFICIENT", ["design"], trace)
    missing = [r for r, v in zip(refs[1:], differences) if v is None]
    if missing:
        return outcome("MISSING_OUTCOME", missing, trace)
    observed = abs(sum(differences))
    # Under the sharp null each of the 2**n assignments has equal probability.
    total = 2 ** len(pairs)
    extreme = sum(abs(sum(s*d for s, d in zip(signs, differences))) >= observed
                  for signs in product((-1, 1), repeat=len(pairs)))
    trace.update(extreme=extreme, assignments=total, exact_p=str(Fraction(extreme, total)),
                 observed_mean_difference=str(Fraction(sum(differences), len(pairs))))
    return outcome("REJECT_SHARP_NULL" if 20*extreme <= total else "INSUFFICIENT_EVIDENCE", refs, trace)


def arithmetic(task):
    wire._fields(task, ("text",), "formal expression")
    if task["text"] is None:
        return outcome("MISSING_EXPRESSION", [], {"missing": "expression"})
    wire._text(task["text"], "expression", 512, content=True)
    report = scoped_composition.evaluate({"schema": scoped_composition.SCHEMA, "profile": "arithmetic",
                                          "text": task["text"]})
    if not report["chain_complete"] or not (report["native_check"] or {}).get("native_checked"):
        return unavailable(report)
    value = report["projection"]["result"]
    if value["status"] == "BLOCKED":
        return outcome(value["reason"], ["expression"], report)
    if value["sort"] == "proposition":
        return outcome("TRUE" if value["truth"] else "FALSE", ["expression"], report)
    q = value["value"]
    return outcome(str(Fraction(int(q["numerator"]), int(q["denominator"]))), ["expression"], report)


def program(task):
    wire._fields(task, ("implementation", "domain"), "finite program specification")
    name = task["implementation"]
    if name not in PROGRAMS:
        raise ValueError("Unknown installed program")
    domain = task["domain"]
    if type(domain) is not list or not 1 <= len(domain) <= 2:
        raise ValueError("Expected one or two inclusive bounds")
    for bound in domain:
        bounded_int(bound, -16, 16)
    if len(domain) == 1:
        return outcome("MISSING_UPPER_BOUND", ["domain"], {"domain": domain})
    lo, hi = domain
    if hi < lo:
        raise ValueError("Reversed bounds")
    checked = 0
    for a, b in product(range(lo, hi+1), repeat=2):
        checked += 1
        actual = PROGRAMS[name](a, b)
        # Contract given independently as an equation, before + output = after.
        if a + actual != b:
            return outcome("COUNTEREXAMPLE", [f"{a},{b}"], {"input": [a,b], "output": actual,
                            "contract": "before + output == after", "inputs_checked": checked})
    return outcome("ALL_IN_DOMAIN", ["domain"], {"domain": domain, "inputs_checked": checked,
                   "contract": "before + output == after"})


def integrated(task):
    wire._fields(task, ("text", "query", "readings", "implementation"), "integrated length report")
    reading = passage({"text": task["text"], "query": task["query"]})
    measurements = measurement({"readings": task["readings"]})
    name = task["implementation"]
    if name not in PROGRAMS:
        raise ValueError("Unknown installed program")
    rows = task["readings"]
    # A linguistic bridge must agree with the query's parsed assertion, its subject,
    # and its direction. A supported but unrelated sentence cannot supply this premise.
    trace = {"language": reading, "measurement": measurements, "implementation": name,
             "scope": "positive_length_increase_between_the_two_supplied_days"}
    if reading["answer"] is None:
        return unavailable(trace)
    q = reading["trace"].get("query", {}).get("query", {})
    language_refs = reading["answer"]["witnesses"]
    m = measurements["answer"]
    if (reading["answer"]["decision"] != "SUPPORTED" or
            q != {"predicate": "متزايد", "args": [rows[0]["object"]], "positive": True}):
        return outcome("NO_MATCHING_CLAIM", language_refs, trace)
    if m["decision"] != "INCREASE":
        return outcome("INCREASE_NOT_ESTABLISHED", m["witnesses"], trace)
    before, after = [row["value"] * SCALES[row["unit"]] for row in rows]
    reference = arithmetic({"text": f"{after}-{before}"})
    trace["formal"] = reference
    if reference["answer"] is None:
        return unavailable(trace)
    output = PROGRAMS[name](before, after)
    trace["program_io_mm"] = [before, after, output]
    if str(output) != reference["answer"]["decision"]:
        return outcome("IMPLEMENTATION_DISAGREES", ["expression", "program"], trace)
    return outcome("APPLIES_TO_RECORDED_INTERVAL", language_refs + m["witnesses"] + ["expression", "program"], trace)


OWNERS = {"sign": sign, "passage": passage, "indication": indication, "measurement": measurement,
          "ontology": ontology, "experiment": paired_trial, "formal": arithmetic, "program": program, "integrated": integrated}


MEASURE_FEATURES = FeatureSchema("ntl_length_increase", "1", ("same_object", "ordered_days", "separated_up"))


def learn_measurement(lesson):
    wire._fields(lesson, ("schema", "action", "unit", "examples", "probes"), "measurement induction")
    if lesson["unit"] != "measurement":
        raise ValueError("This induction profile learns the length-increase guard")
    examples, probes = lesson["examples"], lesson["probes"]
    if any(type(items) is not list or len(items) > 12 for items in (examples, probes)) or not probes:
        raise ValueError("Expected up to 12 training and 1..12 probe records")
    seen, patterns = set(), set()
    learner = LearningSession(GuardLanguage(MEASURE_FEATURES, 3))
    curve = [len(learner.survivors)]
    results = []
    for i, task in enumerate([*examples, *probes]):
        raw = wire.wire(task)
        if raw in seen:
            raise ValueError("Training and probe records must be distinct")
        seen.add(raw)
        result = measurement(task)
        rows = task["readings"]
        training = i < len(examples)
        if len(rows) < 2:
            if training:
                curve.append(len(learner.survivors))
            else:
                results.append({"status": "MISSING_READING", "possible": [], "features": None})
            continue
        first, last = result["trace"]["intervals_mm"]
        features = {"same_object": rows[0]["object"] == rows[1]["object"],
                    "ordered_days": rows[0]["day"] < rows[1]["day"], "separated_up": first[1] < last[0]}
        case = MEASURE_FEATURES.case(str(i), "1", features)
        pattern = tuple(features.values())
        label = result["answer"]["decision"] == "INCREASE"
        if training:
            learner = learner.observe(Observation(str(i), "measurement", case, label))
            patterns.add(pattern)
            curve.append(len(learner.survivors))
        else:
            possible = list(learner.predict(case).possible)
            status = "UNDECIDED" if len(possible) != 1 else "CORRECT" if possible == [label] else "REVISE"
            results.append({"status": status, "features": features, "pattern_seen": pattern in patterns,
                            "possible": possible, "reference": result["answer"]})
    return {"schema": RESULT, "status": "COURSE_SESSION", "action": "induce", "unit": "measurement",
            "execution_measured": True, "candidate_counts": curve, "probes": results,
            "surviving_rules": [g.render(MEASURE_FEATURES) for g in learner.survivors],
            "scope": "declared_conjunctions_of_three_measured_features"}


def portfolio(lesson):
    wire._fields(lesson, ("schema", "action", "submissions"), "core portfolio")
    submitted = lesson["submissions"]
    if type(submitted) is not dict or not set(submitted) <= OWNERS.keys():
        raise ValueError("Unknown portfolio unit")
    rows = {}
    for unit in curriculum():
        if unit in submitted:
            session = run({"schema": SCHEMA, "action": "assess", "unit": unit, "submissions": submitted[unit]})
            grades = {case: entry["grade"] for case, entry in session["cases"].items()}
        else:
            grades = dict.fromkeys(STAGES, "UNANSWERED")
        pending = [stage for stage in STAGES[1:] if grades[stage] != "CORRECT"]
        rows[unit] = {"grades": grades, "earned": len(STAGES)-1-len(pending), "remaining": pending}
    return {"schema": RESULT, "status": "COURSE_SESSION", "action": "portfolio", "execution_measured": True,
            "units": rows, "earned": sum(row["earned"] for row in rows.values()),
            "required": len(rows)*(len(STAGES)-1), "complete_on_declared_core": all(not row["remaining"] for row in rows.values()),
            "scope": "VERSIONED_PUBLIC_BANK"}


def run(lesson):
    wire._encoded(lesson, wire.MAX_REQUEST_BYTES)
    action = lesson.get("action")
    if action == "induce":
        return learn_measurement(lesson)
    if action == "portfolio":
        return portfolio(lesson)
    fields = {"schema", "action", "unit"}
    if action == "assess":
        fields.add("submissions")
    if "task" in lesson:
        fields.add("task")
    wire._fields(lesson, fields, "minimum course")
    unit = lesson["unit"]
    if unit not in OWNERS or action not in ("worksheet", "teach", "assess"):
        raise ValueError("Unknown unit or action")
    spec = curriculum()[unit]
    tasks = {"new": lesson["task"]} if "task" in lesson else spec["cases"]
    answers = lesson.get("submissions", {})
    if type(answers) is not dict or not set(answers) <= tasks.keys():
        raise ValueError("Answers must refer to selected cases")
    for response in answers.values():
        wire._fields(response, ("decision", "witnesses"), "answer")
        wire._text(response["decision"], "decision", 128)
        refs = response["witnesses"]
        if type(refs) is not list or len(refs) > 32:
            raise ValueError("Invalid witness list")
        for ref in refs:
            wire._text(ref, "witness", 2048)
        if len(set(refs)) != len(refs):
            raise ValueError("Witnesses must be distinct")
    entries = {}
    for cid, task in tasks.items():
        entry = {"task": task}
        if action != "worksheet" or "task" in lesson:
            evaluated = OWNERS[unit](task)
            if action == "teach":
                entry.update(evaluated)
            if action == "assess":
                gold, answer = evaluated["answer"], answers.get(cid)
                if gold is None:
                    entry["grade"] = "UNGRADABLE"
                elif answer is None:
                    entry["grade"] = "UNANSWERED"
                else:
                    entry["grade"] = "CORRECT" if (answer["decision"] == gold["decision"] and
                          set(answer["witnesses"]) == set(gold["witnesses"])) else "REVISE"
        if unit in ("program", "integrated"):
            entry["code"] = PROGRAM_SOURCE[task["implementation"]]
        entries[cid] = entry
    result = {"schema": RESULT, "status": "COURSE_SESSION", "execution_measured": True, "unit": unit,
              "objective": spec["objective"], "question": spec["question"], "answer_format": spec["answer_format"],
              "action": action, "cases": entries}
    if action == "assess":
        counted = ["new"] if "task" in lesson else list(STAGES[1:])
        result["assessment"] = {"scope": "submitted_task" if "task" in lesson else "unit_transfer_contrast_withdrawal",
                                "correct": sum(entries[c]["grade"] == "CORRECT" for c in counted),
                                "required": len(counted)}
    return result
