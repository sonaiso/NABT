/-
# حالاتُ ضابط «هذا باب مجارى أواخر الكلم من العربية» المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/majari/cases.json` بـ `python3 -I scripts/bina_dawabit_majari.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `0d53e2c218d12c8ea1780ef573255576907d09a08fc4166e415d06a67a822c20`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والباب قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/majari/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/majari/tajmid.json`. والمثالُ والسندُ في الملفّ المصدر.
-/
import Jisr.MajariKalim

namespace Jisr
namespace MajariKalim
namespace Dawabit

inductive Fia
  | mujib | hadd | kharij | umum | ghumud
  deriving DecidableEq, Repr

structure Hala where
  ism : String
  fia : Fia
  kalima : Kalima
  mutawaqqa : Jawab
  deriving DecidableEq, Repr

def halat : List Hala := [
  ⟨"M01", .mujib, ⟨.ismMutamakkin, "", .nasb⟩, .alamat [.fatha] false⟩,
  ⟨"M02", .mujib, ⟨.ismMutamakkin, "", .raf⟩, .alamat [.damma] false⟩,
  ⟨"M03", .mujib, ⟨.mudari, "", .nasb⟩, .alamat [.fatha] false⟩,
  ⟨"M04", .mujib, ⟨.mudari, "", .raf⟩, .alamat [.damma] false⟩,
  ⟨"M05", .mujib, ⟨.mudari, "", .jazm⟩, .alamat [.sukun] false⟩,
  ⟨"M06", .mujib, ⟨.muthanna, "", .raf⟩, .alamat [.alif] false⟩,
  ⟨"M07", .mujib, ⟨.muthanna, "", .nasb⟩, .alamat [.ya] false⟩,
  ⟨"M08", .mujib, ⟨.jamMudhakkar, "", .raf⟩, .alamat [.waw] false⟩,
  ⟨"M09", .mujib, ⟨.jamMuannath, "", .nasb⟩, .alamat [.kasra] false⟩,
  ⟨"M10", .mujib, ⟨.mudariIthnayn, "", .raf⟩, .alamat [.thubutNun] false⟩,
  ⟨"M11", .mujib, ⟨.mudariIthnayn, "", .jazm⟩, .alamat [.hadhfNun] false⟩,
  ⟨"M12", .mujib, ⟨.mudariSakin, "", .jazm⟩, .alamat [.hadhfAkhir] false⟩,
  ⟨"M13", .mujib, ⟨.mudariSakin, "", .raf⟩, .alamat [.sukun] false⟩,
  ⟨"M14", .mujib, ⟨.mudariNiswa, "", .nasb⟩, .alamat [.sukun] true⟩,
  ⟨"M15", .mujib, ⟨.ismLaYansarif, "", .jarr⟩, .alamat [.fatha] false⟩,
  ⟨"M16", .mujib, ⟨.ghayrMutamakkin, "قبل", .bilaAmil⟩, .alamat [.damma] true⟩,
  ⟨"M17", .mujib, ⟨.ghayrMutamakkin, "كم", .bilaAmil⟩, .alamat [.sukun] true⟩,
  ⟨"M18", .mujib, ⟨.ghayrMutamakkin, "ب", .bilaAmil⟩, .alamat [.kasra] true⟩,
  ⟨"M19", .mujib, ⟨.ghayrMutamakkin, "منذ", .bilaAmil⟩, .alamat [.damma] true⟩,
  ⟨"M20", .mujib, ⟨.amr, "", .bilaAmil⟩, .alamat [.sukun] true⟩,
  ⟨"M21", .hadd, ⟨.ismMutamakkin, "", .jazm⟩, .laYakun⟩,
  ⟨"M22", .hadd, ⟨.mudari, "", .jarr⟩, .laYakun⟩,
  ⟨"M23", .hadd, ⟨.muthanna, "", .jazm⟩, .laYakun⟩,
  ⟨"M24", .hadd, ⟨.madi, "", .jarr⟩, .laYakun⟩,
  ⟨"M25", .hadd, ⟨.amr, "", .jazm⟩, .laYakun⟩,
  ⟨"M26", .kharij, ⟨.jamMuannath, "", .raf⟩, .laHukm⟩,
  ⟨"M27", .kharij, ⟨.mudariSakin, "", .nasb⟩, .laHukm⟩,
  ⟨"M28", .kharij, ⟨.ghayrMutamakkin, "لن", .bilaAmil⟩, .laHukm⟩,
  ⟨"M29", .kharij, ⟨.ghayrMutamakkin, "أول", .bilaAmil⟩, .laHukm⟩,
  ⟨"M30", .kharij, ⟨.ismMutamakkin, "", .bilaAmil⟩, .laHukm⟩,
  ⟨"M31", .umum, ⟨.ismLaYansarifMuarraf, "", .jarr⟩, .alamat [.kasra] false⟩,
  ⟨"M32", .umum, ⟨.ghayrMutamakkin, "أين", .jarr⟩, .alamat [.fatha] true⟩,
  ⟨"M33", .umum, ⟨.mudariJam, "", .raf⟩, .alamat [.thubutNun] false⟩,
  ⟨"M34", .umum, ⟨.mudariIthnayn, "", .nasb⟩, .alamat [.hadhfNun] false⟩,
  ⟨"M35", .umum, ⟨.mudariNiswa, "", .jazm⟩, .alamat [.sukun] true⟩,
  ⟨"M36", .umum, ⟨.mudariMukhataba, "", .jazm⟩, .alamat [.hadhfNun] false⟩,
  ⟨"M37", .ghumud, ⟨.ghayrMutamakkin, "حيث", .bilaAmil⟩, .alamat [.fatha, .damma] true⟩,
  ⟨"M38", .ghumud, ⟨.madi, "", .bilaAmil⟩, .alamat [.fatha, .sukun] true⟩,
  ⟨"M39", .ghumud, ⟨.madi, "", .jazm⟩, .alamat [.fatha, .sukun] true⟩]

end Dawabit
end MajariKalim
end Jisr
