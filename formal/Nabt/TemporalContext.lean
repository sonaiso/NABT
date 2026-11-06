import Std

/-! Closed integer-day intervals under explicitly supplied interpretations.
No parser, calendar conversion, source authenticity or event actuality theorem.
-/
namespace Nabt.TemporalContext

def lawId : String := "nabt.temporal-context.v1"

structure Interval where
  first : Int
  last : Int
  deriving DecidableEq, Repr

def Interval.valid (a : Interval) : Prop := a.first ≤ a.last
instance (a : Interval) : Decidable a.valid := inferInstanceAs (Decidable (a.first ≤ a.last))

inductive Relation where
  | before | after | equals | intersects | contains | within
  deriving DecidableEq, Repr

def holds : Relation → Interval → Interval → Prop
  | .before, a, b => a.last < b.first
  | .after, a, b => b.last < a.first
  | .equals, a, b => a = b
  | .intersects, a, b => a.first ≤ b.last ∧ b.first ≤ a.last
  | .contains, a, b => a.first ≤ b.first ∧ b.last ≤ a.last
  | .within, a, b => b.first ≤ a.first ∧ a.last ≤ b.last

instance (r : Relation) (a b : Interval) : Decidable (holds r a b) := by
  cases r <;> unfold holds <;> infer_instance

inductive Verdict where
  | confirmed | conflict | unknown
  deriving DecidableEq, Repr

def check (r : Relation) : Option Interval → Option Interval → Verdict
  | some a, some b => if a.valid ∧ b.valid ∧ holds r a b then .confirmed else .conflict
  | _, _ => .unknown

theorem check_confirmed_iff (r : Relation) (a b : Interval) :
    check r (some a) (some b) = .confirmed ↔ a.valid ∧ b.valid ∧ holds r a b := by
  simp [check]

theorem missing_left_unknown (r : Relation) (b : Option Interval) :
    check r none b = .unknown := by cases b <;> rfl

theorem missing_right_unknown (r : Relation) (a : Option Interval) :
    check r a none = .unknown := by cases a <;> rfl

theorem before_irreflexive (a : Interval) (h : a.valid) : ¬ holds .before a a := by
  simp only [holds, Interval.valid] at *
  omega

theorem before_transitive (a b c : Interval) (hb : b.valid)
    (hab : holds .before a b) (hbc : holds .before b c) : holds .before a c := by
  simp only [holds, Interval.valid] at *
  omega

def shift (a : Interval) (days : Int) : Interval := ⟨a.first + days, a.last + days⟩

theorem shift_valid_iff (a : Interval) (days : Int) : (shift a days).valid ↔ a.valid := by
  simp only [shift, Interval.valid]
  omega

theorem shift_width (a : Interval) (days : Int) :
    (shift a days).last - (shift a days).first = a.last - a.first := by
  simp only [shift]
  omega

structure Frame where
  scopeId : Nat
  speech : Option Nat
  reference : Option Nat
  event : Option Nat
  deriving DecidableEq, Repr

structure Result where
  frame : Frame
  verdict : Verdict
  worldTruth : Bool

def record (f : Frame) (v : Verdict) : Result := ⟨f, v, false⟩

theorem record_keeps_frame (f : Frame) (v : Verdict) : (record f v).frame = f := rfl
theorem record_no_world_truth (f : Frame) (v : Verdict) : (record f v).worldTruth = false := rfl

end Nabt.TemporalContext
