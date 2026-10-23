import Nabt.Cell

/-!
# Finite governor equations with typed roles and retained alternatives

The inventory and equations adapt MIT-licensed Saleh1967/Mashru,
commit e4c801ffe9171dadedcc3aae23051ea0953ae361:
Jisr/AwamilJadwal.lean, Jisr/Awamil.lean, SLGE/Awamil.lean and SLGE/Wad.lean.
Copyright (c) 2026 Saleh1967. The retained license is in NOTICE.md.

These are native NABT contracts, with no upstream imports. Completeness below
is completeness of a finite equation checker relative to an explicit table.
It does not mean completeness of Arabic grammar, correctness of a parser,
attestation of the original workbook, or truth of an asserted proposition.
An assignment must already bind a role to licensed evidence from one source
and reading. Case equations alone cannot determine lexical activation,
speech force, an omitted word, or the intended scope of a sentence.

Case codes are the ordinary single-mark representation: nasb/fatha=0,
raf/damma=1, jarr/kasra=2, jazm/sukun=3. The mathematical injection into Cell
does not assert that every Arabic case is realized by that surface mark.
-/

namespace Nabt.Governors

def lawId : String := "nabt.governors.v1"

inductive Case where
  | nasb | raf | jarr | jazm
  deriving DecidableEq, Repr

def Case.code : Case → Nat
  | .nasb => 0 | .raf => 1 | .jarr => 2 | .jazm => 3

def Case.ofCode : Nat → Option Case
  | 0 => some .nasb | 1 => some .raf | 2 => some .jarr | 3 => some .jazm | _ => none

def Case.mark (c : Case) : Nabt.Mark := ⟨c.code, by cases c <;> decide⟩

theorem case_decode_code (c : Case) : Case.ofCode c.code = some c := by
  cases c <;> rfl

theorem case_code_injective : Function.Injective Case.code := by
  intro a b h
  have := congrArg Case.ofCode h
  simpa only [case_decode_code, Option.some.injEq] using this

theorem case_cell_mark (carrier : Carrier) (c : Case) :
    (Cell.encode ⟨carrier, c.mark⟩).val % 4 = c.code := by
  have h : c.code < 4 := c.mark.isLt
  simp only [Cell.encode, Case.mark]
  omega

inductive Category where
  | noun | verb
  deriving DecidableEq, Repr

def Category.accepts : Category → Case → Bool
  | .noun, .jazm => false
  | .verb, .jarr => false
  | _, _ => true

inductive Role where
  | primary | complement | imperfect | governedNoun
  | conjunctHead | conjunct | condition | conditionAnswer | vocative
  deriving DecidableEq, Repr

def roles : List Role := [.primary, .complement, .imperfect, .governedNoun,
  .conjunctHead, .conjunct, .condition, .conditionAnswer, .vocative]

def Role.code : Role → Nat
  | .primary => 0 | .complement => 1 | .imperfect => 2 | .governedNoun => 6
  | .conjunctHead => 9 | .conjunct => 10 | .condition => 11
  | .conditionAnswer => 12 | .vocative => 13

def Role.ofCode : Nat → Option Role
  | 0 => some .primary | 1 => some .complement | 2 => some .imperfect
  | 6 => some .governedNoun | 9 => some .conjunctHead | 10 => some .conjunct
  | 11 => some .condition | 12 => some .conditionAnswer | 13 => some .vocative
  | _ => none

def Role.category : Role → Category
  | .imperfect | .condition | .conditionAnswer => .verb
  | _ => .noun

def Role.name : Role → String
  | .primary => "الاسم أو المفعول الأول"
  | .complement => "الخبر أو المفعول الثاني"
  | .imperfect => "المضارع"
  | .governedNoun => "المجرور"
  | .conjunctHead => "المعطوف عليه"
  | .conjunct => "المعطوف"
  | .condition => "فعل الشرط"
  | .conditionAnswer => "جواب الشرط"
  | .vocative => "المنادى"

theorem role_decode_code (r : Role) : Role.ofCode r.code = some r := by
  cases r <;> rfl

theorem role_code_injective : Function.Injective Role.code := by
  intro a b h
  have := congrArg Role.ofCode h
  simpa only [role_decode_code, Option.some.injEq] using this

def roleMarkNumberDomain : String := "nabt.governors.role-mark.v1"

/-- A typed syntactic-role/case code, distinct from a character's Cell code.
The same arithmetic does not identify the two different domains. -/
def roleMarkNumber (r : Role) (c : Case) : Nat := 4 * r.code + c.code

def decodeRoleMark (n : Nat) : Option (Role × Case) := do
  let role ← Role.ofCode (n / 4)
  let mark ← Case.ofCode (n % 4)
  pure (role, mark)

theorem roleMark_decode (r : Role) (c : Case) :
    decodeRoleMark (roleMarkNumber r c) = some (r, c) := by
  have hc : c.code < 4 := c.mark.isLt
  have hd : (4 * r.code + c.code) / 4 = r.code := by omega
  have hm : (4 * r.code + c.code) % 4 = c.code := by omega
  simp [decodeRoleMark, roleMarkNumber, hd, hm, role_decode_code, case_decode_code]

theorem roleMark_injective {r s : Role} {c d : Case}
    (same : roleMarkNumber r c = roleMarkNumber s d) : r = s ∧ c = d := by
  have := congrArg decodeRoleMark same
  simpa only [roleMark_decode, Option.some.injEq, Prod.mk.injEq] using this

theorem roleMark_bound (r : Role) (c : Case) : roleMarkNumber r c < 56 := by
  cases r <;> cases c <;> decide

theorem roleMark_unused_role_rejected :
    decodeRoleMark 12 = none ∧ decodeRoleMark 20 = none := by decide

inductive GovernorClass where
  | kana | inna | zanna | subjunctive | jussive | kada | preposition
  | conjunction | purpose | jussiveCondition | otherCondition | interrogative | vocative
  deriving DecidableEq, Repr

def classes : List GovernorClass := [.kana, .inna, .zanna, .subjunctive, .jussive,
  .kada, .preposition, .conjunction, .purpose, .jussiveCondition,
  .otherCondition, .interrogative, .vocative]

def GovernorClass.code : GovernorClass → Nat
  | .kana => 1 | .inna => 2 | .zanna => 3 | .subjunctive => 4 | .jussive => 5
  | .kada => 6 | .preposition => 7 | .conjunction => 8 | .purpose => 9
  | .jussiveCondition => 10 | .otherCondition => 11 | .interrogative => 12 | .vocative => 13

def GovernorClass.ofCode : Nat → Option GovernorClass
  | 1 => some .kana | 2 => some .inna | 3 => some .zanna
  | 4 => some .subjunctive | 5 => some .jussive | 6 => some .kada
  | 7 => some .preposition | 8 => some .conjunction | 9 => some .purpose
  | 10 => some .jussiveCondition | 11 => some .otherCondition
  | 12 => some .interrogative | 13 => some .vocative | _ => none

def GovernorClass.name : GovernorClass → String
  | .kana => "كان وأخواتها" | .inna => "إنّ وأخواتها" | .zanna => "ظنّ وأخواتها"
  | .subjunctive => "نواصب المضارع" | .jussive => "جوازم المضارع" | .kada => "كاد وأخواتها"
  | .preposition => "حروف الجر" | .conjunction => "العطف" | .purpose => "لام التعليل"
  | .jussiveCondition => "الشرط الجازم" | .otherCondition => "الشرط غير الجازم"
  | .interrogative => "الاستفهام" | .vocative => "النداء"

theorem class_decode_code (c : GovernorClass) : GovernorClass.ofCode c.code = some c := by
  cases c <;> rfl

theorem class_code_injective : Function.Injective GovernorClass.code := by
  intro a b h
  have := congrArg GovernorClass.ofCode h
  simpa only [class_decode_code, Option.some.injEq] using this

theorem class_codes_exact : classes.map GovernorClass.code = List.range' 1 13 := by decide

/-- Unknown integers are not the upstream permissive empty-equation default. -/
theorem unknown_class_not_empty_license :
    GovernorClass.ofCode 0 = none ∧ GovernorClass.ofCode 14 = none := by decide

abbrev Equation := Role × Case
abbrev Alternative := List Equation
abbrev Link := Role × Role

def GovernorClass.equations : GovernorClass → List Alternative
  | .kana => [[(.primary, .raf), (.complement, .nasb)]]
  | .inna => [[(.primary, .nasb), (.complement, .raf)]]
  | .zanna => [[(.primary, .nasb), (.complement, .nasb)]]
  | .subjunctive => [[(.imperfect, .nasb)]]
  | .jussive => [[(.imperfect, .jazm)]]
  | .kada => [[(.primary, .raf), (.imperfect, .raf)]]
  | .preposition => [[(.governedNoun, .jarr)]]
  | .purpose => [[(.governedNoun, .jarr)], [(.imperfect, .nasb)]]
  | .jussiveCondition => [[(.condition, .jazm), (.conditionAnswer, .jazm)]]
  | .vocative => [[(.vocative, .nasb)], [(.vocative, .raf)]]
  | .conjunction | .otherCondition | .interrogative => [[]]

def GovernorClass.links : GovernorClass → List Link
  | .conjunction => [(.conjunctHead, .conjunct)]
  | _ => []

theorem equations_closed (c : GovernorClass) :
    (c.equations.all fun alt => alt.all fun e => e.1.category.accepts e.2) = true := by
  cases c <;> decide

theorem inna_requires_both_slots :
    GovernorClass.inna.equations = [[(.primary, .nasb), (.complement, .raf)]] := rfl

theorem distinct_nasikh_equations :
    ([GovernorClass.kana, .inna, .zanna].map GovernorClass.equations).Nodup := by decide

theorem alternatives_not_collapsed :
    GovernorClass.purpose.equations.length = 2 ∧
    GovernorClass.vocative.equations.length = 2 ∧
    GovernorClass.conjunction.links = [(.conjunctHead, .conjunct)] := by decide

structure Row where
  label : String
  governorClass : GovernorClass
  implicit : Bool
  deriving DecidableEq, Repr

/-- Exact source row order and labels. A label may name an operator rather
than spell an input token. The associated evidence audit is separate. -/
def table : List Row := [
  ⟨"إنّ", .inna, false⟩,
  ⟨"أنّ", .inna, false⟩,
  ⟨"كأنّ", .inna, false⟩,
  ⟨"لكنّ", .inna, false⟩,
  ⟨"ليت", .inna, false⟩,
  ⟨"لعلّ", .inna, false⟩,
  ⟨"كان", .kana, false⟩,
  ⟨"أصبح", .kana, false⟩,
  ⟨"أضحى", .kana, false⟩,
  ⟨"أمسى", .kana, false⟩,
  ⟨"بات", .kana, false⟩,
  ⟨"صار", .kana, false⟩,
  ⟨"ظلّ", .kana, false⟩,
  ⟨"ليس", .kana, false⟩,
  ⟨"ما زال", .kana, false⟩,
  ⟨"ما برح", .kana, false⟩,
  ⟨"ما فتئ", .kana, false⟩,
  ⟨"ما انفكّ", .kana, false⟩,
  ⟨"ما دام", .kana, false⟩,
  ⟨"ظنَّ", .zanna, false⟩,
  ⟨"حسب", .zanna, false⟩,
  ⟨"خال", .zanna, false⟩,
  ⟨"زعم", .zanna, false⟩,
  ⟨"عدَّ", .zanna, false⟩,
  ⟨"جعل", .zanna, false⟩,
  ⟨"رأى", .zanna, false⟩,
  ⟨"وجد", .zanna, false⟩,
  ⟨"علم", .zanna, false⟩,
  ⟨"درى", .zanna, false⟩,
  ⟨"كاد", .kada, false⟩,
  ⟨"أوشك", .kada, false⟩,
  ⟨"عسى", .kada, false⟩,
  ⟨"طفق", .kada, false⟩,
  ⟨"شرع", .kada, false⟩,
  ⟨"بدأ", .kada, false⟩,
  ⟨"من", .preposition, false⟩,
  ⟨"إلى", .preposition, false⟩,
  ⟨"عن", .preposition, false⟩,
  ⟨"على", .preposition, false⟩,
  ⟨"في", .preposition, false⟩,
  ⟨"الباء", .preposition, false⟩,
  ⟨"اللام", .preposition, false⟩,
  ⟨"الكاف", .preposition, false⟩,
  ⟨"حتى (جر)", .preposition, false⟩,
  ⟨"رُبَّ", .preposition, false⟩,
  ⟨"مذ", .preposition, false⟩,
  ⟨"منذ", .preposition, false⟩,
  ⟨"خلا", .preposition, false⟩,
  ⟨"عدا", .preposition, false⟩,
  ⟨"حاشا", .preposition, false⟩,
  ⟨"الواو", .conjunction, false⟩,
  ⟨"الفاء", .conjunction, false⟩,
  ⟨"ثم", .conjunction, false⟩,
  ⟨"أو", .conjunction, false⟩,
  ⟨"أم", .conjunction, false⟩,
  ⟨"بل", .conjunction, false⟩,
  ⟨"لكن (عطف)", .conjunction, false⟩,
  ⟨"حتى (عطف)", .conjunction, false⟩,
  ⟨"لم", .jussive, false⟩,
  ⟨"لما", .jussive, false⟩,
  ⟨"لا الناهية", .jussive, false⟩,
  ⟨"لام الأمر", .jussive, false⟩,
  ⟨"أنْ", .subjunctive, false⟩,
  ⟨"لن", .subjunctive, false⟩,
  ⟨"كي", .subjunctive, false⟩,
  ⟨"إذن", .subjunctive, false⟩,
  ⟨"لام التعليل", .purpose, false⟩,
  ⟨"حتى (المصدرية)", .subjunctive, false⟩,
  ⟨"فاء السببية", .subjunctive, true⟩,
  ⟨"واو المعية", .subjunctive, true⟩,
  ⟨"إنْ", .jussiveCondition, false⟩,
  ⟨"مَن", .jussiveCondition, false⟩,
  ⟨"ما", .jussiveCondition, false⟩,
  ⟨"مهما", .jussiveCondition, false⟩,
  ⟨"متى", .jussiveCondition, false⟩,
  ⟨"أين", .jussiveCondition, false⟩,
  ⟨"أينما", .jussiveCondition, false⟩,
  ⟨"أنى", .jussiveCondition, false⟩,
  ⟨"حيثما", .jussiveCondition, false⟩,
  ⟨"كيفما", .jussiveCondition, false⟩,
  ⟨"إذا", .otherCondition, false⟩,
  ⟨"لو", .otherCondition, false⟩,
  ⟨"لولا", .otherCondition, false⟩,
  ⟨"لوما", .otherCondition, false⟩,
  ⟨"الهمزة (أَ)", .interrogative, false⟩,
  ⟨"هل", .interrogative, false⟩,
  ⟨"مَن", .interrogative, false⟩,
  ⟨"ما", .interrogative, false⟩,
  ⟨"ماذا", .interrogative, false⟩,
  ⟨"أيّ", .interrogative, false⟩,
  ⟨"كم (استفهامية)", .interrogative, false⟩,
  ⟨"كيف", .interrogative, false⟩,
  ⟨"أين", .interrogative, false⟩,
  ⟨"متى", .interrogative, false⟩,
  ⟨"يا", .vocative, false⟩,
  ⟨"أيا", .vocative, false⟩,
  ⟨"هيا", .vocative, false⟩,
  ⟨"آ", .vocative, false⟩,
  ⟨"واو القسم", .preposition, false⟩,
  ⟨"تاء القسم", .preposition, false⟩
]

def lookup (label : String) : List Row := table.filter (fun row => row.label == label)

theorem lookup_exact (label : String) (row : Row) :
    row ∈ lookup label ↔ row ∈ table ∧ row.label = label := by
  simp [lookup]

theorem inventory_rows_exact :
    table.length = 100 ∧
    (classes.map fun c => (table.filter (fun r => r.governorClass == c)).length) =
      [13, 6, 10, 7, 4, 6, 17, 8, 1, 10, 4, 10, 4] := by decide

theorem inventory_labels_exact :
    (table.map Row.label).eraseDups.length = 96 := by decide

theorem implicit_rows_exact :
    (table.filter Row.implicit).map Row.label = ["فاء السببية", "واو المعية"] := by decide

theorem ambiguous_labels_retained :
    (["مَن", "ما", "متى", "أين"].map fun label =>
      (lookup label).map (fun row => row.governorClass.code)) =
        [[10, 12], [10, 12], [10, 12], [10, 12]] := by decide

theorem inna_rows_exact :
    (table.filter (fun row => row.governorClass == .inna)).map Row.label =
      ["إنّ", "أنّ", "كأنّ", "لكنّ", "ليت", "لعلّ"] := by decide

abbrev Assignment := Role → Option Case

/-- Complete check: an unknown role does not satisfy an equality. -/
def checkEquation (a : Assignment) (e : Equation) : Bool := a e.1 == some e.2

def checkLink (a : Assignment) (l : Link) : Bool :=
  match a l.1, a l.2 with
  | some c, some d => c == d
  | _, _ => false

def checkAlternative (a : Assignment) (eqs : Alternative) (links : List Link) : Bool :=
  eqs.all (checkEquation a) && links.all (checkLink a)

/-- Independent proposition stated in terms of observations, not the checker. -/
def Satisfies (a : Assignment) (eqs : Alternative) (links : List Link) : Prop :=
  (∀ r c, (r, c) ∈ eqs → a r = some c) ∧
  (∀ r s, (r, s) ∈ links → ∃ c, a r = some c ∧ a s = some c)

theorem checkEquation_iff (a : Assignment) (e : Equation) :
    checkEquation a e = true ↔ a e.1 = some e.2 := by
  simp [checkEquation]

theorem checkLink_iff (a : Assignment) (l : Link) :
    checkLink a l = true ↔ ∃ c, a l.1 = some c ∧ a l.2 = some c := by
  cases hl : a l.1 with
  | none => simp [checkLink, hl]
  | some left =>
    cases hr : a l.2 with
    | none => simp [checkLink, hl, hr]
    | some right =>
      simp only [checkLink, hl, hr, beq_iff_eq, Option.some.injEq]
      constructor
      · intro same
        exact ⟨left, rfl, same.symm⟩
      · intro h
        obtain ⟨c, hleft, hright⟩ := h
        exact hleft.trans hright.symm

theorem checkAlternative_iff (a : Assignment) (eqs : Alternative) (links : List Link) :
    checkAlternative a eqs links = true ↔ Satisfies a eqs links := by
  simp only [checkAlternative, Bool.and_eq_true, List.all_eq_true]
  constructor
  · intro h
    constructor
    · intro r c member
      exact (checkEquation_iff a (r, c)).mp (h.1 (r, c) member)
    · intro r s member
      exact (checkLink_iff a (r, s)).mp (h.2 (r, s) member)
  · intro h
    constructor
    · intro e member
      exact (checkEquation_iff a e).mpr (h.1 e.1 e.2 member)
    · intro l member
      exact (checkLink_iff a l).mpr (h.2 l.1 l.2 member)

def completeAlternatives (c : GovernorClass) (a : Assignment) : List Alternative :=
  c.equations.filter (fun alt => checkAlternative a alt c.links)

theorem completeAlternatives_exact (c : GovernorClass) (a : Assignment) (alt : Alternative) :
    alt ∈ completeAlternatives c a ↔ alt ∈ c.equations ∧ Satisfies a alt c.links := by
  simp only [completeAlternatives, List.mem_filter, checkAlternative_iff]

theorem completeAlternatives_sound (c : GovernorClass) (a : Assignment) (alt : Alternative)
    (h : alt ∈ completeAlternatives c a) : Satisfies a alt c.links :=
  ((completeAlternatives_exact c a alt).mp h).2

theorem completeAlternatives_complete (c : GovernorClass) (a : Assignment) (alt : Alternative)
    (member : alt ∈ c.equations) (satisfies : Satisfies a alt c.links) :
    alt ∈ completeAlternatives c a :=
  (completeAlternatives_exact c a alt).mpr ⟨member, satisfies⟩

/-- Incomplete evidence stays viable. This is not the complete check above. -/
def viableEquation (a : Assignment) (e : Equation) : Bool :=
  a e.1 == none || checkEquation a e

def viableLink (a : Assignment) (l : Link) : Bool :=
  a l.1 == none || a l.2 == none || checkLink a l

def viableAlternative (a : Assignment) (eqs : Alternative) (links : List Link) : Bool :=
  eqs.all (viableEquation a) && links.all (viableLink a)

def viableAlternatives (c : GovernorClass) (a : Assignment) : List Alternative :=
  c.equations.filter (fun alt => viableAlternative a alt c.links)

theorem unknown_equation_pending (a : Assignment) (r : Role) (c : Case) (h : a r = none) :
    viableEquation a (r, c) = true ∧ checkEquation a (r, c) = false := by
  simp [viableEquation, checkEquation, h]

theorem conflicting_equation_rejected (a : Assignment) (r : Role) (c d : Case)
    (observed : a r = some d) (different : d ≠ c) :
    viableEquation a (r, c) = false := by
  simp [viableEquation, checkEquation, observed, different]

theorem completed_is_viable (a : Assignment) (eqs : Alternative) (links : List Link)
    (complete : checkAlternative a eqs links = true) : viableAlternative a eqs links = true := by
  simp only [checkAlternative, Bool.and_eq_true, List.all_eq_true] at complete
  simp only [viableAlternative, Bool.and_eq_true, List.all_eq_true]
  constructor
  · intro e member
    simp [viableEquation, complete.1 e member]
  · intro l member
    simp [viableLink, complete.2 l member]

theorem completeAlternatives_retained (c : GovernorClass) (a : Assignment) (alt : Alternative)
    (h : alt ∈ completeAlternatives c a) : alt ∈ viableAlternatives c a := by
  simp only [completeAlternatives, List.mem_filter] at h
  simp only [viableAlternatives, List.mem_filter]
  exact ⟨h.1, completed_is_viable a alt c.links h.2⟩

/-- Equality propagates for arbitrary lengths, not just the finite inventory. -/
def chainEqual : List Case → Bool
  | a :: b :: rest => a == b && chainEqual (b :: rest)
  | _ => true

theorem conjunction_propagates : ∀ (rest : List Case) (a : Case),
    chainEqual (a :: rest) = true → ∀ x ∈ rest, x = a
  | [], _, _, x, hx => by simp at hx
  | b :: rest, a, h, x, hx => by
    simp only [chainEqual, Bool.and_eq_true, beq_iff_eq] at h
    obtain ⟨hab, hrest⟩ := h
    simp only [List.mem_cons] at hx
    rcases hx with hx | hx
    · rw [hx, hab]
    · rw [conjunction_propagates rest b hrest x hx, hab]

end Nabt.Governors
