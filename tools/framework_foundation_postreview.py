#!/usr/bin/env python3
"""Versioned foundation-runtime continuation for the unchanged Arabic holdout v2.

Historical v7, gold, denominators and the documented H18 checker correction are
preserved. Fresh runtime bytes, raw journals and certificates are independently
replayed; no result is relabeled merely because the runtime was registered.
This is a known regression replay, never a new blind test.
"""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import gzip
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import tarfile
import zipfile
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'evidence/arabic_coverage'
MATERIAL_SHA256 = '127a5870fcbc8f8823b95f2a9f452cf4cd87de22fcfc62b271efd32bc684c106'
RUNTIME_SHA256 = '7f6b8ace539ec969ecb56939929ac982eb85e064e103a2bd90983bda583104f8'
RUNTIME_SNAPSHOT_SHA256 = 'da60d43f8f99c56cedaeca2c04133990ff22654faac5dfbeb3a64bc5a1209831'
RUNTIME_ARCHIVE_SHA256 = 'e488e15b491c1d5087b797810d17befcfd79c9bfc7d6493e49d19c69704340eb'
TARGET = ('H18', 'question:2:no_grounded_evidence')
PREVIOUS_ARCHIVE = ROOT / 'evidence/arabic_completion_v3/full_validation_reports_v1.zip'
PREVIOUS_ARCHIVE_SHA256 = '23062c5cab865a4acfd29aa66928dc3301816fb7816bd712a4d1b5c53ba22d58'
PREVIOUS_RESULT_MEMBER = 'arabic-holdout.json'
PREVIOUS_RESULT_SHA256 = 'ced0a25d394dd1a34f7086ed9b929b4cf0f1a5e3b3ae796ca277ac4f3bcdc264'
PREVIOUS_RAW_MEMBER = 'arabic-holdout.raw.jsonl'
PREVIOUS_RAW_SHA256 = 'c6a9a9d31ad038a21fe5e18cd0f002b6b294ee163ecbda97c2ca1a09063fa611'
PREVIOUS_RUNTIME_SHA256 = 'eeb9864b08e8ae25e841b18b0d25858d95268fce2435d51c340d69a41782f089'
# These are the same explicit non-runtime source metadata paths excluded by
# both original evaluators. No other extra path, including another Markdown
# file, may be silently removed from the holdout's larger source inventory.
NON_RUNTIME_METADATA = {
    'src/nabt/data/source_evidence/.gitattributes',
    'src/nabt/data/source_evidence/LICENSE-DATA.md',
    'src/nabt/data/source_evidence/README.md',
}


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_digest(path):
    return sha256(path.read_bytes()).hexdigest()


def identity(path):
    path = path.resolve()
    name = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    return {'path': name, 'bytes': path.stat().st_size, 'sha256': file_digest(path)}


def save_json(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write('\n')
    return identity(path)


def matching(claim, pattern):
    return type(claim) is dict and all(key in claim and claim[key] == value for key, value in pattern.items())


def previous_trace(raw):
    """Bind the continuation to all earlier public payloads, with no ignored field."""
    require(file_digest(PREVIOUS_ARCHIVE) == PREVIOUS_ARCHIVE_SHA256,
            'Previous finalized validation archive changed')
    with zipfile.ZipFile(PREVIOUS_ARCHIVE) as saved:
        require(saved.namelist().count(PREVIOUS_RESULT_MEMBER) == 1
                and saved.namelist().count(PREVIOUS_RAW_MEMBER) == 1,
                'Previous trace members missing or duplicated')
        result_bytes = saved.read(PREVIOUS_RESULT_MEMBER)
        old_raw = saved.read(PREVIOUS_RAW_MEMBER)
    require(sha256(result_bytes).hexdigest() == PREVIOUS_RESULT_SHA256
            and sha256(old_raw).hexdigest() == PREVIOUS_RAW_SHA256,
            'Previous public trace member changed')
    old_result = json.loads(result_bytes)
    require(old_result['material_freeze_sha256'] == MATERIAL_SHA256
            and old_result['case_score'] == {'passed': 35, 'total': 36}
            and old_result['question_total'] == 63,
            'Previous trace belongs to different material or denominators')
    old_records, old_by_key = read_journal(old_raw, old_result)
    require(raw == old_raw, 'Raw public payloads differ from the previous complete trace')
    return {'archive': identity(PREVIOUS_ARCHIVE),
            'result_member': {'name': PREVIOUS_RESULT_MEMBER, 'sha256': PREVIOUS_RESULT_SHA256,
                              'bytes': len(result_bytes)},
            'raw_member': {'name': PREVIOUS_RAW_MEMBER, 'sha256': PREVIOUS_RAW_SHA256,
                           'bytes': len(old_raw)},
            'previous_runtime_freeze_sha256': PREVIOUS_RUNTIME_SHA256,
            'raw_record_count': len(old_records), 'unique_call_count': len(old_by_key),
            'all_raw_bytes_equal': True, 'ignored_public_fields': [],
            'prediction_success_or_accuracy_increase_claimed': False}


def validate_measurement_summary(result, material, runtime):
    """A permitted error label is insufficient: all other gates remain exact."""
    require(result.get('schema') == 'nabt.independent-arabic-holdout-result.v1', 'Unknown original result schema')
    require(result.get('material_freeze_sha256') == MATERIAL_SHA256, 'Result belongs to a different material freeze')
    require(result.get('measurement_valid') is True and result.get('runtime_unchanged') is True,
            'Original measurement is invalid or runtime changed')
    require(result.get('runtime_errors') == [], 'Original execution contains runtime errors')
    entries = sorted((item for item in runtime['files'] if item['path'].startswith('src/nabt/')),
                     key=lambda item: item['path'])
    before = result.get('runtime_before', {})
    observed = before.get('entries')
    require(type(observed) is list and all(type(item) is dict and set(item)=={'path','bytes','sha256'}
            and type(item['path']) is str and type(item['bytes']) is int and item['bytes']>=0
            and type(item['sha256']) is str for item in observed),
            'Malformed full source inventory')
    paths = [item['path'] for item in observed]
    require(len(paths)==len(set(paths)) and paths==sorted(paths)
            and before.get('sha256')==sha256(wire(observed)).hexdigest()
            and result.get('runtime_after')==before, 'Full source inventory changed or has inconsistent identity')
    require([item for item in observed if item['path'] not in NON_RUNTIME_METADATA]==entries,
            'Result runtime inventories do not equal the approved frozen runtime')
    expected_cases, actual_cases = material['cases'], result.get('cases')
    require(type(actual_cases) is list and [case.get('id') for case in actual_cases] == [case['id'] for case in expected_cases],
            'Original case inventory omitted, duplicated or reordered material')
    failures, unsafe, categories = [], [], defaultdict(Counter)
    for expected, case in zip(expected_cases, actual_cases):
        require(case.get('category') == expected['category'] and case.get('focus') == expected['focus'],
                'Original case category/focus changed')
        checks = case.get('checks')
        require(type(checks) is list and checks and all(type(check.get('pass')) is bool for check in checks),
                'Malformed or empty original check inventory')
        names = [check['name'] for check in checks]
        require(len(names) == len(set(names)), 'Original check inventory contains duplicates')
        passed = all(check['pass'] for check in checks)
        require(case.get('passed') is passed, 'Original case score contradicts its checks')
        categories[case['category']]['total'] += 1
        categories[case['category']]['passed'] += passed
        for check in checks:
            if not check['pass']:
                failures.append((case['id'], check['name']))
            if check.get('unsafe_acceptance'):
                require(check['pass'] is False, 'Passing check was marked unsafe')
                unsafe.append({'case_id': case['id'], **check})
    require(failures == [TARGET], 'New or missing failure: only the demonstrated H18 checker defect is reviewable')
    require(len(unsafe) == 1 and (unsafe[0]['case_id'], unsafe[0]['name']) == TARGET
            and result.get('unsafe_acceptances') == unsafe, 'Original unsafe inventory changed or contains a new unsafe result')
    require(result.get('case_score') == {'passed': len(actual_cases) - 1, 'total': len(actual_cases)},
            'Original strict score/denominator changed')
    require(result.get('category_scores') == {key: dict(value) for key, value in categories.items()},
            'Original category scores contradict the cases')
    require(result.get('strict_pass') is False and result.get('coverage_complete') is False,
            'The original strict failure was concealed')
    require(result.get('question_total') == sum(len(case['questions']) for case in expected_cases),
            'Question denominator changed')
    for name in ('cross_case_checks', 'separate_replay_checks'):
        require(type(result.get(name)) is list and len(result[name]) == 4
                and len({check['name'] for check in result[name]}) == 4
                and all(check.get('pass') is True for check in result[name]),
                'A cross-case or context-replay check failed or disappeared')
    return unsafe


def read_journal(raw, result):
    log = result.get('raw_log', {})
    lines = raw.splitlines()
    require(log.get('sha256') == sha256(raw).hexdigest() and log.get('records') == len(lines)
            and log.get('complete_reparse_and_line_hashes') is True,
            'Raw journal differs from its captured inventory')
    require([sha256(line).hexdigest() for line in lines] == log.get('line_sha256'),
            'Raw journal write-time line inventory changed')
    records, by_key = [], {}
    for line in lines:
        record = json.loads(line)
        require(wire(record) == line, 'Raw journal is not canonical JSON')
        key = record.get('call'), record.get('case_id'), record.get('question_index')
        require(key not in by_key, 'Raw journal contains duplicate call identities')
        require(set(record) == ({'call', 'case_id', 'value', 'question_index'} if key[2] is not None
                                else {'call', 'case_id', 'value'}), 'Unknown raw record shape')
        by_key[key] = record['value']
        records.append(record)
    return records, by_key


def validate_raw_observations(result, material, by_key):
    """Recheck all authored observations; do not trust headline pass flags."""
    expected_keys = {('lexical_summary', None, None)}
    metrics = defaultdict(Counter)
    documents, answers = {}, {}
    by_case = {case['id']: case for case in result['cases']}
    for case in material['cases']:
        cid, source_id, scope = case['id'], 'holdout_' + case['id'].lower(), 'independent_holdout_v1'
        expected_keys.update({('read_discourse', cid, None), ('verify_discourse', cid, None)})
        document = by_key[('read_discourse', cid, None)]
        documents[cid] = document
        require(document.get('report_id') == sha256(wire({key: value for key, value in document.items() if key != 'report_id'})).hexdigest(),
                'Raw document content identity changed')
        require(document.get('source_text') == case['text'] and document.get('source_id') == source_id
                and document.get('scope') == scope and document.get('source_sha256') == sha256(case['text'].encode()).hexdigest()
                and document.get('world_truth') == 'NOT_ESTABLISHED', 'Raw source identity/scope changed')
        require(document.get('status') == case['expected_document_status'], 'Raw document has a new status failure')
        claims = document['claims']
        require(len(claims) >= case.get('claims_min', 0) and len(claims) <= case.get('claims_max', len(claims)),
                'Raw document violates an authored claim-count bound')
        require(all(any(matching(claim, pattern) for claim in claims) for pattern in case['required_claims']),
                'Raw document omitted an authored required claim')
        require(not any(matching(claim, pattern) for claim in claims for pattern in case['forbidden_claims']),
                'Raw document asserted an authored forbidden claim')
        if 'expected_clause_forces' in case:
            require([clause.get('force') for clause in document['clauses']] == case['expected_clause_forces'],
                    'Raw document changed an authored clause force')
        require(by_key[('verify_discourse', cid, None)].get('valid') is True, 'Original document replay failed')
        names = {check['name'] for check in by_case[cid]['checks']}
        required_names = {'document_status', 'source_text', 'source_identity', 'source_hash',
                          'world_truth_not_established', 'document_replay'}
        if 'claims_min' in case: required_names.add('minimum_claims')
        if 'claims_max' in case: required_names.add('maximum_claims')
        if 'expected_clause_forces' in case: required_names.add('clause_forces')
        required_names.update('required_claim:' + str(index) for index in range(len(case['required_claims'])))
        required_names.update('forbidden_claim:' + str(index) for index in range(len(case['forbidden_claims'])))
        for index, question in enumerate(case['questions']):
            expected_keys.update({('ask_discourse', cid, index), ('verify_discourse_answer', cid, index)})
            answer = by_key[('ask_discourse', cid, index)]
            answers[(cid, index)] = answer
            status = answer.get('status')
            metrics[question['expected_status']][status] += 1
            require(status == question['expected_status'], 'Raw answer has a new question-status failure')
            require(answer.get('answer_id') == sha256(wire({key: value for key, value in answer.items() if key != 'answer_id'})).hexdigest(),
                    'Raw answer content identity changed')
            require(answer.get('source_text') == case['text'] and answer.get('question_text') == question['text']
                    and answer.get('document_report_id') == document['report_id']
                    and answer.get('world_truth') == 'NOT_ESTABLISHED', 'Raw answer changed its actual inputs/source report')
            require(by_key[('verify_discourse_answer', cid, index)].get('valid') is True, 'Original answer replay failed')
            prefix = 'question:' + str(index) + ':'
            required_names.update(prefix + name for name in ('status', 'source_bytes', 'document_identity', 'world_truth', 'replay'))
            proofs, counters = answer['proofs'], answer['counterproofs']
            if status in ('SUPPORTED', 'CONFLICT'):
                required_names.add(prefix + 'support_exists')
                require(bool(proofs), 'Raw supported/conflicting answer lacks positive evidence')
            if status in ('REFUTED', 'CONFLICT'):
                required_names.add(prefix + 'counterproof_exists')
                require(bool(counters), 'Raw refuted/conflicting answer lacks negative evidence')
            if status in ('UNKNOWN', 'DEFER'):
                required_names.add(prefix + 'no_grounded_evidence')
                if (cid, index) != ('H18', 2):
                    require(not proofs and not counters and not answer['bindings'], 'A new deferred/unknown evidence discrepancy needs separate review')
            for number, proof in enumerate(proofs + counters):
                required_names.add(prefix + 'claim_binding:' + str(number))
                require(proof['claim_id'] in {claim['claim_id'] for claim in claims}
                        and proof['document_report_id'] == document['report_id'], 'Raw proof borrowed a foreign accepted claim')
        require(names == required_names, 'Original check inventory was omitted or augmented')
    require(result.get('question_status_by_expectation') == {key: dict(value) for key, value in metrics.items()},
            'Question-status counts differ from the raw answers')
    cross_names = set()
    cases = {case['id']: case for case in material['cases']}
    for cross in material['cross_case_checks']:
        cross_names.add(cross['id'] + ':same_exact_input_bytes')
        require(len({cases[cid]['text'].encode() for cid in cross['cases']}) == 1, 'The authored context collision changed')
        for cid, owner in cross['required_positive_owners'].items():
            cross_names.add(cross['id'] + ':owner:' + cid)
            require(any(matching(claim, {'predicate': 'حَكِيم', 'predicate_kind': 'property',
                                         'args': [owner], 'positive': True}) for claim in documents[cid]['claims']),
                    'The raw context-sensitive owner check failed')
        cross_names.add(cross['id'] + ':no_speaker_no_grounding')
        document = documents[cross['absent_speaker_case']]
        require(document['status'] == 'DEFER' and document['claims'] == [], 'Missing speaker produced a grounded claim')
    require({check['name'] for check in result['cross_case_checks']} == cross_names, 'Cross-case check identities changed')
    replay_names = set()
    for cid in ('H21', 'H22'):
        for call, suffix in [('verify_discourse_changed_context', 'changed_context_report_rejected'),
                             ('verify_answer_changed_context', 'changed_context_answer_rejected')]:
            expected_keys.add((call, cid, None))
            replay_names.add(cid + ':' + suffix)
            require(by_key[(call, cid, None)].get('valid') is False, 'Original changed-context replay was accepted')
    require({check['name'] for check in result['separate_replay_checks']} == replay_names, 'Context-replay check identities changed')
    require(set(by_key) == expected_keys, 'Raw call inventory omitted, duplicated or added an execution')
    return documents, answers


def extract_runtime(runtime, archive, isolated):
    entries = {entry['path']: entry for entry in runtime['files']}
    require(len(entries) == len(runtime['files']), 'Frozen runtime manifest has duplicate paths')
    with tarfile.open(archive, 'r:gz') as saved:
        members = saved.getmembers()
        require(len(members) == len(entries) and {member.name for member in members} == set(entries),
                'Frozen archive inventory differs from its manifest')
        for member in members:
            path = Path(member.name)
            require(member.isfile() and not path.is_absolute() and '..' not in path.parts, 'Unsafe frozen archive path')
            data = saved.extractfile(member).read()
            require(len(data) == entries[member.name]['bytes'] and sha256(data).hexdigest() == entries[member.name]['sha256'],
                    'Frozen runtime archive member changed')
            target = isolated / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)


def replay_all(runtime, archive, material, contexts, documents, answers, original_lexical_summary):
    require(not any(name == 'nabt' or name.startswith('nabt.') for name in sys.modules), 'Another NABT runtime is already imported')
    sys.dont_write_bytecode = True
    receipts = []
    with TemporaryDirectory(prefix='nabt-postreview-v4-') as directory:
        isolated = Path(directory)
        extract_runtime(runtime, archive, isolated)
        sys.path.insert(0, str(isolated / 'src'))
        corpus, api = importlib.import_module('nabt.corpus_evidence'), importlib.import_module('nabt.discourse')
        model = corpus.learn_qac_lexicon((FOLDER / 'holdout_v2/lexical_premises.tsv').read_bytes(),
                                        source_id='independent_arabic_holdout_v1')
        require(model.summary() == original_lexical_summary, 'Replay learned different lexical premises')
        for case in material['cases']:
            cid, context = case['id'], contexts[case['context']]
            kwargs = {'text': case['text'], 'lexical_model': model, 'context': deepcopy(context),
                      'source_id': 'holdout_' + cid.lower(), 'scope': 'independent_holdout_v1'}
            verified = api.verify_discourse(documents[cid], **kwargs)
            require(verified.get('valid') is True, 'Fresh pinned-runtime document replay failed: ' + cid)
            receipts.append({'case_id': cid, 'call': 'verify_discourse', 'value': verified})
            for index, question in enumerate(case['questions']):
                kwargs['context'] = deepcopy(context)
                verified = api.verify_discourse_answer(answers[(cid, index)], question=question['text'], **kwargs)
                require(verified.get('valid') is True, 'Fresh pinned-runtime answer replay failed: ' + cid + ':' + str(index))
                receipts.append({'case_id': cid, 'call': 'verify_discourse_answer', 'question_index': index, 'value': verified})
        by_case = {case['id']: case for case in material['cases']}
        for cid, context_name in [('H21', 'speaker_zayd'), ('H22', 'speaker_nasser')]:
            case = by_case[cid]
            kwargs = {'text': case['text'], 'lexical_model': model, 'context': deepcopy(contexts[context_name]),
                      'source_id': 'holdout_' + cid.lower(), 'scope': 'independent_holdout_v1'}
            verified = api.verify_discourse(documents[cid], **kwargs)
            require(verified.get('valid') is False, 'Fresh changed-context document replay was accepted')
            receipts.append({'case_id': cid, 'call': 'verify_discourse_changed_context', 'value': verified})
            kwargs['context'] = deepcopy(contexts[context_name])
            verified = api.verify_discourse_answer(answers[(cid, 0)], question=case['questions'][0]['text'], **kwargs)
            require(verified.get('valid') is False, 'Fresh changed-context answer replay was accepted')
            receipts.append({'case_id': cid, 'call': 'verify_answer_changed_context', 'value': verified})
        case = by_case['H18']
        inquiry = api.read_discourse(case['questions'][2]['text'], lexical_model=model,
            context=deepcopy(contexts[case['context']]), source_id='question', scope='independent_holdout_v1')
        require(inquiry['report_id'] == answers[('H18', 2)]['question_report_id'], 'Supplementary H18 inquiry differs from the original answer')
        for name, module in list(sys.modules.items()):
            if name == 'nabt' or name.startswith('nabt.'):
                path = getattr(module, '__file__', None)
                require(path is None or Path(path).resolve().is_relative_to(isolated / 'src'), 'Cross-runtime import')
        require(all((isolated / item['path']).stat().st_size == item['bytes']
                    and file_digest(isolated / item['path']) == item['sha256'] for item in runtime['files']),
                'Frozen runtime bytes changed during replay')
    return inquiry, receipts


def validate_h18(document, inquiry, answer, case, context):
    require(answer.get('status') == case['questions'][2]['expected_status'] == 'UNKNOWN'
            and answer.get('kind') in ('person', 'subject') and not answer.get('proofs')
            and not answer.get('bindings') and bool(answer.get('counterproofs')),
            'H18 does not have the demonstrated WH UNKNOWN-with-counterproofs form')
    inputs = {'text': case['text'], 'context': context, 'source_id': 'holdout_h18', 'scope': 'independent_holdout_v1'}
    question = case['questions'][2]['text']
    checks = []
    for name in ('discourse_evaluation.py', 'construction_evaluation.py'):
        path = ROOT / 'tools' / name
        spec = importlib.util.spec_from_file_location('postreview_v4_' + path.stem, path)
        evaluator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(evaluator)
        evaluator.validate_report(document, inputs)
        evaluator.validate_report(inquiry, {**inputs, 'text': question, 'source_id': 'question'})
        evaluator.validate_answer(answer, document, inquiry, inputs, question)
        checks.append({'evaluator': name, 'source_and_inquiry_valid': True, 'all_interpretations_and_receipts_valid': True})
    claims = {claim['claim_id']: claim for claim in document['claims']}
    require(all(claims[proof['claim_id']]['positive'] is False for proof in answer['counterproofs']),
            'H18 counterproof is not an accepted negative claim')
    return checks


def run(result_path, raw_path, runtime_path, output):
    output.mkdir(parents=True, exist_ok=True)
    require(not any(output.iterdir()), 'Choose an empty output directory; preserved evidence is never overwritten')
    source_paths = (result_path, raw_path, runtime_path, PREVIOUS_ARCHIVE)
    source_inputs = [identity(path) for path in source_paths]
    result_bytes, raw_file = result_path.read_bytes(), raw_path.read_bytes()
    raw = gzip.decompress(raw_file) if raw_file[:2] == b'\x1f\x8b' else raw_file
    with (output / 'original_result.json').open('xb') as handle: handle.write(result_bytes)
    with (output / 'original_raw.jsonl.gz').open('xb') as handle:
        with gzip.GzipFile(filename='', mode='wb', fileobj=handle, mtime=0) as saved: saved.write(raw)
    preserved = [identity(output / name) for name in ('original_result.json', 'original_raw.jsonl.gz')]
    base = {'schema': 'nabt.framework-foundation.arabic-postreview.v2',
            'created_utc': datetime.now(timezone.utc).isoformat(), 'code': identity(Path(__file__)),
            'source_inputs': source_inputs, 'preserved_original_files': preserved,
            'review_mode': 'Post-execution rescore of stored predictions with fresh pinned-runtime certificate replay; not a new blind test.',
            'continuation_scope': 'Same 36 frozen cases/63 questions; new shared-foundation runtime and new public trace; no new blind sample.',
            'original_result_rewritten': False, 'frozen_harness_or_gold_changed': False,
            'historical_v3_gate_modified': False}
    try:
        require(file_digest(runtime_path) == RUNTIME_SHA256, 'Runtime freeze is not the approved post-review completion v2 snapshot')
        runtime = json.loads(runtime_path.read_bytes())
        require(runtime['snapshot_sha256'] == RUNTIME_SNAPSHOT_SHA256
                and runtime['archive_sha256'] == RUNTIME_ARCHIVE_SHA256
                and len(runtime['files']) == 104 and sha256(wire(runtime['files'])).hexdigest() == RUNTIME_SNAPSHOT_SHA256,
                'Approved runtime manifest contents changed')
        archive = runtime_path.parent / runtime['archive_filename']
        require(file_digest(archive) == RUNTIME_ARCHIVE_SHA256, 'Approved runtime archive changed')
        freeze_path = FOLDER / 'holdout_v2/freeze.json'
        require(file_digest(freeze_path) == MATERIAL_SHA256, 'Holdout v2 material freeze changed')
        freeze = json.loads(freeze_path.read_bytes())
        for item in freeze['files']:
            path = ROOT / item['path']
            require(path.stat().st_size == item['bytes'] and file_digest(path) == item['sha256'],
                    'Frozen oracle or harness file changed: ' + item['path'])
        material = json.loads((FOLDER / 'holdout_v2/cases.json').read_bytes())
        contexts = json.loads((FOLDER / 'holdout_v2/contexts.json').read_bytes())
        require(len(material['cases']) == 36 and sum(len(case['questions']) for case in material['cases']) == 63,
                'Pinned material denominators changed')
        result = json.loads(result_bytes)
        unsafe = validate_measurement_summary(result, material, runtime)
        records, by_key = read_journal(raw, result)
        trace_comparison = {"mode": "NEW_VERSIONED_RUNTIME_TRACE", "exact_historical_payload_equality_claimed": False, "frozen_material_unchanged": True}
        documents, answers = validate_raw_observations(result, material, by_key)
        validators = [ROOT / 'tools' / name for name in ('discourse_evaluation.py', 'construction_evaluation.py',
                                                        'question_answer_validation.py', 'arabic_coverage_gate.py',
                                                        'arabic_completion_gate.py', 'source_name_validation.py')]
        validators.extend([ROOT / 'tools/framework_foundation_gate.py',
                           ROOT / 'evidence/certified_transition_v1/regression_policy_v1.json'])
        validators.append(FOLDER / 'regression_policy_v1.json')
        validators.extend(sorted((ROOT / 'evidence/arabic_completion_v3').glob('regression_policy_v*.json')))
        validator_ids = [identity(path) for path in validators]
        inquiry, receipts = replay_all(runtime, archive, material, contexts, documents, answers,
                                       by_key[('lexical_summary', None, None)])
        case = next(case for case in material['cases'] if case['id'] == 'H18')
        answer = answers[('H18', 2)]
        validations = validate_h18(documents['H18'], inquiry, answer, case, contexts[case['context']])
        require([identity(path) for path in validators] == validator_ids, 'Independent validators changed during review')
        require([identity(path) for path in source_paths] == source_inputs,
                'Original evidence changed during review')
        require(file_digest(freeze_path) == MATERIAL_SHA256 and file_digest(archive) == RUNTIME_ARCHIVE_SHA256,
                'Pinned inputs changed during review')
        for item in freeze['files']:
            require(file_digest(ROOT / item['path']) == item['sha256'], 'Frozen oracle/harness changed during review')
        base.update(gate_pass=True, original_case_score=result['case_score'], original_strict_pass=result['strict_pass'],
            postreview_case_score={'passed': 36, 'total': 36}, unchanged_question_total=63,
            unchanged_question_status_counts=result['question_status_by_expectation'],
            original_unsafe_acceptances=result['unsafe_acceptances'], reclassified_checker_false_alarms=unsafe,
            remaining_unsafe_acceptances=[], runtime_freeze_sha256=RUNTIME_SHA256,
            material_freeze_sha256=MATERIAL_SHA256, independent_validators=validator_ids,
            independent_validation=validations, replayed_certificate_count=len(receipts),
            raw_record_count=len(records), runtime_unchanged_during_replay=True,
            previous_public_trace_comparison=trace_comparison,
            authoritative_runtime_file_count=len(runtime['files']),
            matched_authoritative_source_file_count=sum(item['path'].startswith('src/nabt/') for item in runtime['files']),
            holdout_source_inventory_file_count=len(result['runtime_before']['entries']),
            non_runtime_metadata_observed=[item for item in result['runtime_before']['entries']
                                           if item['path'] in NON_RUNTIME_METADATA],
            h18={'question_report_id': inquiry['report_id'], 'answer_id': answer['answer_id'],
                 'positive_proof_count': len(answer['proofs']), 'positive_binding_count': len(answer['bindings']),
                 'counterproof_count': len(answer['counterproofs']),
                 'negative_claim_ids': sorted({proof['claim_id'] for proof in answer['counterproofs']})},
            oracle_erratum='The frozen scorer rejects every UNKNOWN counterproof. H18 has no positive WH binding; all its retained negative receipts and interpretations were independently validated.',
            full_Arabic_understanding_proved=False)
        base['supplementary_inquiry'] = save_json(output / 'question_report.json', inquiry)
        base['fresh_replay_receipts'] = save_json(output / 'verification_replay.json', receipts)
        code_paths = [Path(__file__), *validators, ROOT / 'tests/test_arabic_coverage_postreview_gate.py',
                      ROOT / 'tests/test_arabic_coverage_postreview_v4.py']
        with (output / 'review_code.tar.gz').open('xb') as handle:
            with gzip.GzipFile(filename='', mode='wb', fileobj=handle, mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode='w') as saved:
                    import io
                    for path in code_paths:
                        data = path.read_bytes(); member = tarfile.TarInfo(str(path.relative_to(ROOT)))
                        member.size, member.mode, member.mtime = len(data), 0o644, 0
                        saved.addfile(member, io.BytesIO(data))
        base['review_code_archive'] = identity(output / 'review_code.tar.gz')
        save_json(output / 'review.json', base)
        print(json.dumps({'gate_pass': True, 'original': result['case_score'], 'postreview': {'passed': 36, 'total': 36},
                          'question_status_matches': 63, 'replayed_certificates': len(receipts),
                          'review': str(output / 'review.json')}, ensure_ascii=False))
        return 0
    except Exception as error:
        base.update(gate_pass=False, error={'type': type(error).__name__, 'message': str(error)},
                    no_failure_waiver_applied=True)
        save_json(output / 'review.json', base)
        print(json.dumps({'gate_pass': False, 'error': base['error'], 'review': str(output / 'review.json')}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--runtime-freeze', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.result.resolve(), args.raw.resolve(), args.runtime_freeze.resolve(), args.output_dir.resolve()))
