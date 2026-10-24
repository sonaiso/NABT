# Source attribution and scope

MASAQ: Morphologically-Analyzed and Syntactically-Annotated Quran, Majdi
Sawalha, University of Jordan, DOI [10.17632/9yvrzxktmr.2](https://doi.org/10.17632/9yvrzxktmr.2).
The pinned [Alghanem source notice](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/corpora/README.md)
identifies CC BY 3.0. The authors' [2025 corpus paper](https://aclanthology.org/2025.clrel-1.7/)
also states CC BY 3.0. At review, the Mendeley version-2 description states
CC BY 3.0 while its separate License field says CC BY 4.0. This discrepancy
is disclosed rather than silently resolved; attribution is retained.

This experiment uses only the exact pinned repository CSV, 20,302,008 bytes,
SHA-256 `d43d2a813afbe0490254bb26623d6041ed352a273d333e731ddbcda3bd0b6f3a`.
The upstream notice gives this same digest and length. Independent byte
comparison to the original DOI download was not performed. The raw CSV is
not redistributed here. Token strings in the training vocabulary, source
annotations in audit records and source-addressed evaluation labels are
derived from this copy and retain this attribution. Original bytes were not
rewritten. Only morphology supervision was used; no Quranic semantic truth
or general-Arabic benchmark claim is made.

The classical sources in `src/nabt/data/source_evidence/` retain the existing
repository [data license](../../src/nabt/data/source_evidence/LICENSE-DATA.md)
and immutable source manifest. OpenITI text selections and derived quotations
are CC BY-NC-SA 4.0, distinct from MIT source code. The Sibawayhi and Qatr
probe's vowels/target interpretations are editorial additions, explicitly
separate from the original quotes, with no independent human review claim.
Literal book texts were not neural training inputs.

The acquisition queue references the derived [Sibawayhi inventory](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/corpora/sibawayh-abniya.tsv),
33,549 bytes, SHA-256 `678ca5144698b571a42804b19b8d1680766df7f2339cf6c9c53d84994051fdd9`.
Its edition/line pointers and extraction labels are retained. It is an intake
queue, not admitted training data; source rights, edition bytes, vocalization,
and interpretation review remain explicit obligations.
