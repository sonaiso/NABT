import A116.Itar

/-!
# قسمُ الكلمة من الخانات: علاماتُ سيبويه قيودًا، والسقفُ لكلّ دالّة (ADR ١٠٦)

أمرُ المالك: «راجع سيبويه في الكتاب واوجد حلا رياضيا من ال binary».

القسمُ (اسم، فعل، حرف) كان مُدخَلًا عرّافًا (`QISM_ORACLE`، `QISM_IS_INPUT`). وهنا يُقرأ من الخانات، وهي سبعُ
بتّاتٍ لكلّ خانة (`Iqtiran.saa_tamma`)، على وجهين:

* **العلامة** نمطٌ على ذرّات الكلمة وذرّات ما قبلها، معه ما تُبقيه من الأقسام. وأصلُها من النصّ المختوم:
  * الكتاب س103: «فالكلم اسم وفعل وحرف جاء لمعنى»، والحرفُ س109–110: «فنحو ثم وسوف».
  * س123–125: «وليس في الأسماء جزم … والنصب في المضارع من الأفعال لن يفعل … والجزم لم يفعل».
  * س129–130: «سيفعل ذلك وسوف يفعل … كما تلحق الألف واللام الأسماء».
  * شرح ابن عقيل س262–286 (علاماتُ الفعل والحرف).

  والقارئُ مرشَّحوه الأقسامُ الثلاثة تقطعها العلاماتُ التي أُطلقت، والحكمُ ثلاثيّ (`Iqtiran.mantuq`). ولا علامةَ
  للحرف بالغياب: الخلوُّ «لا حكم».
* **السقف**: لكلّ دالّةٍ في الخانات، أيًّا كانت، عددُ ما تصيبه من مرجعٍ مجدول لا يزيد على مجموعِ أكثرِ قسمٍ لكلّ صورة.
  ويُبلغ إن تباينت الصور. والمزجُ (نسيانُ بتّةٍ أو رتبة) لا يرفعه.

المبرهناتُ عامّةٌ في كلّ نمطٍ وكلّ مرجع. وأرقامُ المصحف في `docs/qism-khanat/result.json`، يحسبها
`tools/gen_qism_khanat.py` على تسجيلٍ مسبق.
-/

namespace A116.QismKhanat

open A116

inductive Qism | ism | fil | harf
  deriving DecidableEq, Repr

def kull : List Qism := [.ism, .fil, .harf]

theorem mem_kull (q : Qism) : q ∈ kull := by cases q <;> decide

/-- علامةٌ: نمطٌ على الموضع (ذرّاتُه وسياقُه) وما تُبقيه من الأقسام. -/
structure Alama (α : Type) where
  tutabiq : α → Bool
  tubqi : List Qism

variable {α : Type}

/-- المرشَّحون: كلُّ قسمٍ لم تقطعه علامةٌ أُطلقت. -/
def cands (as : List (Alama α)) (x : α) : List Qism :=
  kull.filter (fun q => as.all (fun a => !a.tutabiq x || a.tubqi.contains q))

def qiraa (as : List (Alama α)) (x : α) : Iqtiran.Mantuq Qism := Iqtiran.mantuq (cands as x)

theorem mem_cands (as : List (Alama α)) (x : α) (q : Qism) :
    q ∈ cands as x ↔ ∀ a ∈ as, a.tutabiq x = true → q ∈ a.tubqi := by
  simp only [cands, List.mem_filter, List.all_eq_true, Bool.or_eq_true, Bool.not_eq_true',
    List.contains_iff_mem, mem_kull, true_and]
  constructor
  · intro h a ha ht
    rcases h a ha with h | h
    · simp [ht] at h
    · exact h
  · intro h a ha
    cases ht : a.tutabiq x
    · exact Or.inl rfl
    · exact Or.inr (h a ha ht)

/-- خطأُ العلامة في موضعٍ من المرجع: أُطلقت وقسمُه ليس ممّا تُبقيه. -/
def khata (a : Alama α) (p : α × Qism) : Bool := a.tutabiq p.1 && !(a.tubqi.contains p.2)

/-- **الحقُّ لا يُقطع**: إن لم تخطئ علامةٌ في الموضع فقسمُه بين مرشَّحيه. -/
theorem haqq_baqi (as : List (Alama α)) (p : α × Qism) (h : ∀ a ∈ as, khata a p = false) :
    p.2 ∈ cands as p.1 := by
  rw [mem_cands]
  intro a ha ht
  have := h a ha
  simp only [khata, ht, Bool.true_and, Bool.not_eq_false', List.contains_iff_mem] at this
  exact this

/-- **المعيَّنُ صائب** إن لم تخطئ علامةٌ فيه. -/
theorem muayyan_sahih (as : List (Alama α)) (p : α × Qism) (h : ∀ a ∈ as, khata a p = false)
    (q : Qism) (hq : qiraa as p.1 = .muayyan q) : q = p.2 := by
  have hm := haqq_baqi as p h
  unfold qiraa at hq
  generalize cands as p.1 = l at hm hq
  match l, hm, hq with
  | [m], hm, hq =>
    simp only [Iqtiran.mantuq, Iqtiran.Mantuq.muayyan.injEq] at hq
    simp at hm; rw [← hq, hm]

/-- **ما قُطع فبعلامةٍ أخطأت**. -/
theorem qat_bi_khata (as : List (Alama α)) (p : α × Qism) (h : p.2 ∉ cands as p.1) :
    ∃ a ∈ as, khata a p = true := by
  apply Classical.byContradiction
  intro hn
  exact h (haqq_baqi as p fun a ha => by
    cases hk : khata a p
    · rfl
    · exact absurd ⟨a, ha, hk⟩ hn)

/-- خطأُ القارئ في الموضع: عيّن قسمًا غيرَ قسمه. -/
def khataQari (as : List (Alama α)) (p : α × Qism) : Bool :=
  (cands as p.1).length == 1 && !((cands as p.1).contains p.2)

theorem countP_or_le (l : List β) (f g : β → Bool) :
    l.countP (fun x => f x || g x) ≤ l.countP f + l.countP g := by
  induction l with
  | nil => simp
  | cons x xs ih =>
    simp only [List.countP_cons]
    cases f x <;> cases g x <;> simp <;> omega

theorem countP_mono (l : List β) (f g : β → Bool) (h : ∀ x ∈ l, f x = true → g x = true) :
    l.countP f ≤ l.countP g := by
  induction l with
  | nil => simp
  | cons x xs ih =>
    simp only [List.countP_cons]
    have ih' := ih fun y hy => h y (List.mem_cons_of_mem _ hy)
    cases hf : f x
    · cases g x <;> simp <;> omega
    · simp [h x (List.mem_cons_self ..) hf]; omega

theorem countP_any_le (l : List β) (as : List γ) (k : γ → β → Bool) :
    l.countP (fun x => as.any (fun a => k a x)) ≤ (as.map fun a => l.countP (k a)).sum := by
  induction as with
  | nil => simp
  | cons a as ih =>
    simp only [List.any_cons, List.map_cons, List.sum_cons]
    exact Nat.le_trans (countP_or_le l _ _) (Nat.add_le_add_left ih _)

/-- **خطأُ القارئ لا يزيد على مجموع أخطاء علاماته**، لكلّ مرجعٍ ولكلّ علامات. فخطأُ المعيَّن يُقاس علامةً علامة. -/
theorem khata_qari_le (as : List (Alama α)) (R : List (α × Qism)) :
    R.countP (khataQari as) ≤ (as.map fun a => R.countP (khata a)).sum := by
  refine Nat.le_trans (countP_mono R _ (fun p => as.any (fun a => khata a p)) ?_)
    (countP_any_le R as khata)
  intro p _ hp
  have hn : p.2 ∉ cands as p.1 := by
    intro hm
    have hc : (cands as p.1).contains p.2 = true := List.contains_iff_mem.mpr hm
    simp [khataQari] at hp
    exact hp.2 hm
  obtain ⟨a, ha, hk⟩ := qat_bi_khata as p hn
  exact List.any_eq_true.mpr ⟨a, ha, hk⟩

theorem sum_map_zero (l : List γ) (f : γ → Nat) (h : ∀ a ∈ l, f a = 0) : (l.map f).sum = 0 := by
  induction l with
  | nil => rfl
  | cons a l ih =>
    simp only [List.map_cons, List.sum_cons]
    rw [h a (List.mem_cons_self ..), ih fun b hb => h b (List.mem_cons_of_mem _ hb)]

/-- **وبلا خطأ علامةٍ لا خطأَ للقارئ**. -/
theorem salim_la_khata (as : List (Alama α)) (R : List (α × Qism))
    (h : ∀ a ∈ as, R.countP (khata a) = 0) : R.countP (khataQari as) = 0 := by
  have := khata_qari_le as R
  have hz : (as.map fun a => R.countP (khata a)).sum = 0 := sum_map_zero as _ h
  omega

theorem two_le_length {l : List Qism} {a b : Qism} (ha : a ∈ l) (hb : b ∈ l) (hab : a ≠ b) :
    2 ≤ l.length := by
  match l with
  | [] => simp at ha
  | [x] => simp at ha hb; exact absurd (ha.trans hb.symm) hab
  | _ :: _ :: _ => simp

/-- **المشتركُ لا يُعيَّن**: صورةٌ بقسمين في المرجع، ولا خطأَ فيهما، فالقارئُ يتركها محتمَلة. -/
theorem mushtarak_muhtamal (as : List (Alama α)) (x : α) (q₁ q₂ : Qism) (hne : q₁ ≠ q₂)
    (h₁ : ∀ a ∈ as, khata a (x, q₁) = false) (h₂ : ∀ a ∈ as, khata a (x, q₂) = false) :
    2 ≤ (cands as x).length :=
  two_le_length (haqq_baqi as (x, q₁) h₁) (haqq_baqi as (x, q₂) h₂) hne

/-! ## السقف: لكلّ دالّةٍ في الصورة

المرجعُ جدولٌ: لكلّ صورةٍ عددُ مواضعها في كلّ قسم. -/

structure Adad where
  i : Nat
  f : Nat
  h : Nat
  deriving DecidableEq, Repr

def Adad.at (c : Adad) : Qism → Nat
  | .ism => c.i
  | .fil => c.f
  | .harf => c.h

def Adad.max3 (c : Adad) : Nat := max c.i (max c.f c.h)
def Adad.sum3 (c : Adad) : Nat := c.i + c.f + c.h
def Adad.add (c d : Adad) : Adad := ⟨c.i + d.i, c.f + d.f, c.h + d.h⟩

theorem at_le_max3 (c : Adad) (q : Qism) : c.at q ≤ c.max3 := by
  cases q <;> simp [Adad.at, Adad.max3] <;> omega

/-- ما تصيبه دالّةٌ في الصورة. -/
def hits (g : α → Qism) (T : List (α × Adad)) : Nat := (T.map fun p => p.2.at (g p.1)).sum

def saqf (T : List (α × Adad)) : Nat := (T.map fun p => p.2.max3).sum
def jumla (T : List (α × Adad)) : Nat := (T.map fun p => p.2.sum3).sum

/-- **لا دالّةَ في الصورة تزيد على السقف**. -/
theorem hits_le_saqf (g : α → Qism) (T : List (α × Adad)) : hits g T ≤ saqf T := by
  induction T with
  | nil => simp [hits, saqf]
  | cons p T ih =>
    simp only [hits, saqf, List.map_cons, List.sum_cons] at *
    exact Nat.add_le_add (at_le_max3 _ _) ih

def argmax (c : Adad) : Qism :=
  if c.f ≤ c.i ∧ c.h ≤ c.i then .ism else if c.h ≤ c.f then .fil else .harf

theorem at_argmax (c : Adad) : c.at (argmax c) = c.max3 := by
  unfold argmax Adad.max3
  split
  · simp [Adad.at]; omega
  · split <;> simp [Adad.at] <;> omega

theorem max3_le_sum3 (c : Adad) : c.max3 ≤ c.sum3 := by simp [Adad.max3, Adad.sum3]; omega

/-- **صورةٌ بقسمين تُنزل السقفَ دون الكلّ**: فالقسمُ ليس دالّةً في الصورة. -/
theorem saqf_lt_jumla (T : List (α × Adad)) (x : α) (c : Adad) (hm : (x, c) ∈ T)
    (h2 : 2 ≤ ([c.i, c.f, c.h].filter (· > 0)).length) : saqf T < jumla T := by
  have hc : c.max3 < c.sum3 := by
    simp only [Adad.max3, Adad.sum3]
    rcases c with ⟨a, b, d⟩
    simp only [List.filter] at h2
    by_cases ha : a > 0 <;> by_cases hb : b > 0 <;> by_cases hd : d > 0 <;> simp_all <;> omega
  induction T with
  | nil => simp at hm
  | cons p T ih =>
    simp only [saqf, jumla, List.map_cons, List.sum_cons] at *
    have hle : ∀ T' : List (α × Adad), (T'.map fun p => p.2.max3).sum ≤ (T'.map fun p => p.2.sum3).sum := by
      intro T'
      induction T' with
      | nil => simp
      | cons q T' ih' => simp only [List.map_cons, List.sum_cons]; exact Nat.add_le_add (max3_le_sum3 _) ih'
    rcases List.mem_cons.mp hm with rfl | hm
    · exact Nat.add_lt_add_of_lt_of_le hc (hle T)
    · exact Nat.add_lt_add_of_le_of_lt (max3_le_sum3 _) (ih hm)

/-- **المزجُ لا يرفع السقف**، لدمجٍ واحدٍ في رأس الجدول: صورتان تُنسى بينهما بتّةٌ أو رتبةٌ فتصيران صورةً واحدة.
وتعميمُه إلى كلّ دالّةِ مفاتيح (تكرارُ الدمج وثباتُ السقف تحت التبديل) غيرُ مكتوب: `DAMJ_GENERAL_NOT_PROVEN`. -/
theorem damj_la_yazid (x y : α) (c d : Adad) (T : List (α × Adad)) :
    saqf ((x, c.add d) :: T) ≤ saqf ((x, c) :: (y, d) :: T) := by
  simp only [saqf, List.map_cons, List.sum_cons, Adad.max3, Adad.add]
  omega

variable [DecidableEq α]

def lookupA (T : List (α × Adad)) (x : α) : Adad :=
  match T.find? (fun p => decide (p.1 = x)) with
  | some p => p.2
  | none => ⟨0, 0, 0⟩

/-- الدالّةُ الحافظة: أكثرُ قسمٍ لكلّ صورة. -/
def hafiz (T : List (α × Adad)) (x : α) : Qism := argmax (lookupA T x)

theorem lookupA_nodup (T : List (α × Adad)) (hT : (T.map Prod.fst).Nodup) :
    ∀ p ∈ T, lookupA T p.1 = p.2 := by
  induction T with
  | nil => simp
  | cons q T ih =>
    simp only [List.map_cons, List.nodup_cons, List.mem_map] at hT
    intro p hp
    rcases List.mem_cons.mp hp with rfl | hp
    · simp [lookupA]
    · have hne : p.1 ≠ q.1 := fun he => hT.1 ⟨p, hp, he⟩
      have := ih hT.2 p hp
      simp only [lookupA, List.find?_cons, decide_eq_false (Ne.symm hne)] at this ⊢
      exact this

theorem hits_eq_saqf_of (T₀ T : List (α × Adad)) (h : ∀ p ∈ T, lookupA T₀ p.1 = p.2) :
    hits (hafiz T₀) T = saqf T := by
  induction T with
  | nil => rfl
  | cons p T ih =>
    simp only [hits, saqf, List.map_cons, List.sum_cons] at *
    rw [ih fun q hq => h q (List.mem_cons_of_mem _ hq), hafiz,
      h p (List.mem_cons_self ..), at_argmax]

/-- **والسقفُ يُبلغ** إن تباينت الصور: الحافظُ يبلغه. -/
theorem saqf_mablugh (T : List (α × Adad)) (hT : (T.map Prod.fst).Nodup) :
    hits (hafiz T) T = saqf T :=
  hits_eq_saqf_of T T (lookupA_nodup T hT)

/-! ## الشواهد على الخانات (`decide`)

الخاناتُ من `Itar.k`. وأقسامُ الشواهد من مرجع QAC، وأعدادُها في `result.json` على B. -/

def cell (s : String) : List Cell := Itar.k s

def takhir (w : List Cell) (n : Nat) : List Cell := w.drop (w.length - n)

/-- `TA_SAKINA` (ابن عقيل س265–267): «تاء التأنيث الساكنة … فاحترزنا بالساكنة عن اللاحقة للأسماء فإنها تكون متحركة
بحركة الإعراب». وفي الخانات تاءُ الاسم المربوطة خانةٌ متحرّكة: «رَحْمَةُ» (تُ) تُفرَّق من «قَالَتْ» (تْ) ببتّتَي الحالة
وحدَهما، و«رَحْمَةً» آخرُها نْ فلا تُطلقها لاختلاف الحرف. والخاناتُ هنا مكتوبةٌ باليد، لا ذرّاتُ بوّابة. -/
def taSakina : Alama (List Cell × Option (List Cell)) where
  tutabiq x := match takhir x.1 2 with
    | [a, b] => a.haraka == .fatha && b == (cell "تْ").headD a
    | _ => false
  tubqi := [.fil]

/-- `BAD_LAM_LAN_SAWFA` (الكتاب س124–125، س129): «لن يفعل … لم يفعل … وسوف يفعل». -/
def badLam : Alama (List Cell × Option (List Cell)) where
  tutabiq x := x.2 == some (cell "لَمْ") || x.2 == some (cell "لَنْ") || x.2 == some (cell "سَوْفَ")
  tubqi := [.fil]

/-- `HARF_LAFZ` (الكتاب س110: «فنحو ثم وسوف»؛ ابن عقيل س280: «كهل وفي ولم»). -/
def harfLafz : Alama (List Cell × Option (List Cell)) where
  tutabiq x := [cell "ثُمْمَ", cell "سَوْفَ", cell "هَلْ", cell "فِيْ", cell "لَمْ"].contains x.1
  tubqi := [.harf]

def alAt (r : List Cell) : Bool :=
  (r.take 2 == cell "ءَلْ" && 2 < r.length) || (r.take 1 == cell "لْ" && 1 < r.length)

/-- `AL` بنمط التسجيل بعينه (الكتاب س130: «كما تلحق الألف واللام الأسماء للمعرفة»): بعد خانةٍ اختياريّةٍ من
{وَ، فَ، بِ، كَ، لِ}، «ءَلْ» أو «لْ» ثمّ خانةٌ على الأقلّ. ولم تُبقِها قاعدةُ الاختيار. -/
def al : Alama (List Cell × Option (List Cell)) where
  tutabiq x := alAt x.1 ||
    ([cell "وَ", cell "فَ", cell "بِ", cell "كَ", cell "لِ"].contains (x.1.take 1) && alAt (x.1.drop 1))
  tubqi := [.ism]

def alamat : List (Alama (List Cell × Option (List Cell))) := [taSakina, badLam, harfLafz]

/-- تاءُ «قَالَتْ» ساكنةٌ فعل، وتاءُ «رَحْمَةً» و«رَحْمَةُ» متحرّكةٌ لا تُطلقها. -/
theorem ta_sakina_shahid :
    qiraa alamat (cell "قَاْلَتْ", none) = .muayyan .fil ∧
    taSakina.tutabiq (cell "رَحْمَتَنْ", none) = false ∧
    taSakina.tutabiq (cell "رَحْمَتُ", none) = false := by
  decide +kernel

/-- «لَمْ يَكُنْ» فعل، و«ثُمَّ» حرف، و«يَكُنْ» وحدَها بلا سياق «محتمَل»: لا علامةَ تقطع. -/
theorem shawahid :
    qiraa alamat (cell "يَكُنْ", some (cell "لَمْ")) = .muayyan .fil ∧
    qiraa alamat (cell "ثُمْمَ", none) = .muayyan .harf ∧
    qiraa alamat (cell "يَكُنْ", none) = .muhtamal [.ism, .fil, .harf] := by
  decide +kernel

/-- **أداةُ التعريف في الخانات تشتبه بغيرها**: «أَلَّا» و«كَلَّا» (حرفان)، و«فَلْيَتَوَكَّلْ» (لامُ الأمر)، و«أَلْقَى»
(لامُ الأصل) تُطلقها كـ«الْكِتَابُ» و«وَالْكِتَابِ». وأخطاؤها على A بهذا النمط 85 من 4,804: 39 حرفًا، و27 لامَ أمر،
و19 لامَ أصل. -/
theorem al_yashtabih :
    al.tutabiq (cell "ءَلْلَاْ", none) = true ∧ al.tutabiq (cell "كَلْلَاْ", none) = true ∧
    al.tutabiq (cell "فَلْيَتَوَكْكَلْ", none) = true ∧ al.tutabiq (cell "ءَلْقَاْ", none) = true ∧
    al.tutabiq (cell "ءَلْكِتَاْبُ", none) = true ∧ al.tutabiq (cell "وَلْكِتَاْبِ", none) = true ∧
    al.tutabiq (cell "كِتَاْبُ", none) = false := by
  decide +kernel

/-- **«مَا» و«أَعْلَمُ» بقسمين في المرجع** (على B: «مَا» 437 اسمًا و115 حرفًا، «أَعْلَمُ» 30 اسمًا و5 أفعال)، فالسقفُ
دون الكلّ ولا دالّةَ في الخانات تصيبهما كلَّهما. -/
def shahidJadwal : List (List Cell × Adad) :=
  [(cell "مَاْ", ⟨437, 0, 115⟩), (cell "ءَعْلَمُ", ⟨30, 5, 0⟩)]

theorem ma_alam : saqf shahidJadwal = 467 ∧ jumla shahidJadwal = 587 ∧
    ∀ g : List Cell → Qism, hits g shahidJadwal ≤ 467 := by
  refine ⟨by decide +kernel, by decide +kernel, fun g => ?_⟩
  have := hits_le_saqf g shahidJadwal
  have h : saqf shahidJadwal = 467 := by decide +kernel
  omega

end A116.QismKhanat
