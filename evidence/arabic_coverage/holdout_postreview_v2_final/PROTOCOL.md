# Holdout v2 post-review gate

The preserved runtime-v2 execution scored **35/36** with the unchanged frozen
scorer and **63/63** matching question statuses. Its only failed check was
`H18 / question:2:no_grounded_evidence`. The original result and unsafe flag
remain in `original_result.json`; the exact raw records are preserved in
`original_raw.jsonl.gz`.

The review yields **36/36 after the demonstrated checker correction**, with
zero remaining unsafe flags. It is a post-execution rescore of those same
predictions, not a new blind experiment or a claim that the original strict
run passed. The earlier runtime-v1 execution and its separate 34-to-35 case
review remain in their original folders.

## Why H18 is a checker defect

The source says `لَيْسَ نَاصِرٌ حَكِيمًا.` and the question is `مَنْ حَكِيمٌ؟`.
The answer is `UNKNOWN`, with no positive proof or returned binding. It retains
counterproof receipts for the accepted negative Nasser claim. A variable
question can lack a positively proved answer while retaining evidence against
a particular candidate. It does not thereby assert that no one is wise.

The frozen scorer instead requires every `UNKNOWN` to contain no counterproofs.
Neither the input question nor its expected `UNKNOWN` was changed. The allowed
correction is limited to this exact failed check under the pinned material and
runtime; any additional failure needs separate review and causes exit 1.

## Pass conditions

1. The material freeze is exactly
   `127a5870fcbc8f8823b95f2a9f452cf4cd87de22fcfc62b271efd32bc684c106`,
   including all input and frozen-harness file hashes. The denominator remains
   36 cases and 63 questions.
2. The runtime manifest is exactly
   `1818fc27f076535734d9d9e90a857683f27d464f0a205637e7231cd6e870c40c`;
   its 77-file archive and every archive member match their approved hashes.
3. The original measurement is valid, its runtime is unchanged, and it has no
   runtime errors. Case/check inventories and all aggregate scores are
   reconciled. The single original H18 false alarm is preserved explicitly.
4. Every authoritative source entry equals the approved inventory. The
   holdout's larger inventory also contains three existing source-metadata
   files excluded by the original evaluators. Only those three exact paths
   may be additional; their complete before/after inventory and hashes must
   remain consistent. Any unknown extra file fails. This execution recorded
   79 source entries: 76 authoritative source entries plus three metadata
   entries. The runtime archive also contains `pyproject.toml`, making 77
   authoritative files in that archive.
5. Every raw line is canonical JSON and matches the captured journal and line
   digests. All 203 call identities are reconciled against the material. Raw
   source/answer identities, required and forbidden claims, claim-count bounds,
   question statuses, force checks, and context-collision observations are
   checked again instead of trusting headline pass flags.
6. The approved archive is extracted into an isolated temporary directory.
   The same lexical premises are relearned, then all **103 certificates** are
   freshly replayed: 36 document certificates, 63 answer certificates, and
   four changed-context rejections. Source bytes must remain unchanged, and
   imports must come from that extracted runtime.
7. H18's inquiry is supplemented from that same runtime and must have exactly
   the original answer's `question_report_id`. Both independent evaluators
   validate its source, inquiry and complete answer, including every viable
   interpretation, signed qualified claim, substitution and adjective
   agreement receipt. Positive proofs and returned bindings must be empty;
   every retained counterproof must be valid.
8. The evaluator files, shared question validator, imported regression gate
   helper and its policy remain unchanged during the review. Their bytes,
   the post-review tool and its adversarial tests are archived for reproduction.

Failure of any condition causes a nonzero exit. The tool never overwrites an
existing output directory or changes the supplied result/raw files.

The first post-review integration attempt is retained separately in
`../holdout_postreview_v2/`. It rejected the larger source inventory before
the explicit metadata correspondence was implemented. That folder preserves
the failed report, exact original tool bytes and the inventory-adapter review.

## Reproduce this preserved review

Use a new output directory:

```sh
python tools/arabic_coverage_postreview_v2.py \
  --result evidence/arabic_coverage/holdout_postreview_v2_final/original_result.json \
  --raw evidence/arabic_coverage/holdout_postreview_v2_final/original_raw.jsonl.gz \
  --runtime-freeze evidence/arabic_coverage/code_freeze_v2.json \
  --output-dir artifacts/local/postreview_reproduction_001
```

For CI, first run the unchanged holdout harness with an unused output path
inside the repository. Its known strict failure returns 1; a wrapper may
continue to the post-review command after that exit code, but must use the
post-review command's exit code as the final gate. Both the result and raw
journal must come from that attempt. The raw filename is the result filename
with `.json` replaced by `.raw.jsonl`.

```sh
PYTHONPATH=src python tools/arabic_coverage_holdout_v2.py \
  --output artifacts/local/arabic_coverage_ci_result.json

python tools/arabic_coverage_postreview_v2.py \
  --result artifacts/local/arabic_coverage_ci_result.json \
  --raw artifacts/local/arabic_coverage_ci_result.raw.jsonl \
  --runtime-freeze evidence/arabic_coverage/code_freeze_v2.json \
  --output-dir artifacts/local/arabic_coverage_ci_review
```

## Limits

All certificates receive runtime replay; the additional independent detailed
answer validation is specifically for H18. The 15 new adversarial unit tests
exercise the gate's refusal conditions without running the parser or changing
the oracle. An independent peer reviewed the original gate and the bounded
metadata/dependency amendment without executing or altering it. None of this
establishes unrestricted Arabic understanding, parser completeness, or world
truth beyond the supplied source statements and context premises.
