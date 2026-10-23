# Independent review of the PR9 counting corrections

The proposed corrections address both reported defects. The same pinned test code and 99-case matrix were run against the previous commit and the corrected runtime. The earlier 184 nominal cases and all historical measurements remain unchanged.

| New regression group | Before, commit `a9efdd7e5a5f9b57aeabce9d3d57fd4bf8a316c2` | After, `0.11.0a2` |
|---|---:|---:|
| Canonical numeral spelling and bounded-domain distinctions | 20/26 | 26/26 |
| Internal and external separator boundaries | 45/73 | 73/73 |
| Total | **65/99** | **99/99** |

The before result reproduces 34 failed cases. Six are long leading-zero spellings: five-digit, twenty-digit and five-zero literals in each supported digit alphabet. The other 28 are four placements of each of seven formerly admitted internal separators: vertical tab, form feed, U+0085 and U+001C through U+001F. LF, CR, U+2028 and U+2029 were already blocked and remain negative controls.

## Review of the implementation changes

The zero-prefix check now examines the first original digit after the entire token has matched one supported digit alphabet. It runs before the four-character domain shortcut. Both digit translation and integer conversion remain after that shortcut. The change therefore preserves the distinction between malformed zero padding and a canonical numeral outside the bounded rule; it does not remove the conversion bound.

The internal-gap predicate now admits TAB or Unicode general category `Zs`. The tests list the expected code points independently of the implementation predicate: TAB and seventeen `Zs` spaces remain accepted. Every line/page/control separator listed above is blocked between a numeral and noun, inside a mixed space/tab gap, and within a compound numeral. Leading and trailing separators remain allowed around an otherwise complete phrase.

Both measurements also require byte-preserved source text and partitions, source replay, no observed grammatical gender from digits, and no actual case, role or world-object count. These are conditional bounded relation checks, not claims of complete Arabic parsing.

## Reproducibility and release binding

- The test file is `tests/test_counting_review_fixes.py`, SHA-256 `b7dc506b7e826a478373a3661d3bf9392b7ec1b0c287f380c03d476b2e3ac9b0`. It defines two discovered unit-test methods over the fixed matrix.
- The matrix is `cases_v1.json`, SHA-256 `dc67e40341781aa8cd14466b2a606cab6f99d15c6b2ea622cc5115d87588d05b`.
- `before_result_v1.json`: `aad613c364dc21be21614360d47efbf9fd71a6cb1a259523a18fbdaebf135d66`.
- `after_result_v1.json`: `502e6470fd7b035bb92cdae7d50fef6c1c32c802642ba334736a001fb75db473`.
- `before_runtime.tar.gz`: `f1923fad4ffc1fe0ff5504d5714c8d8c6df0f96985cec620ea0378f402a6b817`. This Git export was extracted into a temporary directory for the before run; concurrent working-tree edits could not change that baseline.

The matrix and test-file digests are identical between the two runs. Each runtime snapshot has 52 files, and each stayed fixed during its measurement. A path-by-path comparison confirms that every after-run runtime digest matches `evidence/nominal/code_freeze_v2.json`. Its release snapshot is `814ec3f4ea340b09b594ff162e65e49be8e4110088da5feae02fe41eb8a71d6c`; the referenced archive is `code_freeze_v2.tar.gz`, SHA-256 `c7ab0b42159ba60d5a39b65b2adb980ed92df6e6e71eb1dc355bbfb43d838071`.

These are post-review regression cases designed after the two defects were reported. They are not added to the frozen 184-case denominator and are not an external holdout corpus. The independent reviewer changed only the new test file and new files in this review directory. Production changes, version `0.11.0a2`, the second release freeze and full repository/release gates remain parent-owned work.
