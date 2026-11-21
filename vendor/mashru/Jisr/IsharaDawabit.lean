/-
# حالاتُ ضابط أسماء الإشارة المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/ishara/cases.json` بـ `python3 -I scripts/bina_dawabit_ishara.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `5725a39dbc5783835202f7b4876665c6403a07628bee3c0986670de3df9be664`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والمصدرين قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/ishara/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/ishara/tajmid.json`. والمثالُ والسندُ في الملفّ المصدر.
-/
import Jisr.IsharaDabit

namespace Jisr
namespace Ishara
namespace Dawabit

open Dabit

def halat : List Hala := [
  ⟨"I01", .mujib, ⟨.dha, .mufradMudhakkar, .raf, .qarib, false, false, false⟩, [.maqbul], some "I08"⟩,
  ⟨"I02", .hadd, ⟨.dha, .mufradMudhakkar, .raf, .baid, false, false, false⟩, [.khata], some "I03"⟩,
  ⟨"I03", .mujib, ⟨.dha, .mufradMudhakkar, .raf, .baid, false, false, true⟩, [.maqbul], some "I02"⟩,
  ⟨"I04", .hadd, ⟨.dha, .mufradMudhakkar, .raf, .qarib, false, false, true⟩, [.khata], none⟩,
  ⟨"I05", .mujib, ⟨.dha, .mufradMudhakkar, .raf, .baid, false, true, true⟩, [.maqbul], some "I06"⟩,
  ⟨"I06", .umum, ⟨.dha, .mufradMudhakkar, .raf, .baid, true, true, true⟩, [.khata], some "I05"⟩,
  ⟨"I07", .umum, ⟨.dha, .mufradMudhakkar, .nasb, .baid, true, false, true⟩, [.maqbul], none⟩,
  ⟨"I08", .kharij, ⟨.dha, .mufradMudhakkar, .raf, .qarib, true, false, false⟩, [.laHukm], some "I01"⟩,
  ⟨"I09", .hadd, ⟨.dha, .mufradMuannath, .nasb, .qarib, false, false, false⟩, [.khata], some "I10"⟩,
  ⟨"I10", .mujib, ⟨.dhi, .mufradMuannath, .nasb, .qarib, false, false, false⟩, [.maqbul], some "I09"⟩,
  ⟨"I11", .mujib, ⟨.dhih, .mufradMuannath, .jarr, .qarib, false, false, false⟩, [.maqbul], none⟩,
  ⟨"I12", .kharij, ⟨.ti, .mufradMuannath, .jarr, .qarib, true, false, false⟩, [.laHukm], none⟩,
  ⟨"I13", .mujib, ⟨.tih, .mufradMuannath, .raf, .qarib, false, false, false⟩, [.maqbul], none⟩,
  ⟨"I14", .umum, ⟨.tih, .mufradMuannath, .raf, .baid, false, true, true⟩, [.maqbul], none⟩,
  ⟨"I15", .mujib, ⟨.ta, .mufradMuannath, .nasb, .qarib, false, false, false⟩, [.maqbul], some "I16"⟩,
  ⟨"I16", .hadd, ⟨.ta, .jamMuannath, .nasb, .qarib, false, false, false⟩, [.khata], some "I15"⟩,
  ⟨"I17", .mujib, ⟨.dhan, .muthannaMudhakkar, .raf, .qarib, false, false, false⟩, [.maqbul], some "I18"⟩,
  ⟨"I18", .hadd, ⟨.dhan, .muthannaMudhakkar, .nasb, .qarib, false, false, false⟩, [.khata], some "I17"⟩,
  ⟨"I19", .umum, ⟨.dhan, .muthannaMuannath, .raf, .qarib, false, false, false⟩, [.maqbul], none⟩,
  ⟨"I20", .umum, ⟨.dhan, .muthannaMudhakkar, .raf, .baid, false, false, true⟩, [.maqbul], some "I21"⟩,
  ⟨"I21", .hadd, ⟨.dhan, .muthannaMudhakkar, .raf, .baid, false, true, true⟩, [.khata], some "I20"⟩,
  ⟨"I22", .kharij, ⟨.dhan, .muthannaMudhakkar, .raf, .qarib, true, false, false⟩, [.laHukm], some "I28"⟩,
  ⟨"I23", .mujib, ⟨.tan, .muthannaMuannath, .raf, .qarib, false, false, false⟩, [.maqbul], some "I24"⟩,
  ⟨"I24", .hadd, ⟨.tan, .muthannaMuannath, .jarr, .qarib, false, false, false⟩, [.khata], some "I23"⟩,
  ⟨"I25", .mujib, ⟨.dhayn, .muthannaMudhakkar, .nasb, .qarib, false, false, false⟩, [.maqbul], some "I27"⟩,
  ⟨"I26", .umum, ⟨.dhayn, .muthannaMudhakkar, .jarr, .baid, false, false, true⟩, [.maqbul], none⟩,
  ⟨"I27", .kharij, ⟨.dhayn, .muthannaMudhakkar, .nasb, .qarib, true, false, false⟩, [.laHukm], some "I25"⟩,
  ⟨"I28", .hadd, ⟨.dhayn, .muthannaMudhakkar, .raf, .qarib, true, false, false⟩, [.khata], some "I22"⟩,
  ⟨"I29", .mujib, ⟨.tayn, .muthannaMuannath, .jarr, .qarib, false, false, false⟩, [.maqbul], none⟩,
  ⟨"I30", .umum, ⟨.tayn, .muthannaMuannath, .nasb, .baid, false, true, true⟩, [.khata], none⟩,
  ⟨"I31", .mujib, ⟨.ulaa, .jamMudhakkar, .raf, .qarib, false, false, false⟩, [.maqbul], none⟩,
  ⟨"I32", .mujib, ⟨.ulaa, .jamMuannath, .jarr, .qarib, false, false, false⟩, [.maqbul], none⟩,
  ⟨"I33", .hadd, ⟨.ulaa, .jamMudhakkar, .raf, .baid, false, true, true⟩, [.khata], some "I34"⟩,
  ⟨"I34", .umum, ⟨.ula, .jamMudhakkar, .raf, .baid, false, true, true⟩, [.maqbul], some "I33"⟩,
  ⟨"I35", .umum, ⟨.ulaa, .jamMuannath, .nasb, .baid, false, false, true⟩, [.maqbul], none⟩,
  ⟨"I36", .kharij, ⟨.ulaa, .jamMudhakkar, .nasb, .qarib, true, false, false⟩, [.laHukm], none⟩,
  ⟨"I37", .mujib, ⟨.ula, .jamMudhakkar, .nasb, .qarib, false, false, false⟩, [.maqbul], some "I38"⟩,
  ⟨"I38", .hadd, ⟨.ula, .muthannaMudhakkar, .nasb, .qarib, false, false, false⟩, [.khata], some "I37"⟩,
  ⟨"I39", .umum, ⟨.ula, .jamMuannath, .jarr, .qarib, false, false, false⟩, [.maqbul], none⟩,
  ⟨"I40", .mujib, ⟨.huna, .makan, .nasb, .qarib, false, false, false⟩, [.maqbul], none⟩,
  ⟨"I41", .mujib, ⟨.huna, .makan, .nasb, .qarib, true, false, false⟩, [.maqbul], none⟩,
  ⟨"I42", .mujib, ⟨.huna, .makan, .nasb, .baid, false, false, true⟩, [.maqbul], some "I43"⟩,
  ⟨"I43", .hadd, ⟨.huna, .makan, .nasb, .qarib, false, false, true⟩, [.khata], some "I42"⟩,
  ⟨"I44", .mujib, ⟨.huna, .makan, .nasb, .baid, false, true, true⟩, [.maqbul], some "I45"⟩,
  ⟨"I45", .umum, ⟨.huna, .makan, .nasb, .baid, true, true, true⟩, [.khata], some "I44"⟩,
  ⟨"I46", .mujib, ⟨.thamma, .makan, .nasb, .baid, false, false, false⟩, [.maqbul], some "I47"⟩,
  ⟨"I47", .hadd, ⟨.thamma, .makan, .nasb, .qarib, false, false, false⟩, [.khata], some "I46"⟩,
  ⟨"I48", .ghumud, ⟨.huna, .makan, .nasb, .baid, false, false, false⟩, [.maqbul, .khata], none⟩,
  ⟨"I49", .ghumud, ⟨.huna, .makan, .jarr, .baid, false, false, false⟩, [.maqbul, .khata], none⟩]

end Dawabit
end Ishara
end Jisr
