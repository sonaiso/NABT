/-
# حالاتُ ضابط «نفي الفعل» وحروفِ الفعل المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/nafy/cases.json` بـ `python3 -I scripts/bina_dawabit_nafy.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `30271f86d033784c08d02bce3721c6e4697b6c3163017d3542dafaba4df099a5`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والنطاق قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/nafy/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/nafy/tajmid.json`. والمثالُ والسندُ في الملفّ المصدر.
-/
import Jisr.NafyFil

namespace Jisr
namespace NafyFil
namespace Dawabit

inductive Fia
  | mujib | hadd | kharij | umum | ghumud
  deriving DecidableEq, Repr

structure HalaNafy where
  ism : String
  fia : Fia
  sual : Sual
  /-- `none`: «لا_حكم». -/
  suwar : Option (List String)
  deriving DecidableEq, Repr

structure HalaWali where
  ism : String
  fia : Fia
  harf : String
  yali : Yali
  /-- القيمةُ وحدها، أو البديلان في الغموض. -/
  kalam : List Daraja
  /-- `none`: «غير_مسؤول». -/
  shir : Option (List Daraja)
  deriving DecidableEq, Repr

def halatNafy : List HalaNafy := [
  ⟨"N01", .mujib, ⟨.nafy, "فعل", .ghayrMuallan, .ghayrMuallan⟩, some ["لم يفعل"]⟩,
  ⟨"N02", .mujib, ⟨.nafy, "قد فعل", .ghayrMuallan, .ghayrMuallan⟩, some ["لما يفعل"]⟩,
  ⟨"N03", .mujib, ⟨.nafy, "لقد فعل", .ghayrMuallan, .ghayrMuallan⟩, some ["ما فعل"]⟩,
  ⟨"N04", .mujib, ⟨.nafy, "يفعل", .hal, .ghayrMuallan⟩, some ["ما يفعل"]⟩,
  ⟨"N05", .mujib, ⟨.nafy, "يفعل", .ghayrWaqi, .ghayrMuallan⟩, some ["لا يفعل"]⟩,
  ⟨"N06", .ghumud, ⟨.nafy, "يفعل", .ghayrMuallan, .ghayrMuallan⟩, some ["ما يفعل", "لا يفعل"]⟩,
  ⟨"N07", .mujib, ⟨.nafy, "ليفعلن", .ghayrMuallan, .ghayrMuallan⟩, some ["لا يفعل"]⟩,
  ⟨"N08", .mujib, ⟨.nafy, "سوف يفعل", .ghayrMuallan, .ghayrMuallan⟩, some ["لن يفعل"]⟩,
  ⟨"N09", .mujib, ⟨.nafy, "فعل", .ghayrMuallan, .jawabHal⟩, some ["ما فعل"]⟩,
  ⟨"N10", .mujib, ⟨.ithbat, "لن يفعل", .ghayrMuallan, .ghayrMuallan⟩, some ["سوف يفعل", "سيفعل"]⟩,
  ⟨"N11", .mujib, ⟨.ithbat, "لم يفعل", .ghayrMuallan, .ghayrMuallan⟩, some ["فعل"]⟩,
  ⟨"N12", .ghumud, ⟨.ithbat, "لا يفعل", .ghayrMuallan, .ghayrMuallan⟩, some ["يفعل", "ليفعلن"]⟩,
  ⟨"N13", .mujib, ⟨.ithbat, "لا يفعل", .ghayrMuallan, .qasam⟩, some ["ليفعلن"]⟩,
  ⟨"N14", .umum, ⟨.nafy, "سيفعل", .ghayrMuallan, .ghayrMuallan⟩, some ["لن يفعل"]⟩,
  ⟨"N15", .kharij, ⟨.nafy, "قد يفعل", .ghayrMuallan, .ghayrMuallan⟩, none⟩,
  ⟨"N16", .kharij, ⟨.ithbat, "لا تفعل", .ghayrMuallan, .ghayrMuallan⟩, none⟩]

def halatWali : List HalaWali := [
  ⟨"N17", .mujib, "قد", .fil, [.maqbul], none⟩,
  ⟨"N18", .hadd, "قد", .ismThummaFil, [.khata], none⟩,
  ⟨"N19", .hadd, "سوف", .ismThummaFil, [.khata], none⟩,
  ⟨"N20", .hadd, "رب", .fil, [.khata], none⟩,
  ⟨"N21", .hadd, "قلما", .ismThummaFil, [.khata], some [.maqbul]⟩,
  ⟨"N22", .hadd, "هلا", .ismThummaFil, [.khata], some [.maqbul]⟩,
  ⟨"N23", .umum, "لما", .ismThummaFil, [.khata], none⟩,
  ⟨"N24", .mujib, "كما", .fil, [.maqbul], some [.maqbul]⟩,
  ⟨"N25", .umum, "كما", .ismThummaFil, [.khata], none⟩,
  ⟨"N26", .mujib, "لكن", .fil, [.maqbul], none⟩,
  ⟨"N27", .hadd, "هل", .ismThummaFil, [.marjuh], none⟩,
  ⟨"N28", .kharij, "هل", .ism, [.laHukm], none⟩,
  ⟨"N29", .kharij, "رب", .ism, [.laHukm], none⟩,
  ⟨"N30", .kharij, "لم", .ismThummaFil, [.laHukm], none⟩]

end Dawabit
end NafyFil
end Jisr
