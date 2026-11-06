"""Cross-owner source binding, open obligations, and independent replay."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.grammar_catalog import application as a
from tools.arabic_training.unit_composition import execute

ROOT=Path(__file__).resolve().parents[1]
READY=all((ROOT/'formal/.lake/build/bin'/n).is_file() for n in ('unitDiscoveryProbe','progressiveUnitProbe','temporalContextProbe'))
if os.environ.get('NABT_REQUIRE_CONTEXT_NATIVE')=='1' and not READY:
    raise RuntimeError('Context applications require all native owners')


@unittest.skipUnless(READY,'build unit and temporal owners')
class ApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request=json.loads((ROOT/'examples/context_application/application.json').read_text())
        cls.report=a.analyze(cls.request)

    def test_every_row_binds_exact_source_and_all_owners_remain_visible(self):
        r=self.report;raw=self.request['text'].encode()
        self.assertEqual(r['counts']['total'],len(r['irab']['rows']))
        self.assertTrue(r['applications'])
        for row in r['applications']:
            original=r['irab']['rows'][row['row_index']]
            s=row['source_span']
            self.assertEqual(raw[s['start']:s['end']].decode(),original['surface'])
            self.assertEqual(s['source_id'],self.request['source_id'])
            self.assertEqual(row['scope']['polarity'],'negative')
            self.assertTrue(row['lower_run_indices'])
            self.assertFalse(row['world_truth_established'])
            self.assertEqual(row['missing_bridge_obligations'],list(a.BRIDGE))
        self.assertFalse(r['bridge']['application_license_granted'])
        self.assertEqual(r['shape_count']['count_domain'],'A116_LICENSED_WORD_SHAPES')
        self.assertEqual(r['counts']['domain'],'OWNER_EMITTED_ASSIGNMENT_OCCURRENCES')

    def test_current_proof_references_do_not_close_source_rule_links(self):
        r=self.report
        self.assertEqual(len(r['source_rule_links']),22)
        self.assertTrue(all(x['status']=='SOURCE_TO_THEOREM_LINK_OPEN' for x in r['source_rule_links']))
        self.assertTrue(all(not x['formal_application_established'] for x in r['proof_links']['links']))
        self.assertTrue(all(len(x['declaration']['statement_sha256'])==64 for x in r['proof_links']['links']))

    def test_top_k_changes_retrieval_without_pruning_any_owner_rows(self):
        other=a.analyze({**self.request,'limit':1})
        self.assertEqual(other['applications'],self.report['applications'])
        self.assertEqual(other['counts'],self.report['counts'])
        self.assertEqual(other['lower'],self.report['lower'])

    def test_unsupported_adverb_frame_keeps_temporal_result_without_grammar_success(self):
        q=json.loads((ROOT/'examples/context_application/application_with_adverb.json').read_text())
        r=a.analyze(q)
        self.assertEqual(r['counts']['total'],0)
        self.assertEqual(r['status'],'DEFER')
        self.assertEqual(r['reason'],'NO_OWNER_ASSIGNMENT_OCCURRENCES')
        self.assertEqual(r['temporal']['status'],'CHECKED')
        self.assertFalse(r['bridge']['application_license_granted'])

    def test_equal_span_child_scope_is_selected_by_nesting_not_list_order(self):
        q=deepcopy(self.request)
        scopes=q['context']['temporal']['scopes']
        scopes.append({**deepcopy(scopes[0]),'id':'nested','parent':'outer','force':'conditional'})
        r=a.analyze(q)
        self.assertTrue(all(row['scope_id']=='nested' for row in r['applications']))
        self.assertTrue(all(row['scope']['force']=='conditional' for row in r['applications']))

    def test_unknown_legacy_time_and_changed_diacritic_preserve_distinction(self):
        q=json.loads((ROOT/'examples/awamil_agent/nominal.json').read_text())
        r=a.analyze(q)
        self.assertTrue(r['legacy_context_adapted'])
        self.assertEqual(r['temporal']['status'],'UNKNOWN')
        self.assertTrue(all(row['scope'] is None for row in r['applications']))
        lower=execute({'op':'source','text':'كَتَبَ كُتِبَ','mode':'wasl'})['result']
        x,y=lower['written_runs']
        self.assertNotEqual(x['owner_result'],y['owner_result'])
        self.assertLess(x['source_span']['end'],y['source_span']['start'])
        self.assertTrue(lower['source_restored'])

    def test_word_boundaries_punctuation_and_quotation_are_preserved(self):
        text='كَتَبَ، «كُتِبَ» قُمْتُ.'
        r=execute({'op':'source','text':text})['result']
        self.assertEqual([x['surface'] for x in r['written_runs']],['كَتَبَ','قُمْتُ'])
        self.assertEqual(''.join(x['surface'] for x in r['segments']),text)
        self.assertFalse(r['quoted_runs_acquired'])
        for row in r['written_runs']:
            s=row['source_span'];self.assertEqual(text.encode()[s['start']:s['end']].decode(),row['surface'])

    def test_replay_rejects_proof_row_lower_and_scope_replacement(self):
        for mutate in (
            lambda r:r['proof_links']['links'][0]['declaration'].update(statement_sha256='0'*64),
            lambda r:r['applications'][0].update(scope_id='forged'),
            lambda r:r['applications'].pop(),
            lambda r:r['lower']['result']['written_runs'][0]['source_span'].update(end=8192),
            lambda r:r['bridge'].update(application_license_granted=True),
        ):
            r=deepcopy(self.report);mutate(r)
            self.assertFalse(a.verify(r,expected_request=self.request)['valid'])

    def test_replay_requires_independent_source_identity_and_context(self):
        self.assertTrue(a.verify(self.report,expected_request=self.request)['valid'])
        q=deepcopy(self.request);q['source_id']='another_occurrence'
        self.assertFalse(a.verify(self.report,expected_request=q)['valid'])
        q=deepcopy(self.request);q['context']['temporal']['evidence'][0]['active']=False
        self.assertFalse(a.verify(self.report,expected_request=q)['valid'])

    def test_cli_receipt_roundtrip_and_tampering_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            q=Path(directory)/'q.json';r=Path(directory)/'r.json'
            q.write_text(json.dumps(self.request,ensure_ascii=False));r.write_text(json.dumps(self.report,ensure_ascii=False))
            cmd=[sys.executable,'-m','tools.grammar_catalog','application','analyze','--request',str(q),'--verify',str(r)]
            p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            changed=deepcopy(self.report);changed['counts']['total']+=1;r.write_text(json.dumps(changed,ensure_ascii=False))
            p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(p.returncode,2,p.stdout+p.stderr)
