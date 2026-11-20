import A116.Alif
import A116.Count
import A116.Wazn
import A116.Rubai

/-!
# توافيقُ الخانات: عددُ المرخَّص من كلّ سلاسل الشبكة بطولٍ معلوم (ADR ٦٣)

السؤال: «كم تركيبًا من خانات الـ116 يُرخَّص؟» — جوابُه هنا **على الخانات بأعيانها** لا على أصناف
المقاطع (ذلك في `Exhaust.table_length` و`ExhaustPause.pauseTable_length`) ولا على الأوزان
(`PauseCount.pause_count_fib`).

* `seqs n`: كلُّ سلاسل الشبكة المرخَّصة (`Alif.licensable`، 113) بطول n؛ عددُها ‎113^n‎ (`seqs_length`).
* `wasl n` و`waqf n`: ما يقبله `Hadd.strictB` و`Hadd.strictPauseB` منها.
* الطولُ الأوّل: **84** = 28 حاملًا × 3 حركات (`wasl_one`، `one_is_cv`) — الألفُ ليست حاملَ ابتداء
  والساكنُ لا يُبتدأ به؛ فالنموذجُ الثنائيّ (`Count.U 1 = 87`) يزيد بالألف المتحرّكة الثلاث بالضبط
  (`binary_adds_vowelled_alif`).
* الطولُ الثاني: **9,492** = 84 × 84 (CV.CV) + 84 × 29 (CV ثمّ مُغلِقٌ أو مدّ) (`wasl_two`،
  `two_structure`)؛ والوقفُ كذلك (`waqf_two`)؛ لا ‎29 × 4 × 29 = 3,364‎ الذي يعدّ الألفَ حاملَ ابتداء
  والسكونَ حركة.
* **ثغرةٌ مسمّاة** `ALIF_CLOSER_NOT_REFUSED`: الألفُ الساكنة بعد ضمّةٍ أو كسرة صنفُها `c` في `Hadd.kindOne`
  (لأنّ مدَّها الفتحةُ وحدَها) فتُرخَّص مُغلِقًا — كُاْ (`alif_closer_licensed`)، و56 سلسلةً من الطول الثاني
  (`alif_closers_two`)، وكَاْاْ وقفًا (`kaa_aa_pause`) — والألفُ «لا بد لها من حرف قبلها مفتوح» (الكتاب
  س17941) ولا تكون مُغلِقًا أبدًا. الثغرةُ تزيد ولا تنقص: لا كلمةَ من المدوّنة تُرفض بها؛ وسدُّها تغييرٌ
  في `kindOne` يمسّ جداولَ Lean المودَعة كلَّها، فهو ADR بعد قفل الدالّ لا تعديلٌ صامت.

الطولُ الثالث وما بعده يطبعه Lean المترجَم جدولًا (`lake exe a116-table tawafiq`) ويطابقه
`tests/test_tawafiq.py` بمرآة البوّابة؛ وعددُه لكلّ طولٍ **مبرهَنٌ في `A116.TawafiqMasfufa`** (ADR ١١٦، سدّ
`TAWAFIQ_CLOSED_FORM_NOT_PROVEN`): ‎wasl n = uᵀMⁿa‎ بمصفوفة انتقال آلة الحرف لكلّ n، والتكرارُ
‎wasl(n+7) = 84·wasl(n+6) + 2436·wasl(n+5) + 84·wasl(n+4)‎ لكلّ n ووقفًا مثلُه من الطول الخامس.
-/

namespace A116.Tawafiq

open A116 A116.Ladder A116.Hadd

/-- كلُّ سلاسل الشبكة المرخَّصة بطول n. -/
def seqs : Nat → List (List Cell)
  | 0 => [[]]
  | n + 1 => Alif.licensable.flatMap fun c => (seqs n).map (c :: ·)

theorem length_flatMap_cons {α : Type} (l : List α) (m : List (List α)) :
    (l.flatMap fun c => m.map (c :: ·)).length = l.length * m.length := by
  induction l with
  | nil => simp
  | cons c l ih =>
    simp only [List.flatMap_cons, List.length_append, List.length_map, ih, List.length_cons]
    rw [Nat.succ_mul, Nat.add_comm]

theorem seqs_length : ∀ n, (seqs n).length = 113 ^ n
  | 0 => rfl
  | n + 1 => by
    rw [seqs, length_flatMap_cons, seqs_length n, Alif.licensable_length, Nat.pow_succ, Nat.mul_comm]

/-- المرخَّصُ وصلًا من الطول n. -/
def wasl (n : Nat) : Nat := ((seqs n).filter strictB).length

/-- المرخَّصُ وقفًا من الطول n. -/
def waqf (n : Nat) : Nat := ((seqs n).filter strictPauseB).length

/-- ما آخرُه ألفٌ ساكنة صنفُها `c` (مُغلِق) وهو مرخَّصٌ وصلًا. -/
def alifClosers (n : Nat) : Nat :=
  ((seqs n).filter fun w =>
    strictB w && w.getLast? == some (atom 'ا' .sukun) && (kindOf w).getLast? == some .c).length

set_option maxRecDepth 100000

theorem wasl_one : wasl 1 = 84 := by decide +kernel

theorem waqf_one : waqf 1 = 84 := by decide +kernel

/-- الطولُ الأوّل كلُّه CV: 28 حاملًا (بلا ألف) × 3 حركات. -/
theorem one_is_cv : wasl 1 = (carrierCount - 1) * 3 := by rw [wasl_one]; rfl

/-- النموذجُ الثنائيّ على الـ116 يزيد على الثلاثيّ بالألف المتحرّكة الثلاث بالضبط. -/
theorem binary_adds_vowelled_alif : U 1 = wasl 1 + Alif.alifVowelled.length := by
  rw [U_one, wasl_one]; rfl

theorem wasl_two : wasl 2 = 9492 := by decide +kernel

theorem waqf_two : waqf 2 = 9492 := by decide +kernel

/-- الطولُ الثاني: CV ثمّ CV، أو CV ثمّ ساكنٌ (مُغلِقٌ أو مدّ) من الـ29. -/
theorem two_structure : wasl 2 = 84 * 84 + 84 * 29 := by rw [wasl_two]

/-- ‎29 × 4 × 29‎ ليس عددَ المرخَّص من الطول الثاني ولا من أيّ طول: إنّه أكبرُ من الأوّل وأصغرُ من الثاني. -/
theorem not_3364 : wasl 1 < 29 * 4 * 29 ∧ 29 * 4 * 29 < wasl 2 := by
  rw [wasl_one, wasl_two]; decide

/-- `ALIF_CLOSER_NOT_REFUSED`: كُاْ مرخَّصٌ وصلًا والألفُ فيه مُغلِق. -/
theorem alif_closer_licensed :
    strictB [atom 'ك' .damma, atom 'ا' .sukun] = true ∧
    kindOf [atom 'ك' .damma, atom 'ا' .sukun] = [.cv, .c] := by decide +kernel

/-- بعد الفتحة الألفُ مدٌّ لا مُغلِق. -/
theorem alif_after_fatha_is_madd : kindOf [atom 'ك' .fatha, atom 'ا' .sukun] = [.cv, .v] := by decide +kernel

/-- 56 سلسلةً من الطول الثاني ألفُها مُغلِق: 28 حاملًا × (ضمّة، كسرة). -/
theorem alif_closers_two : alifClosers 2 = 56 := by decide +kernel

/-- كَاْاْ: مدٌّ ثمّ ألفٌ مُغلِقةٌ عارضةً وقفًا — تُرخَّص بالثغرة نفسِها. -/
theorem kaa_aa_pause :
    strictPauseB [atom 'ك' .fatha, atom 'ا' .sukun, atom 'ا' .sukun] = true ∧
    strictB [atom 'ك' .fatha, atom 'ا' .sukun, atom 'ا' .sukun] = false := by decide +kernel

/-! ## الفضاءُ المولَّد لا فضاءُ الترخيص (ADR ٦٩): أبنيةُ الاسم الثلاثيّ المجرّد — القانونُ ثمّ النقل

`TEN_OF_TWELVE_IS_NAQL`: على جذرٍ صحيحٍ شاهد (ك ت ب) تكون حركاتُ الأصول الثلاثة ‎4³ = 64‎ توفيقًا؛ قانونُ
الابتداء والوصل والوقف يبقي منها 45 وصلًا و48 وقفًا (`shapes64_wasl`، `shapes64_waqf`)؛ وأبنيةُ الاسم
(الأوّلُ متحرّكٌ من ثلاث، والثاني من أربع، والثالثُ علامةٌ: ضمّةٌ وصلًا وسكونٌ وقفًا) اثنا عشر **كلُّها مرخَّصة**
(`law_ism_twelve`، `law_ism_all`). والعشرةُ المستعملة **نقلٌ** من الكتاب المختوم (باب ما بنت العرب، س18621–18641):
فَعْل صقر، فِعْل عكم، فُعْل برد، فَعَل جبل، فَعِل كتف، فَعُل رجل، فُعَل صرد، فُعُل طنب، فِعَل ضلع، فِعِل إبل؛
والمتروكان بنصّه: «ليس في الأسماء والصفات فُعِل ولا يكون إلّا في الفعل، وليس في الكلام فِعُل» (س18641؛ وعلّتُه
س17924: «كرهوا الضمّة بعد الكسرة»). الكتابُ غيرُ مشكول، فحركةُ كلّ بناءٍ مأخوذةٌ من مثاله (`corpora/sibawayh/`).
فالعشرةُ ⊂ الاثني عشر (`naql_sub_law`) والفرقُ هما بأعيانهما (`law_minus_naql`) — ولا يُنسب الحصرُ في عشرةٍ
إلى القانون في أيّ موضع. -/

def h3 : List Haraka := [.fatha, .damma, .kasra]
def h4 : List Haraka := [.fatha, .damma, .kasra, .sukun]

/-- الأصولُ الثلاثة الشاهدة بحركاتٍ معلومة. -/
def shape (a b c : Haraka) : List Cell := [atom 'ك' a, atom 'ت' b, atom 'ب' c]

def shapes64 : List (List Cell) := h4.flatMap fun a => h4.flatMap fun b => h4.map fun c => shape a b c

theorem shapes64_length : shapes64.length = 64 := by decide +kernel

theorem shapes64_wasl : (shapes64.filter strictB).length = 45 := by decide +kernel

theorem shapes64_waqf : (shapes64.filter strictPauseB).length = 48 := by decide +kernel

/-- الاثنا عشر الممكنة لبناء الاسم. -/
def ismPairs : List (Haraka × Haraka) := h3.flatMap fun a => h4.map fun b => (a, b)

/-- ما يرخّصه القانون منها وصلًا (الآخرُ ضمّة) ووقفًا (الآخرُ ساكن). -/
def lawIsm : List (Haraka × Haraka) :=
  ismPairs.filter fun p => strictB (shape p.1 p.2 .damma) && strictPauseB (shape p.1 p.2 .sukun)

theorem law_ism_twelve : lawIsm.length = 12 := by decide +kernel

/-- القانونُ لا يُسقط بناءً من الاثني عشر. -/
theorem law_ism_all : lawIsm = ismPairs := by decide +kernel

/-- المنقول: (الأوّل، الثاني، سطرُ الكتاب المختوم، المثال). -/
def naqlIsm : List (Haraka × Haraka × Nat × String) :=
  [(.fatha, .sukun, 18625, "صقر"), (.kasra, .sukun, 18626, "عكم"), (.damma, .sukun, 18628, "برد"),
   (.fatha, .fatha, 18630, "جبل"), (.fatha, .kasra, 18631, "كتف"), (.fatha, .damma, 18632, "رجل"),
   (.damma, .fatha, 18633, "صرد"), (.damma, .damma, 18635, "طنب"), (.kasra, .fatha, 18637, "ضلع"),
   (.kasra, .kasra, 18640, "إبل")]

theorem naql_ism_ten : naqlIsm.length = 10 := by rfl

theorem naql_ism_nodup : (naqlIsm.map fun r => (r.1, r.2.1)).Nodup := by decide

/-- كلُّ منقولٍ مرخَّصٌ بالقانون. -/
theorem naql_sub_law : naqlIsm.all (fun r => lawIsm.contains (r.1, r.2.1)) = true := by decide +kernel

/-- ما رخّصه القانونُ ولم تنقله العرب: فُعِل وفِعُل بأعيانهما (س18641). -/
theorem law_minus_naql :
    lawIsm.filter (fun p => !naqlIsm.any fun r => (r.1, r.2.1) == p) = [(.damma, .kasra), (.kasra, .damma)] := by
  decide +kernel

/-- النسبةُ: الفضاءُ المولَّد بالنقل عُشرُ الممكن الأعمى تقريبًا، لا ‎113^n‎. -/
theorem generated_vs_blind : naqlIsm.length * 6 < shapes64.length ∧ shapes64.length < wasl 2 := by
  rw [shapes64_length, wasl_two] <;> decide

/-! ## الدرجاتُ الأعلى في جدول الفضاء المولَّد (ADR ٧٠؛ سدُّ `GENERATED_SPACE_HIGHER_DEGREES`)

* الفعلُ الثلاثيّ المجرّد (آخرُه فتحةٌ أبدًا): الأعمى 12 (الأوّلُ من ثلاث والثاني من أربع)، والقانونُ يبقيها
  (`law_fil_twelve`)؛ والمنقولُ أربعة: فَعَلَ فَعِلَ فَعُلَ (أبوابُ `Tasrif.harakat3`، ADR ٢٦) وفُعِلَ
  («لا يكون إلّا في الفعل»، الكتاب س18641) — `naql_fil_four`، `naql_fil_sub_law`.
* الرباعيُّ المجرّد (أربعةُ أصول، آخرُه فتحة): الأعمى 48، والقانونُ (`law_rubai`)، والمنقولُ واحدٌ فَعْلَلَ
  (`Rubai.rubai_one_mujarrad`، ADR ٢٨) — `naql_rubai_one`.
* الزوائدُ: القوالبُ الإحدى والثلاثون كلُّها مرخَّصة (`Wazn.thulathi_licensed`) — `zawaid_row`. -/

/-- أبنيةُ الفعل الثلاثيّ: الأوّلُ والثاني، والآخرُ فتحة. -/
def lawFil : List (Haraka × Haraka) :=
  ismPairs.filter fun p => strictB (shape p.1 p.2 .fatha) && strictPauseB (shape p.1 p.2 .sukun)

theorem law_fil_twelve : lawFil.length = 12 := by decide +kernel

/-- المنقولُ للفعل: الأبوابُ الثلاثة بفتح الأوّل، وفُعِلَ (س18641). -/
def naqlFil : List (Haraka × Haraka × Nat) :=
  (Tasrif.harakat3.map fun h => (Haraka.fatha, h, 19036)) ++ [(.damma, .kasra, 18641)]

theorem naql_fil_four : naqlFil.length = 4 := by rfl

theorem naql_fil_sub_law : naqlFil.all (fun r => lawFil.contains (r.1, r.2.1)) = true := by
  decide +kernel

/-- فُعِلَ فعلٌ لا اسم: في منقول الفعل وليس في منقول الاسم (س18641). -/
theorem fuila_verb_only :
    naqlFil.any (fun r => (r.1, r.2.1) == (.damma, .kasra)) = true ∧
    naqlIsm.any (fun r => (r.1, r.2.1) == (.damma, .kasra)) = false := by decide +kernel

/-- أصولٌ أربعة شاهدة (د ح ر ج) بحركاتٍ على الثلاثة الأولى، والآخرُ فتحة. -/
def shape4 (a b c : Haraka) : List Cell :=
  [atom 'د' a, atom 'ح' b, atom 'ر' c, atom 'ج' .fatha]

def shapes48 : List (List Cell) := h3.flatMap fun a => h4.flatMap fun b => h4.map fun c => shape4 a b c

theorem shapes48_length : shapes48.length = 48 := by decide +kernel

theorem law_rubai : (shapes48.filter strictB).length = 45 := by decide +kernel

/-- المنقولُ واحد: فَعْلَلَ، وهو مرخَّص. -/
theorem naql_rubai_one :
    (Rubai.abniya.filter fun B => !Rubai.augmented B).length = 2 ∧
    strictB (shape4 .fatha .sukun .fatha) = true := by
  refine ⟨by decide, by decide +kernel⟩

/-- الزوائد: الإحدى والثلاثون قالبًا. -/
theorem zawaid_row : Wazn.thulathi.length = 31 := by decide

end A116.Tawafiq
