# Source-relative meaning, properties, relations, and inquiry

The executable path is now:

```text
original UTF-8 → controlled reader → scoped signed clauses → two closures
             → query status + replayable proof + checked missing-premise plans
```

`src/nabt/text_ir.py` supplies the inert intermediate representation;
`src/nabt/text_reader.py` reads the language documented in `TEXT_READER.md`;
`src/nabt/semantics.py` performs source admission, inference, proof replay,
revision, and inquiry. No module imports an upstream repository at runtime.

This is an executable reader for a declared Arabic sublanguage. It is not a
general Arabic parser, a dictionary of all Arabic senses, or an oracle for the
truth of the text. The accepted vocabulary is supplied by new source documents;
it is not a list of example words embedded in the engine.

## Meaning and truth are different contracts

An atom records a predicate, an ordered tuple of one or two arguments, and an
explicit sign. Its scope is supplied by its source document. A successful text
reading says what the installed grammar attributes to the statement. Inference
says what follows from the active statements and rules in that scope.

Every query and certificate reports `world_truth: "NOT_ESTABLISHED"`. A user can
declare a fictional individual, a local convention, or an inaccurate assertion;
the reader will not turn successful parsing into independent observation of the
world. Nor does a declaration `فرد ...` establish real existence. It introduces
a name into the local theory's finite vocabulary.

The word *mafhum* has different uses in the upstream sources: inferred meaning
of an utterance, and understanding corroborated by perceived reality. This
engine does not merge those uses. Its rule-derived consequences remain
conditional support from declared sources. It does not promote a text to a
reality-grounded concept because a caller labels the source an observation.

## Definitions and typed relations

`تعريف P هو Q و R` is an explicitly declared equivalence:

\[
P(x)\Rightarrow Q(x),\quad P(x)\Rightarrow R(x),\quad
Q(x)\land R(x)\Rightarrow P(x).
\]

`كل P هو Q` is only the forward implication. Neither form creates an instance
of `P`, and neither supplies a contraposition rule. For example, `¬Q(a)` does
not establish `¬P(a)` without an explicit rule in the source.

Concepts have arity one; relations have arity two with ordered arguments. This
is the implemented relation typing boundary. Domain/range ontologies, automatic
inverse relations, transitivity, symmetry, and causal interpretation are not
assumed. A source may explicitly provide a variable-joining rule for any such
operation. A name used at both arities in one scope is an admission error.

Declarations are optional when the predicate occurs in an explicit fact or
rule position. Repeating the same signature in several sources is allowed.
An unseen predicate or wrong query arity is `OUT_OF_SCOPE`; a new individual
queried against a known predicate is `UNKNOWN` unless an explicit ground rule
or fact supports it.

Names retain their exact spelling. Different scopes isolate equal spellings.
Multiple definitions of one name within the same scope are joint assumptions
of that theory. They are not automatically ranked as competing dictionary
senses. Applications that need distinct senses must give them distinct names
or scopes.

## Source admission and exact restoration

`add_document` does not trust supplied facts, rules, residual flags, hashes, or
reader versions. It reparses `document.source.raw_bytes` with the installed
reader, then checks every active source for compatible scoped signatures and
bounded inventory sizes. Every clause is tied to the exact source identity,
whole-source digest, byte interval, interval digest, component intervals, and
reader analysis identity.

Any residual blocks the entire new source. An unsupported statement returns
`DEFER`; malformed controlled syntax or an incompatible signature returns
`REJECT`. Neither partially admits earlier valid-looking statements from that
source. An existing source identity cannot be silently overwritten:
`replace_source` is a separate, explicit operation.

The immutable `SourceBlob` and `SourceSpan` contracts are reused from the native
`nabt.learning.source_evidence` module. Original bytes are preserved; no lossy
normalization is presented as exact restoration. The reader's `segments`
partition includes punctuation and whitespace, while clause and component
spans retain their more precise semantic locations.

## Inference and conflict policy

Rules are finite, function-free, safe Horn clauses. Every variable in a head
must occur in a body premise. Body variables are joined by exact equality;
repeated variables impose equality, and distinct variables do not silently
impose inequality. Facts and queries must be ground. Negative body literals
require explicit negative support; absence never satisfies them.

The engine computes two closures for the requested scope:

1. **Signed closure:** positive and negative atoms are separate propositions.
   Every applicable explicit rule fires. A contradiction does not establish
   unrelated propositions.
2. **Clean closure:** identify every ground atom whose two signs occur in the
   signed closure, then recompute from nonconflicted facts. A rule application
   is usable only when its head and every antecedent are nonconflicted and its
   antecedents have clean derivations.

This is a conservative, global conflict-blocking policy. It is not a claim to
compute all maximal consistent theories, to rank sources, or to resolve their
disagreements. The second closure preserves an alternate clean path even if
another path to the same conclusion uses a contested premise.

For a query `q`, result fields `positive_support` and `negative_support` mean
support for **the requested signed atom** and its opposite respectively. Thus
a negative query can itself be supported.

| Query result | Exact meaning |
|---|---|
| `SUPPORTED` | `q` has a clean derivation and both signs are not jointly supported. |
| `REFUTED` | The opposite of `q` has a clean derivation and both signs are not jointly supported. |
| `CONFLICT` | Both signs occur in signed closure; neither is selected as the answer. |
| `UNKNOWN` | Neither sign is supported by the available source theory. |
| `DEFER / CONTESTED_PREMISES` | Signed support exists only through globally contested premises. |
| `OUT_OF_SCOPE` | No matching scoped predicate signature exists. |
| `DEFER / RESOURCE_LIMIT` | A declared computational or output budget was exhausted. |

Resource exhaustion never becomes a negative assertion or a claim of complete
absence. Malformed inert inputs are rejected separately through `NabtError`.

## Proof certificates and independent replay

`QueryResult.proofs` can contain certificates for `query` and `opposite`. Each
step contains its ground atom, the complete current clause identity, a ground
variable substitution, and indices of preceding checked premise steps. Fact
steps have no premises or substitution. A rule step must match the installed
rule's ordered body and head under exactly its declared variables.

`verify_certificate` reparses the current active source bytes and checks the
certificate against those extracted clauses. It is independent of the
forward-search proof producer. A content digest is only an index; the supplied
clause is compared with the full re-extracted clause using canonical JSON,
which distinguishes `true` from integer `1`. Source locations, polarity,
substitution, future references, caller-added authority flags, unsupported
versions, cyclic objects, malformed Unicode, and noninert values are rejected.
Input byte, node, nesting, integer, and step bounds are checked before replay.

The claimed origin program digest must have occurred among admitted snapshots
in the current kernel session. Even a known origin does not authorize a step:
each current dependency is rechecked. An unrelated source addition or removal
can preserve an old certificate. A changed or withdrawn dependency invalidates
it. A certificate marked `clean` is also checked against current global
conflicts, so a newly added opposing source can invalidate its clean status.

Snapshots contain raw source bytes encoded as hexadecimal and deterministic
metadata. They are data for explicit replay, not authority-bearing saved
objects. A raw integer, a snapshot, a hash, a receipt, or a `passed` flag does
not supply an admitted fact.

## Named missing-premise alternatives

For an unknown query the engine explores backward over installed rules and
grounds additional body variables over the active scope's named constants plus
the query's named arguments. It collects finite alternatives of explicitly
signed, ground missing statements. It removes duplicate and inclusion-dominated
sets under this backward search policy. Already clean premises need no addition;
a conflicted premise or the opposite of a clean premise is not proposed as a
clean completion.

**Every returned alternative is additionally tested by a counterfactual run:**
add its statements only to a temporary hypothesis set, recompute signed closure
and global conflicts, then recompute clean closure. Retain the alternative only
if it makes the requested target clean. This catches both a plan containing
`P(a)` and `¬P(a)`, and a seemingly consistent plan whose rules would indirectly
create a disabling conflict. Hypotheses have no source clause or evidence
identity and cannot be exported as proof certificates. They never enter the
active source store or change a subsequent query.

Directly asserting the target is a possible fallback. It is omitted only after
another counterfactually valid alternative survives. It can itself fail when
the existing theory would derive its opposite. No returned alternatives means
none survived this declared search, not a proof that every imaginable change
to knowledge is impossible.

`missing_complete` refers **only** to the bounded, named
`bounded_grounded_backward_plans_active_and_query_constants.v1` policy. It is
not completeness over all possible new constants, rules, source revisions, or
real-world evidence. Cyclic paths become explicit possible leaves. Depth,
grounding, join-work, plan-size, and plan-count exhaustion produce `DEFER` with
`missing_complete: false`.

## Revision and dependence

`remove_source` removes exactly one active source and rebuilds the theory from
the remaining raw sources. `replace_source` validates the replacement atomically
and keeps the old source on failure. Accepted replacements receive new clause
identities when their source content changes. Consequences with another valid
source path remain available after recomputation.

The revision report lists lost signed supports when it can compute that list
within budget. Removal itself can succeed while the optional change report is
deferred; the report then contains the resource residual. Query results are
always recomputed against the remaining active theory. This realizes the
upstream roadmap's requirement that local revision agree with full scoped
recomputation rather than keeping stale conclusions in an opaque cache.

## Scoped numerical identities

`atom_number(atom, scope)` is an injective, reversible encoding of the complete
versioned scoped atom payload as a big-endian natural, represented in canonical
lowercase hexadecimal. Its record explicitly carries namespace
`nabt.scoped-atom`, version `1`, domain `scoped-signed-atom`, and encoding
`canonical-json-utf8-big-endian`. The decoder validates the framing byte,
structure, exact roundtrip, alphabet/version fields, Unicode, and symmetric
size limits. Leading zeroes and boolean values masquerading as version numbers
are rejected.

The number identifies the statement. It does not give a word an attested
meaning, make the statement true, or authorize its insertion into the theory.

## Public API

```python
from nabt.semantics import SemanticKernel
from nabt.text_reader import parse_document

kernel = SemanticKernel()
document = parse_document(
    "تعريف منظم هو مرتب و موثق. ريم هو مرتب. ريم هو موثق.",
    source_id="example",
    scope="example_theory",
)
admission = kernel.add_document(document)
answer = kernel.query_text("هل ريم هو منظم؟", scope="example_theory")
assert admission.accepted
assert answer.status == "SUPPORTED"
assert kernel.verify_certificate(answer.proofs["query"])["accepted"]
print(answer.as_dict())
```

This example is newly authored test material. It is not a citation of a
dictionary or an observed fact about a person.

The other operations are `add_source(raw, source_id=..., scope=...)`,
`remove_source(source_id)`, `replace_source(raw, source_id=..., scope=...)`,
`query(Query | Atom | str | bytes, scope=...)`, and `snapshot()` / `as_dict()`.
The alias `Kernel` names `SemanticKernel`. A parsed `Query` retains its scope;
an incompatible explicit scope override is rejected. Queries do not mutate
the source inventory or its named individuals.

`SemanticBudget` bounds source count/bytes, clauses, closure atoms, groundings,
join work, rounds, proof steps, backward depth, plans, plan atoms, output bytes,
certificate nodes, and certificate nesting. A zero bound is a valid request
for no work in that dimension. Booleans are not accepted as integer budgets.

## Formal scope and tests

`formal/Nabt/SemanticInference.lean` specifies a generic ground signed calculus
whose admitted fact and rule bindings include source identity, digest, and
scope. It proves proof-replay soundness, conditional model soundness, active
source dependence, absence of spontaneous consequences without facts, source
withdrawal invalidation, extension/reordering preservation, signed
nonexplosion with an actual two-sign witness, and the classifier's explicit
conflict/unknown/tainted cases. For a separately supplied blocking set it also
proves that the filtered clean ground calculus is a subtheory, that every clean
derivation is a signed derivation, and that clean conclusions and rule premises
are unblocked. Computing that global blocking set in Python remains a distinct
implementation obligation.

The Lean claims concern that defined ground calculus. They do not prove the
Arabic reader, Python unification or saturation, cryptographic hash properties,
truth of inputs, or completeness of the missing-plan search. Runtime tests and
the independent evaluation are separate evidence, and must be reported as such.

`tests/test_semantics.py` includes fresh generated definition vocabularies,
binary joins, repeated variables, negative antecedents, same-scope and
cross-scope boundaries, atomic failed admission, source replacement/retraction,
alternative clean proofs, forged certificates, UTF-8/number boundaries, and
bounded work. An independent finite-model oracle enumerates all models for
each of 64 sets of signed premises over six propositional support variables;
it checks query statuses against the signed and clean policies without copying
the engine's unifier or saturation recurrence. Counterfactual-plan tests cover
direct and induced conflict and prove that asking for a plan leaves the active
snapshot unchanged.

## Reused sources, status, and licensing

| Immutable source | Read contracts | Native application |
|---|---|---|
| `Saleh1967/Mashru@e4c801ffe9171dadedcc3aae23051ea0953ae361` | `Aql/Qaida.lean`: admitted rules, sequential proof replay, content-based rule steps | Ground inference specification and source-replayed runtime certificates. |
| Same pin | `Madlul/Dalala.lean`: witnessed full meaning, components, separate entailment | Definitions compile explicit directions; external implications require rules. |
| Same pin | `Jisr/MantuqMafhum.lean`: consequence tied to interpreted antecedent; named conditions on negation | Every consequence retains antecedents and rule source; no implicit contrapositive. |
| Same pin | `Aql/Idaa.lean`, `Madlul/Hawass.lean` | Source interpretation and mathematical proof remain separate from reality truth; whole source/span identity replaces prefix matching. |
| Same pin | `خارطة_الطريق.md`, `hawkama/خطة_الإطلاق_التجريبي.md` | Controlled translator, source binding, withdrawal/recomputation, question interface are implemented here within the declared grammar. |
| `Saleh1967/Alghanem@9d8fa03a51f894416e0abaf3b6821c5ae6441dcd` | `formal/a116/A116/QiraaMadlul.lean`: reading must come from available candidates; syntax licensing separate from semantics | No general Arabic reading or world judgment inferred from the sound kernel. |
| Same pin | `suspended/src/alghanem/ontology/{content,epistemics,substance,inference,facts,operations,verification}.py` | Explicit polarity, typed arity, scope, five-way support distinction, dependency-aware revision. These are reimplemented contracts from **suspended** code, not imports or borrowed proof claims. |

Both source repositories license their code under MIT, copyright (c) 2026
Saleh1967; the same notice and MIT grant are retained in NABT's `LICENSE`.
Only their computational contracts and attributed proof pattern are reused.
No third-party dictionary or book corpus is copied into this implementation.
The separate `hamil-hala-zaman-program` license explicitly excludes named
third-party bytes and distinguishes MIT code from CC BY 4.0 project documents;
those corpus bytes are not incorporated here.

The upstream roadmap records the limitations of its own readers and witnesses.
In particular, prefix-only source matches and caller-supplied witness labels
are not reused as authority. Their presence in an upstream theorem or test does
not turn them into the acceptance policy of this independent implementation.
