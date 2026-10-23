#!/usr/bin/env python3
"""Frozen authored source-template regression; no production decisions used as gold."""
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
MATERIAL_PIN = '69b3c68be10770ecc6288bdacec64591474e3b8685d53ca2971f568925198c45'
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
    '5d4bf3ec6331dab12ebc735f57203cf6bdbc86a563eae0311a66316eb8b820b1': {
        'snapshot_sha256': '1e9d906428ec3824c4ecbff8ef8fb3adc88d6cb6c9dbfa1819c53655b3206c7c',
        'archive_sha256': '9d5ec76ec904c3696d0e5a76e46fe435e9189322fe0578133c6816707b2fd2c5',
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
    freeze_raw = (FOLDER / 'material_freeze_v1.json').read_bytes()
    require(digest(freeze_raw) == MATERIAL_PIN, 'Material freeze changed')
    freeze = json.loads(freeze_raw)
    for item in freeze['files']:
        raw = (FOLDER / safe_path(item['path'])).read_bytes()
        require(len(raw) == item['bytes'] and digest(raw) == item['sha256'], 'Frozen material changed: ' + item['path'])
    material = json.loads((FOLDER / 'material_v1.json').read_bytes())
    require(len(material['cases']) == freeze['case_count'] == 12, 'Case inventory changed')
    require(len({c['id'] for c in material['cases']}) == 12, 'Duplicate case')
    for source in material['sources']:
        raw = (FOLDER / safe_path(source['path'])).read_bytes()
        require(len(raw) == source['bytes'] and digest(raw) == source['sha256'], 'Source changed')
    context = json.loads((FOLDER / safe_path(material['context'])).read_bytes())
    return freeze, material, context


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


def score(case, document, answer, verification):
    expected = case['expected']
    failures = []
    def check(value, label):
        if not value:
            failures.append(label)
    check(document['status'] == expected['document_status'], 'document_status')
    check(answer['status'] == expected['answer_status'], 'answer_status')
    check(len(document['claims']) == expected['claim_count'], 'claim_count')
    targets = [o for o in document['occurrences'] if o['surface'] == case['target_surface']]
    check(len(targets) == 1, 'target_occurrence')
    carriers = [r for o in targets for r in o['readings'] if r.get('nominal_case_carrier') is not None]
    check(bool(carriers) == expected['carrier_licensed'], 'carrier_licensed')
    if expected['carrier_licensed']:
        check(all(r.get('construction') == 'inflected' and r.get('class_candidates') == [0] and
                  r['nominal_case_carrier'].get('full_form_supports') and
                  r['nominal_case_carrier'].get('base_paradigm_supports') for r in carriers), 'qualified_carrier_supports')
        check(any({k: c.get(k) for k in CLAIM_FIELDS} == expected['claim'] for c in document['claims']), 'exact_claim')
        viable = [a for c in document['clauses'] for a in c['analyses'] if a['licensed_syntax'] and
                  a['references_complete'] and not a['rejected_candidate']]
        check(any(all(any(x.get('actual_role') == role and (x.get('inflected_case') or x.get('local_case')) == value
                              for x in a['assignments']) for role, value in expected['activated_roles'].items())
                  for a in viable), 'roles_in_same_analysis')
    check(all(v.get('valid') is True and v.get('status') == 'VERIFIED' for v in verification.values()), 'source_replay')
    false_accept = not expected['carrier_licensed'] and (bool(carriers) or bool(document['claims']) or
                                                       answer['status'] in ('SUPPORTED', 'CONFLICT'))
    return {'id': case['id'], 'passed': not failures, 'failures': failures, 'false_accept': false_accept,
            'observed': {'document_status': document['status'], 'answer_status': answer['status'],
                         'claim_count': len(document['claims']), 'carrier_count': len(carriers)}}


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
    freeze, material, context = load_material()
    archived = archive_inputs(output, freeze)
    sys.path.insert(0, str(runtime_root / 'src'))
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.discourse import read_discourse, ask_discourse, verify_discourse, verify_discourse_answer
    check_origins(runtime_root)
    rows, written = [], []
    journal = output.with_suffix('.raw.jsonl')
    with journal.open('xb') as stream:
        for case in material['cases']:
            source = (FOLDER / safe_path(case['source'])).read_bytes()
            raw = {'case_id': case['id'], 'source_file': case['source'], 'source_sha256': digest(source)}
            try:
                model = learn_qac_lexicon(source, source_id='alif_review')
                document = read_discourse(case['text'], lexical_model=model, context=context)
                answer = ask_discourse(case['text'], case['question'], lexical_model=model, context=context)
                verification = {'document': verify_discourse(document, lexical_model=model, context=context),
                                'answer': verify_discourse_answer(answer, lexical_model=model, context=context)}
                scored = score(case, document, answer, verification)
                raw.update(document=document, answer=answer, verification=verification, score=scored)
            except Exception as error:
                scored = {'id': case['id'], 'passed': False, 'false_accept': False, 'failures': ['execution_error'],
                          'error': {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}}
                raw.update(score=scored)
            payload = canonical(raw) + b'\n'
            stream.write(payload)
            stream.flush()
            written.append({'id': case['id'], 'bytes': len(payload), 'sha256': digest(payload)})
            rows.append(scored)
    payload = journal.read_bytes()
    lines = payload.splitlines(keepends=True)
    require(len(lines) == len(written) == len(rows) == 12, 'Incomplete raw journal')
    for line, receipt, case, scored in zip(lines, written, material['cases'], rows):
        raw = json.loads(line)
        require(line.endswith(b'\n') and canonical(raw) + b'\n' == line, 'Noncanonical raw journal')
        require(len(line) == receipt['bytes'] and digest(line) == receipt['sha256'], 'Raw write/read mismatch')
        require(raw['case_id'] == case['id'] == receipt['id'] and raw['score'] == scored, 'Raw case/score mismatch')
        if 'error' not in scored:
            require(raw['verification']['document'].get('report_id') == raw['document']['report_id'], 'Document replay identity mismatch')
            require(raw['verification']['answer'].get('answer_id') == raw['answer']['answer_id'], 'Answer replay identity mismatch')
    after = snapshot(manifest_path, runtime_root)
    require(after == before, 'Runtime changed during measurement')
    load_material()
    require(digest(Path(__file__).read_bytes()) == archived['runner_sha256'], 'Runner changed during measurement')
    result = {'schema': 'nabt.alif-template-review.result.v1', 'utc': datetime.now(timezone.utc).isoformat(),
              'classification': material['classification'], 'material_freeze_sha256': MATERIAL_PIN,
              'runtime': before, 'runtime_after': after, 'module_origins': check_origins(runtime_root),
              **archived, 'cases': rows, 'total': len(rows), 'passed': sum(r['passed'] for r in rows),
              'false_accepts': sum(r['false_accept'] for r in rows), 'errors': sum('error' in r for r in rows),
              'raw': {'path': str(journal), 'sha256': digest(payload), 'bytes': len(payload),
                      'records': len(lines), 'verified_after_close': True, 'write_receipts': written},
              'strict_pass': all(r['passed'] for r in rows)}
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps({k: result[k] for k in ('total', 'passed', 'false_accepts', 'errors', 'strict_pass')}, sort_keys=True))
    return 0 if result['strict_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
