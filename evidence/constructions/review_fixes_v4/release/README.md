# Construction review release: 0.14.0a3 / constructions_v4

The final runtime has 74 frozen source/configuration files. The complete
`make check` run exited 0 with 957 unit tests and unchanged verification
inputs. A separate `make formal` run also exited 0. The checked theorem
registry contains 663 declarations, including 38 construction declarations;
the finite construction table has 794 rows and 18 replayed source passages.
These are conditional contracts, not a proof of the complete Python reader.

The isolated wheel passed 46 CLI checks across 51 recorded commands. Its
73 runtime files and two documentation files match the intended inputs;
the README inside wheel metadata matches the current release description.
No new performance measurement is claimed by this release.

The original construction suite remains 71/86, including 30/43 positives.
It retains 15 named incomplete cases and strict_pass=false. The separate
legacy discourse suite is 56/86, compared with 57/86 in constructions_v2;
substantive questions are 22/45 compared with 23/45. The intervening v3
score of 40/86 is retained and was not approved for release. P16 preserves
source noun/adjective alternatives with different query constraints;
P26 retains unknown lexical number and therefore cannot activate agreement
and syntactic roles. The two coverage gates do not waive false acceptance,
invalid evidence, incomplete journals, execution errors or replay failures.

The aggregate of ten targeted authored review groups is 76/76. Their v2/v3
baselines and one development counterexample are not pooled into a common
baseline. The six historical query-selection regressions remain distinct.
All results are bounded evaluations, not unrestricted Arabic accuracy.

Attachment baseline recovery is explicit: the complete original six-record
journal was recovered losslessly from its verified checkpoint archive.
The differing incomplete loose journals remain preserved as invalid; their
cause is not established. No score or original file was rewritten.

Historical evidence and the earlier release directory remain byte-identical.
The source and output inventories avoid recursive self-hashes. Git and PR #12
carry the eventual release commit identity; validation.json pins the actual
runtime, sources, tools, reports, commands, package and documented limits.
