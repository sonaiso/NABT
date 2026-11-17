"""Reproduce the fixed pilot readouts. Runtime proposal requires only the standard library."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from . import witness_origins as pilot


def fit():
    import numpy as np
    encoder, fingerprint = pilot.shared.load_model()
    rows = [r for r in pilot.origins() if r["split"] == "train"]
    clauses, windows = [], []
    for r in rows:
        for text, label in ((r["clause"], r["relation"]), (r["context"], "context")):
            features, spans = pilot.views(encoder, text)
            clauses.append((label, features))
            for lo, hi, vector in spans:
                cue = label != "context" and text.encode()[lo:hi].decode() == r["cue"]
                windows.append((cue, vector))

    def weights(examples, labels):
        counts = Counter(label for label, _ in examples)
        x = np.array([v + [1.] for _, v in examples])
        y = np.array([[float(l == k) for k in labels] for l, _ in examples])
        w = np.array([1. / counts[l] for l, _ in examples])
        return np.linalg.solve((x.T * w) @ x + .1 * np.eye(x.shape[1]), (x.T * w) @ y).T.round(10).tolist()

    if sum(label for label, _ in windows) != len(rows):
        raise ValueError("Training cues must be exact contiguous candidates")
    return {"version": 1, "encoder_sha256": fingerprint, "train_ids": [r["id"] for r in rows],
            "train_digest": sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            "relation": weights(clauses, pilot.LABELS), "cue": weights(windows, (False, True))}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    with p.parse_args().output.open("x", encoding="utf-8") as f:
        json.dump(fit(), f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
