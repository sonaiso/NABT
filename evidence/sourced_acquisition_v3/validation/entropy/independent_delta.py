#!/usr/bin/env python3
"""Read audit edge lists only. No NABT imports. Recompute SCCs by mutual reachability."""
import collections
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def measure(vertices, edge_list, expected):
    vertices = sorted(set(vertices))
    edges = {tuple(e) for e in edge_list}
    assert len(edges) == len(edge_list)
    out = {v: set() for v in vertices}
    inc = {v: set() for v in vertices}
    for a, b in edges:
        out[a].add(b)
        inc[b].add(a)
    def reach(start, graph):
        reached = {start}
        todo = [start]
        for v in todo:
            for w in graph[v] - reached:
                reached.add(w)
                todo.append(w)
        return reached
    remaining = set(vertices)
    strong = []
    while remaining:
        v = min(remaining)
        group = reach(v, out) & reach(v, inc)
        strong.append(sorted(group))
        remaining -= group
    undirected = {v: (out[v] | inc[v]) - {v} for v in vertices}
    remaining = set(vertices)
    weak = []
    while remaining:
        group = reach(min(remaining), undirected)
        weak.append(sorted(group))
        remaining -= group
    eu = len({tuple(sorted([a, b])) for a, b in edges if a != b})
    degrees = [len(out[v]) for v in vertices if out[v]]
    e = len(edges)
    h = math.log2(e) - sum(d * math.log2(d) for d in degrees) / e if e else None
    actual = {
        'vertex_count':len(vertices), 'directed_edge_count':e,
        'strong_components': sorted(strong), 'strong_component_count':len(strong),
        'multi_node_strong_components':sorted(c for c in strong if len(c)>1),
        'multi_node_strong_component_count':sum(len(c)>1 for c in strong),
        'cyclic_components':sorted(c for c in strong if len(c)>1 or c[0] in out[c[0]]),
        'weak_components':sorted(weak), 'weak_component_count':len(weak),
        'isolated_vertices':[v for v in vertices if not out[v] and not inc[v]],
        'isolated_vertex_count':sum(not out[v] and not inc[v] for v in vertices),
        'fan_in':{v:len(inc[v]) for v in vertices},
        'fan_out':{v:len(out[v]) for v in vertices},
        'max_in_degree':max(map(len,inc.values()), default=0),
        'max_out_degree':max(map(len,out.values()), default=0),
        'undirected_simple_edge_count':eu,
        'undirected_cycle_rank':eu-len(vertices)+len(weak),
        'self_edge_count':sum(a==b for a,b in edges),
    }
    for k,v in actual.items():
        assert expected[k] == v, (k,expected[k],v)
    if e:
        assert abs(h-expected['outdegree_entropy']['bits']) < 1e-12
    else:
        assert expected['outdegree_entropy']['bits'] is None
    assert expected['outdegree_entropy']['positive_support'] == len(degrees)
    assert expected['outdegree_entropy']['edge_denominator'] == e
    return {
        'all_checked_fields_match':True,
        'vertex_count':len(vertices),'directed_edge_count':e,
        'strong_component_count':len(strong),
        'multi_node_strong_components':actual['multi_node_strong_components'],
        'weak_component_count':len(weak),'isolated_vertex_count':actual['isolated_vertex_count'],
        'undirected_simple_edge_count':eu,'undirected_cycle_rank':eu-len(vertices)+len(weak),
        'positive_outdegree_support':len(degrees),'independent_entropy_bits':h,
        'reported_entropy_bits':expected['outdegree_entropy']['bits'],
        'outdegree_histogram':dict(sorted(collections.Counter(degrees).items())),
        'top_fan_in':sorted(actual['fan_in'].items(),key=lambda x:(-x[1],x[0]))[:10],
        'top_fan_out':sorted(actual['fan_out'].items(),key=lambda x:(-x[1],x[0]))[:10],
    }


import subprocess
BASE = Path('/workspace/scratch/75c40cf673b4/audit-20261028/entropy')
REPO = Path('/workspace/scratch/75c40cf673b4/NABT')
COMMIT = 'eee00163b1151e5cd3aa9adc16a1650ea44ec084'
static_path = HERE/'code-entropy-eee0016.json'
trace_path = HERE/'traceability-eee0016.json'
static = json.loads(static_path.read_text())
trace = json.loads(trace_path.read_text())
base_static = json.loads((BASE/'code-entropy.json').read_text())
base_trace = json.loads((BASE/'traceability.json').read_text())
assert static['provenance']['kind']=='git-tree'
assert static['provenance']['commit']==COMMIT
baseline = base_static['provenance']['commit']
result = {
 'method': 'No NABT imports. Recompute SCCs by mutual forward/reverse reachability; weak components by undirected flood fill; entropy as log2(E)-sum(d*log2(d))/E. Compare every adjacency, component and degree field with measured edge lists.',
 'baseline_commit': baseline, 'current_commit': COMMIT,
 'inputs': {str(p):sha(p) for p in (static_path,trace_path,BASE/'code-entropy.json',BASE/'traceability.json',Path(__file__))},
 'graphs':{}, 'roots':{},
 'interpretation': 'Descriptive dependencies, not Arabic completeness or a code quality score.',
}
scalar_keys = ('vertex_count','directed_edge_count','strong_component_count','weak_component_count','isolated_vertex_count','undirected_simple_edge_count','undirected_cycle_rank','positive_outdegree_support','independent_entropy_bits')
for name,current in static['graphs'].items():
 old = base_static['graphs'][name]
 now_metrics = measure([r['module'] for r in static['inventory']], current['edges'], current)
 old_metrics = measure([r['module'] for r in base_static['inventory']], old['edges'], old)
 result['graphs'][name] = {'current':now_metrics,'baseline':old_metrics,'delta':{k:now_metrics[k]-old_metrics[k] for k in scalar_keys},
  'layer_current':current['layer_edge_counts'], 'layer_delta':{k:v-old['layer_edge_counts'][k] for k,v in current['layer_edge_counts'].items()},
  'added_edges':sorted(set(map(tuple,current['edges']))-set(map(tuple,old['edges']))),
  'removed_edges':sorted(set(map(tuple,old['edges']))-set(map(tuple,current['edges'])))}
for name,current in trace['formal']['projections'].items():
 old = base_trace['formal']['projections'][name]
 now_metrics = measure(current['vertices'],current['edges'],current['metrics'])
 old_metrics = measure(old['vertices'],old['edges'],old['metrics'])
 added = sorted(set(current['vertices'])-set(old['vertices']))
 result['graphs']['advertised_theorem_'+name] = {'current':now_metrics,'baseline':old_metrics,
  'delta':{k:now_metrics[k]-old_metrics[k] for k in scalar_keys if now_metrics[k] is not None and old_metrics[k] is not None},
  'outside_nabt_constants_current':current['outside_nabt_constant_count'],
  'outside_nabt_constants_baseline':old['outside_nabt_constant_count'],
  'added_vertices':added,'new_incident_edges':[edge for edge in current['edges'] if edge[0] in added or edge[1] in added],
  'scope':current['scope']}
for root in ('src/nabt/','tools/','integrations/'):
 current=[r for r in static['inventory'] if r['path'].startswith(root)]
 old=[r for r in base_static['inventory'] if r['path'].startswith(root)]
 counts=lambda rows:{'files':len(rows),'physical_lines':sum(r['physical_lines'] for r in rows),'bytes':sum(r['bytes'] for r in rows)}
 now_counts,old_counts=counts(current),counts(old)
 result['roots'][root]={'current':now_counts,'baseline':old_counts,'delta':{k:now_counts[k]-old_counts[k] for k in now_counts}}
current_inventory={row['path']:row for row in static['inventory']}
old_inventory={row['path']:row for row in base_static['inventory']}
result['added_files']=[current_inventory[path] for path in sorted(set(current_inventory)-set(old_inventory))]
result['changed_files']=[{'path':path,'physical_line_delta':current_inventory[path]['physical_lines']-old_inventory[path]['physical_lines']} for path in sorted(set(current_inventory)&set(old_inventory)) if current_inventory[path]['sha256']!=old_inventory[path]['sha256']]
result['removed_files']=sorted(set(old_inventory)-set(current_inventory))
result['dynamic_import_sites']={'current':len(static['dynamic_import_sites']),'baseline':len(base_static['dynamic_import_sites']),
 'current_call_counts':dict(collections.Counter(r['call'] for r in static['dynamic_import_sites'])),
 'new_module_sites':[r for r in static['dynamic_import_sites'] if r['path'] not in old_inventory]}
result['unresolved_or_external_imports']={'current':len(static['unresolved_or_external_imports']),
 'baseline':len(base_static['unresolved_or_external_imports']),
 'current_classes':dict(collections.Counter(r['kind'] for r in static['unresolved_or_external_imports']))}
result['clone_candidates']={'current':{k:v for k,v in static['clone_candidates'].items() if k!='groups'},
 'baseline':{k:v for k,v in base_static['clone_candidates'].items() if k!='groups'},
 'added_groups':[g for g in static['clone_candidates']['groups'] if g['ast_sha256'] not in {row['ast_sha256'] for row in base_static['clone_candidates']['groups']}],
 'changed_groups':[g for g in static['clone_candidates']['groups'] if g['ast_sha256'] in {row['ast_sha256'] for row in base_static['clone_candidates']['groups']} and g not in base_static['clone_candidates']['groups']]}
result['source_linkage_current']=trace['formal']['source_linkage']
result['source_linkage_baseline']=base_trace['formal']['source_linkage']
result['compiled_counts_current']=trace['formal']['compiled_counts']
result['compiled_counts_baseline']=base_trace['formal']['compiled_counts']
result['boundary']=static['boundary']
result['parser']=static['parser']
result['measurement_source']=static['method']
result['limitations']=static['limitations']
result['traceability_limitation']='Source-matching stored catalogue; no fresh Lean build in this script. Acquisition source replay remains historical v1 (5 files, 23 passages), not v3 source validation.'
# Catalog dependency names are extracted from the immutable committed blob.
catalog_path='evidence/sourced_acquisition_v3/integration/proof_catalog.json'
blob=subprocess.check_output(['git','-C',str(REPO),'show',COMMIT+':'+catalog_path])
assert hashlib.sha256(blob).hexdigest()==trace['formal']['snapshot_sha256']
catalog=json.loads(blob)
old_names=set(base_trace['formal']['projections']['proof_dependencies']['vertices'])
new_rows=[row for row in catalog['theorems'] if row['name'] not in old_names]
new_names={row['name'] for row in new_rows}
result['new_theorem_modules']=dict(collections.Counter(row['module'] for row in new_rows))
result['new_theorem_dependencies']={field:{
 'advertised_new_to_old_edges':sorted({(row['name'],dep) for row in new_rows for dep in row[field] if dep in old_names}),
 'advertised_new_to_new_edges':sorted({(row['name'],dep) for row in new_rows for dep in row[field] if dep in new_names}),
 'outside_advertised_nabt_constants':sorted({dep for row in new_rows for dep in row[field] if dep.startswith('Nabt.') and dep not in old_names|new_names}),
 'outside_advertised_all_constants_count':len({dep for row in new_rows for dep in row[field] if dep not in old_names|new_names})
 } for field in ('proof_dependencies','type_dependencies')}
with (HERE/'independent-delta-eee0016.json').open('x') as stream:
 json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'all_graph_checks_match': True, 'current_commit': COMMIT, 'output': str(HERE/'independent-delta-eee0016.json')}))
