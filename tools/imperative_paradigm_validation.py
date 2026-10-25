"""Independent bare imperative certificate replay from original source bytes.

No production package is imported. Attached-word authority requires its own
source attachment checker; this checker fails closed rather than certifying
such extra claims from the morphology law alone.
"""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAW_ID = 'nabt.sound-imperative-paradigm.v1'
POLICY_SHA256 = '1f0a8baec82a0a7cd37217278e3258d12cec4e18b1408b332d32b7eecb95310d'
_spec = importlib.util.spec_from_file_location('independent_paradigm_source_checks',
                                              Path(__file__).with_name('source_name_validation.py'))
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)


def validate_imperative(candidate, audit):
    w = candidate['productive_derivation']
    S.require(w['law_id'] == LAW_ID and w['policy_sha256'] == POLICY_SHA256 and
              w['target_attested'] is False and w['target_role_labels_used'] is False,
              'wrong imperative paradigm authority')
    folder = ROOT/'src/nabt/data/source_evidence'
    raw = (folder/'imperative_paradigm_v1.json').read_bytes()
    S.require(sha256(raw).hexdigest() == POLICY_SHA256, 'paradigm policy changed')
    for p in json.loads(raw)['passages']:
        source=(folder/(p['source_id']+'.txt')).read_bytes()
        span=source[p['start']:p['end']]
        S.require(sha256(source).hexdigest()==p['source_sha256'] and
                  sha256(span).hexdigest()==p['span_sha256'] and span.decode()==p['raw_text'],
                  'paradigm source changed')
    profiles = {'2FS':(1,0,'ِ',[['ي',set()]]), '2MD':(0,1,'َ',[['ا',set()]]),
                '2FD':(1,1,'َ',[['ا',set()]]), '2MP':(0,2,'ُ',[['و',set()],['ا',set()]]),
                '2FP':(1,2,'ْ',[['ن',{'َ'}]])}
    profile=candidate['profile_id']
    S.require(profile in profiles and w['target_profile']==profile,'wrong subject profile')
    gender,number,final,suffix=profiles[profile]
    S.require(candidate['person_profile']=={'person':2,'gender':gender,'number':number} and
              candidate['aspect']=='IMPV' and candidate['construction']=='built' and
              not candidate['attached_pronouns'] and not candidate['valency_witnesses'],
              'additional subject/object authority requires a separate checker')
    receipts=candidate['supports']
    S.require(receipts and sorted({r['record_id'] for r in receipts})==w['source_support_ids'],
              'imperative receipt identity changed')
    for receipt in receipts:
        r=S._raw_support(receipt,audit)
        t=r['tokens']; form=S._decode(r['form']); parts=S.clusters(form)
        root=S._decode(S._field(t,'ROOT:'),S.ROOT_BW)
        source_profile=w['source_profile']
        prefix={'1S':'أ','1P':'ن','2MS':'ت','3MS':'ي','3FS':'ت'}.get(source_profile)
        S.require(len([other for other in audit.records.values() if other['locator'][:3]==r['locator'][:3]])==1,
                  'attached source cannot silently become a bare lexical witness')
        S.require(r['tag']=='V' and 'IMPF' in t and 'PASS' not in t and source_profile in t and
                  S._field(t,'LEM:')==candidate['lemma_bw'] and form==w['source_form'] and root==w['root'],
                  'wrong raw imperfect source')
        S.require(prefix is not None and len(root)==3 and len(set(root))==3 and
                  not set(root)&set('اويءأإآؤئىة') and len(parts)==4 and
                  parts[0]==[prefix,{'َ'}] and ''.join(p[0] for p in parts[1:])==root and
                  parts[1][1]=={'ْ'} and parts[2][1] in ({'َ'},{'ِ'},{'ُ'}) and parts[3][1]=={'ُ'},
                  'source outside declared sound imperfect class')
        S.require(not (profile=='2FP' and root.endswith('ن')),
                  'nun-final feminine plural requires an independent assimilation law')
        initial='ُ' if parts[2][1]=={'ُ'} else 'ِ'
        singular=[['ا',{initial}],[root[0],{'ْ'}],parts[2],[root[2],{'ْ'}]]
        projected=[['ت',{'َ'}],*parts[1:]]
        expected=[['ا',{initial}],[root[0],{'ْ'}],parts[2],[root[2],{final}],*suffix]
        S.require(S.clusters(w['singular_imperative'])==singular and
                  S.clusters(w['second_person_imperfect'])==projected and
                  S.clusters(candidate['form'])==expected and w['generated_form']==candidate['form'],
                  'imperative shape or intermediate premise changed')
    audit.walk(w)
