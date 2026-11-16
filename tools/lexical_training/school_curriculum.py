"""Versioned public curriculum references, never a grade or theorem authority.

The Jordan and IB records are independently sourced. Selecting both declares a
local alignment candidate; it does not establish equivalence or full coverage.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

from tools import evidence_lifecycle_v1 as wire

DATA = Path(__file__).with_name("data")
CATALOGS = (DATA / "ntl_jordan_framework_v1.json", DATA / "ntl_ib_framework_v1.json")
ROLES = ("student", "teacher", "coordinator", "manager", "parent")
PROGRAMMES = ("PYP", "MYP", "CP")
PROFILES = {"ib.pyp.2026": "PYP", "ib.myp.2026": "MYP",
            "ib.cp.2026": "CP", "ib.cp.2027": "CP"}
AOK = ("history", "human_sciences", "natural_sciences", "mathematics", "arts")
FOCI = ("scope", "perspectives", "methods_and_tools", "ethics")
TOK_QUESTIONS = {
    "scope": "ما الذي يجيز الدليل قوله، وما الذي يبقى خارج نطاقه؟",
    "perspectives": "كيف قد يختلف تفسير هذا الدليل باختلاف المنظور، وما سبب الاختلاف؟",
    "methods_and_tools": "كيف تؤثر طريقة جمع الدليل وأدواته وحدود دقته في الحكم؟",
    "ethics": "من قد يتأثر بهذا الحكم، وما مسؤوليتنا عن جمع الدليل واستعماله؟",
}


def catalog():
    sources, profiles, outcomes, parts, epistemic_frameworks = {}, {}, {}, [], []
    for path in CATALOGS:
        raw = path.read_bytes()
        part = json.loads(raw)
        if part.get("schema") != "ntl.framework-catalog.v1":
            raise ValueError("Unsupported installed school catalog")
        for key, target in (("sources", sources), ("profiles", profiles), ("outcomes", outcomes)):
            for record in part[key]:
                identifier = record.get("id")
                if type(identifier) is not str or not identifier or identifier in target:
                    raise ValueError("Invalid or duplicate installed curriculum identifier")
                target[identifier] = deepcopy(record)
        parts.append({"catalog_id": part["catalog_id"], "version": part["version"],
                      "sha256": sha256(raw).hexdigest(), "coverage": part["coverage"]})
        if "epistemic_framework" in part:
            epistemic_frameworks.append(deepcopy(part["epistemic_framework"]))
    for outcome in outcomes.values():
        if (not outcome.get("source_ids") or not set(outcome["source_ids"]) <= sources.keys()
                or not set(outcome.get("profile_ids", [])) <= profiles.keys()
                or not outcome.get("authority_status") or "source_locator" not in outcome):
            raise ValueError("Unbound installed curriculum reference")
    for framework in epistemic_frameworks:
        if (not set(framework["source_ids"]) <= sources.keys()
                or {row["key"] for row in framework["axes"]} != set(FOCI)
                or {row["key"] for row in framework["areas_of_knowledge"]} != set(AOK)):
            raise ValueError("Local lens vocabulary differs from the installed source framework")
    return {"schema": "ntl.school-curriculum-view.v1", "authority": "SOURCE_REFERENCE_ONLY",
            "parts": parts, "sources": list(sources.values()), "profiles": list(profiles.values()),
            "outcomes": list(outcomes.values()), "epistemic_frameworks": epistemic_frameworks,
            "all_subject_outcomes_loaded": False,
            "official_grade_authority": False,
            "body_of_knowledge": {"name": "local_body_of_knowledge",
                                  "meaning": "versioned source-bound curriculum registry",
                                  "official_ib_component": False},
            "tok": {"official_programme": "DP", "target_programmes": list(PROGRAMMES),
                    "use_in_target_programmes": "LOCAL_PEDAGOGICAL_ADAPTATION",
                    "areas_of_knowledge": list(AOK), "framework_foci": list(FOCI)}}


def validate_context(value):
    wire._fields(value, ("role", "programme", "profile_id", "assessment_session",
                         "programme_year", "national_grade", "national_subject", "subject_group",
                         "outcome_ids", "tok_lens"), "school context")
    if value["role"] not in ROLES or value["programme"] not in PROGRAMMES:
        raise ValueError("Unknown presentation role or programme")
    if PROFILES.get(value["profile_id"]) != value["programme"]:
        raise ValueError("Programme and explicit curriculum version disagree")
    year = value["programme_year"]
    if year is not None and (type(year) is not int or not 1 <= year <= 12):
        raise ValueError("Invalid programme year")
    grade = value["national_grade"]
    if grade is not None and (type(grade) is not int or not 1 <= grade <= 12):
        raise ValueError("Invalid national grade; it is independent of the IB programme year")
    if value["national_subject"] is not None:
        wire._text(value["national_subject"], "national subject", 96)
    if value["programme"] == "MYP" and (type(year) is not int or not 1 <= year <= 5):
        raise ValueError("MYP requires its programme year (1..5)")
    if value["programme"] == "CP" and (type(year) is not int or not 1 <= year <= 2):
        raise ValueError("CP requires its programme year (1..2)")
    wire._text(value["subject_group"], "subject group", 96)
    session = value["assessment_session"]
    if session is not None and (type(session) is not str or not re.fullmatch(r"20[0-9]{2}-(05|11)", session)):
        raise ValueError("Expected an explicit May/November assessment session YYYY-MM")
    if value["programme"] == "CP":
        if session is None:
            raise ValueError("CP requires its expected assessment session")
        if value["profile_id"] == "ib.cp.2027" and session != "2027-05":
            raise ValueError("The revised CP profile currently binds the first May 2027 assessment only")
        if value["profile_id"] == "ib.cp.2026" and session not in ("2026-05", "2026-11"):
            raise ValueError("The installed legacy CP profile is scoped to 2026 assessment sessions")
    ids = value["outcome_ids"]
    if type(ids) is not list or not 1 <= len(ids) <= 32:
        raise ValueError("Select 1..32 explicit curriculum outcome identifiers")
    for identifier in ids:
        wire._text(identifier, "outcome identifier", 160)
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate curriculum outcome identifier")
    lens = value["tok_lens"]
    if lens is not None:
        wire._fields(lens, ("aok", "focus"), "local TOK lens")
        if lens["aok"] not in AOK or lens["focus"] not in FOCI:
            raise ValueError("Unknown TOK area or framework focus")
    return deepcopy(value)


def align(context):
    context = validate_context(context)
    installed = catalog()
    records = {row["id"]: row for row in installed["outcomes"]}
    profiles = {row["id"]: row for row in installed["profiles"]}
    selected, missing, incompatible = [], [], []
    for identifier in context["outcome_ids"]:
        record = records.get(identifier)
        if record is None:
            missing.append(identifier)
            continue
        programmes, profile_ids = record.get("programmes", []), record.get("profile_ids", [])
        # National source profiles and an IB programme profile are different
        # coordinates. No implicit Jordan-grade/MYP-year equivalence is made.
        if ((programmes and context["programme"] not in programmes)
                or (programmes and profile_ids and context["profile_id"] not in profile_ids)
                or (type(record.get("grade")) is int and record["grade"] != context["national_grade"])
                or (record.get("subject") and record["subject"] != context["national_subject"])
                or (record.get("subject_group") and record["subject_group"] != context["subject_group"])):
            incompatible.append(identifier)
        else:
            selected.append(record)
    source_ids = {sid for row in selected for sid in row["source_ids"]}
    lens = context["tok_lens"]
    return {"status": "REFERENCE_GAPS" if missing or incompatible else "LOCAL_ALIGNMENT_CANDIDATE",
            "profile": profiles[context["profile_id"]], "selected_outcomes": selected,
            "sources": [row for row in installed["sources"] if row["id"] in source_ids],
            "missing_outcome_ids": missing, "incompatible_outcome_ids": incompatible,
            "context": context, "catalog_parts": installed["parts"],
            "national_source_profiles": [r for r in installed["profiles"] if r["id"] in {
                p for row in selected if not row.get("programmes") for p in row.get("profile_ids", [])}],
            "school_binding": {"status": "REVIEW_REQUIRED", "outcome_mapping_verified": False,
                "required_profile_fields": profiles[context["profile_id"]].get("required_binding_fields", [])},
            "all_subject_outcomes_loaded": False, "alignment_approved": False,
            "official_grade_authority": False, "role_grants_data_access": False,
            "tok": None if lens is None else {
                **lens, "applicability": "LOCAL_PEDAGOGICAL_ADAPTATION",
                "official_tok_requirement": False, "question_ar": TOK_QUESTIONS[lens["focus"]]}}
