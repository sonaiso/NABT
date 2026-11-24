"""Internal training/assessment contract over the installed ACB scorer.

This is a developer measurement tool, not a second NTP admission boundary.
Reading-set agreement and conditional statistical gates never certify an Arabic
analysis, a CertifiedBridge, the sampling design, or an external-world fact.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path, PurePosixPath

from tools import completeness_metrics as scorer
from tools.training_readiness import components
from . import completion_statistics as stats

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / "evidence/learning_completion_v1"
AXES = {"text_groups", "root_groups", "source_groups", "template_groups", "lexeme_groups"}
ROW_FIELDS = {"id", "split", "objective_id", "stage_id", "text", "question", "input_mode",
              "kind", "root_groups", "source_groups", "template_groups", "lexeme_groups", "provenance_ref"}
EXPERIMENT_FIELDS = {"schema", "scope_id", "required_objective_ids", "holdout_axes",
                     "independence_axes", "exposure", "sampling", "rows", "interventions"}
FULL_PATH_OBLIGATIONS = {"sourceLicense", "hostInventory", "hostLicenses", "grammarLicense",
                         "realizationAligned", "RealizationContracts", "verbalSignifiedSingle",
                         "verbalSignifiedComposition", "referenceResolution", "externalCorrespondence"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return sha256(canonical(value).encode("utf-8")).hexdigest()


def implementation_fingerprints():
    paths = ("tools/lexical_training/completion_criteria.py",
             "tools/lexical_training/completion_statistics.py",
             "tools/completeness_metrics.py", "tools/training_readiness.py")
    return {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}


def read_bytes(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected a bounded regular JSON file")
    with path.open("rb") as stream:
        raw = stream.read(32 * 1024 * 1024 + 1)
    if len(raw) > 32 * 1024 * 1024:
        raise ValueError("JSON byte limit exceeded")
    return raw


def parse_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("Duplicate JSON key: " + key)
            out[key] = value
        return out
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))


def read_json(path):
    return parse_json(read_bytes(path))


def _fields(value, wanted, name):
    if type(value) is not dict or set(value) != set(wanted):
        raise ValueError(name + ": missing or unexpected fields")


def _text(value, name):
    if type(value) is not str or not value.strip() or len(value) > 200_000:
        raise ValueError(name + ": nonempty bounded string required")
    return value


def _ids(value, name, *, empty=False):
    if type(value) is not list or (not value and not empty):
        raise ValueError(name + ": list required")
    for item in value:
        _text(item, name)
    if len(set(value)) != len(value):
        raise ValueError(name + ": duplicate identity")
    return set(value)


def validate_policy(policy):
    fields = {"schema", "version", "status", "basis_commit", "authority", "confidence_family_alpha",
              "simultaneous_statistical_claims", "raw_exact_lower_min", "false_accept_upper_max",
              "unsupported_accept_upper_max", "premature_finalization_upper_max", "retention_lower_min",
              "paired_gain_lower_min", "critical_errors_max", "finite_reference_exact_required",
              "train_groups_per_stage_kind_min", "calibration_groups_per_stage_kind_min", "required_kinds",
              "required_interventions", "sampling_rule", "threshold_rule", "training_rule", "stop_rule"}
    _fields(policy, fields, "policy")
    if (policy["schema"] != "nabt.learning-completion-policy.v1"
            or policy["authority"] != "MEASUREMENT_POLICY_ONLY"
            or policy["status"] != "PROSPECTIVE_ACCEPTANCE_POLICY_NOT_ACHIEVEMENT"):
        raise ValueError("Unknown measurement policy authority")
    for key in ("version", "basis_commit", "sampling_rule", "threshold_rule", "training_rule", "stop_rule"):
        _text(policy[key], key)
    for key in ("confidence_family_alpha", "raw_exact_lower_min", "false_accept_upper_max",
                "unsupported_accept_upper_max", "premature_finalization_upper_max", "retention_lower_min"):
        value = policy[key]
        if type(value) not in {float, int} or not math.isfinite(value) or not 0 < value < 1:
            raise ValueError("Policy probability must be finite and strictly between zero and one")
    for key, expected in (("simultaneous_statistical_claims", 7), ("critical_errors_max", 0)):
        if type(policy[key]) is not int or policy[key] != expected:
            raise ValueError("Changed fixed policy gate count or zero-critical-error requirement")
    for key, expected in (("paired_gain_lower_min", 0), ("finite_reference_exact_required", 1)):
        if type(policy[key]) not in {int, float} or policy[key] != expected:
            raise ValueError("Changed strict improvement or finite exactness requirement")
    for key in ("train_groups_per_stage_kind_min", "calibration_groups_per_stage_kind_min"):
        if type(policy[key]) is not int or not 0 < policy[key] <= 1_000_000:
            raise ValueError("Invalid training intake floor")
    if _ids(policy["required_kinds"], "required kinds") != scorer.KINDS:
        raise ValueError("A mandatory assessment stratum was removed")
    if _ids(policy["required_interventions"], "required interventions") != {
            "withdraw_last_support", "retain_independent_support", "coordinate_reprojection", "scope_change"}:
        raise ValueError("A mandatory intervention was removed")
    return policy


def _owner_refs(refs):
    _ids(refs, "owner_refs")
    for relative in refs:
        p = PurePosixPath(relative)
        target = ROOT / p
        if (p.is_absolute() or ".." in p.parts or ".git" in p.parts or "\\" in relative
                or p.as_posix() != relative or not target.is_file()
                or not target.resolve().is_relative_to(ROOT.resolve())):
            raise ValueError("Unresolved owner reference: " + relative)


def load_contract():
    """Resolve every installed learning objective and owner path; grant no mastery."""
    from .curriculum import curriculum
    framework = curriculum()["learning_framework"]
    objectives = {row["id"]: row for row in framework["objectives"]}
    stages_doc = read_json(DIRECTORY / "stages.json")
    policy = validate_policy(read_json(DIRECTORY / "policy.json"))
    if stages_doc.get("schema") != "nabt.learning-completion-stages.v1":
        raise ValueError("Unknown stage contract")
    if policy.get("schema") != "nabt.learning-completion-policy.v1":
        raise ValueError("Unknown acceptance policy")
    stages = stages_doc["stages"]
    if [s["id"] for s in stages] != [f"L{i:02d}" for i in range(1, 14)]:
        raise ValueError("The thirteen stage identities must be retained in order")
    seen, covered, objective_counts = set(), set(), Counter()
    for stage in stages:
        _fields(stage, {"id", "label_ar", "prerequisites", "objective_ids", "required_outputs",
                        "counterexamples", "owner_refs", "training_actions"}, "stage")
        if not _ids(stage["prerequisites"], "prerequisites", empty=True) <= seen:
            raise ValueError("Stage prerequisites must precede their consumer")
        ids = _ids(stage["objective_ids"], "objective_ids")
        if not ids <= objectives.keys():
            raise ValueError("Unresolved existing curriculum objective")
        covered |= ids
        objective_counts.update(ids)
        seen.add(stage["id"])
        for key in ("required_outputs", "counterexamples", "owner_refs", "training_actions"):
            _ids(stage[key], key)
        _owner_refs(stage["owner_refs"])
    if covered != objectives.keys() or any(n != 1 for n in objective_counts.values()):
        raise ValueError("A preexisting learning objective was dropped")
    obligations = stages_doc.get("full_path_obligations")
    if type(obligations) is not list:
        raise ValueError("Full-path obligations must remain an explicit inventory")
    if _ids([o.get("id") for o in obligations], "full path obligations") != FULL_PATH_OBLIGATIONS:
        raise ValueError("A full-path obligation was dropped or replaced")
    for obligation in obligations:
        _fields(obligation, {"id", "label_ar", "required_evidence_ar", "owner_refs", "stage_ids"}, "full path obligation")
        _text(obligation["label_ar"], "obligation label")
        _text(obligation["required_evidence_ar"], "obligation evidence")
        _owner_refs(obligation["owner_refs"])
        if not _ids(obligation["stage_ids"], "obligation stages") <= seen:
            raise ValueError("Unresolved obligation stage")
    return {"policy": policy, "stages": stages, "objectives": objectives,
            "full_path_obligations": stages_doc["full_path_obligations"],
            "contract_sha256": digest({"policy": policy, "stages": stages_doc}),
            "framework_sha256": digest(framework)}


def _gate(identity, status, reason, measurement=None):
    return {"id": identity, "status": status, "reason": reason, "measurement": measurement}


def _predictions(reference, predictions):
    _fields(reference, {"schema", "version", "scope", "required_families", "cases"}, "reference")
    for key in ("schema", "version", "scope"):
        _text(reference[key], "reference " + key)
    if type(reference["cases"]) is not list:
        raise ValueError("Reference cases must be a list")
    for case in reference["cases"]:
        _fields(case, {"id", "family", "kind", "source_ref", "gold_readings", "gold_complete"}, "reference case")
        for key in ("id", "family", "kind", "source_ref"):
            _text(case[key], "case " + key)
        if type(case["gold_complete"]) is not bool:
            raise ValueError("Reference gold_complete must be a boolean assertion by the reference author")
    if type(predictions) is not list:
        raise ValueError("Predictions must be a list")
    for prediction in predictions:
        _fields(prediction, {"id", "status", "readings"}, "prediction")
    return scorer.evaluate(reference, predictions)


def _prepare(reference, experiment, contract):
    _fields(experiment, EXPERIMENT_FIELDS, "experiment")
    if experiment["schema"] != "nabt.learning-completion-experiment.v1":
        raise ValueError("Unknown experiment schema")
    _text(experiment["scope_id"], "scope_id")
    if experiment["scope_id"] != reference["scope"]:
        raise ValueError("Experiment and reference scopes differ")
    required = _ids(experiment["required_objective_ids"], "required objectives")
    if not required <= contract["objectives"].keys():
        raise ValueError("Unknown required objective")
    for key in ("holdout_axes", "independence_axes"):
        axes = _ids(experiment[key], key)
        if not axes <= AXES or "text_groups" not in axes:
            raise ValueError("Grouping axes must include derived text identity")
    if experiment["exposure"] not in {"PUBLIC_RETROSPECTIVE", "SEALED_NEW"}:
        raise ValueError("Unknown exposure")
    sampling = experiment["sampling"]
    _fields(sampling, {"kind", "population", "frame_ref", "design_ref"}, "sampling")
    if sampling["kind"] not in {"AUTHORED", "PROBABILITY_SAMPLE"}:
        raise ValueError("Unknown sampling kind")
    for key in ("population", "frame_ref", "design_ref"):
        _text(sampling[key], key)
    stages = {s["id"]: s for s in contract["stages"]}
    rows = experiment["rows"]
    if type(rows) is not list or not rows:
        raise ValueError("Absent measurement inventory")
    prepared = []
    for row in rows:
        _fields(row, ROW_FIELDS, "measurement row")
        for key in ("id", "text", "question", "provenance_ref"):
            _text(row[key], key)
        if row["split"] not in {"train", "calibration", "test"} or row["input_mode"] not in {"raw", "assisted"}:
            raise ValueError("Unknown split or input mode")
        if row["kind"] not in scorer.KINDS:
            raise ValueError("Unknown case kind")
        stage = stages.get(row["stage_id"])
        if stage is None or row["objective_id"] not in stage["objective_ids"]:
            raise ValueError("Objective is not in its declared stage")
        for axis in AXES - {"text_groups"}:
            _ids(row[axis], axis, empty=True)
        prepared.append(dict(row, text_groups=[sha256(row["text"].encode("utf-8")).hexdigest()]))
    _ids([r["id"] for r in prepared], "row ids")
    test = {r["id"]: r for r in prepared if r["split"] == "test"}
    cases = {c["id"]: c for c in reference["cases"]}
    if test.keys() != cases.keys():
        raise ValueError("Every reference target must have exactly one test metadata row")
    for key, row in test.items():
        if row["kind"] != cases[key]["kind"] or row["objective_id"] not in required:
            raise ValueError("Test kind or required objective mismatch")
    interventions = experiment["interventions"]
    if type(interventions) is not list:
        raise ValueError("Interventions must be a list")
    _ids([x.get("id") for x in interventions], "intervention ids", empty=True)
    for pair in interventions:
        _fields(pair, {"id", "before", "after", "type"}, "intervention")
        if pair["before"] == pair["after"] or not {pair["before"], pair["after"]} <= cases.keys():
            raise ValueError("An intervention needs two different measured targets")
        if pair["type"] not in contract["policy"]["required_interventions"]:
            raise ValueError("Unknown intervention type")
        before, after = cases[pair["before"]], cases[pair["after"]]
        if pair["type"] == "withdraw_last_support" and not (
                before["kind"] in {"positive", "ambiguity"} and after["kind"] == "needs_context"):
            raise ValueError("Last-support withdrawal requires acceptance then pending reference")
        same = before["kind"] == after["kind"] and set(before["gold_readings"]) == set(after["gold_readings"])
        if pair["type"] in {"retain_independent_support", "coordinate_reprojection"} and not same:
            raise ValueError("An invariant intervention must preserve the reference answer")
        if pair["type"] == "scope_change" and same:
            raise ValueError("A discriminating scope change must change its reference answer")
    return prepared, test


def _split_audit(rows, axes):
    result = components(rows, axes)
    if result["status"] != "MEASURED":
        return dict(result, status="NOT_MEASURED")
    by_id = {r["id"]: r for r in rows}
    overlaps = [g for g in result["groups"] if len({by_id[i]["split"] for i in g}) > 1]
    splits = {r["split"] for r in rows}
    status = "FAIL" if overlaps else ("PASS" if splits == {"train", "calibration", "test"} else "NOT_MEASURED")
    return dict(result, status=status, overlaps=overlaps, missing_splits=sorted({"train", "calibration", "test"} - splits))


def _conditional_gate(identity, value, threshold, *, upper=False, strict=False, eligible=False):
    if value is None or not eligible:
        return _gate(identity, "NOT_MEASURED", "NO_ELIGIBLE_INDEPENDENT_BLIND_DENOMINATOR", value)
    passed = value <= threshold if upper else (value > threshold if strict else value >= threshold)
    return _gate(identity, "PASS" if passed else "FAIL", "CONDITIONAL_ON_DECLARED_SAMPLING_DESIGN", value)


def evaluate_benchmark(reference, predictions, experiment, *, parent_predictions=None, control_predictions=None):
    """Measure supplied, separately frozen ACB reference agreement, not truth."""
    contract = load_contract()
    policy = contract["policy"]
    scores = _predictions(reference, predictions)
    rows, test = _prepare(reference, experiment, contract)
    parent = _predictions(reference, parent_predictions) if parent_predictions is not None else None
    control = _predictions(reference, control_predictions) if control_predictions is not None else None
    split_axes = sorted(set(experiment["holdout_axes"]) | set(experiment["independence_axes"]))
    split = _split_audit(rows, split_axes)
    split["effective_axes"] = split_axes
    by_id = {r["id"]: r for r in scores["cases"]}
    gates = [_gate("split_isolation", split["status"], "CONNECTED_GROUP_SPLIT_AUDIT", split)]
    modes = {}
    for mode in ("raw", "assisted"):
        selected = [r for r in scores["cases"] if test[r["id"]]["input_mode"] == mode]
        modes[mode] = scorer.ratio(sum(r["correct"] for r in selected), len(selected))
    raw = [row for row in rows if row["split"] == "test" and row["input_mode"] == "raw"]
    raw_ids = {r["id"] for r in raw}
    # Build connectivity before selecting a mode/stage/stratum. An excluded
    # assisted or training row can still connect two selected descendants.
    all_groups = components(rows, experiment["independence_axes"])
    if all_groups["status"] == "MEASURED" and raw:
        projected = [[i for i in group if i in raw_ids] for group in all_groups["groups"]]
        groups = {"status": "MEASURED", "groups": [group for group in projected if group],
                  "connection_universe": "ALL_EXPERIMENT_ROWS", "connection_universe_size": len(rows)}
    else:
        groups = {"status": "UNMEASURED", "groups": None, "missing_axes": all_groups.get("missing_axes", [])}
    kind_missing = sorted(set(policy["required_kinds"]) - {r["kind"] for r in raw})
    objective_missing = sorted(set(experiment["required_objective_ids"]) - {r["objective_id"] for r in raw})
    raw_positive_families = {by_id[r["id"]]["family"] for r in raw if r["kind"] in {"positive", "ambiguity"}}
    family_missing = sorted(set(reference["required_families"]) - raw_positive_families)
    raw_exact = bool(raw) and all(by_id[i]["correct"] for i in raw_ids)
    all_reference_correct = all(r["correct"] for r in scores["cases"])
    reference_complete = raw_exact and all_reference_correct and not kind_missing and not objective_missing and not family_missing
    gates.append(_gate("finite_reference_agreement", "PASS" if reference_complete else "FAIL",
                       "DECLARED_REFERENCE_ONLY_NO_CERTIFICATE_VERIFICATION",
                       {"raw": modes["raw"], "all_reference": scorer.ratio(sum(r["correct"] for r in scores["cases"]), len(scores["cases"])),
                        "missing_kinds": kind_missing, "missing_objectives": objective_missing,
                        "missing_positive_families": family_missing}))
    critical = sum(r["status"] in scorer.ACCEPTED for r in scores["cases"] if r["kind"] == "negative")
    critical += sum(r["status"] in scorer.FINAL for r in scores["cases"] if r["kind"] == "needs_context")
    critical += sum((r["fp"] or 0) > 0 for r in scores["cases"] if r["kind"] in {"positive", "ambiguity"})
    critical_n = len(scores["cases"])
    gates.append(_gate("no_forbidden_finalization_observed", "NOT_MEASURED" if not critical_n else ("PASS" if critical == 0 else "FAIL"),
                       "REFERENCE_EXTRA_READINGS_NEGATIVES_AND_CONTEXT", scorer.ratio(critical, critical_n)))
    alpha = policy["confidence_family_alpha"] / policy["simultaneous_statistical_claims"]
    bounds = {"alpha_per_claim": alpha, "groups": groups, "raw_exact_lower": None,
              "false_accept_upper": None, "premature_finalization_upper": None,
              "unsupported_accept_upper": None, "parent": None, "control": None}
    if groups["status"] == "MEASURED":
        clusters = groups["groups"]
        outcomes = [all(by_id[i]["correct"] for i in group) for group in clusters]
        bounds["raw_exact_lower"] = stats.binomial_lower(sum(outcomes), len(outcomes), alpha)
        for kind, field, bad_statuses in (("negative", "false_accept_upper", scorer.ACCEPTED),
                                         ("needs_context", "premature_finalization_upper", scorer.FINAL)):
            relevant = [[i for i in group if by_id[i]["kind"] == kind] for group in clusters]
            relevant = [group for group in relevant if group]
            errors = sum(any(by_id[i]["status"] in bad_statuses for i in group) for group in relevant)
            bounds[field] = stats.binomial_upper(errors, len(relevant), alpha)
            bounds[field + "_counts"] = {"errors": errors, "independent_groups": len(relevant)}
        accepted = [[i for i in group if by_id[i]["status"] in scorer.ACCEPTED] for group in clusters]
        accepted = [group for group in accepted if group]
        unsupported = sum(any((by_id[i]["fp"] or 0) > 0 or by_id[i]["kind"] == "needs_context"
                              for i in group) for group in accepted)
        bounds["unsupported_accept_upper"] = stats.binomial_upper(unsupported, len(accepted), alpha)
        bounds["unsupported_accept_upper_counts"] = {"errors": unsupported, "accepted_groups": len(accepted)}
        for name, baseline in (("parent", parent), ("control", control)):
            if baseline is not None:
                previous = {r["id"]: r for r in baseline["cases"]}
                missing = [i for i in sorted(raw_ids) if previous[i]["status"] == "missing"]
                bounds["missing_" + name + "_ids"] = missing
                if missing:
                    continue
                old = [all(previous[i]["correct"] for i in group) for group in clusters]
                bounds[name] = stats.paired_bounds(old, outcomes, alpha)
                if name == "control":
                    # Only the control difference belongs to the seven-claim
                    # simultaneous family; do not publish an eighth bound.
                    bounds[name].pop("retention_lower", None)
    eligible = (split["status"] == "PASS" and groups["status"] == "MEASURED"
                and experiment["exposure"] == "SEALED_NEW"
                and experiment["sampling"]["kind"] == "PROBABILITY_SAMPLE")
    for identity, field, threshold, upper in (
        ("raw_quality", "raw_exact_lower", policy["raw_exact_lower_min"], False),
        ("false_accept_risk", "false_accept_upper", policy["false_accept_upper_max"], True),
        ("unsupported_accept_risk", "unsupported_accept_upper", policy["unsupported_accept_upper_max"], True),
        ("premature_finalization_risk", "premature_finalization_upper", policy["premature_finalization_upper_max"], True)):
        gates.append(_conditional_gate(identity, bounds[field], threshold, upper=upper, eligible=eligible))
    retained = bounds["parent"]["retention_lower"] if bounds["parent"] else None
    gates.append(_conditional_gate("retention", retained, policy["retention_lower_min"], eligible=eligible))
    for name in ("parent", "control"):
        lower = bounds[name]["delta_lower"] if bounds[name] else None
        gates.append(_conditional_gate("gain_over_" + name, lower, policy["paired_gain_lower_min"], strict=True, eligible=eligible))
    interventions = []
    for pair in experiment["interventions"]:
        correct = by_id[pair["before"]]["correct"] and by_id[pair["after"]]["correct"]
        interventions.append(dict(pair, reference_pair_correct=correct,
                                  authority="REFERENCE_INTERVENTION_AGREEMENT_ONLY"))
    missing_interventions = sorted(set(policy["required_interventions"]) - {p["type"] for p in interventions})
    gates.append(_gate("interventions", "NOT_MEASURED" if missing_interventions else ("PASS" if all(p["reference_pair_correct"] for p in interventions) else "FAIL"),
                       "OWNER_WITHDRAWAL_AND_REPROJECTION_REPLAY_REMAIN_REQUIRED", missing_interventions))
    stage_measurements = []
    queue = []
    active_stages = {s["id"] for s in contract["stages"] if set(s["objective_ids"]) & set(experiment["required_objective_ids"])}
    for stage in contract["stages"]:
        relevant = [r for r in raw if r["stage_id"] == stage["id"]]
        stage_measurements.append({"stage_id": stage["id"], "raw_exact": scorer.ratio(
            sum(by_id[r["id"]]["correct"] for r in relevant), len(relevant)),
            "licensed_path": "NOT_MEASURED", "reason": "MISSING_FULL_PATH_OWNER_ADAPTER"})
        if stage["id"] not in active_stages:
            continue
        for kind in policy["required_kinds"]:
            for part, required in (("train", policy["train_groups_per_stage_kind_min"]),
                                   ("calibration", policy["calibration_groups_per_stage_kind_min"])):
                members = [r for r in rows if r["stage_id"] == stage["id"] and r["kind"] == kind and r["split"] == part]
                identities = {r["id"] for r in members}
                available = (sum(bool(identities.intersection(group)) for group in all_groups["groups"])
                             if all_groups["status"] == "MEASURED" else None)
                queue.append({"stage_id": stage["id"], "kind": kind, "split": part,
                              "minimum_groups": required, "available_groups": available,
                              "additional_groups": max(0, required - available) if available is not None else None})
    missing_training_objectives = [{"objective_id": identity, "split": part}
        for identity in experiment["required_objective_ids"] for part in ("train", "calibration")
        if not any(r["objective_id"] == identity and r["split"] == part and r["input_mode"] == "raw" for r in rows)]
    gates.append(_gate("training_intake", "PASS" if not missing_training_objectives and all(q["additional_groups"] == 0 for q in queue) else "NOT_MEASURED",
                       "INTAKE_FLOOR_NOT_PROOF_OF_LEARNING", queue))
    # No string/boolean/status from the experiment can discharge these owners.
    completion = _gate("licensed_completion", "NOT_MEASURED", "MISSING_FULL_PATH_OWNER_ADAPTER",
                       contract["full_path_obligations"])
    gates.append(completion)
    return {"schema": "nabt.learning-completion-assessment.v1", "authority": "REFERENCE_AGREEMENT_ONLY",
            "integrity_status": "PASS", "contract_sha256": contract["contract_sha256"],
            "measurement_source_sha256": implementation_fingerprints(),
            "reference_sha256": digest(reference), "experiment_sha256": digest(experiment),
            "predictions_sha256": digest(predictions), "reference_scores": scores,
            "split_audit": split, "mode_scores": modes, "cluster_metrics": bounds,
            "statistical_gates_eligible_on_declared_design": eligible,
            "sampling_verification": "DECLARED_DESIGN_NOT_INDEPENDENTLY_ATTESTED",
            "prediction_execution_verified": False,
            "preregistration_verification": "EXTERNAL_OBLIGATION_NOT_ESTABLISHED_BY_HASH",
            "stage_measurements": stage_measurements, "interventions": interventions,
            "missing_training_objectives": missing_training_objectives,
            "training_queue": queue, "gates": gates, "licensed_completion": completion,
            "universal_arabic_completeness": "NOT_INFERRED"}


def current_report(*, replay_v14=False):
    contract = load_contract()
    policy = contract["policy"]
    report = {"schema": "nabt.learning-completion-readiness.v1", "authority": "MEASUREMENT_POLICY_ONLY",
              "contract_sha256": contract["contract_sha256"], "framework_sha256": contract["framework_sha256"],
              "measurement_source_sha256": implementation_fingerprints(),
              "stage_count": len(contract["stages"]), "objective_count": len(contract["objectives"]),
              "policy": policy, "stages": contract["stages"], "full_path_obligations": contract["full_path_obligations"],
              "baseline_replay": "NOT_RUN", "gates": [], "training_queue": []}
    for stage in contract["stages"]:
        report["training_queue"].append({"stage_id": stage["id"], "objective_ids": stage["objective_ids"],
            "status": "NEEDS_SOURCE_MAPPING_AND_INDEPENDENT_GOLD", "mapped_verified_cases": None,
            "next_actions": stage["training_actions"]})
    report["gates"] = [
        _gate("frozen_target_inventory", "NOT_MEASURED", "CURRICULUM_OBJECTIVES_ARE_NOT_OCCURRENCE_QUESTION_TARGETS"),
        _gate("full_path_owner_replay", "NOT_MEASURED", "MISSING_FULL_PATH_OWNER_ADAPTER"),
        _gate("new_blind_assessment", "NOT_MEASURED", "NO_NEW_SEALED_CORPUS_SUPPLIED"),
        _gate("linguistic_reference_adequacy", "NOT_MEASURED", "REQUIRES_SOURCE_AND_INDEPENDENT_ADJUDICATION"),
        _gate("external_judgment_evidence", "NOT_MEASURED", "REQUIRES_DOMAIN_SPECIFIC_WITNESSES")]
    alpha = policy["confidence_family_alpha"] / policy["simultaneous_statistical_claims"]
    report["sample_planning"] = {
        "alpha_per_claim": alpha,
        "zero_error_groups_one_claim_95": stats.zero_error_required_n(policy["false_accept_upper_max"], .05),
        "zero_error_groups_simultaneous_policy": stats.zero_error_required_n(policy["false_accept_upper_max"], alpha),
        "assumption": "Independent Bernoulli units from a justified population sampling design; not arbitrary generated rows"}
    if replay_v14:
        from . import cumulative_v14_audit as old
        full, control = old.replay(), old.replay(old.DIRECTORY / "control")
        retained = full["parent_correct_unique"] - full["lost_from_parent_unique"]
        report["baseline_replay"] = "PASS"
        report["v14"] = {"full": full, "control": control,
                         "parent_retention_point": scorer.ratio(retained, full["parent_correct_unique"]),
                         "assessment_exposure": "PUBLIC_RETROSPECTIVE",
                         "independent_cluster_intervals": "NOT_MEASURED",
                         "semantic_path_coverage": "NOT_MEASURED"}
        report["gates"] += [
            _gate("v14_artifact_reproduction", "PASS", "FRESH_OWNER_REPLAY_BOTH_VARIANTS"),
            _gate("historical_retention_point_diagnostic", "PASS" if retained / full["parent_correct_unique"] >= policy["retention_lower_min"] else "FAIL",
                  "DESCRIPTIVE_ONLY_NOT_BLIND_RETENTION_CERTIFICATE", report["v14"]["parent_retention_point"]),
            _gate("historical_control_comparison", "PASS" if full["final_correct_unique"] > control["final_correct_unique"] else "FAIL",
                  "DESCRIPTIVE_ONLY_NOT_ARCHITECTURAL_SUPERIORITY", {"full": full["final_correct_unique"], "control": control["final_correct_unique"]})]
    report["licensed_completion"] = _gate("licensed_completion", "NOT_MEASURED", "OPEN_TARGET_AND_OWNER_OBLIGATIONS")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-v14", action="store_true", help="Recompute both installed V14 variants with the original owner")
    parser.add_argument("--benchmark", type=Path, help="Frozen reference/predictions/experiment developer bundle")
    parser.add_argument("--benchmark-sha256", help="Independently retained SHA256 of the complete benchmark bytes")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-completion", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.benchmark:
            if args.baseline_v14:
                raise ValueError("Use one assessment mode at a time")
            raw = read_bytes(args.benchmark)
            if not args.benchmark_sha256 or sha256(raw).hexdigest() != args.benchmark_sha256:
                raise ValueError("Benchmark differs from the independently retained byte commitment")
            pack = parse_json(raw)
            _fields(pack, {"reference", "predictions", "experiment", "parent_predictions", "control_predictions"}, "benchmark")
            report = evaluate_benchmark(**pack)
            report["benchmark_bytes_sha256"] = args.benchmark_sha256
        else:
            if args.benchmark_sha256:
                raise ValueError("A benchmark commitment requires its benchmark")
            report = current_report(replay_v14=args.baseline_v14)
        report["evaluator_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(canonical({"status": "INVALID_INPUT", "error": str(exc), "authority": "NONE"}))
        return 1
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        print(canonical({"report": str(args.output), "licensed_completion": report["licensed_completion"]["status"]}))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 2 if args.require_completion and report["licensed_completion"]["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
