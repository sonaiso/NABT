"""Add the reviewed runtime identity; never replace historical registry rows.

Run once after build_runtime_freeze.py. This is registration and selector
migration, not a new evaluation and not permission to modify material/gold.
"""
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OLD_NAME, NEW_NAME = "legacy_migration_v2", "certified_transition_v1"
OLD_HASH = "9f0eded8d010dcd349254adbc4cc4726c5c385aff53286dff37f3ba997fdca4b"
OLD_SNAPSHOT = "fa6a18a4b034433ef9d2dd2faf5754b1207b125b1d459831529344d2383b3d85"
OLD_ARCHIVE = "53a29f62b4a70382f05ccffaef5410b4f594ffd6260e51bf41e916f2df53f473"
OLD_POLICY = "8dac9b09df6c426446d4597421c15507bc80a15ab264d032e218a0caf5154cdc"


def main():
    output = HERE / "evaluator_registration.json"
    if output.exists():
        raise ValueError("Never overwrite an observed registration")
    raw = (HERE / "code_freeze_v1.json").read_bytes()
    manifest = json.loads(raw)
    current_hash = sha256(raw).hexdigest()
    new_snapshot, new_archive = manifest["snapshot_sha256"], manifest["archive_sha256"]
    new_policy = sha256((HERE / "regression_policy_v1.json").read_bytes()).hexdigest()
    count = len(manifest["files"])
    if count != 104 or manifest["previous_runtime_manifest_sha256"] != OLD_HASH:
        raise ValueError("Unexpected runtime predecessor or inventory")
    records = []

    def update(name, transform):
        path = ROOT / name
        before = path.read_bytes()
        after = transform(before.decode("utf-8")).encode("utf-8")
        if before == after:
            raise ValueError("Expected selector/pin delta absent: " + name)
        path.write_bytes(after)
        records.append({"path": name, "before_sha256": sha256(before).hexdigest(),
                        "after_sha256": sha256(after).hexdigest()})

    def new_identity(line):
        return (line.replace(OLD_HASH, current_hash).replace(OLD_SNAPSHOT, new_snapshot)
                .replace(OLD_ARCHIVE, new_archive).replace(OLD_NAME, NEW_NAME))

    def append_registered_rows(text):
        if NEW_NAME in text or current_hash in text:
            raise ValueError("Current identity already registered")
        out = []
        inserted = 0
        for line in text.splitlines(keepends=True):
            # Old rows stay byte-identical. New identity is a separate entry.
            if line.startswith("    '" + OLD_NAME + "':") or line.startswith("    '" + OLD_HASH + "':"):
                out.extend([new_identity(line), line])
                inserted += 1
            else:
                out.append(line.replace(OLD_NAME, NEW_NAME))
        if not inserted:
            raise ValueError("Previous registry row not found")
        return "".join(out)

    for name in ("word_evaluation", "morphology_evaluation", "governor_evaluation",
                 "inflection_evaluation", "discourse_evaluation", "construction_evaluation",
                 "verify_construction_package"):
        update("tools/" + name + ".py", append_registered_rows)
    for name in ("inflection_cli_evaluation", "arabic_syntax_evaluation", "text_inquiry_evaluation"):
        update("tools/" + name + ".py", lambda text: text.replace(OLD_NAME, NEW_NAME))
    for name in ("framework_foundation_gate", "framework_foundation_postreview"):
        update("tools/" + name + ".py", lambda text: new_identity(text).replace(OLD_POLICY, new_policy))
    for name in ("test_arabic_evaluation", "test_arabic_coverage_package_verifier"):
        update("tests/" + name + ".py", lambda text: text.replace(OLD_NAME, NEW_NAME))
    update("tests/test_recursive_source_bridge.py", lambda text: new_identity(text).replace(
        'self.assertEqual(len(frozen["files"]), 104)', 'self.assertEqual(len(frozen["files"]), 104)'))

    def inquiry(text):
        text = text.replace("PREVIOUS_CURRENT = ROOT / 'evidence/interface_migration_v1/code_freeze_v1.json'",
                            "PREVIOUS_CURRENT = ROOT / 'evidence/legacy_migration_v2/code_freeze_v1.json'")
        # Preserve the predecessor line while moving only the current selection.
        return "\n".join(line if line.startswith("PREVIOUS_CURRENT =") else new_identity(line)
                         for line in text.split("\n"))
    update("tests/test_rational_inquiry_freeze.py", inquiry)
    update("tests/test_completion_v6_gate.py", lambda text: text.replace(OLD_NAME, NEW_NAME)
           .replace("test_continuation_v5.py", "test_continuation_v1.py"))
    # Makefile/CI selectors are reviewed by the release integrator separately.

    output.write_text(json.dumps({"schema": "nabt.certified-transition.evaluator-registration.v1",
        "runtime_manifest_sha256": current_hash, "historical_registry_entries_preserved": True,
        "material_and_threshold_changes": False, "files": records,
        "new_runtime_predictions_performed": False}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"registered_runtime": current_hash, "file_count": len(records),
                      "previous_rows_preserved": True}))


if __name__ == "__main__":
    main()
