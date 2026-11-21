import SLGE.TarkibExt
import SLGE.Awamil

/-!
# سِماتُ الخانة في الإطار: الزمن، والتعريف، والجنس والعدد والشخص، والبناء والإعراب، والمحلّ، والعلاقة — كلُّها في ‎n‎

**الخانةُ المسمَّاة:** ‎(حامل/حالة الكلمة، موضعُها في الإطار، سماتُها)‎. السِّمة ‎Attr = (زمن، تعريف، (شخص، جنس، عدد)، مبنيّ؟)‎:
الزمن ‎0‎ ماضٍ، ‎1‎ مضارع، ‎2‎ أمر، ‎9‎ لا زمن؛ التعريف ‎0‎ نكرة، ‎1‎ معرفة، ‎9‎ لا.

**القانون (ابتداء/وصل/وقف) على السمات:**
* **الزمن:** الفعلُ ماضٍ أو مضارعٌ أو أمر؛ الماضي والأمرُ مبنيّان والمضارعُ معرب؛ الناصبُ والجازم لا يدخلان إلّا على المضارع
  (القطر L96–114)؛ والأمرُ فاعلُه مخاطَبٌ مستتر (القطر L59)؛ والناسخُ الفعليّ (كان، ظنّ) ماضٍ مبنيّ أو مضارعٌ معرب.
* **التعريف:** المضمرُ معرفةٌ مبنيّ (القطر L123–126)؛ والمبتدأُ النكرةُ لا يُبتدأ به إلّا بمسوِّغ — والمبنيُّ منها هنا
  تقدّمُ الخبر (‎في الدار رجلٌ‎)؛ وسائرُ المسوِّغات (العموم، الوصف…) غيرُ مبنيّةٍ في هذه الطبقة: لا حكم، لا امتناع.
* **الجنس والعدد (المطابقة):** الفعلُ يطابق فاعلَه جنسًا (القطر L222)، ويُفرَد مع الظاهر (L220–221)، ويطابق المستترَ كلَّه؛
  والرابطُ يطابق المبتدأ؛ والمستترُ يطابق ما يحيل إليه (‎Maqam.refOK‎).
* **البناء والإعراب والمحلّ:** لكلّ موضعٍ إعرابٌ محلّيّ (‎Tarkib.reqState‎) — مرفوعٌ أو منصوبٌ أو مجرورٌ أو مجزوم —
  يُطلب في دالّ المعرب، ويبقى في ‎n‎ للمبنيّ والمقدَّر («في محلّ …»).
* **العلاقة:** الفاعليّةُ للفاعل، والمفعوليّةُ للمفعول، والإسنادُ للمبتدأ والخبر والفعل، والسببيّةُ للجملة بعد فاء السببيّة
  (‎أنْ‎ مضمرة) وبين جملتي الشرط.
-/

set_option synthInstance.maxSize 8192
set_option synthInstance.maxHeartbeats 0
set_option maxRecDepth 100000

namespace SLGE
namespace Simat

open Tarkib Maqam

abbrev Attr := Nat × Nat × Feat × Bool

def isNom (r : Nat) : Bool := r == 0 || r == 1 || r == 3 || r == 4 || r == 6

def attrAt (ats : List Attr) (i : Nat) : Attr := ats.getD i (9, 9, (0, 0, 0), true)

/-- سماتُ الخانة الواحدة بحسب دورها. -/
def slotAttrOK (s a : Nat) (x : Slot) (t : Attr) : Bool :=
  let r := x.1; let f := x.2.1
  let tn := t.1; let d := t.2.1; let ft := t.2.2.1; let mb := t.2.2.2
  if r == 2 then
    tn ≤ 2 && d == 9 && mb == (tn != 1) && ((a != 4 && a != 5) || tn == 1) && (tn != 2 || (a == 0 && s == 1))
  else if isNom r then
    tn == 9 && d ≤ 1 && 1 ≤ ft.1 && ft.1 ≤ 3 && ft.2.1 ≤ 2 && ft.2.2 ≤ 2 &&
    (f != 1 || (d == 1 && mb)) && (ft.1 == 3 || (d == 1 && mb)) && (f == 1 || ft.1 == 3)
  else if r == 7 then d == 9 && (if a == 1 || a == 3 then tn ≤ 1 && mb == (tn == 0) else tn == 9 && mb)
  else tn == 9 && d == 9 && mb

/-- قوانينُ الوصل بين السمات: المطابقةُ والأمرُ والمسوِّغ. -/
def linkOK (s : Nat) (sl : List Slot) (ats : List Attr) : Bool :=
  let rs := roles sl; let pos := fun r => rs.idxOf r; let has := fun r => rs.contains r
  let fv := (attrAt ats (pos 2)).2.2.1
  let fa := (attrAt ats (pos 3)).2.2.1
  let est := fillAt sl (pos 3) == 1
  -- الفعلُ وفاعلُه
  (!(has 2 && has 3) ||
    (fv.2.1 == fa.2.1 && (if est then fv == fa else fv.1 == 3 && fv.2.2 == 0))) &&
  -- الأمرُ: فاعلُه مخاطَبٌ مستتر
  (!(has 2) || (attrAt ats (pos 2)).1 != 2 || (est && fa.1 == 2)) &&
  -- المستترُ يحيل إحالةً مرخَّصة بسماته (الرابطُ في الاسميّة إلى المبتدأ)
  (!(has 3 && est) ||
    (let p := (sl.getD (pos 3) (0, 0, 0)).2.2
     let ante := (List.range (pos 3)).map fun j => (attrAt ats j).2.2.1
     refOK fa p ante (p == sabiq) false false)) &&
  -- المبتدأ النكرة: بمسوِّغ تقدّمِ الخبر
  (!(s == 0 && has 0 && (attrAt ats (pos 0)).2.1 == 0) || (has 1 && decide (pos 1 < pos 0)))

def annOK (f : Frame) (ats : List Attr) : Bool :=
  framesL.contains f && ats.length == f.2.2.length &&
  (f.2.2.zip ats).all (fun p => slotAttrOK f.1 f.2.1 p.1 p.2) && linkOK f.1 f.2.2 ats

/-! ## الشواهد على القانون -/

def past (g n : Nat) : Attr := (0, 9, (3, g, n), true)
def mudari (g n : Nat) : Attr := (1, 9, (3, g, n), false)
def noun (d g n : Nat) : Attr := (9, d, (3, g, n), false)
def pron (p g n : Nat) : Attr := (9, 1, (p, g, n), true)
def harfA : Attr := (9, 9, (0, 0, 0), true)

/-- **المطابقةُ في الجنس:** ‎قامتْ هندٌ‎ مرخَّصة و‎قامَ هندٌ‎ (فعلٌ مذكّر وفاعلٌ مؤنّث) لا؛ والفعلُ مفردٌ مع الظاهر: ‎قاموا الرجالُ‎ لا (في هذه الطبقة). -/
theorem tatabuq :
    annOK (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 1 0, noun 1 1 0] = true ∧
    annOK (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 0 0, noun 1 1 0] = false ∧
    annOK (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 0 2, noun 1 0 2] = false ∧
    annOK (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 0 0, noun 1 0 2] = true := by decide +kernel

/-- **الرابطُ يطابق المبتدأ:** ‎الطالباتُ قُمْنَ‎ مرخَّصة، و‎الطالباتُ قامَ‎ لا. -/
theorem rabit_tatabuq :
    annOK (0, 0, [(0, 0, 0), (2, 0, 0), (3, 1, 1)]) [noun 1 1 2, past 1 2, pron 3 1 2] = true ∧
    annOK (0, 0, [(0, 0, 0), (2, 0, 0), (3, 1, 1)]) [noun 1 1 2, past 0 0, pron 3 0 0] = false := by decide +kernel

/-- **الزمنُ في الإطار:** ‎قُمْ‎ أمرٌ مبنيّ فاعلُه مخاطَبٌ مستتر؛ ولا أمرَ بفاعلٍ غائب؛ و‎لم يقمْ زيدٌ‎ مضارعٌ معرب،
ولا يدخل الجازمُ على الماضي؛ و‎كان‎ الناسخ ماضٍ مبنيّ و‎يكون‎ مضارعٌ معرب، ولا أمرَ في الناسخ. -/
theorem zaman :
    annOK (1, 0, [(2, 0, 0), (3, 1, hudur)]) [(2, 9, (2, 0, 0), true), pron 2 0 0] = true ∧
    annOK (1, 0, [(2, 0, 0), (3, 1, hudur)]) [(2, 9, (3, 0, 0), true), pron 3 0 0] = false ∧
    annOK (1, 0, [(4, 0, 0), (2, 0, 0), (3, 1, 1)]) [noun 1 0 0, (2, 9, (3, 0, 0), true), pron 3 0 0] = false ∧
    annOK (1, 0, [(4, 0, 0), (2, 0, 0), (3, 1, 1)]) [noun 1 0 0, past 0 0, pron 3 0 0] = true ∧
    annOK (1, 5, [(7, 0, 0), (2, 0, 0), (3, 0, 0)]) [harfA, mudari 0 0, noun 1 0 0] = true ∧
    annOK (1, 5, [(7, 0, 0), (2, 0, 0), (3, 0, 0)]) [harfA, past 0 0, noun 1 0 0] = false ∧
    annOK (0, 1, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]) [(0, 9, (0, 0, 0), true), noun 1 0 0, noun 0 0 0] = true ∧
    annOK (0, 1, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]) [(1, 9, (0, 0, 0), false), noun 1 0 0, noun 0 0 0] = true ∧
    annOK (0, 1, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]) [(2, 9, (0, 0, 0), true), noun 1 0 0, noun 0 0 0] = false := by
  decide +kernel

/-- **التعريف:** ‎في الدار رجلٌ‎ (خبرٌ مقدَّم يسوّغ المبتدأ النكرة) مرخَّصة، و‎رجلٌ في الدار‎ بلا مسوِّغٍ مبنيٍّ هنا لا تُرخَّص؛
والمضمرُ معرفةٌ مبنيّ، فمستترٌ نكرةٌ لا يكون. -/
theorem tarif :
    annOK (0, 0, [(1, 0, 0), (0, 0, 0)]) [noun 0 0 0, noun 0 0 0] = true ∧
    annOK (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 0 0 0, noun 0 0 0] = false ∧
    annOK (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 1 0 0, noun 0 0 0] = true ∧
    annOK (1, 0, [(2, 0, 0), (3, 1, hudur)]) [(0, 9, (2, 0, 0), true), (9, 0, (2, 0, 0), true)] = false ∧
    annOK (1, 0, [(2, 0, 0), (3, 1, sabiq)]) [past 0 0, (9, 0, (3, 0, 0), true)] = false ∧
    annOK (1, 0, [(2, 0, 0), (3, 1, sabiq)]) [past 0 0, pron 3 0 0] = true := by
  decide +kernel

/-! ## المحلّ: المرفوعاتُ والمنصوباتُ والمجروراتُ والمجزومات -/

/-- **الإعرابُ المحلّيّ لكلّ موضع** في الأُطر كلّها: عددُ المواضع بمحلّ رفعٍ ونصبٍ وجرٍّ وجزم، وما لا محلَّ له (العاملُ والجارُّ
والمتعلَّقُ المقدَّر والفعلُ في غير الفعليّة). -/
def mahallCounts : List Nat :=
  let all := framesL.flatMap fun f => f.2.2.map fun x => reqState f.1 f.2.1 x.1
  [(all.filter (· == some 1)).length, (all.filter (· == some 0)).length,
   (all.filter (· == some 2)).length, (all.filter (· == some 3)).length, (all.filter (· == none)).length]

theorem mahall_exhaust : mahallCounts = [400, 400, 2, 32, 370] ∧ mahallCounts.sum =
    (framesL.flatMap fun f => f.2.2).length := by decide +kernel

/-- **المبنيُّ والمقدَّرُ لهما محلّ:** في ‎قُمْ‎ الفاعلُ مقدَّرٌ مبنيٌّ في محلّ رفع؛ وفي ‎يا زيدُ‎ الدالُّ ضمّةٌ والمحلُّ نصب. -/
theorem mahall_mabni :
    reqState 1 0 3 = some 1 ∧ (pron 2 0 0).2.2.2 = true ∧
    TarkibExt.nidaDal 0 = some 1 ∧ TarkibExt.nidaMahall = 0 := by decide

/-! ## العلاقة: الفاعليّةُ والمفعوليّةُ والإسنادُ والسببيّة -/

/-- علاقةُ الموضع: ‎1‎ مسندٌ إليه، ‎2‎ مسند، ‎3‎ فاعليّة، ‎4‎ مفعوليّة، ‎5‎ تعلّق، ‎6‎ عامل (ومنه الجارّ). -/
def semOf (r : Nat) : Nat :=
  match r with
  | 0 => 1 | 1 => 2 | 2 => 2 | 3 => 3 | 4 => 4 | 6 => 5 | 8 => 5 | 7 => 6 | 5 => 6 | _ => 0

/-- السببيّةُ في الجملة: فاءُ السببيّة (‎أنْ‎ مضمرة قبل المضارع). -/
def sababiyya (f : Frame) : Bool := f.2.1 == 4 && f.2.2.contains (7, 1, 0)

/-- **كلُّ موضعٍ في كلّ إطارٍ له علاقة**، والتقديمُ لا يغيّر العلاقةَ ويغيّر ‎n‎؛ والسببيّةُ في ‎32‎ إطارًا بعينها،
وبين جملتي الشرط (‎TarkibExt.shartState‎). -/
theorem alaqa :
    framesL.all (fun f => f.2.2.all fun x => semOf x.1 != 0) = true ∧
    ([(2, 0, 0), (3, 0, 0), (4, 0, 0)] : List Slot).map (semOf ·.1) = [2, 3, 4] ∧
    ([(4, 0, 0), (2, 0, 0), (3, 0, 0)] : List Slot).map (semOf ·.1) = [4, 2, 3] ∧
    fIdx (1, 0, [(2, 0, 0), (3, 0, 0), (4, 0, 0)]) ≠ fIdx (1, 0, [(4, 0, 0), (2, 0, 0), (3, 0, 0)]) ∧
    (framesL.filter sababiyya).length = 32 := by decide +kernel

/-! ## الرقم: السماتُ في ‎n‎ -/

def attrCode (t : Attr) : Nat := pair t.1 (pair t.2.1 (pair (pair t.2.2.1.1 (pair t.2.2.1.2.1 t.2.2.1.2.2)) (if t.2.2.2 then 1 else 0)))

theorem attrCode_inj (t u : Attr) (h : attrCode t = attrCode u) : t = u := by
  obtain ⟨a, b, ⟨p, g, n⟩, m⟩ := t
  obtain ⟨a', b', ⟨p', g', n'⟩, m'⟩ := u
  unfold attrCode at h
  obtain ⟨h1, h⟩ := pair_injective h
  obtain ⟨h2, h⟩ := pair_injective h
  obtain ⟨h3, h4⟩ := pair_injective h
  obtain ⟨h5, h3⟩ := pair_injective h3
  obtain ⟨h6, h7⟩ := pair_injective h3
  simp only at h1 h2 h5 h6 h7 h4
  subst h1 h2 h5 h6 h7
  cases m <;> cases m' <;> simp_all

theorem map_inj {α : Type} (g : α → Nat) (hg : ∀ x y, g x = g y → x = y) :
    ∀ (l l' : List α), l.map g = l'.map g → l = l'
  | [], [], _ => rfl
  | [], _ :: _, h => by simp at h
  | _ :: _, [], h => by simp at h
  | x :: l, y :: l', h => by
    simp only [List.map_cons, List.cons.injEq] at h
    rw [hg x y h.1, map_inj g hg l l' h.2]

theorem encS_inj (a b : List Nat) (h : encS a = encS b) : a = b := by
  have := congrArg decS h; rwa [decS_encS, decS_encS] at this

def annEnc (f : Frame) (ats : List Attr) (ws : List (List Nat)) : Nat := pair (sEnc f ws) (encS (ats.map attrCode))

/-- **كلُّ سمةٍ قيمةٌ في ‎n‎:** جملتان مسمّاتان برقمٍ واحد إطارُهما واحد، وكلماتُهما واحدة، وسماتُهما واحدة — زمنًا وتعريفًا
وجنسًا وعددًا وشخصًا وبناءً. -/
theorem attr_value (f g : Frame) (hf : f ∈ framesL) (hg : g ∈ framesL) (ats ats' : List Attr) (ws ws' : List (List Nat))
    (h : annEnc f ats ws = annEnc g ats' ws') : f = g ∧ ws = ws' ∧ ats = ats' := by
  unfold annEnc at h
  obtain ⟨h1, h2⟩ := pair_injective h
  have d := congrArg sDec h1
  rw [s_dec_enc f hf, s_dec_enc g hg] at d
  exact ⟨(Prod.mk.inj d).1, (Prod.mk.inj d).2, map_inj attrCode attrCode_inj _ _ (encS_inj _ _ h2)⟩

/-! ## الإحالةُ بين الجمل: مؤشّرٌ إلى خانةٍ بعينها في جملةٍ بعينها -/

/-- جملةٌ في الكلام: إطار، وسمات، ومؤشّرٌ لكلّ خانة ‎(كم جملةً إلى الوراء، أيّ خانة)‎؛ ‎(0,0)‎ لا مؤشّر. -/
abbrev DSent := Frame × List Attr × List (Nat × Nat)

/-- **قانونُ الإحالة بين الجمل:** كلُّ مستترٍ يحيل إلى سابق يحمل مؤشّرًا إلى خانةٍ اسميّةٍ في جملةٍ قبله، سماتُها تطابقه؛
ولا مؤشّرَ لغيره؛ ولا يحيل أوّلُ الكلام إلى سابق. -/
def discOK (ds : List DSent) : Bool :=
  (List.range ds.length).all fun m =>
    let d := ds.getD m ((0, 0, []), [], [])
    annOK d.1 d.2.1 && d.2.2.length == d.1.2.2.length &&
    (List.range d.1.2.2.length).all fun i =>
      let x := d.1.2.2.getD i (0, 0, 0); let ptr := d.2.2.getD i (0, 0)
      if x.2.2 == sabiq then
        1 ≤ ptr.1 && ptr.1 ≤ m &&
        (let t := ds.getD (m - ptr.1) ((0, 0, []), [], [])
         let y := t.1.2.2.getD ptr.2 (99, 0, 0)
         let fa := (attrAt d.2.1 i).2.2.1; let fb := (attrAt t.2.1 ptr.2).2.2.1
         isNom y.1 && fb.1 == 3 && fa.1 == 3 && fa.2.1 == fb.2.1 && fa.2.2 == fb.2.2)
      else ptr == (0, 0)

/-- **‎جاءتْ هندٌ. ثمّ قامتْ.‎** المستترُ في الثانية يحيل إلى الفاعل في الأولى (جملةٌ واحدةٌ إلى الوراء، الخانة ‎1‎)؛
ولا يحيل مذكّرٌ إليها، ولا إلى الفعل، ولا أوّلُ الكلام. -/
theorem ihala_ptr :
    discOK [((1, 0, [(2, 0, 0), (3, 0, 0)]), [past 1 0, noun 1 1 0], [(0, 0), (0, 0)]),
            ((1, 0, [(2, 0, 0), (3, 1, sabiq)]), [past 1 0, pron 3 1 0], [(0, 0), (1, 1)])] = true ∧
    discOK [((1, 0, [(2, 0, 0), (3, 0, 0)]), [past 1 0, noun 1 1 0], [(0, 0), (0, 0)]),
            ((1, 0, [(2, 0, 0), (3, 1, sabiq)]), [past 0 0, pron 3 0 0], [(0, 0), (1, 1)])] = false ∧
    discOK [((1, 0, [(2, 0, 0), (3, 0, 0)]), [past 1 0, noun 1 1 0], [(0, 0), (0, 0)]),
            ((1, 0, [(2, 0, 0), (3, 1, sabiq)]), [past 1 0, pron 3 1 0], [(0, 0), (1, 0)])] = false ∧
    discOK [((1, 0, [(2, 0, 0), (3, 1, sabiq)]), [past 1 0, pron 3 1 0], [(0, 0), (1, 1)])] = false := by
  decide +kernel

def ptrCode (ps : List (Nat × Nat)) : Nat := encS (ps.map fun p => pair p.1 p.2)

def dEnc (ds : List DSent) (wss : List (List (List Nat))) : Nat :=
  encS ((ds.zip wss).map fun (d, ws) => pair (annEnc d.1 d.2.1 ws) (ptrCode d.2.2))

/-- **المؤشّرُ قيمةٌ في ‎n‎:** الكلامُ نفسُه بمؤشّرين مختلفين رقمان مختلفان. -/
theorem ptr_value (ps ps' : List (Nat × Nat)) (h : ptrCode ps = ptrCode ps') : ps = ps' := by
  unfold ptrCode at h
  apply map_inj (fun p : Nat × Nat => pair p.1 p.2) _ _ _ (encS_inj _ _ h)
  intro x y hxy; obtain ⟨a, b⟩ := pair_injective hxy; exact Prod.ext a b

end Simat
end SLGE
