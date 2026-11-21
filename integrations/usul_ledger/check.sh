#!/bin/sh
set -eu
cd "$(dirname "$0")/../../formal"
lake build verifiedReading
lake env lean ../integrations/usul_ledger/UsulLedger.lean
lake env lean ../integrations/usul_ledger/QualifiedUsul.lean
lake env lean ../integrations/usul_ledger/Lineage.lean
lake env lean ../integrations/usul_ledger/MasdarSlots.lean
