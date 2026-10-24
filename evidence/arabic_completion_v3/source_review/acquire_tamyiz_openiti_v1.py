"""Preserve two bounded source leads as compressed, byte-exact public texts."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
from hashlib import sha1, sha256
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
SOURCES = [
    {"source_id": "samani_tafsir", "repository": "OpenITI/0500AH",
     "commit": "fff9e21790e2e54f14826322ae49ab7671f12744",
     "path": "data/0489IbnMuhammadSamcani/0489IbnMuhammadSamcani.TafsirQuran/0489IbnMuhammadSamcani.TafsirQuran.JK006476-ara1",
     "git_blob_sha1": "8b9ae2f55aa89426e89ea63c294734b3077e8f6f",
     "metadata_blob_sha1": "87e215e20fe0dfc6453a67c0aadaf048e22287d8"},
    {"source_id": "firuzabadi_basair", "repository": "OpenITI/0825AH",
     "commit": "bae1fba53712c020fe43e3e60b37dfe61f2b64a8",
     "path": "data/0817MajdDinFiruzabadi/0817MajdDinFiruzabadi.BasairDhawiTamyiz/0817MajdDinFiruzabadi.BasairDhawiTamyiz.Shamela0009856-ara1",
     "git_blob_sha1": "b15d5ba0a0d1ec84c0f64015a82d5a50342ca969",
     "metadata_blob_sha1": "1fd4a2b77b8020b8c6593fa2ea03afa290f3a2f5"},
]


def acquire(item):
    result = dict(item)
    for suffix, expected, local_suffix in [("", item["git_blob_sha1"], ".txt.gz"),
                                           (".yml", item["metadata_blob_sha1"], ".yml")]:
        url = f"https://raw.githubusercontent.com/{item['repository']}/{item['commit']}/{item['path']}{suffix}"
        with urlopen(Request(url, headers={"User-Agent": "NABT-source-evidence-audit/1.0"}), timeout=45) as response:
            raw = response.read()
        actual = sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        if actual != expected:
            raise ValueError("Unmatched source Git blob: " + item["source_id"] + suffix)
        raw.decode("utf-8")
        payload = gzip.compress(raw, mtime=0) if local_suffix.endswith(".gz") else raw
        name = item["source_id"] + "_openiti_v1" + local_suffix
        with (HERE / name).open("xb") as stream:
            stream.write(payload)
        result["source" if not suffix else "metadata"] = {
            "url": url, "path": item["path"] + suffix, "local_file": name,
            "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
            "git_blob_sha1": actual, "git_blob_matches_pinned_tree": True,
            "stored_bytes": len(payload), "stored_sha256": sha256(payload).hexdigest(),
            "storage": "gzip preserving exact decoded source bytes" if not suffix else "plain upstream bytes",
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        }
        if not suffix:
            assert gzip.decompress(payload) == raw
    return result


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(acquire, SOURCES))
    report = {"schema": "nabt.tamyiz-primary-source-acquisition.v1",
              "selection_phase": "POST_BASELINE_SOURCE_RESEARCH_NOT_BLIND_EVALUATION",
              "license_declaration": "OpenITI corpus CC-BY-NC-SA-4.0; upstream version YAML records CLEANED_VERSION/PRIMARY_VERSION; not a printed-edition rights audit.",
              "files": rows}
    output = HERE / "tamyiz_openiti_retrieval_v1.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
