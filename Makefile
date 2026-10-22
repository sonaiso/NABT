PYTHON ?= python3
LAKE ?= lake
EVIDENCE_DIR ?= artifacts/local
export PYTHONPATH := $(CURDIR)/src

.PHONY: test formal conformance learned-conformance property-conformance source-experiment axioms check benchmark demo

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

source-experiment:
	$(PYTHON) tools/source_learning_experiment.py --output $(EVIDENCE_DIR)/source-learning.json

axioms:
	$(PYTHON) tools/check_axioms.py --lake $(LAKE) --output $(EVIDENCE_DIR)/axioms.json

check: test conformance learned-conformance property-conformance source-experiment axioms
	$(PYTHON) tools/check_integrity.py

benchmark:
	$(PYTHON) tools/benchmark.py

demo:
	$(PYTHON) -m nabt analyse 'كَتَبَ'
	$(PYTHON) -m nabt count --weight 4 --mode waqf
	$(PYTHON) -m nabt generate --weight 4 --rank 0 --mode waqf
