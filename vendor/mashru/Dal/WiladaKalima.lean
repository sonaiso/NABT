import SLGE.Law

/-!
# ولادةُ الكلمة بالحساب الصنفيّ: موقوفًا عليها وفي الوصل

قولُ المالك في الجلسة (2026-11-01، 12:40 بتوقيت عمّان): «… ولكن يجب ان نوحد الحساب من الان وصاعدا بقانون واحد جبري».

آلةُ الكلمة للمالك (`SLGE.Law.Mword` موقوفًا عليها، و`MwordWasl` في الوصل) كما هي، وعدُّها `Machine.lev` بالاستنفاد.
وحالاتُها السبعُ والتسعون تتكافأ في ثلاثة عشر صنفًا، وحسابُها الصنفيّ في ملفّ المالك نفسِه منذ 2026-11-01 (`SLGE.Law.HisabKalima`،
`hisabWaqf`، `hisabWasl`؛ وكان هنا في #119 ونُقل بإذنه، انظر رأس `SLGE/HisabSinfi.lean`)، فيُعدّ الكلمةُ على صفوفها، ويخرج منه هنا التكرار لكلّ درجة:
* موقوفًا عليها: `L(k+4) = 168·L(k+3) + 2296·L(k+2)` (`wilada_waqf`)؛
* وفي الوصل: `L(k+3) = 168·L(k+2) + 2296·L(k+1)` (`wilada_wasl`).

والمعاملان يساويان عددَي مقطعين على آلة المالك: 168 ما وزنُه صامتٌ واحد (‎CV‎ و‎CVV‎، 84 و84)، و2296 ‎CVC‎
(`kalima_maqati`)؛ وكونُ ذلك سببَهما قراءةُ البنّاء. والفرقُ بين الوقف والوصل صنفٌ واحد: الساكنان المعلّقان على الوقف (‎4‎) يُقبلان
موقوفًا عليهما وحدهما، ولا ينتقل منهما شيءٌ إلّا إلى الممتنع، فلا يُعدّ منهما إلّا الدرجةُ صفرٌ موقوفًا عليها
(`y FW 4 0 = 1` و`y FL 4 0 = 0`)، وبه يتأخّر التكرارُ في الوقف درجةً.
وأعدادُ المالك (`SLGE.Law.word_levels`، `word_levels_wasl`) مبرهنةٌ بالحساب الصنفيّ في `SLGE/Law.lean`، و`kalima_bil_qanun` يجمعها هنا
ومعها الدرجةُ الرابعة.

الأصنافُ وصفوفُها في رأس قسمها في `SLGE/Law.lean`.

المبرهنات هنا: 5 بالمعيار الموحَّد: لكلّ 3 (`tawlid`، `wilada_waqf`، `wilada_wasl`)؛ وعلى الشاهد 1 برهانُها decide (`kalima_maqati`)؛ و1 على
الشاهد خارجَ حرف المعيار، معلَن (`kalima_bil_qanun`: `awail`). وعشرون مبرهنةً كانت هنا نُقلت بأسمائها إلى `SLGE.Law.HisabKalima` (`hawkama/الحساب_الصنفي.md`).

**وعدٌّ مباشرٌ معلَن:** `kalima_maqati` يعدّ على آلة `Mword` خانةً وخانتين بـ decide لا بالأصناف، شاهدًا لمعنى المعاملين؛ و84 الأولى يثبت المالك
نظيرَها على 117 رمزًا (`SLGE.Law.cell_count`)، و168 على آلة المقطع (`SLGE.Law.sl1`)؛ وقسمةُ 4648 (`sl2`) إلى 2296 ‎CVC‎ و2352 ‎CVVC‎ عدُّ أداةٍ
(مرآةُ بايثون في مسوّدة الجلسة) بلا وسم.
-/

namespace Dal.WiladaKalima
open SLGE SLGE.Law SLGE.Law.HisabKalima

/-- **التكرارُ من صفوف الخطوة:** `Y₀(k+4) = 168·Y₀(k+3) + 2296·Y₀(k+2)`، ومن الدرجة الأولى إن لم يُقبل الصنفُ ‎4‎. -/
theorem tawlid (Y : Nat → Nat → Nat) (h : Khatwa Y) (k : Nat) :
    Y 0 (k + 4) = 168 * Y 0 (k + 3) + 2296 * Y 0 (k + 2) ∧
    (Y 4 k = 0 → Y 0 (k + 3) = 168 * Y 0 (k + 2) + 2296 * Y 0 (k + 1)) := by
  obtain ⟨a0, a1, a2, a3, a4, a5, a9, a10, a11⟩ := h k
  obtain ⟨b0, b1, b2, b3, b4, b5, b9, b10, b11⟩ := h (k + 1)
  obtain ⟨c0, c1, c2, c3, c4, c5, c9, c10, c11⟩ := h (k + 2)
  obtain ⟨d0, d1, d2, d3, d4, d5, d9, d10, d11⟩ := h (k + 3)
  simp only [Nat.add_assoc, Nat.reduceAdd] at *
  exact ⟨by omega, fun z => by omega⟩

/-- **قانونُ الولادة موقوفًا عليها (لكلّ k):** `L(k+4) = 168·L(k+3) + 2296·L(k+2)`. -/
theorem wilada_waqf (k : Nat) : Mword.lev 3 0 (k + 4) = 168 * Mword.lev 3 0 (k + 3) + 2296 * Mword.lev 3 0 (k + 2) := by
  simp only [lev_waqf]
  exact (tawlid (y FW) (kalima_khatwa FW rfl) k).1

/-- **قانونُ الولادة في الوصل (لكلّ k):** `L(k+3) = 168·L(k+2) + 2296·L(k+1)`. -/
theorem wilada_wasl (k : Nat) :
    MwordWasl.lev 3 0 (k + 3) = 168 * MwordWasl.lev 3 0 (k + 2) + 2296 * MwordWasl.lev 3 0 (k + 1) := by
  simp only [lev_wasl]
  refine (tawlid (y FL) (kalima_khatwa FL rfl) k).2 ?_
  cases k with
  | zero => exact bidaya_wasl.2.2.2.2.1
  | succ m => exact (kalima_khatwa FL rfl m).2.2.2.2.1

/-- **أعدادُ المالك من القانون:** 0 و168 و32872 و6038368 موقوفًا عليها، و5908224 في الوصل للدرجة الثالثة
(`SLGE.Law.word_levels`، `word_levels_wasl`)، والدرجةُ الرابعة 1089919936 و1068055744. -/
theorem kalima_bil_qanun : Mword.lev 3 0 0 = 0 ∧ Mword.lev 3 0 1 = 168 ∧ Mword.lev 3 0 2 = 32872 ∧ Mword.lev 3 0 3 = 6038368 ∧
    Mword.lev 3 0 4 = 1089919936 ∧ MwordWasl.lev 3 0 1 = 168 ∧ MwordWasl.lev 3 0 2 = 32872 ∧
    MwordWasl.lev 3 0 3 = 5908224 ∧ MwordWasl.lev 3 0 4 = 1068055744 ∧ MwordWasl.lev 3 0 0 = 0 := by
  simp only [lev_waqf, lev_wasl]
  obtain ⟨w0, w1, w2, w3, w4, w5, w9, w10, w11⟩ := bidaya_waqf
  obtain ⟨l0, l1, l2, l3, l4, l5, l9, l10, l11⟩ := bidaya_wasl
  have aw := awail (y FW) (kalima_khatwa FW rfl) w0 w1 w2 w3 w5 w9 w10 w11
  have al := awail (y FL) (kalima_khatwa FL rfl) l0 l1 l2 l3 l5 l9 l10 l11
  rw [w4] at aw
  rw [l4] at al
  exact ⟨w0, aw.1, aw.2.1, aw.2.2.1, aw.2.2.2, al.1, al.2.1, al.2.2.1, al.2.2.2, l0⟩

/-- **المقاطع:** خانةٌ واحدةٌ مقبولةٌ وقفًا 84 (‎CV‎)، وخانتان بصامتٍ واحد 84 (‎CV‎ ثمّ مدّ: ‎CVV‎)، وخانتان بصامتين تنتهيان بعد ساكنٍ
مُغلِق 2296 (‎CVC‎) — عدٌّ مباشرٌ على آلة المالك. -/
theorem kalima_maqati :
    ((List.range 116).filter fun a => Fwaqf (run 0 [a])).length = 84 ∧
    (((List.range 116).flatMap fun a => (List.range 116).map fun b => [a, b]).filter
      fun l => Fwaqf (run 0 l) && wt 0 l == 1).length = 84 ∧
    (((List.range 116).flatMap fun a => (List.range 116).map fun b => [a, b]).filter
      fun l => wt 0 l == 2 && 67 ≤ run 0 l && run 0 l < 96).length = 2296 := by
  decide +kernel

end Dal.WiladaKalima
