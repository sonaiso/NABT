"""Bounded occurrence acquisition and conditional dictionary-sense checks.

The installed full QAC supplies source-form alternatives, never a selected
meaning.  The pinned headword matrix supplies candidate links, never the
truth of their application to a new occurrence.  Lean checks the complete
finite receipt relative to those acquired donors and its installed catalogue.
The initial-reference branch is a separate receipt on the same input context.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from nabt.corpus_evidence import buckwalter_to_arabic, lookup_key
from nabt.corpus_sources import read_corpus
from nabt.discourse_context import read_context
from nabt.errors import NabtError
from nabt.person_evidence import _match
from nabt.word_reader import _source, _scan
from tools import attested_lexical_loader as loader, contextual_reference
from tools.epistemic_measurement import InputError, ResourceLimit, strict_loads, wire, digest
from tools.lexical_completion import SOURCE_PATHS
from tools.lexical_testimony import _indications

LAW_ID = "nabt.occurrence-sense-candidates.v1"
NATIVE = ROOT / "formal/.lake/build/bin/occurrenceSense"
SOURCE_REVIEW = ROOT / "evidence/occurrence_sense_v1/source_review.json"
SOURCE_REVIEW_SHA256 = "845ce9ae8a72333cdba300f3c4d7a529b0afa8826a15ac4681dc8ddfd2533e6a"
MAX_INPUT_BYTES = 65536
MAX_NATIVE_BYTES = 1024 * 1024
MAX_DONORS = 4096
MAX_BUDGET = 1_000_000
MAX_GROUPS = 256
FALSE_FLAGS = {"contextual_sense_selected", "world_truth_established", "whole_clause_checked",
               "reference_transferred", "all_arabic_complete"}
RECEIPT_FIELDS = {"binding", "budget", "status", "readings"}
NATIVE_FIELDS = RECEIPT_FIELDS | FALSE_FLAGS | {"law_id", "observed_status", "certificate_checked"}
DECISIONS = {"CANDIDATES_ONLY", "PARTIAL_CANDIDATES", "NO_DICTIONARY_CANDIDATE",
             "NO_MORPHOLOGY_READING", "RESOURCE_LIMIT"}
SCOPE = {
    "occurrence": "OUTER_WRITTEN_RUN_AT_ZERO_BASED_TOKEN_INDEX",
    "morphology": "ALL_COMPATIBLE_VALID_QAC_STEM_RECORDS_UNDER_INSTALLED_SURFACE_POLICY",
    "spelling_policy": "EXISTING_PR43_SURFACE_MATCH_WITH_NO_MUTABLE_VOWEL_POSITIONS",
    "source_acquisition": "PYTHON_PINNED_FULL_SOURCE_REPLAY_PREMISE",
    "finite_enumeration": "LEAN_CHECKED_RELATIVE_TO_SUPPLIED_DONORS_AND_INSTALLED_LINKS",
    "indications": "CONDITIONAL_ON_CATALOGUE_SENSE_APPLICATION_NOT_ESTABLISHED_HERE",
    "budget_unit": "DISTINCT_SOURCE_FORM_LEMMA_ROOT_POS_GROUPS",
    "effective_group_budget": "MIN_REQUESTED_BUDGET_AND_256_INSTALLED_GROUP_LIMIT",
    "initial_reference": "SEPARATE_INITIAL_OCCURRENCE_RECEIPT_ON_THE_SAME_CONTEXT",
    "no_candidate_status": "NO_MATCH_IN_INSTALLED_SCOPE_NOT_LINGUISTIC_REJECTION",
    "context_truth_established": False,
    "sense_licensed_for_new_occurrence": False,
    **{key: False for key in FALSE_FLAGS},
}
_RUNTIME_FILES = ("tools/occurrence_sense.py", "tools/attested_lexical_loader.py",
    "tools/contextual_reference.py", "tools/lexical_completion.py", "tools/lexical_testimony.py",
    "tools/epistemic_measurement.py", "src/nabt/corpus_evidence.py", "src/nabt/corpus_sources.py",
    "src/nabt/person_evidence.py", "src/nabt/word_reader.py", "src/nabt/discourse_context.py")


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nabt import foundation

def _hash(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _bounded_text(value: Any, limit: int, *, controls: bool = False) -> str:
    if type(value) is not str or not value.strip() or (not controls and any(ord(c) < 32 for c in value)):
        raise InputError("Expected nonempty text without control characters")
    if len(value.encode("utf-8", "strict")) > limit:
        raise ResourceLimit("Text byte limit")
    return value


def validate_input(request: Any) -> dict:
    if type(request) is not dict or set(request) != {"text", "context", "token_index", "target", "budget"}:
        raise InputError("Use exactly text, context, token_index, target and budget")
    contextual_reference.validate_input({"text": request["text"], "context": request["context"]})
    for field in ("token_index", "budget"):
        if type(request[field]) is not int or request[field] < 0:
            raise InputError(field + " must be a nonnegative integer, not a Boolean")
    if request["token_index"] >= 128 or request["budget"] > MAX_BUDGET:
        raise ResourceLimit("Occurrence index or enumeration budget exceeds the installed bound")
    target = request["target"]
    if type(target) is not list or not target:
        raise InputError("target must be a nonempty array of exact semantic components")
    if len(target) > 32:
        raise ResourceLimit("Target component count")
    for component in target:
        _bounded_text(component, 2048)
    if len(set(target)) != len(target):
        raise InputError("Target components must be distinct")
    if len(wire(request).encode("utf-8")) > MAX_INPUT_BYTES:
        raise ResourceLimit("Input byte limit")
    return deepcopy(request)


def _occurrence(text: str, index: int) -> dict:
    tokens = [row for row in _scan(_source(text, "occurrence_sense_input", "outer"))
              if row["kind"] == "written_run"]
    if index >= len(tokens):
        raise InputError("token_index does not name an outer written run")
    token = tokens[index]
    _bounded_text(token["surface"], 4096)
    return {"start_byte": token["span"]["start"], "end_byte": token["span"]["end"],
            "surface": token["surface"]}


def _catalogue() -> tuple[dict, dict]:
    raw = loader.CATALOGUE_PATH.read_bytes()
    if _hash(raw) != loader.CATALOGUE_SHA256:
        raise InputError("Installed catalogue identity changed")
    catalogue = strict_loads(raw)
    sources = {work: (ROOT / path).read_bytes() for work, path in SOURCE_PATHS.items()}
    identities = {work: _hash(value) for work, value in sources.items()}
    for row in catalogue["senses"] + catalogue["necessities"]:
        citation = row["citation"]
        source = sources[citation["work"]]
        lo, hi = citation["start_byte"], citation["end_byte"]
        if (type(lo) is not int or type(hi) is not int or not 0 <= lo < hi <= len(source)
                or identities[citation["work"]] != citation["source_sha256"]
                or source[lo:hi] != citation["quotation"].encode("utf-8")):
            raise InputError("Installed dictionary citation does not replay")
    return catalogue, identities


def _installed() -> tuple[Any, dict, dict, dict]:
    if _hash(SOURCE_REVIEW.read_bytes()) != SOURCE_REVIEW_SHA256:
        raise InputError("Installed occurrence source review identity changed")
    old_identity = contextual_reference.identity()
    loaded = loader.load_attested_lexicon()
    matrix, _ = loader._installed_matrix()
    catalogue, sources = _catalogue()
    snapshot = {
        "law_id": LAW_ID,
        "source_review_sha256": SOURCE_REVIEW_SHA256,
        "qac_sha256": _hash(loaded.model.raw),
        "qac_payload_sha256": _hash(loader.DEFAULT_SOURCE.read_bytes()),
        "matrix_sha256": loader.MATRIX_SHA256,
        "catalogue_sha256": loader.CATALOGUE_SHA256,
        "dictionary_source_sha256": sources,
        "initial_reference_identity": old_identity,
        "runtime_dependencies": {path: _hash((ROOT / path).read_bytes()) for path in _RUNTIME_FILES},
        "native_sha256": _hash(NATIVE.read_bytes()) if NATIVE.is_file() else None,
    }
    snapshot["source_registry_sha256"] = digest({key: value for key, value in snapshot.items()
        if key not in {"native_sha256", "runtime_dependencies", "initial_reference_identity"}})
    return loaded, matrix, catalogue, snapshot


def identity() -> dict:
    return _installed()[3]


@lru_cache(maxsize=1)
def _source_index(raw: bytes) -> dict[str, tuple]:
    """Index the full immutable source, without the 42-sense selection filter."""
    if _hash(raw) != loader.SOURCE_SHA256:
        raise InputError("Uninstalled morphology source")
    index: dict[str, list] = {}
    for row in read_corpus(raw, format="qac", source_id=loader.PROFILE_ID)["records"]:
        fields = row["fields"]
        if not row["valid"] or fields["FEATURES"].split("|")[0] != "STEM":
            continue
        form = buckwalter_to_arabic(fields["FORM"])
        key = lookup_key(form)
        if key is None:
            continue  # Outside the installed spelling profile, not rejected Arabic.
        index.setdefault(key, []).append((form, row["identity"], row["byte_start"], row["byte_end"]))
    return {key: tuple(rows) for key, rows in index.items()}


def _donors(surface: str, raw: bytes) -> list[dict]:
    result = []
    for form, ident, lo, hi in _source_index(raw).get(lookup_key(surface), ()):
        if _match(surface, form, mutable=()):
            result.append({"id": ident, "source_id": loader.PROFILE_ID,
                "source_revision": loader.SOURCE_SHA256, "start_byte": lo, "end_byte": hi,
                "record": raw[lo:hi].decode("utf-8")})
    if len(result) > MAX_DONORS:
        raise ResourceLimit("Compatible source-record count exceeds donor budget")
    return result


def _build(request: dict, loaded: Any) -> dict:
    text = request["text"]
    occurrence = _occurrence(text, request["token_index"])
    result = {"source": {"id": "occurrence_sense_input", "revision": _hash(text.encode("utf-8")), "text": text},
        "occurrence": occurrence, "token_index": request["token_index"],
        "context_binding": wire(request["context"]), "donors": _donors(occurrence["surface"], loaded.model.raw),
        "target": deepcopy(request["target"]), "budget": request["budget"], "proposed": None}
    validate_payload(result)
    return result


def build_request(request: Any) -> dict:
    request = validate_input(request)
    loaded, _, _, _ = _installed()
    return _build(request, loaded)


def _parse_donor(donor: dict, surface: str) -> tuple:
    if type(donor) is not dict or set(donor) != {"id", "source_id", "source_revision", "start_byte", "end_byte", "record"}:
        raise InputError("Malformed source donor")
    _bounded_text(donor["id"], 256)
    if donor["source_id"] != loader.PROFILE_ID or donor["source_revision"] != loader.SOURCE_SHA256:
        raise InputError("Donor source labels are outside installed QAC")
    lo, hi, record = donor["start_byte"], donor["end_byte"], donor["record"]
    _bounded_text(record, 4096, controls=True)
    if (type(lo) is not int or type(hi) is not int or not 0 <= lo < hi <= loader.SOURCE_BYTES
            or hi - lo != len(record.encode("utf-8"))):
        raise InputError("Donor byte boundaries do not match its exact record")
    fields = record.rstrip("\r\n").split("\t")
    if len(fields) != 4:
        raise InputError("Donor is not one four-field QAC record")
    tokens = fields[3].split("|")
    if not tokens or tokens[0] != "STEM" or [t for t in tokens if t.startswith("POS:")] != ["POS:" + fields[2]]:
        raise InputError("Source POS annotation is malformed")
    values = []
    for prefix in ("LEM:", "ROOT:"):
        found = [token[len(prefix):] for token in tokens if token.startswith(prefix)]
        if len(found) > 1 or any(not value for value in found):
            raise InputError("Ambiguous or empty source lemma/root annotation")
        values.append(found[0] if found else None)
    form = buckwalter_to_arabic(fields[1])
    if not _match(surface, form, mutable=()):
        raise InputError("Source FORM does not support the occurrence spelling")
    return form, values[0], values[1], fields[2]


def validate_payload(payload: Any) -> None:
    if type(payload) is not dict or set(payload) != {"source", "occurrence", "token_index", "context_binding", "donors", "target", "budget", "proposed"}:
        raise InputError("Malformed native acquisition request")
    source = payload["source"]
    if type(source) is not dict or set(source) != {"id", "revision", "text"}:
        raise InputError("Malformed raw source binding")
    _bounded_text(source["id"], 256)
    _bounded_text(source["revision"], 256)
    if type(payload["context_binding"]) is not str:
        raise InputError("Context binding must be canonical JSON text")
    context = strict_loads(payload["context_binding"])
    if wire(context) != payload["context_binding"]:
        raise InputError("Context binding is not canonical")
    validate_input({"text": source["text"], "context": context, "token_index": payload["token_index"],
                    "target": payload["target"], "budget": payload["budget"]})
    if wire(payload["occurrence"]) != wire(_occurrence(source["text"], payload["token_index"])):
        raise InputError("Occurrence is not the exact indexed outer written run")
    if type(payload["donors"]) is not list:
        raise InputError("Donors must be an array")
    if len(payload["donors"]) > MAX_DONORS or len(wire(payload).encode("utf-8")) > MAX_NATIVE_BYTES:
        raise ResourceLimit("Native acquisition payload limit")
    ids = set()
    for donor in payload["donors"]:
        _parse_donor(donor, payload["occurrence"]["surface"])
        if donor["id"] in ids:
            raise InputError("Duplicate source donor identity")
        ids.add(donor["id"])


def _links(matrix: dict) -> list[dict]:
    return [{"lemma_bw": row["lemma_bw"], "root_bw": row["root_bw"], "pos": row["pos"], "sense_id": entry["id"]}
            for entry in matrix["entries"] for row in entry["morphology_candidates"]]


def exported(matrix: dict, catalogue: dict) -> dict:
    return {"law_id": LAW_ID, "matrix_sha256": loader.MATRIX_SHA256,
        "catalogue_sha256": loader.CATALOGUE_SHA256, "links": _links(matrix), "catalogue": {
            "law_id": "nabt.lexical-completion.v1", "catalogue_id": catalogue["catalogue_id"],
            "semantic_law": catalogue["law_id"],
            "senses": [{key: sense[key] for key in ("id", "root", "citation", "components")} for sense in catalogue["senses"]],
            "necessities": [{key: row[key] for key in ("sense_id", "target", "kind", "citation")} for row in catalogue["necessities"]]}}


def propose(payload: dict, *, matrix: dict | None = None, catalogue: dict | None = None) -> dict:
    """Python cross-check; no result from this function is native evidence."""
    validate_payload(payload)
    if matrix is None:
        matrix, _ = loader._installed_matrix()
    if catalogue is None:
        catalogue, _ = _catalogue()
    groups: dict[tuple, list] = {}
    for donor in payload["donors"]:
        groups.setdefault(_parse_donor(donor, payload["occurrence"]["surface"]), []).append(donor["id"])
    receipt = {"binding": {key: deepcopy(payload[key]) for key in
               ("source", "occurrence", "token_index", "context_binding", "target")},
               "budget": payload["budget"], "status": "RESOURCE_LIMIT", "readings": []}
    if len(groups) > min(payload["budget"], MAX_GROUPS):
        return receipt
    links = _links(matrix)
    for (form, lemma, root, pos), donor_ids in groups.items():
        sense_ids = {link["sense_id"] for link in links
                     if (link["lemma_bw"], link["root_bw"], link["pos"]) == (lemma, root, pos)}
        senses = []
        for sense in catalogue["senses"]:
            if sense["id"] in sense_ids:
                modes = _indications(sense, payload["target"], catalogue["necessities"]) if sense["components"] else []
                senses.append({"id": sense["id"], **{mode: mode in modes for mode in ("mutabaqa", "tadammun", "iltizam")}})
        receipt["readings"].append({"source_form": form, "lemma_bw": lemma, "root_bw": root,
            "pos": pos, "donor_ids": donor_ids, "status": "CANDIDATES_ONLY" if senses else "UNMATCHED_READING", "senses": senses})
    rows = receipt["readings"]
    receipt["status"] = ("NO_MORPHOLOGY_READING" if not rows else
        "NO_DICTIONARY_CANDIDATE" if not any(row["senses"] for row in rows) else
        "PARTIAL_CANDIDATES" if not all(row["senses"] for row in rows) else "CANDIDATES_ONLY")
    return receipt


def _native(payload: dict | None = None) -> dict:
    if payload is not None:
        validate_payload(payload)
    process = subprocess.run([str(NATIVE)] + (["--export"] if payload is None else []),
        input=None if payload is None else wire(payload) + "\n", capture_output=True,
        text=True, encoding="utf-8", timeout=30, check=False)
    if process.returncode != 0:
        raise InputError("Native checker process failed")
    if len(process.stdout.encode("utf-8")) > MAX_NATIVE_BYTES:
        raise ResourceLimit("Native output limit")
    return strict_loads(process.stdout)


def _native_agrees(result: Any, proposal: dict) -> bool:
    return (type(result) is dict and set(result) == NATIVE_FIELDS
        and result["law_id"] == LAW_ID and result["certificate_checked"] is True
        and all(result[key] is False for key in FALSE_FLAGS)
        and result["observed_status"] == proposal["status"]
        and wire({key: result[key] for key in RECEIPT_FIELDS}) == wire(proposal))


def _reference_bound(reference: dict, request: dict) -> bool:
    wanted = {"text": request["text"], "context": request["context"]}
    if (wire(reference.get("input")) != wire(wanted) or reference.get("input_sha256") != digest(wanted)
            or reference.get("context_sha256") != digest(request["context"])):
        return False
    replay = reference.get("execution", {}).get("input")
    if replay is not None:
        context = read_context(request["context"])["value"]
        context = {**context, "speaker": context.get("speaker"), "addressee": context.get("addressee")}
        if wire(replay.get("context")) != wire(context) or replay.get("source", {}).get("text") != request["text"]:
            return False
    return True


def assess(request: Any) -> dict:
    foundation.require_foundation('tools.occurrence_sense.assess')
    answer = {"schema": "nabt.occurrence-sense-observation.v1", "law_id": LAW_ID,
        "status": "UNMEASURED", "native_checked": False, "certificate_checked": False,
        "input": None, "input_sha256": None, "context_sha256": None, "occurrence": None,
        "readings": [], "candidate_senses": [], "initial_reference": None,
        "identity": None, "source_bindings": [], "scope": deepcopy(SCOPE),
        **{key: False for key in FALSE_FLAGS},
        "execution": {"input": None, "input_sha256": None, "proposal": None,
            "proposal_sha256": None, "native_export_sha256": None, "native_result": None,
            "native_result_sha256": None, "error": None}}
    phase = "input"
    try:
        request = validate_input(request)
        foundation.validate_source(request["text"])
        answer.update(input=deepcopy(request), input_sha256=digest(request), context_sha256=digest(request["context"]))
        answer["occurrence"] = _occurrence(request["text"], request["token_index"])
        phase = "installed"
        loaded, matrix, catalogue, before = _installed()
        answer["identity"] = before
        payload = _build(request, loaded)
        answer["source_bindings"] = deepcopy(payload["donors"])
        proposal = propose(payload, matrix=matrix, catalogue=catalogue)
        payload["proposed"] = deepcopy(proposal)
        validate_payload(payload)
        execution = answer["execution"]
        execution.update(input=payload, input_sha256=digest(payload), proposal=proposal, proposal_sha256=digest(proposal))
        # The reference branch retains its own occurrence. There is no clause
        # syntax rule here connecting that referent to this selected token.
        reference = contextual_reference.execute_request({"text": request["text"], "context": request["context"]})
        if not _reference_bound(reference, request):
            raise InputError("Initial-reference receipt is not bound to the input context")
        answer["initial_reference"] = reference
        if before["native_sha256"] is None:
            execution["error"] = "NATIVE_UNAVAILABLE"
        else:
            native_export = _native()
            execution["native_export_sha256"] = digest(native_export)
            if wire(native_export) != wire(exported(matrix, catalogue)):
                raise InputError("Native installed catalogue/link export mismatch")
            result = _native(payload)
            execution.update(native_result=result, native_result_sha256=digest(result))
            if not _native_agrees(result, proposal):
                raise InputError("Native certificate disagrees with the complete proposed receipt")
            after = identity()
            if wire(before) != wire(after):
                raise InputError("Installed source, runtime or native identity changed during execution")
            answer.update(status=proposal["status"], native_checked=True, certificate_checked=True,
                          readings=deepcopy(proposal["readings"]))
            ids = {sense["id"] for row in answer["readings"] for sense in row["senses"]}
            answer["candidate_senses"] = [{"id": entry["id"], "source_headword": entry["source_headword"],
                "dictionary_citation": deepcopy(entry["dictionary_citation"]), "components": deepcopy(entry["components"]),
                "interpretation_status": entry["interpretation_status"], "conditional_only": True,
                "sense_licensed_for_new_occurrence": False,
                "residuals": sorted(set(entry["residuals"]) | {"CROSS_SOURCE_SENSE_ALIGNMENT_UNADJUDICATED",
                    "DICTIONARY_HEADWORD_VOCALIZATION_UNRESOLVED"})}
                for entry in matrix["entries"] if entry["id"] in ids]
    except (ResourceLimit, subprocess.TimeoutExpired) as error:
        answer["status"] = "RESOURCE_LIMIT"
        answer["execution"]["error"] = str(error)
    except (InputError, NabtError, OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError) as error:
        answer["status"] = ("RESOURCE_LIMIT" if isinstance(error, NabtError) and error.code == "RESOURCE_LIMIT"
                            else "INVALID_INPUT" if phase == "input" else "UNMEASURED")
        answer["execution"]["error"] = str(error)
    answer["receipt_sha256"] = digest(answer)
    return answer


def main() -> int:
    foundation.require_foundation('tools.occurrence_sense.main')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, help="Strict UTF-8 JSON request file; '-' reads stdin")
    args = parser.parse_args()
    try:
        if args.request == "-":
            raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        else:
            with Path(args.request).open("rb") as stream:
                raw = stream.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ResourceLimit("Input byte limit")
        result = assess(strict_loads(raw))
    except (ResourceLimit, InputError, ValueError, OSError, UnicodeError) as error:
        result = {"law_id": LAW_ID, "status": "RESOURCE_LIMIT" if isinstance(error, ResourceLimit) else "INVALID_INPUT",
            "native_checked": False, "certificate_checked": False, "error": str(error),
            **{key: False for key in FALSE_FLAGS}}
    print(wire(result))
    return 0 if result.get("native_checked") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
