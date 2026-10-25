# Optional development integration. Keep historically frozen Makefile unchanged.
# Usage: make -f Makefile -f integrations/grammar_catalog.mk check LAKE=/path/to/lake
.PHONY: grammar-catalog proof-catalog routing-conformance
PROOF_CATALOG_REFERENCE ?= evidence/lexical_completion_v1/proof_catalog.json
GRAMMAR_LINK_REFERENCE ?= evidence/lexical_completion_v1/grammar_link_summary.json
grammar-catalog:
	$(PYTHON) -m tools.grammar_catalog catalog --summary --output $(EVIDENCE_DIR)/grammar-catalog.json
	$(PYTHON) tools/benchmark_grammar_catalog.py --output $(EVIDENCE_DIR)/grammar-retrieval.json

proof-catalog:
	$(PYTHON) tools/proof_catalog.py --lake $(LAKE) --check $(PROOF_CATALOG_REFERENCE)
	$(PYTHON) -m tools.grammar_catalog.links --lake $(LAKE) --check $(GRAMMAR_LINK_REFERENCE) --output $(EVIDENCE_DIR)/grammar-proof-links.json

routing-conformance:
	$(PYTHON) tools/check_rule_routing.py --lake $(LAKE) --output $(EVIDENCE_DIR)/routing-conformance.json

check: grammar-catalog proof-catalog routing-conformance
