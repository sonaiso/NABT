import Nabt.Foundation
import Nabt.QatrReading
import Nabt.RecursiveLicensedAlgebra

/-!
# A source-acquired, bounded common-letter six-noun reading

This is an authored fragment, not a parser for all Arabic. It acquires the
governor, exact noun spelling, ending, complement and byte interval from the
source itself. No caller supplies a case, class, licensing flag or proof.
The source interpretation is the common-letter account already declared by
InflectionEvidence. The finite lexical/profile selection is not a theorem
that every homograph has this analysis in every context.

The original Foundation projection remains unchanged, including PARTIAL.
A second explicitly named orthographic profile maps only exact installed
spellings into canonical A116 carrier/mark pairs. It retains the original
spelling and its source interval. It is not a general normalization rule or
a proof of recorded pronunciation. The table expands hamza seats, declared
long vowels and the two installed complements' tanwin; it never guesses a
missing mark in an arbitrary input.

The acquired witness constructs RecursiveLicensedAlgebra.Certified for the
actual case/form grammar below. It is not a general RecursiveSourceBridge
CertifiedBridge, intended-sense certificate, real-world fact or all-Arabic
acceptance. The source-interpretation and authenticity obligations remain.
-/
namespace Nabt.SixNounAcquisition

open RecursiveLicensedAlgebra

def lawId : String := "nabt.six-noun-acquisition.v1"
def orthographicProfile : String := "nabt.six-noun-exact-spelling.v1"

inductive Governor where
  | arrival | seeing | passing
  deriving DecidableEq, BEq, Repr
inductive Lexeme where
  | ab | akh | ham | fu | dhu | han
  deriving DecidableEq, BEq, Repr
inductive Ending where
  | waw | alif | ya
  deriving DecidableEq, BEq, Repr
inductive Complement where
  | zayd | amr
  deriving DecidableEq, BEq, Repr

def Governor.label : Governor → String
  | .arrival => "arrival" | .seeing => "seeing" | .passing => "passing"
def Lexeme.label : Lexeme → String
  | .ab => "ab" | .akh => "akh" | .ham => "ham" | .fu => "fu"
  | .dhu => "dhu" | .han => "han"
def Ending.label : Ending → String
  | .waw => "waw" | .alif => "alif" | .ya => "ya"
def Complement.label : Complement → String
  | .zayd => "zayd" | .amr => "amr"

def Governor.prefix : Governor → String
  | .arrival => "جَاءَ " | .seeing => "رَأَيْتُ " | .passing => "مَرَرْتُ بِ"
def Governor.canonicalPrefix : Governor → String
  | .arrival => "جَاْءَ " | .seeing => "رَءَيْتُ " | .passing => "مَرَرْتُ بِ"
def Governor.expected : Governor → Ending
  | .arrival => .waw | .seeing => .alif | .passing => .ya
def Ending.grammaticalCase : Ending → Governors.Case
  | .waw => .raf | .alif => .nasb | .ya => .jarr
def Ending.caseLabel : Ending → String
  | .waw => "raf" | .alif => "nasb" | .ya => "jarr"
def Ending.caseCode : Ending → Nat
  | .waw => 1 | .alif => 0 | .ya => 2
def Ending.sign : Ending → InflectionEvidence.Sign
  | .waw => .waw | .alif => .alif | .ya => .ya

def word (lexeme : Lexeme) (ending : Ending) : String :=
  match lexeme, ending with
  | .ab, .waw => "أَبُو" | .ab, .alif => "أَبَا" | .ab, .ya => "أَبِي"
  | .akh, .waw => "أَخُو" | .akh, .alif => "أَخَا" | .akh, .ya => "أَخِي"
  | .ham, .waw => "حَمُو" | .ham, .alif => "حَمَا" | .ham, .ya => "حَمِي"
  | .fu, .waw => "فُو" | .fu, .alif => "فَا" | .fu, .ya => "فِي"
  | .dhu, .waw => "ذُو" | .dhu, .alif => "ذَا" | .dhu, .ya => "ذِي"
  | .han, .waw => "هَنُو" | .han, .alif => "هَنَا" | .han, .ya => "هَنِي"

def canonicalWord (lexeme : Lexeme) (ending : Ending) : String :=
  match lexeme, ending with
  | .ab, .waw => "ءَبُوْ" | .ab, .alif => "ءَبَاْ" | .ab, .ya => "ءَبِيْ"
  | .akh, .waw => "ءَخُوْ" | .akh, .alif => "ءَخَاْ" | .akh, .ya => "ءَخِيْ"
  | .ham, .waw => "حَمُوْ" | .ham, .alif => "حَمَاْ" | .ham, .ya => "حَمِيْ"
  | .fu, .waw => "فُوْ" | .fu, .alif => "فَاْ" | .fu, .ya => "فِيْ"
  | .dhu, .waw => "ذُوْ" | .dhu, .alif => "ذَاْ" | .dhu, .ya => "ذِيْ"
  | .han, .waw => "هَنُوْ" | .han, .alif => "هَنَاْ" | .han, .ya => "هَنِيْ"

def Complement.text : Complement → String
  | .zayd => "زَيْدٍ" | .amr => "عَمْرٍو"
def Complement.canonical : Complement → String
  | .zayd => "زَيْدِنْ" | .amr => "عَمْرِنْ"

structure Reading where
  governor : Governor
  lexeme : Lexeme
  ending : Ending
  complement : Complement
  deriving DecidableEq, BEq, Repr

def Reading.word (r : Reading) : String := word r.lexeme r.ending
def Reading.render (r : Reading) : String :=
  r.governor.prefix ++ r.word ++ " " ++ r.complement.text
def Reading.canonical (r : Reading) : String :=
  r.governor.canonicalPrefix ++ canonicalWord r.lexeme r.ending ++ " " ++ r.complement.canonical
def Reading.startByte (r : Reading) : Nat := r.governor.prefix.utf8ByteSize
def Reading.endByte (r : Reading) : Nat := r.startByte + r.word.utf8ByteSize

def canonicalSource (r : Reading) : Foundation.Source :=
  ⟨orthographicProfile, lawId, r.canonical⟩
def Reading.projection (r : Reading) : Foundation.Receipt := Foundation.project (canonicalSource r)

def allReadings : List Reading :=
  ([.arrival, .seeing, .passing] : List Governor).flatMap fun g =>
    ([.ab, .akh, .ham, .fu, .dhu, .han] : List Lexeme).flatMap fun l =>
      ([.waw, .alif, .ya] : List Ending).flatMap fun e =>
        ([.zayd, .amr] : List Complement).map fun c => ⟨g, l, e, c⟩

theorem all_readings_count : allReadings.length = 108 := by decide

def Reading.Exact (source : Foundation.Source) (r : Reading) : Prop :=
  source.text = r.render ∧
  (source.text.toUTF8.data.toList.drop r.startByte).take (r.endByte - r.startByte) =
    r.word.toUTF8.data.toList ∧
  r.startByte < r.endByte ∧ r.endByte ≤ source.text.utf8ByteSize ∧
  (Foundation.project source).status ≠ .invalid

instance (source : Foundation.Source) (r : Reading) : Decidable (r.Exact source) := by
  unfold Reading.Exact
  infer_instance

def readings (source : Foundation.Source) : List Reading :=
  allReadings.filter fun r => decide (r.Exact source)

def acquire (source : Foundation.Source) : Option Reading := (readings source).head?

theorem readings_exact (source : Foundation.Source) (r : Reading) :
    r ∈ readings source ↔ r ∈ allReadings ∧ r.Exact source := by
  simp [readings]

theorem acquired_exact (source : Foundation.Source) (r : Reading)
    (h : acquire source = some r) : r.Exact source := by
  have member : r ∈ readings source := List.mem_of_head? h
  exact ((readings_exact source r).mp member).2

theorem acquired_source_restored (source : Foundation.Source) (r : Reading)
    (h : acquire source = some r) : r.render = source.text :=
  (acquired_exact source r h).1.symm

theorem acquired_exact_word_bytes (source : Foundation.Source) (r : Reading)
    (h : acquire source = some r) :
    (source.text.toUTF8.data.toList.drop r.startByte).take (r.endByte - r.startByte) =
      r.word.toUTF8.data.toList := (acquired_exact source r h).2.1

theorem acquired_byte_bounds (source : Foundation.Source) (r : Reading)
    (h : acquire source = some r) :
    r.startByte < r.endByte ∧ r.endByte ≤ source.text.utf8ByteSize :=
  ⟨(acquired_exact source r h).2.2.1, (acquired_exact source r h).2.2.2.1⟩

theorem canonical_number_restores_cells (r : Reading) :
    Sequence.decode r.projection.number = r.projection.cells :=
  Foundation.number_restores_cells _

/-- The spelling alone never supplies companionship evidence. -/
def companionship (_r : Reading) : Morphology.Evidence := .unknown

def Reading.Supported (r : Reading) : Prop :=
  r.lexeme ≠ .dhu ∧ r.ending = r.governor.expected ∧
  r.projection.status = .complete

instance (r : Reading) : Decidable r.Supported := by
  unfold Reading.Supported
  infer_instance

theorem supported_case_sign (r : Reading) (h : r.Supported) :
    InflectionEvidence.signFor .iSitta r.governor.expected.grammaticalCase = r.ending.sign := by
  have same := h.2.1
  rw [same]
  cases r.governor <;> rfl

theorem dhu_has_no_supported_reading (r : Reading) (h : r.lexeme = .dhu) : ¬ r.Supported := by
  intro supported
  exact supported.1 h

/-- Concrete interfaces carry the observed and required case separately. -/
def prefixFace : Face := ⟨.verbPhrase, 0, 0, []⟩
def nounFace (r : Reading) : Face := ⟨.noun, r.ending.caseCode, 1, []⟩
def complementFace : Face := ⟨.noun, 2, 2, []⟩
def phraseFace (r : Reading) : Face := ⟨.nounPhrase, r.ending.caseCode, 1, []⟩
def sentenceFace (r : Reading) : Face := ⟨.verbalClause, r.governor.expected.caseCode, 0, []⟩

def projected (text : String) : List Nat :=
  (Foundation.project ⟨orthographicProfile, lawId, text⟩).cells.map Fin.val

def nounTree : Tree := .binary 1 (.leaf (.lexical 1)) (.leaf (.lexical 2))
def sentenceTree : Tree := .binary 0 (.leaf (.lexical 0)) nounTree

/-- The grammar is fixed by the acquired reading. Neither the caller nor an
unrelated small integer chooses the gate or its lexical realization. -/
def grammar (r : Reading) : Grammar where
  root3Allowed _ _ _ := False
  root4Allowed _ _ _ _ := False
  lexicalAllowed entry := entry < 3
  lexicalFace entry := if entry = 0 then prefixFace else if entry = 1 then nounFace r else complementFace
  lexicalSurface entry := if entry = 0 then projected r.governor.canonicalPrefix
    else if entry = 1 then projected (canonicalWord r.lexeme r.ending)
    else projected r.complement.canonical
  unaryRule _ := ⟨prefixFace, prefixFace, id, fun _ => False⟩
  binaryRule index := if index = 1 then
    ⟨nounFace r, complementFace, phraseFace r, List.append,
      fun left right => left = .leaf (.lexical 1) ∧ right = .leaf (.lexical 2)⟩
    else if index = 0 then
    ⟨prefixFace, phraseFace r, sentenceFace r, List.append,
      fun left right => left = .leaf (.lexical 0) ∧ right = nounTree ∧ r.Supported⟩
    else ⟨prefixFace, prefixFace, prefixFace, List.append, fun _ _ => False⟩

set_option maxRecDepth 10000 in
set_option maxHeartbeats 4000000 in
/-- All 108 explicitly declared spelling transformations yield complete
canonical carrier/mark pairs. This says nothing about arbitrary spellings. -/
theorem installed_canonical_projection_complete (r : Reading) :
    r.projection.status = .complete := by
  rcases r with ⟨g, l, e, c⟩
  cases g <;> cases l <;> cases e <;> cases c <;> decide +kernel

set_option maxRecDepth 10000 in
set_option maxHeartbeats 4000000 in
/-- The grammatical derivation realizes exactly the A116 sequence obtained
from the same acquired reading's named orthographic transformation. Merely
carrying an independent projection beside a grammar certificate would not
establish this equality. -/
theorem grammar_surface_matches_projection (r : Reading) :
    sentenceTree.surface (grammar r) = r.projection.cells.map Fin.val := by
  rcases r with ⟨g, l, e, c⟩
  cases g <;> cases l <;> cases e <;> cases c <;> decide +kernel

theorem grammar_certified (r : Reading) (h : r.Supported) : Certified (grammar r) sentenceTree := by
  apply Certified.binary
  · exact Certified.leaf (.lexical 0) (by decide)
  · apply Certified.binary
    · exact Certified.leaf (.lexical 1) (by decide)
    · exact Certified.leaf (.lexical 2) (by decide)
    · rfl
    · rfl
    · exact ⟨rfl, rfl⟩
  · rfl
  · rfl
  · exact ⟨rfl, rfl, h⟩

theorem grammar_certificate_requires_support (r : Reading)
    (h : Certified (grammar r) sentenceTree) : r.Supported := by
  have conditions := (certified_iff_all_node_conditions (grammar r) sentenceTree).mp h
  exact conditions.2.2.2.2.2.2

theorem grammar_certified_iff_supported (r : Reading) :
    Certified (grammar r) sentenceTree ↔ r.Supported :=
  ⟨grammar_certificate_requires_support r, grammar_certified r⟩

/-- Failure of the selected convention does not reject every Arabic reading. -/
theorem case_mismatch_blocks_selected_grammar (r : Reading)
    (mismatch : r.ending ≠ r.governor.expected) :
    ¬ Certified (grammar r) sentenceTree := by
  intro certificate
  exact mismatch (grammar_certificate_requires_support r certificate).2.1

/-- The unknown semantic premise cannot be manufactured by a surface match. -/
theorem unknown_companionship_blocks_grammar (r : Reading) (dhu : r.lexeme = .dhu) :
    ¬ Certified (grammar r) sentenceTree := by
  intro certificate
  exact dhu_has_no_supported_reading r dhu
    (grammar_certificate_requires_support r certificate)

structure Certificate (source : Foundation.Source) (context : String) where
  reading : Reading
  acquired : acquire source = some reading
  supported : reading.Supported
  licensed : Certified (grammar reading) sentenceTree

def certify (source : Foundation.Source) (context : String) : Option (Certificate source context) :=
  match h : acquire source with
  | none => none
  | some r => if supported : r.Supported then
      some ⟨r, h, supported, grammar_certified r supported⟩ else none

theorem certificate_preserves_source (source : Foundation.Source) (context : String)
    (cert : Certificate source context) : cert.reading.render = source.text :=
  acquired_source_restored source cert.reading cert.acquired

theorem certificate_all_nodes_licensed (source : Foundation.Source) (context : String)
    (cert : Certificate source context) : AllNodeConditions (grammar cert.reading) sentenceTree :=
  (certified_iff_all_node_conditions _ _).mp cert.licensed

theorem certificate_case_sign (source : Foundation.Source) (context : String)
    (cert : Certificate source context) :
    InflectionEvidence.signFor .iSitta cert.reading.governor.expected.grammaticalCase =
      cert.reading.ending.sign := supported_case_sign cert.reading cert.supported

theorem certificate_realization_matches_projection (source : Foundation.Source) (context : String)
    (cert : Certificate source context) :
    sentenceTree.surface (grammar cert.reading) = cert.reading.projection.cells.map Fin.val :=
  grammar_surface_matches_projection cert.reading

theorem certificate_numeric_realization (source : Foundation.Source) (context : String)
    (cert : Certificate source context) :
    (Sequence.decode cert.reading.projection.number).map Fin.val =
      sentenceTree.surface (grammar cert.reading) := by
  rw [canonical_number_restores_cells, certificate_realization_matches_projection source context cert]

def alternatives (r : Reading) : List String :=
  match r.lexeme with
  | .ab | .akh | .ham => ["QASR_AND_NAQS_NOT_ENUMERATED_BY_THIS_PROFILE"]
  | .han => ["NAQS_PREFERRED_FULL_FORM_READING_ONLY"]
  | .dhu => ["COMPANIONSHIP_OR_RELATIVE_READING_UNRESOLVED"]
  | .fu => []

def unresolved (r : Reading) : List String :=
  ["SOURCE_AUTHENTICITY_NOT_PROVED", "RULE_INTERPRETATION_NOT_PROVED",
   "LEXICAL_PROFILE_NOT_GENERAL_CLASSIFICATION", "READING_EXHAUSTIVENESS_OUTSIDE_PROFILE_NOT_PROVED",
   "INTENDED_REFERENCE_NOT_ESTABLISHED", "EXTERNAL_TRUTH_NOT_ESTABLISHED"] ++
  (if r.lexeme = .dhu then ["DHU_COMPANIONSHIP_NOT_ACQUIRED"] else []) ++
  (if r.ending ≠ r.governor.expected then ["COMMON_LETTER_CASE_MISMATCH"] else []) ++
  (if r.projection.status ≠ .complete then ["DECLARED_ORTHOGRAPHIC_PROFILE_INCOMPLETE"] else [])

end Nabt.SixNounAcquisition
