from pathlib import Path
import subprocess, re, json, hashlib, datetime

root = Path('/workspace/scratch/975bcbd04428')
compiler = Path('/tmp/nabt-tools/lean-4.34.1-linux/bin/lean')
source = root / 'proof/RecursiveLicensedAlgebra.lean'
code = source.read_text()
names = re.findall(r'^theorem ([A-Za-z0-9_]+)', code, re.M)
check = root / 'analysis/RecursiveLicensedAlgebraCheck.lean'
check.write_text(code + '\n' + '\n'.join(
    '#print axioms RecursiveLicensedAlgebra.' + name for name in names) + '\n')
version = subprocess.run([str(compiler), '--version'], text=True, capture_output=True, check=True).stdout.strip()
result = subprocess.run([str(compiler), str(check)], text=True, capture_output=True)
log = result.stdout + result.stderr
(root / 'analysis/recursive_algebra_lean_check.log').write_text(log)
metadata = {
    'source': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'compiler': str(compiler), 'version': version, 'exit_code': result.returncode,
    'theorem_count': len(names), 'theorems': names,
    'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'forbidden_proof_commands': re.findall(r'^\s*(?:sorry|admit|axiom|unsafe)\b|\bnative_decide\b', code, re.M),
    'scope': 'Independent Std-only conditional algebra; no imported Arabic grammar or source-evidence interpreter.',
    'registry_scope': 'Structural n is relative to one fixed grammar registry/version; source occurrence IDs are separate.',
    'upstream_builds_rerun': False
}
(root / 'analysis/recursive_algebra_proof.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k:metadata[k] for k in ['version','exit_code','theorem_count','sha256','forbidden_proof_commands']},ensure_ascii=False))
if result.returncode:
    print(log)
raise SystemExit(result.returncode)
