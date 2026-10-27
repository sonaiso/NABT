# Extend verification without rewriting the historical frozen Makefile.
include Makefile

.PHONY: aligned-acquisition-conformance aligned-acquisition-evaluation
aligned-acquisition-conformance:
	cd formal && $(LAKE) build alignedAcquisition licensedInference
	test -x $(CURDIR)/formal/.lake/build/bin/alignedAcquisition
	test -x $(CURDIR)/formal/.lake/build/bin/licensedInference
	$(PYTHON) -B -m unittest discover -s tests -p test_aligned_acquisition.py -v

aligned-acquisition-evaluation:
	$(PYTHON) tools/freeze_aligned_acquisition.py --output $(EVIDENCE_DIR)/acquisition-freeze.json
	$(PYTHON) tools/evaluate_aligned_acquisition.py --phase exposed --code-freeze $(EVIDENCE_DIR)/acquisition-freeze.json --output $(EVIDENCE_DIR)/acquisition-regression.json

check: aligned-acquisition-conformance aligned-acquisition-evaluation
