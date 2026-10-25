"""Replay the installed selected-source review without accepting caller authority.

The inventory is a reviewed research catalogue, not an occurrence interpreter.
Existing source files are reopened; raw quotations are returned only after their
full file and exact half-open byte ranges match the installed review. Web
references are deliberately not promoted to locally attested premises.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = Path('evidence/mantuq_inference_v1/source_inventory.json')
INVENTORY_SHA256 = 'f439cbf69138f8bf1a93f6947641dee2c290f803aad66d8110b37877b55ac08f'
SUPPLEMENT_PATH = Path('evidence/mantuq_inference_v1/source_supplement.json')
SUPPLEMENT_SHA256 = '0ae87138967f309ec191b4f6390167f32e1c86f18b14113fe11752f84b59f55c'


class SourceInventoryError(ValueError):
    """An installed review or a cited retained source no longer matches."""


def build_inventory(root: Path = ROOT) -> dict:
    """Return fresh, byte-replayed source data; no supplied manifest is admitted.

    The ``root`` override enables isolated source-replay tests. The same pinned
    review and source hashes apply to every root. Theorem names are references;
    this function does not claim to run Lean or authenticate a printed edition.
    """
    return _replay(INVENTORY_PATH, INVENTORY_SHA256, root)


def build_supplement(root: Path = ROOT) -> dict:
    """Replay the separately versioned causal/qiyas source supplement.

    Policy associations provide searchable context, not new executable laws.
    The DOCX comparison is a dated audit; this call rechecks retained bytes.
    """
    return _replay(SUPPLEMENT_PATH, SUPPLEMENT_SHA256, root)


def _replay(metadata_path: Path, metadata_sha256: str, root: Path) -> dict:
    root = Path(root).resolve()
    try:
        raw = (root / metadata_path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != metadata_sha256:
            raise SourceInventoryError('SOURCE_REVIEW_CHANGED: installed inventory differs')
        inventory = json.loads(raw)
        sources = {}
        for source in inventory['sources']:
            path = (root / source['local_path']).resolve()
            if not path.is_relative_to(root):
                raise SourceInventoryError('SOURCE_OUTSIDE_ROOT: source path escapes repository')
            data = path.read_bytes()
            if len(data) != source['bytes'] or hashlib.sha256(data).hexdigest() != source['sha256']:
                raise SourceInventoryError('SOURCE_CHANGED: retained excerpt differs')
            sources[source['source_id']] = data
        for passage in inventory['passages']:
            data = sources[passage['source_id']]
            start, end = passage['start'], passage['end']
            if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(data):
                raise SourceInventoryError('PASSAGE_RANGE_INVALID: expected half-open byte range')
            selected = data[start:end]
            if hashlib.sha256(selected).hexdigest() != passage['sha256']:
                raise SourceInventoryError('PASSAGE_CHANGED: retained passage differs')
            passage['raw_text'] = selected.decode('utf-8')
        inventory['review_sha256'] = metadata_sha256
        inventory['replay'] = {
            'source_files': len(sources),
            'passages': len(inventory['passages']),
            'source_bytes_checked': sum(map(len, sources.values())),
            'retained_sources_checked': True,
            'original_books_rechecked': False,
            'theorem_references_compiled_here': False,
        }
        return inventory
    except (OSError, UnicodeError, KeyError, json.JSONDecodeError) as exc:
        raise SourceInventoryError('SOURCE_REPLAY_FAILED: retained review/source unreadable') from exc
