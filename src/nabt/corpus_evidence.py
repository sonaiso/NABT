"""Learn source-relative lexical witnesses without case, mood or role labels.

QAC is annotated evidence, not an oracle for a new occurrence.  This module
keeps its annotation identities, masks target labels, and transfers only an
explicitly delimited morphological paradigm.  A lemma is not automatically
the singular of a plural.  The original corpus is an external input, never an
installed answer dictionary.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
import re
from types import MappingProxyType

from .errors import NabtError, resource_limit

LEARNER_VERSION = "nabt.qac-lexical-evidence.v3"
PROJECTION_ID = "qac.extended-buckwalter.unicode.v1"
LOOKUP_ID = "qac.lookup.wasl-equivalence.v1"
MASKED_FEATURES = ("NOM", "ACC", "GEN", "MOOD:IND", "MOOD:SUBJ", "MOOD:JUS")
MAX_CORPUS_BYTES = 64 * 1024 * 1024
MAX_VARIANTS = 300000
VOWELS = frozenset("ًٌٍَُِْ")
# The reversible character correspondence published by JQuranTree. Root A has
# a separate, declared meaning below; it must never change FORM decoding.
# Spelling the mapping as pairs makes spaces and Quranic signs unambiguous.
BW = dict(zip("'>&<}AbptvjHxd*rzs$SDTZEgfqklmnhwYyFNKaui~o^#`{",
              "ءأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوىيًٌٍَُِّْٰٓٔٱ", strict=True))
BW.update({":": "\u06dc", "@": "\u06df", '"': "\u06e0", "[": "\u06e2",
           ";": "\u06e3", ",": "\u06e5", ".": "\u06e6", "!": "\u06e8",
           "-": "\u06ea", "+": "\u06eb", "%": "\u06ec", "]": "\u06ed",
           "_": "ـ", " ": " "})
ROOT_BW = {k: v for k, v in BW.items() if v in "ءبتثجحخدذرزسشصضطظعغفقكلمنهوي"}
ROOT_BW["A"] = "ء"


from nabt import foundation

def _wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def buckwalter_to_arabic(value):
    if type(value) is not str or len(value) > 1024:
        raise NabtError("INVALID_BUCKWALTER", "Use a bounded extended Buckwalter string")
    try:
        return "".join(BW[c] for c in value)
    except KeyError as error:
        raise NabtError("UNSUPPORTED_BUCKWALTER", "Character is outside the declared projection") from error


def lookup_clusters(text):
    """A lookup projection only. Never rewrite source or source coordinates.

    Quranic recitation signs outside this small Arabic profile are an explicit
    boundary. No hamza collapse, dagger-alif expansion, or deleted-carrier
    recovery is performed here.
    """
    if type(text) is not str:
        return None
    result = []
    for i, c in enumerate(text):
        if c in VOWELS or c in "ّٰ":
            if not result or c in result[-1][1]:
                return None
            result[-1][1].add(c)
            result[-1][3] = i + 1
            if len(result[-1][1] & VOWELS) > 1:
                return None
        elif ("\u0621" <= c <= "\u063a" or "\u0641" <= c <= "\u064a" or c == "ٱ"):
            result.append(["ا" if c == "ٱ" else c, set(), i, i + 1])
        else:
            return None
    return result or None


def lookup_key(text):
    clusters = lookup_clusters(text)
    return None if clusters is None else "".join(c[0] for c in clusters)


def _render(clusters):
    order = "ًٌٍَُِّْٰ"
    return "".join(c[0] + "".join(m for m in order if m in c[1]) for c in clusters)


def _template(text, *, mutable_last=True):
    clusters = lookup_clusters(text)
    if clusters is None:
        return None
    if mutable_last:
        clusters[-1][1] -= VOWELS
    return _render(clusters)


def template_matches(text, template, *, mutable_last=True):
    observed, expected = lookup_clusters(text), lookup_clusters(template)
    if observed is None or expected is None or len(observed) != len(expected):
        return False
    for i, (a, b) in enumerate(zip(observed, expected)):
        if a[0] != b[0]:
            return False
        left, right = a[1], b[1]
        if mutable_last and i == len(observed) - 1:
            left, right = left - VOWELS, right - VOWELS
        # Missing vowels remain missing evidence. Explicit contradictory vowels
        # and shadda must not be repaired to fit a lexical entry.
        if left & VOWELS and right & VOWELS and left & VOWELS != right & VOWELS:
            return False
        if "ّ" in left and "ّ" not in right:
            return False
        if "ٰ" in left and "ٰ" not in right:
            return False
    return True


@dataclass(frozen=True, slots=True)
class QacLexicon:
    """Only raw evidence and exclusions are accepted, never caller-built entries."""
    raw: bytes
    excluded_verses: tuple[str, ...]
    source_id: str

    def summary(self):
        return json.loads(_compile(self.raw, self.excluded_verses, self.source_id)[1])


def _validate(raw, excluded_verses, source_id):
    if type(raw) is not bytes:
        raise NabtError("INVALID_CORPUS_BYTES", "Supply original, decoded QAC bytes")
    if len(raw) > MAX_CORPUS_BYTES:
        raise resource_limit("QAC source exceeds the learning budget")
    if type(source_id) is not str or not re.fullmatch(r"[a-z][a-z0-9_]{0,127}", source_id):
        raise NabtError("INVALID_SOURCE_ID", "Use a bounded ASCII source identity")
    if type(excluded_verses) is not tuple or len(excluded_verses) > 10000:
        raise NabtError("INVALID_CORPUS_EXCLUSIONS", "Use a tuple of unique chapter:verse identities")
    if any(type(v) is not str or not re.fullmatch(r"[1-9][0-9]{0,3}:[1-9][0-9]{0,4}", v)
           for v in excluded_verses) or len(set(excluded_verses)) != len(excluded_verses):
        raise NabtError("INVALID_CORPUS_EXCLUSIONS", "Exclusions must be canonical and distinct")


def learn_qac_lexicon(raw, *, excluded_verses=(), source_id="qac"):
    foundation.require_foundation('nabt.corpus_evidence.learn_qac_lexicon')
    _validate(raw, excluded_verses, source_id)
    model = QacLexicon(raw, tuple(sorted(excluded_verses)), source_id)
    model.summary()  # Reject malformed corpus input before returning a model.
    return model


def lexical_index(model):
    if type(model) is not QacLexicon:
        raise NabtError("INVALID_LEXICAL_MODEL", "Build lexical evidence from original QAC bytes")
    _validate(model.raw, model.excluded_verses, model.source_id)
    # Recompile from immutable raw input (memoized by the full bytes). The caller
    # cannot inject an entry, a successful status, or an authoritative digest.
    index, summary = _compile(model.raw, model.excluded_verses, model.source_id)
    return index, json.loads(summary)


def _feature(tokens, prefix):
    values = [t[len(prefix):] for t in tokens if t.startswith(prefix)]
    return values[0] if len(values) == 1 else None


def _person_gender_number(tokens):
    values = [t for t in tokens if re.fullmatch(r"[123]?[MF]?[SDP]", t) or t in ("M", "F")]
    if len(values) != 1:
        return None, None, None
    value = values[0]
    gender = "masculine" if "M" in value else "feminine" if "F" in value else None
    number = {"S": "singular", "D": "dual", "P": "plural"}.get(value[-1])
    return value, gender, number


def _root(value):
    if not value or any(c not in ROOT_BW for c in value):
        return None
    return "".join(ROOT_BW[c] for c in value)


def _receipt(row, source):
    return {"record_id": row["identity"], "source_id": source["id"],
            "source_sha256": source["sha256"], "ordinal": row["ordinal"],
            "byte_start": row["byte_start"], "byte_end": row["byte_end"],
            "locator": row["locator"],
            "masked_fields": list(MASKED_FEATURES),
            "authority": "ANNOTATED_TRAINING_SOURCE_ONLY"}


def _subject_shapes(person):
    return ({"ون", "وا", "و"} if person in ("3MP", "2MP") else
            {"ان", "ا"} if person in ("3MD", "3FD", "3D", "2D", "2MD", "2FD") else
            {"ين", "ي"} if person == "2FS" else set())


def _verbal_root_nun_index(entry, clusters, suffixes):
    person = entry["person"]
    key = "".join(c[0] for c in clusters)
    retained = ("ون" if person in ("3MP", "2MP") else "ين" if person == "2FS" else "ان")
    if _subject_shapes(person) and entry["aspect"] == "IMPF" and key.endswith(retained):
        index = len(clusters) - 3
    elif person in ("1S", "1P", "2MS", "3MS", "3FS"):
        index = len(clusters) - 1
    elif suffixes and suffixes[0]["fields"]["FEATURES"] == "SUFFIX|PRON:" + str(person):
        fields = suffixes[0]["fields"]
        try:
            suffix_key = lookup_key(buckwalter_to_arabic(fields["FORM"]))
        except NabtError:
            return None
        if (person in ("3FP", "2FP") and fields["FORM"] == "na" or
                suffix_key in _subject_shapes(person)):
            index = len(clusters) - 1
        else:
            return None
    else:
        return None
    return index if index >= 0 and clusters[index][0] == "ن" else None


def _annotated_verbal_word(stem, suffixes, source, entry):
    """Retain attested suffix evidence without licensing an attached clause.

    These are source-relative segmentation candidates. A source EMPH label
    neither settles directness nor grants an ordinary imperfect paradigm.
    Object/protective suffixes are not silently dropped from the new token.
    """
    if not suffixes:
        return None
    pieces, nuns, form, offset = [], [], "", 0
    for number, row in enumerate([stem, *suffixes]):
        fields = row["fields"]
        if number and (not fields["FEATURES"].startswith("SUFFIX|") or fields["TAG"] not in ("PRON", "EMPH")):
            return None
        try:
            piece = buckwalter_to_arabic(fields["FORM"])
        except NabtError:
            return None
        clusters = lookup_clusters(piece)
        if clusters is None:
            return None
        kind = "verbal_stem" if number == 0 else "annotated_pronominal_suffix"
        if number == 0 and entry["root"] and entry["root"].endswith("ن"):
            radical_index = _verbal_root_nun_index(entry, clusters, suffixes)
            if radical_index is not None:
                nuns.append({"kind": "radical", "cluster_index": radical_index,
                             "realization": "present", "status": "SOURCE_QUALIFIED"})
        if number == 1 and fields["FEATURES"] == "SUFFIX|PRON:" + str(entry["person"]):
            if entry["person"] in ("3FP", "2FP") and fields["FORM"] == "na":
                kind = "feminine_subject"
                nuns.append({"kind": kind, "cluster_index": offset,
                             "realization": "present", "status": "SOURCE_QUALIFIED"})
            else:
                if "".join(c[0] for c in clusters) in _subject_shapes(entry["person"]):
                    kind = "annotated_subject_suffix"
        if fields["TAG"] == "EMPH":
            kind = "annotated_emphasis"
            positions = [i for i, cluster in enumerate(clusters) if cluster[0] == "ن"]
            for index in positions or [None]:
                nuns.append({"kind": "emphasis", "cluster_index": None if index is None else offset + index,
                             "realization": "unresolved" if index is None else "present",
                             "status": "SOURCE_ANNOTATED_CONNECTION_UNKNOWN", "directness": "unknown"})
        pieces.append({"kind": kind, "start_cluster": offset, "end_cluster": offset + len(clusters)})
        offset += len(clusters)
        form += piece
    # Omit a redundant sole-subject candidate only when the ordinary path
    # really admits the same complete form. An attested deleted-nun form
    # without a retained base must remain an annotation-only observation.
    if len(pieces) == 2:
        if pieces[-1]["kind"] == "feminine_subject":
            return None
        if pieces[-1]["kind"] == "annotated_subject_suffix":
            retained = ("ون" if entry["person"] in ("3MP", "2MP") else
                        "ين" if entry["person"] == "2FS" else "ان")
            if (entry["aspect"] in ("PERF", "IMPV") or
                    entry["aspect"] == "IMPF" and len(lookup_clusters(form)) >= 3 and lookup_key(form).endswith(retained)):
                return None
    return {**entry, "form": form, "template": _template(form, mutable_last=False),
            "supports": [_receipt(row, source) for row in [stem, *suffixes]],
            "construction": None, "nun": None, "nun_positions": nuns,
            "source_parts": pieces, "annotation_only": True,
            "suffix_boundary": "ATTACHED_SUFFIX_ACTIVATION_UNIMPLEMENTED",
            "form_rule": "attested_stem_and_suffix_partition", "variant": "attested_attached_word"}


def _plural_letter_observation(entry):
    """A literal paired-form premise, not a singular or soundness inference."""
    if (entry["kind"] != "noun" or entry["gender"] != "masculine" or entry["number"] != "plural"
            or not entry["lemma_bw"] or not entry["root"] or entry["construction"] == "built"):
        return None
    clusters = lookup_clusters(entry["form"])
    key = lookup_key(entry["form"])
    if len(clusters) < 3 or not key.endswith(("ون", "ين")):
        return None
    carrier = key[-2]
    if (clusters[-3][1] & VOWELS != ({"ُ"} if carrier == "و" else {"ِ"})
            or clusters[-2][1] not in (set(), {"ْ"}) or clusters[-1][1] != {"َ"}):
        return None
    identity = (entry["lemma_bw"], entry["root"], entry["pos"], entry["gender"], entry["number"],
                key[:-2], _template(_render(clusters[:-2])))
    return identity, carrier


def _nun_positions(entry):
    """Distinct character witnesses within one reading; deletion has no span."""
    if entry.get("annotation_only"):
        return entry["nun_positions"]
    clusters = lookup_clusters(entry["form"])
    key = lookup_key(entry["form"])
    result = []
    final_kind = entry["nun"]
    deleted = entry["variant"] == "nun_deleted_from_retained_base"
    if final_kind:
        present = key.endswith("ن") and not deleted
        result.append({"kind": final_kind, "cluster_index": len(clusters) - 1 if present else None,
                       "realization": "present" if present else "deleted" if deleted else "unresolved",
                       "status": "SOURCE_QUALIFIED"})
    # The lexical root is a source annotation. Its final nun must also be
    # visible at the corresponding stem boundary, not merely somewhere in
    # a word that happens to contain nun.
    if entry["root"] and entry["root"].endswith("ن") and final_kind != "radical":
        if final_kind in ("five_verb_raf", "nominal_dual_plural"):
            base = lookup_clusters(entry.get("base_form") or entry["form"])
            index = len(base) - 3
        elif final_kind == "feminine_subject":
            index = len(clusters) - 2
        elif entry["kind"] == "verb":
            index = len(clusters) - 1
        else:
            # An unresolved nominal number/ending cannot identify the radical
            # nun merely because both ROOT and the written word end in nun.
            index = -1
        if index >= 0 and index < len(clusters) and clusters[index][0] == "ن":
            result.insert(0, {"kind": "radical", "cluster_index": index,
                              "realization": "present", "status": "SOURCE_QUALIFIED"})
    return result


@lru_cache(maxsize=2)
def _compile(raw, excluded_verses, source_id):
    from .corpus_sources import read_corpus
    corpus = read_corpus(raw, format="qac", source_id=source_id)
    excluded = set(excluded_verses)
    groups = defaultdict(list)
    counts = Counter()
    for record in corpus["records"]:
        loc = record["locator"]
        if loc is None or not record["valid"]:
            counts["invalid_records"] += 1
            continue
        if f"{loc[0]}:{loc[1]}" in excluded:
            counts["excluded_records"] += 1
            continue
        groups[tuple(loc[:3])].append(record)
    entries = []
    for loc, records in groups.items():
        records = sorted(records, key=lambda r: r["locator"][3])
        if [r["locator"][3] for r in records] != list(range(1, len(records) + 1)):
            counts["non_partition_words"] += 1
            continue
        stems = [r for r in records if r["fields"]["FEATURES"].split("|")[0] == "STEM"]
        if len(stems) != 1:
            counts["non_single_stem_words"] += 1
            continue
        stem = stems[0]
        fields = stem["fields"]
        tokens = [t for t in fields["FEATURES"].split("|")
                  if t not in ("NOM", "ACC", "GEN") and not t.startswith("MOOD:")]
        pos = _feature(tokens, "POS:")
        if pos != fields["TAG"] or pos not in ("N", "PN", "ADJ", "PRON", "DEM", "REL", "V"):
            counts["outside_lexical_pos"] += 1
            continue
        if pos == "V" and sum(a in tokens for a in ("PERF", "IMPF", "IMPV")) != 1:
            counts["ambiguous_aspect"] += 1
            continue
        try:
            form = buckwalter_to_arabic(fields["FORM"])
            lemma_bw = _feature(tokens, "LEM:")
            lemma = None if lemma_bw is None else buckwalter_to_arabic(lemma_bw)
        except NabtError:
            counts["unsupported_transliteration"] += 1
            continue
        if lookup_clusters(form) is None:
            counts["outside_lookup_profile"] += 1
            continue
        person, gender, number = _person_gender_number(tokens)
        root = _root(_feature(tokens, "ROOT:"))
        suffixes = records[records.index(stem) + 1:]
        supporting = [stem]
        nun = None
        construction = None
        lexical_entry = {"kind": "verb" if pos == "V" else "noun", "pos": pos,
                         "form": form, "template": _template(form), "lemma": lemma,
                         "lemma_bw": lemma_bw, "root": root, "gender": gender, "number": number,
                         "person": person, "aspect": next((a for a in ("PERF", "IMPF", "IMPV") if a in tokens), None),
                         "voice": "passive" if "PASS" in tokens else "active" if "ACT" in tokens else None,
                         "construction": None, "nun": None,
                         "supports": [_receipt(stem, corpus["source"])],
                         "has_article_source": any("Al+" in r["fields"]["FEATURES"].split("|") for r in records[:records.index(stem)]),
                         "form_rule": "source_stem_and_qualified_subject_suffix", "variant": "attested"}
        if pos in ("N", "ADJ"):
            lexical_entry["nominal_derivation_features"] = sorted(t for t in tokens
                if t in ("ACT", "PASS", "PCPL", "VN") or re.fullmatch(r"\([IVX]+\)", t))
        if pos == "V":
            attached = _annotated_verbal_word(stem, suffixes, corpus["source"], lexical_entry)
            if attached is not None:
                entries.append(attached)
                counts["attested_suffix_candidates"] += 1
        if pos == "V":
            subject = [r for r in suffixes if r["fields"]["FEATURES"] == "SUFFIX|PRON:" + str(person)]
            # First matching-person suffix is only a subject candidate; license
            # it for the plural/dual persons whose verb paradigm requires it.
            if person in ("3MP", "2MP", "3MD", "3FD", "3D", "2D", "2MD", "2FD", "2FS", "3FP", "2FP") and subject:
                if suffixes[0] is not subject[0]:
                    counts["ambiguous_subject_suffix"] += 1
                    continue
                form += buckwalter_to_arabic(subject[0]["fields"]["FORM"])
                supporting.append(subject[0])
            emph = [r for r in suffixes if r["fields"]["TAG"] == "EMPH"]
            if emph:
                # The corpus label EMPH alone does not settle directness. Keep
                # this outside the transferable paradigm, not as an ordinary
                # imperfect and not as deleted five-verb nun.
                counts["emphatic_connection_boundary"] += 1
                continue
            if lookup_clusters(form) is None:
                counts["outside_lookup_profile"] += 1
                continue
            if person in ("3FP", "2FP"):
                if (len(supporting) != 2 or supporting[-1]["fields"]["FORM"] != "na"
                        or not lookup_key(form).endswith("ن")):
                    counts["feminine_suffix_boundary"] += 1
                    continue
                nun, construction = "feminine_subject", "built"
            elif "PERF" in tokens or "IMPV" in tokens:
                construction = "built"
        elif pos in ("PRON", "DEM", "REL"):
            # Dual demonstratives/relatives have a separate inflected analysis.
            construction = None if number == "dual" else "built"
        entry = {**lexical_entry,
                 "form": form, "template": _template(form, mutable_last=construction != "built"),
                 "construction": construction, "nun": nun,
                 "supports": [_receipt(r, corpus["source"]) for r in supporting]}
        entries.append(entry)

    # Paradigms are grouped by a lexical annotation plus its spelling. A lemma
    # and root match alone must not transfer one homograph's gender to another.
    nominal_groups = defaultdict(list)
    singulars = defaultdict(list)
    plural_letters = defaultdict(dict)
    def nominal_key(entry):
        return (entry["lemma_bw"], entry["root"], lookup_key(entry["form"]),
                entry["pos"], entry["gender"], entry["number"], entry["template"],
                tuple(entry.get("nominal_derivation_features", ())))
    for entry in entries:
        if entry["kind"] == "noun":
            nominal_groups[nominal_key(entry)].append(entry)
            observation = _plural_letter_observation(entry)
            if observation:
                identity, carrier = observation
                plural_letters[identity].setdefault(carrier, entry)
            if entry["number"] == "singular" and entry["lemma_bw"] and entry["root"]:
                singulars[(entry["lemma_bw"], entry["root"])].append(entry)

    vowel_families = {"َ": "a", "ً": "a", "ُ": "u", "ٌ": "u", "ِ": "i", "ٍ": "i"}
    nominal_stats = {}
    for key, group in nominal_groups.items():
        seen_vowels, proofs, tanwin_proofs = set(), [], []
        for entry in group:
            observed = lookup_clusters(entry["form"])[-1][1] & VOWELS
            if observed & set("ًٌٍ") and not tanwin_proofs:
                tanwin_proofs.append(entry)
            family = vowel_families.get(next(iter(observed), None))
            if family is not None and family not in seen_vowels:
                seen_vowels.add(family)
                proofs.append(entry)
        nominal_stats[key] = (bool(tanwin_proofs), len(seen_vowels) >= 2, proofs, tanwin_proofs)

    variants = []
    for original in entries:
        entry = dict(original)
        clusters = lookup_clusters(entry["form"])
        key = lookup_key(entry["form"])
        classes = []
        entry["singular_witnesses"] = []
        entry["nominal_form"] = None
        entry["possible_cases"] = [0, 1, 2] if entry["kind"] == "noun" else [0, 1, 3]
        if entry.get("annotation_only"):
            entry.update(class_candidates=[], possible_cases=[])
            variants.append(entry)
            continue
        if entry["kind"] == "noun" and entry["construction"] != "built":
            tanwin, paired, proofs, tanwin_proofs = nominal_stats[nominal_key(entry)]
            lemma_key = lookup_key(entry["lemma"]) if entry["lemma"] else None
            if (lemma_key and lemma_key.endswith("ي") and key == lemma_key[:-1]
                    and entry["root"] and entry["root"].endswith("ي")):
                entry.update(class_candidates=[], construction=None,
                             declension_boundary="DELETED_NOMINAL_YAA_UNIMPLEMENTED")
                variants.append(entry)
                counts["deleted_nominal_yaa_boundary"] += 1
                continue
            base = None
            letter_proofs = []
            if entry["number"] == "dual" and key.endswith(("ان", "ين")) and lemma_key:
                stem_key = key[:-2]
                if stem_key == lemma_key or stem_key == lemma_key.removesuffix("ة") + "ت":
                    classes, entry["nominal_form"], entry["nun"] = [2], "dual", "nominal_dual_plural"
                    base = stem_key
            elif entry["number"] == "plural" and lemma_key:
                if entry["gender"] == "masculine" and key.endswith(("ون", "ين")) and key[:-2] == lemma_key:
                    classes, entry["nominal_form"], entry["nun"] = [3], "masculine_plural_letter_paradigm", "nominal_dual_plural"
                    base = key[:-2]
                elif key.endswith("ات") and (key == lemma_key + "ات" or lemma_key.endswith("ة") and key == lemma_key[:-1] + "ات"):
                    classes, entry["nominal_form"] = [4], "sound_feminine_plural"
            observation = _plural_letter_observation(entry)
            if not classes and observation and set(plural_letters[observation[0]]) == {"و", "ي"}:
                classes, entry["nominal_form"], entry["nun"] = [3], "masculine_plural_letter_paradigm", "nominal_dual_plural"
                base = key[:-2]
                letter_proofs = [plural_letters[observation[0]][carrier] for carrier in ("و", "ي")]
            if not classes and key.endswith(("ى", "ا")) and entry["root"] and entry["root"][-1:] in "وي" and lemma_key and lemma_key.endswith(("ى", "ا")):
                classes = [6]
            elif not classes and key.endswith("ي") and entry["root"] and entry["root"].endswith("ي") and len(clusters) > 1 and "ِ" in clusters[-2][1] and "ّ" not in clusters[-1][1]:
                classes = [7]
            elif not classes:
                classes = [0] if tanwin else [0, 5]
                if entry["number"] == "dual":
                    entry.update(class_candidates=[], construction=None,
                                 declension_boundary="UNIMPLEMENTED_DUAL_PARADIGM")
                    variants.append(entry)
                    counts["unimplemented_dual_paradigm"] += 1
                    continue
            if classes in ([2], [3], [4]) or paired:
                entry["construction"] = "inflected"
                # Keep independent witnesses for the inference. One observed
                # word's unannotated case alone never supplies its target role.
                entry["construction_supports"] = [s for e in (letter_proofs or proofs) for s in e["supports"]]
                entry["construction_basis"] = ("paired_annotated_plural_letter_realizations" if letter_proofs else
                                               "paired_lexical_terminal_realizations" if paired else
                                               "annotated_number_and_lemma_recomposition")
            if entry["number"] == "plural":
                candidates = singulars.get((entry["lemma_bw"], entry["root"]), [])
                seen = set()
                for singular in candidates:
                    if singular["pos"] != entry["pos"]:
                        continue
                    s_key = lookup_key(singular["form"])
                    if s_key not in seen and s_key != key:
                        seen.add(s_key)
                        entry["singular_witnesses"].append({"form": singular["form"], "root": singular["root"],
                                                          "supports": singular["supports"]})
                # A failed sound-plural recognizer does not prove broken
                # plural: annexed and unsupported formations remain unknown.
            entry["class_candidates"] = classes
            if entry["pos"] in ("N", "ADJ") and entry["number"] == "singular" and classes == [0]:
                # Keep the actual surviving raw witness, not just an inferred
                # class flag, for a separately scoped nominal-form bridge.
                entry["nominal_tanwin_supports"] = [s for e in tanwin_proofs for s in e["supports"]]
            if (entry["nun"] is None and entry["root"] and entry["root"].endswith("ن") and key.endswith("ن")
                    and lemma_key == key and (entry["number"] == "singular" or
                                              entry["number"] is None and key == entry["root"])):
                entry["nun"] = "radical"
            variants.append(entry)
            # Letter paradigms require a licensed annotated number + an exact
            # lemma recomposition. Bare -an/-in/-un never creates the class.
            if base is not None:
                endings = (("ان", [1]), ("ين", [0, 2])) if classes == [2] else (("ون", [1]), ("ين", [0, 2]))
                for ending, cases in endings:
                    # The carrier alternation also changes the preceding
                    # vowel for masculine plurals. It never preserves a
                    # nominative damma before the oblique yaa.
                    stem_clusters = [[c, set(marks), lo, hi] for c, marks, lo, hi in clusters[:-2]]
                    stem_clusters[-1][1] -= VOWELS
                    stem_clusters[-1][1].add("َ" if classes == [2] else "ُ" if ending == "ون" else "ِ")
                    form = _render(stem_clusters) + ending
                    variants.append({**entry, "form": form, "template": _template(form), "possible_cases": cases,
                                     "variant": "nominal_letter_paradigm", "form_rule": "paired_annotated_plural_letters" if letter_proofs else "number_lemma_recomposition"})
        elif entry["kind"] == "verb" and entry["aspect"] == "IMPF" and entry["construction"] != "built":
            person = entry["person"]
            five = (9 if person in ("3MD", "3FD", "3D", "2D", "2MD", "2FD") else
                    10 if person in ("3MP", "2MP") else 11 if person == "2FS" else None)
            if five is not None:
                ending = {9: "ان", 10: "ون", 11: "ين"}[five]
                if not key.endswith(ending) or len(clusters) < 3:
                    counts["five_verb_requires_retained_base"] += 1
                    continue
                entry.update(class_candidates=[five], construction="inflected", nun="five_verb_raf", possible_cases=[1],
                             template=_template(entry["form"], mutable_last=False))
                variants.append(entry)
                deleted = _render(clusters[:-1]) + ("ا" if five == 10 else "")
                variants.append({**entry, "form": deleted, "template": _template(deleted, mutable_last=False),
                                 "possible_cases": [0, 3], "variant": "nun_deleted_from_retained_base",
                                 "form_rule": "five_verb_person_and_full_base", "base_form": entry["form"]})
            elif person in ("1S", "1P", "2MS", "3MS", "3FS") and entry["root"] and len(entry["root"]) in (3, 4):
                if entry["root"][-1] in "وي":
                    cls = {"ا": 12, "ى": 12, "و": 13, "ي": 14}.get(key[-1])
                    if cls is None:
                        counts["weak_verb_requires_full_base"] += 1
                        continue
                    required = {12: "َ", 13: "ُ", 14: "ِ"}[cls]
                    if len(clusters) <= 2 or "ّ" in clusters[-1][1] or clusters[-2][1] & VOWELS != {required}:
                        counts["weak_base_geometry_boundary"] += 1
                        continue
                    entry.update(class_candidates=[cls], construction="inflected", possible_cases=[0, 1])
                    variants.append(entry)
                    if len(clusters) > 2:
                        deleted = _render(clusters[:-1])
                        variants.append({**entry, "form": deleted, "template": _template(deleted), "possible_cases": [3],
                                         "variant": "weak_deleted_from_full_base", "form_rule": "weak_root_and_full_imperfect_base",
                                         "base_form": entry["form"]})
                else:
                    entry.update(class_candidates=[8], construction="inflected")
                    if entry["root"].endswith("ن") and key.endswith("ن"):
                        entry["nun"] = "radical"
                    variants.append(entry)
            else:
                counts["imperfect_root_boundary"] += 1
        else:
            entry["class_candidates"] = []
            variants.append(entry)
    if len(variants) > MAX_VARIANTS:
        raise resource_limit("Learned lexical variants exceed the declared budget")
    # Merge identical analyses, keeping bounded deterministic support samples.
    # Dropped duplicate witnesses change no alternative or lexical feature.
    by_key = defaultdict(dict)
    for entry in variants:
        if entry["template"] is None:
            continue
        entry["nun_positions"] = _nun_positions(entry)
        signature_fields = {k: v for k, v in entry.items() if k not in ("supports", "construction_supports", "has_article_source", "form")}
        signature = sha256(_wire(signature_fields)).hexdigest()
        key = lookup_key(entry["form"])
        if signature not in by_key[key]:
            entry["lexical_id"] = signature
            by_key[key][signature] = entry
        else:
            existing = by_key[key][signature]
            if len(existing["supports"]) < 4:
                existing["supports"] += entry["supports"][:4 - len(existing["supports"])]
    index = {k: tuple(_wire(v) for _, v in sorted(values.items())) for k, values in by_key.items()}
    inventory_digest = sha256(_wire({k: [json.loads(v) for v in values] for k, values in sorted(index.items())})).hexdigest()
    summary = {"learner_version": LEARNER_VERSION, "projection_id": PROJECTION_ID, "lookup_id": LOOKUP_ID,
               "source": corpus["source"], "excluded_verses": list(excluded_verses),
               "masked_features": list(MASKED_FEATURES), "target_role_labels_available": False,
               "inventory_sha256": inventory_digest, "lookup_keys": len(index),
               "lexical_readings": sum(len(v) for v in index.values()),
               "training_words": len(groups), "boundaries": dict(sorted(counts.items())),
               "authority": "SOURCE_RELATIVE_TRAINING_WITNESSES_NOT_FREE_ARABIC_ACQUISITION"}
    return MappingProxyType(index), _wire(summary)
