"""Read-only owner probe for PR64's late runtime-input digest replacement.

Only a temporary copy of organization.py is mutated. The actual installed
organization, reuse and catalogue owners run, with their file-identity read
redirected for that one path. The output is an observation, not an oracle.
Run from the repository root with PYTHONPATH=src:. and an exclusive output path.
"""
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

from tools.entropy_framework import organization, reuse, reuse_run
from tools.entropy_framework.registry import FrameworkError
from tools.grammar_catalog import catalog as source_catalogue


ROOT = Path(__file__).resolve().parents[4]
TARGET = "tools/entropy_framework/organization.py"
IDENTITY_PATHS = (
    TARGET,
    "tools/entropy_framework/reuse.py",
    "tools/entropy_framework/registry.py",
    "tools/entropy_framework/registry.json",
    "tools/entropy_framework/__main__.py",
    "tools/grammar_catalog/catalog.py",
    "tools/proof_catalog.py",
    "tests/test_proof_reuse_organization.py",
    "docs/RULE_POLICY_ORGANIZATION_V1_SPEC.md",
    "evidence/rule_policy_organization_v1/acceptance_cases.json",
)
MUTATION = b"\n# Isolated input-identity review mutation.\n"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identity_snapshot():
    return {relative: digest((ROOT / relative).read_bytes())
            for relative in IDENTITY_PATHS}


def observe(mutate):
    original = (ROOT / TARGET).read_bytes()
    observed = {"mutates_temporary_copy": mutate,
                "initial_target_sha256": digest(original)}
    actual_file = reuse._file
    actual_reuse = reuse.build_reuse_report
    actual_catalogue = source_catalogue.build_catalog
    with tempfile.TemporaryDirectory(prefix="nabt-input-identity-") as temporary:
        redirected = Path(temporary) / "organization.py"
        redirected.write_bytes(original)

        def file_owner(root, relative):
            return redirected if relative == TARGET else actual_file(root, relative)

        def reuse_owner(*args, **kwargs):
            result = actual_reuse(*args, **kwargs)
            observed["reuse_projection_target_sha256"] = result["inputs"].get(TARGET)
            observed["reuse_input_count"] = len(result["inputs"])
            return result

        def catalogue_owner(*args, **kwargs):
            result = actual_catalogue(*args, **kwargs)
            observed["actual_catalogue_rule_count"] = len(result["rules"])
            if mutate:
                redirected.write_bytes(original + MUTATION)
            return result

        with ExitStack() as stack:
            stack.enter_context(patch.object(reuse, "_file", side_effect=file_owner))
            stack.enter_context(patch.object(reuse, "build_reuse_report", side_effect=reuse_owner))
            stack.enter_context(patch.object(source_catalogue, "build_catalog", side_effect=catalogue_owner))
            sentinels = [stack.enter_context(patch.object(owner, name,
                         side_effect=AssertionError("unexpected execution: " + name)))
                         for owner, name in ((reuse_run, "run_entry"),
                                             (subprocess, "run"),
                                             (subprocess, "Popen"), (os, "system"))]
            try:
                result = organization.build_organization_report(ROOT)
            except FrameworkError as error:
                observed.update({"outcome": "FRAMEWORK_ERROR", "error": str(error),
                                 "error_type": type(error).__name__})
            else:
                observed.update({"outcome": "REPORT_RETURNED", "status": result["status"],
                                 "final_report_target_sha256": result["inputs"].get(TARGET),
                                 "semantic_authority": result["semantic_authority"],
                                 "action_authority": result["action_authority"],
                                 "runtime_execution_performed": result["runtime_execution_performed"]})
            observed["execution_sentinel_calls"] = sum(item.call_count for item in sentinels)
        observed["temporary_final_sha256"] = digest(redirected.read_bytes())
    observed["installed_target_sha256_after"] = digest((ROOT / TARGET).read_bytes())
    observed["installed_target_unchanged"] = (observed["installed_target_sha256_after"] ==
                                               observed["initial_target_sha256"])
    observed["accepted_identity_disagreement"] = (
        mutate and observed["outcome"] == "REPORT_RETURNED" and
        observed["reuse_projection_target_sha256"] != observed["final_report_target_sha256"])
    return observed


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: probe.py EXCLUSIVE_OUTPUT_JSON")
    started = datetime.now(timezone.utc).isoformat()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                          text=True, capture_output=True).stdout.strip()
    before = identity_snapshot()
    result = {"schema": "nabt.input-identity-review.observation.v1",
              "review_url": "https://github.com/sonaiso/NABT/pull/64#discussion_r4433077476",
              "started_at_utc": started, "git_head": head,
              "command": "PYTHONPATH=src:. python -B " + str(Path(__file__).relative_to(ROOT)) +
                         " " + sys.argv[1],
              "probe_sha256": digest(Path(__file__).read_bytes()),
              "installed_file_sha256_before": before,
              "required_behavior": "Reject disagreement with the earlier owner input digest using FrameworkError; clean control resolves.",
              "clean_control": observe(False), "late_byte_change": observe(True)}
    result["installed_file_sha256_after"] = identity_snapshot()
    result["all_recorded_installed_files_unchanged"] = (before == result["installed_file_sha256_after"])
    result["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    raw = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with Path(sys.argv[1]).open("x", encoding="utf-8") as output:
        output.write(raw)
    print(raw, end="")


if __name__ == "__main__":
    main()
