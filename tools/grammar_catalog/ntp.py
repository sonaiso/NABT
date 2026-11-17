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
    observations = []
    observation_coverage = 'NO_TEXT_FIELD'
    if type(inputs.get('text')) is str:
        from .operations import exact_terms
        from tools.lexical_training.ntp_recursive import forward
        from nabt.errors import NabtError
        terms = exact_terms(inputs['text'])
        observation_coverage = 'COMPLETE_SOURCE_TERMS' if len(terms) <= 128 else 'FIRST_128_TERMS_ONLY'
        for term in terms[:128]:
            try:
                value = forward({'text': term['surface']})
            except (ValueError, NabtError) as error:
                value = {'status': 'DEFER_EXACT_A116_READING', 'reason': str(error),
                         'authority': 'NONE'}
            observations.append({'occurrence': term, 'observation': value})
    return {'schema': 'nabt.ntp-result.v1', 'operation': operation, 'owner_result': owner,
            'owner_operation': owner_operation, 'representation_source': representation_source,
            'recursive_observations': observations, 'authority': 'ORIGINAL_OWNER_CONDITIONS',
            'observation_coverage': observation_coverage,
            'neural_selection_permitted': False, 'world_truth_established': False}


def request(operation, inputs):
    from .gateway import REQUEST_SCHEMA
    payload = validate({'operation': operation, 'input': inputs})
    return {'schema': REQUEST_SCHEMA, 'route': 'ntp', 'payload': payload}
