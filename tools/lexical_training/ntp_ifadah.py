"""Conditional program-choice observations over exact, source-bound A116 operators.

The existing ifadah reader supplies operator segmentation and lexical bindings.
Only the ordered cell groups enter the scorer. All four candidates remain in its
softmax; neither the owner's name nor its accepted program filters them.
"""
from copy import deepcopy
from hashlib import sha256
import json
import math
import re

from nabt.errors import NabtError
from . import ifadah_programs as owner, ntp_recursive as net

DIRECTORY = net.ROOT / 'evidence/ntp_ifadah_v1'
MODEL = DIRECTORY / 'model.json'
MODEL_SHA256 = '6e016cd0b93745ca837b3f73eb030a055c890abee35e334322f2004e33898ff9'
PROTOCOL_SHA256 = 'ff03c37bef2e04f120e2bc183bbf21ca74fa73a5283f8fd02a9f4b1d32a834bc'
SUPERVISION_SHA256 = '346d115a6231ce245b8508a3e4c4c9fdd477fe3913a380cf2e888ed922416a51'
CANDIDATES = ('negation', 'wish', 'ask', 'ask_negation')
FORCES = ('assert', 'ask', 'wish')
FRAMES = ('plain', 'negation')
AXES = tuple((FORCES.index(owner.PROGRAMS[name][0]), FRAMES.index(owner.PROGRAMS[name][1]))
             for name in CANDIDATES)


def shapes():
    return {**net.shared_shapes(), 'program_force': (len(FORCES), net.DIM),
            'program_frame': (len(FRAMES), net.DIM)}


def validate_model(model):
    def shape(value, dims):
        if not dims:
            return type(value) in (int, float) and abs(value) <= 1000 and math.isfinite(value)
        return type(value) is list and len(value) == dims[0] and all(
            shape(child, dims[1:]) for child in value)
    hashes = ('protocol_sha256', 'supervision_sha256', 'initial_model_sha256', 'source_sha256')
    fields = {'schema', 'alphabet_id', 'candidates', 'forces', 'frames', 'parameters',
              'authority', 'release_policy', *hashes}
    if (type(model) is not dict or set(model) != fields
            or model['schema'] != 'nabt.ntp-ifadah-model.v1'
            or model['alphabet_id'] != net.ALPHABET_ID
            or model['candidates'] != list(CANDIDATES) or model['forces'] != list(FORCES)
            or model['frames'] != list(FRAMES) or model['authority'] != 'NONE'
            or model['release_policy'] != 'REVIEW_ONLY'
            or any(type(model[key]) is not str or re.fullmatch('[0-9a-f]{64}', model[key]) is None
                   for key in hashes)
            or type(model['parameters']) is not dict or set(model['parameters']) != set(shapes())
            or any(not shape(model['parameters'][key], dims) for key, dims in shapes().items())):
        raise ValueError('Invalid conditional program-choice model')
    return model


def load():
    raw = MODEL.read_bytes()
    if len(raw) > 1048576 or sha256(raw).hexdigest() != MODEL_SHA256:
        raise ValueError('Program-choice model identity changed')
    model = validate_model(json.loads(raw))
    paths = ((DIRECTORY / 'protocol.json', 'protocol_sha256'),
             (DIRECTORY / 'supervision.json', 'supervision_sha256'),
             (net.MODEL, 'initial_model_sha256'),
             (net.ROOT / 'evidence/ifadah_programs_v1/data.json', 'source_sha256'))
    for path, key in paths:
        if sha256(path.read_bytes()).hexdigest() != model[key]:
            raise ValueError('Program-choice model provenance changed')
    if (model['protocol_sha256'] != PROTOCOL_SHA256
            or model['supervision_sha256'] != SUPERVISION_SHA256
            or model['initial_model_sha256'] != net.MODEL_SHA256):
        raise ValueError('Program-choice protocol changed')
    supervision = json.loads((DIRECTORY / 'supervision.json').read_bytes())
    slots = owner.awamil.DATA / 'awamil_occurrence_bank_v1.json'
    if sha256(slots.read_bytes()).hexdigest() != supervision['slot_source_sha256']:
        raise ValueError('Program-choice lexical slot provenance changed')
    return model


def scores(model, groups):
    p = validate_model(model)['parameters']
    if type(groups) not in (list, tuple) or not 1 <= len(groups) <= 2:
        raise ValueError('Expected one or two ordered operator word groups')
    words = [net.encode_state(p, cells) for cells in groups]
    hidden = words[0]
    for word in words[1:]:
        hidden = net.join_states(p, hidden, word)
    forces = net._linear(p['program_force'], hidden)
    frames = net._linear(p['program_frame'], hidden)
    logits = [forces[force] + frames[frame] for force, frame in AXES]
    weights = [math.exp(value - max(logits)) for value in logits]
    total = sum(weights)
    return [{'name': name, 'score': value / total} for name, value in zip(CANDIDATES, weights, strict=True)]


def _operator_count(tree):
    # Validate the complete retained tree, while keeping its labels out of features.
    owner.program_name(tree)
    count = 0
    while tree['op'] != 'predication':
        count += 1
        tree = tree['body']
    return count


def project(text, source_id):
    # The installed production owner derives this internal ID from a validated
    # 128-byte request identity. Keep its suffix, rather than reapply the outer
    # request limit to the already-derived source.
    owner.wire._text(source_id, 'source_id', 128 + len(':realization'))
    if (type(text) is not str or not text.strip() or len(text) > 256
            or len(text.encode('utf-8', errors='strict')) > 256):
        raise ValueError('Expected nonempty source within 256 UTF-8 bytes')
    raw = text.encode('utf-8')
    digest = sha256(raw).hexdigest()
    retained = owner.understand(text, source_id)
    observations = []
    for index, reading in enumerate(retained['readings']):
        witnesses = []
        if 'g' in reading['bindings']:
            witnesses.append(reading['bindings']['g'])
        if reading.get('outer_question_cue') is not None:
            witnesses.append(reading['outer_question_cue'])
        witnesses.sort(key=lambda witness: witness['utf8_span'][0])
        projected = []
        previous = -1
        for witness in witnesses:
            span = witness['utf8_span']
            if (type(span) is not list or len(span) != 2 or any(type(v) is not int for v in span)
                    or not 0 <= span[0] < span[1] <= len(raw) or span[0] < previous
                    or raw[slice(*span)].decode('utf-8') != witness['surface']
                    or witness.get('source_id', source_id) != source_id
                    or witness.get('source_sha256', digest) != digest):
                raise ValueError('Detached or overlapping source operator')
            previous = span[1]
            item = {'surface': witness['surface'], 'utf8_span': list(span)}
            try:
                _, cells, _ = net.source({'text': witness['surface']})
                item.update(status='EXACT_A116', cells=list(cells))
            except NabtError as error:
                item.update(status='DEFER_A116', code=error.code)
            projected.append(item)
        count = _operator_count(reading['program'])
        if len(witnesses) != count:
            status = 'DEFER_OPERATOR_WITNESS'
        elif not witnesses:
            status = 'DEFER_NO_OPERATOR'
        elif any(item['status'] != 'EXACT_A116' for item in projected):
            status = 'DEFER_OPERATOR_REPRESENTATION'
        elif len(projected) > 2:
            status = 'DEFER_OPERATOR_REPRESENTATION'
        else:
            status = 'ELIGIBLE'
        observations.append({'reading_index': index, 'operator_occurrences': projected,
                             'status': status, 'owner_tree': deepcopy(reading['program'])})
    return {'source_id': source_id, 'source_sha256': digest, 'observations': observations}


def groups(observation):
    if observation['status'] != 'ELIGIBLE':
        raise ValueError('An incomplete operator source is not a training example')
    return [list(item['cells']) for item in observation['operator_occurrences']]


def observe(text, source_id):
    result = project(text, source_id)
    result.update(schema='nabt.ntp-ifadah-observation.v1', candidate_domain=list(CANDIDATES),
                  authority='NONE', release_policy='REVIEW_ONLY', neural_selection_permitted=False,
                  conditioned_on='OWNER_ATTESTED_OPERATOR_SEGMENTATION_AND_LEXICAL_BINDINGS',
                  subject_predicate_binding_learned=False, instruction_intent_learned=False,
                  grammar_certified=False, world_truth_established=False)
    eligible = [item for item in result['observations'] if item['status'] == 'ELIGIBLE']
    model, failure = None, None
    if eligible:
        try:
            model = load()
        except (OSError, ValueError, KeyError) as error:
            failure = str(error)
    for item in result['observations']:
        tree = item.pop('owner_tree')
        if item['status'] != 'ELIGIBLE':
            continue
        if model is None:
            item.update(status='MODEL_UNAVAILABLE', reason=failure)
            continue
        choices = scores(model, groups(item))
        best = max(choice['score'] for choice in choices)
        selected = [choice['name'] for choice in choices if choice['score'] == best]
        item.update(scores=choices, all_candidates_scored=True, model_sha256=MODEL_SHA256)
        if len(selected) != 1:
            item.update(status='DEFER_TIED_PROPOSAL', proposed_name=None, proposed_program=None)
            continue
        _, subject, predicate = owner.program_name(tree)
        proposed = owner.program(selected[0], subject, predicate)
        item.update(status='PROPOSED', proposed_name=selected[0], proposed_program=proposed,
                    matches_retained_reading=proposed == tree)
    statuses = {item['status'] for item in result['observations']}
    result['status'] = ('DEFER_OUTSIDE_FRAGMENT' if not statuses else
                        next(iter(statuses)) if len(statuses) == 1 else 'MIXED_SOURCE_READINGS')
    return result
