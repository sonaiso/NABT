"""Compare six v1 JSONL outputs with the preimplementation bridge bytes.

The historical glue is loaded with its original repository-relative __file__.
Its unchanged installed owners therefore resolve the same source/configuration
paths as the current glue.  This finite compatibility observation does not
claim Arabic coverage or a refinement theorem.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from tools import recursive_bridge as current


BASE = "e9f83a3f6c678fb45ba618800cebf65310427e97"
PATH = "tools/recursive_bridge.py"
CASES = (
    {"id": "direct_template", "text": "كَتَبَ", "source_id": "input", "scope": "default"},
    {"id": "qaal", "text": "قَالَ", "source_id": "input", "scope": "default"},
    {"id": "baa", "text": "بَاعَ", "source_id": "input", "scope": "default"},
    {"id": "repeated_occurrence", "text": "قَالَ قَالَ", "source_id": "input", "scope": "default"},
    {"id": "custom_identity", "text": "  قَوَلَ، بَاعَ ", "source_id": "custom_source", "scope": "سياق تجريبي"},
    {"id": "unvocalized", "text": "قال وباع الكاتب", "source_id": "input", "scope": "default"},
)


def main():
    if not hasattr(current, "read_recursive_applications"):
        raise RuntimeError("Wait for the delegated v2 consumer before comparing current v1")
    logical_path = ROOT / PATH
    before = logical_path.read_bytes()
    historical_bytes = subprocess.check_output(["git", "show", BASE + ":" + PATH], cwd=ROOT)
    historical = ModuleType("nabt_derivation_surface_historical_recursive_v1")
    historical.__file__ = str(logical_path)
    historical.__package__ = "tools"
    exec(compile(historical_bytes, str(logical_path), "exec", dont_inherit=True), historical.__dict__)
    output = Path(__file__).with_name("recursive_v1_compatibility")
    output.mkdir(exist_ok=False)
    report = {
        "schema": "nabt.derivation-surface.recursive-v1-compatibility.v1",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python evidence/derivation_surface_v1/validation/compare_recursive_v1.py",
        "historical_commit": BASE,
        "module_path": PATH,
        "historical_module_sha256": sha256(historical_bytes).hexdigest(),
        "current_module_sha256": sha256(before).hexdigest(),
        "historical_module_file_identity": str(logical_path),
        "owner_resolution": "Both modules use the same unchanged installed runtime and repository source paths",
        "serialization": "Each version's original wire(report) plus one LF, as emitted by its v1 read CLI",
        "scope": "Six finite compatibility cases only; no completeness or new semantic/refinement proof",
        "cases": [],
    }
    for case in CASES:
        options = {"source_id": case["source_id"], "scope": case["scope"]}
        old_report = historical.read_recursive_source(case["text"], **options)
        new_report = current.read_recursive_source(case["text"], **options)
        old = historical.wire(old_report) + b"\n"
        new = current.wire(new_report) + b"\n"
        saved = {}
        for name, raw in (("historical", old), ("current", new)):
            path = output / (case["id"] + "." + name + ".json")
            with path.open("xb") as stream:
                stream.write(raw)
            saved[name] = {"path": str(path.relative_to(ROOT)), "bytes": len(raw),
                           "sha256": sha256(raw).hexdigest()}
        report["cases"].append({**case, "equal_bytes": old == new,
                                 "schema": new_report["schema"], "outputs": saved})
    after = logical_path.read_bytes()
    report["current_module_unchanged_during_comparison"] = before == after
    report["passed"] = before == after and all(row["equal_bytes"] for row in report["cases"])
    with (output / "summary.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": report["passed"], "cases": len(report["cases"]),
                      "bytes_per_version": sum(row["outputs"]["current"]["bytes"] for row in report["cases"]),
                      "current_module_unchanged": before == after}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
