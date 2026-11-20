"""Learn to rank candidate named proof dependencies. Lean supplies the edge label."""
import argparse
from collections import Counter, defaultdict
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import re

from . import mashru_lesson as owner
from tools import mashru_transfer as transfer

MODEL = Path(__file__).with_name("data") / "mashru_dependencies_v1.json"


@lru_cache(maxsize=1)
def core_index(data, expected):
    if sha256(data).hexdigest() != expected:
        raise ValueError("unbound core proof reference")
    return {row["name"]: row for row in json.loads(data)["theorems"]}


def index(catalog, library):
    path = transfer.reference().with_name("proof_catalog.json")
    return {**core_index(path.read_bytes(), catalog["core_catalog_sha256"]), **library}


def hash_int(name):
    return int.from_bytes(sha256(name.encode()).digest()[:8], "big")


def features(source, target):
    a, b = source["name"].split("."), target["name"].split(".")
    a_words = set(re.findall(r"[^_]+", a[-1].lower()))
    b_words = set(re.findall(r"[^_]+", b[-1].lower()))
    overlap = a_words & b_words
    return [1, int(source["module"] == target["module"]), int(a[0] == b[0]),
            int(a[:-1] == b[:-1]), min(len(overlap), 3), int(a[-1].startswith(b[-1])),
            int(b[-1].startswith(a[-1])), int(source["scope"] == target.get("scope"))]


def score(model, source, target):
    return sum(a*b for a,b in zip(model["weights"], features(source, target), strict=True))


def fit():
    import numpy as np
    catalog, library = owner.checked_catalog(transfer.reference().read_bytes())
    rows = index(catalog, library)
    modules = defaultdict(list)
    for name, row in sorted(rows.items()):
        modules[row["module"]].append(name)
    all_names = sorted(rows)
    x, y, held = [], [], []
    counts = Counter()
    for name, source in sorted(library.items()):
        if source["scope"] not in {"imported", "research-countermodel"}:
            continue
        counts["source_theorems"] += 1
        positives = sorted(set(source["proof_dependencies"]) & rows.keys() - {name})
        if not positives:
            counts["without_direct_named_edge"] += 1
            continue
        forbidden = set(positives) | {name}
        local = [n for n in modules[source["module"]] if n not in forbidden]
        for target in positives:
            seed = hash_int(name + "/" + target)
            # Counterexamples include names from the same module and other modules.
            candidates = local if local and seed % 2 else all_names
            i = seed % len(candidates)
            while candidates[i] in forbidden:
                i = (i + 1) % len(candidates)
            bad = candidates[i]
            pair = features(source, rows[target]), features(source, rows[bad])
            if hash_int(name) % 5 == 0:
                held.append(pair)
            else:
                x.extend(pair)
                y.extend([1, -1])
    xx = np.array(x, dtype=float)
    weights = np.linalg.solve(xx.T @ xx + np.eye(xx.shape[1]), xx.T @ np.asarray(y))
    weights = np.rint(weights * 1_000_000).astype(int).tolist()
    def evaluate(w):
        margins = [sum(c*(i-j) for c,i,j in zip(w,a,b,strict=True)) for a,b in held]
        return {"wins": sum(m > 0 for m in margins), "ties": margins.count(0),
                "losses": sum(m < 0 for m in margins)}
    return {"schema": "nabt.mashru-dependency-ranker.v1", "reference_sha256": owner.REFERENCE_SHA,
            "counts": dict(counts), "training_pairs": len(y)//2, "heldout_pairs": len(held),
            "weights": weights, "heldout": evaluate(weights),
            "same_module_baseline": evaluate([0,1,0,0,0,0,0,0])}


def compare(catalog, library, name, candidate):
    rows = index(catalog, library)
    if name not in library or candidate not in rows:
        return {"status": "UNKNOWN_THEOREM", "execution_measured": False}
    source = library[name]
    result = {"status": "CHECKED_DIRECT_DEPENDENCY", "execution_measured": True,
              "named_in_proof_term": candidate in source["proof_dependencies"],
              "named_in_type": candidate in source["type_dependencies"],
              "scope": "DIRECT_COMPILED_REFERENCE_ONLY", "proposal_authority": "NONE"}
    try:
        data = MODEL.read_bytes()
        model = json.loads(data)
        if model["reference_sha256"] != owner.REFERENCE_SHA:
            raise ValueError("unbound dependency model")
        result.update(proposal_status="PROPOSED", neural_rank_score=score(model, source, rows[candidate]),
                      model_sha256=sha256(data).hexdigest())
    except (OSError, ValueError, KeyError) as exc:
        result.update(proposal_status="MODEL_UNAVAILABLE", proposal_reason=type(exc).__name__)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = fit()
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    if args.check:
        if MODEL.read_text() != encoded:
            raise SystemExit("dependency weights or heldout measures changed")
    else:
        MODEL.write_text(encoded)
    print(encoded)
