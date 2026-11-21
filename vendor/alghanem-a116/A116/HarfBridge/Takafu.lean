import A116.Harf.Khana
import A116.Harf.Maqta
import A116.Harf.Satr
import A116.Harf.Thunai
import A116.Hadd
import A116.ContinueCount

/-!
# الجسر: آلةُ Algebra هي قيدُ الحدّ في الغانم، لكلّ كلمة (ADR ٣)

`Harf` عرّف الخانةَ والترخيصَ بنفسه (آلةُ مقاطع بحالاتٍ مسمّاة، الهمزةُ أوّلُ الحوامل)، و`A116.Hadd` عرّفه
بالتقطيع (`Stages.parse`) والأصناف (`kindOf`) وقيدِ المثل (`geminateB`) ومدِّ الفرق (`isFarq`). هذه الوحدةُ
وحدَها تقرأ الطرفين، وتبرهن:

* `proj_bijective`: إسقاطُ الخانة من ترتيب Algebra إلى ترتيب الغانم تقابلٌ على الـ116.
* **`wasl_eq_strictB`**: لكلّ كلمة `w`، `Harf.waslB w = A116.Hadd.strictB (projW w)`.
* **`waqf_eq_strictPauseB`**: لكلّ كلمة `w`، `Harf.waqfB w = A116.Hadd.strictPauseB (projW w)`.
* `mutant_refuted`: آلةٌ تقبل المقطعَ الطويلَ المغلقَ بلا مثل (طفرةُ `MUTANT_CVVC_WITHOUT_GEMINATE`)
  تخالف `strictB` على «قَالْتُ» — فالتكافؤُ يرفض الطفرة.

الطريق: آلةٌ وسيطةٌ على خانات الغانم (`runF`) تحمل حالةَ ما قبلُ (للصنف) وحالةَ الآلة الثلاثيّة (`δC`/`δ`)
وما ينتظره قيدُ المثل (`Pend`)؛ تُبرهَن مساويةً لـ`strictB` بالاستقراء على الكلمة (`runF_eq`)، ثمّ تُطابَق
خطوةُ Algebra بخطوتها على كلّ (حال، خانة) بالحساب (`decide +kernel` على القوائم التامّة `Hal.all`
و`Khana.all`، وتمامُهما مبرهَن: `Hal.mem_all`، `Khana.mem_all`).
-/

set_option autoImplicit false

namespace HarfBridge

open A116 A116.Stages A116.Ternary A116.Hadd A116.Ladder

/-! ## ١. الإسقاط -/

def haalTo : Harf.Haal → Haraka
  | .fath => .fatha
  | .kasr => .kasra
  | .damm => .damma
  | .sukun => .sukun

def proj (x : Harf.Khana) : Cell :=
  ⟨A116.Ladder.carrierOf (Harf.charOf x.hamil), haalTo x.haal⟩

def projW (w : List Harf.Khana) : List Cell := w.map proj

def unproj (c : Cell) : Harf.Khana :=
  (Harf.Khana.all.find? fun x => proj x == c).getD ⟨0, .sukun⟩

theorem proj_bijective :
    (∀ x ∈ Harf.Khana.all, unproj (proj x) = x) ∧ (∀ c ∈ A116.cells, proj (unproj c) = c) := by
  decide +kernel

/-! ## ٢. الآلةُ الوسيطة على خانات الغانم -/

inductive Pend where
  | none | afterV | need (k : Fin carrierCount)
  deriving DecidableEq, Repr

structure FS where
  prev : Option Haraka
  st : St
  g : Pend
  deriving DecidableEq, Repr

def chk : Pend → Cell → Bool
  | .need k, x => x.carrier == k
  | _, _ => true

def pend' : Pend → K → Cell → Pend
  | _, .v, _ => .afterV
  | .afterV, .c, x => .need x.carrier
  | _, _, _ => .none

def stepF (d : St → K → St) : Option FS → Cell → Option FS
  | none, _ => none
  | some s, x =>
    if chk s.g x = true ∧ d s.st (kindOne s.prev x) ≠ .dead then
      some ⟨some x.haraka, d s.st (kindOne s.prev x), pend' s.g (kindOne s.prev x) x⟩
    else none

def runF (d : St → K → St) (e : Pend → Bool) : Option FS → List Cell → Bool
  | none, _ => false
  | some s, [] => s.st != .dead && e s.g
  | some s, x :: t => runF d e (stepF d (some s) x) t

theorem runF_cons (d : St → K → St) (e : Pend → Bool) (o : Option FS) (x : Cell) (t : List Cell) :
    runF d e o (x :: t) = runF d e (stepF d o x) t := by
  cases o <;> simp [runF, stepF]

def accG (d : St → K → St) : St → List K → Bool
  | s, [] => s != .dead
  | s, x :: t => accG d (d s x) t

theorem accG_dead (d : St → K → St) (hd : ∀ x, d .dead x = .dead) : ∀ t, accG d .dead t = false
  | [] => rfl
  | x :: t => by simp only [accG, hd]; exact accG_dead d hd t

theorem accC_eq : ∀ (s : St) (k : List K), accC s k = accG δC s k
  | _, [] => rfl
  | s, x :: t => by simp only [accC, accG]; exact accC_eq _ t

theorem acc_eq : ∀ (s : St) (k : List K), acc s k = accG δ s k
  | _, [] => rfl
  | s, x :: t => by simp only [acc, accG]; exact acc_eq _ t

/-! ## ٣. قيدُ المثل جاريًا -/

def dummy : Cell := ⟨⟨0, by decide⟩, .sukun⟩

def gemW : Pend → List (K × Cell) → Bool
  | .none, l => geminateB l
  | .afterV, l => stepOK (.v, dummy) l && geminateB l
  | .need _, [] => false
  | .need k, a :: l => a.2.carrier == k && geminateB (a :: l)

def gemP : Pend → List (K × Cell) → Bool
  | .none, l => geminatePauseB l
  | .afterV, l => stepOKPause (.v, dummy) l && geminatePauseB l
  | .need _, [] => true
  | .need k, a :: l => a.2.carrier == k && geminatePauseB (a :: l)

theorem stepOK_v (x y : Cell) : ∀ l, stepOK (.v, x) l = stepOK (.v, y) l
  | [] => rfl
  | [(k, _)] => by cases k <;> rfl
  | (k, _) :: (_, _) :: _ => by cases k <;> rfl

theorem stepOKPause_v (x y : Cell) : ∀ l, stepOKPause (.v, x) l = stepOKPause (.v, y) l
  | [] => rfl
  | [(k, _)] => by cases k <;> rfl
  | (k, _) :: (_, _) :: _ => by cases k <;> rfl

theorem stepOK_nv (kk : K) (h : kk ≠ .v) (x : Cell) : ∀ l, stepOK (kk, x) l = true := by
  intro l; cases kk <;> simp at h <;> rcases l with _ | ⟨⟨k2, y⟩, _ | ⟨⟨k3, z⟩, r⟩⟩ <;> rfl

theorem stepOKPause_nv (kk : K) (h : kk ≠ .v) (x : Cell) : ∀ l, stepOKPause (kk, x) l = true := by
  intro l; cases kk <;> simp at h <;> rcases l with _ | ⟨⟨k2, y⟩, _ | ⟨⟨k3, z⟩, r⟩⟩ <;> rfl

theorem stepOK_v_nc (d x : Cell) (kk : K) (h : kk ≠ .c) (l : List (K × Cell)) :
    stepOK (.v, d) ((kk, x) :: l) = true := by
  cases kk <;> simp at h <;> rcases l with _ | ⟨⟨k2, y⟩, r⟩ <;> rfl

theorem stepOKPause_v_nc (d x : Cell) (kk : K) (h : kk ≠ .c) (l : List (K × Cell)) :
    stepOKPause (.v, d) ((kk, x) :: l) = true := by
  cases kk <;> simp at h <;> rcases l with _ | ⟨⟨k2, y⟩, r⟩ <;> rfl

theorem beq_symm' (a b : Fin carrierCount) : (a == b) = (b == a) := by
  rw [Bool.eq_iff_iff, beq_iff_eq, beq_iff_eq]
  exact ⟨Eq.symm, Eq.symm⟩

theorem gemW_cons (g : Pend) (kk : K) (x : Cell) (rest : List (K × Cell)) :
    gemW g ((kk, x) :: rest) = (chk g x && gemW (pend' g kk x) rest) := by
  cases g with
  | none =>
    cases kk with
    | v => simp [gemW, geminateB, chk, pend', stepOK_v x dummy]
    | c => simp [gemW, geminateB, chk, pend', stepOK_nv .c (by decide)]
    | cv => simp [gemW, geminateB, chk, pend', stepOK_nv .cv (by decide)]
  | afterV =>
    cases kk with
    | v => simp [gemW, geminateB, chk, pend', stepOK_v x dummy, stepOK_v_nc dummy x .v (by decide)]
    | cv => simp [gemW, geminateB, chk, pend', stepOK_nv .cv (by decide),
        stepOK_v_nc dummy x .cv (by decide)]
    | c =>
      rcases rest with _ | ⟨⟨k2, y⟩, r⟩
      · rfl
      · simp only [gemW, geminateB, chk, pend', stepOK, Bool.true_and]
        rw [beq_symm' x.carrier y.carrier]
  | need k =>
    cases kk with
    | v => simp [gemW, geminateB, chk, pend', stepOK_v x dummy]
    | c => simp [gemW, geminateB, chk, pend', stepOK_nv .c (by decide)]
    | cv => simp [gemW, geminateB, chk, pend', stepOK_nv .cv (by decide)]

theorem gemP_cons (g : Pend) (kk : K) (x : Cell) (rest : List (K × Cell)) :
    gemP g ((kk, x) :: rest) = (chk g x && gemP (pend' g kk x) rest) := by
  cases g with
  | none =>
    cases kk with
    | v => simp [gemP, geminatePauseB, chk, pend', stepOKPause_v x dummy]
    | c => simp [gemP, geminatePauseB, chk, pend', stepOKPause_nv .c (by decide)]
    | cv => simp [gemP, geminatePauseB, chk, pend', stepOKPause_nv .cv (by decide)]
  | afterV =>
    cases kk with
    | v => simp [gemP, geminatePauseB, chk, pend', stepOKPause_v x dummy,
        stepOKPause_v_nc dummy x .v (by decide)]
    | cv => simp [gemP, geminatePauseB, chk, pend', stepOKPause_nv .cv (by decide),
        stepOKPause_v_nc dummy x .cv (by decide)]
    | c =>
      rcases rest with _ | ⟨⟨k2, y⟩, r⟩
      · rfl
      · simp only [gemP, geminatePauseB, chk, pend', stepOKPause, stepOK, Bool.true_and]
        rw [beq_symm' x.carrier y.carrier]
  | need k =>
    cases kk with
    | v => simp [gemP, geminatePauseB, chk, pend', stepOKPause_v x dummy]
    | c => simp [gemP, geminatePauseB, chk, pend', stepOKPause_nv .c (by decide)]
    | cv => simp [gemP, geminatePauseB, chk, pend', stepOKPause_nv .cv (by decide)]

def endW : Pend → Bool
  | .need _ => false
  | _ => true

def endP : Pend → Bool := fun _ => true

theorem gemW_nil (g : Pend) : gemW g [] = endW g := by cases g <;> rfl

theorem gemP_nil (g : Pend) : gemP g [] = endP g := by cases g <;> rfl

/-- الآلةُ الوسيطة هي الأصنافُ والآلةُ الثلاثيّةُ وقيدُ المثل معًا. -/
theorem runF_eq (d : St → K → St) (hd : ∀ x, d .dead x = .dead) (e : Pend → Bool)
    (gem : Pend → List (K × Cell) → Bool) (hnil : ∀ g, gem g [] = e g)
    (hcons : ∀ g kk x rest, gem g ((kk, x) :: rest) = (chk g x && gem (pend' g kk x) rest)) :
    ∀ (s : FS) (w : List Cell),
      runF d e (some s) w = (accG d s.st (kindGo s.prev w) && gem s.g ((kindGo s.prev w).zip w))
  | s, [] => by simp [runF, kindGo, accG, hnil]
  | s, x :: t => by
    simp only [runF, stepF, kindGo, accG, List.zip_cons_cons, hcons]
    split
    · next hc =>
      rw [runF_eq d hd e gem hnil hcons _ t]
      simp [hc.1]
    · next hc =>
      simp only [runF]
      by_cases h1 : chk s.g x = true
      · have h2 : d s.st (kindOne s.prev x) = .dead :=
          Classical.byContradiction fun h => hc ⟨h1, h⟩
        rw [h2, accG_dead d hd]; simp
      · simp at h1; simp [h1]

theorem δC_dead (x : K) : δC .dead x = .dead := by cases x <;> rfl
theorem δ_dead (x : K) : δ .dead x = .dead := by cases x <;> rfl

def initS : FS := ⟨none, .start, .none⟩
def farqS : FS := ⟨some .sukun, .nv, .none⟩

theorem isFarq_shape {w : List Cell} (h : isFarq w = true) :
    ∃ l t, w = atom 'ء' .fatha :: atom 'ا' .sukun :: l :: t := by
  match w, h with
  | a :: b :: l :: t, h =>
    simp only [isFarq, Bool.and_eq_true, beq_iff_eq] at h
    exact ⟨l, t, by rw [h.1.1, h.1.2]⟩

theorem kind_farq_head : kindOne none (atom 'ء' .fatha) = .cv ∧
    kindOne (some .fatha) (atom 'ا' .sukun) = .v := by decide

theorem strictB_runF (w : List Cell) : strictB w =
    if isFarq w then runF δC endW (some farqS) (w.drop 2) else runF δC endW (some initS) w := by
  unfold strictB haddB
  rw [continueB_eq_accC, accC_eq]
  cases hf : isFarq w with
  | true =>
    simp only [↓reduceIte]
    obtain ⟨l, t, rfl⟩ := isFarq_shape hf
    simp only [List.drop_succ_cons, List.drop_zero, kindOf, kindGo, kind_farq_head,
      List.zip_cons_cons, accG]
    rw [runF_eq δC δC_dead endW gemW gemW_nil gemW_cons farqS (l :: t)]
    rfl
  | false =>
    simp only [Bool.false_eq_true, ↓reduceIte]
    rw [runF_eq δC δC_dead endW gemW gemW_nil gemW_cons initS w]
    rfl

theorem strictPauseB_runF (w : List Cell) : strictPauseB w =
    if isFarq w then runF δ endP (some farqS) (w.drop 2) else runF δ endP (some initS) w := by
  unfold strictPauseB haddPauseB
  rw [pauseB_eq_acc, acc_eq]
  cases hf : isFarq w with
  | true =>
    simp only [↓reduceIte]
    obtain ⟨l, t, rfl⟩ := isFarq_shape hf
    simp only [List.drop_succ_cons, List.drop_zero, kindOf, kindGo, kind_farq_head,
      List.zip_cons_cons, accG]
    rw [runF_eq δ δ_dead endP gemP gemP_nil gemP_cons farqS (l :: t)]
    rfl
  | false =>
    simp only [Bool.false_eq_true, ↓reduceIte]
    rw [runF_eq δ δ_dead endP gemP gemP_nil gemP_cons initS w]
    rfl

/-! ## ٤. حالُ Algebra صورةً في الآلة الوسيطة -/

open Harf in
def sim : Hal → Option FS
  | .bad' => some initS
  | .hamzaAwwal => some ⟨some .fatha, .n, .none⟩
  | .farq => some ⟨some .sukun, .nv, .afterV⟩
  | .nawah q => some ⟨some (haalTo q), .n, .none⟩
  | .madd => some ⟨some .sukun, .nv, .afterV⟩
  | .qasir => some ⟨some .sukun, .nc, .none⟩
  | .tawilFarq => some ⟨some .sukun, .nvc, .none⟩
  | .tawil k => some ⟨some .sukun, .nvc, .need (proj ⟨k, .sukun⟩).carrier⟩
  | .khatm => some ⟨some .sukun, .fin, .none⟩
  | .maddHadd => some ⟨some .sukun, .nv, .afterV⟩
  | .mayyit => none

open Harf in
/-- الحالُ «العاديّ»: بعد الخانة الأولى وما يخصّ مدَّ الفرق. -/
def good : Hal → Bool
  | .bad' | .hamzaAwwal | .farq | .maddHadd => false
  | _ => true

/-- الشرطُ العامّ: على كلّ حالٍ عاديّ تُطابَق الخطوتان ويبقى الحالُ عاديًّا، والقبولُ هو القبول. -/
theorem run_sim (step : Harf.Hal → Harf.Khana → Harf.Hal) (d : St → K → St) (e : Pend → Bool)
    (q : Harf.Hal → Bool) (inv : Harf.Hal → Bool)
    (hc : ∀ a, inv a = true → ∀ x, inv (step a x) = true ∧ sim (step a x) = stepF d (sim a) (proj x))
    (ha : ∀ a, inv a = true → q a = runF d e (sim a) []) :
    ∀ (a : Harf.Hal) (w : List Harf.Khana), inv a = true →
      q (Harf.run step a w) = runF d e (sim a) (projW w)
  | a, [], h => ha a h
  | a, x :: t, h => by
    simp only [Harf.run, projW, List.map_cons]
    rw [runF_cons, ← (hc a h x).2]
    exact run_sim step d e q inv hc ha _ t (hc a h x).1

/-- الكلمةُ كلُّها: الخاناتُ الثلاثُ الأولى بالتفصيل (الابتداء ومدُّ الفرق)، ثمّ `run_sim`. -/
theorem main (step : Harf.Hal → Harf.Khana → Harf.Hal) (d : St → K → St) (e : Pend → Bool)
    (q : Harf.Hal → Bool) (inv : Harf.Hal → Bool)
    (hc : ∀ a, inv a = true → ∀ x, inv (step a x) = true ∧ sim (step a x) = stepF d (sim a) (proj x))
    (ha : ∀ a, inv a = true → q a = runF d e (sim a) [])
    (h0 : q .bad' = runF d e (some initS) [])
    (h1 : ∀ x, x ≠ Harf.k 'ء' .fath → inv (step .bad' x) = true ∧
      sim (step .bad' x) = stepF d (some initS) (proj x) ∧ proj x ≠ atom 'ء' .fatha)
    (h1' : step .bad' (Harf.k 'ء' .fath) = .hamzaAwwal ∧ proj (Harf.k 'ء' .fath) = atom 'ء' .fatha ∧
      stepF d (some initS) (atom 'ء' .fatha) = sim .hamzaAwwal)
    (h2 : ∀ y, y ≠ Harf.k 'ا' .sukun → inv (step .hamzaAwwal y) = true ∧
      sim (step .hamzaAwwal y) = stepF d (sim .hamzaAwwal) (proj y) ∧ proj y ≠ atom 'ا' .sukun)
    (h2' : step .hamzaAwwal (Harf.k 'ا' .sukun) = .farq ∧ proj (Harf.k 'ا' .sukun) = atom 'ا' .sukun ∧
      stepF d (sim .hamzaAwwal) (atom 'ا' .sukun) = sim .farq)
    (hq1 : q .hamzaAwwal = runF d e (sim .hamzaAwwal) [] ∧ q .farq = runF d e (sim .farq) [])
    (h3 : ∀ z, z.hamil ≠ Harf.lam → inv (step .farq z) = true ∧
      sim (step .farq z) = stepF d (sim .farq) (proj z) ∧ (proj z).carrier ≠ A116.Ladder.carrierOf 'ل')
    (h3' : ∀ z, z.hamil = Harf.lam → inv (step .farq z) = true ∧
      sim (step .farq z) = stepF d (some farqS) (proj z) ∧ (proj z).carrier = A116.Ladder.carrierOf 'ل') :
    ∀ w, q (Harf.run step .bad' w) =
      if isFarq (projW w) then runF d e (some farqS) ((projW w).drop 2)
      else runF d e (some initS) (projW w) := by
  intro w
  have hR := run_sim step d e q inv hc ha
  match w with
  | [] => simpa [Harf.run, projW, isFarq] using h0
  | x :: t =>
    by_cases hx : x = Harf.k 'ء' .fath
    · subst hx
      match t with
      | [] =>
        simp [Harf.run, projW, isFarq, h1'.1, h1'.2.1, runF_cons, h1'.2.2, hq1.1]
      | y :: t =>
        by_cases hy : y = Harf.k 'ا' .sukun
        · subst hy
          match t with
          | [] =>
            simp [Harf.run, projW, isFarq, h1'.1, h1'.2.1, h2'.1, h2'.2.1, runF_cons, h1'.2.2,
              h2'.2.2, hq1.2]
          | z :: t =>
            by_cases hz : z.hamil = Harf.lam
            · obtain ⟨hi, hs, hcz⟩ := h3' z hz
              have hf : isFarq (projW (Harf.k 'ء' .fath :: Harf.k 'ا' .sukun :: z :: t)) = true := by
                simp [projW, isFarq, h1'.2.1, h2'.2.1, hcz]
              simp only [hf, ↓reduceIte]
              simp only [Harf.run, h1'.1, h2'.1, projW, List.map_cons, List.drop]
              rw [hR _ t hi, hs, ← runF_cons]
              rfl
            · obtain ⟨hi, hs, hcz⟩ := h3 z hz
              have hf : isFarq (projW (Harf.k 'ء' .fath :: Harf.k 'ا' .sukun :: z :: t)) = false := by
                simp [projW, isFarq, hcz]
              simp only [hf, Bool.false_eq_true, ↓reduceIte]
              simp only [Harf.run, h1'.1, h2'.1, projW, List.map_cons]
              rw [hR _ t hi, hs, runF_cons, runF_cons, runF_cons, h1'.2.1, h1'.2.2, h2'.2.1, h2'.2.2]
              rfl
        · obtain ⟨hi, hs, hpy⟩ := h2 y hy
          have hf : isFarq (projW (Harf.k 'ء' .fath :: y :: t)) = false := by
            cases t <;> simp [projW, isFarq, hpy]
          simp only [hf, Bool.false_eq_true, ↓reduceIte]
          simp only [Harf.run, h1'.1, projW, List.map_cons]
          rw [hR _ t hi, hs, runF_cons, runF_cons, h1'.2.1, h1'.2.2]
          rfl
    · obtain ⟨hi, hs, hpx⟩ := h1 x hx
      have hf : isFarq (projW (x :: t)) = false := by
        match t with
        | [] => rfl
        | [_] => rfl
        | _ :: _ :: _ => simp [projW, isFarq, hpx]
      simp only [hf, Bool.false_eq_true, ↓reduceIte]
      simp only [Harf.run, projW, List.map_cons]
      rw [hR _ t hi, hs, runF_cons]
      rfl

/-! ## ٥. التكافؤ -/

open Harf in
def invW (a : Hal) : Bool := good a && a != .khatm

theorem wasl_comm : ∀ a ∈ Harf.Hal.all, invW a = true → ∀ x ∈ Harf.Khana.all,
    invW (Harf.wasl a x) = true ∧ sim (Harf.wasl a x) = stepF δC (sim a) (proj x) := by
  decide +kernel

theorem wasl_acc : ∀ a ∈ Harf.Hal.all, invW a = true → Harf.qabilWasl a = runF δC endW (sim a) [] := by
  decide +kernel

theorem waqf_comm : ∀ a ∈ Harf.Hal.all, good a = true → ∀ x ∈ Harf.Khana.all,
    good (Harf.waqf a x) = true ∧ sim (Harf.waqf a x) = stepF δ (sim a) (proj x) := by
  decide +kernel

theorem waqf_acc : ∀ a ∈ Harf.Hal.all, good a = true → Harf.qabilWaqf a = runF δ endP (sim a) [] := by
  decide +kernel

theorem head_facts_wasl :
    (∀ x ∈ Harf.Khana.all, x ≠ Harf.k 'ء' .fath → invW (Harf.wasl .bad' x) = true ∧
      sim (Harf.wasl .bad' x) = stepF δC (some initS) (proj x) ∧ proj x ≠ atom 'ء' .fatha) ∧
    (Harf.wasl .bad' (Harf.k 'ء' .fath) = .hamzaAwwal ∧ proj (Harf.k 'ء' .fath) = atom 'ء' .fatha ∧
      stepF δC (some initS) (atom 'ء' .fatha) = sim .hamzaAwwal) ∧
    (∀ y ∈ Harf.Khana.all, y ≠ Harf.k 'ا' .sukun → invW (Harf.wasl .hamzaAwwal y) = true ∧
      sim (Harf.wasl .hamzaAwwal y) = stepF δC (sim .hamzaAwwal) (proj y) ∧ proj y ≠ atom 'ا' .sukun) ∧
    (Harf.wasl .hamzaAwwal (Harf.k 'ا' .sukun) = .farq ∧ proj (Harf.k 'ا' .sukun) = atom 'ا' .sukun ∧
      stepF δC (sim .hamzaAwwal) (atom 'ا' .sukun) = sim .farq) ∧
    (Harf.qabilWasl .bad' = runF δC endW (some initS) [] ∧
      Harf.qabilWasl .hamzaAwwal = runF δC endW (sim .hamzaAwwal) [] ∧
      Harf.qabilWasl .farq = runF δC endW (sim .farq) []) ∧
    (∀ z ∈ Harf.Khana.all, z.hamil ≠ Harf.lam → invW (Harf.wasl .farq z) = true ∧
      sim (Harf.wasl .farq z) = stepF δC (sim .farq) (proj z) ∧
      (proj z).carrier ≠ A116.Ladder.carrierOf 'ل') ∧
    (∀ z ∈ Harf.Khana.all, z.hamil = Harf.lam → invW (Harf.wasl .farq z) = true ∧
      sim (Harf.wasl .farq z) = stepF δC (some farqS) (proj z) ∧
      (proj z).carrier = A116.Ladder.carrierOf 'ل') := by
  decide +kernel

theorem head_facts_waqf :
    (∀ x ∈ Harf.Khana.all, x ≠ Harf.k 'ء' .fath → good (Harf.waqf .bad' x) = true ∧
      sim (Harf.waqf .bad' x) = stepF δ (some initS) (proj x) ∧ proj x ≠ atom 'ء' .fatha) ∧
    (Harf.waqf .bad' (Harf.k 'ء' .fath) = .hamzaAwwal ∧ proj (Harf.k 'ء' .fath) = atom 'ء' .fatha ∧
      stepF δ (some initS) (atom 'ء' .fatha) = sim .hamzaAwwal) ∧
    (∀ y ∈ Harf.Khana.all, y ≠ Harf.k 'ا' .sukun → good (Harf.waqf .hamzaAwwal y) = true ∧
      sim (Harf.waqf .hamzaAwwal y) = stepF δ (sim .hamzaAwwal) (proj y) ∧ proj y ≠ atom 'ا' .sukun) ∧
    (Harf.waqf .hamzaAwwal (Harf.k 'ا' .sukun) = .farq ∧ proj (Harf.k 'ا' .sukun) = atom 'ا' .sukun ∧
      stepF δ (sim .hamzaAwwal) (atom 'ا' .sukun) = sim .farq) ∧
    (Harf.qabilWaqf .bad' = runF δ endP (some initS) [] ∧
      Harf.qabilWaqf .hamzaAwwal = runF δ endP (sim .hamzaAwwal) [] ∧
      Harf.qabilWaqf .farq = runF δ endP (sim .farq) []) ∧
    (∀ z ∈ Harf.Khana.all, z.hamil ≠ Harf.lam → good (Harf.waqf .farq z) = true ∧
      sim (Harf.waqf .farq z) = stepF δ (sim .farq) (proj z) ∧
      (proj z).carrier ≠ A116.Ladder.carrierOf 'ل') ∧
    (∀ z ∈ Harf.Khana.all, z.hamil = Harf.lam → good (Harf.waqf .farq z) = true ∧
      sim (Harf.waqf .farq z) = stepF δ (some farqS) (proj z) ∧
      (proj z).carrier = A116.Ladder.carrierOf 'ل') := by
  decide +kernel

/-- **التكافؤ وصلًا**: لكلّ كلمة، آلةُ Algebra هي قيدُ الحدّ في الغانم. -/
theorem wasl_eq_strictB (w : List Harf.Khana) : Harf.waslB w = strictB (projW w) := by
  obtain ⟨f1, f1', f2, f2', ⟨q0, qa, qf⟩, f3, f3'⟩ := head_facts_wasl
  rw [strictB_runF]
  exact main Harf.wasl δC endW Harf.qabilWasl invW
    (fun a h x => wasl_comm a (Harf.Hal.mem_all a) h x (Harf.Khana.mem_all x))
    (fun a h => wasl_acc a (Harf.Hal.mem_all a) h) q0
    (fun x hx => f1 x (Harf.Khana.mem_all x) hx) f1'
    (fun y hy => f2 y (Harf.Khana.mem_all y) hy) f2' ⟨qa, qf⟩
    (fun z hz => f3 z (Harf.Khana.mem_all z) hz) (fun z hz => f3' z (Harf.Khana.mem_all z) hz) w

/-- **التكافؤ وقفًا**: لكلّ كلمة، آلةُ Algebra وقفًا هي قيدُ الحدّ وقفًا في الغانم. -/
theorem waqf_eq_strictPauseB (w : List Harf.Khana) : Harf.waqfB w = strictPauseB (projW w) := by
  obtain ⟨f1, f1', f2, f2', ⟨q0, qa, qf⟩, f3, f3'⟩ := head_facts_waqf
  rw [strictPauseB_runF]
  exact main Harf.waqf δ endP Harf.qabilWaqf good
    (fun a h x => waqf_comm a (Harf.Hal.mem_all a) h x (Harf.Khana.mem_all x))
    (fun a h => waqf_acc a (Harf.Hal.mem_all a) h) q0
    (fun x hx => f1 x (Harf.Khana.mem_all x) hx) f1'
    (fun y hy => f2 y (Harf.Khana.mem_all y) hy) f2' ⟨qa, qf⟩
    (fun z hz => f3 z (Harf.Khana.mem_all z) hz) (fun z hz => f3' z (Harf.Khana.mem_all z) hz) w

/-! ## ٦. الطفرة: المقطعُ الطويلُ المغلقُ بلا مثل -/

open Harf in
/-- `MUTANT_CVVC_WITHOUT_GEMINATE`: الآلةُ نفسُها إلّا أنّ `tawil` يقبل أيَّ متحرّكٍ بعده. -/
def waslMutant : Hal → Khana → Hal
  | .tawil _, x => if x.haal ≠ .sukun then .nawah x.haal else .mayyit
  | a, x => wasl a x

def mutantB (w : List Harf.Khana) : Bool := Harf.qabilWasl (Harf.run waslMutant .bad' w)

/-- **الطفرةُ مرفوضة**: تقبل «قَالْتُ» ويرفضها `strictB`؛ فلا تكافؤَ لها. -/
theorem mutant_refuted :
    mutantB Harf.qaaltu = true ∧ strictB (projW Harf.qaaltu) = false ∧
    ¬ ∀ w, mutantB w = strictB (projW w) := by
  have h : mutantB Harf.qaaltu = true ∧ strictB (projW Harf.qaaltu) = false := by decide +kernel
  exact ⟨h.1, h.2, fun hall => by have := hall Harf.qaaltu; rw [h.1, h.2] at this; simp at this⟩

end HarfBridge
