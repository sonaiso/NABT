"""Composition agent under the existing grammar catalogue CLI."""
from pathlib import Path


def arguments(parser):
    parser.add_argument("action",choices=("catalog","search","curriculum","run"))
    parser.add_argument("query",nargs="?")
    parser.add_argument("--summary",action="store_true")
    parser.add_argument("--limit",type=int,default=10)
    parser.add_argument("--request",type=Path)
    parser.add_argument("--verify",type=Path)
    parser.add_argument("--output",type=Path)


def run(args):
    from . import unit_catalog
    from tools.arabic_training.unit_composition import execute, verify, read_json, MAX_REPORT
    def read(path, *, report=False):
        if path is None: raise ValueError("This action requires --request")
        with path.open("rb") as stream: return read_json(stream.read(MAX_REPORT+1))
    if args.verify and args.action != "run":
        raise ValueError("--verify applies to units run")
    if args.action == "catalog":
        data = unit_catalog.catalog()
        return {k:v for k,v in data.items() if k != "cards"} if args.summary else data
    if args.action == "search":
        if args.query is None: raise ValueError("Supply a unit RAG query")
        return unit_catalog.search(args.query,args.limit)
    if args.action == "curriculum": return unit_catalog.curriculum()
    request = read(args.request)
    return verify(read(args.verify,report=True),expected_request=request) if args.verify else execute(request)
