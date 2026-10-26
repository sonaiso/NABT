# Additive gate; keep the historical core Makefile unchanged.
.PHONY: epistemic-measurement
epistemic-measurement: formal
	test -x formal/.lake/build/bin/epistemicMeasurement
	$(PYTHON) -m unittest discover -s tests -p 'test_epistemic*.py' -v
	$(PYTHON) tools/benchmark_epistemic_measurement.py --require-native --output $(EVIDENCE_DIR)/epistemic-measurement.json
	node integrations/proof_lab/site/scripts/validate-epistemic-report.mjs $(EVIDENCE_DIR)/epistemic-measurement.json

check: epistemic-measurement
