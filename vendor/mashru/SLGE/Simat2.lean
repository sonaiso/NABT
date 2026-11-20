import SLGE.Simat

/-!
# تتمّةُ السمات: مسوِّغاتُ الابتداء بالنكرة، ومطابقةُ الخبر، والتأنيثُ المجازيّ، ومؤشّراتُ المفعول والعائد

**الامتدادُ لكلّ خانة** ‎Ext = (مسوِّغ، جامد؟، نوعُ التأنيث، نوعُ الكلمة)‎ — وكلُّه قيمةٌ في ‎n‎:
* المسوِّغ (القطر L153: «ويقع المبتدأ نكرةً إن عمّ أو خصّ»): ‎0‎ لا، ‎1‎ عمومٌ بالنفي (‎ما رجلٌ في الدار‎)، ‎2‎ عمومٌ بالاستفهام
  (‎أإلهٌ مع الله‎)، ‎3‎ خصوصٌ بالوصف (‎ولعبدٌ مؤمنٌ خيرٌ‎)، ‎4‎ خصوصٌ بالإضافة (‎خمسُ صلواتٍ‎)؛ وتقدُّمُ الخبر من الإطار نفسِه
  (الألفيّة L189: «ما لم تُفِد كعند زيدٍ نمِرة»).
* الجامد (الألفيّة L185: «والمفردُ الجامدُ فارغ، وإن يشتقّ فهو ذو ضميرٍ مستكن»): الخبرُ المشتقّ فيه ضميرٌ مستتر يحيل إلى المبتدأ،
  **فمطابقتُه مشتقّةٌ من قانون الإحالة نفسِه** (‎Maqam.refOK‎) لا مفروضة؛ والجامدُ فارغٌ فلا يُطلب.
* نوعُ التأنيث في الفاعل الظاهر (القطر L222–229): ‎0‎ حقيقيٌّ متّصل (يجب)، ‎1‎ مجازيّ (الوجهان)، ‎2‎ حقيقيٌّ منفصل (الوجهان)،
  ‎3‎ باب نعم وبئس (الوجهان)، ‎4‎ جمعُ تكسير (الوجهان)، ‎5‎ جمعُ تصحيح («فكمفرديهما»: يجب)؛ والمستترُ يطابق دائمًا («ويمتنع في غيرهن»).
* نوعُ الكلمة: ‎0‎ عاديّ، ‎1‎ ضميرٌ ظاهر (مفعولٌ/مجرورٌ محيل)، ‎2‎ موصول، ‎3‎ إشارة، ‎4‎ عائد.
-/

set_option synthInstance.maxSize 8192
set_option synthInstance.maxHeartbeats 0
set_option maxRecDepth 100000

namespace SLGE
namespace Simat

open Tarkib Maqam

abbrev Ext := Nat × Bool × Nat × Nat

def extAt (ex : List Ext) (i : Nat) : Ext := ex.getD i (0, false, 0, 0)

/-- **الوجهان في التأنيث:** فاعلٌ ظاهر من هذه الأنواع يجوز معه تذكيرُ الفعل وتأنيثُه. -/
def tanithFree (k : Nat) (fa : Feat) : Bool := ((k == 1 || k == 2 || k == 3) && fa.2.1 == 1) || k == 4

/-- قوانينُ الوصل بالامتداد. -/
def linkOK2 (s : Nat) (sl : List Slot) (ats : List Attr) (ex : List Ext) : Bool :=
  let rs := roles sl; let pos := fun r => rs.idxOf r; let has := fun r => rs.contains r
  let fv := (attrAt ats (pos 2)).2.2.1
  let fa := (attrAt ats (pos 3)).2.2.1
  let est := fillAt sl (pos 3) == 1
  let fm := (attrAt ats (pos 0)).2.2.1
  -- الفعلُ وفاعلُه: المطابقةُ في الجنس إلّا في مواضع الوجهين، والإفرادُ مع الظاهر
  (!(has 2 && has 3) ||
    (if est then fv == fa
     else (fv.2.1 == fa.2.1 || tanithFree (extAt ex (pos 3)).2.2.1 fa) && fv.1 == 3 && fv.2.2 == 0)) &&
  -- الأمر
  (!(has 2) || (attrAt ats (pos 2)).1 != 2 || (est && fa.1 == 2)) &&
  -- المستترُ (والرابط) يحيل إحالةً مرخَّصة
  (!(has 3 && est) ||
    (let p := (sl.getD (pos 3) (0, 0, 0)).2.2
     let ante := (List.range (pos 3)).map fun j => (attrAt ats j).2.2.1
     refOK fa p ante (p == sabiq) false false)) &&
  -- المبتدأ النكرة: بمسوِّغ (عمومٌ أو خصوص أو تقدُّمُ الخبر)
  (!(s == 0 && has 0 && (attrAt ats (pos 0)).2.1 == 0) ||
    (has 1 && decide (pos 1 < pos 0)) || (1 ≤ (extAt ex (pos 0)).1 && (extAt ex (pos 0)).1 ≤ 4)) &&
  -- الخبرُ المفرد المشتقّ: ضميرُه المستكنّ يحيل إلى المبتدأ مطابقًا؛ والجامدُ فارغ
  (!(s == 0 && has 0 && has 1 && !(extAt ex (pos 1)).2.1) ||
    refOK (3, (attrAt ats (pos 1)).2.2.1.2.1, (attrAt ats (pos 1)).2.2.1.2.2) 1 [fm] false false false)

def annOK2 (f : Frame) (ats : List Attr) (ex : List Ext) : Bool :=
  framesL.contains f && ats.length == f.2.2.length && ex.length == f.2.2.length &&
  (f.2.2.zip ats).all (fun p => slotAttrOK f.1 f.2.1 p.1 p.2) && linkOK2 f.1 f.2.2 ats ex &&
  ex.all (fun e => e.1 ≤ 4 && e.2.2.1 ≤ 5 && e.2.2.2 ≤ 4)

def e0 : Ext := (0, false, 0, 0)

/-! ## ١. مسوِّغاتُ الابتداء بالنكرة -/

/-- **‎رجلٌ في الدار‎ بلا مسوِّغ لا تُرخَّص؛ وبالنفي (‎ما رجلٌ في الدار‎) وبالاستفهام وبالوصف (‎عبدٌ مؤمنٌ خيرٌ‎) وبالإضافة تُرخَّص؛
وبتقدُّم الخبر (‎عند زيدٍ نمِرةٌ‎) تُرخَّص بلا مسوِّغٍ زائد.** (الخبرُ هنا جامدٌ أو ظرفيٌّ، ‎jamid = true‎.) -/
theorem musawwigh :
    annOK2 (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 0 0 0, noun 0 0 0] [e0, (0, true, 0, 0)] = false ∧
    annOK2 (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 0 0 0, noun 0 0 0] [(1, false, 0, 0), (0, true, 0, 0)] = true ∧
    annOK2 (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 0 0 0, noun 0 0 0] [(2, false, 0, 0), (0, true, 0, 0)] = true ∧
    annOK2 (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 0 0 0, noun 0 0 0] [(3, false, 0, 0), (0, true, 0, 0)] = true ∧
    annOK2 (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 0 0 0, noun 0 0 0] [(4, false, 0, 0), (0, true, 0, 0)] = true ∧
    annOK2 (0, 0, [(1, 0, 0), (0, 0, 0)]) [noun 0 1 0, noun 0 1 0] [(0, true, 0, 0), e0] = true := by decide +kernel

/-! ## ٢. مطابقةُ الخبر المفرد للمبتدأ: من ضميره المستكنّ -/

/-- **‎هندٌ قائمةٌ‎ مرخَّصة و‎هندٌ قائمٌ‎ لا (المشتقّ ذو ضمير)؛ و‎هندٌ أسدٌ‎ مرخَّصة (الجامدُ فارغ)؛ و‎الزيدان قائمان‎ لا ‎قائمٌ‎؛ والمطابقةُ لا تتعلّق بموضع المبتدأ: ‎قائمةٌ هندٌ‎ و‎كانت هندٌ قائمةً‎ تُرخَّصان وبالمذكّر لا.** -/
theorem khabar_tatabuq :
    annOK2 (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 1 1 0, noun 0 1 0] [e0, e0] = true ∧
    annOK2 (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 1 1 0, noun 0 0 0] [e0, e0] = false ∧
    annOK2 (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 1 1 0, noun 0 0 0] [e0, (0, true, 0, 0)] = true ∧
    annOK2 (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 1 0 1, noun 0 0 1] [e0, e0] = true ∧
    annOK2 (0, 0, [(0, 0, 0), (1, 0, 0)]) [noun 1 0 1, noun 0 0 0] [e0, e0] = false ∧
    annOK2 (0, 0, [(1, 0, 0), (0, 0, 0)]) [noun 0 1 0, noun 1 1 0] [e0, e0] = true ∧
    annOK2 (0, 0, [(1, 0, 0), (0, 0, 0)]) [noun 0 0 0, noun 1 1 0] [e0, e0] = false ∧
    annOK2 (0, 1, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]) [(0, 9, (0, 0, 0), true), noun 1 1 0, noun 0 1 0] [e0, e0, e0] = true ∧
    annOK2 (0, 1, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]) [(0, 9, (0, 0, 0), true), noun 1 1 0, noun 0 0 0] [e0, e0, e0] = false := by
  decide +kernel

/-! ## ٣. التأنيثُ المجازيّ ومواضعُ الوجهين -/

/-- **‎طلعتِ الشمسُ‎ و‎طلعَ الشمسُ‎ كلاهما (مجازيّ)؛ ‎قامَ هندٌ‎ لا (حقيقيٌّ متّصل)؛ ‎حضرَ القاضيَ امرأةٌ‎ (منفصل)؛
‎قالتِ الأعرابُ‎ (تكسير)؛ ‎قامتِ الزيدون‎ لا (تصحيح كمفرده)؛ و‎الشمسُ طلعَ‎ لا (المستترُ يطابق).** -/
theorem tanith :
    annOK2 (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 1 0, noun 1 1 0] [e0, (0, false, 1, 0)] = true ∧
    annOK2 (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 0 0, noun 1 1 0] [e0, (0, false, 1, 0)] = true ∧
    annOK2 (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 0 0, noun 1 1 0] [e0, (0, false, 0, 0)] = false ∧
    annOK2 (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 0 0, noun 1 1 0] [e0, (0, false, 2, 0)] = true ∧
    annOK2 (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 1 0, noun 1 0 2] [e0, (0, false, 4, 0)] = true ∧
    annOK2 (1, 0, [(2, 0, 0), (3, 0, 0)]) [past 1 0, noun 1 0 2] [e0, (0, false, 5, 0)] = false ∧
    annOK2 (0, 0, [(0, 0, 0), (2, 0, 0), (3, 1, 1)]) [noun 1 1 0, past 0 0, pron 3 0 0] [e0, e0, (0, false, 1, 0)] = false ∧
    annOK2 (0, 0, [(0, 0, 0), (2, 0, 0), (3, 1, 1)]) [noun 1 1 0, past 1 0, pron 3 1 0] [e0, e0, e0] = true := by
  decide +kernel

/-! ## ٤. المؤشّراتُ: الضميرُ الظاهر المحيل، والعائدُ إلى الموصول -/

abbrev DSent2 := Frame × List Attr × List (Nat × Nat) × List Ext

/-- **قانونُ الإحالة في الكلام:**
* المستترُ المحيلُ إلى سابق، والضميرُ الظاهرُ الغائب (نوع ‎1‎)، يحملان مؤشّرًا إلى خانةٍ اسميّةٍ قبلهما مطابقة؛ ولا مؤشّرَ لغيرهما إلّا العائد.
* العائدُ (نوع ‎4‎) يشير إلى موصولٍ (نوع ‎2‎) في الجملة السابقة مباشرة، ويطابقه (‎Maqam.silaOK‎)؛
* وكلُّ موصولٍ تتبعه صلةٌ فيها عائدٌ إليه. -/
def discOK2 (ds : List DSent2) : Bool :=
  (List.range ds.length).all fun m =>
    let d := ds.getD m ((0, 0, []), [], [], [])
    let n := d.1.2.2.length
    annOK2 d.1 d.2.1 d.2.2.2 && d.2.2.1.length == n &&
    ((List.range n).all fun i =>
      let x := d.1.2.2.getD i (0, 0, 0); let ptr := d.2.2.1.getD i (0, 0)
      let kind := (extAt d.2.2.2 i).2.2.2
      let fa := (attrAt d.2.1 i).2.2.1
      let tgt := ds.getD (m - ptr.1) ((0, 0, []), [], [], [])
      let y := tgt.1.2.2.getD ptr.2 (99, 0, 0)
      let fb := (attrAt tgt.2.1 ptr.2).2.2.1
      if kind == 4 then
        ptr.1 == 1 && 1 ≤ m && (extAt tgt.2.2.2 ptr.2).2.2.2 == 2 && silaOK fb fa (if x.2.1 == 1 then 0 else 1)
      else if (x.2.2 == sabiq) || (kind == 1 && fa.1 == 3) then
        1 ≤ ptr.1 && ptr.1 ≤ m && isNom y.1 && fb.1 == 3 && fa.1 == 3 && fa.2.1 == fb.2.1 && fa.2.2 == fb.2.2
      else ptr == (0, 0)) &&
    -- كلُّ موصولٍ تتبعه صلةٌ بعائد
    ((List.range n).all fun i =>
      (extAt d.2.2.2 i).2.2.2 != 2 ||
        (let nx := ds.getD (m + 1) ((0, 0, []), [], [], [])
         m + 1 < ds.length &&
         (List.range nx.1.2.2.length).any fun j =>
           (extAt nx.2.2.2 j).2.2.2 == 4 && nx.2.2.1.getD j (0, 0) == (1, i)))

def pk : Ext := (0, false, 0, 1)   -- ضميرٌ ظاهر
def mw : Ext := (0, false, 0, 2)   -- موصول
def ad : Ext := (0, false, 0, 4)   -- عائد

/-- **ضميرُ المفعول:** ‎رأيتُ زيدًا. أكرمتُه.‎ الهاءُ تشير إلى ‎زيدًا‎ (جملةٌ إلى الوراء، الخانة ‎2‎)؛ ولا تشير ‎ها‎ المؤنّثةُ إليه، ولا ضميرٌ بلا مؤشّر. -/
theorem ptr_mafool :
    discOK2 [((1, 0, [(2, 0, 0), (3, 1, hudur), (4, 0, 0)]), [(0, 9, (1, 2, 0), true), pron 1 2 0, noun 1 0 0], [(0, 0), (0, 0), (0, 0)], [e0, e0, e0]),
             ((1, 0, [(2, 0, 0), (3, 1, hudur), (4, 0, 0)]), [(0, 9, (1, 2, 0), true), pron 1 2 0, pron 3 0 0], [(0, 0), (0, 0), (1, 2)], [e0, e0, pk])] = true ∧
    discOK2 [((1, 0, [(2, 0, 0), (3, 1, hudur), (4, 0, 0)]), [(0, 9, (1, 2, 0), true), pron 1 2 0, noun 1 0 0], [(0, 0), (0, 0), (0, 0)], [e0, e0, e0]),
             ((1, 0, [(2, 0, 0), (3, 1, hudur), (4, 0, 0)]), [(0, 9, (1, 2, 0), true), pron 1 2 0, pron 3 1 0], [(0, 0), (0, 0), (1, 2)], [e0, e0, pk])] = false ∧
    discOK2 [((1, 0, [(2, 0, 0), (3, 1, hudur), (4, 0, 0)]), [(0, 9, (1, 2, 0), true), pron 1 2 0, noun 1 0 0], [(0, 0), (0, 0), (0, 0)], [e0, e0, e0]),
             ((1, 0, [(2, 0, 0), (3, 1, hudur), (4, 0, 0)]), [(0, 9, (1, 2, 0), true), pron 1 2 0, pron 3 0 0], [(0, 0), (0, 0), (0, 0)], [e0, e0, pk])] = false := by
  decide +kernel

/-- **العائد:** ‎جاءَ الذي — قامَ‎: الفاعلُ المستتر في الصلة عائدٌ إلى الموصول؛ و‎جاءت التي — قامَ‎ لا؛
ولا موصولَ بلا صلةٍ فيها عائد. -/
theorem ptr_aid :
    discOK2 [((1, 0, [(2, 0, 0), (3, 0, 0)]), [past 0 0, pron 3 0 0], [(0, 0), (0, 0)], [e0, mw]),
             ((1, 0, [(2, 0, 0), (3, 1, sabiq)]), [past 0 0, pron 3 0 0], [(0, 0), (1, 1)], [e0, ad])] = true ∧
    discOK2 [((1, 0, [(2, 0, 0), (3, 0, 0)]), [past 1 0, pron 3 1 0], [(0, 0), (0, 0)], [e0, mw]),
             ((1, 0, [(2, 0, 0), (3, 1, sabiq)]), [past 0 0, pron 3 0 0], [(0, 0), (1, 1)], [e0, ad])] = false ∧
    discOK2 [((1, 0, [(2, 0, 0), (3, 0, 0)]), [past 0 0, pron 3 0 0], [(0, 0), (0, 0)], [e0, mw])] = false := by
  decide +kernel

/-! ## الرقم: الامتدادُ في ‎n‎ -/

def extCode (e : Ext) : Nat := pair e.1 (pair (if e.2.1 then 1 else 0) (pair e.2.2.1 e.2.2.2))

theorem extCode_inj (e e' : Ext) (h : extCode e = extCode e') : e = e' := by
  obtain ⟨a, b, c, d⟩ := e
  obtain ⟨a', b', c', d'⟩ := e'
  unfold extCode at h
  obtain ⟨h1, h⟩ := pair_injective h
  obtain ⟨h2, h⟩ := pair_injective h
  obtain ⟨h3, h4⟩ := pair_injective h
  simp only at h1 h2 h3 h4
  subst h1 h3 h4
  cases b <;> cases b' <;> simp_all

/-- **المسوِّغُ والجمودُ ونوعُ التأنيث ونوعُ الكلمة قيمٌ في ‎n‎:** امتدادان برقمٍ واحدٍ امتدادٌ واحد. -/
theorem ext_value (ex ex' : List Ext) (h : encS (ex.map extCode) = encS (ex'.map extCode)) : ex = ex' :=
  map_inj extCode extCode_inj _ _ (encS_inj _ _ h)

end Simat
end SLGE
