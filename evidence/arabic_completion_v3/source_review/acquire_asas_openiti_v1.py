"""Acquire the public cleaned Asas al-Balagha for a bounded lexical search."""
import json
from acquire_tamyiz_openiti_v1 import HERE, acquire

item = {
    "source_id": "zamakhshari_asas", "repository": "OpenITI/0550AH",
    "commit": "6c414b1e23f2646d30e4f7f08f4b07be9832367c",
    "path": "data/0538JarAllahZamakhshari/0538JarAllahZamakhshari.AsasBalagha/0538JarAllahZamakhshari.AsasBalagha.JK007032-ara1",
    "git_blob_sha1": "49b448ad37e077264a443032922c47495fe8b6a2",
    "metadata_blob_sha1": "6713e4219e9015246a30c9c0523581bb75c4e4e0",
}
if __name__ == "__main__":
    result = {"schema": "nabt.asas-primary-source-acquisition.v1",
              "selection_phase": "POST_BASELINE_SOURCE_RESEARCH_NOT_BLIND_EVALUATION",
              "license_declaration": "OpenITI corpus CC-BY-NC-SA-4.0; version YAML records CLEANED_VERSION/PRIMARY_VERSION; not a printed-edition rights audit.",
              "files": [acquire(item)]}
    with (HERE / "asas_openiti_retrieval_v1.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
