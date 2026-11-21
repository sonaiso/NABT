/-
# حالاتُ ضابط «صكّ الجملة» المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/sakk/cases.json` بـ `python3 -I scripts/bina_dawabit_sakk.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `f23fee33de9b5a37f78cc848603823d4b5dce0664695e48aedd9b06ca68ce446`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والنطاق قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/sakk/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/sakk/tajmid.json`. والمثالُ والسندُ في الملفّ المصدر.
-/
import Jisr.SakkJumla

namespace Jisr
namespace SakkJumla
namespace Dawabit

inductive Fia
  | mujib | hadd | kharij | umum | ghumud
  deriving DecidableEq, Repr

structure HalaQ where
  ism : String
  fia : Fia
  dakhil : DakhilQ
  /-- القيمةُ وحدها، أو البديلان في الغموض. -/
  awwal : List Quwwa
  thani : List Quwwa
  deriving DecidableEq, Repr

structure HalaS where
  ism : String
  fia : Fia
  dakhil : DakhilS
  sabab : List Sabab
  deriving DecidableEq, Repr

structure HalaM where
  ism : String
  fia : Fia
  dakhil : DakhilM
  marji : List Marji
  deriving DecidableEq, Repr

def halatQ : List HalaQ := [
  ⟨"S01", .ghumud, ⟨.laShay, .laQawl, .laQawl, .amma⟩, [.ithbat, .insha], [.laThani]⟩,
  ⟨"S02", .mujib, ⟨.lam, .laQawl, .laQawl, .amma⟩, [.nafy], [.laThani]⟩,
  ⟨"S03", .mujib, ⟨.in_, .laQawl, .laQawl, .amma⟩, [.taliq], [.taliq]⟩,
  ⟨"S04", .mujib, ⟨.laShay, .qala, .innaMaksura, .amma⟩, [.ithbat], [.hikaya]⟩,
  ⟨"S05", .mujib, ⟨.laShay, .qala, .marfu, .amma⟩, [.ithbat], [.hikaya]⟩,
  ⟨"S06", .mujib, ⟨.laShay, .taqulMustafhim, .mansub, .amma⟩, [.insha], [.zann]⟩,
  ⟨"S07", .hadd, ⟨.laShay, .taqulMustafhim, .marfu, .amma⟩, [.insha], [.hikaya]⟩,
  ⟨"S08", .mujib, ⟨.laShay, .taqulMustafhim, .annaMaftuha, .amma⟩, [.insha], [.zann]⟩,
  ⟨"S09", .hadd, ⟨.laShay, .taqulMustafhim, .innaMaksura, .amma⟩, [.insha], [.hikaya]⟩,
  ⟨"S10", .umum, ⟨.laShay, .qala, .mansub, .banuSulaym⟩, [.ithbat], [.zann]⟩,
  ⟨"S11", .umum, ⟨.lam, .qala, .innaMaksura, .amma⟩, [.nafy], [.hikaya]⟩,
  ⟨"S12", .ghumud, ⟨.laShay, .taqulMustafhim, .ghayrMuallan, .amma⟩, [.insha], [.zann, .hikaya]⟩]

def halatS : List HalaS := [
  ⟨"S13", .mujib, ⟨.masdarMansub, .mustawfat, .laYantabiq⟩, [.illa]⟩,
  ⟨"S14", .ghumud, ⟨.masdarMansub, .ghayrMuallan, .laYantabiq⟩, [.illa, .ghayrMadhkur]⟩,
  ⟨"S15", .hadd, ⟨.masdarMansub, .faqdWaqt, .laYantabiq⟩, [.laHukm]⟩,
  ⟨"S16", .ghumud, ⟨.lamJarra, .laYantabiq, .laYantabiq⟩, [.illa, .ghayrMadhkur]⟩,
  ⟨"S17", .mujib, ⟨.lamNasiba, .laYantabiq, .laYantabiq⟩, [.illa]⟩,
  ⟨"S18", .umum, ⟨.kay, .laYantabiq, .laYantabiq⟩, [.illa]⟩,
  ⟨"S19", .mujib, ⟨.anBilaLam, .laYantabiq, .laYantabiq⟩, [.illa]⟩,
  ⟨"S20", .mujib, ⟨.hattaMansub, .laYantabiq, .laysaSabab⟩, [.ghayrMadhkur]⟩,
  ⟨"S21", .ghumud, ⟨.hattaMansub, .laYantabiq, .ghayrMuallan⟩, [.ghayrMadhkur, .illa]⟩,
  ⟨"S22", .mujib, ⟨.hattaMarfu, .laYantabiq, .sabab⟩, [.sababiyya]⟩,
  ⟨"S23", .umum, ⟨.hattaMarfu, .laYantabiq, .ghayrMuallan⟩, [.sababiyya]⟩,
  ⟨"S24", .hadd, ⟨.hattaMarfu, .laYantabiq, .laysaSabab⟩, [.ghayrMadhkur]⟩,
  ⟨"S25", .mujib, ⟨.faMansub, .laYantabiq, .ghayrMuallan⟩, [.sababiyya]⟩,
  ⟨"S26", .umum, ⟨.faMansub, .laYantabiq, .sabab⟩, [.sababiyya]⟩,
  ⟨"S27", .hadd, ⟨.faMarfu, .laYantabiq, .laysaSabab⟩, [.ghayrMadhkur]⟩,
  ⟨"S28", .ghumud, ⟨.faMarfu, .laYantabiq, .ghayrMuallan⟩, [.sababiyya, .ghayrMadhkur]⟩,
  ⟨"S29", .mujib, ⟨.qabl, .laYantabiq, .laYantabiq⟩, [.ghayrMadhkur]⟩,
  ⟨"S30", .umum, ⟨.baad, .laYantabiq, .laYantabiq⟩, [.ghayrMadhkur]⟩]

def halatM : List HalaM := [
  ⟨"S31", .mujib, ⟨.ana, .mutakallimMuayyan⟩, [.muayyan]⟩,
  ⟨"S32", .hadd, ⟨.ana, .laShay⟩, [.laHukm]⟩,
  ⟨"S33", .umum, ⟨.anta, .mukhatabMuayyan⟩, [.muayyan]⟩,
  ⟨"S34", .umum, ⟨.huwa, .mufassirWahid⟩, [.muayyan]⟩,
  ⟨"S35", .mujib, ⟨.huwa, .mufassiran⟩, [.muhtamal]⟩,
  ⟨"S36", .hadd, ⟨.huwa, .laShay⟩, [.laHukm]⟩,
  ⟨"S37", .mujib, ⟨.hadha, .musharWahid⟩, [.muayyan]⟩,
  ⟨"S38", .kharij, ⟨.hadha, .musharIthnan⟩, [.laHukm]⟩,
  ⟨"S39", .umum, ⟨.dhaka, .musharWahid⟩, [.muayyan]⟩,
  ⟨"S40", .kharij, ⟨.dhaka, .laShay⟩, [.laHukm]⟩,
  ⟨"S41", .kharij, ⟨.hadha, .mufassirWahid⟩, [.laHukm]⟩,
  ⟨"S42", .kharij, ⟨.dhaka, .musharIthnan⟩, [.laHukm]⟩]

end Dawabit
end SakkJumla
end Jisr
