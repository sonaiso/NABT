import A116.Neutral
import A116.RootGrade
import A116.Mudari

/-!
# التصريفُ على الخانات: الماضي المجرّد بأبوابه الثلاثة ← المضارع ← الأمر، والمعتلُّ داخلَ الترخيص

قرارُ المالك (2026-10-12): «المعتلُّ يجب أن يكون داخلًا وفق قانون الابتداء وقانون الوصل وقانون الوقف ويكون
مرخَّصًا وبالاستنفاد للفعل الماضي المجرّد بصيغ فتح فتح فتح وفتح ضمّ فتح وفتح كسر فتح، ويُرخَّص المضارع من
صيغ الماضي، ويُرخَّص الأمرُ بحذف الزوائد»؛ و«الاستنفادُ داخل الثلاثيّ يجب أن يُبرهَن في كلّ موضعٍ من كلّ وزن».

## الصفة: الجذرُ تقييمٌ، والإعلالُ دالّةٌ في صنف الأصل لا في حامله

صنفُ الحامل (`cls`) خمسة: واو، ياء، همزة، لام، صحيح. وصفةُ الجذر (`sifa`) أصنافُ أصوله الثلاثة وأنّ العينَ
واللامَ مثلان. كلُّ صيغةٍ هنا **قالبٌ تحسبه الصفةُ وحدَها** (`madi`، `mudari`، `amr`) ثمّ يُقيَّم بالجذر
(`fillC`، دالّةُ آرتين من `Wazn`): الأصلُ غيرُ الصحيح حاملُه معيَّنٌ بصنفه فيدخل القالبَ حرفًا (`rad`،
`rad_eval`: التقييمُ لا يتغيّر)، والصحيحُ يبقى متغيّرًا. فالإعلالُ (قلبٌ، نقلٌ، حذف) قواعدُ على القالب
بشروطٍ في الصفة.

## النقل: من الصفة إلى كلّ جذر

`transfer_strict`/`transfer_pause`: جذران متّفقان في الصفة صورتاهما بإسقاطٍ واحد على `cv | v | c`
(`Wazn.kindGo_prof`)، فإن لم يتلُ مدٌّ ساكنًا (`noVC`) فقيدُ الحدّ قائمٌ بلا نظرٍ في الحوامل
(`haddB_of_noVC`). فما قُرِّر على الصفات الـ250 (`allSifa`) بالنواة يصحّ **لكلّ جذرٍ** لا ألفَ فيه — منه
الـ‎28³‎ جذرًا من جدول الدرجة (`RootGrade.table 3`).

## ما يُبرهَن

* `every_position`: كلُّ وزنٍ من الإحدى والثلاثين، على **كلّ** جذرٍ أصولُه من الستّة والعشرين غيرِ المعتلّة
  (الحواملُ إلّا ا و ي، والهمزةُ واللامُ منها)، مرخَّصٌ ابتداءً وصلًا ووقفًا وخاناتُه من المرخَّص؛ و
  `every_cell_in_every_slot`: كلُّ خانةٍ في موضعِ كلِّ أصلٍ من كلِّ وزنٍ تقع بكلّ حاملٍ منها.
* `madi_exhausted`: الماضي المجرّد بأبوابه الثلاثة (فَعَلَ، فَعِلَ، فَعُلَ) على **كلّ** جذرٍ — المعتلُّ
  والمهموزُ والمضعَّفُ واللفيفُ منه — مرخَّصٌ ابتداءً وصلًا ووقفًا، وخاناتُه من المرخَّص.
* `mudari_exhausted`: المضارعُ من كلّ جذرٍ بحروف المضارعة الأربعة (أ ن ي ت) وحركاتِ العين الثلاث
  والرفعِ والنصبِ والجزم، مجرّدًا وأَفْعَلَ، كذلك.
* `amr_exhausted`: الأمرُ بحذف حرف المضارعة من المجزوم (وهمزةِ وصلٍ حركتُها من الثالث إن بدأ بساكن)،
  مرخَّصٌ وصلًا، ووقفُه مرخَّص.
* `madd_drop_forced`: **حذفُ المدّ في مجزوم الأجوف ملزَمٌ بقيد الحدّ لكلّ جذر**: تَقُومْ قافيةُ مدٍّ غيرُ مدغمة
  (`CVVC_NOT_GEMINATE`) فتصير تَقُمْ ثمّ قُمْ.
* `haa_forced`: **الكلمةُ حرفًا واحدًا لا يوقَف عليها**: وقفُ كلّ خانةٍ متحرّكةٍ وحدَها غيرُ مرخَّص، ومعها هاءُ
  السكت مرخَّص — «هذا باب ما يلحق الكلمة إذا اختلت حتى تصير حرفًا فلا يستطاع أن يتكلم بها في الوقف… عِهْ
  وشِهْ» (الكتاب، السطر 17497–17499 من المختوم).
* `taqi_not_syllable_forced`: «لا تَقِهْ… يلزمها الهاء في الوقف… لأنها ذهبت منها الفاء واللام» (17697–17700):
  تَقْ مرخَّصةٌ وقفًا، فلزومُ الهاء هنا **بعدد الأصول الباقية** (أصلٌ واحد) لا بالمقطع — قاعدةٌ مودَعة
  (`amrPause`) لا مبرهنةٌ لغويّة.
* الشواهدُ بخاناتها: قَامَ يَقُومُ قُمْ، نَامَ يَنَامُ نَمْ، وَقَى يَقِي قِ قِهْ، وَعَى يَعِي عِ عِهْ، نَمَا
  يَنْمُو تَنْمُو نَنْمُو أَنْمُو اُنْمُ، أَخَذَ يَأْخُذُ آخُذُ اُوخُذْ وخُذْ، أَعْطَى يُعْطِي تُعْطِي نُعْطِي أُعْطِي
  أَعْطِ، مَدَّ يَمُدُّ يَمْدُدْ اُمْدُدْ.

ولا يُبرهَن هنا أنّ هذه صيغُ العربيّة: Lean يبرهن خواصَّ القواعد المعلَنة على الخانات؛ ومطابقتُها للمرويّ
شاهدٌ مفحوصٌ على المصحف (`tests/test_tasrif.py`). والأبوابُ الستّة (أيُّ حركةِ عينٍ في المضارع لأيّ باب) وضعٌ
لا ترخيص: الترخيصُ هنا للتسع كلِّها.
-/

set_option autoImplicit false

namespace A116.Tasrif

open A116 A116.Stages A116.Ternary A116.Ladder A116.Hadd A116.Boundary A116.Wazn

/-! ## ١. الصنفُ والصفة -/

inductive Cls where
  | waw | ya | hamz | lam | sahih
  deriving DecidableEq, Repr

def cls (k : Fin carrierCount) : Cls :=
  if k == carrierOf 'و' then .waw
  else if k == carrierOf 'ي' then .ya
  else if k == hamza then .hamz
  else if k == carrierOf 'ل' then .lam
  else .sahih

/-- الحاملُ المعيَّنُ بالصنف (الصحيحُ وحدَه متغيّر). -/
def Cls.carrier? : Cls → Option (Fin carrierCount)
  | .waw => some (carrierOf 'و')
  | .ya => some (carrierOf 'ي')
  | .hamz => some hamza
  | .lam => some (carrierOf 'ل')
  | .sahih => none

def Cls.weak : Cls → Bool
  | .waw | .ya => true
  | _ => false

def Cls.ch : Cls → Char
  | .ya => 'ي'
  | _ => 'و'

structure Sifa where
  c0 : Cls
  c1 : Cls
  c2 : Cls
  e12 : Bool
  deriving DecidableEq, Repr

def Sifa.get (s : Sifa) : Fin 3 → Cls
  | ⟨0, _⟩ => s.c0
  | ⟨1, _⟩ => s.c1
  | _ => s.c2

def sifa (r : Root 3) : Sifa := ⟨cls (r 0), cls (r 1), cls (r 2), r 1 == r 2⟩

def allCls : List Cls := [.waw, .ya, .hamz, .lam, .sahih]

def allSifa : List Sifa :=
  allCls.flatMap fun a => allCls.flatMap fun b => allCls.flatMap fun c =>
    [true, false].map fun e => ⟨a, b, c, e⟩

theorem mem_allCls (c : Cls) : c ∈ allCls := by cases c <;> decide

theorem mem_allSifa (s : Sifa) : s ∈ allSifa := by
  obtain ⟨a, b, c, e⟩ := s
  simp only [allSifa, List.mem_flatMap, List.mem_map]
  exact ⟨a, mem_allCls a, b, mem_allCls b, c, mem_allCls c, e, by cases e <;> simp, rfl⟩

theorem allSifa_length : allSifa.length = 250 := by
  decide +kernel

/-- الجذرُ الممثِّل للصفة: كلُّ صحيحٍ كاف. -/
def rep (s : Sifa) : Root 3 := fun i => ((s.get i).carrier?).getD (carrierOf 'ك')

/-- الأصلُ i بحالته في القالب: حرفًا إن عيّنه صنفُه، ومتغيّرًا إن كان صحيحًا. -/
def rad (s : Sifa) (i : Fin 3) (h : Haraka) : CSym 3 :=
  match (s.get i).carrier? with
  | some k => .lit ⟨k, h⟩
  | none => .slot i h

theorem cls_carrier : ∀ k : Fin carrierCount, ((cls k).carrier?).all (· == k) = true := by
  decide +kernel

theorem sifa_get (r : Root 3) (i : Fin 3) : (sifa r).get i = cls (r i) := by
  match i with
  | ⟨0, _⟩ => rfl
  | ⟨1, _⟩ => rfl
  | ⟨2, _⟩ => rfl

/-- **التقييمُ لا يتغيّر**: الأصلُ حرفًا في القالب هو حاملُ الجذر بعينه. -/
theorem rad_eval (r : Root 3) (i : Fin 3) (h : Haraka) : eval r (rad (sifa r) i h) = ⟨r i, h⟩ := by
  unfold rad
  rw [sifa_get]
  have hc := cls_carrier (r i)
  split
  · rename_i k hk
    rw [hk] at hc
    simp only [Option.all_some, beq_iff_eq] at hc
    simp [eval, hc]
  · rfl

/-! ## ٢. النقلُ من الصفة إلى كلّ جذر -/

def NoAlif {n : Nat} (r : Root n) : Prop := ∀ i, r i ≠ carrierOf 'ا'

def Agree {n : Nat} (r r' : Root n) : Prop := ∀ i, cls (r i) = cls (r' i)

theorem madd_of_cls : ∀ k k' : Fin carrierCount, k ≠ carrierOf 'ا' → k' ≠ carrierOf 'ا' →
    cls k = cls k' → maddVowel k = maddVowel k' := by decide +kernel

theorem cls_rep : ∀ k : Fin carrierCount, cls k = cls (((cls k).carrier?).getD (carrierOf 'ك')) := by
  decide +kernel

theorem rep_agree (r : Root 3) : Agree r (rep (sifa r)) := by
  intro i
  simp only [rep, sifa_get]
  exact cls_rep (r i)

theorem rep_noAlif (s : Sifa) : NoAlif (rep s) := by
  intro i
  simp only [rep]
  cases s.get i <;> decide

theorem kindOf_agree {n : Nat} (t : List (CSym n)) {r r' : Root n} (hr : NoAlif r) (hr' : NoAlif r')
    (ha : Agree r r') : kindOf (fillC t r) = kindOf (fillC t r') := by
  have hm : MaddEq r r' := fun i => madd_of_cls _ _ (hr i) (hr' i) (ha i)
  apply kindGo_prof
  simp only [fillC, List.map_map]
  exact List.map_congr_left (fun s _ => prof_eval hm s)

/-- لا مدَّ يتلوه ساكن. -/
def noVC : List K → Bool
  | .v :: .c :: _ => false
  | _ :: t => noVC t
  | [] => true

/-- لا مدَّ يتلوه ساكنٌ إلّا في الطرف (الوقف). -/
def noVCP : List K → Bool
  | [.v, .c] => true
  | .v :: .c :: _ => false
  | _ :: t => noVCP t
  | [] => true

theorem geminateB_of_noVC : ∀ (p : List (K × Cell)), noVC (p.map Prod.fst) = true → geminateB p = true
  | [], _ => rfl
  | [a], _ => by cases a with | mk k x => cases k <;> rfl
  | a :: b :: t, h => by
    obtain ⟨ka, x⟩ := a
    obtain ⟨kb, y⟩ := b
    have ih := geminateB_of_noVC ((kb, y) :: t)
    cases ka <;> cases kb <;> simp_all [noVC, geminateB, stepOK]

theorem noVC_drop : ∀ (n : Nat) (l : List K), noVC l = true → noVC (l.drop n) = true
  | 0, _, h => h
  | _ + 1, [], _ => rfl
  | n + 1, [a], h => by cases n <;> simp [noVC]
  | n + 1, a :: b :: t, h => by
    have : noVC (b :: t) = true := by
      cases a <;> cases b <;> simp_all [noVC]
    simpa using noVC_drop n (b :: t) this

theorem map_fst_zip (k : List K) (w : List Cell) (h : k.length = w.length) :
    (k.zip w).map Prod.fst = k := by
  induction k generalizing w with
  | nil => rfl
  | cons a t ih =>
    cases w with
    | nil => simp at h
    | cons x u => simp [ih u (by simpa using h)]

theorem haddB_of_noVC (w : List Cell) (h : noVC (kindOf w) = true) : haddB w = true := by
  have hl : (kindOf w).length = w.length := kindGo_length _ _
  have hz := map_fst_zip _ _ hl
  unfold haddB
  split
  · apply geminateB_of_noVC
    rw [List.map_drop, hz]
    exact noVC_drop 2 _ h
  · apply geminateB_of_noVC
    rw [hz]; exact h

theorem geminatePauseB_of_noVCP : ∀ (p : List (K × Cell)), noVCP (p.map Prod.fst) = true →
    geminatePauseB p = true
  | [], _ => rfl
  | [a], _ => by cases a with | mk k x => cases k <;> rfl
  | [a, b], h => by
    obtain ⟨ka, x⟩ := a
    obtain ⟨kb, y⟩ := b
    cases ka <;> cases kb <;> simp_all [noVCP, geminatePauseB, stepOKPause, stepOK]
  | a :: b :: c :: t, h => by
    obtain ⟨ka, x⟩ := a
    obtain ⟨kb, y⟩ := b
    have ih := geminatePauseB_of_noVCP ((kb, y) :: c :: t)
    cases ka <;> cases kb <;> simp_all [noVCP, geminatePauseB, stepOKPause, stepOK]

theorem noVCP_drop : ∀ (n : Nat) (l : List K), noVCP l = true → noVCP (l.drop n) = true
  | 0, _, h => h
  | _ + 1, [], _ => rfl
  | n + 1, [a], h => by cases n <;> simp [noVCP]
  | n + 1, a :: b :: t, h => by
    have : noVCP (b :: t) = true := by
      cases t with
      | nil => cases b <;> simp [noVCP]
      | cons x u => cases a <;> cases b <;> simp_all [noVCP]
    simpa using noVCP_drop n (b :: t) this

theorem haddPauseB_of_noVCP (w : List Cell) (h : noVCP (kindOf w) = true) : haddPauseB w = true := by
  have hl : (kindOf w).length = w.length := kindGo_length _ _
  have hz := map_fst_zip _ _ hl
  unfold haddPauseB
  split
  · apply geminatePauseB_of_noVCP
    rw [List.map_drop, hz]
    exact noVCP_drop 2 _ h
  · apply geminatePauseB_of_noVCP
    rw [hz]; exact h

/-- **النقلُ وصلًا**: ما رُخِّص على الممثِّل بلا مدٍّ يتلوه ساكن مرخَّصٌ على كلّ جذرٍ يوافقه. -/
theorem transfer_strict {n : Nat} (t : List (CSym n)) {r r' : Root n} (hr : NoAlif r) (hr' : NoAlif r')
    (ha : Agree r r') (hc : contCheck (fillC t r') = true) (hv : noVC (kindOf (fillC t r')) = true) :
    strictB (fillC t r) = true := by
  have hk := kindOf_agree t hr hr' ha
  have hs := strictB_of_check hc
  unfold strictB at hs ⊢
  simp only [Bool.and_eq_true] at hs ⊢
  refine ⟨hk ▸ hs.1, haddB_of_noVC _ (hk ▸ hv)⟩

/-- **النقلُ وقفًا**. -/
theorem transfer_pause {n : Nat} (t : List (CSym n)) {r r' : Root n} (hr : NoAlif r) (hr' : NoAlif r')
    (ha : Agree r r') (hc : pauseCheck (fillC t r') = true) (hv : noVCP (kindOf (fillC t r')) = true) :
    strictPauseB (fillC t r) = true := by
  have hk := kindOf_agree t hr hr' ha
  have hs := strictPauseB_of_check hc
  unfold strictPauseB at hs ⊢
  simp only [Bool.and_eq_true] at hs ⊢
  refine ⟨hk ▸ hs.1, haddPauseB_of_noVCP _ (hk ▸ hv)⟩

/-- حروفُ القالب كلُّها من المرخَّص. -/
def litsOK {n : Nat} (t : List (CSym n)) : Bool :=
  t.all fun s => match s with
    | .lit c => Alif.licensable.contains c
    | .slot _ _ => true

theorem licensable_of_ne_alif : ∀ c ∈ cells, c.carrier ≠ carrierOf 'ا' →
    Alif.licensable.contains c = true := by decide +kernel

theorem lits_licensable {n : Nat} (t : List (CSym n)) {r : Root n} (hr : NoAlif r) (h : litsOK t = true) :
    (fillC t r).all (Alif.licensable.contains ·) = true := by
  simp only [litsOK, List.all_eq_true] at h
  simp only [fillC, List.all_map, List.all_eq_true, Function.comp]
  intro s hs
  have := h s hs
  cases s with
  | lit c => simpa [eval] using this
  | slot i h' => exact licensable_of_ne_alif _ (mem_cells _) (hr i)

/-! ## ٣. كلُّ موضعٍ من كلّ وزن: الإحدى والثلاثون على كلّ جذرٍ غيرِ معتلّ -/

/-- الوزنُ في سياقه قالبًا: همزةُ الوصل بحركتها حرفٌ، والجسمُ والأصلُ الأخير متغيّرات. -/
def waznT {n : Nat} (W : WaznC n) (wh : Haraka) (entry : Entry) (exit : Exit) (h : Haraka) : List (CSym n) :=
  (if W.wasl && entry == .start then [.lit ⟨hamza, wh⟩] else []) ++
    W.body ++ [.slot W.last (if exit == .pause then .sukun else h)]

theorem realize_eq_fill {n : Nat} (W : WaznC n) (r : Root n) (en : Entry) (ex : Exit) (h : Haraka) :
    realize W r en ex h = fillC (waznT W (waslH W r) en ex h) r := by
  unfold realize waznT
  simp only [fillC_append]
  split <;> simp [fillC, eval]

def Sahih (r : Root 3) : Prop := ∀ i, (cls (r i)).weak = false

theorem lam_of_cls : ∀ k k' : Fin carrierCount, cls k = cls k' →
    (k = carrierOf 'ل' ↔ k' = carrierOf 'ل') := by decide +kernel

theorem lamEq_of_agree {n : Nat} {r r' : Root n} (ha : Agree r r') : LamEq r r' :=
  fun i => lam_of_cls _ _ (ha i)

/-- الجذورُ غيرُ المعتلّة بأصنافها: همزة/لام/صحيح في كلّ موضع (27 صفةً). -/
def sahihSifas : List Sifa := allSifa.filter fun s => !s.c0.weak && !s.c1.weak && !s.c2.weak

theorem every_position_check :
    sahihSifas.all (fun s => ((List.range thulathi.length).zip thulathi).all fun (i, W) =>
      let r := rep s
      let tc := waznT W (waslH W r) .start .continue (lastH i)
      let tp := waznT W (waslH W r) .start .pause (lastH i)
      contCheck (fillC tc r) && noVC (kindOf (fillC tc r)) &&
      pauseCheck (fillC tp r) && noVCP (kindOf (fillC tp r)) && litsOK tc && litsOK tp) = true := by
  decide +kernel

/-- **كلُّ وزنٍ ثلاثيٍّ على كلّ جذرٍ غيرِ معتلّ** مرخَّصٌ ابتداءً وصلًا ووقفًا، وخاناتُه من المرخَّص. -/
theorem every_position (r : Root 3) (hr : NoAlif r) (hs : Sahih r) :
    ∀ p ∈ (List.range thulathi.length).zip thulathi,
      strictB (realize p.2 r .start .continue (lastH p.1)) = true ∧
      strictPauseB (realize p.2 r .start .pause (lastH p.1)) = true ∧
      (realize p.2 r .start .continue (lastH p.1)).all (Alif.licensable.contains ·) = true := by
  intro p hp
  let s := sifa r
  have hmem : s ∈ sahihSifas := by
    simp only [sahihSifas, List.mem_filter, Bool.and_eq_true, Bool.not_eq_true']
    refine ⟨mem_allSifa s, ⟨⟨hs 0, hs 1⟩, hs 2⟩⟩
  have h := every_position_check
  rw [List.all_eq_true] at h
  have h2 := h s hmem
  rw [List.all_eq_true] at h2
  have h3 := h2 p hp
  simp only [Bool.and_eq_true] at h3
  obtain ⟨⟨⟨⟨⟨hc, hv⟩, hpc⟩, hpv⟩, hl⟩, _⟩ := h3
  have ha := rep_agree r
  have hw : waslH p.2 r = waslH p.2 (rep s) := waslH_eq p.2 (lamEq_of_agree ha)
  simp only [realize_eq_fill]
  rw [hw]
  exact ⟨transfer_strict _ hr (rep_noAlif s) ha hc hv,
    transfer_pause _ hr (rep_noAlif s) ha hpc hpv,
    lits_licensable _ hr hl⟩

/-- **كلُّ خانةٍ في موضعِ كلّ أصلٍ من كلّ وزن**: الأصلُ i بحالته h في جسم الوزن يقع بكلّ حاملٍ غيرِ معتلّ
(من الستّة والعشرين) في صيغةٍ مرخَّصة. -/
theorem every_cell_in_every_slot (k : Fin carrierCount) (hk : k ≠ carrierOf 'ا') (hw : (cls k).weak = false) :
    ∀ p ∈ (List.range thulathi.length).zip thulathi, ∀ i h, CSym.slot i h ∈ p.2.body →
      (⟨k, h⟩ : Cell) ∈ realize p.2 (fun _ => k) .start .continue (lastH p.1) ∧
      strictB (realize p.2 (fun _ => k) .start .continue (lastH p.1)) = true := by
  intro p hp i h hm
  refine ⟨?_, (every_position (fun _ => k) (fun _ => hk) (fun _ => hw) p hp).1⟩
  simp only [realize, List.mem_append, fillC, List.mem_map]
  exact Or.inl (Or.inr ⟨_, hm, rfl⟩)

/-! ## ٤. الماضي والمضارعُ والأمرُ قوالبَ في الصفة -/

def litC (ch : Char) (h : Haraka) : CSym 3 := .lit (atom ch h)

def alifL : CSym 3 := .lit Neutral.alifS

def hOf : CSym 3 → Haraka
  | .lit c => c.haraka
  | .slot _ h => h

/-- حرفُ المدّ المجانسُ للحركة. -/
def maddOf : Haraka → CSym 3
  | .damma => litC 'و' .sukun
  | .kasra => litC 'ي' .sukun
  | _ => alifL

/-- اللامُ المعتلّةُ بعد حركةٍ تُجانَس بها (رَضِيَ من رضو، القاعدة ١١؛ والعكس ١٢). -/
def harm (v : Haraka) (c : Cls) : Char :=
  match v with
  | .kasra => 'ي'
  | .damma => 'و'
  | _ => c.ch

def cons (c : Cls) : Bool := !c.weak

/-- **الماضي المجرّد** بحركة عينه a (فَعَلَ/فَعِلَ/فَعُلَ) وحالةِ لامه h (3MS: فتحة). -/
def madi (s : Sifa) (a h : Haraka) : List (CSym 3) :=
  let F := rad s 0 .fatha
  if cons s.c1 && cons s.c2 && s.e12 && h != .sukun then [F, rad s 1 .sukun, rad s 2 h]
  else if s.c1.weak && !s.c2.weak then [F, alifL, rad s 2 h]
  else if s.c2.weak then
    if a == .fatha && h == .fatha then [F, rad s 1 a, alifL]
    else [F, rad s 1 a, litC (harm a s.c2) h]
  else [F, rad s 1 a, rad s 2 h]

inductive Bab where
  | mujarrad
  | afala
  deriving DecidableEq, Repr

/-- حركةُ حرف المضارعة: فتحٌ في المجرّد، وضمٌّ في أَفْعَلَ. -/
def Bab.pv : Bab → Haraka
  | .mujarrad => .fatha
  | .afala => .damma

/-- **المضارع** بحرف المضارعة p وحركة العين v (في أَفْعَلَ كسرةٌ أبدًا) والإعراب m (رفع/نصب/جزم). -/
def mudari (s : Sifa) (bab : Bab) (p : Char) (v0 m : Haraka) : List (CSym 3) :=
  let v := if bab == .afala then .kasra else v0
  let P := litC p bab.pv
  -- القاعدة ٦: واوُ المثال تسقط بين ياءٍ (حرفِ مضارعةٍ مفتوح) وكسرة: يَعِدُ، يَقِي
  let dropF := bab == .mujarrad && s.c0 == .waw && v == .kasra
  -- القاعدة ٧: الهمزةُ الساكنة بعد همزةٍ مفتوحة مدّ: آخُذُ
  let F : List (CSym 3) :=
    if dropF then []
    else if p == 'ء' && bab.pv == .fatha && s.c0 == .hamz then [alifL]
    else [rad s 0 .sukun]
  let ajwaf := s.c1.weak && !s.c2.weak && cons s.c0 && !dropF
  let mudaaf := cons s.c1 && cons s.c2 && s.e12 && m != .sukun && cons s.c0 && !dropF
  -- القاعدة ٣: النقل — حركةُ العين إلى الفاء، والعينُ مدٌّ مجانس (يَقُولُ، يَنَامُ، يُقِيمُ)
  let FA : List (CSym 3) :=
    if ajwaf then
      -- قيدُ الحدّ: المدُّ قبل ساكنٍ غيرِ مدغم يُحذف في الجزم (يَقُلْ) — `madd_drop_forced`
      if m == .sukun then [rad s 0 v] else [rad s 0 v, maddOf v]
    else if mudaaf then [rad s 0 v, rad s 1 .sukun]
    else F ++ [rad s 1 v]
  let L : List (CSym 3) :=
    if s.c2.weak then
      match m with
      | .sukun => []
      | .fatha => if v == .fatha then [alifL] else [litC (harm v s.c2) .fatha]
      | _ => if v == .fatha then [alifL] else [litC (harm v s.c2) .sukun]
    else [rad s 2 m]
  P :: FA ++ L

/-- مجزومُ الأجوف قبل قيد الحدّ (تَقُومْ): المدُّ باقٍ. -/
def jussivePre (s : Sifa) (bab : Bab) (p : Char) (v0 : Haraka) : List (CSym 3) :=
  let v := if bab == .afala then .kasra else v0
  [litC p bab.pv, rad s 0 v, maddOf v, rad s 2 .sukun]

/-- **الأمر**: يُحذف حرفُ المضارعة من المجزوم؛ فإن بدأ بساكنٍ جاءت همزةُ الوصل بحركةٍ من الثالث
(`Wazn.waslVowelVerb`: ضمٌّ إن ضُمّ وإلّا كسر)، وإن تلتها همزةٌ ساكنة صارت مدًّا مجانسًا (أُوكُلْ، الكتاب
السطر 18369)؛ وفي أَفْعَلَ همزةُ القطع مفتوحة، والفاءُ المهموزةُ بعدها مدّ (آمِنْ، القاعدة ٧). -/
def amr (s : Sifa) (bab : Bab) (v : Haraka) : List (CSym 3) :=
  let t := (mudari s bab 'ت' v .sukun).tail
  match bab with
  | .afala => if t.head? == some (litC 'ء' .sukun) then litC 'ء' .fatha :: alifL :: t.tail else litC 'ء' .fatha :: t
  | .mujarrad =>
    match t with
    | x :: y :: rest =>
      if hOf x == .sukun then
        let wv := if hOf y == .damma then Haraka.damma else .kasra
        if s.c0 == .hamz then litC 'ء' wv :: maddOf wv :: y :: rest
        else litC 'ء' wv :: x :: y :: rest
      else t
    | _ => t

/-- خُذْ، كُلْ، مُرْ: الفاءُ المهموزة تُحذف من الأمر — «وأمّا ما جاء من الأفعال فخذ وكل ومر» (الكتاب، السطر
18368)؛ بقيّةٌ مسمّاة `FA_HAMZA_DROPPED_KHUDH_KUL_MUR`، والتامُّ (أُوكُلْ) قياسُ `amr`. -/
def amrKhudh (s : Sifa) (v : Haraka) : List (CSym 3) :=
  ((mudari s .mujarrad 'ت' v .sukun).drop 2)

/-- عددُ الأصول الباقية في الأمر المجرّد بعد الحذف. -/
def amrRadicals (s : Sifa) (v : Haraka) : Nat :=
  (if s.c0 == .waw && v == .kasra then 0 else 1) + 1 + (if s.c2.weak then 0 else 1)

def pauseT (t : List (CSym 3)) : List (CSym 3) :=
  match t.getLast? with
  | some (.lit c) => t.dropLast ++ [.lit ⟨c.carrier, .sukun⟩]
  | some (.slot i _) => t.dropLast ++ [.slot i .sukun]
  | none => []

/-- **وقفُ الأمر**: إن بقي أصلٌ واحد لحقته هاءُ السكت (الكتاب 17497، 17697)، وإلّا سُكِّن آخرُه. -/
def amrPause (s : Sifa) (bab : Bab) (v : Haraka) : List (CSym 3) :=
  if bab == .mujarrad && amrRadicals s v == 1 then amr s bab v ++ [litC 'ه' .sukun]
  else pauseT (amr s bab v)

/-! ## ٥. الاستنفادُ على كلّ جذر -/

def harakat3 : List Haraka := [.fatha, .kasra, .damma]
def prefixes : List Char := ['ء', 'ن', 'ي', 'ت']
def moods : List Haraka := [.damma, .fatha, .sukun]
def babs : List Bab := [.mujarrad, .afala]

def okBoth (tc tp : List (CSym 3)) (r : Root 3) : Bool :=
  contCheck (fillC tc r) && noVC (kindOf (fillC tc r)) &&
  pauseCheck (fillC tp r) && noVCP (kindOf (fillC tp r)) && litsOK tc && litsOK tp

theorem madi_check :
    allSifa.all (fun s => harakat3.all fun a =>
      okBoth (madi s a .fatha) (pauseT (madi s a .fatha)) (rep s)) = true := by
  decide +kernel

/-- فحصُ المضارع لبابٍ وإعرابٍ على الصفات كلِّها وحركاتِ العين وحروفِ المضارعة (يُقسَم ستًّا لذاكرة النواة). -/
def mudariOK (b : Bab) (m : Haraka) : Bool :=
  allSifa.all fun s => harakat3.all fun v => prefixes.all fun p =>
    okBoth (mudari s b p v m) (pauseT (mudari s b p v m)) (rep s)

theorem mudari_I_raf : mudariOK .mujarrad .damma = true := by decide +kernel
theorem mudari_I_nasb : mudariOK .mujarrad .fatha = true := by decide +kernel
theorem mudari_I_jazm : mudariOK .mujarrad .sukun = true := by decide +kernel
theorem mudari_IV_raf : mudariOK .afala .damma = true := by decide +kernel
theorem mudari_IV_nasb : mudariOK .afala .fatha = true := by decide +kernel
theorem mudari_IV_jazm : mudariOK .afala .sukun = true := by decide +kernel

theorem mudari_check (b : Bab) (hb : b ∈ babs) (m : Haraka) (hm : m ∈ moods) : mudariOK b m = true := by
  simp only [babs, moods, List.mem_cons, List.not_mem_nil, or_false] at hb hm
  rcases hb with rfl | rfl <;> rcases hm with rfl | rfl | rfl
  · exact mudari_I_raf
  · exact mudari_I_nasb
  · exact mudari_I_jazm
  · exact mudari_IV_raf
  · exact mudari_IV_nasb
  · exact mudari_IV_jazm

theorem amr_check :
    allSifa.all (fun s => babs.all fun b => harakat3.all fun v =>
      okBoth (amr s b v) (amrPause s b v) (rep s)) = true := by
  decide +kernel

theorem fill_pause (t : List (CSym 3)) (r : Root 3) : fillC (pauseT t) r = Pause.pause (fillC t r) := by
  unfold pauseT
  rcases List.eq_nil_or_concat t with h | ⟨l, x, h⟩
  · subst h; rfl
  · subst h
    simp only [List.concat_eq_append]
    rw [List.getLast?_concat, List.dropLast_concat]
    cases x <;> simp [fillC, eval, Pause.pause_snoc]

/-- جامعُ الاستنفاد: ما قُرِّر على الصفات يصحّ لكلّ جذرٍ بلا ألف. -/
theorem lift (T : Sifa → List (CSym 3)) (TP : Sifa → List (CSym 3))
    (h : allSifa.all (fun s => okBoth (T s) (TP s) (rep s)) = true) (r : Root 3) (hr : NoAlif r) :
    strictB (fillC (T (sifa r)) r) = true ∧ strictPauseB (fillC (TP (sifa r)) r) = true ∧
      (fillC (T (sifa r)) r).all (Alif.licensable.contains ·) = true := by
  rw [List.all_eq_true] at h
  have h1 := h (sifa r) (mem_allSifa _)
  simp only [okBoth, Bool.and_eq_true] at h1
  obtain ⟨⟨⟨⟨⟨hc, hv⟩, hpc⟩, hpv⟩, hl⟩, _⟩ := h1
  have ha := rep_agree r
  exact ⟨transfer_strict _ hr (rep_noAlif _) ha hc hv, transfer_pause _ hr (rep_noAlif _) ha hpc hpv,
    lits_licensable _ hr hl⟩

/-- **الماضي المجرّد مستنفَدًا**: فَعَلَ وفَعِلَ وفَعُلَ على كلّ جذرٍ بلا ألف — صحيحِه ومعتلِّه ومهموزِه
ومضعَّفِه ولفيفِه — مرخَّصٌ ابتداءً وصلًا ووقفًا، وخاناتُه من المرخَّص. -/
theorem madi_exhausted (r : Root 3) (hr : NoAlif r) : ∀ a ∈ harakat3,
    strictB (fillC (madi (sifa r) a .fatha) r) = true ∧
    strictPauseB (Pause.pause (fillC (madi (sifa r) a .fatha) r)) = true ∧
    (fillC (madi (sifa r) a .fatha) r).all (Alif.licensable.contains ·) = true := by
  intro a ha
  have h := madi_check
  rw [List.all_eq_true] at h
  have := lift (fun s => madi s a .fatha) (fun s => pauseT (madi s a .fatha))
    (List.all_eq_true.2 fun s hs => List.all_eq_true.1 (h s hs) a ha) r hr
  rw [← fill_pause]; exact this

theorem mudari_exhausted (r : Root 3) (hr : NoAlif r) :
    ∀ b ∈ babs, ∀ v ∈ harakat3, ∀ p ∈ prefixes, ∀ m ∈ moods,
      strictB (fillC (mudari (sifa r) b p v m) r) = true ∧
      strictPauseB (Pause.pause (fillC (mudari (sifa r) b p v m) r)) = true ∧
      (fillC (mudari (sifa r) b p v m) r).all (Alif.licensable.contains ·) = true := by
  intro b hb v hv p hp m hm
  have h := mudari_check b hb m hm
  unfold mudariOK at h
  rw [List.all_eq_true] at h
  have := lift (fun s => mudari s b p v m) (fun s => pauseT (mudari s b p v m))
    (List.all_eq_true.2 fun s hs => by
      have := List.all_eq_true.1 (h s hs) v hv
      exact List.all_eq_true.1 this p hp) r hr
  rw [← fill_pause]; exact this

theorem amr_exhausted (r : Root 3) (hr : NoAlif r) :
    ∀ b ∈ babs, ∀ v ∈ harakat3,
      strictB (fillC (amr (sifa r) b v) r) = true ∧
      strictPauseB (fillC (amrPause (sifa r) b v) r) = true ∧
      (fillC (amr (sifa r) b v) r).all (Alif.licensable.contains ·) = true := by
  intro b hb v hv
  have h := amr_check
  rw [List.all_eq_true] at h
  exact lift (fun s => amr s b v) (fun s => amrPause s b v)
    (List.all_eq_true.2 fun s hs => by
      have := List.all_eq_true.1 (h s hs) b hb
      exact List.all_eq_true.1 this v hv) r hr

/-- جذورُ جدول الدرجة الثلاثيّة (`RootGrade.table 3`، ‎28³‎ جذرًا) بلا ألف كلُّها، فالاستنفادُ عليها جميعًا. -/
def ofTable (l : List (Fin 28)) : Root 3 := fun i => RootGrade.toCarrier (l.getD i.val 0)

theorem ofTable_noAlif (l : List (Fin 28)) : NoAlif (ofTable l) :=
  fun _ => RootGrade.toCarrier_ne_alif _

theorem madi_exhausted_table : ∀ l ∈ RootGrade.table 3, ∀ a ∈ harakat3,
    strictB (fillC (madi (sifa (ofTable l)) a .fatha) (ofTable l)) = true ∧
    strictPauseB (Pause.pause (fillC (madi (sifa (ofTable l)) a .fatha) (ofTable l))) = true ∧
    (fillC (madi (sifa (ofTable l)) a .fatha) (ofTable l)).all (Alif.licensable.contains ·) = true :=
  fun l _ => madi_exhausted (ofTable l) (ofTable_noAlif l)

/-! ## ٦. ما يُلزمه القانون -/

def endsVC : List K → Bool
  | [.v, .c] => true
  | _ :: t => endsVC t
  | [] => false

theorem geminateB_false_of_endsVC : ∀ (p : List (K × Cell)), endsVC (p.map Prod.fst) = true →
    geminateB p = false
  | [], h => by simp [endsVC] at h
  | [a], h => by cases a with | mk k x => cases k <;> simp [endsVC] at h
  | [a, b], h => by
    obtain ⟨ka, x⟩ := a
    obtain ⟨kb, y⟩ := b
    cases ka <;> cases kb <;> simp_all [endsVC, geminateB, stepOK]
  | a :: b :: c :: t, h => by
    have ih := geminateB_false_of_endsVC (b :: c :: t)
    have h' : endsVC ((b :: c :: t).map Prod.fst) = true := by
      obtain ⟨ka, x⟩ := a; cases ka <;> simpa [endsVC] using h
    show (stepOK a (b :: c :: t) && geminateB (b :: c :: t)) = false
    rw [ih h', Bool.and_false]

/-- الكلمةُ لا تبدأ بهمزةٍ مفتوحةٍ يتلوها ألف. -/
def notFarqT : List (CSym 3) → Bool
  | _ :: .lit c :: _ => c != Neutral.alifS
  | _ :: .slot _ _ :: _ => true
  | _ => true

theorem isFarq_false (t : List (CSym 3)) (r : Root 3) (hr : NoAlif r) (h : notFarqT t = true) :
    isFarq (fillC t r) = false := by
  match t, h with
  | [], _ => rfl
  | [_], _ => rfl
  | [_, _], _ => rfl
  | x :: .lit c :: y :: rest, h =>
    simp only [notFarqT, bne_iff_ne, ne_eq] at h
    have hc : (c == atom 'ا' .sukun) = false := by
      simpa [Neutral.alifS] using h
    simp only [fillC, List.map_cons, isFarq, eval, hc, Bool.and_false, Bool.false_and]
  | x :: .slot i hh :: y :: rest, _ =>
    have hc : ((⟨r i, hh⟩ : Cell) == atom 'ا' .sukun) = false := by
      cases e : ((⟨r i, hh⟩ : Cell) == atom 'ا' .sukun)
      · rfl
      · exact absurd (congrArg Cell.carrier (beq_iff_eq.1 e)) (hr i)
    simp only [fillC, List.map_cons, isFarq, eval, hc, Bool.and_false, Bool.false_and]

def ajwafSifas : List Sifa := allSifa.filter fun s => s.c1.weak && !s.c2.weak && cons s.c0

theorem madd_drop_check :
    ajwafSifas.all (fun s => babs.all fun b => harakat3.all fun v => prefixes.all fun p =>
      endsVC (kindOf (fillC (jussivePre s b p v) (rep s))) && notFarqT (jussivePre s b p v)) = true := by
  decide +kernel

/-- **حذفُ المدّ ملزَم**: مجزومُ الأجوف قبل الحذف (تَقُومْ، أَقُومْ، يُقِيمْ…) غيرُ مرخَّصٍ وصلًا لكلّ جذرٍ أجوف
— قافيةُ مدٍّ غيرُ مدغمة (`CVVC_NOT_GEMINATE`). -/
theorem madd_drop_forced (r : Root 3) (hr : NoAlif r) (hs : (sifa r) ∈ ajwafSifas) :
    ∀ b ∈ babs, ∀ v ∈ harakat3, ∀ p ∈ prefixes,
      strictB (fillC (jussivePre (sifa r) b p v) r) = false := by
  intro b hb v hv p hp
  have h := madd_drop_check
  rw [List.all_eq_true] at h
  have h1 := List.all_eq_true.1 (List.all_eq_true.1 (List.all_eq_true.1 (h _ hs) b hb) v hv) p hp
  simp only [Bool.and_eq_true] at h1
  have hk := kindOf_agree (jussivePre (sifa r) b p v) hr (rep_noAlif _) (rep_agree r)
  have hf := isFarq_false _ r hr h1.2
  have hl : (kindOf (fillC (jussivePre (sifa r) b p v) r)).length =
      (fillC (jussivePre (sifa r) b p v) r).length := kindGo_length _ _
  unfold strictB haddB
  rw [hf]
  simp only [Bool.false_eq_true, ite_false, Bool.and_eq_false_iff]
  right
  apply geminateB_false_of_endsVC
  rw [map_fst_zip _ _ hl, hk]
  exact h1.1

/-- **الكلمةُ حرفًا واحدًا لا يوقَف عليها، وبهاء السكت يوقَف**: لكلّ خانةٍ متحرّكةٍ مرخَّصة. -/
theorem haa_forced : ∀ c ∈ Alif.licensable, c.haraka ≠ .sukun →
    strictPauseB (Pause.pause [c]) = false ∧ strictPauseB [c, atom 'ه' .sukun] = true := by
  decide +kernel

/-! ## ٧. الشواهد -/

def r3 (a b c : Char) : Root 3 := Neutral.rootOf a b c

def form (t : Sifa → List (CSym 3)) (a b c : Char) : List Cell :=
  fillC (t (sifa (r3 a b c))) (r3 a b c)

/-- قَامَ يَقُومُ قُمْ (ق و م: فَعَلَ يَفْعُلُ)، والمحذوفُ قبل الحدّ: قُومْ مرفوضة. -/
theorem qama :
    form (madi · .fatha .fatha) 'ق' 'و' 'م' = [atom 'ق' .fatha, Neutral.alifS, atom 'م' .fatha] ∧
    form (mudari · .mujarrad 'ي' .damma .damma) 'ق' 'و' 'م' =
      [atom 'ي' .fatha, atom 'ق' .damma, atom 'و' .sukun, atom 'م' .damma] ∧
    form (amr · .mujarrad .damma) 'ق' 'و' 'م' = [atom 'ق' .damma, atom 'م' .sukun] ∧
    strictB [atom 'ق' .damma, atom 'و' .sukun, atom 'م' .sukun] = false := by
  decide +kernel

/-- نَامَ يَنَامُ نَمْ (ن و م: فَعِلَ يَفْعَلُ). -/
theorem nama_yanamu :
    form (madi · .kasra .fatha) 'ن' 'و' 'م' = [atom 'ن' .fatha, Neutral.alifS, atom 'م' .fatha] ∧
    form (mudari · .mujarrad 'ي' .fatha .damma) 'ن' 'و' 'م' =
      [atom 'ي' .fatha, atom 'ن' .fatha, Neutral.alifS, atom 'م' .damma] ∧
    form (amr · .mujarrad .fatha) 'ن' 'و' 'م' = [atom 'ن' .fatha, atom 'م' .sukun] := by
  decide +kernel

/-- وَقَى يَقِي قِ قِهْ، ووَعَى يَعِي عِ عِهْ (اللفيفُ المفروق: فَعَلَ يَفْعِلُ). -/
theorem waqa_waa :
    form (madi · .fatha .fatha) 'و' 'ق' 'ي' = [atom 'و' .fatha, atom 'ق' .fatha, Neutral.alifS] ∧
    form (mudari · .mujarrad 'ي' .kasra .damma) 'و' 'ق' 'ي' =
      [atom 'ي' .fatha, atom 'ق' .kasra, atom 'ي' .sukun] ∧
    form (amr · .mujarrad .kasra) 'و' 'ق' 'ي' = [atom 'ق' .kasra] ∧
    form (amrPause · .mujarrad .kasra) 'و' 'ق' 'ي' = [atom 'ق' .kasra, atom 'ه' .sukun] ∧
    form (mudari · .mujarrad 'ي' .kasra .damma) 'و' 'ع' 'ي' =
      [atom 'ي' .fatha, atom 'ع' .kasra, atom 'ي' .sukun] ∧
    form (amr · .mujarrad .kasra) 'و' 'ع' 'ي' = [atom 'ع' .kasra] ∧
    form (amrPause · .mujarrad .kasra) 'و' 'ع' 'ي' = [atom 'ع' .kasra, atom 'ه' .sukun] := by
  decide +kernel

/-- نَمَا يَنْمُو تَنْمُو نَنْمُو أَنْمُو اُنْمُ (ن م و: فَعَلَ يَفْعُلُ؛ الأمرُ بحذف اللام وهمزةِ وصلٍ مضمومة). -/
theorem nama_yanmu :
    form (madi · .fatha .fatha) 'ن' 'م' 'و' = [atom 'ن' .fatha, atom 'م' .fatha, Neutral.alifS] ∧
    ['ي', 'ت', 'ن', 'ء'].map (fun p => form (mudari · .mujarrad p .damma .damma) 'ن' 'م' 'و') =
      ['ي', 'ت', 'ن', 'ء'].map (fun p =>
        [atom p .fatha, atom 'ن' .sukun, atom 'م' .damma, atom 'و' .sukun]) ∧
    form (amr · .mujarrad .damma) 'ن' 'م' 'و' = [atom 'ء' .damma, atom 'ن' .sukun, atom 'م' .damma] := by
  decide +kernel

/-- أَخَذَ يَأْخُذُ آخُذُ، والأمرُ التامُّ أُوخُذْ (أُوكُلْ، الكتاب 18369) والمستعملُ خُذْ (18368). -/
theorem akhadha :
    form (madi · .fatha .fatha) 'ء' 'خ' 'ذ' = [atom 'ء' .fatha, atom 'خ' .fatha, atom 'ذ' .fatha] ∧
    form (mudari · .mujarrad 'ي' .damma .damma) 'ء' 'خ' 'ذ' =
      [atom 'ي' .fatha, atom 'ء' .sukun, atom 'خ' .damma, atom 'ذ' .damma] ∧
    form (mudari · .mujarrad 'ء' .damma .damma) 'ء' 'خ' 'ذ' =
      [atom 'ء' .fatha, Neutral.alifS, atom 'خ' .damma, atom 'ذ' .damma] ∧
    form (amr · .mujarrad .damma) 'ء' 'خ' 'ذ' =
      [atom 'ء' .damma, atom 'و' .sukun, atom 'خ' .damma, atom 'ذ' .sukun] ∧
    form (amrKhudh · .damma) 'ء' 'خ' 'ذ' = [atom 'خ' .damma, atom 'ذ' .sukun] ∧
    strictB (form (amrKhudh · .damma) 'ء' 'خ' 'ذ') = true := by
  decide +kernel

/-- أَعْطَى يُعْطِي تُعْطِي نُعْطِي أُعْطِي أَعْطِ (ع ط و على أَفْعَلَ). -/
theorem atha :
    ['ي', 'ت', 'ن', 'ء'].map (fun p => form (mudari · .afala p .kasra .damma) 'ع' 'ط' 'و') =
      ['ي', 'ت', 'ن', 'ء'].map (fun p =>
        [atom p .damma, atom 'ع' .sukun, atom 'ط' .kasra, atom 'ي' .sukun]) ∧
    form (amr · .afala .kasra) 'ع' 'ط' 'و' = [atom 'ء' .fatha, atom 'ع' .sukun, atom 'ط' .kasra] := by
  decide +kernel

/-- مَدَّ يَمُدُّ لَمْ يَمْدُدْ اُمْدُدْ (المضعَّف: الإدغامُ مع المتحرّك، والفكُّ مع الساكن). -/
theorem madda :
    form (madi · .fatha .fatha) 'م' 'د' 'د' = [atom 'م' .fatha, atom 'د' .sukun, atom 'د' .fatha] ∧
    form (mudari · .mujarrad 'ي' .damma .damma) 'م' 'د' 'د' =
      [atom 'ي' .fatha, atom 'م' .damma, atom 'د' .sukun, atom 'د' .damma] ∧
    form (mudari · .mujarrad 'ي' .damma .sukun) 'م' 'د' 'د' =
      [atom 'ي' .fatha, atom 'م' .sukun, atom 'د' .damma, atom 'د' .sukun] ∧
    form (amr · .mujarrad .damma) 'م' 'د' 'د' =
      [atom 'ء' .damma, atom 'م' .sukun, atom 'د' .damma, atom 'د' .sukun] := by
  decide +kernel

/-- لا تَقِ: أصلٌ واحدٌ في خانتين؛ وقفُها بلا هاءٍ مرخَّصٌ بالمقطع — فلزومُ الهاء فيها (الكتاب 17697) بعدد الأصول. -/
theorem taqi_not_syllable_forced :
    form (mudari · .mujarrad 'ت' .kasra .sukun) 'و' 'ق' 'ي' = [atom 'ت' .fatha, atom 'ق' .kasra] ∧
    strictPauseB (Pause.pause [atom 'ت' .fatha, atom 'ق' .kasra]) = true ∧
    amrRadicals (sifa (r3 'و' 'ق' 'ي')) .kasra = 1 := by
  decide +kernel

/-- اتّساقٌ مع الأوزان المودَعة: على الجذر الصحيح الماضي المجرّد بأبوابه هو `Wazn.realize` للقوالب الثلاثة الأولى. -/
theorem madi_agrees_with_wazn :
    (List.range 3).all (fun i => match thulathi[i]?, harakat3[i]? with
      | some W, some a => fillC (madi (sifa ktb) a .fatha) ktb == realize W ktb .start .continue .fatha
      | _, _ => false) = true := by
  decide +kernel

/-! ## ٨. الاتّساقُ مع `Mudari` (ADR ٢٤) -/

/-- الصيغةُ نفسُها من الوحدتين: باب `Mudari.Form` المجرّدُ وأَفْعَلَ. -/
def babOf (f : Mudari.Form) : Bab := if f == .IV then .afala else .mujarrad

/-- جذورُ `Mudari.refRoots` إلّا المهموزَ الفاء (ءمن) والعين (رءي): فيهما فرقٌ مسمًّى (ADR ٢٦). -/
def sharedRoots : List (Root 3) := Mudari.refRoots.filter fun r => cls (r 0) != .hamz && cls (r 1) != .hamz

/-- **الوحدتان متّفقتان**: على الجذور المرجعيّة المشتركة، المجرّدِ وأَفْعَلَ، كلِّ بابٍ وحرفِ مضارعةٍ ورفعٍ وجزم،
المضارعُ والأمرُ خانةً خانة. -/
theorem agrees_with_mudari :
    sharedRoots.all (fun r => [Mudari.Form.I, .IV].all fun f => (Mudari.babs r f).all fun b =>
      (Mudari.anayt.all fun p => [Haraka.damma, .sukun].all fun e =>
        fillC (mudari (sifa r) (babOf f) p b e) r == Mudari.mudari r f b p e) &&
      fillC (amr (sifa r) (babOf f) b) r == Mudari.amr r f b) = true := by
  decide +kernel

/-- **الفرقُ المسمّى** في المهموز: المتكلّمُ من أمن آمَنُ هنا (القاعدة ٧؛ «هَلْ آمَنُكُمْ»)، وأَأْمَنُ في `Mudari`؛ والأمرُ
اِيمَنْ هنا (أُوكُلْ، الكتاب 18369) واِءْمَنْ هناك؛ وأَفْعَلَ آمِنْ في الوحدتين. -/
theorem hamza_fork :
    fillC (mudari (sifa (r3 'ء' 'م' 'ن')) .mujarrad 'ء' .fatha .damma) (r3 'ء' 'م' 'ن') =
      [atom 'ء' .fatha, Neutral.alifS, atom 'م' .fatha, atom 'ن' .damma] ∧
    Mudari.mudari (r3 'ء' 'م' 'ن') .I .fatha 'ء' .damma =
      [atom 'ء' .fatha, atom 'ء' .sukun, atom 'م' .fatha, atom 'ن' .damma] ∧
    fillC (amr (sifa (r3 'ء' 'م' 'ن')) .afala .kasra) (r3 'ء' 'م' 'ن') = Mudari.amr (r3 'ء' 'م' 'ن') .IV .kasra := by
  decide +kernel

end A116.Tasrif
