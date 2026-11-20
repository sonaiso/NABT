/-
# حالاتُ ضابط الخبر المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/khabar/cases.json` بـ `python3 -I scripts/bina_dawabit_khabar.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `c549d782013f628bf5ac5534dd0aa04c203e5ace75e5e0237e85343d66598f54`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والمصدرين قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/khabar/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/khabar/tajmid.json`. والمثالُ والسندُ في الملفّ المصدر.
-/
import Jisr.KhabarDabit

namespace Jisr
namespace Khabar
namespace Dawabit

open Dabit

def halat : List Hala := [
  ⟨"K01", .mujib, ⟨.mubtadaKhabar, .dhat, .jumlaIsmiyya, .damir, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], some "K02"⟩,
  ⟨"K02", .hadd, ⟨.mubtadaKhabar, .dhat, .jumlaIsmiyya, .laRabit, .la, .la, .la, .la, .la, .la, .la⟩, [.khata], [.bila], some "K01"⟩,
  ⟨"K03", .mujib, ⟨.mubtadaKhabar, .dhat, .jumlaIsmiyya, .ishara, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], none⟩,
  ⟨"K04", .mujib, ⟨.mubtadaKhabar, .maana, .jumlaIsmiyya, .iada, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], none⟩,
  ⟨"K05", .mujib, ⟨.mubtadaKhabar, .dhat, .jumlaFiliyya, .umum, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], none⟩,
  ⟨"K06", .mujib, ⟨.mubtadaKhabar, .maana, .jumlaIsmiyya, .hiya, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], some "K07"⟩,
  ⟨"K07", .hadd, ⟨.mubtadaKhabar, .maana, .jumlaIsmiyya, .laRabit, .la, .la, .la, .la, .la, .la, .la⟩, [.khata], [.bila], some "K06"⟩,
  ⟨"K08", .umum, ⟨.mubtadaKhabar, .maana, .jumlaFiliyya, .hiya, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], none⟩,
  ⟨"K09", .umum, ⟨.mubtadaKhabar, .dhat, .jumlaFiliyya, .damir, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], some "K10"⟩,
  ⟨"K10", .hadd, ⟨.mubtadaKhabar, .dhat, .jumlaFiliyya, .laRabit, .la, .la, .la, .la, .la, .la, .la⟩, [.khata], [.bila], some "K09"⟩,
  ⟨"K11", .umum, ⟨.mubtadaKhabar, .maana, .jumlaFiliyya, .ishara, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], none⟩,
  ⟨"K12", .umum, ⟨.mubtadaKhabar, .dhat, .jumlaFiliyya, .iada, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], none⟩,
  ⟨"K13", .umum, ⟨.mubtadaKhabar, .maana, .jumlaIsmiyya, .umum, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], none⟩,
  ⟨"K14", .mujib, ⟨.mubtadaKhabar, .dhat, .zarfMakan, .la, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], none⟩,
  ⟨"K15", .umum, ⟨.mubtadaKhabar, .maana, .zarfMakan, .la, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], none⟩,
  ⟨"K16", .umum, ⟨.mubtadaKhabar, .dhat, .jarMajrur, .la, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], none⟩,
  ⟨"K17", .mujib, ⟨.mubtadaKhabar, .maana, .jarMajrur, .la, .la, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], none⟩,
  ⟨"K18", .hadd, ⟨.mubtadaKhabar, .dhat, .zarfZaman, .la, .la, .la, .ghayrMufid, .la, .la, .la, .la⟩, [.khata], [.bila], some "K19"⟩,
  ⟨"K19", .ghumud, ⟨.mubtadaKhabar, .dhat, .zarfZaman, .la, .la, .la, .mufid, .la, .la, .la, .la⟩, [.maqbul], [.bitawil, .bila], some "K18"⟩,
  ⟨"K20", .umum, ⟨.mubtadaKhabar, .maana, .zarfZaman, .la, .la, .la, .mufid, .la, .la, .la, .la⟩, [.maqbul], [.bila], some "K21"⟩,
  ⟨"K21", .hadd, ⟨.mubtadaKhabar, .maana, .zarfZaman, .la, .la, .la, .ghayrMufid, .la, .la, .la, .la⟩, [.khata], [.bila], some "K20"⟩,
  ⟨"K22", .mujib, ⟨.mubtadaKhabar, .dhat, .mufradMushtaq, .la, .mustakin, .lisahibihi, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], some "K23"⟩,
  ⟨"K23", .hadd, ⟨.mubtadaKhabar, .dhat, .mufradMushtaq, .la, .laShay, .lisahibihi, .la, .la, .la, .la, .la⟩, [.khata], [.bila], some "K22"⟩,
  ⟨"K24", .mujib, ⟨.mubtadaKhabar, .maana, .mufradMushtaq, .la, .mustakin, .lisahibihi, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], some "K28"⟩,
  ⟨"K25", .mujib, ⟨.mubtadaKhabar, .dhat, .mufradMushtaq, .la, .bariz, .lighayrihi, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], some "K26"⟩,
  ⟨"K26", .hadd, ⟨.mubtadaKhabar, .dhat, .mufradMushtaq, .la, .mustakin, .lighayrihi, .la, .la, .la, .la, .la⟩, [.khata], [.bila], some "K25"⟩,
  ⟨"K27", .umum, ⟨.mubtadaKhabar, .maana, .mufradMushtaq, .la, .bariz, .lighayrihi, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], some "K38"⟩,
  ⟨"K28", .hadd, ⟨.mubtadaKhabar, .maana, .mufradMushtaq, .la, .mustakin, .lighayrihi, .la, .la, .la, .la, .la⟩, [.khata], [.bila], some "K24"⟩,
  ⟨"K29", .hadd, ⟨.mubtadaKhabar, .dhat, .mufradMushtaq, .la, .bariz, .lisahibihi, .la, .la, .la, .la, .la⟩, [.khata], [.bila], none⟩,
  ⟨"K30", .hadd, ⟨.mubtadaKhabar, .maana, .mufradMushtaq, .la, .laShay, .lighayrihi, .la, .la, .la, .la, .la⟩, [.khata], [.bila], none⟩,
  ⟨"K31", .mujib, ⟨.mubtadaKhabar, .dhat, .mufradJamid, .la, .laShay, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], some "K33"⟩,
  ⟨"K32", .mujib, ⟨.mubtadaKhabar, .maana, .mufradJamid, .la, .laShay, .la, .la, .la, .la, .la, .la⟩, [.maqbul], [.bila], some "K34"⟩,
  ⟨"K33", .hadd, ⟨.mubtadaKhabar, .dhat, .mufradJamid, .la, .mustakin, .la, .la, .la, .la, .la, .la⟩, [.khata], [.bila], some "K31"⟩,
  ⟨"K34", .hadd, ⟨.mubtadaKhabar, .maana, .mufradJamid, .la, .bariz, .la, .la, .la, .la, .la, .la⟩, [.khata], [.bila], some "K32"⟩,
  ⟨"K35", .kharij, ⟨.mubtadaKhabar, .dhat, .mufradJamid, .la, .zahir, .la, .la, .la, .la, .la, .la⟩, [.laHukm], [.bila], none⟩,
  ⟨"K36", .kharij, ⟨.mubtadaKhabar, .maana, .mufradJamid, .la, .zahir, .la, .la, .la, .la, .la, .la⟩, [.laHukm], [.bila], none⟩,
  ⟨"K37", .kharij, ⟨.mubtadaKhabar, .dhat, .mufradMushtaq, .la, .zahir, .lighayrihi, .la, .la, .la, .la, .la⟩, [.laHukm], [.bila], none⟩,
  ⟨"K38", .kharij, ⟨.mubtadaKhabar, .maana, .mufradMushtaq, .la, .zahir, .lighayrihi, .la, .la, .la, .la, .la⟩, [.laHukm], [.bila], some "K27"⟩,
  ⟨"K39", .kharij, ⟨.mubtadaKhabar, .dhat, .mufradMushtaq, .la, .zahir, .lisahibihi, .la, .la, .la, .la, .la⟩, [.laHukm], [.bila], none⟩,
  ⟨"K40", .mujib, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .istifham, .mufrad, .muthanna, .failAghna⟩, [.maqbul], [.bila], some "K41"⟩,
  ⟨"K41", .hadd, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .istifham, .mufrad, .muthanna, .khabarMuqaddam⟩, [.khata], [.bila], some "K40"⟩,
  ⟨"K42", .mujib, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .nafy, .mufrad, .muthanna, .failAghna⟩, [.maqbul], [.bila], some "K56"⟩,
  ⟨"K43", .mujib, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .istifham, .mufrad, .jam, .failAghna⟩, [.maqbul], [.bila], none⟩,
  ⟨"K44", .umum, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .istifham, .mufrad, .mufrad, .failAghna⟩, [.maqbul], [.bila], some "K45"⟩,
  ⟨"K45", .hadd, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .istifham, .mufrad, .mufrad, .khabarMuqaddam⟩, [.khata], [.bila], some "K44"⟩,
  ⟨"K46", .umum, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .nafy, .mufrad, .jam, .failAghna⟩, [.maqbul], [.bila], some "K47"⟩,
  ⟨"K47", .ghumud, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .laItimad, .mufrad, .jam, .failAghna⟩, [.maqbul, .khata], [.qalil], some "K46"⟩,
  ⟨"K48", .ghumud, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .laItimad, .mufrad, .mufrad, .failAghna⟩, [.maqbul, .khata], [.qalil], some "K49"⟩,
  ⟨"K49", .umum, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .nafy, .mufrad, .mufrad, .failAghna⟩, [.maqbul], [.bila], some "K48"⟩,
  ⟨"K50", .mujib, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .istifham, .muthanna, .muthanna, .khabarMuqaddam⟩, [.maqbul], [.bila], some "K51"⟩,
  ⟨"K51", .hadd, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .istifham, .muthanna, .jam, .khabarMuqaddam⟩, [.khata], [.bila], some "K50"⟩,
  ⟨"K52", .umum, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .nafy, .jam, .jam, .khabarMuqaddam⟩, [.maqbul], [.bila], some "K53"⟩,
  ⟨"K53", .hadd, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .nafy, .jam, .mufrad, .khabarMuqaddam⟩, [.khata], [.bila], some "K52"⟩,
  ⟨"K54", .umum, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .laItimad, .muthanna, .muthanna, .khabarMuqaddam⟩, [.maqbul], [.bila], none⟩,
  ⟨"K55", .hadd, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .laItimad, .mufrad, .muthanna, .khabarMuqaddam⟩, [.khata], [.bila], some "K57"⟩,
  ⟨"K56", .hadd, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .nafy, .mufrad, .muthanna, .khabarMuqaddam⟩, [.khata], [.bila], some "K42"⟩,
  ⟨"K57", .ghumud, ⟨.wasfMarfu, .la, .la, .la, .la, .la, .la, .laItimad, .mufrad, .muthanna, .failAghna⟩, [.maqbul, .khata], [.qalil], some "K55"⟩]

end Dawabit
end Khabar
end Jisr
