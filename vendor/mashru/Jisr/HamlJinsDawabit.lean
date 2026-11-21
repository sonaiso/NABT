/-
# حالاتُ ضابط «الحمل من الجنس» المجمَّدة — مولَّد

مولَّدٌ من `tahaqquq/dawabit/haml_jins/cases.json` بـ `python3 -I scripts/bina_dawabit_haml_jins.py`؛ لا يُحرَّر يدويًّا.
بصمةُ الحالات: `59c8effa421dc6fd76f4f265f1e97cdadd81fb254946a29e5342bc986660f353`.
كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من المواصفة والمصدر قبل الشفرة، وفي سياقه ما حُقن آليًّا (`tahaqquq/dawabit/haml_jins/taalif.md`)؛ وجُمّدت ببصمتها في `tahaqquq/dawabit/haml_jins/tajmid.json`. والمثالُ والسندُ في الملفّ المصدر.
-/
import Jisr.HamlJinsDabit

namespace Jisr
namespace QabiliyyaJins
namespace Dabit

def halat : List Hala := [
  ⟨"H01", .mujib, some .insan, some .sayr, .isnadiyya, [.murakhkhas]⟩,
  ⟨"H02", .mujib, some .insan, some .jary, .isnadiyya, [.murakhkhas]⟩,
  ⟨"H03", .mujib, some .insan, some .qafz, .isnadiyya, [.murakhkhas]⟩,
  ⟨"H04", .mujib, some .hayawan, some .sayr, .isnadiyya, [.murakhkhas]⟩,
  ⟨"H05", .mujib, some .hayawan, some .rakd, .isnadiyya, [.murakhkhas]⟩,
  ⟨"H06", .mujib, some .hayawan, some .zahf, .isnadiyya, [.murakhkhas]⟩,
  ⟨"H07", .hadd, some .insan, some .sayr, .idafiyya, [.mumtani]⟩,
  ⟨"H08", .hadd, some .hayawan, some .rakd, .idafiyya, [.mumtani]⟩,
  ⟨"H09", .hadd, some .jamad, some .qafz, .idafiyya, [.mumtani]⟩,
  ⟨"H10", .hadd, some .nabat, some .jary, .idafiyya, [.mumtani]⟩,
  ⟨"H11", .hadd, some .jamad, some .sayr, .isnadiyya, [.laHukm]⟩,
  ⟨"H12", .hadd, some .nabat, some .zahf, .isnadiyya, [.laHukm]⟩,
  ⟨"H13", .kharij, none, some .sayr, .isnadiyya, [.laJins]⟩,
  ⟨"H14", .kharij, none, some .rakd, .idafiyya, [.laJins]⟩,
  ⟨"H15", .kharij, none, none, .isnadiyya, [.laJins]⟩,
  ⟨"H16", .kharij, some .insan, none, .isnadiyya, [.laMithal]⟩,
  ⟨"H17", .kharij, some .jamad, none, .isnadiyya, [.laMithal]⟩,
  ⟨"H18", .kharij, some .hayawan, none, .idafiyya, [.laMithal]⟩,
  ⟨"H19", .kharij, some .nabat, none, .isnadiyya, [.laMithal]⟩,
  ⟨"H20", .umum, some .insan, some .rakd, .isnadiyya, [.murakhkhas]⟩,
  ⟨"H21", .umum, some .insan, some .zahf, .isnadiyya, [.murakhkhas]⟩,
  ⟨"H22", .umum, some .hayawan, some .jary, .isnadiyya, [.murakhkhas]⟩,
  ⟨"H23", .umum, some .hayawan, some .qafz, .isnadiyya, [.murakhkhas]⟩,
  ⟨"H24", .ghumud, some .insan, some .sayr, .idafiyya, [.murakhkhas, .mumtani]⟩]

end Dabit
end QabiliyyaJins
end Jisr
