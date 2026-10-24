#!/usr/bin/env python3
"""Reproduce the valid-request/report-budget round-trip defect without large fixtures."""

from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", type=Path, default=ROOT / "tools/classical_language_evidence.py")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    tool_path = args.tool.resolve()
    tool_before = tool_path.read_bytes()
    spec = importlib.util.spec_from_file_location("classical_report_budget_probe", tool_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    request = {
        "version": "nabt.classical-language-evidence.v1", "record_id": "qatr_inna_conditions",
        "claim_kind": "GRAMMAR_APPLICATION",
        "candidate": {
            "law_id": "qatr-inna-v1", "inputs": {"operator": "inna", "form": "full", "ma": "absent"},
            "expected": {f"padding{i}": "x" * 65500 for i in range(7)},
            "target_text": "جملة للفحص",
        },
    }
    request["candidate"]["expected"]["padding7"] = ""
    fill = module.MAX_JSON_BYTES - 32 - len(canonical(request))
    assert 0 < fill <= 65536
    request["candidate"]["expected"]["padding7"] = "x" * fill
    report = module.assess(request, root=ROOT)
    verification = module.verify(report, request, root=ROOT)
    assert tool_path.read_bytes() == tool_before, "Probe implementation changed during execution"
    observed = {
        "issue": "A valid bounded request produced a negative report too large for its own verifier",
        "tool_path": str(tool_path), "tool_sha256": sha256(tool_before).hexdigest(),
        "catalog_sha256": module.CATALOG_SHA256,
        "request_bytes": len(canonical(request)), "report_bytes": len(canonical(report)),
        "request_limit": module.MAX_JSON_BYTES,
        "report_limit": getattr(module, "MAX_REPORT_BYTES", module.MAX_JSON_BYTES),
        "request_sha256": sha256(canonical(request)).hexdigest(),
        "report_sha256": sha256(canonical(report)).hexdigest(),
        "claim_status": report["status"], "source_attested": report["source_attested"],
        "verification": verification,
        "expected": {"claim_status": "MISMATCH", "verification_valid": True},
        "fixed": report["status"] == "MISMATCH" and verification["valid"] is True,
        "reproducer_note": ("The expected object is deliberately incorrect, so no positive claim is "
                            "authorized. The test requires an authentic negative report to replay. "
                            "The payload is regenerated deterministically instead of storing 0.5 MiB of padding."),
    }
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(observed, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(json.dumps(observed, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
