import MashruProofs
import ProofCatalogExport

open Lean Elab Command

run_cmd do
  let input ← IO.FS.readFile "../../formal/theorems.json"
  let manifest ← match Json.parse input >>= (·.getObjVal? "libraries") >>=
      (·.getObjVal? "mashru") >>= (·.getObjValAs? (Array String) "theorems") with
    | .ok names => pure names
    | .error message => throwError "Invalid transfer manifest: {message}"
  ProofCatalog.writeDeclarations manifest

/- The upstream axiom audit also names definitions. They remain definitions in NABT. -/
run_cmd do
  let input ← IO.FS.readFile "../../formal/theorems.json"
  let names ← match Json.parse input >>= (·.getObjVal? "libraries") >>=
      (·.getObjVal? "mashru") >>= (·.getObjValAs? (Array String) "audited_definitions") with
    | .ok names => pure names
    | .error message => throwError "Invalid definition manifest: {message}"
  let env ← getEnv
  for text in names do
    match env.find? text.toName with
    | some (.defnInfo _) => pure ()
    | _ => throwError "Expected audited definition: {text}"
