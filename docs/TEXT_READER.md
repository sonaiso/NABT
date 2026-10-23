# Controlled Arabic text reader: installed law v1

NABT now has a native reader from new text to source-spanned declarations,
definitions, unary properties, binary relations, conditional rules, and ground
questions. Vocabulary comes from the supplied text. It is not a dictionary of
demonstration sentences.

The reader implements a **declared controlled sublanguage**. A successful read
means that the complete statement has the interpretation specified below. It
does not establish ordinary Arabic grammaticality, lexical attestation,
metaphorical intent, or the truth of the assertion in the world. Ordinary prose
outside this grammar remains visible as a residual.

| Contract | Installed identity |
| --- | --- |
| Language law | `nabt.controlled-arabic.v1` |
| Reader | `nabt.text-reader.v1` |
| Shared inert IR | `nabt.semantic-ir.v1` |
| Source representation | Native `learning.source_evidence.SourceBlob` and `SourceSpan` |
| Default scope | Exact string `default` |

This document defines the new accepted language and its interpretation. Changes
to the grammar or inference meaning require a new version and counterexample
tests. The law is a local interface specification, not an attribution of this
restricted notation to a classical Arabic source.

## 1. Exact grammar

The literals below are exact Unicode strings. A keyword must be a separate
unquoted token. Whitespace separates tokens.

```text
declaration  := "مفهوم" name
              | "علاقة" name
              | "فرد" name

definition   := "تعريف" name "هو" name ("و" name)*

unary_atom   := term "هو" name
binary_atom  := term name term
atom         := unary_atom | binary_atom
signed_atom  := atom | "ليس" atom

conditional  := "إذا" ["كان"] signed_atom
                ("و" signed_atom)* "فإن" signed_atom
universal    := "كل" name "هو" name
query        := "هل" signed_atom

term         := name | variable
variable     := "?" identifier
```

Statements are separated outside guillemets by `.`, `;`, `؛`, `؟`, CR, LF, or
ASCII `?` when it is not immediately followed by a variable identifier start.
The end of the source also ends its last statement. A question is identified by
`هل`; its question-mark punctuation is optional. CRLF and all other separators
remain in the source partition.

An unquoted name begins with a Unicode letter, number, or underscore; subsequent
characters can be Unicode letters, combining marks, numbers, or underscores.
This permits fresh Arabic names and application identifiers without installing
a lexicon. Numbers in names are uninterpreted characters, not numeric values.

Guillemets allow exact multiword names and punctuation: `«محطة القياس»` or
`«صفة. و؛ أخرى؟»`. The interior is the name, including any leading or trailing
spaces. The full source span still contains the guillemets. A quoted name must
have non-whitespace content, cannot contain nested guillemets, cannot begin
with `?`, and cannot contain Unicode control, format, surrogate, private-use,
or unassigned characters (Unicode general category `C`). There is no escape
syntax. Quote a complete token, with whitespace before the next token.

The reserved unquoted words are `مفهوم`, `علاقة`, `فرد`, `تعريف`, `هو`, `و`,
`إذا`, `كان`, `فإن`, `كل`, `هل`, and `ليس`. They can be used as names by quoting
them. Keyword spelling is exact; the reader does not silently remove diacritics
or unify hamza spellings. Other spellings remain distinct labels when they
occupy a valid label position.

A variable starts with ASCII `?`, followed by a Unicode letter or underscore,
then letters, combining marks, numbers, or underscores. Variables occur only
as arguments of explicit conditional rules. Every variable in the conclusion
must occur in at least one premise. Facts and questions must be ground.
Predicates and declaration names are never variables.

There is no bare two-word unary form. For example, the shape `name name` is
unsupported; a unary assertion needs the explicit `هو`. There are no implicit
pronouns, attached conjunctions, existential quantifiers, disjunctions,
function-valued terms, default negation, or multiple conclusions. Those require
another declared language version rather than an unreported heuristic.

## 2. Meaning of each form

Declarations introduce an individual, unary concept, or binary relation. They
do not assert a property of an individual. Declarations are optional: explicit
argument positions in assertions and rules also supply symbol signatures.
Downstream admission checks consistent arity; source spelling alone never
changes a unary predicate into a binary one.

`عينة هو بلوري` means the positive unary atom `بلوري(عينة)`. The order in
`عينة يحاذي مجس` means the binary atom `يحاذي(عينة, مجس)`. `ليس` changes the
polarity of the complete following atom. Missing support for an atom does not
create its explicit negative.

Definitions are **local equivalences between unary concepts**. For example:

```text
تعريف شفاف_موصل هو شفاف و موصل.
```

This produces exactly these source-bound rule directions:

1. `شفاف_موصل(x) → شفاف(x)`;
2. `شفاف_موصل(x) → موصل(x)`;
3. `شفاف(x) ∧ موصل(x) → شفاف_موصل(x)`.

It does not create an individual instance, and it does not infer the defined
concept from either member alone. Generated rules keep the defining statement
and every component span. Their kinds are `definition_forward` and
`definition_reverse`.

`كل بلوري هو منتظم` generates only `بلوري(x) → منتظم(x)`, tagged `universal`.
It does not assert that a crystal exists or that every regular thing is a
crystal. Generated variables are local to their rule.

An explicit conditional is a signed Horn rule: when all premise atoms have
support for one consistent substitution, its conclusion has support. A
negative premise requires explicit negative support. No contraposition,
closed-world negation, or real-world causal meaning follows from this notation.

Definitions and assertions belong to the exact caller-selected `scope` string.
The parser places this scope on the document and questions and includes it in
analysis identities. The semantic kernel is responsible for keeping theories
in distinct scopes separate and for replaying sources before admission.

## 3. A complete input with new vocabulary

```text
مفهوم بلوري.
مفهوم منتظم.
علاقة يحاذي.
فرد رقاقة.
فرد مجس.
كل بلوري هو منتظم.
رقاقة هو بلوري.
رقاقة يحاذي مجس.
إذا ?س هو منتظم و ?س يحاذي ?ص فإن ?ص هو مجاور_لمنتظم.
هل مجس هو مجاور_لمنتظم؟
```

Changing these concept, individual, and relation names requires no parser
branch, training example, or authored mapping table. The interpretation comes
from token positions and the installed law. Correct symbolic consequences
remain conditional on this supplied theory.

## 4. Exact source preservation and residuals

The reader accepts a strict UTF-8 `bytes` value or a Python `str` containing only
Unicode scalar values. It retains the original bytes without normalization.
Source IDs match `[a-z][a-z0-9_]*` and are at most 128 characters.

Every document has a complete ordered partition of `Segment` records. A segment
has a `SourceSpan` and a kind: `statement`, `residual`, `whitespace`, or
`separator`. Segment intervals are nonempty, nonoverlapping, contiguous,
half-open intervals in the original UTF-8 bytes. They restore every byte:

```python
restored = b"".join(segment.span.extract(document.source)
                    for segment in document.segments)
assert restored == document.source.raw_bytes
```

Every accepted semantic item also carries its complete statement span and
`component_spans`: the spans of all lexical tokens in source order, including
keywords and guillemets. A token's offset is a byte offset, not a codepoint
index. Different decomposed spellings, marks, whitespace, and source occurrences
remain distinguishable.

An `analysis_id` is a deterministic content identity tied to language version,
reader version, source ID, complete source hash, scope, statement position, and
interpretation kind. It grants no authority by itself. A caller-supplied IR
record, claimed hash, or accepted flag cannot replace replay of the source.

Unsupported syntax is recorded as a `Residual(code, message, span)` covering
the **entire unsupported statement**. A recognized prefix is never extracted
from that statement. An unclosed quoted name retains the entire remaining
source in its residual.

Any residual makes `document.accepted` false and blocks admission of the
**entire document** in v1. Valid statements elsewhere in the same document may
remain visible for inspection; they are not partially admitted. A document
containing only separators or whitespace has an `EMPTY_DOCUMENT` residual.
An actually empty byte sequence raises `EMPTY_TEXT`, because native source
records require nonempty original bytes.

This deterministic explicit grammar avoids choosing among unexpressed natural
language readings. It does not fabricate a single reading for unsupported
syntax. Future ambiguous forms must carry alternatives; they cannot reuse the
current interface to silently choose one.

## 5. Python interface and outcomes

```python
from nabt.text_reader import parse_document, parse_query

document = parse_document(
    "رقاقة هو بلوري. هل رقاقة هو بلوري؟",
    source_id="specimen",
    scope="experiment_a",
)
assert document.accepted
assert document.facts[0].atom.predicate == "بلوري"
assert document.facts[0].atom.args == ("رقاقة",)

query = parse_query("هل رقاقة هو بلوري؟", scope="experiment_a")
assert query.atom.ground
```

`parse_document(raw, *, source_id="text", scope="default")` returns the shared
`ParsedDocument` from `nabt.text_ir`. It exposes `source`, `segments`,
`declarations`, `definitions`, `facts`, `rules`, `queries`, `residuals`,
`accepted`, `raw_text`, and `as_dict()`.

`parse_query(raw, *, source_id="query", scope="default")` requires exactly one
ground `هل` statement. A mixed document, multiple questions, or an unsupported
question raises `NabtError("INVALID_QUERY", ...)`; residuals and their source
spans are preserved in the error details. The wrapper never selects one query
from a longer document.

| Condition | Result |
| --- | --- |
| Complete supported document | `ParsedDocument`, `accepted=True` |
| Unsupported syntax | Full statement residual, `accepted=False` |
| Invalid input type or Unicode | Named `NabtError`, status `REJECT` |
| Empty original bytes | `EMPTY_TEXT`, status `REJECT` |
| Exhausted reader budget | `RESOURCE_LIMIT`, status `DEFER` |
| Contradictory positive/negative assertions | Both signed atoms remain available; the semantic kernel reports support separately |

The reader executes no Python expressions, plugins, shell commands, source
imports, or input-selected law. Even a quoted name resembling executable code
is an inert string.

## 6. Resource domain

| Resource | Maximum |
| --- | ---: |
| Original source | 65,536 bytes |
| One statement | 8,192 bytes |
| Statements | 256 |
| Source segments | 2,048 |
| Tokens in a document | 4,096 |
| Tokens in one statement | 128 |
| Name or variable | 512 Unicode characters |
| Premises in one explicit rule | 16 |
| Members in one definition | 16 |
| Source ID | 128 characters |
| Scope string | 512 characters |

Limits are installed constants, not caller-supplied proof conditions. Crossing
a text, token, rule, or name work budget aborts the read with a named resource
result. Source-ID and scope restrictions validate metadata; invalid metadata
is rejected. No partial result is returned as complete. A resource limit is not
evidence that the Arabic input is false or linguistically impossible.

## 7. Reuse and immutable source inspection

The parser and grammar are new native NABT code. Reuse is explicit and scoped:

| Source and immutable commit | Consulted paths | Reused contribution and limit |
| --- | --- | --- |
| Qeyas `0ac045125f3d4ed9a984ab2f78a787fe9d014cd9` | `qeyas/fractal_learning/source_evidence.py` | The immutable byte/span and replay contract, already adapted natively in NABT; hashes identify evidence without proving truth. |
| Same Qeyas commit | `qeyas/fractal_learning/arabic_six_nouns.py`, `feature_extraction.py` | Narrow reader scope and separation of input cues, observed outputs, and typed properties; their literal cue dictionaries are not copied into this text reader. |
| Same Qeyas commit | `qeyas/engines/meaning_engine.py`, `relation_engine.py`, `qeyas/phonology/unicode_parser_v3.py` | Inspected real APIs. Supplied label/definition mappings and grapheme parsing do not supply a general text-to-proposition compiler. The default sorted-candidate selection is not reused. |
| Same Qeyas commit | `docs/numeric_strategy_after_repository_audit.md` | The roadmap identifies the missing new-occurrence reader and source-bound conditional programs. |
| Taaqol-GPT `91dad107a7d56e6e05cce4ab54c3d63e5bdf5482` | `src/taaqqul_slot_geometry/lge/c1_surface_token_runtime.py`, `c3_relation_slot_runtime.py`; `weight/lafzi_madlul.py`, `weight/relation_candidate.py`; `docs/14_PR_CHAIN_ROADMAP.md` | Separation of carrier identity, interpretation scope, visible residuals, and candidate claims. These carrier APIs are not an Arabic semantic parser. No runtime or rank machinery is imported. |
| Mashru `e4c801ffe9171dadedcc3aae23051ea0953ae361` | `Qari/Main.lean`, `Nizam/QawaidB.lean`, `Nizam/Baqi.lean` | A real vocalized-text reader with named limits, rule execution, and explicit missing-premise obligations. Their supplied premise masks are not automatically source-backed semantic observations. |

Key consulted SHA-256 values:

```text
Qeyas/qeyas/fractal_learning/source_evidence.py
32c931f6a4f340f8f105c16a38dae99e499aff541256af0a43c785abd21ff4de
Qeyas/qeyas/fractal_learning/arabic_six_nouns.py
0f76014297477700d3a92af576fb02aa6c33d964d70b9173901b60d727599f8d
Qeyas/qeyas/engines/meaning_engine.py
c24618429b9b95cc8153bf323b5e154b50764e20b2387710d6aef597c1860202
Qeyas/qeyas/engines/relation_engine.py
a2d5717cbfd2b983fbe50c2f48e2d98113275de1a2af46693dda5a29ee531995
Taaqol-GPT/src/taaqqul_slot_geometry/lge/c1_surface_token_runtime.py
f3462ec7ce4273b67e97a75cd954a271dbf465f280d6a2e2d5166f815370e9c3
Taaqol-GPT/src/taaqqul_slot_geometry/lge/c3_relation_slot_runtime.py
04d6d19108c04cd6cc1d85d2e79cca36b5943d51e6c5d6b9e1a115f1487942f8
Taaqol-GPT/src/taaqqul_slot_geometry/weight/relation_candidate.py
9eacf3e5e698458ea98696527d570156ed72560fdbe97f679cdf97fd8b6abdf3
Mashru/Qari/Main.lean
d850d19a8e2305341b1305f1fbaf558bf74a57e65d81dc2182e98b740b9aee4f
Mashru/Nizam/QawaidB.lean
0f8be7098b4785deb2e727daa041fe8b9f585dfc2d2104f315813ba1e1131f55
Mashru/Nizam/Baqi.lean
64ba42024a43a69ea2b50e00c9c738aff5d3b6c4bacf1c24ecde714a6c9d4e7b
```

NABT retains the existing Qeyas MIT attribution in `NOTICE.md`. The upstream
repositories remain read-only research sources, with no runtime dependency.

## 8. Verification and actual scope

`tests/test_text_reader.py` specifies expected atoms and rule directions by
hand. It checks fresh vocabulary, both relation arguments, explicit negatives,
range-restricted variables, definition equivalence, independent UTF-8 byte
offsets, exact restoration, quoted delimiters, preserved marks, source/scope
identity, unsupported suffixes, malformed quotation, and resource boundaries.

Run the parser checks with:

```sh
PYTHONPATH=src python -m unittest tests.test_text_reader -v
```

These tests establish executable evidence for the declared reader. They do not
prove a general theorem about all Arabic parsing or the truth of any text. A
formal inference theorem applies to its specified IR relation; correctness of
this Python reader against the declared grammar is a separate obligation.
Independent hidden evaluation and genuine-source coverage must be reported
separately from the authored unit tests. Safe refusal alone is not successful
understanding of the refused text.
