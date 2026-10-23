# Standalone conjunction supplement

This is a separate two-case supplement to the frozen consumed-particle review.
The original six cases and their records remain unchanged. The authored source,
context, exact input bytes and expectations were frozen before the standalone
waw guard was changed. This is a regression check, not held-out language accuracy.

The immutable constructions v2 runtime passes the canonical `وَ` control and
incorrectly licenses `وُ`: both inputs produce two claims and support the same
canonical question. The result is therefore **1/2**, with CW02 failing. The
assignment count in the result sums all complete alternative analyses; it is
not a count of distinct grammatical roles.

The `scope` prose in the preserved runner/result was copied from the original
operator runner and incorrectly says “Nine”. The authoritative material,
freeze, result total and raw log all contain exactly **two** cases. This note
corrects that metadata description without changing the preserved runner or
result bytes, checks, expectations or score.

Reproduce the historical result with an independently extracted v2 archive:

```sh
python -I -B evidence/constructions/prefix_review/conjunction_supplement/run_review.py \
  --runtime-root /path/to/extracted/constructions-v2 \
  --runtime-freeze evidence/constructions/code_freeze_v2.json \
  --output-prefix /new/output/results_v2
```

The runner checks the exact 74-file runtime inventory and hashes before and
after execution, verifies the frozen material, rejects preloaded NABT modules,
and verifies that every imported NABT module belongs to the selected archive.
Outputs are created exclusively. The compressed raw log preserves both full
reports and answers.
