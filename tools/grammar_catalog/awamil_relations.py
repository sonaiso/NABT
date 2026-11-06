"""Lossless, analysis-local views of installed discourse owner relations.

The view never licenses a new attachment or projects an embedded assertion.
An unbound verbal/locative head remains an explicit outstanding obligation.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import read_discourse
from tools.evidence_lifecycle_v1 import wire, _encoded
from .operations import digest

RELATION_FAMILY = {
    "predicate_agreement": "predicative", "relative_clause": "embedding",
    "operator": "operator_scope", "prepositional_attachment": "restrictive",
    "temporal_spatial_attachment": "restrictive", "naat": "restrictive",
    "idafa": "restrictive", "idafa_chain": "restrictive", "hal": "restrictive",
    "tamyiz": "restrictive", "badal": "restrictive", "tawkeed": "restrictive",
    "place_adverb": "restrictive", "time_adverb": "restrictive",
}


def matrix(text, *, lexical_text=None, context=None):
    if type(text) is not str or not text.strip() or len(text.encode()) > 32768:
        raise ValueError("Expected nonempty source text up to 32 KiB")
    if lexical_text is not None and (type(lexical_text) is not str or len(lexical_text.encode()) > 1048576):
        raise ValueError("Lexical evidence exceeds 1 MiB or is not text")
    _encoded(context, 262144, floats=False)
    model = learn_qac_lexicon(lexical_text.encode(), source_id="awamil_lexical_evidence") if lexical_text else None
    doc = read_discourse(text, lexical_model=model, context=context)
    rows = []
    for clause in doc["clauses"]:
        for analysis in clause["analyses"]:
            predications = []
            for binding in analysis.get("claim_bindings", []):
                predications.append({"musnad_ilayh": binding["subject_span"],
                    "musnad": binding["predicate_span"], "predication_head": binding["predicate_span"],
                    "head_definition": "PREDICATIVE_ANCHOR_NOT_GOVERNOR_OR_DEPENDENCY_ROOT",
                    "binding": deepcopy(binding), "scope": "embedded" if binding["claim_path"] else "matrix",
                    "basis": "OWNER_CLAIM_PREDICATION_BINDING"})
            # Verbal roles already carry their selected verb's head span. Keep
            # separate alternative analyses; never pick a verb by word position.
            for assignment in analysis["assignments"]:
                if (assignment["role"] == "nominal_predicate" and assignment.get("head_span") and
                        not any(p["musnad"] == assignment["span"] for p in predications)):
                    predications.append({"musnad_ilayh": assignment["head_span"],
                        "musnad": assignment["span"], "predication_head": assignment["span"],
                        "basis": "OWNER_PREDICATE_ASSIGNMENT", "scope": "owner_frame",
                        "head_status": "PHRASE_BOUND_NO_ELLIPSIS_INVENTED"})
                if assignment["role"] in {"active_subject", "passive_subject"}:
                    head = assignment.get("head_span")
                    predications.append({"musnad_ilayh": assignment["span"], "musnad": head,
                        "predication_head": head, "subject_role": assignment["role"],
                        "basis": "OWNER_ROLE_ASSIGNMENT", "scope": "owner_frame",
                        "head_status": "BOUND" if head else "NEEDS_PREDICATE_BINDING"})
            relations = [{"family": RELATION_FAMILY.get(r["kind"], "UNMAPPED_OWNER_RELATION"),
                          "owner_relation": deepcopy(r)} for r in analysis["relations"]]
            rows.append({"clause_id": clause["clause_id"], "analysis_id": analysis["analysis_id"],
                "frame": analysis["frame"], "force": analysis["force"],
                "licensed_syntax": analysis["licensed_syntax"],
                "references_complete": analysis["references_complete"],
                "rejected_candidate": analysis["rejected_candidate"],
                "predications": predications, "relations": relations,
                "assignments": deepcopy(analysis["assignments"]),
                "claims": deepcopy(analysis["claims"]),
                "obligations": deepcopy(analysis["obligations"]),
                "head_status": "BOUND_FROM_OWNER" if predications else "NO_PREDICATION_BINDING",
                "embedded_fact_projection_added": False})
    return {"schema": "nabt.awamil-relation-matrix.v1", "status": doc["status"],
        "source_text": text, "source_sha256": sha256(text.encode()).hexdigest(),
        "lexical_evidence_sha256": sha256(lexical_text.encode()).hexdigest() if lexical_text else None,
        "context_sha256": digest(context), "rows": rows,
        "authority": "EXISTING_DISCOURSE_OWNER_VIEW", "scope": "SOURCE_RELATIVE_NOT_WORLD_TRUTH",
        "matrix_is_new_certificate": False,
        "embedding_definition": "STRUCTURAL_EMBEDDING_NOT_DALALA_TADAMMUN"}


def verify_matrix(report, *, text, lexical_text=None, context=None):
    """Replay against caller-held inputs, not fields copied from the report."""
    _encoded(report, 8 * 1048576, floats=False)
    fresh = matrix(text, lexical_text=lexical_text, context=context)
    return {"valid": wire(report) == wire(fresh), "verification": "FRESH_OWNER_REPLAY",
            "scope": "SOURCE_RELATIVE_NOT_WORLD_TRUTH"}
