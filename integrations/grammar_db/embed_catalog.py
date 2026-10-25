"""Optional pinned-model embedding job; no default model/network download.

Documents and queries use the same search projection. SentenceTransformer's
pinned tokenizer/model defines its sequence limit; long inputs may be truncated.
This index is for proposals only, not exhaustive source or grammar recognition.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .client import (documents, embedding_metadata, search, search_projection,
                     snapshot_digest, store_embeddings)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("index", "query"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--model", required=True, help="SentenceTransformer repository ID")
    parser.add_argument("--revision", required=True, help="immutable 40-character model commit SHA")
    parser.add_argument("--allow-download", action="store_true", help="explicitly allow fetching the pinned model")
    parser.add_argument("--query", default="")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    dsn = os.environ.get("NABT_DATABASE_URL")
    if not dsn:
        parser.error("set NABT_DATABASE_URL outside the repository")
    from tools.grammar_catalog.catalog import build_catalog, validate_catalog
    catalog = validate_catalog(build_catalog(root=args.root), root=args.root)
    digest = snapshot_digest(catalog)
    # Validate immutable revision syntax before loading any third-party model.
    embedding_metadata(digest, args.model, args.revision, 1)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(args.model, revision=args.revision,
                               trust_remote_code=False, local_files_only=not args.allow_download)
    dimensions = model.get_sentence_embedding_dimension()
    metadata = embedding_metadata(digest, args.model, args.revision, dimensions)
    import psycopg
    with psycopg.connect(dsn) as connection:
        if args.command == "index":
            docs = list(documents(catalog))
            vectors = model.encode([row[3] for row in docs], convert_to_numpy=True,
                                   normalize_embeddings=True, show_progress_bar=True)
            store_embeddings(connection, metadata, [(row[0], vector) for row, vector in zip(docs, vectors, strict=True)])
            result = {"status": "EMBEDDINGS_INDEXED", "metadata": metadata,
                      "document_count": len(docs), "model_sequence_limit": model.max_seq_length,
                      "long_input_policy": "pinned model/tokenizer truncation; no exhaustive claim"}
        else:
            vector = model.encode(search_projection(args.query), convert_to_numpy=True,
                                  normalize_embeddings=True)
            result = search(connection, digest, args.query, embedding=vector,
                            embedding_run=metadata, k=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
