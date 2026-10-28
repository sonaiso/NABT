# Productive clause source lifecycle v1

Status: preimplementation adapter specification. Baseline:
`c2c072e17802b62c13109cee7c087b7b58895a1a` (PR58).
This document supplements `EVIDENCE_LIFECYCLE_V1_SPEC.md`; it changes neither
the installed productive language nor the historical acquisition readers.

## Authority and exact dependency scope

The adapter law is `nabt.productive-clause-lifecycle.v1`. It qualifies the
existing `nabt.acquired-productive-clause.v1` result using the independently
checked dependency readiness of `nabt.evidence-lifecycle.v1`. It does not use
an epistemic SUPPORTED verdict as a grammar license.

Python reopens and checks the COMPLETE retained files, pinned packets and
original byte/line slices through the existing source inventories. Lean checks
the finite projection and source dependency transitions. The Lean source
values below contain descriptors and quotation records, not the full books;
the native law does not authenticate the filesystem, verify SHA-256 collision
freedom, or prove that the authored source interpretation is historically true.
No descriptor, digest, citation, graph, ready list or verification flag supplied
by the caller can replace these local checks.

The graph includes the union of all seven retained sources and all thirty
passages of acquisition v3, all eight productive passages, both source packets,
and the three upstream packet dependencies checked by acquisition v3. This
conservative scope mirrors current source availability checks. It is not
selected by sentence tokens, expected labels, or which example is being tested.
In particular, an unused entry in the installed packet remains a dependency.

The productive qatr and sibawayhi sources are merged with the acquisition
entries only after equality of source ID, canonical repository path, full-file
byte length and full-file SHA-256. A mismatch fails source replay. Multiple
quotations from one book retain that common parent; they do not become
independent observations by receiving different passage IDs.

## Public API and events

The additive Python API is:

```text
evaluate_clause(text, *, source_id="input", revision="1", scope="default",
                ending="wasl", onset="word_initial", events=[])
verify_clause(report, *, text, source_id, revision, scope, ending, onset, events)
installed_targets()
```

The usual raw str/UTF-8 bytes and metadata validation is the existing productive
reader's contract. The adapter's serialized episode and source values must also
satisfy lifecycle limits; exceeding a bound is resource exhaustion, not a new
linguistic rejection. `verify_clause` has no default expected binding or events.
`installed_targets` replays the installed source inventories before returning
the exact target IDs and immutable descriptors; it accepts no source path.

Each event has exactly `{event_id, kind, target, reason}`. `kind` is `withdraw`
or `activate`; event IDs are unique and the lifecycle text and count bounds
apply. `target` must be one of the fifty installed source targets below.
The adapter resolves it to the exact complete Source and constructs the native
update `{event_id,kind,source,replacement:null,reason}`. Input, query and derived
row nodes are not caller-addressable targets. `replace`, unknown targets,
extra fields, duplicate IDs, malformed types and caller-supplied sources or
graphs are INVALID_INPUT. No event changes a retained repository file.

Withdraw/activate have the idempotent behavior of the lifecycle law. Replacing
a book, passage or interpretation requires a newly reviewed installed version;
this API cannot inject a replacement using a matching name or caller digest.

## Canonical source values and order

`wire` means UTF-8 JSON with sorted object keys, compact separators,
`ensure_ascii=False`, `allow_nan=False`, strict JSON types and no normalization.
`H` means SHA-256 of exact UTF-8 bytes, computed by the adapter.
Every source is the existing `{identity,revision,content}` structure.
Every origin ID is `origin:` followed by that source's identity. The following
order is normative for sources, origins and bindings, and for ancestry lists.

1. Seven retained source targets in acquisition packet order:
   `sibawayhi`, `qatr`, `mukhtar_sihah`, `sabban`, `ibn_aqil`,
   `linguistic_inventory`, `maqayis`.
2. Three upstream dependency targets in the order in the table below.
3. `input:productive-clause-v1`, then `query:productive-clause-v1`.
4. Thirty `acquisition-passage:<id>` targets, in the order below.
5. Eight `productive-passage:<id>` targets, in the order below.
6. `packet:sourced-acquisition-v3`, then `packet:productive-clause-v1`.
7. `derived:productive-clause-v1`.

This is exactly 53 origins/bindings and initially active Sources. The fifty
installed targets are all of them except input, query and derived. Sources
remain in this order initially; later active order follows the lifecycle
remove/append rules exactly.

| Source class | revision | content before `wire` |
|---|---|---|
| Seven retained files | pinned full-file SHA-256 | `{kind:"retained_source_descriptor",path,bytes,sha256}` |
| Three upstream files | pinned SHA-256 from acquisition packet | `{kind:"upstream_packet_descriptor",path,bytes,sha256}` |
| Two source packets | installed packet SHA-256 | `{kind:"source_packet_descriptor",law_id,path,bytes,sha256}` |
| Each passage | pinned `span_sha256` | `{kind:"passage_quotation",source_id,source_revision,byte_start,byte_end,line_start,line_end,raw_text}` |
| Input | `H(content)` | `{kind:"raw_clause_request",text,source_id,revision,scope,ending,onset}` |
| Query | `H(content)` | `{kind:"dependency_query",adapter_law_id:"nabt.productive-clause-lifecycle.v1"}` |
| Derived row | `H(content)` | `{kind:"clause_dependency",adapter_law_id:"nabt.productive-clause-lifecycle.v1",clause_law_id:"nabt.acquired-productive-clause.v1",syntax_law_id:"nabt.productive-clause.v1",input_revision}` |

For descriptors, `bytes` and `sha256` describe the full reopened file, not a
serialized excerpt. Paths, hashes and lengths come from pinned installed
packets and are checked against local bytes. For upstream files, byte length
is obtained from the completely reopened bounded file after its pinned hash
matches. For passages, `source_id` is the retained parent target, and
`source_revision` is that file's full hash. Byte offsets are zero-based and
end-exclusive; line numbers are one-based and end-inclusive, as in the source
packets. `raw_text` is decoded from that exact file slice and must also equal
the packet's quotation. No success flags appear in these source values.

The packet paths and pins are:

| Target | Path | SHA-256 |
|---|---|---|
| `packet:sourced-acquisition-v3` | `evidence/sourced_acquisition_v3/source_evidence.json` | `64d6d40943ed59a34d16a58de92e11f8672cbdc7ed47ec15f4e341d07594e423` |
| `packet:productive-clause-v1` | `evidence/productive_clause_v1/source_scope.json` | `eb3a1d93730c4a402bce2561afb8934d1f76853ca31fe8ad1167c33ed08d4f17` |
| `dependency:aligned-acquisition-v1` | `evidence/aligned_acquisition_v1/source_evidence.json` | `269f1aa66756aefc6277e5ff0ef4922dc9ad13fdd2a7bab5e9347649c1fa3cc5` |
| `dependency:article-acquisition-v2` | `evidence/article_acquisition_v2/source_evidence.json` | `d5d348e17fd3f34eaa69e5a031956972860dd8dbf3eee25674a265ee4578543c` |
| `dependency:natural-sources-v3` | `evidence/sourced_acquisition_v3/natural_sources.json` | `f96689c943b06155f8e91a10fabf7b94ac9ae34200a8682ffa086aad604db7f6` |

The ordered acquisition passage suffixes are:

```text
qatr_wasl_fatha
sibawayhi_article_initial_fatha
sibawayhi_connected_restart
sibawayhi_sukun_contact
sibawayhi_long_vowel_contact
sibawayhi_article_sun
sibawayhi_article_lam_shown
sibawayhi_haqq_article
mukhtar_labis_counterexample
mukhtar_laib_counterexample
qatr_case_marks
qatr_weak_imperative
mukhtar_haqq
mukhtar_ghulam
mukhtar_qawm
mukhtar_laqiya
mukhtar_walad_and_awlad
sibawayhi_awlad_occurrence
qatr_dual_plural_endings
qatr_qumt_pronoun
sabban_ta_person
ibn_aqil_dhahib
natural_eye_senses
natural_eye_definition
natural_spring_definition
qatr_nominal_frame
ibn_aqil_fronting
ibn_aqil_fronting_restrictions
ibn_aqil_descriptor_dispute
ibn_aqil_predicate_agreement
```

The ordered productive passage suffixes are `QATR_CASE`, `QATR_PROPER_NAMES`,
`QATR_AGENT`, `QATR_PATIENT`, `SIB_TRANSITIVE`, `SIB_ZAYD_AMR_ORDER`,
`SIB_NAME_EXAMPLES`, `SIB_PROPER_NAMES`. Their source mappings, contents and
coordinates are all eight rows of the pinned productive scope, without
selection by input or result. Every listed ID must occur exactly once in its
packet; unexpected, duplicate or missing source/passage rows fail replay.

## Graph and native episode projection

| Origin class | Rank | Ordered parents |
|---|---:|---|
| Retained files, upstream files, input, query | 0 | empty |
| Each acquisition/productive passage | 1 | its retained file origin |
| Acquisition packet | 2 | all thirty acquisition passage origins, then the three upstream origins |
| Productive packet | 2 | all eight productive passage origins |
| Derived row | 3 | input origin, acquisition packet origin, productive packet origin |

The bindings use the exact Source associated with each origin. This graph
records the adapter's installed computational dependencies; it does not claim
that the authors of the books had no other sources. All graph nodes except the
query are ancestors of the derived row. Its normative ancestry list contains
these 52 origin IDs in the source order above. Repeated book parents are not
duplicated in the ancestry list.

The existing EM query key is fixed except for its input-bound context:

```text
axis="recorded_observation"
entity="productive-clause-input"
predicate="installed-clause-dependency"
value="ready"
unit="not-applicable"
context=<input Source revision>
time="0"
place="not-applicable"
```

This is a synthetic diagnostic key, not a statement of a physical event.
The query has `positive=true` and `origin="origin:query:productive-clause-v1"`.
There is exactly one interpretation:

```text
id="productive-clause-dependency"
source=<derived Source>
key=<the same diagnostic key>
positive=true
kind="grammar"
origin="origin:derived:productive-clause-v1"
ancestry=<the ordered 52 origins>
```

The episode schema is `nabt.evidence-lifecycle.episode.v1`; its budget is 1.
Its `episode_id` is `productive-clause:` followed by `H(wire({request,events}))`,
where request is the six ordinary fields after strict raw input decoding and
events are the exact validated public event list. Its initial active sources,
origins and bindings are the complete ordered projection above. Updates are
resolved from targets as specified earlier. The episode contains no clause
verdict, gold label, native success flag or caller-supplied ancestry.

At every valid step, the EM receipt must be UNKNOWN with empty support,
refutation and selected lists: `kind=grammar` is inadmissible as an observation.
Dependency readiness is separately `['productive-clause-dependency']` exactly
when all 52 ancestor Source values are active, and empty otherwise. The blocked
list is its complement within the singleton interpretation ledger. Step 0 is
ready and has empty affected IDs. Each later affected list is the lifecycle
symmetric difference, so repeated withdrawal and partial reactivation are
not automatically counted as changes. No caller field is used to infer this.

## Composite report and current-chain rules

The report schema is `nabt.productive-clause-lifecycle-result.v1`. It retains:

- The exact validated `request` and `events`.
- `source_replay`, with ordered file descriptors and complete passage quotation
  records above, produced only after reopening the files and verifying slices.
- `original_clause`: the entire fresh, unchanged output of the installed
  productive reader, including acquisition, shapes, source evidence, nine
  gates and native syntax response. "Original" means the installed reader's
  result before this episode's virtual withdrawals, not a caller receipt.
- `lifecycle`: the complete newly replayed lifecycle result and its episode.
- `chain_history`: one row per native step, each containing `step`, `event_id`,
  `dependency_ready`, `chain_complete`, `status`, `blocked_by`, and
  `candidate_space`. This is a projection of every checked episode step,
  evaluated against the same original-source clause replay.
- Root `status`, `verified`, `chain_complete`, `reading`, `candidate_space`,
  `blocked_by`, and `current_step`, reflecting only the last checked step.
- `run_identity`: locally measured source-code and native identities, including
  the lifecycle checker and the existing clause verification dependencies.
  These are execution bindings, not origin nodes or caller trust premises.
- `world_truth_established=false`, `referents_established=false`,
  `entails_exclusivity=false`, and `all_arabic_complete=false`.

A current complete chain requires a successful whole lifecycle replay, exact
episode binding, the grammar row in the final dependency-ready list, AND the
existing reader's complete chain with all nine gates. Root `verified` is true
only in that case; readiness by itself cannot set it. The root reading is the
exact original reading only when current chain_complete is true, otherwise null.

If the original status is LICENSED_CLAUSE OR REJECTED_IN_SCOPE and the dependency
row is blocked, root and corresponding history status are
`PENDING_DEPENDENCIES`, with `SOURCE_DEPENDENCY_NOT_READY` in blocked_by.
Neither a licensed reading nor a scoped rejection remains a current judgment
after its required source is withdrawn. Keep the unchanged original status and
native receipt inside original_clause.

For an original licensed reading, retain its syntactic candidate ID, count,
count mode and Hartley value, but set the candidate's state to PENDING and add
the same dependency obligation. For an original scoped rejection, its checked
count 0, EXACT count mode, empty candidate list and null Hartley value may remain
in candidate_space ONLY as the conditional `installed_finite_grammar` structural
diagnostic. They do not authorize a current rejection or prove absence of an
Arabic reading. A blocked rejection has verified=false, chain_complete=false
and reading=null, just as a blocked licensed reading does.

When all dependencies are ready again, an original licensed clause returns to
LICENSED_CLAUSE with a LICENSED candidate and complete chain. An original scoped
rejection returns to REJECTED_IN_SCOPE, retaining verified=false,
chain_complete=false and reading=null. Readiness never promotes that rejection
to a licensed clause. UNKNOWN/DEFER, invalid-input, verification-failure and
resource outcomes remain distinct; do not replace them with a scoped rejection
or derive negation from missing support. Unknown/out-of-scope counts remain
null. This does not regenerate a general semantic candidate space after a
withdrawal.

Invalid public input/events produce INVALID_INPUT without accepted history.
Unavailable or mismatched retained evidence produces SOURCE_EVIDENCE_UNAVAILABLE;
the graph is not constructed from the caller's account of missing files.
Unverified lifecycle execution produces no accepted current chain/history and
preserves its explicit failure/resource outcome. If a checked original syntax
diagnostic remains available on such a failure, its candidate can remain pending
with the failed dependency obligation; it cannot become a current reading.
Resource exhaustion cannot be replaced by a linguistic rejection or a zero
candidate count. Unsupported original clauses retain their original outcomes.

All code/native identities are collected from installed fixed paths and checked
for changes across the run. Execution freezes additionally use the established
validated-byte import boundary; these checks are not a claim of atomic isolation
against a concurrent adversarial writer.

## Whole-receipt verification and independent tests

`verify_clause` decodes a bounded, strict typed receipt, separately validates
the expected raw text, all five ordinary binding fields and the complete event
list, then freshly reopens sources, reruns the original clause reader and
reruns the lifecycle native checker. It compares the ENTIRE canonical composite
report, including the original clause receipt, complete native episode and all
history steps. Booleans must not compare equal to numeric indices or counts.

The returned verification has `replay_matches` separate from `valid`:
an exact historical or suspended receipt may replay, but `valid` is true only
for an exact replay whose final chain_complete is true. An old receipt checked
against a newer event sequence fails whole replay even if its final active
sources, witness IDs and verdict happen to match. Verification never derives
the expected current episode from the submitted receipt itself.

Before implementation, independent connection tests can derive the complete
53-node graph from these frozen sources. Required controls include both VSO/VOS,
unknown and rejected clauses, all fifty single-target withdrawals/reactivations,
an explicitly rejected clause followed by withdrawal and restoration
(REJECTED_IN_SCOPE -> PENDING_DEPENDENCIES -> REJECTED_IN_SCOPE, with no licensed
reading at any step and the original conditional count 0 preserved),
two simultaneous inactive targets and partial reactivation, idempotent events,
changed input binding, stale history with restored final state, changed native
output, modified source bytes/positions, missing source files and malformed
receipt types. These are adapter boundary tests, separate from the forty
authored epistemic scenarios and from the two hundred productive clause cases.

No historical sources, gold cases, readers or result archives are rewritten by
this adapter. General source onboarding, replacement of installed books,
semantic candidate regeneration and external-world reference remain open.
