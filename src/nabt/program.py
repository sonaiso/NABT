"""A bounded numeric instruction language for NABT's checked vertical paths.

Programs contain inert data, never Python, file paths, proof flags or laws.
The compiler supplies instruction structure; every execution replays installed
readers and evidence policies. A program number is reversible transport, not a
theorem. Execution receipts are checked by re-execution, not by trusting hashes.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from enum import IntEnum
from hashlib import sha256
from typing import Any

from .errors import NabtError, natural, resource_limit

ABI = 1
PROGRAM_DOMAIN = "nabt.program.canonical-json-utf8.sentinel256.v1"
EXECUTION_DOMAIN = "nabt.execution.v1"
MAX_PROGRAM_BYTES = 65536
MAX_INSTRUCTIONS = 128
MAX_LITERAL_BYTES = 32768
MAX_RECEIPT_BYTES = 2 * 1024 * 1024
MAX_RECEIPT_NODES = 100000
_RECEIPT_FIELDS = {
    "execution_domain",
    "program",
    "installed_contracts",
    "run_status",
    "trace",
    "final_state",
    "result",
    "semantic_or_real_world_judgment",
}


class Opcode(IntEnum):
    READ_UTF8 = 1
    WORD_SHAPE = 2
    START_LEARNER = 10
    OBSERVE_SOURCE = 11
    WITHDRAW_SOURCE = 12
    QUERY_CUE = 13
    APPLICATION_OBLIGATIONS = 20
    START_TEXT = 30
    ADD_TEXT = 31
    REMOVE_TEXT = 32
    QUERY_TEXT = 33
    REPLACE_TEXT = 34
    START_ARABIC = 35


CONTRACTS = {
    Opcode.READ_UTF8: "exact strict UTF-8; original bytes retained",
    Opcode.WORD_SHAPE: "installed shape law; missing marks retain alternatives",
    Opcode.START_LEARNER: "complete declared signed-conjunction language",
    Opcode.OBSERVE_SOURCE: "source replay before a property constrains learning",
    Opcode.WITHDRAW_SOURCE: "recompute from the complete declared language",
    Opcode.QUERY_CUE: "all surviving rules and missing-feature completions",
    Opcode.APPLICATION_OBLIGATIONS: "source-defined prerequisites; no supplied evidence bits",
    Opcode.START_TEXT: "versioned controlled-Arabic theory; exact scope; no world-truth promotion",
    Opcode.ADD_TEXT: "reparse complete new source; exact spans; atomic conditional premise admission",
    Opcode.REMOVE_TEXT: "withdraw source and rebuild all dependent conditional consequences",
    Opcode.QUERY_TEXT: "parse a new ground question; signed support and conflict-clean proof gate",
    Opcode.REPLACE_TEXT: "explicit source revision; preserve old source unless replacement is admitted",
    Opcode.START_ARABIC: "installed Arabic syntax law; preserve speech force, cues and unresolved readings",
}


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8", "strict")
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise NabtError(
            "INVALID_PROGRAM_DATA", "Data must be bounded strict Unicode JSON"
        ) from exc


def _digest(value: Any) -> str:
    return sha256(_canonical(value)).hexdigest()


def _text(value: object, name: str, *, maximum: int = MAX_LITERAL_BYTES) -> str:
    if type(value) is not str:
        raise NabtError("INVALID_PROGRAM_DATA", f"{name} must be a string")
    if len(value) > maximum:
        raise resource_limit(f"{name} exceeds the text budget", maximum_bytes=maximum)
    try:
        raw = value.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise NabtError(
            "INVALID_UNICODE", f"{name} contains an invalid Unicode scalar"
        ) from exc
    if len(raw) > maximum:
        raise resource_limit(f"{name} exceeds the text budget", maximum_bytes=maximum)
    return value


def _name(value: object, field: str) -> str:
    value = _text(value, field, maximum=128)
    if not value.strip():
        raise NabtError("INVALID_PROGRAM_DATA", f"{field} must be nonempty")
    return value


def _keys(value: object, required: set[str], optional: set[str] = frozenset()) -> dict:
    if (
        type(value) is not dict
        or not required <= value.keys()
        or value.keys() - required - optional
    ):
        raise NabtError(
            "INVALID_PROGRAM_FIELDS",
            "Required fields are missing or unrecognized fields were supplied",
        )
    return value


def _raw_hex(value: object) -> bytes:
    text = _text(value, "UTF-8 bytes", maximum=2 * MAX_LITERAL_BYTES)
    if len(text) % 2 or not re.fullmatch(r"[0-9a-f]*", text):
        raise NabtError(
            "NONCANONICAL_BYTES", "Raw bytes require lowercase even-length hexadecimal"
        )
    return bytes.fromhex(text)


@dataclass(frozen=True, slots=True)
class Instruction:
    opcode: int
    operands: tuple = ()

    def __post_init__(self) -> None:
        natural(self.opcode, "opcode")
        if (
            self.opcode not in {int(op) for op in Opcode}
            or type(self.operands) is not tuple
        ):
            raise NabtError("INVALID_INSTRUCTION", "Unknown opcode or mutable operands")
        args = self.operands
        if self.opcode == Opcode.READ_UTF8:
            if len(args) != 1:
                raise NabtError(
                    "INVALID_INSTRUCTION", "READ_UTF8 expects exact byte data"
                )
            _raw_hex(args[0])
        elif self.opcode == Opcode.WORD_SHAPE:
            if (
                len(args) != 1
                or type(args[0]) is not str
                or args[0] not in {"waqf", "wasl"}
            ):
                raise NabtError(
                    "INVALID_INSTRUCTION", "WORD_SHAPE expects a declared mode"
                )
        elif self.opcode == Opcode.START_LEARNER:
            if len(args) != 1:
                raise NabtError("INVALID_INSTRUCTION", "START_LEARNER expects degree")
            natural(args[0], "degree", maximum=3)
        elif self.opcode in {Opcode.OBSERVE_SOURCE, Opcode.WITHDRAW_SOURCE}:
            if len(args) != 1:
                raise NabtError(
                    "INVALID_INSTRUCTION", "Evidence instructions expect one record ID"
                )
            _name(args[0], "record_id")
        elif self.opcode == Opcode.QUERY_CUE:
            if (
                len(args) != 2
                or type(args[0]) is not tuple
                or not 1 <= len(args[0]) <= 2
            ):
                raise NabtError(
                    "INVALID_INSTRUCTION",
                    "QUERY_CUE expects one or two literal cue parts and a query ID",
                )
            for part in args[0]:
                _text(part, "cue_part", maximum=128)
            _name(args[1], "query_id")
        elif self.opcode in {Opcode.START_TEXT, Opcode.START_ARABIC}:
            if len(args) != 1:
                raise NabtError("INVALID_INSTRUCTION", "START_TEXT expects an exact scope")
            from .text_ir import require_name

            require_name(_name(args[0], "scope"), "scope")
        elif self.opcode in {Opcode.ADD_TEXT, Opcode.REPLACE_TEXT}:
            if len(args) != 2:
                raise NabtError("INVALID_INSTRUCTION", "Text admission expects source ID and exact bytes")
            source_id = _name(args[0], "source_id")
            if re.fullmatch(r"[a-z][a-z0-9_]*", source_id) is None:
                raise NabtError("INVALID_SOURCE_ID", "Source ID must be a bounded lowercase identifier")
            _raw_hex(args[1])
        elif self.opcode == Opcode.REMOVE_TEXT:
            if len(args) != 1:
                raise NabtError("INVALID_INSTRUCTION", "REMOVE_TEXT expects a source ID")
            source_id = _name(args[0], "source_id")
            if re.fullmatch(r"[a-z][a-z0-9_]*", source_id) is None:
                raise NabtError("INVALID_SOURCE_ID", "Source ID must be a bounded lowercase identifier")
        elif self.opcode == Opcode.QUERY_TEXT:
            if len(args) != 2:
                raise NabtError("INVALID_INSTRUCTION", "QUERY_TEXT expects question bytes and a query ID")
            _raw_hex(args[0])
            _name(args[1], "query_id")
        elif args:
            raise NabtError(
                "INVALID_INSTRUCTION",
                "APPLICATION_OBLIGATIONS has no supplied fact operands",
            )

    def as_list(self) -> list:
        return [
            self.opcode,
            *[list(x) if type(x) is tuple else x for x in self.operands],
        ]

    @property
    def number(self) -> int:
        return int.from_bytes(b"\x01" + _canonical(self.as_list()), "big")


@dataclass(frozen=True, slots=True)
class Program:
    instructions: tuple[Instruction, ...]

    def __post_init__(self) -> None:
        if type(self.instructions) is not tuple or not self.instructions:
            raise NabtError(
                "INVALID_PROGRAM",
                "A program needs an immutable nonempty instruction tuple",
            )
        if len(self.instructions) > MAX_INSTRUCTIONS:
            raise resource_limit(
                "Program exceeds its instruction budget", maximum=MAX_INSTRUCTIONS
            )
        for item in self.instructions:
            if type(item) is not Instruction:
                raise NabtError(
                    "INVALID_PROGRAM", "Only inert Instruction records are accepted"
                )
            Instruction(item.opcode, item.operands)
        first = self.instructions[0].opcode
        if first == Opcode.READ_UTF8:
            if len(self.instructions) != 2 or self.instructions[1].opcode not in {
                Opcode.WORD_SHAPE,
                Opcode.APPLICATION_OBLIGATIONS,
            }:
                raise NabtError(
                    "PROGRAM_TYPE_ERROR",
                    "Exact text must feed one declared text consumer",
                )
        elif first == Opcode.START_LEARNER:
            active: set[str] = set()
            query_ids: dict[str, tuple[str, ...]] = {}
            for step in self.instructions[1:]:
                if step.opcode == Opcode.OBSERVE_SOURCE:
                    active.add(step.operands[0])
                elif step.opcode == Opcode.WITHDRAW_SOURCE:
                    if step.operands[0] not in active:
                        raise NabtError(
                            "PROGRAM_TYPE_ERROR",
                            "Cannot withdraw an inactive source record",
                        )
                    active.remove(step.operands[0])
                elif step.opcode == Opcode.QUERY_CUE:
                    cue, query_id = step.operands
                    previous = query_ids.get(query_id)
                    if previous is not None and previous != cue:
                        raise NabtError(
                            "QUERY_ID_REUSED",
                            "Changed input needs a new query identity",
                        )
                    query_ids[query_id] = cue
                else:
                    raise NabtError(
                        "PROGRAM_TYPE_ERROR",
                        "Learner programs accept only evidence and literal queries",
                    )
        elif first in {Opcode.START_TEXT, Opcode.START_ARABIC}:
            active_sources: set[str] = set()
            text_queries: dict[str, str] = {}
            for step in self.instructions[1:]:
                if step.opcode == Opcode.ADD_TEXT:
                    if step.operands[0] in active_sources:
                        raise NabtError("SOURCE_ID_REUSED", "Replace an active source explicitly")
                    active_sources.add(step.operands[0])
                elif step.opcode in {Opcode.REMOVE_TEXT, Opcode.REPLACE_TEXT}:
                    if step.operands[0] not in active_sources:
                        raise NabtError("INACTIVE_TEXT_SOURCE", "Text source has not been admitted by this program")
                    if step.opcode == Opcode.REMOVE_TEXT:
                        active_sources.remove(step.operands[0])
                elif step.opcode == Opcode.QUERY_TEXT:
                    raw, query_id = step.operands
                    if query_id in text_queries and text_queries[query_id] != raw:
                        raise NabtError("QUERY_ID_REUSED", "Changed question needs a new query identity")
                    text_queries[query_id] = raw
                else:
                    raise NabtError("PROGRAM_TYPE_ERROR", "Text theories accept only text events")
        else:
            raise NabtError(
                "PROGRAM_TYPE_ERROR", "A program must establish its input domain first"
            )
        if len(self.to_bytes()) > MAX_PROGRAM_BYTES:
            raise resource_limit(
                "Program exceeds the wire budget", maximum_bytes=MAX_PROGRAM_BYTES
            )

    def to_bytes(self) -> bytes:
        return _canonical(
            {"abi": ABI, "code": [x.as_list() for x in self.instructions]}
        )

    @property
    def number(self) -> int:
        # The sentinel preserves leading zero bytes and length. Only numbers
        # whose decoded payload is canonical well-typed code are executable.
        return int.from_bytes(b"\x01" + self.to_bytes(), "big")

    @property
    def identity(self) -> str:
        return sha256(self.to_bytes()).hexdigest()

    @classmethod
    def from_bytes(cls, raw: bytes) -> Program:
        if type(raw) is not bytes:
            raise NabtError(
                "INVALID_PROGRAM", "Program wire data must be immutable bytes"
            )
        if len(raw) > MAX_PROGRAM_BYTES:
            raise resource_limit(
                "Program exceeds the wire budget", maximum_bytes=MAX_PROGRAM_BYTES
            )

        def pairs(items):
            out = {}
            for key, value in items:
                if key in out:
                    raise NabtError(
                        "DUPLICATE_JSON_KEY", "Program contains a duplicate JSON key"
                    )
                out[key] = value
            return out

        try:
            value = json.loads(
                raw.decode("utf-8", "strict"),
                object_pairs_hook=pairs,
                parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")),
            )
        except (UnicodeError, ValueError, RecursionError) as exc:
            if isinstance(exc, NabtError):
                raise
            raise NabtError(
                "INVALID_PROGRAM", "Program is not strict UTF-8 JSON"
            ) from exc
        _keys(value, {"abi", "code"})
        if (
            type(value["abi"]) is not int
            or value["abi"] != ABI
            or type(value["code"]) is not list
        ):
            raise NabtError(
                "UNSUPPORTED_PROGRAM_ABI", "Program ABI or code type is unsupported"
            )
        if not value["code"]:
            raise NabtError(
                "INVALID_PROGRAM", "A program must contain at least one instruction"
            )
        if len(value["code"]) > MAX_INSTRUCTIONS:
            raise resource_limit("Instruction count is outside the executable budget")
        instructions = []
        for row in value["code"]:
            if type(row) is not list or not row:
                raise NabtError(
                    "INVALID_INSTRUCTION", "Each instruction is a nonempty array"
                )
            operands = tuple(tuple(x) if type(x) is list else x for x in row[1:])
            instructions.append(Instruction(row[0], operands))
        result = cls(tuple(instructions))
        if result.to_bytes() != raw:
            raise NabtError(
                "NONCANONICAL_PROGRAM",
                "Wire bytes must match the canonical program encoding",
            )
        return result

    @classmethod
    def from_number(cls, number: int) -> Program:
        natural(number, "program_number")
        if number.bit_length() > 8 * (MAX_PROGRAM_BYTES + 1):
            raise resource_limit("Program number exceeds the wire budget")
        raw = number.to_bytes((number.bit_length() + 7) // 8, "big")
        if not raw or raw[0] != 1:
            raise NabtError("NONCANONICAL_PROGRAM_NUMBER", "Missing program sentinel")
        return cls.from_bytes(raw[1:])

    def packet(self) -> dict:
        return {
            "domain": PROGRAM_DOMAIN,
            "abi": ABI,
            "program_sha256": self.identity,
            "program_number_hex": hex(self.number),
            "wire_hex": self.to_bytes().hex(),
            "instruction_count": len(self.instructions),
            "authority": "EXECUTABLE_REQUEST_ONLY",
        }


def compile_request(request: dict) -> Program:
    """Compile scoped tasks; new text is interpreted, never supplied as trusted IR."""
    if type(request) is not dict or type(request.get("task")) is not str:
        raise NabtError("INVALID_REQUEST", "A request needs a declared task")
    task = request["task"]
    if task in {"word_shape", "noun_obligations"}:
        _keys(request, {"task", "text"}, {"mode"} if task == "word_shape" else set())
        text = _text(request["text"], "text")
        consumer = (
            Instruction(int(Opcode.WORD_SHAPE), (request.get("mode", "waqf"),))
            if task == "word_shape"
            else Instruction(int(Opcode.APPLICATION_OBLIGATIONS))
        )
        return Program(
            (
                Instruction(int(Opcode.READ_UTF8), (text.encode("utf-8").hex(),)),
                consumer,
            )
        )
    if task in {"text_inquiry", "arabic_inquiry"}:
        _keys(request, {"task", "events"}, {"scope"})
        if type(request["events"]) is not list:
            raise NabtError("INVALID_REQUEST", "Text events must be an array")
        if len(request["events"]) >= MAX_INSTRUCTIONS:
            raise resource_limit("Too many text events")
        starter = Opcode.START_ARABIC if task == "arabic_inquiry" else Opcode.START_TEXT
        steps = [Instruction(int(starter), (request.get("scope", "default"),))]
        for event in request["events"]:
            if type(event) is not dict or type(event.get("op")) is not str:
                raise NabtError("INVALID_REQUEST", "Each text event needs an operation")
            op = event["op"]
            if op in {"add", "replace"}:
                _keys(event, {"op", "source_id", "text"})
                raw = _text(event["text"], "source text").encode("utf-8").hex()
                steps.append(Instruction(int(Opcode.ADD_TEXT if op == "add" else Opcode.REPLACE_TEXT),
                                         (event["source_id"], raw)))
            elif op == "remove":
                _keys(event, {"op", "source_id"})
                steps.append(Instruction(int(Opcode.REMOVE_TEXT), (event["source_id"],)))
            elif op == "query":
                _keys(event, {"op", "text", "query_id"})
                raw = _text(event["text"], "question text").encode("utf-8").hex()
                steps.append(Instruction(int(Opcode.QUERY_TEXT), (raw, event["query_id"])))
            else:
                raise NabtError("UNSUPPORTED_TEXT_EVENT", "Only add, replace, remove and query are installed")
        return Program(tuple(steps))
    if task != "source_learning":
        raise NabtError(
            "UNSUPPORTED_TASK", "The requested interpreter is not installed"
        )
    _keys(request, {"task", "events"}, {"degree"})
    if type(request["events"]) is not list:
        raise NabtError("INVALID_REQUEST", "Events must be an array")
    if len(request["events"]) >= MAX_INSTRUCTIONS:
        raise resource_limit("Too many learning events")
    steps = [Instruction(int(Opcode.START_LEARNER), (request.get("degree", 1),))]
    for event in request["events"]:
        if type(event) is not dict:
            raise NabtError("INVALID_REQUEST", "Events must be records")
        op = event.get("op")
        if type(op) is not str:
            raise NabtError("INVALID_REQUEST", "Event operation must be a string")
        if op in {"observe", "withdraw"}:
            _keys(event, {"op", "record_id"})
            steps.append(
                Instruction(
                    int(
                        Opcode.OBSERVE_SOURCE
                        if op == "observe"
                        else Opcode.WITHDRAW_SOURCE
                    ),
                    (event["record_id"],),
                )
            )
        elif op == "query":
            _keys(event, {"op", "cue", "query_id"})
            if type(event["cue"]) is not list:
                raise NabtError("INVALID_REQUEST", "Cue parts must be an array")
            steps.append(
                Instruction(
                    int(Opcode.QUERY_CUE), (tuple(event["cue"]), event["query_id"])
                )
            )
        else:
            raise NabtError(
                "UNSUPPORTED_EVENT",
                "Only source observation, withdrawal and literal query are installed",
            )
    return Program(tuple(steps))


def _shape(text: str, mode: str) -> dict:
    from .alphabet import parse_word
    from .ambiguity import AmbiguityForest
    from .certificates import issue_certificate
    from .machine import Machine

    forest = AmbiguityForest(text, mode)
    report = forest.as_dict()
    if forest.missing_positions:
        report["status"] = "PENDING" if forest.total else "REJECTED_BY_DECLARED_LAW"
    elif forest.total:
        cells = parse_word(text)
        report.update(
            status="LICENSED_SHAPE",
            certificate=issue_certificate(cells, mode, source_text=text),
        )
    else:
        report.update(
            status="REJECTED_BY_DECLARED_LAW",
            analysis=Machine(mode).analyse(parse_word(text)).as_dict(),
        )
    return report


def _application(text: str, pilot) -> dict:
    from .learning.arabic_six_nouns import APPLICATION_PREDICATES, POLICY_ID
    from .obligations import (
        And,
        Atom,
        Proposition,
        PropositionRegistry,
        compile_obligations,
    )

    assessment = pilot.application_assessment(text)
    result = asdict(assessment)
    result.update(scope="SIX_NOUN_PREREQUISITE_FRAGMENT", status="PENDING")
    if not assessment.required:
        result["status"] = "NO_MATCHING_RULE"
        return result
    source = sha256(text.encode("utf-8")).hexdigest()
    propositions = tuple(
        Proposition(
            name,
            source,
            source,
            "tamam-condition-fragment",
            POLICY_ID,
            "nabt.six-noun-conditions.v1",
            POLICY_ID,
        )
        for i, name in enumerate(APPLICATION_PREDICATES)
        if assessment.required & (1 << i)
    )
    registry = PropositionRegistry(propositions)
    formula = Atom(propositions[0])
    for proposition in propositions[1:]:
        formula = And(formula, Atom(proposition))
    result["computed_obligations"] = (
        compile_obligations(formula, registry).evaluate().as_dict()
    )
    result["outside_fragment_requirements"] = [
        "nominality",
        "singularity",
        "non_diminutive_form",
        "requested_case",
        "resolved_semantic_reading",
    ]
    return result


def execute_program(program: Program) -> dict:
    """Execute only checked instruction records, returning a replayable trace."""
    if type(program) is not Program:
        raise NabtError("INVALID_PROGRAM", "Expected the concrete inert Program format")
    program = Program.from_bytes(program.to_bytes())  # Revalidate at consumption.
    state: dict = {"stage": "start"}
    trace: list[dict] = []
    pilot = session = theory = None
    theory_scope = "default"
    active: dict = {}
    observed_ids: set[str] = set()
    text = ""
    stopped = False
    for pc, instruction in enumerate(program.instructions):
        previous_state = state
        before = _digest(state)
        op, args = instruction.opcode, instruction.operands
        try:
            if op == Opcode.READ_UTF8:
                raw = _raw_hex(args[0])
                try:
                    text = raw.decode("utf-8", "strict")
                except UnicodeError as exc:
                    raise NabtError(
                        "INVALID_UTF8", "Byte stream is not Unicode scalar UTF-8"
                    ) from exc
                result = {
                    "status": "READ",
                    "scope": "EXACT_SOURCE_BYTES",
                    "source_sha256": sha256(raw).hexdigest(),
                    "byte_length": len(raw),
                    "raw_utf8_hex": raw.hex(),
                    "text": text,
                }
                state = {"stage": "text", "source_sha256": result["source_sha256"]}
            elif op == Opcode.WORD_SHAPE:
                result = _shape(text, args[0])
                state = {"stage": "shape", "result": result}
            elif op == Opcode.APPLICATION_OBLIGATIONS:
                from .learning import default_pilot

                pilot = default_pilot()
                result = _application(text, pilot)
                state = {"stage": "obligations", "result": result}
            elif op == Opcode.START_LEARNER:
                from .learning import GuardLanguage, LearningSession, default_pilot
                from .learning.arabic_six_nouns import observation_schema

                pilot = default_pilot()
                observed_ids = {record.record_id for record in pilot.observed_records()}
                session = LearningSession(GuardLanguage(observation_schema(), args[0]))
                result = {
                    "status": "READY",
                    "scope": "DECLARED_OBSERVATIONAL_GUARDS",
                    "hypothesis_count": session.language.count,
                    "count_by_degree": list(session.language.count_by_degree),
                }
            elif op == Opcode.OBSERVE_SOURCE:
                if args[0] not in observed_ids:
                    raise NabtError(
                        "RECORD_OUTSIDE_OBSERVATION_POLICY",
                        "Only the installed actual-example records train this schema",
                    )
                proposal = pilot.propose(args[0])
                checked = pilot.check(proposal)
                observation = pilot.to_observation(
                    proposal
                )  # Fresh replay, not the receipt.
                if observation is None or checked.record is None:
                    raise NabtError(
                        "SOURCE_REPLAY_FAILED",
                        "The proposed property was not established",
                    )
                session = session.observe(observation)
                active[args[0]] = observation
                record = checked.record
                result = {
                    "status": "OBSERVED",
                    "scope": "REPLAYED_LITERAL_SOURCE_PROPERTY",
                    "record_id": args[0],
                    "binding": asdict(record.binding),
                    "context_span": asdict(record.context_span),
                    "cue_spans": [asdict(x) for x in record.cue_spans],
                    "marker_span": asdict(record.marker_span),
                    "cue": record.cue,
                    "target": record.target,
                    "known": record.known,
                    "value": record.value,
                    "label_marker_is_waw": record.label,
                }
            elif op == Opcode.WITHDRAW_SOURCE:
                if args[0] not in active:
                    raise NabtError(
                        "INACTIVE_EVIDENCE",
                        "The source record is not active in this execution",
                    )
                session = session.revise_evidence(active.pop(args[0]).evidence_id, None)
                result = {
                    "status": "WITHDRAWN",
                    "scope": "EVIDENCE_REVISION",
                    "record_id": args[0],
                    "source_was_not_declared_false": True,
                }
            elif op in {Opcode.START_TEXT, Opcode.START_ARABIC}:
                from .semantics import SemanticKernel
                from .text_ir import LANGUAGE_ID, READER_VERSION

                if op == Opcode.START_ARABIC:
                    from .arabic_reader import LANGUAGE_ID, READER_VERSION
                theory = SemanticKernel(language_id=LANGUAGE_ID)
                theory_scope = args[0]
                result = {"status": "READY", "scope": theory_scope,
                          "language_id": LANGUAGE_ID, "reader_version": READER_VERSION,
                          "world_truth": "NOT_ESTABLISHED"}
            elif op in {Opcode.ADD_TEXT, Opcode.REPLACE_TEXT}:
                raw = _raw_hex(args[1])
                if op == Opcode.ADD_TEXT:
                    admission = theory.add_source(raw, source_id=args[0], scope=theory_scope)
                else:
                    admission = theory.replace_source(raw, source_id=args[0], scope=theory_scope)
                result = admission.as_dict()
                if theory.language_id == "nabt.arabic-syntax.v1":
                    from .arabic_reader import read_arabic
                    reading = read_arabic(raw, source_id=args[0], scope=theory_scope)
                    result["reading_steps"] = [step.as_dict() for step in reading.steps]
                if not result.get("accepted", False):
                    result.setdefault("status", "DEFER")
                    stopped = True
            elif op == Opcode.REMOVE_TEXT:
                result = theory.remove_source(args[0]).as_dict()
            elif op == Opcode.QUERY_TEXT:
                raw = _raw_hex(args[0])
                try:
                    question = raw.decode("utf-8", "strict")
                except UnicodeError as exc:
                    raise NabtError("INVALID_UTF8", "Question is not strict UTF-8") from exc
                result = theory.query(question, scope=theory_scope).as_dict()
                result["query_id"] = args[1]
                result["query_source_sha256"] = sha256(raw).hexdigest()
                if theory.language_id == "nabt.arabic-syntax.v1":
                    from .text_ir import span_dict
                    interpreted = theory.read_query(raw, scope=theory_scope)
                    result["query_reading"] = {"language_id": theory.language_id,
                        "atom": interpreted.atom.as_dict(), "span": span_dict(interpreted.span),
                        "analysis_id": interpreted.analysis_id,
                        "component_spans": [span_dict(s) for s in interpreted.component_spans],
                        "context_program_sha256": result["program_sha256"],
                        "authority": "QUESTION_ONLY"}
            else:
                from .learning.arabic_six_nouns import (
                    observation_schema,
                    read_observed_cue,
                )
                from .learning.finite_guard import FeatureCase

                cue, query_id = args
                schema = observation_schema()
                index = read_observed_cue(cue)
                identity = _digest(("literal-query", query_id, cue, schema.fingerprint))
                case = FeatureCase(
                    "query:" + query_id,
                    identity,
                    schema.fingerprint,
                    schema.width,
                    0 if index is None else 7,
                    0 if index is None else 1 << index,
                )
                prediction = session.predict(case)
                result = {
                    "status": prediction.status.value,
                    "scope": "CONDITIONAL_LITERAL_CUE_RELATION",
                    "query_id": query_id,
                    "cue": list(cue),
                    "known": case.known,
                    "value": case.value,
                    "possible_marker_is_waw": list(prediction.possible),
                    "missing_predicates": list(prediction.missing_predicates),
                    "witness_rule_codes": list(prediction.witness_rules),
                    "reason": prediction.reason,
                    "not_a_general_grammatical_case_analysis": True,
                }
            if session is not None:
                state = {
                    "stage": "learner",
                    "schema_id": session.language.schema.fingerprint,
                    "evidence_revision": session.revision,
                    "active_source_records": sorted(active),
                    "surviving_rule_codes": sorted(
                        rule.code for rule in session.survivors
                    ),
                    "pending_evidence": list(session.pending),
                }
                result["learning_state"] = state
            if theory is not None:
                state = {"stage": "text_theory", "scope": theory_scope,
                         "theory": theory.snapshot()}
        except NabtError as exc:
            result = exc.as_dict()
            state = {**previous_state, "stage": "stopped", "reason": result}
            stopped = True
        except (ValueError, KeyError) as exc:
            # A source or definition mismatch is a failed contract, never a new
            # linguistic counterexample. Inputs are bounded before execution.
            result = {
                "status": "DEFER",
                "code": "INSTALLED_CONTRACT_FAILED",
                "message": str(exc),
            }
            state = {**previous_state, "stage": "stopped", "reason": result}
            stopped = True
        if stopped and theory is not None:
            # Preserve the current theory on failed input; a failed replacement
            # must not make its already admitted sources disappear from the
            # receipt. If reporting itself exceeds a bound, retain the last
            # completed state and label it explicitly as historical.
            state = {**state, "stage": "stopped", "scope": theory_scope, "reason": result}
            try:
                state["theory"] = theory.snapshot()
                state["snapshot_status"] = "CURRENT"
            except (NabtError, ValueError, KeyError) as snapshot_error:
                state["snapshot_status"] = "LAST_COMPLETED_INSTRUCTION"
                state["snapshot_error"] = (
                    snapshot_error.as_dict() if isinstance(snapshot_error, NabtError)
                    else {"status": "DEFER", "code": "INSTALLED_CONTRACT_FAILED"}
                )
        trace.append(
            {
                "pc": pc,
                "opcode": op,
                "instruction_number_hex": hex(instruction.number),
                "contract": CONTRACTS[Opcode(op)],
                "before_sha256": before,
                "after_sha256": _digest(state),
                "result": result,
            }
        )
        if sum(len(_canonical(item)) for item in trace) > MAX_RECEIPT_BYTES // 2:
            raise resource_limit("Execution trace exceeds its replay budget",
                                 maximum_bytes=MAX_RECEIPT_BYTES)
        if stopped:
            break
    from .learning.arabic_six_nouns import (
        APPROVED_SOURCE_PINS,
        CHECKER_VERSION,
        POLICY_ID,
    )
    from .machine import EXPECTED_TABLE_SHA256

    receipt = {
        "execution_domain": EXECUTION_DOMAIN,
        "program": program.packet(),
        "installed_contracts": {
            "shape_table_sha256": EXPECTED_TABLE_SHA256,
            "source_checker": CHECKER_VERSION,
            "source_policy": POLICY_ID,
            "source_pins": dict(APPROVED_SOURCE_PINS),
        },
        "run_status": "STOPPED" if stopped else "COMPLETED",
        "trace": trace,
        "final_state": state,
        "result": trace[-1]["result"],
        "semantic_or_real_world_judgment": "NOT_ESTABLISHED",
    }
    if theory is not None:
        from importlib.resources import files
        from .text_ir import LANGUAGE_ID, READER_VERSION

        if theory.language_id == "nabt.arabic-syntax.v1":
            from .arabic_reader import READER_VERSION
        receipt["installed_contracts"]["text_language"] = theory.language_id
        receipt["installed_contracts"]["text_reader"] = READER_VERSION
        receipt["installed_contracts"]["text_implementation_sha256"] = {
            name: sha256(files("nabt").joinpath(name).read_bytes()).hexdigest()
            for name in (("text_ir.py", "text_reader.py", "semantics.py") +
                         (("arabic_reader.py",) if theory.language_id == "nabt.arabic-syntax.v1" else ()))
        }
    # Return inert JSON types; CLI and API share the same representation and
    # a receipt emitted by the CLI always fits its verification input budget.
    result = json.loads(_canonical(receipt))
    if (
        len(json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
        > MAX_RECEIPT_BYTES
    ):
        raise resource_limit(
            "Execution receipt exceeds its replay budget",
            maximum_bytes=MAX_RECEIPT_BYTES,
        )
    return result


def _receipt_preflight(receipt: object) -> None:
    _keys(receipt, _RECEIPT_FIELDS)
    stack = [(receipt, 0)]
    nodes = size = 0
    while stack:
        value, depth = stack.pop()
        nodes += 1
        if nodes > MAX_RECEIPT_NODES or depth > 40:
            raise resource_limit("Receipt exceeds its structural budget")
        if type(value) is str:
            if len(value) > MAX_RECEIPT_BYTES:
                raise resource_limit("Receipt exceeds its byte budget")
            try:
                size += len(value.encode("utf-8", "strict")) + 2
                # JSON escapes quotes, slashes and controls even with
                # ensure_ascii=False; budget the actual encoded string.
                size += sum(
                    1 if c in '\\"\b\f\n\r\t' else 5 if ord(c) < 32 else 0
                    for c in value
                )
            except UnicodeError as exc:
                raise NabtError(
                    "INVALID_UNICODE", "Receipt contains invalid Unicode"
                ) from exc
        elif type(value) is dict:
            if len(value) > MAX_RECEIPT_NODES:
                raise resource_limit("Receipt exceeds its structural budget")
            if any(type(key) is not str for key in value):
                raise NabtError("INVALID_RECEIPT", "Receipt keys must be strings")
            if nodes + len(stack) + 2 * len(value) > MAX_RECEIPT_NODES:
                raise resource_limit("Receipt exceeds its structural budget")
            stack.extend((item, depth + 1) for pair in value.items() for item in pair)
            size += 2 + 2 * len(value)
        elif type(value) is list:
            if len(value) > MAX_RECEIPT_NODES:
                raise resource_limit("Receipt exceeds its structural budget")
            if nodes + len(stack) + len(value) > MAX_RECEIPT_NODES:
                raise resource_limit("Receipt exceeds its structural budget")
            stack.extend((item, depth + 1) for item in value)
            size += 2 + len(value)
        elif value is None or type(value) is bool:
            size += 5
        elif type(value) is int and value.bit_length() <= 512:
            size += len(str(value))
        else:
            raise NabtError(
                "INVALID_RECEIPT", "Receipt must contain bounded inert JSON values"
            )
        if size > MAX_RECEIPT_BYTES:
            raise resource_limit(
                "Receipt exceeds its byte budget", maximum_bytes=MAX_RECEIPT_BYTES
            )


def verify_execution(receipt: object) -> dict:
    """Re-execute bounded code and compare the complete canonical receipt."""
    try:
        _receipt_preflight(receipt)
        if type(receipt.get("program")) is not dict:
            raise NabtError(
                "INVALID_RECEIPT", "Execution receipt has no program packet"
            )
        packet = receipt["program"]
        wire = _text(
            packet.get("wire_hex"), "program wire", maximum=2 * MAX_PROGRAM_BYTES
        )
        if not re.fullmatch(r"(?:[0-9a-f]{2})*", wire):
            raise NabtError(
                "NONCANONICAL_PROGRAM",
                "Program wire must be lowercase hexadecimal bytes",
            )
        program = Program.from_bytes(bytes.fromhex(wire))
        fresh = execute_program(program)
        if _canonical(receipt) != _canonical(fresh):
            return {
                "valid": False,
                "status": "REJECT",
                "code": "EXECUTION_REPLAY_MISMATCH",
            }
        return {
            "valid": True,
            "status": "VERIFIED_REPLAY",
            "program_sha256": program.identity,
            "scope": "SAME_INSTALLED_CONTRACTS_AND_INPUT; no proof-rank promotion",
        }
    except NabtError as exc:
        return {"valid": False, **exc.as_dict()}


__all__ = [
    "Instruction",
    "Opcode",
    "Program",
    "compile_request",
    "execute_program",
    "verify_execution",
]
