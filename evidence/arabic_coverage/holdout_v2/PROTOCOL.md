# Independent Arabic holdout: corrected input revision 2

This revision preserves the 36 cases, 63 questions, all expected statuses,
semantic claim patterns, contexts, lexical premises and denominators from the
independently frozen v1 material. It changes exactly four question strings
before any prediction run. The v1 material and its original freeze remain
unchanged.

The complete independence and metric contract is
[the original protocol](../holdout_v1/PROTOCOL.md). The evaluator is the exact
same frozen `tools/arabic_coverage_holdout_v1.py`; the new v2 command is a wrapper
which selects this corrected material directory. Result-schema version 1 and
the lexical source identity remain unchanged because the report schema and
original lexical premise bytes have not changed. The material freeze hash
identifies which input revision was measured.

## Pre-execution oracle correction

An independent source review found that four authored questions prefixed `هل`
to an explicitly negative clause. Ibn Hisham's *Mughni al-Labib* states a
restriction of `هل` to affirmative clauses and contrasts negative questions
formed with interrogative hamza. The exact primary passage, immutable source
identity and original defective inputs are retained in the
[pre-execution erratum](../holdout_review_v1/question_force_erratum.json).

| Case | Question index (zero based) | Original prefix | Corrected prefix |
|---|---:|---|---|
| H16 | 2 | هَلْ لَيْسَ | أَ لَيْسَ |
| H17 | 0 | هَلْ مَا | أَ مَا |
| H17 | 3 | هَلْ لَيْسَ | أَ لَيْسَ |
| H18 | 0 | هَلْ لَيْسَ | أَ لَيْسَ |

The full changed strings are in `question_source_addendum.json`. Detached
hamza is the published NABT input-token convention; the normally joined
orthographic variant is a separate coverage question and is not silently
normalized by this experiment. This correction follows the cited classical
author's stated rule. It does not claim to classify every modern or dialectal
use of `هل`, or every initial `ما`, which has nonnegative readings elsewhere.

The source correction changes no expected answer. It is not a response to
runtime behavior: neither v1 nor v2 was executed before this revision's freeze,
and the author has still not read pending runtime implementation code. The
original gold question-input audit was deferred until this v2 freeze to keep
the new material authoring separate from that historical material.

## Preservation and execution

The v2 freeze binds the complete corrected input files, source addendum, repair
script, this protocol, the v1 protocol and freeze, the unchanged v1 evaluator,
the v2 wrapper and the pre-execution erratum. Every call receives the same
types of text/context/lexical premises as v1, never expected labels. The
runner preserves every failure and uses exclusive output creation.

```sh
PYTHONPATH=src python tools/arabic_coverage_holdout_v2.py \
  --output evidence/arabic_coverage/holdout_v2/runs/first.json
```

The first run remains deferred until the root agent states that implementation
is ready. Neither input revision is a proof of unrestricted Arabic
understanding; ambiguity and missing context remain part of the tested
contract rather than defects to conceal.
