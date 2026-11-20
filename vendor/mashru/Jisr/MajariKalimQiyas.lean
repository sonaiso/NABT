/-
# مجاري أواخر الكلم على ضابطه المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن.** لكلّ حالةٍ من `Dawabit.halat` (كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والباب، وفي سياقه ما حُقن آليًّا — `taalif.md` —، وجُمّدت ببصمتها في
`tahaqquq/dawabit/majari/tajmid.json` قبل الشفرة): الجوابُ المتوقَّع ومخرجُ `jawab`.

**التصنيف** (`qarin`):
- `sawab`: العلاماتُ نفسُها مجموعتين، والبناءُ نفسُه؛ أو «لا يكون» مقابل «لا يكون»؛ أو «لا حكم» مقابل «لا حكم».
- `naqsTaghtiya`: المتوقَّعُ حكمٌ والمخرجُ «لا حكم». `tajawuz`: العكس.
- `qabulKhati`: المتوقَّعُ «لا يكون» والمخرجُ علامة. `raddKhati`: العكس.
- `khataBina`: العلاماتُ نفسُها والبناءُ غيرُه.
- `ikhtiyar`: بعضُ العلامتين في `غموض`، والبناءُ نفسُه.
- `khataAlama`: ما سوى ذلك.

**الوسم.** العدُّ «مبرهن على الشاهد» (`decide` على الحالات المجمَّدة). ومعناه موافقةُ الشفرة لقراءةٍ مستقلّةٍ للباب، لا تغطيةُ اللغة:
الحالاتُ مؤلَّفة لا عيّنةٌ من استعمال.

**التشغيلات.** المبرهناتُ هنا على الشفرة الحاليّة دائمًا. وسجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/majari/` (`natija_1.json` …)،
ويفحصه `tahaqquq/test_majari.py`:
- `natija_1.json`: التشغيلُ الأوّل على الشفرة المجمَّدة في `7ce1cfb`: 33 صوابًا من 39. وأسماءُ مبرهناته أسماؤها في `9629153`.
- `natija_2.json`: بعد تعديل `Jisr/MajariKalim.lean` بما وُسم فيه «وكان في الشفرة المجمَّدة»، على مادّةٍ مكشوفة: 39 من 39.
- `natija_3.json`: بعد مراجعة `murajii` (الرأسُ والتعليقات، وحذفُ لفظ «ل»، ومدُّ سندين)، على مادّةٍ مكشوفة: 39 من 39.
- `natija_4.json`: بعد المراجعة الثانية (حذفُ لفظ «اللام»، ومدُّ سند `ghayrMutamakkina`، والرأس)، على مادّةٍ مكشوفة: 39 من 39.
- `natija_5.json`: بعد المراجعة الثالثة (رأسُ الشفرة، وشطرٌ يثبّت حذفَ «اللام»)، على مادّةٍ مكشوفة: 39 من 39.
-/
import Jisr.MajariKalim
import Jisr.MajariKalimDawabit

namespace Jisr
namespace MajariKalim
namespace Qiyas

open Dawabit

inductive Natija
  | sawab | naqsTaghtiya | tajawuz | qabulKhati | raddKhati | khataBina | ikhtiyar | khataAlama
  deriving DecidableEq, Repr

def sawa (a b : List Alama) : Bool := a.all (b.contains ·) && b.all (a.contains ·)

def qarin (f : Fia) (m b : Jawab) : Natija :=
  match m, b with
  | .laHukm, .laHukm => .sawab
  | .laHukm, _ => .tajawuz
  | _, .laHukm => .naqsTaghtiya
  | .laYakun, .laYakun => .sawab
  | .laYakun, .alamat _ _ => .qabulKhati
  | .alamat _ _, .laYakun => .raddKhati
  | .alamat x bx, .alamat y bn =>
    if sawa x y then (if bx = bn then .sawab else .khataBina)
    else if f = .ghumud && y.all (x.contains ·) && bx == bn then .ikhtiyar
    else .khataAlama

def natayij : List (String × Fia × Natija) :=
  halat.map (fun h => (h.ism, h.fia, qarin h.fia h.mutawaqqa (jawab h.kalima)))

structure Ihsa where
  sawab : Nat
  naqsTaghtiya : Nat
  tajawuz : Nat
  qabulKhati : Nat
  raddKhati : Nat
  khataBina : Nat
  ikhtiyar : Nat
  khataAlama : Nat
  deriving DecidableEq, Repr

def ihsa (l : List (String × Fia × Natija)) : Ihsa :=
  let c (n : Natija) := (l.filter (fun x => x.2.2 == n)).length
  ⟨c .sawab, c .naqsTaghtiya, c .tajawuz, c .qabulKhati, c .raddKhati, c .khataBina, c .ikhtiyar, c .khataAlama⟩

def ihsaFia (f : Fia) : Ihsa := ihsa (natayij.filter (fun x => x.2.1 == f))

/-- الإخفاقاتُ بأسمائها. -/
def akhta : List (String × Natija) :=
  (natayij.filter (fun x => x.2.2 != .sawab)).map (fun x => (x.1, x.2.2))

/-! ## جدولُ المقارنة (على الشاهد) -/

/-- **الجدول:** الصوابُ على القطر، والامتناعُ نقصُ تغطية، والحكمُ حيث لا حكمَ تجاوز، والعلامةُ حيث «لا يكون» قبولٌ خاطئ، والبناءُ يفرّق،
    والبعضُ في الغموض اختيار. -/
theorem qarin_jadwal :
    qarin .mujib (.alamat [.damma, .fatha] true) (.alamat [.fatha, .damma] true) = .sawab ∧
    qarin .mujib (.alamat [.damma] false) .laHukm = .naqsTaghtiya ∧
    qarin .kharij .laHukm (.alamat [.damma] false) = .tajawuz ∧
    qarin .hadd .laYakun (.alamat [.fatha] true) = .qabulKhati ∧
    qarin .mujib (.alamat [.fatha] true) .laYakun = .raddKhati ∧
    qarin .mujib (.alamat [.fatha] true) (.alamat [.fatha] false) = .khataBina ∧
    qarin .ghumud (.alamat [.fatha, .damma] true) (.alamat [.fatha] true) = .ikhtiyar ∧
    qarin .mujib (.alamat [.fatha, .damma] true) (.alamat [.fatha] true) = .khataAlama := by
  decide

/-! ## النتيجةُ على الشفرة الحاليّة (على الشاهد) -/

/-- أعدادُ المجال بترتيبٍ ثابت (يحسبها `tahaqquq/test_majari.py` من `cases.json` بالترتيب نفسه): الحالات؛ ثمّ متوقَّعُها: علامةٌ واحدة،
    وعلامتان فأكثر، و«لا يكون»، و«لا حكم»؛ ثمّ البناءُ والإعراب. -/
def majalAadad : List Nat :=
  [halat.length,
   (halat.filter (fun h => match h.mutawaqqa with | .alamat l _ => l.length == 1 | _ => false)).length,
   (halat.filter (fun h => match h.mutawaqqa with | .alamat l _ => decide (2 ≤ l.length) | _ => false)).length,
   (halat.filter (·.mutawaqqa = .laYakun)).length,
   (halat.filter (·.mutawaqqa = .laHukm)).length,
   (halat.filter (fun h => match h.mutawaqqa with | .alamat _ b => b | _ => false)).length,
   (halat.filter (fun h => match h.mutawaqqa with | .alamat _ b => !b | _ => false)).length]

/-- **المجالُ غيرُ فارغ ولا مائلٍ إلى «لا حكم»:** 39 حالةً؛ متوقَّعُها علامةٌ واحدة 26، وعلامتان 3، و«لا يكون» 5، و«لا حكم» 5؛ والبناءُ في 11 والإعرابُ
    في 18. -/
theorem majal : majalAadad = [39, 26, 3, 5, 5, 11, 18] := by
  decide +kernel

/-- **النتيجة:** 39 صوابًا من 39 (على الشفرة الحاليّة ومادّةٍ مكشوفة؛ والأوّلُ 33/39 في `natija_1.json`). -/
theorem natija : ihsa natayij = ⟨39, 0, 0, 0, 0, 0, 0, 0⟩ := by
  decide +kernel

/-- **بالفئات:** موجب 20، حدّ 5، خارج 5، عموم 6، غموض 3 — كلُّها صواب. -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map ihsaFia =
      [⟨20, 0, 0, 0, 0, 0, 0, 0⟩, ⟨5, 0, 0, 0, 0, 0, 0, 0⟩, ⟨5, 0, 0, 0, 0, 0, 0, 0⟩, ⟨6, 0, 0, 0, 0, 0, 0, 0⟩,
       ⟨3, 0, 0, 0, 0, 0, 0, 0⟩] := by
  decide +kernel

/-- **ولا إخفاق.** وفي التشغيل الأوّل ستّةٌ بأسمائها في `natija_1.json`. -/
theorem akhta_sifr : akhta = [] := by
  decide +kernel

end Qiyas
end MajariKalim
end Jisr
