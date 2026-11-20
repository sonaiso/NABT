import SLGE.Count

/-!
# الحسابُ الصنفيّ: العدُّ بالاستنفاد على الآلة هو العدُّ على أصنافها

قولُ المالك في الجلسة (2026-11-01، 12:40 بتوقيت عمّان):
«طلب الدمج #119 ما زال ينتظرك حدثه وفق ما استكشف انت وبعده ندمج ولكن يجب ان نوحد الحساب من الان وصاعدا بقانون واحد جبري»
ثمّ رسالتُه بعد دمج #119 (لفظُها ووقتُها 17:56 من ملخّص الجلسة بعد ضغطها)، وصدرُها جملةُ البنّاء من جوابه ألصقها المالك:
«الخطوةُ التالية التي أراها: عدُّ Msyl وMaug بالقانون نفسِه، فيكتمل التوحيد على آلاتك كلّها.»
وهذا ما بعدها:
«جيد موافق لكن يجب ان تجعل كل المشروع لا يعمل الا وفق هذا الحساب وان تجهز لعمل تكامل بن كل المبرهنات والاختبارات وفق حساب الجديد واعطيه منهج الحساب اسما والأهم تعمل توثيق»
ثمّ اختار من سؤالٍ متعدّد الخيارات نصُّ خياراته من البنّاء «عدّل SLGE نفسَها» (لفظُه ولفظُ وصفه من الملخّص). ووصفُ الخيار:
«أستبدل براهين الأعداد في ملفّاتك بالقانون (بإذنك هذا)، فلا يبقى حسابٌ بالجدول في المستودع»

**المنهج واسمُه.** «الحسابُ الصنفيّ» (والاسمُ قراءةُ البنّاء تنتظر إمضاءك): كلُّ عددٍ لما ترخّصه آلةٌ للمالك (`Machine.C`، `Machine.lev` في
`SLGE/Count.lean`) يُحسب على أصناف حالاتها لا على الحالات ولا بجدول؛ ومن الأعداد التي لم تُنقل إليه بعدُ ما في §٥ من `hawkama/الحساب_الصنفي.md` (والجردُ فيه عيّنةٌ لا حصر). والأصنافُ **متكافئة** (`Mutakafi`) — لكلّ حالةٍ في الصنف ‎`i`‎ من
الانتقالات بوزنٍ ‎`u`‎ إلى الصنف ‎`j`‎ العددُ نفسُه — فالعدُّ من كلّ حالةٍ من حالاتها (‎`P q`‎) دالّةٌ في صنفها (`qanun_adad`). وما تحتاجه الصفوفُ من طولٍ يحدّه جهدٌ ‎`pot`‎ وثابتٌ
‎`K`‎: على كلّ مدخلٍ بوزنٍ ‎`u`‎ من صنفٍ غيرِ ميّت ‎`i`‎ إلى صنفٍ غيرِ ميّت ‎`j`‎ ‎`pot j + 1 ≤ pot i + K·u`‎، والصنفُ الميّت لا يقبل ولا ينتقل إلّا
إلى ميّت (`C_mustaqill`)؛ فالعدُّ في الدرجة ‎`w`‎ لا يتوقّف على الطول متى بلغ ‎`K·w + pot i`‎ (`C_thabit2`).
والحسابُ الصنفيُّ لآلةٍ من ابتدائها بنيةٌ واحدة (`Hisab`) تجمع ذلك كلَّه، وعددُ كلّ درجةٍ منها (`Hisab.lev_eq`، `Hisab.C_eq`).

**وفي المشروع.** لآلات المالك السبع حسابٌ صنفيٌّ في ملفّاتها: الجذرُ `Mroot` والزوائدُ `Maug` (`SLGE/Root.lean`)، والكلمةُ موقوفًا عليها `Mword`
وفي الوصل `MwordWasl` والجملةُ `Msent` (`SLGE/Law.lean`)، والمقطعُ `Msyl` وفي الوصل `MsylWasl` (`SLGE/Syllable.lean`)؛ وأعدادُه فيها
(`root3`، `units1`، `word_levels`، `sent_levels`، `syl_levels`، …) مبرهنةٌ به، وحُذف الجدولُ `row` و`tab` و`tab_eq` من `SLGE/Count.lean`. ويفحص
`tahaqquq/test_hisab.py` (البوّابة ٥خ٢) على بيئة Lean نفسِها أنّ لكلّ تعريفٍ نوعُه `SLGE.Machine` في وحدات المشروع حسابًا صنفيًّا، وأنّ كلَّ مبرهنةٍ في قضيّتها عددُ درجةٍ
لآلةٍ بأرقامٍ يمرّ برهانُها بـ `Hisab.lev_eq` أو `Hisab.C_eq`. والتوثيقُ في `hawkama/الحساب_الصنفي.md`.

**التعيين** (البنّاء): قراءةُ قول المالك «بقانون واحد جبري» أنّه هذا: عدُّ المالك نفسُه، وقسمتُه على الأصناف، ومنها
التكرار؛ وقراءةُ «كل المشروع لا يعمل الا وفق هذا الحساب» أنّها كلُّ عددٍ لما ترخّصه آلة — وهما قراءتاي تنتظران إمضاءك.

المبرهنات: 15 بالمعيار الموحَّد (`Nizam/Asas.lean`): لكلّ 13 (`sum_map_one`، `sum_map_add`، `sum_zero`، `sum_ite_eq`، `tajmi`،
`qanun_adad`، `mayyit_sifr`، `C_mustaqill`، `C_thabit`، `C_thabit2`، `C_khatwa1`، `Hisab.C_eq`، `Hisab.lev_eq`)، وتعريفيّة 2 (`base_mayyit`،
`C_khatwa`)؛ ولا شيء على الشاهد.
-/

namespace SLGE

namespace HisabSinfi

/-! ## ١. مساعداتُ الجمع -/

theorem sum_map_one {α : Type} (l : List α) : (l.map fun _ => (1 : Nat)).sum = l.length := by
  induction l with
  | nil => rfl
  | cons a l ih => simp only [List.map_cons, List.sum_cons, List.length_cons, ih]; omega

theorem sum_map_add {α : Type} (l : List α) (f g : α → Nat) :
    (l.map fun x => f x + g x).sum = (l.map f).sum + (l.map g).sum := by
  induction l with
  | nil => rfl
  | cons a l ih => simp only [List.map_cons, List.sum_cons, ih]; omega

theorem sum_zero {α : Type} (l : List α) (f : α → Nat) (h : ∀ x ∈ l, f x = 0) : (l.map f).sum = 0 := by
  induction l with
  | nil => rfl
  | cons a l ih =>
    simp only [List.map_cons, List.sum_cons]
    rw [h a (List.mem_cons_self ..), ih (fun x hx => h x (List.mem_cons_of_mem _ hx))]

theorem sum_ite_eq (n c : Nat) (g : Nat → Nat) (hc : c < n) :
    ((List.range n).map fun x => if x = c then g x else 0).sum = g c := by
  induction n with
  | zero => omega
  | succ n ih =>
    rw [List.range_succ, List.map_append, List.sum_append]
    by_cases h : c < n
    · rw [ih h]; simp; omega
    · have e : c = n := by omega
      subst e
      rw [sum_zero _ _ (fun x hx => by rw [List.mem_range] at hx; simp; omega)]; simp

/-- **الجمعُ بالأصناف:** جمعُ ‎`c x · G (k₁ x) (k₂ x)`‎ على القائمة هو جمعُ ‎`G u j`‎ مضروبًا في مجموع ‎`c`‎ على
ما مفتاحاه ‎`(u, j)`‎. -/
theorem tajmi {α : Type} (U m : Nat) (k1 k2 c : α → Nat) (G : Nat → Nat → Nat) :
    ∀ (L : List α), (∀ x ∈ L, k1 x ≤ U ∧ k2 x < m) →
    (L.map fun x => c x * G (k1 x) (k2 x)).sum =
      ((List.range (U + 1)).map fun u => ((List.range m).map fun j =>
        ((L.filter fun x => k1 x == u && k2 x == j).map c).sum * G u j).sum).sum
  | [], _ => by
    simp only [List.map_nil, List.sum_nil, List.filter_nil, Nat.zero_mul]
    rw [sum_zero _ _ (fun u _ => sum_zero _ _ (fun _ _ => rfl))]
  | a :: L, hL => by
    have ih := tajmi U m k1 k2 c G L (fun x hx => hL x (List.mem_cons_of_mem _ hx))
    obtain ⟨h1, h2⟩ := hL a (List.mem_cons_self ..)
    have e : ∀ u j, (((a :: L).filter fun x => k1 x == u && k2 x == j).map c).sum * G u j =
        (if u = k1 a then (if j = k2 a then c a * G u j else 0) else 0) +
          ((L.filter fun x => k1 x == u && k2 x == j).map c).sum * G u j := by
      intro u j
      simp only [List.filter_cons]
      by_cases hu : u = k1 a
      · by_cases hj : j = k2 a
        · subst hu; subst hj; simp [Nat.add_mul]
        · have : (k1 a == u && k2 a == j) = false := by simp [Ne.symm hj]
          simp [this, hj]
      · have : (k1 a == u && k2 a == j) = false := by simp [Ne.symm hu]
        simp [this, hu]
    simp only [List.map_cons, List.sum_cons, ih, e, sum_map_add]
    rw [show ((List.range (U + 1)).map fun u => ((List.range m).map fun j =>
        if u = k1 a then (if j = k2 a then c a * G u j else 0) else 0).sum) =
        (List.range (U + 1)).map fun u => if u = k1 a then c a * G u (k2 a) else 0 from by
      apply List.map_congr_left; intro u _
      by_cases hu : u = k1 a
      · simp only [hu, ite_true]; exact sum_ite_eq m (k2 a) (fun j => c a * G (k1 a) j) h2
      · simp only [hu, ite_false]; exact sum_zero _ _ (fun _ _ => rfl)]
    rw [sum_ite_eq (U + 1) (k1 a) (fun u => c a * G u (k2 a)) (by omega)]

end HisabSinfi
open HisabSinfi

/-! ## ٢. الأصناف -/

/-- **أصنافُ آلة:** ‎`m`‎ صنفًا؛ ولكلّ صنفٍ صفٌّ من مداخل ‎(الوزن، الصنفُ الهدف، العدد)‎، وقبولٌ على الصنف. -/
structure Asnaf where
  m : Nat
  saff : Nat → List (Nat × Nat × Nat)
  F : Nat → Bool

namespace Asnaf
variable (Q : Asnaf)

def base (w i : Nat) : Nat := if w = 0 ∧ Q.F i = true then 1 else 0

/-- **العدُّ على الأصناف** بالاستنفاد نفسِه: القبولُ، ثمّ لكلّ مدخلٍ عددُه في ما يُكمله بعد وزنه. -/
def C : Nat → Nat → Nat → Nat
  | 0, w, i => Q.base w i
  | f + 1, w, i => Q.base w i +
      ((Q.saff i).map fun e => if e.1 ≤ w then e.2.2 * C f (w - e.1) e.2.1 else 0).sum

end Asnaf

/-- **التكافؤ:** حالاتُ ‎`P`‎ مغلقةٌ بالانتقال، وصنفُ كلٍّ منها ‎`s q`‎، وأوزانُها لا تتجاوز ‎`U`‎، وقبولُها قبولُ صنفها،
ولكلّ حالةٍ من الانتقالات بوزنٍ ‎`u`‎ إلى الصنف ‎`j`‎ ما في صفّ صنفها. -/
structure Mutakafi (M : Machine) (Q : Asnaf) (U : Nat) (s : Nat → Nat) (P : Nat → Prop) : Prop where
  maghluq : ∀ q, P q → ∀ b < M.A, P (M.δ q b)
  sinf : ∀ q, P q → s q < Q.m
  wazn : ∀ q, P q → ∀ b < M.A, M.ω q b ≤ U
  saff : ∀ q, P q → ∀ e ∈ Q.saff (s q), e.1 ≤ U ∧ e.2.1 < Q.m
  qubul : ∀ q, P q → M.F q = Q.F (s q)
  adad : ∀ q, P q → ∀ u ≤ U, ∀ j < Q.m,
    ((List.range M.A).filter fun b => M.ω q b == u && s (M.δ q b) == j).length =
      (((Q.saff (s q)).filter fun e => e.1 == u && e.2.1 == j).map fun e => e.2.2).sum

/-- **قانونُ العدّ الواحد:** على أصنافٍ متكافئة على الحالات ‎`P`‎، عدُّ المالك من كلّ حالةٍ منها (‎`P q`‎) هو العدُّ على صفّ صنفها، لكلّ طولٍ
ووزن. -/
theorem qanun_adad (M : Machine) (Q : Asnaf) (U : Nat) (s : Nat → Nat) (P : Nat → Prop)
    (h : Mutakafi M Q U s P) : ∀ f w q, P q → M.C f w q = Q.C f w (s q)
  | 0, w, q, hq => by simp only [Machine.C, Machine.base, Asnaf.C, Asnaf.base, h.qubul q hq]
  | f + 1, w, q, hq => by
    simp only [Machine.C, Asnaf.C]
    have hb : M.base w q = Q.base w (s q) := by simp only [Machine.base, Asnaf.base, h.qubul q hq]
    rw [hb]; congr 1
    let G : Nat → Nat → Nat := fun u j => if u ≤ w then Q.C f (w - u) j else 0
    have e1 : ((List.range M.A).map fun b => if M.ω q b ≤ w then M.C f (w - M.ω q b) (M.δ q b) else 0) =
        (List.range M.A).map fun b => 1 * G (M.ω q b) (s (M.δ q b)) := by
      apply List.map_congr_left; intro b hb; rw [List.mem_range] at hb
      simp only [G, Nat.one_mul]
      split
      · rw [qanun_adad M Q U s P h f _ _ (h.maghluq q hq b hb)]
      · rfl
    have e2 : ((Q.saff (s q)).map fun e => if e.1 ≤ w then e.2.2 * Q.C f (w - e.1) e.2.1 else 0) =
        (Q.saff (s q)).map fun e => e.2.2 * G e.1 e.2.1 := by
      apply List.map_congr_left; intro e _
      simp only [G]; split <;> simp
    rw [e1, e2]
    rw [tajmi U Q.m (M.ω q) (fun b => s (M.δ q b)) (fun _ => 1) G (List.range M.A)
      (fun b hb => by rw [List.mem_range] at hb; exact ⟨h.wazn q hq b hb, h.sinf _ (h.maghluq q hq b hb)⟩)]
    rw [tajmi U Q.m (fun e => e.1) (fun e => e.2.1) (fun e => e.2.2) G (Q.saff (s q)) (h.saff q hq)]
    congr 1; apply List.map_congr_left; intro u hu; rw [List.mem_range] at hu
    congr 1; apply List.map_congr_left; intro j hj; rw [List.mem_range] at hj
    rw [sum_map_one, h.adad q hq u (by omega) j hj]

/-! ## ٣. الطولُ لا يغيّر العدَّ متى كفى -/

namespace Asnaf
variable (Q : Asnaf)

theorem base_mayyit (w i : Nat) (h : Q.F i = false) : Q.base w i = 0 := by simp [base, h]

/-- **الصنفُ الميّت لا يُعدّ منه شيء:** لا يقبل، ولا ينتقل إلّا إلى ميّت. -/
theorem mayyit_sifr (mayyit : Nat → Bool)
    (hm : ∀ i, mayyit i = true → Q.F i = false ∧ ∀ e ∈ Q.saff i, mayyit e.2.1 = true) :
    ∀ f w i, mayyit i = true → Q.C f w i = 0
  | 0, w, i, hi => by simp only [C]; exact Q.base_mayyit w i (hm i hi).1
  | f + 1, w, i, hi => by
    simp only [C, Q.base_mayyit w i (hm i hi).1, Nat.zero_add]
    exact sum_zero _ _ (fun e he => by
      split
      · rw [mayyit_sifr mayyit hm f _ _ ((hm i hi).2 e he), Nat.mul_zero]
      · rfl)

theorem C_khatwa (f w i : Nat) : Q.C (f + 1) w i = Q.base w i +
    ((Q.saff i).map fun e => if e.1 ≤ w then e.2.2 * Q.C f (w - e.1) e.2.1 else 0).sum := rfl

/-- **الطولُ الكافي:** إن كان على كلّ مدخلٍ من صنفٍ غيرِ ميّت ‎`i`‎ إلى صنفٍ غيرِ ميّت ‎`j`‎ بوزنٍ ‎`u`‎
‎`pot j + 1 ≤ pot i + K·u`‎، وكان الميّتُ لا يقبل ولا ينتقل إلّا إلى ميّت، فالعدُّ بطولٍ ‎`f + 1`‎ هو العدُّ بطولٍ ‎`f`‎
متى كان ‎`K·w + pot i ≤ f`‎. -/
theorem C_mustaqill (K : Nat) (pot : Nat → Nat) (mayyit : Nat → Bool)
    (hm : ∀ i, mayyit i = true → Q.F i = false ∧ ∀ e ∈ Q.saff i, mayyit e.2.1 = true)
    (hp : ∀ i, mayyit i = false → ∀ e ∈ Q.saff i, mayyit e.2.1 = false →
      pot e.2.1 + 1 ≤ pot i + K * e.1) :
    ∀ f w i, K * w + pot i ≤ f → Q.C (f + 1) w i = Q.C f w i
  | 0, w, i, hf => by
    have hw : K * w = 0 := by omega
    have hpi : pot i = 0 := by omega
    rw [C_khatwa]; simp only [C]
    rw [sum_zero _ _ (fun e he => ?_)]; · rfl
    split
    · rename_i hle
      cases hmi : mayyit e.2.1
      · cases hmi' : mayyit i
        · have := hp i hmi' e he hmi
          have : K * e.1 ≤ K * w := Nat.mul_le_mul_left K hle
          omega
        · have := (hm i hmi').2 e he; rw [hmi] at this; exact absurd this (by decide)
      · have := Q.mayyit_sifr mayyit hm 0 (w - e.1) _ hmi
        simp only [C] at this; rw [this, Nat.mul_zero]
    · rfl
  | f + 1, w, i, hf => by
    rw [C_khatwa, C_khatwa Q f]
    congr 2
    apply List.map_congr_left; intro e he
    split
    · rename_i hle
      cases hmi : mayyit e.2.1
      · cases hmi' : mayyit i
        · have hpe := hp i hmi' e he hmi
          have ek : K * (w - e.1) + K * e.1 = K * w := by rw [← Nat.mul_add, Nat.sub_add_cancel hle]
          rw [C_mustaqill K pot mayyit hm hp f (w - e.1) e.2.1 (by omega)]
        · rw [Q.mayyit_sifr mayyit hm (f + 1) _ _ ((hm i hmi').2 e he),
            Q.mayyit_sifr mayyit hm f _ _ ((hm i hmi').2 e he)]
      · rw [Q.mayyit_sifr mayyit hm (f + 1) _ _ hmi, Q.mayyit_sifr mayyit hm f _ _ hmi]
    · rfl

/-- **ثباتُ العدّ:** طولان كافيان يعطيان العددَ نفسَه. -/
theorem C_thabit (K : Nat) (pot : Nat → Nat) (mayyit : Nat → Bool)
    (hm : ∀ i, mayyit i = true → Q.F i = false ∧ ∀ e ∈ Q.saff i, mayyit e.2.1 = true)
    (hp : ∀ i, mayyit i = false → ∀ e ∈ Q.saff i, mayyit e.2.1 = false →
      pot e.2.1 + 1 ≤ pot i + K * e.1) (w i : Nat) :
    ∀ d f, K * w + pot i ≤ f → Q.C (f + d) w i = Q.C f w i
  | 0, f, _ => rfl
  | d + 1, f, hf => by
    rw [show f + (d + 1) = (f + d) + 1 by omega, Q.C_mustaqill K pot mayyit hm hp _ _ _ (by omega)]
    exact C_thabit K pot mayyit hm hp w i d f hf

/-- **طولان كافيان:** كلُّ طولين لا يقلّان عن ‎`K·w + pot i`‎ يعطيان العددَ نفسَه. -/
theorem C_thabit2 (K : Nat) (pot : Nat → Nat) (mayyit : Nat → Bool)
    (hm : ∀ i, mayyit i = true → Q.F i = false ∧ ∀ e ∈ Q.saff i, mayyit e.2.1 = true)
    (hp : ∀ i, mayyit i = false → ∀ e ∈ Q.saff i, mayyit e.2.1 = false →
      pot e.2.1 + 1 ≤ pot i + K * e.1) (w i f f' : Nat)
    (hf : K * w + pot i ≤ f) (hf' : K * w + pot i ≤ f') : Q.C f w i = Q.C f' w i := by
  have h1 := Q.C_thabit K pot mayyit hm hp w i (f - (K * w + pot i)) (K * w + pot i) (Nat.le_refl _)
  have h2 := Q.C_thabit K pot mayyit hm hp w i (f' - (K * w + pot i)) (K * w + pot i) (Nat.le_refl _)
  rw [show K * w + pot i + (f - (K * w + pot i)) = f by omega] at h1
  rw [show K * w + pot i + (f' - (K * w + pot i)) = f' by omega] at h2
  rw [h1, h2]

/-- **الخطوةُ بوزنٍ واحد:** إن لم يزد وزنُ مدخلٍ على واحد، وكان ‎`Pm`‎ فوق الجهد كلِّه و‎`K ≥ 1`‎، فالعدُّ في الدرجة
‎`n + 1`‎ بطول ‎`K·(n+1) + Pm`‎ قبولٌ ثمّ مجموعُ المداخل: ما وزنُه صفرٌ يُعدّ في الدرجة نفسِها، وما وزنُه واحدٌ في ‎`n`‎،
كلٌّ بطوله الكافي. -/
theorem C_khatwa1 (K Pm : Nat) (pot : Nat → Nat) (mayyit : Nat → Bool)
    (hm : ∀ i, mayyit i = true → Q.F i = false ∧ ∀ e ∈ Q.saff i, mayyit e.2.1 = true)
    (hp : ∀ i, mayyit i = false → ∀ e ∈ Q.saff i, mayyit e.2.1 = false →
      pot e.2.1 + 1 ≤ pot i + K * e.1)
    (hK : 1 ≤ K) (hPm : ∀ i, pot i ≤ Pm) (hU : ∀ i, ∀ e ∈ Q.saff i, e.1 ≤ 1) (n i : Nat) :
    Q.C (K * (n + 1) + Pm) (n + 1) i = Q.base (n + 1) i +
      ((Q.saff i).map fun e => e.2.2 * (if e.1 = 0 then Q.C (K * (n + 1) + Pm) (n + 1) e.2.1
        else Q.C (K * n + Pm) n e.2.1)).sum := by
  obtain ⟨k, rfl⟩ : ∃ k, K = k + 1 := ⟨K - 1, by omega⟩
  have ea : (k + 1) * (n + 1) = (k + 1) * n + (k + 1) := Nat.mul_succ _ _
  rw [show (k + 1) * (n + 1) + Pm = ((k + 1) * n + k + Pm) + 1 by omega, C_khatwa]
  congr 2
  apply List.map_congr_left; intro e he
  have h1 := hU i e he
  cases hmj : mayyit e.2.1
  · cases hmi : mayyit i
    · have hpe := hp i hmi e he hmj
      have hpj := hPm e.2.1
      have hpi := hPm i
      by_cases h0 : e.1 = 0
      · rw [h0, Nat.mul_zero] at hpe
        rw [if_pos (by omega), if_pos h0, h0, Nat.sub_zero]
        rw [Q.C_thabit2 (k + 1) pot mayyit hm hp _ _ _ ((k + 1) * n + k + Pm + 1) (by omega) (by omega)]
      · have e1 : e.1 = 1 := by omega
        rw [if_pos (by omega), if_neg h0, e1, Nat.add_sub_cancel]
        rw [Q.C_thabit2 (k + 1) pot mayyit hm hp _ _ _ ((k + 1) * n + Pm) (by omega) (by omega)]
    · have := (hm i hmi).2 e he; rw [hmj] at this; exact absurd this (by decide)
  · split
    · split
      · rw [Q.mayyit_sifr mayyit hm _ _ _ hmj, Q.mayyit_sifr mayyit hm _ _ _ hmj]
      · rw [Q.mayyit_sifr mayyit hm _ _ _ hmj, Q.mayyit_sifr mayyit hm _ _ _ hmj]
    · omega

end Asnaf

/-! ## ٤. الحسابُ الصنفيّ لآلة -/

/-- **الحسابُ الصنفيّ لآلةٍ من ابتدائها:** أصنافٌ متكافئةٌ على حالاتٍ مغلقةٍ تحوي الابتداء، وصنفٌ ميّت، وجهدٌ ‎`pot`‎ بثابتٍ ‎`K`‎
يحدّ الطولَ الكافي. -/
structure Hisab (M : Machine) (q0 : Nat) where
  Q : Asnaf
  U : Nat
  s : Nat → Nat
  P : Nat → Prop
  mutakafi : Mutakafi M Q U s P
  bidaya : P q0
  K : Nat
  pot : Nat → Nat
  mayyit : Nat → Bool
  mayyit_sahih : ∀ i, mayyit i = true → Q.F i = false ∧ ∀ e ∈ Q.saff i, mayyit e.2.1 = true
  juhd : ∀ i, mayyit i = false → ∀ e ∈ Q.saff i, mayyit e.2.1 = false → pot e.2.1 + 1 ≤ pot i + K * e.1

namespace Hisab
variable {M : Machine} {q0 : Nat} (h : Hisab M q0)

/-- **عددُ الآلة بالحساب الصنفيّ:** عددُ المالك من الابتداء بوزنٍ ‎`w`‎ وطولٍ كافٍ هو العدُّ على صفّ صنف الابتداء بأيّ طولٍ كافٍ. -/
theorem C_eq (f f' w : Nat) (hf : h.K * w + h.pot (h.s q0) ≤ f) (hf' : h.K * w + h.pot (h.s q0) ≤ f') :
    M.C f w q0 = h.Q.C f' w (h.s q0) := by
  rw [qanun_adad M h.Q h.U h.s h.P h.mutakafi f w q0 h.bidaya]
  exact h.Q.C_thabit2 h.K h.pot h.mayyit h.mayyit_sahih h.juhd w (h.s q0) f f' hf hf'

/-- **عددُ الدرجة بالحساب الصنفيّ:** ‎`lev K' q0 j`‎ (عددُ ما وزنُه ‎`j`‎ بطول ‎`K'·j`‎) هو العدُّ على صفّ صنف الابتداء متى كفى الطولان. -/
theorem lev_eq (K' j f : Nat) (hK : h.K * j + h.pot (h.s q0) ≤ K' * j) (hf : h.K * j + h.pot (h.s q0) ≤ f) :
    M.lev K' q0 j = h.Q.C f j (h.s q0) :=
  h.C_eq (K' * j) f j hK hf

end Hisab
end SLGE
