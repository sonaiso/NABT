"""OntoLex concept view of the installed conditional denotation owner.

No second sense registry, learned indication classifier, or language rule.
Dictionary root indices do not provide canonical lexical forms. The export
therefore uses OntoLex LexicalConcept/ConceptSet, retaining original sense IDs,
and leaves LexicalEntry/Form/Reference alignment as an explicit obligation.
"""
from copy import deepcopy
from hashlib import sha256
from urllib.parse import quote

from tools import lexical_testimony
from tools.evidence_lifecycle_v1 import _encoded, wire

SCHEMA = "nabt.ontolex-denotation.v1"
CONTEXT = {
    "ontolex": "http://www.w3.org/ns/lemon/ontolex#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "prov": "http://www.w3.org/ns/prov#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "nabt": "urn:nabt:lexical-extension:v1:",
}


def validate(request):
    _encoded(request, 512 * 1024)
    if type(request) is not dict or set(request) != {"entry", "target"}:
        raise ValueError("Expected only installed dictionary index and target components")
    entry, target = request["entry"], request["target"]
    if (type(entry) is not str or not entry.strip() or len(entry.encode()) > 128
            or type(target) is not list or len(target) > 64
            or any(type(t) is not str or not t.strip() or len(t.encode()) > 4096 for t in target)):
        raise ValueError("Invalid lexical index or component list")
    return deepcopy(request)


def assess(request):
    values = validate(request)
    return lexical_testimony.assess(values["entry"], values["target"])


def _literal(value):
    return {"@value": value, "@language": "ar"}


def _concept_graph(owner):
    """Internal projection of a freshly checked owner, never caller input."""
    catalogue = "urn:nabt:lexical-catalog:" + owner["catalogue_sha256"]
    receipt = "urn:nabt:lexical-assessment:" + sha256(wire(owner).encode()).hexdigest()
    graph = [{"@id": catalogue, "@type": "ontolex:ConceptSet",
              "nabt:catalogueSHA256": owner["catalogue_sha256"]},
             {"@id": receipt, "@type": "nabt:ConditionalAssessment",
              "nabt:dictionaryIndex": _literal(owner["entry"]),
              "nabt:targetComponents": {"@list": [_literal(t) for t in owner["target"]]},
              "nabt:ownerStatus": owner["status"],
              "nabt:lawID": owner["law_id"],
              "nabt:nativeSHA256": owner["native_sha256"],
              "nabt:worldTruthEstablished": False,
              "nabt:intendedSenseEstablished": False}]
    for index, row in enumerate(owner["rows"]):
        concept = catalogue + ":concept:" + quote(row["sense_id"], safe="")
        citation = concept + ":citation"
        evaluation = receipt + ":sense:" + quote(row["sense_id"], safe="")
        testimony = row["testimony"]
        source = testimony["citation"]
        graph.extend([
            {"@id": concept, "@type": "ontolex:LexicalConcept",
             "skos:inScheme": {"@id": catalogue},
             "nabt:sourceSenseID": row["sense_id"],
             "nabt:dictionaryIndex": _literal(owner["entry"]),
             "nabt:definitionComponents": {"@list": [_literal(c) for c in row["components"]]},
             "nabt:interpretationStatus": row["interpretation_status"],
             "prov:wasDerivedFrom": {"@id": citation}},
            {"@id": citation, "@type": "prov:Entity",
             "rdf:value": _literal(source["quotation"]),
             "nabt:workTitle": _literal(testimony["work_title"]),
             "nabt:author": _literal(testimony["author"]),
             "nabt:sourceSHA256": source["source_sha256"],
             "nabt:revision": source["revision"],
             "nabt:startByte": source["start_byte"], "nabt:endByte": source["end_byte"],
             "nabt:sourceCheck": testimony["source_check"],
             "nabt:historicalAuthenticityEstablished": False},
            {"@id": evaluation, "@type": "nabt:ConditionalIndication",
             "nabt:assessment": {"@id": receipt}, "nabt:concept": {"@id": concept},
             **{"nabt:" + kind: value for kind, value in row["indications"].items()},
             "nabt:ownerRowPointer": "/owner_result/rows/" + str(index),
             "nabt:worldTruthEstablished": False},
        ])
    return {"@context": deepcopy(CONTEXT), "@graph": graph}


def export(request):
    owner = assess(request)
    graph = _concept_graph(owner) if owner["native_checked"] else None
    return {"schema": SCHEMA, "status": owner["status"], "owner_result": owner,
            "format": "application/ld+json", "graph": graph,
            "graph_sha256": sha256(wire(graph).encode()).hexdigest() if graph is not None else None,
            "export_authority": "CONDITIONAL_CONCEPT_VIEW_NOT_NEW_SEMANTIC_LICENSE",
            "native_checked": owner["native_checked"],
            "all_owner_alternatives_retained": bool(graph is not None),
            "remaining_obligations": ["LEXICAL_FORM_TO_DICTIONARY_SENSE_ALIGNMENT",
                                      "EXACT_OCCURRENCE_AND_INTENDED_SENSE",
                                      "APPLICABLE_EXTERNAL_EVIDENCE_FOR_WORLD_JUDGMENT"],
            "semantic_rank_promoted": False, "new_lean_proof": False,
            "shap_values_are_indications": False}
