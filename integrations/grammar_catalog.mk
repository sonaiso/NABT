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

.PHONY: awamil-agent
awamil-agent:
	PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_awamil_agent -v
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog awamil curriculum --output $(EVIDENCE_DIR)/awamil-curriculum.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog awamil check --request examples/awamil_agent/case.json --output $(EVIDENCE_DIR)/awamil-case.json

.PHONY: progressive-agents
progressive-agents:
	PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_progressive_agent_plan -v
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog agents catalog --summary --output $(EVIDENCE_DIR)/progressive-agents.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog agents transport --request examples/progressive_agents/utf16.json --output $(EVIDENCE_DIR)/utf-transport.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog agents transport --request examples/progressive_agents/utf16.json --verify $(EVIDENCE_DIR)/utf-transport.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog agents gate --request examples/awamil_agent/nominal.json --output $(EVIDENCE_DIR)/progressive-factor-gate.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog agents gate --request examples/awamil_agent/nominal.json --verify $(EVIDENCE_DIR)/progressive-factor-gate.json

.PHONY: unit-composition-agent
unit-composition-agent:
	PYTHONPATH=src:. NABT_REQUIRE_UNIT_NATIVE=1 $(PYTHON) -m unittest tests.test_unit_composition_agent tests.test_unit_article_bridge -v
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog units catalog --summary --output $(EVIDENCE_DIR)/unit-catalog.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog units run --request examples/unit_composition/long_vowel.json --output $(EVIDENCE_DIR)/unit-composition.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog units run --request examples/unit_composition/long_vowel.json --verify $(EVIDENCE_DIR)/unit-composition.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog units run --request examples/unit_composition/enumerate.json --output $(EVIDENCE_DIR)/unit-quotas.json

.PHONY: irab-agent
irab-agent:
	PYTHONPATH=src:tests:. $(PYTHON) -m unittest tests.test_irab_agent -v
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog irab analyze --request examples/irab_agent/jussive.json --output $(EVIDENCE_DIR)/irab-jussive.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog irab analyze --request examples/irab_agent/jussive.json --verify $(EVIDENCE_DIR)/irab-jussive.json

check: grammar-catalog proof-catalog routing-conformance operation-rag awamil-agent progressive-agents unit-composition-agent irab-agent

.PHONY: context-application
context-application:
	PYTHONPATH=src:. NABT_REQUIRE_CONTEXT_NATIVE=1 $(PYTHON) -m unittest tests.test_temporal_context tests.test_context_application -v
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog application analyze --request examples/context_application/application.json --output $(EVIDENCE_DIR)/context-application.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog application analyze --request examples/context_application/application.json --verify $(EVIDENCE_DIR)/context-application.json
	PYTHONPATH=src:. $(PYTHON) -m tools.lexical_training.teaching --request examples/context_application/quotation_lesson.json --output $(EVIDENCE_DIR)/temporal-lesson.json
	PYTHONPATH=src:. $(PYTHON) -m tools.lexical_training.teaching --request examples/context_application/quotation_lesson.json --verify $(EVIDENCE_DIR)/temporal-lesson.json

check: context-application
