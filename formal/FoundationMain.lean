import Nabt.Foundation
import ProbeJson

/-! Bounded JSONL adapter. Projection is the Lean definition; the adapter does
not claim a theorem about JSON parsing, SHA hashes, or linguistic truth. -/
open Lean ProbeJson Nabt.Foundation
namespace FoundationMain

def exactFields (j : Json) (names : List String) : ProbeM Unit := do
  let obj ← liftParse j.getObj?
  if obj.size != names.length || names.any (fun name => (obj.get? name).isNone) then
    invalid "unexpected or missing field"
  else pure ()

def label (j : Json) : ProbeM String := do
  let value ← str j
  if value.isEmpty || value.toList.length > 256 ||
      value.toList.any (fun c => c.toNat < 32 || c.toNat == 127) then
    return ← invalid "source labels must be nonempty, bounded and control-free"
  return value

def parseSource (j : Json) : ProbeM Source := do
  exactFields j ["id", "revision", "text"]
  let id ← label (← field j "id")
  let revision ← label (← field j "revision")
  let content ← str (← field j "text")
  if content.utf8ByteSize > 65536 then return ← limited "source exceeds 65536 bytes"
  return ⟨id, revision, content⟩

def sourceJson (source : Source) : Json := Json.mkObj [
  ("id", toJson source.id), ("revision", toJson source.revision), ("text", toJson source.text)]

def identity : Json := Json.mkObj [
  ("law_id", toJson lawId), ("alphabet_id", toJson alphabetId),
  ("number_domain", toJson numberDomain), ("shape_law_id", toJson shapeLawId),
  ("carriers", toJson Nabt.canonicalCarriers), ("marks", toJson marks),
  ("alphabet_size", toJson (116 : Nat))]

def kindLabel : Kind → String
  | .cell _ => "cell" | .separator => "separator" | .residual => "residual"

def pieceJson (start : Nat) (piece : Piece) : Json := Json.mkObj [
  ("kind", toJson (kindLabel piece.kind)), ("text", toJson piece.text),
  ("start_byte", toJson start), ("end_byte", toJson (start + piece.text.utf8ByteSize)),
  ("cell", toJson (piece.cell.map Fin.val))]

def issueJson (code : String) (start stop : Nat) : Json := Json.mkObj [
  ("code", toJson code), ("start_byte", toJson start), ("end_byte", toJson stop)]

def piecesJson (items : List Piece) : List Json × List Json := Id.run do
  let mut offset := 0
  let mut projected := []
  let mut issues := []
  for piece in items do
    let stop := offset + piece.text.utf8ByteSize
    projected := pieceJson offset piece :: projected
    for code in piece.issues do
      issues := issueJson code offset stop :: issues
    offset := stop
  return (projected.reverse, issues.reverse)

def receiptJson (receipt : Receipt) : Json :=
  let encoded := piecesJson receipt.items
  let issues := if receipt.source.text.isEmpty then
    issueJson "EMPTY_SOURCE" 0 0 :: encoded.2 else encoded.2
  Json.mkObj [
    ("law_id", toJson lawId), ("alphabet_id", toJson alphabetId),
    ("number_domain", toJson numberDomain), ("source", sourceJson receipt.source),
    ("raw_utf8", toJson (receipt.source.text.toUTF8.data.toList.map UInt8.toNat)),
    ("status", toJson receipt.status.label), ("pieces", toJson encoded.1),
    ("cells", toJson (receipt.cells.map Fin.val)), ("number", toJson (toString receipt.number)),
    ("issues", toJson issues)]

structure WireIssue where
  code : String
  start : Nat
  stop : Nat

def parseIssue (j : Json) : ProbeM WireIssue := do
  exactFields j ["code", "start_byte", "end_byte"]
  return ⟨← str (← field j "code"), ← nat (← field j "start_byte"),
    ← nat (← field j "end_byte")⟩

def parsePiece (issues : List WireIssue) (j : Json) : ProbeM Piece := do
  exactFields j ["kind", "text", "start_byte", "end_byte", "cell"]
  let content ← str (← field j "text")
  let start ← nat (← field j "start_byte")
  let stop ← nat (← field j "end_byte")
  let cell ← field j "cell"
  let kind ← match ← str (← field j "kind") with
    | "cell" => do
      let value ← nat cell
      if h : value < 116 then pure (Kind.cell ⟨value, h⟩)
      else invalid "cell outside the installed alphabet"
    | "separator" =>
      if cell == Json.null then pure Kind.separator else invalid "separator has a cell"
    | "residual" =>
      if cell == Json.null then pure Kind.residual else invalid "residual has a cell"
    | _ => invalid "unknown piece kind"
  return ⟨content.toList, kind,
    (issues.filter (fun issue => issue.start == start && issue.stop == stop)).map WireIssue.code⟩

def parseReceipt (j : Json) : ProbeM Receipt := do
  exactFields j ["law_id", "alphabet_id", "number_domain", "source", "raw_utf8",
    "status", "pieces", "cells", "number", "issues"]
  let source ← parseSource (← field j "source")
  let status ← match ← str (← field j "status") with
    | "COMPLETE" => pure Status.complete
    | "PARTIAL" => pure Status.incomplete
    | "INVALID" => pure Status.invalid
    | _ => invalid "unknown proposed projection status"
  let issues ← items parseIssue (← field j "issues")
  let projected ← items (parsePiece issues) (← field j "pieces")
  return ⟨source, projected, status⟩

def boundedProject (source : Source) : ProbeM Receipt := do
  let result := project source
  if result.cells.length > 4096 then return ← limited "projection exceeds 4096 cells"
  if (receiptJson result).compress.utf8ByteSize > 524288 then
    return ← limited "projection receipt exceeds 524288 UTF-8 bytes"
  return result

def parseCells (j : Json) : ProbeM (List Nabt.Atom) := do
  let values ← liftParse j.getArr?
  if values.size > 4096 then return ← limited "cell list exceeds 4096 cells"
  values.toList.mapM fun value => do
    let n ← nat value
    if h : n < 116 then return ⟨n, h⟩ else invalid "cell outside the installed alphabet"

def parseBinding (j : Json) : ProbeM LayerBinding := do
  exactFields j ["source", "scope_id", "occurrence_id", "reading_id", "start_byte", "end_byte", "surface"]
  let source ← parseSource (← field j "source")
  let scope ← label (← field j "scope_id")
  let occurrence ← label (← field j "occurrence_id")
  let reading ← label (← field j "reading_id")
  let start ← nat (← field j "start_byte")
  let stop ← nat (← field j "end_byte")
  let surface ← str (← field j "surface")
  if surface.utf8ByteSize > 65536 then return ← limited "surface exceeds 65536 bytes"
  return ⟨source, scope, occurrence, reading, start, stop, surface⟩

def bindingJson (binding : LayerBinding) : Json := Json.mkObj [
  ("source", sourceJson binding.source), ("scope_id", toJson binding.scopeId),
  ("occurrence_id", toJson binding.occurrenceId), ("reading_id", toJson binding.readingId),
  ("start_byte", toJson binding.startByte), ("end_byte", toJson binding.endByte),
  ("surface", toJson binding.surface)]

def parseOperation (j : Json) : ProbeM Operation := do
  match ← str (← field j "op") with
  | "keep" => exactFields j ["op"]; return .keep
  | "append" =>
    exactFields j ["op", "suffix"]
    return .append (← parseCells (← field j "suffix"))
  | "replace" =>
    exactFields j ["op", "index", "cell"]
    let index ← nat (← field j "index")
    let cell ← nat (← field j "cell")
    if h : cell < 116 then return .replace index ⟨cell, h⟩
    else invalid "replacement cell outside the installed alphabet"
  | _ => invalid "unknown numeric operation"

def operationJson : Operation → Json
  | .keep => Json.mkObj [("op", toJson "keep")]
  | .append suffix => Json.mkObj [("op", toJson "append"), ("suffix", toJson (suffix.map Fin.val))]
  | .replace index atom => Json.mkObj [("op", toJson "replace"),
      ("index", toJson index), ("cell", toJson atom.val)]

def transformJson (receipt : TransformReceipt) : Json := Json.mkObj [
  ("law_id", toJson receipt.law), ("alphabet_id", toJson alphabetId),
  ("number_domain", toJson numberDomain), ("binding", bindingJson receipt.binding),
  ("operation", operationJson receipt.operation),
  ("input_cells", toJson (receipt.input.map Fin.val)),
  ("output_cells", toJson (receipt.output.map Fin.val)),
  ("input_number", toJson (toString (Nabt.Sequence.encode receipt.input))),
  ("output_number", toJson (toString (Nabt.Sequence.encode receipt.output)))]

def parseTransformReceipt (j : Json) : ProbeM TransformReceipt := do
  exactFields j ["law_id", "alphabet_id", "number_domain", "binding", "operation",
    "input_cells", "output_cells", "input_number", "output_number"]
  return ⟨← parseBinding (← field j "binding"), ← str (← field j "law_id"),
    ← parseOperation (← field j "operation"), ← parseCells (← field j "input_cells"),
    ← parseCells (← field j "output_cells")⟩

def computeTransform (binding : LayerBinding) (operation : Operation) : ProbeM TransformReceipt := do
  if !(decide binding.Exact) then return ← invalid "occurrence is not an exact whole-cluster source byte slice"
  let projection ← boundedProject ⟨binding.source.id, binding.source.revision, binding.surface⟩
  match projection.status with
  | .incomplete => return ← .error ⟨"INCOMPLETE_PROJECTION", "numeric layer requires a complete surface projection"⟩
  | .invalid => return ← .error ⟨"INVALID_SOURCE", "numeric layer rejects malformed source marks"⟩
  | .complete => pure ()
  let some output := operation.run projection.cells
    | return ← invalid "operation outside its numerical input domain"
  if output.length > 4096 then return ← limited "operation output exceeds 4096 cells"
  let receipt : TransformReceipt := ⟨binding, transformLawId, operation, projection.cells, output⟩
  if !(checkTransform binding operation receipt) then
    return ← invalid "computed numeric receipt failed its formal checker"
  if (transformJson receipt).compress.utf8ByteSize > 524288 then
    return ← limited "numeric receipt exceeds 524288 UTF-8 bytes"
  return receipt

def dispatch (j : Json) : ProbeM Json := do
  match ← str (← field j "op") with
  | "identity" =>
    exactFields j ["op"]
    return identity
  | "project" =>
    exactFields j ["op", "source"]
    return receiptJson (← boundedProject (← parseSource (← field j "source")))
  | "check" =>
    exactFields j ["op", "source", "receipt"]
    let expected ← parseSource (← field j "source")
    let observed ← boundedProject expected
    let wire ← field j "receipt"
    let proposed ← parseReceipt wire
    -- The typed theorem covers the core receipt. Exact wire comparison also
    -- binds all derived domains, bytes, offsets, cell IDs and decimal number.
    let checked := checkReceipt expected proposed && wire == receiptJson observed
    return Json.mkObj [("law_id", toJson lawId), ("certificate_checked", toJson checked),
      ("observed", receiptJson observed)]
  | "transform" =>
    exactFields j ["op", "binding", "operation"]
    let binding ← parseBinding (← field j "binding")
    let operation ← parseOperation (← field j "operation")
    return transformJson (← computeTransform binding operation)
  | "check_transform" =>
    exactFields j ["op", "binding", "operation", "receipt"]
    let binding ← parseBinding (← field j "binding")
    let operation ← parseOperation (← field j "operation")
    let observed ← computeTransform binding operation
    let wire ← field j "receipt"
    let proposed ← parseTransformReceipt wire
    let checked := checkTransform binding operation proposed && wire == transformJson observed
    return Json.mkObj [("law_id", toJson transformLawId),
      ("certificate_checked", toJson checked), ("observed", transformJson observed)]
  | _ => invalid "unknown foundation operation"

def errorJson (error : Failure) : Json := Json.mkObj [
  ("law_id", toJson lawId), ("status", toJson error.code),
  ("reason", toJson error.message), ("certificate_checked", toJson false)]

def processLine (bytes : ByteArray) (oversized : Bool) : Json :=
  if oversized then errorJson ⟨"RESOURCE_LIMIT", "input line exceeds 1 MiB"⟩
  else match String.fromUTF8? bytes with
    | none => errorJson ⟨"INVALID_INPUT", "input line is not valid UTF-8"⟩
    | some line =>
      match (do
        ProbeJson.preflight line
        dispatch (← liftParse (Json.parse line)) : ProbeM Json) with
      | .ok result => result
      | .error failure => errorJson failure

def emit (output : IO.FS.Stream) (bytes : ByteArray) (oversized : Bool) : IO Unit := do
  output.putStr ((processLine bytes oversized).compress ++ "\n")
  output.flush

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
end FoundationMain

def main (args : List String) : IO Unit := do
  if args == ["--export"] then (← IO.getStdout).putStrLn FoundationMain.identity.compress
  else if args.isEmpty then FoundationMain.readLoop (← IO.getStdin) (← IO.getStdout)
  else throw (IO.userError "usage: foundation [--export]")
