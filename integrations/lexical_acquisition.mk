# Reuse the existing lexical and usage native owners; no acceptance-model head.
.PHONY: lexical-acquisition
lexical-acquisition:
	cd formal && $(LAKE) build lexicalDenotation linguisticTruth
	test -x formal/.lake/build/bin/lexicalDenotation
	test -x formal/.lake/build/bin/linguisticTruth
	OPENBLAS_NUM_THREADS=1 PYTHONPATH=src:. $(PYTHON) -m tools.lexical_training.acquisition train --model $(EVIDENCE_DIR)/lexical-acquisition --compare-to evidence/lexical_acquisition_v1/run_01 --output $(EVIDENCE_DIR)/lexical-acquisition-replay.json
	OPENBLAS_NUM_THREADS=1 PYTHONPATH=src:. NABT_LEXICAL_ACQUISITION_NATIVE=1 NABT_LEXICAL_ACQUISITION_RUN=$(EVIDENCE_DIR)/lexical-acquisition $(PYTHON) -m unittest discover -s tests -p test_lexical_acquisition.py -v
	OPENBLAS_NUM_THREADS=1 PYTHONPATH=src:. NABT_LEXICAL_ACQUISITION_NATIVE=1 NABT_LEXICAL_ACQUISITION_RUN=$(EVIDENCE_DIR)/lexical-acquisition $(PYTHON) -m unittest discover -s tests -p test_lexical_explanation.py -v
	OPENBLAS_NUM_THREADS=1 PYTHONPATH=src:. $(PYTHON) -m tools.lexical_training.acquisition connect --model $(EVIDENCE_DIR)/lexical-acquisition --text 'أعني بالأسد الحيوان المفترس' --profile linguistic --output $(EVIDENCE_DIR)/lexical-acquisition-connection.json
	PYTHONPATH=src:. $(PYTHON) -m tools.lexical_training.curriculum --output $(EVIDENCE_DIR)/lexical-acquisition-curriculum.json
	OPENBLAS_NUM_THREADS=1 PYTHONPATH=src:. $(PYTHON) -m tools.lexical_training.acquisition explain --model $(EVIDENCE_DIR)/lexical-acquisition --text 'أداة نكتب بها' --output $(EVIDENCE_DIR)/lexical-explanation.json
	OPENBLAS_NUM_THREADS=1 PYTHONPATH=src:. $(PYTHON) -m tools.lexical_training.acquisition explain --model $(EVIDENCE_DIR)/lexical-acquisition --text 'أداة نكتب بها' --verify-report $(EVIDENCE_DIR)/lexical-explanation.json --output $(EVIDENCE_DIR)/lexical-explanation-replay.json
