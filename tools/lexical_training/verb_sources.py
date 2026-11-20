"""Root-relative lexical testimonies. Root membership does not identify a sense."""
from collections import defaultdict
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import re
import gzip
import json
import unicodedata

from nabt import derivation

ROOT = Path(__file__).resolve().parents[2]
DICTIONARY = "src/nabt/data/source_evidence/mukhtar_sihah.txt"
LANE = "evidence/verb_morphology_v1/lane/lane-masdar-v2.tsv"
STUDIES = "evidence/ntl_pattern_learning_v1/masdar_studies.json.gz"
STUDY_SHA = "ac48e259c1fdb9cd8bffa96006ae9ee660fee99996e8ce6fcc214cb95b790aa7"
SEATS = str.maketrans(dict.fromkeys("أإؤئ", "ء"))
# Reviewed readings. The byte-addressed quotation must still occur under its own headword.
QUOTES = (
    ("قرء","I","قراءة","قرأ الكتاب قراءة"), ("كتب","I","كتابة","كتابا أيضاو كتابة"),
    ("قول","I","قول","قال يقول قولا"), ("قوم","I","قيام","قام يقوم قياما"),
    ("قوم","IV","إقامة","أقام بالمكان إقامة"), ("بيع","I","بيع","باع الشيء يبيعه بيعا"),
    ("دعو","I","دعاء","دعوت الله له وعليه أدعوه دعاء"), ("رمي","I","رمي","يرميه رميا"),
    ("جلس","I","جلوس","جلس يجلس بالكسر جلوسا"), ("سمع","I","سمع","سمع الشيء بالكسر سمعا"),
    ("زور","I","زيارة","المزار الزيارة وموضع الزيارة"),
)


def checked(path, digest):
    raw = (ROOT / path).read_bytes()
    if sha256(raw).hexdigest() != digest:
        raise ValueError(f"Changed morphology source: {path}")
    return raw


@lru_cache(maxsize=1)
def lexicon():
    raw = checked(DICTIONARY, "e93f4054f3cddb826a7b3fafd01eac8c4b39b25ed2d92ece7ea093b755776691")
    heads, witnesses = {}, defaultdict(list)
    selected = defaultdict(list)
    for root, family, name, quote in QUOTES:
        selected[root].append((family, name, quote))
    offset, root = 0, ""
    for line in raw.splitlines(keepends=True):
        text = line.decode()
        if text.startswith("#"):
            header = re.match(r"^# ((?:[ء-غف-ي] ){3,4})", text)
            root = header[1].replace(" ", "").translate(SEATS) if header else ""
            if root:
                heads.setdefault(root, header[1].replace(" ", ""))
        for family, name, quote in selected.get(root, ()):
            start = line.find(quote.encode())
            if start >= 0:
                witnesses[root, family].append({"masdar":name, "source":DICTIONARY, "quote":quote,
                    "utf8_span":[offset + start, offset + start + len(quote.encode())]})
        offset += len(line)

    raw = checked(LANE, "6a82de0e56251c699aefa4e2851e5f7abe5fa4841c0edcc6249c2a98180c6989")
    offset = 0
    for line in raw.splitlines(keepends=True):
        if offset:
            stratum, file, entry, _, radicals, lemma, _, forms = line.decode().strip().split("\t")
            key = radicals.translate(SEATS)
            heads.setdefault(key, radicals)
            witnesses[key, "I"].append({"masadir":forms.split(), "lemma":lemma, "stratum":stratum,
                "source":LANE, "entry":entry, "file":file, "utf8_span":[offset,offset+len(line.rstrip())]})
        offset += len(line)
    return heads, witnesses


def root_type(root):
    weak = [i for i, c in enumerate(root) if c in "وي"]
    if len(root) != 3:
        return "رباعي معتل" if weak else "رباعي صحيح"
    if len(weak) > 1:
        return "لفيف مفروق" if weak == [0, 2] else "لفيف مقرون"
    if weak:
        return ("مثال","أجوف","ناقص")[weak[0]]
    if "ء" in root:
        return "مهموز"
    return "مضعف" if root[1] == root[2] else "سالم"


@lru_cache(maxsize=1)
def masdar_patterns():
    result = defaultdict(list)
    for p in derivation.installed_registry()["patterns"]:
        if p["family"] == "masdar":
            result[p["id"].split(".")[2]].append(p)
    return result


def spelling_key(word):
    return "".join(c for c in unicodedata.normalize("NFC",word).translate(SEATS)
                   if not unicodedata.combining(c))


@lru_cache(maxsize=1)
def studies():
    data = json.loads(gzip.decompress(checked(STUDIES, STUDY_SHA)))
    by_root, shaped, imperatives = defaultdict(list), defaultdict(list), defaultdict(list)
    for table in ("qamus", "lazim", "trans"):
        for index, (root, *record) in enumerate(data[table]):
            by_root[root.translate(SEATS)].append({"table":table, "index":index, "values":record})
    for index, (word, group, pattern) in enumerate(data["form_II"]):
        shaped[spelling_key(word), group, pattern].append({"masdar":word,"table":"form_II","index":index,
            "source":STUDIES, "pattern":pattern,"scope":"LEXICON_FORM_AND_CLASS_MATCH"})
    for index,(root, context, corpus, dropped) in enumerate(data["imperative"]):
        imperatives[root,context].append({"source":STUDIES,"table":"imperative","index":index,
                                          "corpus":corpus,"dropped_hamza":dropped})
    return by_root, shaped, imperatives


def study_nouns(root, family):
    records, shaped, _ = studies()
    if family != "II" or len(root) != 3:
        return [], records.get(root, []) if family == "I" else []
    first, middle, last = root
    group = root_type(root)
   # Archive classifies the final radical for this study. Lexical surfaces witness both outcomes.
    group = "ناقص" if last in "وي" else "مهموز" if last == "ء" else "سالم"
    candidates = (("تفعيل", "ت" + first + middle + "ي" + last),
                  ("تفعلة", "ت" + first + middle + ("ي" if last in "وي" else last) + "ة"))
    return [row for shape, word in candidates for row in shaped.get((word,group,shape),())], []


def masdar(root, family):
    found = list(lexicon()[1].get((root, family), ()))
    try:
        form_matches, source_patterns = study_nouns(root, family)
    except (OSError, ValueError):
        form_matches, source_patterns, study_status = [], [], "SOURCE_UNAVAILABLE"
    else:
        study_status = "AVAILABLE"
    found.extend(form_matches)
    patterns = masdar_patterns().get(family, ())
    regular = []
    if root_type(root) in ("سالم", "رباعي صحيح"):
        regular = [{"pattern":p["id"], "surface":derivation._fill(p,root),
                    "source_contract":p["source_contract"]} for p in patterns if p["arity"] == len(root)]
    bare_patterns = [p["id"] for p in masdar_patterns()["bare"]] if family == "I" else []
    return {"lexical_witnesses":found, "regular_candidates":regular,
            "bare_catalog_templates_requiring_attestation":bare_patterns,
            "source_pattern_records":source_patterns, "study_status":study_status,
            "status":"LEXICAL_WITNESSES" if found else "CONDITIONAL_PATTERN" if regular else "DEFER_LEXICAL_WITNESS",
            "scope":"ROOT_AND_FAMILY; SENSE_ALIGNMENT_REQUIRED"}
