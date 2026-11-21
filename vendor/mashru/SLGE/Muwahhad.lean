import SLGE.Simat2

/-!
# الإطارُ الموحَّد: كلُّ الأُطر السابقة حالةٌ خاصّةٌ منه

**الإطارُ الموحَّد** ‎U = (غلافٌ قبله، إطارُ التركيب، سماتُه، امتدادُه، عاملٌ خارجيّ على العامل، موضعُ ‎إلّا‎، شِعر؟، حذفُ النون، …)‎.

* **الغلاف** (أدواتٌ تتصدّر الإطار): ‎1‎ النفي (ما/لا)، ‎2‎ هل، ‎3‎ الهمزة. **مسوِّغا العموم مربوطان به:** المبتدأُ النكرة بمسوِّغ النفي
  لا يُرخَّص إلّا وفي الغلاف نفي، وبمسوِّغ الاستفهام إلّا وفيه أداةُ استفهام (القطر L153: «ما رجلٌ في الدار» و«أإلهٌ مع الله»).
* **الاستثناءُ المفرَّغ** (القطر L332: «أو فقد التمامَ فعلى حسب العوامل، ويسمّى مفرَّغًا»): ‎إلّا‎ قبل خانةٍ اسميّةٍ ظاهرة، ولا يكون
  إلّا في غلافٍ فيه نفي؛ والمستثنى يأخذ إعرابَ موضعه؛ فإن كان فاعلًا فالفعلُ يطابق فاعلًا مذكّرًا محذوفًا — فلا تُرخَّص
  «ما قامت إلّا هند» في النثر وتُرخَّص في الشعر (القطر L227: «وإنما امتنع في النثر … لأنّ الفاعل مذكّرٌ محذوف»).
* **العاملُ على العامل:** الناصبُ أو الجازم على الناسخ الفعليّ (‎لن يكونَ، لم يكنْ‎): الناسخُ مضارعٌ معرب، وحالتُه نصبٌ أو جزم،
  ويعمل هو في اسمه وخبره؛ وحذفُ نون مضارع كان المجزوم جائزٌ «إن لم يلقها ساكنٌ ولا ضميرُ نصبٍ متّصل» (القطر L178).
-/

set_option synthInstance.maxSize 8192
set_option synthInstance.maxHeartbeats 0
set_option maxRecDepth 100000

namespace SLGE
namespace Muwahhad

open Tarkib Maqam Simat

/-- ربطُ مسوِّغَي العموم بالغلاف. -/
def musawwighLink (pre : List Nat) (ex : List Ext) : Bool :=
  ex.all fun e => (e.1 != 1 || pre.contains 1) && (e.1 != 2 || pre.contains 2 || pre.contains 3)

def setFeatAt (ats : List Attr) (i : Nat) (ft : Feat) : List Attr :=
  ats.mapIdx fun j t => if j == i then (t.1, t.2.1, ft, t.2.2.2) else t

def setTanithAt (ex : List Ext) (i : Nat) : List Ext :=
  (List.range (max ex.length (i + 1))).map fun j => if j == i then ((extAt ex j).1, (extAt ex j).2.1, 0, (extAt ex j).2.2.2) else extAt ex j

/-- العاملُ الخارجيّ على الناسخ الفعليّ (‎0‎ لا، ‎4‎ ناصب، ‎5‎ جازم). -/
def outerOK (f : Frame) (ats : List Attr) (outer : Nat) (nunDel nextSakin pronAttached : Bool) : Bool :=
  if outer == 0 then !nunDel
  else
    (outer == 4 || outer == 5) && f.1 == 0 && (f.2.1 == 1 || f.2.1 == 3) &&
    (let t := attrAt ats ((roles f.2.2).idxOf 7); t.1 == 1 && !t.2.2.2) &&
    (!nunDel || (outer == 5 && f.2.1 == 1 && !nextSakin && !pronAttached))

/-- **الإطارُ الموحَّد المرخَّص.** -/
def uOK (pre : List Nat) (f : Frame) (ats : List Attr) (ex : List Ext) (outer : Nat) (illa : Option Nat)
    (poetry nunDel nextSakin pronAttached : Bool) : Bool :=
  pre.all (fun t => 1 ≤ t && t ≤ 3) && musawwighLink pre ex &&
  outerOK f ats outer nunDel nextSakin pronAttached &&
  match illa with
  | none => annOK2 f ats ex
  | some i =>
    pre.contains 1 && i < f.2.2.length && isNom (f.2.2.getD i (0, 0, 0)).1 && fillAt f.2.2 i == 0 &&
    (if (f.2.2.getD i (0, 0, 0)).1 == 3 then
       annOK2 f (setFeatAt ats i (3, 0, (attrAt ats i).2.2.1.2.2)) (setTanithAt ex i) ||
       (poetry && annOK2 f ats ex)
     else annOK2 f ats ex)

/-- **التوحيد:** بلا غلافٍ ولا إلّا ولا عاملٍ خارجيّ، الإطارُ الموحَّد هو الإطارُ المسمَّى (‎annOK2‎) بعينه — لكلّ إطارٍ وسماتٍ وامتداد،
ما لم يُدَّعَ مسوِّغُ عمومٍ لا أداةَ له. -/
theorem u_conservative (f : Frame) (ats : List Attr) (ex : List Ext) (h : ex.all (fun e => e.1 != 1 && e.1 != 2) = true) :
    uOK [] f ats ex 0 none false false false false = annOK2 f ats ex := by
  unfold uOK musawwighLink outerOK
  simp only [List.all_nil, Bool.true_and, beq_self_eq_true, if_true, Bool.not_false]
  have : (ex.all fun e => (e.1 != 1 || [].contains 1) && (e.1 != 2 || [].contains 2 || [].contains 3)) = true := by
    rw [List.all_eq_true] at h ⊢
    intro e he
    have := h e he
    simp only [Bool.and_eq_true, bne_iff_ne, ne_eq] at this
    simp [this.1, this.2]
  rw [this]; simp

/-! ## ١. مسوِّغا العموم مربوطان بأداتهما -/

/-- **‎ما رجلٌ في الدار‎ بالنفي مرخَّصة، وبلا أداة النفي لا؛ و‎هل رجلٌ في الدار؟‎ مرخَّصة، وبالنفي وحده لا يُرخَّص مسوِّغُ الاستفهام.** -/
theorem musawwigh_linked :
    uOK [1] (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 0 0 0, noun 0 0 0] [(1, false, 0, 0), (0, true, 0, 0)] 0 none false false false false = true ∧
    uOK [] (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 0 0 0, noun 0 0 0] [(1, false, 0, 0), (0, true, 0, 0)] 0 none false false false false = false ∧
    uOK [2] (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 0 0 0, noun 0 0 0] [(2, false, 0, 0), (0, true, 0, 0)] 0 none false false false false = true ∧
    uOK [3] (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 0 0 0, noun 0 0 0] [(2, false, 0, 0), (0, true, 0, 0)] 0 none false false false false = true ∧
    uOK [1] (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 0 0 0, noun 0 0 0] [(2, false, 0, 0), (0, true, 0, 0)] 0 none false false false false = false := by
  decide +kernel

/-! ## ٢. الاستثناءُ المفرَّغ بإلّا -/

/-- **‎ما قامَ إلّا هندٌ‎ مرخَّصة (الفعلُ للمذكّر المحذوف)، و‎ما قامتْ إلّا هندٌ‎ لا في النثر وتُرخَّص في الشعر؛
ولا مفرَّغَ بلا نفي (‎قامَ إلّا هندٌ‎)؛ و‎ما رأيتُ إلّا زيدًا‎ المستثنى مفعولٌ منصوبٌ بموضعه.** -/
theorem istithna_mufarragh :
    uOK [1] (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 0 0, noun 1 1 0] [e0, e0] 0 (some 1) false false false false = true ∧
    uOK [1] (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 1 0, noun 1 1 0] [e0, e0] 0 (some 1) false false false false = false ∧
    uOK [1] (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 1 0, noun 1 1 0] [e0, e0] 0 (some 1) true false false false = true ∧
    uOK [] (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 0 0, noun 1 1 0] [e0, e0] 0 (some 1) false false false false = false ∧
    uOK [1] (1, 0, [(2, 0, 0), (3, 1, hudur), (4, 0, 0)]) [(0, 9, (1, 2, 0), true), pron 1 2 0, noun 1 0 0] [e0, e0, e0] 0 (some 2)
      false false false false = true ∧
    reqState 1 0 3 = some 1 ∧ reqState 1 0 4 = some 0 := by decide +kernel

/-! ## ٣. العاملُ على العامل -/

/-- **‎لم يكنْ زيدٌ قائمًا‎ (جازمٌ على كان، والنونُ محذوفة)، و‎لن يكونَ زيدٌ قائمًا‎ (ناصب)؛ ولا تُحذف النونُ إن لقيها ساكن
(‎لم يكنِ الذين‎) أو ضميرُ نصبٍ متّصل (‎لم يكنْه‎)، ولا مع الناصب؛ ولا يدخل الجازمُ على كان الماضية، ولا العاملُ الخارجيُّ على ‎إنّ‎.** -/
theorem amil_ala_amil :
    uOK [] (0, 1, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]) [(1, 9, (0, 0, 0), false), noun 1 0 0, noun 0 0 0] [e0, e0, e0] 5 none
      false true false false = true ∧
    uOK [] (0, 1, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]) [(1, 9, (0, 0, 0), false), noun 1 0 0, noun 0 0 0] [e0, e0, e0] 4 none
      false false false false = true ∧
    uOK [] (0, 1, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]) [(1, 9, (0, 0, 0), false), noun 1 0 0, noun 0 0 0] [e0, e0, e0] 5 none
      false true true false = false ∧
    uOK [] (0, 1, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]) [(1, 9, (0, 0, 0), false), noun 1 0 0, noun 0 0 0] [e0, e0, e0] 5 none
      false true false true = false ∧
    uOK [] (0, 1, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]) [(1, 9, (0, 0, 0), false), noun 1 0 0, noun 0 0 0] [e0, e0, e0] 4 none
      false true false false = false ∧
    uOK [] (0, 1, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]) [(0, 9, (0, 0, 0), true), noun 1 0 0, noun 0 0 0] [e0, e0, e0] 5 none
      false false false false = false ∧
    uOK [] (0, 2, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]) [harfA, noun 1 0 0, noun 0 0 0] [e0, e0, e0] 5 none
      false false false false = false := by decide +kernel

/-- **المعادلاتُ تتركّب:** حالةُ الناسخ من العامل الخارجيّ (نصبٌ ‎0‎ أو جزمٌ ‎3‎)، وحالتا اسمه وخبره منه هو (رفعٌ ونصب) —
والأُطرُ الاسميّة التي يدخلها عاملٌ خارجيّ ‎84‎، فالمركّبةُ ‎168‎. -/
theorem amil_compose :
    reqState 1 4 2 = some 0 ∧ reqState 1 5 2 = some 3 ∧ reqState 0 1 0 = some 1 ∧ reqState 0 1 1 = some 0 ∧
    (framesL.filter fun f => f.1 == 0 && (f.2.1 == 1 || f.2.1 == 3)).length = 84 := by decide +kernel

/-! ## الرقم الموحَّد -/

def bCode (b : Bool) : Nat := if b then 1 else 0

def uEnc (pre : List Nat) (f : Frame) (ats : List Attr) (ex : List Ext) (outer : Nat) (illa : Option Nat)
    (poetry nunDel : Bool) (ws : List (List Nat)) : Nat :=
  pair (encS pre) (pair (annEnc f ats ws) (pair (encS (ex.map extCode))
    (pair outer (pair (match illa with | none => 0 | some i => i + 1) (pair (bCode poetry) (bCode nunDel))))))

/-- **كلُّ مكوّنٍ في الإطار الموحَّد قيمةٌ في ‎n‎:** الغلاف، والإطار، والسمات، والكلمات، والامتداد، والعاملُ الخارجيّ، وموضعُ إلّا،
والشعر، وحذفُ النون — رقمان متساويان مكوّناتُهما متساوية. -/
theorem u_value (pre pre' : List Nat) (f g : Frame) (hf : f ∈ framesL) (hg : g ∈ framesL)
    (ats ats' : List Attr) (ex ex' : List Ext) (o o' : Nat) (il il' : Option Nat) (p p' nd nd' : Bool)
    (ws ws' : List (List Nat)) (h : uEnc pre f ats ex o il p nd ws = uEnc pre' g ats' ex' o' il' p' nd' ws') :
    pre = pre' ∧ f = g ∧ ats = ats' ∧ ws = ws' ∧ ex = ex' ∧ o = o' ∧ il = il' ∧ p = p' ∧ nd = nd' := by
  unfold uEnc at h
  obtain ⟨h1, h⟩ := pair_injective h
  obtain ⟨h2, h⟩ := pair_injective h
  obtain ⟨h3, h⟩ := pair_injective h
  obtain ⟨h4, h⟩ := pair_injective h
  obtain ⟨h5, h⟩ := pair_injective h
  obtain ⟨h6, h7⟩ := pair_injective h
  obtain ⟨a1, a2, a3⟩ := attr_value f g hf hg ats ats' ws ws' h2
  refine ⟨encS_inj _ _ h1, a1, a3, a2, ext_value ex ex' h3, h4, ?_, ?_, ?_⟩
  · cases il <;> cases il' <;> simp_all
  · cases p <;> cases p' <;> simp_all [bCode]
  · cases nd <;> cases nd' <;> simp_all [bCode]

end Muwahhad
end SLGE
