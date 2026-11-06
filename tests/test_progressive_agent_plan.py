"""Independent organization/transport boundaries, not Arabic completeness gold."""
from copy import deepcopy
from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools.lexical_training import agent_plan as agents
from tools.grammar_catalog.unicode_transport import transcode, verify, ENCODINGS, MAX_BYTES
from tools.evidence_lifecycle_v1 import ResourceLimit

ROOT = Path(__file__).resolve().parents[1]


class ProgressivePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads((ROOT/'evidence/cognitive_curriculum_v1/learning_framework.json').read_text())
        cls.plan = cls.document['neural_design']['progressive_agents']
        cls.report = agents.build_report()

    def validate(self, plan):
        return agents.validate_plan(plan, agents={r['id'] for r in self.document['agents']},
                                    objectives={r['id'] for r in self.document['objectives']})

    def test_all_topics_are_attached_without_claiming_training(self):
        self.assertEqual(self.report['counts']['profiles'], 33)
        self.assertEqual(self.report['counts']['requested_topics'], 113)
        topics = {t['id'] for r in self.report['profiles'] for t in r['topics']}
        self.assertTrue({'utf8','utf16','utf32','root3','root4','makharij','masdar_genus',
            'sound_names','five_nouns','five_verbs','industrial','diptote_after','past_passive',
            'present_passive','nun_emphasis','nun_feminine','question_names','counterfactual',
            'lawla','cause','exception','noun_after','verb_after','scope_after'} <= topics)
        self.assertFalse(any(r['application_license_granted'] for r in self.report['profiles']))
        self.assertEqual(self.report['semantic_authority'], 'NONE')

    def test_pre_propose_compose_post_license_has_no_self_justification(self):
        plan = agents.plan_for('awamil.license')
        order = plan['prerequisite_order']
        for category in ('noun', 'verb', 'connector'):
            self.assertLess(order.index(category+'.pre'),order.index('awamil.propose'))
            self.assertLess(order.index('syntax.compose'),order.index(category+'.post'))
            self.assertLess(order.index(category+'.post'),order.index('awamil.license'))
        self.assertLess(order.index('awamil.propose'),order.index('syntax.compose'))
        for shape in ('CV','CVV','CVC','CVVC','CVCC','CVVCC'):
            self.assertIn('syllable.'+shape,order)
        self.assertEqual(len(order),len(set(order)))
        self.assertNotIn('review',order)
        self.assertLess(order.index('units.compose'),order.index('roles.stem'))
        self.assertLess(order.index('units.compose'),order.index('roles.grammar'))

    def test_cycles_unknown_owners_and_forged_mastery_are_rejected(self):
        mutations = [lambda p: p['profiles'][0]['prerequisites'].append('awamil.license'),
                     lambda p: p['profiles'][0].update(parent_agent_id='imagined'),
                     lambda p: p['profiles'][0].update(phase=[]),
                     lambda p: p['profiles'][0].update(passed=True),
                     lambda p: p['profiles'][0]['objective_ids'].append('unknown'),
                     lambda p: p['topics'][0].update(profile_id='unknown'),
                     lambda p: p['topics'].append(deepcopy(p['topics'][0])),
                     lambda p: p['contract_fields'].remove('premise_receipts')]
        for mutate in mutations:
            p = deepcopy(self.plan); mutate(p)
            with self.assertRaises(ValueError): self.validate(p)

    def test_topic_source_references_are_resolved_and_unattested_topics_remain_open(self):
        p = deepcopy(self.plan);p['topics'][0]['research_ids']=['invented']
        with self.assertRaisesRegex(ValueError,'research'):
            agents.validate_plan(p,agents={r['id'] for r in self.document['agents']},
                objectives={r['id'] for r in self.document['objectives']},research_ids=set())
        sound = next(t for r in self.report['profiles'] for t in r['topics'] if t['id']=='sound_names')
        self.assertEqual(sound['research_records'],[])
        self.assertEqual(sound['coverage_status'],'REQUEST_MAPPED_APPLICATION_UNMEASURED')

    def test_proof_view_is_exactly_from_current_catalog_and_keeps_dependencies(self):
        from tools.entropy_framework.reuse import current_catalog
        catalog, path, _, _ = current_catalog(ROOT)
        result = agents.proofs('a116')
        rows = {r['name']:r for r in catalog['theorems']}
        self.assertEqual(result['catalog']['path'],path)
        self.assertTrue(result['declarations'])
        self.assertFalse(result['catalog']['compiled_this_run'])
        for d in result['declarations']:
            for k in ('statement_sha256','source_sha256','proof_dependencies','type_dependencies','range'):
                self.assertEqual(d[k],rows[d['name']][k])
            self.assertIn('source_statement',d)
        self.assertFalse(result['complete_topic_proof_claimed'])

    def test_search_returns_owner_and_original_source_candidates_without_licensing(self):
        result = agents.search('الجذر الرباعي',limit=8)
        self.assertTrue({'root.quadriliteral','topic:root4'} <= {r['id'] for r in result['candidates']})
        self.assertIn('source_retrieval',result)
        self.assertEqual(result['authority'],'RETRIEVAL_ONLY')
        self.assertFalse(result['source_candidate_is_topic_certificate'])

    def test_source_lacuna_and_representation_domains_remain_visible(self):
        facts = self.report['foundation_facts']
        self.assertEqual(facts['count_domains']['cells'],116)
        self.assertEqual(facts['count_domains']['cv_candidates'],84)
        self.assertEqual(facts['count_domains']['sukun_cells'],29)
        self.assertEqual(set(facts['source_collation_open_carriers']),{'ل','ن'})
        self.assertFalse(facts['acoustic_validation'])
        self.assertEqual(facts['utf_transport_formal_refinement'],'NOT_ESTABLISHED_BY_PYTHON_ROUNDTRIP')


class ProgressiveGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request = json.loads((ROOT/'examples/awamil_agent/nominal.json').read_text())
        cls.receipt = agents.factor_gate(cls.request)

    def test_existing_source_reading_is_retained_without_false_bridge_promotion(self):
        self.assertEqual(self.receipt['source_relative_status'],'LICENSED_DISCOURSE')
        self.assertEqual(self.receipt['progressive_license_status'],'DEFER')
        self.assertFalse(self.receipt['application_license_granted'])
        self.assertEqual(set(self.receipt['missing_obligations']),
            {'sourceLicense','hostInventory','hostLicenses','grammarLicense','realizationAligned'})

    def test_replay_is_bound_to_independent_text_and_rejects_forged_gate(self):
        self.assertTrue(agents.verify_gate(self.receipt,expected_request=self.request)['valid'])
        forged = deepcopy(self.receipt);forged['application_license_granted']=True
        self.assertFalse(agents.verify_gate(forged,expected_request=self.request)['valid'])
        changed = {**self.request,'text':'زيدٌ حكيمًا.'}
        self.assertFalse(agents.verify_gate(self.receipt,expected_request=changed)['valid'])

    def test_training_scores_or_profile_flags_cannot_unlock_execution(self):
        for field in ('passed','mastery','certificate','native_checked'):
            with self.assertRaises(ValueError):
                agents.factor_gate({**self.request,field:True})


class ExplicitUTFTransportTests(unittest.TestCase):
    def test_all_encodings_preserve_scalars_marks_and_exact_byte_spans(self):
        text='\ufeffبَّ قمتُ 🧠'
        for encoding in ENCODINGS:
            raw=text.encode(encoding)
            request={'source_id':'sample','encoding':encoding,'hex':raw.hex()}
            result=transcode(request)
            self.assertEqual(result['origin']['sha256'],sha256(raw).hexdigest())
            self.assertEqual(result['utf8']['text'],text)
            self.assertEqual(bytes.fromhex(result['utf8']['hex']),text.encode())
            self.assertEqual(''.join(r['scalar'] for r in result['scalar_map']),text)
            for row in result['scalar_map']:
                a,b=row['input_byte_span'];c,d=row['utf8_byte_span']
                self.assertEqual(raw[a:b].decode(encoding),row['scalar'])
                self.assertEqual(text.encode()[c:d].decode(),row['scalar'])
            self.assertTrue(verify(result,expected_request=request)['valid'])
            self.assertFalse(result['acoustic_interpretation_established'])
            self.assertFalse(result['a116_license_established'])

    def test_malformed_or_implicit_encoding_is_never_repaired_silently(self):
        for encoding,hex in [('utf-8','c0af'),('utf-16-le','00d8'),('utf-16-le','00'),
                             ('utf-32-le','00001100'),('utf-16','fffe2806'),('cp1256','c8'),
                             ('utf-8','D8A8'),('utf-8','d8 a8')]:
            with self.assertRaises(ValueError):
                transcode({'source_id':'sample','encoding':encoding,'hex':hex})

    def test_equal_text_does_not_erase_original_encoding_and_tampering_fails(self):
        a={'source_id':'sample','encoding':'utf-8','hex':'بَ'.encode().hex()}
        b={'source_id':'sample','encoding':'utf-16-le','hex':'بَ'.encode('utf-16-le').hex()}
        result=transcode(a)
        self.assertEqual(result['utf8']['sha256'],transcode(b)['utf8']['sha256'])
        self.assertNotEqual(result['origin']['sha256'],transcode(b)['origin']['sha256'])
        self.assertFalse(verify(result,expected_request=b)['valid'])
        result['scalar_map'][0]['input_byte_span']=[0,1]
        self.assertFalse(verify(result,expected_request=a)['valid'])

    def test_byte_budgets_remain_resource_limits_through_the_cli(self):
        from tools.grammar_catalog.__main__ import main
        # Independent counterexample: 6,000 valid UTF-16 bytes become 9,000
        # UTF-8 bytes. Exhaustion is distinct from malformed text.
        cases = [('utf-16-le', ('\u0800' * 3000).encode('utf-16-le').hex(), 3, 'RESOURCE_LIMIT'),
                 ('utf-8', (b'a' * (MAX_BYTES + 1)).hex(), 3, 'RESOURCE_LIMIT'),
                 ('utf-8', 'c0af', 2, 'INPUT_OR_SOURCE_ERROR')]
        for encoding, source_hex, code, status in cases:
            request = {'source_id':'budget','encoding':encoding,'hex':source_hex}
            if code == 3:
                with self.assertRaises(ResourceLimit): transcode(request)
            with TemporaryDirectory() as directory:
                path = Path(directory)/'request.json'
                path.write_text(json.dumps(request))
                output = StringIO()
                with patch('sys.argv', ['grammar_catalog','agents','transport','--request',str(path)]), redirect_stdout(output):
                    actual_code = main()
                receipt = json.loads(output.getvalue())
                self.assertEqual(actual_code, code)
                self.assertEqual(receipt['status'], status)
                self.assertFalse(receipt['grants_language_license'])
        at_limit = transcode({'source_id':'budget','encoding':'utf-8','hex':(b'a' * MAX_BYTES).hex()})
        self.assertEqual(len(bytes.fromhex(at_limit['utf8']['hex'])),MAX_BYTES)


if __name__=='__main__': unittest.main()
