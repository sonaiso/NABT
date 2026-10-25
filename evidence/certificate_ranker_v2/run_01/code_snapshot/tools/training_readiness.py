#!/usr/bin/env python3
"""Offline, read-only intake audit. Repository metadata is not training authority."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil

ROOT = Path(__file__).resolve().parents[1]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def machine():
    def read(path):
        p = Path(path)
        return p.read_text().strip() if p.is_file() else None
    cpu = read('/sys/fs/cgroup/cpu.max')
    memory = read('/sys/fs/cgroup/memory.max')
    quota = None
    if cpu and cpu.split()[0] != 'max':
        n, d = map(int, cpu.split())
        quota = n / d
    return {
        'python': platform.python_version(), 'architecture': platform.machine(),
        'logical_cpus': os.cpu_count(), 'cpu_max_raw': cpu, 'cpu_quota_cores': quota,
        'memory_max_raw': memory,
        'memory_quota_bytes': int(memory) if memory and memory.isdigit() else None,
        'nvidia_smi_exposed': shutil.which('nvidia-smi') is not None,
        'nvidia_devices_exposed': [str(p) for p in Path('/dev').glob('nvidia*')],
        'packages': {p: importlib.util.find_spec(p) is not None for p in
                     ('torch', 'transformers', 'peft', 'trl', 'datasets', 'safetensors')},
        'gpu_training_measurement': None, 'remote_gpu_availability': 'UNMEASURED',
    }


def components(rows, axes):
    """Transitive leakage groups; unknown axis metadata makes the split unauditable.

    A shared source/root/template connects *all* descendants, not just adjacent
    rows. This audit does not silently infer Arabic roots from surface strings.
    """
    ids = [r['id'] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate example identity')
    if any(not r.get(axis) for r in rows for axis in axes):
        return {'status': 'UNMEASURED', 'groups': None, 'missing_axes':
                sorted({a for r in rows for a in axes if not r.get(a)})}
    parent = list(range(len(rows)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    seen = {}
    for i, row in enumerate(rows):
        for axis in axes:
            values = row[axis]
            if type(values) is not list or any(type(v) is not str or not v for v in values):
                raise ValueError('group identifiers must be nonempty string lists')
            for value in values:
                key = (axis, value)
                if key in seen:
                    parent[find(i)] = find(seen[key])
                else:
                    seen[key] = i
    groups = {}
    for i, identity in enumerate(ids):
        groups.setdefault(find(i), []).append(identity)
    groups = sorted(sorted(g) for g in groups.values())
    return {'status': 'MEASURED', 'groups': groups,
            'three_way_split_possible': len(groups) >= 3,
            'note': 'Three groups are necessary, not sufficient, for balanced train/dev/test.'}


def intake():
    """Queue existing public regression cases for review, never promote to gold."""
    path = ROOT / 'evidence/arabic_coverage/holdout_v2/cases.json'
    raw = path.read_bytes()
    cases = json.loads(raw)['cases']
    categories = {'positive': 'positive', 'ambiguity': 'alternative_readings',
                  'boundary': 'near_negative', 'force_boundary': 'near_negative',
                  'coverage_challenge': 'coverage_gap'}
    rows = []
    for case in cases:
        rows.append({
            'id': case['id'], 'category': categories[case['category']],
            'original_category': case['category'], 'focus': case['focus'],
            'source_path': str(path.relative_to(ROOT)), 'source_file_sha256': digest(raw),
            'text_utf8_sha256': digest(case['text'].encode('utf-8')),
            'required_rules': case.get('source_rules', []),
            'question_count': len(case.get('questions', [])),
            'source_groups': [str(path.relative_to(ROOT))],
            'root_groups': [], 'template_groups': [],
            'split': 'public_development_regression', 'hidden': False,
            'training_eligible': False,
            'obligations': ['independent reading-set review', 'root and template annotation',
                            'per-item evidence and data-use review',
                            'separate linguistic adequacy from checker acceptance'],
            'world_truth_established': False,
        })
    return {'schema': 'nabt.training-intake.v1', 'rows': rows,
            'counts': dict(sorted(Counter(r['category'] for r in rows).items())),
            'eligible_arabic_sft_examples': 0,
            'joint_source_root_template_split': components(
                rows, ['source_groups', 'root_groups', 'template_groups']),
            'source_only_split': components(rows, ['source_groups']),
            'note': 'Prior published holdout has been used for repair; it stays development. '
                    'Coverage gaps are obligations, not negative language labels.'}
