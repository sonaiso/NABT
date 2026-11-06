"""Independent source-text oracle, withdrawal and adversarial bridge cases.

The ledger is handwritten and disclosed; expected results do not generate
premises, source clauses or production obligation profiles.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools import explainable_pilot as pilot
from tools.grammar_catalog import relational_bridge as bridge

LEDGER = (
    "موضع1 نص u_1575_1589_1601_1585_1617_32_1575_1604_1588_1580_1585.\n"
    "موضع1 موضع p_0_5.\n"
    "شجرة1 عضوية نبات.\n"
    "موضع1 قراءة yellowing_past.\n"
    "موضع1 حدث حدث1.\n"
    "حدث1 معنى اصفرار.\n"
    "حدث1 حامل شجرة1.\n"
    "شجرة1 خاصية لون_اصفر.\n"
    "نبات يقبل لون_اصفر.\n"
    "اصفرار يحول لون_اصفر.\n"
    "شجرة1 قابلية اصفرار.\n"
    "حدث1 شروط متحققة.\n"
    "ليس حدث1 مانع قائم.\n"
    "حدث1 مكان حديقة1.\n"
    "حدث1 زمان يوم1.\n"
    "شجرة1 بجانب صخرة1.\n"
    "يوم0 قبل يوم1.\n"
    "حدث1 وقوع شجرة1.\n"
    "جفاف1 دليل_سببي حدث1.\n"
)
FRAME={"reading_id":"yellowing_past","stage":"causality","occurrence_id":"موضع1",
       "entity":"شجرة1","kind":"نبات","property":"لون_اصفر","event":"حدث1",
       "time":"يوم1","place":"حديقة1","cause":"جفاف1","start":0,"stop":5,"surface":"اصفرّ"}
TARGET="اصفرّ الشجر"
NATIVE=bridge.ROOT/"formal/.lake/build/bin/verifiedReading"


def request():
    return {"source_text":LEDGER,"source_id":"authored_relational_acceptance",
            "revision":"1","scope":"تعليمي","frame":deepcopy(FRAME)}


def rebind(p,target):
    lines=p['source_text'].splitlines(keepends=True)
    lines=[x for x in lines if ' نص ' not in x and ' موضع ' not in x]
    f=p['frame']
    key='u_'+'_'.join(str(ord(c)) for c in target)
    p['source_text']=''.join(lines)+f"{f['occurrence_id']} نص {key}.\n"+f"{f['occurrence_id']} موضع p_{f['start']}_{f['stop']}.\n"


class RelationalBridgeInput(unittest.TestCase):
    def test_native_required_when_gate_requests_it(self):
        if os.environ.get("NABT_REQUIRE_RELATIONAL_NATIVE"):
            self.assertTrue(NATIVE.is_file())

    def test_boolean_offsets_and_injected_acceptance_flags_rejected(self):
        for key,value in [("start",False),("stop",1.0),("reading_id",[]),("stage",{}),("approved",True)]:
            p=request();p["frame"][key]=value
            with self.assertRaises(ValueError):bridge.validate(p)
        p=request();p['checker']='outside'
        with self.assertRaises(ValueError):bridge.validate(p)

    def test_reading_cards_are_explicit_reviewed_sources(self):
        cards=bridge.lexical_cards()
        self.assertEqual(len(cards),4)
        self.assertEqual(len({r['id'] for r in cards}),4)
        self.assertTrue(all(r['source_review'] and not r['application_certified'] for r in cards))


@unittest.skipUnless(NATIVE.is_file(),"Build verifiedReading for relational native cases")
class NativeRelationalBridge(unittest.TestCase):
    def evaluate(self,p=None,target=TARGET):
        return bridge.evaluate(target,p or request())

    def test_source_bound_causal_license_retains_trace_and_limits(self):
        r=self.evaluate()
        self.assertTrue(r['licensed'],r)
        self.assertEqual(r['status'],'SCOPED_SOURCE_LICENSE')
        self.assertEqual(len(r['native_receipt']['requirements']),17)
        self.assertTrue(r['source_analysis']['source_clauses'])
        self.assertFalse(r['world_truth_established'])
        self.assertFalse(r['grammar_acquisition_proved'])

    def test_withdraw_cause_retains_space_time_and_adjacency(self):
        p=request();p['source_text']=LEDGER.replace('جفاف1 دليل_سببي حدث1.\n','')
        r=self.evaluate(p)
        self.assertFalse(r['licensed'])
        self.assertEqual(r['native_receipt']['qualified_verdict'],'UNKNOWN_PREMISE')
        self.assertEqual([x['predicate'] for x in r['missing']],['دليل_سببي'])
        for text in ['شجرة1 بجانب صخرة1.','يوم0 قبل يوم1.','حدث1 زمان يوم1.','حدث1 مكان حديقة1.']:
            self.assertIn(text,r['ledger']['source_text'])

    def test_disposition_is_not_occurrence(self):
        p=request();p['source_text']=LEDGER.replace('حدث1 وقوع شجرة1.\n','')
        p['frame']['stage']='disposition'
        self.assertTrue(self.evaluate(p)['licensed'])
        p['frame']['stage']='occurrence'
        self.assertFalse(self.evaluate(p)['licensed'])

    def test_unknown_and_positive_blocker_do_not_substitute_for_absence(self):
        p=request();p['source_text']=LEDGER.replace('ليس حدث1 مانع قائم.\n','')
        self.assertEqual(self.evaluate(p)['native_receipt']['qualified_verdict'],'UNKNOWN_PREMISE')
        p['source_text']+='حدث1 مانع قائم.\n'
        self.assertEqual(self.evaluate(p)['status'],'REFUTED')
        p['source_text']=LEDGER+'حدث1 مانع قائم.\n'
        self.assertEqual(self.evaluate(p)['status'],'CONFLICT')

    def test_conflicted_causal_premise_never_licenses(self):
        p=request();p['source_text']+='ليس جفاف1 دليل_سببي حدث1.\n'
        self.assertEqual(self.evaluate(p)['status'],'CONFLICT')

    def test_tainted_derived_cause_cannot_be_laundered(self):
        p=request();p['source_text']=LEDGER.replace('جفاف1 دليل_سببي حدث1.\n','')
        p['source_text']+='سند1 هو صالح.\nليس سند1 هو صالح.\nإذا سند1 هو صالح فإن جفاف1 دليل_سببي حدث1.\n'
        r=self.evaluate(p)
        self.assertFalse(r['licensed'])
        cause=next(x for x in r['native_receipt']['requirements'] if x['predicate']=='دليل_سببي')
        self.assertTrue(cause['present']);self.assertFalse(cause['clean'])

    def test_independent_support_survives_one_withdrawal(self):
        p=request();p['source_text']=LEDGER.replace('جفاف1 دليل_سببي حدث1.\n','')
        p['source_text']+='سند2 هو صالح.\nإذا سند2 هو صالح فإن جفاف1 دليل_سببي حدث1.\n'
        self.assertTrue(self.evaluate(p)['licensed'])

    def test_each_bound_identity_requires_matching_source_support(self):
        for field in ['entity','kind','property','event','time','place','cause','occurrence_id']:
            with self.subTest(field=field):
                p=request();p['frame'][field]='آخر'
                self.assertFalse(self.evaluate(p)['licensed'])

    def test_exact_vowels_and_participle_preserved(self):
        rows=[('اصفرّ','yellowing_past','اصفرار'),('مُصْفَرّ','yellowing_participle','اصفرار'),
              ('كَبِرَ','growth_age','كبر_السن'),('كَبُرَ','growth_magnitude','عظم')]
        for surface,rid,sense in rows:
            p=request();p['frame'].update(reading_id=rid,surface=surface,stop=len(surface))
            p['source_text']=LEDGER.replace('yellowing_past',rid).replace('اصفرار',sense)
            rebind(p,surface)
            r=self.evaluate(p,surface)
            self.assertTrue(r['licensed'],r)
            self.assertEqual(r['native_receipt']['reading_candidates'],[rid])
            p['frame']['surface']='كَبُرَ' if rid=='growth_age' else 'كَبِرَ'
            p['frame']['stop']=len(p['frame']['surface'])
            if rid!='growth_age':continue
            self.assertFalse(self.evaluate(p,p['frame']['surface'])['licensed'])

    def test_unvocalized_growth_keeps_both_but_requires_selected_source_reading(self):
        p=request();p['frame'].update(reading_id='growth_age',surface='كبر',stop=3)
        p['source_text']=LEDGER.replace('yellowing_past','growth_age').replace('اصفرار','كبر_السن')
        rebind(p,'كبر')
        r=self.evaluate(p,'كبر')
        self.assertEqual(r['native_receipt']['reading_candidates'],['growth_age','growth_magnitude'])
        self.assertTrue(r['licensed'])
        p['source_text']=p['source_text'].replace('موضع1 قراءة growth_age.\n','')
        self.assertFalse(self.evaluate(p,'كبر')['licensed'])

    def test_all_reviewed_spellings_match_the_native_reading_domain(self):
        rows=[c['reading'] for c in bridge.lexical_cards()]
        for row in rows:
            for spelling in row['spellings']:
                with self.subTest(reading=row['id'],surface=spelling):
                    p=request();p['frame'].update(reading_id=row['id'],surface=spelling,stop=len(spelling))
                    p['source_text']=LEDGER.replace('yellowing_past',row['id']).replace('اصفرار',row['sense'])
                    rebind(p,spelling)
                    r=self.evaluate(p,spelling)
                    self.assertTrue(r['licensed'],r['status'])
                    self.assertEqual(r['native_receipt']['reading_candidates'],
                        [x['id'] for x in rows if spelling in x['spellings']])

    def test_partial_token_and_bad_offsets_rejected(self):
        for target in ['واصفرّ','اصفرّون']:
            p=request()
            if target.startswith('و'):p['frame'].update(start=1,stop=6)
            r=self.evaluate(p,target)
            self.assertFalse(r['native_receipt']['occurrence_bound']);self.assertFalse(r['licensed'])
        p=request();p['frame']['stop']=4
        self.assertFalse(self.evaluate(p)['licensed'])

    def test_repeated_occurrence_binding_is_not_merged(self):
        p=request();p['frame'].update(start=6,stop=11,occurrence_id='موضع2')
        self.assertFalse(self.evaluate(p,'اصفرّ اصفرّ')['licensed'])
        p['source_text']+='موضع2 قراءة yellowing_past.\nموضع2 حدث حدث1.\n'
        rebind(p,'اصفرّ اصفرّ')
        self.assertTrue(self.evaluate(p,'اصفرّ اصفرّ')['licensed'])

    def test_same_occurrence_id_cannot_move_or_change_target(self):
        p=request();p['frame'].update(start=6,stop=11)
        self.assertFalse(self.evaluate(p,'اصفرّ اصفرّ')['licensed'])
        self.assertFalse(self.evaluate(request(),TARGET+' أمس')['licensed'])

    def test_another_event_with_same_sense_needs_its_own_occurrence_link(self):
        p=request();p['frame']['event']='حدث2'
        p['source_text']+=''.join(line.replace('حدث1','حدث2')
            for line in LEDGER.splitlines(keepends=True)
            if line.startswith(('حدث1 ', 'ليس حدث1 ', 'جفاف1 دليل_سببي ')))
        r=self.evaluate(p)
        self.assertFalse(r['licensed'])
        self.assertEqual([x['predicate'] for x in r['missing']],['حدث'])
        p['source_text']+='موضع1 حدث حدث2.\n'
        self.assertTrue(self.evaluate(p)['licensed'])

    def test_property_and_genus_bridge_is_required(self):
        for line in ['نبات يقبل لون_اصفر.\n','اصفرار يحول لون_اصفر.\n']:
            p=request();p['source_text']=LEDGER.replace(line,'')
            self.assertFalse(self.evaluate(p)['licensed'])

    def test_old_certificate_rejected_after_source_withdrawal(self):
        p=request();r=self.evaluate(p)
        self.assertTrue(r['licensed'])
        with tempfile.TemporaryDirectory() as td:
            paths=[Path(td)/n for n in ['s','q','c','f','t']]
            values=[LEDGER.replace('جفاف1 دليل_سببي حدث1.\n',''),'هل حدث1 وقوع شجرة1؟\n',
                    pilot.wire(r['kernel_certificate']),pilot.wire(p['frame']),TARGET]
            for path,value in zip(paths,values):path.write_text(value)
            run=subprocess.run([str(NATIVE),'relational',*map(str,paths),p['source_id'],p['revision'],p['scope']],capture_output=True)
            self.assertNotEqual(run.returncode,0)
            self.assertEqual(json.loads(run.stdout)['error'],'CERTIFICATE_REJECTED')

    def test_cyclic_rules_without_a_seed_do_not_supply_cause(self):
        p=request();p['source_text']=LEDGER.replace('جفاف1 دليل_سببي حدث1.\n','')
        p['source_text']+='إذا سند1 هو صالح فإن جفاف1 دليل_سببي حدث1.\nإذا جفاف1 دليل_سببي حدث1 فإن سند1 هو صالح.\n'
        self.assertFalse(self.evaluate(p)['licensed'])

    def test_forged_closure_cannot_supply_missing_cause(self):
        p=request();p['source_text']=LEDGER.replace('جفاف1 دليل_سببي حدث1.\n','')
        c=pilot.propose_certificate(p['source_text'].encode(),'هل حدث1 وقوع شجرة1؟\n'.encode(),
                                    p['source_id'],p['revision'],p['scope'])
        forged={'predicate':'دليل_سببي','arguments':['جفاف1','حدث1'],'positive':True}
        c['known'].append(forged);c['clean_known'].append(forged)
        with tempfile.TemporaryDirectory() as td:
            paths=[Path(td)/n for n in ['s','q','c','f','t']]
            values=[p['source_text'],'هل حدث1 وقوع شجرة1؟\n',pilot.wire(c),pilot.wire(p['frame']),TARGET]
            for path,value in zip(paths,values):path.write_text(value)
            run=subprocess.run([str(NATIVE),'relational',*map(str,paths),p['source_id'],p['revision'],p['scope']],capture_output=True)
            self.assertNotEqual(run.returncode,0)
            self.assertEqual(json.loads(run.stdout)['error'],'CERTIFICATE_REJECTED')

    def test_no_native_checker_fails_closed(self):
        from unittest.mock import patch
        with patch.object(pilot,'file_sha',side_effect=FileNotFoundError):r=self.evaluate()
        self.assertFalse(r['licensed']);self.assertEqual(r['status'],'VERIFICATION_UNAVAILABLE')


class GatewayRelationalBridge(unittest.TestCase):
    def test_rag_preserves_reading_contrasts_and_exposes_withdrawal_contract(self):
        from tools.grammar_catalog import relational
        for surface,expected in [('كَبِرَ',['growth_age']),('كَبُرَ',['growth_magnitude']),
                                 ('كبر',['growth_age','growth_magnitude']),('مُصْفَرّ',['yellowing_participle'])]:
            rows=relational.search(surface)['lexical_review_matches']
            self.assertEqual([r['reading']['id'] for r in rows],expected)
        cards={r['id']:r for r in relational.catalog()['cards']}
        self.assertIn('bridge:withdrawal',cards)
        from tools.grammar_catalog.gateway_links import build
        links=build('relations.analyze')
        self.assertIn('Nabt.RelationalBridge.check_exact',{r['name'] for r in links['declarations']})
        self.assertIn('tests/test_relational_bridge.py',{r['path'] for r in links['tests']})

    def test_bridge_is_reachable_only_through_existing_route_and_replayed(self):
        if not NATIVE.is_file():self.skipTest('Build verifiedReading')
        from tools.grammar_catalog import gateway
        p={'schema':gateway.REQUEST_SCHEMA,'route':'relations.analyze','payload':{'text':TARGET,'bridge':request()}}
        r=gateway.run(p)
        self.assertEqual(r['status'],'EXECUTED',r)
        self.assertTrue(r['execution']['owner_result']['ontology_bridge']['licensed'])
        self.assertTrue(gateway.accept_output(r,expected_request=p)['valid'])
        r['execution']['owner_result']['ontology_bridge']['frame']['cause']='invented'
        self.assertFalse(gateway.accept_output(r,expected_request=p)['valid'])
