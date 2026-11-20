import A116.Marja
import A116.Sawt
import Dal.Makharij
import SLGE.Law

/-!
# المرحلة «ج»: آلةُ δ في Mashru على جدول مرجع المالك (A116.Marja)

**الأمر.** قرارُ المالك (2026-10-20، 00:23) بمراحل قانون المواصفة الأربع، ومنها «(ج) برهانُ مطابقة آلة δ لجدول Marja بعد إيداع ملفّاته»؛ ثمّ
قولُه في الجلسة (2026-11-20، 03:10) على اقتراح البنّاء: «i agree to do next step». وملفّاتُ Marja دخلت Mashru باستيراد A116 (`A116/Marja.lean`،
`jadawil/a116/marja*.csv`).

**ما يُقارَن.** جدولُ Marja ‎1044 = 116 × 9‎ ولادةً: لكلّ خانةٍ ولكلّ موضعٍ (الابتداء، والوصلُ والوقفُ بعد كلّ حالةٍ من الأربع) حكمٌ:
مرخَّص، أو مشروطٌ بأصنافٍ من السابق، أو «يُسكَّن»، أو مرفوضٌ باسمه. والآلةُ `SLGE.Law.δ` (آلةُ المالك المنقولة بنصّها) تحكم على سلسلةٍ
عينيّة. **فالجسرُ تعيينُ البنّاء:**
* الخانةُ رمزُها في الآلة ‎4c + s‎: ‎c‎ رتبةُ حرفها في `Dal.hawamil` (حروفُها من `A116.Sawt.charOf`)، و‎s‎ رقمُ حالتها (`ramzA`)؛ وهو تقابلٌ
  على الـ116 (`ramzA_taqabul`).
* حالاتُ الآلة لكلّ صنفٍ من أصناف السابق في Marja (`Marja.qablK`): بعد متحرّكٍ حالتُه ‎p‎ ← ‎1 + p‎؛ وبعد مدّ (`v`) ← ‎4‎؛ وبعد ساكنٍ مُغلِق
  (`c`) ← ‎67 + k‎ لكلّ حاملٍ ‎k‎ إلّا الألف (لا تُغلِق).
* القبولُ وصلًا `Fwasl` ووقفًا `Fwaqf` بعد ‎δ‎؛ والصنفُ مقبولٌ «كلًّا» إن قبلت الآلةُ الخانةَ بعد كلّ حالاته.
* **الموافقة** (`tawafuq`): الابتداءُ مرخَّصٌ ⟺ ‎δ 0 a ≠ 96‎؛ والمرخَّصُ و«يُسكَّن» ⟺ كلُّ أصناف السابق مقبولةٌ كلًّا؛ والمشروطُ بأصنافٍ ⟺ هي
  وحدَها المقبولةُ، كلًّا؛ والمرفوضُ ⟺ لا صنفَ مقبولٌ ولو بحالةٍ واحدة. و«يُسكَّن» (Marja يسكّن المتحرّكَ وقفًا) تقابله الآلةُ بقبول الوقف
  على السلسلة بحالتها — تعيين.

**النتيجة (على الجدول، `decide +kernel`):** الموافقةُ في **925** من 1044، والخلافُ في **119** كلُّه في صنفين مسمّيين لا ثالثَ لهما
(`khilaf_sinfan`، `mawadi_khilaf_alif`):
* **الألفُ الساكنة** (`khilafAlif`، 5): ‎«اْ»‎ بعد ضمّةٍ أو كسرةٍ وصلًا ووقفًا، وبعد ساكنٍ وقفًا — يرخّصها Marja (لا يرى من الألف في الجوار
  إلّا قيدَ `licensableCell`) وتردّها الآلة (الألفُ لا تقع إلّا مدَّ الفتحة: `SLGE.Law.δ`، وسيطٌ معلَن في `SLGE/Law.lean`).
* **التجاور** (`khilafTajawur`، 114): بعد ساكنٍ مُغلِقٍ يرخّص Marja الخانةَ على صنف `c` كلِّه، وتردّها الآلةُ بعد المُغلِق الذي من مخرجها
  (`SLGE.Law.conflict`: حاملان مختلفان من مخرجٍ واحد، ليس أحدُهما حرفَ علّة) — Marja يحكم على الصنف، والآلةُ على الحامل.
والقرارُ في الصنفين للمالك: أيُّ القانونين يُعتمد، أو يُرفع Marja إلى الحامل في الصنف `c`.

**الوسم.** كلُّ ما هنا «مبرهنٌ على الشاهد» (`decide +kernel` على الولادات الـ1044 والخانات الـ116)، والجسرُ (`ramzA`، `halatK`، `tawafuq`)
تعيينُ البنّاء؛ ولا يقول شيئًا في صحّة أيٍّ من القانونين لغةً.
-/

namespace Jisr
namespace MarjaMutabaqa

open A116 SLGE.Law

/-- رمزُ الخانة في آلة المالك: ‎4c + s‎ بترتيب `Dal.hawamil`. -/
def ramzA (x : Cell) : Nat := 4 * Dal.hawamil.idxOf (A116.Sawt.charOf x.carrier) + x.haraka.index

/-- **تقابل**: رموزُ الخانات الـ116 مختلفةٌ وكلُّها دون 116 (فهي ‎0…115‎). -/
theorem ramzA_taqabul :
    (Jadwal.khanat.map ramzA).Nodup ∧ (Jadwal.khanat.map ramzA).all (· < 116) = true ∧ Jadwal.khanat.length = 116 := by
  decide +kernel

/-- حالاتُ الآلة لصنف السابق (‎p‎ رقمُ حالة ما قبلها للمتحرّك). -/
def halatK : A116.Stages.K → Nat → List Nat
  | .cv, p => [1 + p]
  | .v, _ => [4]
  | .c, _ => ((List.range 29).filter (· != 2)).map (67 + ·)

/-- رقمُ حالة ما قبلها، وأصنافُ السابق في Marja (`Marja.qablK` بعينه: `qablM_qablK`). -/
def qablM : Marja.Mawdi → Nat × List A116.Stages.K
  | .ibtida => (0, [])
  | .wasl p | .waqf p => (p.index, if p == .sukun then [.v, .c] else [.cv])

/-- تعريفيّ على الشاهد: أصنافُ السابق هنا هي `Marja.qablK`. -/
theorem qablM_qablK : Marja.mawadi.all (fun m => (qablM m).2 == Marja.qablK m) = true := by decide

/-- القبولُ في الموضع: الوقفُ `Fwaqf`، وما سواه `Fwasl`. -/
def qabul : Marja.Mawdi → Nat → Bool
  | .waqf _ => Fwaqf
  | _ => Fwasl

/-- الأصنافُ المقبولةُ كلًّا: بعد كلّ حالاتها. -/
def kull (m : Marja.Mawdi) (a : Nat) : List A116.Stages.K :=
  (qablM m).2.filter fun k => (halatK k (qablM m).1).all fun q => qabul m (δ q a)

/-- الأصنافُ المقبولةُ ولو بحالةٍ واحدة. -/
def ayy (m : Marja.Mawdi) (a : Nat) : List A116.Stages.K :=
  (qablM m).2.filter fun k => (halatK k (qablM m).1).any fun q => qabul m (δ q a)

/-- **الموافقة** بين حكم Marja والآلة على الولادة. -/
def tawafuq (m : Marja.Mawdi) (x : Cell) : Bool :=
  let a := ramzA x
  match m with
  | .ibtida => (Marja.hukm m x == .murakhkhas) == (δ 0 a != 96)
  | _ => match Marja.hukm m x with
    | .murakhkhas | .yuskan => kull m a == (qablM m).2
    | .mashrut ok _ => kull m a == ok && ayy m a == ok
    | .marfud _ => (ayy m a).isEmpty

/-- خلافُ الألف الساكنة: ‎«اْ»‎ لا تقبلها الآلةُ بعد أيّ صنف. -/
def khilafAlif (m : Marja.Mawdi) (x : Cell) : Bool :=
  x == A116.Ladder.atom 'ا' .sukun && (ayy m (ramzA x)).isEmpty

/-- خلافُ التجاور: كلُّ الأصناف مقبولةٌ ببعض حالاتها، والصنفُ `c` ليس كلًّا، ولحاملها تجاورٌ مع حاملٍ مُغلِق. -/
def khilafTajawur (m : Marja.Mawdi) (x : Cell) : Bool :=
  (qablM m).2.contains .c && ayy m (ramzA x) == (qablM m).2 && !(kull m (ramzA x)).contains .c &&
  ((List.range 29).filter (· != 2)).any fun k => conflict k (ramzA x / 4)

/-- الولاداتُ المخالفة. -/
def khilafat : List (Cell × Marja.Mawdi) := Marja.wiladat.filter fun b => !tawafuq b.2 b.1

/-- **الابتداء**: حكمُ Marja هو حكمُ الآلة على الخانات الـ116 كلِّها. -/
theorem ibtida_tamm : Jadwal.khanat.all (tawafuq .ibtida) = true := by decide +kernel

/-- **الوصلُ بعد الفتحة**: موافقةٌ تامّة. -/
theorem wasl_fatha_tamm : Jadwal.khanat.all (tawafuq (.wasl .fatha)) = true := by decide +kernel

/-- **العدد**: 925 موافقة، و119 خلافًا. -/
theorem adad_mutabaqa : (Marja.wiladat.filter fun b => tawafuq b.2 b.1).length = 925 ∧ khilafat.length = 119 := by
  decide +kernel

/-- **الخلافُ صنفان لا ثالثَ لهما**: الألفُ الساكنة (5) والتجاور (114)، ولا ولادةَ فيهما معًا. -/
theorem khilaf_sinfan :
    (khilafat.filter fun b => khilafAlif b.2 b.1).length = 5 ∧
    (khilafat.filter fun b => khilafTajawur b.2 b.1).length = 114 ∧
    khilafat.all (fun b => khilafAlif b.2 b.1 != khilafTajawur b.2 b.1) = true := by
  decide +kernel

/-- **مواضعُ خلاف الألف**: ‎«اْ»‎ وصلًا بعد الضمّة والكسرة، ووقفًا بعد الضمّة والكسرة والسكون. (والصنفان يصنّفان الخلافَ ولا
يعرّفانه: ‎«اْ»‎ وصلًا بعد ساكنٍ يردّها الاثنان، فهي موافقة.) -/
theorem mawadi_khilaf_alif :
    (khilafat.filter fun b => khilafAlif b.2 b.1).map (·.2) =
      [.wasl .damma, .wasl .kasra, .waqf .damma, .waqf .kasra, .waqf .sukun] := by
  decide +kernel

end MarjaMutabaqa
end Jisr
