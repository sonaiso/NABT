"""Run Mashru's compiled Arabic reader and query its checked declarations through NTP."""
from functools import lru_cache
import gzip
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unicodedata

from tools import mashru_transfer as transfer

SCHEMA = "nabt.mashru-lesson.v1"
RESULT = "nabt.mashru-lesson-result.v1"
NATIVE = transfer.LIB / ".lake/build/bin/mashruAthar"
REFERENCE_SHA = "b7a6296f1017bf6a39780699b0e9d1af92c6e9185c5cdf90c2733a19c74534dd"
SINGLETON = {"JUMLA", "DAWA", "QUWWA", "QAYD", "MAFHUM"}
ARITY = {"ADAT": {4}, "JUMLA": {2}, "ITAR": {3}, "MUQ": {5}, "QUWWA": {2},
         "DAWA": {1}, "MANTUQ": {4}, "QAYD": {1, 2}, "MAFHUM": {3}}


@lru_cache(maxsize=1)
def checked_catalog(data):
    if sha256(data).hexdigest() != REFERENCE_SHA:
        raise ValueError("changed compiled Mashru catalogue")
    catalog = json.loads(gzip.decompress(data))
    return catalog, {row["name"]: row for row in catalog["theorems"]}


def check_text(text):
    if (type(text) is not str or not text.strip() or len(text.encode()) > 256
            or len(text.split(" ")) > 12 or any(unicodedata.category(c)[0] == "C" or
            (c.isspace() and c != " ") for c in text)):
        raise ValueError("expected a single legible line of up to 12 tokens and 256 UTF-8 bytes")


def native_traces(texts):
    if not 1 <= len(texts) <= 128:
        raise ValueError("invalid batch size")
    for text in texts:
        check_text(text)
    with TemporaryDirectory() as directory:
        path = Path(directory) / "input.tsv"
        path.write_text("".join(f"{i}\t{text}\n" for i, text in enumerate(texts)), encoding="utf-8")
        call = subprocess.run([str(NATIVE), str(path)], check=True, capture_output=True,
                              encoding="utf-8", timeout=10 + 2 * len(texts))
    traces = [{} for _ in texts]
    for line in call.stdout.splitlines():
        key, tag, *fields = line.split("\t")
        if not key.isascii() or not key.isdecimal() or int(key) >= len(texts) or tag not in ARITY:
            raise ValueError("foreign native trace record")
        if len(fields) not in ARITY[tag]:
            raise ValueError("malformed native trace")
        traces[int(key)].setdefault(tag, []).append(fields)
    for trace in traces:
        if any(len(trace.get(tag, [])) != 1 for tag in SINGLETON):
            raise ValueError("incomplete native trace")
    return traces


def run(lesson):
    if type(lesson) is not dict or lesson.get("schema") != SCHEMA:
        raise ValueError("unknown Mashru lesson")
    op = lesson.get("operation")
    if op == "lookup" and set(lesson) == {"schema", "operation", "theorem"}:
        name = lesson["theorem"]
        if type(name) is not str or not re.fullmatch(r"[\w.'?]{1,240}", name):
            raise ValueError("invalid theorem identifier")
    elif op == "dependency" and set(lesson) == {"schema", "operation", "theorem", "candidate"}:
        if any(type(lesson[k]) is not str or not re.fullmatch(r"[\w.'?]{1,240}", lesson[k])
               for k in ("theorem", "candidate")):
            raise ValueError("invalid dependency identifiers")
    elif op == "read" and set(lesson) == {"schema", "operation", "source_id", "text"}:
        check_text(lesson["text"])
        if type(lesson["source_id"]) is not str or not re.fullmatch(r"[\w.-]{1,100}", lesson["source_id"]):
            raise ValueError("invalid source ID")
    else:
        raise ValueError("unknown Mashru operation or fields")
    result = {"schema": RESULT, "request": lesson, "execution_measured": False,
              "world_truth_established": False, "action_authority": "NONE"}
    try:
        catalog, by_name = checked_catalog(transfer.reference().read_bytes())
        result.update(commit=catalog["commit"], reference_sha256=REFERENCE_SHA)
        if op == "dependency":
            from . import mashru_dependencies
            return dict(result, **mashru_dependencies.compare(
                catalog, by_name, lesson["theorem"], lesson["candidate"]))
        if op == "lookup":
            row = by_name.get(name)
            if row is None:
                return dict(result, status="UNKNOWN_THEOREM")
            actual_sha = transfer.core.file_sha(transfer.ROOT / row["source_path"])
            if actual_sha != catalog["inputs"][row["source_path"]]:
                raise ValueError("stale declaration source")
            return dict(result, status="FOUND_COMPILED_DECLARATION", theorem=row, execution_measured=True)
        for rel, expected in catalog["inputs"].items():
            if transfer.core.file_sha(transfer.ROOT / rel) != expected:
                raise ValueError("stale native reader inputs")
        from . import mashru_readout
        result["neural_proposal"] = mashru_readout.propose(lesson["text"])
        trace, = native_traces([lesson["text"]])
        return dict(result, status="NATIVE_TRACE", execution_measured=True, trace=trace,
                    text_sha256=sha256(lesson["text"].encode()).hexdigest(),
                    rule_reference="Nizam.Athar.la_tarqiya", semantic_scope="SOURCE_READING_ONLY")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return dict(result, status="DEFER_MASHRU_EVIDENCE", reason=type(exc).__name__ + ": " +
                    ("native reader unavailable" if isinstance(exc, OSError) else str(exc)[:150]))
