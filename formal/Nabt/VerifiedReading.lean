import Nabt.SemanticInference

/-!
Translation validation for `nabt.verified-ground-reading.v1`.
The language is canonical, ground, signed unary/binary Arabic-controlled Horn
text. A certificate proposes a reading, never authority. The checker compares
the whole original UTF-8 sequence with the concrete grammar, replays every
proof, and checks closure. This is per-execution validation, not a proof of the
Python proposer, unrestricted Arabic, or truth outside the source theory.
-/
namespace Nabt.VerifiedReading

def lawId : String := "nabt.verified-ground-reading.v1"

structure Literal where
  predicate : String
  arguments : List String
  positive : Bool
  deriving DecidableEq, Repr

def nameChar (c : Char) : Bool :=
  ('a' ≤ c && c ≤ 'z') || ('A' ≤ c && c ≤ 'Z') ||
  ('0' ≤ c && c ≤ '9') || c == '_' ||
  ('ء' ≤ c && c ≤ 'غ') || ('ف' ≤ c && c ≤ 'ي') ||
  ('ً' ≤ c && c ≤ 'ْ')

def validName (s : String) : Bool :=
  !s.isEmpty && s.toList.all nameChar &&
  !(["ليس", "هو", "إذا", "فإن", "و", "هل", "كل", "كان", "تعريف",
     "مفهوم", "علاقة", "فرد"].contains s)

def Literal.valid (a : Literal) : Bool :=
  validName a.predicate && a.arguments.all validName &&
  (a.arguments.length == 1 || a.arguments.length == 2)

def Literal.render (a : Literal) : String :=
  (if a.positive then "" else "ليس ") ++
  match a.arguments with
  | [subject] => subject ++ " هو " ++ a.predicate
  | [subject, object] => subject ++ " " ++ a.predicate ++ " " ++ object
  | _ => ""

def Literal.lower (scope : String) (a : Literal) : SemanticInference.Atom (String × List String) :=
  ⟨(a.predicate, a.arguments), a.positive, scope⟩

inductive Clause where
  | fact (atom : Literal)
  | rule (body : List Literal) (head : Literal)
  deriving DecidableEq, Repr

def Clause.valid : Clause → Bool
  | .fact a => a.valid
  | .rule body head => !body.isEmpty && body.all Literal.valid && head.valid

def Clause.render : Clause → String
  | .fact a => a.render ++ ".\n"
  | .rule body head => "إذا " ++ String.intercalate " و " (body.map Literal.render) ++
      " فإن " ++ head.render ++ ".\n"

def render (clauses : List Clause) : String := String.join (clauses.map Clause.render)

/-- Identity includes raw bytes, not just a digest. The revision label is not
an assertion of authenticity. -/
structure Source where
  identity : String
  revision : String
  scope : String
  raw : List UInt8
  deriving DecidableEq, Repr

def Source.lower (s : Source) : SemanticInference.Source := ⟨s.identity, s.revision, s.scope⟩
abbrev GroundProgram := SemanticInference.Program (String × List String)
abbrev GroundAtom := SemanticInference.Atom (String × List String)
abbrev GroundStep := SemanticInference.Step (String × List String)

def lower (s : Source) (clauses : List Clause) : GroundProgram where
  sources := [s.lower]
  facts := clauses.filterMap fun c => match c with
    | .fact a => some ⟨s.lower, a.lower s.scope⟩
    | .rule _ _ => none
  rules := clauses.filterMap fun c => match c with
    | .fact _ => none
    | .rule body head => some ⟨s.lower, c.render,
        body.map (Literal.lower s.scope), head.lower s.scope⟩

/-- Authoritative deterministic decoder for the controlled language. This is
independent of the untrusted Python proposer and of the renderer. -/
def readUnsigned (positive : Bool) : List String → Option Literal
  | [subject, middle, object] =>
    let a : Literal := if middle == "هو" then ⟨object, [subject], positive⟩
      else ⟨middle, [subject, object], positive⟩
    if a.valid then some a else none
  | _ => none

def readLiteral : List String → Option Literal
  | "ليس" :: rest => readUnsigned false rest
  | xs => readUnsigned true xs

def readClause (line : String) : Option Clause := do
  match line.splitOn " " with
  | "إذا" :: rest =>
    match rest.splitOn "فإن" with
    | [body, head] =>
      let premises ← (body.splitOn "و").mapM readLiteral
      let conclusion ← readLiteral head
      let c := Clause.rule premises conclusion
      if c.valid then some c else none
    | _ => none
  | xs => return .fact (← readLiteral xs)

def readSource (raw : List UInt8) : Option (List Clause) := do
  let text ← String.fromUTF8? ⟨raw.toArray⟩
  match (text.splitOn ".\n").reverse with
  | "" :: rest =>
    if rest.isEmpty then none else rest.reverse.mapM readClause
  | _ => none

def readQuery (raw : List UInt8) : Option Literal := do
  let text ← String.fromUTF8? ⟨raw.toArray⟩
  match text.splitOn "؟\n" with
  | [body, ""] =>
    match body.splitOn " " with
    | "هل" :: rest => readLiteral rest
    | _ => none
  | _ => none

/-- Concrete syntax is the image of the restricted canonical grammar.
No normalization, ignored suffix, variable or implicit declaration. -/
def Reads (s : Source) (clauses : List Clause) : Prop :=
  clauses ≠ [] ∧ clauses.all Clause.valid = true ∧
  s.raw = (render clauses).toUTF8.data.toList ∧ readSource s.raw = some clauses

instance (s : Source) (cs : List Clause) : Decidable (Reads s cs) := by
  unfold Reads
  infer_instance

def ReadsQuery (raw : List UInt8) (a : Literal) : Prop :=
  a.valid = true ∧ raw = ("هل " ++ a.render ++ "؟\n").toUTF8.data.toList ∧
  readQuery raw = some a

instance (raw : List UInt8) (a : Literal) : Decidable (ReadsQuery raw a) := by
  unfold ReadsQuery
  infer_instance

theorem reading_unique (s : Source) (left right : List Clause)
    (hl : Reads s left) (hr : Reads s right) : left = right := by
  exact Option.some.inj (hl.2.2.2.symm.trans hr.2.2.2)

theorem query_reading_unique (raw : List UInt8) (left right : Literal)
    (hl : ReadsQuery raw left) (hr : ReadsQuery raw right) : left = right := by
  exact Option.some.inj (hl.2.2.symm.trans hr.2.2)

/-- Closure covers all admitted clauses, including those omitted from the
trace. Exhausted proof search therefore cannot manufacture UNKNOWN. -/
def Closed (p : GroundProgram) (known : List GroundAtom) : Prop :=
  p.facts.all (fun f => decide (SemanticInference.FactAdmitted p f → f.atom ∈ known)) = true ∧
  p.rules.all (fun r => decide (SemanticInference.RuleAdmitted p r →
    (∀ a ∈ r.body, a ∈ known) → r.head ∈ known)) = true

instance (p : GroundProgram) (known : List GroundAtom) : Decidable (Closed p known) := by
  unfold Closed
  infer_instance

def checkClosure (p : GroundProgram) (steps : List GroundStep)
    (known : List GroundAtom) : Bool :=
  decide (SemanticInference.replay p [] steps = some known ∧ Closed p known)

theorem closed_complete (p : GroundProgram) (known : List GroundAtom)
    (closed : Closed p known) {a : GroundAtom} (derived : SemanticInference.Derivable p a) :
    a ∈ known := by
  induction derived with
  | fact f admitted => exact (of_decide_eq_true (List.all_eq_true.mp closed.1 f admitted.1)) admitted
  | rule r admitted _ ih => exact (of_decide_eq_true (List.all_eq_true.mp closed.2 r admitted.1)) admitted ih

theorem checked_closure_exact (p : GroundProgram) (steps : List GroundStep)
    (known : List GroundAtom) (checked : checkClosure p steps known = true)
    (a : GroundAtom) : a ∈ known ↔ SemanticInference.Derivable p a := by
  have h := of_decide_eq_true checked
  constructor
  · exact SemanticInference.replay_sound p steps [] known (by simp) h.1 a
  · exact closed_complete p known h.2

/-- Preserve both signs in the original theory; block conflicted atoms in
the clean subtheory, using NABT's existing clean-proof law. -/
def blocked (known : List GroundAtom) (a : GroundAtom) : Bool :=
  decide (a ∈ known ∧ a.opposite ∈ known)

def clean (p : GroundProgram) (known : List GroundAtom) : GroundProgram :=
  SemanticInference.cleanProgram p (blocked known)

structure Certificate where
  source : Source
  queryRaw : List UInt8
  clauses : List Clause
  query : Literal
  steps : List GroundStep
  known : List GroundAtom
  cleanSteps : List GroundStep
  cleanKnown : List GroundAtom

def verify (expected : Source) (queryRaw : List UInt8) (c : Certificate) : Bool :=
  decide (c.source = expected ∧ c.queryRaw = queryRaw ∧
    Reads expected c.clauses ∧ ReadsQuery queryRaw c.query) &&
  checkClosure (lower expected c.clauses) c.steps c.known &&
  checkClosure (clean (lower expected c.clauses) c.known) c.cleanSteps c.cleanKnown

theorem verified_parts (s : Source) (q : List UInt8) (c : Certificate)
    (checked : verify s q c = true) :
    (c.source = s ∧ c.queryRaw = q ∧ Reads s c.clauses ∧ ReadsQuery q c.query) ∧
    checkClosure (lower s c.clauses) c.steps c.known = true ∧
    checkClosure (clean (lower s c.clauses) c.known) c.cleanSteps c.cleanKnown = true := by
  simp only [verify, Bool.and_eq_true_iff, decide_eq_true_eq] at checked
  exact ⟨checked.1.1, checked.1.2, checked.2⟩

theorem verified_source_exact (s : Source) (q : List UInt8) (c : Certificate)
    (checked : verify s q c = true) :
    c.source = s ∧ s.raw = (render c.clauses).toUTF8.data.toList := by
  have h := (verified_parts s q c checked).1
  exact ⟨h.1, h.2.2.1.2.2.1⟩

theorem changed_source_rejects (s : Source) (q : List UInt8) (c : Certificate)
    (different : c.source ≠ s) : verify s q c = false := by
  cases h : verify s q c with
  | false => rfl
  | true => exact False.elim (different (verified_source_exact s q c h).1)

theorem changed_query_rejects (s : Source) (q : List UInt8) (c : Certificate)
    (different : c.queryRaw ≠ q) : verify s q c = false := by
  cases h : verify s q c with
  | false => rfl
  | true => exact False.elim (different (verified_parts s q c h).1.2.1)

structure Evidence where
  positive : Bool
  negative : Bool
  cleanPositive : Bool
  cleanNegative : Bool
  deriving DecidableEq, Repr

def evidence (s : Source) (c : Certificate) : Evidence :=
  let a := c.query.lower s.scope
  ⟨decide (a ∈ c.known), decide (a.opposite ∈ c.known),
   decide (a ∈ c.cleanKnown), decide (a.opposite ∈ c.cleanKnown)⟩

def execute (s : Source) (q : List UInt8) (c : Certificate) : Option Evidence :=
  if verify s q c then some (evidence s c) else none

/-- Contract of the executable checker, without a parser correctness premise,
supplied validity flag, or assumed Python refinement. -/
theorem execution_exact (s : Source) (q : List UInt8) (c : Certificate)
    (e : Evidence) (ran : execute s q c = some e) :
    Reads s c.clauses ∧ ReadsQuery q c.query ∧
    (e.positive = true ↔ SemanticInference.Derivable (lower s c.clauses) (c.query.lower s.scope)) ∧
    (e.negative = true ↔ SemanticInference.Derivable (lower s c.clauses) (c.query.lower s.scope).opposite) ∧
    (e.cleanPositive = true ↔ SemanticInference.Derivable (clean (lower s c.clauses) c.known) (c.query.lower s.scope)) ∧
    (e.cleanNegative = true ↔ SemanticInference.Derivable (clean (lower s c.clauses) c.known) (c.query.lower s.scope).opposite) := by
  unfold execute at ran
  split at ran
  · rename_i checked
    cases ran
    have parts := verified_parts s q c checked
    refine ⟨parts.1.2.2.1, parts.1.2.2.2, ?_, ?_, ?_, ?_⟩
    · simpa only [evidence, decide_eq_true_eq] using (checked_closure_exact _ _ _ parts.2.1 _)
    · simpa only [evidence, decide_eq_true_eq] using (checked_closure_exact _ _ _ parts.2.1 _)
    · simpa only [evidence, decide_eq_true_eq] using (checked_closure_exact _ _ _ parts.2.2 _)
    · simpa only [evidence, decide_eq_true_eq] using (checked_closure_exact _ _ _ parts.2.2 _)
  · contradiction

/-- Compositional denotation of the concrete reading, independent of the
inference engine: signed facts and material Horn implications. -/
def Clause.meaning (scope : String) (v : GroundAtom → Prop) : Clause → Prop
  | .fact a => v (a.lower scope)
  | .rule body head => (∀ a ∈ body, v (a.lower scope)) → v (head.lower scope)

def TextMeaning (s : Source) (cs : List Clause) (v : GroundAtom → Prop) : Prop :=
  ∀ c ∈ cs, c.meaning s.scope v

def Models (s : Source) (cs : List Clause) (meaning : GroundAtom → Prop) : Prop :=
  (∀ f, SemanticInference.FactAdmitted (lower s cs) f → meaning f.atom) ∧
  (∀ r, SemanticInference.RuleAdmitted (lower s cs) r →
    (∀ a ∈ r.body, meaning a) → meaning r.head)

theorem lowering_preserves_meaning (s : Source) (cs : List Clause)
    (v : GroundAtom → Prop) (text : TextMeaning s cs v) : Models s cs v := by
  constructor
  · intro f admitted
    obtain ⟨c, member, hit⟩ := List.mem_filterMap.mp admitted.1
    cases c with
    | fact a =>
      simp only [Option.some.injEq] at hit
      subst f
      exact text (.fact a) member
    | rule body head => simp at hit
  · intro r admitted premises
    obtain ⟨c, member, hit⟩ := List.mem_filterMap.mp admitted.1
    cases c with
    | fact a => simp at hit
    | rule body head =>
      simp only [Option.some.injEq] at hit
      subst r
      apply text (.rule body head) member
      intro a ha
      exact premises (a.lower s.scope) (List.mem_map.mpr ⟨a, ha, rfl⟩)

/-- Every interpretation of the original source reading satisfies a certified
positive answer. This is entailment, not a claim of external-world truth. -/
theorem execution_entails (s : Source) (q : List UInt8) (c : Certificate)
    (e : Evidence) (ran : execute s q c = some e) (positive : e.positive = true)
    (meaning : GroundAtom → Prop) (text : TextMeaning s c.clauses meaning) :
    meaning (c.query.lower s.scope) := by
  have model := lowering_preserves_meaning s c.clauses meaning text
  exact SemanticInference.model_sound _ meaning model.1 model.2
    ((execution_exact s q c e ran).2.2.1.mp positive)

/-- Meaning is now a function of source bytes via the authoritative reader,
not a reading selected by a caller's certificate. -/
def SourceMeaning (s : Source) (v : GroundAtom → Prop) : Prop :=
  match readSource s.raw with
  | none => False
  | some cs => TextMeaning s cs v

theorem source_to_execution_entails (s : Source) (q : List UInt8) (c : Certificate)
    (e : Evidence) (ran : execute s q c = some e) (positive : e.positive = true)
    (v : GroundAtom → Prop) (sourceMeaning : SourceMeaning s v) :
    v (c.query.lower s.scope) := by
  have reading := (execution_exact s q c e ran).1.2.2.2
  have text : TextMeaning s c.clauses v := by
    simpa only [SourceMeaning, reading] using sourceMeaning
  exact execution_entails s q c e ran positive v text

theorem unknown_has_no_derivation (s : Source) (q : List UInt8) (c : Certificate)
    (e : Evidence) (ran : execute s q c = some e)
    (positive : e.positive = false) (negative : e.negative = false) :
    ¬ SemanticInference.Derivable (lower s c.clauses) (c.query.lower s.scope) ∧
    ¬ SemanticInference.Derivable (lower s c.clauses) (c.query.lower s.scope).opposite := by
  have h := execution_exact s q c e ran
  constructor
  · intro derived
    have yes := h.2.2.1.mpr derived
    simp [positive] at yes
  · intro derived
    have yes := h.2.2.2.1.mpr derived
    simp [negative] at yes

end Nabt.VerifiedReading
