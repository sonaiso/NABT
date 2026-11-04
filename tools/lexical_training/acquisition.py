"""Learn source/sense and component proposals without supplied root or targets.

Uses the installed lexical MLP, catalogue, testimony checker, intended-use
reader and sign/denotatum owners. Training never predicts proof acceptance.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import zipfile

import numpy as np

from tools import lexical_testimony as testimony
from tools.lexical_training.senses import catalogue, encode, forward, train

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "evidence/lexical_acquisition_v1/protocol.json"
DIAGNOSTIC = ROOT / "evidence/neural_senses_v1/acceptance.json"
SCHEMA = "nabt.lexical-acquisition-model.v1"
AUTHORITY = "LEARNED_PROPOSALS_WITH_UNCHANGED_OWNER_REPORTS"


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(raw):
    return sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                               allow_nan=False) + "\n", encoding="utf-8")


def dataset():
    """Acquire supervision from the pinned source interpretations, not queries.

    Equal quotations keep every linked sense. Each quotation is one input;
    authored component lists are targets, never additional training inputs.
    Lisan quotations retain their current QUOTATION_ONLY provenance status.
    """
    cat = catalogue()
    ids = [s["id"] for s in cat["senses"]]
    components = sorted({c for s in cat["senses"] for c in s["components"]})
    rows = {}
    for s in cat["senses"]:
        source = testimony._citation(s["citation"], ROOT)
        text = s["citation"]["quotation"]
        row = rows.setdefault(text, {"text": text, "sense_ids": [], "components": [],
                                     "sources": []})
        row["sense_ids"].append(s["id"])
        row["components"] = sorted(set(row["components"]) | set(s["components"]))
        row["sources"].append(source)
    rows = list(rows.values())
    targets = {}
    for head, labels, field in (("sense", ids, "sense_ids"),
                                ("component", components, "components")):
        y = np.zeros((len(rows), len(labels)), dtype=np.float64)
        for i, row in enumerate(rows):
            for label in row[field]:
                y[i, labels.index(label)] = 1 / len(row[field])
        targets[head] = y
    return cat, {"sense": ids, "component": components}, rows, targets


def _rank(scores, labels):
    return sorted(range(len(labels)), key=lambda j: (-float(scores[j]), labels[j]))


def train_run(directory):
    directory = Path(directory)
    protocol_raw = PROTOCOL.read_bytes()
    protocol = testimony._strict_json(protocol_raw)
    cat, labels, rows, targets = dataset()
    # Diagnostic labels are read only after fitting both heads.
    directory.mkdir(parents=True, exist_ok=False)
    x = encode([r["text"] for r in rows])
    tensors, histories, delta = {}, {}, {}
    for head in labels:
        fitted, histories[head] = train(x, targets[head], protocol)
        initial, _ = train(x, targets[head], {**protocol, "epochs": 0})
        delta[head] = float(np.sqrt(sum(np.square(fitted[k] - initial[k]).sum()
                                        for k in fitted)))
        tensors.update({head + "_" + k: v for k, v in fitted.items()})
    np.savez(directory / "weights.npz", **tensors)
    meta = {"schema": SCHEMA, "catalogue_sha256": testimony.CATALOG_SHA,
            "labels": labels, "features": "lexical-crc32-word-char34-v1",
            "protocol_sha256": digest(protocol_raw),
            "training_sha256": digest(wire(rows)),
            "weights_sha256": digest((directory / "weights.npz").read_bytes()),
            "authority": "NONE"}
    save(directory / "model.json", meta)
    save(directory / "training_rows.json", rows)
    save(directory / "protocol.json", protocol)
    models, _, _ = load_model(directory)
    cases_raw = DIAGNOSTIC.read_bytes()
    cases = testimony._strict_json(cases_raw)["queries"]
    if set(r["text"] for r in rows) & set(c["text"] for c in cases):
        raise ValueError("diagnostic quotation overlap")
    z = encode([c["text"] for c in cases])
    scores = {h: forward(w, z) for h, w in models.items()}
    similarity = z @ x.T
    baseline = {h: np.column_stack([similarity[:, targets[h][:, j] > 0].max(axis=1)
                                   for j in range(len(labels[h]))]) for h in labels}
    by_id = {s["id"]: s for s in cat["senses"]}
    predictions = []
    for i, case in enumerate(cases):
        gold = {"sense": case["expected_ids"],
                "component": sorted({c for sid in case["expected_ids"]
                                      for c in by_id[sid]["components"]})}
        row = {"text": case["text"], "gold": gold, "supplied_root": False,
               "supplied_target_components": False}
        for method, values in (("neural", scores), ("lexical_baseline", baseline)):
            row[method] = {}
            for head, names in labels.items():
                ranked = [names[j] for j in _rank(values[head][i], names)]
                first = next(k + 1 for k, name in enumerate(ranked) if name in gold[head])
                row[method][head] = {"ranked_ids": ranked, "first_gold_rank": first,
                                      "top1_correct": first == 1}
        predictions.append(row)
    metrics = {method: {head: {"n": len(predictions),
                 "top1_correct": sum(r[method][head]["top1_correct"] for r in predictions),
                 "mrr": sum(1 / r[method][head]["first_gold_rank"] for r in predictions) / len(predictions)}
               for head in labels} for method in ("neural", "lexical_baseline")}
    report = {"schema": "nabt.lexical-acquisition-evaluation.v1", "authority": "NONE",
              "training_rows": len(rows), "label_counts": {h: len(v) for h,v in labels.items()},
              "parameters": sum(a.size for a in tensors.values()), "history": histories,
              "parameter_delta_l2": delta, "metrics": metrics,
              "diagnostic_sha256": digest(cases_raw),
              "diagnostic_status": "EXPOSED_AUTHORED_SEEN_SENSES_GLOBAL_RANKING",
              "component_metric": "Any gold definition component at rank one, not complete-set extraction",
              "root_supplied_to_predictor": False, "target_supplied_to_predictor": False,
              "native_checked": False, "numpy": np.__version__,
              "independent_semantic_adjudication": False,
              "generalization_to_unseen_senses": "NOT_MEASURED"}
    save(directory / "predictions.json", predictions)
    save(directory / "FIRST_TEST.json", report)
    return report


def load_model(directory):
    directory = Path(directory)
    if (directory / "model.json").stat().st_size > 65536:
        raise ValueError("model metadata limit")
    meta = testimony._strict_json((directory / "model.json").read_bytes())
    cat, labels, rows, _ = dataset()
    if (directory / "weights.npz").stat().st_size > 2_000_000:
        raise ValueError("weights byte limit")
    raw = (directory / "weights.npz").read_bytes()
    if (len(raw) > 2_000_000 or meta.get("schema") != SCHEMA or
        meta.get("catalogue_sha256") != testimony.CATALOG_SHA or
        meta.get("labels") != labels or meta.get("training_sha256") != digest(wire(rows)) or
        meta.get("protocol_sha256") != digest(PROTOCOL.read_bytes()) or
        meta.get("features") != "lexical-crc32-word-char34-v1" or
        meta.get("authority") != "NONE" or meta.get("weights_sha256") != digest(raw)):
        raise ValueError("model identity differs")
    shapes = {h + "_" + k: shape for h, names in labels.items()
              for k, shape in {"w1": (512,32), "b1": (32,), "w2": (32,len(names)),
                               "b2": (len(names),)}.items()}
    with zipfile.ZipFile(directory / "weights.npz") as archive:
        if sum(f.file_size for f in archive.infolist()) > 2_000_000:
            raise ValueError("expanded weights limit")
    with np.load(directory / "weights.npz", allow_pickle=False) as archive:
        if len(archive.files) != len(shapes) or set(archive.files) != set(shapes):
            raise ValueError("unexpected tensors")
        tensors = {k: archive[k] for k in shapes}
    for k, value in tensors.items():
        if (value.shape != shapes[k] or value.dtype.kind != "f" or
            not np.isfinite(value).all() or np.max(np.abs(value)) > 100):
            raise ValueError("invalid tensor")
    return {h: {k: tensors[h + "_" + k] for k in ("w1","b1","w2","b2")}
            for h in labels}, meta, cat


def propose(text, directory):
    x = encode([text])
    models, meta, cat = load_model(directory)
    ranking = {}
    for head, labels in meta["labels"].items():
        scores = forward(models[head], x)[0]
        ranking[head] = [{"id": labels[j], "score": float(scores[j])}
                         for j in _rank(scores, labels)]
    by_id = {s["id"]: s for s in cat["senses"]}
    for row in ranking["sense"]:
        sense = by_id[row["id"]]
        row.update(root_proposal=sense["root"], source=testimony._citation(sense["citation"], ROOT),
                   definition_components=sense["components"],
                   component_origin="INSTALLED_INTERPRETATION_NOT_NEURAL_SEGMENTATION")
    return {"schema": "nabt.lexical-acquisition-proposal.v1", "authority": "NONE",
            "input": text, "input_sha256": digest(text.encode()),
            "model_sha256": meta["weights_sha256"], "ranking": ranking,
            "all_installed_candidates_retained": True,
            "intended_sense_established": False, "calibrated_probabilities": False,
            "unknown_sense_detection": "NOT_IMPLEMENTED"}


def connect(text, directory, *, profile_id=None, source_id="lexical_learning", scope="learning"):
    """Replay actual owners; neural scores cannot furnish their premises.

    A bounded candidate beam proposes roots and targets from learned ranks.
    The owner checks those candidates without scores and retains every sense
    of each queried root. Unchecked alternatives stay visible in full ranks.
    No beam member becomes an accepted premise or an intended-sense witness.
    """
    from tools.arabic_training.madlul_matrix import inspect_text
    from tools.linguistic_truth import acquire
    from nabt.discourse_reader import read_discourse
    from nabt.errors import NabtError
    proposal = propose(text, directory)
    before = inspect_text(text, source_id=source_id, scope=scope)
    usage = acquire(text, profile_id=profile_id, source_id=source_id, context=scope)
    try:
        after = {"report": read_discourse(text, source_id=source_id, scope=scope), "failure": None}
    except NabtError as error:
        after = {"report": None, "failure": error.as_dict()}
    # A search policy, not an acceptance threshold. Keep the full ranking in
    # the result so a bounded search cannot masquerade as Arabic completeness.
    roots = list(dict.fromkeys(r["root_proposal"] for r in proposal["ranking"]["sense"][:3]))
    parts = [r["id"] for r in proposal["ranking"]["component"][:3]]
    targets = [[part] for part in parts] + [parts[:2]]
    queries = {(root, tuple(target)): (root, target, "LEARNED_COMPONENT_PROPOSAL")
               for root in roots for target in targets}
    # Retrieve an existing necessity only for a proposed sense identity. The
    # network cannot create or relabel a mental rule, naming cause or outside fact.
    cat = catalogue()
    for sense in proposal["ranking"]["sense"][:3]:
        for rule in cat["necessities"]:
            if rule["sense_id"] == sense["id"]:
                target = [rule["target"]]
                root = sense["root_proposal"]
                queries[(root, tuple(target))] = (root, target, "RETRIEVED_NECESSITY_PREMISE")
    receipts = [testimony.assess(root, target) for root, target, _ in queries.values()]
    return {"schema": "nabt.lexical-acquisition-connection.v1", "authority": AUTHORITY,
            "proposal": proposal, "before_composition": before, "after_composition": after,
            "usage_owner": usage, "conditional_lexical_receipts": receipts,
            "all_native_lexical_checks_completed": all(r["native_checked"] for r in receipts),
            "query_plan_origin": "LEARNED_CANDIDATE_ROOTS_AND_COMPONENTS_NOT_ACCEPTED_PREMISES",
            "proposed_queries": [{"entry": root, "target": target, "origin": origin}
                                 for root,target,origin in queries.values()],
            "query_budget": {"sense_ranks": 3, "component_ranks": 3,
                             "maximum_requests": 12 + len(cat["necessities"])},
            "all_installed_pairs_checked": False,
            "indication_application": {"status": "DEFER",
                "missing": ["EXACT_USAGE_SENSE_TO_DICTIONARY_SENSE_ALIGNMENT"],
                "mental_necessity_is_sufficient": False,
                "source_relative_usage_acquired": usage.get("intended_sense_acquired", False)},
            "world_truth_established": False}


def verify_connection(report, *, text, directory, profile_id=None,
                      source_id="lexical_learning", scope="learning"):
    fresh = connect(text, directory, profile_id=profile_id, source_id=source_id, scope=scope)
    return {"valid": wire(report) == wire(fresh), "authority": "FRESH_OWNER_REPLAY_ONLY"}


def replay_training(directory, reference):
    actual, meta, _ = load_model(directory)
    expected, retained, _ = load_model(reference)
    if Path(directory).resolve() == Path(reference).resolve():
        raise ValueError("fresh training directory required")
    for head in actual:
        for key in actual[head]:
            if not np.allclose(actual[head][key], expected[head][key], rtol=1e-7, atol=1e-9):
                raise ValueError("fresh training tensor differs")
    for name in ("training_rows.json", "predictions.json"):
        if (Path(directory)/name).read_bytes() != (Path(reference)/name).read_bytes():
            raise ValueError("fresh training evidence differs")
    return {"training_replayed": True, "authority": "NONE"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("train", "propose", "connect"))
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--text")
    parser.add_argument("--profile")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--compare-to", type=Path)
    args = parser.parse_args(argv)
    if (args.operation == "train") == (args.text is not None):
        parser.error("--text is required only for propose/connect")
    if args.profile is not None and args.operation != "connect":
        parser.error("--profile is a connect context only")
    if args.compare_to is not None and args.operation != "train":
        parser.error("--compare-to requires fresh training")
    try:
        if args.operation == "train":
            result = train_run(args.model)
            if args.compare_to:
                result["replay"] = replay_training(args.model, args.compare_to)
        elif args.operation == "propose":
            result = propose(args.text, args.model)
        else:
            result = connect(args.text, args.model, profile_id=args.profile)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            save(args.output, result)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.operation == "connect" and (not result["all_native_lexical_checks_completed"] or
                result["usage_owner"]["status"] in {"SOURCE_UNAVAILABLE", "VERIFICATION_UNAVAILABLE",
                                                    "RESOURCE_EXHAUSTED", "INVALID_INPUT"}):
            return 2
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
