# Nominal review-fix release validation

Version 0.11.0a2: 578 tests, 520 audited theorems, 184/184 unchanged authored independent cases, 99/99 additional review-regression cases, full make check exit 0, and installed-wheel correspondence.

validation.json records exact runtime and verification inputs. verification-artifacts.tar.gz retains full logs, reports, and the final wheel build; verification-artifact-manifest.json lists every member and digest. The package was built after the README was updated, and all 51 package files match the new runtime freeze. The a1 freeze, release, and first independent measurement remain unchanged. Review-fix cases are a separate post-review regression set and do not increase the original 184-case score. Prior corpus coverage gaps remain visible.
