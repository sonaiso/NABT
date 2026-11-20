import A116.MaqayisData
import A116.Rubai

/-!
# شاهدُ الدلالة جدولًا: جذورُ «مقاييس اللغة» صفوفٌ من جدول الدرجة الثلاثيّة

في `Rubai` (ADR ٢٨) سندُ الدلالة للثلاثيّ شاهدٌ عددُه `maqayisCount`، مطابَقٌ في الاختبار. وهنا **الشاهدُ نفسُه جدولًا في
Lean** (`nums`، مولَّدٌ من البايتات المختومة ومطابَقٌ لها في `tests/test_maqayis.py`)، فيُبرهَن عليه:

* `nums_increasing`، `nums_nodup`: لا جذرَ مكرَّرًا.
* `nums_in_range`، `roots_in_table`: كلُّ جذرٍ صفٌّ في `RootGrade.table 3` (‎28³‎).
* `roots_nodup`، `roots_num`: الجذرُ والعددُ تقابل — كلُّ جذرٍ بعدده n لا يشاركه فيه غيرُه.
* `count_is_maqayisCount`: عددُ الصفوف هو عددُ الشاهد الذي فتح الرباعيّ — فالفتحُ صار على جدولٍ مبرهَنٍ لا على عددٍ منقول.
* `witness_share`: الشاهدُ جزءٌ من الجدول: ‎4506 · 100 < 21 · 28³‎ — أقلُّ من خُمسه بقليل؛ وما سواه «لا شاهد» لا «ممتنع».
-/

set_option autoImplicit false

namespace A116.Maqayis

open A116 A116.RootGrade

def increasing : List Nat → Bool
  | a :: b :: t => a < b && increasing (b :: t)
  | _ => true

theorem nums_increasing : increasing nums = true := by decide +kernel

theorem increasing_tail {a : Nat} {t : List Nat} (h : increasing (a :: t) = true) : increasing t = true := by
  cases t with
  | nil => rfl
  | cons b u => simp only [increasing, Bool.and_eq_true] at h; exact h.2

theorem increasing_head_lt : ∀ {a : Nat} {t : List Nat}, increasing (a :: t) = true → ∀ x ∈ t, a < x
  | _, [], _, _, hx => by simp at hx
  | a, b :: u, h, x, hx => by
    simp only [increasing, Bool.and_eq_true, decide_eq_true_eq] at h
    rcases List.mem_cons.1 hx with rfl | hx
    · exact h.1
    · exact Nat.lt_trans h.1 (increasing_head_lt h.2 x hx)

theorem nodup_of_increasing : ∀ {l : List Nat}, increasing l = true → l.Nodup
  | [], _ => List.nodup_nil
  | a :: t, h => by
    refine List.nodup_cons.2 ⟨fun ha => ?_, nodup_of_increasing (increasing_tail h)⟩
    exact Nat.lt_irrefl a (increasing_head_lt h a ha)

theorem nums_nodup : nums.Nodup := nodup_of_increasing nums_increasing

theorem nums_in_range : nums.all (· < 28 ^ 3) = true := by decide +kernel

/-- الجذورُ أصولًا (`RootGrade.unnum`). -/
def roots : List (List (Fin 28)) := nums.map (unnum 3)

theorem roots_in_table : ∀ r ∈ roots, r ∈ table 3 := by
  intro r hr
  simp only [roots, List.mem_map] at hr
  obtain ⟨n, _, rfl⟩ := hr
  exact (mem_table 3 _).2 (unnum_length 3 n)

theorem roots_num : ∀ n ∈ nums, num (unnum 3 n) = n := by
  intro n hn
  exact num_unnum 3 n (by simpa using List.all_eq_true.1 nums_in_range n hn)

theorem nodup_map_of_inj {f : Nat → List (Fin 28)} : ∀ {l : List Nat}, l.Nodup →
    (∀ a ∈ l, ∀ b ∈ l, f a = f b → a = b) → (l.map f).Nodup
  | [], _, _ => List.nodup_nil
  | a :: t, hn, hi => by
    rw [List.nodup_cons] at hn
    simp only [List.map_cons, List.nodup_cons, List.mem_map]
    refine ⟨?_, nodup_map_of_inj hn.2 (fun x hx y hy => hi x (by simp [hx]) y (by simp [hy]))⟩
    rintro ⟨b, hb, hfb⟩
    have := hi b (by simp [hb]) a (by simp) hfb
    exact hn.1 (this ▸ hb)

theorem roots_nodup : roots.Nodup := by
  unfold roots
  refine nodup_map_of_inj nums_nodup ?_
  intro a ha b hb h
  rw [← roots_num a ha, ← roots_num b hb, h]

/-- **عددُ صفوف الشاهد هو عددُ الشاهد الذي فتح الرباعيّ** (`Rubai.maqayisCount`). -/
theorem count_is_maqayisCount : roots.length = Rubai.maqayisCount := by
  simp only [roots, List.length_map]
  decide +kernel

/-- **حدُّ الشاهد**: أقلُّ من 21% من جدول الدرجة. -/
theorem witness_share : roots.length * 100 < 21 * 28 ^ 3 := by
  simp only [roots, List.length_map]
  decide +kernel

end A116.Maqayis
