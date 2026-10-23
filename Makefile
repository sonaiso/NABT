PYTHON ?= python3
LAKE ?= lake
LOCAL_RUN := $(shell $(PYTHON) -c 'import time; print(time.time_ns())')
EVIDENCE_DIR ?= artifacts/local/$(LOCAL_RUN)
TEXT_CODE_FREEZE ?= evidence/governors/code_freeze_v1.json
ARABIC_EVALUATION_DIR ?= artifacts/local/$(LOCAL_RUN)/arabic-regression
GOVERNOR_EVALUATION_DIR ?= $(EVIDENCE_DIR)/governor-regression
export PYTHONPATH := $(CURDIR)/src

.PHONY: test formal conformance learned-conformance property-conformance arabic-conformance governor-conformance source-experiment text-evaluation arabic-evaluation governor-evaluation axioms check benchmark demo

test:
	$(PYTHON) -m unittest discover -s tests -v

formal:
	cd formal && $(LAKE) build

conformance:
	$(PYTHON) tools/check_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/conformance.json

learned-conformance:
	$(PYTHON) tools/export_learned_model.py --check

property-conformance:
	$(PYTHON) tools/check_property_evidence_table.py --lake $(LAKE) --output $(EVIDENCE_DIR)/property-conformance.json

arabic-conformance:
	$(PYTHON) tools/check_arabic_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/arabic-conformance.json

governor-conformance:
	$(PYTHON) tools/check_governor_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/governor-conformance.json

source-experiment:
	$(PYTHON) tools/source_learning_experiment.py --output $(EVIDENCE_DIR)/source-learning.json

text-evaluation:
	$(PYTHON) tools/text_inquiry_evaluation.py --code-freeze $(TEXT_CODE_FREEZE) --output-dir $(EVIDENCE_DIR)/text-regression

arabic-evaluation:
	$(PYTHON) tools/arabic_syntax_evaluation.py --code-freeze $(TEXT_CODE_FREEZE) --output-dir $(ARABIC_EVALUATION_DIR)

governor-evaluation:
	$(PYTHON) tools/governor_evaluation.py --code-freeze $(TEXT_CODE_FREEZE) --output-dir $(GOVERNOR_EVALUATION_DIR) --require-regression-gates

axioms:
	$(PYTHON) tools/check_axioms.py --lake $(LAKE) --output $(EVIDENCE_DIR)/axioms.json

check: test conformance learned-conformance property-conformance arabic-conformance governor-conformance source-experiment text-evaluation arabic-evaluation governor-evaluation axioms
	$(PYTHON) tools/check_integrity.py

benchmark:
	$(PYTHON) tools/benchmark.py

demo:
	$(PYTHON) -m nabt analyse 'كَتَبَ'
	$(PYTHON) -m nabt count --weight 4 --mode waqf
	$(PYTHON) -m nabt generate --weight 4 --rank 0 --mode waqf
