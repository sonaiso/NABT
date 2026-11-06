"""Awamil agent front door under the installed grammar catalogue CLI."""
from __future__ import annotations

from pathlib import Path
import re

from nabt.governors import installed_table, check_assignment
from tools.evidence_lifecycle_v1 import strict_loads
from .awamil import AwamilIndex, answer


def arguments(parser):
    parser.add_argument("action", choices=("catalog", "search", "answer", "curriculum", "train", "matrix", "check"))
    parser.add_argument("query", nargs="?")
    parser.add_argument("--collection", choices=("jurjani", "nabt", "relations"))
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--output", type=Path)


def _read(path, maximum):
    if path is None:
        raise ValueError("This action requires --request or --verify")
    with path.open("rb") as stream:
        return strict_loads(stream.read(maximum + 1), maximum_bytes=maximum)


def check(request):
    if type(request) is not dict or set(request) != {"factor_id", "assignments"}:
        raise ValueError("Supply factor_id and explicit role-code assignments only")
    factor = request["factor_id"]
    if type(factor) is not str or not re.fullmatch(r"nabt:(?:0[0-9]{2}|100)", factor) or factor == "nabt:000":
        raise ValueError("Conditional execution requires an installed nabt:001..100 identity")
    supplied = request["assignments"]
    if type(supplied) is not dict or any(type(k) is not str or not re.fullmatch(r"0|[1-9][0-9]?", k) for k in supplied):
        raise ValueError("Assignments must be a role-code object")
    if any(v is not None and (type(v) is not int or not 0 <= v <= 3) for v in supplied.values()):
        raise ValueError("Marks must be integers 0..3 or null")
    table = installed_table()
    entry = next(e for e in table.entries if e.row_id == int(factor.split(":")[1]))
    receipt = check_assignment(entry.class_code, {int(k): v for k, v in supplied.items()})
    return {"schema": "nabt.awamil-agent.case-check.v1", "factor_id": factor,
        "request": request, "owner": "nabt.governors.check_assignment", "result": receipt,
        "premise_origin": "CALLER_SUPPLIED_NOT_ACQUIRED_FROM_SENTENCE", "application_certified": False}


def run(args):
    if args.verify and args.action != "matrix":
        raise ValueError("--verify applies to matrix replay only")
    if args.action == "catalog":
        return AwamilIndex().catalog()
    if args.action in {"search", "answer"}:
        if args.query is None:
            raise ValueError("Expected a retrieval query")
        learner = None
        if args.model:
            from tools.lexical_training.awamil_agent import Learner
            learner = Learner(args.model)
        return (answer if args.action == "answer" else AwamilIndex().search)(
            args.query, limit=args.limit, collection=args.collection, learned=learner)
    if args.action in {"curriculum", "train"}:
        from tools.lexical_training.awamil_agent import curriculum, train
        if args.action == "curriculum":
            return curriculum()
        if args.run_dir is None:
            raise ValueError("Training requires a new --run-dir")
        return train(args.run_dir)
    request = _read(args.request, 2 * 1048576)
    if args.action == "check":
        return check(request)
    from .awamil_relations import matrix, verify_matrix
    if type(request) is not dict or not {"text"} <= request.keys() or set(request) - {"text", "lexical_text", "context"}:
        raise ValueError("Matrix requires text and optional lexical_text/context")
    if args.verify:
        return verify_matrix(_read(args.verify, 8 * 1048576), **request)
    return matrix(**request)
