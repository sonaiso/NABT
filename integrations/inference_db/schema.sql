-- Additive provenance layer. Install grammar_db/schema.sql first.
-- A foreign key establishes identity, not source truth or inference validity.
CREATE SCHEMA nabt_inference;

CREATE TABLE nabt_inference.snapshots (
    inventory_sha text PRIMARY KEY CHECK (inventory_sha ~ '^[0-9a-f]{64}$'),
    schema_id text NOT NULL,
    authority text NOT NULL CHECK (authority = 'PROVENANCE_ONLY'),
    metadata jsonb NOT NULL,
    imported_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE nabt_inference.grammar_bindings (
    inventory_sha text NOT NULL REFERENCES nabt_inference.snapshots,
    catalog_sha text NOT NULL REFERENCES nabt_catalog.snapshots(snapshot_sha),
    PRIMARY KEY (inventory_sha, catalog_sha)
);
CREATE TABLE nabt_inference.profiles (
    inventory_sha text NOT NULL REFERENCES nabt_inference.snapshots,
    profile_id text NOT NULL CHECK (profile_id <> ''),
    description text NOT NULL,
    PRIMARY KEY (inventory_sha, profile_id)
);
CREATE TABLE nabt_inference.sources (
    inventory_sha text NOT NULL REFERENCES nabt_inference.snapshots,
    source_id text NOT NULL,
    sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    byte_count bigint NOT NULL CHECK (byte_count >= 0),
    local_path text NOT NULL,
    metadata jsonb NOT NULL,
    PRIMARY KEY (inventory_sha, source_id)
);
CREATE TABLE nabt_inference.passages (
    inventory_sha text NOT NULL,
    passage_id text NOT NULL,
    source_id text NOT NULL,
    start_byte bigint NOT NULL CHECK (start_byte >= 0),
    end_byte bigint NOT NULL CHECK (end_byte > start_byte),
    sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    raw_text text NOT NULL,
    metadata jsonb NOT NULL,
    PRIMARY KEY (inventory_sha, passage_id),
    FOREIGN KEY (inventory_sha, source_id) REFERENCES nabt_inference.sources,
    CHECK (octet_length(raw_text) = end_byte - start_byte)
);
CREATE TABLE nabt_inference.rules (
    inventory_sha text NOT NULL,
    rule_id text NOT NULL CHECK (rule_id <> ''),
    profile_id text NOT NULL,
    source_status text NOT NULL,
    search_text text NOT NULL,
    search_vector tsvector GENERATED ALWAYS AS
        (to_tsvector('simple'::regconfig, search_text)) STORED,
    payload jsonb NOT NULL,
    PRIMARY KEY (inventory_sha, rule_id),
    UNIQUE (inventory_sha, rule_id, profile_id),
    FOREIGN KEY (inventory_sha, profile_id) REFERENCES nabt_inference.profiles
);
CREATE INDEX inference_rules_lexical ON nabt_inference.rules USING gin(search_vector);
CREATE TABLE nabt_inference.rule_passages (
    inventory_sha text NOT NULL,
    rule_id text NOT NULL,
    passage_id text NOT NULL,
    PRIMARY KEY (inventory_sha, rule_id, passage_id),
    FOREIGN KEY (inventory_sha, rule_id) REFERENCES nabt_inference.rules,
    FOREIGN KEY (inventory_sha, passage_id) REFERENCES nabt_inference.passages
);
-- Reviewed source context is kept separate from original authored rule
-- citations and compiled theorem references. It cannot establish an occurrence
-- license or silently change an executable rule.
CREATE TABLE nabt_inference.reviewed_contexts (
    inventory_sha text NOT NULL,
    rule_id text NOT NULL,
    passage_id text NOT NULL,
    relation text NOT NULL CHECK (relation = 'REVIEWED_CONTEXT_CANDIDATE_BASIS'),
    source_context_only boolean NOT NULL CHECK (source_context_only = true),
    linguistic_license_established boolean NOT NULL CHECK (linguistic_license_established = false),
    executable_rule_changed boolean NOT NULL CHECK (executable_rule_changed = false),
    PRIMARY KEY (inventory_sha, rule_id, passage_id),
    FOREIGN KEY (inventory_sha, rule_id) REFERENCES nabt_inference.rules,
    FOREIGN KEY (inventory_sha, passage_id) REFERENCES nabt_inference.passages
);
-- These are authored names for navigation, not certificates. The live Lean
-- catalogue and runtime checker remain responsible for proof replay.
CREATE TABLE nabt_inference.theorem_references (
    inventory_sha text NOT NULL,
    rule_id text NOT NULL,
    theorem_name text NOT NULL CHECK (theorem_name <> ''),
    relation text NOT NULL CHECK (relation = 'AUTHORED_REFERENCE'),
    PRIMARY KEY (inventory_sha, rule_id, theorem_name),
    FOREIGN KEY (inventory_sha, rule_id) REFERENCES nabt_inference.rules
);
CREATE TABLE nabt_inference.obligations (
    inventory_sha text NOT NULL,
    rule_id text NOT NULL,
    ordinal integer NOT NULL CHECK (ordinal >= 0),
    role text NOT NULL CHECK (role IN ('premise','cause','condition','blocker_absence',
        'source_bridge','analogy_origin','analogy_cause','analogy_transfer')),
    atom_key text NOT NULL CHECK (atom_key <> ''),
    positive boolean NOT NULL,
    PRIMARY KEY (inventory_sha, rule_id, ordinal),
    FOREIGN KEY (inventory_sha, rule_id) REFERENCES nabt_inference.rules,
    CHECK (role <> 'blocker_absence' OR positive = false)
);
CREATE TABLE nabt_inference.contexts (
    inventory_sha text NOT NULL,
    context_id text NOT NULL,
    profile_id text NOT NULL,
    scope_text text NOT NULL,
    qualifications jsonb NOT NULL,
    PRIMARY KEY (inventory_sha, context_id),
    UNIQUE (inventory_sha, context_id, profile_id),
    FOREIGN KEY (inventory_sha, profile_id) REFERENCES nabt_inference.profiles
);
CREATE TABLE nabt_inference.lexemes (
    inventory_sha text NOT NULL REFERENCES nabt_inference.snapshots,
    lexeme_id text NOT NULL,
    raw_token text NOT NULL,
    morphological_pattern text,
    PRIMARY KEY (inventory_sha, lexeme_id)
);
CREATE INDEX inference_lexeme_token ON nabt_inference.lexemes(raw_token);
CREATE TABLE nabt_inference.concepts (
    inventory_sha text NOT NULL REFERENCES nabt_inference.snapshots,
    concept_id text NOT NULL,
    description text NOT NULL,
    PRIMARY KEY (inventory_sha, concept_id)
);
-- Neither word nor concept determines a unique sense. Every candidate sense
-- has an explicit profile/context and an attested passage.
CREATE TABLE nabt_inference.senses (
    inventory_sha text NOT NULL,
    lexeme_id text NOT NULL,
    concept_id text NOT NULL,
    context_id text NOT NULL,
    profile_id text NOT NULL,
    passage_id text NOT NULL,
    PRIMARY KEY (inventory_sha, lexeme_id, concept_id, context_id, passage_id),
    FOREIGN KEY (inventory_sha, lexeme_id) REFERENCES nabt_inference.lexemes,
    FOREIGN KEY (inventory_sha, concept_id) REFERENCES nabt_inference.concepts,
    FOREIGN KEY (inventory_sha, context_id, profile_id)
        REFERENCES nabt_inference.contexts(inventory_sha, context_id, profile_id),
    FOREIGN KEY (inventory_sha, passage_id) REFERENCES nabt_inference.passages
);
-- Recording an observation is separate from accepting a statement as true.
-- No default "empirically true" exists, and observations are not inference facts.
CREATE TABLE nabt_inference.observations (
    inventory_sha text NOT NULL,
    observation_id text NOT NULL,
    context_id text NOT NULL,
    concept_id text NOT NULL,
    protocol_uri text,
    evidence_sha text CHECK (evidence_sha ~ '^[0-9a-f]{64}$'),
    result_text text,
    review_state text NOT NULL DEFAULT 'UNREVIEWED'
        CHECK (review_state IN ('UNREVIEWED','REPORTED','CONTESTED','RETRACTED')),
    PRIMARY KEY (inventory_sha, observation_id),
    FOREIGN KEY (inventory_sha, context_id) REFERENCES nabt_inference.contexts,
    FOREIGN KEY (inventory_sha, concept_id) REFERENCES nabt_inference.concepts,
    CHECK ((protocol_uri IS NULL AND evidence_sha IS NULL AND result_text IS NULL)
        OR (protocol_uri IS NOT NULL AND protocol_uri <> '' AND evidence_sha IS NOT NULL
            AND result_text IS NOT NULL AND result_text <> ''))
);
-- Optional navigation to existing grammar documents uses their existing
-- lexical/vector index. Both snapshots and the document kind are bound by FK.
CREATE TABLE nabt_inference.grammar_navigation (
    inventory_sha text NOT NULL,
    rule_id text NOT NULL,
    catalog_sha text NOT NULL,
    document_id text NOT NULL,
    PRIMARY KEY (inventory_sha, rule_id, document_id),
    FOREIGN KEY (inventory_sha, rule_id) REFERENCES nabt_inference.rules,
    FOREIGN KEY (inventory_sha, catalog_sha) REFERENCES nabt_inference.grammar_bindings,
    FOREIGN KEY (catalog_sha, document_id) REFERENCES nabt_catalog.documents(snapshot_sha, document_id)
);
CREATE TABLE nabt_inference.embedding_runs (
    inventory_sha text NOT NULL REFERENCES nabt_inference.snapshots,
    run_id text NOT NULL CHECK (run_id ~ '^[0-9a-f]{64}$'),
    model_id text NOT NULL CHECK (model_id <> ''),
    model_revision text NOT NULL CHECK (model_revision ~ '^[0-9a-f]{40}$'),
    dimensions integer NOT NULL CHECK (dimensions BETWEEN 1 AND 16000),
    input_recipe text NOT NULL CHECK (input_recipe = 'nabt.inference.search-projection.v1'),
    PRIMARY KEY (inventory_sha, run_id),
    UNIQUE (inventory_sha, run_id, dimensions)
);
CREATE TABLE nabt_inference.embeddings (
    inventory_sha text NOT NULL,
    run_id text NOT NULL,
    rule_id text NOT NULL,
    dimensions integer NOT NULL,
    embedding vector NOT NULL,
    PRIMARY KEY (inventory_sha, run_id, rule_id),
    FOREIGN KEY (inventory_sha, run_id, dimensions)
        REFERENCES nabt_inference.embedding_runs(inventory_sha, run_id, dimensions),
    FOREIGN KEY (inventory_sha, rule_id) REFERENCES nabt_inference.rules,
    CHECK (vector_dims(embedding) = dimensions),
    CHECK (vector_norm(embedding) BETWEEN 0.999 AND 1.001)
);
CREATE FUNCTION nabt_inference.reject_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'NABT inference provenance is immutable; import a new snapshot';
END;
$$;
DO $$
DECLARE table_name text;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'snapshots','grammar_bindings','profiles','sources','passages','rules','rule_passages','reviewed_contexts',
        'theorem_references','obligations','contexts','lexemes','concepts',
        'senses','observations','grammar_navigation','embedding_runs','embeddings'
    ] LOOP
        EXECUTE format('CREATE TRIGGER immutable_rows BEFORE UPDATE OR DELETE ON nabt_inference.%I '
            'FOR EACH ROW EXECUTE FUNCTION nabt_inference.reject_mutation()', table_name);
        EXECUTE format('CREATE TRIGGER immutable_truncate BEFORE TRUNCATE ON nabt_inference.%I '
            'FOR EACH STATEMENT EXECUTE FUNCTION nabt_inference.reject_mutation()', table_name);
    END LOOP;
END;
$$;
