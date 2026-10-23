# Discourse evaluation: independent material and post-review comparison

## Result and its scope

The final discourse snapshot v3 completes **57/86 independent authored episodes**, including **12/30 designated positive episodes** and **2/4 withheld terminal-realization transfers**. It has **0 observed false acceptances** in this material. The strict suite remains incomplete. The allowed-boundary CI mode is an explicit regression gate for this bounded release; it does not turn the remaining positive misses into successes.

The common-adapter comparison is:

| Measure | v1 | v2 | v3 |
|---|---:|---:|---:|
| Strict complete episodes | 68/86 | 57/86 | 57/86 |
| Positive episodes (P) | 19/30 | 12/30 | 12/30 |
| Withheld terminal realizations (T) | 4/4 | 2/4 | 2/4 |
| Boundary episodes (B) | 26/32 | 24/32 | 24/32 |
| Lexical/acquisition controls (L) | 7/8 | 7/8 | 7/8 |
| Replay and invalid context (V) | 12/12 | 12/12 | 12/12 |
| Substantive questions | 36/45 | 24/45 | 24/45 |
| No-support question controls | 29/29 | 29/29 | 29/29 |
| All question obligations | 65/74 | 53/74 | 53/74 |
| Forbidden accepted claims / integrity false accepts | 1 | 2 | 0 |
| Outer / question execution errors | 0 / 0 | 0 / 0 | 0 / 0 |


A complete episode must satisfy every frozen claim, reading, reference, question, and blocker obligation attached to that episode. A safe `DEFER` does not complete a required positive assertion or a requested reference/role/case loop. Boundary cases can contain both safety obligations and positive sub-obligations, so their pass counts are not pure specificity estimates. The 29 no-support question controls are separated from the 45 substantive questions rather than used to inflate answer success.

These results measure a new bounded interface with explicit context premises and supervised lexical evidence. They are not a replacement score for the older broad Arabic corpus. The original material was authored independently of the new implementation; v2/v3 are comparisons after review feedback, not newly untouched holdouts.

The immutable machine-readable comparison, exact hashes, failed-check deltas, and raw/code archive references are in [independent_comparison_v1.json](../evidence/discourse/independent_comparison_v1.json). Detailed measurement history is in [independent_review.md](../evidence/discourse/independent_review.md).

## What was frozen before implementation inspection

The [protocol](../evidence/discourse/independent_protocol_v1.md), [86 cases](../evidence/discourse/independent_cases_v1.json), [source inventory](../evidence/discourse/independent_source_inventory_v1.json), and [source audit](../evidence/discourse/independent_source_audit_v1.json) were frozen together under [independent_freeze_v1.json](../evidence/discourse/independent_freeze_v1.json). The author read public 0.12.0a3 interfaces, prior published results, pinned QAC bytes, and primary grammar/Lean sources before opening the new discourse/person code. No later correction changes the gold, its source split, names, questions, expected claims, or denominator.

The five groups are 30 positive episodes, four transfer episodes, 32 boundary episodes, eight lexical/acquisition controls, and 12 replay/context cases. The last group comprises seven source/context/question replay mutations and five invalid-context tests. The 74 question calls reuse the original text, context, and learned source model; answers are not passed back as source assertions.

The independent author is an evaluation agent. This is authored, source-informed material, not human-adjudicated natural-corpus gold. Separation from implementation was procedural in a shared workspace, not a filesystem-security guarantee. These distinctions constrain what can be claimed from the scores.

### Source closure and acquisition

The source is QAC 0.4, decoded SHA-256 `a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46`. The independent scanner records exact locations, record byte spans, and complete segment recompositions without importing NABT. Most episodes use source-known lexemes in new authored texts and contexts.

The four transfer cases exclude a fixed union of **83 complete verses** selected by the terminal source realizations أَمِينٌ، كَرِيمٌ، حَكِيمٌ، بَصِيرٌ. Their corresponding source forms are absent after the joint split, while compatible witnessed u/i realizations of each lemma remain. The source-closure check is performed after the union of exclusions, avoiding a claim of transfer when the rule's necessary training premise has also been removed. v3 completes the أمين and حكيم episodes; كريم and بصير remain strict misses because complete compatible predicate-construction evidence is not established across all viable alternatives.

This is transfer to a new terminal realization of a known supervised lemma/root family. QAC POS, lemma, root, person, gender, number, aspect, voice, and segmentation remain human annotations. The learner receives their raw source bytes and exclusions, never this evaluation's role, case, claim, or answer labels. CASE/MOOD are masked; independent erase/poison checks compare semantics, not source hashes, and both pass in this material. An unknown-family control requires abstention. None of this establishes unsupervised lexical meaning or induction of arbitrary new roots.

Context names, entity identities and optional traits, speaker/addressee IDs, deictic targets, and the closed-reference-scope flag are explicit supplied premises. Context does not contain a predicate, role, valency, case, or answer. A supplied participant ID supports a conditional reference, not a discovered real-world identity. Group participants are one declared ID; the reader does not invent their members.

## What the complete positive cases demonstrate

The following are concrete examples from the v3 passing positive subset. The examples retain the exact source/model/context qualification described above.

| Capability | Passing material | What is established |
|---|---|---|
| Speaker and addressee reference | P01 `أَنَا حَكِيمٌ.`; P04 `نَحْنُ فَرِحُونَ.`; P05 `أَنْتُمَا مُسْلِمَانِ.` | Reference follows the supplied participant ID with the requested compatible number/gender evidence; group membership is not inferred. |
| Named nominal assertion | P06 `حَازِمٌ أَمِينٌ.` | A named entity and independently witnessed predicate support the qualified property and its question. |
| Closed prior-reference search | P07 `حَازِمٌ جَمِيلٌ. هُوَ حَكِيمٌ.`; P10 repeats the same entity before the pronoun | A unique compatible prior entity can bind; repeated mentions of that ID do not create fictitious ambiguity. |
| Explicit deixis | P11 `هَذَا حَكِيمٌ.` | The reference uses the explicit context mapping for هذا. |
| Multiple question bindings | P16 `حَازِمٌ حَكِيمٌ. سُهَيْلٌ حَكِيمٌ.` | A person query returns both supported named bindings with their proofs. |
| Qualified events | P19 `عَمِلَ حَازِمٌ.`; P20 `يَعْمَلُ حَازِمٌ.` | Event kind, active voice, actor and past/nonpast tense are retained. |
| Place-qualified event | P21 `يَعْمَلُ حَازِمٌ فِي الْبَيْتِ.` | A source-qualified prepositional relation and explicit place entity qualify the same event. |
| Attached subject participant | P29 `دَخَلْتَ.` | The witnessed host and attached subject identify the supplied addressee; a bare final ت is not a general person rule. |

These 12 episodes demonstrate bounded end-to-end successes. The total 57/86 includes controls and replay, so it should not be quoted as 57 successful positive understanding episodes. Likewise, the seven passing lexical/acquisition controls include prohibitions on unsupported promotion as well as positive observations.

The question breakdown is:

| Expected answer outcome | v1 | v2 | v3 |
|---|---:|---:|---:|
| SUPPORTED | 29/34 | 22/34 | 22/34 |
| REFUTED | 1/2 | 0/2 | 0/2 |
| CONFLICT | 1/1 | 0/1 | 0/1 |
| BINDINGS | 5/8 | 2/8 | 2/8 |
| NO_GROUNDED_SUPPORT | 29/29 | 29/29 | 29/29 |


`SUPPORTED` and `REFUTED` require a proof of the requested signed qualified proposition or its explicit opposite. `CONFLICT` requires both. `BINDINGS` requires complete binding groups with compatible domains and source proofs. `NO_GROUNDED_SUPPORT` allows safe nonanswers but does not demonstrate positive question understanding. The zero v3 refutation/conflict counts in these particular positive tests remain reported, even though the underlying finite semantic law and separate tests cover signed reasoning.

The intermediate obligations distinguish output integrity from successful interpretation:

| Obligation | v1 | v2 | v3 |
|---|---:|---:|---:|
| Correlated required readings | 37/44 | 34/44 | 33/44 |
| Required fully qualified claims | 44/53 | 31/53 | 30/53 |
| Explicit force preservation | 2/5 | 2/5 | 2/5 |
| Original report integrity and replay | 81/81 | 81/81 | 81/81 |
| Answer integrity and replay | 74/74 | 74/74 | 74/74 |
| Rejection after changed input premise | 7/7 | 7/7 | 7/7 |

A required reading combines its requested morphology, reference, role, actual case/sign and source span within one reading. These 44 obligations have different field requirements; their score is not an independently sampled accuracy estimate for every grammatical role. Replay of a correctly deferred report is valid but does not constitute a successful parse. L03 below demonstrates why a correct nun observation and conditional sign are reported separately from actual role/case activation.

## What the review changed

### Predicate construction: corrected acceptance with a coverage cost

In v1, B21 `حَازِمٌ أَمْسِ.` produced a grounded property claim for أمس despite both viable lexical readings having unknown construction. Their nominal-predicate assignment required رفع, but no actual inflected/local case was established. The v2 general guard requires predicate-construction evidence and respects the assignment's obligations. B21 then safely defers.

This is not acquisition of the temporal meaning of أمس. All four QAC lemma records used here are POS `N`, not `T`, and are parts of بالأمس. The correction does not relabel those annotations or add an exception for this word. The guard also rejects other incomplete predicate alternatives. Strict completion falls from 68/86 to 57/86, positive completion from 19/30 to 12/30, and terminal transfer from 4/4 to 2/4. Those losses are retained; weakening the guard to restore the earlier score would undo the reviewed evidence requirement.

The per-case explanation and first preserved result are in [independent_review_v1.json](../evidence/discourse/independent_review_v1.json). The complete v1/v2 comparison is retained in [independent_review_v2.json](../evidence/discourse/independent_review_v2.json).

### Prior-source completeness: corrected narrowing of pronoun candidates

In v2, B04/B05 have the source `حَازِمٌ جَمِيلٌ. سُهَيْلٌ كَرِيمٌ. هُوَ حَكِيمٌ.` The middle clause defers under the stronger predicate guard. Its named entity is consequently omitted from the licensed mention index, leaving only حازم in the later candidate set. The reader wrongly treats this smaller set as closed and asserts that حازم is حكيم. In B05, سهيل's gender/number are unknown; unknown features must keep a possible competitor, not exclude it.

V3 records whether the **prior source prefix is complete**. A preceding `DEFER` prevents closure of the prior-reference search even if the context's closed-scope flag is true. Explicit named, speaker, addressee, deictic, and relative-return premises remain distinct from this antecedent search. A prior `MENTION` or licensed clause does not itself make the prefix incomplete. The current clause is not counted as a prior clause.

This removes the two forbidden accepted claims in B04/B05. They still miss the strict gold's positive candidate/claim obligations: v3 does not manufacture a licensed mention for the deferred middle clause. Their episode scores therefore remain failures. The same conservative rule also removes the previously accepted pronoun claim/reference in P09, whose earlier female clause is incomplete. This additional loss is recorded as new failed checks within an already failing episode; it is not silently waived or counted as successful disambiguation.

The separately authored six-case source-prefix regression improves from 2/6 on v2 to 6/6 after the fix; its [protocol and results](../evidence/discourse/prefix_scope_review/protocol_v1.md) are post-review evidence and are not added to the 86-case independent denominator. The earlier 26-case review matrix is likewise a separate targeted regression, with authored lexical premises rather than claims of untouched QAC examples.

## Remaining strict misses and their interpretation

| Boundary or missing capability | Frozen cases | Interpretation |
|---|---|---|
| Predicate construction incomplete across viable alternatives | P02/P03/P08/P12/P14/P15/P17/P18, T02/T04, B24; related B04/B05 | The evidence guard prevents admission. These are positive coverage losses, not successes merely because the system abstains. |
| Prior-reference prefix incomplete | P09, B04/B05 | V3 blocks a claim to closed search; full candidate retention and positive reference completion remain unfinished. |
| Context-name accusative spelling | P13; contributes to P27 and B15/B16 | حازمًا/سهيلًا include a written alif absent from the declared context names. Conservative matching does not silently delete it. |
| Temporal lexical premise missing | P22/P23/B25 | The intended أمس/غد source records are `N`, not an acquired temporal `T` witness. Future marking alone cannot supply the time relation. |
| Temporal position not covered | P24 | A known adverb between subject and predicate is outside the initial trailing-adverb reduction. |
| Explicit nominal relative return | P25 | The frozen nominal clause with explicit هو is not completed by the initial bounded implicit verbal-return frame. No universal rejection of hidden classical returns is claimed. |
| Gold/runtime qualification interpretation differs | P26 | The runtime preserves idafa restriction and answers the repeated-idafa question; the frozen required claim has `restriction:[]`. The strict miss stays. Erasing the restriction or changing gold to force a pass is unjustified. |
| Full attached host and valency witness | P27/P28 | Unsupported host/recitation geometry is not silently stripped; the new attached-object form and its binding remain unlicensed. |
| Attached interrogative hamza | P30 | The proposition is read, but the hamza joined to the context name does not complete the question. |
| Force recognition incomplete | B14/B15/B16 | No fact is asserted, but the required imperative/wish/hope force is not retained. Abstention is narrower than force understanding. |
| Attached conjunction/name | B19 | The coordinated negative episode is deferred, so the explicit negative query lacks its full proof. |
| Actual mood blocked after morphology succeeds | L03 `لَمْ يَحْزَنُوا.` | Radical nun and deleted رفع nun are correctly distinguished and the conditional جزم/deletion sign exists. Actual جزم remains null because reference/syntax obligations are unresolved. This is a role/case activation gap, not a nun-category acquisition failure. |

The full case/check list is preserved in the result and [review ledger](../evidence/discourse/independent_review.md). Unknown gender/broken-plural singular links, weak lexical bases, and nun attachment outside witnessed source geometry are not claimed solved by this discourse benchmark. Nor do these tests establish arbitrary relative clauses, why/how reasoning, a general causal calculus, calendar grounding, or full command pragmatics.

## Measurement integrity and adapter corrections

Every final comparison run checks the approved runtime manifest, snapshot, original archive and exact 67-file authoritative inventory; a self-consistent arbitrary manifest is not accepted. Fresh subprocesses isolate runtime imports, and loaded module origins must lie in the chosen runtime root. The run archives runtime, evaluator and evaluator-test bytes, preserves raw reports/answers, and rechecks every measured byte at completion. Known existing documentation metadata is explicitly listed separately from authoritative runtime files.

The first attempted measurement completed the 86 raw calls but failed finalization because a shared test filename was overwritten by another task. Its raw log and original code archive remain, and its recovered score is marked `measurement_valid:false`. No original final JSON was created. Test ownership moved to `tests/test_discourse_evaluator.py`.

The first adapter also incorrectly assumed that qualified closed operator readings always carry lexical stem fields. Three integrity failures were adapter errors, not linguistic failures. The correction allows the established exact one-part operator representation only; missing noun/verb stems remain invalid. Both events are documented in [adapter erratum v1](../evidence/discourse/independent_adapter_erratum_v1.json).

A separate reviewer then demonstrated seven evaluator weaknesses using synthetic unit fixtures without reading the independent gold: claim arguments could detach from role references; named references could detach from context names; predicates could borrow a subject lemma; and question kind, variable domain, binding status or complete binding coverage could be forged. The hardened adapter correlates these fields within the same analysis and original context/question. It preserves full time qualifications in proof equality. The changes and retained before/after measurements are in [adapter erratum v2](../evidence/discourse/independent_adapter_erratum_v2.json).

The common comparison adapter adds the v3 pin, source-prefix receipt checks and an explicit opt-in boundary policy. Its **26 focused tests** include the negative mutation checks. All three snapshots are rerun with those identical evaluator/test bytes, recorded in [independent_adapter_release_v1.json](../evidence/discourse/independent_adapter_release_v1.json). Gold is unchanged throughout.

After that comparison, a gate-only revision documents P09's two newly missed positive checks. It adds only `required_claim:0` and `reading:0` to that case's existing `question:0` exception. Every measurement/scoring function is AST-identical to the three-runtime comparison adapter. A new focused test rejects additional signatures and false acceptances, bringing the evaluator test count to **27**. The [old gate rejection](../evidence/discourse/independent_gate_before_p09.json) and [explicit policy revision](../evidence/discourse/independent_gate_revision_v1.json) remain separate from the immutable strict scores.

## Reproduction and the CI contract

A strict v3 measurement can be run from the repository root:

```sh
python tools/discourse_evaluation.py \
  --qac artifacts/local/inflection-evaluation/quranic-corpus-morphology-0.4.txt.gz \
  --runtime-root . \
  --runtime-freeze evidence/discourse/code_freeze_v3.json \
  --output artifacts/local/discourse-evaluation/new_strict_run.json
```

The output path must be new. The tool refuses overwrites. The strict command exits 1 while any frozen obligation fails. The result preserves `strict_pass:false` and `coverage_complete:false` for partial coverage.

`--allow-documented-boundaries` enables a separate release-regression decision. It is restricted to the approved v3 runtime and an explicit **case-and-failed-check** list. It accepts neither an arbitrary new runtime nor a new failed check merely because the case ID was already listed. A false accepted claim, integrity/replay failure, execution error, missing case, or unexpected miss blocks the gate. A passing partial gate means only that the observed incomplete profile is preserved without those prohibited regressions.

No strict result is rewritten to show success. A gate-policy change must be documented independently of the immutable measurement; it must not alter the gold or a preserved output. The current decision and exact permitted checks are described in [independent_review.md](../evidence/discourse/independent_review.md).

The [v3 opt-in rerun](../evidence/discourse/independent_runs/independent_v3_gate_reviewed.json) passes this release policy with **29 documented incomplete cases**, no unexpected failed checks, and zero false acceptances. Its `strict_pass` and `coverage_complete` remain false. All 86 raw case records are identical to the pre-policy v3 measurement after ignoring only `score.seconds`; [independent_gate_verification_v1.json](../evidence/discourse/independent_gate_verification_v1.json) records that comparison. The [retention manifest](../evidence/discourse/independent_retention_manifest_v1.json) identifies 27 exact repository-retained artifacts, including every earlier raw result and measured code archive.

## Published historical regressions remain separate

The release rerun of the older Arabic interface preserves **0/40** complete broad episodes, **8/12** declared-scope episodes, and **0/8** excerpt semantic reads. Its questions are respectively 0/43 and 9/11 where the earlier matrix defines them. The controlled text interface preserves **60/60** episodes and **126/126** question checkpoints. The earlier inflection profile remains 72/74 with its two explicitly documented premise boundaries, post-review 22/22, and CLI 32/32.

Those are published regression materials with different interfaces and premises. They are not held-out discourse results, and comparing 0/40 with 12/30 as one numerical improvement rate would mix denominators. The new evidence is the explicit bounded discourse successes and their current-source proof/answer loops; the broader reading gap remains visible.
