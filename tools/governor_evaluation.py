#!/usr/bin/env python3
"""New independent governor pilot evaluation, with frozen semantic expectations.

The source corpus/gold was frozen before opening the new implementation.
Production APIs execute the program; source semantics and certificate replay
are checked using independently frozen statements and the previously reviewed
independent replay checker, never the production semantic checker.
"""
from __future__ import annotations

import argparse
import copy
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
import time

from arabic_syntax_evaluation_helpers import oracle_helpers as oracle

VERSION = 'nabt.governors.published-regression-evaluator.v2'
CODE_FREEZE_SHA256 = '1d48dd43210fb15b3bedbb0d8dc32b473b691842f89efb1a887d9cc2273b06d8'
CODE_SNAPSHOT_SHA256 = '5b546537c8398eacc5628d5aad1cd8f6f452578a33e834a299a1f68970fe6996'
# Explicitly approved snapshots, never a caller-recomputed manifest override.
# Original material and first-run evidence remain byte-for-byte unchanged.
APPROVED_CODE_FREEZES = {
    'd904702b8633f8102c6795f3beeff0d5584e908ee7b0d1c605c168103ab87f94':
        '814ec3f4ea340b09b594ff162e65e49be8e4110088da5feae02fe41eb8a71d6c',
    '9d9f71eb1b26caac6ea170fe839e7b7f2903eccf827c5bbf7b2c78d3a46a13cd':
        'c00458629fcd08a6cefb616d0fb1caaec5958996b0532043d0fd1a92d922740a',
    '5cdea1a66bd92f3f014cc2f14ab2d502f43f630d03977cb111020e3370907eed':
        'e8e31cdaa1cb56e3700befd4d8fb883e11f83cd684e6cd72b45e133410bf3cac',
    'b15dfab7ed6166aa5aae236c7c0b22ce48f805a6bc0d8f6c3b6f12bae2b951ee':
        '82a5d9b283d403bf257a95e5c8a1eb9b2ea300a90ca1a2e881de478bf29f7496',
    '8449c5c4bf32549c6147de006b0586d41cb4c6f656e2764c63e3437a35b7bffd': '4b5c8f4f7c2bb765791e0a9c94e1be279a1a3ad1e186e6346d77546f23a47d46',
    CODE_FREEZE_SHA256: CODE_SNAPSHOT_SHA256,
    '493626c2bed79ba40a733e7c35995efbbf9d1190139d9e6783fee05a08ad0fc4':
        '96d7e5328966d41eaf0cb5fd012e52b0fd48f783ad5d170bd9eac76e3988fef4',
    '304fddda0276053f8a6404a7d21ca7fb2019e9a0c0aa98b5718b52684efec2da':
        '41ad5f8719d838f3b039633ee69175fcbbceb079e4a786b7d34d2c920821c3ee',
    'b9ffd279e093b30cadbb4c61a23eb3f0b314ae5ae0da1374907ae8b133333434':
        '33cb00870b810ddfef44d1c9c665c289223faf5164517fb1d0bdc803081a5066',
}
PROFILE = 'nabt.arabic-governors.v1'
BASELINE_PROFILE = 'nabt.arabic-syntax.v1'
MATERIAL_FREEZE_SHA256 = '78db2dd50ec89b2ff49047cdae5cf3015eabe8b72533c3c8db1925e5c3b32d82'
ANNOTATION_FREEZE_SHA256 = '0c3827420b1971c3a2092824b35d42193f73022b200008fa581c09fa5a9aee1b'
PREOPEN_ERRATA_SHA256 = '0bfc613d1471084e6dc96eb3099249ef1dc2d8c09bd1ac95bd1a63e9abcb8f78'
SUPPLEMENT_FREEZE_SHA256 = '513d7a578df9e3b65183415b451e6dd2bd55470b73d3d8409a4d22670d447a17'
SUPPLEMENT_ERRATA_SHA256 = '2ca3ade331cc6078b96e0f633378189c6f055c39d2b16f8d2227c4f4b004d4dd'
TABLE_SHA256 = '708eebc31f9600fded7a7dd33e89d77170c451c1fe2779740178b52fe50382e0'


class EvaluatorError(RuntimeError):
    """An unexpected checker failure cannot count as rejected evidence."""


def require(condition, message):
    if not condition:
        raise oracle.ReplayValidationError(message)


def load_pinned(path, digest):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == digest, f'Frozen artifact differs: {path.name}')
    return json.loads(raw)


def verify_listed_files(directory, manifest, expected):
    rows = manifest.get('files')
    require(type(rows) is list, 'Freeze needs a file list')
    require({r['path'] for r in rows} == set(expected) and len(rows) == len(expected),
            'Freeze has an incomplete or repeated file inventory')
    for row in rows:
        raw = (directory / row['path']).read_bytes()
        require(len(raw) == row['bytes'] and sha256(raw).hexdigest() == row['sha256'],
                f'Frozen file differs: {row["path"]}')


def verify_code_freeze(root, path):
    root=Path(root);path=Path(path)
    raw=path.read_bytes()
    manifest_hash=sha256(raw).hexdigest()
    require(manifest_hash in APPROVED_CODE_FREEZES, 'Runtime freeze is not an explicitly approved snapshot')
    manifest=json.loads(raw)
    rows=manifest['files']
    require(type(rows) is list and len(rows)==len({r['path'] for r in rows}), 'Invalid code-freeze inventory')
    digest=sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    require(digest==APPROVED_CODE_FREEZES[manifest_hash]==manifest['snapshot_sha256'], 'Different authoritative code snapshot')
    actual={'pyproject.toml'} | {str(p.relative_to(root)) for p in (root/'src'/'nabt').rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.json','.txt'}}
    require(actual=={r['path'] for r in rows}, 'Code snapshot omits or adds authoritative package files')
    for row in rows:
        raw=(root/row['path']).read_bytes()
        require(len(raw)==row['bytes'] and sha256(raw).hexdigest()==row['sha256'],
                'Authoritative implementation differs from freeze: '+row['path'])
    archive=path.parent/manifest['archive_filename']
    require(sha256(archive.read_bytes()).hexdigest()==manifest['archive_sha256'], 'Archived implementation differs from freeze')
    return {'snapshot_sha256':digest,'files':len(rows),'archive_sha256':manifest['archive_sha256']}


def verify_loaded_package(repository, modules=None):
    """Bind execution to the frozen checkout, not an installed same-name wheel."""
    modules=sys.modules if modules is None else modules
    base=(Path(repository)/'src').resolve()
    checked=[]
    require('nabt' in modules,'The evaluated package has not been imported')
    for name,module in list(modules.items()):
        if name!='nabt' and not name.startswith('nabt.'):
            continue
        expected=base.joinpath(*name.split('.'))
        filename=getattr(module,'__file__',None)
        origin=getattr(getattr(module,'__spec__',None),'origin',None)
        if filename is None:
            locations=list(getattr(module,'__path__',[]))
            require(origin is None and locations and all(Path(p).resolve()==expected for p in locations),
                    'Loaded namespace is outside the frozen package: '+name)
            continue
        actual=Path(filename).resolve()
        require(actual in (expected.with_suffix('.py'),expected/'__init__.py')
                and actual.is_relative_to(base/'nabt') and origin is not None and Path(origin).resolve()==actual,
                'Loaded module is not the frozen checkout: '+name)
        checked.append({'module':name,'path':str(actual.relative_to(base)),
                        'sha256':sha256(actual.read_bytes()).hexdigest()})
    require(any(r['module']=='nabt.governor_reader' for r in checked)
            and any(r['module']=='nabt.semantics' for r in checked),
            'The new reader and kernel must be imported from the frozen checkout')
    return sorted(checked,key=lambda item:item['module'])


def load_material(directory):
    directory = Path(directory)
    freeze = load_pinned(directory / 'material_freeze.json', MATERIAL_FREEZE_SHA256)
    verify_listed_files(directory, freeze, ['build_frozen_material.py', 'episodes.json',
                                           'original_excerpts.json', 'protocol.json',
                                           'dataset_validation.json'])
    af = load_pinned(directory / 'annotation_freeze.json', ANNOTATION_FREEZE_SHA256)
    require(af['parent_freeze_sha256'] == MATERIAL_FREEZE_SHA256, 'Annotation belongs to another freeze')
    verify_listed_files(directory, af, ['build_statement_annotations.py', 'statement_annotations.json'])
    errata = load_pinned(directory / 'preopen_errata.json', PREOPEN_ERRATA_SHA256)
    require(errata['implementation_opened'] is False and errata['runtime_results_seen'] is False,
            'This evaluator only accepts the fixed pre-open interface errata')
    episodes = json.loads((directory / 'episodes.json').read_text())['episodes']
    by_id = {x['id']: x for x in episodes}
    require(len(by_id) == len(episodes) == 32, 'Wrong episode inventory')
    for fix in errata['changes']:
        event = by_id[fix['episode_id']]['events'][fix['event_index']]
        if fix['field'] == 'op':
            require(event['op'] == fix['original'], 'Erratum operation no longer matches its frozen source')
            event['op'] = fix['corrected']
        elif fix['field'] == 'gold.status':
            require(event['gold']['status'] == fix['original'], 'Erratum status no longer matches its frozen source')
            event['gold']['accepted_statuses'] = fix['accepted_statuses']
        else:
            raise oracle.ReplayValidationError('Unrecognized frozen erratum')
    records = json.loads((directory / 'statement_annotations.json').read_text())['records']
    annotations = {x['source_text_sha256']: x for x in records}
    require(len(annotations) == len(records) == 15, 'Wrong independent statement inventory')
    manual = {digest: {'facts': record['facts'], 'rules': record['rules']}
              for digest, record in annotations.items()}
    supplement_freeze=load_pinned(directory/'identity_supplement_freeze.json',SUPPLEMENT_FREEZE_SHA256)
    require(supplement_freeze['original_material_freeze_sha256']==MATERIAL_FREEZE_SHA256,
            'Identity supplement belongs to another original corpus')
    verify_listed_files(directory,supplement_freeze,['build_identity_supplement.py','identity_supplement.json',
                                                   'identity_supplement_annotations.json','prefreeze_protocol_amendment.json'])
    supplement=json.loads((directory/'identity_supplement.json').read_text())['episodes']
    require(len(supplement)==6 and len({c['id'] for c in supplement})==6, 'Wrong identity supplement inventory')
    extra_errata=load_pinned(directory/'identity_supplement_preopen_errata.json',SUPPLEMENT_ERRATA_SHA256)
    require(extra_errata['new_implementation_opened'] is False and extra_errata['new_implementation_results_seen'] is False,
            'Supplement correction was not made before new implementation exposure')
    supplement_by_id={c['id']:c for c in supplement}
    for correction in extra_errata['changes']:
        event=supplement_by_id[correction['episode_id']]['events'][correction['event_index']]
        require(correction['field']=='text' and event['op']=='query' and event['text']==correction['original'],
                'Supplement query erratum differs from the frozen original')
        event['text']=correction['corrected']
    episodes+=supplement
    extra=json.loads((directory/'identity_supplement_annotations.json').read_text())['records']
    require(len(extra)==7 and len({a['source_text_sha256'] for a in extra})==7, 'Wrong supplemental source inventory')
    for record in extra:
        checksum=record['source_text_sha256']
        require(checksum not in annotations, 'Supplement silently replaces earlier annotations')
        annotations[checksum]=record
        manual[checksum]={'facts':record['facts'],'rules':record['rules']}
    excerpts = json.loads((directory / 'original_excerpts.json').read_text())['examples']
    require(len(excerpts) == 6, 'Wrong original-excerpt inventory')
    return episodes, excerpts, manual, annotations


def normalized_gold_rule(rule):
    def convert(atom):
        return {**atom, 'args': ['?x' if term == '$x' else term for term in atom['args']]}
    return {'body': [convert(a) for a in rule['body']], 'head': convert(rule['head'])}


def projection(document, gold):
    actual_facts = [f['atom'] for f in document['facts']]
    actual_rules = [{'body': r['body'], 'head': r['head']} for r in document['rules']]
    expected_facts = gold['facts']
    expected_rules = [normalized_gold_rule(r) for r in gold.get('rules', [])]
    f = list(map(oracle.atom_key, actual_facts)); fg = list(map(oracle.atom_key, expected_facts))
    r = list(map(oracle.rule_key, actual_rules)); rg = list(map(oracle.rule_key, expected_rules))
    exact = sorted(f) == sorted(fg) and sorted(r) == sorted(rg)
    forbidden = set(map(oracle.atom_key, gold.get('forbidden_facts', [])))
    no_forbidden = not (set(f) & forbidden)
    safe = set(f) <= set(fg) and set(r) <= set(rg) and no_forbidden
    return {'exact_manual_projection': exact,
            'admitted_claims_licensed': not document['accepted'] or safe,
            'forbidden_fact_absent': not document['accepted'] or no_forbidden,
            'accepted': document['accepted'], 'fact_count': len(f), 'rule_count': len(r),
            'semantic_read': bool(document['accepted'] and exact and (fg or rg))}


def exception_record(error):
    if hasattr(error, 'as_dict'):
        return error.as_dict()
    return {'type': type(error).__name__, 'message': str(error)}


def check_original_excerpt(example, package_root):
    raw = (package_root / 'data' / 'source_evidence' / (example['document_id'] + '.txt')).read_bytes()
    require(sha256(raw).hexdigest() == example['document_sha256'], 'Original document no longer matches its pin')
    part = raw[example['byte_start']:example['byte_end']]
    require(part == example['raw_text'].encode('utf-8'), 'Original excerpt differs from its source interval')
    require(sha256(part).hexdigest() == example['excerpt_sha256'], 'Original excerpt digest differs')
    context = raw[example['context_byte_start']:example['context_byte_end']]
    require(context == example['context_text'].encode('utf-8'), 'Original excerpt context differs')
    return True


def check_answer(answer, active, scope, manual, annotations, target, language):
    # The frozen question and active inventory are passed independently; the
    # certificate's own target and program fingerprint cannot authorize itself.
    return oracle.validate_answer_certificates(
        answer, active, scope, manual, expected_query=target,
        expected_program_sha256=oracle.program_identity(active, scope, language),
        statement_oracle=annotations,
    )


QATR_SHA256 = '2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d'
POLICY_SHA256 = '26fdd34913ccca180bb1bf19bd58d725881117c0d01027f51374fd29d578dfa6'
POLICY_PASSAGES = {
    'declension_and_substitute_marks': (3959, 5746, 'a4c553289ce6e19ae192accf269e550320727316d003e290d95d81bd9b32cf15', 75, 91),
    'estimated_declension': (5746, 6128, 'fe9907dfb227096e468a9283ff0049a4dd8e209c738c9de4bc90c54370fdc58c', 92, 95),
    'noun_marks': (1516, 1648, 'f2884290fc0e41736434368d50ed57bd5bf4cd582a32a805615355944a401002', 43, 44),
    'inna_roles_and_force': (15482, 15986, 'a72b28bffeed9a4fa9e9df1ea20e36b795442213dca9ca236a2c79993e8a8cba', 187, 190),
    'inna_scopes_and_blockers': (15732, 17068, '8aec6f90cb38e2d980348b3b6679512d3dc5c5df9d1935ab66a658c63d4ac458', 189, 200),
}


def check_source_policy(policy, package_root):
    require(type(policy) is dict, 'Governor evidence needs a source policy')
    require(policy['source_id'] == 'qatr' and policy['source_sha256'] == QATR_SHA256,
            'Governor policy cites a different source')
    require(policy['policy_sha256'] == POLICY_SHA256, 'Governor policy differs from the preannounced pin')
    raw=(package_root/'data'/'source_evidence'/'qatr.txt').read_bytes()
    require(sha256(raw).hexdigest() == QATR_SHA256, 'Installed grammar source differs from independently pinned qatr')
    passages=policy['passages']
    require(type(passages) is list and len(passages)==len(POLICY_PASSAGES), 'Governor source witnesses are incomplete')
    require({p['rule'] for p in passages} == set(POLICY_PASSAGES), 'Wrong governor source-role witnesses')
    for passage in passages:
        expected=POLICY_PASSAGES[passage['rule']]
        require(passage['source_id']=='qatr' and passage['source_sha256']==QATR_SHA256,
                'Passage is bound to a different grammar source')
        actual=tuple(passage[k] for k in ('start','end','span_sha256','line_start','line_end'))
        require(actual == expected, 'Grammar rule is not bound to its complete pinned source window')
        require(all(type(passage[k]) is int for k in ('start','end','line_start','line_end')),
                'Source offsets must be strict integers')
        require(sha256(raw[passage['start']:passage['end']]).hexdigest()==passage['span_sha256'],
                'Grammar passage hash differs from exact original bytes')
    require('وبالتنوين' in raw[1516:1648].decode() and 'وبالحديث عنه' in raw[1516:1648].decode(),
            'The nominality witness does not say what this policy claims')
    inna=raw[15482:15986].decode()
    require(all(s in inna for s in ('إن وأن للتأكيد','فينصبن المبتدأ اسما لهن','ويرفعن الخبر خبرا لهن','ما الحرفية')),
            'The governor/source-role witness lacks the cited requirement')
    return True


def check_governor_cue_report(report, expected, raw, source_id, annotations, package_root, *, require_reference):
    candidates=[step['governor'] for step in report['steps'] if step.get('governor') is not None]
    require(len(candidates)==1, 'Expected one complete governor cue report')
    gov=candidates[0]
    require(gov['law_id']=='nabt.governors.v1' and gov['class_code']==2 and type(gov['class_code']) is int,
            'Wrong governor finite law or class')
    require(gov['row_ids']==[1] and all(type(v) is int for v in gov['row_ids']),
            'An innā witness must identify its declared table row')
    oracle.digest(gov['table_sha256'],'Governor table digest')
    require(gov['table_sha256']==TABLE_SHA256,'Governor table differs from its preannounced pin')
    require(sha256((package_root/'data'/'governors.json').read_bytes()).hexdigest()==TABLE_SHA256,
            'Installed governor table differs from the independently recorded interface pin')
    require(gov['world_truth']=='NOT_ESTABLISHED','A governor is not a world-truth witness')
    check_source_policy(gov['source_policy'],package_root)
    role_gold={role['role']:role for role in expected['roles']}
    op=gov['operator']; wanted=role_gold['governor']
    part=oracle.check_span(op['span'],raw,source_id)
    require((op['span']['start'],op['span']['end'])==(wanted['start'],wanted['end'])
            and part.decode()==wanted['raw']==op['surface'] and op['label']=='إنّ',
            'Governor operator does not match its exact raw token')
    roles=gov['roles']
    require(type(roles) is list and len(roles)==2, 'Governor witness needs its two ordered roles')
    require(gov['syntactic_evidence_complete'] is True,'Nominality, government and actual case were not jointly established')
    record=annotations.get(sha256(raw).hexdigest())
    meaning=[] if record is None else [a for statement in record['statements'] if statement['start']==op['span']['start'] for a in statement['facts']]
    if require_reference:require(len(meaning)==1,'No independently frozen predicate meaning for this governor statement')
    prior_components=[]
    if record:
        for statement in record['statements']:
            if statement['end'] <= op['span']['start']:
                prior_components += [(statement,component) for component in statement['components']]
    for code,role in enumerate(roles):
        expected_role='subject' if code==0 else 'predicate';wanted=role_gold[expected_role]
        require(type(role['role_code']) is int and role['role_code']==code,
                'Governor role code is not its independent grammatical position')
        require(role['role']==('inna_subject' if code==0 else 'inna_predicate'), 'Wrong source-role label')
        part=oracle.check_span(role['span'],raw,source_id)
        require((role['span']['start'],role['span']['end'])==(wanted['start'],wanted['end'])
                and part.decode()==wanted['raw']==role['surface'], 'Governor role does not bind its exact source token')
        if meaning:
            lexeme=meaning[0]['args'][0] if code==0 else meaning[0]['predicate']
            require(role['lexeme']==lexeme,'Role lexical identity differs from independent statement meaning')
        require(role['category']=='noun', 'Nominal category missing from complete governor witness')
        require(type(role['surface_mark']) is int and role['surface_mark']==code,
                'Surface mark differs from the exact independently read regular-case fixture')
        require(type(role['observed_mark']) is int and role['observed_mark']==code,
                'Observed case differs from independent accusative/nominative reading')
        number=role['role_mark_number']
        require(type(number) is dict and number['domain']=='nabt.governors.role-mark.v1'
                and type(number['value']) is int and number['value']==4*code+code
                and number['authority']=='TYPED_ENCODING_ONLY', 'Typed role/mark encoding is wrong or overclaims authority')
        require(type(role['category_evidence']) is list and role['category_evidence'],
                'Role/category field has no nominality witness')
        for evidence in role['category_evidence']:
            evbytes=oracle.check_span(evidence['span'],raw,source_id)
            require(evidence['policy_rule']=='noun_marks','Nominality witness cites another policy role')
            if evidence['kind']=='visible_tanwin':
                require((evidence['span']['start'],evidence['span']['end'])==(wanted['start'],wanted['end']),
                        'Tanwin evidence belongs to another token')
                require(any(c in evbytes.decode() for c in ('ً','ٌ','ٍ')), 'Reported tanwin is absent from its source')
            elif evidence['kind']=='prior_nominal_identity':
                require(evidence['span']['end'] <= op['span']['start'], 'A prior-identity cue must precede its use')
                require(any((component['start'],component['end'])==(evidence['span']['start'],evidence['span']['end'])
                            and set(component['roles']) & {'subject','quoted_subject','predicate'}
                            for _,component in prior_components), 'Nominality cue lacks an independently annotated prior nominal role')
            else:
                raise oracle.ReplayValidationError('Unknown nominality evidence kind')
    case_check=gov['case_check']
    require(type(case_check) is dict and case_check['class_code']==2 and type(case_check['class_code']) is int,
            'Missing finite government calculation')
    require(case_check['complete']==[[[0,0],[1,1]]], 'Case calculation differs from independent two-role equation')
    require(case_check['authority']=='CASE_ASSIGNMENT_ONLY','Case solution cannot license truth or reference')
    if require_reference:
        identity=gov['referent_identity']
        require(type(identity) is dict and identity['scope']=='PREVIOUSLY_READ_IN_THIS_SOURCE',
                'Named-reference projection lacks source-local identity evidence')
        oracle.check_span(identity['span'],raw,source_id)
        require(identity['span']['end']<=op['span']['start'],'Identity witness cannot be self-licensed by the new innā clause')
        require(any((component['start'],component['end'])==(identity['span']['start'],identity['span']['end'])
                    and set(component['roles']) & {'quoted_subject'}
                    and any(identity['name'] in atom['args'] for atom in statement['facts'])
                    for statement,component in prior_components), 'Referent identity is not established by an independently read earlier subject')
        require(gov['semantic_projection']=='SOURCE_RELATIVE_ASSERTION', 'Complete identified construction did not yield its source-relative proposition')
    else:
        require(gov['referent_identity'] is None and gov['semantic_projection']=='DEFER',
                'Unidentified indefinite was turned into a globally named individual')
        require('REFERENT_IDENTITY_EVIDENCE' in json.dumps(report,ensure_ascii=False),
                'Missing indefinite reference identity is not named')
    return {'operator_span':True,'ordered_role_spans':True,'nominality_witnesses':True,
            'case_equation':True,'typed_role_numbers':True,'source_policy':True,
            'reference_identity_established':require_reference,'safe_reference_deferral':not require_reference}


def mutation_checks(answer, active, scope, manual, annotations, target, language):
    """Reject fresh proof mutations without asking the production verifier."""
    proofs = answer.get('proofs', {})
    candidates = [key for key, value in proofs.items() if isinstance(value, dict) and value.get('steps')]
    if not candidates:
        return []
    slot = candidates[0]
    base = proofs[slot]
    out = []
    def check(label, mutate):
        changed = copy.deepcopy(answer)
        mutate(changed, slot)
        try:
            check_answer(changed, active, scope, manual, annotations, target, language)
        except oracle.ReplayValidationError as exc:
            out.append({'id': label, 'rejected': True, 'error': exception_record(exc)})
        except Exception as exc:
            raise EvaluatorError('Unexpected independent checker error during mutation '+label) from exc
        else:
            out.append({'id': label, 'rejected': False})
    check('proof_missing', lambda a, s: a['proofs'].pop(s))
    check('proof_malformed', lambda a, s: a['proofs'].__setitem__(s, []))
    check('proof_wrong_query', lambda a, s: a['proofs'][s]['query'].__setitem__('predicate', 'غير_سؤال_المرجع'))
    check('proof_no_steps', lambda a, s: a['proofs'][s].__setitem__('steps', []))
    def wrong_source(a, s):
        a['proofs'][s]['steps'][0]['clause']['source_id'] = 'absent_source'
    check('proof_wrong_source', wrong_source)
    def role_swap(a, s):
        clause = a['proofs'][s]['steps'][0]['clause']
        spans = clause['component_spans']
        require(len(spans) >= 2, 'Fixture requires at least two independently annotated roles')
        spans[0], spans[1] = spans[1], spans[0]
    check('proof_wrong_roles', role_swap)
    def clipped(a, s):
        clause = a['proofs'][s]['steps'][0]['clause']
        span = clause['span']; span['start'] += 1
        raw = active[clause['source_id']].encode()
        span['span_sha256'] = sha256(raw[span['start']:span['end']]).hexdigest()
        payload = ({'atom': clause['atom']} if clause['kind'] == 'fact' else
                   {'body': clause['body'], 'head': clause['head'], 'kind': clause['rule_kind']})
        payload.update({k: clause[k] for k in ('scope','source_id','source_sha256','span','analysis_id')})
        payload['semantic_version'] = 'nabt.signed-horn.v1'
        clause['clause_id'] = oracle.content_digest(payload)
    check('proof_clipped_source_with_recomputed_hashes', clipped)
    return out


def _strip_gold(event):
    return {k: event[k] for k in ('op', 'source_id', 'query_id', 'text') if k in event}


def run_program_case(case, language):
    from nabt.program import Program, compile_request, execute_program, verify_execution
    request = {'task': 'governor_inquiry' if language == PROFILE else 'arabic_inquiry',
               'scope': 'program_' + case['id'], 'events': [_strip_gold(e) for e in case['events']]}
    program = compile_request(request)
    encoded = program.to_bytes()
    expected_number = 1
    for byte in encoded:
        expected_number = expected_number * 256 + byte
    require(expected_number == program.number, 'Program number differs from independent byte fold')
    require(Program.from_number(expected_number).to_bytes() == encoded, 'Numeric program decoder changed original bytes')
    receipt = execute_program(program)
    replay = verify_execution(receipt)
    require(replay.get('valid') is True, 'Production numeric receipt did not replay')
    return {'numeric_roundtrip': True, 'program_sha256': sha256(encoded).hexdigest(),
            'production_receipt_replay': replay, 'run_status': receipt.get('run_status'),
            'receipt': receipt}


def run(material_dir, *, profile='governor', package_root=None):
    episodes, excerpts, manual, annotations = load_material(material_dir)
    from nabt.semantics import SemanticKernel
    if profile == 'governor':
        from nabt.governor_reader import read_arabic
        language = PROFILE
    elif profile == 'baseline':
        from nabt.arabic_reader import read_arabic
        language = BASELINE_PROFILE
    else:
        raise ValueError('Unrecognized explicit evaluation profile')
    if package_root is None:
        import nabt
        package_root = Path(nabt.__file__).resolve().parent
    results=[]; real=[]; start=time.perf_counter()
    for case in episodes:
        scope='independent_' + case['id']; kernel=SemanticKernel(language_id=language)
        active={}; rows=[]; source_ok=True; query_ok=True; safe=True; restore=True; proof_ok=True
        # The frozen denominator must survive a parser or admission failure.
        required_sources=sum(event['op'] in ('add','replace') and event['gold']['accepted_required']
                             for event in case['events'])
        complete_source_readings=0; qcount=0; qmatches=0; certificates=0; mutants=[]
        for idx,event in enumerate(case['events']):
            row={'event_index':idx,'op':event['op']}; returned_answer=False
            try:
                if event['op'] in ('add','replace'):
                    raw=event['text'].encode(); sid=event['source_id']; gold=event['gold']
                    reading=read_arabic(raw,source_id=sid,scope=scope)
                    doc=reading.document.as_dict(); report=reading.as_dict()
                    restored=oracle.restore_segments(doc,raw,sid)
                    restore &= restored
                    comp=projection(doc,gold)
                    action=kernel.add_source if event['op']=='add' else kernel.replace_source
                    admission=action(raw,source_id=sid,scope=scope).as_dict()
                    require(not admission['accepted'] or doc['accepted'], 'Kernel admitted a rejected reading')
                    if admission['accepted']:
                        active[sid]=event['text']
                    safe &= comp['admitted_claims_licensed']
                    exact=bool(admission['accepted'] and comp['exact_manual_projection'])
                    if gold['accepted_required']:
                        complete_source_readings+=int(exact)
                        source_ok &= exact
                    elif case['group']=='declared_scope':
                        source_ok=False
                    row.update({'reading':report,'comparison':comp,'admission':admission,
                                'source_restored':restored,'expected_source_acceptance':gold['accepted_required']})
                    if language==PROFILE and 'governor_witness' in gold:
                        try:
                            govs=[step['governor'] for step in report['steps'] if step.get('governor') is not None]
                            if len(govs)==1 and govs[0]['syntactic_evidence_complete'] is True:
                                projected=govs[0]['semantic_projection']=='SOURCE_RELATIVE_ASSERTION'
                                row['independent_governor_cues']=check_governor_cue_report(
                                    report,gold['governor_witness'],raw,sid,annotations,package_root,
                                    require_reference=projected)
                            else:
                                row['independent_governor_cues']={'syntactic_evidence_complete':False}
                        except Exception as exc:
                            row['governor_cue_error']=exception_record(exc)
                            proof_ok=False
                            if gold['accepted_required']:source_ok=False
                elif event['op']=='remove':
                    revision=kernel.remove_source(event['source_id']).as_dict()
                    if revision['accepted']:
                        active.pop(event['source_id'],None)
                    source_ok &= revision['accepted'];row['revision']=revision
                elif event['op']=='query':
                    qcount+=1
                    answer=kernel.query(event['text'],scope=scope).as_dict();returned_answer=True
                    row['answer']=answer;target=event['gold']['goal']
                    require(oracle.atom_key(answer['query'])==oracle.atom_key(target), 'Runtime query differs from independent target')
                    status_ok=answer['status'] in event['gold'].get('accepted_statuses',[event['gold']['status']])
                    query_ok &= status_ok;qmatches+=int(status_ok)
                    row['query_status_matches']=status_ok
                    checked=check_answer(answer,active,scope,manual,annotations,target,language)
                    certificates+=len(checked);row['independent_certificates']=checked
                    # Coverage compares with the full intended episode. Safety
                    # is established by replay against the actually admitted
                    # independent gold. A rejected positive source can leave a
                    # valid negative-only theory; REFUTED is then sound even
                    # though the intended two-source episode required CONFLICT.
                    if not mutants and answer.get('proofs'):
                        mutants=mutation_checks(answer,active,scope,manual,annotations,target,language)
                        proof_ok &= all(m['rejected'] for m in mutants)
                    require(answer.get('world_truth')=='NOT_ESTABLISHED','Source-relative answer elevated to external truth')
                else:
                    raise oracle.ReplayValidationError('Unknown frozen operation')
            except Exception as exc:
                if isinstance(exc,EvaluatorError):raise
                row['error']=exception_record(exc)
                if event['op'] in ('add','replace'):
                    source_ok=False
                    if 'source_restored' not in row:restore=False
                else:query_ok=False
                if returned_answer or isinstance(exc,oracle.ReplayValidationError):
                    safe=False;proof_ok=False
                row['failure_stage']='returned_answer_validation' if returned_answer else 'execution_or_reading'
            rows.append(row)
        program_result=None
        try:program_result=run_program_case(case,language)
        except Exception as exc:program_result={'error':exception_record(exc),'numeric_roundtrip':False,'production_receipt_replay':{'valid':False}}
        complete=(case['group'] in ('declared_scope','identity_supplement') and source_ok and query_ok and safe and proof_ok
                  and restore is True and program_result['numeric_roundtrip'] is True
                  and program_result['production_receipt_replay'].get('valid') is True
                  and required_sources>0 and qcount>0 and qcount==qmatches)
        results.append({'id':case['id'],'group':case['group'],'complete_episode':bool(complete),
                        'source_restoration':restore,'admitted_claims_licensed':safe,
                        'independent_certificates_pass':proof_ok,'certificate_count':certificates,
                        'required_sources':required_sources,'complete_source_readings':complete_source_readings,
                        'queries':qcount,'query_matches':qmatches,'events':rows,'mutations':mutants,
                        'numeric_program':program_result})
    for example in excerpts:
        row={'id':example['id'],'kind':example['kind']}
        try:
            row['source_interval_matches']=check_original_excerpt(example,package_root)
            raw=example['raw_text'].encode();reading=read_arabic(raw,source_id=example['id'],scope='original_examples')
            doc=reading.document.as_dict()
            row['source_restored']=oracle.restore_segments(doc,raw,example['id'])
            gold={**example['gold'],'rules':[]}
            row['comparison']=projection(doc,gold);row['reading']=reading.as_dict()
        except Exception as exc:
            row['error']=exception_record(exc);row.setdefault('source_restored',False)
        real.append(row)
    def summarize(group):
        selected=[r for r in results if r['group']==group]
        return {'episodes':len(selected),'complete_episodes':sum(r['complete_episode'] for r in selected),
                'required_sources':sum(r['required_sources'] for r in selected),
                'complete_source_readings':sum(r['complete_source_readings'] for r in selected),
                'queries':sum(r['queries'] for r in selected),'query_matches':sum(r['query_matches'] for r in selected),
                'source_restoration_episodes':sum(r['source_restoration'] for r in selected),
                'licensed_claim_episodes':sum(r['admitted_claims_licensed'] for r in selected),
                'certificate_count':sum(r['certificate_count'] for r in selected),
                'governor_cue_reports':sum('independent_governor_cues' in e for r in selected for e in r['events']),
                'complete_governor_cue_reports':sum(e.get('independent_governor_cues',{}).get('case_equation',False) for r in selected for e in r['events']),
                'governor_cue_errors':sum('governor_cue_error' in e for r in selected for e in r['events']),
                'independent_certificate_episodes':sum(r['independent_certificates_pass'] for r in selected),
                'numeric_program_roundtrips':sum(r['numeric_program']['numeric_roundtrip'] for r in selected),
                'production_receipt_replays':sum(r['numeric_program']['production_receipt_replay'].get('valid') is True for r in selected)}
    return {'schema':'nabt.governors.independent-results.v1','evaluator_version':VERSION,'profile':language,
            'material_freeze_sha256':MATERIAL_FREEZE_SHA256,'annotation_freeze_sha256':ANNOTATION_FREEZE_SHA256,
            'preopen_errata_sha256':PREOPEN_ERRATA_SHA256,
            'identity_supplement_freeze_sha256':SUPPLEMENT_FREEZE_SHA256,
            'identity_supplement_errata_sha256':SUPPLEMENT_ERRATA_SHA256,
            'method':'New author-composed cases and six exact selections from already packaged books; procedural agent separation, no human-expert review. Safe suspension is not reading coverage. Independent semantic replay is separate from production numeric receipt replay.',
            'runtime':{'python':sys.version,'platform':platform.platform()},'seconds':time.perf_counter()-start,
            'summary':{**{g:summarize(g) for g in ('declared_scope','beyond_declared_scope','safety_control','identity_supplement')},
                       'original_excerpts':{'total':len(real),'semantic_read':sum(r.get('comparison',{}).get('semantic_read',False) for r in real),
                                            'source_restored':sum(r.get('source_restored',False) for r in real),
                                            'licensed_claims':sum(r.get('comparison',{}).get('admitted_claims_licensed',False) for r in real)}},
            'episodes':results,'original_excerpts':real}



def regression_gate(result):
    """Retain measured narrow progress without claiming the unmet coverage goal.

    This post-measurement gate is a regression floor, not the original pilot's
    success definition. It inspects episode records, not their cached summary.
    """
    require(result['profile']==PROFILE,'The governor regression gate cannot certify the baseline')
    episodes=result['episodes']; examples=result['original_excerpts']
    require(len(episodes)==38 and len({r['id'] for r in episodes})==38,'Incomplete episode evaluation')
    by_id={r['id']:r for r in episodes}
    require(set(by_id)=={f'g{n:02d}' for n in range(1,33)}|{f'h{n:02d}' for n in range(1,7)},
            'Regression gate received a different frozen inventory')
    original=[by_id[f'g{n:02d}'] for n in range(1,13)]
    capabilities=[by_id[f'h{n:02d}'] for n in range(1,6)]
    required_passes={'h01','h02','h03','h05'}
    require(all(by_id[key]['complete_episode'] is True for key in required_passes),
            'Measured capability floor failed: suspension of every case cannot pass')
    for episode in episodes:
        require(episode['admitted_claims_licensed'] is True,'An admitted claim failed independent source/theory validation: '+episode['id'])
        require(episode['independent_certificates_pass'] is True,'Independent certificate validation failed: '+episode['id'])
        require(episode['source_restoration'] is True,'Exact source restoration failed: '+episode['id'])
        require(episode['numeric_program']['numeric_roundtrip'] is True,'Numeric program roundtrip failed: '+episode['id'])
        require(episode['numeric_program']['production_receipt_replay'].get('valid') is True,
                'Numeric receipt replay failed: '+episode['id'])
        require(not any('governor_cue_error' in event for event in episode['events']),
                'An asserted governor cue failed independent source-role validation: '+episode['id'])
        for mutation in episode['mutations']:
            require(mutation['rejected'] is True and mutation.get('error',{}).get('type')=='ReplayValidationError',
                    'A mutation survived or was counted using an unexpected evaluator exception')
    certificates=sum(r['certificate_count'] for r in episodes)
    mutations=sum(len(r['mutations']) for r in episodes)
    require(certificates>=5 and mutations>=35,'Independent proof/mutation checks became vacuous')
    require(len(examples)==6 and len({r['id'] for r in examples})==6,'Original excerpts were omitted')
    require(all(r.get('source_interval_matches') is True and r.get('source_restored') is True
                and r.get('comparison',{}).get('admitted_claims_licensed') is True for r in examples),
            'Original excerpt byte restoration or claim safety failed')
    original_count=sum(r['complete_episode'] is True for r in original)
    constrained_count=sum(r['complete_episode'] is True for r in capabilities)
    excerpt_count=sum(r.get('comparison',{}).get('semantic_read') is True for r in examples)
    return {'schema':'nabt.governors.published-regression-gate.v1','status':'REGRESSION_PASS',
            'purpose':'Preserve the published measured floor; this is not a passed Arabic coverage or release goal.',
            'successful_constrained_episodes':[r['id'] for r in capabilities if r['complete_episode']],
            'original_scope':{'complete':original_count,'total':12,'baseline_complete':11},
            'constrained_scope':{'complete':constrained_count,'total':5},
            'original_excerpts':{'semantic_read':excerpt_count,'total':6},
            'licensed_claim_episodes':38,'source_restored':44,'independent_certificates':certificates,
            'rejected_certificate_mutations':mutations,
            'original_scope_goal_met':original_count==12,
            'constrained_scope_goal_met':constrained_count==5,
            'original_excerpt_goal_met':excerpt_count==6,
            'coverage_goal_met':original_count==12 and constrained_count==5 and excerpt_count==6}


def main(argv=None):
    if not __debug__:
        raise SystemExit('Independent evaluation refuses Python -O')
    parser=argparse.ArgumentParser(description=__doc__)
    repository=Path(__file__).resolve().parents[1]
    parser.add_argument('--material-dir',type=Path,default=repository/'evidence/governors/independent')
    parser.add_argument('--code-freeze',type=Path,default=repository/'evidence/nominal/code_freeze_v2.json')
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--profile',choices=('governor','baseline'),default='governor')
    parser.add_argument('--require-regression-gates',action='store_true',
                        help='Require the published limited-scope safety/capability floor; unmet coverage stays explicit')
    args=parser.parse_args(argv)
    if args.output_dir.exists():
        raise SystemExit('Output directory must be new; existing results are immutable')
    if args.require_regression_gates and args.profile!='governor':
        parser.error('--require-regression-gates is only meaningful for the frozen governor implementation')
    args.output_dir.mkdir(parents=True)
    result=None
    try:
        implementation=verify_code_freeze(repository,args.code_freeze) if args.profile=='governor' else None
        if implementation is not None:
            import nabt.governor_reader
            import nabt.semantics
            verify_loaded_package(repository)
        result=run(args.material_dir,profile=args.profile)
        if implementation is not None:
            require(verify_code_freeze(repository,args.code_freeze)==implementation,'Implementation changed during evaluation')
            result['implementation_freeze']=implementation
            result['loaded_modules']=verify_loaded_package(repository)
        result['evaluator_sha256']=sha256(Path(__file__).read_bytes()).hexdigest()
        if hasattr(sys,'set_int_max_str_digits'):sys.set_int_max_str_digits(0)
        (args.output_dir/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        (args.output_dir/'summary.json').write_text(json.dumps(result['summary'],ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(result['summary'],ensure_ascii=False,indent=2))
        if args.require_regression_gates:
            gate=regression_gate(result)
            (args.output_dir/'regression_gate.json').write_text(json.dumps(gate,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps(gate,ensure_ascii=False,indent=2))
    except Exception as exc:
        failure={'schema':'nabt.governors.evaluation-failure.v1','status':'EVALUATION_FAILURE',
                 'stage':'regression_gate' if result is not None else 'evaluation',
                 'error':exception_record(exc),'coverage_goal_met':False}
        (args.output_dir/'failure.json').write_text(json.dumps(failure,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(failure,ensure_ascii=False,indent=2),file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
