"""Fresh source-bound acquisition joined to the native finite v3 syntax law.

The proposer never supplies replacement vocalization to another component.
Native syntax success cannot discharge acquisition/shape debt. Neither layer
identifies referents, chooses WALAD's individual/collective sense, or proves
external truth. Historical readers and receipts are not changed.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile

from tools import aligned_acquisition as local
from tools import aligned_acquisition_v2 as receipt_types
from tools import connected_acquisition_v3 as acquisition

LAW_ID = "nabt.acquired-person-nominal.v3"
SYNTAX_LAW_ID = "nabt.acquired-syntax.v3"
MAX_REPORT_BYTES = 8 * 1024 * 1024
_NATIVE_PATH = Path(__file__).resolve().parents[1] / "formal/.lake/build/bin/acquiredSyntaxV3"
_wire = local._wire
_load = local._load

# Two explicit source spellings per entry, not a vowel-subset or suffix rule.
_FORMS = {
    "QUMTU": ("قُمْتُ", "قمتُ"), "QUMTA": ("قُمْتَ", "قمتَ"),
    "QUMTI": ("قُمْتِ", "قمتِ"), "WALAD": ("الْوَلَدُ", "الولدُ"),
    "WALAD_DUAL": ("الْوَلَدَانِ", "الولدانِ"), "AWLAD": ("الْأَوْلَادُ", "الأولادُ"),
    "DHAHIB": ("ذَاهِبٌ", "ذاهبٌ"), "DHAHIB_DUAL": ("ذَاهِبَانِ", "ذاهبانِ"),
    "DHAHIB_PLURAL": ("ذَاهِبُونَ", "ذاهبونَ"),
}
_LEXICON = {raw: key for key, spellings in _FORMS.items() for raw in spellings}
_PERSON = {"QUMTU": (1, None, "ُ"), "QUMTA": (2, "masculine", "َ"),
           "QUMTI": (2, "feminine", "ِ")}
_NOMINAL = (("singular", "WALAD", "DHAHIB"),
            ("dual", "WALAD_DUAL", "DHAHIB_DUAL"),
            ("plural", "AWLAD", "DHAHIB_PLURAL"))
_COORDS = ("start", "end", "byte_start", "byte_end", "raw")


def _request(text, task, source_id, revision, scope, ending, onset):
    request = local._request(text, source_id, revision, scope, ending)
    if type(task) is not str or task not in ("person", "nominal_syntax"):
        raise ValueError("unknown syntax task")
    if type(onset) is not str or onset not in ("word_initial", "connected"):
        raise ValueError("unknown onset")
    return {**request, "task": task, "onset": onset}


def _span(text, start, end):
    return {"start": start, "end": end, "byte_start": len(text[:start].encode("utf-8")),
            "byte_end": len(text[:end].encode("utf-8")), "raw": text[start:end]}


def _suffix(text, token, count):
    return _span(text, token["end"] - count, token["end"])


def _tokens(text):
    pieces = [{key: piece[key] for key in _COORDS} for piece in local._pieces(text)]
    tokens, start, end = [], None, None
    for piece in pieces:
        if piece["raw"][0] in local._SEPARATORS:
            if start is not None:
                tokens.append(_span(text, start, end))
                start = end = None
        else:
            if start is None:
                start = piece["start"]
            end = piece["end"]
    if start is not None:
        tokens.append(_span(text, start, end))
    for token in tokens:
        token["lexeme"] = _LEXICON.get(token["raw"])
    return pieces, tokens


def _diagnostics():
    return [{"reading_id": key, "person": person, "number": "singular", "gender": gender}
            for key, (person, gender, _) in _PERSON.items()]


def propose_syntax(text, *, task, source_id="input", revision="1", scope="default",
                   ending="wasl", onset="word_initial"):
    """Untrusted independent Python proposal of the complete native receipt."""
    request = _request(text, task, source_id, revision, scope, ending, onset)
    text = request["text"]
    pieces, tokens = _tokens(text)
    body = text.rstrip(" \t")
    if body.endswith("."):
        body = body[:-1]
    boundary_valid = all(c not in local._SEPARATORS or c in " \t" for c in body)
    lexemes = [token["lexeme"] for token in tokens]
    reading_id = person = nominal = None
    if boundary_valid and task == "person" and len(lexemes) == 1 and lexemes[0] in _PERSON:
        reading_id = lexemes[0]
        index, gender, vowel = _PERSON[reading_id]
        person = {"reading_id": reading_id, "category": "verb", "tense": "past",
                  "person": index, "number": "singular", "gender": gender,
                  "subject_form": "attached_ta", "word_index": 0, "source_vowel": vowel,
                  "referent": None, "source_word": tokens[0],
                  "source_suffix": _suffix(text, tokens[0], 2)}
    if boundary_valid and task == "nominal_syntax":
        for number, subject, predicate in _NOMINAL:
            for si, pi, order in ((0, 1, "subject_predicate"), (1, 0, "predicate_subject")):
                expected = [subject, predicate] if si == 0 else [predicate, subject]
                if lexemes != expected:
                    continue
                reading_id = "NOMINAL_" + number + ("_SUBJECT_FIRST" if si == 0 else "_PREDICATE_FIRST")
                nominal = {"subject_index": si, "predicate_index": pi,
                    "subject_lexeme": subject, "predicate_lexeme": predicate,
                    "order": order, "number": number, "gender": "masculine",
                    "subject_case": "nominative", "predicate_case": "nominative",
                    "lexical_cardinality_alternatives": ["individual", "collective"] if number == "singular" else [],
                    "denotation_cardinality": None, "referent": None,
                    "source_words": tokens, "subject_source": tokens[si], "predicate_source": tokens[pi],
                    "subject_ending": _suffix(text, tokens[si], 3 if number == "dual" else 1),
                    "predicate_ending": _suffix(text, tokens[pi], 1 if number == "singular" else 3)}
    diagnostic = (_diagnostics() if task == "person" and boundary_valid and len(tokens) == 1 and
                  tokens[0]["raw"] in ("قمت", "قُمْت", "قُمْتْ") else [])
    return {"law_id": SYNTAX_LAW_ID, **request,
            "status": "LICENSED_PERSON" if person else "LICENSED_NOMINAL" if nominal else "DEFER",
            "reason": "FINITE_SOURCE_GRAMMAR" if reading_id else "OUTSIDE_DECLARED_GRAMMAR",
            "boundary_valid": boundary_valid, "source_pieces": pieces, "tokens": tokens,
            "reading_id": reading_id, "person": person, "nominal": nominal,
            "diagnostic_person_hypotheses": diagnostic}


def _native(request):
    if not _NATIVE_PATH.is_file():
        raise FileNotFoundError("Build formal target acquiredSyntaxV3")
    with tempfile.TemporaryDirectory(prefix="nabt-syntax-v3-") as directory:
        path = Path(directory) / "request.json"
        output_path = Path(directory) / "response.json"
        path.write_text(_wire(request), encoding="utf-8")
        with output_path.open("wb") as output:
            process = subprocess.run([str(_NATIVE_PATH), str(path)], stdout=output,
                                     stderr=subprocess.DEVNULL, timeout=30, check=False)
        if output_path.stat().st_size > MAX_REPORT_BYTES:
            raise OverflowError("native response byte budget")
        response = _load(output_path.read_bytes())
    if process.returncode == 2 and response == {
            "law_id": SYNTAX_LAW_ID, "status": "RESOURCE_EXHAUSTED", "error": "RESOURCE_LIMIT"}:
        raise OverflowError("native syntax resource budget")
    if process.returncode != 0 or type(response) is not dict:
        raise ValueError("native transport rejected valid syntax request")
    return response


def _base():
    return {"schema": "nabt.acquired-person-nominal-result.v3", "law_id": LAW_ID,
            "status": "DEFER", "verified": False, "chain_complete": False,
            "acquisition": None, "syntax": None, "gates": {}, "blocked_by": [],
            "person": None, "nominal": None, "diagnostic_person_hypotheses": [],
            "world_truth_established": False, "referents_established": False,
            "all_arabic_complete": False}


def evaluate(text, *, task, source_id="input", revision="1", scope="default",
             ending="wasl", onset="word_initial"):
    result = _base()
    try:
        request = _request(text, task, source_id, revision, scope, ending, onset)
    except OverflowError:
        return {**result, "status": "RESOURCE_EXHAUSTED", "blocked_by": ["SOURCE_BUDGET"]}
    except (ValueError, TypeError, UnicodeError):
        return {**result, "status": "INVALID_INPUT", "blocked_by": ["INVALID_SOURCE_OR_BINDING"]}
    binding = {key: request[key] for key in ("source_id", "revision", "scope", "ending", "onset")}
    result.update(task=task, binding=binding, source_sha256=sha256(request["text"].encode("utf-8")).hexdigest())
    # A fresh dependency validates its pinned packet against retained bytes.
    acquired = acquisition.read_acquired(text, **binding)
    result["acquisition"] = acquired
    proposal = propose_syntax(text, task=task, **binding)
    checked = False
    failure = None
    try:
        if _wire(_native(request)) != _wire(proposal):
            raise ValueError("complete native syntax replay differs")
        checked = True
    except (FileNotFoundError, PermissionError):
        failure = "VERIFICATION_UNAVAILABLE"
    except (subprocess.TimeoutExpired, OverflowError):
        failure = "RESOURCE_EXHAUSTED"
    except (OSError, ValueError, TypeError, RecursionError):
        failure = "VERIFICATION_FAILED"
    result["syntax"] = {"verified": checked, "native_result": proposal if checked else None,
                        "status": proposal["status"] if checked else failure}
    if checked:
        result["diagnostic_person_hypotheses"] = proposal["diagnostic_person_hypotheses"]
    underlying = acquired.get("acquisition", {})
    gates = {"source_acquired": acquired.get("status") == "ACQUIRED",
             "acquisition_native_checked": acquired.get("verified") is True,
             "source_shapes": acquired.get("shape_verified") is True,
             "syntax_native_checked": checked,
             "finite_grammar_reading": checked and proposal["reading_id"] is not None,
             "same_source_binding": all(underlying.get(key) == request[key]
                 for key in ("text", "source_id", "revision", "scope", "ending", "onset"))}
    result["gates"] = gates
    result["blocked_by"] = [key for key, passed in gates.items() if not passed]
    if all(gates.values()):
        result.update(status=proposal["status"], verified=True, chain_complete=True,
                      person=proposal["person"], nominal=proposal["nominal"])
    else:
        # Malformed source and infrastructure/resource failures are not scope negatives.
        statuses = [acquired.get("status"), failure]
        if "SHAPE_CHECK_FAILED" in statuses:
            statuses.append("VERIFICATION_UNAVAILABLE")
        for status in ("INVALID_INPUT", "RESOURCE_EXHAUSTED", "SOURCE_EVIDENCE_UNAVAILABLE",
                       "VERIFICATION_FAILED", "VERIFICATION_UNAVAILABLE"):
            if status in statuses:
                result["status"] = status
                break
    if len(_wire(result).encode("utf-8")) > MAX_REPORT_BYTES:
        return {**_base(), "status": "RESOURCE_EXHAUSTED", "blocked_by": ["WHOLE_REPORT_BUDGET"]}
    return result


def verify(report, *, text, task, source_id, revision, scope, ending, onset):
    """Recompute every component; exact deferred receipts remain incomplete."""
    try:
        if type(report) is not dict:
            raise ValueError("receipt must be an object")
        encoded = receipt_types._receipt_wire(report)
        if len(encoded) > MAX_REPORT_BYTES:
            return {"valid": False, "replay_matches": False, "status": "RESOURCE_EXHAUSTED"}
        expected = evaluate(text, task=task, source_id=source_id, revision=revision,
                            scope=scope, ending=ending, onset=onset)
        if encoded != _wire(expected).encode("utf-8"):
            raise ValueError("whole receipt differs from independent replay")
        return {"valid": expected["chain_complete"], "replay_matches": True,
                "status": "VERIFIED_COMPOSITE_RECEIPT" if expected["chain_complete"] else expected["status"],
                "blocked_by": expected["blocked_by"]}
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        return {"valid": False, "replay_matches": False, "status": "INVALID_RECEIPT"}
