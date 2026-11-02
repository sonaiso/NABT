# Optional inference development gates; historical build freezes remain intact.
.PHONY: mantuq-inference mantuq-source-fold
include integrations/current_proof_references.mk
mantuq-inference: formal
	$(PYTHON) tools/check_qualified_inference.py --lake $(LAKE) --output $(EVIDENCE_DIR)/qualified-inference-conformance.json
	$(PYTHON) -m tools.mantuq_inference.links --lake $(LAKE) --check $(MANTUQ_LINK_REFERENCE) --output $(EVIDENCE_DIR)/inference-proof-links.json
	$(PYTHON) -m tools.benchmark_mantuq_inference --output $(EVIDENCE_DIR)/mantuq-inference-benchmark.json

# Reuse the same original native readers. Absence is a failed gate, never a skip.
mantuq-source-fold: formal
	cd formal && $(LAKE) build verifiedReading classicalSemanticProbe
	PYTHONPATH=src:. NABT_VERIFIED_READING=$(CURDIR)/formal/.lake/build/bin/verifiedReading NABT_CLASSICAL_SEMANTIC_PROBE=$(CURDIR)/formal/.lake/build/bin/classicalSemanticProbe NABT_REQUIRE_MANTUQ_SOURCE_FOLD_NATIVE=1 $(PYTHON) -B -m unittest tests.test_mantuq_source_bound tests.test_mantuq_source_fold -v

mantuq-inference: mantuq-source-fold

check: mantuq-inference
