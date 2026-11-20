/-
# حالاتُ ضابط «هذا باب الجزاء» المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/jaza/cases.json` بـ `python3 -I scripts/bina_dawabit_jaza.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `999ce1fd3019f211c4641b9a0e19a3df15e255764279d22bc1748c62320a22f7`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والباب قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/jaza/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/jaza/tajmid.json`. والمثالُ والسندُ في الملفّ المصدر.
-/
import Jisr.BabJaza

namespace Jisr
namespace BabJaza
namespace Dawabit

inductive Fia
  | mujib | hadd | kharij | umum
  deriving DecidableEq, Repr

structure Hala where
  ism : String
  fia : Fia
  jumla : Jumla
  kalam : Daraja
  /-- `none`: «غير_مسؤول». -/
  shir : Option Daraja
  deriving DecidableEq, Repr

def halat : List Hala := [
  ⟨"J01", .mujib, ⟨"إن", .shartAwwalan, false, .mudariMajzum, .faIsmiyya⟩, .maqbul, none⟩,
  ⟨"J02", .mujib, ⟨"إن", .shartAwwalan, false, .madi, .lamQasam⟩, .maqbul, none⟩,
  ⟨"J03", .mujib, ⟨"إن", .shartAwwalan, true, .madi, .lamQasam⟩, .maqbul, none⟩,
  ⟨"J04", .mujib, ⟨"إن", .jawabAwwalan, false, .madi, .mudariMarfu⟩, .maqbul, none⟩,
  ⟨"J05", .mujib, ⟨"إن", .shartAwwalan, false, .madi, .mudariMarfu⟩, .maqbul, some .maqbul⟩,
  ⟨"J06", .mujib, ⟨"إن", .shartAwwalan, false, .madi, .mudariMajzum⟩, .maqbul, some .maqbul⟩,
  ⟨"J07", .mujib, ⟨"إن", .shartAwwalan, false, .mudariMajzum, .faMudariMarfu⟩, .maqbul, none⟩,
  ⟨"J08", .mujib, ⟨"إن", .shartAwwalan, false, .mudariMajzum, .idhaIsmiyya⟩, .maqbul, none⟩,
  ⟨"J09", .mujib, ⟨"إذا ما", .shartAwwalan, false, .mudariMarfu, .mudariMarfu⟩, .maqbul, some .maqbul⟩,
  ⟨"J10", .mujib, ⟨"إذا", .jawabAwwalan, false, .madi, .mudariMarfu⟩, .maqbul, none⟩,
  ⟨"J11", .mujib, ⟨"حيثما", .shartAwwalan, false, .mudariMajzum, .mudariMajzum⟩, .maqbul, none⟩,
  ⟨"J12", .mujib, ⟨"إذ ما", .shartAwwalan, false, .madi, .faGhayr⟩, .maqbul, some .maqbul⟩,
  ⟨"J13", .mujib, ⟨"حيث", .shartAwwalan, false, .mudariMarfu, .mudariMarfu⟩, .maqbul, none⟩,
  ⟨"J14", .hadd, ⟨"حيث", .shartAwwalan, false, .mudariMajzum, .mudariMajzum⟩, .khata, none⟩,
  ⟨"J15", .hadd, ⟨"إذ", .shartAwwalan, false, .mudariMajzum, .mudariMajzum⟩, .khata, none⟩,
  ⟨"J16", .hadd, ⟨"إن", .shartAwwalan, false, .mudariMajzum, .mudariMarfu⟩, .qabih, some .maqbul⟩,
  ⟨"J17", .hadd, ⟨"إن", .jawabAwwalan, false, .mudariMajzum, .mudariMarfu⟩, .qabih, some .maqbul⟩,
  ⟨"J18", .hadd, ⟨"إن", .shartAwwalan, false, .mudariMajzum, .ismiyya⟩, .khata, some .maqbul⟩,
  ⟨"J19", .hadd, ⟨"من", .shartAwwalan, false, .mudariMajzum, .ismiyya⟩, .khata, some .maqbul⟩,
  ⟨"J20", .hadd, ⟨"إن", .shartAwwalan, false, .mudariMajzum, .lamQasam⟩, .qabih, none⟩,
  ⟨"J21", .hadd, ⟨"إن", .shartAwwalan, true, .mudariMajzum, .lamQasam⟩, .qabih, none⟩,
  ⟨"J22", .hadd, ⟨"إن", .shartAwwalan, false, .mudariMajzum, .waw⟩, .khata, none⟩,
  ⟨"J23", .hadd, ⟨"إن", .shartAwwalan, false, .mudariMajzum, .faIdha⟩, .qabih, none⟩,
  ⟨"J24", .hadd, ⟨"إن", .shartAwwalan, false, .mudariMajzum, .faMudariMajzum⟩, .khata, none⟩,
  ⟨"J25", .hadd, ⟨"إذا", .shartAwwalan, false, .madi, .mudariMajzum⟩, .khata, some .maqbul⟩,
  ⟨"J26", .hadd, ⟨"كيف", .shartAwwalan, false, .mudariMajzum, .mudariMajzum⟩, .qabih, none⟩,
  ⟨"J27", .kharij, ⟨"لو", .shartAwwalan, false, .madi, .madi⟩, .laHukm, some .laHukm⟩,
  ⟨"J28", .kharij, ⟨"كلما", .shartAwwalan, false, .madi, .madi⟩, .laHukm, some .laHukm⟩,
  ⟨"J29", .kharij, ⟨"أيان", .shartAwwalan, false, .mudariMajzum, .mudariMajzum⟩, .laHukm, some .laHukm⟩,
  ⟨"J30", .kharij, ⟨"ما", .shartAwwalan, false, .mudariMarfu, .mudariMarfu⟩, .laHukm, some .laHukm⟩,
  ⟨"J31", .kharij, ⟨"كيفما", .shartAwwalan, false, .mudariMajzum, .mudariMajzum⟩, .laHukm, some .laHukm⟩,
  ⟨"J32", .kharij, ⟨"حينما", .shartAwwalan, false, .mudariMajzum, .mudariMajzum⟩, .laHukm, some .laHukm⟩,
  ⟨"J33", .umum, ⟨"متى", .shartAwwalan, false, .mudariMajzum, .mudariMajzum⟩, .maqbul, none⟩,
  ⟨"J34", .umum, ⟨"أين", .shartAwwalan, false, .mudariMajzum, .faIsmiyya⟩, .maqbul, none⟩,
  ⟨"J35", .umum, ⟨"متى", .shartAwwalan, false, .mudariMajzum, .thumma⟩, .khata, none⟩,
  ⟨"J36", .umum, ⟨"من", .shartAwwalan, false, .mudariMajzum, .lamQasam⟩, .qabih, none⟩,
  ⟨"J37", .umum, ⟨"متى", .shartAwwalan, false, .mudariMajzum, .mudariMarfu⟩, .qabih, none⟩,
  ⟨"J38", .umum, ⟨"ما", .shartAwwalan, false, .mudariMajzum, .mudariMajzum⟩, .maqbul, none⟩,
  ⟨"J39", .umum, ⟨"متى", .shartAwwalan, false, .mudariMajzum, .ismiyya⟩, .khata, some .maqbul⟩]

end Dawabit
end BabJaza
end Jisr
