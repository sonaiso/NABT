"""Regression and forgery checks for the one explicit post-review adapter."""
from copy import deepcopy
import gzip
import importlib.util
import json
from pathlib import Path
import unittest
import tempfile
from hashlib import sha256

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tested_postreview_v2',HERE/'postreview_v2.py')
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
S=P.S;E=P.E
RECORDS={}
for line in gzip.open(HERE/'first_run_v1/raw.jsonl.gz','rt'):
    x=json.loads(line)
    if x['kind']=='case_observation':RECORDS[x['case_id']]=x['record']


def attached(cid='P01'):
    record=deepcopy(RECORDS[cid]);rows,_=E.reading_rows(record['report'])
    row=next(r for r in rows.values() if r.get('kind')=='verb' and r.get('person_evidence',{}).get('attached_pronouns'))
    return record,row


def check(record):
    raw=(HERE/'lexical_base.tsv').read_bytes()
    audit=E.SourceAudit(raw,source_id='independent_oracle_lexical_base')
    return S.attached_host_evidence(record['report'],record['inputs'],audit)


class PostreviewAdapterTests(unittest.TestCase):
    def test_six_original_failures_have_one_complete_occurrence_without_identity(self):
        for cid in sorted(P.AFFECTED):
            record,row=attached(cid)
            self.assertNotIn('identity',row)
            result=check(record)
            with self.subTest(case=cid):
                self.assertEqual(result,{'examined':1,'licensed':0,'errors':[]})
                S.occurrence_for_row(record['report'],row,record['inputs'])

    def test_duplicate_occurrence_and_duplicate_row_are_rejected(self):
        for duplicate_occurrence in (True,False):
            record,row=attached();report=record['report']
            occurrence=next(o for o in report['occurrences'] if any(r['reading_id']==row['reading_id'] for r in o['readings']))
            if duplicate_occurrence:report['occurrences'].append(deepcopy(occurrence))
            else:occurrence['readings'].append(deepcopy(row))
            with self.subTest(occurrence=duplicate_occurrence),self.assertRaisesRegex(ValueError,'exactly one'):
                S.occurrence_for_row(report,row,record['inputs'])

    def test_missing_occurrence_does_not_use_a_loose_span_fallback(self):
        record,row=attached();report=record['report']
        for o in report['occurrences']:o['readings']=[r for r in o['readings'] if r['reading_id']!=row['reading_id']]
        with self.assertRaisesRegex(ValueError,'exactly one'):
            S.occurrence_for_row(report,row,record['inputs'])

    def test_exact_row_comparison_distinguishes_bool_from_int(self):
        record,row=attached('P04');forged=deepcopy(row)
        self.assertEqual(row['person_evidence']['person_profile']['person'],1)
        forged['person_evidence']['person_profile']['person']=True
        self.assertEqual(forged,row)  # Python equality alone is insufficient.
        with self.assertRaisesRegex(ValueError,'exact reading'):
            S.occurrence_for_row(record['report'],forged,record['inputs'])

    def test_source_identity_and_digest_are_not_waived(self):
        for field,value in [('source_id','other'),('source_sha256','0'*64),('span_sha256','0'*64),('start',True)]:
            record,row=attached();occ=next(o for o in record['report']['occurrences'] if row in o['readings'])
            occ['span'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                S.occurrence_for_row(record['report'],row,record['inputs'])

    def test_complete_person_surface_is_required(self):
        record,row=attached();row['person_evidence']['surface']='أَكْرَمَ'
        self.assertTrue(check(record)['errors'])

    def test_gap_overlap_and_omitted_suffix_are_rejected(self):
        for mutation in ('gap','overlap','omitted'):
            record,row=attached();parts=row['segmentation']['parts']
            if mutation=='gap':parts[-1]['span']['start']+=2
            elif mutation=='overlap':parts[-1]['span']['start']-=2
            else:parts.pop()
            with self.subTest(mutation=mutation):self.assertTrue(check(record)['errors'])

    def test_original_frozen_scorer_still_reports_its_original_error(self):
        record,row=attached();audit=E.SourceAudit((HERE/'lexical_base.tsv').read_bytes(),source_id='independent_oracle_lexical_base')
        finding=P.R.S.attached_host_evidence(record['report'],record['inputs'],audit)
        self.assertEqual(finding['errors'][0]['message'],"'identity'")

    def test_saved_first_measurement_still_reproduces_its_full_old_score(self):
        original,records,material,audits,_,_,_=P.checked_inputs(
            HERE/'first_run_v1/result.json',HERE/'first_run_v1/raw.jsonl.gz')
        self.assertEqual(len(records),24)
        self.assertEqual(original['public_api_calls'],171)

    def test_checkout_relocation_is_the_only_snapshot_difference_allowed(self):
        saved={'runtime_root':'/workspace/original','runtime_file_count':80,'runtime_version':'0.17.0a1',
            'runtime_freeze_sha256':'a'*64,'files':[{'path':'src/example.py','bytes':1,'sha256':'b'*64}]}
        current=deepcopy(saved);current['runtime_root']='/home/runner/work/NABT/NABT'
        self.assertTrue(P.snapshot_equal(current,saved))
        variants=[]
        for field,value in [('runtime_file_count',81),('runtime_file_count',80.0),('runtime_version','other'),
                            ('runtime_freeze_sha256','0'*64),('extra_authority',True)]:
            changed=deepcopy(current);changed[field]=value;variants.append(changed)
        changed=deepcopy(current);changed['files'][0]['sha256']='0'*64;variants.append(changed)
        changed=deepcopy(current);changed['files'][0]['bytes']=True;variants.append(changed)
        changed=deepcopy(current);changed['files'][0]['path']='src/other.py';variants.append(changed)
        changed=deepcopy(current);del changed['runtime_root'];variants.append(changed)
        for changed in variants:
            with self.subTest(changed=changed):self.assertFalse(P.snapshot_equal(changed,saved))

    def test_fresh_payload_edit_cannot_use_historical_review_as_authority(self):
        baseline=json.loads((HERE/'first_run_v1/result.json').read_text())
        lines=[json.loads(line) for line in gzip.decompress((HERE/'first_run_v1/raw.jsonl.gz').read_bytes()).splitlines()]
        for change in ('world_truth','public_input','observation_order'):
            with self.subTest(change=change),tempfile.TemporaryDirectory(prefix='oracle_adapter_test_',dir=P.R.ROOT/'artifacts/local') as temporary:
                folder=Path(temporary);values=deepcopy(lines);result=deepcopy(baseline)
                if change=='world_truth':
                    call=next(x for x in values if x.get('name')=='read_discourse')
                    call['returned']['world_truth']='ESTABLISHED'
                elif change=='public_input':
                    call=next(x for x in values if x.get('name')=='read_discourse')
                    call['inputs']['text']='different source'
                else:
                    indices=[i for i,x in enumerate(values) if x['kind']=='case_observation']
                    values[indices[0]],values[indices[1]]=values[indices[1]],values[indices[0]]
                encoded=[P.R.dump(x)+b'\n' for x in values]
                inventory=[{'index':i,'bytes':len(line),'sha256':sha256(line).hexdigest(),
                            'kind':x['kind'],'case_id':x.get('case_id'),'call_id':x.get('call_id')}
                           for i,(line,x) in enumerate(zip(encoded,values))]
                raw_path=folder/'raw.jsonl.gz';raw_path.write_bytes(gzip.compress(b''.join(encoded),mtime=0))
                result['raw_journal']=P.R.finish_journal(raw_path,inventory)
                result_path=folder/'result.json';result_path.write_text(json.dumps(result,ensure_ascii=False))
                with self.assertRaisesRegex(ValueError,'Fresh raw public-call payloads'):
                    P.checked_inputs(result_path,raw_path)


if __name__=='__main__':unittest.main()
