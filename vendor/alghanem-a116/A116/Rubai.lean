import A116.Tasrif
import A116.Zawaid

/-!
# أوزانُ الرباعيّ من الكتاب المختوم، وحركاتُها من المدوّنتين المختومتين

قرارُ المالك (2026-10-12): «أوزانُ الرباعيّ: ابحث عن مصدر سيبويه والمقاييس لابن فارس». والمصدر في الكتاب المختوم
(SLGE `tests/data/openiti-sibawayh-kitab.txt.gz`، «هذا باب تمثيل الفعل من بنات الأربعة مزيدًا أو غير مزيد»، السطر
19315–19328):

> «فإذا كان غيرَ مزيدٍ فإنّه لا يكون إلّا على مثال فعلل، ويكون يفعل منه على يفعلل… نحو دحرج يدحرج… وتدخل التاء على
> دحرج… نحو تدحرج… وتلحق النونُ ثالثةً ويسكن أوّلُ الحرف فيلزمه ألفُ الوصل… نحو احرنجم… وتلحق آخرَه الزيادةُ…
> فيلزم التضعيف ويسكن أوّلُ حرفٍ منه فيلزم ألفُ الوصل… نحو اقشعررت واطمأننت».

فالرباعيُّ فعلًا أربعةُ أبنية: فَعْلَلَ وحدَه مجرّدًا، وتَفَعْلَلَ وافْعَنْلَلَ وافْعَلَلَّ مزيدًا. والنصُّ غيرُ مشكول؛ فالحركاتُ
لا تُخمَّن: كلُّ وزنٍ هنا حركاتُه كلمةٌ مشكولةٌ من مدوّنةٍ مختومة تمرّ على البوّابة (`tests/test_rubai.py`):

| الوزن | الشاهد | المدوّنة |
|---|---|---|
| فَعْلَلَ | حَصْحَصَ، عَسْعَسَ، فَدَمْدَمَ، فَوَسْوَسَ | المصحف |
| فُعْلِلَ (للمجهول) | بُعْثِرَ، زُحْزِحَ، زُلْزِلَتِ | المصحف |
| يُفَعْلِلُ | يُوَسْوِسُ | المصحف |
| تَفَعْلَلَ | فَتَدَحْرَجَ، تَمَضْمَضَ، تَدَهْدَهَ | الصحيحان |
| افْعَلَلَّ | اطْمَأَنَّ، اشْمَأَزَّتْ | المصحف |
| تَفْعَلِلُّ | تَقْشَعِرُّ | المصحف |

و**افْعَنْلَلَ** (احرنجم) لا شاهدَ مشكولًا له في المدوّنتين: يُرفض بناؤه باسمه `IFANLALA_WITHOUT_SEALED_VOWELS` حتى
يُشكَل من مصدرٍ مختوم (`ifanlala_refused`) — لا حركةَ تخمينًا.

## ما يُبرهَن

* `rubai_licensed`: كلُّ وزنٍ من الستّة على **كلّ** جذرٍ رباعيٍّ بلا ألف مرخَّصٌ ابتداءً وصلًا ووقفًا وخاناتُه من المرخَّص —
  بالنقل من صفات الرباعيّ الـ625 (‎5⁴‎، `Tasrif.transfer_strict`).
* `rubai_witnesses`: الشواهدُ بخاناتها.
* `rubai_one_mujarrad`: المجرّدُ واحدٌ لا غير، وما سواه بزيادة: كلُّ وزنٍ غيرِ فَعْلَلَ فيه زائدٌ من «سألتمونيها» أو تضعيف.
-/

set_option autoImplicit false

namespace A116.Rubai

open A116 A116.Stages A116.Ternary A116.Ladder A116.Hadd A116.Boundary A116.Wazn A116.Tasrif

/-! ## ١. الأوزان -/

/-- الوزنُ وحالةُ أصله الأخير (3MS ماضيًا: فتحة؛ مضارعًا مرفوعًا: ضمّة). -/
structure Bina where
  name : String
  w : WaznC 4
  h : Haraka
  deriving DecidableEq, Repr

def faalala : Bina := ⟨"فعلل", ⟨false, [.slot 0 .fatha, .slot 1 .sukun, .slot 2 .fatha], 3⟩, .fatha⟩
def fuilila : Bina := ⟨"فعلل-مجهول", ⟨false, [.slot 0 .damma, .slot 1 .sukun, .slot 2 .kasra], 3⟩, .fatha⟩
def yufaalilu : Bina :=
  ⟨"يفعلل", ⟨false, [.lit (atom 'ي' .damma), .slot 0 .fatha, .slot 1 .sukun, .slot 2 .kasra], 3⟩, .damma⟩
def tafaalala : Bina :=
  ⟨"تفعلل", ⟨false, [.lit (atom 'ت' .fatha), .slot 0 .fatha, .slot 1 .sukun, .slot 2 .fatha], 3⟩, .fatha⟩
def ifalalla : Bina :=
  ⟨"افعللّ", ⟨true, [.slot 0 .sukun, .slot 1 .fatha, .slot 2 .fatha, .slot 3 .sukun], 3⟩, .fatha⟩
def tafalillu : Bina :=
  ⟨"تفعللّ", ⟨false, [.lit (atom 'ت' .fatha), .slot 0 .sukun, .slot 1 .fatha, .slot 2 .kasra, .slot 3 .sukun], 3⟩,
    .damma⟩

def abniya : List Bina := [faalala, fuilila, yufaalilu, tafaalala, ifalalla, tafalillu]

/-- افْعَنْلَلَ: مسمًّى في الكتاب (احرنجم، 19323) ولا حركاتَ له من مختوم — رفضٌ مسمًّى. -/
def ifanlala : Option Bina := none

theorem ifanlala_refused : ifanlala = none := rfl

/-! ## ٢. صفاتُ الرباعيّ والنقل -/

structure Sifa4 where
  c0 : Cls
  c1 : Cls
  c2 : Cls
  c3 : Cls
  deriving DecidableEq, Repr

def Sifa4.get (s : Sifa4) : Fin 4 → Cls
  | ⟨0, _⟩ => s.c0
  | ⟨1, _⟩ => s.c1
  | ⟨2, _⟩ => s.c2
  | _ => s.c3

def sifa4 (r : Root 4) : Sifa4 := ⟨cls (r 0), cls (r 1), cls (r 2), cls (r 3)⟩

def allSifa4 : List Sifa4 :=
  allCls.flatMap fun a => allCls.flatMap fun b => allCls.flatMap fun c => allCls.map fun d => ⟨a, b, c, d⟩

theorem mem_allSifa4 (s : Sifa4) : s ∈ allSifa4 := by
  obtain ⟨a, b, c, d⟩ := s
  simp only [allSifa4, List.mem_flatMap, List.mem_map]
  exact ⟨a, mem_allCls a, b, mem_allCls b, c, mem_allCls c, d, mem_allCls d, rfl⟩

theorem allSifa4_length : allSifa4.length = 625 := by decide +kernel

def rep4 (s : Sifa4) : Root 4 := fun i => ((s.get i).carrier?).getD (carrierOf 'ك')

theorem sifa4_get (r : Root 4) (i : Fin 4) : (sifa4 r).get i = cls (r i) := by
  match i with
  | ⟨0, _⟩ => rfl
  | ⟨1, _⟩ => rfl
  | ⟨2, _⟩ => rfl
  | ⟨3, _⟩ => rfl

theorem rep4_agree (r : Root 4) : Agree r (rep4 (sifa4 r)) := by
  intro i
  simp only [rep4, sifa4_get]
  exact cls_rep (r i)

theorem rep4_noAlif (s : Sifa4) : NoAlif (rep4 s) := by
  intro i
  simp only [rep4]
  cases s.get i <;> decide

def okB (B : Bina) (r : Root 4) : Bool :=
  let tc := waznT B.w (waslH B.w r) .start .continue B.h
  let tp := waznT B.w (waslH B.w r) .start .pause B.h
  contCheck (fillC tc r) && noVC (kindOf (fillC tc r)) &&
  pauseCheck (fillC tp r) && noVCP (kindOf (fillC tp r)) && litsOK tc && litsOK tp

theorem rubai_check : allSifa4.all (fun s => abniya.all fun B => okB B (rep4 s)) = true := by
  decide +kernel

/-- **كلُّ وزنٍ رباعيٍّ على كلّ جذرٍ رباعيٍّ بلا ألف** مرخَّصٌ ابتداءً وصلًا ووقفًا، وخاناتُه من المرخَّص. -/
theorem rubai_licensed (r : Root 4) (hr : NoAlif r) : ∀ B ∈ abniya,
    strictB (realize B.w r .start .continue B.h) = true ∧
    strictPauseB (realize B.w r .start .pause B.h) = true ∧
    (realize B.w r .start .continue B.h).all (Alif.licensable.contains ·) = true := by
  intro B hB
  have h := List.all_eq_true.1 (List.all_eq_true.1 rubai_check _ (mem_allSifa4 (sifa4 r))) B hB
  simp only [okB, Bool.and_eq_true] at h
  obtain ⟨⟨⟨⟨⟨hc, hv⟩, hpc⟩, hpv⟩, hl⟩, _⟩ := h
  have ha := rep4_agree r
  have hw : waslH B.w r = waslH B.w (rep4 (sifa4 r)) := waslH_eq B.w (lamEq_of_agree ha)
  simp only [realize_eq_fill]
  rw [hw]
  exact ⟨transfer_strict _ hr (rep4_noAlif _) ha hc hv, transfer_pause _ hr (rep4_noAlif _) ha hpc hpv,
    lits_licensable _ hr hl⟩

/-! ## ٣. المجرّدُ واحد -/

/-- رموزُ الوزن الزائدة: حروفٌ ليست أصلًا، أو أصلٌ مكرَّر (التضعيف). -/
def augmented (B : Bina) : Bool :=
  B.w.wasl || B.w.body.any (fun s => match s with | .lit _ => true | _ => false) ||
    (B.w.body.filter fun s => match s with | .slot j _ => j == B.w.last | _ => false).length > 0

/-- **المجرّدُ واحد**: فَعْلَلَ وحدَه بلا زيادة (ومجهولُه)، وما سواه بزائدٍ من «سألتمونيها» أو بتضعيف أو بهمزة وصل
(«لا يكون إلّا على مثال فعلل»). -/
theorem rubai_one_mujarrad :
    abniya.filter (fun B => !augmented B) = [faalala, fuilila] ∧
    (abniya.flatMap fun B => B.w.body.filterMap fun s => match s with
      | .lit c => some c.carrier | _ => none).all (fun k => Zawaid.zawaid.contains (Field112.carrierChar k)) =
      true := by
  decide +kernel

/-! ## ٤. الشواهد -/

def r4 (a b c d : Char) : Root 4
  | ⟨0, _⟩ => carrierOf a
  | ⟨1, _⟩ => carrierOf b
  | ⟨2, _⟩ => carrierOf c
  | _ => carrierOf d

def at4 (B : Bina) (a b c d : Char) : List Cell := realize B.w (r4 a b c d) .start .continue B.h

theorem rubai_witnesses :
    at4 faalala 'ح' 'ص' 'ح' 'ص' = [atom 'ح' .fatha, atom 'ص' .sukun, atom 'ح' .fatha, atom 'ص' .fatha] ∧
    at4 fuilila 'ب' 'ع' 'ث' 'ر' = [atom 'ب' .damma, atom 'ع' .sukun, atom 'ث' .kasra, atom 'ر' .fatha] ∧
    at4 yufaalilu 'و' 'س' 'و' 'س' =
      [atom 'ي' .damma, atom 'و' .fatha, atom 'س' .sukun, atom 'و' .kasra, atom 'س' .damma] ∧
    at4 tafaalala 'د' 'ح' 'ر' 'ج' =
      [atom 'ت' .fatha, atom 'د' .fatha, atom 'ح' .sukun, atom 'ر' .fatha, atom 'ج' .fatha] ∧
    at4 ifalalla 'ط' 'م' 'ء' 'ن' =
      [atom 'ء' .kasra, atom 'ط' .sukun, atom 'م' .fatha, atom 'ء' .fatha, atom 'ن' .sukun, atom 'ن' .fatha] ∧
    at4 tafalillu 'ق' 'ش' 'ع' 'ر' =
      [atom 'ت' .fatha, atom 'ق' .sukun, atom 'ش' .fatha, atom 'ع' .kasra, atom 'ر' .sukun, atom 'ر' .damma] := by
  decide +kernel

/-! ## ٥. فتحُ الرباعيّ: الدلالةُ بشاهد المقاييس المختوم

قرارُ المالك: «الدلالة… لا تُفتح إلّا بشاهدٍ مختوم». والشاهدُ المختوم مودَعٌ قبل هذا: جدولُ جذور «مقاييس اللغة»
`maqayis_by_root_csv_999.csv` (بصمتُه في `gate/maqayis_root_table.py`، ADR ١)، ونصُّ المعجم كاملًا في SLGE (OpenITI
JK008008، بتوقيع المالك 2026-10-08). فسندُ الدلالة للثلاثيّ **شاهدٌ** (`Exhaust.Sanad.shahid`): جذورُ المقاييس الثلاثيّةُ
التي أصولُها من الثمانية والعشرين، وعددُها `maqayisCount` يُعاد عدُّه من المودَع نفسه في `tests/test_rubai.py`. وما سواها
من جدول الدرجة (‎28³‎) «لا شاهد» لا «ممتنع» (المادّة ١٦: الغيابُ ليس امتناعًا)؛ والجذورُ المكتوبةُ بالألف في المقاييس
(حجا…) خارجَ الجدول بقيّةٌ مسمّاة `MAQAYIS_ALIF_ROOTS_OUTSIDE_TABLE`. -/

/-- عددُ جذور المقاييس الثلاثيّة في جدول الدرجة — يطابقه الاختبارُ من المودَع. -/
def maqayisCount : Nat := 4506

def maqayisShahid : Exhaust.Sanad := .shahid "maqayis_by_root_csv_999.csv" maqayisCount

/-- الدفترُ بعد الشاهد: دلالةُ الثلاثيّ بشاهد المقاييس، وما سواها كما كان. -/
def openedLedger : Nat → Exhaust.Wazifa → Exhaust.Sanad
  | 3, .dalala => maqayisShahid
  | n, w => RootGrade.rootLedger n w

/-- **الرباعيُّ مرخَّصٌ بعد الثلاثيّ**: جدولُ الثلاثيّ مستنفَد، ووظائفُه السبع مستوفاةٌ — ستٌّ ببرهانٍ والدلالةُ بالشاهد
المختوم — فتنفتح البوّابةُ للرباعيّ، ولا تنفتح لغيره (`RootGrade.only_tri_and_quad`). -/
theorem quad_open_by_maqayis : RootGrade.RootMurakhkhas openedLedger 4 :=
  RootGrade.quad_of_exhausted openedLedger (by intro w; cases w <;> rfl)

/-- وبلا الشاهد لا تنفتح (`RootGrade.rootLedger_quad_waits`): فالمانعُ كان الدلالةَ وحدَها، ورفعَه الشاهدُ وحدَه. -/
theorem opened_only_dalala_changed : ∀ w, w ≠ .dalala → openedLedger 3 w = RootGrade.rootLedger 3 w := by
  intro w hw; cases w <;> first | rfl | exact absurd rfl hw

end A116.Rubai
