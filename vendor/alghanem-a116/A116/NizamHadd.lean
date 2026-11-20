import A116.Nizam
import A116.Exhaust
import A116.Numbering

/-!
# قيدُ الحدّ نظامًا على (صنف، خانة): كلُّ ترخيصٍ في البوّابة مثولٌ للنواة (ADR ٢٥)

قرارُ المالك (2026-10-12): «تكون الخطوة التالية بناء قيد الحدّ نظامًا على (صنف، خانة) … موافق، كلُّ صنفٍ له n
وكلُّ خانةٍ لها n».

في ADR ٢٣ بقي دَينٌ مسمًّى `HADD_AS_NIZAM_UNPROVEN`: قيدُ الحدّ (`Hadd.geminateB`) ليس جوارَ أزواج، لأنّ شرطَه على
**ثلاثة**: مدٌّ (قبلُ)، ثمّ مُغلِقٌ (الاسم)، ثمّ ما بعده بحامل المُغلِق نفسِه (بعدُ) — «علاقةُ ما قبلها بما بعدها» بعينها.
وهذه الوحدةُ تسدّه بنظام الأنظمة نفسِه: **ما كان قيدًا على ثلاثةٍ صار جوارًا على أزواجها** (`chain_azwaj`)، لكلّ قيدٍ
ثلاثيّ ولكلّ نظام؛ فقيدُ الحدّ نظامٌ على الأزواج (`haddN`) عناصرُه أزواجُ (صنف، خانة) المتجاورة.

## المبرهَن

* **لكلّ صنفٍ n ولكلّ خانةٍ n**: `kN` (cv = 0، v = 1، c = 2) و`Numbering.bridgeIndex` (0 … 115)، وعددُ الدور
  ‎roleN = 3·n(الخانة) + n(الصنف)‎ تقابلٌ (`roleN_inj`، `roleN_lt`: دون 348)، وعددُ الزوج ‎edgeN = 348·n(الأوّل) + n(الثاني)‎
  تقابل (`edgeN_inj`)؛ والأدوارُ المرخَّصة 116 بأعدادٍ متباينة (`licensed_roles_n`).
* **الثلاثيُّ جوارٌ على الأزواج** (`chain_azwaj`)، والجوارُ على العناصر جوارٌ على أزواجها (`chain_eq_azwaj`).
* **قيدُ الحدّ نافذةٌ ثلاثيّة وطرف**: `geminate_win3` (وصلًا: النافذةُ و`tarafWasl` — لا مدَّ ثمّ مُغلِقًا في الطرف)،
  `geminatePause_win3` (وقفًا: النافذةُ وحدَها — المدُّ العارضُ للسكون هو سقوطُ شرط الطرف).
* **الجامع**: `strictB_is_nizam` — لكلّ كلمةٍ (غيرِ مدّ الفرق) من خانتين فصاعدًا، `Hadd.strictB` هو ترخيصُ نظام الأزواج
  `haddN` على أزواج أدوارها وشرطُ الطرف؛ و`strictPauseB_split` — `Hadd.strictPauseB` هو الجوارُ الثلاثيُّ وقفًا
  (`Nizam.licWaqf ternary`) والنافذة.
* **مدُّ الفرق استثناءٌ مسمًّى خارج النظام** (`farq_outside_nizam`): آلْآنَ مرخَّصةٌ بـ`strictB` ونافذتُها مرفوضة.
-/

namespace A116.NizamHadd

open A116 A116.Stages A116.Ternary A116.Hadd A116.Nizam

/-! ## ١. لكلّ صنفٍ n ولكلّ خانةٍ n -/

abbrev Role := K × Cell

def kN : K → Nat
  | .cv => 0
  | .v => 1
  | .c => 2

theorem kN_lt (k : K) : kN k < 3 := by cases k <;> decide

theorem kN_inj {a b : K} (h : kN a = kN b) : a = b := by
  cases a <;> cases b <;> simp_all [kN]

/-- عددُ الدور: ‎3·n(الخانة) + n(الصنف)‎. -/
def roleN (r : Role) : Nat := 3 * Numbering.bridgeIndex r.2 + kN r.1

theorem roleN_lt (r : Role) : roleN r < 348 := by
  have := Numbering.bridgeIndex_lt r.2; have := kN_lt r.1; unfold roleN; omega

theorem roleN_inj {r s : Role} (h : roleN r = roleN s) : r = s := by
  unfold roleN at h
  have hk : kN r.1 = kN s.1 := by have := kN_lt r.1; have := kN_lt s.1; omega
  have hc : Numbering.bridgeIndex r.2 = Numbering.bridgeIndex s.2 := by omega
  exact Prod.ext (kN_inj hk) (Numbering.bridgeIndex_injective hc)

/-- عددُ الزوج. -/
def edgeN (e : Role × Role) : Nat := 348 * roleN e.1 + roleN e.2

theorem edgeN_inj {e f : Role × Role} (h : edgeN e = edgeN f) : e = f := by
  unfold edgeN at h
  have := roleN_lt e.2; have := roleN_lt f.2
  have h1 : roleN e.1 = roleN f.1 := by omega
  have h2 : roleN e.2 = roleN f.2 := by omega
  exact Prod.ext (roleN_inj h1) (roleN_inj h2)

/-- الأدوارُ المرخَّصة (`Exhaust.rolesOf` على `Alif.licensable`) مئةٌ وستّ عشرة بأعدادٍ متباينة. -/
theorem licensed_roles_n :
    let ns := Alif.licensable.flatMap fun x => (Exhaust.rolesOf x).map fun k => roleN (k, x)
    ns.length = 116 ∧ ns.Nodup := by
  decide +kernel

/-- أدوارُ الكلمة: كلُّ خانةٍ بصنفها. -/
def roles (w : List Cell) : List Role := (kindOf w).zip w

theorem roles_fst (w : List Cell) : (roles w).map Prod.fst = kindOf w := by
  unfold roles; rw [List.map_fst_zip]; simp [kindOf, kindGo_length]

/-! ## ٢. الثلاثيُّ جوارٌ على الأزواج — لكلّ نظام -/

section
variable {α : Type} [DecidableEq α]

/-- الأزواجُ المتجاورة. -/
def azwaj : List α → List (α × α)
  | a :: b :: t => (a, b) :: azwaj (b :: t)
  | _ => []

/-- النافذةُ الثلاثيّة: كلُّ (قبل، الاسم، بعد) متجاورٍ يحقّق `R`. -/
def win3 (R : α → α → α → Bool) : List α → Bool
  | a :: b :: c :: t => R a b c && win3 R (b :: c :: t)
  | _ => true

/-- نظامُ الأزواج: رخصةُ الزوج `W`، وابتداؤه بابتداء أوّله `I`، وجوارُ زوجين اتّصالُهما وقيدُ الثلاثة `R`. -/
def zawjN (R : α → α → α → Bool) (W : α → α → Bool) (I : α → Bool) : Nizam (α × α) where
  wujud e := W e.1 e.2
  ibtida e := I e.1
  wasl e f := e.2 == f.1 && R e.1 e.2 f.2
  waqf _ _ := false

theorem zawjN_wasl (R : α → α → α → Bool) (W : α → α → Bool) (I : α → Bool) (e f : α × α) :
    (zawjN R W I).wasl e f = (e.2 == f.1 && R e.1 e.2 f.2) := rfl

/-- **ما كان قيدًا على ثلاثةٍ صار جوارًا على أزواجها.** -/
theorem chain_azwaj (R : α → α → α → Bool) (W : α → α → Bool) (I : α → Bool) :
    ∀ (a b : α) (t : List α), chain (zawjN R W I) (a, b) (azwaj (b :: t)) = win3 R (a :: b :: t)
  | _, _, [] => rfl
  | a, b, c :: t => by
    have ih := chain_azwaj R W I b c t
    simp only [azwaj, chain, zawjN_wasl, beq_self_eq_true, Bool.true_and, win3, ih]

omit [DecidableEq α] in
/-- والجوارُ على العناصر جوارٌ على أزواجها. -/
theorem chain_eq_azwaj (N : Nizam α) : ∀ (a : α) (l : List α),
    chain N a l = (azwaj (a :: l)).all fun e => N.wasl e.1 e.2
  | _, [] => rfl
  | a, b :: t => by simp only [chain, azwaj, List.all_cons, chain_eq_azwaj N b t]

omit [DecidableEq α] in
theorem azwaj_map {β : Type} (f : α → β) : ∀ l : List α,
    azwaj (l.map f) = (azwaj l).map fun e => (f e.1, f e.2)
  | [] => rfl
  | [_] => rfl
  | a :: b :: t => by
    have ih := azwaj_map f (b :: t)
    simp only [List.map_cons] at ih
    simp only [List.map_cons, azwaj, ih]

end

/-! ## ٣. قيدُ الحدّ: نافذةٌ ثلاثيّة وطرف -/

/-- قيدُ الحدّ على (قبل، الاسم، بعد): إن كان قبلُ مدًّا والاسمُ مُغلِقًا فبعدُ بحامل المُغلِق. -/
def hR (x y z : Role) : Bool := !(x.1 == .v && y.1 == .c) || (y.2.carrier == z.2.carrier)

/-- شرطُ الطرف وصلًا: لا مدَّ ثمّ مُغلِقًا في الآخر (لا مثلَ بعده). -/
def tarafWasl : List Role → Bool
  | [a, b] => !(a.1 == .v && b.1 == .c)
  | _ :: b :: c :: t => tarafWasl (b :: c :: t)
  | _ => true

theorem geminate_win3 : ∀ p : List Role, geminateB p = (win3 hR p && tarafWasl p)
  | [] => rfl
  | [(ka, _)] => by cases ka <;> rfl
  | [(ka, _), (kb, _)] => by cases ka <;> cases kb <;> rfl
  | (ka, ca) :: (kb, cb) :: (kc, cc) :: t => by
    have ih := geminate_win3 ((kb, cb) :: (kc, cc) :: t)
    simp only [geminateB] at ih ⊢
    rw [ih]
    simp only [win3, tarafWasl]
    cases ka <;> cases kb <;> simp [stepOK, hR, Bool.and_assoc]

theorem geminatePause_win3 : ∀ p : List Role, geminatePauseB p = win3 hR p
  | [] => rfl
  | [(ka, _)] => by cases ka <;> rfl
  | [(ka, _), (kb, _)] => by cases ka <;> cases kb <;> rfl
  | (ka, ca) :: (kb, cb) :: (kc, cc) :: t => by
    have ih := geminatePause_win3 ((kb, cb) :: (kc, cc) :: t)
    simp only [geminatePauseB] at ih ⊢
    rw [ih]
    simp only [win3]
    cases ka <;> cases kb <;> simp [stepOKPause, stepOK, hR]

/-- **نظامُ الحدّ على الأزواج**: الزوجُ مأذونٌ ثلاثيًّا (`waslK`)، والابتداءُ بمتحرّك، والجوارُ قيدُ الحدّ. -/
def haddN : Nizam (Role × Role) :=
  zawjN hR (fun x y => waslK x.1 y.1) (fun x => x.1 == .cv)

/-- اللمّة: الجوارُ الثلاثيُّ على صنفين فصاعدًا هو رخصةُ أزواجهما وابتداءُ أوّلهما. -/
theorem licWasl_ternary_azwaj (a b : Role) (t : List Role) :
    licWasl ternary ((a :: b :: t).map Prod.fst) =
      (((azwaj (a :: b :: t)).all fun e => waslK e.1.1 e.2.1) && a.1 == .cv) := by
  simp only [List.map_cons, licWasl, ternary, Nizam.all_true, Bool.true_and]
  rw [chain_eq_azwaj, ← List.map_cons, ← List.map_cons, azwaj_map, List.all_map]
  simp [Bool.and_comm]
  rfl

/-- **الجامع**: قيدُ الحدّ وصلًا (غيرَ مدّ الفرق) هو ترخيصُ نظام الأزواج `haddN` على أزواج الأدوار وشرطُ الطرف. -/
theorem strictB_is_nizam (w : List Cell) (hf : isFarq w = false) (hl : 2 ≤ w.length) :
    strictB w = (licWasl haddN (azwaj (roles w)) && tarafWasl (roles w)) := by
  have hlen : (roles w).length = w.length := by simp [roles, kindOf, kindGo_length]
  obtain ⟨a, b, t, hp⟩ : ∃ a b t, roles w = a :: b :: t := by
    match h : roles w with
    | a :: b :: t => exact ⟨a, b, t, rfl⟩
    | [] => rw [h] at hlen; simp at hlen; omega
    | [_] => rw [h] at hlen; simp at hlen; omega
  have hk : kindOf w = (a :: b :: t).map Prod.fst := by rw [← hp, roles_fst]
  unfold strictB haddB
  simp only [hf, Bool.false_eq_true, ite_false]
  rw [show (kindOf w).zip w = roles w from rfl, hp, geminate_win3, continueB_local, hk,
    licWasl_ternary_azwaj]
  have hc : chain haddN (a, b) (azwaj (b :: t)) = win3 hR (a :: b :: t) := chain_azwaj _ _ _ a b t
  simp only [azwaj, licWasl, List.all_cons, hc]
  simp only [haddN, zawjN]
  cases (waslK a.1 b.1) <;> cases ((azwaj (b :: t)).all fun e => waslK e.1.1 e.2.1) <;>
    cases (a.1 == .cv) <;> cases win3 hR (a :: b :: t) <;> cases tarafWasl (a :: b :: t) <;> rfl

/-- وقفًا: الجوارُ الثلاثيُّ وقفًا (`Nizam.licWaqf ternary`) والنافذةُ وحدَها — شرطُ الطرف ساقط (المدُّ العارض). -/
theorem strictPauseB_split (w : List Cell) (hf : isFarq w = false) :
    strictPauseB w = (licWaqf ternary (kindOf w) && win3 hR (roles w)) := by
  unfold strictPauseB haddPauseB
  simp only [hf, Bool.false_eq_true, ite_false]
  rw [pauseB_local, show (kindOf w).zip w = roles w from rfl, geminatePause_win3]

open A116.Ladder in
/-- **مدُّ الفرق استثناءٌ مسمًّى خارج النظام**: آلْآنَ مرخَّصةٌ بقيد الحدّ، ونافذتُها في نظام الأزواج مرفوضة. -/
theorem farq_outside_nizam :
    isFarq alaana = true ∧ strictB alaana = true ∧ win3 hR (roles alaana) = false :=
  ⟨by decide, alaana_strict, by decide⟩

open A116.Ladder in
/-- شاهدان: حَاجَّ في النظام (المُغلِقُ أوّلُ مثلين)، وقَالْتُ خارجَه (المُغلِقُ بلا مثله). -/
theorem witnesses :
    licWasl haddN (azwaj (roles hajjaCells)) = true ∧ tarafWasl (roles hajjaCells) = true ∧
    win3 hR (roles qaaltu) = false := by
  decide

end A116.NizamHadd
