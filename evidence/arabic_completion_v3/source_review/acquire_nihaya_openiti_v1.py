"""Acquire the upstream primary cleaned Nihaya version for lexical witnesses."""
import json
from acquire_tamyiz_openiti_v1 import HERE, acquire

item = {
    "source_id": "ibnathir_nihaya", "repository": "OpenITI/0625AH",
    "commit": "f1e38210b32fd0d043949ff6471e869d658c3b16",
    "path": "data/0606IbnAthirMajdDin/0606IbnAthirMajdDin.NihayaFiGharib/0606IbnAthirMajdDin.NihayaFiGharib.Shamela0023691-ara1",
    "git_blob_sha1": "6b967028a27f58d3d8a18f138974f1ba22f93f6b",
    "metadata_blob_sha1": "3f08554bc95a9f3e9583e3071a6bfa93b5a4a36c",
}
if __name__ == "__main__":
    result = {"schema": "nabt.nihaya-primary-source-acquisition.v1",
              "selection_phase": "POST_BASELINE_SOURCE_RESEARCH_NOT_BLIND_EVALUATION",
              "license_declaration": "OpenITI corpus CC-BY-NC-SA-4.0; version YAML records PRIMARY_VERSION/CLEANED_VERSION and editorial removal by PV; not a printed-edition rights audit.",
              "selection_note": "The JK version YAML explicitly points to the Shamela version as primary because JK lacks the author's introduction.",
              "files": [acquire(item)]}
    with (HERE / "nihaya_openiti_retrieval_v1.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
