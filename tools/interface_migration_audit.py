"""Exercise every registered direct admission against a denied foundation.

Imports are repository-owned; all required arguments are inert placeholders.
The sentinel must be raised by the first live guard, before argument handling,
model inference, source I/O, or a native process. Codec primitives and checked
snapshot operations keep their separately audited mathematical contracts.
This is an execution-boundary audit, not a Lean or linguistic coverage proof.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
from pathlib import Path
from unittest.mock import patch

from nabt import foundation
from tools import check_foundation_architecture as architecture

ROOT = Path(__file__).resolve().parents[1]


class _AdmissionDenied(BaseException):
    """Not swallowed by a domain adapter's ordinary error conversion."""


def _callable(row):
    module = row["path"].removeprefix("src/").removesuffix(".py").replace("/", ".")
    target = importlib.import_module(module)
    for name in row["entrypoint"].split("."):
        target = getattr(target, name)
    return target


def _arguments(target):
    args, kwargs = [], {}
    for parameter in inspect.signature(target).parameters.values():
        if parameter.default is not inspect.Parameter.empty:
            continue
        if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD):
            args.append(None)
        elif parameter.kind == parameter.KEYWORD_ONLY:
            kwargs[parameter.name] = None
    return args, kwargs


def audit(root=ROOT):
    registry = json.loads((root / architecture.REGISTRY).read_text(encoding="utf-8"))
    rows, errors = [], []
    for entry in registry["surfaces"]:
        item = {"surface_id": entry["id"], "guard_kind": entry["guard_kind"],
                "denied_before_body": None, "error": None}
        try:
            architecture.validate_surface(entry, root)
            if entry["guard_kind"] == "runtime_foundation":
                target = _callable(entry)
                args, kwargs = _arguments(target)
                with patch.object(foundation, "require_foundation", side_effect=_AdmissionDenied) as guard:
                    try:
                        target(*args, **kwargs)
                    except _AdmissionDenied:
                        item["denied_before_body"] = (guard.call_count == 1
                            and guard.call_args.args == (entry["id"],)
                            and guard.call_args.kwargs == {})
                    else:
                        item["denied_before_body"] = False
                if not item["denied_before_body"]:
                    raise ValueError("FOUNDATION_DENIAL_NOT_OBSERVED_AT_REGISTERED_ADMISSION")
            else:
                item["classification"] = "SEPARATELY_CHECKED_TYPED_PRIMITIVE"
        except (Exception, SystemExit) as exc:
            item["error"] = {"type": type(exc).__name__, "message": str(exc)}
            errors.append(entry["id"])
        rows.append(item)
    return {"schema": "nabt.interface-migration-admission-audit.v1",
        "ok": not errors and bool(rows), "surface_count": len(rows),
        "runtime_boundary_count": sum(r["guard_kind"] == "runtime_foundation" for r in rows),
        "denied_before_body_count": sum(r["denied_before_body"] is True for r in rows),
        "separate_primitive_count": sum(r["guard_kind"] != "runtime_foundation" for r in rows),
        "failures": errors, "surfaces": rows,
        "source_acquisition_proved": False, "all_results_kernel_proved": False,
        "whole_arabic_complete": False,
        "scope": "All registered direct Python admission guards; not source acquisition, result authority, or semantic completeness."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "surfaces"}, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
