/-
# حالاتُ ضابط أبنية اسمَي الفاعل والمفعول المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/abniya/cases.json` بـ `python3 -I scripts/bina_dawabit_abniya.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `6e16c941d8ad07256419351afe3b328b5b7dc456527fc866af1acb7eb9ab371b`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والمصدرين قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/abniya/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/abniya/tajmid.json`. والمثالُ والسندُ في الملفّ المصدر.
-/
import Jisr.AbniyaDabit

namespace Jisr
namespace Abniya
namespace Dawabit

open Dabit

def halat : List Hala := [
  ⟨"B01", .mujib, ⟨.fataha, .mutaaddi, .fail, .faail⟩, [.maqbul], [.qiyas], some "B24"⟩,
  ⟨"B02", .mujib, ⟨.fataha, .lazim, .fail, .faail⟩, [.maqbul], [.qiyas], some "B04"⟩,
  ⟨"B03", .mujib, ⟨.kasra, .lazim, .fail, .faail⟩, [.maqbul], [.qalil], some "B43"⟩,
  ⟨"B04", .mujib, ⟨.damma, .lazim, .fail, .faail⟩, [.maqbul], [.qalil], some "B02"⟩,
  ⟨"B05", .mujib, ⟨.kasra, .lazim, .fail, .faiil_k⟩, [.maqbul], [.qiyas], some "B44"⟩,
  ⟨"B06", .mujib, ⟨.kasra, .lazim, .fail, .afal⟩, [.maqbul], [.qiyas], some "B45"⟩,
  ⟨"B07", .mujib, ⟨.kasra, .lazim, .fail, .falan⟩, [.maqbul], [.qiyas], some "B31"⟩,
  ⟨"B08", .mujib, ⟨.damma, .lazim, .fail, .fal_s⟩, [.maqbul], [.awla], some "B30"⟩,
  ⟨"B09", .mujib, ⟨.damma, .lazim, .fail, .faiil⟩, [.maqbul], [.awla], some "B29"⟩,
  ⟨"B10", .mujib, ⟨.damma, .lazim, .fail, .afal⟩, [.maqbul], [.qalil], some "B34"⟩,
  ⟨"B11", .mujib, ⟨.ghayrThulathi, .mutaaddi, .fail, .mudariMaksur⟩, [.maqbul], [.qiyas], some "B25"⟩,
  ⟨"B12", .mujib, ⟨.ghayrThulathi, .mutaaddi, .mafool, .mudariMaftuh⟩, [.maqbul], [.qiyas], some "B26"⟩,
  ⟨"B13", .mujib, ⟨.fataha, .mutaaddi, .mafool, .mafuul⟩, [.maqbul], [.qiyas], some "B27"⟩,
  ⟨"B14", .mujib, ⟨.fataha, .mutaaddi, .mafool, .faiil⟩, [.maqbul], [.naql], some "B28"⟩,
  ⟨"B15", .umum, ⟨.fataha, .lazim, .mafool, .mafuul⟩, [.maqbul], [.qiyas], none⟩,
  ⟨"B16", .umum, ⟨.ghayrThulathi, .lazim, .fail, .mudariMaksur⟩, [.maqbul], [.qiyas], some "B32"⟩,
  ⟨"B17", .umum, ⟨.ghayrThulathi, .lazim, .mafool, .mudariMaftuh⟩, [.maqbul], [.qiyas], none⟩,
  ⟨"B18", .umum, ⟨.kasra, .mutaaddi, .mafool, .mafuul⟩, [.maqbul], [.qiyas], some "B47"⟩,
  ⟨"B19", .umum, ⟨.damma, .lazim, .mafool, .mafuul⟩, [.maqbul], [.qiyas], some "B33"⟩,
  ⟨"B20", .umum, ⟨.fataha, .lazim, .fail, .faiil⟩, [.maqbul], [.qalil], some "B21"⟩,
  ⟨"B21", .umum, ⟨.fataha, .lazim, .mafool, .faiil⟩, [.maqbul], [.naql], some "B20"⟩,
  ⟨"B22", .umum, ⟨.kasra, .mutaaddi, .mafool, .faiil⟩, [.maqbul], [.naql], some "B46"⟩,
  ⟨"B23", .umum, ⟨.fataha, .mutaaddi, .fail, .fal_s⟩, [.maqbul], [.qalil], some "B35"⟩,
  ⟨"B24", .hadd, ⟨.ghayrThulathi, .mutaaddi, .fail, .faail⟩, [.khata], [.bila], some "B01"⟩,
  ⟨"B25", .hadd, ⟨.ghayrThulathi, .mutaaddi, .fail, .mudariMaftuh⟩, [.khata], [.bila], some "B11"⟩,
  ⟨"B26", .hadd, ⟨.ghayrThulathi, .mutaaddi, .mafool, .mudariMaksur⟩, [.khata], [.bila], some "B12"⟩,
  ⟨"B27", .hadd, ⟨.ghayrThulathi, .mutaaddi, .mafool, .mafuul⟩, [.khata], [.bila], some "B13"⟩,
  ⟨"B28", .hadd, ⟨.ghayrThulathi, .mutaaddi, .mafool, .faiil⟩, [.khata], [.bila], some "B14"⟩,
  ⟨"B29", .hadd, ⟨.kasra, .lazim, .fail, .faiil⟩, [.khata], [.bila], some "B09"⟩,
  ⟨"B30", .hadd, ⟨.kasra, .lazim, .fail, .fal_s⟩, [.khata], [.bila], some "B08"⟩,
  ⟨"B31", .hadd, ⟨.damma, .lazim, .fail, .falan⟩, [.khata], [.bila], some "B07"⟩,
  ⟨"B32", .hadd, ⟨.kasra, .lazim, .fail, .mudariMaksur⟩, [.khata], [.bila], some "B16"⟩,
  ⟨"B33", .hadd, ⟨.damma, .lazim, .fail, .mafuul⟩, [.khata], [.bila], some "B19"⟩,
  ⟨"B34", .hadd, ⟨.ghayrThulathi, .lazim, .fail, .afal⟩, [.khata], [.bila], some "B10"⟩,
  ⟨"B35", .hadd, ⟨.fataha, .mutaaddi, .mafool, .fal_s⟩, [.khata], [.bila], some "B23"⟩,
  ⟨"B36", .hadd, ⟨.kasra, .lazim, .fail, .faal_f⟩, [.khata], [.bila], none⟩,
  ⟨"B37", .hadd, ⟨.damma, .lazim, .fail, .mudariMaksur⟩, [.khata], [.bila], none⟩,
  ⟨"B38", .hadd, ⟨.kasra, .lazim, .mafool, .faiil_k⟩, [.khata], [.bila], none⟩,
  ⟨"B39", .hadd, ⟨.fataha, .mutaaddi, .mafool, .faail⟩, [.khata], [.bila], none⟩,
  ⟨"B40", .hadd, ⟨.fataha, .mutaaddi, .mafool, .mudariMaftuh⟩, [.khata], [.bila], none⟩,
  ⟨"B41", .hadd, ⟨.fataha, .mutaaddi, .mafool, .faal_f⟩, [.khata], [.bila], none⟩,
  ⟨"B42", .hadd, ⟨.ghayrThulathi, .mutaaddi, .fail, .falan⟩, [.khata], [.bila], none⟩,
  ⟨"B43", .kharij, ⟨.kasra, .mutaaddi, .fail, .faail⟩, [.laHukm], [.bila], some "B03"⟩,
  ⟨"B44", .kharij, ⟨.kasra, .mutaaddi, .fail, .faiil_k⟩, [.laHukm], [.bila], some "B05"⟩,
  ⟨"B45", .kharij, ⟨.kasra, .mutaaddi, .fail, .afal⟩, [.laHukm], [.bila], some "B06"⟩,
  ⟨"B46", .kharij, ⟨.kasra, .mutaaddi, .fail, .faiil⟩, [.laHukm], [.bila], some "B22"⟩,
  ⟨"B47", .kharij, ⟨.kasra, .mutaaddi, .fail, .mafuul⟩, [.laHukm], [.bila], some "B18"⟩,
  ⟨"B48", .kharij, ⟨.kasra, .mutaaddi, .fail, .mudariMaksur⟩, [.laHukm], [.bila], none⟩,
  ⟨"B49", .ghumud, ⟨.damma, .lazim, .fail, .faal_f⟩, [.maqbul, .khata], [.qalil, .bila], none⟩,
  ⟨"B50", .ghumud, ⟨.damma, .lazim, .fail, .faiil_k⟩, [.maqbul, .khata], [.qalil, .bila], none⟩]

end Dawabit
end Abniya
end Jisr
