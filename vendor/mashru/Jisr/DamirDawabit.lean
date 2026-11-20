/-
# حالاتُ ضابط الضمير المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/damir/cases.json` بـ `python3 -I scripts/bina_dawabit_damir.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `0361a0902203599f60d41f0072b476398e5b611910b6c6a2ae97eb1ac336d926`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والمصدرين قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/damir/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/damir/tajmid.json`. والمثالُ والسندُ في الملفّ المصدر.
-/
import Jisr.DamirDabit

namespace Jisr
namespace Damir
namespace Dawabit

open Dabit

def halat : List Hala := [
  ⟨"D01", .mujib, ⟨.filWahid, .yali, none, .mukhatab, .muttasil, false⟩, [.maqbul], [.bila], some "D02"⟩,
  ⟨"D02", .hadd, ⟨.filWahid, .yali, none, .mukhatab, .munfasil, false⟩, [.khata], [.bila], some "D01"⟩,
  ⟨"D03", .mujib, ⟨.ism, .yali, none, .ghaib, .muttasil, false⟩, [.maqbul], [.bila], some "D04"⟩,
  ⟨"D04", .hadd, ⟨.ism, .yali, none, .ghaib, .munfasil, false⟩, [.khata], [.bila], some "D03"⟩,
  ⟨"D05", .mujib, ⟨.ism, .yali, none, .mutakallim, .muttasil, false⟩, [.maqbul], [.bila], some "D06"⟩,
  ⟨"D06", .hadd, ⟨.ism, .yali, none, .mutakallim, .munfasil, false⟩, [.khata], [.bila], some "D05"⟩,
  ⟨"D07", .mujib, ⟨.filWahid, .yali, none, .mukhatab, .muttasil, true⟩, [.maqbul], [.bila], some "D08"⟩,
  ⟨"D08", .hadd, ⟨.filWahid, .yali, none, .mukhatab, .munfasil, true⟩, [.khata], [.bila], some "D07"⟩,
  ⟨"D09", .mujib, ⟨.ism, .yali, none, .ghaib, .muttasil, true⟩, [.maqbul], [.bila], some "D10"⟩,
  ⟨"D10", .hadd, ⟨.ism, .yali, none, .ghaib, .munfasil, true⟩, [.khata], [.bila], some "D09"⟩,
  ⟨"D11", .hadd, ⟨.laAmil, .ibtida, none, .mutakallim, .muttasil, false⟩, [.khata], [.bila], some "D12"⟩,
  ⟨"D12", .kharij, ⟨.laAmil, .ibtida, none, .mutakallim, .munfasil, false⟩, [.laHukm], [.bila], some "D11"⟩,
  ⟨"D13", .umum, ⟨.laAmil, .ibtida, none, .ghaib, .muttasil, false⟩, [.khata], [.bila], some "D14"⟩,
  ⟨"D14", .kharij, ⟨.laAmil, .ibtida, none, .ghaib, .munfasil, false⟩, [.laHukm], [.bila], some "D13"⟩,
  ⟨"D15", .hadd, ⟨.filWahid, .badIlla, none, .mukhatab, .muttasil, false⟩, [.khata], [.bila], some "D16"⟩,
  ⟨"D16", .kharij, ⟨.filWahid, .badIlla, none, .mukhatab, .muttasil, true⟩, [.laHukm], [.bila], some "D15"⟩,
  ⟨"D17", .kharij, ⟨.filWahid, .badIlla, none, .mukhatab, .munfasil, false⟩, [.laHukm], [.bila], none⟩,
  ⟨"D18", .umum, ⟨.kana, .badIlla, none, .mukhatab, .muttasil, false⟩, [.khata], [.bila], some "D19"⟩,
  ⟨"D19", .kharij, ⟨.kana, .badIlla, none, .mukhatab, .muttasil, true⟩, [.laHukm], [.bila], some "D18"⟩,
  ⟨"D20", .umum, ⟨.zann, .badIlla, none, .ghaib, .muttasil, false⟩, [.khata], [.bila], none⟩,
  ⟨"D21", .umum, ⟨.filIthnayn, .badIlla, none, .ghaib, .muttasil, false⟩, [.khata], [.bila], none⟩,
  ⟨"D22", .mujib, ⟨.filIthnayn, .yali, some .ghaib, .ghaib, .muttasil, false⟩, [.maqbul], [.marjuh], some "D23"⟩,
  ⟨"D23", .mujib, ⟨.filIthnayn, .yali, some .ghaib, .ghaib, .munfasil, false⟩, [.maqbul], [.rajih], some "D22"⟩,
  ⟨"D24", .mujib, ⟨.filIthnayn, .yali, some .ghaib, .ghaib, .muttasil, true⟩, [.maqbul], [.marjuh], some "D25"⟩,
  ⟨"D25", .mujib, ⟨.filIthnayn, .yali, some .ghaib, .ghaib, .munfasil, true⟩, [.maqbul], [.rajih], some "D24"⟩,
  ⟨"D26", .hadd, ⟨.filIthnayn, .yali, some .mukhatab, .mukhatab, .muttasil, false⟩, [.khata], [.bila], some "D27"⟩,
  ⟨"D27", .mujib, ⟨.filIthnayn, .yali, some .mukhatab, .mukhatab, .munfasil, false⟩, [.maqbul], [.bila], some "D26"⟩,
  ⟨"D28", .hadd, ⟨.filIthnayn, .yali, some .mutakallim, .mutakallim, .muttasil, false⟩, [.khata], [.bila], some "D29"⟩,
  ⟨"D29", .mujib, ⟨.filIthnayn, .yali, some .mutakallim, .mutakallim, .munfasil, false⟩, [.maqbul], [.bila], some "D28"⟩,
  ⟨"D30", .hadd, ⟨.filIthnayn, .yali, some .mukhatab, .mukhatab, .muttasil, true⟩, [.khata], [.bila], none⟩,
  ⟨"D31", .mujib, ⟨.filIthnayn, .yali, some .ghaib, .mukhatab, .munfasil, false⟩, [.maqbul], [.sawa], some "D32"⟩,
  ⟨"D32", .kharij, ⟨.filIthnayn, .yali, some .ghaib, .mukhatab, .muttasil, false⟩, [.laHukm], [.bila], some "D31"⟩,
  ⟨"D33", .mujib, ⟨.filIthnayn, .yali, some .ghaib, .mutakallim, .munfasil, false⟩, [.maqbul], [.sawa], some "D34"⟩,
  ⟨"D34", .kharij, ⟨.filIthnayn, .yali, some .ghaib, .mutakallim, .muttasil, false⟩, [.laHukm], [.bila], some "D33"⟩,
  ⟨"D35", .ghumud, ⟨.filIthnayn, .yali, some .mutakallim, .ghaib, .muttasil, false⟩, [.maqbul], [.rajih, .sawa], some "D36"⟩,
  ⟨"D36", .ghumud, ⟨.filIthnayn, .yali, some .mutakallim, .ghaib, .munfasil, false⟩, [.maqbul], [.marjuh, .sawa], some "D35"⟩,
  ⟨"D37", .ghumud, ⟨.zann, .yali, some .mukhatab, .ghaib, .muttasil, false⟩, [.maqbul], [.rajih, .marjuh], some "D44"⟩,
  ⟨"D38", .ghumud, ⟨.zann, .yali, some .mukhatab, .ghaib, .munfasil, false⟩, [.maqbul], [.rajih, .marjuh], none⟩,
  ⟨"D39", .ghumud, ⟨.zann, .yali, some .mutakallim, .ghaib, .muttasil, false⟩, [.maqbul], [.rajih, .marjuh], none⟩,
  ⟨"D40", .ghumud, ⟨.zann, .yali, some .mutakallim, .ghaib, .munfasil, false⟩, [.maqbul], [.rajih, .marjuh], none⟩,
  ⟨"D41", .ghumud, ⟨.kana, .yali, some .mutakallim, .ghaib, .muttasil, false⟩, [.maqbul], [.rajih, .marjuh], none⟩,
  ⟨"D42", .ghumud, ⟨.kana, .yali, some .mutakallim, .ghaib, .munfasil, false⟩, [.maqbul], [.rajih, .marjuh], none⟩,
  ⟨"D43", .ghumud, ⟨.kana, .yali, some .mukhatab, .ghaib, .muttasil, false⟩, [.maqbul], [.rajih, .marjuh], none⟩,
  ⟨"D44", .umum, ⟨.zann, .yali, some .mukhatab, .mukhatab, .muttasil, false⟩, [.khata], [.bila], some "D37"⟩,
  ⟨"D45", .umum, ⟨.filWahid, .yali, some .ghaib, .ghaib, .muttasil, false⟩, [.maqbul], [.marjuh], none⟩,
  ⟨"D46", .umum, ⟨.filWahid, .yali, some .mukhatab, .mukhatab, .muttasil, false⟩, [.khata], [.bila], none⟩]

end Dawabit
end Damir
end Jisr
