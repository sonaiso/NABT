import Nabt.LexicalGraph
import ProbeJson

open Lean ProbeJson Nabt Nabt.SemanticInference Nabt.VerifiedReading Nabt.LexicalGraph
namespace LexicalGraphMain

def exactFields (j : Json) (names : List String) : ProbeM Unit := do
  let obj ← liftParse j.getObj?
  if obj.size != names.length || names.any (fun n => (obj.get? n).isNone) then
    invalid "unexpected or missing field"
  else pure ()

def text (j : Json) (limit : Nat := 128) : ProbeM String := do
  let s ← str j
  if s.isEmpty || s.toList.all Char.isWhitespace || s.toList.any (fun c => c.toNat < 32) then
    return ← invalid "empty or control-bearing identity"
  if s.utf8ByteSize > limit then return ← limited "text byte limit"
  return s

def boundedItems (parse : Json → ProbeM α) (limit : Nat) (j : Json) : ProbeM (List α) := do
  let xs ← liftParse j.getArr?
  if xs.size > limit then return ← limited "array limit"
  return ← xs.toList.mapM parse

def distinct (xs : List String) : ProbeM Unit := do
  if xs.eraseDups.length != xs.length then invalid "duplicate identity" else pure ()

def parseNode (j : Json) : ProbeM Node := do
  exactFields j ["id", "sense_id", "component", "scope"]
  return ⟨← text (← field j "id"), ← text (← field j "sense_id"),
    ← text (← field j "component") 4096, ← text (← field j "scope")⟩

def parseDimension (j : Json) : ProbeM Dimension := do
  match ← str j with
  | "mutabaqa" => return .matching
  | "tadammun" => return .inclusion
  | "iltizam" => return .mental
  | "definition_reference" => return .definitionReference
  | "opposition_reference" => return .oppositionReference
  | _ => invalid "unknown dimension"

def nodeById (nodes : List Node) (id : String) : ProbeM Node :=
  match nodes.find? (fun n => n.id == id) with
  | some n => pure n
  | none => invalid "unknown node reference"

def parseEdge (nodes : List Node) (j : Json) : ProbeM Edge := do
  exactFields j ["id", "source", "dimension", "body", "head"]
  let id ← text (← field j "id")
  let source ← text (← field j "source")
  let dimension ← parseDimension (← field j "dimension")
  let bodyIds ← boundedItems (fun j => text j) 32 (← field j "body")
  if bodyIds.isEmpty then return ← invalid "a rule needs a nonempty body"
  distinct bodyIds
  let body ← bodyIds.mapM (nodeById nodes)
  let head ← nodeById nodes (← text (← field j "head"))
  return ⟨id, source, dimension, body, head⟩

def inactiveReason (activeSources : List String) (e : Edge) : Option String :=
  if !e.dimension.inferential then some "REFERENCE_ONLY"
  else if !activeSources.contains e.source then some "INACTIVE_SOURCE"
  else if e.body.any (fun n => n.scope != e.head.scope) then some "SCOPE_MISMATCH"
  else if e.body.any (fun n => n.senseId != e.head.senseId) then some "SENSE_MISMATCH"
  else none

def seedSource (n : Node) : SemanticInference.Source :=
  ⟨"EXPLICIT_SEED_ASSUMPTION", LexicalGraph.lawId, n.scope⟩

def makeProgram (seeds : List Node) (activeSources : List String) (edges : List Edge) : GroundProgram :=
  let rules := edges.filterMap (Edge.lower activeSources)
  {sources := (rules.map Rule.source ++ seeds.map seedSource).eraseDups,
   facts := seeds.map (fun n => ⟨seedSource n, n.atom⟩), rules := rules}

def table : Json := Json.mkObj [
  ("law_id", toJson LexicalGraph.lawId),
  ("scope", toJson "FINITE_SOURCE_RELATIVE_SAME_SENSE_HORN_GRAPH"),
  ("dimensions", toJson (["mutabaqa", "tadammun", "iltizam", "definition_reference", "opposition_reference"] : List String)),
  ("limits", Json.mkObj [("nodes",toJson (256 : Nat)), ("rules",toJson (512 : Nat)),
    ("seeds",toJson (256 : Nat)), ("body",toJson (32 : Nat)), ("active_sources",toJson (512 : Nat)),
    ("budget",toJson (512 : Nat)), ("identity_bytes",toJson (128 : Nat)), ("component_bytes",toJson (4096 : Nat))])]

def dispatch (j : Json) : ProbeM Json := do
  exactFields j ["nodes", "rules", "seeds", "active_sources", "budget"]
  let nodes ← boundedItems parseNode 256 (← field j "nodes")
  distinct (nodes.map Node.id)
  let edges ← boundedItems (parseEdge nodes) 512 (← field j "rules")
  distinct (edges.map Edge.id)
  let seedIds ← boundedItems (fun j => text j) 256 (← field j "seeds")
  distinct seedIds
  let seeds ← seedIds.mapM (nodeById nodes)
  let activeSources ← boundedItems (fun j => text j) 512 (← field j "active_sources")
  distinct activeSources
  let budget ← nat (← field j "budget")
  if budget > 512 then return ← limited "activation budget exceeds 512"
  let p := makeProgram seeds activeSources edges
  let scanned := result p budget
  let checked := checkClosure p (trace p budget) scanned.known
  -- Runtime agreement with the proven completion invariant is itself checked;
  -- an internal discrepancy cannot be returned as a successful certificate.
  if scanned.finished != checked then return ← invalid "closure invariant mismatch"
  let knownIds := nodes.filter (fun n => scanned.known.contains n.atom) |>.map Node.id
  let fired := scanned.steps.filterMap (fun step => match step with
    | .rule r => some r.name | .fact _ => none)
  let inactive := edges.filterMap (fun e => (inactiveReason activeSources e).map
    (fun reason => Json.mkObj [("rule_id",toJson e.id),("reason",toJson reason)]))
  return Json.mkObj [
    ("law_id",toJson LexicalGraph.lawId),
    ("status",toJson (if checked then "CHECKED_CLOSURE" else "RESOURCE_EXHAUSTED")),
    ("complete",toJson checked), ("closure_checked",toJson checked),
    ("known",toJson knownIds), ("trace",toJson fired),
    ("seed_assumptions",toJson seedIds), ("active_rule_ids",toJson (p.rules.map Rule.name)),
    ("inactive",Json.arr inactive.toArray), ("activation_count",toJson fired.length),
    ("budget",toJson budget), ("rule_count",toJson edges.length),
    ("active_rule_count",toJson p.rules.length),
    ("world_truth_established",toJson false), ("all_arabic_complete",toJson false)]

def errorJson (e : Failure) : Json := Json.mkObj [("status",toJson e.code),("message",toJson e.message)]

/-- Run only after JSON syntax validation. Lean's object parser overwrites
duplicate keys; retain the raw quoted token and decode it before comparing
keys inside each object. Escaped spellings therefore cannot bypass uniqueness.
This transport check is intentionally local to the new graph protocol. -/
def uniqueObjectKeys (line : String) : ProbeM Unit := do
  let mut quoted := false
  let mut escaped := false
  let mut token : List Char := []
  let mut lastString : Option String := none
  let mut objects : List (List String) := []
  for c in line.toList do
    if quoted then
      token := c :: token
      if escaped then escaped := false
      else if c == '\\' then escaped := true
      else if c == '"' then
        quoted := false
        lastString := some (String.ofList token.reverse)
    else if c == '"' then
      quoted := true
      token := ['"']
      lastString := none
    else if c == '{' then
      objects := [] :: objects
      lastString := none
    else if c == '}' then
      objects := objects.tail
      lastString := none
    else if c == ':' then
      let some raw := lastString | return ← invalid "object key missing"
      let key ← str (← liftParse (Json.parse raw))
      let keys :: rest := objects | return ← invalid "object key outside object"
      if keys.contains key then return ← invalid "duplicate object key"
      objects := (key :: keys) :: rest
      lastString := none
    else if !c.isWhitespace then lastString := none

def processLine (bytes : ByteArray) (oversized : Bool) : Json :=
  if oversized then errorJson ⟨"RESOURCE_LIMIT", "input line exceeds 1 MiB"⟩
  else match String.fromUTF8? bytes with
    | none => errorJson ⟨"INVALID_INPUT", "input line is not valid UTF-8"⟩
    | some line =>
      match (do
        ProbeJson.preflight line
        let request ← liftParse (Json.parse line)
        uniqueObjectKeys line
        dispatch request : ProbeM Json) with
      | .ok result => result
      | .error failure => errorJson failure

def emit (output : IO.FS.Stream) (bytes : ByteArray) (oversized : Bool) : IO Unit := do
  output.putStr ((processLine bytes oversized).compress ++ "\n")
  output.flush

/-- Same bounded JSONL recovery as ProbeJson, with the graph-specific raw-key
check before dispatch. No historical executable changes its parser contract. -/
partial def readLoop (input output : IO.FS.Stream)
    (pending : ByteArray := ByteArray.emptyWithCapacity 0) (overflow : Bool := false) : IO Unit := do
  let chunk ← input.read 1
  if chunk.isEmpty then
    if !pending.isEmpty || overflow then emit output pending overflow
  else
    let mut pending := pending
    let mut overflow := overflow
    for byte in chunk do
      if byte == 10 then
        emit output pending overflow
        pending := ByteArray.emptyWithCapacity 0
        overflow := false
      else if !overflow then
        if pending.size < ProbeJson.maxLineBytes then pending := pending.push byte
        else
          pending := ByteArray.emptyWithCapacity 0
          overflow := true
    readLoop input output pending overflow
end LexicalGraphMain

def main (args : List String) : IO Unit := do
  let output ← IO.getStdout
  if args == ["--export"] then output.putStrLn LexicalGraphMain.table.compress
  else if args.isEmpty then
    LexicalGraphMain.readLoop (← IO.getStdin) output
  else throw (IO.userError "usage: lexicalGraph [--export]")
