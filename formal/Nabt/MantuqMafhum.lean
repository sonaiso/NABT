import Nabt.Shakhsiyya1Rules
import Nabt.Shakhsiyya3Rules
import Nabt.ArabicCoverage
import Nabt.AwamilInventory

/-! Source-relative meaning certificates over every supplied reading.
Premises are explicit. The adapter must obtain them by replaying the source;
this theorem does not prove the free reader's enumeration or projection.
Logical consequence is separate from a source's classification of a specific
Arabic occurrence as iqtida, ishara, agreement, or opposition. -/
namespace Nabt.MantuqMafhum
open SourceSemantics

def lawId := "nabt.mantuq-mafhum-consequence.v1"

inductive Proof where
  | premise (index : Nat)
  | left (child : Proof)
  | right (child : Proof)
  | pair (left right : Proof)
  | apply (rule argument : Proof)
  deriving DecidableEq, Repr

def infer (premises : List Formula) : Proof → Option Formula
  | .premise n => premises[n]?
  | .left p => do
    match ← infer premises p with
    | .both a _ => some a
    | _ => none
  | .right p => do
    match ← infer premises p with
    | .both _ b => some b
    | _ => none
  | .pair p q => return .both (← infer premises p) (← infer premises q)
  | .apply p q => do
    match ← infer premises p with
    | .implies a b => if (← infer premises q) = a then some b else none
    | _ => none

def Proof.usesImplication : Proof → Bool
  | .premise _ => false
  | .left p | .right p => p.usesImplication
  | .pair p q => p.usesImplication || q.usesImplication
  | .apply _ _ => true

def PremisesHold (premises : List Formula) (model : String → List String → Prop)
    (env : Nat → String) : Prop := ∀ f ∈ premises, f.meaning model env

theorem infer_sound (premises : List Formula) (p : Proof) (f : Formula)
    (model : String → List String → Prop) (env : Nat → String)
    (holds : PremisesHold premises model env) (checked : infer premises p = some f) :
    f.meaning model env := by
  induction p generalizing f with
  | premise n =>
    exact holds f (List.mem_of_getElem? (by simpa [infer] using checked))
  | left p ih =>
    cases hp : infer premises p with
    | none => simp [infer, hp] at checked
    | some child =>
      cases child with
      | atom c args => simp [infer, hp] at checked
      | implies a b => simp [infer, hp] at checked
      | both a b =>
        have eq : a = f := by simpa [infer, hp] using checked
        subst f
        exact (ih (.both a b) hp).1
  | right p ih =>
    cases hp : infer premises p with
    | none => simp [infer, hp] at checked
    | some child =>
      cases child with
      | atom c args => simp [infer, hp] at checked
      | implies a b => simp [infer, hp] at checked
      | both a b =>
        have eq : b = f := by simpa [infer, hp] using checked
        subst f
        exact (ih (.both a b) hp).2
  | pair p q ip iq =>
    cases hp : infer premises p with
    | none => simp [infer, hp] at checked
    | some a =>
      cases hq : infer premises q with
      | none => simp [infer, hp, hq] at checked
      | some b =>
        have eq : Formula.both a b = f := by simpa [infer, hp, hq] using checked
        subst f
        exact ⟨ip a hp, iq b hq⟩
  | apply p q ip iq =>
    cases hp : infer premises p with
    | none => simp [infer, hp] at checked
    | some child =>
      cases child with
      | atom c args => simp [infer, hp] at checked
      | both a b => simp [infer, hp] at checked
      | implies a b =>
        cases hq : infer premises q with
        | none => simp [infer, hp, hq] at checked
        | some argument =>
          by_cases same : argument = a
          · subst argument
            have eq : b = f := by simpa [infer, hp, hq] using checked
            subst f
            exact ip (.implies a b) hp (iq a hq)
          · simp [infer, hp, hq, same] at checked

/-- There is no inverse-implication rule and no default-negation rule. -/
theorem no_premise_no_inference (p : Proof) : infer [] p = none := by
  induction p with
  | premise n => simp [infer]
  | left p ih => simp [infer, ih]
  | right p ih => simp [infer, ih]
  | pair p q ip _ => simp [infer, ip]
  | apply p q ip _ => simp [infer, ip]

structure Reading where
  binding : Binding
  premises : Option (List Formula)
  proof : Proof
  deriving DecidableEq, Repr

def Reading.result (r : Reading) : Option Formula := do
  infer (← r.premises) r.proof
def Reading.candidate (r : Reading) : Candidate Formula := ⟨r.binding, r.result⟩
def common (expected : Binding) (readings : List Reading) : Option Formula :=
  consensus expected (readings.map Reading.candidate)

theorem common_each (expected : Binding) (readings : List Reading) (f : Formula)
    (accepted : common expected readings = some f) (r : Reading) (member : r ∈ readings) :
    r.binding = expected ∧ r.result = some f := by
  exact (consensus_all expected _ f accepted).2 r.candidate
    (List.mem_map.mpr ⟨r, member, rfl⟩)

theorem common_entails (expected : Binding) (readings : List Reading) (f : Formula)
    (accepted : common expected readings = some f) (r : Reading) (member : r ∈ readings)
    (premises : List Formula) (complete : r.premises = some premises)
    (model : String → List String → Prop) (env : Nat → String)
    (holds : PremisesHold premises model env) : f.meaning model env := by
  have checked := (common_each expected readings f accepted r member).2
  have inferred : infer premises r.proof = some f := by
    simpa [Reading.result, complete] using checked
  exact infer_sound premises r.proof f model env holds inferred

theorem incomplete_blocks (expected : Binding) (readings : List Reading)
    (r : Reading) (member : r ∈ readings) (incomplete : r.premises = none) :
    common expected readings = none := by
  apply incomplete_reading_blocks expected _ r.candidate
    (List.mem_map.mpr ⟨r, member, rfl⟩)
  simp [Reading.candidate, Reading.result, incomplete]

theorem binding_change_blocks (expected : Binding) (readings : List Reading)
    (r : Reading) (member : r ∈ readings) (changed : r.binding ≠ expected) :
    common expected readings = none :=
  changed_binding_blocks expected _ r.candidate
    (List.mem_map.mpr ⟨r, member, rfl⟩) changed

/-- This is the missing enumeration premise made explicit. It is not claimed
for the existing Python free reader. Coverage of a witness does not follow
merely from agreeing on all supplied witnesses. -/
theorem common_covers_reference (expected : Binding) (readings : List Reading)
    (reference : Reading → Prop) (covers : ∀ r, reference r → r ∈ readings)
    (f : Formula) (accepted : common expected readings = some f)
    (r : Reading) (licensed : reference r) : r.binding = expected ∧ r.result = some f :=
  common_each expected readings f accepted r (covers r licensed)

/-- Qualified claims retain their entire record as atom identity in the
adapter; changing a time, referent, force, sign or scope changes the atom. -/
theorem different_atom_not_same_consequence (a b : String) (different : a ≠ b) :
    infer [.atom a []] (.premise 0) ≠ some (.atom b []) := by
  simp [infer, different]

def literalFormula (scope : String) (a : VerifiedReading.Literal) : Formula :=
  .atom a.predicate ((.name scope) :: (.name (if a.positive then "positive" else "negative")) ::
    a.arguments.map Term.name)

def conjunction : List Formula → Formula
  | [] => .atom "nabt.empty-conjunction-not-admitted" []
  | [f] => f
  | f :: g :: fs => .both f (conjunction (g :: fs))

def clauseFormula (scope : String) : VerifiedReading.Clause → Formula
  | .fact a => literalFormula scope a
  | .rule body head => .implies (conjunction (body.map (literalFormula scope))) (literalFormula scope head)

def groundModel (v : VerifiedReading.GroundAtom → Prop) (concept : String) (args : List String) : Prop :=
  match args with
  | scope :: "positive" :: rest => v ⟨(concept, rest), true, scope⟩
  | scope :: "negative" :: rest => v ⟨(concept, rest), false, scope⟩
  | _ => False

theorem literal_meaning (scope : String) (a : VerifiedReading.Literal)
    (v : VerifiedReading.GroundAtom → Prop) (env : Nat → String) :
    (literalFormula scope a).meaning (groundModel v) env ↔ v (a.lower scope) := by
  cases a with
  | mk predicate arguments positive =>
    cases positive <;> simp [literalFormula, Formula.meaning, groundModel,
      Term.eval, List.map_map, Function.comp_def, VerifiedReading.Literal.lower]

theorem conjunction_meaning (fs : List Formula) (nonempty : fs ≠ [])
    (model : String → List String → Prop) (env : Nat → String) :
    (conjunction fs).meaning model env ↔ ∀ f ∈ fs, f.meaning model env := by
  induction fs with
  | nil => contradiction
  | cons f fs ih =>
    cases fs with
    | nil => simp [conjunction]
    | cons g gs =>
      rw [show conjunction (f :: g :: gs) = .both f (conjunction (g :: gs)) from rfl]
      simp only [Formula.meaning, ih (by simp), List.mem_cons, forall_eq_or_imp]

theorem source_premises_hold (s : VerifiedReading.Source) (cs : List VerifiedReading.Clause)
    (reading : VerifiedReading.Reads s cs) (v : VerifiedReading.GroundAtom → Prop)
    (sourceMeaning : VerifiedReading.SourceMeaning s v) (env : Nat → String) :
    PremisesHold (cs.map (clauseFormula s.scope)) (groundModel v) env := by
  have text : VerifiedReading.TextMeaning s cs v := by
    simpa [VerifiedReading.SourceMeaning, reading.2.2.2] using sourceMeaning
  intro f member
  obtain ⟨c, hc, eq⟩ := List.mem_map.mp member
  subst f
  cases c with
  | fact a => exact (literal_meaning s.scope a v env).mpr (text (.fact a) hc)
  | rule body head =>
    have valid := List.all_eq_true.mp reading.2.1 (.rule body head) hc
    have nonempty : body ≠ [] := by
      cases body with
      | nil => simp [VerifiedReading.Clause.valid] at valid
      | cons a as => simp
    change (conjunction (body.map (literalFormula s.scope))).meaning (groundModel v) env →
      (literalFormula s.scope head).meaning (groundModel v) env
    intro premise
    apply (literal_meaning s.scope head v env).mpr
    apply text (.rule body head) hc
    intro a ha
    apply (literal_meaning s.scope a v env).mp
    exact (conjunction_meaning _ (by simpa using nonempty) _ _).mp premise _
      (List.mem_map.mpr ⟨a, ha, rfl⟩)

theorem source_to_meaning_consequence (s : VerifiedReading.Source)
    (cs : List VerifiedReading.Clause) (reading : VerifiedReading.Reads s cs)
    (p : Proof) (f : Formula) (checked : infer (cs.map (clauseFormula s.scope)) p = some f)
    (v : VerifiedReading.GroundAtom → Prop) (sourceMeaning : VerifiedReading.SourceMeaning s v)
    (env : Nat → String) : f.meaning (groundModel v) env :=
  infer_sound _ p f _ env (source_premises_hold s cs reading v sourceMeaning env) checked

/-- Source admission, consequence, and grounded concept form one conditional
theorem. A reviewed interpretation's semantic adequacy remains a hypothesis;
attested bytes alone cannot prove that hypothesis. -/
theorem acquired_inference_grounded (b : Binding)
    (ss : List ClassicalLanguageEvidence.Source) (rs : List ThinkingRules.Information)
    (p : Proof) (f : Formula) (model : String → List String → Prop) (env : Nat → String)
    (adequate : ∀ i ∈ ThinkingRules.acquire b ss rs, i.proposition.meaning model env)
    (checked : infer ((ThinkingRules.acquire b ss rs).map (·.proposition)) p = some f) :
    Shakhsiyya1Rules.Grounded ⟨b, f⟩ model env := by
  apply infer_sound _ p f model env ?_ checked
  intro premise member
  obtain ⟨i, hi, eq⟩ := List.mem_map.mp member
  subst premise
  exact adequate i hi

end Nabt.MantuqMafhum
