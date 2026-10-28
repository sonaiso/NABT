# Independent preimplementation matrix method

The contract and source registry were committed at
`6981674d2162c4b251d79a5a585742171e648725` before this matrix was authored.
The independent author read the frozen v2 contract/registry, declared A116
alphabet, existing v1 acquisition specification, PR34 finite generative grammar,
and existing sound-shape law. No new v2 runtime, native implementation, or
evaluator was read or executed. No producer output supplied expected cells.

Gold schema: `nabt.article-acquisition-gold.v1`.
Gold SHA-256: `a6e61d9dfd999452730753d290d811c483e77aece737409a34ffb776990798d1`.
Source registry SHA-256:
`d5d348e17fd3f34eaa69e5a031956972860dd8dbf3eee25674a265ee4578543c`.

| Family | Cases | Required positive goals |
|---|---:|---:|
| Orthography | 44 | 25 |
| Person/category | 12 | 11 |
| Nominal predication | 12 | 9 |
| Conditional inference | 21 | 12 |

There are 89 cases and 87 independently authored word-array
expectations. Every installed stem has all three explicit terminal vowels under
both endings and a connected-onset contrast under both endings. This is
preimplementation independence over known finite vocabulary, not a fresh
held-out lexicon. Representation and inference expectations are separate.

Cells were derived as literal arrays from `4 * carrier_index + state`; known
word arrays were reused in explicitly authored clause sequences. The authoring
helper assembled literals only: it did not classify source text, normalize
marks, simulate transitions, or call NABT. Final checks tested schema/types,
unique identifiers, cell-domain integers, exact UTF-8 validity, family minimums,
and the word-array count against an independent separator count. Shape and
conditional outcomes were reasoned from the pre-existing declared laws.

Person/category and nominal syntax requirements remain UNMEASURED, and their
required positives remain misses. Supported conditional goals blocked by
connected acquisition or exact PR34 spelling coverage remain misses. Unknown
and conflict results are distinct from unavailable reading. Source/identity,
type/resource, checker availability and receipt mutations belong to separate
boundary tests; they must not inflate the linguistic denominator.

The first execution, including preflight failures, must be retained. Later
repair runs are exposed replay. Do not relabel cases to match production
results or read gold contents during implementation. These expectations do
not certify Arabic completeness, acquired reference, nominal syntax, source
interpretation, or world truth.
