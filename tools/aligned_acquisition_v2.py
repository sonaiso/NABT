"""Finite article citation readings with independent, exact v2 native replay.

The v1 proposer supplies only untrusted partition and local decisions. Neither
its verified receipts nor the source packet can confer authority on this law.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile

from nabt.alphabet import ALPHABET_ID
from nabt.certificates import issue_certificate, verify_certificate
from nabt.errors import NabtError
from nabt.word_reader import read_words
from tools import aligned_acquisition as v1

LAW_ID = "nabt.aligned-acquisition.v2"
MAX_SOURCE_BYTES = v1.MAX_SOURCE_BYTES
MAX_CODEPOINTS = v1.MAX_CODEPOINTS
MAX_REPORT_BYTES = v1.MAX_REPORT_BYTES
MAX_SOURCE_EVIDENCE_BYTES = 1024 * 1024
_NATIVE_PATH = Path(__file__).resolve().parents[1] / "formal/.lake/build/bin/alignedAcquisitionV2"
_SOURCES_PATH = Path(__file__).resolve().parents[1] / "evidence/article_acquisition_v2/source_evidence.json"
SOURCE_MANIFEST_SHA256 = "d5d348e17fd3f34eaa69e5a031956972860dd8dbf3eee25674a265ee4578543c"
_DEBTS = frozenset(("SILENT_LETTER_LEXICON_REQUIRED", "ORTHOGRAPHIC_LEXICON_REQUIRED"))
_PREFIX = frozenset(("ا", "اَ", "ٱ", "ٱَ"))
_CASE = frozenset("َُِ")
_HAQQ_FINAL = frozenset(("قَّ", "قُّ", "قِّ", "قَّ", "قُّ", "قِّ"))

_wire = v1._wire
_load = v1._load


def _failure(status, error):
    return {"law_id": LAW_ID, "alphabet_id": ALPHABET_ID, "status": status, "error": error}


def _finite_reading(group):
    """Whole raw-word guards authored in the frozen contract, not a prefix guess."""
    raw = tuple(piece["raw"] for piece in group)
    if len(raw) < 4 or raw[0] not in _PREFIX or raw[1] != "لْ":
        return None
    stem = raw[2:]
    if len(stem) == 2 and stem[0] == "حَ" and stem[1] in _HAQQ_FINAL:
        return "ARTICLE_HAQQ"
    if (len(stem) == 3 and stem[:2] == ("قَ", "وْ") and
            len(stem[2]) == 2 and stem[2][0] == "م" and stem[2][1] in _CASE):
        return "ARTICLE_QAWM"
    if (len(stem) == 4 and stem[:3] == ("غُ", "لَ", "ا") and
            len(stem[3]) == 2 and stem[3][0] == "م" and stem[3][1] in _CASE):
        return "ARTICLE_GHULAM"
    return None


def propose_acquisition(text, *, source_id="input", revision="1", scope="default",
                        ending="wasl", onset="word_initial"):
    """Compute an untrusted proposal; only fresh v2 native replay verifies it."""
    proposal = v1.propose_acquisition(text, source_id=source_id, revision=revision,
                                      scope=scope, ending=ending)
    if "error" in proposal:
        return _failure(proposal["status"], proposal["error"])
    if type(onset) is not str or onset not in ("word_initial", "connected"):
        return _failure("INVALID_INPUT", "INVALID_INPUT")
    proposal.update(law_id=LAW_ID, onset=onset)
    groups, group = [], []
    for piece in proposal["pieces"]:
        if piece["status"] == "BOUNDARY":
            if group:
                groups.append(group)
                group = []
        else:
            group.append(piece)
    if group:
        groups.append(group)
    for word, group in zip(proposal["words"], groups):
        rule = None
        if onset == "connected":
            rule = "CONNECTED_ONSET_NOT_IMPLEMENTED"
        elif not any(piece["rule"] in _DEBTS for piece in group):
            reading = _finite_reading(group)
            if reading is not None:
                group[0].update(status="LICENSED", rule=reading + "_INITIAL", cells=[112])
            elif (len(group) >= 2 and group[0]["raw"][0] in "اٱ" and
                  group[1]["raw"][0] == "ل"):
                rule = "ARTICLE_READING_NOT_LICENSED"
        if rule is not None:
            for piece in group:
                if piece["status"] != "INVALID_INPUT":
                    piece.update(status="DEFER", rule=rule, cells=[])
        word.update(status=v1._status(group), cells=[cell for piece in group for cell in piece["cells"]])
    status = v1._status(proposal["pieces"]) if groups else "DEFER"
    reason = ("NO_WORD" if not groups else "INVALID_PIECE" if status == "INVALID_INPUT" else
              "DEFERRED_PIECE" if status == "DEFER" else "COMPLETE_ACQUISITION")
    proposal.update(status=status, reason=reason)
    return proposal


def _native(request):
    if not _NATIVE_PATH.is_file():
        raise FileNotFoundError("Build formal target alignedAcquisitionV2")
    with tempfile.TemporaryDirectory(prefix="nabt-acquisition-v2-") as directory:
        request_path = Path(directory) / "request.json"
        output_path = Path(directory) / "response.json"
        request_path.write_text(_wire(request), encoding="utf-8")
        with output_path.open("wb") as output:
            result = subprocess.run([str(_NATIVE_PATH), str(request_path)], stdout=output,
                                    stderr=subprocess.DEVNULL, timeout=30, check=False)
        if output_path.stat().st_size > MAX_REPORT_BYTES:
            raise OverflowError("native response byte budget")
        response = _load(output_path.read_bytes())
    if (result.returncode == 2 and type(response) is dict and
            _wire(response) == _wire(_failure("RESOURCE_EXHAUSTED", "RESOURCE_LIMIT"))):
        raise OverflowError("native acquisition resource limit")
    if result.returncode != 0 or type(response) is not dict:
        raise ValueError("native transport rejected the valid proposal input")
    return response


def acquire(text, *, source_id="input", revision="1", scope="default", ending="wasl",
            onset="word_initial"):
    proposal = propose_acquisition(text, source_id=source_id, revision=revision, scope=scope,
                                   ending=ending, onset=onset)
    result = {"schema": "nabt.checked-acquisition.v2", "status": proposal["status"],
              "verified": False, "authority": "UNVERIFIED_PROPOSAL", "acquisition": proposal}
    if "error" in proposal:
        return result
    result["onset"] = onset
    request = {key: proposal[key] for key in ("text", "source_id", "revision", "scope", "ending", "onset")}
    try:
        if _wire(_native(request)) != _wire(proposal):
            raise ValueError("complete native replay differs")
    except (FileNotFoundError, PermissionError):
        return {**result, "status": "VERIFICATION_UNAVAILABLE", "error": "NATIVE_CHECKER_UNAVAILABLE"}
    except (subprocess.TimeoutExpired, OverflowError):
        return {**result, "status": "RESOURCE_EXHAUSTED", "error": "NATIVE_RESOURCE_LIMIT"}
    except (OSError, ValueError, RecursionError):
        return {**result, "status": "VERIFICATION_FAILED", "error": "NATIVE_REPLAY_MISMATCH"}
    return {**result, "verified": True, "authority": "NATIVE_REPLAYED_LOCAL_REPRESENTATION"}


def source_inventory():
    """Pin both the reused v1 law's evidence and the additive finite reading packet."""
    base = v1.source_inventory()
    with _SOURCES_PATH.open("rb") as stream:
        raw = stream.read(MAX_SOURCE_EVIDENCE_BYTES + 1)
    if len(raw) > MAX_SOURCE_EVIDENCE_BYTES:
        raise OverflowError("source evidence byte budget")
    if sha256(raw).hexdigest() != SOURCE_MANIFEST_SHA256:
        raise ValueError("installed article source manifest differs")
    document = _load(raw)
    if document["law_id"] != LAW_ID or document["alphabet_id"] != ALPHABET_ID:
        raise ValueError("installed article source authority differs")
    sources = {source["source_id"]: source["source_sha256"] for source in document["sources"]}
    passages = document["passages"]
    for passage in passages:
        excerpt = passage["raw_text"].encode("utf-8", "strict")
        if (sources.get(passage["source_id"]) != passage["source_sha256"] or
                sha256(excerpt).hexdigest() != passage["span_sha256"] or
                len(excerpt) != passage["byte_end_0based_exclusive"] - passage["byte_start_0based"] or
                len(passage["raw_text"].splitlines()) !=
                passage["line_end_1based_inclusive"] - passage["line_start_1based"] + 1):
            raise ValueError("installed article source excerpt differs")
    return {"schema": document["schema"], "sha256": SOURCE_MANIFEST_SHA256,
            "passages": len(passages), "conventions": len(document["conventions"]),
            "finite_readings": [entry["id"] for entry in document["finite_registry"]["entries"]],
            "base_acquisition": base,
            "authority": "AUTHORED_CONVENTIONS_WITH_BOUNDED_SOURCE_EVIDENCE"}


def read_acquired(text, *, source_id="input", revision="1", scope="default", ending="wasl",
                  onset="word_initial"):
    checked = acquire(text, source_id=source_id, revision=revision, scope=scope,
                      ending=ending, onset=onset)
    result = {**checked, "schema": "nabt.acquired-reading.v2", "word_reader": None,
              "shape_handoffs": [], "world_truth": "NOT_ESTABLISHED",
              "interpretation_scope": "FINITE_ARTICLE_CITATION_AND_EXISTING_FINITE_WORD_READER",
              "open_obligations": ["CONNECTED_ONSET_AND_CROSS_WORD_PHONOLOGY",
                                   "PRODUCTIVE_ARTICLE_AND_CLITIC_ANALYSIS", "OMITTED_ALIF_LEXICON",
                                   "GENERAL_LEXICAL_MORPHOLOGICAL_SYNTACTIC_ACQUISITION",
                                   "REFERENCE_AND_WORLD_EVIDENCE"]}
    if not checked["verified"]:
        return result
    try:
        result["source_evidence"] = source_inventory()
    except OverflowError:
        return {**result, "status": "RESOURCE_EXHAUSTED", "verified": False,
                "authority": "UNVERIFIED_PROPOSAL", "error": "SOURCE_EVIDENCE_BYTE_LIMIT"}
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        return {**result, "status": "SOURCE_EVIDENCE_UNAVAILABLE", "verified": False,
                "authority": "UNVERIFIED_PROPOSAL", "error": "INSTALLED_SOURCE_EVIDENCE_MISMATCH"}
    acquisition = checked["acquisition"]
    raw = acquisition["text"].encode("utf-8")
    result["source_sha256"] = sha256(raw).hexdigest()
    try:
        reader = read_words(raw, source_id=source_id, scope=scope)
    except NabtError as exc:
        reader = {"status": "RESOURCE_EXHAUSTED" if exc.code == "RESOURCE_LIMIT" else "DEFER",
                  "error": exc.code, "authority": "NO_WORD_READING"}
    result["word_reader"] = reader
    for index, word in enumerate(acquisition["words"]):
        span = {key: word[key] for key in ("start", "end", "byte_start", "byte_end")}
        occurrence_ids = [occurrence["occurrence_id"] for occurrence in reader.get("occurrences", [])
                          if occurrence["span"]["start"] == word["byte_start"] and
                          occurrence["span"]["end"] == word["byte_end"]]
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


def _receipt_wire(report):
    """Require an actual JSON value tree before complete type-sensitive comparison."""
    pending = [(report, 0)]
    while pending:
        value, depth = pending.pop()
        if depth > 128:
            raise ValueError("receipt nesting limit")
        if type(value) is dict:
            if any(type(key) is not str for key in value):
                raise ValueError("JSON object keys must be strings")
            pending.extend((item, depth + 1) for item in value.values())
        elif type(value) is list:
            pending.extend((item, depth + 1) for item in value)
        elif type(value) not in (str, int, float, bool, type(None)):
            raise ValueError("receipt contains a non-JSON type")
    return _wire(report).encode("utf-8")


def verify_acquired(report, *, text, source_id, revision, scope, ending, onset):
    """Replay the entire receipt against independent bytes and both mode policies."""
    try:
        if type(report) is not dict:
            raise ValueError("report must be a JSON object")
        encoded = _receipt_wire(report)
        if len(encoded) > MAX_REPORT_BYTES:
            return {"valid": False, "status": "RESOURCE_EXHAUSTED", "error": "REPORT_BYTE_LIMIT"}
        expected = read_acquired(text, source_id=source_id, revision=revision, scope=scope,
                                 ending=ending, onset=onset)
        if not expected["verified"]:
            return {"valid": False, "status": expected["status"], "error": expected.get("error", "INVALID_INPUT")}
        if encoded != _wire(expected).encode("utf-8"):
            raise ValueError("source-bound replay mismatch")
        return {"valid": True, "status": "VERIFIED_RECEIPT", "acquisition_status": expected["status"],
                "onset": onset, "authority": "SOURCE_BOUND_LOCAL_REPRESENTATION"}
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        return {"valid": False, "status": "INVALID_RECEIPT", "error": "REPLAY_MISMATCH"}
