import SLGE.Bridge
import SLGE.TarkibLit

/-!
# SLGE التركيب: الجملةُ الاسميّة والفعليّة وشبهُ الجملة على القانون العامّ — والخانةُ المقدَّرة لها قيمةٌ في ‎n‎

**الخانةُ (الموضع):** ‎(دور، ملء، إحالة)‎. الملءُ ‎0‎ ظاهر (له دالّ)، ‎1‎ مقدَّر (مستتر/محذوف: غائبٌ دالُّه، حاضرٌ موضعُه).
الأدوار: ‎0‎ مبتدأ، ‎1‎ خبر، ‎2‎ فعل، ‎3‎ فاعل، ‎4‎ مفعول، ‎5‎ جارّ، ‎6‎ مجرور، ‎7‎ أداةٌ عاملة (ناسخ/ناصب/جازم)، ‎8‎ متعلَّقٌ مقدَّر.
الإحالةُ: ‎0‎ لا إحالة، ‎i+1‎ إلى الخانة ‎i‎، ‎14‎ حضورٌ (متكلّم/مخاطب)، ‎15‎ إلى جملةٍ سابقة.
البنى: ‎0‎ اسميّة، ‎1‎ فعليّة، ‎2‎ شبهُ جملة. الأداة: ‎0‎ لا، ‎1‎ كان، ‎2‎ إنّ، ‎3‎ ظنّ، ‎4‎ ناصبُ المضارع، ‎5‎ جازمُه.

**القانونُ في التركيب:**
* **الابتداء:** الناسخُ يفتتح الاسميّة، والمبتدأُ يسبق خبرَه الجملة؛ ولا يُبتدأ بضميرٍ يحيل إلى ما بعده،
  ولا بإحالةٍ إلى جملةٍ سابقة في أوّل الكلام.
* **الوصل:** العاملُ قبل معموله (الفعلُ قبل فاعله، الجارُّ ملاصقٌ مجرورَه، الناصبُ/الجازمُ ملاصقٌ فعلَه)،
  والتقديمُ والتأخيرُ فيما عدا ذلك تبديلٌ مرخَّص؛ والضميرُ المستتر لا يكون إلّا بإحالة.
* **الوقف:** الأدوارُ المطلوبة كلُّها قائمة — ظاهرةً أو مقدَّرة — والخبرُ الجملةُ فيه رابطٌ إلى المبتدأ، وفي الكلام دالٌّ ظاهر.

**الرقم:** ‎n = pair(رتبةُ الإطار، رقمُ الكلمات الظاهرة)‎. فالدورُ والترتيبُ والتقديرُ والإحالةُ والأداة في الإطار،
والمقدَّرُ لا دالَّ له ولكنّ موضعه في الإطار فيغيّر ‎n‎ قطعًا (‎frame_value‎).
-/

set_option synthInstance.maxSize 8192
set_option synthInstance.maxHeartbeats 0
set_option maxRecDepth 100000

namespace SLGE
namespace Tarkib

open Law

abbrev Slot := Nat × Nat × Nat
abbrev Frame := Nat × Nat × List Slot

def ins (x : Nat) : List Nat → List (List Nat)
  | [] => [[x]]
  | y :: l => (x :: y :: l) :: (ins x l).map (y :: ·)

def perms : List Nat → List (List Nat)
  | [] => [[]]
  | x :: l => (perms l).flatMap (ins x)

def roleSets : Nat → List (List Nat)
  | 0 => [[0, 1], [0, 2, 3], [0, 2, 3, 4]]
  | 1 => [[2, 3], [2, 3, 4]]
  | _ => [[5, 6, 8]]

def amils : Nat → List Nat
  | 0 => [0, 1, 2, 3]
  | 1 => [0, 4, 5]
  | _ => [0]

def deic : Nat := 14
def ext : Nat := 15

def roles (sl : List Slot) : List Nat := sl.map (·.1)
def fillAt (sl : List Slot) (i : Nat) : Nat := (sl.getD i (0, 0, 0)).2.1

/-- **القانونُ في التركيب** (ابتداء، وصل، وقف) — كما في مقدّمة الملف. -/
def okF (s a : Nat) (sl : List Slot) : Bool :=
  let rs := roles sl
  let has := fun r => rs.contains r
  let pos := fun r => rs.idxOf r
  -- الوصل: العاملُ قبل معموله
  (!(has 2 && has 3) || decide (pos 2 < pos 3)) &&
  (!(s == 0 && has 2) || decide (pos 0 < pos 2)) &&
  (!(has 5) || pos 6 == pos 5 + 1) &&
  -- الأداة: تفتتح الاسميّة، وتلاصق الفعلَ في الفعليّة، وهي ظاهرة
  ((a != 0) == has 7) &&
  (!(has 7 && s == 0) || pos 7 == 0) &&
  (!(has 7 && s == 1) || pos 7 + 1 == pos 2) &&
  (!(has 7) || fillAt sl (pos 7) == 0 || a == 4) &&
  -- المتعلَّقُ مقدَّر
  (!(has 8) || fillAt sl (pos 8) == 1) &&
  -- في الكلام دالٌّ ظاهر
  sl.any (fun x => x.2.1 == 0) &&
  -- الملءُ والإحالة
  sl.all (fun x =>
    let r := x.1; let f := x.2.1; let p := x.2.2
    (!(f == 1 && (r == 5 || r == 6))) &&
    (!(f == 1 && r == 2 && s == 0)) &&
    (!(f == 1 && r == 2) || fillAt sl (pos 3) == 0) &&
    (if r == 3 && f == 1 then
       (if s == 0 then p == pos 0 + 1
        else p == deic || p == ext ||
          (1 ≤ p && p ≤ sl.length && decide (p - 1 < pos 3) && [0, 4, 6].contains (rs.getD (p - 1) 99)))
     else p == 0)) &&
  -- الاسميّة: لا يُقدَّر طرفاها معًا
  (!(s == 0 && has 1) || !(fillAt sl (pos 0) == 1 && fillAt sl (pos 1) == 1))

def refOpts (n r f : Nat) : List Nat :=
  if r == 3 && f == 1 then List.range (n + 1) ++ [deic, ext] else [0]

def slotsFor (rs : List Nat) : List (List Slot) :=
  let n := rs.length
  rs.foldr (fun r acc => (([0, 1].flatMap fun f => (refOpts n r f).map fun p => (r, f, p))).flatMap
    fun x => acc.map (x :: ·)) [[]]

/-- مولِّدُ قطعةٍ واحدة: بنيةٌ × أداةٌ × مجموعةُ أدوار. -/
def chunk (s a : Nat) (rset : List Nat) : List Frame :=
  (perms (if a == 0 then rset else rset ++ [7])).flatMap fun rs =>
    ((slotsFor rs).filter fun sl => okF s a sl).map fun sl => (s, a, sl)

def keys : List (Nat × Nat × List Nat) :=
  [0, 1, 2].flatMap fun s => (amils s).flatMap fun a => (roleSets s).map fun rset => (s, a, rset)

/-- **الأُطرُ المستنفَدة:** كلُّ بنيةٍ × أداة × ترتيبٍ × ملءٍ × إحالة، ممّا يرخّصه القانون. -/
def frames : List Frame := keys.flatMap fun k => chunk k.1 k.2.1 k.2.2


/-! ### الأُطرُ الحرفيّة تساوي المولَّدة (قطعةً قطعة، فلا يُعاد التوليد في كلّ فحص) -/

theorem keys_eq : keys = [(0, 0, [0, 1]), (0, 0, [0, 2, 3]), (0, 0, [0, 2, 3, 4]), (0, 1, [0, 1]), (0, 1, [0, 2, 3]), (0, 1, [0, 2, 3, 4]), (0, 2, [0, 1]), (0, 2, [0, 2, 3]), (0, 2, [0, 2, 3, 4]), (0, 3, [0, 1]), (0, 3, [0, 2, 3]), (0, 3, [0, 2, 3, 4]), (1, 0, [2, 3]), (1, 0, [2, 3, 4]), (1, 4, [2, 3]), (1, 4, [2, 3, 4]), (1, 5, [2, 3]), (1, 5, [2, 3, 4]), (2, 0, [5, 6, 8])] := by decide

theorem chunk_0 : chunk 0 0 [0, 1] = TarkibLit.lit.getD 0 [] := by decide +kernel
theorem chunk_1 : chunk 0 0 [0, 2, 3] = TarkibLit.lit.getD 1 [] := by decide +kernel
theorem chunk_2 : chunk 0 0 [0, 2, 3, 4] = TarkibLit.lit.getD 2 [] := by decide +kernel
theorem chunk_3 : chunk 0 1 [0, 1] = TarkibLit.lit.getD 3 [] := by decide +kernel
theorem chunk_4 : chunk 0 1 [0, 2, 3] = TarkibLit.lit.getD 4 [] := by decide +kernel
theorem chunk_5 : chunk 0 1 [0, 2, 3, 4] = TarkibLit.lit.getD 5 [] := by decide +kernel
theorem chunk_6 : chunk 0 2 [0, 1] = TarkibLit.lit.getD 6 [] := by decide +kernel
theorem chunk_7 : chunk 0 2 [0, 2, 3] = TarkibLit.lit.getD 7 [] := by decide +kernel
theorem chunk_8 : chunk 0 2 [0, 2, 3, 4] = TarkibLit.lit.getD 8 [] := by decide +kernel
theorem chunk_9 : chunk 0 3 [0, 1] = TarkibLit.lit.getD 9 [] := by decide +kernel
theorem chunk_10 : chunk 0 3 [0, 2, 3] = TarkibLit.lit.getD 10 [] := by decide +kernel
theorem chunk_11 : chunk 0 3 [0, 2, 3, 4] = TarkibLit.lit.getD 11 [] := by decide +kernel
theorem chunk_12 : chunk 1 0 [2, 3] = TarkibLit.lit.getD 12 [] := by decide +kernel
theorem chunk_13 : chunk 1 0 [2, 3, 4] = TarkibLit.lit.getD 13 [] := by decide +kernel
theorem chunk_14 : chunk 1 4 [2, 3] = TarkibLit.lit.getD 14 [] := by decide +kernel
theorem chunk_15 : chunk 1 4 [2, 3, 4] = TarkibLit.lit.getD 15 [] := by decide +kernel
theorem chunk_16 : chunk 1 5 [2, 3] = TarkibLit.lit.getD 16 [] := by decide +kernel
theorem chunk_17 : chunk 1 5 [2, 3, 4] = TarkibLit.lit.getD 17 [] := by decide +kernel
theorem chunk_18 : chunk 2 0 [5, 6, 8] = TarkibLit.lit.getD 18 [] := by decide +kernel

def framesL : List Frame := TarkibLit.lit.flatten

theorem lit_eq : TarkibLit.lit = [TarkibLit.lit.getD 0 [], TarkibLit.lit.getD 1 [], TarkibLit.lit.getD 2 [], TarkibLit.lit.getD 3 [], TarkibLit.lit.getD 4 [], TarkibLit.lit.getD 5 [], TarkibLit.lit.getD 6 [], TarkibLit.lit.getD 7 [], TarkibLit.lit.getD 8 [], TarkibLit.lit.getD 9 [], TarkibLit.lit.getD 10 [], TarkibLit.lit.getD 11 [], TarkibLit.lit.getD 12 [], TarkibLit.lit.getD 13 [], TarkibLit.lit.getD 14 [], TarkibLit.lit.getD 15 [], TarkibLit.lit.getD 16 [], TarkibLit.lit.getD 17 [], TarkibLit.lit.getD 18 []] := by decide +kernel

/-- **المولَّدُ بالقانون هو الحرفيّ بعينه.** -/
theorem frames_eq : frames = framesL := by
  unfold frames framesL
  rw [keys_eq, lit_eq]
  simp only [List.flatMap_cons, List.flatMap_nil, List.flatten_cons, List.flatten_nil,
    chunk_0, chunk_1, chunk_2, chunk_3, chunk_4, chunk_5, chunk_6, chunk_7, chunk_8, chunk_9, chunk_10, chunk_11, chunk_12, chunk_13, chunk_14, chunk_15, chunk_16, chunk_17, chunk_18]

/-- **الاستنفاد:** ‎298‎ إطارًا — ‎168‎ اسميّة، ‎128‎ فعليّة، ‎2‎ شبهُ جملة — ولا بنيةَ رابعة؛ والأُطرُ متمايزة. -/
theorem frames_count : framesL.length = 298 ∧
    (framesL.filter (·.1 == 0)).length = 168 ∧ (framesL.filter (·.1 == 1)).length = 128 ∧
    (framesL.filter (·.1 == 2)).length = 2 ∧ framesL.all (·.1 < 3) = true := by decide +kernel

theorem frames_nodup : framesL.Nodup := by decide +kernel

/-! ## الرقم -/

def fIdx (f : Frame) : Nat := framesL.idxOf f

/-- **رقمُ الجملة:** رتبةُ الإطار مع رقم الكلمات الظاهرة (كلُّ كلمةٍ سلسلةُ خانات). -/
def sEnc (f : Frame) (ws : List (List Nat)) : Nat := pair (fIdx f) (encS (ws.map encS))

def sDec (n : Nat) : Frame × List (List Nat) :=
  (framesL.getD (unpair n).1 (0, 0, []), (decS (unpair n).2).map decS)

theorem map_decS_encS (ws : List (List Nat)) : (ws.map encS).map decS = ws := by
  induction ws with
  | nil => rfl
  | cons w ws ih => simp only [List.map_cons, decS_encS]; simp only [List.map_map] at ih ⊢; exact congrArg _ ih

theorem idxOf_getD (f : Frame) (h : f ∈ framesL) : framesL.getD (framesL.idxOf f) (0, 0, []) = f := by
  rw [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem (List.idxOf_lt_length_iff.mpr h)]
  simp [List.getElem_idxOf]

/-- **الفكّ:** يُستردّ الإطارُ (بما فيه من مقدَّرٍ وإحالةٍ وترتيب) والكلماتُ الظاهرة. -/
theorem s_dec_enc (f : Frame) (h : f ∈ framesL) (ws : List (List Nat)) : sDec (sEnc f ws) = (f, ws) := by
  unfold sDec sEnc fIdx
  rw [unpair_pair, decS_encS, map_decS_encS, idxOf_getD f h]

/-- **كلُّ ما في الإطار له قيمةٌ في ‎n‎:** إطاران مختلفان (ولو في خانةٍ مقدَّرةٍ وحدها، أو إحالتها، أو موضعها،
أو الأداة) يعطيان رقمين مختلفين للكلمات الظاهرة نفسِها. -/
theorem frame_value (f g : Frame) (hf : f ∈ framesL) (hg : g ∈ framesL) (hne : f ≠ g)
    (ws : List (List Nat)) : sEnc f ws ≠ sEnc g ws := by
  intro h
  have := congrArg sDec h
  rw [s_dec_enc f hf, s_dec_enc g hg] at this
  exact hne (Prod.mk.inj this).1

/-! ## التقديمُ والتأخير، والمستتر، والإحالة، والأداة — على الأُطر -/

/-- **التقديمُ والتأخير:** ‎زيدٌ قائمٌ‎ و‎قائمٌ زيدٌ‎ إطاران مرخَّصان مختلفان؛
والفاعلُ لا يتقدّم فعلَه (‎زيدٌ قام‎ ليست فعليّة) بل تصير اسميّةً خبرُها فعلٌ وفاعلُه مستترٌ يحيل إلى المبتدأ. -/
theorem taqdim :
    (0, 0, [(0, 0, 0), (1, 0, 0)]) ∈ framesL ∧ (0, 0, [(1, 0, 0), (0, 0, 0)]) ∈ framesL ∧
    (1, 0, [(3, 0, 0), (2, 0, 0)]) ∉ framesL ∧
    (0, 0, [(0, 0, 0), (2, 0, 0), (3, 1, 1)]) ∈ framesL ∧
    (1, 0, [(2, 0, 0), (3, 0, 0), (4, 0, 0)]) ∈ framesL ∧ (1, 0, [(4, 0, 0), (2, 0, 0), (3, 0, 0)]) ∈ framesL := by
  decide +kernel

/-- **المستترُ موضعٌ بإحالة:** ‎قُمْ‎ (فاعلٌ مقدَّر بحضور المخاطب)، ‎عَبَسَ‎ (مقدَّرٌ يحيل إلى جملةٍ سابقة)؛
ولا مستترَ بلا إحالة، ولا يحيل إلى ما بعده؛ والخبرُ الجملةُ لا بدّ له من رابطٍ إلى المبتدأ. -/
theorem mustatir :
    (1, 0, [(2, 0, 0), (3, 1, deic)]) ∈ framesL ∧ (1, 0, [(2, 0, 0), (3, 1, ext)]) ∈ framesL ∧
    (1, 0, [(2, 0, 0), (3, 1, 0)]) ∉ framesL ∧
    (1, 0, [(2, 0, 0), (3, 1, 3), (4, 0, 0)]) ∉ framesL ∧
    (1, 0, [(4, 0, 0), (2, 0, 0), (3, 1, 1)]) ∈ framesL ∧
    (0, 0, [(0, 0, 0), (2, 0, 0), (3, 1, deic)]) ∉ framesL := by decide +kernel

/-- **المقدَّرُ يميّز ما لا يميّزه الدالّ:** خمسةُ أطرٍ مرخَّصة لكلٍّ منها دالٌّ ظاهرٌ واحد —
فعلٌ بفاعلٍ حاضر، أو بفاعلٍ يحيل إلى سابق، ومبتدأٌ بخبرٍ محذوف، وخبرٌ بمبتدأٍ محذوف، وفاعلٌ بفعلٍ مقدَّر قبله. -/
theorem one_overt_five :
    ([(1, 0, [(2, 0, 0), (3, 1, deic)]), (1, 0, [(2, 0, 0), (3, 1, ext)]), (0, 0, [(0, 0, 0), (1, 1, 0)]),
      (0, 0, [(0, 1, 0), (1, 0, 0)]), (1, 0, [(2, 1, 0), (3, 0, 0)])] : List Frame).all
      (fun f => framesL.contains f && (f.2.2.filter (·.2.1 == 0)).length == 1) = true := by decide +kernel

/-- **الأداةُ موضعٌ وعامل:** ‎إنّ‎ تفتتح الاسميّة ولا تتوسّطها، و‎لم‎ تلاصق فعلَها. -/
theorem adat :
    (0, 2, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]) ∈ framesL ∧ (0, 2, [(0, 0, 0), (7, 0, 0), (1, 0, 0)]) ∉ framesL ∧
    (1, 5, [(7, 0, 0), (2, 0, 0), (3, 1, deic)]) ∈ framesL ∧ (1, 5, [(2, 0, 0), (7, 0, 0), (3, 0, 0)]) ∉ framesL ∧
    (2, 0, [(5, 0, 0), (6, 0, 0), (8, 1, 0)]) ∈ framesL ∧ (2, 0, [(5, 0, 0), (6, 0, 0), (8, 0, 0)]) ∉ framesL := by
  decide +kernel

/-! ## الحالةُ بالموضع: الإعرابُ من (البنية، الأداة، الدور) إلى حالة الخانة الأخيرة -/

/-- الحالةُ المطلوبة في آخر الكلمة الظاهرة (‎none‎: مبنيّ). شاهدُه جداول القطر (‎Wad‎). -/
def reqState (s a r : Nat) : Option Nat :=
  match r with
  | 0 => some (if a == 2 || a == 3 then 0 else 1)
  | 1 => some (if a == 1 || a == 3 then 0 else 1)
  | 2 => if s == 1 then some (if a == 4 then 0 else if a == 5 then 3 else 1) else none
  | 3 => some 1
  | 4 => some 0
  | 6 => some 2
  | _ => none

def lastSt (w : List Nat) : Nat := w.getLastD 0 % 4

def overt (sl : List Slot) : List Slot := sl.filter (·.2.1 == 0)

/-- **الجملةُ المرخَّصة:** إطارٌ مرخَّص، وكلماتٌ بعدد مواضعه الظاهرة، كلُّ كلمةٍ مكتملةٌ دالًّا،
وحالةُ آخرها ما يطلبه موضعُها (في الوصل). -/
def SentOK (f : Frame) (ws : List (List Nat)) : Bool :=
  framesL.contains f && (ws.length == (overt f.2.2).length) &&
  ((overt f.2.2).zip ws).all fun (x, w) =>
    complete' w && (match reqState f.1 f.2.1 x.1 with | some h => lastSt w == h | none => true)

/-- **الإعرابُ يقابل الحالة** (‎Bridge.irab_state_bij‎): الرفعُ ضمّة ‎1‎، النصبُ فتحة ‎0‎، الجرُّ كسرة ‎2‎، الجزمُ سكون ‎3‎؛
والأداةُ تغيّر حالةَ موضعها: المبتدأُ بعد ‎إنّ‎ فتحة، والخبرُ بعد ‎كان‎ فتحة، والمضارعُ بعد الجازم سكون. -/
theorem irab_by_position :
    reqState 0 0 0 = some (Bridge.irabState .raf) ∧ reqState 0 2 0 = some (Bridge.irabState .nasb) ∧
    reqState 0 1 1 = some (Bridge.irabState .nasb) ∧ reqState 1 5 2 = some (Bridge.irabState .jazm) ∧
    reqState 2 0 6 = some (Bridge.irabState .jarr) ∧ reqState 1 0 3 = some (Bridge.irabState .raf) := by decide

/-- **الحالةُ جزءٌ من البرهان:** ‎زيدٌ قائمٌ‎ (‎زَيْدُ قائِمُ‎ مختصرًا: ‎زَيْدُ / قامُ‎) تُرخَّص، وبالفتحة في المبتدأ لا تُرخَّص
بلا ‎إنّ‎، وتُرخَّص بها. (ز=19، ي=11، د=17، ق=7، ا=2، م=27). -/
theorem state_in_proof :
    SentOK (0, 0, [(0, 0, 0), (1, 0, 0)]) [[4 * 19 + 0, 4 * 11 + 3, 4 * 17 + 1], [4 * 7 + 0, 4 * 2 + 3, 4 * 27 + 1]] = true ∧
    SentOK (0, 0, [(0, 0, 0), (1, 0, 0)]) [[4 * 19 + 0, 4 * 11 + 3, 4 * 17 + 0], [4 * 7 + 0, 4 * 2 + 3, 4 * 27 + 1]] = false ∧
    SentOK (0, 2, [(7, 0, 0), (0, 0, 0), (1, 0, 0)])
      [[4 * 0 + 2, 4 * 14 + 3, 4 * 14 + 0], [4 * 19 + 0, 4 * 11 + 3, 4 * 17 + 0], [4 * 7 + 0, 4 * 2 + 3, 4 * 27 + 1]] = true := by
  decide +kernel

/-- **المقدَّرُ لا يفقد قيمته:** ‎قُمْ‎ بإطارَي الحضور والإحالة السابقة — الكلمةُ واحدة والرقمان مختلفان. -/
theorem mustatir_value :
    sEnc (1, 0, [(2, 0, 0), (3, 1, deic)]) [[4 * 7 + 1, 4 * 27 + 3]] ≠
      sEnc (1, 0, [(2, 0, 0), (3, 1, ext)]) [[4 * 7 + 1, 4 * 27 + 3]] :=
  frame_value _ _ (by decide +kernel) (by decide +kernel) (by decide) _

/-! ## الإحالةُ بين الجمل: الكلامُ سلسلةُ جمل -/

/-- **قانونُ الابتداء في الكلام:** لا تحيل الجملةُ الأولى إلى سابق. -/
def discOK (ds : List Frame) : Bool :=
  ds.all (fun f => framesL.contains f) &&
  match ds with
  | [] => false
  | f :: _ => f.2.2.all (·.2.2 != ext)

def dEnc (ds : List (Frame × List (List Nat))) : Nat := encS (ds.map fun p => sEnc p.1 p.2)

/-- **‎عَبَسَ وَتَوَلَّى‎ لا تُبتدأ بها إن أحال فاعلُها إلى سابق؛ ويُرخَّص الكلامُ إذا تقدّمته جملة.** -/
theorem ihala_between :
    discOK [(1, 0, [(2, 0, 0), (3, 1, ext)])] = false ∧
    discOK [(1, 0, [(2, 0, 0), (3, 0, 0)]), (1, 0, [(2, 0, 0), (3, 1, ext)])] = true := by decide +kernel

end Tarkib
end SLGE
