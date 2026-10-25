import Std

/-!
Ten source-scoped weak-letter relations. Frames are conditional analyses, not
proofs that a free-text word has the supplied lexical class or root alignment.
`bound` records the explicit structural/lexical premises of the corresponding
constructor. The Python adapter checks visible cells but does not acquire the
remaining semantic premises; it always reports application_established=false.
-/
namespace Nabt.ClassicalWeak

def lawId := "nabt.classical-weak.v1"

inductive Letter where | waw | ya | other deriving DecidableEq, Repr
inductive Vowel where | a | i | u | sukun deriving DecidableEq, Repr
inductive Position where | fa | ayn | lam deriving DecidableEq, Repr
inductive Next where | moving | sakin | alif | doubleYa | ending deriving DecidableEq, Repr
inductive NumberClass where | singular | plural | other deriving DecidableEq, Repr
inductive OpenRoot where | wata | wasia | wadaa | other deriving DecidableEq, Repr
inductive DoubleProfile where | regular | ghaya | other deriving DecidableEq, Repr

inductive Frame where
  | initial (letter : Letter) (own following : Vowel) (bound : Bool)
  | initialOpen (root : OpenRoot) (own following : Vowel) (bound : Bool)
  | wawYa (letter : Letter) (previous own : Vowel) (bound : Bool)
  | yaWaw (letter : Letter) (previous own : Vowel) (number : NumberClass) (bound : Bool)
  | alif (letter : Letter) (previous own : Vowel) (original : Bool)
      (position : Position) (following : Next) (bound : Bool)
  | afal (letter : Letter) (previous own : Vowel) (bound : Bool)
  | reciprocal (letter : Letter) (previous own : Vowel) (bound : Bool)
  | doubleWeak (first second : Letter) (previous own following : Vowel)
      (profile : DoubleProfile) (bound : Bool)
  | nominal (letter : Letter) (previous own : Vowel) (bound : Bool)
  | transfer (letter : Letter) (previous own : Vowel) (soundPrevious bound : Bool)
  deriving DecidableEq, Repr

inductive Action where
  | drop | toYa | toWaw | toAlif | keep | lowerPrevious | secondToAlif | transfer
  deriving DecidableEq, Repr

def weak (l : Letter) : Bool := l != .other
def moving (v : Vowel) : Bool := v != .sukun
def alifNext (p : Position) (n : Next) : Bool :=
  (p == .ayn && n == .moving) || (p == .lam && n != .alif && n != .doubleYa)

def candidates : Frame → List Action
  | .initial l v n b => if l == .waw && v == .sukun && n == .i && b then [.drop] else []
  | .initialOpen r v n b => if r != .other && v == .sukun && n == .a && b then [.drop] else []
  | .wawYa l p v b => if l == .waw && p == .i && v == .sukun && b then [.toYa] else []
  | .yaWaw l p v n b =>
      if l == .ya && p == .u && v == .sukun && b then
        match n with | .singular => [.toWaw] | .plural => [.lowerPrevious] | .other => []
      else []
  | .alif l p v o q n b =>
      if weak l && p == .a && moving v && o && alifNext q n && b then [.toAlif] else []
  | .afal l p v b => if weak l && p == .a && moving v && b then [.keep] else []
  | .reciprocal l p v b =>
      if p == .a && moving v && b then
        match l with | .waw => [.keep] | .ya => [.toAlif] | .other => []
      else []
  | .doubleWeak l r p v n profile b =>
      if weak l && weak r && p == .a && v == .a && moving n && b then
        match profile with | .regular => [.secondToAlif] | .ghaya => [.toAlif] | .other => []
      else []
  | .nominal l p v b => if weak l && p == .a && moving v && b then [.keep] else []
  | .transfer l p v s b => if weak l && p == .sukun && moving v && s && b then [.transfer] else []

-- Declarative source-relative relation, independent of candidate-list membership.
def Admissible : Frame → Action → Prop
  | .initial l v n b, a => l = .waw ∧ v = .sukun ∧ n = .i ∧ b = true ∧ a = .drop
  | .initialOpen r v n b, a => r ≠ .other ∧ v = .sukun ∧ n = .a ∧ b = true ∧ a = .drop
  | .wawYa l p v b, a => l = .waw ∧ p = .i ∧ v = .sukun ∧ b = true ∧ a = .toYa
  | .yaWaw l p v n b, a => l = .ya ∧ p = .u ∧ v = .sukun ∧ b = true ∧
      ((n = .singular ∧ a = .toWaw) ∨ (n = .plural ∧ a = .lowerPrevious))
  | .alif l p v o q n b, a => l ≠ .other ∧ p = .a ∧ v ≠ .sukun ∧ o = true ∧
      ((q = .ayn ∧ n = .moving) ∨ (q = .lam ∧ n ≠ .alif ∧ n ≠ .doubleYa)) ∧
      b = true ∧ a = .toAlif
  | .afal l p v b, a => l ≠ .other ∧ p = .a ∧ v ≠ .sukun ∧ b = true ∧ a = .keep
  | .reciprocal l p v b, a => p = .a ∧ v ≠ .sukun ∧ b = true ∧
      ((l = .waw ∧ a = .keep) ∨ (l = .ya ∧ a = .toAlif))
  | .doubleWeak l r p v n profile b, a =>
      l ≠ .other ∧ r ≠ .other ∧ p = .a ∧ v = .a ∧ n ≠ .sukun ∧ b = true ∧
      ((profile = .regular ∧ a = .secondToAlif) ∨ (profile = .ghaya ∧ a = .toAlif))
  | .nominal l p v b, a => l ≠ .other ∧ p = .a ∧ v ≠ .sukun ∧ b = true ∧ a = .keep
  | .transfer l p v s b, a => l ≠ .other ∧ p = .sukun ∧ v ≠ .sukun ∧ s = true ∧ b = true ∧ a = .transfer

theorem enumeration_exact (f : Frame) (a : Action) : a ∈ candidates f ↔ Admissible f a := by
  cases f with
  | initial l v n b => simp [candidates, Admissible, and_assoc]
  | initialOpen r v n b => simp [candidates, Admissible, and_assoc]
  | wawYa l p v b => simp [candidates, Admissible, and_assoc]
  | yaWaw l p v n b => cases n <;> simp [candidates, Admissible, and_assoc]
  | alif l p v o q n b => simp [candidates, Admissible, weak, moving, alifNext, and_assoc]
  | afal l p v b => simp [candidates, Admissible, weak, moving, and_assoc]
  | reciprocal l p v b => cases l <;> simp [candidates, Admissible, moving, and_assoc]
  | doubleWeak l r p v n profile b => cases profile <;> simp [candidates, Admissible, weak, moving, and_assoc]
  | nominal l p v b => simp [candidates, Admissible, weak, moving, and_assoc]
  | transfer l p v s b => simp [candidates, Admissible, weak, moving, and_assoc]

theorem enumeration_sound (f : Frame) (a : Action) (h : a ∈ candidates f) : Admissible f a :=
  (enumeration_exact f a).mp h

theorem enumeration_complete (f : Frame) (a : Action) (h : Admissible f a) : a ∈ candidates f :=
  (enumeration_exact f a).mpr h

theorem no_lost_alternative (f : Frame) (a : Action) (h : Admissible f a)
    (proposed : List Action) (missing : a ∉ proposed) :
    ¬ (∀ x, Admissible f x → x ∈ proposed) := by
  intro all
  exact missing (all a h)

theorem candidates_length_le_one (f : Frame) : (candidates f).length ≤ 1 := by
  cases f <;> simp only [candidates] <;> split <;> simp_all
  all_goals split <;> simp

theorem candidates_nodup (f : Frame) : (candidates f).Nodup := by
  cases f <;> simp only [candidates] <;> split <;> simp_all
  all_goals split <;> simp

theorem initial_ya_not_deleted (v n : Vowel) (b : Bool) :
    candidates (.initial .ya v n b) = [] := by simp [candidates]

theorem open_vowel_not_general_deletion (v : Vowel) (b : Bool) :
    candidates (.initial .waw v .a b) = [] := by simp [candidates]

theorem unnamed_open_exception_blocked (v n : Vowel) (b : Bool) :
    candidates (.initialOpen .other v n b) = [] := by simp [candidates]

theorem plural_preserves_ya : candidates (.yaWaw .ya .u .sukun .plural true) = [.lowerPrevious] := by rfl
theorem singular_changes_ya : candidates (.yaWaw .ya .u .sukun .singular true) = [.toWaw] := by rfl

theorem transient_vowel_blocks_alif (l : Letter) (p v : Vowel) (q : Position) (n : Next) (b : Bool) :
    candidates (.alif l p v false q n b) = [] := by simp [candidates]

theorem medial_sakin_blocks_alif (l : Letter) (p v : Vowel) (o b : Bool) :
    candidates (.alif l p v o .ayn .sakin b) = [] := by simp [candidates, alifNext]

theorem final_alif_blocks_alif (l : Letter) (p v : Vowel) (o b : Bool) :
    candidates (.alif l p v o .lam .alif b) = [] := by simp [candidates, alifNext]

theorem final_double_ya_blocks_alif (l : Letter) (p v : Vowel) (o b : Bool) :
    candidates (.alif l p v o .lam .doubleYa b) = [] := by simp [candidates, alifNext]

theorem reciprocal_waw_preserved : candidates (.reciprocal .waw .a .a true) = [.keep] := by rfl
theorem reciprocal_ya_changed : candidates (.reciprocal .ya .a .a true) = [.toAlif] := by rfl
theorem regular_double_changes_second :
    candidates (.doubleWeak .waw .ya .a .a .a .regular true) = [.secondToAlif] := by rfl
theorem named_double_changes_first :
    candidates (.doubleWeak .ya .ya .a .a .a .ghaya true) = [.toAlif] := by rfl
theorem nominal_block_preserves : candidates (.nominal .waw .a .a true) = [.keep] := by rfl
theorem unsound_predecessor_blocks_transfer (l : Letter) (p v : Vowel) (b : Bool) :
    candidates (.transfer l p v false b) = [] := by simp [candidates]

/- The tape operation is separate from control. A certificate additionally binds
the controls to actual cells and binds the retained source to its window. -/
structure Cell where
  carrier : Nat
  vowel : Vowel
  deriving DecidableEq, Repr

structure Window where
  before : List Cell
  previous : Cell
  focus : Cell
  following : Option Cell
  after : List Cell
  deriving DecidableEq, Repr

-- Local carrier IDs: 0=alif, 1=waw, 2=ya, 3=emphatic ta, 4=sin, 5=dad,
-- 6=hamza, 7=ayn, 8=ghayn, 9=ta, 10=nun; other naturals remain distinct.
def classify (n : Nat) : Letter := if n = 1 then .waw else if n = 2 then .ya else .other
def nextVowel (w : Window) := w.following.map Cell.vowel |>.getD .sukun
def nextLetter (w : Window) := w.following.map (classify ∘ Cell.carrier) |>.getD .other
def nextKind (w : Window) : Next :=
  match w.following with
  | none => .ending
  | some c =>
      if c.carrier = 0 then .alif
      else if c.carrier = 2 && c.vowel == .sukun &&
        w.after.head?.any (fun n => n.carrier == 2 && moving n.vowel) then .doubleYa
      else if moving c.vowel then .moving else .sakin

def rawCells (w : Window) := w.before ++ [w.previous, w.focus] ++ w.following.toList ++ w.after

def localOutput (w : Window) (a : Action) : List Cell :=
  match a with
  | .drop => [w.previous] ++ w.following.toList
  | .toYa => [w.previous, {w.focus with carrier := 2}] ++ w.following.toList
  | .toWaw => [w.previous, {w.focus with carrier := 1}] ++ w.following.toList
  | .toAlif => [w.previous, ⟨0, .sukun⟩] ++ w.following.toList
  | .keep => [w.previous, w.focus] ++ w.following.toList
  | .lowerPrevious => [{w.previous with vowel := .i}, w.focus] ++ w.following.toList
  | .secondToAlif => [w.previous, w.focus] ++ (w.following.map (fun _ => ⟨0, .sukun⟩)).toList
  | .transfer => [{w.previous with vowel := w.focus.vowel}, {w.focus with vowel := .sukun}] ++ w.following.toList

def render (w : Window) (a : Action) := w.before ++ localOutput w a ++ w.after

def BasicMatch (w : Window) (l : Letter) (p v : Vowel) : Prop :=
  classify w.focus.carrier = l ∧ w.previous.vowel = p ∧ w.focus.vowel = v

def OpenRootMatch (w : Window) (r : OpenRoot) : Prop :=
  w.focus.carrier = 1 ∧ w.before = [] ∧ w.previous.carrier = 2 ∧ w.previous.vowel = .a ∧
  match r with
  | .wata => w.following.map Cell.carrier = some 3 ∧ w.after.map Cell.carrier = [6]
  | .wasia => w.following.map Cell.carrier = some 4 ∧ w.after.map Cell.carrier = [7]
  | .wadaa => w.following.map Cell.carrier = some 5 ∧ w.after.map Cell.carrier = [7]
  | .other => True

def finalSuffixSafe (w : Window) : Prop :=
  w.after.head?.map Cell.carrier ≠ some 0 ∧
  ¬ (w.after.head? = some ⟨2, .sukun⟩ ∧
    (w.after[1]?).any (fun c => c.carrier == 2 && moving c.vowel) = true)

def nominalSuffixVisible (w : Window) : Prop :=
  w.following.isSome = true ∧ ∃ rest v, w.after = rest ++ [⟨0, .sukun⟩, ⟨10, v⟩]

def WindowMatches (f : Frame) (w : Window) : Prop :=
  match f with
  | .initial l v n _ => classify w.focus.carrier = l ∧ w.focus.vowel = v ∧
      nextVowel w = n ∧ w.previous.carrier = 2 ∧ w.previous.vowel = .a ∧
      w.before = [] ∧ w.following.isSome = true ∧ w.after.length = 1
  | .initialOpen r v n _ => OpenRootMatch w r ∧ w.focus.vowel = v ∧ nextVowel w = n
  | .wawYa l p v _ | .yaWaw l p v _ _ | .afal l p v _ => BasicMatch w l p v
  | .nominal l p v _ => BasicMatch w l p v ∧ nominalSuffixVisible w
  | .alif l p v _ q n _ => BasicMatch w l p v ∧ nextKind w = n ∧
      ¬ (q = .ayn ∧ w.focus.vowel = .a ∧ nextLetter w ≠ .other ∧ nextVowel w ≠ .sukun)
  | .reciprocal l p v _ => BasicMatch w l p v ∧ nextKind w = .moving ∧
      w.previous.carrier = 9 ∧ ∃ c, w.before = [⟨0, .i⟩, ⟨c, .sukun⟩]
  | .doubleWeak l r p v n profile _ => BasicMatch w l p v ∧ nextLetter w = r ∧ nextVowel w = n ∧
      finalSuffixSafe w ∧
      (profile = .ghaya → w.before = [] ∧ w.previous.carrier = 8 ∧
        w.focus.carrier = 2 ∧ w.following.map Cell.carrier = some 2 ∧ w.after.map Cell.carrier = [9])
  | .transfer l p v sound _ => BasicMatch w l p v ∧
      sound = (w.previous.carrier != 0 && w.previous.carrier != 1 && w.previous.carrier != 2) ∧
      ∃ following, w.following = some following ∧ following.carrier ≠ 0 ∧
        following.carrier ≠ 1 ∧ following.carrier ≠ 2 ∧
        w.after.head?.map Cell.carrier ≠ some following.carrier

structure Certificate where
  source : List Cell
  window : Window
  frame : Frame
  action : Action
  source_matches : source = rawCells window
  controls_match : WindowMatches frame window
  lawful : Admissible frame action

def output (c : Certificate) := render c.window c.action
def restore (c : Certificate) := c.source

def Related (f : Frame) (source result : List Cell) : Prop :=
  ∃ w a, source = rawCells w ∧ WindowMatches f w ∧ Admissible f a ∧ result = render w a

theorem certificate_related (c : Certificate) : Related c.frame c.source (output c) :=
  ⟨c.window, c.action, c.source_matches, c.controls_match, c.lawful, rfl⟩

theorem exact_source_restoration (c : Certificate) : restore c = rawCells c.window := c.source_matches
theorem outer_context_preserved (w : Window) (a : Action) :
    render w a = w.before ++ localOutput w a ++ w.after := rfl
theorem keep_is_identity (w : Window) : render w .keep = rawCells w := by
  simp [render, localOutput, rawCells, List.append_assoc]
theorem transfer_preserves_carriers (w : Window) :
    (localOutput w .transfer).map Cell.carrier = (localOutput w .keep).map Cell.carrier := by
  simp [localOutput]
theorem transfer_target_silent (w : Window) :
    (localOutput w .transfer)[1]? = some {w.focus with vowel := .sukun} := by simp [localOutput]
theorem lower_previous_preserves_target (w : Window) :
    (localOutput w .lowerPrevious)[1]? = some w.focus := by simp [localOutput]
theorem second_change_preserves_first (w : Window) :
    (localOutput w .secondToAlif)[1]? = some w.focus := by simp [localOutput]
theorem drop_shortens_local (w : Window) :
    (localOutput w .drop).length + 1 = (localOutput w .keep).length := by simp [localOutput]
theorem nondrop_preserves_length (w : Window) (a : Action) (h : a ≠ .drop) :
    (localOutput w a).length = (localOutput w .keep).length := by
  cases a <;> simp_all [localOutput]
  cases w.following <;> rfl

theorem classify_waw_exact (n : Nat) : classify n = .waw ↔ n = 1 := by
  simp [classify]; split <;> simp_all

theorem bound_initial_cannot_delete_other (w : Window) (l : Letter) (v n : Vowel) (b : Bool)
    (bound : WindowMatches (.initial l v n b) w) (h : Admissible (.initial l v n b) .drop) :
    w.focus.carrier = 1 := by
  exact (classify_waw_exact _).mp (bound.1.trans h.1)

end Nabt.ClassicalWeak
