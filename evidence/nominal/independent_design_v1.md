# Independent nominal, number and weakness review design v1

This design was written before the reviewer opened the new nominal-number-weakness runtime, generated table, implementation tests or new formal module. The precise public API and controlled source grammar are still being agreed. This file records the independence protocol and planned distinctions; it is **not yet the executable gold fixture**. The final fixture and protocol will be frozen, with hashes, before implementation review.

The existing repository base is `d2013d937fae0336f38c9a49ffd5c8b03858f7fc`. Selected existing primary texts and upstream Lean source passages, their hashes and exact byte spans are recorded in `independent_source_review_v1.json`. No upstream program or Lean build was executed by this reviewer.

## Four separate tasks

1. **Observe raw text:** preserve written occurrences and source spans; record exact cues and their ambiguity. Al-like initial letters, tanwin, ta marbuta, alif/nun, ya/nun, waw/nun, alif/ta and terminal ya do not alone establish lexical nominal classes.
2. **Read explicit source facts:** parse the declared restricted language and keep every claim attached to its source, block/reading and lexical or occurrence identity. Label extraction is reported separately from a classification derived from independently stated conditions. Missing information remains unknown; unsupported clauses prevent an affected conclusion from silently becoming unconditional.
3. **Check count-rule relations:** distinguish a cardinal value, the grammatical number of the counted noun, the gender of its singular lexical unit, and a witnessed relationship between the number expression and that noun. A neighboring token alone is not a relationship certificate. Any licensed expected agreement or government remains a relation requirement rather than an observed actual case/role.
4. **Count written occurrences:** count distinct source occurrences under an explicitly declared selection. Identical spelling at two spans is two occurrences; two references to one occurrence do not create two occurrences. Neither grammatical duality/plurality nor a cardinal word determines the number of world objects.

The weakness task separately classifies the positions of weak radicals in an explicitly supplied root. This is a conditional operation on given radicals, not discovery of the root from a surface verb. Nominal manqus is a different axis from the final weakness of a verbal root.

## Planned independent coverage

| Topic | Positive evidence | Required counterexample or boundary |
|---|---|---|
| Definite/indefinite | Explicit proper-name, interpreted article or independently stated indefinite reading | `محمدٌ` can be a definite proper name despite tanwin; `ألوان`/`الوان` do not become definite from naive al detection; unsupported/ambiguous article identity stays pending |
| Gender | A source-linked lexical gender claim or separately justified agreement witness | `حمزة` and `معاوية` can have masculine readings despite ta marbuta; `شمس` can have a feminine reading without it |
| Singular masculine/feminine | Separate explicit number and gender premises | Absence of a plural suffix does not prove singular; gender and number must not be collapsed into one guessed class |
| Dual masculine/feminine | Source-linked base and dual relation where the contract requires it | `عثمان`/`عنوان` are not established duals by terminal alif/nun; `حين`/`دين` and unvocalized `معلمين` do not settle dual versus plural |
| Sound masculine plural | Witnessed plural/base relation and its licensed conditions | `زيتون`/`قانون` have the same terminal carrier pair; the suffix alone does not establish a sound plural or actual case |
| Sound feminine plural | Witnessed lexical base and licensed added alif/ta operation | `أبيات`/`أوقات` are broken-plural counterexamples to suffix-only classification |
| Broken plural masculine/feminine | Separate lexical-base witnesses for `رجال`/`رجل` and `نساء`/`امرأة` | Pattern fit alone is not a plural-base link; a gender fact for one reading must not migrate to another |
| Cardinal values | Exact supported written number forms or explicit canonical values | Bool-as-one, negative/out-of-domain values, unsupported compound numbers and ordinals must not be coerced into the cardinal profile |
| Three-to-ten relation | Opposite gender of number form relative to the counted noun's singular unit | `ثلاثة رجال` and `ثلاث نساء` versus reversed forms; the plural's syntactic feminine agreement is not the gender of its singular unit |
| One/two and other cardinal ranges | Separate laws only if explicitly installed | Do not extend the three-to-ten opposition to one/two, a compound ten, a tens numeral or a larger unsupported value |
| Counted-noun identity | Explicit source spans and a relationship witness | Duplicate spellings, adjacent unrelated words, quotes, punctuation, newlines and swapped source facts cannot fabricate a link |
| Textual occurrence count | A source-restoring list with distinct occurrence identities | `رجلان` is one written occurrence; `رجل رجل` is two occurrences and does not prove two distinct people; repeated cardinal phrases do not imply addition without an addition rule |
| Middle weakness | Supplied root `قول`, with the middle waw witnessed | Written `قال` cannot reconstruct `قول` rather than another candidate by fiat |
| Separated double weakness | Supplied root `وقي`, positions one and three | Do not call it adjacent double weakness or a merely hollow root |
| Adjacent double weakness | Supplied root `طوي`, positions two and three | Preserve both weak positions; do not discard one to choose a simpler category |
| Initial/final/no weakness | Supplied roots `وعد`, `رمي`, `كتب` | The final weakness of `رمي` does not establish nominal manqus; incomplete, malformed, four-radical or unsupported all-weak roots must retain their explicit boundary |
| Nominal manqus | A nominal inflected reading with a permanent unstressed final ya and preceding kasra, according to the agreed precise contract | `كرسيّ`, `ظبي`, possessive `غلامي`, verbal `يقضي`, and a merely terminal unmarked ya do not supply all premises; dropped-ya `قاضٍ` requires its own source link |
| Contradiction and missing facts | Partial evidence, explicit incompatibilities and distinct alternative readings | Missing is not false; contradictory claims within a reading are not the same as two legitimate alternative readings |
| Replay and authority | Recompute against exact original source and scope | Changing source bytes, source ID, occurrence, base witness, relation or scope invalidates the old report even when the headline class is unchanged |

## Source limits that affect the oracle

- Qatr lines 414–417 and Alfiyya lines 966–967 distinguish the three-to-ten opposition rule. Alfiyya explicitly refers to the gender of the singular units. Compound and tens rules require a separate declared scope.
- Qatr lines 122–149 distinguishes proper names, interpreted articles and other causes of definiteness. A visible prefix or tanwin is not a substitute for that cause.
- Qatr lines 82–95 distinguishes dual/plural endings, final-ya nouns, possessive ya and final-alif nouns after their classes are known. Existing Mashru ending theorems receive `Bab` as an input; they do not acquire it from any word ending in ya.
- Some passages of Sibawayhi use the historical term `منقوص` for final-alif forms. That terminology must not be imported as though it were the later nominal final-ya definition.
- Existing Alghanem weak-root transformations receive roots and conditions. Their proof of a transformation under a condition does not establish the lexical truth of the condition or invert a weak surface to a unique root.

## Freeze and measurement protocol

The final JSON will contain exact inputs and expected outcomes derived from this design and the declared API. Adapters may translate result fields after implementation is opened, but may not change the inputs or expectations to fit it. Generation/supplied-root operands, raw text reading, source-fact parsing, conditional-rule classification, semantic restraint, source replay and occurrence counting will have distinct denominators.

The first runtime evaluation and its code snapshot/archive will be preserved even if it fails. An adapter defect or a legitimate source correction requires a separate explicit erratum, old/new hashes, preserved old results and a separately named later run. No failed case is deleted to improve a score. Authored cases are not described as an untouched external corpus, and post-open integrity attacks are not added to the frozen independent case count.

Every report must preserve raw source identity, exact byte spans, lexical/occurrence boundaries and ambiguity. No lexical or count-rule conclusion may silently become a world-object count, actual syntactic role, actual case or truth about an unrestricted language population.
