"""Storage-contract checks and optional real PostgreSQL adversarial tests.

Static checks do not execute PostgreSQL, prove the SQL, or establish semantics.
The optional suite uses NABT_TEST_DATABASE_URL, creates only additive objects,
and rolls back its entire transaction. It refuses an already installed graph.
"""
import os
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]
SQL = (ROOT / 'integrations/inference_db/lexical_graph.sql').read_text()
DSN = os.environ.get('NABT_TEST_DATABASE_URL')


class LexicalGraphStaticContractTests(unittest.TestCase):
    def test_additive_schema_has_no_seeds_or_new_root_dictionary(self):
        executable = re.sub(r'--[^\n]*', '', SQL)
        self.assertNotRegex(executable, r'(?i)\b(INSERT\s+INTO|ALTER\s+TABLE|DROP\s+TABLE)\b')
        self.assertNotIn('formal_roots', executable)
        self.assertNotIn('20000', executable)
        tables = re.findall(r'CREATE TABLE ([\w.]+)', executable)
        self.assertEqual(len(tables), 7)
        self.assertTrue(all(t.startswith('nabt_inference.lexical_graph_') for t in tables))

    def test_reference_navigation_and_inference_have_distinct_authorities(self):
        self.assertIn("authority = 'REFERENCE_ONLY'", SQL)
        self.assertIn("authority = 'CONDITIONAL_RULE_CANDIDATE'", SQL)
        self.assertIn("authority = 'EXPLICIT_PREMISE_ONLY'", SQL)
        self.assertIn("authority = 'STORAGE_SHAPE_ONLY'", SQL)
        self.assertNotIn('proof_of_completeness', SQL)
        self.assertIn("'ATTESTED_OPPOSITION'", SQL)

    def test_qualified_sense_and_profile_bindings_are_present(self):
        self.assertIn('REFERENCES nabt_inference.senses', SQL)
        self.assertIn('REFERENCES nabt_inference.contexts(inventory_sha, context_id, profile_id)', SQL)
        self.assertIn('source_node_id text NOT NULL', SQL)
        self.assertIn('target_node_id text NOT NULL', SQL)
        self.assertIn("node_kind = 'LEXICAL_SENSE' AND lexeme_id IS NOT NULL", SQL)

    def test_sealing_locks_parent_and_does_not_create_truth_flags(self):
        self.assertIn('FOR UPDATE', SQL)
        self.assertEqual(SQL.count("current_setting('transaction_isolation') <> 'read committed'"), 2)
        self.assertIn('BEFORE INSERT ON nabt_inference.lexical_graph_seals', SQL)
        self.assertIn("rule has no explicit premise; declare a seed instead", SQL)
        self.assertIn("duplicate rule body; retain one rule identity", SQL)
        self.assertNotRegex(SQL, r'(?i)(empirically_true|world_truth_established|native_checked)\s+boolean')

    def test_vector_dimensions_and_similarity_do_not_enter_the_contract(self):
        executable = re.sub(r'--[^\n]*', '', SQL)
        self.assertNotRegex(executable, r'(?i)\bvector\b|<=>|1536|0\.5')


@unittest.skipUnless(DSN, 'NABT_TEST_DATABASE_URL is unset; lexical graph PostgreSQL constraints NOT EXECUTED')
class LexicalGraphPostgreSQLTests(unittest.TestCase):
    inventory = '9' * 64
    graph = 'a' * 64

    @classmethod
    def setUpClass(cls):
        import psycopg
        from integrations.grammar_db import client as grammar
        from integrations.inference_db import client as inference
        cls.psycopg = psycopg
        cls.connection = psycopg.connect(DSN, autocommit=False)
        cls.addClassCleanup(cls.connection.close)
        cls.addClassCleanup(cls.connection.rollback)
        cls.connection.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED')
        if cls.connection.execute("SELECT to_regclass('nabt_inference.lexical_graph_snapshots')").fetchone()[0]:
            raise RuntimeError('lexical graph already exists; use a disposable database')
        if not cls.connection.execute("SELECT to_regclass('nabt_catalog.snapshots')").fetchone()[0]:
            grammar.initialize(cls.connection)
        if not cls.connection.execute("SELECT to_regclass('nabt_inference.snapshots')").fetchone()[0]:
            inference.initialize(cls.connection)
        cls.connection.execute(SQL)
        q = cls.connection.execute
        q("INSERT INTO nabt_inference.snapshots VALUES (%s,'synthetic-graph-test','PROVENANCE_ONLY','{}',now())", (cls.inventory,))
        for profile, context in [('p','ctx'), ('other','other-context')]:
            q("INSERT INTO nabt_inference.profiles VALUES (%s,%s,'synthetic')", (cls.inventory, profile))
            q("INSERT INTO nabt_inference.contexts VALUES (%s,%s,%s,'synthetic','{}')", (cls.inventory, context, profile))
        q("INSERT INTO nabt_inference.sources VALUES (%s,'source',%s,1,'synthetic','{}')", (cls.inventory, '1' * 64))
        q("INSERT INTO nabt_inference.passages VALUES (%s,'passage','source',0,1,%s,'x','{}')", (cls.inventory, '2' * 64))
        q("INSERT INTO nabt_inference.lexemes VALUES (%s,'word','لفظ',NULL)", (cls.inventory,))
        for concept in ['a', 'b', 'c', 'd']:
            q("INSERT INTO nabt_inference.concepts VALUES (%s,%s,'synthetic atom')", (cls.inventory, concept))
        for concept in ['a', 'b']:
            q("INSERT INTO nabt_inference.senses VALUES (%s,'word',%s,'ctx','p','passage')", (cls.inventory, concept))
        q("""INSERT INTO nabt_inference.rules
            (inventory_sha,rule_id,profile_id,source_status,search_text,payload)
            VALUES (%s,'basis','p','AUTHORED_UNREVIEWED','synthetic','{}')""", (cls.inventory,))

    def setUp(self):
        self.connection.execute('SAVEPOINT graph_test')
        self.connection.execute("""INSERT INTO nabt_inference.lexical_graph_snapshots
            VALUES (%s,%s,'ctx','p','nabt.lexical-graph-storage.v1','synthetic-law','PROVENANCE_ONLY')""",
            (self.graph, self.inventory))
        for node in ['a', 'b', 'c']:
            self.node(node)

    def tearDown(self):
        self.connection.execute('ROLLBACK TO SAVEPOINT graph_test')
        self.connection.execute('RELEASE SAVEPOINT graph_test')

    def node(self, node, *, context='ctx', profile='p', kind='SEMANTIC_ATOM', lexeme=None, positive=True, concept=None):
        self.connection.execute("""INSERT INTO nabt_inference.lexical_graph_nodes
            (graph_sha,node_id,inventory_sha,context_id,profile_id,node_kind,concept_id,lexeme_id,passage_id,positive)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'passage',%s)""",
            (self.graph,node,self.inventory,context,profile,kind,concept or node,lexeme,positive))

    def rule(self, rule='r', conclusion='c'):
        self.connection.execute("""INSERT INTO nabt_inference.lexical_graph_rules
            (graph_sha,rule_id,inventory_sha,profile_id,context_id,basis_rule_id,conclusion_node_id,inference_kind,passage_id,authority)
            VALUES (%s,%s,%s,'p','ctx','basis',%s,'EXPLICIT_BRIDGE','passage','CONDITIONAL_RULE_CANDIDATE')""",
            (self.graph, rule, self.inventory, conclusion))

    def premise(self, node='a', ordinal=0, rule='r', positive=True, role='premise'):
        self.connection.execute("INSERT INTO nabt_inference.lexical_graph_premises VALUES (%s,%s,%s,%s,%s,%s)",
                                (self.graph, rule, ordinal, node, positive, role))

    def seal(self, nodes=3, references=0, rules=0, premises=0, seeds=0):
        self.connection.execute("""INSERT INTO nabt_inference.lexical_graph_seals
            (graph_sha,node_count,reference_count,rule_count,premise_count,seed_count,authority)
            VALUES (%s,%s,%s,%s,%s,%s,'STORAGE_SHAPE_ONLY')""",
            (self.graph, nodes, references, rules, premises, seeds))

    def rejected(self, error, action):
        with self.assertRaises(error), self.connection.transaction():
            action()

    def test_reference_cycles_are_storable_and_create_no_seeds(self):
        for source, target in [('a','b'),('b','c'),('c','a')]:
            self.connection.execute("""INSERT INTO nabt_inference.lexical_graph_references
                (graph_sha,reference_id,inventory_sha,source_node_id,target_node_id,passage_id,relation_kind,authority)
                VALUES (%s,%s,%s,%s,%s,'passage','DEFINITION_MENTION','REFERENCE_ONLY')""",
                (self.graph, source + target, self.inventory, source, target))
        self.seal(references=3)
        count = self.connection.execute('SELECT count(*) FROM nabt_inference.lexical_graph_seeds WHERE graph_sha=%s', (self.graph,)).fetchone()[0]
        self.assertEqual(count, 0)

    def test_context_and_full_sense_foreign_keys_reject_mismatches(self):
        self.rejected(self.psycopg.errors.ForeignKeyViolation, lambda: self.node('foreign', concept='d', context='other-context', profile='other'))
        self.rejected(self.psycopg.errors.ForeignKeyViolation, lambda: self.node('invalid-sense', concept='c', kind='LEXICAL_SENSE', lexeme='word'))
        self.rejected(self.psycopg.errors.CheckViolation, lambda: self.node('null-sense', concept='a', kind='LEXICAL_SENSE'))
        self.node('sense-a', concept='a', kind='LEXICAL_SENSE', lexeme='word')
        self.node('sense-b', concept='b', kind='LEXICAL_SENSE', lexeme='word')

    def test_missing_reference_endpoint_is_rejected(self):
        def insert():
            self.connection.execute("""INSERT INTO nabt_inference.lexical_graph_references
                (graph_sha,reference_id,inventory_sha,source_node_id,target_node_id,passage_id,relation_kind,authority)
                VALUES (%s,'missing',%s,NULL,NULL,'passage','DEFINITION_MENTION','REFERENCE_ONLY')""", (self.graph, self.inventory))
        self.rejected(self.psycopg.errors.NotNullViolation, insert)

    def test_empty_rule_cannot_be_sealed_as_an_implicit_fact(self):
        self.rule()
        self.rejected(self.psycopg.errors.RaiseException, lambda: self.seal(rules=1))
        self.premise()
        self.seal(rules=1, premises=1)

    def test_duplicate_rule_body_and_premises_are_rejected(self):
        for rule, first, second in [('r1','a','b'), ('r2','b','a')]:
            self.rule(rule)
            self.premise(first, 0, rule)
            self.premise(second, 1, rule)
        self.rejected(self.psycopg.errors.UniqueViolation, lambda: self.premise('a', 2, 'r1'))
        self.rejected(self.psycopg.errors.RaiseException, lambda: self.seal(rules=2,premises=4))

    def test_polarity_and_blocker_absence_are_explicit(self):
        self.rule()
        self.rejected(self.psycopg.errors.ForeignKeyViolation, lambda: self.premise(positive=False))
        self.rejected(self.psycopg.errors.CheckViolation, lambda: self.premise(role='blocker_absence'))
        self.node('not-a', concept='a', positive=False)
        self.premise('not-a', positive=False, role='blocker_absence')
        self.seal(nodes=4,rules=1,premises=1)

    def test_shape_counts_ordinals_and_post_seal_mutation_fail(self):
        self.rule()
        self.premise(ordinal=1)
        self.rejected(self.psycopg.errors.RaiseException, lambda: self.seal(rules=1,premises=1))
        self.rejected(self.psycopg.errors.RaiseException, lambda: self.seal(nodes=9,rules=1,premises=1))
        self.rejected(self.psycopg.errors.RaiseException, lambda: self.connection.execute('UPDATE nabt_inference.lexical_graph_nodes SET positive=false WHERE graph_sha=%s', (self.graph,)))

    def test_sealed_graph_cannot_gain_rows(self):
        self.seal()
        self.rejected(self.psycopg.errors.RaiseException, lambda: self.node('late', concept='a', positive=False))
        self.rejected(self.psycopg.errors.RaiseException, lambda: self.connection.execute('DELETE FROM nabt_inference.lexical_graph_seals WHERE graph_sha=%s', (self.graph,)))
        # PostgreSQL rejects a referenced table before firing its TRUNCATE
        # trigger. CASCADE reaches the immutability guard without removing rows.
        self.rejected(self.psycopg.errors.FeatureNotSupported,
                      lambda: self.connection.execute('TRUNCATE nabt_inference.lexical_graph_nodes'))
        self.rejected(self.psycopg.errors.RaiseException,
                      lambda: self.connection.execute('TRUNCATE nabt_inference.lexical_graph_nodes CASCADE'))

    def test_non_read_committed_writes_are_rejected_in_temporary_schema(self):
        # The fixture schema above is deliberately uncommitted. Extract the
        # actual trigger bodies into pg_temp in a separate connection, so this
        # test neither publishes that schema nor substitutes a mock guard.
        names = ('lexical_graph_require_unsealed', 'lexical_graph_validate_seal')
        for isolation in ('REPEATABLE READ', 'SERIALIZABLE', 'READ UNCOMMITTED'):
            other = self.psycopg.connect(DSN, autocommit=False)
            try:
                other.execute('SET TRANSACTION ISOLATION LEVEL ' + isolation)
                for index, name in enumerate(names):
                    fixture = 'graph_isolation_fixture_' + str(index)
                    other.execute(f'CREATE TEMP TABLE {fixture} (graph_sha text)')
                    definition = re.search(
                        rf'CREATE FUNCTION nabt_inference\.{name}\(\) RETURNS trigger LANGUAGE plpgsql AS \$\$.*?\n\$\$;',
                        SQL, re.S)
                    self.assertIsNotNone(definition)
                    other.execute(definition.group().replace('CREATE FUNCTION nabt_inference.',
                                                             'CREATE FUNCTION pg_temp.', 1))
                    other.execute(f'CREATE TRIGGER isolation_guard BEFORE INSERT ON {fixture} '
                                  f'FOR EACH ROW EXECUTE FUNCTION pg_temp.{name}()')
                    with self.subTest(isolation=isolation, trigger=name):
                        with self.assertRaises(self.psycopg.errors.RaiseException) as caught:
                            with other.transaction():
                                other.execute(f'INSERT INTO {fixture} VALUES (%s)', (self.graph,))
                        self.assertIn('lexical graph writes require READ COMMITTED', str(caught.exception))
            finally:
                other.rollback()
                other.close()


if __name__ == '__main__':
    unittest.main()
