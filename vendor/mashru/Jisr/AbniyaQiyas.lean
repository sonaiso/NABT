/-
# أبنيةُ اسمَي الفاعل والمفعول على ضابطها المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن.** لكلّ حالةٍ من `Dawabit.halat` (كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والمصدرين، وفي سياقه ما حُقن آليًّا — `taalif.md` —،
وجُمّدت ببصمتها في `tahaqquq/dawabit/abniya/tajmid.json` قبل الشفرة): الحكمُ المتوقَّع وحكمُ `Jisr.Abniya.jawab`، والدرجةُ حين يكون المتوقَّعُ
«مقبول»، بتصنيف `Dabit.qarinHukm` و`Dabit.qarinDaraja`.

**الوسم.** العدُّ «مبرهن على الشاهد» (`decide` على الحالات المجمَّدة). ومعناه موافقةُ الشفرة لقراءةٍ مستقلّةٍ للنطاق، لا تغطيةُ اللغة:
الحالاتُ مؤلَّفة لا عيّنةٌ من استعمال.

**التشغيلات.** المبرهناتُ هنا على الشفرة الحاليّة دائمًا. وسجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/abniya/` (`natija_1.json` …)،
ويفحصه `tahaqquq/test_abniya.py`:
- `natija_1.json`: التشغيلُ الأوّل على الشفرة المجمَّدة في `105aa2d`، قبل أن يقرأ البنّاءُ الحالات: 61 صوابًا من 73 حقلًا مسؤولًا (50 حكمًا و23
  درجة): نقصُ تغطيةٍ 4 (B20، B23 حكمًا ودرجةً)، وتجاوزٌ 6 (B43–B48)، واختيارٌ بلا مرجّح 2 (B49، B50). وأسماءُ مبرهناته أسماؤها في `76fa2e6`.
- `natija_2.json`: بعد تعديل `Jisr/Abniya.lean` بقراءة المؤلّف في المواضع كلِّها (فيه «ما غُيّر بعد قراءة الحالات»)، على مادّةٍ مكشوفة: 73 من 73.
- `natija_3.json`: بعد مراجعة `murajii` الأولى (رأسُ الشفرة وتوثيقُها ورأسُ المقارنة، `2fab43e`)، بلا تغييرٍ في `jawab`: 73 من 73.
-/
import Jisr.AbniyaDawabit

namespace Jisr
namespace Abniya
namespace Qiyas

open Dabit Dawabit

/-- أعدادُ المجال بترتيبٍ ثابت: الحالات؛ ثمّ الحكمُ المتوقَّع: مقبول، خطأ، «لا حكم»، بديلان؛ ثمّ الدرجةُ المتوقَّعة لما متوقَّعُه «مقبول»:
    قياس، أولى، قليل، نقل، بلا درجة، بديلان؛ ثمّ ذواتُ الزوج؛ ثمّ الفئات: موجب، حدّ، خارج، عموم، غموض. -/
def majalAadad : List Nat :=
  let maq := halat.filter (·.hukm == [.maqbul])
  [halat.length] ++
  [Hukm.maqbul, .khata, .laHukm].map (fun d => (halat.filter (·.hukm == [d])).length) ++
  [(halat.filter (fun h => decide (2 ≤ h.hukm.length))).length] ++
  [Daraja.qiyas, .awla, .qalil, .naql, .bila].map (fun d => (maq.filter (·.daraja == [d])).length) ++
  [(maq.filter (fun h => decide (2 ≤ h.daraja.length))).length,
   (halat.filter (·.zawj.isSome)).length] ++
  [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map (fun f => (halat.filter (·.fia == f)).length)

/-- **المجال:** 50 حالة. والحكمُ المتوقَّع: مقبول 23، وخطأ 19، و«لا حكم» 6، وبديلان في 2؛ والدرجةُ فيما متوقَّعُه «مقبول»: قياس 13، وأولى 2،
    وقليل 5، ونقل 3، وبلا درجة 0، وبديلان 0؛ و38 حالةً لها زوج. والفئات: موجب 14، وحدّ 19، وخارج 6، وعموم 9، وغموض 2. -/
theorem majal : majalAadad = [50, 23, 19, 6, 2, 13, 2, 5, 3, 0, 0, 38, 14, 19, 6, 9, 2] := by
  decide +kernel

/-- **النتيجة:** 73 صوابًا من 73 حقلًا مسؤولًا (50 حكمًا و23 درجة). -/
theorem natija : ihsa (natayij halat) = ⟨73, 0, 0, 0, 0, 0, 0, 0⟩ := by
  decide +kernel

/-- **بالفئات:** موجب 28، وحدّ 19، وخارج 6، وعموم 18، وغموض 2؛ صوابٌ كلُّها. -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map (fun f => ihsa ((natayij halat).filter (·.2.1 == f))) =
      [⟨28, 0, 0, 0, 0, 0, 0, 0⟩, ⟨19, 0, 0, 0, 0, 0, 0, 0⟩, ⟨6, 0, 0, 0, 0, 0, 0, 0⟩, ⟨18, 0, 0, 0, 0, 0, 0, 0⟩,
       ⟨2, 0, 0, 0, 0, 0, 0, 0⟩] := by
  decide +kernel

/-- **لا إخفاق.** -/
theorem akhta_sifr : akhta (natayij halat) = [] := by
  decide +kernel

/-- الحقلان في الحالة صوابٌ كلاهما. -/
def sawab (i : String) : Bool :=
  (natayij halat).all fun x => !(x.1 == i || x.1 == i ++ "/daraja") || x.2.2 == Natija.sawab

/-- **الأزواج** (مدخلان يختلفان في حقلٍ واحد): تسعةَ عشرَ زوجًا، يتغيّر جوابُ المحرّك فيها كلِّها، ويصيب الطرفان معًا فيها كلِّها. -/
theorem azwaj_1 :
    (azwaj halat).length = 19 ∧ ((azwaj halat).filter (·.2.2)).length = 19 ∧
    ((azwaj halat).filter fun p => sawab p.1 && sawab p.2.1).length = 19 := by
  decide +kernel

end Qiyas
end Abniya
end Jisr
