import A116.Boundary
import A116.Ilal

/-!
# الهمزة — SLGE لوظائفها وأدوارها وكراسيّها

الهمزةُ في الـ116 **حاملٌ كسائر الحوامل** (الموضع 28) بحالاته الأربع؛ فلا شيءَ في الخانات يميّزها.
ما يميّزها ثلاثةٌ خارج الخانة، وكلٌّ منها هنا مبرهَنٌ أو معلَنٌ باسمه:

## ١. الكرسيّ (أ إ ؤ ئ ء) — رسمٌ مشتقٌّ لا بتٌّ

الكرسيُّ دالّةٌ في **سياق الخانة**: موضعُها (ابتداء/وسط/آخر)، حركتُها، حركةُ ما قبلها، أمدٌّ ما قبلها،
أياءٌ هو، أواوٌ ما بعدها. فإذا عُلم السياقُ عُلم الكرسيّ (`seatOf` دالّةٌ تامّة)، وإذا لم يُعلم لم
يُسترجَع (`Recovery.no_seat_recovery_from_hamza_alone`). فالكرسيُّ **صفرُ بتٍّ** حيث تنطبق القاعدة،
و**بقيّةٌ مسمّاة** حيث تخالفها الطبعة (مِائَة، لُؤْلُؤ، نَبَإٍ، لَئِن…) — والمقيسُ في المصحف: 4,107 من
4,213 كرسيًّا بالقاعدة (97.5%)، والباقي بقيّة.

* `seat_initial_by_own`: في الابتداء الكرسيُّ بحركة الهمزة وحدَها (إ للكسرة، أ لغيرها).
* `seat_final_by_prev`: في الآخر بعد غير مدٍّ الكرسيُّ بحركة ما قبلها وحدَها.
* `seat_after_madd_final_is_line`: في الآخر بعد مدٍّ الهمزةُ على السطر.
* `seat_medial_strongest`: في الوسط بعد غير مدٍّ الكرسيُّ بأقوى الحركتين (كسرة > ضمّة > فتحة > سكون)
  إلّا الضمّةَ قبل واوٍ فعلى السطر.

## ٢. القطعُ والوصل

همزةُ القطع خانةٌ تبقى في الوصل؛ وهمزةُ الوصل خانةٌ تسقط فيه (`Boundary.wasl_dropped_needs_moving_left`).
`qat_stays_when_joined`: وصلُ كلمةٍ مبدوءةٍ بهمزة قطعٍ متحرّكةٍ بما قبلها مرخَّصٌ دائمًا.

## ٣. الأدوار الزائدة

همزةُ الاستفهام (أَ)، وهمزةُ المتكلّم (أَفْعَلُ)، وهمزةُ التعدية (أَفْعَلَ): كلُّها **خانةٌ متحرّكةٌ
تُسبق**؛ و`prefix_hamza_admissible`: إسباقُ همزةٍ متحرّكةٍ لمرخَّصةٍ يُبقيها مرخَّصة. والهمزتان
المتواليتان (أَأْ) تصيران مدًّا (`Ilal.ibdal_restore` بحامل الألف) — آمَنَ.
-/

namespace A116.Hamza

open A116 A116.Junction A116.Boundary A116.Ladder A116.State

/-- الكرسيّ. -/
inductive Seat where
  | alif | alifBelow | waw | ya | line   -- أ إ ؤ ئ ء
  deriving DecidableEq, Repr

inductive Pos where
  | initial | medial | final
  deriving DecidableEq, Repr

/-- سياقُ الهمزة الذي يحدّد كرسيَّها. -/
structure Ctx where
  pos : Pos
  own : Haraka
  prev : Haraka
  prevLong : Bool   -- ما قبلها حرفُ مدّ
  prevYa : Bool     -- وحرفُ المدّ ياء
  nextWaw : Bool    -- ما بعدها واو
  deriving DecidableEq, Repr

/-- قوّةُ الحركة: كسرة > ضمّة > فتحة > سكون. -/
def strength : Haraka → Nat
  | .kasra => 3 | .damma => 2 | .fatha => 1 | .sukun => 0

def seatOfHaraka : Haraka → Seat
  | .kasra => .ya | .damma => .waw | .fatha => .alif | .sukun => .line

def stronger (a b : Haraka) : Haraka := if strength a ≥ strength b then a else b

/-- **قاعدةُ الكرسيّ** (دالّةٌ تامّة؛ مرآتُها `gate/hamza.py`). -/
def seatOf (c : Ctx) : Seat :=
  match c.pos with
  | .initial => if c.own = .kasra then .alifBelow else .alif
  | .final =>
    if c.prevLong then .line else seatOfHaraka c.prev
  | .medial =>
    if c.prevLong then
      if c.prevYa then .ya
      else if c.own = .kasra then .ya
      else if c.own = .damma && !c.nextWaw then .waw
      else .line
    else
      let best := stronger c.own c.prev
      if best = .damma && c.nextWaw then .line else seatOfHaraka best

theorem seat_initial_by_own (c c' : Ctx) (h : c.pos = .initial) (h' : c'.pos = .initial)
    (hown : c.own = c'.own) : seatOf c = seatOf c' := by
  simp [seatOf, h, h', hown]

theorem seat_final_by_prev (c c' : Ctx) (h : c.pos = .final) (h' : c'.pos = .final)
    (hl : c.prevLong = false) (hl' : c'.prevLong = false) (hprev : c.prev = c'.prev) :
    seatOf c = seatOf c' := by
  simp [seatOf, h, h', hl, hl', hprev]

theorem seat_after_madd_final_is_line (c : Ctx) (h : c.pos = .final) (hl : c.prevLong = true) :
    seatOf c = .line := by
  simp [seatOf, h, hl]

theorem seat_medial_strongest (c : Ctx) (h : c.pos = .medial) (hl : c.prevLong = false)
    (hw : c.nextWaw = false) : seatOf c = seatOfHaraka (stronger c.own c.prev) := by
  simp [seatOf, h, hl, hw]

/-- الكرسيُّ يتبع السياق لا الهمزة: سياقان لهمزةٍ واحدةٍ يختلفان كرسيًّا. -/
theorem seat_depends_on_context :
    seatOf ⟨.initial, .kasra, .sukun, false, false, false⟩ ≠
      seatOf ⟨.initial, .fatha, .sukun, false, false, false⟩ := by decide

/-! ## القطع والوصل -/

/-- همزةُ القطع المتحرّكةُ أوّلَ الكلمة تبقى في الوصل، والوصلُ بها مرخَّصٌ مهما كان آخرُ ما قبلها. -/
theorem qat_stays_when_joined (a : List Cell) (c : Cell) (h : Haraka) (hh : h.isSukun = false)
    (t : List Cell) (ha : Admissible (a ++ [c])) (ht : NoAdjacentSukun (⟨carrierOf 'ء', h⟩ :: t)) :
    Admissible ((a ++ [c]) ++ (⟨carrierOf 'ء', h⟩ :: t)) := by
  rw [join_iff a c _ ha]
  cases hc : c.isSukun
  · simpa using ht
  · simp only [↓reduceIte]
    refine ⟨?_, ht⟩
    simpa [HeadNotSukun, Cell.isSukun] using hh

/-! ## الأدوار الزائدة -/

inductive Role where
  | qat        -- همزةُ قطعٍ أصليّة (حرفٌ من الجذر)
  | wasl       -- همزةُ وصلٍ تسقط في الدرج
  | istifham   -- أَ الاستفهام
  | mutakallim -- أَفْعَلُ
  | tadiya     -- أَفْعَلَ
  deriving DecidableEq, Repr

/-- إسباقُ همزةٍ متحرّكةٍ (استفهام، متكلّم، تعدية) لمرخَّصةٍ يُبقيها مرخَّصة. -/
theorem prefix_hamza_admissible (h : Haraka) (hh : h.isSukun = false) (w : List Cell)
    (hw : Admissible w) : Admissible (⟨carrierOf 'ء', h⟩ :: w) := by
  rw [← run_ne_fellOut_iff] at hw ⊢
  have : step awaiting ⟨carrierOf 'ء', h⟩ = afterSeed := by simp [step, Cell.isSukun, hh]
  rw [run_cons, this]
  intro hfell
  apply hw
  -- من afterSeed إلى fellOut يلزم أن تكون w قد أسقطت الآلة من awaiting أيضًا
  rcases w with _ | ⟨c, t⟩
  · simp at hfell
  · cases hc : c.isSukun
    · have e1 : step afterSeed c = afterSeed := by simp [step, hc]
      have e2 : step awaiting c = afterSeed := by simp [step, hc]
      rw [run_cons, e1] at hfell; rw [run_cons, e2]; exact hfell
    · have e1 : step afterSeed c = awaiting := by simp [step, hc]
      have e2 : step awaiting c = fellOut := by simp [step, hc]
      rw [run_cons, e2]; simp

end A116.Hamza
