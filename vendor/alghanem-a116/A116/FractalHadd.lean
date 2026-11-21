import A116.Fractal
import A116.Mizan
import A116.Iltiqa

/-!
# الفراكتالُ بقيد الحدّ وإصلاح الوصل: مرحلتان من التشابه الذاتيّ (ADR ٧٨)

أمرُ المالك (2026-10-16): «برهن أنّ النصّ موصولٌ صحيحًا … الاختبارُ يجب أن يبرهن قيدَ الحدّ ويبرهن إصلاحَ الوصل بين
الكلمات … induction FOR، induction on لبناء الدالّة الفراكتاليّة بين الكلمات، وهي مرحلتان من التشابه الذاتيّ الطبقيّ
وفق الوراثة والتوريث».

`Fractal` (ADR ٧٧) يرفع التوريثَ بلا حدّ. وهنا آلةُ الحرف (`Harf`، ADR ٤٢) نفسُها بحدّها: السطرُ يُقرأ كلمةً كلمة،
وبين كلّ كلمتين خطوةٌ على الحال الموروث (`Harf.hadd`)، وهو `strictLineB` بعينه (`HarfBridge.line_eq_strictLineB`).

**المرحلةُ الأولى — من الخانة إلى السطر:**
* **FOR** (`runLine_for`): السطرُ طيٌّ يساريّ على كلماته: الأولى من حالها، وكلُّ كلمةٍ بعدها ترث حالَ ما قبلها بعد الحدّ
  — وبُرهن بالاستقراء على الكلمات (**induction on**)؛ فالحكمُ على السطر حكمُ هذا الطيّ (`lineB_for`، `lineWaqfB_for`)،
  وهو `strictLineB`/`strictLinePauseB` (`line_for_strict`، `line_for_strict_pause`).
* **الحدُّ صفرٌ بعد المتحرّك** (`hadd_zero_after_vowel`): الحالُ بعد خانةٍ متحرّكة لا يمسّه الحدّ، وصلًا ووقفًا؛
  ويمسّ الحدُّ أربعةَ أحوالٍ وحدَها: المدّ، والفرق، والطويلَ المغلق، وطويلَ الفرق (`hadd_moves_iff`).
* **إصلاحُ الوصل يجعل الحدَّ صفرًا** (`repair_seam_zero`): كلُّ وجهٍ من أوجه `Iltiqa.repair` يُنهي اليسرى بمتحرّك
  (`Iltiqa.repaired_endsVowel`)، فالحدُّ بعدها هويّة — «الصفر» الذي هو محايدُ التركيب.
* **السطرُ الذي حدودُه أصفار هو كلمةٌ واحدة** (`line_flat`): إذا انتهت كلُّ كلمةٍ قبل الأخيرة بمتحرّك فالسطرُ هو
  تسطيحُه بلا حدّ.

**المرحلةُ الثانية — من السطر إلى النصّ:** الآيةُ سطرٌ من الابتداء إلى الوقف، والوقفُ لا يورث (`TawrithSitta.waqf_yaqta`)،
فتركيبُ السطور في النصّ عطفٌ (و) لا وراثة: `textB` تشاكلٌ إلى (Bool، ∧، صحيح) — الفارغُ صحيح (الصفر) والموصولُ
عطفُ الحكمين (`text_zero`، `text_append`)، وبالاستقراء FOR على السطور (`text_for`).
-/

set_option autoImplicit false

namespace A116.FractalHadd

open A116 A116.Hadd HarfBridge

/-! ## ١. المرحلةُ الأولى: FOR بين الكلمات -/

/-- خطوةُ الكلمة بعد الحدّ: ترث الحالَ، فيمرّ بالحدّ، ثمّ تُطوى خاناتُها. -/
def kalimaStep (f : Harf.Hal → Harf.Khana → Harf.Hal) (s : Harf.Hal) (v : List Harf.Khana) : Harf.Hal :=
  Harf.run f (Harf.hadd s) v

/-- **FOR**: السطرُ طيٌّ يساريّ على كلماته — بالاستقراء على الكلمات. -/
theorem runLine_for (f : Harf.Hal → Harf.Khana → Harf.Hal) :
    ∀ (a : Harf.Hal) (w : List Harf.Khana) (ws : List (List Harf.Khana)),
      Harf.runLine f a (w :: ws) = ws.foldl (kalimaStep f) (Harf.run f a w)
  | a, w, [] => rfl
  | a, w, v :: rest => by
    show Harf.runLine f (Harf.hadd (Harf.run f a w)) (v :: rest) = _
    rw [runLine_for f _ v rest]
    rfl

theorem lineB_for (w : List Harf.Khana) (ws : List (List Harf.Khana)) :
    Harf.lineB (w :: ws) = Harf.qabilWasl (ws.foldl (kalimaStep Harf.wasl) (Harf.run Harf.wasl .bad' w)) := by
  unfold Harf.lineB
  rw [runLine_for]

theorem lineWaqfB_for (w : List Harf.Khana) (ws : List (List Harf.Khana)) :
    Harf.lineWaqfB (w :: ws) =
      Harf.qabilWaqf (ws.foldl (kalimaStep Harf.waqf) (Harf.run Harf.waqf .bad' w)) := by
  unfold Harf.lineWaqfB
  rw [runLine_for]

/-- **وهو قيدُ الحدّ على السطر بعينه.** -/
theorem line_for_strict (w : List Harf.Khana) (ws : List (List Harf.Khana)) (hne : ∀ x ∈ w :: ws, x ≠ []) :
    Harf.qabilWasl (ws.foldl (kalimaStep Harf.wasl) (Harf.run Harf.wasl .bad' w)) =
      NizamLine.strictLineB (projL (w :: ws)) := by
  rw [← lineB_for, line_eq_strictLineB _ hne]

theorem line_for_strict_pause (w : List Harf.Khana) (ws : List (List Harf.Khana))
    (hne : ∀ x ∈ w :: ws, x ≠ []) :
    Harf.qabilWaqf (ws.foldl (kalimaStep Harf.waqf) (Harf.run Harf.waqf .bad' w)) =
      NizamLine.strictLinePauseB (projL (w :: ws)) := by
  rw [← lineWaqfB_for, lineWaqf_eq_strictLinePauseB _ hne]

/-! ## ٢. الحدُّ صفرٌ بعد المتحرّك -/

/-- **الحدُّ يمسّ أربعةَ أحوالٍ وحدَها.** -/
theorem hadd_moves_iff : ∀ a ∈ Harf.Hal.all,
    (Harf.hadd a != a) = (a == .madd || a == .farq || a == .tawilFarq ||
      match a with | .tawil _ => true | _ => false) := by
  decide

/-- **الحالُ بعد خانةٍ متحرّكة لا يمسّه الحدّ**، وصلًا ووقفًا. -/
theorem hadd_zero_after_vowel : ∀ a ∈ Harf.Hal.all, ∀ x ∈ Harf.Khana.all, x.haal ≠ .sukun →
    Harf.hadd (Harf.wasl a x) = Harf.wasl a x ∧ Harf.hadd (Harf.waqf a x) = Harf.waqf a x := by
  decide +kernel

theorem run_snoc (f : Harf.Hal → Harf.Khana → Harf.Hal) :
    ∀ (a : Harf.Hal) (u : List Harf.Khana) (x : Harf.Khana), Harf.run f a (u ++ [x]) = f (Harf.run f a u) x
  | _, [], _ => rfl
  | a, y :: u, x => run_snoc f (f a y) u x

/-- كلمةٌ آخرُها متحرّك. -/
def EndsVowelH (w : List Harf.Khana) : Prop := ∃ x, w.getLast? = some x ∧ x.haal ≠ .sukun

theorem seam_zero (pause : Bool) (a : Harf.Hal) (w : List Harf.Khana) (h : EndsVowelH w) :
    Harf.hadd (Harf.run (if pause then Harf.waqf else Harf.wasl) a w) =
      Harf.run (if pause then Harf.waqf else Harf.wasl) a w := by
  obtain ⟨x, hx, hv⟩ := h
  obtain ⟨u, rfl⟩ := List.getLast?_eq_some_iff.1 hx
  rw [run_snoc]
  have := hadd_zero_after_vowel (Harf.run (if pause then Harf.waqf else Harf.wasl) a u)
    (Harf.Hal.mem_all _) x (Harf.Khana.mem_all x) hv
  cases pause
  · exact this.1
  · exact this.2

/-- السكونُ في الخانة يُحفظ في الجسر إلى خانات الآلة. -/
theorem unproj_sukun : ∀ c ∈ A116.cells, ((unproj c).haal == .sukun) = (c.haraka == .sukun) := by
  decide +kernel

theorem toH_endsVowel (l : List Cell) (h : Iltiqa.EndsVowel l) : EndsVowelH (Mizan.toH l) := by
  obtain ⟨p, hp, hv⟩ := h
  refine ⟨unproj p, ?_, ?_⟩
  · simp [Mizan.toH, List.getLast?_map, hp]
  · intro e
    have := unproj_sukun p (mem_cells p)
    rw [e] at this
    simp at this
    exact hv this

/-- **إصلاحُ الوصل يجعل الحدَّ صفرًا**: بعد كلّ وجهٍ من أوجه الإصلاح، الحدُّ بعد اليسرى هويّة. -/
theorem repair_seam_zero (pause : Bool) (a : Harf.Hal) (l r : List Cell) (t : Iltiqa.Repair)
    (h : (Iltiqa.repair l r).2 = some t) :
    Harf.hadd (Harf.run (if pause then Harf.waqf else Harf.wasl) a (Mizan.toH (Iltiqa.repair l r).1)) =
      Harf.run (if pause then Harf.waqf else Harf.wasl) a (Mizan.toH (Iltiqa.repair l r).1) :=
  seam_zero pause a _ (toH_endsVowel _ (Iltiqa.repaired_endsVowel l r t h))

/-- **السطرُ الذي حدودُه أصفار كلمةٌ واحدة**: إن انتهت كلُّ كلمةٍ قبل الأخيرة بمتحرّك فالسطرُ تسطيحُه. -/
theorem line_flat (pause : Bool) : ∀ (a : Harf.Hal) (ws : List (List Harf.Khana)),
    (∀ w ∈ ws.dropLast, EndsVowelH w) →
    Harf.runLine (if pause then Harf.waqf else Harf.wasl) a ws =
      Harf.run (if pause then Harf.waqf else Harf.wasl) a ws.flatten
  | a, [], _ => rfl
  | a, [w], _ => by simp [Harf.runLine]
  | a, w :: v :: rest, h => by
    have hw : EndsVowelH w := h w (by simp)
    show Harf.runLine _ (Harf.hadd (Harf.run _ a w)) (v :: rest) = _
    rw [seam_zero pause a w hw, line_flat pause _ (v :: rest) (fun x hx => h x (by
      simp only [List.dropLast_cons_cons] at hx ⊢; exact List.mem_cons_of_mem _ hx))]
    rw [show (w :: v :: rest).flatten = w ++ (v :: rest).flatten from rfl, run_append]
where
  run_append : ∀ (a : Harf.Hal) (u v : List Harf.Khana),
      Harf.run (if pause then Harf.waqf else Harf.wasl) a (u ++ v) =
        Harf.run (if pause then Harf.waqf else Harf.wasl) (Harf.run (if pause then Harf.waqf else Harf.wasl) a u) v
    | _, [], _ => rfl
    | a, x :: u, v => run_append _ u v

/-! ## ٣. المرحلةُ الثانية: من السطر إلى النصّ -/

/-- النصُّ آياتٌ، كلُّ آيةٍ من الابتداء إلى الوقف. -/
def textB (ls : List (List (List Harf.Khana))) : Bool := ls.all Harf.lineWaqfB

/-- **الصفر**: النصُّ الفارغ صحيح. -/
theorem text_zero : textB [] = true := rfl

/-- **الموصولُ عطفُ الحكمين**: الوقفُ لا يورث، فالسطورُ تُعطف ولا تُورَّث. -/
theorem text_append (ls ms : List (List (List Harf.Khana))) : textB (ls ++ ms) = (textB ls && textB ms) := by
  simp [textB, List.all_append]

/-- **FOR على السطور**: النصُّ طيٌّ بالعطف من الصفر. -/
theorem text_for (ls : List (List (List Harf.Khana))) :
    textB ls = ls.foldl (fun acc l => acc && Harf.lineWaqfB l) true := by
  unfold textB
  suffices h : ∀ b, ls.foldl (fun acc l => acc && Harf.lineWaqfB l) b = (b && ls.all Harf.lineWaqfB) by
    rw [h]; rfl
  induction ls with
  | nil => intro b; simp
  | cons l ls ih => intro b; simp only [List.foldl_cons, List.all_cons, ih, Bool.and_assoc]

/-! ## ٤. الشواهد -/

/-- **الشاهد**: «قُلِ قُلِ لْحَمْدُ» سطرًا طيُّه FOR مقبول، و«يَا + الشَّافِعِينَ» مرفوضٌ بالحدّ وإن قُبل كلمةً واحدة؛
والحدُّ بعد «قُلِ» صفر. -/
theorem shawahid :
    Harf.qabilWasl ([Harf.quli, Harf.lhamdu].foldl (kalimaStep Harf.wasl)
      (Harf.run Harf.wasl .bad' Harf.quli)) = true ∧
    Harf.qabilWasl ([Harf.shshafiina].foldl (kalimaStep Harf.wasl) (Harf.run Harf.wasl .bad' Harf.yaa)) = false ∧
    Harf.waslB (Harf.yaa ++ Harf.shshafiina) = true ∧
    Harf.hadd (Harf.run Harf.wasl .bad' Harf.quli) = Harf.run Harf.wasl .bad' Harf.quli ∧
    Harf.hadd (Harf.run Harf.wasl .bad' Harf.yaa) ≠ Harf.run Harf.wasl .bad' Harf.yaa := by
  decide

end A116.FractalHadd
