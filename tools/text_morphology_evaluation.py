#!/usr/bin/env python3
"""Check the frozen independent properties of NABT's raw-text morphology reader.

This is a source/span and semantic-property adapter over authored cases. It is
not another Arabic parser. The input/gold bytes were fixed before the reviewer
opened the new implementation. Positive and boundary results are separate;
blanket deferral cannot satisfy positive acquisition cases.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

VERSION = 'nabt.text-morphology.independent-evaluator.v1'
MATERIAL_SHA256 = '082f66e559f68f0aeaa3a32f93bf179668e3286b0b78e1a18e4eae2fae427a55'
PROTOCOL_SHA256 = 'e03fc34e3a3ac5966af5ee8d733c33e068080e3ac578cba61d4ae88b36510a85'
POSITIVE_CATEGORIES = {'positive_surface', 'positive_transfer', 'positive_context_candidate', 'lexical_witness'}


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_material():
    folder = ROOT / 'evidence/text_morphology'
    raw = (folder / 'independent_cases_v1.json').read_bytes()
    require(sha256(raw).hexdigest() == MATERIAL_SHA256, 'Frozen case bytes changed')
    require(sha256((folder / 'independent_protocol.md').read_bytes()).hexdigest() == PROTOCOL_SHA256,
            'Frozen protocol bytes changed')
    data = json.loads(raw)
    require(len(data['cases']) == len({c['id'] for c in data['cases']}) == 40, 'Case inventory changed')
    return data


def runtime_snapshot():
    paths = {ROOT / 'pyproject.toml', Path(__file__).resolve()}
    paths.update(p for p in (ROOT / 'src').rglob('*') if p.is_file()
                 and p.suffix in {'.py', '.json', '.txt'} and '__pycache__' not in p.parts
                 and not any(part.endswith(('.egg-info', '.dist-info')) for part in p.parts))
    rows = [{'path': str(p.relative_to(ROOT)), 'bytes': len(p.read_bytes()),
             'sha256': sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]
    return {'snapshot_sha256': sha256(wire(rows)).hexdigest(), 'files': rows}


def preserve_snapshot(snapshot, output):
    archive_path = output.with_suffix('.code.tar.gz')
    require(not archive_path.exists(), 'Refusing to overwrite a measured code archive')
    with tarfile.open(archive_path, 'w:gz') as bundle:
        for row in snapshot['files']:
            payload = (ROOT / row['path']).read_bytes()
            require(len(payload) == row['bytes'] and sha256(payload).hexdigest() == row['sha256'],
                    'Code changed during snapshot capture')
            member = tarfile.TarInfo(row['path'])
            member.size = len(payload)
            member.mode = 0o644
            member.mtime = 0
            bundle.addfile(member, io.BytesIO(payload))
    return {'filename': archive_path.name, 'sha256': sha256(archive_path.read_bytes()).hexdigest()}


def occurrences(report, surface=None):
    values = report['occurrences']
    return values if surface is None else [o for o in values if o['surface'] == surface]


def axis(o, name):
    return o['axes'][name]


def licensed(o, name, value):
    a = axis(o, name)
    return a['status'] == 'LICENSED' and a['candidates'] == [value]


def compact_occurrences(values):
    return [{'surface': o['surface'], 'occurrence_id': o['occurrence_id'],
             'status': o['status'],
             'axes': {name: {'status': a['status'], 'candidates': a['candidates']}
                      for name, a in o['axes'].items()},
             'lexical_readings': [r['lexical_link'] for r in o['readings']],
             'blockers': [b for r in o['readings'] for b in r['blockers']]}
            for o in values]


def independent_structure_checks(report, inputs):
    """Validate byte arithmetic, linkage and authority without calling the parser."""
    raw = inputs['text'].encode('utf-8')
    digest = sha256(raw).hexdigest()
    require(report['raw_text'] == inputs['text'] and report['source_id'] == inputs['source_id']
            and report['scope'] == inputs['scope'] and report['source_sha256'] == digest,
            'Source identity or bytes differ')
    sources = {inputs['source_id']: raw}
    expected_lexical = inputs.get('lexical_text')
    lexical = report['lexical_source']
    if expected_lexical is None:
        require(lexical is None, 'Unexpected lexical premises')
    else:
        require(lexical is not None and lexical['raw_text'] == expected_lexical
                and lexical['source_id'] == 'lexical' and lexical['scope'] == inputs['scope']
                and lexical['sha256'] == sha256(expected_lexical.encode('utf-8')).hexdigest(),
                'Lexical source identity differs')
        sources['lexical'] = expected_lexical.encode('utf-8')

    def check_span(s, surface=None, source_id=None):
        require(type(s['start']) is int and type(s['end']) is int,
                'Offsets must be actual integers')
        src = sources.get(s['source_id'])
        require(src is not None and (source_id is None or source_id == s['source_id']), 'Unknown span source')
        require(0 <= s['start'] < s['end'] <= len(src), 'Invalid span bounds')
        piece = src[s['start']:s['end']]
        decoded = piece.decode('utf-8', 'strict')
        require(s['source_sha256'] == sha256(src).hexdigest()
                and s['span_sha256'] == sha256(piece).hexdigest(), 'Invalid span digest')
        require(surface is None or decoded == surface, 'Span does not support its surface text')

    cursor = 0
    written = []
    for part in report['partition']:
        check_span(part['span'], part['surface'], inputs['source_id'])
        require(part['span']['start'] == cursor, 'Partition gap or overlap')
        cursor = part['span']['end']
        if part['kind'] == 'written_run':
            written.append((part['span']['start'], part['span']['end']))
    require(cursor == len(raw), 'Source suffix is missing')
    observed = [(o['span']['start'], o['span']['end']) for o in occurrences(report)]
    require(observed == written, 'Written occurrence inventory differs from partition')
    require(len({o['occurrence_id'] for o in occurrences(report)}) == len(observed), 'Distinct occurrences merged')
    declared_rules = {r['id'] for r in report['rule_evidence']} | {
        r['id'] for r in report['morphology_rule_evidence']}
    reading_ids = set()
    for o in occurrences(report):
        check_span(o['span'], o['surface'], inputs['source_id'])
        require(o['actual_role'] is None and o['actual_case'] is None, 'Occurrence acquired a role/case')
        require(bool(o['readings']), 'Occurrence has no reading or explicit residual')
        for observation in o['observations']:
            check_span(observation['span'], observation['surface'], inputs['source_id'])
            require(o['span']['start'] <= observation['span']['start'] < observation['span']['end'] <= o['span']['end'],
                    'Observation escaped its occurrence')
        for r in o['readings']:
            require(r['reading_id'] not in reading_ids, 'Reading identity reused')
            reading_ids.add(r['reading_id'])
            require(r['identity']['occurrence_id'] == o['occurrence_id']
                    and r['identity']['source_sha256'] == digest
                    and r['identity']['scope'] == inputs['scope'], 'Reading borrowed an identity')
            require(r['actual_role'] is None and r['actual_case'] is None, 'Reading acquired a role/case')
            for p in r['linked_properties']:
                check_span(p['span'], p['text'], 'lexical')
                require(p['property'] not in {'al', 'idhafa'}, 'Occurrence-local property leaked from lexical source')
            link = r['lexical_link']
            if link is not None:
                require(link['match'] == 'EXACT_UTF8_SURFACE', 'Unexpected lexical linkage policy')
                check_span(link['lexeme_span'], o['surface'], 'lexical')
                require(link['source_id'] == 'lexical' and link['source_sha256'] == lexical['sha256'],
                        'Lexical link source differs')
            for receipt in r['receipts']:
                require(receipt['identity']['reading_id'] == r['reading_id']
                        and receipt['identity']['occurrence_id'] == o['occurrence_id'],
                        'Receipt borrowed a reading/occurrence identity')
                require(receipt['rule_id'] in declared_rules, 'Receipt cites an absent rule')
                require(bool(receipt['supports']), 'Receipt has no source support')
                for support in receipt['supports']:
                    check_span(support['span'], support.get('surface', support.get('text')))
            genitive = r['axes']['diptote']['genitive']
            require(genitive['applied_to_occurrence'] is False
                    and genitive['context_properties_transferred'] is False,
                    'Conditional sign was applied without a new context witness')
    by_id = {o['occurrence_id']: o for o in occurrences(report)}
    for attachment in report['attachments']:
        marker, target = by_id[attachment['marker_occurrence_id']], by_id[attachment['target_occurrence_id']]
        require(attachment['marker_span'] == marker['span'] and attachment['target_span'] == target['span'],
                'Attachment is not bound to its occurrences')
        require(attachment['status'] == 'CANDIDATE' and attachment['kind_constraint_activated'] is False,
                'Candidate adjacency acquired grammatical authority')
        require(attachment['actual_case'] is None and attachment['actual_role'] is None,
                'Candidate adjacency acquired actual case/role')
    require(report['facts'] == [] and report['world_truth'] == 'NOT_ESTABLISHED'
            and report['semantic_projection'] == 'NONE', 'Morphology emitted world facts')
    require(report['recognition_basis']['content_word_answer_entries_used'] == 0,
            'Reader admits using content-word answers')
    return True


def property_check(expected, report=None, error=None):
    name = expected['property']
    if error is not None:
        ok = name == 'no_licensed_kind_or_invalid_input' and error.get('status') == 'REJECT' \
             and error.get('code') in {'CONFLICTING_MARKS', 'INVALID_WORD_MARK', 'INVALID_TEXT_MORPHOLOGY_SOURCE'}
        return {'property': name, 'passed': ok, 'observed': error}
    selected = occurrences(report, expected.get('surface'))
    present = bool(selected)
    value = expected.get('value')
    if name in {'licensed_kind', 'all_occurrences_licensed_kind'}:
        passed = present and all(licensed(o, 'kind', value) for o in selected)
    elif name == 'licensed_axis':
        passed = present and all(licensed(o, expected['axis'], value) for o in selected)
    elif name == 'not_licensed_axis':
        passed = present and all(not licensed(o, expected['axis'], value) for o in selected)
    elif name == 'not_unique_kind':
        passed = present and all(axis(o, 'kind')['status'] != 'LICENSED'
                                 and len(axis(o, 'kind')['candidates']) > 1 for o in selected)
    elif name == 'no_actual_role_or_case':
        passed = present and all(o['actual_role'] is None and o['actual_case'] is None
                                 and all(r['actual_role'] is None and r['actual_case'] is None for r in o['readings'])
                                 for o in selected)
    elif name == 'verb_context_candidate':
        ids = {o['occurrence_id'] for o in selected}
        edges = [a for a in report['attachments'] if a['target_occurrence_id'] in ids]
        passed = present and any(a['status'] == 'CANDIDATE' and a['expected_kind'] == 'verb'
                                 and a['imperfect_onset_observed'] is True
                                 and a['kind_constraint_activated'] is False for a in edges)
    elif name == 'no_context_edges':
        passed = not report['attachments']
    elif name == 'no_context_for':
        ids = {o['occurrence_id'] for o in selected}
        passed = present and not any(a['target_occurrence_id'] in ids for a in report['attachments'])
    elif name == 'no_licensed_use':
        passed = not any(axis(o, 'kind')['status'] == 'LICENSED' for o in occurrences(report))
    elif name == 'separate_occurrences':
        passed = len(selected) == expected['count'] and len({o['occurrence_id'] for o in selected}) == expected['count'] \
            and len({(o['span']['start'],o['span']['end']) for o in selected}) == expected['count']
    elif name == 'retained_lexical_alternatives':
        passed = present and all(
            len([r for r in o['readings'] if r['lexical_link'] is not None]) == expected['reading_count']
            and {r['axes'][expected['axis']]['candidates'][0] for r in o['readings']
                 if r['lexical_link'] is not None and r['axes'][expected['axis']]['status'] == 'LICENSED'}
                == set(expected['values']) for o in selected)
    elif name == 'no_unique_aggregate':
        passed = present and all(axis(o, expected['axis'])['status'] != 'LICENSED'
                                 and len(axis(o, expected['axis'])['candidates']) > 1 for o in selected)
    elif name in {'no_licensed_article', 'no_licensed_idafa'}:
        property_name = 'al' if name == 'no_licensed_article' else 'idhafa'
        passed = present and all(
            all(not any(p['property'] == property_name for p in r['linked_properties'])
                and r['axes']['diptote']['genitive']['context_properties_transferred'] is False
                and r['axes']['diptote']['genitive']['applied_to_occurrence'] is False
                for r in o['readings']) for o in selected)
    elif name == 'no_lexical_match':
        passed = present and all(all(r['lexical_link'] is None for r in o['readings']) for o in selected)
    elif name == 'not_clean_lexical_reading':
        passed = present and all(all(r['axes']['kind']['status'] != 'LICENSED'
                    and any(b['code'] == 'LEXICAL_SOURCE_CONFLICT' for b in r['blockers'])
                    for r in o['readings']) for o in selected)
    elif name == 'no_licensed_kind_or_invalid_input':
        passed = present and all(axis(o, 'kind')['status'] != 'LICENSED'
                and any(b['code'] == 'CONFLICTING_MARKS' and b['status'] == 'REJECT' for b in o['blockers'])
                for o in selected)
    else:
        raise ValueError('Unknown frozen property: ' + name)
    observed = compact_occurrences(selected)
    if name in {'verb_context_candidate','no_context_edges','no_context_for'}:
        observed = {'occurrences': observed, 'attachments': report['attachments']}
    return {'property': name, 'expected': expected, 'passed': bool(passed), 'observed': observed}


def run_case(case):
    from nabt.errors import NabtError
    from nabt.text_morphology import read_text_morphology, verify_text_morphology
    inputs = case['input']
    try:
        report = read_text_morphology(**inputs)
    except NabtError as error:
        checks = [property_check(p, error=error.as_dict()) for p in case['expected']]
        return {'id': case['id'], 'category': case['category'], 'passed': all(c['passed'] for c in checks),
                'checks': checks, 'error': error.as_dict()}
    checks = [property_check(p, report=report) for p in case['expected']]
    try:
        independent_structure_checks(report, inputs)
        checks.append({'property': 'independent_source_structure', 'passed': True})
    except (KeyError, TypeError, ValueError, UnicodeError) as error:
        checks.append({'property': 'independent_source_structure', 'passed': False, 'error': str(error)})
    replay = verify_text_morphology(report, text=inputs['text'], source_id=inputs['source_id'],
                                    scope=inputs['scope'], lexical_text=inputs.get('lexical_text'),
                                    lexical_source_id='lexical')
    checks.append({'property': 'source_bound_replay', 'passed': replay['valid'], 'observed': replay})
    return {'id': case['id'], 'category': case['category'], 'passed': all(c['passed'] for c in checks),
            'report_status': report['status'], 'report_sha256': sha256(wire(report)).hexdigest(), 'checks': checks}


def evaluate():
    material = load_material()
    snapshot = runtime_snapshot()
    results = [run_case(c) for c in material['cases']]
    require(runtime_snapshot() == snapshot, 'Runtime changed while evaluation was running')
    def score(rows):
        return {'passed': sum(r['passed'] for r in rows), 'total': len(rows)}
    positive = [r for r in results if r['category'] in POSITIVE_CATEGORIES]
    boundaries = [r for r in results if r['category'] not in POSITIVE_CATEGORIES]
    return {'schema': VERSION, 'evaluated_at_utc': datetime.now(timezone.utc).isoformat(),
            'material_sha256': MATERIAL_SHA256, 'code_snapshot': snapshot,
            'scope': material['authority_limit'], 'raw_score': score(results),
            'positive_score': score(positive), 'boundary_score': score(boundaries),
            'passed': all(r['passed'] for r in results), 'results': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--capture-code', action='store_true')
    args = parser.parse_args()
    try:
        require(not args.output.exists(), 'Refusing to overwrite a measured evaluation result')
        report = evaluate()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.capture_code:
            report['code_archive'] = preserve_snapshot(report['code_snapshot'], args.output)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({k:report[k] for k in ('schema','raw_score','positive_score','boundary_score','passed')},indent=2))
        return 0 if report['passed'] else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'passed': False, 'evaluation_error': str(error)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
