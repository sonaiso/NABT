import Nabt
import Lean

/-!
Inspection tool, not a new source of proof authority. It reads actual compiled
theorem declarations. The statement encoding erases binder names/metadata and
renames universe parameters by their declared position; it does not unfold
definitions, decide semantic equivalence, or identify Arabic rules.
-/
open Lean Elab Command

namespace ProofCatalog

def node (tag : String) (children : List Json := []) : Json :=
  toJson (toJson tag :: children)

def nameJson : Name → Json
  | .anonymous => node "anonymous"
  | .str parent value => node "str" [nameJson parent, toJson value]
  | .num parent value => node "num" [nameJson parent, toJson value]

def levelJson (params : List Name) : Level → Except String Json
  | .zero => pure (node "zero")
  | .succ level => return node "succ" [← levelJson params level]
  | .max left right => return node "max" [← levelJson params left, ← levelJson params right]
  | .imax left right => return node "imax" [← levelJson params left, ← levelJson params right]
  | .param name =>
    if name ∈ params then pure (node "param" [toJson (params.idxOf name)])
    else .error s!"unbound universe parameter {name}"
  | .mvar _ => .error "unresolved universe metavariable"

def binderJson (info : BinderInfo) : Json := toJson (reprStr info)

def exprJson (params : List Name) : Expr → Except String Json
  | .bvar index => pure (node "bvar" [toJson index])
  | .fvar _ => .error "free variable in a closed declaration"
  | .mvar _ => .error "metavariable in a compiled declaration"
  | .sort level => return node "sort" [← levelJson params level]
  | .const name levels => return node "const" [nameJson name,
      toJson (← levels.mapM (levelJson params))]
  | .app function argument => return node "app" [← exprJson params function, ← exprJson params argument]
  | .lam _ domain body info => return node "lam" [binderJson info, ← exprJson params domain, ← exprJson params body]
  | .forallE _ domain body info => return node "forall" [binderJson info, ← exprJson params domain, ← exprJson params body]
  | .letE _ type value body nondep => return node "let" [toJson nondep, ← exprJson params type, ← exprJson params value, ← exprJson params body]
  | .lit (.natVal value) => pure (node "nat" [toJson value])
  | .lit (.strVal value) => pure (node "string" [toJson value])
  | .mdata _ body => exprJson params body
  | .proj typeName index body => return node "proj" [nameJson typeName, toJson index, ← exprJson params body]

def rangesJson : Option DeclarationRanges → Json
  | none => Json.null
  | some ranges => Json.mkObj [
      ("line", toJson ranges.range.pos.line),
      ("column", toJson ranges.range.pos.column),
      ("end_line", toJson ranges.range.endPos.line),
      ("end_column", toJson ranges.range.endPos.column)]

end ProofCatalog

run_cmd do
  let env ← getEnv
  let input ← IO.FS.readFile "theorems.json"
  let manifest ← match Json.parse input >>= (·.getObjValAs? (Array String) "theorems") with
    | .ok names => pure names
    | .error message => throwError "Invalid theorem manifest: {message}"
  unless manifest.toList.eraseDups.length = manifest.size do
    throwError "Duplicate manifest identifier"
  for text in manifest do
    let name := text.toName
    let info ← match env.find? name with
      | some (.thmInfo info) => pure info
      | _ => throwError "Manifest entry is not a compiled theorem: {name}"
    let statement ← match ProofCatalog.exprJson info.levelParams info.type with
      | .ok value => pure value
      | .error message => throwError "Cannot encode theorem {name}: {message}"
    let module := match env.getModuleIdxFor? name with
      | some index => env.header.moduleNames[index]!.toString
      | none => env.mainModule.toString
    let row := Json.mkObj [
      ("name", toJson text), ("module", toJson module),
      ("universe_parameters", toJson info.levelParams.length),
      ("statement_ast", statement),
      ("proof_dependencies", toJson (info.value.getUsedConstants.map Name.toString)),
      ("type_dependencies", toJson (info.type.getUsedConstants.map Name.toString)),
      ("axioms", toJson ((← collectAxioms name).map Name.toString)),
      ("range", ProofCatalog.rangesJson (← findDeclarationRanges? name))]
    IO.println ("NABT_PROOF " ++ row.compress)
  IO.println s!"NABT_PROOF_COUNT {manifest.size}"
