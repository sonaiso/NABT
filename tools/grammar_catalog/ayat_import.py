"""Rebuild the offline observation fixture from an explicit Hokom demo JSON export."""
import argparse
import json
from hashlib import sha256
from pathlib import Path

DATA = Path(__file__).with_name("data") / "ayat_al_dayn"
HOKOM = "086973036b3bc28f0acb90dd867baa20bbfae5cb"
VENDOR = "bc9d1ea5ef45970f5f3ec132441e30fd54b3da52"


def project(rows, text):
    words = text.split()
    if len(rows) != len(words) or len(words) != 129:
        raise ValueError("Incomplete verse export")
    out = []
    for i,(r,surface) in enumerate(zip(rows,words,strict=True),1):
        if r["original_surface"]!=surface or r["token_index"]!=i or r["error"]:
            raise ValueError(f"Source or execution mismatch at {i}")
        runtime = r["taaqol"]["runtime"]
        if runtime["vendor_sha"]!=VENDOR or not runtime["kernel_loaded"]:
            raise ValueError("Unavailable or different upstream runtime")
        out.append({"position":i, "surface":surface, "segment":r["segmentation"],
                    "class":r["word_class"]["class"],"class_verdict":r["word_class"]["verdict"],
                    "root_state":r["root_analysis"]["root_state"],"root":r["root_analysis"]["canonical_root"],
                    "weight_display":r["root_analysis"].get("wazn"),"family":r["root_analysis"].get("cra_form_family"),
                    "layers":{layer["layer"]:layer["layer_verdict"] for layer in r["composite_verdict"]["by_layer"]},"licensed":r["composite_verdict"]["licensed_claims"],
                    "deferred":r["composite_verdict"]["deferred_claims"],"unopened":r["composite_verdict"]["not_opened_layers"],
                    "routing_slots":{s["slot_id"]:[s["state"],s["value"]] for s in r["typed_slots"] if
                                     s["slot_id"] in {"SEGMENT_HOST","BOUNDARY_TYPE_SLOT","PATH_DIRECTIVE_SLOT","WORD_CLASS_SLOT","RADICAL_R1"}},
                    "h11_h15":r["h11_h15"]["reached"],"runtime_trace_events":runtime["trace_event_count"],
                    "gate_executed":runtime["gate_executed"],"gamma_executed":runtime["gamma_executed"]})
    return {"producer":"hhiyassat/taaqol-hokom-final-septemper/scripts/demo_ayat_al_dayn.py::run_all",
            "commit":HOKOM,"vendor":VENDOR,"source_sha256":sha256(text.encode()).hexdigest(),"rows":out}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rows",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    obj=project(json.loads(args.rows.read_bytes()),(DATA/"source.txt").read_text())
    with args.output.open("x",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,separators=(",",":"))
        f.write("\n")
