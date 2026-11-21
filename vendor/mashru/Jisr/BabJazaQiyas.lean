/-
# باب الجزاء على ضابطه المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن.** لكلّ حالةٍ من `Dawabit.halat` (39 حالة كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والباب، وفي سياقه ما حُقن آليًّا، وجُمّدت ببصمتها في
`tahaqquq/dawabit/jaza/tajmid.json` قبل الشفرة؛ وما في سياقه في `mulhaq_1.md`): متوقَّعُ الكلام ومخرجُ `hukm` له، ثمّ متوقَّعُ الشعر
ومخرجُه حيث سأل عنه المؤلّف (`some`). و«غير_مسؤول» (`none`) لا يُعدّ.

**التصنيف** (`qarin`؛ منهجُ الضوابط §٤-هـ، `hawkama/منهج_الضوابط.md` في طلبه):
- `sawab`: المخرجُ هو المتوقَّع.
- `naqsTaghtiya`: المتوقَّعُ حكمٌ والمخرجُ «لا حكم». امتناعٌ لا يُعدّ نجاحًا.
- `tajawuz`: المتوقَّعُ «لا حكم» والمخرجُ حكم.
- `qabulKhati`: المتوقَّعُ قبيحٌ أو خطأ والمخرجُ مقبول.
- `raddKhati`: المتوقَّعُ مقبولٌ والمخرجُ قبيحٌ أو خطأ.
- `ikhtilafDaraja`: قبيحٌ مقابلَ خطأ.

**الوسم.** العدُّ «مبرهن على الشاهد» (`decide` على الحالات المجمَّدة). ومعناه موافقةُ الشفرة لقراءةٍ مستقلّةٍ للباب، لا تغطيةُ
اللغة: الحالاتُ مؤلَّفة لا عيّنةٌ من استعمال.

**التشغيلات.** المبرهناتُ هنا على الشفرة الحاليّة دائمًا. وسجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/jaza/`:
- `natija_1.json`: التشغيلُ الأوّل على الشفرة المجمَّدة في `b442a34` (بصمةُ `Jisr/BabJaza.lean` فيه
  `16af675d0a2e2050b0d0f4e434bb1f4bcdcff09682b684136185b519b5a4743d`)، قبل أيّ تعديل: 55 صوابًا من 55. وأسماءُ المبرهنات فيه
  (`majal_1`، `natija_1`، …) أسماؤها في `68911d9`.
- `natija_2.json` إلى `natija_5.json`: بعد إكمال الرأس والتعليقات وتوثيق `suraQatr`، وتصحيح مدى سندٍ في `asanid` (في الثاني)، بمراجعة
  `murajii` في أربع جولات، بلا تغييرٍ في الأحكام، على مادّةٍ مكشوفة.
ويفحص `tahaqquq/test_jaza.py`:
- أنّ بصمةَ `natija_1.json` ثابتةٌ في الاختبار نفسه.
- وأنّ كلّ سجلٍّ بعده يحمل بصمةَ ما قبله.
- وأنّ آخرَها لبصمة الشفرة الحاليّة، وأعدادُه هي أعدادُ هذه المبرهنات، وقائمةُ أسمائها فيه هي القائمةُ المتوقَّعة بعينها.
-/
import Jisr.BabJaza
import Jisr.BabJazaDawabit

namespace Jisr
namespace BabJaza
namespace Qiyas

open Dawabit

inductive Natija
  | sawab | naqsTaghtiya | tajawuz | qabulKhati | raddKhati | ikhtilafDaraja
  deriving DecidableEq, Repr

def qarin (mutawaqqa bani : Daraja) : Natija :=
  if mutawaqqa = bani then .sawab
  else match mutawaqqa, bani with
    | .laHukm, _ => .tajawuz
    | _, .laHukm => .naqsTaghtiya
    | .maqbul, _ => .raddKhati
    | _, .maqbul => .qabulKhati
    | _, _ => .ikhtilafDaraja

/-- **جدولُ المقارنة كاملًا** (16 زوجًا، على الشاهد): الصوابُ على القطر وحده، والامتناعُ عن حكمٍ نقصُ تغطية، والحكمُ حيث لا حكمَ
    تجاوز. -/
theorem qarin_jadwal :
    [Daraja.maqbul, .qabih, .khata, .laHukm].flatMap (fun m => [Daraja.maqbul, .qabih, .khata, .laHukm].map (qarin m)) =
      [.sawab, .raddKhati, .raddKhati, .naqsTaghtiya,
       .qabulKhati, .sawab, .ikhtilafDaraja, .naqsTaghtiya,
       .qabulKhati, .ikhtilafDaraja, .sawab, .naqsTaghtiya,
       .tajawuz, .tajawuz, .tajawuz, .sawab] := by
  decide

/-- الحقلُ المسؤول: الكلامُ دائمًا، والشعرُ حين سأل عنه المؤلّف. -/
inductive Haql
  | kalam | shir
  deriving DecidableEq, Repr

def natayij : List (String × Fia × Haql × Natija) :=
  halat.flatMap fun h =>
    let b := hukm h.jumla
    (h.ism, h.fia, Haql.kalam, qarin h.kalam b.kalam) ::
      (match h.shir with
       | none => []
       | some x => [(h.ism, h.fia, Haql.shir, qarin x b.shir)])

structure Ihsa where
  sawab : Nat
  naqsTaghtiya : Nat
  tajawuz : Nat
  qabulKhati : Nat
  raddKhati : Nat
  ikhtilafDaraja : Nat
  deriving DecidableEq, Repr

def ihsa (l : List (String × Fia × Haql × Natija)) : Ihsa :=
  let c (n : Natija) := (l.filter (fun x => x.2.2.2 == n)).length
  ⟨c .sawab, c .naqsTaghtiya, c .tajawuz, c .qabulKhati, c .raddKhati, c .ikhtilafDaraja⟩

def ihsaFia (f : Fia) : Ihsa := ihsa (natayij.filter (fun x => x.2.1 == f))

/-- الإخفاقاتُ بأسمائها: (الحالة، الحقل، النتيجة). -/
def akhta : List (String × Haql × Natija) :=
  (natayij.filter (fun x => x.2.2.2 != .sawab)).map (fun x => (x.1, x.2.2.1, x.2.2.2))

/-! ## النتيجةُ على الشفرة الحاليّة (على الشاهد) -/

/-- **المجالُ غيرُ فارغ ولا مائلٍ إلى «لا حكم»:** 39 حالةً، و55 حقلًا مسؤولًا. ومتوقَّعُ الكلام: 16 مقبولًا، و8 قبيحًا، و9 خطأً، و6 «لا حكم».
    ومتوقَّعُ الشعر: 10 مقبولًا، و6 «لا حكم»، و23 غيرَ مسؤول. -/
theorem majal :
    halat.length = 39 ∧ natayij.length = 55 ∧
    [Daraja.maqbul, .qabih, .khata, .laHukm].map (fun d => (halat.filter (·.kalam == d)).length) = [16, 8, 9, 6] ∧
    [some Daraja.maqbul, some .qabih, some .khata, some .laHukm, none].map
      (fun d => (halat.filter (·.shir == d)).length) = [10, 0, 0, 6, 23] := by
  decide +kernel

/-- **النتيجة:** 55 صوابًا من 55، بلا نقص تغطيةٍ ولا تجاوزٍ ولا قبولٍ خاطئٍ ولا ردٍّ خاطئٍ ولا اختلافِ درجة. -/
theorem natija : ihsa natayij = ⟨55, 0, 0, 0, 0, 0⟩ := by
  decide +kernel

/-- **بالفئات:** موجب 17، حدّ 18، خارج 12، عموم 8 — كلُّها صواب. -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .umum].map ihsaFia =
      [⟨17, 0, 0, 0, 0, 0⟩, ⟨18, 0, 0, 0, 0, 0⟩, ⟨12, 0, 0, 0, 0, 0⟩, ⟨8, 0, 0, 0, 0, 0⟩] := by
  decide +kernel

/-- **ولا إخفاق.** -/
theorem akhta_sifr : akhta = [] := by
  decide +kernel

end Qiyas
end BabJaza
end Jisr
