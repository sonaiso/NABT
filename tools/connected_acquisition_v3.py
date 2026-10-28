"""Source-bound finite citation and guarded connected realization, v3.

Original text and citation/connected cells remain separate. Native replay is
mandatory; source evidence is pinned, and never a caller-supplied authority.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile

from nabt.alphabet import ALPHABET_ID
from nabt.certificates import issue_certificate, verify_certificate
from nabt.errors import NabtError
from tools import aligned_acquisition as v1

LAW_ID = "nabt.sourced-acquisition.v3"
SOURCE_MANIFEST_SHA256 = "64d6d40943ed59a34d16a58de92e11f8672cbdc7ed47ec15f4e341d07594e423"
ROOT = Path(__file__).resolve().parents[1]
_SOURCES_PATH = ROOT / "evidence/sourced_acquisition_v3/source_evidence.json"
_NATIVE_PATH = ROOT / "formal/.lake/build/bin/connectedAcquisitionV3"
MAX_SOURCE_BYTES = 8192
MAX_CODEPOINTS = 4096
MAX_WORDS = 32
MAX_PHRASE_CELLS = 4096
MAX_REPORT_BYTES = 8 * 1024 * 1024
MAX_SOURCE_PACKET_BYTES = 1024 * 1024
_wire, _load = v1._wire, v1._load

# Literal installed specification rows, generated before any evaluation run.
_READINGS = [{'id': 'ARTICLE_HAQQ_U',
  'canonical': 'الْحَقُّ',
  'article_kind': 'moon',
  'input_surfaces': ['الْحَقُّ',
                     'اَلْحَقُّ',
                     'ٱلْحَقُّ',
                     'ٱَلْحَقُّ',
                     'الْحَقُّ',
                     'اَلْحَقُّ',
                     'ٱلْحَقُّ',
                     'ٱَلْحَقُّ'],
  'source_passages': ['sibawayhi_haqq_article', 'mukhtar_haqq', 'sibawayhi_article_initial_fatha', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_QAWM_U',
  'canonical': 'الْقَوْمُ',
  'article_kind': 'moon',
  'input_surfaces': ['الْقَوْمُ', 'اَلْقَوْمُ', 'ٱلْقَوْمُ', 'ٱَلْقَوْمُ'],
  'source_passages': ['sibawayhi_article_initial_fatha', 'mukhtar_qawm', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_GHULAM_U',
  'canonical': 'الْغُلَامُ',
  'article_kind': 'moon',
  'input_surfaces': ['الْغُلَامُ', 'اَلْغُلَامُ', 'ٱلْغُلَامُ', 'ٱَلْغُلَامُ'],
  'source_passages': ['qatr_wasl_fatha', 'mukhtar_ghulam', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_RAJUL_U',
  'canonical': 'الرَّجُلُ',
  'article_kind': 'sun',
  'input_surfaces': ['الرَّجُلُ',
                     'اَلرَّجُلُ',
                     'ٱلرَّجُلُ',
                     'ٱَلرَّجُلُ',
                     'الرَّجُلُ',
                     'اَلرَّجُلُ',
                     'ٱلرَّجُلُ',
                     'ٱَلرَّجُلُ'],
  'source_passages': ['sibawayhi_article_sun', 'sibawayhi_article_initial_fatha', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_WALAD_U',
  'canonical': 'الْوَلَدُ',
  'article_kind': 'moon',
  'input_surfaces': ['الْوَلَدُ', 'اَلْوَلَدُ', 'ٱلْوَلَدُ', 'ٱَلْوَلَدُ', 'الولدُ'],
  'source_passages': ['mukhtar_walad_and_awlad', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_AWLAD_U',
  'canonical': 'الْأَوْلَادُ',
  'article_kind': 'moon',
  'input_surfaces': ['الْأَوْلَادُ', 'اَلْأَوْلَادُ', 'ٱلْأَوْلَادُ', 'ٱَلْأَوْلَادُ', 'الأولادُ'],
  'source_passages': ['mukhtar_walad_and_awlad', 'sibawayhi_awlad_occurrence', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_AYN_U',
  'canonical': 'الْعَيْنُ',
  'article_kind': 'moon',
  'input_surfaces': ['الْعَيْنُ', 'اَلْعَيْنُ', 'ٱلْعَيْنُ', 'ٱَلْعَيْنُ'],
  'source_passages': ['natural_eye_senses', 'natural_eye_definition', 'natural_spring_definition', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_JARIYA_U',
  'canonical': 'الْجَارِيَةُ',
  'article_kind': 'moon',
  'input_surfaces': ['الْجَارِيَةُ', 'اَلْجَارِيَةُ', 'ٱلْجَارِيَةُ', 'ٱَلْجَارِيَةُ'],
  'source_passages': ['natural_eye_senses', 'natural_spring_definition', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_BASIRA_U',
  'canonical': 'الْبَاصِرَةُ',
  'article_kind': 'moon',
  'input_surfaces': ['الْبَاصِرَةُ', 'اَلْبَاصِرَةُ', 'ٱلْبَاصِرَةُ', 'ٱَلْبَاصِرَةُ'],
  'source_passages': ['natural_eye_senses', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_HAQQ_A',
  'canonical': 'الْحَقَّ',
  'article_kind': 'moon',
  'input_surfaces': ['الْحَقَّ',
                     'اَلْحَقَّ',
                     'ٱلْحَقَّ',
                     'ٱَلْحَقَّ',
                     'الْحَقَّ',
                     'اَلْحَقَّ',
                     'ٱلْحَقَّ',
                     'ٱَلْحَقَّ'],
  'source_passages': ['sibawayhi_haqq_article', 'mukhtar_haqq', 'sibawayhi_article_initial_fatha', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_QAWM_A',
  'canonical': 'الْقَوْمَ',
  'article_kind': 'moon',
  'input_surfaces': ['الْقَوْمَ', 'اَلْقَوْمَ', 'ٱلْقَوْمَ', 'ٱَلْقَوْمَ'],
  'source_passages': ['sibawayhi_article_initial_fatha', 'mukhtar_qawm', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_GHULAM_A',
  'canonical': 'الْغُلَامَ',
  'article_kind': 'moon',
  'input_surfaces': ['الْغُلَامَ', 'اَلْغُلَامَ', 'ٱلْغُلَامَ', 'ٱَلْغُلَامَ'],
  'source_passages': ['qatr_wasl_fatha', 'mukhtar_ghulam', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_RAJUL_A',
  'canonical': 'الرَّجُلَ',
  'article_kind': 'sun',
  'input_surfaces': ['الرَّجُلَ',
                     'اَلرَّجُلَ',
                     'ٱلرَّجُلَ',
                     'ٱَلرَّجُلَ',
                     'الرَّجُلَ',
                     'اَلرَّجُلَ',
                     'ٱلرَّجُلَ',
                     'ٱَلرَّجُلَ'],
  'source_passages': ['sibawayhi_article_sun', 'sibawayhi_article_initial_fatha', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_WALAD_A',
  'canonical': 'الْوَلَدَ',
  'article_kind': 'moon',
  'input_surfaces': ['الْوَلَدَ', 'اَلْوَلَدَ', 'ٱلْوَلَدَ', 'ٱَلْوَلَدَ'],
  'source_passages': ['mukhtar_walad_and_awlad', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_AWLAD_A',
  'canonical': 'الْأَوْلَادَ',
  'article_kind': 'moon',
  'input_surfaces': ['الْأَوْلَادَ', 'اَلْأَوْلَادَ', 'ٱلْأَوْلَادَ', 'ٱَلْأَوْلَادَ'],
  'source_passages': ['mukhtar_walad_and_awlad', 'sibawayhi_awlad_occurrence', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_AYN_A',
  'canonical': 'الْعَيْنَ',
  'article_kind': 'moon',
  'input_surfaces': ['الْعَيْنَ', 'اَلْعَيْنَ', 'ٱلْعَيْنَ', 'ٱَلْعَيْنَ'],
  'source_passages': ['natural_eye_senses', 'natural_eye_definition', 'natural_spring_definition', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_JARIYA_A',
  'canonical': 'الْجَارِيَةَ',
  'article_kind': 'moon',
  'input_surfaces': ['الْجَارِيَةَ', 'اَلْجَارِيَةَ', 'ٱلْجَارِيَةَ', 'ٱَلْجَارِيَةَ'],
  'source_passages': ['natural_eye_senses', 'natural_spring_definition', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_BASIRA_A',
  'canonical': 'الْبَاصِرَةَ',
  'article_kind': 'moon',
  'input_surfaces': ['الْبَاصِرَةَ', 'اَلْبَاصِرَةَ', 'ٱلْبَاصِرَةَ', 'ٱَلْبَاصِرَةَ'],
  'source_passages': ['natural_eye_senses', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_HAQQ_I',
  'canonical': 'الْحَقِّ',
  'article_kind': 'moon',
  'input_surfaces': ['الْحَقِّ',
                     'اَلْحَقِّ',
                     'ٱلْحَقِّ',
                     'ٱَلْحَقِّ',
                     'الْحَقِّ',
                     'اَلْحَقِّ',
                     'ٱلْحَقِّ',
                     'ٱَلْحَقِّ'],
  'source_passages': ['sibawayhi_haqq_article', 'mukhtar_haqq', 'sibawayhi_article_initial_fatha', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_QAWM_I',
  'canonical': 'الْقَوْمِ',
  'article_kind': 'moon',
  'input_surfaces': ['الْقَوْمِ', 'اَلْقَوْمِ', 'ٱلْقَوْمِ', 'ٱَلْقَوْمِ'],
  'source_passages': ['sibawayhi_article_initial_fatha', 'mukhtar_qawm', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_GHULAM_I',
  'canonical': 'الْغُلَامِ',
  'article_kind': 'moon',
  'input_surfaces': ['الْغُلَامِ', 'اَلْغُلَامِ', 'ٱلْغُلَامِ', 'ٱَلْغُلَامِ'],
  'source_passages': ['qatr_wasl_fatha', 'mukhtar_ghulam', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_RAJUL_I',
  'canonical': 'الرَّجُلِ',
  'article_kind': 'sun',
  'input_surfaces': ['الرَّجُلِ',
                     'اَلرَّجُلِ',
                     'ٱلرَّجُلِ',
                     'ٱَلرَّجُلِ',
                     'الرَّجُلِ',
                     'اَلرَّجُلِ',
                     'ٱلرَّجُلِ',
                     'ٱَلرَّجُلِ'],
  'source_passages': ['sibawayhi_article_sun', 'sibawayhi_article_initial_fatha', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_WALAD_I',
  'canonical': 'الْوَلَدِ',
  'article_kind': 'moon',
  'input_surfaces': ['الْوَلَدِ', 'اَلْوَلَدِ', 'ٱلْوَلَدِ', 'ٱَلْوَلَدِ'],
  'source_passages': ['mukhtar_walad_and_awlad', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_AWLAD_I',
  'canonical': 'الْأَوْلَادِ',
  'article_kind': 'moon',
  'input_surfaces': ['الْأَوْلَادِ', 'اَلْأَوْلَادِ', 'ٱلْأَوْلَادِ', 'ٱَلْأَوْلَادِ'],
  'source_passages': ['mukhtar_walad_and_awlad', 'sibawayhi_awlad_occurrence', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_AYN_I',
  'canonical': 'الْعَيْنِ',
  'article_kind': 'moon',
  'input_surfaces': ['الْعَيْنِ', 'اَلْعَيْنِ', 'ٱلْعَيْنِ', 'ٱَلْعَيْنِ'],
  'source_passages': ['natural_eye_senses', 'natural_eye_definition', 'natural_spring_definition', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_JARIYA_I',
  'canonical': 'الْجَارِيَةِ',
  'article_kind': 'moon',
  'input_surfaces': ['الْجَارِيَةِ', 'اَلْجَارِيَةِ', 'ٱلْجَارِيَةِ', 'ٱَلْجَارِيَةِ'],
  'source_passages': ['natural_eye_senses', 'natural_spring_definition', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_BASIRA_I',
  'canonical': 'الْبَاصِرَةِ',
  'article_kind': 'moon',
  'input_surfaces': ['الْبَاصِرَةِ', 'اَلْبَاصِرَةِ', 'ٱلْبَاصِرَةِ', 'ٱَلْبَاصِرَةِ'],
  'source_passages': ['natural_eye_senses', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'ARTICLE_WALAD_DUAL',
  'canonical': 'الْوَلَدَانِ',
  'article_kind': 'moon',
  'input_surfaces': ['الْوَلَدَانِ', 'اَلْوَلَدَانِ', 'ٱلْوَلَدَانِ', 'ٱَلْوَلَدَانِ', 'الولدانِ'],
  'source_passages': ['mukhtar_walad_and_awlad', 'qatr_dual_plural_endings', 'qatr_case_marks'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'QUMT_SPEAKER',
  'canonical': 'قُمْتُ',
  'article_kind': 'none',
  'input_surfaces': ['قُمْتُ', 'قمتُ'],
  'source_passages': ['qatr_qumt_pronoun', 'sabban_ta_person'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'QUMT_ADDRESSEE_M',
  'canonical': 'قُمْتَ',
  'article_kind': 'none',
  'input_surfaces': ['قُمْتَ', 'قمتَ'],
  'source_passages': ['qatr_qumt_pronoun', 'sabban_ta_person'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'QUMT_ADDRESSEE_F',
  'canonical': 'قُمْتِ',
  'article_kind': 'none',
  'input_surfaces': ['قُمْتِ', 'قمتِ'],
  'source_passages': ['qatr_qumt_pronoun', 'sabban_ta_person'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'DHAHIB_SINGULAR',
  'canonical': 'ذَاهِبٌ',
  'article_kind': 'none',
  'input_surfaces': ['ذَاهِبٌ', 'ذاهبٌ'],
  'source_passages': ['ibn_aqil_dhahib'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'DHAHIB_DUAL',
  'canonical': 'ذَاهِبَانِ',
  'article_kind': 'none',
  'input_surfaces': ['ذَاهِبَانِ', 'ذاهبانِ'],
  'source_passages': ['ibn_aqil_dhahib', 'qatr_dual_plural_endings'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'},
 {'id': 'DHAHIB_PLURAL',
  'canonical': 'ذَاهِبُونَ',
  'article_kind': 'none',
  'input_surfaces': ['ذَاهِبُونَ', 'ذاهبونَ'],
  'source_passages': ['ibn_aqil_dhahib', 'qatr_dual_plural_endings'],
  'authority': 'FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS'}]


def _failure(status, error):
    return {"law_id": LAW_ID, "alphabet_id": ALPHABET_ID, "status": status, "error": error}


def _reading(group):
    raw = "".join(piece["raw"] for piece in group)
    matches = [r for r in _READINGS if raw in r["input_surfaces"]]
    return matches[0] if len(matches) == 1 else None


def _groups(pieces):
    groups, word = [], []
    for piece in pieces:
        if piece["status"] == "BOUNDARY":
            if word:
                groups.append(word)
                word = []
            groups.append([piece])
        else:
            word.append(piece)
    if word:
        groups.append(word)
    return groups


def _is_word(group):
    return bool(group) and not any(p["status"] == "BOUNDARY" for p in group)


def _defer(group, reason):
    for piece in group:
        if piece["status"] not in ("BOUNDARY", "INVALID_INPUT"):
            piece.update(status="DEFER", rule=reason, cells=[])


def _article_shaped(group):
    return (len(group) >= 2 and group[0]["raw"][0] in "اٱ" and group[1]["raw"][0] == "ل")


def _word_json(group):
    r = _reading(group)
    return {"start": group[0]["start"], "end": group[-1]["end"],
            "byte_start": group[0]["byte_start"], "byte_end": group[-1]["byte_end"],
            "raw": "".join(p["raw"] for p in group), "status": v1._status(group),
            "cells": [c for p in group for c in p["cells"]],
            "reading_id": r["id"] if r else None, "source_passages": r["source_passages"] if r else []}


def _short_final(group):
    if not group or any(p["status"] != "LICENSED" for p in group):
        return False
    last = group[-1]
    vowels = [c for c in last["raw"][1:] if c in v1._VOWELS]
    return (len(vowels) == 1 and vowels[0] in "َُِ" and bool(last["cells"]) and
            last["cells"][-1] % 4 == "َُِ".index(vowels[0]))


def propose_acquisition(text, *, source_id="input", revision="1", scope="default",
                        ending="wasl", onset="word_initial"):
    base = v1.propose_acquisition(text, source_id=source_id, revision=revision, scope=scope, ending=ending)
    if "error" in base:
        return _failure(base["status"], base["error"])
    if type(onset) is not str or onset not in ("word_initial", "connected"):
        return _failure("INVALID_INPUT", "INVALID_INPUT")
    groups = _groups(base["pieces"])
    words = [g for g in groups if _is_word(g)]
    if len(words) > MAX_WORDS:
        return _failure("RESOURCE_EXHAUSTED", "RESOURCE_LIMIT")
    for group in groups:
        r = _reading(group) if _is_word(group) else None
        for piece in group:
            piece.update(reading_id=r["id"] if r else None,
                         source_passages=r["source_passages"] if r else [])
        if not _is_word(group) or any(p["status"] == "INVALID_INPUT" for p in group):
            continue
        if any(p["rule"] in ("SILENT_LETTER_LEXICON_REQUIRED", "ORTHOGRAPHIC_LEXICON_REQUIRED") for p in group):
            continue
        if r:
            canonical = v1._pieces(r["canonical"])
            v1._classify_word(canonical, ending == "waqf" and group is words[-1])
            if r["article_kind"] != "none":
                canonical[0].update(status="LICENSED", rule="ARTICLE_INITIAL", cells=[112])
                if r["article_kind"] == "sun":
                    canonical[1].update(status="LICENSED", rule="ARTICLE_SUN_LAM", cells=[])
            if len(group) != len(canonical):
                _defer(group, "TEMPLATE_ALIGNMENT_FAILED")
                continue
            for original, interpreted in zip(group, canonical):
                original.update(status=interpreted["status"], rule="FINITE:" + r["id"] + ":" + interpreted["rule"],
                                cells=interpreted["cells"])
        elif _article_shaped(group):
            _defer(group, "ARTICLE_READING_NOT_LICENSED")
    citation_status = v1._status(base["pieces"]) if words else "DEFER"
    reason = ("NO_WORD" if not words else "INVALID_PIECE" if citation_status == "INVALID_INPUT" else
              "DEFERRED_PIECE" if citation_status == "DEFER" else "COMPLETE_ACQUISITION")
    base.update(law_id=LAW_ID, onset=onset, status=citation_status, reason=reason,
                words=[_word_json(g) for g in words])
    continuous = bool(words) and base["text"] == " ".join(w["raw"] for w in base["words"])
    realized_groups = deepcopy(groups)
    previous = None
    for original, group in zip(groups, realized_groups):
        if not _is_word(original):
            continue
        if onset == "connected":
            if not continuous:
                _defer(group, "BOUNDARY_CONTINUITY_UNLICENSED")
            elif previous is not None:
                if not _short_final(previous):
                    _defer(group, "CONTACT_REPAIR_NOT_IMPLEMENTED")
                else:
                    r = _reading(original)
                    if r and r["article_kind"] != "none":
                        group[0].update(status="LICENSED", rule="ARTICLE_WASL_ELISION", cells=[])
        previous = original
    realized_pieces = [p for g in realized_groups for p in g]
    realized_words = [_word_json(g) for g in realized_groups if _is_word(g)]
    realization_status = v1._status(realized_pieces) if words else "DEFER"
    status = ("INVALID_INPUT" if citation_status == "INVALID_INPUT" else
              "DEFER" if citation_status != "ACQUIRED" else realization_status)
    phrase_cells = ([c for p in realized_pieces for c in p["cells"]]
                    if onset == "connected" and status == "ACQUIRED" else [])
    if len(phrase_cells) > MAX_PHRASE_CELLS:
        return _failure("RESOURCE_EXHAUSTED", "RESOURCE_LIMIT")
    offset = 0
    intervals = onset == "connected" and status == "ACQUIRED"
    for piece in realized_pieces:
        stop = offset + len(piece["cells"])
        piece.update(cell_start=offset if intervals else None, cell_end=stop if intervals else None)
        offset = stop
    joins = []
    for index, (left, right) in enumerate(zip(words, words[1:])):
        lo, hi = left[-1], right[0]
        r = _reading(right)
        guarded = continuous and _short_final(left)
        elided = onset == "connected" and guarded and bool(r and r["article_kind"] != "none")
        join_status = "CITATION_BOUNDARY" if onset == "word_initial" else "JOINED" if guarded else "DEFER"
        join_rule = ("CITATION_BOUNDARY" if onset == "word_initial" else
                     "BOUNDARY_CONTINUITY_UNLICENSED" if not continuous else
                     "CONTACT_REPAIR_NOT_IMPLEMENTED" if not _short_final(left) else
                     "ARTICLE_WASL_ELISION" if elided else "ONSET_UNCHANGED")
        joins.append({"left_word": index, "right_word": index + 1, "status": join_status,
                      "rule": join_rule, "elided": elided,
                      "span": {"start": lo["end"], "end": hi["start"],
                               "byte_start": lo["byte_end"], "byte_end": hi["byte_start"],
                               "raw": base["text"][lo["end"]:hi["start"]]}})
    realization = {"mode": onset, "status": "REALIZED" if realization_status == "ACQUIRED" else realization_status,
                   "pieces": realized_pieces, "words": realized_words, "joins": joins, "phrase_cells": phrase_cells}
    result = {"law_id": LAW_ID, "alphabet_id": ALPHABET_ID, "onset": onset, "status": status,
              "acquisition": base, "realization": realization}
    if len(_wire(result).encode()) > MAX_REPORT_BYTES:
        return _failure("RESOURCE_EXHAUSTED", "RESOURCE_LIMIT")
    return result


def _installed_path(relative):
    """Require a canonical repository path with no symlink components."""
    if (type(relative) is not str or not relative or Path(relative).is_absolute()
            or Path(relative).as_posix() != relative
            or any(part in {"", ".", ".."} for part in relative.split("/"))):
        raise ValueError("noncanonical source path")
    current = ROOT.resolve(strict=True)
    for part in Path(relative).parts:
        current /= part
        if current.is_symlink():
            raise ValueError("symlinked source path")
    if current.resolve(strict=True) != current or not current.is_file():
        raise ValueError("source path is not a regular installed file")
    return current


def _read_bounded(path, limit):
    if type(limit) is not int or limit < 0:
        raise ValueError("invalid source byte bound")
    with path.open("rb") as stream:
        return stream.read(limit + 1)


def source_inventory():
    packet_relative = _SOURCES_PATH.relative_to(ROOT).as_posix()
    if packet_relative != "evidence/sourced_acquisition_v3/source_evidence.json":
        raise ValueError("installed source packet path differs")
    raw = _read_bounded(_installed_path(packet_relative), MAX_SOURCE_PACKET_BYTES)
    if len(raw) > MAX_SOURCE_PACKET_BYTES:
        raise OverflowError("source packet budget")
    if sha256(raw).hexdigest() != SOURCE_MANIFEST_SHA256:
        raise ValueError("installed v3 source packet changed")
    packet = _load(raw)
    if packet["law_id"] != LAW_ID or packet["alphabet_id"] != ALPHABET_ID:
        raise ValueError("source law binding differs")
    sources = {}
    for source in packet["sources"]:
        path = _installed_path(source["repository_path"])
        data = _read_bounded(path, source["bytes"])
        if len(data) != source["bytes"] or sha256(data).hexdigest() != source["source_sha256"]:
            raise ValueError("retained source bytes changed")
        sources[source["source_id"]] = data
    for passage in packet["passages"]:
        data = sources[passage["source_id"]]
        if sha256(data).hexdigest() != passage["source_sha256"]:
            raise ValueError("passage source identity differs")
        span = data[passage["byte_start_0based"]:passage["byte_end_0based_exclusive"]]
        if span.decode("utf-8", "strict") != passage["raw_text"] or sha256(span).hexdigest() != passage["span_sha256"]:
            raise ValueError("retained source excerpt differs")
        if "line_start_1based" in passage:
            lines = data.splitlines(keepends=True)
            first, last = passage["line_start_1based"], passage["line_end_1based_inclusive"]
            if (sum(map(len, lines[:first-1])) != passage["byte_start_0based"] or
                    sum(map(len, lines[:last])) != passage["byte_end_0based_exclusive"]):
                raise ValueError("source line/byte indices differ")
    for dependency in packet["upstream_dependencies"]:
        path = _installed_path(dependency["path"])
        data = _read_bounded(path, MAX_SOURCE_PACKET_BYTES)
        if len(data) > MAX_SOURCE_PACKET_BYTES:
            raise OverflowError("source dependency byte budget")
        if sha256(data).hexdigest() != dependency["sha256"]:
            raise ValueError("source dependency changed")
    if _wire(packet["finite_registry"]["readings"]) != _wire(_READINGS):
        raise ValueError("installed reading table differs from frozen source specification")
    return {"schema": packet["schema"], "sha256": SOURCE_MANIFEST_SHA256,
            "sources": len(sources), "passages": len(packet["passages"]),
            "readings": len(_READINGS), "surfaces": sum(len(r["input_surfaces"]) for r in _READINGS),
            "authority": "SOURCE_IDENTITY_AND_BOUNDED_AUTHORED_INTERPRETATION"}


def _native(request):
    if not _NATIVE_PATH.is_file():
        raise FileNotFoundError("Build formal target connectedAcquisitionV3")
    with tempfile.TemporaryDirectory(prefix="nabt-acquisition-v3-") as directory:
        path, output = Path(directory) / "request.json", Path(directory) / "response.json"
        path.write_text(_wire(request), encoding="utf-8")
        with output.open("wb") as stream:
            result = subprocess.run([str(_NATIVE_PATH), str(path)], stdout=stream,
                                    stderr=subprocess.DEVNULL, timeout=30, check=False)
        if output.stat().st_size > MAX_REPORT_BYTES:
            raise OverflowError("native response byte budget")
        report = _load(output.read_bytes())
    if result.returncode == 2 and report == _failure("RESOURCE_EXHAUSTED", "RESOURCE_LIMIT"):
        raise OverflowError("native resource budget")
    if result.returncode != 0 or type(report) is not dict:
        raise ValueError("native transport rejected request")
    return report


def acquire(text, *, source_id="input", revision="1", scope="default", ending="wasl", onset="word_initial"):
    proposal = propose_acquisition(text, source_id=source_id, revision=revision, scope=scope, ending=ending, onset=onset)
    result = {**proposal, "schema": "nabt.checked-acquisition.v3", "verified": False,
              "authority": "UNVERIFIED_PROPOSAL"}
    if "error" in proposal:
        return result
    request = {key: proposal["acquisition"][key] for key in ("text", "source_id", "revision", "scope", "ending", "onset")}
    try:
        evidence = source_inventory()
    except OverflowError:
        return {**result, "status": "RESOURCE_EXHAUSTED", "error": "SOURCE_EVIDENCE_BYTE_LIMIT"}
    except (OSError, ValueError, KeyError, TypeError, UnicodeError):
        return {**result, "status": "SOURCE_EVIDENCE_UNAVAILABLE", "error": "INSTALLED_SOURCE_EVIDENCE_MISMATCH"}
    try:
        if _wire(_native(request)) != _wire(proposal):
            raise ValueError("native v3 replay mismatch")
    except (FileNotFoundError, PermissionError):
        return {**result, "status": "VERIFICATION_UNAVAILABLE", "error": "NATIVE_CHECKER_UNAVAILABLE"}
    except (subprocess.TimeoutExpired, OverflowError):
        return {**result, "status": "RESOURCE_EXHAUSTED", "error": "NATIVE_RESOURCE_LIMIT"}
    except (OSError, ValueError, RecursionError):
        return {**result, "status": "VERIFICATION_FAILED", "error": "NATIVE_REPLAY_MISMATCH"}
    return {**result, "verified": True, "authority": "NATIVE_REPLAYED_FINITE_SOURCEFUL_REPRESENTATION",
            "source_evidence": evidence}


def citation_acquire(text, *, source_id="input", revision="1", scope="default", ending="wasl"):
    return acquire(text, source_id=source_id, revision=revision, scope=scope, ending=ending, onset="word_initial")


def _shape(cells, mode):
    try:
        certificate = issue_certificate(cells, mode, source_text=None)
        if not verify_certificate(certificate).valid:
            raise NabtError("SHAPE_REPLAY_FAILED", "shape certificate did not replay")
        return {"status": "SHAPE_LICENSED", "mode": mode, "certificate": certificate}
    except NabtError as error:
        return {"status": "RESOURCE_EXHAUSTED" if error.code == "RESOURCE_LIMIT" else
                "SHAPE_REJECTED" if error.code == "UNLICENSED_SHAPE" else "SHAPE_CHECK_FAILED",
                "error": error.code, "mode": mode}


def read_acquired(text, *, source_id="input", revision="1", scope="default", ending="wasl", onset="word_initial"):
    result = acquire(text, source_id=source_id, revision=revision, scope=scope, ending=ending, onset=onset)
    result.update(schema="nabt.acquired-reading.v3", shape_verified=False, shape_handoffs=[], phrase_shape=None,
                  world_truth="NOT_ESTABLISHED", linguistic_rejection=False,
                  ordinary_arabic_completeness_established=False)
    if result["status"] != "ACQUIRED" or result["verified"] is not True:
        return result
    if onset == "connected":
        result["phrase_shape"] = _shape(result["realization"]["phrase_cells"], ending)
        checks = [result["phrase_shape"]]
    else:
        words = result["acquisition"]["words"]
        checks = []
        for index, word in enumerate(words):
            mode = ending if index == len(words)-1 else "wasl"
            checks.append({"word_index": index, "span": {k: word[k] for k in ("start", "end", "byte_start", "byte_end")},
                           **_shape(word["cells"], mode)})
        result["shape_handoffs"] = checks
    result["shape_verified"] = bool(checks) and all(c["status"] == "SHAPE_LICENSED" for c in checks)
    if not result["shape_verified"]:
        result["status"] = next(c["status"] for c in checks if c["status"] != "SHAPE_LICENSED")
    if len(_wire(result).encode()) > MAX_REPORT_BYTES:
        return {**_failure("RESOURCE_EXHAUSTED", "RESOURCE_LIMIT"), "schema": "nabt.acquired-reading.v3",
                "verified": False, "shape_verified": False, "authority": "UNVERIFIED_PROPOSAL"}
    return result


def _receipt_wire(report):
    if type(report) is not dict:
        raise ValueError("receipt must be a JSON object")
    pending = [(report, 0)]
    while pending:
        value, depth = pending.pop()
        if depth > 128:
            raise ValueError("receipt nesting limit")
        if type(value) is dict:
            if any(type(key) is not str for key in value):
                raise ValueError("nonstring JSON key")
            pending.extend((item, depth + 1) for item in value.values())
        elif type(value) is list:
            pending.extend((item, depth + 1) for item in value)
        elif type(value) not in (str, int, float, bool, type(None)):
            raise ValueError("non-JSON receipt value")
    raw = _wire(report).encode("utf-8", "strict")
    if len(raw) > MAX_REPORT_BYTES:
        raise ValueError("receipt byte budget")
    return raw


def verify_acquired_reading(report, text, *, source_id="input", revision="1", scope="default", ending="wasl", onset="word_initial"):
    try:
        encoded = _receipt_wire(report)
        expected = read_acquired(text, source_id=source_id, revision=revision, scope=scope, ending=ending, onset=onset)
        return expected["verified"] is True and encoded == _receipt_wire(expected)
    except (OSError, ValueError, TypeError, KeyError, RecursionError, UnicodeError):
        return False
