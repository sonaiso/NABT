# Explicit-path Lean shell driver

This host's official `bin/lean` fails while locating `IO.appPath` before it
processes any command line option. `lean_explicit_path.c` uses the unmodified,
digest-verified official Lean 4.34.1 `libleanshared.so` and calls
`Lean.initSearchPath` with `/tmp/nabt-tools/lean-4.34.1-linux` explicitly.
It then delegates option handling and the complete frontend/proof checking to
that library's exported shell functions. No proof rule, environment axiom,
compiler output, `.olean`, or kernel code is patched.

Build:

```sh
cc -O2 -I /tmp/nabt-tools/lean-4.34.1-linux/include lean_explicit_path.c \
  -L /tmp/nabt-tools/lean-4.34.1-linux/lib/lean \
  -Wl,-rpath,/tmp/nabt-tools/lean-4.34.1-linux/lib/lean \
  -lleanshared -o lean
```

Use from the `formal` directory with a normal `LEAN_PATH`, e.g.:

```sh
LEAN_PATH=.lake/build/lib/lean /workspace/scratch/8ead824583ac/lean-driver/lean \
  -o .lake/build/lib/lean/Nabt/FourSlotClosure.olean Nabt/FourSlotClosure.lean
```

Validated locally: `--version` reports the pinned official release; a true
arithmetic theorem compiles to `.olean`; `--run` prints the expected string;
`example : 2 + 2 = 5 := by decide` is rejected. This driver does not claim to
repair Lake, and direct frontend checks must be reported separately from a
successful normal `lake build`.

The discarded `app_path.c` preload experiment did not work because the official
shared library calls its internal `IO.appPath` symbol directly. It is not used
by the driver.

## Actual Lake and native compilation

A subsequent isolated package test completed all four Lake jobs, including
native linking, and its executable printed `lean-driver-smoke-ok`. To make
Lake use the explicit-path shell, the original official `bin/lean` was preserved
as `bin/lean.official` and replaced only in the temporary toolchain installation
by this driver. The library `.lake/build/lib/lean/libLake.so` in that temporary
installation is a symlink to the official `lib/lean/libLake_shared.so`.

`lake` is a wrapper for the official Lake binary with `LAKE_HOME` and
`LEAN_SYSROOT` fixed to that installation and `LEAN_CC` set to `cc` in this
folder. The latter invokes the host `/usr/bin/cc` with a single added linker
search path for the official Lean dependency archives. It does not change Lean
options, recursion bounds, proof checking, source laws or generated machine
values. Using `LIBRARY_PATH` was deliberately avoided because it also selects
the bundled, incompatible startup objects on this host.

The final source SHA256 after enabling standard option permutation (Lake puts
options after the input filename) is:
`eb7c1bc8e7784e8035d74c5ab7e04ec20496f65d4e5834b832a294dc6b97d857`.
The corresponding driver binary SHA256 is:
`14decf83665d37ddba803902af86f599d104b996f6d6998faaeebf22529686b0`.

Use:

```sh
make formal LAKE=/workspace/scratch/8ead824583ac/lean-driver/lake
make conformance LAKE=/workspace/scratch/8ead824583ac/lean-driver/lake
```

The full NABT build log is `nabt-lake-build.log`; its recorded terminal status,
not the existence of the driver or smoke output, determines whether the full
project's native build succeeded.

Final integrated NABT build: **success**, exit status 0, `175 jobs`, recorded in
`nabt-lake-build-integrated.log`. It includes all four newly integrated imports
and the new native phonological/reference exporters. The earlier
`nabt-lake-build.log` records one expected missing-module failure because the
root import file changed after that run had constructed its dependency graph;
the integrated rerun rebuilt the graph and succeeded.
