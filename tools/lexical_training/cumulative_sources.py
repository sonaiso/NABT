"""Prepare source-linked training and assessment episodes from pinned PR trees."""
from collections import defaultdict
import csv
from functools import lru_cache
import gzip
import io
import json
from pathlib import Path

from . import corpus_verbs, cumulative_assertions
from .cumulative_history import DATA, canonical, digest, git, snapshot
from .train_corpus_verbs import root_script, split as root_split

TRACKING = {"source_id", "revision", "scope", "id"}
TEXT_FIELDS = {"text", "surface", "lexical_text", "query", "question", "source_text", "word",
               "ending", "mode", "model_profile", "onset"}
AUDIT_FIELDS = {"id", "source_id", "revision", "scope", "sha256", "case_id", "surface", "text"}


def holdout(text):
    return "test" if int(digest(text.encode()), 16) % 5 == 0 else "train"


def leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            if key not in AUDIT_FIELDS:
                yield from leaves(child, (*path, key))
    elif type(value) in (int, str, bool) and len(str(value)) <= 64:
        yield path, canonical(value)


@lru_cache(maxsize=256)
def published_cases(blob, path):
    if blob == "0"*40 or int(git("cat-file", "-s", blob)) > 3_000_000:
        return {}
    data = json.loads(git("cat-file", "blob", blob))
    cases = data.get("cases") if isinstance(data, dict) else data
    out = {}
    for i, row in enumerate(cases if type(cases) is list else ()):
        if type(row) is not dict or not ("expected" in row or "expect" in row):
            continue
        inputs = row.get("input", row.get("request", {"text": row.get("text")}))
        if type(inputs) is not dict or set(inputs) - TEXT_FIELDS - TRACKING:
            continue
        args = {k: v for k, v in inputs.items() if k in TEXT_FIELDS}
        if not args or any(type(v) is not str for v in args.values()):
            continue
        text = args["text"] if set(args) == {"text"} else canonical(args)
        if not text.strip() or len(text.encode()) > 1024:
            continue
        for fields, label in leaves(row.get("expected", row.get("expect"))):
            task = "case:" + path + ":" + "/".join(fields)
            out[task, text, label] = i
    return out


def build(history):
    pulls = json.loads((DATA / "pulls.json").read_bytes())
    rows = list(cumulative_assertions.episodes(history))
    def add(pr, task, text, label, split, src, lane):
        if type(text) is str and text.strip() and type(label) is str and label and split in ("train", "test"):
            rows.append(dict(pr=pr, task=task, text=text, gold=label, split=split, source=src, lane=lane))
    for r in history["rows"]:
        add(r["pr"], r["task"], r["text"], r["gold"], holdout(r["text"]), r["blob"]+":"+r["source"], "published_test")
    for p in pulls:
        for path, old, new, _ in history["changes"][str(p["number"])]:
            if not (path.startswith("evidence/") and "case" in Path(path).name and path.endswith(".json")):
                continue
            after = published_cases(new, path)
            for key in sorted(after.keys() - published_cases(old, path).keys()):
                task, text, target = key
                add(p["number"], task, text, target, holdout(text), f"{new}:{path}#/cases/{after[key]}", "published_case")

    def source(pr, path):
        blob = git("rev-parse", pulls[pr-1]["head"]+":"+path).decode().strip()
        data = git("cat-file", "blob", blob).decode()
        values = list(csv.DictReader(io.StringIO(data), delimiter="\t")) if path.endswith(".tsv") else json.loads(data)
        return values, blob+":"+path

    def paired(pr, task, folder, paths, fields):
        for part, name in zip(("train", "test"), paths, strict=True):
            data, ref = source(pr, "evidence/"+folder+"/"+name)
            for i, row in enumerate(data):
                add(pr, task, row[fields[0]], row[fields[1]], part, ref+"#"+str(i), "source_split")

    for p in pulls:
        changed = {c[0] for c in history["changes"][str(p["number"])]}
        if "evidence/licensed_speech_v1/train.tsv" in changed and "evidence/licensed_speech_v1/challenge.tsv" in changed:
            paired(p["number"], "speech_force", "licensed_speech_v1", ("train.tsv","challenge.tsv"), ("text","force"))
    paired(86, "contextual_sense", "contextual_alignment_v1", ("train.json","test.json"), ("text","category"))
    paired(102, "dictionary_use", "lexical_indication_learning_v1", ("usage_train.tsv","usage_test.tsv"), ("text","sense"))
    paired(109, "question_family", "ayat_cognition_v1", ("train.tsv","probes.tsv"), ("question","family"))
    for part, name, field in (("train","training_rows","sense_ids"), ("test","predictions","expected_ids")):
        data, ref = source(68, "evidence/neural_senses_v1/run_01/"+name+".json")
        for i, row in enumerate(data):
            if len(row[field]) == 1:
                add(68,"lexical_identity",row["text"],row[field][0],part,ref+"#"+str(i),"source_split")
    for part in ("train","test"):
        for n, folder, labels in ((85,"shared_cognition_v1",("concept","witness")),
                                  (93,"shared_cell_reading_v1",("reading","morphology","attachment"))):
            data, ref = source(n, "evidence/"+folder+"/"+part+".json")
            for i, row in enumerate(data):
                for key in labels:
                    y = row["labels"].get(key)
                    if isinstance(y, list):
                        y = y[0] if len(y) == 1 else None
                    add(n,key,row["text"],y,part,ref+"#"+str(i),"source_split")
    data, ref = source(114,"tools/lexical_training/data/ntl_witness_origins.tsv")
    for i, r in enumerate(data):
        add(114, "witness_relation", r["clause"], r["relation"], r["split"], ref+"#"+str(i),"source_split")
    for n, path in ((115,"evidence/ifadah_programs_v1/data.json"),(120,"evidence/ntp_ifadah_v1/supervision.json")):
        data, ref = source(n, path)
        for i, row in enumerate(data["rows"]):
            if row["split"] not in ("train","lexical_test","structure_test"):
                continue
            split = "train" if row["split"]=="train" else "test"
            if n==120 and row["status"] != "ELIGIBLE":
                continue
            add(n, "ifadah_program" if n==115 else "eligible_program_from_text", row["text"],
                row.get("program",row.get("target_program")), split,ref+"#"+str(i),"source_split")
    data, ref = source(128,"evidence/verb_morphology_v1/lane/lane-masdar-v2.tsv")
    for i, row in enumerate(data):
        surface = row["key"]
        letters = corpus_verbs.carriers(surface)
        root = row["radicals"].translate(corpus_verbs.ROOT_GRAPH)
        ops = root_script(letters,root)
        if ops and corpus_verbs.apply_script(ops,letters) == root:
            add(128, "root_recipe", surface, canonical(ops), root_split(root),ref+"#"+str(i),"root_split")
    for split, name in (("train","train"),("test","holdout")):
        data, ref = source(139, "evidence/inspection_discourse_v1/"+name+".tsv")
        for i, row in enumerate(data):
            for role in ("report","content","condition","request","tail"):
                add(139,"clause_role", row[role], row["tail_role"] if role=="tail" else role, split, ref+"#"+str(i),"source_split")
    data, ref = source(101, "evidence/awamil_occurrence_v1/manual.tsv")
    for i,r in enumerate(data):
        add(101,"governed_case",r["text"],r["case"],holdout(r["id"]),ref+"#"+str(i),"published_case")
    path = "integrations/role_readings/event.jsonl"
    blob = git("rev-parse", pulls[133]["head"]+":"+path).decode().strip()
    for i,line in enumerate(git("cat-file","blob",blob).decode().splitlines()):
        case = json.loads(line)
        named = case["request"]["payload"]["named_matrix"]
        for q,y in zip(named["queries"],case["statuses"],strict=True):
            add(134,"event_role_evidence",named["ledger"]+"\n"+canonical(q),y,holdout(case["id"]),
                f"{blob}:{path}#{i}","published_case")
    # Reproduce the four finite mode combinations from the mixed-mode owner's regression.
    path = "tests/test_sim_aql_engine.py"
    blob = git("rev-parse",pulls[141]["head"]+":"+path).decode().strip()
    import ast
    method = next(n for n in ast.walk(ast.parse(git("cat-file","blob",blob)))
                  if isinstance(n,ast.FunctionDef) and n.name=="test_reviewed_inputs_respect_the_inference_mode_at_each_step")
    table = ast.literal_eval(next(n.iter for n in method.body if isinstance(n,ast.For)))
    for first,last,status,_ in table:
        text = canonical({"first_mode":first,"final_mode":last})
        add(142,"mixed_inference_admission",text,status,
            "test" if first=="CONDITIONAL" and last=="FACTUAL" else "train",blob+":"+path+"::"+method.name,
            "published_case")
    rows.extend(json.loads((DATA/"deposit.json").read_bytes()))
    return rows


def prepare(rows):
    # An occurrence reused by another PR cannot cross the global fitting boundary.
    heldout = {r["text"] for r in rows if r["split"] == "test"}
    golds = defaultdict(set)
    seen = set()
    result, counts = [], defaultdict(int)
    for r in rows:
        golds[r["task"],r["text"]].add(r["gold"])
    for r in rows:
        key = (r["task"],r["text"],r["pr"],r["split"])
        if len(golds[r["task"],r["text"]]) != 1:
            counts["conflicting"] += 1
        elif r["split"] == "train" and r["text"] in heldout:
            counts["overlapping_train"] += 1
        elif key in seen:
            counts["duplicate"] += 1
        else:
            seen.add(key)
            result.append(r)
    return sorted(result,key=lambda r:(r["pr"],r["task"],r["text"],r["source"])),dict(counts)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = build(snapshot())
    out, removed = prepare(rows)
    args.output.write_bytes(gzip.compress(canonical({"rows":out,"excluded":removed}).encode(),mtime=0))
    print(len(rows),len(out),removed)
