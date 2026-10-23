import argparse
import hashlib
import json
import time
from pathlib import Path

from .integrity import require_output, verify_code_freeze, verify_published_inputs, write_report

ROOT=Path(__file__).resolve().parents[2]
PRIVATE=ROOT/'evidence/text_inquiry'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--code-freeze',required=True,type=Path)
    args=ap.parse_args()
    require_output(args.output, data=PRIVATE, freeze=args.code_freeze)
    verify_published_inputs(PRIVATE)
    protocol=json.loads((PRIVATE/'natural_probe_protocol.json').read_text())
    path=PRIVATE/protocol['source_manifest']
    assert sha(path.read_bytes())==protocol['source_manifest_sha256']
    manifest=json.loads(path.read_text())
    code=verify_code_freeze(args.code_freeze)
    from nabt.text_reader import parse_document
    from nabt.semantics import SemanticKernel
    results=[]
    for record in manifest['records']:
        started=time.perf_counter()
        raw=(ROOT/record['path']).read_bytes()
        assert sha(raw)==record['source_sha256'] and len(raw)==record['source_bytes']
        excerpt=raw[record['start']:record['end']]
        assert sha(excerpt)==record['span_sha256'] and excerpt.decode('utf-8')==record['text']
        errors=[]
        details={}
        try:
            doc=parse_document(excerpt,source_id='book_probe',scope='natural')
            restored=b''.join(segment.span.extract(doc.source) for segment in doc.segments)
            admission=SemanticKernel().add_document(doc).as_dict()
            details={'reader_accepted':doc.accepted,'kernel_admitted':admission['accepted'],
                     'residuals':[r.as_dict() for r in doc.residuals],
                     'raw_bytes_preserved':doc.source.raw_bytes==excerpt,
                     'segment_restoration_exact':restored==excerpt,
                     'admission':admission}
            if doc.accepted or admission['accepted']:
                errors.append('unexpected_admission_requires_semantic_review')
            if not doc.residuals:
                errors.append('no_named_residual')
            if doc.source.raw_bytes!=excerpt or restored!=excerpt:
                errors.append('source_byte_loss')
        except Exception as exc:
            details={'exception':{'type':type(exc).__name__,'message':str(exc)}}
            errors.append('unexpected_exception')
        elapsed=time.perf_counter()-started
        if elapsed>protocol['episode_budget_seconds']:
            errors.append('budget_exceeded')
        results.append({'id':record['id'],'source_id':record['source_id'],'start':record['start'],'end':record['end'],
                        'span_sha256':record['span_sha256'],'safety_passed':not errors,'elapsed_seconds':elapsed,'errors':errors,**details})
    summary={'raw_book_spans':len(results),'safety_passed':sum(r['safety_passed'] for r in results),
             'fully_admitted':sum(r.get('reader_accepted',False) and r.get('kernel_admitted',False) for r in results),
             'semantic_successes_confirmed':0,
             'semantic_coverage_denominator':len(results),
             'note':'A safe unsupported result contributes zero semantic coverage. Any unexpected admission needs independent semantic review.'}
    output={'schema':'nabt-independent-natural-source-results-v1','protocol':protocol,'code_freeze':code,'summary':summary,'results':results}
    write_report(args.output, output, data=PRIVATE, freeze=args.code_freeze)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
