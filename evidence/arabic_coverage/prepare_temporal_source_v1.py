"""Pin the Hijazi built-on-kasra reading of ams from the unchanged Qatr."""
from hashlib import sha256
import json
from pathlib import Path

from prepare_source_supplement_v1 import passage, write_json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATA = ROOT / "src/nabt/data/source_evidence"
PREVIOUS = "6f29126ba013562653fcc4db28b9e25b543014c1e66a2cb3d7cdfa92216ce3bb"


def main():
    path = DATA / "discourse_policy.json"
    original = path.read_bytes()
    assert sha256(original).hexdigest() == PREVIOUS
    policy = json.loads(original)
    documents = {d["source_id"]: d for d in json.loads((DATA / "source_manifest.json").read_text())["documents"]}
    assert not any(p["rule"] == "temporal_ams_built" for p in policy["passages"])
    row = passage("temporal_ams_built", "qatr", 45, 56,
        "Qatr explicitly assigns ams the fixed-kasra Hijazi reading. A temporal accusative function can therefore coexist with a built kasra surface in that named dialectal reading. This does not license every kasra-marked noun as an accusative adverb, erase the inflected Tamimi alternatives discussed at lines424-434, or establish a date/event in the external world. Lexical temporal identity and complete syntactic attachment remain separate premises.", documents)
    policy["passages"].append(row)
    save = HERE / "source_policy_before_temporal_v1.json"
    assert not save.exists()
    save.write_bytes(original)
    write_json(path, policy)
    write_json(HERE / "temporal_source_supplement_v1.json", {
        "schema": "nabt.temporal-source-supplement.v1",
        "phase": "Post-baseline primary-source review; not blind validation",
        "previous_policy_path": str(save.relative_to(ROOT)),
        "previous_policy_sha256": PREVIOUS,
        "installed_policy_id": policy["policy_id"],
        "installed_policy_sha256": sha256(path.read_bytes()).hexdigest(),
        "raw_source_files_changed": False,
        "added_passage": row,
        "dialect_countercontext": passage("tamimi_ams_countercontext", "qatr", 424, 434,
            "The book separately describes Tamimi inflection and conditions. The installed exception must retain its Hijazi scope rather than asserting a universal ending for ams.", documents),
    })
    print(sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
