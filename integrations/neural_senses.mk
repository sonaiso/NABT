# Optional NumPy proposal gate. Acceptance remains owned by lexical_testimony.
.PHONY: neural-senses
neural-senses:
	cd formal && $(LAKE) build lexicalDenotation
	test -x formal/.lake/build/bin/lexicalDenotation
	$(PYTHON) -c 'import numpy'
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tools/train_lexical_senses.py --output-dir $(EVIDENCE_DIR)/neural-senses
	NABT_NEURAL_SENSES_NATIVE=1 NABT_LEXICAL_DENOTATION=$(CURDIR)/formal/.lake/build/bin/lexicalDenotation $(PYTHON) -m unittest discover -s tests -p test_neural_senses.py -v
	NABT_LEXICAL_DENOTATION=$(CURDIR)/formal/.lake/build/bin/lexicalDenotation $(PYTHON) -m unittest discover -s tests -p test_lexical_denotation.py -v
