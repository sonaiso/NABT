# Additive graph gates; the historically frozen main Makefile is unchanged.
.PHONY: lexical-graph
lexical-graph: formal
	$(PYTHON) tools/build_lexical_graph.py --check --audit-output $(EVIDENCE_DIR)/lexical-graph-license-audit.json
	test -x formal/.lake/build/bin/lexicalGraph
	$(PYTHON) -m unittest discover -s tests -p test_lexical_graph.py -v
	$(PYTHON) tools/benchmark_lexical_graph.py --output $(EVIDENCE_DIR)/lexical-graph-benchmark.json
	$(PYTHON) -m unittest discover -s integrations/inference_db/tests -p test_lexical_graph_schema.py -v

check: lexical-graph
