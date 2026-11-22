.PHONY: io-gateway io-gateway-build io-gateway-native
.PHONY: relational-bridge
relational-bridge:
	LAKE="$(LAKE)" sh integrations/usul_ledger/check.sh
	PYTHONPATH=src:. NABT_REQUIRE_RELATIONAL_NATIVE=1 $(PYTHON) -m unittest tests.test_relational_bridge tests.test_ontological_continuity tests.test_relational_alignment tests.test_genus_chains tests.test_valency tests.test_named_matrix tests.test_usul_ledger tests.test_lineage_roles tests.test_masdar_frames tests.test_event_roles -v

check: relational-bridge

io-gateway:
	PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_ntp_recursive tests.test_ntp_cli tests.test_ntp_runtime_integration tests.test_ntp_learning_contract tests.test_report_draft tests.test_ntp_ifadah_learning tests.test_ntp_ifadah_gradients tests.test_io_gateway tests.test_relational_rag tests.test_lexical_ontolex tests.test_relational_root_sense tests.test_definition_network tests.test_interpretation_chains tests.test_question_cognition tests.test_question_answer_cycle tests.test_graded_questions tests.test_witness_recall tests.test_licensed_speech tests.test_partial_speech tests.test_graph_interventions tests.test_ntl_pr_integration tests.test_ntl_atlas tests.test_lesson_dispatch_regression tests.test_ntl_witness_pilot tests.test_ntl_curriculum tests.test_ntl_course tests.test_ntl_core tests.test_context_transfer tests.test_corpus_concepts tests.test_literal_event_roles tests.test_event_scene tests.test_derived_event_roles tests.test_pr113_regressions tests.test_ifadah_programs -v
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog gateway catalog --output $(EVIDENCE_DIR)/io-catalog.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog gateway run --request examples/io_gateway/contrast.json --output $(EVIDENCE_DIR)/io-contrast.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog gateway verify --request examples/io_gateway/contrast.json --receipt $(EVIDENCE_DIR)/io-contrast.json

io-gateway-build:
	cd formal && $(LAKE) build verifiedReading classicalSemanticProbe progressiveUnitProbe alignedAcquisition connectedAcquisitionV3 temporalContextProbe recursiveBridgeProbe epistemicMeasurement lexicalDenotation scopedCompositionProbe linguisticTruth updateMemoryProbe

.PHONY: ntl-course-check
ntl-course-check: io-gateway-build
	PYTHONPATH=src:. NABT_REQUIRE_IO_GATEWAY_NATIVE=1 $(PYTHON) -m unittest tests.test_lesson_dispatch_regression tests.test_ntl_witness_pilot tests.test_ntl_curriculum tests.test_ntl_course tests.test_ntl_core tests.test_context_transfer tests.test_corpus_concepts tests.test_literal_event_roles tests.test_event_scene tests.test_derived_event_roles tests.test_pr113_regressions tests.test_ifadah_programs -v

io-gateway-native: ntl-course-check
	PYTHONPATH=src:. NABT_REQUIRE_IO_GATEWAY_NATIVE=1 $(PYTHON) -m unittest tests.test_ntp_recursive tests.test_ntp_cli tests.test_ntp_runtime_integration tests.test_ntp_learning_contract tests.test_report_draft tests.test_ntp_ifadah_learning tests.test_ntp_ifadah_gradients tests.test_io_gateway tests.test_relational_rag tests.test_lexical_ontolex tests.test_relational_root_sense tests.test_definition_network tests.test_interpretation_chains tests.test_question_cognition tests.test_question_answer_cycle tests.test_graded_questions tests.test_witness_recall tests.test_licensed_speech tests.test_partial_speech tests.test_graph_interventions tests.test_ntl_pr_integration tests.test_ntl_atlas -v

test unit-composition-agent context-application: io-gateway-build
check: io-gateway-native

.PHONY: shared-cognition
shared-cognition: io-gateway-build
	cd formal && $(LAKE) build evidenceLifecycleV1
	PYTHONPATH=src:. NABT_REQUIRE_SHARED_NATIVE=1 $(PYTHON) -m unittest tests.test_shared_cognition tests.test_contextual_alignment tests.test_cognitive_graph -v

check: shared-cognition

.PHONY: cognitive-orchestration
cognitive-orchestration: io-gateway-build
	cd formal && $(LAKE) build exportCognitiveDispatch linguisticTruth
	PYTHONPATH=src:. NABT_REQUIRE_ORCHESTRATION_NATIVE=1 $(PYTHON) -m unittest tests.test_bootstrap_lean tests.test_cognitive_orchestration tests.test_usage_witness tests.test_source_neural_reading tests.test_text_reading tests.test_passive_gateway tests.test_passive_relation tests.test_passive_relation_holdout tests.test_passive_transfer tests.test_classical_role_attention -v
	PYTHONPATH=src:. $(PYTHON) -m tools.lexical_training.passive_source_audit
	PYTHONPATH=src:. $(PYTHON) tools/check_cognitive_dispatch.py --output $(EVIDENCE_DIR)/cognitive-dispatch.json

check: cognitive-orchestration

.PHONY: case-application
case-application: io-gateway-build
	cd formal && $(LAKE) build evidenceLifecycleV1
	PYTHONPATH=src:. NABT_REQUIRE_CASE_NATIVE=1 $(PYTHON) -m unittest tests.test_case_application -v
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog gateway run --request examples/io_gateway/case_application.json --output $(EVIDENCE_DIR)/case-application.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog gateway verify --request examples/io_gateway/case_application.json --receipt $(EVIDENCE_DIR)/case-application.json

check: case-application

.PHONY: scoped-composition
scoped-composition: io-gateway-build
	cd formal && $(LAKE) build evidenceLifecycleV1
	PYTHONPATH=src:. NABT_REQUIRE_COMPOSITION_NATIVE=1 $(PYTHON) -m unittest tests.test_scoped_composition tests.test_composition_explanation -v
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog gateway run --request examples/io_gateway/composition_quantifier.json --output $(EVIDENCE_DIR)/composition-quantifier.json
	PYTHONPATH=src:. $(PYTHON) -m tools.grammar_catalog gateway verify --request examples/io_gateway/composition_quantifier.json --receipt $(EVIDENCE_DIR)/composition-quantifier.json

check: scoped-composition

.PHONY: ifadah-programs
ifadah-programs:
	PYTHONPATH=src:. $(PYTHON) -B -m unittest tests.test_ifadah_programs tests.test_pr113_regressions -v

.PHONY: ntl-school-check
ntl-school-check:
	PYTHONPATH=src:. $(PYTHON) -B -m unittest tests.test_school_apprentice tests.test_school_ib_catalog tests.test_school_jordan_catalog tests.test_apprentice_readout tests.test_knowledge_assessment -v

io-gateway ntl-course-check: ntl-school-check

.PHONY: scoped-report-native
# Exercise these integrations with the original gateway/checker prerequisites.
scoped-report-native: io-gateway-build
	PYTHONPATH=src:. NABT_REQUIRE_IO_GATEWAY_NATIVE=1 $(PYTHON) -B -m unittest tests.test_ntp_recursive tests.test_io_gateway tests.test_relational_input_regression tests.post_segmentation_routing.test_ayat_al_dayn_routing tests.post_segmentation_routing.test_ayat_cognition tests.post_segmentation_routing.test_report_rank -v

check io-gateway-native: scoped-report-native

.PHONY: ntl-update-memory-check
ntl-update-memory-check: io-gateway-build
	PYTHONPATH=src:. NABT_REQUIRE_UPDATE_MEMORY_NATIVE=1 $(PYTHON) -m unittest tests.test_ntl_update_memory -v
	PYTHONPATH=src:. $(PYTHON) -m tools.lexical_training.train_update_memory --check

check io-gateway-native: ntl-update-memory-check

.PHONY: ntp-check
ntp-check:
	PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_ntp_recursive tests.test_ntp_cli tests.test_ntp_runtime_integration tests.test_ntp_learning_contract tests.test_report_draft tests.test_ntp_ifadah_learning tests.test_ntp_ifadah_gradients -v

.PHONY: nabt-comparison-check
nabt-comparison-check:
	PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_comparison_simulation -v
	PYTHONPATH=src:. $(PYTHON) -m tools.lexical_training.train_comparison_simulation --check

check: nabt-comparison-check

.PHONY: maqayis-matrix-check
maqayis-matrix-check:
	mkdir -p $(EVIDENCE_DIR)
	cd formal && $(LAKE) build lexicalDenotation
	PYTHONPATH=src:. $(PYTHON) -m unittest tests.test_morphology_matrix -v
	PYTHONPATH=src:. $(PYTHON) -m tools.ntp run --request examples/io_gateway/maqayis_concept_matrix.json --output $(EVIDENCE_DIR)/maqayis-matrix.json
	$(PYTHON) -c 'import json,sys; result=json.load(open(sys.argv[1]))["execution"]["owner_result"]["owner_result"]["morphology_matrix"]; assert result["common_indications"] == ["iltizam"], result["readings"][0]["denotation"]' $(EVIDENCE_DIR)/maqayis-matrix.json
	PYTHONPATH=src:. $(PYTHON) -m tools.ntp verify --request examples/io_gateway/maqayis_concept_matrix.json --receipt $(EVIDENCE_DIR)/maqayis-matrix.json

relational-bridge: maqayis-matrix-check
