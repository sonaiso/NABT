"""Seal authored material before any prediction; never rewrite a freeze."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path


OUT = Path(__file__).resolve().parent
NAMES = [
    "CONTRACT.md", "author_material.py", "freeze_material.py", "cases.json", "contexts.json",
    "lexical_profiles.json", "lexical_base.tsv", "lexical_mahira_number_omitted.tsv",
    "lexical_kariym_cross_pos.tsv", "source_premises.json", "audit_read_set.json",
    "pre_execution_validation.json", "adversarial_checks.json", "residual_and_validator_audit.json",
    "context_name_bridge_review.json",
]
validation = json.loads((OUT / "pre_execution_validation.json").read_text())
assert validation["case_count"] == 24 and validation["runtime_predictions_executed"] is False
assert validation["runtime_imported"] is False
rows = []
for name in NAMES:
    raw = (OUT / name).read_bytes()
    rows.append({"path": name, "bytes": len(raw), "sha256": sha256(raw).hexdigest()})
freeze = {"schema": "nabt.arabic-completion-independent-oracle-freeze.v1",
          "created_utc": datetime.now(timezone.utc).isoformat(),
          "before_new_runtime_prediction": True, "statistical_blind_sample_claimed": False,
          "runtime_implementation_reviewed": False,
          "old_gold_or_validator_or_runtime_modified": False,
          "baseline_commit": "d791fd7730cde2256dfac8a27687010b392876b3",
          "case_count": 24, "fixed_status_cases": 22, "conditional_provenance_probes": 2,
          "question_count": validation["question_count"], "files": rows,
          "scope": "Authored directed evidence/reference suite; independent of pending implementation, with disclosed prior-system and old-gold exposure."}
with (OUT / "freeze.json").open("x", encoding="utf-8") as handle:
    handle.write(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"freeze_sha256": sha256((OUT / "freeze.json").read_bytes()).hexdigest(),
                  "file_count": len(rows), "case_count": 24,
                  "question_count": validation["question_count"]}, ensure_ascii=False))
