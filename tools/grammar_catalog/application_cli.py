from pathlib import Path
from tools.arabic_training.unit_composition import read_json,MAX_REPORT,wire
from . import application,temporal

def arguments(parser):
    parser.add_argument('action',choices=('analyze','temporal','proofs'))
    parser.add_argument('--request',type=Path)
    parser.add_argument('--verify',type=Path)
    parser.add_argument('--output',type=Path)

def read(path):
    if path is None:raise ValueError('This action requires --request')
    with path.open('rb') as f:return read_json(f.read(MAX_REPORT+1))

def run(args):
    if args.action=='proofs':
        if args.request or args.verify:raise ValueError('proofs takes no caller evidence')
        return application.proof_links()
    owner=temporal if args.action=='temporal' else application
    request=read(args.request)
    result=(owner.verify(read(args.verify),expected_request=request) if args.verify else
            (owner.evaluate(request) if args.action=='temporal' else owner.analyze(request)))
    wire(result)
    return result
