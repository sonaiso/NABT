import A116.Hadd
import A116.Alif
import A116.Residue
import A116.Grade

/-!
# الاستنفادُ قبل الانتقال: جداولُ الدرجات، وعددُها، وبوّابتُها

قرارُ المالك (2026-10-11): «يُستنفد أوّلًا: لكلّ صورةٍ مجموعُ أصنافها كاملًا، ومبرهنةٌ تقول إنّ المجموع
مغلق؛ ثمّ يُسمح بالانتقال». والانتقالُ من مقطعٍ إلى مقطعين إلى ثلاثة: ‎cv + v‎ و‎cv + c‎ عددٌ جديد، ثمّ
‎cv + cv‎ … حتى استنفاد توافيق المقطعين، ثمّ الثلاثة.

## الدرجة

**درجةُ الكلمة عددُ مقاطعها** في التقطيع المبرهَن (`Stages.parse`، وحيدٌ ومعكوسُه الوصل). هذا تعريفٌ مُعلَن
هنا لا مرويّ: إن أراد المالكُ بـ«الثلاثيّ والرباعيّ» عددَ الحروف الأصول (دَحْرَجَ = ‎cvc + cv + cv‎ ثلاثةُ
مقاطع وأربعةُ أصول) فالدرجةُ غيرُ هذه، ويُعاد تعريفُها قبل أيّ بناءٍ عليها.

## ما يُبرهَن (لكلّ درجة، لا على مدوّنة)

* `tableI` جدولُ المقاطع الداخليّة بطول k = صورةُ ‎{0 … 4^k − 1}‎ بالفكّ `decodeI`، و`table k` جدولُ
  الكلمة وصلًا بالدرجة k+1 (k داخليّة ثمّ طرفيّ) = صورةُ ‎{0 … 3·4^k − 1}‎.
* **العددُ الجديد من العدد السابق** (`codeI_snoc`، `decodeI_succ`): ‎N_{k+1} = 4·N_k + d‎ — كلُّ عددٍ في
  الدرجة k+1 مولَّدٌ من عددٍ في الدرجة k ورقمِ مقطعٍ واحد، وتقابلٌ في الاتّجاهين (`decodeI_codeI`،
  `codeI_decodeI`)، وبلا تكرار (`tableI_nodup`، `table_nodup`)، وطولُه ‎4^k‎ و‎3·4^k‎.
* **الترخيصُ داخلَ الجدول** (`strict_mem_table`): كلُّ كلمةٍ من خانات الـ116 مرخَّصةٍ بقيد الحدّ وصلًا
  (`Hadd.strictB`) ليست مدَّ فرق، تقطيعُها صفٌّ في جدول درجتها — لكلّ طول. ومدُّ الفرق هو الاستثناءُ
  المسمّى (`farq_is_the_exception`: ءَاْلْ مقطعٌ واحدٌ CVVC مرخَّص).
* **الجامعُ المانع لكلّ درجة** (`table_iff_licensed`): الصفُّ في جدول الدرجة k+1 ⟺ تقطيعُ كلمةٍ من خاناتٍ
  مرخَّصةٍ بقيد الحدّ وصلًا (غيرِ مدّ الفرق) — لكلّ k، بشاهدٍ موحَّد على طريقة آرتين (`table_realized`). وللدرجات
  1، 2، 3 فحصٌ إضافيٌّ أنّ خاناتِ الشاهد من المرخَّص (`table_realized_upto_three`).
* **استنفادُ الـ116 بأدوارها داخل الثلاثيّ** (`roles_exhausted_within_three`): كلُّ خانةٍ من الـ113
  المرخَّصة (`Alif.licensable`) تقع في كلّ دورٍ تقبله (`cv`، `c`، و`v` لحروف المدّ) آخرَ كلمةٍ مرخَّصةٍ
  بكلّ درجةٍ من 1 و2 و3.

## البوّابة (`Murakhkhas`) والوظائفُ السبع

لكلّ درجةٍ صفٌّ بسبعة حقول: ترميز، إملاء، صوت، اشتقاق، صرف، نحو، دلالة. الحقلُ سندُه إمّا **برهانٌ**
يحمل حدَّه (حدُّ Lean نفسُه، لا اسمُه)، أو **شاهدٌ مودَع** (للدلالة: «طريقُ معرفة اللغة النقل» — لا
تُبرهَن)، أو **معلَّقٌ باسمه**. والدرجةُ k+1 لا تُرخَّص إلّا إذا استوفت كلُّ درجةٍ ≤ k حقولَها السبعة:
`exhaustion_gate` و`no_skip`. والدفترُ الحاليّ (`current`) يملأ ما بُرهن ويعلّق الباقي بسببه، فيُبرهَن
عليه: الدرجةُ الأولى غيرُ مستوفاة (`current_row1_not_mustawfa`)، **فلا ترخيصَ لما فوقها**
(`current_stops_at_one`).

ولا يُبرهَن هنا شيءٌ «على العربيّة»: Lean يُبرهن خواصَّ التعريف على الخانات، ومطابقتُه للمرويّ تُقاس.
-/

set_option autoImplicit false

namespace A116.Exhaust

open A116 A116.Stages A116.Ternary A116.Ladder A116.Hadd

/-! ## ١. أرقامُ المقاطع -/

/-- رقمُ المقطع. الداخليّةُ وصلًا: CV 0، CVV 1، CVC 2، CVVC 3؛ والطرفيّةُ وصلًا: الثلاثةُ الأولى. -/
def dC : Syl → Nat
  | .CV => 0
  | .CVV => 1
  | .CVC => 2
  | .CVVC => 3
  | .CVCC => 4
  | .CVVCC => 5

def ofDC : Nat → Syl
  | 0 => .CV
  | 1 => .CVV
  | 2 => .CVC
  | _ => .CVVC

/-- مقطعٌ داخليٌّ وصلًا: ليس من مقاطع الوقف. -/
def inner (s : Syl) : Bool := !pauseOnly s

/-- مقطعٌ طرفيٌّ وصلًا: داخليٌّ وليس CVVC (لا مثلَ بعد المُغلِق: `geminateB_vc_final`). -/
def final (s : Syl) : Bool := inner s && s != .CVVC

theorem dC_lt {s : Syl} (h : inner s = true) : dC s < 4 := by
  cases s <;> simp_all [inner, pauseOnly, dC]

theorem dC_lt_final {s : Syl} (h : final s = true) : dC s < 3 := by
  cases s <;> simp_all [final, inner, pauseOnly, dC]

theorem ofDC_dC {s : Syl} (h : inner s = true) : ofDC (dC s) = s := by
  cases s <;> simp_all [inner, pauseOnly, dC, ofDC]

theorem dC_ofDC {m : Nat} (h : m < 4) : dC (ofDC m) = m := by
  match m, h with
  | 0, _ => rfl
  | 1, _ => rfl
  | 2, _ => rfl
  | 3, _ => rfl

theorem inner_ofDC (m : Nat) : inner (ofDC m) = true := by
  match m with
  | 0 => rfl
  | 1 => rfl
  | 2 => rfl
  | _ + 3 => rfl

theorem final_ofDC {m : Nat} (h : m < 3) : final (ofDC m) = true := by
  match m, h with
  | 0, _ => rfl
  | 1, _ => rfl
  | 2, _ => rfl

theorem inner_of_final {s : Syl} (h : final s = true) : inner s = true := by
  simp only [final, Bool.and_eq_true] at h; exact h.1


/-- الاستقراءُ من الآخر: ما صحّ للفارغ وانتقل من `t` إلى `t ++ [s]` صحّ لكلّ سلسلة. -/
theorem snoc_induction {α : Type} {P : List α → Prop} (h0 : P [])
    (hs : ∀ t s, P t → P (t ++ [s])) : ∀ l, P l := by
  intro l
  induction h : l.length generalizing l with
  | zero => rw [List.eq_nil_of_length_eq_zero h]; exact h0
  | succ n ih =>
    rcases List.eq_nil_or_concat l with e | ⟨t, s, e⟩
    · subst e; simp at h
    · simp only [List.concat_eq_append] at e
      subst e
      simp at h
      exact hs t s (ih t h)

/-- صورةُ قائمةٍ بلا تكرار بدالّةٍ متباينةٍ عليها بلا تكرار. -/
theorem nodup_map_on {α β : Type} (f : α → β) :
    ∀ l : List α, (∀ x ∈ l, ∀ y ∈ l, f x = f y → x = y) → l.Nodup → (l.map f).Nodup
  | [], _, _ => List.nodup_nil
  | a :: t, hf, hn => by
    rw [List.nodup_cons] at hn
    rw [List.map_cons, List.nodup_cons]
    refine ⟨?_, nodup_map_on f t (fun x hx y hy => hf x (List.mem_cons_of_mem _ hx) y
      (List.mem_cons_of_mem _ hy)) hn.2⟩
    intro hm
    obtain ⟨b, hb, e⟩ := List.mem_map.1 hm
    have := hf b (List.mem_cons_of_mem _ hb) a List.mem_cons_self e
    subst this
    exact hn.1 hb

/-! ## ٢. العددُ في الدرجة: الجديدُ من السابق -/

/-- عددُ سلسلةِ مقاطع داخليّة: أرقامٌ بالأساس 4، الأقدمُ أعلى. -/
def codeI (ss : List Syl) : Nat := ss.foldl (fun a s => 4 * a + dC s) 0

/-- الفكّ: الدرجةُ k+1 من الدرجة k ورقمٍ واحد. -/
def decodeI : Nat → Nat → List Syl
  | 0, _ => []
  | k + 1, n => decodeI k (n / 4) ++ [ofDC (n % 4)]

theorem codeI_nil : codeI [] = 0 := rfl

/-- **العددُ الجديد من العدد السابق**: ‎N(ss ++ [s]) = 4·N(ss) + d(s)‎. -/
theorem codeI_snoc (ss : List Syl) (s : Syl) : codeI (ss ++ [s]) = 4 * codeI ss + dC s := by
  simp [codeI, List.foldl_append]

theorem decodeI_succ (k n : Nat) : decodeI (k + 1) n = decodeI k (n / 4) ++ [ofDC (n % 4)] := rfl

theorem decodeI_length : ∀ k n, (decodeI k n).length = k
  | 0, _ => rfl
  | k + 1, n => by simp [decodeI, decodeI_length k]

theorem decodeI_inner : ∀ k n, ∀ s ∈ decodeI k n, inner s = true
  | 0, _ => by simp [decodeI]
  | k + 1, n => by
    intro s hs
    simp only [decodeI, List.mem_append, List.mem_singleton] at hs
    rcases hs with hs | rfl
    · exact decodeI_inner k _ s hs
    · exact inner_ofDC _

theorem codeI_lt : ∀ (ss : List Syl), (∀ s ∈ ss, inner s = true) → codeI ss < 4 ^ ss.length := by
  refine snoc_induction (by intro _; decide) ?_
  intro t s ih h
  have ht := ih (fun x hx => h x (List.mem_append_left _ hx))
  have hs := dC_lt (h s (List.mem_append_right _ (List.mem_singleton_self s)))
  rw [codeI_snoc, List.length_append, List.length_singleton, Nat.pow_succ]
  omega

/-- **الفكُّ بعد العدّ يعيد السلسلة.** -/
theorem decodeI_codeI : ∀ (ss : List Syl), (∀ s ∈ ss, inner s = true) →
    decodeI ss.length (codeI ss) = ss := by
  refine snoc_induction (by intro _; rfl) ?_
  intro t s ih h
  have ht := ih (fun x hx => h x (List.mem_append_left _ hx))
  have hin := h s (List.mem_append_right _ (List.mem_singleton_self s))
  have hs := dC_lt hin
  rw [List.length_append, List.length_singleton, decodeI_succ, codeI_snoc]
  have e1 : (4 * codeI t + dC s) / 4 = codeI t := by omega
  have e2 : (4 * codeI t + dC s) % 4 = dC s := by omega
  rw [e1, e2, ht, ofDC_dC hin]

/-- **العدُّ بعد الفكّ يعيد العدد.** -/
theorem codeI_decodeI : ∀ k n, n < 4 ^ k → codeI (decodeI k n) = n
  | 0, n, h => by simp at h; subst h; rfl
  | k + 1, n, h => by
    rw [decodeI_succ, codeI_snoc]
    have hk : n / 4 < 4 ^ k := by rw [Nat.pow_succ] at h; omega
    rw [codeI_decodeI k _ hk, dC_ofDC (Nat.mod_lt _ (by decide))]
    omega

/-! ## ٣. الجداول -/

/-- جدولُ المقاطع الداخليّة بطول k: صورةُ ‎{0 … 4^k − 1}‎. -/
def tableI (k : Nat) : List (List Syl) := (List.range (4 ^ k)).map (decodeI k)

theorem tableI_length (k : Nat) : (tableI k).length = 4 ^ k := by simp [tableI]

theorem mem_tableI (k : Nat) (ss : List Syl) :
    ss ∈ tableI k ↔ ss.length = k ∧ ∀ s ∈ ss, inner s = true := by
  simp only [tableI, List.mem_map, List.mem_range]
  constructor
  · rintro ⟨n, _, rfl⟩
    exact ⟨decodeI_length k n, decodeI_inner k n⟩
  · rintro ⟨hl, hi⟩
    refine ⟨codeI ss, ?_, ?_⟩
    · have := codeI_lt ss hi; rw [hl] at this; exact this
    · have := decodeI_codeI ss hi; rw [hl] at this; exact this

theorem tableI_nodup (k : Nat) : (tableI k).Nodup := by
  refine nodup_map_on _ _ ?_ List.nodup_range
  intro x hx y hy e
  simp only [List.mem_range] at hx hy
  have := congrArg codeI e
  rwa [codeI_decodeI k x hx, codeI_decodeI k y hy] at this

/-- كلمةٌ بالدرجة k+1: عددُها ‎3·N(داخليّة) + d(طرفيّ)‎. -/
def decodeW (k n : Nat) : List Syl := decodeI k (n / 3) ++ [ofDC (n % 3)]

def codeW (t : List Syl) (s : Syl) : Nat := 3 * codeI t + dC s

/-- جدولُ الكلمة وصلًا بالدرجة k+1: k داخليّة ثمّ طرفيّ. -/
def table (k : Nat) : List (List Syl) := (List.range (3 * 4 ^ k)).map (decodeW k)

theorem table_length (k : Nat) : (table k).length = 3 * 4 ^ k := by simp [table]

/-- صفٌّ في جدول الدرجة k+1: k داخليّة ثمّ مقطعٌ طرفيّ. -/
def WordRow (k : Nat) (ss : List Syl) : Prop :=
  ∃ t s, ss = t ++ [s] ∧ t.length = k ∧ (∀ x ∈ t, inner x = true) ∧ final s = true

theorem mem_table (k : Nat) (ss : List Syl) : ss ∈ table k ↔ WordRow k ss := by
  simp only [table, List.mem_map, List.mem_range, decodeW]
  constructor
  · rintro ⟨n, hn, rfl⟩
    exact ⟨_, _, rfl, decodeI_length k _, decodeI_inner k _, final_ofDC (Nat.mod_lt _ (by decide))⟩
  · rintro ⟨t, s, rfl, hl, hi, hf⟩
    have hct := codeI_lt t hi
    rw [hl] at hct
    have hs := dC_lt_final hf
    refine ⟨codeW t s, ?_, ?_⟩
    · simp only [codeW]; omega
    · have e1 : codeW t s / 3 = codeI t := by simp only [codeW]; omega
      have e2 : codeW t s % 3 = dC s := by simp only [codeW]; omega
      rw [e1, e2, ofDC_dC (inner_of_final hf)]
      have := decodeI_codeI t hi
      rw [hl] at this
      rw [this]

theorem table_nodup (k : Nat) : (table k).Nodup := by
  refine nodup_map_on _ _ ?_ List.nodup_range
  intro x hx y hy e
  simp only [List.mem_range] at hx hy
  simp only [decodeW] at e
  have hl : (decodeI k (x / 3)).length = (decodeI k (y / 3)).length := by
    simp [decodeI_length]
  obtain ⟨e1, e2⟩ := List.append_inj e hl
  simp only [List.cons.injEq, and_true] at e2
  have hx' : x / 3 < 4 ^ k := by omega
  have hy' : y / 3 < 4 ^ k := by omega
  have q := congrArg codeI e1
  rw [codeI_decodeI k _ hx', codeI_decodeI k _ hy'] at q
  have r := congrArg dC e2
  rw [dC_ofDC (by omega), dC_ofDC (by omega)] at r
  omega

/-- **الجديدُ من السابق في جدول الكلمة**: كلُّ صفٍّ بالدرجة k+2 صفٌّ داخليٌّ بالدرجة k+1 ومقطعٌ طرفيّ،
وعددُه من عدد سابقه: ‎codeW (t ++ [s]) u = 3·(4·N(t) + d(s)) + d(u)‎. -/
theorem codeW_snoc (t : List Syl) (s u : Syl) :
    codeW (t ++ [s]) u = 3 * (4 * codeI t + dC s) + dC u := by
  simp [codeW, codeI_snoc]

theorem table_counts : (List.range 4).map (fun k => (table k).length) = [3, 12, 48, 192] := by
  simp only [table_length]; decide

/-! ## ٤. الترخيصُ داخلَ الجدول -/

theorem zip_ends_vc {α : Type} (X : List Stages.K) (cs : List α)
    (h : (X ++ [Stages.K.v, Stages.K.c]).length = cs.length) :
    ∃ p a x, (X ++ [Stages.K.v, Stages.K.c]).zip cs = p ++ [(Stages.K.v, a), (Stages.K.c, x)] := by
  have hlen : cs.length = X.length + 2 := by simp at h; omega
  have hd : (cs.drop X.length).length = 2 := by simp [hlen]
  have ht : (cs.take X.length).length = X.length := by simp [hlen]
  rcases e : cs.drop X.length with _ | ⟨a, _ | ⟨x, _ | ⟨y, r⟩⟩⟩
  · rw [e] at hd; simp at hd
  · rw [e] at hd; simp at hd
  · refine ⟨X.zip (cs.take X.length), a, x, ?_⟩
    conv => lhs; rw [← List.take_append_drop X.length cs, e]
    rw [List.zip_append ht.symm]
    rfl
  · rw [e] at hd; simp at hd

theorem parse_ne_nil_of_ne {k : List Stages.K} {ss : List Syl} (hk : k ≠ [])
    (h : parse k = some (.none, ss)) : ss ≠ [] := by
  intro e
  subst e
  have := flat_parse h
  simp [flat, Lead.atoms] at this
  exact hk this

/-- **كلُّ مرخَّصٍ بقيد الحدّ وصلًا (غيرِ مدّ الفرق) صفٌّ في جدول درجته**، لكلّ طول. -/
theorem strict_mem_table (w : List Cell) (hw : w ≠ []) (hf : isFarq w = false)
    (h : strictB w = true) :
    ∃ ss, parse (kindOf w) = some (.none, ss) ∧ ss ≠ [] ∧ ss ∈ table (ss.length - 1) := by
  simp only [strictB, Bool.and_eq_true] at h
  obtain ⟨hc, hh⟩ := h
  obtain ⟨ss, hp, hn⟩ := (continueB_iff _).1 hc
  have hk : kindOf w ≠ [] := by
    intro e
    have := kindGo_length none w
    simp only [kindOf] at e
    rw [e] at this
    exact hw (List.eq_nil_of_length_eq_zero this.symm)
  have hne := parse_ne_nil_of_ne hk hp
  refine ⟨ss, hp, hne, ?_⟩
  rcases List.eq_nil_or_concat ss with e | ⟨t, s, e⟩
  · exact absurd e hne
  · simp only [List.concat_eq_append] at e
    subst e
    rw [mem_table]
    refine ⟨t, s, rfl, by simp, ?_, ?_⟩
    · intro x hx
      have := hn x (List.mem_append_left _ hx)
      simp [inner, this]
    · have hs := hn s (List.mem_append_right _ (List.mem_singleton_self s))
      simp only [final, inner, hs, Bool.not_false, Bool.true_and]
      cases s with
      | CVVC =>
        exfalso
        have hflat := flat_parse hp
        have hk2 : kindOf w = (flat .none t ++ [Stages.K.cv]) ++ [Stages.K.v, Stages.K.c] := by
          rw [← hflat]; simp [flat, Lead.atoms, Syl.atoms, Syl.coda]
        have hl : ((flat .none t ++ [Stages.K.cv]) ++ [Stages.K.v, Stages.K.c]).length = w.length := by
          rw [← hk2]; exact kindGo_length none w
        obtain ⟨p, a, x, hz⟩ := zip_ends_vc _ w hl
        simp only [haddB, hf, Bool.false_eq_true, ↓reduceIte] at hh
        rw [hk2, hz, geminateB_vc_final] at hh
        exact absurd hh (by decide)
      | _ => rfl

/-- خاناتُ مدّ الفرق: ءَ اْ لْ. -/
def farqCells : List Cell := [atom 'ء' .fatha, atom 'ا' .sukun, atom 'ل' .sukun]

/-- مدُّ الفرق هو الاستثناءُ المسمّى: ءَاْلْ مرخَّصةٌ بالقيد ومقطعُها الوحيدُ CVVC (طرفٌ لا يقبله الجدول). -/
theorem farq_is_the_exception :
    strictB farqCells = true ∧ parse (kindOf farqCells) = some (.none, [.CVVC]) ∧
    [Syl.CVVC] ∉ table 0 := by
  have hk : kindOf farqCells = flat .none [.CVVC] := by decide
  refine ⟨?_, by rw [hk]; exact parse_flat _ _, ?_⟩
  · simp only [strictB, hk, continueB_flat]; decide
  · rw [mem_table]
    rintro ⟨t, s, e, hl, _, hf⟩
    have : t = [] := List.eq_nil_of_length_eq_zero hl
    subst this
    simp at e
    subst e
    exact absurd hf (by decide)

/-- ما إسقاطُه صفٌّ داخليّ وقيدُ حدّه قائمٌ فهو مرخَّصٌ وصلًا. -/
theorem strict_of_kind {w : List Cell} {ss : List Syl} (hk : kindOf w = flat .none ss)
    (hi : ∀ s ∈ ss, inner s = true) (hh : haddB w = true) : strictB w = true := by
  simp only [strictB, hk, continueB_flat, hh, Bool.and_true, List.all_eq_true]
  intro s hs
  have := hi s hs
  simpa [inner] using this

/-! ## ٤′. الصلةُ بدرجات ADR ١٤ (`A116.Grade`): الجدولُ هنا هو `contGrade` بقيد الحدّ -/

theorem mem_tableI_iff_contGrade (k : Nat) (ss : List Syl) :
    ss ∈ tableI k ↔ ss ∈ Grade.contGrade k := by
  rw [mem_tableI, Grade.mem_cont_iff_all]
  constructor
  · rintro ⟨hl, hi⟩
    exact ⟨hl, fun s hs => by have := hi s hs; simpa [inner] using this⟩
  · rintro ⟨hl, hi⟩
    exact ⟨hl, fun s hs => by simp [inner, hi s hs]⟩

/-- **جدولُ الدرجة k+1 هنا = درجةُ الوصل k+1 في `Grade` بلا صفٍّ آخرُه CVVC** — وهو قيدُ الحدّ وحدَه
(`Hadd.geminateB_vc_final`): الطرفُ CVVC لا مثلَ بعد مُغلِقه. -/
theorem mem_table_iff_contGrade (k : Nat) (ss : List Syl) :
    ss ∈ table k ↔ ss ∈ Grade.contGrade (k + 1) ∧ ss.getLast? ≠ some .CVVC := by
  rw [mem_table, Grade.mem_cont_iff_all]
  constructor
  · rintro ⟨t, s, rfl, hl, hi, hf⟩
    refine ⟨⟨by simp [hl], ?_⟩, ?_⟩
    · intro x hx
      rcases List.mem_append.1 hx with hx | hx
      · have := hi x hx; simpa [inner] using this
      · rw [List.mem_singleton.1 hx]
        have := inner_of_final hf; simpa [inner] using this
    · simp only [List.getLast?_append, List.getLast?_singleton, Option.some_or]
      intro e
      simp only [Option.some.injEq] at e
      subst e
      exact absurd hf (by decide)
  · rintro ⟨⟨hl, hi⟩, hlast⟩
    have hne : ss ≠ [] := by intro e; subst e; simp at hl
    obtain ⟨t, s, rfl⟩ := Grade.exists_concat ss hne
    refine ⟨t, s, rfl, by simp at hl; omega, ?_, ?_⟩
    · intro x hx; simp [inner, hi x (List.mem_append_left _ hx)]
    · have hs := hi s (List.mem_append_right _ (List.mem_singleton_self s))
      simp only [List.getLast?_append, List.getLast?_singleton, Option.some_or, ne_eq,
        Option.some.injEq] at hlast
      simp only [final, inner, hs, Bool.not_false, Bool.true_and, bne_iff_ne, ne_eq]
      exact hlast

/-- ما يُسقطه قيدُ الحدّ من درجة الوصل k+1: ‎4^(k+1) − 3·4^k = 4^k‎ صفًّا (آخرُها CVVC). -/
theorem hadd_removes (k : Nat) :
    (Grade.contGrade (k + 1)).length = (table k).length + 4 ^ k := by
  rw [Grade.cont_length, table_length, Nat.pow_succ]; omega

/-! ## ٥. الجدولُ كلُّه مرخَّصٌ على الخانات (الدرجات 1–3) -/

def bv : Cell := atom 'ب' .fatha

/-- خاناتُ المقطع: كلُّ مقطعٍ يبدأ بـ«بَ»، فالمُغلِقُ بعد المدّ (بْ) يليه مثلُه. -/
def block : Syl → List Cell
  | .CV => [bv]
  | .CVV => [bv, atom 'ا' .sukun]
  | .CVC => [bv, atom 'ب' .sukun]
  | .CVVC => [bv, atom 'ا' .sukun, atom 'ب' .sukun]
  | .CVCC => [bv, atom 'ب' .sukun, atom 'ب' .sukun]
  | .CVVCC => [bv, atom 'ا' .sukun, atom 'ب' .sukun, atom 'ب' .sukun]

def realize (ss : List Syl) : List Cell := ss.flatMap block

/-- كلُّ خانةٍ في التحقيق مرخَّصة (`Alif.licensable`). -/
def realizedLicensable (ss : List Syl) : Bool := (realize ss).all (Alif.licensable.contains ·)

theorem realized_check :
    ∀ k ∈ [0, 1, 2], ∀ ss ∈ table k,
      kindOf (realize ss) = flat .none ss ∧ haddB (realize ss) = true ∧
      realizedLicensable ss = true := by
  decide +kernel

theorem inner_of_row {k : Nat} {ss : List Syl} (h : ss ∈ table k) : ∀ s ∈ ss, inner s = true := by
  obtain ⟨t, u, rfl, _, hi, hf⟩ := (mem_table k ss).1 h
  intro s hs
  rcases List.mem_append.1 hs with hs | hs
  · exact hi s hs
  · rw [List.mem_singleton.1 hs]; exact inner_of_final hf

/-- **كلُّ صفٍّ في جداول الدرجات 1 و2 و3 تحقّقه كلمةٌ من خاناتٍ مرخَّصة يقبلها `strictB`.** -/
theorem table_realized_upto_three :
    ∀ k ∈ [0, 1, 2], ∀ ss ∈ table k,
      strictB (realize ss) = true ∧ kindOf (realize ss) = flat .none ss ∧
      realizedLicensable ss = true := by
  intro k hk ss hss
  obtain ⟨h1, h2, h3⟩ := realized_check k hk ss hss
  exact ⟨strict_of_kind h1 (inner_of_row hss) h2, h1, h3⟩

/-! ## ٥′. الجامعُ المانع لكلّ درجة: الصفُّ في الجدول ⟺ تحقّقه كلمةٌ مرخَّصة

درسُ آرتين: يُعطى **كلُّ** عنصرٍ شاهدَه دفعةً واحدة بقاعدةٍ موحَّدة، ثمّ يُبرهَن أنّ الشاهدَ لا يناقض القيد. وهنا:
لكلّ صفٍّ في أيّ درجة، الكلمةُ `realize` (كلُّ مقطعٍ يبدأ بـ«بَ»، والمُغلِقُ بعد المدّ «بْ» يليه مثلُه) مرخَّصةٌ بقيد
الحدّ وإسقاطُها الصفُّ بعينه — لكلّ طول، لا بالحساب على الدرجات الثلاث وحدَها. ومع `strict_mem_table` يصير
الجدولُ **جامعًا** (كلُّ مرخَّصٍ فيه) **مانعًا** (كلُّ ما فيه مرخَّص). -/

/-- أزواجُ (صنف، خانة) لكلّ مقطع. -/
def pairsOf (ss : List Syl) : List (Stages.K × Cell) := ss.flatMap fun s => s.atoms.zip (block s)

theorem block_length (s : Syl) : (block s).length = s.atoms.length := by
  cases s <;> rfl

theorem kindOne_bv (p : Option Haraka) : kindOne p bv = .cv := by simp [kindOne, bv, atom]
theorem kindOne_alif : kindOne (some .fatha) (atom 'ا' .sukun) = .v := by decide
theorem kindOne_ba_f : kindOne (some .fatha) (atom 'ب' .sukun) = .c := by decide
theorem kindOne_ba_s : kindOne (some .sukun) (atom 'ب' .sukun) = .c := by decide

theorem kindGo_block (s : Syl) (p : Option Haraka) (rest : List Cell) :
    ∃ q, kindGo p (block s ++ rest) = s.atoms ++ kindGo q rest := by
  cases s with
  | CV => exact ⟨some .fatha, by
      simp only [block, List.cons_append, List.nil_append, kindGo, kindOne_bv, Syl.atoms, Syl.coda]
      rfl⟩
  | CVV => exact ⟨some .sukun, by
      simp only [block, List.cons_append, List.nil_append, kindGo, kindOne_bv, Syl.atoms, Syl.coda]
      simp only [bv, atom]; simp; decide⟩
  | CVC => exact ⟨some .sukun, by
      simp only [block, List.cons_append, List.nil_append, kindGo, kindOne_bv, Syl.atoms, Syl.coda]
      simp only [bv, atom]; simp; decide⟩
  | CVVC => exact ⟨some .sukun, by
      simp only [block, List.cons_append, List.nil_append, kindGo, kindOne_bv, Syl.atoms, Syl.coda]
      simp only [bv, atom]; simp; decide⟩
  | CVCC => exact ⟨some .sukun, by
      simp only [block, List.cons_append, List.nil_append, kindGo, kindOne_bv, Syl.atoms, Syl.coda]
      simp only [bv, atom]; simp; decide⟩
  | CVVCC => exact ⟨some .sukun, by
      simp only [block, List.cons_append, List.nil_append, kindGo, kindOne_bv, Syl.atoms, Syl.coda]
      simp only [bv, atom]; simp; decide⟩

theorem kindGo_realize : ∀ (ss : List Syl) (p : Option Haraka),
    kindGo p (realize ss) = flat .none ss
  | [], _ => rfl
  | s :: t, p => by
    obtain ⟨q, hq⟩ := kindGo_block s p (realize t)
    have e : realize (s :: t) = block s ++ realize t := by simp [realize]
    rw [e, hq, kindGo_realize t q]
    simp [flat, Lead.atoms]

theorem kindOf_realize (ss : List Syl) : kindOf (realize ss) = flat .none ss :=
  kindGo_realize ss none

theorem zip_realize : ∀ ss : List Syl, (flat .none ss).zip (realize ss) = pairsOf ss
  | [] => rfl
  | s :: t => by
    have e : realize (s :: t) = block s ++ realize t := by simp [realize]
    have ef : flat .none (s :: t) = s.atoms ++ flat .none t := by simp [flat, Lead.atoms]
    rw [e, ef, List.zip_append (by rw [block_length]), zip_realize t]
    simp [pairsOf]

/-- ما بعد المقطع: فارغٌ أو يبدأ بـ«بَ» متحرّكة. -/
def StartsBv (rest : List (Stages.K × Cell)) : Prop :=
  rest = [] ∨ ∃ r, rest = (Stages.K.cv, bv) :: r

theorem pairsOf_starts (t : List Syl) : StartsBv (pairsOf t) := by
  cases t with
  | nil => left; rfl
  | cons s u => right; cases s <;> exact ⟨_, by simp [pairsOf, block, Syl.atoms, Syl.coda]; rfl⟩

theorem geminate_block (s : Syl) (hs : inner s = true) (rest : List (Stages.K × Cell))
    (hr : StartsBv rest) (hne : s = .CVVC → rest ≠ []) :
    geminateB (s.atoms.zip (block s) ++ rest) = geminateB rest := by
  rcases hr with rfl | ⟨r, rfl⟩
  · cases s <;> simp_all [inner, pauseOnly, block, Syl.atoms, Syl.coda, geminateB, stepOK]
  · cases s <;> simp_all [inner, pauseOnly, block, Syl.atoms, Syl.coda, geminateB, stepOK, bv, atom]

theorem geminate_realize : ∀ ss : List Syl, (∀ s ∈ ss, inner s = true) →
    ss.getLast? ≠ some .CVVC → geminateB (pairsOf ss) = true
  | [], _, _ => rfl
  | s :: t, hi, hl => by
    have hs := hi s List.mem_cons_self
    have ht : ∀ x ∈ t, inner x = true := fun x hx => hi x (List.mem_cons_of_mem _ hx)
    have e : pairsOf (s :: t) = s.atoms.zip (block s) ++ pairsOf t := by simp [pairsOf]
    rw [e]
    cases t with
    | nil =>
      rw [geminate_block s hs _ (pairsOf_starts []) ?_]
      · rfl
      · intro hc; subst hc; simp at hl
    | cons u v =>
      have hl' : (u :: v).getLast? ≠ some .CVVC := by
        intro h; apply hl; rw [List.getLast?_cons_cons]; exact h
      rw [geminate_block s hs _ (pairsOf_starts _) (fun _ => by simp [pairsOf]; cases u <;> simp [block, Syl.atoms])]
      exact geminate_realize (u :: v) ht hl'

theorem isFarq_bv (rest : List Cell) : isFarq (bv :: rest) = false := by
  have hb : (bv == atom 'ء' .fatha) = false := by decide
  match rest with
  | [] => rfl
  | [_] => rfl
  | _ :: _ :: _ => simp only [isFarq, hb, Bool.false_and]

theorem isFarq_realize (ss : List Syl) : isFarq (realize ss) = false := by
  cases ss with
  | nil => rfl
  | cons s t =>
    have e : realize (s :: t) = block s ++ realize t := by simp [realize]
    rw [e]
    cases s <;> exact isFarq_bv _

/-- **مانع لكلّ درجة**: كلُّ صفٍّ في جدول الدرجة k+1 تحقّقه كلمةٌ مرخَّصةٌ بقيد الحدّ إسقاطُها الصفُّ بعينه. -/
theorem table_realized (k : Nat) (ss : List Syl) (h : ss ∈ table k) :
    strictB (realize ss) = true ∧ kindOf (realize ss) = flat .none ss ∧ isFarq (realize ss) = false := by
  have hi := inner_of_row h
  have hl : ss.getLast? ≠ some .CVVC := ((mem_table_iff_contGrade k ss).1 h).2
  refine ⟨strict_of_kind (kindOf_realize ss) hi ?_, kindOf_realize ss, isFarq_realize ss⟩
  simp only [haddB, isFarq_realize, Bool.false_eq_true, ↓reduceIte, kindOf_realize, zip_realize]
  exact geminate_realize ss hi hl

/-- **الجامعُ المانع لكلّ درجة**: الصفُّ في جدول الدرجة k+1 ⟺ تقطيعُ كلمةٍ من خاناتٍ، مرخَّصةٍ بقيد الحدّ وصلًا، ليست
مدَّ فرق، بطول k+1. -/
theorem table_iff_licensed (k : Nat) (ss : List Syl) :
    ss ∈ table k ↔ ∃ w : List Cell, w ≠ [] ∧ isFarq w = false ∧ strictB w = true ∧
      parse (kindOf w) = some (.none, ss) ∧ ss.length = k + 1 := by
  constructor
  · intro h
    obtain ⟨hs, hk, hf⟩ := table_realized k ss h
    obtain ⟨t, u, rfl, hl, _, _⟩ := (mem_table k _).1 h
    refine ⟨realize (t ++ [u]), ?_, hf, hs, by rw [hk]; exact parse_flat _ _, by simp [hl]⟩
    intro e
    have := congrArg List.length (kindOf_realize (t ++ [u]))
    rw [e] at this
    simp [kindOf, kindGo, flat, Lead.atoms, Syl.atoms] at this
  · rintro ⟨w, hw, hf, h, hp, hl⟩
    obtain ⟨ss', hp', _, hm⟩ := strict_mem_table w hw hf h
    rw [hp] at hp'
    simp only [Option.some.injEq, Prod.mk.injEq, true_and] at hp'
    subst hp'
    rw [hl] at hm
    simpa using hm

/-! ## ٦. استنفادُ الـ116 بأدوارها داخل الثلاثيّ -/

/-- أدوارُ الخانة: المتحرّكةُ `cv`؛ والساكنةُ `c`، و`v` أيضًا إن كانت حرفَ مدّ. -/
def rolesOf (x : Cell) : List Stages.K :=
  if x.haraka ≠ .sukun then [.cv]
  else match maddVowel x.carrier with
    | some _ => [.c, .v]
    | none => [.c]

/-- الحركةُ التي تسبق الخانةَ في دورها: للمدّ حركتُه المجانسة، وللمُغلِق حركةٌ غيرُها. -/
def before (x : Cell) (r : Stages.K) : Haraka :=
  match r, maddVowel x.carrier with
  | .v, some h => h
  | .c, some .fatha => .kasra
  | _, _ => .fatha

/-- الشاهد: ‎(d − 1)‎ مقطعَ «بَ» ثمّ الخانةُ في دورها آخرَ الكلمة. -/
def witness (x : Cell) (r : Stages.K) (d : Nat) : List Cell :=
  List.replicate (d - 1) bv ++
    (if r = .cv then [x] else [atom 'ب' (before x r), x])

/-- المقطعُ الأخيرُ للشاهد بحسب الدور. -/
def lastSyl : Stages.K → Syl
  | .cv => .CV
  | .v => .CVV
  | .c => .CVC

def expect (r : Stages.K) (d : Nat) : List Syl := List.replicate (d - 1) .CV ++ [lastSyl r]

def exhaustedAt (d : Nat) (x : Cell) : Bool :=
  (rolesOf x).all fun r =>
    let w := witness x r d
    kindOf w == flat .none (expect r d) && haddB w && (kindOf w).getLast? == some r &&
      w.getLast? == some x && w.all (Alif.licensable.contains ·)

theorem exhausted_check : ∀ d ∈ [1, 2, 3], Alif.licensable.all (exhaustedAt d) = true := by
  decide +kernel

theorem expect_inner (r : Stages.K) (d : Nat) : ∀ s ∈ expect r d, inner s = true := by
  intro s hs
  simp only [expect, List.mem_append, List.mem_replicate, List.mem_singleton] at hs
  rcases hs with ⟨_, rfl⟩ | rfl
  · rfl
  · cases r <;> rfl

theorem expect_length (r : Stages.K) {d : Nat} (hd : 1 ≤ d) : (expect r d).length = d := by
  simp [expect]; omega

/-- **كلُّ خانةٍ مرخَّصة، في كلّ دورٍ تقبله، تقع آخرَ كلمةٍ مرخَّصةٍ بكلّ درجةٍ من 1 و2 و3.** -/
theorem roles_exhausted_within_three :
    ∀ d ∈ [1, 2, 3], ∀ x ∈ Alif.licensable, ∀ r ∈ rolesOf x,
      strictB (witness x r d) = true ∧ (kindOf (witness x r d)).getLast? = some r ∧
      (witness x r d).getLast? = some x ∧
      ∃ ss, parse (kindOf (witness x r d)) = some (.none, ss) ∧ ss.length = d := by
  intro d hd x hx r hr
  have h := exhausted_check d hd
  rw [List.all_eq_true] at h
  have h2 := h x hx
  simp only [exhaustedAt, List.all_eq_true] at h2
  have h3 := h2 r hr
  simp only [Bool.and_eq_true, beq_iff_eq] at h3
  obtain ⟨⟨⟨⟨hk, hh⟩, hl⟩, hx'⟩, _⟩ := h3
  have hd1 : 1 ≤ d := by simp at hd; omega
  refine ⟨strict_of_kind hk (expect_inner r d) hh, hl, hx', expect r d, ?_, expect_length r hd1⟩
  rw [hk]; exact parse_flat _ _

/-- عددُ (الخانة، الدور) المستنفَدة في كلّ درجة: 113 خانة، منها ثلاثةُ أحرف مدٍّ ساكنة بدورين. -/
theorem role_count : (Alif.licensable.map fun x => (rolesOf x).length).sum = 116 := by
  decide

/-! ## ٧. الوظائفُ السبع والبوّابة -/

inductive Wazifa where
  | tarmiz | imla | sawt | ishtiqaq | sarf | nahw | dalala
  deriving DecidableEq, Repr

def Wazifa.all : List Wazifa := [.tarmiz, .imla, .sawt, .ishtiqaq, .sarf, .nahw, .dalala]

theorem Wazifa.mem_all (w : Wazifa) : w ∈ Wazifa.all := by cases w <;> decide

/-- سندُ الحقل: برهانٌ يحمل حدَّه، أو شاهدٌ مودَع (بمودَعه وعدد شواهده)، أو معلَّقٌ باسمه. -/
inductive Sanad where
  | burhan {p : Prop} (h : p)
  | shahid (deposit : String) (count : Nat)
  | muallaq (reason : String)

def Sanad.qaim : Sanad → Bool
  | .muallaq _ => false
  | _ => true

/-- صفُّ الدرجة مستوفًى: لا حقلَ من السبعة معلَّق. -/
def Mustawfa (row : Wazifa → Sanad) : Prop := ∀ w, (row w).qaim = true

/-- البوّابة: الدرجةُ 1 (الخاناتُ ومقطعُها) مدخل؛ والدرجةُ k+2 لا تُرخَّص إلّا بترخيص k+1 واستيفاء صفّها. -/
def Murakhkhas (L : Nat → Wazifa → Sanad) : Nat → Prop
  | 0 => True
  | 1 => True
  | k + 2 => Murakhkhas L (k + 1) ∧ Mustawfa (L (k + 1))

/-- **بوّابةُ الاستنفاد**: ترخيصُ الدرجة k+1 يستلزم استيفاءَ كلّ درجةٍ من 1 إلى k. -/
theorem exhaustion_gate (L : Nat → Wazifa → Sanad) :
    ∀ k, Murakhkhas L (k + 1) → ∀ j, 1 ≤ j → j ≤ k → Mustawfa (L j)
  | 0, _, j, h1, h2 => absurd (Nat.le_trans h1 h2) (by decide)
  | k + 1, h, j, h1, h2 => by
    obtain ⟨hk, hm⟩ := h
    rcases Nat.lt_or_ge j (k + 1) with hj | hj
    · exact exhaustion_gate L k hk j h1 (by omega)
    · have : j = k + 1 := by omega
      subst this; exact hm

/-- **لا قفز**: درجةٌ دونها صفٌّ غيرُ مستوفًى لا تُرخَّص. -/
theorem no_skip (L : Nat → Wazifa → Sanad) (k j : Nat) (h1 : 1 ≤ j) (h2 : j ≤ k)
    (hj : ¬ Mustawfa (L j)) : ¬ Murakhkhas L (k + 1) :=
  fun h => hj (exhaustion_gate L k h j h1 h2)

/-- والعكس: استيفاءُ ما دونها كافٍ. -/
theorem gate_of_exhausted (L : Nat → Wazifa → Sanad) :
    ∀ k, (∀ j, 1 ≤ j → j ≤ k → Mustawfa (L j)) → Murakhkhas L (k + 1)
  | 0, _ => trivial
  | k + 1, h => ⟨gate_of_exhausted L k (fun j h1 h2 => h j h1 (by omega)), h (k + 1) (by omega) (Nat.le_refl _)⟩

/-! ## ٨. الدفترُ الحاليّ: ما بُرهن يحمل حدَّه، وما لم يُبرهَن معلَّقٌ باسمه -/

/-- الترميزُ في الدرجة d: عددُ صفّ الكلمة تقابلٌ مع ‎{0 … 3·4^(d−1) − 1}‎ بلا تكرار. -/
def TarmizAt (d : Nat) : Prop :=
  (table (d - 1)).length = 3 * 4 ^ (d - 1) ∧ (table (d - 1)).Nodup ∧
    ∀ ss, ss ∈ table (d - 1) ↔ WordRow (d - 1) ss

theorem tarmizAt (d : Nat) : TarmizAt d :=
  ⟨table_length _, table_nodup _, mem_table _⟩

/-- الصوتُ في الدرجة d: كلُّ مرخَّصٍ بقيد الحدّ وصلًا بدرجة d (غيرِ مدّ الفرق) صفٌّ في جدولها. -/
def SawtAt (d : Nat) : Prop :=
  ∀ w : List Cell, w ≠ [] → isFarq w = false → strictB w = true →
    ∀ ss, parse (kindOf w) = some (.none, ss) → ss.length = d → ss ∈ table (d - 1)

theorem sawtAt (d : Nat) : SawtAt d := by
  intro w hw hf h ss hp hl
  obtain ⟨ss', hp', _, hm⟩ := strict_mem_table w hw hf h
  rw [hp] at hp'
  simp only [Option.some.injEq, Prod.mk.injEq, true_and] at hp'
  subst hp'
  rw [← hl]; exact hm

/-- الإملاء: سلسلةُ قواعد الطبعة تُردّ بعينها (`Residue.chain_restore`) — عامٌّ في كلّ درجة. -/
def ImlaAt (_d : Nat) : Prop :=
  ∀ (sts : List Residue.Step) (s : List Residue.Glyph),
    Residue.restoreAll (Residue.runSteps sts s).1 (Residue.runSteps sts s).2 = s

theorem imlaAt (d : Nat) : ImlaAt d := Residue.chain_restore

/-- الدفترُ الحاليّ لكلّ درجة. -/
def current (d : Nat) : Wazifa → Sanad
  | .tarmiz => .burhan (tarmizAt d)
  | .imla => .burhan (imlaAt d)
  | .sawt => .burhan (sawtAt d)
  | .ishtiqaq => .muallaq "JAMID_MUSHTAQ_PER_NUMBER_UNDEFINED"
  | .sarf => .muallaq "MABNI_MURAB_MAMNU_PER_NUMBER_UNDEFINED"
  | .nahw => .muallaq "NAHW_PER_NUMBER_UNDEFINED"
  | .dalala => .muallaq "DALALA_NEEDS_SEALED_WITNESS"

theorem current_row1_not_mustawfa : ¬ Mustawfa (current 1) := by
  intro h
  have := h .sarf
  simp [current, Sanad.qaim] at this

theorem current_licensed_one : Murakhkhas current 1 := trivial

/-- **بقانون الاستنفاد نفسِه: الدفترُ الحاليّ يقف عند الدرجة الأولى.** -/
theorem current_stops_at_one : ∀ k, ¬ Murakhkhas current (k + 2) :=
  fun k => no_skip current (k + 1) 1 (Nat.le_refl _) (by omega) current_row1_not_mustawfa

/-- الحقولُ المبرهَنةُ ثلاثةٌ من سبعة في كلّ درجة. -/
theorem current_qaim_count (d : Nat) :
    (Wazifa.all.filter fun w => (current d w).qaim).length = 3 := by
  simp [Wazifa.all, current, Sanad.qaim]

end A116.Exhaust
