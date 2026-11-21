import A116.Rubai
import A116.Sijill

/-!
# قفلُ الدالّ وحده (ADR ٦٢، أمرُ المالك «اقفل الدالّ»، 2026-10-14)

الدفترُ `Ledger.filled` (ADR ١٩) يملأ الوظائفَ الستّ على **القوالب الثلاثيّة الصحيحة** وحدَها. والقفلُ بقرار المالك
(ADR ٦٠) **يمتدّ إلى المعتلّ والرباعيّ**. فهذا الدفتر `locked` يجمع ما بُرهن في وحداتٍ متفرّقة في صفٍّ واحدٍ لكلّ
درجة، كلُّ سندٍ برهانًا يحمل حدَّه:

* **الاشتقاقُ** (`IshtiqaqLocked`): على القوالب الصحيحة (`Ledger.ishtiqaqAt`)؛ **وعلى كلّ جذرٍ ثلاثيٍّ بلا ألف —
  صحيحِه ومعتلِّه ومهموزِه ومضعَّفِه — الماضي المجرّدُ بأبوابه الثلاثة، والمضارعُ بحروف المضارعة والإعراب، والأمرُ**
  (`Tasrif.madi_exhausted`، `mudari_exhausted`، `amr_exhausted`: مرخَّصٌ ابتداءً وصلًا ووقفًا وخاناتُه من المرخَّص)؛
  **وعلى كلّ جذرٍ رباعيٍّ بلا ألف** أبنيتُه الستّ (`Rubai.rubai_licensed`)؛ **والمعتلُّ بالمحايد** على الجذور المرجعيّة
  بالأوزان الإحدى والثلاثين (`Neutral.weak_licensed`).
* **الصرفُ** (`SarfLocked`): حالةُ الآخر بقالبه على القوالب الصحيحة (`Ledger.sarfAt`)، وما يُلزمه القانون في المعتلّ:
  حذفُ المدّ في مجزوم الأجوف وهاءُ السكت (`Tasrif.madd_drop_forced`، `haa_forced`).
* **النحوُ** (`Ledger.mahallAt`)، و**الترميزُ والإملاءُ والصوتُ** كما في `Exhaust.current`.
* **الدلالةُ** ليست من الدالّ وحده: سندُها **منفذُ الجسر** إلى المرحلة الثالثة (`DALALA_AT_DAL_MADLUL_BRIDGE`)،
  لا دَينٌ على الغانم. فالدفترُ يقف عند الدرجة الأولى بقانونه نفسِه (`locked_stops_at_one`)، والدلالةُ وحدَها
  المانع (`dalala_alone_opens`).

## ما يقوله القفل

* `locked_six_qaim`: الوظائفُ الستّ قائمةٌ في كلّ درجة، و`locked_qaim_count`: ستٌّ من سبع.
* `locked_beyond_sahih`: ما كان مقصورًا على الصحيح (`Tasrif.every_position` يشترط `Sahih`) صار على كلّ جذرٍ بلا ألف
  في الماضي والمضارع والأمر — شاهدُه «قَالَ» من قول و«وَعَدَ» من وعد و«رَمَى» من رمي و«مَدَّ» من مدد.
* `locked_quad`: الرباعيُّ داخل القفل، والبوّابةُ بعدد الأصول مفتوحةٌ له بشاهد المقاييس (`Rubai.quad_open_by_maqayis`).
* `dal_locked`: الجامع — كلُّ ما سبق في عبارةٍ واحدة.

## ما ليس في القفل، باسمه

* `SIJILL_OUTSIDE_LOCK`: سجلُّ تراخيص ملفّات الشجرة القديمة (`A116.Sijill`) يقف عند الدرجة 0 بدليله الحاضر
  (`sijill_stops_at_zero`)؛ وهو سجلُّ ملفّاتٍ لا قانونُ الدالّ، فيُعلَن خارج حدّ القفل حتى يقرّر المالك.
* `ILHAQ_OUTSIDE_LOCK`: الإلحاقُ بالرباعيّ سماعيٌّ مفحوصٌ لا مقيس (`Hadd.ilhaqPair`)، خارج الدفتر.
* `IFANLALA_WITHOUT_SEALED_VOWELS`: افْعَنْلَلَ بلا شاهدٍ مشكول (`Rubai.ifanlala_refused`)، مرفوضٌ باسمه لا مقفول.
-/

namespace A116.Qufl

open A116 A116.Stages A116.Ternary A116.Ladder A116.Hadd A116.Boundary A116.Exhaust A116.Wazn A116.Tasrif

/-- **الاشتقاقُ مقفولًا**: الصحيحُ بالأوزان، وكلُّ جذرٍ بلا ألف بالماضي والمضارع والأمر، والرباعيُّ بأبنيته،
والمعتلُّ بالمحايد على الجذور المرجعيّة. -/
def IshtiqaqLocked (d : Nat) : Prop :=
  Ledger.IshtiqaqAt d ∧
  (∀ r : Root 3, NoAlif r → ∀ a ∈ harakat3,
    strictB (fillC (madi (sifa r) a .fatha) r) = true ∧
    strictPauseB (Pause.pause (fillC (madi (sifa r) a .fatha) r)) = true ∧
    (fillC (madi (sifa r) a .fatha) r).all (Alif.licensable.contains ·) = true) ∧
  (∀ r : Root 3, NoAlif r → ∀ b ∈ babs, ∀ v ∈ harakat3, ∀ p ∈ prefixes, ∀ m ∈ moods,
    strictB (fillC (mudari (sifa r) b p v m) r) = true ∧
    strictPauseB (Pause.pause (fillC (mudari (sifa r) b p v m) r)) = true ∧
    (fillC (mudari (sifa r) b p v m) r).all (Alif.licensable.contains ·) = true) ∧
  (∀ r : Root 3, NoAlif r → ∀ b ∈ babs, ∀ v ∈ harakat3,
    strictB (fillC (amr (sifa r) b v) r) = true ∧
    strictPauseB (fillC (amrPause (sifa r) b v) r) = true ∧
    (fillC (amr (sifa r) b v) r).all (Alif.licensable.contains ·) = true) ∧
  (∀ r : Root 4, NoAlif r → ∀ B ∈ Rubai.abniya,
    strictB (realize B.w r .start .continue B.h) = true ∧
    strictPauseB (realize B.w r .start .pause B.h) = true ∧
    (realize B.w r .start .continue B.h).all (Alif.licensable.contains ·) = true) ∧
  (∀ r ∈ Neutral.refRoots, ∀ p ∈ (List.range thulathi.length).zip thulathi,
    strictB (Neutral.realizeN p.2 r .start .continue (lastH p.1)) = true)

theorem ishtiqaqLocked (d : Nat) : IshtiqaqLocked d :=
  ⟨Ledger.ishtiqaqAt d, fun r hr => madi_exhausted r hr, fun r hr => mudari_exhausted r hr,
    fun r hr => amr_exhausted r hr, fun r hr => Rubai.rubai_licensed r hr, Neutral.weak_licensed⟩

/-- **الصرفُ مقفولًا**: آخرُ الصيغة بقالبه على الصحيح، وما يُلزمه القانونُ في المعتلّ: حذفُ المدّ وهاءُ السكت. -/
def SarfLocked (d : Nat) : Prop :=
  Ledger.SarfAt d ∧
  (∀ r : Root 3, NoAlif r → sifa r ∈ ajwafSifas → ∀ b ∈ babs, ∀ v ∈ harakat3, ∀ p ∈ prefixes,
    strictB (fillC (jussivePre (sifa r) b p v) r) = false) ∧
  (∀ c ∈ Alif.licensable, c.haraka ≠ .sukun →
    strictPauseB (Pause.pause [c]) = false ∧ strictPauseB [c, atom 'ه' .sukun] = true)

theorem sarfLocked (d : Nat) : SarfLocked d :=
  ⟨Ledger.sarfAt d, fun r hr hs => madd_drop_forced r hr hs, haa_forced⟩

/-- الدفترُ المقفول: ستٌّ ببرهانٍ يحمل حدَّه، والدلالةُ منفذُ جسرٍ إلى «الدالّ والمدلول معًا». -/
def locked (d : Nat) : Wazifa → Sanad
  | .tarmiz => .burhan (tarmizAt d)
  | .imla => .burhan (imlaAt d)
  | .sawt => .burhan (sawtAt d)
  | .ishtiqaq => .burhan (ishtiqaqLocked d)
  | .sarf => .burhan (sarfLocked d)
  | .nahw => .burhan (Ledger.mahallAt d)
  | .dalala => .muallaq "DALALA_AT_DAL_MADLUL_BRIDGE"

/-- **الستُّ قائمة** في كلّ درجة. -/
theorem locked_six_qaim (d : Nat) : ∀ w, w ≠ .dalala → (locked d w).qaim = true := by
  intro w hw; cases w <;> first | rfl | exact absurd rfl hw

theorem locked_qaim_count (d : Nat) :
    (Wazifa.all.filter fun w => (locked d w).qaim).length = 6 := by
  simp [Wazifa.all, locked, Sanad.qaim]

/-- الدفترُ المقفول يوافق `Ledger.filled` في كلّ ما ليس ترميزًا ولا اشتقاقًا ولا صرفًا: لا شيءَ نُقص. -/
theorem locked_extends_filled (d : Nat) :
    ∀ w, w ≠ .ishtiqaq → w ≠ .sarf → w ≠ .dalala → (locked d w).qaim = (Ledger.filled d w).qaim := by
  intro w _ _ _; cases w <;> rfl

/-- **بقانون الاستنفاد**: الدفترُ المقفول يقف عند الدرجة الأولى — الدلالةُ ليست هنا. -/
theorem locked_stops_at_one : ∀ k, ¬ Murakhkhas locked (k + 2) :=
  fun k => no_skip locked (k + 1) 1 (Nat.le_refl _) (by omega)
    (fun h => by have := h .dalala; simp [locked, Sanad.qaim] at this)

/-- **الدلالةُ وحدَها تفتح**: أيُّ سندٍ قائمٍ لها عبر الجسر يفتح الدرجاتِ كلَّها. -/
theorem dalala_alone_opens (s : Nat → Sanad) (hs : ∀ d, (s d).qaim = true) :
    ∀ k, Murakhkhas (fun d w => if w = .dalala then s d else locked d w) (k + 1) :=
  fun k => gate_of_exhausted _ k fun j _ _ w => by
    by_cases hw : w = .dalala
    · simp [hw, hs]
    · simp only [hw, ite_false]; exact locked_six_qaim j w hw

/-! ## ما يتجاوزه القفل عن الصحيح، بشواهدَ بأعيانها -/

/-- جذورٌ من كلّ صفة: صحيح، مثال (واويّ الفاء)، أجوف، ناقص، مهموز، مضعّف. -/
def shawahid : List (Root 3) :=
  [r3 'ك' 'ت' 'ب', r3 'و' 'ع' 'د', r3 'ق' 'و' 'ل', r3 'ر' 'م' 'ي', r3 'ء' 'خ' 'ذ', r3 'م' 'د' 'د']

theorem shawahid_noAlif : ∀ r ∈ shawahid, NoAlif r := by
  intro r hr
  simp only [shawahid, List.mem_cons, List.not_mem_nil, or_false] at hr
  rcases hr with rfl | rfl | rfl | rfl | rfl | rfl <;> (intro i; revert i; decide)

/-- خمسةٌ من الستّة ليست صحيحة، فلا يبلغها `Tasrif.every_position`؛ والقفلُ يبلغها. -/
theorem shawahid_not_all_sahih : ¬ ∀ r ∈ shawahid, Sahih r := by
  intro h
  have := h (r3 'ق' 'و' 'ل') (by simp [shawahid])
  exact absurd (this 1) (by decide)

/-- **القفلُ يتجاوز الصحيح**: على كلّ شاهدٍ، صحيحًا كان أو معتلًّا، الماضي فَعَلَ مرخَّصٌ وصلًا ووقفًا. -/
theorem locked_beyond_sahih : ∀ r ∈ shawahid,
    strictB (fillC (madi (sifa r) .fatha .fatha) r) = true ∧
    strictPauseB (Pause.pause (fillC (madi (sifa r) .fatha .fatha) r)) = true :=
  fun r hr =>
    let h := (ishtiqaqLocked 1).2.1 r (shawahid_noAlif r hr) .fatha (by simp [harakat3])
    ⟨h.1, h.2.1⟩

/-- **الرباعيُّ داخل القفل**: دَحْرَجَ على فَعْلَلَ مرخَّص، والبوّابةُ بعدد الأصول مفتوحةٌ له. -/
theorem locked_quad :
    strictB (realize Rubai.faalala.w (Rubai.r4 'د' 'ح' 'ر' 'ج') .start .continue Rubai.faalala.h) = true ∧
    RootGrade.RootMurakhkhas Rubai.openedLedger 4 :=
  ⟨((ishtiqaqLocked 1).2.2.2.2.1 _ (by intro i; revert i; decide) Rubai.faalala (by simp [Rubai.abniya])).1,
    Rubai.quad_open_by_maqayis⟩

/-- **قفلُ الدالّ وحده**، في عبارةٍ واحدة: الستُّ قائمةٌ في كلّ درجة، والاشتقاقُ والصرفُ ممتدّان إلى المعتلّ
والرباعيّ، والدلالةُ وحدَها وراء الجسر، والدفترُ يقف عندها بقانونه. -/
theorem dal_locked :
    (∀ d w, w ≠ .dalala → (locked d w).qaim = true) ∧
    (∀ d, IshtiqaqLocked d ∧ SarfLocked d) ∧
    (∀ d, locked d .dalala = .muallaq "DALALA_AT_DAL_MADLUL_BRIDGE") ∧
    (∀ k, ¬ Murakhkhas locked (k + 2)) :=
  ⟨locked_six_qaim, fun d => ⟨ishtiqaqLocked d, sarfLocked d⟩, fun _ => rfl, locked_stops_at_one⟩

/-- ما خارج القفل باسمه: سجلُّ الملفّات يقف عند الصفر بدليله، وهو غيرُ دفتر الدالّ. -/
theorem sijill_outside_lock : ¬ Murakhkhas (Sijill.L SijillData.rows) 2 ∧ Murakhkhas locked 1 :=
  ⟨Sijill.sijill_stops_at_zero, trivial⟩

end A116.Qufl
