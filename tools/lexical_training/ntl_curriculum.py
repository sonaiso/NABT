"""Four domain views of one count-change lesson; all evidence comes from its owner."""
from copy import deepcopy
import json
from operator import sub
from pathlib import Path

from nabt.learning.finite_guard import FeatureSchema, GuardLanguage, LearningSession, Observation
from tools import evidence_lifecycle_v1 as wire
from tools.grammar_catalog import interpretation_chains as records, scoped_composition

SCHEMA = "ntl.count-change-lesson.v1"
RESULT = "ntl.count-change-result.v1"
FRAMEWORK = Path(__file__).with_name("data") / "ntl_domains_v1.json"
DOMAINS = ("linguistic", "physical", "formal", "programming")
FEATURES = FeatureSchema("ntl_recorded_change", "1", ("same_unit", "second_larger"))
PROGRAMS = {"signed_delta": lambda before, after: sub(after, before),
            "magnitude": lambda before, after: abs(sub(after, before))}


def framework():
    return json.loads(FRAMEWORK.read_text(encoding="utf-8"))


def integer(value, label, minimum=0, maximum=999999):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(label + " outside integer range")


def validate(lesson):
    wire._encoded(lesson, wire.MAX_REQUEST_BYTES)
    required = {"schema", "lesson_id", "record", "exercise", "implementation", "examples"}
    optional = {"answers"} if "answers" in lesson else set()
    wire._fields(lesson, required | optional, "NTL lesson")
    wire._text(lesson["lesson_id"], "lesson id", 128)
    wire._text(lesson["record"], "record", 4096, content=True)
    if lesson["schema"] != SCHEMA or lesson["implementation"] not in PROGRAMS:
        raise ValueError("Unknown NTL lesson or implementation")
    ex = lesson["exercise"]
    wire._fields(ex, ("first_day", "last_day", "before", "after", "unit"), "exercise")
    for k in ("first_day", "last_day", "before", "after"):
        integer(ex[k], k)
    if ex["first_day"] >= ex["last_day"] or ex["unit"] not in ("فرد", "جزء", "قطعة"):
        raise ValueError("Expected ordered days and a supported count unit")
    examples = lesson["examples"]
    if type(examples) is not list or len(examples) > 32:
        raise ValueError("Expected at most 32 demonstrations")
    for row in examples:
        wire._fields(row, ("before", "after", "before_unit", "after_unit"), "demonstration")
        for key in ("before","after"):
            integer(row[key], key)
        if any(row[k] not in ("فرد", "جزء", "قطعة") for k in ("before_unit","after_unit")):
            raise ValueError("Unsupported count unit in demonstration")
    supplied = lesson.get("answers", {})
    if type(supplied) is not dict or not set(supplied) <= set(DOMAINS):
        raise ValueError("Unknown learner answer")
    for key, answer in supplied.items():
        if key in ("formal", "linguistic"):
            integer(answer, key, minimum=-999999 if key == "formal" else 0)
        elif key == "programming" and type(answer) is not bool:
            raise ValueError("Expected a Boolean test prediction")
        elif key == "physical" and answer not in ("ALIGNED", "MISMATCH", "CONFLICT", "OPEN"):
            raise ValueError("Unknown observation decision")


def learn(examples, exercise):
    """Examples are public worked cases; no target answer or trusted rank is input."""
    session = LearningSession(GuardLanguage(FEATURES, 2))
    curve = [len(session.survivors)]
    for i, row in enumerate(examples):
        values = {"same_unit": row["before_unit"] == row["after_unit"],
                  "second_larger": row["after"] > row["before"]}
        case = FEATURES.case(str(i), "1", values)
        label = values["same_unit"] and values["second_larger"]
        session = session.observe(Observation(str(i), "worked_examples", case, label))
        curve.append(len(session.survivors))
    probe = FEATURES.case("new", "1", {"same_unit": True, "second_larger": exercise["after"] > exercise["before"]})
    prediction = session.predict(probe)
    target_features_seen = any(row["before_unit"] == row["after_unit"] and
                               (row["after"] > row["before"]) == (exercise["after"] > exercise["before"])
                               for row in examples)
    pool = [FEATURES.case(f"query-{unit}-{larger}", "1", {"same_unit": unit, "second_larger": larger})
            for unit in (False, True) for larger in (False, True)]
    choice = session.choose_query(pool)
    return {"question": "هل زاد العدد تحت وحدة عدّ مشتركة في المثال التعليمي؟", "candidate_counts": curve,
            "candidate_rules": [g.render(FEATURES) for g in session.survivors],
            "prediction": list(prediction.possible), "status": prediction.status.value,
            "target_feature_pattern_seen": target_features_seen,
            "next_query": None if choice.case is None else {"same_unit": bool(choice.case.value & 1),
                "second_larger": bool(choice.case.value & 2), "split": [choice.true_count, choice.false_count]},
            "scope": "DECLARED_BOOLEAN_FEATURES_AND_WORKED_EXAMPLES"}


def observation_status(record, ex, axis="العدد"):
    pair = (ex["first_day"], ex["last_day"])
    if any(c["axis"]==axis and c["unit"]==ex["unit"] and c["day"] in pair
           for c in record.get("conflicts", [])):
        return "CONFLICT", None
    for row in record.get("changes", []):
        if (row["from_day"],row["to_day"]) != pair or row["unit"] != ex["unit"] or row["axis"] != axis:
            continue
        if row.get("verification_failure") or (axis == "العدد" and "difference" not in row):
            return "UNVERIFIED", row
        aligned = row["from_alternatives"] == [ex["before"]] and row["to_alternatives"] == [ex["after"]]
        return ("ALIGNED" if aligned else "MISMATCH"), row
    status = record.get("status")
    if status == "PARTIAL_VERIFICATION":
        return "UNVERIFIED", None
    return ("OPEN" if status == "SOURCE_RELATIVE_CHAIN" else status), None


def attributed_reading(owner, ex, axis):
    claims = [r for r in owner.get("records", []) if r["kind"]=="report" and r["axis"]==axis
              and r["unit"]==ex["unit"] and r["day"]==ex["last_day"]]
    readings = sorted({r["value"] for r in claims})
    report_complete = owner["status"] in ("SOURCE_RELATIVE_CHAIN", "PARTIAL_VERIFICATION")
    language_status = ("ATTRIBUTED" if len(readings)==1 else "MULTIPLE" if readings else "OPEN") if report_complete else owner["status"]
    claims_by_id = {r["claim"]: r for r in owner.get("reports", [])}
    report_checks = [{"claim": claim["id"],
                      "status": (check["observation_check"] if check["native_checked"] and check["certificate_checked"]
                                 else "UNVERIFIED")}
                     for claim in claims if (check := claims_by_id.get(claim["id"])) is not None]
    return readings, language_status, [r["id"] for r in claims], report_checks


def run(lesson):
    validate(lesson)
    ex = lesson["exercise"]
    owner = records.analyze(lesson["record"]) or {"status":"OUTSIDE_GRAMMAR","records":[]}
    readings, language_status, claim_ids, report_checks = attributed_reading(owner, ex, "العدد")
    empirical, row = observation_status(owner, ex)
    expression = f'{ex["after"]}-{ex["before"]}'
    maths = scoped_composition.evaluate({"schema":scoped_composition.SCHEMA,"profile":"arithmetic","text":expression})
    checked = bool(maths["chain_complete"] and maths["status"]=="COMPUTED"
                   and (maths["native_check"] or {}).get("native_checked"))
    expected = int(maths["projection"]["result"]["value"]["numerator"]) if checked else None
    actual = PROGRAMS[lesson["implementation"]](ex["before"], ex["after"])
    agrees = (expected==actual) if checked else None
    applied = "OPEN"
    if empirical == "ALIGNED" and checked:
        applied = "APPLIES_TO_RECORD" if agrees and expected==row["difference"] else "COUNTEREXAMPLE"
    cards = {
        "linguistic":{"question":"ما العدد المنسوب إلى المخبرين في اليوم الأخير وبهذه الوحدة؟",
            "status":language_status, "answer":readings[0] if len(readings)==1 else None,
            "readings":readings, "witness_ids":claim_ids},
        "physical":{"question":"هل تطابق أرصاد السجل هذين المدخلين في الزمنين وبالوحدة المطلوبة؟",
            "status":empirical,"answer":empirical if empirical in ("OPEN","CONFLICT","ALIGNED","MISMATCH") else None,
            "comparison":row, "missing_if_open":"رصدان قابلان للمقارنة في يومين متجاورين بين أرصاد المحور والوحدة"},
        "formal":{"question":"ما الفرق الموقّع وفق ترتيب الزمنين في التمرين؟","status":maths["status"],
            "answer":expected, "expression":expression},
        "programming":{"question":"هل يوافق التنفيذ المختار مواصفة الفرق على هذين المدخلين؟",
            "status":"UNVERIFIED" if agrees is None else "MATCH_ON_CASE" if agrees else "COUNTEREXAMPLE",
            "answer":agrees,"input":[ex["before"],ex["after"]],"output":actual,"implementation":lesson["implementation"]}
    }
    bridges = {
        "linguistic_to_physical": {"scope": "REPORTED_VALUE_AGAINST_OBSERVATIONS", "claims": report_checks},
        "physical_to_formal": {"status": empirical, "unit": ex["unit"],
                               "observation_ids": [] if row is None else row["dependencies"]},
        "formal_to_programming": {"status": cards["programming"]["status"], "native_reference": checked},
        "programming_to_physical": {"status": applied, "scope": "BOUND_ENDPOINTS_IN_THIS_RECORD"}
    }
    for domain, answer in lesson.get("answers", {}).items():
        gold = cards[domain]["answer"]
        cards[domain]["feedback"] = "UNGRADABLE" if gold is None else "CORRECT" if gold==answer else "REVISE"
    return {"schema":RESULT,"request":deepcopy(lesson),"status":"LESSON_RUN",
            "execution_measured":True, "framework":framework(),"cards":cards,
            "learning":learn(lesson["examples"],ex),"bridges":bridges,"transfer_to_record":applied,
            "owners":{"record":owner,"arithmetic":maths},
            "limits":{"single_record":True,"physical_cause_established":False,
                      "world_truth_established":False,"program_proved_for_all_inputs":False,
                      "neural_training_performed":False}}
