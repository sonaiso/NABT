"""Source-scoped NTL observations and independent public NTP replay."""
from copy import deepcopy
from hashlib import sha256
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway, gateway_routes, ntp
from tools.lexical_training import (context_transfer, ifadah_programs,
    ntl_core, ntl_witness_pilot, school_apprentice, teaching)
from tools.lexical_training import ntp_recursive as recursive
from tools.lexical_training import ntp_ifadah
from tools.evidence_lifecycle_v1 import ResourceLimit
from nabt import machine
from nabt.errors import resource_limit


def request(lesson):
    return ntp.request('cognitive.lesson', {'lesson': lesson})


def resolve(value, pointer):
    for part in pointer.strip('/').split('/'):
        value = value[int(part)] if type(value) is list else value[part]
    return value


def context_lesson(probes=None):
    return {'schema': context_transfer.SCHEMA, 'term': 'بحر', 'examples': [],
            'probes': probes or ['هذا بَحْرٌ في العلم.', 'ذلك بَحْرٌ تتلاطم أمواجه.']}


def reflection_lesson():
    return {'schema': school_apprentice.SCHEMA, 'action': 'inquire',
            'context': {'role': 'student', 'programme': 'MYP', 'profile_id': 'ib.myp.2026',
                'assessment_session': None, 'programme_year': 3, 'national_grade': 8,
                'national_subject': 'science', 'subject_group': 'sciences',
                'outcome_ids': ['jordan.general.inquiry_problem_solving'],
                'tok_lens': {'aok': 'natural_sciences', 'focus': 'methods_and_tools'}},
            'problem': {'case_id': 'reflection-case', 'revision': 0, 'unit': 'reflection',
                'text': 'ما الذي يسند الحكم؟', 'response': None,
                'task': {'question': 'كيف نفحص الشاهد؟',
                    'sources': [{'id': 'first-source', 'text': 'كَتَبَ', 'citation': 'retained-one'},
                                {'id': 'second-source', 'text': 'كَتَبَ', 'citation': 'retained-two'}],
                    'perspectives': ['يحتاج الخبر إلى شاهد مستقل.', 'يجب فحص مجال تطبيقه.']}}}


class LessonSourceContracts(unittest.TestCase):
    def assert_trace(self, req, trace):
        text = resolve(req, trace['request_path'])
        raw = text.encode('utf-8')
        self.assertEqual(trace['source_sha256'], sha256(raw).hexdigest())
        self.assertEqual(trace['source_byte_length'], len(raw))
        self.assertEqual(trace['source_encoding'], 'UTF8_TEXT')
        for row in trace['observations']:
            occurrence = row['occurrence']
            a, b = occurrence['utf8_span']
            self.assertEqual(raw[a:b].decode('utf-8'), occurrence['surface'])
            a, b = occurrence['codepoint_span']
            self.assertEqual(text[a:b], occurrence['surface'])

    def test_witness_source_is_observed_without_changing_unbound_owner(self):
        lesson = {'schema': ntl_witness_pilot.SCHEMA, 'source_id': 'original-source', 'text': 'كَتَبَ'}
        req = request(lesson)
        expected = teaching.run_lesson(lesson)
        result = ntp.execute('ntp', req['payload'])
        self.assertEqual(expected['status'], 'UNBOUND_READING')
        self.assertEqual(result['owner_result'], expected)
        self.assertEqual(result['observation_request_path'], '/payload/input/lesson/text')
        self.assertEqual(result['observation_source_id'], 'original-source')
        self.assertEqual(result['observation_source_sha256'], sha256(lesson['text'].encode()).hexdigest())
        self.assertEqual(result['observation_coverage'], 'COMPLETE_SOURCE_TERMS')
        self.assertEqual(result['recursive_observations'][0]['observation']['cells'], [84, 8, 4])
        with patch.object(recursive, 'load', side_effect=OSError('withheld model')):
            absent = ntp.execute('ntp', req['payload'])
        self.assertEqual(absent['owner_result'], expected)
        self.assertEqual(absent['recursive_observations'][0]['observation']['status'], 'MODEL_UNAVAILABLE')
        self.assertIs(absent['neural_selection_permitted'], False)

    def test_context_sources_keep_each_request_path_and_local_occurrence(self):
        lesson = context_lesson()
        req = request(lesson)
        result = ntp.execute('ntp', req['payload'])
        self.assertEqual(result['owner_result'], context_transfer.run(lesson))
        self.assertEqual(result['recursive_observations'], [])
        self.assertEqual(result['observation_coverage'], 'COMPLETE_SOURCE_TRACES')
        self.assertEqual([t['request_path'] for t in result['source_traces']],
                         ['/payload/input/lesson/probes/0', '/payload/input/lesson/probes/1'])
        for trace in result['source_traces']:
            self.assert_trace(req, trace)
            self.assertEqual(trace['role'], 'PROBE')
            self.assertIsNone(trace['source_id'])
        self.assertIs(result['owner_result']['semantic_license'], False)

    def test_optional_observer_failure_does_not_erase_original_lesson(self):
        lesson = {'schema': ifadah_programs.SCHEMA, 'mode': 'understand',
                  'source_id': 'source', 'text': 'هَلْ الْكَاتِبُ حَاضِرٌ؟'}
        req = request(lesson)
        expected = teaching.run_lesson(lesson)
        with patch.object(recursive, 'Machine', side_effect=FileNotFoundError('effect checker unavailable')):
            unavailable = ntp.execute('ntp', req['payload'])
        self.assertEqual(unavailable['owner_result'], expected)
        self.assertEqual(unavailable['recursive_observations'][0]['observation']['status'],
                         'NEURAL_OBSERVER_UNAVAILABLE')
        with patch.object(recursive, 'forward', side_effect=ResourceLimit('observer budget')):
            limited = ntp.execute('ntp', req['payload'])
        self.assertEqual(limited['owner_result'], expected)
        self.assertEqual(limited['recursive_observations'][0]['observation']['status'], 'NEURAL_RESOURCE_LIMIT')
        self.assertEqual(limited['recursive_observations'][0]['observation']['authority'], 'NONE')
        with patch.object(recursive, 'forward', side_effect=resource_limit('effect budget')):
            structured = ntp.execute('ntp', req['payload'])
        failure = structured['recursive_observations'][0]['observation']
        self.assertEqual(failure['status'], 'NEURAL_RESOURCE_LIMIT')
        self.assertEqual(failure['input_error']['code'], 'RESOURCE_LIMIT')
        self.assertEqual(structured['owner_result'], expected)

    def test_recursive_source_budget_preserves_valid_original_witness_lesson(self):
        lesson = {'schema': ntl_witness_pilot.SCHEMA, 'source_id': 'long-source',
                  'text': 'كَ' * 65}
        expected = teaching.run_lesson(lesson)
        result = ntp.execute('ntp', request(lesson)['payload'])
        self.assertEqual(expected['status'], 'UNBOUND_READING')
        self.assertEqual(result['owner_result'], expected)
        self.assertEqual(result['observation_coverage'], 'COMPLETE_SOURCE_TERMS')
        self.assertEqual(result['recursive_observations'][0]['occurrence']['surface'], lesson['text'])
        observation = result['recursive_observations'][0]['observation']
        self.assertEqual(observation['status'], 'NEURAL_RESOURCE_LIMIT')
        self.assertEqual(observation['input_error']['code'], 'RESOURCE_LIMIT')
        self.assertEqual(observation['authority'], 'NONE')

    def test_installed_law_failures_are_observer_unavailability_not_reading_rejection(self):
        lesson = {'schema': ntl_witness_pilot.SCHEMA, 'source_id': 'source', 'text': 'كَتَبَ'}
        expected = teaching.run_lesson(lesson)
        load_table = machine._load_table.__wrapped__
        cases = (('LAW_TABLE_UNAVAILABLE', None),
                 ('LAW_TABLE_INTEGRITY', b'changed installed table'),
                 ('LAW_TABLE_SCHEMA', b'{}'))
        for code, raw in cases:
            with self.subTest(code=code):
                pinned = sha256(raw).hexdigest() if code == 'LAW_TABLE_SCHEMA' else machine.EXPECTED_TABLE_SHA256
                with patch.object(machine, '_load_table', side_effect=load_table), \
                     patch.object(machine, 'EXPECTED_TABLE_SHA256', pinned), \
                     patch.object(machine, 'files') as files:
                    read = files.return_value.joinpath.return_value.read_bytes
                    if raw is None:
                        read.side_effect = FileNotFoundError('withheld installed law table')
                    else:
                        read.return_value = raw
                    result = ntp.execute('ntp', request(lesson)['payload'])
                self.assertEqual(result['owner_result'], expected)
                observation = result['recursive_observations'][0]['observation']
                self.assertEqual(observation['status'], 'NEURAL_OBSERVER_UNAVAILABLE')
                self.assertEqual(observation['input_error']['code'], code)
                self.assertEqual(observation['authority'], 'NONE')
                self.assertNotIn('law', observation)
                self.assertFalse(result['neural_selection_permitted'])

    def test_unimplemented_adapter_does_not_validate_or_observe_retained_payload(self):
        text_like = {
            'source_learning': {'sources': [{'id': 'unvalidated', 'text': 'كَتَبَ'}]},
            'qualified_inference': {'source_id': 'unvalidated', 'source_text': 'كَتَبَ'}}
        for adapter, payload in text_like.items():
            for supplied in ({}, payload):
                with self.subTest(adapter=adapter, payload=supplied):
                    lesson = {'schema': teaching.SCHEMA, 'lesson_id': 'uninstalled-adapter',
                              'domain_id': 'communication', 'matrix_id': 'restricted',
                              'adapter': adapter, 'payload': supplied}
                    expected = teaching.run_lesson(lesson)
                    self.assertEqual(expected['status'], 'DEFER')
                    self.assertFalse(expected['execution_measured'])
                    self.assertIsNone(expected['owner_result'])
                    self.assertEqual(expected['next_step']['action'], 'IMPLEMENT_ACQUISITION_CONTRACT')
                    with patch.object(recursive, 'forward', side_effect=AssertionError('unvalidated source')) as observer:
                        result = ntp.execute('ntp', request(lesson)['payload'])
                    observer.assert_not_called()
                    self.assertEqual(result['owner_result'], expected)
                    self.assertEqual(result['observation_coverage'], 'OWNER_INPUT_NOT_VALIDATED')
                    self.assertEqual(result['recursive_observations'], [])
                    self.assertEqual(result['observation_limits']['source_count'], 0)
                    self.assertNotIn('source_traces', result)

    def test_validated_unmeasured_adapters_keep_their_submitted_sources(self):
        from tests.test_cognitive_teaching import lesson as source_lesson, qualified
        pilot = teaching.source_learning_connection.pilot
        for lesson in (source_lesson(), qualified()):
            with self.subTest(adapter=lesson['adapter']):
                with patch.object(pilot, 'checker_path', side_effect=pilot.PilotError(
                        'CHECKER_UNAVAILABLE', 'withheld native checker')):
                    expected = teaching.run_lesson(lesson)
                    result = ntp.execute('ntp', request(lesson)['payload'])
                self.assertEqual(expected['status'], 'VERIFICATION_UNAVAILABLE')
                self.assertFalse(expected['execution_measured'])
                self.assertIsInstance(expected['owner_result'], dict)
                self.assertEqual(result['owner_result'], expected)
                self.assertGreater(result['observation_limits']['observed_terms'], 0)
                if lesson['adapter'] == 'source_learning':
                    self.assertEqual(result['observation_coverage'], 'COMPLETE_SOURCE_TRACES')
                    for trace in result['source_traces']:
                        self.assert_trace(request(lesson), trace)
                    self.assertEqual([trace['source_id'] for trace in result['source_traces']],
                                     [source['id'] for source in lesson['payload']['sources']])
                else:
                    self.assertEqual(result['observation_coverage'], 'COMPLETE_SOURCE_TERMS')
                    self.assertEqual(result['observation_request_path'], '/payload/input/lesson/payload/source_text')
                    self.assertEqual(result['observation_source_id'], lesson['payload']['source_id'])
                    self.assertEqual(result['observation_source_sha256'],
                                     sha256(lesson['payload']['source_text'].encode()).hexdigest())

    def test_equal_school_texts_keep_distinct_source_ids_and_revision_paths(self):
        lesson = reflection_lesson()
        req = request(lesson)
        result = ntp.execute('ntp', req['payload'])
        self.assertEqual(result['owner_result'], school_apprentice.run(lesson))
        sources = [t for t in result['source_traces'] if t['source_id'] is not None]
        self.assertEqual([t['source_id'] for t in sources], ['first-source', 'second-source'])
        self.assertEqual(sources[0]['source_sha256'], sources[1]['source_sha256'])
        self.assertNotEqual(sources[0]['request_path'], sources[1]['request_path'])
        for trace in result['source_traces']:
            self.assert_trace(req, trace)
        lesson['action'] = 'revise'
        lesson['previous'] = deepcopy(lesson['problem'])
        lesson['problem']['revision'] = 1
        lesson['problem']['task']['sources'][0]['text'] = 'كُتِبَ'
        revised = ntp.execute('ntp', request(lesson)['payload'])
        by_path = {t['request_path']: t for t in revised['source_traces']}
        current = by_path['/payload/input/lesson/problem/task/sources/0/text']
        previous = by_path['/payload/input/lesson/previous/task/sources/0/text']
        self.assertEqual(current['source_id'], previous['source_id'])
        self.assertNotEqual(current['source_sha256'], previous['source_sha256'])
        self.assertEqual(revised['owner_result'], school_apprentice.run(lesson))

    def test_submitted_core_text_is_not_lost_and_numeric_tasks_are_not_text(self):
        lesson = {'schema': ntl_core.SCHEMA, 'action': 'teach', 'unit': 'formal',
                  'task': {'text': '2+2'}}
        result = ntp.execute('ntp', request(lesson)['payload'])
        self.assertEqual(result['owner_result'], teaching.run_lesson(lesson))
        self.assertEqual(result['observation_request_path'], '/payload/input/lesson/task/text')
        self.assertEqual([x['occurrence']['surface'] for x in result['recursive_observations']], ['2', '2'])
        self.assertTrue(all(x['observation']['status'] == 'DEFER_EXACT_A116_READING'
                            for x in result['recursive_observations']))
        lesson = {'schema': school_apprentice.SCHEMA, 'action': 'catalog'}
        result = ntp.execute('ntp', request(lesson)['payload'])
        self.assertEqual(result['owner_result']['status'], 'CATALOG')
        self.assertEqual(result['observation_coverage'], 'NO_REQUEST_TEXT_SOURCE')
        self.assertEqual(result['recursive_observations'], [])

    def test_optional_observation_budget_preserves_every_original_source(self):
        probes = [('كَتَبَ ' * 20) + str(i) for i in range(12)]
        lesson = context_lesson(probes)
        req = request(lesson)
        result = ntp.execute('ntp', req['payload'])
        self.assertEqual(result['owner_result'], context_transfer.run(lesson))
        self.assertEqual(req['payload']['input']['lesson']['probes'], probes)
        self.assertEqual(len(result['source_traces']), 12)
        self.assertEqual(sum(len(t['observations']) for t in result['source_traces']), 128)
        self.assertEqual(result['observation_coverage'], 'PARTIAL_SOURCE_TRACES')
        self.assertTrue(all(t['coverage'] == 'NEURAL_BUDGET_DEFER'
                            for t in result['source_traces'][8:]))
        for trace in result['source_traces']:
            self.assert_trace(req, trace)
        self.assertFalse(result['neural_selection_permitted'])

    def test_unknown_and_invalid_lessons_cannot_acquire_observation_authority(self):
        bad_lessons = [None, {'schema': []}, {'schema': 'caller-chosen', 'text': 'كَتَبَ'},
            {'schema': ntl_witness_pilot.SCHEMA, 'source_id': 's', 'text': 'كَتَبَ', 'approved': True},
            {'schema': ifadah_programs.SCHEMA, 'mode': 'understand', 'source_id': 's', 'text': 3}]
        for lesson in bad_lessons:
            with self.subTest(lesson=lesson):
                result = ntp.execute('ntp', request(lesson)['payload'])
                self.assertEqual(result['owner_result']['status'], 'INVALID_INPUT')
                self.assertEqual(result['owner_result'], teaching.run_lesson(lesson))
                self.assertEqual(result['recursive_observations'], [])
                self.assertNotIn('source_traces', result)
                self.assertNotIn('program_choice_observation', result)
                self.assertIs(result['neural_selection_permitted'], False)

    def test_owner_resource_failure_remains_distinct_from_invalid_source(self):
        lesson = reflection_lesson()
        lesson['padding'] = 'x' * 100000
        result = ntp.execute('ntp', request(lesson)['payload'])
        self.assertEqual(result['owner_result']['status'], 'RESOURCE_LIMIT')
        self.assertEqual(result['observation_coverage'], 'OWNER_RESOURCE_LIMIT')
        self.assertEqual(result['recursive_observations'], [])
        self.assertNotIn('source_traces', result)

    def test_bit_frame_observation_points_to_actual_request_field(self):
        packed = recursive.pack_cells((84, 8, 4)).hex()
        req = ntp.request('think', {'packed_hex': packed})
        preserved = {'status': 'DEFER', 'pending': ['original lexical witness']}
        with patch.object(gateway_routes, '_execute_owner', return_value=preserved):
            result = ntp.execute('ntp', req['payload'])
        self.assertEqual(resolve(req, result['observation_request_path']), packed)
        self.assertEqual(result['observation_source_encoding'], 'A116_BIT_FRAME')
        self.assertEqual(result['observation_source_sha256'], sha256('كَتَبَ'.encode()).hexdigest())
        self.assertEqual(result['owner_result'], preserved)


class PublicSourceReplay(unittest.TestCase):
    def test_witness_gateway_replays_source_identity_and_rejects_changed_source(self):
        lesson = {'schema': ntl_witness_pilot.SCHEMA, 'source_id': 'source-one', 'text': 'كَتَبَ'}
        req = request(lesson)
        receipt = gateway.run(req)
        self.assertEqual(receipt['status'], 'EXECUTED', receipt)
        accepted = gateway.accept_output(receipt, expected_request=req)
        self.assertTrue(accepted['valid'], accepted)
        forged = deepcopy(receipt)
        forged['execution']['owner_result']['observation_source_id'] = 'other-source'
        self.assertFalse(gateway.accept_output(forged, expected_request=req)['valid'])
        changed = deepcopy(req)
        changed['payload']['input']['lesson']['text'] = 'كُتِبَ'
        self.assertFalse(gateway.accept_output(receipt, expected_request=changed)['valid'])

    def test_multisource_gateway_rejects_swapped_source_paths(self):
        req = request(context_lesson())
        receipt = gateway.run(req)
        self.assertEqual(receipt['status'], 'EXECUTED', receipt)
        accepted = gateway.accept_output(receipt, expected_request=req)
        self.assertTrue(accepted['valid'], accepted)
        forged = deepcopy(receipt)
        traces = forged['execution']['owner_result']['source_traces']
        traces[0]['request_path'], traces[1]['request_path'] = traces[1]['request_path'], traces[0]['request_path']
        self.assertEqual(forged['execution']['owner_result']['owner_result'],
                         receipt['execution']['owner_result']['owner_result'])
        self.assertFalse(gateway.accept_output(forged, expected_request=req)['valid'])

    def test_program_observation_requires_fresh_source_bound_replay(self):
        req = request({'schema': ifadah_programs.SCHEMA, 'mode': 'understand',
                       'source_id': 'program-source', 'text': 'هَلْ لَيْسَ الْكَاتِبُ حَاضِرًا؟'})
        receipt = gateway.run(req)
        self.assertEqual(receipt['status'], 'EXECUTED', receipt)
        accepted = gateway.accept_output(receipt, expected_request=req)
        self.assertTrue(accepted['valid'], accepted)
        result = receipt['execution']['owner_result']
        observation = result['program_choice_observation']['observation']
        self.assertEqual(observation['source_id'], 'program-source')
        self.assertFalse(result['neural_selection_permitted'])
        self.assertEqual(result['owner_result']['accepted_program'], {
            'op': 'ask', 'body': {'op': 'negation', 'body': {
                'op': 'predication', 'subject': 0, 'predicate': 0}}})
        self.assertEqual(observation['status'], 'PROPOSED')
        self.assertEqual([item['name'] for item in observation['observations'][0]['scores']],
                         ['negation', 'wish', 'ask', 'ask_negation'])
        forged = deepcopy(receipt)
        changed = forged['execution']['owner_result']['program_choice_observation']['observation']
        changed['observations'][0]['operator_occurrences'][0]['utf8_span'] = [0, 2]
        self.assertEqual(forged['execution']['owner_result']['owner_result'], result['owner_result'])
        self.assertFalse(gateway.accept_output(forged, expected_request=req)['valid'])


class ConditionalProgramObservations(unittest.TestCase):
    def test_understanding_observes_original_operators_without_gold_inputs(self):
        source = 'هَلْ لَيْسَ الْكَاتِبُ حَاضِرًا؟'
        lesson = {'schema': ifadah_programs.SCHEMA, 'mode': 'understand',
                  'source_id': 'operator-source', 'text': source}
        expected = teaching.run_lesson(lesson)
        with patch.object(ntp_ifadah, 'observe', wraps=ntp_ifadah.observe) as observer:
            result = ntp.execute('ntp', request(lesson)['payload'])
        observer.assert_called_once_with(source, 'operator-source')
        self.assertEqual(result['owner_result'], expected)
        trace = result['program_choice_observation']
        self.assertEqual(trace['source_kind'], 'ORIGINAL_REQUEST')
        self.assertEqual(trace['source_path'], '/payload/input/lesson/text')
        observation = trace['observation']
        self.assertEqual(observation['source_id'], 'operator-source')
        self.assertEqual(observation['source_sha256'], sha256(source.encode()).hexdigest())
        self.assertEqual(observation['candidate_domain'], ['negation', 'wish', 'ask', 'ask_negation'])
        self.assertEqual(observation['authority'], 'NONE')
        self.assertEqual(observation['release_policy'], 'REVIEW_ONLY')
        self.assertFalse(observation['neural_selection_permitted'])
        self.assertNotIn('accepted_program', observation)
        occurrences = observation['observations'][0]['operator_occurrences']
        self.assertEqual([item['surface'] for item in occurrences], ['هَلْ', 'لَيْسَ'])
        for item in occurrences:
            start, end = item['utf8_span']
            self.assertEqual(source.encode()[start:end].decode(), item['surface'])
            self.assertEqual(item['status'], 'EXACT_A116')
        self.assertFalse(observation['subject_predicate_binding_learned'])
        self.assertFalse(observation['instruction_intent_learned'])

    def test_production_observes_generated_source_and_keeps_instruction_separate(self):
        source_id = 's' * 128
        realized_source_id = source_id + ':realization'
        lesson = {'schema': ifadah_programs.SCHEMA, 'mode': 'produce', 'source_id': source_id,
                  'instruction': 'اسأل عن ثبوت الصفة الآن', 'subject': 0, 'predicate': 0}
        expected = teaching.run_lesson(lesson)
        with patch.object(ntp_ifadah, 'observe', wraps=ntp_ifadah.observe) as observer:
            result = ntp.execute('ntp', request(lesson)['payload'])
        observer.assert_called_once_with(expected['generated_text'], realized_source_id)
        self.assertEqual(result['owner_result'], expected)
        self.assertIsNone(result['owner_result']['accepted_program'])
        self.assertEqual(result['observation_request_path'], '/payload/input/lesson/instruction')
        self.assertTrue(all('owner_witness_paths' not in row for row in result['recursive_observations']))
        trace = result['program_choice_observation']
        self.assertEqual(trace['source_kind'], 'OWNER_REALIZATION')
        self.assertEqual(trace['source_path'], '/owner_result/generated_text')
        observation = trace['observation']
        self.assertEqual(observation['source_id'], realized_source_id)
        self.assertEqual(expected['realization_owner']['readings'][0]['bindings']['subject']['source_id'],
                         realized_source_id)
        self.assertEqual(observation['source_sha256'], sha256(expected['generated_text'].encode()).hexdigest())
        self.assertFalse(observation['instruction_intent_learned'])

    def test_misleading_or_unavailable_program_observation_preserves_original_owner(self):
        lesson = {'schema': ifadah_programs.SCHEMA, 'mode': 'understand',
                  'source_id': 'source', 'text': 'هَلْ الْكَاتِبُ حَاضِرٌ؟'}
        expected = teaching.run_lesson(lesson)
        misleading = {'schema': 'nabt.ntp-ifadah-observation.v1', 'status': 'PROPOSED',
                      'proposed_name': 'wish', 'authority': 'NONE', 'release_policy': 'REVIEW_ONLY',
                      'neural_selection_permitted': False}
        with patch.object(ntp_ifadah, 'observe', return_value=misleading):
            result = ntp.execute('ntp', request(lesson)['payload'])
        self.assertEqual(result['owner_result'], expected)
        self.assertEqual(result['owner_result']['accepted_program']['op'], 'ask')
        self.assertEqual(result['program_choice_observation']['observation'], misleading)
        self.assertFalse(result['neural_selection_permitted'])
        for error, status in ((OSError('withheld'), 'MODEL_UNAVAILABLE'),
                              (ResourceLimit('observer budget'), 'NEURAL_RESOURCE_LIMIT'),
                              (resource_limit('effect budget'), 'NEURAL_RESOURCE_LIMIT')):
            with self.subTest(error=type(error).__name__):
                with patch.object(ntp_ifadah, 'observe', side_effect=error):
                    result = ntp.execute('ntp', request(lesson)['payload'])
                self.assertEqual(result['owner_result'], expected)
                observation = result['program_choice_observation']['observation']
                self.assertEqual(observation['status'], status)
                self.assertEqual(observation['source_id'], lesson['source_id'])
                self.assertEqual(observation['source_sha256'], sha256(lesson['text'].encode()).hexdigest())
                self.assertEqual(observation['authority'], 'NONE')
                self.assertFalse(observation['neural_selection_permitted'])


if __name__ == '__main__':
    unittest.main()
