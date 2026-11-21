#!/bin/sh
set -eu
cd "$(dirname "$0")/../../formal"
"${LAKE:-lake}" build verifiedReading Nabt.Derivation
"${LAKE:-lake}" env lean ../integrations/usul_ledger/UsulLedger.lean
"${LAKE:-lake}" env lean ../integrations/usul_ledger/QualifiedUsul.lean
"${LAKE:-lake}" env lean ../integrations/usul_ledger/Lineage.lean
"${LAKE:-lake}" env lean ../integrations/usul_ledger/MasdarSlots.lean
"${LAKE:-lake}" env lean ../integrations/usul_ledger/WeightedReading.lean
