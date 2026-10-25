import Std

/-!
Source-relative gemination control and cell projection. A frame is an explicit
morphological premise, not a proof that free text has that analysis. The original
Sibawayhi/Bakr reading does not specify a final vowel: its action therefore has
no completed surface. This absence is preserved, never filled by a synthetic
vowel. Source replay and Python correspondence are separate checked obligations.
-/
namespace Nabt.ClassicalGemination

def lawId := "nabt.classical-gemination.v1"

inductive Vowel where
  | s | a | i | u
  deriving DecidableEq, Repr

inductive Rule where
  | voweled | jussive | feminine | exclamation
  deriving DecidableEq, Repr

inductive Context where
  | ordinary | command | jussive | feminine | exclamation | hallumma
  deriving DecidableEq, Repr

inductive Dialect where
  | hijaz | tamim | kabGhani | bakr | attestedUnion
  deriving DecidableEq, Repr

inductive Action where
  | split | contractKeep | contractA | contractI | contractU
  | bakrUnvocalized | retainHallumma
  deriving DecidableEq, Repr

def follows : Vowel → Action
  | .a | .s => .contractA
  | .i => .contractI
  | .u => .contractU

def enumerate (r : Rule) (c : Context) (d : Dialect) (preceding last : Vowel) : List Action :=
  if r == .exclamation && c == .hallumma then
    if preceding == .u && last == .a then [.retainHallumma] else []
  else if preceding == .s then []
  else match r, c, last with
  | .voweled, .ordinary, .a | .voweled, .ordinary, .i | .voweled, .ordinary, .u =>
      [.contractKeep]
  | .jussive, .command, .s | .jussive, .jussive, .s =>
      match d with
      | .hijaz => [.split]
      | .tamim => if preceding == .a then [.contractA] else [.contractA, follows preceding]
      | .kabGhani => [.contractI]
      | .bakr => []
      | .attestedUnion => if preceding == .u then
            [.split, .contractA, .contractI, .contractU]
          else [.split, .contractA, .contractI]
  | .feminine, .feminine, .s =>
      match d with
      | .bakr => [.bakrUnvocalized]
      | .attestedUnion => [.split, .bakrUnvocalized]
      | _ => [.split]
  | .exclamation, .exclamation, .s => [.split]
  | _, _, _ => []

-- Independently stated, source-relative operation relation.
def Admissible (r : Rule) (c : Context) (d : Dialect) (preceding last : Vowel)
    (a : Action) : Prop :=
  (r = .exclamation ∧ c = .hallumma ∧ preceding = .u ∧ last = .a ∧ a = .retainHallumma) ∨
  (preceding ≠ .s ∧ (
    (r = .voweled ∧ c = .ordinary ∧ last ≠ .s ∧ a = .contractKeep) ∨
    (r = .jussive ∧ (c = .command ∨ c = .jussive) ∧ last = .s ∧
      ((d = .hijaz ∧ a = .split) ∨
       (d = .tamim ∧ (a = .contractA ∨ a = follows preceding)) ∨
       (d = .kabGhani ∧ a = .contractI) ∨
       (d = .attestedUnion ∧ (a = .split ∨ a = .contractA ∨ a = .contractI ∨
          (preceding = .u ∧ a = .contractU))))) ∨
    (r = .feminine ∧ c = .feminine ∧ last = .s ∧
      ((d ≠ .bakr ∧ a = .split) ∨
       ((d = .bakr ∨ d = .attestedUnion) ∧ a = .bakrUnvocalized))) ∨
    (r = .exclamation ∧ c = .exclamation ∧ last = .s ∧ a = .split)))

set_option maxRecDepth 2000 in
set_option maxHeartbeats 1600000 in
theorem enumeration_exact (r : Rule) (c : Context) (d : Dialect) (preceding last : Vowel)
    (a : Action) : a ∈ enumerate r c d preceding last ↔ Admissible r c d preceding last a := by
  cases r <;> cases c <;> cases d <;> cases preceding <;> cases last <;>
    simp [enumerate, Admissible, follows]

theorem enumeration_sound (r : Rule) (c : Context) (d : Dialect) (preceding last : Vowel)
    (a : Action) (h : a ∈ enumerate r c d preceding last) : Admissible r c d preceding last a :=
  (enumeration_exact r c d preceding last a).mp h

theorem enumeration_complete (r : Rule) (c : Context) (d : Dialect) (preceding last : Vowel)
    (a : Action) (h : Admissible r c d preceding last a) : a ∈ enumerate r c d preceding last :=
  (enumeration_exact r c d preceding last a).mpr h

set_option maxHeartbeats 1000000 in
theorem enumeration_nodup (r : Rule) (c : Context) (d : Dialect) (preceding last : Vowel) :
    (enumerate r c d preceding last).Nodup := by
  cases r <;> cases c <;> cases d <;> cases preceding <;> cases last <;>
    simp [enumerate, follows]

def Covers (r : Rule) (c : Context) (d : Dialect) (preceding last : Vowel)
    (proposal : List Action) : Prop :=
  ∀ a, Admissible r c d preceding last a → a ∈ proposal

theorem omitted_variant_rejects_completeness (r : Rule) (c : Context) (d : Dialect)
    (preceding last : Vowel) (a : Action) (proposal : List Action)
    (h : Admissible r c d preceding last a) (missing : a ∉ proposal) :
    ¬ Covers r c d preceding last proposal := by
  intro complete
  exact missing (complete a h)

theorem feminine_bakr_preserved (preceding : Vowel) (h : preceding ≠ .s) :
    Action.bakrUnvocalized ∈ enumerate .feminine .feminine .attestedUnion preceding .s := by
  cases preceding <;> simp_all [enumerate]

theorem feminine_hijaz_split_only (preceding : Vowel) (h : preceding ≠ .s) :
    enumerate .feminine .feminine .hijaz preceding .s = [.split] := by
  cases preceding <;> simp_all [enumerate]

theorem exclamation_never_contracts (d : Dialect) (preceding last : Vowel) :
    Action.contractKeep ∉ enumerate .exclamation .exclamation d preceding last := by
  cases preceding <;> cases last <;> simp [enumerate]

theorem hallumma_never_split (d : Dialect) (preceding last : Vowel) :
    Action.split ∉ enumerate .exclamation .hallumma d preceding last := by
  cases preceding <;> cases last <;> simp [enumerate]

structure Cell where
  letter : String
  vowel : Vowel
  deriving DecidableEq, Repr

structure Payload where
  leftCells : List Cell
  first : Cell
  second : Cell
  rightCells : List Cell
  deriving DecidableEq, Repr

def original (p : Payload) : List Cell := p.leftCells ++ [p.first, p.second] ++ p.rightCells

def transfer (leftCells : List Cell) (v : Vowel) : List Cell :=
  match leftCells.reverse with
  | [] => []
  | x :: rest =>
      if x.vowel == .s && x.letter != "ا" && x.letter != "ى" && x.letter != "آ" then
        (rest.reverse ++ [{x with vowel := v}])
      else leftCells

-- Only a direct wasl + newly-vocalized consonant loses supporting wasl.
def removeDirectWasl (before after : List Cell) : List Cell :=
  match before, after with
  | [h, c], [_, newC] =>
      if h.letter == "ٱ" && c.vowel == .s && newC.vowel != .s then [newC] else after
  | _, _ => after

def contractingPrefix (p : Payload) : List Cell :=
  removeDirectWasl p.leftCells (transfer p.leftCells p.first.vowel)

def finalVowel (a : Action) (old : Vowel) : Vowel :=
  match a with
  | .contractA => .a | .contractI => .i | .contractU => .u | _ => old

def project (p : Payload) (a : Action) : Option (List Cell) :=
  match a with
  | .bakrUnvocalized => none
  | .split | .retainHallumma => some (original p)
  | _ => some (contractingPrefix p ++
      [{p.first with vowel := .s}, {p.second with vowel := finalVowel a p.second.vowel}] ++ p.rightCells)

structure Result where
  input : Payload
  action : Action
  surface : Option (List Cell)
  deriving DecidableEq, Repr

def realize (p : Payload) (a : Action) : Result := ⟨p, a, project p a⟩

theorem original_frame_preserved (p : Payload) (a : Action) : (realize p a).input = p := rfl

theorem split_is_identity (p : Payload) : project p .split = some (original p) := rfl

theorem bakr_vowel_not_fabricated (p : Payload) : project p .bakrUnvocalized = none := rfl

theorem twin_identities_preserved (p : Payload) (a : Action)
    (h1 : a ≠ .split) (h2 : a ≠ .retainHallumma) (h3 : a ≠ .bakrUnvocalized) :
    project p a = some (contractingPrefix p ++
      [⟨p.first.letter, .s⟩, ⟨p.second.letter, finalVowel a p.second.vowel⟩] ++ p.rightCells) := by
  cases a <;> simp_all [project]

theorem rightCells_preserved (p : Payload) (a : Action)
    (h1 : a ≠ .split) (h2 : a ≠ .retainHallumma) (h3 : a ≠ .bakrUnvocalized) :
    ∃ front, project p a = some (front ++ p.rightCells) := by
  exact ⟨contractingPrefix p ++
    [⟨p.first.letter, .s⟩, ⟨p.second.letter, finalVowel a p.second.vowel⟩],
    twin_identities_preserved p a h1 h2 h3⟩

theorem distant_wasl_not_dropped (before after : List Cell)
    (h : before.length ≠ 2) : removeDirectWasl before after = after := by
  cases before with
  | nil => rfl
  | cons x xs => cases xs with
    | nil => rfl
    | cons y ys => cases ys with
      | nil => simp at h
      | cons z zs => rfl

inductive Connection where
  | withinWord | wordBoundaryWasl | wordBoundaryWaqf
  deriving DecidableEq, Repr

def NunAdmissible (left right : Cell) (c : Connection) : Prop :=
  left.letter = "ن" ∧ left.vowel = .s ∧ right.letter = "ب" ∧ c ≠ .wordBoundaryWaqf

def nunToMim (left right : Cell) (c : Connection) : Option (Cell × Cell) :=
  if left.letter == "ن" && left.vowel == .s && right.letter == "ب" &&
      c != .wordBoundaryWaqf then some (⟨"م", .s⟩, right) else none

theorem nun_exact (left right : Cell) (c : Connection) :
    nunToMim left right c = some (⟨"م", .s⟩, right) ↔ NunAdmissible left right c := by
  simp [nunToMim, NunAdmissible, Bool.and_eq_true, ite_eq_left_iff]

theorem nun_not_before_ya (left : Cell) (v : Vowel) (c : Connection) :
    nunToMim left ⟨"ي", v⟩ c = none := by simp [nunToMim]

theorem nun_not_across_pause (left right : Cell) :
    nunToMim left right .wordBoundaryWaqf = none := by simp [nunToMim]

theorem nun_vocalized_blocked (left right : Cell) (c : Connection) (h : left.vowel ≠ .s) :
    nunToMim left right c = none := by simp [nunToMim, h]

theorem nun_right_identity (left right : Cell) (c : Connection) (x y : Cell)
    (h : nunToMim left right c = some (x, y)) : y = right := by
  unfold nunToMim at h
  split at h <;> simp_all

end Nabt.ClassicalGemination
