import Nabt.Words
import Nabt.Obligations

/-!
# Conditional construction, nominal denotation, and diptote realization

Native NABT contracts, informed by MIT-licensed Saleh1967/Alghanem
9d8fa03a51f894416e0abaf3b6821c5ae6441dcd, A116/Qism.lean and A116/Mamnu.lean,
and Saleh1967/Mashru e4c801ffe9171dadedcc3aae23051ea0953ae361,
Dal/AqsamAlism.lean and Jisr/TasnifAlism.lean. See NOTICE.md.
Exact Arabic source windows are pinned in evidence/morphology/source_passages.json.

The grammatical traits are source-bound premises, not conclusions from an
arbitrary suffix, integer, or shape. In particular a noun's resemblance to a
particle is the licensed grammatical criterion; an unchanged spelling in one
sample does not establish it. The direct attachment of an emphatic nun must
already be established. An unknown trait is not a negative trait.

`NominalDenotation` is the cited semantic division of a universal noun into
genus/quality-bearer. It does not claim to discover an etymological root,
establish a productive morphological derivation, or classify a frozen verb.

A diptote cause is kept outside the realization operation. The finite sign
table predicts a sign *conditional on* an inflected diptote being genitive.
The actual-realization wrapper additionally requires the supplied noun,
inflected-status, cause and genitive-government witnesses. `al` or idhafa
changes the genitive sign; neither operation deletes the lexical cause.
The finite exports and theorems concern this conditional algebra. They do
not prove the external source reader, evidence authenticity, or all Arabic.
-/

namespace Nabt.Morphology

open Words (Kind Ending)

def lawId : String := "nabt.morphology.v1"

/-- Positive and negative support remain distinct, including a relevant
conflict. `unknown` does not assert that a property is absent. -/
inductive Evidence where
  | unknown | affirmed | denied | conflict
  deriving DecidableEq, Repr

def evidenceStates : List Evidence := [.unknown, .affirmed, .denied, .conflict]

def Evidence.code : Evidence → Nat
  | .unknown => 0 | .affirmed => 1 | .denied => 2 | .conflict => 3

def Evidence.ofCode : Nat → Option Evidence
  | 0 => some .unknown | 1 => some .affirmed | 2 => some .denied
  | 3 => some .conflict | _ => none

def Evidence.label : Evidence → String
  | .unknown => "unknown" | .affirmed => "affirmed"
  | .denied => "denied" | .conflict => "conflict"

def Evidence.positive : Evidence → Bool
  | .affirmed | .conflict => true | _ => false

def Evidence.negative : Evidence → Bool
  | .denied | .conflict => true | _ => false

def Evidence.allows : Evidence → Bool → Bool
  | .unknown, _ => true
  | .affirmed, value => value
  | .denied, value => !value
  | .conflict, _ => false

def Evidence.values (evidence : Evidence) : List Bool :=
  [false, true].filter evidence.allows

theorem evidence_code_roundtrip (evidence : Evidence) :
    Evidence.ofCode evidence.code = some evidence := by cases evidence <;> rfl

theorem unknown_preserves_boolean_alternatives :
    Evidence.unknown.values = [false, true] ∧ Evidence.denied.values = [false] := by decide

theorem conflicting_evidence_has_no_completion : Evidence.conflict.values = [] := by decide

inductive Construction where
  | built | inflected
  deriving DecidableEq, Repr

def constructions : List Construction := [.built, .inflected]

def Construction.code : Construction → Nat
  | .built => 0 | .inflected => 1

def Construction.label : Construction → String
  | .built => "built" | .inflected => "inflected"

inductive Tense where
  | past | imperfect | imperative
  deriving DecidableEq, Repr

def tenses : List Tense := [.past, .imperfect, .imperative]

def Tense.code : Tense → Nat
  | .past => 0 | .imperfect => 1 | .imperative => 2

def Tense.ofCode : Nat → Option Tense
  | 0 => some .past | 1 => some .imperfect | 2 => some .imperative | _ => none

def Tense.label : Tense → String
  | .past => "past" | .imperfect => "imperfect" | .imperative => "imperative"

inductive NunConnection where
  | none | directEmphatic | separatedEmphatic | femininePlural
  deriving DecidableEq, Repr

def nunConnections : List NunConnection :=
  [.none, .directEmphatic, .separatedEmphatic, .femininePlural]

def NunConnection.code : NunConnection → Nat
  | .none => 0 | .directEmphatic => 1 | .separatedEmphatic => 2 | .femininePlural => 3

def NunConnection.ofCode : Nat → Option NunConnection
  | 0 => some .none | 1 => some .directEmphatic | 2 => some .separatedEmphatic
  | 3 => some .femininePlural | _ => none

def NunConnection.label : NunConnection → String
  | .none => "none" | .directEmphatic => "direct_emphatic"
  | .separatedEmphatic => "separated_emphatic" | .femininePlural => "feminine_plural"

def verbConstruction : Tense → NunConnection → Construction
  | .past, _ | .imperative, _ => .built
  | .imperfect, .directEmphatic | .imperfect, .femininePlural => .built
  | .imperfect, .none | .imperfect, .separatedEmphatic => .inflected

theorem verb_inflected_iff (tense : Tense) (nun : NunConnection) :
    verbConstruction tense nun = .inflected ↔
      tense = .imperfect ∧ (nun = .none ∨ nun = .separatedEmphatic) := by
  cases tense <;> cases nun <;> simp [verbConstruction]

theorem direct_and_separated_nun_differ :
    verbConstruction .imperfect .directEmphatic ≠
      verbConstruction .imperfect .separatedEmphatic := by decide

/-- A code for a supplied grammatical input pair, not for its evidence. -/
def verbStateNumberDomain : String := "nabt.morphology.verb-input.v1"

def verbStateNumber (tense : Tense) (nun : NunConnection) : Nat :=
  4 * tense.code + nun.code

def decodeVerbState (number : Nat) : Option (Tense × NunConnection) := do
  let tense ← Tense.ofCode (number / 4)
  let nun ← NunConnection.ofCode (number % 4)
  pure (tense, nun)

theorem verb_state_roundtrip (tense : Tense) (nun : NunConnection) :
    decodeVerbState (verbStateNumber tense nun) = some (tense, nun) := by
  cases tense <;> cases nun <;> rfl

theorem verb_state_injective {t u : Tense} {n m : NunConnection}
    (same : verbStateNumber t n = verbStateNumber u m) : t = u ∧ n = m := by
  have decoded := congrArg decodeVerbState same
  simpa only [verb_state_roundtrip, Option.some.injEq, Prod.mk.injEq] using decoded

theorem verb_state_rejects_outside (number : Nat) (outside : 12 ≤ number) :
    decodeVerbState number = none := by
  have beyond : 3 ≤ number / 4 := by omega
  simp only [decodeVerbState]
  have noTense : Tense.ofCode (number / 4) = none := by
    match h : number / 4 with
    | 0 | 1 | 2 => omega
    | _ + 3 => rfl
  simp [noTense]

/-- `none` means not established; `.some .none` is positive evidence that
neither relevant nun relation is present. -/
structure VerbQuery where
  tense : Option Tense := none
  nun : Option NunConnection := none
  deriving DecidableEq, Repr

def optionAllows [DecidableEq α] (known : Option α) (candidate : α) : Bool :=
  match known with
  | none => true
  | some value => decide (value = candidate)

def verbInputs : List (Tense × NunConnection) :=
  tenses.flatMap (fun tense => nunConnections.map (fun nun => (tense, nun)))

def verbReadings (query : VerbQuery) : List (Tense × NunConnection) :=
  verbInputs.filter (fun input => optionAllows query.tense input.1 && optionAllows query.nun input.2)

def verbCandidates (query : VerbQuery) : List Construction :=
  constructions.filter (fun output => (verbReadings query).any
    (fun input => decide (verbConstruction input.1 input.2 = output)))

theorem mem_verbInputs (tense : Tense) (nun : NunConnection) :
    (tense, nun) ∈ verbInputs := by cases tense <;> cases nun <;> decide

theorem mem_verbReadings_iff (query : VerbQuery) (tense : Tense) (nun : NunConnection) :
    (tense, nun) ∈ verbReadings query ↔
      optionAllows query.tense tense = true ∧ optionAllows query.nun nun = true := by
  simp [verbReadings, mem_verbInputs]

theorem mem_verbCandidates_iff (query : VerbQuery) (output : Construction) :
    output ∈ verbCandidates query ↔
      ∃ input ∈ verbReadings query, verbConstruction input.1 input.2 = output := by
  have complete : output ∈ constructions := by cases output <;> decide
  simp [verbCandidates, complete, List.any_eq_true]

theorem full_verb_query_exact (tense : Tense) (nun : NunConnection) :
    verbCandidates ⟨some tense, some nun⟩ = [verbConstruction tense nun] := by
  cases tense <;> cases nun <;> decide

theorem unknown_imperfect_nun_is_not_absent :
    verbCandidates ⟨some .imperfect, none⟩ = [.built, .inflected] ∧
    verbCandidates ⟨some .imperfect, some .none⟩ = [.inflected] := by decide

theorem fixed_past_does_not_need_nun :
    verbCandidates ⟨some .past, none⟩ = [.built] := by decide

/-- The conditional nominal criterion is transported from its source; it
is not inferred from the token's spelling being unchanged. -/
def nounConstruction (licensedParticleResemblance : Bool) : Construction :=
  if licensedParticleResemblance then .built else .inflected

def nounCandidates (evidence : Evidence) : List Construction :=
  constructions.filter (fun output => evidence.values.any
    (fun resemblance => decide (nounConstruction resemblance = output)))

theorem noun_unknown_keeps_both : nounCandidates .unknown = [.built, .inflected] := by decide

theorem noun_negative_is_explicit : nounCandidates .denied = [.inflected] := by decide

theorem noun_conflict_does_not_classify : nounCandidates .conflict = [] := by decide

def particleConstruction : Construction := .built

/-- Governor contexts over a fixed licensed lexical reading are the domain
of a construction-invariance claim. The domain is an explicit parameter. -/
def BuiltOn (licensed : Context → Prop) (realize : Context → Ending) : Prop :=
  ∀ a b, licensed a → licensed b → realize a = realize b

theorem singleton_observation_does_not_prove_built :
    let realize : Bool → Ending := fun c => if c then .fatha else .damma
    BuiltOn (fun c => c = false) realize ∧ ¬ BuiltOn (fun _ => True) realize := by
  dsimp
  constructor
  · intro a b ha hb
    simp [ha, hb]
  · intro allContexts
    have impossible := allContexts false true trivial trivial
    contradiction

/-- Semantic genus/quality-bearer division of *universal nouns* only. It is
orthogonal to construction and to a syntactic role. -/
inductive NominalDenotation where
  | outsideUniversal | genus | qualityBearer
  deriving DecidableEq, Repr

def nominalDenotations : List NominalDenotation := [.outsideUniversal, .genus, .qualityBearer]

def NominalDenotation.code : NominalDenotation → Nat
  | .outsideUniversal => 0 | .genus => 1 | .qualityBearer => 2

def NominalDenotation.label : NominalDenotation → String
  | .outsideUniversal => "outside_universal_noun"
  | .genus => "jins_jamid" | .qualityBearer => "mushtaq_quality_bearer"

def nominalDenotation (universal qualityBearer : Bool) : NominalDenotation :=
  if universal then if qualityBearer then .qualityBearer else .genus else .outsideUniversal

def nominalDenotationCandidates (universal qualityBearer : Evidence) : List NominalDenotation :=
  nominalDenotations.filter (fun output => universal.values.any (fun u =>
    qualityBearer.values.any (fun q => decide (nominalDenotation u q = output))))

theorem semantic_mushtaq_requires_both (universal qualityBearer : Bool) :
    nominalDenotation universal qualityBearer = .qualityBearer ↔
      universal = true ∧ qualityBearer = true := by
  cases universal <;> cases qualityBearer <;> decide

theorem particular_is_not_genus (qualityBearer : Bool) :
    nominalDenotation false qualityBearer = .outsideUniversal := by rfl

theorem semantic_unknown_is_not_jamid :
    nominalDenotationCandidates .affirmed .unknown = [.genus, .qualityBearer] := by decide

/-- The two properties cannot supply one another: their product keeps both
inputs. Neither component asserts a grammatical role or an attested root. -/
def nominalAxes (resemblance universal qualityBearer : Bool) :
    Construction × NominalDenotation :=
  (nounConstruction resemblance, nominalDenotation universal qualityBearer)

theorem derivation_does_not_change_construction (resemblance u q u' q' : Bool) :
    (nominalAxes resemblance u q).1 = (nominalAxes resemblance u' q').1 := rfl

theorem construction_does_not_change_denotation (r r' universal qualityBearer : Bool) :
    (nominalAxes r universal qualityBearer).2 = (nominalAxes r' universal qualityBearer).2 := rfl

/-- Source-qualified factors, not bare strings or shape matches. `wasf` is
the eligible original adjectival status; `falan`, `afal`, etc. include the
source's qualifications and exceptions for their application. A declaration
of a similar surface pattern alone does not establish one of these traits. -/
inductive CauseTrait where
  | alam | wasf | tanithAlif | muntaha | falan | afal | adl | tarkib
  | tanith | ajamiOver3 | waznFil
  deriving DecidableEq, Repr

def causeTraits : List CauseTrait :=
  [.alam, .wasf, .tanithAlif, .muntaha, .falan, .afal, .adl, .tarkib,
   .tanith, .ajamiOver3, .waznFil]

def CauseTrait.code : CauseTrait → Nat
  | .alam => 0 | .wasf => 1 | .tanithAlif => 2 | .muntaha => 3
  | .falan => 4 | .afal => 5 | .adl => 6 | .tarkib => 7
  | .tanith => 8 | .ajamiOver3 => 9 | .waznFil => 10

def CauseTrait.label : CauseTrait → String
  | .alam => "alam" | .wasf => "wasf" | .tanithAlif => "tanithAlif"
  | .muntaha => "muntaha" | .falan => "falan" | .afal => "afal"
  | .adl => "adl" | .tarkib => "tarkib" | .tanith => "tanith"
  | .ajamiOver3 => "ajamiOver3" | .waznFil => "waznFil"

theorem mem_causeTraits (trait : CauseTrait) : trait ∈ causeTraits := by cases trait <;> decide

/-- The imported finite cause algebra, without the upstream al/tanwin
realization guards. Its negative result is relative to this qualified
11-factor model; it is not proof that every possible Arabic cause is absent. -/
def intrinsicDiptote (traits : CauseTrait → Bool) : Bool :=
  (traits .tanithAlif || traits .muntaha) ||
  (traits .wasf && (traits .falan || traits .afal || traits .adl)) ||
  (traits .alam && (traits .tarkib || traits .falan || traits .tanith ||
    traits .ajamiOver3 || traits .waznFil || traits .adl))

def intrinsicCauseFormula : Obligations.Formula Nat :=
  .disj (.disj
    (.disj (.atom 2) (.atom 3))
    (.conj (.atom 1) (.disj (.disj (.atom 4) (.atom 5)) (.atom 6))))
    (.conj (.atom 0)
      (.disj (.disj (.disj (.disj (.disj (.atom 7) (.atom 4)) (.atom 8)) (.atom 9))
        (.atom 10)) (.atom 6)))

abbrev CauseInput := Fin 2048

def causeInputNumberDomain : String := "nabt.morphology.qualified-causes.v1"

def causeInputs : List CauseInput := List.finRange 2048

def CauseInput.traits (input : CauseInput) (trait : CauseTrait) : Bool :=
  input.val.testBit trait.code

def CauseInput.diptote (input : CauseInput) : Bool := intrinsicDiptote input.traits

theorem intrinsic_formula_matches_numeric (input : CauseInput) :
    intrinsicCauseFormula.eval input.val.testBit = input.diptote := by
  rfl

theorem qualified_strong_cause_suffices (traits : CauseTrait → Bool)
    (strong : traits .tanithAlif = true ∨ traits .muntaha = true) :
    intrinsicDiptote traits = true := by
  rcases strong with alif | plural
  · simp [intrinsicDiptote, alif]
  · simp [intrinsicDiptote, plural]

theorem lone_properness_does_not_suffice :
    intrinsicDiptote (fun trait => decide (trait = .alam)) = false := by decide

theorem lone_adjectival_status_does_not_suffice :
    intrinsicDiptote (fun trait => decide (trait = .wasf)) = false := by decide

abbrev CauseQuery := CauseTrait → Evidence

def causeAgrees (query : CauseQuery) (input : CauseInput) : Bool :=
  causeTraits.all (fun trait => (query trait).allows (input.traits trait))

def causeCandidates (query : CauseQuery) : List CauseInput := causeInputs.filter (causeAgrees query)

def causePredictions (query : CauseQuery) : List Bool :=
  [false, true].filter (fun output => (causeCandidates query).any
    (fun input => decide (input.diptote = output)))

theorem cause_candidates_exact (query : CauseQuery) (input : CauseInput) :
    input ∈ causeCandidates query ↔
      ∀ trait, (query trait).allows (input.traits trait) = true := by
  simp [causeCandidates, causeInputs, causeAgrees, List.all_eq_true, mem_causeTraits]

theorem cause_prediction_exact (query : CauseQuery) (output : Bool) :
    output ∈ causePredictions query ↔
      ∃ input ∈ causeCandidates query, input.diptote = output := by
  have complete : output ∈ [false, true] := by cases output <;> decide
  simp [causePredictions, complete, List.any_eq_true]

/-- A refinement adds compatible support. Retraction or replacement requires
recomputing from the changed source; it is not assumed monotone here. -/
def CauseRefines (narrow wide : CauseQuery) : Prop :=
  ∀ trait value, (narrow trait).allows value = true → (wide trait).allows value = true

theorem cause_refinement_removes_only (narrow wide : CauseQuery)
    (refines : CauseRefines narrow wide) (input : CauseInput)
    (survives : input ∈ causeCandidates narrow) : input ∈ causeCandidates wide := by
  rw [cause_candidates_exact] at survives ⊢
  exact fun trait => refines trait (input.traits trait) (survives trait)

theorem cause_prediction_refines (narrow wide : CauseQuery)
    (refines : CauseRefines narrow wide) (output : Bool)
    (survives : output ∈ causePredictions narrow) : output ∈ causePredictions wide := by
  obtain ⟨input, member, predicts⟩ := (cause_prediction_exact narrow output).mp survives
  exact (cause_prediction_exact wide output).mpr
    ⟨input, cause_refinement_removes_only narrow wide refines input member, predicts⟩

theorem unknown_causes_keep_every_input (input : CauseInput) :
    input ∈ causeCandidates (fun _ => .unknown) := by
  rw [cause_candidates_exact]
  exact fun _ => rfl

theorem conflicting_cause_refuses_completion (query : CauseQuery) (trait : CauseTrait)
    (conflicting : query trait = .conflict) : causeCandidates query = [] := by
  apply List.eq_nil_iff_forall_not_mem.mpr
  intro input member
  have required := (cause_candidates_exact query input).mp member trait
  simp [conflicting, Evidence.allows] at required

/-- `causeId` names an already licensed source-bound diptote cause. No
integer, ending, `al`, or idhafa operation manufactures that license. -/
structure DiptoteIdentity where
  word : Words.Analysis
  causeId : Nat
  deriving DecidableEq, Repr

/-- Inflection is a witnessed property of this exact source-bound reading,
not an independently supplied enum which happens to equal `.inflected`. -/
structure LicensedDiptote (CauseWitness : DiptoteIdentity → Prop)
    (ConstructionWitness : Words.Analysis → Construction → Prop) where
  identity : DiptoteIdentity
  isNoun : identity.word.kind = .noun
  evidencedInflection : ConstructionWitness identity.word .inflected
  cause : CauseWitness identity

/-- Input masks are scoped to al=bit 0 and idhafa=bit 1. -/
structure GenitiveContext where
  al : Evidence
  idhafa : Evidence
  deriving DecidableEq, Repr

def genitiveContexts : List GenitiveContext :=
  evidenceStates.flatMap (fun idhafa => evidenceStates.map (fun al => ⟨al, idhafa⟩))

def genitiveStateNumberDomain : String := "nabt.morphology.diptote-context.v1"
def genitiveResidualNumberDomain : String := "nabt.morphology.diptote-residual.v1"

def GenitiveContext.number (context : GenitiveContext) : Nat :=
  context.al.code + 4 * context.idhafa.code

def decodeGenitiveContext (number : Nat) : Option GenitiveContext := do
  let al ← Evidence.ofCode (number % 4)
  let idhafa ← Evidence.ofCode (number / 4)
  pure ⟨al, idhafa⟩

def GenitiveContext.positive (context : GenitiveContext) : Nat :=
  context.al.positive.toNat + 2 * context.idhafa.positive.toNat

def GenitiveContext.negative (context : GenitiveContext) : Nat :=
  context.al.negative.toNat + 2 * context.idhafa.negative.toNat

def genitiveOverride : Obligations.Formula Nat := .disj (.atom 0) (.atom 1)

def GenitiveContext.plans (context : GenitiveContext) : List Nat :=
  Obligations.plans context.positive context.negative genitiveOverride

inductive GenitiveResult where
  | pending | fatha | kasra | conflict
  deriving DecidableEq, Repr

def GenitiveResult.code : GenitiveResult → Nat
  | .pending => 0 | .fatha => 1 | .kasra => 2 | .conflict => 3

def GenitiveResult.label : GenitiveResult → String
  | .pending => "pending" | .fatha => "fatha" | .kasra => "kasra" | .conflict => "conflict"

def GenitiveResult.ending : GenitiveResult → Option Ending
  | .fatha => some .fatha | .kasra => some .kasra | _ => none

/-- The sign if the word is an inflected diptote governed in the genitive.
This conditional result cannot establish the premise of genitive government. -/
def genitiveResult (context : GenitiveContext) : GenitiveResult :=
  match Obligations.assess context.positive context.negative genitiveOverride with
  | .licensed => .kasra
  | .rejected => .fatha
  | .pending => .pending
  | .conflict => .conflict

def concreteGenitive (al idhafa : Bool) : Ending := if al || idhafa then .kasra else .fatha

def genitiveCandidates (context : GenitiveContext) : List Ending :=
  [Ending.fatha, Ending.kasra].filter (fun output => context.al.values.any (fun al =>
    context.idhafa.values.any (fun idhafa => decide (concreteGenitive al idhafa = output))))

theorem genitive_state_roundtrip (context : GenitiveContext) :
    decodeGenitiveContext context.number = some context := by
  rcases context with ⟨al, idhafa⟩
  cases al <;> cases idhafa <;> rfl

theorem genitive_state_injective : Function.Injective GenitiveContext.number := by
  intro a b same
  have decoded := congrArg decodeGenitiveContext same
  simpa only [genitive_state_roundtrip, Option.some.injEq] using decoded

theorem genitive_state_outside_rejected (number : Nat) (outside : 16 ≤ number) :
    decodeGenitiveContext number = none := by
  have beyond : 4 ≤ number / 4 := by omega
  have noIdhafa : Evidence.ofCode (number / 4) = none := by
    match h : number / 4 with
    | 0 | 1 | 2 | 3 => omega
    | _ + 4 => rfl
  simp [decodeGenitiveContext, noIdhafa]

theorem unknown_context_retains_alternatives :
    genitiveResult ⟨.unknown, .unknown⟩ = .pending ∧
    genitiveCandidates ⟨.unknown, .unknown⟩ = [.fatha, .kasra] ∧
    GenitiveContext.plans ⟨.unknown, .unknown⟩ = [1, 2] := by decide

theorem fatha_requires_both_negatives (context : GenitiveContext) :
    genitiveResult context = .fatha ↔ context.al = .denied ∧ context.idhafa = .denied := by
  rcases context with ⟨al, idhafa⟩
  cases al <;> cases idhafa <;> decide

theorem kasra_requires_supported_override (context : GenitiveContext) :
    genitiveResult context = .kasra ↔
      (context.al = .affirmed ∨ context.idhafa = .affirmed) ∧
      context.al ≠ .conflict ∧ context.idhafa ≠ .conflict := by
  rcases context with ⟨al, idhafa⟩
  cases al <;> cases idhafa <;> decide

theorem relevant_conflict_precedes_sign (context : GenitiveContext) :
    genitiveResult context = .conflict ↔
      context.al = .conflict ∨ context.idhafa = .conflict := by
  rcases context with ⟨al, idhafa⟩
  cases al <;> cases idhafa <;> decide

theorem genitive_singleton_iff (context : GenitiveContext) (observed : Ending) :
    (genitiveResult context).ending = some observed ↔
      genitiveCandidates context = [observed] := by
  rcases context with ⟨al, idhafa⟩
  cases al <;> cases idhafa <;> cases observed <;> decide

/-- Every returned positive plan suffices to establish the override under
the supplied positive support. This does not permit inventing its witness. -/
theorem genitive_residual_sound (context : GenitiveContext) (plan : Nat)
    (member : plan ∈ context.plans) :
    genitiveOverride.eval (fun i => (context.positive ||| plan).testBit i) = true :=
  Obligations.plans_sound context.positive context.negative genitiveOverride plan member

theorem genitive_residual_complete (context : GenitiveContext) (completion : Nat)
    (avoids : completion &&& context.negative = 0)
    (succeeds : genitiveOverride.eval
      (fun i => (context.positive ||| completion).testBit i) = true) :
    ∃ plan ∈ context.plans, Obligations.Submask plan completion :=
  Obligations.plans_complete context.positive context.negative completion genitiveOverride avoids succeeds

/-- An actual contextual application additionally requires a genitive
government witness for the same reading whose inflection was witnessed.
Al/idhafa evidence remains a supplied context input; its binding to this
reading is an external replay obligation, not a theorem about the Python
source extractor. A raw conditional sign table manufactures no witnesses. -/
structure DiptoteRealization (CauseWitness : DiptoteIdentity → Prop)
    (ConstructionWitness : Words.Analysis → Construction → Prop)
    (GovernmentWitness : Words.Analysis → Governors.Case → Prop) where
  original : LicensedDiptote CauseWitness ConstructionWitness
  context : GenitiveContext
  governed : GovernmentWitness original.identity.word .jarr

def realizeDiptote {CauseWitness : DiptoteIdentity → Prop}
    {ConstructionWitness : Words.Analysis → Construction → Prop}
    {GovernmentWitness : Words.Analysis → Governors.Case → Prop}
    (word : LicensedDiptote CauseWitness ConstructionWitness) (context : GenitiveContext)
    (government : GovernmentWitness word.identity.word .jarr) :
    DiptoteRealization CauseWitness ConstructionWitness GovernmentWitness :=
      ⟨word, context, government⟩

theorem realization_preserves_cause {CauseWitness : DiptoteIdentity → Prop}
    {ConstructionWitness : Words.Analysis → Construction → Prop}
    {GovernmentWitness : Words.Analysis → Governors.Case → Prop}
    (word : LicensedDiptote CauseWitness ConstructionWitness) (context : GenitiveContext)
    (government : GovernmentWitness word.identity.word .jarr) :
    (realizeDiptote word context government).original.identity = word.identity := rfl

theorem realization_cannot_change_word_kind {CauseWitness : DiptoteIdentity → Prop}
    {ConstructionWitness : Words.Analysis → Construction → Prop}
    {GovernmentWitness : Words.Analysis → Governors.Case → Prop}
    (word : LicensedDiptote CauseWitness ConstructionWitness) (context : GenitiveContext)
    (government : GovernmentWitness word.identity.word .jarr) :
    (realizeDiptote word context government).original.identity.word.kind = .noun := word.isNoun

end Nabt.Morphology
