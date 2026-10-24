import Lean

/-!
Bounded JSONL transport copied from the reviewed UnitDiscoveryProbe transport
without changing that existing executable. New consumers supply their own
operation dispatcher and error envelope. Transport bounds, canonical naturals,
UTF-8 validity and surrogate handling are shared with the preserved contract.
This module is an executable adapter, not a proof of JSON parser refinement.
-/

open Lean
namespace ProbeJson

def maxLineBytes : Nat := 1048576
def maxDepth : Nat := 64
def maxNumberDigits : Nat := 256

structure Failure where
  code : String
  message : String

abbrev ProbeM := Except Failure

def invalid (message : String) : ProbeM α := .error ⟨"INVALID_INPUT", message⟩
def limited (message : String) : ProbeM α := .error ⟨"RESOURCE_LIMIT", message⟩

def liftParse (result : Except String α) : ProbeM α :=
  result.mapError (fun message => ⟨"INVALID_INPUT", message⟩)

def field (object : Json) (name : String) : ProbeM Json :=
  liftParse (object.getObjVal? name)

def optionalField (object : Json) (name : String) : ProbeM (Option Json) := do
  let entries ← liftParse object.getObj?
  return entries.get? name

def nat (value : Json) : ProbeM Nat := liftParse value.getNat?
def str (value : Json) : ProbeM String := liftParse value.getStr?
def boolean (value : Json) : ProbeM Bool := liftParse value.getBool?

def items (parse : Json → ProbeM α) (value : Json) : ProbeM (List α) := do
  let values ← liftParse value.getArr?
  values.toList.mapM parse

def atom (value : Json) : ProbeM String := do
  let value ← str value
  if value.isEmpty then invalid "an atom must be a nonempty declared string"
  else return value

def hexDigit : Char → Option Nat
  | character =>
    if '0' ≤ character && character ≤ '9' then some (character.toNat - '0'.toNat)
    else if 'a' ≤ character && character ≤ 'f' then some (10 + character.toNat - 'a'.toNat)
    else if 'A' ≤ character && character ≤ 'F' then some (10 + character.toNat - 'A'.toNat)
    else none

def hexQuad (a b c d : Char) : Option Nat := do
  return 4096 * (← hexDigit a) + 256 * (← hexDigit b) + 16 * (← hexDigit c) + (← hexDigit d)

/-- Lean's general JSON parser replaces lone UTF-16 surrogate escapes with
U+FFFD. Reject them before decoding, so distinct invalid inputs cannot silently
collapse to the same source atom. Escaped backslashes and literal U+FFFD are
preserved; an escaped high surrogate requires an immediate escaped low one. -/
def unicodeEscapesValid : List Char → Bool → Bool
  | [], _ => true
  | '\\' :: 'u' :: a :: b :: c :: d :: rest, true =>
    match hexQuad a b c d with
    | none => false
    | some value =>
      if 0xD800 ≤ value && value ≤ 0xDBFF then
        match rest with
        | '\\' :: 'u' :: e :: f :: g :: h :: tail =>
          match hexQuad e f g h with
          | none => false
          | some low =>
            if 0xDC00 ≤ low && low ≤ 0xDFFF then unicodeEscapesValid tail true else false
        | _ => false
      else if 0xDC00 ≤ value && value ≤ 0xDFFF then false
      else unicodeEscapesValid rest true
  | '\\' :: _ :: rest, true => unicodeEscapesValid rest true
  | '"' :: rest, true => unicodeEscapesValid rest false
  | _ :: rest, true => unicodeEscapesValid rest true
  | character :: rest, false => unicodeEscapesValid rest (character == '"')

/-- A small lexical boundary check before the general JSON parser prevents
unbounded numeric exponents and deeply nested malformed input. Strings and
escapes are preserved; interpretation still belongs to Lean's JSON parser. -/
def preflight (line : String) : ProbeM Unit := do
  let characters := line.toList
  if !unicodeEscapesValid characters false then
    return ← invalid "invalid Unicode escape or unpaired UTF-16 surrogate"
  let mut quoted := false
  let mut escaped := false
  let mut depth := 0
  let mut digits := 0
  for character in characters do
    if quoted then
      if escaped then escaped := false
      else if character == '\\' then escaped := true
      else if character == '"' then quoted := false
    else
      if character == '"' then
        quoted := true
        digits := 0
      else if '0' ≤ character && character ≤ '9' then
        digits := digits + 1
        if digits > maxNumberDigits then
          return ← limited "a JSON numeric token exceeds 256 decimal digits"
      else
        if (digits > 0 && (character == '.' || character == 'e' || character == 'E')) ||
            character == '-' || character == '+' then
          return ← invalid "numeric fields require unsigned decimal integer tokens"
        digits := 0
        if character == '[' || character == '{' then
          depth := depth + 1
          if depth > maxDepth then return ← limited "JSON nesting exceeds 64 levels"
        else if character == ']' || character == '}' then
          depth := depth - 1

def processLine (dispatch : Json → ProbeM Json) (errorResponse : Failure → Json) (bytes : ByteArray) (oversized : Bool) : Json :=
  if oversized then errorResponse ⟨"RESOURCE_LIMIT", "input line exceeds 1 MiB"⟩
  else match String.fromUTF8? bytes with
    | none => errorResponse ⟨"INVALID_INPUT", "input line is not valid UTF-8"⟩
    | some line =>
      match (do
        preflight line
        let request ← liftParse (Json.parse line)
        dispatch request : ProbeM Json) with
      | .ok result => result
      | .error failure => errorResponse failure

def emit (dispatch : Json → ProbeM Json) (errorResponse : Failure → Json) (output : IO.FS.Stream) (bytes : ByteArray) (oversized : Bool) : IO Unit := do
  output.putStr ((processLine dispatch errorResponse bytes oversized).compress ++ "\n")
  output.flush

/-- Bounded streaming, including discard-to-newline after an oversized line.
The following JSONL request is still processed independently. -/
partial def readLoop (dispatch : Json → ProbeM Json) (errorResponse : Failure → Json) (input output : IO.FS.Stream)
    (pending : ByteArray := ByteArray.empty) (overflow : Bool := false) : IO Unit := do
  -- `Stream.read n` may wait for n bytes through buffered stdio. A one-byte
  -- request lets a complete line receive its response before stdin reaches EOF.
  let chunk ← input.read 1
  if chunk.isEmpty then
    if !pending.isEmpty || overflow then emit dispatch errorResponse output pending overflow
  else
    let mut pending := pending
    let mut overflow := overflow
    for byte in chunk do
      if byte == 10 then
        emit dispatch errorResponse output pending overflow
        pending := ByteArray.empty
        overflow := false
      else if !overflow then
        if pending.size < maxLineBytes then pending := pending.push byte
        else
          pending := ByteArray.empty
          overflow := true
    readLoop dispatch errorResponse input output pending overflow


end ProbeJson
