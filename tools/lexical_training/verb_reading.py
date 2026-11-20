"""Source-bound verb candidates. Never select a lexical sense from neural scores."""
from collections import defaultdict
from functools import lru_cache
import gzip
from itertools import product
import json
import unicodedata

from nabt import derivation, inflection, text_morphology
from nabt.corpus_evidence import lookup_clusters
from . import _alghanem_mabni as inflect, pattern_learning as net, verb_sources as source

RULES = "evidence/ntl_pattern_learning_v1/a116_verb_rules.json.gz"
HEADS = "evidence/ntl_pattern_learning_v1/verb_contrast_heads.json"
RULE_SHA = "1966774cbc15d84d9545316447e844f9fa94548e377c33db51700b66763016d8"
HEAD_SHA = "83e78a79e202b256d79ee432902b6ec253ac216f2833146c66a50dedc2073dfc"
VOWELS = "َُِْ"
OBJECTS = ("هَا","هُ","هُمَا","هُمْ","هُنَّ","كُمَا","كُمْ","كُمُ","كَ","كِ","نِي","نَا")
QUAD = {"فعلل":("past","quad"), "فعلل-مجهول":("passive","quad"),
        "يفعلل":("imperfect","quad"), "تفعلل":("past","quad.II"),
        "افعللّ":("past","quad.IV"), "تفعللّ":("imperfect","quad.IV")}
MOODS = {"ُ":"مرفوع", "َ":"منصوب", "ْ":"مجزوم"}
SUBJECTS = {unicodedata.normalize("NFC", v):p for p,v in inflect.CONSONANT_PERSONS}


@lru_cache(maxsize=1)
def tables():
    raw = json.loads(gzip.decompress(source.checked(RULES, RULE_SHA)))
    masks, index = defaultdict(set), defaultdict(list)
    for domain, key, recipe in raw["paradigms"]:
        positions = tuple(i for i,c in enumerate(recipe) if c in "1234")
        mask = "".join("*" if c in "1234" else c for c in recipe)
        masks[len(recipe)].add(positions)
        index[mask].append((domain,key,recipe))
    return raw["prefix_slots"], masks, index


@lru_cache(maxsize=1)
def readouts():
    raw = json.loads(source.checked(HEADS, HEAD_SHA))
    if raw["encoder"] != net.MODEL_SHA:
        raise ValueError("Contrast heads require their training encoder")
    return raw["heads"], raw["cell_readouts"]["heads"]


def as_cells(word):
    """Witnessed spelling projection. Length carriers inherit sukun; shadda expands in place."""
    cs = lookup_clusters(word)
    if not cs:
        return None
    cells = []
    for i,(base, marks, _, _) in enumerate(cs):
        base = base.translate(source.SEATS)
        vowels = marks & set(VOWELS)
        if marks - set(VOWELS + "ّ") or len(vowels) > 1:
            return None
        vowel = next(iter(vowels), None)
        if "ّ" in marks:
            cells.extend((base, "ْ"))
        if vowel is None:
            if not cells or (base,cells[-1]) not in (("ا","َ"),("ى","َ"),("و","ُ"),("ي","ِ")):
                return None
            vowel = "ْ"
        if base == "ى":
            base = "ا"
        if i == 0 and base == "ا" and vowel != "ْ":
            base = "ء"
        cells.extend((base,vowel))
    return "".join(cells)


def cell_readings(word):
    cells = as_cells(word)
    if not cells:
        return
    _, masks, index = tables()
    for positions in sorted(masks.get(len(cells), ())):
        probe = list(cells)
        for pos in positions:
            probe[pos] = "*"
        for domain, key, recipe in index.get("".join(probe), ()):
            quad = key in QUAD
            root = list("****" if quad else domain[:3])
            for pos in positions:
                slot = int(recipe[pos])-1
                if root[slot] not in ("*",cells[pos]):
                    break
                root[slot] = cells[pos]
            else:
                root = "".join(root)
                if any(c not in derivation.RADICALS for c in root):
                    continue
                if quad and domain != "****" and (root[0] == "ل") != (domain[0] == "ل"):
                    continue
                if not quad:
                    classes = "".join(c if c in "ويلء" else "*" for c in root)
                    if classes != domain[:3] or (root[1] == root[2]) != (domain[3] == "="):
                        continue
                refill = "".join(root[int(c)-1] if c in "1234" else c for c in recipe)
                if refill != cells:
                    continue
                fields = key.split(".")
                aspect, family = QUAD[key] if quad else fields[:2]
                mood = MOODS[fields[-1]] if aspect == "imperfect" and not quad else ("مرفوع" if aspect=="imperfect" else None)
                yield {"root":root,"aspect":"past" if aspect=="passive" else aspect,
                       "voice":"passive" if aspect=="passive" else "active","family":family,"mood":mood,
                       "rule":"A116.Rubai.abniya" if quad else "A116.Tasrif."+{
                           "past":"madi","imperfect":"mudari","imperative":"amr"}[aspect],
                       "key":key,"recipe":recipe,"rebuilt_cells":refill}


def canonical(word):
    return unicodedata.normalize("NFC", word).translate(source.SEATS)


def direct_readings(word):
    spelling = canonical(word)
    for _, candidate in net.alternatives(spelling):
        spec = pattern_map()[candidate["pattern"]]
        if spec.get("form") not in ("past","imperfect","imperative"):
            continue
        root = candidate["root"]
        if any(c in root for c in "وي") or root[1] == root[2]:
            continue
        expected = canonical(candidate["stem"])
        endings = [end for end in spec["endings"] if expected + end == spelling]
        if not endings:
            continue
        yield {"root":root,"aspect":spec["form"],"family":spec["family"],"voice":spec["voice"],
               "mood":MOODS[endings[0]] if spec["form"]=="imperfect" else None,
               "rule":spec["source_contract"],"pattern":spec["id"],"rebuilt":expected+endings[0]}


@lru_cache(maxsize=1)
def pattern_map():
    return {p["id"]:p for p in net.inventory()}


def prefixes(word):
    for seq in product(*tables()[0]):
        parts = tuple(s for s in seq if s)
        prefix = "".join(parts)
        if word.startswith(prefix) and len(prefix) < len(word):
            yield parts, word[len(prefix):]


def endings(word):
    for obj in ("", *OBJECTS):
        if obj and not word.endswith(obj):
            continue
        host = word[:-len(obj)] if obj else word
        for suffix, person in SUBJECTS.items():
            surface = inflect.BEFORE_OBJECT.get(suffix, suffix) if obj else suffix
            if host.endswith(surface):
                yield host[:-len(surface)], surface, person, obj
        for person, _, suffix in inflect.VOWEL_PERSONS:
            surface = inflect.BEFORE_OBJECT.get(suffix, suffix) if obj else suffix
            if surface and host.endswith(surface):
                yield host[:-len(surface)], surface, person, obj
            elif not surface and (obj or host.startswith(("أَ", "آ", "اِ", "ٱ")) or
                                  (host.endswith(("ى","ا")) and "ّ" in host)):
                yield host, "", person, obj


@lru_cache(maxsize=64)
def inflections(root, before_object):
    return inflect.verb_forms(root, before_object)


def conjugated(word):
    for bare, sub, person, obj in endings(word):
        if not 2 <= len(bare) <= 16 or (person in SUBJECTS.values() and not bare.endswith("ْ")):
            continue
        target = canonical(bare + sub)
        if not lookup_clusters(bare):
            continue
        candidates = inflect.candidate_roots(bare)
        attested = source.lexicon()[0]
        # Hypotheses with a deleted radical require an independent root inventory.
        for root in candidates:
            if root not in attested:
                continue
            for kind, form, who in inflections(root,bool(obj)).get(target, ()):
                if who != person or kind not in ("PAST","PASSIVE"):
                    continue
                # The witness is an exact generated host under the named seat projection.
                yield ({"root":root,"aspect":"past","voice":"active" if kind=="PAST" else "passive",
                        "family":form.split("-")[0],"form":form,"person":person,"mood":None,
                        "rule":"Alghanem.mabni_verbs.verb_forms","rebuilt":target,
                        "subject_realization":"implicit_or_external" if person in ("3MS","3FS") else "attached"}, bare, sub, obj)


# Surface pieces include the pronoun and, when present, the inflectional nun.
# The sign law and the possible moods come from the installed Lean inflection table.
FIVE_ENDINGS = (
    ("انِ", "َ", 9, "ا", "نِ"), ("ونَ", "ُ", 10, "و", "نَ"), ("ينَ", "ِ", 11, "ي", "نَ"),
    ("ا", "َ", 9, "ا", ""), ("وا", "ُ", 10, "و", ""), ("ي", "ِ", 11, "ي", ""),
)


def five_verbs(host, prefix):
    if host[:1] not in ("ي","ت"):
        return
    for suffix, vowel, cls, pronoun, nun in FIVE_ENDINGS:
        if not host.endswith(vowel+suffix) or (cls == 11 and host[0] != "ت"):
            continue
        body = host[:-len(suffix)]
        # Project only the Qur'anic small high sukun when consulting the cell generator.
        projection = body[:-1].replace("ۡ","ْ") + "ُ"
        parts = [("prefix",s) for s in prefix] + [
            ("imperfect_prefix",body[:2]), ("stem",body[2:]), ("subject",pronoun)]
        if nun:
            parts.append(("inflectional_nun",nun))
        elif suffix == "وا":
            parts.append(("orthographic_alif","ا"))
        for host_row in cell_readings(projection):
            if host_row["aspect"] != "imperfect" or host_row["root"][-1] in "وي":
                continue
            for sign in inflection.sign_candidates([cls]):
                if sign["sign_name"] != ("nun_retained" if nun else "nun_deleted"):
                    continue
                yield ({"root":host_row["root"], "aspect":"imperfect", "family":host_row["family"],
                        "voice":host_row["voice"], "mood":{"raf":"مرفوع","nasb":"منصوب","jazm":"مجزوم"}[sign["case_name"]],
                        "rule":"A116.Tasrif.mudari+Nabt.InflectionEvidence.realize",
                        "host_cells":host_row["rebuilt_cells"], "host_key":host_row["key"],
                        "host_recipe":host_row["recipe"], "ending_sign":sign,
                        "subject_realization":"attached", "rebuilt":body+suffix},parts)


def lexical_commands(host, prefix, initial):
    """A deleted initial hamza is invisible to slot recovery; try the attested roots."""
    if len(host) > 14:
        return
    try:
        records = source.studies()[2]
    except (OSError, ValueError):
        return
    contexts = ("وصل",) if prefix else ("ابتداء",) if initial else ("ابتداء","وصل")
    spelling = canonical(host)
    for root in dict.fromkeys(r for r, _ in records):
        for kind, family, person in inflections(root,False).get(spelling,()):
            if (kind, family, person) != ("IMPERATIVE","I","2MS"):
                continue
            dropped = not any(c in "ءأإؤئآ" for c in host)
            witnesses = [dict(w,context=c) for c in contexts for w in records.get((root,c),())
                         if w["dropped_hamza"] == dropped]
            if witnesses:
                yield {"root":root,"aspect":"imperative","family":"I","voice":"active","person":person,
                       "mood":None,"rule":"SamaiImperative+Alghanem.mabni_verbs.verb_forms",
                       "rebuilt":spelling,"attested_hamza_contexts":witnesses}


def parts_for(prefix, base, sub="", obj="", person=None):
    parts = [("prefix",p) for p in prefix] + [("stem",base)]
    if sub:
        if sub == "تُمُو":
            parts += [("subject","تُ"),("plural_mark","مُ"),("link","و")]
        elif person == "3FS":
            parts.append(("feminine_mark",sub))
        elif person == "3FD":
            parts.extend((("feminine_mark","تَ"),("subject","ا")))
        elif person == "3MP" and sub == "وا":
            parts.extend((("subject","و"),("orthographic_alif","ا")))
        else:
            parts.append(("subject",sub))
    if obj:
        parts.append(("object",obj))
    return parts


def segments(parts, term):
    start = term["utf8_span"][0]
    result = []
    for role, surface in parts:
        end = start + len(surface.encode())
        result.append({"role":role,"surface":surface,"utf8_span":[start,end]})
        start = end
    if start != term["utf8_span"][1] or "".join(p["surface"] for p in result) != term["surface"]:
        raise ValueError("Source reconstruction failed")
    return result


def contrast_score(row, encoder):
    pattern = row.get("pattern")
    if encoder is None:
        return None
    if not pattern and row.get("form") and row["root_class"] in ("سالم", "مهموز"):
        form = row["form"].replace("-", ".")
        pattern = "passive." + row["family"] if row["voice"] == "passive" else "past." + form
    shapes, cells = readouts()
    if row.get("rebuilt_cells"):
        head, stem = cells[row["key"]], row["rebuilt_cells"]
    elif pattern in shapes:
        head, stem = shapes[pattern], derivation._fill(pattern_map()[pattern], row["root"])
    else:
        return None
    hidden = net.hidden_state(encoder, net.features(stem))
    return head["bias"] + sum(w*x for w,x in zip(head["weights"],hidden,strict=True))


def read(term, encoder):
    word = term["surface"]
    if not 2 <= len(word) <= 40 or not any(c in VOWELS for c in word):
        return None
    if word in text_morphology._MARKERS:
        return {**term, "status":"EXACT_FUNCTION_MARKER", "alternatives":[], "masdars":{},
                "marker":text_morphology._MARKERS[word][1]}
    alternatives, lexical = [], {}
    for prefix, host in prefixes(word):
        readings = [(row,parts_for(prefix,host)) for row in [*cell_readings(host), *direct_readings(host),
                    *lexical_commands(host,prefix,term["utf8_span"][0] == 0)]]
        readings.extend(five_verbs(host,prefix))
        readings.extend((row,parts_for(prefix,base,sub,obj,row["person"])) for row,base,sub,obj in conjugated(host))
        for row, parts in readings:
            root, family = row["root"],row["family"]
            if len(alternatives) >= 128:
                return {**term,"status":"DEFER_CANDIDATE_LIMIT","alternatives":[],"masdars":{}}
            row["segments"] = segments(parts,term)
            row["root_class"] = source.root_type(root)
            row["root_display"] = source.lexicon()[0].get(root,root)
            row["contrast_score"] = contrast_score(row,encoder)
            key = root + "/" + family
            if key not in lexical:
                lexical[key] = source.masdar(root,family)
            row["masdar_ref"] = key
            alternatives.append(row)
    if alternatives:
        return {**term,"status":"CONDITIONAL_REFILL","alternatives":alternatives,"masdars":lexical,
                "projection":"HAMZA_CARRIER_AND_NFC_OR_EXPLICIT_A116_CELLS",
                "authority":"CONDITIONAL_MORPHOLOGY_ONLY"}
