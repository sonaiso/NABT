# Frozen discourse post-review regression protocol

Created: **2026-10-23T16:35:24Z**. Author: the source-audit reviewer.

## Scope and independence

This material preserves **26 authored cases** for six concrete defects reported in the bounded read-only review and the accusative-alif boundary raised by the implementation author. It is independent review authorship, **not a blind evaluation**, a naturally occurring corpus, or a revision to the separately frozen v1 evaluation. The reviewer had inspected the relevant code and reported the counterexamples before writing this regression matrix. No independent gold was opened, copied, or modified.

The seven groups are question force, indicative obligations inside a relative clause, temporal qualification, source-backed agreement when context gender is unknown, the imperfect host required by sawfa, CLI resource-check ordering, and accusative orthography. Controls reuse the corresponding supported forms. The cases and oracle permit conservative deferral where the contract does not require new coverage.

## Authored lexical premises

`post_review_training.tsv` preserves an exact copy of the already declared instructional fixture `examples/discourse_training.tsv`, followed by one explicitly authored comment and record. These records are **not quotations from QAC**. The new record is:

```text
(1:25:1:1)	yawomFA	T	STEM|POS:T|LEM:yawom|ROOT:ywm|M|ACC
```

It supplies an indefinite-day lexical observation alongside the fixture's article + day observation. It is designed to verify that shared `LEM:yawom` cannot erase the distinction between `يَوْمًا` and `الْيَوْمَ`. Case and mood labels stay masked in the learner; this test does not authorize recovering the answer from `ACC`.

`post_review_context.json` preserves the fixture's explicit entity/participant/deixis premises. The six agreement cases set only Zayd's context gender to `unknown`; the lexical `MS` witness remains. This makes failure to use the source-backed gender observable without manufacturing a gender from context.

## Frozen oracle

`post_review_cases.json` is the sole case/expectation manifest. `tests/test_discourse_review.py` consumes these cases and checks the freeze digests before compiling their lexical model. The bounded evaluator records only decisions and relevant qualifiers; it does not substitute a policy answer into the reader.

- A question written with `؟` may be a licensed question or a deferral. It may not yield an asserted claim. The explicit polar-question and ordinary assertive controls distinguish the two forces.
- Ungoverned jussive sound/hollow forms inside the declared relative frame must defer. Their indicative counterparts are positive controls.
- Indefinite day evidence must not support the specifically definite day question. Exact repeated qualifications remain supported controls. No calendar anchor or date arithmetic is introduced.
- Source-backed contradictory agreement must defer even if context gender is unknown. Compatible SVO/VSO and relative controls remain licensed; no universal claim about Arabic agreement is inferred from these few examples.
- A perfect after `سوف` must defer; the qualified imperfect control preserves future tense.
- Oversized report/context/text requests must yield structured `DEFER/RESOURCE_LIMIT` before optional QAC opening or compilation. Text reads remain bounded by one byte over the existing limit. The valid read is a positive control. This is a resource-order property, not an unbounded-text-read allegation.
- `كان زيد عالم` must not acquire a missing accusative alif silently. `كان زيد عالمًا` may be licensed by an explicit supported implementation or deferred at its coverage boundary. The ordinary nominative `زيد عالم` remains the control. This regression does not assert coverage of all modern spelling exceptions.

The original source window relevant to accusative pause is the already pinned `src/nabt/data/source_evidence/sibawayhi.txt`, lines 17782–17792. It is not treated as a complete modern orthographic specification for every hamza, feminine-ending, or final-alif exception.

## Measurement

The review freeze records exact bytes and SHA256 values before this regression suite is run. Runtime files are deliberately outside this fixture freeze: the implementation author is fixing them concurrently. Each measurement records before/after runtime digests and may be used as a stable-version result only if those digests match. A live result is not an historical v1 result and does not replace that separately preserved comparison.

No full make check, packaging, broader corpus performance, or release completion is asserted by this material. New measurements may rerun this unchanged matrix; they must not silently alter its expectations.
