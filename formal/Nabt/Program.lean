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
  deriving DecidableEq, Repr

def opcode : Op → Nat
  | .readUtf8 => 1
  | .wordShape => 2
  | .startLearner => 10
  | .observeSource => 11
  | .withdrawSource => 12
  | .queryCue => 13
  | .applicationObligations => 20

def decodeOpcode : Nat → Option Op
  | 1 => some .readUtf8
  | 2 => some .wordShape
  | 10 => some .startLearner
  | 11 => some .observeSource
  | 12 => some .withdrawSource
  | 13 => some .queryCue
  | 20 => some .applicationObligations
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
  | start | text | learner | shapeResult | obligationsResult
  deriving DecidableEq, Repr

def step : Domain → Op → Option Domain
  | .start, .readUtf8 => some .text
  | .text, .wordShape => some .shapeResult
  | .start, .startLearner => some .learner
  | .learner, .observeSource => some .learner
  | .learner, .withdrawSource => some .learner
  | .learner, .queryCue => some .learner
  | .text, .applicationObligations => some .obligationsResult
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

end Nabt.Program
