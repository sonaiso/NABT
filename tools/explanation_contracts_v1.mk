# Extend native explanation verification without rewriting frozen build inputs.
include Makefile

.PHONY: explanation-contracts-conformance explanation-contracts-evaluation
explanation-contracts-conformance: explainable-pilot-conformance
	test -x $(CURDIR)/formal/.lake/build/bin/verifiedReading
	NABT_VERIFIED_READING=$(CURDIR)/formal/.lake/build/bin/verifiedReading NABT_REQUIRE_EXPLANATION_CONTRACTS_NATIVE=1 $(PYTHON) -B -m unittest discover -s tests -p test_explainable_contracts.py -v

explanation-contracts-evaluation: explanation-contracts-conformance
	NABT_VERIFIED_READING=$(CURDIR)/formal/.lake/build/bin/verifiedReading $(PYTHON) -B tools/evaluate_explainable_pilot.py --output $(EVIDENCE_DIR)/explainable-pilot.json

check: explanation-contracts-conformance
