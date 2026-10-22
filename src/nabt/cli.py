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


def read_certificate(path: Path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES:
        raise resource_limit("Certificate file exceeds the byte budget", maximum_bytes=MAX_JSON_BYTES)
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
