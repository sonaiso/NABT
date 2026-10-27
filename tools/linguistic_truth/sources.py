"""Pinned, attributed linguistic-designation review and exact source replay.

The source author reports conventions. Replaying that report establishes its
stored byte identity, not historical first designation, the user's intention,
or an external fact. The public reader never accepts a caller's replacement
ledger. Historical mantuq source inventories remain unchanged.
"""
from pathlib import Path
import hashlib
import json
import re

from tools.mantuq_sources import SourceInventoryError, _replay

ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = Path('evidence/linguistic_truth_v1/source_inventory.json')
INVENTORY_SHA256 = '2186d8f4c52d148f13592feef50f617675a8576ff1dfc33f0c9fc6a4bdb56e05'
SUPPLEMENT_PATH = Path('evidence/natural_use_sources_v1/source_inventory.json')
SUPPLEMENT_SHA256 = '3e97720bf5e73514c0b3758fd822eeac5a49f9abd6818e0e1756cbfbd5a687a3'
_MARKS = re.compile(r'[\u064b-\u065f\u0670\u0640]')


def _merge_supplement(inventory, root):
    supplement = _replay(SUPPLEMENT_PATH, SUPPLEMENT_SHA256, root)
    if (supplement['schema'] != 'nabt.linguistic-source-supplement.v1'
            or supplement['base_review_sha256'] != INVENTORY_SHA256):
        raise SourceInventoryError('WRONG_LEXICAL_SUPPLEMENT')
    passages = {row['passage_id']: row for row in supplement['passages']}
    _ids(supplement['passages'], 'passage_id')
    _ids(supplement['sources'], 'source_id')
    for row in supplement['designations']:
        _quotes(row, passages)
    extension = supplement['acquisition_extension']
    _ids(extension['cue_verbs'], 'normal')
    if extension['initial_conjunction'] is not None:
        raise SourceInventoryError('UNREVIEWED_INITIAL_CONJUNCTION')
    for row in extension['cue_verbs']:
        if (not row['forms'] or len(row['forms']) != len(set(row['forms']))
                or any(_MARKS.sub('', form) != row['normal'] for form in row['forms'])
                or not row['passage_ids'] or not set(row['passage_ids']) <= passages.keys()):
            raise SourceInventoryError('UNBOUND_CUE_FORM')
    seen = set()
    expressions = {row['expression'] for row in
                   inventory['designations'] + supplement['designations']}
    for row in extension['retrieval_forms']:
        key = (row['expression'], row['form'])
        if (key in seen or row['expression'] not in expressions
                or _MARKS.sub('', row['form']) != row['normal']
                or row['authority'] != 'LEXICAL_RETRIEVAL_PROPOSAL'
                or row['selected_sense'] is not None
                or not row['passage_ids'] or not set(row['passage_ids']) <= passages.keys()):
            raise SourceInventoryError('UNBOUND_RETRIEVAL_FORM')
        seen.add(key)
    # An exact shared source may be referenced twice by independent reviews.
    # A duplicate identity with different metadata is not silently overwritten.
    for name, key in [('sources', 'source_id'), ('passages', 'passage_id'),
                      ('designations', 'designation_id'), ('relations', 'relation_id')]:
        known = {row[key]: row for row in inventory[name]}
        for row in supplement[name]:
            if row[key] in known:
                if row != known[row[key]]:
                    raise SourceInventoryError('SUPPLEMENT_IDENTITY_COLLISION')
            else:
                inventory[name].append(row)
                known[row[key]] = row
    inventory['base_review_sha256'] = INVENTORY_SHA256
    inventory['supplement_review_sha256'] = SUPPLEMENT_SHA256
    inventory['review_sha256'] = hashlib.sha256(json.dumps(
        [INVENTORY_SHA256, SUPPLEMENT_SHA256], separators=(',', ':')).encode()).hexdigest()
    inventory['acquisition_extension'] = dict(extension, law_id=supplement['law_id'],
        review_sha256=SUPPLEMENT_SHA256, authority=supplement['authority'])
    inventory['extension_scope'] = supplement['scope']
    inventory['replay'].update(source_files=len(inventory['sources']),
        passages=len(inventory['passages']),
        source_bytes_checked=sum(row['bytes'] for row in inventory['sources']),
        supplemental_sources_replayed=True)
    return inventory


def _ids(rows, key):
    values = [row[key] for row in rows]
    if any(type(x) is not str or not x for x in values) or len(set(values)) != len(values):
        raise SourceInventoryError('DUPLICATE_OR_INVALID_SOURCE_IDENTITY')
    return set(values)


def _quotes(row, passages):
    if not row['passage_ids'] or set(row['passage_ids']) != {x['passage_id'] for x in row['evidence']}:
        raise SourceInventoryError('UNBOUND_DESIGNATION_EVIDENCE')
    for evidence in row['evidence']:
        p = passages[evidence['passage_id']]
        start, end = evidence['start'], evidence['end']
        if (type(start) is not int or type(end) is not int or
                not p['start'] <= start < end <= p['end']):
            raise SourceInventoryError('SUBQUOTE_OUTSIDE_PASSAGE')
        selected = p['raw_text'].encode('utf-8')[start-p['start']:end-p['start']]
        if (selected.decode('utf-8') != evidence['quote'] or
                hashlib.sha256(selected).hexdigest() != evidence['sha256'] or
                evidence['original_start'] != p['original_start'] + start-p['start'] or
                evidence['original_end'] != p['original_start'] + end-p['start']):
            raise SourceInventoryError('SUBQUOTE_CHANGED')


def build_inventory(root=ROOT):
    """Reopen the installed review and every excerpt on each call; no cache."""
    inv = _replay(INVENTORY_PATH, INVENTORY_SHA256, root)
    try:
        inv = _merge_supplement(inv, root)
        if inv['schema'] != 'nabt.linguistic-truth-inventory.v1':
            raise SourceInventoryError('WRONG_SOURCE_REVIEW_SCHEMA')
        sources = _ids(inv['sources'], 'source_id')
        _ids(inv['passages'], 'passage_id')
        profiles = _ids(inv['profiles'], 'profile_id')
        designations = _ids(inv['designations'], 'designation_id')
        _ids(inv['relations'], 'relation_id')
        passages = {p['passage_id']:p for p in inv['passages']}
        for p in passages.values():
            if p['source_id'] not in sources:
                raise SourceInventoryError('PASSAGE_SOURCE_MISSING')
        for profile in inv['profiles']:
            if profile['convention'] != profile['profile_id'] or not set(profile['source_passage_ids']) <= passages.keys():
                raise SourceInventoryError('UNBOUND_CONVENTION_PROFILE')
        for row in inv['designations']:
            if row['convention'] not in profiles or row['origin'] not in {'original','transferred'}:
                raise SourceInventoryError('INVALID_DESIGNATION_CONVENTION')
            if not row['forms'] or not row['sense_forms'] or not row['sense_id']:
                raise SourceInventoryError('EMPTY_DESIGNATION')
            _quotes(row, passages)
        for relation in inv['relations']:
            if relation['designation_id'] not in designations or not relation['target_forms']:
                raise SourceInventoryError('UNBOUND_FIGURATIVE_RELATION')
            _quotes(relation, passages)
        inv['replay']['original_comparison_performed_here'] = False
        inv['replay']['designation_subquotes_checked'] = sum(len(x['evidence']) for x in inv['designations']+inv['relations'])
        return inv
    except (KeyError, TypeError, UnicodeError) as exc:
        raise SourceInventoryError('INVALID_LINGUISTIC_SOURCE_REVIEW') from exc
