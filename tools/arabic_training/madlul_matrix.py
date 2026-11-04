"""Source-bound denotatum taxonomy aligned with existing NABT contracts.

The five kinds describe the denoted object, not the grammatical kind of the
denoting expression. This is an executable crosswalk and owner-report view,
not a new classifier, interpreter, theorem catalogue or source of authority.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

from nabt.derivation import read_derivation
from nabt.errors import NabtError
from nabt.learning.source_evidence import SourceBlob, SourceSpan
from nabt.text_morphology import read_text_morphology
from nabt.word_reader import read_words
from tools.entropy_framework.registry import load_json
from tools.entropy_framework.reuse import current_catalog

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = "evidence/madlul_matrix_v1/catalog.json"
CATALOG_SHA256 = "ee07f18d38c93746523d7a9bd643a1fd24e0caeea1dc7963d0d80533575f1995"
AUTHORITY = "SOURCE_BOUND_CROSSWALK_NOT_RUNTIME_SEMANTIC_LICENSE"
KIND_IDS = ("meaning", "used_simple_expression", "unused_simple_expression",
            "used_compound_expression", "unused_compound_expression")
MAX_TEXT_BYTES = 8192


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _path(relative):
    if type(relative) is not str or not relative:
        raise ValueError("repository path required")
    p = Path(relative)
    full = ROOT / p
    if p.is_absolute() or p.as_posix() != relative or ".." in p.parts or full.resolve() != full:
        raise ValueError("canonical repository file required")
    if not full.is_file():
        raise ValueError("missing repository file: " + relative)
    return full


def _catalog():
    path = _path(CATALOG_PATH)
    if path.stat().st_size > 1024 * 1024 or sha256(path.read_bytes()).hexdigest() != CATALOG_SHA256:
        raise ValueError("madlul catalogue changed; review its source contract")
    d = load_json(path)
    if d["schema"] != "nabt.madlul-matrix.v1" or d["authority"] != AUTHORITY:
        raise ValueError("unexpected matrix schema or authority")
    if [r["id"] for r in d["kinds"]] != list(KIND_IDS):
        raise ValueError("five-way source taxonomy differs")
    if any(type(r["code"]) is not int or r["code"] != i for i,r in enumerate(d["kinds"])):
        raise ValueError("kind codes are exact natural ordinals, not evidence")
    return d


def _sources(d):
    sources = {}
    for s in d["sources"]:
        if s["id"] in sources:
            raise ValueError("duplicate source")
        source = SourceBlob(s["id"], _path(s["path"]).read_bytes())
        if source.sha256 != s["sha256"]:
            raise ValueError("source bytes changed: " + s["id"])
        sources[s["id"]] = source
    seen = set()
    for a in d["anchors"]:
        if a["id"] in seen:
            raise ValueError("duplicate source anchor")
        seen.add(a["id"])
        s = sources[a["source_id"]]
        SourceSpan(s.source_id, s.sha256, a["start"], a["end"], a["sha256"]).extract(s)
        loc = a["locator"]
        if "lines_inclusive" in loc:
            first, last = loc["lines_inclusive"]
            lines = s.raw_bytes.splitlines(keepends=True)
            if (type(first) is not int or type(last) is not int or
                not 1 <= first <= last <= len(lines) or
                a["start"] != sum(map(len,lines[:first-1])) or
                a["end"] != sum(map(len,lines[:last]))):
                raise ValueError("line locator does not match byte anchor")
    return sources


def matrix():
    d = _catalog()
    sources = _sources(d)
    catalog, path, _, _ = current_catalog(ROOT)
    declarations = {r["name"]:r for r in catalog["theorems"]}
    owners = {r["id"]:r for r in d["owners"]}
    anchors = {a["id"]:a for a in d["anchors"]}
    if len(owners) != len(d["owners"]) or len({r["id"] for r in d["rows"]}) != len(d["rows"]):
        raise ValueError("duplicate owner or row")
    resolved = []
    for o in d["owners"]:
        for name in o["declarations"]:
            decl = declarations.get(name)
            if decl is None or decl["module"] != o["module"]:
                raise ValueError("unresolved compiled owner: " + name)
            resolved.append({"name":name,"module":decl["module"],
                             "statement_sha256":decl["statement_sha256"]})
        for p in o["runtime_paths"]:
            _path(p)
    for kind in d["kinds"]:
        if kind["anchor"] not in anchors:
            raise ValueError("kind source missing")
    for row in d["rows"]:
        if not row["anchors"] or not row["owners"] or not row["required_evidence"]:
            raise ValueError("row lacks its source, owner or premises")
        if any(x not in owners for x in row["owners"]) or any(x not in anchors for x in row["anchors"]):
            raise ValueError("unresolved row link")
    design = json.loads(sources["interpretation_design"].raw_bytes)
    wanted = d["interpretation_design"]["contract_ids"]
    if [x["id"] for x in design["contracts"]] != wanted:
        raise ValueError("interpretation design inventory differs")
    return {**d, "catalog_sha256":CATALOG_SHA256,
            "source_bytes_replayed":True, "interpretation_authenticity_proved":False,
            "proof_catalogue":{"path":path,"status":"RECORDED_COMPILED_SNAPSHOT_WITH_CURRENT_SOURCE_MATCH",
                               "compiled_this_run":False,"resolved_declarations":resolved},
            "interpretation_guards":[{k:r[k] for k in ("id","topic","engineering_contract","boundary")}
                                     for r in design["contracts"]],
            "counts":{"denotatum_kinds":len(d["kinds"]),"crosswalk_rows":len(d["rows"]),
                      "source_anchors":len(d["anchors"]),"owners":len(owners),
                      "resolved_declarations":len(resolved),"interpretation_guards":len(wanted)},
            "runtime_execution_performed":False}


def kind_by_code(code):
    """Decode a declared ordinal. Never infer a kind from a word or A116 id."""
    if type(code) is not int or not 0 <= code < len(KIND_IDS):
        raise ValueError("kind code must be an integer in this five-element domain")
    return _catalog()["kinds"][code]


def inspect_text(text, *, source_id="madlul_input", scope="madlul_diagnostic"):
    if type(text) is not str or not text or len(text.encode("utf-8", "strict")) > MAX_TEXT_BYTES:
        raise ValueError("nonempty bounded UTF-8 text required")
    m = matrix()
    # These are the original readers and reports. No status is promoted and no
    # owner's report is silently used as a denotatum or external-world judgment.
    reports, failures = {}, {}
    for name, reader in (("word", read_words),
                         ("text_morphology", read_text_morphology),
                         ("derivation", read_derivation)):
        try:
            reports[name] = reader(text,source_id=source_id,scope=scope)
        except NabtError as error:
            # Keep the owner's structured failure, without manufacturing an
            # owner report or treating its limit as a denotatum classification.
            failures[name] = error.as_dict()
    return {"schema":"nabt.madlul-owner-view.v1","authority":AUTHORITY,
            "input":{"text":text,"source_id":source_id,"scope":scope},
            "source_sha256":sha256(text.encode()).hexdigest(),"catalog_sha256":m["catalog_sha256"],
            "owner_reports":reports,"owner_failures":failures,
            "denotatum":{"status":"DEFER","candidate_kinds":list(KIND_IDS),
                         "missing":["DENOTATUM_OBJECT_LEVEL","PART_MEANING_ALIGNMENT",
                                    "SOURCE_BOUND_USAGE_CLASSIFICATION"],
                         "classifier_implemented":False},
            "world_truth":"NOT_ESTABLISHED","learning_achieved":False}


def verify_inspection(report, *, text, source_id="madlul_input", scope="madlul_diagnostic"):
    # Re-run from fresh explicit inputs, not from the report's embedded source.
    fresh = inspect_text(text,source_id=source_id,scope=scope)
    return {"valid":wire(report)==wire(fresh),"authority":"EXACT_OWNER_VIEW_REPLAY_ONLY"}


PROBE_TEXTS = ("بِ", "باء", "«بِ»", "الكلمة", "الخبر", "عبد الله", "بعلبك",
               "أمس", "كَتَبَ", "كِتَابَةٌ", "كَاتِبٌ", "هو", "مِنْ",
               "ضَرَبَ زَيْدٌ عَمْرًا", "ضَرَبَ عَمْرٌو زَيْدًا", "لفظغيرمثبت")


def probe():
    rows = [inspect_text(t) for t in PROBE_TEXTS]
    return {"schema":"nabt.madlul-development-probes.v1","authority":AUTHORITY,
            "exposed_authored_inputs":True,"training_performed":False,
            "denominator":{"inputs":len(rows),"owners_per_input":3},
            "execution":{"attempted_owner_calls":len(rows)*3,
                         "returned_reports":sum(len(r["owner_reports"]) for r in rows),
                         "structured_failures":sum(len(r["owner_failures"]) for r in rows)},
            "rows":rows,"semantic_accuracy":"NOT_MEASURED",
            "note":"These diagnose installed readers; they are not a learned five-way classifier."}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation",choices=("matrix","inspect","probe"))
    p.add_argument("--text")
    p.add_argument("--output",type=Path)
    args=p.parse_args(argv)
    if (args.operation=="inspect") != (args.text is not None):
        p.error("--text is required only for inspect")
    try:
        result = matrix() if args.operation=="matrix" else probe() if args.operation=="probe" else inspect_text(args.text)
        out=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(out,encoding="utf-8")
        else:
            print(out,end="")
    except (ValueError,OSError) as exc:
        print(str(exc),file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
