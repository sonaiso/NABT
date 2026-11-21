import A116.HarfBridge.Satr

/-!
# الميزان: حكمُ الموصول آلةً منتهيةً جدولُها كاملٌ (ADR ٤٢)

`GATE_JOINED_VS_STRICTJOINB` كان «مسدودًا بالمطابقة» على جدولٍ محدود الطول. وهنا يُرفع: حكمُ الموصول **آلةٌ منتهية**
(`Harf`: 42 حالًا × 116 خانة) وعلى كلّ طولٍ هي `strictJoinB` بعينها (`machineJoin_eq`، `machineJoin_pause_eq`، من
`HarfBridge.join_eq_strictJoinB`). ودالّةُ الانتقال منتهيةُ المجال، فجدولُها المولَّد (`a116-table mizan`) **هو الدالّةُ
نفسُها على مجالها كلِّه** لا عيّنةً منها: كلُّ حالٍ وكلُّ خانةٍ صفّ (`hal_nodup`، `khana_nodup`، `Hal.mem_all`،
`Khana.mem_all`). فلا يبقى بين بايثون والبرهان إلّا مفسِّرُ الجدول: طيٌّ على الكلمة (`Harf.run`) بين حدّين (`Harf.hadd`).
-/

set_option autoImplicit false

namespace A116.Mizan

open A116 A116.Hadd HarfBridge

/-- الكلمةُ من خانات الغانم إلى خانات الآلة. -/
def toH (w : List Cell) : List Harf.Khana := w.map unproj

theorem projW_toH (w : List Cell) : projW (toH w) = w := by
  induction w with
  | nil => rfl
  | cons c t ih =>
    simp only [toH, projW, List.map_cons] at ih ⊢
    rw [ih, proj_bijective.2 c (mem_cells c)]

theorem toH_ne {w : List Cell} (h : w ≠ []) : toH w ≠ [] := by
  cases w <;> simp_all [toH]

/-- حكمُ الموصول بالآلة: اليسارُ من أوّله، ثمّ الحدّ، ثمّ اليمين؛ وصلًا أو وقفًا. -/
def machineJoin (pause : Bool) (L W : List Cell) : Bool :=
  if pause then
    Harf.qabilWaqf (Harf.run Harf.waqf (Harf.hadd (Harf.run Harf.waqf .bad' (toH L))) (toH W))
  else
    Harf.qabilWasl (Harf.run Harf.wasl (Harf.hadd (Harf.run Harf.wasl .bad' (toH L))) (toH W))

/-- **الموصولُ وصلًا هو `strictJoinB` بعينه، على كلّ طول**. -/
theorem machineJoin_eq (L W : List Cell) (hL : L ≠ []) (hW : W ≠ []) :
    machineJoin false L W = strictJoinB L W := by
  have h := join_eq_strictJoinB (toH L) (toH W) (toH_ne hL) (toH_ne hW)
  rw [projW_toH, projW_toH] at h
  rw [← h]; rfl

/-- **ووقفًا `strictJoinPauseB` بعينه**. -/
theorem machineJoin_pause_eq (L W : List Cell) (hL : L ≠ []) (hW : W ≠ []) :
    machineJoin true L W = strictJoinPauseB L W := by
  have h := joinWaqf_eq_strictJoinPauseB (toH L) (toH W) (toH_ne hL) (toH_ne hW)
  rw [projW_toH, projW_toH] at h
  rw [← h]; rfl

/-- الجدولُ دالّة: لا حالَ يتكرّر ولا خانة، فالرقمُ في الجدول يعيّن صاحبَه. -/
theorem hal_nodup : Harf.Hal.all.Nodup := by decide +kernel
theorem khana_nodup : Harf.Khana.all.Nodup := by decide +kernel
theorem hal_count : Harf.Hal.all.length ∈ [42] := by decide
theorem bad_first : Harf.Hal.all.head? = some .bad' := rfl

/-- رقمُ الحال ورقمُ الخانة في الجدول: موضعُهما في قائمتَي المجال (`hal_nodup`، `khana_nodup`). -/
def hi (s : Harf.Hal) : Nat := Harf.Hal.all.idxOf s
def ki (x : Harf.Khana) : Nat := Harf.Khana.all.idxOf x

/-- والخانةُ من الغانم تُنقل نقلًا واحدًا: لكلّ خانةٍ صفُّها في جدول الآلة. -/
theorem cells_map : ∀ c ∈ A116.cells, unproj c ∈ Harf.Khana.all := fun _ _ => Harf.Khana.mem_all _

end A116.Mizan
