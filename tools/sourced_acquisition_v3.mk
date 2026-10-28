# Additive v3 gates: preserve and replay v1, v2 and the original PR 34 language.
include tools/article_acquisition.mk

SOURCED_PHASE ?= exposed
SOURCED_LINK_REFERENCE ?= $(NABT_PROOF_REFERENCE_DIR)/sourced_proof_links.json

.PHONY: sourced-acquisition-native sourced-acquisition-conformance sourced-acquisition-evaluation
sourced-acquisition-native: article-acquisition-evaluation
	cd formal && $(LAKE) build connectedAcquisitionV3 acquiredSyntaxV3 linguisticTruth
	test -x $(CURDIR)/formal/.lake/build/bin/connectedAcquisitionV3
	test -x $(CURDIR)/formal/.lake/build/bin/acquiredSyntaxV3
	test -x $(CURDIR)/formal/.lake/build/bin/linguisticTruth

sourced-acquisition-conformance: sourced-acquisition-native
	$(PYTHON) -B -m unittest discover -s tests -p 'test_*acquisition*v3*.py' -v
	$(PYTHON) -B -m unittest discover -s tests -p test_acquired_person_nominal_v3.py -v
	$(PYTHON) -B -m unittest discover -s tests -p test_sourced_acquisition_links.py -v
	$(PYTHON) -B -m unittest discover -s tests -p test_operator_traceability.py -v
	$(PYTHON) -m tools.check_sourced_acquisition_links --proof-reference $(PROOF_CATALOG_REFERENCE) --check $(SOURCED_LINK_REFERENCE) --output $(EVIDENCE_DIR)/sourced-source-links.json

sourced-acquisition-evaluation: sourced-acquisition-conformance
	$(PYTHON) tools/freeze_sourced_acquisition_v3.py --output $(EVIDENCE_DIR)/sourced-freeze.json
	$(PYTHON) tools/evaluate_sourced_acquisition_v3.py --phase $(SOURCED_PHASE) --code-freeze $(EVIDENCE_DIR)/sourced-freeze.json --output $(EVIDENCE_DIR)/sourced-result.json

check: sourced-acquisition-evaluation
