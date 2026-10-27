"""Native, bounded authority for the installed 24 classical rule families.

This additional entry does not change the legacy evaluator. It executes the
repository-owned Lean export and binds one exact finite control/result row to
the recomputed parent receipt. Control abstraction and free-text acquisition
remain Python obligations. No source interpretation, output spelling, or
whole-Arabic claim is obtained merely by exporting the control relation.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import subprocess

from nabt import foundation
from . import classical_laws

SCHEMA = "nabt.classical-certified-control.v1"
_ROOT = Path(__file__).resolve().parents[2]
_MAX_EXPORT_BYTES = 8 * 1024 * 1024
_EXPORTS = {
    "classical_weak": "exportClassicalWeak",
    "classical_hamza": "exportClassicalHamza",
    "classical_gemination": "exportClassicalGemination",
    "classical_boundary_affixes": "exportClassicalBoundaryAffixes",
}


def _wire(value):
    return classical_laws._canonical(value)


def _digest(value):
    return sha256(_wire(value)).hexdigest()


def _json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_NATIVE_EXPORT_FIELD")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_NATIVE_EXPORT")))


def _native_export(module_name):
    executable = _ROOT / "formal/.lake/build/bin" / _EXPORTS[module_name]
    binary_digest = sha256(executable.read_bytes()).hexdigest()
    completed = subprocess.run([str(executable)], input=b"", capture_output=True,
                               timeout=60, check=False)
    if completed.returncode:
        raise ValueError("NATIVE_EXPORT_FAILED")
    if len(completed.stdout) > _MAX_EXPORT_BYTES:
        raise OverflowError("NATIVE_EXPORT_RESOURCE_LIMIT")
    if sha256(executable.read_bytes()).hexdigest() != binary_digest:
        raise ValueError("NATIVE_EXPORT_CHANGED_DURING_EXECUTION")
    return _json(completed.stdout.decode("utf-8", "strict")), binary_digest


def _expected_export(name, module):
    expected = module.finite_export_rows()
    if type(expected) is list:
        expected = {"law_id": module.LAW_ID, "rows": expected}
        if name == "classical_boundary_affixes":
            expected["alphabet"] = module.ALPHABET_ID
    return expected


def _select(name, module, parent, exported):
    rule, frame, result = parent["rule_id"], parent["input_frame"], parent["result"]
    if name == "classical_weak":
        key = {"frame": result["control"]}
        proposed = {**key, "actions": [item["action"] for item in result["alternatives"]]}
        group, theorem = "rows", "Nabt.ClassicalWeak.enumeration_exact"
    elif name == "classical_gemination":
        if rule == "ASSIM-NUN-B-BLOCKED-TEXT":
            key = {"left": frame["left"][0], "vowel": frame["left"][1],
                   "right": frame["right"][0], "connection": frame["connection"]}
            group, theorem = "assimilation", "Nabt.ClassicalGemination.nun_exact"
        else:
            normalized = module._frame(frame, False)
            if module._shape_reason(normalized) is not None:
                return None
            key = {"rule_id": rule, "context": frame["context"], "dialect": frame["dialect"],
                   "preceding": module._preceding(normalized), "last": frame["second"][1]}
            group, theorem = "morphology", "Nabt.ClassicalGemination.enumeration_exact"
        proposed = {**key, "actions": [item["operation"] for item in result["alternatives"]]}
    elif name == "classical_hamza":
        key = {"rule_id": rule, "frame": frame}
        proposed = {**key, "input": result["input_morphophonemes"],
                    "operations": [item["operation"] for item in result["alternatives"]],
                    "outputs": [item["morphophonemes"] for item in result["alternatives"]]}
        group, theorem = "rows", "Nabt.ClassicalHamza.enumeration_exact"
    else:
        key = {"rule_id": rule, "frame": frame}
        proposed = {**key, "alternatives": result["alternatives"]}
        group = "rows"
        theorem = "Nabt.ClassicalBoundaryAffixes." + {
            "CMD-WEAK-DELETE": "weak_exact", "AFFIX-LIGHT-NUN-PAUSE": "light_exact",
            "MUGHNI-ANA-BOUNDARY": "ana_exact"}[rule]
    rows = [row for row in exported[group]
            if _wire({field: row.get(field) for field in key}) == _wire(key)]
    if not rows:
        return None
    if len(rows) != 1 or _wire(rows[0]) != _wire(proposed):
        raise ValueError("NATIVE_SELECTED_CONTROL_MISMATCH")
    return {"group": group, "control": key, "row": rows[0], "theorem": theorem}


def _frame_projection(name, frame):
    """Project only explicitly supplied vowels; never invent missing harakat."""
    if name == "classical_weak":
        cells = frame["cells"]
    elif name == "classical_gemination":
        cells = ([frame["left"], frame["right"]] if "left" in frame else
                 frame["prefix"] + [frame["first"], frame["second"]] + frame["suffix"])
    else:
        return {"status": "BRIDGE_REQUIRED", "reason": "NON_A116_SYMBOLIC_ALPHABET",
                "native_projection_checked": False, "observed_text": False}
    marks = {"a": "َ", "i": "ِ", "u": "ُ", "0": "ْ", "s": "ْ"}
    text = "".join(letter + marks[vowel] for letter, vowel in cells)
    receipt = foundation.inspect_source(text, source_id="supplied_classical_frame",
                                        revision=_digest(frame))
    return {"status": receipt["status"], "receipt": receipt,
            "authority": "SERIALIZED_SUPPLIED_FRAME_NOT_OBSERVED_TEXT",
            "native_projection_checked": False, "observed_text": False}


def evaluate_certified(rule_id, frame):
    """Bind a conditional finite Lean row to one source-replayed supplied frame.

    The caller cannot select a checker, ledger, receipt, proof flag or evidence
    rank. Frames outside an export's exact domain remain diagnostic. A checked
    empty action set is a bounded equation, not rejection of an Arabic word.
    """
    foundation.require_foundation("nabt.classical_certified.evaluate_certified")
    parent = classical_laws.evaluate(rule_id, frame)
    # Whitelisted installed modules only; evaluation already validates the ID.
    module_name = next(name for name in _EXPORTS
                       if rule_id in import_module("nabt." + name).RULE_IDS)
    module = import_module("nabt." + module_name)
    binding = {"rule_id": rule_id, "frame_sha256": parent["input_sha256"],
               "parent_receipt_sha256": _digest(parent),
               "source_inventory_sha256": parent["inventory_sha256"],
               "source_passages_sha256": _digest(parent["result"]["source_spans"])}
    result = {"schema": SCHEMA, "status": "DEFER", "authority": "DIAGNOSTIC_ONLY",
              "binding": binding, "parent_receipt": parent, "claims": [],
              "native_checked": False, "bounded_rule_checked": False,
              "strict_language_accepted": False, "grants_language_license": False,
              "source_to_control_proved": False, "whole_arabic_complete": False,
              "a116_frame_projection": _frame_projection(module_name, parent["input_frame"]),
              "residuals": ["SUPPLIED_FRAME_NOT_ACQUIRED_FROM_TEXT",
                            "SOURCE_INTERPRETATION_IS_A_DECLARED_PREMISE",
                            "CONTROL_ABSTRACTION_NOT_KERNEL_PROVED",
                            "NO_END_TO_END_A116_LANGUAGE_LICENSE"]}
    try:
        exported, binary_digest = _native_export(module_name)
        if _wire(exported) != _wire(_expected_export(module_name, module)):
            raise ValueError("NATIVE_EXPORT_CONFORMANCE_MISMATCH")
        selected = _select(module_name, module, parent, exported)
        result.update(native_checked=True, native_export_sha256=_digest(exported),
                      native_binary_sha256=binary_digest)
        if selected is None:
            result["residuals"].append("FRAME_OUTSIDE_EXACT_NATIVE_EXPORT_DOMAIN")
            return result
        claim_binding = {**binding, "native_export_sha256": _digest(exported),
                         "native_row_sha256": _digest(selected["row"])}
        result["claims"] = [{"kind": "CLASSICAL_FINITE_CONTROL_EQUATION",
            "binding": claim_binding, "control": deepcopy(selected["control"]),
            "equation_result": deepcopy(selected["row"]),
            "scope": "Exact native finite row conditional on the supplied frame/control. No free-text acquisition, general Python refinement, surface spelling, source authenticity or whole-language acceptance.",
            "unresolved_premises": list(result["residuals"]),
            "proof": {"kind": "NATIVE_LEAN_EXPORT_ROW", "law_id": module.LAW_ID,
                      "theorems": [selected["theorem"]], "export": _EXPORTS[module_name],
                      "group": selected["group"]}}]
        result.update(status="CHECKED_CONDITIONAL_CONTROL", bounded_rule_checked=True,
                      authority="NATIVE_FINITE_CONTROL_ONLY")
    except (OverflowError, subprocess.TimeoutExpired):
        result.update(status="RESOURCE_EXHAUSTED", reason="NATIVE_EXPORT_RESOURCE_LIMIT")
        result["residuals"].append(result["reason"])
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, RecursionError):
        result.update(status="VERIFICATION_UNAVAILABLE", reason="NATIVE_EXPORT_UNAVAILABLE_OR_MISMATCH")
        result["residuals"].append(result["reason"])
    return result
