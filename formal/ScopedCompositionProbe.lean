import ScopedArithmetic
import ScopedQuantifier

open Lean ProbeJson
namespace ScopedCompositionProbe
def lawId := "nabt.scoped-composition.v1"
def dispatch (request : Json) : ProbeM Json := do
  if (← str (← field request "law_id")) != lawId then return ← invalid "Unknown composition law"
  let profile ← str (← field request "profile")
  let text ← str (← field request "text")
  if text.toUTF8.size > 2048 then return ← limited "Source byte bound"
  let projection ← match profile with
    | "arithmetic" => ScopedArithmetic.project text
    | "quantifier" => ScopedQuantifier.project text (← items str (← field request "domain"))
    | _ => invalid "Unknown composition profile"
  return Json.mkObj [("law_id",toJson lawId),("status",toJson "OK"),
    ("request",request),("projection",projection)]
def errorResponse (f : Failure) : Json := Json.mkObj [
  ("law_id",toJson lawId),("status",toJson "ERROR"),("code",toJson f.code),("message",toJson f.message)]
end ScopedCompositionProbe

def main : IO Unit := do
  ProbeJson.readLoop ScopedCompositionProbe.dispatch
    ScopedCompositionProbe.errorResponse (← IO.getStdin) (← IO.getStdout)
