import ProbeJson

/-! Independent finite-scope compiler. Inference belongs to VerifiedReading
and EvidenceLifecycleV1; this executable neither asserts domain membership nor
claims that a supplied finite list exhausts a real-world genus. -/
open Lean ProbeJson
namespace ScopedQuantifier

def defer (s : String) : ProbeM α := .error ⟨"DEFER",s⟩
def array (s : List String) : Json := toJson (s.map toJson)
def reserved := ["نتيجة_النطاق","النطاق","القضية"]

-- Same bounded ground-name alphabet as VerifiedReading, checked independently.
def name (s : String) : Bool := !s.isEmpty && s.length ≤ 64 &&
  !["ليس","هو","إذا","فإن","و","هل","كل","كان","تعريف","مفهوم","علاقة","فرد"].contains s &&
  s.toList.all (fun c => ('a' ≤ c && c ≤ 'z') || ('A' ≤ c && c ≤ 'Z') ||
    ('0' ≤ c && c ≤ '9') || c == '_' || ('ء' ≤ c && c ≤ 'غ') ||
    ('ف' ≤ c && c ≤ 'ي') || ('ً' ≤ c && c ≤ 'ْ'))

def parse (text : String) : ProbeM (String × String × String × Json) := do
  let question := text.startsWith "هل "
  let core := if question then (text.drop 3).toString else text
  let core := if core.endsWith (if question then "؟" else ".") then (core.dropEnd 1).toString else core
  let words := core.splitOn " "
  let (kind, genus, prop, alignment) ←
    if core == "ليس كل طالب مجتهدًا" then pure ("not_all","طالب","مجتهد","AUTHORED_LITERAL_ALIAS_V1")
    else if core == "كل طالب غير مجتهد" then pure ("all_not","طالب","مجتهد","AUTHORED_LITERAL_ALIAS_V1")
    else match words with
      | ["كل",g,"هو",p] => pure ("all",g,p,"CONTROLLED_COPULA_V1")
      | ["ليس","كل",g,"هو",p] => pure ("not_all",g,p,"CONTROLLED_COPULA_V1")
      | ["كل",g,"ليس","هو",p] => pure ("all_not",g,p,"CONTROLLED_COPULA_V1")
      | _ => defer "Outside quantifier grammar"
  if reserved.contains genus || reserved.contains prop then return ← invalid "Reserved scope symbols"
  if !name genus || !name prop then return ← defer "Noncanonical quantifier concept"
  let mut offset := if question then "هل ".toUTF8.size else 0
  let mut rows := []
  for word in words do
    rows := rows ++ [Json.mkObj [("raw",toJson word),("span",toJson [offset,offset+word.toUTF8.size])]]
    offset := offset + word.toUTF8.size + 1
  let inner := array ["all",genus,prop]
  let scope := if kind == "not_all" then toJson [toJson "not",inner]
    else if kind == "all_not" then toJson [toJson "all",toJson genus,array ["not",prop]] else inner
  let frame := Json.mkObj [("kind",toJson kind),("genus",toJson genus),("property",toJson prop),
    ("force",toJson (if question then "question" else "assertion_target")),
    ("alignment",toJson alignment),("tokens",toJson rows),("scope_tree",scope)]
  return (kind,genus,prop,frame)

structure Atom where
  predicate : String
  arguments : List String
  positive : Bool := true
def atomJson (a : Atom) : Json := Json.mkObj [("predicate",toJson a.predicate),
  ("arguments",toJson a.arguments),("positive",toJson a.positive)]
def render (a : Atom) : String :=
  let signText := if a.positive then "" else "ليس "
  match a.arguments with
  | [n] => signText ++ n ++ " هو " ++ a.predicate
  | [x,y] => signText ++ x ++ " " ++ a.predicate ++ " " ++ y
  | _ => ""
def goal (positive : Bool) : Atom := ⟨"نتيجة_النطاق",["النطاق","القضية"],positive⟩
def rule (body : List Atom) (positive : Bool) : Json × String :=
  (Json.mkObj [("kind",toJson "rule"),("body",toJson (body.map atomJson)),("head",atomJson (goal positive))],
   "إذا " ++ String.intercalate " و " (body.map render) ++ " فإن " ++ render (goal positive) ++ ".\n")

def project (text : String) (domain : List String) : ProbeM Json := do
  if domain.isEmpty || domain.length > 4 then return ← invalid "Nonempty bounded domain required"
  if domain.eraseDups != domain then return ← invalid "Duplicate domain identity"
  if !domain.all (fun n => name n && !reserved.contains n) then return ← invalid "Invalid scope identity"
  let (kind,genus,prop,frame) ← parse text
  let universal := domain.flatMap fun n => [Atom.mk genus [n] true, Atom.mk prop [n] (kind != "all_not")]
  let rules := rule universal (kind != "not_all") :: domain.map (fun n =>
    rule [⟨genus,[n],true⟩,⟨prop,[n],kind == "all_not"⟩] (kind == "not_all"))
  return Json.mkObj [("frame",frame),("domain",toJson domain),("clauses",toJson (rules.map Prod.fst)),
    ("policy_text",toJson (String.intercalate "" (rules.map Prod.snd))),
    ("query_text",toJson ("هل " ++ render (goal true) ++ "؟\n"))]
end ScopedQuantifier
