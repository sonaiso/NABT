"""A bounded Arabic reader joining morphology, reference and qualified claims.

Every result is conditional on the original text, the declared grammar, raw
lexical training sources and explicit discourse premises. Alternatives stay
correlated inside whole analyses. This module is not an unrestricted parser,
and neither a surface suffix nor a context label is a dependency answer.
"""

from copy import deepcopy
from dataclasses import asdict
from itertools import product

from .corpus_evidence import lexical_index, lookup_clusters, lookup_key, template_matches
from .discourse_adverbs import adverb_candidates
from .discourse_context import (identity, wire, read_context, resolve_reference,
                                form_matches, profile_compatibility)
from .discourse_laws import (LAW_ID, EXPECTED_TABLE_SHA256, assertion_allowed,
                             coordination_projection, replay_discourse_policy,
                             role_case)
from .errors import NabtError, resource_limit
from .inflection import relation_candidate, sign_candidates
from .inflection_reader import _read_run, _surface_accepts, replay_inflection_policy
from .text_ir import span_dict
from .word_reader import _scan, _source, _span
from .construction_sources import replay_construction_policy
from .construction_laws import (LAW_ID as CONSTRUCTION_LAW_ID,
    EXPECTED_TABLE_SHA256 as CONSTRUCTION_TABLE_SHA256, ROLES as CONSTRUCTION_ROLES,
    role_case as construction_role_case, predicate_agreement_status)

LANGUAGE_ID = "nabt.arabic-discourse-frames.v5"
READER_VERSION = "nabt.discourse-reader.v5"
MAX_ANALYSES = 128
MAX_CLAUSES = 32
_UNSET = object()
_CASE_NAMES = ("nasb", "raf", "jarr", "jazm")

# These are grammatical paradigms anchored in the replayed source policy,
# not a list of answers about arbitrary content words or their referents.
_DEMONSTRATIVES = (
    ("هَذَا", "masculine", "singular", "built", ()),
    ("هَذِهِ", "feminine", "singular", "built", ()),
    ("ذَلِكَ", "masculine", "singular", "built", ()),
    ("تِلْكَ", "feminine", "singular", "built", ()),
    ("هَؤُلَاءِ", None, "plural", "built", ()),
    ("أُولَئِكَ", None, "plural", "built", ()),
    ("هَذَانِ", "masculine", "dual", "inflected", (2,)),
    ("هَذَيْنِ", "masculine", "dual", "inflected", (2,)),
    ("هَاتَانِ", "feminine", "dual", "inflected", (2,)),
    ("هَاتَيْنِ", "feminine", "dual", "inflected", (2,)),
)
_RELATIVES = (
    ("الَّذِي", "masculine", "singular", "built", ()),
    ("الَّتِي", "feminine", "singular", "built", ()),
    ("الَّذِينَ", "masculine", "plural", "built", ()),
    ("اللَّاتِي", "feminine", "plural", "built", ()),
    ("اللَّائِي", "feminine", "plural", "built", ()),
    ("اللَّذَانِ", "masculine", "dual", "inflected", (2,)),
    ("اللَّذَيْنِ", "masculine", "dual", "inflected", (2,)),
    ("اللَّتَانِ", "feminine", "dual", "inflected", (2,)),
    ("اللَّتَيْنِ", "feminine", "dual", "inflected", (2,)),
)
_OPERATORS = {
    "هل": ("polar_interrogative", "QUESTION"),
    "أ": ("polar_interrogative", "QUESTION"),
    "من": ("wh_subject", "QUESTION_OR_RELATIVE_OR_PREPOSITION"),
    "ما": ("wh_subject", "QUESTION_OR_NEGATION_OR_RELATIVE"),
    "ماذا": ("wh_subject", "QUESTION"),
    "أين": ("place_time_complements", "QUESTION"),
    "متى": ("place_time_complements", "QUESTION"),
    "كيف": ("force_nonassertive", "QUESTION"),
    "إن": ("inna_case", "EMPHASIS_OR_CONDITION"),
    "أن": ("inna_case", "SUBORDINATION"),
    "كأن": ("inna_case", "SIMILITUDE"),
    "لكن": ("clause_conjunction", "ADVERSATIVE"),
    "كان": ("kana_case", "PAST_COPULA_OR_VERB"),
    "ليس": ("laysa_negation", "NEGATION"),
    "لم": ("imperfect_prefix", "NEGATION_JUSSIVE"),
    "لن": ("imperfect_prefix", "NEGATION_SUBJUNCTIVE"),
    "لا": ("force_nonassertive", "NEGATION_OR_PROHIBITION"),
    "ليت": ("force_nonassertive", "WISH"),
    "لعل": ("force_nonassertive", "HOPE"),
    "يا": ("force_nonassertive", "VOCATIVE"),
    "إلا": ("restriction", "RESTRICTION_OR_EXCEPTION"),
    "إنما": ("restriction", "RESTRICTION_REQUIRES_SCOPE"),
    "و": ("clause_conjunction", "CONJUNCTION"),
    "أو": ("clause_conjunction", "DISJUNCTION"),
    "ف": ("cause", "CONSEQUENCE_OR_CAUSE_OR_COORDINATION"),
    "لأن": ("cause", "CAUSAL_ATTACHMENT_REQUIRES_WITNESS"),
    "في": ("place_time_complements", "PREPOSITION"),
    "سوف": ("imperfect_prefix", "FUTURE"),
}


def _profile(reading):
    candidate = reading.get("person_evidence")
    if candidate and candidate.get("person_profile") is not None:
        p = candidate["person_profile"]
        return {"person": p["person"], "gender": ("masculine", "feminine", None)[p["gender"]],
                "number": ("singular", "dual", "plural")[p["number"]]}
    if candidate is not None:
        return {"person": 3 if candidate.get("pos") in ("N", "PN", "ADJ") else None,
                "gender": candidate.get("gender_name"), "number": candidate.get("number_name")}
    features = reading.get("lexical_features", {})
    person = features.get("person")
    return {"person": int(person[0]) if type(person) is str and person[:1] in ("1", "2", "3") else None,
            "gender": features.get("gender"), "number": features.get("number")}


def _token(source, segment):
    result = deepcopy(segment)
    result["token_id"] = identity([source.sha256, segment["span"], segment["surface"]])
    return result


def _slice(source, token, start, end, kind):
    surface = token["surface"]
    lo = token["span"]["start"] + len(surface[:start].encode("utf-8"))
    hi = token["span"]["start"] + len(surface[:end].encode("utf-8"))
    part = {"kind": "written_run", "surface": surface[start:end],
            "span": span_dict(_span(source, lo, hi)), "parent_span": token["span"],
            "segmentation_basis": kind}
    return _token(source, part)


def _synthetic_reading(token, *, pos, profile=None, construction="built", classes=(), rule):
    return {"reading_id": identity([token["token_id"], pos, profile, rule]), "kind": "noun",
            "construction": construction, "class_candidates": list(classes),
            "lexical_features": {"pos": pos, "lemma": token["surface"], "root": None,
                                 "gender": (profile or {}).get("gender"),
                                 "number": (profile or {}).get("number"), "aspect": None, "person": None},
            "profile": profile or {}, "support_records": [{"kind": "grammar", "rule": rule}],
            "stem_surface": token["surface"], "stem_span": token["span"],
            "variant": "declared_grammatical_paradigm", "al_evidence": 2,
            "sign_candidates": [], "nun_readings": [], "annotation_only": False,
            "segmentation": {"licensed": True, "coverage_valid": True,
                             "parts": [{"kind": pos, "surface": token["surface"], "span": token["span"]}]},
            "obligations": []}


class _Reader:
    def __init__(self, source, scope, lexical_model, context):
        self.source, self.scope, self.model = source, scope, lexical_model
        self.context = read_context(context)
        self.index, self.model_summary = ({}, None) if lexical_model is None else lexical_index(lexical_model)
        self.policy, self.inflection_policy = replay_discourse_policy(), replay_inflection_policy()
        self.construction_policy = replay_construction_policy()
        self.cache, self.mentions, self.derived = {}, [], {}
        self.entities = {e["id"]: e for e in self.context["value"]["entities"]}
        self.analysis_count = 0
        self.source_prefix_complete = True

    def support(self, rule):
        return {"kind": "source_grammar", "rule": rule, "policy_sha256": self.policy["policy_sha256"],
                "passage": self.policy["rules"][rule]}

    def reference(self, surface, **kwargs):
        return resolve_reference(surface, source_prefix_complete=self.source_prefix_complete, **kwargs)

    def readings(self, token):
        if token["token_id"] in self.cache:
            return self.cache[token["token_id"]]
        from .person_evidence import person_candidates
        occurrence = _read_run(self.source, self.scope, token, self.index,
                               self.model_summary, self.inflection_policy)
        readings = list(occurrence["readings"])
        for candidate in person_candidates(token["surface"], lexical_model=self.model):
            parts = []
            clusters = lookup_clusters(token["surface"])
            for spec in candidate.get("parts", []):
                lo, hi = spec["start_cluster"], spec["end_cluster"]
                if type(lo) is not int or type(hi) is not int or not 0 <= lo < hi <= len(clusters):
                    raise NabtError("INVALID_PERSON_PARTITION", "Person evidence must conserve complete clusters")
                p = _slice(self.source, token, clusters[lo][2], clusters[hi - 1][3], "source_person_partition")
                parts.append({"kind": spec.get("kind", "person_part"), "surface": p["surface"], "span": p["span"]})
            if parts and "".join(p["surface"] for p in parts) != token["surface"]:
                raise NabtError("INVALID_PERSON_PARTITION", "Person partition lost original bytes")
            kind = "verb" if candidate.get("aspect") in ("PERF", "IMPF", "IMPV") else "noun"
            row = {"reading_id": identity([token["token_id"], candidate["id"]]), "kind": kind,
                   "construction": candidate.get("construction"),
                   "class_candidates": candidate.get("class_candidates", []),
                   "lexical_features": {k: candidate.get(k) for k in ("pos", "lemma", "root", "aspect", "voice")},
                   "person_evidence": candidate, "support_records": candidate.get("supports", []),
                   "stem_surface": token["surface"], "stem_span": token["span"],
                   "variant": candidate.get("variant", "attested"), "al_evidence": 2,
                   "sign_candidates": [], "nun_readings": deepcopy(candidate.get("nun_readings", [])),
                   "annotation_only": False,
                   "segmentation": {"parts": parts or [{"kind": kind, "surface": token["surface"], "span": token["span"]}],
                                    "licensed": not candidate.get("obligations"), "coverage_valid": True,
                                    "basis": "SOURCE_PERSON_EVIDENCE"},
                   "obligations": candidate.get("obligations", [])}
            profile = _profile(row)
            row["profile"] = profile
            row["lexical_features"].update({"gender": profile["gender"], "number": profile["number"],
                                              "person": profile["person"]})
            if kind == "noun" and candidate.get("form_kind") == "separate_pronoun":
                row["lexical_features"]["pos"] = "PRON"
                row["construction"] = "built"
            row["segmentation"]["licensed"] = candidate["segmentation_licensed"]
            host_end = candidate["host_end_cluster"]
            if type(host_end) is not int or not 0 < host_end <= len(clusters):
                raise NabtError("INVALID_PERSON_HOST", "A case host must occupy a complete observed cluster prefix")
            host = _slice(self.source, token, 0, clusters[host_end - 1][3], "qualified_case_host")
            row["stem_surface"], row["stem_span"] = host["surface"], host["span"]
            row["variant"] = candidate["host_variant"]
            row["possible_cases"] = list(candidate["possible_cases"])
            for nun in row["nun_readings"]:
                relative = nun.get("span")
                if relative is not None:
                    nun["span"] = span_dict(_span(self.source, token["span"]["start"] + relative["byte_start"],
                                                  token["span"]["start"] + relative["byte_end"]))
                nun["reading_id"] = row["reading_id"]
            readings.append(row)
        for forms, pos, rule in ((_DEMONSTRATIVES, "DEM", "demonstrative"),
                                  (_RELATIVES, "REL", "relative_return")):
            for template, gender, number, construction, classes in forms:
                if template_matches(token["surface"], template, mutable_last=False):
                    readings.append(_synthetic_reading(token, pos=pos, construction=construction, classes=classes,
                                    profile={"person": 3, "gender": gender, "number": number}, rule=rule))
        # Names are explicit naming premises. Prefer an independent lexical
        # reading when available; a premise never overrides its contrary mark.
        if any(form_matches(token["surface"], e["name"]) for e in self.entities.values()):
            noun_rows = [r for r in readings if r["kind"] == "noun" and not r.get("annotation_only")
                         and r["lexical_features"].get("pos") not in ("PRON", "DEM", "REL")]
            if not noun_rows:
                row = _synthetic_reading(token, pos="PN", construction=None, rule="context_naming_premise")
                row["support_records"] = [{"kind": "explicit_context", "sha256": self.context["sha256"],
                                            "field": "entities.name"}]
                readings.append(row)
        unique = {}
        from .construction_nominals import qualify_attested_alif
        readings = qualify_attested_alif(readings, token=token, source=self.source,
                                         index=self.index, policy=self.construction_policy)
        for row in readings:
            unique.setdefault(row["reading_id"], row)
        if len(unique) > MAX_ANALYSES:
            raise resource_limit("Discourse lexical ambiguity exceeds its budget", maximum=MAX_ANALYSES)
        self.cache[token["token_id"]] = list(unique.values())
        return self.cache[token["token_id"]]

    def assignment(self, token, reading, role, *, head=None, idhafa=False, inherited_case=None):
        if role in CONSTRUCTION_ROLES:
            case = construction_role_case(role, inherited_case)
            if case is None:
                raise NabtError("MISSING_INHERITED_CASE", "A dependent role needs its independently assigned head case")
        elif role in ("nominal_subject", "nominal_predicate", "imperfect_indicative"):
            case = role_case(role)
        else:
            case = relation_candidate(role, kind=reading["kind"], construction=reading["construction"])["case"]
        if type(case) is dict:
            case = case["case"]
        construction = reading["construction"]
        signs = sign_candidates(reading["class_candidates"], cases=(case,),
                                 al=reading.get("al_evidence", 0), idhafa=1 if idhafa else 2)
        case_surface = reading.get("nominal_case_carrier", {}).get("base_surface", reading["stem_surface"])
        signs = [s for s in signs if _surface_accepts(s, case_surface, reading)]
        if "possible_cases" in reading and case not in reading["possible_cases"]:
            signs = []
        # Missing short vowels do not license deletion of an orthographic
        # carrier. This reader does not generate an unwitnessed accusative
        # alif. Only the unambiguous ordinary endings below can pass this
        # conservative guard; other spelling exceptions remain uncovered.
        key = lookup_key(reading["stem_surface"])
        orthography_blocked = (case == 0 and reading["kind"] == "noun" and
            reading.get("al_evidence") != 1 and not idhafa and 0 in reading["class_candidates"] and
            not (key.endswith(("ا", "ى", "ة")) or key.endswith("اء")))
        if orthography_blocked:
            signs = [s for s in signs if s["class"] != 0]
        compatible = (construction != "inflected" or bool(signs)) and not (
            orthography_blocked and reading["class_candidates"] == [0])
        obligations = ["ACCUSATIVE_ORTHOGRAPHY_WITNESS"] if orthography_blocked else []
        # A lexical noun label does not establish the construction of a new
        # predicate. In particular, a stem extracted from a source PP must
        # not become a case-free property merely because no sign rejects it.
        # Naming premises identify subjects; they do not supply predicates.
        if role in ("nominal_predicate", "inna_predicate", "kana_predicate") and construction is None:
            obligations.append("PREDICATE_CONSTRUCTION_EVIDENCE_REQUIRED")
        return {"reading_id": reading["reading_id"], "span": token["span"], "surface": token["surface"],
                "role": role, "required_case": _CASE_NAMES[case], "compatible": compatible,
                "inflected_case": _CASE_NAMES[case] if construction == "inflected" and signs else None,
                "local_case": _CASE_NAMES[case] if construction == "built" else None,
                "case_domain": "inflected_case" if construction == "inflected" else "local_case" if construction == "built" else None,
                "sign_candidates": signs, "head_span": None if head is None else head["span"],
                "obligations": obligations,
                "status": "LICENSED_IN_DECLARED_FRAME" if compatible and construction else "CONSTRUCTION_EVIDENCE_NEEDED",
                "authority": "SOURCE_RELATIVE_SYNTACTIC_ASSIGNMENT"}

    def referents(self, token, role, *, head=None, variable=None, return_entity=None):
        if variable is not None:
            row = _synthetic_reading(token, pos="INTG", rule="wh_subject")
            return [{"reading": row, "reference": {"origin": "question_variable", "status": "VARIABLE",
                     "span": token["span"], "bound_entity_id": variable, "candidate_entity_ids": [],
                     "reference_id": identity([token["token_id"], variable])},
                     "assignment": self.assignment(token, row, role, head=head), "entity": variable}]
        result = []
        for row in self.readings(token):
            if row["kind"] != "noun" or row.get("annotation_only"):
                continue
            if row.get("person_evidence", {}).get("attached_pronouns"):
                continue
            pos = row["lexical_features"].get("pos")
            profile = row.get("profile", _profile(row))
            if pos == "PRON":
                origin = {1: "speaker", 2: "addressee", 3: "antecedent"}.get(profile.get("person"))
                if origin is None:
                    continue
            elif pos == "DEM":
                origin = "deictic"
            elif pos == "REL":
                if return_entity is None:
                    continue
                origin = "relative_return"
            else:
                origin = "named"
            carrier = row.get("nominal_case_carrier") if origin == "named" else None
            reference_surface = carrier["base_surface"] if carrier else token["surface"]
            reference = self.reference(reference_surface, origin=origin, profile=profile,
                                          context=self.context, mentions=self.mentions, span=token["span"],
                                          scope=self.scope, return_entity=return_entity)
            if carrier:
                reference["written_surface"] = token["surface"]
                reference["nominal_carrier_reading_id"] = row["reading_id"]
                reference["reference_id"] = identity({k: v for k, v in reference.items() if k != "reference_id"})
            assignment = self.assignment(token, row, role, head=head)
            result.append({"reading": row, "reference": reference, "assignment": assignment,
                           "entity": reference["bound_entity_id"]})
        return result

    def predicates(self, token):
        return [r for r in self.readings(token) if r["kind"] == "noun" and
                r["lexical_features"].get("pos") in ("N", "ADJ") and
                r["lexical_features"].get("lemma") and not r.get("annotation_only") and
                not r.get("prefix_relation") and r.get("al_evidence") != 1 and
                not r.get("person_evidence", {}).get("attached_pronouns")]

    def verbs(self, token):
        return [r for r in self.readings(token) if r["kind"] == "verb" and
                r["lexical_features"].get("lemma") and not r.get("annotation_only") and
                r.get("segmentation", {}).get("licensed", False) and "person_evidence" in r]

    def predicate_agreement(self, readings, assignments, refs, *, force):
        """Replay direct adjective agreement at the selected predication edge.

        This is separate from naat: case and definiteness do not have to
        agree. A source-declared ordinary noun predicate is outside this
        adjective rule. Nonhuman plural regimes, unknown source features and
        an unbound subject edge remain unproved rather than being guessed.
        """
        pairs = {"nominal_predicate": "nominal_subject", "kana_predicate": "kana_subject",
                 "inna_predicate": "inna_subject", "zanna_object2": "zanna_object1"}
        by_id = {r["reading_id"]: r for r in readings}
        obligations, relations, supports = [], [], []
        for predicate in assignments:
            role = predicate["role"]
            reading = by_id.get(predicate["reading_id"])
            if role not in pairs or reading is None or reading["lexical_features"].get("pos") != "ADJ":
                continue
            candidates = [a for a in assignments if a["role"] == pairs[role] and
                ((role == "nominal_predicate" and predicate["head_span"] == a["span"]) or
                 (role != "nominal_predicate" and predicate["head_span"] is not None and
                  predicate["head_span"] == a["head_span"]))]
            candidates = list({identity([a["span"], a["reading_id"]]): a for a in candidates}.values())
            if len(candidates) != 1 or candidates[0]["reading_id"] not in by_id:
                obligations.append("PREDICATE_SUBJECT_BINDING_EVIDENCE_REQUIRED")
                continue
            subject = candidates[0]
            subject_reading = by_id[subject["reading_id"]]
            left, right = _profile(subject_reading), _profile(reading)
            subject_refs = [r for r in refs if r["span"] == subject["span"]]
            entity_ids = {r["bound_entity_id"] for r in subject_refs}
            # A question variable has no acquired subject gender/number.
            # Preserve the selected adjective's requirements as a typed
            # query constraint; only substitution against an independently
            # licensed source predication can discharge it. This bounded
            # singular-person query is not a general agreement law for من.
            if (force == "QUESTION" and role == "nominal_predicate" and
                    subject_reading["lexical_features"].get("pos") == "INTG" and
                    subject_reading.get("support_records") == [{"kind": "grammar", "rule": "wh_subject"}] and
                    template_matches(subject_reading["stem_surface"], "مَنْ", mutable_last=False) and
                    len(subject_refs) == 1 and subject_refs[0].get("origin") == "question_variable" and
                    subject_refs[0].get("status") == "VARIABLE" and
                    subject_refs[0].get("bound_entity_id") == "?person" and
                    right.get("gender") in ("masculine", "feminine") and right.get("number") == "singular"):
                relations.append({"kind": "predicate_agreement", "head_span": subject["span"],
                    "dependent_span": predicate["span"], "head_reading_id": subject["reading_id"],
                    "dependent_reading_id": predicate["reading_id"], "subject_role": subject["role"],
                    "predicate_role": role, "regime": "constrained_singular_person_query",
                    "regime_licensed": False, "status": "pending_substitution",
                    "question_variable": "?person", "subject_profile": deepcopy(left),
                    "predicate_profile": deepcopy(right),
                    "predicate_lemma": reading["lexical_features"].get("lemma"),
                    "subject_reference_ids": [subject_refs[0]["reference_id"]],
                    "law_id": CONSTRUCTION_LAW_ID, "law_sha256": CONSTRUCTION_TABLE_SHA256,
                    "case_and_definiteness_equalities_required": False,
                    "authority": "QUERY_CONSTRAINT_REQUIRING_AN_INDEPENDENT_SOURCE_BINDING"})
                continue
            gender_basis = {"kind": "selected_lexical_or_grammatical_profile"}
            # A context-only personal name is an explicit naming premise,
            # not an acquired lexical noun. Its uniquely named individual
            # can supply a *semantic* singular-person agreement profile.
            # Never fill the stored reading or override an independent
            # source N/PN reading, even when that source profile is unknown.
            named_premise = (
                subject_reading["lexical_features"].get("pos") == "PN" and
                subject_reading.get("construction") is None and
                subject_reading.get("variant") == "declared_grammatical_paradigm" and
                subject_reading.get("segmentation", {}).get("licensed") and
                subject_reading.get("support_records") == [{"kind": "explicit_context",
                    "sha256": self.context["sha256"], "field": "entities.name"}] and
                len(subject_refs) == 1 and subject_refs[0].get("origin") == "named" and
                subject_refs[0].get("status") == "RESOLVED")
            if named_premise:
                entity_id = subject_refs[0]["bound_entity_id"]
                entity = self.entities.get(entity_id, {})
                if (entity.get("kind") == "person" and entity.get("number") == "singular" and
                        entity.get("gender") in ("masculine", "feminine")):
                    left = {"person": 3, "gender": entity["gender"], "number": entity["number"]}
                    gender_basis = {"kind": "explicit_named_person_semantic_profile",
                        "entity_id": entity_id, "context_sha256": self.context["sha256"],
                        "reference_ids": [subject_refs[0]["reference_id"]],
                        "source_fields": ["entities.name", "entities.kind", "entities.gender", "entities.number"],
                        "lexical_profile_acquired": False}
            # A common-gender pronoun (e.g. أنا) is not an unseen noun whose
            # lexical gender may be supplied by a name. Its separately
            # resolved discourse referent can license semantic agreement.
            # Preserve the source profile unchanged and record this premise.
            common_pronoun = False
            if (subject_reading["lexical_features"].get("pos") == "PRON" and left.get("gender") is None and
                    subject_reading.get("segmentation", {}).get("licensed")):
                from .person_evidence import installed_registry as person_registry, EXPECTED_TABLE_SHA256 as person_sha
                common_pronoun = any(p["gender"] == 2 and p["person"] == left.get("person") and
                    ("singular", "dual", "plural")[p["number"]] == left.get("number") and
                    template_matches(subject_reading["stem_surface"], p["surface"], mutable_last=False)
                    for p in person_registry()["separate_pronouns"])
            if (common_pronoun and
                    len(entity_ids) == 1 and any(r.get("status") == "RESOLVED" for r in subject_refs)):
                entity_id = next(iter(entity_ids))
                gender = self.entities.get(entity_id, {}).get("gender")
                if gender in ("masculine", "feminine"):
                    left = {**left, "gender": gender}
                    gender_basis = {"kind": "resolved_common_gender_pronoun", "entity_id": entity_id,
                                    "context_sha256": self.context["sha256"],
                                    "person_law_sha256": person_sha,
                                    "reference_ids": sorted({r["reference_id"] for r in subject_refs
                                                             if r.get("status") == "RESOLVED"})}
            human = (len(entity_ids) == 1 and
                     self.entities.get(next(iter(entity_ids)), {}).get("kind") == "person")
            regime = (left.get("number") == "singular" or
                      left.get("number") in ("dual", "plural") and human)
            axes = {axis: ("possible" if left.get(axis) in (None, "unknown") or
                    right.get(axis) in (None, "unknown") else
                    "confirmed" if left[axis] == right[axis] else "conflict")
                    for axis in ("gender", "number")}
            state = predicate_agreement_status(regime_licensed=regime, **axes)
            if state != "confirmed":
                obligations.append("CONSTRUCTION_CONFLICT" if state == "conflict" else
                                   "PREDICATE_AGREEMENT_EVIDENCE_REQUIRED")
            relations.append({"kind": "predicate_agreement", "head_span": subject["span"],
                "dependent_span": predicate["span"], "head_reading_id": subject["reading_id"],
                "dependent_reading_id": predicate["reading_id"], "subject_role": subject["role"],
                "predicate_role": role, "regime": "source_declared_direct_adjective",
                "regime_licensed": regime, "axes": axes, "status": state,
                "subject_gender_basis": gender_basis,
                "subject_profile": deepcopy(left), "predicate_profile": deepcopy(right),
                "predicate_lemma": reading["lexical_features"].get("lemma"),
                "subject_reference_ids": sorted({r["reference_id"] for r in subject_refs}),
                "law_id": CONSTRUCTION_LAW_ID, "law_sha256": CONSTRUCTION_TABLE_SHA256,
                "case_and_definiteness_equalities_required": False})
        if relations:
            rule = "predicate_adjectival_agreement"
            supports.append({"kind": "source_construction_grammar", "rule": rule,
                "law_id": CONSTRUCTION_LAW_ID, "law_sha256": CONSTRUCTION_TABLE_SHA256,
                "policy_sha256": self.construction_policy["policy_sha256"],
                "passage": self.construction_policy["rules"][rule]})
        return obligations, relations, supports

    def analysis(self, tokens, *, frame, force, refs, assignments, readings, claims,
                 obligations=(), supports=(), relations=()):
        self.analysis_count += 1
        if self.analysis_count > MAX_ANALYSES * MAX_CLAUSES:
            raise resource_limit("Discourse composition budget exceeded")
        for reading in readings:
            self.derived[reading["reading_id"]] = reading
        agreement_obligations, agreement_relations, agreement_supports = self.predicate_agreement(
            readings, assignments, refs, force=force)
        # Rebuilds recompute the check; an existing relation is not authority.
        # Reference completeness is derived again from these exact references
        # below. A composed frame can carry the previous analysis's public
        # missing-premise list; an unresolved referent in that list is not a
        # missing syntactic premise. In particular, it must not erase a
        # witnessed case/mood assignment while still withholding assertion.
        obligations = [o for o in obligations if o != "REFERENCE_NOT_UNIQUELY_LICENSED"] + agreement_obligations
        relations = [r for r in relations if r.get("kind") != "predicate_agreement"] + agreement_relations
        supports = list(supports) + [s for s in agreement_supports if s not in supports]
        claims = deepcopy(claims)
        for relation in agreement_relations:
            if relation["status"] != "pending_substitution":
                continue
            variable = relation["question_variable"]
            profile = relation["predicate_profile"]
            constraint = {"kind": "question_variable", "name": variable,
                          "gender": profile["gender"], "number": profile["number"]}
            matched = False
            for claim in claims:
                if (claim["predicate_kind"] == "property" and claim["predicate"] == relation["predicate_lemma"] and
                        (claim["args"] == [variable] or claim["args"] == [constraint])):
                    claim["args"] = [deepcopy(constraint)]
                    matched = True
            if not matched:
                obligations.append("QUESTION_AGREEMENT_CONSTRAINT_BINDING_REQUIRED")
        missing = list(obligations)
        if any(r["bound_entity_id"] is None for r in refs):
            missing.append("REFERENCE_NOT_UNIQUELY_LICENSED")
        if any(not a["compatible"] for a in assignments):
            missing.append("OBSERVED_FORM_CONFLICTS_WITH_REQUIRED_CASE")
        missing.extend(o for a in assignments for o in a.get("obligations", []))
        rejected = (any(not a["compatible"] for a in assignments) or
                    any(o in ("PERSON_AGREEMENT_CONFLICT", "OVERT_SUBJECT_PERSON_CONFLICT", "CONSTRUCTION_CONFLICT") for o in obligations) or
                    any(r.get("candidates") and all(c["compatibility"] == "conflict" for c in r["candidates"])
                        for r in refs))
        syntax_complete = (not obligations and not any(a.get("obligations") for a in assignments)
                           and all(a["compatible"] for a in assignments))
        references_complete = all(r["bound_entity_id"] is not None for r in refs)
        allowed = assertion_allowed(force, licensed_syntax=syntax_complete, scope_complete=True,
                                    references_complete=references_complete, qualifiers_preserved=True,
                                    nonquoted=True, source_supported=bool(supports))
        assignments = deepcopy(assignments)
        for assigned in assignments:
            assigned["activated"] = syntax_complete and not rejected
            assigned["actual_role"] = assigned["role"] if assigned["activated"] else None
            if not assigned["activated"]:
                assigned["inflected_case"], assigned["local_case"] = None, None
                assigned["status"] = "CANDIDATE_IN_UNLICENSED_FRAME"
        result = {"frame": frame, "force": force, "span": span_dict(_span(self.source,
                    min(t["span"]["start"] for t in tokens), max(t["span"]["end"] for t in tokens))),
                  "reading_ids": [r["reading_id"] for r in readings],
                  "references": deepcopy(refs), "assignments": assignments,
                  "relations": list(relations), "claims": claims,
                  "licensed_syntax": syntax_complete, "references_complete": references_complete,
                  "rejected_candidate": rejected,
                  "assertion_allowed": allowed, "obligations": sorted(set(missing)),
                  "supports": list(supports)}
        result["analysis_id"] = identity(result)
        return result

    @staticmethod
    def claim(predicate, args, positive, tense, time, place, restriction):
        return {"predicate": predicate, "args": args, "positive": positive,
                "predicate_kind": "property", "voice": None,
                "tense": tense, "time": time, "place": place, "restriction": restriction}

    def nominal(self, tokens, *, force, subject_role, predicate_role, positive, tense,
                time, place, restriction, head=None, wh=None):
        if len(tokens) != 2:
            return []
        subjects = self.referents(tokens[0], subject_role, head=head,
                                  variable="?person" if wh == "subject" else None)
        result = []
        for subject, predicate in product(subjects, self.predicates(tokens[1])):
            assignment = self.assignment(tokens[1], predicate, predicate_role, head=head or tokens[0])
            claim = self.claim(predicate["lexical_features"]["lemma"], [subject["entity"]],
                               positive, tense, time, place, restriction)
            result.append(self.analysis(tokens, frame="nominal_predication", force=force,
                refs=[subject["reference"]], assignments=[subject["assignment"], assignment],
                readings=[subject["reading"], predicate], claims=[claim],
                supports=[self.support("nominal_predication")]))
        return result

    def _agreement(self, verb, subject, *, before_subject):
        profile = verb.get("profile", _profile(verb))
        eid = subject["entity"]
        if eid is None or eid.startswith("?"):
            return []
        subject_profile = subject["reading"].get("profile", _profile(subject["reading"]))
        expected_person = subject_profile.get("person") or 3
        if profile.get("person") != expected_person:
            return ["PERSON_AGREEMENT_NOT_WITNESSED" if profile.get("person") is None else "PERSON_AGREEMENT_CONFLICT"]
        entity = self.entities[eid]
        if before_subject:
            # VSO number agreement is not SVO agreement: in this small profile
            # a singular third-person verb can precede a plural nominal subject.
            if profile.get("number") != "singular":
                return ["OVERT_SUBJECT_PERSON_CONFLICT"]
            profile = {**profile, "number": None}
        # A context's missing trait cannot erase the independent lexical
        # feature of this particular subject reading.
        compatibilities = [profile_compatibility(profile, subject_profile), profile_compatibility(profile, entity)]
        return ["PERSON_AGREEMENT_CONFLICT"] if "conflict" in compatibilities else []

    def attached_references(self, token, reading):
        result = []
        clusters = lookup_clusters(token["surface"])
        for suffix in reading.get("person_evidence", {}).get("attached_pronouns", []):
            if not suffix["licensed"] or suffix["person_profile"] is None:
                return None
            relations = suffix["attachment_candidates"]
            if relations not in (["verbal_object"], ["possessive"]):
                return None
            start, end = suffix["start_cluster"], suffix["end_cluster"]
            part = _slice(self.source, token, clusters[start][2], clusters[end - 1][3], "qualified_attached_pronoun")
            raw = suffix["person_profile"]
            profile = {"person": raw["person"], "gender": ("masculine", "feminine", None)[raw["gender"]],
                       "number": ("singular", "dual", "plural")[raw["number"]]}
            origin = {1: "speaker", 2: "addressee", 3: "antecedent"}[profile["person"]]
            reference = self.reference(part["surface"], origin=origin, profile=profile, context=self.context,
                                           mentions=self.mentions, span=part["span"], scope=self.scope)
            row = _synthetic_reading(part, pos="PRON", profile=profile, rule="independent_pronouns")
            row["support_records"] = reading["support_records"]
            role = "direct_object" if relations == ["verbal_object"] else "idafa_complement"
            result.append({"reading": row, "reference": reference, "entity": reference["bound_entity_id"],
                           "assignment": self.assignment(part, row, role, head=token), "relation": relations[0]})
        return result

    def verbal(self, tokens, *, force, positive, tense, time, place, restriction,
               head=None, mood=None, wh=None):
        if not tokens or len(tokens) > 3:
            return []
        positions = (0,) if len(tokens) == 1 else (0, 1)
        result = []
        for vpos in positions:
            if vpos >= len(tokens):
                continue
            verb_token = tokens[vpos]
            for verb in self.verbs(verb_token):
                features = verb["lexical_features"]
                aspect = features.get("aspect")
                if aspect not in ("PERF", "IMPF", "IMPV"):
                    continue
                profile = verb.get("profile", _profile(verb))
                voice = features.get("voice")
                if voice is None:
                    # QAC's declared default, recorded here rather than editing
                    # the historical masked lexical index.
                    voice = "active"
                local_force = "COMMAND" if aspect == "IMPV" else force
                vtense = tense if tense != "unspecified" else "past" if aspect == "PERF" else "nonpast"
                obligations = [o for o in verb.get("obligations", []) if not
                               (o == "SHORT_HOLLOW_FORM_REQUIRES_EXTERNAL_JUSSIVE_CONTEXT" and mood == "imperfect_jussive")]
                attached = self.attached_references(verb_token, verb)
                if attached is None or len(attached) > 1:
                    obligations.append("ATTACHED_ARGUMENT_REQUIRES_COMPLETE_REFERENCE")
                    attached = []
                if mood and aspect != "IMPF":
                    obligations.append("GOVERNOR_REQUIRES_IMPERFECT")
                if head is not None and lookup_key(head["surface"]) == "سوف" and aspect != "IMPF":
                    obligations.append("FUTURE_PARTICLE_REQUIRES_IMPERFECT")
                vassign = []
                if mood:
                    vassign.append(self.assignment(verb_token, verb, mood, head=head))
                elif aspect == "IMPF":
                    vassign.append(self.assignment(verb_token, verb, "imperfect_indicative", head=head))
                role = "passive_subject" if voice == "passive" else "active_subject"
                if len(tokens) == 1:
                    origin = {1: "speaker", 2: "addressee", 3: "antecedent"}.get(profile.get("person"))
                    if origin is None:
                        continue
                    reference = self.reference(verb_token["surface"], origin=origin, profile=profile,
                        context=self.context, mentions=self.mentions, span=verb_token["span"], scope=self.scope)
                    subject = {"reading": verb, "reference": reference,
                               "entity": reference["bound_entity_id"], "assignment": None}
                    subjects = [subject]
                    spos = None
                else:
                    spos = 1 if vpos == 0 else 0
                    subjects = self.referents(tokens[spos], role, head=verb_token,
                        variable="?person" if wh == "subject" and spos == 0 else None)
                for subject in subjects:
                    extra = list(obligations)
                    if spos is not None:
                        extra.extend(self._agreement(verb, subject, before_subject=vpos == 0))
                        if vpos == 0 and profile.get("person") not in (None, 3):
                            extra.append("OVERT_SUBJECT_PERSON_CONFLICT")
                    assignments = vassign + ([subject["assignment"]] if subject["assignment"] else [])
                    assignments += [p["assignment"] for p in attached]
                    refs = [subject["reference"]] + [p["reference"] for p in attached]
                    readings = [verb] + ([subject["reading"]] if spos is not None else []) + [p["reading"] for p in attached]
                    args = [subject["entity"]] + [p["entity"] for p in attached]
                    if len(tokens) == 3:
                        # Only a replayed full host+object-pronoun witness can
                        # establish this bounded lexical valency premise.
                        witnesses = verb.get("person_evidence", {}).get("valency_witnesses", [])
                        if not witnesses or voice != "active" or attached:
                            extra.append("INDEPENDENT_TRANSITIVE_HOST_WITNESS")
                            objects = []
                        else:
                            objects = self.referents(tokens[2], "direct_object", head=verb_token,
                                                     variable="?object" if wh == "object" else None)
                        if not objects:
                            extra.append("DIRECT_OBJECT_READING")
                        for obj in objects:
                            claim = self.claim(features["lemma"], args + [obj["entity"]], positive, vtense, time, place, restriction)
                            claim.update(predicate_kind="event", voice=voice)
                            result.append(self.analysis(tokens, frame="active_verb_subject_object", force=local_force,
                                refs=refs + [obj["reference"]], assignments=assignments + [obj["assignment"]],
                                readings=readings + [obj["reading"]], claims=[claim], obligations=extra,
                                supports=[self.support("active_subject"), {"kind": "valency_source", "witnesses": witnesses}]))
                        # With no object reading this production has not
                        # consumed its third token. It is not a complete
                        # competing analysis of a newly supported modifier.
                        continue
                    claim = self.claim(features["lemma"], args, positive, vtense, time, place, restriction)
                    claim.update(predicate_kind="event", voice=voice)
                    result.append(self.analysis(tokens, frame="verbal_predication", force=local_force,
                        refs=refs, assignments=assignments, readings=readings, claims=[claim], obligations=extra,
                        supports=[self.support("active_subject")]))
        return result

    def complements(self, tokens):
        """At most one witnessed time adverb and one literal في+place phrase."""
        variants = [{"tokens": list(tokens), "time": [], "place": [], "refs": [],
                     "assignments": [], "readings": [], "supports": [], "obligations": [],
                     "requires_event": False}]
        for _ in range(2):
            expanded = []
            for variant in variants:
                body = variant["tokens"]
                if len(body) >= 3 and lookup_key(body[-2]["surface"]) == "في" and not variant["place"]:
                    options = self.referents(body[-1], "preposition_object", head=body[-2])
                    for option in options:
                        value = deepcopy(variant)
                        value["tokens"] = body[:-2]
                        value["place"] = [option["entity"]]
                        value["refs"].append(option["reference"])
                        value["assignments"].append(option["assignment"])
                        value["readings"].append(option["reading"])
                        value["supports"].append(self.support("place_time_complements"))
                        if option["entity"] is not None and self.entities[option["entity"]]["kind"] != "place":
                            value["obligations"].append("LITERAL_PLACE_CONTEXT_WITNESS")
                        expanded.append(value)
                    if options:
                        continue
                if len(body) >= 2 and not variant["time"]:
                    indices = [len(body) - 1] + ([1] if len(body) == 3 else [])
                    for index in dict.fromkeys(indices):
                        token = body[index]
                        choices = []
                        for adverb in adverb_candidates(token["surface"], lexical_model=self.model):
                            if adverb["pos"] != "T":
                                continue
                            row = _synthetic_reading(token, pos="T", construction=None,
                                                     rule="place_time_complements")
                            row["reading_id"] = identity([token["token_id"], adverb["id"]])
                            row["support_records"] = adverb["supports"]
                            row["lexical_features"]["lemma"] = adverb["lemma"]
                            choices.append((row, {"lemma": adverb["lemma"], "form": lookup_key(adverb["form"]),
                                "source_article": adverb["source_article"]}, "place_time_complements", False))
                        # The primary passage names these two temporal uses
                        # with verbal events and explicitly retains their
                        # other noun uses. Keep POS=N and its lexical source;
                        # do not acquire a general N->T conversion or case.
                        named_example = {"أمس": "أمس", "غدا": "غد"}.get(lookup_key(token["surface"]))
                        if named_example is not None and index == len(body) - 1:
                            for row in self.readings(token):
                                features = row["lexical_features"]
                                if (features.get("pos") != "N" or lookup_key(features.get("lemma") or "") != named_example
                                        or row.get("annotation_only") or not row.get("segmentation", {}).get("licensed")
                                        or row.get("person_evidence", {}).get("attached_pronouns")
                                        or not any("byte_start" in s for s in row.get("support_records", []))):
                                    continue
                                if (named_example == "أمس" and row["construction"] is None
                                        and lookup_clusters(token["surface"])[-1][1] == {"ِ"}
                                        and template_matches(token["surface"], "أَمْسِ", mutable_last=False)):
                                    # This named Hijazi reading has a built
                                    # kasra surface and an accusative local
                                    # function. Refine only this temporal
                                    # reading; the occurrence's original N
                                    # readings and other dialects stay intact.
                                    original_reading = row
                                    row = deepcopy(original_reading)
                                    basis = {"rule": "temporal_ams_built", "dialect": "Hijazi",
                                        "scope": "EXPLICIT_KASRA_TEMPORAL_AMS_IN_A_VERBAL_EVENT",
                                        "origin_reading_id": original_reading["reading_id"],
                                        "original_construction": original_reading["construction"],
                                        "original_class_candidates": original_reading["class_candidates"],
                                        "surface_realization": "fixed_kasra", "function": "local_accusative",
                                        "source": self.support("temporal_ams_built")}
                                    row.update(construction="built", class_candidates=[],
                                        variant="source_witnessed_hijazi_temporal_ams",
                                        construction_premise=basis,
                                        obligations=[o for o in row.get("obligations", []) if o != "CONSTRUCTION_EVIDENCE"])
                                    row["reading_id"] = identity([original_reading["reading_id"], basis])
                                choices.append((row, {"lemma": features["lemma"], "form": lookup_key(token["surface"]),
                                    "source_article": False}, "temporal_noun_examples", True))
                        for row, temporal, rule, requires_event in choices:
                            value = deepcopy(variant)
                            value["tokens"] = body[:index] + body[index + 1:]
                            value["time"] = [temporal]
                            value["requires_event"] = requires_event
                            value["assignments"].append(self.assignment(token, row, "time_adverb", head=body[0]))
                            value["readings"].append(row)
                            value["supports"].append(self.support(rule))
                            if row.get("construction_premise", {}).get("rule") == "temporal_ams_built":
                                value["supports"].append(self.support("temporal_ams_built"))
                            expanded.append(value)
                    # A witnessed T use does not erase a separately acquired
                    # N/object use of the same token. Retain the unconsumed
                    # token sequence; only an actual complete grammar
                    # production may turn it into a competing analysis.
                expanded.append(variant)
            # Repeating the bounded attachment pass can rediscover the same
            # source reading. Only identical variants are coalesced.
            variants = list({wire(v): v for v in expanded}.values())
        return variants

    def location(self, tokens, *, force, subject_role, positive, tense, time, place,
                 restriction, head=None, wh=None):
        if len(tokens) != 1 or not place:
            return []
        result = []
        for subject in self.referents(tokens[0], subject_role, head=head):
            claim = self.claim("@located", [subject["entity"]], positive, tense, time, place, restriction)
            claim["predicate_kind"] = "location"
            result.append(self.analysis(tokens, frame="locative_predication", force=force,
                refs=[subject["reference"]], assignments=[subject["assignment"]], readings=[subject["reading"]],
                claims=[claim], supports=[self.support("nominal_predication"), self.support("place_time_complements")]))
        return result

    def idafa(self, tokens, *, force, subject_role, predicate_role, positive, tense,
              time, place, restriction, head=None, wh=None):
        """A definite head noun + named/pronominal complement + predicate.

        The construct relation is grammatical, not a claim of ownership. A
        head individual must be independently named in the explicit context;
        an idafa phrase is never an invented entity identifier.
        """
        if len(tokens) != 3 or wh is not None:
            return []
        result = []
        for noun in self.predicates(tokens[0]):
            if noun["stem_surface"][-1:] in ("ٌ", "ٍ", "ً"):
                continue
            for complement in self.referents(tokens[1], "idafa_complement", head=tokens[0]):
                for predicate in self.predicates(tokens[2]):
                    headref = self.reference(tokens[0]["surface"], origin="named", profile=_profile(noun),
                        context=self.context, mentions=self.mentions, span=tokens[0]["span"], scope=self.scope)
                    assignments = [self.assignment(tokens[0], noun, subject_role, head=head, idhafa=True),
                                   complement["assignment"], self.assignment(tokens[2], predicate, predicate_role, head=tokens[0])]
                    relation = {"kind": "idafa", "head_span": tokens[0]["span"], "complement_span": tokens[1]["span"],
                                "complement_reference": complement["reference"]["reference_id"],
                                "head_referent": headref["bound_entity_id"], "ownership_asserted": False}
                    claim = self.claim(predicate["lexical_features"]["lemma"], [headref["bound_entity_id"]], positive,
                        tense, time, place, restriction + [{"kind": "idafa", "complement": complement["entity"]}])
                    result.append(self.analysis(tokens, frame="idafa_subject_predication", force=force,
                        refs=[headref, complement["reference"]], assignments=assignments, readings=[noun, complement["reading"], predicate],
                        claims=[claim], relations=[relation],
                        supports=[self.support("idafa"), self.support("nominal_predication")]))
        return result

    def attached_nominal(self, tokens, *, force, subject_role, predicate_role, positive, tense,
                         time, place, restriction, head=None, wh=None):
        if len(tokens) != 2 or wh is not None:
            return []
        result = []
        for noun in self.readings(tokens[0]):
            if noun["kind"] != "noun" or not noun.get("person_evidence", {}).get("attached_pronouns"):
                continue
            attached = self.attached_references(tokens[0], noun)
            if attached is None or len(attached) != 1 or attached[0]["relation"] != "possessive":
                continue
            complement = attached[0]
            headref = self.reference(noun["stem_surface"], origin="named", profile=_profile(noun),
                context=self.context, mentions=self.mentions, span=noun["stem_span"], scope=self.scope)
            for predicate in self.predicates(tokens[1]):
                claim = self.claim(predicate["lexical_features"]["lemma"], [headref["bound_entity_id"]], positive,
                    tense, time, place, restriction + [{"kind": "idafa", "complement": complement["entity"]}])
                result.append(self.analysis(tokens, frame="attached_idafa_subject_predication", force=force,
                    refs=[headref, complement["reference"]], assignments=[
                        self.assignment(tokens[0], noun, subject_role, head=head, idhafa=True), complement["assignment"],
                        self.assignment(tokens[1], predicate, predicate_role, head=tokens[0])],
                    readings=[noun, complement["reading"], predicate], claims=[claim],
                    relations=[{"kind": "idafa", "head_span": noun["stem_span"],
                                "complement_span": complement["reference"]["span"], "ownership_asserted": False}],
                    supports=[self.support("idafa"), self.support("nominal_predication")]))
        return result

    def relative(self, tokens, *, force, subject_role, predicate_role, positive, tense,
                 time, place, restriction, head=None, wh=None):
        """Named/deictic head + relative + qualified singular verb + predicate."""
        if len(tokens) == 5 and wh is None:
            return self.nominal_relative(tokens, force=force, subject_role=subject_role,
                predicate_role=predicate_role, positive=positive, tense=tense, time=time,
                place=place, restriction=restriction, head=head)
        if len(tokens) != 4 or wh is not None:
            return []
        result = []
        for subject in self.referents(tokens[0], subject_role, head=head):
            for relative in self.readings(tokens[1]):
                if relative["lexical_features"].get("pos") != "REL":
                    continue
                for verb in self.verbs(tokens[2]):
                    profile = verb.get("profile", _profile(verb))
                    if (profile.get("person") != 3 or profile.get("number") != "singular" or
                            verb["lexical_features"].get("aspect") != "IMPF" or
                            verb.get("person_evidence", {}).get("attached_pronouns")):
                        continue
                    ret = self.reference(tokens[2]["surface"], origin="relative_return", profile=profile,
                        context=self.context, mentions=self.mentions, span=tokens[2]["span"], scope=self.scope,
                        return_entity=subject["entity"])
                    relref = self.reference(tokens[1]["surface"], origin="relative_return",
                        profile=relative.get("profile", _profile(relative)), context=self.context,
                        mentions=self.mentions, span=tokens[1]["span"], scope=self.scope,
                        return_entity=subject["entity"])
                    for predicate in self.predicates(tokens[3]):
                        relative_profile = relative.get("profile", _profile(relative))
                        subject_profile = subject["reading"].get("profile", _profile(subject["reading"]))
                        agreement = [profile_compatibility(relative_profile, subject_profile),
                                     profile_compatibility(profile, relative_profile),
                                     profile_compatibility(profile, subject_profile)]
                        obligations = list(verb.get("obligations", []))
                        if "conflict" in agreement:
                            obligations.append("PERSON_AGREEMENT_CONFLICT")
                        claim = self.claim(predicate["lexical_features"]["lemma"], [subject["entity"]],
                                           positive, tense, time, place, restriction)
                        relation = {"kind": "relative_clause", "relative_span": tokens[1]["span"],
                                    "verb_span": tokens[2]["span"], "antecedent_span": tokens[0]["span"],
                                    "return_kind": "qualified_implicit_third_singular_subject",
                                    "return_reference": ret["reference_id"], "separate_world_assertion": False}
                        result.append(self.analysis(tokens, frame="relative_subject_predication", force=force,
                            refs=[subject["reference"], relref, ret], assignments=[subject["assignment"],
                                  self.assignment(tokens[2], verb, "imperfect_indicative"),
                                  self.assignment(tokens[3], predicate, predicate_role, head=tokens[0])],
                            readings=[subject["reading"], relative, verb, predicate], claims=[claim], relations=[relation],
                            obligations=obligations, supports=[self.support("relative_return"),
                                self.support("imperfect_indicative"), self.support("nominal_predication")]))
        return result

    def nominal_relative(self, tokens, *, force, subject_role, predicate_role, positive,
                         tense, time, place, restriction, head=None):
        """Definite head + relative + overt resumptive + predicate + predicate.

        The inner nominal predication must itself be syntactically complete.
        Its overt third-person pronoun returns to this relative's own head;
        it is never resolved by recency or promoted to a separate assertion.
        """
        result = []
        for subject in self.referents(tokens[0], subject_role, head=head):
            subject_row = subject["reading"]
            if (subject_row["lexical_features"].get("pos") not in ("PN", "PRON", "DEM")
                    and subject_row.get("al_evidence") != 1):
                continue
            for relative in self.readings(tokens[1]):
                if relative["lexical_features"].get("pos") != "REL":
                    continue
                relative_profile = _profile(relative)
                relref = self.reference(tokens[1]["surface"], origin="relative_return",
                    profile=relative_profile, context=self.context, mentions=self.mentions,
                    span=tokens[1]["span"], scope=self.scope, return_entity=subject["entity"])
                for pronoun in self.readings(tokens[2]):
                    profile = _profile(pronoun)
                    if (pronoun["lexical_features"].get("pos") != "PRON" or profile.get("person") != 3
                            or not pronoun.get("segmentation", {}).get("licensed")
                            or pronoun.get("person_evidence", {}).get("attached_pronouns")):
                        continue
                    returned = self.reference(tokens[2]["surface"], origin="relative_return",
                        profile=profile, context=self.context, mentions=self.mentions,
                        span=tokens[2]["span"], scope=self.scope, return_entity=subject["entity"])
                    compatibility = [profile_compatibility(relative_profile, _profile(subject_row)),
                                     profile_compatibility(profile, relative_profile),
                                     profile_compatibility(profile, _profile(subject_row))]
                    obligations = ["PERSON_AGREEMENT_CONFLICT"] if "conflict" in compatibility else []
                    for inner, outer in product(self.predicates(tokens[3]), self.predicates(tokens[4])):
                        claim = self.claim(outer["lexical_features"]["lemma"], [subject["entity"]],
                                           positive, tense, time, place, restriction)
                        relation = {"kind": "relative_clause", "relative_span": tokens[1]["span"],
                            "antecedent_span": tokens[0]["span"], "return_span": tokens[2]["span"],
                            "inner_predicate_span": tokens[3]["span"],
                            "inner_predicate_reading_id": inner["reading_id"],
                            "inner_predicate_lemma": inner["lexical_features"]["lemma"],
                            "return_kind": "explicit_third_person_nominal_subject",
                            "return_reference": returned["reference_id"], "separate_world_assertion": False}
                        result.append(self.analysis(tokens, frame="nominal_relative_subject_predication", force=force,
                            refs=[subject["reference"], relref, returned],
                            assignments=[subject["assignment"],
                                self.assignment(tokens[2], pronoun, "nominal_subject"),
                                self.assignment(tokens[3], inner, "nominal_predicate", head=tokens[2]),
                                self.assignment(tokens[4], outer, predicate_role, head=head or tokens[0])],
                            readings=[subject_row, relative, pronoun, inner, outer], claims=[claim],
                            relations=[relation], obligations=obligations,
                            supports=[self.support("relative_return"), self.support("nominal_predication")]))
        return result

    def parse(self, tokens, *, question=False, inherited_force=None, depth=0):
        """Retain whole-word and witnessed attached-interrogative readings.

        Splitting an initial hamza is a candidate in the declared written
        question convention. It neither removes a lexical hamza nor chooses
        between a named whole word and a different named remainder.
        """
        results = self._parse_unprefixed(tokens, question=question,
                                         inherited_force=inherited_force, depth=depth)
        if (question and tokens and tokens[0]["kind"] == "written_run"
                and inherited_force in (None, "QUESTION")):
            token = tokens[0]
            clusters = lookup_clusters(token["surface"])
            if (len(clusters) > 1 and clusters[0][0] == "أ"
                    and clusters[0][1] <= set("َ")):
                prefix = _slice(self.source, token, 0, clusters[0][3], "interrogative_prefix")
                remainder = _slice(self.source, token, clusters[1][2], len(token["surface"]),
                                   "interrogative_prefix")
                alternatives = self._parse_unprefixed([prefix, remainder] + tokens[1:],
                    question=True, inherited_force=inherited_force, depth=depth + 1)
                for row in alternatives:
                    row["relations"].append({"kind": "interrogative_prefix",
                        "prefix_span": prefix["span"], "remainder_span": remainder["span"],
                        "parent_span": token["span"], "scope": "complete_question"})
                    row["analysis_id"] = identity({k: v for k, v in row.items() if k != "analysis_id"})
                results.extend(alternatives)
        if len(results) > MAX_ANALYSES:
            raise resource_limit("Discourse alternatives exceed the per-clause budget", maximum=MAX_ANALYSES)
        return results

    def _parse_unprefixed(self, tokens, *, question=False, inherited_force=None, depth=0):
        if depth > 8:
            raise resource_limit("Discourse attachment depth exceeds its budget")
        if not tokens or any(t["kind"] != "written_run" for t in tokens):
            return []
        original = list(tokens)
        body = list(tokens)
        # A written question boundary blocks assertion even without هل. This
        # is a declared punctuation convention, not a claim about all speech.
        force = inherited_force or ("QUESTION" if question else "ASSERT")
        subject_role, predicate_role = "nominal_subject", "nominal_predicate"
        positive, tense, restriction = True, "unspecified", []
        head, mood, wh = None, None, None
        extra, supports = [], []
        first = lookup_key(body[0]["surface"])
        if first in ("هل", "أ"):
            if not template_matches(body[0]["surface"], {"هل": "هَلْ", "أ": "أَ"}[first], mutable_last=False):
                return []
            force = "QUESTION"
            supports.append(self.support("polar_interrogative"))
            body = body[1:]
        elif first in ("من", "ماذا", "أين", "متى", "كيف") and question:
            template = {"من": "مَنْ", "ماذا": "مَاذَا", "أين": "أَيْنَ", "متى": "مَتَى", "كيف": "كَيْفَ"}[first]
            if not template_matches(body[0]["surface"], template, mutable_last=False):
                return []
            if first == "من" and template_matches(body[0]["surface"], "مَنْ", mutable_last=False):
                wh, force = "subject", "QUESTION"
            elif first == "ماذا":
                wh, force = "object", "QUESTION"
                body = body[1:] + body[:1]
            elif first in ("أين", "متى"):
                wh, force = ("place" if first == "أين" else "time"), "QUESTION"
                body = body[1:]
            else:
                return []
            supports.append(self.support("wh_subject"))
        if not body:
            return []
        construction_body = list(body)
        from .construction_reader import operator_frames
        operator_rows = operator_frames(self, body, force=force, wh=wh, depth=depth)
        if operator_rows is not None:
            results = []
            for row in operator_rows:
                obligations = list(row["obligations"])
                # This bounded question profile has no license for hal over
                # an overt negative matrix. Recognize the fresh, source-bound
                # matrix analysis, not the substring "hal ma": relative ma,
                # interrogative ma and continuative ma-zala are different
                # constructions. Hamza retains its separate question route.
                # The classical norm and its scope limits are recorded in
                # evidence/arabic_coverage/oracle_audit_v1/question_input_audit.json.
                if (first == "هل" and row["force"] == "QUESTION" and
                        any(r.get("kind") == "matrix_negation" and
                            r.get("scope") == "epistemic_matrix" and
                            r.get("head_span") == body[0]["span"] for r in row["relations"]) and
                        any(s.get("rule") == "matrix_ma_negation" and
                            s.get("policy_sha256") == self.construction_policy["policy_sha256"]
                            for s in row["supports"])):
                    obligations.append("NEGATIVE_POLAR_QUESTION_REQUIRES_LICENSE")
                rebuilt = self.analysis(original, frame=row["frame"], force=row["force"],
                    refs=row["references"], assignments=row["assignments"],
                    readings=[r for rid in row["reading_ids"] if (r := self._reading_by_id(rid)) is not None],
                    claims=row["claims"], obligations=obligations,
                    supports=row["supports"] + supports, relations=row["relations"])
                rebuilt["question_kind"] = row.get("question_kind")
                rebuilt["analysis_id"] = identity({k: v for k, v in rebuilt.items() if k != "analysis_id"})
                results.append(rebuilt)
            return results
        key = lookup_key(body[0]["surface"])
        if key in ("يا", "لا", "لن", "لم", "سوف"):
            head, body = body[0], body[1:]
            template = {"يا": "يَا", "لا": "لَا", "لن": "لَنْ", "لم": "لَمْ", "سوف": "سَوْفَ"}[key]
            if not template_matches(head["surface"], template, mutable_last=False):
                return []
            if key == "يا":
                force = "VOCATIVE"
                extra.append("VOCATIVE_CLAUSE_OUTSIDE_ASSERTIVE_FRAMES")
            elif key == "لا":
                force = "AMBIGUOUS"
                extra.append("LA_NEGATION_PROHIBITION_AND_SCOPE_UNRESOLVED")
            elif key in ("لم", "لن"):
                if key == "لم" and "َ" not in lookup_clusters(head["surface"])[0][1]:
                    extra.append("LAM_NEGATION_VOCALIZATION_EVIDENCE")
                positive = False
                tense = "past" if key == "لم" else "future"
                mood = "imperfect_jussive" if key == "لم" else "imperfect_subjunctive"
                supports.append(self.support("imperfect_prefix"))
            elif key == "سوف":
                tense = "future"
                supports.append(self.support("deictic_adverbs"))
        if not body:
            return []
        results = []
        for complement in self.complements(body):
            reduced = complement["tokens"]
            qtime = ["?time"] if wh == "time" else complement["time"]
            qplace = ["?place"] if wh == "place" else complement["place"]
            options = dict(force=force, subject_role=subject_role, predicate_role=predicate_role,
                           positive=positive, tense=tense, time=qtime, place=qplace,
                           restriction=restriction, head=head, wh=wh)
            parsed = []
            if not mood and key != "سوف" and not complement["requires_event"]:
                parsed.extend(self.nominal(reduced, **options))
                parsed.extend(self.idafa(reduced, **options))
                parsed.extend(self.attached_nominal(reduced, **options))
                parsed.extend(self.relative(reduced, **options))
                loc_options = {k: v for k, v in options.items() if k != "predicate_role"}
                parsed.extend(self.location(reduced, **loc_options))
            if key not in ("إن", "كان", "ليس", "ليت", "لعل", "يا"):
                voptions = {k: v for k, v in options.items() if k not in ("subject_role", "predicate_role")}
                parsed.extend(self.verbal(reduced, mood=mood, **voptions))
            for row in parsed:
                # Rebuild rather than toggling a successful status. Complements,
                # operators and all qualification participate in one analysis.
                readings = [self._reading_by_id(rid) for rid in row["reading_ids"]]
                readings = [r for r in readings if r is not None] + complement["readings"]
                rebuilt = self.analysis(original, frame=row["frame"], force=row["force"],
                    refs=row["references"] + complement["refs"],
                    assignments=row["assignments"] + complement["assignments"], readings=readings,
                    claims=row["claims"], obligations=row["obligations"] + extra + complement["obligations"],
                    supports=row["supports"] + supports + complement["supports"], relations=row["relations"])
                rebuilt["question_kind"] = wh or "polar" if rebuilt["force"] == "QUESTION" else None
                rebuilt["analysis_id"] = identity({k: v for k, v in rebuilt.items() if k != "analysis_id"})
                results.append(rebuilt)
        if wh is None:
            from .construction_reader import nominal_frames, verbal_frames, event_modifiers
            from .construction_complements import adverbial_frames, quantified_frames
            extensions = (nominal_frames(self, construction_body, force=force) +
                          verbal_frames(self, construction_body, force=force) +
                          event_modifiers(self, construction_body, force=force, depth=depth) +
                          adverbial_frames(self, construction_body, force=force, depth=depth) +
                          quantified_frames(self, construction_body, force=force))
            for row in extensions:
                rebuilt = self.analysis(original, frame=row["frame"], force=row["force"],
                    refs=row["references"], assignments=row["assignments"],
                    readings=[r for rid in row["reading_ids"] if (r := self._reading_by_id(rid)) is not None],
                    claims=row["claims"], obligations=row["obligations"], supports=row["supports"] + supports,
                    relations=row["relations"])
                rebuilt["question_kind"] = "polar" if rebuilt["force"] == "QUESTION" else None
                rebuilt["analysis_id"] = identity({k: v for k, v in rebuilt.items() if k != "analysis_id"})
                results.append(rebuilt)
        if len(results) > MAX_ANALYSES:
            raise resource_limit("Discourse alternatives exceed the per-clause budget", maximum=MAX_ANALYSES)
        # Complete positive clauses may share a conjunction. Scope under
        # negation, a question or a request is never distributed by this rule.
        if force == "ASSERT" and head is None and wh is None:
            for i in range(1, len(original) - 1):
                token = original[i]
                clusters = lookup_clusters(token["surface"])
                key_at = lookup_key(token["surface"])
                if key_at == "و":
                    if not template_matches(token["surface"], "وَ", mutable_last=False):
                        continue
                    left, right = original[:i], original[i + 1:]
                    connector_span = token["span"]
                elif key_at and key_at.startswith("و") and len(clusters) > 1 and clusters[0][1] <= set("َ"):
                    left = original[:i]
                    right = [_slice(self.source, token, clusters[1][2], len(token["surface"]), "conjunction_prefix")] + original[i + 1:]
                    connector_span = _slice(self.source, token, 0, clusters[0][3], "conjunction_prefix")["span"]
                else:
                    continue
                lrows, rrows = self.parse(left, depth=depth + 1), self.parse(right, depth=depth + 1)
                for lrow, rrow in product(lrows, rrows):
                    if lrow["force"] != "ASSERT" or rrow["force"] != "ASSERT":
                        continue
                    permitted = coordination_projection("AND", "positive")
                    row = self.analysis(original, frame="complete_clause_conjunction", force="ASSERT",
                        refs=lrow["references"] + rrow["references"],
                        assignments=lrow["assignments"] + rrow["assignments"],
                        readings=[r for rid in lrow["reading_ids"] + rrow["reading_ids"]
                                  if (r := self._reading_by_id(rid)) is not None],
                        claims=lrow["claims"] + rrow["claims"] if permitted else [],
                        obligations=lrow["obligations"] + rrow["obligations"],
                        supports=lrow["supports"] + rrow["supports"] + [self.support("clause_conjunction")],
                        relations=[{"kind": "AND", "span": connector_span, "scope": "two_complete_clauses"}])
                    row["question_kind"] = None
                    row["analysis_id"] = identity({k: v for k, v in row.items() if k != "analysis_id"})
                    results.append(row)
                    if len(results) > MAX_ANALYSES:
                        raise resource_limit("Discourse coordination exceeds the alternative budget")
        return results

    def _reading_by_id(self, rid):
        return self.derived.get(rid) or next((r for rows in self.cache.values() for r in rows if r["reading_id"] == rid), None)


def _clauses(source, segments):
    clauses, current = [], []
    for segment in segments:
        if segment["kind"] == "spacing":
            if "\n" in segment["surface"] and current:
                clauses.append((current, False))
                current = []
            continue
        if segment["kind"] == "punctuation" and segment["surface"] in (".", "؛", "!", "؟", "?"):
            if current:
                clauses.append((current, segment["surface"] in ("؟", "?")))
                current = []
            continue
        current.append(_token(source, segment))
    if current:
        clauses.append((current, False))
    if len(clauses) > MAX_CLAUSES:
        raise resource_limit("Discourse clause budget exceeded", maximum=MAX_CLAUSES)
    return clauses


def _semantic_key(analysis):
    return wire({"force": analysis["force"], "claims": sorted(analysis["claims"], key=wire),
                 "question_kind": analysis.get("question_kind")})


def read_discourse(text, *, lexical_model=None, context=None, source_id="input", scope="default"):
    """Read complete bounded clauses, retaining original bytes and alternatives."""
    source = _source(text, source_id, scope)
    engine = _Reader(source, scope, lexical_model, context)
    segments = _scan(source)
    reports, claims = [], []
    for tokens, interrogative in _clauses(source, segments):
        quoted = len(tokens) == 1 and tokens[0]["kind"] == "quotation"
        analyses = [] if quoted else engine.parse(tokens, question=interrogative)
        viable = [a for a in analyses if not a["rejected_candidate"]]
        complete = [a for a in viable if a["licensed_syntax"] and a["references_complete"]]
        # An unresolved full parse is not discarded merely because another
        # analysis happens to resolve a convenient entity or case.
        licensed = bool(complete) and len(complete) == len(viable) and len({_semantic_key(a) for a in complete}) == 1
        status = "MENTION" if quoted else "LICENSED" if licensed else "DEFER"
        span = span_dict(_span(source, tokens[0]["span"]["start"], tokens[-1]["span"]["end"]))
        clause = {"span": span, "status": status, "force": "QUOTED" if quoted else
                  complete[0]["force"] if licensed else "AMBIGUOUS",
                  "analyses": analyses, "obligations": [] if licensed or quoted else
                  sorted({o for a in analyses for o in a["obligations"]}) or ["COMPLETE_SUPPORTED_CLAUSE_READING"]}
        clause["clause_id"] = identity(clause)
        if licensed:
            for analysis in complete:
                if analysis["assertion_allowed"]:
                    for claim in analysis["claims"]:
                        claim_id = identity([source.source_id, source.sha256, scope, engine.context["sha256"], claim])
                        existing = next((c for c in claims if c["claim_id"] == claim_id), None)
                        evidence = {"clause_id": clause["clause_id"], "analysis_id": analysis["analysis_id"], "span": span}
                        if existing is None:
                            claims.append({"claim_id": claim_id, **deepcopy(claim), "proofs": [evidence]})
                        else:
                            existing["proofs"].append(evidence)
                if analysis["force"] == "ASSERT":
                    for reference in analysis["references"]:
                        eid = reference["bound_entity_id"]
                        if eid is None or eid.startswith("?"):
                            continue
                        features = reference.get("profile", {})
                        mention = {"entity_id": eid, "scope": scope, "quoted": False,
                                   "span": reference["span"], "reference_id": reference["reference_id"],
                                   "gender": features.get("gender"), "number": features.get("number")}
                        if mention not in engine.mentions:
                            engine.mentions.append(mention)
        reports.append(clause)
        if status == "DEFER":
            engine.source_prefix_complete = False
    occurrences = []
    from .governors import lookup
    for segment in segments:
        if segment["kind"] not in ("written_run", "quotation"):
            continue
        token = _token(source, segment)
        key = lookup_key(token["surface"])
        readings = [] if token["kind"] == "quotation" else engine.readings(token)
        operator = _OPERATORS.get(key)
        occurrences.append({**token, "readings": deepcopy(readings),
                            "operator_candidates": [] if operator is None else [{"rule": operator[0], "interpretation": operator[1],
                                "authority": "GRAMMATICAL_CANDIDATE_REQUIRING_COMPLETE_FRAME"}],
                            "governor_candidates": [] if key is None or len(key) > 128 else [asdict(e) for e in lookup(key)]})
    status = "LICENSED_DISCOURSE" if reports and all(c["status"] != "DEFER" for c in reports) else "DEFER"
    result = {"schema": "nabt.discourse-report.v1", "language_id": LANGUAGE_ID, "reader_version": READER_VERSION,
              "law_id": LAW_ID, "law_sha256": EXPECTED_TABLE_SHA256,
              "policy_sha256": engine.policy["policy_sha256"],
              "construction_law_id": CONSTRUCTION_LAW_ID,
              "construction_law_sha256": CONSTRUCTION_TABLE_SHA256,
              "construction_policy_sha256": engine.construction_policy["policy_sha256"],
              "source_id": source.source_id, "source_sha256": source.sha256,
              "source_text": source.raw_bytes.decode("utf-8"), "scope": scope,
              "context": engine.context, "lexical_model": engine.model_summary,
              "partition": segments, "occurrences": occurrences,
              "derived_readings": [deepcopy(r) for rid, r in engine.derived.items()
                                   if not any(rid == existing["reading_id"] for o in occurrences for existing in o["readings"])],
              "clauses": reports,
              "claims": claims, "status": status,
              "authority": "SOURCE_RELATIVE_BOUNDED_DISCOURSE_NOT_WORLD_TRUTH",
              "world_truth": "NOT_ESTABLISHED"}
    result["report_id"] = identity(result)
    wire(result)
    return result


def verify_discourse(report, *, text=_UNSET, lexical_model=None, context=None,
                     source_id=None, scope=None):
    """Recompute from original sources; supplied successes and hashes are inert."""
    try:
        if type(report) is not dict:
            return {"valid": False, "status": "REJECT", "code": "INVALID_DISCOURSE_REPORT"}
        raw = report["source_text"] if text is _UNSET else text
        fresh = read_discourse(raw, lexical_model=lexical_model, context=context,
                               source_id=report["source_id"] if source_id is None else source_id,
                               scope=report["scope"] if scope is None else scope)
        if wire(report) != wire(fresh):
            return {"valid": False, "status": "REJECT", "code": "DISCOURSE_REPLAY_MISMATCH"}
        return {"valid": True, "status": "VERIFIED", "report_id": fresh["report_id"],
                "authority": "TEXT_CONTEXT_AND_LEXICAL_SOURCE_REPLAY_ONLY"}
    except (KeyError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, NabtError) and error.status == "DEFER":
            return {"valid": False, "status": "DEFER", "code": error.code}
        return {"valid": False, "status": "REJECT", "code": "INVALID_DISCOURSE_REPORT"}
