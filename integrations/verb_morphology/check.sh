#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
destination=${1:-artifacts/local/verb-morphology}
mkdir -p "$destination"
destination=$(cd "$destination" && pwd)
export PYTHONPATH="$root/src:$root" LEAN_NUM_THREADS=${LEAN_NUM_THREADS:-1}
cd integrations/verb_morphology
lake build +Nabt.NominalPatterns +Nabt.Bridges +Nabt.Law +A116.Numbering +A116.Ishtiqaq +A116.Alif +A116.Sawabiq +A116.Fractal +A116.QiraaMadlul +A116.Rubai +Archive.AjwafFuul +Archive.LexSamai +Archive.MasdarLazim +Archive.SamaiImperative +Archive.Witnesses
for file in PortCheck FractalBridge LexicalWitness Conjugation; do
    lake env lean "$file.lean"
done
lake env lean --run Export.lean > "$destination/export.json"
lake env lean --run StudyExport.lean > "$destination/studies.json"
cd "$root"
python -m tools.lexical_training.train_verb_contrasts "$destination/export.json" --studies "$destination/studies.json" --check
make io-gateway-build
python -m unittest tests.test_verb_morphology -v
python - "$destination/request.json" <<'PY'
import json, sys
from pathlib import Path
from tools.grammar_catalog.ntp import request
Path(sys.argv[1]).write_text(json.dumps(request("think", {"text":"ما جذر فَقَرَأْتُمُوهَا؟"}), ensure_ascii=False))
PY
python -m tools.ntp run --request "$destination/request.json" --output "$destination/receipt.json"
python -m tools.ntp verify --request "$destination/request.json" --receipt "$destination/receipt.json" --output "$destination/verification.json"
