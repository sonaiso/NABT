import Nabt.MeaningPreservation

/-! Update-sensitive observations. The finite model has five fixed witness slots;
it does not encode arbitrary witness identities, Arabic interpretation or truth.
The generic theorem reuses MeaningPreservation's exact collision criterion. -/
namespace Nabt.UpdateMemory

def lawId := "nabt.update-memory.v1"

def runUpdates {X A : Type} (step : X → A → X) (x : X) (actions : List A) : X :=
  actions.foldl step x

def futureQuery {X A Q O : Type} (step : X → A → X) (observe : X → Q → O)
    (x : X) (request : List A × Q) : O := observe (runUpdates step x request.1) request.2

def FutureCompatible {X A Q O R : Type} (encode : X → R)
    (step : X → A → X) (observe : X → Q → O) : Prop :=
  MeaningPreservation.FiberCompatible encode (futureQuery step observe)

theorem future_decoder_iff {X A Q O R : Type} (encode : X → R)
    (step : X → A → X) (observe : X → Q → O) :
    (∃ decode : MeaningPreservation.Image encode → (List A × Q → O),
      MeaningPreservation.DecoderCorrect encode (futureQuery step observe) decode ∧
      ∀ other, MeaningPreservation.DecoderCorrect encode (futureQuery step observe) other →
        other = decode) ↔ FutureCompatible encode step observe :=
  MeaningPreservation.unique_decoder_on_image_iff encode (futureQuery step observe)

abbrev Memory := Bool × Bool × Bool × Bool × Bool
abbrev Answer := Bool × Bool × Bool × Bool

def observe (m : Memory) : Answer :=
  (m.1 && m.2.1, m.2.2.1, m.2.2.2.1, m.2.2.2.2)

def addProperty (m : Memory) : Memory := (true, m.2)
def addLaw (m : Memory) : Memory := (m.1, true, m.2.2)
def signature (m : Memory) := (observe m, observe (addProperty m), observe (addLaw m))

def memories : List Memory :=
  [false, true].flatMap fun h => [false, true].flatMap fun l =>
  [false, true].flatMap fun e => [false, true].flatMap fun n =>
  [false, true].map fun s => (h, l, e, n, s)

theorem memory_count : memories.length = 32 := by decide
theorem memory_complete (m : Memory) : m ∈ memories := by
  rcases m with ⟨h, l, e, n, s⟩
  cases h <;> cases l <;> cases e <;> cases n <;> cases s <;> decide
theorem current_answer_count : (memories.map observe).eraseDups.length = 16 := by decide
theorem update_signature_count : (memories.map signature).eraseDups.length = 32 := by decide

theorem signature_injective : ∀ x y : Memory, signature x = signature y → x = y := by
  rintro ⟨h, l, e, n, s⟩ ⟨h', l', e', n', s'⟩ same
  have hh := congrArg (fun z => z.2.2.1) same
  have hl := congrArg (fun z => z.2.1.1) same
  have he := congrArg (fun z => z.1.2.1) same
  have hn := congrArg (fun z => z.1.2.2.1) same
  have hs := congrArg (fun z => z.1.2.2.2) same
  simp only [signature, observe, addProperty, addLaw, Bool.and_true, Bool.true_and] at hh hl he hn hs
  cases hh; cases hl; cases he; cases hn; cases hs
  rfl

theorem present_collision :
    observe (true, false, false, false, false) =
      observe (false, true, false, false, false) := by decide

theorem same_law_separates :
    observe (addLaw (true, false, false, false, false)) ≠
      observe (addLaw (false, true, false, false, false)) := by decide

theorem no_answer_only_update :
    ¬ ∃ f : Answer → Answer, ∀ m, f (observe m) = observe (addLaw m) := by
  rintro ⟨f, hf⟩
  apply same_law_separates
  calc
    observe (addLaw (true, false, false, false, false)) =
        f (observe (true, false, false, false, false)) := (hf _).symm
    _ = f (observe (false, true, false, false, false)) := congrArg f present_collision
    _ = observe (addLaw (false, true, false, false, false)) := hf _

end Nabt.UpdateMemory
