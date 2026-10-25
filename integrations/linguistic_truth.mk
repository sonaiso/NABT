# Optional source-grounded linguistic-use reader; coverage gaps stay explicit.
.PHONY: linguistic-truth
LINGUISTIC_LINK_REFERENCE ?= evidence/lexical_completion_v1/linguistic_proof_links.json
linguistic-truth: formal
	$(PYTHON) tools/check_linguistic_truth.py --lake $(LAKE) --output $(EVIDENCE_DIR)/linguistic-truth-conformance.json
	$(PYTHON) -m tools.linguistic_truth.verify_originals --output $(EVIDENCE_DIR)/linguistic-truth-retained-sources.json
	$(PYTHON) -m tools.linguistic_truth.links --lake $(LAKE) --check $(LINGUISTIC_LINK_REFERENCE) --output $(EVIDENCE_DIR)/linguistic-truth-proof-links.json
	PYTHONPATH=src:. $(PYTHON) -m unittest discover -s tests -p 'test_linguistic_truth*.py' -v
	$(PYTHON) evidence/linguistic_truth_v1/security_review/run_independent_review.py --output $(EVIDENCE_DIR)/linguistic-truth-security-review.json
	$(PYTHON) tools/audit_linguistic_truth_citations.py --output $(EVIDENCE_DIR)/linguistic-truth-citation-audit.json
	$(PYTHON) tools/benchmark_linguistic_truth.py --require-contracts --output $(EVIDENCE_DIR)/linguistic-truth-benchmark.json

check: linguistic-truth
