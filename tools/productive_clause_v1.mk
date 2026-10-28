# Additive productive-clause and organizational gates. Historical laws stay pinned.
include tools/sourced_acquisition_v3.mk

PRODUCTIVE_PHASE ?= exposed

.PHONY: entropy-framework productive-clause-native productive-clause-conformance productive-clause-evaluation
entropy-framework:
	PYTHONPATH=src:. $(PYTHON) -B -m unittest discover -s tests -p test_entropy_framework.py -v
	PYTHONPATH=src:. $(PYTHON) -B -m tools.entropy_framework validate
	@mkdir -p $(EVIDENCE_DIR)
	PYTHONPATH=src:. $(PYTHON) -B -m tools.entropy_framework report > $(EVIDENCE_DIR)/entropy-framework.json

# Run the existing source/native/reference chain before the new freeze, even -j.
productive-clause-native: sourced-acquisition-evaluation
	cd formal && $(LAKE) build productiveClauseV1
	test -x $(CURDIR)/formal/.lake/build/bin/productiveClauseV1

productive-clause-conformance: productive-clause-native
	PYTHONPATH=src:. $(PYTHON) -B -m unittest discover -s tests -p 'test_productive_clause*.py' -v

productive-clause-evaluation: productive-clause-conformance entropy-framework
	$(PYTHON) tools/freeze_productive_clause_v1.py --output $(EVIDENCE_DIR)/productive-clause-freeze.json
	$(PYTHON) tools/evaluate_productive_clause_v1.py --phase $(PRODUCTIVE_PHASE) --code-freeze $(EVIDENCE_DIR)/productive-clause-freeze.json --output $(EVIDENCE_DIR)/productive-clause-result.json

check: productive-clause-evaluation
