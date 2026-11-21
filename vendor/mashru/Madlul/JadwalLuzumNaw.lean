/-
  Madlul/JadwalLuzumNaw.lean — أنواعُ صفّ جدول اللزوم من شبكة المعاجم (المقاييس واللسان المختومان).
  يستورده الملفّ المولَّد `Madlul/JadwalLuzumData.lean` والبناءُ عليه `Madlul/JadwalLuzum.lean`.
-/

namespace JadwalLuzum

/-- المعجمُ الشاهد. -/
inductive Mujam | lisan | maqayis
  deriving DecidableEq, Repr

/-- القضيّةُ الأولى المشهودة (قواعد `shabaka/jadwal_luzum.py`):
    `juz` جزءُ حدٍّ في تفسير اللسان (R3)، `taraduf` تفسيرٌ بجذرٍ واحد (R3، R3-ب)، `kharij` نقيضٌ/ضدٌّ/خلاف (R3)،
    `asl` أصلُ ابن فارس (R4)، `luzum` لازمٌ بجملة تعليل (R5). -/
inductive Naw | juz | taraduf | luzum | kharij | asl
  deriving DecidableEq, Repr

/-- الصفّ: المعجم، جذرُ المادّة، اللفظ المفسَّر أو المسمّى، القضيّة، الجذرُ الآخر، سطرُ الشاهد في المودَع. -/
structure Saff where
  mujam : Mujam
  a : String
  w : String
  naw : Naw
  b : String
  satr : Nat
  deriving DecidableEq, Repr

end JadwalLuzum
