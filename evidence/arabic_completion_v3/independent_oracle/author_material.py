"""Author a bounded independent reference without importing or querying NABT.

Run once before prediction. Existing files are never overwritten. Source
passages and prior audit inputs are read from the pre-change Git tree only.
The teaching corpus is authored morphology, not quotations from the Quran.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = "d791fd7730cde2256dfac8a27687010b392876b3"
SCOPE = "arabic_completion_v3_independent_oracle_v1"


def wire(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def write(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        handle.write(value if isinstance(value, str) else wire(value))


def baseline(path):
    return subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)


def identity(path, raw):
    return {"path": path, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def person(eid, name, gender="masculine", number="singular"):
    return {"id": eid, "name": name, "kind": "person", "gender": gender, "number": number}


entities = [
    person("khalid", "خالد"), person("malik", "مالك"), person("said", "سعيد"),
    person("hind", "هند", "feminine"), person("teacher", "المدرس"),
    person("teachers", "المدرسون", number="plural"),
    {"id": "vessel", "name": "الإناء", "kind": "thing", "gender": "masculine", "number": "singular"},
    {"id": "earth", "name": "الأرض", "kind": "thing", "gender": "feminine", "number": "singular"},
]
contexts = {"base": {"entities": entities, "closed_reference_scope": True}}
contexts["duplicate_teacher"] = deepcopy(contexts["base"])
contexts["duplicate_teacher"]["entities"].append(person("teacher_other", "المدرس"))
contexts["no_teacher"] = deepcopy(contexts["base"])
contexts["no_teacher"]["entities"] = [e for e in entities if e["id"] != "teacher"]
contexts["explicit_active_name"] = deepcopy(contexts["base"])
next(e for e in contexts["explicit_active_name"]["entities"] if e["id"] == "teacher")["name"] = "الْمُدَرِّس"
contexts["unknown_malik_traits"] = deepcopy(contexts["base"])
next(e for e in contexts["unknown_malik_traits"]["entities"] if e["id"] == "malik").update(
    gender="unknown", number="unknown")
for name, fields in (("speaker_malik", {"speaker": "malik"}),
                     ("speaker_hind", {"speaker": "hind"}),
                     ("addressee_malik", {"addressee": "malik"})):
    contexts[name] = {**deepcopy(contexts["base"]), **fields}


def prop(lemma, owner):
    return {"predicate_kind": "property", "predicate": lemma, "args": [owner], "positive": True}


def event(lemma, *args):
    return {"predicate_kind": "event", "predicate": lemma, "args": list(args), "positive": True}


def question(text, status, reason):
    return {"text": text, "expected_status": status, "reason": reason}


cases = []


def case(cid, family, category, text, *, status=None, context="base", profile="base",
         source_rules=(), questions=(), required=(), forbidden=(), obligations=(),
         claims_min=None, claims_max=None, rationale, relations=(), references=(), forces=()):
    row = {"id": cid, "family": family, "category": category,
           "input": {"text": text, "source_id": cid.lower(), "scope": SCOPE,
                     "context_id": context, "lexical_profile": profile},
           "expected": {"document_status": status, "questions": list(questions),
                        "required_claims": list(required), "forbidden_claims": list(forbidden),
                        "obligations": list(obligations), "relations": list(relations),
                        "references": list(references), "clause_forces": list(forces)},
           "source_rules": list(source_rules), "authored_rationale": rationale}
    if claims_min is not None:
        row["expected"]["claims_min"] = claims_min
    if claims_max is not None:
        row["expected"]["claims_max"] = claims_max
    cases.append(row)


case("G01", "geminated_nominal_identity", "positive", "جَاءَ الْمُدَرِّسُ الْمَاهِرُ.",
     status="LICENSED_DISCOURSE", source_rules=["QATR_CASE", "QATR_SUBJECT", "QATR_NAAT"],
     questions=[question("هَلْ جَاءَ الْمُدَرِّسُ الْمَاهِرُ؟", "SUPPORTED", "complete event and adjective"),
                question("هَلْ جَاءَ الْمُدَرِّسُ؟", "UNKNOWN", "published exact qualified-claim policy")],
     required=[event("جَاءَ", "teacher")], forbidden=[prop("مَاهِر", "teacher")], claims_min=1,
     relations=[{"kind": "naat", "head": "الْمُدَرِّسُ", "dependent": "الْمَاهِرُ", "owner": "teacher"}],
     obligations=["SAME_READING_GEMINATION", "NO_CONTEXT_MORPHOLOGY"],
     rationale="The authored noun paradigms independently preserve internal shadda. The entirely unvocalized contextual label supplies an identity, not that morphology.")
case("G02", "geminated_nominal_identity", "positive", "إِنَّ الْمُدَرِّسَ مَاهِرٌ.",
     status="LICENSED_DISCOURSE", source_rules=["QATR_CASE", "QATR_INNA", "SIB_DIRECT_ADJECTIVE"],
     questions=[question("هَلْ الْمُدَرِّسُ مَاهِرٌ؟", "SUPPORTED", "inna's assertion keeps the same subject")],
     required=[prop("مَاهِر", "teacher")], claims_min=1,
     obligations=["INNA_NASB_RAF", "SAME_READING_GEMINATION", "NO_CONTEXT_MORPHOLOGY"],
     rationale="Changing the external case does not delete the internal gemination or turn context identity into declension evidence.")
case("G03", "geminated_nominal_identity", "boundary", "إِنَّ الْمُدَرِّسُ مَاهِرٌ.",
     status="DEFER", source_rules=["QATR_INNA"], claims_max=0,
     questions=[question("هَلْ الْمُدَرِّسُ مَاهِرٌ؟", "DEFER", "visible subject-case conflict is not repaired")],
     obligations=["NO_ACTIVATED_WRONG_CASE", "NO_SILENT_SOURCE_REPAIR"],
     rationale="Within the explicitly heavy-inna, overt-subject fragment, the nominative subject conflicts with the required accusative. No quotation, ellipsis or correction reading is supplied.")
case("G04", "geminated_nominal_identity", "boundary", "الْمُدَرَّسُ مَاهِرٌ.",
     status="DEFER", context="explicit_active_name", source_rules=["QATR_CASE", "ALFIYYA_IDGHAM"], claims_max=0,
     questions=[question("هَلْ الْمُدَرِّسُ مَاهِرٌ؟", "DEFER", "explicit contradictory internal vowel cannot be erased")],
     obligations=["NO_VOCALIZED_CONTEXT_ALIAS", "NO_LEXEME_COLLAPSE"],
     references=[{"surface": "الْمُدَرَّسُ", "forbidden_bound": ["teacher"]}],
     rationale="Both active and passive nominal paradigms are independently supplied. The only teacher label explicitly says مُدَرِّس; it does not identify the distinct vocalized مُدَرَّس reading. This is a declared-name identity test, not a ban on the latter Arabic word.")
case("G05", "geminated_nominal_identity", "ambiguity", "الْمُدَرِّسُ مَاهِرٌ.",
     status="DEFER", context="duplicate_teacher", source_rules=["QATR_CASE"], claims_max=0,
     questions=[question("مَنْ مَاهِرٌ؟", "DEFER", "two indistinguishable declared names cannot be selected arbitrarily")],
     references=[{"surface": "الْمُدَرِّسُ", "required_candidates": ["teacher", "teacher_other"], "bound": None}],
     obligations=["PRESERVE_ALL_REFERENCE_CANDIDATES"],
     rationale="An independently licensed shadda does not disambiguate two identities with the same entirely unvocalized label.")
case("G06", "geminated_nominal_identity", "missing_context", "الْمُدَرِّسُ مَاهِرٌ.",
     status="DEFER", context="no_teacher", source_rules=["QATR_CASE"], claims_max=0,
     questions=[question("هَلْ الْمُدَرِّسُ مَاهِرٌ؟", "DEFER", "lexical evidence does not create a contextual person")],
     obligations=["NO_INVENTED_ENTITY", "LEXICAL_COMPLETENESS_DISTINCT_FROM_REFERENCE"],
     rationale="The same complete lexical paradigms are available as in G01. The missing referent is a separate obligation from recognizing a geminated noun.")

case("N01", "nominal_number_evidence", "positive", "هِنْدٌ مَاهِرَةٌ.",
     status="LICENSED_DISCOURSE", source_rules=["QATR_CASE", "SIB_DIRECT_ADJECTIVE", "QAC_FEATURES"],
     questions=[question("هَلْ هِنْدٌ مَاهِرَةٌ؟", "SUPPORTED", "independently explicit feminine singular adjective")],
     required=[prop("مَاهِرَة", "hind")], claims_min=1,
     obligations=["AGREEMENT_SAME_READING_AND_SUBJECT"],
     rationale="The adjective's FS profile and the subject identity are independently supplied; their roles must be linked in the same predication.")
case("N02", "nominal_number_evidence", "boundary", "هِنْدٌ مَاهِرَتَانِ.",
     status="DEFER", source_rules=["SIB_DIRECT_ADJECTIVE", "QAC_FEATURES"], claims_max=0,
     questions=[question("هَلْ هِنْدٌ مَاهِرَةٌ؟", "DEFER", "dual adjective is not silently singularized")],
     obligations=["NO_ACTIVATED_DIRECT_NUMBER_CONFLICT"],
     rationale="The supplied direct human adjectival regime has an explicit singular subject and dual predicate. Exceptional invariant predicates and quoted names are excluded from this declared fragment.")
case("N03", "nominal_number_evidence", "provenance_probe", "هِنْدٌ مَاهِرَةٌ.",
     profile="mahira_number_omitted", source_rules=["QAC_FEATURES", "SIB_DIRECT_ADJECTIVE"],
     obligations=["NO_MISSING_NUMBER_DEFAULT", "INDEPENDENT_NUMBER_DERIVATION_OR_ABSTENTION", "NO_CONTEXT_MORPHOLOGY"],
     rationale="The only difference from N01 is omission of S in all matching adjective source records. No fixed final status is imposed: a new separately justified morphological law may infer number, but absence alone, context traits, or the desired answer cannot be its evidence. This is a provenance test, not an extra coverage success for deferral.")
case("N04", "nominal_number_evidence", "coverage_challenge", "الْمُدَرِّسُونَ مَاهِرُونَ.",
     status="LICENSED_DISCOURSE", source_rules=["QATR_CASE", "SIB_DIRECT_ADJECTIVE", "QAC_FEATURES"],
     questions=[question("هَلْ الْمُدَرِّسُونَ مَاهِرُونَ؟", "SUPPORTED", "explicit human plural profiles are preserved")],
     required=[prop("مَاهِر", "teachers")], claims_min=1,
     obligations=["NO_PLURAL_TO_SINGULAR_DEFAULT", "AGREEMENT_SAME_READING_AND_SUBJECT"],
     rationale="The source explicitly supplies MP and sound-plural forms for both nouns. This challenges the published singular-human acquisition boundary without treating all Arabic plural agreement as identical.")
case("N05", "nominal_number_evidence", "ambiguity", "خَالِدٌ مَاهِرٌ. مَالِكٌ مَاهِرٌ. هُوَ حَاضِرٌ.",
     status="DEFER", context="unknown_malik_traits", source_rules=["QATR_PRONOUN", "QAC_FEATURES"],
     questions=[question("مَنْ حَاضِرٌ؟", "DEFER", "unknown contextual features do not eliminate a prior referent")],
     required=[prop("مَاهِر", "khalid"), prop("مَاهِر", "malik")],
     forbidden=[prop("حَاضِر", "khalid"), prop("حَاضِر", "malik")],
     references=[{"surface": "هُوَ", "required_candidates": ["khalid", "malik"], "bound": None}],
     obligations=["PRESERVE_POSSIBLE_UNKNOWN_FEATURE_CANDIDATES"],
     rationale="Two named persons are established by preceding clauses. Unknown context traits for one person do not mean contradiction. Neither identity is selected by proximity or completeness of its context row.")
case("N06", "nominal_number_evidence", "provenance_probe", "خَالِدٌ كَرِيمٌ.",
     profile="kariym_cross_pos", source_rules=["QATR_CASE", "QAC_FEATURES", "SIB_DIRECT_ADJECTIVE"],
     obligations=["PRESERVE_N_AND_ADJ_READINGS", "NO_CROSS_READING_TRAIT_COPY", "MORPHOLOGY_BRIDGE_DOES_NOT_GRANT_SENSE"],
     rationale="Two independent nominal paradigms share the written form and lemma: N has only M while ADJ has MS. A case-pattern bridge may be justified, but it must not retag N as ADJ, fill its number from the other reading, import an adjectival meaning, or discard a viable incomplete alternative. A separately justified number derivation remains possible and must be identified.")

case("T01", "tamyiz_scope_and_owner", "positive", "امْتَلَأَ الْإِنَاءُ مَاءً.",
     status="LICENSED_DISCOURSE", source_rules=["QATR_TAMYIZ", "SIB_TAMYIZ"],
     questions=[question("هَلْ امْتَلَأَ الْإِنَاءُ مَاءً؟", "SUPPORTED", "primary exemplified nisba frame"),
                question("هَلْ امْتَلَأَ الْإِنَاءُ؟", "UNKNOWN", "published exact qualification policy, not a general entailment claim")],
     required=[event("امْتَلَأَ", "vessel")], claims_min=1,
     relations=[{"kind": "tamyiz", "dependent": "مَاءً", "governor": "امْتَلَأَ", "target": "الْإِنَاءُ", "owner": "vessel"}],
     obligations=["TAMYIZ_QUALIFIER_SAME_CLAIM_OWNER", "NO_TAMYIZ_AS_DIRECT_OBJECT"],
     rationale="The primary text expressly gives امتلأ الإناء ماء. Water specifies the filling relation; it is not introduced as a separate grounded object identity.")
case("T02", "tamyiz_scope_and_owner", "coverage_challenge", "امْتَلَأَ الْإِنَاءُ عَسَلًا.",
     status="LICENSED_DISCOURSE", source_rules=["QATR_TAMYIZ", "SIB_TAMYIZ"],
     questions=[question("هَلْ امْتَلَأَ الْإِنَاءُ عَسَلًا؟", "SUPPORTED", "authored literal filling-content composition"),
                question("هَلْ امْتَلَأَ الْإِنَاءُ مَاءً؟", "UNKNOWN", "content unit is not replaced by a familiar exemplar")],
     required=[event("امْتَلَأَ", "vessel")], claims_min=1,
     relations=[{"kind": "tamyiz", "dependent": "عَسَلًا", "governor": "امْتَلَأَ", "target": "الْإِنَاءُ", "owner": "vessel"}],
     obligations=["INDEPENDENT_TAMYIZ_FRAME_NOT_ANY_ACCUSATIVE_NOUN", "TAMYIZ_QUALIFIER_SAME_CLAIM_OWNER"],
     rationale="This is an authored extension, not a quoted primary example. Honey is used literally as the filling material; the primary general definition and exemplar motivate the interpretation. The public lexical/context input has no content-medium ontology field, so an acquisition or input-contract debt must be reported if the runtime cannot establish this use independently.")
case("T03", "tamyiz_scope_and_owner", "coverage_challenge", "فَجَّرَ خَالِدٌ الْأَرْضَ عُيُونًا.",
     status="LICENSED_DISCOURSE", source_rules=["QATR_TAMYIZ", "QATR_SUBJECT"],
     questions=[question("هَلْ فَجَّرَ خَالِدٌ الْأَرْضَ عُيُونًا؟", "SUPPORTED", "object-related tamyiz keeps its own target")],
     required=[event("فَجَّرَ", "khalid", "earth")], claims_min=1,
     relations=[{"kind": "tamyiz", "dependent": "عُيُونًا", "governor": "فَجَّرَ", "target": "الْأَرْضَ", "owner": "earth"}],
     obligations=["TAMYIZ_OBJECT_OWNER_NOT_SUBJECT_DEFAULT", "TAMYIZ_QUALIFIER_SAME_CLAIM_OWNER"],
     rationale="The source explicitly cites وفجرنا الأرض عيونا as transformed nisba tamyiz. Replacing the source's first-person plural actor by the independently supplied name is authored composition. The target is the earth, not whichever claim argument comes first.")
case("T04", "tamyiz_scope_and_owner", "boundary", "امْتَلَأَ الْإِنَاءُ الْمَاءَ.",
     status="DEFER", source_rules=["QATR_TAMYIZ", "SIB_TAMYIZ"], claims_max=0,
     questions=[question("هَلْ امْتَلَأَ الْإِنَاءُ مَاءً؟", "DEFER", "definite noun is not silently made indefinite tamyiz")],
     obligations=["NO_ACTIVATED_UNLICENSED_TAMYIZ", "NO_SILENT_SOURCE_REPAIR"],
     rationale="The bounded ordinary nisba-tamyiz analysis requires an indefinite noun. Sibawayhi expressly excludes the corresponding definite-object behavior. Exceptional marked constructions, quotation and corrective ellipsis are outside this probe.")
case("T05", "tamyiz_scope_and_owner", "boundary", "امْتَلَأَ الْإِنَاءُ مَاءٌ.",
     status="DEFER", source_rules=["QATR_TAMYIZ", "QATR_CASE"], claims_max=0,
     questions=[question("هَلْ امْتَلَأَ الْإِنَاءُ مَاءً؟", "DEFER", "visible nominative cannot license the proposed accusative role")],
     obligations=["NO_ACTIVATED_UNLICENSED_TAMYIZ", "NO_ACTIVATED_WRONG_CASE"],
     rationale="The visible ending conflicts with the proposed local tamyiz. No second clause boundary, replacement or unexpressed predication is supplied in the declared fragment.")
case("T06", "tamyiz_scope_and_owner", "positive", "امْتَلَأَ الْإِنَاءُ مَاءً. طَابَ خَالِدٌ نَفْسًا.",
     status="LICENSED_DISCOURSE", source_rules=["QATR_TAMYIZ", "SIB_TAMYIZ", "ALFIYYA_TAMYIZ"],
     questions=[question("هَلْ امْتَلَأَ الْإِنَاءُ مَاءً؟", "SUPPORTED", "first clause qualifier"),
                question("هَلْ طَابَ خَالِدٌ نَفْسًا؟", "SUPPORTED", "second clause qualifier"),
                question("هَلْ طَابَ مَالِكٌ نَفْسًا؟", "UNKNOWN", "known but uninvolved identity is not the owner")],
     required=[event("امْتَلَأَ", "vessel"), event("طَابَ", "khalid")], claims_min=2,
     relations=[{"kind": "tamyiz", "dependent": "مَاءً", "governor": "امْتَلَأَ", "target": "الْإِنَاءُ", "owner": "vessel"},
                {"kind": "tamyiz", "dependent": "نَفْسًا", "governor": "طَابَ", "target": "خَالِدٌ", "owner": "khalid"}],
     obligations=["NO_CROSS_CLAUSE_QUALIFIER_BORROWING", "TAMYIZ_QUALIFIER_SAME_CLAIM_OWNER"],
     rationale="Two independently supported frame families coexist. Neither the tamyiz label nor membership of an entity in the context licenses moving a qualifier or owner to the other clause.")

case("P01", "attached_verb_participants", "positive", "خَالِدٌ مَاهِرٌ. أَكْرَمَهُ مَالِكٌ.",
     status="LICENSED_DISCOURSE", source_rules=["QATR_PRONOUN", "QATR_SUBJECT", "QAC_FEATURES"],
     questions=[question("هَلْ أَكْرَمَ مَالِكٌ خَالِدًا؟", "SUPPORTED", "actor and attached object are independently bound"),
                question("هَلْ أَكْرَمَ خَالِدٌ مَالِكًا؟", "UNKNOWN", "participant order is not reversible")],
     required=[prop("مَاهِر", "khalid"), event("أَكْرَمَ", "malik", "khalid")],
     forbidden=[event("أَكْرَمَ", "khalid", "malik")], claims_min=2,
     references=[{"surface": "هُ", "within": "أَكْرَمَهُ", "required_candidates": ["khalid"], "bound": "khalid"}],
     obligations=["CONNECTED_HOST_SOURCE_CONSERVATION", "SUBJECT_FEATURES_NOT_OBJECT_FEATURES"],
     rationale="The teaching input contains only connected أكرم hosts, not bare occurrences of that verb. The attached third-person object refers to the sole earlier compatible mention under the declared closed-prefix policy; the later explicit subject has a different role.")
case("P02", "attached_verb_participants", "ambiguity", "خَالِدٌ مَاهِرٌ. مَالِكٌ مَاهِرٌ. أَكْرَمَهُ سَعِيدٌ.",
     status="DEFER", source_rules=["QATR_PRONOUN", "QAC_FEATURES"],
     questions=[question("هَلْ أَكْرَمَ سَعِيدٌ خَالِدًا؟", "DEFER", "two earlier compatible object referents remain")],
     required=[prop("مَاهِر", "khalid"), prop("مَاهِر", "malik")],
     forbidden=[event("أَكْرَمَ", "said", "khalid"), event("أَكْرَمَ", "said", "malik")],
     references=[{"surface": "هُ", "within": "أَكْرَمَهُ", "required_candidates": ["khalid", "malik"], "bound": None}],
     obligations=["PRESERVE_ALL_REFERENCE_CANDIDATES", "NO_NEAREST_ANTECEDENT_DEFAULT"],
     rationale="Correct segmentation does not identify the intended antecedent when two prior masculine singular identities survive.")
case("P03", "attached_verb_participants", "missing_context", "أَكْرَمَهُ مَالِكٌ.",
     status="DEFER", source_rules=["QATR_PRONOUN", "QAC_FEATURES"], claims_max=0,
     questions=[question("هَلْ أَكْرَمَ مَالِكٌ خَالِدًا؟", "DEFER", "context's name catalogue is not an antecedent assertion")],
     obligations=["NO_INVENTED_ANTECEDENT", "CONNECTED_HOST_SOURCE_CONSERVATION"],
     rationale="Entities exist in the context, but no prior mention, deictic field or external object binding identifies ه. The first sentence's direct object cannot be filled from a convenient answer.")
same_speaker_text = "خَالِدٌ مَاهِرٌ. أَكْرَمْتُهُ."
case("P04", "attached_verb_participants", "positive", same_speaker_text,
     status="LICENSED_DISCOURSE", context="speaker_malik", source_rules=["QATR_PRONOUN", "QATR_PAST", "QAC_FEATURES"],
     questions=[question("هَلْ أَكْرَمَ مَالِكٌ خَالِدًا؟", "SUPPORTED", "first-person host follows the supplied speaker"),
                question("هَلْ أَكْرَمَ خَالِدٌ مَالِكًا؟", "UNKNOWN", "suffix person must not replace host person")],
     required=[event("أَكْرَمَ", "malik", "khalid")], forbidden=[event("أَكْرَمَ", "khalid", "malik")], claims_min=2,
     obligations=["SUBJECT_FEATURES_NOT_OBJECT_FEATURES", "SPEAKER_CONTEXT_BOUND_REPLAY", "CONNECTED_HOST_SOURCE_CONSERVATION"],
     rationale="The independently annotated host is first person singular while the suffix is third person masculine singular. They are different participants and require different reference premises.")
case("P05", "attached_verb_participants", "positive", same_speaker_text,
     status="LICENSED_DISCOURSE", context="speaker_hind", source_rules=["QATR_PRONOUN", "QATR_PAST", "QAC_FEATURES"],
     questions=[question("هَلْ أَكْرَمَتْ هِنْدٌ خَالِدًا؟", "SUPPORTED", "same first-person text with a different explicitly supplied speaker")],
     required=[event("أَكْرَمَ", "hind", "khalid")], forbidden=[event("أَكْرَمَ", "malik", "khalid")], claims_min=2,
     obligations=["SUBJECT_FEATURES_NOT_OBJECT_FEATURES", "SPEAKER_CONTEXT_BOUND_REPLAY", "CONNECTED_HOST_SOURCE_CONSERVATION"],
     rationale="First-person singular morphology does not specify speaker gender or identity. Exactly the same utterance bytes as P04 have another valid actor under a different explicit context.")
case("P06", "attached_verb_participants", "force_boundary", "خَالِدٌ مَاهِرٌ. أَكْرِمْهُ.",
     status="LICENSED_DISCOURSE", context="addressee_malik", source_rules=["QATR_IMPERATIVE", "QATR_PRONOUN", "QAC_FEATURES"],
     questions=[question("هَلْ أَكْرَمَ مَالِكٌ خَالِدًا؟", "UNKNOWN", "an imperative does not establish compliance")],
     required=[prop("مَاهِر", "khalid")], forbidden=[event("أَكْرَمَ", "malik", "khalid")],
     claims_min=1, claims_max=1, forces=["ASSERT", "COMMAND"],
     obligations=["IMPERATIVE_IS_NOT_ASSERTION", "CONNECTED_HOST_SOURCE_CONSERVATION"],
     rationale="A complete imperative with an attached object must preserve command force and its addressee without projecting a past event. Failure to parse is not a successful force-boundary result.")

write("contexts.json", contexts)
write("cases.json", {"schema": "nabt.arabic-completion-independent-oracle.v1", "baseline_commit": BASE,
      "scope": SCOPE, "case_count": len(cases), "cases": cases,
      "cross_case_checks": [
          {"id": "X01", "cases": ["G01", "G05", "G06"], "kind": "lexical_evidence_does_not_create_or_choose_identity"},
          {"id": "X02", "cases": ["N01", "N03"], "kind": "number_annotation_withdrawal_changes_proof_obligation"},
          {"id": "X03", "cases": ["P04", "P05"], "kind": "identical_text_different_speaker",
           "source_text": same_speaker_text, "required_actors": {"P04": "malik", "P05": "hind"},
           "require_context_changed_certificate_rejection": True}],
      "universal_obligations": ["EXACT_SOURCE_RESTORATION", "PINNED_MODEL_AND_CONTEXT", "PRESERVE_ALL_VIABLE_READINGS",
                                "NO_BORROWED_OCCURRENCE_OR_CLAUSE", "NO_WORLD_TRUTH_PROMOTION", "ERROR_IS_NOT_DEFER"],
      "scope_note": "Directed, manually authored 24-case evidence suite. Two provenance probes have conditional evidence obligations rather than a prescribed final status. No statistical blind-test, universal-completeness, or replacement-of-old-gold claim."})

# Synthetic locations are record identifiers only; these rows are not Quran
# quotations. Full external vowels are observations, but CASE/MOOD and syntactic
# roles are never teaching fields. A context entity ID never appears here.
words = []
lexicon = []


def word(parts):
    words.append(parts)


def nominal(base, pos, root, features, *, article=False, alif=True, extra=""):
    lexicon.append({"lemma_buckwalter": base, "pos": pos, "root_buckwalter": root,
                    "features": features, "extra": extra, "authorship": "authored lexical premise"})
    feat = f"STEM|POS:{pos}|LEM:{base}|ROOT:{root}|{features}" + ("|" + extra if extra else "")
    for ending in ("N", "K", "FA" if alif else "F", "u", "i", "a"):
        word([(base + ending, pos, feat)])
    if article:
        for ending in ("u", "i", "a"):
            word([("Al", "DET", "PREFIX|Al+"), (base + ending, pos, feat)])


for base, pos, root, features, article, alif, extra in (
    ("xaAlid", "PN", "xld", "MS", False, True, ""),
    ("maAlik", "PN", "mlk", "MS", False, True, ""),
    ("saEiyd", "PN", "sEd", "MS", False, True, ""),
    ("hinod", "PN", "hnd", "FS", False, True, ""),
    ("mudar~is", "N", "drs", "MS", True, True, "(II)|ACT|PCPL"),
    ("mudar~as", "N", "drs", "MS", True, True, "(II)|PASS|PCPL"),
    ("maAhir", "ADJ", "mhr", "MS", True, True, ""),
    ("maAhirap", "ADJ", "mhr", "FS", True, False, ""),
    ("HaADir", "ADJ", "HDr", "MS", False, True, ""),
    ("kariym", "ADJ", "krm", "MS", False, True, ""),
    ("<inaA'", "N", "Any", "MS", True, False, ""),
    ("maA'", "N", "mwh", "MS", True, False, ""),
    ("Easal", "N", "Esl", "MS", False, True, ""),
    ("nafos", "N", "nfs", "FS", False, True, ""),
    (">aroD", "N", "ArD", "FS", True, True, ""),
    ("Euyuwn", "N", "Eyn", "FP", False, True, ""),
):
    nominal(base, pos, root, features, article=article, alif=alif, extra=extra)
for base, pos, root in (("mudar~is", "N", "drs"), ("maAhir", "ADJ", "mhr")):
    for form in (base + "uwna", base + "iyna"):
        for prefixed in (False, True):
            part = (form, pos, f"STEM|POS:{pos}|LEM:{base}|ROOT:{root}|MP")
            word([("Al", "DET", "PREFIX|Al+"), part] if prefixed else [part])
for form in ("maAhirataAni", "maAhiratayoni"):
    word([(form, "ADJ", "STEM|POS:ADJ|LEM:maAhirap|ROOT:mhr|FD")])
for form, lemma, root, features in (("jaA'a", "jaA'a", "jy'", "PERF|3MS"),
                                   ("Amotala>a", "Amotala>a", "ml'", "PERF|(VIII)|3MS"),
                                   ("TaAba", "TaAba", "Tyb", "PERF|3MS"),
                                   ("faj~ara", "faj~ara", "fjr", "PERF|(II)|3MS")):
    word([(form, "V", f"STEM|POS:V|LEM:{lemma}|ROOT:{root}|{features}")])
# A direct-object use is independently present for فجّر. It is not inferred
# merely from POS:N on a following word or from a gold role.
word([("faj~ara", "V", "STEM|POS:V|LEM:faj~ara|ROOT:fjr|PERF|(II)|3MS"),
      ("hu", "PRON", "SUFFIX|PRON:3MS")])
# No bare أكرم word is taught in any profile. A whole connected word preserves
# host and suffix observations separately, including their different persons.
for host, aspect, person_features in ((">akorama", "PERF", "3MS"),
                                      (">akoramato", "PERF", "3FS"),
                                      (">akoramotu", "PERF", "1S"),
                                      (">akorimo", "IMPV", "2MS")):
    word([(host, "V", f"STEM|POS:V|LEM:>akorama|ROOT:krm|(IV)|{aspect}|{person_features}"),
          ("hu", "PRON", "SUFFIX|PRON:3MS")])


def corpus_bytes(source_words):
    rows = []
    for index, parts in enumerate(source_words, 1):
        for segment, (form, tag, features) in enumerate(parts, 1):
            rows.append(f"(97:{index}:1:{segment})\t{form}\t{tag}\t{features}")
    return ("# Authored lexical premises; synthetic locations; not Quran quotations.\n"
            "# No CASE/MOOD, target roles, entity IDs, answers or relation owners.\n"
            "LOCATION\tFORM\tTAG\tFEATURES\n" + "\n".join(rows) + "\n")


base_words = deepcopy(words)
weak_words = [[(form, tag, feats.replace("|FS", "|F") if "|LEM:maAhirap|" in feats else feats)
               for form, tag, feats in parts] for parts in words]
cross_words = deepcopy(words)
for ending in ("N", "K", "FA", "u", "i", "a"):
    cross_words.append([("kariym" + ending, "N", "STEM|POS:N|LEM:kariym|ROOT:krm|M")])
profiles = {"base": base_words, "mahira_number_omitted": weak_words, "kariym_cross_pos": cross_words}
profile_rows = {}
for name, source_words in profiles.items():
    filename = "lexical_" + name + ".tsv"
    raw = corpus_bytes(source_words)
    write(filename, raw)
    profile_rows[name] = {"file": filename, "word_count": len(source_words),
                          "segment_count": sum(map(len, source_words)),
                          "sha256": sha256(raw.encode()).hexdigest()}
write("lexical_profiles.json", {"schema": "nabt.authored-morphology-premises.v1", "profiles": profile_rows,
      "lexical_inventory": lexicon,
      "input_scope": "Raw source forms, POS, root, lemma, observed segmentation and morphological profiles only. These synthetic records are supplied premises, not naturally sampled attestations.",
      "number_omission": "N03 removes S from every FS maAhirap record; explicit FD records remain FD. No source-format default is asserted.",
      "cross_pos": "N06 adds independently authored N kariym forms with M and no number; the ADJ paradigm retains MS.",
      "connected_host_condition": "Every >akorama lemma occurrence is inside a multi-segment word with a separately annotated object pronoun. No bare verb word occurs.",
      "semantic_limit": "No factivity, intended pronoun referent, tamyiz role, honey-as-filling-material ontology, answer or contextual identity is taught in these records."})

source_manifest = json.loads(baseline("src/nabt/data/source_evidence/source_manifest.json"))
documents = {d["source_id"]: d for d in source_manifest["documents"]}
source_specs = [
    ("QATR_CASE", "qatr", 42, 50, "The noun/inflected/built distinction. Context identity is not a witness of morphology."),
    ("QATR_CASE_SIGNS", "qatr", 75, 90, "External case signs and explicit exceptions; singular/full declension are premises, not inferred from gender or absence of number."),
    ("QATR_PAST", "qatr", 52, 57, "Past verb with mobile subject pronoun has a distinct ending; does not identify its speaker."),
    ("QATR_IMPERATIVE", "qatr", 58, 63, "Imperative request/form distinction; occurrence of the request does not assert compliance."),
    ("QATR_PRONOUN", "qatr", 122, 128, "Speaker/addressee/absent reference and attached examples. Does not prove an antecedent selection algorithm complete."),
    ("QATR_NOMINAL", "qatr", 152, 164, "Nominal subject and predicate case, with structural alternatives; not a universal adjectival agreement law."),
    ("QATR_INNA", "qatr", 187, 195, "Heavy inna and sisters assign accusative subject/nominative predicate subject to stated conditions; the suite's exact fragment excludes the exceptions."),
    ("QATR_SUBJECT", "qatr", 219, 235, "Subject case and order versus direct object; the excerpt records qualifications and exceptional orders."),
    ("QATR_TAMYIZ", "qatr", 313, 320, "Indefinite explanatory nominal, quantity and nisba examples including filling-water and earth-springs. Not every accusative noun is tamyiz."),
    ("QATR_NAAT", "qatr", 375, 379, "Conditional direct naat agreement, distinct from predicate agreement."),
    ("SIB_DIRECT_ADJECTIVE", "sibawayhi", 4780, 4800, "Direct adjectival predication and human plural/feminine examples, distinguished from adjective-first structures. Not a universal rule for noun predicates, nonhuman plurals, or invariant descriptions."),
    ("SIB_TAMYIZ", "sibawayhi", 2048, 2056, "Filling-water/fat constructions are distinguished from ordinary transitive objects and definite-object behavior."),
    ("ALFIYYA_TAMYIZ", "alfiyya", 469, 476, "Explanatory indefinite tamyiz and طِب نفسا; not independent acquisition of every new verb/content pair."),
    ("ALFIYYA_IDGHAM", "alfiyya", 1277, 1286, "Gemination and its conditioned alternations are structural. This is not a source for erasing all shadda or for an arbitrary nominal alias."),
]
passages = []
for sid, docid, start, end, scope in source_specs:
    path = "src/nabt/data/source_evidence/" + docid + ".txt"
    raw = baseline(path)
    metadata = documents[docid]
    assert sha256(raw).hexdigest() == metadata["sha256"]
    lines = raw.splitlines(keepends=True)
    before = sum(map(len, lines[:start-1]))
    excerpt = b"".join(lines[start-1:end])
    passages.append({"id": sid, "source_id": docid, "source_path": path,
                     "source_sha256": sha256(raw).hexdigest(),
                     "source_url": metadata["pinned_url"], "author": metadata["attribution"]["author_short_name"],
                     "title": metadata["attribution"]["title"], "line_start_1based": start,
                     "line_end_1based_inclusive": end, "byte_start": before,
                     "byte_end_exclusive": before + len(excerpt), "excerpt_sha256": sha256(excerpt).hexdigest(),
                     "raw_excerpt": excerpt.decode(), "interpretive_scope": scope})
write("source_premises.json", {"schema": "nabt.arabic-completion-independent-sources.v1", "baseline_commit": BASE,
      "primary_passages": passages,
      "lexical_spot_checks": [
          {"url": "https://corpus.quran.com/qurandictionary.jsp?q=Any", "access_date_utc": "2026-10-24",
           "scope": "The official root listing places vessels آنية under hamza-nun-ya. This informed the authored إناء root annotation before any material execution or freeze; it does not make the synthetic rows Quran quotations."},
          {"url": "https://corpus.quran.com/qurandictionary.jsp?q=ArD", "access_date_utc": "2026-10-24",
           "scope": "The official root listing identifies أرض with hamza-ra-dad; the teaching representation follows its ArD root convention."}],
      "format_source": {"id": "QAC_FEATURES", "url": "https://corpus.quran.com/documentation/morphologicalfeatures.jsp",
          "access_date_utc": "2026-10-24", "retrieval": "Primary site opened with web retrieval before material freeze; no full HTML hash asserted.",
          "sections": ["Person, Gender and Number", "Verb Features", "Suffixes"],
          "short_exact_quote": "S, D, P singular, dual, plural",
          "scope": "The page defines separate S/D/P features and attached pronoun profiles, and distinguishes subject/object suffix functions. It expressly documents voice/mood defaults but does not state a missing-number-equals-singular default on this page.",
          "limits": "This page alone neither establishes such a number default nor proves it absent from every QAC resource. Authored test records use its notation but are not QAC attestations."},
      "source_transmission": "Exact existing OpenITI byte versions from the pinned pre-change Git tree, with their existing attribution and CC-BY-NC-SA-4.0 corpus-license record. Cleaned text/markup and source selection do not grant new semantic authority or prove print/manuscript identity.",
      "oracle_semantics": [
          "All named identities, traits and participant fields are explicit authored context premises.",
          "The 24 sentences are authored controls/compositions, except where a grammar exemplar is explicitly identified; source texts do not contain these test answers.",
          "The two provenance probes do not demand rejection of a newly justified independent derivation.",
          "UNKNOWN after dropping a qualification is the existing exact qualified-claim query policy, not a denial of ordinary weaker entailments.",
          "Earlier-mention pronoun selection is evaluated within the declared closed-prefix API scope; other Arabic discourse uses need independent context/order licenses.",
          "T02's literal filling-material interpretation is authored linguistic judgment; no hidden semantic type is sent to the runtime.",
          "No lexical trait, semantic frame, assertion truth or unique intended interpretation is established by these source quotations alone."]})

read_paths = ["AGENTS.md", "tools/construction_evaluation.py", "tools/discourse_evaluation.py",
              "tools/question_answer_validation.py", "evidence/constructions/independent_cases_v1.json",
              "evidence/discourse/independent_cases_v1.json",
              "evidence/arabic_coverage/construction_residual_review_v2/review.json",
              "evidence/arabic_coverage/discourse_residual_review_v2/review.json",
              "evidence/arabic_coverage/discourse_residual_review_v1/residual_matrix_v1.json",
              "evidence/arabic_coverage/oracle_audit_v1/question_input_audit.json"]
write("audit_read_set.json", {"schema": "nabt.independent-oracle-read-set.v1", "baseline_commit": BASE,
      "same_premerge_tree_commit": "9f776b598e4f61012e0b6577cd92351ab29eae42",
      "files": [identity(p, baseline(p)) for p in read_paths],
      "disclosure": ["Old gold, retained v2 results/residual diagnoses and existing validator implementation were read before authorship.",
                     "No new runtime implementation or post-change predictions were read before the freeze.",
                     "The parent disclosed a proposed context-name bridge and a proposed morphology-only N/ADJ bridge before freeze. General boundary discussion occurred; no new prediction was supplied.",
                     "The parent requested 24 cases and broad four-family scope. The author did not claim statistical sampling or a secret lexical split."]})

assert len(cases) == 24
assert all(n == 6 for n in Counter(c["family"] for c in cases).values())
assert len({c["id"] for c in cases}) == 24
assert all(c["input"]["context_id"] in contexts and c["input"]["lexical_profile"] in profiles for c in cases)
source_ids = {p["id"] for p in passages} | {"QAC_FEATURES"}
assert all(set(c["source_rules"]) <= source_ids for c in cases)
assert sum(c["category"] == "provenance_probe" for c in cases) == 2
assert cases[-3]["input"]["text"] == cases[-2]["input"]["text"] == same_speaker_text
for source_words in profiles.values():
    for parts in source_words:
        assert all("CASE:" not in feats and "MOOD:" not in feats for _, _, feats in parts)
        if any("LEM:>akorama|" in feats for _, _, feats in parts):
            assert len(parts) == 2 and parts[-1][1:] == ("PRON", "SUFFIX|PRON:3MS")
write("pre_execution_validation.json", {"schema": "nabt.independent-material-validation.v1",
      "created_utc": datetime.now(timezone.utc).isoformat(), "material_only": True,
      "runtime_imported": False, "runtime_predictions_executed": False,
      "case_count": len(cases), "question_count": sum(len(c["expected"]["questions"]) for c in cases),
      "case_categories": dict(Counter(c["category"] for c in cases)),
      "family_counts": dict(Counter(c["family"] for c in cases)),
      "checks": ["unique ids", "six cases per family", "valid source/context/profile references", "two disclosed conditional provenance probes",
                 "all paired speaker input bytes equal", "no CASE/MOOD teaching labels", "no bare akrama training word",
                 "primary excerpt bytes and document hashes match the pre-change tree"],
      "semantic_review_limit": "These are authoring-integrity checks, not parser predictions, validator acceptance tests, or proof that the author's linguistic judgment is infallible."})
