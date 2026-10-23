# Construction law: proof and correspondence scope

Law: `nabt.construction-evidence.v1`.
Native module: `formal/Nabt/ConstructionEvidence.lean`.
Exporter: `formal/ExportConstructionEvidence.lean`.
Installed adapter: `src/nabt/construction_laws.py`.

This extension is a conditional algebra of supplied construction witnesses.
It does not prove the acquisition of a lexical sense, an attachment, a role,
an agreement regime, a reference identity, or a complete source analysis.
The discourse reader must acquire and replay those premises separately.
Neither a caller's digest nor a Boolean assertion acquires that authority.

## Source relation

The exact source review is in `evidence/constructions/source_audit.json`.
The independently replayed grammar policy is
`src/nabt/data/source_evidence/construction_policy.json`, policy ID
`nabt.construction-grammar-sources.v1`, with 13 source windows.
Its SHA-256 at this task's source review is
`91b79dcb43467ff1ddf1012cee71a9e47fa8fe4b6f13fc4b3bdad9a35365f21e`.

Before the runtime freeze, the source auditor extended that policy to 17
windows for the counted-tens and attested accusative-alif bridges. The final
installed policy SHA-256 is
`51cd562baefd50a3de493fb88cb39f5b9442c648acdeedd02cdd3a75de378bb4`.
Those additional acquisition premises do not extend the native finite law or
turn the reader's source matching into a Lean theorem.

The reviewed implementation sources are Mashru at
`e4c801ffe9171dadedcc3aae23051ea0953ae361` and Alghanem at
`9d8fa03a51f894416e0abaf3b6821c5ae6441dcd`.
Mashru's `Jisr/Mulhaqat.lean` consumes supplied classifications and anchors.
In particular, `idafaOK` does not establish deletion of tanwin or inflection
nun; `badalOK` does not establish identity, part, or association; the semantic
tawkeed predicate omits a full possessive-pronoun link. The native law does
not treat those omissions as positive witnesses. Arabic source conditions,
including rare permissible forms with «أن», remain explicit premises.

## What the law computes

| Exported relation | Complete finite inventory | Meaning |
| --- | ---: | --- |
| Operator slots | 4 | Licensed kana/inna/zanna/kada constituent requirements |
| Role case requirements | 68 | 17 roles × unknown/nasb/raf/jarr inherited head case |
| Direct adjective agreement | 81 | Four axes, each possible/confirmed/conflict |
| Idafa head evidence | 256 | Two modes × four states for each of three traits × article-exception flag |
| «أن» policy | 7 | Six named operators and a separately licensed inception family |
| Activation core | 256 | Four families × 64 witness masks |
| Identity preservation | 16 | Four relation kinds × four witness masks |
| Scoped projection | 88 | Eleven scopes × eight witness masks |
| **Total** | **776** | Finite table correspondence, not 776 language examples |

Existing case codes are preserved: nasb `0`, raf `1`, jarr `2`, jazm `3`.
The inherited nominal case domain excludes jazm. Unknown inherited case
stays unknown for `naat`, `badal`, and `tawkeed`.

The case of a licensed constituent is separate from the construction and
sign of any word. `assignWordCase` requires a known built/inflected state;
built words receive local case. It explicitly excludes the kada predicate
from word-case assignment. `kadaClause` attaches local nasb to a predicate
clause while preserving its complete internal assignment value. An internal
imperfect's raf/nasb/jazm must therefore come from its own licensed relation.

The adjective table is restricted to a licensed direct-agreement regime of
the real adjective. It is not a universal rule for causal adjectives or
exceptional number/gender agreement. An unknown feature remains possible;
it is not silently filled with a masculine or singular default.

Hal and tamyiz share a conditional nasb requirement, which cannot identify
either role. Here they denote already licensed nominal accusative
constructions. The independent numeral law continues to govern counted
nouns, including genitive counted nouns after 3–10; this table does not
convert every counted noun into accusative tamyiz.

Canonical idafa head confirmation needs explicit evidence that tanwin and
the **inflection nun** are absent. A radical nun is outside that trait.
Unknown is not negative evidence. An independently licensed article
exception is available only for the verbal-idafa mode; it cannot authorize
the article in the canonical semantic mode or override another conflict.
Unknown article evidence remains unresolved even when the exception flag
is present; the law chooses no unobserved realization.

The «أن» table separates permissibility from preference. حرى and اخلولق
require it; the licensed inception sense forbids it. كاد/كرب/عسى/أوشك
permit both alternatives, with the usual preference recorded separately.
`inception` is a sense family, not an exhaustive word list. A rare allowed
form may be outside a reader's implemented coverage, but this law does not
declare it grammatically invalid.

Total badal and nominal tawkeed can preserve an independently witnessed
identity. Part and association do not thereby identify the whole entity.
Shared case and adjacency never create a reference witness.

## General proofs

The module adds **34 registered theorems**. Their groups are:

| Theorem group | Count | Actual contract |
| --- | ---: | --- |
| Role requirements and assignment domains | 8 | Conditional case maps, no inferred role from a shared case, no assignment from unknown construction, built/local separation, outer clause/internal separation |
| Agreement | 3 | Confirmation iff every required axis is confirmed; a conflict blocks; unknown is not confirmation |
| Idafa evidence | 4 | Confirmation requires witnessed absence of tanwin/nun; unknown does not confirm; scoped article restrictions |
| «أن» policy | 2 | Rare permissible alternatives remain allowed; required and inception conditions differ |
| Activation core | 1 | Exact conjunction of six conditional witness fields |
| Indexed receipt isolation | 7 | Exact graph indices/readings/rule; valid distinct source-scoped nodes; nonempty valid support; foreign, incomplete, or blocked receipts rejected |
| Observation boundary | 3 | Adjacency/case observations create no receipt; empty input creates none; every accepted edge has an admitted input receipt |
| Identity boundary | 2 | Independent relation and identity witnesses are needed; part/association do not transfer whole identity |
| Scoped projection | 4 | Complete frame required; exact returned record and metadata preserved; no bare embedded projection |

The receipt context uses `Fin n` indices into a node function. Each node
carries source ID, revision, scope, occurrence, byte interval, segmentation,
and reading identity. Receipt acceptance also checks the expected rule,
distinct disjoint endpoint spans, activity, blocking, complete frame,
attachment/sense licenses, and nonempty support from the same source revision.
The source bytes and their length are not parameters of this formal check:
external replay must establish actual source containment, content and the
linguistic meaning of the cited supports. The general proofs enforce binding
and isolation once those premises exist; they do not authenticate a source.

The scoped claim retains family, sense, tense, time, place, polarity,
restriction, operator binding, and the entire embedded value. Native
`projectScoped` checks equality of the complete original and proposed record.
The finite adapter exposes the corresponding conditional gate; the runtime
must compute its equality witness. All eleven scoped senses conservatively
block bare embedded projection, including certainty and transformation.
This is an information-preservation policy, not a theorem that every lexical
use of علم is nonfactive. An independently justified plain kana/inna claim
uses the existing discourse contract; it is not silently obtained by erasing
one of these scoped records.

## Executed checks

The installed JSON is generated by Lean and has SHA-256:

```text
7499b2b3d1179d02b4c9a8990ae45a2e60f047cd4ad47b525975fea752f57263
```

The task-local validation completed successfully:

- Full pinned `lake build`: 69 jobs, including `exportConstructionEvidence`.
- `tools/check_construction_conformance.py`: complete fresh JSON matched the
  packaged table with type-sensitive comparison; independent oracles and
  the Python adapter agreed on all 776 rows. Report:
  `artifacts/local/construction-development/law-conformance.json`.
- `tests/test_construction_laws.py`: 13 authored boundary tests passed.
  These cover incomplete witnesses, unknown agreement/inheritance, rare
  «أن», idafa exceptions, independent identity, retained scope, strict
  types, cache isolation, and changed installed bytes.
- `tools/check_axioms.py`: all **659** registered theorems passed, including
  the 625 previous declarations and 34 new declarations. The enforcing
  scan covered all `Nabt` declarations. Only `Classical.choice`, `Quot.sound`
  and `propext` were observed. No custom axiom is allowed. Records:
  `artifacts/local/construction-development/axioms.json` and `axioms.log`.

These are kernel and correspondence results. They are not a full release
gate, an independent language evaluation, a parser proof, or a measurement
of successful acquisition from unseen text.
