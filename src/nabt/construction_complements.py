"""Witnessed adverbial attachments and a bounded counted-noun construction."""

from copy import deepcopy
from itertools import product

from .corpus_evidence import lookup_key
from .discourse_context import identity
from .discourse_adverbs import adverb_candidates
from .discourse_reader import _profile, _synthetic_reading
from .construction_reader import (_support, _relation, _extend, _build, _with_question,
    _limit, _reading_obligations, _definite, _np_atom, noun_phrases, _clause_token)

# These regular, inflected adverb heads are explicitly bounded by the Qatr
# passage about directions, عند, and time nouns. A new occurrence must also
# have a matching independent T/LOC lexical source, with no role/case labels.
_SPATIAL_HEADS = frozenset(("أمام", "خلف", "فوق", "تحت", "يمين", "شمال", "عند"))
_TEMPORAL_HEADS = frozenset(("يوم", "حين", "أسبوع"))
_TENS = frozenset(("عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"))


def _predicate_token(reader, tokens, base):
    # Prefer the actual verbal head, not the first token of an SVO sentence.
    for rid in base["reading_ids"]:
        reading = reader._reading_by_id(rid)
        if reading is not None and reading["kind"] == "verb":
            for token in tokens:
                if (token["span"]["start"] <= reading["stem_span"]["start"] and
                        reading["stem_span"]["end"] <= token["span"]["end"]):
                    return token
    predicate = next((a for a in base["assignments"] if a["role"] == "nominal_predicate"), None)
    if predicate is not None:
        return next((t for t in tokens if t["span"] == predicate["span"]), tokens[0])
    return tokens[0]


def adverbial_frames(reader, tokens, *, force, depth):
    """Attach a source-tagged adverb + independently resolved genitive NP.

    The retained spatial/temporal relation is a textual qualification, not a
    claim of ownership, a world coordinate, or a guessed attachment to the
    nearest noun. Multiple qualified parses remain separate alternatives.
    """
    results = []
    for index in range(1, len(tokens) - 1):
        head = tokens[index]
        key = lookup_key(head["surface"])
        if key not in _SPATIAL_HEADS | _TEMPORAL_HEADS:
            continue
        sources = [a for a in adverb_candidates(head["surface"], lexical_model=reader.model)
                   if a["pos"] == ("LOC" if key in _SPATIAL_HEADS else "T") and not a["source_article"]]
        if not sources:
            continue
        complements = noun_phrases(reader, tokens[index + 1:], "idafa_complement", head=head)
        if not complements:
            continue
        bases = reader.parse(tokens[:index], inherited_force=force, depth=depth + 1)
        for source, complement in product(sources, complements):
            spatial = source["pos"] == "LOC"
            field, role = ("place", "place_adverb") if spatial else ("time", "time_adverb")
            reading = _synthetic_reading(head, pos=source["pos"], construction="inflected", classes=(0,),
                                         rule="temporal_spatial_attachment")
            reading["support_records"] = source["supports"]
            reading["lexical_features"]["lemma"] = source["lemma"]
            reading["reading_id"] = identity([reading["reading_id"], source["id"], source["supports"]])
            qualification = {"kind": "spatial_relation" if spatial else "temporal_relation",
                             "relation": source["lemma"], "object": complement["entity"]}
            if complement["restriction"]:
                qualification["qualifiers"] = complement["restriction"]
            for base in bases:
                if (not base["licensed_syntax"] or not base["references_complete"] or base["rejected_candidate"] or
                        len(base["claims"]) != 1 or base["claims"][0][field]):
                    continue
                predicate = _predicate_token(reader, tokens[:index], base)
                assigned = reader.assignment(head, reading, role, head=predicate, idhafa=True)
                claims = deepcopy(base["claims"])
                claims[0][field].append(qualification)
                relations = [_relation(role, predicate, head, complement_span=complement["root"]["span"],
                    relation_lemma=source["lemma"], dependent_reading_id=reading["reading_id"],
                    ownership_asserted=False), _relation("idafa", head, complement["root"],
                    complement_span=complement["root"]["span"], ownership_asserted=False)] + complement["relations"]
                results.append(_extend(reader, tokens, base, readings=[reading] + complement["readings"],
                    assignments=[assigned] + complement["assignments"], refs=complement["refs"],
                    relations=relations, claims=claims, obligations=complement["obligations"],
                    supports=[_support(reader, "temporal_spatial_attachment"), _support(reader, "idafa_chain")] + complement["supports"],
                    frame="predication_with_" + role))
                _limit(results)
            # A spatial phrase can itself predicate a location. The lexical
            # adverb's accusative and the predicate constituent's local raf
            # are distinct. A time noun does not predicate a bare individual.
            if spatial and index == 1:
                for subject in _np_atom(reader, tokens[0], "nominal_subject", None):
                    assigned = reader.assignment(head, reading, role, head=tokens[0], idhafa=True)
                    phrase = _clause_token(reader, tokens[index:])
                    phrase_reading = _synthetic_reading(phrase, pos="ADVERBIAL_PHRASE", rule="temporal_spatial_attachment")
                    phrase_assignment = reader.assignment(phrase, phrase_reading, "nominal_predicate", head=tokens[0])
                    phrase_assignment["case_domain"] = "phrase_local_case"
                    claim = reader.claim("@located", [subject["entity"]], True, "unspecified", [], [qualification], subject["restriction"])
                    claim["predicate_kind"] = "location"
                    relations = [_relation("place_adverb", tokens[0], head, complement_span=complement["root"]["span"],
                        relation_lemma=source["lemma"], phrase_local_case="raf", ownership_asserted=False),
                        _relation("idafa", head, complement["root"], complement_span=complement["root"]["span"], ownership_asserted=False)]
                    row = _build(reader, tokens, frame="spatial_adverbial_predication", force=force,
                        parts=[subject, complement], readings=[reading, phrase_reading],
                        assignments=[assigned, phrase_assignment], claims=[claim], relations=relations,
                        supports=[_support(reader, "temporal_spatial_attachment"), _support(reader, "idafa_chain"), reader.support("nominal_predication")])
                    results.append(_with_question(row))
                    _limit(results)
    return results


def quantified_frames(reader, tokens, *, force):
    """Tens + a singular, indefinite counted noun in a complete verbal frame.

    The numeral itself needs a source-qualified inflection family. The result
    preserves its source lemma as a quantified nominal term. It neither
    invents individual entity IDs nor asserts an independently counted world
    cardinality. Compound teens and coordinated numerals remain outside this
    acquisition grammar, although the separate conditional number law is wider.
    """
    if len(tokens) not in (3, 4):
        return []
    vtoken, ntoken, unit_token = tokens[0], tokens[-2], tokens[-1]
    numerals = [r for r in reader.readings(ntoken) if r["kind"] == "noun" and
        lookup_key(r["lexical_features"].get("lemma") or "") in _TENS and
        r.get("class_candidates") == [3] and _definite(r) == "indefinite" and
        not r.get("annotation_only") and not r.get("prefix_relation") and
        not r.get("person_evidence", {}).get("attached_pronouns")]
    units = [r for r in reader.predicates(unit_token) if r["lexical_features"].get("pos") == "N" and
             _profile(r).get("number") == "singular" and _definite(r) == "indefinite"]
    results = []
    for verb, numeral, unit in product(reader.verbs(vtoken), numerals, units):
        f, profile = verb["lexical_features"], _profile(verb)
        if f.get("aspect") not in ("PERF", "IMPF") or verb.get("person_evidence", {}).get("attached_pronouns"):
            continue
        voice = f.get("voice") or "active"
        term = {"kind": "quantified_nominal", "numeral": numeral["lexical_features"]["lemma"],
                "unit": unit["lexical_features"]["lemma"]}
        assignments, parts, obligations = [], [], list(verb.get("obligations", []))
        witnesses = verb.get("person_evidence", {}).get("valency_witnesses", [])
        if len(tokens) == 3 and profile.get("person") == 3:
            nrole = "active_subject" if voice == "active" else "passive_subject"
            subjects = [None]
            if profile.get("number") != "singular":
                obligations.append("CONSTRUCTION_CONFLICT")
            gender = _profile(unit).get("gender")
            if gender is None:
                obligations.append("COUNTED_NOUN_GENDER_REQUIRED")
            elif gender != profile.get("gender"):
                obligations.append("CONSTRUCTION_CONFLICT")
        elif voice == "active" and witnesses:
            nrole = "direct_object"
            if len(tokens) == 4:
                subjects = _np_atom(reader, tokens[1], "active_subject", vtoken)
            else:
                origin = {1: "speaker", 2: "addressee"}.get(profile.get("person"))
                if origin is None:
                    continue
                reference = reader.reference(vtoken["surface"], origin=origin, profile=profile,
                    context=reader.context, mentions=reader.mentions, span=vtoken["span"], scope=reader.scope)
                subjects = [{"entity": reference["bound_entity_id"], "refs": [reference], "readings": [],
                    "assignments": [], "relations": [], "restriction": [], "obligations": [], "supports": []}]
        else:
            continue
        for subject in subjects:
            local = list(obligations)
            if subject is not None and len(tokens) == 4:
                local += reader._agreement(verb, subject, before_subject=True)
            parts = [subject] if subject else []
            args = [subject["entity"], term] if subject else [term]
            assignments = [reader.assignment(ntoken, numeral, nrole, head=vtoken),
                           reader.assignment(unit_token, unit, "tamyiz", head=ntoken)]
            if f["aspect"] == "IMPF":
                assignments.append(reader.assignment(vtoken, verb, "imperfect_indicative"))
            claim = reader.claim(f["lemma"], args, True, "past" if f["aspect"] == "PERF" else "nonpast", [], [],
                [{"kind": "tamyiz", "subtype": "counted_tens", "numeral": term["numeral"], "unit": term["unit"]}])
            claim.update(predicate_kind="event", voice=voice)
            relation = _relation("tamyiz", ntoken, unit_token, subtype="counted_tens",
                cardinality_asserted_as_world_fact=False, head_reading_id=numeral["reading_id"],
                dependent_reading_id=unit["reading_id"])
            row = _build(reader, tokens, frame="verbal_counted_tens", force=force, parts=parts,
                readings=[verb, numeral, unit], assignments=assignments, claims=[claim], relations=[relation],
                obligations=local + _reading_obligations(numeral) + _reading_obligations(unit),
                supports=[_support(reader, "tamyiz_measure"), _support(reader, "counted_tens_forms"),
                    _support(reader, "counted_tens_specification"), _support(reader, "counted_tens_paradigm"),
                    reader.support("active_subject")] +
                    ([{"kind": "valency_source", "witnesses": witnesses}] if subject else []))
            results.append(_with_question(row))
            _limit(results)
    return results
