"""Compare frozen occurrence obligations without sending labels to the runtime.

The adapter below is defined from the public receipt schema.  Safety, useful
acquisition, ambiguity, missing coverage and native checking have separate
denominators.  A checked refusal is never a successful linguistic acquisition.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

HOLDOUT = ROOT / "evidence/occurrence_sense_v1/holdout"
FREEZE_FILE_SHA256 = "2df54b11cd2f027db0a20ee3460dc5e30b372c7d77f559851b369e1799a4ced3"
FREEZE_IDENTITY = "bbb88fc64e6325841816f15a37a62930e2eb0d105aa7c4f629cb97838ef4ff81"
ERRATUM = HOLDOUT.parent / "reference_erratum_v1.json"
ERRATUM_SHA256 = "6ec6cbc3852b5c3766860e976fcc0d60889be69bd3a1f1e9cf986b4840f66e4a"
DERIVED_REFERENCE_SHA256 = "764208a476624011483f90cffd6e3059953145c56a725fa0abc19fbfe40b9289"
PASSAGE_ID_ERRATA = {"QATR-REFERENCE", "SIRAFI-PARTICIPANTS"}
SCHEMA = "nabt.occurrence-sense-observation.v1"
STATUSES = {"CANDIDATES_ONLY", "PARTIAL_CANDIDATES", "NO_DICTIONARY_CANDIDATE",
            "NO_MORPHOLOGY_READING", "RESOURCE_LIMIT", "INVALID_INPUT", "UNMEASURED"}
COMPLETE = {"CANDIDATES_ONLY", "PARTIAL_CANDIDATES", "NO_DICTIONARY_CANDIDATE",
            "NO_MORPHOLOGY_READING"}
INDICATIONS = {"matching": "mutabaqa", "inclusion": "tadammun", "entailment": "iltizam"}
AXES = ("safety", "candidate_acquisition", "conditional_indication", "ambiguity",
        "initial_reference", "occurrence_reference_separation", "bounded_behavior",
        "linguistic_coverage", "native")


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _strict_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON key")
        value[key] = item
    return value


def strict_json(path):
    def invalid_constant(value):
        raise ValueError("Nonfinite JSON: " + value)
    return json.loads(Path(path).read_text(), object_pairs_hook=_strict_pairs,
                      parse_constant=invalid_constant)


def apply_erratum(reference, amendments, *, catalogue_ids, passage_ids):
    """Apply exact, reviewable array edits; never filter arbitrary unknown IDs."""
    if PASSAGE_ID_ERRATA & catalogue_ids or not PASSAGE_ID_ERRATA <= passage_ids:
        raise ValueError("Erratum membership evidence changed")
    derived = deepcopy(reference)
    by_id = {row["id"]: row for row in derived["cases"]}
    seen = set()
    for amendment in amendments:
        if set(amendment) != {"case_id", "field", "before", "after", "reason"}:
            raise ValueError("Unexpected erratum operation")
        key = (amendment["case_id"], amendment["field"])
        if key in seen or key[0] not in by_id or key[1] not in {"candidate_sense_ids_exact", "forbidden_sense_ids"}:
            raise ValueError("Erratum cannot change inputs or other expectation fields")
        seen.add(key)
        before, after = amendment["before"], amendment["after"]
        if type(before) is not list or type(after) is not list or not set(before) & PASSAGE_ID_ERRATA:
            raise ValueError("Erratum must identify actual provenance pollution")
        if by_id[key[0]]["expect"].get(key[1]) != before:
            raise ValueError("Erratum before-array differs from frozen reference")
        if after != [sid for sid in before if sid not in PASSAGE_ID_ERRATA]:
            raise ValueError("Erratum cannot remove, add or reorder actual sense labels")
        if not _strings(after) or not set(after) <= catalogue_ids:
            raise ValueError("Erratum result is not a unique catalogue-sense array")
        by_id[key[0]]["expect"][key[1]] = deepcopy(after)
    return derived


def validate_reference_labels(reference, catalogue_ids):
    fields = {"candidate_sense_ids_exact", "forbidden_sense_ids", "unresolved_sense_ids",
              "linguistic_candidate_obligation"} | {
                  "conditional_" + key + "_sense_ids_exact" for key in INDICATIONS}
    for case in reference["cases"]:
        for field in fields & case["expect"].keys():
            labels = case["expect"][field]
            if not _strings(labels) or not set(labels) <= catalogue_ids:
                raise ValueError("Non-catalogue or duplicate reference sense: " + case["id"] + "/" + field)


def load_reference(*, original=False):
    raw = (HOLDOUT / "freeze.json").read_bytes()
    if sha256(raw).hexdigest() != FREEZE_FILE_SHA256:
        raise ValueError("Frozen manifest bytes changed")
    freeze = strict_json(HOLDOUT / "freeze.json")
    identity = freeze.pop("freeze_sha256")
    if identity != FREEZE_IDENTITY or digest(freeze) != identity:
        raise ValueError("Frozen manifest identity changed")
    for name, wanted in freeze["files"].items():
        if Path(name).name != name or sha256((HOLDOUT / name).read_bytes()).hexdigest() != wanted:
            raise ValueError("Frozen reference member changed")
    reference = strict_json(HOLDOUT / "reference.json")
    cases = reference["cases"]
    if len(cases) != 20 or len({row["id"] for row in cases}) != 20:
        raise ValueError("Frozen denominator changed")
    if any(set(row["input"]) != {"text", "context", "token_index", "target", "budget"}
           for row in cases):
        raise ValueError("Runtime input boundary changed")
    if original:
        return reference
    if sha256(ERRATUM.read_bytes()).hexdigest() != ERRATUM_SHA256:
        raise ValueError("Versioned reference erratum changed")
    erratum = strict_json(ERRATUM)
    if (erratum.get("base_freeze_identity") != FREEZE_IDENTITY or
            erratum.get("base_reference_sha256") != freeze["files"]["reference.json"] or
            erratum.get("recorded_after_first_observation") is not True or
            erratum.get("amendment_count") != 10 or len(erratum.get("amendments", [])) != 10):
        raise ValueError("Erratum scope/binding mismatch")
    evidence = erratum["source_membership_evidence"]
    catalogue_path, ledger_path = ROOT / evidence["catalogue_path"], ROOT / evidence["passage_ledger_path"]
    for path, wanted in ((catalogue_path, evidence["catalogue_sha256"]),
                         (ledger_path, evidence["passage_ledger_sha256"])):
        if sha256(path.read_bytes()).hexdigest() != wanted:
            raise ValueError("Erratum source membership evidence changed")
    catalogue_ids = {row["id"] for row in strict_json(catalogue_path)["senses"]}
    passage_ids = {row["id"] for row in strict_json(ledger_path)["passages"]}
    derived = apply_erratum(reference, erratum["amendments"], catalogue_ids=catalogue_ids, passage_ids=passage_ids)
    validate_reference_labels(derived, catalogue_ids)
    if digest(derived) != DERIVED_REFERENCE_SHA256 or erratum["derived_reference_canonical_sha256"] != DERIVED_REFERENCE_SHA256:
        raise ValueError("Derived reference identity mismatch")
    return derived


def outer_occurrences(text):
    """Independent span oracle for this authored set's Arabic written runs.

    This simple scanner is deliberately not a general Arabic parser. It knows
    the literal quote delimiters used by the reference and Unicode letters and
    combining marks. It imports no production scanner or lexical knowledge.
    """
    tokens, start, closing = [], None, None
    quotes = {"«": "»", '"': '"', "“": "”", "‘": "’"}
    for index, char in enumerate(text + " "):
        if closing is not None:
            if char == closing:
                closing = None
            continue
        written = (unicodedata.category(char)[0] in ("L", "M") and
                   "ARABIC" in unicodedata.name(char, ""))
        if written and start is None:
            start = index
        if not written and start is not None:
            tokens.append({"start_byte": len(text[:start].encode()),
                           "end_byte": len(text[:index].encode()),
                           "surface": text[start:index]})
            start = None
        if char in quotes:
            closing = quotes[char]
    return tokens


def _strings(value):
    return (type(value) is list and all(type(item) is str for item in value)
            and len(value) == len(set(value)))


def normalize(execution):
    """Fail closed on missing fields and contradictory/duplicate inventories."""
    errors = []
    if type(execution) is not dict:
        return {"errors": ["NOT_AN_OBJECT"], "status": "UNMEASURED"}
    status = execution.get("status")
    if execution.get("schema") != SCHEMA or status not in STATUSES:
        errors.append("UNKNOWN_RECEIPT_SCHEMA_OR_STATUS")
    readings, metadata = execution.get("readings"), execution.get("candidate_senses")
    ids, indicated, unresolved = set(), {key: set() for key in INDICATIONS}, set()
    per_sense, row_count, unmatched = {}, None, None
    if type(readings) is not list or type(metadata) is not list:
        errors.append("MISSING_CANDIDATE_INVENTORY")
    else:
        row_count, unmatched = len(readings), 0
        for reading in readings:
            if (type(reading) is not dict or type(reading.get("senses")) is not list or
                    reading.get("status") not in ("CANDIDATES_ONLY", "UNMATCHED_READING")):
                errors.append("MALFORMED_READING")
                continue
            if reading["status"] == "UNMATCHED_READING":
                unmatched += 1
            seen = set()
            for sense in reading["senses"]:
                if (type(sense) is not dict or type(sense.get("id")) is not str or
                        any(type(sense.get(field)) is not bool for field in INDICATIONS.values())):
                    errors.append("MALFORMED_INDICATION")
                    continue
                sid = sense["id"]
                flags = tuple(sense[field] for field in INDICATIONS.values())
                if sid in seen or (sid in per_sense and per_sense[sid] != flags):
                    errors.append("DUPLICATE_OR_INCONSISTENT_SENSE")
                seen.add(sid)
                ids.add(sid)
                per_sense[sid] = flags
                for key, field in INDICATIONS.items():
                    if sense[field]:
                        indicated[key].add(sid)
            if bool(reading["senses"]) != (reading["status"] == "CANDIDATES_ONLY"):
                errors.append("READING_STATUS_CONTRADICTS_SENSES")
        metadata_ids = []
        for sense in metadata:
            if type(sense) is not dict or type(sense.get("id")) is not str:
                errors.append("MALFORMED_CANDIDATE_METADATA")
                continue
            metadata_ids.append(sense["id"])
            if (sense.get("conditional_only") is not True or
                    sense.get("sense_licensed_for_new_occurrence") is not False):
                errors.append("CANDIDATE_PROMOTED_TO_OCCURRENCE_MEANING")
            interpretation = sense.get("interpretation_status")
            if type(interpretation) is not str:
                errors.append("MISSING_INTERPRETATION_STATUS")
            elif interpretation.startswith("UNRESOLVED"):
                unresolved.add(sense["id"])
        if not _strings(metadata_ids) or set(metadata_ids) != ids:
            errors.append("CANDIDATE_METADATA_INVENTORY_MISMATCH")
        if status in COMPLETE:
            if status == "NO_MORPHOLOGY_READING" and readings:
                errors.append("MORPHOLOGY_STATUS_CONTRADICTION")
            if status == "NO_DICTIONARY_CANDIDATE" and (not readings or ids):
                errors.append("DICTIONARY_STATUS_CONTRADICTION")
            if status == "CANDIDATES_ONLY" and (not ids or unmatched):
                errors.append("COMPLETE_STATUS_CONTRADICTION")
            if status == "PARTIAL_CANDIDATES" and (not ids or not unmatched):
                errors.append("PARTIAL_STATUS_CONTRADICTION")
        elif ids or any(indicated.values()):
            errors.append("STOP_RESULT_CONTAINS_SUCCESS_CANDIDATES")
    receipt_hash = execution.get("receipt_sha256")
    try:
        actual = digest({key: value for key, value in execution.items() if key != "receipt_sha256"})
    except (TypeError, ValueError):
        actual = None
    if type(receipt_hash) is not str or receipt_hash != actual:
        errors.append("RECEIPT_INTEGRITY_MISMATCH")
    return {"errors": sorted(set(errors)), "status": status,
            "candidate_sense_ids": sorted(ids), "indicated": {k: sorted(v) for k, v in indicated.items()},
            "unresolved_sense_ids": sorted(unresolved), "reading_count": row_count,
            "unmatched_reading_count": unmatched}


def check(ok, reason, *, unavailable=False):
    return {"status": "UNMEASURED" if unavailable else "PASS" if ok else "FAIL", "reason": reason}


def compare_case(case, execution):
    wanted, request = case["expect"], case["input"]
    observed = normalize(execution)
    result = {axis: {"status": "NOT_APPLICABLE", "reason": "NO_OBLIGATION"} for axis in AXES}
    unavailable = observed["status"] == "UNMEASURED"
    valid = not observed["errors"]
    actual = execution if type(execution) is dict else {}
    false_fields = ("world_truth_established", "contextual_sense_selected", "reference_transferred",
                    "whole_clause_checked", "all_arabic_complete")
    bound = actual.get("input") == request and actual.get("input_sha256") == digest(request)
    safe = valid and bound and all(actual.get(field) is False for field in false_fields)
    result["safety"] = check(safe, "STRICT_RECEIPT_SCOPE_AND_INPUT_BINDING", unavailable=unavailable)
    result["occurrence_reference_separation"] = check(
        actual.get("reference_transferred") is False and actual.get("whole_clause_checked") is False,
        "INITIAL_REFERENCE_DOES_NOT_BIND_LATER_NOUN", unavailable=unavailable)
    complete = valid and observed["status"] in COMPLETE
    candidates = observed.get("candidate_sense_ids", [])
    if "candidate_sense_ids_exact" in wanted:
        exact = set(candidates) == set(wanted["candidate_sense_ids_exact"])
        result["candidate_acquisition"] = check(complete and exact, "EXACT_INSTALLED_CANDIDATE_SET", unavailable=unavailable)
        indications_ok = all(set(observed.get("indicated", {}).get(key, [])) ==
                             set(wanted.get("conditional_" + key + "_sense_ids_exact", []))
                             for key in INDICATIONS)
        result["conditional_indication"] = check(complete and exact and indications_ok,
                                                   "PER_SENSE_CONDITIONAL_INDICATION", unavailable=unavailable)
        if len(wanted["candidate_sense_ids_exact"]) > 1:
            result["ambiguity"] = check(complete and exact and actual.get("contextual_sense_selected") is False,
                                        "ALL_ALTERNATIVES_RETAINED", unavailable=unavailable)
    obligations = []
    if "forbidden_sense_ids" in wanted:
        obligations.append(not set(wanted["forbidden_sense_ids"]) & set(candidates))
    if "unresolved_sense_ids" in wanted:
        obligations.append(set(wanted["unresolved_sense_ids"]) <= set(observed.get("unresolved_sense_ids", [])))
        obligations.append(not any(set(wanted["unresolved_sense_ids"]) & set(v)
                                   for v in observed.get("indicated", {}).values()))
    if wanted.get("morphology_reading_required") is True:
        obligations.append(type(observed.get("reading_count")) is int and observed["reading_count"] > 0)
    if wanted.get("no_attested_occurrence_reading_required"):
        obligations.append(observed["status"] == "NO_MORPHOLOGY_READING" and observed.get("reading_count") == 0)
    if wanted.get("catalogue_coverage_gap_required"):
        obligations.append(observed["status"] in ("NO_DICTIONARY_CANDIDATE", "PARTIAL_CANDIDATES"))
    if wanted.get("coverage_gap_required"):
        obligations.append(observed["status"] in ("NO_DICTIONARY_CANDIDATE", "NO_MORPHOLOGY_READING", "PARTIAL_CANDIDATES"))
    if wanted.get("no_selected_outer_occurrence"):
        obligations.append(observed["status"] == "INVALID_INPUT" and actual.get("occurrence") is None and not candidates)
    if wanted.get("resource_or_invalid_budget_rejection_required"):
        obligations.append(observed["status"] in ("RESOURCE_LIMIT", "INVALID_INPUT") and not candidates)
    if obligations:
        result["bounded_behavior"] = check(valid and safe and all(obligations), "EXPLICIT_SCOPE_COVERAGE_OR_RESOURCE_OBLIGATIONS", unavailable=unavailable)
    overclaims = bool(set(wanted.get("forbidden_sense_ids", [])) & set(candidates))
    if "candidate_sense_ids_exact" in wanted:
        overclaims = overclaims or bool(set(candidates) - set(wanted["candidate_sense_ids_exact"]))
        for key in INDICATIONS:
            overclaims = overclaims or bool(set(observed.get("indicated", {}).get(key, [])) -
                                            set(wanted.get("conditional_" + key + "_sense_ids_exact", [])))
    if wanted.get("no_selected_outer_occurrence") or wanted.get("resource_or_invalid_budget_rejection_required"):
        overclaims = overclaims or observed["status"] in COMPLETE or bool(candidates)
    if overclaims:
        result["safety"] = check(False, "REFERENCE_FORBIDS_REPORTED_POSITIVE_CLAIM", unavailable=unavailable)
    tokens = outer_occurrences(request["text"])
    index = request["token_index"]
    if type(index) is int and 0 <= index < len(tokens) and observed["status"] in COMPLETE:
        if actual.get("occurrence") != tokens[index]:
            result["safety"] = check(False, "WRONG_SELECTED_OCCURRENCE")
            result["candidate_acquisition"] = check(False, "CANDIDATES_FOR_WRONG_OCCURRENCE")
    if "linguistic_candidate_obligation" in wanted:
        result["linguistic_coverage"] = check(
            complete and set(wanted["linguistic_candidate_obligation"]) <= set(candidates),
            "DESIRED_LINGUISTIC_COVERAGE_IS_NOT_SAFE_ABSTENTION", unavailable=unavailable)
    if "initial_reference" in wanted:
        expected = wanted["initial_reference"]
        receipt = actual.get("initial_reference")
        receipt = receipt if type(receipt) is dict else {}
        ref = receipt.get("reference")
        ref = ref if type(ref) is dict else {}
        supplied = ref.get("candidate_entity_ids")
        native_input = receipt.get("execution", {})
        native_input = native_input.get("input", {}) if type(native_input) is dict else {}
        native_input = native_input if type(native_input) is dict else {}
        own = tokens[expected["occurrence_token_index"]] if tokens else None
        ref_input = {"text": request["text"], "context": request["context"]}
        expected_status = ("RESOLVED" if expected["bound_entity_id"] is not None else
                           "AMBIGUOUS" if expected["candidate_entity_ids_exact"] else "NO_CANDIDATE")
        ok = (_strings(supplied) and set(supplied) == set(expected["candidate_entity_ids_exact"]) and
              "bound_entity_id" in ref and ref["bound_entity_id"] == expected["bound_entity_id"] and
              ref.get("status") == expected_status and ref.get("scope") == "outer" and
              type(ref.get("occurrence")) is int and ref["occurrence"] == expected["occurrence_token_index"] and
              native_input.get("occurrence") == own and receipt.get("input") == ref_input and
              receipt.get("input_sha256") == digest(ref_input) and receipt.get("native_checked") is True and
              receipt.get("certificate_checked") is True)
        result["initial_reference"] = check(valid and ok, "REFERENCE_OWN_OCCURRENCE_CONTEXT_AND_ENTITY_SET", unavailable=unavailable)
    native_required = not (wanted.get("no_selected_outer_occurrence") or
                           wanted.get("resource_or_invalid_budget_rejection_required"))
    if native_required:
        result["native"] = check(actual.get("native_checked") is True and actual.get("certificate_checked") is True,
                                  "NATIVE_CHECK_IS_SEPARATE_FROM_REFERENCE_CORRECTNESS", unavailable=unavailable)
    return {"id": case["id"], "logical_class": wanted["logical_class"], "input": deepcopy(request),
            "input_sha256": digest(request), "expected": deepcopy(wanted), "comparison": result,
            "observed": observed, "execution": deepcopy(execution)}


def metric(rows):
    statuses = [row["status"] for row in rows]
    if set(statuses) - {"PASS", "FAIL", "UNMEASURED", "NOT_APPLICABLE"}:
        raise ValueError("Unknown comparison status")
    return {"eligible": sum(s != "NOT_APPLICABLE" for s in statuses),
            "passed": statuses.count("PASS"), "failed": statuses.count("FAIL"),
            "unmeasured": statuses.count("UNMEASURED")}


def compare_pairs(obligations, rows):
    by_id, results = {row["id"]: row for row in rows}, []
    for number, obligation in enumerate(obligations, 1):
        selected = [by_id[cid] for cid in obligation["cases"]]
        checks = []
        for relation in ("same", "different"):
            for field in obligation.get(relation, []):
                values = []
                for row in selected:
                    receipt = row["execution"]
                    receipt = receipt if type(receipt) is dict else {}
                    if field == "candidate_sense_ids":
                        value = row["observed"].get("candidate_sense_ids")
                    elif field == "conditional_matching_sense_ids":
                        value = row["observed"].get("indicated", {}).get("matching")
                    elif field == "initial_reference.bound_entity_id":
                        initial = receipt.get("initial_reference")
                        initial = initial if type(initial) is dict else {}
                        ref = initial.get("reference")
                        value = ref.get("bound_entity_id") if type(ref) is dict else None
                    elif field == "context_sha256":
                        value = receipt.get("context_sha256")
                    else:
                        raise ValueError("Unknown frozen pair field: " + field)
                    values.append(value)
                present = all(value is not None for value in values)
                equal = all(value == values[0] for value in values)
                checks.append(present and (equal if relation == "same" else len({digest(v) for v in values}) == len(values)))
        usable = all(not row["observed"]["errors"] and row["observed"]["status"] in COMPLETE
                     and row["comparison"]["candidate_acquisition"]["status"] == "PASS" for row in selected)
        results.append({"id": "M" + str(number), "cases": obligation["cases"],
                        **check(usable and all(checks), "FROZEN_QUERY_OR_CONTEXT_INVARIANCE")})
    return results


def summarize(rows, pairs):
    summary = {axis: metric([row["comparison"][axis] for row in rows]) for axis in AXES}
    summary["context_and_query_invariance"] = metric(pairs)
    summary["positive_candidate_acquisition"] = metric([
        row["comparison"]["candidate_acquisition"] for row in rows
        if row["expected"].get("candidate_sense_ids_exact")])
    return summary


def run(*, execute=None, require_native=False, require_safety=False):
    reference = load_reference()
    original = load_reference(original=True)
    # This lazy import is the only entry into the new runtime. Unit tests use
    # artificial receipts and never execute production acquisition.
    if execute is None:
        from tools.occurrence_sense import assess
        execute = assess
    rows = []
    for case in reference["cases"]:
        request = deepcopy(case["input"])
        try:
            execution = execute(request)
        except Exception as error:
            # Infrastructure failure is preserved, not converted to either a
            # linguistic rejection or a successful conservative abstention.
            execution = {"status": "UNMEASURED", "error_type": type(error).__name__,
                         "error": str(error)[:2048]}
        rows.append(compare_case(case, execution))
    pairs = compare_pairs(reference["metamorphic_obligations"], rows)
    summary = summarize(rows, pairs)
    executions = {row["id"]: row["execution"] for row in rows}
    original_rows = [compare_case(case, executions[case["id"]]) for case in original["cases"]]
    original_pairs = compare_pairs(original["metamorphic_obligations"], original_rows)
    native_ok = summary["native"]["failed"] == summary["native"]["unmeasured"] == 0
    safety_ok = summary["safety"]["passed"] == len(rows)
    identities = [row["execution"].get("identity") for row in rows
                  if type(row["execution"]) is dict and row["observed"]["status"] in COMPLETE]
    identity_stable = (bool(identities) and all(type(value) is dict and value for value in identities)
                       and all(value == identities[0] for value in identities))
    # Identities document reproducibility. They do not establish authenticity
    # of a historical source or replace native receipt checking.
    report = {"schema": "nabt.occurrence-sense-benchmark.v1", "freeze_identity": FREEZE_IDENTITY,
              "freeze_file_sha256": FREEZE_FILE_SHA256, "scorer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
              "case_count": len(rows), "summary": summary, "cases": rows, "metamorphic_checks": pairs,
              "reference_version": "FROZEN_V1_WITH_EXPLICIT_POST_OBSERVATION_ERRATUM_V1",
              "reference_erratum_sha256": ERRATUM_SHA256,
              "derived_reference_canonical_sha256": DERIVED_REFERENCE_SHA256,
              "original_reference_summary_same_executions": summarize(original_rows, original_pairs),
              "original_first_observation": strict_json(ERRATUM)["original_first_report"],
              "all_required_cases_native_checked": native_ok, "all_cases_safety_passed": safety_ok,
              "runtime_identity_stable": bool(identity_stable),
              "runtime_identity": identities[0] if identity_stable else None,
              "integrity_obligations": {"count": 6, "status": "SEPARATE_TESTS_REQUIRED", "included_in_case_denominator": False},
              "whole_arabic_complete": False, "world_truth_established": False,
              "reference_correctness_is_native_proof": False,
              "scope": "INDEPENDENT_AUTHORED_DIAGNOSTIC_WITH_SEPARATE_COVERAGE_AND_SAFETY_DENOMINATORS",
              "requirements_met": (not require_native or native_ok) and (not require_safety or safety_ok)}
    load_reference()  # Also reject source/reference mutation during measurement.
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-native", action="store_true")
    parser.add_argument("--require-safety", action="store_true")
    args = parser.parse_args()
    report = run(require_native=args.require_native, require_safety=args.require_safety)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"case_count": report["case_count"], "summary": report["summary"],
                      "requirements_met": report["requirements_met"]}, ensure_ascii=False))
    return 0 if report["requirements_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
