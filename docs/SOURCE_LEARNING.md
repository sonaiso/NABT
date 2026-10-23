# Source-bound property learning

NABT includes a native, bounded learning experiment over **three actual examples
quoted by Sībawayhi** and a separate compilation of **six grammatical
prescriptions** from Qatr al-Nada and the Alfiyya. Original UTF-8 bytes, source
pins, occurrence identity, reading identity, input cues, target endings, and
learner hypotheses remain separate throughout the path.

The implementation uses Python's standard library and the installed NABT
package. It has no runtime import, path lookup, symlink, submodule, download, or
execution dependency on a prior repository. The source adapter is deliberately
limited to its nine declared records. It does not parse arbitrary Arabic,
discover its own primitive property meanings, or establish a general case rule.

## Material and provenance

The modules were adapted from Qeyas commit
[`0ac045125f3d4ed9a984ab2f78a787fe9d014cd9`](https://github.com/sonaiso/Qeyas/tree/0ac045125f3d4ed9a984ab2f78a787fe9d014cd9),
including `qeyas/fractal_learning/{finite_guard,source_evidence,arabic_six_nouns}.py`
and `formal/{RuleLearning,PropertyEvidence}.lean`. The earlier rule-learning
baseline was commit `6af5840128f685e45ed5ae1070e606303985fb9a`. The native checker
and receipt domains are `nabt-six-nouns-source-v1` and
`nabt-source-receipt-v1`; their identities do not claim a new source authority.
The MIT copyright and permission notice for imported code is retained in the
repository's third-party notices.

The three complete original files are packaged in
`src/nabt/data/source_evidence/`, with their headers, OpenITI markup, original
spelling and line endings intact. Their combined size is 2,777,361 bytes.

| Source | Complete file SHA-256 | Bytes |
| --- | --- | ---: |
| Qatr al-Nada | `2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d` | 40,168 |
| Alfiyyat Ibn Malik | `13b351a0a02d9060fdedbb5db568544718eb4e89bef323f5572b8a26c0921ca0` | 97,798 |
| Kitab Sibawayhi | `a160f940bb194e6fe7e6655d2c7f28e41f1fc648c4c5e340cc4e42306d5cb625` | 2,639,395 |

The accompanying `source_manifest.json` retains immutable OpenITI references,
the prior Mashru citation audit and the explicit absence of its original
`qawaid.tsv` deposit. `pilot_examples.json` independently records selected
byte intervals. `pilot_conditions.json` records authored interpretation notes
and alternative readings. Their historical schema names are retained as
provenance. These descriptive files cannot change the approved source pins,
authorize a new source, or supply arbitrary truth bits to the learner.

The original texts and source-derived annotations retain **CC BY-NC-SA 4.0**
under the notice in
[`LICENSE-DATA.md`](../src/nabt/data/source_evidence/LICENSE-DATA.md).
The code license does not replace that data license. The bundled
[`README.md`](../src/nabt/data/source_evidence/README.md) and
`license_evidence.json` retain attribution, upstream notices and the recorded
limits of the prior license audit.

## Two separately typed schemas

### Literal examples

The observational schema declares these literal properties, in this order:

1. `cue_is_hadha`
2. `cue_is_raaytu`
3. `cue_is_marartu_ba`

| Record identifier | Input cue bytes | Target bytes | Independently read carrier | Label: carrier is waw |
| --- | --- | --- | --- | --- |
| `sibawayhi_han_hadha` | `هذا` | `هنوك` | `و` before `ك` | true |
| `sibawayhi_han_raaytu` | `رأيت` | `هناك` | `ا` before `ك` | false |
| `sibawayhi_han_marartu_ba` | separate `مررت` and `ب` spans | `هنيك` within `بهنيك` | `ي` before `ك` | false |

The third cue has two byte spans; the implementation does not fabricate a
contiguous `مررت ب` substring. Input spans do not overlap the target span.
Feature extraction sees only cues, while the output reader sees only the
target. The output reader accepts the declared four-codepoint `هن_ك` shape,
without cleaning, stripping marks, or normalizing Unicode.

These are three quotations in one selected passage about one lexeme. Their
interpretation as examples of **هن**, including the contextual reading of
`هناك`, is an explicit authored assumption. The schema assigns no
nominative, accusative, or genitive role to arbitrary text. No generated word
is counted as a source observation, and there are zero independent held-out
examples.

### Explicit prescriptions

The prescription schema declares `operation_is_raf`, `operation_is_nasb`,
and `operation_is_jarr`. Six records separately read the operation token and
the letter-name span from Qatr and the Alfiyya. An authored lexical mapping
interprets `واو`, `ألف`, and `ياء` as marker tags.

This path compiles existing author prescriptions. The second book repeats the
same three operation/marker vectors; it adds source agreement without adding
new feature vectors or an independent held-out evaluation. Prescription and
observation schemas have different fingerprints. The learner rejects an
attempt to mix them in one session.

## Public API and installed resources

```python
from nabt.learning import (
    GuardLanguage,
    LearningSession,
    default_pilot,
    observation_schema,
)

pilot = default_pilot()
proposal = pilot.propose("sibawayhi_han_hadha")
observation = pilot.to_observation(proposal)
assert observation is not None

session = LearningSession(GuardLanguage(observation_schema(), degree=1))
for item in pilot.observations("observed_example"):
    session = session.observe(item)

prediction = session.predict(observation.case)
assert prediction.status.value == "conditional_consensus"
assert prediction.possible == (True,)
```

`default_pilot()` and `SixNounPilot.from_package()` use
`importlib.resources` to read the complete installed source files. They also
work with archive-backed package resources. A process does not need the
repository checkout or a particular working directory.
`SixNounPilot.from_directory(path)` remains available for an explicitly
chosen copy of the same pinned files. A different copy with recomputed
manifest hashes is rejected.

| Method | Result and boundary |
| --- | --- |
| `propose(record_id)` | Build an untrusted proposal for one declared record |
| `check(proposal)` | Replay the fixed record, check every binding field, and distinguish accepted, pending and rejected |
| `to_observation(proposal)` | Replay again at consumption; return an observation only after ready admission |
| `observations(kind, source_id=None)` | Obtain checked records of `prescription` or `observed_example` kind |
| `prescription_records()` / `observed_records()` | Inspect the full source projections and their distinct spans |
| `assess_family(alternatives)` | Retain alternatives; unresolved families emit no independent asserted facts |
| `application_assessment(noun, alternatives=())` | Name missing application conditions and preserve source-described alternatives |

## Admission and trust boundaries

`SourceBlob` preserves an immutable byte snapshot and checks strict UTF-8.
`SourceSpan` is a nonempty half-open interval in those original bytes. It
checks the source identity, complete source digest, valid byte boundaries,
bounds and span digest. Canonically equivalent but differently encoded Unicode
strings retain different byte identities.

The fixed source policy pins complete files and selected context spans in
code. Every replay verifies the selected context and re-extracts the cue,
target and marker. Binding records retain occurrence, reading, source hash,
context hash, property definition, policy, schema and checker version.
Changing any of these rejects a proposal. An accepted receipt is a
recomputable identifier; it grants no authority when reused. Consumption
performs the replay again against the immutable checked snapshot. Later disk
edits cannot silently mutate that snapshot; creating a new snapshot checks
the complete source pin again.

A missing label stays unknown. Missing property bits stay unknown, and
unknown bits may not contain values. A partial proposal is pending and cannot
enter the source-derived observations as a negative or as a completed fact.
An unresolved interpretation family keeps its alternatives without asserting
each alternative simultaneously. Alternatives referring to different
occurrences are rejected as a family.

The generic `Observation` constructor represents externally supplied judgments.
It remains deliberately separate from source admission: caller-created
observations, ledgers, records, or receipts are not source certificates.
Source-derived callers must use `pilot.to_observation` or
`pilot.observations`. Neither the adapter nor the learner issues a proof rank
or a claim of grammatical truth.

## Finite learner and revisions

For `n` declared Boolean predicates and maximum conjunction degree `d`, the
hypothesis language contains both constants and every signed conjunction of
up to `d` predicates. Its size is

```text
2 + sum(comb(n, j) * 2**j for j in range(1, d + 1))
```

A guard code is interpreted relative to its feature schema and width. Each
base-three digit means omitted, positive, or negative; explicit false has
code `3**n`. Schemas carry a domain, version and ordered predicate names.
Their fingerprints preserve identity without authenticating the named
property meanings.

The degree-one observational run retains **8 → 4 → 2 → 1** hypotheses.
Its surviving selector is `cue_is_hadha`, code 1. The second example removes
the constant-true candidate. This result is conditional on the declared
degree-one language and the fixed source projection. Allowing degree three
retains five rules on the same data, demonstrating that a single survivor in
the smaller language does not identify a universal grammar.

All consistent alternatives remain available. Only completely interpreted,
explicitly labelled observations constrain the current implementation;
partial observations remain named in `pending`. Predictions also range over
all completions of missing query features. The outcomes are:

| Status | Meaning |
| --- | --- |
| `conditional_consensus` | All surviving guards and missing-feature completions agree |
| `underdetermined` | At least two such possibilities disagree |
| `exhausted_declared_grammar` | No rule remains in the declared language; the reason distinguishes conflicting labels, feature collisions and an insufficient rule language |

An empty hypothesis space never produces vacuous consensus. Evidence
correction or withdrawal rebuilds the version space from the original full
language and leaves the old immutable session intact. Withdrawing the third
source observation changes the survivor count from one to two; replaying it
restores one and the original evidence revision digest. Changed feature
interpretations require a new analysis identity.

There are explicit ceilings on source bytes, hypothesis count, observation
count, learning checks, query cases, query checks and family size. Observation
and family iterables are bounded before complete materialization. Exceeding
an execution ceiling raises NABT's structured `RESOURCE_LIMIT` with status
`DEFER`; it does not refute an observation or exhaust the linguistic grammar.
Malformed domain values are rejected separately, including Python booleans
where natural-number masks or codes are required.

## Application conditions and evidence arithmetic

`application_assessment` tracks the selected four-condition fragment:
`idafa`, `not_first_person_ya`, `companionship`, and `mim_absent`.
Bare noun strings do not establish these properties. The six listed noun
forms therefore remain pending with named missing conditions. The adapter
also preserves qasr/naqs alternatives, the preference concerning **هن**, and
the relative-pronoun interpretation of **ذو**. Caller-supplied names can add
alternatives but cannot remove those retained by the source policy.

Nominality, singularity, non-diminutive form, requested case and full semantic
disambiguation are not established by this fragment. An unknown noun returns
`no_matching_rule` and no license decision. The arithmetically true empty
requirement mask cannot make a failed rule lookup succeed.

The generic evidence ledger retains positive and negative masks separately.
A required atom with both witnesses is a conflict; a required negative-only
atom rejects; an unknown required atom leaves the decision pending. Only
complete positive, nonconflicting support licenses the conjunction. Conflict
outside the required set remains recorded without deciding this particular
claim. Supplying a bit mask is a mathematical premise, not a checked witness
for arbitrary source semantics.

## Formal scope and executable checks

`formal/Nabt/RuleLearning.lean` supplies 12 general Lean theorems about its
abstract finite-list learner: exact surviving membership, unknown identity,
monotonic filtering, elimination, conditional true-model survival, nonempty
consensus, conditional consensus correctness and strict progress from a
distinguishing observation.

`formal/Nabt/PropertyEvidence.lean` supplies 20 theorems about exact replayed
record admission, nontransferable binding and labels, readiness, unknown
labels, finite-ledger judgments, absent rule lookup, and numeric mask bits.
It assumes an expected record has been supplied by a reader. It does not
prove the authenticity of that reader, source authority, SHA-256 collision
freedom, or an Arabic interpretation.

`formal/PropertyEvidenceTable.lean` exports all 4,096 combinations of required,
positive and negative masks at width four using finite predicates.
`tools/check_property_evidence_table.py` compares this independent specification
with the Python bit implementation. The checked table contains 1,695 conflict,
1,105 rejected, 671 pending and 625 licensed states, with zero mismatches.
Its SHA-256 is
`4d6454114d2949a02c16fda44dbef2352a68531e6f0f7c6b4debb3a40eee2db6`.
This finite comparison is separate from the general Lean theorems and does not
constitute a universal Python refinement proof.

```sh
PYTHONPATH=src python3 -m unittest tests.test_source_learning -v
python3 tools/source_learning_experiment.py
python3 tools/check_property_evidence_table.py --lake lake
```

The independent tests include set-based ledger reasoning, signed-feature
truth oracles, all small-domain feature completions, source-span fixtures,
forged labels and bindings, unknown states, ambiguity, schema collisions,
evidence withdrawal, resource deferral and isolated archive-resource loading.
The experiment reports actual source records and bounded learning behavior;
it does not report general Arabic accuracy or independent test-set coverage.
