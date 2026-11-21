/-
# أسماءُ الإشارة على ضابطها المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن.** لكلّ حالةٍ من `Dawabit.halat` (كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والمصدرين، وفي سياقه ما حُقن آليًّا — `taalif.md` —،
وجُمّدت ببصمتها في `tahaqquq/dawabit/ishara/tajmid.json` قبل الشفرة): الحكمُ المتوقَّع وحكمُ `Jisr.Ishara.hukm`، بتصنيف `Dabit.qarinHukm`.

**الوسم.** العدُّ «مبرهن على الشاهد» (`decide` على الحالات المجمَّدة). ومعناه موافقةُ الشفرة لقراءةٍ مستقلّةٍ للنطاق، لا تغطيةُ اللغة:
الحالاتُ مؤلَّفة لا عيّنةٌ من استعمال.

**التشغيلات.** المبرهناتُ هنا على الشفرة الحاليّة دائمًا. وسجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/ishara/` (`natija_1.json` …)،
ويفحصه `tahaqquq/test_ishara.py`:
- `natija_1.json`: التشغيلُ الأوّل على الشفرة المجمَّدة في `0446d1e`، قبل أن يقرأ البنّاءُ الحالات: 42 صوابًا من 49؛ خمسةُ تجاوزات (I08 وI12
  وI22 وI27 وI36: «ها» مع القريب) واختياران (I48 وI49: «هنا» بلا كافٍ للبعيد). وأسماءُ مبرهناته أسماؤها في `7a9a064`.
- `natija_2.json`: بعد تعديل `Jisr/Ishara.lean` بقراءة المؤلّف في الموضعين (فيه «ما غُيّر بعد قراءة الحالات»)، على مادّةٍ مكشوفة: 49 من 49.
- `natija_3.json`: بعد تصحيحات مراجعة `murajii` («ها» مع «ثم»، لا تمسّه حالة؛ و`maqam_ishara`)، على مادّةٍ مكشوفة: 49 من 49.
- `natija_4.json`: بعد تصحيحات المراجعة الثانية في التوثيق (`4b9e2f2`)، بلا تغييرٍ في `hukm`: 49 من 49.

وفي توجيه البنّاء إلى المؤلّف (`tawjih_muallif.md`) عبارةٌ تدلّه على الضبط الذي لا يكتبه النطاق («vowelings the scope does not write … that is for
the غموض category or for «لا_حكم», as the spec says»)، وهي مادّةُ I48 وI49؛ فقراءتُه فيهما، وهي التي أُخذ بها، ليست مستقلّةً عن التوجيه.
-/
import Jisr.IsharaDawabit

namespace Jisr
namespace Ishara
namespace Qiyas

open Dabit Dawabit

/-- أعدادُ المجال بترتيبٍ ثابت (يحسبها `tahaqquq/test_ishara.py` من `cases.json` بالترتيب نفسه): الحالات؛ ثمّ الحكمُ المتوقَّع: مقبول،
    خطأ، «لا حكم»، بديلان؛ ثمّ ذواتُ الزوج؛ ثمّ الفئاتُ: موجب، حدّ، خارج، عموم، غموض. -/
def majalAadad : List Nat :=
  [halat.length] ++
  [Hukm.maqbul, .khata, .laHukm].map (fun d => (halat.filter (·.hukm == [d])).length) ++
  [(halat.filter (fun h => decide (2 ≤ h.hukm.length))).length,
   (halat.filter (·.zawj.isSome)).length] ++
  [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map (fun f => (halat.filter (·.fia == f)).length)

/-- **المجالُ غيرُ فارغ ولا مائلٍ إلى «لا حكم»:** 49 حالة. والمتوقَّع: مقبول 27، وخطأ 15، و«لا حكم» 5، وبديلان في 2؛ و30 حالةً لها زوج.
    والفئات: موجب 19، وحدّ 12، وخارج 5، وعموم 11، وغموض 2. -/
theorem majal : majalAadad = [49, 27, 15, 5, 2, 30, 19, 12, 5, 11, 2] := by
  decide +kernel

/-- **النتيجة:** 49 صوابًا من 49 (على الشفرة الحاليّة ومادّةٍ مكشوفة؛ والأوّلُ 42/49 في `natija_1.json`). -/
theorem natija : ihsa (natayij halat) = ⟨49, 0, 0, 0, 0, 0, 0⟩ := by
  decide +kernel

/-- **بالفئات:** موجب 19، وحدّ 12، وخارج 5، وعموم 11، وغموض 2 — كلُّها صواب. -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map (fun f => ihsa ((natayij halat).filter (·.2.1 == f))) =
      [⟨19, 0, 0, 0, 0, 0, 0⟩, ⟨12, 0, 0, 0, 0, 0, 0⟩, ⟨5, 0, 0, 0, 0, 0, 0⟩, ⟨11, 0, 0, 0, 0, 0, 0⟩, ⟨2, 0, 0, 0, 0, 0, 0⟩] := by
  decide +kernel

/-- **ولا إخفاق.** وفي التشغيل الأوّل سبعةٌ بأسمائها في `natija_1.json`. -/
theorem akhta_sifr : akhta (natayij halat) = [] := by
  decide +kernel

/-- الحكمُ في الحالة صواب. -/
def sawab (i : String) : Bool := (natayij halat).any fun x => x.1 == i && x.2.2 == Natija.sawab

/-- **الأزواج** (مدخلان يختلفان في حقلٍ واحد): خمسةَ عشرَ زوجًا، يتغيّر حكمُ المحرّك فيها كلِّها، ويصيب الطرفان معًا فيها كلِّها. وفي
    التشغيل الأوّل لم يتغيّر في I01/I08 وI25/I27، وأصاب الطرفان في اثني عشر (`natija_1.json`). -/
theorem azwaj_1 :
    (azwaj halat).length = 15 ∧ ((azwaj halat).filter (·.2.2)).length = 15 ∧
    ((azwaj halat).filter fun p => sawab p.1 && sawab p.2.1).length = 15 := by
  decide +kernel

end Qiyas
end Ishara
end Jisr
