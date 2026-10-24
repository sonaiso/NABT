# Standalone adapter and the historical runtime boundary

The first complete `make check` ran 1,139 tests and correctly rejected two
historical replay boundary tests. Adding `src/nabt/recursive_bridge.py` changed
the installed runtime's authoritative inventory from 74 files to 75, even though
the original 74 files had not changed. The original failed log and command
record remain in `validation_v1/full_check.*`.

The resolution is a separate repository tool, `tools/recursive_bridge.py`, over
the unchanged installed runtime APIs. No existing runtime module or package
entry point imports the new tool. Its own law, source archive, tests, and
measurement record pin it independently. The historical exact-inventory guard
was not relaxed, and no exclusion was added to it. `review.json` records the
original and relocated source identities and verifies the unchanged guards.

`placement.diff` contains the complete production change: import bootstrap,
absolute package imports, and the tool's default repository-root calculation.
The source/grammar/evidence algorithms and frozen measurement assertions are
unchanged. The final executable command is:

```sh
python tools/recursive_bridge.py lean-morphology examples/recursive_morphology.txt
python tools/recursive_bridge.py lean-frame examples/recursive_discourse.txt --qac examples/discourse_training.tsv --context examples/discourse_context.json
```

The independent checker explicitly snapshots the standalone tool, so moving it
does not remove it from its own experiment's source inventory. The original
measurement and archive remain in `independent_runs/run_v1.*`; the new run,
raw-output replay and byte comparison are recorded separately as v2.

The earlier adapter review and its example envelope also remain unchanged.
Its archived replay script names the original module location. To inspect the
current tool use the final v2 independent checker and
`tests/test_recursive_source_bridge.py`; full envelope replay still requires
the external text, corpus and context, with `--kind frame` when applicable.

This placement means the adapter is supplied as a repository tool. Distributing
it inside the installed `nabt-machine` package later would require a new complete
runtime freeze and explicit evaluator registration. The old closed inventory
does not silently acquire new files.
