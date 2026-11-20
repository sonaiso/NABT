/-
# حالاتُ ضابط «هذا باب الفاء» المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/fa/cases.json` بـ `python3 -I scripts/bina_dawabit_fa.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `7eda15eb08e723e7e02caf1f05e9639debce0a781ed00d2c742c898495d8a4c8`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والباب قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/fa/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/fa/tajmid.json`. والمثالُ والسندُ في الملفّ المصدر.
-/
import Jisr.BabFa

namespace Jisr
namespace BabFa
namespace Dawabit

inductive Fia
  | mujib | hadd | kharij | umum | ghumud
  deriving DecidableEq, Repr

structure Hala where
  ism : String
  fia : Fia
  jumla : Jumla
  /-- القيمةُ وحدها، أو البديلان في الغموض. -/
  kalam : List Daraja
  /-- `none`: «غير_مسؤول». -/
  shir : Option (List Daraja)
  deriving DecidableEq, Repr

def halat : List Hala := [
  ⟨"F01", .mujib, ⟨.nafyLa, .sabab, .nasb⟩, [.maqbul], none⟩,
  ⟨"F02", .mujib, ⟨.nafyMaMudari, .sabab, .nasb⟩, [.maqbul], none⟩,
  ⟨"F03", .mujib, ⟨.nafyMaMudari, .shirka, .raf⟩, [.maqbul], none⟩,
  ⟨"F04", .mujib, ⟨.nafyMaMudari, .qat, .raf⟩, [.maqbul], none⟩,
  ⟨"F05", .mujib, ⟨.nafyMaMadi, .sabab, .nasb⟩, [.maqbul], some [.maqbul]⟩,
  ⟨"F06", .mujib, ⟨.nafyMaMadi, .qat, .raf⟩, [.maqbul], none⟩,
  ⟨"F07", .mujib, ⟨.nafyIsmi, .sabab, .nasb⟩, [.maqbul], some [.maqbul]⟩,
  ⟨"F08", .mujib, ⟨.nafyIsmi, .qat, .raf⟩, [.maqbul], some [.maqbul]⟩,
  ⟨"F09", .mujib, ⟨.ard, .shirka, .raf⟩, [.maqbul], none⟩,
  ⟨"F10", .mujib, ⟨.tamanni, .sabab, .nasb⟩, [.maqbul], none⟩,
  ⟨"F11", .mujib, ⟨.nahy, .shirka, .jazm⟩, [.maqbul], none⟩,
  ⟨"F12", .mujib, ⟨.nahy, .qat, .raf⟩, [.maqbul], none⟩,
  ⟨"F13", .mujib, ⟨.amr, .sabab, .nasb⟩, [.maqbul], some [.maqbul]⟩,
  ⟨"F14", .mujib, ⟨.amr, .qat, .raf⟩, [.maqbul], none⟩,
  ⟨"F15", .mujib, ⟨.istifham, .sabab, .raf⟩, [.maqbul], none⟩,
  ⟨"F16", .mujib, ⟨.dua, .qat, .raf⟩, [.laHukm], some [.maqbul]⟩,
  ⟨"F17", .mujib, ⟨.wajib, .qat, .raf⟩, [.maqbul], none⟩,
  ⟨"F18", .mujib, ⟨.nafyLam, .sabab, .nasb⟩, [.maqbul], none⟩,
  ⟨"F19", .mujib, ⟨.tashbihNafy, .sabab, .nasb⟩, [.maqbul], none⟩,
  ⟨"F20", .hadd, ⟨.wajib, .sabab, .nasb⟩, [.daif], some [.maqbul]⟩,
  ⟨"F21", .hadd, ⟨.nafyIsmi, .shirka, .raf⟩, [.khata], none⟩,
  ⟨"F22", .hadd, ⟨.amr, .sabab, .jazm⟩, [.khata], none⟩,
  ⟨"F23", .hadd, ⟨.amr, .shirka, .jazm⟩, [.khata], none⟩,
  ⟨"F24", .hadd, ⟨.tamanni, .ghayrMuallan, .jazm⟩, [.khata], none⟩,
  ⟨"F25", .hadd, ⟨.tamanni, .qat, .raf⟩, [.khata], none⟩,
  ⟨"F26", .ghumud, ⟨.zann, .sabab, .nasb⟩, [.maqbul, .khata], none⟩,
  ⟨"F27", .ghumud, ⟨.nafyLa, .shirka, .raf⟩, [.maqbul, .qabih], none⟩,
  ⟨"F28", .ghumud, ⟨.tamanni, .shirka, .raf⟩, [.maqbul, .khata], none⟩,
  ⟨"F29", .ghumud, ⟨.nafyMaMadi, .shirka, .raf⟩, [.maqbul, .daif], none⟩,
  ⟨"F30", .ghumud, ⟨.istifham, .sabab, .nasb⟩, [.maqbul, .khata], some [.maqbul]⟩,
  ⟨"F31", .umum, ⟨.dua, .sabab, .nasb⟩, [.maqbul], some [.maqbul]⟩,
  ⟨"F32", .umum, ⟨.wajib, .ghayrMuallan, .jazm⟩, [.khata], none⟩,
  ⟨"F33", .umum, ⟨.wajib, .ghayrMuallan, .nasb⟩, [.daif], some [.maqbul]⟩,
  ⟨"F34", .umum, ⟨.nafyLam, .shirka, .jazm⟩, [.maqbul], none⟩,
  ⟨"F35", .kharij, ⟨.ard, .ghayrMuallan, .jazm⟩, [.laHukm], none⟩,
  ⟨"F36", .kharij, ⟨.nafyMaMudari, .ghayrMuallan, .jazm⟩, [.laHukm], none⟩,
  ⟨"F37", .kharij, ⟨.zann, .ghayrMuallan, .jazm⟩, [.laHukm], none⟩,
  ⟨"F38", .kharij, ⟨.ard, .qat, .raf⟩, [.laHukm], none⟩,
  ⟨"F39", .kharij, ⟨.nafyLa, .qat, .raf⟩, [.laHukm], none⟩]

end Dawabit
end BabFa
end Jisr
