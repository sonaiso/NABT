"""Pinned merge repair; no main writes, no skipped release checks."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

MAIN = 'aa2dba34332b19d9dd25d88f485986d0e93120fa'
HEAD = '009339e5d3c4d1e3c3b31aba9c256fd94032984c'

def git(*args):
    return subprocess.check_output(['git', *args])

assert git('rev-parse', 'HEAD').decode().strip() == HEAD
p = subprocess.run(['git', 'merge', '--no-commit', '--no-ff', MAIN])
assert p.returncode in (0, 1)
conflicts = set(git('diff', '--name-only', '--diff-filter=U').decode().splitlines())
assert conflicts <= {'tools/lexical_training/teaching.py'}, conflicts
path = Path('tools/lexical_training/teaching.py')
s = git('show', MAIN + ':' + str(path)).decode()
assert s.count('ntl_curriculum, school_apprentice\n') == 1
assert s.count('ifadah_programs, school_apprentice):') == 1
s = s.replace('ntl_curriculum, school_apprentice\n', 'ntl_curriculum, school_apprentice, ntl_witness_pilot\n', 1)
s = s.replace('ifadah_programs, school_apprentice):', 'ifadah_programs, school_apprentice, ntl_witness_pilot):', 1)
s = s.replace('from . import school_apprentice\n        shared', 'from . import school_apprentice, ntl_witness_pilot\n        shared', 1)
s = s.replace('SCHEMA_V4, school_apprentice.SCHEMA)', 'SCHEMA_V4, school_apprentice.SCHEMA, ntl_witness_pilot.SCHEMA)', 1)
path.write_text(s, encoding='utf-8')
path = Path('integrations/io_gateway.mk')
s = git('show', MAIN + ':' + str(path)).decode()
s = s.replace('tests.test_ntl_curriculum tests.test_ntl_course', 'tests.test_lesson_dispatch_regression tests.test_ntl_witness_pilot tests.test_ntl_curriculum tests.test_ntl_course')
path.write_text(s, encoding='utf-8')
Path('tests/test_lesson_dispatch_regression.py').write_bytes(Path(sys.argv[1]).read_bytes())
expected = {
 'tools/lexical_training/teaching.py': '11d1ee2aad3c39f18948d47ff392ae1bdb3ff2e6',
 'integrations/io_gateway.mk': '048069b53b9b9ab4c2b3e5136f1b572330208c3c',
 'tools/entropy_framework/registry.json': '5291f8255ed2bb0ca9ca1d611ea5126e938d1193',
 'tests/test_lesson_dispatch_regression.py': 'e2c0edc618b376a8ff599d3df13ba0a947319b14',
}
for name, sha in expected.items():
    raw = Path(name).read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    assert actual == sha, (name, actual, sha)
    subprocess.run(['git', 'add', '--', name], check=True)
assert not git('diff', '--name-only', '--diff-filter=U').strip()
subprocess.run(['git', 'diff', '--cached', '--check'], check=True)
print(json.dumps({'main':MAIN,'head':HEAD,'verified_blobs':expected}, indent=2))
