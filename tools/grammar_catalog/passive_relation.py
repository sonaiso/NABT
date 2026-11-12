"""Finite written passive clauses, projected from the existing discourse reader.

The lexicon supplies lemma, aspect, voice and nominal inflection exemplars. The
discourse owner must separately build a licensed verbal predication for this
particular source. Its external reference debt stays open.
"""
from hashlib import sha256
import json

from nabt.corpus_evidence import (
    buckwalter_to_arabic as arabic, learn_qac_lexicon, lookup_clusters, lookup_key,
)
from nabt.discourse_reader import read_discourse
from tools.arabic_training.source_reading import compatible

from .operations import ROOT, exact_terms


SCHEMA = "nabt.written-passive-frames.v1"
INVENTORY = "tools/grammar_catalog/data/passive_event_frames_v1.json"
INVENTORY_SHA256 = "2877c90bc41f77487c7ce6606a10ad1afcc7b9e1506ea97d35a3b7657d4b5c87"


def _inventory():
    raw = (ROOT / INVENTORY).read_bytes()
    if sha256(raw).hexdigest() != INVENTORY_SHA256:
        raise ValueError("Written passive lexical inventory changed")
    return json.loads(raw)


def _source_words(text):
    """One independent declarative frame, with only horizontal internal gaps."""
    words = exact_terms(text)
    if len(words) not in (2, 3):
        return []
    left = words[0]["codepoint_span"][0]
    right = words[-1]["codepoint_span"][1]
    if text[:left].strip() or text[right:].strip() not in ("", "."):
        return []
    for first, second in zip(words, words[1:]):
        gap = text[first["codepoint_span"][1]:second["codepoint_span"][0]]
        if not gap or any(c not in " \t" for c in gap):
            return []
    return words


def _lexicon(inventory):
    entries = []
    for family in inventory["families"]:
        for lemma, past, imperfect in family["readings"]:
            for surface, aspect in ((past, "PERF"), (imperfect, "IMPF")):
                entries.append((surface, "V", f"STEM|POS:V|{aspect}|PASS|LEM:{lemma}|ROOT:{family['root']}|3MS"))
    for stem, root in inventory["nouns"]:
        for ending in ("N", "K", "FA"):
            entries.append((stem + ending, "N", f"STEM|POS:N|LEM:{stem}|ROOT:{root}|MS"))
    lines = ["LOCATION\tFORM\tTAG\tFEATURES"]
    for i, (form, tag, features) in enumerate(entries, 1):
        lines.append(f"(1:{i}:1:1)\t{form}\t{tag}\t{features}")
    return learn_qac_lexicon(("\n".join(lines) + "\n").encode(), source_id="written_passive_inventory")


def _matching_family(surface, inventory, negative):
    clusters = lookup_clusters(surface)
    if not clusters or len(clusters) < 3:
        return None
    if "ُ" not in clusters[0][1] or ("َ" if negative else "ِ") not in clusters[-2][1]:
        return None
    for family in inventory["families"]:
        for _, past, imperfect in family["readings"]:
            # The attested imperfect exemplar supplies its stem. The local
            # jussive governor determines its ending, checked again by syntax.
            expected = arabic(imperfect[:-1] + "o" if negative else past)
            if compatible(surface, expected):
                return family
    return None


def _patient_lemma(surface, inventory):
    # Compare every written mark, including marks on long carriers and the
    # definite article. A conflict cannot be silently ignored by lookup.
    for stem, _ in inventory["nouns"]:
        noun = arabic(stem)
        if noun[0] in "تثدذرزسشصضطظلن":
            proposed = "اَل" + noun[0] + "ّ" + noun[1:] + "ُ"
        else:
            proposed = "اَلْ" + noun + "ُ"
        if compatible(surface, proposed):
            return lookup_key(noun)
    return None


def _passive_matches(checked, words, family):
    verb, patient = words[-2:]
    predicate_lemmas = {arabic(row[0]) for row in family["readings"]}
    matches = []
    for clause in checked["clauses"]:
        for analysis in clause["analyses"]:
            if (analysis["frame"] != "verbal_predication" or analysis["force"] != "ASSERT"
                    or not analysis["licensed_syntax"] or analysis["rejected_candidate"]):
                continue
            subjects = [a for a in analysis["assignments"] if a["actual_role"] == "passive_subject"]
            if len(subjects) != 1:
                continue
            subject = subjects[0]
            bound = subject["span"]
            head = subject["head_span"]
            if ([bound["start"], bound["end"]] != patient["utf8_span"]
                    or not head or [head["start"], head["end"]] != verb["utf8_span"]):
                continue
            for claim in analysis["claims"]:
                if (claim["predicate_kind"] == "event" and claim["voice"] == "passive"
                        and claim["predicate"] in predicate_lemmas
                        and claim["positive"] == (len(words) == 2) and claim["tense"] == "past"):
                    matches.append({"lemma": claim["predicate"], "analysis_id": analysis["analysis_id"],
                                    "reading_ids": analysis["reading_ids"], "obligations": analysis["obligations"]})
    return matches


def _witnesses(inventory, names):
    results = {}
    for name in names:
        row = inventory["witnesses"][name]
        start, end = row["utf8_span"]
        with (ROOT / row["path"]).open("rb") as source:
            source.seek(start)
            raw = source.read(end - start)
        if sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("Written passive source excerpt changed")
        results[name] = {**row, "quote": raw.decode().strip()}
    return results


def analyze(text):
    """A conditional text interpretation, with raw source and checker source distinguished."""
    from .text_reading import card

    words = _source_words(text)
    if not words:
        return []
    negative = len(words) == 3
    cue = words[0] if negative else None
    if cue and not compatible(cue["surface"], "لَمْ"):
        return []
    inventory = _inventory()
    verb, patient = words[-2:]
    family = _matching_family(verb["surface"], inventory, negative)
    noun = _patient_lemma(patient["surface"], inventory)
    if not family or not noun:
        return []

    # Unmarked لم is compatible with the interrogative لِمَ. Replay the
    # marked lexical hypothesis; it is never an observation on the parent.
    conditional_cue = bool(cue and "َ" not in lookup_clusters(cue["surface"])[0][1])
    checked_text = text
    if conditional_cue:
        start, end = cue["codepoint_span"]
        checked_text = text[:start] + "لَمْ" + text[end:]
    source_id = "written_passive_hypothesis" if conditional_cue else "written_passive_source"
    report = read_discourse(checked_text, source_id=source_id, lexical_model=_lexicon(inventory))
    checked_words = _source_words(checked_text)
    matches = _passive_matches(report, checked_words, family)
    if not matches:
        return []

    rule_witnesses = ["passive_pattern", "passive_subject", family["sense_witness"]]
    if negative:
        rule_witnesses.append("lam")
    relation = "DENY_PASSIVE" if negative else "ASSERT_PASSIVE"
    masdar = family["masdar"]
    sign = "ينفي" if negative else "يخبر عن"
    reason = f"ضبط «{verb['surface']}» يسند الفعل إلى نائب فاعله «{patient['surface']}»."
    pending = "تبقى هوية المرجع الخارجي والفاعل والآلة والتحقق من الواقعة مفتوحة. تخصّ صفة المتأثّر المعنى الحسّي المفترض."
    if cue:
        reason += f" في قراءة «{cue['surface']}» حرفَ نفي وجزم، يشمل النفي الحدث."
    if conditional_cue:
        pending += " لم تُكتب فتحة اللام؛ تظل القراءة الاستفهامية المحتملة للرسم خارج هذا الوجه."
    mapping = [{"observed": a["surface"], "analyzed": b["surface"], "source_span": a["utf8_span"],
                "analyzed_span": b["utf8_span"]} for a, b in zip(words, checked_words)]
    return [card(
        "source_event_relation",
        "قراءة مشروطة بضبط أداة النفي" if conditional_cue else "إفادة في القراءة المكتوبة المرخّصة",
        f"في القراءة الحسية، النص {sign} حدث {masdar} المتعلّق بالاسم «{patient['surface']}».",
        reason, pending,
        rule_version=SCHEMA, lexical_inventory=INVENTORY, lexical_sha256=INVENTORY_SHA256,
        source_sha256=sha256(text.encode()).hexdigest(), relation=relation,
        event_family=arabic(family["root"]), event_sense_id=SCHEMA + ":" + family["sense_witness"],
        lexical_lemmas=sorted({m["lemma"] for m in matches}),
        patient_key=noun, verb_span=verb["utf8_span"], patient_span=patient["utf8_span"],
        cue_span=cue["utf8_span"] if cue else None, syntax_role="passive_subject",
        semantic_role="affected_in_authored_concrete_reading", scope_mode="source_relative_past",
        operator_reading_conditional=conditional_cue, written_case_observed="ُ" in lookup_clusters(patient["surface"])[-1][1],
        analyzed_source={"id": source_id, "sha256": sha256(checked_text.encode()).hexdigest(), "mapping": mapping},
        owner_analyses=matches, witnesses=_witnesses(inventory, rule_witnesses),
        checker="PYTHON_WRITTEN_FRAME_AND_EXISTING_DISCOURSE_REPLAY",
        all_lexical_senses_established=False, external_referent_established=False, world_truth_established=False,
    )]
