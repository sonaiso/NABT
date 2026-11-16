"""Conditional conceptual readings from a fitted QAC/MASAQ grammar model."""
import json
import re
import unicodedata
from hashlib import sha256
from pathlib import Path

from nabt.corpus_evidence import lookup_clusters

SCHEMA = "ntl.corpus-concepts.v1"
RESULT = "ntl.corpus-concepts.result.v1"
DATA = Path(__file__).with_name("data") / "corpus_concepts_v1.json"
# A finite role-to-concept teaching contract. No source supplies world labels.
# Slots identify the target's structural contribution; the other endpoint is open.
FRAMES = {
    "subject": ("مسند إليه الفعل المبني للمعلوم", "relation:subject", "Jisr.TartibMamul"),
    "object": ("معمول الفعل في موضع المفعول به", "relation:object", "Jisr.TartibMamul"),
    "deputy": ("مسند إليه في بناء حُذف فاعله", None, "Aql.Isnad"),
    "prep": ("الاسم الذي تقيّده علاقة حرف الجر", None, "SLGE.Tarkib"),
    "idafa": ("طرف التقييد بالإضافة", None, "SLGE.Tarkib"),
    "attribute": ("وصف مقيِّد للمنعوت", None, "SLGE.Tarkib"),
    "topic": ("طرف الإسناد الاسمي المحكوم عليه", None, "Aql.Isnad"),
    "predicate": ("المسند في الإخبار الاسمي", None, "Aql.Isnad"),
    "time": ("قيد زمني للتعلّق", "relation:event_time", "Aql.Azmina"),
    "place": ("قيد مكاني للتعلّق", "relation:event_place", "Aql.Makan"),
    "active": ("صيغة إسناد فعل مبني للمعلوم", None, "Aql.Isnad"),
    "passive": ("صيغة إسناد فعل مبني للمجهول", None, "Aql.Isnad"),
    "imperative": ("صيغة طلب فعل", None, "SLGE.Tarkib"),
}
OTHER = "other"
NOMINAL = {"N", "PN", "ADJ", "T", "LOC"}
TOKEN_FEATURES = ("pos", "case", "voice", "aspect", "prep_prefix", "det", "suffix")
FEATURES = (*TOKEN_FEATURES, "previous", "previous_suffix")
VOWELS = re.compile("[ً-ْ]")
TOKEN = re.compile(r"[ء-غف-يً-ْٰٱ]+")
SCRIPT_MARKS = str.maketrans({"ٱ": "ا", "ـ": "", "ٰ": ""})
# Printed pause signs; miniature consonants such as U+06E5 are retained.
RECITATION = re.compile(r"[\u06d6-\u06dc]")


def spelling(text):
    """Orthographic join/lookup key. Retains ordinary vowels, shadda and hamza."""
    return unicodedata.normalize("NFC", RECITATION.sub("", text.translate(SCRIPT_MARKS)))


def key(text):
    return sha256(spelling(text).encode()).hexdigest()


def features(current, previous, *, initial):
    values = dict(zip(TOKEN_FEATURES, current, strict=True))
    if initial:
        values.update(previous="BOS", previous_suffix="NA")
    elif previous is not None:
        pos, _, voice, _, _, _, suffix = previous
        values.update(previous=voice if pos == "V" else pos, previous_suffix=suffix)
    return values


def leaf(tree, observed):
    trace = []
    while "feature" in tree:
        name = tree["feature"]
        value = observed.get(name)
        trace.append({"feature": name, "value": value})
        if value not in tree["children"]:
            return None, trace
        tree = tree["children"][value]
    return tree, trace


def pattern(word):
    clusters = lookup_clusters(spelling(word))
    if not clusters or len(clusters) < 3 or sum(bool(c[1]) for c in clusters) < 2:
        return None
    article = "".join(c[0] for c in clusters[:2]) == "ال"
    parts = []
    for i, (letter, marks, _, _) in enumerate(clusters):
        fixed = letter in "اويىةءؤئأإآ" or (article and i < 2)
        parts.append((letter if fixed else "C") + "".join(sorted(marks)))
    return "/".join(parts)


def analysis(model, word, *, use_patterns=True):
    if not word or not TOKEN.fullmatch(word) or not VOWELS.search(word):
        return None, None
    word_key = key(word)
    index = model["lexicon"].get(word_key)
    if index is not None:
        return model["analyses"][index], {"method": "seen_vocalized_form"}
    if use_patterns and word_key not in model["shape_blocks"]:
        shape = pattern(word)
        rule = model["patterns"].get(shape)
        if rule:
            return model["analyses"][rule["analysis"]], {"method": "transferred_pattern",
                                                         "pattern": shape, **rule}
    return None, None


def surface_observation(model, target, previous, initial, *, use_patterns=True):
    if not TOKEN.fullmatch(target) or (previous and not TOKEN.fullmatch(previous)):
        return None
    current, _ = analysis(model, target, use_patterns=use_patterns)
    if current is None or current[0] not in NOMINAL | {"V"}:
        return None
    prev, _ = analysis(model, previous, use_patterns=use_patterns)
    return features(current, prev, initial=initial)


SURFACE_FEATURES = ("ending", "last_carrier", "article", "length", "first_mark", "second_mark",
                    "penultimate_mark", "previous_length", "previous_ending", "previous_first_mark")


def written_features(word, previous, initial):
    def marks(pair):
        return "".join(sorted(pair[1])) or "NONE"

    if not TOKEN.fullmatch(word) or not VOWELS.search(word):
        return None
    cells = lookup_clusters(spelling(word))
    if not cells:
        return None
    last = cells[-1][0]
    features = {"ending": marks(cells[-1]), "last_carrier": last if last in "اويىة" else "C",
                "length": str(min(len(cells), 7)), "article": str(word.startswith("ال")),
                "first_mark": marks(cells[0]), "second_mark": marks(cells[1]) if len(cells) > 1 else "NONE",
                "penultimate_mark": marks(cells[-2]) if len(cells) > 1 else "NONE"}
    if initial:
        features.update(previous_length="BOS", previous_ending="BOS", previous_first_mark="BOS")
    elif previous and TOKEN.fullmatch(previous) and VOWELS.search(previous):
        prev = lookup_clusters(spelling(previous))
        if prev:
            features.update(previous_length=str(min(len(prev), 7)), previous_ending=marks(prev[-1]),
                            previous_first_mark=marks(prev[0]))
    return features


def compatible(candidate, reading):
    if reading is None:
        return True
    pos, _, voice, aspect, *_ = reading
    if candidate in {"active", "passive", "imperative"}:
        if pos != "V":
            return False
        if candidate == "imperative":
            return aspect == "IMPV"
        return aspect != "IMPV" and voice == ("PASS" if candidate == "passive" else "ACT")
    return pos in NOMINAL


def select(model, target, previous, initial):
    observed = surface_observation(model, target, previous, initial)
    node, trace = leaf(model["tree"], observed) if observed is not None else (None, [])
    if node and node["admitted"]:
        return node, trace, "morphosyntax"
    original = node, trace, "morphosyntax"
    raw = written_features(target, previous, initial)
    if raw is None:
        return original
    fallback, path = leaf(model["written_tree"], raw)
    if fallback and fallback["admitted"]:
        reading, _ = analysis(model, target)
        if compatible(fallback["candidate"], reading):
            return fallback, path, "vowel_and_position"
        # Preserve the blocked candidate for audit without treating its
        # calibrated leaf as an admitted occurrence.
        return dict(fallback, admitted=False, blocker="CONFLICTING_TARGET_ANALYSIS"), path, "vowel_and_position"
    return original if observed is not None else (fallback, path, "vowel_and_position")


def run(lesson):
    if type(lesson) is not dict or set(lesson) != {"schema", "text", "target_index"} or lesson["schema"] != SCHEMA:
        raise ValueError("Expected schema, text and a zero-based target_index")
    text, index = lesson["text"], lesson["target_index"]
    if type(text) is not str or not 0 < len(text) <= 2048 or type(index) is not int:
        raise ValueError("Expected bounded Arabic text and integer target index")
    # Whitespace-delimited single clause; a terminal full stop is permitted.
    # Do not skip internal material or punctuation to manufacture adjacency.
    clause = text.rstrip().removesuffix(".")
    spans = list(re.finditer(r"\S+", clause))
    if not 0 <= index < len(spans) <= 64:
        raise ValueError("Target outside bounded clause")
    if not all(TOKEN.fullmatch(m[0]) for m in spans):
        raise ValueError("Expected one whitespace-tokenized Arabic clause")
    model = json.loads(DATA.read_text(encoding="utf-8"))
    target = spans[index]
    def bind(match):
        return {"surface": match[0], "utf8_span": [len(text[:i].encode()) for i in match.span()]}

    prev = spans[index - 1] if index else None
    result = {"schema": RESULT, "status": "COURSE_SESSION", "execution_measured": True,
              "decision": "DEFER", "target": bind(target), "frame": None, "trace": [],
              "model_id": model["model_id"], "semantic_license": False,
              "world_truth_established": False, "other_endpoint_identified": False}
    node, trace, channel = select(model, target[0], prev[0] if prev else None, not index)
    result["channel"] = channel
    result["reading"] = analysis(model, target[0])[1]
    result["trace"] = trace
    if any(item["feature"].startswith("previous") for item in trace) and prev:
        result["context"] = {**bind(prev), "reading": analysis(model, prev[0])[1]}
    if node is None:
        reason = "MISSING_OR_UNSEEN_FEATURE" if trace else "NEED_VOCALIZED_TARGET_ANALYSIS"
        return dict(result, reason=reason)
    result["evidence"] = node
    if not node["admitted"]:
        return dict(result, reason=node.get("blocker", "INSUFFICIENT_AGREEMENT_OR_OTHER_ROLE"))
    label = node["candidate"]
    meaning, relation, unit = FRAMES[label]
    return dict(result, decision="PROPOSE", reason="TRAIN_AND_VALIDATION_AGREEMENT",
                frame={"id": label, "slot_ar": meaning, "relation_card": relation,
                       "atlas_unit": model["atlas"][unit]})
