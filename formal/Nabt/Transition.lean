import Std

namespace Nabt

/-- A finite alphabet can be supplied separately; the algebra itself is general. -/
structure Machine (Q A : Type) where
  step : Q → A → Q
  cost : Q → A → Nat
  final : Q → Bool

namespace Machine
variable {Q A : Type} (M : Machine Q A)

def run : Q → List A → Q
  | q, [] => q
  | q, a :: xs => run (M.step q a) xs

def weight : Q → List A → Nat
  | _, [] => 0
  | q, a :: xs => M.cost q a + weight (M.step q a) xs

abbrev Licensed (q : Q) (xs : List A) : Prop := M.final (M.run q xs) = true

theorem run_append (q : Q) (xs ys : List A) :
    M.run q (xs ++ ys) = M.run (M.run q xs) ys := by
  induction xs generalizing q with
  | nil => rfl
  | cons a xs ih => exact ih (M.step q a)

theorem weight_append (q : Q) (xs ys : List A) :
    M.weight q (xs ++ ys) = M.weight q xs + M.weight (M.run q xs) ys := by
  induction xs generalizing q with
  | nil => simp [weight, run]
  | cons a xs ih => simp only [List.cons_append, weight, run, ih]; omega

theorem licensed_append (q : Q) (xs ys : List A) :
    M.Licensed q (xs ++ ys) ↔ M.Licensed (M.run q xs) ys := by
  simp only [Licensed, M.run_append]

theorem path_compose {q r s : Q} {xs ys : List A}
    (hx : M.run q xs = r) (hy : M.run r ys = s) : M.run q (xs ++ ys) = s := by
  rw [M.run_append, hx, hy]

end Machine

structure Effect (Q : Type) where
  transform : Q → Q
  weight : Q → Nat

namespace Effect
variable {Q : Type}

def identity : Effect Q := ⟨id, fun _ => 0⟩
def compose (u v : Effect Q) : Effect Q :=
  ⟨fun q => v.transform (u.transform q), fun q => u.weight q + v.weight (u.transform q)⟩

theorem then_assoc (a b c : Effect Q) : (a.compose b).compose c = a.compose (b.compose c) := by
  cases a; cases b; cases c
  simp only [compose]
  congr 1
  funext q
  omega

theorem identity_left (a : Effect Q) : identity.compose a = a := by cases a; simp [compose, identity]
theorem identity_right (a : Effect Q) : a.compose identity = a := by
  cases a
  simp [compose, identity]

end Effect

def Machine.effect {Q A : Type} (M : Machine Q A) (xs : List A) : Effect Q :=
  ⟨fun q => M.run q xs, fun q => M.weight q xs⟩

theorem Machine.effect_append {Q A : Type} (M : Machine Q A) (xs ys : List A) :
    M.effect (xs ++ ys) = (M.effect xs).compose (M.effect ys) := by
  simp only [Machine.effect, Effect.compose]
  congr 1
  · funext q; exact M.run_append q xs ys
  · funext q; exact M.weight_append q xs ys

end Nabt
