.PHONY: io-gateway io-gateway-build io-gateway-native
.PHONY: relational-bridge
relational-bridge:
	cd formal && $(LAKE) build verifiedReading
	PYTHONPATH=src:. NABT_REQUIRE_RELATIONAL_NATIVE=1 $(PYTHON) -m unittest tests.test_relational_bridge -v

check: relational-bridge

io-gateway:
	PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_io_gateway tests.test_relational_rag tests.test_lexical_ontolex -v
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog gateway catalog --output $(EVIDENCE_DIR)/io-catalog.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog gateway run --request examples/io_gateway/contrast.json --output $(EVIDENCE_DIR)/io-contrast.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog gateway verify --request examples/io_gateway/contrast.json --receipt $(EVIDENCE_DIR)/io-contrast.json

io-gateway-build:
	cd formal && $(LAKE) build verifiedReading classicalSemanticProbe progressiveUnitProbe alignedAcquisition temporalContextProbe recursiveBridgeProbe epistemicMeasurement lexicalDenotation

io-gateway-native: io-gateway-build
	PYTHONPATH=src:. NABT_REQUIRE_IO_GATEWAY_NATIVE=1 $(PYTHON) -m unittest tests.test_io_gateway tests.test_relational_rag tests.test_lexical_ontolex -v

test unit-composition-agent context-application: io-gateway-build
check: io-gateway-native

.PHONY: shared-cognition
shared-cognition: io-gateway-build
	cd formal && $(LAKE) build evidenceLifecycleV1
	PYTHONPATH=src:. NABT_REQUIRE_SHARED_NATIVE=1 $(PYTHON) -m unittest tests.test_shared_cognition tests.test_contextual_alignment tests.test_cognitive_graph -v

check: shared-cognition
