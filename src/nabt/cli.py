"""JSON command line boundary for NABT; all authority remains in the package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from . import __version__
from .alphabet import ALPHABET_ID, LAW_ID, CARRIERS, HARAKAT, parse_word, render_word
from .certificates import issue_certificate, verify_certificate
from .codec import append_numbers, decode_number, encode_cells, pack_cells, replace_cell, split_number
from .errors import NabtError, resource_limit
from .machine import Machine, MAX_WEIGHT

MAX_JSON_BYTES = 262144


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise NabtError("INVALID_ARGUMENT", message)


def number(value: str) -> int:
    """Bound text before integer conversion; hex supports the whole codec domain."""
    if len(value) > 8192:
        raise resource_limit("Numeric input exceeds the command-line budget")
    if re.fullmatch(r"0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)", value):
        return int(value[2:], 16)
    if re.fullmatch(r"(?:0|[1-9][0-9]*)", value, flags=re.ASCII):
        if len(value) > 4000:
            raise resource_limit("Use hexadecimal for integers exceeding 4000 decimal digits")
        return int(value)
    raise NabtError("INVALID_NATURAL", "Expected a canonical non-negative decimal or 0x hexadecimal integer")


def numeric_payload(n: int) -> dict:
    cells = decode_number(n)
    return {"scope": "ENCODING_ONLY", "alphabet_id": ALPHABET_ID,
            "numeric_code": str(n) if n.bit_length() <= 12000 else None,
            "numeric_code_hex": hex(n), "cell_length": len(cells),
            "cells": list(cells), "text": render_word(cells)}


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise NabtError("DUPLICATE_JSON_KEY", f"Repeated JSON key: {key}")
        result[key] = value
    return result


def read_certificate(path: Path, maximum_bytes: int = MAX_JSON_BYTES):
    with path.open("rb") as stream:
        raw = stream.read(maximum_bytes + 1)
    if len(raw) > maximum_bytes:
        raise resource_limit("JSON document exceeds the byte budget", maximum_bytes=maximum_bytes)
    try:
        return json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=unique_keys,
                          parse_constant=lambda value: (_ for _ in ()).throw(
                              NabtError("INVALID_JSON", f"Non-JSON numeric constant: {value}")))
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, NabtError):
            raise
        raise NabtError("INVALID_JSON", "Certificate must be bounded, strict UTF-8 JSON") from exc


def parser() -> Parser:
    result = Parser(prog="nabt", description="Independent Arabic numerical shape kernel")
    result.add_argument("--version", action="version", version=__version__)
    sub = result.add_subparsers(dest="command", required=True, parser_class=Parser)
    for name in ("encode", "analyse", "certify", "rank", "effect"):
        command = sub.add_parser(name)
        command.add_argument("word", help="One exact word, with one supported mark on each carrier")
        if name in {"analyse", "certify", "rank"}:
            command.add_argument("--mode", choices=("waqf", "wasl"), default="waqf")
    decode = sub.add_parser("decode")
    decode.add_argument("number")
    for name in ("count", "generate"):
        command = sub.add_parser(name)
        command.add_argument("--weight", required=True)
        command.add_argument("--mode", choices=("waqf", "wasl"), default="waqf")
        if name == "generate":
            command.add_argument("--rank", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("certificate", type=Path)
    for name in ("compile", "run", "verify-run"):
        command = sub.add_parser(name)
        command.add_argument("document", type=Path)
    execute = sub.add_parser("execute")
    execute.add_argument("program_number")
    transcode = sub.add_parser("transcode")
    transcode.add_argument("number")
    transcode.add_argument("--from-codec", required=True)
    transcode.add_argument("--to-codec", required=True)
    sub.add_parser("pilot")
    append = sub.add_parser("append")
    append.add_argument("left")
    append.add_argument("right")
    split = sub.add_parser("split")
    split.add_argument("number")
    split.add_argument("--at", required=True, help="Number of cells in the left part")
    replace = sub.add_parser("replace")
    replace.add_argument("number")
    replace.add_argument("--at", required=True, help="Zero-based cell position")
    replace.add_argument("--cell", required=True)
    sub.add_parser("law")
    return result


def run(args) -> tuple[dict, int]:
    # argparse catches ValueError from type converters. NabtError derives from
    # ValueError, so conversion here preserves RESOURCE_LIMIT as DEFER.
    for field in ("number", "left", "right", "weight", "rank", "at", "cell"):
        if hasattr(args, field):
            setattr(args, field, number(getattr(args, field)))
    command = args.command
    if command in {"compile", "run", "execute", "verify-run", "pilot"}:
        from .program import Program, compile_request, execute_program, verify_execution
        if command == "verify-run":
            from .program import MAX_RECEIPT_BYTES
            report = verify_execution(read_certificate(args.document, MAX_RECEIPT_BYTES))
            return report, 0 if report["valid"] else (3 if report["status"] == "DEFER" else 2)
        if command == "pilot":
            from .learning import default_pilot
            try:
                records = default_pilot().observed_records()
            except NabtError:
                raise
            except (ValueError, KeyError) as error:
                raise NabtError(
                    "INSTALLED_CONTRACT_FAILED",
                    "Installed source contract could not be replayed",
                    status="DEFER",
                ) from error
            events = [{"op": "observe", "record_id": row.record_id} for row in records]
            events += [{"op": "query", "cue": ["مررت", "ب"], "query_id": "comparison"},
                       {"op": "withdraw", "record_id": records[2].record_id},
                       {"op": "query", "cue": ["مررت", "ب"], "query_id": "comparison"},
                       {"op": "observe", "record_id": records[2].record_id},
                       {"op": "query", "cue": ["مررت", "ب"], "query_id": "comparison"},
                       {"op": "query", "cue": ["إشارة جديدة"], "query_id": "unresolved"}]
            program = compile_request({"task": "source_learning", "events": events})
        elif command == "execute":
            # Program wire permits larger hex than the word-number CLI. Bound
            # before parsing; decimal program numbers are deliberately excluded.
            from .program import MAX_PROGRAM_BYTES
            encoded = args.program_number
            if len(encoded) > 2 * (MAX_PROGRAM_BYTES + 1) + 2:
                raise resource_limit("Program number exceeds the wire budget")
            if not re.fullmatch(r"0x[1-9a-f][0-9a-f]*", encoded):
                raise NabtError("NONCANONICAL_PROGRAM_NUMBER", "Use canonical lowercase 0x program number")
            program = Program.from_number(int(encoded[2:], 16))
        else:
            program = compile_request(read_certificate(args.document))
        if command == "compile":
            return program.packet(), 0
        receipt = execute_program(program)
        return receipt, (0 if receipt["run_status"] == "COMPLETED" else
                         3 if receipt["result"].get("status") == "DEFER" else 2)
    if command == "transcode":
        from .bridges import convert_number
        return convert_number(args.number, args.from_codec, args.to_codec).as_dict(), 0
    if command == "law":
        machine = Machine()
        return {"version": __version__, "alphabet_id": ALPHABET_ID, "law_id": LAW_ID,
                "table_sha256": machine.table_sha256, "carriers": list(CARRIERS),
                "marks": list(HARAKAT), "state_count": 97, "alphabet_size": 116,
                "maximum_consonant_weight": MAX_WEIGHT,
                "scope": "WORD_SHAPE; no lexical or semantic assertion"}, 0
    if command == "verify":
        report = verify_certificate(read_certificate(args.certificate))
        return report.as_dict(), 0 if report.valid else (3 if report.status == "DEFER" else 2)
    if command == "decode":
        return numeric_payload(args.number), 0
    if command == "append":
        return numeric_payload(append_numbers(args.left, args.right)), 0
    if command == "split":
        left, right = split_number(args.number, args.at)
        return {"left": numeric_payload(left), "right": numeric_payload(right)}, 0
    if command == "replace":
        return numeric_payload(replace_cell(args.number, args.at, args.cell)), 0
    if command in {"count", "generate"}:
        machine = Machine(args.mode)
        if command == "count":
            return {"law_id": LAW_ID, "mode": args.mode, "start_state": 0,
                    "consonant_weight": args.weight, "count": str(machine.count(args.weight)),
                    "scope": "NUMBER_OF_SHAPES_IN_DECLARED_LAW"}, 0
        cells = machine.unrank(args.weight, args.rank)
        return issue_certificate(cells, args.mode), 0
    cells = parse_word(args.word)
    if command == "encode":
        result = numeric_payload(encode_cells(cells))
        result["wire_hex"] = pack_cells(cells).hex()
        return result, 0
    if command == "effect":
        return Machine().effect(cells).as_dict(), 0
    if command == "certify":
        return issue_certificate(cells, args.mode, source_text=args.word), 0
    machine = Machine(args.mode)
    if command == "rank":
        result = numeric_payload(encode_cells(cells))
        result.update({"scope": "LICENSED_SHAPE_RANK", "law_id": LAW_ID,
                       "mode": args.mode, "rank": str(machine.rank(cells))})
        return result, 0
    result = machine.analyse(cells)
    return result.as_dict(), 0 if result.licensed else 2


def main(argv=None) -> int:
    try:
        result, code = run(parser().parse_args(argv))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except NabtError as exc:
        print(json.dumps(exc.as_dict(), ensure_ascii=False), file=sys.stderr)
        return 3 if exc.status == "DEFER" else 2
    except OSError as exc:
        print(json.dumps({"status": "DEFER", "code": "IO_ERROR", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
