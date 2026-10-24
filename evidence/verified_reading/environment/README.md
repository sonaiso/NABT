# Local execution environment

The stock pinned Lean binary failed before processing source because its
application-directory detection is unavailable in this host. Stock Lake also
failed installation detection. The two `make` failure logs are preserved.

`main.c` is a small local driver using the **unmodified official Lean 4.34.1
shared library**. It calls the public `Lean.initSearchPath` with the explicit
installed root, then the official shell frontend. It neither patches the
kernel nor substitutes an axiom checker nor intercepts a denied filesystem
operation. Its supported options are intentionally limited to those used.
The kernel, compiler, libraries and proof files were not changed to accommodate
the environment. The pinned archive digest was checked again.

`build_formal.py` traversed imports and compiled the full Nabt dependency graph.
The initial graph audit had 1000 declarations. The final deterministic reader
and its three additional theorems were then compiled, Nabt recompiled and
Audit rerun; the final audit in `../axioms.log.gz` has **1003** declarations.
This is incremental validation over unchanged dependencies, not a claim that
stock `make formal` succeeded. The public command path still needs ordinary
CI on a host with working Lake.

The adapter and its dependencies were emitted as C by this same official
Lean compiler, compiled with the host GCC and linked with the official Lean
shared library. Python tests invoke that native executable. The compiler,
runtime, JSON decoding, file IO and OS are in the declared TCB.

The driver paths record this run and are not the product's distribution API.
On a normal installation, use the standard Lake targets in the documentation.
