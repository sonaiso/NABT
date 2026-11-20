/-
# الموصول على ضابطه المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن.** لكلّ حالةٍ من `Dawabit.halat` (كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والمصدرين، وفي سياقه ما حُقن آليًّا — `taalif.md` —،
وجُمّدت ببصمتها في `tahaqquq/dawabit/mawsul/tajmid.json` قبل الشفرة): الحكمُ المتوقَّع وحكمُ `Jisr.Mawsul.jawab`، والدرجةُ حين يكون المتوقَّعُ
«مقبول»، بتصنيف `Dabit.qarinHukm` و`Dabit.qarinDaraja`.

**الوسم.** العدُّ «مبرهن على الشاهد» (`decide` على الحالات المجمَّدة). ومعناه موافقةُ الشفرة لقراءةٍ مستقلّةٍ للنطاق، لا تغطيةُ اللغة:
الحالاتُ مؤلَّفة لا عيّنةٌ من استعمال.

**التشغيلات.** المبرهناتُ هنا على الشفرة الحاليّة دائمًا. وسجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/mawsul/` (`natija_1.json` …)،
ويفحصه `tahaqquq/test_mawsul.py`:
- `natija_1.json`: التشغيلُ الأوّل على الشفرة المجمَّدة في `e13b5a0`، قبل أن يقرأ البنّاءُ الحالات: 79 صوابًا من 88 حقلًا مسؤولًا (59 حكمًا و29
  درجة): نقصُ تغطيةٍ 3 (M29، M31، M36)، وتجاوزٌ 2 (M13، M47)، واختيارٌ بلا مرجّح 4 (M56–M59). وأسماءُ مبرهناته أسماؤها في `1954797`.
- `natija_2.json`: بعد تعديل `Jisr/Mawsul.lean` بقراءة المؤلّف في المواضع كلِّها (فيه «ما غُيّر بعد قراءة الحالات»)، على مادّةٍ مكشوفة: 88 من 88.
- `natija_3.json`: بعد مراجعة `murajii` الأولى (مبرهناتٌ أربعٌ ورأسُ الشفرة، `8cf5170`)، بلا تغييرٍ في `jawab`: 88 من 88.
-/
import Jisr.MawsulDawabit

namespace Jisr
namespace Mawsul
namespace Qiyas

open Dabit Dawabit

/-- أعدادُ المجال بترتيبٍ ثابت: الحالات؛ ثمّ الحكمُ المتوقَّع: مقبول، خطأ، «لا حكم»، بديلان؛ ثمّ الدرجةُ المتوقَّعة لما متوقَّعُه «مقبول»:
    قليل، نزر، لغة، بلا درجة، بديلان؛ ثمّ ذواتُ الزوج؛ ثمّ الفئات: موجب، حدّ، خارج، عموم، غموض. -/
def majalAadad : List Nat :=
  let maq := halat.filter (·.hukm == [.maqbul])
  [halat.length] ++
  [Hukm.maqbul, .khata, .laHukm].map (fun d => (halat.filter (·.hukm == [d])).length) ++
  [(halat.filter (fun h => decide (2 ≤ h.hukm.length))).length] ++
  [Daraja.qalil, .nazr, .lugha, .bila].map (fun d => (maq.filter (·.daraja == [d])).length) ++
  [(maq.filter (fun h => decide (2 ≤ h.daraja.length))).length,
   (halat.filter (·.zawj.isSome)).length] ++
  [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map (fun f => (halat.filter (·.fia == f)).length)

/-- **المجال:** 59 حالة. والحكمُ المتوقَّع: مقبول 29، وخطأ 21، و«لا حكم» 5، وبديلان في 4؛ والدرجةُ فيما متوقَّعُه «مقبول»: قليل 0، ونزر 1،
    ولغة 1، وبلا درجة 27، وبديلان 0؛ و32 حالةً لها زوج. والفئات: موجب 24، وحدّ 19، وخارج 5، وعموم 7، وغموض 4. -/
theorem majal : majalAadad = [59, 29, 21, 5, 4, 0, 1, 1, 27, 0, 32, 24, 19, 5, 7, 4] := by
  decide +kernel

/-- **النتيجة:** 88 صوابًا من 88 حقلًا مسؤولًا (59 حكمًا و29 درجة). -/
theorem natija : ihsa (natayij halat) = ⟨88, 0, 0, 0, 0, 0, 0, 0⟩ := by
  decide +kernel

/-- **بالفئات:** موجب 48، وحدّ 19، وخارج 5، وعموم 12، وغموض 4؛ صوابٌ كلُّها. -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map (fun f => ihsa ((natayij halat).filter (·.2.1 == f))) =
      [⟨48, 0, 0, 0, 0, 0, 0, 0⟩, ⟨19, 0, 0, 0, 0, 0, 0, 0⟩, ⟨5, 0, 0, 0, 0, 0, 0, 0⟩, ⟨12, 0, 0, 0, 0, 0, 0, 0⟩,
       ⟨4, 0, 0, 0, 0, 0, 0, 0⟩] := by
  decide +kernel

/-- **لا إخفاق.** -/
theorem akhta_sifr : akhta (natayij halat) = [] := by
  decide +kernel

/-- الحقلان في الحالة صوابٌ كلاهما. -/
def sawab (i : String) : Bool :=
  (natayij halat).all fun x => !(x.1 == i || x.1 == i ++ "/daraja") || x.2.2 == Natija.sawab

/-- **الأزواج** (مدخلان يختلفان في حقلٍ واحد): ستّةَ عشرَ زوجًا، يتغيّر جوابُ المحرّك فيها كلِّها، ويصيب الطرفان معًا فيها كلِّها. -/
theorem azwaj_1 :
    (azwaj halat).length = 16 ∧ ((azwaj halat).filter (·.2.2)).length = 16 ∧
    ((azwaj halat).filter fun p => sawab p.1 && sawab p.2.1).length = 16 := by
  decide +kernel

end Qiyas
end Mawsul
end Jisr
