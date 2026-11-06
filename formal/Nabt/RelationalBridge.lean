import Nabt.QualifiedInference

/-!
Source-bound, graded relational licensing. The source's controlled predicates
and the selected reading are explicit interpreted premises, not discoveries
about unrestricted Arabic or the physical world. VerifiedReading validates
the original bytes and complete full/clean closures. QualifiedInference owns
signed premise checks. Neither retrieval scores nor caller-selected lists of
requirements enter this law. Lexical rows are a bounded reviewed domain.
-/
namespace Nabt.RelationalBridge
open VerifiedReading

def lawId : String := "nabt.relational-bridge.v1"

inductive Reading where
  | yellowPast | yellowParticiple | age | magnitude
  deriving DecidableEq, Repr

def readings : List Reading := [.yellowPast, .yellowParticiple, .age, .magnitude]

def Reading.label : Reading → String
  | .yellowPast => "yellowing_past"
  | .yellowParticiple => "yellowing_participle"
  | .age => "growth_age"
  | .magnitude => "growth_magnitude"

def Reading.sense : Reading → String
  | .yellowPast | .yellowParticiple => "اصفرار"
  | .age => "كبر_السن"
  | .magnitude => "عظم"

def Reading.spellings : Reading → List String
  | .yellowPast => ["اصفرّ", "اِصْفَرَّ", "اصفرَّ", "اصفر"]
  | .yellowParticiple => ["مُصْفَرّ", "مصفرّ", "مصفر"]
  | .age => ["كَبِرَ", "كبر"]
  | .magnitude => ["كَبُرَ", "كبر"]

def candidates (surface : String) : List Reading :=
  readings.filter (fun r => r.spellings.contains surface)

inductive Stage where
  | disposition | occurrence | causality
  deriving DecidableEq, Repr

structure Frame where
  reading : Reading
  stage : Stage
  occurrenceId : String
  entity : String
  kind : String
  property : String
  event : String
  time : String
  place : String
  cause : String
  start : Nat
  stop : Nat
  surface : String
  deriving DecidableEq, Repr

def delimiter (c : Char) : Bool :=
  c.isWhitespace || ([".", ",", "،", "؛", ":", "!", "؟", "«", "»", "(", ")", "\""].contains (String.singleton c))

/-- Character offsets, not byte offsets; Unicode scalars are kept unchanged. -/
def occurrenceBound (target : String) (f : Frame) : Bool :=
  let xs := target.toList
  f.start < f.stop && f.stop ≤ xs.length &&
  String.ofList ((xs.drop f.start).take (f.stop - f.start)) == f.surface &&
  (f.start == 0 || (xs[f.start - 1]?).any delimiter) &&
  (f.stop == xs.length || (xs[f.stop]?).any delimiter)

def atom (scope predicate left right : String) (positive : Bool := true) : GroundAtom :=
  ⟨(predicate, [left, right]), positive, scope⟩

abbrev Requirement := QualifiedInference.Requirement (String × List String)

def occurrenceAtom (scope : String) (f : Frame) := atom scope "وقوع" f.event f.entity
def causeAtom (scope : String) (f : Frame) := atom scope "دليل_سببي" f.cause f.event
def blockerAtom (scope : String) (f : Frame) := atom scope "مانع" f.event "قائم" false

def targetKey (target : String) : String :=
  "u_" ++ String.intercalate "_" (target.toList.map (fun c => toString c.toNat))

def positionKey (f : Frame) : String := "p_" ++ toString f.start ++ "_" ++ toString f.stop

def requirements (scope target : String) (f : Frame) : List Requirement :=
  [⟨.premise, atom scope "نص" f.occurrenceId (targetKey target)⟩,
   ⟨.premise, atom scope "موضع" f.occurrenceId (positionKey f)⟩,
   ⟨.premise, atom scope "عضوية" f.entity f.kind⟩,
   ⟨.premise, atom scope "قراءة" f.occurrenceId f.reading.label⟩,
   ⟨.premise, atom scope "حدث" f.occurrenceId f.event⟩,
   ⟨.premise, atom scope "معنى" f.event f.reading.sense⟩,
   ⟨.premise, atom scope "حامل" f.event f.entity⟩,
   ⟨.premise, atom scope "خاصية" f.entity f.property⟩,
   ⟨.premise, atom scope "يقبل" f.kind f.property⟩,
   ⟨.premise, atom scope "يحول" f.reading.sense f.property⟩,
   ⟨.premise, atom scope "قابلية" f.entity f.reading.sense⟩,
   ⟨.condition, atom scope "شروط" f.event "متحققة"⟩,
   ⟨.blockerAbsence, blockerAtom scope f⟩,
   ⟨.premise, atom scope "مكان" f.event f.place⟩,
   ⟨.premise, atom scope "زمان" f.event f.time⟩] ++
  (match f.stage with
   | .disposition => []
   | .occurrence => [⟨.premise, occurrenceAtom scope f⟩]
   | .causality => [⟨.premise, occurrenceAtom scope f⟩, ⟨.cause, causeAtom scope f⟩])

def kind (f : Frame) : QualifiedInference.Kind :=
  match f.stage with | .causality => .causal | _ => .direct

def check (s : Source) (q : List UInt8) (c : Certificate) (target : String) (f : Frame) : Bool :=
  verify s q c && occurrenceBound target f && (candidates f.surface).contains f.reading &&
  decide (QualifiedInference.assess (kind f) (requirements s.scope target f) c.known = .supported) &&
  decide (QualifiedInference.Present c.cleanKnown (requirements s.scope target f))

theorem check_exact (s : Source) (q : List UInt8) (c : Certificate) (target : String) (f : Frame) :
    check s q c target f = true ↔
      verify s q c = true ∧ occurrenceBound target f = true ∧
      f.reading ∈ candidates f.surface ∧
      QualifiedInference.assess (kind f) (requirements s.scope target f) c.known = .supported ∧
      QualifiedInference.Present c.cleanKnown (requirements s.scope target f) := by
  simp [check, and_assoc]

theorem licensed_source_exact (s : Source) (q : List UInt8) (c : Certificate)
    (target : String) (f : Frame) (h : check s q c target f = true) :
    c.source = s ∧ c.queryRaw = q ∧ Reads s c.clauses ∧ ReadsQuery q c.query :=
  (verified_parts s q c ((check_exact s q c target f).mp h).1).1

theorem licensed_obligation_derivable (s : Source) (q : List UInt8) (c : Certificate)
    (target : String) (f : Frame) (h : check s q c target f = true)
    (r : Requirement) (member : r ∈ requirements s.scope target f) :
    SemanticInference.Derivable (lower s c.clauses) r.atom := by
  have checked := (check_exact s q c target f).mp h
  have present := ((QualifiedInference.supported_exact _ _ _).mp checked.2.2.2.1).2.1 r member
  exact (checked_closure_exact _ _ _ (verified_parts s q c checked.1).2.1 r.atom).mp present

theorem missing_obligation_blocks (s : Source) (q : List UInt8) (c : Certificate)
    (target : String) (f : Frame) (r : Requirement)
    (member : r ∈ requirements s.scope target f) (missing : r.atom ∉ c.known) :
    check s q c target f ≠ true := by
  intro h
  exact QualifiedInference.missing_obligation_blocks _ _ _ r member missing
    ((check_exact s q c target f).mp h).2.2.2.1

theorem capability_does_not_supply_occurrence (s : Source) (q : List UInt8) (c : Certificate)
    (target : String) (f : Frame) (stage : f.stage ≠ .disposition)
    (missing : occurrenceAtom s.scope f ∉ c.known) : check s q c target f ≠ true := by
  apply missing_obligation_blocks s q c target f ⟨.premise, occurrenceAtom s.scope f⟩ _ missing
  cases hs : f.stage <;> simp_all [requirements]

theorem adjacency_and_time_do_not_supply_cause (s : Source) (q : List UInt8) (c : Certificate)
    (target : String) (f : Frame) (stage : f.stage = .causality)
    (missing : causeAtom s.scope f ∉ c.known) : check s q c target f ≠ true := by
  apply missing_obligation_blocks s q c target f ⟨.cause, causeAtom s.scope f⟩ _ missing
  simp [requirements, stage]

theorem licensed_blocker_explicitly_absent (s : Source) (q : List UInt8) (c : Certificate)
    (target : String) (f : Frame) (h : check s q c target f = true) :
    blockerAtom s.scope f ∈ c.known ∧ (blockerAtom s.scope f).opposite ∉ c.known := by
  have accepted := ((check_exact s q c target f).mp h).2.2.2.1
  have member : (⟨.blockerAbsence, blockerAtom s.scope f⟩ : Requirement) ∈ requirements s.scope target f := by
    simp [requirements]
  exact (QualifiedInference.blocker_requires_explicit_negative _ _ _ _ member rfl accepted).2

theorem opposed_obligation_blocks (s : Source) (q : List UInt8) (c : Certificate)
    (target : String) (f : Frame) (r : Requirement) (member : r ∈ requirements s.scope target f)
    (opposed : r.atom.opposite ∈ c.known) : check s q c target f ≠ true := by
  intro h
  exact QualifiedInference.opposite_obligation_blocks _ _ _ r member opposed
    ((check_exact s q c target f).mp h).2.2.2.1

theorem tainted_obligation_blocks (s : Source) (q : List UInt8) (c : Certificate)
    (target : String) (f : Frame) (r : Requirement) (member : r ∈ requirements s.scope target f)
    (missing : r.atom ∉ c.cleanKnown) : check s q c target f ≠ true := by
  intro h
  exact missing (((check_exact s q c target f).mp h).2.2.2.2 r member)

theorem changed_source_rejects_old_license (s : Source) (q : List UInt8) (c : Certificate)
    (target : String) (f : Frame) (changed : c.source ≠ s) : check s q c target f ≠ true := by
  intro h
  exact changed (licensed_source_exact s q c target f h).1

theorem vocalized_growth_readings_distinct :
    candidates "كَبِرَ" = [.age] ∧ candidates "كَبُرَ" = [.magnitude] ∧
    candidates "كبر" = [.age, .magnitude] := by decide

theorem yellowing_readings_distinct :
    candidates "اصفرّ" = [.yellowPast] ∧ candidates "مُصْفَرّ" = [.yellowParticiple] := by decide

end Nabt.RelationalBridge
