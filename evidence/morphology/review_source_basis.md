# Independent source basis before implementation review

The reviewer read the NABT parent snapshot
`34afbd4fb7adc16471ee7be8dcd48d945a65ad90`, packaged primary texts, and
upstream Git objects. New morphology runtime and formal files were not read
before the independent case material was defined. This note records the
source distinctions used to design that material; it does not certify a
particular implementation or a general Arabic parser.

## Source pins

- Mashru: `e4c801ffe9171dadedcc3aae23051ea0953ae361`.
- Alghanem: `9d8fa03a51f894416e0abaf3b6821c5ae6441dcd`.
- Qatr, Alfiyya and Sibawayhi are the exact packaged primary texts at the
  NABT parent snapshot. Independent material records the bytes of the
  passages on which an expectation depends.

## Distinctions the evaluator must preserve

| Topic | Source-supported distinction | Required independent counterexample |
|---|---|---|
| Noun inflection | Qatr 47 defines change due to grammatical factors. A fixed occurrence does not show all counterfactual behavior. | One unchanged spelling cannot prove construction; absence of an inflection witness cannot be converted into a negative witness. |
| Past and imperative | Qatr 55–63 and Alfiyya 66 state that they are built. Different attached forms can have different built endings. | Construction must not be defined as one spelling across every attachment. |
| Imperfect | Qatr 65–69 and Alfiyya 66–67 distinguish feminine-plural nun and **direct** emphatic nun from the other contexts. | An unidentified final nun, or missing attachment evidence, cannot license either construction or inflection. |
| Particle | Qatr 70–72 and Alfiyya 68 state that particles are built. | Failure to detect a noun or verb sign is not evidence that no such sign is accepted. |
| Diptote realization | Qatr 87–89 and Alfiyya's early declension section give fatha for the diptote's genitive, with al/idafa exceptions. | With al or idafa, kasra is a realization; the underlying cause must remain independently recorded. |
| Diptote causes | Alfiyya 851 onwards qualifies the paired causes, original adjectival status, feminine restrictions, proper-name conditions, and further exceptions. | A name, suffix, or apparent pattern alone is not the full qualified cause. |
| Semantic jamid/mushtaq | Shakhsiyya j3 in Alghanem's pinned text separates the universal essence/name-of-genus from a universal indicating a bearer of an attribute. Mashru `Dal/AqsamAlism.lean` encodes this typed partition. | A negative or absent derivation-origin witness cannot by itself establish the semantic name-of-genus branch. |
| Morphological origin | Alghanem `A116/Ishtiqaq.lean` proves template-conditioned recovery and explicitly separates it from semantic relatedness. | A form may admit more than one root/template; common spelling cannot establish shared meaning or derivation origin. |
| Source identity | A grammatical observation is a claim about a reading in a source and scope. | Copying its certificate to identical text with another source identity, another occurrence, or another lexical reading must fail. |

## Upstream results that need a restricted interpretation

1. `Alghanem/formal/a116/A116/Mamnu.lean` defines its `mamnu` Boolean with
   `!tanwin && !al`. That Boolean is not a suitable enduring identity for a
   diptote lexeme: its own cited exception is about the genitive realization.
   The new model should have separate cause, context, and sign values. The
   original theorem remains a theorem of its own definition.
2. `Alghanem/formal/a116/A116/Hudud.lean` proves that a finite list is stable
   under a final-mark operation. The lists include `أيّ` and dual
   demonstratives. This finite property is not a proof that every listed
   linguistic category is built. A new classifier must use scoped source
   rules and preserve the exceptions.
3. `Mashru/SLGE/Simat2.lean` receives a `jamid?` Boolean and defaults missing
   tuple entries to `false`. Its proofs concern computation **after** that
   input. Unknown information in a new text must remain unknown instead of
   becoming the opposite lexical class.
4. `Mashru/Madlul/Jamad.lean` is about physical solids/liquids/gases. It is
   unrelated to the nominal jamid/mushtaq distinction. Likewise a verbal
   nonconjugability property and the nominal semantic classification must
   not share one unqualified flag.
5. `Ishtiqaq.form_alone_does_not_determine_root` uses `انْتَبَرَ` with two
   templates/roots. A recoverable numerical representation therefore
   preserves an already selected analysis; it does not select the root or
   semantic relation from shape alone.

## Measurement boundary

Reading a sentence that explicitly supplies a class is label extraction.
Deriving a class from independently stated properties is a stronger, but
still conditional, task. Neither is evidence that the observations are true
of unrestricted Arabic usage. The independent cases separate these tasks,
exercise unseen identifiers, and record unsupported input as coverage debt.
Positive expectations cannot be passed by a system that always defers.

The review requires both explicit negative evidence and missing-evidence
cases, contradictory source claims, retraction, generic identifier transfer,
exact-source replay, and malformed-certificate rejection. Numerical
round-trips and finite conformance are supplementary checks; they do not
replace the independent source-derived cases.

## Source correction recorded after the first material freeze

Shakhsiyya j3 line 373 distinguishes time indicated **by the morphological
form** from temporal content in a noun's meaning. The preliminary controlled
clause for an event associated with time omitted that qualifier. The source
audit caught this before the first executable evaluation. V1 material is
preserved; V2 uniformly supplies the missing qualifier and adds an explicit
counterexample. The evaluator and assessment keep this post-open correction
visible. V2 is a source-corrected regression set, not an untouched holdout.
