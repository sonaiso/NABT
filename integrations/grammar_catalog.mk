# Optional development integration. Keep historically frozen Makefile unchanged.
# Usage: make -f Makefile -f integrations/grammar_catalog.mk check LAKE=/path/to/lake
.PHONY: grammar-catalog proof-catalog routing-conformance operation-rag
include integrations/current_proof_references.mk
grammar-catalog:
	$(PYTHON) -m tools.grammar_catalog catalog --summary --output $(EVIDENCE_DIR)/grammar-catalog.json
	$(PYTHON) tools/benchmark_grammar_catalog.py --output $(EVIDENCE_DIR)/grammar-retrieval.json

proof-catalog:
	$(PYTHON) tools/proof_catalog.py --lake $(LAKE) --check $(PROOF_CATALOG_REFERENCE)
	$(PYTHON) -m tools.grammar_catalog.links --lake $(LAKE) --check $(GRAMMAR_LINK_REFERENCE) --output $(EVIDENCE_DIR)/grammar-proof-links.json

routing-conformance:
	$(PYTHON) tools/check_rule_routing.py --lake $(LAKE) --output $(EVIDENCE_DIR)/routing-conformance.json

operation-rag:
	PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_operation_rag -v
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog rag --request examples/operation_rag/contrast.json --output $(EVIDENCE_DIR)/operation-rag-contrast.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog rag --request examples/operation_rag/contrast.json --verify $(EVIDENCE_DIR)/operation-rag-contrast.json

check: grammar-catalog proof-catalog routing-conformance operation-rag
