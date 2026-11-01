"""Measure exact-text repetition before introducing any token-output cache."""
from collections import Counter, OrderedDict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
from tools.grammar_catalog.retrieval import SearchIndex

output = Path(__file__).with_name('token_reuse_population_prechange_1535ca8.json')
if output.exists():
    raise SystemExit('Observation exists')
before = hashlib.sha256((ROOT / 'tools/grammar_catalog/retrieval.py').read_bytes()).hexdigest()
index = SearchIndex(root=ROOT)
texts = [record['search_text'] for record in index._docs.values()]
lengths = sorted(map(len, texts))
counts = Counter(texts)
maximum = 4096

def percentile(fraction):
    return lengths[min(len(lengths) - 1, int(fraction * (len(lengths) - 1)))]

simulations = []
for capacity in (512, 1024):
    cache = OrderedDict()
    scans = []
    for iteration in range(3):
        hits = misses = bypassed = 0
        hit_characters = miss_characters = bypassed_characters = 0
        for text in texts:
            if len(text) > maximum:
                bypassed += 1
                bypassed_characters += len(text)
                continue
            if text in cache:
                hits += 1
                hit_characters += len(text)
                cache.move_to_end(text)
            else:
                misses += 1
                miss_characters += len(text)
                cache[text] = None
                if len(cache) > capacity:
                    cache.popitem(last=False)
        scans.append({'scan': iteration + 1, 'hits': hits, 'misses': misses,
                      'bypassed': bypassed, 'hit_fraction_all_documents': hits / len(texts),
                      'hit_characters': hit_characters, 'miss_characters': miss_characters,
                      'bypassed_characters': bypassed_characters,
                      'hit_fraction_all_characters': hit_characters / sum(lengths),
                      'resident_entries': len(cache),
                      'resident_key_codepoints': sum(map(len, cache)),
                      'resident_key_utf8_bytes': sum(len(x.encode('utf-8')) for x in cache)})
    simulations.append({'capacity': capacity, 'maximum_admitted_codepoints': maximum,
                        'scans': scans})

after = hashlib.sha256((ROOT / 'tools/grammar_catalog/retrieval.py').read_bytes()).hexdigest()
assert before == after
record = {'schema': 'nabt.pure-token-reuse-population.v1',
          'observed_utc': datetime.now(timezone.utc).isoformat(),
          'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'retrieval_sha256': before, 'production_unchanged': True,
          'catalog_sha256': index.catalog_sha256, 'documents': len(texts),
          'unique_exact_strings': len(counts), 'codepoints': sum(lengths),
          'utf8_bytes': sum(len(x.encode('utf-8')) for x in texts),
          'length_codepoints': {'min': lengths[0], 'p50': percentile(.5), 'p90': percentile(.9),
                                'p95': percentile(.95), 'p99': percentile(.99), 'max': lengths[-1]},
          'eligible_documents': sum(len(x) <= maximum for x in texts),
          'eligible_unique_strings': sum(len(x) <= maximum for x in counts),
          'simulations': simulations,
          'limits': ['LRU key simulation only, not an implemented token-output cache.',
                     'Exact unnormalized built-in strings in actual document traversal order.',
                     'Documents may repeat source text; counts are not independent evidence sources.',
                     'Codepoint/UTF-8 sizes do not measure total Python heap use.']}
with output.open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(record, ensure_ascii=False, indent=2))
