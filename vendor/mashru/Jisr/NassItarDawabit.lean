/-
# حالاتُ ضابط «من النصّ إلى الإطار» المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/nass/cases.json` بـ `python3 -I scripts/bina_dawabit_nass.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `a2e37d38a9be0ce4fe69c252daba8ba247726eb1eeaed43b1a1f615955ffe2ff`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والنطاق قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/nass/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/nass/tajmid.json`. والكلماتُ خلايا كما قرأها القارئ (`qari --khalaya`)، و`none` ما رفضه؛ والسندُ في الملفّ المصدر.
-/
import Jisr.NassItarDabit

namespace Jisr
namespace NassItar
namespace Dabit

def halat : List Hala := [
  -- N01 «قَامَ زَيْدٌ»
  ⟨"N01", .mujib, some [⟨[28, 11, 108], false, false⟩, ⟨[76, 47, 69, 59], false, false⟩],
   [.murakhkhas], [[.fil, .fail]], some "N02"⟩,
  -- N02 «قَامَ زَيْدًا»
  ⟨"N02", .hadd, some [⟨[28, 11, 108], false, false⟩, ⟨[76, 47, 68, 59], false, false⟩],
   [.mumtani], [[.fil, .fail]], some "N01"⟩,
  -- N03 «جَاءَ أَبُو الْوَلَدِ»
  ⟨"N03", .mujib, some [⟨[36, 11, 0], false, false⟩, ⟨[0, 105, 115], false, false⟩, ⟨[55, 112, 52, 70], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .mudafIlayh]], some "N04"⟩,
  -- N04 «جَاءَ أَبِي الْوَلَدِ»
  ⟨"N04", .hadd, some [⟨[36, 11, 0], false, false⟩, ⟨[0, 106, 47], false, false⟩, ⟨[55, 112, 52, 70], true, true⟩],
   [.mumtani], [[.fil, .fail, .mudafIlayh]], some "N03"⟩,
  -- N05 «جَاءَ أَبَا الْوَلَدِ»
  ⟨"N05", .mujib, some [⟨[36, 11, 0], false, false⟩, ⟨[0, 104, 11], false, false⟩, ⟨[55, 112, 52, 70], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .mudafIlayh]], none⟩,
  -- N06 «ضَرَبَ الرَّجُلُ أَبَا الْوَلَدِ»
  ⟨"N06", .mujib, some [⟨[48, 60, 104], false, false⟩, ⟨[63, 60, 37, 53], true, true⟩, ⟨[0, 104, 11], false, false⟩, ⟨[55, 112, 52, 70], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .maful, .mudafIlayh]], some "N07"⟩,
  -- N07 «ضَرَبَ الرَّجُلُ أَبُو الْوَلَدِ»
  ⟨"N07", .hadd, some [⟨[48, 60, 104], false, false⟩, ⟨[63, 60, 37, 53], true, true⟩, ⟨[0, 105, 115], false, false⟩, ⟨[55, 112, 52, 70], true, true⟩],
   [.mumtani], [[.fil, .fail, .maful, .mudafIlayh]], some "N06"⟩,
  -- N08 «مِنْ أَبِ الرَّجُلِ»
  ⟨"N08", .mujib, some [⟨[110, 59], false, false⟩, ⟨[0, 106], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.murakhkhas], [[.harfJarr, .majrur, .mudafIlayh]], none⟩,
  -- N09 «جَاءَ أَبٌ»
  ⟨"N09", .umum, some [⟨[36, 11, 0], false, false⟩, ⟨[0, 105, 59], false, false⟩],
   [.murakhkhas], [[.fil, .fail]], some "N10"⟩,
  -- N10 «جَاءَ أَبُو»
  ⟨"N10", .hadd, some [⟨[36, 11, 0], false, false⟩, ⟨[0, 105, 115], false, false⟩],
   [.mumtani], [[.fil, .fail]], some "N09"⟩,
  -- N11 «جَاءَ أَبٌ الرَّجُلِ»
  ⟨"N11", .hadd, some [⟨[36, 11, 0], false, false⟩, ⟨[0, 105, 59], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.mumtani], [[.fil, .fail, .mudafIlayh]], none⟩,
  -- N12 «ضَرَبَ أَبٌ أَخَا الرَّجُلِ»
  ⟨"N12", .umum, some [⟨[48, 60, 104], false, false⟩, ⟨[0, 105, 59], false, false⟩, ⟨[0, 24, 11], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .maful, .mudafIlayh]], some "N13"⟩,
  -- N13 «ضَرَبَ أَبُو أَخَا الرَّجُلِ»
  ⟨"N13", .hadd, some [⟨[48, 60, 104], false, false⟩, ⟨[0, 105, 115], false, false⟩, ⟨[0, 24, 11], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.mumtani], [[.fil, .fail, .maful, .mudafIlayh]], some "N12"⟩,
  -- N14 «مِنْ أَخِي الرَّجُلِ»
  ⟨"N14", .mujib, some [⟨[110, 59], false, false⟩, ⟨[0, 26, 47], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.murakhkhas], [[.harfJarr, .majrur, .mudafIlayh]], some "N15"⟩,
  -- N15 «مِنْ أَخُو الرَّجُلِ»
  ⟨"N15", .hadd, some [⟨[110, 59], false, false⟩, ⟨[0, 25, 115], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.mumtani], [[.harfJarr, .majrur, .mudafIlayh]], some "N14"⟩,
  -- N16 «عَنْ أَخَا الرَّجُلِ»
  ⟨"N16", .mujib, some [⟨[12, 59], false, false⟩, ⟨[0, 24, 11], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.murakhkhas], [[.harfJarr, .majrur, .mudafIlayh]], none⟩,
  -- N17 «جَاءَ الْأَخُ الرَّجُلِ»
  ⟨"N17", .hadd, some [⟨[36, 11, 0], false, false⟩, ⟨[55, 0, 25], true, true⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.mumtani], [[.fil, .fail, .mudafIlayh]], none⟩,
  -- N18 «سَمِعَ الْوَلَدُ أَخًا»
  ⟨"N18", .umum, some [⟨[80, 110, 12], false, false⟩, ⟨[55, 112, 52, 69], true, true⟩, ⟨[0, 24, 59], false, false⟩],
   [.murakhkhas], [[.fil, .fail, .maful]], some "N19"⟩,
  -- N19 «سَمِعَ الْوَلَدُ أَخُو»
  ⟨"N19", .hadd, some [⟨[80, 110, 12], false, false⟩, ⟨[55, 112, 52, 69], true, true⟩, ⟨[0, 25, 115], false, false⟩],
   [.mumtani], [[.fil, .fail, .maful]], some "N18"⟩,
  -- N20 «جَاءَ حَمُو الْمَرْأَةِ»
  ⟨"N20", .mujib, some [⟨[36, 11, 0], false, false⟩, ⟨[16, 109, 115], false, false⟩, ⟨[55, 108, 63, 0, 74], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .mudafIlayh]], some "N21"⟩,
  -- N21 «جَاءَ حَمِي الْمَرْأَةِ»
  ⟨"N21", .hadd, some [⟨[36, 11, 0], false, false⟩, ⟨[16, 110, 47], false, false⟩, ⟨[55, 108, 63, 0, 74], true, true⟩],
   [.mumtani], [[.fil, .fail, .mudafIlayh]], some "N20"⟩,
  -- N22 «زَارَ الرَّجُلُ حَمَا الْمَرْأَةِ»
  ⟨"N22", .mujib, some [⟨[76, 11, 60], false, false⟩, ⟨[63, 60, 37, 53], true, true⟩, ⟨[16, 108, 11], false, false⟩, ⟨[55, 108, 63, 0, 74], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .maful, .mudafIlayh]], none⟩,
  -- N23 «جَاءَ هَنُو الرَّجُلِ»
  ⟨"N23", .mujib, some [⟨[36, 11, 0], false, false⟩, ⟨[4, 57, 115], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .mudafIlayh]], some "N24"⟩,
  -- N24 «جَاءَ هَنَا الرَّجُلِ»
  ⟨"N24", .hadd, some [⟨[36, 11, 0], false, false⟩, ⟨[4, 56, 11], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.mumtani], [[.fil, .fail, .mudafIlayh]], some "N23"⟩,
  -- N25 «جَاءَ هَنُ الرَّجُلِ»
  ⟨"N25", .mujib, some [⟨[36, 11, 0], false, false⟩, ⟨[4, 57], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .mudafIlayh]], none⟩,
  -- N26 «عَلَى هَنٍ»
  ⟨"N26", .mujib, some [⟨[12, 52, 11], false, false⟩, ⟨[4, 58, 59], false, false⟩],
   [.murakhkhas], [[.harfJarr, .majrur]], none⟩,
  -- N27 «طَابَ فُو الرَّجُلِ»
  ⟨"N27", .mujib, some [⟨[64, 11, 104], false, false⟩, ⟨[101, 115], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .mudafIlayh]], some "N28"⟩,
  -- N28 «طَابَ فَا الرَّجُلِ»
  ⟨"N28", .hadd, some [⟨[64, 11, 104], false, false⟩, ⟨[100, 11], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.mumtani], [[.fil, .fail, .mudafIlayh]], some "N27"⟩,
  -- N29 «فَتَحَ الطَّبِيبُ فَا الرَّجُلِ»
  ⟨"N29", .mujib, some [⟨[100, 72, 16], false, false⟩, ⟨[67, 64, 106, 47, 105], true, true⟩, ⟨[100, 11], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .maful, .mudafIlayh]], some "N30"⟩,
  -- N30 «فَتَحَ الطَّبِيبُ فِي الرَّجُلِ»
  ⟨"N30", .hadd, some [⟨[100, 72, 16], false, false⟩, ⟨[67, 64, 106, 47, 105], true, true⟩, ⟨[102, 47], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.mumtani], [[.fil, .fail, .maful, .mudafIlayh]], some "N29"⟩,
  -- N31 «فِي فِي الرَّجُلِ»
  ⟨"N31", .mujib, some [⟨[102, 47], false, false⟩, ⟨[102, 47], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.murakhkhas], [[.harfJarr, .majrur, .mudafIlayh]], none⟩,
  -- N32 «طَابَ فَمُ الرَّجُلِ»
  ⟨"N32", .umum, some [⟨[64, 11, 104], false, false⟩, ⟨[100, 109], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .mudafIlayh]], some "N33"⟩,
  -- N33 «طَابَ فَمُو الرَّجُلِ»
  ⟨"N33", .hadd, some [⟨[64, 11, 104], false, false⟩, ⟨[100, 109, 115], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.mumtani], [[.fil, .fail, .mudafIlayh]], some "N32"⟩,
  -- N34 «جَاءَ ذُو الْمَالِ»
  ⟨"N34", .mujib, some [⟨[36, 11, 0], false, false⟩, ⟨[93, 115], false, false⟩, ⟨[55, 108, 11, 54], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .mudafIlayh]], some "N35"⟩,
  -- N35 «جَاءَ ذَا الْمَالِ»
  ⟨"N35", .hadd, some [⟨[36, 11, 0], false, false⟩, ⟨[92, 11], false, false⟩, ⟨[55, 108, 11, 54], true, true⟩],
   [.mumtani], [[.fil, .fail, .mudafIlayh]], some "N34"⟩,
  -- N36 «عَرَفَ الرَّجُلُ ذَا الْمَالِ»
  ⟨"N36", .mujib, some [⟨[12, 60, 100], false, false⟩, ⟨[63, 60, 37, 53], true, true⟩, ⟨[92, 11], false, false⟩, ⟨[55, 108, 11, 54], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .maful, .mudafIlayh]], some "N37"⟩,
  -- N37 «عَرَفَ الرَّجُلُ ذِي الْمَالِ»
  ⟨"N37", .hadd, some [⟨[12, 60, 100], false, false⟩, ⟨[63, 60, 37, 53], true, true⟩, ⟨[94, 47], false, false⟩, ⟨[55, 108, 11, 54], true, true⟩],
   [.mumtani], [[.fil, .fail, .maful, .mudafIlayh]], some "N36"⟩,
  -- N38 «إِلَى ذِي الْمَالِ»
  ⟨"N38", .mujib, some [⟨[2, 52, 11], false, false⟩, ⟨[94, 47], false, false⟩, ⟨[55, 108, 11, 54], true, true⟩],
   [.murakhkhas], [[.harfJarr, .majrur, .mudafIlayh]], some "N39"⟩,
  -- N39 «إِلَى ذُو الْمَالِ»
  ⟨"N39", .hadd, some [⟨[2, 52, 11], false, false⟩, ⟨[93, 115], false, false⟩, ⟨[55, 108, 11, 54], true, true⟩],
   [.mumtani], [[.harfJarr, .majrur, .mudafIlayh]], some "N38"⟩,
  -- N40 «جَاءَ ذُو»
  ⟨"N40", .hadd, some [⟨[36, 11, 0], false, false⟩, ⟨[93, 115], false, false⟩],
   [.mumtani], [[.fil, .fail]], none⟩,
  -- N41 «ضَرَبَ الرَّجُلُ الْوَلَدَ»
  ⟨"N41", .umum, some [⟨[48, 60, 104], false, false⟩, ⟨[63, 60, 37, 53], true, true⟩, ⟨[55, 112, 52, 68], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .maful]], some "N42"⟩,
  -- N42 «ضَرَبَ الرَّجُلُ الْوَلَدِ»
  ⟨"N42", .hadd, some [⟨[48, 60, 104], false, false⟩, ⟨[63, 60, 37, 53], true, true⟩, ⟨[55, 112, 52, 70], true, true⟩],
   [.mumtani], [[.fil, .fail, .mudafIlayh]], some "N41"⟩,
  -- N43 «فِي الدَّارِ»
  ⟨"N43", .umum, some [⟨[102, 47], false, false⟩, ⟨[71, 68, 11, 62], true, true⟩],
   [.murakhkhas], [[.harfJarr, .majrur]], some "N44"⟩,
  -- N44 «فِي الدَّارَ»
  ⟨"N44", .hadd, some [⟨[102, 47], false, false⟩, ⟨[71, 68, 11, 60], true, true⟩],
   [.mumtani], [[.harfJarr, .majrur]], some "N43"⟩,
  -- N45 «جَاءَ الضَّارِبُ الرَّجُلِ»
  ⟨"N45", .mujib, some [⟨[36, 11, 0], false, false⟩, ⟨[51, 48, 11, 62, 105], true, true⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .mudafIlayh]], none⟩,
  -- N46 «جَاءَ أَبًا»
  ⟨"N46", .kharij, some [⟨[36, 11, 0], false, false⟩, ⟨[0, 104, 59], false, false⟩],
   [.laHukm], [[.fil, .fail]], none⟩,
  -- N47 «مِنْ أَخَا»
  ⟨"N47", .kharij, some [⟨[110, 59], false, false⟩, ⟨[0, 24, 11], false, false⟩],
   [.laHukm], [[.harfJarr, .majrur]], none⟩,
  -- N48 «ضَرَبَ الرَّجُلُ حَمَا»
  ⟨"N48", .kharij, some [⟨[48, 60, 104], false, false⟩, ⟨[63, 60, 37, 53], true, true⟩, ⟨[16, 108, 11], false, false⟩],
   [.laHukm], [[.fil, .fail, .maful]], none⟩,
  -- N49 «جَاءَ الْأَخَا»
  ⟨"N49", .kharij, some [⟨[36, 11, 0], false, false⟩, ⟨[55, 0, 24, 11], true, true⟩],
   [.laHukm], [[.fil, .fail]], none⟩,
  -- N50 «ضَرَبَ أَبَا أَخَا الرَّجُلِ»
  ⟨"N50", .kharij, some [⟨[48, 60, 104], false, false⟩, ⟨[0, 104, 11], false, false⟩, ⟨[0, 24, 11], false, false⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.laHukm], [[.fil, .fail, .maful, .mudafIlayh]], none⟩]

end Dabit
end NassItar
end Jisr
