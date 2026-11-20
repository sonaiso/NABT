/-
# صكُّ الجملة على ضابطه المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن.** لكلّ حالةٍ من `Dawabit.halatQ` و`Dawabit.halatS` و`Dawabit.halatM` (كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والنطاق،
وفي سياقه ما حُقن آليًّا — `taalif.md` —، وجُمّدت ببصمتها في `tahaqquq/dawabit/sakk/tajmid.json` قبل الشفرة) حقولُها المسؤولة:
- **القوّة:** `awwal` بمخرج `awwal`، و`thani` بمخرج `thani`.
- **السبب:** `sabab` بمخرج `sabab`.
- **المرجع:** `marji` بمخرج `marji`.

والمقارنةُ قائمتين **مجموعتين** (`qarin`)، على المواصفة:
- التساوي صواب.
- و«لا حكم» حيث المتوقَّعُ حكمٌ نقصُ تغطية (`naqsTaghtiya`).
- وحكمٌ حيث المتوقَّعُ «لا حكم» تجاوز (`tajawuz`).
- وفي `غموض`: بعضُ البديلين اختيارٌ بلا مرجّح (`ikhtiyar`).
- وما سوى ذلك خطأ (`khata`)، ومنه مخرجٌ ذو بديلين حيث المتوقَّعُ أحدُهما.

**الوسم.** العدُّ «مبرهن على الشاهد» (`decide` على الحالات المجمَّدة). ومعناه موافقةُ الشفرة لقراءةٍ مستقلّةٍ للنطاق، لا تغطيةُ اللغة:
الحالاتُ مؤلَّفة لا عيّنةٌ من استعمال.

**التشغيلات.** المبرهناتُ هنا على الشفرة الحاليّة دائمًا. وسجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/sakk/` (`natija_1.json` …)، ويفحص
`tahaqquq/test_sakk.py` أنّ بصمةَ الأوّل ثابتةٌ فيه، وأنّ كلّ سجلٍّ بعده يحمل بصمةَ ما قبله، وأنّ آخرَها لبصمة الشفرة الحاليّة وأعدادُه هي
أعدادُ هذه المبرهنات.
- `natija_1.json`: التشغيلُ الأوّل على الشفرة المجمَّدة في `1112732`: 48 صوابًا من 54. الإخفاقاتُ ستّة:
  - S01 (غموض، القوّةُ الأولى): اختيارٌ بلا مرجّح، فالشفرةُ تُخرج الخبرَ وحده.
  - S14 (غموض) وS24 (حدّ)، السبب: نقصُ تغطية.
  - S25 (موجب)، السبب: خطأ؛ الشفرةُ تُخرج الوجهين حيث المتوقَّعُ السببيّة.
  - S38 وS42 (خارج)، المرجع: تجاوز؛ الشفرةُ تحكم بالاحتمال في الإشارة إلى اثنين، والنطاقُ لا يحكم فيها.
- `natija_2.json`: بعد مراجعة `murajii` الثانية (رأسُ `Jisr/SakkJumla.lean` وتوثيقُه، وبرهانُ `lam_nafy_madi` بـ `decide`، وعدُّ المجال بالقيم)،
  على مادّةٍ مكشوفة، بلا تغييرٍ في دوالّ الحكم: 48 من 54، والإخفاقاتُ الستّةُ نفسُها.
- `natija_3.json`: بعد قرارَي المالك (2026-10-26)، على مادّةٍ مكشوفة: 53 من 54.
  - الإشارةُ إلى اثنين «لا حكم» حتى يُودَع لها سند (S38، S42).
  - وتعديلُ الشفرة في S14 وS24 وS25 بعد خيار المالك «عدّلها بسندٍ من النطاق» (نصُّ الخيار من البنّاء). وما قاله السجلُّ إنّه سندُها لا يصدق.
  - والباقي S01: «بعت» خبرٌ وحده في الشفرة، والمتوقَّعُ الخبرُ والإنشاء. ولم يُطلب تعديلُه.
- `natija_4.json`: بعد المراجعتين الثالثة والرابعة، بلا تغييرٍ في دوالّ الحكم: 53 من 54؛ ووسمُ التعديلات الثلاثة فيه تعيينًا واختيارًا.
- `natija_5.json`: بعد ردّ S14 وS24 وS25 إلى الشفرة المجمَّدة (المراجعة الخامسة)، على مادّةٍ مكشوفة: 50 من 54. والإخفاقاتُ الأربعةُ إخفاقاتُ
  `natija_1.json` بلا S38 وS42. وفي ملاحظته نسبةُ أسانيد إلى غير إيداعاتها، وسببٌ لردّ S14 لم تُوزن عليه نصوصُ النطاق؛ يصحّحهما `natija_6.json`.
  وفيه مدى «يريكم البرق خوفا وطمعا» س12997 والشاهدُ إلى س12998؛ يصحّحه `natija_8.json`.
- `natija_6.json`: بعد المراجعة السادسة، بلا تغييرٍ في دوالّ الحكم: 50 من 54. وفي ملاحظته قائمةٌ لنصوص النطاق تُقرأ حاصرة، و«شرطُ اتّحاد
  الفاعل» مقرَّرًا وهو في المغني خلاف (س12999–13001)، ونقلُ «تعميمٌ من شاهدَي المغني» بلا «في النطاق»؛ يصحّح `natija_7.json`
  الأوّلين، والثالثَ `natija_8.json`.
- `natija_7.json`: بعد المراجعة السابعة، بلا تغييرٍ في دوالّ الحكم: 50 من 54. ومداه للمصدر المنصوب أوسعُ منه، وجملتُه عن `natija_5.json`
  بلا خبر؛ يصحّحهما `natija_8.json`.
- `natija_8.json`: بعد المراجعة الثامنة، بلا تغييرٍ في دوالّ الحكم: 50 من 54.
-/
import Jisr.SakkJumla
import Jisr.SakkJumlaDawabit

namespace Jisr
namespace SakkJumla
namespace Qiyas

open Dawabit

inductive Natija
  | sawab | naqsTaghtiya | tajawuz | ikhtiyar | khata
  deriving DecidableEq, Repr

/-- القائمتان مجموعتين. -/
def sawa {α : Type} [DecidableEq α] (a b : List α) : Bool := a.all (b.contains ·) && b.all (a.contains ·)

/-- المتوقَّعُ `taw` والمخرجُ `makh`، و`la` قيمةُ «لا حكم» في الحقل. -/
def qarin {α : Type} [DecidableEq α] (la : α) (f : Fia) (taw makh : List α) : Natija :=
  if sawa taw makh then .sawab
  else if makh = [la] then .naqsTaghtiya
  else if taw = [la] then .tajawuz
  else if f = .ghumud && makh.all (taw.contains ·) then .ikhtiyar
  else .khata

inductive Haql
  | awwal | thani | sabab | marji
  deriving DecidableEq, Repr

def natayij : List (String × Fia × Haql × Natija) :=
  halatQ.flatMap (fun h =>
    [(h.ism, h.fia, Haql.awwal, qarin Quwwa.laHukm h.fia h.awwal [awwal h.dakhil]),
     (h.ism, h.fia, Haql.thani, qarin Quwwa.laHukm h.fia h.thani (thani h.dakhil))]) ++
  halatS.map (fun h => (h.ism, h.fia, Haql.sabab, qarin Sabab.laHukm h.fia h.sabab (sabab h.dakhil))) ++
  halatM.map (fun h => (h.ism, h.fia, Haql.marji, qarin Marji.laHukm h.fia h.marji [marji h.dakhil]))

structure Ihsa where
  sawab : Nat
  naqsTaghtiya : Nat
  tajawuz : Nat
  ikhtiyar : Nat
  khata : Nat
  deriving DecidableEq, Repr

def ihsa (l : List (String × Fia × Haql × Natija)) : Ihsa :=
  let c (n : Natija) := (l.filter (fun x => x.2.2.2 == n)).length
  ⟨c .sawab, c .naqsTaghtiya, c .tajawuz, c .ikhtiyar, c .khata⟩

def ihsaFia (f : Fia) : Ihsa := ihsa (natayij.filter (fun x => x.2.1 == f))

/-- الإخفاقاتُ بأسمائها: (الحالة، الحقل، النتيجة). -/
def akhta : List (String × Haql × Natija) :=
  (natayij.filter (fun x => x.2.2.2 != .sawab)).map (fun x => (x.1, x.2.2.1, x.2.2.2))

/-! ## المقارنة (على الشاهد) -/

/-- **المجموعتان**: الترتيبُ لا يهمّ، والبعضُ في الغموض اختيار وفي غيره خطأ، والزائدُ خطأ، والامتناعُ نقصُ تغطية، والحكمُ حيث لا حكمَ تجاوز. -/
theorem qarin_shawahid :
    qarin Sabab.laHukm .mujib [.illa, .ghayrMadhkur] [.ghayrMadhkur, .illa] = .sawab ∧
    qarin Sabab.laHukm .ghumud [.illa, .ghayrMadhkur] [.illa] = .ikhtiyar ∧
    qarin Sabab.laHukm .mujib [.illa, .ghayrMadhkur] [.illa] = .khata ∧
    qarin Sabab.laHukm .mujib [.illa] [.illa, .ghayrMadhkur] = .khata ∧
    qarin Sabab.laHukm .mujib [.illa] [.laHukm] = .naqsTaghtiya ∧
    qarin Sabab.laHukm .kharij [.laHukm] [.illa] = .tajawuz := by
  decide

/-! ## النتيجةُ على الشفرة الحاليّة (على الشاهد) -/

/-- عددُ المتوقَّع في حقلٍ بقيمه: لكلّ قيمةٍ عددُ ما متوقَّعُه هي وحدها، ثمّ عددُ ما متوقَّعُه بديلان فأكثر. -/
def aadadQiyam {α : Type} [DecidableEq α] (qiyam : List α) (l : List (List α)) : List Nat :=
  qiyam.map (fun v => (l.filter (· = [v])).length) ++ [(l.filter (fun x => decide (2 ≤ x.length))).length]

/-- أعدادُ المجال بترتيبٍ ثابت (يحسبها `tahaqquq/test_sakk.py` من `cases.json` بالترتيب نفسه): حالاتُ الأنواع الثلاثة، والحقولُ المسؤولة؛
    ثمّ لكلّ حقلٍ متوقَّعُه بقيمه، ثمّ بديلان فأكثر: `awwal` (إثبات، نفي، تعليق، إنشاء، لا حكم)، و`thani` (إثبات، نفي، تعليق، حكاية، ظنّ،
    لا ثاني، لا حكم)، و`sabab` (علّة، سببيّة، غيرُ مذكور، لا حكم)، و`marji` (معيَّن، محتمَل، لا حكم). -/
def majalAadad : List Nat :=
  [halatQ.length, halatS.length, halatM.length, natayij.length] ++
  aadadQiyam [Quwwa.ithbat, .nafy, .taliq, .insha, .laHukm] (halatQ.map (·.awwal)) ++
  aadadQiyam [Quwwa.ithbat, .nafy, .taliq, .hikaya, .zann, .laThani, .laHukm] (halatQ.map (·.thani)) ++
  aadadQiyam [Sabab.illa, .sababiyya, .ghayrMadhkur, .laHukm] (halatS.map (·.sabab)) ++
  aadadQiyam [Marji.muayyan, .muhtamal, .laHukm] (halatM.map (·.marji))

/-- **المجالُ غيرُ فارغ ولا مائلٍ إلى «لا حكم»:** 12 حالةَ قوّة، و18 سببًا، و12 مرجعًا، و54 حقلًا مسؤولًا.
    - القوّةُ الأولى: إثبات 3، نفي 2، تعليق 1، إنشاء 5، لا حكم 0، وبديلان 1.
    - والثانية: إثبات 0، نفي 0، تعليق 1، حكاية 5، ظنّ 3، لا ثاني 2، لا حكم 0، وبديلان 1.
    - والسبب: علّة 4، سببيّة 4، غيرُ مذكور 5، لا حكم 1، وبديلان 4.
    - والمرجع: معيَّن 5، محتمَل 1، لا حكم 6، وبديلان 0. -/
theorem majal : majalAadad = [12, 18, 12, 54, 3, 2, 1, 5, 0, 1, 0, 0, 1, 5, 3, 2, 0, 1, 4, 4, 5, 1, 4, 5, 1, 6, 0] := by
  decide +kernel

/-- **النتيجة:** 50 صوابًا من 54، ونقصُ تغطيةٍ 2، واختيارٌ بلا مرجّح 1، وخطأٌ 1 (على الشفرة الحاليّة ومادّةٍ مكشوفة؛ والأوّلُ 48/54 في
    `natija_1.json`). -/
theorem natija : ihsa natayij = ⟨50, 2, 0, 1, 1⟩ := by
  decide +kernel

/-- **بالفئات:** موجب 21 من 22 (خطأٌ واحد)، حدّ 8 من 9 (نقصٌ واحد)، خارج 4 من 4، عموم 11 من 11، غموض 6 من 8 (نقصٌ واختيار). -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map ihsaFia =
      [⟨21, 0, 0, 0, 1⟩, ⟨8, 1, 0, 0, 0⟩, ⟨4, 0, 0, 0, 0⟩, ⟨11, 0, 0, 0, 0⟩, ⟨6, 1, 0, 1, 0⟩] := by
  decide +kernel

/-- **الإخفاقاتُ بأسمائها:** إخفاقاتُ التشغيل الأوّل (`natija_1.json`) بلا S38 وS42. -/
theorem akhta_5 :
    akhta = [("S01", .awwal, .ikhtiyar), ("S14", .sabab, .naqsTaghtiya), ("S24", .sabab, .naqsTaghtiya),
             ("S25", .sabab, .khata)] := by
  decide +kernel

end Qiyas
end SakkJumla
end Jisr
