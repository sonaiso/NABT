import A116.Fractal
import Nabt.Law

namespace PortCheck.Fractal
open A116

/-- The terminal decision and transitions are supplied by the original NABT machine. -/
def liftMachine {Q A : Type} (m : Nabt.Machine Q A) (initial : Q) :
    Tawrith.Tawrith A Q := ⟨initial, fun q a => some (m.step q a), m.final⟩

theorem flatRun {Q A : Type} (m : Nabt.Machine Q A) (initial q : Q) (xs : List A) :
    Tawrith.run (liftMachine m initial) q xs = some (m.run q xs) := by
  induction xs generalizing q with
  | nil => rfl
  | cons a xs ih => exact ih (m.step q a)

theorem licensePreserved {Q A : Type} (m : Nabt.Machine Q A) (initial : Q)
    (n : Nat) (xs : List (A116.Fractal.Lvl A n)) :
    Tawrith.lic (A116.Fractal.fractal (liftMachine m initial) n) xs =
      m.final (m.run initial (A116.Fractal.flatN n xs)) := by
  rw [A116.Fractal.fractal_lic]
  unfold Tawrith.lic
  rw [flatRun]
  rfl

theorem a116SoundShape (mode : Bool) (n : Nat) (xs : List (A116.Fractal.Lvl Nabt.Atom n)) :
    Tawrith.lic (A116.Fractal.fractal (liftMachine (Nabt.Law.machine mode) 0) n) xs =
      (Nabt.Law.machine mode).final ((Nabt.Law.machine mode).run 0 (A116.Fractal.flatN n xs)) :=
  licensePreserved _ _ _ _

#print axioms flatRun
#print axioms licensePreserved
#print axioms a116SoundShape
end PortCheck.Fractal
