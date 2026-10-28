# Additive lifecycle law after the complete historical acquisition/clause gates.
include tools/productive_clause_v1.mk

LIFECYCLE_PHASE ?= exposed

.PHONY: evidence-lifecycle-native evidence-lifecycle-conformance evidence-lifecycle-evaluation
evidence-lifecycle-native: productive-clause-evaluation
	cd formal && $(LAKE) build evidenceLifecycleV1
	test -x $(CURDIR)/formal/.lake/build/bin/evidenceLifecycleV1

evidence-lifecycle-conformance: evidence-lifecycle-native
	PYTHONPATH=src:. $(PYTHON) -B -m unittest discover -s tests -p 'test_evidence_lifecycle*.py' -v
	PYTHONPATH=src:. $(PYTHON) -B -m unittest discover -s tests -p 'test_productive_lifecycle*.py' -v

evidence-lifecycle-evaluation: evidence-lifecycle-conformance
	$(PYTHON) tools/freeze_evidence_lifecycle_v1.py --output $(EVIDENCE_DIR)/evidence-lifecycle-freeze.json
	$(PYTHON) tools/evaluate_evidence_lifecycle_v1.py --phase $(LIFECYCLE_PHASE) --code-freeze $(EVIDENCE_DIR)/evidence-lifecycle-freeze.json --output $(EVIDENCE_DIR)/evidence-lifecycle-result.json

check: evidence-lifecycle-evaluation
