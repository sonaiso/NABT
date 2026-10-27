#!/usr/bin/env python3
"""Independent frozen construction composition evaluation.

Gold is never supplied to NABT. Shared source/identity checks are derived from
our previously reviewed discourse evaluator, with new explicit schema adapters.
No production parser or law function is imported to decide expected outcomes.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import gzip
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import tarfile
import time
import traceback
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
_QUESTION_SPEC = importlib.util.spec_from_file_location(
    'independent_question_answer_validation', Path(__file__).with_name('question_answer_validation.py'))
question_validation = importlib.util.module_from_spec(_QUESTION_SPEC)
_QUESTION_SPEC.loader.exec_module(question_validation)
_GATE_SPEC = importlib.util.spec_from_file_location(
    'reviewed_arabic_coverage_gate', Path(__file__).with_name('arabic_coverage_gate.py'))
coverage_gate = importlib.util.module_from_spec(_GATE_SPEC)
_GATE_SPEC.loader.exec_module(coverage_gate)
_COMPLETION_SPEC = importlib.util.spec_from_file_location(
    'reviewed_arabic_completion_gate', Path(__file__).with_name('arabic_completion_gate.py'))
completion_gate = importlib.util.module_from_spec(_COMPLETION_SPEC)
_COMPLETION_SPEC.loader.exec_module(completion_gate)
_PRODUCTIVE_GATE_SPEC = importlib.util.spec_from_file_location(
    'productive_completion_gate', Path(__file__).with_name('arabic_completion_v4_gate.py'))
productive_gate = importlib.util.module_from_spec(_PRODUCTIVE_GATE_SPEC)
_PRODUCTIVE_GATE_SPEC.loader.exec_module(productive_gate)
_CLASSICAL_GATE_SPEC = importlib.util.spec_from_file_location(
    'classical_completion_gate', Path(__file__).with_name('arabic_completion_v5_gate.py'))
classical_gate = importlib.util.module_from_spec(_CLASSICAL_GATE_SPEC)
_CLASSICAL_GATE_SPEC.loader.exec_module(classical_gate)
_EXTENSION_GATE_SPEC = importlib.util.spec_from_file_location(
    'classical_extension_gate', Path(__file__).with_name('arabic_completion_v6_gate.py'))
extension_gate = importlib.util.module_from_spec(_EXTENSION_GATE_SPEC)
_EXTENSION_GATE_SPEC.loader.exec_module(extension_gate)
_FOUNDATION_GATE_SPEC = importlib.util.spec_from_file_location(
    'framework_foundation_gate', Path(__file__).with_name('framework_foundation_gate.py'))
foundation_gate = importlib.util.module_from_spec(_FOUNDATION_GATE_SPEC)
_FOUNDATION_GATE_SPEC.loader.exec_module(foundation_gate)
_SOURCE_SPEC = importlib.util.spec_from_file_location(
    'independent_source_witness_validation', Path(__file__).with_name('source_name_validation.py'))
source_validation = importlib.util.module_from_spec(_SOURCE_SPEC)
_SOURCE_SPEC.loader.exec_module(source_validation)
FOLDER = ROOT / 'evidence/constructions'
VERSION = 'nabt.constructions.independent-evaluation.v3'
GOLD_FREEZE_SHA256 = '5e4e9856b00ee648888e58c84e62c0a334cd3875d14cea326273d7c0f732254e'
SOURCE_ID = 'construction_authored_lexicon'
PINS = {
    '7f6b8ace539ec969ecb56939929ac982eb85e064e103a2bd90983bda583104f8': {'snapshot_sha256': 'da60d43f8f99c56cedaeca2c04133990ff22654faac5dfbeb3a64bc5a1209831', 'archive_sha256': 'e488e15b491c1d5087b797810d17befcfd79c9bfc7d6493e49d19c69704340eb', 'file_count': 104, 'version': '0.20.0a1'},
    '9f0eded8d010dcd349254adbc4cc4726c5c385aff53286dff37f3ba997fdca4b': {'snapshot_sha256': 'fa6a18a4b034433ef9d2dd2faf5754b1207b125b1d459831529344d2383b3d85', 'archive_sha256': '53a29f62b4a70382f05ccffaef5410b4f594ffd6260e51bf41e916f2df53f473', 'file_count': 104, 'version': '0.20.0a1'},
    'b3a6ddeaf65f0f3c1397a0c265ba3b21fe4dafc0b088498345789b257e4c8271': {'snapshot_sha256': '48f7f637cc489cb50cdc912fe167a7f30efbc200cd0559d199a1801e3111d607', 'archive_sha256': 'd65857512be35a17389dc69b5da5e4ba6b2b5d64f647f4bd49ab9ce2e862c4a5', 'file_count': 102, 'version': '0.20.0a1'},
    'ba748dfab327531e79bd0f35814c43e37501315faad9cfdce5835f3939fbec7b': {'snapshot_sha256': 'c913baa9667ce54ae5da2726cb622ecb55fec0557876038989c4c353af541d78', 'archive_sha256': '19471ac4523c0e829579e71df563ab6703f814101ee20c94c3c7331e14ca3a94', 'file_count': 102, 'version': '0.20.0a1'},
    'b184a00c3c19b3204b889f14567b042c987046e7698f657bf9586ff307f01cf5': {'snapshot_sha256': 'dba50fbcc16fae7bdf2046e56afa55f7daf2657b25b2c0cb7be486d664d9f188', 'archive_sha256': '8646f73fef57bd97428cc3686843a0f3c9e12f2cf850342c6462e507c232c8e9', 'file_count': 102, 'version': '0.20.0a1'},
    '1b49907b0b0ec2475113daa93366a6ec127b7b303c12d8e3313681c30bbdab0f': {'snapshot_sha256': '422ecda54cd92c27b1408feb2d6616eb4011dec751ee8754692eb1a16c08085b', 'archive_sha256': '16a6e83e0d8cffe5898789751a221053da1530119ec12871be52fc26e6968d01', 'file_count': 101, 'version': '0.20.0a1'},
    '1c47bfee3fa0baa190ec0e0455dfcb2528aec65a6280694956c1e00186948d30': {'snapshot_sha256': '8ea9f386852e40ae092ec9a0c9c37ae7a3c48d50468191038209511f156ac280', 'archive_sha256': 'd04ff4bf22171441e5731bfdb67dd4b4d6e6470db0e75b58977656d42e5172c2', 'file_count': 101, 'version': '0.20.0a1'},
    'a192d915f933a8f98ddb4d166f741be4ab976d34cc2c13be71eb940f08ca06e4': {'snapshot_sha256': '36fba6536d27a077bba568c024ac0eabb22c1defbaec17ae45c665083e361766', 'archive_sha256': '6da895ca88448dd9261f6acf0e5fe244fef311ef6dfe785acda9307a6b928598', 'file_count': 101, 'version': '0.20.0a1'},
    '00b06260322f06a6394b3a1164aa78833758a86f1c71c232433d1ab786077447': {'snapshot_sha256': '9f497aa3f3083d7e8073b77e21599445add23ef139b3c419372178be91a954e9', 'archive_sha256': '168c7a1a90761cb0d90c90f4f0f0f4ce80e955813448f7c519696b94b20c6f2f', 'file_count': 101, 'version': '0.20.0a1'},
    '31bd37d919364742033a08ab4cb557e93b92280539dd7a55364763cae236dfec': {'snapshot_sha256': '8d2e24747ee0a4ba454c1eaeb4936ba510945a24992653a47db9664348029d23', 'archive_sha256': '15bfc5ffdd08667cb79bf530d3b5baecd49f1c0493b8bf252f934b5fea55a922', 'file_count': 99, 'version': '0.20.0a1'},
    '06f4f774c5637936b41be95360b07ad6cfe8aaeaa9fee1514396db501112ce57': {'snapshot_sha256': '1ad20efd09752b7f66aae30ceeac1b442c5b520bcf494e528f8a9097bd5de68c', 'archive_sha256': 'a377cba60bfd1491351322b6543678e023ac83b18ec0cb2543f181f046d318ed', 'file_count': 94, 'version': '0.19.0a1'},
    'eda208c3e092a8185a3223ba8f0848ff6d0232aca3b8c3e94645482233d7dcb9': {'snapshot_sha256': '5338e35cd0575996e5df0f8d00a6319add42c610764ece7f8bc898d79a30e797', 'archive_sha256': '614377594215e73cc2ecd0e3b2ce12e19da64d4dd6f8f4aa4e55e5604ef52d43', 'file_count': 83, 'version': '0.18.0a1'},
    '40e6e10d95f444c5a1e1e6c72b4ff997d25a9d1a9caac5c0ff910b1551df677b': {'snapshot_sha256': '36e1e17ace7e5ebaac7b4ef1bb66a1ae8c9212d87f3c60c93c9660cbb9381862', 'archive_sha256': '7e5cfc227fd280ab5052c9cb8937799cde28bd8bf6037e9cd73a32013c842cea', 'file_count': 83, 'version': '0.18.0a1'},
    '045d6b3d6d3c2f6744b3157a2bd3cbf025b401e2efd215d8a4200182685978dd': {
        'snapshot_sha256': 'adb248f5e22007d4155448f77fe9d845ec1780c1032bb158d8f6d3d50d65964f',
        'archive_sha256': 'c1056d20779c557fd060787d5018c503128778712b81eb669881c89e4e7a0e84',
        'file_count': 80, 'version': '0.17.0a1',
    },
    'eeb9864b08e8ae25e841b18b0d25858d95268fce2435d51c340d69a41782f089': {
        'snapshot_sha256': 'fb14e51c7f7d751b13307ecf65573c1863c7f579252aa402231586aeda11412f',
        'archive_sha256': '8576765bdd5b9dbb93db76ec11b485634fa2f34691113a45d59dbf49238c0c87',
        'file_count': 80, 'version': '0.17.0a1',
    },
    '1818fc27f076535734d9d9e90a857683f27d464f0a205637e7231cd6e870c40c': {
        'snapshot_sha256': '46070144ca2e2fe7bcfb73292498fceebf669c6a8756c9ec771c6f4dee528851',
        'archive_sha256': '8446ae35115ba9eb1b332ea7395a7be9b1d1be9285073918d711a7466237b163',
        'file_count': 77,
        'version': '0.16.0a1',
    },
    'a7194b9b52ab8a6db0c92d65c7dae76dc23c1f1c8777b4e10b2fb71efa01c89f': {
        'snapshot_sha256': '602fe4a4d81044adbbd01849284f14c699f2104a36595db2bd6f8e80facf7804',
        'archive_sha256': '54452a9f9375caf4837b00156a98a1be3076b6bd9e4afa2980e8f3d73755e289',
        'file_count': 77,
        'version': '0.16.0a1',
    },
    '49a9c891446e945b74b28489f4abda522473093ada40e503e1fcd5ce99905f4b': {
        'snapshot_sha256': '97bae287bf823be44033a9e3c174647ed3abb6a15a214e6f4542ba2bb4cc6d64',
        'archive_sha256': 'fd1ed9ab3cc8b6b5f98c7b1e04f7bd9255cbc2abee0447cbf9a33f234e28a194',
        'file_count': 75, 'version': '0.15.0a1',
    },
    'cefe19d399b19e30175579e427272b790d24eab0e07b54b152e0cd3a45dc5dc4': {
        'snapshot_sha256': 'f4f56c8d8e5b8cf7260cb51fa5b87cd8952a2a746294e0050a072c5e3b17f79f',
        'archive_sha256': '19bc1ab5e1c78d3163cc0ff1af4c0acb85f71886ec8cc3973aeab23529ff5714',
        'file_count': 75, 'version': '0.15.0a1',
    },
    '42476d67e30e7e86506c3e878552966ce9dc784ae1e5d98bec3af50e6f0a1aa5': {
        'snapshot_sha256': '3a6e9594cf6b094ca6bfce61a4969e854604f5fc4520db90c793aa7fda0b4e58',
        'archive_sha256': '62d395428f49785c005ceaf55d86ed1e66cce12453d8ed2a03146436b5ba0567',
        'file_count': 74, 'version': '0.14.0a3',
    },
    '23d04d307c3e560c8198ee0700923673af001a8835d8e00d6c11d79534e6d611': {
        'snapshot_sha256': '2c1b6b30e22b5322046109b461f850974e356736f2aedb06c4911be82375188f',
        'archive_sha256': 'b5363658881c8e265295ad727d346ea8925348e9342b89f50eb014be824a19f1',
        'file_count': 74, 'version': '0.14.0a2',
    },
    'f1e035f7d20395abb82c2e87ac42f374630bef6bab71a22490873c7a08e8e519': {
        'snapshot_sha256': '2d79ea2227dda5169413eb314b9b65b5bc04fcacb447d00066ef56d3c7b69108',
        'archive_sha256': 'af7b88818f8d46a4d810927df39f1eb839c28dd7862f3919c3ac52f66abdbf8e',
        'file_count': 67, 'version': '0.13.0a2',
    },
    '96ffa98008bf1b6a6d1f5ab6b79a330fe4b8a9329887d9ac3f8ff9d31eb12e1e': {
        'snapshot_sha256': '87c7d5dc6c4aa5f46d42f7cd27a1595e2a2844af50da42a45a0f3b3bc09812b9',
        'archive_sha256': 'edaff6bb63863e10734993bbaf5101160dab3308b22e763ba188d89fa28e3575',
        'file_count': 74, 'version': '0.14.0a1',
    },
    '5d4bf3ec6331dab12ebc735f57203cf6bdbc86a563eae0311a66316eb8b820b1': {
        'snapshot_sha256': '1e9d906428ec3824c4ecbff8ef8fb3adc88d6cb6c9dbfa1819c53655b3206c7c',
        'archive_sha256': '9d5ec76ec904c3696d0e5a76e46fe435e9189322fe0578133c6816707b2fd2c5',
        'file_count': 74, 'version': '0.14.0a1',
    },
}
NON_RUNTIME = frozenset({'src/nabt/data/source_evidence/README.md',
                         'src/nabt/data/source_evidence/LICENSE-DATA.md',
                         'src/nabt/data/source_evidence/.gitattributes'})
EXPECTED_KEYS = frozenset('complete_construction_required required_roles required_relations required_claims required_scopes\nrequired_qualifications forbidden_claims questions no_grounded_claims required_force\nforbid_unique_cognitive_reading_from_lemma_alone forbid_bare_embedded_property\nno_categorical_linguistic_rejection preserve_idafa_chain_order forbid_activated_idafa\nhal_owner_candidates forbid_arbitrary_unique_hal_owner forbid_activated_hal\nforbid_activated_tamyiz required_relation_candidates forbid_context_identity_merge\nforbid_whole_from_part forbid_activated_badal_part forbid_arbitrary_unique_badal_reading\nforbid_activated_tawkeed replay'.split())
CLAIM_FIELDS = ('predicate', 'predicate_kind', 'voice', 'args', 'positive', 'tense', 'time', 'place', 'restriction')
CASE_VALUES = ('nasb', 'raf', 'jarr', 'jazm')
SIGNS = ('damma', 'fatha', 'kasra', 'sukun', 'waw', 'alif', 'ya', 'nun_retained', 'nun_deleted', 'weak_deleted')
ROLE_CASE = {
    'nominal_subject':'raf','nominal_predicate':'raf','active_subject':'raf','passive_subject':'raf',
    'direct_object':'nasb','inna_subject':'nasb','inna_predicate':'raf','kana_subject':'raf',
    'kana_predicate':'nasb','preposition_object':'jarr','idafa_complement':'jarr',
    'time_adverb':'nasb','place_adverb':'nasb','imperfect_indicative':'raf',
    'imperfect_subjunctive':'nasb','imperfect_jussive':'jazm','zanna_subject':'raf',
    'zanna_object1':'nasb','zanna_object2':'nasb','kada_subject':'raf','kada_predicate':'nasb',
    'hal':'nasb','tamyiz':'nasb','numeral_object':'nasb','numeral_subject':'raf',
}
INHERITED_ROLES = frozenset({'naat','badal','tawkeed'})
ROLE_ALIASES = {'zanna_subject':'active_subject'}
OPERATOR_FORMS = {
    'inna': frozenset({'إن','أن','كأن','لكن','ليت','لعل'}),
    'kana': frozenset({'كان','يكون','تكون','ليس','أصبح','أمسى','أضحى','بات','ظل','صار','زال','برح','فتئ','انفك','دام'}),
    'zanna': frozenset({'ظن','حسب','خال','زعم','رأى','وجد','علم','ألفى','جعل','عد','حجا','هب','درى','تعلم','ترك','وهب','اتخذ','اتخذ'}),
    'kada': frozenset({'كاد','كرب','أوشك','عسى','حرى','اخلولق','شرع','أخذ','طفق','جعل','أنشأ','علق','هب'}),
}
SCOPE_ALIASES = {'inception':'onset','belief':'epistemic','knowledge':'epistemic','proximity':'approximation'}
ASPECT_ALIASES = {'PERF':'perfect','IMPF':'imperfect','IMPV':'imperative'}
TIME_LABELS = {('يَوْم','اليوم',True):'اليوم',('أَمْس','أمس',False):'أمس',('غَد','غدا',False):'غدا'}
BOUNDARY_RUNTIME_SHA256 = '5d4bf3ec6331dab12ebc735f57203cf6bdbc86a563eae0311a66316eb8b820b1'
# Reviewed only after all three same-adapter runs and independent raw rescoring.
# These are coverage failures, not successful cases or exemptions from evidence.
DOCUMENTED_FAILURES = {
    'CON-Z02': frozenset('complete_construction role:0 role:1 role:2 roles_same_analysis relation:0 relations_same_analysis scope:0 coherent_analysis question:0 question:1'.split()),
    'CON-Z07': frozenset('complete_construction role:0 role:1 role:2 roles_same_analysis scope:0 coherent_analysis question:0 question:1'.split()),
    'CON-Z10': frozenset('complete_construction role:0 role:1 role:2 roles_same_analysis scope:0 coherent_analysis question:0 question:1'.split()),
    'CON-A07': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis scope:0 coherent_analysis question:0 question:1'.split()),
    'CON-D03': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relation:1 relations_same_analysis coherent_analysis question:0'.split()),
    'CON-N01': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-N02': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-H05': frozenset('complete_construction role:0 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-M01': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-M02': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-M03': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-B01': frozenset('relation_candidates'.split()),
    'CON-B02': frozenset('relation_candidates'.split()),
    'CON-W01': frozenset('qualification:0 coherent_analysis'.split()),
    'CON-W02': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0'.split()),
}

# Independently reviewed after the frozen v3 comparison; original v2 policy stays unchanged.
BOUNDARY_RUNTIME_V3_SHA256 = '23d04d307c3e560c8198ee0700923673af001a8835d8e00d6c11d79534e6d611'
DOCUMENTED_FAILURES_V3 = {
    'CON-Z02': frozenset('complete_construction role:0 role:1 role:2 roles_same_analysis relation:0 relations_same_analysis scope:0 coherent_analysis question:0 question:1'.split()),
    'CON-Z07': frozenset('complete_construction role:0 role:1 role:2 roles_same_analysis scope:0 coherent_analysis question:0 question:1'.split()),
    'CON-Z10': frozenset('complete_construction role:0 role:1 role:2 roles_same_analysis scope:0 coherent_analysis question:0 question:1'.split()),
    'CON-A07': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis scope:0 coherent_analysis question:0 question:1'.split()),
    'CON-D03': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relation:1 relations_same_analysis coherent_analysis question:0'.split()),
    'CON-N01': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-N02': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-H05': frozenset('complete_construction role:0 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-M01': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-M02': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-M03': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-B01': frozenset('relation_candidates'.split()),
    'CON-B02': frozenset('relation_candidates'.split()),
    'CON-W01': frozenset('qualification:0 coherent_analysis'.split()),
    'CON-W02': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0'.split()),
}

# v4 reviewed separately after complete same-adapter strict replay and raw rescoring.
BOUNDARY_RUNTIME_V4_SHA256 = '42476d67e30e7e86506c3e878552966ce9dc784ae1e5d98bec3af50e6f0a1aa5'
RATIONAL_INQUIRY_BOUNDARY_RUNTIME_SHA256 = 'cefe19d399b19e30175579e427272b790d24eab0e07b54b152e0cd3a45dc5dc4'
RATIONAL_INQUIRY_V2_BOUNDARY_RUNTIME_SHA256 = '49a9c891446e945b74b28489f4abda522473093ada40e503e1fcd5ce99905f4b'
DOCUMENTED_FAILURES_V4 = {
    'CON-Z02': frozenset('complete_construction role:0 role:1 role:2 roles_same_analysis relation:0 relations_same_analysis scope:0 coherent_analysis question:0 question:1'.split()),
    'CON-Z07': frozenset('complete_construction role:0 role:1 role:2 roles_same_analysis scope:0 coherent_analysis question:0 question:1'.split()),
    'CON-Z10': frozenset('complete_construction role:0 role:1 role:2 roles_same_analysis scope:0 coherent_analysis question:0 question:1'.split()),
    'CON-A07': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis scope:0 coherent_analysis question:0 question:1'.split()),
    'CON-D03': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relation:1 relations_same_analysis coherent_analysis question:0'.split()),
    'CON-N01': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-N02': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-H05': frozenset('complete_construction role:0 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-M01': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-M02': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-M03': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0 question:1'.split()),
    'CON-B01': frozenset('relation_candidates'.split()),
    'CON-B02': frozenset('relation_candidates'.split()),
    'CON-W01': frozenset('qualification:0 coherent_analysis'.split()),
    'CON-W02': frozenset('complete_construction role:0 role:1 roles_same_analysis relation:0 relations_same_analysis qualification:0 coherent_analysis question:0'.split()),
}

DOCUMENTED_BOUNDARY_POLICIES = {
    BOUNDARY_RUNTIME_SHA256: DOCUMENTED_FAILURES,
    BOUNDARY_RUNTIME_V3_SHA256: DOCUMENTED_FAILURES_V3,
    BOUNDARY_RUNTIME_V4_SHA256: DOCUMENTED_FAILURES_V4,
    # Reuse exactly the reviewed v4 debt; the inquiry extension adds no waiver.
    RATIONAL_INQUIRY_BOUNDARY_RUNTIME_SHA256: DOCUMENTED_FAILURES_V4,
    RATIONAL_INQUIRY_V2_BOUNDARY_RUNTIME_SHA256: DOCUMENTED_FAILURES_V4,
}

def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def digest(value):
    return sha256(wire(value)).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def capture_code(snapshot, output):
    path = output.with_suffix('.code.tar.gz')
    require(not path.exists(), 'Refusing to replace code archive')
    with tarfile.open(path, 'w:gz') as saved:
        for n, item in enumerate(snapshot['files']):
            base = Path(snapshot['runtime_root']) if n < snapshot['runtime_file_count'] else ROOT
            data = (base / item['path']).read_bytes()
            require(sha256(data).hexdigest() == item['sha256'], 'Code changed while capturing measurement')
            member = tarfile.TarInfo(item['path'])
            member.size, member.mode, member.mtime = len(data), 0o644, 0
            saved.addfile(member, io.BytesIO(data))
    return {'filename': path.name, 'sha256': sha256(path.read_bytes()).hexdigest()}

def finalize_raw_log(path, material, result, written_inventory=None):
    """Reopen the closed gzip and reconcile every record with this attempt.

    A compressed-file hash alone cannot distinguish a completed evidence log
    from a consistently hashed truncated one.  This check includes gzip CRC and
    EOF validation, canonical JSON, complete case/question/error inventories,
    and exact scores.  New attempts also bind every line to its write-time hash.
    """
    payload = path.read_bytes()
    decoded = gzip.decompress(payload)
    require(decoded.endswith(b'\n'), 'Raw log lacks its final record terminator')
    lines = decoded.splitlines(keepends=True)
    records, inventory = [], []
    for index, line in enumerate(lines):
        value = json.loads(line.decode('utf-8'))
        require(type(value) is dict and wire(value) + b'\n' == line,
                'Raw log record is not canonical JSON')
        records.append(value)
        inventory.append({'index': index, 'bytes': len(line), 'sha256': sha256(line).hexdigest(),
                          'kind': 'model' if 'model_summary' in value else 'case',
                          'id': value.get('id')})
    if written_inventory is not None:
        require(inventory == written_inventory, 'Raw log differs from the records written during this attempt')
    require(records and records[0] == {'model_summary': result['model_summary'],
            'source_sha256': result['source_sha256']}, 'Raw model/source record mismatch')
    expected_cases = material['cases']
    expected_ids = [case['id'] for case in expected_cases]
    require(len(expected_ids) == len(set(expected_ids)), 'Expected raw case IDs are not unique')
    require([entry['id'] for entry in result['cases']] == expected_ids,
            'Result case inventory differs from frozen material')
    case_records = records[1:]
    require([entry.get('id') for entry in case_records] == expected_ids,
            'Raw case inventory differs from frozen material')
    execution_errors, question_errors = [], []
    question_count = skipped_questions = 0
    for case, record, scored in zip(expected_cases, case_records, result['cases'], strict=True):
        require(set(record) == {'id', 'report', 'questions', 'verification', 'replay', 'score'},
                'Unexpected raw case record fields')
        require(wire(record['score']) == wire(scored), 'Raw score differs from recorded result: ' + case['id'])
        failures = [failure['details'] for failure in scored['failures'] if failure['check'] == 'execution']
        require(len(failures) <= 1, 'Multiple execution failures for one raw case')
        execution_errors.extend(failures)
        questions = record['questions']
        require(type(questions) is list, 'Raw questions must be an ordered list')
        expected_count = len(case['expected'].get('questions', []))
        if len(questions) != expected_count:
            require(not questions and len(failures) == 1 and failures[0]['stage'] in ('read', 'verify'),
                    'Raw question inventory is incomplete without an early execution failure')
            skipped_questions += expected_count
        question_count += len(questions)
        for index, question in enumerate(questions):
            if 'error' in question:
                require(set(question) == {'error'}, 'Question error has conflicting successful output')
                question_errors.append({'id': case['id'], 'index': index, **question['error']})
            else:
                require(set(question) == {'answer', 'inquiry', 'verification'}, 'Raw question evidence is incomplete')
    require(wire(execution_errors) == wire(result['execution_errors']), 'Raw execution error inventory mismatch')
    require(wire(question_errors) == wire(result['question_execution_errors']), 'Raw question error inventory mismatch')
    expected_questions = sum(len(case['expected'].get('questions', [])) for case in expected_cases)
    require(question_count + skipped_questions == expected_questions, 'Raw question total mismatch')
    return {'filename': path.name, 'sha256': sha256(payload).hexdigest(), 'bytes': len(payload),
            'decoded_sha256': sha256(decoded).hexdigest(), 'decoded_bytes': len(decoded),
            'complete_gzip_verified': True, 'canonical_json_verified': True,
            'write_time_inventory_verified': written_inventory is not None,
            'record_count': len(records), 'case_count': len(case_records),
            'case_ids': expected_ids, 'question_count': question_count,
            'expected_question_count': expected_questions, 'early_failure_skipped_questions': skipped_questions,
            'execution_error_count': len(execution_errors), 'question_error_count': len(question_errors),
            'record_inventory': inventory, 'record_inventory_sha256': digest(inventory)}

def verify_import_origins(runtime_root):
    for name, module in sys.modules.items():
        if name == 'nabt' or name.startswith('nabt.'):
            path = getattr(module, '__file__', None)
            require(path is None or Path(path).resolve().is_relative_to((runtime_root / 'src').resolve()),
                    'Cross-runtime import: ' + name)

class SourceAudit:
    def __init__(self, raw, exclusions=(), source_id='qac'):
        self.raw, self.sha, self.source_id = raw, sha256(raw).hexdigest(), source_id
        self.exclusions = set(exclusions)
        self.records, offset, ordinal = {}, 0, 0
        self.verified = set()
        for line in raw.splitlines(keepends=True):
            end = offset + len(line)
            if line.startswith(b'('):
                ordinal += 1
                fields = line.rstrip(b'\r\n').decode().split('\t')
                locator = list(map(int, fields[0].strip('()').split(':')))
                self.records[(offset, end)] = {'ordinal': ordinal, 'locator': locator,
                    'form': fields[1], 'tag': fields[2], 'tokens': fields[3].split('|')}
            offset = end

    def receipt(self, value):
        start, end = value['byte_start'], value['byte_end']
        require(type(start) is int and type(end) is int, 'Receipt byte bounds must be exact integers')
        row = self.records.get((start, end))
        require(row is not None, 'Receipt does not cover a complete raw QAC record')
        require(value['source_id'] == self.source_id and value['source_sha256'] == self.sha,
                'Receipt source identity mismatch')
        require(type(value['ordinal']) is int and value['ordinal'] == row['ordinal']
                and value['locator'] == row['locator'], 'Receipt locator/ordinal mismatch')
        require(':'.join(map(str, row['locator'][:2])) not in self.exclusions, 'Excluded verse used as evidence')
        expected_id = digest(['nabt.corpus-source.v1', 'qac', self.source_id, self.sha, start, end, row['ordinal']])
        require(value['record_id'] == expected_id, 'Receipt identity mismatch')
        return row

    def walk(self, value):
        if isinstance(value, dict):
            if {'record_id', 'byte_start', 'byte_end', 'source_id'} <= set(value):
                key = wire(value)
                if key not in self.verified:
                    self.receipt(value)
                    self.verified.add(key)
            for item in value.values():
                self.walk(item)
        elif isinstance(value, list):
            for item in value:
                self.walk(item)

def span_bounds(span):
    if type(span) is not dict:
        raise ValueError('A current-source span is missing')
    a, b = span['start'], span['end']
    require(type(a) is int and type(b) is int and 0 <= a < b, 'Invalid byte span')
    return a, b

def check_span(span, inputs, surface=None):
    raw = inputs['text'].encode()
    a, b = span_bounds(span)
    require(b <= len(raw) and span['source_id'] == inputs['source_id']
            and span['source_sha256'] == sha256(raw).hexdigest(), 'Span borrowed another source')
    observed = raw[a:b].decode('utf-8')
    require(surface is None or observed == surface, 'Span does not restore observed surface')
    return observed

def reading_rows(report):
    rows = {}
    ranges = defaultdict(set)
    for occurrence in report.get('occurrences', []):
        for row in occurrence.get('readings', []):
            rid = row['reading_id']
            require(rid not in rows or rows[rid] == row, 'One reading ID names different evidence')
            rows[rid] = row
            ranges[rid].add(span_bounds(occurrence['span']))
    for row in report.get('derived_readings', []):
        rid = row['reading_id']
        require(rid not in rows or rows[rid] == row, 'Derived reading ID collision')
        rows[rid] = row
        ranges[rid].add(span_bounds(row['stem_span']))
    return rows, ranges

def claim_is_in_analysis(claim, analysis):
    return any(claim_key(claim) == claim_key(c) for c in analysis.get('claims', []))

def context_form_compatible(surface, declared):
    """Independent conservative comparison of written letters and shared marks.

    Missing marks do not invent a different name. Only the published wasl/alif
    correspondence changes a letter; the final case mark is not name identity.
    """
    def clusters(text):
        result = []
        for char in text:
            if unicodedata.combining(char):
                if not result:
                    return []
                result[-1][1].add(char)
            else:
                result.append(['ا' if char == 'ٱ' else char, set()])
        return result
    observed, named = clusters(surface), clusters(declared)
    if not observed or len(observed) != len(named) or [x[0] for x in observed] != [x[0] for x in named]:
        return False
    vowels = set('ًٌٍَُِْ')
    for (_, left), (_, right) in zip(observed[:-1], named[:-1]):
        lm, rm = left & vowels, right & vowels
        if lm and rm and lm != rm:
            return False
        # The published source lookup profile is asymmetric for these marks:
        # explicit observed shadda/dagger alif needs the same declared mark.
        if ('ّ' in left and 'ّ' not in right) or ('ٰ' in left and 'ٰ' not in right):
            return False
    if ('ّ' in observed[-1][1] and 'ّ' not in named[-1][1]) or ('ٰ' in observed[-1][1] and 'ٰ' not in named[-1][1]):
        return False
    return True

def validate_reference_origin(ref, inputs, entities, *, analysis=None, rows=None, audit=None, model_summary=None):
    origin, ids = ref['origin'], set(ref.get('candidate_entity_ids', []))
    context = inputs.get('context') or {}
    correspondence = ref.get('name_correspondence')
    if correspondence is not None:
        source_validation.validate_name_correspondence(ref, inputs, entities, analysis=analysis,
            rows=rows, audit=audit, model_summary=model_summary)
    if origin == 'named':
        possible = {eid for eid, entity in entities.items()
                    if context_form_compatible(ref['surface'], entity['name']) or
                    correspondence is not None and source_validation.unvocalized_label_compatible(
                        ref['surface'], entity['name'])}
    elif origin in ('speaker', 'addressee'):
        possible = {context[origin]} if origin in context else set()
    elif origin == 'deictic':
        possible = {eid for item in context.get('deixis', [])
                    if context_form_compatible(ref['surface'], item['form']) for eid in item['entity_ids']}
    else:
        return
    profile = ref.get('profile', {})
    possible = {eid for eid in possible if all(
        profile.get(field) in (None, 'unknown') or entities[eid].get(field) in (None, 'unknown')
        or profile[field] == entities[eid][field] for field in ('gender', 'number'))}
    require(ids == possible, 'Reference candidates contradict their original context/name/participant premise')

def validate_reference_prefix(ref, previous_clauses, context):
    # v1/v2 did not expose this field. Their complete replay remains pinned;
    # v3 adds an independently checkable receipt for the prior source prefix.
    if 'source_prefix_complete' not in ref:
        return
    complete = not any(c['status'] == 'DEFER' for c in previous_clauses)
    require(ref['source_prefix_complete'] is complete, 'Reference prefix receipt contradicts previous source clauses')
    if ref['origin'] == 'antecedent':
        closed = bool(context.get('closed_reference_scope', False)) and complete
        require(ref['closed_scope'] is closed, 'Antecedent closed scope ignores an incomplete source prefix')
        require(complete or ref.get('bound_entity_id') is None,
                'Antecedent reference resolved across an incomplete source prefix')

def nun_span_valid(nun, inputs):
    try:
        surface = check_span(nun['span'], inputs, nun.get('surface'))
        if not surface.startswith('ن') or any(not unicodedata.combining(c) for c in surface[1:]):
            return False
        a, b = span_bounds(nun['span'])
        suffix = inputs['text'].encode()[b:].decode()
        return not suffix or not unicodedata.combining(suffix[0])
    except (ValueError, KeyError, TypeError, UnicodeError):
        return False

def instantiate(pattern, bindings):
    result = claim_view(pattern)
    used = set()
    for field in ('args', 'time', 'place'):
        for i, value in enumerate(result[field]):
            if type(value) is str and value.startswith('?'):
                require(value in bindings, 'Proof omitted a query variable')
                result[field][i] = deepcopy(bindings[value])
                used.add(value)
    require(used == set(bindings), 'Proof adds an unrequested binding')
    return result

def validate_answer(answer, document, inquiry, inputs, question):
    require(answer['source_text'] == inputs['text'] and answer['question_text'] == question
            and answer['scope'] == inputs['scope'] and answer['source_id'] == inputs['source_id'],
            'Answer changed the actual source/question/scope')
    require(answer['source_sha256'] == document['source_sha256'] and answer['question_sha256'] == inquiry['source_sha256']
            and answer['document_report_id'] == document['report_id'] and answer['question_report_id'] == inquiry['report_id']
            and answer['context_sha256'] == document['context']['sha256'], 'Answer report identity mismatch')
    require(answer['answer_id'] == digest({k: v for k, v in answer.items() if k != 'answer_id'}),
            'Answer content identity mismatch')
    require(answer['world_truth'] == 'NOT_ESTABLISHED', 'Answer promoted world truth')
    require(answer['status'] in ('SUPPORTED', 'REFUTED', 'CONFLICT', 'UNKNOWN', 'DEFER', 'OUT_OF_SCOPE'),
            'Unknown answer status')
    if answer.get('schema') == 'nabt.discourse-answer.v2' or 'question_interpretations' in answer:
        question_validation.validate_interpretations(answer, document, inquiry, inputs, claim_view=claim_view)
        return
    if answer['proofs'] or answer['counterproofs'] or answer['bindings']:
        require(document['status'] == 'LICENSED_DISCOURSE' and inquiry['status'] == 'LICENSED_DISCOURSE',
                'Grounded answer requires complete document and question reports')
    accepted = {c['claim_id']: c for c in document['claims']}
    entities = {e['id']: e for e in (inputs.get('context') or {}).get('entities', [])}
    if answer['query'] is not None:
        require(len(inquiry['clauses']) == 1 and inquiry['clauses'][0]['status'] == 'LICENSED',
                'Query has no complete original-question reading')
        clause = inquiry['clauses'][0]
        viable = [a for a in clause['analyses'] if not a['rejected_candidate']]
        require(viable and all(a['force'] == 'QUESTION' and claim_is_in_analysis(answer['query'], a) for a in viable),
                'Answer query differs from the original question/force')
        require(all((a.get('question_kind') or 'polar') == answer['kind'] for a in viable),
                'Answer kind differs from the original question reading')
        variables = {value for field in ('args', 'time', 'place') for value in answer['query'][field]
                     if type(value) is str and value.startswith('?')}
        variable_by_kind = {'polar': set(), 'person': {'?person'}, 'subject': {'?person'}, 'object': {'?object'},
                            'place': {'?place'}, 'time': {'?time'}}
        require(answer['kind'] in variable_by_kind and variables == variable_by_kind[answer['kind']],
                'Question kind and variable domain disagree')
    else:
        require(answer['kind'] is None and not answer['proofs'] and not answer['counterproofs']
                and not answer['bindings'], 'Unparsed question acquired an answer type/evidence')
    for sign in ('proofs', 'counterproofs'):
        for proof in answer[sign]:
            require(proof['claim_id'] in accepted and answer['query'] is not None, 'Answer proof is not an accepted source claim')
            claim = accepted[proof['claim_id']]
            require(proof['document_report_id'] == document['report_id'] and proof['question_report_id'] == inquiry['report_id']
                    and proof['source_proofs'] == claim['proofs'], 'Answer proof borrowed another query/source')
            wanted = instantiate(answer['query'], proof['bindings'])
            for variable, value in proof['bindings'].items():
                if variable in ('?person', '?place'):
                    require(type(value) is str and entities.get(value, {}).get('kind') == variable[1:],
                            'Question binding lacks its declared person/place domain')
            if sign == 'counterproofs':
                wanted['positive'] = not wanted['positive']
            require(wire(wanted) == claim_key(claim), 'Answer proof dropped or changed a qualified claim field')
    grouped = {}
    for sign in ('proofs', 'counterproofs'):
        for proof in answer[sign]:
            group = grouped.setdefault(wire(proof['bindings']), {'proofs': [], 'counterproofs': []})
            group[sign].append(proof)
    wanted_groups = {key for key, value in grouped.items() if value['proofs']}
    actual_groups = [wire(binding['values']) for binding in answer['bindings']]
    if answer['kind'] == 'polar':
        require(not actual_groups, 'Polar answer invented variable bindings')
    elif answer['query'] is not None:
        require(set(actual_groups) == wanted_groups and len(actual_groups) == len(wanted_groups),
                'Variable answer omitted or duplicated a proved binding group')
    for binding in answer['bindings']:
        require(binding['proofs'], 'Returned binding has no positive proof')
        group = grouped[wire(binding['values'])]
        require(all(Counter(map(wire, binding[sign])) == Counter(map(wire, group[sign]))
                    for sign in ('proofs', 'counterproofs')), 'Variable binding changed its complete proof group')
        wanted_status = 'CONFLICT' if group['counterproofs'] else 'SUPPORTED'
        require(binding['status'] == wanted_status, 'Variable binding status contradicts its own proof signs')
    supported, refuted = bool(answer['proofs']), bool(answer['counterproofs'])
    if answer['status'] == 'SUPPORTED':
        require(supported and (answer['kind'] != 'polar' or not refuted), 'Supported status lacks clean support')
    if answer['status'] == 'REFUTED':
        require(refuted and not supported, 'Refuted status lacks the requested opposition')
    if answer['status'] == 'CONFLICT':
        require(supported and refuted, 'Conflict status lacks both signs')
    if answer['status'] in ('DEFER', 'OUT_OF_SCOPE'):
        require(not supported and not refuted and not answer['bindings'], 'Unknown/deferred answer contains accepted evidence')
    if answer['status'] == 'UNKNOWN':
        require(not supported and not answer['bindings'] and (answer['kind'] != 'polar' or not refuted),
                'Unknown answer contains a supported binding or settled polar conclusion')
    if answer['kind'] not in (None, 'polar') and answer['bindings']:
        wanted_status = 'CONFLICT' if any(b['status'] == 'CONFLICT' for b in answer['bindings']) else 'SUPPORTED'
        require(answer['status'] == wanted_status, 'Variable answer status contradicts its binding groups')


def letters(value):
    """Written letters for the closed operator vocabulary only; no hamza fold."""
    return ''.join(c for c in value if not unicodedata.combining(c))


def claim_view(row, *, embedded=False):
    require(type(row) is dict and all(k in row for k in CLAIM_FIELDS), 'Claim omits qualification fields')
    require(type(row['positive']) is bool and row['predicate_kind'] in ('property','event','location','scoped'),
            'Invalid claim domain')
    require(type(row['predicate']) is str and row['voice'] in (None,'active','passive'), 'Invalid predicate/voice')
    domain = ('unspecified','past','nonpast','future') + (('relative_to_operator','relative_nonpast') if embedded else ())
    require(row['tense'] in domain, 'Invalid or escaped relative tense')
    require(all(type(row[k]) is list for k in ('args','time','place','restriction')), 'Claim sequences required')
    # Incomplete analyses retain unresolved argument slots as null. Such slots
    # are never accepted as grounded claims or complete query participants.
    require(all(a is None or type(a) is str or question_validation.constrained_person_argument(a)
                for a in row['args']), 'Claim argument identity required')
    if any(question_validation.constrained_person_argument(a) for a in row['args']):
        require(row['predicate_kind'] == 'property' and row['voice'] is None and len(row['args']) == 1,
                'Typed person argument escaped its single-subject property domain')
    for t in row['time']:
        require(type(t) is str or (type(t) is dict and set(t) == {'lemma','form','source_article'}
            and type(t['lemma']) is str and type(t['form']) is str and type(t['source_article']) is bool),
            'Invalid qualified time representation')
    for q in row['restriction']:
        if type(q) is dict and q.get('kind') == 'operator_scope':
            require(row['predicate_kind'] == 'scoped' and q.get('embedded_fact_projection') is False,
                    'Operator scope projects a bare embedded fact')
            require(type(q.get('embedded')) is list and q['embedded'], 'Operator lacks its embedded proposition')
            for child in q['embedded']:
                claim_view(child, embedded=True)
    if row['predicate_kind'] == 'scoped':
        require(sum(type(q) is dict and q.get('kind') == 'operator_scope' for q in row['restriction']) == 1,
                'Scoped claim lost or duplicated its governing operator')
    return {k:deepcopy(row[k]) for k in CLAIM_FIELDS}


def claim_key(row):
    return wire(claim_view(row))


def gold_time(value):
    if type(value) is dict and set(value) == {'lemma','form','source_article'}:
        return TIME_LABELS.get((value['lemma'],value['form'],value['source_article']), deepcopy(value))
    return {'يَوْم':'اليوم','أَمْس':'أمس','غَد':'غدا','غدًا':'غدا'}.get(value,value) if type(value) is str else value


def semantic_key(row, *, embedded=False):
    value = claim_view(row, embedded=embedded)
    value['time'] = [gold_time(t) for t in value['time']]
    return wire(value)


def bound_at(analysis, span):
    return {r.get('bound_entity_id') for r in analysis['references'] if r['span'] == span and r.get('bound_entity_id') is not None}


def assignment_case(assignment, analysis):
    role = assignment['role']
    if role in ROLE_CASE:
        return ROLE_CASE[role]
    require(role in INHERITED_ROLES, 'Unknown role in output: '+str(role))
    heads = [a for a in analysis['assignments'] if a is not assignment and a['span'] == assignment.get('head_span')]
    cases = {a['required_case'] for a in heads}
    require(len(cases) == 1 and next(iter(cases)) in CASE_VALUES, 'Dependent role lacks a unique same-analysis inherited case')
    return next(iter(cases))


def validate_carrier(row, inputs, audit=None):
    carrier = row.get('nominal_case_carrier')
    if not carrier:
        return
    if carrier.get('rule') == 'productive_accusative_alif':
        spec = importlib.util.spec_from_file_location('independent_productive_validation',
                                                     Path(__file__).with_name('productive_form_validation.py'))
        validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        validator.validate_nominal(row, inputs, audit)
        return
    require(carrier.get('generated_form') is False and carrier.get('rule') == 'attested_accusative_alif',
            'Carrier bridge invented an unobserved form')
    base = check_span(carrier['base_span'], inputs, carrier['base_surface'])
    suffix = check_span(carrier['carrier_span'], inputs, carrier['carrier_surface'])
    a,b = span_bounds(carrier['base_span']); c,d = span_bounds(carrier['carrier_span'])
    require(b == c and (a,d) == span_bounds(row['stem_span']) and suffix == 'ا'
            and base + suffix == row['stem_surface'], 'Carrier span does not conserve its complete source word')
    require(letters(base) == letters(row['lexical_features']['lemma']) and base.endswith('ً'),
            'Carrier bridge does not witness the same lexical base and tanwin')
    require(carrier.get('full_form_supports') and len(carrier.get('base_paradigm_supports',[])) >= 2,
            'Carrier lacks full-form and independent paired-base receipts')
    if audit:
        audit.walk(carrier)


def validate_relations(analysis, rows, inputs):
    """Validate identity/attachments without using runtime tables or parser helpers."""
    ca,cb = span_bounds(analysis['span'])
    assignments = analysis['assignments']
    refs = {r['reference_id']:r for r in analysis['references']}
    for relation in analysis.get('relations',[]):
        require(type(relation) is dict and type(relation.get('kind')) is str, 'Malformed relation')
        for field, value in relation.items():
            if field.endswith('_span') or field == 'span':
                if value is not None:
                    check_span(value, inputs)
                    a,b = span_bounds(value)
                    require(ca <= a < b <= cb, 'Relation endpoint escaped its analysis')
            if field.endswith('_reading_id'):
                require(value in analysis['reading_ids'] and value in rows, 'Relation borrowed another reading')
        kind = relation['kind']
        if kind == 'operator':
            family = relation.get('family')
            require(family in OPERATOR_FORMS and relation.get('scope_preserved') is True,
                    'Operator relation lost its declared family/scope')
            head = check_span(relation['head_span'], inputs)
            row = rows[relation['operator_reading_id']]
            require(span_bounds(row['stem_span']) == span_bounds(relation['head_span']), 'Operator reading moved to another occurrence')
            lemma = row.get('lexical_features',{}).get('lemma')
            require((letters(lemma or head) == relation['lemma'] or letters(head) == relation['lemma'])
                    and relation['lemma'] in OPERATOR_FORMS[family], 'Operator lemma is not its source reading')
            require(relation.get('aspect') == row.get('lexical_features',{}).get('aspect'),
                    'Operator aspect is not its lexical source')
            if family == 'kada':
                require(relation.get('local_case') == 'nasb' and relation.get('case_domain') == 'clause_local_case',
                        'Kada clause lost its local case')
                inner = [a for a in assignments if a['span'] == relation.get('internal_verb_span')
                         and a['role'] in ('imperfect_indicative','imperfect_subjunctive')]
                require(inner and all(a['required_case'] == relation.get('internal_verb_required_case') for a in inner),
                        'Clause case replaced the independent inner verb case')
                ref = refs.get(relation.get('internal_subject_reference'))
                require(ref is not None and ref['span'] == relation.get('subject_span'), 'Complement subject return borrowed another reference')
        for side, key in [('head','head_reading_id'),('dependent','dependent_reading_id'),('owner','owner_reading_id')]:
            if key in relation:
                span = relation.get(side+'_span')
                if span is not None:
                    a,b = span_bounds(span); sa,sb = span_bounds(rows[relation[key]]['stem_span'])
                    require(a <= sa < sb <= b, 'Relation reading is detached from its endpoint')
        if 'owner_reference' in relation:
            ref = refs.get(relation['owner_reference'])
            require(ref is not None and ref['span'] == relation.get('owner_span'), 'Modifier owner borrowed another reference')
        if 'complement_reference' in relation:
            ref = refs.get(relation['complement_reference'])
            require(ref is not None and ref['span'] == relation.get('complement_span'), 'Idafa complement borrowed another reference')
        if kind == 'tawkeed' and relation.get('subtype') == 'semantic_self' and relation.get('identity_preserved'):
            pronouns = [r for r in analysis['references'] if r['span'] == relation.get('pronoun_span')]
            owners = bound_at(analysis, relation.get('head_span'))
            require(pronouns and owners and all(r.get('bound_entity_id') in owners for r in pronouns),
                    'Emphasis pronominal return differs from its emphasized owner')


def validate_claim_roles(claim, analysis, rows, ranges, *, embedded_family=None):
    assignments, refs = analysis['assignments'], analysis['references']
    if any(question_validation.constrained_person_argument(value) for value in claim['args']):
        require(embedded_family is None and question_validation.typed_question_claim_supported(claim, analysis, rows),
                'Typed question claim lacks its own pending interrogative adjective edge')
        return
    def at(argument,span):
        if argument is None:
            return (analysis['references_complete'] is False and
                    any(r['span']==span and r.get('bound_entity_id') is None for r in refs))
        return argument in bound_at(analysis,span)
    kind = claim['predicate_kind']
    if kind == 'scoped':
        scope = next(q for q in claim['restriction'] if type(q) is dict and q.get('kind') == 'operator_scope')
        operators = [r for r in analysis['relations'] if r.get('kind') == 'operator'
                     and all(r.get(k) == scope.get(k) for k in ('family','lemma','sense','aspect'))]
        require(operators and claim['predicate'] == '@operator:'+scope['lemma'] and claim['voice'] is None,
                'Scoped claim changed its governing operator')
        require(len(claim['args']) == 1 and any(at(claim['args'][0],r['subject_span']) for r in operators),
                'Scoped claim changed its matrix participant')
        for child in scope['embedded']:
            validate_claim_roles(child, analysis, rows, ranges, embedded_family=scope['family'])
        return
    if kind in ('property','location'):
        predicate_roles = {'nominal_predicate','inna_predicate','kana_predicate'}
        subject_roles = {'nominal_subject','inna_subject','kana_subject'}
        if embedded_family == 'zanna':
            predicate_roles, subject_roles = {'zanna_object2'}, {'zanna_object1'}
        require(len(claim['args']) == 1 and claim['voice'] is None, 'Property/location argument or voice mismatch')
        subjects = [a for a in assignments if a['role'] in subject_roles and at(claim['args'][0],a['span'])]
        require(subjects, 'Property/location argument is not its bound subject-role reference')
        if kind == 'location':
            require(claim['predicate'] == '@located' and claim['place'], 'Location lacks qualified place')
        else:
            predicates = [a for a in assignments if a['role'] in predicate_roles
                and rows[a['reading_id']].get('lexical_features',{}).get('lemma') == claim['predicate']]
            require(predicates, 'Claim predicate is not its predicate-role lexical reading')
            require(any(p.get('head_span') == s['span'] if p['role'] == 'nominal_predicate'
                        else p.get('head_span') == s.get('head_span') for p in predicates for s in subjects),
                    'Predicate and subject do not share their own governing frame')
        return
    require(kind == 'event' and claim['voice'] in ('active','passive'), 'Invalid event kind/voice')
    for rid in analysis['reading_ids']:
        row = rows[rid]; feat = row.get('lexical_features',{})
        if row['kind'] != 'verb' or feat.get('lemma') != claim['predicate'] or (feat.get('voice') or 'active') != claim['voice']:
            continue
        if embedded_family == 'kada':
            operators = [r for r in analysis['relations'] if r.get('kind') == 'operator' and r.get('family') == 'kada'
                         and r.get('internal_verb_span') == row['stem_span']]
            if len(claim['args']) == 1 and any(at(claim['args'][0],r['subject_span']) for r in operators):
                return
            continue
        roles = {'active_subject' if claim['voice'] == 'active' else 'passive_subject'}
        subjects = [a for a in assignments if a['role'] in roles and a.get('head_span') is not None
                    and span_bounds(a['head_span']) in ranges[rid]]
        objects = [a for a in assignments if a['role'] in ('direct_object','numeral_object') and a.get('head_span') is not None
                   and span_bounds(a['head_span']) in ranges[rid]]
        if len(subjects) > 1 or len(objects) > 1 or len(claim['args']) != 1+len(objects):
            continue
        actor = (subjects and at(claim['args'][0],subjects[0]['span'])) or (
            not subjects and any(at(claim['args'][0],r['span']) and span_bounds(r['span']) in ranges[rid] for r in refs))
        if actor and (not objects or at(claim['args'][1],objects[0]['span'])):
            return
    raise ValueError('Event predicate and arguments do not share their governing source readings')


def validate_new_sense_receipts(analysis, rows, inputs, audit):
    for relation in analysis.get('relations', []):
        if 'independent_sense_witness' in relation:
            source_validation.validate_sense_witness(relation, analysis, rows, inputs, audit)
        elif (relation.get('kind') == 'operator' and relation.get('family') == 'zanna'
              and relation.get('lemma') == 'حسب' and analysis.get('licensed_syntax')):
            require(False, 'Licensed hasiba sense omitted its independent raw/source witness')


def validate_report(report, inputs, audit=None):
    raw = inputs['text'].encode()
    require(report['source_text'] == inputs['text'] and report['source_id'] == inputs['source_id']
        and report['source_sha256'] == sha256(raw).hexdigest() and report['scope'] == inputs['scope'], 'Report changed original input identity')
    require(report['world_truth'] == 'NOT_ESTABLISHED', 'Report promoted source claims to world truth')
    require(report['report_id'] == digest({k:v for k,v in report.items() if k != 'report_id'}), 'Report hash mismatch')
    context = report['context']['value']; supplied = inputs.get('context') or {}
    require(digest(context) == report['context']['sha256'], 'Context hash mismatch')
    entities = {e['id']:e for e in supplied.get('entities',[])}
    require({e['id'] for e in context['entities']} == set(entities), 'Context invented or discarded an entity')
    for e in context['entities']:
        require(e == {'gender':'unknown','number':'unknown','kind':'unknown',**entities[e['id']]}, 'Context traits changed')
    require(all(context.get(k) == supplied.get(k) for k in ('speaker','addressee')), 'Context participants changed')
    require(context['deixis'] == supplied.get('deixis',[]) and context['closed_reference_scope'] is supplied.get('closed_reference_scope',False),
            'Context reference scope changed')
    cursor=0; expected_ranges=[]
    for segment in report['partition']:
        a,b=span_bounds(segment['span']);require(a==cursor,'Partition has a gap/overlap')
        check_span(segment['span'],inputs,segment['surface']);cursor=b
        if segment['kind'] in ('written_run','quotation'):expected_ranges.append((a,b))
    require(cursor==len(raw) and [span_bounds(o['span']) for o in report['occurrences']]==expected_ranges, 'Source occurrence inventory changed')
    rows,ranges=reading_rows(report)
    for occurrence in report['occurrences']:check_span(occurrence['span'],inputs,occurrence['surface'])
    for row in rows.values():
        if 'stem_span' in row:check_span(row['stem_span'],inputs,row['stem_surface'])
        else:require(row.get('kind')=='particle' and row.get('operator_qualified') is True,'Lexical reading has no source stem')
        for part in row.get('segmentation',{}).get('parts',[]):check_span(part['span'],inputs,part['surface'])
        validate_carrier(row,inputs,audit)
        if 'nominal_paradigm_correspondence' in row or row.get('construction_basis') == 'same_form_nominal_independent_pair':
            source_validation.validate_nominal_correspondence(row, inputs, audit)
        for nun in row.get('nun_readings',[]):
            if nun.get('realization')=='deleted':require(nun.get('span') is None,'Deleted nun fabricated a span')
            if nun.get('realization')=='present':require(nun_span_valid(nun,inputs),'Visible nun lost complete cluster identity')
    analyses={}
    for clause in report['clauses']:
        check_span(clause['span'],inputs)
        require(clause['clause_id']==digest({k:v for k,v in clause.items() if k!='clause_id'}),'Clause hash mismatch')
        previous=[c for c in report['clauses'] if span_bounds(c['span'])[1]<=span_bounds(clause['span'])[0]]
        if clause['status']=='LICENSED':
            viable=[a for a in clause['analyses'] if not a['rejected_candidate']]
            require(viable and all(a['licensed_syntax'] and a['references_complete'] and a['force']==clause['force'] for a in viable),
                    'Licensed clause contains an incomplete viable alternative')
            require(len({wire([claim_view(c) for c in a['claims']]) for a in viable})==1,
                    'Licensed clause discarded a disagreeing proposition alternative')
        for analysis in clause['analyses']:
            aid=analysis['analysis_id'];require(aid==digest({k:v for k,v in analysis.items() if k!='analysis_id'}),'Analysis hash mismatch')
            require(aid not in analyses,'Duplicate analysis ID');analyses[aid]=(clause,analysis)
            check_span(analysis['span'],inputs)
            require(all(rid in rows for rid in analysis['reading_ids']),'Dangling analysis reading')
            for ref in analysis['references']:
                check_span(ref['span'],inputs,ref.get('written_surface',ref.get('surface')))
                if 'nominal_carrier_reading_id' in ref:
                    carrier_row=rows.get(ref['nominal_carrier_reading_id'])
                    require(carrier_row is not None and carrier_row['reading_id'] in analysis['reading_ids']
                        and carrier_row['stem_span']==ref['span'] and carrier_row.get('nominal_case_carrier',{}).get('base_surface')==ref['surface'],
                        'Named reference borrowed a carrier from another reading')
                ids=ref.get('candidate_entity_ids',[]);bound=ref.get('bound_entity_id')
                require(len(ids)==len(set(ids)) and set(ids)<=set(entities),'Reference invented candidate IDs')
                if ref.get('origin')=='question_variable':require(type(bound) is str and bound.startswith('?'),'Invalid question variable')
                else:
                    require(ref['scope']==inputs['scope'] and ref['context_sha256']==report['context']['sha256'],'Reference scope/context mismatch')
                    require(bound is None or ids==[bound],'Bound reference is not the sole candidate')
                    require(ref['reference_id']==digest({k:v for k,v in ref.items() if k!='reference_id'}),'Reference hash mismatch')
                    validate_reference_origin(ref, inputs, entities, analysis=analysis, rows=rows, audit=audit,
                        model_summary=report.get('lexical_model'));validate_reference_prefix(ref,previous,supplied)
            for assigned in analysis['assignments']:
                rid=assigned['reading_id'];require(rid in analysis['reading_ids'],'Assignment borrowed another reading')
                row=rows[rid];wanted=assignment_case(assigned,analysis)
                require(assigned['required_case']==wanted,'Role/case law mismatch')
                check_span(assigned['span'],inputs,assigned['surface']);a,b=span_bounds(assigned['span']);sa,sb=span_bounds(row['stem_span'])
                require(a<=sa<sb<=b,'Assignment changed its lexical occurrence')
                if assigned.get('head_span') is not None:
                    check_span(assigned['head_span'],inputs);ha,hb=span_bounds(assigned['head_span']);ca,cb=span_bounds(clause['span'])
                    require(ca<=ha<hb<=cb,'Assignment governor escaped its clause')
                    if assigned['role'].startswith(('kana_','inna_','zanna_','kada_')):
                        family=assigned['role'].split('_')[0]
                        require(letters(raw[ha:hb].decode()) in OPERATOR_FORMS[family],'Operator role has a wrong governor')
                if assigned.get('activated'):
                    require(analysis['licensed_syntax'] and not analysis['rejected_candidate'] and assigned.get('actual_role')==assigned['role'],
                            'Role activated through an unlicensed analysis')
                else:require(assigned.get('actual_role') is None and assigned.get('inflected_case') is None and assigned.get('local_case') is None,
                             'Unactivated assignment acquired an actual conclusion')
                actual,local=assigned.get('inflected_case'),assigned.get('local_case')
                require(actual is None or row.get('construction')=='inflected' and actual==wanted and assigned.get('case_domain')=='inflected_case'
                        and assigned['sign_candidates'],'Actual case lacks its reading/sign/domain')
                require(local is None or row.get('construction')=='built' and local==wanted and assigned.get('case_domain') in ('local_case','clause_local_case'),
                        'Local case/domain mismatch')
                for sign in assigned['sign_candidates']:
                    require(type(sign['case']) is int and 0<=sign['case']<4 and CASE_VALUES[sign['case']]==wanted,'Sign belongs to another case')
                    require(type(sign['sign']) is int and 0<=sign['sign']<len(SIGNS) and SIGNS[sign['sign']]==sign['sign_name'],'Sign code/name mismatch')
            validate_relations(analysis,rows,inputs)
            validate_new_sense_receipts(analysis, rows, inputs, audit)
            for claim in analysis['claims']:
                claim_view(claim);validate_claim_roles(claim,analysis,rows,ranges)
                if analysis['assertion_allowed']:
                    require(analysis['force']=='ASSERT' and analysis['licensed_syntax'] and analysis['references_complete']
                            and not analysis['rejected_candidate'],'Nonassertive or incomplete analysis asserted')
    for claim in report['claims']:
        claim_view(claim);require(all(type(a) is str and a in entities for a in claim['args']),'Claim invented an entity')
        require(claim['proofs'],'Grounded claim has no source proof')
        for proof in claim['proofs']:
            require(proof['analysis_id'] in analyses,'Claim proof has a dangling analysis')
            clause,analysis=analyses[proof['analysis_id']]
            require(proof['clause_id']==clause['clause_id'] and proof['span']==clause['span'] and clause['status']=='LICENSED'
                and analysis['assertion_allowed'] and claim_is_in_analysis(claim,analysis),'Claim proof borrowed another force/source')
            viable=[a for a in clause['analyses'] if not a['rejected_candidate']]
            require(viable and all(a['licensed_syntax'] and a['references_complete'] and claim_is_in_analysis(claim,a) for a in viable),
                    'Unresolved or disagreeing alternative was discarded to assert')
    if audit:audit.walk(report)
    return rows,ranges,analyses


def word_anchors(text):
    # The frozen material uses Arabic words separated by spaces plus final
    # punctuation. This is an independent source span inventory, not a parser.
    return [{'surface':m.group(), 'span':[len(text[:m.start()].encode()),len(text[:m.end()].encode())]}
            for m in re.finditer(r'[\u0621-\u065f\u0670\u0671]+',text)]


def anchor_matches(expected, actual, row=None):
    wanted=tuple(expected['span']);got=span_bounds(actual)
    if got==wanted:return True
    return bool(row is not None and expected.get('span_basis')=='occurrence_or_licensed_stem'
                and row.get('segmentation',{}).get('licensed') is True
                and got==span_bounds(row['stem_span']) and wanted[0]<=got[0]<got[1]<=wanted[1])


def role_matches(expected, assigned, analysis, rows):
    row=rows[assigned['reading_id']]
    if ROLE_ALIASES.get(assigned['role'],assigned['role'])!=expected['role'] or not assigned.get('activated'):
        return False
    if not anchor_matches(expected,assigned['span'],row):return False
    if assigned.get('actual_role')!=assigned['role'] or assigned['required_case']!=expected['case']:return False
    domain=expected.get('case_domain','inflected')
    if domain=='inflected':
        if assigned.get('inflected_case')!=expected['case'] or assigned.get('case_domain')!='inflected_case':return False
        if not any(s['sign_name']==expected['sign'] and CASE_VALUES[s['case']]==expected['case'] for s in assigned['sign_candidates']):return False
    elif domain=='local_clause':
        if assigned.get('local_case')!=expected['case'] or assigned.get('case_domain')!='clause_local_case':return False
    else:raise ValueError('Unimplemented gold role domain: '+domain)
    if 'governor' in expected:
        heads=[]
        if assigned.get('head_span') is not None:
            head_span=assigned['head_span']
            heads.append((head_span,None))
            # A licensed stem can satisfy the declared occurrence-or-stem
            # anchor only through this analysis's actual head assignment.
            heads.extend((head_span,rows[a['reading_id']]) for a in analysis['assignments']
                         if a['span']==head_span and a.get('activated') is True
                         and a.get('actual_role')==a['role']
                         and a['reading_id'] in analysis['reading_ids'] and a['reading_id'] in rows)
        # The public nominal-subject assignment has no governor. Its reciprocal
        # predicate assignment explicitly names this subject, so use that edge.
        if assigned['role']=='nominal_subject':
            heads.extend((a['span'],rows[a['reading_id']]) for a in analysis['assignments']
                         if a['role']=='nominal_predicate' and a.get('head_span')==assigned['span']
                         and a['reading_id'] in analysis['reading_ids'] and a['reading_id'] in rows)
        if not any(anchor_matches(expected['governor'],h,row) for h,row in heads):return False
    return True


def relation_rows(analysis):
    """Explicit edges in the public relations or assignment head/span fields."""
    rows=[]
    for relation in analysis.get('relations',[]):
        kind=relation['kind']
        if kind=='operator' and relation.get('family')=='zanna' and 'object1_span' in relation:
            rows.append({**relation,'kind':'zanna_predication','head_span':relation['object1_span'],
                         'dependent_span':relation['object2_span'],'governor_span':relation['head_span']})
        elif kind=='operator' and relation.get('family')=='kada':
            rows.append({**relation,'kind':'clausal_predicate','dependent_span':relation['internal_verb_span'],
                         'clause_span':relation['complement_span']})
        else:
            row=deepcopy(relation)
            if 'dependent_span' not in row and 'complement_span' in row:row['dependent_span']=row['complement_span']
            rows.append(row)
    for a in analysis['assignments']:
        if a.get('head_span') is not None and a['role']=='preposition_object':
            rows.append({'kind':'preposition_object','head_span':a['head_span'],'dependent_span':a['span'],
                         'dependent_reading_id':a['reading_id'],'from_explicit_assignment':True})
    return rows


def relation_matches(expected, relation, analysis, rows, anchors):
    if relation.get('kind')!=expected['kind'] or 'head_span' not in relation or 'dependent_span' not in relation:return False
    hrow=rows.get(relation.get('head_reading_id'));drow=rows.get(relation.get('dependent_reading_id'))
    if not anchor_matches(expected['head'],relation['head_span'],hrow) or not anchor_matches(expected['dependent'],relation['dependent_span'],drow):return False
    for name in ('governor','owner','target'):
        if name+'_word_index' in expected:
            target=anchors[expected[name+'_word_index']]
            span=relation.get(name+'_span')
            if span is None and name=='target':
                # A nisba relation's target is its explicitly governed subject,
                # not an invented anonymous target attached by the scorer.
                matches=[a['span'] for a in analysis['assignments'] if a['role'] in ('active_subject','passive_subject') and a.get('head_span')==relation['head_span']]
                if not any(anchor_matches(target,s) for s in matches):return False
            elif span is None or not anchor_matches(target,span):return False
    if 'owner_id' in expected and expected['owner_id'] not in bound_at(analysis,relation.get('owner_span')):return False
    if 'coreference_id' in expected:
        owner=expected['coreference_id']
        if owner not in bound_at(analysis,relation['head_span']):return False
        if relation.get('subtype')=='semantic_self' and owner not in bound_at(analysis,relation.get('pronoun_span')):return False
        if relation.get('identity_preserved') is not True:return False
    if expected.get('case_domain')=='local_clause':
        if relation.get('case_domain')!='clause_local_case' or relation.get('local_case')!=expected['clause_case']:return False
        clause_span=relation.get('clause_span')
        if clause_span is None:return False
        start=anchors[expected['clause_start_word_index']]['span'][0]
        if span_bounds(clause_span)!=(start,expected['dependent']['span'][1]):return False
        if expected['subject_return_id'] not in bound_at(analysis,relation.get('subject_span')):return False
        matching=[a for a in analysis['assignments'] if a['role']=='kada_predicate' and a['span']==clause_span and a.get('activated')
                  and a.get('local_case')==expected['clause_case'] and a.get('case_domain')=='clause_local_case']
        if not matching:return False
    return True


def embedded_matches(expected, actual, outer, scope):
    wanted=claim_view(expected,embedded=True);got=claim_view(actual,embedded=True)
    wanted['time']=[gold_time(t) for t in wanted['time']];got['time']=[gold_time(t) for t in got['time']]
    # Representation correspondence inside an explicit operator scope only.
    # This is never used for source/query proof equality or top-level facts.
    if wanted['tense']=='nonpast' and got['tense']=='relative_nonpast' and scope['family']=='kada':got['tense']='nonpast'
    if wanted['tense']=='unspecified' and (got['tense']=='relative_to_operator' or
        scope['family'] in ('kana','inna') and got['tense']==outer['tense']):got['tense']='unspecified'
    return wire(wanted)==wire(got)


def scope_matches(expected, claim):
    if claim.get('predicate_kind')!='scoped':return False
    for scope in claim['restriction']:
        if type(scope) is not dict or scope.get('kind')!='operator_scope':continue
        if SCOPE_ALIASES.get(scope.get('sense'),scope.get('sense'))!=expected['family']:continue
        operator=expected.get('operator_lemma',expected.get('operator_surface'))
        if operator is not None and letters(operator)!=scope.get('lemma'):continue
        if 'operator_aspect' in expected and ASPECT_ALIASES.get(scope.get('aspect'),scope.get('aspect'))!=expected['operator_aspect']:continue
        if claim['args']!=expected['matrix_args'] or claim['positive'] is not expected.get('positive',True):continue
        if expected.get('operator_aspect')=='perfect' and claim['tense']!='past':continue
        if 'trigger_surface' in expected and expected['family']!='continuation':continue
        if scope.get('embedded_fact_projection') is not False:continue
        if len(scope.get('embedded',[]))==1 and embedded_matches(expected['embedded'],scope['embedded'][0],claim,scope):return True
    return False


def walk_qualifiers(value):
    if type(value) is dict:
        if 'kind' in value:yield value
        for item in value.values():yield from walk_qualifiers(item)
    elif type(value) is list:
        for item in value:yield from walk_qualifiers(item)


def prepositional_tawkeed_owner_matches(owner, qualifier, claim, analysis, rows, anchors,
                                       relations, verbs, *, scope, context_sha256):
    """Prove the owner is this event's explicitly qualified PP object.

    Event arguments stay unchanged. An arbitrary qualifier, a reference from
    another clause, or a same-lemma noun elsewhere cannot supply this link.
    The caller first performs full report validation, including inherited case.
    """
    if (type(owner) is not str or type(scope) is not str or type(context_sha256) is not str
            or claim['predicate_kind']!='event' or qualifier.get('kind')!='tawkeed'
            or qualifier.get('owner')!=owner or qualifier not in claim['restriction']
            or analysis.get('rejected_candidate') is not False or analysis.get('licensed_syntax') is not True
            or analysis.get('references_complete') is not True or analysis.get('assertion_allowed') is not True
            or analysis.get('force')!='ASSERT' or not claim_is_in_analysis(claim,analysis)
            or not any(p.get('analysis_id')==analysis['analysis_id'] and p.get('span')==analysis['span']
                       for p in claim.get('proofs',[]))):
        return False
    span=analysis['span'];start,end=span_bounds(span)
    def local(location):
        return (type(location) is dict and location.get('source_id')==span.get('source_id')
                and location.get('source_sha256')==span.get('source_sha256')
                and start<=location.get('start',-1)<location.get('end',-1)<=end)
    def resolved(reference,location):
        return (reference.get('status')=='RESOLVED' and reference.get('bound_entity_id')==owner
                and reference.get('candidate_entity_ids')==[owner] and reference.get('span')==location
                and reference.get('scope')==scope and reference.get('context_sha256')==context_sha256
                and local(location) and reference.get('reference_id')==digest({
                    k:v for k,v in reference.items() if k!='reference_id'}))
    def surface(location):
        if not local(location):return None
        a,b=span_bounds(location)
        matches=[anchor['surface'].encode()[a-anchor['span'][0]:b-anchor['span'][0]].decode()
                 for anchor in anchors if anchor['span'][0]<=a<b<=anchor['span'][1]]
        return matches[0] if len(matches)==1 else None
    pp_qualifiers=[q for q in claim['restriction'] if type(q) is dict
                   and q.get('kind')=='prepositional' and q.get('object')==owner]
    for relation in relations:
        if (relation.get('kind')!='tawkeed' or relation.get('identity_preserved') is not True
                or relation.get('subtype')!=qualifier.get('subtype')):
            continue
        head_id,dependent_id=relation.get('head_reading_id'),relation.get('dependent_reading_id')
        head_span,dependent_span=relation.get('head_span'),relation.get('dependent_span')
        if (head_id not in analysis['reading_ids'] or dependent_id not in analysis['reading_ids']
                or head_id not in rows or dependent_id not in rows or not local(head_span) or not local(dependent_span)
                or rows[head_id].get('kind')!='noun'
                or rows[dependent_id].get('lexical_features',{}).get('lemma')!=qualifier.get('predicate')):
            continue
        if relation.get('subtype')=='semantic_self':
            pronoun_span=relation.get('pronoun_span')
            if not any(resolved(ref,pronoun_span) for ref in analysis['references']):continue
        for pp in analysis.get('relations',[]):
            if (pp.get('kind')!='preposition_object' or pp.get('dependent_reading_id')!=head_id
                    or pp.get('dependent_span')!=head_span or not local(pp.get('head_span'))):
                continue
            references=[ref for ref in analysis['references'] if ref.get('reference_id')==pp.get('object_reference')]
            if len(references)!=1 or not resolved(references[0],head_span):continue
            objects=[a for a in analysis['assignments'] if a['role']=='preposition_object'
                     and a['reading_id']==head_id and a['span']==head_span and a.get('head_span')==pp['head_span']
                     and a.get('activated') is True and a.get('actual_role')=='preposition_object'
                     and a.get('required_case')=='jarr']
            dependents=[a for a in analysis['assignments'] if a['role']=='tawkeed'
                        and a['reading_id']==dependent_id and a['span']==dependent_span
                        and a.get('head_span')==head_span and a.get('activated') is True
                        and a.get('actual_role')=='tawkeed' and a.get('required_case')=='jarr']
            if not objects or not dependents:continue
            prep_surface=surface(pp['head_span'])
            if prep_surface is None:continue
            for attachment in analysis.get('relations',[]):
                if (attachment.get('kind')!='prepositional_attachment'
                        or attachment.get('dependent_span')!=pp['head_span']
                        or attachment.get('object_span')!=head_span
                        or not any(attachment.get('head_span')==verb['stem_span'] for verb in verbs)):
                    continue
                if any(type(q.get('preposition')) is str and letters(q['preposition'])==letters(prep_surface)
                       and q.get('semantic_relation')==attachment.get('interpretation') for q in pp_qualifiers):
                    return True
    return False


def qualification_matches(expected, claim, analysis, rows, anchors, *, scope=None, context_sha256=None):
    dep=anchors[expected['dependent_word_index']];head=anchors[expected['head_word_index']]
    rels=[r for r in relation_rows(analysis) if r.get('kind')==expected['kind'] and r.get('dependent_span') is not None
          and anchor_matches(dep,r['dependent_span'],rows.get(r.get('dependent_reading_id')))]
    if not rels:return False
    dependent_rows=[rows[rid] for rid in analysis['reading_ids'] if 'stem_span' in rows[rid]
                    and dep['span'][0]<=span_bounds(rows[rid]['stem_span'])[0]<span_bounds(rows[rid]['stem_span'])[1]<=dep['span'][1]]
    if not any(r.get('lexical_features',{}).get('lemma')==expected['dependent_lemma'] for r in dependent_rows):return False
    owner=expected.get('owner_id')
    if expected['kind']=='idafa':
        rels=[r for r in rels if anchor_matches(head,r['head_span'])]
        if not rels or owner not in claim['args']:return False
        dependents={eid for r in rels for eid in bound_at(analysis,r['dependent_span'])}
        matched=any(q.get('kind')=='idafa' and q.get('complement') in dependents for q in walk_qualifiers(claim['restriction']))
    else:
        verbs=[rows[rid] for rid in analysis['reading_ids'] if rows[rid].get('kind')=='verb'
               and anchor_matches(head,rows[rid]['stem_span']) and rows[rid].get('lexical_features',{}).get('lemma')==claim['predicate']]
        if not verbs:return False
        matched=False
        for q in walk_qualifiers(claim['restriction']):
            if q.get('kind')!=expected['kind'] or q.get('predicate',q.get('lemma'))!=expected['dependent_lemma']:continue
            declared_owner=q.get('owner',q.get('target',q.get('entity')))
            if declared_owner is not None and declared_owner!=owner:continue
            if expected['kind']=='hal':
                if not any(owner in bound_at(analysis,r.get('owner_span')) for r in rels):continue
            elif expected['kind']=='naat':
                if not any(owner in bound_at(analysis,r.get('head_span')) for r in rels):continue
            elif expected['kind']=='tamyiz' and owner not in claim['args']:continue
            elif expected['kind']=='tawkeed' and owner not in claim['args']:
                if not prepositional_tawkeed_owner_matches(owner,q,claim,analysis,rows,anchors,rels,verbs,
                                                           scope=scope,context_sha256=context_sha256):continue
            matched=True
    if expected.get('required_time') is not None and [gold_time(t) for t in claim['time']]!=expected['required_time']:return False
    return matched


def score_case(case, report, questions, verification, audit=None, replay=None):
    expected=case['expected'];inputs=case['input'];checks=[];failures=[];false=[]
    def check(name,ok,details=None,safety=False):
        row={'check':name,'passed':bool(ok)}
        if details is not None:row['details']=details
        checks.append(row)
        if not ok:
            failures.append(row)
            if safety:false.append(row)
    rows,ranges,analyses=validate_report(report,inputs,audit)
    anchors=word_anchors(inputs['text']);claims=report['claims']
    check('report_replay',verification.get('valid') is True)
    viable=[a for _,a in analyses.values() if not a['rejected_candidate']]
    complete=[a for c,a in analyses.values() if c['status']=='LICENSED' and a['licensed_syntax'] and a['references_complete'] and not a['rejected_candidate']]
    active=[a for a in viable if a['licensed_syntax']]
    if expected.get('complete_construction_required'):
        check('complete_construction',bool(complete) and report['status']=='LICENSED_DISCOURSE')
    if expected.get('required_roles'):
        for i,r in enumerate(expected['required_roles']):
            check('role:'+str(i),any(any(role_matches(r,a,analysis,rows) for a in analysis['assignments']) for analysis in active))
        check('roles_same_analysis',any(all(any(role_matches(r,a,analysis,rows) for a in analysis['assignments']) for r in expected['required_roles']) for analysis in active))
    if expected.get('required_relations'):
        for i,r in enumerate(expected['required_relations']):
            check('relation:'+str(i),any(any(relation_matches(r,a,analysis,rows,anchors) for a in relation_rows(analysis)) for analysis in active))
        check('relations_same_analysis',any(all(any(relation_matches(r,a,analysis,rows,anchors) for a in relation_rows(analysis)) for r in expected['required_relations']) for analysis in active))
    for i,wanted in enumerate(expected.get('required_claims',[])):
        check('claim:'+str(i),any(semantic_key(wanted)==semantic_key(c) for c in claims))
    for i,wanted in enumerate(expected.get('required_scopes',[])):
        def triggered(claim,analysis):
            if 'trigger_surface' not in wanted:return True
            operators=[r for r in analysis['relations'] if r.get('kind')=='operator' and r.get('sense')==wanted['family']]
            return any(i>0 and anchors[i-1]['surface']==wanted['trigger_surface']
                for r in operators for i,a in enumerate(anchors) if tuple(a['span'])==span_bounds(r['head_span']))
        check('scope:'+str(i),any(scope_matches(wanted,c) and any(triggered(c,analyses[p['analysis_id']][1]) for p in c['proofs']) for c in claims))
    for i,wanted in enumerate(expected.get('required_qualifications',[])):
        check('qualification:'+str(i),any(qualification_matches(wanted,c,analyses[p['analysis_id']][1],rows,anchors,
            scope=inputs['scope'],context_sha256=report['context']['sha256']) for c in claims for p in c['proofs']))
    for i,forbidden in enumerate(expected.get('forbidden_claims',[])):
        check('forbidden_claim:'+str(i),not any(semantic_key(forbidden)==semantic_key(c) for c in claims),safety=True)
    if expected.get('no_grounded_claims'):check('no_grounded_claims',not claims,safety=True)
    if expected.get('complete_construction_required'):
        def coherent(analysis):
            accepted=[c for c in claims if any(p['analysis_id']==analysis['analysis_id'] for p in c['proofs'])]
            return (all(any(role_matches(r,a,analysis,rows) for a in analysis['assignments']) for r in expected.get('required_roles',[]))
                and all(any(relation_matches(r,t,analysis,rows,anchors) for t in relation_rows(analysis)) for r in expected.get('required_relations',[]))
                and all(any(semantic_key(w)==semantic_key(c) for c in accepted) for w in expected.get('required_claims',[]))
                and all(any(scope_matches(w,c) for c in accepted) for w in expected.get('required_scopes',[]))
                and all(any(qualification_matches(w,c,analysis,rows,anchors,
                    scope=inputs['scope'],context_sha256=report['context']['sha256']) for c in accepted)
                    for w in expected.get('required_qualifications',[])))
        check('coherent_analysis',any(coherent(a) for a in complete))
    if 'required_force' in expected:
        check('force',any(a['force']==expected['required_force'] for a in viable)
              or any(c.get('force')==expected['required_force'] for c in report['clauses']))
    if expected.get('no_categorical_linguistic_rejection'):
        check('no_categorical_rejection',report.get('status')!='REJECT' and not report.get('linguistically_impossible'),safety=True)
    if expected.get('forbid_unique_cognitive_reading_from_lemma_alone'):
        check('no_unlicensed_cognitive_disambiguation',not any(c['predicate_kind']=='scoped' and any(q.get('family')=='zanna' for q in walk_qualifiers(c['restriction'])) for c in claims),safety=True)
    if expected.get('forbid_bare_embedded_property'):
        check('no_bare_embedded_property',not any(c['predicate_kind']=='property' and not c['restriction'] for c in claims),safety=True)
    for kind in ('idafa','hal','tamyiz','badal_part','tawkeed'):
        if expected.get('forbid_activated_'+kind):
            def prohibited(r):
                return r.get('kind')==kind or kind=='badal_part' and r.get('kind')=='badal' and r.get('subtype') in ('part','some','partitive')
            present=any(any(prohibited(r) for r in relation_rows(a)) or any(s.get('activated') and s['role']==kind for s in a['assignments']) for a in active)
            check('no_activated_'+kind,not present,safety=True)
    if expected.get('preserve_idafa_chain_order'):
        wanted=expected['required_relations']
        check('idafa_chain_order',len(wanted)>=2 and any(all(any(relation_matches(r,t,a,rows,anchors) for t in relation_rows(a)) for r in wanted) for a in active))
    owner_ids={eid for a in viable for r in relation_rows(a) if r.get('kind')=='hal' for eid in bound_at(a,r.get('owner_span'))}
    if 'hal_owner_candidates' in expected:
        check('hal_owner_candidates',set(expected['hal_owner_candidates'])<=owner_ids,{'observed':sorted(owner_ids)})
    if expected.get('forbid_arbitrary_unique_hal_owner'):
        check('no_unique_hal_owner',not claims or len({q.get('owner') for c in claims for q in walk_qualifiers(c['restriction']) if q.get('kind')=='hal'})!=1,safety=True)
    if 'required_relation_candidates' in expected:
        candidates={r['kind'] if not(r['kind']=='badal' and r.get('subtype') in ('part','partitive')) else 'badal_part' for a in viable for r in relation_rows(a)}
        check('relation_candidates',set(expected['required_relation_candidates'])<=candidates,{'observed':sorted(candidates)})
    if expected.get('forbid_context_identity_merge'):
        bad=False
        for a in active:
            for r in relation_rows(a):
                if r.get('identity_preserved') is True and r.get('head_span') and r.get('dependent_span'):
                    left,right=bound_at(a,r['head_span']),bound_at(a,r['dependent_span'])
                    bad |= bool(left and right and not left & right)
        check('no_context_identity_merge',not bad,safety=True)
    if expected.get('forbid_whole_from_part'):
        check('no_whole_from_part',not any(c['predicate_kind']=='event' and len(c['args'])>1 and not c['restriction'] for c in claims),safety=True)
    if expected.get('forbid_arbitrary_unique_badal_reading'):
        check('no_unique_badal',not any(r.get('kind')=='badal' for a in complete for r in relation_rows(a)),safety=True)
    for i,wanted in enumerate(expected.get('questions',[])):
        value=questions[i]
        if 'error' in value:
            check('question:'+str(i),False,value['error']);continue
        answer,inquiry=value['answer'],value['inquiry']
        validate_report(inquiry,{**inputs,'text':wanted['text'],'source_id':'question'},audit)
        validate_answer(answer,report,inquiry,inputs,wanted['text'])
        certificate=value['verification'].get('valid') is True
        grounded=bool(answer['proofs'] or answer['counterproofs'] or answer['bindings'])
        if wanted['outcome']=='NO_GROUNDED_SUPPORT':
            ok=answer['status'] in ('UNKNOWN','DEFER','OUT_OF_SCOPE') and not grounded
        else:
            query_complete=(bool(answer['question_interpretations']) if 'question_interpretations' in answer
                            else answer['query'] is not None and inquiry['status']=='LICENSED_DISCOURSE')
            ok=answer['status']==wanted['outcome'] and query_complete
        check('question:'+str(i),ok and (certificate or not wanted['certificate_required']),
              {'expected':wanted['outcome'],'status':answer['status'],
               'query_complete':bool(answer['question_interpretations']) if 'question_interpretations' in answer
                                else answer['query'] is not None and inquiry['status']=='LICENSED_DISCOURSE',
               'certificate':certificate},
              safety=wanted['outcome']!='SUPPORTED' and grounded)
    if 'replay' in expected:
        check('replay_original_report',verification.get('valid') is True)
        check('replay_original_answer',questions and 'answer' in questions[0] and questions[0]['verification'].get('valid') is True)
        check('replay_changed_report',not expected['replay']['changed_report_must_invalidate'] or replay and replay['report'].get('valid') is False,safety=True)
        check('replay_changed_answer',replay and replay['answer'].get('valid') is False,safety=True)
    return {'id':case['id'],'group':case['group'],'mode':case['mode'],'passed':not failures,
            'checks':checks,'failures':failures,'false_accepts':false,
            'observed':{'report_status':report['status'],'complete_analyses':len(complete),'viable_analyses':len(viable),'claims':len(claims)}}


def load_material():
    payload=(FOLDER/'independent_freeze_v1.json').read_bytes()
    require(sha256(payload).hexdigest()==GOLD_FREEZE_SHA256,'Independent freeze changed')
    freeze=json.loads(payload)
    for item in freeze['files']:
        path=ROOT/item['path'];data=path.read_bytes()
        require(path.resolve().is_relative_to(FOLDER.resolve()) and len(data)==item['bytes'] and sha256(data).hexdigest()==item['sha256'],
                'Frozen material changed: '+item['path'])
    material=json.loads((FOLDER/'independent_cases_v1.json').read_bytes())
    cases=material['cases']
    require(len(cases)==len({c['id'] for c in cases})==86 and sum(c['mode']=='replay' for c in cases)==6,'Case inventory changed')
    require(sum(len(c['expected'].get('questions',[])) for c in cases)==106,'Question inventory changed')
    for case in cases:
        require(set(case['expected'])<=EXPECTED_KEYS,'Unimplemented expected predicate')
        require(re.fullmatch('[a-z][a-z0-9_]{0,127}',case['input']['source_id']) is not None,'Invalid material source ID')
        require(case['input']['lexical_profile']=='authored_full','Unknown lexical source profile')
        for role in case['expected'].get('required_roles',[]):
            require(set(role)<={'surface','span','span_basis','role','case','case_domain','sign','governor'},'Unimplemented role requirement')
        for relation in case['expected'].get('required_relations',[]):
            require(set(relation)<={'kind','head','dependent','governor_word_index','owner_word_index','owner_id','target_word_index',
                'coreference_id','clause_case','case_domain','subject_return_id','clause_start_word_index'},'Unimplemented relation requirement')
        for qual in case['expected'].get('required_qualifications',[]):
            require(set(qual)<={'kind','head_word_index','dependent_word_index','dependent_lemma','owner_id','must_belong_to_same_accepted_claim','required_time'},
                    'Unimplemented qualification requirement')
            require(qual['must_belong_to_same_accepted_claim'] is True,'Unknown qualification correlation contract')
    return freeze,material,(FOLDER/material['source_file']).read_bytes()


def runtime_snapshot(manifest_path,runtime_root):
    payload=manifest_path.read_bytes();checksum=sha256(payload).hexdigest()
    require(checksum in PINS,'Unapproved runtime manifest')
    manifest,pin=json.loads(payload),PINS[checksum]
    require(len(manifest['files'])==pin['file_count'],'Runtime inventory count changed')
    require(all(manifest[k]==pin[k] for k in ('snapshot_sha256','archive_sha256')),'Runtime pin mismatch')
    require(digest(manifest['files'])==pin['snapshot_sha256'],'Runtime inventory hash mismatch')
    paths=[r['path'] for r in manifest['files']]
    actual={'pyproject.toml'}|{str(p.relative_to(runtime_root)) for p in (runtime_root/'src').rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and not any(s.endswith(('.egg-info','.dist-info')) for s in p.parts)}
    require(len(paths)==len(set(paths)) and actual-NON_RUNTIME==set(paths),'Actual authoritative package inventory changed')
    for item in manifest['files']:
        require(not Path(item['path']).is_absolute() and '..' not in Path(item['path']).parts,'Unsafe runtime inventory path')
        data=(runtime_root/item['path']).read_bytes()
        require(len(data)==item['bytes'] and sha256(data).hexdigest()==item['sha256'],'Runtime bytes changed: '+item['path'])
    archive=manifest_path.parent/manifest['archive_filename']
    require(sha256(archive.read_bytes()).hexdigest()==pin['archive_sha256'],'Runtime archive changed')
    by_path={r['path']:r for r in manifest['files']}
    with tarfile.open(archive,'r:gz') as saved:
        members=saved.getmembers()
        require(len(members)==len(paths) and {m.name for m in members}==set(paths) and all(m.isfile() for m in members),'Runtime archive inventory changed')
        for member in members:
            data=saved.extractfile(member).read()
            require(len(data)==by_path[member.name]['bytes'] and sha256(data).hexdigest()==by_path[member.name]['sha256'],'Runtime archive member changed')
    files=list(manifest['files'])
    for path in (Path(__file__),Path(__file__).with_name('question_answer_validation.py'),
                 ROOT/'tests/test_construction_evaluator.py',ROOT/'tests/test_question_interpretation_validation.py',
                 Path(__file__).with_name('arabic_coverage_gate.py'), coverage_gate.POLICY_PATH,
                 ROOT/'tests/test_arabic_coverage_gate.py', Path(__file__).with_name('source_name_validation.py'),
                 ROOT/'tests/test_source_witness_validation.py', *source_validation.fixture_paths(),
                 Path(__file__).with_name('arabic_completion_gate.py'), completion_gate.POLICY_PATH,
                 ROOT/'tests/test_arabic_completion_gate.py', Path(__file__).with_name('productive_form_validation.py'),
                 Path(__file__).with_name('arabic_completion_v4_gate.py'), productive_gate.POLICY_PATH,
                 Path(__file__).with_name('arabic_completion_v5_gate.py'), classical_gate.POLICY_PATH,
                 Path(__file__).with_name('arabic_completion_v6_gate.py'), extension_gate.POLICY_PATH,
                 Path(__file__).with_name('framework_foundation_gate.py'), foundation_gate.POLICY_PATH,
                 Path(__file__).with_name('imperative_paradigm_validation.py')):
        data=path.read_bytes();files.append({'path':str(path.relative_to(ROOT)),'bytes':len(data),'sha256':sha256(data).hexdigest()})
    return {'runtime_root':str(runtime_root),'runtime_freeze':str(manifest_path.relative_to(ROOT)),
        'runtime_freeze_sha256':checksum,'runtime_snapshot_sha256':pin['snapshot_sha256'],'runtime_archive_sha256':pin['archive_sha256'],
        'runtime_version':pin['version'],'runtime_file_count':len(paths),'files':files,'measured_snapshot_sha256':digest(files),
        'excluded_existing_documentation_metadata':sorted(actual & NON_RUNTIME)}


def gate_decision(result, allow_documented_boundaries=False):
    """Optional regression acceptance; never relabel a failed linguistic check."""
    if result['snapshot']['runtime_freeze_sha256'] == foundation_gate.RUNTIME_SHA256:
        return foundation_gate.gate_decision('construction', result, allow_documented_boundaries)
    if result['snapshot']['runtime_freeze_sha256'] == extension_gate.RUNTIME_SHA256:
        return extension_gate.gate_decision('construction', result, allow_documented_boundaries)
    if result['snapshot']['runtime_freeze_sha256'] == classical_gate.RUNTIME_SHA256:
        return classical_gate.gate_decision('construction', result, allow_documented_boundaries)
    if result['snapshot']['runtime_freeze_sha256'] == productive_gate.RUNTIME_SHA256:
        return productive_gate.gate_decision('construction', result, allow_documented_boundaries)
    if result['snapshot']['runtime_freeze_sha256'] == completion_gate.RUNTIME_SHA256:
        return completion_gate.gate_decision('construction', result, allow_documented_boundaries)
    if result['snapshot']['runtime_freeze_sha256'] == coverage_gate.RUNTIME_SHA256:
        return coverage_gate.gate_decision('construction', result, allow_documented_boundaries)
    cases=result['cases'];raw=result['raw_log'];integrity=[]
    if type(result['total']) is not int or result['total']!=86 or len(cases)!=86:
        integrity.append('complete_case_inventory_required')
    if [c['id'] for c in cases]!=raw.get('case_ids') or len({c['id'] for c in cases})!=len(cases):
        integrity.append('raw_case_inventory_mismatch')
    if not all(raw.get(k) is True for k in ('complete_gzip_verified','canonical_json_verified','write_time_inventory_verified')):
        integrity.append('complete_raw_finalization_required')
    if result['measurement_valid'] is not True or any(result[k] for k in ('execution_errors','question_execution_errors','finalization_errors')):
        integrity.append('execution_or_finalization_error')
    if type(result['false_accept_count']) is not int or result['false_accept_count']!=0 or any(c['false_accepts'] for c in cases):
        integrity.append('false_accepts_are_never_waived')
    if type(result['passed']) is not int or result['passed']!=sum(c['passed'] is True for c in cases):
        integrity.append('pass_total_mismatch')
    for case in cases:
        if type(case['passed']) is not bool or case['passed']!=(not case['failures']):
            integrity.append('case_pass_flag_mismatch:'+case['id'])
        if wire([c for c in case['checks'] if c['passed'] is False])!=wire(case['failures']):
            integrity.append('case_failure_inventory_mismatch:'+case['id'])
        if any(c['check'].startswith('question:') and c.get('details',{}).get('certificate') is not True for c in case['checks']):
            integrity.append('question_certificate_required:'+case['id'])
    runtime=result['snapshot']['runtime_freeze_sha256']
    policy=DOCUMENTED_BOUNDARY_POLICIES.get(runtime)
    eligible=(allow_documented_boundaries and result['gold_freeze_sha256']==GOLD_FREEZE_SHA256
              and policy is not None)
    documented=[];unexpected=[]
    for case in cases:
        for failure in case['failures']:
            item={'id':case['id'],'check':failure['check']}
            if eligible and failure['check'] in policy.get(case['id'],frozenset()):
                documented.append(item)
            else:
                unexpected.append(item)
    strict=not integrity and not documented and not unexpected and result['passed']==86
    if type(result['strict_pass']) is not bool or result['strict_pass']!=strict:
        integrity.append('strict_pass_flag_mismatch')
    return {'gate_pass':not integrity and not unexpected and (strict or eligible),
            'gate_mode':('documented_partial_coverage_v3' if runtime in {
                             BOUNDARY_RUNTIME_V4_SHA256, RATIONAL_INQUIRY_BOUNDARY_RUNTIME_SHA256,
                             RATIONAL_INQUIRY_V2_BOUNDARY_RUNTIME_SHA256}
                         else 'documented_partial_coverage_v2' if runtime==BOUNDARY_RUNTIME_V3_SHA256
                         else 'documented_partial_coverage_v1') if allow_documented_boundaries else 'strict',
            'documented_boundary_runtime_sha256':runtime if eligible else None,
            'documented_boundary_failures':documented,'unexpected_failures':unexpected,
            'gate_integrity_errors':integrity,
            'documented_boundary_inventory_sha256':digest({k:sorted(v) for k,v in
                (policy if policy is not None else DOCUMENTED_FAILURES).items()})}


def evaluate(output,manifest_path,runtime_root,allow_documented_boundaries=False):
    require(not any(n=='nabt' or n.startswith('nabt.') for n in sys.modules),'Use a fresh process before importing NABT')
    require(not output.exists(),'Refusing to overwrite a result')
    freeze,material,source=load_material();snapshot=runtime_snapshot(manifest_path,runtime_root)
    output.parent.mkdir(parents=True,exist_ok=True);captured=capture_code(snapshot,output)
    raw_path=output.with_suffix('.raw.jsonl.gz');require(not raw_path.exists(),'Refusing to overwrite raw output')
    result={'schema':VERSION,'started_at_utc':datetime.now(timezone.utc).isoformat(),'gold_freeze_sha256':GOLD_FREEZE_SHA256,
        'snapshot':snapshot,'code_archive':captured,'source_sha256':sha256(source).hexdigest(),
        'source_authority':'AUTHORED_LEXICAL_PREMISES_NOT_QUOTED_QAC','cases':[], 'execution_errors':[], 'question_execution_errors':[], 'finalization_errors':[],
        'scope':'Independent authored composition from supplied lexical/context premises; first frozen material unchanged.',
        'not_claimed':['untouched external corpus','unsupervised lexical knowledge','world truth','general Arabic completeness']}
    sys.path.insert(0,str(runtime_root/'src'))
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.discourse import read_discourse,ask_discourse,verify_discourse,verify_discourse_answer
    from nabt.errors import NabtError
    verify_import_origins(runtime_root)
    model=learn_qac_lexicon(source,source_id=SOURCE_ID);audit=SourceAudit(source,source_id=SOURCE_ID)
    result['model_summary']=model.summary();started=time.monotonic()
    written_inventory=[]
    with gzip.open(raw_path,'wb') as raw_log:
        def log(value):
            line=wire(value)+b'\n'
            written_inventory.append({'index':len(written_inventory),'bytes':len(line),'sha256':sha256(line).hexdigest(),
                'kind':'model' if 'model_summary' in value else 'case','id':value.get('id')})
            raw_log.write(line);raw_log.flush()
        log({'model_summary':result['model_summary'],'source_sha256':result['source_sha256']})
        for case in material['cases']:
            inputs,expected=case['input'],case['expected'];case_started=time.monotonic()
            kwargs={'lexical_model':model,'context':inputs['context'],'source_id':inputs['source_id'],'scope':inputs['scope']}
            report=None;questions=[];verification=None;replay=None;stage='read'
            try:
                report=read_discourse(inputs['text'],**kwargs)
                stage='verify';verification=verify_discourse(report,text=inputs['text'],**kwargs)
                stage='questions'
                for qi,wanted in enumerate(expected.get('questions',[])):
                    try:
                        answer=ask_discourse(inputs['text'],wanted['text'],**kwargs)
                        inquiry=read_discourse(wanted['text'],**{**kwargs,'source_id':'question'})
                        qverify=verify_discourse_answer(answer,text=inputs['text'],question=wanted['text'],**kwargs)
                        questions.append({'answer':answer,'inquiry':inquiry,'verification':qverify})
                    except Exception as error:
                        failure={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
                        questions.append({'error':failure});result['question_execution_errors'].append({'id':case['id'],'index':qi,**failure})
                if 'replay' in expected:
                    stage='replay';change=expected['replay']['changed_inputs'];new_kwargs={**kwargs}
                    for key in ('context','scope','source_id','lexical_model'):
                        if key in change:new_kwargs[key]=change[key]
                    new_text=change.get('text',inputs['text']);old_answer=questions[0].get('answer')
                    new_report=verify_discourse(report,text=new_text,**new_kwargs) if expected['replay']['changed_report_must_invalidate'] else {'valid':True,'not_applicable':True}
                    new_answer=verify_discourse_answer(old_answer,text=new_text,question=change.get('question',expected['questions'][0]['text']),**new_kwargs) if old_answer else {'valid':False,'missing_original_answer':True}
                    replay={'report':new_report,'answer':new_answer}
                stage='scoring';entry=score_case(case,report,questions,verification,audit,replay)
            except Exception as error:
                failure={'id':case['id'],'stage':stage,'type':type(error).__name__,'message':str(error),
                    'diagnostic':error.as_dict() if isinstance(error,NabtError) else None,'traceback':traceback.format_exc()}
                result['execution_errors'].append(failure)
                entry={'id':case['id'],'group':case['group'],'mode':case['mode'],'passed':False,
                    'checks':[],'failures':[{'check':'execution','details':failure}],'false_accepts':[]}
            entry['seconds']=round(time.monotonic()-case_started,6);result['cases'].append(entry)
            log({'id':case['id'],'report':report,'questions':questions,'verification':verification,'replay':replay,'score':entry})
            print(json.dumps({'case':case['id'],'passed':entry['passed'],'failures':[f['check'] for f in entry['failures']]},ensure_ascii=False),flush=True)
    verify_import_origins(runtime_root)
    require(runtime_snapshot(manifest_path,runtime_root)['measured_snapshot_sha256']==snapshot['measured_snapshot_sha256'],'Measured bytes changed during evaluation')
    try:
        result['raw_log']=finalize_raw_log(raw_path,material,result,written_inventory)
    except Exception as error:
        result['raw_log']={'filename':raw_path.name,'sha256':sha256(raw_path.read_bytes()).hexdigest(),'complete_gzip_verified':False}
        result['finalization_errors'].append({'stage':'raw_finalization','type':type(error).__name__,
            'message':str(error),'traceback':traceback.format_exc()})
    check_counts=defaultdict(lambda:{'passed':0,'total':0});by_mode=defaultdict(lambda:{'passed':0,'total':0});by_group=defaultdict(lambda:{'passed':0,'total':0})
    for case in result['cases']:
        for target,key in ((by_mode,case['mode']),(by_group,case['id'].split('-')[1][0])):
            target[key]['total']+=1;target[key]['passed']+=int(case['passed'])
        for check in case['checks']:
            key=check['check'].split(':')[0];check_counts[key]['total']+=1;check_counts[key]['passed']+=int(check['passed'])
    by_question=defaultdict(lambda:{'passed':0,'total':0});entries={c['id']:c for c in result['cases']}
    for case in material['cases']:
        if case['mode']=='replay':continue
        checks={c['check']:c['passed'] for c in entries[case['id']]['checks']}
        for i,q in enumerate(case['expected'].get('questions',[])):
            by_question[q['outcome']]['total']+=1;by_question[q['outcome']]['passed']+=int(checks.get('question:'+str(i),False))
    result.update(completed_at_utc=datetime.now(timezone.utc).isoformat(),seconds=round(time.monotonic()-started,6),
        passed=sum(c['passed'] for c in result['cases']),total=86,
        comprehension={'passed':sum(c['passed'] for c in result['cases'] if c['mode']!='replay'),'total':80},
        replay={'passed':sum(c['passed'] for c in result['cases'] if c['mode']=='replay'),'total':6},
        by_mode=dict(by_mode),by_group=dict(by_group),by_check=dict(check_counts),by_question_outcome=dict(by_question),
        false_accept_count=sum(len(c['false_accepts']) for c in result['cases']),
        false_accept_case_count=sum(bool(c['false_accepts']) for c in result['cases']))
    result['measurement_valid']=not result['execution_errors'] and not result['question_execution_errors'] and not result['finalization_errors']
    result['strict_pass']=result['passed']==86 and result['measurement_valid'] and result['false_accept_count']==0
    result.update(gate_decision(result,allow_documented_boundaries))
    output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','total','comprehension','replay','false_accept_count','strict_pass')},ensure_ascii=False),flush=True)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root',type=Path,default=ROOT)
    parser.add_argument('--runtime-freeze',type=Path,default=ROOT/'evidence/certified_transition_v1/code_freeze_v1.json')
    parser.add_argument('--allow-documented-boundaries',action='store_true',
                        help='Accept only explicitly reviewed v2 coverage failures; strict_pass remains false.')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    result=evaluate(args.output.resolve(),args.runtime_freeze.resolve(),args.runtime_root.resolve(),args.allow_documented_boundaries)
    return 0 if result['gate_pass'] else 1


if __name__=='__main__':
    raise SystemExit(main())
