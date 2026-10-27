import Nabt.QualifiedCueLicensing
import ProbeJson

open Lean ProbeJson Nabt.QualifiedCueLicensing
namespace QualifiedCueLicensingMain

def rowJson (form : Form) : Json := Json.mkObj [
  ("normal", toJson form.normal), ("role", toJson form.role),
  ("form", toJson form.surface), ("lexeme_ids", toJson form.lexemeIds),
  ("rule_ids", toJson form.ruleIds),
  ("next_requirement", toJson (match form.nextRequirement with
    | .any => "any" | .definiteWasl => "definite_wasl"))]

def dispatch (value : Json) : ProbeM Json := do
  let obj ← liftParse value.getObj?
  if obj.size != 1 || (obj.get? "review_sha256").isNone then
    return ← invalid "expected exactly review_sha256; no caller-supplied lexical ledger"
  let review ← str (← field value "review_sha256")
  if review != reviewSha256 then return ← invalid "uninstalled source review"
  return Json.mkObj [
    ("schema", toJson lawId), ("review_sha256", toJson reviewSha256),
    ("status", toJson "CHECKED_CONDITIONAL_FORMS"),
    ("forms", toJson (installedForms.map rowJson)),
    ("source_interpretation_kernel_proved", toJson false),
    ("intended_sense_established", toJson false),
    ("strict_language_accepted", toJson false), ("whole_arabic_complete", toJson false)]

def errorJson (failure : Failure) : Json :=
  Json.mkObj [("status", toJson failure.code), ("message", toJson failure.message)]

end QualifiedCueLicensingMain

def main (args : List String) : IO Unit := do
  if !args.isEmpty then throw (IO.userError "usage: qualifiedCueLicensing (bounded JSONL)")
  ProbeJson.readLoop QualifiedCueLicensingMain.dispatch QualifiedCueLicensingMain.errorJson
    (← IO.getStdin) (← IO.getStdout) (ByteArray.emptyWithCapacity 0) false
