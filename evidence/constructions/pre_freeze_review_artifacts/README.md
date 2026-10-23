# Authored construction review records

`authored_review_records.tar.gz` preserves the 11 original diagnostic/fixture
files and four teaching-source/context inputs used in the development review.
Paths inside the archive retain their repository-relative names. `manifest.json`
records the byte length and SHA-256 of every member and of the archive.

The archive uses sorted regular-file members, zero timestamps and ownership,
mode 0644, and gzip with a zero timestamp. The archive was reopened and every
member compared against its manifest after creation.

Read `../pre_freeze_review.md` for the observations and their confirmed
corrections. These are authored code-review cases. They are not an independent
evaluation or a release gate. Intermediate module hashes in the reports do not
constitute full runtime snapshots. The initial quantified-prefix result was
reduced from tool output; no full initial report for that additional case was
saved. That limitation is retained in the later recheck record and manifest.

To inspect without changing the checkout:

```sh
tar -tzf evidence/constructions/pre_freeze_review_artifacts/authored_review_records.tar.gz
```

Extract into an empty temporary directory if individual inputs are needed.
No independent gold, learned model archive, credentials, or remote-operation
data is included.
