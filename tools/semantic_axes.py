"""Input-only adapter for the independently frozen semantic-axes diagnostic.

No expected labels, case IDs, or benchmark files are read here. The existing
bounded discourse reader is replayed with the same explicit context and the
same pre-existing teaching corpus. Replay is Python evidence, not live Lean.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TRAINING = ROOT / "examples/discourse_training.tsv"
VERSION = "nabt.semantic-axes-adapter.v1"
LEXICAL_PROFILES = ("teaching_v1", "attested_qac_v1")
MAX_INPUT_BYTES = 65536
MAX_PUBLIC_COUNT = (1 << 53) - 1
# A public benchmark role name and the installed reader's equivalent label.
# This projection changes neither case licensing nor any expected annotation.
ROLE_PROJECTION = {"time_adverb": "temporal_adverb"}


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def identity(value):
    return sha256(wire(value)).hexdigest()


def build_request(case):
    """Only the explicit input crosses the scorer/runtime boundary."""
    return validate_request(deepcopy(case["input"]))


def validate_request(request):
    if type(request) is not dict or set(request) - {"text", "context", "query"}:
        raise ValueError("Input accepts text, explicit context, and optional query only")
    if type(request.get("text")) is not str or not request["text"].strip():
        raise ValueError("Input text must be a nonempty string")
    if type(request.get("context", {})) is not dict:
        raise ValueError("Input context must be an object")
    if "query" in request and request["query"] is not None and type(request["query"]) is not str:
        raise ValueError("Optional query must be a string or null")
    if len(wire(request)) > MAX_INPUT_BYTES:
        raise ValueError("Input exceeds the declared byte budget")
    return deepcopy(request)


@lru_cache(maxsize=4)
def _model(raw):
    from nabt.corpus_evidence import learn_qac_lexicon
    return learn_qac_lexicon(raw, source_id="authored_discourse_training")


def _unique(rows):
    return list({wire(row): row for row in rows}.values())


def observe(report):
    """Project actual licensed fields; never guess motives or external facts."""
    syntax, readings, references, alternatives = [], [], [], []
    nominal = {"nominal_predication", "composed_nominal_predication",
               "locative_predication", "idafa_subject_predication",
               "attached_idafa_subject_predication", "relative_subject_predication",
               "nominal_relative_subject_predication"}
    verbal = {"verbal_predication", "composed_verbal_predication",
              "active_verb_subject_object", "event_with_hal", "event_with_tamyiz"}
    for clause in report["clauses"]:
        semantic_options = set()
        if clause["status"] == "MENTION" and clause["force"] == "QUOTED":
            readings.append({"force": "QUOTED", "span": clause["span"]})
        for analysis in clause["analyses"]:
            if analysis["rejected_candidate"] or not analysis["licensed_syntax"]:
                continue
            semantic_options.add(wire({"force": analysis["force"], "claims": [
                {k: claim[k] for k in ("positive", "predicate_kind", "predicate", "tense", "time", "place", "restriction")}
                for claim in analysis["claims"]]}))
            frame = analysis["frame"]
            form = "nominal" if frame in nominal else "verbal" if frame in verbal else None
            syntax.append({"clause_form": form, "frame": frame,
                "roles": [{"surface": a["surface"],
                           "role": ROLE_PROJECTION.get(a["actual_role"], a["actual_role"]),
                           "runtime_role": a["actual_role"]}
                          for a in analysis["assignments"] if a["activated"]],
                "analysis_id": analysis["analysis_id"], "span": analysis["span"]})
            # Reference alternatives do not manufacture semantic ambiguity.
            # Only the explicit semantic features of an analysis are exposed.
            if analysis["claims"]:
                for claim in analysis["claims"]:
                    readings.append({"force": analysis["force"],
                        **{k: deepcopy(claim[k]) for k in
                           ("positive", "predicate_kind", "predicate", "tense", "time", "place", "restriction")},
                        "span": analysis["span"]})
            else:
                readings.append({"force": analysis["force"], "span": analysis["span"]})
            for reference in analysis["references"]:
                references.append({k: deepcopy(reference[k]) for k in
                    ("surface", "status", "candidate_entity_ids", "bound_entity_id", "reference_id")})
        alternatives.append(len(semantic_options))
    mentions_only = bool(report["clauses"]) and all(c["status"] == "MENTION" for c in report["clauses"])
    selection = ("mention" if mentions_only else "ambiguous" if any(n > 1 for n in alternatives)
                 else "unique" if alternatives and all(n == 1 for n in alternatives) else None)
    return {"syntax": _unique(syntax), "readings": _unique(readings),
            "reading_selection": selection, "semantic_alternative_counts": alternatives,
            "references": _unique(references), "asserted_claims": deepcopy(report["claims"]),
            "acquisition_diagnostics": {"engine_analysis_count": sum(len(c["analyses"]) for c in report["clauses"]),
                "lexical_occurrences": [{"surface": item["surface"],
                    "reading_count": len(item["readings"]),
                    "operator_candidate_count": len(item.get("operator_candidates", [])),
                    "governor_candidate_count": len(item.get("governor_candidates", []))}
                    for item in report.get("occurrences", [])]},
            "world_truth": report["world_truth"], "reader_status": report["status"],
            "missing_premises": sorted({o for c in report["clauses"] for o in c["obligations"]}),
            "motive_inference_available": False, "world_verification_available": False}


def lexical_profile_resources(profile):
    """Select installed evidence only; the request supplies no data or authority."""
    if type(profile) is not str or profile not in LEXICAL_PROFILES:
        raise ValueError("Unsupported lexical profile")
    if profile == "teaching_v1":
        raw = TRAINING.read_bytes()
        return _model(raw), {"path": str(TRAINING.relative_to(ROOT)),
            "sha256": sha256(raw).hexdigest(),
            "authority": "PRE_EXISTING_AUTHORED_TEACHING_CORPUS_NOT_EXTERNAL_ATTESTATION"}, None
    from tools.attested_lexical_loader import load_attested_lexicon
    loaded = load_attested_lexicon()
    report = loaded.report
    matrix = report["matrix"]
    from nabt.errors import natural
    counts = {
        "source_record_count": report["source"]["record_count"],
        "model_entry_count": report["model_summary"]["lexical_readings"],
        "matrix_sense_count": matrix["entry_count"],
        "matrix_aligned_count": matrix["aligned_entry_count"],
        "matrix_unresolved_count": matrix["unmatched_entry_count"],
    }
    for name, value in counts.items():
        natural(value, name, maximum=MAX_PUBLIC_COUNT)
    if counts["matrix_aligned_count"] + counts["matrix_unresolved_count"] != counts["matrix_sense_count"]:
        raise ValueError("Lexical matrix counts do not partition the declared entries")
    loading = {"schema": "nabt.semantic-axes-lexical-loading.v1",
        "profile": profile, "source_sha256": report["source"]["sha256"],
        "matrix_sha256": matrix["sha256"],
        "authority": "SOURCE_ANNOTATION_NOT_SENSE_OR_WORLD_LICENSE",
        "lean_native_checked": False,
        **counts}
    return loaded.model, {"path": report["source"]["path"],
        "sha256": report["source"]["sha256"],
        "authority": loading["authority"]}, loading


def execute_request(request, *, reader=None, verifier=None, lexical_model=None,
                    lexical_profile="teaching_v1"):
    """Execute only text/context; query is preserved but not used as an oracle.

    Injectable reader/verifier are for boundary tests. They cannot promote
    replay to a Lean-native certificate. Production uses the installed reader.
    """
    request = validate_request(request)
    if lexical_profile != "teaching_v1" and any(value is not None for value in (reader, verifier, lexical_model)):
        raise ValueError("An installed source profile cannot accept substituted model, reader or verifier")
    if reader is None or verifier is None:
        from nabt.discourse_reader import read_discourse, verify_discourse
        reader = read_discourse if reader is None else reader
        verifier = verify_discourse if verifier is None else verifier
    model, training, loading = lexical_profile_resources(lexical_profile)
    if lexical_model is not None:
        if lexical_profile != "teaching_v1":
            raise ValueError("An installed source profile cannot accept a substituted model")
        model = lexical_model
    kwargs = {"lexical_model": model, "context": request.get("context", {}),
              "source_id": "semantic_axes_input", "scope": "declared_context"}
    raw = reader(request["text"], **kwargs)
    replay = verifier(raw, text=request["text"], **kwargs)
    checked = replay.get("valid") is True and replay.get("status") == "VERIFIED"
    receipt = {"schema": "nabt.semantic-axes-replay.v1", "input_sha256": identity(request),
               "report_sha256": identity(raw), "replay": replay,
               "training_sha256": training["sha256"], "adapter_version": VERSION,
               "lexical_profile": lexical_profile, "lexical_loading": loading}
    return {"schema": "nabt.semantic-axes-observation.v1", "adapter_version": VERSION,
            "input_sha256": identity(request), "context_sha256": identity(request.get("context", {})),
            "executed": True, "replay_checked": checked,
            "observed": observe(raw) if checked else None,
            "replay_receipt": receipt, "replay_receipt_sha256": identity(receipt),
            "training": training, "lexical_profile": lexical_profile,
            "lexical_loading": loading,
            "verification_kind": "PYTHON_REPLAY", "lean_native_checked": False,
            "query_executed": False, "all_arabic_complete": False,
            "authority": "BOUNDED_TEXT_AND_EXPLICIT_CONTEXT_REPLAY_NOT_WORLD_OR_MOTIVE_TRUTH"}


def runtime_snapshot():
    """Hash repository modules actually loaded, without runtime/secret values."""
    paths = {Path(__file__).resolve()}
    for module in tuple(sys.modules.values()):
        path = getattr(module, "__file__", None)
        if path and Path(path).suffix == ".py":
            resolved = Path(path).resolve()
            if resolved.is_relative_to(ROOT):
                paths.add(resolved)
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths) if p.is_file()}
