import Init.Data.Rat.Basic
import Nabt.RecursiveLicensedAlgebra
import ProbeJson

/-! Executable bounded reader, not a parser soundness theorem. It reparses the
original source independently of the Python proposal. No supplied AST is used.
Recursive algebra is reused for structural projection only, not grammar license. -/
open Lean ProbeJson
namespace ScopedArithmetic

def defer (s : String) : ProbeM α := .error ⟨"DEFER", s⟩
def pair (a b : Nat) : Json := toJson [a,b]

structure Token where
  raw : String
  kind : String
  first : Nat
  last : Nat
  deriving Inhabited

def tokenJson (t : Token) : Json := Json.mkObj [
  ("raw",toJson t.raw),("kind",toJson t.kind),("span",pair t.first t.last)]

def digit (c : Char) : Bool := '0' ≤ c && c ≤ '9'

def tokenize (text : String) : ProbeM (Array Token) := do
  if text.isEmpty then return ← defer "Empty arithmetic source"
  if text.toUTF8.size > 2048 then return ← limited "Arithmetic byte bound"
  let chars := text.toList.toArray
  let mut offsets := #[0]
  for c in chars do offsets := offsets.push (offsets.back! + (String.singleton c).toUTF8.size)
  let mut pos := 0
  let mut result := #[]
  for _ in [:chars.size] do
    if pos < chars.size then
      let c := chars[pos]!
      if [' ', '\t', '\n', '\r'].contains c then pos := pos + 1
      else
        let start := pos
        let mut raw := String.singleton c
        let mut kind := raw
        pos := pos + 1
        if digit c then
          for _ in [:chars.size] do
            if pos < chars.size && digit chars[pos]! then
              raw := raw.push chars[pos]!
              pos := pos + 1
          if raw.length > 9 then return ← limited "Literal bound"
          if raw.length > 1 && c == '0' then return ← defer "Noncanonical literal"
          kind := "number"
        else
          kind := if c == '×' then "*" else if c == '÷' then "/" else raw
          if !["+","-","*","/","^","(",")","="].contains kind then
            return ← defer "Unsupported arithmetic character"
        result := result.push ⟨raw,kind,offsets[start]!,offsets[pos]!⟩
        if result.size > 63 then return ← limited "Token bound"
  if result.isEmpty then return ← defer "No arithmetic tokens"
  return result

inductive Expr where
  | number (t : Token)
  | unary (op : String) (t : Token) (last : Nat) (child : Expr)
  | binary (op : String) (t : Token) (left right : Expr)

def first : Expr → Nat
  | .number t | .unary _ t _ _ => t.first
  | .binary _ _ a _ => first a
def last : Expr → Nat
  | .number t => t.last
  | .unary _ _ stop _ => stop
  | .binary _ _ _ b => last b
def height : Expr → Nat
  | .number _ => 1
  | .unary _ _ _ c => height c + 1
  | .binary _ _ a b => max (height a) (height b) + 1
def operator : Expr → String
  | .number _ => "number"
  | .unary op _ _ _ | .binary op _ _ _ => op

def binding (s : String) : Option (Nat × String) := match s with
  | "+" => some (10,"add") | "-" => some (10,"sub")
  | "*" => some (20,"mul") | "/" => some (20,"div")
  | "^" => some (30,"pow") | _ => none

def expression : Nat → Array Token → Nat → Nat → Nat → ProbeM (Expr × Nat)
  | 0, _, _, _, _ => limited "Parser fuel bound"
  | fuel+1, rows, pos, minimum, depth => do
    if depth > 12 then return ← limited "Nesting bound"
    if pos ≥ rows.size then return ← defer "Missing operand"
    let t := rows[pos]!
    let mut pos := pos + 1
    let (initial, next) ← if t.kind == "number" then pure (.number t, pos)
      else if t.kind == "+" || t.kind == "-" then do
        let (child, next) ← expression fuel rows pos 25 (depth+1)
        pure (.unary (if t.kind == "+" then "pos" else "neg") t (last child) child, next)
      else if t.kind == "(" then do
        let (child, next) ← expression fuel rows pos 0 (depth+1)
        if next ≥ rows.size || rows[next]!.kind != ")" then return ← defer "Unclosed group"
        pure (.unary "group" t rows[next]!.last child, next+1)
      else defer "Expected operand"
    let mut left := initial
    pos := next
    for _ in [:rows.size] do
      if pos < rows.size then
        if let some (precedence, op) := binding rows[pos]!.kind then
          if precedence ≥ minimum then
            let token := rows[pos]!
            let (right, next) ← expression fuel rows (pos+1)
              (if op == "pow" then precedence else precedence+1) (depth+1)
            left := .binary op token left right
            pos := next
    return (left, pos)

def parse (rows : Array Token) : ProbeM Expr := do
  let (initial, pos) ← expression 64 rows 0 0 0
  let (tree, pos) ← if pos < rows.size && rows[pos]!.kind == "=" then do
    let (right, next) ← expression 64 rows (pos+1) 0 0
    pure (.binary "equals" rows[pos]! initial right, next)
    else pure (initial, pos)
  if pos != rows.size then return ← defer "Unconsumed arithmetic source"
  if height tree > 12 then return ← limited "Tree height bound"
  return tree

def treeJson (e : Expr) : Json :=
  let (token, value, children) := match e with
    | .number t => (t, toJson t.raw, [])
    | .unary _ t _ c => (t, Json.null, [treeJson c])
    | .binary _ t a b => (t, Json.null, [treeJson a,treeJson b])
  Json.mkObj [("op",toJson (operator e)),("span",pair (first e) (last e)),
    ("operator_span",pair token.first token.last),("value",value),("children",toJson children)]

def operationTree : Expr → Json
  | .number t => toJson [toJson "number",toJson t.raw]
  | .unary "group" _ _ c => operationTree c
  | .unary op _ _ c => toJson [toJson op, operationTree c]
  | .binary op _ a b => toJson [toJson op, operationTree a, operationTree b]

def registry : String → Nat
  | "pos" => 1 | "neg" => 2 | "group" => 3 | "add" => 10 | "sub" => 11
  | "mul" => 12 | "div" => 13 | "pow" => 14 | "equals" => 20 | _ => 0

open Nabt.RecursiveLicensedAlgebra
def projectCore : Expr → Tree
  | .number t => .leaf (.lexical (t.raw.toNat?.getD 0))
  | .unary op _ _ c => .unary (registry op) (projectCore c)
  | .binary op _ a b => .binary (registry op) (projectCore a) (projectCore b)
def coreJson : Tree → Json
  | .leaf (.lexical n) => Json.mkObj [("kind",toJson "leaf"),
      ("seed",Json.mkObj [("kind",toJson "lexical"),("entry",toJson n)])]
  | .leaf _ => Json.null -- unreachable in this arithmetic projection
  | .unary n c => Json.mkObj [("kind",toJson "unary"),("rule",toJson n),("child",coreJson c)]
  | .binary n a b => Json.mkObj [("kind",toJson "binary"),("rule",toJson n),
      ("left",coreJson a),("right",coreJson b)]

structure Value where
  status : String := "COMPUTED"
  reason : Json := Json.null
  value : Option Rat := none
  truth : Json := Json.null

def rational (q : Rat) : Json := Json.mkObj [
  ("numerator",toJson (toString q.num)),("denominator",toJson (toString q.den))]
def valueFields (v : Value) : List (String × Json) := [
  ("status",toJson v.status),("reason",v.reason),
  ("value",v.value.map rational |>.getD Json.null),("truth",v.truth)]
def blocked (status reason : String) : Value := {status, reason := toJson reason}
def bounded (q : Rat) : Value :=
  if q.num.natAbs > 9007199254740991 || q.den > 9007199254740991 then
    blocked "RESOURCE_LIMIT" "EXACT_VALUE_BOUND"
  else {value := some q}

def evaluate (e : Expr) : Value × List Json :=
  let (v, trace) := match e with
    | .number t => (bounded (Rat.ofInt (t.raw.toInt?.getD 0)), [])
    | .unary op _ _ c =>
      let (v, trace) := evaluate c
      (if v.status != "COMPUTED" then v
       else bounded (if op == "neg" then -(v.value.getD 0) else v.value.getD 0), trace)
    | .binary op _ a b =>
      let (av, traceA) := evaluate a
      let (bv, traceB) := evaluate b
      let x := av.value.getD 0
      let y := bv.value.getD 0
      let value := if av.status != "COMPUTED" then av
        else if bv.status != "COMPUTED" then bv
        else match op with
          | "add" => bounded (x+y) | "sub" => bounded (x-y) | "mul" => bounded (x*y)
          | "div" => if y == 0 then blocked "BLOCKED" "DIVISION_BY_ZERO" else bounded (x/y)
          | "pow" => if y.den != 1 || y.num < 0 then blocked "OUTSIDE_SCOPE" "NON_NATURAL_EXPONENT"
              else if y.num > 12 then blocked "RESOURCE_LIMIT" "EXPONENT_BOUND"
              else if x == 0 && y == 0 then blocked "BLOCKED" "ZERO_TO_ZERO_EXCLUDED"
              else bounded (x ^ y.num.toNat)
          | "equals" => {truth := toJson (x == y)}
          | _ => blocked "DEFER" "UNKNOWN_OPERATOR"
      (value, traceA ++ traceB)
  (v, trace ++ [Json.mkObj ([("span",pair (first e) (last e)),("op",toJson (operator e))] ++ valueFields v)])

def project (text : String) : ProbeM Json := do
  let rows ← tokenize text
  let tree ← parse rows
  let (value, trace) := evaluate tree
  return Json.mkObj [("tokens",toJson (rows.toList.map tokenJson)),("tree",treeJson tree),
    ("operation_tree",operationTree tree),("recursive_tree",coreJson (projectCore tree)),
    ("result",Json.mkObj ([("sort",toJson (if operator tree == "equals" then "proposition" else "quantity"))]
      ++ valueFields value)),("trace",toJson trace)]
end ScopedArithmetic
