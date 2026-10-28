# Add the versioned article bridge after the complete v1/PR34 integration gate.
include tools/aligned_acquisition.mk

ARTICLE_PHASE ?= exposed
ARTICLE_LINK_REFERENCE ?= evidence/article_acquisition_v2/integration/article_proof_links.json

.PHONY: article-acquisition-native article-acquisition-conformance article-acquisition-evaluation
article-acquisition-native: aligned-acquisition-evaluation
	cd formal && $(LAKE) build alignedAcquisitionV2
	test -x $(CURDIR)/formal/.lake/build/bin/alignedAcquisitionV2

article-acquisition-conformance: article-acquisition-native
	$(PYTHON) -B -m unittest discover -s tests -p test_article_acquisition_v2.py -v
	$(PYTHON) -B -m unittest discover -s tests -p test_acquired_inference_v2.py -v
	$(PYTHON) -B -m unittest discover -s tests -p test_article_acquisition_evaluator.py -v
	$(PYTHON) -B -m unittest discover -s tests -p test_article_source_links.py -v
	$(PYTHON) -B -m unittest discover -s tests -p test_article_acquisition_build_order.py -v
	$(PYTHON) -m tools.check_article_source_links --proof-reference $(PROOF_CATALOG_REFERENCE) --check $(ARTICLE_LINK_REFERENCE) --output $(EVIDENCE_DIR)/article-source-links.json

article-acquisition-evaluation: article-acquisition-conformance
	$(PYTHON) tools/freeze_article_acquisition.py --output $(EVIDENCE_DIR)/article-freeze.json
	$(PYTHON) tools/evaluate_article_acquisition.py --phase $(ARTICLE_PHASE) --code-freeze $(EVIDENCE_DIR)/article-freeze.json --output $(EVIDENCE_DIR)/article-result.json

check: article-acquisition-evaluation
