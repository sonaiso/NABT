import Nabt.SemanticInference

/-! Grounded passage v1. Typed projection of one scoped one-dimensional episode.
The caller of this internal executable supplies interpreted sources. The public
lesson collector checks their bindings and acquires the Arabic clause before
constructing this projection. Coordinates are exact, on one oriented axis.
All arithmetic and signed proof admission run here. -/
namespace Nabt.GroundedPassage
open Nabt.SemanticInference

structure Sample where
  minute : Nat
  x : Int
structure Measurement where
  id : String
  cmPerUnit : Nat
  samples : List Sample
structure MapRecord where
  id : String
  cmPerUnit : Nat
  gateX : Int
structure Permission where
  id : String
  minute : Nat
  endpoint : String
structure Input where
  scope : String
  active : List String
  facing : String
  maps : List MapRecord
  fixes : List Measurement
  tracks : List Measurement
  permits : List Permission

inductive Claim where
  | input (id : String)
  | position (minute : Nat) (cm : Int)
  | side (minute : Nat) (direction : String)
  | distance (minute cm : Nat)
  | crossing (minute : Nat)
  | deadline (minute : Nat) (endpoint : String)
  | within (minute limit : Nat)
  deriving DecidableEq, Repr

/-- Every candidate carries its complete replay, including intermediate rules. -/
structure Path where
  goal : Atom Claim
  steps : List (Step Claim)


/-- Source support is read from the actual replayed fact steps. -/
def Path.support (p : Path) : List String :=
  (p.steps.filterMap fun step => match step with
    | .fact f => some f.source.identity
    | .rule _ => none).eraseDups

def lawId := "nabt.grounded-passage.v1"
def law (scope : String) : Source := ⟨lawId, lawId, scope⟩
def record (scope id : String) : Source := ⟨id, id, scope⟩
def leaf (scope id : String) : Path :=
  let a : Atom Claim := ⟨.input id, true, scope⟩
  ⟨a, [.fact ⟨record scope id, a⟩]⟩

def derive (scope name : String) (head : Claim) (parents : List Path) : Path :=
  let goal : Atom Claim := ⟨head, true, scope⟩
  let r : Rule Claim := ⟨law scope, name, parents.map Path.goal, goal⟩
  ⟨goal, parents.flatMap Path.steps ++ [.rule r]⟩

/-- Witness of a sampled forward passage: three consecutive readings, the
middle exactly on the plane. It does not interpolate unobserved times. -/
def hits (gate : Int) (scale : Nat) : List Sample → List Nat
  | a :: b :: c :: rest =>
    let more := hits gate scale (b :: c :: rest)
    if a.x * scale < gate && b.x * scale == gate && c.x * scale > gate
      then b.minute :: more else more
  | _ => []

def candidates (i : Input) : List Path := Id.run do
  let newPath := derive i.scope
  let source := leaf i.scope
  let mut answers := []
  let mut crossings : List (Nat × Path) := []
  for f in i.fixes do
    for s in f.samples do
      let x := s.x * f.cmPerUnit
      let pos := newPath "position_cm" (.position s.minute x) [source f.id]
      answers := pos :: answers
      for m in i.maps do
        let delta := x - m.gateX * m.cmPerUnit
        let view := if i.facing == "forward" then delta else -delta
        let side := if view > 0 then "right" else if view < 0 then "left" else "at_gate"
        answers := newPath "observer_axis" (.side s.minute side) [pos, source m.id] ::
                   newPath "absolute_displacement" (.distance s.minute delta.natAbs) [pos, source m.id] :: answers
  for m in i.maps do
    for track in i.tracks do
      for t in hits (m.gateX * m.cmPerUnit) track.cmPerUnit track.samples do
        let hit := newPath "sampled_forward_passage" (.crossing t) [source m.id, source track.id]
        crossings := (t,hit) :: crossings
        answers := hit :: answers
  for p in i.permits do
    let bound := newPath "message_endpoint" (.deadline p.minute p.endpoint) [source p.id]
    answers := bound :: answers
    for (t,hit) in crossings do
      if t < p.minute then
        answers := newPath "strictly_before_endpoint" (.within t p.minute) [hit,bound] :: answers
  return answers.reverse

/-- Minimality is relative to the full profile-generated path family for the
same signed goal. Distinct incomparable alternatives are retained. -/
def strictSubsupport (xs ys : List String) : Bool :=
  xs.all ys.contains && !(ys.all xs.contains)

def minimalChecked (program : Program Claim) (paths : List Path) : List Path :=
  let admitted := paths.filter fun p => accepts program p.goal p.steps
  admitted.filter fun p => !(admitted.any fun q =>
    q.goal == p.goal && strictSubsupport q.support p.support)

/-- Exact coverage relative to the enumerated candidate family, including
the reverse implication: every checked inclusion-minimal path is returned. -/
theorem mem_minimalChecked_iff (program : Program Claim) (paths : List Path) (p : Path) :
    p ∈ minimalChecked program paths ↔
      p ∈ paths ∧ accepts program p.goal p.steps = true ∧
      ∀ q ∈ paths, accepts program q.goal q.steps = true → q.goal = p.goal →
        strictSubsupport q.support p.support = false := by
  simp [minimalChecked, List.any_eq_false]
  grind

theorem reported_derivable (program : Program Claim) (paths : List Path) (p : Path)
    (reported : p ∈ minimalChecked program paths) : Derivable program p.goal := by
  have admitted := (List.mem_filter.mp reported).1
  exact accepts_sound program p.goal p.steps (List.mem_filter.mp admitted).2

theorem reported_no_smaller_checked_path (program : Program Claim) (paths : List Path) (p q : Path)
    (reported : p ∈ minimalChecked program paths) (candidate : q ∈ paths)
    (checked : accepts program q.goal q.steps = true) (same : q.goal = p.goal) :
    strictSubsupport q.support p.support = false := by
  have minimal := (List.mem_filter.mp reported).2
  simp only [Bool.not_eq_true', List.any_eq_false] at minimal
  have excluded := minimal q (List.mem_filter.mpr ⟨candidate, checked⟩)
  simpa [same] using excluded

end Nabt.GroundedPassage
