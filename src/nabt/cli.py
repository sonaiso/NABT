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
    word_reader = sub.add_parser("read-words")
    word_reader.add_argument("document", type=Path)
    word_reader.add_argument("--scope", default="default")
    word_reader.add_argument("--with-number", action="store_true")
    word_verifier = sub.add_parser("verify-words")
    word_verifier.add_argument("report", type=Path)
    word_verifier.add_argument("--source", type=Path, help="Bind replay to these expected source bytes")
    word_verifier.add_argument("--scope", default=None, help="Bind replay to this expected scope")
    morphology_reader = sub.add_parser("read-morphology")
    morphology_reader.add_argument("document", type=Path)
    morphology_reader.add_argument("--scope", default="default")
    morphology_reader.add_argument("--with-number", action="store_true")
    morphology_verifier = sub.add_parser("verify-morphology")
    morphology_verifier.add_argument("report", type=Path)
    morphology_verifier.add_argument("--source", type=Path, required=True)
    morphology_verifier.add_argument("--scope", default="default")
    text_morphology = sub.add_parser("read-text-morphology")
    text_morphology.add_argument("document", type=Path)
    text_morphology.add_argument("--scope", default="default")
    text_morphology.add_argument("--lexical-source", type=Path)
    text_morphology.add_argument("--with-number", action="store_true")
    text_morphology_verifier = sub.add_parser("verify-text-morphology")
    text_morphology_verifier.add_argument("report", type=Path)
    text_morphology_verifier.add_argument("--source", type=Path, required=True)
    text_morphology_verifier.add_argument("--scope", default="default")
    text_morphology_verifier.add_argument("--lexical-source", type=Path)
    sub.add_parser("derivation-catalog")
    derivation_generator = sub.add_parser("generate-derivation")
    derivation_generator.add_argument("root")
    derivation_generator.add_argument("pattern")
    derivation_generator.add_argument("--ending", default="")
    for name in ("read-derivation", "read-verb-paradigm"):
        command = sub.add_parser(name)
        command.add_argument("document", type=Path)
        command.add_argument("--scope", default="default")
        if name == "read-derivation":
            command.add_argument("--profile", choices=("stem_exact_v1", "surface_v1"), default="surface_v1")
            command.add_argument("--with-number", action="store_true")
    for name in ("verify-derivation", "verify-verb-paradigm"):
        command = sub.add_parser(name)
        command.add_argument("report", type=Path)
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--scope", default="default")
        if name == "verify-derivation":
            command.add_argument("--profile", choices=("stem_exact_v1", "surface_v1"), default="surface_v1")
    sub.add_parser("nominal-catalog")
    sub.add_parser("inflection-catalog")
    corpus_audit = sub.add_parser("audit-corpus")
    corpus_audit.add_argument("document", type=Path)
    corpus_audit.add_argument("--format", choices=("qac", "masaq-ar", "masaq-en"), required=True)
    learn_qac = sub.add_parser("learn-qac-lexicon")
    learn_qac.add_argument("document", type=Path)
    learn_qac.add_argument("--exclude-verse", action="append", default=[])
    for name in ("read-inflection", "verify-inflection"):
        command = sub.add_parser(name)
        command.add_argument("document", type=Path)
        command.add_argument("--qac", type=Path, help="Original QAC TSV (optionally gzip); labels for case/mood are masked")
        command.add_argument("--exclude-verse", action="append", default=[])
        command.add_argument("--scope", default="default")
        if name == "verify-inflection":
            command.add_argument("--source", type=Path, required=True)
    weak = sub.add_parser("weak-root-profile")
    weak.add_argument("root")
    cardinal = sub.add_parser("number-rule")
    cardinal.add_argument("quantity")
    cardinal.add_argument("singular_gender", choices=("masculine", "feminine"))
    for name in ("read-nominal", "read-nominal-facts", "count-source-units", "read-count-phrase"):
        command = sub.add_parser(name)
        command.add_argument("document", type=Path)
        command.add_argument("--scope", default="default")
        if name in {"read-nominal", "read-count-phrase"}:
            command.add_argument("--lexical-source", type=Path)
        if name == "read-nominal":
            command.add_argument("--with-number", action="store_true")
    for name in ("verify-nominal", "verify-nominal-facts", "verify-source-count", "verify-count-phrase"):
        command = sub.add_parser(name)
        command.add_argument("report", type=Path)
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--scope", default="default")
        if name in {"verify-nominal", "verify-count-phrase"}:
            command.add_argument("--lexical-source", type=Path)
    for name in ("read-text", "ask-text", "read-arabic", "ask-arabic", "read-governors", "ask-governors"):
        command = sub.add_parser(name)
        command.add_argument("document", type=Path)
        command.add_argument("--scope", default="default")
        if name in {"read-arabic", "read-governors"}:
            command.add_argument("--with-number", action="store_true", help="Include reversible source-replayed reading number")
        if name in {"ask-text", "ask-arabic", "ask-governors"}:
            command.add_argument("question", help="One question in the declared Arabic text language")
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
    if command in {"inflection-catalog", "audit-corpus", "learn-qac-lexicon", "read-inflection", "verify-inflection"}:
        from .inflection import inflection_catalog
        from .corpus_sources import read_corpus
        from .corpus_evidence import learn_qac_lexicon, MAX_CORPUS_BYTES
        from .inflection_reader import read_inflection, verify_inflection, MAX_REPORT_BYTES
        def corpus_bytes(path):
            import gzip
            opener = gzip.open if path.suffix == ".gz" else open
            with opener(path, "rb") as stream:
                raw = stream.read(MAX_CORPUS_BYTES + 1)
            if len(raw) > MAX_CORPUS_BYTES:
                raise resource_limit("Corpus exceeds the declared byte budget")
            return raw
        if command == "inflection-catalog":
            return inflection_catalog(), 0
        if command == "audit-corpus":
            result = read_corpus(corpus_bytes(args.document), format=args.format)
            return {k: result[k] for k in ("schema", "format", "source", "summary", "authority")}, 0
        if command == "learn-qac-lexicon":
            return learn_qac_lexicon(corpus_bytes(args.document), excluded_verses=tuple(args.exclude_verse)).summary(), 0
        if args.exclude_verse and args.qac is None:
            raise NabtError("INVALID_CORPUS_EXCLUSIONS", "Exclusions require an explicit QAC source")
        model = None if args.qac is None else learn_qac_lexicon(corpus_bytes(args.qac), excluded_verses=tuple(args.exclude_verse))
        if command == "verify-inflection":
            result = verify_inflection(read_certificate(args.document, MAX_REPORT_BYTES),
                                       text=args.source.read_bytes(), lexical_model=model, scope=args.scope)
            return result, 0 if result["valid"] else 3 if result["status"] == "DEFER" else 2
        result = read_inflection(args.document.read_bytes(), lexical_model=model, scope=args.scope)
        return result, 0 if result["status"] == "LICENSED_READINGS" else 3
    if command in {"nominal-catalog", "weak-root-profile", "number-rule"}:
        from .nominal import nominal_catalog, weak_root_profile, number_rule
        if command == "nominal-catalog":
            return nominal_catalog(), 0
        if command == "weak-root-profile":
            return weak_root_profile(args.root), 0
        return number_rule(number(args.quantity), args.singular_gender), 0
    if command in {"read-nominal", "verify-nominal", "read-nominal-facts", "verify-nominal-facts",
                   "count-source-units", "verify-source-count", "read-count-phrase", "verify-count-phrase"}:
        from .nominal import (MAX_REPORT_BYTES, NUMBER_DOMAIN, nominal_number,
                              read_nominal, verify_nominal, read_nominal_facts, verify_nominal_facts)
        from .counting import (count_source_units, verify_source_count, read_count_phrase, verify_count_phrase)
        from .word_reader import MAX_SOURCE_BYTES
        verifying = command.startswith("verify-")
        path = args.source if verifying else args.document
        with path.open("rb") as handle:
            raw = handle.read(MAX_SOURCE_BYTES + 1)
        if len(raw) > MAX_SOURCE_BYTES:
            raise resource_limit("Nominal source exceeds its byte budget")
        options = {"scope": args.scope}
        if command in {"read-nominal", "verify-nominal", "read-count-phrase", "verify-count-phrase"}:
            lexical = None
            if args.lexical_source is not None:
                with args.lexical_source.open("rb") as handle:
                    lexical = handle.read(MAX_SOURCE_BYTES + 1)
                if len(lexical) > MAX_SOURCE_BYTES:
                    raise resource_limit("Nominal assertions exceed their byte budget")
            # Explicit None withdraws a lexical premise, including on verification.
            options.update(lexical_text=lexical, lexical_source_id="nominal_lexicon")
        if command in {"read-nominal", "verify-nominal"}:
            reader, verifier, source_id = read_nominal, verify_nominal, "input"
        elif command in {"read-nominal-facts", "verify-nominal-facts"}:
            reader, verifier, source_id = read_nominal_facts, verify_nominal_facts, "nominal_lexicon"
        elif command in {"count-source-units", "verify-source-count"}:
            reader, verifier, source_id = count_source_units, verify_source_count, "count"
        else:
            reader, verifier, source_id = read_count_phrase, verify_count_phrase, "count_phrase"
        options["source_id"] = source_id
        if verifying:
            result = verifier(read_certificate(args.report, MAX_REPORT_BYTES), text=raw, **options)
            return result, 0 if result["valid"] else 3 if result["status"] == "DEFER" else 2
        report = reader(raw, **options)
        code = 0 if report["status"] == "READ" else 3 if report["status"] == "DEFER" else 2
        if getattr(args, "with_number", False):
            return {"report": report, "encoding": {"domain": NUMBER_DOMAIN,
                    "number_hex": hex(nominal_number(report)), "authority": "ENCODING_ONLY"}}, code
        return report, code
    if command == "derivation-catalog":
        from .derivation import pattern_catalog
        return pattern_catalog(), 0
    if command == "generate-derivation":
        from .derivation import generate_derivation
        return generate_derivation(args.root, args.pattern, ending=args.ending), 0
    if command in {"read-derivation", "verify-derivation", "read-verb-paradigm", "verify-verb-paradigm"}:
        from .derivation import (MAX_SOURCE_BYTES, MAX_REPORT_BYTES, NUMBER_DOMAIN,
                                 read_derivation, verify_derivation, derivation_number)
        from .verb_paradigm import read_verb_paradigm, verify_verb_paradigm
        verifying = command.startswith("verify-")
        path = args.source if verifying else args.document
        with path.open("rb") as handle:
            raw = handle.read(MAX_SOURCE_BYTES + 1)
        if len(raw) > MAX_SOURCE_BYTES:
            raise resource_limit("Derivation source exceeds its byte budget")
        options = {"source_id": "input", "scope": args.scope}
        if command.endswith("derivation"):
            options["profile"] = args.profile
            reader, verifier = read_derivation, verify_derivation
        else:
            reader, verifier = read_verb_paradigm, verify_verb_paradigm
        if verifying:
            result = verifier(read_certificate(args.report, MAX_REPORT_BYTES), text=raw, **options)
            return result, 0 if result["valid"] else 3 if result["status"] == "DEFER" else 2
        report = reader(raw, **options)
        code = 0 if report["status"] == "READ" else 3 if report["status"] == "DEFER" else 2
        if getattr(args, "with_number", False):
            return {"report": report, "encoding": {"domain": NUMBER_DOMAIN,
                    "number_hex": hex(derivation_number(report)), "authority": "ENCODING_ONLY"}}, code
        return report, code
    if command in {"read-text-morphology", "verify-text-morphology"}:
        from .text_morphology import (MAX_SOURCE_BYTES, MAX_REPORT_BYTES, NUMBER_DOMAIN,
                                      read_text_morphology, verify_text_morphology, text_morphology_number)
        from .morphology_reader import MAX_SOURCE_BYTES as MAX_LEXICAL_BYTES
        path = args.document if command == "read-text-morphology" else args.source
        with path.open("rb") as handle:
            raw = handle.read(MAX_SOURCE_BYTES + 1)
        if len(raw) > MAX_SOURCE_BYTES:
            raise resource_limit("Text morphology source exceeds its byte budget")
        lexical = None
        if args.lexical_source is not None:
            with args.lexical_source.open("rb") as handle:
                lexical = handle.read(MAX_LEXICAL_BYTES + 1)
            if len(lexical) > MAX_LEXICAL_BYTES:
                raise resource_limit("Lexical source exceeds its byte budget")
        if command == "verify-text-morphology":
            # Explicit None binds the expected absence of lexical premises.
            result = verify_text_morphology(read_certificate(args.report, MAX_REPORT_BYTES),
                text=raw, source_id="input", scope=args.scope, lexical_text=lexical,
                lexical_source_id="lexical")
            return result, 0 if result["valid"] else 3 if result["status"] == "DEFER" else 2
        report = read_text_morphology(raw, source_id="input", scope=args.scope, lexical_text=lexical)
        code = 0 if report["status"] == "READ" else 3 if report["status"] == "DEFER" else 2
        if args.with_number:
            return {"reading": report, "encoding": {"domain": NUMBER_DOMAIN,
                    "number_hex": hex(text_morphology_number(report)), "authority": "ENCODING_ONLY"}}, code
        return report, code
    if command in {"read-morphology", "verify-morphology"}:
        from .morphology_reader import (MAX_SOURCE_BYTES, MAX_REPORT_BYTES, NUMBER_DOMAIN,
                                        read_morphology, verify_morphology, morphology_number)
        path = args.document if command == "read-morphology" else args.source
        with path.open("rb") as handle:
            raw = handle.read(MAX_SOURCE_BYTES + 1)
        if len(raw) > MAX_SOURCE_BYTES:
            raise resource_limit("Morphology source exceeds its byte budget")
        if command == "verify-morphology":
            report = verify_morphology(read_certificate(args.report, MAX_REPORT_BYTES),
                                       text=raw, source_id="input", scope=args.scope)
            return report, 0 if report["valid"] else 3 if report["status"] == "DEFER" else 2
        report = read_morphology(raw, source_id="input", scope=args.scope)
        code = 0 if report["status"] == "READ" else 3 if report["status"] == "DEFER" else 2
        if args.with_number:
            return {"reading": report, "encoding": {"domain": NUMBER_DOMAIN,
                    "number_hex": hex(morphology_number(report)), "authority": "ENCODING_ONLY"}}, code
        return report, code
    if command in {"read-words", "verify-words"}:
        from .word_reader import (MAX_SOURCE_BYTES, MAX_REPORT_BYTES, NUMBER_DOMAIN,
                                  read_words, verify_word_reading, word_reading_number)
        expected = None
        path = args.document if command == "read-words" else args.source
        if path is not None:
            with path.open("rb") as handle:
                expected = handle.read(MAX_SOURCE_BYTES + 1)
            if len(expected) > MAX_SOURCE_BYTES:
                raise resource_limit("Word source exceeds its byte budget")
        if command == "verify-words":
            report = verify_word_reading(read_certificate(args.report, MAX_REPORT_BYTES),
                                         source=expected, scope=args.scope)
            return report, 0 if report["valid"] else (3 if report["status"] == "DEFER" else 2)
        report = read_words(expected, source_id="input", scope=args.scope)
        if args.with_number:
            # The packet wraps the replayed report; it is not part of that
            # report and does not grant additional linguistic authority.
            return {"reading": report, "encoding": {"domain": NUMBER_DOMAIN,
                    "number_hex": hex(word_reading_number(report)), "authority": "ENCODING_ONLY"}}, (0 if report["status"] == "READ" else 3 if report["status"] == "DEFER" else 2)
        return report, 0 if report["status"] == "READ" else 3 if report["status"] == "DEFER" else 2
    if command in {"read-text", "ask-text", "read-arabic", "ask-arabic", "read-governors", "ask-governors"}:
        from .program import MAX_LITERAL_BYTES, compile_request, execute_program
        with args.document.open("rb") as handle:
            raw = handle.read(MAX_LITERAL_BYTES + 1)
        if len(raw) > MAX_LITERAL_BYTES:
            raise resource_limit("Text input exceeds the installed source budget")
        try:
            text = raw.decode("utf-8", "strict")
        except UnicodeError as error:
            raise NabtError("INVALID_UTF8", "Text source must be strict UTF-8") from error
        if command == "read-text":
            from .text_reader import parse_document
            document = parse_document(raw, source_id="input", scope=args.scope)
            report = document.as_dict()
            report["status"] = "INTERPRETED" if document.accepted else "DEFER"
            report["world_truth"] = "NOT_ESTABLISHED"
            return report, 0 if document.accepted else 3
        if command in {"read-arabic", "read-governors"}:
            if command == "read-governors":
                from .governor_reader import read_arabic
            else:
                from .arabic_reader import read_arabic
            reading = read_arabic(raw, source_id="input", scope=args.scope)
            report = reading.as_dict()
            if args.with_number:
                report["encoding"] = reading.packet()
            return report, 0 if reading.accepted else 3
        task = {"ask-text": "text_inquiry", "ask-arabic": "arabic_inquiry", "ask-governors": "governor_inquiry"}[command]
        program = compile_request({"task": task, "scope": args.scope,
                                   "events": [
                                       {"op": "add", "source_id": "input", "text": text},
                                       {"op": "query", "query_id": "question", "text": args.question},
                                   ]})
        receipt = execute_program(program)
        return receipt, (0 if receipt["run_status"] == "COMPLETED" else
                         3 if receipt["result"].get("status") == "DEFER" else 2)
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
