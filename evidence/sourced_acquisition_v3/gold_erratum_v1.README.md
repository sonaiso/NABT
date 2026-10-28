# Exposed oracle erratum v1: ayin's A116 index

`gold_erratum_v1.json` is an additive correction to six literal integers in the
independently authored matrix. **Do not edit or replace `gold.json`, its frozen
specifications, or the first execution artifacts.** The independent author
mistakenly encoded `عَ` using index 16, which denotes `ظَ` in A116.

The unchanged definitions in `formal/Nabt/Cell.lean:19` and
`formal/Nabt/Cell.lean:72`, corroborated by the alphabet declaration in
`src/nabt/alphabet.py:14`, give ayin index 17 and fatha state 0:
`4 × 17 + 0 = 68`. The frozen connected specification and source registry
contain `الْعَيْنُ`, `الْعَيْنَ`, and `الْعَيْنِ`; none contains `ظَ`.
This derivation does not depend on the producer's answers.

For each of `o_ayn_u`, `o_ayn_a`, and `o_ayn_i`, the overlay replaces integer
64 with integer 68 at exactly these zero-based locations:

| Expected projection | Array index |
|---|---:|
| `/realization/phrase_cells` | 4 |
| `/acquisition/words/1/cells` | 2 |

No source text, mode, status, goal predicate, denominator, other expected value,
or production behavior changes. The JSON includes the original matrix hash,
the preserved first-result hash, and hashes/locators for all four normative
inputs. Verify its code-owned hash and strict integer before-values before
applying the overlay to an in-memory copy.

Independent static rescoring traversed the existing first-run raw reports
using JSON pointers and exact type equality, without importing NABT or running
native executables:

| Observation on unchanged raw results | Original oracle | Corrected overlay |
|---|---:|---:|
| Contract projections matched | 158/161 | 161/161 |
| Positive goal predicates matched | 90/109 | 90/109 |
| Positive goal predicates **and contract** matched | 87/109 | 90/109 |
| Negative contract controls matched | 52/52 | 52/52 |

The first result stored 90 positive acquisitions and three false-authorization
flags. The latter arose from these erroneous oracle arrays. Preserve those
stored observations and label corrected rescoring separately. Goal-predicate
matching alone is not sufficient for acquisition credit; the complete contract
and independently checked safety conditions remain required. This static
rescore does not rerun those native/source safety checks.

This is an **exposed scoring correction**, not improved linguistic behavior,
a new held-out result, or a proof of Arabic completeness. Every subsequent
runtime evaluation is an exposed replay.

Erratum SHA-256:
`49074e4171a3b2c365018e41c3b9e7af2a03ec0c1915c77628b3e25958014633`.
