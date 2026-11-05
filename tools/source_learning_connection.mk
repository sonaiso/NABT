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

.PHONY: cognitive-teaching
cognitive-teaching:
	cd formal && $(LAKE) build verifiedReading classicalSemanticProbe evidenceLifecycleV1 epistemicMeasurement connectedAcquisitionV3 groundedPassage
	NABT_REQUIRE_COGNITIVE_NATIVE=1 $(PYTHON) -m unittest tests.test_cognitive_teaching tests.test_grounded_passage tests.test_learning_framework -v
	$(PYTHON) -m tools.lexical_training.curriculum --output $(EVIDENCE_DIR)/curriculum.json
	$(PYTHON) -m tools.lexical_training.teaching --request examples/cognitive_teaching/learning.json --output $(EVIDENCE_DIR)/learning.json
	$(PYTHON) -m tools.lexical_training.teaching --request examples/cognitive_teaching/learning.json --verify $(EVIDENCE_DIR)/learning.json --output $(EVIDENCE_DIR)/learning-replay.json
	$(PYTHON) -m tools.lexical_training.teaching --request examples/cognitive_teaching/qualified.json --output $(EVIDENCE_DIR)/qualified.json
	$(PYTHON) -m tools.lexical_training.teaching --request examples/cognitive_teaching/epistemic.json --output $(EVIDENCE_DIR)/epistemic.json
	$(PYTHON) -m tools.lexical_training.teaching --request examples/cognitive_teaching/world_prior.json --output $(EVIDENCE_DIR)/world-prior.json
	$(PYTHON) -m tools.lexical_training.teaching --request examples/cognitive_teaching/world_prior.json --verify $(EVIDENCE_DIR)/world-prior.json --output $(EVIDENCE_DIR)/world-prior-replay.json
	$(PYTHON) -m tools.lexical_training.teaching --request examples/cognitive_teaching/passage.json --output $(EVIDENCE_DIR)/passage.json
	$(PYTHON) -m tools.lexical_training.teaching --request examples/cognitive_teaching/passage.json --verify $(EVIDENCE_DIR)/passage.json --output $(EVIDENCE_DIR)/passage-replay.json
