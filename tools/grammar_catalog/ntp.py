"""One NTP dispatch under the existing independently replayed I/O gateway.

All legacy adapters enter this dispatcher. Owners keep their exact licenses;
the recursive learner is an observation, never a replacement license.
"""
from copy import deepcopy


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


def _term_observations(text):
    from .operations import exact_terms
    from tools.lexical_training.ntp_recursive import forward
    from nabt.errors import NabtError

    terms = exact_terms(text)
    observations = []
    for term in terms[:128]:
        try:
            value = forward({'text': term['surface']})
        except (ValueError, NabtError) as error:
            value = {'status': 'DEFER_EXACT_A116_READING', 'reason': str(error),
                     'authority': 'NONE'}
        observations.append({'occurrence': term, 'observation': value})
    coverage = 'COMPLETE_SOURCE_TERMS' if len(terms) <= 128 else 'FIRST_128_TERMS_ONLY'
    return observations, coverage


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
        result['recursive_observations'], result['observation_coverage'] = _term_observations(inputs['text'])
    elif owner_operation == 'cognitive.lesson':
        from tools.lexical_training import ifadah_programs
        lesson = inputs['lesson']
        # Only the installed lesson owner returns its validated request and source.
        if owner.get('schema') == ifadah_programs.RESULT and owner.get('request') == lesson and 'source_text' in owner:
            field = 'text' if lesson['mode'] == 'understand' else 'instruction'
            result['observation_request_path'] = '/payload/input/lesson/' + field
            observations, coverage = _term_observations(lesson[field])
            result.update(recursive_observations=observations, observation_coverage=coverage)
            if 'owner' in owner:
                _link_ifadah_witnesses(observations, owner['owner'], '/owner_result/owner')
            if 'generated_text' in owner:
                generated, coverage = _term_observations(owner['generated_text'])
                _link_ifadah_witnesses(generated, owner['realization_owner'], '/owner_result/realization_owner')
                result['realization_trace'] = {'text_path': '/owner_result/generated_text',
                                               'observations': generated, 'coverage': coverage}
    return result


def request(operation, inputs):
    from .gateway import REQUEST_SCHEMA
    payload = validate({'operation': operation, 'input': inputs})
    return {'schema': REQUEST_SCHEMA, 'route': 'ntp', 'payload': payload}
