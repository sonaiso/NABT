# Additive integration: make -f Makefile -f integrations/occurrence_sense.mk occurrence-sense
# Keep the historical evaluation registries and core Makefile unchanged.
.PHONY: occurrence-sense
occurrence-sense:
	$(PYTHON) tools/fetch_lisan_source.py --output artifacts/local/lisan.txt
	$(PYTHON) tools/fetch_qac_source.py --output $(QAC_SOURCE)
	$(PYTHON) tools/build_lexical_completion.py --check
	$(PYTHON) evidence/lexical_loading_v1/build_matrix.py --check
	$(LAKE) --dir formal build
	$(PYTHON) tools/check_axioms.py --lake $(LAKE) --output $(EVIDENCE_DIR)/occurrence-sense-axioms.json
	test -x formal/.lake/build/bin/occurrenceSense
	test -x formal/.lake/build/bin/contextualReference
	test -x formal/.lake/build/bin/lexicalCompletion
	$(PYTHON) -m unittest discover -s tests -p 'test_occurrence_sense*.py' -v
	$(PYTHON) tools/benchmark_occurrence_sense.py --require-native --require-safety --output $(EVIDENCE_DIR)/occurrence-sense-benchmark.json

check: occurrence-sense
