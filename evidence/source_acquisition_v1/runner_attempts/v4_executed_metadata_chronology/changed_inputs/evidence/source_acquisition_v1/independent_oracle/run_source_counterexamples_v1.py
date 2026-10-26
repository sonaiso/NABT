#!/usr/bin/env python3
"""Six separately frozen source-premise cases; never part of the 24/29 score."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import gzip
import importlib.util
import json
from pathlib import Path
import re
import sys
import traceback

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('source_counterexample_review', HERE / 'review_continuation_v1.py')
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
R, E, S = P.R, P.E, P.S
MATERIAL = P.ORACLE / 'continuation_v3/source_counterexamples_v1'
VERSION = 'nabt.completion-source-counterexample-execution.v1'


def load_cases():
    frozen = json.loads(P.pinned(MATERIAL / 'freeze.json', P.SOURCE_MATERIAL))
    for row in frozen['files']:
        path = MATERIAL / row['path']
        E.require(not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts,
                  'Unsafe source-counterexample path')
        data = path.read_bytes()
        E.require(len(data) == row['bytes'] and sha256(data).hexdigest() == row['sha256'],
                  'Frozen source-counterexample material changed')
    material = json.loads((MATERIAL / 'cases.json').read_text())
    context = json.loads((MATERIAL / 'context.json').read_text())
    P.pinned(R.ROOT / material['base_fixture']['path'], material['base_fixture']['sha256'])
    E.require([c['id'] for c in material['cases']] == ['H01', 'H02', 'H03', 'H04', 'H05', 'H06'] and
              sum(len(c['expected']['questions']) for c in material['cases']) == 4,
              'Separate source-counterexample denominator changed')
    for case in material['cases']:
        raw = (MATERIAL / case['raw_file']).read_bytes()
        E.require(sha256(raw).hexdigest() == case['raw_sha256'], 'Counterexample raw source changed')
        E.require(raw_can_license(raw) is case['independently_licensed_source_premise'],
                  'Authored source premise does not match its independent raw condition')
    return material, context


def raw_can_license(raw):
    """A narrow independent predicate for these authored rows, not a QAC parser."""
    records = E.SourceAudit(raw, source_id='static_counterexample_audit').records.values()
    selected = [x for x in records if x['locator'] == [1, 1, 1, 1]]
    if len(selected) != 1:
        return False
    row = selected[0]
    tokens = row['tokens']
    fields = lambda prefix: [t for t in tokens if t.startswith(prefix)]
    return bool(row['form'] == 'Hasiba' and row['tag'] == 'V' and tokens[0] == 'STEM'
                and fields('POS:') == ['POS:V'] and fields('LEM:') == ['LEM:Hasiba']
                and fields('ROOT:') == ['ROOT:Hsb'] and 'PASS' not in tokens
                and [t for t in tokens if re.fullmatch(r'[123][MF]?[SDP]', t)] == ['3MS']
                and [t for t in tokens if t in ('PERF', 'IMPF', 'IMPV')] == ['PERF']
                and [t for t in tokens if t.startswith('(') and t.endswith(')')] in ([], ['(I)']))


def score_case(case, record, context):
    expected_input = {**case['input'], 'context': context}
    E.require(E.wire(record['inputs']) == E.wire(expected_input), 'Counterexample target/context changed')
    raw = (MATERIAL / case['raw_file']).read_bytes()
    audit = E.SourceAudit(raw, source_id=case['source_id'])
    report = record.get('report')
    checks, questions = [], []

    def check(name, passed, kind='coverage', detail=None):
        checks.append({'check': name, 'passed': bool(passed), 'kind': kind, 'detail': detail})

    try:
        E.require(type(report) is dict, 'Missing source-counterexample report')
        fixture_path = R.ROOT / json.loads((MATERIAL / 'cases.json').read_text())['base_fixture']['path']
        expected_report_keys = set(json.loads(fixture_path.read_text())['report'])
        E.require(set(report) == expected_report_keys, 'Counterexample report added or omitted authority fields')
        E.validate_report(report, record['inputs'], audit)
        E.require(record['verification'].get('valid') is True, 'Counterexample production replay failed')
        check('independent_report_integrity', True, 'integrity')
    except Exception as error:
        check('independent_report_integrity', False, 'integrity',
              {'type': type(error).__name__, 'message': str(error)})
    if type(report) is not dict:
        return {'id': case['id'], 'passed': False, 'checks': checks, 'questions': questions}
    check('document_status', report['status'] == case['expected']['document_status'])
    positive = case['independently_licensed_source_premise']
    claims = report['claims']
    beliefs = [c for c in claims if c.get('predicate') == '@operator:حسب' and
               c.get('predicate_kind') == 'scoped' and c.get('args') == ['farid'] and c.get('positive') is True]
    check('accepted_scoped_belief', len(beliefs) == 1 if positive else not beliefs,
          'coverage' if positive else 'safety')
    check('no_extra_claim_or_embedded_fact', len(claims) == (1 if positive else 0), 'safety')
    witnesses = []
    for analysis in S.analyses(report):
        for relation in analysis.get('relations', []):
            witness = relation.get('independent_sense_witness')
            if witness is not None:
                witnesses.append(witness)
    check('source_witness_requires_raw_premise', bool(witnesses) if positive else not witnesses,
          'coverage' if positive else 'safety')
    preserved_scope = all(w.get('embedded_fact_projection') is False and
                          w.get('target_role_used_as_sense_evidence') is False for w in witnesses)
    for claim in beliefs:
        restriction = claim.get('restriction', [])
        preserved_scope = preserved_scope and len(restriction) == 1
        if len(restriction) == 1:
            operator = restriction[0]
            embedded = operator.get('embedded', [])
            preserved_scope = (preserved_scope and operator.get('kind') == 'operator_scope' and
                operator.get('sense') == 'belief' and operator.get('embedded_fact_projection') is False and
                len(embedded) == 1 and embedded[0].get('predicate') == 'حَاضِر' and
                embedded[0].get('args') == ['mahir'] and embedded[0].get('predicate_kind') == 'property')
    check('scope_preserved', preserved_scope, 'safety')
    check('question_inventory', len(record['questions']) == len(case['expected']['questions']), 'integrity')
    for index, (wanted, actual) in enumerate(zip(case['expected']['questions'], record['questions'])):
        valid, detail = False, None
        try:
            inquiry_inputs = {**record['inputs'], 'text': wanted['text'], 'source_id': 'question'}
            E.validate_report(actual['inquiry'], inquiry_inputs, audit)
            E.validate_answer(actual['answer'], report, actual['inquiry'], record['inputs'], wanted['text'])
            E.require(actual['verification'].get('valid') is True and
                      actual['inquiry_verification'].get('valid') is True, 'Counterexample question replay failed')
            valid = True
        except Exception as error:
            detail = {'type': type(error).__name__, 'message': str(error)}
        answer = actual.get('answer') or {}
        status_match = answer.get('status') == wanted['status']
        questions.append({'index': index, 'status': answer.get('status'), 'expected': wanted['status'],
                          'status_match': status_match, 'independently_validated': valid})
        check('question_integrity:' + str(index), valid, 'integrity', detail)
        check('question_status:' + str(index), status_match,
              'safety' if wanted['status'] == 'UNKNOWN' else 'coverage')
        if wanted['status'] == 'UNKNOWN':
            check('no_embedded_answer_proof:' + str(index), not answer.get('proofs') and not answer.get('bindings'), 'safety')
    return {'id': case['id'], 'passed': all(c['passed'] for c in checks), 'checks': checks, 'questions': questions}


def summarize(scores):
    questions = [q for score in scores for q in score['questions']]
    unsafe = [{'id': s['id'], 'check': c['check']} for s in scores for c in s['checks']
              if c['kind'] == 'safety' and not c['passed']]
    integrity = [{'id': s['id'], 'check': c['check'], 'detail': c['detail']} for s in scores for c in s['checks']
                 if c['kind'] == 'integrity' and not c['passed']]
    return {'total': 6, 'positive_controls': 2, 'negative_cases': 4,
            'passed': sum(s['passed'] for s in scores), 'questions': 4,
            'status_matches': sum(q['status_match'] for q in questions),
            'independently_validated': sum(q['independently_validated'] for q in questions),
            'unsafe_check_failures': unsafe, 'independent_integrity_failures': integrity,
            'gate_pass': len(scores) == 6 and all(s['passed'] for s in scores) and len(questions) == 4
                         and not unsafe and not integrity,
            'not_added_to_historical_denominators': True}


def execute(output_dir):
    E.require(not any(n == 'nabt' or n.startswith('nabt.') for n in sys.modules), 'Fresh runtime process required')
    E.require(not output_dir.exists() and output_dir.is_relative_to(R.ROOT), 'Use a new repository-local output directory')
    material, context = load_cases()
    original_material = R.load_material()[0]
    runner = R.check_runner_freeze(HERE / 'runner_freeze_v4.json')
    runtime_freeze = R.ROOT / 'evidence/source_acquisition_v1/code_freeze_v1.json'
    snapshot = E.runtime_snapshot(runtime_freeze, R.ROOT)
    output_dir.mkdir(parents=True)
    output = output_dir / 'result.json'
    measured, archive = R.capture(snapshot, output, original_material, runner)
    result = {'schema': VERSION, 'started_utc': datetime.now(timezone.utc).isoformat(),
              'material_freeze_sha256': R.MATERIAL_SHA, 'source_material_freeze_sha256': P.SOURCE_MATERIAL,
              'runtime_freeze_sha256': R.RUNTIME_SHA, 'runner': runner, 'snapshot': measured, 'code_archive': archive,
              'cases': [], 'execution_errors': [], 'scoring_errors': [], 'not_a_blind_sample': True,
              'historical_denominators_unchanged': True}
    sys.path.insert(0, str(R.ROOT / 'src'))
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.discourse import read_discourse, ask_discourse, verify_discourse, verify_discourse_answer
    E.verify_import_origins(R.ROOT)
    journal_path = output_dir / 'raw.jsonl.gz'
    inventory, call_id = [], 0
    with gzip.open(journal_path, 'wb') as journal:
        def log(value):
            line = R.dump(value) + b'\n'
            inventory.append({'index': len(inventory), 'bytes': len(line), 'sha256': sha256(line).hexdigest(),
                              'kind': value['kind'], 'case_id': value.get('case_id'), 'call_id': value.get('call_id')})
            journal.write(line)
            journal.flush()

        def call(name, fn, cid, inputs, qi=None):
            nonlocal call_id
            call_id += 1
            row = {'kind': 'public_api_call', 'call_id': call_id, 'name': name, 'case_id': cid,
                   'question_index': qi, 'inputs': inputs}
            try:
                returned = fn()
                row['returned'] = returned
            except Exception as error:
                returned = None
                row['error'] = {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}
                result['execution_errors'].append({'call_id': call_id, 'case_id': cid, 'name': name, 'error': row['error']})
            log(row)
            return returned

        for case in material['cases']:
            cid = case['id']
            raw = (MATERIAL / case['raw_file']).read_bytes()
            models = []

            def acquire():
                models.append(learn_qac_lexicon(raw, source_id=case['source_id']))
                return models[0].summary()

            summary = call('learn_qac_lexicon', acquire, cid,
                           {'source_id': case['source_id'], 'raw_hex': raw.hex(), 'raw_sha256': sha256(raw).hexdigest(),
                            'excluded_verses': []})
            inputs = {**case['input'], 'context': context}
            record = {'case_id': cid, 'inputs': inputs, 'questions': [], 'report': None, 'verification': None}
            if models:
                kwargs = {'lexical_model': models[0], 'context': context,
                          'source_id': inputs['source_id'], 'scope': inputs['scope']}
                public = {**inputs, 'model_summary': summary}
                report = call('read_discourse', lambda: read_discourse(inputs['text'], **kwargs), cid, public)
                record['report'] = report
                if report is not None:
                    record['verification'] = call('verify_discourse', lambda: verify_discourse(report, text=inputs['text'], **kwargs),
                        cid, {**public, 'certificate_report_id': report['report_id']})
                for qi, wanted in enumerate(case['expected']['questions']):
                    question = wanted['text']
                    entry = {}
                    entry['answer'] = call('ask_discourse', lambda: ask_discourse(inputs['text'], question, **kwargs),
                        cid, {**public, 'question': question}, qi)
                    inquiry_kwargs = {**kwargs, 'source_id': 'question'}
                    entry['inquiry'] = call('read_discourse', lambda: read_discourse(question, **inquiry_kwargs),
                        cid, {**public, 'text': question, 'source_id': 'question'}, qi)
                    if entry['inquiry'] is not None:
                        entry['inquiry_verification'] = call('verify_discourse',
                            lambda: verify_discourse(entry['inquiry'], text=question, **inquiry_kwargs), cid,
                            {**public, 'text': question, 'source_id': 'question',
                             'certificate_report_id': entry['inquiry']['report_id']}, qi)
                    if entry['answer'] is not None:
                        entry['verification'] = call('verify_discourse_answer',
                            lambda: verify_discourse_answer(entry['answer'], text=inputs['text'], question=question, **kwargs), cid,
                            {**public, 'question': question, 'certificate_answer_id': entry['answer']['answer_id']}, qi)
                    record['questions'].append(entry)
            try:
                score = score_case(case, record, context)
            except Exception as error:
                detail = {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}
                result['scoring_errors'].append({'case_id': cid, 'error': detail})
                score = {'id': cid, 'passed': False, 'questions': [], 'checks': [
                    {'check': 'scorer_completed', 'passed': False, 'kind': 'integrity', 'detail': detail}]}
            result['cases'].append(score)
            log({'kind': 'case_observation', 'case_id': cid, 'record': record, 'score': score})
            print(json.dumps({'id': cid, 'passed': score['passed']}, ensure_ascii=False), flush=True)
    result['raw_journal'] = R.finish_journal(journal_path, inventory)
    after = E.runtime_snapshot(runtime_freeze, R.ROOT)
    result.update(public_api_calls=call_id, snapshot_after=after, runtime_unchanged=after == snapshot,
                  runner_and_helpers_unchanged=R.check_runner_freeze(HERE / 'runner_freeze_v4.json') == runner,
                  summary=summarize(result['cases']), finished_utc=datetime.now(timezone.utc).isoformat())
    result['measurement_valid'] = not (result['execution_errors'] or result['scoring_errors'] or
                                       result['summary']['independent_integrity_failures'])
    result['gate_pass'] = bool(result['summary']['gate_pass'] and result['measurement_valid'] and
                              result['runtime_unchanged'] and result['runner_and_helpers_unchanged'])
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return 0 if result['gate_pass'] else 1


def review_saved(result_path, raw_path):
    material, context = load_cases()
    result, values, current, runner, inventory = P.checked_artifacts(result_path, raw_path)
    E.require(set(result) == {'schema', 'started_utc', 'material_freeze_sha256', 'source_material_freeze_sha256',
        'runtime_freeze_sha256', 'runner', 'snapshot', 'code_archive', 'cases', 'execution_errors', 'scoring_errors',
        'not_a_blind_sample', 'historical_denominators_unchanged', 'raw_journal', 'public_api_calls', 'snapshot_after',
        'runtime_unchanged', 'runner_and_helpers_unchanged', 'summary', 'finished_utc', 'measurement_valid', 'gate_pass'},
        'Counterexample result added or omitted fields')
    E.require(result['schema'] == VERSION and result['source_material_freeze_sha256'] == P.SOURCE_MATERIAL
              and result['not_a_blind_sample'] is True and result['historical_denominators_unchanged'] is True,
              'Counterexample evaluation contract changed')
    cursor, call_id = 0, 0

    def take(name, cid, inputs, qi=None):
        nonlocal cursor, call_id
        E.require(cursor < len(values), 'Counterexample call omitted')
        row = values[cursor]
        cursor += 1
        call_id += 1
        E.require(set(row) == {'kind', 'call_id', 'name', 'case_id', 'question_index', 'inputs', 'returned'} and
                  row['kind'] == 'public_api_call' and type(row['call_id']) is int and row['call_id'] == call_id
                  and row['name'] == name and row['case_id'] == cid and E.wire(row['question_index']) == E.wire(qi)
                  and E.wire(row['inputs']) == E.wire(inputs), 'Counterexample call/inputs omitted, changed, reordered or errored')
        return row['returned']

    scores = []
    for case in material['cases']:
        cid, raw = case['id'], (MATERIAL / case['raw_file']).read_bytes()
        summary = take('learn_qac_lexicon', cid, {'source_id': case['source_id'], 'raw_hex': raw.hex(),
                                                'raw_sha256': sha256(raw).hexdigest(), 'excluded_verses': []})
        inputs = {**case['input'], 'context': context}
        public = {**inputs, 'model_summary': summary}
        report = take('read_discourse', cid, public)
        E.require(E.wire(report['lexical_model']) == E.wire(summary), 'Report changed its acquired raw model')
        verification = take('verify_discourse', cid, {**public, 'certificate_report_id': report['report_id']})
        record = {'case_id': cid, 'inputs': inputs, 'questions': [], 'report': report, 'verification': verification}
        for qi, wanted in enumerate(case['expected']['questions']):
            question = wanted['text']
            answer = take('ask_discourse', cid, {**public, 'question': question}, qi)
            inquiry = take('read_discourse', cid, {**public, 'text': question, 'source_id': 'question'}, qi)
            inquiry_verification = take('verify_discourse', cid,
                {**public, 'text': question, 'source_id': 'question', 'certificate_report_id': inquiry['report_id']}, qi)
            answer_verification = take('verify_discourse_answer', cid,
                {**public, 'question': question, 'certificate_answer_id': answer['answer_id']}, qi)
            record['questions'].append({'answer': answer, 'inquiry': inquiry,
                                        'inquiry_verification': inquiry_verification, 'verification': answer_verification})
        E.require(cursor < len(values), 'Counterexample observation omitted')
        observation = values[cursor]
        cursor += 1
        score = score_case(case, record, context)
        E.require(E.wire(observation) == E.wire({'kind': 'case_observation', 'case_id': cid, 'record': record, 'score': score}),
                  'Counterexample observations/scores not bound to actual public calls')
        scores.append(score)
    summary = summarize(scores)
    E.require(cursor == len(values) == 40 and call_id == result['public_api_calls'] == 34,
              'Counterexample records added, repeated or omitted')
    E.require(E.wire(scores) == E.wire(result['cases']) and E.wire(summary) == E.wire(result['summary']),
              'Counterexample score differs from independent fresh validation')
    E.require(result['execution_errors'] == [] and result['scoring_errors'] == []
              and result['measurement_valid'] is True and result['gate_pass'] is True
              and summary['gate_pass'] is True, 'Counterexample source guard failed')
    E.require(E.wire(R.check_runner_freeze(HERE / 'runner_freeze_v4.json')) == E.wire(runner) and
              E.wire(E.runtime_snapshot(R.ROOT / 'evidence/source_acquisition_v1/code_freeze_v1.json', R.ROOT)) == E.wire(current),
              'Runtime/dependencies changed during source-counterexample review')
    return {'schema': 'nabt.completion-source-counterexample-review.v1', 'summary': summary,
            'source_material_freeze_sha256': P.SOURCE_MATERIAL, 'runtime_freeze_sha256': R.RUNTIME_SHA,
            'dependency_freeze_sha256': runner['sha256'], 'raw_journal': inventory,
            'all_public_calls_and_observations_bound': True, 'independently_rescored': True,
            'new_runtime_calls_in_review': 0, 'gate_pass': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    sys.exit(execute(args.output_dir.resolve()))
