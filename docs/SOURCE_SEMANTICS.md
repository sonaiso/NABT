# Classical sources and semantic contracts

This change adds four source-specific Lean modules and a native checker for
semantic contracts at the free-reader boundary. It does **not** close the
proof of unrestricted Arabic reading, complete any of the four books, or
establish that a reported event happened in the world.

## Source coverage

`evidence/source_semantics/passages.json` retains six exact byte passages,
full-edition hashes, edition metadata, revision, and byte offsets. Existing
source files and historical measurement reports are unchanged.

| Lean module | Selected source content | Conditions and exclusions |
|---|---|---|
| `SibawayhiRules` | Kitab lines 111–138, 234–239: case domains and the two sides of predication | Version 2 requires independent noun/present-verb AND overt-primary-ending qualification before inverting a mark. Unqualified marks retain every class-appropriate case; substitute and estimated endings are not excluded by the class alone. |
| `QatrRules` | Matn Qatr al-Nada lines 55–96: past attachments, present building, five-verb nun, diptote genitive exceptions | Direct emphasis is required; an ordinary present verb is not declared built. Diptote and attachment classification are explicit premises. This is the matn, not its commentary. |
| `AwamilRules` | Retained Dar al-Minhaj 2009 transcription, pp. 40–41: 91/7/2 partition and two ba meanings | The original rule module models only this excerpt. The later `AwamilInventory` adds 100 numbered entries, without completing their application conditions. Attribution, transcription and variant readings are not authenticated by Lean. The two ba senses do not exhaust ba. |
| `MaqayisRules` | Entry علم, lines 27039–27065: five selected glosses | The list is partial. A common root does not choose an occurrence's meaning. A selection is bound to source, revision, offset and spelling. |

The native `source_rule` operation verifies the quote against an independently
opened file and checks that the selected law belongs to that work. Python
additionally checks the whole file hash against the installed catalog. Changing
a byte outside the quote is therefore detected by edition replay. Hashes pin
a digital artifact; they do not authenticate an attribution or narration chain.

`ruleBound` proves work/occurrence binding, **not the correctness of the authored
interpretation**. The six passages are not six independent speaker samples.
Maqayis is a compilation with declared predecessors; repeated transmission
cannot be counted as independent evidence without checking shared ancestry.

## What the semantic theorems say

`SourceSemantics.lean` provides the following contracts:

- `substitution_preserves_meaning`: simultaneous substitution in an explicit
  binder-free concept formula agrees with substitution in its environment.
  Distinct variable indices are retained. This is not a proof of Arabic
  variable parsing, quantifier scope, or unrestricted recursive definitions.
- `definition_expansion`: a nonrecursive, binder-free definition expands
  compositionally. A definition does not assert a true instance. Unprovided
  substitutions remain variables in the executable adapter.
- `reference_requires_closed_singleton`: resolving a reference requires a
  closed singleton candidate set. The proof does not establish that the
  context's closure declaration is correct about the world.
- `time_restriction_sound`: an interval assertion can be narrowed to a
  nonempty contained interval. `time_cannot_be_erased` supplies a counterexample
  to promoting a bounded statement to all times. Calendar interpretation of
  أمس or a narrative tense is not proved by this abstract interval theorem.
- `consensus_all`: every supplied candidate has the same complete meaning and
  exact source/context/lexicon binding if consensus returns a value. An
  incomplete candidate or changed binding blocks consensus. Completeness of
  the supplied candidate set is **not** an assumption secretly proved here.
- `recursive_evidence_exact`: a recursively joined evidence tree validates
  exactly when every retained leaf is attested in the inventory.
  `recursive_withdrawal_blocks` prevents deleting a cited source while retaining
  a valid tree. This does not prove linguistic correctness of arbitrary
  recursive word formation or the existing free-reader parser.
- `execution_in_world`: the existing verified ground reader's positive result
  holds in a world interpretation **if that interpretation satisfies the
  source's meaning**. This is an explicit semantic-adequacy premise.
  `a_written_fact_needs_world_evidence` exhibits why written assertion alone
  cannot discharge it. No executable `world_truth=true` flag supplies a proof.

The prior controlled ground-reading route remains described separately in
`VERIFIED_READING.md`. Its source-to-inference proof has a stricter grammar than
the free reader. The new contracts do not enlarge that verified grammar.

## Actual free-reader connection

`tools/source_semantics.py` runs the existing free reader from the original
text, training bytes and context, and replays its report. A caller-supplied
report must equal that fresh report. Every viable analysis participates in
native Lean consensus; incomplete rivals are represented by `none`.

The semantic comparison preserves the **entire** claim record: predicate,
arguments, sign, speech force, tense, time, place, and restrictions. Closed
reference candidates are checked by the native singleton rule only when the adapter has the stronger reader premises. Antecedents with unconfirmed gender/number compatibility remain `UNMEASURED`, even in a closed singleton set.
The result reports disagreement instead of rewriting the reader's result.
The source-rule binding results are reported separately from these target
reading contracts: no claim is made that the four newly selected rule tables
now drive every analysis in the existing parser.

The Python projection and free-reader enumeration are still trusted software,
not formally refined to the Lean semantic specification. In particular, the
formula substitution operation is executable and proved, but the free reader
is not proved to translate every Arabic definition into that formula language.
These gaps remain explicit false fields in the output. Passing these checks
is engineering evidence; it is not a new Arabic acquisition score.

## Reproduction and validation

Normal environment:

```sh
make source-semantics-conformance
make verified-reading-conformance
make test
make formal
make conformance
```

Example:

```sh
NABT_CLASSICAL_SEMANTIC_PROBE="$PWD/formal/.lake/build/bin/classicalSemanticProbe" \
  python tools/source_semantics.py examples/discourse.txt \
  --training examples/discourse_training.tsv \
  --context examples/discourse_context.json \
  --output artifacts/local/source-semantics-audit.json
```

The local environment cannot locate the Lake application. The recorded
fallback uses the pinned official Lean 4.34.1 library and its public embedding
entry points, the same kernel, and ordinary Lean-generated C compiled with
GCC. `evidence/source_semantics/build_direct.py` records the complete dependency
build, both native executables, and a fresh law export. It does not report that
Lake succeeded. The driver is retained under
`evidence/verified_reading/environment/main.c`.

Native execution exposed an empty-buffer problem in the shared JSONL adapter.
`ProbeJson.readLoop` now explicitly allocates empty byte buffers with
`ByteArray.emptyWithCapacity 0`. Regression tests cover malformed input,
oversized lines, invalid UTF-8, and recovery for the following request.
No Lean runtime, kernel, generated C, or installed library is patched.

The tests include an independently tabulated rule oracle, all 121 lists of
length 0–4 over two meanings and an incomplete reading, all 81 pairs of
intervals with endpoints -1/0/1, wrong-work binding, byte/offset mutations,
recursive evidence, definition substitution, and free-reader ambiguity,
reference and time cases. These authored finite checks are distinct from
general theorems and from held-out linguistic measurements.

Actual counts, logs and file digests are in
`evidence/source_semantics/VALIDATION.json`. Neither a remote Actions pass nor
a release gate is claimed for unpublished changes.

## Remaining proof obligations

1. A formally checked translation from the free reader's source grammar to
   these semantic structures, with all viable readings preserved.
2. Coverage against a declared, independently annotated witness corpus;
   whole-book inventories and variant/narration provenance must be enumerated
   before a finite completeness claim can even be measured.
3. Independent observational or testimony-adequacy evidence for world claims.
   Textual occurrence, grammatical acceptability, and truth about an external
   event are different propositions.

Unmeasured obligations remain unmeasured. They are not converted to test
failures or successes. Universal Arabic completeness and unconditional world
truth are not justified by these additions.
