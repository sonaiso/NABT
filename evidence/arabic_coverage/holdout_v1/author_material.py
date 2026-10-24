"""Create independently authored holdout material without importing NABT.

This is authoring provenance, not a runtime oracle learned from predictions.
Do not rerun to amend frozen material; corrections require a new version.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = "f0064f0a4baab3cc816087a322aabc0c8fbb2d19"


def write_json(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


entities = [
    {"id": "nasser", "name": "ناصر", "gender": "masculine", "number": "singular", "kind": "person"},
    {"id": "zayd", "name": "زيد", "gender": "masculine", "number": "singular", "kind": "person"},
    {"id": "hind", "name": "هند", "gender": "feminine", "number": "singular", "kind": "person"},
    {"id": "house", "name": "بيت", "gender": "masculine", "number": "singular", "kind": "place"},
    {"id": "home", "name": "دار", "gender": "feminine", "number": "singular", "kind": "place"},
]
contexts = {"base": {"entities": entities, "closed_reference_scope": True}}
for name, extra in (
    ("speaker_nasser", {"speaker": "nasser"}),
    ("speaker_zayd", {"speaker": "zayd"}),
    ("open_reference", {"closed_reference_scope": False}),
):
    contexts[name] = {**deepcopy(contexts["base"]), **extra}
contexts["duplicate_name"] = deepcopy(contexts["base"])
contexts["duplicate_name"]["entities"].append({
    "id": "nasser_other", "name": "ناصر", "gender": "masculine", "number": "singular", "kind": "person"})
contexts["no_owner_identity"] = deepcopy(contexts["base"])
contexts["no_owner_identity"]["entities"] = [row for row in entities if row["id"] != "zayd"]


def question(text, status, label, **extra):
    return {"text": text, "expected_status": status, "label": label, **extra}


def prop(lemma, owner, positive=True):
    return {"predicate": lemma, "predicate_kind": "property", "args": [owner], "positive": positive}


def event(lemma, *args):
    return {"predicate": lemma, "predicate_kind": "event", "args": list(args), "positive": True}


cases = []


def case(cid, category, focus, text, questions, *, rationale, rules, context="base",
         licensed=True, claims_min=None, claims_max=None, required=(), forbidden=(), forces=()):
    row = {"id": cid, "category": category, "focus": focus, "text": text,
           "context": context, "expected_document_status": "LICENSED_DISCOURSE" if licensed else "DEFER",
           "rationale": rationale, "source_rules": rules, "questions": questions,
           "required_claims": list(required), "forbidden_claims": list(forbidden)}
    if claims_min is not None:
        row["claims_min"] = claims_min
    if claims_max is not None:
        row["claims_max"] = claims_max
    if forces:
        row["expected_clause_forces"] = list(forces)
    cases.append(row)


case("H01", "positive", "independent lexical control", "نَاصِرٌ حَكِيمٌ.", [
    question("هَلْ نَاصِرٌ حَكِيمٌ؟", "SUPPORTED", "named owner"),
    question("هَلْ زَيْدٌ حَكِيمٌ؟", "UNKNOWN", "unrelated identity")],
    rationale="The explicit noun predicate belongs to the named subject only.",
    rules=["nominal_predication", "predicate_adjectival_agreement"], claims_min=1,
    required=[prop("حَكِيم", "nasser")], forbidden=[prop("حَكِيم", "zayd")])
case("H02", "positive", "ordered subject and object", "ضَرَبَ نَاصِرٌ زَيْدًا.", [
    question("هَلْ ضَرَبَ نَاصِرٌ زَيْدًا؟", "SUPPORTED", "ordered arguments"),
    question("هَلْ ضَرَبَ زَيْدٌ نَاصِرًا؟", "UNKNOWN", "argument reversal")],
    rationale="An active event assigns different subject and object positions; reversing them is unsupported.",
    rules=["active_subject"], claims_min=1, required=[event("ضَرَبَ", "nasser", "zayd")],
    forbidden=[event("ضَرَبَ", "zayd", "nasser")])
case("H03", "positive", "PP with idafa", "كَتَبَ نَاصِرٌ فِي بَيْتِ زَيْدٍ.", [
    question("هَلْ كَتَبَ نَاصِرٌ فِي بَيْتِ زَيْدٍ؟", "SUPPORTED", "complete PP and idafa"),
    question("هَلْ كَتَبَ نَاصِرٌ؟", "UNKNOWN", "place qualification retained")],
    rationale="The preposition governs the head, idafa governs its dependent, and the complete place restriction is retained.",
    rules=["idafa_chain", "temporal_spatial_attachment"], claims_min=1)
case("H04", "positive", "PP idafa adjective on head", "كَتَبَ نَاصِرٌ فِي دَارِ زَيْدٍ الكَبِيرَةِ.", [
    question("هَلْ كَتَبَ نَاصِرٌ فِي دَارِ زَيْدٍ الكَبِيرَةِ؟", "SUPPORTED", "gender identifies adjective head"),
    question("هَلْ كَتَبَ نَاصِرٌ فِي دَارِ زَيْدٍ؟", "UNKNOWN", "adjective qualification retained")],
    rationale="In the declared direct adjective regime, feminine singular الكبيرة agrees with دار and not masculine زيد.",
    rules=["idafa_chain", "naat_agreement", "temporal_spatial_attachment"], claims_min=1)
case("H05", "positive", "PP idafa adjective on dependent", "كَتَبَ نَاصِرٌ فِي دَارِ زَيْدٍ الكَرِيمِ.", [
    question("هَلْ كَتَبَ نَاصِرٌ فِي دَارِ زَيْدٍ الكَرِيمِ؟", "SUPPORTED", "masculine dependent adjective"),
    question("هَلْ نَاصِرٌ كَرِيمٌ؟", "UNKNOWN", "no subject contamination")],
    rationale="The masculine genitive adjective can describe زيد; it cannot describe the feminine دار or nominative ناصر in this direct regime.",
    rules=["idafa_chain", "naat_agreement", "temporal_spatial_attachment"], claims_min=1,
    forbidden=[prop("كَرِيم", "nasser")])
case("H06", "ambiguity", "PP idafa ambiguous adjective", "كَتَبَ نَاصِرٌ فِي بَيْتِ زَيْدٍ الكَبِيرِ.", [
    question("هَلْ كَتَبَ نَاصِرٌ فِي بَيْتِ زَيْدٍ الكَبِيرِ؟", "DEFER", "unresolved attachment")],
    rationale="Both بيت and زيد are masculine singular genitives and definite in the idafa. No context field licenses choosing the adjective attachment.",
    rules=["idafa_chain", "naat_agreement"], licensed=False, claims_max=0)
case("H07", "boundary", "PP overt case conflict", "كَتَبَ نَاصِرٌ فِي بَيْتُ زَيْدٍ.", [
    question("هَلْ كَتَبَ نَاصِرٌ فِي بَيْتِ زَيْدٍ؟", "DEFER", "no silent vowel repair")],
    rationale="The visible nominative head conflicts with the direct preposition-governed reading; no alternate corrective premise is supplied.",
    rules=["idafa_chain"], licensed=False, claims_max=0)
case("H08", "boundary", "PP idafa tanwin conflict", "كَتَبَ نَاصِرٌ فِي بَيْتٍ زَيْدٍ.", [
    question("هَلْ كَتَبَ نَاصِرٌ فِي بَيْتِ زَيْدٍ؟", "DEFER", "no tanwin deletion")],
    rationale="An overtly nunated semantic-idafa head cannot be accepted by treating visible tanwin as absent.",
    rules=["idafa_chain"], licensed=False, claims_max=0)
case("H09", "positive", "hal and time", "جَاءَ نَاصِرٌ رَاكِبًا اليَوْمَ.", [
    question("هَلْ جَاءَ نَاصِرٌ رَاكِبًا اليَوْمَ؟", "SUPPORTED", "event circumstance and time"),
    question("هَلْ نَاصِرٌ رَاكِبٌ؟", "UNKNOWN", "no enduring unqualified property"),
    question("هَلْ جَاءَ نَاصِرٌ رَاكِبًا أَمْسِ؟", "UNKNOWN", "different time")],
    rationale="The circumstantial rider description is tied to the arrival event and its temporal restriction.",
    rules=["hal_attachment", "temporal_spatial_attachment"], claims_min=1,
    forbidden=[{**prop("رَاكِب", "nasser"), "time": [], "place": [], "restriction": []}])
case("H10", "positive", "hal subject disambiguated", "ضَرَبَ نَاصِرٌ هِنْدًا رَاكِبًا اليَوْمَ.", [
    question("هَلْ ضَرَبَ نَاصِرٌ هِنْدًا رَاكِبًا اليَوْمَ؟", "SUPPORTED", "masculine subject owns hal"),
    question("هَلْ هِنْدٌ رَاكِبَةٌ؟", "UNKNOWN", "no hal on feminine object")],
    rationale="The masculine hal agrees with the male subject, while the female object is excluded by explicit gender evidence.",
    rules=["active_subject", "hal_attachment"], claims_min=1, forbidden=[prop("رَاكِبَة", "hind")])
case("H11", "positive", "hal object disambiguated", "ضَرَبَتْ هِنْدٌ نَاصِرًا رَاكِبًا اليَوْمَ.", [
    question("هَلْ ضَرَبَتْ هِنْدٌ نَاصِرًا رَاكِبًا اليَوْمَ؟", "SUPPORTED", "masculine object owns hal"),
    question("هَلْ هِنْدٌ رَاكِبَةٌ؟", "UNKNOWN", "no subject promotion")],
    rationale="The male object is the compatible owner of the masculine hal; linear proximity to the verb does not make the female subject its owner.",
    rules=["active_subject", "hal_attachment"], claims_min=1, forbidden=[prop("رَاكِبَة", "hind")])
case("H12", "ambiguity", "hal competing owners", "ضَرَبَ نَاصِرٌ زَيْدًا رَاكِبًا اليَوْمَ.", [
    question("هَلْ ضَرَبَ نَاصِرٌ زَيْدًا رَاكِبًا اليَوْمَ؟", "DEFER", "same gender does not choose an owner")],
    rationale="Both named male participants can own the singular masculine hal. The context supplies no attachment choice.",
    rules=["active_subject", "hal_attachment"], licensed=False, claims_max=0)
case("H13", "positive", "semantic emphasis plus time", "جَاءَ نَاصِرٌ نَفْسُهُ اليَوْمَ.", [
    question("هَلْ جَاءَ نَاصِرٌ نَفْسُهُ اليَوْمَ؟", "SUPPORTED", "own matching emphatic pronoun"),
    question("هَلْ جَاءَ نَاصِرٌ نَفْسُهُ أَمْسِ؟", "UNKNOWN", "emphasis does not erase time")],
    rationale="Nafs carries an attached masculine singular pronoun matching the emphasized named subject; the event keeps its time.",
    rules=["tawkeed_reference", "temporal_spatial_attachment"], claims_min=1)
case("H14", "positive", "literal repetition plus time", "جَاءَ نَاصِرٌ نَاصِرٌ أَمْسِ.", [
    question("هَلْ جَاءَ نَاصِرٌ نَاصِرٌ أَمْسِ؟", "SUPPORTED", "same reference repetition"),
    question("هَلْ جَاءَ زَيْدٌ زَيْدٌ أَمْسِ؟", "UNKNOWN", "no identity substitution")],
    rationale="Literal emphatic repetition is restricted to the same independently resolved person and event.",
    rules=["tawkeed_reference", "temporal_spatial_attachment"], claims_min=1)
case("H15", "boundary", "mismatching emphatic suffix", "جَاءَ نَاصِرٌ نَفْسُهَا اليَوْمَ.", [
    question("هَلْ جَاءَ نَاصِرٌ نَفْسُهُ اليَوْمَ؟", "DEFER", "no suffix repair")],
    rationale="The feminine attached pronoun is not a matching emphasis witness for the male subject.",
    rules=["tawkeed_reference"], licensed=False, claims_max=0)
case("H16", "positive", "epistemic embedding", "ظَنَّ نَاصِرٌ زَيْدًا حَكِيمًا.", [
    question("هَلْ ظَنَّ نَاصِرٌ زَيْدًا حَكِيمًا؟", "SUPPORTED", "attributed belief"),
    question("هَلْ زَيْدٌ حَكِيمٌ؟", "UNKNOWN", "no embedded assertion"),
    question("هَلْ لَيْسَ زَيْدٌ حَكِيمًا؟", "UNKNOWN", "no embedded negation")],
    rationale="The belief is attributed to ناصر. Neither the positive nor the negative unqualified embedded property is established.",
    rules=["zanna_sisters"], claims_min=1, forbidden=[prop("حَكِيم", "zayd"), prop("حَكِيم", "zayd", False)])
case("H17", "coverage_challenge", "matrix negation of belief", "مَا ظَنَّ نَاصِرٌ زَيْدًا حَكِيمًا.", [
    question("هَلْ مَا ظَنَّ نَاصِرٌ زَيْدًا حَكِيمًا؟", "SUPPORTED", "negative matrix claim"),
    question("هَلْ ظَنَّ نَاصِرٌ زَيْدًا حَكِيمًا؟", "REFUTED", "opposite matrix polarity"),
    question("هَلْ زَيْدٌ حَكِيمٌ؟", "UNKNOWN", "negated belief is not positive embedded truth"),
    question("هَلْ لَيْسَ زَيْدٌ حَكِيمًا؟", "UNKNOWN", "negated belief is not belief in negation")],
    rationale="This deliberately requests a broader coverage frame: matrix ما-negation denies the attributed belief and does not move negation into its content. Scope is an authored semantic premise, not a theorem extracted from one cited line.",
    rules=["zanna_sisters", "laysa_negation"], claims_min=1,
    forbidden=[prop("حَكِيم", "zayd"), prop("حَكِيم", "zayd", False)])
case("H18", "positive", "signed negative property", "لَيْسَ نَاصِرٌ حَكِيمًا.", [
    question("هَلْ لَيْسَ نَاصِرٌ حَكِيمًا؟", "SUPPORTED", "negative claim"),
    question("هَلْ نَاصِرٌ حَكِيمٌ؟", "REFUTED", "explicit opposite"),
    question("مَنْ حَكِيمٌ؟", "UNKNOWN", "variable needs positive evidence")],
    rationale="A negative property can refute its exact polar opposite, while a variable question still lacks a positive witness.",
    rules=["laysa_negation", "wh_subject"], claims_min=1,
    required=[prop("حَكِيم", "nasser", False)], forbidden=[prop("حَكِيم", "nasser")])
case("H19", "positive", "approximation with time", "كَادَ نَاصِرٌ يَكْتُبُ اليَوْمَ.", [
    question("هَلْ كَادَ نَاصِرٌ يَكْتُبُ اليَوْمَ؟", "SUPPORTED", "near event remains scoped"),
    question("هَلْ يَكْتُبُ نَاصِرٌ اليَوْمَ؟", "UNKNOWN", "no realized embedded event")],
    rationale="The approximation frame retains its embedded event and time without affirming that writing occurs.",
    rules=["kada_complement", "temporal_spatial_attachment"], claims_min=1,
    forbidden=[event("كَتَبَ", "nasser")])
case("H20", "positive", "future qualification", "سَوْفَ يَكُونُ نَاصِرٌ حَكِيمًا.", [
    question("هَلْ سَوْفَ يَكُونُ نَاصِرٌ حَكِيمًا؟", "SUPPORTED", "future property"),
    question("هَلْ نَاصِرٌ حَكِيمٌ؟", "UNKNOWN", "no future to present erasure")],
    rationale="An explicit future operator is retained; it is not a current unqualified property assertion.",
    rules=["kana_sisters", "tense_aspect"], claims_min=1)
for cid, owner, other, context in (("H21", "نَاصِرٌ", "زَيْدٌ", "speaker_nasser"), ("H22", "زَيْدٌ", "نَاصِرٌ", "speaker_zayd")):
    eid = "nasser" if context == "speaker_nasser" else "zayd"
    case(cid, "positive", "same utterance different speaker", "أَنَا حَكِيمٌ.", [
        question(f"هَلْ {owner} حَكِيمٌ؟", "SUPPORTED", "explicit speaker"),
        question(f"هَلْ {other} حَكِيمٌ؟", "UNKNOWN", "other person not substituted")],
        rationale="Identical utterance bytes denote a different owner when the independently supplied speaker identity changes.",
        rules=["independent_pronouns", "predicate_adjectival_agreement"], context=context,
        claims_min=1, required=[prop("حَكِيم", eid)])
case("H23", "ambiguity", "speaker absent", "أَنَا حَكِيمٌ.", [
    question("هَلْ نَاصِرٌ حَكِيمٌ؟", "DEFER", "speaker cannot be guessed")],
    rationale="Neither the pronoun form nor a list of compatible people establishes who is speaking.",
    rules=["independent_pronouns"], licensed=False, claims_max=0)
case("H24", "positive", "one closed antecedent", "نَاصِرٌ كَرِيمٌ. هُوَ حَكِيمٌ.", [
    question("هَلْ نَاصِرٌ حَكِيمٌ؟", "SUPPORTED", "single compatible closed antecedent")],
    rationale="The closed domain and complete source prefix leave one licensed masculine singular antecedent.",
    rules=["independent_pronouns", "nominal_predication"], claims_min=2,
    required=[prop("حَكِيم", "nasser")])
case("H25", "ambiguity", "two closed antecedents", "نَاصِرٌ كَرِيمٌ. زَيْدٌ كَرِيمٌ. هُوَ حَكِيمٌ.", [
    question("هَلْ نَاصِرٌ حَكِيمٌ؟", "DEFER", "no first antecedent selection"),
    question("هَلْ زَيْدٌ حَكِيمٌ؟", "DEFER", "no nearest antecedent selection")],
    rationale="Closing the reference domain does not make two compatible antecedents unique. Earlier licensed claims may remain, but no new حكيم claim is grounded.",
    rules=["independent_pronouns"], licensed=False, forbidden=[{"predicate": "حَكِيم"}])
case("H26", "ambiguity", "open reference domain", "نَاصِرٌ كَرِيمٌ. هُوَ حَكِيمٌ.", [
    question("هَلْ نَاصِرٌ حَكِيمٌ؟", "DEFER", "one observed antecedent is not a closed domain")],
    rationale="An explicit open reference scope leaves unobserved referents possible.",
    rules=["independent_pronouns"], context="open_reference", licensed=False,
    forbidden=[{"predicate": "حَكِيم"}])
case("H27", "ambiguity", "duplicate name identities", "نَاصِرٌ حَكِيمٌ.", [
    question("هَلْ نَاصِرٌ حَكِيمٌ؟", "DEFER", "a name is not a unique person")],
    rationale="Two distinct context identities share the same name and features; string equality does not choose one.",
    rules=["nominal_predication"], context="duplicate_name", licensed=False, claims_max=0)
case("H28", "positive", "property does not move from subject to object", "نَاصِرٌ حَكِيمٌ. ضَرَبَ نَاصِرٌ زَيْدًا.", [
    question("هَلْ نَاصِرٌ حَكِيمٌ؟", "SUPPORTED", "original property owner"),
    question("هَلْ زَيْدٌ حَكِيمٌ؟", "UNKNOWN", "object not contaminated")],
    rationale="The event's second participant does not inherit a separate property of the first.",
    rules=["nominal_predication", "active_subject"], claims_min=2,
    required=[prop("حَكِيم", "nasser")], forbidden=[prop("حَكِيم", "zayd")])
case("H29", "positive", "property does not move from object to subject", "زَيْدٌ حَكِيمٌ. ضَرَبَ نَاصِرٌ زَيْدًا.", [
    question("هَلْ زَيْدٌ حَكِيمٌ؟", "SUPPORTED", "original property owner"),
    question("هَلْ نَاصِرٌ حَكِيمٌ؟", "UNKNOWN", "subject not contaminated")],
    rationale="The event's first participant does not inherit a separate property of the second.",
    rules=["nominal_predication", "active_subject"], claims_min=2,
    required=[prop("حَكِيم", "zayd")], forbidden=[prop("حَكِيم", "nasser")])
for cid, text, force, focus, rule in (
    ("H30", "هَلْ نَاصِرٌ حَكِيمٌ؟", "QUESTION", "explicit question force", "polar_interrogative"),
    ("H31", "نَاصِرٌ حَكِيمٌ؟", "QUESTION", "punctuation question force", "force_nonassertive"),
    ("H32", "لَيْتَ نَاصِرًا حَكِيمٌ.", "WISH", "wish force", "inna_sisters"),
    ("H33", "لَعَلَّ نَاصِرًا حَكِيمٌ.", "HOPE", "hope force", "inna_sisters"),
    ("H34", "«نَاصِرٌ حَكِيمٌ».", "QUOTED", "quoted mention", "force_nonassertive"),
):
    case(cid, "force_boundary", focus, text, [
        question("هَلْ نَاصِرٌ حَكِيمٌ؟", "UNKNOWN", "nonassertive source gives no fact")],
        rationale="The public written-language force policy does not promote this nonassertive or quoted content into a factual claim.",
        rules=[rule], claims_max=0, forces=[force])
case("H35", "positive", "separate coordinated owners", "نَاصِرٌ حَكِيمٌ وَ زَيْدٌ كَرِيمٌ.", [
    question("هَلْ نَاصِرٌ حَكِيمٌ؟", "SUPPORTED", "first conjunct"),
    question("هَلْ زَيْدٌ كَرِيمٌ؟", "SUPPORTED", "second conjunct"),
    question("هَلْ زَيْدٌ حَكِيمٌ؟", "UNKNOWN", "no cross conjunct owner borrowing")],
    rationale="Independent complete affirmative conjuncts preserve their distinct property owners.",
    rules=["clause_conjunction", "nominal_predication"], claims_min=2,
    required=[prop("حَكِيم", "nasser"), prop("كَرِيم", "zayd")], forbidden=[prop("حَكِيم", "zayd")])
case("H36", "boundary", "idafa owner identity absent", "كَتَبَ نَاصِرٌ فِي بَيْتِ زَيْدٍ.", [
    question("هَلْ كَتَبَ نَاصِرٌ فِي بَيْتِ زَيْدٍ؟", "DEFER", "no referent invented from a lexical name")],
    rationale="The name's lexical morphology does not create a context identity for the possessor.",
    rules=["idafa_chain"], context="no_owner_identity", licensed=False, claims_max=0)

write_json("cases.json", {"schema": "nabt.independent-arabic-holdout.v1", "baseline_commit": BASE,
    "authoring": "independent agent; no pending runtime inspection or prediction probes before freeze",
    "cases": cases,
    "cross_case_checks": [{"id": "X01", "kind": "same_text_different_speaker",
        "cases": ["H21", "H22", "H23"], "text": "أَنَا حَكِيمٌ.",
        "required_positive_owners": {"H21": "nasser", "H22": "zayd"},
        "absent_speaker_case": "H23",
        "argument": "The same bytes plus two permissible speaker contexts yield different referents. A function of these utterance bytes alone cannot recover both intended owners uniquely; absence of context must remain underspecified."}]})
write_json("contexts.json", contexts)

# These source rows attest only lexical morphology and segmentation. No case,
# mood, dependency, attachment, reference, role, force or question label enters
# the runtime input. All synthetic verse locations are independently named.
rows = []
verse = 0
lexical_inventory = []


def word(parts):
    global verse
    verse += 1
    for segment, (form, tag, features) in enumerate(parts, 1):
        rows.append(f"(97:{verse}:1:{segment})\t{form}\t{tag}\t{features}")


def nominal(base, tag, root, profile, *, article=False, alif=True):
    lexical_inventory.append({"lemma_buckwalter": base, "pos": tag, "root_buckwalter": root, "profile": profile})
    features = f"STEM|POS:{tag}|LEM:{base}|ROOT:{root}|{profile}"
    endings = ("N", "K", "FA" if alif else "F", "u", "i", "a")
    for ending in endings:
        word([(base + ending, tag, features)])
    if article:
        for ending in ("u", "i", "a"):
            word([("Al", "DET", "PREFIX|Al+"), (base + ending, tag, features)])


for base, tag, root, profile, article, alif in (
    ("naASir", "PN", "nSr", "MS", False, True),
    ("zayod", "PN", "zyd", "MS", False, True),
    ("hinod", "PN", "hnd", "FS", False, True),
    ("bayot", "N", "byt", "MS", True, True),
    ("daAr", "N", "dwr", "FS", True, True),
    ("Hakiym", "ADJ", "Hkm", "MS", True, True),
    ("kariym", "ADJ", "krm", "MS", True, True),
    ("kabiyr", "ADJ", "kbr", "MS", True, True),
    ("kabiyrap", "ADJ", "kbr", "FS", True, False),
    ("raAkib", "ADJ", "rkb", "MS", True, True),
    ("raAkibap", "ADJ", "rkb", "FS", True, False),
    ("nafos", "N", "nfs", "FS", False, True),
):
    nominal(base, tag, root, profile, article=article, alif=alif)
for form, lemma, root, aspect, profile in (
    ("kataba", "kataba", "ktb", "PERF", "3MS"),
    ("yakotubu", "kataba", "ktb", "IMPF", "3MS"),
    ("Daraba", "Daraba", "Drb", "PERF", "3MS"),
    ("Darabato", "Daraba", "Drb", "PERF", "3FS"),
    ("yaDoribu", "Daraba", "Drb", "IMPF", "3MS"),
    ("jaA'a", "jaA'a", "jy'", "PERF", "3MS"),
    ("jaA'ato", "jaA'a", "jy'", "PERF", "3FS"),
    ("Zan~a", "Zan~a", "Znn", "PERF", "3MS"),
    ("yaZun~u", "Zan~a", "Znn", "IMPF", "3MS"),
    ("kaAda", "kaAda", "kwd", "PERF", "3MS"),
    ("yakuwnu", "kaAna", "kwn", "IMPF", "3MS"),
):
    word([(form, "V", f"STEM|POS:V|{aspect}|LEM:{lemma}|ROOT:{root}|{profile}")])
# Independent complete object hosts and attached words make transitivity a
# lexical premise. Their suffix referents are not test answers.
for form, root, aspect, profile in (("Daraba", "Drb", "PERF", "3MS"), ("Darabato", "Drb", "PERF", "3FS"), ("yaDoribu", "Drb", "IMPF", "3MS")):
    word([(form, "V", f"STEM|POS:V|{aspect}|LEM:Daraba|ROOT:{root}|{profile}"),
          ("ka", "PRON", "SUFFIX|PRON:2MS")])
for ending in ("u", "i", "a"):
    for suffix, profile in (("hu", "3MS"), ("haA", "3FS")):
        word([("nafos" + ending, "N", "STEM|POS:N|LEM:nafos|ROOT:nfs|FS"),
              (suffix, "PRON", "SUFFIX|PRON:" + profile)])
word([("Al", "DET", "PREFIX|Al+"), ("yawoma", "T", "STEM|POS:T|LEM:yawom|ROOT:ywm|M")])
word([(">amosi", "T", "STEM|POS:T|LEM:>amos|ROOT:'ms|M")])
with (OUT / "lexical_premises.tsv").open("x", encoding="utf-8") as handle:
    handle.write("# Authored lexical premises, not Quran quotations or a natural corpus.\n")
    handle.write("# No CASE/MOOD, test roles, attachment labels, entity IDs or answers.\n")
    handle.write("LOCATION\tFORM\tTAG\tFEATURES\n" + "\n".join(rows) + "\n")

needed = {rule for row in cases for rule in row["source_rules"]}
source_records = []
for policy_name in ("construction", "discourse"):
    path = f"src/nabt/data/source_evidence/{policy_name}_policy.json"
    raw = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)
    policy = json.loads(raw)
    for entry in policy["passages"]:
        if entry["rule"] in needed:
            source_records.append({"policy_path": path, "policy_sha256": sha256(raw).hexdigest(),
                "policy_id": policy["policy_id"], **{k: entry[k] for k in (
                    "rule", "source_id", "source_commit", "source_path", "source_sha256",
                    "line_start", "line_end", "start", "end", "span_sha256", "premise_scope")}})
write_json("source_premises.json", {"schema": "nabt.independent-arabic-holdout-sources.v1",
    "baseline_commit": BASE, "primary_passages": source_records,
    "lexical_inventory": lexical_inventory, "authored_word_count": verse,
    "lexical_record_count": len(rows),
    "source_limit": "Pinned primary source rules motivate conditional grammar obligations. They do not prove arbitrary sentence acquisition, the author's semantic oracle, Python behavior, or world truth.",
    "explicit_semantic_premises": [
        "Context entities, their names, grammatical traits, speaker and reference-scope closure are supplied premises, never discovered world facts.",
        "In H06 and H12 both attachment candidates satisfy the declared agreement constraints; no lexical or context premise distinguishes their attachment.",
        "H17 is a coverage challenge for ordinary matrix ما-negation. No claim is made that the cited ليس window is itself a proof for every ما use.",
        "UNKNOWN for qualification erasure follows the published NABT query contract. It is not a general assertion that natural-language entailment cannot weaken descriptions.",
        "No claim is made that every natural use of a bare noun property describes a permanent trait; the hal controls prohibit unsupported unqualified projection under this contract.",
        "Punctuation-only questions and quotation are evaluated under the published written-language force convention.",
        "The two-speaker counterexample establishes underdetermination from utterance bytes alone, not undecidability of every linguistic inference."
    ]})

print(json.dumps({"cases": len(cases), "questions": sum(len(x["questions"]) for x in cases),
                  "word_count": verse, "record_count": len(rows)}, sort_keys=True))
