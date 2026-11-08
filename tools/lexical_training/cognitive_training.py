"""Masked, contrastive shared-encoder training with reproducible PCGrad.

Extends the installed contextual owner. No new acceptance head or concept IDs.
Unreviewed occurrences have zero supervision, not an invented negative label.
All test partitions are evaluated only after fixed training and calibration.
"""
import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from . import contextual_alignment as runtime, contextual_data as data
from . import contextual_training as old, shared_encoder as shared
from . import shared_training as previous

DIRECTORY = shared.ROOT / "evidence/cognitive_graph_v1"
REVIEW = DIRECTORY / "review.json"
FRESH = DIRECTORY / "transfer.json"
PROTOCOL = {"id": "nabt.masked-shared-cognition-training.v1", "seed": 118,
            "epochs": 120, "warmup_epochs": 20, "encoder_lr": 0.0003,
            "head_lr": 0.01, "legacy_head_lr": 0.001,
            "contrast_weight": 0.05, "temperature": 0.2, "distillation_weight": 0.5,
            "gradient_mode": "pcgrad", "selection": "FIXED_FINAL_EPOCH",
            "test_selection": False, "unknown_supervision": "MASKED",
            "validation": "REVIEWED_ONLY_F1_WITH_REVIEWED_NEGATIVE_FPR_AT_MOST_0.10",
            "independent_semantic_adjudication": False}


def reviewed_tokens(rows, review):
    """Only exact, explicitly reviewed occurrences can become negative targets."""
    from tools.grammar_catalog.operations import exact_terms
    known = set(shared.load_model()[0]["labels"]["concept"])
    seen = set()
    for row in rows:
        runtime.validate_request({"text": row["text"]})
        if row["id"] in seen:
            raise ValueError("Duplicate review source")
        seen.add(row["id"])
        terms = {tuple(t["codepoint_span"]): t for t in exact_terms(row["text"])}
        spans = set()
        for annotation in row["annotations"]:
            _coordinates(annotation)
            span = tuple(annotation["codepoint_span"])
            labels = annotation["concept_ids"]
            if (span in spans or span not in terms or not labels or len(set(labels)) != len(labels)
                    or not set(labels) <= known or annotation["surface"] != terms[span]["surface"]
                    or annotation["utf8_span"] != terms[span]["utf8_span"]):
                raise ValueError("Invalid reviewed positive occurrence")
            spans.add(span)
    tokens = data.token_rows(rows)
    entries = {}
    for r in review["negative_occurrences"]:
        _coordinates(r)
        key = (r["id"], tuple(r["codepoint_span"]))
        if key in entries or r["status"] != "REVIEWED_NOT_IN_INSTALLED_INVENTORY":
            raise ValueError("Invalid or duplicate reviewed negative")
        entries[key] = r
    for row in tokens:
        key = (row["id"], tuple(row["codepoint_span"]))
        entry = entries.get(key)
        if runtime.NULL not in row["gold"]:
            if entry is not None:
                raise ValueError("Negative review contradicts positive annotation")
            row["review_status"] = "POSITIVE_OR_ACCEPTABLE_ALTERNATIVES"
        elif entry is not None:
            if (entry["text_sha256"] != sha256(row["text"].encode()).hexdigest()
                    or entry["surface"] != row["surface"] or entry["utf8_span"] != row["utf8_span"]):
                raise ValueError("Review does not bind the original occurrence")
            row["review_status"] = entry["status"]
        else:
            row["review_status"] = "UNREVIEWED"
    relevant = {r["id"] for r in rows}
    keys = {(r["id"], tuple(r["codepoint_span"])) for r in tokens}
    if any(k[0] in relevant and k not in keys for k in entries):
        raise ValueError("Review span is not a written occurrence")
    return tokens


def _coordinates(row):
    for name in ("codepoint_span", "utf8_span"):
        span = row[name]
        if (type(span) is not list or len(span) != 2 or any(type(x) is not int for x in span)
                or not 0 <= span[0] < span[1]):
            raise ValueError("Review coordinates must be two ordered exact integers")


def masked_loss(logits, rows, labels):
    """Set-valued supervision: credit total mass on acceptable alternatives."""
    import torch
    losses = {True: [], False: []}
    for i, row in enumerate(rows):
        if row["review_status"] == "UNREVIEWED":
            continue
        ids = [labels.index(x) for x in row["gold"]]
        loss = torch.logsumexp(logits[i], 0) - torch.logsumexp(logits[i, ids], 0)
        losses[runtime.NULL not in row["gold"]].append(loss)
    groups = [torch.stack(v).mean() for v in losses.values() if v]
    if not groups:
        return logits.sum() * 0
    return torch.stack(groups).mean()


def contrastive_loss(features, rows, temperature):
    """SupCon within reviewed exact label sets; no assumed concept equivalence."""
    import torch
    indices = [i for i, r in enumerate(rows) if runtime.NULL not in r["gold"]]
    if len(indices) < 2:
        return features.sum() * 0
    z = torch.nn.functional.normalize(features[indices], dim=1)
    sim = z @ z.T / temperature
    diagonal = torch.eye(len(indices), dtype=torch.bool)
    positive = torch.tensor([[i != j and set(rows[x]["gold"]) == set(rows[y]["gold"])
                              for j, y in enumerate(indices)] for i, x in enumerate(indices)])
    valid = positive.any(1)
    if not valid.any():
        return features.sum() * 0
    logp = sim - torch.logsumexp(sim.masked_fill(diagonal, -torch.inf), dim=1, keepdim=True)
    return -(logp.masked_fill(~positive, 0).sum(1)[valid] / positive.sum(1)[valid]).mean()


def project_gradients(gradients, generator):
    """PCGrad: project each task against original other task gradients."""
    import torch
    projected = []
    conflicts = comparisons = 0
    for i, g in enumerate(gradients):
        value = g.clone()
        for j in torch.randperm(len(gradients), generator=generator).tolist():
            if i == j:
                continue
            other = gradients[j]
            norm = other.square().sum()
            dot = value @ other
            comparisons += 1
            if dot < 0 and norm > 0:
                value = value - dot / norm * other
                conflicts += 1
        projected.append(value)
    return torch.stack(projected).mean(0), conflicts, comparisons


def measure(rows, scores, model):
    selected = [i for i, r in enumerate(rows) if r["review_status"] != "UNREVIEWED"]
    result, _ = old.summarize([rows[i] for i in selected], [scores[i] for i in selected], model)
    _, predictions = old.summarize(rows, scores, model)
    unknown = [i for i, r in enumerate(rows) if r["review_status"] == "UNREVIEWED"]
    for i in unknown:
        predictions[i]["correct"] = None
    result.update(reviewed_tokens=len(selected), unreviewed_tokens=len(unknown),
                  unreviewed_proposals=sum(predictions[i]["proposed_id"] is not None for i in unknown),
                  evaluation_scope="EXPLICIT_REVIEW_ONLY_UNKNOWN_NOT_NEGATIVE")
    return result, predictions


def calibrate(rows, scores, model):
    selected = [i for i, r in enumerate(rows) if r["review_status"] != "UNREVIEWED"]
    return old.calibrate([rows[i] for i in selected], [scores[i] for i in selected], model)


def legacy_metrics(model, rows, base):
    import torch
    with torch.no_grad():
        scores = model([r["text"] for r in rows])
    return {h: {"n": sum(h in r["labels"] for r in rows),
                "top1_correct": sum(base["labels"][h][int(scores[h][i].argmax())] in r["labels"][h]
                                    for i, r in enumerate(rows) if h in r["labels"])} for h in shared.HEADS}


def train_run(directory, *, gradient_mode="pcgrad", epochs=None):
    import torch
    protocol = {**PROTOCOL, "gradient_mode": gradient_mode}
    if epochs is not None:
        if type(epochs) is not int or epochs < 1:
            raise ValueError("Positive integer epoch budget required")
        protocol["epochs"] = epochs
        protocol["warmup_epochs"] = min(protocol["warmup_epochs"], max(0, epochs - 1))
    if gradient_mode not in ("pcgrad", "sum"):
        raise ValueError("Unknown gradient mode")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(protocol["seed"])
    generator = torch.Generator().manual_seed(protocol["seed"])
    partitions = data.dataset()
    # Parse and identify precisely the bytes used by this run. Never rebind an
    # already trained model to annotations that appeared later on disk.
    retained_inputs = {"review": (REVIEW, REVIEW.read_bytes()),
                       "fresh": (FRESH, FRESH.read_bytes())}
    input_hashes = {name + "_sha256": sha256(raw).hexdigest()
                    for name, (_, raw) in retained_inputs.items()}
    review = json.loads(retained_inputs["review"][1])
    fresh = json.loads(retained_inputs["fresh"][1])
    if set(r["text"] for r in fresh["rows"]) & set(r["text"] for v in partitions.values() for r in v):
        raise ValueError("Fresh transfer text overlaps retained corpus")
    for row in fresh["rows"]:
        runtime.validate_request({"text": row["text"]})
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=False)
    previous.save(directory / "protocol.json", {"protocol": protocol,
                  "partition_hashes": {k: data.digest(v) for k, v in partitions.items()},
                  **input_hashes})
    if review["source_corpus_sha256"] != sha256(data.CORPUS.read_bytes()).hexdigest():
        raise ValueError("Review corpus changed")
    train, validation = partitions["train"], partitions["validation"]
    train_tokens = reviewed_tokens(train, review)
    base, base_sha = shared.load_model()
    native = shared.concepts.catalogue()
    if base["concept_references"] != {r["identity"]["id"]: r["reference"] for r in native["concepts"]}:
        raise ValueError("Warm-start definitions changed")
    model = old.make_model(base)
    initial = deepcopy(model.state_dict())
    labels = base["labels"]["concept"] + [runtime.NULL]
    rehearsal, legacy_test, legacy_labels = previous.dataset()
    if legacy_labels != base["labels"]:
        raise ValueError("Legacy identities changed")
    with torch.no_grad():
        teacher = {h: v.detach() for h, v in model([r["text"] for r in rehearsal]).items()}
    before_legacy = legacy_metrics(model, legacy_test, base)
    encoder = [p for n, p in model.named_parameters() if n.startswith(("embedding.", "gru."))]
    optimizer = torch.optim.Adam([{"params": encoder, "lr": protocol["encoder_lr"]},
                                 {"params": model.heads.parameters(), "lr": protocol["legacy_head_lr"]},
                                 {"params": model.alignment.parameters(), "lr": protocol["head_lr"]}])
    history = []
    for epoch in range(protocol["epochs"]):
        optimizer.zero_grad()
        features = old.occurrence_features(model, train)
        alignment = masked_loss(model.alignment(features), train_tokens, labels)
        contrast = contrastive_loss(features, train_tokens, protocol["temperature"])
        tasks = [alignment + protocol["contrast_weight"] * contrast]
        prior = model([r["text"] for r in rehearsal])
        for h in shared.HEADS:
            indices = [i for i, r in enumerate(rehearsal) if h in r["labels"]]
            supervised = []
            for i in indices:
                gold = [legacy_labels[h].index(x) for x in rehearsal[i]["labels"][h]]
                supervised.append(torch.logsumexp(prior[h][i], 0) - torch.logsumexp(prior[h][i, gold], 0))
            kl = torch.nn.functional.kl_div(torch.log_softmax(prior[h], 1),
                                           torch.softmax(teacher[h], 1), reduction="batchmean")
            tasks.append(torch.stack(supervised).mean() + protocol["distillation_weight"] * kl)
        shared_grads = []
        for task in tasks:
            gradients = torch.autograd.grad(task, encoder, retain_graph=True)
            shared_grads.append(torch.cat([g.flatten() for g in gradients]))
        merged, conflicts, comparisons = project_gradients(shared_grads, generator)
        if gradient_mode == "sum":
            merged = torch.stack(shared_grads).mean(0)
        torch.stack(tasks).mean().backward()
        offset = 0
        for p in encoder:
            size = p.numel()
            p.grad = (merged[offset:offset+size].reshape_as(p).clone()
                      if epoch >= protocol["warmup_epochs"] else None)
            offset += size
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        history.append({"epoch": epoch + 1, "alignment": float(alignment.detach()),
                        "contrastive": float(contrast.detach()), "legacy": [float(t.detach()) for t in tasks[1:]],
                        "gradient_conflicts": conflicts, "gradient_comparisons": comparisons,
                        "encoder_updated": epoch >= protocol["warmup_epochs"]})
    model.eval()
    value = old.exported(model, base, train, validation)
    value["protocol"] = protocol; value["shared_model"]["protocol"] = protocol
    with torch.no_grad():
        scores = old.score_occurrences(model, validation).tolist()
    value["calibration"], validation_metrics = calibrate(reviewed_tokens(validation, review), scores, value)
    previous.save(directory / "model.json", value)
    portable, _ = runtime.load_model(directory / "model.json")
    # Test is neither an update source nor a model/threshold/epoch selector.
    evaluation = {}
    frozen_test = partitions["test"]
    for name, rows, rev in (("retained_test", frozen_test, review),
                            ("fresh_authored_transfer", fresh["rows"], fresh)):
        tokens = reviewed_tokens(rows, rev)
        with torch.no_grad():
            scores = old.score_occurrences(model, rows).tolist()
        metrics, predictions = measure(tokens, scores, value)
        all_portable = [x["logits"] for row in rows for x in runtime.occurrence_logits(portable, row["text"])[0]]
        parity = max(abs(a-b) for l, r in zip(scores, all_portable) for a, b in zip(l, r))
        _, portable_predictions = measure(tokens, all_portable, value)
        if parity >= 1e-4 or [x["proposed_id"] for x in predictions] != [x["proposed_id"] for x in portable_predictions]:
            raise ValueError("Portable inference differs")
        published, _ = runtime.load_model()
        old_scores = [x["logits"] for row in rows for x in runtime.occurrence_logits(published, row["text"])[0]]
        reference_scores = old.nearest_scores(data.token_rows(train), tokens, labels)
        reference_model = deepcopy(value); reference_model["calibration"].update(min_probability=0., min_margin=0.)
        evaluation[name] = {"neural": metrics, "published_model": measure(tokens, old_scores, published)[0],
                            "nearest_context": measure(tokens, reference_scores, reference_model)[0],
                            "portable_max_abs_error": parity, "rows_sha256": data.digest(rows)}
        previous.save(directory / (name + "_predictions.json"), predictions)
    after_legacy = legacy_metrics(model, legacy_test, base)
    delta = float(sum((v - initial[k]).square().sum() for k, v in model.state_dict().items()
                      if k.startswith(("embedding.", "gru."))).sqrt())
    report = {"schema": "nabt.cognitive-graph-training-evaluation.v1", "protocol": protocol,
              "evaluation": evaluation, "validation_metrics": validation_metrics,
              "legacy_exposed_before": before_legacy, "legacy_exposed_after": after_legacy,
              "critical_heads_nonregressing": all(after_legacy[h]["top1_correct"] >= before_legacy[h]["top1_correct"]
                                                  for h in ("reading", "morphology", "attachment")),
              "supervision_counts": dict(Counter(r["review_status"] for r in train_tokens)),
              "optimizer_steps": len(history), "shared_encoder_delta_l2": delta,
              "parameters": sum(p.numel() for p in model.parameters()), "history": history,
              "warm_start_sha256": base_sha, "torch_version": torch.__version__,
              "weights_sha256": sha256((directory / "model.json").read_bytes()).hexdigest(),
              **input_hashes,
              "partition_hashes": {k: data.digest(v) for k, v in partitions.items()},
              "world_truth_established": False, "all_fourteen_learned": False,
              "independent_semantic_adjudication": False, "predictions_grant_authority": False}
    for name, (path, raw) in retained_inputs.items():
        if path.read_bytes() != raw:
            raise ValueError("Training input changed: " + name)
    # FIRST_TEST is the completion receipt; partial weights are not a finished
    # evaluation when an input was replaced during training.
    for name, obj in [("train.json", train), ("validation.json", validation), ("test.json", frozen_test), ("FIRST_TEST.json", report)]:
        previous.save(directory / name, obj)
    return {k: v for k, v in report.items() if k != "history"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--gradient-mode", choices=("pcgrad", "sum"), default="pcgrad")
    parser.add_argument("--epochs", type=int)
    args = parser.parse_args()
    print(json.dumps(train_run(args.run_dir, gradient_mode=args.gradient_mode, epochs=args.epochs), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
