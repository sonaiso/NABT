/-
# حالاتُ ضابط «أثر العُقَد» المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/athar/cases.json` بـ `python3 -I scripts/bina_dawabit_athar.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `7bd6204545366af11dfca85769739d65ff23a3d863139ffee90f1c49d6f032ab`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والنطاق، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/athar/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/athar/tajmid.json`. والجملةُ نصُّها كما كُتبت؛ والسندُ في الملفّ المصدر.
-/
import Nizam.AtharDabit

namespace Nizam.Athar
namespace Dabit

def halat : List Hala := [
  -- A01
  ⟨"A01", .quwwa, .mujib, "هَلْ قَامَ زَيْدٌ",
   [.insha], [], some "A02"⟩,
  -- A02
  ⟨"A02", .quwwa, .mujib, "مَا قَامَ زَيْدٌ",
   [.nafy], [], some "A01"⟩,
  -- A03
  ⟨"A03", .quwwa, .mujib, "أَعْطِنِي الْكِتَابَ",
   [.insha], [], some "A04"⟩,
  -- A04
  ⟨"A04", .quwwa, .umum, "أَعْطَيْتَنِي الْكِتَابَ",
   [.ithbat], [], some "A03"⟩,
  -- A05
  ⟨"A05", .quwwa, .mujib, "الَّذِي يَأْتِينِي فَلَهُ دِرْهَمَانِ",
   [.taliq], [], some "A06"⟩,
  -- A06
  ⟨"A06", .quwwa, .hadd, "الَّذِي يَأْتِينِي لَهُ دِرْهَمَانِ",
   [.ithbat], [], some "A05"⟩,
  -- A07
  ⟨"A07", .quwwa, .hadd, "أَلَمْ نَشْرَحْ",
   [.insha], [], some "A08"⟩,
  -- A08
  ⟨"A08", .quwwa, .mujib, "لَمْ نَشْرَحْ",
   [.nafy], [], some "A07"⟩,
  -- A09
  ⟨"A09", .quwwa, .mujib, "لَا تُؤَاخِذْنَا",
   [.insha], [], some "A10"⟩,
  -- A10
  ⟨"A10", .quwwa, .hadd, "لَا تُؤَاخِذُنَا",
   [.nafy], [], some "A09"⟩,
  -- A11
  ⟨"A11", .quwwa, .mujib, "لَمَّا يَقْضِ",
   [.nafy], [], none⟩,
  -- A12
  ⟨"A12", .quwwa, .mujib, "إِنْ تَأْتِنِي آتِكَ",
   [.taliq], [], none⟩,
  -- A13
  ⟨"A13", .quwwa, .mujib, "آتِيكَ إِنْ أَتَيْتَنِي",
   [.taliq], [], none⟩,
  -- A14
  ⟨"A14", .quwwa, .mujib, "ائْتِنِي آتِكَ",
   [.taliq], [], none⟩,
  -- A15
  ⟨"A15", .quwwa, .mujib, "حَيْثُمَا تَكُنْ أَكُنْ",
   [.taliq], [], none⟩,
  -- A16
  ⟨"A16", .quwwa, .hadd, "حَيْثُ تَكُونُ أَكُونُ",
   [.ithbat], [], none⟩,
  -- A17
  ⟨"A17", .quwwa, .hadd, "مَا تَدُومُ لِي أَدُومُ لَكَ",
   [.ithbat], [], none⟩,
  -- A18
  ⟨"A18", .quwwa, .hadd, "أَنَا طَالِبٌ كَذَا",
   [.ithbat], [], none⟩,
  -- A19
  ⟨"A19", .quwwa, .hadd, "وَإِذَا مَا غَضِبُوا هُمْ يَغْفِرُونَ",
   [.ithbat], [], none⟩,
  -- A20
  ⟨"A20", .quwwa, .hadd, "وَاللَّيْلِ إِذَا يَغْشَى",
   [.insha], [], none⟩,
  -- A21
  ⟨"A21", .quwwa, .umum, "مَتَى تُسَافِرُ",
   [.insha], [], none⟩,
  -- A22
  ⟨"A22", .quwwa, .umum, "لَيْتَهُ عِنْدَنَا",
   [.insha], [], none⟩,
  -- A23
  ⟨"A23", .quwwa, .umum, "مَا زَيْدٌ قَائِمًا",
   [.nafy], [], none⟩,
  -- A24
  ⟨"A24", .quwwa, .ghumud, "بِعْتُكَ الدَّارَ",
   [.ithbat, .insha], [], none⟩,
  -- A25
  ⟨"A25", .quwwa, .ghumud, "أَعْتَقْتُ عَبْدِي",
   [.ithbat, .insha], [], none⟩,
  -- A26
  ⟨"A26", .quwwa, .kharij, "حَبَّذَا زَيْدٌ",
   [.laHukm], [], none⟩,
  -- A27
  ⟨"A27", .quwwa, .kharij, "نِعْمَ الرَّجُلُ زَيْدٌ",
   [.laHukm], [], none⟩,
  -- A28
  ⟨"A28", .quwwa, .kharij, "أَكْرِمْ بِزَيْدٍ",
   [.laHukm], [], none⟩,
  -- A29
  ⟨"A29", .quwwa, .mujib, "إِنْ جَاءَنِي فَوَاللَّهِ لَأُكْرِمَنَّهُ",
   [.taliq], [], none⟩,
  -- A30
  ⟨"A30", .qayd, .mujib, "مَطْلُ الْغَنِيِّ ظُلْمٌ",
   [], [.sinf .sifa], some "A31"⟩,
  -- A31
  ⟨"A31", .qayd, .hadd, "مَطْلُ زَيْدٍ ظُلْمٌ",
   [], [.laQayd], some "A30"⟩,
  -- A32
  ⟨"A32", .qayd, .mujib, "فِي الْغَنَمِ زَكَاةٌ",
   [], [.laQayd], some "A33"⟩,
  -- A33
  ⟨"A33", .qayd, .mujib, "فِي السَّائِمَةِ زَكَاةٌ",
   [], [.sinf .sifa], some "A32"⟩,
  -- A34
  ⟨"A34", .qayd, .umum, "صَلِّ رَكْعَتَيْنِ",
   [], [.sinf .adad], some "A35"⟩,
  -- A35
  ⟨"A35", .qayd, .umum, "صَلِّ الظُّهْرَ",
   [], [.laQayd], some "A34"⟩,
  -- A36
  ⟨"A36", .qayd, .mujib, "وَإِنْ كُنَّ أُولَاتِ حَمْلٍ فَأَنْفِقُوا عَلَيْهِنَّ",
   [], [.sinf .shart], none⟩,
  -- A37
  ⟨"A37", .qayd, .umum, "مَنْ جَاءَكَ فَأَكْرِمْهُ",
   [], [.sinf .shart], none⟩,
  -- A38
  ⟨"A38", .qayd, .mujib, "ثُمَّ أَتِمُّوا الصِّيَامَ إِلَى اللَّيْلِ",
   [], [.sinf .ghaya], none⟩,
  -- A39
  ⟨"A39", .qayd, .mujib, "وَلَا تَقْرَبُوهُنَّ حَتَّى يَطْهُرْنَ",
   [], [.sinf .ghaya], none⟩,
  -- A40
  ⟨"A40", .qayd, .mujib, "فَاجْلِدُوهُمْ ثَمَانِينَ جَلْدَةً",
   [], [.sinf .adad], none⟩,
  -- A41
  ⟨"A41", .qayd, .mujib, "فَأَمِّرُوا عَلَيْكُمْ أَحَدَكُمْ",
   [], [.sinf .adad], none⟩,
  -- A42
  ⟨"A42", .qayd, .mujib, "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ",
   [], [.laQayd], none⟩,
  -- A43
  ⟨"A43", .qayd, .umum, "قَامَ أَبُو بَكْرٍ",
   [], [.laQayd], none⟩,
  -- A44
  ⟨"A44", .qayd, .hadd, "ادْعُهُمْ إِلَى التَّحَوُّلِ مِنْ دَارِهِمْ",
   [], [.laQayd], none⟩,
  -- A45
  ⟨"A45", .qayd, .ghumud, "أَكْرِمِ الْأَمِينَ",
   [], [.sinf .sifa, .laQayd], none⟩,
  -- A46
  ⟨"A46", .qayd, .mujib, "لِلسَّائِلِ حَقٌّ",
   [], [.sinf .sifa], none⟩,
  -- A47
  ⟨"A47", .qayd, .mujib, "وَلَيْسَ لِمُحْتَجِرٍ حَقٌّ بَعْدَ ثَلَاثٍ",
   [], [.sinf .sifa, .sinf .adad], none⟩,
  -- A48
  ⟨"A48", .qayd, .mujib, "إِنْ تَسْتَغْفِرْ سَبْعِينَ مَرَّةً فَلَنْ يُغْفَرَ لَهُمْ",
   [], [.sinf .shart, .sinf .adad], none⟩,
  -- A49
  ⟨"A49", .qayd, .mujib, "أَعْطِنِي الْقِرْشَيْنِ",
   [], [.sinf .adad], none⟩,
  -- A50
  ⟨"A50", .qayd, .umum, "صُمْ يَوْمَ الْخَمِيسِ",
   [], [.laQayd], none⟩]

end Dabit
end Nizam.Athar
