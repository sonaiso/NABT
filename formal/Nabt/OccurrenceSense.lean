import Nabt.ContextualReference
import Nabt.LexicalCompletionCatalog

/-!
Occurrence-bound acquisition of dictionary *candidates*, relative to a retained
QAC STEM-record ledger and the installed, authored headword alignment matrix.
The native law parses the records, checks the exact outer written occurrence,
enumerates every distinct morphological key and every installed candidate, and
runs the existing indication checker on each complete catalogue Sense.

Authenticity and completeness of extraction from the pinned source files remain
collector premises. A headword alignment is not a contextual sense license;
even a singleton candidate does not select a meaning. Context bytes are bound
without interpreting them. This law has no referent field, clause rule, or
external-world conclusion. Initial-reference receipts remain a separate branch.
-/
namespace Nabt.OccurrenceSense

open ContextualReference (Target Occurrence Donor ExactOccurrence decodeBuckwalter surfaceCompatible)
open LexicalDenotation (Sense Indication)

def lawId := "nabt.occurrence-sense-candidates.v1"
def matrixSha256 := "1c6444380a5192d45e040b893a822cb344384079aa4e89e174a363c5790b6368"
def catalogueSha256 := "1ac5b25629f7847e9f128cf2c75cfbe573657df769446afae3cc3436f566a872"
def donorSourceId := "qac_attested_source_v1"
def donorSourceRevision := "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46"
def donorSourceBytes := 6309503

/-- Exact Python word-reader whitespace set; it does not rewrite source bytes. -/
def spacing (c : Char) : Bool :=
  (9 ≤ c.toNat && c.toNat ≤ 13) || (28 ≤ c.toNat && c.toNat ≤ 32) ||
  [133, 160, 5760, 8232, 8233, 8239, 8287, 12288].contains c.toNat ||
  (8192 ≤ c.toNat && c.toNat ≤ 8202)

def punctuation (c : Char) : Bool := ".،؛,:!?؟()[]{}".toList.contains c
def closer (c : Char) : Option Char :=
  if c == '«' then some '»' else if c == '“' then some '”'
  else if c == Char.ofNat 34 then some (Char.ofNat 34) else none
def boundary (c : Char) : Bool := spacing c || punctuation c || (closer c).isSome
def byteLength (cs : List Char) := (String.ofList cs).utf8ByteSize

/-- Quotes are opaque spans and never enter the outer token enumeration.
The fuel is the original character count plus one; each step consumes input. -/
def scan : Nat → List Char → Nat → Option (List ContextualReference.Occurrence)
  | 0, _, _ => none
  | _ + 1, [], _ => some []
  | fuel + 1, c :: rest, offset => do
    if spacing c || punctuation c then
      scan fuel rest (offset + byteLength [c])
    else if let some closing := closer c then
      let inside := rest.takeWhile (· != closing)
      match rest.drop inside.length with
      | [] => none
      | last :: tail => scan fuel tail (offset + byteLength (c :: inside ++ [last]))
    else
      let tail := rest.takeWhile (fun char => !boundary char)
      let run := c :: tail
      let surface := String.ofList run
      let endByte := offset + surface.utf8ByteSize
      let remaining ← scan fuel (rest.drop tail.length) endByte
      return ⟨offset, endByte, surface⟩ :: remaining

def writtenRuns (text : String) : Option (List ContextualReference.Occurrence) :=
  scan (text.toList.length + 1) text.toList 0

structure Binding where
  source : Target
  occurrence : ContextualReference.Occurrence
  tokenIndex : Nat
  contextBinding : String
  target : List String
  deriving DecidableEq, Repr

def Binding.Exact (binding : Binding) : Prop :=
  ExactOccurrence binding.source binding.occurrence ∧
  (writtenRuns binding.source.text).bind (fun rows => rows[binding.tokenIndex]?) =
    some binding.occurrence

instance (binding : Binding) : Decidable binding.Exact := by
  unfold Binding.Exact
  infer_instance

structure MorphologyKey where
  sourceForm : String
  lemmaBW : Option String
  rootBW : Option String
  pos : String
  deriving DecidableEq, Repr

/-- Missing LEM/ROOT remains absent. Duplicate or empty annotations are invalid. -/
def feature (name : String) (tokens : List String) : Option (Option String) := do
  match tokens.filter (fun token => token.startsWith (name ++ ":")) with
  | [] => return none
  | [value] =>
    let value := String.ofList (value.toList.drop (name.length + 1))
    if value.isEmpty then none else return some value
  | _ => none

def parseRecord (donor : Donor) : Option MorphologyKey := do
  let fields := donor.record.trimAscii.toString.splitOn "\t"
  match fields with
  | [location, form, pos, features] =>
    let tokens := features.splitOn "|"
    if location.isEmpty || pos.isEmpty || tokens.head? != some "STEM" then none
    else if (← feature "POS" tokens) != some pos then none
    else return ⟨← decodeBuckwalter form, ← feature "LEM" tokens,
      ← feature "ROOT" tokens, pos⟩
  | _ => none

structure Input where
  binding : Binding
  donors : List Donor
  deriving DecidableEq, Repr

def supported (input : Input) (donor : Donor) : Prop :=
  donor.Valid input.donors ∧ donor.sourceId = donorSourceId ∧
  donor.sourceRevision = donorSourceRevision ∧ donor.endByte ≤ donorSourceBytes ∧
  ∃ key, parseRecord donor = some key ∧
    surfaceCompatible input.binding.occurrence.surface key.sourceForm = true

instance (input : Input) (donor : Donor) : Decidable (supported input donor) := by
  unfold supported
  cases parseRecord donor with
  | none => simp; infer_instance
  | some key => simp; infer_instance

def Input.Valid (input : Input) : Prop :=
  input.binding.Exact ∧ ∀ donor ∈ input.donors, supported input donor

instance (input : Input) : Decidable input.Valid := by
  unfold Input.Valid
  infer_instance

def morphologyKeys (donors : List Donor) : List MorphologyKey :=
  (donors.filterMap parseRecord).eraseDups

structure CandidateLink where
  lemmaBW : String
  rootBW : String
  pos : String
  senseId : String
  deriving DecidableEq, Repr

-- BEGIN FIXED CANDIDATE LINKS: generated mechanically from the pinned matrix.
def links : List CandidateLink := [
  ⟨"qalam", "qlm", "N", "lisan:qalam-writing"⟩,
  ⟨"qalam", "qlm", "N", "lisan:qalam-lot"⟩,
  ⟨"qalam", "qlm", "N", "lisan:qalam-gambling"⟩,
  ⟨"samoE", "smE", "N", "lisan:sama-hearing"⟩,
  ⟨"samoE", "smE", "N", "lisan:sama-ear"⟩,
  ⟨"baSar", "bSr", "N", "lisan:basar"⟩,
  ⟨"saqof", "sqf", "N", "lisan:saqf"⟩,
  ⟨"EamFY", "Emy", "N", "lisan:ama"⟩,
  ⟨">aroD", "ArD", "N", "lisan:v2:earth"⟩,
  ⟨"walad", "wld", "N", "lisan:v2:child"⟩,
  ⟨"*ahaAb", "*hb", "N", "lisan:v2:going"⟩,
  ⟨"xuruwj", "xrj", "N", "lisan:v2:exit"⟩,
  ⟨"Eilom", "Elm", "N", "lisan:v2:knowledge"⟩,
  ⟨"layol", "lyl", "N", "lisan:v2:night"⟩,
  ⟨"layol", "lyl", "T", "lisan:v2:night"⟩,
  ⟨"Hajar", "Hjr", "N", "lisan:v2:stone"⟩,
  ⟨"Hijor", "Hjr", "ADJ", "lisan:v2:stone"⟩,
  ⟨"Hijor", "Hjr", "N", "lisan:v2:stone"⟩,
  ⟨"samaA^'", "smw", "N", "lisan:v2:sky"⟩,
  ⟨"Eayon", "Eyn", "N", "lisan:v2:eye-vision"⟩,
  ⟨"Eiyn", "Eyn", "ADJ", "lisan:v2:eye-vision"⟩,
  ⟨"Eiyn", "Eyn", "N", "lisan:v2:eye-vision"⟩,
  ⟨"Eayon", "Eyn", "N", "lisan:v2:eye-spy"⟩,
  ⟨"Eiyn", "Eyn", "ADJ", "lisan:v2:eye-spy"⟩,
  ⟨"Eiyn", "Eyn", "N", "lisan:v2:eye-spy"⟩,
  ⟨"Eayon", "Eyn", "N", "lisan:v2:eye-spring"⟩,
  ⟨"Eiyn", "Eyn", "ADJ", "lisan:v2:eye-spring"⟩,
  ⟨"Eiyn", "Eyn", "N", "lisan:v2:eye-spring"⟩,
  ⟨"Eayon", "Eyn", "N", "lisan:v2:eye-cash"⟩,
  ⟨"Eiyn", "Eyn", "ADJ", "lisan:v2:eye-cash"⟩,
  ⟨"Eiyn", "Eyn", "N", "lisan:v2:eye-cash"⟩,
  ⟨"Eayon", "Eyn", "N", "lisan:v2:eye-letter"⟩,
  ⟨"Eiyn", "Eyn", "ADJ", "lisan:v2:eye-letter"⟩,
  ⟨"Eiyn", "Eyn", "N", "lisan:v2:eye-letter"⟩,
  ⟨"$amos", "$ms", "N", "lisan:v2:sun-deictic"⟩,
  ⟨"$ajar", "$jr", "N", "lisan:v2:tree-stem"⟩,
  ⟨"$ajar", "$jr", "N", "lisan:v2:tree-rising"⟩,
  ⟨"rajul", "rjl", "N", "lisan:v2:man"⟩,
  ⟨"rajil", "rjl", "N", "lisan:v2:man"⟩,
  ⟨"rijol", "rjl", "N", "lisan:v2:man"⟩,
  ⟨"Sidoq", "Sdq", "N", "lisan:v2:truth"⟩,
  ⟨"ka*ib", "k*b", "N", "lisan:v2:falsehood"⟩
]
-- END FIXED CANDIDATE LINKS

def CandidateLink.Matches (link : CandidateLink) (key : MorphologyKey) : Prop :=
  key.lemmaBW = some link.lemmaBW ∧ key.rootBW = some link.rootBW ∧ key.pos = link.pos

instance (link : CandidateLink) (key : MorphologyKey) : Decidable (link.Matches key) := by
  unfold CandidateLink.Matches
  infer_instance

def Linked (key : MorphologyKey) (sense : Sense) : Prop :=
  ∃ link ∈ links, link.senseId = sense.id ∧ link.Matches key

instance (key : MorphologyKey) (sense : Sense) : Decidable (Linked key sense) := by
  unfold Linked
  infer_instance

def dictionaryCandidates (key : MorphologyKey) : List Sense :=
  LexicalCompletionCatalog.senses.filter (fun sense => decide (Linked key sense))

structure SenseResult where
  sense : Sense
  mutabaqa : Bool
  tadammun : Bool
  iltizam : Bool
  deriving DecidableEq, Repr

def evaluate (target : List String) (sense : Sense) : SenseResult :=
  ⟨sense,
    LexicalDenotation.check LexicalCompletionCatalog.necessities sense .matching target,
    LexicalDenotation.check LexicalCompletionCatalog.necessities sense .inclusion target,
    LexicalDenotation.check LexicalCompletionCatalog.necessities sense .entailment target⟩

structure ReadingResult where
  key : MorphologyKey
  donorIds : List String
  senses : List SenseResult
  deriving DecidableEq, Repr

def readingResult (input : Input) (key : MorphologyKey) : ReadingResult :=
  ⟨key, (input.donors.filter (fun donor => parseRecord donor == some key)).map Donor.id,
    (dictionaryCandidates key).map (evaluate input.binding.target)⟩

def readingResults (input : Input) : List ReadingResult :=
  (morphologyKeys input.donors).map (readingResult input)

inductive Status where
  | candidatesOnly | partialCandidates | noDictionaryCandidate | noMorphologyReading | resourceLimit
  deriving DecidableEq, Repr

def Status.label : Status → String
  | .candidatesOnly => "CANDIDATES_ONLY"
  | .partialCandidates => "PARTIAL_CANDIDATES"
  | .noDictionaryCandidate => "NO_DICTIONARY_CANDIDATE"
  | .noMorphologyReading => "NO_MORPHOLOGY_READING"
  | .resourceLimit => "RESOURCE_LIMIT"

structure Receipt where
  binding : Binding
  budget : Nat
  status : Status
  readings : List ReadingResult
  deriving DecidableEq, Repr

def receipt (input : Input) (budget : Nat) : Receipt :=
  let keys := morphologyKeys input.donors
  if keys.length > min budget 256 then ⟨input.binding, budget, .resourceLimit, []⟩
  else if keys.isEmpty then ⟨input.binding, budget, .noMorphologyReading, []⟩
  else
    let rows := readingResults input
    let status := if rows.all (fun row => row.senses.isEmpty) then .noDictionaryCandidate
      else if rows.any (fun row => row.senses.isEmpty) then .partialCandidates
      else .candidatesOnly
    ⟨input.binding, budget, status, rows⟩

def checkReceipt (input : Input) (budget : Nat) (proposed : Receipt) : Bool :=
  decide (input.Valid ∧ proposed = receipt input budget)

theorem checked_receipt_exact (input : Input) (budget : Nat) (proposed : Receipt)
    (checked : checkReceipt input budget proposed = true) : proposed = receipt input budget := by
  exact (of_decide_eq_true checked).2

theorem checked_source_and_scope (input : Input) (budget : Nat) (proposed : Receipt)
    (checked : checkReceipt input budget proposed = true) : input.binding.Exact := by
  exact (of_decide_eq_true checked).1.1

theorem checked_all_donors_supported (input : Input) (budget : Nat) (proposed : Receipt)
    (checked : checkReceipt input budget proposed = true) :
    ∀ donor ∈ input.donors, supported input donor := by
  exact (of_decide_eq_true checked).1.2

theorem receipt_keeps_complete_binding (input : Input) (budget : Nat) :
    (receipt input budget).binding = input.binding := by
  unfold receipt
  dsimp only
  split <;> simp_all
  split <;> rfl

theorem checked_keeps_complete_binding (input : Input) (budget : Nat) (proposed : Receipt)
    (checked : checkReceipt input budget proposed = true) : proposed.binding = input.binding := by
  rw [checked_receipt_exact input budget proposed checked]
  exact receipt_keeps_complete_binding input budget

theorem receipt_keeps_supplied_budget (input : Input) (budget : Nat) :
    (receipt input budget).budget = budget := by
  unfold receipt
  dsimp only
  split <;> simp_all
  split <;> rfl

theorem budget_change_invalidates_old_receipt (input : Input) (budget changed : Nat)
    (proposed : Receipt) (checked : checkReceipt input budget proposed = true)
    (different : budget ≠ changed) : checkReceipt input changed proposed = false := by
  cases h : checkReceipt input changed proposed with
  | false => rfl
  | true =>
    have first := congrArg Receipt.budget (checked_receipt_exact input budget proposed checked)
    have second := congrArg Receipt.budget (checked_receipt_exact input changed proposed h)
    rw [receipt_keeps_supplied_budget] at first second
    exact False.elim (different (first.symm.trans second))

theorem context_swap_invalidates_old_receipt (input changed : Input) (budget : Nat)
    (proposed : Receipt) (checked : checkReceipt input budget proposed = true)
    (different : input.binding.contextBinding ≠ changed.binding.contextBinding) :
    checkReceipt changed budget proposed = false := by
  cases h : checkReceipt changed budget proposed with
  | false => rfl
  | true =>
    have first := checked_keeps_complete_binding input budget proposed checked
    have second := checked_keeps_complete_binding changed budget proposed h
    exact False.elim (different (congrArg Binding.contextBinding (first.symm.trans second)))

theorem every_morphology_key_retained (input : Input) (key : MorphologyKey)
    (member : key ∈ morphologyKeys input.donors) : readingResult input key ∈ readingResults input := by
  exact List.mem_map.mpr ⟨key, member, rfl⟩

theorem every_parsed_donor_key_retained (donors : List Donor) (donor : Donor)
    (key : MorphologyKey) (member : donor ∈ donors) (parsed : parseRecord donor = some key) :
    key ∈ morphologyKeys donors := by
  simp only [morphologyKeys, List.mem_eraseDups, List.mem_filterMap]
  exact ⟨donor, member, parsed⟩

theorem morphology_key_has_retained_record (donors : List Donor) (key : MorphologyKey)
    (member : key ∈ morphologyKeys donors) :
    ∃ donor ∈ donors, parseRecord donor = some key := by
  simpa only [morphologyKeys, List.mem_eraseDups, List.mem_filterMap] using member

theorem no_invented_morphology_reading (input : Input) (row : ReadingResult)
    (member : row ∈ readingResults input) :
    ∃ key ∈ morphologyKeys input.donors, row = readingResult input key := by
  obtain ⟨key, mem, eq⟩ := List.mem_map.mp member
  exact ⟨key, mem, eq.symm⟩

theorem dictionary_candidates_exact (key : MorphologyKey) (sense : Sense) :
    sense ∈ dictionaryCandidates key ↔ sense ∈ LexicalCompletionCatalog.senses ∧ Linked key sense := by
  simp [dictionaryCandidates]

theorem missing_lemma_has_no_dictionary_candidate (key : MorphologyKey)
    (missing : key.lemmaBW = none) : dictionaryCandidates key = [] := by
  apply List.eq_nil_iff_forall_not_mem.mpr
  intro sense member
  obtain ⟨_, link, _, _, matched⟩ := (dictionary_candidates_exact key sense).mp member
  simp [CandidateLink.Matches, missing] at matched

theorem every_dictionary_candidate_retained (input : Input) (key : MorphologyKey) (sense : Sense)
    (member : sense ∈ dictionaryCandidates key) :
    evaluate input.binding.target sense ∈ (readingResult input key).senses := by
  exact List.mem_map.mpr ⟨sense, member, rfl⟩

theorem returned_sense_requires_catalogue_and_link (input : Input) (key : MorphologyKey)
    (result : SenseResult) (member : result ∈ (readingResult input key).senses) :
    result.sense ∈ LexicalCompletionCatalog.senses ∧ Linked key result.sense := by
  obtain ⟨sense, mem, eq⟩ := List.mem_map.mp member
  subst result
  exact (dictionary_candidates_exact key sense).mp mem

theorem per_sense_indications_exact (target : List String) (sense : Sense) :
    ((evaluate target sense).mutabaqa = true ↔
      LexicalDenotation.Admitted LexicalCompletionCatalog.necessities sense .matching target) ∧
    ((evaluate target sense).tadammun = true ↔
      LexicalDenotation.Admitted LexicalCompletionCatalog.necessities sense .inclusion target) ∧
    ((evaluate target sense).iltizam = true ↔
      LexicalDenotation.Admitted LexicalCompletionCatalog.necessities sense .entailment target) := by
  exact ⟨LexicalDenotation.check_exact _ _ _ _, LexicalDenotation.check_exact _ _ _ _,
    LexicalDenotation.check_exact _ _ _ _⟩

theorem unmatched_morphology_retained (input : Input) (key : MorphologyKey)
    (member : key ∈ morphologyKeys input.donors) (unmatched : dictionaryCandidates key = []) :
    readingResult input key ∈ readingResults input ∧ (readingResult input key).senses = [] := by
  exact ⟨every_morphology_key_retained input key member, by simp [readingResult, unmatched]⟩

theorem insufficient_budget_has_no_readings (input : Input) (budget : Nat)
    (insufficient : budget < (morphologyKeys input.donors).length) :
    (receipt input budget).status = .resourceLimit ∧ (receipt input budget).readings = [] := by
  have effective : min budget 256 < (morphologyKeys input.donors).length :=
    Nat.lt_of_le_of_lt (Nat.min_le_left _ _) insufficient
  simp [receipt, effective]

theorem sufficient_budget_preserves_all_readings (input : Input) (budget : Nat)
    (sufficient : (morphologyKeys input.donors).length ≤ min budget 256) :
    (receipt input budget).readings = readingResults input := by
  unfold receipt
  dsimp only
  simp only [Nat.not_lt.mpr sufficient, ↓reduceIte]
  split
  next empty =>
    have zero : morphologyKeys input.donors = [] := List.isEmpty_iff.mp empty
    simp [readingResults, zero]
  next => rfl

theorem no_morphology_no_sense (binding : Binding) (budget : Nat) :
    (receipt ⟨binding, []⟩ budget).status = .noMorphologyReading ∧
    (receipt ⟨binding, []⟩ budget).readings = [] := by
  simp [receipt, morphologyKeys]

end Nabt.OccurrenceSense
