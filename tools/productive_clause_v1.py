"""Original-source, finite productive verbal frames with checked handoff.

The source scope and independent matrix were frozen before this implementation.
This tool composes installed acquisition/shape checks with a separate native
syntax law. It does not alter historical readers or infer external referents,
world truth, or exclusivity. Structural candidate counts keep that limited scope.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile

from nabt.alphabet import ALPHABET_ID
from tools import aligned_acquisition as source
from tools import connected_acquisition_v3 as acquisition

LAW_ID = "nabt.acquired-productive-clause.v1"
SYNTAX_LAW_ID = "nabt.productive-clause.v1"
SOURCE_SCOPE_SHA256 = "eb3a1d93730c4a402bce2561afb8934d1f76853ca31fe8ad1167c33ed08d4f17"
SOURCE_SCOPE_PATH = "evidence/productive_clause_v1/source_scope.json"
ROOT = Path(__file__).resolve().parents[1]
_NATIVE_PATH = ROOT / "formal/.lake/build/bin/productiveClauseV1"
MAX_SOURCE_BYTES = source.MAX_SOURCE_BYTES
MAX_REPORT_BYTES = 8 * 1024 * 1024
MAX_SOURCE_PACKET_BYTES = 1024 * 1024
_wire, _load = source._wire, source._load
_COORDS = ("start", "end", "byte_start", "byte_end", "raw")

# Installed source-interpretation rows, not sentence-level expected answers.
# Case/name classifications and full vocalization are authored scope premises.
_FORMS = (
    ("ضَرَبَ", "DARABA", "verb", None),
    ("زَيْدٌ", "ZAYD", "proper_name", "nom"),
    ("زَيْدًا", "ZAYD", "proper_name", "acc"),
    ("بَكْرٌ", "BAKR", "proper_name", "nom"),
    ("بَكْرًا", "BAKR", "proper_name", "acc"),
    ("خَالِدٌ", "KHALID", "proper_name", "nom"),
    ("خَالِدًا", "KHALID", "proper_name", "acc"),
    ("سَعِيدٌ", "SAID", "proper_name", "nom"),
    ("سَعِيدًا", "SAID", "proper_name", "acc"),
    ("قَيْسٌ", "QAYS", "proper_name", "nom"),
    ("عَمْرًا", "AMR", "proper_name", "acc"),
)
_LEXICON = {raw: (lexeme, category, case) for raw, lexeme, category, case in _FORMS}
GATE_NAMES = (
    "source_evidence_checked", "source_acquired", "acquisition_native_checked",
    "source_shapes", "syntax_native_checked", "finite_grammar_reading",
    "same_source_binding", "source_alignment", "scope_modes",
)


def _request(text, source_id, revision, scope, ending, onset):
    request = source._request(text, source_id, revision, scope, ending)
    if type(onset) is not str or onset not in ("word_initial", "connected"):
        raise ValueError("unknown onset")
    return {**request, "onset": onset}


def _span(text, start, end):
    return {"start": start, "end": end, "byte_start": len(text[:start].encode("utf-8")),
            "byte_end": len(text[:end].encode("utf-8")), "raw": text[start:end]}


def _tokens(text):
    pieces = [{key: piece[key] for key in _COORDS} for piece in source._pieces(text)]
    tokens, start, end = [], None, None
    for piece in pieces:
        if piece["raw"][0] in source._SEPARATORS:
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
        lexeme, category, case = _LEXICON.get(token["raw"], (None, None, None))
        token.update(lexeme=lexeme, category=category, nominal_case=case)
    return pieces, tokens


def propose_clause(text, *, source_id="input", revision="1", scope="default",
                   ending="wasl", onset="word_initial"):
    """Untrusted Python proposal; a status here is never a checked chain."""
    request = _request(text, source_id, revision, scope, ending, onset)
    pieces, tokens = _tokens(request["text"])
    body = request["text"].rstrip(" \t")
    if body.endswith("."):
        body = body[:-1]
    boundary = all(c not in source._SEPARATORS or c in " \t" for c in body)
    status, reason, reading, reading_id = "DEFER", "OUTSIDE_DECLARED_GRAMMAR", None, None
    if ending != "wasl" or onset != "word_initial":
        reason = "MODE_OUTSIDE_DECLARED_SCOPE"
    elif not boundary:
        reason = "BOUNDARY_OUTSIDE_DECLARED_SCOPE"
    elif any(token["lexeme"] is None for token in tokens):
        reason = "OUTSIDE_DECLARED_LEXICON"
    elif (len(tokens) == 3 and tokens[0]["category"] == "verb" and
          all(t["category"] == "proper_name" for t in tokens[1:])):
        cases = [token["nominal_case"] for token in tokens[1:]]
        if cases in (["nom", "acc"], ["acc", "nom"]):
            si, oi = (1, 2) if cases[0] == "nom" else (2, 1)
            order = "VSO" if si == 1 else "VOS"
            reading_id = "DARABA_" + tokens[si]["lexeme"] + "_" + tokens[oi]["lexeme"] + "_" + order
            reading = {"verb_lexeme": tokens[0]["lexeme"],
                "subject_lexeme": tokens[si]["lexeme"], "object_lexeme": tokens[oi]["lexeme"],
                "verb_index": 0, "subject_index": si, "object_index": oi, "order": order,
                "tense": "past", "voice": "active", "subject_case": "nom", "object_case": "acc",
                "source_words": tokens, "verb_source": tokens[0],
                "subject_source": tokens[si], "object_source": tokens[oi],
                "referents": None, "world_truth": None}
            status, reason = "LICENSED_CLAUSE", "DECLARED_ACTIVE_TRANSITIVE_FRAME"
        else:
            status, reason = "REJECTED_IN_SCOPE", "ROLE_CASE_CONFLICT"
    return {"law_id": SYNTAX_LAW_ID, **request, "status": status, "reason": reason,
            "boundary_valid": boundary, "source_pieces": pieces, "tokens": tokens,
            "reading_id": reading_id, "reading": reading}


def source_inventory():
    """Reopen retained source bytes and exact slices; do not trust citation IDs."""
    raw = acquisition._read_bounded(acquisition._installed_path(SOURCE_SCOPE_PATH), MAX_SOURCE_PACKET_BYTES)
    if len(raw) > MAX_SOURCE_PACKET_BYTES:
        raise OverflowError("source packet byte budget")
    if sha256(raw).hexdigest() != SOURCE_SCOPE_SHA256:
        raise ValueError("installed productive clause scope changed")
    packet = _load(raw)
    if packet["law_id"] != SYNTAX_LAW_ID or packet["alphabet_id"] != ALPHABET_ID:
        raise ValueError("source scope law binding differs")
    rows = [(r["surface"], r["lexeme_id"], r["category"], r["nominal_case"])
            for r in packet["lexical_readings"]]
    if rows != list(_FORMS):
        raise ValueError("installed lexical interpretation differs")
    sources = {}
    for item in packet["sources"]:
        if item["source_id"] in sources:
            raise ValueError("duplicate retained source")
        data = acquisition._read_bounded(acquisition._installed_path(item["repository_path"]), item["bytes"])
        if len(data) != item["bytes"] or sha256(data).hexdigest() != item["source_sha256"]:
            raise ValueError("retained source differs")
        sources[item["source_id"]] = data
    passages = set()
    for passage in packet["passages"]:
        if passage["id"] in passages:
            raise ValueError("duplicate source passage")
        passages.add(passage["id"])
        data = sources[passage["source_id"]]
        if sha256(data).hexdigest() != passage["source_sha256"]:
            raise ValueError("passage source identity differs")
        start, end = passage["byte_start_0based"], passage["byte_end_0based_exclusive"]
        excerpt = data[start:end]
        if excerpt.decode("utf-8", "strict") != passage["raw_text"] or sha256(excerpt).hexdigest() != passage["span_sha256"]:
            raise ValueError("retained passage differs")
        lines = data.splitlines(keepends=True)
        first, last = passage["line_start_1based"], passage["line_end_1based_inclusive"]
        if sum(map(len, lines[:first - 1])) != start or sum(map(len, lines[:last])) != end:
            raise ValueError("passage line and byte positions differ")
    for row in packet["lexical_readings"]:
        if not row["source_refs"] or not set(row["source_refs"]) <= passages:
            raise ValueError("lexical interpretation has missing source references")
    return {"schema": packet["schema"], "sha256": SOURCE_SCOPE_SHA256,
            "sources": len(sources), "passages": len(passages), "passage_ids": sorted(passages),
            "lexical_sources": [{"surface": row["surface"], "lexeme_id": row["lexeme_id"],
                                 "source_refs": row["source_refs"]} for row in packet["lexical_readings"]],
            "authority": "SOURCE_IDENTITY_AND_AUTHORED_SCOPE"}


def _native(request):
    if not _NATIVE_PATH.is_file():
        raise FileNotFoundError("Build formal target productiveClauseV1")
    with tempfile.TemporaryDirectory(prefix="nabt-productive-clause-") as directory:
        path, output_path = Path(directory) / "request.json", Path(directory) / "response.json"
        path.write_text(_wire(request), encoding="utf-8")
        with output_path.open("wb") as output:
            process = subprocess.run([str(_NATIVE_PATH), str(path)], stdout=output,
                                     stderr=subprocess.DEVNULL, timeout=30, check=False)
        if output_path.stat().st_size > MAX_REPORT_BYTES:
            raise OverflowError("native response byte budget")
        report = _load(output_path.read_bytes())
    if process.returncode == 2 and report == {
            "law_id": SYNTAX_LAW_ID, "status": "RESOURCE_EXHAUSTED", "error": "RESOURCE_LIMIT"}:
        raise OverflowError("native resource budget")
    if process.returncode != 0 or type(report) is not dict:
        raise ValueError("native transport rejected valid request")
    return report


def _candidate_space(proposal=None, *, checked=False, complete=False, blocked_by=()):
    exact = checked and proposal["status"] in ("LICENSED_CLAUSE", "REJECTED_IN_SCOPE")
    reading = proposal["reading"] if checked else None
    count = (1 if reading is not None else 0) if exact else None
    return {"domain_id": SYNTAX_LAW_ID, "unit": "scoped_syntactic_reading",
            "completeness_scope": "installed_finite_grammar",
            "count_mode": "EXACT" if exact else "UNMEASURED", "count": count,
            "hartley_bits": 0.0 if count == 1 else None,
            "unknown_reason": None if exact else "NATIVE_READING_NOT_WITHIN_VERIFIED_SCOPE",
            "candidates": [{"id": proposal["reading_id"],
                            "state": "LICENSED" if complete else "PENDING",
                            "obligations": [] if complete else list(blocked_by)}] if reading is not None else [],
            "world_truth_established": False}


def _base():
    return {"schema": "nabt.acquired-productive-clause-result.v1", "law_id": LAW_ID,
            "status": "DEFER", "verified": False, "chain_complete": False,
            "source_evidence": None, "acquisition": None, "syntax": None,
            "gates": {}, "blocked_by": [], "reading": None,
            "candidate_space": _candidate_space(),
            "world_truth_established": False, "referents_established": False,
            "entails_exclusivity": False, "all_arabic_complete": False}


def evaluate(text, *, source_id="input", revision="1", scope="default", ending="wasl", onset="word_initial"):
    result = _base()
    try:
        request = _request(text, source_id, revision, scope, ending, onset)
    except OverflowError:
        return {**result, "status": "RESOURCE_EXHAUSTED", "blocked_by": ["SOURCE_BUDGET"]}
    except (ValueError, TypeError, UnicodeError):
        return {**result, "status": "INVALID_INPUT", "blocked_by": ["INVALID_SOURCE_OR_BINDING"]}
    binding = {key: request[key] for key in ("source_id", "revision", "scope", "ending", "onset")}
    result.update(binding=binding, source_sha256=sha256(request["text"].encode("utf-8")).hexdigest())
    failures = []
    try:
        result["source_evidence"] = source_inventory()
    except OverflowError:
        failures.append("RESOURCE_EXHAUSTED")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError):
        failures.append("SOURCE_EVIDENCE_UNAVAILABLE")
    acquired = acquisition.read_acquired(text, **binding)
    result["acquisition"] = acquired
    proposal = propose_clause(text, **binding)
    checked, native_failure = False, None
    try:
        if _wire(_native(request)) != _wire(proposal):
            raise ValueError("whole native syntax replay differs")
        checked = True
    except (FileNotFoundError, PermissionError):
        native_failure = "VERIFICATION_UNAVAILABLE"
    except (subprocess.TimeoutExpired, OverflowError):
        native_failure = "RESOURCE_EXHAUSTED"
    except (OSError, ValueError, TypeError, RecursionError):
        native_failure = "VERIFICATION_FAILED"
    result["syntax"] = {"verified": checked, "status": proposal["status"] if checked else native_failure,
                        "native_result": proposal if checked else None}
    underlying = acquired.get("acquisition", {})
    aligned = _wire([{key: word.get(key) for key in _COORDS} for word in underlying.get("words", [])]) == \
              _wire([{key: token[key] for key in _COORDS} for token in proposal["tokens"]])
    gates = dict(zip(GATE_NAMES, (
        result["source_evidence"] is not None,
        acquired.get("status") == "ACQUIRED", acquired.get("verified") is True,
        acquired.get("shape_verified") is True, checked,
        checked and proposal["reading"] is not None,
        all(underlying.get(key) == request[key] for key in request),
        checked and aligned, ending == "wasl" and onset == "word_initial",
    )))
    result["gates"] = gates
    result["blocked_by"] = [name for name, passed in gates.items() if not passed]
    if all(gates.values()):
        result.update(status="LICENSED_CLAUSE", verified=True, chain_complete=True, reading=proposal["reading"])
    else:
        failures += [native_failure, acquired.get("status")]
        if "SHAPE_CHECK_FAILED" in failures:
            failures.append("VERIFICATION_FAILED")
        for status in ("INVALID_INPUT", "RESOURCE_EXHAUSTED", "SOURCE_EVIDENCE_UNAVAILABLE",
                       "VERIFICATION_FAILED", "VERIFICATION_UNAVAILABLE"):
            if status in failures:
                result["status"] = status
                break
        else:
            # This is rejection of this installed frame only. Source/acquisition
            # debt prevents promotion of a nested structural rejection as well.
            if checked and proposal["status"] == "REJECTED_IN_SCOPE" and all(
                    passed for name, passed in gates.items() if name != "finite_grammar_reading"):
                result["status"] = "REJECTED_IN_SCOPE"
    result["candidate_space"] = _candidate_space(proposal, checked=checked,
        complete=result["chain_complete"], blocked_by=result["blocked_by"])
    if len(_wire(result).encode("utf-8")) > MAX_REPORT_BYTES:
        return {**_base(), "status": "RESOURCE_EXHAUSTED", "blocked_by": ["WHOLE_REPORT_BUDGET"]}
    return result


def verify(report, *, text, source_id, revision, scope, ending, onset):
    """Reopen every dependency and compare the whole typed receipt to replay."""
    try:
        try:
            encoded = acquisition._receipt_wire(report)
        except ValueError as error:
            # The historical serializer reports this resource bound as ValueError.
            # Preserve its typed JSON checks without turning exhaustion into invalidity.
            if str(error) == "receipt byte budget":
                return {"valid": False, "replay_matches": False, "status": "RESOURCE_EXHAUSTED"}
            raise
        if len(encoded) > MAX_REPORT_BYTES:
            return {"valid": False, "replay_matches": False, "status": "RESOURCE_EXHAUSTED"}
        expected = evaluate(text, source_id=source_id, revision=revision, scope=scope, ending=ending, onset=onset)
        if encoded != _wire(expected).encode("utf-8"):
            raise ValueError("whole receipt differs from replay")
        return {"valid": expected["chain_complete"], "replay_matches": True,
                "status": "VERIFIED_COMPOSITE_RECEIPT" if expected["chain_complete"] else expected["status"],
                "blocked_by": expected["blocked_by"]}
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        return {"valid": False, "replay_matches": False, "status": "INVALID_RECEIPT"}
