"""Optional local comparison with supplied originals (not distributed in git).

For the legacy Thinking DOC, supply its LibreOffice-converted DOCX separately.
This validates bytes and extraction, not authenticity, edition or interpretation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--originals", type=Path, required=True)
    p.add_argument("--thinking-docx", type=Path, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    catalog = json.loads((Path(__file__).parent / "sources.json").read_text())
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    checked = []
    for source in catalog["sources"]:
        artifact = source["original_artifact"]
        path = args.originals / artifact["filename"]
        raw = path.read_bytes()
        if digest(raw) != artifact["sha256"] or len(raw) != artifact["bytes"]:
            raise ValueError("Original bytes changed: " + source["source_id"])
        docx = args.thinking_docx if path.suffix == ".doc" else path
        with zipfile.ZipFile(docx) as archive:
            document = ET.fromstring(archive.read("word/document.xml"))
        body = document.find("w:body", ns)
        paragraphs = ["".join(t.text or "" for t in node.findall(".//w:t", ns)) + "\n"
                      for node in body.findall(".//w:p", ns)]
        extracted = "".join(paragraphs).encode()
        extraction = source["canonical_extraction"]
        if digest(extracted) != extraction["sha256"] or len(extracted) != extraction["bytes"]:
            raise ValueError("Extraction changed: " + source["source_id"])
        excerpt = (root / source["local_path"]).read_bytes()
        if digest(excerpt) != source["source_sha256"]:
            raise ValueError("Excerpt changed")
        offset = 0
        for span in source["spans"]:
            quote = span["quote"].encode()
            start = span["extraction_offset"]
            if (paragraphs[span["paragraph"] - 1].encode() != quote or
                    extracted[start:start + len(quote)] != quote or
                    span["offset"] != offset or excerpt[offset:offset + len(quote)] != quote):
                raise ValueError("Paragraph or byte range changed")
            offset += len(quote)
        if offset != len(excerpt):
            raise ValueError("Unaccounted excerpt bytes")
        checked.append({"source_id": source["source_id"], "original_sha256": digest(raw),
                        "docx_sha256": digest(docx.read_bytes()), "extraction_sha256": digest(extracted),
                        "retained_sha256": digest(excerpt), "paragraphs_checked": len(source["spans"])})
    print(json.dumps({"ok": True, "sources": checked, "scope": "local byte comparison only",
                      "authenticity_established": False}, indent=2))


if __name__ == "__main__":
    main()
