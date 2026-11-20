import SLGE.Law

/-!
# الجذرُ والوزنُ والزائد: الكلمةُ رقمُ جذرٍ ورقمُ وزنٍ ورقمُ وحدة — لا رقمُ سلسلة

* **الجذرُ المرخَّص** ‎k‎ حواملَ ليس فيها ألف، ولا يتجاور فيها حاملان مختلفان من مخرجٍ واحد
  (غيرَ حروف العلّة). وهذا **نتيجةُ قانون الوصل**: كلُّ تجاورٍ كهذا يقع في النموذج الكامل ساكنًا قبل متحرّك
  (‎فَعْل‎ للثاني والثالث، و‎يَفْعَل‎ للأوّل والثاني) فيمتنع. عددُها: ‎20,430‎ ثلاثيًّا، ‎552,078‎ رباعيًّا،
  ‎14,918,778‎ خماسيًّا — بترقيمٍ تقابليّ.
* **الوزنُ المجرّد** حالاتُ الحوامل إلّا الأخير: ‎12, 45, 171‎ — ما لا يلتقي فيه ساكنان.
* **الميزانُ لا يُختار:** كلُّ جذرٍ مرخَّصٍ صحيح يسير على كلّ وزنٍ سيرَ الميزان (بالمخارج والتجاور).
* **الزائدُ وحدةٌ مرخَّصةٌ سابقًا:** سلسلةٌ من حروف «سألتمونيها» يرخّصها القانون وحدَها، مرقَّمةٌ بدرجتها:
  ‎54‎ وحدةً بصامتٍ واحد، ‎3,384‎ بصامتين. والمزيدُ بوحدةٍ سابقةٍ واحدة = توافيقُ الوحدة مع الوزن: ‎729‎.
* **منعُ التضخّم:** رقمُ الكلمة = رقمُ الجذر × عددُ الأوزان + رقمُ الوزن.
-/

namespace SLGE
namespace Law

/-! ## السلسلة من الجذر والوزن -/

def rootChain (r ss : List Nat) : List Nat := (r.zip (ss ++ [0])).map fun p => 4 * p.1 + p.2

def allSt : Nat → List (List Nat)
  | 0 => [[]]
  | n + 1 => (List.range 4).flatMap fun s => (allSt n).map (s :: ·)

/-- حالاتُ ‎k-1‎ حاملًا: الأوّلُ متحرّك. -/
def stK (k : Nat) : List (List Nat) := (List.range 3).flatMap fun s => (allSt (k - 2)).map (s :: ·)

/-- الميزان: ‎ف=25، ع=3، ل=13‎. -/
def mizan : Nat → List Nat
  | 3 => [25, 3, 13]
  | 4 => [25, 3, 13, 13]
  | _ => [25, 3, 13, 13, 13]

def waznList (k : Nat) : List (List Nat) :=
  (stK k).filter fun ss => Fwasl (run 0 (rootChain (mizan k) ss))

def W (k : Nat) : Nat := (waznList k).length

/-- لا يلتقي ساكنان. -/
def noSS : List Nat → Bool
  | a :: b :: l => !(a == 3 && b == 3) && noSS (b :: l)
  | _ => true

/-- **الاستنفادُ في الوزن المجرّد:** ‎12, 45, 171‎. -/
theorem wazn_counts : W 3 = 12 ∧ W 4 = 45 ∧ W 5 = 171 := by decide +kernel

/-- **الوزنُ المرخَّص هو الذي لا يلتقي فيه ساكنان** — نتيجةُ قانون الوصل لا قيدٌ مضاف. -/
theorem wazn_char : (∀ ss ∈ stK 3, Fwasl (run 0 (rootChain (mizan 3) ss)) = noSS ss) ∧
    (∀ ss ∈ stK 4, Fwasl (run 0 (rootChain (mizan 4) ss)) = noSS ss) ∧
    (∀ ss ∈ stK 5, Fwasl (run 0 (rootChain (mizan 5) ss)) = noSS ss) := by decide +kernel

/-! ## الجذرُ المرخَّص: الألفُ لا تكون أصلًا، ولا يتجاور مختلفان من مخرج -/

def δr (q c : Nat) : Nat :=
  if 30 ≤ q ∨ 29 ≤ c ∨ c = 2 then 30 else if q = 0 then c + 1
  else if conflict (q - 1) c then 30 else c + 1

def Mroot : Machine := ⟨29, δr, fun _ _ => 1, fun q => decide (1 ≤ q ∧ q ≤ 29)⟩

theorem root_wt : ∀ (q : Nat) (l : List Nat), Mroot.wtL q l = l.length
  | _, [] => rfl
  | q, a :: l => by
    show 1 + Mroot.wtL (δr q a) l = l.length + 1
    rw [root_wt (δr q a) l]; omega

theorem root_hK : ∀ l, Mroot.Lic 0 l → l.length ≤ 3 * Mroot.wtL 0 l := by
  intro l _; rw [root_wt]; omega

theorem root_close : ∀ q < 31, ∀ a < Mroot.A, Mroot.δ q a < 31 := by
  show ∀ q < 31, ∀ a < 29, δr q a < 31
  decide +kernel

/-! ### الحسابُ الصنفيّ للجذر (`SLGE/HisabSinfi.lean`)

أُضيف بإذن المالك في الجلسة (2026-11-01؛ اختار «عدّل SLGE نفسَها»، انظر رأس `SLGE/HisabSinfi.lean`)، منقولًا من `Dal/WiladaJadhr.lean`
(#119)، لتُبرهَن به أعدادُ الجذر بعده (`root3`، `root4`، `root5`) — وكانت بالجدول `tab` (`root_lev_tab`، حُذف). صنفُ الحامل عددُ ما
يتجاور معه من الحوامل غيرِ الألف (`sinfT`، `SLGE/Law.lean`)، وحالاتُ الآلة بعد الحامل تتكافأ بصنفه: ‎0‎ ابتداء، و‎1‎–‎3‎ بعد حاملٍ بلا مجاورٍ
وبمجاورٍ وبمجاورَين، و‎4‎ ممتنع. والأصنافُ وصفوفُها تعيينُ البنّاء، يفحصه التكافؤُ نفسُه (`jadhr_mutakafi`)؛ وأعدادُ الجذر الثلاثة تمرّ
بـ `Hisab.lev_eq`.
-/

namespace HisabJadhr

/-- صنفُ حالة الآلة: الابتداء 0، وبعد الحامل ‎`c`‎ ‎`1 + sinf c`‎، والممتنع 4. -/
def sJ (q : Nat) : Nat := if q = 0 then 0 else if q ≤ 29 then 1 + sinfT.getD (q - 1) 0 else 4

/-- **صفوفُ الأصناف** (الوزن، الصنفُ الهدف، العدد): بعد الحامل يسقط من صنفه بعددِ ما يجاوره، والألفُ إلى الممتنع. -/
def saffJ : Nat → List (Nat × Nat × Nat)
  | 0 => [(1, 1, 9), (1, 2, 10), (1, 3, 9), (1, 4, 1)]
  | 1 => [(1, 1, 9), (1, 2, 10), (1, 3, 9), (1, 4, 1)]
  | 2 => [(1, 1, 9), (1, 2, 9), (1, 3, 9), (1, 4, 2)]
  | 3 => [(1, 1, 9), (1, 2, 10), (1, 3, 7), (1, 4, 3)]
  | 4 => [(1, 4, 29)]
  | _ => []

def QJ : Asnaf := ⟨5, saffJ, fun i => i == 1 || i == 2 || i == 3⟩

/-- **التكافؤ:** حالاتُ آلة الجذر تتكافأ بأصنافها. -/
theorem jadhr_mutakafi : Mutakafi Mroot QJ 1 sJ (fun q => q < 31) where
  maghluq := fun q hq b hb => root_close q hq b hb
  sinf := by show ∀ q < 31, sJ q < 5; decide +kernel
  wazn := fun _ _ _ _ => Nat.le_refl 1
  saff := by show ∀ q < 31, ∀ e ∈ saffJ (sJ q), e.1 ≤ 1 ∧ e.2.1 < 5; decide +kernel
  qubul := by show ∀ q < 31, decide (1 ≤ q ∧ q ≤ 29) = (sJ q == 1 || sJ q == 2 || sJ q == 3); decide +kernel
  adad := by
    show ∀ q < 31, ∀ u ≤ 1, ∀ j < 5, ((List.range 29).filter fun b => (1 : Nat) == u && sJ (δr q b) == j).length =
      (((saffJ (sJ q)).filter fun e => e.1 == u && e.2.1 == j).map fun e => e.2.2).sum
    decide +kernel

/-- ما يُكمل الجذرَ بطول ‎`n`‎ من الصنف ‎`i`‎. -/
def x (i n : Nat) : Nat := QJ.C n n i

theorem mayyitJ : ∀ i, (i == 4) = true → QJ.F i = false ∧ ∀ e ∈ QJ.saff i, (e.2.1 == 4) = true := by
  intro i hi; simp at hi; subst hi; exact ⟨rfl, by simp [QJ, saffJ]⟩

theorem potJ : ∀ i, (i == 4) = false → ∀ e ∈ QJ.saff i, (e.2.1 == 4) = false →
    (fun _ => 0) e.2.1 + 1 ≤ (fun _ => 0) i + 1 * e.1 := by
  intro i _ e he _
  have : i < 5 ∨ 5 ≤ i := by omega
  rcases this with h | h
  · have : ∀ i < 5, ∀ e ∈ saffJ i, e.1 = 1 := by decide +kernel
    simp only [this i h e he]; omega
  · have : saffJ i = [] := by
      match i, h with
      | n + 5, _ => rfl
    simp [QJ, this] at he

theorem wazn1 : ∀ i, ∀ e ∈ QJ.saff i, e.1 ≤ 1 := by
  intro i e he
  have : i < 5 ∨ 5 ≤ i := by omega
  rcases this with h | h
  · have : ∀ i < 5, ∀ e ∈ saffJ i, e.1 ≤ 1 := by decide +kernel
    exact this i h e he
  · have : saffJ i = [] := by
      match i, h with
      | n + 5, _ => rfl
    simp [QJ, this] at he

/-- **الحسابُ الصنفيّ للجذر:** الأصنافُ الخمسة، والجهدُ صفرٌ بثابتٍ ‎1‎، والممتنعُ ميّت. -/
def hisabJadhr : Hisab Mroot 0 where
  Q := QJ
  U := 1
  s := sJ
  P := fun q => q < 31
  mutakafi := jadhr_mutakafi
  bidaya := by decide
  K := 1
  pot := fun _ => 0
  mayyit := (· == 4)
  mayyit_sahih := mayyitJ
  juhd := potJ

/-- **العدُّ بالحساب الصنفيّ:** عددُ الجذور بطول ‎`n`‎ هو العدُّ من صنف الابتداء. -/
theorem lev_jadhr (n : Nat) : Mroot.lev 3 0 n = x 0 n :=
  hisabJadhr.lev_eq 3 n n (by show 1 * n + 0 ≤ 3 * n; omega) (by show 1 * n + 0 ≤ n; omega)

theorem x_dead (n : Nat) : x 4 n = 0 := QJ.mayyit_sifr (· == 4) mayyitJ n n 4 rfl

/-- **الخطوة:** كلُّ صنفٍ بطول ‎`n + 1`‎ مجموعُ صفّه على الأصناف بطول ‎`n`‎. -/
theorem x_khatwa (i n : Nat) : x i (n + 1) = QJ.base (n + 1) i +
    ((QJ.saff i).map fun e => e.2.2 * (if e.1 = 0 then x e.2.1 (n + 1) else x e.2.1 n)).sum := by
  have := QJ.C_khatwa1 1 0 (fun _ => 0) (· == 4) mayyitJ potJ (Nat.le_refl 1) (fun _ => Nat.le_refl 0) wazn1 n i
  simp only [Nat.one_mul, Nat.add_zero] at this
  exact this

theorem x_bidaya (i : Nat) : x i 0 = QJ.base 0 i := rfl

theorem jadhr_khatwa (n : Nat) :
    x 0 (n + 1) = 9 * x 1 n + 10 * x 2 n + 9 * x 3 n ∧
    x 1 (n + 1) = 9 * x 1 n + 10 * x 2 n + 9 * x 3 n ∧
    x 2 (n + 1) = 9 * x 1 n + 9 * x 2 n + 9 * x 3 n ∧
    x 3 (n + 1) = 9 * x 1 n + 10 * x 2 n + 7 * x 3 n := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;>
  · rw [x_khatwa]
    simp [QJ, saffJ, Asnaf.base, x_dead]
    omega

theorem jadhr_shahid : x 1 0 = 1 ∧ x 2 0 = 1 ∧ x 3 0 = 1 := by decide +kernel

/-- صفوفُ خطوة الجذر على متتاليةٍ مجرّدة. -/
def KhatwaJ (X : Nat → Nat → Nat) : Prop := ∀ n,
    X 0 (n + 1) = 9 * X 1 n + 10 * X 2 n + 9 * X 3 n ∧
    X 1 (n + 1) = 9 * X 1 n + 10 * X 2 n + 9 * X 3 n ∧
    X 2 (n + 1) = 9 * X 1 n + 9 * X 2 n + 9 * X 3 n ∧
    X 3 (n + 1) = 9 * X 1 n + 10 * X 2 n + 7 * X 3 n

/-- **الأوائلُ من صفوف الخطوة:** 28 و756 و20430 و552078 و14918778. -/
theorem awailJ (X : Nat → Nat → Nat) (h : KhatwaJ X) (h1 : X 1 0 = 1) (h2 : X 2 0 = 1) (h3 : X 3 0 = 1) :
    X 0 1 = 28 ∧ X 0 2 = 756 ∧ X 0 3 = 20430 ∧ X 0 4 = 552078 ∧ X 0 5 = 14918778 := by
  obtain ⟨a0, a1, a2, a3⟩ := h 0
  obtain ⟨b0, b1, b2, b3⟩ := h 1
  obtain ⟨c0, c1, c2, c3⟩ := h 2
  obtain ⟨d0, d1, d2, d3⟩ := h 3
  obtain ⟨e0, e1, e2, e3⟩ := h 4
  simp only [Nat.reduceAdd] at *
  refine ⟨by omega, by omega, by omega, by omega, by omega⟩

/-- **أعدادُ الجذر بالحساب الصنفيّ.** -/
theorem adad_jadhr : x 0 1 = 28 ∧ x 0 2 = 756 ∧ x 0 3 = 20430 ∧ x 0 4 = 552078 ∧ x 0 5 = 14918778 :=
  awailJ x jadhr_khatwa jadhr_shahid.1 jadhr_shahid.2.1 jadhr_shahid.2.2

end HisabJadhr

/-- **الاستنفادُ في الجذر:** ‎20,430‎ ثلاثيًّا من ‎21,952‎، و‎552,078‎ رباعيًّا، و‎14,918,778‎ خماسيًّا. -/
theorem root3 : Mroot.lev 3 0 3 = 20430 := by rw [HisabJadhr.lev_jadhr]; exact HisabJadhr.adad_jadhr.2.2.1
theorem root4 : Mroot.lev 3 0 4 = 552078 := by rw [HisabJadhr.lev_jadhr]; exact HisabJadhr.adad_jadhr.2.2.2.1
theorem root5 : Mroot.lev 3 0 5 = 14918778 := by rw [HisabJadhr.lev_jadhr]; exact HisabJadhr.adad_jadhr.2.2.2.2

/-- **رقمُ الجذر:** الجذورُ المرخَّصة بطول ‎k‎ تقابل ‎[0, lev k)‎ بالرتبة. -/
theorem root_numbering (k : Nat) :
    (∀ r, Mroot.Lic 0 r → r.length = k → Mroot.rank (3 * k) k 0 r < Mroot.lev 3 0 k) ∧
    (∀ r r', Mroot.Lic 0 r → Mroot.Lic 0 r' → r.length = k → r'.length = k →
      Mroot.rank (3 * k) k 0 r = Mroot.rank (3 * k) k 0 r' → r = r') ∧
    (∀ i, i < Mroot.lev 3 0 k → ∃ r, Mroot.Lic 0 r ∧ r.length = k ∧ Mroot.rank (3 * k) k 0 r = i) := by
  have h := Mroot.level_count 3 0 k root_hK
  refine ⟨fun r hr hl => h.1 r hr (by rw [root_wt, hl]), fun r r' hr hr' hl hl' =>
    h.2.1 r r' hr hr' (by rw [root_wt, hl]) (by rw [root_wt, hl']), fun i hi => ?_⟩
  obtain ⟨r, hr, hw, hrk⟩ := h.2.2 i hi
  exact ⟨r, hr, by rw [root_wt] at hw; exact hw, hrk⟩

set_option synthInstance.maxHeartbeats 0 in
set_option synthInstance.maxSize 4096 in
/-- **التجاورُ نتيجةُ الوصل:** ساكنٌ مُغلِق ثمّ متحرّكٌ مختلفٌ من مخرجه يمتنع بعد أيّ متحرّك؛
فالجذرُ الذي يتجاور فيه اثنان كهذين يمتنع في ‎فَعْل‎ (الثاني والثالث) وفي ‎يَفْعَل‎ (الأوّل والثاني). -/
theorem tajawur_root : ∀ h < 3, ∀ a < 29, ∀ b < 29, (conflict a b = true ∧ a ≠ 2) → ∀ s < 3,
    δ (δ (1 + h) (4 * a + 3)) (4 * b + s) = 96 := by decide +kernel

/-! ## الجذرُ المرخَّص الصحيح يسير سيرَ الميزان -/

/-- صورةُ الحالة: المُغلِقاتُ كلُّها صورةٌ واحدة. -/
def shape (q : Nat) : Nat := if 67 ≤ q ∧ q < 96 then 67 else q

def Rs (q : Nat) : Bool := q == 0 || q == 1 || q == 2 || q == 3 || (67 ≤ q && q < 96) || q == 35 || q == 96

def sig (p s : Nat) : Nat := shape (δ p (4 * 25 + s))

def closedOK (q c : Nat) : Bool := !(67 ≤ q && q < 96) || !conflict (q - 67) c

def weakC (c : Nat) : Prop := c = 2 ∨ c = 11 ∨ c = 28

set_option synthInstance.maxHeartbeats 0 in
set_option synthInstance.maxSize 4096 in
theorem fin_shape : ∀ q < 97, ∀ c < 29, ∀ s < 4,
    (Rs q = true ∧ c ≠ 2 ∧ c ≠ 11 ∧ c ≠ 28 ∧ closedOK q c = true) →
    shape (δ q (4 * c + s)) = sig (shape q) s ∧ Rs (δ q (4 * c + s)) = true ∧
    (67 ≤ δ q (4 * c + s) ∧ δ q (4 * c + s) < 96 → δ q (4 * c + s) = 67 + c) := by decide +kernel

theorem fin_shapeF : ∀ q < 97, Rs q = true → Fwasl q = Fwasl (shape q) := by decide +kernel

theorem Rs_lt (q : Nat) (h : Rs q = true) : q < 97 := by simp [Rs] at h; omega

def Spaced : List Nat → Prop
  | a :: b :: l => conflict a b = false ∧ Spaced (b :: l)
  | _ => True

def SoundR (r : List Nat) : Prop := ∀ c ∈ r, c < 29 ∧ c ≠ 2 ∧ c ≠ 11 ∧ c ≠ 28

theorem shape_run : ∀ (r ss : List Nat) (q : Nat), Rs q = true → SoundR r → Spaced r →
    (∀ s ∈ ss, s < 4) → (∀ c ∈ r.head?, closedOK q c = true) →
    shape (run q ((r.zip ss).map fun p => 4 * p.1 + p.2)) = ((ss.take r.length).foldl sig (shape q)) ∧
    Rs (run q ((r.zip ss).map fun p => 4 * p.1 + p.2)) = true
  | [], ss, q, hq, _, _, _, _ => by cases ss <;> simp [run, hq]
  | _ :: _, [], q, hq, _, _, _, _ => by simp [run, hq]
  | c :: r, s :: ss, q, hq, hr, hsp, hs, hc => by
    have hcs := hr c (by simp)
    have h4 := hs s (by simp)
    have f := fin_shape q (Rs_lt q hq) c hcs.1 s h4 ⟨hq, hcs.2.1, hcs.2.2.1, hcs.2.2.2, hc c (by simp)⟩
    have hsp' : Spaced r := by
      cases r with
      | nil => trivial
      | cons d r => exact hsp.2
    have hc' : ∀ d ∈ r.head?, closedOK (δ q (4 * c + s)) d = true := by
      intro d hd
      cases r with
      | nil => simp at hd
      | cons e r =>
        simp at hd; subst hd
        unfold closedOK
        by_cases hcl : 67 ≤ δ q (4 * c + s) ∧ δ q (4 * c + s) < 96
        · rw [f.2.2 hcl]; simp [hsp.1]
        · simp [hcl]; omega
    have ih := shape_run r ss (δ q (4 * c + s)) f.2.1 (fun d hd => hr d (by simp [hd])) hsp'
      (fun t ht => hs t (by simp [ht])) hc'
    simp only [List.zip_cons_cons, List.map_cons, run, List.length_cons, List.take_succ_cons,
      List.foldl_cons]
    rw [← f.1]; exact ih

/-- من حالةٍ ليست مُغلِقة، جذران صحيحان لا تجاورَ فيهما يسيران على الحالات نفسِها سيرًا واحدًا. -/
theorem wazn_from (q : Nat) (hq : Rs q = true) (hq67 : q < 67) (r m ss : List Nat)
    (hr : SoundR r) (hsp : Spaced r) (hm : SoundR m) (hmsp : Spaced m)
    (hlen : r.length = m.length) (hs : ∀ s ∈ ss, s < 4) :
    Fwasl (run q (rootChain r ss)) = Fwasl (run q (rootChain m ss)) := by
  have hs' : ∀ t ∈ ss ++ [0], t < 4 := by
    intro t ht; simp at ht; rcases ht with h | h
    · exact hs t h
    · omega
  have hc : ∀ c, closedOK q c = true := by intro c; unfold closedOK; simp; omega
  have a := shape_run r (ss ++ [0]) q hq hr hsp hs' (fun c _ => hc c)
  have b := shape_run m (ss ++ [0]) q hq hm hmsp hs' (fun c _ => hc c)
  unfold rootChain
  rw [fin_shapeF _ (Rs_lt _ a.2) a.2, fin_shapeF _ (Rs_lt _ b.2) b.2, a.1, b.1, hlen]

theorem mizan_ok (k : Nat) : SoundR (mizan k) ∧ Spaced (mizan k) := by
  unfold mizan; split <;> exact ⟨by unfold SoundR; decide, by simp only [Spaced]; decide⟩

/-- **الميزانُ لا يُختار:** كلُّ جذرٍ صحيحٍ لا تجاورَ فيه يرخّصه الوزنُ كما يرخّص الميزان. -/
theorem wazn_any_root (k : Nat) (r ss : List Nat) (hr : SoundR r) (hsp : Spaced r)
    (hlen : r.length = (mizan k).length) (hs : ∀ s ∈ ss, s < 4) :
    Fwasl (run 0 (rootChain r ss)) = Fwasl (run 0 (rootChain (mizan k) ss)) :=
  wazn_from 0 rfl (by decide) r (mizan k) ss hr hsp (mizan_ok k).1 (mizan_ok k).2 hlen hs

/-! ## رقمُ الكلمة المجرّدة: رقمُ الجذر المرخَّص × عددُ الأوزان + رقمُ الوزن -/

def mujEnc (k : Nat) (r ss : List Nat) : Nat := Mroot.rank (3 * k) k 0 r * W k + (waznList k).idxOf ss
def mujDec (k n : Nat) : List Nat × List Nat :=
  (Mroot.unrank (3 * k) k 0 (n / W k), (waznList k).getD (n % W k) [])

theorem idx_ok (k : Nat) (hk : k = 3 ∨ k = 4 ∨ k = 5) :
    (∀ i < W k, (waznList k).idxOf ((waznList k).getD i []) = i) ∧
    (∀ ss ∈ waznList k, (waznList k).idxOf ss < W k ∧
      (waznList k).getD ((waznList k).idxOf ss) [] = ss) := by
  rcases hk with rfl | rfl | rfl <;> decide +kernel

theorem W_pos (k : Nat) (hk : k = 3 ∨ k = 4 ∨ k = 5) : 0 < W k := by
  rcases hk with rfl | rfl | rfl <;> decide +kernel

theorem root_acc (k : Nat) (r : List Nat) (hr : Mroot.Lic 0 r) (hl : r.length = k) :
    Mroot.Acc (3 * k) k 0 r :=
  (Mroot.acc_iff r _ _ _).2 ⟨hr.1, by omega, by rw [root_wt, hl], hr.2⟩

/-- **رقمُ الكلمة المجرّدة تقابل** بين (جذرٍ مرخَّصٍ بطول ‎k‎، وزنٍ مرخَّص) و‎[0, lev k · W k)‎. -/
theorem muj_numbering (k : Nat) (hk : k = 3 ∨ k = 4 ∨ k = 5) :
    (∀ r ss, Mroot.Lic 0 r → r.length = k → ss ∈ waznList k →
      mujDec k (mujEnc k r ss) = (r, ss) ∧ mujEnc k r ss < Mroot.lev 3 0 k * W k) ∧
    (∀ n, n < Mroot.lev 3 0 k * W k →
      Mroot.Lic 0 (mujDec k n).1 ∧ (mujDec k n).1.length = k ∧ (mujDec k n).2 ∈ waznList k ∧
      mujEnc k (mujDec k n).1 (mujDec k n).2 = n) := by
  have hW := W_pos k hk
  obtain ⟨i1, i2⟩ := idx_ok k hk
  constructor
  · intro r ss hr hl hss
    obtain ⟨j1, j2⟩ := i2 ss hss
    have ha := root_acc k r hr hl
    have hlt := Mroot.rank_lt r _ _ _ ha
    have e1 : (Mroot.rank (3 * k) k 0 r * W k + (waznList k).idxOf ss) / W k = Mroot.rank (3 * k) k 0 r := by
      rw [Nat.add_comm, Nat.add_mul_div_right _ _ hW, Nat.div_eq_of_lt j1]; omega
    have e2 : (Mroot.rank (3 * k) k 0 r * W k + (waznList k).idxOf ss) % W k = (waznList k).idxOf ss := by
      rw [Nat.add_comm, Nat.add_mul_mod_self_right, Nat.mod_eq_of_lt j1]
    refine ⟨?_, ?_⟩
    · simp only [mujDec, mujEnc, e1, e2, j2, Mroot.unrank_rank r _ _ _ ha]
    · unfold mujEnc Machine.lev
      have : Mroot.rank (3 * k) k 0 r * W k + W k ≤ Mroot.C (3 * k) k 0 * W k := by
        have := Nat.mul_le_mul_right (W k) (Nat.succ_le_of_lt hlt)
        rw [Nat.succ_mul] at this; exact this
      omega
  · intro n hn
    have hq : n / W k < Mroot.lev 3 0 k := by rw [Nat.div_lt_iff_lt_mul hW]; exact hn
    obtain ⟨hA, hR⟩ := Mroot.unrank_spec _ _ _ _ hq
    have hl := (Mroot.acc_iff _ _ _ _).1 hA
    have hm : n % W k < W k := Nat.mod_lt _ hW
    have hmem : (waznList k).getD (n % W k) [] ∈ waznList k := by
      rw [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem hm, Option.getD_some]
      exact List.getElem_mem hm
    refine ⟨⟨hl.1, hl.2.2.2⟩, ?_, hmem, ?_⟩
    · show (Mroot.unrank (3 * k) k 0 (n / W k)).length = k
      rw [← root_wt 0]; exact hl.2.2.1
    simp only [mujDec, mujEnc, hR, i1 _ hm]
    exact Nat.div_add_mod' n (W k)

/-- **منعُ التضخّم:** المجرّداتُ الثلاثيّةُ المرخَّصة ‎245,160‎ (‎20,430 × 12‎). -/
theorem muj_size3 : Mroot.lev 3 0 3 * W 3 = 245160 := by rw [root3, wazn_counts.1]

/-! ## الزائدُ وحدةٌ مرخَّصةٌ سابقًا -/

/-- حروفُ «سألتمونيها»: ‎س ء ل ت م و ن ي ه ا‎. -/
def augs : List Nat := [20, 0, 13, 18, 27, 28, 14, 11, 1, 2]

def isAug (c : Nat) : Bool := augs.contains c

def δa (q a : Nat) : Nat := if isAug (a / 4) then δ q a else 96

/-- الوحدةُ: سلسلةٌ من الزوائد يرخّصها القانونُ وحدَها، وتقبل أن يليها (الوصل). -/
def Maug : Machine := ⟨116, δa, ω, Fwasl⟩

theorem aug_close : ∀ q < 97, ∀ a < Maug.A, Maug.δ q a < 97 := by
  show ∀ q < 97, ∀ a < 116, δa q a < 97
  decide +kernel

/-! ### الحسابُ الصنفيّ للزوائد (`SLGE/HisabSinfi.lean`)

أُضيف بإذن المالك في الجلسة (2026-11-01؛ اختار «عدّل SLGE نفسَها»، انظر رأس `SLGE/HisabSinfi.lean`) لتُبرهَن به عددا الوحدات بعده
(`units1`، `units2`) — وكانا بالجدول `tab` (`aug_lev_tab`، حُذف). حالاتُ آلة الزوائد السبعُ والتسعون تتكافأ في عشرة أصناف (`HisabZaid.sA`):
‎0‎ ابتداء (ومعه ‎37‎)، ‎1‎ بعد مفتوح، ‎2‎ بعد مضمومٍ أو مكسور، ‎3‎ بعد مدّ، ‎4‎ مدٌّ ثمّ ساكنٌ ليس من الزوائد أو ألف (ومعه الحالةُ ‎5‎)،
‎5‎ مدٌّ ثمّ ساكنٌ من الزوائد غيرِ الألف، ‎6‎ ممتنع (ومعه ‎35‎ و‎36‎ والحدُّ بعد ‎4‎)، ‎7‎ حدٌّ بعد ‎5‎، ‎8‎ و‎9‎ بعد ساكنٍ مُغلِقٍ يجاوره من الزوائد
غيرِ الألف واحدٌ أو لا شيء (`sinfA`). والأصنافُ وصفوفُها وجهدُها تعيينُ البنّاء، يفحصه التكافؤُ نفسُه (`zaid_mutakafi`)؛ وعددا الوحدات يمرّان
بـ `Hisab.lev_eq`. أمّا `unitList1_ok` و`mazidU1_count` بعده فعدُّ قائمةٍ بـ decide (`hawkama/الحساب_الصنفي.md` §٥).
-/

namespace HisabZaid
open HisabKalima (waznK)

/-- جدولُ صنف الحامل بين الزوائد: عددُ حروف «سألتمونيها» غيرِ الألف التي تتجاور معه (`sinfA_sinf`). -/
def sinfA : List Nat := [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0]

theorem sinfA_sinf : ∀ c < 29, sinfA.getD c 0 = (augs.filter fun b => b != 2 && conflict c b).length := by
  decide +kernel

/-- صنفُ حالة الزوائد. -/
def sA (q : Nat) : Nat :=
  if q = 0 ∨ q = 37 then 0 else if q = 1 then 1 else if q ≤ 3 then 2 else if q = 4 then 3 else if q = 5 then 4
  else if q ≤ 34 then (if isAug (q - 6) && q - 6 != 2 then 5 else 4)
  else if q ≤ 36 then 6
  else if q ≤ 66 then (if isAug (q - 38) && q - 38 != 2 then 7 else 6)
  else if q ≤ 95 then (if sinfA.getD (q - 67) 0 = 1 then 8 else 9) else 6

/-- **صفوفُ الأصناف** (الوزن، الصنفُ الهدف، العدد) على الخانات الـ116. -/
def saffA : Nat → List (Nat × Nat × Nat)
  | 0 => [(1, 1, 9), (1, 2, 18), (1, 6, 89)]
  | 1 => [(0, 3, 1), (1, 1, 9), (1, 2, 18), (1, 6, 79), (1, 8, 2), (1, 9, 7)]
  | 2 => [(0, 3, 1), (1, 1, 9), (1, 2, 18), (1, 6, 80), (1, 8, 2), (1, 9, 6)]
  | 3 => [(1, 1, 9), (1, 2, 18), (1, 5, 9), (1, 6, 80)]
  | 4 => [(1, 6, 116)]
  | 5 => [(1, 1, 1), (1, 2, 2), (1, 6, 113)]
  | 6 => [(1, 6, 116)]
  | 7 => [(1, 1, 1), (1, 2, 2), (1, 6, 113)]
  | 8 => [(1, 1, 8), (1, 2, 16), (1, 6, 92)]
  | 9 => [(1, 1, 9), (1, 2, 18), (1, 6, 89)]
  | _ => []

/-- القبولُ في الوصل: كلُّ صنفٍ إلّا الابتداءَ والممتنعَ والحدّ. -/
def FA (i : Nat) : Bool := !(i == 0 || i == 6 || i == 7)

def QA : Asnaf := ⟨10, saffA, FA⟩

theorem sinfAq : ∀ q < 97, sA q < 10 := by decide +kernel
theorem saffA_hadd : ∀ q < 97, ∀ e ∈ saffA (sA q), e.1 ≤ 1 ∧ e.2.1 < 10 := by decide +kernel
/-- ما يُفحص لكلّ حالة: عددُ انتقالاتها بكلّ وزنٍ إلى كلّ صنفٍ هو ما في صفّ صنفها. -/
abbrev ShartA (q : Nat) : Prop := ∀ u ≤ 1, ∀ j < 10,
    ((List.range 116).filter fun b => ω q b == u && sA (δa q b) == j).length =
      (((saffA (sA q)).filter fun e => e.1 == u && e.2.1 == j).map fun e => e.2.2).sum

private theorem ShartA_0 : ∀ r < 8, ShartA (r + 0) := by decide +kernel
private theorem ShartA_1 : ∀ r < 8, ShartA (r + 8) := by decide +kernel
private theorem ShartA_2 : ∀ r < 8, ShartA (r + 16) := by decide +kernel
private theorem ShartA_3 : ∀ r < 8, ShartA (r + 24) := by decide +kernel
private theorem ShartA_4 : ∀ r < 8, ShartA (r + 32) := by decide +kernel
private theorem ShartA_5 : ∀ r < 8, ShartA (r + 40) := by decide +kernel
private theorem ShartA_6 : ∀ r < 8, ShartA (r + 48) := by decide +kernel
private theorem ShartA_7 : ∀ r < 8, ShartA (r + 56) := by decide +kernel
private theorem ShartA_8 : ∀ r < 8, ShartA (r + 64) := by decide +kernel
private theorem ShartA_9 : ∀ r < 8, ShartA (r + 72) := by decide +kernel
private theorem ShartA_10 : ∀ r < 8, ShartA (r + 80) := by decide +kernel
private theorem ShartA_11 : ∀ r < 8, ShartA (r + 88) := by decide +kernel
private theorem ShartA_12 : ∀ r < 1, ShartA (r + 96) := by decide +kernel

theorem adadA : ∀ q < 97, ShartA q := by
  intro q hq
  have h : q < 8 ∨ (8 ≤ q ∧ q < 16) ∨ (16 ≤ q ∧ q < 24) ∨ (24 ≤ q ∧ q < 32) ∨ (32 ≤ q ∧ q < 40) ∨ (40 ≤ q ∧ q < 48) ∨ (48 ≤ q ∧ q < 56) ∨ (56 ≤ q ∧ q < 64) ∨ (64 ≤ q ∧ q < 72) ∨ (72 ≤ q ∧ q < 80) ∨ (80 ≤ q ∧ q < 88) ∨ (88 ≤ q ∧ q < 96) ∨ (96 ≤ q ∧ q < 97) := by omega
  rcases h with h | h | h | h | h | h | h | h | h | h | h | h | h
  · have := ShartA_0 q h; rwa [Nat.add_zero] at this
  · have := ShartA_1 (q - 8) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartA_2 (q - 16) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartA_3 (q - 24) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartA_4 (q - 32) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartA_5 (q - 40) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartA_6 (q - 48) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartA_7 (q - 56) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartA_8 (q - 64) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartA_9 (q - 72) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartA_10 (q - 80) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartA_11 (q - 88) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this
  · have := ShartA_12 (q - 96) (by omega); rwa [Nat.sub_add_cancel (by omega)] at this

/-- **التكافؤ:** حالاتُ آلة الزوائد تتكافأ في عشرة أصناف. -/
theorem zaid_mutakafi : Mutakafi Maug QA 1 sA (fun q => q < 97) where
  maghluq := fun q hq b hb => aug_close q hq b hb
  sinf := sinfAq
  wazn := fun q hq b hb => waznK q hq b hb
  saff := saffA_hadd
  qubul := by show ∀ q < 97, Fwasl q = FA (sA q); decide +kernel
  adad := adadA

/-- الجهد: يكفي الصنفَ طولُ ‎`2·w + pA i`‎. -/
def pA (i : Nat) : Nat := if i = 1 ∨ i = 2 then 1 else 0

theorem saffA_kabir (i : Nat) (h : 10 ≤ i) : saffA i = [] := by
  match i, h with
  | n + 10, _ => rfl

theorem mayyitA : ∀ i, (i == 6) = true → QA.F i = false ∧ ∀ e ∈ QA.saff i, (e.2.1 == 6) = true := by
  intro i hi; simp at hi; subst hi
  exact ⟨rfl, by simp [QA, saffA]⟩

theorem potA : ∀ i, (i == 6) = false → ∀ e ∈ QA.saff i, (e.2.1 == 6) = false → pA e.2.1 + 1 ≤ pA i + 2 * e.1 := by
  intro i hi e he hj
  have : i < 10 ∨ 10 ≤ i := by omega
  rcases this with h | h
  · have k : ∀ i < 10, (i == 6) = false → ∀ e ∈ saffA i, (e.2.1 == 6) = false → pA e.2.1 + 1 ≤ pA i + 2 * e.1 := by
      decide +kernel
    exact k i h hi e he hj
  · simp [QA, saffA_kabir i h] at he

theorem wazn1A : ∀ i, ∀ e ∈ QA.saff i, e.1 ≤ 1 := by
  intro i e he
  have : i < 10 ∨ 10 ≤ i := by omega
  rcases this with h | h
  · have k : ∀ i < 10, ∀ e ∈ saffA i, e.1 ≤ 1 := by decide +kernel
    exact k i h e he
  · simp [QA, saffA_kabir i h] at he

/-- **الحسابُ الصنفيّ للزوائد:** الأصنافُ العشرة، والجهدُ ‎`pA`‎ بثابتٍ ‎2‎، والممتنعُ ميّت. -/
def hisabZaid : Hisab Maug 0 where
  Q := QA
  U := 1
  s := sA
  P := fun q => q < 97
  mutakafi := zaid_mutakafi
  bidaya := by decide
  K := 2
  pot := pA
  mayyit := (· == 6)
  mayyit_sahih := mayyitA
  juhd := potA

/-- ما يُكمل الوحدةَ بوزن ‎`n`‎ من الصنف ‎`i`‎ (بطولٍ كافٍ ‎`2n + 1`‎). -/
def v (i n : Nat) : Nat := QA.C (2 * n + 1) n i

theorem pA_le : ∀ i, pA i ≤ 1 := by intro i; unfold pA; split <;> omega

theorem v_khatwa (i n : Nat) : v i (n + 1) = QA.base (n + 1) i +
    ((QA.saff i).map fun e => e.2.2 * (if e.1 = 0 then v e.2.1 (n + 1) else v e.2.1 n)).sum :=
  QA.C_khatwa1 2 1 pA (· == 6) mayyitA potA (by decide +kernel) pA_le wazn1A n i

theorem v_dead (n : Nat) : v 6 n = 0 := QA.mayyit_sifr (· == 6) mayyitA _ _ 6 rfl

/-- **صفوفُ الخطوة.** -/
theorem zaid_khatwa (n : Nat) :
    v 0 (n + 1) = 9 * v 1 n + 18 * v 2 n ∧
    v 1 (n + 1) = v 3 (n + 1) + 9 * v 1 n + 18 * v 2 n + 2 * v 8 n + 7 * v 9 n ∧
    v 2 (n + 1) = v 3 (n + 1) + 9 * v 1 n + 18 * v 2 n + 2 * v 8 n + 6 * v 9 n ∧
    v 3 (n + 1) = 9 * v 1 n + 18 * v 2 n + 9 * v 5 n ∧
    v 5 (n + 1) = v 1 n + 2 * v 2 n ∧
    v 8 (n + 1) = 8 * v 1 n + 16 * v 2 n ∧
    v 9 (n + 1) = 9 * v 1 n + 18 * v 2 n := by
  have d := v_dead
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
  · rw [v_khatwa]
    simp [QA, saffA, Asnaf.base, d]
    try omega

theorem bidaya_zaid : v 0 0 = 0 ∧ v 1 0 = 2 ∧ v 2 0 = 2 ∧ v 3 0 = 1 ∧ v 5 0 = 1 ∧ v 8 0 = 1 ∧ v 9 0 = 1 := by
  decide +kernel

/-- **العدُّ بالحساب الصنفيّ:** عددُ الوحدات بوزن ‎`n`‎ هو العدُّ من صنف الابتداء. -/
theorem lev_zaid (n : Nat) : Maug.lev 3 0 n = v 0 n :=
  hisabZaid.lev_eq 3 n (2 * n + 1) (by show 2 * n + 0 ≤ 3 * n; omega)
    (by show 2 * n + 0 ≤ 2 * n + 1; omega)

/-- صفوفُ خطوة الزوائد على متتاليةٍ مجرّدة. -/
def KhatwaA (V : Nat → Nat → Nat) : Prop := ∀ n,
    V 0 (n + 1) = 9 * V 1 n + 18 * V 2 n ∧
    V 1 (n + 1) = V 3 (n + 1) + 9 * V 1 n + 18 * V 2 n + 2 * V 8 n + 7 * V 9 n ∧
    V 2 (n + 1) = V 3 (n + 1) + 9 * V 1 n + 18 * V 2 n + 2 * V 8 n + 6 * V 9 n ∧
    V 3 (n + 1) = 9 * V 1 n + 18 * V 2 n + 9 * V 5 n ∧
    V 5 (n + 1) = V 1 n + 2 * V 2 n ∧
    V 8 (n + 1) = 8 * V 1 n + 16 * V 2 n ∧
    V 9 (n + 1) = 9 * V 1 n + 18 * V 2 n

/-- **الأوائلُ من صفوف الخطوة:** 54 و3384. -/
theorem awailA (V : Nat → Nat → Nat) (h : KhatwaA V) (h0 : V 0 0 = 0) (h1 : V 1 0 = 2) (h2 : V 2 0 = 2)
    (h3 : V 3 0 = 1) (h5 : V 5 0 = 1) (h8 : V 8 0 = 1) (h9 : V 9 0 = 1) :
    V 0 1 = 54 ∧ V 0 2 = 3384 := by
  obtain ⟨a0, a1, a2, a3, a5, a8, a9⟩ := h 0
  obtain ⟨b0, b1, b2, b3, b5, b8, b9⟩ := h 1
  simp only [Nat.reduceAdd] at *
  refine ⟨by omega, by omega⟩

/-- **عددا الوحدات بالحساب الصنفيّ.** -/
theorem adad_zaid : v 0 1 = 54 ∧ v 0 2 = 3384 := by
  obtain ⟨w0, w1, w2, w3, w5, w8, w9⟩ := bidaya_zaid
  exact awailA v zaid_khatwa w0 w1 w2 w3 w5 w8 w9

end HisabZaid

/-- **الاستنفادُ في الوحدات:** ‎54‎ وحدةً بصامتٍ واحد، و‎3,384‎ بصامتين. -/
theorem units1 : Maug.lev 3 0 1 = 54 := by rw [HisabZaid.lev_zaid]; exact HisabZaid.adad_zaid.1
theorem units2 : Maug.lev 3 0 2 = 3384 := by rw [HisabZaid.lev_zaid]; exact HisabZaid.adad_zaid.2

/-- الوحداتُ بصامتٍ واحد صريحةً: متحرّكٌ من الزوائد، وبعده مدُّه أو لا. -/
def unitList1 : List (List Nat) :=
  ((augs.flatMap fun c => (List.range 3).map fun h => [4 * c + h]) ++
   (augs.flatMap fun c => (List.range 3).map fun h => [4 * c + h, 4 * maddOf h + 3])).filter
    fun u => Fwasl (run 0 u) && wt 0 u == 1

theorem unitList1_ok : unitList1.length = 54 ∧ unitList1.Nodup ∧
    ∀ u ∈ unitList1, Maug.runL 0 u = run 0 u ∧ Fwasl (run 0 u) = true ∧ wt 0 u = 1 ∧
      ∀ a ∈ u, isAug (a / 4) = true ∧ a < 116 := by decide +kernel

theorem δa_dead (a : Nat) : δa 96 a = 96 := by
  unfold δa; split
  · exact δ_big a (Nat.le_refl 96)
  · rfl

theorem aug_dead : ∀ l, Maug.runL 96 l = 96
  | [] => rfl
  | a :: l => by show Maug.runL (δa 96 a) l = 96; rw [δa_dead]; exact aug_dead l

theorem aug_live : ∀ (q : Nat) (l : List Nat), Maug.runL q l ≠ 96 →
    Maug.runL q l = run q l ∧ Maug.wtL q l = wt q l
  | _, [], _ => ⟨rfl, rfl⟩
  | q, a :: l, h => by
    have hd : δa q a ≠ 96 := by
      intro e; apply h; show Maug.runL (δa q a) l = 96; rw [e]; exact aug_dead l
    have he : δa q a = δ q a := by unfold δa at hd ⊢; split <;> simp_all
    have ih := aug_live (δa q a) l h
    rw [he] at ih
    refine ⟨?_, ?_⟩
    · show Maug.runL (δa q a) l = run (δ q a) l
      rw [he]; exact ih.1
    · show ω q a + Maug.wtL (δa q a) l = ω q a + wt (δ q a) l
      rw [he, ih.2]

def pot2 (q : Nat) : Nat :=
  if q = 0 then 0 else if q ≤ 3 then 1 else if q = 4 then 0 else if q < 35 then 1
  else if q = 35 then 2 else if q = 36 then 1 else if 67 ≤ q ∧ q < 96 then 2 else 0

theorem fin_pot2 : ∀ q < 96, ∀ a < 116, δ q a ≠ 96 → 1 + pot2 (δ q a) ≤ 2 * ω q a + pot2 q := by
  decide +kernel

theorem len_bound2 : ∀ (l : List Nat) (q : Nat), q < 96 → (∀ a ∈ l, a < 116) → run q l ≠ 96 →
    l.length + pot2 (run q l) ≤ 2 * wt q l + pot2 q
  | [], q, _, _, _ => by simp [run, wt]
  | a :: l, q, hq, hl, hr => by
    have hd : δ q a ≠ 96 := fun h => hr (by simp only [run, h, run_dead])
    have hs := fin_pot2 q hq a (hl a (by simp)) hd
    have hle := δ_le q a
    have ih := len_bound2 l (δ q a) (by omega) (fun b hb => hl b (by simp [hb])) hr
    simp only [run, wt, List.length_cons] at ih ⊢
    omega

set_option synthInstance.maxHeartbeats 0 in
set_option synthInstance.maxSize 4096 in
theorem units1_small : ∀ a < 116, ∀ b < 116,
    ((isAug (a / 4) && Fwasl (run 0 [a]) && wt 0 [a] == 1) → [a] ∈ unitList1) ∧
    ((isAug (a / 4) && isAug (b / 4) && Fwasl (run 0 [a, b]) && wt 0 [a, b] == 1) → [a, b] ∈ unitList1) := by
  decide +kernel

/-- **وحداتُ الصامت الواحد مستنفدةٌ صراحةً:** كلُّ وحدةٍ يرخّصها القانونُ بصامتٍ واحد في القائمة، وعددُها ‎54‎. -/
theorem units1_complete (u : List Nat) (hu : Maug.Lic 0 u) (hw : Maug.wtL 0 u = 1) : u ∈ unitList1 := by
  have hlive : Maug.runL 0 u ≠ 96 := fun h => by
    have := hu.2; rw [h] at this; exact absurd this (by decide)
  have e := aug_live 0 u hlive
  have hA : ∀ a ∈ u, a < 116 := hu.1
  have hrun : run 0 u ≠ 96 := by rw [← e.1]; exact hlive
  have hF : Fwasl (run 0 u) = true := by rw [← e.1]; exact hu.2
  have hw' : wt 0 u = 1 := by rw [← e.2]; exact hw
  have hb := len_bound2 u 0 (by decide) hA hrun
  rw [hw'] at hb
  have hlen : u.length ≤ 2 := by simp [pot2] at hb; omega
  have augOf : ∀ (l : List Nat) (q : Nat), Maug.runL q l ≠ 96 → ∀ a ∈ l, isAug (a / 4) = true := by
    intro l
    induction l with
    | nil => intro q _ a ha; simp at ha
    | cons x l ih =>
      intro q h a ha
      have hd : δa q x ≠ 96 := by
        intro e; apply h; show Maug.runL (δa q x) l = 96; rw [e]; exact aug_dead l
      simp at ha
      rcases ha with rfl | ha
      · unfold δa at hd; split at hd
        · assumption
        · exact absurd rfl hd
      · exact ih (δa q x) h a ha
  have hg := augOf u 0 hlive
  match u, hlen with
  | [], _ => exact absurd hF (by decide)
  | [a], _ =>
    exact (units1_small a (hA a (by simp)) 0 (by decide)).1 (by simp [hF, hw', hg a (by simp)])
  | [a, b], _ =>
    exact (units1_small a (hA a (by simp)) b (hA b (by simp))).2
      (by simp [hF, hw', hg a (by simp), hg b (by simp)])

/-- **المزيدُ بوحدةٍ سابقة:** الوحدةُ قبل الجذر، وحالاتُ ‎ف ع‎ كلُّها (فالفاءُ تسكن بعد الوحدة: ‎يَفْعَل، أَفْعَل‎). -/
def mazidU1 : List (List Nat × List Nat) :=
  unitList1.flatMap fun u => ((allSt 2).filter fun ss => Fwasl (run 0 (u ++ rootChain (mizan 3) ss))).map (u, ·)

/-- **عددُ المزيد بوحدةٍ بصامتٍ واحد:** ‎729‎ = ‎27 × 15 + 27 × 12‎ (بعد متحرّكٍ تسكن الفاءُ أو تتحرّك،
وبعد مدٍّ لا تسكن — لأنّ ساكنًا بعد مدٍّ لا يكون إلّا مدغمًا). -/
theorem mazidU1_count : mazidU1.length = 729 := by decide +kernel

theorem unit_end_all : ∀ u ∈ unitList1, run 0 u = 1 ∨ run 0 u = 2 ∨ run 0 u = 3 ∨ run 0 u = 4 := by
  decide +kernel

theorem unit_end (u : List Nat) (hu : u ∈ unitList1) :
    run 0 u = 1 ∨ run 0 u = 2 ∨ run 0 u = 3 ∨ run 0 u = 4 := unit_end_all u hu

theorem fin_madd_mover : ∀ c < 29, c ≠ 2 → ∀ s < 3, δ 4 (4 * c + s) = 1 + s := by decide +kernel
theorem fin_mc_mover : ∀ j < 29, ∀ c < 29, c ≠ j → ∀ s < 3, δ (6 + j) (4 * c + s) = 96 := by
  decide +kernel

/-- بعد مدّ: جذران صحيحان لا تجاورَ فيهما، أوّلُ كلٍّ منهما غيرُ ثانيه، يسيران سيرًا واحدًا. -/
theorem from_madd (c1 c2 c3 d1 d2 d3 s1 s2 : Nat) (hc : SoundR [c1, c2, c3]) (hd : SoundR [d1, d2, d3])
    (hcs : Spaced [c1, c2, c3]) (hds : Spaced [d1, d2, d3]) (hc12 : c1 ≠ c2) (hd12 : d1 ≠ d2)
    (hs1 : s1 < 4) (hs2 : s2 < 4) :
    Fwasl (run 4 (rootChain [c1, c2, c3] [s1, s2])) = Fwasl (run 4 (rootChain [d1, d2, d3] [s1, s2])) := by
  have e : ∀ x y z : Nat, rootChain [x, y, z] [s1, s2] = [4 * x + s1, 4 * y + s2, 4 * z + 0] := by
    intro x y z; rfl
  have e2 : ∀ y z : Nat, rootChain [y, z] [s2] = [4 * y + s2, 4 * z + 0] := by intro y z; rfl
  have g := fun (l : List Nat) (x : Nat) (hx : x ∈ l) (h : SoundR l) => h x hx
  have c1s := hc c1 (by simp); have c2s := hc c2 (by simp); have c3s := hc c3 (by simp)
  have d1s := hd d1 (by simp); have d2s := hd d2 (by simp); have d3s := hd d3 (by simp)
  rw [e, e]
  by_cases h1 : s1 < 3
  · simp only [run, fin_madd_mover c1 c1s.1 c1s.2.1 s1 h1, fin_madd_mover d1 d1s.1 d1s.2.1 s1 h1]
    have := wazn_from (1 + s1) (by simp [Rs]; omega) (by omega) [c2, c3] [d2, d3] [s2]
      (fun x hx => hc x (by simp at hx ⊢; omega)) hcs.2 (fun x hx => hd x (by simp at hx ⊢; omega))
      hds.2 rfl (by intro t ht; simp at ht; omega)
    rw [e2, e2] at this
    simpa only [run] using this
  · have h13 : s1 = 3 := by omega
    subst h13
    have a1 := (fin_afterK c1 c1s.1 c1s.2.1).1
    have b1 := (fin_afterK d1 d1s.1 d1s.2.1).1
    simp only [run, a1, b1]
    by_cases h2 : s2 < 3
    · rw [fin_mc_mover c1 c1s.1 c2 c2s.1 (Ne.symm hc12) s2 h2,
        fin_mc_mover d1 d1s.1 d2 d2s.1 (Ne.symm hd12) s2 h2]
      simp only [δ_big _ (Nat.le_refl 96), run_dead]
    · have h23 : s2 = 3 := by omega
      subst h23
      rw [(fin_afterJ c1 c1s.1 c2 c2s.1 c2s.2.1).1, (fin_afterJ d1 d1s.1 d2 d2s.1 d2s.2.1).1,
        (terminal _).2, (terminal _).2]

/-- **وبالجذر:** كلُّ جذرٍ صحيحٍ لا تجاورَ فيه، أوّلُه غيرُ ثانيه، يرخّصه المزيدُ بوحدةٍ كما يرخّصه الميزان. -/
theorem mazid_any_root (c1 c2 c3 s1 s2 : Nat) (u : List Nat) (hu : u ∈ unitList1)
    (hr : SoundR [c1, c2, c3]) (hsp : Spaced [c1, c2, c3]) (h12 : c1 ≠ c2) (hs1 : s1 < 4) (hs2 : s2 < 4) :
    Fwasl (run 0 (u ++ rootChain [c1, c2, c3] [s1, s2])) =
      Fwasl (run 0 (u ++ rootChain (mizan 3) [s1, s2])) := by
  have hq : run 0 u = 1 ∨ run 0 u = 2 ∨ run 0 u = 3 ∨ run 0 u = 4 := unit_end u hu
  rw [run_append, run_append]
  have hs : ∀ s ∈ [s1, s2], s < 4 := by intro s hs; simp at hs; omega
  rcases hq with h | h | h | h <;> rw [h]
  · exact wazn_from 1 rfl (by decide) _ _ _ hr hsp (mizan_ok 3).1 (mizan_ok 3).2 rfl hs
  · exact wazn_from 2 rfl (by decide) _ _ _ hr hsp (mizan_ok 3).1 (mizan_ok 3).2 rfl hs
  · exact wazn_from 3 rfl (by decide) _ _ _ hr hsp (mizan_ok 3).1 (mizan_ok 3).2 rfl hs
  · exact from_madd c1 c2 c3 25 3 13 s1 s2 hr (mizan_ok 3).1 hsp (mizan_ok 3).2 h12 (by decide) hs1 hs2

end Law
end SLGE
