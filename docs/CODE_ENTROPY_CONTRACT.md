# Code entropy and strategic coherence — measurement contract v1

Base: `a14332afb934bedd4f35bf2fb3d34c9004df52b7` (merged PR 53).
This contract precedes the new audit implementation. It specifies engineering
observations, not a new Arabic law, proof of Python refinement, or release gate.

## Populations and reproducibility

Read tracked production Python files under `src/nabt/`, `tools/`, and
`integrations/`; exclude paths with a `tests` component. Never import inspected
modules. Record the inventory, file hashes, parser version and exclusions.
Distinguish a committed Git-tree baseline from a working-tree measurement;
untracked files are outside the declared population. Outputs are exclusively
created. Syntax errors or ambiguous module identities fail the audit explicitly.

Resolve literal internal Import/ImportFrom statements, including relative
imports, against that inventory. Retain import locations and distinguish direct
module-body statements from nested statements. Report unresolved/external names
and dynamic import sites separately. These are explicit static import graphs;
they omit implicit package initialization, subprocess/native, data and dynamic
execution dependencies. Acyclicity of either projection does not prove runtime
initialization safety or complete architectural independence.

For each projection report vertices, distinct directed edges, strongly connected
components, weak components, isolated vertices and degree concentrations. For
the simple undirected projection, report `E - V + components`; do not call it a
directed-cycle count or a correctness score. An advertised-theorem projection
must separately count references to definitions/helpers outside its vertex set.

Shannon entropy uses the explicitly declared distribution
`p(module) = its outgoing distinct edges / all distinct edges`. Report bits,
the edge denominator and positive-probability support. An empty edge population
has no measured distribution. Entropy is descriptive: neither lower nor higher
values imply better code, stronger proofs or better Arabic coverage. No combined
quality score or arbitrary weighted ranking is allowed.

Exact clone candidates use AST equality including function names, identifiers,
literals and docstrings, excluding source locations, for functions spanning at
least eight physical lines. Report occurrences and spans. Do not sum nested
spans as an amount of removable code. Historical versions and independent
oracles must not be deduplicated merely to improve this measurement.

## Enforced boundary and strategic evidence

The executable architectural gate prohibits static core (`src/nabt`) imports
from tooling or integrations. Existing core SCCs are reported, not relabelled
as new failures. No statistical metric grants execution or linguistic authority.

Report source-policy rules, runtime operators, supplied theorem links, missing
links and missing implemented-scope metadata with separate denominators.
Missing links do not imply missing theorems; zero unresolved supplied links does
not imply complete linkage. Reuse current catalogue code and references.

Keep the original 72-case acquisition matrix, its positive-goal denominators,
its unmeasured downstream goals and the separate 12-case exposed composition
regression distinct. A required positive case that defers remains a coverage
miss. Static compatibility findings must name the exact two versioned languages.

## Bounded improvements

Share the freeze inventory policy between producer and verifier, while retaining
independent native replay and source/alignment checks. Keep the policy in the
already trusted evaluator bootstrap rather than adding an ordinary prevalidation
helper import. Reject omitted required source/toolchain/data/evidence files.
Sequence native readiness before freezing/evaluation through additive Make
integration. Preserve historical evidence and the installed grammar/kernel.

Validate with independent synthetic graph/import/clone examples, forbidden-edge
mutations, freeze-omission cases and ordering checks. Replay the original matrix
after the code is committed. Document observed changes and remaining strategic
obligations; this audit does not itself implement hamzat-wasl or nominal syntax.
