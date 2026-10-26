-- Optional additive storage contract: install grammar_db/schema.sql and
-- inference_db/schema.sql first. No seeds, roots, vectors or facts are inserted.
-- This is provenance storage, not the Lean authority or a public importer.
CREATE TABLE nabt_inference.lexical_graph_snapshots (
    graph_sha text PRIMARY KEY CHECK (graph_sha ~ '^[0-9a-f]{64}$'),
    inventory_sha text NOT NULL,
    context_id text NOT NULL,
    profile_id text NOT NULL,
    schema_id text NOT NULL CHECK (schema_id = 'nabt.lexical-graph-storage.v1'),
    law_id text NOT NULL CHECK (law_id <> ''),
    authority text NOT NULL CHECK (authority = 'PROVENANCE_ONLY'),
    UNIQUE (graph_sha, inventory_sha),
    UNIQUE (graph_sha, inventory_sha, context_id, profile_id),
    FOREIGN KEY (inventory_sha, context_id, profile_id)
        REFERENCES nabt_inference.contexts(inventory_sha, context_id, profile_id)
);

-- A node is a qualified signed atom, never a bare root. A lexical-sense atom
-- must identify an existing many-to-many sense in the original ledger. An
-- authored semantic atom identifies an existing concept and cited passage.
CREATE TABLE nabt_inference.lexical_graph_nodes (
    graph_sha text NOT NULL,
    node_id text NOT NULL CHECK (node_id <> ''),
    inventory_sha text NOT NULL,
    context_id text NOT NULL,
    profile_id text NOT NULL,
    node_kind text NOT NULL CHECK (node_kind IN ('LEXICAL_SENSE','SEMANTIC_ATOM')),
    concept_id text NOT NULL,
    lexeme_id text,
    passage_id text NOT NULL,
    positive boolean NOT NULL,
    interpretation_state text NOT NULL DEFAULT 'AUTHORED_UNREVIEWED'
        CHECK (interpretation_state IN ('AUTHORED_UNREVIEWED','REVIEWED_INTERPRETATION','CONTESTED')),
    PRIMARY KEY (graph_sha, node_id),
    UNIQUE (graph_sha, node_id, positive),
    FOREIGN KEY (graph_sha, inventory_sha, context_id, profile_id)
        REFERENCES nabt_inference.lexical_graph_snapshots(graph_sha, inventory_sha, context_id, profile_id),
    FOREIGN KEY (inventory_sha, concept_id) REFERENCES nabt_inference.concepts,
    FOREIGN KEY (inventory_sha, passage_id) REFERENCES nabt_inference.passages,
    FOREIGN KEY (inventory_sha, lexeme_id, concept_id, context_id, passage_id)
        REFERENCES nabt_inference.senses,
    CHECK ((node_kind = 'LEXICAL_SENSE' AND lexeme_id IS NOT NULL)
        OR (node_kind = 'SEMANTIC_ATOM' AND lexeme_id IS NULL))
);
CREATE UNIQUE INDEX lexical_graph_unique_sense ON nabt_inference.lexical_graph_nodes
    (graph_sha, lexeme_id, concept_id, passage_id, positive) WHERE node_kind = 'LEXICAL_SENSE';
CREATE UNIQUE INDEX lexical_graph_unique_atom ON nabt_inference.lexical_graph_nodes
    (graph_sha, concept_id, positive) WHERE node_kind = 'SEMANTIC_ATOM';

-- A mention/paraphrase link can be cyclic. It is never an inference rule and
-- cannot become one through a label, review state, path or vector similarity.
CREATE TABLE nabt_inference.lexical_graph_references (
    graph_sha text NOT NULL,
    reference_id text NOT NULL CHECK (reference_id <> ''),
    inventory_sha text NOT NULL,
    source_node_id text NOT NULL,
    target_node_id text NOT NULL,
    passage_id text NOT NULL,
    relation_kind text NOT NULL CHECK (relation_kind IN
        ('DEFINITION_MENTION','ATTESTED_PARAPHRASE','ATTESTED_OPPOSITION',
         'AUTHORED_COMPONENT_LINK','AUTHORED_NECESSITY_LINK')),
    review_state text NOT NULL DEFAULT 'UNREVIEWED'
        CHECK (review_state IN ('UNREVIEWED','REVIEWED','CONTESTED')),
    authority text NOT NULL CHECK (authority = 'REFERENCE_ONLY'),
    PRIMARY KEY (graph_sha, reference_id),
    UNIQUE (graph_sha, source_node_id, target_node_id, relation_kind, passage_id),
    FOREIGN KEY (graph_sha, inventory_sha) REFERENCES nabt_inference.lexical_graph_snapshots(graph_sha, inventory_sha),
    FOREIGN KEY (graph_sha, source_node_id) REFERENCES nabt_inference.lexical_graph_nodes,
    FOREIGN KEY (graph_sha, target_node_id) REFERENCES nabt_inference.lexical_graph_nodes,
    FOREIGN KEY (inventory_sha, passage_id) REFERENCES nabt_inference.passages
);

-- Typed rule candidates need a separately installed base law, citation and
-- explicit prerequisite rows. The kind alone does not license composition.
CREATE TABLE nabt_inference.lexical_graph_rules (
    graph_sha text NOT NULL,
    rule_id text NOT NULL CHECK (rule_id <> ''),
    inventory_sha text NOT NULL,
    profile_id text NOT NULL,
    context_id text NOT NULL,
    basis_rule_id text NOT NULL,
    conclusion_node_id text NOT NULL,
    inference_kind text NOT NULL CHECK (inference_kind IN
        ('MUTABAQA','TADAMMUN','MENTAL_NECESSITY','EXPLICIT_BRIDGE')),
    passage_id text NOT NULL,
    interpretation_state text NOT NULL DEFAULT 'AUTHORED_UNREVIEWED'
        CHECK (interpretation_state IN ('AUTHORED_UNREVIEWED','REVIEWED_INTERPRETATION','CONTESTED')),
    authority text NOT NULL CHECK (authority = 'CONDITIONAL_RULE_CANDIDATE'),
    PRIMARY KEY (graph_sha, rule_id),
    FOREIGN KEY (graph_sha, inventory_sha, context_id, profile_id)
        REFERENCES nabt_inference.lexical_graph_snapshots(graph_sha, inventory_sha, context_id, profile_id),
    FOREIGN KEY (inventory_sha, basis_rule_id, profile_id)
        REFERENCES nabt_inference.rules(inventory_sha, rule_id, profile_id),
    FOREIGN KEY (graph_sha, conclusion_node_id) REFERENCES nabt_inference.lexical_graph_nodes,
    FOREIGN KEY (inventory_sha, passage_id) REFERENCES nabt_inference.passages
);
CREATE TABLE nabt_inference.lexical_graph_premises (
    graph_sha text NOT NULL,
    rule_id text NOT NULL,
    ordinal integer NOT NULL CHECK (ordinal >= 0),
    premise_node_id text NOT NULL,
    required_positive boolean NOT NULL,
    role text NOT NULL CHECK (role IN
        ('premise','condition','source_license','context_license','blocker_absence')),
    PRIMARY KEY (graph_sha, rule_id, ordinal),
    UNIQUE (graph_sha, rule_id, premise_node_id),
    FOREIGN KEY (graph_sha, rule_id) REFERENCES nabt_inference.lexical_graph_rules,
    FOREIGN KEY (graph_sha, premise_node_id, required_positive)
        REFERENCES nabt_inference.lexical_graph_nodes(graph_sha, node_id, positive),
    CHECK (role <> 'blocker_absence' OR required_positive = false)
);

-- Seeds are explicit premises of a run, not truths inferred from a cycle.
-- An attestation premise still needs local source replay before runtime use.
CREATE TABLE nabt_inference.lexical_graph_seeds (
    graph_sha text NOT NULL,
    seed_id text NOT NULL CHECK (seed_id <> ''),
    inventory_sha text NOT NULL,
    node_id text NOT NULL,
    passage_id text NOT NULL,
    basis_kind text NOT NULL CHECK (basis_kind IN ('ATTESTATION_PREMISE','DECLARED_HYPOTHESIS')),
    authority text NOT NULL CHECK (authority = 'EXPLICIT_PREMISE_ONLY'),
    PRIMARY KEY (graph_sha, seed_id),
    UNIQUE (graph_sha, node_id, passage_id, basis_kind),
    FOREIGN KEY (graph_sha, inventory_sha) REFERENCES nabt_inference.lexical_graph_snapshots(graph_sha, inventory_sha),
    FOREIGN KEY (graph_sha, node_id) REFERENCES nabt_inference.lexical_graph_nodes,
    FOREIGN KEY (inventory_sha, passage_id) REFERENCES nabt_inference.passages
);
CREATE TABLE nabt_inference.lexical_graph_seals (
    graph_sha text PRIMARY KEY REFERENCES nabt_inference.lexical_graph_snapshots,
    node_count bigint NOT NULL CHECK (node_count >= 0),
    reference_count bigint NOT NULL CHECK (reference_count >= 0),
    rule_count bigint NOT NULL CHECK (rule_count >= 0),
    premise_count bigint NOT NULL CHECK (premise_count >= 0),
    seed_count bigint NOT NULL CHECK (seed_count >= 0),
    sealed_at timestamptz NOT NULL DEFAULT now(),
    authority text NOT NULL CHECK (authority = 'STORAGE_SHAPE_ONLY')
);

CREATE INDEX lexical_graph_reference_source ON nabt_inference.lexical_graph_references(graph_sha, source_node_id);
CREATE INDEX lexical_graph_rule_conclusion ON nabt_inference.lexical_graph_rules(graph_sha, conclusion_node_id);
CREATE INDEX lexical_graph_premise_node ON nabt_inference.lexical_graph_premises(graph_sha, premise_node_id);

CREATE FUNCTION nabt_inference.lexical_graph_require_unsealed() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    -- Under REPEATABLE READ, locking an unchanged parent does not refresh the
    -- transaction snapshot. A newly committed seal could otherwise be missed.
    IF current_setting('transaction_isolation') <> 'read committed' THEN
        RAISE EXCEPTION 'lexical graph writes require READ COMMITTED';
    END IF;
    -- The parent lock serializes child INSERTs with sealing, avoiding a race in
    -- which a successfully checked graph gains additional rows afterwards.
    PERFORM 1 FROM nabt_inference.lexical_graph_snapshots WHERE graph_sha = NEW.graph_sha FOR UPDATE;
    IF EXISTS (SELECT 1 FROM nabt_inference.lexical_graph_seals WHERE graph_sha = NEW.graph_sha) THEN
        RAISE EXCEPTION 'lexical graph is sealed; import a new graph snapshot';
    END IF;
    RETURN NEW;
END;
$$;
CREATE FUNCTION nabt_inference.lexical_graph_validate_seal() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF current_setting('transaction_isolation') <> 'read committed' THEN
        RAISE EXCEPTION 'lexical graph writes require READ COMMITTED';
    END IF;
    PERFORM 1 FROM nabt_inference.lexical_graph_snapshots WHERE graph_sha = NEW.graph_sha FOR UPDATE;
    IF NEW.node_count <> (SELECT count(*) FROM nabt_inference.lexical_graph_nodes WHERE graph_sha = NEW.graph_sha)
        OR NEW.reference_count <> (SELECT count(*) FROM nabt_inference.lexical_graph_references WHERE graph_sha = NEW.graph_sha)
        OR NEW.rule_count <> (SELECT count(*) FROM nabt_inference.lexical_graph_rules WHERE graph_sha = NEW.graph_sha)
        OR NEW.premise_count <> (SELECT count(*) FROM nabt_inference.lexical_graph_premises WHERE graph_sha = NEW.graph_sha)
        OR NEW.seed_count <> (SELECT count(*) FROM nabt_inference.lexical_graph_seeds WHERE graph_sha = NEW.graph_sha) THEN
        RAISE EXCEPTION 'lexical graph row counts differ from seal';
    END IF;
    IF EXISTS (SELECT 1 FROM nabt_inference.lexical_graph_rules r
        WHERE r.graph_sha = NEW.graph_sha AND NOT EXISTS (
            SELECT 1 FROM nabt_inference.lexical_graph_premises p
            WHERE p.graph_sha = r.graph_sha AND p.rule_id = r.rule_id)) THEN
        RAISE EXCEPTION 'rule has no explicit premise; declare a seed instead';
    END IF;
    IF EXISTS (SELECT 1 FROM nabt_inference.lexical_graph_premises
        WHERE graph_sha = NEW.graph_sha GROUP BY rule_id
        HAVING min(ordinal) <> 0 OR max(ordinal) <> count(*) - 1) THEN
        RAISE EXCEPTION 'rule premise ordinals must be contiguous from zero';
    END IF;
    IF EXISTS (SELECT 1 FROM (
        SELECT r.basis_rule_id, r.inference_kind, r.conclusion_node_id,
            ARRAY(SELECT p.premise_node_id FROM nabt_inference.lexical_graph_premises p
                WHERE p.graph_sha = r.graph_sha AND p.rule_id = r.rule_id
                ORDER BY p.premise_node_id) AS required_nodes
        FROM nabt_inference.lexical_graph_rules r WHERE r.graph_sha = NEW.graph_sha
    ) signatures GROUP BY basis_rule_id, inference_kind, conclusion_node_id, required_nodes
        HAVING count(*) > 1) THEN
        RAISE EXCEPTION 'duplicate rule body; retain one rule identity';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER lexical_graph_seal_shape BEFORE INSERT ON nabt_inference.lexical_graph_seals
    FOR EACH ROW EXECUTE FUNCTION nabt_inference.lexical_graph_validate_seal();
DO $$
DECLARE table_name text;
BEGIN
    FOREACH table_name IN ARRAY ARRAY['lexical_graph_nodes','lexical_graph_references',
        'lexical_graph_rules','lexical_graph_premises','lexical_graph_seeds'] LOOP
        EXECUTE format('CREATE TRIGGER graph_unsealed BEFORE INSERT ON nabt_inference.%I '
            'FOR EACH ROW EXECUTE FUNCTION nabt_inference.lexical_graph_require_unsealed()', table_name);
    END LOOP;
    FOREACH table_name IN ARRAY ARRAY['lexical_graph_snapshots','lexical_graph_nodes',
        'lexical_graph_references','lexical_graph_rules','lexical_graph_premises',
        'lexical_graph_seeds','lexical_graph_seals'] LOOP
        EXECUTE format('CREATE TRIGGER immutable_rows BEFORE UPDATE OR DELETE ON nabt_inference.%I '
            'FOR EACH ROW EXECUTE FUNCTION nabt_inference.reject_mutation()', table_name);
        EXECUTE format('CREATE TRIGGER immutable_truncate BEFORE TRUNCATE ON nabt_inference.%I '
            'FOR EACH STATEMENT EXECUTE FUNCTION nabt_inference.reject_mutation()', table_name);
    END LOOP;
END;
$$;
