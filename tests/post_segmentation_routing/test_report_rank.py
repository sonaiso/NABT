from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from unittest import TestCase

from tools.grammar_catalog import ayat_al_dayn, gateway, report_rank, valency


class ScopedRanks(TestCase):
    def setUp(self):
        fixture = Path(__file__).resolve().parents[2] / 'examples/io_gateway/report_rank.json'
        self.request = json.loads(fixture.read_bytes())
        self.payload = self.request['payload']
        self.text = self.payload['text']
        self.model = self.payload['report_model']

    def read(self, text=None):
        text = text or self.text
        digest = sha256(text.encode()).hexdigest()
        return report_rank.assess(valency.analyze(text), self.model, self.payload['source_id'], digest)

    def test_withdrawing_actor_and_time_individually(self):
        actor, time = self.model['witnesses']
        for cuts, whole, who, when in [
                ([actor, time], [1, 1], [1, 1], [1, 1]),
                ([actor], [3, 5], [1, 1], [3, 5]),
                ([time], [3, 4], [3, 4], [1, 1]),
                ([], [3, 8], [5, 8], [1, 2])]:
            with self.subTest(cards=cuts):
                self.model['witnesses'] = cuts
                out = self.read()
                self.assertEqual(out['report']['fraction'], whole)
                self.assertEqual(out['roles']['opener']['fraction'], who)
                self.assertEqual(out['roles']['time']['fraction'], when)
                self.assertEqual(out['roles']['opened_entity']['fraction'], [1, 1])
                self.assertEqual(out['empirical_cause'], 'UNASSESSED')
        self.assertEqual(out['report']['rank'], 'DISFAVORED')
        self.assertEqual(out['roles']['time']['rank'], 'BALANCED')

    def test_conflict_and_refutation_have_different_denominators(self):
        original = self.model['witnesses'][0]
        opposite = {**original, 'id': 'other-actor', 'value': 'العامل'}
        self.model['witnesses'] = [opposite]
        self.assertEqual(self.read()['report']['rank'], 'REFUTED_IN_CONDITIONED_SCENE')
        self.model['witnesses'].append(original)
        out = self.read()
        self.assertEqual(out['status'], 'NO_COMPATIBLE_ALTERNATIVE')
        self.assertIsNone(out['report']['fraction'])
        self.assertEqual(out['report']['rank'], 'UNASSESSED')

    def test_scope_identity_and_duplicate_sources(self):
        original = self.read()
        actor, time = self.model['witnesses']
        self.model['witnesses'] += [{**actor, 'id': 'copy'}, {**time, 'id': 'tomorrow', 'event': 'other', 'value': 'مساء'}]
        out = self.read()
        self.assertEqual(out['report'], original['report'])
        self.assertEqual(out['out_of_scope_witnesses'], ['tomorrow'])
        for field in ('source_id', 'source_sha256'):
            with self.subTest(field=field):
                valid = self.model[field]
                self.model[field] = 'different'
                with self.assertRaises(ValueError):
                    self.read()
                self.model[field] = valid

    def test_empty_and_unenumerated_and_unsupported(self):
        self.model['witnesses'] = []
        self.model['worlds'] = self.model['worlds'][1:]
        self.assertEqual(self.read()['report']['rank'], 'ABSENT_FROM_ENUMERATED_MODEL')
        self.model['worlds'] = []
        self.assertEqual(self.read()['status'], 'NO_ALTERNATIVES_SUPPLIED')
        text = 'اكتب الدين.'
        self.model['source_sha256'] = sha256(text.encode()).hexdigest()
        self.assertEqual(self.read(text)['status'], 'OUTSIDE_OPENING_REPORT_PROFILE')

    def test_alternatives_preserve_unknowns_and_mass_type(self):
        world = self.model['worlds'][0]
        for change in [{'id': 'copy'}, {'id': 'blank', 'text': 'فَتَحَ الْحَارِسُ الْبَابَ.'},
                       {'id': 'boolean', 'mass': True}]:
            self.model['worlds'].append({**world, **change})
            with self.assertRaises(ValueError):
                self.read()
            self.model['worlds'].pop()

    def test_human_model_and_request_are_independently_retractable(self):
        text = ayat_al_dayn.source()
        def states(**args):
            report = ayat_al_dayn.analyze(text, **args)
            return {c['id'][4:]: c['state'] for c in report['cognition']['claims']}
        a = states(withdraw_context=['cognitive_faculty'])
        self.assertEqual({k for k,v in a.items() if v=='WITHDRAWN'}, {'sharing','understanding'})
        a = states(withdraw_context=['species_instinct','religious_instinct'])
        self.assertEqual({k for k,v in a.items() if v=='WITHDRAWN'}, {'reproduction','sanctification'})
        b = states(withdraw=[11])
        self.assertEqual(b['if_then'], 'WITHDRAWN')
        self.assertEqual(b['understanding'], 'SUPPORTED_IN_SCOPE')

    def test_impossibility_requires_rule_and_scoped_membership(self):
        base = {'event': 'opening-1', 'axis': 'disposition', 'type': 'مثبت الإغلاق طوال التجربة'}
        law = {**base, 'id': 'law-1', 'role': 'opened_entity', 'source': 'قيد التجربة'}
        card = {**base, 'id': 'lab-card', 'entity': 'الباب', 'positive': True, 'source': 'سجل تجهيز الباب'}
        contract = self.model['compatibility'] = {'exclusions': [law], 'memberships': [card]}
        out = self.read()
        self.assertEqual(out['report']['rank'], 'IMPOSSIBLE_UNDER_SUPPLIED_RULE')
        self.assertEqual(out['report']['blockers'][0]['supports'], ['lab-card'])
        self.assertIsNone(out['report']['fraction'])
        self.assertEqual(out['external_truth'], 'UNASSESSED')
        contract['memberships'].append({**card, 'id': 'second-card', 'positive': False})
        self.assertEqual(self.read()['report']['rank'], 'CONFLICTING_MEMBERSHIP')
        contract['memberships'] = [{**card, 'event': 'previous-opening'}]
        self.assertEqual(self.read()['report']['rank'], 'CERTAIN_IN_CONDITIONED_SCENE')
        contract['memberships'] = [card]
        contract['exclusions'] = []
        self.assertEqual(self.read()['report']['rank'], 'CERTAIN_IN_CONDITIONED_SCENE')

    def test_attribution_changes_rank_only_with_matched_prior_evidence(self):
        self.model['witnesses'] = []
        def audit(event, speaker, said, outcome):
            return {'event': event, 'source': 'دفتر التجربة', 'speaker': speaker, 'setting': 'الغرفة',
                    'masdar': 'فتح', 'reported': said, 'observed': outcome}
        first, second = self.model['speaker'], 'راو آخر'
        history = [audit(str(i), speaker, said, outcome)
                   for speaker in (first, second) for i, outcome in enumerate((True, True, False, False))
                   for said in [outcome if speaker == first else not outcome]]
        self.model['speaker_history'] = {'setting': 'الغرفة', 'audits': history}
        out = self.read()
        self.assertEqual(out['report']['fraction'], [9, 14])
        self.assertEqual(out['roles']['opener']['fraction'], [11, 14])
        history.extend([dict(history[0]), audit('opening-1', first, False, False),
                        {**history[0], 'setting': 'معمل آخر', 'reported': False}])
        self.assertEqual(self.read()['report'], out['report'])
        self.model['speaker'] = second
        self.assertEqual(self.read()['report']['fraction'], [1, 6])
        self.model['speaker'] = 'بلا سجل'
        self.assertEqual(self.read()['report']['fraction'], [3, 8])
        self.model['speaker'] = first
        history.append(audit('0', first, False, True))
        self.assertEqual(self.read()['speaker_calibration']['status'], 'CONFLICTING_HISTORY_UNUSED')
        self.assertEqual(self.read()['report']['fraction'], [3, 8])

    def test_normal_gateway_and_tamper(self):
        receipt = gateway.run(self.request)
        self.assertTrue(gateway.accept_output(receipt, expected_request=self.request)['valid'])
        self.assertEqual(receipt['execution']['owner_result']['report_assessment']['report']['rank'],
                         'CERTAIN_IN_CONDITIONED_SCENE')
        forged = deepcopy(receipt)
        forged['execution']['owner_result']['report_assessment']['external_truth'] = 'CERTAIN'
        self.assertFalse(gateway.accept_output(forged, expected_request=self.request)['valid'])
