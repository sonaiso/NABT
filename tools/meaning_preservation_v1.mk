# Additive meaning transport; preserve all historical acquisition/lifecycle gates.
include tools/evidence_lifecycle_v1.mk

MEANING_PHASE ?= exposed

.PHONY: meaning-preservation-native meaning-preservation-conformance meaning-preservation-evaluation
meaning-preservation-native: evidence-lifecycle-evaluation
	cd formal && $(LAKE) build meaningPreservationV1
	test -x $(CURDIR)/formal/.lake/build/bin/meaningPreservationV1

meaning-preservation-conformance: meaning-preservation-native
	NABT_REQUIRE_MEANING_PRESERVATION_NATIVE=1 PYTHONPATH=src:. $(PYTHON) -B -m unittest discover -s tests -p 'test_meaning_preservation*.py' -v
	PYTHONPATH=src:. $(PYTHON) -B -m tools.meaning_preservation_cli inventory > $(EVIDENCE_DIR)/meaning-research-inventory.json

meaning-preservation-evaluation: meaning-preservation-conformance
	$(PYTHON) tools/freeze_meaning_preservation_v1.py --output $(EVIDENCE_DIR)/meaning-preservation-freeze.json
	$(PYTHON) tools/evaluate_meaning_preservation_v1.py --phase $(MEANING_PHASE) --code-freeze $(EVIDENCE_DIR)/meaning-preservation-freeze.json --output $(EVIDENCE_DIR)/meaning-preservation-result.json

check: meaning-preservation-evaluation
