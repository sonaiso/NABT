/-
# حالاتُ ضابط «قراءة الجملة بالعوامل» المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/tahlil/cases.json` بـ `python3 -I scripts/bina_dawabit_tahlil.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `571c7abb14a660d3268d69b18cd0a270ed7b8778b078c087c80109eb643e937f`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والقطر قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/tahlil/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/tahlil/tajmid.json`. والكلماتُ خلايا كما قرأها القارئ (`qari --khalaya`)، و`none` ما رفضه؛ والسندُ في الملفّ المصدر.
-/
import Jisr.TahlilDabit

namespace Jisr
namespace Tahlil
namespace Dabit

def halat : List Hala := [
  -- T01 «ضَرَبْتُ زَيْدًا»
  ⟨"T01", .mujib, some [⟨[48, 60, 107, 73], false, false⟩, ⟨[76, 47, 68, 59], false, false⟩],
   [.murakhkhas], [[.fil, .maful]], none⟩,
  -- T02 «قَامَ زَيْدٌ»
  ⟨"T02", .mujib, some [⟨[28, 11, 108], false, false⟩, ⟨[76, 47, 69, 59], false, false⟩],
   [.murakhkhas], [[.fil, .fail]], some "T03"⟩,
  -- T03 «قَامَ زَيْدٍ»
  ⟨"T03", .hadd, some [⟨[28, 11, 108], false, false⟩, ⟨[76, 47, 70, 59], false, false⟩],
   [.mumtani], [[.fil, .fail]], some "T02"⟩,
  -- T04 «يَقُومُ زَيْدٌ»
  ⟨"T04", .mujib, some [⟨[44, 29, 115, 109], false, false⟩, ⟨[76, 47, 69, 59], false, false⟩],
   [.murakhkhas], [[.fil, .fail]], some "T05"⟩,
  -- T05 «يَقُومَ زَيْدٌ»
  ⟨"T05", .hadd, some [⟨[44, 29, 115, 108], false, false⟩, ⟨[76, 47, 69, 59], false, false⟩],
   [.mumtani], [[.fil, .fail]], some "T04"⟩,
  -- T06 «لَنْ نَبْرَحَ»
  ⟨"T06", .mujib, some [⟨[52, 59], false, false⟩, ⟨[56, 107, 60, 16], false, false⟩],
   [.murakhkhas], [[.nasib, .fil]], some "T07"⟩,
  -- T07 «لَنْ نَبْرَحُ»
  ⟨"T07", .hadd, some [⟨[52, 59], false, false⟩, ⟨[56, 107, 60, 17], false, false⟩],
   [.mumtani], [[.nasib, .fil]], some "T06"⟩,
  -- T08 «لَمْ يَقُمْ»
  ⟨"T08", .mujib, some [⟨[52, 111], false, false⟩, ⟨[44, 29, 111], false, false⟩],
   [.murakhkhas], [[.jazim, .fil]], none⟩,
  -- T09 «لِيُنْفِقْ»
  ⟨"T09", .mujib, some [⟨[54, 45, 59, 102, 31], false, false⟩],
   [.murakhkhas], [[.jazim, .fil]], none⟩,
  -- T10 «لَا تُؤَاخِذْنَا»
  ⟨"T10", .mujib, some [⟨[52, 11], false, false⟩, ⟨[73, 0, 11, 26, 95, 56, 11], false, false⟩],
   [.murakhkhas], [[.jazim, .fil, .maful]], none⟩,
  -- T11 «لَنْ تَفْعَلُوا»
  ⟨"T11", .mujib, some [⟨[52, 59], false, false⟩, ⟨[72, 103, 12, 53, 115], false, false⟩],
   [.murakhkhas], [[.nasib, .fil]], some "T12"⟩,
  -- T12 «لَنْ تَفْعَلُونَ»
  ⟨"T12", .hadd, some [⟨[52, 59], false, false⟩, ⟨[72, 103, 12, 53, 115, 56], false, false⟩],
   [.mumtani], [[.nasib, .fil]], some "T11"⟩,
  -- T13 «تَفْعَلُونَ»
  ⟨"T13", .mujib, some [⟨[72, 103, 12, 53, 115, 56], false, false⟩],
   [.murakhkhas], [[.fil]], some "T14"⟩,
  -- T14 «تَفْعَلُوا»
  ⟨"T14", .hadd, some [⟨[72, 103, 12, 53, 115], false, false⟩],
   [.mumtani], [[.fil]], some "T13"⟩,
  -- T15 «أَنْ يَغْفِرَ لِي»
  ⟨"T15", .mujib, some [⟨[0, 59], false, false⟩, ⟨[44, 23, 102, 60], false, false⟩, ⟨[54, 47], false, false⟩],
   [.murakhkhas], [[.nasib, .fil, .harfJarr, .majrur]], none⟩,
  -- T16 «أَقُومُ»
  ⟨"T16", .mujib, some [⟨[0, 29, 115, 109], false, false⟩],
   [.murakhkhas], [[.fil]], none⟩,
  -- T17 «أَكْرَمَكَ»
  ⟨"T17", .mujib, some [⟨[0, 35, 60, 108, 32], false, false⟩],
   [.murakhkhas], [[.fil, .maful]], none⟩,
  -- T18 «ضَرَبُوا»
  ⟨"T18", .mujib, some [⟨[48, 60, 105, 115], false, false⟩],
   [.murakhkhas], [[.fil]], none⟩,
  -- T19 «اللَّهُ رَبُّنَا»
  ⟨"T19", .mujib, some [⟨[55, 52, 5], true, true⟩, ⟨[60, 107, 105, 56, 11], false, false⟩],
   [.murakhkhas], [[.mubtada, .khabar, .mudafIlayh]], none⟩,
  -- T20 «قُومُوا»
  ⟨"T20", .mujib, some [⟨[29, 115, 109, 115], false, false⟩],
   [.murakhkhas], [[.fil]], none⟩,
  -- T21 «يُدَحْرِجُ الْمُعَلِّمُونَ الْحَجَرَ»
  ⟨"T21", .mujib, some [⟨[45, 68, 19, 62, 37], false, false⟩, ⟨[55, 109, 12, 55, 54, 109, 115, 56], true, true⟩, ⟨[55, 16, 36, 60], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .maful]], none⟩,
  -- T22 «يَدَحْرِجُ الْوَلَدُ الْحَجَرَ»
  ⟨"T22", .hadd, some [⟨[44, 68, 19, 62, 37], false, false⟩, ⟨[55, 112, 52, 69], true, true⟩, ⟨[55, 16, 36, 60], true, true⟩],
   [.mumtani], [[.fil, .fail, .maful]], none⟩,
  -- T23 «أَنْ يَكْتُبْنَ»
  ⟨"T23", .umum, some [⟨[0, 59], false, false⟩, ⟨[44, 35, 73, 107, 56], false, false⟩],
   [.murakhkhas], [[.nasib, .fil]], none⟩,
  -- T24 «كَتَبَ الْوَلَدَانِ»
  ⟨"T24", .umum, some [⟨[32, 72, 104], false, false⟩, ⟨[55, 112, 52, 68, 11, 58], true, true⟩],
   [.murakhkhas], [[.fil, .fail]], some "T25"⟩,
  -- T25 «كَتَبَا الْوَلَدَانِ»
  ⟨"T25", .hadd, some [⟨[32, 72, 104, 11], false, false⟩, ⟨[55, 112, 52, 68, 11, 58], true, true⟩],
   [.mumtani], [[.fil, .fail]], some "T24"⟩,
  -- T26 «كَتَبَ الْمُعَلِّمُونَ»
  ⟨"T26", .umum, some [⟨[32, 72, 104], false, false⟩, ⟨[55, 109, 12, 55, 54, 109, 115, 56], true, true⟩],
   [.murakhkhas], [[.fil, .fail]], some "T27"⟩,
  -- T27 «كَتَبُوا الْمُعَلِّمُونَ»
  ⟨"T27", .hadd, some [⟨[32, 72, 105, 115], false, false⟩, ⟨[55, 109, 12, 55, 54, 109, 115, 56], true, true⟩],
   [.mumtani], [[.fil, .fail]], some "T26"⟩,
  -- T28 «الْوَلَدُ قَائِمٌ»
  ⟨"T28", .umum, some [⟨[55, 112, 52, 69], true, true⟩, ⟨[28, 11, 2, 109, 59], false, false⟩],
   [.murakhkhas], [[.mubtada, .khabar]], some "T29"⟩,
  -- T29 «الْوَلَدُ قَائِمًا»
  ⟨"T29", .hadd, some [⟨[55, 112, 52, 69], true, true⟩, ⟨[28, 11, 2, 108, 59], false, false⟩],
   [.mumtani], [[.mubtada, .khabar]], some "T28"⟩,
  -- T30 «الرَّجُلُ فِي الدَّارِ»
  ⟨"T30", .umum, some [⟨[63, 60, 37, 53], true, true⟩, ⟨[102, 47], false, false⟩, ⟨[71, 68, 11, 62], true, true⟩],
   [.murakhkhas], [[.mubtada, .harfJarr, .majrur]], some "T31"⟩,
  -- T31 «الرَّجُلُ فِي الدَّارُ»
  ⟨"T31", .hadd, some [⟨[63, 60, 37, 53], true, true⟩, ⟨[102, 47], false, false⟩, ⟨[71, 68, 11, 61], true, true⟩],
   [.mumtani], [[.mubtada, .harfJarr, .majrur]], some "T30"⟩,
  -- T32 «رَجُلٌ فِي الدَّارِ»
  ⟨"T32", .hadd, some [⟨[60, 37, 53, 59], false, false⟩, ⟨[102, 47], false, false⟩, ⟨[71, 68, 11, 62], true, true⟩],
   [.mumtani], [[.mubtada, .harfJarr, .majrur]], none⟩,
  -- T33 «الْوَلَدُ كَهُ»
  ⟨"T33", .hadd, some [⟨[55, 112, 52, 69], true, true⟩, ⟨[32, 5], false, false⟩],
   [.mumtani], [[.mubtada, .harfJarr, .majrur]], none⟩,
  -- T34 «الْخَيْرُ فِيهِ»
  ⟨"T34", .umum, some [⟨[55, 24, 47, 61], true, true⟩, ⟨[102, 47, 6], false, false⟩],
   [.murakhkhas], [[.mubtada, .harfJarr, .majrur]], none⟩,
  -- T35 «كِتَابُ الْوَلَدِ جَدِيدٌ»
  ⟨"T35", .umum, some [⟨[34, 72, 11, 105], false, false⟩, ⟨[55, 112, 52, 70], true, true⟩, ⟨[36, 70, 47, 69, 59], false, false⟩],
   [.murakhkhas], [[.mubtada, .mudafIlayh, .khabar]], some "T36"⟩,
  -- T36 «كِتَابٌ الْوَلَدِ جَدِيدٌ»
  ⟨"T36", .hadd, some [⟨[34, 72, 11, 105, 59], false, false⟩, ⟨[55, 112, 52, 70], true, true⟩, ⟨[36, 70, 47, 69, 59], false, false⟩],
   [.mumtani], [[.mubtada, .mudafIlayh, .khabar]], some "T35"⟩,
  -- T37 «كِتَابُكَ جَدِيدٌ»
  ⟨"T37", .umum, some [⟨[34, 72, 11, 105, 32], false, false⟩, ⟨[36, 70, 47, 69, 59], false, false⟩],
   [.murakhkhas], [[.mubtada, .mudafIlayh, .khabar]], none⟩,
  -- T38 «قَامَ غُلَامَاهُ»
  ⟨"T38", .umum, some [⟨[28, 11, 108], false, false⟩, ⟨[21, 52, 11, 108, 11, 5], false, false⟩],
   [.murakhkhas], [[.fil, .fail, .mudafIlayh]], some "T39"⟩,
  -- T39 «قَامَ غُلَامَانِهِ»
  ⟨"T39", .hadd, some [⟨[28, 11, 108], false, false⟩, ⟨[21, 52, 11, 108, 11, 58, 6], false, false⟩],
   [.mumtani], [[.fil, .fail, .mudafIlayh]], some "T38"⟩,
  -- T40 «ضَرَبَ الْوَلَدُ الزَّيْدَيْنِ»
  ⟨"T40", .umum, some [⟨[48, 60, 104], false, false⟩, ⟨[55, 112, 52, 69], true, true⟩, ⟨[79, 76, 47, 68, 47, 58], true, true⟩],
   [.murakhkhas], [[.fil, .fail, .maful]], some "T41"⟩,
  -- T41 «ضَرَبَ الْوَلَدُ الزَّيْدَانِ»
  ⟨"T41", .hadd, some [⟨[48, 60, 104], false, false⟩, ⟨[55, 112, 52, 69], true, true⟩, ⟨[79, 76, 47, 68, 11, 58], true, true⟩],
   [.mumtani], [[.fil, .fail, .maful]], some "T40"⟩,
  -- T42 «لَا يَكْتُبُ الْوَلَدُ»
  ⟨"T42", .umum, some [⟨[52, 11], false, false⟩, ⟨[44, 35, 73, 105], false, false⟩, ⟨[55, 112, 52, 69], true, true⟩],
   [.murakhkhas], [[.nafiya, .fil, .fail]], some "T43"⟩,
  -- T43 «لَا يَكْتُبَ الْوَلَدُ»
  ⟨"T43", .hadd, some [⟨[52, 11], false, false⟩, ⟨[44, 35, 73, 104], false, false⟩, ⟨[55, 112, 52, 69], true, true⟩],
   [.mumtani], [[.nafiya, .fil, .fail]], some "T42"⟩,
  -- T44 «لَا تَكْتُبُونَهُ»
  ⟨"T44", .umum, some [⟨[52, 11], false, false⟩, ⟨[72, 35, 73, 105, 115, 56, 5], false, false⟩],
   [.murakhkhas], [[.nafiya, .fil, .maful]], none⟩,
  -- T45 «وَلَا تَكْتُبُوا بِهِ»
  ⟨"T45", .umum, some [⟨[112, 52, 11], false, false⟩, ⟨[72, 35, 73, 105, 115], false, false⟩, ⟨[106, 6], false, false⟩],
   [.murakhkhas], [[.rabit, .jazim, .fil, .harfJarr, .majrur]], none⟩,
  -- T46 «فَلْيَكْتُبْ زَيْدٌ»
  ⟨"T46", .umum, some [⟨[100, 55, 44, 35, 73, 107], false, false⟩, ⟨[76, 47, 69, 59], false, false⟩],
   [.murakhkhas], [[.rabit, .jazim, .fil, .fail]], some "T47"⟩,
  -- T47 «فَلْيَكْتُبُ زَيْدٌ»
  ⟨"T47", .hadd, some [⟨[100, 55, 44, 35, 73, 105], false, false⟩, ⟨[76, 47, 69, 59], false, false⟩],
   [.mumtani], [[.rabit, .jazim, .fil, .fail]], some "T46"⟩,
  -- T48 «أَكْتُبُ الْوَلَدُ»
  ⟨"T48", .hadd, some [⟨[0, 35, 73, 105], false, false⟩, ⟨[55, 112, 52, 69], true, true⟩],
   [.mumtani], [[.fil, .fail]], none⟩,
  -- T49 «قَامَ كِلَا الرَّجُلَيْنِ»
  ⟨"T49", .kharij, some [⟨[28, 11, 108], false, false⟩, ⟨[34, 52, 11], false, false⟩, ⟨[63, 60, 37, 52, 47, 58], true, true⟩],
   [.laHukm], [[.fil, .fail, .mudafIlayh]], none⟩,
  -- T50 «قَامَ الضَّارِبُ الرَّجُلِ»
  ⟨"T50", .kharij, some [⟨[28, 11, 108], false, false⟩, ⟨[51, 48, 11, 62, 105], true, true⟩, ⟨[63, 60, 37, 54], true, true⟩],
   [.laHukm], [[.fil, .fail, .mudafIlayh]], none⟩,
  -- T51 «رَجُلٌ فِي الدَّارِ قَائِمٌ»
  ⟨"T51", .kharij, some [⟨[60, 37, 53, 59], false, false⟩, ⟨[102, 47], false, false⟩, ⟨[71, 68, 11, 62], true, true⟩, ⟨[28, 11, 2, 109, 59], false, false⟩],
   [.laHukm], [[.mubtada, .harfJarr, .majrur, .khabar]], none⟩,
  -- T52 «أَنْ كَتَبَ الْوَلَدُ»
  ⟨"T52", .kharij, some [⟨[0, 59], false, false⟩, ⟨[32, 72, 104], false, false⟩, ⟨[55, 112, 52, 69], true, true⟩],
   [.laHukm], [[.nasib, .fil, .fail]], none⟩,
  -- T53 «لَنْ كَتَبَ زَيْدٌ»
  ⟨"T53", .kharij, some [⟨[52, 59], false, false⟩, ⟨[32, 72, 104], false, false⟩, ⟨[76, 47, 69, 59], false, false⟩],
   [.laHukm], [[.nasib, .fil, .fail]], none⟩,
  -- T54 «لَا يَكْتُبْنَ»
  ⟨"T54", .ghumud, some [⟨[52, 11], false, false⟩, ⟨[44, 35, 73, 107, 56], false, false⟩],
   [.murakhkhas], [[.nafiya, .fil], [.jazim, .fil]], none⟩,
  -- T55 «كَاتِبُ الدَّرْسِ حَاضِرٌ»
  ⟨"T55", .ghumud, some [⟨[32, 11, 74, 105], false, false⟩, ⟨[71, 68, 63, 82], true, true⟩, ⟨[16, 11, 50, 61, 59], false, false⟩],
   [.murakhkhas, .mumtani], [[.mubtada, .mudafIlayh, .khabar]], none⟩]

end Dabit
end Tahlil
end Jisr
