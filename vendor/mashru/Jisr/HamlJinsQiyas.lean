/-
# الحملُ من الجنس على ضابطه المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن** (`Jisr/HamlJinsDabit.lean`، بنصّ المواصفة `tahaqquq/dawabit/haml_jins/wasf.md` §القياس): لكلّ حالةٍ من `Dabit.halat` (كتبها مؤلّفٌ
مستقلٌّ إجرائيًّا من المواصفة والمصدر `masdar.md` — أقوالِ المالك وقراراتِه بنصّها —، وفي سياقه ما حُقن آليًّا — `taalif.md` —، وجُمّدت ببصمتها في
`tahaqquq/dawabit/haml_jins/tajmid.json` قبل الشفرة): حقلُ الحكم (`hukmMujarrad` على الجنس والمثال والنسبة).

**الوسم.** أربعُ مبرهناتٍ على الشاهد بالمعيار الموحَّد: `majal`، `natija`، `natija_fia`، `akhta_1` (`decide` على الحالات المجمَّدة). ومعنى العدّ
موافقةُ الشفرة لقراءةٍ مستقلّةٍ لأقوال المالك، لا تغطيةُ اللغة: الحالاتُ مؤلَّفة لا عيّنةٌ من استعمال.

**التشغيلات.** سجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/haml_jins/` (`natija_1.json` …).
- `natija_1.json`: التشغيلُ الأوّل على الشفرة كما دُفعت في `506e52d` (والحالاتُ مجمَّدةٌ في `8c5ef73` قبلها): 23 صوابًا من 24، واختيارٌ بلا مرجّحٍ واحد في حالة الغموض H24 (أحدُ البديلين).
-/
import Jisr.HamlJinsDawabit

namespace Jisr
namespace QabiliyyaJins
namespace Qiyas

open Dabit

/-- أعدادُ المجال بترتيبٍ ثابت (يحسبها `tahaqquq/test_haml_jins.py` من `cases.json` بالترتيب نفسه): الحالات؛ ثمّ الحكمُ المتوقَّع: مرخَّص،
    لا حكم، ممتنع، لا جنس، لا مثال، بديلان؛ ثمّ الفئاتُ: موجب، حدّ، خارج، عموم، غموض. -/
def majalAadad : List Nat :=
  [halat.length] ++
  [HukmMujarrad.murakhkhas, .laHukm, .mumtani, .laJins, .laMithal].map (fun d => (halat.filter (·.hukm == [d])).length) ++
  [(halat.filter (fun h => decide (2 ≤ h.hukm.length))).length] ++
  [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map (fun f => (halat.filter (·.fia == f)).length)

/-- **المجالُ غيرُ فارغ ولا مائلٍ إلى «لا حكم»:** 24 حالة. والمتوقَّع: مرخَّص 10، ولا حكم 2، وممتنع 4، ولا جنس 3، ولا مثال 4، وبديلان في
    حالةٍ واحدة؛ والفئات: موجب 6، وحدّ 6، وخارج 7، وعموم 4، وغموض 1. -/
theorem majal : majalAadad = [24, 10, 2, 4, 3, 4, 1, 6, 6, 7, 4, 1] := by
  decide +kernel

/-- **النتيجة على الشفرة الحاليّة:** 23 صوابًا من 24، واختيارٌ بلا مرجّحٍ واحد؛ ولا نقصَ تغطية ولا تجاوزَ ولا قبولَ خاطئًا ولا ردَّ خاطئًا. -/
theorem natija : ihsa (natayij halat) = ⟨23, 0, 0, 0, 0, 1, 0⟩ := by
  decide +kernel

/-- **بالفئات:** موجب 6، وحدّ 6، وخارج 7، وعموم 4 — كلُّها صواب؛ وغموض 1 اختيارٌ بلا مرجّح. -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map (fun f => ihsa ((natayij halat).filter (·.2.1 == f))) =
      [⟨6, 0, 0, 0, 0, 0, 0⟩, ⟨6, 0, 0, 0, 0, 0, 0⟩, ⟨7, 0, 0, 0, 0, 0, 0⟩, ⟨4, 0, 0, 0, 0, 0, 0⟩,
       ⟨0, 0, 0, 0, 0, 1, 0⟩] := by
  decide +kernel

/-- **والإخفاقُ الواحد بعينه:** H24 (غموضٌ ببديلين) اختار المحرّكُ أحدَهما. -/
theorem akhta_1 :
    akhta (natayij halat) = [("H24", .ikhtiyar)] := by
  decide +kernel

end Qiyas
end QabiliyyaJins
end Jisr
