/-
  Dal/AqsamAllafz.lean — المرحلة ١ (الدال وحده): «صورة» أقسام اللفظ باعتبار الدال وحده.

  السند (الشخصية ج3، أرقام أسطر الملف المحوَّل a2.txt):
  * 737: ينقسم اللفظ باعتبار الدال وحده «أي باعتبار دلالة الألفاظ» إلى: مطابقة، تضمّن، التزام.
  * 741: المفرد: اسم، فعل، حرف.
  * 767: المركّب «من أقسام الدال وحده»: استفهام، أمر، التماس، سؤال، خبر، تنبيه.

  هنا تُعرَّف الأنواع وحدها (المخطّط)، بلا أيّ محتوى معنى. تحقُّق نوعٍ بعينه للفظٍ بعينه
  يحتاج مادّة المدلول (المرحلة ٢)، ويُحسب في الجسر (المرحلة ٣، Jisr/Tawafuq.lean).
  بلا sorry ولا axiom ولا native_decide.
-/
namespace Dal

/-- أنواع الدلالة الثلاثة (ج3 737). -/
inductive NawDalala
  | mutabaqa   -- على تمام المسمّى
  | tadammun   -- على جزء المسمّى
  | iltizam    -- على لازمه الذهنيّ
deriving DecidableEq, Repr

/-- أقسام المفرد (ج3 741). -/
inductive QismMufrad
  | ism | fil | harf
deriving DecidableEq, Repr

/-- أقسام المركّب (ج3 767). -/
inductive QismMurakkab
  | istifham | amr | iltimas | sual | khabar | tanbih
deriving DecidableEq, Repr

namespace NawDalala
def kull : List NawDalala := [mutabaqa, tadammun, iltizam]
theorem kull_hasir (k : NawDalala) : k ∈ kull := by cases k <;> simp [kull]
theorem kull_nodup : kull.Nodup := by decide
theorem kull_length : kull.length = 3 := rfl
end NawDalala

namespace QismMufrad
def kull : List QismMufrad := [ism, fil, harf]
theorem kull_hasir (k : QismMufrad) : k ∈ kull := by cases k <;> simp [kull]
theorem kull_nodup : kull.Nodup := by decide
end QismMufrad

namespace QismMurakkab
def kull : List QismMurakkab := [istifham, amr, iltimas, sual, khabar, tanbih]
theorem kull_hasir (k : QismMurakkab) : k ∈ kull := by cases k <;> simp [kull]
theorem kull_nodup : kull.Nodup := by decide
theorem kull_length : kull.length = 6 := rfl
end QismMurakkab

end Dal
