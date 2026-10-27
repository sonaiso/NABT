import Nabt.AttestedLexicalLoading
import Nabt.DiscourseEvidence
import Nabt.PersonEvidence

/-!
Initial-occurrence reference relative to a retained QAC interpretation ledger
and an explicit context. The ledger is an acquisition premise. Record bytes,
QAC FORM/part-of-speech/profile columns, the exact target interval, and every
context alternative are checked; authenticity of the full corpus extraction
and linguistic adequacy of the declared spelling policy remain separate.

This does not license the containing clause, acquire a dictionary sense, assert
an external event or motive, assess transmission frequency, or cover Arabic.
The initial-position restriction prevents an unparsed preceding quotation or
report from silently reusing the outer speaker. Noninitial occurrences need a
future independently licensed scope bridge.
-/
namespace Nabt.ContextualReference

open ClassicalLanguageEvidence (Source Passage Attested)
open DiscourseEvidence (Compatibility ReferenceOrigin SelectionStatus)

def lawId := "nabt.initial-contextual-reference.v1"

structure Target where
  id : String
  revision : String
  text : String
  deriving DecidableEq, Repr

structure Occurrence where
  startByte : Nat
  endByte : Nat
  surface : String
  deriving DecidableEq, Repr

def Target.source (target : Target) : Source :=
  ⟨target.id, .targetText, "initial-reference-input", target.revision,
    target.text.toUTF8.toList⟩

def Occurrence.passage (occurrence : Occurrence) (target : Target) : Passage :=
  ⟨target.source, occurrence.startByte, occurrence.surface.toUTF8.toList⟩

def ExactOccurrence (target : Target) (occurrence : Occurrence) : Prop :=
  Attested [target.source] (occurrence.passage target) ∧
  occurrence.endByte = occurrence.startByte + occurrence.surface.utf8ByteSize

instance (target : Target) (occurrence : Occurrence) : Decidable (ExactOccurrence target occurrence) := by
  unfold ExactOccurrence
  infer_instance

def asciiSpace (byte : UInt8) : Bool :=
  byte == 9 || byte == 10 || byte == 13 || byte == 32

def boundaryAfter (target : Target) (occurrence : Occurrence) : Bool :=
  let tail := target.text.toUTF8.toList.drop occurrence.endByte
  tail.isEmpty || [" ", "\t", "\r", "\n", ".", ",", "!", "?", ":", ";", "،", "؛", "؟"].any
    (fun mark => mark.toUTF8.toList.isPrefixOf tail)

def initialScope (target : Target) (occurrence : Occurrence) : Bool :=
  (target.text.toUTF8.toList.take occurrence.startByte).all asciiSpace &&
  boundaryAfter target occurrence

structure Donor where
  id : String
  sourceId : String
  sourceRevision : String
  startByte : Nat
  endByte : Nat
  record : String
  deriving DecidableEq, Repr

/-- A retained record is the full source value at this level. Original corpus
offsets remain explicit. Membership in the complete authenticated QAC file is
an obligation of the installed collector, not inferred from a digest label. -/
def Donor.source (donor : Donor) : Source :=
  ⟨donor.sourceId, .targetText, donor.id ++ "@" ++ toString donor.startByte,
    donor.sourceRevision, donor.record.toUTF8.toList⟩

def Donor.passage (donor : Donor) : Passage :=
  ⟨donor.source, 0, donor.record.toUTF8.toList⟩

def Donor.Valid (donors : List Donor) (donor : Donor) : Prop :=
  donor ∈ donors ∧ Attested (donors.map Donor.source) donor.passage ∧
  donor.endByte = donor.startByte + donor.record.utf8ByteSize

instance (donors : List Donor) (donor : Donor) : Decidable (donor.Valid donors) := by
  unfold Donor.Valid
  infer_instance

inductive PartOfSpeech where
  | pronoun | demonstrative | other
  deriving DecidableEq, Repr

def PartOfSpeech.label : PartOfSpeech → String
  | .pronoun => "PRON" | .demonstrative => "DEM" | .other => "OTHER"

structure Alternative where
  id : String
  pos : PartOfSpeech
  profile : Option PersonEvidence.Profile
  targetSurface : String
  sourceForm : String
  donorIds : List String
  deriving DecidableEq, Repr

def Alternative.origin (alternative : Alternative) : Option ReferenceOrigin := do
  let profile ← alternative.profile
  if !(PersonEvidence.profiles.contains profile) then none
  else match alternative.pos, profile.person with
    | .pronoun, 1 => some .speaker
    | .pronoun, 2 => some .addressee
    | .demonstrative, 3 => some .deictic
    | _, _ => none

/-- Versioned documentary transliteration. Unknown Buckwalter symbols fail;
this is a character mapping, not a lexical or external-world assertion. -/
def buckwalterPairs : List (Char × Char) :=
  "'>&<}AbptvjHxd*rzs$SDTZEgfqklmnhwYyFNKaui~o^#`{".toList.zip
    "ءأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوىيًٌٍَُِّْٰٓٔٱ".toList ++
  [(':', Char.ofNat 0x06DC), ('@', Char.ofNat 0x06DF),
   (Char.ofNat 34, Char.ofNat 0x06E0), ('[', Char.ofNat 0x06E2),
   (';', Char.ofNat 0x06E3), (',', Char.ofNat 0x06E5), ('.', Char.ofNat 0x06E6),
   ('!', Char.ofNat 0x06E8), ('-', Char.ofNat 0x06EA), ('+', Char.ofNat 0x06EB),
   ('%', Char.ofNat 0x06EC), (']', Char.ofNat 0x06ED), ('_', 'ـ'), (' ', ' ')]

def decodeBuckwalter (encoded : String) : Option String := do
  let decoded ← encoded.toList.mapM (fun char => (buckwalterPairs.find? (fun p => p.1 == char)).map Prod.snd)
  return String.ofList decoded

structure SpellingCluster where
  carrier : Char
  marks : List Char
  deriving DecidableEq, Repr

def vowel (char : Char) : Bool := "ًٌٍَُِْ".toList.contains char

def mark (char : Char) : Bool := vowel char || char == 'ّ' || char == 'ٰ'

def carrier (char : Char) : Bool :=
  (0x0621 ≤ char.toNat && char.toNat ≤ 0x063A) ||
  (0x0641 ≤ char.toNat && char.toNat ≤ 0x064A) || char == 'ٱ'

/-- Unlike deleting all diacritics, this keeps shadda and every explicit mark.
Repeated marks and two vowel marks on one carrier are invalid. -/
def clusters (text : String) : Option (List SpellingCluster) := do
  let mut result : List SpellingCluster := []
  for char in text.toList do
    if mark char then
      let first :: rest := result | none
      if first.marks.contains char || (vowel char && first.marks.any vowel) then none
      else result := {first with marks := char :: first.marks} :: rest
    else if carrier char then
      result := ⟨if char == 'ٱ' then 'ا' else char, []⟩ :: result
    else none
  if result.isEmpty then none else return result.reverse

def clusterCompatible (observed expected : SpellingCluster) : Bool :=
  observed.carrier == expected.carrier &&
  (observed.marks.filter vowel).all (fun v =>
    !(expected.marks.any vowel) || expected.marks.contains v) &&
  (!observed.marks.contains 'ّ' || expected.marks.contains 'ّ') &&
  (!observed.marks.contains 'ٰ' || expected.marks.contains 'ٰ')

/-- qac.initial-reference-observed-spelling.v1: no stem edits, hamza collapse,
or guessed letters. Missing marks do not become positive observed evidence. -/
def surfaceCompatible (observed expected : String) : Bool :=
  match clusters observed, clusters expected with
  | some left, some right => left.length == right.length &&
      (left.zip right).all (fun pair => clusterCompatible pair.1 pair.2)
  | _, _ => false

def Donor.annotationMatches (donor : Donor) (alternative : Alternative) : Bool :=
  match alternative.profile with
  | none => false
  | some profile =>
    let fields := donor.record.trimAscii.toString.splitOn "\t"
    let wanted := if alternative.pos = .demonstrative then String.ofList profile.qac.toList.tail
      else profile.qac
    match fields with
    | [_location, form, pos, features] =>
      decodeBuckwalter form == some alternative.sourceForm &&
      surfaceCompatible alternative.targetSurface alternative.sourceForm &&
      pos == alternative.pos.label && (features.splitOn "|").contains ("POS:" ++ pos) &&
      (features.splitOn "|").contains wanted
    | _ => false

def Alternative.Supported (donors : List Donor) (occurrence : Occurrence)
    (alternative : Alternative) : Prop :=
  alternative.targetSurface = occurrence.surface ∧ alternative.sourceForm ≠ "" ∧
  alternative.donorIds ≠ [] ∧ alternative.origin.isSome = true ∧
  ∀ id ∈ alternative.donorIds, ∃ donor ∈ donors,
    donor.id = id ∧ donor.Valid donors ∧ donor.annotationMatches alternative = true

instance (donors : List Donor) (occurrence : Occurrence) (alternative : Alternative) :
    Decidable (alternative.Supported donors occurrence) := by
  unfold Alternative.Supported
  infer_instance

structure Entity where
  id : String
  name : String
  gender : Option Nat
  number : Option Nat
  kind : String
  deriving DecidableEq, Repr

structure Deixis where
  form : String
  entityIds : List String
  deriving DecidableEq, Repr

structure Context where
  entities : List Entity
  speaker : Option String
  addressee : Option String
  deixis : List Deixis
  closedReferenceScope : Bool
  deriving DecidableEq, Repr

structure Input where
  target : Target
  occurrence : Occurrence
  context : Context
  donors : List Donor
  alternatives : List Alternative
  deriving DecidableEq, Repr

/-- The dependent certificate has actual proof obligations, not an author name
constructor. Its interpretation and collector premises are explicit in input. -/
structure LexicalCertificate (input : Input) (alternative : Alternative) : Prop where
  member : alternative ∈ input.alternatives
  occurrence : ExactOccurrence input.target input.occurrence
  supported : alternative.Supported input.donors input.occurrence

def compatibility (alternative : Alternative) (entity : Entity) : Compatibility :=
  match alternative.profile with
  | none => .possible
  | some profile => DiscourseEvidence.combineCompatibility
      (if profile.gender = 2 then .confirmed else
        DiscourseEvidence.featureCompatibility (some profile.gender) entity.gender)
      (DiscourseEvidence.featureCompatibility (some profile.number) entity.number)

def selectedByContext (context : Context) (surface : String)
    (origin : ReferenceOrigin) (entity : Entity) : Bool :=
  match origin with
  | .speaker => context.speaker == some entity.id
  | .addressee => context.addressee == some entity.id
  | .deictic => context.deixis.any (fun d => d.form == surface && d.entityIds.contains entity.id)
  | _ => false

def candidates (input : Input) (alternative : Alternative) : List Entity :=
  match alternative.origin with
  | none => []
  | some origin => DiscourseEvidence.filterCandidates
      (input.context.entities.filter (selectedByContext input.context input.occurrence.surface origin))
      [compatibility alternative]

inductive Status where
  | resolved | ambiguous | noCandidate | openScope | unsupportedReading
  | noLexicalReading | outOfScope | resourceLimit | unresolvedFeatures
  deriving DecidableEq, Repr

def Status.label : Status → String
  | .resolved => "RESOLVED" | .ambiguous => "AMBIGUOUS"
  | .noCandidate => "NO_CANDIDATE" | .openScope => "OPEN_SCOPE"
  | .unsupportedReading => "UNSUPPORTED_READING" | .noLexicalReading => "NO_LEXICAL_READING"
  | .outOfScope => "OUT_OF_SCOPE" | .resourceLimit => "RESOURCE_LIMIT"
  | .unresolvedFeatures => "UNRESOLVED_FEATURES"

def Status.ofSelection : SelectionStatus → Status
  | .resolved => .resolved | .ambiguous => .ambiguous | .noCandidate => .noCandidate
  | .openScope => .openScope | .unresolvedFeatures => .unresolvedFeatures

structure ReadingResult where
  id : String
  status : Status
  candidateEntityIds : List String
  boundEntityId : Option String
  deriving DecidableEq, Repr

def readingResult (input : Input) (alternative : Alternative) : ReadingResult :=
  if alternative.Supported input.donors input.occurrence then
    let selected := candidates input alternative
    let ids := selected.map Entity.id
    let allConfirmed := selected.all (fun entity => compatibility alternative entity == .confirmed)
    let status := Status.ofSelection
      (DiscourseEvidence.selectionStatus ids.length input.context.closedReferenceScope allConfirmed)
    ⟨alternative.id, status, ids, if status = .resolved then ids.head? else none⟩
  else ⟨alternative.id, .unsupportedReading, [], none⟩

def readingResults (input : Input) : List ReadingResult :=
  input.alternatives.map (readingResult input)

structure Receipt where
  status : Status
  readingIds : List String
  candidateEntityIds : List String
  boundEntityId : Option String
  readingResults : List ReadingResult
  deriving DecidableEq, Repr

def emptyReceipt (status : Status) : Receipt := ⟨status, [], [], none, []⟩

def commonReference (rows : List ReadingResult) : Option String :=
  match rows with
  | [] => none
  | first :: _ => match first.boundEntityId with
    | none => none
    | some id => if rows.all (fun row => row.status == .resolved && row.boundEntityId == some id)
        then some id else none

def aggregateStatus (context : Context) (rows : List ReadingResult)
    (ids : List String) (agreed : Option String) : Status :=
  if rows.any (fun row => row.status == .unsupportedReading) then .unsupportedReading
  else if !context.closedReferenceScope then .openScope
  else if ids.isEmpty then .noCandidate
  else if rows.any (fun row => row.status == .unresolvedFeatures) then .unresolvedFeatures
  else if agreed.isSome then .resolved else .ambiguous

def receipt (input : Input) (budget : Nat) : Receipt :=
  if !initialScope input.target input.occurrence then emptyReceipt .outOfScope
  else if input.alternatives.length + input.context.entities.length > budget then emptyReceipt .resourceLimit
  else if input.alternatives.isEmpty then emptyReceipt .noLexicalReading
  else
    let rows := readingResults input
    let ids := (input.context.entities.filter (fun entity => rows.any
      (fun row => row.candidateEntityIds.contains entity.id))).map Entity.id
    let agreed := commonReference rows
    let status := aggregateStatus input.context rows ids agreed
    ⟨status, input.alternatives.map Alternative.id, ids,
      if status = .resolved then agreed else none, rows⟩

def checkReceipt (input : Input) (budget : Nat) (proposed : Receipt) : Bool :=
  decide (ExactOccurrence input.target input.occurrence ∧ proposed = receipt input budget)

theorem checked_keeps_exact_source (input : Input) (budget : Nat) (proposed : Receipt)
    (checked : checkReceipt input budget proposed = true) :
    Attested [input.target.source] (input.occurrence.passage input.target) := by
  have checked := of_decide_eq_true checked
  exact checked.1.1

theorem checked_receipt_exact (input : Input) (budget : Nat) (proposed : Receipt) :
    checkReceipt input budget proposed = true ↔
      ExactOccurrence input.target input.occurrence ∧ proposed = receipt input budget := by
  simp [checkReceipt]

theorem every_lexical_alternative_retained (input : Input) (alternative : Alternative)
    (member : alternative ∈ input.alternatives) :
    readingResult input alternative ∈ readingResults input :=
  List.mem_map.mpr ⟨alternative, member, rfl⟩

theorem no_invented_reading_result (input : Input) (row : ReadingResult)
    (member : row ∈ readingResults input) :
    ∃ alternative ∈ input.alternatives, readingResult input alternative = row :=
  List.mem_map.mp member

theorem candidate_requires_context_and_compatibility (input : Input) (alternative : Alternative)
    (entity : Entity) (member : entity ∈ candidates input alternative) :
    entity ∈ input.context.entities ∧ compatibility alternative entity ≠ .conflict := by
  unfold candidates at member
  split at member
  · simp at member
  · have kept := (DiscourseEvidence.candidate_filter_exact _ _ entity).mp member
    exact ⟨(List.mem_filter.mp kept.1).1, kept.2 _ (by simp)⟩

theorem no_reference_from_empty_lexical_ledger (input : Input) (budget : Nat)
    (empty : input.alternatives = []) : (receipt input budget).boundEntityId = none := by
  simp only [receipt, empty, List.length_nil, Nat.zero_add, List.isEmpty_nil, ite_true]
  split <;> simp only [emptyReceipt]
  split <;> rfl

theorem initial_scope_required (input : Input) (budget : Nat)
    (outside : initialScope input.target input.occurrence = false) :
    receipt input budget = emptyReceipt .outOfScope := by simp [receipt, outside]

theorem common_reference_requires_every_alternative (rows : List ReadingResult) (id : String)
    (common : commonReference rows = some id) :
    rows ≠ [] ∧ ∀ row ∈ rows, row.status = .resolved ∧ row.boundEntityId = some id := by
  cases rows with
  | nil => simp [commonReference] at common
  | cons first rest =>
    constructor
    · simp
    · cases bound : first.boundEntityId with
      | none => simp [commonReference, bound] at common
      | some value =>
        simp only [commonReference, bound] at common
        split at common
        · rename_i all
          have same : value = id := Option.some.inj common
          subst value
          intro row member
          simpa using List.all_eq_true.mp all row member
        · contradiction

/-- Resolution uses existing discourse laws: complete scope, one survivor,
and positive confirmation of every required feature. -/
theorem resolved_reading_requires_closed_confirmed_singleton
    (input : Input) (alternative : Alternative)
    (resolved : (readingResult input alternative).status = .resolved) :
    alternative.Supported input.donors input.occurrence ∧
    input.context.closedReferenceScope = true ∧
    (candidates input alternative).length = 1 ∧
    ∀ entity ∈ candidates input alternative, compatibility alternative entity = .confirmed := by
  by_cases supported : alternative.Supported input.donors input.occurrence
  · simp only [readingResult, supported, ↓reduceIte] at resolved
    have raw : DiscourseEvidence.selectionStatus
        ((candidates input alternative).map Entity.id).length input.context.closedReferenceScope
        ((candidates input alternative).all (fun entity => compatibility alternative entity == .confirmed)) = .resolved := by
      generalize DiscourseEvidence.selectionStatus
        ((candidates input alternative).map Entity.id).length input.context.closedReferenceScope
        ((candidates input alternative).all (fun entity => compatibility alternative entity == .confirmed)) = status at resolved ⊢
      cases status <;> simp_all [Status.ofSelection]
    have exact := DiscourseEvidence.resolved_exact _ _ _ |>.mp raw
    refine ⟨supported, exact.1, ?_, ?_⟩
    · simpa using exact.2.1
    · intro entity member
      simpa using List.all_eq_true.mp exact.2.2 entity member
  · simp [readingResult, supported] at resolved

theorem resolved_reading_has_dependent_lexical_certificate
    (input : Input) (alternative : Alternative)
    (exactSource : ExactOccurrence input.target input.occurrence)
    (member : alternative ∈ input.alternatives)
    (resolved : (readingResult input alternative).status = .resolved) :
    LexicalCertificate input alternative :=
  ⟨member, exactSource, (resolved_reading_requires_closed_confirmed_singleton input alternative resolved).1⟩

/-- A checked rejection or resource receipt remains a scoped negative result;
it never returns an entity merely because a supplied list was truncated. -/
theorem insufficient_budget_has_no_reference (input : Input) (budget : Nat)
    (insufficient : budget < input.alternatives.length + input.context.entities.length) :
    (receipt input budget).boundEntityId = none := by
  simp only [receipt]
  split
  · rfl
  · simp [emptyReceipt]

/-- Source annotation, spelling and all referenced donor intervals remain
actual dependent obligations rather than author-name labels. -/
theorem lexical_certificate_keeps_all_donor_obligations
    (input : Input) (alternative : Alternative) (certificate : LexicalCertificate input alternative) :
    alternative.donorIds ≠ [] ∧
    ∀ id ∈ alternative.donorIds, ∃ donor ∈ input.donors,
      donor.id = id ∧ donor.Valid input.donors ∧ donor.annotationMatches alternative = true :=
  ⟨certificate.supported.2.2.1, certificate.supported.2.2.2.2⟩

/-- A returned reference is consensus across the complete supplied lexical
ledger, not merely the first successful lexical reading. -/
theorem returned_reference_requires_every_reading (input : Input) (budget : Nat)
    (id : String) (returned : (receipt input budget).boundEntityId = some id) :
    readingResults input ≠ [] ∧ ∀ row ∈ readingResults input,
      row.status = .resolved ∧ row.boundEntityId = some id := by
  have common : commonReference (readingResults input) = some id := by
    unfold receipt at returned
    split at returned
    · cases returned
    · split at returned
      · cases returned
      · split at returned
        · cases returned
        · simp only at returned
          split at returned
          · exact returned
          · cases returned
  exact common_reference_requires_every_alternative _ _ common

end Nabt.ContextualReference
