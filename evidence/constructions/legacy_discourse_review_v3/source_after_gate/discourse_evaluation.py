#!/usr/bin/env python3
"""Evaluate the pre-implementation, source-informed discourse material.

The learner only receives the raw QAC source/exclusions. Gold, questions, and
semantic expectations are confined to this scorer. No runtime parser helper is
used to judge an output. A fresh process isolates an approved source snapshot.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import sys
import tarfile
import time
import traceback
import unicodedata
import zlib

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'evidence/discourse'
VERSION = 'nabt.discourse.independent-evaluation.v1'
GOLD_FREEZE_SHA256 = '3f65aa1c7fca3f6d5d4685654ebecbfc4c260c9920c562d8c5cad3dd41dccfe5'
QAC_SHA256 = 'a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46'
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
    '96ffa98008bf1b6a6d1f5ab6b79a330fe4b8a9329887d9ac3f8ff9d31eb12e1e': {
        'snapshot_sha256': '87c7d5dc6c4aa5f46d42f7cd27a1595e2a2844af50da42a45a0f3b3bc09812b9',
        'archive_sha256': 'edaff6bb63863e10734993bbaf5101160dab3308b22e763ba188d89fa28e3575',
        'file_count': 74,
    },
    '4e2e6701f989f6e631948dbfb958e07f384ab1294d4c87faf915a6a42853c64b': {
        'snapshot_sha256': '688cdaa08abbec8137b9b0456042f5af17e0986b708e4bfe1629dd2a74e48545',
        'archive_sha256': '15beae68fafde0467f22323e75bf21947ea20e7a320fa3ede5fc31eebc66f7ea',
        'file_count': 67,
    },
    '22350accf750741680f351b34cf97f95bf146b7389765cd74d937a8aa4291ae4': {
        'snapshot_sha256': 'e82b9d72b45d8cbcd667708140b9f5b91a967822002a54a76bc87b097912a2f9',
        'archive_sha256': '0085bb7482ef89d20f0f8667ca015f0cf198ab283d9e439ecc814b9167b13775',
        'file_count': 67,
    },
    'c74b029c986fa3e1bb6a6ab3c5cbd423f77c902733626105ec95f5e366b71018': {
        'snapshot_sha256': '6b78f1c8e36058d350d1e572bf20737c3517d38a8498fc4a50ece6bf6725fd30',
        'archive_sha256': '4fbcadee8997087223cbf8ffc365dd7a1b6cac4eb0990350e8925098ec557b51',
        'file_count': 67,
    },
    'f1e035f7d20395abb82c2e87ac42f374630bef6bab71a22490873c7a08e8e519': {
        'snapshot_sha256': '2d79ea2227dda5169413eb314b9b65b5bc04fcacb447d00066ef56d3c7b69108',
        'archive_sha256': 'af7b88818f8d46a4d810927df39f1eb839c28dd7862f3919c3ac52f66abdbf8e',
        'file_count': 67,
    },
}
DOCUMENTED_BOUNDARY_RUNTIME = 'f1e035f7d20395abb82c2e87ac42f374630bef6bab71a22490873c7a08e8e519'
# These are observed coverage/representation misses, not waived safety checks.
# A new failed check even in a listed case must receive a new review.
DOCUMENTED_BOUNDARIES = {
    'DSC-P02': frozenset({'required_claim:0', 'question:0'}),
    'DSC-P03': frozenset({'required_claim:0', 'question:0'}),
    'DSC-P08': frozenset({'required_claim:0', 'reading:0', 'question:0'}),
    # V3's incomplete-prefix guard also blocks the positive pronoun claim/reference.
    # See independent_gate_before_p09.json; this does not waive any false acceptance.
    'DSC-P09': frozenset({'required_claim:0', 'reading:0', 'question:0'}),
    'DSC-P12': frozenset({'required_claim:0', 'question:0'}),
    'DSC-P13': frozenset({'required_claim:0', 'reading:0', 'question:0'}),
    'DSC-P14': frozenset({'required_claim:0', 'reading:0', 'question:0'}),
    'DSC-P15': frozenset({'required_claim:0', 'reading:0', 'question:0'}),
    'DSC-P17': frozenset({'required_claim:1', 'question:0'}),
    'DSC-P18': frozenset({'required_claim:0', 'required_claim:1', 'question:0', 'question:1'}),
    'DSC-P22': frozenset({'required_claim:0', 'question:0'}),
    'DSC-P23': frozenset({'required_claim:0', 'question:0'}),
    'DSC-P24': frozenset({'required_claim:0', 'question:0'}),
    'DSC-P25': frozenset({'required_claim:0', 'reading:0', 'question:0'}),
    'DSC-P26': frozenset({'required_claim:0'}),
    'DSC-P27': frozenset({'required_claim:0', 'reading:0', 'question:0'}),
    'DSC-P28': frozenset({'required_claim:1', 'reading:0', 'question:0'}),
    'DSC-P30': frozenset({'question:0'}),
    'DSC-T02': frozenset({'required_claim:0', 'question:0'}),
    'DSC-T04': frozenset({'required_claim:0', 'question:0'}),
    'DSC-B04': frozenset({'required_claim:1', 'reading:0'}),
    'DSC-B05': frozenset({'reading:0'}),
    'DSC-B14': frozenset({'force_preserved'}),
    'DSC-B15': frozenset({'force_preserved'}),
    'DSC-B16': frozenset({'force_preserved'}),
    'DSC-B19': frozenset({'question:0'}),
    'DSC-B24': frozenset({'required_claim:0'}),
    'DSC-B25': frozenset({'required_claim:0'}),
    'DSC-L03': frozenset({'reading:0'}),
}
# Versioned extension approved only after the same-adapter three-runtime review.
# Preserve the discourse-v4 policy above, including its narrower P26 check set.
# The construction reader retains an unresolved construction alternative for a
# context-only name; this loses P26's positive answer rather than proving it false.
# See evidence/constructions/legacy_discourse_review_v1/comparison.json.
CONSTRUCTION_BOUNDARY_RUNTIME = '5d4bf3ec6331dab12ebc735f57203cf6bdbc86a563eae0311a66316eb8b820b1'
CONSTRUCTION_BOUNDARIES = {
    **DOCUMENTED_BOUNDARIES,
    'DSC-P26': DOCUMENTED_BOUNDARIES['DSC-P26'] | frozenset({'question:0'}),
}
# Separate v4 coverage debt, approved only after the paired strict run and
# source diagnosis in constructions/legacy_discourse_review_v3. V3's larger
# regression remains unapproved; no historical policy is changed here.
CONSTRUCTION_V4_BOUNDARY_RUNTIME = '42476d67e30e7e86506c3e878552966ce9dc784ae1e5d98bec3af50e6f0a1aa5'
CONSTRUCTION_V4_BOUNDARIES = {
    **CONSTRUCTION_BOUNDARIES,
    'DSC-P16': frozenset({'question:0'}),
    'DSC-P26': CONSTRUCTION_BOUNDARIES['DSC-P26'] | frozenset({'reading:0'}),
}
NON_RUNTIME = frozenset({'src/nabt/data/source_evidence/README.md',
                         'src/nabt/data/source_evidence/LICENSE-DATA.md',
                         'src/nabt/data/source_evidence/.gitattributes'})
EXPECTED_KEYS = frozenset('''required_claims questions required_readings forbidden_claims
no_grounded_claims force restriction_must_be_preserved no_material_implication
forbid_person_promotion_from_final_t forbid_inflected_case_without_complete_witness
forbid_predicate_from_root semantic_invariance replay invalid_input named_diagnostic_required
no_traceback'''.split())
READING_KEYS = frozenset('''surface span occurrence_index kind role inflected_case local_case
reference person gender number root lemma nun_kinds distinct_nun_positions deleted_nun_span'''.split())
CLAIM_FIELDS = ('predicate', 'predicate_kind', 'voice', 'args', 'positive', 'tense', 'time', 'place', 'restriction')
CASE_VALUES = ('nasb', 'raf', 'jarr', 'jazm')
ROLE_CASE = {
    'nominal_subject': 'raf', 'nominal_predicate': 'raf',
    'active_subject': 'raf', 'passive_subject': 'raf',
    'direct_object': 'nasb', 'inna_subject': 'nasb', 'inna_predicate': 'raf',
    'kana_subject': 'raf', 'kana_predicate': 'nasb',
    'preposition_object': 'jarr', 'idafa_complement': 'jarr',
    'time_adverb': 'nasb', 'place_adverb': 'nasb',
    'imperfect_indicative': 'raf', 'imperfect_subjunctive': 'nasb', 'imperfect_jussive': 'jazm',
}
ROLE_ALIASES = {'predicate': 'nominal_predicate', 'verb_subject': 'active_subject',
                'verb_object': 'direct_object', 'laysa_predicate': 'kana_predicate'}
REFERENCE_BASES = {
    'speaker': 'speaker', 'addressee': 'addressee', 'context_name': 'named',
    'explicit_deixis': 'deictic', 'prior_compatible_closed_scope': 'antecedent',
    'entity_identity_with_multiple_mentions': 'antecedent', 'open_candidate_scope': 'antecedent',
    'relative_subject_return': 'relative_return', 'licensed_attached_object': 'antecedent',
}
# These are exact representation correspondences for the three gold time labels,
# not a general normalization of predicates, roots, context names, or raw text.
TIME_LABELS = {'اليوم': 'اليوم', 'يَوْم': 'اليوم', 'الْيَوْم': 'اليوم',
               'أمس': 'أمس', 'أَمْس': 'أمس', 'غدا': 'غدا', 'غَد': 'غدا'}
TIME_QUALIFIED_LABELS = {('يَوْم', 'اليوم', True): 'اليوم',
                        ('أَمْس', 'أمس', False): 'أمس',
                        ('غَد', 'غدا', False): 'غدا'}
PERSON_LABELS = {1: 'first', 2: 'second', 3: 'third',
                 'speaker': 'first', 'addressee': 'second', 'third': 'third'}


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return sha256(wire(value)).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def raw_record_identity(value):
    """Identify a journal row without interpreting any linguistic answer."""
    require(type(value) is dict, 'Raw journal record is not an object')
    if 'model_profile' in value:
        require(type(value['model_profile']) is str and 'id' not in value,
                'Raw journal profile identity is invalid')
        return {'kind': 'profile', 'profile': value['model_profile']}
    require(type(value.get('id')) is str, 'Raw journal case identity is invalid')
    if 'variant' in value:
        require(type(value['variant']) is str, 'Raw journal variant identity is invalid')
        return {'kind': 'variant', 'id': value['id'], 'variant': value['variant']}
    return {'kind': 'case', 'id': value['id']}


def verify_raw_journal(path, captured, inventory, scores):
    """Reopen the closed gzip and compare every recorded byte and row.

    A compressed-file digest alone also hashes a truncated stream. Capture
    receipts are made at log time, then checked against complete decompression,
    scheduled case/variant/profile identities and the separately held scores.
    This must succeed before a final measurement report may be published.
    """
    checksum, total_bytes = sha256(), 0
    observed = []
    by_id = {row['id']: row for row in scores}
    require(len(by_id) == len(scores), 'Raw journal scores repeat a case')
    try:
        with gzip.open(path, 'rb') as stream:
            for expected in captured['records']:
                payload = stream.readline(expected['bytes'] + 1)
                require(len(payload) == expected['bytes'] and payload.endswith(b'\n')
                        and sha256(payload).hexdigest() == expected['sha256'],
                        'Raw journal record bytes differ from log-time capture')
                value = json.loads(payload.decode('utf-8', 'strict'))
                identity = raw_record_identity(value)
                require(identity == expected['identity'], 'Raw journal record identity changed')
                observed.append(identity)
                checksum.update(payload)
                total_bytes += len(payload)
                if identity['kind'] == 'case':
                    require(identity['id'] in by_id, 'Raw journal case has no result')
                    score = {k: v for k, v in by_id[identity['id']].items() if k != 'seconds'}
                    require(value.get('score') == score, 'Raw journal score differs from result')
                    if 'report' in value:
                        require(type(value.get('questions')) is list and len(value['questions'])
                                == inventory['question_counts'][identity['id']],
                                'Raw journal question inventory differs')
            # Reading past the last captured newline verifies the gzip trailer
            # and rejects extra concatenated records.
            require(stream.read(1) == b'', 'Raw journal has additional unrecorded data')
    except (EOFError, OSError, zlib.error, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('Invalid raw measurement journal: ' + str(error)) from error
    require(total_bytes == captured['bytes'] and checksum.hexdigest() == captured['sha256'],
            'Raw journal content differs from log-time capture')
    cases = [row['id'] for row in observed if row['kind'] == 'case']
    variants = [[row['id'], row['variant']] for row in observed if row['kind'] == 'variant']
    profiles = [row['profile'] for row in observed if row['kind'] == 'profile']
    require(cases == inventory['case_ids'] == [row['id'] for row in scores],
            'Raw journal case inventory/order differs')
    require(variants == inventory['variants'] and profiles == inventory['profiles'],
            'Raw journal variant/profile inventory differs')
    return {'valid': True, 'filename': path.name, 'sha256': sha256(path.read_bytes()).hexdigest(),
            'uncompressed_sha256': checksum.hexdigest(), 'uncompressed_bytes': total_bytes,
            'record_count': len(observed), 'case_count': len(cases), 'variant_count': len(variants),
            'profile_count': len(profiles), 'records': captured['records']}


def load_material():
    payload = (FOLDER / 'independent_freeze_v1.json').read_bytes()
    require(sha256(payload).hexdigest() == GOLD_FREEZE_SHA256, 'Gold freeze changed')
    freeze = json.loads(payload)
    for item in freeze['files']:
        data = (ROOT / item['path']).read_bytes()
        require(len(data) == item['bytes'] and sha256(data).hexdigest() == item['sha256'],
                'Frozen material changed: ' + item['path'])
    material = json.loads((FOLDER / 'independent_cases_v1.json').read_bytes())
    inventory = json.loads((FOLDER / 'independent_source_inventory_v1.json').read_bytes())
    cases = material['cases']
    require(len(cases) == len({c['id'] for c in cases}) == 86, 'Case inventory changed')
    require(sum(len(c['expected']['questions']) for c in cases) == 74, 'Question inventory changed')
    for case in cases:
        require(set(case['expected']) <= EXPECTED_KEYS, 'Unimplemented expected predicate')
        require(all(set(r) <= READING_KEYS for r in case['expected']['required_readings']),
                'Unimplemented reading predicate')
        require(re.fullmatch('[a-z][a-z0-9_]{0,127}', case['input']['source_id']) is not None,
                'Invalid fixed source ID')
    return freeze, material, inventory


def runtime_snapshot(manifest_path, runtime_root):
    payload = manifest_path.read_bytes()
    checksum = sha256(payload).hexdigest()
    require(checksum in PINS, 'Unapproved runtime manifest')
    manifest, pin = json.loads(payload), PINS[checksum]
    require(len(manifest['files']) == pin['file_count'], 'Runtime file count changed')
    for key in ('snapshot_sha256', 'archive_sha256'):
        require(manifest[key] == pin[key], 'Runtime pin mismatch: ' + key)
    require(digest(manifest['files']) == pin['snapshot_sha256'], 'Bad runtime inventory digest')
    paths = [r['path'] for r in manifest['files']]
    actual = {'pyproject.toml'} | {str(p.relative_to(runtime_root)) for p in (runtime_root / 'src').rglob('*')
        if p.is_file() and '__pycache__' not in p.parts
        and not any(s.endswith(('.egg-info', '.dist-info')) for s in p.parts)}
    require(len(paths) == len(set(paths)) and actual - NON_RUNTIME == set(paths),
            'Actual package inventory differs from frozen inventory')
    for item in manifest['files']:
        data = (runtime_root / item['path']).read_bytes()
        require(len(data) == item['bytes'] and sha256(data).hexdigest() == item['sha256'],
                'Runtime bytes changed: ' + item['path'])
    archive = manifest_path.parent / manifest['archive_filename']
    require(sha256(archive.read_bytes()).hexdigest() == pin['archive_sha256'], 'Runtime archive changed')
    by_path = {r['path']: r for r in manifest['files']}
    with tarfile.open(archive, 'r:gz') as saved:
        members = saved.getmembers()
        require(len(members) == len(paths) and {m.name for m in members} == set(paths)
                and all(m.isfile() for m in members), 'Frozen archive inventory changed')
        for member in members:
            data = saved.extractfile(member).read()
            require(len(data) == by_path[member.name]['bytes'] and sha256(data).hexdigest() == by_path[member.name]['sha256'],
                    'Frozen archive member changed')
    files = list(manifest['files'])
    for path in (Path(__file__), ROOT / 'tests/test_discourse_evaluator.py'):
        data = path.read_bytes()
        files.append({'path': str(path.relative_to(ROOT)), 'bytes': len(data), 'sha256': sha256(data).hexdigest()})
    return {'runtime_root': str(runtime_root), 'runtime_freeze': str(manifest_path.relative_to(ROOT)),
            'runtime_freeze_sha256': checksum, 'runtime_snapshot_sha256': pin['snapshot_sha256'],
            'runtime_file_count': len(paths), 'files': files, 'measured_snapshot_sha256': digest(files),
            'excluded_existing_documentation_metadata': sorted(actual & NON_RUNTIME)}


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


def constrained_person_argument(value):
    """Recognize the declared typed query schema without erasing its axes."""
    return (type(value) is dict and set(value) == {'kind', 'name', 'gender', 'number'}
            and value['kind'] == 'question_variable' and value['name'] == '?person'
            and value['gender'] in ('masculine', 'feminine') and value['number'] == 'singular')


def claim_view(row):
    # Unknown or missing qualification is a malformed result, not a wildcard.
    require(all(k in row for k in CLAIM_FIELDS), 'Claim omits qualification fields')
    require(type(row['positive']) is bool and row['predicate_kind'] in ('property', 'event', 'location')
            and row['voice'] in (None, 'active', 'passive'), 'Invalid claim domain')
    require(row['tense'] in ('unspecified', 'past', 'nonpast', 'future'), 'Invalid tense')
    require(all(type(row[k]) is list for k in ('args', 'time', 'place', 'restriction')), 'Claim sequences required')
    require(all(value is None or type(value) is str or constrained_person_argument(value)
                for value in row['args']), 'Invalid claim argument representation')
    if any(constrained_person_argument(value) for value in row['args']):
        require(row['predicate_kind'] == 'property' and row['voice'] is None and len(row['args']) == 1,
                'Typed person argument escaped its single-subject property domain')
    for value in row['time']:
        if type(value) is dict:
            if value.get('kind') == 'temporal_relation':
                # An unresolved complement remains None in a candidate claim;
                # validate_relational_time checks its exact attachment and
                # prevents that candidate from becoming a grounded assertion.
                require(set(value) == {'kind', 'relation', 'object'}
                        and type(value['relation']) is str and bool(value['relation'])
                        and (value['object'] is None or type(value['object']) is str),
                        'Invalid relational time representation')
            else:
                require(set(value) == {'lemma', 'form', 'source_article'}
                        and type(value['lemma']) is str and type(value['form']) is str
                        and type(value['source_article']) is bool, 'Invalid qualified time representation')
        else:
            require(type(value) is str, 'Invalid time representation')
    # Source proof equality keeps every qualification byte. The independent
    # gold has three display labels; mapping to those is a separate operation.
    return {k: deepcopy(row[k]) for k in CLAIM_FIELDS}


def claim_key(row):
    return wire(claim_view(row))


def gold_time_label(value):
    if type(value) is str:
        # v1 exposed the source lemma alone. Keep that historical adapter
        # correspondence only for its scalar output, never for a v2 object.
        return TIME_LABELS.get(value, value)
    if type(value) is dict and set(value) == {'lemma', 'form', 'source_article'}:
        require(type(value['source_article']) is bool, 'Invalid time article domain')
        return TIME_QUALIFIED_LABELS.get((value['lemma'], value['form'], value['source_article']), deepcopy(value))
    return deepcopy(value)


def gold_claim_key(row):
    result = claim_view(row)
    result['time'] = [gold_time_label(value) for value in result['time']]
    return wire(result)


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
    return True


def validate_reference_origin(ref, inputs, entities):
    origin, ids = ref['origin'], set(ref.get('candidate_entity_ids', []))
    context = inputs.get('context') or {}
    if origin == 'named':
        possible = {eid for eid, entity in entities.items()
                    if context_form_compatible(ref['surface'], entity['name'])}
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


def validate_claim_roles(claim, analysis, rows, ranges):
    """Correlate predicate and ordered arguments with this analysis's roles.

    A matching noun elsewhere in a clause is not its predicate. An entity in
    the context is not an argument until the same role's reference binds it.
    """
    assignments, refs = analysis['assignments'], analysis['references']
    def at(span):
        return {r.get('bound_entity_id') for r in refs if r['span'] == span}
    def role_arguments(roles):
        return [a for a in assignments if a['role'] in roles]
    def in_reading(span, row):
        return span is not None and span_bounds(span) in ranges[row['reading_id']]
    def argument_matches(subject, predicate):
        argument = claim['args'][0]
        if not constrained_person_argument(argument):
            return argument in at(subject['span'])
        # This is a constraint on a question interpretation, not a feature
        # acquired for the interrogative noun or an already grounded entity.
        head, dependent = rows[subject['reading_id']], rows[predicate['reading_id']]
        required = {axis: argument[axis] for axis in ('gender', 'number')}
        if (analysis['force'] != 'QUESTION' or analysis['assertion_allowed']
                or subject['role'] != 'nominal_subject' or predicate['role'] != 'nominal_predicate'
                or head.get('lexical_features', {}).get('pos') != 'INTG'
                or head.get('support_records') != [{'kind': 'grammar', 'rule': 'wh_subject'}]
                or dependent.get('lexical_features', {}).get('pos') != 'ADJ'
                or any(feature(dependent, axis) != value for axis, value in required.items())):
            return False
        question_refs = [ref for ref in refs if ref['span'] == subject['span']]
        if (len(question_refs) != 1 or question_refs[0].get('origin') != 'question_variable'
                or question_refs[0].get('status') != 'VARIABLE'
                or question_refs[0].get('bound_entity_id') != argument['name']):
            return False
        ref = question_refs[0]
        return any(
            relation.get('kind') == 'predicate_agreement'
            and relation.get('status') == 'pending_substitution'
            and relation.get('regime_licensed') is False
            and relation.get('question_variable') == argument['name']
            and relation.get('predicate_lemma') == claim['predicate']
            and relation.get('head_reading_id') == subject['reading_id']
            and relation.get('dependent_reading_id') == predicate['reading_id']
            and relation.get('head_span') == subject['span']
            and relation.get('dependent_span') == predicate['span']
            and relation.get('subject_role') == subject['role']
            and relation.get('predicate_role') == predicate['role']
            and relation.get('subject_reference_ids') == [ref.get('reference_id')]
            and all(relation.get('predicate_profile', {}).get(axis) == value for axis, value in required.items())
            and all(relation.get('subject_profile', {}).get(axis) in (None, 'unknown')
                    for axis in ('gender', 'number'))
            for relation in analysis.get('relations', []))
    if claim['predicate_kind'] in ('property', 'location'):
        subjects = role_arguments({'nominal_subject', 'inna_subject', 'kana_subject'})
        require(len(claim['args']) == 1, 'Property/location claim has an unsupported argument count')
        if claim['predicate_kind'] == 'property':
            predicates = role_arguments({'nominal_predicate', 'inna_predicate', 'kana_predicate'})
            predicates = [p for p in predicates if rows[p['reading_id']]['kind'] == 'noun'
                          and rows[p['reading_id']].get('lexical_features', {}).get('lemma') == claim['predicate']]
            require(predicates and claim['voice'] is None,
                    'Claim predicate is not its predicate-role lexical reading')
            matching_subject = {'nominal_predicate': 'nominal_subject',
                                'inna_predicate': 'inna_subject', 'kana_predicate': 'kana_subject'}
            for predicate in predicates:
                for subject in subjects:
                    linked = (predicate.get('head_span') == subject['span'] if predicate['role'] == 'nominal_predicate'
                              else predicate.get('head_span') == subject.get('head_span'))
                    if (subject['role'] == matching_subject[predicate['role']] and linked
                            and argument_matches(subject, predicate)):
                        return
            raise ValueError('Claim argument is not the bound reference of its subject role')
        else:
            require(claim['predicate'] == '@located' and claim['voice'] is None and claim['place'],
                    'Location claim lacks its declared relation/qualification')
            require(any(claim['args'][0] in at(s['span']) for s in subjects),
                    'Claim argument is not the bound reference of its subject role')
        return
    require(claim['voice'] in ('active', 'passive'), 'Event claim voice is not supported')
    for rid in analysis['reading_ids']:
        row = rows[rid]
        features = row.get('lexical_features', {})
        if (row['kind'] != 'verb' or features.get('lemma') != claim['predicate']
                or features.get('voice') != claim['voice']):
            continue
        subjects = [a for a in role_arguments({'active_subject' if claim['voice'] == 'active' else 'passive_subject'})
                    if in_reading(a.get('head_span'), row)]
        objects = [a for a in role_arguments({'direct_object'}) if in_reading(a.get('head_span'), row)]
        if len(subjects) > 1 or len(objects) > 1 or len(claim['args']) != 1 + len(objects):
            continue
        if subjects:
            subject = subjects[0]
            if not in_reading(subject.get('head_span'), row) or claim['args'][0] not in at(subject['span']):
                continue
        elif not any(claim['args'][0] == r.get('bound_entity_id') and in_reading(r['span'], row)
                     for r in refs):
            continue
        if objects and (not in_reading(objects[0].get('head_span'), row)
                        or claim['args'][1] not in at(objects[0]['span'])):
            continue
        return
    raise ValueError('Event predicate/arguments do not share their governing verb and references')


def validate_relational_time(claim, analysis, rows, ranges):
    """Check the bounded temporal-idafa representation, never normalize it away."""
    for value in claim['time']:
        if type(value) is not dict or value.get('kind') != 'temporal_relation':
            continue
        if value['object'] is None:
            require(not analysis['references_complete'] and not analysis['assertion_allowed'],
                    'Unresolved temporal object was promoted to a complete assertion')
        matched = False
        for relation in analysis.get('relations', []):
            rid = relation.get('dependent_reading_id')
            if (relation.get('kind') != 'time_adverb' or relation.get('relation_lemma') != value['relation']
                    or rid not in analysis['reading_ids'] or rid not in rows):
                continue
            row = rows[rid]
            head, dependent, complement = (relation.get(k) for k in ('head_span', 'dependent_span', 'complement_span'))
            if (not all(type(span) is dict for span in (head, dependent, complement))
                    or span_bounds(dependent) not in ranges[rid]
                    or row.get('kind') != 'noun' or row.get('lexical_features', {}).get('pos') != 'T'
                    or row.get('lexical_features', {}).get('lemma') != value['relation']
                    or relation.get('ownership_asserted') is not False):
                continue
            governed = any(a['role'] == 'time_adverb' and a['reading_id'] == rid
                           and a['span'] == dependent and a.get('head_span') == head
                           for a in analysis['assignments'])
            attached = any(a['role'] == 'idafa_complement' and a['span'] == complement
                           and a.get('head_span') == dependent for a in analysis['assignments'])
            linked = any(r.get('kind') == 'idafa' and r.get('head_span') == dependent
                         and r.get('dependent_span') == complement
                         and r.get('complement_span') == complement
                         and r.get('ownership_asserted') is False for r in analysis.get('relations', []))
            referred = any(r['span'] == complement and r.get('bound_entity_id') == value['object']
                           for r in analysis['references'])
            predicate = any(rows[x].get('lexical_features', {}).get('lemma') == claim['predicate']
                            and span_bounds(head) in ranges[x] for x in analysis['reading_ids'])
            if governed and attached and linked and referred and predicate:
                matched = True
                break
        require(matched, 'Temporal qualification lost its lexical head, idafa edge or object reference')


def validate_report(report, inputs, audit=None):
    raw = inputs['text'].encode()
    require(report['source_text'] == inputs['text'] and report['source_id'] == inputs['source_id']
            and report['source_sha256'] == sha256(raw).hexdigest() and report['scope'] == inputs['scope'],
            'Report original input identity mismatch')
    require(report['world_truth'] == 'NOT_ESTABLISHED', 'Report promoted source claims to world truth')
    require(report['report_id'] == digest({k: v for k, v in report.items() if k != 'report_id'}),
            'Report content identity mismatch')
    require(digest(report['context']['value']) == report['context']['sha256'], 'Context hash mismatch')
    supplied = inputs.get('context') or {}
    entities = {e['id']: e for e in supplied.get('entities', [])}
    require({e['id'] for e in report['context']['value']['entities']} == set(entities), 'Context invented entities')
    for e in report['context']['value']['entities']:
        want = {'gender': 'unknown', 'number': 'unknown', 'kind': 'unknown', **entities[e['id']]}
        require(e == want, 'Context traits changed')
    for key in ('speaker', 'addressee'):
        require(report['context']['value'].get(key) == supplied.get(key), 'Context participant changed')
    require(report['context']['value']['deixis'] == supplied.get('deixis', [])
            and report['context']['value']['closed_reference_scope'] is supplied.get('closed_reference_scope', False),
            'Context reference premises changed')
    cursor = 0
    expected_ranges = []
    for segment in report['partition']:
        a, b = span_bounds(segment['span'])
        require(a == cursor, 'Raw partition has a gap/overlap')
        check_span(segment['span'], inputs, segment['surface'])
        cursor = b
        if segment['kind'] in ('written_run', 'quotation'):
            expected_ranges.append((a, b))
    require(cursor == len(raw), 'Raw partition is incomplete')
    require([span_bounds(o['span']) for o in report['occurrences']] == expected_ranges,
            'Occurrence inventory differs from written source runs')
    rows, ranges = reading_rows(report)
    for occurrence in report['occurrences']:
        check_span(occurrence['span'], inputs, occurrence['surface'])
    for row in rows.values():
        if 'stem_span' in row:
            check_span(row['stem_span'], inputs, row['stem_surface'])
        else:
            # Existing inflection-reader closed operator candidates have a
            # complete operator segmentation, but no lexical stem fields.
            # This is an API adapter distinction, not a missing noun/verb
            # witness and not a morphology prediction to repair in gold.
            require(row.get('kind') == 'particle' and row.get('operator_qualified') is True,
                    'Lexical reading omitted its stem witness')
            parts = row.get('segmentation', {}).get('parts', [])
            require(len(parts) == 1 and span_bounds(parts[0]['span']) in ranges[row['reading_id']],
                    'Closed operator reading lacks its exact occurrence span')
        for part in row.get('segmentation', {}).get('parts', []):
            check_span(part['span'], inputs, part['surface'])
        for nun in row.get('nun_readings', []):
            if nun.get('realization') == 'deleted':
                require(nun.get('span') is None, 'Deleted nun has a fabricated observed span')
            elif nun.get('realization') == 'present':
                require(nun_span_valid(nun, inputs), 'Visible nun does not conserve a complete source cluster')
    clauses, analyses = {}, {}
    for clause in report['clauses']:
        check_span(clause['span'], inputs)
        require(clause['clause_id'] == digest({k: v for k, v in clause.items() if k != 'clause_id'}),
                'Clause identity mismatch')
        clauses[clause['clause_id']] = clause
        previous_clauses = [c for c in report['clauses'] if span_bounds(c['span'])[1] <= span_bounds(clause['span'])[0]]
        for analysis in clause['analyses']:
            aid = analysis['analysis_id']
            require(aid == digest({k: v for k, v in analysis.items() if k != 'analysis_id'}),
                    'Analysis identity mismatch')
            require(aid not in analyses, 'Duplicate analysis identity')
            analyses[aid] = (clause, analysis)
            check_span(analysis['span'], inputs)
            require(all(rid in rows for rid in analysis['reading_ids']), 'Analysis uses a dangling reading')
            refs = analysis['references']
            for ref in refs:
                check_span(ref['span'], inputs, ref.get('surface'))
                ids = ref.get('candidate_entity_ids', [])
                require(len(ids) == len(set(ids)) and set(ids) <= set(entities), 'Reference invented candidates')
                bound = ref.get('bound_entity_id')
                if ref.get('origin') == 'question_variable':
                    require(type(bound) is str and bound.startswith('?'), 'Invalid question-variable reference')
                else:
                    require(ref['scope'] == inputs['scope'] and ref['context_sha256'] == report['context']['sha256'],
                            'Reference scope/context mismatch')
                    require(bound is None or ids == [bound], 'Bound reference is not the sole candidate')
                    require(ref['reference_id'] == digest({k: v for k, v in ref.items() if k != 'reference_id'}),
                            'Reference identity mismatch')
                    validate_reference_origin(ref, inputs, entities)
                    validate_reference_prefix(ref, previous_clauses, supplied)
            for assignment in analysis['assignments']:
                rid, role = assignment['reading_id'], assignment['role']
                require(rid in analysis['reading_ids'] and role in ROLE_CASE, 'Assignment is detached from its reading/law')
                row = rows[rid]
                check_span(assignment['span'], inputs, assignment['surface'])
                require(assignment['required_case'] == ROLE_CASE[role], 'Role/case law mismatch')
                a, b = span_bounds(assignment['span'])
                sa, sb = span_bounds(row['stem_span'])
                require(a <= sa < sb <= b, 'Assignment changed the reading occurrence')
                if assignment.get('head_span') is not None:
                    check_span(assignment['head_span'], inputs)
                    ha, hb = span_bounds(assignment['head_span'])
                    ca, cb = span_bounds(clause['span'])
                    require(ca <= ha < hb <= cb, 'Governor escaped its clause')
                    head_rows = [rows[x] for x in analysis['reading_ids']
                                 if any(a <= ha and hb <= b for a, b in ranges.get(x, set()))]
                    if role in ('active_subject', 'passive_subject', 'direct_object'):
                        require(any(r['kind'] == 'verb' for r in head_rows), 'Verbal role has a nonverbal governor')
                    elif role == 'nominal_predicate':
                        require(any(a['role'] == 'nominal_subject' and a['span'] == assignment['head_span']
                                    for a in analysis['assignments']), 'Predicate governor is not its own subject')
                    elif role == 'idafa_complement':
                        require(any(r['kind'] == 'noun' for r in head_rows), 'Idafa complement lost its noun head')
                    elif role in ('inna_subject', 'inna_predicate', 'kana_subject', 'kana_predicate'):
                        letters = ''.join(c for c in raw[ha:hb].decode() if not unicodedata.combining(c))
                        allowed = {'إن', 'ليت', 'لعل'} if role.startswith('inna_') else {'كان', 'ليس'}
                        require(letters in allowed, 'Operator role has the wrong governor')
                if assignment.get('activated'):
                    require(analysis['licensed_syntax'] and not analysis['rejected_candidate']
                            and assignment['actual_role'] == role, 'Role activation ignores failed syntax')
                else:
                    require(assignment.get('actual_role') is None and assignment.get('inflected_case') is None
                            and assignment.get('local_case') is None, 'Unactivated assignment acquired an actual conclusion')
                actual = assignment.get('inflected_case')
                local = assignment.get('local_case')
                require(actual is None or (row['construction'] == 'inflected' and actual == ROLE_CASE[role]
                    and assignment['case_domain'] == 'inflected_case' and assignment['sign_candidates']),
                    'Actual case lacks the same reading/sign/domain')
                require(local is None or (row['construction'] == 'built' and local == ROLE_CASE[role]
                    and assignment['case_domain'] == 'local_case'), 'Local case/domain mismatch')
                for sign in assignment['sign_candidates']:
                    require(type(sign['case']) is int and CASE_VALUES[sign['case']] == ROLE_CASE[role],
                            'Sign candidate belongs to another case')
            for claim in analysis['claims']:
                claim_view(claim)
                validate_claim_roles(claim, analysis, rows, ranges)
                validate_relational_time(claim, analysis, rows, ranges)
                if analysis['assertion_allowed']:
                    require(analysis['force'] == 'ASSERT' and analysis['licensed_syntax']
                            and analysis['references_complete'] and not analysis['rejected_candidate'],
                            'Nonassertive/incomplete reading asserted a claim')
    for claim in report['claims']:
        claim_view(claim)
        require(all(type(a) is str and a in entities for a in claim['args']),
                'Grounded claim invented an entity or retained a query variable')
        require(claim['proofs'], 'Accepted claim has no proof')
        for proof in claim['proofs']:
            require(proof['analysis_id'] in analyses, 'Claim proof has a dangling analysis')
            clause, analysis = analyses[proof['analysis_id']]
            require(proof['clause_id'] == clause['clause_id'] and proof['span'] == clause['span']
                    and clause['status'] == 'LICENSED' and analysis['assertion_allowed']
                    and claim_is_in_analysis(claim, analysis), 'Claim proof borrowed another clause/claim/force')
            viable = [a for a in clause['analyses'] if not a['rejected_candidate']]
            require(viable and all(a['licensed_syntax'] and a['references_complete'] for a in viable),
                    'An unresolved alternative was discarded to assert')
            require(all(any(claim_key(claim) == claim_key(c) for c in a['claims']) for a in viable),
                    'Viable complete alternatives disagree about the accepted claim')
    if audit is not None:
        audit.walk(report)
    return rows, ranges, analyses


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


def nun_name(nun):
    if nun['kind'] == 'five_verb_raf':
        return 'raf_deleted' if nun.get('realization') == 'deleted' else 'raf'
    return nun['kind']


def feature(row, name):
    value = row.get('profile', {}).get(name, row.get('lexical_features', {}).get(name))
    if name == 'person':
        if type(value) is str and value[:1] in ('1', '2', '3'):
            value = int(value[0])
        value = PERSON_LABELS.get(value, value)
    return value


def reading_matches(expected, row, report, inputs, ranges):
    target = tuple(expected['span'])
    if target not in ranges.get(row['reading_id'], set()):
        return False
    for key in ('kind', 'person', 'gender', 'number', 'root', 'lemma'):
        actual = row.get('kind') if key == 'kind' else feature(row, key)
        if key in expected and actual != expected[key]:
            return False
    nuns = row.get('nun_readings', [])
    if not set(expected.get('nun_kinds', [])) <= {nun_name(n) for n in nuns}:
        return False
    if expected.get('distinct_nun_positions'):
        wanted = set(expected['nun_kinds'])
        chosen = [n for n in nuns if nun_name(n) in wanted and n.get('realization') == 'present']
        if {nun_name(n) for n in chosen} != wanted or not all(nun_span_valid(n, inputs) for n in chosen):
            return False
        if len({span_bounds(n['span']) for n in chosen}) != len(wanted):
            return False
        if not all(target[0] <= span_bounds(n['span'])[0] < span_bounds(n['span'])[1] <= target[1]
                   for n in chosen):
            return False
    if 'deleted_nun_span' in expected:
        deleted = [n for n in nuns if nun_name(n) == 'raf_deleted']
        if not deleted or any(n.get('span') is not None for n in deleted):
            return False
    correlation_keys = {'role', 'inflected_case', 'local_case', 'reference'} & set(expected)
    if not correlation_keys:
        return True
    for clause in report['clauses']:
        for analysis in clause['analyses']:
            if row['reading_id'] not in analysis['reading_ids'] or analysis['rejected_candidate']:
                continue
            assignments = [a for a in analysis['assignments'] if a['reading_id'] == row['reading_id']
                and span_bounds(a['span']) == target]
            if correlation_keys & {'role', 'inflected_case', 'local_case'}:
                matched = False
                for a in assignments:
                    if 'role' in expected and a.get('actual_role') != ROLE_ALIASES.get(expected['role'], expected['role']):
                        continue
                    if any(a.get(k) != expected[k] for k in ('inflected_case', 'local_case') if k in expected):
                        continue
                    matched = True
                if not matched:
                    continue
            if 'reference' in expected:
                want = expected['reference']
                refs = [r for r in analysis['references'] if span_bounds(r['span']) == target]
                if not any(set(r.get('candidate_entity_ids', [])) == set(want['candidates'])
                    and r.get('bound_entity_id') == want['bound']
                    and ('basis' not in want or r['origin'] == REFERENCE_BASES[want['basis']]) for r in refs):
                    continue
            return True
    return False


def instantiate(pattern, bindings, *, entities=None):
    result = claim_view(pattern)
    used = set()
    for field in ('args', 'time', 'place'):
        for i, value in enumerate(result[field]):
            if constrained_person_argument(value):
                require(field == 'args' and value['name'] in bindings, 'Proof omitted a typed query variable')
                bound = bindings[value['name']]
                entity = (entities or {}).get(bound, {}) if type(bound) is str else {}
                require(entity.get('kind') == 'person' and all(
                    entity.get(axis) == value[axis] for axis in ('gender', 'number')),
                    'Typed question binding lacks explicit matching person traits')
                result[field][i] = bound
                used.add(value['name'])
            elif type(value) is str and value.startswith('?'):
                require(value in bindings, 'Proof omitted a query variable')
                result[field][i] = deepcopy(bindings[value])
                used.add(value)
    require(used == set(bindings), 'Proof adds an unrequested binding')
    return result


def agreement_subject_supported(row, relation, reference, required, context_sha256):
    """Keep acquired lexical traits separate from explicit semantic premises."""
    if all(feature(row, axis) == value for axis, value in required.items()):
        return True
    basis = relation.get('subject_gender_basis', {})
    features = row.get('lexical_features', {})
    common = (features.get('pos') == 'PRON' and feature(row, 'gender') in (None, 'unknown')
              and feature(row, 'number') == required['number']
              and basis.get('kind') == 'resolved_common_gender_pronoun'
              and reference.get('reference_id') in basis.get('reference_ids', [])
              and row.get('segmentation', {}).get('licensed') is True)
    named = (features.get('pos') == 'PN' and row.get('construction') is None
             and row.get('variant') == 'declared_grammatical_paradigm'
             and row.get('segmentation', {}).get('licensed') is True
             and row.get('support_records') == [{'kind': 'explicit_context',
                  'sha256': context_sha256, 'field': 'entities.name'}]
             and reference.get('origin') == 'named'
             and basis.get('kind') == 'explicit_named_person_semantic_profile'
             and basis.get('lexical_profile_acquired') is False
             and basis.get('source_fields') == ['entities.name', 'entities.kind', 'entities.gender', 'entities.number']
             and basis.get('reference_ids') == [reference.get('reference_id')]
             and all(features.get(axis) is None for axis in ('gender', 'number')))
    return ((common or named) and basis.get('entity_id') == reference.get('bound_entity_id')
            and basis.get('context_sha256') == context_sha256)


def source_agreement_witnesses(claim, required, entity_id, document):
    """Independently bind a typed answer to the accepted claim's own ADJ edge.

    An N predicate with the same lemma, an unrelated reference, or a second
    differently qualified claim in the analysis cannot lend an agreement
    witness. These checks do not infer the lexical profile or parse Arabic.
    """
    rows, ranges = reading_rows(document)
    analyses = {(c['clause_id'], a['analysis_id']): a for c in document['clauses']
                if c['status'] == 'LICENSED' for a in c['analyses']}
    pairs = {'nominal_predicate': 'nominal_subject', 'inna_predicate': 'inna_subject',
             'kana_predicate': 'kana_subject'}
    witnesses = []
    for proof in claim['proofs']:
        analysis = analyses.get((proof['clause_id'], proof['analysis_id']))
        if (analysis is None or analysis.get('rejected_candidate') is not False
                or analysis.get('licensed_syntax') is not True or analysis.get('references_complete') is not True
                or analysis.get('assertion_allowed') is not True or analysis.get('force') != 'ASSERT'
                or not claim_is_in_analysis(claim, analysis)):
            continue
        # Until claims carry their own explicit edge IDs, an analysis with
        # multiple distinct semantic claims does not select this one edge.
        if any(claim_key(other) != claim_key(claim) for other in analysis['claims']):
            continue
        for relation in analysis.get('relations', []):
            head_id, dependent_id = relation.get('head_reading_id'), relation.get('dependent_reading_id')
            head_span, dependent_span = relation.get('head_span'), relation.get('dependent_span')
            if (relation.get('kind') != 'predicate_agreement' or relation.get('status') != 'confirmed'
                    or relation.get('regime_licensed') is not True
                    or relation.get('predicate_lemma') != claim['predicate']
                    or any(relation.get('axes', {}).get(axis) != 'confirmed' for axis in required)
                    or any(relation.get(profile, {}).get(axis) != value
                           for profile in ('subject_profile', 'predicate_profile') for axis, value in required.items())
                    or head_id not in analysis['reading_ids'] or dependent_id not in analysis['reading_ids']
                    or head_id not in rows or dependent_id not in rows
                    or type(head_span) is not dict or type(dependent_span) is not dict
                    or span_bounds(head_span) not in ranges[head_id]
                    or span_bounds(dependent_span) not in ranges[dependent_id]):
                continue
            head, dependent = rows[head_id], rows[dependent_id]
            features = dependent.get('lexical_features', {})
            predicate_role, subject_role = relation.get('predicate_role'), relation.get('subject_role')
            if (dependent.get('kind') != 'noun' or features.get('pos') != 'ADJ'
                    or features.get('lemma') != claim['predicate']
                    or any(feature(dependent, axis) != value for axis, value in required.items())
                    or predicate_role not in pairs or pairs[predicate_role] != subject_role):
                continue
            heads = [a for a in analysis['assignments'] if a['reading_id'] == head_id
                     and a['role'] == subject_role and a['span'] == head_span]
            dependents = [a for a in analysis['assignments'] if a['reading_id'] == dependent_id
                          and a['role'] == predicate_role and a['span'] == dependent_span]
            if not any(a.get('activated') is True and b.get('activated') is True
                       and (b.get('head_span') == a['span'] if predicate_role == 'nominal_predicate'
                            else b.get('head_span') is not None and b.get('head_span') == a.get('head_span'))
                       for a in heads for b in dependents):
                continue
            for reference in analysis['references']:
                if (reference.get('status') != 'RESOLVED' or reference.get('bound_entity_id') != entity_id
                        or reference.get('span') != head_span
                        or reference.get('reference_id') not in relation.get('subject_reference_ids', [])
                        or reference.get('context_sha256') != document['context']['sha256']
                        or not agreement_subject_supported(head, relation, reference, required,
                                                           document['context']['sha256'])):
                    continue
                witness = {'clause_id': proof['clause_id'], 'analysis_id': proof['analysis_id'],
                           'head_reading_id': head_id, 'dependent_reading_id': dependent_id,
                           'reference_id': reference['reference_id']}
                if witness not in witnesses:
                    witnesses.append(witness)
    return witnesses


def validate_agreement_bindings(proof, query, claim, document):
    constraints = [(i, value) for i, value in enumerate(query['args']) if constrained_person_argument(value)]
    if not constraints:
        require('predicate_agreement_bindings' not in proof, 'Untyped query acquired a typed agreement receipt')
        return
    receipts = proof.get('predicate_agreement_bindings')
    require(type(receipts) is list and len(receipts) == len(constraints), 'Typed query lacks its agreement receipt')
    for receipt, (index, constraint) in zip(receipts, constraints):
        required = {axis: constraint[axis] for axis in ('gender', 'number')}
        require(type(receipt) is dict and set(receipt) == {
            'argument_index', 'variable', 'entity_id', 'required_profile', 'context_sha256', 'source_witnesses'}
            and type(receipt['argument_index']) is int and receipt['argument_index'] == index
            and receipt['variable'] == constraint['name'] and receipt['entity_id'] == proof['bindings'][constraint['name']]
            and receipt['required_profile'] == required and receipt['context_sha256'] == document['context']['sha256'],
            'Typed agreement receipt changed its argument, profile or context')
        witnesses = receipt['source_witnesses']
        require(type(witnesses) is list and witnesses and all(type(w) is dict and set(w) == {
            'clause_id', 'analysis_id', 'head_reading_id', 'dependent_reading_id', 'reference_id'}
            and all(type(v) is str for v in w.values()) for w in witnesses),
            'Typed agreement receipt has an invalid source witness')
        actual = list(map(wire, witnesses))
        expected = list(map(wire, source_agreement_witnesses(claim, required, receipt['entity_id'], document)))
        require(expected and len(actual) == len(set(actual)) and set(actual) == set(expected),
                'Typed agreement receipt lost its same-claim ADJ edge or explicit subject premise')


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
        variables.update(value['name'] for value in answer['query']['args'] if constrained_person_argument(value))
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
            wanted = instantiate(answer['query'], proof['bindings'], entities=entities)
            for variable, value in proof['bindings'].items():
                if variable in ('?person', '?place'):
                    require(type(value) is str and entities.get(value, {}).get('kind') == variable[1:],
                            'Question binding lacks its declared person/place domain')
            if sign == 'counterproofs':
                wanted['positive'] = not wanted['positive']
            require(wire(wanted) == claim_key(claim), 'Answer proof dropped or changed a qualified claim field')
            validate_agreement_bindings(proof, answer['query'], claim, document)
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


def semantic_view(report):
    rows, _ = reading_rows(report)
    return {'claims': sorted((claim_view(c) for c in report['claims']), key=wire),
            'readings': sorted(({'surface': r.get('stem_surface', ''.join(p['surface'] for p in r.get('segmentation', {}).get('parts', []))), 'kind': r['kind'],
                'construction': r['construction'], 'classes': r.get('class_candidates', []),
                'features': r['lexical_features'], 'profile': r.get('profile'),
                'nuns': [(n['kind'], n.get('realization')) for n in r.get('nun_readings', [])]}
                for r in rows.values()), key=wire),
            'clauses': [{'status': c['status'], 'force': c['force'],
                'alternatives': sorted(({'force': a['force'], 'claims': [claim_view(x) for x in a['claims']],
                    'syntax': a['licensed_syntax'], 'complete': a['references_complete'],
                    'refs': [(r['origin'], r.get('candidate_entity_ids'), r.get('bound_entity_id')) for r in a['references']]}
                    for a in c['analyses']), key=wire)} for c in report['clauses']]}


def score_case(case, report, questions, verification, audit=None, replay=None, invariance=None):
    failures, false_accepts, metrics = [], [], []
    expected, inputs = case['expected'], case['input']
    def check(name, ok, details=None, *, unsafe=False):
        metrics.append({'check': name, 'passed': bool(ok)})
        if not ok:
            failure = {'check': name, 'details': details}
            failures.append(failure)
            if unsafe:
                false_accepts.append(failure)
    try:
        rows, ranges, analyses = validate_report(report, inputs, audit)
        check('report_integrity', True)
    except (ValueError, KeyError, TypeError, UnicodeError, IndexError) as error:
        check('report_integrity', False, str(error), unsafe=True)
        rows, ranges = reading_rows(report)
    check('original_report_replay', verification.get('valid') is True, verification, unsafe=True)
    keys = {gold_claim_key(c) for c in report['claims']}
    for index, claim in enumerate(expected['required_claims']):
        check(f'required_claim:{index}', gold_claim_key(claim) in keys, claim_view(claim))
    for index, claim in enumerate(expected['forbidden_claims']):
        check(f'forbidden_claim:{index}', gold_claim_key(claim) not in keys, claim_view(claim), unsafe=True)
    if expected.get('no_grounded_claims'):
        check('no_grounded_claims', not report['claims'], [claim_view(c) for c in report['claims']], unsafe=True)
    for index, want in enumerate(expected['required_readings']):
        check(f'reading:{index}', any(reading_matches(want, r, report, inputs, ranges) for r in rows.values()), want)
    if 'force' in expected:
        wanted = {'interrogative': {'QUESTION'}, 'nonassertive_request': {'COMMAND', 'PROHIBITION'},
                  'wish': {'WISH'}, 'hope': {'HOPE'}}[expected['force']]
        observed = {a['force'] for c in report['clauses'] for a in c['analyses'] if not a['rejected_candidate']}
        check('force_preserved', bool(observed & wanted), {'expected': sorted(wanted), 'observed': sorted(observed)})
    if expected.get('restriction_must_be_preserved'):
        check('restriction_preserved', all(c['restriction'] for c in report['claims']), unsafe=True)
    if expected.get('no_material_implication'):
        check('no_material_implication', not report.get('rules') and not any(
            rel.get('kind') in ('IMPLIES', 'material_implication')
            for c in report['clauses'] for a in c['analyses'] for rel in a.get('relations', [])), unsafe=True)
    if expected.get('forbid_predicate_from_root'):
        roots = {r.get('lexical_features', {}).get('root') for r in rows.values()}
        check('no_root_predicate_promotion', all(c['predicate'] not in roots for c in report['claims']), unsafe=True)
    if expected.get('forbid_inflected_case_without_complete_witness'):
        bad = []
        for row in rows.values():
            if row['construction'] != 'inflected':
                continue
            supports = [s for s in row.get('support_records', []) if 'byte_start' in s]
            forms = {audit.receipt(s)['form'] for s in supports} if audit is not None else set()
            if len(forms) < 2:
                bad.append(row['reading_id'])
        check('no_shape_only_nominal_construction', not bad, bad, unsafe=True)
    if expected.get('forbid_person_promotion_from_final_t'):
        bad = []
        for row in rows.values():
            if feature(row, 'person') != 'first':
                continue
            supports = [s for s in row.get('support_records', []) if 'byte_start' in s]
            if audit is None or not any('1S' in audit.receipt(s)['tokens'] for s in supports):
                bad.append(row['reading_id'])
        check('no_final_t_person_promotion', not bad, bad, unsafe=True)
    for index, want in enumerate(expected['questions']):
        observed = questions[index]
        if observed.get('error'):
            check(f'question:{index}', False, observed['error'])
            continue
        answer = observed['answer']
        try:
            validate_answer(answer, report, observed['inquiry'], inputs, want['text'])
            check(f'question_integrity:{index}', True)
        except (ValueError, KeyError, TypeError, IndexError) as error:
            check(f'question_integrity:{index}', False, str(error), unsafe=True)
        check(f'answer_replay:{index}', observed['verification'].get('valid') is True,
              observed['verification'], unsafe=True)
        outcome = want['outcome']
        if outcome == 'NO_GROUNDED_SUPPORT':
            ok = answer['status'] in ('UNKNOWN', 'DEFER', 'OUT_OF_SCOPE') and not answer['proofs'] and not answer['counterproofs'] and not answer['bindings']
            check(f'question:{index}', ok, {'status': answer['status']}, unsafe=not ok)
        elif outcome == 'BINDINGS':
            variable = {'place': '?place', 'time': '?time', 'object': '?object'}.get(want.get('binding_kind'), '?person')
            actual = []
            for binding in answer['bindings']:
                if set(binding['values']) == {variable} and binding['status'] == 'SUPPORTED':
                    value = binding['values'][variable]
                    actual.append(gold_time_label(value) if variable == '?time' else value)
            actual_keys, wanted_keys = {wire(v) for v in actual}, {wire(v) for v in want['bindings']}
            ok = (answer['status'] == 'SUPPORTED' and actual_keys == wanted_keys
                  and len(actual) == len(actual_keys) == len(answer['bindings']))
            check(f'question:{index}', ok, {'status': answer['status'], 'expected': want['bindings'], 'actual': actual},
                  unsafe=bool(actual_keys - wanted_keys))
        else:
            ok = answer['status'] == outcome
            check(f'question:{index}', ok, {'expected': outcome, 'actual': answer['status']},
                  unsafe=answer['status'] in ('SUPPORTED', 'REFUTED', 'CONFLICT') and not ok)
    if 'replay' in expected:
        check('changed_input_replay_rejected', replay is not None and replay.get('passed') is True, replay,
              unsafe=replay is not None and replay.get('passed') is False)
    if 'semantic_invariance' in expected:
        for variant in expected['semantic_invariance']:
            check('nonleakage:' + variant, invariance is not None and invariance.get(variant, {}).get('equal') is True,
                  None if invariance is None else invariance.get(variant), unsafe=True)
    return {'id': case['id'], 'track': case['track'], 'passed': not failures, 'failures': failures,
            'false_accepts': false_accepts, 'checks': metrics, 'report_status': report['status'],
            'accepted_claim_count': len(report['claims'])}


def corpus_variant(raw, mode):
    lines = []
    replacements = {'NOM': 'GEN', 'GEN': 'ACC', 'ACC': 'NOM',
                    'MOOD:IND': 'MOOD:JUS', 'MOOD:JUS': 'MOOD:SUBJ', 'MOOD:SUBJ': 'MOOD:IND'}
    for line in raw.decode().splitlines(keepends=True):
        if not line.startswith('('):
            lines.append(line)
            continue
        ending = '\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
        fields = line.rstrip('\r\n').split('\t')
        tokens = fields[3].split('|')
        if mode == 'erase_qac_case_and_mood':
            tokens = [t for t in tokens if t not in ('NOM', 'ACC', 'GEN') and not t.startswith('MOOD:')]
        else:
            tokens = [replacements.get(t, t) for t in tokens]
        fields[3] = '|'.join(tokens)
        lines.append('\t'.join(fields) + ending)
    return ''.join(lines).encode()


def gate_decision(result, allow_documented_boundaries=False):
    unexpected = []
    documented = []
    runtime = result['snapshot']['runtime_freeze_sha256']
    construction_policy = runtime == CONSTRUCTION_BOUNDARY_RUNTIME
    construction_v4_policy = runtime == CONSTRUCTION_V4_BOUNDARY_RUNTIME
    boundaries = (CONSTRUCTION_V4_BOUNDARIES if construction_v4_policy else
                  CONSTRUCTION_BOUNDARIES if construction_policy else DOCUMENTED_BOUNDARIES)
    for case in result['cases']:
        if case['passed']:
            continue
        failed = {f['check'] for f in case['failures']}
        allowed = boundaries.get(case['id'], frozenset())
        p26_signature_ok = not ((construction_policy or construction_v4_policy) and case['id'] == 'DSC-P26') or all(
            failure['check'] != 'question:0' or failure.get('details') == {
                'actual': 'DEFER', 'expected': 'SUPPORTED'}
            for failure in case['failures'])
        v4_signature_ok = not construction_v4_policy or all(
            (case['id'], failure['check']) not in {
                ('DSC-P16', 'question:0'), ('DSC-P26', 'reading:0')}
            or failure.get('details') == ({'actual': [], 'expected': ['h', 's'], 'status': 'DEFER'}
                if case['id'] == 'DSC-P16' else {'occurrence_index': 0, 'role': 'idafa_complement',
                                                'span': [13, 27], 'surface': 'حَازِمٍ'})
            for failure in case['failures'])
        entry = {'id': case['id'], 'failed_checks': sorted(failed)}
        if failed and failed <= allowed and p26_signature_ok and v4_signature_ok and not case.get('false_accepts'):
            documented.append(entry)
        else:
            unexpected.append(entry)
    safety_ok = (not result['false_accept_count'] and not result['execution_errors']
                 and not result.get('question_execution_errors') and result['total'] == 86
                 and len(result['cases']) == 86)
    if construction_policy or construction_v4_policy:
        safety_ok = (safety_ok and result.get('measurement_valid') is True
                     and result.get('raw_log', {}).get('valid') is True)
    approved = (construction_policy or construction_v4_policy or (DOCUMENTED_BOUNDARY_RUNTIME is not None
                                        and runtime == DOCUMENTED_BOUNDARY_RUNTIME))
    partial_gate = bool(allow_documented_boundaries and approved and safety_ok and not unexpected)
    return {'gate_mode': 'documented_boundaries' if allow_documented_boundaries else 'strict',
            'gate_pass': bool(result['strict_pass'] or partial_gate),
            'coverage_complete': result['strict_pass'],
            'documented_boundary_failures': documented,
            'unexpected_failures': unexpected,
            'boundary_policy': 'EXACT_CASE_AND_CHECK_ALLOWLIST_NO_FALSE_ACCEPT_OR_REPLAY_EXCEPTION',
            'boundary_policy_revision': ('constructions_v4' if construction_v4_policy else
                                         'constructions_v2' if construction_policy else
                                         'discourse_v4' if approved else None),
            'boundary_policy_runtime_approved': approved}


def evaluate(qac_path, output, manifest_path, runtime_root, *, allow_documented_boundaries=False):
    require(not any(n == 'nabt' or n.startswith('nabt.') for n in sys.modules),
            'Run evaluator in a fresh process before importing any nabt module')
    require(not output.exists(), 'Refusing to overwrite a result')
    freeze, material, inventory = load_material()
    snapshot = runtime_snapshot(manifest_path, runtime_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    captured = capture_code(snapshot, output)
    data = qac_path.read_bytes()
    raw = gzip.decompress(data) if data.startswith(b'\x1f\x8b') else data
    require(sha256(raw).hexdigest() == QAC_SHA256, 'QAC source is not pinned decoded bytes')
    raw_path = output.with_suffix('.raw.jsonl.gz')
    require(not raw_path.exists(), 'Refusing to overwrite raw outputs')
    result = {'schema': VERSION, 'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'gold_freeze_sha256': GOLD_FREEZE_SHA256, 'snapshot': snapshot, 'code_archive': captured,
              'source_sha256': QAC_SHA256, 'frozen_case_count': 86, 'frozen_question_count': 74,
              'model_profiles': {}, 'cases': [], 'execution_errors': [], 'question_execution_errors': [],
              'scope': 'Authored independent source-informed episodes; known QAC labels/context premises; four withheld realizations.',
              'not_claimed': ['external natural corpus', 'unsupervised lexical semantics', 'general Arabic completeness', 'world truth']}
    sys.path.insert(0, str(runtime_root / 'src'))
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.discourse import read_discourse, ask_discourse, verify_discourse, verify_discourse_answer
    from nabt.errors import NabtError
    verify_import_origins(runtime_root)
    models, audits = {'none': None}, {'none': None}
    started = time.monotonic()
    captured_rows, captured_hash = [], sha256()
    captured_bytes = 0
    with gzip.open(raw_path, 'wb') as raw_log:
        def log(value):
            nonlocal captured_bytes
            payload = wire(value) + b'\n'
            receipt = {'identity': raw_record_identity(value), 'bytes': len(payload),
                       'sha256': sha256(payload).hexdigest()}
            require(raw_log.write(payload) == len(payload), 'Incomplete raw journal write')
            raw_log.flush()
            captured_rows.append(receipt)
            captured_hash.update(payload)
            captured_bytes += len(payload)
        for case in material['cases']:
            inputs, expected = case['input'], case['expected']
            profile = inputs['lexical_profile']
            if profile not in models:
                exclusions = tuple(':'.join(map(str, p)) for p in inventory['profiles'][profile]['excluded_verses'])
                models[profile] = learn_qac_lexicon(raw, excluded_verses=exclusions, source_id='qac')
                audits[profile] = SourceAudit(raw, exclusions)
                result['model_profiles'][profile] = models[profile].summary()
                log({'model_profile': profile, 'summary': result['model_profiles'][profile]})
            model, audit = models[profile], audits[profile]
            kwargs = {'lexical_model': model, 'context': inputs['context'],
                      'source_id': inputs['source_id'], 'scope': inputs['scope']}
            case_started = time.monotonic()
            try:
                try:
                    report = read_discourse(inputs['text'], **kwargs)
                except NabtError as error:
                    if not expected.get('invalid_input'):
                        raise
                    diagnostic = error.as_dict()
                    passed = diagnostic.get('status') == 'REJECT' and bool(diagnostic.get('code'))
                    entry = {'id': case['id'], 'track': case['track'], 'passed': passed,
                             'failures': [] if passed else [{'check': 'structured_invalid_input', 'details': diagnostic}],
                             'false_accepts': [], 'checks': [{'check': 'structured_invalid_input', 'passed': passed}],
                             'diagnostic': diagnostic}
                    log({'id': case['id'], 'diagnostic': diagnostic, 'score': entry})
                    entry['seconds'] = round(time.monotonic() - case_started, 6)
                    result['cases'].append(entry)
                    continue
                if expected.get('invalid_input'):
                    entry = {'id': case['id'], 'track': case['track'], 'passed': False,
                             'failures': [{'check': 'invalid_context_accepted', 'details': report['status']}],
                             'false_accepts': [{'check': 'invalid_context_accepted'}], 'checks': []}
                    log({'id': case['id'], 'unexpected_report': report, 'score': entry})
                else:
                    verification = verify_discourse(report, text=inputs['text'], **kwargs)
                    questions = []
                    for q in expected['questions']:
                        try:
                            answer = ask_discourse(inputs['text'], q['text'], **kwargs)
                            inquiry = read_discourse(q['text'], **{**kwargs, 'source_id': 'question'})
                            inquiry_inputs = {**inputs, 'text': q['text'], 'source_id': 'question'}
                            validate_report(inquiry, inquiry_inputs, audit)
                            qverify = verify_discourse_answer(answer, text=inputs['text'], question=q['text'], **kwargs)
                            questions.append({'answer': answer, 'inquiry': inquiry, 'verification': qverify})
                        except Exception as error:
                            failure = {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}
                            questions.append({'error': failure})
                            result['question_execution_errors'].append({'id': case['id'], 'question_index': len(questions) - 1,
                                                                       **failure})
                    replay = None
                    if 'replay' in expected:
                        change = expected['replay']['change']
                        new_kwargs = {**kwargs}
                        for key in ('context', 'scope', 'source_id'):
                            if key in change:
                                new_kwargs[key] = change[key]
                        if change.get('lexical_profile') == 'none':
                            new_kwargs['lexical_model'] = None
                        new_text = change.get('text', inputs['text'])
                        old_answer = questions[0].get('answer')
                        old_report_result = (verify_discourse(report, text=new_text, **new_kwargs)
                            if expected['replay']['kind'] != 'question_replace' else {'valid': True, 'not_applicable': True})
                        old_answer_result = (verify_discourse_answer(old_answer, text=new_text,
                            question=change.get('question', expected['questions'][0]['text']), **new_kwargs)
                            if old_answer is not None else {'valid': False, 'missing_baseline_answer': True})
                        replay = {'report': old_report_result, 'answer': old_answer_result,
                                  'passed': old_answer is not None and old_answer_result.get('valid') is False
                                    and (old_report_result.get('not_applicable') or old_report_result.get('valid') is False)}
                    invariance = None
                    if 'semantic_invariance' in expected:
                        invariance = {}
                        for mode in expected['semantic_invariance']:
                            modified = corpus_variant(raw, mode)
                            changed_model = learn_qac_lexicon(modified, source_id='qac')
                            changed = read_discourse(inputs['text'], **{**kwargs, 'lexical_model': changed_model})
                            changed_audit = SourceAudit(modified)
                            validate_report(changed, inputs, changed_audit)
                            invariance[mode] = {'equal': semantic_view(changed) == semantic_view(report),
                                                'source_sha256': sha256(modified).hexdigest()}
                            log({'id': case['id'], 'variant': mode, 'report': changed})
                    entry = score_case(case, report, questions, verification, audit, replay, invariance)
                    log({'id': case['id'], 'report': report, 'questions': questions,
                         'verification': verification, 'replay': replay, 'invariance': invariance, 'score': entry})
            except Exception as error:
                diagnostic = error.as_dict() if isinstance(error, NabtError) else None
                failure = {'id': case['id'], 'type': type(error).__name__, 'message': str(error),
                           'diagnostic': diagnostic, 'traceback': traceback.format_exc()}
                result['execution_errors'].append(failure)
                entry = {'id': case['id'], 'track': case['track'], 'passed': False,
                         'failures': [{'check': 'execution', 'details': failure}], 'false_accepts': [], 'checks': []}
                log({'id': case['id'], 'execution_error': failure, 'score': entry})
            entry['seconds'] = round(time.monotonic() - case_started, 6)
            result['cases'].append(entry)
            print(json.dumps({'case': case['id'], 'passed': entry['passed'],
                              'failures': [f['check'] for f in entry['failures']]}, ensure_ascii=False), flush=True)
    journal = verify_raw_journal(raw_path,
        {'records': captured_rows, 'sha256': captured_hash.hexdigest(), 'bytes': captured_bytes},
        {'case_ids': [case['id'] for case in material['cases']],
         'variants': [[case['id'], mode] for case in material['cases']
                      for mode in case['expected'].get('semantic_invariance', [])],
         'profiles': list(result['model_profiles']),
         'question_counts': {case['id']: len(case['expected']['questions']) for case in material['cases']}},
        result['cases'])
    verify_import_origins(runtime_root)
    # Recheck every authoritative byte after the run, not merely before it.
    require(runtime_snapshot(manifest_path, runtime_root)['measured_snapshot_sha256'] == snapshot['measured_snapshot_sha256'],
            'Measured source changed during evaluation')
    counts = defaultdict(lambda: {'passed': 0, 'total': 0})
    for case in result['cases']:
        counts[case['track']]['total'] += 1
        counts[case['track']]['passed'] += int(case['passed'])
    check_counts = Counter()
    for case in result['cases']:
        for check in case.get('checks', []):
            prefix = check['check'].split(':')[0]
            check_counts[(prefix, 'total')] += 1
            check_counts[(prefix, 'passed')] += int(check['passed'])
    by_group = {label: {'passed': sum(c['passed'] for c in result['cases'] if c['id'].startswith('DSC-' + label)),
                        'total': sum(c['id'].startswith('DSC-' + label) for c in result['cases'])}
                for label in ('P', 'T', 'B', 'L', 'V')}
    by_question_outcome = defaultdict(lambda: {'passed': 0, 'total': 0})
    scored_cases = {c['id']: c for c in result['cases']}
    for case in material['cases']:
        checks = {c['check']: c['passed'] for c in scored_cases[case['id']].get('checks', [])}
        for index, question in enumerate(case['expected']['questions']):
            count = by_question_outcome[question['outcome']]
            count['total'] += 1
            count['passed'] += int(checks.get(f'question:{index}', False))
    result.update(completed_at_utc=datetime.now(timezone.utc).isoformat(), seconds=round(time.monotonic() - started, 6),
                  passed=sum(c['passed'] for c in result['cases']), total=len(result['cases']),
                  by_track=dict(counts), false_accept_count=sum(len(c['false_accepts']) for c in result['cases']),
                  by_group=by_group, by_question_outcome=dict(by_question_outcome),
                  false_accept_case_count=sum(bool(c['false_accepts']) for c in result['cases']),
                  raw_log=journal, measurement_valid=True,
                  by_check={name: {'passed': check_counts[(name, 'passed')], 'total': check_counts[(name, 'total')]}
                      for name in sorted({key[0] for key in check_counts})})
    result['strict_pass'] = (result['passed'] == result['total'] == 86 and not result['execution_errors']
                             and not result['question_execution_errors'] and not result['false_accept_count'])
    result.update(gate_decision(result, allow_documented_boundaries))
    output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('passed', 'total', 'strict_pass', 'false_accept_count', 'gate_pass', 'gate_mode')}, ensure_ascii=False))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qac', type=Path, required=True)
    parser.add_argument('--runtime-root', type=Path, default=ROOT)
    parser.add_argument('--runtime-freeze', type=Path, default=ROOT / 'evidence/constructions/code_freeze_v4.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-documented-boundaries', action='store_true',
                        help='Permit only reviewed coverage misses; strict_pass remains false and every false acceptance blocks')
    args = parser.parse_args(argv)
    result = evaluate(args.qac.resolve(), args.output.resolve(), args.runtime_freeze.resolve(), args.runtime_root.resolve(),
                      allow_documented_boundaries=args.allow_documented_boundaries)
    return 0 if result['gate_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
