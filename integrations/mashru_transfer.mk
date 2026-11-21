.PHONY: mashru-transfer-check
mashru-transfer-check:
	PYTHONPATH=src:. $(PYTHON) -m tools.mashru_transfer --lake $(LAKE) --check
	cd vendor/mashru && $(LAKE) build mashruAthar
	PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 $(PYTHON) -m tools.lexical_training.mashru_dependencies --check
	PYTHONPATH=src:. OPENBLAS_NUM_THREADS=1 $(PYTHON) -m tools.lexical_training.mashru_readout --check
	PYTHONPATH=src:. $(PYTHON) -m unittest -v tests.test_mashru_transfer tests.test_current_proof_references
