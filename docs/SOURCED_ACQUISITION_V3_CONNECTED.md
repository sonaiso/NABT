# Sourced citation and bounded connected realization — v3

Status: source/specification freeze candidate; no v3 runtime has been written.
Law: `nabt.sourced-acquisition.v3`; alphabet: `nabt.a116.v1`.
Source packet: `evidence/sourced_acquisition_v3/source_evidence.json`.
This is an additive finite representation law. V1/v2 implementations, laws,
evidence, and frozen matrices are unchanged. The v3 law does not assert general
Arabic phonology, an acoustic observation, lexical completeness, actual speaker
intention, syntactic correctness, or truth in the world.

## Source basis and authored reading conventions

The retained Sibawayhi text establishes deletion of hamzat-wasl after preceding
speech and retention after an actual break/restart (physical lines 17575–17581).
Its article examples and initial fatha occur at 17540–17553. Lines 21531–21540
describe definite-article lam assimilation and explicitly name الرجل. The same
source separately treats sukun/tanwin contact repairs at 17595–17603 and
long-vowel deletion at 17643–17650. Those latter rules are boundaries of this
implementation, not silently omitted transformations.

The source packet pins original bytes and exact excerpts. It includes Qatr,
Sibawayhi, Mukhtar al-Sihah, Sabban and Ibn Aqil witnesses for the finite reading
profiles below, and the retained natural-lexicon excerpts for عين/جارية/باصرة.
Exact marked templates, case variants, U+0671 spellings and the small set of
partially marked aliases are **authored representation conventions**. They are
not presented as fully vocalized verbatim quotations from those sources.

The packet has 34 canonical representation readings and 151 exact input
surfaces. These are finite spelling/representation witnesses, not 34 senses,
151 independent linguistic observations, or a productive article grammar.
An installed input spelling must match exactly one canonical representation;
multiple distinct representations for the same input cause DEFER rather than
an arbitrary selection. Semantic alternatives with the same pronunciation
remain the responsibility of the downstream lexical reader.

| Canonical family | Installed canonical forms | Scope |
|---|---|---|
| HAQQ, QAWM, GHULAM | الْحَقُّ/الْحَقَّ/الْحَقِّ; الْقَوْمُ/َ/ِ; الْغُلَامُ/َ/ِ | Existing v2 finite moon readings |
| RAJUL | الرَّجُلُ/َ/ِ | Only new sun-article family; bare written lam, explicit ra shadda+fatha |
| WALAD | الْوَلَدُ/َ/ِ | Pronunciation profile; one/collective lexical alternatives remain unresolved |
| WALAD_DUAL | الْوَلَدَانِ | One finite nominative dual representation |
| AWLAD | الْأَوْلَادُ/َ/ِ | Finite broken-plural form; internal written hamza is retained |
| AYN, JARIYA, BASIRA | الْعَيْنُ/َ/ِ; الْجَارِيَةُ/َ/ِ; الْبَاصِرَةُ/َ/ِ | Pronunciation only; no choice among eye/spring/gold or other senses |
| QUMT | قُمْتُ; قُمْتَ; قُمْتِ | Three distinct explicitly ended readings |
| DHAHIB | ذَاهِبٌ; ذَاهِبَانِ; ذَاهِبُونَ | Three finite nominative forms, not a general inflector |

For each article canonical form, the initial source piece may be exactly ا,
اَ, ٱ, or ٱَ. One shadda plus its vowel may appear in either raw order in HAQQ
and RAJUL; neither normalization nor duplicate collapse is performed. Moon
forms require the explicit lam sukun in these full spellings; RAJUL requires
bare lam. All other canonical marks are exact. The packet lists all surfaces
literally; its list, not a general missing-mark rule, defines the registry.

These nine partial aliases alone are additionally installed:

| Exact source | Canonical representation |
|---|---|
| قمتُ | قُمْتُ |
| قمتَ | قُمْتَ |
| قمتِ | قُمْتِ |
| الولدُ | الْوَلَدُ |
| الولدانِ | الْوَلَدَانِ |
| الأولادُ | الْأَوْلَادُ |
| ذاهبٌ | ذَاهِبٌ |
| ذاهبانِ | ذَاهِبَانِ |
| ذاهبونَ | ذَاهِبُونَ |

The original grapheme carriers align one-for-one with each canonical template;
only the explicitly installed interpretation supplies the absent marks. The
stored source is never replaced by the canonical text. Every supplied mark and
cell cites the original source piece, reading ID, and supporting passage IDs.
An unlisted partial spelling, such as الولد or قمت, is not filled by analogy.
Unknown article-shaped words remain deferred even when a local cell parser
could otherwise assign their characters a shape. Fully marked nonarticle words
continue to use the unchanged v1 local representation rules; that does not
grant them lexical attestation or a semantic reading.

## Request and public API

Module: `tools/connected_acquisition_v3.py`.

```python
propose_acquisition(text, *, source_id="input", revision="1", scope="default",
                    ending="wasl", onset="word_initial")
acquire(text, *, source_id="input", revision="1", scope="default",
        ending="wasl", onset="word_initial")
citation_acquire(text, *, source_id="input", revision="1", scope="default",
                 ending="wasl")  # acquire(..., onset="word_initial")
read_acquired(text, *, source_id="input", revision="1", scope="default",
              ending="wasl", onset="word_initial")
verify_acquired_reading(report, text, *, source_id="input", revision="1",
                        scope="default", ending="wasl", onset="word_initial")
source_inventory()
```

`text` may be exact UTF-8 bytes or a string as in v1. Native requests explicitly
contain exactly `text`, `source_id`, `revision`, `scope`, `ending`, `onset`.
Onset is `word_initial` or `connected`; ending is independently `wasl` or
`waqf`. No caller-supplied lexical match, certificate, registry, Boolean or hash
may select a reading or confer authority. Independent expected metadata is
required when verifying an external receipt. Byte/type/JSON/duplicate-field
checks and resource failures remain distinct from linguistic judgments.

Budget: at most 8192 source bytes, 4096 Unicode scalars, 32 source words,
4096 emitted phrase cells, 8 MiB complete response. Existing stricter reader
budgets remain separately visible. Overflow is `RESOURCE_EXHAUSTED` with no
complete reading/shape authority. A complete response is never truncated.

## Citation acquisition is distinct from connected realization

First partition the **original** source using the v1 exact piece/word grouping.
Preserve all original raw spans, byte offsets, scalar offsets and boundary
pieces. Malformed marks retain `INVALID_INPUT` precedence. Original whole-word
orthographic/silent-letter debts are not bypassed by a partial match.

For an exact finite match, compute the canonical local representation with the
same carrier/mark/long-vowel/tanwin/pausal rules as v1. Article onset at citation
is hamza+fatha, A116 `[112]`. Moon lam contributes lam+sukun. In RAJUL, the raw
lam is retained as a licensed, explicitly assimilated empty realization; the
explicit ra shadda contributes ra+sukun then ra+fatha. Do not retain a lam cell
or add a third ra. Each supplied piece must retain its corresponding original
span; any carrier-count/alignment discrepancy causes DEFER.

Ending affects only the last source word; every earlier word uses wasl ending.
For `word_initial`, each word starts separately, including inside multiword
text. The v1 boundary policy is retained: spaces and punctuation remain source
boundary pieces. This mode is not uninterrupted pronunciation.

For `connected`, the first word starts initially. A one-word request is valid
and has no elision. Multiword source must consist of nonempty words separated
by **exactly one ASCII space**, without leading/trailing spaces, punctuation,
tab, newline, doubled space, or an implicit external predecessor. These other
boundaries return `DEFER/BOUNDARY_CONTINUITY_UNLICENSED`, preserving all bytes.
Punctuation is not guessed to be a pause or silently removed. A caller chooses
the declared continuous-reading profile; the program does not prove that a
human actually spoke continuously.

Every internal join in this first profile additionally requires the preceding
word's original final piece to carry exactly one ordinary short vowel
(fatha/damma/kasra), not tanwin, sukun, or a following long-vowel carrier. Its
complete citation acquisition must end in the corresponding short-vowel cell.
Shadda plus one short vowel is allowed. The guard is checked from the original
piece and replayed cells, not from a supplied `vowel_final` flag. Otherwise
return `DEFER/CONTACT_REPAIR_NOT_IMPLEMENTED` for this realization. This
conservative join restriction also applies before ordinary nonarticle words;
it avoids claiming unimplemented general cross-word sandhi.

At a guarded join into an installed article, delete **only** the article's
initial citation hamza+fatha cell. The alif/wasla source piece remains present
with a licensed empty realization and rule `ARTICLE_WASL_ELISION`. Moon lam
remains; RAJUL retains its already assimilated ra pair. All internal qat'
hamzas, including the hamza in الْأَوْلَادُ, remain. For a nonarticle next word,
the onset is unchanged. Productive clitic prefixes, generic wasl verbs/nouns,
unlisted sun words, interrogative exceptions, sukun/tanwin contact vowels and
long-vowel deletion are outside this law and cannot be inferred from a prefix.

## Stable report projection and downstream gates

`acquire` returns schema `nabt.checked-acquisition.v3`; `read_acquired` returns
`nabt.acquired-reading.v3`. Both retain top-level `law_id`, `alphabet_id`,
`onset`, `status`, `verified`, `authority`, `acquisition`, `realization`.

* `acquisition.text/source_id/revision/scope/ending/onset` binds the exact request.
* `acquisition.pieces` retain v2-style `raw/start/end/byte_start/byte_end`,
  status/rule/cells. Their cells describe the **citation** representation.
  Finite matches also expose their representation reading and passage IDs.
* `acquisition.words[N].cells` remains citation/local cells; source word spans
  are unchanged. `acquisition.status` describes this layer alone.
* `realization.mode` equals the onset policy. `realization.status` is
  `REALIZED`, `DEFER`, or `INVALID_INPUT`. `realization.words[N].cells` holds
  the actually selected citation/connected representation with the same source
  word span. A deferred word has no complete realized cell authority.
* `realization.pieces` contains every original source piece in order, including
  boundaries and elided pieces, with original span, realized cells, rule, and
  phrase cell interval. Empty intervals explicitly record boundary/elision;
  they never erase source identity. Citation mode has no phrase interval claim.
* `realization.joins` identifies adjacent source word indices, exact separator
  span, guard status, and any article elision. It records `CITATION_BOUNDARY`
  in word_initial mode and `JOINED` or `DEFER` in connected mode.
* `realization.phrase_cells` is the flattened complete connected realization
  only when connected and `REALIZED`; otherwise it is `[]`. An incomplete
  prefix is not promoted to a whole-source phrase.

`acquire.status == ACQUIRED` means native-replayed source acquisition and
realization are complete; it does not yet mean the shape machine accepts.
`read_acquired` adds `shape_verified`, `shape_handoffs`, and `phrase_shape`.
In word_initial mode, it checks each complete citation word from q0 using the
unchanged shape law and the correct ending. In connected mode it checks
**one whole phrase from q0**, with final ending, and sets `phrase_shape`.
It never issues a standalone q0 certificate for an elided-onset word.
Citation mode `phrase_shape` is null; connected mode `shape_handoffs` is empty.

For `read_acquired`, top `status == ACQUIRED` requires all required shape
checks to pass. A complete representation with rejected shape is
`SHAPE_REJECTED`, not Arabic linguistic rejection. Scope debt is `DEFER`.
`shape_verified` is true only after exact native replay and verification of
all required shape certificates. The safe gate on a freshly computed report
is `status == "ACQUIRED" and verified is True and shape_verified is True`.
Externally supplied reports require `verify_acquired_reading`, which recomputes
from independent exact input/binding and compares the entire typed JSON tree.
Caller flags, nested certificate names, or a matching hash alone never pass.

Shape licenses belong to a sound-shape law, not to lexical identity or syntax.
Raw source, citation cells, connected cells, lexical analyses and later semantic
evidence are separate objects. Downstream person/nominal/natural readers receive
the original bytes and offsets, never a rewritten canonical transcription.
They may report their narrower success while this acquisition remains DEFER;
such an answer is not a completed acquisition-to-meaning chain.

## Native contract and proof obligations

Owned implementation targets, after independent freeze:
`formal/Nabt/ConnectedAcquisitionV3.lean`,
`formal/ConnectedAcquisitionV3Main.lean`, and
`tools/connected_acquisition_v3.py` with corresponding focused tests.
The coordinator registers imports, lake targets, Audit and theorem manifests;
those shared files are not independently edited by this component owner.

The native implementation independently replays original-source partition,
finite-template selection, canonical-to-original span mapping, local endings,
boundary guards and the connected projection. Python is a proposer. The
installed source packet and original source bytes are pinned and replayed;
missing native/source authority fails closed. Runtime may reuse unchanged
local functions, but no v1/v2 success flag proves the new law.

Meaningful Lean obligations are: original span/order/contiguity preservation;
whole-source restoration; request/onset/ending binding; finite witness
necessity for a changed article or alias; no unsupported prefix license;
source piece retained after empty realization; initial hamza retained; guarded
later article hamza removed exactly once; sun lam empty with exactly the
existing ra pair; other cells preserved; incomplete joins block a phrase;
whole-phrase handoff implies complete sourceful realization and the unchanged
machine's license. Standard axiom policy applies. No formal theorem claims
the citations prove the authored interpretation, Python refinement, JSON or
compiler correctness, acoustic accuracy, all Arabic, or external truth.

## Independent freeze and evaluation

Freeze this spec and the source packet before new runtime. The independent
matrix author may read this law, packet, A116 alphabet, existing laws and source
passages, but not the new implementation. Implementers do not inspect gold
rows. Freeze exact code/native binaries before the first evaluator execution;
preserve preflight/first-run failures and later repairs rather than relabeling.

The stable matrix entrypoint is `read_acquired`. Suitable exact expectations
are `/status`, `/verified`, `/shape_verified`,
`/acquisition/words/N/cells`, `/realization/words/N/cells`,
`/realization/phrase_cells`, and `/phrase_shape/status`. Independently author
literal A116 arrays rather than importing the proposer. Include initial versus
connected article, first-word retention, one-word connected, each finite family,
sun assimilation without double counting, internal qat' preservation, explicit
short-vowel contact versus tanwin/sukun/long-vowel debt, pause endings, exact
partial alias versus unlisted missing marks, raw order, malformed precedence,
separator contrasts and source/identity/onset/ending receipt mutations.

Keep phonological success, per-word identity, person/nominal analysis, lexical
sense alternatives and full-chain success as separate metrics. A correct DEFER
on a required positive remains a coverage miss; a declared unsupported negative
is not counted as a successful Arabic reading. Do not combine v1/v2 replay
counts, source excerpt counts, finite spellings and independent case counts.
