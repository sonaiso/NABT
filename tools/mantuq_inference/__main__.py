"""Command-line research adapter; text search never supplies logical premises."""
import argparse
import json
from pathlib import Path

from . import EvaluationBudget, build_inventory, evaluate


def _source_parsers(sub):
    """Extend the current entry point without changing the legacy operations."""
    for name in ("source", "fold", "verify-fold"):
        command = sub.add_parser(name)
        command.add_argument("source", type=Path)
        command.add_argument("query_file", type=Path)
        if name == "verify-fold":
            command.add_argument("packet", type=Path)
        command.add_argument("--plan", type=Path, required=True)
        command.add_argument("--source-id", default="text")
        command.add_argument("--revision", default="1")
        command.add_argument("--scope", default="default")
        command.add_argument("--context", default="unspecified")
        command.add_argument("--time", default="unspecified")
        command.add_argument("--max-readings", type=int, default=64)
        command.add_argument("--max-hypotheses", type=int, default=128)
        command.add_argument("--max-total-atoms", type=int, default=2048)
        command.add_argument("--timeout", type=int, default=20,
                             help="integer seconds per native call (1..60)")
        command.add_argument("--checker", type=Path,
                             help="trusted native verifiedReading executable")
        command.add_argument("--semantic-probe", type=Path,
                             help="trusted native classicalSemanticProbe executable")
        command.add_argument("--output", type=Path, required=name == "fold",
                             help="create a new file; existing paths are never overwritten")
    command = sub.add_parser("unfold")
    command.add_argument("packet", type=Path)
    command.add_argument("--output", type=Path, required=True,
                         help="restore untrusted data into a new file")


def _source_main(args):
    from tools.explainable_pilot import PilotError, read_bounded
    from .source_bound import evaluate_source
    from .source_fold import (MAX_ENVELOPE_BYTES, bounded_wire, strict_input,
                              fold_source, unfold_source, verify_fold)
    from hashlib import sha256

    try:
        if args.operation == "unfold":
            packet = strict_input(read_bounded(args.packet, MAX_ENVELOPE_BYTES),
                                  maximum=MAX_ENVELOPE_BYTES)
            out = {"schema": "nabt.mantuq-source-unfolded.v1", "status": "DECODED_UNVERIFIED",
                   "verified": False, "result": unfold_source(packet),
                   "requires_source_replay": True, "conditional_consequence": False,
                   "world_truth_established": False, "action_authority": "NONE"}
        else:
            raw = read_bounded(args.source, 65536)
            query = read_bounded(args.query_file, 8192)
            plan = strict_input(read_bounded(args.plan, 1048576), maximum=1048576)
            options = {"source_id": args.source_id, "revision": args.revision,
                       "scope": args.scope, "context": args.context, "time": args.time,
                       "budget": EvaluationBudget(max_readings=args.max_readings,
                                                  max_hypotheses=args.max_hypotheses,
                                                  max_total_atoms=args.max_total_atoms),
                       "timeout": args.timeout, "checker": args.checker,
                       "semantic_probe": args.semantic_probe}
            if args.operation == "source":
                out = evaluate_source(raw, query, plan, **options)
            elif args.operation == "fold":
                out = fold_source(raw, query, plan, **options)
            else:
                packet = strict_input(read_bounded(args.packet, MAX_ENVELOPE_BYTES),
                                      maximum=MAX_ENVELOPE_BYTES)
                out = verify_fold(raw, query, plan, packet, **options)
        encoded = bounded_wire(out, MAX_ENVELOPE_BYTES) + b"\n"
        if args.output is not None:
            # Encode and check the complete result before creating a destination.
            # Exclusive creation protects existing user files and prior evidence.
            with args.output.open("xb") as stream:
                stream.write(encoded)
            print(json.dumps({"schema": "nabt.mantuq-source-output.v1",
                              "operation": args.operation, "output": str(args.output),
                              "sha256": sha256(encoded).hexdigest(),
                              "status": out.get("status", "FOLDED_TRANSPORT"),
                              "conditional_consequence": out.get("conditional_consequence", False),
                              "world_truth_established": False}, ensure_ascii=False))
        else:
            print(encoded.decode("utf-8"), end="")
        return 0 if out.get("status") not in {
            "INVALID", "OUTSIDE_VERIFIED_LANGUAGE", "SOURCE_ERROR",
            "RESOURCE_EXHAUSTED", "VERIFICATION_UNAVAILABLE",
        } else 2
    except (PilotError, ValueError, OSError) as error:
        code = getattr(error, "code", "IO_ERROR" if isinstance(error, OSError) else "INVALID_INPUT")
        print(json.dumps({"schema": "nabt.mantuq-source-error.v1", "status": code,
                          "reason": str(error), "verified": False,
                          "conditional_consequence": False, "world_truth_established": False,
                          "all_arabic_complete": False, "action_authority": "NONE"},
                         ensure_ascii=False, allow_nan=False))
        return 2


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON object key: " + key)
        out[key] = value
    return out


def _load(path):
    raw = path.read_bytes()
    if len(raw) > 1048576:
        raise ValueError("request exceeds one MiB")
    return json.loads(raw, object_pairs_hook=_unique,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError("nonfinite JSON number")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    sub.add_parser("catalogue")
    run = sub.add_parser("evaluate")
    run.add_argument("request", type=Path)
    run.add_argument("--max-readings", type=int, default=64)
    find = sub.add_parser("search")
    find.add_argument("query")
    find.add_argument("--limit", type=int, default=10)
    pipeline = sub.add_parser("pipeline")
    pipeline.add_argument("query")
    pipeline.add_argument("requests", type=Path, help="object mapping installed policy IDs to explicit requests")
    pipeline.add_argument("--limit", type=int, default=10, help="displayed retrieval candidates only")
    pipeline.add_argument("--max-policies", type=int)
    _source_parsers(sub)
    args = parser.parse_args()
    if args.operation in {"source", "fold", "unfold", "verify-fold"}:
        return _source_main(args)
    if args.operation == "catalogue":
        out = build_inventory()
    elif args.operation == "search":
        from .retrieval import search
        out = search(args.query, limit=args.limit)
    else:
        try:
            if args.operation == "pipeline":
                from .pipeline import run
                out = run(args.query, _load(args.requests), display_limit=args.limit, max_policies=args.max_policies)
            else:
                out = evaluate(_load(args.request), budget=EvaluationBudget(max_readings=args.max_readings))
        except (ValueError, OSError) as exc:
            out = {"status": "INVALID", "reason": str(exc), "conditional_consequence": False,
                   "all_arabic_complete": False, "world_truth_established": False}
    print(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if out.get("status") not in {"INVALID", "SOURCE_ERROR", "VERIFICATION_UNAVAILABLE"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
