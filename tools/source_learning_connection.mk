PYTHON ?= python3
LAKE ?= lake
EVIDENCE_DIR ?= artifacts/local/source-learning-connection
export PYTHONPATH := $(CURDIR)/src:$(CURDIR)

.PHONY: source-learning-connection
source-learning-connection:
	cd formal && $(LAKE) build verifiedReading evidenceLifecycleV1
	NABT_REQUIRE_CONNECTION_NATIVE=1 $(PYTHON) -m unittest discover -s tests -p test_source_learning_connection.py -v
	$(PYTHON) -m tools.source_learning_connection --request examples/source_learning_connection/request.json --output $(EVIDENCE_DIR)/connection.json
	$(PYTHON) -m tools.source_learning_connection --request examples/source_learning_connection/request.json --verify $(EVIDENCE_DIR)/connection.json --output $(EVIDENCE_DIR)/replay.json
