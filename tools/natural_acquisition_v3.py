"""Finite natural lexical readings, with source replay and native guard checks.

The recognizer selects a reading only within the frozen literal-profile
grammar. It does not identify an actual speaker's intention. Sound acquisition
and the semantic reading are checked separately before their chain is joined.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess

from tools.linguistic_truth.inventory import build_inventory
from tools.linguistic_truth.sources import INVENTORY_PATH, INVENTORY_SHA256
from tools.linguistic_truth.runtime import (
    _candidate_rows, _known, _native_ledger, _validate_native, _verify_native,
)
from tools.aligned_acquisition_v2 import _receipt_wire

ROOT = Path(__file__).resolve().parents[1]
LAW_ID = "nabt.natural-acquisition.v3"
SOURCE_PATH = Path("evidence/sourced_acquisition_v3/natural_sources.json")
SOURCE_SHA256 = "f96689c943b06155f8e91a10fabf7b94ac9ae34200a8682ffa086aad604db7f6"
MAX_BYTES = 16384
MAX_OCCURRENCES = 64
MAX_RECEIPT_BYTES = 4 * 1024 * 1024
_TOKENS = re.compile(r"[^\s.!?؛;،؟«»()\[\]{}\"“”'‘’`,:]+")
_BARRIERS = frozenset('.!?؛;،؟«»()[]{}"“”\'‘’`,:')
_ADJECTIVES = (("جارية", "جَارِيَة", "ayn_spring"),
               ("باصرة", "بَاصِرَة", "ayn_eye"))


def _wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _load(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("DUPLICATE_FIELD")
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE")))


def _installed_path(relative):
    """Only canonical repository-relative paths, with no symlink components."""
    if (type(relative) is not str or not relative or Path(relative).is_absolute()
            or Path(relative).as_posix() != relative
            or any(part in {"", ".", ".."} for part in relative.split("/"))):
        raise ValueError("NONCANONICAL_SOURCE_PATH")
    current = ROOT.resolve(strict=True)
    for part in Path(relative).parts:
        current /= part
        if current.is_symlink():
            raise ValueError("SYMLINK_SOURCE_PATH")
    if current.resolve(strict=True) != current or not current.is_file():
        raise ValueError("SOURCE_PATH_NOT_REGULAR")
    return current


def _read_bounded(path, limit):
    with path.open("rb") as stream:
        return stream.read(limit + 1)


def source_inventory():
    """Reopen the code-pinned packet and every whole retained source file."""
    raw = _read_bounded(_installed_path(SOURCE_PATH.as_posix()), 1024 * 1024)
    if len(raw) > 1024 * 1024 or _sha(raw) != SOURCE_SHA256:
        raise ValueError("NATURAL_SOURCE_PACKET_CHANGED")
    packet = _load(raw)
    if (packet["schema"] != "nabt.natural-acquisition-source.v3" or
            packet["law_id"] != LAW_ID):
        raise ValueError("NATURAL_SOURCE_LAW_CHANGED")
    files = {}
    for source in packet["sources"]:
        data = _read_bounded(_installed_path(source["path"]), source["bytes"])
        if len(data) != source["bytes"] or _sha(data) != source["sha256"]:
            raise ValueError("RETAINED_SOURCE_CHANGED")
        files[source["source_id"]] = data
    for passage in packet["passages"]:
        start, end = passage["start_byte"], passage["end_byte"]
        data = files[passage["source_id"]]
        if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(data)
                or data[start:end] != passage["quote"].encode("utf-8")
                or _sha(data[start:end]) != passage["sha256"]):
            raise ValueError("RETAINED_PASSAGE_CHANGED")
    return packet


def _ledger(packet):
    """Extend the current fixed ledger without changing its historical bytes."""
    # Check the inherited pinned registry and its path components before the
    # legacy replay opens them; no same-bytes symlink grants installed identity.
    raw = _read_bounded(_installed_path(INVENTORY_PATH.as_posix()), 1024 * 1024)
    if _sha(raw) != INVENTORY_SHA256:
        raise ValueError("HISTORICAL_INVENTORY_CHANGED")
    for source in _load(raw)["sources"]:
        _installed_path(source["local_path"])
    inventory = build_inventory(ROOT)
    designations, relations = _native_ledger(inventory)
    forms, senses = {}, {}
    for row in inventory["designations"]:
        for form in row["forms"]:
            forms.setdefault(form, set()).add(row["expression"])
        senses.setdefault(row["expression"], {})[row["sense_id"]] = {"gloss": row["gloss"]}
    by_id = {row["designation_id"]: row for row in inventory["designations"]}
    for row in inventory["relations"]:
        expression = by_id[row["designation_id"]]["expression"]
        senses.setdefault(expression, {})[row["target_sense_id"]] = {"gloss": row["target_gloss"]}
    passages = {row["passage_id"]: row for row in packet["passages"]}
    sources = {row["source_id"]: row for row in packet["sources"]}
    for row in packet["added_senses"]:
        passage = passages[row["passage_ids"][0]]
        source = sources[passage["source_id"]]
        citation = {"work": source["source_id"], "revision": source["sha256"],
                    "source_sha256": source["sha256"], "start_byte": passage["start_byte"],
                    "end_byte": passage["end_byte"], "quotation": passage["quote"]}
        designations.append({"id": row["designation_id"], "expression": row["expression"],
                             "sense": row["sense_id"], "convention": row["convention"],
                             "origin": row["origin"], "citation": citation})
        senses.setdefault(row["expression"], {})[row["sense_id"]] = {"gloss": row["gloss"]}
    for expression, aliases in packet["lexical_form_aliases"].items():
        for form in aliases:
            forms.setdefault(form, set()).add(expression)
    return inventory, forms, senses, designations, relations


def _phrase(words):
    """Recognize frozen adjective pairs; return sense, marking style and case."""
    if len(words) != 2:
        return None
    noun, adjective = words
    for plain, marked, sense in _ADJECTIVES:
        if (noun, adjective) in (("عين", plain), ("العين", "ال" + plain)):
            return {"sense": sense, "style": "plain", "case": "unspecified"}
        if noun in ("عينًا", "عيناً") and adjective == plain:
            return {"sense": sense, "style": "plain", "case": "accusative"}
        for case, vowel, tanwin in (("nominative", "ُ", "ٌ"),
                                     ("accusative", "َ", "ً"),
                                     ("genitive", "ِ", "ٍ")):
            if noun == "الْعَيْن" + vowel and adjective == "الْ" + marked + vowel:
                return {"sense": sense, "style": "marked", "case": case}
            nouns = ("عَيْنًا", "عَيْناً") if case == "accusative" else ("عَيْن" + tanwin,)
            if noun in nouns and adjective == marked + tanwin:
                return {"sense": sense, "style": "marked", "case": case}
    return None


def _parse(text):
    body = text.strip(" \t")
    left = len(text) - len(text.lstrip(" \t"))
    if body.endswith("."):
        body = body[:-1].rstrip(" \t")
    if (not body or any(char in _BARRIERS for char in body)
            or any(char.isspace() and char not in " \t" for char in body)
            or any(ord(char) < 32 and char != "\t" for char in body)):
        return None
    matches = list(re.finditer(r"[^ \t]+", body))
    words = [match.group() for match in matches]
    noun_index, polarity, rule = 0, "none", "ADJECTIVE_PHRASE"
    phrase = _phrase(words)
    # Bare lightly marked accusative words are not a frozen phrase production.
    if phrase and phrase["style"] == "plain" and phrase["case"] != "unspecified":
        phrase = None
    if phrase is None:
        prefixes = ((["رأيت"], "plain", "positive"),
                    (["لم", "أر"], "plain", "negative"),
                    (["رَأَيْتُ"], "marked", "positive"),
                    (["لَمْ", "أَرَ"], "marked", "negative"))
        for prefix, style, sign in prefixes:
            if words[:len(prefix)] != prefix:
                continue
            candidate = _phrase(words[len(prefix):])
            if candidate is None or candidate["style"] != style:
                continue
            tail = words[len(prefix):]
            valid_case = candidate["case"] == "accusative" or (
                style == "plain" and tail[0] == "العين")
            if valid_case:
                phrase, noun_index, polarity = candidate, len(prefix), sign
                rule = "NEGATED_PERCEPTION" if sign == "negative" else "PERCEPTION"
                break
    if phrase is None and len(words) == 5:
        plain = (words[0] == "شرب" and words[1] in {"زيد", "عمرو", "المسافر"}
                 and words[2] == "من")
        marked = (words[0] == "شَرِبَ" and words[1] in {"زَيْدٌ", "عَمْرٌو", "الْمُسَافِرُ"}
                  and words[2] == "مِنْ")
        candidate = _phrase(words[3:])
        if (candidate and candidate["sense"] == "ayn_spring" and (
                (plain and candidate["style"] == "plain" and candidate["case"] == "unspecified") or
                (marked and candidate["style"] == "marked" and candidate["case"] == "genitive"))):
            phrase, noun_index, polarity, rule = candidate, 3, "positive", "DRINKING"
    if phrase is None:
        return None
    match = matches[noun_index]
    return {**phrase, "rule": rule, "assertion_polarity": polarity,
            "start_byte": len(text[:left + match.start()].encode("utf-8")),
            "end_byte": len(text[:left + match.end()].encode("utf-8")),
            "clause_start_byte": len(text[:left].encode("utf-8")),
            "clause_end_byte": len(text[:left + len(body)].encode("utf-8"))}


def _span(raw, start, end):
    return {"start_byte": start, "end_byte": end,
            "raw_text": raw[start:end].decode("utf-8"), "sha256": _sha(raw[start:end])}


def _base():
    return {"schema": "nabt.natural-acquisition-result.v3", "law_id": LAW_ID,
            "status": "UNKNOWN", "authority": "BOUNDED_LITERAL_PROFILE_ONLY",
            "profile_id": "linguistic", "profile_authority": "INSTALLED_CONDITIONAL_PROFILE",
            "occurrences": [], "candidate_sense_ids": [], "selected_sense_ids": [],
            "semantic_scope_complete": False, "native_checked": False,
            "chain_complete": False, "assertion_polarity": "none",
            "source_witnesses": [], "acquisition": None,
            "author_intention_established": False, "reference_resolved": False,
            "grammar_certified": False, "world_truth_established": False,
            "all_arabic_complete": False, "all_arabic_senses_enumerated": False,
            "general_acquisition_refinement_proved": False}


def _evaluate(text, *, source_id="user_text", revision="1", scope="unspecified",
              ending="wasl", onset="word_initial"):
    """Read original bytes under the frozen grammar and retain alternatives."""
    out = _base()
    try:
        if type(text) not in {str, bytes}:
            raise ValueError("RAW_TEXT_REQUIRED")
        raw = text.encode("utf-8", "strict") if type(text) is str else text
        text = raw.decode("utf-8", "strict")
        if not text or not text.strip():
            raise ValueError("EMPTY_TEXT")
        for value in (source_id, revision, scope):
            if type(value) is not str or not value.strip() or len(value.encode("utf-8")) > 4096:
                raise ValueError("INVALID_BINDING")
        if type(ending) is not str or ending not in {"wasl", "waqf"}:
            raise ValueError("INVALID_ENDING")
        if type(onset) is not str or onset not in {"word_initial", "connected"}:
            raise ValueError("INVALID_ONSET")
    except (ValueError, UnicodeError):
        return {**out, "status": "INVALID_INPUT", "reason": "INVALID_RAW_INPUT_OR_BINDING"}
    out["source"] = {"source_id": source_id, "revision": revision,
                     "raw_text": text, "sha256": _sha(raw), "bytes": len(raw)}
    out["binding"] = {"source_id": source_id, "revision": revision, "scope": scope,
                      "ending": ending, "onset": onset}
    if len(raw) > MAX_BYTES:
        return {**out, "status": "RESOURCE_EXHAUSTED", "reason": "MAX_INPUT_BYTES"}
    try:
        packet = source_inventory()
        inventory, forms, senses, designations, relations = _ledger(packet)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError):
        return {**out, "status": "SOURCE_UNAVAILABLE", "reason": "SOURCE_REPLAY_FAILED"}
    out["source_witnesses"] = {"packet_sha256": SOURCE_SHA256,
        "historical_inventory_sha256": inventory["review_sha256"],
        "sources": deepcopy(packet["sources"]), "passages": deepcopy(packet["passages"]),
        "authority": "RETAINED_BYTES_AND_AUTHORED_BOUNDED_INTERPRETATION"}
    parsed = _parse(text)
    if parsed:
        out["reading_rule"] = parsed["rule"]
        out["assertion_polarity"] = parsed["assertion_polarity"]
    failures = []
    for match in _TOKENS.finditer(text):
        start = len(text[:match.start()].encode("utf-8"))
        end = len(text[:match.end()].encode("utf-8"))
        for expression in sorted(forms.get(match.group(), ())):
            if len(out["occurrences"]) >= MAX_OCCURRENCES:
                return {**_base(), "status": "RESOURCE_EXHAUSTED", "reason": "MAX_OCCURRENCES",
                        "source": out["source"], "binding": out["binding"]}
            frame = {"occurrence": {"source": source_id, "revision": revision, "raw": text,
                     "start_byte": start, "end_byte": end, "referent": "unresolved",
                     "time": "unspecified", "context": scope},
                     "expression": expression, "convention": "linguistic"}
            rows = _candidate_rows(frame, designations, relations, senses[expression])
            active = (parsed is not None and expression == "العين" and
                      (start, end) == (parsed["start_byte"], parsed["end_byte"]))
            selected = [parsed["sense"]] if active else []
            known = [_known("established", scope=scope, designation=d) for d in designations]
            known += [_known("related", scope=scope, relation=r) for r in relations]
            for sense in selected:
                known.append(_known("used", scope=scope, frame=frame, sense=sense))
                for designation in designations:
                    if designation["expression"] == expression and designation["sense"] == sense:
                        known.append(_known("excludes", positive=False, scope=scope,
                                            frame=frame, designation=designation))
            request = {"frame": frame, "designations": designations, "relations": relations,
                       "known": known, "proposed": [row["candidate"] for row in rows], "budget": 4096}
            occurrence = {"expression": expression, "span": _span(raw, start, end),
                          "candidates": rows, "selected_sense_ids": [], "native_checked": False,
                          "native_request": request, "author_intention_established": False}
            if active:
                occurrence["cue_span"] = _span(raw, parsed["clause_start_byte"], parsed["clause_end_byte"])
            try:
                checked = _verify_native(request, ROOT)
                status, verified = _validate_native(checked, rows, request)
                occurrence["native_result"] = checked
                if status == "RESOURCE_EXHAUSTED":
                    failures.append("RESOURCE_EXHAUSTED")
                else:
                    occurrence.update(candidates=verified, native_checked=True)
                    supported = {row["sense_id"] for row in verified
                                 if row["support_status"] == "SUPPORTED_PREMISES"}
                    if not set(selected) <= supported:
                        raise ValueError("SELECTED_READING_NOT_NATIVE_SUPPORTED")
                    occurrence["selected_sense_ids"] = selected
            except (OverflowError, subprocess.TimeoutExpired):
                failures.append("RESOURCE_EXHAUSTED")
            except (OSError, ValueError, KeyError, TypeError):
                occurrence.update(native_checked=False, selected_sense_ids=[])
                failures.append("VERIFICATION_UNAVAILABLE")
            out["occurrences"].append(occurrence)
    out["candidate_sense_ids"] = sorted({row["sense_id"] for occurrence in out["occurrences"]
                                         for row in occurrence["candidates"]})
    out["selected_sense_ids"] = sorted({sense for occurrence in out["occurrences"]
                                        for sense in occurrence["selected_sense_ids"]})
    out["native_checked"] = bool(out["occurrences"]) and not failures
    out["semantic_scope_complete"] = bool(parsed and out["native_checked"] and
                                           out["selected_sense_ids"] == [parsed["sense"]])
    if failures:
        out.update(status="RESOURCE_EXHAUSTED" if "RESOURCE_EXHAUSTED" in failures
                   else "VERIFICATION_UNAVAILABLE", selected_sense_ids=[], semantic_scope_complete=False)
    else:
        out["status"] = "COMPLETE" if out["semantic_scope_complete"] else "UNKNOWN"
    # Fresh sourceful acquisition is an independent gate, never a rewrite of
    # the lexical clause into the old explicit-metalinguistic cue language.
    try:
        from tools.connected_acquisition_v3 import read_acquired
        acquisition = read_acquired(text, source_id=source_id, revision=revision,
                                    scope=scope, ending=ending, onset=onset)
        out["acquisition"] = acquisition
        bound = acquisition.get("acquisition", {})
        same_source = all(bound.get(key) == value for key, value in {
            "text": text, "source_id": source_id, "revision": revision, "scope": scope,
            "ending": ending, "onset": onset}.items())
        out["chain_complete"] = bool(out["semantic_scope_complete"] and same_source and
            acquisition.get("status") == "ACQUIRED" and acquisition.get("verified") is True and
            acquisition.get("shape_verified") is True)
    except (ImportError, OSError, ValueError, KeyError, TypeError, RecursionError):
        out["acquisition"] = {"status": "VERIFICATION_UNAVAILABLE", "verified": False,
                              "shape_verified": False}
    return out


def evaluate(text, *, source_id="user_text", revision="1", scope="unspecified",
             ending="wasl", onset="word_initial"):
    """Bound both input processing and the complete returned receipt."""
    result = _evaluate(text, source_id=source_id, revision=revision, scope=scope,
                       ending=ending, onset=onset)
    try:
        if len(_receipt_wire(result)) <= MAX_RECEIPT_BYTES:
            return result
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        return {**_base(), "status": "VERIFICATION_UNAVAILABLE", "reason": "INVALID_INTERNAL_RECEIPT"}
    return {**_base(), "status": "RESOURCE_EXHAUSTED", "reason": "MAX_RECEIPT_BYTES"}


def verify(report, *, text, source_id="user_text", revision="1", scope="unspecified",
           ending="wasl", onset="word_initial"):
    """Replay the whole receipt against independently supplied raw-source binding."""
    try:
        if type(report) is not dict:
            raise ValueError("REPORT_REQUIRED")
        encoded = _receipt_wire(report)
        if len(encoded) > MAX_RECEIPT_BYTES:
            return {"valid": False, "replay_matches": False, "status": "RESOURCE_EXHAUSTED"}
        expected = evaluate(text, source_id=source_id, revision=revision, scope=scope,
                            ending=ending, onset=onset)
        if encoded != _wire(expected).encode("utf-8"):
            raise ValueError("RECEIPT_DIFFERS")
        return {"valid": expected["chain_complete"], "replay_matches": True,
                "status": "VERIFIED_NATURAL_CHAIN" if expected["chain_complete"] else expected["status"]}
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        return {"valid": False, "replay_matches": False, "status": "INVALID_RECEIPT"}
