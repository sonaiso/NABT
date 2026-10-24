import Std

/-!
# Classical passages and conditional linguistic applications

There are two evidence levels here. `Attested` checks an exact, nonempty byte
occurrence in a complete source value in the inventory. `Supported` also
requires an explicit interpretation record and an explicit reading of the
exact target. Neither a book title nor a matching quotation supplies that
reading. The interpretation and reading ledgers are premises of the theorem;
their linguistic correctness, source authentication, Unicode parsing and the
Python adapter are not proved by this module.

Three bounded laws are newly formalized from these retained primary passages:

* Sibawayhi, Kitab, OpenITI JK006989, lines 111–120, source SHA-256
  a160f940bb194e6fe7e6655d2c7f28e41f1fc648c4c5e340cc4e42306d5cb625:
  eight ending functions share four surface markings. The mapping is not
  injective. A marking alone cannot determine inflection versus building.
* Ibn Hisham, Matn Qatr al-Nada, Shamela0011376, lines 187–190, SHA-256
  2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d:
  the full inna family assigns nasb/raf when it governs; ma al-kaffa blocks
  that operator, with working and nonworking readings both allowed for layta.
  A blocked operator assigns no replacement case pair. Lightened forms and
  unknown ma status are outside this installed rule's resolved domain.
* Al-Jurjani, al-Awamil al-mi'a, Dar al-Minhaj 1430/2009, printed p. 40:
  the text divides its hundred into 91 transmitted, 7 analogical and 2
  nonverbal factors. This does not identify an owner's different 100-row
  spreadsheet with the book. The scan's interpretation is an explicit
  transcription premise, separate from an automated text extraction.
  Scan SHA-256: 0e589cd1c11d54337ce6db0fff7460540be1cc57ddabbc739d81a0e30fac4c9e.

Immutable textual sources:
https://github.com/OpenITI/0200AH/blob/599f22fe249871f602efe2e0ddc801d3742960a3/data/0180Sibawayhi/0180Sibawayhi.KitabSibawayhi/0180Sibawayhi.KitabSibawayhi.JK006989-ara1
https://github.com/OpenITI/0775AH/blob/61b0c7891699554aeff8dffdb8b1a2a59d2d22ab/data/0761JamalDinIbnHisham/0761JamalDinIbnHisham.MatnQatrNada/0761JamalDinIbnHisham.MatnQatrNada.Shamela0011376-ara1

Lexicon entry attestation stays distinct from the meaning of every use.
An owner's inventory stays distinct from a bound Jurjani passage. Missing
support returns `notEstablished`; no negation is inferred from absence.
There is no application rule for a universal language claim or an external
event. The model does not formalize any of these books in its entirety.
-/

namespace Nabt.ClassicalLanguageEvidence

def lawId : String := "nabt.classical-language-evidence.v1"
def endingLawId : String := "sibawayhi-functions-v1"
def innaLawId : String := "qatr-inna-v1"
def awamilPartitionLawId : String := "jurjani-awamil-partition-v1"

inductive Course where
  | nasb | jarr | raf | jazm | fath | damm | kasr | waqf
  deriving DecidableEq, Repr

inductive Surface where
  | fatha | kasra | damma | sukun
  deriving DecidableEq, Repr

inductive Regime where
  | irab | bina
  deriving DecidableEq, Repr

def courses : List Course := [.nasb, .jarr, .raf, .jazm, .fath, .damm, .kasr, .waqf]
def surfaces : List Surface := [.fatha, .kasra, .damma, .sukun]

def Course.label : Course → String
  | .nasb => "nasb" | .jarr => "jarr" | .raf => "raf" | .jazm => "jazm"
  | .fath => "fath" | .damm => "damm" | .kasr => "kasr" | .waqf => "waqf"

def Surface.label : Surface → String
  | .fatha => "fatha" | .kasra => "kasra" | .damma => "damma" | .sukun => "sukun"

def Regime.label : Regime → String | .irab => "irab" | .bina => "bina"

def Course.surface : Course → Surface
  | .nasb | .fath => .fatha
  | .jarr | .kasr => .kasra
  | .raf | .damm => .damma
  | .jazm | .waqf => .sukun

def Course.regime : Course → Regime
  | .nasb | .jarr | .raf | .jazm => .irab
  | .fath | .damm | .kasr | .waqf => .bina

def coursesForSurface (surface : Surface) : List Course :=
  courses.filter (fun course => decide (course.surface = surface))

theorem course_inventory : courses.length = 8 ∧ courses.Nodup := by decide
theorem surface_inventory : surfaces.length = 4 ∧ surfaces.Nodup := by decide

theorem surface_pairs :
    surfaces.map coursesForSurface =
      [[.nasb, .fath], [.jarr, .kasr], [.raf, .damm], [.jazm, .waqf]] := by decide

theorem each_surface_has_two_readings (surface : Surface) :
    (coursesForSurface surface).length = 2 := by cases surface <;> decide

theorem course_member (course : Course) : course ∈ courses := by cases course <;> decide

theorem surface_readings_exact (course : Course) (surface : Surface) :
    course ∈ coursesForSurface surface ↔ course.surface = surface := by
  simp [coursesForSurface, course_member]

theorem same_surface_different_function :
    Course.nasb.surface = Course.fath.surface ∧ Course.nasb ≠ Course.fath ∧
    Course.nasb.regime ≠ Course.fath.regime := by decide

theorem surface_not_injective : ¬ Function.Injective Course.surface := by
  intro injective
  have impossible := injective (a₁ := Course.nasb) (a₂ := Course.fath) rfl
  cases impossible

theorem surface_and_regime_determine_course (left right : Course)
    (mark : left.surface = right.surface) (regime : left.regime = right.regime) : left = right := by
  cases left <;> cases right <;> simp_all [Course.surface, Course.regime]

inductive InnaOperator where
  | inna | anna | kaanna | lakinna | layta | laalla
  deriving DecidableEq, Repr

inductive InnaForm where
  | full | light
  deriving DecidableEq, Repr

inductive MaStatus where
  | absent | kaffa | unknown
  deriving DecidableEq, Repr

inductive InnaEffect where
  | governed | blocked
  deriving DecidableEq, Repr

def innaOperators : List InnaOperator := [.inna, .anna, .kaanna, .lakinna, .layta, .laalla]
def innaForms : List InnaForm := [.full, .light]
def maStatuses : List MaStatus := [.absent, .kaffa, .unknown]

def InnaOperator.label : InnaOperator → String
  | .inna => "inna" | .anna => "anna" | .kaanna => "kaanna"
  | .lakinna => "lakinna" | .layta => "layta" | .laalla => "laalla"

def InnaForm.label : InnaForm → String | .full => "full" | .light => "light"
def MaStatus.label : MaStatus → String
  | .absent => "absent" | .kaffa => "kaffa" | .unknown => "unknown"
def InnaEffect.label : InnaEffect → String | .governed => "governed" | .blocked => "blocked"

/-- `absent` is a qualified reading, never the absence of an observation. -/
def innaOptions (operator : InnaOperator) (form : InnaForm) (ma : MaStatus) : List InnaEffect :=
  match form, ma with
  | .full, .absent => [.governed]
  | .full, .kaffa => if operator = .layta then [.governed, .blocked] else [.blocked]
  | _, _ => []

/-- A nonworking inna operator does not assign a default raf/raf frame. -/
def workingCases : InnaEffect → Option (Course × Course)
  | .governed => some (.nasb, .raf)
  | .blocked => none

theorem governed_case_pair : workingCases .governed = some (.nasb, .raf) := rfl
theorem blocked_assigns_no_cases : workingCases .blocked = none := rfl

theorem full_without_kaffa_governs (operator : InnaOperator) :
    innaOptions operator .full .absent = [.governed] := rfl

theorem kaffa_blocks_except_layta (operator : InnaOperator) (other : operator ≠ .layta) :
    innaOptions operator .full .kaffa = [.blocked] := by simp [innaOptions, other]

theorem layta_preserves_both_readings :
    innaOptions .layta .full .kaffa = [.governed, .blocked] := by decide

theorem unknown_ma_is_unresolved (operator : InnaOperator) (form : InnaForm) :
    innaOptions operator form .unknown = [] := by cases form <;> rfl

theorem light_form_is_outside_rule (operator : InnaOperator) (ma : MaStatus) :
    innaOptions operator .light ma = [] := by cases ma <;> rfl

theorem governed_requires_qualified_frame (operator : InnaOperator) (form : InnaForm) (ma : MaStatus)
    (permitted : InnaEffect.governed ∈ innaOptions operator form ma) :
    form = .full ∧ (ma = .absent ∨ (ma = .kaffa ∧ operator = .layta)) := by
  cases operator <;> cases form <;> cases ma <;> simp_all [innaOptions]

structure AwamilPartition where
  samai : Nat
  qiyasi : Nat
  manawi : Nat
  deriving DecidableEq, Repr

def AwamilPartition.total (partition : AwamilPartition) : Nat :=
  partition.samai + partition.qiyasi + partition.manawi

def jurjaniPartition : AwamilPartition := ⟨91, 7, 2⟩

theorem jurjani_partition_total : jurjaniPartition.total = 100 := by decide

/-- A matching total does not establish agreement of the component inventory. -/
theorem hundred_does_not_determine_partition :
    ∃ other : AwamilPartition, other.total = 100 ∧ other ≠ jurjaniPartition := by
  exact ⟨⟨90, 8, 2⟩, by decide, by decide⟩

inductive Work where
  | sibawayhi | qatr | maqayis | ownerAwamil | jurjaniAwamil
  deriving DecidableEq, Repr

/-- Complete source identity includes its bytes and bibliographic binding. -/
structure Source where
  sourceId : String
  work : Work
  edition : String
  revision : String
  bytes : List UInt8
  deriving DecidableEq, Repr

structure Passage where
  source : Source
  offset : Nat
  quote : List UInt8
  deriving DecidableEq, Repr

def Attested (inventory : List Source) (passage : Passage) : Prop :=
  passage.source ∈ inventory ∧ passage.quote ≠ [] ∧
  passage.offset + passage.quote.length ≤ passage.source.bytes.length ∧
  (passage.source.bytes.drop passage.offset).take passage.quote.length = passage.quote

instance (inventory : List Source) (passage : Passage) : Decidable (Attested inventory passage) :=
  inferInstanceAs (Decidable (_ ∧ _ ∧ _ ∧ _))

def attested (inventory : List Source) (passage : Passage) : Bool := decide (Attested inventory passage)

theorem attested_iff (inventory : List Source) (passage : Passage) :
    attested inventory passage = true ↔ Attested inventory passage := by simp [attested]

theorem attested_source_exact (inventory : List Source) (passage : Passage)
    (valid : attested inventory passage = true) : passage.source ∈ inventory :=
  ((attested_iff inventory passage).mp valid).1

theorem attested_nonempty (inventory : List Source) (passage : Passage)
    (valid : attested inventory passage = true) : passage.quote ≠ [] :=
  ((attested_iff inventory passage).mp valid).2.1

theorem attested_bounds (inventory : List Source) (passage : Passage)
    (valid : attested inventory passage = true) :
    passage.offset + passage.quote.length ≤ passage.source.bytes.length :=
  ((attested_iff inventory passage).mp valid).2.2.1

theorem attested_bytes_exact (inventory : List Source) (passage : Passage)
    (valid : attested inventory passage = true) :
    (passage.source.bytes.drop passage.offset).take passage.quote.length = passage.quote :=
  ((attested_iff inventory passage).mp valid).2.2.2

theorem changed_bytes_change_source (left right : Source) (changed : left.bytes ≠ right.bytes) :
    left ≠ right := by
  intro same
  exact changed (congrArg Source.bytes same)

inductive InventoryOrigin where
  | owner | jurjani
  deriving DecidableEq, Repr

def InventoryOrigin.work : InventoryOrigin → Work | .owner => .ownerAwamil | .jurjani => .jurjaniAwamil

/-- Lexicon interpretation is local to one entry and its quoted explanation. -/
inductive Rule where
  | endingFunctions
  | innaOperators
  | lexiconEntry (root explanation : String)
  | inventory (origin : InventoryOrigin) (count : Nat)
  | jurjaniPartition
  deriving DecidableEq, Repr

def Rule.work : Rule → Work
  | .endingFunctions => .sibawayhi
  | .innaOperators => .qatr
  | .lexiconEntry _ _ => .maqayis
  | .inventory origin _ => origin.work
  | .jurjaniPartition => .jurjaniAwamil

structure Interpretation where
  passage : Passage
  scope : String
  rule : Rule
  deriving DecidableEq, Repr

/-- These are independently supplied target readings, not deductions from bytes. -/
inductive Observation where
  | ending (course : Course)
  | innaFrame (operator : InnaOperator) (form : InnaForm) (ma : MaStatus)
  | entry (root explanation : String)
  | inventory (origin : InventoryOrigin) (count : Nat)
  | partition (value : AwamilPartition)
  deriving DecidableEq, Repr

structure Reading where
  target : Passage
  scope : String
  observation : Observation
  deriving DecidableEq, Repr

inductive Conclusion where
  | ending (surface : Surface) (regime : Regime)
  | inna (effect : InnaEffect)
  | entry (root explanation : String)
  | inventory (origin : InventoryOrigin) (count : Nat)
  | partition (value : AwamilPartition)
  | everyUseMeaning (root explanation : String)
  | languageGeneral (statement : String)
  | externalEvent (statement : String)
  deriving DecidableEq, Repr

/-- Installed rule-specific applications. Empty output is absence of a license. -/
def conclusions : Rule → Observation → List Conclusion
  | .endingFunctions, .ending course => [.ending course.surface course.regime]
  | .innaOperators, .innaFrame operator form ma => (innaOptions operator form ma).map Conclusion.inna
  | .lexiconEntry root explanation, .entry actualRoot actualExplanation =>
      if root = actualRoot ∧ explanation = actualExplanation then [.entry root explanation] else []
  | .inventory origin count, .inventory actualOrigin actualCount =>
      if origin = actualOrigin ∧ count = actualCount then [.inventory origin count] else []
  | .jurjaniPartition, .partition value =>
      if value = jurjaniPartition then [.partition jurjaniPartition] else []
  | _, _ => []

theorem lexicon_entry_bound (root explanation actualRoot actualExplanation claimRoot claimExplanation : String)
    (accepted : Conclusion.entry claimRoot claimExplanation ∈
      conclusions (.lexiconEntry root explanation) (.entry actualRoot actualExplanation)) :
    actualRoot = root ∧ actualExplanation = explanation ∧ claimRoot = root ∧ claimExplanation = explanation := by
  simp only [conclusions] at accepted
  split at accepted
  · rename_i same
    simp only [List.mem_singleton, Conclusion.entry.injEq] at accepted
    exact ⟨same.1.symm, same.2.symm, accepted.1, accepted.2⟩
  · simp at accepted

theorem lexicon_entry_is_not_inna_rule (root explanation : String)
    (operator : InnaOperator) (form : InnaForm) (ma : MaStatus) :
    conclusions (.lexiconEntry root explanation) (.innaFrame operator form ma) = [] := rfl

theorem entry_does_not_license_every_use (rule : Rule) (observation : Observation) (root explanation : String) :
    Conclusion.everyUseMeaning root explanation ∉ conclusions rule observation := by
  cases rule <;> cases observation <;> simp [conclusions]

theorem no_general_language_conclusion (rule : Rule) (observation : Observation) (statement : String) :
    Conclusion.languageGeneral statement ∉ conclusions rule observation := by
  cases rule <;> cases observation <;> simp [conclusions]

theorem no_external_event_conclusion (rule : Rule) (observation : Observation) (statement : String) :
    Conclusion.externalEvent statement ∉ conclusions rule observation := by
  cases rule <;> cases observation <;> simp [conclusions]

theorem owner_inventory_is_not_jurjani (count requestedCount : Nat) (observation : Observation) :
    Conclusion.inventory .jurjani requestedCount ∉ conclusions (.inventory .owner count) observation := by
  cases observation <;> simp [conclusions]

structure Context where
  sources : List Source
  interpretations : List Interpretation
  readings : List Reading
  deriving DecidableEq, Repr

structure Request where
  target : Passage
  scope : String
  conclusion : Conclusion
  deriving DecidableEq, Repr

structure Evidence where
  interpretation : Interpretation
  reading : Reading
  deriving DecidableEq, Repr

/-- A source quotation and an interpretation are different premises. -/
def Supported (ctx : Context) (request : Request) (evidence : Evidence) : Prop :=
  evidence.interpretation ∈ ctx.interpretations ∧ evidence.reading ∈ ctx.readings ∧
  Attested ctx.sources evidence.interpretation.passage ∧
  evidence.interpretation.passage.source.work = evidence.interpretation.rule.work ∧
  Attested ctx.sources request.target ∧ evidence.reading.target = request.target ∧
  evidence.reading.scope = request.scope ∧ evidence.interpretation.scope = request.scope ∧
  request.scope ≠ "" ∧
  request.conclusion ∈ conclusions evidence.interpretation.rule evidence.reading.observation

instance (ctx : Context) (request : Request) (evidence : Evidence) :
    Decidable (Supported ctx request evidence) :=
  inferInstanceAs (Decidable (_ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _))

def supports (ctx : Context) (request : Request) (evidence : Evidence) : Bool :=
  decide (Supported ctx request evidence)

theorem supports_iff (ctx : Context) (request : Request) (evidence : Evidence) :
    supports ctx request evidence = true ↔ Supported ctx request evidence := by simp [supports]

theorem support_requires_interpretation (ctx : Context) (request : Request) (evidence : Evidence)
    (licensed : supports ctx request evidence = true) : evidence.interpretation ∈ ctx.interpretations :=
  ((supports_iff ctx request evidence).mp licensed).1

theorem support_requires_reading (ctx : Context) (request : Request) (evidence : Evidence)
    (licensed : supports ctx request evidence = true) : evidence.reading ∈ ctx.readings :=
  ((supports_iff ctx request evidence).mp licensed).2.1

theorem support_requires_attested_passage (ctx : Context) (request : Request) (evidence : Evidence)
    (licensed : supports ctx request evidence = true) :
    Attested ctx.sources evidence.interpretation.passage :=
  ((supports_iff ctx request evidence).mp licensed).2.2.1

theorem support_work_binding (ctx : Context) (request : Request) (evidence : Evidence)
    (licensed : supports ctx request evidence = true) :
    evidence.interpretation.passage.source.work = evidence.interpretation.rule.work :=
  ((supports_iff ctx request evidence).mp licensed).2.2.2.1

theorem jurjani_partition_requires_jurjani_binding (ctx : Context) (request : Request) (evidence : Evidence)
    (licensed : supports ctx request evidence = true)
    (rule : evidence.interpretation.rule = .jurjaniPartition) :
    evidence.interpretation.passage.source.work = .jurjaniAwamil := by
  have binding := support_work_binding ctx request evidence licensed
  simpa [rule, Rule.work] using binding

theorem support_target_binding (ctx : Context) (request : Request) (evidence : Evidence)
    (licensed : supports ctx request evidence = true) :
    Attested ctx.sources request.target ∧ evidence.reading.target = request.target := by
  have accepted := (supports_iff ctx request evidence).mp licensed
  exact ⟨accepted.2.2.2.2.1, accepted.2.2.2.2.2.1⟩

theorem support_scope_binding (ctx : Context) (request : Request) (evidence : Evidence)
    (licensed : supports ctx request evidence = true) :
    evidence.reading.scope = request.scope ∧ evidence.interpretation.scope = request.scope ∧ request.scope ≠ "" := by
  have accepted := (supports_iff ctx request evidence).mp licensed
  exact ⟨accepted.2.2.2.2.2.2.1, accepted.2.2.2.2.2.2.2.1, accepted.2.2.2.2.2.2.2.2.1⟩

theorem support_rule_application (ctx : Context) (request : Request) (evidence : Evidence)
    (licensed : supports ctx request evidence = true) :
    request.conclusion ∈ conclusions evidence.interpretation.rule evidence.reading.observation :=
  ((supports_iff ctx request evidence).mp licensed).2.2.2.2.2.2.2.2.2

theorem support_excludes_external_event (ctx : Context) (request : Request) (evidence : Evidence)
    (licensed : supports ctx request evidence = true) (statement : String) :
    request.conclusion ≠ .externalEvent statement := by
  intro event
  have member := support_rule_application ctx request evidence licensed
  rw [event] at member
  exact no_external_event_conclusion _ _ _ member

theorem support_excludes_general_language (ctx : Context) (request : Request) (evidence : Evidence)
    (licensed : supports ctx request evidence = true) (statement : String) :
    request.conclusion ≠ .languageGeneral statement := by
  intro general
  have member := support_rule_application ctx request evidence licensed
  rw [general] at member
  exact no_general_language_conclusion _ _ _ member

theorem support_excludes_every_use (ctx : Context) (request : Request) (evidence : Evidence)
    (licensed : supports ctx request evidence = true) (root explanation : String) :
    request.conclusion ≠ .everyUseMeaning root explanation := by
  intro every
  have member := support_rule_application ctx request evidence licensed
  rw [every] at member
  exact entry_does_not_license_every_use _ _ _ _ member

def hasSupport (ctx : Context) (request : Request) : Bool :=
  ctx.interpretations.any fun interpretation =>
    ctx.readings.any fun reading => supports ctx request ⟨interpretation, reading⟩

theorem hasSupport_iff (ctx : Context) (request : Request) :
    hasSupport ctx request = true ↔
      ∃ interpretation ∈ ctx.interpretations, ∃ reading ∈ ctx.readings,
        supports ctx request ⟨interpretation, reading⟩ = true := by
  simp [hasSupport, List.any_eq_true]

inductive Judgment where
  | conditionallySupported | notEstablished
  deriving DecidableEq, Repr

def assess (ctx : Context) (request : Request) : Judgment :=
  if hasSupport ctx request then .conditionallySupported else .notEstablished

theorem judgment_supported_iff (ctx : Context) (request : Request) :
    assess ctx request = .conditionallySupported ↔ hasSupport ctx request = true := by
  simp [assess]

theorem absence_leaves_unestablished (ctx : Context) (request : Request)
    (absent : hasSupport ctx request = false) : assess ctx request = .notEstablished := by
  simp [assess, absent]

theorem source_only_does_not_license (sources : List Source) (readings : List Reading) (request : Request) :
    assess ⟨sources, [], readings⟩ request = .notEstablished := by simp [assess, hasSupport]

theorem unread_target_does_not_license (sources : List Source) (interpretations : List Interpretation)
    (request : Request) : assess ⟨sources, interpretations, []⟩ request = .notEstablished := by
  simp [assess, hasSupport]

end Nabt.ClassicalLanguageEvidence
