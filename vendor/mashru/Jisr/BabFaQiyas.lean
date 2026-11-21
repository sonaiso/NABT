/-
# باب الفاء على ضابطه المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن.** لكلّ حالةٍ من `Dawabit.halat` (كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والباب، وفي سياقه ما حُقن آليًّا — `taalif.md` —، وجُمّدت ببصمتها في
`tahaqquq/dawabit/fa/tajmid.json` قبل الشفرة): متوقَّعُ الكلام ومخرجُ `kalam`، ثمّ متوقَّعُ الشعر ومخرجُ `shir` حيث سأل عنه المؤلّف (`some`).
و«غير_مسؤول» (`none`) لا يُعدّ. والمتوقَّعُ والمخرجُ كلاهما قائمةُ درجات: واحدةٌ، أو بديلان.

**التصنيف** (`qarin`):
- `sawab`: القائمتان مجموعةٌ واحدة.
- `tajawuz`: المتوقَّعُ «لا حكم» والمخرجُ غيرُه. `naqsTaghtiya`: العكس.
- درجةٌ مقابلَ درجة (`qarinDaraja`): `qabulKhati` (المتوقَّعُ ضعيفٌ أو قبيحٌ أو خطأ والمخرجُ مقبول)، و`raddKhati` (العكس)،
  و`ikhtilafDaraja` (ضعيف/قبيح/خطأ بينها).
- `ikhtiyar`: المتوقَّعُ بديلان والمخرجُ بعضُهما. `tawaqquf`: المتوقَّعُ درجةٌ والمخرجُ بديلان هي منهما.
- `khata`: ما سوى ذلك.

**الوسم.** العدُّ «مبرهن على الشاهد» (`decide` على الحالات المجمَّدة). ومعناه موافقةُ الشفرة لقراءةٍ مستقلّةٍ للباب، لا تغطيةُ اللغة:
الحالاتُ مؤلَّفة لا عيّنةٌ من استعمال.

**التشغيلات.** المبرهناتُ هنا على الشفرة الحاليّة دائمًا. وسجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/fa/` (`natija_1.json` …)، ويفحصه
`tahaqquq/test_fa.py`:
- `natija_1.json`: التشغيلُ الأوّل على الشفرة المجمَّدة في `355c449`: 38 صوابًا من 48. وأسماءُ مبرهناته أسماؤها في `2c4fb89`.
- `natija_2.json`: بعد تعديل `Jisr/BabFa.lean` بما وُسم فيه «ما غُيّر بعد قراءة الحالات»، على مادّةٍ مكشوفة: 46 من 48. وقبله تشغيلٌ على الحالات لم
  يُسجَّل (43/48، `mulhaq_1.md`).
- `natija_3.json`: بعد مراجعة `murajii` (الرأسُ والتعليقات والأوسام، بلا تغييرٍ في الأحكام)، على مادّةٍ مكشوفة: 46 من 48.
- `natija_4.json`: بعد مراجعةٍ ثانية (رأسُ الشفرة، بلا تغييرٍ في الأحكام)، على مادّةٍ مكشوفة: 46 من 48.
- `natija_5.json`: بعد مراجعةٍ ثالثة (رأسُ الشفرة، بلا تغييرٍ في الأحكام)، على مادّةٍ مكشوفة: 46 من 48.
- `natija_6.json`: بعد مراجعةٍ رابعة (رأسُ الشفرة، بلا تغييرٍ في الأحكام)، على مادّةٍ مكشوفة: 46 من 48.
-/
import Jisr.BabFa
import Jisr.BabFaDawabit

namespace Jisr
namespace BabFa
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
    (h.ism, h.fia, Haql.kalam, qarin h.kalam (kalam h.jumla)) ::
      (match h.shir with
       | none => []
       | some x => [(h.ism, h.fia, Haql.shir, qarin x (shir h.jumla))])

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

/-- أعدادُ المجال بترتيبٍ ثابت (يحسبها `tahaqquq/test_fa.py` من `cases.json` بالترتيب نفسه): الحالاتُ والحقولُ المسؤولة؛ ثمّ متوقَّعُ الكلام:
    مقبول، ضعيف، قبيح، خطأ، «لا حكم»، بديلان؛ ثمّ متوقَّعُ الشعر: مقبول، ضعيف، قبيح، خطأ، «لا حكم»، بديلان، غيرُ مسؤول. -/
def majalAadad : List Nat :=
  [halat.length, natayij.length] ++
  [Daraja.maqbul, .daif, .qabih, .khata, .laHukm].map (fun d => (halat.filter (·.kalam = [d])).length) ++
  [(halat.filter (fun h => decide (2 ≤ h.kalam.length))).length] ++
  [Daraja.maqbul, .daif, .qabih, .khata, .laHukm].map (fun d => (halat.filter (·.shir = some [d])).length) ++
  [(halat.filter (fun h => decide (2 ≤ (h.shir.map List.length).getD 0))).length,
   (halat.filter (·.shir = none)).length]

/-- **المجالُ غيرُ فارغ ولا مائلٍ إلى «لا حكم»:** 39 حالةً و48 حقلًا مسؤولًا. ومتوقَّعُ الكلام: مقبول 20، وضعيف 2، وقبيح 0، وخطأ 6، و«لا حكم» 6،
    وبديلان 5. ومتوقَّعُ الشعر: مقبول 9، وغيرُ مسؤول 30. -/
theorem majal : majalAadad = [39, 48, 20, 2, 0, 6, 6, 5, 9, 0, 0, 0, 0, 0, 30] := by
  decide +kernel

/-- **النتيجة:** 46 صوابًا من 48: تجاوزٌ واحد واختيارٌ واحد (على الشفرة الحاليّة ومادّةٍ مكشوفة؛ والأوّلُ 38/48 في `natija_1.json`). -/
theorem natija : ihsa natayij = ⟨46, 0, 1, 0, 0, 0, 1, 0, 0⟩ := by
  decide +kernel

/-- **بالفئات:** موجب 24، حدّ 7، خارج 4 وتجاوزٌ واحد، عموم 6، غموض 5 واختيارٌ واحد. -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map ihsaFia =
      [⟨24, 0, 0, 0, 0, 0, 0, 0, 0⟩, ⟨7, 0, 0, 0, 0, 0, 0, 0, 0⟩, ⟨4, 0, 1, 0, 0, 0, 0, 0, 0⟩, ⟨6, 0, 0, 0, 0, 0, 0, 0, 0⟩,
       ⟨5, 0, 0, 0, 0, 0, 1, 0, 0⟩] := by
  decide +kernel

/-- **والإخفاقان بأسمائهما:** قراءتان للمؤلّف لم تأخذهما الشفرة (`mulhaq_1.md`). -/
theorem akhta_2 : akhta = [("F30", .kalam, .ikhtiyar), ("F38", .kalam, .tajawuz)] := by
  decide +kernel

end Qiyas
end BabFa
end Jisr
