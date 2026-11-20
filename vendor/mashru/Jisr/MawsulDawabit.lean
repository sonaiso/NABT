/-
# حالاتُ ضابط الموصول المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/mawsul/cases.json` بـ `python3 -I scripts/bina_dawabit_mawsul.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `8f92e0f553336d92badf2e5437e355e7a08104174cf802f546cc81ca707154b3`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والمصدرين قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/mawsul/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/mawsul/tajmid.json`. والمثالُ والسندُ في الملفّ المصدر.
-/
import Jisr.MawsulDabit

namespace Jisr
namespace Mawsul
namespace Dawabit

open Dabit

def halat : List Hala := [
  ⟨"M01", .mujib, ⟨.alladhi, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .mufradMudhakkar⟩, [.maqbul], [.bila], some "M02"⟩,
  ⟨"M02", .hadd, ⟨.alladhi, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .mufradMuannath⟩, [.khata], [.bila], some "M01"⟩,
  ⟨"M03", .mujib, ⟨.allati, .mufradMuannath, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .mustatir, some .mufradMuannath⟩, [.maqbul], [.bila], some "M04"⟩,
  ⟨"M04", .hadd, ⟨.alladhi, .mufradMuannath, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .mustatir, some .mufradMuannath⟩, [.khata], [.bila], some "M03"⟩,
  ⟨"M05", .mujib, ⟨.man, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .zarfTamm, .mustatir, some .mufradMudhakkar⟩, [.maqbul], [.bila], none⟩,
  ⟨"M06", .mujib, ⟨.alladhani, .muthannaMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .muthannaMudhakkar⟩, [.maqbul], [.bila], some "M07"⟩,
  ⟨"M07", .hadd, ⟨.alladhani, .muthannaMudhakkar, .jarr, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .muthannaMudhakkar⟩, [.khata], [.bila], some "M06"⟩,
  ⟨"M08", .mujib, ⟨.alladhayni, .muthannaMudhakkar, .nasb, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .muthannaMudhakkar⟩, [.maqbul], [.bila], none⟩,
  ⟨"M09", .mujib, ⟨.allatani, .muthannaMuannath, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .muthannaMuannath⟩, [.maqbul], [.bila], some "M10"⟩,
  ⟨"M10", .hadd, ⟨.allatiyani, .muthannaMuannath, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .muthannaMuannath⟩, [.khata], [.bila], some "M09"⟩,
  ⟨"M11", .hadd, ⟨.allatayni, .muthannaMuannath, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .muthannaMuannath⟩, [.khata], [.bila], none⟩,
  ⟨"M12", .mujib, ⟨.alladhina, .jamMudhakkar, .nasb, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMudhakkar⟩, [.maqbul], [.bila], some "M13"⟩,
  ⟨"M13", .kharij, ⟨.alladhina, .jamMudhakkar, .nasb, true, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMudhakkar⟩, [.laHukm], [.bila], some "M12"⟩,
  ⟨"M14", .mujib, ⟨.allaa, .jamMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMudhakkar⟩, [.maqbul], [.nazr], some "M15"⟩,
  ⟨"M15", .umum, ⟨.alladhina, .jamMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMudhakkar⟩, [.maqbul], [.bila], some "M14"⟩,
  ⟨"M16", .mujib, ⟨.alladhuna, .jamMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMudhakkar⟩, [.maqbul], [.lugha], some "M17"⟩,
  ⟨"M17", .hadd, ⟨.alladhuna, .jamMudhakkar, .nasb, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMudhakkar⟩, [.khata], [.bila], some "M16"⟩,
  ⟨"M18", .mujib, ⟨.alula, .jamMudhakkar, .jarr, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMudhakkar⟩, [.maqbul], [.bila], none⟩,
  ⟨"M19", .mujib, ⟨.allati_j, .jamMuannath, .jarr, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMuannath⟩, [.maqbul], [.bila], some "M20"⟩,
  ⟨"M20", .hadd, ⟨.alladhina, .jamMuannath, .jarr, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMuannath⟩, [.khata], [.bila], some "M19"⟩,
  ⟨"M21", .mujib, ⟨.allai, .jamMuannath, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMuannath⟩, [.maqbul], [.bila], none⟩,
  ⟨"M22", .mujib, ⟨.allat, .jamMuannath, .nasb, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMuannath⟩, [.maqbul], [.bila], none⟩,
  ⟨"M23", .mujib, ⟨.ma, .mufradMudhakkar, .nasb, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .mahdhuf, some .mufradMudhakkar⟩, [.maqbul], [.bila], none⟩,
  ⟨"M24", .mujib, ⟨.ayy, .mufradMudhakkar, .nasb, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .mahdhuf, some .mufradMudhakkar⟩, [.maqbul], [.bila], none⟩,
  ⟨"M25", .mujib, ⟨.al, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .wasfSarih, .mustatir, some .mufradMudhakkar⟩, [.maqbul], [.bila], some "M58"⟩,
  ⟨"M26", .mujib, ⟨.al, .mufradMudhakkar, .nasb, false, .ghayrMadhkura, .ghayruhuma, false, .wasfSarih, .mustatir, some .mufradMudhakkar⟩, [.maqbul], [.bila], some "M27"⟩,
  ⟨"M27", .hadd, ⟨.al, .mufradMudhakkar, .nasb, false, .ghayrMadhkura, .ghayruhuma, false, .ismTafdil, .mustatir, some .mufradMudhakkar⟩, [.khata], [.bila], some "M26"⟩,
  ⟨"M28", .mujib, ⟨.dhu, .mufradMudhakkar, .raf, false, .tayyi, .ghayruhuma, false, .jumlaKhabariyya, .mustatir, some .mufradMudhakkar⟩, [.maqbul], [.bila], some "M29"⟩,
  ⟨"M29", .hadd, ⟨.dhu, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .mustatir, some .mufradMudhakkar⟩, [.khata], [.bila], some "M28"⟩,
  ⟨"M30", .mujib, ⟨.dhat, .mufradMuannath, .raf, false, .tayyi, .ghayruhuma, false, .jumlaKhabariyya, .mustatir, some .mufradMuannath⟩, [.maqbul], [.bila], some "M31"⟩,
  ⟨"M31", .hadd, ⟨.dhat, .mufradMuannath, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .mustatir, some .mufradMuannath⟩, [.khata], [.bila], some "M30"⟩,
  ⟨"M32", .mujib, ⟨.dhawat, .jamMuannath, .raf, false, .tayyi, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMuannath⟩, [.maqbul], [.bila], none⟩,
  ⟨"M33", .mujib, ⟨.dha, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .maIstifham, false, .jumlaKhabariyya, .mahdhuf, some .mufradMudhakkar⟩, [.maqbul], [.bila], some "M34"⟩,
  ⟨"M34", .kharij, ⟨.dha, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .maIstifham, true, .jumlaKhabariyya, .mahdhuf, some .mufradMudhakkar⟩, [.laHukm], [.bila], some "M33"⟩,
  ⟨"M35", .mujib, ⟨.dha, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .manIstifham, false, .jumlaKhabariyya, .zahir, some .mufradMudhakkar⟩, [.maqbul], [.bila], some "M36"⟩,
  ⟨"M36", .hadd, ⟨.dha, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .mufradMudhakkar⟩, [.khata], [.bila], some "M35"⟩,
  ⟨"M37", .mujib, ⟨.alladhi, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .zarfTamm, .mustatir, some .mufradMudhakkar⟩, [.maqbul], [.bila], some "M38"⟩,
  ⟨"M38", .hadd, ⟨.alladhi, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .zarfNaqis, .mustatir, some .mufradMudhakkar⟩, [.khata], [.bila], some "M37"⟩,
  ⟨"M39", .mujib, ⟨.alladhi, .mufradMudhakkar, .nasb, false, .ghayrMadhkura, .ghayruhuma, false, .jarrTamm, .mustatir, some .mufradMudhakkar⟩, [.maqbul], [.bila], some "M40"⟩,
  ⟨"M40", .hadd, ⟨.alladhi, .mufradMudhakkar, .nasb, false, .ghayrMadhkura, .ghayruhuma, false, .jarrNaqis, .mustatir, some .mufradMudhakkar⟩, [.khata], [.bila], some "M39"⟩,
  ⟨"M41", .hadd, ⟨.alladhiyani, .muthannaMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .muthannaMudhakkar⟩, [.khata], [.bila], none⟩,
  ⟨"M42", .hadd, ⟨.al, .jamMudhakkar, .jarr, false, .ghayrMadhkura, .ghayruhuma, false, .ismTafdil, .mustatir, some .jamMudhakkar⟩, [.khata], [.bila], none⟩,
  ⟨"M43", .hadd, ⟨.al, .mufradMuannath, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .mufradMuannath⟩, [.khata], [.bila], none⟩,
  ⟨"M44", .hadd, ⟨.allati, .mufradMuannath, .nasb, false, .ghayrMadhkura, .ghayruhuma, false, .zarfNaqis, .mustatir, some .mufradMuannath⟩, [.khata], [.bila], none⟩,
  ⟨"M45", .hadd, ⟨.man, .mufradMudhakkar, .jarr, false, .ghayrMadhkura, .ghayruhuma, false, .jarrNaqis, .zahir, some .mufradMudhakkar⟩, [.khata], [.bila], none⟩,
  ⟨"M46", .hadd, ⟨.alladhi, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .laAid, none⟩, [.khata], [.bila], none⟩,
  ⟨"M47", .kharij, ⟨.alladhuna, .jamMudhakkar, .raf, true, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMudhakkar⟩, [.laHukm], [.bila], none⟩,
  ⟨"M48", .kharij, ⟨.dha, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .manIstifham, true, .laSila, .laAid, none⟩, [.laHukm], [.bila], none⟩,
  ⟨"M49", .kharij, ⟨.man, .mufradMudhakkar, .raf, true, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .mustatir, some .mufradMudhakkar⟩, [.laHukm], [.bila], none⟩,
  ⟨"M50", .umum, ⟨.allatayni, .muthannaMuannath, .jarr, true, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .muthannaMuannath⟩, [.maqbul], [.bila], none⟩,
  ⟨"M51", .umum, ⟨.ayy, .muthannaMuannath, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jarrTamm, .mustatir, some .muthannaMuannath⟩, [.maqbul], [.bila], none⟩,
  ⟨"M52", .umum, ⟨.dhu, .jamMudhakkar, .raf, false, .tayyi, .ghayruhuma, false, .jumlaKhabariyya, .zahir, some .jamMudhakkar⟩, [.maqbul], [.bila], none⟩,
  ⟨"M53", .umum, ⟨.dha, .jamMuannath, .raf, false, .ghayrMadhkura, .maIstifham, false, .jumlaKhabariyya, .zahir, some .jamMuannath⟩, [.maqbul], [.bila], none⟩,
  ⟨"M54", .umum, ⟨.al, .mufradMudhakkar, .jarr, false, .ghayrMadhkura, .ghayruhuma, false, .wasfSarih, .laAid, none⟩, [.khata], [.bila], none⟩,
  ⟨"M55", .umum, ⟨.man, .mufradMudhakkar, .nasb, false, .ghayrMadhkura, .ghayruhuma, false, .laSila, .laAid, none⟩, [.khata], [.bila], none⟩,
  ⟨"M56", .ghumud, ⟨.alladhi, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaInshaiyya, .zahir, some .mufradMudhakkar⟩, [.maqbul, .khata], [.bila], none⟩,
  ⟨"M57", .ghumud, ⟨.allati, .mufradMuannath, .nasb, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaInshaiyya, .zahir, some .mufradMuannath⟩, [.maqbul, .khata], [.bila], none⟩,
  ⟨"M58", .ghumud, ⟨.al, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .filMurab, .mustatir, some .mufradMudhakkar⟩, [.maqbul, .khata], [.qalil], some "M25"⟩,
  ⟨"M59", .ghumud, ⟨.al, .muthannaMuannath, .jarr, false, .ghayrMadhkura, .ghayruhuma, false, .filMurab, .zahir, some .muthannaMuannath⟩, [.maqbul, .khata], [.qalil], none⟩]

end Dawabit
end Mawsul
end Jisr
