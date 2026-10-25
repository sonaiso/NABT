"""Replay installed source bytes for the bounded licensed-inference law.

The compiled review pin authorizes this authored source selection. A matching
hash authenticates bytes, not their scholarly interpretation or world truth.
Full unpublished DOCX replay is optional and is never implied by default.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LAW_ID = "nabt.licensed-inference.v1"
REVIEW_PATH = "evidence/licensed_inference_v1/source_links.json"
SOURCE_LINKS_SHA256 = "e4da54a815ecb4fbce4ba2365177aa9ae588d3e8c0ab8c536452702e9352b79d"
MAX_REVIEW_BYTES = 131_072
MAX_SOURCE_BYTES = 8_388_608
MAX_RECORDS = 512


class SourceValidationError(ValueError):
    """The installed review or a source cannot be replayed exactly."""


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise SourceValidationError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _integer(value: Any, label: str, minimum: int = 0) -> int:
    _require(type(value) is int and value >= minimum, f"invalid {label}")
    return value


def _digest(value: Any, label: str) -> str:
    _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
             f"invalid {label}")
    return value


def _records(value: Any, key: str) -> list[dict[str, Any]]:
    _require(isinstance(value, list) and 0 < len(value) <= MAX_RECORDS,
             f"invalid {key} records")
    _require(all(isinstance(item, dict) for item in value), f"invalid {key} record")
    return value


def _unique(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = row.get(key)
        _require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.:-]+", value) is not None,
                 f"invalid {key}")
        _require(value not in result, f"duplicate {key}: {value}")
        result[value] = row
    return result


def _read(root: Path, relative: Any, limit: int) -> bytes:
    _require(isinstance(relative, str) and bool(relative), "invalid source path")
    path = PurePosixPath(relative)
    _require(not path.is_absolute() and ".." not in path.parts and "\\" not in relative
             and str(path) == relative, "source path must be canonical and relative")
    try:
        resolved_root = root.resolve(strict=True)
        candidate = (resolved_root / relative).resolve(strict=True)
        _require(candidate.is_relative_to(resolved_root), "source path escapes root")
        _require(candidate.is_file(), "source is not a regular file")
        _require(candidate.stat().st_size <= limit, "source exceeds resource bound")
        with candidate.open("rb") as handle:
            raw = handle.read(limit + 1)
        _require(len(raw) <= limit, "source exceeds resource bound")
        return raw
    except OSError as exc:
        raise SourceValidationError(f"source unavailable: {relative}") from exc


def _check_identity(raw: bytes, record: dict[str, Any], label: str) -> None:
    _require(len(raw) == _integer(record.get("bytes"), f"{label} bytes"),
             f"{label} byte count mismatch")
    _require(_sha(raw) == _digest(record.get("sha256"), f"{label} hash"),
             f"{label} hash mismatch")


def _span(raw: bytes, record: dict[str, Any], label: str) -> bytes:
    start = _integer(record.get("start"), f"{label} start")
    end = _integer(record.get("end"), f"{label} end", 1)
    _require(start < end <= len(raw), f"{label} span out of bounds")
    chunk = raw[start:end]
    try:
        chunk.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SourceValidationError(f"{label} invalid UTF-8 boundary") from exc
    _require(_sha(chunk) == _digest(record.get("sha256"), f"{label} hash"),
             f"{label} span hash mismatch")
    return chunk


def _optional_original_replay(
    original_part3: Path | None, source: dict[str, Any], retained: bytes
) -> dict[str, Any]:
    if original_part3 is None:
        return {"requested": False, "performed": False, "scope": []}
    try:
        with Path(original_part3).open("rb") as handle:
            original = handle.read(2_097_153)
    except OSError as exc:
        raise SourceValidationError("original DOCX unavailable") from exc
    _require(len(original) <= 2_097_152, "original DOCX exceeds resource bound")
    _check_identity(original, source["original_artifact"], "original DOCX")
    try:
        # Hash equality was checked before opening the archive. The extra bound
        # prevents accidental unbounded XML reading even if the law is revised.
        with zipfile.ZipFile(io.BytesIO(original)) as archive:
            info = archive.getinfo("word/document.xml")
            _require(info.file_size <= 33_554_432, "original XML exceeds resource bound")
            xml = ET.fromstring(archive.read(info))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        raise SourceValidationError("original DOCX cannot be extracted") from exc
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = [
        ("".join(node.text or "" for node in paragraph.findall(".//w:t", ns)) + "\n").encode()
        for paragraph in xml.findall(".//w:p", ns)
    ]
    canonical = b"".join(paragraphs)
    extraction = source["canonical_extraction"]
    _check_identity(canonical, extraction, "canonical extraction")
    _require(len(paragraphs) == extraction["paragraphs"], "original paragraph count mismatch")
    for span in source["retained_original_spans"]:
        paragraph = span["paragraph"]
        start = sum(map(len, paragraphs[:paragraph - 1]))
        end = start + len(paragraphs[paragraph - 1])
        _require((start, end) == (span["original_start"], span["original_end"]),
                 "original paragraph offsets mismatch")
        _require(canonical[start:end] == retained[span["start"]:span["end"]],
                 "original paragraph differs from retained excerpt")
    return {"requested": True, "performed": True,
            "scope": [source["source_id"]], "original_sha256": _sha(original),
            "canonical_sha256": _sha(canonical), "paragraphs_replayed": [574, 576]}


def _validate_document(root: Path, document: dict[str, Any]) -> dict[str, Any]:
    """Validate structure and replay; public entry point also enforces the pin."""
    _require(document.get("schema") == "nabt.licensed-inference-sources.v1", "unsupported review schema")
    _require(document.get("law_id") == LAW_ID, "wrong law identity")
    registries = _records(document.get("source_registries"), "registry")
    registry_paths: set[str] = set()
    for record in registries:
        path = record.get("path")
        _require(isinstance(path, str) and path not in registry_paths, "duplicate/invalid registry path")
        registry_paths.add(path)
        _check_identity(_read(root, path, MAX_SOURCE_BYTES), record, "registry")

    source_map = _unique(_records(document.get("sources"), "source"), "source_id")
    source_raw: dict[str, bytes] = {}
    paths: set[str] = set()
    for sid, source in source_map.items():
        path = source.get("local_path")
        _require(isinstance(path, str) and path not in paths, "duplicate/invalid source path")
        paths.add(path)
        raw = _read(root, path, MAX_SOURCE_BYTES)
        _check_identity(raw, source, f"source {sid}")
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SourceValidationError(f"source {sid} is not UTF-8") from exc
        source_raw[sid] = raw
        registry = source.get("provenance", {}).get("registry")
        _require(registry is None or registry in registry_paths, "unknown source registry")
        if "retained_original_spans" in source:
            cursor = 0
            previous_original_end = 0
            seen: set[int] = set()
            for span in _records(source["retained_original_spans"], "original span"):
                paragraph = _integer(span.get("paragraph"), "original paragraph", 1)
                _require(paragraph not in seen, "duplicate original paragraph")
                seen.add(paragraph)
                chunk = _span(raw, span, "retained original")
                os = _integer(span.get("original_start"), "original start")
                oe = _integer(span.get("original_end"), "original end", 1)
                _require(span["start"] == cursor and oe - os == len(chunk)
                         and os >= previous_original_end, "invalid retained original coverage")
                cursor, previous_original_end = span["end"], oe
            _require(cursor == len(raw), "incomplete retained original coverage")

    passages = _unique(_records(document.get("passages"), "passage"), "passage_id")
    seen_spans: set[tuple[str, int, int]] = set()
    for pid, passage in passages.items():
        sid = passage.get("source_id")
        _require(isinstance(sid, str) and sid in source_raw, "unknown passage source")
        raw = source_raw[sid]
        chunk = _span(raw, passage, pid)
        _require(isinstance(passage.get("raw_text"), str), f"{pid} invalid raw text")
        try:
            quoted_bytes = passage["raw_text"].encode("utf-8")
        except UnicodeEncodeError as exc:
            raise SourceValidationError(f"{pid} raw text is not valid Unicode") from exc
        _require(quoted_bytes == chunk, f"{pid} raw text mismatch")
        a = _integer(passage.get("line_start"), "line start", 1)
        z = _integer(passage.get("line_end"), "line end", 1)
        lines = raw.splitlines(keepends=True)
        _require(a <= z <= len(lines), f"{pid} line range out of bounds")
        _require((sum(map(len, lines[:a - 1])), sum(map(len, lines[:z])))
                 == (passage["start"], passage["end"]), f"{pid} line/span mismatch")
        identity = (sid, passage["start"], passage["end"])
        _require(identity not in seen_spans, "duplicate source span")
        seen_spans.add(identity)
    relations = _unique(_records(document.get("relations"), "relation"), "relation_id")
    for relation in relations.values():
        ids = relation.get("passage_ids")
        _require(isinstance(ids, list) and 0 < len(ids) <= MAX_RECORDS
                 and all(isinstance(pid, str) and pid in passages for pid in ids)
                 and len(set(ids)) == len(ids), "invalid relation passage links")
    for lexical in _records(document.get("lexical_forms"), "lexical form"):
        _require(isinstance(lexical.get("passage_ids"), list)
                 and bool(lexical["passage_ids"])
                 and all(isinstance(pid, str) and pid in passages for pid in lexical["passage_ids"]),
                 "invalid lexical passage links")
    return {"source_map": source_map, "source_raw": source_raw,
            "passages": passages, "relations": relations}


def build_inventory(root: Path = ROOT, *, original_part3: Path | None = None) -> dict[str, Any]:
    """Return installed reviewed inventory after exact source replay.

    `original_part3` checks only the new retained p574/p576 excerpt against its
    supplied DOCX. All other sources retain their existing provenance scope.
    A source mismatch raises; it never becomes a linguistic rejection.
    """
    raw = _read(Path(root), REVIEW_PATH, MAX_REVIEW_BYTES)
    _require(_sha(raw) == SOURCE_LINKS_SHA256, "installed source review hash mismatch")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceValidationError("invalid source review encoding") from exc
    _require(isinstance(document, dict), "invalid source review document")
    replay = _validate_document(Path(root), document)
    original = _optional_original_replay(
        original_part3, replay["source_map"]["nabhani_condition_profile"],
        replay["source_raw"]["nabhani_condition_profile"],
    )
    return {
        "schema": document["schema"], "law_id": LAW_ID,
        "review_sha256": SOURCE_LINKS_SHA256,
        "source_count": len(replay["source_map"]), "passage_count": len(replay["passages"]),
        "relation_ids": list(replay["relations"]),
        "source_replay": {
            "mode": "retained_bytes_with_scoped_original_recheck" if original["performed"] else "retained_bytes_only",
            "retained_sources_replayed": len(replay["source_map"]),
            "retained_passages_replayed": len(replay["passages"]),
            "originals_rechecked": original["performed"], "original_recheck": original,
            "source_interpretation_proved": False, "world_truth_established": False,
        },
        "sources": document["sources"], "passages": document["passages"],
        "relations": document["relations"], "lexical_forms": document["lexical_forms"],
        "grammar_contract": document["grammar_contract"],
    }


def replay_sources(root: Path = ROOT, *, original_part3: Path | None = None) -> dict[str, Any]:
    """Named alias for callers that only need the source replay receipt."""
    return build_inventory(root, original_part3=original_part3)
