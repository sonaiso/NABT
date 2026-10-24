#!/usr/bin/env python3
"""Bounded, post-execution H18 checker review of the preserved first run.

This does not run or alter the frozen holdout scorer. It supplements the stored
H18 question with its report from the exact frozen runtime, verifies the same
report identity, and applies the independent answer validators. Its adjusted
metric is explicitly a post-review rescore of already observed predictions.
"""
import argparse
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
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'evidence/arabic_coverage'
RUNTIME_SHA256 = 'a7194b9b52ab8a6db0c92d65c7dae76dc23c1f1c8777b4e10b2fb71efa01c89f'
MATERIAL_SHA256 = '127a5870fcbc8f8823b95f2a9f452cf4cd87de22fcfc62b271efd32bc684c106'
FIRST_RESULT_SHA256 = 'da114e1ccedee5a523b599e006ec0da178e04ee38d4235699bd982c9c6e20c4e'


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest_file(path):
    return sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(path):
    return {'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size, 'sha256': digest_file(path)}


def write_new(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write('\n')
    return identity(path)


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    require(not any((output / name).exists() for name in ('review.json', 'question_report.json', 'oracle_erratum.json')),
            'Refusing to overwrite any previous post-review artifact')
    material_path, runtime_path = FOLDER / 'holdout_v2/freeze.json', FOLDER / 'code_freeze_v1.json'
    result_path, raw_path = FOLDER / 'holdout_runs_v1/first_v2.json', FOLDER / 'holdout_runs_v1/first_v2.raw.jsonl.gz'
    require(digest_file(material_path) == MATERIAL_SHA256, 'Holdout v2 freeze changed')
    require(digest_file(runtime_path) == RUNTIME_SHA256, 'Frozen first-run runtime manifest changed')
    require(digest_file(result_path) == FIRST_RESULT_SHA256, 'Preserved first-run result changed')
    material_freeze, runtime = json.loads(material_path.read_bytes()), json.loads(runtime_path.read_bytes())
    preservation_path = FOLDER / 'holdout_runs_v1/preservation.json'
    preservation = json.loads(preservation_path.read_bytes())
    checked_inputs = [identity(path) for path in (material_path, runtime_path, result_path, raw_path, preservation_path)]
    for item in material_freeze['files'] + preservation['files']:
        path = ROOT / item['path']
        require(path.stat().st_size == item['bytes'] and digest_file(path) == item['sha256'],
                'Frozen input or preserved first-run artifact changed: ' + item['path'])
        checked_inputs.append(identity(path))
    with gzip.open(raw_path, 'rb') as handle:
        raw = handle.read()
    require(sha256(raw).hexdigest() == preservation['raw_uncompressed_sha256'], 'First-run raw journal changed')
    records = [json.loads(line) for line in raw.splitlines()]
    def record(call, case_id, question_index=None):
        matches = [row['value'] for row in records if row['call'] == call and row['case_id'] == case_id
                   and (question_index is None or row.get('question_index') == question_index)]
        require(len(matches) == 1, 'Raw record is missing or not unique')
        return matches[0]
    document, answer = record('read_discourse', 'H18'), record('ask_discourse', 'H18', 2)
    require(record('verify_discourse_answer', 'H18', 2).get('valid') is True, 'Original answer replay did not pass')
    cases = json.loads((FOLDER / 'holdout_v2/cases.json').read_bytes())['cases']
    case = next(case for case in cases if case['id'] == 'H18')
    context = json.loads((FOLDER / 'holdout_v2/contexts.json').read_bytes())[case['context']]
    inputs = {'text': case['text'], 'context': context, 'source_id': 'holdout_h18', 'scope': 'independent_holdout_v1'}
    question = case['questions'][2]['text']
    require(case['questions'][2]['expected_status'] == answer['status'] == 'UNKNOWN', 'The reviewed status changed')
    require(answer['kind'] in ('person', 'subject') and not answer['proofs'] and not answer['bindings']
            and answer['counterproofs'], 'The bounded UNKNOWN-with-counterproofs premise does not hold')
    require(answer['question_text'] == question and answer['source_text'] == inputs['text'], 'Reviewed input identity changed')
    archive = runtime_path.parent / runtime['archive_filename']
    require(digest_file(archive) == runtime['archive_sha256'], 'Frozen runtime archive changed')
    checked_inputs.append(identity(archive))
    validators = [ROOT / 'tools' / name for name in ('discourse_evaluation.py', 'construction_evaluation.py',
                                                    'question_answer_validation.py')]
    validator_identity = [identity(path) for path in validators]
    require(not any(name == 'nabt' or name.startswith('nabt.') for name in sys.modules),
            'A different NABT runtime was already imported')
    sys.dont_write_bytecode = True
    with TemporaryDirectory(prefix='nabt-h18-postreview-') as directory:
        isolated = Path(directory)
        entries = {entry['path']: entry for entry in runtime['files']}
        require(len(entries) == len(runtime['files']), 'Frozen runtime contains duplicate paths')
        with tarfile.open(archive, 'r:gz') as saved:
            members = saved.getmembers()
            require(len(members) == len(entries) and {member.name for member in members} == set(entries),
                    'Frozen runtime archive inventory differs from its manifest')
            for member in members:
                path = Path(member.name)
                require(member.isfile() and not path.is_absolute() and '..' not in path.parts,
                        'Unsafe member in frozen runtime archive')
                data = saved.extractfile(member).read()
                require(len(data) == entries[member.name]['bytes']
                        and sha256(data).hexdigest() == entries[member.name]['sha256'], 'Frozen runtime member changed')
                target = isolated / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        sys.path.insert(0, str(isolated / 'src'))
        corpus = importlib.import_module('nabt.corpus_evidence')
        api = importlib.import_module('nabt.discourse')
        model = corpus.learn_qac_lexicon((FOLDER / 'holdout_v2/lexical_premises.tsv').read_bytes(),
                                        source_id='independent_arabic_holdout_v1')
        require(model.summary() == record('lexical_summary', None), 'Supplementary replay learned different premises')
        inquiry = api.read_discourse(question, lexical_model=model, context=deepcopy(context),
                                     source_id='question', scope=inputs['scope'])
        require(inquiry['report_id'] == answer['question_report_id'],
                'Supplementary inquiry differs from the original answer question report')
        replay = api.verify_discourse_answer(answer, text=case['text'], question=question, lexical_model=model,
                                             context=deepcopy(context), source_id=inputs['source_id'], scope=inputs['scope'])
        require(replay.get('valid') is True, 'Exact frozen-runtime supplementary answer replay failed')
        for name, module in list(sys.modules.items()):
            if name == 'nabt' or name.startswith('nabt.'):
                require(Path(module.__file__).resolve().is_relative_to(isolated / 'src'), 'Cross-runtime import')
        require(all((isolated / path).stat().st_size == entry['bytes']
                    and digest_file(isolated / path) == entry['sha256'] for path, entry in entries.items()),
                'Frozen runtime bytes changed during supplementary replay')
    validations = []
    for path in validators[:2]:
        spec = importlib.util.spec_from_file_location('postreview_' + path.stem, path)
        evaluator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(evaluator)
        evaluator.validate_report(document, inputs)
        evaluator.validate_report(inquiry, {**inputs, 'text': question, 'source_id': 'question'})
        evaluator.validate_answer(answer, document, inquiry, inputs, question)
        validations.append({'evaluator': str(path.relative_to(ROOT)), 'document_valid': True,
                            'inquiry_valid': True, 'all_interpretations_and_answer_receipts_valid': True})
    require([identity(path) for path in validators] == validator_identity, 'Validator code changed during the review')
    accepted = {claim['claim_id']: claim for claim in document['claims']}
    negative_ids = sorted({proof['claim_id'] for proof in answer['counterproofs']})
    require(all(accepted[claim_id]['positive'] is False for claim_id in negative_ids), 'A counterproof is not negative')
    first = json.loads(result_path.read_bytes())
    target = next(row for row in first['cases'] if row['id'] == 'H18')
    failed = [check for check in target['checks'] if check['pass'] is not True]
    require(len(failed) == 1 and failed[0]['name'] == 'question:2:no_grounded_evidence'
            and failed[0].get('unsafe_acceptance') is True, 'The original H18 failure is not the bounded checker defect')
    reclassified = [entry for entry in first['unsafe_acceptances']
                    if entry['case_id'] == 'H18' and entry['name'] == failed[0]['name']]
    require(len(reclassified) == 1, 'Original unsafe-acceptance entry is missing or duplicated')
    remaining_unsafe = [entry for entry in first['unsafe_acceptances'] if entry not in reclassified]
    case_results = [{'case_id': row['id'], 'original_passed': row['passed'],
                     'postreview_passed': True if row['id'] == 'H18' else row['passed'],
                     'checker_erratum_applied': row['id'] == 'H18'} for row in first['cases']]
    erratum = {'schema': 'nabt.independent-holdout-postexecution-checker-erratum.v1',
               'identified_after_first_predictions': True, 'frozen_inputs_or_scorer_changed': False,
               'case_id': 'H18', 'question_index_zero_based': 2, 'question': question,
               'original_failed_check': failed[0], 'original_unsafe_acceptance_entry': reclassified[0],
               'original_scorer': identity(ROOT / 'tools/arabic_coverage_holdout_v1.py'),
               'defect': 'The frozen scorer demands no counterproofs for every UNKNOWN. A variable question can have no positively proved bindings while retaining exact counterproofs for named candidates.',
               'bounded_correction': 'For this stored WH UNKNOWN result, require no positive proofs or returned bindings, and validate every counterproof, substitution, signed qualified claim, ADJ witness, and query interpretation independently.',
               'unchanged_expected_status': 'UNKNOWN', 'unchanged_observed_status': 'UNKNOWN',
               'no_new_blind_test_claim': True, 'preserve_original_unsafe_flag_in_original_result': True,
               'full_question_report_limitation': 'The first raw journal did not capture inquiry reports separately. This review supplements only H18 question 2 using the exact frozen runtime and requires the original question_report_id.'}
    inquiry_file = write_new(output / 'question_report.json', inquiry)
    erratum_file = write_new(output / 'oracle_erratum.json', erratum)
    for item in checked_inputs:
        require(identity(ROOT / item['path']) == item, 'Original evidence changed during post-review')
    review = {'schema': 'nabt.independent-arabic-postreview-rescore.v1',
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'review_mode': 'Post-execution bounded checker correction on the same stored predictions; not a new blind score.',
              'code': identity(Path(__file__)), 'independent_validators': validator_identity,
              'checked_original_inputs': checked_inputs, 'original_inputs_unchanged': True,
              'question_report': inquiry_file, 'oracle_erratum': erratum_file,
              'supplementary_replay': {'runtime_manifest_sha256': RUNTIME_SHA256, 'runtime_unchanged': True,
                  'question_report_id_matches_original': True, 'question_report_id': inquiry['report_id'],
                  'answer_id': answer['answer_id'], 'verification': replay},
              'independent_validation': validations, 'accepted_negative_claim_ids': negative_ids,
              'counterproof_count': len(answer['counterproofs']), 'positive_proof_count': len(answer['proofs']),
              'positive_binding_count': len(answer['bindings']),
              'original_case_score': first['case_score'], 'original_unsafe_acceptances': first['unsafe_acceptances'],
              'reclassified_checker_false_alarms': reclassified, 'remaining_unsafe_acceptances': remaining_unsafe,
              'postreview_case_score': {'passed': sum(row['postreview_passed'] for row in case_results), 'total': len(case_results)},
              'case_results': case_results, 'unchanged_question_status_counts': first['question_status_by_expectation'],
              'remaining_failed_case_ids': [row['case_id'] for row in case_results if not row['postreview_passed']],
              'strict_frozen_first_result_still_failed': first['strict_pass'] is False,
              'universal_Arabic_completeness_established': False}
    write_new(output / 'review.json', review)
    print(json.dumps({'review': str((output / 'review.json').relative_to(ROOT)),
                      'original': review['original_case_score'], 'postreview': review['postreview_case_score'],
                      'reclassified_unsafe_flags': len(reclassified), 'remaining_unsafe_flags': len(remaining_unsafe),
                      'remaining_failed_cases': review['remaining_failed_case_ids']}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.output_directory.resolve())
