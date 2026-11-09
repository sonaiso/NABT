"""Small external client: always run and independently verify the public gateway.

The JSON request is retained once before either subprocess. No raw owner receipt
or user-supplied success flag is accepted as an application response.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=ROOT / "examples/io_gateway/case_application.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/local/case-application-client")
    args = parser.parse_args()
    with args.request.open("rb") as stream:
        original = stream.read(2 * 1048576 + 1)
    if len(original) > 2 * 1048576:
        parser.error("Request exceeds the gateway byte limit")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    # The independent input and receipts share a private directory. Only after
    # successful admission are the review copies written to the chosen output.
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT))
    with tempfile.TemporaryDirectory(prefix="nabt-case-client-") as directory:
        directory = Path(directory)
        request, receipt, verification = (directory / name for name in ("request.json", "receipt.json", "verification.json"))
        request.write_bytes(original)
        base = [sys.executable, "-m", "tools.grammar_catalog", "gateway"]
        commands = [base + ["run", "--request", str(request), "--output", str(receipt)],
                    base + ["verify", "--request", str(request), "--receipt", str(receipt), "--output", str(verification)]]
        for command in commands:
            run = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
            if run.returncode:
                print(json.dumps({"status": "NOT_ADMITTED", "exit_code": run.returncode,
                                  "detail": run.stderr or run.stdout}, ensure_ascii=False))
                return 2
        admitted = json.loads(verification.read_text())
        if admitted.get("valid") is not True:
            print(json.dumps({"status": "NOT_ADMITTED", "verification": admitted}, ensure_ascii=False))
            return 2
        report = json.loads(receipt.read_text())
        if report["request"]["route"] != "application.case":
            print(json.dumps({"status": "NOT_A_CASE_APPLICATION"}))
            return 2
        owner = report["execution"]["owner_result"]
        binding = owner.get("policy_binding") or {}
        latest = owner.get("history", [])[-1:]
        ledger = owner.get("source_ledger", [])
        summary = {"gateway_verified": True, "status": owner["status"],
            "chain_complete": owner["chain_complete"], "decision": owner.get("current_decision"),
            "case": binding.get("case"),
            "policy": {"id": binding.get("policy", {}).get("id"),
                       "statement_ar": binding.get("policy", {}).get("statement_ar"),
                       "sha256": binding.get("sha256")},
            "premises": [{"label_ar": r["label_ar"], "atom": r["atom"],
                "present_in_native_closure": r["present_in_native_closure"],
                "present_in_clean_closure": r["present_in_clean_closure"],
                "opposite_in_native_closure": r["opposite_in_native_closure"],
                "witnesses": [ledger[i] for i in r["source_witnesses"]],
                "opposing_witnesses": [ledger[i] for i in r["opposing_source_witnesses"]]}
                for step in latest for r in step.get("requirements", [])],
            "history": [{"step": h["step"], "event": h["event_id"], "status": h["status"],
                         "explanation_ar": h.get("explanation_ar"), "change": h.get("change")}
                        for h in owner.get("history", [])], "limits": owner["limits"]}
        for path in (request, receipt, verification):
            (output / path.name).write_bytes(path.read_bytes())
        (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if owner["chain_complete"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
