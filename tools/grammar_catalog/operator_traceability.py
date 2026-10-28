"""Validate additive, explicitly scoped references for the 24 selected operators.

The caller must first verify the registry's code-owned byte pin. Literal Lean
headers bind authored references to source declarations; they are not compiled
types, kernel evidence, source fidelity or Python refinement proofs.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Callable

SCHEMA = "nabt.operator-traceability.v1"
AUTHORITY = "AUTHORED_EXPLICIT_OPERATOR_REFERENCES_NOT_SOURCE_FIDELITY_OR_RUNTIME_PROOF"
CLAIMS = (
    "source_translation_fidelity_established",
    "free_text_premise_acquisition_established",
    "python_lean_refinement_established",
    "whole_source_rule_complete",
    "whole_arabic_complete",
)


class TraceabilityError(ValueError):
    """An installed operator reference is incomplete, stale or overclaimed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TraceabilityError(message)


def validate_registry(registry: dict, crosswalk: dict, crosswalk_path: str,
                      theorem_names: set[str], read_file: Callable[[str], bytes]
                      ) -> tuple[dict[str, dict], list[dict]]:
    """Check a previously pinned registry; arbitrary inputs grant no authority."""
    _require(registry.get("schema") == SCHEMA and registry.get("authority") == AUTHORITY,
             "invalid operator traceability schema or authority")
    claims = registry.get("claims")
    _require(type(claims) is dict and set(claims) == set(CLAIMS) and
             all(claims[key] is False for key in CLAIMS), "overclaimed operator traceability")
    base = registry.get("base_crosswalk", {})
    _require(base.get("path") == crosswalk_path and
             base.get("sha256") == sha256(read_file(crosswalk_path)).hexdigest(),
             "operator traceability historical crosswalk differs")
    expected = {row["rule_id"]: row for row in crosswalk["rows"]
                if row["status"] == "new_scoped_conditional_operator"}
    rows = registry.get("rows")
    _require(type(rows) is list and len(rows) == len(expected) == 24,
             "operator traceability must cover exactly 24 designated operators")
    indexed, inputs = {}, {}
    for row in rows:
        _require(type(row) is dict, "invalid operator traceability row")
        rid = row.get("rule_id")
        _require(type(rid) is str and rid in expected and rid not in indexed,
                 "missing, extra or duplicate operator traceability identity")
        previous = expected[rid]
        path = row.get("implementation_path")
        _require(path == previous["implementation_path"], "operator implementation path differs")
        implementation = read_file(path)
        _require(bool(implementation), "empty operator implementation reference")
        inputs[path] = {"path": path, "sha256": sha256(implementation).hexdigest(),
                        "bytes": len(implementation),
                        "identity_policy": "observed_implementation_reference_not_refinement_evidence"}
        for field in ("implemented_scope", "formal_specialization"):
            _require(type(row.get(field)) is str and bool(row[field].strip()),
                     "missing operator " + field)
        if previous.get("implemented_scope") is not None:
            _require(row["implemented_scope"] == previous["implemented_scope"],
                     "additive registry changed an existing implemented scope")
        references = row.get("formal_references")
        _require(type(references) is list and len(references) == 1,
                 "operator requires one explicit conditional theorem reference")
        reference = references[0]
        _require(type(reference) is dict, "invalid operator theorem reference")
        name = reference.get("declaration")
        _require(type(name) is str and name in theorem_names,
                 "operator theorem absent from installed declaration manifest")
        if "formal_exactness_theorem" in previous:
            _require(name == previous["formal_exactness_theorem"],
                     "additive registry changed an existing explicit theorem")
        path = reference.get("source_path")
        _require(path == "formal/" + name.rsplit(".", 1)[0].replace(".", "/") + ".lean",
                 "operator theorem source path differs from declaration module")
        source = read_file(path)
        _require(reference.get("source_sha256") == sha256(source).hexdigest(),
                 "operator theorem source changed")
        start, end = reference.get("statement_start_byte"), reference.get("statement_end_byte")
        _require(type(start) is int and type(end) is int and 0 <= start < end <= len(source),
                 "invalid operator theorem statement offsets")
        statement = source[start:end]
        _require(statement.decode("utf-8") == reference.get("statement_source_text") and
                 sha256(statement).hexdigest() == reference.get("statement_source_sha256"),
                 "operator theorem statement differs from current Lean source")
        _require(statement.startswith(("theorem " + name.rsplit(".", 1)[1] + " ").encode()) and
                 b":=" not in statement and source[end:].lstrip().startswith(b":="),
                 "operator reference does not identify a complete declaration header")
        for field, actual in (("statement_start_line", source[:start].count(b"\n") + 1),
                              ("statement_end_line", source[:end - 1].count(b"\n") + 1)):
            _require(type(reference.get(field)) is int and reference[field] == actual,
                     "operator theorem statement line differs")
        _require(type(reference.get("proof_scope")) is str and bool(reference["proof_scope"].strip()),
                 "missing conditional theorem scope")
        inputs[path] = {"path": path, "sha256": sha256(source).hexdigest(), "bytes": len(source),
                        "identity_policy": "code_pinned_declaration_source_not_kernel_evidence"}
        indexed[rid] = row
    _require(set(indexed) == set(expected), "operator traceability coverage differs")
    return indexed, sorted(inputs.values(), key=lambda row: row["path"])
