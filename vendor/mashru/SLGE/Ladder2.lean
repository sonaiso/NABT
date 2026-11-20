import SLGE.Root
import SLGE.Category

/-!
# سُلَّمُ الضرورة «لكلّ»: الترتيبُ، والموضع، والإفادة، والأدوات

* **الترتيب** (‎nec_order3‎، لكلّ ثلاثيٍّ مرخَّص): الحواملُ وحدها لا تعيّن الجذر — لكلّ جذرٍ مرخَّصٍ
  غيرِ متماثل الحروف جذرٌ آخرُ مرخَّصٌ بحوامله نفسِها.
* **الموضع** (‎nec_position_all‎، لكلّ جذرٍ صحيحٍ لا تجاورَ فيه، ثلاثيٍّ ورباعيٍّ وخماسيّ): الترتيبُ وحده
  لا يعيّن الكلمة — يرخّصه القانونُ على ‎12 / 45 / 171‎ وزنًا.
* **الإفادة** (على جدول الدور المعلَن في ‎Category.lean‎): الكلمةُ الواحدة لا تفيد بأيّ قسمٍ كانت، والحرفُ
  لا يُفيد ولا يزيد في الإفادة شيئًا، والفعلُ يحتاج اسمًا؛ وأدنى المفيد كلمتان: ثلاثٌ من تسع.
* **الأدوات** (مودَعُ وضع: المرادي، الجنى الداني): ‎14 + 33 + 36 + 19 + 3 = 105‎ حرفًا، بالأحاديّ إلى الخماسيّ؛
  وحروفُ الزيادة ‎سألتمونيها‎ كلُّها من الأحاديّ. ولا يُفيد تركيبٌ من حروفٍ وحدها.
-/

namespace SLGE
namespace Law

/-! ## ١. الترتيب -/

def licB (l : List Nat) : Bool := l.all (· < 29) && Mroot.F (Mroot.runL 0 l)

theorem licB_iff (l : List Nat) : Mroot.Lic 0 l ↔ licB l = true := by
  unfold licB Machine.Lic; simp [Mroot]

set_option synthInstance.maxHeartbeats 0 in
set_option synthInstance.maxSize 4096 in
theorem nec_order3B : ∀ a < 29, ∀ b < 29, ∀ c < 29, licB [a, b, c] = true →
    (a = b ∧ b = c) ∨ (a ≠ c ∧ licB [c, b, a] = true) ∨ (a = c ∧ b ≠ a ∧ licB [a, a, b] = true) := by
  decide +kernel

/-- **لكلّ ثلاثيٍّ مرخَّص:** متماثلُ الحروف، أو يُرخَّص مقلوبُه وهو غيرُه، أو (‎أبأ‎) يُرخَّص ‎أأب‎. -/
theorem nec_order3 (a b c : Nat) (ha : a < 29) (hb : b < 29) (hc : c < 29) (h : Mroot.Lic 0 [a, b, c]) :
    (a = b ∧ b = c) ∨ (a ≠ c ∧ Mroot.Lic 0 [c, b, a]) ∨ (a = c ∧ b ≠ a ∧ Mroot.Lic 0 [a, a, b]) := by
  rw [licB_iff, licB_iff]; rw [licB_iff] at h
  exact nec_order3B a ha b hb c hc h

theorem perm_rev (a b c : Nat) : [c, b, a].Perm [a, b, c] := List.reverse_perm [a, b, c]
theorem perm_swap (a b : Nat) : [a, a, b].Perm [a, b, a] := List.Perm.cons a (List.Perm.swap b a [])

/-! ## ٢. الموضع -/

theorem stK_bound : (∀ ss ∈ stK 3, ∀ s ∈ ss, s < 4) ∧ (∀ ss ∈ stK 4, ∀ s ∈ ss, s < 4) ∧
    (∀ ss ∈ stK 5, ∀ s ∈ ss, s < 4) := by decide +kernel

/-- **لكلّ جذرٍ صحيحٍ لا تجاورَ فيه:** عددُ أوزانه المرخَّصة عددُ أوزان الميزان، ‎12 / 45 / 171‎. -/
theorem nec_position_all (k : Nat) (hk : k = 3 ∨ k = 4 ∨ k = 5) (r : List Nat) (hr : SoundR r)
    (hsp : Spaced r) (hl : r.length = (mizan k).length) :
    ((stK k).filter fun ss => Fwasl (run 0 (rootChain r ss))).length = W k := by
  unfold W waznList
  have hb : ∀ ss ∈ stK k, ∀ s ∈ ss, s < 4 := by
    rcases hk with h | h | h <;> subst h
    · exact stK_bound.1
    · exact stK_bound.2.1
    · exact stK_bound.2.2
  rw [List.filter_congr (fun ss hss => wazn_any_root k r ss hr hsp hl (hb ss hss))]

end Law

namespace Cat

/-! ## ٣. الإفادة: أدنى المكتمل كلمتان بينهما إسناد -/

/-- **الإفادة:** مسنَدٌ إليه ومسنَدٌ من كلمتين مختلفتين. -/
def ifada (ks : List Kind) : Bool :=
  (List.range ks.length).any fun i => (List.range ks.length).any fun j =>
    i != j && (rolesOf (ks.getD i .harf)).1 && (rolesOf (ks.getD j .harf)).2

def kinds : List Kind := [.ism, .fil, .harf]

/-- **الكلمةُ الواحدة لا تفيد** — بالاستنفاد على الأقسام الثلاثة. -/
theorem nec_compose : ∀ k : Kind, ifada [k] = false := by intro k; cases k <;> decide

/-- **أدنى المفيد كلمتان:** من تسعِ أزواجٍ مرتّبة تفيد ثلاث: اسمٌ واسم، اسمٌ وفعل، فعلٌ واسم. -/
theorem ifada_pairs :
    ((kinds.flatMap fun a => kinds.map fun b => [a, b]).filter ifada) =
      [[.ism, .ism], [.ism, .fil], [.fil, .ism]] := by decide

/-- **الفعلُ يحتاج اسمًا:** لا يفيد وحدَه، ولا مع فعلٍ أو حرف، ويفيد مع اسم. -/
theorem fil_needs_ism : ifada [.fil] = false ∧ ifada [.fil, .fil] = false ∧ ifada [.fil, .harf] = false ∧
    ifada [.fil, .ism] = true := by decide

theorem getD_harf (ks : List Kind) (h : ∀ k ∈ ks, k = .harf) (i : Nat) : ks.getD i .harf = .harf := by
  rw [List.getD_eq_getElem?_getD]
  cases hc : ks[i]? with
  | none => rfl
  | some k => exact h k (List.mem_iff_getElem?.mpr ⟨i, hc⟩)

/-- **الحرفُ لا يفيد:** ما تألّف من حروفٍ وحدها لا يفيد، بأيّ عددٍ كان. -/
theorem harf_never (ks : List Kind) (h : ∀ k ∈ ks, k = .harf) : ifada ks = false := by
  unfold ifada
  rw [List.any_eq_false]; intro i _
  rw [getD_harf ks h i]; simp [rolesOf]

/-- **الحرفُ معنًى في غيره:** لا يزيد الإفادةَ ولا ينقصها (لكلّ تركيبٍ إلى ثلاث كلمات). -/
theorem harf_neutral : ∀ a ∈ kinds, ∀ b ∈ kinds,
    ifada [.harf, a, b] = ifada [a, b] ∧ ifada [a, .harf, b] = ifada [a, b] ∧ ifada [a, b, .harf] = ifada [a, b] := by
  decide

end Cat

namespace Law

/-! ## ٤. مودَعُ الأدوات: المرادي، الجنى الداني (OpenITI ‎0749BadrDinMisriMuradi.JanaDani.Shamela0026099-ara1‎)

الحواملُ بالنطق: المشدَّدُ حرفان، والألفُ المنطوقة حرف (كما عدّها المرادي: ‎إنّ‎ ثلاثيّ، ‎لكنّ‎ خماسيّ).
ء0 ه1 ا2 ع3 ح4 غ5 خ6 ق7 ك8 ج9 ش10 ي11 ض12 ل13 ن14 ر15 ط16 د17 ت18 ز19 س20 ص21 ظ22 ذ23 ث24 ف25 ب26 م27 و28. -/

/-- الباب الأوّل (L186–190): الهمزة، الباء، التاء، السين، الشين، الفاء، الكاف، اللام، الميم، النون، الهاء، الواو، الألف، الياء. -/
def harf1 : List (List Nat) :=
  [[0], [26], [18], [20], [10], [25], [8], [13], [27], [14], [1], [28], [2], [11]]

/-- الباب الثاني (L1917–1920): إذ، أل، أم، إن، أن، أو، آ، أي، إي، بل، ذا، عن، في، قد، كم، كي، لم، لن، لو، لا، مذ، مع،
من، من، ما، هل، ها، هو، هي، هم، وا، وي، يا. -/
def harf2 : List (List Nat) :=
  [[0,23], [0,13], [0,27], [0,14], [0,14], [0,28], [0,2], [0,11], [0,11], [26,13], [23,2], [3,14], [25,11],
   [7,17], [8,27], [8,11], [13,27], [13,14], [13,28], [13,2], [27,23], [27,3], [27,14], [27,14], [27,2], [1,13],
   [1,2], [1,28], [1,11], [1,27], [28,2], [28,11], [11,2]]

/-- الباب الثالث (L3903–3909): أجل، إذن، إذا، ألا، إلى، أما، إنّ، أنّ، أنا، أنتَ، أنتِ، آي، أيا، بجل، بلى، بله، ثمّ، جلل، جير، خلا،
ربّ، سوف، عدا، عسى، على، كما، لات، ليت، ليس، منذ، متى، نعم، نحن، هما، هنّ، هيا. -/
def harf3 : List (List Nat) :=
  [[0,9,13], [0,23,14], [0,23,2], [0,13,2], [0,13,2], [0,27,2], [0,14,14], [0,14,14], [0,14,2], [0,14,18],
   [0,14,18], [0,2,11], [0,11,2], [26,9,13], [26,13,2], [26,13,1], [24,27,27], [9,13,13], [9,11,15], [6,13,2],
   [15,26,26], [20,28,25], [3,17,2], [3,20,2], [3,13,2], [8,27,2], [13,2,18], [13,11,18], [13,11,20],
   [27,14,23], [27,18,2], [14,3,27], [14,4,14], [1,27,2], [1,14,14], [1,11,2]]

/-- الباب الرابع (L5563–5566): إذ ما، ألّا، إلّا، أمّا، إمّا، أنتم، إيّا، أيمن، حتّى، حاشا، كأنّ، كلّا، لعلّ، لكنْ، لمّا، لولا، لوما،
مهما، هلّا. -/
def harf4 : List (List Nat) :=
  [[0,23,27,2], [0,13,13,2], [0,13,13,2], [0,27,27,2], [0,27,27,2], [0,14,18,27], [0,11,11,2], [0,11,27,14],
   [4,18,18,2], [4,2,10,2], [8,0,14,14], [8,13,13,2], [13,3,13,13], [13,2,8,14], [13,27,27,2], [13,28,13,2],
   [13,28,27,2], [27,1,27,2], [1,13,13,2]]

/-- الباب الخامس (L6750–6754): لكنّ، أنتما، أنتنّ. -/
def harf5 : List (List Nat) := [[13,2,8,14,14], [0,14,18,27,2], [0,14,18,14,14]]

/-- **المودَعُ كما عدّه المرادي:** ‎14، 33، 36، 19، 3‎ — وكلُّ حرفٍ في بابه بعدد حروفه (فحصٌ للنقل). -/
theorem harf_table :
    harf1.length = 14 ∧ harf2.length = 33 ∧ harf3.length = 36 ∧ harf4.length = 19 ∧ harf5.length = 3 ∧
    harf1.all (·.length == 1) ∧ harf2.all (·.length == 2) ∧ harf3.all (·.length == 3) ∧
    harf4.all (·.length == 4) ∧ harf5.all (·.length == 5) ∧
    (harf1 ++ harf2 ++ harf3 ++ harf4 ++ harf5).length = 105 ∧
    (harf1 ++ harf2 ++ harf3 ++ harf4 ++ harf5).all (·.all (· < 29)) := by decide

/-- **حروفُ الزيادة أحاديّةُ المعاني:** كلُّ حرفٍ من ‎سألتمونيها‎ (‎augs‎، الوحدة المرخَّصة سابقًا) حرفُ معنًى أحاديّ،
والأحاديّ يزيد عليها ‎ب ك ش ف‎. -/
theorem augs_are_harf1 : augs.all (fun c => harf1.contains [c]) = true ∧
    (harf1.filter fun l => !augs.contains (l.headD 0)) = [[26], [10], [25], [8]] := by decide

end Law
end SLGE
