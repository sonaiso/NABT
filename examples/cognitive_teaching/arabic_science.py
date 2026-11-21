"""Build and replay paired Arabic and physics lessons through the installed NTP gateway.

Usage: python examples/cognitive_teaching/arabic_science.py OUT [arabic|physics]
The three reviewed training labels are separate from the held-out comparison.
The reader alignment, paradigm annotations and measurement fields are supplied.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[2]
CASES = ("A", "B", "C", "D", "E", "F", "G")
TRAIN_LABELS = {"A": True, "B": False, "C": False}
# Gold is kept outside the request, even after observing B and C.
HELD_OUT = {"D": True, "E": False, "F": False, "G": False}
EVENTS = [
    ("observe", "#$B"), ("observe", "#$C"),
    ("withdraw", "B-label"), ("restore", "B-label"),
    ("withdraw", "D-first"), ("restore", "D-first"),
]
# Each tuple contains the visible passage and the teacher's aligned finite
# verb paradigm in the indicative. An unmarked verb is not parsed by guessing.
ARABIC = [
    ("لَنْ تَكْتُبُوا", "لَنْ", "تكتبون"),
    ("لَنْ يَكْتُبَ", "لَنْ", "يكتب"),
    ("لَمْ تَكْتُبُوا", "لَمْ", "تكتبون"),
    ("لَنْ تُخْفِقُوا", "لَنْ", "تخفقون"),
    ("لَمْ يَجْلِسْ", "لَمْ", "يجلس"),
    ("لَنْ يَجْلِسَ", "لَنْ", "يجلس"),
    ("لَمْ تُخْفِقُوا", "لَمْ", "تخفقون"),
]
# Magnitudes of momentum change in N s and positive durations in s,
# before and after the change of conditions. These are authored measurements.
PHYSICS = [
    (12, 2, 12, 4), (12, 4, 12, 2), (12, 2, 30, 4),
    (20, 2, 20, 5), (10, 4, 12, 3), (18, 3, 18, 3), (20, 2, 21, 5),
]


def domain_rows(domain):
    if domain == "arabic":
        features = ("#$Lan", "#$FiveVerbParadigm")
        # This inventory is limited to the sound forms supplied above.
        paradigms = {"تكتبون": True, "تخفقون": True, "يكتب": False, "يجلس": False}
        rows = []
        for text, governor, indicative in ARABIC:
            if text.split()[0] != governor:
                raise ValueError("Governor alignment does not match the source")
            rows.append((text, (governor == "لَنْ", paradigms[indicative])))
        return features, "#$SubjunctiveNunDeletion", rows
    if domain == "physics":
        features = ("#$SameNonzeroImpulseMagnitude", "#$LongerTime")
        rows = []
        for old_dp, old_dt, new_dp, new_dt in PHYSICS:
            if min(old_dp, new_dp) < 0 or min(old_dt, new_dt) <= 0:
                raise ValueError("Expected magnitudes and positive durations")
            text = f"تغيّر الزخم {old_dp} ثم {new_dp} نيوتن ثانية، والزمن {old_dt} ثم {new_dt} ثانية."
            rows.append((text, (old_dp == new_dp and old_dp > 0, new_dt > old_dt)))
        # Licensing this particular explanation differs from the numerical
        # question whether the magnitude of average net force happened to fall.
        return features, "#$FixedImpulseTimeExplanation", rows
    raise ValueError("Unknown domain")


def request(domain, event_count, probe_domain=None):
    if not 0 <= event_count <= len(EVENTS):
        raise ValueError("Unknown evidence stage")
    features, target, rows = domain_rows(domain)
    if probe_domain is not None:
        if probe_domain == domain:
            raise ValueError("Transfer requires two different domains")
        # This experimental alignment is supplied, not learned from Arabic.
        # Slot 1: governing particle / equal nonzero impulse magnitudes.
        # Slot 2: indicative paradigm / increased duration.
        _, _, probes = domain_rows(probe_domain)
        rows = rows[:3] + probes[3:]
        features = ("#$FirstPremise", "#$SecondPremise")
        target = "#$ExplanationApplies"
    records = []
    def fact(case_id, field, predicate, value):
        formula = f"(isa #${case_id} {predicate})"
        records.append(dict(id=f"{case_id}-{field}", mt="#$LessonMt", strength="monotonic",
                            formula=formula if value else f"(not {formula})"))
    for case_id, (_, values) in zip(CASES, rows, strict=True):
        for field, pred, value in zip(("first", "second"), features, values, strict=True):
            fact(case_id, field, pred, value)
        if case_id in TRAIN_LABELS:
            fact(case_id, "label", target, TRAIN_LABELS[case_id])
    ledger = "".join(json.dumps(r, sort_keys=True) + "\n" for r in records)
    name = domain if probe_domain is None else f"{domain}-to-{probe_domain}"
    label = "paired_school_" + name
    source = dict(id=label, revision="1", uri="urn:nabt:paired-school:" + name,
                  license="Authored educational encoding", sha256=sha256(ledger.encode()).hexdigest())
    lesson = dict(schema="nabt.opencyc-inquiry.v1", source_id=label,
                  text="\n".join(f"{k} {row[0]}" for k, row in zip(CASES, rows, strict=True)),
                  target_class=target, feature_classes=list(features), degree=2,
                  training_subjects=["#$A"], probe_subjects=["#$"+c for c in CASES[1:]],
                  events=[dict(id=f"e{i}", operation=op, target=t)
                          for i, (op,t) in enumerate(EVENTS[:event_count], 1)])
    lesson["slice"] = dict(schema="nabt.opencyc-slice.v1", source=source, ledger=ledger,
                           context="#$LessonMt", withdrawn=[], bindings=[], application=None,
                           query=dict(predicate="isa", arguments=["#$A",target], positive=True))
    return dict(schema="nabt.io.request.v1", route="ntp",
                payload=dict(operation="cognitive.lesson", input=dict(lesson=lesson)))


def run_stage(output, domain, stage, probe_domain=None):
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(map(str, (ROOT/"src", ROOT))))
    command = [sys.executable, "-m", "tools.grammar_catalog", "gateway"]
    # Concurrent and repeated runs keep their own independently retained request.
    folder = output / (domain if probe_domain is None else f"{domain}-to-{probe_domain}")
    folder.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=folder) as tmp:
        work = Path(tmp)
        original, receipt, verification = [work/(k+".json") for k in ("request", "receipt", "verify")]
        original.write_text(json.dumps(request(domain, stage, probe_domain), ensure_ascii=False), encoding="utf8")
        for args in (["run","--request",original,"--output",receipt],
                     ["verify","--request",original,"--receipt",receipt,"--output",verification]):
            subprocess.run(command + args, cwd=ROOT, env=env, check=True)
        if not json.loads(verification.read_text())["valid"]:
            raise RuntimeError("Public replay failed")
        envelope = json.loads(receipt.read_text())
        owner = envelope["execution"]["owner_result"]["owner_result"]
        learning = owner.get("learning")
        if not owner.get("execution_measured") or not learning:
            raise RuntimeError("Learning owner unavailable: " + owner["status"])
        if learning["withheld_probe_labels_used"] or learning["new_rule_adopted"]:
            raise RuntimeError("Unexpected probe or promotion authority")
        probes = {p["subject"][2:]:p for p in learning["probe_predictions"]}
        checked = {k:probes[k]["possible"] == [v] for k,v in HELD_OUT.items()}
        result = dict(stage=stage, request_sha256=envelope["request_sha256"],
                      curves=learning["candidate_counts"], rules=learning["survivor_expressions"],
                      next_step=learning["next_step"], predictions={k:probes[k] for k in HELD_OUT},
                      correct=checked)
        # The verified envelope and independently retained request are exported together.
        for file in (original, receipt, verification):
            file.replace(folder/f"{stage}.{file.name}")
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("domain", nargs="?", choices=("arabic", "physics"))
    parser.add_argument("--transfer-only", action="store_true",
                        help="Run the frozen, explicitly aligned, opposite-domain probes")
    args = parser.parse_args()
    for domain in ([args.domain] if args.domain else ["arabic","physics"]):
        if args.transfer_only:
            target = "physics" if domain == "arabic" else "arabic"
            result = run_stage(args.output.resolve(), domain, 2, target)
            (args.output/f"{domain}-to-{target}"/"summary.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2))
            print(domain, "to", target, result["correct"], flush=True)
            continue
        with ThreadPoolExecutor(max_workers=2) as pool:
            stages = list(pool.map(lambda i: run_stage(args.output.resolve(), domain, i), range(len(EVENTS)+1)))
        (args.output/domain/"summary.json").write_text(json.dumps(stages, ensure_ascii=False, indent=2))
        print(domain, [len(s["rules"]) for s in stages], flush=True)


if __name__ == "__main__":
    main()
