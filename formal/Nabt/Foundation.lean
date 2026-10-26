import Nabt.Cell
import Nabt.Sequence

/-! Exact source-bound A116 representation. COMPLETE licenses representation
only, never word shape, lexical meaning, reference or world truth. Unsupported
orthography remains residual; no missing vowel is inferred. -/
namespace Nabt.Foundation

def lawId : String := "nabt.foundation.v1"
def alphabetId : String := "nabt.a116.v1"
def numberDomain : String := "nabt.foundation.projected-cells.bijective116.v1"
def shapeLawId : String := "nabt-sound-shape-v1"
def marks : List String := ["َ", "ُ", "ِ", "ْ"]

structure Source where
  id : String
  revision : String
  text : String
  deriving DecidableEq, Repr
inductive Kind where
  | cell (atom : Atom)
  | separator
  | residual
  deriving DecidableEq, Repr
structure Piece where
  raw : List Char
  kind : Kind
  issues : List String
  deriving DecidableEq, Repr

def Piece.cell : Piece → Option Atom
  | ⟨_, .cell atom, _⟩ => some atom
  | _ => none

def Piece.text (piece : Piece) : String := String.ofList piece.raw

def isMark (c : Char) : Bool :=
  let n := c.toNat
  (0x064B ≤ n && n ≤ 0x065F) || n == 0x0670 || (0x06D6 ≤ n && n ≤ 0x06ED)
def isVowel (c : Char) : Bool :=
  let n := c.toNat
  (0x064B ≤ n && n ≤ 0x0650) || n == 0x0652

def separator (c : Char) : Bool :=
  [9, 10, 13, 32].contains c.toNat ||
    (".،؛,:!?؟()[]{}«»\"“”".toList.contains c)
def carrier (c : Char) : Option Carrier :=
  (List.finRange 29).find? (fun i => canonicalCarriers[i.val]? == some (String.ofList [c]))
def mark : Char → Option Mark
  | 'َ' => some 0 | 'ُ' => some 1 | 'ِ' => some 2 | 'ْ' => some 3 | _ => none

/-- Validation runs on all clusters, including unsupported hamza seats. -/
def clusterIssues : List Char → List String
  | [] => []
  | c :: rest =>
    if isMark c then ["MARK_WITHOUT_CARRIER"]
    else if rest.eraseDups.length != rest.length ||
        (rest.filter isVowel).length > 1 then ["CONFLICTING_MARKS"] else []

def classify (raw : List Char) : Piece :=
  let issues := clusterIssues raw
  let kind := match raw with
    | [c] => if separator c then Kind.separator else .residual
    | [c, m] => match carrier c, mark m with
      | some carrier, some mark => .cell (Cell.encode ⟨carrier, mark⟩)
      | _, _ => .residual
    | _ => .residual
  let issues := if !issues.isEmpty then issues else match kind with
    | .residual => match raw with
      | [c] => if (carrier c).isSome then ["MISSING_VOCALIZATION"] else ["UNSUPPORTED_ORTHOGRAPHY"]
      | _ => ["UNSUPPORTED_ORTHOGRAPHY"]
    | _ => []
  ⟨raw, kind, issues⟩
theorem classify_preserves_raw (raw : List Char) : (classify raw).raw = raw := rfl

set_option maxRecDepth 10000 in
set_option maxHeartbeats 3000000 in
/-- Exhaustive kernel check of the installed named carrier/mark table. -/
theorem all_116_cells_project : ∀ atom : Atom,
    (classify ((canonicalCarriers.getD (Cell.decode atom).carrier.val "").toList ++
      (marks.getD (Cell.decode atom).mark.val "").toList)).kind = .cell atom := by
  decide +kernel

def takeMarks : List Char → List Char × List Char
  | [] => ([], [])
  | c :: rest =>
    if isMark c then
      let split := takeMarks rest
      (c :: split.1, split.2)
    else ([], c :: rest)

theorem takeMarks_reconstruct (chars : List Char) :
    (takeMarks chars).1 ++ (takeMarks chars).2 = chars := by
  induction chars with
  | nil => rfl
  | cons c rest ih =>
    simp only [takeMarks]
    split
    · simp only [List.cons_append, List.cons.injEq, true_and]
      exact ih
    · rfl

/-- Exhaustion retains the entire remaining source as an invalid residual. -/
def piecesAux : Nat → List Char → List Piece
  | 0, [] => []
  | 0, chars@(_ :: _) => [⟨chars, .residual, ["RESOURCE_LIMIT"]⟩]
  | _ + 1, [] => []
  | fuel + 1, c :: rest =>
    if separator c then classify [c] :: piecesAux fuel rest
    else
      let split := takeMarks rest
      classify (c :: split.1) :: piecesAux fuel split.2

theorem piecesAux_reconstruct (fuel : Nat) (chars : List Char) :
    (piecesAux fuel chars).flatMap Piece.raw = chars := by
  induction fuel generalizing chars with
  | zero => cases chars <;> simp [piecesAux]
  | succ fuel ih =>
    cases chars with
    | nil => rfl
    | cons c rest =>
      simp only [piecesAux]
      split
      · simp only [List.flatMap_cons, classify_preserves_raw, ih, List.singleton_append]
      · simp only [List.flatMap_cons, classify_preserves_raw, ih, List.cons_append]
        exact congrArg (List.cons c) (takeMarks_reconstruct rest)

def pieces (source : Source) : List Piece :=
  piecesAux (source.text.toList.length + 1) source.text.toList
def restore (items : List Piece) : String := String.ofList (items.flatMap Piece.raw)
theorem projection_restores_source (source : Source) : restore (pieces source) = source.text := by
  simp only [restore, pieces, piecesAux_reconstruct, String.ofList_toList]

inductive Status where
  | complete | incomplete | invalid
  deriving DecidableEq, Repr

def Status.label : Status → String
  | .complete => "COMPLETE" | .incomplete => "PARTIAL" | .invalid => "INVALID"
def status (source : Source) (items : List Piece) : Status :=
  if source.text.isEmpty || items.any (fun piece => piece.issues.any (fun code =>
      ["MARK_WITHOUT_CARRIER", "CONFLICTING_MARKS", "RESOURCE_LIMIT"].contains code)) then .invalid
  else if items.any (fun piece => piece.kind == .residual) then .incomplete
  else .complete
structure Receipt where
  source : Source
  items : List Piece
  status : Status
  deriving DecidableEq, Repr

def project (source : Source) : Receipt :=
  let items := pieces source
  ⟨source, items, status source items⟩
def Receipt.cells (receipt : Receipt) : List Atom := receipt.items.filterMap Piece.cell
def Receipt.number (receipt : Receipt) : Nat := Sequence.encode receipt.cells

/-- Fresh projection is the authority, not caller flags or digests. -/
def checkReceipt (expected : Source) (proposed : Receipt) : Bool :=
  decide (proposed = project expected)
theorem checkReceipt_exact (expected : Source) (proposed : Receipt) :
    checkReceipt expected proposed = true ↔ proposed = project expected := by simp [checkReceipt]
theorem checked_source_exact (expected : Source) (proposed : Receipt)
    (checked : checkReceipt expected proposed = true) : proposed.source = expected := by
  rw [(checkReceipt_exact _ _).mp checked]
  rfl
theorem checked_identity_exact (expected : Source) (proposed : Receipt)
    (checked : checkReceipt expected proposed = true) :
    proposed.source.id = expected.id ∧ proposed.source.revision = expected.revision := by
  rw [checked_source_exact _ _ checked]
  exact ⟨rfl, rfl⟩
theorem checked_receipt_restores_source (expected : Source) (proposed : Receipt)
    (checked : checkReceipt expected proposed = true) : restore proposed.items = expected.text := by
  rw [(checkReceipt_exact _ _).mp checked]
  exact projection_restores_source expected
theorem projected_cells_bounded (receipt : Receipt) (atom : Atom)
    (_member : atom ∈ receipt.cells) : atom.val < 116 := atom.isLt
theorem number_restores_cells (receipt : Receipt) :
    Sequence.decode receipt.number = receipt.cells := Sequence.decode_encode _
theorem checked_number_exact (expected : Source) (proposed : Receipt)
    (checked : checkReceipt expected proposed = true) :
    proposed.number = Sequence.encode (project expected).cells := by
  rw [(checkReceipt_exact _ _).mp checked]
  rfl
theorem partial_not_promoted (expected : Source) (proposed : Receipt)
    (incomplete : (project expected).status = .incomplete)
    (checked : checkReceipt expected proposed = true) : proposed.status ≠ .complete := by
  rw [(checkReceipt_exact _ _).mp checked, incomplete]
  decide
theorem invalid_not_promoted (expected : Source) (proposed : Receipt)
    (invalid : (project expected).status = .invalid)
    (checked : checkReceipt expected proposed = true) : proposed.status ≠ .complete := by
  rw [(checkReceipt_exact _ _).mp checked, invalid]
  decide
theorem changed_source_rejected (expected : Source) (proposed : Receipt)
    (changed : proposed.source ≠ expected) : checkReceipt expected proposed = false := by
  cases check : checkReceipt expected proposed with
  | false => rfl
  | true => exact False.elim (changed (checked_source_exact _ _ check))

/-! Reusable numerical layer binding. Exact source occurrence and reading are
retained; operations compute cells and never assert their linguistic meaning. -/
def transformLawId : String := "nabt.foundation.cell-transform.v1"
structure LayerBinding where
  source : Source
  scopeId : String
  occurrenceId : String
  readingId : String
  startByte : Nat
  endByte : Nat
  surface : String
  deriving DecidableEq, Repr

/-- Full-source cluster boundaries, including declared separators. A local
numeric operation cannot hide an observed following mark by cutting its cluster.
Residuals elsewhere in the source do not invalidate a complete local span. -/
def pieceBoundaries (offset : Nat) : List Piece → List Nat
  | [] => [offset]
  | piece :: rest => offset :: pieceBoundaries (offset + piece.text.utf8ByteSize) rest

def sourceBoundaries (source : Source) : List Nat := pieceBoundaries 0 (pieces source)

def LayerBinding.Exact (binding : LayerBinding) : Prop :=
  binding.startByte < binding.endByte ∧
  binding.endByte ≤ binding.source.text.utf8ByteSize ∧
  binding.startByte ∈ sourceBoundaries binding.source ∧
  binding.endByte ∈ sourceBoundaries binding.source ∧
  (binding.source.text.toUTF8.data.toList.drop binding.startByte).take
      (binding.endByte - binding.startByte) = binding.surface.toUTF8.data.toList
instance (binding : LayerBinding) : Decidable binding.Exact := by
  unfold LayerBinding.Exact
  infer_instance

def LayerBinding.projection (binding : LayerBinding) : Receipt :=
  project ⟨binding.source.id, binding.source.revision, binding.surface⟩
inductive Operation where
  | keep
  | append (suffix : List Atom)
  | replace (index : Nat) (atom : Atom)
  deriving DecidableEq, Repr

def Operation.run (operation : Operation) (input : List Atom) : Option (List Atom) :=
  match operation with
  | .keep => some input
  | .append suffix => some (input ++ suffix)
  | .replace index atom => if index < input.length then some (input.set index atom) else none
structure TransformReceipt where
  binding : LayerBinding
  law : String
  operation : Operation
  input : List Atom
  output : List Atom
  deriving DecidableEq, Repr

def checkTransform (expected : LayerBinding) (operation : Operation)
    (receipt : TransformReceipt) : Bool :=
  decide (expected.Exact ∧ receipt.binding = expected ∧ receipt.law = transformLawId ∧
    receipt.operation = operation ∧ expected.projection.status = .complete ∧
    receipt.input = expected.projection.cells ∧
    operation.run receipt.input = some receipt.output)
theorem checked_transform_exact (expected : LayerBinding) (operation : Operation)
    (receipt : TransformReceipt) (checked : checkTransform expected operation receipt = true) :
    expected.Exact ∧ receipt.binding = expected ∧ receipt.law = transformLawId ∧
    receipt.operation = operation ∧ expected.projection.status = .complete ∧
    receipt.input = expected.projection.cells ∧
    operation.run receipt.input = some receipt.output := of_decide_eq_true checked

theorem checked_transform_preserves_binding (expected : LayerBinding) (operation : Operation)
    (receipt : TransformReceipt) (checked : checkTransform expected operation receipt = true) :
    receipt.binding = expected := (checked_transform_exact _ _ _ checked).2.1

theorem checked_transform_computes_output (expected : LayerBinding) (operation : Operation)
    (receipt : TransformReceipt) (checked : checkTransform expected operation receipt = true) :
    operation.run expected.projection.cells = some receipt.output := by
  have exact := checked_transform_exact _ _ _ checked
  rw [← exact.2.2.2.2.2.1]
  exact exact.2.2.2.2.2.2

theorem checked_append_number (expected : LayerBinding) (suffix : List Atom)
    (receipt : TransformReceipt) (checked : checkTransform expected (.append suffix) receipt = true) :
    Sequence.encode receipt.output =
      116 ^ suffix.length * Sequence.encode receipt.input + Sequence.encode suffix := by
  have output := (checked_transform_exact _ _ _ checked).2.2.2.2.2.2
  have same : receipt.input ++ suffix = receipt.output := Option.some.inj output
  rw [← same]
  exact Sequence.encode_append _ _

theorem changed_reading_rejected (expected : LayerBinding) (operation : Operation)
    (receipt : TransformReceipt) (different : receipt.binding.readingId ≠ expected.readingId) :
    checkTransform expected operation receipt = false := by
  cases h : checkTransform expected operation receipt with
  | false => rfl
  | true => exact False.elim (different (congrArg LayerBinding.readingId
      (checked_transform_preserves_binding _ _ _ h)))

end Nabt.Foundation
