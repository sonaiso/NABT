import SLGE.Madlul
import SLGE.Wad
import SLGE.Necessity

/-!
# الجسر: الاقترانُ دالٌّ مرخَّصٌ وحده × مدلولٌ مرخَّصٌ وحده — وقفلُ البرهان

جبران مستقلّان، كلٌّ مغلقٌ على نفسه:
* **SLGE الدالّ وحده** (‎Law‎): القانونُ (ابتداء/وصل/وقف)، والحدُّ الأدنى المكتمل ‎complete'‎، والاستنفادُ.
* **SLGE المدلول وحده** (‎Madlul‎، ‎Cat‎): الأقسامُ الخمسة، والوضعُ ‎Mustamal‎، والإسنادُ زوج.

والجسرُ لا يأخذ من أحدهما ما ليس فيه. يبرهن:
1. **لا اقترانَ بلا مدلول** ولا **بلا دالٍّ مرخَّص** (‎iqtiran_needs_madlul‎، ‎iqtiran_needs_dal‎).
2. **الدالُّ وحده لا يقرّر المدلول:** كلُّ دالٍّ مرخَّصٍ يقبل وضعًا يجعله مستعملًا ووضعًا يجعله مهملًا (‎dal_undetermines‎).
3. **ترخيصُ الانتقال:** ما دون الكلمة يرخّصه نقصُ الدالّ (الخانةُ الواحدة لا تكتمل، ‎nec_second‎)؛
   والكلمةُ تكتمل دالًّا (‎two_complete‎) فلا يُلجئ الدالُّ إلى ما فوقها — والذي يُلجئ إلى التركيب
   نقصُ المدلول وحده (لا إسنادَ في مفرد، ‎Cat.nec_compose‎). فشرطُ انتقال الدالّ مدلولٌ يرخّصه (‎transition‎).
4. **الحالةُ تحمل الإعراب:** الإعراباتُ الأربعة تقابل حالاتِ الخانة الأربع (قطر الندى L77: «فيرفع بضمّة، وينصب بفتحة،
   ويجرّ بكسرة، ويجزم بحذف حركة»)، والعلاماتُ الفرعيّة حواملُها من حروف الزيادة.
5. **الجملةُ المقترنة** أدناها كلمتان، كلٌّ منهما مقترنة.

والشواهد (سيبويه، قطر الندى، المغني، الألفيّة، QAC) تشهد ولا تبني: أسطرُها في ‎wad/MANIFEST.json‎.
-/

namespace SLGE
namespace Bridge

open Law Madlul Cat

/-! ## ١. شرطا الاقتران -/

/-- **الدالُّ المرخَّص وحده:** مكتملٌ ابتداءً ووصلًا ووقفًا. -/
def DalLic (l : List Nat) : Prop := complete' l = true

/-- **الاقتران:** دالٌّ مرخَّص × مدلولٌ موضوعٌ له. -/
def Iqtiran {M : Type} (wad : List Nat → M → Prop) (l : List Nat) : Prop := DalLic l ∧ Mustamal wad l

theorem iqtiran_needs_madlul {M : Type} (wad : List Nat → M → Prop) (h : M → False) (l : List Nat) :
    ¬ Iqtiran wad l := fun ⟨_, hm⟩ => no_maana_no_dal wad h l hm

theorem iqtiran_needs_dal {M : Type} (wad : List Nat → M → Prop) (l : List Nat) (h : complete' l = false) :
    ¬ Iqtiran wad l := fun ⟨hd, _⟩ => by unfold DalLic at hd; rw [h] at hd; cases hd

/-- **أيُّ وضعٍ كان، لا تقترن خانةٌ واحدة** — نقصُ الدالّ يسبق المدلول. -/
theorem no_single_cell {M : Type} (wad : List Nat → M → Prop) : ∀ a < 116, ¬ Iqtiran wad [a] := by
  intro a ha
  apply iqtiran_needs_dal
  have h0 := List.length_eq_zero_iff.mp nec_second.2
  have hn := List.filter_eq_nil_iff.mp h0 a (List.mem_range.mpr ha)
  exact Bool.eq_false_iff.mpr hn

/-! ## ٢. الدالُّ وحده لا يقرّر المدلول -/

/-- **لكلّ دالٍّ مرخَّص:** وضعٌ يقرنه بمعنى، ووضعٌ يتركه مهملًا — فالقسمُ (مستعمل/مهمل) ليس من الدالّ. -/
theorem dal_undetermines (l : List Nat) (_ : DalLic l) :
    Iqtiran (fun x (_ : Unit) => x = l) l ∧ ¬ Mustamal (fun (_ : List Nat) (_ : Unit) => False) l :=
  ⟨⟨by assumption, ⟨(), rfl⟩⟩, fun ⟨_, h⟩ => h⟩

/-! ## ٣. ترخيصُ الانتقال -/

/-- **ما دون الكلمة يرخّصه الدالّ، وما فوقها يرخّصه المدلول:**
(أ) الخانةُ الواحدة لا تكتمل فيُلجئ الدالُّ إلى الثانية؛ (ب) الكلمةُ تكتمل دالًّا (‎9,520‎ من خانتين)؛
(ج) ولا مفردَ يحمل إسنادًا بأيّ قسمٍ كان، وأدنى الإسناد زوجٌ (ثلاثةٌ من تسعة)، ولا زوجَ فيه حرف. -/
theorem transition :
    ((List.range 116).filter fun a => complete' [a]).length = 0 ∧
    (((List.range 116).flatMap fun a => (List.range 116).map fun b => [a, b]).filter complete').length = 9520 ∧
    (∀ k : Kind, ifada [k] = false) ∧
    (Madlul.pairs.filter fun p => isnad p.1 p.2).length = 3 ∧
    (∀ k : Kind, isnad .harf k = false) :=
  ⟨nec_second.2, two_complete, nec_compose, isnad_count.2, fun k => (isnad_harf k).1⟩

/-- **الدالُّ يكتمل حيث لا يكتمل المدلول:** كلمةٌ مكتملةٌ دالًّا (‎قِهْ‎) ومدلولُها المفرد لا يفيد. -/
theorem dal_complete_madlul_not : complete' [4 * 7 + 2, 4 * 1 + 3] = true ∧ ifada [.fil] = false := by
  decide

/-! ## ٤. الحالةُ تحمل الإعراب -/

/-- الإعرابُ ← حالةُ الخانة الأخيرة (فتحة ‎0‎، ضمّة ‎1‎، كسرة ‎2‎، سكون ‎3‎). -/
def irabState : Wad.Irab → Nat
  | .raf => 1
  | .nasb => 0
  | .jarr => 2
  | .jazm => 3

/-- **الإعراباتُ الأربعة هي الحالاتُ الأربع بعينها** — تقابلٌ تامّ. -/
theorem irab_state_bij :
    Wad.allIrab.map irabState = [1, 0, 2, 3] ∧
    (∀ r s : Wad.Irab, irabState r = irabState s → r = s) ∧
    (∀ h < 4, ∃ r, irabState r = h) := by
  refine ⟨rfl, fun r s h => by cases r <;> cases s <;> first | rfl | simp [irabState] at h, fun h hh => ?_⟩
  rcases (by omega : h = 0 ∨ h = 1 ∨ h = 2 ∨ h = 3) with e | e | e | e <;> subst e
  · exact ⟨.nasb, rfl⟩
  · exact ⟨.raf, rfl⟩
  · exact ⟨.jarr, rfl⟩
  · exact ⟨.jazm, rfl⟩

/-- **والجزمُ سكونٌ:** قسمٌ لا يقبل الجزمَ (الاسم) لا تحمل حالتَه آخرَ المعرب؛ والجرُّ كسرةٌ لا يقبلها الفعل. -/
theorem jazm_sukun_fil : irabState .jazm = 3 ∧ (Wad.irabOf .ism).all (fun r => irabState r < 3) = true ∧
    (Wad.irabOf .fil).all (fun r => irabState r != 2) = true := by decide

/-- العلاماتُ الفرعيّة (القطر L78–91): (الباب، الإعراب، حاملُ العلامة). ‎ن=14، ا=2، و=28، ي=11‎. -/
def farIya : List (String × Wad.Irab × Nat) :=
  [("الأسماء الستة", .raf, 28), ("الأسماء الستة", .nasb, 2), ("الأسماء الستة", .jarr, 11),
   ("المثنى", .raf, 2), ("المثنى", .nasb, 11), ("المثنى", .jarr, 11),
   ("جمع المذكر", .raf, 28), ("جمع المذكر", .nasb, 11), ("جمع المذكر", .jarr, 11),
   ("الأمثلة الخمسة", .raf, 14)]

/-- **حواملُ العلامات الفرعيّة كلُّها من حروف الزيادة** (‎سألتمونيها‎): الوحدةُ المرخَّصة سابقًا تحمل الإعراب. -/
theorem fariya_augs : farIya.all (fun x => augs.contains x.2.2) = true := by decide

/-! ## ٥. الجملةُ المقترنة -/

/-- جملةٌ مقترنة: كلُّ كلمةٍ دالٌّ مرخَّص، ولكلٍّ قسمٌ بالوضع، ومجموعُ الأقسام مفيد. -/
def SentIqtiran (ws : List (List Nat)) (kindOf : List Nat → Option Kind) : Prop :=
  (∀ w ∈ ws, DalLic w) ∧ ∃ ks : List Kind, ws.map kindOf = ks.map some ∧ ifada ks = true

/-- **لا جملةَ مقترنةً من كلمةٍ واحدة**، أيًّا كان وضعُها. -/
theorem sent_min (w : List Nat) (kindOf : List Nat → Option Kind) : ¬ SentIqtiran [w] kindOf := by
  rintro ⟨_, ks, hks, hi⟩
  cases ks with
  | nil => simp at hks
  | cons k ks' =>
    cases ks' with
    | nil => rw [nec_compose k] at hi; cases hi
    | cons _ _ => simp at hks

/-- **وتقع من كلمتين:** ‎قِهْ‎ (فعلًا) و‎عِدْ‎ (اسمًا) بوضعٍ مسمًّى للتمثيل — الصورةُ وحدها لا تمنع ولا توجب. -/
theorem sent_two : SentIqtiran [[4 * 7 + 2, 4 * 1 + 3], [4 * 3 + 2, 4 * 17 + 3]]
    (fun w => if w.headD 0 = 4 * 7 + 2 then some .fil else some .ism) := by
  refine ⟨?_, [.fil, .ism], by decide, by decide⟩
  intro w hw; simp at hw; rcases hw with h | h <;> subst h <;> (unfold DalLic; decide)

end Bridge
end SLGE
