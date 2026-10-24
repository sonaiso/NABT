"""Independent raw-premise checks for names, nominal inflection and lexical sense.

No production reader, lexical compiler or name-matching helper is imported.
The caller supplies its raw SourceAudit and already indexed report readings.
Raw observations establish the lexical premises; model/reading hashes are
identity checks only. Full compiler identity remains a separate replay gate.
"""
from hashlib import sha256
import json
import re


LAW = 'nabt.source-bound-unvocalized-name.v1'
VOWELS = frozenset('ًٌٍَُِْ')
MARKS = VOWELS | frozenset('ّٰ')
ORDER = 'ًٌٍَُِّْٰ'
# The declared public extended-Buckwalter character correspondence. The
# independently checked name domain excludes Quranic signs outside MARKS.
BW = dict(zip("'>&<}AbptvjHxd*rzs$SDTZEgfqklmnhwYyFNKaui~o^#`{",
              'ءأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوىيًٌٍَُِّْٰٓٔٱ', strict=True))
ROOT_BW = {key: value for key, value in BW.items()
           if value in 'ءبتثجحخدذرزسشصضطظعغفقكلمنهوي'}
ROOT_BW['A'] = 'ء'
FIELDS = {'kind', 'law_id', 'reading_id', 'lexical_id', 'occurrence_span', 'stem_span',
          'source_template', 'source_form', 'lexical_source', 'inventory_sha256',
          'support_records', 'construction_basis', 'construction_supports',
          'context_supplies_lexical_marks', 'authority'}


def require(condition, message):
    if not condition:
        raise ValueError('Name correspondence: ' + message)


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def clusters(value):
    require(type(value) is str and value, 'nonempty Arabic form required')
    result = []
    for char in value:
        if char in MARKS:
            require(result and char not in result[-1][1], 'orphan or duplicate mark')
            result[-1][1].add(char)
            require(len(result[-1][1] & VOWELS) <= 1, 'contradictory marks on one letter')
        else:
            require('\u0621' <= char <= '\u063a' or '\u0641' <= char <= '\u064a' or char == 'ٱ',
                    'form outside the declared Arabic lookup alphabet')
            result.append(['ا' if char == 'ٱ' else char, set()])
    return result


def letters(value):
    return ''.join(letter for letter, _ in clusters(value))


def template(value):
    parts = clusters(value)
    parts[-1][1] -= VOWELS
    return ''.join(letter + ''.join(mark for mark in ORDER if mark in marks)
                   for letter, marks in parts)


def observed_form_supported(observed, source_template):
    left, right = clusters(observed), clusters(source_template)
    if len(left) != len(right):
        return False
    for index, ((a, marks), (b, supplied)) in enumerate(zip(left, right)):
        if a != b:
            return False
        if index + 1 < len(left) and marks & VOWELS and supplied & VOWELS and marks & VOWELS != supplied & VOWELS:
            return False
        if any(mark in marks and mark not in supplied for mark in ('ّ', 'ٰ')):
            return False
    return True


def unvocalized_label_compatible(surface, declared):
    try:
        parts = clusters(declared)
        return all(not marks for _, marks in parts) and letters(surface) == letters(declared)
    except ValueError:
        return False


def check_span(span, inputs, surface):
    require(type(span) is dict and type(span.get('start')) is int and type(span.get('end')) is int,
            'span bounds must be exact integers')
    raw = inputs['text'].encode()
    start, end = span['start'], span['end']
    require(0 <= start < end <= len(raw), 'span outside input')
    require(span.get('source_id') == inputs['source_id'] and span.get('source_sha256') == sha256(raw).hexdigest(),
            'span belongs to another source')
    piece = raw[start:end]
    require(piece.decode() == surface, 'span moved or changed its surface')
    if 'span_sha256' in span:
        require(span['span_sha256'] == sha256(piece).hexdigest(), 'span digest mismatch')


def _field(tokens, prefix):
    found = [token[len(prefix):] for token in tokens if token.startswith(prefix)]
    require(len(found) <= 1, 'ambiguous raw feature')
    return found[0] if found else None


def _decode(value, mapping=BW):
    if value is None:
        return None
    require(type(value) is str and all(char in mapping for char in value), 'unsupported raw transliteration')
    return ''.join(mapping[char] for char in value)


def raw_features(row):
    tokens = row['tokens']
    require(tokens and tokens[0] == 'STEM' and _field(tokens, 'POS:') == row['tag']
            and row['tag'] in ('N', 'PN', 'ADJ'), 'receipt is not its annotated nominal stem')
    profiles = [token for token in tokens if re.fullmatch(r'[123]?[MF]?[SDP]|[MF]', token)]
    require(len(profiles) <= 1, 'ambiguous raw person/gender/number profile')
    profile = profiles[0] if profiles else None
    features = {'pos': row['tag'], 'lemma': _decode(_field(tokens, 'LEM:')),
                'root': _decode(_field(tokens, 'ROOT:'), ROOT_BW),
                'person': profile,
                'gender': 'masculine' if profile and 'M' in profile else 'feminine' if profile and 'F' in profile else None,
                'number': next((name for mark, name in (('S', 'singular'), ('D', 'dual'), ('P', 'plural'))
                                if profile and mark in profile), None),
                'aspect': next((token for token in ('PERF', 'IMPF', 'IMPV') if token in tokens), None),
                'voice': 'passive' if 'PASS' in tokens else 'active' if 'ACT' in tokens else None}
    derivation = sorted(token for token in tokens
                        if token in ('ACT', 'PASS', 'PCPL', 'VN') or re.fullmatch(r'\([IVX]+\)', token))
    return features, derivation


def _raw_support(receipt, audit):
    require(type(receipt) is dict, 'raw receipt is not an object')
    require(type(receipt.get('locator')) is list and len(receipt['locator']) == 4
            and all(type(item) is int and item > 0 for item in receipt['locator']), 'invalid raw locator')
    row = audit.receipt(receipt)
    group = [item for item in audit.records.values() if item['locator'][:3] == row['locator'][:3]]
    require([item['locator'][3] for item in group] == list(range(1, len(group) + 1))
            and sum(item['tokens'][0] == 'STEM' for item in group) == 1,
            'raw word has a missing/duplicated segment or multiple stems')
    return row


def _construction_proven(reading, source_features, source_derivation, audit):
    proofs = reading.get('construction_supports')
    require(type(proofs) is list and proofs, 'no independent inflection observations')
    rows = [_raw_support(proof, audit) for proof in proofs]
    forms = [_decode(row['form']) for row in rows]
    require(all(raw_features(row) == (source_features, source_derivation) for row in rows),
            'inflection support borrowed another lexical profile')
    basis = reading.get('construction_basis')
    if basis == 'paired_lexical_terminal_realizations':
        require(all(template(form) == template(forms[0]) for form in forms)
                and observed_form_supported(reading['stem_surface'], template(forms[0])),
                'terminal pair changed the internal word')
        families = {'a' if marks & set('ًَ') else 'u' if marks & set('ٌُ') else 'i' if marks & set('ٍِ') else None
                    for form in forms for _, marks in [clusters(form)[-1]]}
        require(len(families - {None}) >= 2, 'inflection needs two distinct terminal-vowel families')
        return
    raise ValueError('Name correspondence: unsupported independent nominal-construction proof: ' + str(basis))


def validate_name_correspondence(ref, inputs, entities, *, analysis, rows, audit, model_summary):
    witness = ref.get('name_correspondence')
    require(type(witness) is dict and set(witness) == FIELDS, 'unknown or incomplete witness schema')
    require(ref.get('origin') == 'named', 'witness attached to a non-named reference')
    require(witness['kind'] == 'source_bound_unvocalized_name' and witness['law_id'] == LAW,
            'unapproved witness law')
    require(witness['context_supplies_lexical_marks'] is False and witness['authority'] ==
            'CONDITIONAL_IDENTITY_FROM_NAMING_PREMISE_AND_SELECTED_LEXICAL_READING', 'authority or lexical-origin changed')
    require(audit is not None and type(model_summary) is dict, 'raw source audit and model identity are required')
    require(type(analysis) is dict and type(rows) is dict, 'same-analysis readings are required')
    rid = witness['reading_id']
    require(rid in analysis['reading_ids'] and rid in rows, 'reading borrowed from another analysis')
    reading = rows[rid]
    ident = reading.get('identity', {})
    require(reading.get('reading_id') == rid and digest(ident) == rid,
            'reading identity is inconsistent')
    require(ident.get('source_id') == inputs['source_id'] and ident.get('scope') == inputs['scope']
            and ident.get('source_sha256') == sha256(inputs['text'].encode()).hexdigest(), 'reading source/scope changed')
    require(reading.get('kind') == 'noun' and reading.get('construction') == 'inflected'
            and reading.get('variant') == 'attested' and not reading.get('annotation_only'),
            'witness requires an attested inflected nominal reading')
    require(not any(reading.get(key) for key in ('person_evidence', 'prefix_relation', 'nominal_case_carrier')),
            'carrier, prefix or attached/person profile outside this bridge')
    require(type(witness['lexical_id']) is str and witness['lexical_id'] == ident.get('lexical_id')
            and re.fullmatch(r'[0-9a-f]{64}', witness['lexical_id']),
            'lexical identity mismatch')
    require(witness['occurrence_span'] == ident.get('span') == ref.get('span')
            and witness['stem_span'] == reading.get('stem_span'), 'witness moved its occurrence/stem')
    check_span(ref['span'], inputs, ref['surface'])
    check_span(reading['stem_span'], inputs, reading['stem_surface'])
    observed = clusters(ref['surface'])
    require(any('ّ' in marks for _, marks in observed) and all('ٰ' not in marks for _, marks in observed),
            'new bridge needs a source shadda and excludes dagger alif')
    require(any(unvocalized_label_compatible(ref['surface'], entity['name']) for entity in entities.values()),
            'no entirely unvocalized compatible naming premise')

    segmentation = reading.get('segmentation', {})
    parts = segmentation.get('parts', [])
    require(segmentation.get('licensed') is True and segmentation.get('coverage_valid') is True,
            'unlicensed target segmentation')
    require([part.get('kind') for part in parts] in (['nominal_stem'], ['article', 'nominal_stem']),
            'unsupported target prefix/suffix segmentation')
    require(''.join(part['surface'] for part in parts) == ref['surface']
            and parts[-1]['surface'] == reading['stem_surface'] and parts[-1]['span'] == reading['stem_span'],
            'target segmentation does not conserve the word and stem')
    cursor = ref['span']['start']
    for part in parts:
        check_span(part['span'], inputs, part['surface'])
        require(part['span']['start'] == cursor, 'target segmentation has a gap/overlap')
        cursor = part['span']['end']
    require(cursor == ref['span']['end'], 'target segmentation misses source bytes')
    if len(parts) == 2:
        require(letters(parts[0]['surface']) == 'ال' and reading.get('al_evidence') == 1
                and not any(marks & set('ّٰ') for _, marks in clusters(parts[0]['surface'])),
                'unsupported article reconstruction')

    source = {'id': audit.source_id, 'sha256': audit.sha, 'byte_length': len(audit.raw)}
    require(witness['lexical_source'] == source == model_summary.get('source'), 'raw model source identity mismatch')
    require(set(model_summary.get('excluded_verses', [])) == audit.exclusions, 'model/audit exclusions differ')
    require(model_summary.get('projection_id') == 'qac.extended-buckwalter.unicode.v1'
            and model_summary.get('lookup_id') == 'qac.lookup.wasl-equivalence.v1'
            and model_summary.get('target_role_labels_available') is False, 'unapproved source projection/target labels')
    require(witness['inventory_sha256'] == model_summary.get('inventory_sha256')
            and type(witness['inventory_sha256']) is str and re.fullmatch(r'[0-9a-f]{64}', witness['inventory_sha256']),
            'inventory identity mismatch')
    supports = witness['support_records']
    require(type(supports) is list and supports
            and len({proof.get('record_id') for proof in supports}) == len(supports), 'empty or duplicated lexical support')
    require(all(proof in reading.get('support_records', []) for proof in supports), 'support borrowed from another reading')
    source_rows = [_raw_support(proof, audit) for proof in supports]
    source_features, derivation = raw_features(source_rows[0])
    require(all(raw_features(row) == (source_features, derivation) for row in source_rows),
            'lexical support mixed incompatible raw profiles')
    require(all(reading.get('lexical_features', {}).get(key) == value for key, value in source_features.items()),
            'output lexical features differ from the raw source')
    forms = [_decode(row['form']) for row in source_rows]
    require(witness['source_form'] in forms and witness['source_template'] == template(witness['source_form'])
            and all(template(form) == witness['source_template'] for form in forms), 'source form/template does not replay')
    require(observed_form_supported(reading['stem_surface'], witness['source_template']),
            'observed internal marks conflict with their source template')
    require(witness['construction_basis'] == reading.get('construction_basis') ==
            'paired_lexical_terminal_realizations' and witness['construction_supports'] ==
            reading.get('construction_supports'), 'inflection witness detached from its paired source construction')
    _construction_proven(reading, source_features, derivation, audit)
    return True


# Independently selected primary intervals; a runtime-supplied passage or hash
# cannot broaden them. Installed bytes are checked without a production loader.
PRIMARY = {
    'same_form_nominal_inflection': ('sibawayhi',
        'a160f940bb194e6fe7e6655d2c7f28e41f1fc648c4c5e340cc4e42306d5cb625',
        23873, 25642, 'b7a28f0fc6d818c62c4fd862d3b32799b17ba3d84f61c9ce71f3c66fb03d8e3f',
        216, 229, '599f22fe249871f602efe2e0ddc801d3742960a3',
        'data/0180Sibawayhi/0180Sibawayhi.KitabSibawayhi/0180Sibawayhi.KitabSibawayhi.JK006989-ara1'),
    'vocalized_hasiba_sense': ('mukhtar_sihah',
        'e93f4054f3cddb826a7b3fafd01eac8c4b39b25ed2d92ece7ea093b755776691',
        290519, 291512, 'f9fb3243022e5497d8f33a04bbd3fdd69f2529f7b9117d2b80df220362d48995',
        2723, 2730, '4b1d2886508b435eb0377ccab96e1da96cc8ee0a',
        'data/0666IbnAbiBakrZaynDinRazi/0666IbnAbiBakrZaynDinRazi.MukhtarSihah/0666IbnAbiBakrZaynDinRazi.MukhtarSihah.JK000107-ara1'),
}


def _hex(value):
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def validate_primary_passage(passage, rule):
    from pathlib import Path
    require(type(passage) is dict and rule in PRIMARY, 'missing selected primary passage')
    keys = ('source_id', 'source_sha256', 'start', 'end', 'span_sha256',
            'line_start', 'line_end', 'source_commit', 'source_path')
    require(tuple(passage.get(key) for key in keys) == PRIMARY[rule]
            and all(type(passage.get(key)) is int for key in ('start', 'end', 'line_start', 'line_end')),
            'primary passage changed its selected identity/interval')
    source = Path(__file__).resolve().parents[1] / 'src/nabt/data/source_evidence' / (passage['source_id'] + '.txt')
    raw = source.read_bytes()
    require(sha256(raw).hexdigest() == passage['source_sha256'], 'primary raw source changed')
    start, end = passage['start'], passage['end']
    lines = raw.splitlines(keepends=True)
    require(sha256(raw[start:end]).hexdigest() == passage['span_sha256']
            and sum(map(len, lines[:passage['line_start'] - 1])) == start
            and sum(map(len, lines[:passage['line_end']])) == end, 'primary interval cannot be replayed')
    if rule == 'vocalized_hasiba_sense':
        require(passage.get('supplementary_registry_sha256') ==
                '96f505a0e34964e6b7fc65ed7dfaa6c0f5430c75a51766760495c25295ab1fe7',
                'unregistered supplementary lexical source')


def _observations(proofs, audit, *, tanwin=False, pair=False):
    require(audit is not None and type(proofs) is list and proofs, 'raw nominal observations required')
    require(all(type(p) is dict for p in proofs) and
            len({p.get('record_id') for p in proofs}) == len(proofs), 'duplicate/malformed raw observations')
    rows = [_raw_support(p, audit) for p in proofs]
    features, derivation = raw_features(rows[0])
    forms = [_decode(row['form']) for row in rows]
    lemma_bw = _field(rows[0]['tokens'], 'LEM:')
    require(all(raw_features(row) == (features, derivation) and
                _field(row['tokens'], 'LEM:') == lemma_bw for row in rows), 'raw nominal profiles differ')
    require(all(template(form) == template(forms[0]) for form in forms), 'raw internal templates differ')
    require(features['pos'] in ('N', 'ADJ') and features['number'] == 'singular'
            and features['gender'] in ('masculine', 'feminine') and features['root'] and lemma_bw,
            'ordinary singular nominal source features are incomplete')
    endings = [clusters(form)[-1][1] & VOWELS for form in forms]
    if tanwin:
        require(all(ending in ({'ً'}, {'ٌ'}, {'ٍ'}) for ending in endings), 'own tanwin must be directly observed')
    if pair:
        families = {'a' if marks & set('ًَ') else 'u' if marks & set('ٌُ') else 'i' if marks & set('ٍِ') else None
                    for marks in endings}
        require(len(families - {None}) >= 2, 'donor has no two terminal-vowel families')
    shared = {'lemma_bw': lemma_bw, 'root': features['root'], 'template': template(forms[0]),
              'gender': features['gender'], 'number': features['number'],
              'nominal_derivation_features': derivation}
    return features, shared


def validate_nominal_correspondence(reading, inputs, audit):
    witness = reading.get('nominal_paradigm_correspondence')
    require(type(witness) is dict and set(witness) == {
        'kind', 'rule', 'policy_sha256', 'passage', 'recipient_lexical_id', 'recipient_pos',
        'shared_features', 'recipient_tanwin_supports', 'donors', 'transferred_fields',
        'source_pos_preserved', 'semantic_equivalence_claimed', 'target_role_labels_used'},
        'nominal correspondence schema changed')
    require(witness['kind'] == witness['rule'] == 'same_form_nominal_inflection'
            and _hex(witness['policy_sha256']) and witness['transferred_fields'] == ['construction']
            and witness['source_pos_preserved'] is True and witness['semantic_equivalence_claimed'] is False
            and witness['target_role_labels_used'] is False, 'nominal bridge expanded its authority')
    validate_primary_passage(witness['passage'], 'same_form_nominal_inflection')
    require(reading.get('kind') == 'noun' and reading.get('variant') == 'attested'
            and not reading.get('annotation_only') and not reading.get('nominal_case_carrier')
            and reading.get('construction') == 'inflected' and reading.get('class_candidates') == [0]
            and reading.get('construction_basis') == 'same_form_nominal_independent_pair',
            'nominal bridge changed its recipient domain')
    person = reading.get('person_evidence')
    if person is not None:
        require(not person.get('attached_pronouns') and person.get('form_kind') == 'nominal'
                and person.get('family') is None and _hex(person.get('source_lexical_id')),
                'nominal bridge borrowed an attached/non-nominal person profile')
    lexical_id = reading.get('identity', {}).get('lexical_id') if person is None else person['source_lexical_id']
    require(_hex(lexical_id) and witness['recipient_lexical_id'] == lexical_id,
            'nominal recipient identity changed')
    check_span(reading['stem_span'], inputs, reading['stem_surface'])
    own, shared = _observations(witness['recipient_tanwin_supports'], audit, tanwin=True)
    require(witness['recipient_pos'] == own['pos'] and witness['shared_features'] == shared,
            'nominal witness does not describe its raw recipient')
    require(all(reading.get('lexical_features', {}).get(k) == v for k, v in own.items() if k != 'person')
            and observed_form_supported(reading['stem_surface'], shared['template']),
            'nominal reading copied features or changed the raw recipient form')
    if person is None:
        require(reading['lexical_features'].get('person') == own['person'], 'nominal raw profile changed')
    else:
        require(person.get('source_person_code') == own['person']
                and type(reading['lexical_features'].get('person')) is int
                and reading['lexical_features']['person'] == 3
                and person.get('person_profile') == {'person': 3,
                    'gender': 0 if own['gender'] == 'masculine' else 1, 'number': 0},
                'nominal person adapter changed the independently annotated traits')
    require(witness in reading.get('support_records', []) and all(p in reading['support_records']
            for p in witness['recipient_tanwin_supports']), 'nominal recipient borrowed another reading support')
    donors = witness['donors']
    require(type(donors) is list and donors and all(type(d) is dict for d in donors)
            and len({d.get('lexical_id') for d in donors}) == len(donors), 'missing/repeated nominal donor')
    all_pairs = []
    for donor in donors:
        require(set(donor) == {'lexical_id', 'pos', 'tanwin_supports', 'paired_terminal_supports'}
                and _hex(donor['lexical_id']) and donor['lexical_id'] != lexical_id,
                'nominal donor identity/schema changed')
        other, donor_shared = _observations(donor['tanwin_supports'], audit, tanwin=True)
        paired, pair_shared = _observations(donor['paired_terminal_supports'], audit, pair=True)
        require(other['pos'] == paired['pos'] == donor['pos'] and donor['pos'] != own['pos']
                and donor_shared == pair_shared == shared, 'nominal donor changed POS or shared raw features')
        require(all(p in donor['paired_terminal_supports'] for p in donor['tanwin_supports']),
                'donor tanwin detached from its own terminal paradigm')
        all_pairs.extend(donor['paired_terminal_supports'])
    require(reading.get('construction_supports') == all_pairs, 'transferred inflection receipts differ from donors')
    return True


def validate_sense_witness(relation, analysis, rows, inputs, audit):
    witness = relation.get('independent_sense_witness')
    require(type(witness) is dict and set(witness) == {'kind', 'rule', 'operator_span',
        'operator_surface', 'operator_reading_id', 'required_medial_vowel', 'required_written_active_form',
        'sense', 'source', 'target_role_used_as_sense_evidence', 'embedded_fact_projection'},
        'lexical sense witness schema changed')
    require(witness['kind'] == 'observed_medial_vowel_lexical_sense'
            and witness['rule'] == 'vocalized_hasiba_sense' and witness['sense'] == 'belief'
            and witness['required_medial_vowel'] == 'ِ' and witness['required_written_active_form'] == 'حَسِبَ'
            and witness['target_role_used_as_sense_evidence'] is False
            and witness['embedded_fact_projection'] is False, 'sense witness expanded its authority')
    source = witness['source']
    require(type(source) is dict and source.get('kind') == 'source_construction_grammar'
            and source.get('rule') == witness['rule'] and _hex(source.get('policy_sha256'))
            and _hex(source.get('law_sha256')), 'sense witness lost its grammar-source receipt')
    validate_primary_passage(source.get('passage'), 'vocalized_hasiba_sense')
    require(relation.get('kind') == 'operator' and relation.get('family') == 'zanna'
            and relation.get('lemma') == 'حسب' and relation.get('sense') == 'belief'
            and relation.get('aspect') == 'PERF' and relation.get('scope_preserved') is True
            and relation.get('embedded_fact_projection') is False, 'sense is outside the bounded cognitive operator')
    rid = witness['operator_reading_id']
    require(rid in analysis['reading_ids'] and rid in rows and rid == relation.get('operator_reading_id'),
            'sense borrowed another analysis/reading')
    reading = rows[rid]
    require(reading.get('kind') == 'verb' and reading.get('variant') == 'attested'
            and not reading.get('annotation_only') and witness['operator_span'] == relation.get('head_span')
            == reading.get('stem_span'), 'sense borrowed a fallback or another occurrence')
    check_span(witness['operator_span'], inputs, witness['operator_surface'])
    require(clusters(witness['operator_surface']) == clusters('حَسِبَ'),
            'active hasiba needs all three explicit source vowels')
    features = reading.get('lexical_features', {})
    require(features.get('pos') == 'V' and letters(features.get('root') or '') == 'حسب'
            and letters(features.get('lemma') or '') == 'حسب' and features.get('aspect') == 'PERF'
            and features.get('voice') != 'passive' and type(features.get('person')) is int and features['person'] == 3
            and features.get('gender') == 'masculine' and features.get('number') == 'singular',
            'sense reading lacks the acquired active third-person lexical profile')
    require(audit is not None, 'sense requires its raw lexical audit')
    proofs = [p for p in reading.get('support_records', []) if type(p) is dict and 'record_id' in p]
    require(proofs, 'grammar fallback alone cannot license the lexical sense')
    for proof in proofs:
        raw = _raw_support(proof, audit)
        tokens = raw['tokens']
        require(tokens[0] == 'STEM' and raw['tag'] == _field(tokens, 'POS:') == 'V'
                and 'PERF' in tokens and 'IMPF' not in tokens and 'IMPV' not in tokens and 'PASS' not in tokens
                and '3MS' in tokens and not any(re.fullmatch(r'\([IVX]+\)', token) and token != '(I)' for token in tokens)
                and _decode(_field(tokens, 'ROOT:'), ROOT_BW) == 'حسب'
                and _decode(_field(tokens, 'LEM:')) == features['lemma']
                and clusters(_decode(raw['form'])) == clusters('حَسِبَ'),
                'raw lexical receipt does not independently witness active form-I hasiba')
    require(not any(claim.get('predicate_kind') != 'scoped' for claim in analysis.get('claims', [])),
            'cognitive sense projected an embedded fact into a separate assertion')
    return True



def fixture_paths():
    from pathlib import Path
    folder = Path(__file__).resolve().parents[1] / 'evidence/arabic_completion_v3/independent_oracle/validator_review_v1'
    return tuple(folder / (name + '.json') for name in
                 ('name_v2', 'nominal_v1', 'nominal_unmarked_v1', 'sense_v1'))
