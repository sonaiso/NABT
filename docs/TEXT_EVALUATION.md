# Independent evaluation of bounded text inquiry

The final runtime answers **126/126 query checkpoints across 60 controlled-Arabic
episodes**, including new definitions, properties, directed relations,
conditional rules, missing information, contradictions, and source revisions.
On **12 authentic passages** selected from the packaged grammatical books, it
preserves the original bytes and safely declines every unsupported passage:
**natural-source semantic coverage is 0/12**. These are deliberately separate
results. The controlled score is not a claim of arbitrary Arabic comprehension.

The original results, exact source texts, manual gold, runtime snapshots,
protocol, and replay tools are published in
[`evidence/text_inquiry/`](../evidence/text_inquiry/README.md). The reader's syntax
is specified in [TEXT_READER.md](TEXT_READER.md), and the source-relative inference
contract in [TEXT_INQUIRY.md](TEXT_INQUIRY.md).

## What was independent

A separate evaluator authored the corpus after agreeing the public grammar and
API with the builders. The evaluator read the earlier requirements and source
materials, but did not inspect the new reader or kernel implementations before
the recorded hidden runs. Expected statuses were manually assigned from the
declared contract; neither the production parser nor the production inference
engine generated the gold. No test text or gold was disclosed to the builders
before both hidden partitions had been executed.

The corpus uses new labels and combinations within an explicitly controlled
language. It is a hand-authored test collection, not an independently sampled
natural-language corpus. It contains no book passage disguised as a controlled
restatement. The book passages form a separate raw-source stratum.

Every returned proof was checked by evaluator code that did not call the
production verifier. That check independently read the ground question and
replayed source and excerpt hashes, source activation, scope, literal identity,
fact steps, rule substitutions, premise references, and the final conclusion.
This checks a finite returned derivation against the supplied text-bound
clauses. It does not prove that an arbitrary natural-language sentence has been
correctly interpreted, nor that a source assertion is true in the world.

## Freeze, reserve, and disclosure

The frozen dataset has SHA-256
`1edb63bd0df4e6c35e466b989a9bc4e55d5204d66a4771f6b72f073895419127`.
Its sixty episodes and 40/20 partition were fixed before the implementation was
run. Full chronology and exact snapshot identifiers are in the
[protocol](../evidence/text_inquiry/PROTOCOL.md).

| Run | Role at execution | Runtime snapshot prefix | Episodes | Query checkpoints |
| --- | --- | --- | ---: | ---: |
| Initial forty | Hidden first run | `454adcd3df89` | 40/40 | 81/81 |
| Reserved twenty | Previously unopened reserve | `215e3c72501c` | 20/20 | 45/45 |
| Initial forty after fixes | Regression | `215e3c72501c` | 40/40 | 81/81 |
| Complete portable replay | Published regression | `215e3c72501c` | 60/60 | 126/126 |

Between the first and reserve runs, independent code review found a missing-plan
counterexample and two VM defects. A proposed set of missing facts could itself
create a contradiction, so asserting it would fail to produce a clean answer.
The corrected implementation counterfactually checks proposed completions.
Separately, VM review required exact scope validation even for an otherwise
empty text program, and preservation of the active theory snapshot when a text
operation stops with an error. The VM evidence is in
[`program_review.json`](../evidence/text_inquiry/program_review.json).

These changes were **post-first-freeze reviewer adaptations**. They were not
driven by disclosed hidden episode text or gold. The first results remain
unchanged, and the reserve was opened only after the next runtime was frozen
and archived. The two original hidden partitions consequently refer to different
runtime snapshots; the final sixty-episode result is a regression result on the
final snapshot.

The first snapshot initially consisted of file hashes. After the review fixes,
the four changed files were reconstructed by reversing the known edits. All
33 files were checked against their original hashes before the reconstructed
archive was created. The [reconstruction record](../evidence/text_inquiry/code_freeze_first40_reconstruction.json)
states this explicitly. The reserve snapshot's bytes were archived before its
first run. Both archives are available for replay.

**The cases and labels are public now. Future runs on them are regression, not
new heldout evidence.**

## Controlled-language coverage

| Family | Episodes | Query checkpoints | Tested behavior |
| --- | ---: | ---: | --- |
| Definitions | 10 | 19 | New conjunction definitions, both equivalence directions, nested definitions, no invented instances, quoted labels |
| Facts | 10 | 21 | Positive and negative assertions, exact Unicode identity, duplicates, unknown entities, declarations without facts |
| Relations | 10 | 18 | Direction, argument identity, inverse rules, joins, repeated variables, quoted relation labels |
| Rules | 10 | 18 | Universal implications, chains, conjunction, negative premises and heads, constant heads, recursive structures |
| Uncertainty | 10 | 16 | Named missing literals, direct and derived conflict, contested dependencies, surviving clean alternate proofs |
| Revision | 10 | 34 | Fact/rule withdrawal, replacement, restored alternatives, source replay, independent scopes, unaffected results |
| **Total** | **60** | **126** | **All checkpoints passed on the final runtime** |

The 126 manually specified statuses comprise **50 supported, 11 refuted,
47 unknown, 11 conflicting, and 7 deferred because all available derivations
depend on contested premises**. A supported or refuted result remains conditional
on the supplied source theory; every checked result retains
`world_truth = NOT_ESTABLISHED`.

The conflict cases exercise the declared two-stage semantics: first compute
signed consequences, then exclude globally conflicted atoms from clean
derivations. Both signs for a question are a conflict. A single sign with an
independent clean proof remains usable; a sign available only through a
contested route defers. Unknown facts are never turned into negative facts.

The definition and relation examples test new combinations of the public
operations. They do not measure acquisition of a new parser, unannounced syntax,
or lexical meanings outside those operations. “Transfer” here means applying
the same declared operations to new labels and different rule/argument
structures without adding a case to the implementation.

## Comparison with a declared fact-only baseline

The baseline receives the same raw text, reader, source scope, and revision
sequence. It retrieves explicitly asserted signed facts and applies no
definition, universal, or conditional rule. It therefore isolates the benefit
of executing source-written rules after reading. It is not a language model,
a learned statistical system, or a competitor to one.

| Metric on all sixty episodes | Fact-only retrieval | Final inquiry kernel |
| --- | ---: | ---: |
| Correct status checkpoints | 84/126 — 66.7% | 126/126 — 100% |
| Episodes with every status correct | 28/60 — 46.7% | 60/60 — 100% |
| Correct supported/refuted answers | 28/29 — 96.6% | 61/61 — 100% |
| Correct answers among sufficient-evidence questions | 28/61 — 45.9% | 61/61 — 100% |

The baseline's one incorrect positive answer ignores a contradiction that is
derived by an explicit rule. Its other misses primarily reflect rules it does
not execute. The kernel obtains 33 additional correct supported/refuted answers
and 42 additional correct statuses on this selected set. These are bounded
inference gains; they do not establish statistical learning or general-language
superiority. Full baseline per-checkpoint output is in
[`results_fact_baseline.json`](../evidence/text_inquiry/results_fact_baseline.json).

## Authentic book passages

The evaluator selected four nonpilot excerpts from each packaged book. Original
UTF-8 byte intervals are half-open, zero-based, and verified against the pinned
whole-file hashes. Excerpts preserve internal markup, spelling, spacing, and
line breaks; no passage is cleaned or rewritten to fit the controlled grammar.

| Source | Original byte intervals | Selected content |
| --- | --- | --- |
| Qatr al-Nada | `[1452,1515)`, `[1681,1785)`, `[3822,3958)`, `[3548,3819)` | Word definition, declension characterization, speech definition, particle characterization |
| Alfiyya | `[2029,2115)`, `[3256,3342)`, `[12439,12536)`, `[2996,3085)` | Speech and predicate definitions, particle property, declension characterization |
| Kitab Sibawayhi | `[9391,9520)`, `[26150,26385)`, `[522895,523141)`, `[493166,493229)` | Word classes, predication dependence, definite-noun classes, genitive relation |

The [frozen manifest](../evidence/text_inquiry/real_source_candidates.json)
contains every raw excerpt, full parent-source hash, exact interval, excerpt
hash, and explicitly authored interpretation note. Parent-book offsets are
kept separate from the excerpt-relative source used for parsing.

All twelve excerpts produced named residuals, exact source restoration, and
whole-document nonadmission. Thus **12/12 safety checks passed, while 0/12
excerpts were semantically admitted**. A safe abstention is not counted as
understanding. The books were already packaged and visible to builders, and
the selections were purposeful; this is neither an unseen-book evaluation nor
a random estimate of Arabic corpus coverage.

The genuine excerpts and derived annotations retain their original
[CC BY-NC-SA 4.0 data terms and attribution](../evidence/text_inquiry/LICENSE-DATA.md).
The independently authored controlled episodes are marked separately.

## Integrity, revisions, and missing-plan review

All **37 public-contract adversarial/control probes** passed on both recorded
runtimes. They include **22 mutated certificates, all rejected**: changed
subjects, predicates, signs, scope, source identity, hashes, byte intervals,
rule bodies, bindings, premise links, version, analysis identity, and an
unsupported world-truth claim. Other probes check source withdrawal,
contradiction invalidating an old clean proof, harmless unrelated changes,
atomic rejection of invalid replacement, unsupported syntax, and resource
deferral. The count includes valid controls, so it is not described as 37
independent forgery attacks.

Three additional source-boundary probes passed: a caller-altered fact AST,
caller-altered rule AST, and caller-erased residual could not authorize the
invented claim. These are recorded separately from the original probe set.

Seven missing-plan review scenarios also passed. Each returned plan was added
as actual new raw text to a fresh copy of its source theory, and the target
question had to become cleanly supported. All seven returned plans did so;
zero infeasible plans were returned in these cases. A consistent-conjunction
control requires a real completion, preventing an implementation that returns
no plans from passing vacuously. These are reviewer-counterexample regressions,
not additional hidden language episodes.

## Uncertainty, cost, and limits

The exact raw counts and nominal Wilson intervals are stored in
[`summary_metrics.json`](../evidence/text_inquiry/summary_metrics.json). For
example, the 40/40 and 20/20 episode counts yield nominal 95% intervals of
91.2–100% and 83.9–100%; the two explicitly scored missing-premise items yield
34.2–100%. Zero accepted mutations among 22 trials has a nominal upper bound
of 14.9%. These figures make the small denominators visible. The hand selection,
shared patterns, and dependent checkpoints mean the intervals must not be
interpreted as population guarantees or confidence bounds for general Arabic.

The original forty completed in approximately **0.085 seconds**, the unopened
reserve in **0.043 seconds**, and the complete portable regression in
**0.122 seconds** in their recorded runs. Python and platform identifiers are
stored with the controlled results. Each episode was below its predeclared
5-second budget, and each complete run was below 180 seconds. These are small
local runs, not controlled hardware comparisons; peak memory was not measured.

The evaluation does not establish the roadmap's proposed 300-episode generality
gate, independent natural-language accuracy, correctness on unsupported syntax,
truth of external facts, or a universal refinement proof for Python. The formal
claims and their actual assumptions belong in [PROOF_STATUS.md](PROOF_STATUS.md).

## Reproduce the published regression

From the repository root, using the unchanged recorded runtime:

```sh
PYTHONPATH=src python tools/text_inquiry_evaluation.py \
  --output-dir /tmp/nabt-text-evaluation-rerun
```

The entrypoint runs all sixty controlled cases, twelve raw-source probes,
adversarial controls, completion-validity regressions, parsed-document boundary
probes, and the fact-only baseline. It returns a nonzero exit status if a scored
kernel/probe check fails. The frozen dataset and runtime file hashes are checked
before execution. The default checksum manifest is the
[portable projection](../evidence/text_inquiry/code_freeze_reserve20_portable.json)
of the recorded reserve/final snapshot. It preserves all **29 authoritative
source, configuration, and packaged-data records unchanged**, excluding only
four explicitly listed generated `.egg-info` metadata files. Those generated
files are absent from a fresh checkout and may be rewritten by packaging.
The original 33-file manifests, archives, and results remain unchanged.

The portable projection has its own manifest identifier,
`28f5f1a224a8896eeec3f0de4f920a543428000a154a3d3ed6b75fc7e005cfc9`;
it is not a changed runtime or a new hidden evaluation. A fresh source copy
without packaging metadata reproduced every suite. The defect, exact exclusions,
independent audit, and fresh-copy result are recorded in
[`portability_review.json`](../evidence/text_inquiry/portability_review.json).
Future snapshot capture also excludes generated packaging metadata.

`--suite`, `--partition`, `--data-root`, and `--code-freeze`
allow a focused replay or an explicit unchanged data copy. Historical evidence
is never the default output destination.

A deliberately changed runtime requires a new recorded checksum manifest. Such
a run is still regression on these public cases. It must not silently replace
the original scores or be described as a fresh heldout evaluation.
