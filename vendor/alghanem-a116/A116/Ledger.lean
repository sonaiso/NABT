import A116.ExhaustPause
import A116.Wazn

/-!
# الدفترُ مملوءًا من الأوزان المبرهنة (ADR ١٩)

قرارُ المالك (2026-10-12): «حقولُ الاشتقاق والصرف والنحو تُملأ من الأوزان المبرهنة»، و«الأصولُ ثلاثٌ أو أربع
وتُقرأ بتوافيق n المقاطع». فهذا الدفترُ `filled` يأخذ حقولَ الترميز والإملاء والصوت كما هي في `Exhaust.current`
(لا يمسّه)، ويملأ ثلاثةً ببراهين `A116.Wazn` (ADR ١٦) — كلُّ برهانٍ يحمل حدَّه في نوعه:

* **الاشتقاق** (`IshtiqaqAt`): كلُّ وزنٍ من الإحدى والثلاثين صفٌّ في جدول درجته بعدده n (`wazn_row_mem`)، فهو
  «مشتقٌّ» بقرارٍ محسوب (`mushtaq`)؛ وصفُّه لا يتغيّر بتغيّر الأصل الصحيح (`Wazn.syllables_fixed_by_wazn`)؛
  والأصلُ يُستردّ من الصيغة بوزنها (`Wazn.realize_determines_root`). وما لم يبلغه وزنٌ مبرهَن فـ`mushtaq` له
  `false` — جامدٌ **بالنسبة إلى هذه الأوزان** لا جامدٌ مطلقًا.
* **الصرف** (`SarfAt`): كلُّ وزنٍ في درجته مرخَّصٌ بقيد الحدّ وصلًا ووقفًا (`Wazn.thulathi_licensed`)، وحالةُ آخره
  في الوصل يعيّنها قالبُه (`lastH`: الماضي فتح، والأمرُ سكون) — أي مبنيّ؛ والمعرَبُ والممنوعُ من الصرف في الأسماء
  ليسا في هذه القوالب الفعليّة.
* **النحو** (`MahallAt`): **موضعُ العلامة** في المفرد واحدٌ هو الأخير — تغييرُ الحالة لا يمسّ ما قبله، والوقفُ يمحوها.
  أمّا العاملُ الذي يعيّنها فدرجةُ التركيب، بعدُ.
* **الدلالة**: معلَّقةٌ باسمها `DALALA_NEEDS_SEALED_WITNESS` — فالبوّابةُ تقف عند الدرجة الأولى بقانونها نفسِه
  (`filled_stops_at_one`)، والدلالةُ وحدَها هي المانع (`dalala_alone_blocks`).

والأصول: `four_and_three_share_n` — دَحْرَجَ (أربعة أصول) وكَتَّبَ (ثلاثة) صفٌّ واحدٌ بعددٍ واحد (الدرجة 3، n = 24):
فعددُ الأصول يحمله الوزنُ (`Root n`)، ويُقرأ عبر توافيق n المقاطع، ولا يُقرأ من n وحدَه.
-/

namespace A116.Ledger

open A116 A116.Stages A116.Ternary A116.Ladder A116.Hadd A116.Boundary A116.Exhaust A116.Wazn

/-- الأوزانُ الثلاثيّةُ بأرقامها في `mabni_verbs.SOUND_TEMPLATES`. -/
def indexed : List (Nat × WaznC 3) := (List.range thulathi.length).zip thulathi

/-- الصيغةُ المرجعيّة للوزن ابتداءً (على ك ت ب) بحالة آخره الصرفيّة. -/
def formOf (p : Nat × WaznC 3) (ex : Exit) : List Cell := realize p.2 ktb .start ex (lastH p.1)

/-- صفُّ الوزن وصلًا: مقاطعُه. -/
def rowOf (p : Nat × WaznC 3) : Option (List Syl) := syllables (formOf p .continue)

/-- الدرجةُ والعدد n لصفٍّ: ‎n = codeW t s‎ (`Exhaust.codeW`). -/
def nOf (ss : List Syl) : Option (Nat × Nat) :=
  ss.getLast?.map fun s => (ss.length, codeW ss.dropLast s)

/-- جدولُ الأوزان: (رقمُ القالب، الدرجة، n). -/
def waznRows : List (Nat × Nat × Nat) :=
  indexed.filterMap fun p => ((rowOf p).bind nOf).map fun dn => (p.1, dn.1, dn.2)

/-- **كلُّ وزنٍ بدرجته وعدده**: الماضي المجرّدُ والمبنيُّ للمجهول درجةُ 3 أو 4، والأمرُ 2 أو 3. -/
theorem wazn_rows : waznRows =
    [(0, 3, 0), (1, 3, 0), (2, 3, 0), (3, 3, 24), (4, 3, 12), (5, 3, 24), (6, 4, 24), (7, 4, 12),
     (8, 4, 96), (9, 4, 96), (10, 4, 120), (11, 3, 0), (12, 3, 24), (13, 3, 12), (14, 3, 24),
     (15, 4, 24), (16, 4, 12), (17, 4, 96), (18, 4, 96), (19, 4, 120), (20, 2, 8), (21, 2, 8),
     (22, 2, 8), (23, 2, 8), (24, 2, 5), (25, 2, 8), (26, 3, 8), (27, 3, 5), (28, 3, 26),
     (29, 3, 26), (30, 3, 32)] := by
  decide +kernel

theorem rows_check :
    indexed.all (fun p => (rowOf p).isSome && !isFarq (formOf p .continue) &&
      !(formOf p .continue).isEmpty) = true := by
  decide +kernel

/-- **كلُّ وزنٍ صفٌّ في جدول درجته** (`Exhaust.table`)، بالبرهان لا بالحساب وحدَه: ترخيصُه بقيد الحدّ
(`thulathi_licensed`) والجامعُ (`strict_mem_table`). -/
theorem wazn_row_mem (p : Nat × WaznC 3) (hp : p ∈ indexed) :
    ∃ ss, rowOf p = some ss ∧ ss ∈ table (ss.length - 1) := by
  have hc := List.all_eq_true.1 rows_check p hp
  simp only [Bool.and_eq_true, Bool.not_eq_true', List.isEmpty_eq_false_iff] at hc
  obtain ⟨⟨hs, hf⟩, hne⟩ := hc
  obtain ⟨ss, hss⟩ := Option.isSome_iff_exists.1 hs
  have hl := (thulathi_licensed p hp).1
  obtain ⟨ss', hp', _, hm⟩ := strict_mem_table (formOf p .continue) hne hf hl
  have hp2 := parse_of_sylF hss
  rw [hp2] at hp'
  simp only [Option.some.injEq, Prod.mk.injEq, true_and] at hp'
  subst hp'
  exact ⟨ss, hss, hm⟩

/-- الصفُّ مشتقٌّ إن كان صفَّ وزنٍ مبرهَن — قرارٌ محسوبٌ لكلّ n. -/
def mushtaq (ss : List Syl) : Bool := indexed.any fun p => rowOf p == some ss

/-! ## الحقولُ الثلاثة -/

/-- الاشتقاقُ في الدرجة d. -/
def IshtiqaqAt (d : Nat) : Prop :=
  (∀ p ∈ indexed, ∀ ss, rowOf p = some ss → ss.length = d → ss ∈ table (d - 1) ∧ mushtaq ss = true) ∧
  (∀ p ∈ indexed, ∀ r : Root 3, Sound r →
    kindOf (realize p.2 r .start .continue (lastH p.1)) = kindOf (formOf p .continue)) ∧
  (∀ p ∈ indexed, ∀ (r r' : Root 3) (en : Entry) (ex : Exit) (h : Haraka),
    realize p.2 r en ex h = realize p.2 r' en ex h → waslH p.2 r = waslH p.2 r' →
      r p.2.last = r' p.2.last ∧ ∀ i h', CSym.slot i h' ∈ p.2.body → r i = r' i)

theorem ishtiqaqAt (d : Nat) : IshtiqaqAt d := by
  refine ⟨?_, ?_, ?_⟩
  · intro p hp ss hs hd
    obtain ⟨ss', hs', hm⟩ := wazn_row_mem p hp
    rw [hs] at hs'
    simp only [Option.some.injEq] at hs'
    subst hs'
    refine ⟨hd ▸ hm, ?_⟩
    exact List.any_eq_true.2 ⟨p, hp, by simp [hs]⟩
  · intro p _ r hr
    exact syllables_fixed_by_wazn p.2 hr ktb_sound .start .continue (lastH p.1)
  · intro p _ r r' en ex h e hw
    exact realize_determines_root p.2 r r' en ex h e hw

/-- الصرفُ في الدرجة d: مرخَّصٌ وصلًا ووقفًا، وآخرُه مبنيٌّ بقالبه. -/
def SarfAt (d : Nat) : Prop :=
  ∀ p ∈ indexed, ∀ ss, rowOf p = some ss → ss.length = d →
    strictB (formOf p .continue) = true ∧ strictPauseB (formOf p .pause) = true ∧
      (formOf p .continue).getLast? = some ⟨ktb p.2.last, lastH p.1⟩

theorem sarfAt (d : Nat) : SarfAt d := by
  intro p hp _ _ _
  obtain ⟨h1, h2⟩ := thulathi_licensed p hp
  refine ⟨h1, h2, ?_⟩
  simp [formOf, Wazn.realize]

/-- النحوُ في المفرد: موضعُ العلامة واحدٌ هو الأخير، والوقفُ يمحوها. -/
def MahallAt (_d : Nat) : Prop :=
  ∀ (n : Nat) (W : WaznC n) (r : Root n) (en : Entry) (h h' : Haraka),
    (∃ pre, realize W r en .continue h = pre ++ [⟨r W.last, h⟩] ∧
      realize W r en .continue h' = pre ++ [⟨r W.last, h'⟩]) ∧
    realize W r en .pause h = realize W r en .pause h'

theorem mahallAt (d : Nat) : MahallAt d := by
  intro n W r en h h'
  refine ⟨⟨(if W.wasl && en == .start then [⟨hamza, waslH W r⟩] else []) ++ fillC W.body r, ?_, ?_⟩, ?_⟩ <;>
    simp [Wazn.realize]

/-! ## الدفترُ المملوء والبوّابة -/

def filled (d : Nat) : Wazifa → Sanad
  | .tarmiz => .burhan (tarmizAt d)
  | .imla => .burhan (imlaAt d)
  | .sawt => .burhan (sawtAt d)
  | .ishtiqaq => .burhan (ishtiqaqAt d)
  | .sarf => .burhan (sarfAt d)
  | .nahw => .burhan (mahallAt d)
  | .dalala => .muallaq "DALALA_NEEDS_SEALED_WITNESS"

/-- القائمُ ستّةٌ من سبعة في كلّ درجة. -/
theorem filled_qaim_count (d : Nat) :
    (Wazifa.all.filter fun w => (filled d w).qaim).length = 6 := by
  simp [Wazifa.all, filled, Sanad.qaim]

/-- والناقصُ الدلالةُ وحدَها. -/
theorem filled_missing_only_dalala (d : Nat) (w : Wazifa) :
    (filled d w).qaim = false ↔ w = .dalala := by
  cases w <;> simp [filled, Sanad.qaim]

/-- **بقانون الاستنفاد: الدفترُ المملوء يقف عند الدرجة الأولى أيضًا** — بالدلالة. -/
theorem filled_stops_at_one : ∀ k, ¬ Murakhkhas filled (k + 2) :=
  fun k => no_skip filled (k + 1) 1 (Nat.le_refl _) (by omega)
    (fun h => by have := h .dalala; simp [filled, Sanad.qaim] at this)

/-- **الدلالةُ وحدَها المانع**: أيُّ سندٍ قائمٍ لها في كلّ درجةٍ يفتح الدرجاتِ كلَّها. -/
theorem dalala_alone_blocks (s : Nat → Sanad) (hs : ∀ d, (s d).qaim = true) :
    ∀ k, Murakhkhas (fun d w => if w = .dalala then s d else filled d w) (k + 1) :=
  fun k => gate_of_exhausted _ k fun j _ _ w => by
    by_cases hw : w = .dalala
    · simp [hw, hs]
    · simp only [hw, ite_false]
      cases w <;> simp_all [filled, Sanad.qaim]

/-! ## الأصولُ ثلاثٌ أو أربع، تُقرأ بتوافيق n المقاطع -/

/-- دَحْرَجَ (فَعْلَلَ، أربعةُ أصول) وكَتَّبَ (فَعَّلَ، ثلاثة): صفٌّ واحد CVC CV CV بعددٍ واحد (3، 24). -/
theorem four_and_three_share_n :
    (syllables (realize fa'lala dhrj .start .continue .fatha)).bind nOf = some (3, 24) ∧
    (3, 3, 24) ∈ waznRows := by
  decide +kernel

end A116.Ledger
