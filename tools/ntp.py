"""NTP user entry; all output is an existing gateway receipt or verification."""
import argparse
import json
from pathlib import Path
import sys

from tools.grammar_catalog import gateway
from tools.grammar_catalog.ntp import request
from tools.evidence_lifecycle_v1 import strict_loads


def main():
    parser = argparse.ArgumentParser(description='NTP: one NABT input/output entry')
    parser.add_argument('action', choices=('run', 'verify', 'read', 'forward', 'catalog'))
    parser.add_argument('--request', type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--text')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'catalog':
        if args.request or args.receipt or args.text is not None:
            parser.error('catalog accepts no request, receipt or text')
        result = gateway.catalog()
    else:
        if args.action in ('read', 'forward'):
            if args.request or args.receipt: parser.error('use --text for read/forward')
            req = request('think' if args.action == 'read' else 'forward',
                          {'text': args.text if args.text is not None else sys.stdin.read()})
        else:
            if not args.request or args.text is not None:
                parser.error('run/verify require --request and no --text')
            with args.request.open('rb') as source:
                req = gateway.request_from_bytes(source.read(gateway.MAX_REQUEST + 1))
            if req['route'] != 'ntp': parser.error('NTP requests require route=ntp')
            if (args.action == 'verify') != (args.receipt is not None):
                parser.error('verify requires --receipt; run accepts none')
        if args.action == 'verify':
            with args.receipt.open('rb') as source:
                report = strict_loads(source.read(8 * 1048576 + 1), maximum_bytes=8 * 1048576, report=True)
            result = gateway.accept_output(report, expected_request=req)
        else:
            result = gateway.run(req)
        # Consumers still need independent verification of run/read/forward.
    raw = json.dumps(result, ensure_ascii=False, sort_keys=True) + '\n'
    if args.output: args.output.write_text(raw)
    else: print(raw, end='')
    if args.action == 'verify': return 0 if result['valid'] else 2
    return 0 if result.get('status', 'EXECUTED') == 'EXECUTED' else 3


if __name__ == '__main__':
    raise SystemExit(main())
