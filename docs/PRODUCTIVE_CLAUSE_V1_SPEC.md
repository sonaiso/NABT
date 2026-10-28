# Productive clause v1: sourced, bounded active verbal frames

This additive law follows main `b7442580e7e681a68a85f40bc247be8ee286e7e3`.
Its name is `nabt.productive-clause.v1`. It does not change the installed v1/v2/v3
acquisition laws, their historical matrices, `src/`, or the PR 34 inference
language. The finite source scope is frozen before its independent expected
matrix; both are frozen before accepted-language implementation.

## Source and lexical contract

`evidence/productive_clause_v1/source_scope.json` retains exact local source
identities, UTF-8 byte slices and physical-line coordinates for Qatr and
Sibawayhi. The selected passages support visible regular case marking,
daraba with an agent and a direct object, and VSO/VOS order. Their authors did
not supply a ready-made machine-readable lexicon: the exact vocalizations,
finite lexical classifications and interpretation of the passages are authored
conventions, explicitly separated from verbatim source text.

The only verb is `ضَرَبَ` (DARABA, past, active, transitive). The nominative
forms are `زَيْدٌ`, `بَكْرٌ`, `خَالِدٌ`, `سَعِيدٌ`, `قَيْسٌ`. The accusative
forms are `زَيْدًا`, `بَكْرًا`, `خَالِدًا`, `سَعِيدًا`, `عَمْرًا`.
QAYS has nominative support only; AMR has accusative support only. Uninstalled
forms, including `قَيْسًا` and nominative Amr, defer. This is a partial finite
lexicon, not a claim that those forms are impossible in Arabic. Nominative Amr
also needs a separate silent-waw acquisition contract.

Case endings are read under `ending=wasl`, `onset=word_initial`. There is no
article, cross-word elision or silent normalization. The boundary language is
ASCII spaces/tabs between words, optional leading/trailing spaces/tabs, and at
most one final ASCII full stop after the last word. Internal punctuation,
quotes, newlines and unsupported boundaries defer. Three exact words are
required; the verb must be first.

## Grammar and outcomes

The grammar combines lexical classes, not a list of complete sentences:

- `DARABA + NOM + ACC` is VSO; the second word is agent and third patient.
- `DARABA + ACC + NOM` is VOS; the second word is patient and third agent.
- If all three forms are installed but the two names are NOM/NOM or ACC/ACC,
  the declared three-role frame is `REJECTED_IN_SCOPE`. This is not a universal
  judgment of Arabic ill-formedness; omitted objects, apposition and other
  constructions are outside this law.
- Unknown lexical forms, other grammatical orders, voices, particles,
  morphology, modes or boundaries return `DEFER`, without a licensed reading.
- Malformed API values or resource exhaustion keep their existing separate
  failure conditions. They must not become linguistic rejection.

The native syntax outcome is `LICENSED_CLAUSE`, `REJECTED_IN_SCOPE` or `DEFER`.
A proposed Python reading is not a certified chain. Complete-chain authority
requires original-source acquisition, relevant shape licenses, replay by the
native clause checker, exact request/source/span agreement, and the declared
source packet. A nested success cannot fill a missing obligation.

Each role identifies its original word occurrence by index and both codepoint
and UTF-8 byte bounds. Two occurrences of the lexical name Zayd must not be
collapsed into an externally identified person. Grammatical role and name
classification establish neither coreference nor actual-world identity.
The content is a scoped active-past DARABA relation with agent/patient slots;
it asserts no independently verified event and no exclusivity over other agents.

## Independent acceptance matrix

There are 200 authored acceptance cases, with separate fixed denominators:

| Slice | Size | Independent target |
|---|---:|---|
| Positive in scope | 100 surfaces / 50 frames | Exact source-bound roles, cells and lexical reading |
| Negative in scope | 50 | Known forms but NOM/NOM or ACC/ACC: no licensed three-role frame |
| Outside scope | 50 | Defer without importing unsupported meaning or analysis |

The 50 positive frames are five nominative forms times five accusative forms
times two constituent orders. Each frame has a full-stop and a no-full-stop
surface. A frame succeeds only if both surfaces succeed. These are 50
combinations, not 100 independent linguistic constructions. No held-out lexeme
or blind-test claim is made: source scope, forms and the matrix are exposed to
implementers before implementation. This tests finite compositional production
and source binding, not unrestricted Arabic generalization.

Negative cases comprise 25 ordered NOM/NOM pairs and 25 ordered ACC/ACC pairs.
All their lexical forms are installed. Outside cases explicitly test unsupported
verbs, case/name forms, structures, boundaries, modes and request framing.
No outside case becomes a negative within-scope example after seeing results.

The cell gold is independently tabulated from the declared A116 alphabet; no
runtime acquisition, parser, verifier or implementation recurrence produces the
expected array. Exact word spans are calculated from the authored input strings
by an independent source-coordinate calculation. The source packet's lexical
cells and the matrix's literal arrays are subject to independent review. An
erratum preserves the original and all first outputs rather than silently
editing expectations after exposure.

## Acceptance, freezing and replay

The positive surface target is at least 95/100 complete correct source-bound
readings, while all 50 frame outcomes remain visible. The full framed target
also reports a proposed 48/50 frames; no surface-only success hides failure of
its paired surface. Zero observed false complete-chain authorizations is
required in both negative slices. Correct defer in a required positive case is
a positive-coverage miss, not a successful understanding.

The evaluator reports syntax-only outcomes separately from joined complete-chain
outcomes. Missing native executables, failed source inventory, incomplete
acquisition or failed shape certificates never earn complete-chain credit.
Absent optional projections are `UNMEASURED`; they do not count as passes.
Source integrity, native replay and finite correctness remain distinct evidence
dimensions. No finite result proves absence of errors outside this contract.

Freeze the source/specification commit first, then the independent expected
matrix and GOLD_METHOD commit. Record their ancestry before production implementation. Bind the
first executed snapshot, data, source packet, evaluator and native binaries;
preserve the first attempt, including preflight failure. Later attempts are
exposed replays. Historical NABT reference selectors and independent evidence
are preserved; formal changes require the existing crosslink and integration
process described by `CLAUDE.md`.
