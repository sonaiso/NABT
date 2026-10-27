"""Reproduce the 11-input import-order comparison against the published parent.

This replay script was retained after the original interactive comparison.
The original comparison result is proposal-differential.json. Replay writes a
new output path and refuses to overwrite evidence. This is a deterministic toy
model comparison, not retraining or a language-coverage measurement.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import inspect
import json
from pathlib import Path
import subprocess
import sys
import types


ROOT = Path(__file__).resolve().parents[3]
BASE = "3727825da5dde66f9f69909128626c1915edb484"
PRIOR_SHA = "16c0f1abbe48166e1aadda83144e75f8b4f6fe69622530792126487c2d7e7d61"
CURRENT_SHA = "e6b5fb097d321f2e05327e88e2539bca36e9586d8b6ffd418187eae543bfad8b"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite an existing result")
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    import torch
    from tools.arabic_training.proposal import propose
    from tools.arabic_training.model_v2 import MaskedMorphologyModel

    filename = "tools/arabic_training/proposal.py"
    prior = subprocess.check_output(["git", "show", BASE + ":" + filename], cwd=ROOT)
    current = (ROOT / filename).read_bytes()
    if sha256(prior).hexdigest() != PRIOR_SHA or sha256(current).hexdigest() != CURRENT_SHA:
        raise SystemExit("Comparison implementation identity changed")
    legacy = types.ModuleType("tools.arabic_training._prior_proposal")
    legacy.__file__ = str(ROOT / filename)
    legacy.__package__ = "tools.arabic_training"
    exec(compile(prior, legacy.__file__, "exec"), legacy.__dict__)

    torch.set_num_threads(1)
    torch.manual_seed(47)
    vocab = dict(words=["<PAD>", "<UNK>", "كَتَبَ", "زَيْدٌ"],
                 chars=["<PAD>", "<UNK>", *sorted(set("كَتَبَزَيْدٌ"))],
                 labels=dict(tag=["NOUN_PROP", "PV"], declension=["معرب", "مبني"],
                             case_mood=["مرفوع", "مبني"]), affixes=["PRON"])
    model = MaskedMorphologyModel(vocab).eval()
    receipt = dict(files={"weights.npz": "differential-fixture-only"})
    inputs = [b"\xff", b"", b" ", b"x" * 16385, *[text.encode() for text in [
        "كَتَبَ زَيْدٌ", "  كَتَبَ\tزَيْدٌ\nكتب ", "َكَتَبَ", "كَُتَبَ",
        "بَ" * 20, "١َ", "كَتَبَ،"]]]
    rows = []
    for raw in inputs:
        before = legacy.propose(raw, model, vocab, receipt)
        after = propose(raw, model, vocab, receipt)
        if before != after:
            raise SystemExit("Proposal result differs for " + sha256(raw).hexdigest())
        rows.append({"input_sha256": sha256(raw).hexdigest(), "bytes": len(raw),
                     "status": after["status"], "unchanged": True})
    if inspect.signature(propose) != inspect.signature(legacy.propose):
        raise SystemExit("Public signature changed")
    result = {"schema": "nabt.proposal-admission-followup-differential.v1",
        "base_commit": BASE, "old_proposal_sha256": PRIOR_SHA, "new_proposal_sha256": CURRENT_SHA,
        "signature_unchanged": True, "result_count": len(rows), "exact_results_unchanged": True,
        "cases": rows,
        "scope": "Same deterministic toy weights and inputs before/after import-order refactor; no retraining or linguistic-coverage claim."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(json.dumps({"result_count": len(rows), "exact_results_unchanged": True}))


if __name__ == "__main__":
    main()
