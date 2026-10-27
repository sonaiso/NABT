# Replay and provenance

The canonical raw run records are stored as deterministic gzip files. Their
uncompressed SHA-256 values are in `summary.json`. Decompression does not create
a new experiment. The original first run used `implementation_freeze_v2.json`
at local commit `b895a52fe76c2f1ec33cd1792df03cc6c18df35e`. Freeze v1 was never
used for a gold execution: a historical Makefile dependency was preserved
before the first evaluation. The relocated, exposed run used v3 at
`6dbf994c55f0cdc2ad162c601c51c365fa83a2df` and retained all outcome counts.

The local Git history is preserved in `local_history.bundle`, through commit
`b2e7ae75682c3da9688fabbf69fc8ce0519dd7e7`. It requires the unchanged upstream
base `a3ba5b32e67c25b2a71a6c8ebc8635659e6e7f74`. It contains the actual ordered
specification, independent matrix, implementation, relocations, and result
commits; local commit IDs are not represented as upstream published commits.

From a NABT checkout containing that base:

```sh
git bundle verify evidence/aligned_acquisition_v1/local_history.bundle
git fetch evidence/aligned_acquisition_v1/local_history.bundle refs/heads/codex/acquisition-reader-contract:refs/heads/acquisition-measured-history
```

This fetch imports the measurement history without switching branches or
merging it into main. The final delivery bundle additionally contains the
validation and documentation commits made after that measured history.

For a new, explicitly exposed regression run from a committed checkout:

```sh
lake --dir formal build alignedAcquisition licensedInference
make -f tools/aligned_acquisition.mk aligned-acquisition-conformance
make -f tools/aligned_acquisition.mk aligned-acquisition-evaluation EVIDENCE_DIR=artifacts/local/acquisition-new-run
```

Choose a new output path each time. The evaluator refuses overwriting results,
checks committed runtime files and source registries, pins the independent
gold/specification bytes, and separately gates native/source integrity and
every declared representation expectation. Positive downstream coverage is
reported independently and may remain missing or unmeasured.

No second run is described as first or held out. Exposed replay after a copied
or squashed publication verifies content and current commits; it does not
pretend that the publication preserved the original local ancestry.
