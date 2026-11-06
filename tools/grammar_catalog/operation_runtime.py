"""Typed adapters to installed owners; retrieved text is never executable code.

No new linguistic law is defined here. Owner reports, including deferred and
conflicting results, are transported intact. Replay is not semantic promotion.
"""
from __future__ import annotations

from copy import deepcopy
from types import MappingProxyType

from nabt.alphabet import parse_word
from nabt.cli import number, numeric_payload
from nabt.codec import encode_cells
from nabt.errors import NabtError
from nabt.machine import Machine, compose_effects


def _spec(title, fields, required, owner, scope, defaults=None):
    return {"title": title, "input_contract": {"fields": fields, "required": required,
            "additional_fields": False}, "owner": owner, "scope": scope,
            "defaults": defaults or {}}


_MODE = {"mode": "mode", "start_state": "state"}
_DEFAULTS = {"mode": "waqf", "start_state": 0}
_SPECS = MappingProxyType({
    "encode": _spec("ترميز كلمة مشكولة إلى عدد وخلايا encode", {"text": "text"}, ["text"],
        ("src/nabt/codec.py", "encode_cells", "Nabt.Sequence"), "ENCODING_ONLY"),
    "decode": _spec("فك الترميز العددي إلى الحروف والحركات decode", {"number": "number"}, ["number"],
        ("src/nabt/codec.py", "decode_number", "Nabt.Sequence"), "ENCODING_ONLY"),
    "contrast": _spec("مقارنة الحركة والترتيب والموضع بين كلمات مشكولة contrast",
        {"texts": "texts"}, ["texts"], ("src/nabt/alphabet.py", "parse_word", "Nabt.Cell"),
        "EXACT_REPRESENTATION_NOT_PERSON_VOICE_OR_MEANING"),
    "analyse": _spec("تحليل ترخيص الشكل الصوتي والوزن والمسار analyse",
        {"text": "text", **_MODE}, ["text"], ("src/nabt/machine.py", "Machine.analyse", "Nabt.Law"),
        "DECLARED_SHAPE_LAW", _DEFAULTS),
    "effect": _spec("حساب الأثر العددي على جميع الحالات effect", {"text": "text"}, ["text"],
        ("src/nabt/machine.py", "Machine.effect", "Nabt.Transition"), "TOTAL_NUMERICAL_EFFECT"),
    "compose_effects": _spec("تركيب الآثار وحفظ ترتيب الأجزاء compose_effects",
        {"texts": "texts"}, ["texts"], ("src/nabt/machine.py", "compose_effects", "Nabt.Transition"),
        "TOTAL_NUMERICAL_EFFECT_NOT_WORD_LICENSE"),
    "count": _spec("عد الأشكال المرخصة حسب الوزن والحالة count",
        {"weight": "weight", **_MODE}, ["weight"], ("src/nabt/machine.py", "Machine.count", "Nabt.Count"),
        "COUNT_OF_SHAPES_IN_DECLARED_LAW", _DEFAULTS),
    "rank": _spec("رتبة الشكل في الوزن وفق القانون rank",
        {"text": "text", **_MODE}, ["text"], ("src/nabt/machine.py", "Machine.rank", "Nabt.Count"),
        "SHAPE_RANK_NOT_EVIDENCE_RANK", _DEFAULTS),
    "unrank": _spec("استخراج الشكل من الوزن والرتبة unrank",
        {"weight": "weight", "rank": "number", **_MODE}, ["weight", "rank"],
        ("src/nabt/machine.py", "Machine.unrank", "Nabt.Count"), "DECLARED_SHAPE_LAW", _DEFAULTS),
    "derivation": _spec("استرجاع مرشحي الجذر والوزن والاشتقاق derivation",
        {"text": "text", "source_id": "id", "scope": "id", "profile": "profile"}, ["text"],
        ("src/nabt/derivation.py", "read_derivation", "Nabt.Derivation"), "OWNER_PATTERN_CANDIDATES",
        {"source_id": "input", "scope": "default", "profile": "surface_v1"}),
    "person": _spec("مرشحو الشخص والعدد والجنس من الشواهد الصرفية person",
        {"text": "text"}, ["text"], ("src/nabt/person_evidence.py", "person_candidates", "Nabt.PersonEvidence"),
        "MORPHOLOGICAL_CANDIDATES_NOT_REFERENCE"),
    "program": _spec("برنامج التعلم والاستعلام وسحب المصدر وإعادته program",
        {"request": "object"}, ["request"], ("src/nabt/program.py", "execute_program", "Nabt.Program"),
        "EXISTING_INERT_PROGRAM_CONTRACTS"),
    "lesson": _spec("درس معرفي عبر مسار التعلم الحالي lesson",
        {"lesson": "object"}, ["lesson"], ("tools/lexical_training/teaching.py", "run_lesson", None),
        "EXISTING_LESSON_OWNER_CONTRACTS"),
})


def specifications():
    """Return data copies; editing a card cannot change the dispatch table."""
    return deepcopy(dict(_SPECS))


def validate_inputs(operation, inputs):
    if type(operation) is not str or operation not in _SPECS:
        raise ValueError("Unknown installed operation")
    spec = _SPECS[operation]
    fields = spec["input_contract"]["fields"]
    if type(inputs) is not dict or set(inputs) - fields.keys():
        raise ValueError("Unknown operation input fields")
    if not set(spec["input_contract"]["required"]) <= inputs.keys():
        raise ValueError("Missing required operation inputs")
    resolved = deepcopy({**spec["defaults"], **inputs})
    for key, value in resolved.items():
        kind = fields[key]
        valid = False
        if kind in {"text", "id", "number", "mode", "profile"}:
            valid = type(value) is str and 0 < len(value.encode("utf-8")) <= (1024 if kind == "id" else 8192)
            if valid and kind == "number":
                number(value)
            if kind == "mode":
                valid = valid and value in ("waqf", "wasl")
            if kind == "profile":
                valid = valid and value in ("surface_v1", "stem_exact_v1")
        elif kind in {"state", "weight"}:
            valid = type(value) is int and 0 <= value <= (96 if kind == "state" else 16)
        elif kind == "texts":
            valid = (type(value) is list and 2 <= len(value) <= 8 and
                     all(type(t) is str and 0 < len(t.encode("utf-8")) <= 8192 for t in value))
        elif kind == "object":
            valid = type(value) is dict  # Nested schema belongs to the existing owner.
        if not valid:
            raise ValueError(f"Invalid {key}: expected {kind}")
    return resolved


def _encode(text):
    return numeric_payload(encode_cells(parse_word(text)))


def execute(operation, inputs):
    """Execute a fixed adapter; do not interpret a retrieved path or symbol."""
    values = validate_inputs(operation, inputs)
    owner_check = None
    try:
        if operation == "encode":
            result = _encode(values["text"])
        elif operation == "decode":
            result = numeric_payload(number(values["number"]))
        elif operation == "contrast":
            observations = []
            for text in values["texts"]:
                try:
                    observations.append({"raw_text": text, "result": _encode(text), "status": "ENCODED"})
                except NabtError as error:
                    observations.append({"raw_text": text, "result": error.as_dict(), "status": error.status})
            complete = all(row["status"] == "ENCODED" for row in observations)
            result = {"status": "ENCODED" if complete else "INCOMPLETE", "observations": observations,
                "all_distinct": len({r["result"]["numeric_code_hex"] for r in observations}) == len(observations)
                    if complete else None, "semantic_roles_established": False}
        elif operation in ("effect", "compose_effects"):
            texts = [values["text"]] if operation == "effect" else values["texts"]
            machine = Machine()
            effects = [machine.effect(parse_word(t)) for t in texts]
            effect = effects[0]
            for following in effects[1:]:
                effect = compose_effects(effect, following)
            result = effect.as_dict()
        elif operation in ("analyse", "count", "rank", "unrank"):
            machine = Machine(values["mode"])
            state = values["start_state"]
            if operation == "analyse":
                result = machine.analyse(parse_word(values["text"]), state).as_dict()
            elif operation == "count":
                result = {"count": str(machine.count(values["weight"], state))}
            elif operation == "rank":
                result = {**_encode(values["text"]), "rank": str(machine.rank(parse_word(values["text"]), state))}
            else:
                result = numeric_payload(encode_cells(machine.unrank(values["weight"], number(values["rank"]), state)))
        elif operation == "derivation":
            from nabt.derivation import read_derivation, verify_derivation
            result = read_derivation(**values)
            owner_check = verify_derivation(result, **values)
        elif operation == "person":
            from nabt.person_evidence import person_candidates
            rows = person_candidates(values["text"])
            result = {"candidates": rows, "status": "SOURCE_QUALIFIED_ALTERNATIVES" if rows else "DEFER",
                      "authority": "MORPHOLOGICAL_CANDIDATES_NOT_CASE_ROLE_OR_REFERENCE"}
        elif operation == "program":
            from nabt.program import compile_request, execute_program, verify_execution
            expected = compile_request(values["request"])
            result = execute_program(expected)
            owner_check = verify_execution(result)
            if result["program"] != expected.packet():
                raise ValueError("Owner receipt is not bound to the independent request")
        else:  # validate_inputs proved this is the one remaining installed id.
            from tools.lexical_training.teaching import run_lesson, verify_lesson
            result = run_lesson(values["lesson"])
            owner_check = verify_lesson(result, expected_lesson=values["lesson"])
        return {"execution_status": "EXECUTED", "effective_inputs": values,
                "owner_result": result, "owner_verification": owner_check,
                "scope": _SPECS[operation]["scope"], "semantic_rank_promoted": False}
    except NabtError as error:
        return {"execution_status": "RESOURCE_LIMIT" if error.code == "RESOURCE_LIMIT" else "OWNER_ERROR",
                "effective_inputs": values, "owner_result": error.as_dict(), "owner_verification": None,
                "scope": _SPECS[operation]["scope"], "semantic_rank_promoted": False}
