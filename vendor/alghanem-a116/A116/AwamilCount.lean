import A116.AwamilData

/-! العواملُ المائة على المودَع (ADR ٧١): العدُّ، وأعدادُ الأصناف، والمرساةُ لكلّ ذي أثر. -/

namespace A116.Awamil

/-- سطورُ أبواب الألفيّة التي تُرسي الأصناف (شرحُ ابن عقيل المختوم). -/
def babs : List Nat := [1847, 2202, 2339, 2794, 4074, 4634, 6440, 6680, 7398, 7577]

theorem rows_length : rows.length = 100 := by decide

def count (a : Athar) : Nat := (rows.filter fun r => r.2.1 == a).length

theorem class_counts :
    count .rafNasb = 13 ∧ count .jarr = 14 ∧ count .nasbNasb = 10 ∧ count .jazmFilayn = 10 ∧
    count .tabi = 8 ∧ count .nasbFil = 7 ∧ count .nasbRaf = 6 ∧ count .rafTawil = 6 ∧
    count .jazmFil = 4 ∧ count .nida = 4 ∧ count .jarrOrNasb = 3 ∧ count .jarrOrNasbFil = 1 ∧
    count .none = 14 := by decide

theorem counts_sum : (all.map count).sum = rows.length := by decide

/-- كلُّ عاملٍ له أثرٌ مرسًى في بابٍ من الأبواب العشرة؛ وما لا أثرَ له إمّا مرسًى (الشرطُ غيرُ الجازم) أو بلا باب (الاستفهام). -/
theorem anchored_or_none :
    rows.all (fun r => (first r.2.1).isNone || babs.contains r.2.2) = true := by decide

/-- الاسمُ الواحد بعملين: مَن وما ومتى وأين شرطًا واستفهامًا — أربعةُ تكرارات (لكن وحتّى مميَّزتان في المرفق). -/
theorem names_repeat : rows.length - (rows.map (·.1)).eraseDups.length = 4 := by decide

end A116.Awamil
