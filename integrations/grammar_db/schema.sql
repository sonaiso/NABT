-- NABT optional retrieval catalogue v1. This schema confers no grammar authority.
-- Run once with an extension/schema owner; give applications only required rights.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA nabt_catalog;

CREATE TABLE nabt_catalog.snapshots (
    snapshot_sha text PRIMARY KEY CHECK (snapshot_sha ~ '^[0-9a-f]{64}$'),
    schema_id text NOT NULL,
    authority text NOT NULL CHECK (authority = 'RETRIEVAL_ONLY'),
    coverage jsonb NOT NULL,
    imported_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE nabt_catalog.sources (
    snapshot_sha text NOT NULL REFERENCES nabt_catalog.snapshots,
    source_key text NOT NULL,
    source_id text NOT NULL,
    sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    title text NOT NULL,
    local_path text,
    original_url text,
    byte_count bigint CHECK (byte_count >= 0),
    content_available boolean NOT NULL,
    provenance jsonb NOT NULL,
    PRIMARY KEY (snapshot_sha, source_key),
    UNIQUE (snapshot_sha, source_id, sha256)
);
CREATE TABLE nabt_catalog.passages (
    snapshot_sha text NOT NULL,
    passage_id text NOT NULL,
    source_key text NOT NULL,
    start_byte bigint NOT NULL CHECK (start_byte >= 0),
    end_byte bigint NOT NULL CHECK (end_byte > start_byte),
    sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    raw_text text NOT NULL,
    kinds jsonb NOT NULL,
    provenance jsonb NOT NULL,
    PRIMARY KEY (snapshot_sha, passage_id),
    UNIQUE (snapshot_sha, source_key, start_byte, end_byte, sha256),
    FOREIGN KEY (snapshot_sha, source_key) REFERENCES nabt_catalog.sources
);
CREATE TABLE nabt_catalog.rules (
    snapshot_sha text NOT NULL REFERENCES nabt_catalog.snapshots,
    rule_key text NOT NULL,
    registry_id text NOT NULL,
    local_id text NOT NULL,
    title text NOT NULL,
    description text NOT NULL,
    keywords text[] NOT NULL,
    runtime_rule_id text,
    source_status text NOT NULL,
    scope jsonb NOT NULL,
    provenance jsonb NOT NULL,
    PRIMARY KEY (snapshot_sha, rule_key),
    UNIQUE (snapshot_sha, registry_id, local_id)
);
CREATE TABLE nabt_catalog.attestations (
    snapshot_sha text NOT NULL,
    rule_key text NOT NULL,
    passage_id text NOT NULL,
    PRIMARY KEY (snapshot_sha, rule_key, passage_id),
    FOREIGN KEY (snapshot_sha, rule_key) REFERENCES nabt_catalog.rules,
    FOREIGN KEY (snapshot_sha, passage_id) REFERENCES nabt_catalog.passages
);
-- A named theorem link is provenance, not proof of the rule or free-text input.
CREATE TABLE nabt_catalog.theorem_references (
    snapshot_sha text NOT NULL,
    rule_key text NOT NULL,
    theorem_name text NOT NULL,
    PRIMARY KEY (snapshot_sha, rule_key, theorem_name),
    FOREIGN KEY (snapshot_sha, rule_key) REFERENCES nabt_catalog.rules
);
CREATE TABLE nabt_catalog.items (
    snapshot_sha text NOT NULL REFERENCES nabt_catalog.snapshots,
    item_id text NOT NULL,
    item_kind text NOT NULL,
    payload jsonb NOT NULL,
    PRIMARY KEY (snapshot_sha, item_id)
);
-- Documents are rebuildable search projections; raw evidence stays in passages.
CREATE TABLE nabt_catalog.documents (
    snapshot_sha text NOT NULL REFERENCES nabt_catalog.snapshots,
    document_id text NOT NULL,
    kind text NOT NULL CHECK (kind IN ('rule', 'passage', 'item')),
    entity_id text NOT NULL,
    rule_entity_id text GENERATED ALWAYS AS
        (CASE WHEN kind = 'rule' THEN entity_id END) STORED,
    passage_entity_id text GENERATED ALWAYS AS
        (CASE WHEN kind = 'passage' THEN entity_id END) STORED,
    item_entity_id text GENERATED ALWAYS AS
        (CASE WHEN kind = 'item' THEN entity_id END) STORED,
    search_text text NOT NULL,
    search_vector tsvector GENERATED ALWAYS AS
        (to_tsvector('simple'::regconfig, search_text)) STORED,
    PRIMARY KEY (snapshot_sha, document_id),
    UNIQUE (snapshot_sha, kind, entity_id),
    CHECK (document_id = kind || ':' || entity_id),
    FOREIGN KEY (snapshot_sha, rule_entity_id) REFERENCES nabt_catalog.rules,
    FOREIGN KEY (snapshot_sha, passage_entity_id) REFERENCES nabt_catalog.passages,
    FOREIGN KEY (snapshot_sha, item_entity_id) REFERENCES nabt_catalog.items
);
CREATE INDEX documents_lexical ON nabt_catalog.documents USING gin (search_vector);
CREATE INDEX rules_keywords ON nabt_catalog.rules USING gin (keywords);
CREATE TABLE nabt_catalog.embedding_runs (
    snapshot_sha text NOT NULL REFERENCES nabt_catalog.snapshots,
    run_id text NOT NULL CHECK (run_id ~ '^[0-9a-f]{64}$'),
    model_id text NOT NULL,
    model_revision text NOT NULL CHECK (model_revision ~ '^[0-9a-f]{40}$'),
    dimensions integer NOT NULL CHECK (dimensions BETWEEN 1 AND 16000),
    input_recipe text NOT NULL,
    PRIMARY KEY (snapshot_sha, run_id),
    UNIQUE (snapshot_sha, run_id, dimensions)
);
CREATE TABLE nabt_catalog.embeddings (
    snapshot_sha text NOT NULL,
    run_id text NOT NULL,
    document_id text NOT NULL,
    dimensions integer NOT NULL,
    embedding vector NOT NULL,
    PRIMARY KEY (snapshot_sha, run_id, document_id),
    FOREIGN KEY (snapshot_sha, run_id, dimensions)
        REFERENCES nabt_catalog.embedding_runs (snapshot_sha, run_id, dimensions),
    FOREIGN KEY (snapshot_sha, document_id) REFERENCES nabt_catalog.documents,
    CHECK (vector_dims(embedding) = dimensions),
    CHECK (vector_norm(embedding) BETWEEN 0.999 AND 1.001)
);
-- Exact distance scan is intentional: no IVFFlat/HNSW recall assumption.
-- pgvector itself rejects non-finite stored components.
-- Evidence is append-only under normal DML; changes require a new snapshot.
CREATE FUNCTION nabt_catalog.reject_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'NABT catalogue rows are immutable; import a new snapshot';
END;
$$;
DO $$
DECLARE table_name text;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'snapshots','sources','passages','rules','attestations',
        'theorem_references','items','documents','embedding_runs','embeddings'
    ] LOOP
        EXECUTE format('CREATE TRIGGER immutable_rows BEFORE UPDATE OR DELETE ON nabt_catalog.%I '
            'FOR EACH ROW EXECUTE FUNCTION nabt_catalog.reject_mutation()', table_name);
        EXECUTE format('CREATE TRIGGER immutable_truncate BEFORE TRUNCATE ON nabt_catalog.%I '
            'FOR EACH STATEMENT EXECUTE FUNCTION nabt_catalog.reject_mutation()', table_name);
    END LOOP;
END;
$$;
