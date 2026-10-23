import Nabt.TextEvidence

/-!
# Source-bound nominal candidates, cardinal agreement and weak positions

This is a conditional algebra, not a proof of Arabic lexical extraction.
An admitted constraint requires an independently established nominal reading
and a receipt tied to its source revision, scope, occurrence span/segmentation
and reading. Correctness of the source statement, linguistic rule activation,
Unicode reader and witness qualification remains external. Raw article,
tanwin, suffix and pattern observations never activate a feature constraint.

Gender is lexical masculine/feminine; plural morphology is a separate axis.
In particular, a masculine noun may have sound-feminine-plural morphology.
The dual profile records grammatical number only, not inflected-dual status.
These profiles establish neither a contextual case nor a grammatical role.

Cardinal agreement is scoped to 1..99, 100 and 1000 with the singular gender
of the counted noun already witnessed. The case field is a construction
condition, never a sentence's actual parsed case. It does not create an
ordinal reading or a fact about a number of world entities.

Weak-position classification concerns W/Y slots in a supplied canonical
triliteral root. It supplies no lexical attestation, inverse ilal, or root
reconstruction. Nominal manqus is a separate conjunction of five witnessed
properties; failure to observe one property is not its negation.
-/

namespace Nabt.NominalEvidence

def lawId : String := "nabt.nominal-evidence.v1"

structure Profile where
  gender : Fin 2
  form : Fin 6
  definiteness : Fin 2
  deriving DecidableEq, Repr

def Profile.code (p : Profile) : Nat := 12 * p.gender.val + 2 * p.form.val + p.definiteness.val

def Profile.number (p : Profile) : Nat :=
  if p.form.val = 0 then 0 else if p.form.val = 1 then 1 else 2

/-- A true sound-masculine-plural class excludes lexical feminine. The reverse
restriction is intentionally absent for sound-feminine-plural morphology. -/
def Profile.admissible (p : Profile) : Bool := !(p.gender.val == 1 && p.form.val == 2)

def allProfiles : List Profile := (List.finRange 2).flatMap fun g =>
  (List.finRange 6).flatMap fun f =>
    (List.finRange 2).map fun d => ⟨g, f, d⟩

def profiles : List Profile := allProfiles.filter Profile.admissible

inductive Constraint where
  | masculine | feminine | singular | dual | plural
  | soundMasculine | soundFeminine | broken | otherPlural
  | definite | indefinite
  deriving DecidableEq, Repr

def constraints : List Constraint := [.masculine, .feminine, .singular, .dual, .plural,
  .soundMasculine, .soundFeminine, .broken, .otherPlural, .definite, .indefinite]

def Constraint.code : Constraint → Nat
  | .masculine => 0 | .feminine => 1 | .singular => 2 | .dual => 3 | .plural => 4
  | .soundMasculine => 5 | .soundFeminine => 6 | .broken => 7 | .otherPlural => 8
  | .definite => 9 | .indefinite => 10

def Constraint.accepts : Constraint → Profile → Bool
  | .masculine, p => p.gender.val == 0
  | .feminine, p => p.gender.val == 1
  | .singular, p => p.number == 0
  | .dual, p => p.number == 1
  | .plural, p => p.number == 2
  | .soundMasculine, p => p.form.val == 2
  | .soundFeminine, p => p.form.val == 3
  | .broken, p => p.form.val == 4
  | .otherPlural, p => p.form.val == 5
  | .definite, p => p.definiteness.val == 1
  | .indefinite, p => p.definiteness.val == 0

def refine (evidence : List Constraint) : List Profile :=
  profiles.filter fun p => evidence.all (fun c => c.accepts p)

theorem profiles_complete (p : Profile) : p ∈ profiles ↔ p.admissible = true := by
  have member : p ∈ allProfiles := by
    rcases p with ⟨g, f, d⟩
    simp [allProfiles, List.mem_flatMap, List.mem_map, List.mem_finRange]
  simp [profiles, member]

theorem profile_code_injective (p q : Profile) (h : p.code = q.code) : p = q := by
  rcases p with ⟨⟨g, hg⟩, ⟨f, hf⟩, ⟨d, hd⟩⟩
  rcases q with ⟨⟨g', hg'⟩, ⟨f', hf'⟩, ⟨d', hd'⟩⟩
  simp only [Profile.code] at h
  have h1 : g = g' := by omega
  have h2 : f = f' := by omega
  have h3 : d = d' := by omega
  subst g'; subst f'; subst d'; rfl

theorem profile_inventory : profiles.length = 22 ∧
    (profiles.map Profile.code).Nodup ∧
    (profiles.map Profile.code) = (List.range 24).filter (fun n => n != 16 && n != 17) := by
  decide

theorem masculine_sound_feminine_retained (d : Fin 2) :
    (⟨0, 3, d⟩ : Profile) ∈ profiles := by
  rw [profiles_complete]; rfl

theorem refine_exact (evidence : List Constraint) (p : Profile) :
    p ∈ refine evidence ↔ p.admissible = true ∧ ∀ c ∈ evidence, c.accepts p = true := by
  simp [refine, profiles_complete, List.all_eq_true]

theorem no_constraint_retains_all : refine [] = profiles := by simp [refine]

theorem deletion_cannot_narrow (kept removed : List Constraint) (p : Profile)
    (h : p ∈ refine (kept ++ removed)) : p ∈ refine kept := by
  rw [refine_exact] at h ⊢
  exact ⟨h.1, fun c hc => h.2 c (List.mem_append_left _ hc)⟩

theorem duplicate_constraint_idempotent (c : Constraint) (rest : List Constraint) :
    refine (c :: c :: rest) = refine (c :: rest) := by
  simp [refine]

theorem constraint_order_irrelevant (left right : List Constraint) :
    refine (left ++ right) = refine (right ++ left) := by
  simp [refine, List.all_append, Bool.and_comm]

theorem refinement_composes (left right : List Constraint) :
    (refine left).filter (fun p => right.all (fun c => c.accepts p)) = refine (left ++ right) := by
  simp [refine, List.filter_filter, List.all_append, Bool.and_comm]

theorem contradictory_gender_empty (rest : List Constraint) :
    refine (.masculine :: .feminine :: rest) = [] := by
  apply List.eq_nil_iff_forall_not_mem.mpr
  intro p h
  have hs := (refine_exact _ p).mp h
  have hm := hs.2 .masculine (by simp)
  have hf := hs.2 .feminine (by simp)
  simp only [Constraint.accepts, beq_iff_eq] at hm hf
  omega

abbrev Binding := TextEvidence.Binding

structure Receipt where
  binding : Binding
  constraint : Constraint
  active : Bool
  blocked : Bool
  deriving DecidableEq, Repr

/-- Bit order: source, scope, occurrence, reading, active, blocked, noun domain.
Only the blocker has negative polarity. These are structural prerequisites;
the public boundary must rederive them from qualified source evidence. -/
def activation (source scope occurrence reading active blocked nounDomain : Bool) : Bool :=
  source && scope && occurrence && reading && active && !blocked && nounDomain

def Receipt.admissible (target : Binding) (nounDomain : Bool) (r : Receipt) : Bool :=
  activation
    (decide (r.binding.sourceId = target.sourceId ∧ r.binding.sourceRevision = target.sourceRevision))
    (decide (r.binding.scopeId = target.scopeId))
    (decide (r.binding.occurrenceId = target.occurrenceId ∧
      r.binding.byteStart = target.byteStart ∧ r.binding.byteEnd = target.byteEnd ∧
      r.binding.segmentationId = target.segmentationId))
    (decide (r.binding.readingId = target.readingId)) r.active r.blocked nounDomain

inductive Observation where
  | article | tanwin | suffix | pattern
  deriving DecidableEq, Repr

inductive Input where
  | observed (value : Observation)
  | receipt (value : Receipt)
  deriving DecidableEq, Repr

def Input.accepted (target : Binding) (nounDomain : Bool) : Input → Option Constraint
  | .observed _ => none
  | .receipt r => if r.admissible target nounDomain then some r.constraint else none

def acceptedConstraints (target : Binding) (nounDomain : Bool) (inputs : List Input) : List Constraint :=
  inputs.filterMap (Input.accepted target nounDomain)

def qualifiedCandidates (target : Binding) (nounDomain : Bool) (inputs : List Input) : List Profile :=
  if nounDomain then refine (acceptedConstraints target nounDomain inputs) else []

theorem activation_exact (s c o r a b n : Bool) :
    activation s c o r a b n = true ↔
      s = true ∧ c = true ∧ o = true ∧ r = true ∧ a = true ∧ b = false ∧ n = true := by
  cases s <;> cases c <;> cases o <;> cases r <;> cases a <;> cases b <;> cases n <;> decide

theorem admitted_binding_and_domain (target : Binding) (nounDomain : Bool) (r : Receipt)
    (h : r.admissible target nounDomain = true) : r.binding = target ∧ nounDomain = true := by
  have bits := (activation_exact _ _ _ _ _ _ _).mp h
  have hs := of_decide_eq_true bits.1
  have hc := of_decide_eq_true bits.2.1
  have ho := of_decide_eq_true bits.2.2.1
  have hr := of_decide_eq_true bits.2.2.2.1
  refine ⟨?_, bits.2.2.2.2.2.2⟩
  cases hb : r.binding; cases target
  simp_all

theorem foreign_receipt_inert (target : Binding) (nounDomain : Bool) (r : Receipt)
    (foreign : r.binding ≠ target) : Input.accepted target nounDomain (.receipt r) = none := by
  simp only [Input.accepted]
  have h : r.admissible target nounDomain ≠ true := fun h => foreign (admitted_binding_and_domain _ _ _ h).1
  simp [h]

theorem inactive_or_blocked_inert (target : Binding) (nounDomain : Bool) (r : Receipt)
    (h : r.active = false ∨ r.blocked = true) :
    Input.accepted target nounDomain (.receipt r) = none := by
  rcases h with h | h <;> simp [Input.accepted, Receipt.admissible, activation, h]

theorem observed_shape_inert (target : Binding) (nounDomain : Bool) (o : Observation) (rest : List Input) :
    qualifiedCandidates target nounDomain (.observed o :: rest) = qualifiedCandidates target nounDomain rest := rfl

theorem nonnominal_has_no_profiles (target : Binding) (inputs : List Input) :
    qualifiedCandidates target false inputs = [] := rfl

theorem qualified_candidate_has_domain (target : Binding) (nounDomain : Bool) (inputs : List Input)
    (p : Profile) (h : p ∈ qualifiedCandidates target nounDomain inputs) : nounDomain = true := by
  cases nounDomain <;> simp_all [qualifiedCandidates]

theorem accepted_constraint_has_receipt (target : Binding) (nounDomain : Bool) (inputs : List Input)
    (c : Constraint) (h : c ∈ acceptedConstraints target nounDomain inputs) :
    ∃ r, Input.receipt r ∈ inputs ∧ r.admissible target nounDomain = true ∧ r.constraint = c := by
  obtain ⟨input, member, someC⟩ := List.mem_filterMap.mp h
  cases input with
  | observed o => simp [Input.accepted] at someC
  | receipt r =>
    refine ⟨r, member, ?_⟩
    simp only [Input.accepted] at someC
    split at someC <;> simp_all

theorem deleting_receipts_cannot_narrow (target : Binding) (nounDomain : Bool)
    (kept removed : List Input) (p : Profile)
    (h : p ∈ qualifiedCandidates target nounDomain (kept ++ removed)) :
    p ∈ qualifiedCandidates target nounDomain kept := by
  have domain := qualified_candidate_has_domain target nounDomain (kept ++ removed) p h
  subst nounDomain
  simp only [qualifiedCandidates, ite_true, acceptedConstraints,
    List.filterMap_append] at h ⊢
  exact deletion_cannot_narrow _ _ p h

namespace Cardinal

def quantities : List Nat := List.range' 1 99 ++ [100, 1000]

def supported (q : Nat) : Bool := decide ((1 ≤ q ∧ q ≤ 99) ∨ q = 100 ∨ q = 1000)

inductive CaseRequirement where
  | contextual | genitive | accusative
  deriving DecidableEq, Repr

def CaseRequirement.label : CaseRequirement → String
  | .contextual => "contextual" | .genitive => "genitive" | .accusative => "accusative"

structure Rule where
  countedNumber : Nat
  countedCase : CaseRequirement
  unitGender : Option (Fin 2)
  tenGender : Option (Fin 2)
  deriving DecidableEq, Repr

def opposite (g : Fin 2) : Fin 2 := if g.val = 0 then 1 else 0

def body (q : Nat) (g : Fin 2) : Rule :=
  let unit := if q ≤ 19 then q else q % 10
  { countedNumber := if q = 1 then 0 else if q = 2 then 1 else if q ≤ 10 then 2 else 0
    countedCase := if q ≤ 2 then .contextual else if q ≤ 10 || q = 100 || q = 1000 then .genitive else .accusative
    unitGender := if q = 100 || q = 1000 || (20 ≤ q && q % 10 == 0) then none
      else if unit ≤ 2 || q = 11 || q = 12 then some g else some (opposite g)
    tenGender := if 11 ≤ q && q ≤ 19 then some g else none }

def rule (q : Nat) (g : Fin 2) : Option Rule := if supported q then some (body q g) else none

theorem support_exact (q : Nat) : q ∈ quantities ↔ supported q = true := by
  simp [quantities, supported]; omega

theorem rule_exact (q : Nat) (g : Fin 2) (r : Rule) :
    rule q g = some r ↔ supported q = true ∧ body q g = r := by
  simp only [rule]
  split <;> simp_all

theorem unsupported_no_rule (q : Nat) (g : Fin 2) (h : supported q = false) : rule q g = none := by
  simp [rule, h]

theorem no_zero_or_composite_hundreds (g : Fin 2) :
    rule 0 g = none ∧ rule 101 g = none ∧ rule 200 g = none ∧ rule 1001 g = none := by
  simp [rule, supported]

theorem opposite_involutive (g : Fin 2) : opposite (opposite g) = g := by
  have bound := g.isLt
  have cases : g.val = 0 ∨ g.val = 1 := by omega
  rcases cases with h | h
  · have eq : g = 0 := Fin.ext h
    subst g; rfl
  · have eq : g = 1 := Fin.ext h
    subst g; rfl

set_option maxRecDepth 16384 in
theorem quantities_inventory : quantities.length = 101 ∧ quantities.Nodup := by decide

end Cardinal

namespace Weak

structure Mask where
  first : Bool
  middle : Bool
  last : Bool
  deriving DecidableEq, Repr

def Mask.code (m : Mask) : Nat := (if m.first then 1 else 0) +
  (if m.middle then 2 else 0) + (if m.last then 4 else 0)

inductive Class where
  | sound | mithal | ajwaf | naqis | lafifMafruq | lafifMaqrun
  | initialAdjacentResidual | tripleWeakResidual
  deriving DecidableEq, Repr

def Class.label : Class → String
  | .sound => "sound" | .mithal => "mithal" | .ajwaf => "ajwaf" | .naqis => "naqis"
  | .lafifMafruq => "lafif_mafruq" | .lafifMaqrun => "lafif_maqrun"
  | .initialAdjacentResidual => "initial_adjacent_residual"
  | .tripleWeakResidual => "triple_weak_residual"

def classify : Mask → Class
  | ⟨false, false, false⟩ => .sound
  | ⟨true, false, false⟩ => .mithal
  | ⟨false, true, false⟩ => .ajwaf
  | ⟨false, false, true⟩ => .naqis
  | ⟨true, false, true⟩ => .lafifMafruq
  | ⟨false, true, true⟩ => .lafifMaqrun
  | ⟨true, true, false⟩ => .initialAdjacentResidual
  | ⟨true, true, true⟩ => .tripleWeakResidual

def radicalWeak (c : Char) : Bool := c == 'و' || c == 'ي'

def ofRoot (root : Fin 3 → Char) : Mask :=
  ⟨radicalWeak (root 0), radicalWeak (root 1), radicalWeak (root 2)⟩

theorem radical_exact (c : Char) : radicalWeak c = true ↔ c = 'و' ∨ c = 'ي' := by
  simp [radicalWeak]

theorem classify_injective (a b : Mask) (h : classify a = classify b) : a = b := by
  rcases a with ⟨a1,a2,a3⟩; rcases b with ⟨b1,b2,b3⟩
  cases a1 <;> cases a2 <;> cases a3 <;> cases b1 <;> cases b2 <;> cases b3 <;> simp_all [classify]

theorem root_mask_exact (root : Fin 3 → Char) :
    (ofRoot root).first = radicalWeak (root 0) ∧
    (ofRoot root).middle = radicalWeak (root 1) ∧
    (ofRoot root).last = radicalWeak (root 2) := ⟨rfl,rfl,rfl⟩

theorem sound_iff_no_weak_slot (m : Mask) :
    classify m = .sound ↔ m.first = false ∧ m.middle = false ∧ m.last = false := by
  rcases m with ⟨a,b,c⟩; cases a <;> cases b <;> cases c <;> decide

end Weak

namespace Manqus

structure Features where
  noun : Bool
  inflected : Bool
  necessaryFinalYaa : Bool
  precedingKasra : Bool
  finalYaaUnshaddad : Bool
  deriving DecidableEq, Repr

def Features.accepted (f : Features) : Bool :=
  f.noun && f.inflected && f.necessaryFinalYaa && f.precedingKasra && f.finalYaaUnshaddad

def Features.code (f : Features) : Nat := (if f.noun then 1 else 0) +
  (if f.inflected then 2 else 0) + (if f.necessaryFinalYaa then 4 else 0) +
  (if f.precedingKasra then 8 else 0) + (if f.finalYaaUnshaddad then 16 else 0)

def models : List Features := [false,true].flatMap fun n =>
  [false,true].flatMap fun i => [false,true].flatMap fun y =>
    [false,true].flatMap fun k => [false,true].map fun s => ⟨n,i,y,k,s⟩

/-- Positive and negative features are independently witnessed. An unknown
property has both bits false; contradiction has both true. -/
def compatible (positive negative model : Features) : Bool :=
  (!positive.noun || model.noun) && (!negative.noun || !model.noun) &&
  (!positive.inflected || model.inflected) && (!negative.inflected || !model.inflected) &&
  (!positive.necessaryFinalYaa || model.necessaryFinalYaa) && (!negative.necessaryFinalYaa || !model.necessaryFinalYaa) &&
  (!positive.precedingKasra || model.precedingKasra) && (!negative.precedingKasra || !model.precedingKasra) &&
  (!positive.finalYaaUnshaddad || model.finalYaaUnshaddad) && (!negative.finalYaaUnshaddad || !model.finalYaaUnshaddad)

def candidates (positive negative : Features) : List Features :=
  models.filter (compatible positive negative)

def conflicts (p n : Features) : Bool :=
  (p.noun && n.noun) || (p.inflected && n.inflected) ||
  (p.necessaryFinalYaa && n.necessaryFinalYaa) ||
  (p.precedingKasra && n.precedingKasra) || (p.finalYaaUnshaddad && n.finalYaaUnshaddad)

theorem accepted_exact (f : Features) : f.accepted = true ↔
    f.noun = true ∧ f.inflected = true ∧ f.necessaryFinalYaa = true ∧
      f.precedingKasra = true ∧ f.finalYaaUnshaddad = true := by
  simp [Features.accepted, and_assoc]

theorem models_complete (f : Features) : f ∈ models := by
  rcases f with ⟨a,b,c,d,e⟩; cases a <;> cases b <;> cases c <;> cases d <;> cases e <;> decide

theorem partial_exact (p n f : Features) : f ∈ candidates p n ↔ compatible p n f = true := by
  simp [candidates, models_complete]

theorem unknown_retains_all : candidates ⟨false,false,false,false,false⟩ ⟨false,false,false,false,false⟩ = models := by
  simp [candidates, compatible]

theorem unknown_does_not_decide :
    (⟨true,true,true,true,true⟩ : Features) ∈ candidates ⟨false,false,false,false,false⟩ ⟨false,false,false,false,false⟩ ∧
    (⟨false,false,false,false,false⟩ : Features) ∈ candidates ⟨false,false,false,false,false⟩ ⟨false,false,false,false,false⟩ := by
  rw [unknown_retains_all]
  exact ⟨models_complete _, models_complete _⟩

theorem negative_noun_blocks_acceptance (f : Features) (h : f.noun = false) : f.accepted = false := by
  simp [Features.accepted, h]

/-- A geminate final ya, as in كرسيّ, fails this defining condition even if
the four other complete-model flags are true. Preceding kasra is phonological
adjacency, not merely the last written vowel before a shadda cluster. -/
theorem final_gemination_blocks (f : Features) (h : f.finalYaaUnshaddad = false) : f.accepted = false := by
  simp [Features.accepted, h]

theorem contradictory_features_eliminate (p n : Features) (h : conflicts p n = true) :
    candidates p n = [] := by
  apply List.eq_nil_iff_forall_not_mem.mpr
  intro f member
  have hf := (partial_exact p n f).mp member
  simp only [conflicts, Bool.or_eq_true, Bool.and_eq_true] at h
  rcases h with (((⟨hp,hn⟩ | ⟨hp,hn⟩) | ⟨hp,hn⟩) | ⟨hp,hn⟩) | ⟨hp,hn⟩ <;>
    simp_all [compatible, and_assoc]

end Manqus

def occurrenceCount (occurrences : List Nat) : Nat := occurrences.eraseDups.length

private theorem erased_nodup : ∀ xs : List Nat, xs.eraseDups.Nodup
  | [] => by simp
  | a :: xs => by
    rw [List.eraseDups_cons]
    apply List.nodup_cons.mpr
    constructor
    · simp [List.mem_eraseDups]
    · exact erased_nodup (xs.filter fun b => !b == a)
termination_by xs => xs.length
decreasing_by exact Nat.lt_succ_of_le (List.length_filter_le _ _)

theorem count_depends_on_members (a b : List Nat) (h : ∀ x, x ∈ a ↔ x ∈ b) :
    occurrenceCount a = occurrenceCount b := by
  have perm : a.eraseDups.Perm b.eraseDups :=
    (List.perm_ext_iff_of_nodup (erased_nodup a) (erased_nodup b)).mpr (by simpa using h)
  exact perm.length_eq

theorem duplicate_occurrence_idempotent (x : Nat) (xs : List Nat) :
    occurrenceCount (x :: x :: xs) = occurrenceCount (x :: xs) := by
  apply count_depends_on_members
  intro y; simp

theorem occurrence_order_irrelevant (a b : List Nat) :
    occurrenceCount (a ++ b) = occurrenceCount (b ++ a) := by
  apply count_depends_on_members
  intro x; simp [or_comm]

theorem equal_count_does_not_recover_order (a b : Nat) (different : a ≠ b) :
    occurrenceCount [a,b] = occurrenceCount [b,a] ∧ ([a,b] : List Nat) ≠ [b,a] := by
  constructor
  · apply count_depends_on_members; intro x; simp [or_comm]
  · intro h; exact different (List.cons.inj h).1

/-- New Unicode projection of Mashru's fourteen pronoun readings. Gender2
means unspecified for this NABT projection (the source calls it shared).
No Unicode/A116 equivalence or general partial-vocalization parser theorem
is asserted. Definiteness is licensed by a separate qualified pronoun rule. -/
structure PronounRow where
  surface : String
  person : Nat
  gender : Nat
  number : Nat
  deriving DecidableEq, Repr

def pronounRows : List PronounRow := [
  ⟨"هُوَ",3,0,0⟩, ⟨"هُمَا",3,0,1⟩, ⟨"هُمْ",3,0,2⟩,
  ⟨"هِيَ",3,1,0⟩, ⟨"هُمَا",3,1,1⟩, ⟨"هُنَّ",3,1,2⟩,
  ⟨"أَنْتَ",2,0,0⟩, ⟨"أَنْتُمَا",2,0,1⟩, ⟨"أَنْتُمْ",2,0,2⟩,
  ⟨"أَنْتِ",2,1,0⟩, ⟨"أَنْتُمَا",2,1,1⟩, ⟨"أَنْتُنَّ",2,1,2⟩,
  ⟨"أَنَا",1,2,0⟩, ⟨"نَحْنُ",1,2,2⟩]

theorem pronoun_inventory : pronounRows.length = 14 ∧ pronounRows.Nodup := by decide

theorem dual_pronoun_gender_ambiguous :
    ((pronounRows.filter (fun p => p.surface == "هُمَا")).map PronounRow.gender) = [0,1] ∧
    ((pronounRows.filter (fun p => p.surface == "أَنْتُمَا")).map PronounRow.gender) = [0,1] := by decide

end Nabt.NominalEvidence
