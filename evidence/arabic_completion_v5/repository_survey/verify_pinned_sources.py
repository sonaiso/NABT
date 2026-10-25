#!/usr/bin/env python3
"""Audit saved evidence, optionally re-fetch pinned public bytes; no credentials.

Default is offline. --content fetches selected files, --external fetches four
supplemental OpenITI blobs. --limit bounds selected content requests (0 = all).
Network operations are GET only. No repository files are changed by this script.
"""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent

def read(name):
    return json.loads((ROOT / name).read_text())

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'NABT-source-survey-verifier/1'})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()

def blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--content', action='store_true')
    parser.add_argument('--external', action='store_true')
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()
    if args.limit < 0:
        parser.error('--limit must be nonnegative')
    inv, index = read('inventory.json'), read('content_scan_index.json')
    trees = {}
    for row in inv['repositories_detail']:
        data = json.loads(gzip.decompress((ROOT / row['tree_file']).read_bytes()))
        if data['head_sha'] != row['head_sha'] or data['tree_sha'] != row['tree_sha']:
            raise ValueError('Pinned tree metadata mismatch: ' + row['repo'])
        if data['truncated'] or len(data['tree']) != row['tree_entries']:
            raise ValueError('Incomplete tree: ' + row['repo'])
        trees[row['repo']] = {x['path']: x for x in data['tree'] if x['type'] == 'blob'}
    for row in index:
        if trees[row['repo']][row['path']]['sha'] != row['blob_sha']:
            raise ValueError('Blob not in pinned tree: ' + row['path'])
        if row['scan_level'] == 'full-file-keyword-scan':
            if any(m['line'] < 1 or m['line'] > row['line_count'] for m in row['matches']):
                raise ValueError('Match outside line bounds: ' + row['path'])
    scanned = [r for r in index if r['scan_level'] == 'full-file-keyword-scan']
    if len(scanned) != inv['counts']['content_scanned_files']:
        raise ValueError('Content scan count mismatch')
    result = {'offline': 'pass', 'repositories': len(trees), 'scanned_files': len(scanned),
              'remote_content_verified': 0, 'remote_external_verified': 0, 'errors': []}
    if args.content:
        for r in scanned[:args.limit or None]:
            url = ('https://raw.githubusercontent.com/' + r['repo'] + '/' + r['commit'] +
                   '/' + urllib.parse.quote(r['path']))
            try:
                data = get(url)
                if blob_sha(data) != r['blob_sha']:
                    raise ValueError('Git blob SHA mismatch')
                if r.get('scan_input') == 'decompressed UTF-8 text':
                    if hashlib.sha256(data).hexdigest() != r['compressed_sha256']:
                        raise ValueError('Compressed SHA-256 mismatch')
                    data = gzip.decompress(data)
                if hashlib.sha256(data).hexdigest() != r['sha256']:
                    raise ValueError('Text SHA-256 mismatch')
                result['remote_content_verified'] += 1
            except Exception as exc:
                result['errors'].append({'path': r['path'], 'error': str(exc)})
    if args.external:
        for r in read('external_source_refs.json'):
            try:
                payload = json.loads(get(r['url']))
                data = base64.b64decode(payload['content'])
                if blob_sha(data) != r['blob'] or hashlib.sha256(data).hexdigest() != r['sha256']:
                    raise ValueError('External blob hash mismatch')
                result['remote_external_verified'] += 1
            except Exception as exc:
                result['errors'].append({'path': r['path'], 'error': str(exc)})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return bool(result['errors'])

if __name__ == '__main__':
    raise SystemExit(main())
