import Nabt.ArabicInnaFragment
import ProbeJson

/-!
Executable transport for the proved `ArabicInnaFragment.recognize` function.
It executes that function, not a Python reimplementation. The request contains
exact source bytes and a supplied interpreted lexical ledger. No source
authenticity, completeness of that ledger, or external truth is conferred by
the request's strings or tags. A separate runner must record the program,
request, response and independently frozen lexical-source identities.

The mathematical theorem covers the Bytes/ledger recognizer. The Lean JSON
library, this bounded transport, compiler and operating system remain part of
the execution boundary; this file does not claim a verified JSON refinement.

Canonical compact JSON is required, including sorted object keys. Comparing
the parsed value's canonical encoding with the original line rejects duplicate
keys, alternate numeric encodings and ambiguous escapes before dispatch.
-/

open Lean ProbeJson
open Nabt.ArabicInnaFragment

namespace ArabicInnaFragmentProbe

def requestSchema : String := "nabt.arabic-inna-case-fragment.request.v1"
def responseSchema : String := "nabt.arabic-inna-case-fragment.response.v1"
def maxRequestBytes : Nat := 65536
def maxOutputBytes : Nat := 2097152
def maxSourceBytes : Nat := 2048
def maxSurfaceBytes : Nat := 256
def maxLexicalReadings : Nat := 32

def envelope (fields : List (String × Json)) : Json := Json.mkObj (
  [("schema", toJson responseSchema), ("law_id", toJson lawId),
   ("authority", toJson "CONDITIONAL_ON_SUPPLIED_LEXICAL_PREMISES"),
   ("source_acquisition_established", toJson false),
   ("lexicon_exhaustiveness_established", toJson false),
   ("ordinary_arabic_completeness_established", toJson false),
   ("semantic_interpretation_established", toJson false),
   ("world_truth", toJson "NOT_ESTABLISHED"),
   ("linguistic_rejection", toJson false)] ++ fields)

def errorResponse (failure : Failure) : Json := envelope [
  ("status", toJson "ERROR"), ("error", toJson failure.code),
  ("message", toJson failure.message),
  ("case_assignment_complete", toJson false)]

def exactKeys (value : Json) (allowed : List String) : ProbeM Unit := do
  let entries ← liftParse value.getObj?
  if entries.size != allowed.length ||
      !(allowed.all fun key => (entries.get? key).isSome) then
    return ← invalid "object fields must be exactly those of the installed schema"

def identifier (maximum : Nat) (value : Json) : ProbeM String := do
  let value ← str value
  if value.isEmpty then return ← invalid "lexical identifiers must be nonempty"
  if value.toUTF8.size > maximum then return ← limited "lexical identifier exceeds its byte limit"
  if !(value.toList.all fun c =>
      ('a' ≤ c && c ≤ 'z') || ('A' ≤ c && c ≤ 'Z') || ('0' ≤ c && c ≤ '9') ||
      c == '_' || c == '-' || c == '.' || c == ':' || c == '/' || c == '#') then
    return ← invalid "identifiers require ASCII letters, digits or _-.:/#"
  return value

def lowerHexDigit (character : Char) : Option Nat :=
  if '0' ≤ character && character ≤ '9' then some (character.toNat - '0'.toNat)
  else if 'a' ≤ character && character ≤ 'f' then some (10 + character.toNat - 'a'.toNat)
  else none

def decodeHex : List Char → ProbeM Bytes
  | [] => pure []
  | first :: second :: rest => do
    let high ← match lowerHexDigit first with
      | some value => pure value
      | none => invalid "hex input requires lowercase hexadecimal pairs"
    let low ← match lowerHexDigit second with
      | some value => pure value
      | none => invalid "hex input requires lowercase hexadecimal pairs"
    return UInt8.ofNat (high * 16 + low) :: (← decodeHex rest)
  | _ => invalid "hex input requires complete byte pairs"

def hexChar : Nat → Char
  | 0 => '0' | 1 => '1' | 2 => '2' | 3 => '3' | 4 => '4'
  | 5 => '5' | 6 => '6' | 7 => '7' | 8 => '8' | 9 => '9'
  | 10 => 'a' | 11 => 'b' | 12 => 'c' | 13 => 'd' | 14 => 'e' | 15 => 'f'
  | _ => '?'

def encodeHex (bytes : Bytes) : String := String.ofList (bytes.flatMap fun byte =>
  [hexChar (byte.toNat / 16), hexChar (byte.toNat % 16)])

def bytesField (maximum : Nat) (value : Json) : ProbeM Bytes := do
  let text ← str value
  if text.length > maximum * 2 then return ← limited "hex byte field exceeds its limit"
  let bytes ← decodeHex text.toList
  if encodeHex bytes != text then return ← invalid "hex encoding is not canonical"
  if (String.fromUTF8? ⟨bytes.toArray⟩).isNone then
    return ← invalid "source and lexical surfaces require valid UTF-8"
  return bytes

def category : String → ProbeM Category
  | "proper_name" => pure .properName | "adjective" => pure .adjective
  | "other" => pure .other | "unknown" => pure .unknown
  | _ => invalid "uninstalled lexical category"

def number : String → ProbeM Number
  | "singular" => pure .singular | "other" => pure .other | "unknown" => pure .unknown
  | _ => invalid "uninstalled number value"

def declension : String → ProbeM Declension
  | "triptote" => pure .triptote | "other" => pure .other | "unknown" => pure .unknown
  | _ => invalid "uninstalled declension value"

def caseTag : String → ProbeM Case
  | "nasb" => pure .nasb | "raf" => pure .raf | "jarr" => pure .jarr
  | "unknown" => pure .unknown
  | _ => invalid "uninstalled case value"

def categoryName : Category → String
  | .properName => "proper_name" | .adjective => "adjective"
  | .other => "other" | .unknown => "unknown"

def numberName : Number → String
  | .singular => "singular" | .other => "other" | .unknown => "unknown"

def declensionName : Declension → String
  | .triptote => "triptote" | .other => "other" | .unknown => "unknown"

def caseName : Case → String
  | .nasb => "nasb" | .raf => "raf" | .jarr => "jarr" | .unknown => "unknown"

def observedEnding (surface : Bytes) : Option Case :=
  if writtenNasb surface then some .nasb
  else if writtenRaf surface then some .raf
  else if writtenJarr surface then some .jarr
  else none

def lexicalReading (value : Json) : ProbeM LexicalReading := do
  exactKeys value ["id", "witness", "surface_hex", "category", "number", "declension", "case"]
  let result : LexicalReading := {
    id := ← identifier 128 (← field value "id")
    witness := ← identifier 256 (← field value "witness")
    surface := ← bytesField maxSurfaceBytes (← field value "surface_hex")
    category := ← category (← str (← field value "category"))
    number := ← number (← str (← field value "number"))
    declension := ← declension (← str (← field value "declension"))
    observedCase := ← caseTag (← str (← field value "case")) }
  if !(decide (SurfaceWithin result.surface)) then
    return ← invalid "lexical surfaces must be nonempty and obey the fragment byte-boundary profile"
  match observedEnding result.surface with
  | some actual =>
    if result.observedCase != .unknown && result.observedCase != actual then
      return ← invalid "declared lexical case conflicts with the explicit written ending"
  | none => pure ()
  return result

def lexicalJson (r : LexicalReading) : Json := Json.mkObj [
  ("id", toJson r.id), ("witness", toJson r.witness),
  ("surface_hex", toJson (encodeHex r.surface)),
  ("category", toJson (categoryName r.category)), ("number", toJson (numberName r.number)),
  ("declension", toJson (declensionName r.declension)), ("case", toJson (caseName r.observedCase))]

def analysisJson (a : Analysis) : Json :=
  let subjectStart := innaPrefix.length
  let subjectStop := subjectStart + a.subject.surface.length
  let predicateStart := subjectStop + wordSeparator.length
  let predicateStop := predicateStart + a.predicate.surface.length
  Json.mkObj [
    ("subject_id", toJson a.subject.id), ("predicate_id", toJson a.predicate.id),
    ("subject_witness", toJson a.subject.witness), ("predicate_witness", toJson a.predicate.witness),
    ("subject_span", toJson [subjectStart, subjectStop]),
    ("predicate_span", toJson [predicateStart, predicateStop]),
    ("required_subject_case", toJson "nasb"), ("required_predicate_case", toJson "raf")]

def statusName : Status → String
  | .completeWithinFragment => "COMPLETE_WITHIN_DECLARED_FRAGMENT"
  | .deferLexicalPremises => "DEFER_LEXICAL_PREMISES"
  | .noReadingInFragment => "NO_READING_IN_DECLARED_FRAGMENT"

def dispatch (request : Json) : ProbeM Json := do
  exactKeys request ["schema", "op", "source_hex", "lexicon"]
  if (← str (← field request "schema")) != requestSchema then
    return ← invalid "unsupported request schema"
  if (← str (← field request "op")) != "recognize" then
    return ← invalid "this version installs only the recognize operation"
  let source ← bytesField maxSourceBytes (← field request "source_hex")
  let values ← liftParse (← field request "lexicon").getArr?
  if values.size > maxLexicalReadings then return ← limited "lexical ledger exceeds 32 readings"
  let ledger ← values.toList.mapM lexicalReading
  if !(decide (ledger.map LexicalReading.id).Nodup) then
    return ← invalid "lexical reading identifiers must be unique"
  let recognized := recognize ledger source
  let unresolved := pending ledger source
  let outcome := status ledger source
  let response := envelope [
    ("status", toJson (statusName outcome)),
    ("source_hex", toJson (encodeHex source)),
    ("lexicon", toJson (ledger.map lexicalJson)),
    ("recognized", toJson (recognized.map analysisJson)),
    ("pending", toJson (unresolved.map analysisJson)),
    ("case_assignment_complete", toJson (outcome == .completeWithinFragment)),
    ("reference_equivalence", toJson "Nabt.ArabicInnaFragment.recognize_iff_reference"),
    ("written_case_basis", toJson "literal_utf8_tanwin_endings_with_explicit_accusative_alif.v1"),
    ("input_profile", toJson "exact_inna_prefix_single_ascii_spaces_no_final_punctuation.v1"),
    ("scope", toJson "all_case_assignments_in_declared_inna_fragment_relative_to_supplied_lexicon")]
  if response.compress.toUTF8.size + 1 > maxOutputBytes then
    return ← limited "complete response would exceed its 2 MiB wire budget"
  return response

def processLine (bytes : ByteArray) (oversized : Bool) : Json :=
  if oversized then errorResponse ⟨"RESOURCE_LIMIT", "input line exceeds 64 KiB"⟩
  else match String.fromUTF8? bytes with
    | none => errorResponse ⟨"INVALID_INPUT", "input line is not valid UTF-8"⟩
    | some line =>
      match (do
        preflight line
        let request ← liftParse (Json.parse line)
        if request.compress != line then
          return ← invalid "request must use canonical compact JSON with sorted object keys"
        dispatch request : ProbeM Json) with
      | .ok result => result
      | .error failure => errorResponse failure

def emit (output : IO.FS.Stream) (bytes : ByteArray) (oversized : Bool) : IO Unit := do
  output.putStr ((processLine bytes oversized).compress ++ "\n")
  output.flush

/-- Bounded JSONL transport, preserving the next request after overflow. -/
partial def readLoop (input output : IO.FS.Stream)
    (bytes : ByteArray := ByteArray.emptyWithCapacity 0) (overflow : Bool := false) : IO Unit := do
  let chunk ← input.read 1
  if chunk.isEmpty then
    if !bytes.isEmpty || overflow then emit output bytes overflow
  else
    let mut bytes := bytes
    let mut overflow := overflow
    for byte in chunk do
      if byte == 10 then
        emit output bytes overflow
        bytes := ByteArray.emptyWithCapacity 0
        overflow := false
      else if !overflow then
        if bytes.size < maxRequestBytes then bytes := bytes.push byte
        else
          bytes := ByteArray.emptyWithCapacity 0
          overflow := true
    readLoop input output bytes overflow

end ArabicInnaFragmentProbe

def main : IO Unit := do
  ArabicInnaFragmentProbe.readLoop (← IO.getStdin) (← IO.getStdout)
