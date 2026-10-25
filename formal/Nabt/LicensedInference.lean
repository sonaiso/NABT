import Nabt.VerifiedReading
import Nabt.BookCoverage

/-!
A finite generative surface grammar plus all-reading closure checking. Explicit
name labels, verb frames and signs are interpretation conventions, not world
facts. Source.scope carries an explicitly fixed discourse/time index. Omitted
condition subjects remain unresolved. Exactness concerns this grammar, not all
Arabic; generic semantic adequacy remains an independent premise.
-/
namespace Nabt.LicensedInference
open VerifiedReading SemanticInference

def lawId : String := "nabt.licensed-inference.v1"
inductive Person where
  | zayd | amr
  deriving DecidableEq, Repr
def Person.label : Person → String | .zayd => "زيد" | .amr => "عمرو"
def persons : List Person := [.zayd, .amr]
inductive Modifier where
  | none | front | behind | both
  deriving DecidableEq, Repr
def modifiers : List Modifier := [.none, .front, .behind, .both]
def Modifier.tokens : Modifier → List String
  | .none => [] | .front => ["أمامك"] | .behind => ["خلف", "الدار"]
  | .both => ["أمامك", "خلف", "الدار"]
def Modifier.arguments : Modifier → List String
  | .none => [] | .front => ["أمامك"] | .behind => ["خلف_الدار"]
  | .both => ["أمامك_خلف_الدار"]
inductive AtomForm where
  | knowing (person : Person) (positive : Bool)
  | walking (person : Person) (modifier : Modifier) (positive : Bool)
  deriving DecidableEq, Repr
def AtomForm.tokens : AtomForm → List String
  | .knowing n true => ["عرف", n.label, "الحق"]
  | .knowing n false => ["لم", "يعرف", n.label, "الحق"]
  | .walking n m true => ["سار", n.label] ++ m.tokens
  | .walking n m false => ["لم", "يسر", n.label] ++ m.tokens
def AtomForm.lower : AtomForm → Literal
  | .knowing n p => ⟨"عرف", [n.label, "الحق"], p⟩
  | .walking n m p => ⟨"سار", n.label :: m.arguments, p⟩
def atoms : List AtomForm :=
  persons.flatMap (fun n => [true, false].map (AtomForm.knowing n)) ++
  persons.flatMap (fun n => modifiers.flatMap (fun m => [true, false].map (AtomForm.walking n m)))
def readAtom (ts : List String) : Option AtomForm := atoms.find? (fun a => a.tokens == ts)
theorem atom_roundtrip (a : AtomForm) : readAtom a.tokens = some a := by
  cases a with
  | knowing n p => cases n <;> cases p <;> decide
  | walking n m p => cases n <;> cases m <;> cases p <;> decide
theorem atom_read_exact (ts : List String) (a : AtomForm) :
    readAtom ts = some a ↔ a.tokens = ts := by
  constructor
  · intro h
    have found := List.find?_some h
    simpa [readAtom, beq_iff_eq] using found
  · intro h; rw [← h]; exact atom_roundtrip a

inductive Order where
  | front | post
  deriving DecidableEq, Repr
def arrange (order : Order) (condition consequence : List String) : List String :=
  match order with
  | .front => ["إن"] ++ condition ++ consequence
  | .post => consequence ++ ["إن"] ++ condition
inductive Statement where
  | fact (atom : AtomForm)
  | conditional (order : Order) (conditionPerson : Person) (conditionPositive : Bool)
      (person : Person) (modifier : Modifier) (positive : Bool)
  | unresolved (order : Order) (conditionPositive : Bool)
      (person : Person) (modifier : Modifier) (positive : Bool)
  deriving DecidableEq, Repr
def Statement.tokens : Statement → List String
  | .fact a => a.tokens
  | .conditional order n p m md q => arrange order (AtomForm.knowing n p).tokens (AtomForm.walking m md q).tokens
  | .unresolved order p m md q => arrange order
      (if p then ["عرف", "الحق"] else ["لم", "يعرف", "الحق"]) (AtomForm.walking m md q).tokens
def Statement.lower : Statement → Option Clause
  | .fact a => some (.fact a.lower)
  | .conditional _ n p m md q => some (.rule [(AtomForm.knowing n p).lower] (AtomForm.walking m md q).lower)
  | .unresolved .. => none
def statements : List Statement :=
  atoms.map Statement.fact ++
  [Order.front, .post].flatMap (fun o => persons.flatMap (fun n => [true,false].flatMap (fun p =>
    persons.flatMap (fun m => modifiers.flatMap (fun md => [true,false].map
      (Statement.conditional o n p m md)))))) ++
  [Order.front, .post].flatMap (fun o => [true,false].flatMap (fun p =>
    persons.flatMap (fun m => modifiers.flatMap (fun md => [true,false].map
      (Statement.unresolved o p m md)))))
def readStatement (ts : List String) : Option Statement := statements.find? (fun a => a.tokens == ts)
set_option maxRecDepth 10000 in
set_option maxHeartbeats 3000000 in
theorem statement_roundtrip (s : Statement) : readStatement s.tokens = some s := by
  cases s with
  | fact a => cases a with
    | knowing n p => cases n <;> cases p <;> decide
    | walking n m p => cases n <;> cases m <;> cases p <;> decide
  | conditional o n p m md q =>
    cases o <;> cases n <;> cases p <;> cases m <;> cases md <;> cases q <;> decide
  | unresolved o p m md q =>
    cases o <;> cases p <;> cases m <;> cases md <;> cases q <;> decide
theorem statement_read_exact (ts : List String) (s : Statement) :
    readStatement ts = some s ↔ s.tokens = ts := by
  constructor
  · intro h
    have found := List.find?_some h
    simpa [readStatement, beq_iff_eq] using found
  · intro h; rw [← h]; exact statement_roundtrip s

/-- Only listed lexical spellings are mapped; wrong or unknown marks remain. -/
def canonicalToken : String → String
  | "زَيْدٌ" => "زيد" | "عَمْرٌو" => "عمرو"
  | "سَارَ" => "سار" | "عَرَفَ" => "عرف" | "الْحَقَّ" => "الحق"
  | "إِنْ" => "إن" | "لَمْ" => "لم" | "يَسِرْ" => "يسر" | "يَعْرِفْ" => "يعرف"
  | "أَمَامَكَ" => "أمامك" | "خَلْفَ" => "خلف" | "الدَّارِ" => "الدار"
  | "هَلْ" => "هل" | token => token
def asciiSpace (c : Char) : Bool := c == ' ' || c == '\t' || c == '\r' || c == '\n'
def tokens (text : String) : List String :=
  ((text.map (fun c => if asciiSpace c then ' ' else c)).splitOn " ").filterMap
    (fun t => if t == "" then none else some (canonicalToken t))
def splitSource (raw : List UInt8) : Option (List (List String)) := do
  let text ← String.fromUTF8? ⟨raw.toArray⟩
  let parts := (text.splitOn ".").map tokens
  let lines := if parts.getLast? = some [] then parts.dropLast else parts
  if lines.isEmpty || lines.any List.isEmpty then none else some lines

def readStatements : List (List String) → Option (List Statement)
  | [] => some []
  | line :: rest => do return (← readStatement line) :: (← readStatements rest)
theorem statements_read_exact (lines : List (List String)) (ss : List Statement) :
    readStatements lines = some ss ↔ ss.map Statement.tokens = lines := by
  induction lines generalizing ss with
  | nil => cases ss <;> simp [readStatements]
  | cons line rest ih =>
    cases ss with
    | nil =>
      cases h : readStatement line <;> cases g : readStatements rest <;> simp [readStatements, h, g]
    | cons s ss =>
      cases h : readStatement line with
      | none =>
        have miss : s.tokens ≠ line := by
          intro eq
          have := (statement_read_exact line s).mpr eq
          simp [h] at this
        simp [readStatements, h, miss]
      | some a =>
        have ha := (statement_read_exact line a).mp h
        cases g : readStatements rest with
        | none =>
          have miss : ss.map Statement.tokens ≠ rest := by
            intro eq
            have := (ih ss).mpr eq
            simp [g] at this
          simp [readStatements, h, g, miss]
        | some tail =>
          have ht := (ih tail).mp g
          have unique : s.tokens = line ↔ s = a := by
            constructor
            · intro eq
              have hs := (statement_read_exact line s).mpr eq
              exact Option.some.inj (hs.symm.trans h)
            · intro eq; subst s; exact ha
          have uniqueTail : ss.map Statement.tokens = rest ↔ ss = tail := by
            constructor
            · intro eq
              have hs := (ih ss).mpr eq
              exact Option.some.inj (hs.symm.trans g)
            · intro eq; subst ss; exact ht
          simp only [readStatements, h, g, Option.pure_def, List.map_cons, List.cons.injEq]
          rw [unique, uniqueTail]
          simp [eq_comm]

/-- Generative syntax specification; no call to the source reader. -/
def LicensedSource (raw : List UInt8) (ss : List Statement) : Prop :=
  ∃ lines, splitSource raw = some lines ∧ ss.map Statement.tokens = lines
def readSource (raw : List UInt8) : Option (List Statement) := do readStatements (← splitSource raw)
theorem source_read_exact (raw : List UInt8) (ss : List Statement) :
    readSource raw = some ss ↔ LicensedSource raw ss := by
  cases h : splitSource raw with
  | none => simp [readSource, LicensedSource, h]
  | some lines => simp [readSource, LicensedSource, h, statements_read_exact]
def trimProfile (text : String) : String :=
  String.ofList (((text.toList.dropWhile asciiSpace).reverse.dropWhile asciiSpace).reverse)
def queryTokens (raw : List UInt8) : Option (List String) := do
  let text ← String.fromUTF8? ⟨raw.toArray⟩
  match (trimProfile text).splitOn "؟" with
  | [body, ""] => match tokens body with | "هل" :: rest => some rest | _ => none
  | _ => none
def readQuery (raw : List UInt8) : Option AtomForm := do readAtom (← queryTokens raw)
def LicensedQuery (raw : List UInt8) (a : AtomForm) : Prop := queryTokens raw = some a.tokens
theorem query_read_exact (raw : List UInt8) (a : AtomForm) :
    readQuery raw = some a ↔ LicensedQuery raw a := by
  cases h : queryTokens raw with
  | none => simp [readQuery, LicensedQuery, h]
  | some ts =>
    simp only [readQuery, LicensedQuery, h, Option.some.injEq]
    change readAtom ts = some a ↔ ts = a.tokens
    rw [atom_read_exact]
    exact eq_comm
def lowerStatements : List Statement → Option (List Clause)
  | [] => some []
  | s :: rest => do return (← s.lower) :: (← lowerStatements rest)
structure Reading where
  clauses : List Clause
  query : Literal
  deriving DecidableEq, Repr
def read (source query : List UInt8) : Option Reading := do
  let ss ← readSource source
  let a ← readQuery query
  return ⟨← lowerStatements ss, a.lower⟩
def LicensedReading (source query : List UInt8) (r : Reading) : Prop :=
  ∃ ss a, LicensedSource source ss ∧ LicensedQuery query a ∧
    lowerStatements ss = some r.clauses ∧ a.lower = r.query
/-- Exactness for the declared generative fragment, not all Arabic. -/
theorem reading_exact (source query : List UInt8) (r : Reading) :
    read source query = some r ↔ LicensedReading source query r := by
  constructor
  · intro accepted
    cases hs : readSource source with
    | none => simp [read, hs] at accepted
    | some ss =>
      cases hq : readQuery query with
      | none => simp [read, hs, hq] at accepted
      | some a =>
        cases hl : lowerStatements ss with
        | none => simp [read, hs, hq, hl] at accepted
        | some cs =>
          have eq : Reading.mk cs a.lower = r := by simpa [read, hs, hq, hl] using accepted
          subst r
          exact ⟨ss, a, (source_read_exact source ss).mp hs,
            (query_read_exact query a).mp hq, hl, rfl⟩
  · rintro ⟨ss, a, sourceOK, queryOK, lowerOK, resultOK⟩
    have hs := (source_read_exact source ss).mpr sourceOK
    have hq := (query_read_exact query a).mpr queryOK
    cases r
    simp_all [read]

structure Certificate where
  reading : Reading
  steps : List GroundStep
  known : List GroundAtom
  cleanSteps : List GroundStep
  cleanKnown : List GroundAtom

def checkRow (source : VerifiedReading.Source) (expected : Reading) (c : Certificate) : Bool :=
  decide (c.reading = expected) && checkClosure (lower source expected.clauses) c.steps c.known &&
  checkClosure (clean (lower source expected.clauses) c.known) c.cleanSteps c.cleanKnown

def rowEvidence (source : VerifiedReading.Source) (c : Certificate) : Evidence :=
  let a := c.reading.query.lower source.scope
  ⟨decide (a ∈ c.known), decide (a.opposite ∈ c.known),
    decide (a ∈ c.cleanKnown), decide (a.opposite ∈ c.cleanKnown)⟩

def checkRows (source : VerifiedReading.Source) : List Reading → List Certificate → Bool
  | [], [] => true
  | r :: rs, c :: cs => checkRow source r c && checkRows source rs cs
  | _, _ => false

theorem checked_row_exact (source : VerifiedReading.Source) (expected : Reading) (c : Certificate)
    (checked : checkRow source expected c = true) :
    c.reading = expected ∧
    ((rowEvidence source c).positive = true ↔ Derivable (lower source expected.clauses) (expected.query.lower source.scope)) ∧
    ((rowEvidence source c).negative = true ↔ Derivable (lower source expected.clauses) (expected.query.lower source.scope).opposite) ∧
    ((rowEvidence source c).cleanPositive = true ↔ Derivable (clean (lower source expected.clauses) c.known) (expected.query.lower source.scope)) ∧
    ((rowEvidence source c).cleanNegative = true ↔ Derivable (clean (lower source expected.clauses) c.known) (expected.query.lower source.scope).opposite) := by
  have h : (c.reading = expected ∧ checkClosure (lower source expected.clauses) c.steps c.known = true) ∧
      checkClosure (clean (lower source expected.clauses) c.known) c.cleanSteps c.cleanKnown = true := by
    simpa [checkRow] using checked
  refine ⟨h.1.1, ?_, ?_, ?_, ?_⟩ <;> simp only [rowEvidence, h.1.1, decide_eq_true_eq]
  · exact checked_closure_exact _ _ _ h.1.2 _
  · exact checked_closure_exact _ _ _ h.1.2 _
  · exact checked_closure_exact _ _ _ h.2 _
  · exact checked_closure_exact _ _ _ h.2 _

theorem checked_rows_preserve_readings (source : VerifiedReading.Source) (rs : List Reading) (cs : List Certificate)
    (checked : checkRows source rs cs = true) : cs.map Certificate.reading = rs := by
  induction rs generalizing cs with
  | nil => cases cs <;> simp_all [checkRows]
  | cons r rs ih =>
    cases cs with
    | nil => simp [checkRows] at checked
    | cons c cs =>
      have h := Bool.and_eq_true_iff.mp checked
      simp [(checked_row_exact source r c h.1).1, ih cs h.2]

theorem checked_rows_each (source : VerifiedReading.Source) (rs : List Reading) (cs : List Certificate)
    (checked : checkRows source rs cs = true) (c : Certificate) (member : c ∈ cs) :
    checkRow source c.reading c = true := by
  induction rs generalizing cs with
  | nil => cases cs <;> simp_all [checkRows]
  | cons r rs ih =>
    cases cs with
    | nil => simp [checkRows] at checked
    | cons first rest =>
      have h := Bool.and_eq_true_iff.mp checked
      rcases List.mem_cons.mp member with same | tail
      · subst first
        have eq := (checked_row_exact source r c h.1).1
        simpa [eq] using h.1
      · exact ih rest h.2 tail

/-- Claim binding and source-derived reading admission are checked in the kernel. -/
def verify (expected claimed : VerifiedReading.Source) (query claimedQuery : List UInt8)
    (cs : List Certificate) : Bool :=
  decide (claimed = expected ∧ claimedQuery = query) &&
  match read expected.raw query with
  | none => false
  | some r => checkRows expected [r] cs

theorem verified_execution (expected claimed : VerifiedReading.Source)
    (query claimedQuery : List UInt8) (cs : List Certificate)
    (accepted : verify expected claimed query claimedQuery cs = true) :
    claimed = expected ∧ claimedQuery = query ∧ ∃ r,
      LicensedReading expected.raw query r ∧ cs.map Certificate.reading = [r] ∧
      checkRows expected [r] cs = true := by
  have h := Bool.and_eq_true_iff.mp accepted
  have binding : claimed = expected ∧ claimedQuery = query := of_decide_eq_true h.1
  refine ⟨binding.1, binding.2, ?_⟩
  cases hr : read expected.raw query with
  | none => simp [hr] at h
  | some r =>
    have checked : checkRows expected [r] cs = true := by simpa [hr] using h.2
    exact ⟨r, (reading_exact expected.raw query r).mp hr,
      checked_rows_preserve_readings expected [r] cs checked, checked⟩

theorem changed_source_rejected (expected claimed : VerifiedReading.Source)
    (query claimedQuery : List UInt8) (cs : List Certificate) (different : claimed ≠ expected) :
    verify expected claimed query claimedQuery cs = false := by simp [verify, different]

theorem changed_query_rejected (expected claimed : VerifiedReading.Source)
    (query claimedQuery : List UInt8) (cs : List Certificate) (different : claimedQuery ≠ query) :
    verify expected claimed query claimedQuery cs = false := by simp [verify, different]

/-- No external truth follows without independently supplied text meaning. -/
theorem execution_entails (expected claimed : VerifiedReading.Source)
    (query claimedQuery : List UInt8) (cs : List Certificate)
    (accepted : verify expected claimed query claimedQuery cs = true)
    (c : Certificate) (member : c ∈ cs) (positive : (rowEvidence expected c).positive = true)
    (meaning : GroundAtom → Prop) (text : TextMeaning expected c.reading.clauses meaning) :
    meaning (c.reading.query.lower expected.scope) := by
  obtain ⟨_, _, r, _, _, checked⟩ := verified_execution expected claimed query claimedQuery cs accepted
  have checkedRow := checked_rows_each expected [r] cs checked c member
  have derived := (checked_row_exact expected c.reading c checkedRow).2.1.mp positive
  have model := lowering_preserves_meaning expected c.reading.clauses meaning text
  exact SemanticInference.model_sound _ meaning model.1 model.2 derived

/-- Exact aggregate consequence requires independently established parsing and
meaning adequacy; neither is manufactured from hashes or labels. -/
theorem compositional_answers_exact (source : VerifiedReading.Source) (rows : List Reading) (cs : List Certificate)
    (licensed : Reading → Prop) (consequence : Reading → Prop)
    (parseExact : ∀ r, r ∈ rows ↔ licensed r)
    (checked : checkRows source rows cs = true)
    (meaningExact : ∀ r, licensed r →
      (Derivable (lower source r.clauses) (r.query.lower source.scope) ↔ consequence r)) :
    ((∃ c ∈ cs, (rowEvidence source c).positive = true) ↔ ∃ r, licensed r ∧ consequence r) ∧
    (((∃ c, c ∈ cs) ∧ ∀ c ∈ cs, (rowEvidence source c).positive = true) ↔
      (∃ r, licensed r) ∧ ∀ r, licensed r → consequence r) := by
  have identities := checked_rows_preserve_readings source rows cs checked
  have membership : ∀ r, r ∈ rows ↔ ∃ c ∈ cs, c.reading = r := by
    intro r; rw [← identities]; simp
  have each : ∀ c ∈ cs, (rowEvidence source c).positive = true ↔ consequence c.reading := by
    intro c member
    have row := checked_rows_each source rows cs checked c member
    exact (checked_row_exact source c.reading c row).2.1.trans
      (meaningExact c.reading ((parseExact _).mp ((membership _).mpr ⟨c, member, rfl⟩)))
  constructor
  · constructor
    · rintro ⟨c, member, positive⟩
      exact ⟨c.reading, (parseExact _).mp ((membership _).mpr ⟨c, member, rfl⟩), (each c member).mp positive⟩
    · rintro ⟨r, license, follows⟩
      obtain ⟨c, member, eq⟩ := (membership r).mp ((parseExact r).mpr license)
      exact ⟨c, member, (each c member).mpr (by simpa [eq] using follows)⟩
  · constructor
    · rintro ⟨⟨c, member⟩, every⟩
      refine ⟨⟨c.reading, (parseExact _).mp ((membership _).mpr ⟨c, member, rfl⟩)⟩, ?_⟩
      intro r license
      obtain ⟨d, included, eq⟩ := (membership r).mp ((parseExact r).mpr license)
      exact eq ▸ (each d included).mp (every d included)
    · rintro ⟨⟨r, license⟩, every⟩
      obtain ⟨c, member, _⟩ := (membership r).mp ((parseExact r).mpr license)
      refine ⟨⟨c, member⟩, ?_⟩
      intro d included
      exact (each d included).mpr (every d.reading ((parseExact _).mp ((membership _).mpr ⟨d, included, rfl⟩)))

structure Aggregate where
  credulousPositive : Bool
  credulousNegative : Bool
  skepticalPositive : Bool
  skepticalNegative : Bool
  credulousCleanPositive : Bool
  credulousCleanNegative : Bool
  skepticalCleanPositive : Bool
  skepticalCleanNegative : Bool
  withinReadingConflict : Bool
  crossReadingOpposition : Bool
  deriving DecidableEq, Repr

def aggregate (es : List Evidence) : Aggregate :=
  let ne := !es.isEmpty
  ⟨es.any (·.positive), es.any (·.negative), ne && es.all (·.positive), ne && es.all (·.negative),
   es.any (·.cleanPositive), es.any (·.cleanNegative), ne && es.all (·.cleanPositive), ne && es.all (·.cleanNegative),
   es.any (fun e => e.positive && e.negative),
   es.zipIdx.any (fun (a,i) => es.zipIdx.any (fun (b,j) => i != j && a.positive && b.negative))⟩

def Aggregate.status (a : Aggregate) : String :=
  if a.withinReadingConflict then "CONFLICT"
  else if a.crossReadingOpposition then "DISAGREEMENT"
  else if a.skepticalCleanPositive && !a.credulousNegative then "SUPPORTED"
  else if a.skepticalCleanNegative && !a.credulousPositive then "REFUTED"
  else if !a.credulousPositive && !a.credulousNegative then "UNKNOWN"
  else "DEFER"

theorem empty_readings_not_skeptical : (aggregate []).skepticalPositive = false ∧
    (aggregate []).skepticalNegative = false := by decide

theorem skeptical_positive_exact (es : List Evidence) :
    (aggregate es).skepticalPositive = true ↔ es ≠ [] ∧ ∀ e ∈ es, e.positive = true := by
  simp [aggregate]

theorem credulous_positive_exact (es : List Evidence) :
    (aggregate es).credulousPositive = true ↔ ∃ e ∈ es, e.positive = true := by
  simp [aggregate]

end Nabt.LicensedInference
