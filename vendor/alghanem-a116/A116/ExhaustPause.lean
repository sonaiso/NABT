import A116.Exhaust
import A116.Boundary

/-!
# جدولُ الوقف بقيد الحدّ: الجامعُ المانع لكلّ درجة (ADR ١٨)

نظيرُ جدول الوصل في `A116.Exhaust` (ADR ١٥) على قانون الوقف (`Hadd.strictPauseB`). الدرجةُ d وقفًا: ‎d − 1‎
مقطعًا داخليًّا من {CV، CVV، CVC، CVVC} ثمّ **طرفيٌّ من الستّة** — فالوقفُ يزيد على الوصل ثلاثةَ أطراف: CVVC (المدُّ
العارض للسكون: الرَّحِيمْ)، وCVCC (بَحْرْ)، وCVVCC (تَامّْ). والمدُّ قبل مُغلِقٍ داخلَ الكلمة مدغمٌ وقفًا كما هو وصلًا
(`Hadd.geminatePauseB_vc_carrier`)، فالداخليّةُ هي الداخليّةُ نفسُها.

## المبرهنات (لكلّ درجة)

* `mem_pauseTable` و`pauseTable_nodup` و`pauseTable_length`: الصفُّ k داخليّة ثمّ طرفيّ، بلا تكرار، وعددُه ‎6·4^k‎؛
  والعدد ‎N(t, u) = 6·I(t) + d(u)‎ والداخليُّ من السابق ‎I(t ++ [s]) = 4·I(t) + d(s)‎ (`codeP_snoc`).
* `strict_pause_mem_table` — **الجامع**: كلُّ كلمةٍ من خاناتٍ مرخَّصةٍ بقيد الحدّ وقفًا صفٌّ في جدول درجتها، لكلّ طول
  (ومدُّ الفرق داخلٌ فيه وقفًا).
* `pause_table_realized` — **المانع**: كلُّ صفٍّ تحقّقه كلمةٌ مرخَّصةٌ بقيد الحدّ وقفًا إسقاطُها الصفُّ بعينه — بالشاهد
  الموحَّد نفسِه (`Exhaust.realize`: كلُّ مقطعٍ يبدأ بـ«بَ» والمُغلِقُ بعد المدّ «بْ» يليه مثلُه).
* `pauseTable_iff_licensed` — الجامعُ المانع معًا.
* `table_sub_pauseTable`، `pause_adds`: كلُّ صفٍّ وصلًا صفٌّ وقفًا (قانونُ الوصل يستلزم قانونَ الوقف)، والزيادةُ ‎3·4^k‎
  صفًّا هي الأطرافُ الثلاثةُ وحدَها.

## قانونُ «ا و ا و ا» (تعريفُ المالك: الابتداءُ والوصلُ والوقف)

* `awa`: الابتداءُ ألّا تبدأ الكلمةُ بساكن، والوصلُ `strictB`، والوقفُ `strictPauseB` — تعريف.
* `awa_wasl_waqf`، `awa_waqf_ibtida`، `awa_chain`: الوصلُ ⇒ الوقفُ ⇒ الابتداء — مبرهن.
-/

namespace A116.ExhaustPause

open A116.Stages A116.Ternary A116.Hadd A116.Exhaust

/-- رمزُ المقطع الطرفيّ وقفًا (الستّة). -/
def dP : Syl → Nat
  | .CV => 0 | .CVV => 1 | .CVC => 2 | .CVVC => 3 | .CVCC => 4 | .CVVCC => 5

def ofDP : Nat → Syl
  | 0 => .CV | 1 => .CVV | 2 => .CVC | 3 => .CVVC | 4 => .CVCC | _ => .CVVCC

/-- الرمزُ يردّ المقطع. -/
theorem ofDP_dP (s : Syl) : ofDP (dP s) = s := by cases s <;> rfl

/-- الرمزُ دون الستّة. -/
theorem dP_lt (s : Syl) : dP s < 6 := by cases s <;> decide

/-- المقطعُ يردّ الرمز. -/
theorem dP_ofDP {m : Nat} (h : m < 6) : dP (ofDP m) = m := by
  match m, h with
  | 0, _ | 1, _ | 2, _ | 3, _ | 4, _ | 5, _ => rfl

/-- الطرفُ وقفًا ودونه وصلًا: رمزا الطرف وصلًا ووقفًا واحدٌ على الثلاثة المشتركة. -/
theorem dP_eq_dC {s : Syl} (h : final s = true) : dP s = dC s := by
  cases s <;> simp_all [final, inner, pauseOnly, dP, dC]

def decodeP (k n : Nat) : List Syl := decodeI k (n / 6) ++ [ofDP (n % 6)]

/-- عددُ صفّ الوقف. -/
def codeP (t : List Syl) (s : Syl) : Nat := 6 * codeI t + dP s

/-- جدولُ الكلمة وقفًا بالدرجة k+1: k داخليّة ثمّ طرفيٌّ من الستّة. -/
def pauseTable (k : Nat) : List (List Syl) := (List.range (6 * 4 ^ k)).map (decodeP k)

/-- عددُ جدول الوقف ‎6·4^k‎. -/
theorem pauseTable_length (k : Nat) : (pauseTable k).length = 6 * 4 ^ k := by simp [pauseTable]

/-- صفٌّ في جدول الوقف بالدرجة k+1. -/
def PauseRow (k : Nat) (ss : List Syl) : Prop :=
  ∃ t s, ss = t ++ [s] ∧ t.length = k ∧ ∀ x ∈ t, inner x = true

/-- **التمام:** الصفُّ في الجدول ⟺ k داخليّة ثمّ طرفيّ. -/
theorem mem_pauseTable (k : Nat) (ss : List Syl) : ss ∈ pauseTable k ↔ PauseRow k ss := by
  simp only [pauseTable, List.mem_map, List.mem_range, decodeP]
  constructor
  · rintro ⟨n, _, rfl⟩
    exact ⟨_, _, rfl, decodeI_length k _, decodeI_inner k _⟩
  · rintro ⟨t, s, rfl, hl, hi⟩
    have hct := codeI_lt t hi
    rw [hl] at hct
    have hs := dP_lt s
    refine ⟨codeP t s, ?_, ?_⟩
    · simp only [codeP]; omega
    · have e1 : codeP t s / 6 = codeI t := by simp only [codeP]; omega
      have e2 : codeP t s % 6 = dP s := by simp only [codeP]; omega
      rw [e1, e2, ofDP_dP]
      have := decodeI_codeI t hi
      rw [hl] at this
      rw [this]

/-- **لا تكرار:** لكلّ صفٍّ عددٌ واحد. -/
theorem pauseTable_nodup (k : Nat) : (pauseTable k).Nodup := by
  refine nodup_map_on _ _ ?_ List.nodup_range
  intro x hx y hy e
  simp only [List.mem_range] at hx hy
  simp only [decodeP] at e
  have hl : (decodeI k (x / 6)).length = (decodeI k (y / 6)).length := by
    simp [decodeI_length]
  obtain ⟨e1, e2⟩ := List.append_inj e hl
  simp only [List.cons.injEq, and_true] at e2
  have hx' : x / 6 < 4 ^ k := by omega
  have hy' : y / 6 < 4 ^ k := by omega
  have q := congrArg codeI e1
  rw [codeI_decodeI k _ hx', codeI_decodeI k _ hy'] at q
  have r := congrArg dP e2
  rw [dP_ofDP (by omega), dP_ofDP (by omega)] at r
  omega

/-- **الجديدُ من السابق:** عددُ صفّ الوقف بالدرجة k+2 من عدد صفّه الداخليّ بالدرجة k+1. -/
theorem codeP_snoc (t : List Syl) (s u : Syl) :
    codeP (t ++ [s]) u = 6 * (4 * codeI t + dC s) + dP u := by
  simp [codeP, codeI_snoc]

/-- الأعدادُ بالحساب للدرجات 1..4 وقفًا. -/
theorem pause_table_counts :
    (List.range 4).map (fun k => (pauseTable k).length) = [6, 24, 96, 384] := by
  simp only [pauseTable_length]; decide

/-! ## الجامع: كلُّ مرخَّصٍ وقفًا صفٌّ في جدوله -/

/-- **الجامع:** كلُّ كلمةٍ من خاناتٍ مرخَّصةٍ بقيد الحدّ وقفًا صفٌّ في جدول درجتها — لكلّ طول. -/
theorem strict_pause_mem_table (w : List Cell) (hw : w ≠ []) (h : strictPauseB w = true) :
    ∃ ss, parse (kindOf w) = some (.none, ss) ∧ ss ≠ [] ∧ ss ∈ pauseTable (ss.length - 1) := by
  simp only [strictPauseB, Bool.and_eq_true] at h
  obtain ⟨ss, hp, hn⟩ := (pauseB_iff _).1 h.1
  have hk : kindOf w ≠ [] := by
    intro e
    have := kindGo_length none w
    simp only [kindOf] at e
    rw [e] at this
    exact hw (List.eq_nil_of_length_eq_zero this.symm)
  have hne := parse_ne_nil_of_ne hk hp
  refine ⟨ss, hp, hne, ?_⟩
  obtain ⟨t, s, rfl⟩ := Grade.exists_concat ss hne
  rw [mem_pauseTable]
  refine ⟨t, s, rfl, by simp, fun x hx => ?_⟩
  have := hn x (by simp [hx])
  simp [inner, this]

/-! ## المانع: كلُّ صفٍّ تحقّقه كلمةٌ مرخَّصةٌ وقفًا -/

/-- المقطعُ وحدَه طرفًا مدغمٌ وقفًا. -/
theorem geminatePause_last (s : Syl) : geminatePauseB (s.atoms.zip (block s)) = true := by
  cases s <;> decide

/-- مقطعٌ داخليٌّ قبل ما يبدأ بـ«بَ» لا يغيّر الإدغامَ وقفًا. -/
theorem geminatePause_block (s : Syl) (hs : inner s = true) (rest : List (Stages.K × Cell))
    (r : List (Stages.K × Cell)) (hr : rest = (Stages.K.cv, bv) :: r) :
    geminatePauseB (s.atoms.zip (block s) ++ rest) = geminatePauseB rest := by
  subst hr
  cases s <;> simp_all [inner, pauseOnly, block, Syl.atoms, Syl.coda, geminatePauseB, stepOKPause,
    stepOK, bv, Ladder.atom]

theorem pairsOf_snoc_starts (t : List Syl) (s : Syl) :
    ∃ r, pairsOf (t ++ [s]) = (Stages.K.cv, bv) :: r := by
  rcases pairsOf_starts (t ++ [s]) with h | h
  · exfalso
    have : pairsOf (t ++ [s]) = pairsOf t ++ s.atoms.zip (block s) := by simp [pairsOf]
    rw [this] at h
    cases s <;> simp [Syl.atoms, block] at h
  · exact h

/-- الإدغامُ وقفًا على الشاهد الموحَّد: داخليّةٌ ثمّ أيُّ طرف. -/
theorem geminatePause_realize : ∀ (t : List Syl) (s : Syl), (∀ x ∈ t, inner x = true) →
    geminatePauseB (pairsOf (t ++ [s])) = true
  | [], s, _ => by simpa [pairsOf] using geminatePause_last s
  | x :: t, s, hi => by
    have e : pairsOf (x :: t ++ [s]) = x.atoms.zip (block x) ++ pairsOf (t ++ [s]) := by
      simp [pairsOf]
    obtain ⟨r, hr⟩ := pairsOf_snoc_starts t s
    rw [e, geminatePause_block x (hi x List.mem_cons_self) _ r hr]
    exact geminatePause_realize t s (fun y hy => hi y (List.mem_cons_of_mem _ hy))

/-- **المانع:** كلُّ صفٍّ في جدول الوقف تحقّقه كلمةٌ مرخَّصةٌ بقيد الحدّ وقفًا إسقاطُها الصفُّ بعينه. -/
theorem pause_table_realized (k : Nat) (ss : List Syl) (h : ss ∈ pauseTable k) :
    strictPauseB (realize ss) = true ∧ kindOf (realize ss) = flat .none ss := by
  obtain ⟨t, s, rfl, _, hi⟩ := (mem_pauseTable k _).1 h
  refine ⟨?_, kindOf_realize _⟩
  simp only [strictPauseB, Bool.and_eq_true]
  refine ⟨?_, ?_⟩
  · rw [kindOf_realize]
    unfold pauseB
    rw [parse_flat]
    simp only [List.dropLast_concat, List.all_eq_true, Bool.not_eq_true']
    intro x hx
    have := hi x hx
    simpa [inner] using this
  · simp only [haddPauseB, isFarq_realize, Bool.false_eq_true, ↓reduceIte, kindOf_realize,
      zip_realize]
    exact geminatePause_realize t s hi

/-- **الجامعُ المانع لكلّ درجة (الوقف):** الصفُّ في جدول الوقف بالدرجة k+1 ⟺ تقطيعُ كلمةٍ من خاناتٍ، مرخَّصةٍ بقيد
الحدّ وقفًا، بطول k+1. -/
theorem pauseTable_iff_licensed (k : Nat) (ss : List Syl) :
    ss ∈ pauseTable k ↔ ∃ w : List Cell, w ≠ [] ∧ strictPauseB w = true ∧
      parse (kindOf w) = some (.none, ss) ∧ ss.length = k + 1 := by
  constructor
  · intro h
    obtain ⟨hs, hk⟩ := pause_table_realized k ss h
    obtain ⟨t, u, rfl, hl, _⟩ := (mem_pauseTable k _).1 h
    refine ⟨realize (t ++ [u]), ?_, hs, by rw [hk]; exact parse_flat _ _, by simp [hl]⟩
    intro e
    have := congrArg List.length (kindOf_realize (t ++ [u]))
    rw [e] at this
    simp [kindOf, kindGo, flat, Lead.atoms, Syl.atoms] at this
  · rintro ⟨w, hw, h, hp, hl⟩
    obtain ⟨ss', hp', _, hm⟩ := strict_pause_mem_table w hw h
    rw [hp] at hp'
    simp only [Option.some.injEq, Prod.mk.injEq, true_and] at hp'
    subst hp'
    rw [hl] at hm
    simpa using hm

/-! ## الوصلُ داخلَ الوقف -/

/-- **قانونُ الوصل يستلزم قانونَ الوقف:** كلُّ صفٍّ في جدول الوصل صفٌّ في جدول الوقف. -/
theorem table_sub_pauseTable (k : Nat) (ss : List Syl) (h : ss ∈ table k) : ss ∈ pauseTable k := by
  obtain ⟨t, s, rfl, hl, hi, _⟩ := (mem_table k ss).1 h
  exact (mem_pauseTable k _).2 ⟨t, s, rfl, hl, hi⟩

/-- **ما يزيده الوقف:** ‎6·4^k − 3·4^k = 3·4^k‎ صفًّا — الأطرافُ الثلاثة CVVC وCVCC وCVVCC. -/
theorem pause_adds (k : Nat) : (pauseTable k).length = (table k).length + 3 * 4 ^ k := by
  rw [pauseTable_length, table_length]; omega

/-! ## قانونُ «ا و ا و ا»: الابتداءُ والوصلُ والوقف (نصُّ المالك، 2026-10-12)

سمّى المالكُ قانونَ الحدّ الثلاثيّ «ا و ا و ا» ثمّ بيّنه: «المقصود قانون الابتداء وقانون الوصل وقانون الوقف». فهو هنا
تعريفٌ لا مبرهنة: الابتداءُ ألّا تبدأ الكلمةُ بساكن (`Boundary.initialSukun`)، والوصلُ `Hadd.strictB`، والوقفُ
`Hadd.strictPauseB`. والمبرهَن ترتيبُها: الوصلُ يستلزم الوقف، والوقفُ يستلزم الابتداء؛ وجدولُ الوصل داخلَ جدول الوقف. -/

/-- الحدودُ الثلاثة. -/
inductive AWA where
  | ibtida | wasl | waqf
  deriving DecidableEq, Repr

/-- ترخيصُ الكلمة بكلّ قانونٍ من الثلاثة. -/
def awa : AWA → List Cell → Bool
  | .ibtida, w => !Boundary.initialSukun w
  | .wasl, w => strictB w
  | .waqf, w => strictPauseB w

/-- **الوصلُ يستلزم الوقف.** -/
theorem awa_wasl_waqf {w : List Cell} (h : awa .wasl w = true) : awa .waqf w = true :=
  strictB_pause h

/-- كلُّ ما يُقطَّع بلا قطعةٍ صادرة يبدأ بمتحرّك. -/
theorem flat_head (ss : List Syl) : (flat .none ss).head? = none ∨ (flat .none ss).head? = some .cv := by
  cases ss with
  | nil => left; rfl
  | cons s t => right; cases s <;> rfl

/-- **الوقفُ يستلزم الابتداء:** ما رُخِّص وقفًا لا يبدأ بساكن. -/
theorem awa_waqf_ibtida {w : List Cell} (h : awa .waqf w = true) : awa .ibtida w = true := by
  simp only [awa, strictPauseB, Bool.and_eq_true] at h
  obtain ⟨ss, hp, _⟩ := (pauseB_iff _).1 h.1
  have hf := flat_parse hp
  cases w with
  | nil => rfl
  | cons x t =>
    have hk : (kindOf (x :: t)).head? = some (kindOne none x) := by
      simp [kindOf, kindGo]
    rw [← hf] at hk
    rcases flat_head ss with e | e <;> rw [e] at hk
    · simp at hk
    · simp only [Option.some.injEq] at hk
      simp only [awa, Boundary.initialSukun]
      cases hs : x.isSukun
      · rfl
      · exfalso
        have : x.haraka = .sukun := by
          have h2 : x.haraka.isSukun = true := by simpa [Cell.isSukun] using hs
          cases e2 : x.haraka <;> simp_all [Haraka.isSukun]
        simp [kindOne, this] at hk

/-- **الترتيب:** الوصلُ ⇒ الوقف ⇒ الابتداء. -/
theorem awa_chain {w : List Cell} (h : awa .wasl w = true) :
    awa .waqf w = true ∧ awa .ibtida w = true :=
  ⟨awa_wasl_waqf h, awa_waqf_ibtida (awa_wasl_waqf h)⟩

end A116.ExhaustPause
