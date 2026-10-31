"""Validate a work registry; declared results never become checked evidence."""
from __future__ import annotations

import json
from hashlib import sha256
import math
from pathlib import Path
import re


SCHEMA = "nabt.entropy-framework.registry.v2"
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_INTEGER_DIGITS = 4096
DEFAULT_REGISTRY = Path(__file__).with_name("registry.json")
WORK_STATES = {
    "PLANNED", "READY", "IN_PROGRESS", "IN_REVIEW", "DELIVERED", "BLOCKED",
}
MEASUREMENT_STATES = {"NOT_MEASURED", "MEASURED", "STALE", "NOT_APPLICABLE"}
AUTHORITY_FIELDS = {
    "admission", "authority", "semantic_authority", "evidence_verified",
    "authenticated", "release_admission", "verification_status",
}
RULE_REQUIRED_FIELDS = (
    "id", "version", "operation_kind", "source_refs", "interpretation_id", "scope",
    "preconditions", "exceptions", "input_type", "output_type", "implementation_ref",
    "proof_refs", "open_assumptions", "test_suite_ref", "dependencies", "review_state",
)
OPERATION_KINDS = ("FILTER", "TRANSFORM", "BIND", "INFER", "MEASURE")
RULE_PROVENANCE_POLICY = "record source integrity separately from interpretation validity"
FRESHNESS_IDENTITY_FIELDS = (
    "code_commit", "build_id", "toolchain", "binary_digest", "source_digests",
    "rules_versions", "dataset_digest", "gold_digest", "evaluator_digest",
    "configuration", "scope",
)
FRESHNESS_POLICY = (
    "retain historical result; invalidate current applicability only along affected "
    "dependencies; revalidate or recompute"
)
FRESHNESS_ABSENCE_POLICY = "missing evidence suspends support; it does not prove negation"
MIGRATION_SOURCE = {
    "source_schema": "nabt.entropy-framework.registry.v1",
    "source_commit": "c2c072e17802b62c13109cee7c087b7b58895a1a",
    "source_path": "tools/entropy_framework/registry.json",
    "source_sha256": "09ad43d5602e5f00fa3ea50b8bae89dbea2aa064b77a604dea1a80a910a8c8bb",
}


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


def load_json(path, *, with_sha256=False):
    """Read strict UTF-8 JSON, rejecting repeated keys and nonfinite numbers.

    Optional identity is the digest of the same bounded byte buffer that was
    parsed, never a separate file read that could identify a different snapshot.
    """
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
        return (result, sha256(raw).hexdigest()) if with_sha256 else result
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


def validate_base_contracts(registry):
    """Check installed metadata invariants, never a caller-selected lower bar.

    The optional organization is separately versioned. Its owner references do
    not belong to this base projection, including when the base is referenced.
    """
    object_value(registry, "registry")
    rule = object_value(registry.get("rule_contract"), "rule_contract")
    require(set(rule) - {"organization"} ==
            {"required", "operation_kinds", "provenance_policy"},
            "rule_contract: exact base fields and optional organization required")
    for field, expected in (("required", RULE_REQUIRED_FIELDS),
                            ("operation_kinds", OPERATION_KINDS)):
        actual = strings(rule.get(field), "rule_contract." + field)
        require(set(actual) == set(expected),
                "rule_contract." + field + ": differs from installed vocabulary")
    enum_value(rule["provenance_policy"], (RULE_PROVENANCE_POLICY,),
               "rule_contract.provenance_policy")
    freshness = object_value(registry.get("evidence_freshness"), "evidence_freshness")
    require(set(freshness) == {"identity", "policy", "absence_policy"},
            "evidence_freshness: exact fields required")
    identity = strings(freshness.get("identity"), "evidence_freshness.identity")
    require(set(identity) == set(FRESHNESS_IDENTITY_FIELDS),
            "evidence_freshness.identity: differs from installed vocabulary")
    enum_value(freshness["policy"], (FRESHNESS_POLICY,), "evidence_freshness.policy")
    enum_value(freshness["absence_policy"], (FRESHNESS_ABSENCE_POLICY,),
               "evidence_freshness.absence_policy")
    return {
        "rule_contract": {"required": list(rule["required"]),
                          "operation_kinds": list(rule["operation_kinds"]),
                          "provenance_policy": rule["provenance_policy"]},
        "evidence_freshness": {"identity": list(freshness["identity"]),
                               "policy": freshness["policy"],
                               "absence_policy": freshness["absence_policy"]},
    }


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
    if "additional_denominators" in dataset:
        denominators = object_value(dataset["additional_denominators"], f"{where}.additional_denominators")
        require(bool(denominators), f"{where}: empty additional denominators")
        for name, count in denominators.items():
            nonempty_string(name, f"{where}.denominator name")
            natural(count, f"{where}.additional_denominators.{name}")


def _no_authority_fields(row, where):
    require(not (AUTHORITY_FIELDS & row.keys()), f"{where}: authority is not an input field")


def _measurement(gate, evidence):
    where = f"gate {gate['id']}.measurement"
    value = object_value(gate.get("measurement"), where)
    _no_authority_fields(value, where)
    require(set(value) == {"state", "reported_outcome", "evidence_ids", "reason"},
            f"{where}: exact measurement fields required")
    state = enum_value(value["state"], MEASUREMENT_STATES, f"{where}.state")
    reason = value["reason"]
    if reason is not None:
        nonempty_string(reason, f"{where}.reason")
    ids = strings(value["evidence_ids"], f"{where}.evidence_ids")
    require(set(ids) <= evidence.keys(), f"{where}: dangling evidence reference")
    for identity in ids:
        item = evidence[identity]
        require(item["gate_id"] == gate["id"] and item["scope"] == gate["scope"],
                f"{where}: evidence bound to a different gate or scope")
    if state in {"NOT_MEASURED", "NOT_APPLICABLE"}:
        require(value["reported_outcome"] is None and not ids,
                f"{where}: unmeasured state cannot carry a result")
    else:
        outcome = enum_value(value["reported_outcome"], {"PASS", "FAIL"},
                             f"{where}.reported_outcome")
        require(bool(ids), f"{where}: reported result needs evidence references")
        outcomes = [evidence[identity]["reported_outcome"] for identity in ids]
        require((outcome == "PASS" and all(item == "PASS" for item in outcomes)) or
                (outcome == "FAIL" and "FAIL" in outcomes),
                f"{where}: outcome differs from selected evidence")
    if state in {"STALE", "NOT_APPLICABLE"}:
        require(reason is not None, f"{where}: state requires a reason")
    if state == "MEASURED":
        dataset = gate["dataset"]
        require(dataset["status"] == "frozen", f"{where}: measurement before dataset freeze")
        for identity in ids:
            run = evidence[identity]["run_identity"]
            require(run["dataset_sha256"] == dataset["sha256"] and
                    run["suite_version"] == dataset["version"],
                    f"{where}: evidence dataset identity differs")


def _migration(value, known_ids):
    row = object_value(value, "migration")
    # Lock the declared ancestry to the installed v2 contract. Equality here
    # does not read Git, authenticate old bytes, or verify any evidence record.
    for key, expected in MIGRATION_SOURCE.items():
        require(row.get(key) == expected, f"migration.{key}: differs from the installed source identity")
    changes = indexed(row.get("changes"), "migration.changes")
    require(bool(changes), "migration: no recorded changes")
    for identity, change in changes.items():
        require(set(change) == {"id", "affected_ids", "reason"},
                f"migration {identity}: exact change fields required")
        nonempty_string(change["reason"], f"migration {identity}.reason")
        affected = strings(change["affected_ids"], f"migration {identity}.affected_ids")
        require(bool(affected) and set(affected) <= known_ids,
                f"migration {identity}: empty or unknown affected ids")


def validate_registry(registry):
    """Validate metadata consistency, separating measurement from readiness.

    Evidence records remain supplied descriptions. No file hash, executable,
    theorem, linguistic interpretation, or result is authenticated here.
    """
    object_value(registry, "registry")
    require(registry.get("schema") == SCHEMA, "unsupported registry schema")
    require(registry.get("schema_version") == "0.2.0", "unsupported framework version")
    validate_base_contracts(registry)
    organization_state = "NOT_DECLARED"
    if "organization" in registry["rule_contract"]:
        # Ordinary validation checks shape only. Resolving owners is the
        # explicitly requested organization view, not an implicit catalogue load.
        from .organization import validate_organization_structure
        validate_organization_structure(registry["rule_contract"]["organization"])
        organization_state = "DECLARED_REFERENCES_NOT_RESOLVED"
    require("gate_states" not in registry, "v1 gate_states is not a v2 field")
    nonempty_string(registry.get("framework_id"), "framework_id")
    baseline = object_value(registry.get("baseline"), "baseline")
    sha(baseline.get("nabt_commit"), "baseline.nabt_commit")
    for key in ("mashru_commit", "mashru_vendor_nabt_commit"):
        if key in baseline:
            sha(baseline[key], f"baseline.{key}")
    require(set(strings(registry.get("work_states"), "work_states")) == WORK_STATES,
            "work_states differs from the installed registry schema")
    require(set(strings(registry.get("measurement_states"), "measurement_states")) == MEASUREMENT_STATES,
            "measurement_states differs from the installed registry schema")
    roles = indexed(registry.get("roles"), "roles")
    layers = indexed(registry.get("layers"), "layers")
    gates = indexed(registry.get("gates"), "gates")
    tasks = indexed(registry.get("tasks"), "tasks")
    evidence = indexed(registry.get("evidence_records"), "evidence_records")
    capabilities = indexed(registry.get("capabilities", []), "capabilities")
    require(bool(roles) and bool(layers) and bool(gates), "roles, layers and gates must be nonempty")
    gate_order = dependency_order(gates, "gates")
    task_order = dependency_order(tasks, "tasks")
    parents = {}
    children = {identity: [] for identity in tasks}
    for identity, row in tasks.items():
        require("parent_task_id" in row, f"task {identity}: parent_task_id is required")
        parent = row["parent_task_id"]
        require(parent is None or (type(parent) is str and parent in tasks),
                f"task {identity}: unknown parent")
        parents[identity] = {"depends_on": [] if parent is None else [parent]}
        if parent is not None:
            children[parent].append(identity)
    dependency_order(parents, "task parents")
    _migration(registry.get("migration"), set(roles) | set(layers) | set(gates) |
               set(tasks) | set(capabilities) | {"registry"})
    for identity, row in evidence.items():
        _no_authority_fields(row, f"evidence {identity}")
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
        _no_authority_fields(row, f"gate {identity}")
        require(not ({"status", "evidence_ids", "baseline"} & row.keys()),
                f"gate {identity}: legacy gate status/evidence/baseline fields")
        nonempty_string(row.get("title"), f"gate {identity}.title")
        nonempty_string(row.get("scope"), f"gate {identity}.scope")
        requirements = strings(row.get("requirements"), f"gate {identity}.requirements")
        require(bool(requirements), f"gate {identity}: no acceptance requirements")
        _dataset(row.get("dataset"), f"gate {identity}.dataset")
        _measurement(row, evidence)
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
            gate = gates[row["gate_id"]]
            dataset = gate["dataset"]
            run = evidence[item]["run_identity"]
            require(gate["measurement"]["state"] in {"MEASURED", "STALE"} and
                    item in gate["measurement"]["evidence_ids"],
                    f"capability {identity}: run is not part of its gate measurement")
            if gate["measurement"]["state"] == "MEASURED":
                require(dataset["status"] == "frozen" and
                        run["dataset_sha256"] == dataset["sha256"] and
                        run["suite_version"] == dataset["version"],
                        f"capability {identity}: evidence dataset identity differs")
        if row["state"] == "EVALUATED":
            require(bool(ids), f"capability {identity}: evaluated state needs reported run")
        else:
            require(not ids, f"capability {identity}: unevaluated state has run evidence")
    for identity, row in tasks.items():
        require(not ({"gate_status", "scoped_evidence_ids"} & row.keys()),
                f"task {identity}: legacy task gate/evidence fields")
        nonempty_string(row.get("title"), f"task {identity}.title")
        nonempty_string(row.get("deliverable"), f"task {identity}.deliverable")
        nonempty_string(row.get("scope"), f"task {identity}.scope")
        require(type(row.get("owner_role")) is str and row["owner_role"] in roles,
                f"task {identity}: unknown owner")
        require(type(row.get("reviewer_role")) is str and row["reviewer_role"] in roles,
                f"task {identity}: unknown reviewer")
        require(row["owner_role"] != row["reviewer_role"], f"task {identity}: reviewer equals owner")
        enum_value(row.get("work_status"), WORK_STATES, f"task {identity}.work_status")
        ids = strings(row.get("evidence_ids"), f"task {identity}.evidence_ids")
        require(set(ids) <= evidence.keys(), f"task {identity}: dangling evidence reference")
        links = strings(row.get("gates"), f"task {identity}.gates")
        require(set(links) <= gates.keys(), f"task {identity}: unknown gate")
        require(all(evidence[item]["gate_id"] in links for item in ids),
                f"task {identity}: evidence belongs to an unlinked gate")
        strings(row.get("blockers"), f"task {identity}.blockers")
        if "delivery_references" in row:
            strings(row["delivery_references"], f"task {identity}.delivery_references")
        if row["work_status"] in {"READY", "DELIVERED"}:
            require(all(tasks[dep].get("work_status") == "DELIVERED" for dep in row["depends_on"]),
                    f"task {identity}: {row['work_status']} before prerequisites delivered")
        if row["work_status"] == "DELIVERED":
            require(all(tasks[child].get("work_status") == "DELIVERED" for child in children[identity]),
                    f"task {identity}: DELIVERED before children delivered")
    release = object_value(registry.get("release_policy"), "release_policy")
    require(type(release.get("required_skips_allowed")) is int and
            release["required_skips_allowed"] == 0, "required skips must be zero")
    for key in ("empty_required_suite_allowed", "stale_required_evidence_allowed",
                "optional_omissions_count_as_success", "nabt_depends_on_mashru_release"):
        require(release.get(key) is False, f"release_policy.{key} must be false")
    return {"schema": "nabt.entropy-framework.validation.v2", "valid": True,
            "authority": "METADATA_CONSISTENCY_ONLY", "semantic_authority": "NONE",
            "evidence_verified": False, "gate_execution": "NOT_PERFORMED",
            "release_admission": "NOT_EVALUATED",
            "organization_state": organization_state,
            "roles": len(roles), "layers": len(layers), "gates": len(gates),
            "tasks": len(tasks), "capabilities": len(capabilities),
            "gate_order": gate_order, "task_order": task_order}


def report_registry(registry):
    validation = validate_registry(registry)
    gates = {row["id"]: row for row in registry["gates"]}
    tasks = {row["id"]: row for row in registry["tasks"]}
    children = {identity: [] for identity in tasks}
    for identity, task in tasks.items():
        if task["parent_task_id"] is not None:
            children[task["parent_task_id"]].append(identity)
    admissions = {}
    for identity in validation["gate_order"]:
        gate = gates[identity]
        measurement = gate["measurement"]
        blockers = [dep for dep in gate["depends_on"]
                    if admissions[dep]["readiness"] != "READY_FOR_REVIEW"]
        if measurement["state"] != "MEASURED" or measurement["reported_outcome"] != "PASS":
            readiness = "BLOCKED_MEASUREMENT"
        elif blockers:
            readiness = "BLOCKED_DEPENDENCIES"
        else:
            readiness = "READY_FOR_REVIEW"
        admissions[identity] = {"readiness": readiness, "blockers": blockers,
                                "decision": "NOT_EVALUATED", "evidence_verified": False}
    return {
        "schema": "nabt.entropy-framework.report.v2",
        "authority": "DECLARED_RECORDS_ONLY", "semantic_authority": "NONE",
        "release_admission": "NOT_EVALUATED", "evidence_verified": False,
        "validation": validation, "baseline": registry["baseline"],
        "base_contracts": validate_base_contracts(registry),
        "organization_state": validation["organization_state"],
        "migration": registry["migration"],
        "scoped_capabilities": [{"id": row["id"], "state": row["state"],
                                 "gate_id": row["gate_id"], "scope": row["scope"],
                                 "evidence_ids": row["evidence_ids"],
                                 "evidence_verified": False,
                                 "measurement": gates[row["gate_id"]]["measurement"],
                                 "admission": admissions[row["gate_id"]]}
                                for row in registry.get("capabilities", [])],
        "gates": [{"id": identity, "title": gates[identity]["title"],
                   "scope": gates[identity]["scope"],
                   "measurement": gates[identity]["measurement"],
                   "admission": admissions[identity],
                   "verification_status": "NOT_PERFORMED",
                   "dataset": gates[identity]["dataset"]}
                  for identity in validation["gate_order"]],
        "tasks": [{"id": identity, "title": tasks[identity]["title"],
                   "work_status": tasks[identity]["work_status"],
                   "scope": tasks[identity]["scope"],
                   "parent_task_id": tasks[identity]["parent_task_id"],
                   "children": children[identity],
                   "gates": tasks[identity]["gates"],
                   "owner_role": tasks[identity]["owner_role"],
                   "reviewer_role": tasks[identity]["reviewer_role"],
                   "undelivered_prerequisites": [dep for dep in tasks[identity]["depends_on"]
                                                 if tasks[dep]["work_status"] != "DELIVERED"]}
                  for identity in validation["task_order"]],
    }
