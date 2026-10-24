import Nabt.Sequence
import Nabt.Law
import Nabt.UnitDiscovery

/-!
# Reusing a compound as a carrier without changing the atomic alphabet

A symbol has a nonempty, exactly recoverable A116 payload. Its number is a
content address in the existing versioned sequence alphabet, not a new member
of `Fin 116`. Reuse runs the payload's complete state/weight transformer.
Acceptance is always relative to the entry state and the declared boundary
mode. It cannot be obtained by testing each piece independently at state zero.

The numeric address carries no witness of lexical attestation or phonological
interpretation. Occurrence identity remains source/version/position qualified.
-/

namespace Nabt.UnitCarrier

def lawId : String := "nabt.unit-carrier.v1"
def alphabetId : String := "nabt.a116-sequence.v1"

structure Symbol where
  cells : List Atom
  nonempty : cells ≠ []
  deriving DecidableEq

def make (cells : List Atom) : Option Symbol :=
  if nonempty : cells ≠ [] then some ⟨cells, nonempty⟩ else none

def number (unit : Symbol) : Nat := Sequence.encode unit.cells

theorem number_restores (unit : Symbol) :
    Sequence.decode (number unit) = unit.cells := Sequence.decode_encode _

theorem number_injective : Function.Injective number := by
  intro left right same
  have cellsSame := Sequence.encode_injective same
  cases left
  cases right
  cases cellsSame
  rfl

theorem number_positive (unit : Symbol) : 0 < number unit := by
  have nonzero : number unit ≠ 0 := by
    intro zero
    have restored := number_restores unit
    rw [zero] at restored
    exact unit.nonempty restored.symm
  omega

def join (left right : Symbol) : Symbol :=
  ⟨left.cells ++ right.cells, by
    intro empty
    exact left.nonempty (List.append_eq_nil_iff.mp empty).1⟩

theorem join_number (left right : Symbol) :
    number (join left right) =
      116 ^ right.cells.length * number left + number right :=
  Sequence.encode_append _ _

theorem join_associative (left middle right : Symbol) :
    join (join left middle) right = join left (join middle right) := by
  apply number_injective
  simp only [number, join, List.append_assoc]

/-- A reified carrier is the entire transformer, including its input-dependent
weight. No single selected entry state stands in for this effect. -/
def effect (wasl : Bool) (unit : Symbol) : Effect Nat :=
  (Law.machine wasl).effect unit.cells

def accepts (wasl : Bool) (entry : Nat) (unit : Symbol) : Bool :=
  (Law.machine wasl).final ((effect wasl unit).transform entry)

theorem effect_join (wasl : Bool) (left right : Symbol) :
    effect wasl (join left right) =
      (effect wasl left).compose (effect wasl right) :=
  Machine.effect_append _ _ _

theorem effect_join_state (wasl : Bool) (entry : Nat) (left right : Symbol) :
    (effect wasl (join left right)).transform entry =
      (effect wasl right).transform ((effect wasl left).transform entry) := by
  rw [effect_join]
  rfl

theorem effect_join_weight (wasl : Bool) (entry : Nat) (left right : Symbol) :
    (effect wasl (join left right)).weight entry =
      (effect wasl left).weight entry +
        (effect wasl right).weight ((effect wasl left).transform entry) := by
  rw [effect_join]
  rfl

theorem accepts_join (wasl : Bool) (entry : Nat) (left right : Symbol) :
    accepts wasl entry (join left right) =
      accepts wasl ((effect wasl left).transform entry) right := by
  simp only [accepts, effect_join_state]

structure Occurrence where
  source : UnitDiscovery.Source Atom
  before : List Atom
  unit : Symbol
  after : List Atom
  deriving DecidableEq

def Exact (occurrence : Occurrence) : Prop :=
  occurrence.source.atoms =
    occurrence.before ++ occurrence.unit.cells ++ occurrence.after

instance (occurrence : Occurrence) : Decidable (Exact occurrence) :=
  inferInstanceAs (Decidable (_ = _))

/-- Content, location and derivation identity are separate. Two equal payloads
at distinct positions must not become one occurrence merely because n agrees. -/
structure OccurrenceKey where
  source : UnitDiscovery.Source Atom
  start : Nat
  stop : Nat
  contentNumber : Nat
  deriving DecidableEq

def occurrenceKey (occurrence : Occurrence) : OccurrenceKey :=
  ⟨occurrence.source, occurrence.before.length,
    occurrence.before.length + occurrence.unit.cells.length,
    number occurrence.unit⟩

theorem occurrence_key_preserves_source (left right : Occurrence)
    (same : occurrenceKey left = occurrenceKey right) :
    left.source = right.source := congrArg OccurrenceKey.source same

theorem occurrence_key_preserves_position (left right : Occurrence)
    (same : occurrenceKey left = occurrenceKey right) :
    left.before.length = right.before.length := congrArg OccurrenceKey.start same

theorem occurrence_key_preserves_content (left right : Occurrence)
    (same : occurrenceKey left = occurrenceKey right) : left.unit = right.unit :=
  number_injective (congrArg OccurrenceKey.contentNumber same)

/-- A source-correct occurrence is fully identified by its source, position
and content key. Exactness is essential: malformed context bytes cannot be
recovered merely from a prefix length. -/
theorem occurrence_key_injective_on_exact (left right : Occurrence)
    (leftExact : Exact left) (rightExact : Exact right)
    (same : occurrenceKey left = occurrenceKey right) : left = right := by
  have sourceSame := occurrence_key_preserves_source left right same
  have positionSame := occurrence_key_preserves_position left right same
  have unitSame := occurrence_key_preserves_content left right same
  have replay : left.before ++ (left.unit.cells ++ left.after) =
      right.before ++ (right.unit.cells ++ right.after) := by
    calc
      _ = left.source.atoms := by simpa [Exact, List.append_assoc] using leftExact.symm
      _ = right.source.atoms := congrArg UnitDiscovery.Source.atoms sourceSame
      _ = _ := by simpa [Exact, List.append_assoc] using rightExact
  have contexts := List.append_inj replay positionSame
  have beforeSame := contexts.1
  have afterSame := List.append_inj_right contexts.2 (by rw [unitSame])
  cases left
  cases right
  cases sourceSame
  cases beforeSame
  cases unitSame
  cases afterSame
  rfl

theorem exact_occurrence_restores (occurrence : Occurrence) (exact : Exact occurrence) :
    occurrence.before ++ Sequence.decode (number occurrence.unit) ++
      occurrence.after = occurrence.source.atoms := by
  rw [number_restores]
  exact exact.symm

/-- Finite counterexample in the existing declared sound-shape law: both
pieces finish at waqf when begun at zero, but their direct concatenation fails.
This is a machine witness, not a statement that either piece is an attested word. -/
theorem standalone_acceptance_does_not_license_join :
    let left : Symbol := ⟨[⟨84, by decide⟩, ⟨11, by decide⟩, ⟨11, by decide⟩], by decide⟩
    let right : Symbol := ⟨[⟨84, by decide⟩], by decide⟩
    accepts false 0 left = true ∧ accepts false 0 right = true ∧
      accepts false 0 (join left right) = false := by decide

end Nabt.UnitCarrier
