"""Reference-only organization of existing rules, contracts and capabilities.

Owner loaders retain their authority boundaries. This view does not create rule
bodies, adopt candidates, infer scope containment, dispatch programs, or observe
formation/application/revision events. Ordinary reuse does not import this view.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from tools import proof_catalog
from .registry import (
    OPERATION_KINDS, FrameworkError, FrameworkResourceError, dependency_order,
    enum_value, list_value, load_json, nonempty_string, object_value, require,
    strings, validate_base_contracts, validate_registry,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "nabt.rule-organization.references.v1"
REPORT_SCHEMA = "nabt.rule-organization.report.v1"
SUMMARY_SCHEMA = "nabt.rule-organization.summary.v1"
AUTHORITY = "ORGANIZATIONAL_REFERENCE_MAP_ONLY"
ROLES = (
    "DEFINITION_OR_TYPE", "FORMATION_METHOD", "LANGUAGE_INTERPRETATION_RULE",
    "INFERENCE_LICENSE", "EVIDENCE_ADMISSION_POLICY", "NORMATIVE_ACTION_POLICY",
    "EVALUATION_GATE",
)
PHASES = ("formation", "adoption", "application", "revision")
REFERENCE_KINDS = {
    "catalogue_rule", "reuse_family", "compiled_declaration",
    "framework_contract", "evaluation_gate",
}
FRAMEWORK_CONTRACTS = {"rule_contract", "evidence_freshness", "release_policy"}
RELATION_KINDS = {"JUSTIFICATION", "PREREQUISITE", "REFERENCE", "CONFLICT", "INFERENCE"}
PREREQUISITE_KINDS = {"JUSTIFICATION", "PREREQUISITE"}
PROFILE_FIELDS = {
    "id", "role", "operation_kind", "subject", "family_ids", "scope",
    "phase_contract_refs",
}
MAX_PROFILES = 64
MAX_RELATIONS = 256
MAX_REFERENCES_PER_PHASE = 32
MAX_FAMILIES_PER_PROFILE = 64
MAX_ID_BYTES = 512
MAX_SCOPE_BYTES = 8192
MAX_ORGANIZATION_BYTES = 1024 * 1024
MAX_REPORT_BYTES = 8 * 1024 * 1024


def _fields(value, expected, where):
    object_value(value, where)
    require(set(value) == set(expected), where + ": exact fields required")


def _text(value, where, maximum=MAX_ID_BYTES):
    nonempty_string(value, where)
    if len(value.encode("utf-8")) > maximum:
        raise FrameworkResourceError(where + ": text byte budget exceeded")
    return value


def _array(value, where, maximum):
    list_value(value, where)
    if len(value) > maximum:
        raise FrameworkResourceError(where + ": item budget exceeded")
    return value


def _encoded_limit(value, maximum, where):
    try:
        size = len(proof_catalog.canonical_json(value).encode("utf-8"))
    except (TypeError, ValueError, UnicodeError) as error:
        raise FrameworkError(where + ": noncanonical JSON value") from error
    except RecursionError as error:
        raise FrameworkResourceError(where + ": JSON nesting budget exceeded") from error
    if size > maximum:
        raise FrameworkResourceError(where + ": JSON byte budget exceeded")


def _reference(value, where):
    _fields(value, {"kind", "id"}, where + " reference")
    enum_value(value["kind"], REFERENCE_KINDS, where + " reference.kind")
    _text(value["id"], where + " reference.id")
    return value["kind"], value["id"]


def validate_organization_structure(value):
    """Check bounded structure and prerequisite cycles without loading owners.

    A well-shaped external identity may remain unresolved. The explicit report
    resolver performs owner lookup; shape validation never claims that lookup.
    """
    where = "rule_contract.organization"
    _fields(value, {"schema", "profiles", "relations"}, where)
    enum_value(value["schema"], (SCHEMA,), where + ".schema")
    profiles = _array(value["profiles"], where + ".profiles", MAX_PROFILES)
    indexed = {}
    for profile in profiles:
        label = where + ".profile"
        _fields(profile, PROFILE_FIELDS, label)
        identity = _text(profile["id"], label + ".id")
        require(identity not in indexed, label + ": duplicate profile id")
        indexed[identity] = profile
        enum_value(profile["role"], ROLES, label + ".role")
        operation = profile["operation_kind"]
        if operation is not None:
            enum_value(operation, OPERATION_KINDS, label + ".operation_kind")
        _reference(profile["subject"], label + ".subject")
        _text(profile["scope"], label + ".scope", MAX_SCOPE_BYTES)
        family_ids = _array(profile["family_ids"], label + ".family_ids", MAX_FAMILIES_PER_PROFILE)
        for family in family_ids:
            _text(family, label + ".family_ids")
        strings(family_ids, label + ".family_ids")
        phases = profile["phase_contract_refs"]
        _fields(phases, PHASES, label + ".phase_contract_refs")
        for phase in PHASES:
            phase_label = label + ".phase_contract_refs." + phase
            references = _array(phases[phase], phase_label, MAX_REFERENCES_PER_PHASE)
            seen = set()
            for reference in references:
                key = _reference(reference, phase_label)
                require(key not in seen, phase_label + ": duplicate reference")
                seen.add(key)
    relations = _array(value["relations"], where + ".relations", MAX_RELATIONS)
    dependencies = {identity: {"depends_on": []} for identity in indexed}
    seen = set()
    for relation in relations:
        label = where + ".relation"
        _fields(relation, {"from", "to", "kind", "phase"}, label)
        for endpoint in ("from", "to"):
            _text(relation[endpoint], label + "." + endpoint)
            require(relation[endpoint] in indexed, label + ": dangling profile reference")
        enum_value(relation["kind"], RELATION_KINDS, label + ".kind")
        enum_value(relation["phase"], PHASES, label + ".phase")
        key = tuple(relation[field] for field in ("from", "to", "kind", "phase"))
        require(key not in seen, label + ": duplicate relation")
        seen.add(key)
        if relation["kind"] in PREREQUISITE_KINDS:
            # Distinct typed/phase relations can share the same graph edge.
            parents = dependencies[relation["from"]]["depends_on"]
            if relation["to"] not in parents:
                parents.append(relation["to"])
    try:
        order = dependency_order(dependencies, where + ".prerequisites")
    except FrameworkError as error:
        raise FrameworkError(where + ": prerequisite cycle: " + str(error)) from error
    _encoded_limit(value, MAX_ORGANIZATION_BYTES, where)
    return {"prerequisite_order": order}


def _boundaries():
    return {"authority": AUTHORITY, "semantic_authority": "NONE",
            "action_authority": "NONE", "runtime_execution_performed": False,
            "scope_relation_established": False}


def build_organization_report(root=ROOT, *, registry=None):
    """Resolve the complete owner population before presenting authored labels.

    Supplied registry metadata remains descriptive. Existing source loaders and
    the recorded compiled catalogue define the referenced owner identities.
    """
    from .reuse import REGISTRY, _file, build_reuse_report
    from tools.grammar_catalog import catalog as grammar_catalog

    root = Path(root).resolve()
    supplied = registry is not None
    registry_sha = None
    if registry is None:
        registry, registry_sha = load_json(_file(root, REGISTRY), with_sha256=True)
    validate_registry(registry)
    try:
        registry = deepcopy(registry)
    except RecursionError as error:
        raise FrameworkResourceError("rule_contract.organization: snapshot nesting budget exceeded") from error
    contracts = validate_base_contracts(registry)
    organization = registry["rule_contract"].get("organization")
    structure = (validate_organization_structure(organization) if organization is not None
                 else {"prerequisite_order": []})
    # This path never uses reuse_run or a native checker. The ordinary reuse
    # report still validates the current recorded compiled source identities.
    reuse = build_reuse_report(root, registry=registry)
    try:
        catalogue = grammar_catalog.build_catalog(root)
    except grammar_catalog.CatalogError as error:
        raise FrameworkError("rule organization catalogue owner: " + str(error)) from error
    catalogue_sha = grammar_catalog.catalog_sha256(catalogue)
    families = {row["id"]: row for row in reuse["families"]}
    family_owners = {row["id"]: row for row in registry["reuse"]["families"]}
    rules = {row["rule_key"]: row for row in catalogue["rules"]}
    passages = {row["passage_id"]: row for row in catalogue["passages"]}
    declarations = {row["name"]: (module, row) for module in reuse["modules"]
                    for row in module["declarations"]}
    gates = {row["id"]: row for row in registry["gates"]}
    framework = {**contracts, "release_policy": registry["release_policy"]}
    profiles = organization["profiles"] if organization is not None else []
    relations = organization["relations"] if organization is not None else []

    def resolve(reference):
        kind, identity = _reference(reference, "rule organization owner")
        owner_scope = None
        if kind == "catalogue_rule":
            require(identity in rules, "rule organization reference: unknown catalogue rule " + identity)
            row = rules[identity]
            owner_scope = row["scope"]
            owner = {"catalogue_schema": catalogue["schema"], "catalogue_sha256": catalogue_sha,
                     "registry_id": row["registry_id"], "local_id": row["local_id"],
                     "record_sha256": proof_catalog.digest(row),
                     "source_passage_ids": list(row["source_passage_ids"]),
                     "source_references": [
                         {key: passages[pid][key] for key in
                          ("passage_id", "source_key", "source_id", "start", "end", "sha256")}
                         for pid in row["source_passage_ids"]],
                     "source_status": row["source_status"],
                     "runtime_rule_id": row["runtime_rule_id"],
                     "theorem_names": list(row["theorem_names"])}
        elif kind == "reuse_family":
            require(identity in family_owners, "rule organization reference: unknown reuse family " + identity)
            row = family_owners[identity]
            owner_scope = row["scope"]
            owner = {"registry_path": REGISTRY, "schema": registry["reuse"]["schema"],
                     "record_sha256": proof_catalog.digest(row),
                     "formal_modules": list(row["formal_modules"]),
                     "metadata_origin": "SUPPLIED_REGISTRY_METADATA" if supplied else "INSTALLED_REGISTRY_METADATA"}
        elif kind == "compiled_declaration":
            require(identity in declarations, "rule organization reference: unknown compiled declaration " + identity)
            module, row = declarations[identity]
            owner = {"catalogue_path": reuse["catalogue"]["path"],
                     "catalogue_sha256": reuse["catalogue"]["sha256"],
                     "canonical_name": row["canonical_name"],
                     "statement_sha256": row["statement_sha256"],
                     "source_path": module["source_path"], "source_sha256": module["source_sha256"],
                     "source_statement": deepcopy(row["source_statement"]),
                     "axioms": deepcopy(row["axioms"]),
                     "verification": reuse["catalogue"]["verification"], "compiled_this_run": False}
        elif kind == "framework_contract":
            require(identity in FRAMEWORK_CONTRACTS,
                    "rule organization reference: unknown framework contract " + identity)
            owner = {"registry_path": REGISTRY, "schema": registry["schema"],
                     "schema_version": registry["schema_version"], "field": identity,
                     "record_sha256": proof_catalog.digest(framework[identity]),
                     "metadata_origin": "SUPPLIED_REGISTRY_METADATA" if supplied else "INSTALLED_REGISTRY_METADATA"}
        else:
            require(identity in gates, "rule organization reference: unknown evaluation gate " + identity)
            row = gates[identity]
            owner_scope = row["scope"]
            owner = {"registry_path": REGISTRY, "schema": registry["schema"],
                     "schema_version": registry["schema_version"],
                     "record_sha256": proof_catalog.digest(row),
                     "metadata_origin": "SUPPLIED_REGISTRY_METADATA" if supplied else "INSTALLED_REGISTRY_METADATA"}
        return {"kind": kind, "id": identity, "owner_scope": owner_scope,
                "owner_identity": owner}

    resolved = []
    rule_profiles = {identity: [] for identity in rules}
    family_profiles = {identity: [] for identity in families}
    role_counts = dict.fromkeys(ROLES, 0)
    for profile in profiles:
        subject = resolve(profile["subject"])
        capability_links = []
        for identity in profile["family_ids"]:
            require(identity in families,
                    "rule organization reference: unknown capability family " + identity)
            capability_links.append(deepcopy(families[identity]))
            family_profiles[identity].append(profile["id"])
        if profile["subject"]["kind"] == "catalogue_rule":
            rule_profiles[profile["subject"]["id"]].append(profile["id"])
        elif profile["subject"]["kind"] == "reuse_family":
            ids = family_profiles[profile["subject"]["id"]]
            if profile["id"] not in ids:
                ids.append(profile["id"])
        role_counts[profile["role"]] += 1
        resolved.append({**deepcopy(profile), "subject_owner": subject,
                         "resolved_phase_contract_refs": {
                             phase: [resolve(ref) for ref in profile["phase_contract_refs"][phase]]
                             for phase in PHASES},
                         "capability_links": capability_links,
                         "lifecycle_evidence": dict.fromkeys(PHASES, "NOT_OBSERVED"),
                         "scope_relation_established": False})
    rows = [{**deepcopy(row), "owner_scope": row["scope"],
             "profile_ids": sorted(rule_profiles[row["rule_key"]]),
             "mapping_status": "MAPPED" if rule_profiles[row["rule_key"]] else "UNMAPPED",
             "scope_relation_established": False} for row in catalogue["rules"]]
    mapped = [row["rule_key"] for row in rows if row["profile_ids"]]
    unmapped = [row["rule_key"] for row in rows if not row["profile_ids"]]
    inputs = dict(reuse["inputs"])
    for row in catalogue["inputs"]:
        path, digest = row["path"], row["sha256"]
        require(path not in inputs or inputs[path] == digest,
                "rule organization owner input changed during resolution: " + path)
        inputs[path] = digest
    for path in ("tools/entropy_framework/organization.py", "tools/entropy_framework/registry.py"):
        digest = sha256(_file(root, path).read_bytes()).hexdigest()
        require(path not in inputs or inputs[path] == digest,
                "rule organization owner input changed during resolution: " + path)
        inputs[path] = digest
    if not supplied:
        _, current_sha = load_json(_file(root, REGISTRY), with_sha256=True)
        require(current_sha == registry_sha,
                "rule organization installed registry changed during resolution")
        inputs[REGISTRY] = registry_sha
    report = {
        "schema": REPORT_SCHEMA, "status": "RESOLVED" if organization is not None else "NOT_DECLARED",
        **_boundaries(), "base_contracts": contracts,
        "organization_schema": SCHEMA if organization is not None else None,
        "organization_sha256": proof_catalog.digest(organization) if organization is not None else None,
        "profiles": resolved, "relations": deepcopy(relations),
        "prerequisite_order": structure["prerequisite_order"], "role_counts": role_counts,
        "catalogue": {"schema": catalogue["schema"], "authority": catalogue["authority"],
                      "sha256": catalogue_sha, "rule_count": len(rows),
                      "mapped_rule_count": len(mapped), "unmapped_rule_count": len(unmapped),
                      "mapped_rule_keys": mapped, "unmapped_rule_keys": unmapped, "rules": rows},
        "families": [{**deepcopy(row), "owner_scope": row["scope"],
                      "profile_ids": sorted(family_profiles[row["id"]]),
                      "mapping_status": "MAPPED" if family_profiles[row["id"]] else "UNMAPPED",
                      "scope_relation_established": False} for row in reuse["families"]],
        "inputs": dict(sorted(inputs.items())),
        "limits": [
            "Classification and relations are authored navigation metadata, not evidence or executable proof edges.",
            "Owner references do not establish formation history, rule adoption, application witnesses or revision events.",
            "Profile scope and owner scope are retained independently; scope equality or containment is not established.",
            "Mapped and unmapped counts describe this organization only, not Arabic coverage or implementation availability.",
            "Source review status, quotation integrity, interpretation fidelity and installed runtime mappings remain distinct.",
            "The existing compiled catalogue is a recorded snapshot checked against sources, not a new kernel run.",
            "No generic candidate-rule adoption bridge, concept induction method or action authorization is supplied.",
            "Reference, conflict and inference cycles remain metadata; no closure or conflict resolution is performed.",
            f"Organization budgets: {MAX_PROFILES} profiles; {MAX_RELATIONS} relations; "
            f"{MAX_REFERENCES_PER_PHASE} references per phase; {MAX_FAMILIES_PER_PROFILE} families per profile; "
            f"{MAX_ID_BYTES} UTF-8 bytes per identity; {MAX_SCOPE_BYTES} UTF-8 bytes per profile scope; "
            f"{MAX_ORGANIZATION_BYTES} canonical JSON bytes per organization; "
            f"{MAX_REPORT_BYTES} canonical JSON bytes per full report.",
        ],
    }
    _encoded_limit(report, MAX_REPORT_BYTES, "rule organization report")
    return report


def summary(report):
    """Compact display only; output files retain the full resolved report."""
    return {
        "schema": SUMMARY_SCHEMA, "status": report["status"], **_boundaries(),
        "organization_schema": report["organization_schema"],
        "organization_sha256": report["organization_sha256"],
        "profile_count": len(report["profiles"]), "relation_count": len(report["relations"]),
        "role_counts": dict(report["role_counts"]),
        "catalogue": {key: deepcopy(value) for key, value in report["catalogue"].items() if key != "rules"},
        "families": {"count": len(report["families"]),
                     "mapped_count": sum(bool(row["profile_ids"]) for row in report["families"])},
        "profiles": [{key: deepcopy(row[key]) for key in ("id", "role", "operation_kind", "subject")}
                     for row in report["profiles"]],
        "limits": list(report["limits"]),
    }
