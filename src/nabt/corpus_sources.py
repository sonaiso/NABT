"""Byte-bound external QAC/MASAQ annotation records, with exact replay.

This module imports annotations; it does not infer grammatical facts from text.
The three explicit schemas remain distinct. A locator is not an occurrence ID:
duplicate locators and malformed data rows are retained in source order.

The strict CSV dialect uses commas, double-quoted fields, doubled quote escapes,
and CR, LF or CRLF record endings. Newlines inside quotes remain in the field.
Spaces after a closing quote and quotes inside unquoted fields are syntax errors.
The byte scanner has no process-global csv.field_size_limit side effect.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import re

from .errors import NabtError, resource_limit

SCHEMA = "nabt.corpus-source.v1"
AUTHORITY = "ANNOTATION_REPLAY_ONLY"
MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_RECORDS = 300_000
MAX_SOURCE_ID_LENGTH = 128
MAX_COORDINATE = 2**63 - 1

QAC_HEADER = ("LOCATION", "FORM", "TAG", "FEATURES")
MASAQ_AR_HEADER = (
    "ID", "Sura_No", "Verse_No", "Column5", "Word_No", "Word",
    "Without_Diacritics", "Segmented_Word", "Morph_tag", "Morph_type",
    "Punctuation_Mark", "Invariable_Declinable", "Syntactic_Role",
    "Possessive_Construct", "Case_Mood", "Case_Mood_Marker", "Phrase",
    "Phrasal_Function", "Notes",
)
MASAQ_EN_HEADER = (
    "ID", "Sura_No", "Verse_No", "Word_No", "Segment_No", "Word",
    "Without_Diacritics", "Segmented_Word", "Morph_Tag", "Morph_Type",
    "Punctuation_Mark", "Invariable_Declinable", "Syntactic_Role",
    "Possessive_Construct", "Case_Mood", "Case_Mood_Marker", "Phrase",
    "Phrasal_Function", "Gloss",
)
HEADERS = {"qac": QAC_HEADER, "masaq-ar": MASAQ_AR_HEADER,
           "masaq-en": MASAQ_EN_HEADER}
_BOM = b"\xef\xbb\xbf"
_LINES = re.compile(rb"[^\r\n]*(?:\r\n?|\n|$)")
_CSV_SPECIAL = re.compile(rb'[,"\r\n]')
_LOCATION = re.compile(r"\(([1-9][0-9]{0,18}):([1-9][0-9]{0,18}):"
                       r"([1-9][0-9]{0,18}):([1-9][0-9]{0,18})\)")
_DECIMAL = re.compile(r"[1-9][0-9]{0,18}")


def _source(raw, format, source_id):
    if type(format) is not str or format not in HEADERS:
        raise NabtError("INVALID_CORPUS_FORMAT", "Choose qac, masaq-ar or masaq-en")
    if (type(source_id) is not str or len(source_id) > MAX_SOURCE_ID_LENGTH
            or re.fullmatch(r"[a-z][a-z0-9_]*", source_id) is None):
        raise NabtError("INVALID_CORPUS_SOURCE_ID",
                        "Use a bounded lowercase ASCII source identifier")
    if type(raw) is not bytes or not raw:
        raise NabtError("INVALID_CORPUS_SOURCE", "Use nonempty UTF-8 source bytes")
    if len(raw) > MAX_SOURCE_BYTES:
        raise resource_limit("Corpus exceeds its byte budget", maximum=MAX_SOURCE_BYTES)
    try:
        raw.decode("utf-8", "strict")
    except UnicodeError as error:
        raise NabtError("INVALID_UTF8", "Corpus must be strict UTF-8") from error
    return {"id": source_id, "sha256": sha256(raw).hexdigest(),
            "byte_length": len(raw)}


def _span(raw, start, end):
    return {"byte_start": start, "byte_end": end,
            "raw_record": raw[start:end].decode("utf-8")}


def _physical_lines(raw):
    for match in _LINES.finditer(raw):
        if match.start() != match.end():
            yield match.start(), match.end()


def _tsv_records(raw):
    """QAC comments/empty lines are layout, not silently discarded records."""
    for start, end in _physical_lines(raw):
        body = raw[start:end]
        if body.endswith(b"\r\n"):
            body = body[:-2]
        elif body.endswith((b"\r", b"\n")):
            body = body[:-1]
        if start == 0 and body.startswith(_BOM):
            body = body[len(_BOM):]
        if not body or body.startswith(b"#"):
            yield start, end, None, 0
        else:
            width = body.count(b"\t") + 1
            values = body.decode("utf-8").split("\t") if width == len(QAC_HEADER) else []
            yield start, end, values, width


def _csv_syntax(offset, message):
    return NabtError("INVALID_CORPUS_CSV", message, details={"byte_offset": offset})


def _csv_records(raw):
    """Yield logical CSV records and their full physical byte intervals.

    Only separator/quote bytes need scanning: UTF-8 continuation bytes cannot
    equal any of them. Field decoding does not alter line endings or Unicode.
    A BOM is accepted only at the start of the source and kept in the raw header.
    """
    record_start = 0
    field_start = len(_BOM) if raw.startswith(_BOM) else 0
    values = []
    width = 0
    quoted = False
    closing_quote = None
    skip_until = 0

    for match in _CSV_SPECIAL.finditer(raw):
        pos = match.start()
        if pos < skip_until:
            continue
        byte = raw[pos]
        if quoted:
            if byte == 34:
                if pos + 1 < len(raw) and raw[pos + 1] == 34:
                    skip_until = pos + 2
                else:
                    quoted = False
                    closing_quote = pos
            continue

        if closing_quote is not None and pos != closing_quote + 1:
            raise _csv_syntax(closing_quote + 1, "Characters follow a closing quote")
        if byte == 34:
            if pos != field_start or closing_quote is not None:
                raise _csv_syntax(pos, "Quote in an unquoted CSV field")
            quoted = True
            continue

        width += 1
        # No malformed row can allocate one Python string per separator across
        # the entire byte budget. Raw bytes and the full column count survive.
        if width <= len(MASAQ_EN_HEADER):
            if closing_quote is not None:
                value = raw[field_start + 1:closing_quote].replace(b'""', b'"')
            else:
                value = raw[field_start:pos]
            values.append(value.decode("utf-8"))
        closing_quote = None
        end = pos + 1
        if byte == 13 and raw[pos + 1:pos + 2] == b"\n":
            end += 1
        field_start = end
        if byte != 44:
            yield record_start, end, values, width
            values = []
            width = 0
            record_start = end
            skip_until = end

    if quoted:
        raise _csv_syntax(field_start, "Unterminated quoted CSV field")
    if closing_quote is not None and closing_quote + 1 != len(raw):
        raise _csv_syntax(closing_quote + 1, "Characters follow a closing quote")
    if record_start < len(raw):
        width += 1
        if width <= len(MASAQ_EN_HEADER):
            if closing_quote is not None:
                value = raw[field_start + 1:closing_quote].replace(b'""', b'"')
            else:
                value = raw[field_start:]
            values.append(value.decode("utf-8"))
        yield record_start, len(raw), values, width


def _positive_decimal(value):
    """A coordinate/ID is canonical ASCII decimal in 1..2^63-1."""
    if _DECIMAL.fullmatch(value) is None:
        return None
    number = int(value)
    return number if number <= MAX_COORDINATE else None


def _row(raw, start, end, values, width, *, format, source, ordinal):
    expected = HEADERS[format]
    diagnostics = []
    fields = {}
    locator = None
    if width != len(expected):
        diagnostics.append({"code": "COLUMN_COUNT", "expected": len(expected),
                            "actual": width})
    else:
        fields = dict(zip(expected, values))
        if format == "qac":
            match = _LOCATION.fullmatch(fields["LOCATION"])
            if match:
                coords = [_positive_decimal(value) for value in match.groups()]
                if all(value is not None for value in coords):
                    locator = coords
        else:
            columns = (("Sura_No", "Verse_No", "Column5", "Word_No")
                       if format == "masaq-ar" else
                       ("Sura_No", "Verse_No", "Word_No", "Segment_No"))
            coords = [_positive_decimal(fields[name]) for name in columns]
            if all(value is not None for value in coords):
                locator = coords
            if _positive_decimal(fields["ID"]) is None:
                diagnostics.append({"code": "INVALID_ID", "field": "ID"})
        if locator is None:
            diagnostics.append({"code": "INVALID_LOCATOR"})

    identity = sha256(json.dumps(
        [SCHEMA, format, source["id"], source["sha256"], start, end, ordinal],
        separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()
    result = {"identity": identity, **_span(raw, start, end), "ordinal": ordinal,
              "locator": locator, "fields": fields, "valid": not diagnostics,
              "diagnostics": diagnostics}
    if format == "qac":
        result["feature_tokens"] = fields["FEATURES"].split("|") if fields else []
    return result


def read_corpus(raw: bytes, *, format: str, source_id: str = "corpus") -> dict:
    """Read a bounded external corpus without repairing or merging its rows.

    Globally malformed input (encoding/header/CSV syntax) raises NabtError.
    A malformed data row remains in the report with valid=False. Wrong-width
    rows have fields={} rather than assigning a truncated row to the schema.
    IDs and locator coordinates require canonical positive ASCII decimal within
    signed 64-bit range; raw strings are always retained, including invalid ones.
    A syntactically valid row is not a claim of linguistic truth or completeness.
    """
    source = _source(raw, format, source_id)
    header = None
    records = []
    layout = []
    # Coalescing adjacent QAC layout spans bounds output independently of how
    # many empty/comment lines an input places before or between records.
    layout_start = None
    layout_end = None
    occurrences = Counter()
    diagnostic_counts = Counter()
    invalid_count = 0
    spans = _tsv_records(raw) if format == "qac" else _csv_records(raw)
    for start, end, values, width in spans:
        if values is None:
            if layout_start is None:
                layout_start = start
            layout_end = end
            continue
        if layout_start is not None:
            layout.append({"kind": "qac_layout", **_span(raw, layout_start, layout_end)})
            layout_start = layout_end = None
        if header is None:
            if width != len(HEADERS[format]) or tuple(values) != HEADERS[format]:
                raise NabtError("INVALID_CORPUS_HEADER",
                                "Header must match the chosen corpus schema exactly")
            header = {"fieldnames": values, **_span(raw, start, end)}
            continue
        if len(records) >= MAX_RECORDS:
            raise resource_limit("Corpus exceeds its record budget", maximum=MAX_RECORDS)
        record = _row(raw, start, end, values, width, format=format, source=source,
                      ordinal=len(records) + 1)
        records.append(record)
        invalid_count += not record["valid"]
        if record["locator"] is not None:
            occurrences[tuple(record["locator"])] += 1
        diagnostic_counts.update(d["code"] for d in record["diagnostics"])
    if layout_start is not None:
        layout.append({"kind": "qac_layout", **_span(raw, layout_start, layout_end)})
    if header is None:
        raise NabtError("INVALID_CORPUS_HEADER", "Corpus has no schema header")

    record_bytes = sum(row["byte_end"] - row["byte_start"] for row in records)
    header_bytes = header["byte_end"] - header["byte_start"]
    layout_bytes = sum(part["byte_end"] - part["byte_start"] for part in layout)
    return {"schema": SCHEMA, "format": format, "source": source,
            "authority": AUTHORITY,
            "status": "READ_WITH_ERRORS" if invalid_count else "READ",
            "header": header, "records": records, "nonrecord_fragments": layout,
            "summary": {"record_count": len(records),
                        "valid_count": len(records) - invalid_count,
                        "invalid_count": invalid_count,
                        "diagnostic_counts": dict(sorted(diagnostic_counts.items())),
                        "duplicate_locator_groups": sum(n > 1 for n in occurrences.values()),
                        "duplicate_locator_excess_records": sum(n - 1 for n in occurrences.values()),
                        "record_bytes": record_bytes, "header_bytes": header_bytes,
                        "nonrecord_bytes": layout_bytes,
                        "source_coverage_complete": record_bytes + header_bytes + layout_bytes == len(raw)}}


def _same_json(left, right):
    """Exact typed comparison, bounded by the freshly read finite report.

    Unlike Python equality, True cannot replace 1; tuples, subclasses and extra
    keys are rejected. No recursion or large duplicated canonical JSON buffer is
    needed, and a cyclic forged input cannot extend the fresh traversal.
    """
    pending = [iter(((left, right),))]
    while pending:
        try:
            actual, expected = next(pending[-1])
        except StopIteration:
            pending.pop()
            continue
        if type(actual) is not type(expected):
            return False
        if type(expected) is dict:
            if (len(actual) != len(expected) or any(type(k) is not str for k in actual)
                    or actual.keys() != expected.keys()):
                return False
            pending.append(zip(actual.values(), map(expected.__getitem__, actual)))
        elif type(expected) is list:
            if len(actual) != len(expected):
                return False
            pending.append(iter(zip(actual, expected)))
        elif actual != expected:
            return False
    return True


def verify_corpus(report, *, raw: bytes, format: str, source_id: str = "corpus") -> dict:
    """Re-read all external bytes; a matching report proves annotation replay only."""
    if type(report) is not dict:
        return {"valid": False, "status": "REJECT", "code": "INVALID_CORPUS_REPORT",
                "diagnostics": [{"code": "INVALID_CORPUS_REPORT"}]}
    try:
        fresh = read_corpus(raw, format=format, source_id=source_id)
    except NabtError as error:
        return {"valid": False, "status": error.status, "code": error.code,
                "diagnostics": [{"code": error.code, "message": error.message}]}
    if not _same_json(report, fresh):
        return {"valid": False, "status": "REJECT", "code": "INVALID_CORPUS_REPORT",
                "diagnostics": [{"code": "REPORT_DIFFERS_FROM_SOURCE_REPLAY"}]}
    return {"valid": True, "status": "VERIFIED", "diagnostics": [],
            "source_sha256": fresh["source"]["sha256"], "authority": AUTHORITY}
