import Nabt.ClassicalWeak
import Lean

open Lean Nabt.ClassicalWeak

def letterName : Letter → String
  | .waw => "waw" | .ya => "ya" | .other => "other"
def vowelName : Vowel → String
  | .a => "a" | .i => "i" | .u => "u" | .sukun => "0"
def positionName : Nabt.ClassicalWeak.Position → String
  | .fa => "fa" | .ayn => "ayn" | .lam => "lam"
def nextName : Next → String
  | .moving => "moving" | .sakin => "sakin" | .alif => "alif"
  | .doubleYa => "double_ya" | .ending => "end"
def numberName : NumberClass → String
  | .singular => "singular" | .plural => "plural" | .other => "other"
def rootName : OpenRoot → String
  | .wata => "wata" | .wasia => "wasia" | .wadaa => "wadaa" | .other => "other"
def profileName : DoubleProfile → String
  | .regular => "regular" | .ghaya => "ghaya" | .other => "other"
def actionName : Action → String
  | .drop => "drop" | .toYa => "to_ya" | .toWaw => "to_waw"
  | .toAlif => "to_alif" | .keep => "keep" | .lowerPrevious => "lower_previous"
  | .secondToAlif => "second_to_alif" | .transfer => "transfer"

def frameJson : Frame → Json
  | .initial l v n b => toJson [toJson (0 : Nat), toJson (letterName l), toJson (vowelName v), toJson (vowelName n), toJson b]
  | .initialOpen r v n b => toJson [toJson (1 : Nat), toJson (rootName r), toJson (vowelName v), toJson (vowelName n), toJson b]
  | .wawYa l p v b => toJson [toJson (2 : Nat), toJson (letterName l), toJson (vowelName p), toJson (vowelName v), toJson b]
  | .yaWaw l p v n b => toJson [toJson (3 : Nat), toJson (letterName l), toJson (vowelName p), toJson (vowelName v), toJson (numberName n), toJson b]
  | .alif l p v o q n b => toJson [toJson (4 : Nat), toJson (letterName l), toJson (vowelName p), toJson (vowelName v), toJson o, toJson (positionName q), toJson (nextName n), toJson b]
  | .afal l p v b => toJson [toJson (5 : Nat), toJson (letterName l), toJson (vowelName p), toJson (vowelName v), toJson b]
  | .reciprocal l p v b => toJson [toJson (6 : Nat), toJson (letterName l), toJson (vowelName p), toJson (vowelName v), toJson b]
  | .doubleWeak l r p v n profile b => toJson [toJson (7 : Nat), toJson (letterName l), toJson (letterName r), toJson (vowelName p), toJson (vowelName v), toJson (vowelName n), toJson (profileName profile), toJson b]
  | .nominal l p v b => toJson [toJson (8 : Nat), toJson (letterName l), toJson (vowelName p), toJson (vowelName v), toJson b]
  | .transfer l p v s b => toJson [toJson (9 : Nat), toJson (letterName l), toJson (vowelName p), toJson (vowelName v), toJson s, toJson b]

def letters : List Letter := [.waw, .ya, .other]
def vowels : List Vowel := [.a, .i, .u, .sukun]
def flags : List Bool := [false, true]

def frames : List Frame := Id.run do
  let mut result := []
  for l in letters do
    for p in vowels do
      for v in vowels do
        for b in flags do
          result := result ++ [.initial l v p b, .wawYa l p v b, .afal l p v b,
            .reciprocal l p v b, .nominal l p v b]
          for n in ([.singular, .plural, .other] : List NumberClass) do
            result := result ++ [.yaWaw l p v n b]
          for s in flags do result := result ++ [.transfer l p v s b]
          for o in flags do
            for q in ([.fa, .ayn, .lam] : List Nabt.ClassicalWeak.Position) do
              for n in ([.moving, .sakin, .alif, .doubleYa, .ending] : List Next) do
                result := result ++ [.alif l p v o q n b]
          for r in letters do
            for n in vowels do
              for profile in ([.regular, .ghaya, .other] : List DoubleProfile) do
                result := result ++ [.doubleWeak l r p v n profile b]
  for r in ([.wata, .wasia, .wadaa, .other] : List OpenRoot) do
    for v in vowels do
      for n in vowels do
        for b in flags do result := result ++ [.initialOpen r v n b]
  return result

def main : IO Unit := do
  let rows := frames.map fun f => Json.mkObj [
    ("frame", frameJson f), ("actions", toJson ((candidates f).map actionName))]
  IO.println (Json.mkObj [("law_id", toJson lawId), ("rows", toJson rows),
    ("scope", toJson "complete finite conditional control domain; not Arabic lexical membership")]).compress
