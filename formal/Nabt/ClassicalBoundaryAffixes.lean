import Std
/-! Conditional symbolic transformations. Source acquisition, Python decoding,
free-text morphology and acoustic truth are outside these theorems. -/
namespace Nabt.ClassicalBoundaryAffixes

def lawId := "nabt.classical-boundary-affixes.v1"
def alphabetId := "nabt.boundary-affix-segments.v1"
abbrev Seg := Nat
def a : Seg := 29
def i : Seg := 30
def u : Seg := 31
def aa : Seg := 32
def ii : Seg := 33
def uu : Seg := 34
def nun : Seg := 25
def waw : Seg := 27
def ya : Seg := 28
inductive Radical where | waw | ya | sound deriving DecidableEq, Repr
inductive LongVowel where | a | i | u deriving DecidableEq, Repr
inductive Person where | ms | fs | dual | mp | fp deriving DecidableEq, Repr
inductive Suffix where | none | subject | object | emphatic deriving DecidableEq, Repr
inductive End where | wasl | waqf deriving DecidableEq, Repr
inductive Following where | none | consonant | hamzatWasl deriving DecidableEq, Repr
inductive Profile where | khalil | yunus | both deriving DecidableEq, Repr
inductive NunKind where | light | heavy | feminine deriving DecidableEq, Repr
inductive Shape where
 | singularOpen | deletedYaCommand | deletedWawCommand | retainedYaCommand
 | retainedWawCommand | deletedYaIndicative | deletedWawIndicative | indicativeDual
 deriving DecidableEq, Repr
inductive Tag where
 | deleteWeak | retain | dropBeforeWasl | alif | restoreGlide | dropAfterRetained
 | restoreIndicative | yunusReplacement | anaPause | anaFatha | anaSukun
 deriving DecidableEq, Repr
inductive Evidence where
 | conditional | khalil | yunus | analogyYunus | majority | minority
 deriving DecidableEq, Repr
structure Alternative where
 segments : List Seg
 tag : Tag
 evidence : Evidence := .conditional
 deriving DecidableEq, Repr
structure WeakFrame where
 stem : List Seg
 radical : Radical
 vowel : LongVowel
 person : Person
 suffix : Suffix
 deriving DecidableEq, Repr

def longSegment : LongVowel → Seg | .a => aa | .i => ii | .u => uu
def shortSegment : LongVowel → Seg | .a => a | .i => i | .u => u
def WeakMatch : Radical → LongVowel → Prop
 | .waw, .a | .waw, .u | .ya, .a | .ya, .i => True
 | _, _ => False
instance (r : Radical) (v : LongVowel) : Decidable (WeakMatch r v) := by
 cases r <;> cases v <;> simp [WeakMatch] <;> infer_instance

def WeakLicensed (f : WeakFrame) (out : Alternative) : Prop :=
 f.person = .ms ∧ f.suffix = .none ∧ WeakMatch f.radical f.vowel ∧
 out = ⟨f.stem ++ [shortSegment f.vowel], .deleteWeak, .conditional⟩
def weakEnumerate (f : WeakFrame) : List Alternative :=
 if f.person == .ms && f.suffix == .none && decide (WeakMatch f.radical f.vowel)
 then [⟨f.stem ++ [shortSegment f.vowel], .deleteWeak, .conditional⟩] else []

theorem weak_exact (f : WeakFrame) (out : Alternative) :
 out ∈ weakEnumerate f ↔ WeakLicensed f out := by
 simp only [weakEnumerate, WeakLicensed]
 split <;> simp_all

theorem weak_sound (f : WeakFrame) (out : Alternative)
 (h : out ∈ weakEnumerate f) : WeakLicensed f out := (weak_exact f out).mp h

theorem weak_complete (f : WeakFrame) (out : Alternative)
 (h : WeakLicensed f out) : out ∈ weakEnumerate f := (weak_exact f out).mpr h

theorem weak_suffix_blocks (f : WeakFrame) (h : f.suffix ≠ .none) :
 weakEnumerate f = [] := by simp [weakEnumerate, h]

theorem weak_person_blocks (f : WeakFrame) (h : f.person ≠ .ms) :
 weakEnumerate f = [] := by simp [weakEnumerate, h]

theorem weak_preserves_stem (f : WeakFrame) (out : Alternative)
 (h : WeakLicensed f out) : out.segments = f.stem ++ [shortSegment f.vowel] := by
 rcases h with ⟨_, _, _, rfl⟩
 rfl

structure LightFrame where
 stem : List Seg
 shape : Shape
 profile : Profile
 nunKind : NunKind
 ending : End
 following : Following
 deriving DecidableEq, Repr

def sourceTail : Shape → List Seg
 | .singularOpen => [a,nun]
 | .deletedYaCommand | .deletedYaIndicative => [i,nun]
 | .deletedWawCommand | .deletedWawIndicative => [u,nun]
 | .retainedYaCommand => [ya,i,nun]
 | .retainedWawCommand => [waw,u,nun]
 | .indicativeDual => [aa,nun,i]

def validLight (f : LightFrame) : Bool :=
 f.nunKind == .light && !(f.shape == .indicativeDual && f.profile == .yunus) &&
 (f.ending == .wasl || f.following == .none)

def PausalTag : Shape → Profile → Tag → Prop
 | .singularOpen, _, .alif => True
 | .deletedYaCommand, _, .restoreGlide | .deletedWawCommand, _, .restoreGlide => True
 | .retainedYaCommand, p, .dropAfterRetained | .retainedWawCommand, p, .dropAfterRetained => p ≠ .yunus
 | .retainedYaCommand, p, .yunusReplacement | .retainedWawCommand, p, .yunusReplacement => p ≠ .khalil
 | .deletedYaIndicative, p, .restoreIndicative | .deletedWawIndicative, p, .restoreIndicative => p ≠ .yunus
 | .deletedYaIndicative, p, .yunusReplacement | .deletedWawIndicative, p, .yunusReplacement => p ≠ .khalil
 | .indicativeDual, _, .restoreIndicative => True
 | _, _, _ => False

def pauseTags : Shape → Profile → List Tag
 | .singularOpen, _ => [.alif]
 | .deletedYaCommand, _ | .deletedWawCommand, _ => [.restoreGlide]
 | .retainedYaCommand, .khalil | .retainedWawCommand, .khalil => [.dropAfterRetained]
 | .retainedYaCommand, .yunus | .retainedWawCommand, .yunus => [.yunusReplacement]
 | .retainedYaCommand, .both | .retainedWawCommand, .both => [.dropAfterRetained,.yunusReplacement]
 | .deletedYaIndicative, .khalil | .deletedWawIndicative, .khalil => [.restoreIndicative]
 | .deletedYaIndicative, .yunus | .deletedWawIndicative, .yunus => [.yunusReplacement]
 | .deletedYaIndicative, .both | .deletedWawIndicative, .both => [.restoreIndicative,.yunusReplacement]
 | .indicativeDual, _ => [.restoreIndicative]

theorem pause_tags_exact (s : Shape) (p : Profile) (t : Tag) :
 t ∈ pauseTags s p ↔ PausalTag s p t := by
 cases s <;> cases p <;> cases t <;> simp [pauseTags,PausalTag]

def LightTag (f : LightFrame) (t : Tag) : Prop :=
 validLight f = true ∧ match f.ending with
 | .waqf => PausalTag f.shape f.profile t
 | .wasl => if f.shape ≠ .indicativeDual ∧ f.following = .hamzatWasl
            then t = .dropBeforeWasl else t = .retain

def lightTags (f : LightFrame) : List Tag :=
 if validLight f then match f.ending with
 | .waqf => pauseTags f.shape f.profile
 | .wasl => if f.shape != .indicativeDual && f.following == .hamzatWasl
            then [.dropBeforeWasl] else [.retain]
 else []

theorem light_tags_exact (f : LightFrame) (t : Tag) :
 t ∈ lightTags f ↔ LightTag f t := by
 unfold lightTags LightTag
 split
 · rename_i h
   simp only [h, true_and]
   cases f.ending
   · simp only
     split <;> simp_all
   · exact pause_tags_exact f.shape f.profile t
 · simp_all

def lightSuffix (f : LightFrame) : Tag → List Seg
 | .retain => sourceTail f.shape
 | .dropBeforeWasl => (sourceTail f.shape).dropLast
 | .alif => [aa]
 | .restoreGlide => if f.shape == .deletedYaCommand then [ii] else [uu]
 | .dropAfterRetained => if f.shape == .retainedYaCommand then [ya] else [waw]
 | .restoreIndicative => match f.shape with
   | .deletedYaIndicative => [ii,nun]
   | .deletedWawIndicative => [uu,nun]
   | _ => [aa,nun]
 | .yunusReplacement => match f.shape with
   | .retainedYaCommand => [ya,ii]
   | .retainedWawCommand => [waw,uu]
   | .deletedYaIndicative => [ii]
   | _ => [uu]
 | _ => []

def lightEvidence (s : Shape) : Tag → Evidence
 | .dropAfterRetained | .restoreIndicative => .khalil
 | .yunusReplacement => match s with
   | .retainedYaCommand | .retainedWawCommand => .yunus
   | _ => .analogyYunus
 | _ => .conditional

def lightRender (f : LightFrame) (t : Tag) : Alternative :=
 ⟨f.stem ++ lightSuffix f t, t, lightEvidence f.shape t⟩
def LightLicensed (f : LightFrame) (out : Alternative) : Prop :=
 ∃ t, LightTag f t ∧ out = lightRender f t
def lightEnumerate (f : LightFrame) : List Alternative := (lightTags f).map (lightRender f)

theorem light_exact (f : LightFrame) (out : Alternative) :
 out ∈ lightEnumerate f ↔ LightLicensed f out := by
 simp only [lightEnumerate,List.mem_map,light_tags_exact,LightLicensed]
 constructor
 · rintro ⟨t,h,eq⟩; exact ⟨t,h,eq.symm⟩
 · rintro ⟨t,h,eq⟩; exact ⟨t,h,eq.symm⟩

theorem light_sound (f : LightFrame) (out : Alternative)
 (h : out ∈ lightEnumerate f) : LightLicensed f out := (light_exact f out).mp h

theorem light_complete (f : LightFrame) (out : Alternative)
 (h : LightLicensed f out) : out ∈ lightEnumerate f := (light_exact f out).mpr h

theorem heavy_not_light (f : LightFrame) (h : f.nunKind = .heavy) :
 lightEnumerate f = [] := by simp [lightEnumerate,lightTags,validLight,h]

theorem feminine_not_light (f : LightFrame) (h : f.nunKind = .feminine) :
 lightEnumerate f = [] := by simp [lightEnumerate,lightTags,validLight,h]

theorem contradictory_pause_blocked (f : LightFrame)
 (pause : f.ending = .waqf) (connected : f.following ≠ .none) :
 lightEnumerate f = [] := by
 simp [lightEnumerate,lightTags,validLight,pause,connected]

theorem light_stem_preserved (f : LightFrame) (out : Alternative)
 (h : LightLicensed f out) : ∃ tail, out.segments = f.stem ++ tail := by
 rcases h with ⟨t,_,rfl⟩
 exact ⟨lightSuffix f t,rfl⟩

theorem analogy_not_reported (f : LightFrame)
 (h : f.shape = .deletedYaIndicative ∨ f.shape = .deletedWawIndicative) :
 (lightRender f .yunusReplacement).evidence = .analogyYunus := by
 rcases h with h | h <;> simp [lightRender,lightEvidence,h]

inductive AnaAnalysis where | speaker | masdariyya | other deriving DecidableEq, Repr
inductive AnaProfile where | majority | minoritySukun | both deriving DecidableEq, Repr
structure AnaFrame where
 analysis : AnaAnalysis
 profile : AnaProfile
 ending : End
 deriving DecidableEq, Repr

def AnaTag (f : AnaFrame) (t : Tag) : Prop :=
 f.analysis = .speaker ∧ match t with
 | .anaPause => f.ending = .waqf ∧ f.profile ≠ .minoritySukun
 | .anaFatha => f.ending = .wasl ∧ f.profile ≠ .minoritySukun
 | .anaSukun => f.ending = .wasl ∧ f.profile ≠ .majority
 | _ => False

def anaTags (f : AnaFrame) : List Tag :=
 if f.analysis != .speaker then [] else match f.ending, f.profile with
 | .waqf, .minoritySukun => [] | .waqf, _ => [.anaPause]
 | .wasl, .majority => [.anaFatha] | .wasl, .minoritySukun => [.anaSukun]
 | .wasl, .both => [.anaFatha,.anaSukun]

def anaRender : Tag → Alternative
 | .anaPause => ⟨[0,a,nun,aa],.anaPause,.majority⟩
 | .anaFatha => ⟨[0,a,nun,a],.anaFatha,.majority⟩
 | .anaSukun => ⟨[0,a,nun],.anaSukun,.minority⟩
 | t => ⟨[],t,.conditional⟩
def AnaLicensed (f : AnaFrame) (out : Alternative) : Prop :=
 ∃ t, AnaTag f t ∧ out = anaRender t
def anaEnumerate (f : AnaFrame) : List Alternative := (anaTags f).map anaRender

theorem ana_tags_exact (f : AnaFrame) (t : Tag) : t ∈ anaTags f ↔ AnaTag f t := by
 rcases f with ⟨s,p,e⟩
 cases s <;> cases p <;> cases e <;> cases t <;> simp [anaTags,AnaTag]

theorem ana_exact (f : AnaFrame) (out : Alternative) :
 out ∈ anaEnumerate f ↔ AnaLicensed f out := by
 simp only [anaEnumerate,List.mem_map,ana_tags_exact,AnaLicensed]
 constructor
 · rintro ⟨t,h,eq⟩; exact ⟨t,h,eq.symm⟩
 · rintro ⟨t,h,eq⟩; exact ⟨t,h,eq.symm⟩

theorem ana_sound (f : AnaFrame) (out : Alternative)
 (h : out ∈ anaEnumerate f) : AnaLicensed f out := (ana_exact f out).mp h

theorem ana_complete (f : AnaFrame) (out : Alternative)
 (h : AnaLicensed f out) : out ∈ anaEnumerate f := (ana_exact f out).mpr h

theorem particle_blocked (f : AnaFrame) (h : f.analysis = .masdariyya) :
 anaEnumerate f = [] := by simp [anaEnumerate,anaTags,h]

theorem unknown_minority_pause_blocked :
 anaEnumerate ⟨.speaker,.minoritySukun,.waqf⟩ = [] := rfl

theorem light_missing_alternative_refutes_completeness
 (f : LightFrame) (out : Alternative) (proposal : List Alternative)
 (licensed : LightLicensed f out) (missing : out ∉ proposal) :
 ¬ (∀ r, LightLicensed f r → r ∈ proposal) := by
 intro complete
 exact missing (complete out licensed)
end Nabt.ClassicalBoundaryAffixes
