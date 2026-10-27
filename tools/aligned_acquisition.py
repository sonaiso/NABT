"""Source-aligned, independently replayed local representation (not semantics).

The strict alphabet reader remains unchanged. Only ``acquire`` grants native
replay authority; ``propose_acquisition`` is an untrusted computation. Every
transformation retains its exact source piece and its authored rule identifier.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile

from nabt.alphabet import ALPHABET_ID, CARRIERS
from nabt.certificates import issue_certificate, verify_certificate
from nabt.errors import NabtError
from nabt.word_reader import read_words

LAW_ID = "nabt.aligned-acquisition.v1"
MAX_SOURCE_BYTES = 8192
MAX_CODEPOINTS = 4096
MAX_REPORT_BYTES = 8 * 1024 * 1024
_NATIVE_PATH = Path(__file__).resolve().parents[1] / "formal/.lake/build/bin/alignedAcquisition"
_SEPARATORS = frozenset(' \t\r\n.،؛,:!?؟()[]{}«»"“”')
_VOWELS = "ًٌٍَُِْ"
_MARKS = frozenset(_VOWELS + "ّٰ")
_SEATS = frozenset("أإؤئ")
_OMITTED = frozenset("هذا هذه هذان هذين هؤلاء ذلك لكن إله الله الرحمن".split())
_SILENT = frozenset("أولو أولي أولئك أولاء".split())
_SOURCES_PATH = Path(__file__).resolve().parents[1] / "evidence/aligned_acquisition_v1/source_evidence.json"
SOURCE_MANIFEST_SHA256 = "269f1aa66756aefc6277e5ff0ef4922dc9ad13fdd2a7bab5e9347649c1fa3cc5"


def _wire(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _load(raw: bytes):
    return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def _failure(status: str, error: str) -> dict:
    return {"law_id": LAW_ID, "alphabet_id": ALPHABET_ID, "status": status, "error": error}


def _request(text, source_id, revision, scope, ending):
    if type(text) not in (str, bytes):
        raise ValueError("text must be an exact string or bytes")
    if len(text) > (MAX_CODEPOINTS if type(text) is str else MAX_SOURCE_BYTES):
        raise OverflowError("source length budget")
    raw = text.encode("utf-8", "strict") if type(text) is str else text
    if len(raw) > MAX_SOURCE_BYTES:
        raise OverflowError("source byte budget")
    decoded = raw.decode("utf-8", "strict")
    if len(decoded) > MAX_CODEPOINTS:
        raise OverflowError("source scalar budget")
    for value in (source_id, revision, scope):
        if (type(value) is not str or not value or len(value) > 512 or
                any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value)):
            raise ValueError("invalid source identity")
        value.encode("utf-8", "strict")
    if type(ending) is not str or ending not in ("wasl", "waqf"):
        raise ValueError("invalid ending")
    return {"text": decoded, "source_id": source_id, "revision": revision,
            "scope": scope, "ending": ending}


def _cell(head: str, mark: int) -> int:
    return CARRIERS.index(head) * 4 + mark


def _pieces(text: str) -> list[dict]:
    pieces = []
    start = byte_start = 0
    while start < len(text):
        end = start + 1
        if text[start] not in _SEPARATORS:
            while end < len(text) and text[end] in _MARKS:
                end += 1
        raw = text[start:end]
        byte_end = byte_start + len(raw.encode("utf-8"))
        pieces.append({"start": start, "end": end, "byte_start": byte_start,
                       "byte_end": byte_end, "raw": raw, "status": "DEFER",
                       "rule": "UNSUPPORTED_CHARACTER", "cells": []})
        start, byte_start = end, byte_end
    return pieces


def _classification(raw: str):
    marks = raw[1:]
    vowels = [c for c in marks if c in _VOWELS]
    if raw[0] in _MARKS:
        return "MARK_WITHOUT_CARRIER"
    if len(vowels) > 1 or marks.count("ّ") > 1 or marks.count("ٰ") > 1:
        return "CONFLICTING_MARKS"
    if "ّ" in marks and "ْ" in vowels:
        return "SHADDA_WITH_SUKUN"
    if "ٰ" in marks and vowels and vowels != ["َ"]:
        return "DAGGER_VOWEL_CONFLICT"
    return None


def _classify_word(pieces: list[dict], pause: bool):
    skeleton = "".join(c for p in pieces for c in p["raw"] if c not in _MARKS)
    debt = ("SILENT_LETTER_LEXICON_REQUIRED" if skeleton in _SILENT else
            "ORTHOGRAPHIC_LEXICON_REQUIRED" if skeleton in _OMITTED and
            not any("ٰ" in p["raw"] for p in pieces) else None)
    for index, piece in enumerate(pieces):
        raw, final = piece["raw"], index == len(pieces) - 1
        head, marks = raw[0], raw[1:]
        vowels = [c for c in marks if c in _VOWELS]
        vowel = vowels[0] if vowels else None
        previous = pieces[index - 1] if index else None
        support_alif = (not final and index + 2 == len(pieces) and
                        pieces[index + 1]["raw"] == "ا" and vowel == "ً")
        at_end = final or support_alif

        def assign(status, rule, cells=()):
            piece.update(status=status, rule=rule, cells=list(cells))

        def after_short(state):
            return (previous is not None and previous["status"] == "LICENSED" and
                    previous["cells"] and previous["cells"][-1] % 4 == state and
                    [c for c in previous["raw"][1:] if c in _VOWELS] == [_VOWELS[state]])

        malformed = _classification(raw)
        if malformed:
            assign("INVALID_INPUT", malformed)
        elif debt:
            assign("DEFER", debt)
        elif head == "ـ":
            assign("DEFER", "TATWEEL_UNSUPPORTED")
        elif head == "آ":
            assign("DEFER", "MADDA_REQUIRED")
        elif head == "ٱ":
            assign("DEFER", "HAMZAT_WASL_REQUIRED")
        elif head == "ى":
            if not marks and final and after_short(0):
                assign("LICENSED", "MAQSURA", [_cell("ا", 3)])
            else:
                assign("DEFER", "MAQSURA_CONTEXT_REQUIRED")
        elif head == "ة":
            if not final or vowel is None or vowel == "ْ" or "ٰ" in marks:
                assign("DEFER", "TA_MARBUTA_CONTEXT_REQUIRED")
            else:
                carrier = "ه" if pause else "ت"
                cells = [_cell(carrier, 3)] if "ّ" in marks else []
                state = _VOWELS.index(vowel)
                cells += [_cell(carrier, 3 if pause else state if state < 4 else state - 4)]
                if not pause and state >= 4:
                    cells += [_cell("ن", 3)]
                assign("LICENSED", "TA_MARBUTA_WAQF" if pause else "TA_MARBUTA_WASL", cells)
        elif head not in CARRIERS and head not in _SEATS:
            assign("DEFER", "UNSUPPORTED_CHARACTER")
        elif vowel is None:
            if "ٰ" in marks or marks:
                assign("DEFER", "MISSING_VOCALIZATION")
            elif (head == "ا" and final and previous and previous["status"] == "LICENSED"
                  and [c for c in previous["raw"][1:] if c in _VOWELS] == ["ً"]):
                assign("LICENSED", "ALIF_TANWIN")
            elif head in "اوي" and after_short("اوي".index(head)):
                assign("LICENSED", "LONG_VOWEL", [_cell(head, 3)])
            elif head == "ا" and index == 0:
                assign("DEFER", "HAMZAT_WASL_REQUIRED")
            elif head == "ا" and final and previous and previous["raw"][0] == "و":
                assign("DEFER", "PLURAL_ALIF_REQUIRED")
            elif (head == "ل" and previous and previous["raw"] == "ا" and
                  previous["rule"] == "HAMZAT_WASL_REQUIRED"):
                assign("DEFER", "ARTICLE_LAM_REQUIRED")
            elif head in "اوي":
                assign("DEFER", "LONG_VOWEL_CONTEXT_REQUIRED")
            else:
                assign("DEFER", "MISSING_VOCALIZATION")
        else:
            carrier = "ء" if head in _SEATS else head
            state = _VOWELS.index(vowel)
            cells = [_cell(carrier, 3)] if "ّ" in marks else []
            if carrier == "ء" and vowel == "ً" and at_end and previous and previous["raw"] == "ا":
                assign("DEFER", "HAMZA_TANWIN_EXCEPTION")
            elif "ٰ" in marks:
                assign("LICENSED", "DAGGER_ALIF", cells + [_cell(carrier, 0), _cell("ا", 3)])
            elif state >= 4:
                if pause and at_end:
                    cells += ([_cell(carrier, 0), _cell("ا", 3)] if state == 4 else [_cell(carrier, 3)])
                    assign("LICENSED", "TANWIN_WAQF", cells)
                else:
                    assign("LICENSED", "TANWIN_WASL", cells + [_cell(carrier, state - 4), _cell("ن", 3)])
            elif pause and final:
                assign("LICENSED", "ORDINARY_WAQF", cells + [_cell(carrier, 3)])
            else:
                rule = "SHADDA" if "ّ" in marks else "HAMZA_SEAT" if head in _SEATS else "MARKED_CARRIER"
                assign("LICENSED", rule, cells + [_cell(carrier, state)])


def _status(pieces: list[dict]) -> str:
    if any(p["status"] == "INVALID_INPUT" for p in pieces):
        return "INVALID_INPUT"
    if any(p["status"] == "DEFER" for p in pieces):
        return "DEFER"
    return "ACQUIRED"


def propose_acquisition(text, *, source_id="input", revision="1", scope="default", ending="wasl") -> dict:
    """Compute a diagnostic proposal; it is never a verification certificate."""
    try:
        request = _request(text, source_id, revision, scope, ending)
    except OverflowError:
        return _failure("RESOURCE_EXHAUSTED", "RESOURCE_LIMIT")
    except (ValueError, UnicodeError):
        return _failure("INVALID_INPUT", "INVALID_INPUT")
    pieces = _pieces(request["text"])
    groups = []
    group = []
    for piece in pieces:
        if piece["raw"] in _SEPARATORS:
            piece.update(status="BOUNDARY", rule="BOUNDARY")
            if group:
                groups.append(group)
                group = []
        else:
            group.append(piece)
    if group:
        groups.append(group)
    words = []
    for index, group in enumerate(groups):
        _classify_word(group, ending == "waqf" and index == len(groups) - 1)
        words.append({"start": group[0]["start"], "end": group[-1]["end"],
                      "byte_start": group[0]["byte_start"], "byte_end": group[-1]["byte_end"],
                      "status": _status(group), "cells": [c for p in group for c in p["cells"]]})
    status = _status(pieces) if words else "DEFER"
    reason = ("NO_WORD" if not words else "INVALID_PIECE" if status == "INVALID_INPUT" else
              "DEFERRED_PIECE" if status == "DEFER" else "COMPLETE_ACQUISITION")
    return {"law_id": LAW_ID, "alphabet_id": ALPHABET_ID, **request, "status": status,
            "reason": reason, "pieces": pieces, "words": words}


def _native(request: dict) -> dict:
    # The checker location is installed by the repository build, never supplied
    # by a report/caller. Installed wheels without this build fail closed.
    if not _NATIVE_PATH.is_file():
        raise FileNotFoundError("Build formal target alignedAcquisition")
    with tempfile.TemporaryDirectory(prefix="nabt-acquisition-") as directory:
        request_path = Path(directory) / "request.json"
        output_path = Path(directory) / "response.json"
        request_path.write_text(_wire(request), encoding="utf-8")
        with output_path.open("wb") as output:
            result = subprocess.run([str(_NATIVE_PATH), str(request_path)], stdout=output,
                                    stderr=subprocess.DEVNULL, timeout=30, check=False)
        if output_path.stat().st_size > MAX_REPORT_BYTES:
            raise OverflowError("native response byte budget")
        response = _load(output_path.read_bytes())
    if result.returncode != 0 or type(response) is not dict:
        raise ValueError("native transport rejected the valid proposal input")
    return response


def acquire(text, *, source_id="input", revision="1", scope="default", ending="wasl") -> dict:
    proposal = propose_acquisition(text, source_id=source_id, revision=revision, scope=scope, ending=ending)
    result = {"schema": "nabt.checked-acquisition.v1", "status": proposal["status"],
              "verified": False, "authority": "UNVERIFIED_PROPOSAL", "acquisition": proposal}
    if "error" in proposal:
        return result
    request = {key: proposal[key] for key in ("text", "source_id", "revision", "scope", "ending")}
    try:
        replay = _native(request)
        if _wire(replay) != _wire(proposal):
            raise ValueError("complete native replay differs")
    except (FileNotFoundError, PermissionError):
        return {**result, "status": "VERIFICATION_UNAVAILABLE", "error": "NATIVE_CHECKER_UNAVAILABLE"}
    except (subprocess.TimeoutExpired, OverflowError):
        return {**result, "status": "RESOURCE_EXHAUSTED", "error": "NATIVE_RESOURCE_LIMIT"}
    except (OSError, ValueError, RecursionError):
        return {**result, "status": "VERIFICATION_FAILED", "error": "NATIVE_REPLAY_MISMATCH"}
    return {**result, "verified": True, "authority": "NATIVE_REPLAYED_LOCAL_REPRESENTATION"}


def source_inventory() -> dict:
    """Validate pinned embedded excerpts; original books are research inputs."""
    raw = _SOURCES_PATH.read_bytes()
    if sha256(raw).hexdigest() != SOURCE_MANIFEST_SHA256:
        raise ValueError("installed acquisition source manifest differs")
    document = _load(raw)
    if document["law_id"] != LAW_ID or document["alphabet_id"] != ALPHABET_ID:
        raise ValueError("installed source authority differs")
    sources = {s["source_id"]: s["source_sha256"] for s in document["sources"]}
    passages = document["passages"]
    for passage in passages:
        excerpt = passage["raw_text"].encode("utf-8", "strict")
        if (sources.get(passage["source_id"]) != passage["source_sha256"] or
                sha256(excerpt).hexdigest() != passage["span_sha256"] or
                len(excerpt) != passage["end"] - passage["start"] or
                len(passage["raw_text"].splitlines()) != passage["line_end"] - passage["line_start"] + 1):
            raise ValueError("installed source excerpt differs")
    return {"schema": document["schema"], "sha256": SOURCE_MANIFEST_SHA256,
            "passages": len(passages), "conventions": len(document["conventions"]),
            "authority": "AUTHORED_CONVENTIONS_WITH_BOUNDED_SOURCE_EVIDENCE"}


def read_acquired(text, *, source_id="input", revision="1", scope="default", ending="wasl") -> dict:
    checked = acquire(text, source_id=source_id, revision=revision, scope=scope, ending=ending)
    result = {**checked, "schema": "nabt.acquired-reading.v1", "word_reader": None,
              "shape_handoffs": [], "world_truth": "NOT_ESTABLISHED",
              "interpretation_scope": "LOCAL_REPRESENTATION_AND_EXISTING_FINITE_WORD_READER",
              "open_obligations": ["CLITIC_AND_OMITTED_ALIF_ANALYSIS", "CROSS_WORD_PHONOLOGY",
                                   "GENERAL_LEXICAL_MORPHOLOGICAL_SYNTACTIC_ACQUISITION",
                                   "REFERENCE_AND_WORLD_EVIDENCE"]}
    if not checked["verified"]:
        return result
    try:
        result["source_evidence"] = source_inventory()
    except (OSError, ValueError, KeyError, TypeError):
        return {**result, "status": "SOURCE_EVIDENCE_UNAVAILABLE", "verified": False,
                "authority": "UNVERIFIED_PROPOSAL", "error": "INSTALLED_SOURCE_EVIDENCE_MISMATCH"}
    acquisition = checked["acquisition"]
    raw = acquisition["text"].encode("utf-8")
    result["source_sha256"] = sha256(raw).hexdigest()
    # Original source only: expanded cells never substitute for textual evidence.
    try:
        reader = read_words(raw, source_id=source_id, scope=scope)
    except NabtError as exc:
        reader = {"status": "RESOURCE_EXHAUSTED" if exc.code == "RESOURCE_LIMIT" else "DEFER",
                  "error": exc.code, "authority": "NO_WORD_READING"}
    result["word_reader"] = reader
    for index, word in enumerate(acquisition["words"]):
        span = {key: word[key] for key in ("start", "end", "byte_start", "byte_end")}
        occurrence_ids = [o["occurrence_id"] for o in reader.get("occurrences", [])
                          if o["span"]["start"] == word["byte_start"] and
                          o["span"]["end"] == word["byte_end"]]
        mode = ending if index == len(acquisition["words"]) - 1 else "wasl"
        handoff = {"word_index": index, "span": span, "mode": mode,
                   "occurrence_ids": occurrence_ids, "status": "ACQUISITION_INCOMPLETE"}
        if word["status"] == "ACQUIRED":
            try:
                certificate = issue_certificate(word["cells"], mode, source_text=None)
                if not verify_certificate(certificate).valid:
                    raise NabtError("SHAPE_REPLAY_FAILED", "Generated shape failed exact replay")
                handoff.update(status="SHAPE_LICENSED", certificate=certificate)
            except NabtError as exc:
                handoff.update(status="RESOURCE_EXHAUSTED" if exc.code == "RESOURCE_LIMIT" else
                               "SHAPE_REJECTED" if exc.code == "UNLICENSED_SHAPE" else "SHAPE_CHECK_FAILED",
                               error=exc.code)
        result["shape_handoffs"].append(handoff)
    return result


def verify_acquired(report, *, text, source_id, revision, scope, ending) -> dict:
    """Replay against independently supplied source AND all expected metadata."""
    try:
        if type(report) is not dict:
            raise ValueError("report must be a JSON object")
        encoded = _wire(report).encode("utf-8")
        if len(encoded) > MAX_REPORT_BYTES:
            return {"valid": False, "status": "RESOURCE_EXHAUSTED", "error": "REPORT_BYTE_LIMIT"}
        expected = read_acquired(text, source_id=source_id, revision=revision, scope=scope, ending=ending)
        if not expected["verified"]:
            return {"valid": False, "status": expected["status"], "error": expected.get("error", "INVALID_INPUT")}
        if encoded != _wire(expected).encode("utf-8"):
            raise ValueError("source-bound replay mismatch")
        return {"valid": True, "status": "VERIFIED_RECEIPT", "acquisition_status": expected["status"],
                "authority": "SOURCE_BOUND_LOCAL_REPRESENTATION"}
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        return {"valid": False, "status": "INVALID_RECEIPT", "error": "REPLAY_MISMATCH"}
