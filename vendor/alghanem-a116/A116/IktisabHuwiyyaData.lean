import A116.IktisabHuwiyya

/-! مولَّدٌ بـ`tools/gen_iktisab_huwiyya.py` (ADR ١٢٤) — لا يُحرَّر باليد.
    ما اكتسبه المتعلّم: أصغرُ مجموعة أوصافٍ تعيّن كلَّ قانون، وجدولُه عليها. -/

namespace A116.IktisabHuwiyyaData

open A116.IktisabHuwiyya

/-- `wujud`: hala + jazari17. -/
def wujudW : List Wasf := [.hala, .jazari]

def wujudJ : List (List Nat × Bool) := [([0, 0], false), ([0, 1], true), ([0, 2], true), ([0, 3], true), ([0, 4], true), ([0, 5], true), ([0, 6], true), ([0, 7], true), ([0, 8], true), ([0, 9], true), ([0, 10], true), ([0, 11], true), ([0, 12], true), ([0, 13], true), ([0, 14], true), ([0, 15], true), ([1, 0], false), ([1, 1], true), ([1, 2], true), ([1, 3], true), ([1, 4], true), ([1, 5], true), ([1, 6], true), ([1, 7], true), ([1, 8], true), ([1, 9], true), ([1, 10], true), ([1, 11], true), ([1, 12], true), ([1, 13], true), ([1, 14], true), ([1, 15], true), ([2, 0], false), ([2, 1], true), ([2, 2], true), ([2, 3], true), ([2, 4], true), ([2, 5], true), ([2, 6], true), ([2, 7], true), ([2, 8], true), ([2, 9], true), ([2, 10], true), ([2, 11], true), ([2, 12], true), ([2, 13], true), ([2, 14], true), ([2, 15], true), ([3, 0], true), ([3, 1], true), ([3, 2], true), ([3, 3], true), ([3, 4], true), ([3, 5], true), ([3, 6], true), ([3, 7], true), ([3, 8], true), ([3, 9], true), ([3, 10], true), ([3, 11], true), ([3, 12], true), ([3, 13], true), ([3, 14], true), ([3, 15], true)]

/-- `ibtida`: hala. -/
def ibtidaW : List Wasf := [.hala]

def ibtidaJ : List (List Nat × Bool) := [([0], true), ([1], true), ([2], true), ([3], false)]

/-- `mubtada`: hala + jazari17. -/
def mubtadaW : List Wasf := [.hala, .jazari]

def mubtadaJ : List (List Nat × Bool) := [([0, 0], false), ([0, 1], true), ([0, 2], true), ([0, 3], true), ([0, 4], true), ([0, 5], true), ([0, 6], true), ([0, 7], true), ([0, 8], true), ([0, 9], true), ([0, 10], true), ([0, 11], true), ([0, 12], true), ([0, 13], true), ([0, 14], true), ([0, 15], true), ([1, 0], false), ([1, 1], true), ([1, 2], true), ([1, 3], true), ([1, 4], true), ([1, 5], true), ([1, 6], true), ([1, 7], true), ([1, 8], true), ([1, 9], true), ([1, 10], true), ([1, 11], true), ([1, 12], true), ([1, 13], true), ([1, 14], true), ([1, 15], true), ([2, 0], false), ([2, 1], true), ([2, 2], true), ([2, 3], true), ([2, 4], true), ([2, 5], true), ([2, 6], true), ([2, 7], true), ([2, 8], true), ([2, 9], true), ([2, 10], true), ([2, 11], true), ([2, 12], true), ([2, 13], true), ([2, 14], true), ([2, 15], true), ([3, 0], false), ([3, 1], false), ([3, 2], false), ([3, 3], false), ([3, 4], false), ([3, 5], false), ([3, 6], false), ([3, 7], false), ([3, 8], false), ([3, 9], false), ([3, 10], false), ([3, 11], false), ([3, 12], false), ([3, 13], false), ([3, 14], false), ([3, 15], false)]

end A116.IktisabHuwiyyaData
