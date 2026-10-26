import Nabt.CertifiedLexical

/-!
# Exact witnessed lexical surfaces, composed with the existing A116 contract

This is an additive bridge, not another induction or inference calculus.
`Foundation` already proves lossless source projection and `Sequence` proves
the numerical bijection. Here a retained source FORM uses a declared strict
Buckwalter carrier/mark-pair encoding, decoded to the same A116 atoms. The
observed Arabic surface must equal the rendering of those atoms byte for byte,
as well as having the same cell number. Separators cannot silently disappear.

The witness ledger is an explicit reviewed interpretation premise. Its source
authenticity and assignment of a source form to an expression/convention remain
outside this theorem. A corpus spelling is not evidence that every occurrence
has the corpus's intended sense. There is no vowel erasure, guessed mark,
arbitrary replacement rule, inflection transfer, or contextual sense selection.
-/
namespace Nabt.LexicalSurfaceBinding

open LinguisticTruth

def lawId : String := "nabt.lexical-surface-binding.v1"

/-- Restricted documentary code in the order of Nabt.canonicalCarriers.
Hamza seats, tanwin, shadda, long-vowel omission and other Qur'anic marks are
not silently normalized into this direct-pair domain. -/
def bwCarriers : List Char := "AbtvjHxd*rzs$SDTZEgfqklmnhwy'".toList
def bwMarks : List Char := ['a', 'u', 'i', 'o']

def encodeAtom (atom : Atom) : List Char :=
  [bwCarriers.getD (Cell.decode atom).carrier.val '?',
   bwMarks.getD (Cell.decode atom).mark.val '?']

def decodePair (carrier mark : Char) : Option Atom :=
  (List.finRange 116).find? (fun atom => encodeAtom atom == [carrier, mark])

def decodePairs : List Char → Option (List Atom)
  | [] => some []
  | [_] => none
  | carrier :: mark :: rest => do
      let atom ← decodePair carrier mark
      let tail ← decodePairs rest
      return atom :: tail

def encodeForm (cells : List Atom) : String := String.ofList (cells.flatMap encodeAtom)
def decodeForm (text : String) : Option (List Atom) := decodePairs text.toList

def renderArabic (cells : List Atom) : String :=
  String.ofList (cells.flatMap fun atom =>
    (canonicalCarriers.getD (Cell.decode atom).carrier.val "").toList ++
    (Foundation.marks.getD (Cell.decode atom).mark.val "").toList)

set_option maxRecDepth 10000 in
set_option maxHeartbeats 3000000 in
theorem all_116_pair_codes_roundtrip : ∀ atom : Atom,
    decodePair (bwCarriers.getD (Cell.decode atom).carrier.val '?')
      (bwMarks.getD (Cell.decode atom).mark.val '?') = some atom := by
  decide +kernel

/-- This induction covers every finite sequence in the declared pair code;
it does not assert that every generated sequence is an Arabic word. -/
theorem decodePairs_encode (cells : List Atom) :
    decodePairs (cells.flatMap encodeAtom) = some cells := by
  induction cells with
  | nil => rfl
  | cons atom tail ih =>
      simp only [List.flatMap_cons, encodeAtom, List.cons_append, List.nil_append, decodePairs]
      rw [all_116_pair_codes_roundtrip]
      simp [ih]

theorem decodeForm_encode (cells : List Atom) : decodeForm (encodeForm cells) = some cells := by
  simpa [decodeForm, encodeForm] using decodePairs_encode cells

theorem decodePair_retains_code (carrier mark : Char) (atom : Atom)
    (decoded : decodePair carrier mark = some atom) : encodeAtom atom = [carrier, mark] := by
  have matching : (encodeAtom atom == [carrier, mark]) = true :=
    List.find?_some (p := fun (value : Atom) => encodeAtom value == [carrier, mark]) decoded
  simpa using matching

theorem encodePairs_decode (chars : List Char) (cells : List Atom)
    (decoded : decodePairs chars = some cells) : cells.flatMap encodeAtom = chars := by
  cases chars with
  | nil =>
      have empty : cells = [] := by simpa [decodePairs] using decoded.symm
      simp [empty]
  | cons carrier tail =>
      cases tail with
      | nil => simp [decodePairs] at decoded
      | cons mark rest =>
          cases pair : decodePair carrier mark with
          | none => simp [decodePairs, pair] at decoded
          | some atom =>
              cases next : decodePairs rest with
              | none => simp [decodePairs, pair, next] at decoded
              | some remaining =>
                  have same : atom :: remaining = cells := by
                    simpa [decodePairs, pair, next] using decoded
                  rw [← same, List.flatMap_cons, decodePair_retains_code _ _ _ pair,
                    encodePairs_decode rest remaining next]
                  rfl
termination_by chars.length

/-- Successful decoding preserves the exact original code, not merely a
normalized alias of it. Unsupported symbols and unmatched carriers fail. -/
theorem encodeForm_decode (text : String) (cells : List Atom)
    (decoded : decodeForm text = some cells) : encodeForm cells = text := by
  have exactCode := encodePairs_decode text.toList cells decoded
  simpa [encodeForm] using congrArg String.ofList exactCode

theorem encodeForm_injective : Function.Injective encodeForm := by
  intro left right same
  have decoded := congrArg decodeForm same
  simpa only [decodeForm_encode, Option.some.injEq] using decoded

/-- Full witness identity is retained. The installed collector supplies the
source and reviews the lexical label; a name alone grants no membership. -/
structure Witness where
  id : String
  binding : Foundation.LayerBinding
  expression : String
  convention : String
  deriving DecidableEq, Repr

/-- The binding's surface is the ASCII FORM substring in its original source
record. It is not a fabricated Arabic quotation. -/
def Witness.decoded (witness : Witness) : Option (List Atom) :=
  decodeForm witness.binding.surface

def Witness.cells (witness : Witness) : List Atom := witness.decoded.getD []

def occurrenceBinding (source : Foundation.Source) (frame : Frame)
    (surface : String) : Foundation.LayerBinding :=
  ⟨source, frame.occurrence.context,
    toString frame.occurrence.startByte ++ ":" ++ toString frame.occurrence.endByte,
    frame.expression, frame.occurrence.startByte, frame.occurrence.endByte, surface⟩

def Available (ledger : List Witness) (witness : Witness) : Prop :=
  witness ∈ ledger ∧ witness.id ≠ "" ∧ witness.binding.Exact ∧
  witness.decoded.isSome = true ∧ witness.cells ≠ [] ∧
  witness.expression ≠ "" ∧ witness.convention ≠ ""

instance (ledger : List Witness) (witness : Witness) : Decidable (Available ledger witness) := by
  unfold Available
  infer_instance

/-- No orthographic equivalence is assumed: this first bridge admits only
the exact reviewed spelling, including every observed mark. -/
def Matches (source : Foundation.Source) (frame : Frame) (surface : String)
    (witness : Witness) : Prop :=
  CertifiedLexical.SourceBound source frame ∧
  (occurrenceBinding source frame surface).Exact ∧
  (occurrenceBinding source frame surface).projection.status = .complete ∧
  surface = renderArabic witness.cells ∧
  (occurrenceBinding source frame surface).projection.number = Sequence.encode witness.cells ∧
  frame.expression = witness.expression ∧ frame.convention = witness.convention

instance (source : Foundation.Source) (frame : Frame) (surface : String)
    (witness : Witness) : Decidable (Matches source frame surface witness) := by
  unfold Matches
  infer_instance

def checkWitness (source : Foundation.Source) (frame : Frame) (surface : String)
    (ledger : List Witness) (witness : Witness) : Bool :=
  decide (Available ledger witness ∧ Matches source frame surface witness)

def witnesses (source : Foundation.Source) (frame : Frame) (surface : String)
    (ledger : List Witness) : List Witness :=
  ledger.filter (checkWitness source frame surface ledger)

theorem checkWitness_exact (source : Foundation.Source) (frame : Frame) (surface : String)
    (ledger : List Witness) (witness : Witness) :
    checkWitness source frame surface ledger witness = true ↔
      Available ledger witness ∧ Matches source frame surface witness := by
  simp [checkWitness]

theorem witnesses_exact (source : Foundation.Source) (frame : Frame) (surface : String)
    (ledger : List Witness) (witness : Witness) :
    witness ∈ witnesses source frame surface ledger ↔
      Available ledger witness ∧ Matches source frame surface witness := by
  simp only [witnesses, List.mem_filter, checkWitness_exact]
  constructor
  · exact fun h => h.2
  · exact fun h => ⟨h.1.1, h⟩

theorem checked_occurrence_exact (source : Foundation.Source) (frame : Frame) (surface : String)
    (ledger : List Witness) (witness : Witness)
    (checked : checkWitness source frame surface ledger witness = true) :
    (occurrenceBinding source frame surface).Exact :=
  ((checkWitness_exact _ _ _ _ _).mp checked).2.2.1

theorem checked_source_witness_retained (source : Foundation.Source) (frame : Frame)
    (surface : String) (ledger : List Witness) (witness : Witness)
    (checked : checkWitness source frame surface ledger witness = true) :
    witness ∈ ledger ∧ witness.binding.Exact ∧
      witness.decoded.isSome = true := by
  have available := ((checkWitness_exact _ _ _ _ _).mp checked).1
  exact ⟨available.1, available.2.2.1, available.2.2.2.1⟩

theorem checked_surface_exact (source : Foundation.Source) (frame : Frame) (surface : String)
    (ledger : List Witness) (witness : Witness)
    (checked : checkWitness source frame surface ledger witness = true) :
    surface = renderArabic witness.cells :=
  ((checkWitness_exact _ _ _ _ _).mp checked).2.2.2.2.1

/-- Equality of the declared bijective116 numbers recovers every cell, so a
carrier or vowel change cannot hide behind the numerical representation. -/
theorem checked_cells_exact (source : Foundation.Source) (frame : Frame) (surface : String)
    (ledger : List Witness) (witness : Witness)
    (checked : checkWitness source frame surface ledger witness = true) :
    (occurrenceBinding source frame surface).projection.cells = witness.cells := by
  apply Sequence.encode_injective
  exact ((checkWitness_exact _ _ _ _ _).mp checked).2.2.2.2.2.1

theorem checked_expression_exact (source : Foundation.Source) (frame : Frame) (surface : String)
    (ledger : List Witness) (witness : Witness)
    (checked : checkWitness source frame surface ledger witness = true) :
    frame.expression = witness.expression ∧ frame.convention = witness.convention :=
  ((checkWitness_exact _ _ _ _ _).mp checked).2.2.2.2.2.2

theorem changed_surface_rejected (source : Foundation.Source) (frame : Frame) (surface : String)
    (ledger : List Witness) (witness : Witness)
    (changed : surface ≠ renderArabic witness.cells) :
    checkWitness source frame surface ledger witness = false := by
  apply Bool.eq_false_iff.mpr
  exact fun checked => changed (checked_surface_exact _ _ _ _ _ checked)

theorem changed_expression_rejected (source : Foundation.Source) (frame : Frame) (surface : String)
    (ledger : List Witness) (witness : Witness)
    (changed : frame.expression ≠ witness.expression) :
    checkWitness source frame surface ledger witness = false := by
  apply Bool.eq_false_iff.mpr
  exact fun checked => changed (checked_expression_exact _ _ _ _ _ checked).1

theorem missing_witness_rejected (source : Foundation.Source) (frame : Frame) (surface : String)
    (ledger : List Witness) (witness : Witness) (missing : witness ∉ ledger) :
    checkWitness source frame surface ledger witness = false := by
  apply Bool.eq_false_iff.mpr
  exact fun checked => missing (checked_source_witness_retained _ _ _ _ _ checked).1

theorem no_ledger_no_witness (source : Foundation.Source) (frame : Frame) (surface : String) :
    witnesses source frame surface [] = [] := by simp [witnesses]

/-- Additive composition: the existing candidate contract is unchanged, but
the new path additionally requires a nonempty exact-witness derivation. -/
def Ready (source : Foundation.Source) (cells : List Atom) (frame : Frame)
    (ds : List Designation) (rs : List Relation) (cs : List Candidate) (budget : Nat)
    (surface : String) (ledger : List Witness) : Prop :=
  CertifiedLexical.Ready source cells frame ds rs cs budget ∧
  witnesses source frame surface ledger ≠ []

instance (source : Foundation.Source) (cells : List Atom) (frame : Frame)
    (ds : List Designation) (rs : List Relation) (cs : List Candidate) (budget : Nat)
    (surface : String) (ledger : List Witness) :
    Decidable (Ready source cells frame ds rs cs budget surface ledger) := by
  unfold Ready
  infer_instance

def checkCandidates (source : Foundation.Source) (cells : List Atom) (frame : Frame)
    (ds : List Designation) (rs : List Relation) (cs : List Candidate) (budget : Nat)
    (surface : String) (ledger : List Witness) : Bool :=
  decide (Ready source cells frame ds rs cs budget surface ledger)

theorem checkCandidates_exact (source : Foundation.Source) (cells : List Atom) (frame : Frame)
    (ds : List Designation) (rs : List Relation) (cs : List Candidate) (budget : Nat)
    (surface : String) (ledger : List Witness) :
    checkCandidates source cells frame ds rs cs budget surface ledger = true ↔
      Ready source cells frame ds rs cs budget surface ledger := by simp [checkCandidates]

theorem checked_preserves_candidate_contract (source : Foundation.Source) (cells : List Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation) (cs : List Candidate)
    (budget : Nat) (surface : String) (ledger : List Witness)
    (checked : checkCandidates source cells frame ds rs cs budget surface ledger = true) :
    CertifiedLexical.checkCandidates source cells frame ds rs cs budget = true := by
  exact (CertifiedLexical.candidate_check_exact _ _ _ _ _ _ _).mpr
    (((checkCandidates_exact _ _ _ _ _ _ _ _ _).mp checked).1)

theorem checked_has_installed_witness (source : Foundation.Source) (cells : List Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation) (cs : List Candidate)
    (budget : Nat) (surface : String) (ledger : List Witness)
    (checked : checkCandidates source cells frame ds rs cs budget surface ledger = true) :
    ∃ witness, Available ledger witness ∧ Matches source frame surface witness := by
  have nonempty := ((checkCandidates_exact _ _ _ _ _ _ _ _ _).mp checked).2
  obtain ⟨witness, member⟩ := List.exists_mem_of_ne_nil _ nonempty
  exact ⟨witness, (witnesses_exact _ _ _ _ _).mp member⟩

theorem missing_witness_blocks_candidates (source : Foundation.Source) (cells : List Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation) (cs : List Candidate)
    (budget : Nat) (surface : String) (ledger : List Witness)
    (missing : witnesses source frame surface ledger = []) :
    checkCandidates source cells frame ds rs cs budget surface ledger = false := by
  simp [checkCandidates, Ready, missing]

/-- The new surface bridge cannot fill the inherited intended-use premise. -/
theorem witnessed_surface_does_not_supply_usage (source : Foundation.Source) (cells : List Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation) (cs : List Candidate)
    (budget : Nat) (surface : String) (ledger : List Witness) (candidate : Candidate)
    (_checked : checkCandidates source cells frame ds rs cs budget surface ledger = true) :
    assess frame candidate [] ≠ .supported := LinguisticTruth.no_evidence_no_support _ _

end Nabt.LexicalSurfaceBinding
