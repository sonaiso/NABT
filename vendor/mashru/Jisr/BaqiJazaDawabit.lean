/-
# حالاتُ ضابط بقيّة أبواب الجزاء المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/jaza2/cases.json` بـ `python3 -I scripts/bina_dawabit_jaza2.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `2f8c85a66c3151c6a20450733b80716e32504d63a99523424318a79a78f9079c`.
كتبها مؤلّفٌ مستقلٌّ من المواصفة والنطاق قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/jaza2/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/jaza2/tajmid.json`. والمثالُ والسندُ في الملفّ المصدر.
-/
import Jisr.BaqiJaza

namespace Jisr
namespace BaqiJaza
namespace Dawabit

inductive Fia
  | mujib | hadd | kharij | umum | ghumud
  deriving DecidableEq, Repr

structure Hala where
  ism : String
  fia : Fia
  dakhil : Dakhil
  /-- القيمةُ وحدها، أو البديلان في الغموض. -/
  kalam : List Daraja
  /-- `none`: «غير_مسؤول». -/
  shir : Option (List Daraja)
  deriving DecidableEq, Repr

def halat : List Hala := [
  ⟨"B01", .mujib, ⟨.laShay, .ma, .mudari, .shart, .bila, .marfu, .sila⟩, [.maqbul], none⟩,
  ⟨"B02", .hadd, ⟨.laShay, .mahma, .mudari, .shart, .bila, .marfu, .sila⟩, [.khata], none⟩,
  ⟨"B03", .umum, ⟨.laShay, .ayna, .mudari, .shart, .bila, .marfu, .sila⟩, [.khata], none⟩,
  ⟨"B04", .mujib, ⟨.nasikhMashghul, .man, .mudari, .jawab, .bila, .majzum, .jaza⟩, [.maqbul], none⟩,
  ⟨"B05", .umum, ⟨.nasikhMashghul, .ayy, .mudari, .jawab, .bila, .majzum, .jaza⟩, [.maqbul], none⟩,
  ⟨"B06", .ghumud, ⟨.nasikh, .man, .mudari, .jawab, .bila, .majzum, .jaza⟩, [.maqbul, .khata], some [.maqbul]⟩,
  ⟨"B07", .hadd, ⟨.nasikh, .inn, .mudari, .jawab, .bila, .majzum, .jaza⟩, [.khata], none⟩,
  ⟨"B08", .hadd, ⟨.harfIbtida, .man, .mudari, .shart, .bila, .majzum, .jaza⟩, [.qabih], some [.maqbul]⟩,
  ⟨"B09", .hadd, ⟨.harfIbtida, .inn, .mudari, .jawab, .bila, .majzum, .jaza⟩, [.qabih], some [.maqbul]⟩,
  ⟨"B10", .umum, ⟨.harfIbtida, .ayy, .mudari, .shart, .bila, .majzum, .jaza⟩, [.qabih], some [.maqbul]⟩,
  ⟨"B11", .mujib, ⟨.harfIbtidaMafsul, .man, .mudari, .shart, .bila, .majzum, .jaza⟩, [.maqbul], none⟩,
  ⟨"B12", .mujib, ⟨.idhaMudmar, .man, .mudari, .shart, .bila, .majzum, .jaza⟩, [.maqbul], none⟩,
  ⟨"B13", .hadd, ⟨.idhaFujaiyya, .man, .mudari, .shart, .bila, .majzum, .jaza⟩, [.khata], none⟩,
  ⟨"B14", .mujib, ⟨.la, .inn, .madi, .jawab, .bila, .madi, .jaza⟩, [.maqbul], none⟩,
  ⟨"B15", .mujib, ⟨.harfIbtida, .inn, .madi, .shart, .bila, .madi, .jaza⟩, [.maqbul], none⟩,
  ⟨"B16", .hadd, ⟨.laShay, .mata, .mudari, .shart, .bila, .marfu, .sila⟩, [.khata], none⟩,
  ⟨"B17", .mujib, ⟨.harfJarr, .ayy, .mudari, .jawab, .bila, .majzum, .jaza⟩, [.maqbul], none⟩,
  ⟨"B18", .ghumud, ⟨.harfJarr, .man, .mudari, .jawab, .bila, .majzum, .jaza⟩, [.maqbul, .daif], some [.maqbul]⟩,
  ⟨"B19", .hadd, ⟨.hamza, .inn, .mudari, .jawab, .bila, .marfu, .ghayrMuallan⟩, [.qabih], none⟩,
  ⟨"B20", .umum, ⟨.hamza, .mahma, .mudari, .jawab, .bila, .majzum, .jaza⟩, [.maqbul], none⟩,
  ⟨"B21", .mujib, ⟨.mubtadaQasam, .inn, .mudari, .jawab, .bila, .manfiLaMajzum, .jaza⟩, [.maqbul], none⟩,
  ⟨"B22", .hadd, ⟨.qasam, .man, .mudari, .jawab, .bila, .majzum, .jaza⟩, [.khata], none⟩,
  ⟨"B23", .hadd, ⟨.qasam, .inn, .mudari, .jawab, .bila, .marfu, .ghayrMuallan⟩, [.qabih], none⟩,
  ⟨"B24", .ghumud, ⟨.qasam, .inn, .madi, .jawab, .bila, .marfu, .ghayrMuallan⟩, [.khata, .maqbul], none⟩,
  ⟨"B25", .mujib, ⟨.laShay, .inn, .mudari, .baynMajzumayn, .bila, .marfu, .hal⟩, [.maqbul], none⟩,
  ⟨"B26", .mujib, ⟨.laShay, .inn, .mudari, .baynMajzumayn, .fa, .mansub, .shirka⟩, [.maqbul], none⟩,
  ⟨"B27", .umum, ⟨.laShay, .inn, .mudari, .baynMajzumayn, .aw, .majzum, .shirka⟩, [.maqbul], none⟩,
  ⟨"B28", .hadd, ⟨.laShay, .inn, .mudari, .baynMajzumayn, .thumma, .marfu, .ibtida⟩, [.khata], none⟩,
  ⟨"B29", .hadd, ⟨.laShay, .inn, .mudari, .jawab, .fa, .mansub, .ghayrMuallan⟩, [.khata], none⟩,
  ⟨"B30", .hadd, ⟨.laShay, .inn, .mudari, .baadJawab, .waw, .mansub, .shirka⟩, [.daif], some [.maqbul]⟩,
  ⟨"B31", .mujib, ⟨.laShay, .inn, .madi, .jawab, .bila, .manfiLam, .jaza⟩, [.maqbul], none⟩,
  ⟨"B32", .hadd, ⟨.laShay, .inn, .mudari, .jawab, .bila, .manfiLam, .jaza⟩, [.qabih], none⟩,
  ⟨"B33", .ghumud, ⟨.laShay, .inn, .mudari, .baadJawab, .bila, .majzum, .ghayrMuallan⟩, [.khata, .daif], none⟩,
  ⟨"B34", .ghumud, ⟨.laShay, .talabNahy, .laYantabiq, .jawabTalab, .bila, .majzum, .jaza⟩, [.maqbul, .qabih], none⟩,
  ⟨"B35", .mujib, ⟨.laShay, .talabNahy, .laYantabiq, .jawabTalab, .fa, .mansub, .ghayrMuallan⟩, [.maqbul], none⟩,
  ⟨"B36", .ghumud, ⟨.laShay, .talabAmr, .laYantabiq, .jawabTalab, .bila, .marfu, .hal⟩, [.maqbul, .daif], some [.maqbul]⟩,
  ⟨"B37", .kharij, ⟨.laShay, .talabArd, .laYantabiq, .jawabTalab, .bila, .marfu, .ibtida⟩, [.laHukm], none⟩,
  ⟨"B38", .umum, ⟨.laShay, .manaAmr, .laYantabiq, .jawabTalab, .bila, .majzum, .jaza⟩, [.maqbul], none⟩,
  ⟨"B39", .mujib, ⟨.laShay, .amma, .laYantabiq, .jawab, .bila, .marfu, .ghayrMuallan⟩, [.maqbul], none⟩,
  ⟨"B40", .hadd, ⟨.laShay, .khabarWajib, .laYantabiq, .jawabTalab, .bila, .manfiLaMajzum, .jaza⟩, [.khata], some [.maqbul]⟩,
  ⟨"B41", .kharij, ⟨.laShay, .kullama, .madi, .jawab, .bila, .madi, .ghayrMuallan⟩, [.laHukm], none⟩,
  ⟨"B42", .kharij, ⟨.laShay, .alladhi, .mudari, .jawab, .bila, .majzum, .jaza⟩, [.laHukm], none⟩,
  ⟨"B43", .kharij, ⟨.laShay, .amma, .laYantabiq, .jawab, .fa, .marfu, .ibtida⟩, [.laHukm], none⟩,
  ⟨"B44", .kharij, ⟨.laShay, .manaAmr, .laYantabiq, .jawabTalab, .fa, .mansub, .ghayrMuallan⟩, [.laHukm], none⟩]

end Dawabit
end BaqiJaza
end Jisr
