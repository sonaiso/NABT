"""Read-only actual dependency check plus isolated deterministic scheduler witness."""
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

ROOT = Path('/workspace/scratch/75c40cf673b4/NABT')
HERE = Path(__file__).resolve().parent
run = subprocess.run(['make', '-qp', '-f', 'tools/sourced_acquisition_v3.mk'], cwd=ROOT,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
if run.returncode not in (0, 1):
    raise RuntimeError(run.stderr)
graph = {}
for line in run.stdout.splitlines():
    match = re.fullmatch(r'([^\s:#=]+):(?:\s+(.*))?', line)
    if match:
        graph.setdefault(match[1], set()).update((match[2] or '').replace('|', ' ').split())
def reachable(target):
    seen, pending = set(), [target]
    while pending:
        current = pending.pop()
        for child in graph.get(current, ()):
            if child not in seen:
                seen.add(child); pending.append(child)
    return seen
assert 'article-acquisition-evaluation' in graph['sourced-acquisition-native']
assert 'linguistic-truth' not in reachable('sourced-acquisition-evaluation')
assert {'sourced-acquisition-evaluation', 'linguistic-truth'} <= graph['check']
assert 'formal' in graph['linguistic-truth']
worker = r'''
from pathlib import Path
import json, sys, time
role = sys.argv[1]
if role == 'linguistic':
    Path('native.active').write_text('rebuild')
    Path('native.started').write_text('started')
    end = time.monotonic() + 0.5
    while time.monotonic() < end and not Path('freeze.json').exists():
        time.sleep(0.005)
    Path('native.active').unlink()
elif role == 'native':
    end = time.monotonic() + 3
    while not Path('native.started').exists():
        if time.monotonic() >= end: raise RuntimeError('parallel branch never started')
        time.sleep(0.005)
elif role == 'freeze':
    Path('freeze.json').write_text(json.dumps({'other_native_rebuild_active':Path('native.active').exists()}))
'''
observations = {}
for fixed in (False, True):
    with tempfile.TemporaryDirectory(prefix='nabt-v3-make-review-') as directory:
        temp = Path(directory)
        (temp/'worker.py').write_text(worker)
        call = shlex.quote(sys.executable) + ' worker.py '
        # Contract each unrelated branch to formal/article readiness, preserving
        # the actual unordered competing measured-native branch and v3 sequence.
        makefile = '.PHONY: check formal article-acquisition-evaluation sourced-acquisition-native sourced-acquisition-conformance sourced-acquisition-evaluation linguistic-truth\n'
        makefile += 'check: sourced-acquisition-evaluation linguistic-truth\n'
        makefile += 'formal:\n\t@:\narticle-acquisition-evaluation: formal\n\t@:\n'
        makefile += 'linguistic-truth: formal\n\t@' + call + 'linguistic\n'
        makefile += 'sourced-acquisition-native: article-acquisition-evaluation' + (' linguistic-truth' if fixed else '') + '\n\t@' + call + 'native\n'
        makefile += 'sourced-acquisition-conformance: sourced-acquisition-native\n\t@:\n'
        makefile += 'sourced-acquisition-evaluation: sourced-acquisition-conformance\n\t@' + call + 'freeze\n'
        (temp/'Makefile').write_text(makefile)
        subprocess.run(['make', '-j2', 'check'], cwd=temp, check=True, capture_output=True)
        observation = json.loads((temp/'freeze.json').read_text())
        assert observation['other_native_rebuild_active'] is (not fixed), observation
        observations['with_prerequisite' if fixed else 'current_graph'] = observation
result = {
    'commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'scope':'Actual make -qp reachability plus isolated minimal scheduling witness; no real repository recipe or native binary executed.',
    'actual_prerequisites':{key:sorted(graph[key]) for key in ('sourced-acquisition-native','sourced-acquisition-conformance','sourced-acquisition-evaluation','linguistic-truth')},
    'linguistic_gate_precedes_v3_freeze':False,
    'observations':observations,
    'inputs':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('tools/sourced_acquisition_v3.mk','integrations/linguistic_truth.mk','tools/check_linguistic_truth.py')},
    'suggested_change':'sourced-acquisition-native: article-acquisition-evaluation linguistic-truth',
    'impact':'A separately scheduled measured-native rebuild can overlap the v3 freeze/evaluation under make -j check. This is an ordering/reproducibility defect; snapshot checks fail closed when changed bytes persist.'
}
with (HERE/'build-order-proof.json').open('x') as stream:
    json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result,indent=2))
