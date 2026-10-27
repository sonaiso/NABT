#!/usr/bin/env python3
"""Record this release's dependencies without resealing prior observations.

This is a post-development identity freeze, not a claim of unseen test data.
Historical raw observations and their checkers remain at their pinned paths.
The freezer makes no language prediction and does not change any denominator.
"""
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = ROOT / "evidence/source_acquisition_v1/independent_oracle/runner_freeze_v5.json"
PREVIOUS_SHA256 = "ecf96d1d8eabaa42d53522d179142ace305587eec3a3b49bd52a799a12ac323a"
PREVIOUS_ATTEMPT = HERE / "runner_freeze_v3.json"
PREVIOUS_ATTEMPT_SHA256 = "111fc2619cda93fd0225d7d6b7f602ba61ab538e0974d00173030bd26e81ea16"
HISTORICAL_FIELDS = ("material_freeze_sha256", "source_counterexample_material_sha256",
                     "historical_first_result_sha256", "historical_review_result_sha256")


def _previous():
    raw = PREVIOUS.read_bytes()
    if sha256(raw).hexdigest() != PREVIOUS_SHA256:
        raise ValueError("Historical dependency freeze changed")
    return json.loads(raw)


def _execution_lifecycle():
    previous = _previous()
    if sha256(PREVIOUS_ATTEMPT.read_bytes()).hexdigest() != PREVIOUS_ATTEMPT_SHA256:
        raise ValueError("Previous release attempt identity changed")
    return {
        "previous_release_attempt": {"path": str(PREVIOUS_ATTEMPT.relative_to(ROOT)),
                                     "sha256": PREVIOUS_ATTEMPT_SHA256},
        "identity_change_reason": "Run interface audit as a module so Makefile PYTHONPATH=src retains package resolution; no runtime, gold, UI, or formal-law change from v3",
        "before_first_new_runtime_oracle_prediction": False,
        "freeze_phase": "post_development_release_dependency_freeze",
        "development_measurements_may_precede_freeze": True,
        "blind_evaluation_claimed": False,
        "previous_published_dependency_freeze": {
            "path": str(PREVIOUS.relative_to(ROOT)),
            "sha256": PREVIOUS_SHA256,
            "created_utc": previous["created_utc"],
        },
        "runtime_calls_performed_by_freezer": False,
    }


def check_execution_lifecycle(freeze):
    for key, value in _execution_lifecycle().items():
        actual = json.dumps(freeze.get(key), ensure_ascii=False, sort_keys=True, allow_nan=False)
        expected = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
        if key not in freeze or actual != expected:
            raise ValueError("Dependency freeze execution lifecycle differs: " + key)
    if datetime.fromisoformat(freeze["created_utc"]) <= datetime.fromisoformat(_previous()["created_utc"]):
        raise ValueError("Current identity must follow the published predecessor")
    prior_attempt = json.loads(PREVIOUS_ATTEMPT.read_bytes())
    if datetime.fromisoformat(freeze["created_utc"]) <= datetime.fromisoformat(prior_attempt["created_utc"]):
        raise ValueError("Current identity must follow the preserved previous release attempt")


def dependency_paths(snapshot):
    previous = _previous()
    old_prefix = "evidence/source_acquisition_v1/independent_oracle/"
    new_prefix = "evidence/interface_migration_v1/independent_oracle/"
    wrappers = {name + "_v1.py": name + "_v4.py" for name in (
        "run_oracle", "run_regression", "review_continuation",
        "run_source_counterexamples", "test_continuation", "freeze_runner")}
    # Advance executable identities, keeping the first release attempt byte-exact.
    selected = {new_prefix + wrappers[row["path"].removeprefix(old_prefix)]
                if row["path"].startswith(old_prefix)
                and row["path"].removeprefix(old_prefix) in wrappers else row["path"]
                for row in previous["files"]}
    selected.update(new_prefix + name for name in wrappers)
    selected.update(new_prefix + name.replace("_v1.py", "_v2.py") for name in wrappers)
    selected.add(new_prefix + "runner_freeze_v1.json")
    selected.update(new_prefix + name.replace("_v1.py", "_v3.py") for name in wrappers)
    selected.add(new_prefix + "runner_freeze_v2.json")
    selected.add(str(PREVIOUS_ATTEMPT.relative_to(ROOT)))
    third_attempt = HERE.parent / "runner_attempts/03_cli_module_import_path"
    selected.update(str(path.relative_to(ROOT)) for path in third_attempt.rglob("*") if path.is_file())
    second_attempt = HERE.parent / "runner_attempts/02_ci_selector_not_advanced"
    selected.update(str(path.relative_to(ROOT)) for path in second_attempt.rglob("*") if path.is_file())
    preserved = HERE.parent / "runner_attempts/01_ui_scope_demo_before_correction"
    selected.update(str(path.relative_to(ROOT)) for path in preserved.rglob("*") if path.is_file())
    selected.add(str(PREVIOUS.relative_to(ROOT)))
    selected.update({
        "evidence/source_acquisition_v1/code_freeze_v1.json",
        "evidence/source_acquisition_v1/code_freeze_v1.tar.gz",
        "evidence/source_acquisition_v1/regression_policy_v1.json",
        "evidence/interface_migration_v1/build_runtime_freeze.py",
        "evidence/interface_migration_v1/build_catalog_references.py",
        "evidence/interface_migration_v1/regression_policy_v1.json",
        "tests/test_interface_migration_runtime_freeze.py",
    })
    # Complete source identities of the new executable layers are inexpensive
    # manifests; their raw bytes are archived only when a run is captured.
    for folder, pattern in (("tools", "*.py"), ("formal", "*.lean"),
                            ("integrations/proof_lab", "*.py"),
                            ("integrations/proof_lab/site", "*.mjs"),
                            ("integrations/proof_lab/site", "*.js"),
                            ("integrations/proof_lab/site", "*.json"),
                            ("integrations/proof_lab/site", "*.html"),
                            ("integrations/proof_lab/site", "*.css")):
        selected.update(str(path.relative_to(ROOT)) for path in (ROOT / folder).rglob(pattern)
                        if not ({".lake", ".openai", "node_modules", "dist", "__pycache__"} & set(path.parts))
                        and str(path.relative_to(ROOT)) != "integrations/proof_lab/site/worker/index.js")
    selected.update("evidence/interface_migration_v1/" + name for name in (
        "runtime_migration.json", "evaluator_registration.json",
        "catalog_references/proof_catalog.json", "catalog_references/grammar_link_summary.json",
        "catalog_references/mantuq_proof_links.json", "catalog_references/linguistic_proof_links.json",
        "catalog_references/licensed_proof_links.json", "catalog_references/catalog_migration.json"))
    # Future release summaries and transport metadata are not evaluator inputs.
    # New linguistic materials are pinned before release replay, not inferred
    # from whichever JSON output happens to be present afterward.
    for folder in ("evidence/lexical_transmission_v1", "evidence/scope_acquisition_v1"):
        for name in ("source_review.json", "independent_cases.json", "independent_cases.sha256"):
            path = ROOT / folder / name
            if path.is_file():
                selected.add(str(path.relative_to(ROOT)))
    independent = ROOT / "evidence/interface_migration_v1/independent_review"
    if independent.is_dir():
        selected.update(str(path.relative_to(ROOT)) for path in independent.glob("*.json"))
    selected.update(str(path.relative_to(ROOT)) for path in (ROOT / "tests").glob("*.py"))
    # Release entrypoint selectors are executable dependencies, including the new UI workflow.
    selected.update(str(path.relative_to(ROOT)) for path in (ROOT / ".github/workflows").glob("*.yml"))
    selected.update(row["path"] for row in snapshot["files"])
    # Pin source files referenced by the new independently reviewed inventories.
    for name in tuple(selected):
        if name.endswith("source_review.json") and (ROOT / name).is_file():
            review = json.loads((ROOT / name).read_bytes())
            for source in review.get("sources", []):
                if isinstance(source, dict) and isinstance(source.get("path"), str):
                    path = ROOT / source["path"]
                    if not path.resolve().is_relative_to(ROOT):
                        raise ValueError("Reviewed source escapes the repository")
                    selected.add(source["path"])
    return selected


def main():
    output = HERE / "runner_freeze_v4.json"
    if output.exists():
        raise ValueError("Never overwrite an observed dependency freeze")
    spec = importlib.util.spec_from_file_location("interface_migration_oracle", HERE / "run_oracle_v4.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runtime = HERE.parent / "code_freeze_v1.json"
    snapshot = runner.E.runtime_snapshot(runtime, ROOT)
    old = _previous()
    rows = [runner.file_row(ROOT / name) for name in sorted(dependency_paths(snapshot))]
    frozen = {key: old[key] for key in HISTORICAL_FIELDS}
    frozen.update(schema="nabt.interface-migration.directed-runner-freeze.v4",
                  created_utc=datetime.now(timezone.utc).isoformat(),
                  runtime_freeze_sha256=sha256(runtime.read_bytes()).hexdigest(),
                  previous_dependency_freeze_sha256=PREVIOUS_SHA256,
                  files=rows, historical_files_repinned=False,
                  scope="Known 24-case/29-question continuation and six source controls; no new blind sample.")
    frozen.update(_execution_lifecycle())
    check_execution_lifecycle(frozen)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(frozen, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"runner_freeze": str(output.relative_to(ROOT)),
                      "sha256": sha256(output.read_bytes()).hexdigest(),
                      "files": len(rows), "runtime_calls_performed": False}))


if __name__ == "__main__":
    main()
