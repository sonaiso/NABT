"""Bind an unvocalized naming premise to one independently read occurrence.

The context names an entity; it does not teach a lexical template. This narrow
bridge only restores a shadda already witnessed by the selected lexical entry.
It changes neither source bytes nor the context, and does not merge entities.
"""

from copy import deepcopy
import json

from .corpus_evidence import lookup_clusters, lookup_key, template_matches

LAW_ID = "nabt.source-bound-unvocalized-name.v1"


def unvocalized_name_matches(surface, declared):
    """Only an entirely unmarked naming premise enters this new profile."""
    clusters = lookup_clusters(declared)
    return bool(clusters and all(not c[1] for c in clusters) and
                lookup_key(surface) == lookup_key(declared))


def lexical_name_witness(token, reading, *, index, model_summary):
    """Replay a particular attested entry, never a caller's proposed receipt.

    The lexical index comes from immutable raw source and its exclusions.
    Carrier transformations, pronominal hosts, prefixes other than the article,
    dagger alif and context-only readings remain outside this profile.
    """
    surface = token["surface"]
    observed = lookup_clusters(surface)
    ident = reading.get("identity", {})
    segmentation = reading.get("segmentation", {})
    parts = segmentation.get("parts", [])
    stem = reading.get("stem_surface", "")
    if (not observed or not any("ّ" in c[1] for c in observed) or
            any("ٰ" in c[1] for c in observed) or
            reading.get("kind") != "noun" or reading.get("annotation_only") or
            reading.get("construction") != "inflected" or
            reading.get("construction_basis") != "paired_lexical_terminal_realizations" or
            reading.get("variant") != "attested" or
            reading.get("prefix_relation") or reading.get("nominal_case_carrier") or
            reading.get("person_evidence") or ident.get("span") != token["span"] or
            not segmentation.get("licensed") or not segmentation.get("coverage_valid") or
            [p.get("kind") for p in parts] not in (["nominal_stem"], ["article", "nominal_stem"]) or
            "".join(p["surface"] for p in parts) != surface or
            parts[-1].get("surface") != stem or
            parts[-1].get("span") != reading.get("stem_span") or
            parts[0]["span"]["start"] != token["span"]["start"] or
            parts[-1]["span"]["end"] != token["span"]["end"] or
            any(a["span"]["end"] != b["span"]["start"] for a, b in zip(parts, parts[1:])) or
            model_summary is None):
        return None
    if len(parts) == 2:
        article = lookup_clusters(parts[0]["surface"])
        if (not article or lookup_key(parts[0]["surface"]) != "ال" or
                any(c[1] & set("ّٰ") for c in article) or reading.get("al_evidence") != 1):
            return None
    matches = [entry for encoded in index.get(lookup_key(stem), ())
               for entry in (json.loads(encoded),)
               if entry.get("lexical_id") == ident.get("lexical_id")]
    if len(matches) != 1:
        return None
    entry = matches[0]
    if (entry.get("kind") != "noun" or entry.get("pos") not in ("N", "PN", "ADJ") or
            entry.get("annotation_only") or entry.get("variant") != "attested" or
            entry.get("construction") != "inflected" or
            entry.get("construction_basis") != "paired_lexical_terminal_realizations" or
            len({s["record_id"] for s in entry.get("construction_supports", ())}) < 2 or
            not entry.get("supports") or
            any(s not in reading.get("support_records", ()) for s in entry["supports"]) or
            any(entry.get(k) != reading.get("lexical_features", {}).get(k)
                for k in ("pos", "lemma", "root", "gender", "number")) or
            not template_matches(stem, entry["template"], mutable_last=True)):
        return None
    return {"kind": "source_bound_unvocalized_name", "law_id": LAW_ID,
            "reading_id": reading["reading_id"], "lexical_id": entry["lexical_id"],
            "occurrence_span": deepcopy(token["span"]), "stem_span": deepcopy(reading["stem_span"]),
            "source_template": entry["template"], "source_form": entry["form"],
            "construction_basis": entry["construction_basis"],
            "construction_supports": deepcopy(entry["construction_supports"]),
            "lexical_source": deepcopy(model_summary["source"]),
            "inventory_sha256": model_summary["inventory_sha256"],
            "support_records": deepcopy(entry["supports"]),
            "context_supplies_lexical_marks": False,
            "authority": "CONDITIONAL_IDENTITY_FROM_NAMING_PREMISE_AND_SELECTED_LEXICAL_READING"}
