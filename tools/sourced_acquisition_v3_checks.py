"""Independent structural checks for the v3 evaluator, using only the stdlib.

These checks do not grant native, grammatical, semantic, or world authority.
They check that claimed stages refer to the independently supplied request and
that source pieces, realized cells, and downstream projections stay aligned.
No runtime, source packet, or evaluation matrix is imported here.
"""
from hashlib import sha256
import json


SEPARATORS = frozenset(' \t\r\n.،؛,:!?؟()[]{}«»"“”')
COORDS = ("start", "end", "byte_start", "byte_end", "raw")
PERSON_GATES = frozenset(("source_acquired", "acquisition_native_checked", "source_shapes",
                          "syntax_native_checked", "finite_grammar_reading", "same_source_binding"))
PR34_GATES = frozenset(("source_acquired", "query_acquired", "source_shapes", "query_shapes",
                        "reading_and_closures", "same_onset", "same_binding"))


def _wire(value):
    pending = [(value, 0)]
    count = 0
    while pending:
        item, depth = pending.pop()
        count += 1
        if depth > 128 or count > 1_000_000:
            raise ValueError("JSON structural limit")
        if type(item) is dict:
            if any(type(key) is not str for key in item):
                raise ValueError("non-JSON object key")
            pending.extend((child, depth + 1) for child in item.values())
        elif type(item) is list:
            pending.extend((child, depth + 1) for child in item)
        elif type(item) not in (str, int, bool, type(None)):
            raise ValueError("non-JSON value")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _same(left, right):
    try:
        return _wire(left) == _wire(right)
    except (ValueError, TypeError, RecursionError):
        return False


def _fields(value, expected):
    return type(value) is dict and all(key in value and _same(value[key], item)
                                      for key, item in expected.items())


def _span(text, start, end):
    return {"start": start, "end": end, "byte_start": len(text[:start].encode("utf-8")),
            "byte_end": len(text[:end].encode("utf-8")), "raw": text[start:end]}


def _words(text, *, natural=False):
    result, cursor = [], 0
    separators = SEPARATORS | frozenset(";'‘’`") if natural else SEPARATORS
    def boundary(char):
        return char in separators or (natural and char.isspace())
    while cursor < len(text):
        if boundary(text[cursor]):
            cursor += 1
            continue
        start = cursor
        while cursor < len(text) and not boundary(text[cursor]):
            cursor += 1
        result.append(_span(text, start, cursor))
    return result


def _partition(pieces, text):
    if type(pieces) is not list:
        return False
    cursor = 0
    for piece in pieces:
        if type(piece) is not dict:
            return False
        start, end = piece.get("start"), piece.get("end")
        if (type(start) is not int or type(end) is not int or start != cursor or
                not start < end <= len(text) or not _fields(piece, _span(text, start, end))):
            return False
        cursor = end
    return cursor == len(text)


def _cells(value):
    return type(value) is list and all(type(cell) is int and 0 <= cell < 116 for cell in value)


def source_checks(acquisition, *, text, source_id, revision="1", scope, ending, onset,
                  law="nabt.sourced-acquisition.v3"):
    """Check source geometry independently of reported word membership."""
    checks = dict.fromkeys(("identity", "restoration", "pieces", "word_members", "cell_domain"), False)
    if type(acquisition) is not dict or type(text) is not str:
        return checks
    checks["identity"] = _fields(acquisition, {
        "text": text, "source_id": source_id, "revision": revision, "scope": scope,
        "ending": ending, "onset": onset, "law_id": law, "alphabet_id": "nabt.a116.v1"})
    pieces, words = acquisition.get("pieces"), acquisition.get("words")
    if (type(pieces) is not list or type(words) is not list or
            any(type(piece) is not dict for piece in pieces + words)):
        return checks
    checks["restoration"] = (all(type(piece.get("raw")) is str for piece in pieces) and
                             "".join(piece["raw"] for piece in pieces) == text)
    checks["cell_domain"] = all(_cells(piece.get("cells")) for piece in pieces + words)
    checks["pieces"] = _partition(pieces, text)
    if not checks["pieces"] or not checks["cell_domain"]:
        return checks
    expected_words = _words(text)
    if len(words) != len(expected_words):
        return checks
    used = set()
    for word, expected in zip(words, expected_words):
        # v1/v2 words omit raw; if supplied it must also match exactly.
        required = {key: value for key, value in expected.items() if key != "raw" or "raw" in word}
        if not _fields(word, required):
            return checks
        start, end = expected["start"], expected["end"]
        members = [(i, piece) for i, piece in enumerate(pieces)
                   if piece["start"] < end and start < piece["end"]]
        if (not members or members[0][1]["start"] != start or members[-1][1]["end"] != end or
                any(not start <= piece["start"] < piece["end"] <= end or
                    any(char in SEPARATORS for char in piece["raw"]) or i in used
                    for i, piece in members)):
            return checks
        if not _same(word["cells"], [cell for _, piece in members for cell in piece["cells"]]):
            return checks
        used.update(i for i, _ in members)
    if any(i not in used and (piece["cells"] or not all(char in SEPARATORS for char in piece["raw"]))
           for i, piece in enumerate(pieces)):
        return checks
    checks["word_members"] = True
    return checks


def realization_checks(acquisition, realization, **binding):
    """Check retained source spans, elision, phrase cells and cell intervals."""
    checks = dict.fromkeys(("geometry", "piece_preservation", "word_preservation", "joins",
                            "phrase_cells", "cell_intervals", "elision"), False)
    if type(acquisition) is not dict or type(realization) is not dict:
        return checks
    realized = {**acquisition, "pieces": realization.get("pieces"), "words": realization.get("words")}
    checks["geometry"] = all(source_checks(realized, **binding).values())
    if not checks["geometry"] or not all(source_checks(acquisition, **binding).values()):
        return checks
    original, pieces = acquisition["pieces"], realized["pieces"]
    original_words, words = acquisition["words"], realized["words"]
    checks["piece_preservation"] = len(original) == len(pieces) and all(
        _fields(right, {key: left[key] for key in COORDS}) for left, right in zip(original, pieces))
    checks["word_preservation"] = len(original_words) == len(words) and all(
        _fields(right, {key: left[key] for key in COORDS}) for left, right in zip(original_words, words))
    if not checks["piece_preservation"] or not checks["word_preservation"]:
        return checks
    onset, text = binding["onset"], binding["text"]
    complete = acquisition.get("status") == "ACQUIRED" and realization.get("status") == "REALIZED"
    intervals = onset == "connected" and complete
    flattened = [cell for piece in pieces for cell in piece["cells"]]
    checks["phrase_cells"] = (realization.get("mode") == onset and
                              _same(realization.get("phrase_cells"), flattened if intervals else []))
    cursor, valid = 0, True
    for piece in pieces:
        stop = cursor + len(piece["cells"])
        valid = valid and _fields(piece, {"cell_start": cursor if intervals else None,
                                         "cell_end": stop if intervals else None})
        cursor = stop
    checks["cell_intervals"] = valid
    joins = realization.get("joins")
    if type(joins) is not list or len(joins) != max(0, len(words) - 1):
        return checks
    valid, elided_starts = True, set()
    for index, join in enumerate(joins):
        left, right = words[index], words[index + 1]
        if (type(join) is not dict or type(join.get("elided")) is not bool or
                not _fields(join, {"left_word": index, "right_word": index + 1,
                                   "span": _span(text, left["end"], right["start"])})):
            valid = False
            continue
        if onset == "word_initial":
            valid = valid and _fields(join, {"status": "CITATION_BOUNDARY", "rule": "CITATION_BOUNDARY", "elided": False})
        else:
            valid = valid and join.get("status") in ("JOINED", "DEFER")
            if complete:
                valid = valid and join.get("status") == "JOINED"
            if join.get("status") == "JOINED":
                previous = [piece for piece in original if left["start"] <= piece["start"] < left["end"]]
                last = previous[-1]
                vowels = [char for char in last["raw"][1:] if char in "ًٌٍَُِْ"]
                valid = valid and (text == " ".join(word["raw"] for word in words) and
                    len(vowels) == 1 and vowels[0] in "َُِ" and bool(last["cells"]) and
                    last["cells"][-1] % 4 == "َُِ".index(vowels[0]))
            if join["elided"]:
                valid = valid and join.get("status") == "JOINED" and join.get("rule") == "ARTICLE_WASL_ELISION"
                elided_starts.add(right["start"])
            elif join.get("status") == "JOINED":
                valid = valid and join.get("rule") == "ONSET_UNCHANGED"
    checks["joins"] = valid
    valid = True
    for before, after in zip(original, pieces):
        if after["start"] in elided_starts:
            valid = valid and (before["raw"][0] in "اٱ" and before["cells"] == [112] and
                                after["cells"] == [] and after.get("rule") == "ARTICLE_WASL_ELISION")
        elif complete or onset == "word_initial":
            valid = valid and _same(before["cells"], after["cells"])
    checks["elision"] = valid
    return checks


def _shape(row, cells, mode):
    return (_fields(row, {"status": "SHAPE_LICENSED", "mode": mode}) and
            _fields(row.get("certificate"), {"cells": cells, "mode": mode,
                "alphabet_id": "nabt.a116.v1", "source_text": None, "source_sha256": None,
                "start_state": 0, "cell_length": len(cells), "certificate_type": "WORD_SHAPE"}))


def _shape_checks(report, *, ending, onset, v3):
    """Check shape-to-cell binding only; native shape replay is a separate gate."""
    if type(report) is not dict or type(report.get("acquisition")) is not dict:
        return {"handoff_bindings": True, "complete": False}
    words, rows = report["acquisition"].get("words"), report.get("shape_handoffs")
    if type(words) is not list or type(rows) is not list:
        return {"handoff_bindings": False, "complete": False}
    if v3 and onset == "connected":
        phrase = report.get("phrase_shape")
        valid = rows == []
        licensed = type(phrase) is dict and phrase.get("status") == "SHAPE_LICENSED"
        if licensed:
            realization = report.get("realization")
            valid = valid and type(realization) is dict and _shape(phrase, realization.get("phrase_cells"), ending)
        return {"handoff_bindings": valid, "complete": valid and licensed}
    if rows and len(rows) != len(words):
        return {"handoff_bindings": False, "complete": False}
    valid = not v3 or report.get("phrase_shape") is None
    for index, row in enumerate(rows):
        word = words[index]
        mode = ending if index == len(words) - 1 else "wasl"
        valid = valid and _fields(row, {"word_index": index, "mode": mode,
            "span": {key: word[key] for key in COORDS[:-1]}})
        if type(row) is dict and row.get("status") == "SHAPE_LICENSED":
            valid = valid and _shape(row, word["cells"], mode)
    complete = bool(rows) and len(rows) == len(words) and all(
        type(row) is dict and row.get("status") == "SHAPE_LICENSED" for row in rows)
    return {"handoff_bindings": valid, "complete": valid and complete}


def _gate_set(value, keys):
    return type(value) is dict and set(value) == keys and all(type(item) is bool for item in value.values())


def _byte_span(span, raw):
    if type(span) is not dict:
        return False
    start, end = span.get("start_byte"), span.get("end_byte")
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(raw):
        return False
    try:
        raw[:start].decode("utf-8"); text = raw[start:end].decode("utf-8"); raw[end:].decode("utf-8")
    except UnicodeError:
        return False
    return _fields(span, {"raw_text": text, "sha256": sha256(raw[start:end]).hexdigest()})


def _natural_checks(report, *, text, source_id, revision, scope, ending, onset):
    checks = {}
    raw = text.encode("utf-8")
    claimed = bool(report.get("selected_sense_ids")) or report.get("semantic_scope_complete") is True
    if "source" in report or claimed:
        checks["natural_source"] = _fields(report.get("source"), {"source_id": source_id,
            "revision": revision, "raw_text": text, "sha256": sha256(raw).hexdigest(), "bytes": len(raw)})
        checks["natural_binding"] = _same(report.get("binding"), dict(source_id=source_id,
            revision=revision, scope=scope, ending=ending, onset=onset))
    occurrences = report.get("occurrences")
    if type(occurrences) is not list:
        return {**checks, "natural_occurrences": False}
    candidates, selected, occurrence_checks = set(), set(), []
    word_spans = {(word["byte_start"], word["byte_end"]) for word in _words(text, natural=True)}
    for occurrence in occurrences:
        if type(occurrence) is not dict:
            occurrence_checks.append(False); continue
        span, request = occurrence.get("span"), occurrence.get("native_request")
        valid = (_byte_span(span, raw) and (span["start_byte"], span["end_byte"]) in word_spans and
                 type(request) is dict)
        if not valid:
            occurrence_checks.append(False); continue
        frame = request.get("frame")
        valid = _fields(frame, {"expression": occurrence.get("expression"), "convention": "linguistic"}) and _fields(
            frame.get("occurrence") if type(frame) is dict else None,
            {"source": source_id, "revision": revision, "raw": text, "start_byte": span["start_byte"],
             "end_byte": span["end_byte"], "referent": "unresolved", "time": "unspecified", "context": scope})
        if "cue_span" in occurrence:
            cue = occurrence["cue_span"]
            valid = valid and _byte_span(cue, raw) and cue["start_byte"] <= span["start_byte"] < span["end_byte"] <= cue["end_byte"]
        rows, chosen = occurrence.get("candidates"), occurrence.get("selected_sense_ids")
        if (type(rows) is not list or any(type(row) is not dict or type(row.get("sense_id")) is not str for row in rows)
                or type(chosen) is not list or any(type(sense) is not str for sense in chosen)):
            occurrence_checks.append(False); continue
        candidates.update(row["sense_id"] for row in rows); selected.update(chosen)
        valid = valid and _same(request.get("proposed"), [row.get("candidate") for row in rows])
        valid = valid and all(_fields(row.get("candidate"), {"intended_sense": row["sense_id"]}) for row in rows)
        known = request.get("known")
        valid = valid and type(known) is list
        if type(known) is list:
            for premise in known:
                valid = valid and _fields(premise, {"scope": scope}) and type(premise.get("positive")) is bool
                value = premise.get("value") if type(premise) is dict else None
                if type(value) is dict and "frame" in value:
                    valid = valid and _same(value["frame"], frame)
        supported = {row["sense_id"] for row in rows if row.get("support_status") == "SUPPORTED_PREMISES"}
        valid = valid and set(chosen) <= supported and (not chosen or (
            occurrence.get("native_checked") is True and "cue_span" in occurrence))
        if occurrence.get("native_checked") is True:
            native = occurrence.get("native_result")
            valid = valid and _fields(native, {"status": "CHECKED", "law_id": "nabt.linguistic-truth.v1",
                "authority": "CONDITIONAL_SUPPLIED_LEDGER", "complete_proposal": True,
                "all_arabic_senses_enumerated": False, "world_truth_asserted": False})
            native_rows = native.get("rows") if type(native) is dict else None
            valid = valid and type(native_rows) is list and len(native_rows) == len(rows)
            if type(native_rows) is list and len(native_rows) == len(rows):
                valid = valid and all(_fields(native_row, {"candidate": row.get("candidate"),
                    "kind": row.get("native_use_kind"), "verdict": row.get("support_status")})
                    for row, native_row in zip(rows, native_rows))
        occurrence_checks.append(valid)
    checks["natural_occurrences"] = all(occurrence_checks)
    checks["natural_candidate_union"] = _same(report.get("candidate_sense_ids"), sorted(candidates))
    # A failed global native call may clear top-level selections while retaining
    # independently checked per-occurrence diagnostics; it grants no reading.
    checks["natural_selected_union"] = _same(report.get("selected_sense_ids"), sorted(selected)) or (
        report.get("status") in ("RESOURCE_EXHAUSTED", "VERIFICATION_UNAVAILABLE") and report.get("selected_sense_ids") == [])
    checks["natural_native_gate"] = report.get("native_checked") is not True or (
        bool(occurrences) and all(occurrence.get("native_checked") is True for occurrence in occurrences))
    checks["natural_semantic_gate"] = not claimed or (report.get("semantic_scope_complete") is True and
        report.get("native_checked") is True and report.get("status") == "COMPLETE" and bool(selected))
    return checks


def _syntax_checks(report, *, text, source_id, revision, scope, ending, onset, task):
    checks = {}
    binding = dict(source_id=source_id, revision=revision, scope=scope, ending=ending, onset=onset)
    if "binding" in report or report.get("chain_complete") is True:
        checks["syntax_outer_binding"] = (_same(report.get("binding"), binding) and report.get("task") == task and
            report.get("source_sha256") == sha256(text.encode("utf-8")).hexdigest())
    syntax = report.get("syntax")
    if type(syntax) is not dict or syntax.get("verified") is not True:
        return {**checks, "syntax_unchecked_projection": report.get("person") is None and report.get("nominal") is None}
    native = syntax.get("native_result")
    checks["syntax_native_binding"] = _fields(native, {**binding, "text": text, "task": task,
                                                         "law_id": "nabt.acquired-syntax.v3"})
    if type(native) is not dict:
        return checks
    tokens = native.get("tokens")
    expected = _words(text)
    checks["syntax_source_pieces"] = _partition(native.get("source_pieces"), text)
    checks["syntax_tokens"] = type(tokens) is list and len(tokens) == len(expected) and all(
        _fields(token, span) for token, span in zip(tokens, expected))
    checks["syntax_status"] = syntax.get("status") == native.get("status")
    if not checks["syntax_tokens"]:
        return checks
    person, nominal = native.get("person"), native.get("nominal")
    valid = True
    if person is not None:
        index = person.get("word_index") if type(person) is dict else None
        valid = type(index) is int and 0 <= index < len(tokens)
        if valid:
            token = tokens[index]
            valid = (_same(person.get("source_word"), token) and
                _same(person.get("source_suffix"), _span(text, token["end"] - 2, token["end"])) and
                token["start"] <= token["end"] - 2 and person.get("source_vowel") == text[token["end"] - 1] and
                type(person.get("person")) is int and person["person"] in (1, 2) and person.get("referent") is None)
    if nominal is not None:
        si, pi = (nominal.get("subject_index"), nominal.get("predicate_index")) if type(nominal) is dict else (None, None)
        valid = valid and type(si) is int and type(pi) is int and si != pi and 0 <= si < len(tokens) and 0 <= pi < len(tokens)
        if valid:
            valid = (_same(nominal.get("source_words"), tokens) and
                _same(nominal.get("subject_source"), tokens[si]) and _same(nominal.get("predicate_source"), tokens[pi]) and
                nominal.get("referent") is None and nominal.get("denotation_cardinality") is None)
            for role, index, count in (("subject", si, 3 if nominal.get("number") == "dual" else 1),
                                       ("predicate", pi, 1 if nominal.get("number") == "singular" else 3)):
                token = tokens[index]
                valid = valid and token["start"] <= token["end"] - count and _same(
                    nominal.get(role + "_ending"), _span(text, token["end"] - count, token["end"]))
    checks["syntax_projection_spans"] = valid
    checks["syntax_projection_gate"] = (report.get("chain_complete") is True and
        _same(report.get("person"), person) and _same(report.get("nominal"), nominal)) or (
        report.get("chain_complete") is not True and report.get("person") is None and report.get("nominal") is None)
    return checks


def audit_report(entry_point, report, *, text, source_id, revision="1", scope, ending, onset,
                 task=None, query=None, query_ending=None, time="unspecified"):
    """Return safety checks; neither a receipt's own gates nor hashes are authority."""
    try:
        return _audit_report(entry_point, report, text=text, source_id=source_id, revision=revision,
            scope=scope, ending=ending, onset=onset, task=task, query=query, query_ending=query_ending, time=time)
    except (KeyError, IndexError, TypeError, ValueError, UnicodeError, RecursionError):
        return {"source_safe": False, "chain_safe": False, "claim_safe": False,
                "source_checks": [], "realization_checks": [], "binding_checks": {"well_formed_report": False}}


def _audit_report(entry_point, report, *, text, source_id, revision, scope, ending, onset,
                  task, query, query_ending, time):
    if type(report) is not dict:
        raise ValueError("report must be an object")
    _wire(report)
    binding = dict(text=text, source_id=source_id, revision=revision, scope=scope, ending=ending, onset=onset)
    native_scope = _wire({"scope": scope, "time": time})
    v3 = entry_point != "conditional_pr34"
    receipts = ([report] if entry_point == "connected" else [report.get("acquisition")]) if v3 else [
        report.get("source_acquisition"), report.get("query_acquisition")]
    source, realization, stages, complete = [], [], {}, []
    for index, receipt in enumerate(receipts):
        request = binding if v3 else {**binding, "text": text if index == 0 else query,
            "ending": ending if index == 0 else query_ending, "scope": native_scope,
            "law": "nabt.aligned-acquisition.v2"}
        if type(receipt) is not dict or type(receipt.get("acquisition")) is not dict:
            complete.append(False)
            if type(receipt) is dict and (receipt.get("verified") is True or receipt.get("status") == "ACQUIRED" or receipt.get("shape_verified") is True):
                stages[f"acquisition_{index}_missing_source"] = False
            continue
        acquisition = receipt["acquisition"]
        source.append(source_checks(acquisition, **request))
        stages[f"acquisition_{index}_onset"] = receipt.get("onset") == onset
        if v3:
            realization.append(realization_checks(acquisition, receipt.get("realization"), **request))
        shapes = _shape_checks(receipt, ending=request["ending"], onset=onset, v3=v3)
        stages[f"acquisition_{index}_shape_bindings"] = shapes["handoff_bindings"]
        stages[f"acquisition_{index}_shape_claim"] = not v3 or receipt.get("shape_verified") is not True or shapes["complete"]
        complete.append(receipt.get("status") == "ACQUIRED" and receipt.get("verified") is True and
                        acquisition.get("status") == "ACQUIRED" and shapes["complete"] and
                        (not v3 or receipt.get("shape_verified") is True))
    chain = report.get("chain_complete") is True
    shape_safe = all(stages.values())
    if entry_point == "connected":
        stages["connected_grant"] = report.get("status") != "ACQUIRED" or complete == [True]
    elif entry_point == "person_nominal":
        stages.update(_syntax_checks(report, **binding, task=task))
        if chain or report.get("verified") is True or report.get("person") is not None or report.get("nominal") is not None or report.get("status") in ("LICENSED_PERSON", "LICENSED_NOMINAL"):
            syntax = report.get("syntax") or {}; native = syntax.get("native_result") or {}
            stages["person_chain"] = (chain and report.get("verified") is True and complete == [True] and
                _gate_set(report.get("gates"), PERSON_GATES) and all(report["gates"].values()) and
                syntax.get("verified") is True and native.get("reading_id") is not None and
                native.get("status") == report.get("status") and
                ((task == "person" and report.get("status") == "LICENSED_PERSON" and type(report.get("person")) is dict and report.get("nominal") is None) or
                 (task == "nominal_syntax" and report.get("status") == "LICENSED_NOMINAL" and type(report.get("nominal")) is dict and report.get("person") is None)))
    elif entry_point == "natural":
        stages.update(_natural_checks(report, **binding))
        stages["natural_chain"] = not chain or (complete == [True] and report.get("semantic_scope_complete") is True and report.get("native_checked") is True)
    elif entry_point == "conditional_pr34":
        if "binding" in report or chain:
            stages["pr34_binding"] = _same(report.get("binding"), {"source_id": source_id, "revision": revision,
                "scope": scope, "time": time, "native_scope": native_scope, "onset": onset,
                "source_ending": ending, "query_ending": query_ending})
        licensed = report.get("licensed_inference")
        if type(licensed) is dict and licensed.get("verified") is True:
            native = licensed.get("native_result")
            stages["pr34_source_metadata"] = _fields(licensed.get("source"), {"source_id": source_id,
                "revision": revision, "raw_text": text, "bytes": len(text.encode("utf-8")), "sha256": sha256(text.encode("utf-8")).hexdigest()})
            stages["pr34_query_metadata"] = _fields(licensed.get("query"), {"raw_text": query,
                "bytes": len(query.encode("utf-8")), "sha256": sha256(query.encode("utf-8")).hexdigest()})
            stages["pr34_inference_binding"] = _fields(licensed.get("binding"), {"source_id": source_id,
                "revision": revision, "scope": scope, "time": time, "native_scope": native_scope})
            proposal = licensed.get("proposal")
            stages["pr34_proposal_binding"] = _fields(proposal, {"law_id": "nabt.licensed-inference.v1",
                "source": {"identity": source_id, "revision": revision, "scope": native_scope, "text": text}, "query_text": query})
            stages["pr34_native_binding"] = _fields(native, {"source_text": text, "query_text": query,
                "source_id": source_id, "revision": revision, "source_scope": native_scope,
                "law_id": "nabt.licensed-inference.v1", "verified": True})
            stages["pr34_native_projection"] = _fields(native, {"status": licensed.get("status"), "aggregate": licensed.get("aggregate")})
        if chain or report.get("verified") is True or report.get("answer") is not None:
            stages["pr34_chain"] = (chain and report.get("verified") is True and complete == [True, True] and onset == "word_initial" and
                _gate_set(report.get("gates"), PR34_GATES) and all(report["gates"].values()) and
                _fields(licensed, {"verified": True, "native_checked": True, "closures_checked": True, "all_readings_complete": True}) and
                _same(report.get("answer"), {"status": licensed.get("status"), "aggregate": licensed.get("aggregate")}) and
                report.get("status") == licensed.get("status"))
    else:
        raise ValueError("unknown entry point")
    # Explicit denials are typed booleans; none may be promoted by a stage join.
    forbidden = ("world_truth_established", "all_arabic_complete", "author_intention_established",
        "reference_resolved", "grammar_certified", "all_arabic_senses_enumerated", "referents_established",
        "general_acquisition_refinement_proved", "python_lean_composition_theorem",
        "ordinary_arabic_completeness_established", "linguistic_rejection")
    stages["bounded_authority"] = all(report[key] is False for key in forbidden if key in report)
    stages["typed_stage_flags"] = all(type(report[key]) is bool for key in (
        "verified", "chain_complete", "shape_verified", "native_checked", "semantic_scope_complete") if key in report)
    geometric = all(all(check.values()) for check in source + realization)
    safe = geometric and all(stages.values())
    return {"source_safe": geometric and all(value for key, value in stages.items()
                if any(token in key for token in ("binding", "source", "tokens", "occurrences", "spans"))),
            "chain_safe": safe, "claim_safe": safe and shape_safe,
            "source_checks": source, "realization_checks": realization, "binding_checks": stages}
