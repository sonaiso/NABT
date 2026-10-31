# Authored interpretation-link examples

These small QAC-shaped records and lexical descriptions are authored contract
premises. They are not quotations from the Quranic Arabic Corpus, independently
held-out language observations, or evidence that an assertion is true outside
the supplied source. The context explicitly names two individuals.

The descriptive source supplies two separately named readings: a genus reading
of `رَجُلٌ` and a quality-bearer reading of `كَاتِبٌ`. The QAC-shaped source
independently annotates the latter as `ACT|PCPL`. Exact spelling does not prove
that the descriptive and corpus readings denote the same sense. The resulting
answer therefore exposes conditional descriptive alternatives and the missing
sense correspondence, alongside the selected predicate's own source tags.

Run the existing CLI from the repository root:

```sh
PYTHONPATH=src python -m nabt.cli ask-discourse examples/interpretive_links_source.txt 'هل سَالِمٌ كَاتِبٌ؟' --qac examples/interpretive_links_training.tsv --context examples/interpretive_links_context.json --lexical-source examples/interpretive_links_lexical.txt
```

`verify-discourse-answer` requires the same original source, question, training,
context and descriptions explicitly. Omitting or changing the descriptions
invalidates an answer created with them. Reading or answering without the
descriptions is still allowed; the nominal denotation then remains unknown.
