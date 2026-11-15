"""First-test evaluation of the frozen proposal model. No fitting or holdout-based selection."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import platform

from tools.grammar_catalog.operations import exact_terms
from . import passive_transfer as runtime
from . import passive_transfer_training as training

HOLDOUT = runtime.DIRECTORY / "holdout.json"
HOLDOUT_SHA256 = "6aa167d831b38042b79e1f2367f0cd9647ebcae3647249129d7f2fd91e8cc7b5"
FIELDS = ("relation", "verb_span", "patient_span", "cue_span")


def surface_baseline(text, *, require_shape):
    """Fixed-position cue baseline, optionally requiring the observed vowel pair.

    Deliberately has no dictionary, judgment authority or access to gold spans.
    """
    terms = exact_terms(text)
    empty = dict.fromkeys(FIELDS)
    empty["relation"] = runtime.OUTSIDE
    cue = None
    if len(terms) == 2:
        kind, verb, patient, vowels = runtime.ASSERT, 0, 1, "ُِ"
    elif len(terms) == 3 and runtime.observed(terms[0]["surface"])[0] == "لم":
        kind, verb, patient, vowels, cue = runtime.DENY, 1, 2, "َُ", terms[0]["utf8_span"]
    else:
        return empty
    written = "".join(c for c in terms[verb]["surface"] if c in "َُِ")
    if require_shape and not written.startswith(vowels):
        return empty
    return {"relation":kind,"verb_span":terms[verb]["utf8_span"],
            "patient_span":terms[patient]["utf8_span"],"cue_span":cue}


def check_cases(document):
    if set(document["held_out_roots"]).intersection(row[0] for row in training.TRAIN + training.DEV):
        raise ValueError("Train/dev roots overlap reserved roots")
    if len({r["id"] for r in document["cases"]}) != len(document["cases"]):
        raise ValueError("Duplicate case identity")
    dev_texts = {r["text"] for r in training.examples(training.TRAIN + training.DEV)}
    for row in document["cases"]:
        spans = [t["utf8_span"] for t in exact_terms(row["text"])]
        gold = training.target(row)
        if row["group"] == "heldout" and (row["root"] not in document["held_out_roots"] or
                                          row["text"] in dev_texts):
            raise ValueError("Incorrect held-out partition")
        if row["relation"] == runtime.OUTSIDE:
            if any(gold[k] is not None for k in FIELDS[1:]):
                raise ValueError("Outside annotation includes a binding")
        else:
            present = [gold[k] for k in FIELDS[1:] if gold[k] is not None]
            if (not all(s in spans for s in present) or len({tuple(s) for s in present}) != len(present)
                    or gold["verb_span"] is None or gold["patient_span"] is None
                    or (gold["cue_span"] is None) != (row["relation"] == runtime.ASSERT)):
                raise ValueError("Gold binding is not a unique exact source token")


def evaluate():
    raw = HOLDOUT.read_bytes()
    if sha256(raw).hexdigest() != HOLDOUT_SHA256:
        raise ValueError("Frozen benchmark changed")
    document = json.loads(raw)
    check_cases(document)
    model = runtime.load_model()
    systems = ("trained", "context_only_occlusion", "shape_only_occlusion", "cue_position", "cue_plus_vowels")
    metrics = {}
    pairs = {}
    first_test = []
    for row in document["cases"]:
        rows = runtime.candidates(row["text"])
        if rows is None or len(row["text"].encode()) > runtime.MAX_BYTES:
            raise ValueError("Authored case exceeds scorer domain")
        prediction = runtime.propose(row["text"])
        if prediction["status"] not in ("PROPOSED", "OUTSIDE"):
            raise ValueError("Evaluation requires available frozen model")
        values = (prediction, runtime.rank(rows,model,"context")[0], runtime.rank(rows,model,"shape")[0],
                  surface_baseline(row["text"],require_shape=False), surface_baseline(row["text"],require_shape=True))
        gold = training.target(row)
        trial = {"id":row["id"], "group":row["group"],"root":row["root"],"gold":gold,"predictions":{}}
        for name, result in zip(systems, values, strict=True):
            bound = training.target(result)
            correct = bound == gold
            trial["predictions"][name] = bound
            group = metrics.setdefault(name, {}).setdefault(row["group"], {
                "total":0,"exact":0,"relation_correct":0,"outside_gold":0,"outside_false_positive":0})
            group["total"] += 1
            group["exact"] += int(correct)
            group["relation_correct"] += int(bound["relation"] == gold["relation"])
            group["outside_gold"] += int(row["relation"] == runtime.OUTSIDE)
            group["outside_false_positive"] += int(row["relation"] == runtime.OUTSIDE and
                                                   bound["relation"] != runtime.OUTSIDE)
            if row.get("pair_id"):
                by_pair = pairs.setdefault(name, {}).setdefault((row["group"], row["pair_id"]), {})
                if row["relation"] in by_pair:
                    raise ValueError("Duplicate paired polarity")
                by_pair[row["relation"]] = correct
        first_test.append(trial)
    paired = {}
    for name, group_pairs in pairs.items():
        for (group, _), sides in group_pairs.items():
            if set(sides) != {runtime.ASSERT, runtime.DENY}:
                raise ValueError("Unpaired polarity intervention")
            counter = paired.setdefault(name,{}).setdefault(group,{"exact_both":0,"pairs":0})
            counter["pairs"] += 1
            counter["exact_both"] += int(all(sides.values()))
    return {"schema":"nabt.passive-relation-first-test.v1", "holdout_sha256":HOLDOUT_SHA256,
            "model_sha256":runtime.MODEL_SHA256, "training_sha256":model["training_sha256"],
            "reference_python":platform.python_version(), "counts":metrics, "pair_counts":paired,
            "scope":"AUTHORED_SHORT_WRITTEN_CLAUSES_NOT_EXTERNAL_CORPUS_OR_HUMAN_ADJUDICATION",
            "occlusion":"TEST_TIME_CHANNEL_MASKS_NO_RETRAINING",
            "deployment":"PROPOSAL_ONLY_CONTROL_FAILURES_RETAINED",
            "gold_used_as_model_input":False,"world_truth_established":False,"cases":first_test}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    path = parser.parse_args().output
    report = evaluate()
    if path:
        with path.open("xb") as handle:
            handle.write(training.encoded(report))
    print(json.dumps({"counts":report["counts"],"pairs":report["pair_counts"]},ensure_ascii=False,indent=2))
