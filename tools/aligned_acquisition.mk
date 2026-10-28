# Extend verification without rewriting the historical frozen Makefile.
include Makefile
include integrations/grammar_catalog.mk
include integrations/mantuq_inference.mk
include integrations/linguistic_truth.mk
include integrations/licensed_inference.mk

.PHONY: aligned-acquisition-conformance aligned-acquisition-evaluation aligned-acquisition-integration
aligned-acquisition-conformance:
	cd formal && $(LAKE) build alignedAcquisition licensedInference
	test -x $(CURDIR)/formal/.lake/build/bin/alignedAcquisition
	test -x $(CURDIR)/formal/.lake/build/bin/licensedInference
	$(PYTHON) -B -m unittest discover -s tests -p test_aligned_acquisition.py -v
	$(PYTHON) -B -m unittest discover -s tests -p test_aligned_acquisition_evaluator.py -v
	$(PYTHON) -B -m unittest discover -s tests -p test_aligned_acquisition_imports.py -v
	$(PYTHON) -B -m unittest discover -s tests -p test_acquired_inference.py -v
	$(PYTHON) -B -m unittest discover -s tests -p test_current_proof_references.py -v

# Exercise the existing PR 34 contracts and the shared compiled-reference graph.
aligned-acquisition-integration: proof-catalog routing-conformance licensed-inference
	$(PYTHON) tools/check_acquired_inference.py --output $(EVIDENCE_DIR)/acquired-inference.json

aligned-acquisition-evaluation:
	$(PYTHON) tools/freeze_aligned_acquisition.py --output $(EVIDENCE_DIR)/acquisition-freeze.json
	$(PYTHON) tools/evaluate_aligned_acquisition.py --phase exposed --code-freeze $(EVIDENCE_DIR)/acquisition-freeze.json --output $(EVIDENCE_DIR)/acquisition-regression.json

check: aligned-acquisition-conformance aligned-acquisition-evaluation aligned-acquisition-integration
