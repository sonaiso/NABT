/-
  Dal/AqsamAlism.lean — المرحلة ١ (الدال وحده): صورة أقسام الاسم.

  السند (ج3، أسطر a2.txt):
  * 745: الاسم كلّيّ أو جزئيّ؛ والكلّيّ «لا يمنع نفس تصوّره من وقوع الشركة فيه»؛
         والكلّيّ متواطئ إن استوى معناه في أفراده، وإلّا فمشكّك.
  * 747: «والكلّيّ أيضًا نوعان: جنس ومشتقّ» — الجنس ما دلّ على ذاتٍ غير معيّنة (نفس الماهية)،
         والمشتقّ ما دلّ على ذي صفة معيّنة. (والكتاب يقابل «الجامد» بـ«المشتقّ» في 814.)
  * 749: الجزئيّ نوعان: علمٌ إن استقلّ بالدلالة، وضميرٌ إن افتقر إلى ما يفسّره.

  «أيضًا» في 747 تجعل قسمتَي الكلّيّ محورين مستقلّين، فأقسام الاسم 2×2 + 2 = 6.
-/
namespace Dal

inductive Tawatu | mutawati | mushakkik deriving DecidableEq, Repr
/-- الجنس (وهو الجامد المقابل للمشتقّ) أو المشتقّ. -/
inductive JinsMushtaq | jinsJamid | mushtaq deriving DecidableEq, Repr
inductive AlamDamir | alam | damir deriving DecidableEq, Repr

/-- أقسام الاسم: كلّيّ بمحوريه، أو جزئيّ بقسميه. -/
inductive QismIsm
  | kulli (t : Tawatu) (j : JinsMushtaq)
  | juzi (a : AlamDamir)
deriving DecidableEq, Repr

namespace QismIsm
def kull : List QismIsm :=
  [kulli .mutawati .jinsJamid, kulli .mutawati .mushtaq,
   kulli .mushakkik .jinsJamid, kulli .mushakkik .mushtaq,
   juzi .alam, juzi .damir]

theorem kull_hasir (q : QismIsm) : q ∈ kull := by
  rcases q with ⟨t, j⟩ | a
  · cases t <;> cases j <;> simp [kull]
  · cases a <;> simp [kull]

theorem kull_nodup : kull.Nodup := by decide

/-- 2×2 + 2 = 6 (ج3 745–749). -/
theorem sitta : kull.length = 2 * 2 + 2 := rfl

def isKulli : QismIsm → Bool
  | kulli _ _ => true
  | juzi _ => false
end QismIsm

end Dal
