import A116.Ledger

/-!
# الدرجةُ بعدد الأصول: جدولُ الثلاثيّ مستنفَدًا مرقَّمًا، ولا رباعيَّ قبله، ولا درجةَ أصولٍ بعده

قرارُ المالك (2026-10-12): «قراري عددُ الأصول ٣ أو ٤ الحروف». فالدرجةُ هنا **عددُ الحروف الأصول** لا عددُ المقاطع
(`Wazn.root_degree_is_not_syllable_degree` يفرّق بينهما)، وقانونُه: لا يُرخَّص الرباعيُّ إلّا بعد استنفاد الثلاثيّ —
جدولًا تامًّا مرقَّمًا ووظائفَ مستوفاة — وبالرباعيّ يُغلق الجبر وما سواه زوائد («حتى يستنفد 116 في الرباعيّ يكون تمّ
إغلاقُ الجبر ويكون ما عدا ذلك زوائد»).

## الأصول

الأصلُ حاملٌ من الـ29 إلّا الألف: الألفُ لا تكون إلّا ساكنة (`Alif`) وهي المحايد (`Neutral`) — لا تحمل حالةَ أصل. فالأصولُ
ثمانيةٌ وعشرون، والأصلُ رقمٌ ‎d < 28‎ وحاملُه ‎d + 1‎ (`toCarrier`؛ الألفُ الحاملُ 0: `alif_val`)، تقابلًا مع ما ليس ألفًا
(`toCarrier_injective`، `toCarrier_ne_alif`، `toCarrier_onto`).

## ما يُبرهَن

* `mem_table`، `table_length`: جدولُ الدرجة n (`table n`) هو **كلُّ** جذرٍ من n أصلًا لا غيرُه، وعددُه ‎28^n‎.
* `num_lt`، `num_inj`، `num_unnum`: لكلّ جذرٍ في درجته عددٌ في ‎[0, 28^n)‎ لا يشترك فيه اثنان ولا يفوته عدد — «n جديدة»
  لكلّ جذر، والعددُ الجديدُ من السابق: ‎num (d :: t) = d + 28·num t‎.
* `RootMurakhkhas`، `quad_needs_tri`، `quad_of_exhausted`، `only_tri_and_quad`: **البوّابة بعدد الأصول** — الثلاثيُّ مدخل،
  والرباعيُّ لا يُرخَّص إلّا باستنفاد جدول الثلاثيّ واستيفاء وظائفه السبع (`Exhaust.Mustawfa`)، ولا درجةَ أصولٍ غيرهما.
* `sinf`، `khumasi_jamid`، `usul_three_four_five`، `murakhkhas_mutasarrif`، `jamid_not_murakhkhas`: **الخماسيُّ جامد**
  (قرارُ المالك وشاهدُ الكتاب): الأصولُ ثلاثةٌ أو أربعةٌ أو خمسة، والخمسةُ لا فعلَ لها ولا مصدر، فلا تفتحها البوّابة.
* `rootLedger_quad_waits`، `root_dalala_alone_opens`: **الدفترُ بعدد الأصول** — الترميزُ (ترقيمُ الجذور) والإملاءُ
  والصوت، والاشتقاقُ والصرفُ والنحوُ على الأوزان الثلاثيّة كلِّها (`Ledger.ishtiqaqAt`، `sarfAt`، `mahallAt` لكلّ
  درجة مقاطع) برهانٌ يحمل حدَّه؛ والدلالةُ وحدَها معلَّقة، فالرباعيُّ ينتظرها وحدَها، وأيُّ سندٍ قائمٍ لها يفتحه.
* `tri_witness_all`، `cells_exhausted_within_thulathi`: **استنفادُ الـ116 داخل الثلاثيّ** — كلُّ خانةٍ من الـ113 المرخَّصة
  تقع في صيغةٍ من وزنٍ ثلاثيٍّ (`Wazn.thulathi`) على جذرٍ ثلاثيٍّ بلا ألف، مرخَّصةٍ بقيد الحدّ ابتداءً وصلًا (`strictB`).

## ما ليس هنا — باسمه

* حدُّ الاشتقاق والصرف في الدفتر حدُّ `Ledger`: القوالبُ الثلاثيّةُ الصحيحة؛ والمعتلُّ داخلٌ في `Tasrif` للماضي المجرّد
  والمضارع والأمر على كلّ جذر، وفي المزيد (غير أَفْعَلَ) على الجذور المرجعيّة وحدَها (`Neutral.weak_licensed`).
* أوزانُ الرباعيّ وفتحُ بوّابته بشاهد المقاييس: في `Rubai` (ADR ٢٨)؛ والدفترُ هنا يبقى معلَّقَ الدلالة بلا شاهد.
-/

namespace A116.RootGrade

open A116 A116.Wazn A116.Ladder A116.Exhaust

/-! ## ١. الأصول: الحواملُ إلّا الألف -/

/-- الألف. -/
def alif : Fin carrierCount := carrierOf 'ا'

theorem alif_val : alif.val = 0 := by decide

/-- حاملُ الأصل d: الحواملُ بترتيبها بعد الألف. -/
def toCarrier (d : Fin 28) : Fin carrierCount := ⟨d.val + 1, by unfold carrierCount; omega⟩

theorem toCarrier_injective {a b : Fin 28} (h : toCarrier a = toCarrier b) : a = b := by
  apply Fin.ext
  have := congrArg Fin.val h
  simp only [toCarrier] at this
  omega

theorem toCarrier_ne_alif (d : Fin 28) : toCarrier d ≠ alif := by
  intro h
  have := congrArg Fin.val h
  rw [alif_val] at this
  simp [toCarrier] at this

theorem toCarrier_onto (c : Fin carrierCount) (h : c ≠ alif) : ∃ d, toCarrier d = c := by
  have h0 : c.val ≠ 0 := fun e => h (Fin.ext (by rw [e, alif_val]))
  have hc := c.isLt
  unfold carrierCount at hc
  refine ⟨⟨c.val - 1, by omega⟩, Fin.ext ?_⟩
  simp only [toCarrier]
  omega

/-! ## ٢. جدولُ الدرجة n: كلُّ الجذور -/

/-- جدولُ الجذور من n أصلًا. -/
def table : Nat → List (List (Fin 28))
  | 0 => [[]]
  | k + 1 => (List.finRange 28).flatMap fun d => (table k).map (d :: ·)

/-- **جامعٌ مانع:** ما في جدول الدرجة n هو كلُّ جذرٍ من n أصلًا، لا غير. -/
theorem mem_table : ∀ (k : Nat) (r : List (Fin 28)), r ∈ table k ↔ r.length = k
  | 0, r => by cases r <;> simp [table]
  | k + 1, r => by
    cases r with
    | nil => simp [table]
    | cons d t =>
      simp only [table, List.mem_flatMap, List.mem_map, List.length_cons]
      constructor
      · rintro ⟨d', _, t', ht', h⟩
        simp only [List.cons.injEq] at h
        obtain ⟨rfl, rfl⟩ := h
        simp [(mem_table k _).1 ht']
      · intro h
        exact ⟨d, List.mem_finRange d, t, (mem_table k t).2 (by omega), rfl⟩

private theorem length_flatMap_const {α β : Type} (l : List α) (f : α → List β) (m : Nat)
    (h : ∀ a, (f a).length = m) : (l.flatMap f).length = l.length * m := by
  induction l with
  | nil => simp
  | cons a t ih => simp [List.flatMap_cons, ih, h, Nat.succ_mul, Nat.add_comm]

/-- عددُ جذور الدرجة n: ‎28^n‎. -/
theorem table_length : ∀ k : Nat, (table k).length = 28 ^ k
  | 0 => rfl
  | k + 1 => by
    rw [table, length_flatMap_const _ _ (28 ^ k) (fun _ => by simp [table_length k])]
    simp [Nat.pow_succ, Nat.mul_comm]

/-! ## ٣. لكلّ جذرٍ عددٌ جديدٌ وحيد -/

/-- عددُ الجذر: الأصلُ الأوّلُ منزلةُ الآحاد بأساس ثمانيةٍ وعشرين. -/
def num : List (Fin 28) → Nat
  | [] => 0
  | d :: t => d.val + 28 * num t

/-- الجذرُ من عدده بدرجةٍ معلومة. -/
def unnum : Nat → Nat → List (Fin 28)
  | 0, _ => []
  | k + 1, n => ⟨n % 28, Nat.mod_lt _ (by decide)⟩ :: unnum k (n / 28)

theorem num_lt : ∀ r : List (Fin 28), num r < 28 ^ r.length
  | [] => by simp [num]
  | d :: t => by
    have h1 := d.isLt
    have h2 := num_lt t
    simp only [num, List.length_cons, Nat.pow_succ]
    omega

/-- **لا يشترك جذران من درجةٍ واحدةٍ في عدد.** -/
theorem num_inj : ∀ r s : List (Fin 28), r.length = s.length → num r = num s → r = s
  | [], [], _, _ => rfl
  | [], _ :: _, h, _ => by simp at h
  | _ :: _, [], h, _ => by simp at h
  | d :: t, d' :: t', hl, hn => by
    simp only [num] at hn
    have h1 := d.isLt
    have h2 := d'.isLt
    have hd : d = d' := Fin.ext (by omega)
    have ht : num t = num t' := by omega
    rw [hd, num_inj t t' (by simpa using hl) ht]

theorem unnum_length : ∀ k n : Nat, (unnum k n).length = k
  | 0, _ => rfl
  | k + 1, n => by simp [unnum, unnum_length k]

/-- **لا يفوته عدد:** كلُّ عددٍ دون ‎28^n‎ عددُ جذرٍ من n أصلًا. -/
theorem num_unnum : ∀ k n : Nat, n < 28 ^ k → num (unnum k n) = n
  | 0, n, h => by simp [unnum, num] at *; omega
  | k + 1, n, h => by
    have hk : n / 28 < 28 ^ k := by rw [Nat.pow_succ] at h; omega
    simp only [unnum, num]
    rw [num_unnum k (n / 28) hk]
    omega

/-! ## ٤. البوّابةُ بعدد الأصول -/

/-- استنفادُ جدول الدرجة n: كلُّ جذرٍ من n أصلًا فيه. -/
def TableExhausted (n : Nat) : Prop := ∀ r : List (Fin 28), r.length = n → r ∈ table n

theorem tableExhausted (n : Nat) : TableExhausted n := fun r h => (mem_table n r).2 h

/-- الترخيصُ بعدد الأصول: الثلاثيُّ مدخل، والرباعيُّ باستنفاد جدول الثلاثيّ واستيفاء وظائفه، ولا غيرُهما. -/
def RootMurakhkhas (L : Nat → Wazifa → Sanad) : Nat → Prop
  | 3 => True
  | 4 => TableExhausted 3 ∧ Mustawfa (L 3)
  | _ => False

/-- **لا رباعيَّ قبل استنفاد الثلاثيّ.** -/
theorem quad_needs_tri (L : Nat → Wazifa → Sanad) (h : RootMurakhkhas L 4) :
    TableExhausted 3 ∧ Mustawfa (L 3) := h

/-- والاستنفادُ متحقّقٌ جدولًا، فاستيفاءُ وظائف الثلاثيّ كافٍ لترخيص الرباعيّ. -/
theorem quad_of_exhausted (L : Nat → Wazifa → Sanad) (h : Mustawfa (L 3)) : RootMurakhkhas L 4 :=
  ⟨tableExhausted 3, h⟩

/-- **بالرباعيّ يُغلق الجبر:** لا درجةَ أصولٍ مرخَّصةً إلّا الثلاثيّ والرباعيّ. تُصاغ عضويّةً في القائمة
`[3, 4]` لا ‎`n = 3 ∨ n = 4`‎: هي فصلٌ بين درجتين لا عددٌ يُعَدّ، فلا تدخل سجلَّ الأعداد (`gen_claims`، ADR ١٢). -/
theorem only_tri_and_quad (L : Nat → Wazifa → Sanad) (n : Nat) (h : RootMurakhkhas L n) :
    n ∈ [3, 4] := by
  match n, h with
  | 3, _ => exact .head _
  | 4, _ => exact .tail _ (.head _)

/-! ## ٣ب. الخماسيُّ جامد: لا فعلَ له ولا مصدر

قرارُ المالك (2026-10-12): «الخماسيُّ جامدٌ لا فعلَ له ولا مصدر». وشاهدُه في الكتاب المختوم (SLGE
`tests/data/openiti-sibawayh-kitab.txt.gz`، السطر 18476–18479): «ثمّ بناتُ الخمسة وهي أقلّ، لا تكون في الفعل البتّة…
فالكلامُ على ثلاثة أحرفٍ وأربعة أحرفٍ وخمسةٍ لا زيادةَ فيها ولا نقصان». فعددُ الأصول ثلاثةٌ أو أربعةٌ أو خمسة،
والخمسةُ وحدَها جامدة. -/

/-- صنفُ عدد الأصول: متصرِّفٌ (فعلٌ ومصدرٌ واشتقاق)، أو جامد (اسمٌ لا فعلَ له ولا مصدر)، أو ليس عددَ أصول. -/
inductive Sinf where
  | mutasarrif
  | jamid
  | laysaAsl
  deriving DecidableEq, Repr

def sinf : Nat → Sinf
  | 3 | 4 => .mutasarrif
  | 5 => .jamid
  | _ => .laysaAsl

/-- له فعلٌ ومصدر. -/
def hasFil (n : Nat) : Bool := sinf n == .mutasarrif

/-- **الخماسيُّ جامد**: لا فعلَ له ولا مصدر. -/
theorem khumasi_jamid : sinf 5 = .jamid ∧ hasFil 5 = false := ⟨rfl, rfl⟩

/-- **الأصولُ ثلاثةٌ أو أربعةٌ أو خمسة**، لا غيرُها. -/
theorem usul_three_four_five (n : Nat) : sinf n ≠ .laysaAsl ↔ n ∈ [3, 4, 5] := by
  constructor
  · intro h
    match n, h with
    | 3, _ => exact .head _
    | 4, _ => exact .tail _ (.head _)
    | 5, _ => exact .tail _ (.tail _ (.head _))
    | 0, h => exact absurd rfl h
    | 1, h => exact absurd rfl h
    | 2, h => exact absurd rfl h
    | _ + 6, h => exact absurd rfl h
  · intro h
    simp only [List.mem_cons, List.not_mem_nil, or_false] at h
    rcases h with rfl | rfl | rfl <;> decide

/-- **المرخَّصُ بالبوّابة متصرِّفٌ**، والجامدُ لا تفتحه البوّابة: الخماسيُّ خارجَ الاشتقاق لا معلَّقًا عليه. -/
theorem murakhkhas_mutasarrif (L : Nat → Wazifa → Sanad) (n : Nat) (h : RootMurakhkhas L n) :
    sinf n = .mutasarrif := by
  have := only_tri_and_quad L n h
  simp only [List.mem_cons, List.not_mem_nil, or_false] at this
  rcases this with rfl | rfl <;> rfl

theorem jamid_not_murakhkhas (L : Nat → Wazifa → Sanad) (n : Nat) (h : sinf n = .jamid) :
    ¬ RootMurakhkhas L n := by
  intro hm
  have := murakhkhas_mutasarrif L n hm
  rw [h] at this
  exact absurd this (by decide)

/-- الدفترُ الحاليّ بعدد الأصول. -/
def rootLedger (n : Nat) : Wazifa → Sanad
  | .tarmiz => .burhan (num_unnum n)
  | .imla => .burhan (imlaAt n)
  | .sawt => .burhan (sawtAt n)
  | .ishtiqaq => .burhan (fun d => Ledger.ishtiqaqAt d)
  | .sarf => .burhan (fun d => Ledger.sarfAt d)
  | .nahw => .burhan (fun d => Ledger.mahallAt d)
  | .dalala => .muallaq "DALALA_NEEDS_SEALED_WITNESS"

/-- **الرباعيُّ ينتظر:** الدلالةُ في الثلاثيّ معلَّقة، فلا يُرخَّص الرباعيّ. -/
theorem rootLedger_quad_waits : ¬ RootMurakhkhas rootLedger 4 := by
  intro h
  have := h.2 .dalala
  simp [rootLedger, Sanad.qaim] at this

/-- **الدلالةُ وحدَها المانع:** أيُّ سندٍ قائمٍ لها في الثلاثيّ يرخّص الرباعيّ. -/
theorem root_dalala_alone_opens (s : Sanad) (hs : s.qaim = true) :
    RootMurakhkhas (fun n w => if w = .dalala then s else rootLedger n w) 4 := by
  refine quad_of_exhausted _ fun w => ?_
  by_cases hw : w = .dalala
  · simp [hw, hs]
  · simp only [hw, ite_false]
    cases w <;> simp_all [rootLedger, Sanad.qaim]

/-! ## ٥. استنفادُ الـ116 داخل الثلاثيّ -/

/-- جذرٌ ثلاثيٌّ: ك ت ب وفي الموضع i الحاملُ c. -/
def subst (c : Fin carrierCount) (i : Fin 3) : Root 3 := fun j => if j = i then c else ktb j

/-- الجذورُ المرشَّحةُ شاهدًا للخانة: ك ت ب، وحاملُ الخانة في كلّ موضعٍ إن لم يكن ألفًا. -/
def candidates (c : Cell) : List (Root 3) :=
  ktb :: (if c.carrier = alif then [] else [subst c.carrier 0, subst c.carrier 1, subst c.carrier 2])

/-- الأوزانُ الثلاثيّةُ بأرقامها. -/
def indexedThulathi : List (Nat × WaznC 3) := (List.range thulathi.length).zip thulathi

/-- للخانة شاهدٌ: صيغةٌ من وزنٍ ثلاثيٍّ على جذرٍ بلا ألف، فيها الخانة، مرخَّصةٌ وصلًا. -/
def triWitness (c : Cell) : Bool :=
  indexedThulathi.any fun (i, W) =>
    (candidates c).any fun r =>
      (List.finRange 3).all (fun j => r j != alif) &&
        (realize W r .start .continue (lastH i)).contains c &&
        contCheck (realize W r .start .continue (lastH i))

theorem tri_witness_all : Alif.licensable.all triWitness = true := by decide +kernel

/-- **استنفادُ الـ116 داخل الثلاثيّ:** كلُّ خانةٍ مرخَّصةٍ تقع في صيغةٍ مرخَّصةٍ من وزنٍ ثلاثيٍّ على جذرٍ ثلاثيٍّ بلا ألف. -/
theorem cells_exhausted_within_thulathi (c : Cell) (hc : c ∈ Alif.licensable) :
    ∃ i W, (i, W) ∈ indexedThulathi ∧ ∃ r : Root 3, (∀ j, r j ≠ alif) ∧
      c ∈ realize W r .start .continue (lastH i) ∧
      Hadd.strictB (realize W r .start .continue (lastH i)) = true := by
  have h := List.all_eq_true.1 tri_witness_all c hc
  simp only [triWitness, List.any_eq_true, Bool.and_eq_true, List.all_eq_true, bne_iff_ne,
    ne_eq, List.contains_iff_mem] at h
  obtain ⟨⟨i, W⟩, hp, r, _, ⟨⟨hna, hmem⟩, hchk⟩⟩ := h
  exact ⟨i, W, hp, r, fun j => hna j (List.mem_finRange j), hmem, strictB_of_check hchk⟩

end A116.RootGrade
