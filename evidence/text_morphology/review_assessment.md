# Independent text-morphology review

## Result

The 40 cases authored before opening the new reader passed on its first usable
measurement and again after the post-open correction. Each result contains the
runtime/evaluator file inventory and digest, and each measured snapshot has a
separate code archive. Original material and results were not overwritten.

| Measurement | Positive capability | Boundaries and restraint | Total |
|---|---:|---:|---:|
| First usable reader | 16/16 | 24/24 | 40/40 |
| Reader after the alif-tanwin correction | 16/16 | 24/24 | 40/40 |

The positive score covers noun evidence from terminal tanwin on unfamiliar
stems, candidate verb links after three exact markers, and source-qualified
nominal/construction/diptote consequences. A candidate verb link remains a
candidate; its success does not count as a licensed lexical verb or a case
assignment. The 18 post-open test methods also pass. One method replays the
40 fixed cases; the others test independent byte structure, omission of lexical
evidence, source revision, contradictory readings, attacks on reports and
numerical encodings, and malformed input.

## Defect found after the fixed-case run

The initial reader accepted `اٌ`, `اٍ`, `رَجُلاٌ`, and `رَجُلاٍ` as licensed noun
readings because it treated every terminal tanwin placement as orthographically
available. The observed overreach is preserved in `review_findings_v1.json`.
The declared ordinary spelling profile does not license damm/kasr tanwin on an
alif long/support carrier. A new guard now raises `INVALID_ALIF_TANWIN` before
any noun receipt is issued. The new regression test is explicitly post-open;
it was not inserted retrospectively into the frozen 40-case material.

Both frozen fath-tanwin notations, `رَجُلًا` and `رَجُلاً`, continue to pass.
Broader orthographic, Quranic, poetic and lexical spelling coverage is not
established by these tests.

## Material and evaluator independence

`independent_material_freeze_v1.json` records the material freeze and its hashes.
The reviewer had read the public scope proposal, the previous reader's source
language, and the pinned grammatical audit before creating the cases. This
informed design is disclosed; the cases are not a hidden external corpus.
The evaluator's byte/hash/identity checks do not call the production parser.
Its linguistic property checks project the fixed gold onto the public report.
The additional replay call checks a submitted report against the source using
the production reader; that replay is not a second independent Arabic parser.

Source-local `al` and `idhafa` properties are excluded from transferred lexical
premises. Identical surface occurrences keep distinct byte identities. Exact
lexical matching preserves spelling and cannot silently strip a final vowel.
The source-relative semantic division `jins_jamid` versus `mushtaq` remains the
universal-nominal denotation axis; the review does not infer etymological roots,
verb productivity, agent roles, actual case, or world facts from it.

## Review conclusion

The measured implementation supports the declared bounded acquisition path and
its replay boundary. It does not complete the wider objective of deriving all
Arabic lexical classes, nun attachments, article segmentations, derivations or
government relations from unrestricted new text. Those remain named debts, not
answers supplied by the fixed property fixture or the source policy.
