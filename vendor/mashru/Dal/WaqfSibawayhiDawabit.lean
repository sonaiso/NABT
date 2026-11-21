/-
# حالاتُ ضابط الوقف على أواخر الكلم المتحرّكة في الوصل المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/waqf/cases.json` بـ `python3 -I scripts/bina_dawabit_waqf.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `9b6e35e2983fdef2893c3e9d72dbf473d7414bc9127eb1e5eb341d4a4a259853`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والبابين قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/waqf/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/waqf/tajmid.json`. والمثالُ والسندُ في الملفّ المصدر.
-/
import Dal.WaqfSibawayhi

namespace Dal
namespace WaqfSibawayhi
namespace Dawabit

inductive Fia
  | mujib | hadd | kharij | umum | ghumud
  deriving DecidableEq, Repr

structure Hala where
  ism : String
  fia : Fia
  kalima : Kalima
  /-- القيمةُ وحدها، أو البديلان في الغموض. -/
  kalam : List Daraja
  /-- `none`: «غير_مسؤول». -/
  shir : Option (List Daraja)
  deriving DecidableEq, Repr

def halat : List Hala := [
  ⟨"W01", .mujib, ⟨.sahih, true, true, .raf, .ishmam⟩, [.maqbul], none⟩,
  ⟨"W02", .mujib, ⟨.sahih, false, true, .raf, .ishmam⟩, [.maqbul], none⟩,
  ⟨"W03", .mujib, ⟨.sahih, true, true, .raf, .iskan⟩, [.maqbul], none⟩,
  ⟨"W04", .mujib, ⟨.sahih, false, true, .raf, .rawm⟩, [.maqbul], none⟩,
  ⟨"W05", .mujib, ⟨.sahih, true, true, .raf, .tadif⟩, [.maqbul], some [.maqbul]⟩,
  ⟨"W06", .mujib, ⟨.sahih, true, true, .jarr, .iskan⟩, [.maqbul], none⟩,
  ⟨"W07", .mujib, ⟨.sahih, false, true, .nasb, .iskan⟩, [.maqbul], none⟩,
  ⟨"W08", .mujib, ⟨.sahih, false, true, .nasb, .rawm⟩, [.maqbul], none⟩,
  ⟨"W09", .mujib, ⟨.sahih, false, true, .nasb, .tadif⟩, [.maqbul], some [.maqbul]⟩,
  ⟨"W10", .mujib, ⟨.sahih, true, true, .jarr, .tadif⟩, [.maqbul], some [.maqbul]⟩,
  ⟨"W11", .mujib, ⟨.haTaanith, false, true, .raf, .ha⟩, [.maqbul], none⟩,
  ⟨"W12", .mujib, ⟨.haTaanith, false, true, .raf, .ta⟩, [.lugha], none⟩,
  ⟨"W13", .mujib, ⟨.sahih, true, false, .raf, .wawAwYa⟩, [.lugha], some [.maqbul]⟩,
  ⟨"W14", .mujib, ⟨.sahih, true, false, .jarr, .wawAwYa⟩, [.lugha], some [.maqbul]⟩,
  ⟨"W15", .mujib, ⟨.taJam, false, false, .raf, .ta⟩, [.maqbul], none⟩,
  ⟨"W16", .mujib, ⟨.taMulhaqa, true, false, .raf, .ta⟩, [.maqbul], none⟩,
  ⟨"W17", .mujib, ⟨.yaBaadKasra, false, true, .raf, .hadhfYa⟩, [.maqbul], none⟩,
  ⟨"W18", .mujib, ⟨.sahih, false, true, .nasb, .ha⟩, [.lugha], none⟩,
  ⟨"W19", .mujib, ⟨.sahih, true, false, .raf, .ishmam⟩, [.maqbul], none⟩,
  ⟨"W20", .mujib, ⟨.sahih, true, false, .raf, .rawm⟩, [.maqbul], none⟩,
  ⟨"W21", .mujib, ⟨.sahih, true, false, .raf, .iskan⟩, [.maqbul], none⟩,
  ⟨"W22", .hadd, ⟨.sahih, true, false, .raf, .tadif⟩, [.khata], some [.maqbul]⟩,
  ⟨"W23", .hadd, ⟨.sahih, true, false, .nasb, .tadif⟩, [.khata], some [.maqbul]⟩,
  ⟨"W24", .hadd, ⟨.sahih, true, true, .jarr, .ishmam⟩, [.khata], none⟩,
  ⟨"W25", .hadd, ⟨.sahih, false, true, .nasb, .ishmam⟩, [.khata], none⟩,
  ⟨"W26", .hadd, ⟨.taJam, false, false, .jarr, .ha⟩, [.khata], none⟩,
  ⟨"W27", .hadd, ⟨.taMulhaqa, true, false, .jarr, .ha⟩, [.khata], none⟩,
  ⟨"W28", .hadd, ⟨.sahih, true, false, .nasb, .iskan⟩, [.khata], none⟩,
  ⟨"W29", .hadd, ⟨.sahih, false, true, .nasb, .alif⟩, [.khata], some [.maqbul]⟩,
  ⟨"W30", .kharij, ⟨.sahih, false, true, .raf, .ha⟩, [.laHukm], none⟩,
  ⟨"W31", .kharij, ⟨.haTaanith, true, true, .raf, .ishmam⟩, [.laHukm], none⟩,
  ⟨"W32", .kharij, ⟨.sahih, true, false, .jarr, .ha⟩, [.laHukm], none⟩,
  ⟨"W33", .kharij, ⟨.yaBaadKasra, false, true, .raf, .ishmam⟩, [.laHukm], none⟩,
  ⟨"W34", .umum, ⟨.sahih, true, false, .nasb, .alif⟩, [.maqbul], some [.maqbul]⟩,
  ⟨"W35", .umum, ⟨.taMulhaqa, true, false, .nasb, .alif⟩, [.maqbul], some [.maqbul]⟩,
  ⟨"W36", .umum, ⟨.haTaanith, true, true, .jarr, .ha⟩, [.maqbul], none⟩,
  ⟨"W37", .umum, ⟨.sahih, true, true, .raf, .rawm⟩, [.maqbul], none⟩,
  ⟨"W38", .umum, ⟨.sahih, false, false, .raf, .rawm⟩, [.maqbul], none⟩,
  ⟨"W39", .umum, ⟨.sahih, false, false, .raf, .tadif⟩, [.khata], some [.maqbul]⟩,
  ⟨"W40", .umum, ⟨.sahih, true, false, .jarr, .tadif⟩, [.khata], some [.maqbul]⟩]

end Dawabit
end WaqfSibawayhi
end Dal
