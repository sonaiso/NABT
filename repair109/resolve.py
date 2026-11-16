"""Reconcile pinned PR109 with main and repair independently reproduced syntax/input defects."""
from pathlib import Path
import ast, hashlib, subprocess, sys
MAIN='aa2dba34332b19d9dd25d88f485986d0e93120fa'
HEAD='9720ef1bf4425afa317c2f49f5d936ba165082d9'
def git(*args): return subprocess.check_output(['git',*args])
assert git('rev-parse','HEAD').decode().strip()==HEAD
subprocess.run(['git','merge','--no-commit','--no-ff',MAIN],check=True)
p=Path('tools/grammar_catalog/relational.py');s=p.read_text()
start=s.index('def validate(request):\n');end=s.index('        raise ValueError',start)
assert '"report_model"' in s[start:end] and s[start:end].count('}:')==2
s=s[:start]+'''def validate(request):
    allowed = {"text", "source_id", "query", "limit", "lexical_text", "context", "temporal",
               "inference", "bridge", "neural_continuity", "root_sense", "question",
               "question_chain", "genus_chains", "valency_context", "report_model",
               "licensed_speech"}
    if type(request) is not dict or "text" not in request or set(request) - allowed:
'''+s[end:]
p.write_text(s)
p=Path('tools/grammar_catalog/gateway_routes.py');s=p.read_text()
old='"question_chain", "valency_context", "report_model", "licensed_speech")),'
assert s.count(old)==1
s=s.replace(old,'"question_chain", "genus_chains", "valency_context", "report_model", "licensed_speech")),')
p.write_text(s)
p=Path('integrations/io_gateway.mk');s=p.read_text()+'''
.PHONY: scoped-report-native
# Exercise these integrations with the original gateway/checker prerequisites.
scoped-report-native: io-gateway-build
\tPYTHONPATH=src:. NABT_REQUIRE_IO_GATEWAY_NATIVE=1 $(PYTHON) -B -m unittest tests.test_io_gateway tests.test_relational_input_regression tests.post_segmentation_routing.test_ayat_al_dayn_routing tests.post_segmentation_routing.test_ayat_cognition tests.post_segmentation_routing.test_report_rank -v

check io-gateway-native: scoped-report-native
'''
p.write_text(s)
Path('tests/test_relational_input_regression.py').write_bytes(Path(sys.argv[1]).read_bytes())
expected={'tools/grammar_catalog/relational.py':'fce05874a3fd056df9b5e98214e80ebbb6fa5ef9','tools/grammar_catalog/gateway_routes.py':'3f8e79c84cd4b9f61cfb04e7accb5da59614073b','integrations/io_gateway.mk':'ec652d19511753f45f7d9781cc1f5305a59debb7','tests/test_relational_input_regression.py':'8e2c0024478881839fa861600d519e94bb854276'}
for path,sha in expected.items():
 raw=Path(path).read_bytes();actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 assert actual==sha,(path,actual,sha)
 subprocess.run(['git','add','--',path],check=True)
for base in ('src','tools','tests'):
 for file in Path(base).rglob('*.py'):ast.parse(file.read_bytes())
assert not git('diff','--name-only','--diff-filter=U').strip()
subprocess.run(['git','diff','--cached','--check'],check=True)
print(expected)
