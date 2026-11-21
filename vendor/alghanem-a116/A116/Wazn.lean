import A116.Exhaust
import A116.Ishtiqaq
import A116.Boundary

/-!
# الأوزانُ على الخانات بعدد الأصول، ومقاطعُها بقانون الحدّ، والدالّةُ من آرتين

قرارُ المالك (2026-10-12): «بعدد الأصول أوّلًا، وتنتظر بقانون الابتداء وقانون الوصل وقانون الوقف؛ اضبط
المقاطع داخل الأوزان؛ أوجد الدالّة من آرتين».

## الدرجة بعدد الأصول

`Root n`: لكلّ أصلٍ من n حاملٌ من الـ29 — ثلاثيٌّ n = 3، رباعيٌّ n = 4. والوزنُ (`WaznC n`) خاناتٌ زائدةٌ وأصولٌ
بحالاتها، وطرفاه **ينتظران قانونَ الحدّ**:
* **الابتداء**: همزةُ الوصل (إن كانت) تثبت ابتداءً بحركتها من الثاني والثالث (`Boundary.waslVowel`) وتسقط وصلًا
  (`Boundary.dropWasl`)، فالموصولُ يبدأ بساكنٍ ولا يُرخَّص إلّا بجاره الأيسر (`Boundary.wasl_dropped_needs_moving_left`).
* **الوقف/الوصل**: حالةُ الأصل الأخير حالتُه الصرفيّة (حركةُ الضمير) وصلًا، وسكونٌ وقفًا.

## الدالّةُ من آرتين: التقييم

في آرتين المتغيّرُ ‎x_f‎ يُرسَل إلى جذرٍ ‎r_f‎ بالتقييم ‎aeval r‎، وهو تشاكلٌ يحفظ البنية، والقيدُ يُفحص على صورته.
وهنا: **الأصلُ متغيّرٌ في الوزن، والجذرُ تقييمٌ له** — `eval r : CSym n → Cell` يرسل الأصلَ i بحالته h إلى الخانة
‎(r i، h)‎ ويُبقي الزائد. فالصيغةُ = ‎fillC t r‎ = صورةُ الوزن بالتقييم، وهي:
* **تشاكل** على الوصل (`fillC_append`).
* **تحفظ الجذر** (`fillC_determines_root`، `realize_determines_root`): كلُّ أصلٍ يقع في الوزن يُستردّ من الصورة.
* **مقاطعُها دالّةٌ في الوزن وحدَه** (`kindOf_realize_invariant`): جذران متّفقان في «ملمح المدّ» (أيُّ أصلٍ حرفُ مدٍّ
  وبأيّ حركة) وفي موضع اللام، صورتاهما بإسقاطٍ واحد على `cv | v | c` في كلّ سياق — فالمقاطعُ **داخل الوزن** لا في
  الجذر. ولكلّ جذرين صحيحين (`Sound`) ذلك بلا شرط (`syllables_fixed_by_wazn`).

## ما يُبرهَن على الأوزان المودَعة

* `convert_all`: قوالبُ `SOUND_TEMPLATES` الإحدى والثلاثون تُترجَم أوزانًا على الخانات (الشدّةُ مثلان: ساكنٌ ثمّ
  متحرّك؛ حرفُ المدّ بلا علامة ساكن؛ الأصلُ الأخيرُ بلا علامة ينتظر الحدّ؛ والألفُ الأولى همزةُ وصل).
* `thulathi_licensed`: كلُّ وزنٍ منها مرخَّصٌ بقيد الحدّ ابتداءً مع الوصل (بحركة 3MS/2MS) ومع الوقف، على جذرٍ صحيح.
* `wasl_joined_waits`: الموصولُ من أوزان همزة الوصل يبدأ بساكن — ترخيصُه ينتظر جارَه.
* `root_degree_is_not_syllable_degree`: دَحْرَجَ (أربعةُ أصول) وكَتَبَ (ثلاثة) ثلاثةُ مقاطع كلاهما، واسْتَخْرَجَ
  (ثلاثة) أربعة — فالدرجةُ بالأصول غيرُ الدرجة بالمقاطع في الاتّجاهين.
* `wasl_lam_conflict`: قاعدةُ `waslVowel` «فتحةٌ قبل اللام» وُضعت للأداة، فتأخذ لامَ الأصل في افتعل (الْتَقَى) فتفتح
  الهمزة، وقاعدةُ الفعل (`waslVowelVerb`) تكسرها — دَينٌ مسمًّى `WASL_LAM_ARTICLE_VS_ROOT` لا يُصلَح هنا.

ولا يُبرهَن هنا أنّ هذه الأوزانَ أوزانُ العربيّة: Lean يُبرهن خواصَّ التعريف على القوالب المودَعة.
-/

set_option autoImplicit false

namespace A116.Wazn

open A116 A116.Stages A116.Ternary A116.Ladder A116.Hadd A116.Boundary A116.Exhaust

/-! ## ١. الوزنُ والجذرُ والتقييم -/

/-- رمزُ الوزن: خانةٌ زائدة، أو أصلٌ i بحالته. -/
inductive CSym (n : Nat) where
  | lit : Cell → CSym n
  | slot : Fin n → Haraka → CSym n
  deriving DecidableEq, Repr

/-- الجذر: لكلّ أصلٍ من n حامل. -/
abbrev Root (n : Nat) := Fin n → Fin carrierCount

/-- **دالّةُ آرتين**: التقييم — الأصلُ إلى حامله بحالته، والزائدُ ثابت. -/
def eval {n : Nat} (r : Root n) : CSym n → Cell
  | .lit c => c
  | .slot i h => ⟨r i, h⟩

def fillC {n : Nat} (t : List (CSym n)) (r : Root n) : List Cell := t.map (eval r)

theorem fillC_append {n : Nat} (a b : List (CSym n)) (r : Root n) :
    fillC (a ++ b) r = fillC a r ++ fillC b r := by simp [fillC]

/-- الوزن: همزةُ وصلٍ أو لا، وجسمٌ، وأصلٌ أخيرٌ حالتُه تنتظر الحدّ. -/
structure WaznC (n : Nat) where
  wasl : Bool
  body : List (CSym n)
  last : Fin n
  deriving DecidableEq, Repr

/-- حركةُ همزة الوصل ابتداءً من أوّل رمزين في الجسم (قاعدةُ المستودع `Boundary.waslVowel`). -/
def waslH {n : Nat} (W : WaznC n) (r : Root n) : Haraka :=
  match W.body with
  | s1 :: s2 :: _ => waslVowel (eval r s1) (eval r s2)
  | _ => .kasra

/-- **الوزنُ في سياقه**: `entry` (ابتداء/وصل) و`exit` (استمرار/وقف) و`h` حالةُ الأصل الأخير الصرفيّة. -/
def realize {n : Nat} (W : WaznC n) (r : Root n) (entry : Entry) (exit : Exit) (h : Haraka) :
    List Cell :=
  (if W.wasl && entry == .start then [⟨hamza, waslH W r⟩] else []) ++
    fillC W.body r ++ [⟨r W.last, if exit == .pause then .sukun else h⟩]

/-! ## ٢. التقييمُ يحفظ الجذر -/

theorem fillC_determines_root {n : Nat} :
    ∀ (t : List (CSym n)) (r r' : Root n), fillC t r = fillC t r' →
      ∀ i h, CSym.slot i h ∈ t → r i = r' i
  | [], _, _, _, _, _, hm => by simp at hm
  | s :: t, r, r', e, i, h, hm => by
    simp only [fillC, List.map_cons, List.cons.injEq] at e
    rcases List.mem_cons.1 hm with rfl | hm
    · have := congrArg Cell.carrier e.1; simpa [eval] using this
    · exact fillC_determines_root t r r' e.2 i h hm

theorem realize_determines_root {n : Nat} (W : WaznC n) (r r' : Root n) (en : Entry) (ex : Exit)
    (h : Haraka) (e : realize W r en ex h = realize W r' en ex h) (hw : waslH W r = waslH W r') :
    r W.last = r' W.last ∧ ∀ i h', CSym.slot i h' ∈ W.body → r i = r' i := by
  simp only [realize, hw, List.append_assoc] at e
  have e2 := List.append_cancel_left e
  have hl : (fillC W.body r).length = (fillC W.body r').length := by simp [fillC]
  obtain ⟨e3, e4⟩ := List.append_inj e2 hl
  simp only [List.cons.injEq, and_true] at e4
  exact ⟨congrArg Cell.carrier e4, fillC_determines_root W.body r r' e3⟩

/-! ## ٣. المقاطعُ دالّةٌ في الوزن: الإسقاطُ لا يرى من الخانة إلّا حالتَها وملمحَ مدّها -/

/-- ملمحُ الخانة: حالتُها، وحركةُ المدّ التي يكون حاملُها حرفَ مدٍّ معها. -/
def prof (c : Cell) : Haraka × Option Haraka := (c.haraka, maddVowel c.carrier)

theorem kindOne_prof {p : Option Haraka} {x y : Cell} (e : prof x = prof y) :
    kindOne p x = kindOne p y := by
  simp only [prof, Prod.mk.injEq] at e
  simp only [kindOne, e.1, e.2]

theorem kindGo_prof : ∀ (p : Option Haraka) (w w' : List Cell), w.map prof = w'.map prof →
    kindGo p w = kindGo p w'
  | _, [], [], _ => rfl
  | _, [], _ :: _, e => by simp at e
  | _, _ :: _, [], e => by simp at e
  | p, x :: t, y :: t', e => by
    simp only [List.map_cons, List.cons.injEq] at e
    have hh : x.haraka = y.haraka := congrArg Prod.fst e.1
    simp only [kindGo, kindOne_prof e.1, hh, kindGo_prof _ t t' e.2]

/-- جذران متّفقان في ملمح المدّ لكلّ أصل. -/
def MaddEq {n : Nat} (r r' : Root n) : Prop := ∀ i, maddVowel (r i) = maddVowel (r' i)

/-- جذران متّفقان في موضع اللام (لأنّ قاعدةَ همزة الوصل تقرأ اللام). -/
def LamEq {n : Nat} (r r' : Root n) : Prop := ∀ i, (r i = carrierOf 'ل') ↔ (r' i = carrierOf 'ل')

theorem prof_eval {n : Nat} {r r' : Root n} (hm : MaddEq r r') (s : CSym n) :
    prof (eval r s) = prof (eval r' s) := by
  cases s with
  | lit c => rfl
  | slot i h => simp [prof, eval, hm i]

theorem waslH_eq {n : Nat} (W : WaznC n) {r r' : Root n} (hl : LamEq r r') :
    waslH W r = waslH W r' := by
  unfold waslH
  match W.body with
  | s1 :: s2 :: _ =>
    simp only
    cases s1 with
    | lit c => cases s2 <;> rfl
    | slot i h =>
      simp only [waslVowel, eval]
      by_cases e : r i = carrierOf 'ل'
      · have e' := (hl i).1 e; simp [e, e']
      · have e' : ¬ r' i = carrierOf 'ل' := fun h' => e ((hl i).2 h')
        simp only [e, e', ite_false]
        cases s2 <;> rfl
  | [] => rfl
  | [_] => rfl

/-- **المقاطعُ داخل الوزن**: جذران متّفقان في ملمح المدّ وموضع اللام، صورتاهما بإسقاطٍ واحد في كلّ سياق. -/
theorem kindOf_realize_invariant {n : Nat} (W : WaznC n) {r r' : Root n} (hm : MaddEq r r')
    (hl : LamEq r r') (en : Entry) (ex : Exit) (h : Haraka) :
    kindOf (realize W r en ex h) = kindOf (realize W r' en ex h) := by
  apply kindGo_prof
  simp only [realize, waslH_eq W hl, List.map_append, fillC, List.map_map]
  have h1 : List.map (prof ∘ eval r) W.body = List.map (prof ∘ eval r') W.body :=
    List.map_congr_left (fun s _ => prof_eval hm s)
  rw [h1]
  simp [prof, hm W.last]

/-- الجذرُ الصحيح: لا أصلَ فيه حرفُ مدّ ولا لام. -/
def Sound {n : Nat} (r : Root n) : Prop := ∀ i, maddVowel (r i) = none ∧ r i ≠ carrierOf 'ل'

theorem syllables_fixed_by_wazn {n : Nat} (W : WaznC n) {r r' : Root n} (hr : Sound r) (hr' : Sound r')
    (en : Entry) (ex : Exit) (h : Haraka) :
    kindOf (realize W r en ex h) = kindOf (realize W r' en ex h) :=
  kindOf_realize_invariant W (fun i => by rw [(hr i).1, (hr' i).1])
    (fun i => ⟨fun e => absurd e (hr i).2, fun e => absurd e (hr' i).2⟩) en ex h

/-! ## ٤. تقطيعٌ قابلٌ للحساب في النواة، صادقٌ لـ`Stages.parse` -/

/-- التقطيعُ بوقود: يبدأ بمتحرّكٍ ويأخذ ذيلَه حتى المتحرّك التالي. -/
def sylF : Nat → List Stages.K → Option (List Syl)
  | _, [] => some []
  | 0, _ :: _ => none
  | f + 1, .cv :: t =>
    let coda := t.takeWhile (· != .cv)
    let rest := t.dropWhile (· != .cv)
    match sylOf coda, sylF f rest with
    | some s, some ss => some (s :: ss)
    | _, _ => none
  | _ + 1, _ :: _ => none

/-- **الصدق**: ما يقطّعه `sylF` يُعيده الوصلُ بعينه، فهو تقطيعُ `parse` الوحيد. -/
theorem sylF_sound : ∀ (f : Nat) (k : List Stages.K) (ss : List Syl),
    sylF f k = some ss → flat .none ss = k
  | _, [], ss, h => by simp [sylF] at h; subst h; rfl
  | 0, _ :: _, _, h => by simp [sylF] at h
  | f + 1, .cv :: t, ss, h => by
    simp only [sylF] at h
    split at h
    · rename_i s ss' hs hss
      simp only [Option.some.injEq] at h
      subst h
      have ih := sylF_sound f _ ss' hss
      have hc := coda_of_sylOf hs
      simp only [flat, Lead.atoms, List.nil_append] at ih ⊢
      simp only [List.flatMap_cons, Syl.atoms, hc, ih, List.cons_append, List.takeWhile_append_dropWhile]
    · simp at h
  | _ + 1, .v :: _, _, h => by simp [sylF] at h
  | _ + 1, .c :: _, _, h => by simp [sylF] at h

theorem parse_of_sylF {f : Nat} {k : List Stages.K} {ss : List Syl} (h : sylF f k = some ss) :
    parse k = some (.none, ss) := by
  rw [← sylF_sound f k ss h]; exact parse_flat _ _

/-- المقاطعُ في سياق، بالحساب. -/
def syllables (w : List Cell) : Option (List Syl) := sylF w.length (kindOf w)

/-- الترخيصُ وصلًا بالحساب (يطابق `strictB` حيث يقطّع `sylF`: `strictB_of_check`). -/
def contCheck (w : List Cell) : Bool :=
  match syllables w with
  | some ss => ss.all (fun s => !pauseOnly s) && haddB w
  | none => false

def pauseCheck (w : List Cell) : Bool :=
  match syllables w with
  | some ss => ss.dropLast.all (fun s => !pauseOnly s) && haddPauseB w
  | none => false

theorem strictB_of_check {w : List Cell} (h : contCheck w = true) : strictB w = true := by
  unfold contCheck at h
  split at h
  · rename_i ss hs
    simp only [Bool.and_eq_true] at h
    have hk := sylF_sound _ _ _ hs
    simp only [strictB, ← hk, continueB_flat, h.1, h.2, Bool.and_self]
  · simp at h

theorem strictPauseB_of_check {w : List Cell} (h : pauseCheck w = true) : strictPauseB w = true := by
  unfold pauseCheck at h
  split at h
  · rename_i ss hs
    simp only [Bool.and_eq_true] at h
    have hk := sylF_sound _ _ _ hs
    simp only [strictPauseB, ← hk, Grade.pauseB_flat, h.1, h.2, Bool.and_self]
  · simp at h

/-! ## ٥. ترجمةُ القوالب المودَعة إلى أوزانٍ على الخانات -/

def markH : Char → Option Haraka
  | 'َ' => some .fatha
  | 'ُ' => some .damma
  | 'ِ' => some .kasra
  | 'ْ' => some .sukun
  | _ => none

def mk : Ishtiqaq.Sym Char → Haraka → CSym 3
  | .lit c, h => .lit (atom c h)
  | .slot i, h => .slot i h

/-- الجسمُ والأصلُ الأخير: الشدّةُ مثلان (ساكنٌ ثمّ متحرّك)، والحرفُ بلا علامة قبل حرفٍ ساكنٌ (حرفُ المدّ)،
والأصلُ الأخيرُ بلا علامة ينتظر الحدّ. -/
def go : List (Ishtiqaq.Sym Char) → Option (List (CSym 3) × Fin 3)
  | [.slot i] => some ([], i)
  | b :: .lit 'ّ' :: .lit m :: rest =>
    match markH m, go rest with
    | some h, some (xs, l) => some (mk b .sukun :: mk b h :: xs, l)
    | _, _ => none
  | b :: .lit m :: rest =>
    match markH m with
    | some h => (go rest).map fun (xs, l) => (mk b h :: xs, l)
    | none => (go (.lit m :: rest)).map fun (xs, l) => (mk b .sukun :: xs, l)
  | b :: .slot i :: rest => (go (.slot i :: rest)).map fun (xs, l) => (mk b .sukun :: xs, l)
  | _ => none

/-- القالبُ ← الوزن: الألفُ الأولى همزةُ وصل. -/
def convert (t : Ishtiqaq.Template Char) : Option (WaznC 3) :=
  match t with
  | .lit 'ا' :: rest => (go rest).map fun (b, l) => ⟨true, b, l⟩
  | _ => (go t).map fun (b, l) => ⟨false, b, l⟩

def thulathi : List (WaznC 3) := Ishtiqaq.soundTemplates.filterMap convert

theorem convert_all : thulathi.length = Ishtiqaq.soundTemplates.length := by decide

/-- حالةُ الأصل الأخير الصرفيّة في القالب: الأمرُ (من الواحد والعشرين فصاعدًا) مبنيٌّ على السكون، وسواه 3MS فتحة. -/
def lastH (i : Nat) : Haraka := if i < 20 then .fatha else .sukun

/-- جذرٌ صحيحٌ مرجعيّ: ك ت ب. -/
def ktb : Root 3
  | ⟨0, _⟩ => carrierOf 'ك'
  | ⟨1, _⟩ => carrierOf 'ت'
  | _ => carrierOf 'ب'

theorem ktb_sound : Sound ktb := by
  unfold Sound; decide

/-- **كلُّ وزنٍ ثلاثيٍّ مرخَّصٌ ابتداءً** وصلًا بحالته الصرفيّة ووقفًا. -/
theorem thulathi_check :
    ((List.range thulathi.length).zip thulathi).all (fun (i, W) =>
      contCheck (realize W ktb .start .continue (lastH i)) &&
      pauseCheck (realize W ktb .start .pause (lastH i)) &&
      (realize W ktb .start .continue (lastH i)).all (Alif.licensable.contains ·)) = true := by
  decide +kernel

theorem thulathi_licensed :
    ∀ p ∈ (List.range thulathi.length).zip thulathi,
      strictB (realize p.2 ktb .start .continue (lastH p.1)) = true ∧
      strictPauseB (realize p.2 ktb .start .pause (lastH p.1)) = true := by
  intro p hp
  have h := thulathi_check
  rw [List.all_eq_true] at h
  have := h p hp
  simp only [Bool.and_eq_true] at this
  exact ⟨strictB_of_check this.1.1, strictPauseB_of_check this.1.2⟩

/-- **الموصولُ ينتظر جارَه**: كلُّ وزنٍ بهمزة وصلٍ يبدأ موصولًا بساكن (`Boundary.initialSukun`). -/
theorem wasl_joined_waits :
    (thulathi.filter (·.wasl)).all (fun W => initialSukun (realize W ktb .joined .continue .fatha))
      = true ∧ (thulathi.filter (·.wasl)).length = 12 := by
  decide +kernel

/-! ## ٦. الرباعيّ والدرجتان -/

def fa'lala : WaznC 4 := ⟨false, [.slot 0 .fatha, .slot 1 .sukun, .slot 2 .fatha], 3⟩

def dhrj : Root 4
  | ⟨0, _⟩ => carrierOf 'د'
  | ⟨1, _⟩ => carrierOf 'ح'
  | ⟨2, _⟩ => carrierOf 'ر'
  | _ => carrierOf 'ج'

/-- **الدرجةُ بالأصول غيرُ الدرجة بالمقاطع**: دَحْرَجَ أربعةُ أصولٍ وثلاثةُ مقاطع، وكَتَبَ ثلاثةٌ وثلاثة،
واسْتَخْرَجَ (ابتداءً: ءِسْ تَخْ رَ جَ) ثلاثةُ أصولٍ وأربعةُ مقاطع. -/
theorem root_degree_is_not_syllable_degree :
    (syllables (realize fa'lala dhrj .start .continue .fatha)).map List.length = some 3 ∧
    (thulathi.head?.bind fun W => (syllables (realize W ktb .start .continue .fatha)).map List.length)
      = some 3 ∧
    ((thulathi[10]?).bind fun W => (syllables (realize W ktb .start .continue .fatha)).map List.length)
      = some 4 := by
  decide +kernel

/-! ## ٧. همزةُ الوصل: لامُ الأداة ولامُ الأصل -/

/-- حركةُ همزة الوصل في الفعل: ضمّةٌ إن ضُمّ الثالث وإلّا كسرة — بلا شرط اللام. -/
def waslVowelVerb (third : Cell) : Haraka := if third.haraka = .damma then .damma else .kasra

def lqy : Root 3
  | ⟨0, _⟩ => carrierOf 'ل'
  | ⟨1, _⟩ => carrierOf 'ق'
  | _ => carrierOf 'ي'

/-- **الدَّينُ المسمّى `WASL_LAM_ARTICLE_VS_ROOT`**: في افتعل من جذرٍ أوّلُه لام (الْتَقَى) تفتح `waslVowel` الهمزةَ
لأنّ ثانيها لام، وقاعدةُ الفعل تكسرها. -/
theorem wasl_lam_conflict :
    ((thulathi[9]?).map fun W => waslH W lqy) = some .fatha ∧
    ((thulathi[9]?).bind fun W => (W.body[1]?).map fun s => waslVowelVerb (eval lqy s)) = some .kasra := by
  decide +kernel

end A116.Wazn
