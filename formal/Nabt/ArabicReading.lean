import Nabt.SemanticInference
import Nabt.Sequence

/-!
# Contracts for lowering a licensed Arabic reading into the existing kernel

The source audit is `docs/MASHRU_SYNTAX_AUDIT.md`. The separation of the
syntactic frame from its wrapper, and the conditional interpretation of
connectives, are informed by MIT-licensed
Saleh1967/Mashru@e4c801ffe9171dadedcc3aae23051ea0953ae361:
SLGE/Muwahhad.lean, SLGE/TarkibExt.lean, Aql/AdawatMaani.lean,
and Jisr/Mulhaqat.lean. Copyright (c) 2026 Saleh1967.

This is a *post-reading* contract. The input reading, its force, its exact
scope, and its completeness must already have been licensed by a reader.
These theorems do not prove a Python parser, Arabic grammatical universality,
the truth of a source, or a refinement between JSON and these Lean values.

The lowering shares SemanticInference's signed, source-relative ground
calculus. It does not introduce a competing inference kernel. Questions and
other nonassertive speech acts have no fact/rule effects here; their query or
dialogue routing is outside this specification. Scoped explicit negation is
already represented by the polarity of SemanticInference.Atom.

The numerical envelope reuses Sequence's proven base-116 codec. Its payload
is an explicitly supplied list of cells, not an assertion that unrestricted
UTF-8 text has been transformed into A116 phonology.
-/

namespace Nabt.ArabicReading

inductive Mood where
  | assertive | question | command | prohibition | wish | hope | vocative | ambiguous
  deriving DecidableEq, Repr

/-- Shared `nabt.arabic-syntax.v1` tags. -/
def Mood.code : Mood → Nat
  | .assertive => 0
  | .question => 1
  | .command => 2
  | .prohibition => 3
  | .wish => 4
  | .hope => 5
  | .vocative => 6
  | .ambiguous => 7

def Mood.ofCode : Nat → Option Mood
  | 0 => some .assertive
  | 1 => some .question
  | 2 => some .command
  | 3 => some .prohibition
  | 4 => some .wish
  | 5 => some .hope
  | 6 => some .vocative
  | 7 => some .ambiguous
  | _ => none

theorem mood_decode_code (m : Mood) : Mood.ofCode m.code = some m := by
  cases m <;> rfl

theorem mood_code_injective : Function.Injective Mood.code := by
  intro a b same
  have decoded := congrArg Mood.ofCode same
  simpa only [mood_decode_code, Option.some.injEq] using decoded

theorem mood_code_bound (m : Mood) : m.code < 8 := by
  cases m <;> decide

variable {α : Type}

abbrev Proposition (α : Type) := SemanticInference.Atom α

/-- The limited logical content understood by this lowering. A disjunction is
retained as a content constructor but has no Horn-program branch selection. -/
inductive Content (α : Type) where
  | atom (a : Proposition α)
  | conjunction (left right : Content α)
  | conditional (premises : List (Proposition α)) (conclusion : Proposition α)
  | disjunction (left right : Content α)
  deriving DecidableEq, Repr

def factsOf : Content α → List (Proposition α)
  | .atom a => [a]
  | .conjunction left right => factsOf left ++ factsOf right
  | .conditional _ _ | .disjunction _ _ => []

def rulesOf : Content α → List (List (Proposition α) × Proposition α)
  | .conditional premises conclusion => [(premises, conclusion)]
  | .conjunction left right => rulesOf left ++ rulesOf right
  | .atom _ | .disjunction _ _ => []

def interpret (meaning : Proposition α → Prop) : Content α → Prop
  | .atom a => meaning a
  | .conjunction left right => interpret meaning left ∧ interpret meaning right
  | .conditional premises conclusion =>
      (∀ a ∈ premises, meaning a) → meaning conclusion
  | .disjunction left right => interpret meaning left ∨ interpret meaning right

/-- Admission, scope checks and rejection of empty-body rules remain the
responsibility of SemanticInference.FactAdmitted / RuleAdmitted. -/
def lower (source : SemanticInference.Source) (ruleName : String)
    (mood : Mood) (content : Content α) : SemanticInference.Program α where
  sources := [source]
  facts := if mood = .assertive then
      (factsOf content).map (fun atom => ⟨source, atom⟩) else []
  rules := if mood = .assertive then
      (rulesOf content).map (fun (body, head) => ⟨source, ruleName, body, head⟩) else []

theorem nonassertive_empty (source : SemanticInference.Source) (name : String)
    (mood : Mood) (content : Content α) (nonassertive : mood ≠ .assertive) :
    (lower source name mood content).facts = [] ∧
    (lower source name mood content).rules = [] := by
  simp [lower, nonassertive]

theorem nonassertive_no_consequence (source : SemanticInference.Source) (name : String)
    (mood : Mood) (content : Content α) (nonassertive : mood ≠ .assertive)
    (a : Proposition α) : ¬ SemanticInference.Derivable (lower source name mood content) a :=
  SemanticInference.no_facts_no_consequence _ (nonassertive_empty source name mood content nonassertive).1 a

/-- A conjunction preserves both signed atoms, including their exact scopes. -/
theorem conjunction_projection (source : SemanticInference.Source) (name : String)
    (left right : Content α) :
    (lower source name .assertive (.conjunction left right)).facts =
      (lower source name .assertive left).facts ++
      (lower source name .assertive right).facts ∧
    (lower source name .assertive (.conjunction left right)).rules =
      (lower source name .assertive left).rules ++
      (lower source name .assertive right).rules := by
  simp [lower, factsOf, rulesOf, List.map_append]

theorem conditional_no_facts (source : SemanticInference.Source) (name : String)
    (premises : List (Proposition α)) (head : Proposition α) :
    (lower source name .assertive (.conditional premises head)).facts = [] := rfl

/-- A rule alone asserts neither its antecedent nor its consequent. A caller
can later add facts; this theorem is for the standalone conditional program. -/
theorem conditional_no_consequence (source : SemanticInference.Source) (name : String)
    (premises : List (Proposition α)) (head target : Proposition α) :
    ¬ SemanticInference.Derivable (lower source name .assertive (.conditional premises head)) target :=
  SemanticInference.no_facts_no_consequence _ rfl target

theorem disjunction_no_facts_or_rules (source : SemanticInference.Source) (name : String)
    (left right : Content α) :
    (lower source name .assertive (.disjunction left right)).facts = [] ∧
    (lower source name .assertive (.disjunction left right)).rules = [] := ⟨rfl, rfl⟩

theorem disjunction_no_branch_consequence (source : SemanticInference.Source) (name : String)
    (left right : Content α) (target : Proposition α) :
    ¬ SemanticInference.Derivable (lower source name .assertive (.disjunction left right)) target :=
  SemanticInference.no_facts_no_consequence _ rfl target

theorem projected_fact_sound (meaning : Proposition α → Prop) (content : Content α) :
    ∀ atom ∈ factsOf content, interpret meaning content → meaning atom := by
  induction content with
  | atom a =>
    intro atom member valid
    have same : atom = a := by simpa [factsOf] using member
    subst same
    exact valid
  | conjunction left right ihLeft ihRight =>
    intro atom member valid
    rcases List.mem_append.mp member with hLeft | hRight
    · exact ihLeft atom hLeft valid.1
    · exact ihRight atom hRight valid.2
  | conditional premises head => simp [factsOf]
  | disjunction left right _ _ => simp [factsOf]

theorem projected_rule_sound (meaning : Proposition α → Prop) (content : Content α) :
    ∀ pair ∈ rulesOf content, interpret meaning content →
      (∀ atom ∈ pair.1, meaning atom) → meaning pair.2 := by
  induction content with
  | atom a => simp [rulesOf]
  | conjunction left right ihLeft ihRight =>
    intro pair member valid premises
    rcases List.mem_append.mp member with hLeft | hRight
    · exact ihLeft pair hLeft valid.1 premises
    · exact ihRight pair hRight valid.2 premises
  | conditional premises head =>
    intro pair member valid given
    have same : pair = (premises, head) := by simpa [rulesOf] using member
    subst same
    exact valid given
  | disjunction left right _ _ => simp [rulesOf]

/-- Semantic validity is an explicit premise. Parsing and verification of a
source assertion do not manufacture this premise. -/
theorem lowered_derivation_sound (source : SemanticInference.Source) (name : String)
    (mood : Mood) (content : Content α) (meaning : Proposition α → Prop)
    (validReading : mood = .assertive → interpret meaning content)
    {target : Proposition α}
    (derived : SemanticInference.Derivable (lower source name mood content) target) :
    meaning target := by
  by_cases hMood : mood = .assertive
  · subst hMood
    apply SemanticInference.model_sound (lower source name .assertive content) meaning _ _ derived
    · intro fact admitted
      have member : fact ∈ (factsOf content).map (fun atom => SemanticInference.Fact.mk source atom) :=
        by simpa [lower] using admitted.1
      obtain ⟨atom, atomMember, same⟩ := List.mem_map.mp member
      subst same
      exact projected_fact_sound meaning content atom atomMember (validReading rfl)
    · intro rule admitted premises
      have member : rule ∈ (rulesOf content).map
          (fun (body, head) => SemanticInference.Rule.mk source name body head) :=
        by simpa [lower] using admitted.1
      obtain ⟨pair, pairMember, same⟩ := List.mem_map.mp member
      subst same
      exact projected_rule_sound meaning content pair pairMember (validReading rfl) premises
  · exact False.elim (nonassertive_no_consequence source name mood content hMood target derived)

/-- Every newly lowered fact and rule retains the same supplied source. -/
theorem lowered_source_preserved (source : SemanticInference.Source) (name : String)
    (mood : Mood) (content : Content α) :
    (∀ fact ∈ (lower source name mood content).facts, fact.source = source) ∧
    (∀ rule ∈ (lower source name mood content).rules, rule.source = source) := by
  by_cases hMood : mood = .assertive
  · simp only [lower, hMood, ↓reduceIte]
    constructor
    · intro fact member
      obtain ⟨atom, _, same⟩ := List.mem_map.mp member
      subst same
      rfl
    · intro rule member
      obtain ⟨pair, _, same⟩ := List.mem_map.mp member
      subst same
      rfl
  · simp [lower, hMood]

structure Candidate (α : Type) where
  mood : Mood
  content : Content α
  complete : Bool
  deriving DecidableEq, Repr

/-- A singleton candidate must also be complete. No first-alternative rule. -/
def selectUniqueComplete : List (Candidate α) → Option (Candidate α)
  | [candidate] => if candidate.complete then some candidate else none
  | _ => none

theorem selected_unique_complete (alternatives : List (Candidate α)) (candidate : Candidate α)
    (selected : selectUniqueComplete alternatives = some candidate) :
    alternatives = [candidate] ∧ candidate.complete = true := by
  cases alternatives with
  | nil => simp [selectUniqueComplete] at selected
  | cons first rest =>
    cases rest with
    | nil =>
      simp only [selectUniqueComplete] at selected
      split at selected
      · rename_i complete
        have same : first = candidate := Option.some.inj selected
        subst same
        exact ⟨rfl, complete⟩
      · contradiction
    | cons second rest => simp [selectUniqueComplete] at selected

theorem complete_singleton_selected (candidate : Candidate α) (complete : candidate.complete = true) :
    selectUniqueComplete [candidate] = some candidate := by
  simp [selectUniqueComplete, complete]

theorem incomplete_not_selected (candidate : Candidate α) (incomplete : candidate.complete = false) :
    selectUniqueComplete [candidate] = none := by
  simp [selectUniqueComplete, incomplete]

theorem alternatives_not_selected (first second : Candidate α) (rest : List (Candidate α)) :
    selectUniqueComplete (first :: second :: rest) = none := rfl

def lowerUnique (source : SemanticInference.Source) (name : String)
    (alternatives : List (Candidate α)) : Option (SemanticInference.Program α) :=
  (selectUniqueComplete alternatives).map (fun c => lower source name c.mood c.content)

theorem lowerUnique_requires_complete_singleton (source : SemanticInference.Source) (name : String)
    (alternatives : List (Candidate α)) (program : SemanticInference.Program α)
    (accepted : lowerUnique source name alternatives = some program) :
    ∃ candidate, alternatives = [candidate] ∧ candidate.complete = true ∧
      program = lower source name candidate.mood candidate.content := by
  unfold lowerUnique at accepted
  cases checked : selectUniqueComplete alternatives with
  | none => simp [checked] at accepted
  | some candidate =>
    have same : lower source name candidate.mood candidate.content = program := by
      simpa [checked] using accepted
    obtain ⟨single, complete⟩ := selected_unique_complete alternatives candidate checked
    exact ⟨candidate, single, complete, same.symm⟩

structure Envelope where
  mood : Mood
  payload : List Nabt.Atom
  deriving DecidableEq, Repr

/-- Namespace: `nabt.arabic-reading-envelope.b116.v1`. The low base-116 digit
is the mood tag; all higher digits hold the already-declared cell payload. -/
def envelopeNumber (envelope : Envelope) : Nat :=
  116 * Sequence.encode envelope.payload + envelope.mood.code

def decodeEnvelope (number : Nat) : Option Envelope := do
  let mood ← Mood.ofCode (number % 116)
  pure ⟨mood, Sequence.decode (number / 116)⟩

theorem envelope_decode_encode (envelope : Envelope) :
    decodeEnvelope (envelopeNumber envelope) = some envelope := by
  have small := mood_code_bound envelope.mood
  have remainder : envelopeNumber envelope % 116 = envelope.mood.code := by
    unfold envelopeNumber
    omega
  have quotient : envelopeNumber envelope / 116 = Sequence.encode envelope.payload := by
    unfold envelopeNumber
    omega
  simp only [decodeEnvelope, remainder, quotient, mood_decode_code, Sequence.decode_encode]
  rfl

theorem envelope_number_injective : Function.Injective envelopeNumber := by
  intro a b same
  have decoded := congrArg decodeEnvelope same
  simpa only [envelope_decode_encode, Option.some.injEq] using decoded

theorem envelope_mood_preserved (a b : Envelope) (same : envelopeNumber a = envelopeNumber b) :
    a.mood = b.mood := congrArg Envelope.mood (envelope_number_injective same)

theorem envelope_payload_preserved (a b : Envelope) (same : envelopeNumber a = envelopeNumber b) :
    a.payload = b.payload := congrArg Envelope.payload (envelope_number_injective same)

theorem changed_mood_changes_number (a b : Envelope) (different : a.mood ≠ b.mood) :
    envelopeNumber a ≠ envelopeNumber b := by
  intro same
  exact different (envelope_mood_preserved a b same)

end Nabt.ArabicReading
