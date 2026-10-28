"""Validate a work registry; declared results never become checked evidence."""
from __future__ import annotations

import json
import math
from pathlib import Path
import re


SCHEMA = "nabt.entropy-framework.registry.v1"
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_INTEGER_DIGITS = 4096
DEFAULT_REGISTRY = Path(__file__).with_name("registry.json")
WORK_STATES = {
    "PLANNED", "READY", "IN_PROGRESS", "IN_REVIEW", "DELIVERED", "BLOCKED",
}
GATE_STATES = {"NOT_MEASURED", "PASS", "FAIL", "STALE", "NOT_APPLICABLE"}


class FrameworkError(ValueError):
    """Malformed or inconsistent organizational/measurement input."""


class FrameworkResourceError(FrameworkError):
    """Input processing exceeded a declared or interpreter resource budget."""


def require(condition, message):
    if not condition:
        raise FrameworkError(message)


def nonempty_string(value, where):
    require(type(value) is str and bool(value.strip()), f"{where}: nonempty string required")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as error:
        raise FrameworkError(f"{where}: non-scalar Unicode string") from error
    return value


def natural(value, where):
    require(type(value) is int and value >= 0, f"{where}: nonnegative integer required")
    return value


def enum_value(value, choices, where):
    require(type(value) is str and value in choices, f"{where}: unsupported value")
    return value


def object_value(value, where):
    require(type(value) is dict, f"{where}: object required")
    return value


def list_value(value, where):
    require(type(value) is list, f"{where}: list required")
    return value


def strings(value, where):
    list_value(value, where)
    for item in value:
        nonempty_string(item, where)
    require(len(set(value)) == len(value), f"{where}: duplicate member")
    return value


def sha(value, where, length=40):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None,
            f"{where}: lowercase {length}-digit hexadecimal identity required")


def load_json(path):
    """Read strict UTF-8 JSON, rejecting repeated keys and nonfinite numbers."""
    path = Path(path)
    with path.open("rb") as handle:
        raw = handle.read(MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES:
        raise FrameworkResourceError("JSON exceeds the declared 8 MiB input limit")

    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"duplicate JSON key: {key!r}")
            result[key] = value
        return result

    def constant(value):
        raise FrameworkError(f"nonfinite JSON constant: {value}")

    def finite_float(value):
        number = float(value)
        require(math.isfinite(number), f"nonfinite JSON number: {value}")
        return number

    def bounded_integer(value):
        if len(value.lstrip("-")) > MAX_INTEGER_DIGITS:
            raise FrameworkResourceError("JSON integer exceeds the 4096-digit input budget")
        try:
            return int(value)
        except ValueError as error:
            raise FrameworkResourceError("JSON integer exceeds the interpreter conversion budget") from error

    try:
        result = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=pairs,
                            parse_constant=constant, parse_float=finite_float,
                            parse_int=bounded_integer)
        # Escaped lone surrogates are accepted by Python's JSON decoder, but
        # cannot be represented as UTF-8. Inspect metadata too, not only fields
        # interpreted by the registry validator.
        pending = [result]
        while pending:
            item = pending.pop()
            if type(item) is str:
                item.encode("utf-8", errors="strict")
            elif type(item) is list:
                pending.extend(item)
            elif type(item) is dict:
                pending.extend(item.keys())
                pending.extend(item.values())
        return result
    except RecursionError as error:
        raise FrameworkResourceError("JSON nesting exceeds the interpreter budget") from error
    except (UnicodeError, json.JSONDecodeError) as error:
        raise FrameworkError(f"invalid JSON: {error}") from error


def indexed(rows, where):
    list_value(rows, where)
    result = {}
    for row in rows:
        object_value(row, where)
        identity = nonempty_string(row.get("id"), f"{where}.id")
        require(identity not in result, f"{where}: duplicate id {identity}")
        result[identity] = row
    return result


def dependency_order(nodes, where):
    """Kahn ordering avoids recursive traversal limits for large registries."""
    remaining = {}
    dependants = {identity: [] for identity in nodes}
    for identity, row in nodes.items():
        deps = strings(row.get("depends_on"), f"{where}.{identity}.depends_on")
        require(set(deps) <= nodes.keys(), f"{where}.{identity}: unknown dependency")
        require(identity not in deps, f"{where}.{identity}: self dependency")
        remaining[identity] = len(deps)
        for dep in deps:
            dependants[dep].append(identity)
    queue = [identity for identity in nodes if not remaining[identity]]
    result = []
    for identity in queue:
        result.append(identity)
        for child in dependants[identity]:
            remaining[child] -= 1
            if remaining[child] == 0:
                queue.append(child)
    require(len(result) == len(nodes), f"{where}: dependency cycle")
    return result


def _dataset(dataset, where):
    object_value(dataset, where)
    enum_value(dataset.get("status"), {"not_created", "draft", "frozen"}, f"{where}.status")
    nonempty_string(dataset.get("unit"), f"{where}.unit")
    size = dataset.get("size")
    if size is not None:
        natural(size, f"{where}.size")
        require(size > 0, f"{where}: required population cannot be empty")
    if dataset["status"] == "frozen":
        require(size is not None, f"{where}: frozen dataset needs a size")
        nonempty_string(dataset.get("version"), f"{where}.version")
        sha(dataset.get("sha256"), f"{where}.sha256", 64)
    if "slices" in dataset:
        slices = object_value(dataset["slices"], f"{where}.slices")
        require(bool(slices), f"{where}: empty slices")
        for name, count in slices.items():
            nonempty_string(name, f"{where}.slice name")
            natural(count, f"{where}.slices.{name}")
        require(size is not None and sum(slices.values()) == size,
                f"{where}: slice denominators do not sum to population")
    if dataset["unit"] == "minimal_pair":
        require(size is not None, f"{where}: pair denominator missing")
        total = natural(dataset.get("individual_inputs"), f"{where}.individual_inputs")
        require(total == 2 * size, f"{where}: pair and individual denominators differ")
    if "positive_distinct_frames" in dataset or "positive_surface_variants" in dataset:
        frames = natural(dataset.get("positive_distinct_frames"), f"{where}.positive_distinct_frames")
        variants = natural(dataset.get("positive_surface_variants"), f"{where}.positive_surface_variants")
        require(frames > 0 and variants > 0 and
                frames * variants == dataset.get("slices", {}).get("positive_in_scope"),
                f"{where}: frame and surface denominators differ")


def validate_registry(registry):
    """Validate metadata consistency only, including declared PASS obligations.

    Evidence records remain supplied descriptions. No file hash, executable,
    theorem, linguistic interpretation, or result is authenticated here.
    """
    object_value(registry, "registry")
    require(registry.get("schema") == SCHEMA, "unsupported registry schema")
    nonempty_string(registry.get("framework_id"), "framework_id")
    baseline = object_value(registry.get("baseline"), "baseline")
    sha(baseline.get("nabt_commit"), "baseline.nabt_commit")
    for key in ("mashru_commit", "mashru_vendor_nabt_commit"):
        if key in baseline:
            sha(baseline[key], f"baseline.{key}")
    require(set(strings(registry.get("work_states"), "work_states")) == WORK_STATES,
            "work_states differs from the installed registry schema")
    require(set(strings(registry.get("gate_states"), "gate_states")) == GATE_STATES,
            "gate_states differs from the installed registry schema")
    roles = indexed(registry.get("roles"), "roles")
    layers = indexed(registry.get("layers"), "layers")
    gates = indexed(registry.get("gates"), "gates")
    tasks = indexed(registry.get("tasks"), "tasks")
    evidence = indexed(registry.get("evidence_records"), "evidence_records")
    capabilities = indexed(registry.get("capabilities", []), "capabilities")
    require(bool(roles) and bool(layers) and bool(gates), "roles, layers and gates must be nonempty")
    gate_order = dependency_order(gates, "gates")
    task_order = dependency_order(tasks, "tasks")
    for identity, row in evidence.items():
        require(type(row.get("gate_id")) is str and row["gate_id"] in gates,
                f"evidence {identity}: unknown gate")
        enum_value(row.get("reported_outcome"), {"PASS", "FAIL"}, f"evidence {identity}.reported_outcome")
        nonempty_string(row.get("scope"), f"evidence {identity}.scope")
        nonempty_string(row.get("reference"), f"evidence {identity}.reference")
        binding = object_value(row.get("run_identity"), f"evidence {identity}.run_identity")
        sha(binding.get("code_commit"), f"evidence {identity}.code_commit")
        for key in ("toolchain", "suite_version", "evaluator_version"):
            nonempty_string(binding.get(key), f"evidence {identity}.{key}")
        for key in ("dataset_sha256", "gold_sha256", "evaluator_sha256"):
            sha(binding.get(key), f"evidence {identity}.{key}", 64)
        counts = object_value(row.get("required_checks"), f"evidence {identity}.required_checks")
        for key in ("passed", "failed", "skipped", "missing"):
            natural(counts.get(key), f"evidence {identity}.required_checks.{key}")
        if row["reported_outcome"] == "PASS":
            require(counts["passed"] > 0 and
                    counts["failed"] == counts["skipped"] == counts["missing"] == 0,
                    f"evidence {identity}: reported PASS has empty or unexecuted required checks")
    for identity, row in gates.items():
        nonempty_string(row.get("title"), f"gate {identity}.title")
        nonempty_string(row.get("scope"), f"gate {identity}.scope")
        enum_value(row.get("status"), GATE_STATES, f"gate {identity}.status")
        requirements = strings(row.get("requirements"), f"gate {identity}.requirements")
        require(bool(requirements), f"gate {identity}: no acceptance requirements")
        _dataset(row.get("dataset"), f"gate {identity}.dataset")
        ids = strings(row.get("evidence_ids"), f"gate {identity}.evidence_ids")
        require(set(ids) <= evidence.keys(), f"gate {identity}: dangling evidence reference")
        for item in ids:
            require(evidence[item]["gate_id"] == identity and
                    evidence[item]["scope"] == row["scope"],
                    f"gate {identity}: evidence bound to a different gate or scope")
        if row["status"] == "NOT_MEASURED":
            require(not ids and row.get("baseline") is None,
                    f"gate {identity}: unmeasured target has measured evidence/baseline")
        if row["status"] in {"PASS", "FAIL", "STALE"}:
            require(bool(ids), f"gate {identity}: reported result needs evidence references")
        if row["status"] == "PASS":
            require(row["dataset"]["status"] == "frozen", f"gate {identity}: PASS before dataset freeze")
            require(all(gates[dep]["status"] == "PASS" for dep in row["depends_on"]),
                    f"gate {identity}: PASS with an unsatisfied prerequisite")
            require(all(evidence[item]["reported_outcome"] == "PASS" for item in ids),
                    f"gate {identity}: PASS with failing evidence")
            for item in ids:
                run = evidence[item]["run_identity"]
                require(run["dataset_sha256"] == row["dataset"]["sha256"] and
                        run["suite_version"] == row["dataset"]["version"],
                        f"gate {identity}: evidence dataset identity differs")
        if row["status"] == "NOT_APPLICABLE":
            nonempty_string(row.get("not_applicable_reason"), f"gate {identity}.not_applicable_reason")
    for identity, row in capabilities.items():
        enum_value(row.get("state"), {"PLANNED", "SOURCES_FROZEN", "IMPLEMENTED_AWAITING_EVALUATION", "EVALUATED"},
                   f"capability {identity}.state")
        require(type(row.get("gate_id")) is str and row["gate_id"] in gates,
                f"capability {identity}: unknown parent gate")
        nonempty_string(row.get("scope"), f"capability {identity}.scope")
        require(row["scope"] == gates[row["gate_id"]]["scope"],
                f"capability {identity}: scope differs from declared parent measurement")
        ids = strings(row.get("evidence_ids"), f"capability {identity}.evidence_ids")
        require(set(ids) <= evidence.keys(), f"capability {identity}: dangling evidence reference")
        for item in ids:
            require(evidence[item]["gate_id"] == row["gate_id"] and
                    evidence[item]["scope"] == row["scope"],
                    f"capability {identity}: evidence scope mismatch")
            dataset = gates[row["gate_id"]]["dataset"]
            run = evidence[item]["run_identity"]
            require(dataset["status"] == "frozen" and
                    run["dataset_sha256"] == dataset["sha256"] and
                    run["suite_version"] == dataset["version"],
                    f"capability {identity}: evidence dataset identity differs")
        if row["state"] == "EVALUATED":
            require(bool(ids), f"capability {identity}: evaluated state needs reported run")
        else:
            require(not ids, f"capability {identity}: unevaluated state has run evidence")
    for identity, row in tasks.items():
        nonempty_string(row.get("title"), f"task {identity}.title")
        nonempty_string(row.get("deliverable"), f"task {identity}.deliverable")
        require(type(row.get("owner_role")) is str and row["owner_role"] in roles,
                f"task {identity}: unknown owner")
        require(type(row.get("reviewer_role")) is str and row["reviewer_role"] in roles,
                f"task {identity}: unknown reviewer")
        require(row["owner_role"] != row["reviewer_role"], f"task {identity}: reviewer equals owner")
        enum_value(row.get("work_status"), WORK_STATES, f"task {identity}.work_status")
        enum_value(row.get("gate_status"), GATE_STATES, f"task {identity}.gate_status")
        ids = strings(row.get("evidence_ids"), f"task {identity}.evidence_ids")
        require(set(ids) <= evidence.keys(), f"task {identity}: dangling evidence reference")
        links = strings(row.get("gates"), f"task {identity}.gates")
        require(set(links) <= gates.keys(), f"task {identity}: unknown gate")
        strings(row.get("blockers"), f"task {identity}.blockers")
        if row["gate_status"] == "PASS":
            require(bool(links) and all(gates[g]["status"] == "PASS" for g in links),
                    f"task {identity}: PASS without passing linked gates")
        if row["work_status"] == "READY":
            require(all(tasks[dep]["work_status"] == "DELIVERED" for dep in row["depends_on"]),
                    f"task {identity}: READY before prerequisites delivered")
    release = object_value(registry.get("release_policy"), "release_policy")
    require(type(release.get("required_skips_allowed")) is int and
            release["required_skips_allowed"] == 0, "required skips must be zero")
    for key in ("empty_required_suite_allowed", "stale_required_evidence_allowed",
                "optional_omissions_count_as_success", "nabt_depends_on_mashru_release"):
        require(release.get(key) is False, f"release_policy.{key} must be false")
    return {"schema": "nabt.entropy-framework.validation.v1", "valid": True,
            "authority": "METADATA_CONSISTENCY_ONLY", "semantic_authority": "NONE",
            "evidence_verified": False, "gate_execution": "NOT_PERFORMED",
            "roles": len(roles), "layers": len(layers), "gates": len(gates),
            "tasks": len(tasks), "capabilities": len(capabilities),
            "gate_order": gate_order, "task_order": task_order}


def report_registry(registry):
    validation = validate_registry(registry)
    gates = {row["id"]: row for row in registry["gates"]}
    tasks = {row["id"]: row for row in registry["tasks"]}
    return {
        "schema": "nabt.entropy-framework.report.v1",
        "authority": "DECLARED_RECORDS_ONLY", "semantic_authority": "NONE",
        "release_admission": "NOT_EVALUATED", "evidence_verified": False,
        "validation": validation, "baseline": registry["baseline"],
        "scoped_capabilities": [{"id": row["id"], "state": row["state"],
                                 "gate_id": row["gate_id"], "scope": row["scope"],
                                 "evidence_ids": row["evidence_ids"],
                                 "evidence_verified": False,
                                 "parent_gate_admission": "NOT_EVALUATED"}
                                for row in registry.get("capabilities", [])],
        "gates": [{"id": identity, "title": gates[identity]["title"],
                   "scope": gates[identity]["scope"],
                   "reported_status": gates[identity]["status"],
                   "verification_status": "NOT_PERFORMED",
                   "dataset": gates[identity]["dataset"],
                   "evidence_ids": gates[identity]["evidence_ids"],
                   "unpassed_prerequisites": [dep for dep in gates[identity]["depends_on"]
                                              if gates[dep]["status"] != "PASS"]}
                  for identity in validation["gate_order"]],
        "tasks": [{"id": identity, "title": tasks[identity]["title"],
                   "work_status": tasks[identity]["work_status"],
                   "owner_role": tasks[identity]["owner_role"],
                   "reviewer_role": tasks[identity]["reviewer_role"],
                   "undelivered_prerequisites": [dep for dep in tasks[identity]["depends_on"]
                                                 if tasks[dep]["work_status"] != "DELIVERED"]}
                  for identity in validation["task_order"]],
    }
