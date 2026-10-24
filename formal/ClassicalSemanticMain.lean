import Nabt.SourceSemantics
import Nabt.MantuqMafhum
import ProbeJson

/-! Executable adapter. JSON and file IO remain in the computing base.
All verdicts are contract checks, not Arabic/world completeness claims. -/
open Lean ProbeJson Nabt.SourceSemantics
namespace ClassicalSemanticMain

def keys (j : Json) (names : List String) : ProbeM Unit := do
  let entries ← liftParse j.getObj?
  if entries.size != names.length || names.any (fun n => (entries.get? n).isNone) then
    return ← invalid "fields do not match schema"

def bounded (n : Nat) (parse : Json → ProbeM α) (j : Json) : ProbeM (List α) := do
  let xs ← liftParse j.getArr?
  if xs.size > n then return ← limited "too many elements"
  xs.toList.mapM parse

def bytes (j : Json) : ProbeM (List UInt8) := do return (← str j).toUTF8.data.toList
def binding (j : Json) : ProbeM Binding := do
  keys j ["source", "source_id", "scope", "context", "lexicon"]
  return ⟨← bytes (← field j "source"), ← str (← field j "source_id"),
    ← str (← field j "scope"), ← bytes (← field j "context"), ← bytes (← field j "lexicon")⟩

def candidate (j : Json) : ProbeM (Candidate String) := do
  keys j ["binding", "meaning"]
  let value ← field j "meaning"
  let meaning ← if value == Json.null then pure none else some <$> str value
  return ⟨← binding (← field j "binding"), meaning⟩

def term (j : Json) : ProbeM Nabt.SourceSemantics.Term := do
  let kind ← str (← field j "kind")
  if kind == "name" then
    keys j ["kind", "value"]
    return .name (← str (← field j "value"))
  else if kind == "variable" then
    keys j ["kind", "index"]
    return .variable (← nat (← field j "index"))
  else invalid "unknown term kind"

def formula : Nat → Json → ProbeM Formula
  | 0, _ => limited "formula depth exceeds 32"
  | fuel + 1, j => do
    let kind ← str (← field j "kind")
    if kind == "atom" then
      keys j ["kind", "concept", "args"]
      return .atom (← str (← field j "concept")) (← bounded 16 term (← field j "args"))
    else if kind == "both" || kind == "implies" then
      keys j ["kind", "left", "right"]
      let l ← formula fuel (← field j "left")
      let r ← formula fuel (← field j "right")
      return if kind == "both" then .both l r else .implies l r
    else invalid "unknown formula kind"

def termJson : Nabt.SourceSemantics.Term → Json
  | .name s => Json.mkObj [("kind", toJson "name"), ("value", toJson s)]
  | .variable n => Json.mkObj [("kind", toJson "variable"), ("index", toJson n)]
def formulaJson : Formula → Json
  | .atom c args => Json.mkObj [("kind", toJson "atom"), ("concept", toJson c),
      ("args", Json.arr (args.map termJson).toArray)]
  | .both l r => Json.mkObj [("kind", toJson "both"), ("left", formulaJson l), ("right", formulaJson r)]
  | .implies l r => Json.mkObj [("kind", toJson "implies"), ("left", formulaJson l), ("right", formulaJson r)]

def meaningProof : Nat → Json → ProbeM Nabt.MantuqMafhum.Proof
  | 0, _ => limited "meaning proof exceeds depth 32"
  | fuel + 1, j => do
    let kind ← str (← field j "kind")
    if kind == "premise" then
      keys j ["kind", "index"]
      return .premise (← nat (← field j "index"))
    else if kind == "left" || kind == "right" then
      keys j ["kind", "child"]
      let p ← meaningProof fuel (← field j "child")
      return if kind == "left" then .left p else .right p
    else if kind == "pair" then
      keys j ["kind", "left", "right"]
      return .pair (← meaningProof fuel (← field j "left"))
        (← meaningProof fuel (← field j "right"))
    else if kind == "apply" then
      keys j ["kind", "rule", "argument"]
      return .apply (← meaningProof fuel (← field j "rule"))
        (← meaningProof fuel (← field j "argument"))
    else invalid "unknown proof rule"

def meaningReading (j : Json) : ProbeM Nabt.MantuqMafhum.Reading := do
  keys j ["binding", "premises", "proof"]
  let premises ← field j "premises"
  let ps ← if premises == Json.null then pure none else
    some <$> bounded 128 (formula 32) premises
  return ⟨← binding (← field j "binding"), ps, ← meaningProof 32 (← field j "proof")⟩

def optionFormula : Option Formula → Json
  | none => Json.null
  | some f => formulaJson f

def response (fields : List (String × Json)) : Json := Json.mkObj (
  [("law_id", toJson lawId), ("world_truth_established", toJson false),
   ("all_arabic_complete", toJson false), ("reader_enumeration_proved", toJson false)] ++ fields)
def errorResponse (e : Failure) : Json := response [
  ("error", toJson e.code), ("message", toJson e.message)]

def ruleTable : Json := Id.run do
  let mut rows : List Json := []
  for (kind, label) in [(Nabt.SibawayhiRules.InflectedClass.noun, "noun"), (.presentVerb, "present_verb")] do
    for (regime, regimeLabel) in [(Nabt.SibawayhiRules.EndingRegime.unqualified, "unqualified"),
                                  (.overtPrimary, "overt_primary")] do
      for surface in Nabt.ClassicalLanguageEvidence.surfaces do
        rows := rows ++ [Json.mkObj [("class", toJson label), ("regime", toJson regimeLabel),
          ("surface", toJson surface.label),
          ("courses", toJson ((Nabt.SibawayhiRules.readings kind regime surface).map (·.label)))]]
  return response [("sibawayhi", toJson rows), ("sibawayhi_law_id", toJson Nabt.SibawayhiRules.lawId),
    ("qatr_past", toJson ([Nabt.QatrRules.PastAttachment.ordinary, .groupWaw, .movingSubjectPronoun].map
      (fun a => (Nabt.QatrRules.pastEnding a).label))),
    ("qatr_present", toJson ([Nabt.QatrRules.PresentAttachment.ordinary, .feminineNun, .directEmphasisNun].map
      (fun a => (Nabt.QatrRules.presentBuilding a).map (·.label)))),
    ("qatr_five_verbs", toJson ([Nabt.QatrRules.FiveVerbCase.raf, .nasb, .jazm].map
      (fun c => decide (Nabt.QatrRules.fiveVerbNun c = .retained)))),
    ("qatr_diptote", toJson ([false, true].flatMap (fun a => [false, true].map
      (fun b => (Nabt.QatrRules.diptoteGenitive a b).label)))),
    ("awamil_partition", toJson [Nabt.ClassicalLanguageEvidence.jurjaniPartition.samai,
      Nabt.ClassicalLanguageEvidence.jurjaniPartition.qiyasi, Nabt.ClassicalLanguageEvidence.jurjaniPartition.manawi]),
    ("awamil_selected_ba_senses", toJson ((Nabt.AwamilRules.candidates none).map (fun s =>
      match s with | .attachment => "attachment" | .instrument => "instrument"))),
    ("maqayis_selected_senses", toJson (Nabt.MaqayisRules.senses.map (fun s =>
      match s with
      | .mark => "mark"
      | .flag => "flag"
      | .mountain => "mountain"
      | .lipCleft => "lip_cleft"
      | .knowledge => "knowledge")))]

def tree (source : Nabt.ClassicalLanguageEvidence.Source) : Nat → Json → ProbeM EvidenceTree
  | 0, _ => limited "evidence depth exceeds 32"
  | fuel + 1, j => do
    let kind ← str (← field j "kind")
    if kind == "leaf" then
      keys j ["kind", "offset", "quote"]
      return .leaf ⟨source, ← nat (← field j "offset"), ← bytes (← field j "quote")⟩
    else if kind == "join" then
      keys j ["kind", "left", "right"]
      return .join (← tree source fuel (← field j "left")) (← tree source fuel (← field j "right"))
    else invalid "unknown evidence node"

def dispatch (source : Option Nabt.ClassicalLanguageEvidence.Source) (j : Json) : ProbeM Json := do
  let op ← str (← field j "op")
  if op == "rules" then
    keys j ["op"]
    return ruleTable
  else if op == "awamil_inventory" then
    keys j ["op"]
    return response [("inventory_law_id", toJson Nabt.AwamilInventory.lawId),
      ("entries", toJson (Nabt.AwamilInventory.entries.map fun e => Json.mkObj [
        ("id", toJson e.number), ("name", toJson e.name), ("page", toJson e.page),
        ("group", toJson e.group), ("family", toJson e.family)])),
      ("full_rule_semantics_complete", toJson false), ("occurrence_license_established", toJson false)]
  else if op == "meaning_from_source" then
    keys j ["op", "scope", "proof"]
    let some s := source | invalid "meaning derivation requires independently opened source"
    if s.bytes.length > 65536 then return ← limited "controlled source exceeds 64 KiB"
    let scope ← str (← field j "scope")
    let target : Nabt.VerifiedReading.Source := ⟨s.sourceId, s.revision, scope, s.bytes⟩
    let some clauses := Nabt.VerifiedReading.readSource s.bytes | invalid "outside controlled reading grammar"
    if clauses.length > 128 then return ← limited "too many controlled clauses"
    if !decide (Nabt.VerifiedReading.Reads target clauses) then
      return ← invalid "controlled reading does not match exact bytes"
    let proof ← meaningProof 32 (← field j "proof")
    let ps := clauses.map (Nabt.MantuqMafhum.clauseFormula scope)
    let result := Nabt.MantuqMafhum.infer ps proof
    return response [("meaning_law_id", toJson Nabt.MantuqMafhum.lawId),
      ("conclusion", optionFormula result), ("checked", toJson result.isSome),
      ("source_reading_checked", toJson true), ("source_id", toJson s.sourceId),
      ("source_text", toJson (Nabt.VerifiedReading.render clauses)),
      ("revision", toJson s.revision), ("scope", toJson scope),
      ("premise_truth_established", toJson false), ("usuli_subtype_established", toJson false)]
  else if op == "meaning_infer" then
    keys j ["op", "premises", "proof"]
    let ps ← bounded 128 (formula 32) (← field j "premises")
    let proof ← meaningProof 32 (← field j "proof")
    let result := Nabt.MantuqMafhum.infer ps proof
    return response [("meaning_law_id", toJson Nabt.MantuqMafhum.lawId),
      ("conclusion", optionFormula result), ("checked", toJson result.isSome),
      ("uses_implication", toJson proof.usesImplication),
      ("premise_truth_established", toJson false), ("usuli_subtype_established", toJson false)]
  else if op == "meaning_common" then
    keys j ["op", "expected", "readings"]
    let expected ← binding (← field j "expected")
    let readings ← bounded 128 meaningReading (← field j "readings")
    let result := Nabt.MantuqMafhum.common expected readings
    return response [("meaning_law_id", toJson Nabt.MantuqMafhum.lawId),
      ("conclusion", optionFormula result), ("checked", toJson result.isSome),
      ("readings_checked", toJson readings.length),
      ("premise_truth_established", toJson false), ("usuli_subtype_established", toJson false)]
  else if op == "contrast_policy" then
    keys j ["op", "kind", "qualified", "overridden", "usual_case"]
    let name ← str (← field j "kind")
    let kind ← match name with
      | "attribute" => pure Nabt.Shakhsiyya3Rules.ContrastKind.attribute
      | "condition" => pure .condition | "endpoint" => pure .endpoint
      | "number" => pure .number | "name" => pure .name | "innama" => pure .innama
      | _ => invalid "unknown contrast category"
    let allowed := Nabt.Shakhsiyya3Rules.permitsContrast kind
      (← boolean (← field j "qualified")) (← boolean (← field j "overridden"))
      (← boolean (← field j "usual_case"))
    return response [("policy_law_id", toJson Nabt.Shakhsiyya3Rules.lawId),
      ("conditional_policy_allows", toJson allowed), ("occurrence_license_established", toJson false)]
  else if op == "method_source" then
    keys j ["op", "law", "offset", "quote"]
    let some s := source | invalid "method source requires independently opened source file"
    let law ← str (← field j "law")
    let expectedWork ← if law == Nabt.ThinkingRules.lawId then pure Nabt.ClassicalLanguageEvidence.Work.thinking
      else if law == Nabt.Shakhsiyya1Rules.lawId then pure .shakhsiyyaFirst
      else if law == Nabt.Shakhsiyya3Rules.lawId then pure .shakhsiyyaThird
      else invalid "unknown method law"
    let p : Nabt.ClassicalLanguageEvidence.Passage :=
      ⟨s, ← nat (← field j "offset"), ← bytes (← field j "quote")⟩
    return response [("attested", toJson (Nabt.ClassicalLanguageEvidence.attested [s] p)),
      ("work_matches", toJson (decide (s.work = expectedWork))),
      ("interpretation_correctness_established", toJson false)]
  else if op == "consensus" then
    keys j ["op", "expected", "readings"]
    let result := consensus (← binding (← field j "expected"))
      (← bounded 128 candidate (← field j "readings"))
    return response [("consensus", toJson result), ("contract_verified", toJson result.isSome)]
  else if op == "reference" then
    keys j ["op", "closed", "candidates"]
    return response [("entity", toJson (resolveReference (← boolean (← field j "closed"))
      (← bounded 128 str (← field j "candidates"))))]
  else if op == "substitute" then
    keys j ["op", "formula", "replacements"]
    let f ← formula 32 (← field j "formula")
    let replacements ← bounded 128 term (← field j "replacements")
    return response [("formula", formulaJson (f.subst (fun n => (replacements[n]?).getD (.variable n))))]
  else if op == "time" then
    keys j ["op", "small", "big"]
    let interval (value : Json) : ProbeM Interval := do
      keys value ["first", "last"]
      -- String signed integers avoid the transport's natural-number fields.
      let firstText ← str (← field value "first")
      let lastText ← str (← field value "last")
      let some first := firstText.toInt? | invalid "invalid first time"
      let some last := lastText.toInt? | invalid "invalid last time"
      if toString first != firstText || toString last != lastText then
        return ← invalid "time endpoints require canonical signed decimal strings"
      return ⟨first, last⟩
    return response [("contained", toJson (decide ((← interval (← field j "small")).Within
      (← interval (← field j "big")))))]
  else if op == "evidence" then
    keys j ["op", "tree"]
    let some s := source | invalid "evidence operation requires independently opened source file"
    let t ← tree s 32 (← field j "tree")
    return response [("attested", toJson (t.valid [s])), ("source_id", toJson s.sourceId),
      ("edition", toJson s.edition), ("revision", toJson s.revision), ("leaves", toJson t.leaves.length)]
  else if op == "source_rule" then
    keys j ["op", "law", "offset", "quote"]
    let some s := source | invalid "source rule requires independently opened source file"
    let lawName ← str (← field j "law")
    let laws : List SelectedLaw := [.sibawayhi, .qatr, .awamil, .maqayis]
    let some law := laws.find? (fun l => l.version == lawName) | invalid "unknown selected law"
    let p : Nabt.ClassicalLanguageEvidence.Passage :=
      ⟨s, ← nat (← field j "offset"), ← bytes (← field j "quote")⟩
    return response [("attested", toJson (Nabt.ClassicalLanguageEvidence.attested [s] p)),
      ("interpretation_bound", toJson (ruleBound [s] law p)),
      ("selected_law_id", toJson law.version), ("source_id", toJson s.sourceId),
      ("edition", toJson s.edition), ("revision", toJson s.revision)]
  else invalid "unknown operation"

def work : String → Option Nabt.ClassicalLanguageEvidence.Work
  | "sibawayhi" => some .sibawayhi | "qatr" => some .qatr
  | "maqayis" => some .maqayis | "jurjaniAwamil" => some .jurjaniAwamil
  | "thinking" => some .thinking | "shakhsiyyaFirst" => some .shakhsiyyaFirst
  | "shakhsiyyaThird" => some .shakhsiyyaThird | "target" => some .targetText | _ => none

end ClassicalSemanticMain
open ClassicalSemanticMain

def main (args : List String) : IO UInt32 := do
  let out ← IO.getStdout
  try
    let source ← match args with
      | [] => pure none
      | [path, identity, edition, revision, kind] => do
        let some w := work kind | throw (IO.userError "unknown work")
        if identity.isEmpty || edition.isEmpty || revision.isEmpty then
          throw (IO.userError "source metadata must be nonempty")
        let h ← IO.FS.Handle.mk path .read
        let raw ← h.read 8388609
        if raw.size > 8388608 then
          out.putStrLn (errorResponse ⟨"RESOURCE_LIMIT", "source exceeds 8 MiB"⟩).compress
          return 2
        pure (some ⟨identity, w, edition, revision, raw.data.toList⟩)
      | _ => throw (IO.userError "expected no arguments or SOURCE ID EDITION REVISION WORK")
    ProbeJson.readLoop (dispatch source) errorResponse (← IO.getStdin) out
    return 0
  catch e =>
    out.putStrLn (errorResponse ⟨"IO_ERROR", e.toString⟩).compress
    return 2
