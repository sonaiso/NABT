/-
# بقيّةُ أبواب الجزاء على ضابطها المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن.** لكلّ حالةٍ من `Dawabit.halat` (كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والنطاق، وفي سياقه ما حُقن آليًّا — `taalif.md` —، وجُمّدت ببصمتها في
`tahaqquq/dawabit/jaza2/tajmid.json` قبل الشفرة): متوقَّعُ الكلام ومخرجُ `(hukm _).kalam`، ثمّ متوقَّعُ الشعر ومخرجُ `(hukm _).shir` حيث
سأل عنه المؤلّف (`some`). و«غير_مسؤول» (`none`) لا يُعدّ. والمتوقَّعُ والمخرجُ كلاهما قائمةُ درجات: واحدةٌ، أو بديلان فأكثر.

**التصنيف** (`qarin`)، كما في ضابط باب الفاء:
- `sawab`: القائمتان مجموعةٌ واحدة.
- `tajawuz`: المتوقَّعُ «لا حكم» والمخرجُ غيرُه. `naqsTaghtiya`: العكس.
- درجةٌ مقابلَ درجة (`qarinDaraja`): `qabulKhati` (المتوقَّعُ ضعيفٌ أو قبيحٌ أو خطأ والمخرجُ مقبول)، و`raddKhati` (العكس)،
  و`ikhtilafDaraja` (ضعيف/قبيح/خطأ بينها).
- `ikhtiyar`: المتوقَّعُ بديلان والمخرجُ بعضُهما. `tawaqquf`: المتوقَّعُ درجةٌ والمخرجُ بدائلُ هي منها.
- `khata`: ما سوى ذلك.

**الوسم.** العدُّ «مبرهن على الشاهد» (`decide` على الحالات المجمَّدة). ومعناه موافقةُ الشفرة لقراءةٍ مستقلّةٍ للنطاق، لا تغطيةُ اللغة:
الحالاتُ مؤلَّفة لا عيّنةٌ من استعمال.

**التشغيلات.** المبرهناتُ هنا على الشفرة الحاليّة دائمًا. وسجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/jaza2/` (`natija_1.json` …).
- `natija_1.json`: التشغيلُ الأوّل على الشفرة المجمَّدة في `97b392b`: 46 صوابًا من 52. وأسماءُ مبرهناته أسماؤها في `f61d635`.
- `natija_2.json`: بعد تعديل `Jisr/BaqiJaza.lean` بما وُسم فيه «ما غُيّر بعد قراءة الحالات»، على مادّةٍ مكشوفة: 48 من 52.
- `natija_3.json`: بعد مراجعة `murajii` (الرأسُ والتعليقات، والواوُ مرفوعًا حالًا بين المجزومين بديلين)، على مادّةٍ مكشوفة: 48 من 52.
- `natija_4.json`: بعد المراجعة الثانية («لكن» بديلان، والواوُ مرفوعًا بلا معنًى معلن بديلان، والرأس)، على مادّةٍ مكشوفة: 48 من 52.
- `natija_5.json`: بعد المراجعة الثالثة (شعرُ «لكن»، و`bayn_la_raf`، والرأس)، على مادّةٍ مكشوفة: 48 من 52.
- `natija_6.json`: بعد المراجعة الرابعة (الرأس)، على مادّةٍ مكشوفة: 48 من 52.
-/
import Jisr.BaqiJaza
import Jisr.BaqiJazaDawabit

namespace Jisr
namespace BaqiJaza
namespace Qiyas

open Dawabit

inductive Natija
  | sawab | naqsTaghtiya | tajawuz | qabulKhati | raddKhati | ikhtilafDaraja | ikhtiyar | tawaqquf | khata
  deriving DecidableEq, Repr

def qarinDaraja (m b : Daraja) : Natija :=
  if m = b then .sawab
  else match m, b with
    | .laHukm, _ => .tajawuz
    | _, .laHukm => .naqsTaghtiya
    | .maqbul, _ => .raddKhati
    | _, .maqbul => .qabulKhati
    | _, _ => .ikhtilafDaraja

def sawa (a b : List Daraja) : Bool := a.all (b.contains ·) && b.all (a.contains ·)

def qarin (m b : List Daraja) : Natija :=
  if sawa m b then .sawab
  else match m, b with
    | [x], [y] => qarinDaraja x y
    | [.laHukm], _ => .tajawuz
    | _, [.laHukm] => .naqsTaghtiya
    | [x], _ => if b.contains x then .tawaqquf else .khata
    | _, _ => if b.all (m.contains ·) then .ikhtiyar else .khata

inductive Haql
  | kalam | shir
  deriving DecidableEq, Repr

def natayij : List (String × Fia × Haql × Natija) :=
  halat.flatMap fun h =>
    (h.ism, h.fia, Haql.kalam, qarin h.kalam (hukm h.dakhil).kalam) ::
      (match h.shir with
       | none => []
       | some x => [(h.ism, h.fia, Haql.shir, qarin x (hukm h.dakhil).shir)])

structure Ihsa where
  sawab : Nat
  naqsTaghtiya : Nat
  tajawuz : Nat
  qabulKhati : Nat
  raddKhati : Nat
  ikhtilafDaraja : Nat
  ikhtiyar : Nat
  tawaqquf : Nat
  khata : Nat
  deriving DecidableEq, Repr

def ihsa (l : List (String × Fia × Haql × Natija)) : Ihsa :=
  let c (n : Natija) := (l.filter (fun x => x.2.2.2 == n)).length
  ⟨c .sawab, c .naqsTaghtiya, c .tajawuz, c .qabulKhati, c .raddKhati, c .ikhtilafDaraja, c .ikhtiyar, c .tawaqquf, c .khata⟩

def ihsaFia (f : Fia) : Ihsa := ihsa (natayij.filter (fun x => x.2.1 == f))

/-- الإخفاقاتُ بأسمائها: (الحالة، الحقل، النتيجة). -/
def akhta : List (String × Haql × Natija) :=
  (natayij.filter (fun x => x.2.2.2 != .sawab)).map (fun x => (x.1, x.2.2.1, x.2.2.2))

def t (i : Ihsa) : List Nat :=
  [i.sawab, i.naqsTaghtiya, i.tajawuz, i.qabulKhati, i.raddKhati, i.ikhtilafDaraja, i.ikhtiyar, i.tawaqquf, i.khata]

/-! ## جدولُ المقارنة (على الشاهد) -/

/-- **جدولُ الدرجات كاملًا** (25 زوجًا). -/
theorem qarin_jadwal :
    [Daraja.maqbul, .daif, .qabih, .khata, .laHukm].flatMap
      (fun m => [Daraja.maqbul, .daif, .qabih, .khata, .laHukm].map (qarinDaraja m)) =
      [.sawab, .raddKhati, .raddKhati, .raddKhati, .naqsTaghtiya,
       .qabulKhati, .sawab, .ikhtilafDaraja, .ikhtilafDaraja, .naqsTaghtiya,
       .qabulKhati, .ikhtilafDaraja, .sawab, .ikhtilafDaraja, .naqsTaghtiya,
       .qabulKhati, .ikhtilafDaraja, .ikhtilafDaraja, .sawab, .naqsTaghtiya,
       .tajawuz, .tajawuz, .tajawuz, .tajawuz, .sawab] := by
  decide

/-- **البديلان** (على الشاهد): الترتيبُ لا يهمّ، والبعضُ اختيار، والبديلان حيث الدرجةُ واحدةٌ منهما توقّف. -/
theorem qarin_badil :
    qarin [.maqbul, .khata] [.khata, .maqbul] = .sawab ∧ qarin [.maqbul, .khata] [.maqbul] = .ikhtiyar ∧
    qarin [.maqbul] [.maqbul, .khata] = .tawaqquf ∧ qarin [.maqbul, .khata] [.laHukm] = .naqsTaghtiya := by
  decide

/-! ## النتيجةُ على الشفرة الحاليّة (على الشاهد) -/

/-- أعدادُ المجال بترتيبٍ ثابت (يحسبها `tahaqquq/test_jaza2.py` من `cases.json` بالترتيب نفسه): الحالاتُ والحقولُ المسؤولة؛ ثمّ متوقَّعُ
    الكلام: مقبول، ضعيف، قبيح، خطأ، «لا حكم»، بديلان؛ ثمّ متوقَّعُ الشعر: مقبول، ضعيف، قبيح، خطأ، «لا حكم»، بديلان، غيرُ مسؤول. -/
def majalAadad : List Nat :=
  [halat.length, natayij.length] ++
  [Daraja.maqbul, .daif, .qabih, .khata, .laHukm].map (fun d => (halat.filter (·.kalam = [d])).length) ++
  [(halat.filter (fun h => decide (2 ≤ h.kalam.length))).length] ++
  [Daraja.maqbul, .daif, .qabih, .khata, .laHukm].map (fun d => (halat.filter (·.shir = some [d])).length) ++
  [(halat.filter (fun h => decide (2 ≤ (h.shir.map List.length).getD 0))).length,
   (halat.filter (·.shir = none)).length]

/-- **المجالُ غيرُ فارغ ولا مائلٍ إلى «لا حكم»:** 44 حالةً و52 حقلًا مسؤولًا. ومتوقَّعُ الكلام: مقبول 17، وضعيف 1، وقبيح 6، وخطأ 9،
    و«لا حكم» 5، وبديلان 6. ومتوقَّعُ الشعر: مقبول 8، وغيرُ مسؤول 36 — **فالشعرُ لا يشهد إلّا للقبول**: لا حالةَ فيه تستطيع أن تعدّ قبولًا
    خاطئًا ولا تجاوزًا. -/
theorem majal : majalAadad = [44, 52, 17, 1, 6, 9, 5, 6, 8, 0, 0, 0, 0, 0, 36] := by
  decide +kernel

/-- **النتيجة:** 48 صوابًا من 52: اختياران، وتوقّفٌ واحد، وخطأٌ واحد (على الشفرة الحاليّة ومادّةٍ مكشوفة؛ والأوّلُ 46/52 في
    `natija_1.json`). -/
theorem natija : ihsa natayij = ⟨48, 0, 0, 0, 0, 0, 2, 1, 1⟩ := by
  decide +kernel

/-- **بالفئات:** موجب 12 وتوقّفٌ واحد، حدّ 18، خارج 5، عموم 7، غموض 6 واختياران وخطأٌ واحد. -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map ihsaFia =
      [⟨12, 0, 0, 0, 0, 0, 0, 1, 0⟩, ⟨18, 0, 0, 0, 0, 0, 0, 0, 0⟩, ⟨5, 0, 0, 0, 0, 0, 0, 0, 0⟩, ⟨7, 0, 0, 0, 0, 0, 0, 0, 0⟩,
       ⟨6, 0, 0, 0, 0, 0, 2, 0, 1⟩] := by
  decide +kernel

/-- **والإخفاقاتُ الأربعة بأسمائها:** قراءاتٌ للمؤلّف لم تأخذها الشفرة (`mulhaq_1.md`)؛ وفي B33 زادت الشفرةُ بعد قراءة الحالات «ضعيف» باتّجاه
    المؤلّف ولم تبلغ قراءته. -/
theorem akhta_2 :
    akhta = [("B06", .kalam, .ikhtiyar), ("B17", .kalam, .tawaqquf), ("B33", .kalam, .khata),
      ("B34", .kalam, .ikhtiyar)] := by
  decide +kernel

end Qiyas
end BaqiJaza
end Jisr
