# Unified NABT I/O acceptance contract

Base: `fb397e3ad0b78862f69dfc4a770a1f5530ff6ba9` (PR 82).
Written before implementing the gateway. This extends the installed owners;
the standalone cognitive-algebra laboratory is not imported into production.

1. The supported external boundary accepts one versioned request envelope and
   emits one versioned result envelope. Consumers reject raw owner results.
2. Dispatch selects installed adapters only. Requests cannot select Python
   symbols, executables, arbitrary paths, proof catalogues, or test outcomes.
3. Each admitted request and emitted result binds the exact source snapshot,
   independent request, selected current compiled catalogue, and route.
4. Proof names/canonical statements are derived from `current_catalog`, never
   copied into a new authoritative theorem list. Stale selectors/sources fail.
5. RAG/source links and owner-family/test links have distinct types. Missing
   explicit source-to-theorem links stay open; family membership is not proof
   of refinement or per-theorem test coverage.
6. Tests are discovered from existing family test references. Their source
   fingerprints and test identifiers are bound. Listing a test never says it ran.
7. Retrieval cannot prune the complete owner search or overwrite its result.
   Explicit operations remain executable when absent from the display top-k.
8. Mantuq/mafhum uses `evaluate_source`, with original source/query and a role
   plan; no synthetic premises from the research laboratory are introduced.
9. Replaying an output needs an independently supplied request and fresh owner
   execution. Altering the request, payload, bridge, status, or snapshot fails.
10. DEFER, CONFLICT, unavailable native checker and resource exhaustion remain
    distinct owner results. Replay success never grants world truth or action.
11. Worker time/output/CPU limits apply to descendants. Deployment exposes only
    the gateway; internal Python APIs/CLIs remain test/development interfaces.
    This is an application contract, not an OS sandbox against a local programmer.
12. CI and the repository check target exercise input/output rejection, proof
    and test resolution, real owner execution and native source inference.

Counterexamples: raw owner receipt; invented route; duplicate JSON key;
boolean display limit; injected checker path; forged proof/test pass flag;
stale test fingerprint; deleted source mapping; changed context or quotation;
tampered output with recomputed self-hash; unknown versus false premise;
missing native binary; worker resource limit; successful replay of DEFER.
