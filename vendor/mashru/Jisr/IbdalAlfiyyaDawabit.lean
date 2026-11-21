/-
# حالاتُ ضابط «الإبدال: الواوُ والياءُ في الكلمة» المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/ibdal/cases.json` بـ `python3 -I scripts/bina_dawabit_ibdal.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `732403d34c0ab79d45609d0db1be1ca2abe5ae0c8a732cb216182d080ecfad9d`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والمصدرين (الألفيّةُ، والكتابُ للفهم)، وفي سياقه ما حُقن آليًّا، وطبع بحثُه الأوّلُ أسطرًا من الكتاب خارج أبواب الإبدال (`tahaqquq/dawabit/ibdal/taalif.md` و`mulhaq_1.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/ibdal/tajmid.json` ودُفعت قبل إيداع الشفرة. والكلمةُ خلايا كما قرأها القارئ (`qari --khalaya`)، و`none` ما رفضه؛ والسندُ في الملفّ المصدر.
-/
import Jisr.IbdalAlfiyyaDabit

namespace Jisr.IbdalAlfiyya.Dabit

def halat : List Hala := [
  -- B01 «مُوْقِنٌ»
  ⟨"B01", .mujib, some ⟨[109, 115, 30, 57, 59], false, false⟩, [.ghayrMamnu], some "B02"⟩,
  -- B02 «مُيْقِنٌ»
  ⟨"B02", .hadd, some ⟨[109, 47, 30, 57, 59], false, false⟩, [.mamnu], some "B01"⟩,
  -- B03 «مُوْسِرٌ»
  ⟨"B03", .mujib, some ⟨[109, 115, 82, 61, 59], false, false⟩, [.ghayrMamnu], some "B04"⟩,
  -- B04 «مُيْسِرٌ»
  ⟨"B04", .hadd, some ⟨[109, 47, 82, 61, 59], false, false⟩, [.mamnu], some "B03"⟩,
  -- B05 «يُوْقِنُ»
  ⟨"B05", .mujib, some ⟨[45, 115, 30, 57], false, false⟩, [.ghayrMamnu], some "B06"⟩,
  -- B06 «يُيْقِنُ»
  ⟨"B06", .hadd, some ⟨[45, 47, 30, 57], false, false⟩, [.mamnu], some "B05"⟩,
  -- B07 «هِيْمٌ»
  ⟨"B07", .mujib, some ⟨[6, 47, 109, 59], false, false⟩, [.ghayrMamnu], some "B08"⟩,
  -- B08 «هُيْمٌ»
  ⟨"B08", .hadd, some ⟨[5, 47, 109, 59], false, false⟩, [.mamnu], some "B07"⟩,
  -- B09 «بِيْضٌ»
  ⟨"B09", .mujib, some ⟨[106, 47, 49, 59], false, false⟩, [.ghayrMamnu], some "B10"⟩,
  -- B10 «بُيْضٌ»
  ⟨"B10", .hadd, some ⟨[105, 47, 49, 59], false, false⟩, [.mamnu], some "B09"⟩,
  -- B11 «غِيْدٌ»
  ⟨"B11", .mujib, some ⟨[22, 47, 69, 59], false, false⟩, [.ghayrMamnu], some "B12"⟩,
  -- B12 «غُيْدٌ»
  ⟨"B12", .hadd, some ⟨[21, 47, 69, 59], false, false⟩, [.mamnu], some "B11"⟩,
  -- B13 «مَرْمُوَةٌ»
  ⟨"B13", .mujib, some ⟨[108, 63, 109, 112, 73, 59], false, false⟩, [.ghayrMamnu], some "B14"⟩,
  -- B14 «مَرْمُيَةٌ»
  ⟨"B14", .hadd, some ⟨[108, 63, 109, 44, 73, 59], false, false⟩, [.mamnu], some "B13"⟩,
  -- B15 «رَمُوَانٌ»
  ⟨"B15", .mujib, some ⟨[60, 109, 112, 11, 57, 59], false, false⟩, [.ghayrMamnu], some "B16"⟩,
  -- B16 «رَمُيَانٌ»
  ⟨"B16", .hadd, some ⟨[60, 109, 44, 11, 57, 59], false, false⟩, [.mamnu], some "B15"⟩,
  -- B17 «سَبُعَانُ»
  ⟨"B17", .mujib, some ⟨[80, 105, 12, 11, 57], false, false⟩, [.ghayrMamnu], none⟩,
  -- B18 «مَقْضُوَةٌ»
  ⟨"B18", .mujib, some ⟨[108, 31, 49, 112, 73, 59], false, false⟩, [.ghayrMamnu], some "B19"⟩,
  -- B19 «مَقْضُيَةٌ»
  ⟨"B19", .hadd, some ⟨[108, 31, 49, 44, 73, 59], false, false⟩, [.mamnu], some "B18"⟩,
  -- B20 «قَضُيَانٌ»
  ⟨"B20", .hadd, some ⟨[28, 49, 44, 11, 57, 59], false, false⟩, [.mamnu], none⟩,
  -- B21 «قَرَاطِاسُ»
  ⟨"B21", .umum, some ⟨[28, 60, 11, 66, 11, 81], false, false⟩, [.mamnu], some "B22"⟩,
  -- B22 «قَرَاطِيسُ»
  ⟨"B22", .umum, some ⟨[28, 60, 11, 66, 47, 81], false, false⟩, [.ghayrMamnu], some "B21"⟩,
  -- B23 «غُزَيْالٌ»
  ⟨"B23", .umum, some ⟨[21, 76, 47, 11, 53, 59], false, false⟩, [.mamnu], none⟩,
  -- B24 «شَقِوَ»
  ⟨"B24", .umum, some ⟨[40, 30, 112], false, false⟩, [.mamnu], some "B25"⟩,
  -- B25 «شَقِيَ»
  ⟨"B25", .umum, some ⟨[40, 30, 44], false, false⟩, [.ghayrMamnu], some "B24"⟩,
  -- B26 «غَازِوَةٌ»
  ⟨"B26", .umum, some ⟨[20, 11, 78, 112, 73, 59], false, false⟩, [.mamnu], none⟩,
  -- B27 «غَزِوَانٌ»
  ⟨"B27", .umum, some ⟨[20, 78, 112, 11, 57, 59], false, false⟩, [.mamnu], some "B44"⟩,
  -- B28 «عِوَضٌ»
  ⟨"B28", .umum, some ⟨[14, 112, 49, 59], false, false⟩, [.ghayrMamnu], none⟩,
  -- B29 «مِوْزَانٌ»
  ⟨"B29", .umum, some ⟨[110, 115, 76, 11, 57, 59], false, false⟩, [.ghayrMamnu], none⟩,
  -- B30 «قُاتِلَ»
  ⟨"B30", .umum, some ⟨[29, 11, 74, 52], false, false⟩, [.mamnu], some "B31"⟩,
  -- B31 «قُوتِلَ»
  ⟨"B31", .umum, some ⟨[29, 115, 74, 52], false, false⟩, [.ghayrMamnu], some "B30"⟩,
  -- B32 «ضُايْرِبٌ»
  ⟨"B32", .umum, some ⟨[49, 11, 47, 62, 105, 59], false, false⟩, [.mamnu], none⟩,
  -- B33 «ضُوَيْرِبٌ»
  ⟨"B33", .umum, some ⟨[49, 112, 47, 62, 105, 59], false, false⟩, [.ghayrMamnu], none⟩,
  -- B34 «مُيَسِّرٌ»
  ⟨"B34", .umum, some ⟨[109, 44, 83, 82, 61, 59], false, false⟩, [.ghayrMamnu], none⟩,
  -- B35 «نَهُيَ»
  ⟨"B35", .umum, some ⟨[56, 5, 44], false, false⟩, [.mamnu], some "B36"⟩,
  -- B36 «نَهُوَ»
  ⟨"B36", .umum, some ⟨[56, 5, 112], false, false⟩, [.ghayrMamnu], some "B35"⟩,
  -- B37 «سَيْوِدٌ»
  ⟨"B37", .umum, some ⟨[80, 47, 114, 69, 59], false, false⟩, [.mamnu], none⟩,
  -- B38 «سَيِّدٌ»
  ⟨"B38", .umum, some ⟨[80, 47, 46, 69, 59], false, false⟩, [.ghayrMamnu], none⟩,
  -- B39 «طَوْيٌ»
  ⟨"B39", .umum, some ⟨[64, 115, 45, 59], false, false⟩, [.mamnu], some "B45"⟩,
  -- B40 «طَوِيلٌ»
  ⟨"B40", .umum, some ⟨[64, 114, 47, 53, 59], false, false⟩, [.ghayrMamnu], none⟩,
  -- B41 «ضَيْوَنٌ»
  ⟨"B41", .umum, some ⟨[48, 47, 112, 57, 59], false, false⟩, [.mamnu], none⟩,
  -- B42 «بُويِعَ»
  ⟨"B42", .umum, some ⟨[105, 115, 46, 12], false, false⟩, [.laHukm], none⟩,
  -- B43 «قَوْيَانٌ»
  ⟨"B43", .ghumud, some ⟨[28, 115, 44, 11, 57, 59], false, false⟩, [.mamnu, .ghayrMamnu], none⟩,
  -- B44 «غَزَوَانٌ»
  ⟨"B44", .kharij, some ⟨[20, 76, 112, 11, 57, 59], false, false⟩, [.ghayrMamnu], some "B27"⟩,
  -- B45 «طَوْلٌ»
  ⟨"B45", .kharij, some ⟨[64, 115, 53, 59], false, false⟩, [.ghayrMamnu], some "B39"⟩,
  -- B46 «يُرْضَوَانِ»
  ⟨"B46", .kharij, some ⟨[45, 63, 48, 112, 11, 58], false, false⟩, [.ghayrMamnu], none⟩,
  -- B47 «بَيَعَ»
  ⟨"B47", .kharij, some ⟨[104, 44, 12], false, false⟩, [.ghayrMamnu], none⟩,
  -- B48 «قَاوِلٌ»
  ⟨"B48", .kharij, some ⟨[28, 11, 114, 53, 59], false, false⟩, [.ghayrMamnu], none⟩,
  -- B49 «عُونٌ»
  ⟨"B49", .ghumud, some ⟨[13, 115, 57, 59], false, false⟩, [.mamnu, .ghayrMamnu], none⟩]

end Jisr.IbdalAlfiyya.Dabit
