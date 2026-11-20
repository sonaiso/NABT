/-
# نفيُ الفعل وحروفُ الفعل على ضابطه المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن.** لكلّ حالةٍ من `Dawabit.halatNafy` و`Dawabit.halatWali` (كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والنطاق، وفي سياقه ما حُقن آليًّا — `taalif.md` —، وجُمّدت ببصمتها في
`tahaqquq/dawabit/nafy/tajmid.json` قبل الشفرة):
- **النوعُ الأوّل** (`نفي`): قائمةُ الصور المتوقَّعة ومخرجُ `jawab`، **مجموعتين**: التساوي صواب؛ و«لا حكم» حيث المتوقَّع قائمةٌ نقصُ
  تغطية؛ وقائمةٌ حيث المتوقَّع «لا حكم» تجاوز؛ وبعضُ البديلين في `غموض` اختيارٌ بلا مرجّح (`ikhtiyar`)؛ وما سوى ذلك خطأ (`khata`).
- **النوعُ الثاني** (`ولي`): متوقَّعُ الكلام ومخرجُ `hukmWali` له، ثمّ متوقَّعُ الشعر ومخرجُه حيث سأل عنه المؤلّف (`some`). و«غير_مسؤول»
  (`none`) لا يُعدّ. والدرجتان كما في ضابط باب الجزاء، و`marjuh` مقبولٌ في القبول والردّ (`qarinDaraja`)؛ والمتوقَّعُ بديلين (`غموض`):
  مخرجٌ منهما اختيارٌ بلا مرجّح.

**الوسم.** العدُّ «مبرهن على الشاهد» (`decide` على الحالات المجمَّدة). ومعناه موافقةُ الشفرة لقراءةٍ مستقلّةٍ للنطاق، لا تغطيةُ اللغة:
الحالاتُ مؤلَّفة لا عيّنةٌ من استعمال.

**التشغيلات.** المبرهناتُ هنا على الشفرة الحاليّة دائمًا. وسجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/nafy/` (`natija_1.json` …)، ويفحص
`tahaqquq/test_nafy.py` أنّ بصمةَ الأوّل ثابتةٌ فيه، وأنّ كلّ سجلٍّ بعده يحمل بصمةَ ما قبله، وأنّ آخرَها لبصمة الشفرة الحاليّة وأعدادُه هي
أعدادُ هذه المبرهنات.
- `natija_1.json`: التشغيلُ الأوّل على الشفرة المجمَّدة في `e7ac675`: 32 صوابًا من 33، ونقصُ تغطيةٍ في N20 («رب يقول»). وأسماءُ مبرهناته
  أسماؤها في `5cb531f`.
- `natija_2.json`: بعد إضافة `bilaMa` (س9764) إلى `Jisr/NafyFil.lean`، على مادّةٍ مكشوفة: 33 من 33.
- `natija_3.json`: بعد مراجعة `murajii` (الرأسُ وشاهدان، بلا تغييرٍ في الأحكام)، على مادّةٍ مكشوفة: 33 من 33.
-/
import Jisr.NafyFil
import Jisr.NafyFilDawabit

namespace Jisr
namespace NafyFil
namespace Qiyas

open Dawabit

inductive Natija
  | sawab | naqsTaghtiya | tajawuz | ikhtiyar | khata | qabulKhati | raddKhati | ikhtilafDaraja
  deriving DecidableEq, Repr

/-! ## النوع الأوّل: مجموعتان -/

def sawaMajmua (a b : List String) : Bool := a.all (b.contains ·) && b.all (a.contains ·)

def qarinSuwar (f : Fia) (m b : Option (List String)) : Natija :=
  match m, b with
  | none, none => .sawab
  | none, some _ => .tajawuz
  | some _, none => .naqsTaghtiya
  | some x, some y =>
    if sawaMajmua x y then .sawab
    else if f = .ghumud && y.all (x.contains ·) then .ikhtiyar
    else .khata

/-! ## النوع الثاني: درجات -/

def maqbulan : Daraja → Bool
  | .maqbul | .marjuh => true
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

def qarinWali (m : List Daraja) (b : Daraja) : Natija :=
  match m with
  | [x] => qarinDaraja x b
  | _ => if m.contains b then .ikhtiyar else if b = .laHukm then .naqsTaghtiya else .khata

/-! ## النتائج -/

inductive Haql
  | suwar | kalam | shir
  deriving DecidableEq, Repr

def natayij : List (String × Fia × Haql × Natija) :=
  halatNafy.map (fun h => (h.ism, h.fia, Haql.suwar, qarinSuwar h.fia h.suwar (jawab h.sual))) ++
  halatWali.flatMap (fun h =>
    let b := hukmWali h.harf h.yali
    (h.ism, h.fia, Haql.kalam, qarinWali h.kalam b.kalam) ::
      (match h.shir with
       | none => []
       | some x => [(h.ism, h.fia, Haql.shir, qarinWali x b.shir)]))

structure Ihsa where
  sawab : Nat
  naqsTaghtiya : Nat
  tajawuz : Nat
  ikhtiyar : Nat
  khata : Nat
  qabulKhati : Nat
  raddKhati : Nat
  ikhtilafDaraja : Nat
  deriving DecidableEq, Repr

def ihsa (l : List (String × Fia × Haql × Natija)) : Ihsa :=
  let c (n : Natija) := (l.filter (fun x => x.2.2.2 == n)).length
  ⟨c .sawab, c .naqsTaghtiya, c .tajawuz, c .ikhtiyar, c .khata, c .qabulKhati, c .raddKhati, c .ikhtilafDaraja⟩

def ihsaFia (f : Fia) : Ihsa := ihsa (natayij.filter (fun x => x.2.1 == f))

/-- الإخفاقاتُ بأسمائها: (الحالة، الحقل، النتيجة). -/
def akhta : List (String × Haql × Natija) :=
  (natayij.filter (fun x => x.2.2.2 != .sawab)).map (fun x => (x.1, x.2.2.1, x.2.2.2))

/-! ## جدولا المقارنة (على الشاهد) -/

/-- **جدولُ الدرجات كاملًا** (25 زوجًا): الصوابُ على القطر وحده، والامتناعُ عن حكمٍ نقصُ تغطية، والحكمُ حيث لا حكمَ تجاوز، والمرجوحُ
    مقبولٌ في القبول والردّ. -/
theorem qarin_jadwal :
    [Daraja.maqbul, .marjuh, .qabih, .khata, .laHukm].flatMap
      (fun m => [Daraja.maqbul, .marjuh, .qabih, .khata, .laHukm].map (qarinDaraja m)) =
      [.sawab, .ikhtilafDaraja, .raddKhati, .raddKhati, .naqsTaghtiya,
       .ikhtilafDaraja, .sawab, .raddKhati, .raddKhati, .naqsTaghtiya,
       .qabulKhati, .qabulKhati, .sawab, .ikhtilafDaraja, .naqsTaghtiya,
       .qabulKhati, .qabulKhati, .ikhtilafDaraja, .sawab, .naqsTaghtiya,
       .tajawuz, .tajawuz, .tajawuz, .tajawuz, .sawab] := by
  decide

/-- **المجموعتان** (على الشاهد): الترتيبُ لا يهمّ، والبعضُ في الغموض اختيار، وفي غيره خطأ. -/
theorem qarin_suwar :
    qarinSuwar .mujib (some ["أ", "ب"]) (some ["ب", "أ"]) = .sawab ∧
    qarinSuwar .ghumud (some ["أ", "ب"]) (some ["أ"]) = .ikhtiyar ∧
    qarinSuwar .mujib (some ["أ", "ب"]) (some ["أ"]) = .khata ∧
    qarinSuwar .mujib (some ["أ"]) none = .naqsTaghtiya ∧
    qarinSuwar .kharij none (some ["أ"]) = .tajawuz := by
  decide

/-! ## النتيجةُ على الشفرة الحاليّة (على الشاهد) -/

/-- أعدادُ المجال بترتيبٍ ثابت (يحسبها `tahaqquq/test_nafy.py` من `cases.json` بالترتيب نفسه): حالاتُ النوعين والحقولُ المسؤولة؛ ثمّ
    متوقَّعُ الصور: «لا حكم»، وصورةٌ واحدة، وصورتان فأكثر؛ ثمّ متوقَّعُ الكلام في الثاني: مقبول، مرجوح، قبيح، خطأ، «لا حكم»، بديلان؛ ثمّ
    متوقَّعُ الشعر: مقبول، مرجوح، قبيح، خطأ، «لا حكم»، غيرُ مسؤول. -/
def majalAadad : List Nat :=
  [halatNafy.length, halatWali.length, natayij.length,
   (halatNafy.filter (·.suwar = none)).length,
   (halatNafy.filter (fun h => h.suwar.map List.length = some 1)).length,
   (halatNafy.filter (fun h => decide (2 ≤ (h.suwar.map List.length).getD 0))).length] ++
  [Daraja.maqbul, .marjuh, .qabih, .khata, .laHukm].map (fun d => (halatWali.filter (·.kalam = [d])).length) ++
  [(halatWali.filter (fun h => decide (2 ≤ h.kalam.length))).length] ++
  [some [Daraja.maqbul], some [.marjuh], some [.qabih], some [.khata], some [.laHukm], none].map
    (fun d => (halatWali.filter (·.shir = d)).length)

/-- **المجالُ غيرُ فارغ ولا مائلٍ إلى «لا حكم»:** 16 حالةً من النوع الأوّل و14 من الثاني، و33 حقلًا مسؤولًا. ومتوقَّعُ الصور: «لا حكم» 2، وصورةٌ واحدة
    11، وصورتان فأكثر 3. ومتوقَّعُ الكلام في الثاني: مقبول 3، ومرجوح 1، وقبيح 0، وخطأ 7، و«لا حكم» 3، وبديلان 0. ومتوقَّعُ الشعر: مقبول 3،
    وغيرُ مسؤول 11. -/
theorem majal : majalAadad = [16, 14, 33, 2, 11, 3, 3, 1, 0, 7, 3, 0, 3, 0, 0, 0, 0, 11] := by
  decide +kernel

/-- **النتيجة:** 33 صوابًا من 33 (على الشفرة الحاليّة ومادّةٍ مكشوفة؛ والأوّلُ 32/33 في `natija_1.json`). -/
theorem natija : ihsa natayij = ⟨33, 0, 0, 0, 0, 0, 0, 0⟩ := by
  decide +kernel

/-- **بالفئات:** موجب 15، حدّ 8، خارج 5، عموم 3، غموض 2 — كلُّها صواب. -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map ihsaFia =
      [⟨15, 0, 0, 0, 0, 0, 0, 0⟩, ⟨8, 0, 0, 0, 0, 0, 0, 0⟩, ⟨5, 0, 0, 0, 0, 0, 0, 0⟩, ⟨3, 0, 0, 0, 0, 0, 0, 0⟩,
       ⟨2, 0, 0, 0, 0, 0, 0, 0⟩] := by
  decide +kernel

/-- **ولا إخفاق.** وفي التشغيل الأوّل N20 («رب يقول»)، الكلام، نقصُ تغطية (`natija_1.json`). -/
theorem akhta_sifr : akhta = [] := by
  decide +kernel

end Qiyas
end NafyFil
end Jisr
