import A116.Exhaust
import A116.SijillData

/-!
# سجلُّ التراخيص محسوبًا (ADR ٢٩)

«الشجرة المرخَّصة — سجلّ التراخيص» (مودَعُ المالك `docs/sijill/ledger.json`) يكتب الحالةَ «مرخَّص» بيده ويعلن:
«الدرجةُ k+1 لا تُرخَّص إلّا إذا كان جدولُ الدرجة k تامًّا». وهنا تُحسب الحالة ولا تُكتب:

* لكلّ مدخلٍ دليلٌ بمحتواه (`SijillData.Row.audited`: عددُ مبرهناتٍ مدقَّقة، و0 معلَّق)، ووظيفةٌ اختياريّة.
* الدفترُ مصفوفة: الصفُّ درجةُ السجلّ d بفهرس `Exhaust` ‎d+1‎، والعمودُ وظيفةٌ من السبع؛ والخانةُ قائمةٌ إن
  وُجد فيها مدخلٌ دليلُه قائم.
* «مرخَّص» هو `Exhaust.Murakhkhas`، فتعمل `exhaustion_gate` و`no_skip` و`gate_of_exhausted` بلا عملٍ جديد.

والمبرهناتُ العامّة لكلّ قائمة صفوف (أيّ إسنادٍ للوظائف وأيّ أدلّة)؛ ومبرهناتُ القسم الأخير على المودَع.
-/

set_option autoImplicit false

namespace A116.Sijill

open A116.Exhaust
open A116.SijillData

def _root_.A116.SijillData.Row.qaim (e : Row) : Bool := decide (0 < e.audited)

/-- دليلُ ملفٍّ خارج هذه النواة لا يحمل حدَّه هنا: يدخل شاهدًا مودَعًا بعدد مدقَّقاته، والمعلَّقُ معلَّق. -/
def toSanad (e : Row) : Sanad :=
  if e.audited = 0 then .muallaq "لا دليل" else .shahid "مدقَّق" e.audited

def matchRow (d : Nat) (w : Wazifa) (e : Row) : Bool :=
  e.daraja == d && e.wazifa == some w && e.qaim

def cell (es : List Row) (d : Nat) (w : Wazifa) : Sanad :=
  match es.find? (matchRow d w) with
  | some e => toSanad e
  | none => .muallaq "لا شاهد"

/-- الدفترُ بفهرس `Exhaust`: الصفُّ ‎d+1‎ درجةُ السجلّ d. -/
def L (es : List Row) : Nat → Wazifa → Sanad
  | 0 => fun _ => .muallaq "لا صفّ"
  | d + 1 => cell es d

theorem toSanad_qaim (e : Row) (h : e.qaim = true) : (toSanad e).qaim = true := by
  unfold toSanad
  have : e.audited ≠ 0 := by simp [Row.qaim] at h; omega
  simp [this, Sanad.qaim]

/-- **الخانةُ قائمةٌ ⟺ فيها مدخلٌ دليلُه قائم.** -/
theorem cell_qaim_iff (es : List Row) (d : Nat) (w : Wazifa) :
    (cell es d w).qaim = true ↔ ∃ e ∈ es, e.daraja = d ∧ e.wazifa = some w ∧ e.qaim = true := by
  unfold cell
  cases hf : es.find? (matchRow d w) with
  | some e =>
    have hp := List.find?_some hf
    have hm := List.mem_of_find?_eq_some hf
    simp only [matchRow, Bool.and_eq_true, beq_iff_eq] at hp
    exact ⟨fun _ => ⟨e, hm, hp.1.1, hp.1.2, hp.2⟩, fun _ => toSanad_qaim e hp.2⟩
  | none =>
    simp only [Sanad.qaim, Bool.false_eq_true, false_iff]
    rintro ⟨e, hm, h1, h2, h3⟩
    have := List.find?_eq_none.mp hf e hm
    simp [matchRow, h1, h2, h3] at this

/-- **القانونُ محسوبًا**: ترخيصُ الدرجة ‎k‎ (بفهرس Exhaust) يستلزم لكلّ درجة سجلٍّ دونها ولكلّ وظيفةٍ مدخلًا دليلُه قائم. -/
theorem ledger_gate (es : List Row) (k : Nat) (h : Murakhkhas (L es) (k + 1)) :
    ∀ j, j < k → ∀ w, ∃ e ∈ es, e.daraja = j ∧ e.wazifa = some w ∧ e.qaim = true := by
  intro j hj w
  exact (cell_qaim_iff es j w).mp (exhaustion_gate (L es) k h (j + 1) (by omega) (by omega) w)

/-- والعكس: الاستيفاءُ كافٍ. -/
theorem gate_of_witnesses (es : List Row) (k : Nat)
    (h : ∀ j, j < k → ∀ w, ∃ e ∈ es, e.daraja = j ∧ e.wazifa = some w ∧ e.qaim = true) :
    Murakhkhas (L es) (k + 1) :=
  gate_of_exhausted (L es) k fun j h1 h2 => by
    obtain ⟨i, rfl⟩ : ∃ i, j = i + 1 := ⟨j - 1, by omega⟩
    exact fun w => (cell_qaim_iff es i w).mpr (h i (by omega) w)

/-- **درجةٌ لا دليلَ قائمًا فيها توقف ما بعدها**، أيًّا كان عددُ ملفّاتها وإسنادُها. -/
theorem stops_at (es : List Row) (d : Nat) (h : ∀ e ∈ es, e.daraja = d → e.qaim = false) :
    ¬ Murakhkhas (L es) (d + 2) := by
  intro hm
  obtain ⟨e, he, h1, -, hq⟩ := ledger_gate es (d + 1) hm d (by omega) .tarmiz
  simp [h e he h1] at hq

theorem wazifa_nodup : Wazifa.all.Nodup := by decide

theorem count_eq_filter (es : List Row) (d : Nat) :
    (es.map Row.daraja).count d = (es.filter fun e => e.daraja == d).length := by
  induction es with
  | nil => rfl
  | cons a t ih =>
    simp only [List.map_cons, List.count_cons, List.filter_cons]
    split <;> simp_all

/-- **الحمام**: صفٌّ مستوفًى يحتاج سبعةَ مدخلاتٍ في درجته على الأقلّ — وظيفةٌ لكلّ واحد. -/
theorem mustawfa_needs_seven (es : List Row) (d : Nat) (h : Mustawfa (L es (d + 1))) :
    Wazifa.all.length ≤ (es.map Row.daraja).count d := by
  rw [count_eq_filter]
  have hsub : Wazifa.all ⊆ ((es.filter fun e => e.daraja == d).map Row.wazifa).filterMap id := by
    intro w _
    obtain ⟨e, he, h1, h2, -⟩ := (cell_qaim_iff es d w).mp (h w)
    exact List.mem_filterMap.mpr ⟨some w, List.mem_map.mpr ⟨e, List.mem_filter.mpr ⟨he, by simp [h1]⟩, h2⟩, rfl⟩
  have h1 := wazifa_nodup.length_le_of_subset hsub
  have h2 := List.length_filterMap_le id ((es.filter fun e => e.daraja == d).map Row.wazifa)
  simp only [List.length_map] at h2
  omega

/-- القانونُ مكتوبًا باليد: الحالةُ معاملٌ يكتبه الكاتب. -/
def DeclComplete (es : List Row) (status : Nat → Bool) (k : Nat) : Prop :=
  ∀ i, (h : i < es.length) → es[i].daraja ≤ k → status i = true

/-- **فراغُه**: الحالةُ «مرخَّصٌ للكلّ» تجعل كلَّ درجةٍ تامّةً في كلّ سجلّ — فلا يقيّد شيئًا. -/
theorem declared_law_vacuous (es : List Row) (k : Nat) : DeclComplete es (fun _ => true) k :=
  fun _ _ _ => rfl

/-- رتابةُ الدليل على حوافّ الترخيص: كلُّ مدخلٍ دليلُه قائمٌ مرخِّصُه دليلُه قائم. -/
def rankMono (es : List Row) : Bool :=
  es.all fun e => match e.licensedBy with
    | some p => !e.qaim || ((es[p]?).map Row.qaim == some true)
    | none => true

/-! ## على المودَع (`SijillData.rows`، مولَّدٌ ببصمة السجلّ) -/

/-- أعدادُ الدرجات 0..6 في السجلّ (مبرهنٌ على الشاهد). -/
theorem degree_counts :
    (List.range 7).map (fun d => (rows.map Row.daraja).count d) = [29, 383, 88, 36, 4, 404, 150] := by
  decide +kernel

theorem rows_length : rows.length = 1094 := by decide +kernel

theorem mana_count : (rows.map Row.daraja).count 4 = 4 := by decide +kernel

/-- المدخلاتُ ذاتُ الدليل القائم سبعةٌ، كلُّها في الزوائد (الدرجة 6). -/
theorem qaim_count : (rows.filter Row.qaim).length = 7 := by decide +kernel

theorem qaim_only_in_zur : ∀ e ∈ rows, e.qaim = true → e.daraja ∈ [6] := by decide +kernel

/-- **السجلُّ على دليله الحاضر يقف عند الدرجة 0**: لا مدخلَ فيها دليلُه قائم، فلا تُرخَّص الدرجة 1. -/
theorem sijill_stops_at_zero : ¬ Murakhkhas (L rows) 2 :=
  stops_at rows 0 fun e he h0 => by
    cases hq : e.qaim
    · rfl
    · have := qaim_only_in_zur e he hq; simp at this; omega

/-- **ولأيّ أدلّةٍ وأيّ إسنادٍ على درجات هذا السجلّ: لا تُستوفى الدرجة 4 (المعنى)** — أربعةُ ملفّاتٍ لسبع وظائف. -/
theorem mana_never_mustawfa (es : List Row) (h : es.map Row.daraja = rows.map Row.daraja) :
    ¬ Mustawfa (L es 5) := by
  intro hm
  have := mustawfa_needs_seven es 4 hm
  rw [h, mana_count] at this
  simp [Wazifa.all] at this

/-- **فلا يُرخَّص المختبرُ (5) ولا الزوائدُ (6) بقانون السجلّ نفسِه**، ولو استوفت كلُّ ملفّاته أدلّتَها. -/
theorem mukhtabar_never_licensed (es : List Row) (h : es.map Row.daraja = rows.map Row.daraja) :
    ¬ Murakhkhas (L es) 6 ∧ ¬ Murakhkhas (L es) 7 :=
  ⟨no_skip (L es) 5 5 (by omega) (by omega) (mana_never_mustawfa es h),
   no_skip (L es) 6 5 (by omega) (by omega) (mana_never_mustawfa es h)⟩

/-- **الرتبةُ مقلوبةٌ في السجلّ**: وحداتُ Lean المدقَّقة يرخّصها مدخلٌ لا دليلَ قائمًا له (شاهدُه `f1021` ← `f0978`). -/
theorem sijill_not_rank_mono : rankMono rows = false := by decide +kernel

end A116.Sijill
