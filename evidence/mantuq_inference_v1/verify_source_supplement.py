"""Optional exact original DOCX replay; no book is downloaded by this command.

The original user-supplied DOCX is not distributed in git. A successful check
establishes byte correspondence, not printed-edition authenticity or meaning.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.mantuq_sources import build_supplement


def verify(docx: Path) -> dict:
    review = build_supplement()
    source = review['sources'][0]
    original = docx.read_bytes()
    artifact = source['original_artifact']
    if len(original) != artifact['bytes'] or hashlib.sha256(original).hexdigest() != artifact['sha256']:
        raise ValueError('ORIGINAL_CHANGED')
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    with zipfile.ZipFile(docx) as archive:
        body = ET.fromstring(archive.read('word/document.xml')).find('w:body', ns)
    if body is None:
        raise ValueError('DOCUMENT_BODY_MISSING')
    paragraphs = [''.join(t.text or '' for t in p.findall('.//w:t', ns)) + '\n'
                  for p in body.findall('.//w:p', ns)]
    raw = ''.join(paragraphs).encode()
    extraction = source['canonical_extraction']
    if (len(raw) != extraction['bytes'] or len(paragraphs) != extraction['paragraphs'] or
            hashlib.sha256(raw).hexdigest() != extraction['sha256']):
        raise ValueError('EXTRACTION_CHANGED')
    for passage in review['passages']:
        text = passage['raw_text']
        if (text != paragraphs[passage['paragraph'] - 1] or
                raw[passage['original_extraction_start']:passage['original_extraction_end']] != text.encode()):
            raise ValueError('SUPPLEMENT_PARAGRAPH_CHANGED')
    previous = json.loads((ROOT / 'evidence/mantuq_mafhum/sources.json').read_text())['sources'][2]
    for p in previous['spans']:
        if (paragraphs[p['paragraph'] - 1] != p['quote'] or
                raw[p['extraction_offset']:p['extraction_offset'] + len(p['quote'].encode())] != p['quote'].encode()):
            raise ValueError('PREVIOUS_PARAGRAPH_CHANGED')
    for section in review['chapter_audit']:
        selected = raw[section['original_extraction_start']:section['original_extraction_end']]
        if hashlib.sha256(selected).hexdigest() != section['sha256']:
            raise ValueError('CHAPTER_CHANGED')
    return dict(ok=True, original_sha256=artifact['sha256'], extraction_sha256=extraction['sha256'],
                previous_passages_checked=len(previous['spans']),
                supplementary_passages_checked=len(review['passages']),
                chapter_ranges_checked=len(review['chapter_audit']),
                printed_edition_authenticated=False, interpretation_adequacy_proved=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--docx', type=Path, required=True)
    print(json.dumps(verify(parser.parse_args().docx), ensure_ascii=False, indent=2))
