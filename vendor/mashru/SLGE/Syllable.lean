import SLGE.Law

/-!
# المقطع وحده: ترقيمٌ متدرّجٌ لا ثغرةَ فيه

المقطعُ سلسلةٌ فيها متحرّكٌ واحد. آلتُه آلةُ القانون نفسُها مع شرطٍ واحد: لا متحرّكَ ولا حدَّ بعد الأوّل.
فيُرقَّم ما يرخّصه القانونُ من المقاطع وحدَه — لا ما يُعَدّ من القوالب وتُميته الألف — ترقيمًا متدرّجًا
بعدد الصوامت: ‎168‎ ثمّ ‎4648‎ ثمّ ‎130144‎، ومجموعُها ‎134960‎؛ والمرخَّصُ منها في الوصل ‎4816‎.
-/

namespace SLGE
namespace Law

def δ1 (q a : Nat) : Nat :=
  if 1 ≤ q ∧ a < 116 ∧ a % 4 < 3 then 96 else if a = 116 then 96 else δ q a

def Msyl : Machine := ⟨116, δ1, ω, Fwaqf⟩
def MsylWasl : Machine := ⟨116, δ1, ω, Fwasl⟩

theorem δ1_dead (a : Nat) : δ1 96 a = 96 := by
  unfold δ1; split
  · rfl
  · split
    · rfl
    · exact δ_big a (Nat.le_refl 96)

theorem run1_dead (F : Nat → Bool) : ∀ l, (Machine.mk 116 δ1 ω F).runL 96 l = 96
  | [] => rfl
  | a :: l => by
    show (Machine.mk 116 δ1 ω F).runL (δ1 96 a) l = 96
    rw [δ1_dead]; exact run1_dead F l

theorem δ1_eq (q a : Nat) (h : δ1 q a ≠ 96) : δ1 q a = δ q a := by
  unfold δ1 at h ⊢; split
  · simp_all
  · split
    · simp_all
    · rfl

theorem run1_live (F : Nat → Bool) : ∀ (q : Nat) (l : List Nat), (Machine.mk 116 δ1 ω F).runL q l ≠ 96 →
    (Machine.mk 116 δ1 ω F).runL q l = run q l ∧ (Machine.mk 116 δ1 ω F).wtL q l = wt q l
  | _, [], _ => ⟨rfl, rfl⟩
  | q, a :: l, h => by
    have hd : δ1 q a ≠ 96 := by
      intro e; apply h
      show (Machine.mk 116 δ1 ω F).runL (δ1 q a) l = 96
      rw [e]; exact run1_dead F l
    have ih := run1_live F (δ1 q a) l h
    rw [δ1_eq q a hd] at ih
    constructor
    · show (Machine.mk 116 δ1 ω F).runL (δ1 q a) l = run (δ q a) l
      rw [δ1_eq q a hd]; exact ih.1
    · show ω q a + (Machine.mk 116 δ1 ω F).wtL (δ1 q a) l = ω q a + wt (δ q a) l
      rw [δ1_eq q a hd, ih.2]

theorem live_of (F : Nat → Bool) (hF : ∀ q, F q = true → q ≠ 96) (l : List Nat)
    (h : (Machine.mk 116 δ1 ω F).Lic 0 l) : (Machine.mk 116 δ1 ω F).runL 0 l ≠ 96 :=
  hF _ h.2

/-- أعلى وزنٍ يبقى من كلّ حالةٍ داخل مقطعٍ واحد. -/
def maxw (q : Nat) : Nat :=
  if q = 0 then 3 else if q ≤ 4 then 2 else if q < 35 then 1
  else if 67 ≤ q ∧ q < 96 then 1 else 0

theorem fin_maxw : ∀ q < 96, ∀ a < 116, δ1 q a ≠ 96 → ω q a + maxw (δ1 q a) ≤ maxw q := by
  decide +kernel

theorem fin_close1 : ∀ q < 97, ∀ a < 116, δ1 q a < 97 := by decide +kernel

theorem δ1_le (q a : Nat) : δ1 q a ≤ 96 := by
  unfold δ1; split
  · omega
  · split
    · omega
    · exact δ_le q a

theorem wt_bound1 (F : Nat → Bool) : ∀ (l : List Nat) (q : Nat), q < 96 → (∀ a ∈ l, a < 116) →
    (Machine.mk 116 δ1 ω F).runL q l ≠ 96 → (Machine.mk 116 δ1 ω F).wtL q l ≤ maxw q
  | [], _, _, _, _ => Nat.zero_le _
  | a :: l, q, hq, hl, h => by
    have hd : δ1 q a ≠ 96 := by
      intro e; apply h
      show (Machine.mk 116 δ1 ω F).runL (δ1 q a) l = 96
      rw [e]; exact run1_dead F l
    have hs := fin_maxw q hq a (hl a (by simp)) hd
    have ih := wt_bound1 F l (δ1 q a) (by have := δ1_le q a; omega) (fun b hb => hl b (by simp [hb])) h
    show ω q a + (Machine.mk 116 δ1 ω F).wtL (δ1 q a) l ≤ maxw q
    omega

theorem hK1 (F : Nat → Bool) (hF : ∀ q, F q = true → q ≠ 96) :
    ∀ l, (Machine.mk 116 δ1 ω F).Lic 0 l → l.length ≤ 3 * (Machine.mk 116 δ1 ω F).wtL 0 l := by
  intro l hl
  have hlive := live_of F hF l hl
  have e := run1_live F 0 l hlive
  rw [e.2]
  apply bound l (fun a ha => by have := hl.1 a ha; simp at this; omega)
  rw [← e.1]; exact hlive

theorem hW1 (F : Nat → Bool) (hF : ∀ q, F q = true → q ≠ 96) :
    ∀ l, (Machine.mk 116 δ1 ω F).Lic 0 l → (Machine.mk 116 δ1 ω F).wtL 0 l ≤ 3 := by
  intro l hl
  have := wt_bound1 F l 0 (by decide) (fun a ha => by have := hl.1 a ha; simp at this; exact this)
    (live_of F hF l hl)
  simpa [maxw] using this

theorem hFwaqf : ∀ q, Fwaqf q = true → q ≠ 96 := fun q h => live_of_F q (Or.inl h)
theorem hFwasl : ∀ q, Fwasl q = true → q ≠ 96 := fun q h => live_of_F q (Or.inr h)

/-! ### الحسابُ الصنفيّ للمقطع (`SLGE/HisabSinfi.lean`)

أُضيف بإذن المالك في الجلسة (2026-11-01؛ اختار «عدّل SLGE نفسَها»، انظر رأس `SLGE/HisabSinfi.lean`) لتُبرهَن به أعدادُ المقطع بعده
(`sl0` … `slw3`) — وكانت بالجدول `tab` (`lev_tab`، حُذف). حالاتُ آلة المقطع السبعُ والتسعون تتكافأ في ثمانية أصناف (`HisabMaqta.sM`):
‎0‎ ابتداء، ‎1‎ بعد مفتوح، ‎2‎ بعد مضمومٍ أو مكسور، ‎3‎ بعد مدّ، ‎4‎ الحالةُ ‎5‎ (لا تُبلغ من الابتداء)، ‎5‎ بعد ساكنٍ مُغلِقٍ أو مدٍّ ثمّ ساكن،
‎6‎ ساكنان معلّقان على الوقف (‎35‎، ‎36‎)، ‎7‎ ممتنع (ومعه حالاتُ الحدّ، وآلةُ المقطع تُميت الحدّ). والأصنافُ وصفوفُها وجهدُها تعيينُ البنّاء،
يفحصه التكافؤُ نفسُه (`maqta_mutakafi_waqf`، `maqta_mutakafi_wasl`)؛ وأعدادُ المقطع (`sl0` … `slw3`) تمرّ بـ `Hisab.lev_eq`. وأُبقي على `decide`
في ثلاثَ عشرةَ مساعدةً خاصّةً (`ShartM_0` …) كما في الكلمة، ولم يُقس فيه ما يبلغه decide على الحالات كلِّها معًا.
-/

namespace HisabMaqta
open HisabKalima (waznK)

/-- صنفُ حالة المقطع. -/
def sM (q : Nat) : Nat :=
  if q = 0 then 0 else if q = 1 then 1 else if q ≤ 3 then 2 else if q = 4 then 3 else if q = 5 then 4
  else if q ≤ 34 then 5 else if q ≤ 36 then 6 else if q ≤ 66 then 7 else if q ≤ 95 then 5 else 7

/-- **صفوفُ الأصناف** (الوزن، الصنفُ الهدف، العدد) على الخانات الـ116. -/
def saffM : Nat → List (Nat × Nat × Nat)
  | 0 => [(1, 1, 28), (1, 2, 56), (1, 7, 32)]
  | 1 => [(0, 3, 1), (1, 5, 28), (1, 7, 87)]
  | 2 => [(0, 3, 1), (1, 5, 27), (1, 7, 88)]
  | 3 => [(1, 5, 28), (1, 7, 88)]
  | 4 => [(1, 7, 116)]
  | 5 => [(1, 6, 28), (1, 7, 88)]
  | 6 => [(1, 7, 116)]
  | 7 => [(1, 7, 116)]
  | _ => []

/-- القبولُ موقوفًا عليه: كلُّ صنفٍ إلّا الابتداءَ والممتنع. -/
def FWm (i : Nat) : Bool := !(i == 0 || i == 7)
/-- القبولُ في الوصل: ويسقط الساكنان المعلّقان على الوقف (‎6‎). -/
def FLm (i : Nat) : Bool := !(i == 0 || i == 6 || i == 7)

def QM (F : Nat → Bool) : Asnaf := ⟨8, saffM, F⟩

theorem sinfM : ∀ q < 97, sM q < 8 := by decide +kernel
theorem saffM_hadd : ∀ q < 97, ∀ e ∈ saffM (sM q), e.1 ≤ 1 ∧ e.2.1 < 8 := by decide +kernel
/-- ما يُفحص لكلّ حالة: عددُ انتقالاتها بكلّ وزنٍ إلى كلّ صنفٍ هو ما في صفّ صنفها. -/
abbrev ShartM (q : Nat) : Prop := ∀ u ≤ 1, ∀ j < 8,
    ((List.range 116).filter fun b => ω q b == u && sM (δ1 q b) == j).length =
      (((saffM (sM q)).filter fun e => e.1 == u && e.2.1 == j).map fun e => e.2.2).sum

private theorem ShartM_0 : ∀ r < 8, ShartM (r + 0) := by decide +kernel
private theorem ShartM_1 : ∀ r < 8, ShartM (r + 8) := by decide +kernel
private theorem ShartM_2 : ∀ r < 8, ShartM (r + 16) := by decide +kernel
private theorem ShartM_3 : ∀ r < 8, ShartM (r + 24) := by decide +kernel
private theorem ShartM_4 : ∀ r < 8, ShartM (r + 32) := by decide +kernel
private theorem ShartM_5 : ∀ r < 8, ShartM (r + 40) := by decide +kernel
private theorem ShartM_6 : ∀ r < 8, ShartM (r + 48) := by decide +kernel
private theorem ShartM_7 : ∀ r < 8, ShartM (r + 56) := by decide +kernel
private theorem ShartM_8 : ∀ r < 8, ShartM (r + 64) := by decide +kernel
private theorem ShartM_9 : ∀ r < 8, ShartM (r + 72) := by decide +kernel
private theorem ShartM_10 : ∀ r < 8, ShartM (r + 80) := by decide +kernel
private theorem ShartM_11 : ∀ r < 8, ShartM (r + 88) := by decide +kernel
private theorem ShartM_12 : ∀ r < 1, ShartM (r + 96) := by decide +kernel

theorem adadM : ∀ q < 97, ShartM q := by
  intro q hq
  have h : q < 8 ∨ (8 ≤ q ∧ q < 16) ∨ (16 ≤ q ∧ q < 24) ∨ (24 ≤ q ∧ q < 32) ∨ (32 ≤ q ∧ q < 40) ∨ (40 ≤ q ∧ q < 48) ∨ (48 ≤ q ∧ q < 56) ∨ (56 ≤ q ∧ q < 64) ∨ (64 ≤ q ∧ q < 72) ∨ (72 ≤ q ∧ q < 80) ∨ (80 ≤ q ∧ q < 88) ∨ (88 ≤ q ∧ q < 96) ∨ (96 ≤ q ∧ q < 97) := by omega
  rcases h with h | h | h | h | h | h | h | h | h | h | h | h | h
  · have := ShartM_0 q h; rwa [Nat.add_zero] at this
  · have := ShartM_1 (q - 8) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartM_2 (q - 16) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartM_3 (q - 24) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartM_4 (q - 32) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartM_5 (q - 40) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartM_6 (q - 48) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartM_7 (q - 56) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartM_8 (q - 64) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartM_9 (q - 72) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartM_10 (q - 80) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartM_11 (q - 88) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartM_12 (q - 96) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this

/-- **التكافؤ (الوقف):** حالاتُ المقطع موقوفًا عليه تتكافأ في ثمانية أصناف. -/
theorem maqta_mutakafi_waqf : Mutakafi Msyl (QM FWm) 1 sM (fun q => q < 97) where
  maghluq := fun q hq b hb => fin_close1 q hq b hb
  sinf := sinfM
  wazn := fun q hq b hb => waznK q hq b hb
  saff := saffM_hadd
  qubul := by show ∀ q < 97, Fwaqf q = FWm (sM q); decide +kernel
  adad := adadM

/-- **التكافؤ (الوصل).** -/
theorem maqta_mutakafi_wasl : Mutakafi MsylWasl (QM FLm) 1 sM (fun q => q < 97) where
  maghluq := fun q hq b hb => fin_close1 q hq b hb
  sinf := sinfM
  wazn := fun q hq b hb => waznK q hq b hb
  saff := saffM_hadd
  qubul := by show ∀ q < 97, Fwasl q = FLm (sM q); decide +kernel
  adad := adadM

/-- الجهد: يكفي الصنفَ طولُ ‎`2·w + pM i`‎. -/
def pM (i : Nat) : Nat := if i = 1 ∨ i = 2 then 1 else 0

theorem saffM_kabir (i : Nat) (h : 8 ≤ i) : saffM i = [] := by
  match i, h with
  | n + 8, _ => rfl

theorem mayyitM (F : Nat → Bool) (hF : F 7 = false) :
    ∀ i, (i == 7) = true → (QM F).F i = false ∧ ∀ e ∈ (QM F).saff i, (e.2.1 == 7) = true := by
  intro i hi; simp at hi; subst hi
  exact ⟨hF, by simp [QM, saffM]⟩

theorem potM (F : Nat → Bool) : ∀ i, (i == 7) = false → ∀ e ∈ (QM F).saff i, (e.2.1 == 7) = false →
    pM e.2.1 + 1 ≤ pM i + 2 * e.1 := by
  intro i hi e he hj
  have : i < 8 ∨ 8 ≤ i := by omega
  rcases this with h | h
  · have k : ∀ i < 8, (i == 7) = false → ∀ e ∈ saffM i, (e.2.1 == 7) = false → pM e.2.1 + 1 ≤ pM i + 2 * e.1 := by
      decide +kernel
    exact k i h hi e he hj
  · simp [QM, saffM_kabir i h] at he

theorem wazn1M (F : Nat → Bool) : ∀ i, ∀ e ∈ (QM F).saff i, e.1 ≤ 1 := by
  intro i e he
  have : i < 8 ∨ 8 ≤ i := by omega
  rcases this with h | h
  · have k : ∀ i < 8, ∀ e ∈ saffM i, e.1 ≤ 1 := by decide +kernel
    exact k i h e he
  · simp [QM, saffM_kabir i h] at he

/-- **الحسابُ الصنفيّ للمقطع موقوفًا عليه:** الأصنافُ الثمانية، والجهدُ ‎`pM`‎ بثابتٍ ‎2‎، والممتنعُ ميّت. -/
def hisabWaqf : Hisab Msyl 0 where
  Q := QM FWm
  U := 1
  s := sM
  P := fun q => q < 97
  mutakafi := maqta_mutakafi_waqf
  bidaya := by decide
  K := 2
  pot := pM
  mayyit := (· == 7)
  mayyit_sahih := mayyitM FWm rfl
  juhd := potM FWm

/-- **الحسابُ الصنفيّ للمقطع في الوصل.** -/
def hisabWasl : Hisab MsylWasl 0 where
  Q := QM FLm
  U := 1
  s := sM
  P := fun q => q < 97
  mutakafi := maqta_mutakafi_wasl
  bidaya := by decide
  K := 2
  pot := pM
  mayyit := (· == 7)
  mayyit_sahih := mayyitM FLm rfl
  juhd := potM FLm

/-- ما يُكمل المقطعَ بوزن ‎`n`‎ من الصنف ‎`i`‎ (بطولٍ كافٍ ‎`2n + 1`‎). -/
def m (F : Nat → Bool) (i n : Nat) : Nat := (QM F).C (2 * n + 1) n i

theorem pM_le : ∀ i, pM i ≤ 1 := by intro i; unfold pM; split <;> omega

/-- **الخطوة:** الصنفُ بوزن ‎`n + 1`‎ مجموعُ صفّه: ما وزنُه صفرٌ في الدرجة نفسِها، وما وزنُه واحدٌ في ‎`n`‎. -/
theorem m_khatwa (F : Nat → Bool) (hF : F 7 = false) (i n : Nat) : m F i (n + 1) = (QM F).base (n + 1) i +
    (((QM F).saff i).map fun e => e.2.2 * (if e.1 = 0 then m F e.2.1 (n + 1) else m F e.2.1 n)).sum :=
  (QM F).C_khatwa1 2 1 pM (· == 7) (mayyitM F hF) (potM F) (by decide +kernel) pM_le (wazn1M F) n i

theorem m_dead (F : Nat → Bool) (hF : F 7 = false) (n : Nat) : m F 7 n = 0 :=
  (QM F).mayyit_sifr (· == 7) (mayyitM F hF) _ _ 7 rfl

/-- **صفوفُ الخطوة** لكلّ قبولٍ لا يقبل الممتنع. -/
theorem maqta_khatwa (F : Nat → Bool) (hF : F 7 = false) (n : Nat) :
    m F 0 (n + 1) = 28 * m F 1 n + 56 * m F 2 n ∧
    m F 1 (n + 1) = m F 3 (n + 1) + 28 * m F 5 n ∧
    m F 2 (n + 1) = m F 3 (n + 1) + 27 * m F 5 n ∧
    m F 3 (n + 1) = 28 * m F 5 n ∧
    m F 5 (n + 1) = 28 * m F 6 n ∧
    m F 6 (n + 1) = 0 := by
  have d := m_dead F hF
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
  · rw [m_khatwa F hF]
    simp [QM, saffM, Asnaf.base, d]
    try omega

theorem bidaya_waqf : m FWm 0 0 = 0 ∧ m FWm 1 0 = 2 ∧ m FWm 2 0 = 2 ∧ m FWm 3 0 = 1 ∧ m FWm 5 0 = 1 ∧
    m FWm 6 0 = 1 := by decide +kernel

theorem bidaya_wasl : m FLm 0 0 = 0 ∧ m FLm 1 0 = 2 ∧ m FLm 2 0 = 2 ∧ m FLm 3 0 = 1 ∧ m FLm 5 0 = 1 ∧
    m FLm 6 0 = 0 := by decide +kernel

/-- **العدُّ بالحساب الصنفيّ (الوقف):** عددُ المقاطع بوزن ‎`n`‎ هو العدُّ من صنف الابتداء. -/
theorem lev_waqf (n : Nat) : Msyl.lev 3 0 n = m FWm 0 n :=
  hisabWaqf.lev_eq 3 n (2 * n + 1) (by show 2 * n + 0 ≤ 3 * n; omega)
    (by show 2 * n + 0 ≤ 2 * n + 1; omega)

theorem lev_wasl (n : Nat) : MsylWasl.lev 3 0 n = m FLm 0 n :=
  hisabWasl.lev_eq 3 n (2 * n + 1) (by show 2 * n + 0 ≤ 3 * n; omega)
    (by show 2 * n + 0 ≤ 2 * n + 1; omega)

/-- صفوفُ خطوة المقطع على متتاليةٍ مجرّدة. -/
def KhatwaM (Y : Nat → Nat → Nat) : Prop := ∀ n,
    Y 0 (n + 1) = 28 * Y 1 n + 56 * Y 2 n ∧ Y 1 (n + 1) = Y 3 (n + 1) + 28 * Y 5 n ∧
    Y 2 (n + 1) = Y 3 (n + 1) + 27 * Y 5 n ∧ Y 3 (n + 1) = 28 * Y 5 n ∧ Y 5 (n + 1) = 28 * Y 6 n ∧ Y 6 (n + 1) = 0

/-- **الأوائلُ من صفوف الخطوة:** على ‎`Y₆(0)`‎ (قبولُ الساكنين المعلّقين). -/
theorem awailM (Y : Nat → Nat → Nat) (h : KhatwaM Y) (h0 : Y 0 0 = 0) (h1 : Y 1 0 = 2) (h2 : Y 2 0 = 2)
    (h3 : Y 3 0 = 1) (h5 : Y 5 0 = 1) :
    Y 0 1 = 168 ∧ Y 0 2 = 4648 ∧ Y 0 3 = 130144 * Y 6 0 := by
  obtain ⟨a0, a1, a2, a3, a5, a6⟩ := h 0
  obtain ⟨b0, b1, b2, b3, b5, b6⟩ := h 1
  obtain ⟨c0, c1, c2, c3, c5, c6⟩ := h 2
  simp only [Nat.reduceAdd] at *
  refine ⟨by omega, by omega, by omega⟩

/-- **أعدادُ المقطع موقوفًا عليه:** 168 و4648 و130144. -/
theorem adad_waqf : m FWm 0 1 = 168 ∧ m FWm 0 2 = 4648 ∧ m FWm 0 3 = 130144 := by
  obtain ⟨w0, w1, w2, w3, w5, w6⟩ := bidaya_waqf
  have a := awailM (m FWm) (maqta_khatwa FWm rfl) w0 w1 w2 w3 w5
  rw [w6] at a
  exact a

/-- **أعدادُ المقطع في الوصل:** 168 و4648 وصفر. -/
theorem adad_wasl : m FLm 0 1 = 168 ∧ m FLm 0 2 = 4648 ∧ m FLm 0 3 = 0 := by
  obtain ⟨w0, w1, w2, w3, w5, w6⟩ := bidaya_wasl
  have a := awailM (m FLm) (maqta_khatwa FLm rfl) w0 w1 w2 w3 w5
  rw [w6] at a
  exact a

end HisabMaqta

theorem sl0 : Msyl.lev 3 0 0 = 0 := by rw [HisabMaqta.lev_waqf]; exact HisabMaqta.bidaya_waqf.1
theorem sl1 : Msyl.lev 3 0 1 = 168 := by rw [HisabMaqta.lev_waqf]; exact HisabMaqta.adad_waqf.1
theorem sl2 : Msyl.lev 3 0 2 = 4648 := by rw [HisabMaqta.lev_waqf]; exact HisabMaqta.adad_waqf.2.1
theorem sl3 : Msyl.lev 3 0 3 = 130144 := by rw [HisabMaqta.lev_waqf]; exact HisabMaqta.adad_waqf.2.2
theorem slw1 : MsylWasl.lev 3 0 1 = 168 := by rw [HisabMaqta.lev_wasl]; exact HisabMaqta.adad_wasl.1
theorem slw2 : MsylWasl.lev 3 0 2 = 4648 := by rw [HisabMaqta.lev_wasl]; exact HisabMaqta.adad_wasl.2.1
theorem slw3 : MsylWasl.lev 3 0 3 = 0 := by rw [HisabMaqta.lev_wasl]; exact HisabMaqta.adad_wasl.2.2

/-- **الاستنفادُ في المقطع:** ‎0, 168, 4648, 130144‎ لصامتٍ ‎0, 1, 2, 3‎؛ وفي الوصل ‎0, 168, 4648, 0‎. -/
theorem syl_levels : Msyl.lev 3 0 0 = 0 ∧ Msyl.lev 3 0 1 = 168 ∧ Msyl.lev 3 0 2 = 4648 ∧
    Msyl.lev 3 0 3 = 130144 ∧
    MsylWasl.lev 3 0 1 = 168 ∧ MsylWasl.lev 3 0 2 = 4648 ∧ MsylWasl.lev 3 0 3 = 0 :=
  ⟨sl0, sl1, sl2, sl3, slw1, slw2, slw3⟩

theorem offFrom_four (L : Nat → Nat) : Machine.offFrom L 0 (3 + 1) = L 0 + L 1 + L 2 + L 3 := by
  show L 0 + (L 1 + (L 2 + (L 3 + 0))) = _; omega

theorem eoff : Machine.offFrom (Msyl.lev 3 0) 0 (3 + 1) = 134960 := by
  rw [offFrom_four, sl0, sl1, sl2, sl3]

def sylNum (l : List Nat) : Nat := Msyl.gEnc 3 0 l
def sylOfNum (n : Nat) : List Nat := Msyl.gDecF 3 0 3 n

/-- **ترقيمُ المقطع المرخَّص:** تقابلٌ بين المقاطع التي يرخّصها القانون و‎[0, 134960)‎، متدرّجٌ بالصوامت. -/
theorem syl_numbering :
    (∀ l, Msyl.Lic 0 l → sylOfNum (sylNum l) = l) ∧
    (∀ n, n < 134960 → Msyl.Lic 0 (sylOfNum n) ∧ sylNum (sylOfNum n) = n) ∧
    (∀ l, Msyl.Lic 0 l → Machine.offFrom (Msyl.lev 3 0) 0 (Msyl.wtL 0 l) ≤ sylNum l ∧
      sylNum l < Machine.offFrom (Msyl.lev 3 0) 0 (Msyl.wtL 0 l + 1)) := by
  have g := Msyl.gradedFin 3 0 3 (hK1 Fwaqf hFwaqf) (hW1 Fwaqf hFwaqf)
  exact ⟨g.1, fun n hn => g.2.1 n (by rw [eoff]; exact hn), g.2.2⟩

/-- **المقطعُ المرخَّص أحدُ الستّة، ولا ألفَ فيه فاتحًا ولا مُغلِقًا.** -/
theorem syl_structure (l : List Nat) (h : Msyl.Lic 0 l) :
    ∃ x, Valid x ∧ AlifOK x ∧ chainOf x = l := by
  have hlive : Msyl.runL 0 l ≠ 96 := hFwaqf _ h.2
  have e := run1_live Fwaqf 0 l hlive
  have hrun : run 0 l ≠ 96 := by rw [← e.1]; exact hlive
  cases l with
  | nil => exact absurd h.2 (by decide)
  | cons a rest =>
    have hA : ∀ b ∈ a :: rest, b < 116 := h.1
    have ha : a < 116 ∧ a % 4 < 3 := by
      apply fin_start a (by have := hA a (by simp); omega)
      intro hd; apply hrun; simp only [run, hd, run_dead]
    obtain ⟨x, r, ⟨hx, hxa⟩, heq, hr⟩ := split 0 a rest ha.1 ha.2 hrun
    refine ⟨x, hx, hxa, ?_⟩
    rcases r with _ | ⟨b, r'⟩
    · simpa using heq.symm
    · exfalso
      have hb : b < 116 := hA b (by rw [heq]; simp)
      have hbs := hr b (by simp)
      have hq0 : δ 0 (onsetSym x) ≠ 96 := by
        intro hd; apply hrun; rw [heq, run_append]
        obtain ⟨t, o, k₁, k₂⟩ := x
        have : chainOf (t, o, k₁, k₂) = onsetSym (t, o, k₁, k₂) :: (chainOf (t, o, k₁, k₂)).tail := by
          match t with
          | 0 | 1 | 2 | 3 | 4 => rfl
          | _ + 5 => rfl
        rw [this]; simp only [run, hd, run_dead, δ_big _ (Nat.le_refl 96)]
      have hs := (syl_run x hx hxa 0 hq0).1
      have hpos : 1 ≤ endSt x := by
        unfold endSt; split <;> omega
      have hsame : Msyl.runL 0 (chainOf x) = endSt x := by
        have hl1 : Msyl.runL 0 (chainOf x) ≠ 96 := by
          intro h0; apply hlive; rw [heq, Machine.runL_append, h0]; exact run1_dead Fwaqf _
        exact (run1_live Fwaqf 0 _ hl1).1.trans hs
      apply hlive
      rw [heq, Machine.runL_append, hsame]
      show Msyl.runL (δ1 (endSt x) b) r' = 96
      have : δ1 (endSt x) b = 96 := by
        unfold δ1; rw [if_pos ⟨hpos, hb, by omega⟩]
      rw [this]; exact run1_dead Fwaqf r'

end Law
end SLGE
