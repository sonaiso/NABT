"""Hybrid proposal ranking over freshly replayed linguistic-use sources.

Uses the existing BM25/RRF/vector envelope; neither scores nor database text
can install a convention, select a user's sense, or authenticate a world fact.
"""
from collections import Counter

from tools.grammar_catalog.retrieval import SearchIndex, RetrievalError, tokens
from tools.mantuq_inference.retrieval import inventory_sha256
from .inventory import ROOT, build_inventory

INPUT_RECIPE = 'nabt.linguistic-truth.search-projection.v1'


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from nabt import foundation

def iter_documents(inventory):
    for row in inventory['designations']:
        yield 'item', 'designation:'+row['designation_id'], ' '.join([
            row['expression'],row['gloss'],row['convention']]), {'record_kind':'designation',**row}
    for row in inventory['relations']:
        yield 'item', 'relation:'+row['relation_id'], ' '.join([
            row['target_gloss'],row['kind']]), {'record_kind':'relation',**row}
    for row in inventory['passages']:
        yield 'passage', row['passage_id'], row['raw_text'], row


class LinguisticTruthSearchIndex(SearchIndex):
    def __init__(self, *, root=ROOT):
        self._catalog = build_inventory(root)
        self.catalog_sha256 = inventory_sha256(self._catalog)
        self._docs = {}
        for kind, identifier, text, row in iter_documents(self._catalog):
            self._add(kind,identifier,text,row)
        self._tf = {key:Counter(tokens(doc['search_text'])) for key,doc in self._docs.items()}

    def search(self, query, limit=10, hints=None, vector_scores=None, kind=None):
        foundation.require_foundation('tools.linguistic_truth.retrieval.linguistictruthsearchindex.search')
        if vector_scores is not None and (type(vector_scores) is not dict or
                vector_scores.get('input_recipe') != INPUT_RECIPE):
            raise RetrievalError('Linguistic-use embedding recipe mismatch')
        result = super().search(query,limit,hints,vector_scores,kind)
        return {**result,'schema':'nabt.linguistic-truth-retrieval.v1',
                'world_truth_established':False,'source_interpretation_established':False}

    def rehydrate_database(self, proposals):
        foundation.require_foundation('tools.linguistic_truth.retrieval.linguistictruthsearchindex.rehydrate_database')
        if (type(proposals) is not dict or
                proposals.get('schema') != 'nabt.linguistic-truth-database-proposals.v1' or
                proposals.get('inventory_sha') != self.catalog_sha256):
            raise RetrievalError('Linguistic-use database schema/snapshot mismatch')
        result=super().rehydrate_database({'schema':'nabt.database-proposals.v1',
            'snapshot_sha':self.catalog_sha256,'candidates':proposals.get('candidates')})
        return {**result,'schema':'nabt.rehydrated-linguistic-truth-proposals.v1',
                'world_truth_established':False,'source_interpretation_established':False}
