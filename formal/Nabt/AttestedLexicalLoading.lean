import Nabt.ClassicalLanguageEvidence
import Nabt.LexicalDenotation

/-!
# A source-paired lexical loading contract

The installed Python loader aligns an explicit dictionary headword with a
separately annotated morphological occurrence. This module specifies that
join. Both source passages and both interpretation ledgers are supplied
premises. In particular, a root-only dictionary entry has no headword key and
cannot license an arbitrary derivative merely by sharing its root.

`lemmaKey` is a supplied, already qualified comparison key. Unicode handling,
vocalization, shadda preservation, headword extraction, source authenticity,
SHA-256 validation and refinement of the Python loader are NOT proved here.
The full definition and annotation identities survive the join. Alignment is
not a claim that a corpus occurrence bears the dictionary sense, nor that an
external individual instantiates the definition. Existing
`LexicalDenotation.definition_does_not_assert_world` remains the world boundary.

The theorem `load_exact` proves catalogue-relative enumeration for this candidate join;
it does not prove completeness of the source catalogues or Arabic.
-/

namespace Nabt.AttestedLexicalLoading

open ClassicalLanguageEvidence (Source Passage Attested)

def lawId : String := "nabt.attested-lexical-loading.v1"

/-- A headword interpretation remains separate from the quoted definition.
`none` means that only a root, not an exact headword, has been licensed. -/
structure Headword where
  sense : LexicalDenotation.Sense
  lemmaKey : Option String
  passage : Passage
  deriving DecidableEq, Repr

/-- This ledger is interpreted from a morphological source. Features remain
the source's annotations; absent features are not assigned default values. -/
structure Annotation where
  identity : String
  root : String
  lemmaKey : String
  surface : String
  features : List (String × String)
  passage : Passage
  deriving DecidableEq, Repr

structure Alignment where
  headword : Headword
  annotation : Annotation
  deriving DecidableEq, Repr

/-- The interpreted definition must name this exact quotation interval and
revision. The SHA label remains metadata, not a proved hash computation. -/
def CitationBound (h : Headword) : Prop :=
  h.sense.citation.work = h.passage.source.sourceId ∧
  h.sense.citation.revision = h.passage.source.revision ∧
  h.sense.citation.startByte = h.passage.offset ∧
  h.sense.citation.endByte = h.passage.offset + h.passage.quote.length ∧
  h.sense.citation.quotation.toUTF8.toList = h.passage.quote

instance (h : Headword) : Decidable (CitationBound h) := by
  unfold CitationBound
  infer_instance

/-- A compatible key is necessary, but by itself supplies no source evidence. -/
def Compatible (h : Headword) (a : Annotation) : Prop :=
  h.lemmaKey = some a.lemmaKey ∧ h.sense.root = a.root ∧ a.lemmaKey ≠ ""

instance (h : Headword) (a : Annotation) : Decidable (Compatible h a) := by
  unfold Compatible
  infer_instance

/-- Admission of a CANDIDATE pair retains independent dictionary and
morphology witnesses. It is not a contextual sense license. -/
def Admitted (sources : List Source) (headwords : List Headword)
    (annotations : List Annotation) (row : Alignment) : Prop :=
  row.headword ∈ headwords ∧ row.annotation ∈ annotations ∧
  (Attested sources row.headword.passage ∧ CitationBound row.headword) ∧
  Attested sources row.annotation.passage ∧
  Compatible row.headword row.annotation

instance (sources : List Source) (headwords : List Headword)
    (annotations : List Annotation) (row : Alignment) :
    Decidable (Admitted sources headwords annotations row) := by
  unfold Admitted
  infer_instance

def accepts (sources : List Source) (headwords : List Headword)
    (annotations : List Annotation) (row : Alignment) : Bool :=
  decide (Admitted sources headwords annotations row)

/-- Enumerate the complete supplied cross-product, then retain qualified
alignments. No first-match branch selects one definition over another. -/
def load (sources : List Source) (headwords : List Headword)
    (annotations : List Annotation) : List Alignment :=
  (headwords.flatMap fun h => annotations.map fun a => ⟨h, a⟩).filter
    (accepts sources headwords annotations)

theorem load_exact (sources : List Source) (headwords : List Headword)
    (annotations : List Annotation) (row : Alignment) :
    row ∈ load sources headwords annotations ↔ Admitted sources headwords annotations row := by
  constructor
  · intro member
    have accepted := (List.mem_filter.mp member).2
    exact of_decide_eq_true accepted
  · intro admitted
    apply List.mem_filter.mpr
    constructor
    · apply List.mem_flatMap.mpr
      refine ⟨row.headword, admitted.1, ?_⟩
      apply List.mem_map.mpr
      exact ⟨row.annotation, admitted.2.1, rfl⟩
    · exact decide_eq_true admitted

theorem admitted_keeps_both_ledgers (sources : List Source)
    (headwords : List Headword) (annotations : List Annotation) (row : Alignment)
    (member : row ∈ load sources headwords annotations) :
    row.headword ∈ headwords ∧ row.annotation ∈ annotations := by
  have h := (load_exact sources headwords annotations row).mp member
  exact ⟨h.1, h.2.1⟩

theorem admitted_keeps_both_passages (sources : List Source)
    (headwords : List Headword) (annotations : List Annotation) (row : Alignment)
    (member : row ∈ load sources headwords annotations) :
    Attested sources row.headword.passage ∧ Attested sources row.annotation.passage := by
  have h := (load_exact sources headwords annotations row).mp member
  exact ⟨h.2.2.1.1, h.2.2.2.1⟩

theorem admitted_definition_citation_bound (sources : List Source)
    (headwords : List Headword) (annotations : List Annotation) (row : Alignment)
    (member : row ∈ load sources headwords annotations) : CitationBound row.headword :=
  ((load_exact sources headwords annotations row).mp member).2.2.1.2

theorem root_only_is_not_a_headword_license (sources : List Source)
    (headwords : List Headword) (annotations : List Annotation) (row : Alignment)
    (rootOnly : row.headword.lemmaKey = none) :
    row ∉ load sources headwords annotations := by
  intro member
  have compatible := ((load_exact sources headwords annotations row).mp member).2.2.2.2
  simp [Compatible, rootOnly] at compatible

theorem missing_morphology_blocks (sources : List Source)
    (headwords : List Headword) (annotations : List Annotation) (row : Alignment)
    (missing : row.annotation ∉ annotations) :
    row ∉ load sources headwords annotations := by
  intro member
  exact missing (admitted_keeps_both_ledgers sources headwords annotations row member).2

/-- Distinct dictionary senses aligned to one morphological occurrence are
kept as distinct rows. This is preservation, not sense disambiguation. -/
theorem shared_lemma_preserves_distinct_senses (sources : List Source)
    (headwords : List Headword) (annotations : List Annotation)
    (left right : Headword) (a : Annotation)
    (hleft : Admitted sources headwords annotations ⟨left, a⟩)
    (hright : Admitted sources headwords annotations ⟨right, a⟩)
    (different : left.sense ≠ right.sense) :
    Alignment.mk left a ∈ load sources headwords annotations ∧
    Alignment.mk right a ∈ load sources headwords annotations ∧
    Alignment.mk left a ≠ Alignment.mk right a := by
  refine ⟨(load_exact sources headwords annotations _).mpr hleft,
    (load_exact sources headwords annotations _).mpr hright, ?_⟩
  intro same
  exact different (congrArg (fun row : Alignment => row.headword.sense) same)

/-- Adding ledgers does not authorize replacing any old source bytes,
definition, annotation, or lemma binding. The old row itself survives. -/
theorem extension_preserves_full_alignment (sources extraSources : List Source)
    (headwords extraHeadwords : List Headword) (annotations extraAnnotations : List Annotation)
    (row : Alignment) (member : row ∈ load sources headwords annotations) :
    row ∈ load (sources ++ extraSources) (headwords ++ extraHeadwords)
      (annotations ++ extraAnnotations) := by
  have h := (load_exact sources headwords annotations row).mp member
  apply (load_exact _ _ _ row).mpr
  refine ⟨List.mem_append_left extraHeadwords h.1,
    List.mem_append_left extraAnnotations h.2.1, ?_, ?_, h.2.2.2.2⟩
  · exact ⟨⟨List.mem_append_left extraSources h.2.2.1.1.1, h.2.2.1.1.2⟩,
      h.2.2.1.2⟩
  · exact ⟨List.mem_append_left extraSources h.2.2.2.1.1, h.2.2.2.1.2⟩

/-- Full membership is checked after construction. Changing only features
cannot reuse a ledger whose annotation no longer matches. -/
theorem unlicensed_feature_change_rejected (sources : List Source)
    (headwords : List Headword) (annotations : List Annotation) (row : Alignment)
    (features : List (String × String))
    (unlicensed : {row.annotation with features := features} ∉ annotations) :
    {row with annotation := {row.annotation with features := features}} ∉
      load sources headwords annotations := by
  exact missing_morphology_blocks sources headwords annotations _ unlicensed

/-- A contextual sense selection requires a separate interpreted ledger.
The complete source/context/lexicon binding is reused from SourceSemantics.
The current Python source-loading matrix does NOT produce this license. -/
structure SenseLicense where
  alignment : Alignment
  binding : SourceSemantics.Binding
  deriving DecidableEq, Repr

def selectsSense (sources : List Source) (headwords : List Headword)
    (annotations : List Annotation) (licenses : List SenseLicense)
    (row : Alignment) (binding : SourceSemantics.Binding) : Bool :=
  accepts sources headwords annotations row && decide (SenseLicense.mk row binding ∈ licenses)

/-- Even an admitted dictionary/morphology pair supplies no contextual sense
selection when the separate interpreted sense ledger is empty. -/
theorem candidate_is_not_a_contextual_sense_license (sources : List Source)
    (headwords : List Headword) (annotations : List Annotation)
    (row : Alignment) (binding : SourceSemantics.Binding) :
    selectsSense sources headwords annotations [] row binding = false := by
  simp [selectsSense]

theorem selected_sense_keeps_contextual_license (sources : List Source)
    (headwords : List Headword) (annotations : List Annotation) (licenses : List SenseLicense)
    (row : Alignment) (binding : SourceSemantics.Binding)
    (selected : selectsSense sources headwords annotations licenses row binding = true) :
    row ∈ load sources headwords annotations ∧ SenseLicense.mk row binding ∈ licenses := by
  have checked := Bool.and_eq_true_iff.mp selected
  exact ⟨(load_exact sources headwords annotations row).mpr (of_decide_eq_true checked.1),
    of_decide_eq_true checked.2⟩

end Nabt.AttestedLexicalLoading
