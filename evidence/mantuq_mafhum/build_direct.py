"""Reproduce local fallback using the documented public Lean embedding driver.

Normal CI uses Lake. This script does not emulate Lake or report a Lake pass.
See ../verified_reading/environment/main.c for the driver and its fixed root.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

p = argparse.ArgumentParser()
p.add_argument("--driver", type=Path, required=True)
p.add_argument("--toolchain", type=Path, required=True)
p.add_argument("--output", type=Path, required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[2]
build = a.output.resolve()
build.mkdir(parents=True, exist_ok=True)
env = {**os.environ, "LEAN_PATH": str(build)}
done, records = set(), []
cmodules = {"Nabt.ClassicalLanguageEvidence", "Nabt.SemanticInference", "Nabt.VerifiedReading",
            "Nabt.SibawayhiRules", "Nabt.QatrRules", "Nabt.AwamilRules", "Nabt.MaqayisRules",
            "Nabt.SourceSemantics", "Nabt.RationalInquiry", "Nabt.ArabicCoverage",
            "Nabt.ThinkingRules", "Nabt.Shakhsiyya1Rules", "Nabt.Shakhsiyya3Rules",
            "Nabt.MantuqMafhum", "Nabt.AwamilInventory", "ProbeJson", "ClassicalSemanticMain", "VerifiedReadingMain"}


def build_module(name):
    if name in done:
        return
    source = root / "formal" / (name.replace(".", "/") + ".lean")
    if not source.exists():
        return
    for line in source.read_text().splitlines():
        if line.startswith("import "):
            for dependency in line[7:].split():
                build_module(dependency)
    base = build / name.replace(".", "/")
    base.parent.mkdir(parents=True, exist_ok=True)
    command = [str(a.driver), "-o", str(base.with_suffix(".olean"))]
    if name in cmodules:
        command += ["-c", str(base.with_suffix(".c"))]
    command += [str(source)]
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    run = subprocess.run(command, cwd=root / "formal", env=env, capture_output=True, text=True)
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_sha256:
        raise RuntimeError("Source changed during compilation: " + name)
    records.append({"module": name, "source_sha256": source_sha256,
                    "exit_code": run.returncode, "stdout": run.stdout, "stderr": run.stderr})
    (build / "kernel.json").write_text(json.dumps(records, indent=2) + "\n")
    print(name, run.returncode, flush=True)
    if run.returncode:
        print(run.stdout, run.stderr)
    run.check_returncode()
    done.add(name)


for module in ["Nabt", "Audit", "ClassicalSemanticMain", "VerifiedReadingMain"]:
    build_module(module)
common = [build / "Nabt/SemanticInference.c", build / "Nabt/VerifiedReading.c", build / "ProbeJson.c"]
extra = [build / "Nabt" / (name + ".c") for name in
         ["ClassicalLanguageEvidence", "SibawayhiRules", "QatrRules", "AwamilRules", "MaqayisRules", "SourceSemantics",
          "RationalInquiry", "ArabicCoverage", "ThinkingRules", "Shakhsiyya1Rules", "Shakhsiyya3Rules", "MantuqMafhum", "AwamilInventory"]]
for executable, main, more in [("classicalSemanticProbe", "ClassicalSemanticMain", extra),
                               ("verifiedReading", "VerifiedReadingMain", [])]:
    command = ["gcc", "-O2", "-I" + str(a.toolchain / "include"),
               *map(str, common + more + [build / (main + ".c")]),
               "-L" + str(a.toolchain / "lib/lean"),
               "-Wl,-rpath," + str(a.toolchain / "lib/lean"), "-lleanshared", "-o", str(build / executable)]
    subprocess.run(command, check=True)
    print(executable, "compiled", flush=True)
run = subprocess.run([str(a.driver), "--run", "ExportTable.lean"], cwd=root / "formal",
                     env=env, capture_output=True, text=True)
run.check_returncode()
(build / "law-export.json").write_text(run.stdout)
print("fresh law exported", flush=True)
