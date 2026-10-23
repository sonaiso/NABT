#!/usr/bin/env python3
"""Authored, pre-correction context-only name agreement regression."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import sys
import tarfile
import traceback

FOLDER = Path(__file__).resolve().parent
MATERIAL_PIN = 'db70a1ccad6ba0114b4fb1dbdaa93e7561a616c27cfcc5ea18191d0603741a58'
PINS = {
    '42476d67e30e7e86506c3e878552966ce9dc784ae1e5d98bec3af50e6f0a1aa5': {
        'snapshot_sha256': '3a6e9594cf6b094ca6bfce61a4969e854604f5fc4520db90c793aa7fda0b4e58',
        'archive_sha256': '62d395428f49785c005ceaf55d86ed1e66cce12453d8ed2a03146436b5ba0567',
        'file_count': 74,
    },
    '23d04d307c3e560c8198ee0700923673af001a8835d8e00d6c11d79534e6d611': {
        'snapshot_sha256': '2c1b6b30e22b5322046109b461f850974e356736f2aedb06c4911be82375188f',
        'archive_sha256': 'b5363658881c8e265295ad727d346ea8925348e9342b89f50eb014be824a19f1',
        'file_count': 74,
    },
}
NON_RUNTIME = frozenset({'src/nabt/data/source_evidence/README.md',
                        'src/nabt/data/source_evidence/LICENSE-DATA.md',
                        'src/nabt/data/source_evidence/.gitattributes'})
CLAIM_FIELDS = ('predicate', 'predicate_kind', 'voice', 'args', 'positive',
                'tense', 'time', 'place', 'restriction')

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(data):
    return sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_path(value):
    path = Path(value)
    require(not path.is_absolute() and '..' not in path.parts, 'Unsafe inventory path')
    return path


def load_material():
    raw = (FOLDER / 'material_freeze_v1.json').read_bytes()
    require(digest(raw) == MATERIAL_PIN, 'Material freeze changed')
    freeze = json.loads(raw)
    for item in freeze['files']:
        payload = (FOLDER / safe_path(item['path'])).read_bytes()
        require(len(payload) == item['bytes'] and digest(payload) == item['sha256'], 'Frozen material changed: ' + item['path'])
    material = json.loads((FOLDER / 'material_v1.json').read_bytes())
    require(len(material['cases']) == freeze['case_count'] == 16, 'Case inventory changed')
    require(len({c['id'] for c in material['cases']}) == 16, 'Duplicate case')
    return freeze, material

def snapshot(manifest_path, runtime_root):
    raw = manifest_path.read_bytes()
    pin = PINS.get(digest(raw))
    require(pin is not None, 'Unapproved runtime manifest')
    manifest = json.loads(raw)
    files = manifest['files']
    require(len(files) == pin['file_count'], 'Runtime file count changed')
    require(digest(canonical(files)) == manifest['snapshot_sha256'] == pin['snapshot_sha256'], 'Runtime snapshot changed')
    require(manifest['archive_sha256'] == pin['archive_sha256'], 'Archive pin changed')
    paths = [r['path'] for r in files]
    require(len(set(paths)) == len(paths), 'Duplicate runtime file')
    actual = {'pyproject.toml'} | {str(p.relative_to(runtime_root)) for p in (runtime_root / 'src').rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and not any(s.endswith(('.egg-info', '.dist-info')) for s in p.parts)}
    require(actual - NON_RUNTIME == set(paths), 'Authoritative runtime inventory changed')
    for item in files:
        path = runtime_root / safe_path(item['path'])
        payload = path.read_bytes()
        require(not path.is_symlink() and len(payload) == item['bytes'] and digest(payload) == item['sha256'], 'Runtime file changed: ' + item['path'])
    archive = manifest_path.parent / safe_path(manifest['archive_filename'])
    require(digest(archive.read_bytes()) == pin['archive_sha256'], 'Runtime archive changed')
    by_name = {r['path']: r for r in files}
    with tarfile.open(archive, 'r:gz') as saved:
        members = saved.getmembers()
        require(len(members) == len(paths) and {m.name for m in members} == set(paths) and all(m.isfile() for m in members), 'Archive inventory changed')
        for member in members:
            payload = saved.extractfile(member).read()
            item = by_name[member.name]
            require(len(payload) == item['bytes'] and digest(payload) == item['sha256'], 'Archive member changed')
    return {'manifest_path': str(manifest_path), 'manifest_sha256': digest(raw),
            'runtime_root': str(runtime_root), 'snapshot_sha256': pin['snapshot_sha256'],
            'archive_sha256': pin['archive_sha256'], 'file_count': len(paths),
            'excluded_documentation': sorted(actual & NON_RUNTIME)}


def check_origins(runtime_root):
    origins = {}
    source_root = (runtime_root / 'src').resolve()
    for name, module in sys.modules.items():
        if name == 'nabt' or name.startswith('nabt.'):
            origin = getattr(module, '__file__', None)
            require(origin is not None, 'Unidentified runtime origin')
            path = Path(origin).resolve()
            require(path.is_relative_to(source_root), 'Runtime import escaped selected root: ' + name)
            origins[name] = str(path.relative_to(runtime_root))
    return origins


def claim_view(claim):
    return {key: claim.get(key) for key in CLAIM_FIELDS}


def span_ok(span, text, surface, offset):
    raw = text.encode('utf-8')
    start, end = offset, offset + len(surface.encode('utf-8'))
    return (type(span) is dict and span.get('start') == start and span.get('end') == end and
            span.get('source_id') == 'input' and span.get('source_sha256') == digest(raw) and
            span.get('span_sha256') == digest(raw[start:end]))


def source_profiles(case):
    values = []
    for line in (FOLDER / safe_path(case['source'])).read_text().splitlines()[1:]:
        _, _, pos, features = line.split('\t')
        if pos not in ('N', 'PN'):
            continue
        fields = features.split('|')
        gender = 'masculine' if 'MS' in fields else 'feminine' if 'FS' in fields else None
        number = 'singular' if 'MS' in fields or 'FS' in fields else None
        values.append((pos, gender, number))
    return set(values)


def score(case, document, answer, verification, changed=None):
    expected = case['expected']
    failures, integrity = [], []
    def check(ok, name, *, safety=False):
        if not ok:
            failures.append(name)
            if safety:
                integrity.append(name)
    check(document['status'] == expected['document_status'], 'document_status')
    check(answer['status'] == expected['answer_status'], 'answer_status')
    check(len(document['claims']) == expected['claim_count'], 'claim_count')
    check(all(v.get('valid') is True and v.get('status') == 'VERIFIED' for v in verification.values()), 'original_source_replay', safety=True)
    check(verification['document'].get('report_id') == document['report_id'] and
          verification['answer'].get('answer_id') == answer['answer_id'], 'replay_identities', safety=True)
    subject_surface, predicate_surface = case['text'].removesuffix('.').split(' ')
    offset = len((subject_surface + ' ').encode('utf-8'))
    subjects = [o for o in document['occurrences'] if span_ok(o.get('span'), case['text'], subject_surface, 0)]
    check(len(subjects) == 1, 'subject_occurrence')
    subject_rows = [r for o in subjects for r in o['readings'] if r['kind'] == 'noun']
    if expected['context_profile_must_not_become_lexical_features']:
        naming_rows = [r for r in subject_rows if any(s.get('kind') == 'explicit_context' and
                       s.get('field') == 'entities.name' for s in r.get('support_records', []))]
        check(bool(naming_rows), 'context_name_reading')
        check(all(r['lexical_features'].get('gender') is None and r['lexical_features'].get('number') is None and
                  r.get('construction') is None and r.get('class_candidates') == [] for r in naming_rows),
              'lexical_profile_unchanged', safety=True)
    else:
        profiles = source_profiles(case)
        sourced = [r for r in subject_rows if r['lexical_features'].get('pos') in ('N', 'PN')]
        check(bool(sourced), 'source_noun_reading')
        check(all((r['lexical_features'].get('pos'), r['lexical_features'].get('gender'),
                   r['lexical_features'].get('number')) in profiles and not any(
                   s.get('kind') == 'explicit_context' for s in r.get('support_records', [])) for r in sourced),
              'independent_lexical_profile_not_overridden', safety=True)
    analyses = [a for c in document['clauses'] for a in c['analyses']]
    if 'expected_reference_candidates' in case:
        references = [r for a in analyses for r in a['references']
                      if span_ok(r.get('span'), case['text'], subject_surface, 0)]
        check(bool(references) and all(r['bound_entity_id'] is None and
              sorted(r['candidate_entity_ids']) == case['expected_reference_candidates'] for r in references),
              'all_same_name_competitors_preserved', safety=True)
    if expected['positive_agreement_required']:
        wanted = expected['grounded_claim']
        check([claim_view(c) for c in document['claims']] == [wanted], 'exact_grounded_claim')
        viable = [a for a in analyses if a['licensed_syntax'] and a['references_complete'] and not a['rejected_candidate']]
        check(bool(viable), 'complete_viable_analysis')
        for i, analysis in enumerate(viable):
            prefix = 'analysis:' + str(i) + ':'
            check(analysis['claims'] == [wanted], prefix + 'exact_claim', safety=True)
            subject_edges = [a for a in analysis['assignments'] if a.get('actual_role') == 'nominal_subject' and
                             span_ok(a.get('span'), case['text'], subject_surface, 0)]
            predicate_edges = [a for a in analysis['assignments'] if a.get('actual_role') == 'nominal_predicate' and
                               span_ok(a.get('span'), case['text'], predicate_surface, offset)]
            check(len(subject_edges) == len(predicate_edges) == 1, prefix + 'correlated_roles', safety=True)
            if len(subject_edges) != 1 or len(predicate_edges) != 1:
                continue
            se, pe = subject_edges[0], predicate_edges[0]
            check(se.get('required_case') == pe.get('required_case') == 'raf' and pe.get('inflected_case') == 'raf' and
                  (se.get('inflected_case') or se.get('local_case')) == expected['subject_actual_case'] and
                  pe.get('head_span') == se.get('span'), prefix + 'case_and_head', safety=True)
            refs = [r for r in analysis['references'] if r.get('span') == se['span']]
            check(len(refs) == 1 and refs[0].get('status') == 'RESOLVED' and
                  refs[0].get('bound_entity_id') == wanted['args'][0], prefix + 'resolved_identity', safety=True)
            agreements = [r for r in analysis['relations'] if r.get('kind') == 'predicate_agreement' and
                          r.get('head_span') == se['span'] and r.get('dependent_span') == pe['span'] and
                          r.get('head_reading_id') == se['reading_id'] and r.get('dependent_reading_id') == pe['reading_id']]
            check(len(agreements) == 1 and agreements[0].get('status') == 'confirmed' and
                  agreements[0].get('axes') == {'gender':'confirmed','number':'confirmed'},
                  prefix + 'agreement_edge', safety=True)
            if expected['context_profile_must_not_become_lexical_features'] and len(agreements) == len(refs) == 1:
                basis = agreements[0].get('subject_gender_basis', {})
                entity = next(e for e in case['context']['entities'] if e['id'] == wanted['args'][0])
                check(basis.get('kind') == 'explicit_named_person_semantic_profile' and
                      basis.get('entity_id') == entity['id'] and basis.get('context_sha256') == document['context']['sha256'] and
                      basis.get('reference_ids') == [refs[0]['reference_id']] and
                      set(basis.get('source_fields', [])) == {'entities.name','entities.kind','entities.gender','entities.number'} and
                      basis.get('lexical_profile_acquired') is False and
                      agreements[0].get('subject_profile') == {'person':3,'gender':entity['gender'],'number':entity['number']},
                      prefix + 'source_bound_semantic_profile', safety=True)
    if changed is not None:
        check(changed['document']['status'] == case['expected_changed_document_status'], 'changed_document_status')
        check(changed['answer']['status'] == case['expected_changed_answer_status'], 'changed_answer_status')
        check(len(changed['document']['claims']) == case['expected_changed_claim_count'], 'changed_claim_count', safety=True)
        check(all(v.get('valid') is False for v in changed['old_certificate_verification'].values()),
              'old_certificate_invalidated', safety=True)
        check(all(v.get('valid') is True for v in changed['fresh_verification'].values()), 'changed_source_replay', safety=True)
    false_accept = (not expected['positive_agreement_required'] and (bool(document['claims']) or
                    answer['status'] in ('SUPPORTED','REFUTED','CONFLICT'))) or bool(integrity)
    return {'id':case['id'], 'group':case['group'], 'passed':not failures, 'failures':failures,
            'false_accept':false_accept, 'observed':{'document_status':document['status'], 'answer_status':answer['status'],
            'claim_count':len(document['claims']), 'viable_analyses':sum(a['licensed_syntax'] and a['references_complete'] and
            not a['rejected_candidate'] for a in analyses), 'context_sha256':document['context']['sha256']}}


def execute_case(case, api):
    learn, read, ask, verify, verify_answer = api
    payload = (FOLDER / safe_path(case['source'])).read_bytes()
    model = learn(payload, source_id='context_name_review')
    context = case['context']
    document = read(case['text'], lexical_model=model, context=context)
    answer = ask(case['text'], case['question'], lexical_model=model, context=context)
    verification = {'document':verify(document, lexical_model=model, context=context),
                    'answer':verify_answer(answer, lexical_model=model, context=context)}
    changed = None
    if 'changed_context' in case:
        alternate = case['changed_context']
        d = read(case['text'], lexical_model=model, context=alternate)
        a = ask(case['text'], case['question'], lexical_model=model, context=alternate)
        changed = {'document':d, 'answer':a,
                   'old_certificate_verification':{'document':verify(document, lexical_model=model, context=alternate),
                       'answer':verify_answer(answer, lexical_model=model, context=alternate)},
                   'fresh_verification':{'document':verify(d, lexical_model=model, context=alternate),
                       'answer':verify_answer(a, lexical_model=model, context=alternate)}}
    scored = score(case, document, answer, verification, changed)
    return {'case_id':case['id'], 'source_sha256':digest(payload), 'context':context,
            'document':document, 'answer':answer, 'verification':verification, 'changed':changed, 'score':scored}

def archive_inputs(output, freeze):
    runner = Path(__file__).read_bytes()
    runner_path = output.with_suffix('.runner.py')
    with runner_path.open('xb') as saved:
        saved.write(runner)
    bundle_path = output.with_suffix('.inputs.tar.gz')
    require(not bundle_path.exists(), 'Refuse to overwrite input archive')
    names = [r['path'] for r in freeze['files']] + ['material_freeze_v1.json', 'run_review.py']
    with tarfile.open(bundle_path, 'x:gz') as bundle:
        for name in sorted(names):
            payload = (FOLDER / name).read_bytes()
            member = tarfile.TarInfo(name)
            member.size, member.mtime, member.mode = len(payload), 0, 0o644
            bundle.addfile(member, io.BytesIO(payload))
    return {'runner_path': str(runner_path), 'runner_sha256': digest(runner),
            'inputs_archive_path': str(bundle_path), 'inputs_archive_sha256': digest(bundle_path.read_bytes())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--runtime-freeze', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    runtime_root, manifest_path, output = args.runtime_root.resolve(), args.runtime_freeze.resolve(), args.output.resolve()
    require(not output.exists() and not output.with_suffix('.raw.jsonl').exists(), 'Refuse to overwrite results')
    output.parent.mkdir(parents=True, exist_ok=True)
    require(not any(n == 'nabt' or n.startswith('nabt.') for n in sys.modules), 'Runtime imported before selection')
    before = snapshot(manifest_path, runtime_root)
    freeze, material = load_material()
    archived = archive_inputs(output, freeze)
    sys.path.insert(0, str(runtime_root / 'src'))
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.discourse import read_discourse, ask_discourse, verify_discourse, verify_discourse_answer
    api = (learn_qac_lexicon, read_discourse, ask_discourse, verify_discourse, verify_discourse_answer)
    check_origins(runtime_root)
    rows, written = [], []
    journal = output.with_suffix('.raw.jsonl')
    with journal.open('xb') as stream:
        for case in material['cases']:
            try:
                raw = execute_case(case, api)
                scored = raw['score']
            except Exception as error:
                scored = {'id':case['id'], 'group':case['group'], 'passed':False, 'false_accept':False,
                          'failures':['execution_error'], 'error':{'type':type(error).__name__,
                          'message':str(error), 'traceback':traceback.format_exc()}}
                raw = {'case_id':case['id'], 'score':scored}
            payload = canonical(raw) + b'\n'
            stream.write(payload)
            stream.flush()
            written.append({'id':case['id'], 'bytes':len(payload), 'sha256':digest(payload)})
            rows.append(scored)
    payload = journal.read_bytes()
    lines = payload.splitlines(keepends=True)
    require(len(lines) == len(written) == len(rows) == 16, 'Incomplete raw journal')
    for line, receipt, case, scored in zip(lines, written, material['cases'], rows):
        raw = json.loads(line)
        require(line.endswith(b'\n') and canonical(raw) + b'\n' == line, 'Noncanonical raw journal')
        require(len(line) == receipt['bytes'] and digest(line) == receipt['sha256'], 'Raw write/read mismatch')
        require(raw['case_id'] == case['id'] == receipt['id'] and raw['score'] == scored, 'Raw case/score mismatch')
        if 'error' not in scored:
            require(score(case, raw['document'], raw['answer'], raw['verification'], raw['changed']) == scored,
                    'Stored report rescore mismatch')
    after = snapshot(manifest_path, runtime_root)
    require(after == before, 'Runtime changed during measurement')
    load_material()
    require(digest(Path(__file__).read_bytes()) == archived['runner_sha256'], 'Runner changed during measurement')
    result = {'schema':'nabt.context-name-review.result.v1', 'utc':datetime.now(timezone.utc).isoformat(),
              'classification':material['classification'], 'material_freeze_sha256':MATERIAL_PIN,
              'runtime':before, 'runtime_after':after, 'module_origins':check_origins(runtime_root),
              **archived, 'cases':rows, 'total':len(rows), 'passed':sum(r['passed'] for r in rows),
              'false_accepts':sum(r['false_accept'] for r in rows), 'errors':sum('error' in r for r in rows),
              'raw':{'path':str(journal), 'sha256':digest(payload), 'bytes':len(payload), 'records':len(lines),
                     'verified_after_close':True, 'rescored_from_raw':True, 'write_receipts':written},
              'strict_pass':all(r['passed'] for r in rows)}
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps({k:result[k] for k in ('total','passed','false_accepts','errors','strict_pass')}, sort_keys=True))
    return 0 if result['strict_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
