/-
# حالاتُ ضابط «نواة التوليد» المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/nawat_tawlid/cases.json` بـ `python3 -I scripts/bina_dawabit_tawlid.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `81a98e5f423945672bfb34db7b6d9d3d5e47fbc8e7f0b163cc37b739b228ea61`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والمصدر قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/nawat_tawlid/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/nawat_tawlid/tajmid.json`. والسندُ في الملفّ المصدر.
-/
import Jisr.TawlidDabit

namespace Jisr
namespace Tawlid
namespace Dabit

def halat : List Hala := [
  ⟨"T01", .mujib, "ع-ل-م", .failiyya, some .insan, some "عالم", [.hayat, .aql, .idrak], some none, [.murakhkhas]⟩,
  ⟨"T02", .mujib, "ع-ل-م", .mubalagha, some .insan, some "علّام", [.hayat, .aql, .idrak], some none, [.murakhkhas]⟩,
  ⟨"T03", .mujib, "ع-ل-م", .sababiyya, some .insan, some "أعلم", [.hayat, .aql, .idrak], some none, [.murakhkhas]⟩,
  ⟨"T04", .mujib, "ك-س-ر", .ala, some .jamad, some "مكسار", [.maddiyya, .salabaNisbiyya], some (some .sulb), [.murakhkhas]⟩,
  ⟨"T05", .hadd, "ع-ل-م", .failiyya, some .hayawan, some "عالم", [.hayat, .aql, .idrak], some none, [.mumtani]⟩,
  ⟨"T06", .hadd, "ع-ل-م", .failiyya, some .jamad, some "عالم", [.hayat, .aql, .idrak], some none, [.mumtani]⟩,
  ⟨"T07", .hadd, "ع-ل-م", .ala, some .jamad, some "معلام", [.maddiyya, .salabaNisbiyya], some (some .sulb), [.mumtani]⟩,
  ⟨"T08", .hadd, "ك-س-ر", .ala, some .insan, some "مكسار", [.maddiyya, .salabaNisbiyya], some (some .sulb), [.mumtani]⟩,
  ⟨"T09", .hadd, "ع-ل-م", .ala, some .nabat, some "معلام", [.maddiyya, .salabaNisbiyya], some (some .sulb), [.mumtani]⟩,
  ⟨"T10", .hadd, "ع-ل-م", .mafuliyya, some .hayawan, some "معلوم", [.qabiliyyaTasawwur], some none, [.mumtani]⟩,
  ⟨"T11", .hadd, "ع-ل-م", .zamanMakan, some .jamad, some "معلم", [.tahayyuz], some none, [.mumtani]⟩,
  ⟨"T12", .hadd, "ك-س-ر", .ala, some .hayawan, some "مكسار", [.maddiyya, .salabaNisbiyya], some (some .sulb), [.mumtani]⟩,
  ⟨"T13", .hadd, "ع-ل-م", .ala, some .insan, some "معلام", [.maddiyya, .salabaNisbiyya], some (some .sulb), [.mumtani]⟩,
  ⟨"T14", .hadd, "ع-ل-م", .mutawaa, some .hayawan, some "انعلم", [.qabiliyyaTasawwur], some none, [.mumtani]⟩,
  ⟨"T15", .hadd, "ع-ل-م", .mubalagha, some .jamad, some "علّام", [.hayat, .aql, .idrak], some none, [.mumtani]⟩,
  ⟨"T16", .kharij, "غائب", .failiyya, some .insan, none, [], none, [.laNawat]⟩,
  ⟨"T17", .kharij, "غائب", .ala, none, none, [], none, [.laNawat]⟩,
  ⟨"T18", .kharij, "ك-س-ر", .mafuliyya, none, some "مكسور", [.maddiyya, .tamasukJuzi], some (some .sulb), [.laJins]⟩,
  ⟨"T19", .kharij, "ع-ل-م", .ala, none, some "معلام", [.maddiyya, .salabaNisbiyya], some (some .sulb), [.laJins]⟩,
  ⟨"T20", .kharij, "غائب", .mutawaa, some .jamad, none, [], none, [.laNawat]⟩,
  ⟨"T21", .kharij, "ع-ل-م", .zamanMakan, none, some "معلم", [.tahayyuz], some none, [.laJins]⟩,
  ⟨"T22", .sura, "ك-س-ر", .failiyya, some .insan, some "كاسر", [.quwwaMuaththira, .haraka], some none, [.laHukm]⟩,
  ⟨"T23", .sura, "ك-س-ر", .mafuliyya, some .jamad, some "مكسور", [.maddiyya, .tamasukJuzi], some (some .sulb), [.laHukm]⟩,
  ⟨"T24", .sura, "ك-س-ر", .mutawaa, some .jamad, some "انكسر", [.maddiyya, .tamasukJuzi], some (some .sulb), [.laHukm]⟩,
  ⟨"T25", .sura, "ك-س-ر", .zamanMakan, some .jamad, some "مكسر", [.tahayyuz], some none, [.laHukm]⟩,
  ⟨"T26", .sura, "ك-س-ر", .mubalagha, some .hayawan, some "كسّار", [.quwwaMuaththira, .haraka], some none, [.laHukm]⟩,
  ⟨"T27", .sura, "ك-س-ر", .sababiyya, some .insan, some "أكسر", [.quwwaMuaththira, .haraka], some none, [.laHukm]⟩,
  ⟨"T28", .sura, "ع-ل-م", .failiyya, some .nabat, some "عالم", [.hayat, .aql, .idrak], some none, [.laHukm]⟩,
  ⟨"T29", .sura, "ع-ل-م", .mafuliyya, some .insan, some "معلوم", [.qabiliyyaTasawwur], some none, [.laHukm]⟩,
  ⟨"T30", .sura, "ع-ل-م", .mutawaa, some .insan, some "انعلم", [.qabiliyyaTasawwur], some none, [.laHukm]⟩,
  ⟨"T31", .sura, "ع-ل-م", .zamanMakan, some .insan, some "معلم", [.tahayyuz], some none, [.laHukm]⟩,
  ⟨"T32", .sura, "ع-ل-م", .sababiyya, some .nabat, some "أعلم", [.hayat, .aql, .idrak], some none, [.laHukm]⟩]

end Dabit
end Tawlid
end Jisr
