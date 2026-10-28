import Nabt.AcquiredSyntaxV3
import ProbeJson

open Lean ProbeJson Nabt.AcquiredSyntaxV3
namespace AcquiredSyntaxV3Main

/- Bounded transport guards are copied without changing the historical
acquisition executable. JSON/OS refinement remains a testing boundary. -/
def uniqueObjectKeys (text : String) : ProbeM Unit := do
  let mut stack : List (Option (List String)) := []
  let mut quoted := false
  let mut escaped := false
  let mut token : List Char := []
  let mut lastString : Option String := none
  for ch in text.toList do
    if quoted then
      token := ch :: token
      if escaped then escaped := false
      else if ch == '\\' then escaped := true
      else if ch == '"' then
        quoted := false
        lastString := some (String.ofList token.reverse)
        token := []
    else if ch == '"' then
      quoted := true
      token := ['"']
      lastString := none
    else if ch == ':' then
      match stack, lastString with
      | some names :: rest, some encoded =>
        if names.length >= 16 then return ← limited "JSON object exceeds 16 fields"
        let key ← str (← liftParse (Json.parse encoded))
        if names.contains key then return ← ProbeJson.invalid "duplicate JSON object key"
        stack := some (key :: names) :: rest
      | _, _ => pure ()
      lastString := none
    else if ch == '{' then
      stack := some [] :: stack
      lastString := none
    else if ch == '[' then
      stack := none :: stack
      lastString := none
    else if ch == '}' || ch == ']' then
      stack := stack.tail
      lastString := none
    else if !(ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n') then
      lastString := none

def keys (j : Json) (names : List String) : ProbeM Unit := do
  let entries ← liftParse j.getObj?
  if entries.size != names.length || names.any (fun n => (entries.get? n).isNone) then
    ProbeJson.invalid "object fields do not match the versioned schema"
  else pure ()

def metadata (j : Json) : ProbeM String := do
  let s ← str j
  if s.isEmpty || s.length > 512 || s.toList.any (fun c => c.toNat < 32 || (127 ≤ c.toNat && c.toNat ≤ 159)) then
    ProbeJson.invalid "identity must be nonempty, at most 512 scalars, and contain no C0/C1 controls"
  else return s

def request (j : Json) : ProbeM Request := do
  keys j ["text", "task", "source_id", "revision", "scope", "ending", "onset"]
  let text ← str (← field j "text")
  if text.toUTF8.size > 8192 || text.length > 4096 then return ← limited "source exceeds syntax budget"
  let task ← str (← field j "task")
  let task ← match task with
    | "person" => pure Task.person
    | "nominal_syntax" => pure Task.nominal
    | _ => ProbeJson.invalid "unknown syntax task"
  let sourceId ← metadata (← field j "source_id")
  let revision ← metadata (← field j "revision")
  let scope ← metadata (← field j "scope")
  let ending ← str (← field j "ending")
  if ending != "wasl" && ending != "waqf" then return ← ProbeJson.invalid "unknown ending"
  let onset ← str (← field j "onset")
  if onset != "word_initial" && onset != "connected" then return ← ProbeJson.invalid "unknown onset"
  return ⟨text, task, sourceId, revision, scope, ending, onset⟩

open Nabt.AlignedAcquisition (Span)
def spanJson (s : Span) : Json := Json.mkObj [
  ("start", toJson s.start), ("end", toJson s.stop),
  ("byte_start", toJson s.byteStart), ("byte_end", toJson s.byteStop),
  ("raw", toJson (String.ofList s.raw))]
def tokenJson (s : Span) : Json := Json.mkObj [
  ("start", toJson s.start), ("end", toJson s.stop),
  ("byte_start", toJson s.byteStart), ("byte_end", toJson s.byteStop),
  ("raw", toJson (String.ofList s.raw)),
  ("lexeme", toJson ((readLexeme (String.ofList s.raw)).map Lexeme.label))]
def suffix (s : Span) (count : Nat) : Span :=
  let raw := s.raw.reverse.take count |>.reverse
  ⟨s.stop - raw.length, s.byteStop - (String.ofList raw).utf8ByteSize, raw⟩
def diagnosticJson (p : PersonForm) : Json := Json.mkObj [
  ("reading_id", toJson p.lexeme.label), ("person", toJson p.person),
  ("number", toJson "singular"), ("gender", toJson p.gender)]
def personJson (p : PersonForm) (token : Span) : Json := Json.mkObj [
  ("reading_id", toJson p.lexeme.label), ("category", toJson "verb"),
  ("tense", toJson "past"), ("person", toJson p.person),
  ("number", toJson "singular"), ("gender", toJson p.gender),
  ("subject_form", toJson "attached_ta"), ("word_index", toJson (0 : Nat)),
  ("source_vowel", toJson p.vowel), ("referent", Json.null),
  ("source_word", tokenJson token), ("source_suffix", spanJson (suffix token 2))]
def nominalJson (n : Number) (o : Order) (tokens : List Span) : Json :=
  let si := if o == .subjectFirst then 0 else 1
  let pi := if o == .subjectFirst then 1 else 0
  let subject := tokens[si]?.getD ⟨0, 0, []⟩
  let predicate := tokens[pi]?.getD ⟨0, 0, []⟩
  Json.mkObj [
    ("subject_index", toJson si), ("predicate_index", toJson pi),
    ("subject_lexeme", toJson n.subject.label), ("predicate_lexeme", toJson n.predicate.label),
    ("order", toJson (if o == .subjectFirst then "subject_predicate" else "predicate_subject")),
    ("number", toJson n.label), ("gender", toJson "masculine"),
    ("subject_case", toJson "nominative"), ("predicate_case", toJson "nominative"),
    ("lexical_cardinality_alternatives", toJson (if n == .singular then ["individual", "collective"] else [])),
    ("denotation_cardinality", Json.null), ("referent", Json.null),
    ("source_words", toJson (tokens.map tokenJson)),
    ("subject_source", tokenJson subject), ("predicate_source", tokenJson predicate),
    ("subject_ending", spanJson (suffix subject (if n == .dual then 3 else 1))),
    ("predicate_ending", spanJson (suffix predicate (if n == .singular then 1 else 3)))]

def resultJson (r : Result) : Json :=
  let tokens := wordSpans r.request.text
  let person := match r.reading with
    | some (.person p) => personJson p (tokens.head?.getD ⟨0, 0, []⟩)
    | _ => Json.null
  let nominal := match r.reading with
    | some (.nominal n o) => nominalJson n o tokens
    | _ => Json.null
  let status := match r.reading with
    | some (.person _) => "LICENSED_PERSON"
    | some (.nominal ..) => "LICENSED_NOMINAL"
    | none => "DEFER"
  Json.mkObj [
    ("law_id", toJson lawId), ("text", toJson r.request.text),
    ("task", toJson (if r.request.task == .person then "person" else "nominal_syntax")),
    ("source_id", toJson r.request.sourceId), ("revision", toJson r.request.revision),
    ("scope", toJson r.request.scope), ("ending", toJson r.request.ending), ("onset", toJson r.request.onset),
    ("status", toJson status),
    ("reason", toJson (if r.reading.isSome then "FINITE_SOURCE_GRAMMAR" else "OUTSIDE_DECLARED_GRAMMAR")),
    ("boundary_valid", toJson (boundaryValid r.request.text)),
    ("source_pieces", toJson ((sourcePieces r.request.text).map spanJson)),
    ("tokens", toJson (tokens.map tokenJson)), ("reading_id", toJson (r.reading.map Frame.label)),
    ("person", person), ("nominal", nominal),
    ("diagnostic_person_hypotheses", toJson (if undecided r.request.text r.request.task then
      ([.qumtu, .qumta, .qumti] : List PersonForm).map diagnosticJson else []))]

def failureJson (e : Failure) : Json := Json.mkObj [
  ("law_id", toJson lawId),
  ("status", toJson (if e.code == "RESOURCE_LIMIT" then "RESOURCE_EXHAUSTED" else "INVALID_INPUT")),
  ("error", toJson e.code)]
def evaluate (bytes : ByteArray) : ProbeM Json := do
  if bytes.size > maxLineBytes then return ← limited "request exceeds 1 MiB"
  let some text := String.fromUTF8? bytes | ProbeJson.invalid "request must be strict UTF-8"
  preflight text
  uniqueObjectKeys text
  let r ← request (← liftParse (Json.parse text))
  return resultJson (Nabt.AcquiredSyntaxV3.evaluate r)
def readBounded (path : System.FilePath) : IO ByteArray := do
  let h ← IO.FS.Handle.mk path .read
  h.read (maxLineBytes + 1).toUSize
end AcquiredSyntaxV3Main
open AcquiredSyntaxV3Main

def main (args : List String) : IO UInt32 := do
  let out ← IO.getStdout
  match args with
  | [path] =>
    try
      match evaluate (← readBounded path) with
      | .error e => out.putStrLn (failureJson e).compress; return 2
      | .ok result =>
        let encoded := result.compress
        if encoded.toUTF8.size > 8388608 then
          out.putStrLn (failureJson ⟨"RESOURCE_LIMIT", "output exceeds 8 MiB"⟩).compress
          return 2
        out.putStrLn encoded
        return 0
    catch _ =>
      out.putStrLn (failureJson ⟨"INVALID_INPUT", "could not read request"⟩).compress
      return 2
  | _ =>
    out.putStrLn (failureJson ⟨"INVALID_INPUT", "expected one request file"⟩).compress
    return 2
