#!/usr/bin/env python3
"""Reproduce PR19's source-sense mismatch on the exact pre-fix commit.

Only an isolated, archived runtime is imported. Historical evidence and the
working runtime are never edited. These authored review cases are not a blind
linguistic sample and do not change the original evaluation denominators.
"""
from datetime import datetime, timezone
from hashlib import sha256
import gzip
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = HERE / 'before_run_v1'
COMMIT = 'd26342bafce26c9e5c1c725682cb49b035450688'
FREEZE = 'evidence/arabic_completion_v3/code_freeze_v1.json'
FREEZE_SHA = 'eeb9864b08e8ae25e841b18b0d25858d95268fce2435d51c340d69a41782f089'
ARCHIVE_SHA = '8576765bdd5b9dbb93db76ec11b485634fa2f34691113a45d59dbf49238c0c87'
TOOLS = ('construction_evaluation.py', 'source_name_validation.py', 'question_answer_validation.py',
         'arabic_coverage_gate.py', 'arabic_completion_gate.py')
TEXT = 'حَسِبَ زيدٌ سالمًا حكيمًا.'
BASE_FEATURES = 'STEM|POS:V|PERF|LEM:Hasiba|ROOT:Hsb|3MS'
CASES = [
    ('control_implicit_I', 'Hasiba', BASE_FEATURES, True),
    ('control_explicit_I', 'Hasiba', BASE_FEATURES.replace('|PERF|', '|PERF|(I)|'), True),
    ('control_explicit_ACT', 'Hasiba', BASE_FEATURES.replace('|PERF|', '|PERF|ACT|'), True),
    ('review_form_II', 'Hasiba', BASE_FEATURES.replace('|PERF|', '|PERF|(II)|'), False),
    ('review_unvocalized_raw', 'Hsb', BASE_FEATURES, False),
    ('negative_wrong_person', 'Hasiba', BASE_FEATURES.replace('|3MS', '|2MS'), False),
    ('negative_conflicting_person', 'Hasiba', BASE_FEATURES.replace('|3MS', '|2MS|3MS'), False),
    ('negative_passive', 'Husiba', BASE_FEATURES.replace('|PERF|', '|PERF|PASS|'), False),
    ('negative_mixed_aspect', 'Hasiba', BASE_FEATURES.replace('|PERF|', '|PERF|IMPF|'), False),
    ('negative_wrong_root', 'Hasiba', BASE_FEATURES.replace('ROOT:Hsb', 'ROOT:Elm'), False),
    ('negative_withdrawn', None, None, False),
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def git_bytes(name):
    return subprocess.run(['git', 'show', COMMIT + ':' + name], cwd=ROOT,
                          check=True, capture_output=True).stdout


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(data)


def save(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode() + b'\n')


def identity(name, data):
    return {'path': name, 'bytes': len(data), 'sha256': sha256(data).hexdigest()}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def captured(function):
    try:
        value = function()
    except Exception as error:
        return {'valid': False, 'error_type': type(error).__name__, 'message': str(error)}
    return {'valid': True, 'returned': value}


def main():
    require(not RUN.exists(), 'Refusing to replace a reproduction')
    require(not any(n == 'nabt' or n.startswith('nabt.') for n in sys.modules), 'Runtime already imported')
    started = datetime.now(timezone.utc).isoformat()
    manifest_bytes = git_bytes(FREEZE)
    require(sha256(manifest_bytes).hexdigest() == FREEZE_SHA, 'Historical freeze bytes differ')
    manifest = json.loads(manifest_bytes)
    archive_path = str(Path(FREEZE).parent / manifest['archive_filename'])
    archive_bytes = git_bytes(archive_path)
    require(sha256(archive_bytes).hexdigest() == ARCHIVE_SHA, 'Historical archive bytes differ')
    training = git_bytes('examples/construction_training.tsv')
    context_bytes = git_bytes('examples/construction_context.json')
    context = json.loads(context_bytes)
    RUN.mkdir()
    write(RUN / 'base_training.tsv', training)
    write(RUN / 'context.json', context_bytes)
    matrix = {'schema': 'nabt.hasiba-postpublication-review-matrix.v1', 'created_utc': started,
        'basis': 'AUTHORED_AFTER_GITHUB_REVIEW_NOT_BLIND_NOT_ORIGINAL_GOLD',
        'reported_review_comment_id': '4367840528', 'runtime_commit': COMMIT, 'target': TEXT,
        'cases': [{'id': cid, 'raw_form': form, 'raw_features': features,
                   'source_sense_premises_expected': expected} for cid, form, features, expected in CASES]}
    save(RUN / 'case_matrix.json', matrix)
    preserved = [identity('examples/construction_training.tsv', training),
                 identity('examples/construction_context.json', context_bytes)]
    tool_bytes = {name: git_bytes('tools/' + name) for name in TOOLS}
    for name, data in tool_bytes.items():
        write(RUN / 'before_code/tools' / name, data)
        preserved.append(identity('tools/' + name, data))
    for name in ('construction_reader.py', 'corpus_evidence.py'):
        data = git_bytes('src/nabt/' + name)
        write(RUN / 'before_code/src/nabt' / name, data)
        preserved.append(identity('src/nabt/' + name, data))

    results, raw_records, imported = [], [], []
    with tempfile.TemporaryDirectory(prefix='isolated-commit-', dir=RUN) as temporary:
        isolated = Path(temporary)
        by_path = {item['path']: item for item in manifest['files']}
        require(len(by_path) == len(manifest['files']) == 80, 'Historical runtime inventory changed')
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode='r:gz') as archive:
            members = archive.getmembers()
            require(len(members) == 80 and {m.name for m in members} == set(by_path)
                    and all(m.isfile() for m in members), 'Historical runtime archive inventory changed')
            for member in members:
                relative = Path(member.name)
                require(not relative.is_absolute() and '..' not in relative.parts, 'Unsafe archived runtime path')
                data = archive.extractfile(member).read()
                require(identity(member.name, data) == by_path[member.name], 'Archive member identity differs')
                require(data == git_bytes(member.name), 'Archived runtime differs from the committed runtime')
                write(isolated / member.name, data)
        for name, data in tool_bytes.items():
            write(isolated / 'tools' / name, data)
        sys.path.insert(0, str(isolated / 'src'))
        from nabt.corpus_evidence import learn_qac_lexicon
        from nabt.discourse import read_discourse, verify_discourse
        E = load_module('postpublication_committed_independent_evaluator', isolated / 'tools/construction_evaluation.py')
        V = E.source_validation
        for cid, raw_form, features, expected in CASES:
            suffix = b'' if raw_form is None else f'(9:80:1:1)\t{raw_form}\tV\t{features}\n'.encode()
            raw = training + suffix
            request = {'text': TEXT, 'source_id': 'postpublication_hasiba_' + cid,
                       'scope': 'source-review', 'context': context}
            lexical_source_id = 'authored_hasiba_' + cid
            write(RUN / 'inputs' / (cid + '.tsv'), raw)
            save(RUN / 'inputs' / (cid + '.json'), {**request, 'lexical_source_id': lexical_source_id})
            model = learn_qac_lexicon(raw, source_id=lexical_source_id)
            report = read_discourse(**request, lexical_model=model)
            verification = verify_discourse(report, **request, lexical_model=model)
            audit = E.SourceAudit(raw, model.excluded_verses, model.source_id)
            rows, _ = E.reading_rows(report)
            witnesses = []
            for clause in report['clauses']:
                for analysis in clause['analyses']:
                    for relation in analysis['relations']:
                        if 'independent_sense_witness' in relation:
                            checked = captured(lambda: V.validate_sense_witness(relation, analysis, rows, request, audit))
                            row = rows[relation['operator_reading_id']]
                            proofs = [p for p in row['support_records'] if isinstance(p, dict) and 'record_id' in p]
                            witnesses.append({'clause_id': clause['clause_id'], 'analysis_id': analysis['analysis_id'],
                                'reading_id': row['reading_id'], 'lexical_features': row['lexical_features'],
                                'source_records': [audit.receipt(p) for p in proofs],
                                'independent_validation': checked})
            whole = captured(lambda: E.validate_report(report, request, audit))
            row = {'id': cid, 'source_sense_premises_expected': expected,
                'raw_suffix': suffix.decode(), 'raw_source_sha256': sha256(raw).hexdigest(),
                'status': report['status'], 'claims': len(report['claims']),
                'claim_kinds': sorted({c['predicate_kind'] for c in report['claims']}),
                'runtime_verification': verification,
                'witness_count': len(witnesses),
                'independent_sense_results': [w['independent_validation'] for w in witnesses],
                'independent_report_validation': whole,
                'obligations': sorted({o for c in report['clauses'] for a in c['analyses'] for o in a['obligations']}),
                'world_truth': report['world_truth']}
            results.append(row)
            raw_records.append({'kind': 'authored_review_case', 'id': cid, 'inputs': request,
                'lexical_source_id': lexical_source_id, 'lexical_raw': raw.decode(),
                'model_summary': model.summary(), 'report': report, 'runtime_verification': verification,
                'sense_witness_checks': witnesses, 'independent_report_validation': whole})
            print(json.dumps({'id': cid, 'status': row['status'], 'verify': verification.get('valid'),
                'witnesses': len(witnesses), 'independent_valid': whole['valid']}, ensure_ascii=False), flush=True)
        for name, module in sorted(sys.modules.items()):
            if name == 'nabt' or name.startswith('nabt.'):
                path = Path(module.__file__).resolve()
                require(path.is_relative_to(isolated / 'src'), 'Runtime import escaped the isolated committed source')
                imported.append(identity(path.relative_to(isolated).as_posix(), path.read_bytes()))
        require(all(identity(name, (isolated / name).read_bytes()) == row for name, row in by_path.items()),
                'Historical runtime changed during reproduction')
    by_id = {row['id']: row for row in results}
    for cid in ('review_form_II', 'review_unvocalized_raw'):
        row = by_id[cid]
        require(row['status'] == 'LICENSED_DISCOURSE' and row['runtime_verification'].get('valid') is True
                and row['witness_count'] > 0 and not row['independent_report_validation']['valid']
                and all(not check['valid'] for check in row['independent_sense_results']), 'Reported discrepancy did not reproduce')
    for cid in ('control_implicit_I', 'control_explicit_I', 'control_explicit_ACT'):
        row = by_id[cid]
        require(row['status'] == 'LICENSED_DISCOURSE' and row['runtime_verification'].get('valid') is True
                and row['independent_report_validation']['valid'] and row['witness_count'] > 0
                and all(check['valid'] for check in row['independent_sense_results']), 'Legitimate control failed')
    journal = b''.join(wire(record) + b'\n' for record in raw_records)
    write(RUN / 'raw_before_v1.jsonl.gz', gzip.compress(journal, mtime=0))
    reopened = gzip.decompress((RUN / 'raw_before_v1.jsonl.gz').read_bytes())
    require(reopened == journal and reopened.endswith(b'\n') and len(reopened.splitlines()) == len(CASES), 'Raw journal incomplete')
    for line, expected in zip(reopened.splitlines(keepends=True), raw_records):
        require(line == wire(json.loads(line)) + b'\n' and json.loads(line) == expected, 'Raw case replay differs')
    summary = {'schema': 'nabt.hasiba-postpublication-reproduction.v1', 'started_utc': started,
        'completed_utc': datetime.now(timezone.utc).isoformat(), 'runtime_commit': COMMIT,
        'runtime_freeze': identity(FREEZE, manifest_bytes), 'runtime_archive': identity(archive_path, archive_bytes),
        'all_80_archived_runtime_files_equal_commit': True, 'isolated_runtime_imports': imported,
        'historical_runtime_unchanged': True, 'original_evidence_or_gold_modified': False,
        'preserved_source_inputs_and_validators': preserved,
        'reproducer': identity(str(Path(__file__).relative_to(ROOT)), Path(__file__).read_bytes()),
        'raw_journal': identity(str((RUN / 'raw_before_v1.jsonl.gz').relative_to(ROOT)), (RUN / 'raw_before_v1.jsonl.gz').read_bytes()),
        'raw_uncompressed_sha256': sha256(journal).hexdigest(), 'raw_record_count': len(raw_records),
        'reported_discrepancies_reproduced': ['review_form_II', 'review_unvocalized_raw'],
        'cases': results,
        'scope': 'Postpublication authored source-premise counterexamples, not an accuracy estimate or new blind oracle.',
        'implementation_bug_confirmed': True, 'runtime_replay_is_not_independent_source_validation': True,
        'world_truth_established': False}
    save(RUN / 'result.json', summary)
    print(json.dumps({'result': str(RUN / 'result.json'), 'reported_discrepancies_reproduced': True,
                      'cases': len(results)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
