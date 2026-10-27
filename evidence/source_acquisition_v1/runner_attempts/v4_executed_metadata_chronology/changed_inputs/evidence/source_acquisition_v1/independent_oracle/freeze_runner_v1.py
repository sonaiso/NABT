#!/usr/bin/env python3
"""Freeze additive continuation dependencies; never rewrite the old oracle.

The old material, scorer, first-run journal and corrected postreview are still
read by their original pinned paths. New wrappers only select the new runtime
identity and preserve the existing comparison obligations.
"""
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = ROOT / 'evidence/progressive_rule_audit_v1/independent_oracle/runner_freeze_v1.json'
PREVIOUS_SHA256 = 'e3ddc002acc6b9ac951b9c7c36e1c7d42e936b5854aeed97b6b5848abbb411b5'


def dependency_paths(snapshot):
    raw = PREVIOUS.read_bytes()
    if sha256(raw).hexdigest() != PREVIOUS_SHA256:
        raise ValueError('Historical dependency freeze changed')
    previous = json.loads(raw)
    prefix = 'evidence/progressive_rule_audit_v1/independent_oracle/'
    destination = 'evidence/source_acquisition_v1/independent_oracle/'
    selected = {destination + row['path'].removeprefix(prefix)
                if row['path'].startswith(prefix) else row['path']
                for row in previous['files']}
    selected.remove('evidence/progressive_rule_audit_v1/regression_policy_v1.json')
    selected.update({
        'evidence/source_acquisition_v1/regression_policy_v1.json',
        'evidence/source_acquisition_v1/build_runtime_freeze.py',
        'tests/test_source_acquisition_runtime_freeze.py',
        'tests/test_progressive_rule_runtime_freeze.py',
        'evidence/progressive_rule_audit_v1/code_freeze_v1.json',
        'evidence/progressive_rule_audit_v1/code_freeze_v1.tar.gz',
        'evidence/progressive_rule_audit_v1/regression_policy_v1.json',
        'tools/text_evaluation/integrity.py',
        'evidence/certified_natural_use_v1/code_freeze_v1.json',
        'evidence/certified_natural_use_v1/code_freeze_v1.tar.gz',
        'evidence/certified_natural_use_v1/regression_policy_v1.json',
        'evidence/progressive_rule_audit_v1/independent_oracle/runner_freeze_v1.json',
    })
    # Retain the source-acquisition implementation separately from the unchanged
    # packaged runtime. These retain exact code and independently authored input identities.
    selected.update({
        'evidence/source_acquisition_v1/build_catalog_references.py',
        'evidence/source_acquisition_v1/pack_verification.py',
        'tests/test_verification_byte_bundle.py',
        'tools/attested_lexical_loader.py',
        'tools/benchmark_linguistic_truth.py',
        'tools/measure_natural_use.py',
        'tests/test_natural_use_measurement.py',
        'tools/benchmark_certified_natural_use.py',
        'tests/test_linguistic_truth_benchmark.py',
        'tests/test_benchmark_module_provenance.py',
        'tests/test_linguistic_truth_foundation.py',
        'tests/test_lexical_surface_binding.py',
        'evidence/certified_natural_use_v1/independent_cases.json',
        'evidence/certified_natural_use_v1/projection_controls.json',
        'evidence/qualified_cue_licensing_v1/independent_cases.json',
        'evidence/qualified_cue_licensing_v1/independent_cases.sha256',
        'evidence/qualified_cue_licensing_v1/source_review.json',
        'formal/lake-manifest.json',
        'tools/benchmark_qualified_cues.py',
        'tools/grammar_catalog/routing.py',
        'tools/grammar_catalog/__main__.py',
        'evidence/lexical_surface_binding_v1/source_ledger.json',
        'evidence/attested_mark_recovery_v1/source_review.json',
        'tests/test_lexical_source_acquisition.py',
        'tests/test_qualified_cue_licensing.py',
        'tests/test_qualified_cue_benchmark.py',
        'tests/test_grammar_native_authority.py',
        'formal/lean-toolchain',
        'formal/theorems.json',
        '.github/workflows/lexical-completion.yml',
        '.github/workflows/grammar-catalog-database.yml',
        'integrations/grammar_catalog.mk',
        'integrations/mantuq_inference.mk',
        'integrations/linguistic_truth.mk',
        'integrations/licensed_inference.mk',
        'tests/test_proof_catalog.py',
    })
    for review_name in ('evidence/attested_mark_recovery_v1/source_review.json',
                        'evidence/qualified_cue_licensing_v1/source_review.json'):
        review = json.loads((ROOT / review_name).read_bytes())
        for source in review['sources']:
            path = ROOT / source['path']
            if not path.resolve().is_relative_to(ROOT):
                raise ValueError('Reviewed source escapes the repository')
            selected.add(source['path'])
    selected.update('evidence/source_acquisition_v1/catalog_references/' + name
                    for name in ('proof_catalog.json', 'grammar_link_summary.json',
                                 'mantuq_proof_links.json', 'linguistic_proof_links.json',
                                 'licensed_proof_links.json', 'catalog_migration.json'))
    selected.update(str(path.relative_to(ROOT))
                    for path in (ROOT / 'tools/linguistic_truth').glob('*.py'))
    selected.update(str(path.relative_to(ROOT))
                    for path in (ROOT / 'formal').rglob('*.lean')
                    if '.lake' not in path.parts)
    return selected


def main():
    output = HERE / 'runner_freeze_v4.json'
    if output.exists():
        raise ValueError('Never overwrite an observed dependency freeze')
    spec = importlib.util.spec_from_file_location('source_acquisition_oracle_runner', HERE / 'run_oracle_v1.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runtime = ROOT / 'evidence/source_acquisition_v1/code_freeze_v1.json'
    snapshot = runner.E.runtime_snapshot(runtime, ROOT)
    old = json.loads(PREVIOUS.read_bytes())
    rows = [runner.file_row(ROOT / name) for name in sorted(dependency_paths(snapshot))]
    frozen = {key: value for key, value in old.items()
              if key not in ('schema', 'created_utc', 'runtime_freeze_sha256', 'files',
                             'upstream_hardening_commit', 'supersedes_pre_execution_dependency_freeze_sha256',
                             'supersedes_executed_dependency_freeze_sha256')}
    frozen.update(schema='nabt.source-acquisition.directed-runner-freeze.v1',
                  created_utc=datetime.now(timezone.utc).isoformat(),
                  runtime_freeze_sha256=sha256(runtime.read_bytes()).hexdigest(),
                  previous_dependency_freeze_sha256=PREVIOUS_SHA256, files=rows,
                  supersedes_executed_dependency_freeze_sha256='453fc9d7e0cf846a1c7c8bd6c57580937d32bd71c979ac2fac0c77c4d56deb96',
                  review_correction='Versioned additive runtime and exact dependency identities; all historical material, scorers, denominators and residual signatures remain unchanged. Native source acquisition, qualified cue licensing and routing are evaluated separately.',
                  runtime_calls_performed_by_freezer=False,
                  historical_files_repinned=False,
                  scope='Same 24 authored cases, 29 questions and separate six source counterexamples; historical evidence is read-only.')
    with output.open('x', encoding='utf-8') as stream:
        json.dump(frozen, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'runner_freeze': str(output.relative_to(ROOT)),
                      'sha256': sha256(output.read_bytes()).hexdigest(),
                      'files': len(rows), 'runtime_calls_performed': False}))


if __name__ == '__main__':
    main()
