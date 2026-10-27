"""Source-replayed, catalogue-relative composition of ordered dictionary slots.

Lean supplies the executable verdict. Python verifies provenance and transport;
it neither parses free Arabic nor promotes a retrieved definition to a fact.
No implicit network requests, caller-defined law, vector score, or truth flag.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from nabt.source_lexicon import SourceLexicon
from tools.lexical_testimony import _strict_json, _native, _indications

CATALOG = Path("evidence/lexical_completion_v1/catalog.json")
CATALOG_SHA = "1ac5b25629f7847e9f128cf2c75cfbe573657df769446afae3cc3436f566a872"
LAW = "nabt.lexical-completion.v1"
LIMIT = 512
SOURCE_PATHS = {
    "lisan": "artifacts/local/lisan.txt",
    "maqayis": "evidence/classical_language/sources/maqayis.txt",
    "shakhsiyya3": "evidence/mantuq_mafhum/sources/shakhsiyya3.txt",
}
DISCLAIMER = ("الاكتمال هنا بالنسبة إلى القراءات المثبتة وفهارسها المعجمية فقط؛ "
              "صدق التفسير وقاعدة اللزوم مقدمات، والتواتر والمراد والواقع غير مثبتة.")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    # Unlike Python equality this distinguishes Boolean values from numbers.
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate(request):
    if type(request) is not dict or set(request) != {"slots"}:
        raise ValueError("INVALID_INPUT")
    slots = request["slots"]
    if type(slots) is not list or not slots:
        raise ValueError("INVALID_INPUT")
    if len(slots) > 8:
        raise ValueError("RESOURCE_LIMIT")

    def text(value, limit):
        if type(value) is not str or not value.strip() or any(ord(c) < 32 for c in value):
            raise ValueError("INVALID_INPUT")
        if len(value.encode("utf-8")) > limit:
            raise ValueError("RESOURCE_LIMIT")

    for slot in slots:
        if type(slot) is not dict or set(slot) != {"entry", "target"}:
            raise ValueError("INVALID_INPUT")
        text(slot["entry"], 128)
        if type(slot["target"]) is not list:
            raise ValueError("INVALID_INPUT")
        if len(slot["target"]) > 64:
            raise ValueError("RESOURCE_LIMIT")
        for component in slot["target"]:
            text(component, 4096)
    # Match the JSONL transport's whole-line bound as well as per-field bounds.
    if len(json.dumps(request, ensure_ascii=False).encode("utf-8")) > 1024 * 1024:
        raise ValueError("RESOURCE_LIMIT")


def replay(citation, sources):
    start, end = citation["start_byte"], citation["end_byte"]
    raw = sources[citation["work"]]
    quotation = citation["quotation"].encode("utf-8")
    if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(raw)
            or end - start != len(quotation) or sha(raw) != citation["source_sha256"]
            or raw[start:end] != quotation):
        raise ValueError("SOURCE_BYTES_CHANGED")


class CompletionEngine:
    """Immutable in-memory snapshot; rebuild the engine after a source update."""

    def __init__(self, root=ROOT):
        self.root = Path(root)
        raw = (self.root / CATALOG).read_bytes()
        if sha(raw) != CATALOG_SHA:
            raise ValueError("CATALOGUE_IDENTITY_CHANGED")
        self.catalogue = _strict_json(raw)
        self.sources = {work: (self.root / path).read_bytes() for work, path in SOURCE_PATHS.items()}
        self.indexes = {work: SourceLexicon(work, self.sources[work]) for work in ("lisan", "maqayis")}
        for reading in self.catalogue["senses"] + self.catalogue["necessities"]:
            replay(reading["citation"], self.sources)
        self.exe = self.root / "formal/.lake/build/bin/lexicalCompletion"

    def exported(self):
        return {"law_id": LAW, "catalogue_id": self.catalogue["catalogue_id"],
                "semantic_law": self.catalogue["law_id"],
                "senses": [{k: s[k] for k in ("id", "root", "citation", "components")}
                           for s in self.catalogue["senses"]],
                "necessities": [{k: r[k] for k in ("sense_id", "target", "kind", "citation")}
                                for r in self.catalogue["necessities"]]}

    def inventory(self):
        senses = self.catalogue["senses"]
        return {"catalogue_readings": len(senses),
                "interpreted_readings": sum(bool(s["components"]) for s in senses),
                "unresolved_readings": sum(not s["components"] for s in senses),
                "entry_indices": len({s["root"] for s in senses}),
                "mental_rules": len(self.catalogue["necessities"]),
                "independently_adjudicated_readings": 0,
                "whole_arabic_denominator": None,
                "source_indexes": {k: v.inventory() for k, v in self.indexes.items()}}

    def expected_native(self, slots):
        """Transport cross-check only; not counted as an independent benchmark."""
        pools, result_slots = [], []
        unknown = unresolved = False
        for i, slot in enumerate(slots):
            senses = [s for s in self.catalogue["senses"] if s["root"] == slot["entry"]]
            readings = []
            for sense in senses:
                indications = (_indications(sense, slot["target"], self.catalogue["necessities"])
                               if sense["components"] else [])
                readings.append({"sense_id": sense["id"], "definition_present": bool(sense["components"]),
                                 "indications": indications})
                unresolved |= not sense["components"]
            unknown |= not senses
            pools.append([(r["sense_id"], bool(r["indications"])) for r in readings]
                         or [("UNMEASURED:" + slot["entry"], False)])
            result_slots.append({"position": i, **slot, "readings": readings})
        count = 1
        for pool in pools:
            count *= len(pool)
        exhausted = count > LIMIT
        rows = [] if exhausted else [{"sense_ids": [s[0] for s in row],
                                      "targets_licensed": all(s[1] for s in row)}
                                     for row in itertools.product(*pools)]
        all_ready = None if exhausted else all(row["targets_licensed"] for row in rows)
        status = ("RESOURCE_EXHAUSTED" if exhausted else
                  "UNMEASURED_ENTRY" if unknown else
                  "UNMEASURED_DEFINITION" if unresolved else
                  "CONDITIONAL_ALL_READINGS" if all_ready else
                  "CONDITIONAL_SOME_READINGS" if any(r["targets_licensed"] for r in rows) else
                  "NO_LICENSE_FOR_TARGETS")
        return {"law_id": LAW, "status": status, "combination_count": count, "combination_limit": LIMIT,
                "all_installed_combinations_checked": not exhausted, "all_targets_licensed": all_ready,
                "slots": result_slots, "combinations": rows}

    def assess(self, request):
        validate(request)
        binary_sha = sha(self.exe.read_bytes())
        if canonical(_native(self.exe)) != canonical(self.exported()):
            raise ValueError("NATIVE_CATALOGUE_DIFFERS")
        native = _native(self.exe, request)
        if canonical(native) != canonical(self.expected_native(request["slots"])):
            raise ValueError("NATIVE_RESULT_DIFFERS")
        if sha(self.exe.read_bytes()) != binary_sha:
            raise ValueError("NATIVE_CHANGED_DURING_EXECUTION")
        retrieval, testimony = [], []
        for i, slot in enumerate(request["slots"]):
            found = []
            for work, index in self.indexes.items():
                # Return source coordinates, not full large dictionary articles.
                found.extend({"work": work, "start_byte": b.start_byte, "end_byte": b.end_byte,
                              "heading": b.heading, "block_sha256": b.block_sha256}
                             for b in index.blocks if b.heading == slot["entry"])
            retrieval.append({"position": i, "blocks": found, "authority": "SOURCE_TEXT_RETRIEVAL_ONLY"})
            for sense in self.catalogue["senses"]:
                if sense["root"] == slot["entry"]:
                    testimony.append({"position": i, **sense, "source_file_replayed": True,
                                      "transmission_type": "UNASSESSED"})
        return {"schema": LAW, "status": native["status"],
                "native_checked": True, "native_sha256": binary_sha, "catalogue_sha256": CATALOG_SHA,
                "request_sha256": sha(canonical(request).encode()), "native_request": request,
                "native_result": native, "testimonies": testimony, "retrieval": retrieval,
                "source_sha256": {k: sha(v) for k, v in self.sources.items()},
                "necessities": self.catalogue["necessities"],
                "scope": "ORDERED_DICTIONARY_SLOTS_WITHIN_INSTALLED_CATALOGUE",
                "all_arabic_complete": False, "world_truth_established": False,
                "transmission_type": "UNASSESSED", "free_text_parsing_established": False,
                "app_disclaimer": DISCLAIMER}


def assess(request, *, engine=None):
    failed = {"schema": LAW, "status": "INVALID_INPUT", "native_checked": False,
              "all_arabic_complete": False, "world_truth_established": False,
              "app_disclaimer": DISCLAIMER}
    try:
        validate(request)
    except (ValueError, UnicodeError) as exc:
        return {**failed, "status": "RESOURCE_LIMIT" if str(exc) == "RESOURCE_LIMIT" else "INVALID_INPUT"}
    try:
        engine = engine or CompletionEngine()
    except (OSError, ValueError, KeyError):
        return {**failed, "status": "SOURCE_UNAVAILABLE"}
    try:
        return engine.assess(request)
    except subprocess.TimeoutExpired:
        return {**failed, "status": "RESOURCE_EXHAUSTED"}
    except ValueError as exc:
        return {**failed, "status": ("RESOURCE_EXHAUSTED" if str(exc) == "NATIVE_RESPONSE_LIMIT"
                                      else "VERIFICATION_UNAVAILABLE")}
    except (OSError, KeyError, subprocess.CalledProcessError):
        return {**failed, "status": "VERIFICATION_UNAVAILABLE"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--request", type=Path, help="UTF-8 JSON with an ordered slots array")
    p.add_argument("--inventory", action="store_true")
    a = p.parse_args()
    if a.inventory:
        result = CompletionEngine().inventory()
    elif a.request:
        try:
            if a.request.stat().st_size > 1024 * 1024:
                result = {**assess(None), "status": "RESOURCE_LIMIT"}
            else:
                result = assess(_strict_json(a.request.read_bytes().decode("utf-8")))
        except (OSError, ValueError, UnicodeError):
            result = assess(None)
    else:
        p.error("--request or --inventory is required")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if a.inventory or result["native_checked"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
