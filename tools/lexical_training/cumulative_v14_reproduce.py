"""Refit both frozen V14 protocols, replay assessments, and verify exact resume.

This developer command never selects a model from assessment performance. It
compares the predeclared full variant and its retrained channel control. The
production NTP owner still reads only its independently pinned installed model.
"""

import argparse
from pathlib import Path
import tempfile

import numpy as np

from . import cumulative_v14_model as model, cumulative_v14_train as train
from . import cumulative_v14_audit as audit


def compare_weights(expected, actual):
    if expected["gates"] != actual["gates"] or set(expected["residual_heads"]) != set(actual["residual_heads"]):
        raise ValueError("Refitting changed calibrated gates or task identities")
    pairs = [(expected[k], actual[k]) for k in ("adapter_columns", "adapter_bias")]
    pairs += [(expected["residual_heads"][t], actual["residual_heads"][t]) for t in expected["residual_heads"]]
    maximum = 0.0
    for a, b in pairs:
        left, right = np.asarray(a), np.asarray(b)
        if left.shape != right.shape or not np.isfinite(right).all():
            raise ValueError("Refitting changed parameter shapes or finite values")
        maximum = max(maximum, float(np.max(np.abs(left - right))))
    # Pinned float64 training should be very close across BLAS builds. Resume
    # in the same process environment below must be byte-for-byte identical.
    if maximum > 1e-8:
        raise ValueError(f"Refit differs from retained parameters: {maximum}")
    return {"maximum_absolute_parameter_difference": maximum, "gates_equal": True}


def reproduce(directory):
    directory = Path(directory)
    results = {}
    for variant, relative in (("full", ""), ("without_task_memory", "control")):
        output = directory / variant
        installed = model.DIRECTORY / relative
        train.experiment(output, variant=variant,
                         save_step=128 if variant == "full" else None,
                         checkpoint_dir=directory / "after128" if variant == "full" else None)
        results[variant] = compare_weights(model.read(installed / "weights.json.gz"), model.read(output / "weights.json.gz"))
        fresh = audit.build_report(output)
        saved = model.read(installed / "evaluation.json")
        if model.canonical(fresh["summary"]) != model.canonical(saved["summary"]):
            raise ValueError("Refitted historical assessment changed")
        if model.canonical(fresh["predictions"]) != model.canonical(model.read(installed / "predictions.json.gz")):
            raise ValueError("Refitted prediction, parent, or baseline row changed")
        audit.save_report(output, fresh)
        results[variant].update(heldout_rows=len(fresh["predictions"]),
                                measured_rows=fresh["summary"]["measured_rows"],
                                final_correct_rows=fresh["summary"]["final_correct_rows"])
    train.experiment(directory / "resumed", resume=directory / "after128")
    files = ("weights.json.gz", "manifest.json", "training.json", "protocol.json", "skill_layout.json")
    equality = {name: (directory / "full" / name).read_bytes() == (directory / "resumed" / name).read_bytes() for name in files}
    if not all(equality.values()):
        raise ValueError("Resumed training differs from uninterrupted training")
    result = {"schema": "nabt.cumulative-v14-reproduction.v1", "variants": results,
              "resume_128_to_256": equality, "assessment_used_for_selection": False,
              "authority": "NONE", "status": "PASS"}
    train.write_json(directory / "reproduction.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output:
        result = reproduce(args.output)
    else:
        with tempfile.TemporaryDirectory(prefix="nabt-v14-reproduction-") as directory:
            result = reproduce(directory)
    print(model.canonical(result))


if __name__ == "__main__":
    main()
