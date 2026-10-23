import Std

/-!
The instruction tags and domain transitions of NABT's bounded interpreter.
These theorems establish opcode identity, lossless list assembly, domain
composition and the typing of the three compiler forms. They do not prove
Python refinement, UTF-8 decoding, source authenticity or Arabic semantics.
Operand readiness and evidence withdrawal identities are additional runtime
contracts. No domain here is a real-world truth or a semantic proof rank.
-/
namespace Nabt.Program

inductive Op where
  | readUtf8 | wordShape | startLearner | observeSource | withdrawSource
  | queryCue | applicationObligations
  | startText | addText | removeText | queryText | replaceText
  | startArabic
  deriving DecidableEq, Repr

def opcode : Op → Nat
  | .readUtf8 => 1
  | .wordShape => 2
  | .startLearner => 10
  | .observeSource => 11
  | .withdrawSource => 12
  | .queryCue => 13
  | .applicationObligations => 20
  | .startText => 30
  | .addText => 31
  | .removeText => 32
  | .queryText => 33
  | .replaceText => 34
  | .startArabic => 35

def decodeOpcode : Nat → Option Op
  | 1 => some .readUtf8
  | 2 => some .wordShape
  | 10 => some .startLearner
  | 11 => some .observeSource
  | 12 => some .withdrawSource
  | 13 => some .queryCue
  | 20 => some .applicationObligations
  | 30 => some .startText
  | 31 => some .addText
  | 32 => some .removeText
  | 33 => some .queryText
  | 34 => some .replaceText
  | 35 => some .startArabic
  | _ => none

theorem decode_opcode (op : Op) : decodeOpcode (opcode op) = some op := by
  cases op <;> rfl

theorem opcode_injective : Function.Injective opcode := by
  intro a b h
  have t := congrArg decodeOpcode h
  simpa only [decode_opcode, Option.some.injEq] using t

def assemble (ops : List Op) : List Nat := ops.map opcode

def disassemble : List Nat → Option (List Op)
  | [] => some []
  | n :: ns => do
    let op ← decodeOpcode n
    let rest ← disassemble ns
    pure (op :: rest)

theorem disassemble_assemble (ops : List Op) :
    disassemble (assemble ops) = some ops := by
  induction ops with
  | nil => rfl
  | cons op ops ih => simp [assemble, disassemble, decode_opcode, ih, assemble] at *

theorem assemble_injective : Function.Injective assemble := by
  intro a b h
  have t := congrArg disassemble h
  simpa only [disassemble_assemble, Option.some.injEq] using t

inductive Domain where
  | start | text | learner | shapeResult | obligationsResult | textTheory
  deriving DecidableEq, Repr

def step : Domain → Op → Option Domain
  | .start, .readUtf8 => some .text
  | .text, .wordShape => some .shapeResult
  | .start, .startLearner => some .learner
  | .learner, .observeSource => some .learner
  | .learner, .withdrawSource => some .learner
  | .learner, .queryCue => some .learner
  | .text, .applicationObligations => some .obligationsResult
  | .start, .startText => some .textTheory
  | .start, .startArabic => some .textTheory
  | .textTheory, .addText => some .textTheory
  | .textTheory, .removeText => some .textTheory
  | .textTheory, .queryText => some .textTheory
  | .textTheory, .replaceText => some .textTheory
  | _, _ => none

def run : Domain → List Op → Option Domain
  | q, [] => some q
  | q, op :: ops => (step q op).bind fun q' => run q' ops

theorem run_append (q : Domain) (a b : List Op) :
    run q (a ++ b) = (run q a).bind (fun q' => run q' b) := by
  induction a generalizing q with
  | nil => rfl
  | cons op ops ih =>
    simp only [List.cons_append, run]
    cases h : step q op with
    | none => rfl
    | some q' => simpa using ih q'

inductive Event where
  | observe | withdraw | query
  deriving DecidableEq, Repr

def eventOp : Event → Op
  | .observe => .observeSource
  | .withdraw => .withdrawSource
  | .query => .queryCue

theorem event_domain_preserved (event : Event) :
    step .learner (eventOp event) = some .learner := by cases event <;> rfl

theorem events_domain_preserved (events : List Event) :
    run .learner (events.map eventOp) = some .learner := by
  induction events with
  | nil => rfl
  | cons event events ih => simp [run, event_domain_preserved, ih]

def compileLearning (events : List Event) : List Op := .startLearner :: events.map eventOp
def compileShape : List Op := [.readUtf8, .wordShape]
def compileObligations : List Op := [.readUtf8, .applicationObligations]

theorem compiled_learning_typed (events : List Event) :
    run .start (compileLearning events) = some .learner := by
  simp [compileLearning, run, step, events_domain_preserved]

theorem compiled_shape_typed : run .start compileShape = some .shapeResult := rfl
theorem compiled_obligations_typed :
    run .start compileObligations = some .obligationsResult := rfl

theorem shape_does_not_enter_learner :
    run .text [.wordShape, .queryCue] = none := rfl

theorem source_cannot_be_observed_before_learner :
    run .start [.observeSource] = none := rfl

/-! The textual theory is a separate execution domain. Domain typing alone
does not prove that a source was admitted, that a withdrawal names an active
source, or that a source statement is true. Those are separate contracts. -/

inductive TextEvent where
  | add | remove | query | replace
  deriving DecidableEq, Repr

def textEventOp : TextEvent → Op
  | .add => .addText
  | .remove => .removeText
  | .query => .queryText
  | .replace => .replaceText

theorem text_event_domain_preserved (event : TextEvent) :
    step .textTheory (textEventOp event) = some .textTheory := by cases event <;> rfl

theorem text_events_domain_preserved (events : List TextEvent) :
    run .textTheory (events.map textEventOp) = some .textTheory := by
  induction events with
  | nil => rfl
  | cons event events ih => simp [run, text_event_domain_preserved, ih]

def compileText (events : List TextEvent) : List Op := .startText :: events.map textEventOp

theorem compiled_text_typed (events : List TextEvent) :
    run .start (compileText events) = some .textTheory := by
  simp [compileText, run, step, text_events_domain_preserved]

theorem text_source_requires_theory : run .start [.addText] = none := rfl

theorem learner_cannot_query_theory : run .learner [.queryText] = none := rfl

theorem theory_cannot_claim_shape : run .textTheory [.wordShape] = none := rfl

/-! Two distinct entry opcodes share the existing text-theory continuation.
The language selection is exposed explicitly here. Persistent profile state,
raw-source replay and the Python reader implementation remain runtime
contracts, not consequences of this domain-only machine. -/

inductive TextProfile where
  | controlledArabic | arabicSyntax
  deriving DecidableEq, Repr

def TextProfile.languageId : TextProfile → String
  | .controlledArabic => "nabt.controlled-arabic.v1"
  | .arabicSyntax => "nabt.arabic-syntax.v1"

def TextProfile.startOp : TextProfile → Op
  | .controlledArabic => .startText
  | .arabicSyntax => .startArabic

def profileOfStart : Op → Option TextProfile
  | .startText => some .controlledArabic
  | .startArabic => some .arabicSyntax
  | _ => none

theorem arabic_start_opcode :
    opcode .startArabic = 35 ∧ decodeOpcode 35 = some .startArabic := ⟨rfl, rfl⟩

theorem text_start_profiles_distinct :
    opcode TextProfile.controlledArabic.startOp ≠ opcode TextProfile.arabicSyntax.startOp ∧
    TextProfile.controlledArabic.languageId ≠ TextProfile.arabicSyntax.languageId := by decide

theorem start_profile_roundtrip (profile : TextProfile) :
    profileOfStart profile.startOp = some profile := by cases profile <;> rfl

def compileTextProfile (profile : TextProfile) (events : List TextEvent) : List Op :=
  profile.startOp :: events.map textEventOp

theorem compiled_text_profile_typed (profile : TextProfile) (events : List TextEvent) :
    run .start (compileTextProfile profile events) = some .textTheory := by
  cases profile <;> simp [compileTextProfile, TextProfile.startOp, run, step, text_events_domain_preserved]

theorem controlled_profile_preserves_compiler (events : List TextEvent) :
    compileTextProfile .controlledArabic events = compileText events := rfl

theorem compiled_profiles_distinguishable (events other : List TextEvent) :
    compileTextProfile .controlledArabic events ≠ compileTextProfile .arabicSyntax other := by
  simp [compileTextProfile, TextProfile.startOp]

theorem followup_does_not_select_profile (event : TextEvent) :
    profileOfStart (textEventOp event) = none := by cases event <;> rfl

theorem arabic_start_cannot_reset_theory_or_learner :
    step .textTheory .startArabic = none ∧ step .learner .startArabic = none := ⟨rfl, rfl⟩

theorem arabic_theory_cannot_observe_learner_source (events : List TextEvent) :
    run .start (compileTextProfile .arabicSyntax events ++ [.observeSource]) = none := by
  rw [run_append, compiled_text_profile_typed]
  rfl

end Nabt.Program
