# Optional inference development gates; historical build freezes remain intact.
.PHONY: mantuq-inference
include integrations/current_proof_references.mk
mantuq-inference: formal
	$(PYTHON) tools/check_qualified_inference.py --lake $(LAKE) --output $(EVIDENCE_DIR)/qualified-inference-conformance.json
	$(PYTHON) -m tools.mantuq_inference.links --lake $(LAKE) --check $(MANTUQ_LINK_REFERENCE) --output $(EVIDENCE_DIR)/inference-proof-links.json
	$(PYTHON) -m tools.benchmark_mantuq_inference --output $(EVIDENCE_DIR)/mantuq-inference-benchmark.json

check: mantuq-inference
