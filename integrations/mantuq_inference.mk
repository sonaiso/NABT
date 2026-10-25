# Optional inference development gates; historical build freezes remain intact.
.PHONY: mantuq-inference
mantuq-inference: formal
	$(PYTHON) tools/check_qualified_inference.py --lake $(LAKE) --output $(EVIDENCE_DIR)/qualified-inference-conformance.json
	$(PYTHON) -m tools.mantuq_inference.links --lake $(LAKE) --check evidence/mantuq_inference_v1/proof_links.json --output $(EVIDENCE_DIR)/inference-proof-links.json
	$(PYTHON) -m tools.benchmark_mantuq_inference --output $(EVIDENCE_DIR)/mantuq-inference-benchmark.json

check: mantuq-inference
