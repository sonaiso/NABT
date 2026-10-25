"""Pinned, attributed linguistic-designation review and exact source replay.

The source author reports conventions. Replaying that report establishes its
stored byte identity, not historical first designation, the user's intention,
or an external fact. The public reader never accepts a caller's replacement
ledger. Historical mantuq source inventories remain unchanged.
"""
from pathlib import Path
import hashlib

from tools.mantuq_sources import SourceInventoryError, _replay

ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = Path('evidence/linguistic_truth_v1/source_inventory.json')
INVENTORY_SHA256 = '2186d8f4c52d148f13592feef50f617675a8576ff1dfc33f0c9fc6a4bdb56e05'


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
