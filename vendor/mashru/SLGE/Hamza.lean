import SLGE.Law

/-!
# الهمزات تحت القانون: الابتداء والوصل والوقف

* **همزة القطع** حاملٌ كسائر الحوامل: ‎ء‎ رقمُه ‎0‎، أوّلُ المخارج.
* **همزة الوصل نتيجة:** الكلمةُ التي أوّلُها ساكن (‎اكْتُبْ = ْكْتُبْ‎ في الأصل) ممتنعةٌ ابتداءً بقانون الابتداء؛
  وأدنى إصلاحٍ مكتمل خانةٌ واحدةٌ متحرّكةٌ قبلها، وأصغرُها رقمًا بحركةٍ معيّنة همزةٌ بتلك الحركة.
  والحركةُ (كسرة، وضمّة إن كان الثالثُ مضمومًا، وفتحة مع أل) **وسيطٌ معلَن** لا نتيجة.
* **سقوطها في الوصل:** بعد متحرّك لا حاجة إليها؛ بعد مدٍّ يلتقي ساكنان فيُحذف المدّ؛
  بعد ساكنٍ مُغلِق يلتقي ساكنان فيُحرَّك. وكلاهما **التعديلُ الوحيد لخانةٍ واحدة الحافظُ للوزن**
  (عدد الصوامت): المدّ وزنُه ‎0‎ فحذفُه لا ينقص الدالّ، والمُغلِق وزنُه ‎1‎ فحذفُه ينقصه.
  واختيارُ الكسرة من بين الحركات الثلاث وسيطٌ معلَن.
-/

namespace SLGE
namespace Law

/-! ## همزة الوصل: الإصلاحُ الأدنى للابتداء -/

theorem fin_start_mover : ∀ m < 116, m % 4 < 3 → m / 4 ≠ 2 → δ 0 m = 1 + m % 4 := by decide +kernel

set_option synthInstance.maxHeartbeats 0 in
set_option synthInstance.maxSize 4096 in
theorem fin_free_suk_mov' : ∀ h < 3, ∀ c < 29, ∀ m < 116,
    (c ≠ 2 ∧ m % 4 < 3 ∧ m / 4 ≠ 2 ∧ conflict c (m / 4) = false) →
    δ (δ (1 + h) (4 * c + 3)) m = 1 + m % 4 := by decide +kernel

theorem fin_free_suk_mov (h : Nat) (hh : h < 3) (c : Nat) (hc : c < 29) (hc2 : c ≠ 2) (m : Nat)
    (hm : m < 116) (hm3 : m % 4 < 3) (hmA : m / 4 ≠ 2) (hcf : conflict c (m / 4) = false) :
    δ (δ (1 + h) (4 * c + 3)) m = 1 + m % 4 :=
  fin_free_suk_mov' h hh c hc m hm ⟨hc2, hm3, hmA, hcf⟩

/-- **قانون الابتداء:** ما أوّلُه ساكنٌ ممتنعٌ ابتداءً، أيًّا كان ما بعده. -/
theorem sukun_first_dead (c : Nat) (hc : c < 29) (u : List Nat) : run 0 ((4 * c + 3) :: u) = 96 := by
  have : δ 0 (4 * c + 3) = 96 := by
    have := (by decide +kernel : ∀ c < 29, δ 0 (4 * c + 3) = 96) c hc; exact this
  simp only [run, this, run_dead]

/-- **همزةُ الوصل تُصلح ولا تزيد قيدًا:** الكلمةُ بهمزةٍ متحرّكةٍ قبل ساكنها تسير سيرَ ما بعد الساكن. -/
theorem wasl_hamza_repair (h c m : Nat) (hh : h < 3) (hc : c < 29) (hc2 : c ≠ 2) (hm : m < 116)
    (hm3 : m % 4 < 3) (hmA : m / 4 ≠ 2) (hcf : conflict c (m / 4) = false) (rest : List Nat) : run 0 (h :: (4 * c + 3) :: m :: rest) = run 0 (m :: rest) := by
  have e0 : δ 0 h = 1 + h := by
    have := (by decide +kernel : ∀ h < 3, δ 0 h = 1 + h) h hh; exact this
  simp only [run, e0, fin_free_suk_mov h hh c hc hc2 m hm hm3 hmA hcf, fin_start_mover m hm hm3 hmA]

/-- **الإصلاحُ بخانةٍ واحدة:** خانةٌ ‎b‎ قبل الساكن ترخّص الكلمةَ إن كانت متحرّكة، وتمنعها إن لم تكن. -/
theorem prefix_licenses (b c m : Nat) (hb : b < 117) (hc : c < 29) (hc2 : c ≠ 2) (hm : m < 116)
    (hm3 : m % 4 < 3) (hmA : m / 4 ≠ 2) (hcf : conflict c (m / 4) = false) (rest : List Nat) :
    (b < 116 ∧ b % 4 < 3 ∧ b / 4 ≠ 2 → run 0 (b :: (4 * c + 3) :: m :: rest) = run 0 (m :: rest)) ∧
    (¬ (b < 116 ∧ b % 4 < 3 ∧ b / 4 ≠ 2) → run 0 (b :: (4 * c + 3) :: m :: rest) = 96) := by
  constructor
  · intro ⟨h1, h2, h3⟩
    simp only [run, fin_start_mover b h1 h2 h3, fin_free_suk_mov (b % 4) h2 c hc hc2 m hm hm3 hmA hcf,
      fin_start_mover m hm hm3 hmA]
  · intro hn
    have : δ 0 b = 96 := by
      by_cases h : δ 0 b = 96
      · exact h
      · have := fin_start b hb h
        have hA : b / 4 = 2 := by omega
        have : b = 8 + b % 4 := by omega
        rw [this]; exact alif_mover_dead 0 _ (by omega)
    simp only [run, this, δ_big _ (Nat.le_refl 96), run_dead]

/-- **الحدُّ الأدنى:** بين الخانات المرخِّصة بحركةٍ ‎h‎، أصغرُها رقمًا خانةُ الهمزة ‎(0, h)‎ —
لأنّ ‎ء‎ أوّلُ المخارج. -/
theorem hamza_least (h b : Nat) (hb : b % 4 = h) : cellEnc 0 h ≤ b ∧ cellEnc 0 h = h ∧
    carrierDec 0 = (0, 0) := by
  refine ⟨?_, ?_, by decide⟩ <;> simp [cellEnc, mixEnc] <;> omega

/-- حركةُ همزة الوصل (وسيطٌ معلَن): فتحةٌ مع أل، وضمّةٌ إن ضُمَّ الثالث، وإلّا كسرة. -/
def waslHaraka (isAl : Bool) (m : Nat) : Nat := if isAl then 0 else if m % 4 = 1 then 1 else 2

theorem waslHaraka_lt (isAl : Bool) (m : Nat) : waslHaraka isAl m < 3 := by
  unfold waslHaraka; split <;> (try split) <;> omega

/-- النطقُ في الابتداء: تُزاد همزةُ الوصل حيث يبدأ الأصلُ بساكن. -/
def ibtidaForm (isAl : Bool) : List Nat → List Nat
  | a :: m :: rest => if a < 116 ∧ a % 4 = 3 then waslHaraka isAl m :: a :: m :: rest else a :: m :: rest
  | u => u

/-! ## الوصل: حلُّ التقاء الساكنين عند همزة الوصل -/

theorem fin_junction4 : ∀ c < 29, ∀ m < 116, m % 4 < 3 → m / 4 ≠ c → δ (δ 4 (4 * c + 3)) m = 96 := by
  decide +kernel

theorem fin_junction5 : ∀ k < 29, ∀ c < 29, ∀ m < 116, m % 4 < 3 → δ (δ (67 + k) (4 * c + 3)) m = 96 := by
  decide +kernel

theorem fin_madd_edit : ∀ h < 3, ∀ s < 4,
    δ (1 + h) (4 * maddOf h + s) = (if s < 3 then (if h = 0 then 96 else 1 + s) else 4) ∧
    ω (1 + h) (4 * maddOf h + s) = (if s < 3 then 1 else 0) := by decide +kernel

set_option synthInstance.maxHeartbeats 0 in
set_option synthInstance.maxSize 4096 in
theorem fin_closed_edit' : ∀ h < 3, ∀ c < 29, ∀ s < 4, (c ≠ maddOf h ∧ c ≠ 2) →
    δ (1 + h) (4 * c + s) = (if s < 3 then 1 + s else 67 + c) ∧ ω (1 + h) (4 * c + s) = 1 := by
  decide +kernel

theorem fin_closed_edit (h : Nat) (hh : h < 3) (c : Nat) (hc : c < 29) (hcm : c ≠ maddOf h)
    (hc2 : c ≠ 2) (s : Nat) (hs : s < 4) :
    δ (1 + h) (4 * c + s) = (if s < 3 then 1 + s else 67 + c) ∧ ω (1 + h) (4 * c + s) = 1 :=
  fin_closed_edit' h hh c hc s hs ⟨hcm, hc2⟩

/-- **بعد متحرّك:** تسقط همزةُ الوصل بلا إصلاح — «قَالَ اكْتُبْ» ‎→‎ ‎qāla-ktub‎. -/
theorem wasl_after_mover (h c m : Nat) (hh : h < 3) (hc : c < 29) (hc2 : c ≠ 2) (hm : m < 116)
    (hm3 : m % 4 < 3) (hmA : m / 4 ≠ 2) (hcf : conflict c (m / 4) = false) (rest : List Nat) :
    run (1 + h) ((4 * c + 3) :: m :: rest) = run 0 (m :: rest) := by
  simp only [run, fin_free_suk_mov h hh c hc hc2 m hm hm3 hmA hcf, fin_start_mover m hm hm3 hmA]

/-- **بعد مدّ:** التقاءُ الساكنين ممتنع (ما لم يكن إدغامًا)؛ وتعديلُ خانة المدّ بأيّ حالةٍ أخرى
يغيّر الوزن، وحذفُها وحده يرخّص ويحفظ الوزن — «قَالُوا اكْتُبُوا» ‎→‎ ‎qālu-ktubū‎. -/
theorem wasl_after_madd (h c m : Nat) (hh : h < 3) (hc : c < 29) (hc2 : c ≠ 2) (hm : m < 116)
    (hm3 : m % 4 < 3) (hmA : m / 4 ≠ 2) (hcf : conflict c (m / 4) = false) (hne : m / 4 ≠ c) (rest : List Nat) :
    run (1 + h) ((4 * maddOf h + 3) :: (4 * c + 3) :: m :: rest) = 96 ∧
    ω (1 + h) (4 * maddOf h + 3) = 0 ∧
    (∀ s < 3, ω (1 + h) (4 * maddOf h + s) ≠ ω (1 + h) (4 * maddOf h + 3)) ∧
    run (1 + h) ((4 * c + 3) :: m :: rest) = run 0 (m :: rest) := by
  have e := fin_madd_edit h hh 3 (by omega)
  simp only [show ¬ (3 < 3) from by omega, if_false] at e
  refine ⟨?_, e.2, fun s hs => ?_, wasl_after_mover h c m hh hc hc2 hm hm3 hmA hcf rest⟩
  · have hd := fin_junction4 c hc m hm hm3 hne
    simp only [run, e.1, hd, run_dead]
  · have e' := fin_madd_edit h hh s (by omega)
    simp only [hs, ↓reduceIte] at e'; rw [e'.2, e.2]; omega

/-- **بعد ساكنٍ مُغلِق:** التقاءُ الساكنين ممتنع؛ وحذفُ المُغلِق ينقص الوزن، وتحريكُه بأيّ حركةٍ
يرخّص ويحفظ الوزن — «قُمِ اللَّيْلَ». (اختيارُ الكسرة وسيط.) -/
theorem wasl_after_closed (h k c m : Nat) (hh : h < 3) (hk : k < 29) (hkm : k ≠ maddOf h) (hk2 : k ≠ 2)
    (hc : c < 29) (hc2 : c ≠ 2) (hm : m < 116) (hm3 : m % 4 < 3) (hmA : m / 4 ≠ 2) (hcf : conflict c (m / 4) = false) (rest : List Nat) :
    run (1 + h) ((4 * k + 3) :: (4 * c + 3) :: m :: rest) = 96 ∧
    ω (1 + h) (4 * k + 3) = 1 ∧
    (∀ s < 3, ω (1 + h) (4 * k + s) = ω (1 + h) (4 * k + 3) ∧
      run (1 + h) ((4 * k + s) :: (4 * c + 3) :: m :: rest) = run 0 (m :: rest)) := by
  have e := fin_closed_edit h hh k hk hkm hk2 3 (by omega)
  simp only [show ¬ (3 < 3) from by omega, if_false] at e
  refine ⟨?_, e.2, fun s hs => ?_⟩
  · have hd := fin_junction5 k hk c hc m hm hm3
    simp only [run, e.1, hd, run_dead]
  · have e' := fin_closed_edit h hh k hk hkm hk2 s (by omega)
    simp only [hs, ↓reduceIte] at e'
    refine ⟨by rw [e'.2, e.2], ?_⟩
    simp only [run, e'.1, fin_free_suk_mov s hs c hc hc2 m hm hm3 hmA hcf, fin_start_mover m hm hm3 hmA]

/-! ## التجاور: ساكنٌ ثمّ متحرّكٌ من مخرجه — يمتنع، والإدغامُ إصلاحُه الأدنى -/

/-- **التجاورُ من قانون الوصل:** بعد ساكنٍ مُغلِقٍ حاملُه ‎k‎ لا يرد متحرّكٌ من مخرجه بحاملٍ آخر؛
وإبدالُ ‎k‎ بحامل المتحرّك (الإدغام) يرخّص بخانةٍ واحدةٍ ويحفظ الوزن. -/
theorem tajawur : ∀ k < 29, ∀ m < 29, conflict k m = true → ∀ s < 3,
    δ (67 + k) (4 * m + s) = 96 ∧ δ (67 + m) (4 * m + s) = 1 + s ∧
    ω (67 + k) (4 * m + s) = ω (67 + m) (4 * m + s) := by decide +kernel

/-- **حروفُ العلّة لا تدخل في التجاور**، والمثلان (الحاملُ نفسُه) إدغامٌ مرخَّص. -/
theorem tajawur_free : ∀ k < 29, ∀ m < 29, conflict k m = false → m ≠ 2 → ∀ s < 3,
    δ (67 + k) (4 * m + s) = 1 + s := by decide +kernel

/-! ## الإملاء: كرسيُّ الهمزة من جدول المدّ -/

/-- قوّةُ الحركة (وسيطٌ معلَن): كسرة ‎3‎ > ضمّة ‎2‎ > فتحة ‎1‎ > سكون ‎0‎. -/
def strength (h : Nat) : Nat := if h = 2 then 3 else if h = 1 then 2 else if h = 0 then 1 else 0

/-- الكرسيّ وسطًا: مدُّ أقوى الحركتين، أو ‎ء‎ (رقمُها ‎0‎) إن سكنتا. -/
def seatMedial (hp ho : Nat) : Nat :=
  if strength ho = 0 ∧ strength hp = 0 then 0
  else if strength ho ≥ strength hp then maddOf ho else maddOf hp

/-- **الكرسيُّ أحدُ حروف المدّ الثلاثة أو لا كرسيّ، ولا خامس.** -/
theorem seat_range : ∀ hp < 4, ∀ ho < 4, seatMedial hp ho ∈ [0, 2, 28, 11] := by decide +kernel

end Law
end SLGE
