import SLGE.Law

/-!
# ولادةُ الجملة بالحساب الصنفيّ: الأصنافُ نفسُها والحدُّ انتقالٌ بلا وزن

قولُ المالك في الجلسة (2026-11-01، 12:40 بتوقيت عمّان): «… ولكن يجب ان نوحد الحساب من الان وصاعدا بقانون واحد جبري».

آلةُ الجملة للمالك (`SLGE.Law.Msent`: الخاناتُ الـ116 والحدُّ 116) كما هي. وأصنافُ الكلمة الثلاثة عشر (`SLGE.Law.HisabKalima.sK`)
نفسُها تتكافأ عليها (`SLGE.Law.HisabJumla.jumla_mutakafi`؛ والحسابُ الصنفيّ `hisabJumla` في ملفّ المالك منذ 2026-11-01، وكان هنا في #119)، وحدُّ الكلمة مدخلٌ وزنُه صفر: من الأصناف ‎1‎ و‎2‎ و‎3‎ و‎9‎ و‎10‎ و‎11‎ إلى الابتداء، ومن ‎5‎ إلى ‎7‎،
وممّا سواها إلى الممتنع. فيخرج من القانون الواحد التكرار لكلّ درجة: `S(k+4) = 336·S(k+3) + 4676·S(k+2)` (`wilada_jumla`)،
وأعدادُ المالك (`SLGE.Law.sent_levels`) مبرهنةٌ بالحساب الصنفيّ في `SLGE/Law.lean`، و`jumla_bil_qanun` يجمعها هنا ومعها الدرجةُ
الرابعة 7490858144.

والمعاملان من صفوف الأصناف (`jumla_khatwa`)؛ والمبرهَنُ التكرارُ نفسُه، وتأويلُ 336 و4676 بالمقاطع لم يُبنَ.

المبرهنات هنا: 3 بالمعيار الموحَّد: لكلّ 2 (`tawlidS`، `wilada_jumla`)؛ و1 على الشاهد خارجَ حرف المعيار، معلَن (`jumla_bil_qanun`: `awailS`).
وخمسَ عشرةَ مبرهنةً كانت هنا نُقلت بأسمائها إلى `SLGE.Law.HisabJumla` (`hawkama/الحساب_الصنفي.md`).
-/

namespace Dal.WiladaJumla
open SLGE SLGE.Law SLGE.Law.HisabJumla

/-- **التكرارُ من صفوف الخطوة:** `Z₀(k+4) = 336·Z₀(k+3) + 4676·Z₀(k+2)`. -/
theorem tawlidS (Z : Nat → Nat → Nat) (h : KhatwaS Z) (k : Nat) :
    Z 0 (k + 4) = 336 * Z 0 (k + 3) + 4676 * Z 0 (k + 2) := by
  obtain ⟨a0, a1, a2, a3, a4, a5, a7, a9, a10, a11⟩ := h k
  obtain ⟨b0, b1, b2, b3, b4, b5, b7, b9, b10, b11⟩ := h (k + 1)
  obtain ⟨c0, c1, c2, c3, c4, c5, c7, c9, c10, c11⟩ := h (k + 2)
  obtain ⟨d0, d1, d2, d3, d4, d5, d7, d9, d10, d11⟩ := h (k + 3)
  simp only [Nat.add_assoc, Nat.reduceAdd] at *
  omega

/-- **قانونُ ولادة الجملة (لكلّ k):** `S(k+4) = 336·S(k+3) + 4676·S(k+2)`. -/
theorem wilada_jumla (k : Nat) :
    Msent.lev 3 0 (k + 4) = 336 * Msent.lev 3 0 (k + 3) + 4676 * Msent.lev 3 0 (k + 2) := by
  simp only [lev_jumla]
  exact tawlidS z jumla_khatwa k

/-- **أعدادُ المالك من القانون:** 0 و168 و61096 و21443968 (`SLGE.Law.sent_levels`)، والدرجةُ الرابعة 7490858144. -/
theorem jumla_bil_qanun : Msent.lev 3 0 0 = 0 ∧ Msent.lev 3 0 1 = 168 ∧ Msent.lev 3 0 2 = 61096 ∧ Msent.lev 3 0 3 = 21443968 ∧
    Msent.lev 3 0 4 = 7490858144 := by
  simp only [lev_jumla]
  obtain ⟨w0, w1, w2, w3, w4, w5, w7, w9, w10, w11⟩ := bidaya_jumla
  exact ⟨w0, awailS z jumla_khatwa w0 w1 w2 w3 w4 w5 w7 w9 w10 w11⟩

end Dal.WiladaJumla
