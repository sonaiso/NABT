"""Reproduce the post-baseline source-policy supplements from unchanged books."""
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "src/nabt/data/source_evidence"
HERE = Path(__file__).resolve().parent


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def passage(rule, source, low, high, scope, documents):
    doc = documents[source]
    raw = (DATA / (source + ".txt")).read_bytes()
    assert sha256(raw).hexdigest() == doc["sha256"]
    lines = raw.splitlines(keepends=True)
    start, end = sum(map(len, lines[:low - 1])), sum(map(len, lines[:high]))
    excerpt = raw[start:end]
    return {"rule": rule, "source_id": source, "source_commit": doc["commit"],
            "source_path": doc["path"], "source_sha256": doc["sha256"],
            "line_start": low, "line_end": high, "start": start, "end": end,
            "raw_text": excerpt.decode("utf-8"), "span_sha256": sha256(excerpt).hexdigest(),
            "premise_scope": scope}


def main():
    documents = {d["source_id"]: d for d in json.loads((DATA / "source_manifest.json").read_text())["documents"]}
    additions = {
        "construction": [
            ("matrix_ma_negation", "sibawayhi", 9782, 9787,
             "Primary verb-negation contrast. The added reader handles an independently parsed ma-negative perfect epistemic matrix only. Matrix negation does not negate, assert or erase the embedded proposition; other uses of ma and unlicensed frames remain separate."),
            ("explanatory_apposition", "qatr", 396, 401,
             "Bayan is an explanatory or specifying follower; a total-badal reading additionally requires licensed substitution. The source permits competing candidate labels but does not acquire identity, substitution, rigidity, speaker intention or a part-whole relation for a new target."),
            ("prepositional_attachment", "qatr", 337, 345,
             "The listed prepositions govern a genitive nominal, including an independently licensed idafa or adjectival expansion. Prefix and nominal source witnesses, complete predicate and attachment remain required. Unresolved meanings of bi/ka/li are retained as unspecified textual PP qualifications; they do not become location, ownership or causal facts."),
        ],
        "discourse": [
            ("temporal_noun_examples", "sibawayhi", 346, 351,
             "The explicit examples license possible temporal uses of ams and ghad with verbal events; the same passage expressly permits non-adverb uses. This does not turn every noun into an adverb, force a unique reading, or assert an event in the external world. Lexical identity, retained alternatives, syntactic attachment and scope still require checks."),
        ],
    }
    versions = {"construction": ("v2", "v3"), "discourse": ("v1", "v2")}
    receipt = {"schema": "nabt.arabic-coverage-source-supplement.v1",
               "base_commit": "f0064f0a4baab3cc816087a322aabc0c8fbb2d19",
               "selection_phase": "Post-baseline primary-source review; not blind validation or newly discovered grammar",
               "raw_source_files_changed": False, "policies": {}}
    saved = HERE / "source_policy_before_v1"
    saved.mkdir(exist_ok=True)
    for family, rows in additions.items():
        path = DATA / (family + "_policy.json")
        original = path.read_bytes()
        policy = json.loads(original)
        old, new = versions[family]
        assert policy["policy_id"] == f"nabt.{family}-grammar-sources.{old}"
        previous = saved / path.name
        assert not previous.exists(), "Prior policy must not be replaced"
        previous.write_bytes(original)
        existing = {p["rule"] for p in policy["passages"]}
        assert not existing.intersection(r[0] for r in rows)
        added = [passage(*r, documents) for r in rows]
        policy["passages"].extend(added)
        policy["policy_id"] = f"nabt.{family}-grammar-sources.{new}"
        write_json(path, policy)
        receipt["policies"][family] = {
            "previous_path": str(previous.relative_to(ROOT)),
            "previous_sha256": sha256(original).hexdigest(),
            "installed_path": str(path.relative_to(ROOT)), "policy_id": policy["policy_id"],
            "sha256": sha256(path.read_bytes()).hexdigest(),
            "rules_added": [{k: p[k] for k in ("rule", "source_id", "source_commit", "source_path", "source_sha256", "line_start", "line_end", "span_sha256", "premise_scope")} for p in added],
        }
    write_json(HERE / "source_supplement_v1.json", receipt)
    print(json.dumps({k: {"policy_id": v["policy_id"], "sha256": v["sha256"],
                         "rules_added": [p["rule"] for p in v["rules_added"]]}
                      for k, v in receipt["policies"].items()}))


if __name__ == "__main__":
    main()
