/-
  Dal/Adad.lean — عددُ سلسلة الخلايا: ترقيمٌ تقابليٌّ لكلّ سلسلةٍ منتهية، والوصلُ عمليّةٌ على الأعداد.

  قولُ المالك (2026-10-21، 20:35 بتوقيت عمّان)، في آخر تحليلٍ لصقه (أُحيل إلى سطور رسالته بالحرف ر): «انت يجب انت تعمل بمنطق رقمي وفق
  الطريقة العقلية ححل واستنتج وطبق». والتحليلُ يقترح «ترميز يحفظ العمليات» (ر5)، وصيغتُه لعدد السلسلة F(w) = Σ_{j<n} 116^j +
  Σ_i dᵢ·116^(n−1−i) (ر75–79)، وقانونُ الوصل F(uv) = 116^|v|·F(u) + F(v) (ر229) وقال فيه: «لم أضف مبرهنة Lean لهذا القانون في هذه
  الجولة» (ر274)؛ وذكر لـF «براهين التباين والشمول في `Numbering.lean`» من مستودع Alghanem (ر102) — لم أقرأه. وهنا يُبرهَن ذلك على خلايا
  Mashru (`4·حامل + حالة` بترتيب `Dal.hawamil`). ومثالُه («أدخلت البوابة «كَتَبَ»»، ر62) لا يسمّي ترتيبًا، والتحليلُ عرّف رقم الخانة
  d(c,h) = 4·i(c) + i(h) بترتيب الجسر (ر25، ر34) وذكر ترتيبين للحوامل (ر58)؛ فقراءةُ أرقامه بترتيب الجسر قراءةُ البنّاء. خانةُ «كَ» عنده 84 (ر66)
  وهنا 32 (ك رقمُه 8، تاسعُ الحوامل)، وF(كَ) عنده 85 (ر243) وهنا 33، وF(كَتَبَ) عنده 1,144,809 (ر89) وهنا 452,621 (`kataba_wasl`) — فالأرقامُ لا
  تنتقل بين ترتيبين.

  `adad` تُحسب من آخر السلسلة (`adadR` على المقلوب، كلُّ خانةٍ d تُعدّ d+1)، وهي صيغةُ التحليل بحدّيها: `adad_sigha` (لكلّ سلسلة) —
  adad w = majmuAwwal |w| + qima w، و`majmuAwwal n` = Σ_{j<n} 116^j، و`qima w` = Σ_i dᵢ·116^(n−1−i).

  ما يُبرهَن:
  ١. **الوصل** (`adad_wasl`): عددُ الموصول من عددَي الجزأين وطولِ الثاني وحده.
  ٢. **التقابل على المجال** (الخلايا أقلّ من 116): لا يجمع سلسلتين في عدد (`adad_inj`)، ولكلّ عددٍ سلسلةٌ في المجال تعود إليه
     (`adad_fakk`، `fakk_majal`)، والفكُّ يعيد السلسلة (`fakk_adad`). وخارجَ المجال لا تقابل: [116] و[0، 0] عددٌ واحد (`kharij_majal`)،
     فمن يستعمل العددَ رمزًا يحرس المجال أوّلًا.
  ٣. **أثرُ تبديل خانةٍ في موضعها** (`adad_tabdil`): يتغيّر العددُ بفرق الخانتين في منزلتها وحده. وتبديلُ الحركة وحدها في الخليّة 4c+h
     فرقُه فرقُ الحالتين — حسابٌ على الترميز لا مبرهنة —، فلا يتعلّق بترتيب الحوامل؛ وشاهدُه «كَتَبَ» ← «كُتِبَ»: 13,688 (`kataba_kutiba`).
  ٤. **لماذا d+1** (`bila_tul_yajma`): الطيُّ بالأساس 116 بلا إزاحةٍ يجمع «أَبُو» (أوّلُها «ءَ» خليّةُ 0) و«بُو» في عددٍ واحد، وعددُهما هنا مختلف.

  19 مبرهنة بالمعيار الموحَّد (`Nizam/Asas.lean`): 15 لكلّ (`adadR_append`، `adad_wasl`، `adadR_inj`، `adad_inj`، `fakkR_adadR`،
  `adadR_fakkR`، `fakkR_majal`، `fakk_adad`، `adad_fakk`، `fakk_majal`، `adad_tabdil`، `majmuAwwal_succ`، `jam_darb`، `qima_snoc`،
  `adad_sigha`)، ولا تعريفيّة، و4 على الشاهد (`kataba_wasl`، `kataba_kutiba`، `bila_tul_yajma`، `kharij_majal`). طفراتُها P414–P415 في
  `tahaqquq/tafrat.json` تُفشل `lake build`؛ وأعدادُ «كَتَبَ» و«كُتِبَ» فيهما وخلاياهما يحسبها `tahaqquq/test_qawaid.py` §٤ من صورتيهما
  اليدويّتين بصيغة التحليل بحدّيها، مستقلًّا عن `adadR`؛ وP425 (شاهدُ «كَتَبَ» بخليّةٍ أخرى متّسقًا: يمرّ في Lean) يقتلها الاختبارُ وحده.
  لا يُدّعى: أنّ هذا العددَ عددُ الشهادة (لا يحمل همزةَ الوصل ولا «ال» ولا حدودَ الكلمات)؛ ولا أنّ وصلَ خليّتين مرخَّصٌ لغةً — الوصلُ
  هنا حسابٌ على الأعداد، والترخيصُ لقانون الدالّ.
  بلا sorry ولا axiom ولا native_decide.
-/

namespace Dal
namespace Adad

/-- عددُ السلسلة من آخرها: الخانةُ الأولى من القائمة أدنى منزلة، وكلُّ خانةٍ d تُعدّ d+1. -/
def adadR : List Nat → Nat
  | [] => 0
  | d :: l => d + 1 + 116 * adadR l

/-- **عددُ السلسلة**: Σ (dᵢ+1)·116^(n−1−i)، وهي صيغةُ التحليل بحدّيها (`adad_sigha`). -/
def adad (w : List Nat) : Nat := adadR w.reverse

theorem adadR_append : ∀ (a b : List Nat), adadR (a ++ b) = adadR a + 116 ^ a.length * adadR b
  | [], b => by simp [adadR]
  | d :: a, b => by
    simp only [List.cons_append, adadR, List.length_cons, adadR_append a b, Nat.pow_succ]
    have : 116 ^ a.length * 116 * adadR b = 116 * (116 ^ a.length * adadR b) := by
      rw [Nat.mul_comm (116 ^ a.length) 116, Nat.mul_assoc]
    rw [this, Nat.mul_add]; omega

/-- **قانونُ الوصل:** F(u ++ v) = 116^|v|·F(u) + F(v). -/
theorem adad_wasl (u v : List Nat) : adad (u ++ v) = 116 ^ v.length * adad u + adad v := by
  unfold adad
  rw [List.reverse_append, adadR_append, List.length_reverse]
  omega

theorem adadR_inj : ∀ (a b : List Nat), (∀ x ∈ a, x < 116) → (∀ x ∈ b, x < 116) → adadR a = adadR b → a = b
  | [], [], _, _, _ => rfl
  | [], e :: b, _, _, h => by simp [adadR] at h <;> omega
  | d :: a, [], _, _, h => by simp [adadR] at h <;> omega
  | d :: a, e :: b, ha, hb, h => by
    simp only [adadR] at h
    have hd := ha d List.mem_cons_self
    have he := hb e List.mem_cons_self
    have hde : d = e := by omega
    subst hde
    have hab : adadR a = adadR b := by omega
    rw [adadR_inj a b (fun x hx => ha x (List.mem_cons_of_mem _ hx)) (fun x hx => hb x (List.mem_cons_of_mem _ hx)) hab]

/-- **لا يجمع سلسلتين في المجال في عددٍ واحد.** -/
theorem adad_inj (u v : List Nat) (hu : ∀ x ∈ u, x < 116) (hv : ∀ x ∈ v, x < 116) (h : adad u = adad v) : u = v := by
  have := adadR_inj u.reverse v.reverse (fun x hx => hu x (List.mem_reverse.mp hx))
    (fun x hx => hv x (List.mem_reverse.mp hx)) h
  exact List.reverse_inj.mp this

/-! ## الفكّ: لكلّ عددٍ سلسلتُه -/

/-- الفكُّ من آخر السلسلة، بوقودٍ يكفيه العددُ نفسُه. -/
def fakkR : Nat → Nat → List Nat
  | 0, _ => []
  | f + 1, n => if n = 0 then [] else (n - 1) % 116 :: fakkR f ((n - 1) / 116)

def fakk (n : Nat) : List Nat := (fakkR n n).reverse

theorem fakkR_adadR : ∀ (a : List Nat), (∀ x ∈ a, x < 116) → ∀ f, adadR a ≤ f → fakkR f (adadR a) = a
  | [], _, f, _ => by cases f <;> simp [fakkR, adadR]
  | d :: a, ha, f, hf => by
    have hd := ha d List.mem_cons_self
    obtain ⟨f', rfl⟩ : ∃ f', f = f' + 1 := ⟨f - 1, by simp only [adadR] at hf; omega⟩
    simp only [adadR] at hf ⊢
    simp only [fakkR]
    have hne : ¬ (d + 1 + 116 * adadR a = 0) := by omega
    have hm : (d + 1 + 116 * adadR a - 1) % 116 = d := by omega
    have hq : (d + 1 + 116 * adadR a - 1) / 116 = adadR a := by omega
    simp only [hne, ↓reduceIte]
    rw [hm, hq, fakkR_adadR a (fun x hx => ha x (List.mem_cons_of_mem _ hx)) f' (by omega)]

theorem adadR_fakkR : ∀ (f n : Nat), n ≤ f → adadR (fakkR f n) = n
  | 0, n, h => by simp [fakkR, adadR]; omega
  | f + 1, n, h => by
    simp only [fakkR]
    split
    · rename_i h0; simp [adadR, h0]
    · rename_i h0
      simp only [adadR]
      rw [adadR_fakkR f ((n - 1) / 116) (by omega)]
      omega

theorem fakkR_majal : ∀ (f n : Nat), ∀ x ∈ fakkR f n, x < 116
  | 0, _, x, hx => by simp [fakkR] at hx
  | f + 1, n, x, hx => by
    simp only [fakkR] at hx
    split at hx
    · simp at hx
    · rcases List.mem_cons.mp hx with h | h
      · rw [h]; exact Nat.mod_lt _ (by decide)
      · exact fakkR_majal f _ x h

/-- **الفكُّ يعيد السلسلة** ما كانت خلاياها في المجال. -/
theorem fakk_adad (w : List Nat) (hw : ∀ x ∈ w, x < 116) : fakk (adad w) = w := by
  unfold fakk adad
  rw [fakkR_adadR w.reverse (fun x hx => hw x (List.mem_reverse.mp hx)) _ (Nat.le_refl _), List.reverse_reverse]

/-- **الشمول:** كلُّ عددٍ عددُ سلسلة. -/
theorem adad_fakk (n : Nat) : adad (fakk n) = n := by
  unfold adad fakk
  rw [List.reverse_reverse, adadR_fakkR n n (Nat.le_refl _)]

/-- وسلسلتُه في المجال. -/
theorem fakk_majal (n : Nat) : ∀ x ∈ fakk n, x < 116 := by
  intro x hx
  exact fakkR_majal n n x (List.mem_reverse.mp hx)

/-- **أثرُ تبديل خانةٍ في موضعها:** بين `a ++ d :: b` و`a ++ e :: b` فرقُ (e − d)·116^|b| (مكتوبًا بلا طرحٍ في ℕ). -/
theorem adad_tabdil (a b : List Nat) (d e : Nat) :
    adad (a ++ e :: b) + 116 ^ b.length * d = adad (a ++ d :: b) + 116 ^ b.length * e := by
  have k : ∀ x, adad (a ++ x :: b) = 116 ^ b.length * (116 * adad a + (x + 1)) + adad b := by
    intro x
    rw [show a ++ x :: b = (a ++ [x]) ++ b by simp, adad_wasl, adad_wasl]
    simp [adad, adadR]
  rw [k e, k d, Nat.mul_add, Nat.mul_add, Nat.mul_add, Nat.mul_add]
  omega

/-! ## صيغةُ التحليل بحدّيها -/

/-- Σ_{j<n} 116^j: الحدُّ الأوّل في صيغة التحليل. -/
def majmuAwwal (n : Nat) : Nat := ((List.range n).map (116 ^ ·)).sum

/-- Σ_i dᵢ·116^(n−1−i): الحدُّ الثاني. -/
def qima (w : List Nat) : Nat := ((List.range w.length).map (fun i => w.getD i 0 * 116 ^ (w.length - 1 - i))).sum

theorem majmuAwwal_succ (n : Nat) : majmuAwwal (n + 1) = 116 * majmuAwwal n + 1 := by
  have e : ∀ n, majmuAwwal (n + 1) = majmuAwwal n + 116 ^ n := by
    intro n; simp [majmuAwwal, List.range_succ, List.map_append, List.sum_append]
  have h : ∀ n, majmuAwwal n + 116 ^ n = 116 * majmuAwwal n + 1 := by
    intro n
    induction n with
    | zero => simp [majmuAwwal]
    | succ n ih => rw [e, Nat.pow_succ]; omega
  rw [e, h]

theorem jam_darb : ∀ (l : List Nat) (f : Nat → Nat), (l.map (fun i => 116 * f i)).sum = 116 * (l.map f).sum
  | [], _ => rfl
  | a :: l, f => by simp [List.map_cons, List.sum_cons, jam_darb l f, Nat.mul_add]

theorem qima_snoc (u : List Nat) (d : Nat) : qima (u ++ [d]) = 116 * qima u + d := by
  unfold qima
  simp only [List.length_append, List.length_singleton]
  rw [List.range_succ, List.map_append, List.sum_append]
  have hm : (List.range u.length).map (fun i => (u ++ [d]).getD i 0 * 116 ^ (u.length + 1 - 1 - i)) =
      (List.range u.length).map (fun i => 116 * (u.getD i 0 * 116 ^ (u.length - 1 - i))) := by
    apply List.map_congr_left
    intro i hi
    have hi' : i < u.length := List.mem_range.mp hi
    have hg : (u ++ [d]).getD i 0 = u.getD i 0 := by
      simp [List.getD_eq_getElem?_getD, List.getElem?_append_left hi']
    rw [hg, show u.length + 1 - 1 - i = (u.length - 1 - i) + 1 by omega, Nat.pow_succ,
      Nat.mul_comm (116 ^ (u.length - 1 - i)) 116, ← Nat.mul_assoc, Nat.mul_comm (u.getD i 0) 116, Nat.mul_assoc]
  rw [hm, jam_darb]
  simp [List.getD_eq_getElem?_getD]

/-- **`adad` هي صيغةُ التحليل بحدّيها** لكلّ سلسلة. -/
theorem adad_sigha (w : List Nat) : adad w = majmuAwwal w.length + qima w := by
  obtain ⟨r, rfl⟩ : ∃ r, w = r.reverse := ⟨w.reverse, (List.reverse_reverse w).symm⟩
  induction r with
  | nil => rfl
  | cons d r ih =>
    rw [List.reverse_cons, adad_wasl, ih, List.length_append, List.length_singleton, majmuAwwal_succ, qima_snoc]
    simp only [adad, adadR, List.reverse_singleton, Nat.pow_one]
    rw [Nat.mul_add]; omega

/-! ## على الشاهد -/

/-- «كَتَبَ» بخلايا Mashru (`Nizam.Aqd.kataba`: ك 8، ت 18، ب 26 بالفتحة) عددُها 452,621؛ وهو وصلُ «كَ» (33) و«تَبَ» (8,573) بقانون الوصل. -/
theorem kataba_wasl :
    adad [32, 72, 104] = 452621 ∧ adad [32] = 33 ∧ adad [72, 104] = 8573 ∧ 116 ^ 2 * 33 + 8573 = 452621 := by decide

/-- «كُتِبَ» (ضمّةٌ ثمّ كسرة) تزيد على «كَتَبَ» بـ 1·116² + 2·116 = 13,688. -/
theorem kataba_kutiba : adad [33, 74, 104] = adad [32, 72, 104] + 13688 := by decide

/-- **الطيُّ بلا إزاحةٍ يجمع**: «أَبُو» [0، 105، 115] و«بُو» [105، 115] عددٌ واحدٌ بالأساس 116 وحده (الهمزةُ المفتوحة خليّةُ 0)، وعددان
مختلفان بـ `adad`. -/
theorem bila_tul_yajma :
    [0, 105, 115].foldl (fun n d => 116 * n + d) 0 = [105, 115].foldl (fun n d => 116 * n + d) 0 ∧
    adad [0, 105, 115] ≠ adad [105, 115] := by decide

/-- **خارجَ المجال لا تقابل**: حدُّ الكلمة 116 وحده و[0، 0] عددٌ واحد (117). -/
theorem kharij_majal : adad [116] = adad [0, 0] := by decide

end Adad
end Dal
