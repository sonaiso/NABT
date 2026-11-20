/-
# نواةُ التوليد على ضابطها المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن** (`Jisr/TawlidDabit.lean`، بنصّ المواصفة `tahaqquq/dawabit/nawat_tawlid/wasf.md` §القياس): لكلّ حالةٍ من `Dabit.halat` (كتبها مؤلّفٌ
مستقلٌّ إجرائيًّا من المواصفة والمصدر `masdar.md` — أقوالِ المالك وقراراتِه بنصّها —، وفي سياقه ما حُقن آليًّا — `taalif.md` —، وجُمّدت ببصمتها في
`tahaqquq/dawabit/nawat_tawlid/tajmid.json` قبل الشفرة): الصيغةُ والموروثُ والقيدُ بالتساوي، وحقلُ الحكم (`hukmMiftah` على الجذر والعامل والجنس).

**الوسم.** أربعُ مبرهناتٍ على الشاهد بالمعيار الموحَّد: `majal`، `natija`، `natija_fia`، `akhta_1` (`decide` على الحالات المجمَّدة). ومعنى العدّ
موافقةُ الشفرة لقراءةٍ مستقلّةٍ لأقوال المالك، لا تغطيةُ اللغة: الحالاتُ مؤلَّفة لا عيّنةٌ من استعمال؛ ونواةٌ من جذرين لا معجم.

**التشغيلات.** سجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/nawat_tawlid/` (`natija_1.json` …).
- `natija_1.json`: التشغيلُ الأوّل على الشفرة كما أُودعت في `284bdf4` (والحالاتُ مجمَّدةٌ في `c965a18` قبلها): 32 صوابًا من 32.
-/
import Jisr.TawlidDawabit

namespace Jisr
namespace Tawlid
namespace Qiyas

open Dabit

/-- أعدادُ المجال بترتيبٍ ثابت (يحسبها `tahaqquq/test_tawlid.py` من `cases.json` بالترتيب نفسه): الحالات؛ ثمّ الحكمُ المتوقَّع: مرخَّص،
    لا حكم، ممتنع، لا نواة، لا جنس، بديلان؛ ثمّ الفئاتُ: موجب، حدّ، خارج، صورة، غموض. -/
def majalAadad : List Nat :=
  [halat.length] ++
  [Hukm.murakhkhas, .laHukm, .mumtani, .laNawat, .laJins].map (fun d => (halat.filter (·.hukm == [d])).length) ++
  [(halat.filter (fun h => decide (2 ≤ h.hukm.length))).length] ++
  [Fia.mujib, .hadd, .kharij, .sura, .ghumud].map (fun f => (halat.filter (·.fia == f)).length)

/-- **المجالُ غيرُ فارغ ولا مائلٍ إلى «لا حكم»:** 32 حالة. والمتوقَّع: مرخَّص 4، ولا حكم 11، وممتنع 11، ولا نواة 3، ولا جنس 3، ولا بديلين؛
    والفئات: موجب 4، وحدّ 11، وخارج 6، وصورة 11، وغموض 0. -/
theorem majal : majalAadad = [32, 4, 11, 11, 3, 3, 0, 4, 11, 6, 11, 0] := by
  decide +kernel

/-- **النتيجة على الشفرة الحاليّة:** 32 صوابًا من 32؛ ولا نقصَ تغطية ولا تجاوزَ ولا قبولَ خاطئًا ولا ردَّ خاطئًا ولا اختيارَ ولا خطأ. -/
theorem natija : ihsa (natayij halat) = ⟨32, 0, 0, 0, 0, 0, 0⟩ := by
  decide +kernel

/-- **بالفئات:** موجب 4، وحدّ 11، وخارج 6، وصورة 11 — كلُّها صواب؛ وغموض 0. -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .sura, .ghumud].map (fun f => ihsa ((natayij halat).filter (·.2.1 == f))) =
      [⟨4, 0, 0, 0, 0, 0, 0⟩, ⟨11, 0, 0, 0, 0, 0, 0⟩, ⟨6, 0, 0, 0, 0, 0, 0⟩, ⟨11, 0, 0, 0, 0, 0, 0⟩,
       ⟨0, 0, 0, 0, 0, 0, 0⟩] := by
  decide +kernel

/-- **ولا إخفاق.** -/
theorem akhta_1 :
    akhta (natayij halat) = [] := by
  decide +kernel

end Qiyas
end Tawlid
end Jisr
