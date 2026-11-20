import A116.Zawaid

/-!
# السوابقُ قبل الفعل المبنيّ: قائمةٌ مغلقة، والمرشَّحاتُ لواحقُ الكلمة نفسِها (ADR ٤٦، قرارُ المالك 2026-10-12)

`gate.recover` لا يقرأ «فَقَالُوا» لأنّ الفهرسَ صورُ الفعل وحدَه (`PROCLITIC_NOT_STRIPPED`، ADR ٤١: 3,444 فعلًا بسابقةٍ
بلا قراءة من 3,516). والسوابقُ ليست زوائدَ الاشتقاق: هي حروفُ معانٍ أحاديّةٌ تتّصل بما بعدها خطًّا (مغني اللبيب،
باب الحروف المفردة). وقبل الفعل الماضي والأمر أربعٌ، مفتوحةً كلُّها، بترتيبٍ لا يُبدَّل:

    همزةُ الاستفهام «أَ»  ←  العاطفة «وَ» أو «فَ»  ←  لامُ الابتداء/القسم «لَ»

## ما يُبرهَن

* `candidates_head`: الكلمةُ نفسُها أوّلُ المرشَّحات — فالتقشيرُ لا يُسقط قراءةً مباشرة.
* `candidates_suffix`: كلُّ مرشَّحٍ لاحقةٌ للكلمة (لا يُضاف حرفٌ ولا يُغيَّر) — `isSuffix`.
* `candidates_length_le`: اثنا عشر مرشَّحًا على الأكثر (‎2 × 3 × 2‎).
* `peel_exact`: لكلّ سلسلةٍ مرتّبةٍ من السوابق ولكلّ جذع، الجذعُ بعينه بين المرشَّحات — الاستعادةُ تامّة.
* `fa_not_zawaid`: الفاءُ والباءُ والكافُ ليست من «سألتمونيها» — فالسابقةُ غيرُ الزائد، وتقشيرُها غيرُ تقشير القالب.

## ما لا يُدّعى

أيُّ المرشَّحات يقرؤه الفهرس — هذا قياسٌ لا برهان (`docs/qac/PREREG-2.md`). والباءُ والكافُ والسينُ خارجَ هذه
القائمة لأنّها لا تسبق الماضي ولا الأمر.
-/

set_option autoImplicit false

namespace A116.Sawabiq

/-- فتحة. -/
def fatha : Char := 'َ'

def hamzaQ : List Char := ['أ', fatha]
def waw : List Char := ['و', fatha]
def fa : List Char := ['ف', fatha]
def lam : List Char := ['ل', fatha]

/-- الخاناتُ الثلاث بترتيبها: ما يُقشَّر من كلّ خانة (أو لا شيء). -/
def slot1 : List (List Char) := [[], hamzaQ]
def slot2 : List (List Char) := [[], waw, fa]
def slot3 : List (List Char) := [[], lam]

/-- يُقشَّر `p` إن كان سابقةً للكلمة. -/
def strip (p w : List Char) : Option (List Char) :=
  if p.isPrefixOf w then some (w.drop p.length) else none

/-- مرشَّحاتُ الخانة: لكلّ ما قبلها، ما يُقشَّر منه بكلّ اختيار. -/
def step (opts : List (List Char)) (ws : List (List Char)) : List (List Char) :=
  ws.flatMap fun w => opts.filterMap fun p => strip p w

/-- **المرشَّحات**: الكلمةُ أوّلًا، ثمّ ما يبقى بعد كلّ سلسلةٍ مرتّبة. -/
def candidates (w : List Char) : List (List Char) := step slot3 (step slot2 (step slot1 [w]))

theorem strip_nil (w : List Char) : strip [] w = some w := by simp [strip, List.isPrefixOf]

theorem candidates_head (w : List Char) : (candidates w).head? = some w := by
  simp [candidates, step, slot1, slot2, slot3, strip_nil]

theorem strip_suffix {p w v : List Char} (h : strip p w = some v) : v <:+ w := by
  unfold strip at h
  split at h
  · cases h; exact List.drop_suffix _ _
  · cases h

theorem step_suffix (opts : List (List Char)) (ws : List (List Char)) (w : List Char)
    (hw : ∀ v ∈ ws, v <:+ w) : ∀ v ∈ step opts ws, v <:+ w := by
  intro v hv
  simp only [step, List.mem_flatMap, List.mem_filterMap] at hv
  obtain ⟨u, hu, p, _, hp⟩ := hv
  exact (strip_suffix hp).trans (hw u hu)

/-- **كلُّ مرشَّحٍ لاحقةٌ للكلمة.** -/
theorem candidates_suffix (w : List Char) : ∀ v ∈ candidates w, v <:+ w := by
  unfold candidates
  apply step_suffix; apply step_suffix; apply step_suffix
  intro v hv
  simp at hv
  rw [hv]; exact List.suffix_refl _

theorem step_length_le (opts : List (List Char)) (ws : List (List Char)) :
    (step opts ws).length ≤ opts.length * ws.length := by
  induction ws with
  | nil => simp [step]
  | cons u us ih =>
    simp only [step, List.flatMap_cons, List.length_append] at ih ⊢
    have := List.length_filterMap_le (fun p => strip p u) opts
    rw [List.length_cons, Nat.mul_succ]
    omega

/-- **اثنا عشر مرشَّحًا على الأكثر.** -/
theorem candidates_length_le (w : List Char) : (candidates w).length ≤ 12 := by
  have h1 := step_length_le slot1 [w]
  have h2 := step_length_le slot2 (step slot1 [w])
  have h3 := step_length_le slot3 (step slot2 (step slot1 [w]))
  unfold candidates
  simp only [slot1, slot2, slot3, List.length_cons, List.length_nil] at h1 h2 h3 ⊢
  omega

theorem strip_append (p w : List Char) : strip p (p ++ w) = some w := by
  simp [strip, List.isPrefixOf_iff_prefix]

theorem mem_step {opts : List (List Char)} {ws : List (List Char)} {p w : List Char}
    (hp : p ∈ opts) (hw : p ++ w ∈ ws) : w ∈ step opts ws := by
  simp only [step, List.mem_flatMap, List.mem_filterMap]
  exact ⟨p ++ w, hw, p, hp, strip_append p w⟩

/-- **الاستعادةُ تامّة**: لكلّ سلسلةٍ مرتّبةٍ من السوابق ولكلّ جذع، الجذعُ بين المرشَّحات. -/
theorem peel_exact (a b c stem : List Char) (ha : a ∈ slot1) (hb : b ∈ slot2) (hc : c ∈ slot3) :
    stem ∈ candidates (a ++ (b ++ (c ++ stem))) := by
  unfold candidates
  apply mem_step hc
  apply mem_step hb
  apply mem_step ha
  simp

/-- شاهد: «فَقَالُوا» يُعطي «قَالُوا». -/
theorem fa_qalu : "قَالُوا".toList ∈ candidates "فَقَالُوا".toList := by decide

/-- شاهد: «أَفَلَ…» يُقشَّر سلسلةً تامّة. -/
theorem afala : "قَالَ".toList ∈ candidates ("أَفَلَقَالَ").toList := by decide

/-- **السابقةُ غيرُ الزائد**: الفاءُ والباءُ والكافُ ليست من «سألتمونيها». -/
theorem fa_not_zawaid :
    Zawaid.zawaid.contains 'ف' = false ∧ Zawaid.zawaid.contains 'ب' = false ∧
      Zawaid.zawaid.contains 'ك' = false := by decide

end A116.Sawabiq
