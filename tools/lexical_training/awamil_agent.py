"""Train the existing lexical Retriever for source-qualified governor cards.

Public, authored retrieval curriculum. Template-held-out retrieval is measured
separately from source-reader application. No case assignments are neural gold
features, no test result chooses weights, and no score becomes a certificate.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path

from tools.grammar_catalog.awamil import AwamilIndex, document, build_awamil_catalog
from tools.grammar_catalog.operations import digest
from tools.grammar_catalog.retrieval import SearchIndex
from tools.evidence_lifecycle_v1 import strict_loads

PROTOCOL = {"schema": "nabt.awamil-training.v1", "seed": 116, "buckets": 2048,
    "dim": 24, "epochs": 30, "batch_size": 128, "lr": .004, "temperature": .09,
    "threads": 2, "split_unit": "QUESTION_TEMPLATE", "selection": "DEV_MULTIPOSITIVE_NLL",
    "task": "SOURCE_CARD_RETRIEVAL", "acceptance_authority": "NONE"}
TEMPLATES = {
    "train": ("اشرح {label} في باب {family}", "ما عمل {label} ضمن {family}",
              "أتعلم {family} وأبحث عن {label}", "بطاقة {label} من {family}"),
    "dev": ("أحتاج شاهد {label} المتصل بموضوع {family}", "استرجع تعريف {family} المتعلق بلفظ {label}"),
    "test": ("كيف أراجع شروط استعمال {label} عند دراسة {family}؟", "بين مصدر {label} في مبحث {family} مع حدود تطبيقه"),
}


def dataset(catalog):
    """Labels are namespaced IDs, never supplied as part of the input query."""
    cards = catalog["cards"]
    rows = []
    for split, templates in TEMPLATES.items():
        for template_no, template in enumerate(templates):
            for card in cards:
                query = template.format(label=card["label"], family=card["description"])
                # Same-text cards in the two inventories are legitimate joint
                # positives, not in-batch false negatives.
                gold = [c["id"] for c in cards if document(c) == document(card)]
                rows.append({"id": f"{split}:{template_no}:{card['id']}", "split": split,
                    "query": query, "gold": gold, "factor_id": card["id"]})
    queries = {s: {r["query"] for r in rows if r["split"] == s} for s in TEMPLATES}
    if any(queries[a] & queries[b] for a in queries for b in queries if a != b):
        raise ValueError("Cross-split query overlap")
    return rows


def curriculum(*, dev_results=None):
    catalog = build_awamil_catalog()
    # Only development feedback affects the teaching schedule, never test gold.
    failures = set()
    if dev_results is not None:
        for row in dev_results:
            if not row["top1_correct"]:
                failures.add(row["factor_id"])
    alignment = {x["source_id"]: x for x in catalog["crosswalk"]}
    units = []
    for card in catalog["cards"][:100]:
        units.append({"unit_id": card["id"], "label_ar": card["label"],
            "group": card["group"], "family_ar": card["description"], "source": card["source"],
            "prerequisites": ["lang.word_kind", "lang.declension"],
            "objective_id": "lang.awamil", "retrieval_priority": 0 if card["id"] in failures else 1,
            "case_table_alignment": alignment[card["id"]],
            "lessons": ["استرجاع هوية العامل ومصدره", "تمييز الرسم المشترك والاستعمال",
                "تعيين المعمول والعمل والشروط والموانع", "تعيين المسند والمسند إليه ورأس الإسناد",
                "حفظ التضمين والتقييد والتعلق", "تطبيق ونقض وسحب شاهد ثم نقل إلى سياق جديد"],
            "application_gate": "INDEPENDENT_OCCURRENCE_AND_OWNER_RECEIPT_REQUIRED",
            "application_mastered": False})
    units.sort(key=lambda r: (r["retrieval_priority"], r["group"], r["unit_id"]))
    return {"schema": "nabt.awamil-agent.curriculum.v1", "agent_id": "awamil",
        "learning_framework_objective": "lang.awamil", "catalog_sha256": digest(catalog),
        "unit_count": len(units), "units": units,
        "relation_cards": [r["id"] for r in catalog["cards"] if r["collection"] == "relations"],
        "table_practice_ids": [r["id"] for r in catalog["cards"] if r["collection"] == "nabt"],
        "schedule_basis": "DEVELOPMENT_RETRIEVAL_ERRORS_ONLY", "mastery_certified": False}


def _metrics(rows, ordered):
    details = []
    for row, ids in zip(rows, ordered, strict=True):
        rank = min(ids.index(k) + 1 for k in row["gold"])
        details.append({"case_id": row["id"], "factor_id": row["factor_id"],
            "top1_correct": rank == 1, "recall5_hit": rank <= 5, "rank": rank,
            "top5": ids[:5], "gold": row["gold"]})
    n = len(details)
    return {"n": n, "top1": sum(r["top1_correct"] for r in details) / n,
        "hit5": sum(r["recall5_hit"] for r in details) / n,
        "mrr": sum(1 / r["rank"] for r in details) / n, "cases": details}


def train(output, *, protocol=None):
    import numpy as np
    import torch
    from torch.nn import functional as F
    from .model import Retriever, encode, embed

    output = Path(output)
    if output.exists():
        raise ValueError("Training output must be new; do not overwrite first-test evidence")
    p = deepcopy(PROTOCOL if protocol is None else protocol)
    if (type(p) is not dict or set(p) != set(PROTOCOL) or
            any(p[k] != PROTOCOL[k] for k in ("schema", "buckets", "dim", "split_unit", "selection", "task", "acceptance_authority")) or
            any(type(p[k]) is not int or not 1 <= p[k] <= 32768
            for k in ("buckets", "dim", "epochs", "batch_size", "threads", "seed")) or
            p["threads"] > 8 or p["epochs"] > 200 or p["dim"] > 128 or
            any(type(p[k]) not in (int, float) or not math.isfinite(p[k]) or not 0 < p[k] < 1
                for k in ("lr", "temperature"))):
        raise ValueError("Invalid bounded training protocol")
    index = AwamilIndex()
    catalog = index.catalog()
    rows = dataset(catalog)
    ids = [c["id"] for c in catalog["cards"]]
    by_id = {c["id"]: c for c in catalog["cards"]}
    pairs = [{**r, "document": document(by_id[r["factor_id"]])} for r in rows]
    torch.manual_seed(p["seed"])
    np.random.seed(p["seed"])
    torch.set_num_threads(p["threads"])
    torch.use_deterministic_algorithms(True)
    _, qi, qw, idf = encode(pairs, p)
    qi, qw = qi[:len(rows)], qw[:len(rows)]
    _, di, dw, _ = encode([{"query": document(c), "document": document(c), "split": "train"}
                          for c in catalog["cards"]], p, idf=idf)
    di, dw = di[:len(ids)], dw[:len(ids)]
    target = torch.tensor([[float(k in r["gold"]) for k in ids] for r in rows])
    train_idx = [i for i, r in enumerate(rows) if r["split"] == "train"]
    dev_idx = [i for i, r in enumerate(rows) if r["split"] == "dev"]
    test_idx = [i for i, r in enumerate(rows) if r["split"] == "test"]
    model = Retriever(p["buckets"], p["dim"])
    initial = {k: v.detach().clone() for k, v in model.state_dict().items()}
    optimizer = torch.optim.AdamW(model.parameters(), lr=p["lr"])

    def loss(scores, labels):
        # All equivalent cards share probability mass; no arbitrary serial ID
        # is taught as the sole correct answer to an indistinguishable query.
        return -(torch.logsumexp(scores.masked_fill(labels == 0, -torch.inf), 1)
                 - torch.logsumexp(scores, 1)).mean()

    history, best, best_loss, updates = [], None, float("inf"), 0
    for epoch in range(p["epochs"]):
        model.train()
        shuffled = torch.tensor(train_idx)[torch.randperm(len(train_idx))]
        total = 0.0
        for batch in shuffled.split(p["batch_size"]):
            optimizer.zero_grad()
            scores = model(qi[batch], qw[batch]) @ model(di, dw).T / p["temperature"]
            value = loss(scores, target[batch])
            value.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total += value.item() * len(batch)
            updates += 1
        model.eval()
        with torch.no_grad():
            validation = loss(model(qi[dev_idx], qw[dev_idx]) @ model(di, dw).T / p["temperature"],
                              target[dev_idx]).item()
        history.append({"epoch": epoch + 1, "train_loss": total / len(train_idx), "dev_loss": validation})
        if validation < best_loss:
            best_loss = validation
            best = {k: v.detach().clone() for k, v in model.state_dict().items()}
            best_epoch = epoch + 1
    model.load_state_dict(best)
    delta = sum(float(torch.sum((best[k] - initial[k]) ** 2)) for k in best) ** .5
    artifact = {"schema": "nabt.awamil-retriever-weights.v1", "protocol": p,
        "catalog_sha256": index.catalog_sha256, "dataset_sha256": digest(rows), "card_ids": ids,
        "idf": idf.tolist(), "state_dict": {k: v.tolist() for k, v in best.items()},
        "selected_epoch": best_epoch, "authority": "PROPOSAL_ONLY",
        "training_code": {path: sha256((Path(__file__).resolve().parents[2] / path).read_bytes()).hexdigest()
            for path in ("tools/lexical_training/awamil_agent.py", "tools/lexical_training/model.py",
                         "tools/lexical_training/features.py")}}
    output.mkdir(parents=True)
    # Plain bounded JSON tensors, no pickle execution and no remote model code.
    (output / "model.json").write_text(json.dumps(artifact, separators=(",", ":")) + "\n")
    model_hash = sha256((output / "model.json").read_bytes()).hexdigest()
    qv, dv = embed(model, qi, qw), embed(model, di, dw)

    def evaluate(indices):
        selected = [rows[i] for i in indices]
        ordered = [[ids[j] for j in np.argsort(-(qv[i] @ dv.T), kind="stable")] for i in indices]
        measured = _metrics(selected, ordered)
        baseline = []
        for row in selected:
            result = SearchIndex.search(index, row["query"], len(ids))
            matched = [r["id"] for r in result["candidates"]]
            baseline.append(matched + [k for k in ids if k not in matched])
        measured["bm25_baseline"] = _metrics(selected, baseline)
        return measured

    dev = evaluate(dev_idx)
    # FIRST access to test scores happens only after writing selected weights.
    test = evaluate(test_idx)
    per_card = [{"id": k, "train_examples": sum(k in r["gold"] for r in rows if r["split"] == "train"),
        "test_examples": sum(r["factor_id"] == k for r in test["cases"]),
        "test_top1_correct": sum(r["factor_id"] == k and r["top1_correct"] for r in test["cases"])} for k in ids]
    report = {"schema": "nabt.awamil-training-report.v1", "protocol": p,
        "model_sha256": model_hash, "dataset_sha256": digest(rows), "catalog_sha256": index.catalog_sha256,
        "torch_version": torch.__version__, "optimizer_updates": updates, "weight_delta_l2": delta,
        "history": history, "selected_epoch": best_epoch, "dev": dev, "test": test,
        "coverage": catalog["counts"], "per_card": per_card,
        "evaluation_scope": "PUBLIC_AUTHORED_TEMPLATE_HELD_OUT_RETRIEVAL",
        "ranking_admitted_by_dev": (dev["top1"] >= dev["bm25_baseline"]["top1"] and
                                    dev["hit5"] >= dev["bm25_baseline"]["hit5"]),
        "unseen_roots_or_free_sentences_measured": False, "linguistic_application_mastered": False}
    for name, value in (("report.json", report), ("curriculum.json", curriculum(dev_results=dev["cases"]))):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return {k: report[k] for k in ("model_sha256", "coverage", "optimizer_updates", "weight_delta_l2", "selected_epoch")}


class Learner:
    """Load bounded numeric weights, bind the catalogue, and propose only IDs."""
    def __init__(self, path):
        import numpy as np
        import torch
        from .model import Retriever, encode, embed
        with Path(path).open("rb") as stream:
            raw = stream.read(8 * 1048576 + 1)
        data = strict_loads(raw, maximum_bytes=8 * 1048576, report=True)
        required = {"schema", "protocol", "catalog_sha256", "dataset_sha256", "card_ids", "idf",
                    "state_dict", "selected_epoch", "authority"}
        if (type(data) is not dict or not required <= data.keys() or
                set(data) - required - {"training_code"} or
                data.get("schema") != "nabt.awamil-retriever-weights.v1" or data.get("authority") != "PROPOSAL_ONLY"):
            raise ValueError("Unknown weight format")
        p = data["protocol"]
        if (type(p) is not dict or set(p) != set(PROTOCOL) or
                type(p["buckets"]) is not int or type(p["dim"]) is not int or
                p["buckets"] != PROTOCOL["buckets"] or p["dim"] != PROTOCOL["dim"]):
            raise ValueError("Unsupported model dimensions")
        self.catalog = build_awamil_catalog()
        self.catalog_sha256 = digest(self.catalog)
        self.ids = [c["id"] for c in self.catalog["cards"]]
        if data["catalog_sha256"] != self.catalog_sha256 or data["card_ids"] != self.ids:
            raise ValueError("MODEL_CATALOG_MISMATCH")
        torch.set_num_threads(2)
        self.model = Retriever(p["buckets"], p["dim"])
        if type(data["state_dict"]) is not dict or set(data["state_dict"]) != set(self.model.state_dict()):
            raise ValueError("Invalid weight names")
        try:
            state = {k: torch.tensor(v, dtype=torch.float32) for k, v in data["state_dict"].items()}
        except (TypeError, ValueError, RuntimeError) as exc:
            raise ValueError("Invalid weight tensors") from exc
        if any(not torch.isfinite(t).all() for t in state.values()):
            raise ValueError("Nonfinite weights")
        try:
            self.model.load_state_dict(state, strict=True)
        except RuntimeError as exc:
            raise ValueError("Invalid weight shapes") from exc
        self.idf = np.array(data["idf"], dtype=np.float32)
        if self.idf.shape != (p["buckets"],) or not np.isfinite(self.idf).all() or (self.idf <= 0).any():
            raise ValueError("Invalid IDF")
        self.protocol = p
        self.model_sha256 = sha256(raw).hexdigest()
        _, di, dw, _ = encode([{"query": document(c), "document": document(c), "split": "train"}
                              for c in self.catalog["cards"]], p, idf=self.idf)
        self.vectors = embed(self.model, di[:len(self.ids)], dw[:len(self.ids)])
        rows = dataset(self.catalog)
        if data["dataset_sha256"] != digest(rows):
            raise ValueError("MODEL_DATASET_MISMATCH")
        # Recompute admission from development queries. A supplied artifact
        # cannot grant itself a passing grade. Test data is never consulted.
        dev = [r for r in rows if r["split"] == "dev"]
        _, qi, qw, _ = encode([{"query": r["query"], "document": "", "split": "dev"}
                               for r in dev], p, idf=self.idf)
        vectors = embed(self.model, qi[:len(dev)], qw[:len(dev)])
        ranked = [[self.ids[j] for j in np.argsort(-(v @ self.vectors.T), kind="stable")] for v in vectors]
        index = AwamilIndex()
        base = []
        for row in dev:
            matched = [c["id"] for c in SearchIndex.search(index, row["query"], len(self.ids))["candidates"]]
            base.append(matched + [k for k in self.ids if k not in matched])
        neural, lexical = _metrics(dev, ranked), _metrics(dev, base)
        self.ranking_admitted = neural["top1"] >= lexical["top1"] and neural["hit5"] >= lexical["hit5"]
        self.dev_metrics = {"neural_top1": neural["top1"], "bm25_top1": lexical["top1"]}

    def scores(self, query):
        from .model import encode, embed
        if type(query) is not str or not query.strip() or len(query.encode()) > 16384:
            raise ValueError("Invalid query")
        _, qi, qw, _ = encode([{"query": query, "document": "", "split": "query"}], self.protocol, idf=self.idf)
        scores = embed(self.model, qi[:1], qw[:1])[0] @ self.vectors.T
        return {k: float(v) for k, v in zip(self.ids, scores, strict=True)}
