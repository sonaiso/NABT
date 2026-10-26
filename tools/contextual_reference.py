"""Source-bound reference of an initial occurrence, separate from its clause.

Only installed full-QAC source alternatives and explicit discourse premises
are used. Source extraction and annotation interpretation remain Python
premises; the native law checks bounded scope and complete candidate receipts.
No result here supplies a missing predicate, human motive or external fact.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
from tools import attested_lexical_loader as loader
from tools.epistemic_measurement import InputError, ResourceLimit, strict_loads, wire, digest
from nabt.discourse_context import read_context
from nabt.person_evidence import person_candidates, _match, EXPECTED_TABLE_SHA256 as PERSON_TABLE_SHA256
from nabt.corpus_evidence import buckwalter_to_arabic
from nabt.word_reader import _source, _scan

LAW_ID = "nabt.initial-contextual-reference.v1"
PROFILE_ID = "attested_initial_reference_v1"
NATIVE = ROOT / "formal/.lake/build/bin/contextualReference"
MAX_INPUT_BYTES = 65536
MAX_NATIVE_BYTES = 1024 * 1024
SOURCE_REVIEW = ROOT / "evidence/lexical_loading_v1/source_review.json"
SOURCE_REVIEW_SHA256 = "67e4486ce94f6abacf6e2234c8b07b98ff1296e11dcd71ff2497f76e71c5c0bd"
CONTEXTUAL_REVIEW = ROOT / "evidence/contextual_semantics_v1/source_review.json"
CONTEXTUAL_REVIEW_SHA256 = "3d946d0cb2ad72dfdf030db47ee9b3444d223b50e535ff06a5add464d09b198e"
SCOPE = {
    "reference": "INITIAL_SOURCE_ATTESTED_OCCURRENCE_WITH_EXPLICIT_CONTEXT",
    "source_acquisition": "PYTHON_PINNED_RAW_SOURCE_REPLAY",
    "typed_annotation_interpretation": "DECLARED_PREMISE_NOT_PROVED_BY_LEAN",
    "lexical_inventory": "ALL_SOURCE_BACKED_PERSON_BRIDGE_ALTERNATIVES_FOR_EXACT_SURFACE",
    "sentence_syntax_promoted": False,
    "sentence_readings_promoted": False,
    "context_truth_established": False,
    "world_truth_established": False,
    "hidden_motive_established": False,
    "whole_arabic_complete": False,
    "tawatur_status": "UNKNOWN",
}


def validate_input(request: Any) -> dict:
    if type(request) is not dict or set(request) != {"text", "context"}:
        raise InputError("Initial reference accepts text and explicit context only")
    if type(request["context"]) is not dict:
        raise InputError("Explicit context must be an object")
    if type(request["text"]) is not str or not request["text"].strip():
        raise InputError("Nonempty text required")
    if len(wire(request).encode("utf-8")) > MAX_INPUT_BYTES:
        raise ResourceLimit("Initial reference input byte limit")
    read_context(request["context"])
    return deepcopy(request)


def identity() -> dict:
    if sha256(CONTEXTUAL_REVIEW.read_bytes()).hexdigest() != CONTEXTUAL_REVIEW_SHA256:
        raise InputError("Installed contextual source review digest mismatch")
    if sha256(SOURCE_REVIEW.read_bytes()).hexdigest() != SOURCE_REVIEW_SHA256:
        raise InputError("Installed lexical source review digest mismatch")
    return {"law_id": LAW_ID,
            "source_registry_sha256": digest({"qac_sha256": loader.SOURCE_SHA256,
                "qac_bytes": loader.SOURCE_BYTES, "source_review_sha256": SOURCE_REVIEW_SHA256,
                "contextual_review_sha256": CONTEXTUAL_REVIEW_SHA256,
                "matrix_sha256": loader.MATRIX_SHA256, "person_table_sha256": PERSON_TABLE_SHA256,
                "profile": PROFILE_ID}),
            "runtime_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "native_sha256": sha256(NATIVE.read_bytes()).hexdigest() if NATIVE.is_file() else None}


def _source_alternatives(surface: str, model: Any) -> tuple[list[dict], list[dict]]:
    """Keep all source-backed matching alternatives, including non-reference ones.

    The declared, source-free pronoun inventory is not a QAC alternative. Its
    exclusion is explicit and does not license an unwitnessed personal form.
    """
    if sha256(model.raw).hexdigest() != loader.SOURCE_SHA256:
        raise InputError("Lexical model raw source differs from installed QAC")
    source_rows = []
    records = {}
    for candidate in person_candidates(surface, lexical_model=model):
        supports = candidate.get("supports", [])
        if not supports:
            continue
        record_ids = []
        for support in supports:
            if support.get("source_sha256") != loader.SOURCE_SHA256 or support.get("source_id") != loader.PROFILE_ID:
                raise InputError("Lexical alternative cites an uninstalled source")
            lo, hi = support.get("byte_start"), support.get("byte_end")
            if type(lo) is not int or type(hi) is not int or not 0 <= lo < hi <= len(model.raw):
                raise InputError("Invalid lexical source record boundary")
            raw = model.raw[lo:hi]
            quotation = raw.decode("utf-8")
            if not quotation.strip():
                raise InputError("Empty source record")
            ident = support["record_id"]
            record = {"id": ident, "source_id": loader.PROFILE_ID, "source_sha256": loader.SOURCE_SHA256,
                      "byte_start": lo, "byte_end": hi, "content": quotation,
                      "content_sha256": sha256(raw).hexdigest(), "locator": deepcopy(support["locator"])}
            if ident in records and records[ident] != record:
                raise InputError("Conflicting source record identity")
            records[ident] = record
            record_ids.append(ident)
        profile = candidate.get("person_profile")
        kind = "unsupported"
        if (candidate.get("segmentation_licensed") is True and not candidate.get("attached_pronouns")
                and not candidate.get("obligations") and candidate.get("kind") == "noun"
                and type(profile) is dict):
            if candidate.get("pos") == "PRON" and candidate.get("form_kind") == "separate_pronoun":
                kind = {1: "speaker", 2: "addressee"}.get(profile.get("person"), "unsupported")
            elif candidate.get("pos") == "DEM":
                kind = "deictic"
        source_rows.append({"candidate": deepcopy(candidate), "kind": kind,
                            "profile": deepcopy(profile), "record_ids": record_ids})
    return source_rows, list(records.values())


def _token_with_quote_boundary(text: str) -> dict | None:
    """Byte-tokenize a quote only to certify its noninitial outer-source span."""
    source = _source(text, "contextual_reference_input", "initial_occurrence")
    for segment in _scan(source):
        if segment["kind"] == "written_run":
            return deepcopy(segment)
        if segment["kind"] == "quotation":
            inner = segment["surface"][1:-1]
            offset = segment["span"]["start"] + len(segment["surface"][0].encode("utf-8"))
            inner_source = _source(inner, "contextual_reference_input", "unlicensed_quote_scope")
            for token in _scan(inner_source):
                if token["kind"] == "written_run":
                    answer = deepcopy(token)
                    answer["span"]["start"] += offset
                    answer["span"]["end"] += offset
                    return answer
            return None
    return None


def build_request(request: Any) -> tuple[dict, list[dict]]:
    request = validate_input(request)
    identity()
    token = _token_with_quote_boundary(request["text"])
    if token is None:
        raise InputError("OUT_OF_SCOPE: no nonempty written occurrence")
    loaded = loader.load_attested_lexicon()
    alternatives, records = _source_alternatives(token["surface"], loaded.model)
    context = read_context(request["context"])["value"]
    context = {**context, "speaker": context.get("speaker"), "addressee": context.get("addressee")}
    donors = [{"id": record["id"], "source_id": record["source_id"],
               "source_revision": record["source_sha256"], "start_byte": record["byte_start"],
               "end_byte": record["byte_end"], "record": record["content"]} for record in records]
    readings = []
    for item in alternatives:
        candidate = item["candidate"]
        pos = candidate["pos"] if candidate.get("pos") in ("PRON", "DEM") else "OTHER"
        profile_code = candidate.get("profile_id")
        if item["kind"] == "unsupported" and not (candidate.get("pos") == "PRON"
                and candidate.get("form_kind") == "separate_pronoun"
                and candidate.get("segmentation_licensed") is True
                and not candidate.get("attached_pronouns") and not candidate.get("obligations")):
            pos, profile_code = "OTHER", None
        readings.append({"id": candidate["id"], "pos": pos, "profile_code": profile_code,
                         "target_surface": token["surface"], "source_form": candidate["form"],
                         "donor_ids": list(item["record_ids"])})
    payload = {"source": {"id": "contextual_reference_input", "revision": sha256(request["text"].encode("utf-8")).hexdigest(),
                          "text": request["text"]},
               "occurrence": {"start_byte": token["span"]["start"], "end_byte": token["span"]["end"],
                              "surface": token["surface"]},
               "context": context, "donors": donors, "alternatives": readings, "budget": 256, "proposed": None}
    bindings = [{key: value for key, value in record.items() if key != "content"} for record in records]
    validate_payload(payload)
    return payload, bindings


def _fields(value: Any, fields: set[str], name: str) -> None:
    if type(value) is not dict or set(value) != fields:
        raise InputError(name + " has missing or unexpected fields")


def _text(value: Any, name: str, maximum: int = 4096, *, content: bool = False) -> None:
    if type(value) is not str or not value.strip():
        raise InputError(name + " must be nonempty text")
    if not content and any(ord(char) < 32 for char in value):
        raise InputError(name + " has a control character")
    try:
        if len(value.encode("utf-8")) > maximum:
            raise ResourceLimit(name + " exceeds byte limit")
    except UnicodeError as exc:
        raise InputError(name + " is not UTF-8") from exc


def _natural(value: Any, maximum: int, name: str) -> None:
    if type(value) is not int or value < 0:
        raise InputError(name + " must be a natural integer, not Boolean/float")
    if value > maximum:
        raise ResourceLimit(name + " exceeds bound")


def _list(value: Any, maximum: int, name: str) -> None:
    if type(value) is not list:
        raise InputError(name + " must be an array")
    if len(value) > maximum:
        raise ResourceLimit(name + " exceeds item bound")


def _ids(value: Any, maximum: int, name: str, *, unique: bool = True) -> None:
    _list(value, maximum, name)
    for ident in value:
        _text(ident, name)
    if unique and len(set(value)) != len(value):
        raise InputError("Duplicate " + name)


def _profiles() -> dict:
    from nabt.person_evidence import installed_registry
    return {profile["qac"]: profile for profile in installed_registry()["profiles"]}


DECISIONS = frozenset({"RESOLVED", "AMBIGUOUS", "NO_CANDIDATE", "OPEN_SCOPE", "UNSUPPORTED_READING",
                       "NO_LEXICAL_READING", "OUT_OF_SCOPE", "RESOURCE_LIMIT", "UNRESOLVED_FEATURES"})
RECEIPT_FIELDS = {"status", "reading_ids", "candidate_entity_ids", "bound_entity_id", "reading_results"}


def validate_proposal(value: Any) -> None:
    _fields(value, RECEIPT_FIELDS, "proposed")
    if type(value["status"]) is not str or value["status"] not in DECISIONS:
        raise InputError("Unknown proposed status")
    _ids(value["reading_ids"], 64, "proposed reading IDs", unique=False)
    _ids(value["candidate_entity_ids"], 64, "proposed candidate IDs", unique=False)
    if value["bound_entity_id"] is not None:
        _text(value["bound_entity_id"], "proposed bound entity")
    _list(value["reading_results"], 64, "proposed reading results")
    for row in value["reading_results"]:
        _fields(row, {"id", "status", "candidate_entity_ids", "bound_entity_id"}, "proposed reading")
        _text(row["id"], "reading result ID")
        if type(row["status"]) is not str or row["status"] not in DECISIONS:
            raise InputError("Unknown reading result status")
        _ids(row["candidate_entity_ids"], 64, "reading candidates", unique=False)
        if row["bound_entity_id"] is not None:
            _text(row["bound_entity_id"], "reading bound entity")


def validate_payload(payload: Any) -> dict:
    _fields(payload, {"source", "occurrence", "context", "donors", "alternatives", "budget", "proposed"}, "native input")
    source = payload["source"]
    _fields(source, {"id", "revision", "text"}, "source")
    _text(source["id"], "source ID")
    _text(source["revision"], "source revision")
    _text(source["text"], "source text", MAX_INPUT_BYTES, content=True)
    occurrence = payload["occurrence"]
    _fields(occurrence, {"start_byte", "end_byte", "surface"}, "occurrence")
    raw = source["text"].encode("utf-8")
    for field in ("start_byte", "end_byte"):
        _natural(occurrence[field], len(raw), "occurrence " + field)
    _text(occurrence["surface"], "occurrence surface")
    lo, hi = occurrence["start_byte"], occurrence["end_byte"]
    if not lo < hi or raw[lo:hi] != occurrence["surface"].encode("utf-8"):
        raise InputError("Occurrence does not reproduce its exact source bytes")
    try:
        raw[:lo].decode("utf-8")
        raw[hi:].decode("utf-8")
    except UnicodeError as exc:
        raise InputError("Occurrence splits a UTF-8 character") from exc
    context = payload["context"]
    _fields(context, {"entities", "speaker", "addressee", "deixis", "closed_reference_scope"}, "context")
    read_context({key: value for key, value in context.items() if not (key in ("speaker", "addressee") and value is None)})
    _list(payload["donors"], 256, "donors")
    donor_ids = []
    for donor in payload["donors"]:
        _fields(donor, {"id", "source_id", "source_revision", "start_byte", "end_byte", "record"}, "donor")
        for name in ("id", "source_id", "source_revision"):
            _text(donor[name], "donor " + name)
        _text(donor["record"], "donor record", 4096, content=True)
        for name in ("start_byte", "end_byte"):
            _natural(donor[name], 2**53 - 1, "donor " + name)
        if donor["end_byte"] - donor["start_byte"] != len(donor["record"].encode("utf-8")):
            raise InputError("Donor record byte range differs")
        donor_ids.append(donor["id"])
    if len(donor_ids) != len(set(donor_ids)):
        raise InputError("Duplicate donor identity")
    _list(payload["alternatives"], 64, "alternatives")
    ids = []
    profiles = _profiles()
    for row in payload["alternatives"]:
        _fields(row, {"id", "pos", "profile_code", "target_surface", "source_form", "donor_ids"}, "alternative")
        for key in ("id", "target_surface", "source_form"):
            _text(row[key], "alternative " + key)
        if row["pos"] not in ("PRON", "DEM", "OTHER"):
            raise InputError("Unknown alternative POS")
        if row["profile_code"] is not None and (type(row["profile_code"]) is not str or row["profile_code"] not in profiles):
            raise InputError("Unknown alternative person profile")
        if row["target_surface"] != occurrence["surface"]:
            raise InputError("Alternative belongs to a different occurrence")
        _ids(row["donor_ids"], 256, "alternative donor IDs")
        if not row["donor_ids"] or any(ident not in donor_ids for ident in row["donor_ids"]):
            raise InputError("Alternative lacks retained donor evidence")
        ids.append(row["id"])
    if len(ids) != len(set(ids)):
        raise InputError("Duplicate alternative identity")
    _natural(payload["budget"], 256, "budget")
    if payload["proposed"] is not None:
        validate_proposal(payload["proposed"])
    if len(wire(payload).encode("utf-8")) > MAX_NATIVE_BYTES:
        raise ResourceLimit("Native payload byte limit")
    return payload


def _donors_support(payload: dict, alternative: dict, profile: dict) -> bool:
    expected_code = profile["qac"] if alternative["pos"] == "PRON" else profile["qac"][1:]
    records = {donor["id"]: donor["record"] for donor in payload["donors"]}
    for ident in alternative["donor_ids"]:
        fields = records[ident].strip(" \t\n\r\v\f").split("\t")
        if len(fields) != 4:
            return False
        try:
            if buckwalter_to_arabic(fields[1]) != alternative["source_form"]:
                return False
        except Exception:
            return False
        if not _match(alternative["target_surface"], alternative["source_form"], mutable=()):
            return False
        tokens = fields[3].split("|")
        if fields[2] != alternative["pos"] or "POS:" + alternative["pos"] not in tokens or expected_code not in tokens:
            return False
    return True


def propose(payload: dict) -> dict:
    """Compute the complete finite selector receipt independently of Lean."""
    validate_payload(payload)
    occurrence = payload["occurrence"]
    raw = payload["source"]["text"].encode("utf-8")
    lo, hi = occurrence["start_byte"], occurrence["end_byte"]
    prefix, suffix = raw[:lo], raw[hi:].decode("utf-8")
    empty = {"status": "OUT_OF_SCOPE", "reading_ids": [], "candidate_entity_ids": [],
             "bound_entity_id": None, "reading_results": []}
    if any(byte not in (9, 10, 13, 32) for byte in prefix) or (suffix and suffix[0] not in " \t\r\n.,!?:;،؛؟"):
        return empty
    context = payload["context"]
    entities, alternatives = context["entities"], payload["alternatives"]
    if len(entities) + len(alternatives) > payload["budget"]:
        return {**empty, "status": "RESOURCE_LIMIT"}
    if not alternatives:
        return {**empty, "status": "NO_LEXICAL_READING"}
    profiles = _profiles()
    rows = []
    for alternative in alternatives:
        profile = profiles.get(alternative["profile_code"])
        selected = set()
        supported = False
        source_supported = profile is not None and _donors_support(payload, alternative, profile)
        if source_supported and alternative["pos"] == "PRON" and profile["person"] in (1, 2):
            participant = context["speaker" if profile["person"] == 1 else "addressee"]
            if participant is not None:
                selected.add(participant)
            supported = True
        elif source_supported and alternative["pos"] == "DEM" and profile["person"] == 3:
            for item in context["deixis"]:
                if item["form"] == occurrence["surface"]:
                    selected.update(item["entity_ids"])
            supported = True
        candidates = []
        all_confirmed = True
        if supported:
            gender = ("masculine", "feminine", "unknown")[profile["gender"]]
            number = ("singular", "dual", "plural")[profile["number"]]
            for entity in entities:
                if (entity["id"] in selected
                        and not (gender != "unknown" and entity["gender"] != "unknown" and gender != entity["gender"])
                        and not (entity["number"] != "unknown" and number != entity["number"])):
                    candidates.append(entity["id"])
                    if ((gender != "unknown" and entity["gender"] == "unknown")
                            or entity["number"] == "unknown"):
                        all_confirmed = False
        status = ("UNSUPPORTED_READING" if not supported else "OPEN_SCOPE" if not context["closed_reference_scope"]
                  else "NO_CANDIDATE" if not candidates else "UNRESOLVED_FEATURES" if len(candidates) == 1 and not all_confirmed
                  else "RESOLVED" if len(candidates) == 1 else "AMBIGUOUS")
        rows.append({"id": alternative["id"], "status": status, "candidate_entity_ids": candidates,
                     "bound_entity_id": candidates[0] if status == "RESOLVED" else None})
    union = {ident for row in rows for ident in row["candidate_entity_ids"]}
    candidates = [entity["id"] for entity in entities if entity["id"] in union]
    same = rows[0]["bound_entity_id"] is not None and all(row["status"] == "RESOLVED" and row["bound_entity_id"] == rows[0]["bound_entity_id"] for row in rows)
    status = ("UNSUPPORTED_READING" if any(row["status"] == "UNSUPPORTED_READING" for row in rows)
              else "OPEN_SCOPE" if not context["closed_reference_scope"] else "NO_CANDIDATE" if not candidates
              else "UNRESOLVED_FEATURES" if any(row["status"] == "UNRESOLVED_FEATURES" for row in rows)
              else "RESOLVED" if same else "AMBIGUOUS")
    return {"status": status, "reading_ids": [row["id"] for row in rows], "candidate_entity_ids": candidates,
            "bound_entity_id": rows[0]["bound_entity_id"] if status == "RESOLVED" else None, "reading_results": rows}


FALSE_FLAGS = {"whole_clause_checked", "world_truth_established", "motive_established", "all_arabic_complete"}
NATIVE_FIELDS = RECEIPT_FIELDS | FALSE_FLAGS | {"law_id", "observed_status", "certificate_checked"}


def _native(payload: dict) -> dict:
    """Run the installed checker; imported native declarations are never trusted."""
    validate_payload(payload)
    process = subprocess.run([str(NATIVE)], input=wire(payload) + "\n", capture_output=True,
                             text=True, encoding="utf-8", timeout=30, check=False)
    if process.returncode != 0:
        raise InputError("Native checker process failed")
    if len(process.stdout.encode("utf-8")) > MAX_NATIVE_BYTES:
        raise ResourceLimit("Native receipt byte limit")
    return strict_loads(process.stdout)


def _native_agrees(result: Any, proposal: dict) -> bool:
    if type(result) is not dict or set(result) != NATIVE_FIELDS:
        return False
    if (result["law_id"] != LAW_ID or result["certificate_checked"] is not True
            or any(result[key] is not False for key in FALSE_FLAGS)):
        return False
    try:
        receipt = {key: result[key] for key in RECEIPT_FIELDS}
        validate_proposal(receipt)
    except (InputError, ResourceLimit, TypeError, ValueError):
        return False
    return receipt == proposal and result["observed_status"] == proposal["status"]


def execute_request(request: Any) -> dict:
    """Acquire only from the installed source and check the complete receipt.

    Full-file source acquisition and exhaustiveness of the acquired lexical
    ledger remain Python premises. Lean checks each retained donor's FORM
    decoding, the declared mark-preserving source-to-target spelling policy,
    annotation tags, bounded scope and the complete candidate receipt. Those
    checks do not establish source authenticity or whole-clause meaning.
    """
    execution = {"input": None, "input_sha256": None, "proposal": None, "proposal_sha256": None,
                 "native_result": None, "native_result_sha256": None, "native_sha256": None, "error": None}
    answer = {"schema": "nabt.contextual-reference-observation.v1", "law_id": LAW_ID,
              "status": "UNMEASURED", "native_checked": False, "certificate_checked": False,
              "reference": None, "input": None, "input_sha256": None, "context_sha256": None,
              "lexical_source_sha256": loader.SOURCE_SHA256, "source_registry_sha256": None,
              "runtime_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "native_sha256": None,
              "source_bindings": [], "scope": deepcopy(SCOPE), "execution": execution}
    try:
        # Normalize strictly serializable input before retaining it in a report.
        # JSON parsing rejects duplicate keys before this structured entry point.
        request = strict_loads(wire(request))
        answer["input"] = deepcopy(request)
        answer["input_sha256"] = digest(request)
        if type(request) is dict and "context" in request:
            answer["context_sha256"] = digest(request["context"])
        request = validate_input(request)
        current = identity()
        answer.update({key: current[key] for key in ("source_registry_sha256", "runtime_sha256", "native_sha256")})
        payload, bindings = build_request(request)
        answer["source_bindings"] = bindings
        proposal = propose(payload)
        payload["proposed"] = deepcopy(proposal)
        validate_payload(payload)  # Recheck wire bound after the full certificate.
        execution.update({"input": payload, "input_sha256": digest(payload), "proposal": proposal,
                          "proposal_sha256": digest(proposal), "native_sha256": current["native_sha256"]})
        if current["native_sha256"] is None:
            execution["error"] = "NATIVE_UNAVAILABLE"
        else:
            result = _native(payload)
            execution["native_result"] = result
            execution["native_result_sha256"] = digest(result)
            after = sha256(NATIVE.read_bytes()).hexdigest()
            if after != current["native_sha256"]:
                execution["error"] = "NATIVE_CHANGED_DURING_EXECUTION"
            elif not _native_agrees(result, proposal):
                error_fields = FALSE_FLAGS | {"law_id", "status", "reason"}
                if (type(result) is dict and set(result) == error_fields and result.get("law_id") == LAW_ID
                        and result.get("status") in {"INVALID_INPUT", "RESOURCE_LIMIT"}
                        and type(result.get("reason")) is str
                        and all(result[key] is False for key in FALSE_FLAGS)):
                    answer["status"] = result["status"]
                    execution["error"] = "NATIVE_" + result["status"] + ": " + result["reason"]
                else:
                    execution["error"] = "NATIVE_CERTIFICATE_REJECTED_OR_MALFORMED"
            else:
                answer.update(status=proposal["status"], native_checked=True, certificate_checked=True)
                if proposal["status"] in {"RESOLVED", "AMBIGUOUS", "NO_CANDIDATE"}:
                    occurrence = payload["occurrence"]
                    raw = request["text"].encode("utf-8")
                    reference = {"surface": occurrence["surface"], "status": proposal["status"],
                                 "candidate_entity_ids": deepcopy(proposal["candidate_entity_ids"]),
                                 "bound_entity_id": proposal["bound_entity_id"],
                                 "span": {"start": len(raw[:occurrence["start_byte"]].decode("utf-8")),
                                          "end": len(raw[:occurrence["end_byte"]].decode("utf-8"))},
                                 "scope": "outer", "occurrence": 0}
                    reference["reference_id"] = digest(reference)
                    answer["reference"] = reference
    except ResourceLimit as exc:
        answer["status"] = "RESOURCE_LIMIT"
        execution["error"] = str(exc)
    except subprocess.TimeoutExpired:
        answer["status"] = "RESOURCE_LIMIT"
        execution["error"] = "NATIVE_TIMEOUT"
    except Exception as exc:
        # Sources/contexts are external acquisition premises. Any failed replay,
        # strict validation or decoder error closes this path without a proof.
        message = str(exc)
        answer["status"] = "OUT_OF_SCOPE" if message.startswith("OUT_OF_SCOPE:") else "INVALID_INPUT"
        execution["error"] = type(exc).__name__ + ": " + message[:4096]
    answer["receipt_sha256"] = digest(answer)
    return answer
