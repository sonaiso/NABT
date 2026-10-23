#!/usr/bin/env python3
"""Author-owned preparation, never imported by NABT or its learner.

This script freezes inputs, linguistic obligations, source witnesses and split
diagnostics. It does not execute or inspect the new implementation. Its QAC
decoder is a literal independent transcription of the published Unicode table.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unicodedata


PIN = "9d8fa03a51f894416e0abaf3b6821c5ae6441dcd"
QAC_PATH = "corpora/qac/quranic-corpus-morphology-0.4.txt.gz"
RAW_SHA = "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46"
BASE_COMMIT = "880fad4b1c613813ca02e6288bd87a46de90d1e5"
BW = {
    "'": "ء", ">": "أ", "&": "ؤ", "<": "إ", "}": "ئ", "A": "ا",
    "b": "ب", "p": "ة", "t": "ت", "v": "ث", "j": "ج", "H": "ح",
    "x": "خ", "d": "د", "*": "ذ", "r": "ر", "z": "ز", "s": "س",
    "$": "ش", "S": "ص", "D": "ض", "T": "ط", "Z": "ظ", "E": "ع",
    "g": "غ", "_": "ـ", "f": "ف", "q": "ق", "k": "ك", "l": "ل",
    "m": "م", "n": "ن", "h": "ه", "w": "و", "Y": "ى", "y": "ي",
    "F": "ً", "N": "ٌ", "K": "ٍ", "a": "َ", "u": "ُ", "i": "ِ",
    "~": "ّ", "o": "ْ", "^": "ٓ", "#": "ٔ", "`": "ٰ", "{": "ٱ",
    ":": "ۜ", "@": "۟", '"': "۠", "[": "ۢ", ";": "ۣ", ",": "ۥ",
    ".": "ۦ", "!": "ۨ", "-": "۪", "+": "۫", "%": "۬", "]": "ۭ",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def arabic(value: str, *, root: bool = False) -> str:
    # The one source PN FORM with a literal space remains a space.
    return "".join("ء" if root and c == "A" else BW[c] if c != " " else " " for c in value)


def lookup(value: str) -> str:
    # The declared matching profile. No other spelling is folded.
    return value.replace("ٱ", "ا")


def audit_aliases(value: str) -> set[str]:
    # Conservative split-only equivalence; never supplied to production lookup.
    # Keep hamza seats and ordinary case vowels. Quranic stop/ornament signs and
    # alternative dagger-alif spellings are grouped so they cannot disclose a
    # held-out realization through a different orthographic rendering.
    value = unicodedata.normalize("NFC", lookup(value))
    ornaments = "ۣ۪ۭۜ۟۠ۢۨ۫۬ٓ"
    cleaned = "".join(c for c in value if c not in ornaments)
    return {value, cleaned, cleaned.replace("ٰ", ""), cleaned.replace("ٰ", "ا")}


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def parse_source(raw: bytes) -> tuple[list[dict], dict[tuple[int, int, int], list[dict]]]:
    rows: list[dict] = []
    words: dict[tuple[int, int, int], list[dict]] = collections.defaultdict(list)
    offset = 0
    for line_number, line_bytes in enumerate(raw.splitlines(keepends=True), 1):
        line = line_bytes.rstrip(b"\r\n").decode()
        if line.startswith("("):
            locator, form, tag, features = line.split("\t")
            location = tuple(map(int, re.findall(r"\d+", locator)))
            clauses = features.split("|")
            kv = dict(x.split(":", 1) for x in clauses if ":" in x)
            row = {
                "location": list(location), "line": line_number,
                "byte_start": offset, "byte_end": offset + len(line_bytes),
                "line_sha256": sha(line_bytes), "form_buckwalter": form,
                "form": arabic(form), "tag": tag, "features": clauses,
                "kv": kv,
            }
            rows.append(row)
            words[location[:3]].append(row)
        offset += len(line_bytes)
    return rows, words


def source_realizations(segments: list[dict]) -> list[str]:
    """All stem-to-suffix prefixes, to exclude a target under any clitic.

    This deliberately uses only the source split audit, outside the predictor.
    No segment position or target boundary is supplied to read_inflection.
    """
    result = []
    for i, row in enumerate(segments):
        if "STEM" not in row["features"]:
            continue
        text = row["form"]
        result.append(text)
        for following in segments[i + 1:]:
            if "SUFFIX" not in following["features"]:
                break
            text += following["form"]
            result.append(text)
    return result


def expect_reading(kind: str, cls: str, cases: list[str], root: str | None = None,
                   actual: str | None = None, **more: object) -> dict:
    result = {
        "kind_contains": [kind], "class_case_contains": [
            {"class": cls, "case": case} for case in cases
        ],
        "actual_case": actual,
        "actual_role": "preposition_object" if kind == "noun" and actual else
                       "governed_imperfect" if actual else None,
    }
    if root is not None:
        result["source_root_contains"] = [root]
    result.update(more)
    return result


def make_cases() -> list[dict]:
    cases: list[dict] = []

    def add(case_id: str, track: str, text: str, target: str, expected: dict,
            reason: str, *, model: str = "heldout_qac", action: str = "read",
            root_bw: str | None = None, lemma_bw: str | None = None,
            unseen: bool = False, basis: str = "authored_grammar_contrast") -> None:
        assert text.count(target) == 1 or case_id == "INF-A12"
        entry = {
            "id": case_id, "track": track, "action": action,
            "input": {"text": text, "source_id": case_id.lower().replace("-", "_"),
                      "scope": "independent_inflection_v1", "model_profile": model},
            "target_surface": target, "expected": expected,
            "reason": reason, "material_basis": basis,
            "target_realization_must_be_unseen": unseen,
        }
        if root_bw:
            entry["audit_root_buckwalter"] = root_bw
        if lemma_bw:
            entry["audit_lemma_buckwalter"] = lemma_bw
        cases.append(entry)

    # Twenty authored realizations. Their exact stem realization is excluded
    # throughout the source, not merely at one selected verse.
    nouns = [
        ("مِنْ بَحْرٍ", "بَحْرٍ", "bHr", "baHor"),
        ("فِي وَجْهٍ", "وَجْهٍ", "wjh", "wajoh"),
        ("إِلَى قَمَرٍ", "قَمَرٍ", "qmr", "qamar"),
        ("عَنْ طَعَامٍ", "طَعَامٍ", "TEm", "TaEaAm"),
        ("عَلَى جَبَلٍ", "جَبَلٍ", "jbl", "jabal"),
        ("مِنْ جُندٍ", "جُندٍ", "jnd", "jund"),
        ("إِلَى حَبْلٍ", "حَبْلٍ", "Hbl", "Habol"),
        ("فِي أَرْجُلٍ", "أَرْجُلٍ", "rjl", "rijol"),
    ]
    for number, (text, target, root, lemma) in enumerate(nouns, 1):
        expected = expect_reading("noun", "iSahih", ["jarr"], arabic(root, root=True), "jarr")
        expected["sign_contains"] = [{"case": "jarr", "sign": "kasra", "mode": "overt", "origin": "original"}]
        if number == 8:
            expected["singular_origin_must_not_cross_same_root_lemma"] = True
        add(f"INF-T{number:02}", "unseen_realization", text, target, expected,
            "Independently witnessed noun stem and retained construction evidence; the target ending is withheld. The preposition does not supply nounhood.",
            root_bw=root, lemma_bw=lemma, unseen=True)

    verbs = [
        ("لَمْ يَسْمَعْ", "يَسْمَعْ", "smE", "samiEa", "fSahih", "jazm", "sukun", "overt", "original"),
        ("لَنْ يَسْجُدَ", "يَسْجُدَ", "sjd", "sajada", "fSahih", "nasb", "fatha", "overt", "original"),
        ("لَمْ يَبْسُطْ", "يَبْسُطْ", "bsT", "basaTa", "fSahih", "jazm", "sukun", "overt", "original"),
        ("لَنْ يَحْمِلَ", "يَحْمِلَ", "Hml", "Hamala", "fSahih", "nasb", "fatha", "overt", "original"),
        ("لَمْ يَرْكَبُوا", "يَرْكَبُوا", "rkb", "rakiba", "fKhamsaW", "jazm", "nun_deleted", "deletion", "substitute"),
        ("لَنْ تَرْكَبُوا", "تَرْكَبُوا", "rkb", "rakiba", "fKhamsaW", "nasb", "nun_deleted", "deletion", "substitute"),
        ("لَمْ يَسْجُدَا", "يَسْجُدَا", "sjd", "sajada", "fKhamsaA", "jazm", "nun_deleted", "deletion", "substitute"),
        ("لَنْ تَعْجَبِي", "تَعْجَبِي", "Ejb", "Eajibu", "fKhamsaY", "nasb", "nun_deleted", "deletion", "substitute"),
        ("لَمْ يَدْعُ", "يَدْعُ", "dEw", "daEaA", "fMutalW", "jazm", "weak_deleted", "deletion", "substitute"),
        ("لَمْ تَرْمِ", "تَرْمِ", "rmy", "ramaY`", "fMutalY", "jazm", "weak_deleted", "deletion", "substitute"),
        ("لَمْ تَخْشَ", "تَخْشَ", "x$y", "xa$iYa", "fMutalAlif", "jazm", "weak_deleted", "deletion", "substitute"),
        ("لَنْ يَدْعُوَ", "يَدْعُوَ", "dEw", "daEaA", "fMutalW", "nasb", "fatha", "overt", "original"),
    ]
    for number, (text, target, root, lemma, cls, case, sign, mode, origin) in enumerate(verbs, 9):
        expected = expect_reading("verb", cls, [case], arabic(root, root=True), case)
        expected["sign_contains"] = [{"case": case, "sign": sign, "mode": mode, "origin": origin}]
        if sign.endswith("deleted"):
            expected["deletion_requires_retained_full_base_receipt"] = True
        add(f"INF-T{number:02}", "unseen_realization", text, target, expected,
            "An attested compatible imperfect base and person/aspect evidence license the proposed transformation; lam/lan only selects a compatible role/case.",
            root_bw=root, lemma_bw=lemma, unseen=True)

    contexts = [
        ("مِنْ مَلَكَيْنِ", "مَلَكَيْنِ", "noun", "iMuthanna", ["jarr"], "mlk", "jarr"),
        ("عَنْ فِئَتَيْنِ", "فِئَتَيْنِ", "noun", "iMuthanna", ["jarr"], "fAy", "jarr"),
        ("مِنْ مُصْلِحِينَ", "مُصْلِحِينَ", "noun", "iJamM", ["jarr"], "SlH", "jarr"),
        ("مِنْ مُفْلِحِينَ", "مُفْلِحِينَ", "noun", "iJamM", ["jarr"], "flH", "jarr"),
        ("مِنْ جَنَّاتٍ", "جَنَّاتٍ", "noun", "iJamF", ["jarr"], "jnn", "jarr"),
        ("مَلَكَيْنِ", "مَلَكَيْنِ", "noun", "iMuthanna", ["nasb", "jarr"], "mlk", None),
        ("مُصْلِحِينَ", "مُصْلِحِينَ", "noun", "iJamM", ["nasb", "jarr"], "SlH", None),
        ("جَنَّاتٍ", "جَنَّاتٍ", "noun", "iJamF", ["nasb", "jarr"], "jnn", None),
        ("يَرْكَبُونَ", "يَرْكَبُونَ", "verb", "fKhamsaW", ["raf"], "rkb", None),
        ("يَسْجُدَانِ", "يَسْجُدَانِ", "verb", "fKhamsaA", ["raf"], "sjd", None),
        ("تَعْجَبِينَ", "تَعْجَبِينَ", "verb", "fKhamsaY", ["raf"], "Ejb", None),
        ("الْقَمَرُ", "الْقَمَرُ", "noun", "iSahih", ["raf"], "qmr", None),
    ]
    for number, (text, target, kind, cls, cands, root, actual) in enumerate(contexts, 1):
        expected = expect_reading(kind, cls, cands, arabic(root, root=True), actual)
        if number == 4:
            expected["singular_origin_absent_without_actual_attestation"] = True
        if number in (9, 10, 11):
            expected["sign_contains"] = [{"case": "raf", "sign": "nun_retained", "mode": "overt", "origin": "substitute"}]
        if number == 8:
            expected["sign_contains"] = [
                {"case": "nasb", "sign": "kasra", "mode": "overt", "origin": "substitute"},
                {"case": "jarr", "sign": "kasra", "mode": "overt", "origin": "original"},
            ]
        if number == 12:
            expected["only_declared_wasl_lookup_projection"] = True
        add(f"INF-K{number:02}", "known_form_context_or_ambiguity", text, target, expected,
            "The lexical form can be present in training. Context transfer and isolated conditional alternatives are scored separately from unseen-realization transfer.",
            root_bw=root)

    boundaries = [
        ("يَحْمِلْنَهَا", {"kind_contains": ["verb"], "nun_evidence_contains": ["feminine_subject"], "forbidden_classes": ["fKhamsaA", "fKhamsaW", "fKhamsaY"], "actual_case": None, "actual_role": None},
         "A feminine subject nun and object suffix do not turn pre-nun sukun into an overt jussive sign.", "Hml"),
        ("قَلَمِ", {"kind_contains": ["noun"], "construction_not_licensed": True, "actual_case": None, "actual_role": None},
         "POS:N and repeated copies of the same final kasra, with no compatible tanwin or varying-ending attestation, do not establish inflection by themselves.", "qlm"),
        ("يُؤْمِنُونَ", {"kind_contains": ["verb"], "nun_evidence_contains": ["radical", "inflection_retained"], "distinct_nun_positions": True, "source_root_contains": ["ءمن"], "actual_case": None, "actual_role": None},
         "The stem's radical nun and the final inflectional nun have different positions and witnesses; the root A is hamza, not FORM alif.", "Amn"),
        ("أَكْفِلْنِيهَا", {"kind_contains": ["verb"], "forbidden_nun_evidence": ["inflection_retained", "inflection_deleted"], "actual_case": None, "actual_role": None},
         "The witnessed first-person suffix includes protective nun; its spelling cannot grant five-verb mood or a syntactic role to the object.", "kfl"),
        ("يَأْتِيَنَّكُم", {"kind_contains": ["verb"], "nun_evidence_contains": ["emphasis"], "emphasis_tag_alone_not_directness_proof": True, "actual_case": None, "actual_role": None},
         "An EMPH source tag supports emphasis evidence, not an unqualified transfer of directness or mood.", "Aty"),
        ("تَرَيِنَّ", {"kind_contains": ["verb"], "nun_evidence_contains": ["emphasis"], "emphasis_tag_alone_not_directness_proof": True, "actual_case": None, "actual_role": None},
         "A 2FS form with emphasis must retain the evidence about its attachment; the EMPH tag cannot be treated as the ordinary five-verb nun.", "rAy"),
        ("الزَّيْتُونِ", {"kind_contains": ["noun"], "forbidden_classes": ["iJamM"], "actual_case": None, "actual_role": None},
         "A lexical noun ending in the letters waw/nun is not a sound masculine plural. The non-root nun also cannot be called a radical merely from its presence.", "zyt"),
        ("هَدْىِ", {"kind_contains": ["noun"], "forbidden_classes": ["iManqus"], "forbidden_sign_modes": ["estimated"], "actual_case": None, "actual_role": None},
         "Final weak root plus final ya does not prove manqus: the preceding dal is explicitly sakin, and case marks are overt on the ya.", "hdy"),
    ]
    boundaries += [
        ("صَهٍ", {"no_licensed_declension_class": True, "actual_case": None, "actual_role": None},
         "The tanwin of a built imperative noun does not establish inflection; no QAC lexical attestation is supplied for this authored source-grammar control.", None),
        ("قَاضٍ", {"kind_contains": ["noun"], "construction_not_licensed": True, "forbidden_licensed_classes": ["iManqus"], "actual_case": None, "actual_role": None},
         "A single tanwined N attestation plus a final-weak root does not by itself witness all necessary underlying-ya and inflection conditions. Conditional candidates may remain.", "qDy"),
    ]
    for number, (text, expected, reason, root) in enumerate(boundaries, 1):
        add(f"INF-B{number:02}", "nun_and_nominal_boundary", text, text, expected, reason,
            root_bw=root, basis="source_grammar_counterexample" if root is None else "source_form_with_authored_isolation")

    unknowns = [
        ("مِنْ نَمَطٍ", "نَمَطٍ", "nmT"), ("لَمْ يَدْرِزْ", "يَدْرِزْ", "drz"),
        ("لَنْ يَفْلُسَ", "يَفْلُسَ", "fls"), ("نَمَطَانِ", "نَمَطَانِ", "nmT"),
        ("نَمَطُونَ", "نَمَطُونَ", "nmT"), ("دَرْزٌ", "دَرْزٌ", "drz"),
        ("لَمْ يَرْصُنُوا", "يَرْصُنُوا", "rSn"), ("لَنْ يَسْلُجَا", "يَسْلُجَا", "slj"),
    ]
    for number, (text, target, root) in enumerate(unknowns, 1):
        add(f"INF-U{number:02}", "unknown_family_abstention", text, target,
            {"no_source_attested_root": True, "no_licensed_declension_class": True, "actual_case": None, "actual_role": None},
            "This family is absent from the allowed corpus. Pattern candidates may be reported, but a governor or suffix-shaped spelling cannot manufacture lexical attestation or inflected class.", root_bw=root)

    adversaries = [
        ("مِنْ بَحْرٌ", "بَحْرٌ", "Incompatible overt nominal ending must block activation of the preposition frame."),
        ("لَمْ يَسْمَعُ", "يَسْمَعُ", "The retained damma is incompatible with overt jazm for this ordinary sound imperfect."),
        ("لَنْ يَسْجُدْ", "يَسْجُدْ", "Sukun is not the nasb fatha of the sound imperfect."),
        ("لَمْ يَرْكَبُونَ", "يَرْكَبُونَ", "Retained five-verb nun cannot be silently deleted to satisfy lam."),
        ("«مِنْ» بَحْرٍ", "بَحْرٍ", "Quoted marker mention does not govern an outside occurrence."),
        ("مِنْ «بَحْرٍ»", "بَحْرٍ", "An outside marker does not turn a quoted mention into its actual object."),
        ("لَمْ\nيَسْمَعْ", "يَسْمَعْ", "A line boundary prevents this explicitly closed two-word relation."),
        ("مِنْ\u0085بَحْرٍ", "بَحْرٍ", "NEL is a line separator, not licensed internal horizontal spacing."),
        ("مِنْ، بَحْرٍ", "بَحْرٍ", "Punctuation breaks the declared closed frame."),
        ("مِنْ بَحْرٍ قَمَرٌ", "بَحْرٍ", "An extra unaccounted occurrence is outside the closed two-word source scope."),
        ("من بحر", "بحر", "Missing vocalization and the man/min homograph do not uniquely select this governor frame."),
        ("بَحْرٍ مِنْ بَحْرٍ", "بَحْرٍ", "Repeated lexical text has distinct occurrences; a receipt cannot be copied to an ungoverned position."),
        ("بَحْرٍ", "بَحْرٍ", "The lexical initial ba with fatha is not a prepositional bi prefix."),
        ("بِبَحْرٍ", "بَحْرٍ", "The attached bi frame needs a complete compatible segmentation and independent noun evidence."),
        ("فِي اَرْجُلٍ", "اَرْجُلٍ", "Replacing hamza-above with bare alif is outside the declared wasl-only lookup profile."),
        ("لَمْ يَرْكَبُوا۟", "يَرْكَبُوا۟", "A recitation mark is preserved; supported exact decoding or explicit deferral is allowed, silent stripping is not."),
    ]
    for number, (text, target, reason) in enumerate(adversaries, 1):
        expected: dict = {"actual_case": None, "actual_role": None}
        if number == 12:
            expected["distinct_occurrences_not_interchangeable"] = True
        if number == 14:
            expected = expect_reading("noun", "iSahih", ["jarr"], "بحر", "jarr", attachment_requires_complete_segmentation=True)
        if number == 15:
            expected["no_hamza_seat_folding"] = True
        if number == 16:
            expected = {"raw_bytes_preserved": True, "no_silent_recitation_mark_stripping": True,
                        "allowed_outcomes": ["source_supported_exact_analysis", "defer_unsupported_mark"]}
        add(f"INF-A{number:02}", "attachment_and_representation_boundary", text, target, expected, reason)

    controls = [
        ("مِنْ بَحْرٍ", "بَحْرٍ", "no_model", "read", {"no_source_attested_root": True, "no_licensed_declension_class": True, "actual_case": None, "actual_role": None}, "Withdrawal removes model-dependent nominal authority."),
        ("لَمْ يَسْمَعْ", "يَسْمَعْ", "no_model", "read", {"no_source_attested_root": True, "no_licensed_declension_class": True, "actual_case": None, "actual_role": None}, "Lam does not supply the independent imperfect reading when its model is withdrawn."),
        ("لَمْ يَسْمَعْ", "يَسْمَعْ", "case_mood_erased", "semantic_invariance", {"reference_case": "INF-T09", "same_semantic_content": True}, "Erasing forbidden case/mood fields must not change the acquired reading. Source hashes and receipt identities may change."),
        ("مِنْ بَحْرٍ", "بَحْرٍ", "case_mood_poisoned", "semantic_invariance", {"reference_case": "INF-T01", "same_semantic_content": True}, "Poisoning forbidden case/mood labels must not steer the predictor."),
        ("مِنْ بَحْرٍ", "بَحْرٍ", "exclude_bHr_family", "read", {"no_source_attested_root": True, "no_licensed_declension_class": True, "actual_case": None, "actual_role": None}, "Excluding every source verse for the noun family prevents hidden lookup in the complete source bytes."),
        ("لَمْ يَسْمَعْ", "يَسْمَعْ", "exclude_smE_family", "read", {"no_source_attested_root": True, "no_licensed_declension_class": True, "actual_case": None, "actual_role": None}, "Excluding every source verse for the verb family removes its authority even though the archived corpus still contains it."),
        ("مِنْ بَحْرٍ", "بَحْرٍ", "heldout_qac", "source_identity_change", {"reference_case": "INF-T01", "same_semantic_content": True, "input_occurrence_ids_change": True}, "Changing source_id preserves compatible semantics but must replace every input occurrence/attachment identity."),
        ("مِنْ بَحْرٍ", "بَحْرٍ", "heldout_qac", "verify_model_withdrawal", {"verification_accepts_original": True, "verification_rejects_explicit_model_none": True}, "Verification cannot restore a withdrawn model from authority-bearing content in the old report."),
    ]
    for number, (text, target, model, action, expected, reason) in enumerate(controls, 1):
        add(f"INF-S{number:02}", "source_counterfactual", text, target, expected, reason, model=model, action=action)
    assert len(cases) == 74
    return cases


def sign_law() -> dict:
    # Independently transcribed from the cited grammar, not any new export.
    rows = []
    ordinary_nouns = {
        "iSahih": [("damma", "overt", "original"), ("fatha", "overt", "original"), ("kasra", "overt", "original")],
        "iSitta": [("waw", "overt", "substitute"), ("alif", "overt", "substitute"), ("ya", "overt", "substitute")],
        "iMuthanna": [("alif", "overt", "substitute"), ("ya", "overt", "substitute"), ("ya", "overt", "substitute")],
        "iJamM": [("waw", "overt", "substitute"), ("ya", "overt", "substitute"), ("ya", "overt", "substitute")],
        "iJamF": [("damma", "overt", "original"), ("kasra", "overt", "substitute"), ("kasra", "overt", "original")],
        "iMamnu": [("damma", "overt", "original"), ("fatha", "overt", "original"), ("fatha", "overt", "substitute")],
        "iMaqsur": [("damma", "estimated", "original"), ("fatha", "estimated", "original"), ("kasra", "estimated", "original")],
        "iManqus": [("damma", "estimated", "original"), ("fatha", "overt", "original"), ("kasra", "estimated", "original")],
    }
    verbs = {
        "fSahih": [("damma", "overt", "original"), ("fatha", "overt", "original"), ("sukun", "overt", "original")],
        "fKhamsaA": [("nun_retained", "overt", "substitute"), ("nun_deleted", "deletion", "substitute"), ("nun_deleted", "deletion", "substitute")],
        "fKhamsaW": [("nun_retained", "overt", "substitute"), ("nun_deleted", "deletion", "substitute"), ("nun_deleted", "deletion", "substitute")],
        "fKhamsaY": [("nun_retained", "overt", "substitute"), ("nun_deleted", "deletion", "substitute"), ("nun_deleted", "deletion", "substitute")],
        "fMutalAlif": [("damma", "estimated", "original"), ("fatha", "estimated", "original"), ("weak_deleted", "deletion", "substitute")],
        "fMutalW": [("damma", "estimated", "original"), ("fatha", "overt", "original"), ("weak_deleted", "deletion", "substitute")],
        "fMutalY": [("damma", "estimated", "original"), ("fatha", "overt", "original"), ("weak_deleted", "deletion", "substitute")],
    }
    for source, cases in ((ordinary_nouns, ("raf", "nasb", "jarr")), (verbs, ("raf", "nasb", "jazm"))):
        for cls, signs in source.items():
            for case, (sign, mode, origin) in zip(cases, signs):
                rows.append({"class": cls, "case": case, "sign": sign, "mode": mode, "origin": origin})
    excluded = [{"class": cls, "case": "jazm"} for cls in ordinary_nouns]
    excluded += [{"class": cls, "case": "jarr"} for cls in verbs]
    return {"schema": "nabt.inflection.independent-sign-law.v1", "conditional_on_licensed_class_and_context": True,
            "source": "independent_prior_gap_audit_v1.json:primary_grammar_passages",
            "admitted_rows": rows, "excluded_class_case": excluded,
            "source_scope": "The six-noun and diptote side conditions are premises. This matrix does not infer those conditions from a suffix."}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", required=True)
    parser.add_argument("--out-dir", default=str(Path(__file__).parent))
    args = parser.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw = gzip.decompress(subprocess.check_output(["git", "-C", args.source_repo, "show", f"{PIN}:{QAC_PATH}"]))
    assert sha(raw) == RAW_SHA
    rows, words = parse_source(raw)
    cases = make_cases()
    unseen = {alias for c in cases if c["target_realization_must_be_unseen"] for alias in audit_aliases(c["target_surface"])}
    excluded = set()
    for key, segments in words.items():
        if unseen.intersection(alias for s in source_realizations(segments) for alias in audit_aliases(s)):
            excluded.add(key[:2])
    kept_rows = [r for r in rows if tuple(r["location"][:2]) not in excluded]
    kept_words = {k: v for k, v in words.items() if k[:2] not in excluded}
    kept_forms = {alias for v in kept_words.values() for s in source_realizations(v) for alias in audit_aliases(s)}
    all_forms = {alias for v in words.values() for s in source_realizations(v) for alias in audit_aliases(s)}
    rootset = {r["kv"].get("ROOT") for r in kept_rows}
    source_checks = []
    for c in cases:
        r = c.get("audit_root_buckwalter")
        lem = c.get("audit_lemma_buckwalter")
        compatible = [x for x in kept_rows if x["kv"].get("ROOT") == r and (not lem or x["kv"].get("LEM") == lem)] if r else []
        if c["target_realization_must_be_unseen"]:
            assert not audit_aliases(c["target_surface"]).intersection(kept_forms), c["id"]
            assert compatible, (c["id"], "missing base family", r, lem)
        if c["track"] == "unknown_family_abstention":
            assert r not in rootset, (c["id"], "family present")
        paired = []
        if c["id"] in {f"INF-T{i:02}" for i in range(1, 9)}:
            target_stem = c["target_surface"][:-1]
            paired = [x for x in compatible if x["form"][:-1] == target_stem and x["form"][-1:] in "ًٌٍَُِ"]
            groups = collections.defaultdict(list)
            for x in paired:
                grammatical = tuple(f for f in x["features"] if re.fullmatch(r"(?:[123])?[MF]?[SDP]", f) or f in ("M", "F"))
                groups[(x["tag"], grammatical)].append(x)
            assert any(len({x["form"][-1] for x in group}) >= 2 for group in groups.values()), (c["id"], "no compatible paired terminal vowels")
        source_checks.append({
            "paired_terminal_witness_locations": [x["location"] for x in paired],
            "case_id": c["id"], "target_stem_realization_seen_before_exclusions": bool(audit_aliases(c["target_surface"]).intersection(all_forms)),
            "target_stem_realization_seen_after_exclusions": bool(audit_aliases(c["target_surface"]).intersection(kept_forms)),
            "compatible_retained_source_rows": len(compatible),
            "retained_witnesses": [{k: row[k] for k in ("location", "line", "byte_start", "byte_end", "line_sha256", "form_buckwalter", "form", "tag", "features")} for row in compatible[:5]],
        })
    additional = {}
    for name, root in (("exclude_bHr_family", "bHr"), ("exclude_smE_family", "smE")):
        group = excluded | {tuple(r["location"][:2]) for r in rows if r["kv"].get("ROOT") == root}
        additional[name] = {"excluded_verses": [list(v) for v in sorted(group)], "family_root_buckwalter": root}
    material = {
        "schema": "nabt.inflection.independent-cases.v1", "base_commit": BASE_COMMIT,
        "new_implementation_read_before_authoring": False,
        "description": "Authored source-informed pre-implementation holdout and controls; not an untouched external natural corpus.",
        "predictor_inputs": ["input.text", "input.source_id", "input.scope", "trained model selected by input.model_profile"],
        "gold_and_audit_fields_never_passed_to_predictor": True,
        "cases": cases,
    }
    split = {
        "schema": "nabt.inflection.independent-split.v1", "source_repository": "Saleh1967/Alghanem", "source_commit": PIN,
        "source_path": QAC_PATH, "decompressed_source_sha256": RAW_SHA,
        "projection_id": "qac.extended-buckwalter.unicode.v1", "lookup_id": "qac.lookup.v1",
        "audit_alias_profile": "nabt.independent.qac-orthographic-split-aliases.v1",
        "mapping_primary_source": "https://corpus.quran.com/java/buckwalter.jsp", "mapping": BW,
        "root_A_decodes_to_hamza_separately": True,
        "exclusion_rule": "Whole verses containing any held-out target stem-to-suffix realization, independent of external prefix or following suffix. Split-only conservative aliases group canonical Unicode mark order, wasl/bare alif, nonphonemic recitation ornaments, and stripped/expanded dagger-alif spellings. They never change predictor input or authorize runtime normalization; ordinary case vowels and hamza seats are retained.",
        "excluded_verses": [list(v) for v in sorted(excluded)],
        "source_rows_total": len(rows), "source_rows_retained": len(kept_rows),
        "source_words_total": len(words), "source_words_retained": len(kept_words),
        "additional_model_profiles": additional,
        "case_mood_erased": "Remove standalone NOM/ACC/GEN feature atoms and MOOD:* atoms only, retaining source FORM bytes and all allowed features.",
        "case_mood_poisoned": "Permute NOM->ACC->GEN->NOM and MOOD:SUBJ<->MOOD:JUS, leaving every allowed feature unchanged.",
        "unknown_family_roots": sorted({c["audit_root_buckwalter"] for c in cases if c["track"] == "unknown_family_abstention"}),
        "source_checks": source_checks,
        "not_claimed": ["Unseen roots are acquired", "QAC labels are infallible linguistic truth", "Known-form calibration is unseen-form transfer", "Verse grouping is independent of the source corpus", "A sign-law pass closes broader Arabic semantic episodes"],
    }
    for filename, value in (("independent_cases_v1.json", material), ("independent_split_v1.json", split), ("independent_sign_law_v1.json", sign_law())):
        p = out / filename
        if p.exists():
            raise SystemExit(f"Refusing to overwrite existing frozen material: {p}")
        p.write_bytes(json_bytes(value))
        print(filename, sha(p.read_bytes()))
    print("counts", json.dumps(dict(collections.Counter(c["track"] for c in cases)), ensure_ascii=False))
    print("excluded_verse_count", len(excluded))


if __name__ == "__main__":
    main()
