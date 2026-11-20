/-
  Madlul/Fard116.lean — فرضيّة الـ116 على جذور المعجمين المختومين.

  الفرضيّة كما نقلتُها بعبارتي عن رسالة المالك (`Madlul/فرضية_116.md` §١): عددُ الجذوع في المعجمين محدودٌ مقيس، والرباعيُّ
  والخماسيُّ يتولّدان من توافيق الـ116.
  والآلةُ آلتُه بعينها: `SLGE.Law.Mroot` (SLGE/Root.lean) وعددُها مبرهنٌ عنده (`root3`، `root4`، `root5`).

  ما هنا:
  * **مبرهن لكلّ:** آلةُ الجذر المرخَّص هي بعينها: لا ألفَ أصلًا، ولا يتجاور حاملان مختلفان من مخرجٍ واحد غيرَ حروف العلّة
    (`licB_iff_spaced`) — معنى ترويسة Root.lean مبرهنًا؛ وحرفُ العلّة لا يدخل التجاور (`illa_la_tajawur`).
  * **مبرهن على الشاهد** (`decide +kernel` على قوائم `Madlul/Fard116Data.lean` المولَّدة من المودَعين بـ `shabaka/fard116.py --lean`؛
    والمبرهناتُ في `Madlul/Fard116Shawahid.lean`، مرورٌ واحدٌ لكلٍّ منها): عددُ المخالِف للآلة في كلّ جمهور، وعددُ ما فيه الأقصرُ المشهود (G1/G2/Gr)، وعددُ المتجاور من أزواج القانون ومن أشدّ ما يُتجنَّب خارجه،
    وعددُ ما اجتمع فيه حرفا كلِّ قيدٍ منقول، وعددُ التماثل. أمّا خطوطُ الأساس (البعثرة والفضاء المرخَّص بالتساوي) فعدٌّ مُعاد بالأداة لا برهان.
  التحليل كاملًا في `Madlul/فرضية_116.md`.
-/
import SLGE.Root
import Madlul.Fard116Data

namespace Madlul.Fard116

open SLGE.Law
open Madlul.Fard116Data

/-! ## ١. الآلةُ قاعدةً مقروءة -/

/-- قبولُ الآلة بالقيمة: `Mroot.Lic 0` حكمًا. -/
def licB (r : List Nat) : Bool := r.all (· < 29) && Mroot.F (Mroot.runL 0 r)

theorem licB_iff (r : List Nat) : licB r = true ↔ Mroot.Lic 0 r := by
  unfold licB SLGE.Machine.Lic
  simp only [Bool.and_eq_true, List.all_eq_true, decide_eq_true_eq]
  exact Iff.rfl

theorem runL_imtina : ∀ l : List Nat, Mroot.runL 30 l = 30
  | [] => rfl
  | a :: l => by
    show Mroot.runL (δr 30 a) l = 30
    have : δr 30 a = 30 := by unfold δr; simp
    rw [this]; exact runL_imtina l

/-- من حالة «بعد الحامل a»: القبولُ = كلُّ ما بعده حاملٌ غيرُ الألف، ولا تجاورَ من a فما بعده. -/
theorem runL_qabul : ∀ (l : List Nat) (a : Nat), a < 29 → a ≠ 2 →
    (Mroot.F (Mroot.runL (a + 1) l) = true ↔ (∀ c ∈ l, c < 29 ∧ c ≠ 2) ∧ Spaced (a :: l))
  | [], a, ha, _ => by
    show decide (1 ≤ a + 1 ∧ a + 1 ≤ 29) = true ↔ _
    simp [Spaced]; omega
  | c :: l, a, ha, ha2 => by
    show Mroot.F (Mroot.runL (δr (a + 1) c) l) = true ↔ _
    by_cases hc : 29 ≤ c ∨ c = 2
    · have : δr (a + 1) c = 30 := by unfold δr; simp [hc]
      rw [this, runL_imtina]
      constructor
      · intro h; exact absurd h (by decide)
      · rintro ⟨h, _⟩; have := h c (by simp); omega
    · have hc' : c < 29 ∧ c ≠ 2 := by omega
      by_cases hk : conflict a c = true
      · have : δr (a + 1) c = 30 := by
          unfold δr; simp [hk] <;> omega
        rw [this, runL_imtina]
        constructor
        · intro h; exact absurd h (by decide)
        · rintro ⟨_, hs⟩; simp [Spaced] at hs; simp [hs.1] at hk
      · have : δr (a + 1) c = c + 1 := by
          unfold δr; simp [hk] <;> omega
        rw [this, runL_qabul l c hc'.1 hc'.2]
        simp only [Spaced, List.mem_cons, forall_eq_or_imp]
        simp at hk
        constructor
        · rintro ⟨h1, h2⟩; exact ⟨⟨hc', h1⟩, hk, h2⟩
        · rintro ⟨⟨_, h1⟩, _, h2⟩; exact ⟨h1, h2⟩

/-- **قانونُ الجذر مقروءًا (لكلّ جذر):** الجذرُ مرخَّصٌ في آلة المالك إذا وفقط إذا لم يكن فارغًا، ولا ألفَ فيه ولا ما فوق الحوامل،
ولا يتجاور فيه حاملان مختلفان من مخرجٍ واحد ليس أحدُهما حرفَ علّة (`Spaced`). -/
theorem licB_iff_spaced (r : List Nat) :
    licB r = true ↔ r ≠ [] ∧ (∀ c ∈ r, c < 29 ∧ c ≠ 2) ∧ Spaced r := by
  rw [licB_iff]
  unfold SLGE.Machine.Lic
  cases r with
  | nil => simp; rfl
  | cons a l =>
    show ((∀ x ∈ a :: l, x < 29) ∧ Mroot.F (Mroot.runL (δr 0 a) l) = true) ↔ _
    by_cases ha : 29 ≤ a ∨ a = 2
    · have : δr 0 a = 30 := by unfold δr; simp [ha]
      rw [this, runL_imtina]
      constructor
      · rintro ⟨_, h⟩; exact absurd h (by decide)
      · rintro ⟨_, h, _⟩; have := h a (by simp); omega
    · have : δr 0 a = a + 1 := by unfold δr; simp <;> omega
      rw [this, runL_qabul l a (by omega) (by omega)]
      simp only [List.mem_cons, forall_eq_or_imp, ne_eq, reduceCtorEq, not_false_eq_true, true_and]
      constructor
      · rintro ⟨⟨_, _⟩, h, hs⟩; exact ⟨⟨⟨by omega, by omega⟩, fun c hc => h c hc⟩, hs⟩
      · rintro ⟨⟨_, h⟩, hs⟩; exact ⟨⟨by omega, fun c hc => (h c hc).1⟩, h, hs⟩

/-- **حرفُ العلّة لا يدخل التجاور (لكلّ حامل):** فترميزُ الألف المكتوبة واوًا أو ياءً سواءٌ في الحكم. -/
theorem illa_la_tajawur (a : Nat) :
    conflict a 28 = false ∧ conflict 28 a = false ∧ conflict a 11 = false ∧ conflict 11 a = false := by
  simp [conflict, weak]

/-! ## ٢. الحكمُ السريع: جدولُ التجاور خريطةَ بِتّات، مساويًا للآلة لكلّ جذر -/

/-- جدولُ `conflict` على 29×29 خريطةَ بِتّات (البِتّ 29a+b). -/
def CT : Nat := 0x20000002000000000000000c000000a0000006000000030000002800000180000000c000000a0000006000000000000000000000000000000000000000000000800000080000000000000000000000800000080000000800000080000000000000020000002

def tajB (a b : Nat) : Bool := (CT >>> (29 * a + b)) % 2 == 1

theorem tajB_eq : ∀ a < 29, ∀ b < 29, tajB a b = conflict a b := by decide +kernel

def spacedB : List Nat → Bool
  | a :: b :: l => !tajB a b && spacedB (b :: l)
  | _ => true

theorem spacedB_iff : ∀ r : List Nat, (∀ c ∈ r, c < 29) → (spacedB r = true ↔ Spaced r)
  | [], _ => by simp [spacedB, Spaced]
  | [_], _ => by simp [spacedB, Spaced]
  | a :: b :: l, h => by
    have ih := spacedB_iff (b :: l) (fun c hc => h c (List.mem_cons_of_mem a hc))
    simp only [spacedB, Spaced, Bool.and_eq_true, Bool.not_eq_true']
    rw [tajB_eq a (h a (by simp)) b (h b (by simp)), ih]

def licF (r : List Nat) : Bool := !r.isEmpty && r.all (fun c => c < 29 && c != 2) && spacedB r

/-- **الحكمُ السريع هو حكمُ الآلة (لكلّ جذر).** -/
theorem licF_eq (r : List Nat) : licF r = licB r := by
  apply Bool.eq_iff_iff.mpr
  rw [licB_iff_spaced]
  unfold licF
  simp only [Bool.and_eq_true, Bool.not_eq_true', List.isEmpty_eq_false_iff, List.all_eq_true,
    bne_iff_ne, decide_eq_true_eq, ne_eq]
  constructor
  · rintro ⟨⟨hne, hall⟩, hs⟩
    exact ⟨hne, hall, (spacedB_iff r (fun c hc => (hall c hc).1)).mp hs⟩
  · rintro ⟨hne, hall, hs⟩
    exact ⟨⟨hne, hall⟩, (spacedB_iff r (fun c hc => (hall c hc).1)).mpr hs⟩

/-- على الثلاثيّ في الموضعين اللذين تقع فيهما الألفُ في العناوين (الآخر في «بغا»، والوسط في «قام» بالمقاييس): الواوُ والياءُ سواء. -/
theorem illa_sawa : ∀ a < 29, ∀ b < 29,
    licB [a, b, 28] = licB [a, b, 11] ∧ licB [a, 28, b] = licB [a, 11, b] := by
  have h : ∀ a < 29, ∀ b < 29,
      licF [a, b, 28] = licF [a, b, 11] ∧ licF [a, 28, b] = licF [a, 11, b] := by decide +kernel
  intro a ha b hb
  simpa only [licF_eq] using h a ha b hb

/-! ## ٣. الجذرُ رمزًا: تعريفاتُ الحكم على الجماهير -/

/-- حواملُ الرمز c بطول k (الأوّلُ أعلاها) — فكُّ `ramz`. -/
def arqam : Nat → Nat → List Nat
  | 0, _ => []
  | k + 1, c => arqam k (c / 29) ++ [c % 29]

/-- رمزُ الجذر: حواملُه أرقامًا بالأساس 29. -/
def ramz (r : List Nat) : Nat := r.foldl (fun n c => 29 * n + c) 0

/-- حكمُ الآلة على رمزٍ بطول k. -/
def licK (k c : Nat) : Bool := licF (arqam k c)

/-- حكمُ الآلة على الثلاثيّ حسابًا بلا قوائم. -/
def licN3 (c : Nat) : Bool :=
  let x := c / 29 / 29 % 29; let y := c / 29 % 29; let z := c % 29
  x != 2 && y != 2 && z != 2 && !tajB x y && !tajB y z

/-- **والحسابُ هو حكمُ الآلة (لكلّ رمز).** -/
theorem licN3_eq (c : Nat) : licN3 c = licB (arqam 3 c) := by
  rw [← licF_eq]
  have h1 : c / 29 / 29 % 29 < 29 := Nat.mod_lt _ (by decide)
  have h2 : c / 29 % 29 < 29 := Nat.mod_lt _ (by decide)
  have h3 : c % 29 < 29 := Nat.mod_lt _ (by decide)
  simp [licN3, licF, arqam, spacedB, h1, h2, h3]
  cases tajB (c / 29 / 29 % 29) (c / 29 % 29) <;> cases tajB (c / 29 % 29) (c % 29) <;> simp [Bool.and_assoc, Bool.and_comm, Bool.and_left_comm]

/-- يتجاور a وb في الثلاثيّ c (بأيّ ترتيب، في 1–2 أو 2–3). -/
def jiwarN (c a b : Nat) : Bool :=
  let x := c / 29 / 29 % 29; let y := c / 29 % 29; let z := c % 29
  (x == a && y == b) || (x == b && y == a) || (y == a && z == b) || (y == b && z == a)

/-- حاملُ الموضع i (0، 1، 2) من الثلاثيّ c. -/
def harf3 (c i : Nat) : Nat := if i = 0 then c / 29 / 29 % 29 else if i = 1 then c / 29 % 29 else c % 29

/-- الموضعان i وj من الثلاثيّ c متماثلان. -/
def mithlN (c i j : Nat) : Bool := harf3 c i == harf3 c j

/-- وهو حاملُ `arqam` في موضعه (لكلّ رمز). -/
theorem harf3_arqam (c : Nat) : arqam 3 c = [harf3 c 0, harf3 c 1, harf3 c 2] := by
  simp [arqam, harf3]

/-- الحاملان a وb معًا في الجذر c بطول k في أيّ موضع. -/
def maanK (k c a b : Nat) : Bool := (arqam k c).contains a && (arqam k c).contains b

/-- وعلى الثلاثيّ حسابًا. -/
def maanN3 (c a b : Nat) : Bool :=
  (harf3 c 0 == a || harf3 c 1 == a || harf3 c 2 == a) && (harf3 c 0 == b || harf3 c 1 == b || harf3 c 2 == b)

/-- **وهو `maanK 3` (لكلّ رمز).** -/
theorem maanN3_eq (c a b : Nat) : maanN3 c a b = maanK 3 c a b := by
  simp only [maanK, harf3_arqam, maanN3, List.contains_cons, List.contains_nil, Bool.or_false]
  simp [Bool.beq_comm, Bool.or_assoc]

/-- أزواجُ القانون الأربعة عشر (`conflict`) بترميز `Dal.hawamil`: ء0 ه1 ع3 ح4 غ5 خ6 ج9 ش10 ط16 د17 ت18 ز19 س20 ص21 ظ22 ذ23 ث24 ب26 م27. -/
def azwajQanun : List (Nat × Nat) :=
  [(0, 1), (3, 4), (5, 6), (9, 10), (16, 17), (16, 18), (17, 18), (19, 20), (19, 21), (20, 21),
   (22, 23), (22, 24), (23, 24), (26, 27)]

/-- **وهي أزواجُ القانون كلُّها:** كلُّ زوجٍ فيها متعارض، والمتعارضُ a < b في الحوامل كلّها هي هي. -/
theorem azwajQanun_kulluha :
    ((List.range 29).flatMap fun a => (List.range 29).filterMap fun b =>
      if a < b ∧ conflict a b then some (a, b) else none) = azwajQanun := by decide +kernel

/-- **والقانونُ يجيز المتماثلَين متجاورَين (لكلّ حامل):** `conflict` يشترط الاختلاف. -/
theorem tamathul_mujaz (a : Nat) : conflict a a = false := by simp [conflict]

/-! ## ٤. التولّد: الأطولُ من الأقصر المشهود -/

def fiKharita (bits : Nat) (r : List Nat) : Bool := (bits >>> ramz r) % 2 == 1

/-- رموزُ الإسقاطات المشهودة بلا تكرار، للجذر c بطول k. -/
def mashhud (k bits c : Nat) : List Nat :=
  let q := arqam k c
  (((List.range q.length).map (fun i => q.eraseIdx i)).filter (fiKharita bits)).map ramz |>.eraseDups

def G1 (k bits c : Nat) : Bool := !(mashhud k bits c).isEmpty
def G2 (k bits c : Nat) : Bool := decide (2 ≤ (mashhud k bits c).length)
def Gr (c : Nat) : Bool := match arqam 4 c with
  | [a, b, c, d] => a == c && b == d
  | _ => false

/-! ## ٥. الجماهير (مبرهن على الشاهد؛ والباقي في `Madlul/Fard116Shawahid.lean`) -/

theorem jumhur_atwal :
    lisan3.length = 6409 ∧ lisan4.length = 2522 ∧ lisan5.length = 70 ∧ maqayis3.length = 4119 := by
  decide +kernel

/-- الخريطةُ المولَّدة للثلاثيّ هي رموزُ قائمته بعينها. -/
theorem kharita3 : bits3 = lisan3.foldl (fun b c => b ||| (1 <<< c)) 0 := by decide +kernel
/-- والرباعيّ. -/
theorem kharita4 : bits4 = lisan4.foldl (fun b c => b ||| (1 <<< c)) 0 := by decide +kernel

/-- والرمزُ يعود حواملَه (لكلّ ثلاثيّ): `ramz (arqam 3 c) = c` لما دون 29³. -/
theorem ramz_arqam3 (c : Nat) (h : c < 24389) : ramz (arqam 3 c) = c := by
  simp [ramz, arqam]; omega

end Madlul.Fard116
