"""Bounded Arabic intended-sense acquisition from raw text, with source replay.

The installed lexical ledger supplies conventions; it does not supply the
user's intended meaning. This reader acquires that meaning only from complete
explicit Arabic metalinguistic clauses. Every other clause remains visible.
The native checker verifies a conditional calculus, never external reality.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess

from nabt import foundation
from nabt.errors import NabtError

from .calculus import canonical_json, enumerate_candidates, evaluate_request

ROOT = Path(__file__).resolve().parents[2]
LAW_ID = "nabt.linguistic-truth-acquisition.v5"
_MARKS = re.compile(r"[\u064b-\u065f\u0670\u0640]")
_WORDS = re.compile(r"[^\s.!?؛;،؟«»()\[\]\"“”]+")
_SEPARATORS = re.compile(r"[.!?؛;؟\r\n]+")


@dataclass(frozen=True)
class AcquisitionBudget:
    max_input_bytes: int = 65536
    max_occurrences: int = 256
    max_readings: int = 2048
    max_native_scan: int = 4096

    def __post_init__(self):
        for key, value in vars(self).items():
            if type(value) is not int or not 0 <= value <= 1000000:
                raise ValueError(f"{key} must be a bounded natural, not a boolean")
        if self.max_input_bytes > 65536:
            raise ValueError("max_input_bytes exceeds the installed 65536-byte bound")
        if self.max_native_scan > 4096:
            raise ValueError("max_native_scan exceeds the native 4096-entry bound")


def _wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _normal(text):
    # Retrieval spelling only. Exact original bytes and hamza/maqsura survive.
    return _MARKS.sub("", text)


def _is_observed_mark(char):
    return char != "\u0640" and _MARKS.fullmatch(char) is not None


def _marked_clusters(text):
    """Compare spellings without inventing vowels or interpreting shadda.

    Tatweel remains retrieval formatting only. Whitespace separates words;
    Arabic marks belong to their preceding carrier and stay significant.
    Source validation separately rejects orphan/conflicting marks.
    """
    words = []
    for word in text.split():
        clusters = []
        for char in word:
            if char == "\u0640":
                continue
            if _is_observed_mark(char):
                if not clusters:
                    return None
                clusters[-1][1].add(char)
            else:
                clusters.append([char, set()])
        words.append(clusters)
    return words


def _covers_observed_marks(observed, reviewed):
    """A supplied mark needs the same mark at the same reviewed carrier.

    An unmarked reviewed form is not a fully vocalized reading. Missing input
    marks may remain unspecified; visible input marks cannot be discarded to
    obtain an intended-use premise. This relation grants no source authority.
    """
    left, right = _marked_clusters(observed), _marked_clusters(reviewed)
    return (left is not None and right is not None and len(left) == len(right)
            and all(len(a) == len(b) and all(c == d and marks <= licensed
                    for (c, marks), (d, licensed) in zip(a, b))
                    for a, b in zip(left, right)))


def _orthography_gate(parsed, tokens, raw, inventory, senses, mark_review=None):
    """Bind each cue reading to its own reviewed expression/sense spellings.

    A separate source-replayed review may supply inflected spellings. It can
    only license existing parsed alternatives, never insert a semantic answer.
    Bare inventory forms remain available for unspecified input marks.
    """
    head = tokens[parsed["token_index"]]
    head_forms = ["ب" + form for row in inventory["designations"]
                  if row["expression"] == parsed["expression"] for form in row["forms"]]
    from .marked_forms import _reviewed_forms
    head_license = [] if mark_review is None else [candidate for candidate in
        _reviewed_forms(mark_review, parsed["expression"], "expression")
        if _covers_observed_marks(head["text"], candidate["form"])]
    head_ok = (any(_covers_observed_marks(head["text"], form) for form in head_forms)
               or bool(head_license))
    admitted, failures, licenses = [], [], []
    for reading in parsed["readings"]:
        issues = []
        reading_licenses = [{**candidate, "span": _span(raw, head["start"], head["end"])}
                            for candidate in head_license]
        covered = [(head["start"], head["end"])]
        if not head_ok:
            issues.append({"start": head["start"], "end": head["end"], "role": "expression"})
        for premise in reading:
            start, end = premise["start"], premise["end"]
            covered.append((start, end))
            observed = raw[start:end].decode("utf-8")
            reviewed = senses[parsed["expression"]][premise["sense_id"]]["forms"]
            derived = [] if mark_review is None else [candidate for form in reviewed
                for candidate in _reviewed_forms(mark_review, _normal(form), "sense")
                if _covers_observed_marks(observed, candidate["form"])]
            if not any(_covers_observed_marks(observed, form) for form in reviewed) and not derived:
                issues.append({"start": start, "end": end, "role": "sense",
                               "sense_id": premise["sense_id"]})
            reading_licenses.extend({**candidate, "sense_id": premise["sense_id"],
                                     "span": _span(raw, start, end)} for candidate in derived)
        for token in tokens:
            grammar_licenses = [] if mark_review is None else [candidate for candidate in
                _reviewed_forms(mark_review, token["normal"], "grammar")
                if _covers_observed_marks(token["text"], candidate["form"])]
            # New cue spellings have their own pinned lexical/derivational
            # evidence. A normal-form match alone never licenses a visible
            # vowel, and these receipts do not establish psychological intent.
            grammar_licenses.extend(candidate for candidate in parsed.get("syntax_licenses", [])
                if candidate["start"] == token["start"] and candidate["end"] == token["end"]
                and _covers_observed_marks(token["text"], candidate["form"]))
            if grammar_licenses:
                covered.append((token["start"], token["end"]))
                reading_licenses.extend({**candidate,
                    "span": _span(raw, token["start"], token["end"])} for candidate in grammar_licenses)
            cursor = token["start"]
            for char in token["text"]:
                end = cursor + len(char.encode("utf-8"))
                if (_is_observed_mark(char)
                        and not any(start <= cursor < stop for start, stop in covered)):
                    issues.append({"start": cursor, "end": end, "role": "grammar"})
                cursor = end
        if issues:
            failures.extend(issues)
        else:
            admitted.append(reading)
            licenses.extend(reading_licenses)
    if admitted:
        return {**parsed, "readings": admitted,
                "orthography_licenses": list({_wire(row): row for row in licenses}.values())}, []
    return None, list({_wire(issue): issue for issue in failures}.values())


def _span(raw, start, end):
    return {"start_byte": start, "end_byte": end, "sha256": _sha(raw[start:end]),
            "raw_text": raw[start:end].decode("utf-8")}


def _base():
    return {"schema": "nabt.linguistic-truth.v1", "law_id": LAW_ID,
            "authority": "SOURCE_ATTESTATION_AND_BOUNDED_INTENDED_USE_ONLY",
            "occurrences": [], "unclassified_spans": [], "acquired_premises": [],
            "acquisition_scan_complete": False, "all_installed_readings_retained": False,
            "intended_sense_acquired": False, "native_checked": False,
            "all_arabic_complete": False, "world_truth_established": False,
            "truth_of_claim_established": False, "empirical_validation_established": False,
            "external_observations": [], "unverified_verse_references": [],
            "accepted_language": "explicit metalinguistic clauses; standard fusha only"}


def _regions(text):
    cursor = 0
    for separator in _SEPARATORS.finditer(text):
        if cursor < separator.start():
            yield cursor, separator.start()
        cursor = separator.end()
    if cursor < len(text):
        yield cursor, len(text)


def _tokens(text, start, end, offsets):
    return [{"text": m.group(), "normal": _normal(m.group()),
             "start": offsets[m.start()], "end": offsets[m.end()]}
            for m in _WORDS.finditer(text, start, end)]


def _form_index(inventory):
    forms = {}
    senses = {}
    for row in inventory["designations"]:
        for form in row["forms"]:
            key = _normal(form)
            forms.setdefault(key, set()).add(row["expression"])
        senses.setdefault(row["expression"], {}).setdefault(row["sense_id"], {
            "sense_id": row["sense_id"], "gloss": row["gloss"], "forms": set()})["forms"].update(row["sense_forms"])
    by_id = {d["designation_id"]: d for d in inventory["designations"]}
    for row in inventory["relations"]:
        expression = by_id[row["designation_id"]]["expression"]
        senses.setdefault(expression, {}).setdefault(row["target_sense_id"], {
            "sense_id": row["target_sense_id"], "gloss": row["target_gloss"], "forms": set()})["forms"].update(row["target_forms"])
    return forms, senses


def _occurrence_forms(token, forms, *, retrieval_forms=()):
    """Retrieve possible segmentation; this never supplies an intended sense.

    A rejected or unsupported clause must not hide an observable known form
    behind common attached ب/و/ف. All matching segmentations are retained as
    retrieval proposals, while the cue parser still requires its whole grammar.
    """
    normal = token["normal"]
    matches = {}
    for prefix in ("", "ب", "و", "ف", "وب", "فب"):
        if not normal.startswith(prefix):
            continue
        for expression in forms.get(normal[len(prefix):], set()):
            matches.setdefault(expression, []).append({"normalized_prefix": prefix,
                "normalized_form": normal[len(prefix):], "authority": "LEXICAL_RETRIEVAL_PROPOSAL"})
        # Inflected retrieval forms belong only to this proposal path. Adding
        # accusative أسداً to designation.forms would also license the false
        # genitive cue بأسداً through the independent parser's bare form table.
        for row in retrieval_forms:
            if normal[len(prefix):] == row["normal"]:
                matches.setdefault(row["expression"], []).append({"normalized_prefix": prefix,
                    "normalized_form": row["normal"], "reviewed_form": row["form"],
                    "passage_ids": row["passage_ids"],
                    "authority": "LEXICAL_RETRIEVAL_PROPOSAL"})
    return matches


def _read_tail(tokens, start, sense_rows, negative, *, cue_verbs=("أعني", "أريد")):
    """Enumerate whole-tail readings; never accept a recognized prefix alone.

    Independent expressions joined by و are retained. A standalone لا changes
    polarity for the following group. `ولا أعني به`/`ولا أريد به` is a bounded
    same-occurrence reference. Unsupported suffixes invalidate the whole cue.
    """
    if len(tokens) > 256:
        raise OverflowError("cue exceeds the installed 256-token budget")
    forms = []
    for sense in sense_rows.values():
        for form in sorted(sense["forms"]):
            normalized = tuple(_normal(form).split())
            if normalized:
                forms.append((normalized, sense["sense_id"]))
    solutions = []
    work = 0

    def walk(position, positive, found):
        nonlocal work
        work += 1
        if work > 4096:
            raise OverflowError("cue exceeds the installed 4096-state budget")
        if len(solutions) >= 64:
            raise OverflowError("cue segmentation exceeds 64 readings")
        if position == len(tokens):
            solutions.append(found)
            return
        for form, sense_id in forms:
            length = len(form)
            if tuple(t["normal"] for t in tokens[position:position + length]) != form:
                continue
            evidence = {"sense_id": sense_id, "positive": positive,
                        "start": tokens[position]["start"],
                        "end": tokens[position + length - 1]["end"]}
            after = position + length
            if after == len(tokens):
                walk(after, positive, found + [evidence])
                continue
            rest = [t["normal"] for t in tokens[after:]]
            if len(rest) >= 3 and rest[0] == "ولا" and rest[1] in cue_verbs and rest[2] == "به":
                walk(after + 3, False, found + [evidence])
            if rest[0] in {"لا", "وليس", "ولا"}:
                walk(after + 1, False, found + [evidence])
            if rest[0] == "و":
                walk(after + 1, positive, found + [evidence])
            # A joined conjunction is consumed only if the remainder begins a
            # complete known sense phrase, rather than normalizing every word.
            if rest[0].startswith("و") and len(rest[0]) > 1 and rest[0] != "ولا":
                original = tokens[after]
                # Consume the raw conjunction cluster, including its marks;
                # adding only the two-byte waw would start a sense at a mark.
                cut = 0
                while cut < len(original["text"]) and original["text"][cut] == "\u0640":
                    cut += 1
                cut += 1
                while cut < len(original["text"]) and _MARKS.fullmatch(original["text"][cut]):
                    cut += 1
                remainder = original["text"][cut:]
                tokens[after] = {**original, "text": remainder, "normal": rest[0][1:],
                    "start": original["start"] + len(original["text"][:cut].encode("utf-8"))}
                walk(after, positive, found + [evidence])
                tokens[after] = original

    walk(start, not negative, [])
    # Two aliases with identical meaning and spans do not create extra proofs.
    unique = {_wire(solution): solution for solution in solutions}
    return list(unique.values())


def _parse_clause(tokens, forms, senses, *, extension=None):
    # Only the installed source loader supplies this extension to the public
    # reader. The private parser's fixture argument carries no authority. A
    # source witness for a verb does not license unreviewed conjunctions,
    # quotation scope, other persons, or a free synonym expansion.
    extension_rows = [] if extension is None else extension["cue_verbs"]
    cue_verbs = {"أعني", "أريد", *(row["normal"] for row in extension_rows)}
    index = 0
    negative = bool(tokens and tokens[0]["normal"] == "لا")
    if negative:
        index += 1
    if index >= len(tokens) or tokens[index]["normal"] not in cue_verbs:
        return None
    index += 1
    if index >= len(tokens) or not tokens[index]["normal"].startswith("ب"):
        return None
    expressions = forms.get(tokens[index]["normal"][1:], set())
    if len(expressions) != 1:
        return None
    expression = next(iter(expressions))
    if index + 1 == len(tokens):
        return None
    if len(tokens) > 256:
        raise OverflowError("cue exceeds the installed 256-token budget")
    # A deliberately small, versioned negative correction: exactly two known
    # sense phrases. Positive بل, chained corrections and ellipsis stay unknown.
    correction = negative and sum(t["normal"] == "بل" for t in tokens[index + 1:]) == 1
    if correction:
        pivot = next(i for i in range(index + 1, len(tokens)) if tokens[i]["normal"] == "بل")
        left = _read_tail(tokens[:pivot], index + 1, senses[expression], True, cue_verbs=cue_verbs)
        right = _read_tail(tokens[pivot + 1:], 0, senses[expression], False, cue_verbs=cue_verbs)
        readings = [a + b for a in left for b in right
                    if len(a) == len(b) == 1 and not a[0]["positive"] and b[0]["positive"]]
    else:
        readings = _read_tail(tokens, index + 1, senses[expression], negative, cue_verbs=cue_verbs)
    if not readings:
        return None
    syntax_licenses = [{"form": form, "role": "grammar", "law_id": extension["law_id"],
                        "review_sha256": extension["review_sha256"],
                        "passage_ids": row["passage_ids"], "start": token["start"], "end": token["end"],
                        "authority": "SOURCE_REPLAYED_BOUNDED_CUE_DERIVATION",
                        "native_acquisition_proof": False}
                       for token in tokens for row in extension_rows
                       if token["normal"] == row["normal"] for form in row["forms"]]
    return {"token_index": index, "expression": expression, "readings": readings,
            "negative_correction": correction, "syntax_licenses": syntax_licenses}


def _citation(inventory, passage_ids):
    passages = {p["passage_id"]: p for p in inventory["passages"]}
    sources = {s["source_id"]: s for s in inventory["sources"]}
    passage = passages[passage_ids[0]]
    source = sources[passage["source_id"]]
    return {"work": source["source_id"], "revision": source["sha256"],
            "source_sha256": source["sha256"], "start_byte": passage["start"],
            "end_byte": passage["end"], "quotation": passage["raw_text"]}


def _native_ledger(inventory):
    designations = [{"id": d["designation_id"], "expression": d["expression"],
                     "sense": d["sense_id"], "convention": d["convention"],
                     "origin": d["origin"], "citation": _citation(inventory, d["passage_ids"])}
                    for d in inventory["designations"]]
    by_id = {d["id"]: d for d in designations}
    relations = [{"designation": by_id[r["designation_id"]], "target_sense": r["target_sense_id"],
                  "kind": r["kind"], "citation": _citation(inventory, r["passage_ids"])}
                 for r in inventory["relations"]]
    return designations, relations


def _known(kind, *, positive=True, scope, **identity):
    return {"value": {"kind": kind, **identity}, "positive": positive, "scope": scope}


def _candidate_rows(frame, designations, relations, senses):
    candidates = enumerate_candidates(frame, designations, relations)
    return [{"sense_id": c["intended_sense"], "gloss": senses[c["intended_sense"]]["gloss"],
             "designation_id": c["designation"]["id"],
             "use_kind": "literal" if c["relation"] is None else "figurative",
             "candidate": c, "support_status": "UNKNOWN_PREMISE"} for c in candidates]


def _verify_native(request, root):
    # `root` redirects replay fixtures only; it cannot select another checker.
    executable = ROOT / "formal/.lake/build/bin/linguisticTruth"
    encoded = _wire(request) + "\n"
    if len(encoded.encode()) > 1048576:
        raise OverflowError("native request exceeds one MiB")
    result = subprocess.run([str(executable)], input=encoded,
                            text=True, capture_output=True, timeout=60, check=False)
    if result.returncode:
        raise ValueError("native linguisticTruth failed: " + result.stderr[-1024:])
    return json.loads(result.stdout)


def _validate_native(checked, rows, request):
    """Validate the entire response before exposing any supported result."""
    if type(checked) is not dict:
        raise ValueError("native response must be an object")
    if checked.get("status") == "RESOURCE_LIMIT":
        return "RESOURCE_EXHAUSTED", []
    expected = {"status", "law_id", "authority", "complete_proposal", "rows",
                "all_arabic_senses_enumerated", "world_truth_asserted"}
    if (set(checked) != expected or checked["law_id"] != "nabt.linguistic-truth.v1"
            or checked["authority"] != "CONDITIONAL_SUPPLIED_LEDGER"
            or checked["all_arabic_senses_enumerated"] is not False
            or checked["world_truth_asserted"] is not False):
        raise ValueError("native response law, authority or field set differs")
    if canonical_json(checked) != canonical_json(evaluate_request(request)):
        raise ValueError("native full response differs from the installed finite adapter")
    if checked["status"] == "RESOURCE_EXHAUSTED":
        if checked["rows"] != [] or checked["complete_proposal"] is not None:
            raise ValueError("native exhaustion cannot contain a partial certificate")
        return "RESOURCE_EXHAUSTED", []
    if (checked["status"] != "CHECKED" or checked["complete_proposal"] is not True
            or type(checked["rows"]) is not list or len(checked["rows"]) != len(rows)):
        raise ValueError("native checker did not confirm complete enumeration")
    verified = []
    verdicts = {"SUPPORTED_PREMISES", "UNKNOWN_PREMISE", "REFUTED_PREMISE", "CONFLICT", "INVALID_PROFILE"}
    for row, native in zip(rows, checked["rows"]):
        expected_kind = "figurative" if row["use_kind"] == "figurative" else "literal_" + row["candidate"]["designation"]["origin"]
        if (type(native) is not dict or set(native) != {"candidate", "kind", "verdict"}
                or _wire(native["candidate"]) != _wire(row["candidate"]) or native["kind"] != expected_kind
                or type(native["verdict"]) is not str or native["verdict"] not in verdicts):
            raise ValueError("native candidate identity, shape or guard verdict differs")
        verified.append({**row, "support_status": native["verdict"], "native_use_kind": native["kind"]})
    return "CHECKED", verified


def _acquire_profile(text, *, profile_id="linguistic", budget=None, source_id="user_text",
            subject="unspecified", time="unspecified", context="unspecified", root=ROOT):
    """Acquire only the documented raw-text sublanguage; no truth flags input.

    A convention profile is explicit context supplied by the caller, not an
    inferred authorial intention. Source authentication is always replayed.
    """
    output = _base()
    if budget is None:
        budget = AcquisitionBudget()
    if type(budget) is not AcquisitionBudget:
        return {**output, "status": "INVALID_INPUT", "reason": "EXPECTED_ACQUISITION_BUDGET"}
    if type(text) not in {str, bytes}:
        return {**output, "status": "INVALID_INPUT", "reason": "RAW_TEXT_REQUIRED"}
    try:
        raw = text.encode("utf-8", "strict") if type(text) is str else text
        text = raw.decode("utf-8", "strict")
    except UnicodeError:
        return {**output, "status": "INVALID_INPUT", "reason": "INVALID_UTF8"}
    if not raw or not text.strip():
        return {**output, "status": "INVALID_INPUT", "reason": "EMPTY_TEXT"}
    for name, value in {"profile_id": profile_id, "source_id": source_id, "subject": subject,
                        "time": time, "context": context}.items():
        if type(value) is not str or not value.strip() or len(value) > 4096:
            return {**output, "status": "INVALID_INPUT", "reason": "INVALID_" + name.upper()}
        try:
            value.encode("utf-8", "strict")
        except UnicodeError:
            return {**output, "status": "INVALID_INPUT", "reason": "INVALID_UTF8_CONTEXT"}
    output["source"] = {"source_id": source_id, "sha256": _sha(raw), "bytes": len(raw), "raw_text": text}
    output["context"] = {"profile_id": profile_id, "subject": subject, "time": time, "context": context,
                         "authority": "EXPLICIT_CONTEXT_ASSUMPTION"}
    if len(raw) > budget.max_input_bytes:
        return {**output, "status": "RESOURCE_EXHAUSTED", "reason": "MAX_INPUT_BYTES"}
    try:
        foundation.validate_source(text)
    except NabtError as exc:
        if exc.code == "FOUNDATION_SOURCE_INVALID":
            return {**output, "status": "INVALID_INPUT", "reason": exc.code,
                    "foundation_error": exc.as_dict()}
        if exc.code == "RESOURCE_LIMIT":
            return {**output, "status": "RESOURCE_EXHAUSTED", "reason": exc.code,
                    "foundation_error": exc.as_dict()}
        raise
    try:
        from .inventory import build_inventory
        inventory = build_inventory(root)
        if profile_id not in {p["profile_id"] for p in inventory["profiles"]}:
            return {**output, "status": "INVALID_INPUT", "reason": "UNKNOWN_PROFILE"}
        forms, senses = _form_index(inventory)
        designations, relations = _native_ledger(inventory)
        extension = inventory.get("acquisition_extension")
        if extension is not None:
            output["acquisition_extension_sha256"] = extension["review_sha256"]
        mark_review = None
        if any(_is_observed_mark(char) for char in text):
            from .marked_forms import _load_review, REVIEW_SHA256
            mark_review = _load_review(root)
            output["mark_review_sha256"] = REVIEW_SHA256
    except (OSError, ValueError, KeyError, ImportError) as exc:
        return {**output, "status": "SOURCE_UNAVAILABLE", "reason": str(exc)}
    output["inventory_sha256"] = inventory["review_sha256"]
    if len(raw) > 16384:
        return {**output, "status": "RESOURCE_EXHAUSTED", "reason": "MAX_NATIVE_TEXT_BYTES"}
    offsets = [0]
    for char in text:
        offsets.append(offsets[-1] + len(char.encode("utf-8")))
    reading_count = 0
    native_unavailable = False
    native_exhausted = False
    quotation_barrier = any(c in text for c in '«»()[]{}"“”\'‘’`')
    for start, end in _regions(text):
        if not text[start:end].strip():
            continue
        clause_span = _span(raw, offsets[start], offsets[end])
        tokens = _tokens(text, start, end, offsets)
        orthography_issues = []
        try:
            # Quotation, punctuation and controls cannot be silently erased to
            # turn a mentioned clause into an assertion of intended use.
            barred = quotation_barrier or any(c in text[start:end] for c in '،,\':') or any(
                ord(c) < 32 and c not in "\t" for c in text[start:end])
            parsed = None if barred else _parse_clause(tokens, forms, senses, extension=extension)
            if parsed is not None:
                parsed, orthography_issues = _orthography_gate(parsed, tokens, raw, inventory, senses, mark_review)
            if parsed is not None and parsed["orthography_licenses"]:
                output.setdefault("orthography_evidence", []).append({"clause_span": clause_span,
                    "licenses": parsed["orthography_licenses"],
                    "authority": "REPLAYED_REVIEW_AND_PYTHON_ACQUISITION",
                    "native_acquisition_proof": False})
            if parsed is not None and parsed["syntax_licenses"]:
                output.setdefault("syntax_evidence", []).append({"law_id": LAW_ID,
                    "rule": "SOURCE_REPLAYED_EXPLICIT_INTENTION_VERB", "clause_span": clause_span,
                    "licenses": parsed["syntax_licenses"],
                    "authority": "REPLAYED_REVIEW_AND_PYTHON_ACQUISITION",
                    "native_acquisition_proof": False})
            if parsed is not None and parsed["negative_correction"]:
                from .correction import replay_correction_source
                try:
                    citation = replay_correction_source(root)
                except (OSError, ValueError):
                    return {**output, "status": "SOURCE_UNAVAILABLE", "reason": "CORRECTION_SOURCE_UNAVAILABLE"}
                output.setdefault("syntax_evidence", []).append({"law_id": LAW_ID,
                    "rule": "NEGATIVE_SINGLE_BAL_CORRECTION", "clause_span": clause_span,
                    "citation": citation, "authority": "BOUNDED_READING_NOT_ALL_SCHOOLS"})
        except OverflowError as exc:
            return {**output, "status": "RESOURCE_EXHAUSTED", "reason": str(exc)}
        if parsed is None:
            output["unclassified_spans"].append({**clause_span,
                "reason": "UNSUPPORTED_OBSERVED_MARKS" if orthography_issues else "OUTSIDE_BOUNDED_CUE_LANGUAGE",
                **({"orthography_issues": [{"role": issue["role"],
                    **({"sense_id": issue["sense_id"]} if "sense_id" in issue else {}),
                    "span": _span(raw, issue["start"], issue["end"])} for issue in orthography_issues]}
                    if orthography_issues else {})})
        for token_index, token in enumerate(tokens):
            possible_forms = _occurrence_forms(token, forms,
                retrieval_forms=() if extension is None else extension["retrieval_forms"])
            keys = possible_forms.keys()
            if not keys:
                continue
            for expression in sorted(keys):
                if len(output["occurrences"]) >= budget.max_occurrences:
                    return {**output, "status": "RESOURCE_EXHAUSTED", "reason": "MAX_OCCURRENCES"}
                span = _span(raw, token["start"], token["end"])
                frame = {"occurrence": {"source": source_id, "revision": _sha(raw), "raw": text,
                         "start_byte": token["start"], "end_byte": token["end"],
                         "referent": subject, "time": time, "context": context},
                         "expression": expression, "convention": profile_id}
                rows = _candidate_rows(frame, designations, relations, senses[expression])
                reading_count += len(rows)
                if reading_count > budget.max_readings:
                    return {**output, "status": "RESOURCE_EXHAUSTED", "reason": "MAX_READINGS"}
                scope = frame["occurrence"]["context"]
                evidence = []
                active_cue = (parsed is not None and token_index == parsed["token_index"]
                              and expression == parsed["expression"])
                if active_cue:
                    # Distinct parse readings are retained; only evidence common
                    # to all parses enters the guard's signed support set.
                    sets = [{_wire(c): c for c in solution} for solution in parsed["readings"]]
                    common = set(sets[0]).intersection(*(set(s) for s in sets[1:]))
                    evidence = [sets[0][k] for k in sorted(common)]
                used = {(e["sense_id"], e["positive"]) for e in evidence}
                known = [_known("established", scope=scope, designation=d) for d in designations]
                known += [_known("related", scope=scope, relation=r) for r in relations]
                known += [_known("used", scope=scope, frame=frame, sense=sense, positive=positive)
                          for sense, positive in sorted(used)]
                for row in rows:
                    d = row["candidate"]["designation"]
                    if (d["sense"], False) in used:
                        known.append(_known("excludes", scope=scope, frame=frame, designation=d))
                    if (d["sense"], True) in used:
                        known.append(_known("excludes", scope=scope, frame=frame, designation=d, positive=False))
                unique_known = list({_wire(a): a for a in known}.values())
                request = {"frame": frame, "designations": designations, "relations": relations,
                           "known": unique_known, "proposed": [r["candidate"] for r in rows],
                           "budget": budget.max_native_scan}
                item = {"occurrence_id": source_id + ":" + str(token["start"]) + ":" + expression,
                        "expression": expression, "span": span, "clause_span": clause_span,
                        "surface_segmentations": possible_forms[expression],
                        "frame": frame, "candidates": rows,
                        "available_senses": [{"sense_id": s["sense_id"], "gloss": s["gloss"]}
                                             for s in senses[expression].values()],
                        "selected_sense_ids": sorted(s for s, positive in used if positive),
                        "excluded_sense_ids": sorted(s for s, positive in used if not positive),
                        "intended_sense_acquired": bool(used),
                        "cue_readings": [[{**e, "span": _span(raw, e["start"], e["end"])} for e in solution]
                                         for solution in parsed["readings"]] if active_cue else [],
                        "cue_span": clause_span if active_cue else None,
                        "signed_conflict": any((s, not p) in used for s, p in used),
                        "native_checked": False, "native_request": request,
                        "reason": "ACQUIRED_EXPLICIT_INTENDED_USE" if used else "NO_COMPLETE_INTENDED_SENSE_CUE"}
                try:
                    checked = _verify_native(request, root)
                    native_status, verified_rows = _validate_native(checked, rows, request)
                    item["native_result"] = checked
                    item["native_checked"] = native_status == "CHECKED"
                    native_exhausted |= native_status == "RESOURCE_EXHAUSTED"
                    if item["native_checked"]:
                        rows = verified_rows
                        item["candidates"] = verified_rows
                except OverflowError as exc:
                    native_exhausted = True
                    item["native_error"] = str(exc)
                except subprocess.TimeoutExpired as exc:
                    native_exhausted = True
                    item["native_error"] = str(exc)
                except (OSError, ValueError, KeyError) as exc:
                    native_unavailable = True
                    item["native_error"] = str(exc)
                supported = [r for r in rows if r["support_status"] == "SUPPORTED_PREMISES"]
                item["certified_sense_ids"] = sorted({r["sense_id"] for r in supported})
                item["supported_use_kinds"] = sorted({r["use_kind"] for r in supported})
                item["formal_guard_decided"] = item["native_checked"] and bool(supported)
                item["classification_status"] = (
                    "CONFLICT" if item["signed_conflict"] or any(r["support_status"] == "CONFLICT" for r in rows)
                    else "SUPPORTED" if supported else "UNKNOWN")
                for e in evidence:
                    output["acquired_premises"].append({"kind": "intended_use", "occurrence_id": item["occurrence_id"],
                        "sense_id": e["sense_id"], "positive": e["positive"],
                        "cue_span": clause_span, "sense_span": _span(raw, e["start"], e["end"]),
                        "basis": "WHOLE_CLAUSE_BOUNDED_ARABIC_PARSE"})
                output["occurrences"].append(item)
    output["acquisition_scan_complete"] = True
    output["all_installed_readings_retained"] = not native_exhausted
    output["intended_sense_acquired"] = bool(output["acquired_premises"])
    output["native_checked"] = bool(output["occurrences"]) and not native_unavailable and not native_exhausted
    if native_exhausted:
        output.update(status="RESOURCE_EXHAUSTED", reason="NATIVE_SCAN_BUDGET")
    elif native_unavailable:
        output.update(status="VERIFICATION_UNAVAILABLE", reason="NATIVE_CHECKER_UNAVAILABLE_OR_REJECTED")
    elif any(o["signed_conflict"] for o in output["occurrences"]):
        output.update(status="CONFLICT", reason="OPPOSED_EXPLICIT_INTENDED_USE")
    elif output["unclassified_spans"] or not output["intended_sense_acquired"]:
        output.update(status="UNKNOWN", reason=("UNSUPPORTED_OBSERVED_MARKS"
            if any(s["reason"] == "UNSUPPORTED_OBSERVED_MARKS" for s in output["unclassified_spans"])
            else "UNCLASSIFIED_TEXT_OR_NO_INTENDED_USE"))
    else:
        output.update(status="COMPLETE", reason="BOUNDED_ACQUISITION_SCAN_COMPLETE")
    return output


def acquire(text, *, profile_id=None, budget=None, source_id="user_text",
            subject="unspecified", time="unspecified", context="unspecified", root=ROOT):
    """Acquire raw cues without silently assigning a linguistic convention.

    When no profile is supplied, every installed convention is retained as a
    hypothesis. Native branch checks remain conditional and do not certify a
    literal or figurative interpretation for the unassigned occurrence.
    """
    foundation.require_foundation("tools.linguistic_truth.acquire")
    arguments = {"budget": budget, "source_id": source_id, "subject": subject,
                 "time": time, "context": context, "root": root}
    if profile_id is not None:
        return _acquire_profile(text, profile_id=profile_id, **arguments)
    # This first branch also performs uniform input validation before source
    # access. Its convention is never promoted to a supplied user context.
    first = _acquire_profile(text, profile_id="linguistic", **arguments)
    if first["status"] in {"INVALID_INPUT", "SOURCE_UNAVAILABLE", "RESOURCE_EXHAUSTED"}:
        if "context" in first:
            first["context"].update(profile_id=None, authority="UNESTABLISHED_CONVENTION")
        return first
    try:
        from .inventory import build_inventory
        inventory = build_inventory(root)
    except (OSError, ValueError, KeyError, ImportError) as exc:
        return {**_base(), "source": first["source"], "status": "SOURCE_UNAVAILABLE", "reason": str(exc)}
    profiles = [p["profile_id"] for p in inventory["profiles"]]
    branches = {p: first if p == "linguistic" else _acquire_profile(text, profile_id=p, **arguments)
                for p in profiles}
    output = {**first, "context": {**first["context"], "profile_id": None,
              "authority": "UNESTABLISHED_CONVENTION"}, "occurrences": [],
              "status": "UNKNOWN", "reason": "CONVENTION_PROFILE_UNESTABLISHED",
              "pending_profiles": profiles, "formal_guard_decided": False}
    grouped = {}
    for profile, branch in branches.items():
        for item in branch["occurrences"]:
            item["profile_authority"] = "UNESTABLISHED_PROFILE_HYPOTHESIS"
            grouped.setdefault(item["occurrence_id"], []).append((profile, item))
    for entries in grouped.values():
        first_item = entries[0][1]
        merged = {key: value for key, value in first_item.items()
                  if key not in {"frame", "native_request", "native_result", "candidates"}}
        merged.update(candidates=[], profile_readings=[], certified_sense_ids=[], supported_use_kinds=[],
                      formal_guard_decided=False, classification_status="UNKNOWN",
                      reason="CONVENTION_PROFILE_UNESTABLISHED")
        for profile, item in entries:
            merged["profile_readings"].append({"profile_id": profile,
                "authority": "UNESTABLISHED_PROFILE_HYPOTHESIS", "conditional_result": item})
            for row in item["candidates"]:
                merged["candidates"].append({**row, "convention": profile,
                    "conditional_support_status": row["support_status"],
                    "support_status": "UNKNOWN_PREMISE",
                    "reason": "CONVENTION_PROFILE_UNESTABLISHED"})
        merged["native_checked"] = all(item["native_checked"] for _, item in entries)
        if merged["signed_conflict"]:
            merged["classification_status"] = "CONFLICT"
        output["occurrences"].append(merged)
    output["native_checked"] = all(b["native_checked"] for b in branches.values())
    output["all_installed_readings_retained"] = all(b["all_installed_readings_retained"] for b in branches.values())
    effective_budget = budget or AcquisitionBudget()
    if any(b["status"] == "SOURCE_UNAVAILABLE" for b in branches.values()):
        output.update(status="SOURCE_UNAVAILABLE", reason="PROFILE_SOURCE_REPLAY_FAILED",
                      acquisition_scan_complete=False, all_installed_readings_retained=False)
    elif sum(len(o["candidates"]) for o in output["occurrences"]) > effective_budget.max_readings:
        output.update(status="RESOURCE_EXHAUSTED", reason="MAX_READINGS_ACROSS_PROFILES",
                      all_installed_readings_retained=False)
    elif any(b["status"] == "RESOURCE_EXHAUSTED" for b in branches.values()):
        output.update(status="RESOURCE_EXHAUSTED", reason="PROFILE_BRANCH_BUDGET")
    elif any(b["status"] == "VERIFICATION_UNAVAILABLE" for b in branches.values()):
        output.update(status="VERIFICATION_UNAVAILABLE", reason="NATIVE_CHECKER_UNAVAILABLE_OR_REJECTED")
    elif any(b["status"] == "CONFLICT" for b in branches.values()):
        output.update(status="CONFLICT", reason="OPPOSED_EXPLICIT_INTENDED_USE")
    return output
