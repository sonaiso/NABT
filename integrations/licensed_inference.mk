# Source-to-reading-to-closure bridge; historical kernel gates remain intact.
.PHONY: licensed-inference
LICENSED_LINK_REFERENCE ?= evidence/occurrence_sense_v1/catalog_references/licensed_proof_links.json
licensed-inference: formal
	cd formal && $(LAKE) build licensedInference
	test -x $(CURDIR)/formal/.lake/build/bin/licensedInference
	$(PYTHON) tools/check_axioms.py --lake $(LAKE) --output $(EVIDENCE_DIR)/licensed-inference-axioms.json
	$(PYTHON) tools/check_licensed_inference.py --executable $(CURDIR)/formal/.lake/build/bin/licensedInference --output $(EVIDENCE_DIR)/licensed-inference-conformance.json
	PYTHONPATH=src:. $(PYTHON) -m tools.licensed_inference.links --lake $(LAKE) --check $(LICENSED_LINK_REFERENCE) --output $(EVIDENCE_DIR)/licensed-inference-proof-links.json
	NABT_LICENSED_INFERENCE=$(CURDIR)/formal/.lake/build/bin/licensedInference PYTHONPATH=src:. $(PYTHON) -m unittest discover -s tests -p 'test_licensed_inference*.py' -v
	NABT_LICENSED_INFERENCE=$(CURDIR)/formal/.lake/build/bin/licensedInference $(PYTHON) tools/benchmark_licensed_inference.py --require-contracts --output $(EVIDENCE_DIR)/licensed-inference-benchmark.json

check: licensed-inference
