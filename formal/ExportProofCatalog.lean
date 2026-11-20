import Nabt
import ProofCatalogExport

open Lean Elab Command

run_cmd do
  let input ← IO.FS.readFile "theorems.json"
  let manifest ← match Json.parse input >>= (·.getObjValAs? (Array String) "theorems") with
    | .ok names => pure names
    | .error message => throwError "Invalid theorem manifest: {message}"
  ProofCatalog.writeDeclarations manifest
