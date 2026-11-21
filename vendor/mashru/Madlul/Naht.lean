/-
  Madlul/Naht.lean — النحتُ عند ابن فارس: الرباعيُّ من ثلاثيَّين «آخذةٌ منهما جميعا بحظ».

  السند (المقاييس المختوم): س5274–5283 «أن أكثر ما تراه منه منحوت. ومعنى النحت أن تؤخذ كلمتان وتنحت منهما كلمة تكون آخذة منهما
  جميعا بحظ … على ضربين: أحدهما المنحوت … والضرب الآخر [الموضوع] وضعا»؛ وأمثلتُه بحتر (بتر، حتر) س5289، بحثر (بحث، بثر) س5294،
  بعثق (بعق، بثق) س5299؛ وبلعوم/بلعم «مأخوذ من بلع، إلا أنه زيد عليه ما زيد» س5285–5287.

  المعيار N1 (تعيين البنّاء، `shabaka/naht.py`): الرباعيُّ منحوتٌ إن كان من إسقاطاته (حذفِ حرفٍ واحد) ثلاثيّان مختلفان مشهودان.
  * مبرهن لكلّ: `aakhidha_bihazz` — لكلّ كلمةٍ q وإسقاطين مختلفين: كلُّ حرفٍ من q (بموضعه) عضوٌ في أحد الثلاثيَّين المسقَطين؛
    `manhut_ithnan` — المنحوتُ له ثلاثيّان مختلفان مشهودان بعينهما.
  * على الشاهد (الثلاثيّاتُ كلُّ ما في اللسان من إسقاطات الأمثلة، مولَّدةً في `NahtData.lean`): الثلاثةُ منحوتةٌ والكلمتان اللتان
    سمّاهما ابن فارس بين مشهوداتها (`amthila_manhuta`)؛ و«بلعم» منحوتٌ بـ N1 مع أنّ ابن فارس جعله مزيدًا (`bulum_yukhalif`):
    فـ N1 وحده يُفرط، وقياسُه على اللسان كلِّه (95.4% مقابل 85–87% للحروف المبعثرة) في `Madlul/جدول_اللزوم.md`.
  Lean يبرهن خواصَّ هذا المعيار على المرويّ، لا أنّ الرباعيّ منحوتٌ في اللغة (الدستور م17). بلا sorry ولا axiom ولا native_decide.
-/
import Madlul.NahtData

namespace Naht

/-- إسقاطُ الحرف i. -/
def isqat (q : List Char) (i : Nat) : List Char := q.eraseIdx i

/-- إزالةُ التكرار (يُبقي آخرَ ظهور). -/
def farid : List (List Char) → List (List Char)
  | [] => []
  | a :: l => if a ∈ farid l then farid l else a :: farid l

/-- الثلاثيّاتُ المشهودة من إسقاطات q، بلا تكرار. -/
def mashhudat (T : List (List Char)) (q : List Char) : List (List Char) :=
  farid (((List.range q.length).map (isqat q)).filter (· ∈ T))

/-- N1: منحوتٌ إن كان له ثلاثيّان مختلفان مشهودان. -/
def manhut (T : List (List Char)) (q : List Char) : Bool := decide (2 ≤ (mashhudat T q).length)

/-- «آخذةٌ منهما جميعا بحظ» حرفًا حرفًا: إسقاطان مختلفان i ≠ j من الكلمة q — كلُّ حرفٍ من q باقٍ في أحد الثلاثيَّين. -/
theorem aakhidha_bihazz (q : List Char) {i j : Nat} (h : i ≠ j) (k : Nat) (hk : k < q.length) :
    q[k] ∈ isqat q i ∨ q[k] ∈ isqat q j := by
  unfold isqat
  by_cases hki : k = i
  · subst hki
    exact Or.inr (List.mem_eraseIdx_iff_getElem.mpr ⟨k, hk, h, rfl⟩)
  · exact Or.inl (List.mem_eraseIdx_iff_getElem.mpr ⟨k, hk, hki, rfl⟩)

theorem farid_nodup : ∀ l : List (List Char), (farid l).Nodup
  | [] => by simp [farid]
  | a :: l => by
    unfold farid
    split
    · exact farid_nodup l
    · rename_i h
      exact List.nodup_cons.mpr ⟨h, farid_nodup l⟩

/-- المنحوتُ بـ N1 له ثلاثيّان مختلفان مشهودان بعينهما. -/
theorem manhut_ithnan (T : List (List Char)) (q : List Char) (h : manhut T q = true) :
    ∃ a b, a ∈ mashhudat T q ∧ b ∈ mashhudat T q ∧ a ≠ b := by
  unfold manhut at h
  have h2 := of_decide_eq_true h
  have hn := farid_nodup (((List.range q.length).map (isqat q)).filter (· ∈ T))
  unfold mashhudat at h2 ⊢
  generalize farid (((List.range q.length).map (isqat q)).filter (· ∈ T)) = l at h2 hn ⊢
  match l, h2, hn with
  | a :: b :: _, _, hn =>
    refine ⟨a, b, by simp, by simp, ?_⟩
    intro hab
    subst hab
    simp at hn

/-! ## على الشاهد -/

def T : List (List Char) := thulathiyyat.map String.toList

/-- أمثلةُ ابن فارس الثلاثة منحوتةٌ بـ N1، والكلمتان اللتان سمّاهما بين مشهوداتها. -/
theorem amthila_manhuta :
    ((amthila.filter (·.2.2.2 != "")).all fun e =>
      manhut T e.1.toList && (mashhudat T e.1.toList).contains e.2.2.1.toList &&
        (mashhudat T e.1.toList).contains e.2.2.2.toList) = true := by decide

/-- و«بلعم» — مزيدٌ عند ابن فارس («مأخوذ من بلع، إلا أنه زيد عليه») — منحوتٌ بـ N1: المعيارُ وحده يُفرط. -/
theorem bulum_yukhalif : manhut T "بلعم".toList = true ∧ (mashhudat T "بلعم".toList).contains "بلع".toList = true := by
  decide

end Naht
