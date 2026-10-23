import Nabt.Governors

/-!
# A witnessed single-word layer before syntactic composition

Native NABT contracts informed by MIT-licensed Saleh1967/Alghanem,
commit 9d8fa03a51f894416e0abaf3b6821c5ae6441dcd:
A116/Mufrad.lean, Qism.lean, QismKhanat.lean, QismAwamil.lean,
QismDaraja.lean, Hudud.lean and Boundary.lean under formal/a116/.
The predication capacities also follow SLGE/Category.lean at
Saleh1967/Mashru@e4c801ffe9171dadedcc3aae23051ea0953ae361 (MIT).
Copyright (c) 2026 Saleh1967. See the retained MIT notice in NOTICE.md.

The traits and declension classes below must already be supported by a
source-bound reading. A Boolean trait, class code or numerical occurrence ID
does not itself prove its linguistic interpretation. This module proves the
algebra of supplied constraints and the inverse of an explicitly declared
finite ending table, not completeness of Arabic morphology, a parser, the
authenticity of the source binding, or its Python implementation.

The ending table has the same 15 conditional classes as the cited Qism table.
Admission of a class must establish all relevant side conditions: for example
the licensed six-noun construction or the diptote form without the conditions
that license kasra. The class label alone cannot establish those conditions.
Built words and unresolved classes may have no declension class here.

NABT case numbers remain nasb=0, raf=1, jarr=2, jazm=3, independently of the
ordering in Alghanem. Kind is separate from syntactic Role. The preserved
Analysis retains source/span/segmentation/reading; a contextual application
adds an explicitly supplied witness without replacing that analysis.
-/

namespace Nabt.Words

open Governors (Case Role)

def lawId : String := "nabt.words.v1"

inductive Kind where
  | noun | verb | particle
  deriving DecidableEq, Repr

def Kind.code : Kind → Nat
  | .noun => 0 | .verb => 1 | .particle => 2

def Kind.ofCode : Nat → Option Kind
  | 0 => some .noun | 1 => some .verb | 2 => some .particle | _ => none

def Kind.label : Kind → String
  | .noun => "noun" | .verb => "verb" | .particle => "particle"

/-- Capacity for predication, not a claim that a particular occurrence
already fills either syntactic role. Pair order is subject, predicate. -/
def Kind.capacities : Kind → Bool × Bool
  | .noun => (true, true)
  | .verb => (false, true)
  | .particle => (false, false)

def Kind.ofCategory : Governors.Category → Kind
  | .noun => .noun | .verb => .verb

def kinds : List Kind := [.noun, .verb, .particle]

theorem kind_decode_code (kind : Kind) : Kind.ofCode kind.code = some kind := by
  cases kind <;> rfl

theorem kind_code_injective : Function.Injective Kind.code := by
  intro a b same
  have decoded := congrArg Kind.ofCode same
  simpa only [kind_decode_code, Option.some.injEq] using decoded

theorem mem_kinds (kind : Kind) : kind ∈ kinds := by cases kind <;> decide

theorem capacities_injective : Function.Injective Kind.capacities := by
  intro a b same
  cases a <;> cases b <;> simp_all [Kind.capacities]

theorem capacities_no_fourth (kind : Kind) : kind.capacities ≠ (true, false) := by
  cases kind <;> decide

theorem subject_capacity_requires_predicate (kind : Kind)
    (subject : kind.capacities.1 = true) : kind.capacities.2 = true := by
  cases kind <;> simp_all [Kind.capacities]

/-- Conditional lexical inputs, not a surface-feature extractor. In particular,
`needsReference` is not the semantic dependence of a particle. -/
structure LexicalTraits where
  independent : Bool
  timeInForm : Bool
  needsReference : Bool
  deriving DecidableEq, Repr

def kindOf (traits : LexicalTraits) : Kind :=
  if traits.independent then
    if traits.timeInForm then .verb else .noun
  else .particle

theorem reference_need_preserves_kind (traits : LexicalTraits) (needed : Bool) :
    kindOf {traits with needsReference := needed} = kindOf traits := rfl

theorem noun_from_witnessed_traits (traits : LexicalTraits)
    (independent : traits.independent = true) (timeless : traits.timeInForm = false) :
    kindOf traits = .noun := by simp [kindOf, independent, timeless]

theorem verb_from_witnessed_traits (traits : LexicalTraits)
    (independent : traits.independent = true) (timed : traits.timeInForm = true) :
    kindOf traits = .verb := by simp [kindOf, independent, timed]

theorem particle_from_witnessed_traits (traits : LexicalTraits)
    (dependent : traits.independent = false) : kindOf traits = .particle := by
  simp [kindOf, dependent]

/-- Every member of `cues` is the allowed set of an already activated,
source-licensed cue. No absence of a cue is negative evidence. -/
def kindCandidates (cues : List (List Kind)) : List Kind :=
  kinds.filter (fun kind => cues.all (fun allowed => allowed.contains kind))

theorem mem_kindCandidates (cues : List (List Kind)) (kind : Kind) :
    kind ∈ kindCandidates cues ↔ ∀ allowed ∈ cues, kind ∈ allowed := by
  simp [kindCandidates, List.mem_filter, List.all_eq_true, mem_kinds]

theorem kind_candidates_refine (old extra : List (List Kind)) (kind : Kind)
    (survives : kind ∈ kindCandidates (old ++ extra)) :
    kind ∈ kindCandidates old := by
  rw [mem_kindCandidates] at survives ⊢
  exact fun allowed member => survives allowed (List.mem_append_left _ member)

theorem no_cue_retains_all : kindCandidates [] = [.noun, .verb, .particle] := rfl

theorem no_cue_is_not_particle : kindCandidates [] ≠ [.particle] := by decide

/-- A shared surface is allowed to retain two different kind readings when
all actual cues permit both. The cues' linguistic correctness is a premise. -/
theorem shared_surface_keeps_alternatives (cues : List (List Kind)) (a b : Kind)
    (different : a ≠ b) (permits : ∀ allowed ∈ cues, a ∈ allowed ∧ b ∈ allowed) :
    a ∈ kindCandidates cues ∧ b ∈ kindCandidates cues ∧
      2 ≤ (kindCandidates cues).length := by
  have ha := (mem_kindCandidates cues a).mpr (fun allowed h => (permits allowed h).1)
  have hb := (mem_kindCandidates cues b).mpr (fun allowed h => (permits allowed h).2)
  refine ⟨ha, hb, ?_⟩
  generalize kindCandidates cues = candidates at ha hb ⊢
  match candidates with
  | [] => simp at ha
  | [first] =>
    have sameA : a = first := by simpa using ha
    have sameB : b = first := by simpa using hb
    exact False.elim (different (sameA.trans sameB.symm))
  | _ :: _ :: _ => simp

inductive DeclensionClass where
  | iSahih | iSitta | iMuthanna | iJamM | iJamF | iMamnu | iMaqsur | iManqus
  | fSahih | fKhamsaA | fKhamsaW | fKhamsaY | fMutalAlif | fMutalW | fMutalY
  deriving DecidableEq, Repr

def declensionClasses : List DeclensionClass :=
  [.iSahih, .iSitta, .iMuthanna, .iJamM, .iJamF, .iMamnu, .iMaqsur, .iManqus,
   .fSahih, .fKhamsaA, .fKhamsaW, .fKhamsaY, .fMutalAlif, .fMutalW, .fMutalY]

def DeclensionClass.code : DeclensionClass → Nat
  | .iSahih => 0 | .iSitta => 1 | .iMuthanna => 2 | .iJamM => 3
  | .iJamF => 4 | .iMamnu => 5 | .iMaqsur => 6 | .iManqus => 7
  | .fSahih => 8 | .fKhamsaA => 9 | .fKhamsaW => 10 | .fKhamsaY => 11
  | .fMutalAlif => 12 | .fMutalW => 13 | .fMutalY => 14

def DeclensionClass.ofCode : Nat → Option DeclensionClass
  | 0 => some .iSahih | 1 => some .iSitta | 2 => some .iMuthanna | 3 => some .iJamM
  | 4 => some .iJamF | 5 => some .iMamnu | 6 => some .iMaqsur | 7 => some .iManqus
  | 8 => some .fSahih | 9 => some .fKhamsaA | 10 => some .fKhamsaW | 11 => some .fKhamsaY
  | 12 => some .fMutalAlif | 13 => some .fMutalW | 14 => some .fMutalY | _ => none

def DeclensionClass.label : DeclensionClass → String
  | .iSahih => "iSahih" | .iSitta => "iSitta" | .iMuthanna => "iMuthanna"
  | .iJamM => "iJamM" | .iJamF => "iJamF" | .iMamnu => "iMamnu"
  | .iMaqsur => "iMaqsur" | .iManqus => "iManqus" | .fSahih => "fSahih"
  | .fKhamsaA => "fKhamsaA" | .fKhamsaW => "fKhamsaW" | .fKhamsaY => "fKhamsaY"
  | .fMutalAlif => "fMutalAlif" | .fMutalW => "fMutalW" | .fMutalY => "fMutalY"

def DeclensionClass.kind : DeclensionClass → Kind
  | .iSahih | .iSitta | .iMuthanna | .iJamM | .iJamF | .iMamnu | .iMaqsur | .iManqus => .noun
  | _ => .verb

theorem declension_decode_code (cls : DeclensionClass) :
    DeclensionClass.ofCode cls.code = some cls := by cases cls <;> rfl

theorem declension_code_injective : Function.Injective DeclensionClass.code := by
  intro a b same
  have decoded := congrArg DeclensionClass.ofCode same
  simpa only [declension_decode_code, Option.some.injEq] using decoded

theorem declension_codes_exact : declensionClasses.map DeclensionClass.code = List.range 15 := by
  decide

theorem declension_ne_particle (cls : DeclensionClass) : cls.kind ≠ .particle := by
  cases cls <;> decide

def classCaseNumberDomain : String := "nabt.words.class-case.v1"

/-- A pair identifier, not a cell, an observed ending, or a licensed use. -/
def classCaseNumber (cls : DeclensionClass) (case : Case) : Nat := 4 * cls.code + case.code

def decodeClassCase (number : Nat) : Option (DeclensionClass × Case) := do
  let cls ← DeclensionClass.ofCode (number / 4)
  let case ← Case.ofCode (number % 4)
  pure (cls, case)

theorem classCase_decode (cls : DeclensionClass) (case : Case) :
    decodeClassCase (classCaseNumber cls case) = some (cls, case) := by
  have bound : case.code < 4 := case.mark.isLt
  have quotient : (4 * cls.code + case.code) / 4 = cls.code := by omega
  have residue : (4 * cls.code + case.code) % 4 = case.code := by omega
  simp [decodeClassCase, classCaseNumber, quotient, residue,
    declension_decode_code, Governors.case_decode_code]

theorem classCase_injective {a b : DeclensionClass} {c d : Case}
    (same : classCaseNumber a c = classCaseNumber b d) : a = b ∧ c = d := by
  have decoded := congrArg decodeClassCase same
  simpa only [classCase_decode, Option.some.injEq, Prod.mk.injEq] using decoded

theorem classCase_bound (cls : DeclensionClass) (case : Case) :
    classCaseNumber cls case < 60 := by cases cls <;> cases case <;> decide

theorem unknown_classCase_rejected : decodeClassCase 60 = none := by decide

inductive Ending where
  | damma | fatha | kasra | sukun | waw | alif | ya | ani | ayni | una | ina
  deriving DecidableEq, Repr

def endings : List Ending :=
  [.damma, .fatha, .kasra, .sukun, .waw, .alif, .ya, .ani, .ayni, .una, .ina]

def Ending.code : Ending → Nat
  | .damma => 0 | .fatha => 1 | .kasra => 2 | .sukun => 3 | .waw => 4
  | .alif => 5 | .ya => 6 | .ani => 7 | .ayni => 8 | .una => 9 | .ina => 10

def Ending.ofCode : Nat → Option Ending
  | 0 => some .damma | 1 => some .fatha | 2 => some .kasra | 3 => some .sukun
  | 4 => some .waw | 5 => some .alif | 6 => some .ya | 7 => some .ani
  | 8 => some .ayni | 9 => some .una | 10 => some .ina | _ => none

def Ending.label : Ending → String
  | .damma => "damma" | .fatha => "fatha" | .kasra => "kasra" | .sukun => "sukun"
  | .waw => "waw" | .alif => "alif" | .ya => "ya" | .ani => "ani"
  | .ayni => "ayni" | .una => "una" | .ina => "ina"

theorem ending_decode_code (observed : Ending) : Ending.ofCode observed.code = some observed := by
  cases observed <;> rfl

theorem ending_code_injective : Function.Injective Ending.code := by
  intro a b same
  have decoded := congrArg Ending.ofCode same
  simpa only [ending_decode_code, Option.some.injEq] using decoded

theorem ending_codes_exact : endings.map Ending.code = List.range 11 := by decide

/-- Conditional realization table. This is not a classifier from a suffix. -/
def ending : DeclensionClass → Case → Option Ending
  | .iSahih, .raf => some .damma | .iSahih, .nasb => some .fatha | .iSahih, .jarr => some .kasra
  | .iSitta, .raf => some .waw | .iSitta, .nasb => some .alif | .iSitta, .jarr => some .ya
  | .iMuthanna, .raf => some .ani | .iMuthanna, .nasb | .iMuthanna, .jarr => some .ayni
  | .iJamM, .raf => some .una | .iJamM, .nasb | .iJamM, .jarr => some .ina
  | .iJamF, .raf => some .damma | .iJamF, .nasb | .iJamF, .jarr => some .kasra
  | .iMamnu, .raf => some .damma | .iMamnu, .nasb | .iMamnu, .jarr => some .fatha
  | .iMaqsur, .raf | .iMaqsur, .nasb | .iMaqsur, .jarr => some .alif
  | .iManqus, .raf | .iManqus, .jarr => some .ya | .iManqus, .nasb => some .fatha
  | .fSahih, .raf => some .damma | .fSahih, .nasb => some .fatha | .fSahih, .jazm => some .sukun
  | .fKhamsaA, .raf => some .ani | .fKhamsaA, .nasb | .fKhamsaA, .jazm => some .alif
  | .fKhamsaW, .raf => some .una | .fKhamsaW, .nasb | .fKhamsaW, .jazm => some .waw
  | .fKhamsaY, .raf => some .ina | .fKhamsaY, .nasb | .fKhamsaY, .jazm => some .ya
  | .fMutalAlif, .raf | .fMutalAlif, .nasb => some .alif | .fMutalAlif, .jazm => some .fatha
  | .fMutalW, .raf => some .waw | .fMutalW, .nasb => some .fatha | .fMutalW, .jazm => some .damma
  | .fMutalY, .raf => some .ya | .fMutalY, .nasb => some .fatha | .fMutalY, .jazm => some .kasra
  | _, _ => none

def allCases : List Case := [.nasb, .raf, .jarr, .jazm]

theorem mem_allCases (case : Case) : case ∈ allCases := by cases case <;> decide

def caseCandidates (cls : DeclensionClass) (observed : Ending) : List Case :=
  allCases.filter (fun case => decide (ending cls case = some observed))

/-- Exact inverse-image membership: both soundness and completeness are
relative to the declared table, not to unrestricted Arabic. -/
theorem mem_caseCandidates_iff (cls : DeclensionClass) (observed : Ending) (case : Case) :
    case ∈ caseCandidates cls observed ↔ ending cls case = some observed := by
  simp [caseCandidates, mem_allCases]

theorem inverse_reading_sound (cls : DeclensionClass) (observed : Ending) (case : Case)
    (accepted : case ∈ caseCandidates cls observed) : ending cls case = some observed :=
  (mem_caseCandidates_iff cls observed case).mp accepted

theorem inverse_reading_complete (cls : DeclensionClass) (observed : Ending) (case : Case)
    (realized : ending cls case = some observed) : case ∈ caseCandidates cls observed :=
  (mem_caseCandidates_iff cls observed case).mpr realized

def caseCandidatesFor (classes : List DeclensionClass) (observed : Ending) : List Case :=
  allCases.filter (fun case => classes.any (fun cls => decide (ending cls case = some observed)))

theorem mem_caseCandidatesFor_iff (classes : List DeclensionClass) (observed : Ending) (case : Case) :
    case ∈ caseCandidatesFor classes observed ↔
      ∃ cls ∈ classes, ending cls case = some observed := by
  simp [caseCandidatesFor, mem_allCases, List.any_eq_true]

/-- Retain the correlated reading, rather than independently projecting a
class set and case set and taking their Cartesian product afterwards. -/
def caseReadings (classes : List DeclensionClass) (observed : Ending) :
    List (DeclensionClass × Case) :=
  classes.flatMap (fun cls => (caseCandidates cls observed).map (fun case => (cls, case)))

theorem mem_caseReadings_iff (classes : List DeclensionClass) (observed : Ending)
    (cls : DeclensionClass) (case : Case) :
    (cls, case) ∈ caseReadings classes observed ↔
      cls ∈ classes ∧ ending cls case = some observed := by
  simp [caseReadings, List.mem_flatMap, List.mem_map, mem_caseCandidates_iff,
    Prod.mk.injEq]

theorem caseReadings_cannot_mix (classes : List DeclensionClass) (observed : Ending)
    (cls : DeclensionClass) (case : Case) (unrealized : ending cls case ≠ some observed) :
    (cls, case) ∉ caseReadings classes observed := by
  intro accepted
  exact unrealized ((mem_caseReadings_iff classes observed cls case).mp accepted).2

theorem no_cross_class_recombination :
    caseReadings [.iSahih, .iSitta] .fatha = [(.iSahih, .nasb)] ∧
    (.iSitta, .nasb) ∉ caseReadings [.iSahih, .iSitta] .fatha := by decide

/-- Better-supported class information may remove possibilities, never add
one. Withdrawal or replacement of evidence is a separate recomputation. -/
theorem class_refinement_monotone (narrow wide : List DeclensionClass) (observed : Ending)
    (refines : ∀ cls ∈ narrow, cls ∈ wide) (case : Case)
    (accepted : case ∈ caseCandidatesFor narrow observed) :
    case ∈ caseCandidatesFor wide observed := by
  obtain ⟨cls, member, realized⟩ := (mem_caseCandidatesFor_iff narrow observed case).mp accepted
  exact (mem_caseCandidatesFor_iff wide observed case).mpr ⟨cls, refines cls member, realized⟩

def readCase (cls : DeclensionClass) (observed : Ending) : Option Case :=
  match caseCandidates cls observed with
  | [case] => some case
  | _ => none

theorem readCase_iff (cls : DeclensionClass) (observed : Ending) (case : Case) :
    readCase cls observed = some case ↔ caseCandidates cls observed = [case] := by
  unfold readCase
  generalize caseCandidates cls observed = candidates
  match candidates with
  | [] => simp
  | first :: rest =>
    cases rest with
    | nil => simp
    | cons next tail => simp

theorem readCase_sound (cls : DeclensionClass) (observed : Ending) (case : Case)
    (read : readCase cls observed = some case) : ending cls case = some observed := by
  have singleton := (readCase_iff cls observed case).mp read
  exact inverse_reading_sound cls observed case (by rw [singleton]; simp)

theorem readCase_complete (cls : DeclensionClass) (observed : Ending) (case : Case)
    (unique : caseCandidates cls observed = [case]) : readCase cls observed = some case :=
  (readCase_iff cls observed case).mpr unique

theorem noun_has_no_jazm (cls : DeclensionClass) (noun : cls.kind = .noun) :
    ending cls .jazm = none := by
  cases cls <;> simp_all [DeclensionClass.kind, ending]

theorem verb_has_no_jarr (cls : DeclensionClass) (verb : cls.kind = .verb) :
    ending cls .jarr = none := by
  cases cls <;> simp_all [DeclensionClass.kind, ending]

theorem ambiguity_is_retained :
    caseCandidates .iJamF .kasra = [.nasb, .jarr] ∧
    caseCandidates .iMaqsur .alif = [.nasb, .raf, .jarr] ∧
    readCase .fMutalW .damma = some .jazm := by decide

/-- Source identity is an externally bound natural, not a hash proof.
Coordinates are original UTF-8 byte offsets, not character indices. -/
structure Occurrence where
  sourceId : Nat
  byteStart : Nat
  byteEnd : Nat
  deriving DecidableEq, Repr

def Occurrence.valid (occurrence : Occurrence) : Prop := occurrence.byteStart < occurrence.byteEnd

structure Analysis where
  occurrence : Occurrence
  segmentationId : Nat
  readingId : Nat
  kind : Kind
  declension : Option DeclensionClass
  deriving DecidableEq, Repr

def Analysis.WellFormed (analysis : Analysis) : Prop :=
  analysis.occurrence.valid ∧
    ∀ cls, analysis.declension = some cls → cls.kind = analysis.kind

/-- A concrete compatibility condition, distinct from the witness that an
operator actually governs this occurrence. The class is read from `analysis`,
never manufactured from `role`. The observed ending is also supplied evidence.
This relation does not prove a refinement of the Python reader. -/
def CaseCompatible (analysis : Analysis) (role : Role) (case : Case) (observed : Ending) : Prop :=
  analysis.WellFormed ∧
    ∃ cls, analysis.declension = some cls ∧
      cls.kind = Kind.ofCategory role.category ∧ ending cls case = some observed

theorem compatible_class_is_original (analysis : Analysis) (role : Role) (case : Case)
    (observed : Ending) (compatible : CaseCompatible analysis role case observed) :
    ∃ cls, analysis.declension = some cls ∧ cls.kind = analysis.kind ∧
      ending cls case = some observed := by
  obtain ⟨wellFormed, cls, declared, _, realized⟩ := compatible
  exact ⟨cls, declared, wellFormed.2 cls declared, realized⟩

theorem compatible_kind_matches_role (analysis : Analysis) (role : Role) (case : Case)
    (observed : Ending) (compatible : CaseCompatible analysis role case observed) :
    analysis.kind = Kind.ofCategory role.category := by
  obtain ⟨wellFormed, cls, declared, aligned, _⟩ := compatible
  exact (wellFormed.2 cls declared).symm.trans aligned

theorem role_cannot_supply_missing_kind (analysis : Analysis) (role : Role) (case : Case)
    (observed : Ending) (different : analysis.kind ≠ Kind.ofCategory role.category) :
    ¬ CaseCompatible analysis role case observed := by
  intro compatible
  exact different (compatible_kind_matches_role analysis role case observed compatible)

theorem verb_cannot_borrow_noun_role (analysis : Analysis) (role : Role) (case : Case)
    (observed : Ending) (verb : analysis.kind = .verb) (nounRole : role.category = .noun) :
    ¬ CaseCompatible analysis role case observed := by
  apply role_cannot_supply_missing_kind
  simp [verb, nounRole, Kind.ofCategory]

theorem missing_class_cannot_borrow_role (analysis : Analysis) (role : Role) (case : Case)
    (observed : Ending) (missing : analysis.declension = none) :
    ¬ CaseCompatible analysis role case observed := by
  rintro ⟨_, cls, declared, _, _⟩
  rw [missing] at declared
  contradiction

def filterAnalyses (analyses : List Analysis) (allows : Analysis → Bool) : List Analysis :=
  analyses.filter allows

theorem filter_does_not_add (analyses : List Analysis) (allows : Analysis → Bool) (analysis : Analysis)
    (survives : analysis ∈ filterAnalyses analyses allows) : analysis ∈ analyses := by
  exact (List.mem_filter.mp survives).1

/-- The witness predicate belongs to the independently checked contextual
relation, for example `CaseCompatible` conjoined with an activation witness.
This wrapper does not manufacture its witness or infer a role. -/
structure ContextualWord (Witness : Analysis → Role → Case → Prop) where
  analysis : Analysis
  role : Role
  grammaticalCase : Case
  licensed : Witness analysis role grammaticalCase

def contextualize {Witness : Analysis → Role → Case → Prop} (analysis : Analysis)
    (role : Role) (case : Case) (witness : Witness analysis role case) : ContextualWord Witness :=
  ⟨analysis, role, case, witness⟩

theorem contextualize_preserves_analysis {Witness : Analysis → Role → Case → Prop}
    (analysis : Analysis) (role : Role) (case : Case) (witness : Witness analysis role case) :
    (contextualize analysis role case witness).analysis = analysis := rfl

theorem contextualize_preserves_occurrence {Witness : Analysis → Role → Case → Prop}
    (analysis : Analysis) (role : Role) (case : Case) (witness : Witness analysis role case) :
    (contextualize analysis role case witness).analysis.occurrence = analysis.occurrence := rfl

/-- A source-bound replay must compare the entire expected reading, not only
its kind or a caller-supplied status. The source reader remains external. -/
def admitsAnalysis (expected proposed : Analysis) : Bool := decide (expected = proposed)

theorem admitted_analysis_exact (expected proposed : Analysis)
    (accepted : admitsAnalysis expected proposed = true) : proposed = expected := by
  exact (of_decide_eq_true accepted).symm

theorem source_identity_cannot_transfer (expected proposed : Analysis)
    (different : expected.occurrence.sourceId ≠ proposed.occurrence.sourceId) :
    admitsAnalysis expected proposed = false := by
  apply decide_eq_false
  intro same
  exact different (congrArg (fun a : Analysis => a.occurrence.sourceId) same)

theorem span_identity_cannot_transfer (expected proposed : Analysis)
    (different : expected.occurrence.byteStart ≠ proposed.occurrence.byteStart ∨
      expected.occurrence.byteEnd ≠ proposed.occurrence.byteEnd) :
    admitsAnalysis expected proposed = false := by
  apply decide_eq_false
  intro same
  rcases different with start | stop
  · exact start (congrArg (fun a : Analysis => a.occurrence.byteStart) same)
  · exact stop (congrArg (fun a : Analysis => a.occurrence.byteEnd) same)

theorem reading_identity_cannot_transfer (expected proposed : Analysis)
    (different : expected.readingId ≠ proposed.readingId ∨
      expected.segmentationId ≠ proposed.segmentationId) :
    admitsAnalysis expected proposed = false := by
  apply decide_eq_false
  intro same
  rcases different with reading | segmentation
  · exact reading (congrArg Analysis.readingId same)
  · exact segmentation (congrArg Analysis.segmentationId same)

end Nabt.Words
