/-
# الوقفُ عند سيبويه على ضابطه المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن.** لكلّ حالةٍ من `Dawabit.halat` (كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والبابين، وفي سياقه ما حُقن آليًّا — `taalif.md` —، وجُمّدت ببصمتها في
`tahaqquq/dawabit/waqf/tajmid.json` قبل الشفرة): متوقَّعُ الكلام ومخرجُ `hukm` له، ثمّ متوقَّعُ الشعر ومخرجُه حيث سأل عنه المؤلّف
(`some`). و«غير_مسؤول» (`none`) لا يُعدّ.

**التصنيف** (`qarinDaraja`): صواب؛ نقصُ تغطية (المتوقَّعُ حكمٌ والمخرجُ «لا حكم»)؛ تجاوز (العكس)؛ قبولٌ خاطئ (المتوقَّعُ خطأ والمخرجُ مقبولٌ
أو لغة)؛ ردٌّ خاطئ (العكس)؛ اختلافُ درجة (مقبولٌ مقابل لغة). والمتوقَّعُ بديلين (`غموض`): مخرجٌ منهما اختيارٌ بلا مرجّح.

**الوسم.** العدُّ «مبرهن على الشاهد» (`decide` على الحالات المجمَّدة). ومعناه موافقةُ الشفرة لقراءةٍ مستقلّةٍ للبابين، لا تغطيةُ اللغة:
الحالاتُ مؤلَّفة لا عيّنةٌ من استعمال.

**التشغيلات.** المبرهناتُ هنا على الشفرة الحاليّة دائمًا. وسجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/waqf/` (`natija_1.json` …)،
ويفحصه `tahaqquq/test_waqf.py`:
- `natija_1.json`: التشغيلُ الأوّل على الشفرة المجمَّدة في `ed25842`: 41 صوابًا من 52. وأسماءُ مبرهناته أسماؤها في `961bb5d`.
- `natija_2.json`: بعد تعديل `Dal/WaqfSibawayhi.lean` بما وُسم فيه «بعد قراءة الحالات»، على مادّةٍ مكشوفة: 49 من 52.
- `natija_3.json`: بعد مراجعة `murajii` (تعميمُ قاعدة المنوَّن نصبًا، وقصرُ حذف الياء والشعرِ على الحركة، والرأس)، على مادّةٍ مكشوفة: 49 من 52،
  ولم تتغيّر نتيجةُ حالة.
- `natija_4.json`: بعد المراجعة الثانية (كلُّ وجهٍ ممكنٍ بلا ألفٍ في المنوَّن نصبًا خطأ، وما لا يمكن «لا حكم»: `mumkin`)، على مادّةٍ مكشوفة:
  49 من 52، ولم تتغيّر نتيجةُ حالة.
- `natija_5.json`: بعد المراجعة الثالثة (رأسُ الشفرة ووصفُ `mumkin_shawahid`)، على مادّةٍ مكشوفة: 49 من 52.
- `natija_6.json`: بعد المراجعة الرابعة (رأسُ الشفرة)، على مادّةٍ مكشوفة: 49 من 52.
-/
import Dal.WaqfSibawayhi
import Dal.WaqfSibawayhiDawabit

namespace Dal
namespace WaqfSibawayhi
namespace Qiyas

open Dawabit

inductive Natija
  | sawab | naqsTaghtiya | tajawuz | qabulKhati | raddKhati | ikhtilafDaraja | ikhtiyar | khata
  deriving DecidableEq, Repr

def maqbulan : Daraja → Bool
  | .maqbul | .lugha => true
  | _ => false

def qarinDaraja (m b : Daraja) : Natija :=
  if m = b then .sawab
  else match m, b with
    | .laHukm, _ => .tajawuz
    | _, .laHukm => .naqsTaghtiya
    | _, _ =>
      if maqbulan m && !maqbulan b then .raddKhati
      else if !maqbulan m && maqbulan b then .qabulKhati
      else .ikhtilafDaraja

def qarin (m : List Daraja) (b : Daraja) : Natija :=
  match m with
  | [x] => qarinDaraja x b
  | _ => if m.contains b then .ikhtiyar else if b = .laHukm then .naqsTaghtiya else .khata

inductive Haql
  | kalam | shir
  deriving DecidableEq, Repr

def natayij : List (String × Fia × Haql × Natija) :=
  halat.flatMap fun h =>
    let b := hukm h.kalima
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
  ikhtiyar : Nat
  khata : Nat
  deriving DecidableEq, Repr

def ihsa (l : List (String × Fia × Haql × Natija)) : Ihsa :=
  let c (n : Natija) := (l.filter (fun x => x.2.2.2 == n)).length
  ⟨c .sawab, c .naqsTaghtiya, c .tajawuz, c .qabulKhati, c .raddKhati, c .ikhtilafDaraja, c .ikhtiyar, c .khata⟩

def ihsaFia (f : Fia) : Ihsa := ihsa (natayij.filter (fun x => x.2.1 == f))

/-- الإخفاقاتُ بأسمائها: (الحالة، الحقل، النتيجة). -/
def akhta : List (String × Haql × Natija) :=
  (natayij.filter (fun x => x.2.2.2 != .sawab)).map (fun x => (x.1, x.2.2.1, x.2.2.2))

/-! ## جدولُ المقارنة (على الشاهد) -/

/-- **جدولُ الدرجات كاملًا** (16 زوجًا). -/
theorem qarin_jadwal :
    [Daraja.maqbul, .lugha, .khata, .laHukm].flatMap (fun m => [Daraja.maqbul, .lugha, .khata, .laHukm].map (qarinDaraja m)) =
      [.sawab, .ikhtilafDaraja, .raddKhati, .naqsTaghtiya,
       .ikhtilafDaraja, .sawab, .raddKhati, .naqsTaghtiya,
       .qabulKhati, .qabulKhati, .sawab, .naqsTaghtiya,
       .tajawuz, .tajawuz, .tajawuz, .sawab] := by
  decide

/-! ## النتيجةُ على الشفرة الحاليّة (على الشاهد) -/

/-- أعدادُ المجال بترتيبٍ ثابت (يحسبها `tahaqquq/test_waqf.py` من `cases.json` بالترتيب نفسه): الحالاتُ والحقولُ المسؤولة؛ ثمّ متوقَّعُ
    الكلام: مقبول، لغة، خطأ، «لا حكم»، بديلان؛ ثمّ متوقَّعُ الشعر: مقبول، لغة، خطأ، «لا حكم»، بديلان، غيرُ مسؤول. -/
def majalAadad : List Nat :=
  [halat.length, natayij.length] ++
  [Daraja.maqbul, .lugha, .khata, .laHukm].map (fun d => (halat.filter (·.kalam = [d])).length) ++
  [(halat.filter (fun h => decide (2 ≤ h.kalam.length))).length] ++
  [Daraja.maqbul, .lugha, .khata, .laHukm].map (fun d => (halat.filter (·.shir = some [d])).length) ++
  [(halat.filter (fun h => decide (2 ≤ (h.shir.map List.length).getD 0))).length,
   (halat.filter (·.shir = none)).length]

/-- **المجالُ غيرُ فارغ ولا مائلٍ إلى «لا حكم»:** 40 حالةً و52 حقلًا مسؤولًا. ومتوقَّعُ الكلام: مقبول 22، ولغة 4، وخطأ 10، و«لا حكم» 4،
    وبديلان 0. ومتوقَّعُ الشعر: مقبول 12، وغيرُ مسؤول 28 — **فالشعرُ لا يشهد إلّا للقبول**: لا حالةَ فيه تستطيع أن تعدّ قبولًا خاطئًا ولا
    تجاوزًا. -/
theorem majal : majalAadad = [40, 52, 22, 4, 10, 4, 0, 12, 0, 0, 0, 0, 28] := by
  decide +kernel

/-- **النتيجة:** 49 صوابًا من 52، وثلاثةُ نقوص تغطية (على الشفرة الحاليّة ومادّةٍ مكشوفة؛ والأوّلُ 41/52 في `natija_1.json`). -/
theorem natija : ihsa natayij = ⟨49, 3, 0, 0, 0, 0, 0, 0⟩ := by
  decide +kernel

/-- **بالفئات:** موجب 26، حدّ 8 وثلاثةُ نقوص، خارج 4، عموم 11، غموض 0. -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map ihsaFia =
      [⟨26, 0, 0, 0, 0, 0, 0, 0⟩, ⟨8, 3, 0, 0, 0, 0, 0, 0⟩, ⟨4, 0, 0, 0, 0, 0, 0, 0⟩, ⟨11, 0, 0, 0, 0, 0, 0, 0⟩,
       ⟨0, 0, 0, 0, 0, 0, 0, 0⟩] := by
  decide +kernel

/-- **والإخفاقاتُ بأسمائها:** الهاءُ على تاء الجمع والتاء الملحقة، والألفُ بعد غير المنوَّن — قراءتان للمؤلّف لم تأخذهما الشفرة
    (`mulhaq_1.md`). -/
theorem akhta_2 :
    akhta = [("W26", .kalam, .naqsTaghtiya), ("W27", .kalam, .naqsTaghtiya), ("W29", .kalam, .naqsTaghtiya)] := by
  decide +kernel

end Qiyas
end WaqfSibawayhi
end Dal
