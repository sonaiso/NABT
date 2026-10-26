"""Load an unchanged, pinned annotation source through the existing learner.

The external QAC source is a separate runtime profile, not an overlay on the
authored teaching corpus. Its morphological annotations are source-relative
testimony. A dictionary/annotation alignment neither settles a word's sense
in a new utterance nor establishes external reality, motives or transmission.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path
import unicodedata
import zlib

from nabt.corpus_evidence import (QacLexicon, ROOT_BW, buckwalter_to_arabic,
                             learn_qac_lexicon)
from nabt.corpus_sources import read_corpus
from nabt.errors import NabtError, resource_limit


VERSION = "nabt.attested-lexical-loading.v1"
PROFILE_ID = "qac_attested_source_v1"
SOURCE_SHA256 = "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46"
SOURCE_BYTES = 6309503
# Allow gzip framing and an uncompressed DEFLATE representation, while
# independently bounding the decoded original to its exact pinned size.
MAX_PAYLOAD_BYTES = SOURCE_BYTES + 65536
SOURCE_URL = (
    "https://raw.githubusercontent.com/Saleh1967/Alghanem/"
    "9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/"
    "corpora/qac/quranic-corpus-morphology-0.4.txt.gz"
)
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "artifacts/local/external/quranic-corpus-morphology-0.4.txt.gz"
MATRIX_PATH = ROOT / "evidence/lexical_loading_v1/matrix.json"
# Updated only with the independently selected, reviewed source matrix.
MATRIX_SHA256 = "1c6444380a5192d45e040b893a822cb344384079aa4e89e174a363c5790b6368"
CATALOGUE_PATH = ROOT / "evidence/lexical_completion_v1/catalog.json"
CATALOGUE_SHA256 = "1ac5b25629f7847e9f128cf2c75cfbe573657df769446afae3cc3436f566a872"


@dataclass(frozen=True, slots=True)
class LoadedLexicon:
    """The immutable raw-source model and a scoped, reproducible load receipt."""

    model: QacLexicon
    report: dict


@lru_cache(maxsize=2)
def _decode_source(payload: bytes) -> bytes:
    if type(payload) is not bytes or not payload:
        raise NabtError("INVALID_ATTESTED_SOURCE", "Supply the unchanged source bytes")
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise resource_limit("Source exceeds its transport byte budget", maximum=MAX_PAYLOAD_BYTES)
    if payload[:2] == b"\x1f\x8b":
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(payload)) as stream:
                raw = stream.read(SOURCE_BYTES + 1)
        except (OSError, EOFError, zlib.error) as error:
            raise NabtError("INVALID_ATTESTED_SOURCE", "Invalid source compression") from error
    else:
        raw = payload
    if len(raw) > SOURCE_BYTES:
        raise resource_limit("Decoded source exceeds its pinned byte budget", maximum=SOURCE_BYTES)
    if len(raw) != SOURCE_BYTES or sha256(raw).hexdigest() != SOURCE_SHA256:
        raise NabtError("ATTESTED_SOURCE_IDENTITY_MISMATCH", "The original source size or SHA-256 differs")
    return raw


def _installed_matrix() -> tuple[dict, str]:
    raw = MATRIX_PATH.read_bytes()
    digest = sha256(raw).hexdigest()
    if digest != MATRIX_SHA256:
        raise NabtError("LEXICAL_MATRIX_IDENTITY_MISMATCH", "The installed lexical matrix differs")
    value = json.loads(raw)
    if type(value) is not dict or value.get("schema") != "nabt.lexical-loading-matrix.v1":
        raise NabtError("INVALID_LEXICAL_MATRIX", "Unknown installed lexical matrix schema")
    return value, digest


def _matrix_report(matrix: dict, raw: bytes, digest: str) -> dict:
    """Replay matrix source spans; this is not an authority supplied by a caller."""
    catalogue_raw = CATALOGUE_PATH.read_bytes()
    if sha256(catalogue_raw).hexdigest() != CATALOGUE_SHA256:
        raise NabtError("LEXICAL_CATALOGUE_IDENTITY_MISMATCH", "The prior catalogue differs")
    # Bytes, rather than an editable dict or its caller-reported digest, key the
    # cache. Decode a fresh receipt so a caller cannot mutate later results.
    matrix_raw = json.dumps(matrix, ensure_ascii=False, sort_keys=True,
                            separators=(",", ":"), allow_nan=False).encode()
    return json.loads(_replay_matrix(matrix_raw, raw, catalogue_raw, digest))


def _require(condition: bool, message: str) -> None:
    if condition is not True:
        raise NabtError("LEXICAL_MATRIX_REPLAY_MISMATCH", message)


def _candidate_key(value: str) -> str:
    """The declared search projection; shadda, dagger alif and hamza survive."""
    _require(type(value) is str and bool(value), "Candidate headwords must be nonempty strings")
    ignored = set("ًٌٍَُِْٓ")
    decomposed = unicodedata.normalize("NFD", value)
    return unicodedata.normalize("NFC", "".join(c for c in decomposed if c not in ignored))


@lru_cache(maxsize=2)
def _replay_matrix(matrix_raw: bytes, raw: bytes, catalogue_raw: bytes,
                   digest: str) -> bytes:
    matrix, catalogue = json.loads(matrix_raw), json.loads(catalogue_raw)
    _require(len(raw) == SOURCE_BYTES and sha256(raw).hexdigest() == SOURCE_SHA256,
             "Matrix replay requires the unchanged source")
    _require(matrix["sources"]["qac"]["sha256"] == SOURCE_SHA256 and
             type(matrix["sources"]["qac"]["bytes"]) is int and
             matrix["sources"]["qac"]["bytes"] == SOURCE_BYTES,
             "Matrix source identity differs")
    _require(matrix["sources"]["catalogue"]["sha256"] == CATALOGUE_SHA256,
             "Matrix prior-catalogue identity differs")
    original = {entry["id"]: entry for entry in catalogue["senses"]}
    entries = matrix["entries"]
    _require(type(entries) is list and len(entries) == len(original) and
             {entry["id"] for entry in entries} == set(original),
             "The matrix must preserve every selected prior sense exactly once")
    corpus = read_corpus(raw, format="qac", source_id=PROFILE_ID)
    records = {(r["byte_start"], r["byte_end"]): r for r in corpus["records"]}
    nominal_groups = {}
    for row in corpus["records"]:
        fields = row.get("fields")
        if not fields or fields["TAG"] not in ("N", "PN", "ADJ", "T", "LOC"):
            continue
        tokens = fields["FEATURES"].split("|")
        if tokens[0] != "STEM":
            continue
        lemmas = [f[4:] for f in tokens if f.startswith("LEM:")]
        roots = [f[5:] for f in tokens if f.startswith("ROOT:")]
        if len(lemmas) != 1 or len(roots) > 1:
            continue
        try:
            lemma = buckwalter_to_arabic(lemmas[0])
            buckwalter_to_arabic(fields["FORM"])
        except NabtError:
            continue
        group = (lemmas[0], roots[0] if roots else None, fields["TAG"])
        nominal_groups.setdefault(_candidate_key(lemma), {}).setdefault(group, set()).add(
            (row["byte_start"], row["byte_end"]))
    source_witnesses, candidate_lemmas, candidate_ids = set(), set(), set()
    witness_links = aligned = groups = 0
    for entry in entries:
        prior = original[entry["id"]]
        _require(entry["dictionary_citation"] == prior["citation"] and
                 entry["root"] == prior["root"] and entry["components"] == prior["components"] and
                 entry["interpretation_status"] == prior["interpretation_status"],
                 "A prior dictionary reading was changed")
        _require(entry["sense_licensed_for_new_occurrence"] is False and
                 entry["world_truth_asserted"] is False,
                 "Alignment must not promote a sense or world claim")
        candidates = entry["morphology_candidates"]
        _require(type(candidates) is list, "Candidate groups must be a list")
        headword = entry["source_headword"]
        _require(entry["lemma"] == (headword[2:] if headword and headword.startswith("ال") else headword),
                 "The declared headword and base lemma disagree")
        expected_groups = nominal_groups.get(_candidate_key(entry["lemma"]), {}) if entry["lemma"] else {}
        _require({(c["lemma_bw"], c["root_bw"], c["pos"]) for c in candidates} == set(expected_groups),
                 "A headword's source candidate groups were added or omitted")
        _require(entry["alignment_status"] == ("CANDIDATES_ONLY" if candidates else "UNRESOLVED"),
                 "Alignment status contradicts candidate availability")
        aligned += bool(candidates)
        for candidate in candidates:
            _require(candidate["id"] not in candidate_ids, "Duplicate morphology candidate identity")
            candidate_ids.add(candidate["id"])
            _require(candidate["contextual_sense_identified"] is False and
                     candidate["alignment_authority"] == "CONSONANTAL_HEADWORD_CANDIDATE_ONLY",
                     "Morphology candidates cannot resolve contextual senses")
            _require(candidate["pos"] in ("N", "PN", "ADJ", "T", "LOC"), "The matrix only selects nominal candidates")
            _require(candidate["lemma"] == buckwalter_to_arabic(candidate["lemma_bw"]),
                     "Candidate lemma projection changed")
            root_bw = candidate["root_bw"]
            root = (None if root_bw is None or any(c not in ROOT_BW for c in root_bw)
                    else "".join(ROOT_BW[c] for c in root_bw))
            _require(candidate["root"] == root, "Candidate root projection changed")
            expected_agreement = ("EXACT_RECORDED_LABEL" if candidate["root"] == entry["root"]
                                  else "DIFFERENT_OR_UNRESOLVED_LABEL")
            _require(candidate["root_agreement"] == expected_agreement,
                     "A different source root was hidden")
            witnesses = candidate["witnesses"]
            _require(type(witnesses) is list and bool(witnesses) and
                     type(candidate["occurrence_count"]) is int and
                     candidate["occurrence_count"] == len(witnesses),
                     "Candidate count must equal the retained witness list")
            seen = set()
            for witness in witnesses:
                span = witness["source_record"]
                lo, hi = span["byte_start"], span["byte_end"]
                _require(type(lo) is int and type(hi) is int and 0 <= lo < hi <= len(raw),
                         "Source spans use strict bounded byte integers")
                _require((lo, hi) not in seen, "A source witness was counted twice in one group")
                seen.add((lo, hi))
                row = records.get((lo, hi))
                _require(row is not None and row["valid"] is True and
                         sha256(raw[lo:hi]).hexdigest() == span["sha256"],
                         "Source witness bytes or original record boundary differ")
                fields = row["fields"]
                loc = row["locator"]
                word_loc = witness["word_locator"]
                _require(type(word_loc) is list and len(word_loc) == 3 and
                         all(type(n) is int and n > 0 for n in word_loc) and word_loc == loc[:3] and
                         witness["locator"] == fields["LOCATION"],
                         "Witness locator differs from the original record")
                _require(witness["form_bw"] == fields["FORM"] and
                         witness["surface"] == buckwalter_to_arabic(fields["FORM"]) and
                         witness["features"] == fields["FEATURES"] and
                         candidate["pos"] == fields["TAG"],
                         "Witness surface or annotation changed")
                features = fields["FEATURES"].split("|")
                _require(features[0] == "STEM" and f"POS:{candidate['pos']}" in features and
                         [f[4:] for f in features if f.startswith("LEM:")] == [candidate["lemma_bw"]] and
                         [f[5:] for f in features if f.startswith("ROOT:")] == ([] if root_bw is None else [root_bw]),
                         "Candidate features are not carried by its exact source witness")
                source_witnesses.add((lo, hi))
                witness_links += 1
            _require(seen == expected_groups[(candidate["lemma_bw"], candidate["root_bw"], candidate["pos"])],
                     "A morphology group's source occurrences were added or omitted")
            candidate_lemmas.add((candidate["lemma_bw"], candidate["pos"]))
            groups += 1
    counts = matrix["counts"]
    measured = {"catalogue_senses": len(entries), "entries_with_morphological_candidates": aligned,
                "entries_without_morphological_candidates": len(entries) - aligned,
                "candidate_groups": groups, "unique_candidate_lemmas": len(candidate_lemmas),
                "unique_candidate_source_records": len(source_witnesses),
                "cross_source_senses_licensed": 0}
    _require(all(type(counts.get(key)) is int and counts[key] == value for key, value in measured.items()),
             "Declared matrix counts contradict source replay")
    report = {"sha256": digest, "entry_count": len(entries),
              "aligned_entry_count": aligned, "unmatched_entry_count": len(entries) - aligned,
              "candidate_group_count": groups, "candidate_lemma_count": len(candidate_lemmas),
              "witness_count": len(source_witnesses), "witness_link_count": witness_links,
              "source_record_count": len(corpus["records"]),
              "cross_source_senses_licensed": 0, "source_spans_replayed": True,
              "dictionary_citations": "PINNED_PRIOR_CATALOGUE_REFERENCES",
              "authority": "SOURCE_ROW_REPLAY_AND_CANDIDATE_ALIGNMENT_ONLY"}
    return json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def load_attested_lexicon(source_path: str | Path | None = None) -> LoadedLexicon:
    """Load only the pinned corpus; a path chooses storage, never source authority.

    Downloads are explicit via ``tools/fetch_qac_source.py``. The full unchanged
    corpus is passed to ``learn_qac_lexicon``; the separate alignment matrix
    documents dictionary coverage and never filters or supplies parse answers.
    """
    path = DEFAULT_SOURCE if source_path is None else Path(source_path)
    try:
        with path.open("rb") as stream:
            payload = stream.read(MAX_PAYLOAD_BYTES + 1)
    except FileNotFoundError as error:
        raise NabtError("ATTESTED_SOURCE_UNAVAILABLE", "Fetch the pinned QAC source before selecting this profile",
                        status="DEFER", details={"path": str(path), "source_url": SOURCE_URL}) from error
    raw = _decode_source(payload)
    matrix, matrix_digest = _installed_matrix()
    matrix_receipt = _matrix_report(matrix, raw, matrix_digest)
    model = learn_qac_lexicon(raw, source_id=PROFILE_ID)
    display_path = path.resolve()
    if display_path.is_relative_to(ROOT):
        display_path = display_path.relative_to(ROOT)
    report = {
        "schema": VERSION,
        "profile_id": PROFILE_ID,
        "source": {"source_id": PROFILE_ID, "sha256": SOURCE_SHA256,
                   "byte_length": SOURCE_BYTES, "url": SOURCE_URL,
                   "path": str(display_path), "record_count": matrix_receipt.pop("source_record_count"),
                   "authority": "EXTERNAL_ANNOTATED_SOURCE_NOT_LEMMA_OR_SENSE_ORACLE"},
        "model_summary": model.summary(),
        "matrix": matrix_receipt,
        "teaching_corpus_included": False,
        "matrix_filters_runtime": False,
        "query_or_gold_used_for_source_selection": False,
        "verification_kind": "PYTHON_SOURCE_REPLAY",
        "lean_native_checked": False,
        "world_truth_asserted": False,
        "transmission_evaluated": False,
        "all_arabic_complete": False,
    }
    return LoadedLexicon(model, report)
