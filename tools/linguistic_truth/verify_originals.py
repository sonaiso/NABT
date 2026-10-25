"""Replay selected linguistic-truth excerpts against explicitly supplied books.

No original book is downloaded or distributed by this command. With no book
arguments it checks retained bytes only and reports originals_rechecked=false.
The --part1, --part3 and --thinking arguments must be supplied together for an
original replay. SHA-256 correspondence does not authenticate an edition,
interpretation, independent witness or statement about the external world.

DOCX extraction retains every descendant w:p in word/document.xml, joins its
w:t text in document order, and emits LF after each paragraph, including empty
ones. Legacy DOC conversion uses LibreOffice in a fresh temporary profile.
The cognition excerpt uses txt:Text, UTF-8-SIG decoding and universal-newline
conversion. Its unit count is text lines, not printed pages or DOCX paragraphs.
The receipt records the converter executable, actual version and command
configuration. Canonical hashes, rather than a version label alone, determine
whether a conversion reproduced the installed extraction.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "evidence/linguistic_truth_v1/source_inventory.json"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _docx_text(path: Path) -> tuple[bytes, int]:
    with zipfile.ZipFile(path) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
    paragraphs = ["".join(t.text or "" for t in p.findall(".//w:t", NS))
                  for p in document.findall(".//w:p", NS)]
    if not paragraphs:
        raise ValueError("DOCUMENT_PARAGRAPHS_MISSING")
    return ("\n".join(paragraphs) + "\n").encode("utf-8"), len(paragraphs)


def _find_soffice(explicit: Path | None) -> Path:
    if explicit is not None:
        candidate = explicit.expanduser().resolve()
        if not candidate.is_file():
            raise ValueError("CONVERTER_NOT_FOUND")
        return candidate
    installed = shutil.which("soffice") or shutil.which("libreoffice")
    if installed:
        return Path(installed).resolve()
    runtime = os.environ.get("CODEX_PRIMARY_RUNTIME_ROOT")
    if runtime:
        candidate = (Path(runtime) / "dependencies/native/libreoffice-headless/"
                     "libreoffice/program/soffice")
        if candidate.is_file():
            return candidate.resolve()
    raise ValueError("CONVERTER_NOT_FOUND: provide --soffice")


def _convert_doc(path: Path, *, soffice: Path) -> tuple[bytes, int, dict]:
    version = subprocess.run([str(soffice), "--version"], check=True,
                             capture_output=True, text=True, timeout=30).stdout.strip()
    format_name = "txt:Text"
    with tempfile.TemporaryDirectory(prefix="nabt-original-replay-") as temporary:
        directory = Path(temporary)
        profile = (directory / "profile").as_uri()
        command = [str(soffice), f"-env:UserInstallation={profile}", "--headless",
                   "--convert-to", format_name, "--outdir", str(directory), str(path)]
        conversion = subprocess.run(command, capture_output=True, text=True, timeout=60)
        output = directory / (path.stem + ".txt")
        if conversion.returncode != 0 or not output.is_file():
            raise ValueError("DOC_CONVERSION_FAILED")
        # read_text deliberately performs universal-newline conversion.
        text = output.read_text(encoding="utf-8-sig")
        raw, count = text.encode("utf-8"), len(text.splitlines())
    return raw, count, {
        "executable": str(soffice), "version": version,
        "arguments": ["-env:UserInstallation=<fresh-temporary-profile>", "--headless",
                      "--convert-to", format_name, "--outdir", "<temporary-directory>",
                      "<explicit-original-path>"],
        "isolated_profile": True,
        "postprocessing": "UTF-8-SIG decoding; universal newlines; UTF-8 encoding; no Arabic normalization",
    }


def _natural(value, field: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"INVALID_NATURAL: {field}")
    return value


def _check_blob(raw: bytes, expected: dict, label: str) -> None:
    if len(raw) != _natural(expected["bytes"], f"{label}.bytes") or _sha(raw) != expected["sha256"]:
        raise ValueError(f"{label}_CHANGED")


def _range(raw: bytes, start, end, label: str) -> bytes:
    start = _natural(start, f"{label}.start")
    end = _natural(end, f"{label}.end")
    if not start < end <= len(raw):
        raise ValueError(f"{label}_RANGE_INVALID")
    selected = raw[start:end]
    # A byte interval may not start/end inside a UTF-8 scalar.
    selected.decode("utf-8")
    return selected


def _source_path(source: dict) -> Path:
    relative = Path(source["local_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("SOURCE_PATH_OUTSIDE_REPOSITORY")
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError("SOURCE_PATH_OUTSIDE_REPOSITORY")
    return path


def _check_passages(source: dict, passages: list[dict], retained: bytes,
                    canonical: bytes | None = None) -> int:
    if not passages:
        raise ValueError("SOURCE_PASSAGES_MISSING")
    cursor = 0
    units = canonical.splitlines(keepends=True) if canonical is not None else []
    offsets = [0]
    for unit in units:
        offsets.append(offsets[-1] + len(unit))
    for passage in passages:
        if passage["source_id"] != source["source_id"]:
            raise ValueError("PASSAGE_SOURCE_MISMATCH")
        selected = _range(retained, passage["start"], passage["end"], "RETAINED")
        if passage["start"] != cursor or _sha(selected) != passage["sha256"]:
            raise ValueError("RETAINED_PASSAGE_CHANGED")
        cursor = passage["end"]
        start = _natural(passage["original_start"], "original_start")
        end = _natural(passage["original_end"], "original_end")
        if end - start != len(selected):
            raise ValueError("ORIGINAL_PASSAGE_LENGTH_MISMATCH")
        if canonical is not None:
            if _range(canonical, start, end, "ORIGINAL") != selected:
                raise ValueError("ORIGINAL_PASSAGE_CHANGED")
            if "paragraph" in passage:
                first = last = _natural(passage["paragraph"], "paragraph")
            else:
                first = _natural(passage["unit_start"], "unit_start")
                last = _natural(passage["unit_end"], "unit_end")
            if not 1 <= first <= last <= len(units):
                raise ValueError("ORIGINAL_UNIT_RANGE_INVALID")
            if (start, end) != (offsets[first - 1], offsets[last]):
                raise ValueError("ORIGINAL_UNIT_RANGE_CHANGED")
    if cursor != len(retained):
        raise ValueError("RETAINED_PASSAGE_COVERAGE_INCOMPLETE")
    return len(passages)


def verify(*, part1: Path | None = None, part3: Path | None = None,
           thinking: Path | None = None, soffice: Path | None = None) -> dict:
    """Check the installed inventory; original arguments are explicit local files."""
    supplied = {"shakhsiyya1": part1, "shakhsiyya3": part3, "thinking": thinking}
    full_recheck = all(path is not None for path in supplied.values())
    if any(path is not None for path in supplied.values()) and not full_recheck:
        raise ValueError("ALL_THREE_ORIGINALS_REQUIRED")
    inventory_raw = INVENTORY.read_bytes()
    inventory = json.loads(inventory_raw)
    sources = inventory["sources"]
    passages = inventory["passages"]
    if len({s["source_id"] for s in sources}) != len(sources):
        raise ValueError("DUPLICATE_SOURCE_ID")
    if len({p["passage_id"] for p in passages}) != len(passages):
        raise ValueError("DUPLICATE_PASSAGE_ID")
    source_ids = {s["source_id"] for s in sources}
    if any(p["source_id"] not in source_ids for p in passages):
        raise ValueError("UNKNOWN_PASSAGE_SOURCE")
    if {s["work"] for s in sources} != set(supplied):
        raise ValueError("UNEXPECTED_SOURCE_WORKS")
    checked, originals, cache = [], [], {}
    for source in sources:
        retained = _source_path(source).read_bytes()
        _check_blob(retained, source, "RETAINED_SOURCE")
        selected = [p for p in passages if p["source_id"] == source["source_id"]]
        canonical = None
        work = source["work"]
        if full_recheck:
            path = supplied[work].expanduser().resolve()
            if work not in cache:
                original = path.read_bytes()
                _check_blob(original, source["original_artifact"], "ORIGINAL")
                if work == "thinking":
                    canonical, unit_count, converter = _convert_doc(path, soffice=_find_soffice(soffice))
                else:
                    canonical, unit_count = _docx_text(path)
                    converter = None
                cache[work] = (original, canonical, unit_count)
                originals.append({
                    "work": work, "original_path": str(path), "original_bytes": len(original),
                    "original_sha256": _sha(original), "canonical_bytes": len(canonical),
                    "canonical_sha256": _sha(canonical), "canonical_units": unit_count,
                    "canonical_unit_kind": "text_lines" if work == "thinking" else "xml_paragraphs",
                    "method": source["canonical_extraction"]["method"], "converter": converter,
                })
            original, canonical, unit_count = cache[work]
            # Duplicate retained subsets of one book must agree on both identities.
            _check_blob(original, source["original_artifact"], "ORIGINAL")
            expected = source["canonical_extraction"]
            _check_blob(canonical, expected, "CANONICAL_EXTRACTION")
            if unit_count != _natural(expected["paragraphs"], "canonical_extraction.paragraphs"):
                raise ValueError("CANONICAL_UNIT_COUNT_CHANGED")
        count = _check_passages(source, selected, retained, canonical)
        retained_units = sum(1 if "paragraph" in p else
                             _natural(p["unit_end"], "unit_end") -
                             _natural(p["unit_start"], "unit_start") + 1 for p in selected)
        if retained_units != _natural(source["retained_units"], "retained_units"):
            raise ValueError("RETAINED_UNIT_COUNT_CHANGED")
        checked.append({"source_id": source["source_id"], "retained_sha256": _sha(retained),
                        "retained_bytes": len(retained), "passages_checked": count,
                        "retained_units": retained_units,
                        "original_ranges_rechecked": canonical is not None})
    return {
        "schema": "nabt.linguistic-truth.original-recheck.v1", "ok": True,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "ORIGINAL_RECHECK" if full_recheck else "RETAINED_ONLY",
        "inventory_sha256": _sha(inventory_raw),
        "verifier_sha256": _sha(Path(__file__).read_bytes()),
        "originals_rechecked": full_recheck, "original_book_count": len(originals),
        "sources": checked, "originals": originals,
        "passages_checked": sum(s["passages_checked"] for s in checked),
        "retained_units_checked": sum(s["retained_units"] for s in checked),
        "printed_edition_authenticated": False, "interpretation_adequacy_proved": False,
        "world_truth_established": False, "whole_books_formalized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("part1", "part3", "thinking", "soffice"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--output", type=Path, help="write a JSON receipt; books remain untouched")
    args = parser.parse_args()
    try:
        report = verify(part1=args.part1, part3=args.part3, thinking=args.thinking, soffice=args.soffice)
    except (ValueError, KeyError, OSError, zipfile.BadZipFile, ET.ParseError,
            subprocess.SubprocessError) as error:
        report = {"schema": "nabt.linguistic-truth.original-recheck.v1", "ok": False,
                  "mode": "REJECT", "originals_rechecked": False, "error": str(error),
                  "world_truth_established": False}
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
