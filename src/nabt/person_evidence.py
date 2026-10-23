"""Source-relative, correlated person and attachment hypotheses.

The first letter of a word is never a lexical or person witness.  A complete
QAC-backed family licenses a bounded prefix substitution.  Full word/segment
evidence and independent host witnesses are retained for attached forms.
These results contain no assigned role, case, discourse referent or truth.
Every span is relative to the supplied surface; a source reader must bind it
to its own source, occurrence, reading and scope and replay the original QAC.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
import json
import re
from types import MappingProxyType

from .corpus_evidence import (MASKED_FEATURES, VOWELS, buckwalter_to_arabic,
                              lexical_index, lookup_clusters, lookup_key,
                              template_matches)
from .errors import NabtError, resource_limit

LAW_ID = "nabt.person-evidence.v1"
READER_VERSION = "nabt.source-person-bridge.v1"
EXPECTED_TABLE_SHA256 = "f77c9b65b3a7b638166b5807fff1218cb30079d2d301c815b1b512a665858d15"
MAX_SURFACE_BYTES = 8192
MAX_CANDIDATES = 512
MAX_VARIANTS = 300000
_GENDER = ("masculine", "feminine", None)
_NUMBER = ("singular", "dual", "plural")
_PERSON = {1: "speaker", 2: "addressee", 3: "third"}
_ORDER = "ًٌٍَُِّْٰ"


def _wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def installed_registry():
    try:
        raw = files("nabt").joinpath("data/person_evidence.json").read_bytes()
        if sha256(raw).hexdigest() != EXPECTED_TABLE_SHA256:
            raise ValueError("table digest differs")
        table = json.loads(raw)
        if table["law_id"] != LAW_ID:
            raise ValueError("law identity differs")
        for name, size in (("profiles", 14), ("prefix_rows", 20),
                           ("separate_pronouns", 14), ("attached_forms", 20)):
            if type(table[name]) is not list or len(table[name]) != size:
                raise ValueError("inventory differs")
        return table
    except (OSError, ValueError, UnicodeError, KeyError, TypeError) as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Installed person law cannot be replayed",
                        status="DEFER") from error


def person_catalog():
    return {"law_id": LAW_ID, "table_sha256": EXPECTED_TABLE_SHA256,
            "reader_version": READER_VERSION, "table": installed_registry(),
            "authority": "CONDITIONAL_PERSON_AND_SOURCE_MORPHOLOGY_NOT_REFERENCE"}


def _profile(row):
    return {name: row[name] for name in ("person", "gender", "number")}


def _profiles(code, table):
    if type(code) is not str or re.fullmatch(r"[123](?:[MF])?[SDP]", code) is None:
        return []
    person = int(code[0])
    gender = 0 if "M" in code else 1 if "F" in code else None
    number = "SDP".index(code[-1])
    return [row for row in table["profiles"] if row["person"] == person and
            row["number"] == number and (gender is None or row["gender"] == gender)]


def _compatible_profiles(code, family, pre, table):
    allowed = next((row["profiles"] for row in table["prefix_rows"]
                    if row["family"] == family and row["prefix"] == pre), [])
    return [row for row in _profiles(code, table) if row["qac"] in allowed]


def _render(clusters):
    return "".join(c[0] + "".join(mark for mark in _ORDER if mark in c[1]) for c in clusters)


def _match(surface, template, mutable=()):
    left, right = lookup_clusters(surface), lookup_clusters(template)
    if left is None or right is None or len(left) != len(right):
        return False
    for index, (observed, expected) in enumerate(zip(left, right)):
        if observed[0] != expected[0]:
            return False
        a, b = observed[1], expected[1]
        if index in mutable:
            a, b = a - VOWELS, b - VOWELS
        if a & VOWELS and b & VOWELS and a & VOWELS != b & VOWELS:
            return False
        if "ّ" in a and "ّ" not in b or "ٰ" in a and "ٰ" not in b:
            return False
    return True


def _family(entry):
    if entry.get("annotation_only") or entry["aspect"] != "IMPF":
        return None
    if entry["nun"] == "feminine_subject":
        return "feminine_plural"
    classes = entry["class_candidates"]
    if classes == [9]:
        return "dual"
    if classes == [10]:
        return "masculine_plural"
    if classes == [11]:
        return "feminine_singular"
    if classes in ([8], [12], [13], [14]) and entry["person"] in ("1S", "1P", "2MS", "3MS", "3FS"):
        return "plain"
    return None


def _voice(entry):
    if entry["kind"] != "verb":
        return None, None
    if entry.get("voice_basis"):
        return entry["voice"], entry["voice_basis"]
    return (entry["voice"], "QAC_EXPLICIT_VOICE") if entry["voice"] else (
        "active", "QAC_DEFAULT_ACTIVE_ABSENT_PASS")


def _base_parts(entry, family, count):
    if family in ("dual", "masculine_plural", "feminine_singular"):
        deleted = entry["variant"] == "nun_deleted_from_retained_base"
        tail = 2 if not deleted or family == "masculine_plural" else 1
        boundary = count - tail
        result = [{"kind": "verbal_stem", "start_cluster": 0, "end_cluster": boundary},
                  {"kind": "subject_pronoun", "start_cluster": boundary,
                   "end_cluster": boundary + 1}]
        if not deleted:
            result.append({"kind": "inflection_nun", "start_cluster": count - 1, "end_cluster": count})
        elif family == "masculine_plural":
            result.append({"kind": "separator_alif", "start_cluster": count - 1, "end_cluster": count})
        return result
    if family == "feminine_plural":
        return [{"kind": "verbal_stem", "start_cluster": 0, "end_cluster": count - 1},
                {"kind": "feminine_subject", "start_cluster": count - 1, "end_cluster": count}]
    return [{"kind": "verbal_stem" if entry["kind"] == "verb" else "nominal_stem",
             "start_cluster": 0, "end_cluster": count}]


def _candidate(entry, profile, family):
    clusters = lookup_clusters(entry["form"])
    voice, basis = _voice(entry)
    mutable = ([len(clusters) - 1] if entry["construction"] == "inflected" and family in (None, "plain") and
               entry["variant"] not in ("nun_deleted_from_retained_base", "weak_deleted_from_full_base") else [])
    result = {"kind": entry["kind"], "pos": entry["pos"], "form": entry["form"],
              "base_form": entry.get("base_form"), "person_profile": None if profile is None else _profile(profile),
              "profile_id": None if profile is None else profile["qac"], "family": family,
              "form_kind": {"IMPF": "imperfect", "PERF": "perfect", "IMPV": "imperative"}.get(
                  entry["aspect"], "separate_pronoun" if entry["pos"] == "PRON" else "nominal"),
              "aspect": entry["aspect"], "voice": voice, "voice_basis": basis,
              "lemma": entry["lemma"], "lemma_bw": entry["lemma_bw"], "root": entry["root"],
              "lexical_gender": entry.get("gender"), "lexical_number": entry.get("number"),
              "construction": entry["construction"], "class_candidates": list(entry["class_candidates"]),
              "possible_cases": list(entry["possible_cases"]), "variant": entry["variant"],
              "host_form": entry["form"], "host_variant": entry["variant"], "host_end_cluster": len(clusters),
              "segmentation_licensed": True,
              "parts": _base_parts(entry, family, len(clusters)),
              "nun_readings": deepcopy(entry.get("nun_positions", [])),
              "attached_pronouns": [], "valency_witnesses": [], "supports": list(entry["supports"]),
              "rule_ids": ["QAC_COMPLETE_LEXICAL_FORM"], "obligations": [],
              "mutable_clusters": mutable, "source_person_code": entry["person"],
              "authority": "SOURCE_RELATIVE_MORPHOLOGICAL_CANDIDATE"}
    if entry.get("construction_supports"):
        result["supports"] += list(entry["construction_supports"])
    if family:
        result["rule_ids"].append("QUALIFIED_FAMILY_PREFIX_CORRELATION")
    return result


def _base_variants(index, table, complete_forms):
    for encoded in (encoded for rows in index.values() for encoded in rows):
        entry = json.loads(encoded)
        if entry.get("annotation_only"):
            continue
        expected_base = lookup_key(entry.get("base_form") or entry["form"])
        entry["supports"] = [s for s in entry["supports"]
                             if expected_base in complete_forms.get(s["record_id"], ())]
        if not entry["supports"]:
            continue
        family = _family(entry)
        clusters = lookup_clusters(entry["form"])
        if family:
            if not entry["root"] or not entry["lemma_bw"] or not _compatible_profiles(
                    entry["person"], family, clusters[0][0], table) or not _full_family_geometry(entry, family):
                continue
            for row in table["prefix_rows"]:
                if row["family"] != family:
                    continue
                # Hamza collision/madda repair is outside this projection.
                if row["prefix"] == "أ" and len(clusters) > 1 and clusters[1][0] in ("أ", "ء", "إ", "آ"):
                    if clusters[0][0] != "أ":
                        continue
                projected = deepcopy(entry)
                shape = deepcopy(clusters)
                shape[0][0] = row["prefix"]
                projected["form"] = _render(shape)
                for profile in table["profiles"]:
                    if profile["qac"] not in row["profiles"]:
                        continue
                    candidate = _candidate(projected, profile, family)
                    candidate["base_form"] = entry.get("base_form") or entry["form"]
                    if row["prefix"] != clusters[0][0] or profile["qac"] != entry["person"]:
                        candidate["rule_ids"].append("SAME_FAMILY_PREFIX_SUBSTITUTION")
                    yield candidate
                    if family == "plain" and entry["variant"] == "attested":
                        hollow = _hollow_variant(candidate)
                        if hollow:
                            yield hollow
        else:
            ps = _profiles(entry["person"], table)
            if entry["kind"] == "noun" and entry["pos"] != "PRON":
                ps = [row for row in table["profiles"] if row["person"] == 3 and
                      _GENDER[row["gender"]] == entry["gender"] and _NUMBER[row["number"]] == entry["number"]]
            if entry["kind"] == "verb" and entry["aspect"] == "IMPF":
                # An unqualified imperfect stays outside person projection.
                continue
            for profile in ps or [None]:
                yield _candidate(entry, profile, family)


def _full_family_geometry(entry, family):
    full = lookup_clusters(entry.get("base_form") or entry["form"])
    if not full or full[0][1] not in ({"َ"}, {"ُ"}):
        return False
    if family == "plain":
        return len(full) >= 3
    if family == "feminine_plural":
        return (len(full) >= 4 and full[-1][0] == "ن" and full[-1][1] == {"َ"}
                and full[-2][1] == {"ْ"})
    carrier, vowel, nun_vowel = {"dual": ("ا", "َ", "ِ"),
                                "masculine_plural": ("و", "ُ", "َ"),
                                "feminine_singular": ("ي", "ِ", "َ")}[family]
    return (len(full) >= 5 and full[-2][0] == carrier and full[-2][1] in (set(), {"ْ"}) and
            full[-3][1] == {vowel} and full[-1][0] == "ن" and full[-1][1] == {nun_vowel})


def _hollow_variant(candidate):
    root = candidate["root"]
    clusters = lookup_clusters(candidate["form"])
    if (not root or len(root) != 3 or root[1] not in "وي" or root[0] in "ءوي" or root[2] in "ءوي"
            or len(clusters) != 4 or clusters[1][0] != root[0] or clusters[3][0] != root[2]
            or clusters[2][0] not in "اوي" or any("ّ" in c[1] or "ٰ" in c[1] for c in clusters)):
        return None
    vowel = {"ا": "َ", "و": "ُ", "ي": "ِ"}[clusters[2][0]]
    if clusters[1][1] != {vowel} or clusters[2][1] not in (set(), {"ْ"}):
        return None
    short = deepcopy(clusters[:2] + clusters[3:])
    short[-1][1] = {"ْ"}
    result = deepcopy(candidate)
    result.update(form=_render(short), base_form=candidate["form"],
                  variant="hollow_short_from_full_base", possible_cases=[3], mutable_clusters=[])
    result.update(host_form=result["form"], host_variant=result["variant"], host_end_cluster=3)
    result["parts"] = [{"kind": "verbal_stem", "start_cluster": 0, "end_cluster": 3}]
    result["rule_ids"].append("QUALIFIED_TRILITERAL_HOLLOW_SHORT_BEFORE_FINAL_SUKUN")
    result["obligations"].append("SHORT_HOLLOW_FORM_REQUIRES_EXTERNAL_JUSSIVE_CONTEXT")
    result["nun_readings"] = [{**n, "cluster_index": 2 if n["kind"] == "radical" else n["cluster_index"]}
                              for n in result["nun_readings"]]
    result["weak_origin"] = {"root": root, "position": 1, "radical": root[1],
                             "authority": "SUPPLIED_SOURCE_ROOT_AND_COMPLETE_BASE"}
    return result


def _add(index, candidate):
    key = lookup_key(candidate["form"])
    semantic = {name: value for name, value in candidate.items()
                if name not in ("supports", "base_form", "source_person_code")}
    semantic["attached_pronouns"] = [{name: value for name, value in p.items()
                                     if name not in ("support_ids", "source_person_code")}
                                    for p in candidate["attached_pronouns"]]
    semantic["valency_witnesses"] = sorted({_wire({name: value for name, value in witness.items()
                                                  if name not in ("support_ids", "source_form")}).decode("utf-8")
                                            for witness in candidate["valency_witnesses"]})
    signature = _wire(semantic)
    if signature not in index[key]:
        index[key][signature] = candidate
    else:
        existing = index[key][signature]
        seen = {s["record_id"] for s in existing["supports"]}
        for support in candidate["supports"]:
            if support["record_id"] not in seen and len(existing["supports"]) < 8:
                existing["supports"].append(support)
                seen.add(support["record_id"])


@lru_cache(maxsize=2)
def _compile(raw, excluded_verses, source_id, table_sha):
    from .corpus_evidence import QacLexicon
    model = QacLexicon(raw, excluded_verses, source_id)
    lexical, _ = lexical_index(model)
    table = installed_registry()
    nodes = _source_words(raw, excluded_verses, source_id)
    complete_forms = defaultdict(set)
    for node in nodes:
        if node["bare"]:
            for support in node["supports"]:
                complete_forms[support["record_id"]].add(lookup_key(node["form"]))
    bases = list(_base_variants(lexical, table, complete_forms))
    bases += list(_bare_subject_candidates(nodes, table))
    attached_index = defaultdict(dict)
    for candidate in _source_attached_variants(nodes, bases, table):
        _add(attached_index, candidate)
    attached = [candidate for rows in attached_index.values() for candidate in rows.values()]
    capacities = defaultdict(list)
    for candidate in attached:
        for witness in candidate["valency_witnesses"]:
            group = capacities[_capacity_key(candidate, witness["host_form"])]
            # Extra matching source occurrences are redundant witnesses, not
            # new lexical readings or an unbounded valency graph.
            if len(group) < 2:
                group.append((witness, candidate["supports"]))
    index = defaultdict(dict)
    for candidate in bases:
        seen = set()
        for witness, supports in capacities.get(_capacity_key(candidate, candidate["form"]), ()):
            fingerprint = _wire(witness)
            if fingerprint not in seen:
                seen.add(fingerprint)
                candidate["valency_witnesses"].append(witness)
                candidate["supports"] += supports
        candidate["supports"] = list({s["record_id"]: s for s in candidate["supports"]}.values())
        _add(index, candidate)
    for candidate in attached:
        _add(index, candidate)
    if sum(len(rows) for rows in index.values()) > MAX_VARIANTS:
        raise resource_limit("Person bridge exceeds its variant budget")
    return MappingProxyType({key: tuple(_wire(row) for _, row in sorted(rows.items()))
                             for key, rows in index.items()})


def _capacity_key(candidate, form):
    clusters = lookup_clusters(form)
    # A capacity witness transfers only inside the witnessed complete body,
    # not from a shared root to another derivational form or lexical sense.
    if candidate["family"]:
        clusters[0][0] = "ي"
    if candidate["construction"] == "inflected" and candidate["family"] in (None, "plain"):
        clusters[-1][1] -= VOWELS
    return (candidate["lemma_bw"], candidate["root"], candidate["voice"], candidate["aspect"],
            candidate["family"], _render(clusters))


def _surface_fields(candidate, surface):
    result = deepcopy(candidate)
    result.pop("mutable_clusters", None)
    result["surface"] = surface
    profile = result["person_profile"]
    result.update(person_name=("third" if result["kind"] == "noun" and result["pos"] != "PRON" else None)
                  if profile is None else _PERSON[profile["person"]],
                  gender_name=result.get("lexical_gender") if profile is None else _GENDER[profile["gender"]],
                  number_name=result.get("lexical_number") if profile is None else _NUMBER[profile["number"]])
    clusters = lookup_clusters(surface)
    for part in result["parts"]:
        start, end = part["start_cluster"], part["end_cluster"]
        lo, hi = clusters[start][2], clusters[end - 1][3]
        part.update(char_start=lo, char_end=hi, byte_start=len(surface[:lo].encode("utf-8")),
                    byte_end=len(surface[:hi].encode("utf-8")), surface=surface[lo:hi])
    support_ids = sorted({s["record_id"] for s in result["supports"]})
    for nun in result["nun_readings"]:
        index = nun.get("cluster_index")
        nun["support_ids"] = support_ids
        nun["span"] = None
        nun["surface"] = None
        if index is not None and nun["realization"] == "present":
            if type(index) is not int or not 0 <= index < len(clusters) or clusters[index][0] != "ن":
                raise NabtError("PERSON_SOURCE_GEOMETRY_FAILED", "A visible nun lost its source cluster", status="DEFER")
            lo, hi = clusters[index][2:4]
            nun["span"] = {"byte_start": len(surface[:lo].encode("utf-8")),
                           "byte_end": len(surface[:hi].encode("utf-8"))}
            nun["surface"] = surface[lo:hi]
    result["law_id"] = LAW_ID
    result["reader_version"] = READER_VERSION
    result["id"] = sha256(_wire(result)).hexdigest()
    return result


def person_candidates(surface, *, lexical_model=None):
    """Replay source-backed alternatives for one bounded written surface.

    Span coordinates are relative to this exact UTF-8 surface.  A candidate
    is never a uniquely selected analysis, actual attachment, or referent.
    """
    if type(surface) is not str:
        raise NabtError("INVALID_PERSON_SURFACE", "Use one Arabic text surface")
    try:
        encoded_size = len(surface.encode("utf-8"))
    except UnicodeError as error:
        raise NabtError("INVALID_UTF8", "Use a Unicode surface encodable as UTF-8") from error
    if encoded_size > MAX_SURFACE_BYTES:
        raise resource_limit("Person surface exceeds its byte budget")
    table = installed_registry()
    clusters = lookup_clusters(surface)
    if clusters is None:
        return []
    candidates = []
    for row in table["separate_pronouns"]:
        if _match(surface, row["surface"]):
            candidates.append({"kind": "noun", "pos": "PRON", "form": row["surface"],
                "base_form": None, "person_profile": _profile(row), "profile_id": None,
                "family": None, "form_kind": "separate_pronoun", "aspect": None,
                "voice": None, "voice_basis": None, "lemma": None, "lemma_bw": None, "root": None,
                "construction": "built", "class_candidates": [], "possible_cases": [0, 1, 2],
                "variant": "declared_separate_pronoun", "supports": [], "source_person_code": None,
                "host_form": row["surface"], "host_variant": "declared_separate_pronoun",
                "host_end_cluster": len(clusters), "segmentation_licensed": True,
                "parts": [{"kind": "separate_pronoun", "start_cluster": 0, "end_cluster": len(clusters)}],
                "attached_pronouns": [], "nun_readings": [], "valency_witnesses": [],
                "rule_ids": ["DECLARED_UNICODE_SEPARATE_PRONOUN_INVENTORY"],
                "obligations": ["REFERENT_REQUIRES_SEPARATE_GROUNDED_CONTEXT"],
                "authority": "DECLARED_INVENTORY_READING_NOT_WORLD_REFERENCE"})
    if lexical_model is not None:
        lexical_index(lexical_model)  # validates type, full bytes and exclusions
        index = _compile(lexical_model.raw, lexical_model.excluded_verses,
                         lexical_model.source_id, EXPECTED_TABLE_SHA256)
        for encoded in index.get(lookup_key(surface), ()):
            candidate = json.loads(encoded)
            if _match(surface, candidate["form"], candidate["mutable_clusters"]):
                candidates.append(candidate)
    if len(candidates) > MAX_CANDIDATES:
        raise resource_limit("Person surface exceeds its candidate budget")
    return sorted((_surface_fields(row, surface) for row in candidates), key=lambda row: row["id"])


def _field(tokens, start):
    values = [value[len(start):] for value in tokens if value.startswith(start)]
    return values[0] if len(values) == 1 else None


def _support(row, source):
    return {"record_id": row["identity"], "source_id": source["id"],
            "source_sha256": source["sha256"], "ordinal": row["ordinal"],
            "byte_start": row["byte_start"], "byte_end": row["byte_end"],
            "locator": row["locator"], "masked_fields": list(MASKED_FEATURES),
            "authority": "ANNOTATED_TRAINING_SOURCE_ONLY"}


def _subject_suffix(node, suffix):
    """Complete source person + suffix geometry, never PRON alone."""
    if suffix["tag"] != "PRON" or suffix["code"] != node["person"]:
        return False
    p, aspect, form = node["person"], node["aspect"], suffix["form"]
    if aspect == "IMPF":
        shapes = ({"3MP", "2MP"}, ("و", "وَا", "وْا", "وْ", "ونَ", "ون"))
        if p in shapes[0] and lookup_key(form) in {lookup_key(s) for s in shapes[1]}:
            return True
        if p in ("3MD", "3FD", "3D", "2D", "2MD", "2FD") and lookup_key(form) in ("ا", "ان"):
            return True
        if p == "2FS" and lookup_key(form) in ("ي", "ين"):
            return True
        return p in ("3FP", "2FP") and _match(form, "نَ")
    shapes = ({"1S": ["تُ"], "1P": ["نَا"], "2MS": ["تَ"], "2FS": ["تِ"],
               "2D": ["تُمَا"], "2MD": ["تُمَا"], "2FD": ["تُمَا"], "2MP": ["تُمْ"],
               "2FP": ["تُنَّ"], "3D": ["ا"], "3MD": ["ا"], "3FD": ["ا"],
               "3MP": ["وا", "و"], "3FP": ["نَ"]} if aspect == "PERF" else
              {"2D": ["ا"], "2MD": ["ا"], "2FD": ["ا"], "2MP": ["وا", "و"],
               "2FS": ["ي"], "2FP": ["نَ"]} if aspect == "IMPV" else {})
    return any(_match(form, expected) for expected in shapes.get(p, ()))


def _source_words(raw, excluded_verses, source_id):
    from .corpus_sources import read_corpus
    from .corpus_evidence import ROOT_BW
    corpus = read_corpus(raw, format="qac", source_id=source_id)
    groups = defaultdict(list)
    for row in corpus["records"]:
        loc = row["locator"]
        if row["valid"] and loc and f"{loc[0]}:{loc[1]}" not in excluded_verses:
            groups[tuple(loc[:3])].append(row)
    result = []
    for loc, rows in groups.items():
        rows.sort(key=lambda row: row["locator"][3])
        if [row["locator"][3] for row in rows] != list(range(1, len(rows) + 1)):
            continue
        stems = [row for row in rows if row["feature_tokens"][0] == "STEM"]
        if len(stems) != 1:
            continue
        stem = stems[0]
        before, after = rows[:rows.index(stem)], rows[rows.index(stem) + 1:]
        if any(row["feature_tokens"][0] != "PREFIX" for row in before):
            continue
        tokens = [t for t in stem["feature_tokens"] if t not in ("NOM", "ACC", "GEN") and not t.startswith("MOOD:")]
        pos = _field(tokens, "POS:")
        if pos != stem["fields"]["TAG"] or pos not in ("N", "PN", "ADJ", "PRON", "DEM", "REL", "V"):
            continue
        aspects = [a for a in ("PERF", "IMPF", "IMPV") if a in tokens]
        if pos == "V" and (len(aspects) != 1 or "ACT" in tokens and "PASS" in tokens):
            continue
        pg = [token for token in tokens if re.fullmatch(r"[123](?:[MF])?[SDP]", token)]
        nominal_traits = [token for token in tokens if re.fullmatch(r"[123]?[MF]?[SDP]", token) or token in ("M", "F")]
        traits = nominal_traits[0] if len(nominal_traits) == 1 else ""
        root_bw, lemma_bw = _field(tokens, "ROOT:"), _field(tokens, "LEM:")
        root = "".join(ROOT_BW[c] for c in root_bw) if root_bw and all(c in ROOT_BW for c in root_bw) else None
        try:
            form = buckwalter_to_arabic(stem["fields"]["FORM"])
            lemma = None if lemma_bw is None else buckwalter_to_arabic(lemma_bw)
            suffixes = [{"tag": row["fields"]["TAG"], "code": _field(row["feature_tokens"], "PRON:"),
                         "form": buckwalter_to_arabic(row["fields"]["FORM"]),
                         "support": _support(row, corpus["source"])} for row in after]
        except NabtError:
            continue
        if lookup_clusters(form) is None or any(lookup_clusters(s["form"]) is None for s in suffixes):
            continue
        if any(row["feature_tokens"][0] != "SUFFIX" or row["fields"]["TAG"] not in ("PRON", "EMPH") for row in after):
            continue
        node = {"loc": loc, "stem": form, "pos": pos, "kind": "verb" if pos == "V" else "noun",
                "person": pg[0] if len(pg) == 1 else None, "aspect": aspects[0] if aspects else None,
                "gender": "masculine" if "M" in traits else "feminine" if "F" in traits else None,
                "number": {"S": "singular", "D": "dual", "P": "plural"}.get(traits[-1:] or None),
                "voice": "passive" if "PASS" in tokens else "active" if pos == "V" else None,
                "voice_basis": "QAC_EXPLICIT_VOICE" if "PASS" in tokens or "ACT" in tokens else
                    "QAC_DEFAULT_ACTIVE_ABSENT_PASS" if pos == "V" else None,
                "lemma": lemma, "lemma_bw": lemma_bw, "root": root, "suffixes": suffixes,
                "has_article": any("Al+" in row["feature_tokens"] for row in before),
                "supports": [_support(row, corpus["source"]) for row in [stem, *after]]}
        subject = bool(suffixes and node["kind"] == "verb" and _subject_suffix(node, suffixes[0]))
        node["subject"] = subject
        node["host_form"] = form + (suffixes[0]["form"] if subject else "")
        node["form"] = form + "".join(suffix["form"] for suffix in suffixes)
        node["bare"] = len(suffixes) == int(subject)
        result.append(node)
    return result


def _bare_subject_candidates(nodes, table):
    for node in nodes:
        if not node["bare"] or not node["subject"] or node["aspect"] not in ("PERF", "IMPV"):
            continue
        stem_length, length = len(lookup_clusters(node["stem"])), len(lookup_clusters(node["form"]))
        for profile in _profiles(node["person"], table):
            entry = {**node, "form": node["form"], "variant": "complete_attested_subject_word",
                     "construction": "built", "class_candidates": [], "possible_cases": [], "nun_positions": []}
            candidate = _candidate(entry, profile, None)
            candidate["parts"] = [{"kind": "verbal_stem", "start_cluster": 0, "end_cluster": stem_length},
                                  {"kind": "subject_pronoun", "start_cluster": stem_length, "end_cluster": length}]
            if node["person"] in ("2FP", "3FP") and lookup_key(node["suffixes"][0]["form"]) == "ن":
                candidate["nun_readings"] = [{"kind": "feminine_subject", "cluster_index": stem_length,
                                              "realization": "present", "status": "SOURCE_QUALIFIED"}]
            candidate["rule_ids"] = ["QAC_COMPLETE_SUBJECT_SUFFIX_WORD"]
            yield candidate


def _matching_bases(node, bases_by_key, table):
    key = lookup_key(node["host_form"])
    options = list(bases_by_key.get(key, ()))
    # Orthographic separator alif is omitted before an attached object. This
    # branch still requires an independently retained full -waw-nun base.
    if key.endswith("و"):
        options += [b for b in bases_by_key.get(key + "ا", ())
                    if b["family"] == "masculine_plural" and b["variant"] == "nun_deleted_from_retained_base"]
    allowed_profiles = {_wire(_profile(p)) for p in _profiles(node["person"], table)}
    result = []
    for base in options:
        if (not node["lemma_bw"] or not node["root"] or base["lemma_bw"] != node["lemma_bw"]
                or base["root"] != node["root"] or base["pos"] != node["pos"]
                or base["aspect"] != node["aspect"] or base["voice"] != node["voice"]):
            continue
        if node["kind"] == "verb" and _wire(base["person_profile"]) not in allowed_profiles:
            continue
        if not any(tuple(s["locator"][:3]) != node["loc"] for s in base["supports"]):
            continue
        expected = base["form"]
        if lookup_key(expected) == key + "ا":
            expected = _render(lookup_clusters(expected)[:-1])
        if _match(node["host_form"], expected, base["mutable_clusters"]):
            result.append(base)
    return result


def _attachment_options(suffix, node, table):
    source_profiles = {p["qac"] for p in _profiles(suffix["code"], table)}
    key = lookup_key(suffix["form"])
    rows = [row for row in table["attached_forms"] if row["host"] in (node["kind"], "either") and
            lookup_key(row["surface"]) == key]
    # A conflicting source annotation cannot establish the suffix family.
    if not any(row["qac"] in source_profiles and _match(suffix["form"], row["surface"]) for row in rows):
        return []
    # Ka/ki is a productive person/gender contrast in one source-established
    # pronominal slot. Hu/hi is a phonologically conditioned allomorph: this
    # bounded bridge keeps the attested vocalization instead of freely
    # switching it after an unchanged host. Dual gender remains ambiguous.
    return [row for row in rows if key == "ك" or _match(suffix["form"], row["surface"])]


def _source_attached_variants(nodes, bases, table):
    bases_by_key = defaultdict(list)
    profile_by_id = {row["qac"]: row for row in table["profiles"]}
    for base in bases:
        bases_by_key[lookup_key(base["form"])].append(base)
    for node in nodes:
        if node["bare"]:
            continue
        n_host = len(lookup_clusters(node["host_form"]))
        matched = _matching_bases(node, bases_by_key, table)
        for base in matched or [None]:
            source_profiles = _profiles(node["person"], table)
            if base and base["person_profile"]:
                source_profiles = [row for row in source_profiles if _profile(row) == base["person_profile"]]
            for profile in source_profiles or [None]:
                if base:
                    initial = deepcopy(base)
                    initial.update(form=node["host_form"], base_form=base["form"],
                                   supports=list(node["supports"]) + list(base["supports"]))
                else:
                    entry = {**node, "form": node["host_form"], "variant": "attested_attached_word",
                             "construction": None, "class_candidates": [], "possible_cases": [], "nun_positions": []}
                    initial = _candidate(entry, profile, None)
                    initial["obligations"].append("INDEPENDENT_COMPLETE_HOST_BASE_REQUIRED")
                    stem_clusters = lookup_clusters(node["stem"])
                    if (node["kind"] == "verb" and node["root"] and node["root"].endswith("ن") and
                            stem_clusters[-1][0] == "ن" and
                            (node["person"] in ("1S", "1P", "2MS", "3MS", "3FS") or node["subject"])):
                        initial["nun_readings"] = [{"kind": "radical", "cluster_index": len(stem_clusters) - 1,
                                                    "realization": "present", "status": "SOURCE_ROOT_AND_STEM_BOUNDARY"}]
                initial["form_kind"] = "attached_pronoun_word"
                initial["variant"] = "attested_attached_word"
                initial["host_form"] = node["host_form"]
                initial["host_variant"] = None if base is None else base["variant"]
                initial["host_end_cluster"] = n_host
                initial["segmentation_licensed"] = bool(base)
                initial["mutable_clusters"] = []
                initial["parts"] = [{"kind": "verbal_stem" if node["kind"] == "verb" else "nominal_stem",
                                     "start_cluster": 0, "end_cluster": len(lookup_clusters(node["stem"]))}]
                initial["attached_pronouns"] = []
                initial["valency_witnesses"] = []
                if node["subject"]:
                    initial["parts"].append({"kind": "subject_pronoun", "start_cluster": len(lookup_clusters(node["stem"])),
                                             "end_cluster": n_host})
                # The host base may contain a separator alif absent before a
                # suffix. Its deletion cannot create an observed nun span.
                if base and lookup_key(base["form"]) == lookup_key(node["host_form"]) + "ا":
                    initial["rule_ids"].append("SEPARATOR_ALIF_OMITTED_BEFORE_ATTACHED_PRONOUN")
                variants = [initial]
                for index, suffix in enumerate(node["suffixes"][int(node["subject"]):]):
                    next_variants = []
                    for candidate in variants:
                        start = len(lookup_clusters(candidate["form"]))
                        if suffix["tag"] == "EMPH":
                            next_variants.append(_attach_emphasis(candidate, suffix, node, base, start, index))
                            continue
                        options = _attachment_options(suffix, node, table)
                        for option in options or [None]:
                            result = deepcopy(candidate)
                            form = suffix["form"] if option is None else option["surface"]
                            end = start + len(lookup_clusters(form))
                            result["form"] += form
                            p = None if option is None else _profile(profile_by_id[option["qac"]])
                            licensed = bool(base and option is not None and
                                            (node["kind"] == "verb" and node["voice"] == "active" or
                                             node["pos"] in ("N", "PN") and not node["has_article"]))
                            relation = "verbal_object" if node["kind"] == "verb" else "possessive"
                            result["parts"].append({"kind": relation if licensed else "annotated_pronominal_suffix",
                                                    "start_cluster": start, "end_cluster": end})
                            result["attached_pronouns"].append({"person_profile": p,
                                "start_cluster": start, "end_cluster": end,
                                "attachment_candidates": [relation] if licensed else ["unknown"],
                                "licensed": licensed, "source_person_code": suffix["code"],
                                "support_ids": [s["record_id"] for s in result["supports"]]})
                            if licensed:
                                result["rule_ids"].append("SOURCE_SUFFIX_AND_INDEPENDENT_HOST_ATTACHMENT")
                                if relation == "verbal_object":
                                    result["valency_witnesses"].append({"kind": "source_attached_object",
                                        "lemma_bw": node["lemma_bw"], "root": node["root"], "voice": node["voice"],
                                        "host_form": node["host_form"], "source_form": node["form"],
                                        "support_ids": [s["record_id"] for s in result["supports"]],
                                        "authority": "CONDITIONAL_OBJECT_CAPACITY_NOT_AN_ASSIGNED_ROLE"})
                                if node["kind"] == "verb" and option["qac"] == "1S" and lookup_key(form) == "ني":
                                    result["nun_readings"].append({"kind": "protective", "cluster_index": start,
                                        "realization": "present", "status": "INDEPENDENT_BASE_AND_SOURCE_SUFFIX_QUALIFIED"})
                                    result["rule_ids"].append("VERB_BASE_PLUS_1S_NI_PROTECTIVE_NUN")
                            else:
                                result["segmentation_licensed"] = False
                                result["obligations"].append("ATTACHMENT_FUNCTION_UNRESOLVED")
                            next_variants.append(result)
                    variants = next_variants
                    if len(variants) > MAX_CANDIDATES:
                        raise resource_limit("Attached source word exceeds its correlated candidate budget")
                for candidate in variants:
                    candidate["supports"] = list({s["record_id"]: s for s in candidate["supports"]}.values())
                    yield candidate


def _attach_emphasis(candidate, suffix, node, base, start, previous_suffixes):
    result = deepcopy(candidate)
    form = suffix["form"]
    clusters = lookup_clusters(form)
    nuns = [index for index, cluster in enumerate(clusters) if cluster[0] == "ن"]
    result["form"] += form
    result["parts"].append({"kind": "annotated_emphasis", "start_cluster": start,
                            "end_cluster": start + len(clusters)})
    complete_nun = len(clusters) == 1 and len(nuns) == 1
    host_last = lookup_clusters(node["host_form"])[-1][1]
    direct = bool(base and complete_nun and clusters[0][1] in ({"ّ", "َ"}, {"ْ"}) and
                  host_last == {"َ"} and not previous_suffixes and not node["subject"] and
                  node["aspect"] == "IMPF" and base["family"] == "plain" and
                  base["variant"] == "attested")
    separated = bool(base and complete_nun and clusters[0][1] == {"ّ", "ِ"} and
                     not previous_suffixes and node["subject"] and
                     node["aspect"] == "IMPF" and base["family"] == "dual" and
                     base["variant"] == "nun_deleted_from_retained_base" and
                     lookup_key(node["suffixes"][0]["form"]) == "ا")
    if direct:
        result.update(construction="built", class_candidates=[], possible_cases=[])
        result["rule_ids"].append("DIRECT_EMPHASIS_FROM_COMPLETE_PLAIN_HOST_AND_SOURCE_PARTITION")
    elif separated:
        result.update(construction="inflected", class_candidates=[], possible_cases=[])
        result["rule_ids"].append("DUAL_ALIF_SEPARATES_EMPHASIS_WITH_FULL_FIVE_VERB_BASE")
        result["obligations"].append("SEPARATED_EMPHASIS_SIGN_REALIZATION_UNIMPLEMENTED")
    else:
        result["segmentation_licensed"] = False
        result.update(construction=None, class_candidates=[], possible_cases=[])
        result["obligations"].append("EMPHASIS_DIRECTNESS_UNRESOLVED")
    for index in nuns or [None]:
        result["nun_readings"].append({"kind": "emphatic_direct" if direct else "emphatic_separated" if separated else "emphasis",
            "cluster_index": None if index is None else start + index,
            "realization": "unresolved" if index is None else "present",
            "status": "SOURCE_AND_COMPLETE_BASE_QUALIFIED" if direct or separated else "SOURCE_ANNOTATED_CONNECTION_UNKNOWN",
            "directness": "direct" if direct else "separated" if separated else "unknown"})
    return result
