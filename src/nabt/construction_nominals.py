"""Source-bound nominal bridges with separate attested and productive laws.

Each productive form retains its independently paired lexical premise; it
never claims target attestation, a dependency or a grounded world referent.
"""

from copy import deepcopy
import json

from .corpus_evidence import VOWELS, lookup_clusters, lookup_key, template_matches
from .discourse_context import identity
from .text_ir import span_dict
from .word_reader import _span

NOMINAL_PARADIGM_RULE = "same_form_nominal_inflection"


def generate_accusative_alif(readings, base_readings, *, token, source, index):
    """Derive a new written form from an independently paired plain base.

    Existing full-form lexical alternatives are never replaced. This v1
    profile requires a completely vocalized target and a singular, ordinary
    source declension. Weak, hamza, article, possessive and plural cases stay
    outside it. The base is acquired afresh from the lexical source.
    """
    from .productive_forms import replay_policy, POLICY_SHA256
    if any(r.get("kind") == "noun" for r in readings):
        return readings
    shape = lookup_clusters(token["surface"])
    if (not shape or len(shape) < 3 or shape[-1][0] != "ا" or shape[-1][1] or
            shape[-2][1] & VOWELS != {"ً"} or shape[-2][0] in "ءأإآؤئىيةاو" or
            any(not marks & VOWELS and not (
                    not marks and i > 0 and letter in "اوي" and
                    shape[i - 1][1] & VOWELS == {{"ا": "َ", "و": "ُ", "ي": "ِ"}[letter]})
                for i, (letter, marks, _, _) in enumerate(shape[:-1]))):
        return readings
    policy = replay_policy()
    result = list(readings)
    base_surface = token["surface"][:shape[-1][2]]
    carrier_start = token["span"]["start"] + len(base_surface.encode())
    base_span = span_dict(_span(source, token["span"]["start"], carrier_start))
    carrier_span = span_dict(_span(source, carrier_start, token["span"]["end"]))
    for original in base_readings:
        f = original.get("lexical_features", {})
        if (original.get("kind") != "noun" or original.get("construction") != "inflected" or
                original.get("class_candidates") != [0] or original.get("variant") != "attested" or
                original.get("construction_basis") != "paired_lexical_terminal_realizations" or
                original.get("person_evidence") or original.get("prefix_relation") or
                original.get("al_evidence") != 2 or original.get("annotation_only") or
                original.get("stem_span") != base_span or
                f.get("number") != "singular" or f.get("pos") not in ("N", "ADJ", "PN") or
                not f.get("root") or lookup_key(f.get("lemma") or "") != lookup_key(base_surface) or
                not original.get("segmentation", {}).get("licensed")):
            continue
        entries = [json.loads(e) for e in index.get(lookup_key(base_surface), ())]
        own = [e for e in entries if e.get("lexical_id") == original.get("identity", {}).get("lexical_id")]
        if len(own) != 1 or len({s["record_id"] for s in own[0].get("construction_supports", [])}) < 2:
            continue
        entry = own[0]
        if _base_template(shape[:-1]) != _base_template(lookup_clusters(entry["form"])):
            continue
        witness = {"kind": "productive_nominal_carrier", "rule": "productive_accusative_alif",
            "law_id": "nabt.productive-accusative-alif.v1", "policy_sha256": POLICY_SHA256,
            "source_lexical_id": entry["lexical_id"], "source_form": entry["form"],
            "source_template": entry["template"], "base_surface": base_surface, "base_span": base_span,
            "carrier_surface": "ا", "carrier_span": carrier_span,
            "base_paradigm_supports": deepcopy(entry["construction_supports"]),
            "source_supports": deepcopy(entry["supports"]),
            "generated_form": True, "target_attested": False, "target_role_labels_used": False,
            "source_passage": next(p for p in policy["passages"] if p["source_id"] == "qatr" and p["line_start"] == 440)}
        row = deepcopy(original)
        row.update(stem_surface=token["surface"], stem_span=deepcopy(token["span"]),
                   variant="productive_accusative_alif", possible_cases=[0],
                   nominal_case_carrier=witness,
                   construction_basis="paired_base_and_productive_orthography")
        row["segmentation"] = {"licensed": True, "coverage_valid": True,
            "basis": "PRODUCTIVE_PAIRED_BASE", "parts": [
                {"kind": "nominal_stem", "surface": base_surface, "span": base_span},
                {"kind": "accusative_alif", "surface": "ا", "span": carrier_span}]}
        row["support_records"].append(witness)
        row["reading_id"] = identity([original["reading_id"], token["span"], witness])
        row["identity"] = {**row["identity"], "span": deepcopy(token["span"]),
                           "productive_source_reading_id": original["reading_id"]}
        row["obligations"] = [o for o in row.get("obligations", []) if o != "OBSERVED_FORM_CONFLICTS_WITH_CONDITIONAL_SIGN_LAW"]
        for nun in row.get("nun_readings", []):
            nun["reading_id"] = row["reading_id"]
        result.append(row)
    return result


def qualify_same_form_nominal(readings, *, index, policy):
    """Share an independently witnessed inflection, never lexical semantics.

    Both N and ADJ groups must themselves witness ordinary singular tanwin.
    A directly equal internal template, lemma, root, derivational features,
    gender and number is required. Unknown number, diptotes, PN, spelling
    normalization and reconstruction from the target are outside this rule.
    """
    result = []
    for original in readings:
        row = original
        ident = row.get("identity", {})
        person = row.get("person_evidence")
        if (row.get("kind") != "noun" or row.get("construction") is not None or
                row.get("annotation_only") or row.get("variant") != "attested" or
                row.get("nominal_case_carrier") or
                person is not None and (person.get("attached_pronouns") or
                    person.get("form_kind") != "nominal" or person.get("family") is not None or
                    not person.get("source_lexical_id")) or
                row.get("class_candidates") != [0]):
            result.append(row)
            continue
        entries = [json.loads(encoded) for encoded in index.get(lookup_key(row.get("stem_surface", "")), ())]
        lexical_id = ident.get("lexical_id") if person is None else person["source_lexical_id"]
        own = [entry for entry in entries if entry["lexical_id"] == lexical_id]
        if len(own) != 1:
            result.append(row)
            continue
        own = own[0]
        if (own.get("pos") not in ("N", "ADJ") or own.get("number") != "singular" or
                own.get("gender") not in ("masculine", "feminine") or
                not own.get("root") or not own.get("lemma_bw") or
                own.get("class_candidates") != [0] or not own.get("nominal_tanwin_supports") or
                own.get("construction") is not None or not own.get("supports") or
                any(own.get(k) != row.get("lexical_features", {}).get(k)
                    for k in ("pos", "lemma", "root", "gender", "number")) or
                any(s not in row.get("support_records", ()) for s in own["supports"])):
            result.append(row)
            continue
        fields = ("lemma_bw", "root", "template", "gender", "number", "nominal_derivation_features")
        donors = [entry for entry in entries if
            entry.get("kind") == "noun" and entry.get("pos") in ("N", "ADJ") and
            entry["pos"] != own["pos"] and not entry.get("annotation_only") and
            entry.get("variant") == "attested" and entry.get("construction") == "inflected" and
            entry.get("construction_basis") == "paired_lexical_terminal_realizations" and
            entry.get("class_candidates") == [0] and entry.get("nominal_tanwin_supports") and
            len({s["record_id"] for s in entry.get("construction_supports", ())}) >= 2 and
            all(entry.get(field) == own.get(field) for field in fields)]
        if not donors:
            result.append(row)
            continue
        witness = {"kind": "same_form_nominal_inflection", "rule": NOMINAL_PARADIGM_RULE,
            "policy_sha256": policy["policy_sha256"], "passage": policy["rules"][NOMINAL_PARADIGM_RULE],
            "recipient_lexical_id": own["lexical_id"], "recipient_pos": own["pos"],
            "shared_features": {field: deepcopy(own.get(field)) for field in fields},
            "recipient_tanwin_supports": deepcopy(own["nominal_tanwin_supports"]),
            "donors": [{"lexical_id": entry["lexical_id"], "pos": entry["pos"],
                "tanwin_supports": deepcopy(entry["nominal_tanwin_supports"]),
                "paired_terminal_supports": deepcopy(entry["construction_supports"])}
                for entry in sorted(donors, key=lambda e: e["lexical_id"])],
            "transferred_fields": ["construction"], "source_pos_preserved": True,
            "semantic_equivalence_claimed": False, "target_role_labels_used": False}
        row = deepcopy(original)
        row["construction"] = "inflected"
        row["construction_basis"] = "same_form_nominal_independent_pair"
        row["nominal_paradigm_correspondence"] = witness
        row["construction_supports"] = [deepcopy(s) for entry in donors for s in entry["construction_supports"]]
        row["support_records"].append(witness)
        row["obligations"] = [o for o in row.get("obligations", ()) if o != "CONSTRUCTION_EVIDENCE"]
        row["reading_id"] = identity([original["reading_id"], witness])
        for nun in row.get("nun_readings", ()):
            nun["reading_id"] = row["reading_id"]
        result.append(row)
    return result


def _base_template(clusters):
    """Exact internal source template, leaving only the case ending mutable.

    Compatibility with an unvocalized input is not transitive. The full-form
    witness and paired base must therefore agree directly with each other,
    including shadda and every observed internal vowel. Missing source marks
    do not manufacture the missing equality premise.
    """
    return tuple((letter, tuple(sorted(marks - VOWELS if i == len(clusters) - 1 else marks)))
                 for i, (letter, marks, _, _) in enumerate(clusters))


def qualify_attested_alif(readings, *, token, source, index, policy):
    result = []
    for original in readings:
        row = original
        features = row.get("lexical_features", {})
        surface = row.get("stem_surface", "")
        clusters = lookup_clusters(surface)
        # This guard deliberately excludes lexical final alif, hamza spelling,
        # taa marbuta, manqus and maqsur and all attached/prefixed forms.
        if (row.get("kind") != "noun" or row.get("annotation_only") or
                features.get("pos") not in ("N", "PN", "ADJ") or
                row.get("person_evidence", {}).get("attached_pronouns") or
                row.get("prefix_relation") or row.get("al_evidence") != 2 or
                not clusters or len(clusters) < 3 or clusters[-1][0] != "ا" or
                clusters[-1][1] or
                clusters[-2][0] in "ءأإآؤئىيةاو" or
                lookup_key(features.get("lemma") or "") != lookup_key(surface)[:-1]):
            result.append(row)
            continue
        key = lookup_key(surface)
        same = lambda entry: all(entry.get(field) == features.get(field) for field in
                                  ("pos", "lemma", "root", "gender", "number"))
        # The observed source, not an input label, witnesses the complete form
        # and its tanwin. Mark placement on the final alif itself is left out
        # of this profile until it has its own orthographic correspondence.
        full = {}
        for encoded in index.get(key, ()):
            entry = json.loads(encoded)
            form = lookup_clusters(entry["form"])
            if (same(entry) and not entry.get("annotation_only") and form and
                    len(form) == len(clusters) and form[-2][1] & set("ًٌٍَُِْ") == {"ً"} and
                    not form[-1][1] and template_matches(surface, entry["template"], mutable_last=False) and
                    any(s in row.get("support_records", ()) for s in entry["supports"])):
                # Bind this particular lexical reading to its own full-form
                # witness; a different matching template is an alternative.
                full.setdefault(_base_template(form[:-1]), []).append(entry)
        base_surface = surface[:clusters[-1][2]]
        base = {}
        for encoded in index.get(key[:-1], ()):
            entry = json.loads(encoded)
            if (same(entry) and entry.get("construction") == "inflected" and entry.get("class_candidates") == [0]
                    and entry.get("construction_basis") == "paired_lexical_terminal_realizations" and
                    template_matches(base_surface, entry["template"], mutable_last=True)):
                base.setdefault(_base_template(lookup_clusters(entry["form"])), []).append(entry)
        shared = full.keys() & base.keys()
        if not shared:
            result.append(row)
            continue
        start = row["stem_span"]["start"]
        carrier_start = start + len(base_surface.encode("utf-8"))
        base_span = span_dict(_span(source, start, carrier_start))
        carrier_span = span_dict(_span(source, carrier_start, row["stem_span"]["end"]))
        for template in sorted(shared):
            support = {"kind": "source_attested_nominal_carrier", "rule": "attested_accusative_alif",
                       "policy_sha256": policy["policy_sha256"], "passage": policy["rules"]["attested_accusative_alif"],
                       "full_form_supports": [s for e in full[template] for s in e["supports"]],
                       "base_paradigm_supports": [s for e in base[template] for s in e["construction_supports"]],
                       "shared_internal_template": [[letter, list(marks)] for letter, marks in template],
                       "template_basis": "DIRECT_SOURCE_TEMPLATE_EQUALITY_EXCEPT_CASE_ENDING",
                       "base_surface": base_surface, "base_span": base_span,
                       "carrier_surface": surface[clusters[-1][2]:], "carrier_span": carrier_span,
                       "generated_form": False}
            qualified = deepcopy(original)
            qualified.update(construction="inflected", class_candidates=[0], possible_cases=[0],
                       construction_basis="attested_carrier_and_independent_paired_base",
                       nominal_case_carrier=support)
            qualified["obligations"] = [o for o in qualified.get("obligations", []) if o not in
                                  ("CONSTRUCTION_EVIDENCE", "OBSERVED_FORM_CONFLICTS_WITH_CONDITIONAL_SIGN_LAW")]
            qualified["support_records"].append(support)
            qualified["reading_id"] = identity([original["reading_id"], support])
            for nun in qualified.get("nun_readings", []):
                nun["reading_id"] = qualified["reading_id"]
            result.append(qualified)
    return result
