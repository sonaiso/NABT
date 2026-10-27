# Foundation proof catalogue references

The shared A116 foundation adds 20 compiled declarations. These five reports
were regenerated through the existing public exporters using the pinned Lean
toolchain. The references in `evidence/occurrence_sense_v1/catalog_references`
remain historical and unchanged. The strict typed-JSON comparisons and source
replay are unchanged; CI compares committed references after compilation.

The compiled catalogue has 1,544 declarations and 1,541 normalized statement
groups. All 1,524 previous declaration records remain identical. The grammar
graph retains 36 reference edges and 26 canonical theorem nodes; its catalogue
and manifest bindings and total declaration count change. The other three link
reports change only their full compiled-catalogue digest. These indices do not
establish Arabic coverage, translation fidelity, or world truth.

Regenerate only after a reviewed formal change, with the pinned toolchain:

```sh
REF=evidence/framework_foundation_v1/catalog_references
python3 tools/proof_catalog.py --lake "$LAKE" --output "$REF/proof_catalog.json"
python3 -m tools.grammar_catalog.links --lake "$LAKE" --output "$REF/grammar_link_summary.json"
python3 -m tools.mantuq_inference.links --lake "$LAKE" --output "$REF/mantuq_proof_links.json"
python3 -m tools.linguistic_truth.links --lake "$LAKE" --output "$REF/linguistic_proof_links.json"
python3 -m tools.licensed_inference.links --lake "$LAKE" --output "$REF/licensed_proof_links.json"
```

The existing integration tests discover all five active reference paths from
the Make recipes, check their source hashes and manifest, and require the same
compiled catalogue identity throughout. They supplement the actual compiled
and source-replayed checks; no comparison is replaced by a snapshot-only test.

The full affected integration command is:

```sh
make -f Makefile -f integrations/grammar_catalog.mk \
  -f integrations/mantuq_inference.mk -f integrations/linguistic_truth.mk \
  -f integrations/licensed_inference.mk grammar-catalog proof-catalog \
  routing-conformance mantuq-inference linguistic-truth licensed-inference \
  LAKE="$LAKE" EVIDENCE_DIR=artifacts/local/foundation/integration
```

The Mantuq diagnostic also checks its versioned authoring-contract migration
in `../mantuq_benchmark_contracts_v1.json`; the 34 historical gold cases and
all scoring rules remain unchanged. See `../mantuq_contract_sources/README.md`.

The complete integration command currently fails the unchanged natural-use
nonregression gate on M09: the fully vowelized explicit-intent example retains
its candidates and exact source but no longer acquires `lion`/`literal` under
the stricter mark-preserving contract. Its reason is
`NO_COMPLETE_INTENDED_SENSE_CUE`. M05 improves from FAIL to PASS; that improvement
does not cancel M09's regression. The historical gold, baseline, and success
condition have not been changed. The remaining licensed-inference target is
run separately; its success cannot make the full integration green. Release
remains blocked pending an attested mark bridge for the positive acquisition.
The commands, outcomes, and retained log identities are in `validation.json`.
