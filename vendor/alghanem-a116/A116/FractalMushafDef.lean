/-!
# صفُّ الآية في مودَع الفراكتال (ADR ٧٨)

`A116.FractalData` يولّده `tools/gen_fractal.py` من تشغيل البوّابة على المصحف المختوم؛ وهنا نوعُ صفّه وجبرُ الأثر.
-/

namespace A116.FractalMushaf

/-- صفُّ الآية: أثرُها على الأصناف، وعددُ الجاهز والمرفوض بلا سياق، وجهوزُها في السياق، وقبولُ آلة الحرف وقفًا
بحدّها بعد الإصلاح، وعددُ الحدود والإصلاح، والحدودُ التي حرّكها الحدّ، وما حرّكه منها بعد إصلاح. -/
structure Aya where
  athar : List Nat
  ready : Nat
  refused : Nat
  ctx : Bool
  accepted : Bool
  seams : Nat
  repairs : Nat
  moved : Nat
  movedRepaired : Nat

/-- الانقطاع. -/
def dead : Nat := 4

/-- تطبيقُ الأثر على حالة. -/
def app (g : List Nat) (s : Nat) : Nat := if s = dead then dead else g.getD s dead

/-- تركيبُ أثرين: الأوّلُ ثمّ الثاني. -/
def comp (f g : List Nat) : List Nat := f.map (app g)

/-- الصفر: الهويّة على الحالات الأربع. -/
def sifr : List Nat := [0, 1, 2, 3]

theorem comp_sifr_left (g : List Nat) (hg : g.length = 4) : comp sifr g = g := by
  match g, hg with
  | [a, b, c, d], _ => rfl

/-- **التركيبُ تطبيقٌ متتابع**: صورةُ الحالة بالمركَّب صورةُ صورتِها. -/
theorem app_comp (f g : List Nat) (s : Nat) (hs : s < f.length) (h4 : s ≠ dead) :
    app (comp f g) s = app g (app f s) := by
  simp [app, comp, h4, List.getD_eq_getElem?_getD, hs]

end A116.FractalMushaf
