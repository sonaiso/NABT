"""Package one independently verified run with the sources needed to replay in its checkout."""
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

directory = Path(sys.argv[1]).resolve()
root = Path(__file__).resolve().parents[2]
verification = json.loads((directory / "verification.json").read_bytes())
if verification.get("valid") is not True:
    raise ValueError("Successful NTP verification is required")
paths = ("vendor/alghanem-a116", "integrations/verb_morphology", "tests/test_verb_morphology.py",
         "tools/lexical_training", "tools/grammar_catalog/text_reading.py", "tools/grammar_catalog/gateway.py",
         "evidence/ntl_pattern_learning_v1", "evidence/verb_morphology_v1", "docs/VERB_MORPHOLOGY_AR.md")
changes = subprocess.check_output(["git", "status", "--porcelain", "--", *paths], cwd=root)
if changes:
    raise ValueError("Commit the production inputs before packaging a replay")
tracked = subprocess.check_output(["git", "ls-files", "-z", "--", *paths], cwd=root).decode().split("\0")
commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
with ZipFile(directory / "NABT_Verb_Morphology.zip", "w", ZIP_DEFLATED) as archive:
    archive.writestr("COMMIT.txt", commit + "\n")
    for name in filter(None, tracked):
        archive.write(root / name, name)
    for name in ("export.json", "studies.json", "request.json", "receipt.json", "verification.json"):
        archive.write(directory / name, "replay/" + name)
