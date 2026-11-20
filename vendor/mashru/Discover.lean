import MashruProofs
import Lean

open Lean Elab Command

/- Inspect named upstream declarations at their source locations, including audited definitions. -/
run_cmd do
  let env ← getEnv
  for (name, info) in env.constants do
    let some idx := env.getModuleIdxFor? name | continue
    let mod := env.header.moduleNames[idx]!
    unless ["A116", "Aql", "Dal", "Faahis", "Jisr", "Madlul", "Nabt", "Nizam", "SLGE", "tahaqquq"].contains mod.getRoot.toString do
      continue
    let kind := match info with
      | .thmInfo _ => "theorem"
      | .defnInfo _ => "definition"
      | _ => "other"
    if name.isInternal then continue
    let some ranges ← findDeclarationRanges? name | continue
    let row := Json.arr #[toJson name.toString, toJson mod.toString, toJson kind,
      toJson ranges.selectionRange.pos.line, toJson ranges.selectionRange.pos.column,
      toJson ranges.selectionRange.endPos.column]
    IO.println ("MASHRU_DECL " ++ row.compress)
