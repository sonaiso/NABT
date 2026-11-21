import A116.FractalTarkib

/-! مولَّدٌ بـ`tools/gen_fractal_tarkib.py` (ADR ٨٠)؛ لا يُحرَّر باليد. عدُّ الأزواج على المصحف قطعةً قطعة، كلُّ قطعةٍ تفحصها النواة، ثمّ تُوصل بالطيّ (`List.foldl_append`). -/

set_option maxRecDepth 200000

namespace A116.FractalTarkib

def accs : List (List Nat) := [
  [0, 0, 0, 0, 0, 0, 0, 0, 0],
  [2495, 933, 2654, 1547, 20, 382, 2354, 948, 593],
  [5110, 1811, 5476, 3272, 33, 774, 4677, 2141, 1222],
  [7311, 2665, 7619, 4783, 63, 1141, 6530, 3090, 1752],
  [9561, 3343, 9888, 6131, 77, 1472, 8482, 4033, 2319],
  [11310, 3932, 11604, 7165, 93, 1793, 10100, 4723, 2759],
  [13051, 4381, 12958, 8096, 119, 2126, 11299, 5482, 3102],
  [14566, 4808, 14400, 8957, 130, 2360, 12631, 6110, 3463],
  [15906, 5154, 15506, 9706, 141, 2577, 13692, 6654, 3729],
  [17730, 5836, 17343, 10861, 162, 2931, 15410, 7433, 4173],
  [18876, 6172, 18410, 11537, 177, 3084, 16483, 7888, 4484],
  [20581, 6746, 19940, 12444, 192, 3363, 18000, 8461, 4864],
  [22011, 7173, 21128, 13263, 195, 3544, 19113, 9005, 5151],
  [23393, 7547, 22219, 13951, 201, 3666, 20205, 9417, 5449],
  [24429, 7838, 22976, 14524, 212, 3834, 21006, 9843, 5667],
  [24950, 8027, 23236, 14779, 218, 3893, 21455, 10008, 5772],
  [25287, 8117, 23390, 14941, 221, 3941, 21697, 10151, 5861]]

theorem qitaa0 : ayat0.foldl cntPairs (accs.getD 0 []) = accs.getD 1 [] := by
  decide +kernel

theorem qitaa1 : ayat1.foldl cntPairs (accs.getD 1 []) = accs.getD 2 [] := by
  decide +kernel

theorem qitaa2 : ayat2.foldl cntPairs (accs.getD 2 []) = accs.getD 3 [] := by
  decide +kernel

theorem qitaa3 : ayat3.foldl cntPairs (accs.getD 3 []) = accs.getD 4 [] := by
  decide +kernel

theorem qitaa4 : ayat4.foldl cntPairs (accs.getD 4 []) = accs.getD 5 [] := by
  decide +kernel

theorem qitaa5 : ayat5.foldl cntPairs (accs.getD 5 []) = accs.getD 6 [] := by
  decide +kernel

theorem qitaa6 : ayat6.foldl cntPairs (accs.getD 6 []) = accs.getD 7 [] := by
  decide +kernel

theorem qitaa7 : ayat7.foldl cntPairs (accs.getD 7 []) = accs.getD 8 [] := by
  decide +kernel

theorem qitaa8 : ayat8.foldl cntPairs (accs.getD 8 []) = accs.getD 9 [] := by
  decide +kernel

theorem qitaa9 : ayat9.foldl cntPairs (accs.getD 9 []) = accs.getD 10 [] := by
  decide +kernel

theorem qitaa10 : ayat10.foldl cntPairs (accs.getD 10 []) = accs.getD 11 [] := by
  decide +kernel

theorem qitaa11 : ayat11.foldl cntPairs (accs.getD 11 []) = accs.getD 12 [] := by
  decide +kernel

theorem qitaa12 : ayat12.foldl cntPairs (accs.getD 12 []) = accs.getD 13 [] := by
  decide +kernel

theorem qitaa13 : ayat13.foldl cntPairs (accs.getD 13 []) = accs.getD 14 [] := by
  decide +kernel

theorem qitaa14 : ayat14.foldl cntPairs (accs.getD 14 []) = accs.getD 15 [] := by
  decide +kernel

theorem qitaa15 : ayat15.foldl cntPairs (accs.getD 15 []) = accs.getD 16 [] := by
  decide +kernel

/-- **الأنواعُ التسعة كلُّها واقعةٌ بأعدادها** برمز ‎3a + b‎ (0 اسم، 1 فعل، 2 حرف). -/
theorem azwaj_mushaf :
    ayat.foldl cntPairs [0, 0, 0, 0, 0, 0, 0, 0, 0] = [25287, 8117, 23390, 14941, 221, 3941, 21697, 10151, 5861] := by
  rw [show [0, 0, 0, 0, 0, 0, 0, 0, 0] = accs.getD 0 [] from rfl]
  simp only [ayat, List.foldl_append, qitaa0, qitaa1, qitaa2, qitaa3, qitaa4, qitaa5, qitaa6, qitaa7, qitaa8, qitaa9, qitaa10, qitaa11, qitaa12, qitaa13, qitaa14, qitaa15]
  rfl

end A116.FractalTarkib
