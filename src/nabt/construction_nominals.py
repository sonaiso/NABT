"""A narrow, source-attested accusative-alif bridge for nominal readings.

No word is generated. Both the complete written carrier form and an ordinary
paired base paradigm must already occur in the independent lexical source.
The case/mood labels remain masked. The bridge supplies neither a dependency
nor a world referent; the reader must establish those separately.
"""

from copy import deepcopy
import json

from .corpus_evidence import lookup_clusters, lookup_key, template_matches
from .discourse_context import identity
from .text_ir import span_dict
from .word_reader import _span


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
        full = []
        for encoded in index.get(key, ()):
            entry = json.loads(encoded)
            form = lookup_clusters(entry["form"])
            if (same(entry) and not entry.get("annotation_only") and form and
                    len(form) == len(clusters) and form[-2][1] & set("ًٌٍَُِْ") == {"ً"} and
                    not form[-1][1] and template_matches(surface, entry["template"], mutable_last=False)):
                full.append(entry)
        base_surface = surface[:clusters[-1][2]]
        base = []
        for encoded in index.get(key[:-1], ()):
            entry = json.loads(encoded)
            if (same(entry) and entry.get("construction") == "inflected" and entry.get("class_candidates") == [0]
                    and entry.get("construction_basis") == "paired_lexical_terminal_realizations" and
                    template_matches(base_surface, entry["template"], mutable_last=True)):
                base.append(entry)
        if not full or not base:
            result.append(row)
            continue
        start = row["stem_span"]["start"]
        carrier_start = start + len(base_surface.encode("utf-8"))
        base_span = span_dict(_span(source, start, carrier_start))
        carrier_span = span_dict(_span(source, carrier_start, row["stem_span"]["end"]))
        support = {"kind": "source_attested_nominal_carrier", "rule": "attested_accusative_alif",
                   "policy_sha256": policy["policy_sha256"], "passage": policy["rules"]["attested_accusative_alif"],
                   "full_form_supports": [s for e in full for s in e["supports"]],
                   "base_paradigm_supports": [s for e in base for s in e["construction_supports"]],
                   "base_surface": base_surface, "base_span": base_span,
                   "carrier_surface": surface[clusters[-1][2]:], "carrier_span": carrier_span,
                   "generated_form": False}
        row = deepcopy(row)
        row.update(construction="inflected", class_candidates=[0], possible_cases=[0],
                   construction_basis="attested_carrier_and_independent_paired_base",
                   nominal_case_carrier=support)
        row["obligations"] = [o for o in row.get("obligations", []) if o not in
                              ("CONSTRUCTION_EVIDENCE", "OBSERVED_FORM_CONFLICTS_WITH_CONDITIONAL_SIGN_LAW")]
        row["support_records"].append(support)
        row["reading_id"] = identity([original["reading_id"], support])
        for nun in row.get("nun_readings", []):
            nun["reading_id"] = row["reading_id"]
        result.append(row)
    return result
