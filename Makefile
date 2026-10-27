PYTHON ?= python3
LAKE ?= lake
LOCAL_RUN := $(shell $(PYTHON) -c 'import time; print(time.time_ns())')
EVIDENCE_DIR ?= artifacts/local/$(LOCAL_RUN)
# Change both selectors only after the evaluator registries pin the new freeze.
RUNTIME_FREEZE_VERSION ?= certified_transition_v2
TEXT_CODE_FREEZE ?= evidence/certified_transition_v2/code_freeze_v1.json
QAC_SOURCE ?= artifacts/local/external/quranic-corpus-morphology-0.4.txt.gz
ARABIC_EVALUATION_DIR ?= artifacts/local/$(LOCAL_RUN)/arabic-regression
GOVERNOR_EVALUATION_DIR ?= $(EVIDENCE_DIR)/governor-regression
export PYTHONPATH := $(CURDIR)/src

.PHONY: test formal conformance learned-conformance property-conformance arabic-conformance governor-conformance word-conformance morphology-conformance morphology-evaluation text-evidence-conformance text-morphology-evaluation derivation-conformance derivation-evaluation nominal-conformance nominal-evaluation inflection-conformance inflection-evaluation discourse-conformance person-conformance construction-conformance construction-evaluation discourse-evaluation source-experiment text-evaluation arabic-evaluation governor-evaluation word-evaluation axioms check benchmark demo

test:
	$(PYTHON) -m unittest discover -s tests -v

formal:
	cd formal && $(LAKE) build

.PHONY: foundation-conformance foundation-architecture
foundation-architecture:
	$(PYTHON) tools/check_foundation_architecture.py --output $(EVIDENCE_DIR)/foundation-architecture.json

foundation-conformance: foundation-architecture
	$(PYTHON) tools/check_foundation.py --lake $(LAKE) --output $(EVIDENCE_DIR)/foundation-conformance.json

check: foundation-conformance

.PHONY: certified-lexical-conformance
certified-lexical-conformance: formal
	cd formal && $(LAKE) build linguisticTruth
	test -x formal/.lake/build/bin/linguisticTruth
	$(PYTHON) -m unittest discover -s tests -p 'test_certified_native_protocol.py' -v
	$(PYTHON) tools/benchmark_certified_natural_use.py --output $(EVIDENCE_DIR)/certified-natural-use.json.gz

check: certified-lexical-conformance

.PHONY: progressive-rule-conformance
progressive-rule-conformance:
	cd formal && $(LAKE) build lexicalSourceRows lexicalSurface exportClassicalWeak exportClassicalHamza exportClassicalGemination exportClassicalBoundaryAffixes
	cd formal && $(LAKE) env lean LexicalSurfaceBindingChecks.lean
	$(PYTHON) tools/fetch_qac_source.py --output artifacts/local/external/quranic-corpus-morphology-0.4.txt.gz
	test -x formal/.lake/build/bin/lexicalSurface
	test -x formal/.lake/build/bin/lexicalSourceRows
	$(PYTHON) -m unittest discover -s tests -p 'test_lexical_surface_binding.py' -v
	$(PYTHON) -m unittest discover -s tests -p 'test_classical_certified.py' -v

check: progressive-rule-conformance

.PHONY: source-acquisition-conformance
source-acquisition-conformance:
	cd formal && $(LAKE) build lexicalSourceRows lexicalSurface qualifiedCueLicensing linguisticTruth exportClassicalWeak exportClassicalHamza exportClassicalGemination exportClassicalBoundaryAffixes
	cd formal && $(LAKE) env lean LexicalSourceAcquisitionChecks.lean
	$(PYTHON) tools/fetch_qac_source.py --output artifacts/local/external/quranic-corpus-morphology-0.4.txt.gz
	test -x formal/.lake/build/bin/lexicalSourceRows
	test -x formal/.lake/build/bin/qualifiedCueLicensing
	test -x formal/.lake/build/bin/lexicalSurface
	test -x formal/.lake/build/bin/linguisticTruth
	test -x formal/.lake/build/bin/exportClassicalWeak
	test -x formal/.lake/build/bin/exportClassicalHamza
	test -x formal/.lake/build/bin/exportClassicalGemination
	test -x formal/.lake/build/bin/exportClassicalBoundaryAffixes
	$(PYTHON) -m unittest discover -s tests -p 'test_lexical_source_acquisition.py' -v
	$(PYTHON) -m unittest discover -s tests -p 'test_qualified_cue_licensing.py' -v
	$(PYTHON) -m unittest discover -s tests -p 'test_grammar_native_authority.py' -v
	$(PYTHON) tools/benchmark_qualified_cues.py --output $(EVIDENCE_DIR)/qualified-cue-cases.json.gz

check: source-acquisition-conformance

.PHONY: certified-transition-conformance
certified-transition-conformance:
	cd formal && $(LAKE) build Nabt sixNounAcquisition scopeAcquisition foundationProbe
	cd formal && $(LAKE) env lean SixNounAcquisitionChecks.lean
	test -x formal/.lake/build/bin/sixNounAcquisition
	NABT_REQUIRE_NATIVE_TRANSPORT=1 $(PYTHON) -m unittest discover -s tests -p 'test_six_noun*.py' -v
	$(PYTHON) tools/benchmark_six_noun_acquisition.py --require-native --output $(EVIDENCE_DIR)/six-noun-acquisition.json

check: certified-transition-conformance

.PHONY: licensed-interface-conformance
licensed-interface-conformance:
	cd formal && $(LAKE) build sixNounAcquisition lexicalSourceRows lexicalSurface qualifiedCueLicensing linguisticTruth lexicalTransmission scopeAcquisition exportClassicalWeak exportClassicalHamza exportClassicalGemination exportClassicalBoundaryAffixes
	cd formal && $(LAKE) env lean LexicalTransmissionChecks.lean
	cd formal && $(LAKE) env lean ScopeAcquisitionChecks.lean
	$(PYTHON) tools/fetch_qac_source.py --output artifacts/local/external/quranic-corpus-morphology-0.4.txt.gz
	test -x formal/.lake/build/bin/lexicalTransmission
	test -x formal/.lake/build/bin/scopeAcquisition
	$(PYTHON) -m tools.interface_migration_audit --output $(EVIDENCE_DIR)/interface-admission-audit.json
	$(PYTHON) -m unittest discover -s tests -p 'test_licensed_workflow.py' -v
	$(PYTHON) -m unittest discover -s tests -p 'test_scope_acquisition.py' -v
	$(PYTHON) -m unittest discover -s tests -p 'test_lexical_transmission.py' -v
	$(PYTHON) -m unittest discover -s tests -p 'test_interface_migration_audit.py' -v

check: licensed-interface-conformance

.PHONY: legacy-migration-conformance
legacy-migration-conformance:
	cd formal && $(LAKE) build sixNounAcquisition discourseBoundaryCue linguisticTruth qualifiedCueLicensing licensedInference lexicalDenotation epistemicMeasurement contextualReference lexicalSourceRows lexicalSurface lexicalTransmission scopeAcquisition exportClassicalWeak exportClassicalHamza exportClassicalGemination exportClassicalBoundaryAffixes
	cd formal && $(LAKE) env lean DiscourseBoundaryCueChecks.lean
	$(PYTHON) tools/fetch_qac_source.py --output artifacts/local/external/quranic-corpus-morphology-0.4.txt.gz
	test -x formal/.lake/build/bin/discourseBoundaryCue
	test -x formal/.lake/build/bin/linguisticTruth
	test -x formal/.lake/build/bin/qualifiedCueLicensing
	test -x formal/.lake/build/bin/licensedInference
	$(PYTHON) evidence/legacy_migration_v2/build_queue.py --check
	NABT_REQUIRE_NATIVE_TRANSPORT=1 $(PYTHON) -m unittest tests.test_discourse_boundary_cue tests.test_transport_contract tests.test_legacy_cli_transport tests.test_transport_mode_replay tests.test_legacy_migration_queue tests.test_independent_legacy_migration_attackcases tests.test_live_transport_binding -v
	mkdir -p $(EVIDENCE_DIR)
	$(PYTHON) -m evidence.legacy_migration_v2.independent_review.run_reference --output $(EVIDENCE_DIR)/legacy-boundary-authority-reference.json.gz

check: legacy-migration-conformance

conformance:
	$(PYTHON) tools/check_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/conformance.json

learned-conformance:
	$(PYTHON) tools/export_learned_model.py --check

property-conformance:
	$(PYTHON) tools/check_property_evidence_table.py --lake $(LAKE) --output $(EVIDENCE_DIR)/property-conformance.json

arabic-conformance:
	$(PYTHON) tools/check_arabic_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/arabic-conformance.json

governor-conformance:
	$(PYTHON) tools/check_governor_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/governor-conformance.json

word-conformance:
	$(PYTHON) tools/check_word_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/word-conformance.json

morphology-conformance:
	$(PYTHON) tools/check_morphology_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/morphology-conformance.json

morphology-evaluation:
	$(PYTHON) tools/morphology_evaluation.py --freeze-version $(RUNTIME_FREEZE_VERSION) --output $(EVIDENCE_DIR)/morphology-regression.json --allow-documented-boundaries

text-evidence-conformance:
	$(PYTHON) tools/check_text_evidence_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/text-evidence-conformance.json

text-morphology-evaluation:
	$(PYTHON) tools/text_morphology_evaluation.py --output $(EVIDENCE_DIR)/text-morphology-regression.json

derivation-conformance:
	$(PYTHON) tools/check_derivation_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/derivation-conformance.json

derivation-evaluation:
	$(PYTHON) tools/derivation_evaluation.py --output $(EVIDENCE_DIR)/derivation-regression.json

nominal-conformance:
	$(PYTHON) tools/check_nominal_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/nominal-conformance.json

nominal-evaluation:
	$(PYTHON) tools/nominal_evaluation.py --output $(EVIDENCE_DIR)/nominal-regression.json

inflection-conformance:
	$(PYTHON) tools/check_inflection_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/inflection-conformance.json

inflection-evaluation:
	$(PYTHON) tools/fetch_qac_source.py --output $(QAC_SOURCE)
	$(PYTHON) tools/inflection_evaluation.py --qac $(QAC_SOURCE) --runtime-freeze $(TEXT_CODE_FREEZE) --output $(EVIDENCE_DIR)/inflection-regression.json --allow-documented-boundaries
	$(PYTHON) tools/inflection_evaluation.py --post-review --runtime-freeze $(TEXT_CODE_FREEZE) --output $(EVIDENCE_DIR)/inflection-post-review-regression.json
	$(PYTHON) tools/inflection_cli_evaluation.py --runtime-freeze $(TEXT_CODE_FREEZE) --output $(EVIDENCE_DIR)/inflection-cli-regression.json

discourse-conformance:
	$(PYTHON) tools/check_discourse_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/discourse-conformance.json

person-conformance:
	$(PYTHON) tools/check_person_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/person-conformance.json

construction-conformance:
	$(PYTHON) tools/check_construction_conformance.py --lake $(LAKE) --output $(EVIDENCE_DIR)/construction-conformance.json

.PHONY: unit-discovery-conformance
unit-discovery-conformance:
	$(PYTHON) tools/check_unit_discovery.py --lake $(LAKE) --output $(EVIDENCE_DIR)/unit-discovery-conformance.json
	NABT_UNIT_DISCOVERY_PROBE=$(CURDIR)/formal/.lake/build/bin/unitDiscoveryProbe $(PYTHON) -B -m unittest discover -s tests -p test_unit_discovery_probe.py -v

.PHONY: progressive-unit-conformance
progressive-unit-conformance:
	$(PYTHON) tools/check_progressive_units.py --lake $(LAKE) --output $(EVIDENCE_DIR)/progressive-unit-conformance.json
	NABT_PROGRESSIVE_UNIT_PROBE=$(CURDIR)/formal/.lake/build/bin/progressiveUnitProbe $(PYTHON) -B -m unittest discover -s tests -p test_progressive_unit_probe.py -v
	NABT_PROGRESSIVE_UNIT_PROBE=$(CURDIR)/formal/.lake/build/bin/progressiveUnitProbe $(PYTHON) -B -m unittest discover -s tests -p test_binary_unit_domain_probe.py -v

.PHONY: recursive-bridge-conformance
recursive-bridge-conformance:
	$(PYTHON) tools/check_recursive_bridge.py --lake $(LAKE) --output $(EVIDENCE_DIR)/recursive-bridge-conformance.json
	NABT_RECURSIVE_BRIDGE_PROBE=$(CURDIR)/formal/.lake/build/bin/recursiveBridgeProbe $(PYTHON) -B -m unittest discover -s tests -p test_recursive_bridge_probe.py -v
	NABT_RECURSIVE_BRIDGE_PROBE=$(CURDIR)/formal/.lake/build/bin/recursiveBridgeProbe $(PYTHON) -B -m unittest discover -s tests -p test_recursive_source_bridge.py -v

.PHONY: inquiry-conformance
inquiry-conformance:
	$(PYTHON) tools/check_rational_inquiry.py --lake $(LAKE) --output $(EVIDENCE_DIR)/inquiry-conformance.json

.PHONY: arabic-inna-fragment-conformance
arabic-inna-fragment-conformance:
	cd formal && $(LAKE) build arabicInnaFragmentProbe
	$(PYTHON) tools/check_arabic_inna_fragment.py --output-dir $(EVIDENCE_DIR)/arabic-inna-fragment

construction-evaluation:
	$(PYTHON) tools/construction_evaluation.py --runtime-root $(CURDIR) --runtime-freeze $(TEXT_CODE_FREEZE) --allow-documented-boundaries --output $(EVIDENCE_DIR)/construction-regression.json

discourse-evaluation:
	$(PYTHON) tools/fetch_qac_source.py --output $(QAC_SOURCE)
	$(PYTHON) tools/discourse_evaluation.py --qac $(QAC_SOURCE) --runtime-freeze $(TEXT_CODE_FREEZE) --output $(EVIDENCE_DIR)/discourse-regression.json --allow-documented-boundaries

.PHONY: arabic-coverage-holdout
arabic-coverage-holdout:
	$(PYTHON) tools/arabic_coverage_holdout_v2.py --output $(EVIDENCE_DIR)/arabic-holdout.json; holdout_status=$$?; test "$$holdout_status" -eq 0 -o "$$holdout_status" -eq 1
	$(PYTHON) tools/framework_foundation_postreview.py --result $(EVIDENCE_DIR)/arabic-holdout.json --raw $(EVIDENCE_DIR)/arabic-holdout.raw.jsonl --runtime-freeze $(TEXT_CODE_FREEZE) --output-dir $(EVIDENCE_DIR)/arabic-holdout-postreview

.PHONY: arabic-completion-oracle
arabic-completion-oracle:
	$(PYTHON) -B -m unittest discover -s evidence/arabic_completion_v3/independent_oracle/continuation_v3 -p 'test_*.py' -v
	$(PYTHON) evidence/certified_transition_v2/independent_oracle/run_regression_v1.py --output-dir $(EVIDENCE_DIR)/arabic-completion-oracle

source-experiment:
	$(PYTHON) tools/source_learning_experiment.py --output $(EVIDENCE_DIR)/source-learning.json

text-evaluation:
	$(PYTHON) tools/text_inquiry_evaluation.py --code-freeze $(TEXT_CODE_FREEZE) --output-dir $(EVIDENCE_DIR)/text-regression

arabic-evaluation:
	$(PYTHON) tools/arabic_syntax_evaluation.py --code-freeze $(TEXT_CODE_FREEZE) --output-dir $(ARABIC_EVALUATION_DIR)

governor-evaluation:
	$(PYTHON) tools/governor_evaluation.py --code-freeze $(TEXT_CODE_FREEZE) --output-dir $(GOVERNOR_EVALUATION_DIR) --require-regression-gates

word-evaluation:
	$(PYTHON) tools/word_evaluation.py --freeze-version $(RUNTIME_FREEZE_VERSION) --output $(EVIDENCE_DIR)/word-regression.json --require-regression-gates

axioms:
	$(PYTHON) tools/check_axioms.py --lake $(LAKE) --output $(EVIDENCE_DIR)/axioms.json

check: test conformance learned-conformance property-conformance arabic-conformance governor-conformance word-conformance morphology-conformance morphology-evaluation text-evidence-conformance text-morphology-evaluation derivation-conformance derivation-evaluation nominal-conformance nominal-evaluation inflection-conformance inflection-evaluation discourse-conformance person-conformance construction-conformance unit-discovery-conformance progressive-unit-conformance recursive-bridge-conformance construction-evaluation discourse-evaluation arabic-coverage-holdout arabic-completion-oracle source-experiment text-evaluation arabic-evaluation governor-evaluation word-evaluation axioms inquiry-conformance classical-language-conformance arabic-inna-fragment-conformance
	$(PYTHON) tools/check_integrity.py

benchmark:
	$(PYTHON) tools/benchmark.py

.PHONY: classical-laws-conformance book-coverage
classical-laws-conformance:
	$(PYTHON) tools/check_classical_laws.py --lake $(LAKE) --output $(EVIDENCE_DIR)/classical-laws-conformance.json
	$(PYTHON) evidence/arabic_completion_v6/independent_review/run_benchmark.py --output $(EVIDENCE_DIR)/classical-independent-benchmark.json

book-coverage:
	$(PYTHON) tools/book_rule_coverage.py --check evidence/arabic_completion_v6/books/book_source_index_v1.json --summary $(EVIDENCE_DIR)/book-coverage.json

check: classical-laws-conformance book-coverage

demo:
	$(PYTHON) -m nabt analyse 'كَتَبَ'
	$(PYTHON) -m nabt count --weight 4 --mode waqf
	$(PYTHON) -m nabt generate --weight 4 --rank 0 --mode waqf

.PHONY: classical-language-conformance
classical-language-conformance:
	$(PYTHON) tools/check_classical_language_evidence.py --lake $(LAKE) --output $(EVIDENCE_DIR)/classical-language-conformance.json
	$(PYTHON) tools/classical_language_evidence.py audit --output $(EVIDENCE_DIR)/classical-language-sources.json

.PHONY: verified-reading-conformance
verified-reading-conformance:
	cd formal && $(LAKE) build verifiedReading
	test -x $(CURDIR)/formal/.lake/build/bin/verifiedReading
	NABT_VERIFIED_READING=$(CURDIR)/formal/.lake/build/bin/verifiedReading $(PYTHON) -B -m unittest discover -s tests -p test_verified_reading.py -v

check: verified-reading-conformance

.PHONY: source-semantics-conformance
source-semantics-conformance:
	cd formal && $(LAKE) build classicalSemanticProbe
	test -x $(CURDIR)/formal/.lake/build/bin/classicalSemanticProbe
	NABT_CLASSICAL_SEMANTIC_PROBE=$(CURDIR)/formal/.lake/build/bin/classicalSemanticProbe $(PYTHON) -B -m unittest discover -s tests -p test_source_semantics.py -v

check: source-semantics-conformance

.PHONY: mantuq-mafhum-conformance
mantuq-mafhum-conformance:
	cd formal && $(LAKE) build classicalSemanticProbe verifiedReading
	test -x $(CURDIR)/formal/.lake/build/bin/classicalSemanticProbe
	test -x $(CURDIR)/formal/.lake/build/bin/verifiedReading
	NABT_CLASSICAL_SEMANTIC_PROBE=$(CURDIR)/formal/.lake/build/bin/classicalSemanticProbe NABT_VERIFIED_READING=$(CURDIR)/formal/.lake/build/bin/verifiedReading $(PYTHON) -B -m unittest discover -s tests -p test_mantuq_mafhum.py -v
	NABT_CLASSICAL_SEMANTIC_PROBE=$(CURDIR)/formal/.lake/build/bin/classicalSemanticProbe $(PYTHON) -B -m unittest discover -s tests -p test_reading_enumeration.py -v
	NABT_CLASSICAL_SEMANTIC_PROBE=$(CURDIR)/formal/.lake/build/bin/classicalSemanticProbe $(PYTHON) -B -m unittest discover -s tests -p test_completion_semantic_integration.py -v

check: mantuq-mafhum-conformance

.PHONY: explainable-pilot explainable-pilot-conformance
explainable-pilot-conformance:
	cd formal && $(LAKE) build verifiedReading
	test -x $(CURDIR)/formal/.lake/build/bin/verifiedReading
	NABT_VERIFIED_READING=$(CURDIR)/formal/.lake/build/bin/verifiedReading $(PYTHON) -B -m unittest discover -s tests -p test_explainable_pilot.py -v

explainable-pilot: explainable-pilot-conformance
	$(PYTHON) tools/evaluate_explainable_pilot.py --output $(EVIDENCE_DIR)/explainable-pilot.json

check: explainable-pilot-conformance

.PHONY: certificate-training
certificate-training:
	$(PYTHON) tools/train_certificate_ranker.py --output-dir $(EVIDENCE_DIR)/certificate-training

.PHONY: qatr-reading-conformance
qatr-reading-conformance:
	cd formal && $(LAKE) build qatrReading
	NABT_QATR_READING=$(CURDIR)/formal/.lake/build/bin/qatrReading $(PYTHON) -B -m unittest discover -s tests -p test_qatr_readings.py -v

check: qatr-reading-conformance

.PHONY: productive-conformance productive-evaluation
productive-conformance:
	$(PYTHON) tools/check_productive_forms.py --lake $(LAKE)
productive-evaluation:
	$(PYTHON) tools/productive_evaluation.py --output $(EVIDENCE_DIR)/productive-evaluation.json
check: productive-conformance productive-evaluation

.PHONY: classical-extension-conformance classical-extension-evaluation
classical-extension-conformance:
	$(PYTHON) tools/check_imperative_paradigm.py --lake $(LAKE)
	$(PYTHON) tools/check_phonological_modes.py --lake $(LAKE)
	$(PYTHON) tools/check_classical_reference_readings.py --lake $(LAKE) --output $(EVIDENCE_DIR)/classical-reference-readings.json

classical-extension-evaluation:
	$(PYTHON) tools/classical_rule_inventory.py
	$(PYTHON) tools/imperative_paradigm_evaluation.py --output $(EVIDENCE_DIR)/imperative-paradigm.json

check: classical-extension-conformance classical-extension-evaluation
