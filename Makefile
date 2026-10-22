PYTHON ?= python3
LAKE ?= lake
export PYTHONPATH := $(CURDIR)/src

.PHONY: test formal conformance axioms check benchmark demo

test:
	$(PYTHON) -m unittest discover -s tests -v

formal:
	cd formal && $(LAKE) build

conformance:
	$(PYTHON) tools/check_conformance.py --lake $(LAKE)

axioms:
	$(PYTHON) tools/check_axioms.py --lake $(LAKE)

check: test conformance axioms
	$(PYTHON) tools/check_integrity.py

benchmark:
	$(PYTHON) tools/benchmark.py

demo:
	$(PYTHON) -m nabt analyse 'كَتَبَ'
	$(PYTHON) -m nabt count --weight 4 --mode waqf
	$(PYTHON) -m nabt generate --weight 4 --rank 0 --mode waqf
