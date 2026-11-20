import A116.Dal
import A116.WadData

/-!
# علاقةُ الوضع مودَعةً، ودَينُ `Dal` بصيغته الصحيحة (ADR ٥٦)

«الوضعُ هو تخصيص لفظ بمعنى» (الشخصيّة ج3 ف393) — **علاقةٌ** بين لفظٍ ومعنى تُنقل (ف397)، لا دالّة. والدالُّ
والمدلولُ سبعةُ أقسامٍ (ف418) لا يتّحد فيها اللفظُ والمعنى إلّا في المنفرد؛ ومنها المشترك: «يكون اللفظ واحداً
والمعنى كثير … وضع لكل واحد من تلك المعاني»، وتعيينُ أحدها «يحتاج إلى قرينة مبينة» (ف423).

فدَينُ «تكافؤ الدالّ والمدلول» (`A116.Dal`) يُعاد صوغُه هنا ويُبرهَن:

* `function_iff_no_mushtarak`: لعلاقةٍ ما دالّةٌ تطابقها (كلُّ لفظٍ ← معناه) **إن وفقط إن** لم يكن فيها لفظٌ بمعنيين.
  فـ«التكافؤ» بمعنى الدالّة مكافئٌ لانعدام الاشتراك، لا أكثر.
* `munfarid_part_function`: والجزءُ الذي ليس فيه اشتراكٌ دالّةٌ دائمًا.
* `qarina_iff`: والتعيينُ بالقرينة: دالّةٌ في (اللفظ، القرينة) تطابق العلاقةَ ⟺ لا لفظَ وقرينةً بمعنيين.
* **على المودَع** (`WadData`، مولَّدٌ من `corpora/wad/wad.tsv`): كلُّ صفٍّ مشتركٌ بجذرين متمايزين فأكثر
  (`mushtarak_rows`)، وفيه «قَ اْ ل» بجذرَي `Dal` نفسيهما (`qala_in_deposit`، `qwl_from_deposit`،
  `qyl_from_deposit`)، فلا دالّةَ من اللفظ إلى الجذر تطابق العلاقةَ المودَعة (`deposit_not_function`).

ما لا يُبرهَن هنا: صدقُ النقل نفسِه (Lean يبرهن المرويَّ لا اللغة، المادّة ١٧)، والمعنى الجزئيّ دون المادّة.
-/

set_option autoImplicit false

namespace A116.Wad

/-- العلاقةُ أزواجُ (لفظ، معنى). -/
abbrev Rel (L M : Type) := List (L × M)

/-- لا لفظَ فيها بمعنيين مختلفين. -/
def NoMushtarak {L M : Type} (w : Rel L M) : Prop :=
  ∀ p ∈ w, ∀ q ∈ w, p.1 = q.1 → p.2 = q.2

/-- دالّةٌ تطابق العلاقة: كلُّ زوجٍ فيها صورةُ لفظه. -/
def Realizes {L M : Type} (w : Rel L M) (f : L → M) : Prop := ∀ p ∈ w, f p.1 = p.2

/-- الدالّةُ المختارةُ من العلاقة: أوّلُ معنًى لِلّفظ، أو الافتراضيّ. -/
def pick {L M : Type} [DecidableEq L] [Inhabited M] (w : Rel L M) (l : L) : M :=
  match w.find? (fun p => decide (p.1 = l)) with
  | some p => p.2
  | none => default

theorem pick_spec {L M : Type} [DecidableEq L] [Inhabited M] (w : Rel L M) (p : L × M) (hp : p ∈ w) :
    ∃ q ∈ w, q.1 = p.1 ∧ pick w p.1 = q.2 := by
  unfold pick
  cases h : w.find? (fun q => decide (q.1 = p.1)) with
  | none =>
    have := List.find?_eq_none.mp h p hp
    simp at this
  | some q =>
    have hq := List.find?_some h
    exact ⟨q, List.mem_of_find?_eq_some h, by simpa using hq, rfl⟩

/-- **التكافؤُ دالّةً ⟺ لا اشتراك.** -/
theorem function_iff_no_mushtarak {L M : Type} [DecidableEq L] [Inhabited M] (w : Rel L M) :
    (∃ f, Realizes w f) ↔ NoMushtarak w := by
  constructor
  · rintro ⟨f, hf⟩ p hp q hq h
    rw [← hf p hp, ← hf q hq, h]
  · intro h
    refine ⟨pick w, fun p hp => ?_⟩
    obtain ⟨q, hq, h1, h2⟩ := pick_spec w p hp
    rw [h2]
    exact h q hq p hp h1

/-- لفظٌ بمعنيين مختلفين في العلاقة يمنع كلَّ دالّة. -/
theorem mushtarak_no_function {L M : Type} (w : Rel L M) (l : L) (a b : M) (ha : (l, a) ∈ w)
    (hb : (l, b) ∈ w) (hab : a ≠ b) : ¬ ∃ f, Realizes w f := by
  rintro ⟨f, hf⟩
  exact hab ((hf _ ha).symm.trans (hf _ hb))

/-- معاني اللفظ في العلاقة. -/
def maanas {L M : Type} [DecidableEq L] (w : Rel L M) (l : L) : List M :=
  (w.filter fun p => decide (p.1 = l)).map (·.2)

theorem mem_maanas {L M : Type} [DecidableEq L] (w : Rel L M) (l : L) (m : M) :
    m ∈ maanas w l ↔ (l, m) ∈ w := by
  unfold maanas
  constructor
  · intro h
    obtain ⟨p, hp, rfl⟩ := List.mem_map.mp h
    have := List.mem_filter.mp hp
    have he : p.1 = l := by simpa using this.2
    have : (l, p.2) = p := by rw [← he]
    rw [this]; exact (List.mem_filter.mp hp).1
  · intro h
    exact List.mem_map.mpr ⟨(l, m), List.mem_filter.mpr ⟨h, by simp⟩, rfl⟩

/-- الجزءُ المنفرد: الأزواجُ التي ليس لِلفظها معنًى غيرُ معناها. -/
def munfaridPart {L M : Type} [DecidableEq L] [DecidableEq M] (w : Rel L M) : Rel L M :=
  w.filter fun p => (maanas w p.1).all (fun m => decide (m = p.2))

/-- **والمنفردُ دالّةٌ دائمًا**، لكلّ علاقة. -/
theorem munfarid_part_function {L M : Type} [DecidableEq L] [DecidableEq M] [Inhabited M]
    (w : Rel L M) : ∃ f, Realizes (munfaridPart w) f := by
  rw [function_iff_no_mushtarak]
  intro p hp q hq h
  have hp' := List.mem_filter.mp hp
  have hq' := (List.mem_filter.mp hq).1
  have hall := List.all_eq_true.mp hp'.2 q.2 ((mem_maanas w p.1 q.2).mpr (by rw [h]; exact hq'))
  exact (of_decide_eq_true hall).symm

/-- **التعيينُ بالقرينة**: دالّةٌ في (اللفظ، القرينة) ⟺ لا لفظَ وقرينةً بمعنيين. -/
theorem qarina_iff {L Q M : Type} [DecidableEq L] [DecidableEq Q] [Inhabited M]
    (w : Rel (L × Q) M) : (∃ f : L × Q → M, Realizes w f) ↔ NoMushtarak w :=
  function_iff_no_mushtarak w

/-! ## على المودَع -/

open A116.WadData A116.Wazn

/-- العلاقةُ المودَعةُ في جزئها المشترك: (اللفظ، الجذر). -/
def mushtarakRel : Rel String String :=
  mushtarak.flatMap fun r => r.2.map fun x => (r.1, x.1)

/-- كلُّ صفٍّ مشتركٌ بجذرين متمايزين فأكثر، وكلُّ زوجٍ رواه لين. -/
theorem mushtarak_rows :
    mushtarak.all (fun r => decide (2 ≤ r.2.length) && (r.2.map (·.1)).Nodup &&
      r.2.all (fun x => x.2.contains "lane")) = true := by decide +kernel

theorem mushtarak_count : mushtarak.length = 382 := by decide +kernel

/-- «قَ اْ ل» في المودَع بجذرين: قول وقيل، كلاهما من رواية لين. -/
theorem qala_in_deposit :
    ("قَ اْ ل", [("قول", ["lane"]), ("قيل", ["lane"])]) ∈ mushtarak := by decide +kernel

/-- الجذرُ نصًّا ← جذرٌ على الحوامل. -/
def ofStr3 (s : String) : Root 3 :=
  Tasrif.r3 (s.toList.getD 0 ' ') (s.toList.getD 1 ' ') (s.toList.getD 2 ' ')

/-- جذرا `Dal` هما جذرا المودَع بأعيانهما. -/
theorem qwl_from_deposit : ofStr3 "قول" = Dal.qwl := by
  funext i; revert i; decide

theorem qyl_from_deposit : ofStr3 "قيل" = Dal.qyl := by
  funext i; revert i; decide

/-- **دَينُ `Dal` بصيغته الصحيحة على المودَع**: لا دالّةَ من اللفظ إلى الجذر تطابق علاقةَ الوضع المودَعة —
لأنّ فيها مشتركًا (قَالَ)، لا لأنّ «التكافؤ» فات. -/
theorem deposit_not_function : ¬ ∃ f, Realizes mushtarakRel f :=
  mushtarak_no_function mushtarakRel "قَ اْ ل" "قول" "قيل" (by decide +kernel) (by decide +kernel)
    (by decide)

end A116.Wad
