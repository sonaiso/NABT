"""Exact, source-bound dictionary heading retrieval; no semantic authority.

The parser preserves every OpenITI heading block, including irregular headings,
duplicates and non-root sections. A root-shaped heading is only a candidate;
neither a dictionary heading nor a returned gloss licenses a syntactic analysis.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re


LAW_ID = "nabt.source-lexicon.v1"
_MANIFEST = Path(__file__).parent / "data" / "source_evidence" / "source_lexicon_v1.json"
POLICY_SHA256 = "d2e3b32712248a3d614ec7831ad2b81fe7c3d8dd0b1ca436782bd8a7e3c67b5f"
_HEAD = re.compile(rb"^### [^\r\n]*(?:\r?\n|$)", re.M)
_LETTERS = re.compile(r"[ء-غف-ي]{2,5}")
_MARKS = re.compile(r"[\u064b-\u065f\u0670]")


class SourceIdentityError(ValueError):
    """The bytes do not match an installed source identity."""


@dataclass(frozen=True)
class HeadingBlock:
    ordinal: int
    heading: str
    heading_status: str
    start_byte: int
    heading_end_byte: int
    end_byte: int
    block_sha256: str


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def source_registry() -> dict:
    """Return the installed registry, never a caller-supplied authority file."""
    raw = _MANIFEST.read_bytes()
    if _sha(raw) != POLICY_SHA256:
        raise SourceIdentityError("installed lexicon source policy identity mismatch")
    return json.loads(raw.decode("utf-8"))


def _heading(raw: bytes, source_id: str) -> tuple[str, str]:
    line = raw.decode("utf-8").rstrip("\r\n")
    pattern = r"### \| \(([^\n]+)\)\s*" if source_id == "maqayis" else r"### \$ ([^:\n]+):.*"
    match = re.fullmatch(pattern, line)
    if match:
        # Only delimiters are removed. No hamza/maqsura/vowel/root folding.
        label = match.group(1)
        stripped = _MARKS.sub("", label)
        if _LETTERS.fullmatch(stripped):
            return label, "ROOT_HEADER_CANDIDATE"
        if re.match(r"(?:\[?)(?:باب|كتاب|فصل|المقدمة|مقدمة|تم كتاب)(?:\s|\]|$)", label):
            return label, "SECTION_HEADER"
        return label, "REVIEW_REQUIRED"
    label = re.sub(r"^### [|$ ]*", "", line)
    section = re.match(r"(?:\[?)(?:باب|كتاب|فصل|المقدمة|مقدمة|تم كتاب)(?:\s|\]|$)", label)
    return label, "SECTION_HEADER" if section else "REVIEW_REQUIRED"


def _scan(raw: bytes, source_id: str) -> tuple[HeadingBlock, ...]:
    """Structural parser only. Public loading authenticates bytes first."""
    matches = list(_HEAD.finditer(raw))
    blocks = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        label, status = _heading(match.group(), source_id)
        blocks.append(HeadingBlock(i, label, status, match.start(), match.end(), end,
                                   _sha(raw[match.start():end])))
    return tuple(blocks)


@dataclass(frozen=True)
class SourceLexicon:
    source_id: str
    raw: bytes
    blocks: tuple[HeadingBlock, ...] = field(init=False)

    def __post_init__(self) -> None:
        registry = source_registry()["sources"]
        if not isinstance(self.source_id, str) or self.source_id not in registry:
            raise ValueError("unknown installed dictionary source")
        spec = registry[self.source_id]
        if type(self.raw) is not bytes or len(self.raw) != spec["bytes"] or _sha(self.raw) != spec["sha256"]:
            raise SourceIdentityError(f"{self.source_id}: pinned source bytes/hash mismatch")
        blob = hashlib.sha1(b"blob " + str(len(self.raw)).encode() + b"\0" + self.raw).hexdigest()
        if blob != spec["git_blob_sha1"]:
            raise SourceIdentityError(f"{self.source_id}: pinned Git blob mismatch")
        self.raw.decode("utf-8", errors="strict")
        object.__setattr__(self, "blocks", _scan(self.raw, self.source_id))

    @classmethod
    def load(cls, source_id: str, path: str | Path) -> "SourceLexicon":
        registry = source_registry()["sources"]
        if not isinstance(source_id, str) or source_id not in registry:
            raise ValueError("unknown installed dictionary source")
        spec = registry[source_id]
        # Bound the read; an oversized file cannot turn into an empty lexicon.
        with Path(path).open("rb") as stream:
            raw = stream.read(spec["bytes"] + 1)
        return cls(source_id, raw)

    def lookup_exact(self, heading: str) -> dict:
        if not isinstance(heading, str) or not heading or len(heading) > 256:
            raise ValueError("heading must be a nonempty string of at most 256 characters")
        if any(ord(c) < 32 for c in heading):
            raise ValueError("heading cannot contain control characters")
        # Deliberately no normalization, alias expansion or first-match selection.
        selected = [block for block in self.blocks if block.heading == heading]
        return {
            "law_id": LAW_ID,
            "status": "FOUND_SOURCE_HEADINGS" if selected else "NOT_INDEXED",
            "query": heading,
            "source_id": self.source_id,
            "source_sha256": _sha(self.raw),
            "source": source_registry()["sources"][self.source_id],
            "authority": "SOURCE_TEXT_RETRIEVAL_ONLY",
            "reading_licensed": False,
            "syntactic_licence": False,
            "world_truth_asserted": False,
            "all_arabic_senses_enumerated": False,
            "complete_exact_heading_matches": True,
            "alternatives": [self.record(block) for block in selected],
        }

    def record(self, block: HeadingBlock) -> dict:
        # A foreign/mutated block cannot be used to manufacture a source quote.
        if type(block.ordinal) is not int or not 0 <= block.ordinal < len(self.blocks):
            raise ValueError("block is not in this index")
        if self.blocks[block.ordinal] != block:
            raise ValueError("block is not in this index")
        return {
            "id": f"{self.source_id}:{block.start_byte}:{block.end_byte}",
            "heading": block.heading,
            "heading_status": block.heading_status,
            "start_byte": block.start_byte,
            "heading_end_byte": block.heading_end_byte,
            "end_byte": block.end_byte,
            "block_sha256": block.block_sha256,
            "raw_block": self.raw[block.start_byte:block.end_byte].decode("utf-8"),
        }

    def inventory(self) -> dict:
        counts = Counter(block.heading_status for block in self.blocks)
        heading_counts = Counter(block.heading for block in self.blocks)
        prefix_end = self.blocks[0].start_byte if self.blocks else len(self.raw)
        covered = prefix_end + sum(b.end_byte - b.start_byte for b in self.blocks)
        return {
            "law_id": LAW_ID, "source_id": self.source_id,
            "source_sha256": _sha(self.raw), "source_bytes": len(self.raw),
            "heading_blocks": len(self.blocks), "heading_status_counts": dict(sorted(counts.items())),
            "duplicate_headings": {k:v for k,v in sorted(heading_counts.items()) if v > 1},
            "preamble_start_byte": 0, "preamble_end_byte": prefix_end,
            "preamble_sha256": _sha(self.raw[:prefix_end]),
            "partition_bytes": covered,
            "source_bytes_partitioned": covered == len(self.raw),
            "all_roots_enumerated": False,
            "all_senses_enumerated": False,
            "linguistic_completeness_denominator": None,
            "authority": "SOURCE_TEXT_RETRIEVAL_ONLY",
        }
