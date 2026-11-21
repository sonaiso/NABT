#!/bin/sh
# Build the exact two owners without installing the vendor into NABT's core.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
build=$(mktemp -d)
trap 'rm -rf "$build"' EXIT
export LEAN_PATH="$build"
mkdir -p "$build/Nabt" "$build/Jisr"
lean --root="$root/formal" -o "$build/Nabt/Cell.olean" "$root/formal/Nabt/Cell.lean"
lean --root="$root/formal" -o "$build/Nabt/Governors.olean" "$root/formal/Nabt/Governors.lean"
lean --root="$root/formal" -o "$build/Nabt/ArabicCoverage.olean" "$root/formal/Nabt/ArabicCoverage.lean"
lean --root="$root/formal" -o "$build/Nabt/RecursiveLicensedAlgebra.olean" "$root/formal/Nabt/RecursiveLicensedAlgebra.lean"
lean --root="$root/vendor/mashru" -o "$build/Jisr/AwamilUslub.olean" "$root/vendor/mashru/Jisr/AwamilUslub.lean"
lean --root="$root/integrations/awamil_profile" -o "$build/GovernorProfile.olean" "$root/integrations/awamil_profile/GovernorProfile.lean"
lean --root="$root/integrations/awamil_profile" "$root/integrations/awamil_profile/SurfaceFragment.lean"
