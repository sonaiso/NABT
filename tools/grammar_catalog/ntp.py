"""One NTP dispatch under the existing independently replayed I/O gateway.

All legacy adapters enter this dispatcher. Owners keep their exact licenses;
the recursive learner is an observation, never a replacement license.
"""
from copy import deepcopy
from hashlib import sha256


MAX_OBSERVATION_SOURCES = 8
MAX_OBSERVATION_TERMS = 128
MAX_OBSERVATION_SOURCE_BYTES = 8192


def validate(payload):
    from . import gateway_routes as routes
    if type(payload) is not dict or set(payload) != {'operation', 'input'}:
        raise ValueError('NTP requires operation and input only')
    op = payload['operation']
    if type(op) is not str or op == 'ntp':
        raise ValueError('No nested NTP dispatch')
    if op == 'forward' or (op == 'think' and type(payload['input']) is dict and 'packed_hex' in payload['input']):
        from tools.lexical_training.ntp_recursive import source
        source(payload['input'])
    elif op == 'think':
        routes.validate('text.read', payload['input'])
    else:
        routes.validate(op, payload['input'])
    return deepcopy(payload)


def _term_observations(text, *, max_terms=MAX_OBSERVATION_TERMS):
    from .operations import exact_terms
    from tools.lexical_training.ntp_recursive import forward
    from tools.evidence_lifecycle_v1 import ResourceLimit
    from nabt.errors import NabtError

    terms = exact_terms(text)
    observations = []
    for term in terms[:max_terms]:
        try:
            value = forward({'text': term['surface']})
        except (ResourceLimit, MemoryError) as error:
            value = {'status': 'NEURAL_RESOURCE_LIMIT', 'reason': type(error).__name__,
                     'authority': 'NONE'}
        except OSError as error:
            value = {'status': 'NEURAL_OBSERVER_UNAVAILABLE', 'reason': type(error).__name__,
                     'authority': 'NONE'}
        except NabtError as error:
            if error.code == 'RESOURCE_LIMIT':
                status = 'NEURAL_RESOURCE_LIMIT'
            elif error.code in ('LAW_TABLE_UNAVAILABLE', 'LAW_TABLE_INTEGRITY', 'LAW_TABLE_SCHEMA'):
                status = 'NEURAL_OBSERVER_UNAVAILABLE'
            else:
                status = 'DEFER_EXACT_A116_READING'
            value = {'status': status,
                     'reason': str(error), 'input_error': error.as_dict(), 'authority': 'NONE'}
        except ValueError as error:
            value = {'status': 'DEFER_EXACT_A116_READING', 'reason': str(error),
                     'authority': 'NONE'}
        observations.append({'occurrence': term, 'observation': value})
    coverage = ('COMPLETE_SOURCE_TERMS' if len(terms) <= max_terms
                else f'FIRST_{max_terms}_TERMS_ONLY')
    return observations, coverage


def _lesson_sources(lesson, owner):
    """Select only source fields in installed, already validated lesson contracts.

    Labels, answers, identifiers and arbitrary nested strings are not source
    texts. Multiple sources retain separate request locations even when their
    content, source IDs or local occurrence offsets happen to coincide.
    """
    from tools.lexical_training import (context_transfer, corpus_concepts,
        ifadah_programs, ntl_core, ntl_course, ntl_curriculum,
        ntl_witness_pilot, opencyc_inquiry, school_apprentice, teaching)

    runners = (context_transfer, corpus_concepts, ifadah_programs, ntl_core,
               ntl_course, ntl_curriculum, ntl_witness_pilot,
               opencyc_inquiry, school_apprentice)
    schemas = {runner.SCHEMA: runner.RESULT for runner in runners}
    schemas.update({teaching.SCHEMA: teaching.RESULT_SCHEMA,
                    teaching.SCHEMA_V2: 'nabt.cognitive-lesson-result.v2',
                    teaching.SCHEMA_V3: 'nabt.cognitive-lesson-result.v3',
                    teaching.SCHEMA_V4: 'nabt.cognitive-lesson-result.v4'})
    schema = lesson.get('schema') if type(lesson) is dict else None
    if type(schema) is not str or schema not in schemas or owner.get('schema') != schemas[schema]:
        return [], 'UNMAPPED_LESSON_SOURCE_CONTRACT'
    if owner.get('status') in ('INVALID_INPUT', 'RESOURCE_LIMIT'):
        return [], 'OWNER_' + owner['status']
    if (('request' in owner and owner['request'] != lesson)
            or (owner.get('execution_measured') is not True and owner.get('request') != lesson)):
        return [], 'OWNER_INPUT_NOT_VALIDATED'

    sources = []
    prefix = '/payload/input/lesson'

    def add(text, suffix, role='SOURCE', source_id=None):
        if type(text) is str:
            sources.append({'text': text, 'request_path': prefix + suffix,
                            'role': role, 'source_id': source_id})

    if schema == ifadah_programs.SCHEMA:
        field = 'text' if lesson['mode'] == 'understand' else 'instruction'
        add(lesson[field], '/' + field, 'SOURCE' if field == 'text' else 'INSTRUCTION', lesson['source_id'])
    elif schema in (ntl_witness_pilot.SCHEMA, corpus_concepts.SCHEMA, opencyc_inquiry.SCHEMA):
        add(lesson['text'], '/text', source_id=lesson.get('source_id'))
    elif schema == ntl_curriculum.SCHEMA:
        add(lesson['record'], '/record')
    elif schema == ntl_core.SCHEMA:
        task = lesson.get('task', {})
        add(task.get('text'), '/task/text')
        add(task.get('query'), '/task/query', 'QUESTION')
    elif schema == context_transfer.SCHEMA:
        for i, example in enumerate(lesson['examples']):
            add(example['text'], f'/examples/{i}/text', 'DEMONSTRATION')
        for i, text in enumerate(lesson['probes']):
            add(text, f'/probes/{i}', 'PROBE')
        for i, text in enumerate(lesson.get('query_pool', [])):
            add(text, f'/query_pool/{i}', 'QUESTION_CANDIDATE')
    elif schema == school_apprentice.SCHEMA:
        # Current and prior snapshots are independent sources; neither inherits
        # the other's observation spans, evidence support or source identity.
        fields = ('problem', 'previous') if lesson.get('action') == 'revise' else ('problem',)
        for field in fields:
            problem = lesson.get(field)
            if problem is None:
                continue
            base = '/' + field
            add(problem['text'], base + '/text', 'INQUIRY')
            task = problem['task']
            if problem['unit'] == 'passage':
                add(task.get('text'), base + '/task/text')
                add(task.get('query'), base + '/task/query', 'QUESTION')
            elif problem['unit'] == 'reflection':
                add(task.get('question'), base + '/task/question', 'QUESTION')
                for i, source in enumerate(task['sources']):
                    add(source['text'], f'{base}/task/sources/{i}/text', source_id=source['id'])
                for i, text in enumerate(task['perspectives']):
                    add(text, f'{base}/task/perspectives/{i}', 'PERSPECTIVE')
    elif schema != ntl_course.SCHEMA:
        # These are the exact source contracts already used by
        # shared_encoder.observe_lesson/contextual_alignment.observe_lesson.
        # Teaching retains a request before a v1 acquisition-contract DEFER;
        # that early return has not validated its adapter payload. A completed
        # adapter may still be unmeasured when its native checker is unavailable.
        if type(owner.get('owner_result')) is not dict or type(owner.get('measurements')) is not dict:
            return [], 'OWNER_INPUT_NOT_VALIDATED'
        payload = lesson['payload']
        if lesson['adapter'] == 'source_learning':
            for i, source in enumerate(payload['sources']):
                add(source['text'], f'/payload/sources/{i}/text', source_id=source['id'])
        elif lesson['adapter'] == 'qualified_inference':
            add(payload['source_text'], '/payload/source_text', source_id=payload['source_id'])
    return sources, 'NO_REQUEST_TEXT_SOURCE'


def _observe_sources(result, sources, empty_coverage):
    """Bound optional work without truncating or changing the original owner."""
    traces, remaining = [], MAX_OBSERVATION_TERMS
    for index, source in enumerate(sources):
        raw = source['text'].encode('utf-8')
        trace = {key: source[key] for key in ('request_path', 'source_id', 'role')}
        trace.update(source_sha256=sha256(raw).hexdigest(), source_byte_length=len(raw),
                     source_encoding=source.get('source_encoding', 'UTF8_TEXT'),
                     observations=[], coverage='NEURAL_BUDGET_DEFER')
        if (index < MAX_OBSERVATION_SOURCES and remaining > 0
                and len(raw) <= MAX_OBSERVATION_SOURCE_BYTES):
            observations, coverage = _term_observations(source['text'], max_terms=remaining)
            trace.update(observations=observations, coverage=coverage)
            remaining -= len(observations)
        traces.append(trace)
    result['observation_limits'] = {
        'max_sources': MAX_OBSERVATION_SOURCES, 'max_terms': MAX_OBSERVATION_TERMS,
        'max_source_bytes': MAX_OBSERVATION_SOURCE_BYTES, 'source_count': len(sources),
        'observed_terms': MAX_OBSERVATION_TERMS - remaining}
    if not traces:
        result['observation_coverage'] = empty_coverage
    elif len(traces) == 1:
        trace = traces[0]
        result.update(recursive_observations=trace['observations'], observation_coverage=trace['coverage'],
                      observation_request_path=trace['request_path'], observation_source_id=trace['source_id'],
                      observation_source_sha256=trace['source_sha256'], observation_source_role=trace['role'],
                      observation_source_encoding=trace['source_encoding'])
    else:
        result.update(source_traces=traces, observation_coverage=(
            'COMPLETE_SOURCE_TRACES' if all(t['coverage'] == 'COMPLETE_SOURCE_TERMS' for t in traces)
            else 'PARTIAL_SOURCE_TRACES'))


def _link_ifadah_witnesses(observations, reading_owner, owner_path):
    """Refer to each reading separately, only at the identical written occurrence."""
    occurrences = {(tuple(row['occurrence']['utf8_span']), row['occurrence']['surface']): row
                   for row in observations}
    for index, reading in enumerate(reading_owner.get('readings', [])):
        base = f'{owner_path}/readings/{index}'
        witnesses = [(f'{base}/bindings/{role}', witness)
                     for role, witness in reading['bindings'].items()]
        if reading.get('outer_question_cue'):
            witnesses.append((base + '/outer_question_cue', reading['outer_question_cue']))
        for path, witness in witnesses:
            row = occurrences.get((tuple(witness['utf8_span']), witness['surface']))
            if row is not None:
                row.setdefault('owner_witness_paths', []).append(path)


def _observe_ifadah_program(text, source_id, source_path, source_kind):
    """Observe a source only; the neural scorer never receives its gold program."""
    from tools.evidence_lifecycle_v1 import ResourceLimit
    from nabt.errors import NabtError
    failure = None
    try:
        from tools.lexical_training.ntp_ifadah import observe
        observation = observe(text, source_id)
    except (ResourceLimit, MemoryError) as error:
        failure = ('NEURAL_RESOURCE_LIMIT', type(error).__name__)
    except NabtError as error:
        failure = ('NEURAL_RESOURCE_LIMIT' if error.code == 'RESOURCE_LIMIT' else 'MODEL_UNAVAILABLE',
                   error.code)
    except (ImportError, OSError, ValueError, KeyError) as error:
        failure = ('MODEL_UNAVAILABLE', type(error).__name__)
    if failure is not None:
        observation = {'schema': 'nabt.ntp-ifadah-observation.v1',
                       'source_id': source_id, 'source_sha256': sha256(text.encode()).hexdigest(),
                       'status': failure[0], 'reason': failure[1],
                       'authority': 'NONE', 'release_policy': 'REVIEW_ONLY',
                       'neural_selection_permitted': False}
    return {'source_path': source_path, 'source_kind': source_kind, 'observation': observation}


def execute(route, payload, *, inside_worker=False):
    from . import gateway_routes as routes
    if route == 'ntp':
        p = validate(payload)
        operation, inputs = p['operation'], p['input']
    else:
        operation, inputs = route, payload
    if operation == 'forward':
        from tools.lexical_training.ntp_recursive import forward
        return forward(inputs)
    owner_operation = operation
    representation_source = 'ORIGINAL_INPUT'
    if operation == 'think':
        owner_operation = 'text.read'
        if 'packed_hex' in inputs:
            from tools.lexical_training.ntp_recursive import source
            text, _, _ = source(inputs)
            inputs = {'text': text}
            representation_source = 'EXACT_DECODED_A116_BIT_FRAME'
    owner = routes._execute_owner(owner_operation, inputs, inside_worker=inside_worker)
    if route != 'ntp':
        return owner
    result = {'schema': 'nabt.ntp-result.v1', 'operation': operation, 'owner_result': owner,
              'owner_operation': owner_operation, 'representation_source': representation_source,
              'recursive_observations': [], 'authority': 'ORIGINAL_OWNER_CONDITIONS',
              'observation_coverage': 'NO_TEXT_FIELD',
              'neural_selection_permitted': False, 'world_truth_established': False}
    if type(inputs.get('text')) is str:
        framed = representation_source == 'EXACT_DECODED_A116_BIT_FRAME'
        _observe_sources(result, [{'text': inputs['text'],
                                  'request_path': '/payload/input/packed_hex' if framed else '/payload/input/text',
                                  'source_encoding': 'A116_BIT_FRAME' if framed else 'UTF8_TEXT',
                                  'source_id': inputs.get('source_id'), 'role': 'SOURCE'}], 'NO_TEXT_FIELD')
    elif owner_operation == 'cognitive.lesson':
        from tools.lexical_training import ifadah_programs
        lesson = inputs['lesson']
        sources, empty_coverage = _lesson_sources(lesson, owner)
        _observe_sources(result, sources, empty_coverage)
        # Only the installed lesson owner returns its validated request and source.
        if owner.get('schema') == ifadah_programs.RESULT and owner.get('request') == lesson and 'source_text' in owner:
            if 'owner' in owner:
                _link_ifadah_witnesses(result['recursive_observations'], owner['owner'], '/owner_result/owner')
                result['program_choice_observation'] = _observe_ifadah_program(
                    lesson['text'], lesson['source_id'], '/payload/input/lesson/text', 'ORIGINAL_REQUEST')
            if 'generated_text' in owner:
                generated, coverage = _term_observations(owner['generated_text'])
                _link_ifadah_witnesses(generated, owner['realization_owner'], '/owner_result/realization_owner')
                result['realization_trace'] = {'text_path': '/owner_result/generated_text',
                                               'observations': generated, 'coverage': coverage}
                result['program_choice_observation'] = _observe_ifadah_program(
                    owner['generated_text'], lesson['source_id'] + ':realization',
                    '/owner_result/generated_text', 'OWNER_REALIZATION')
    return result


def request(operation, inputs):
    from .gateway import REQUEST_SCHEMA
    payload = validate({'operation': operation, 'input': inputs})
    return {'schema': REQUEST_SCHEMA, 'route': 'ntp', 'payload': payload}
