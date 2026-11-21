/-!
# الاشتقاقُ الأصغر — شقُّه الصوريّ مبرهَنًا

ابن جني (الخصائص، باب في الاشتقاق الأكبر): الأصغر «أن تأخذ أصلًا من الأصول فتتقرّاه،
فتجمع بين معانيه وإن اختلفت صيغه ومبانيه». في الدعوى شقّان:

* **صوريّ:** الصيغُ مبنيّةٌ من الأصل بحروفه وترتيبه، والأصلُ يُستردّ منها.
* **دلاليّ:** المعنى مشتركٌ بينها. وهذا لا يُبرهَن هنا: خريطةُ «المقاييس» تعطي الأصلَ
  أصولَه بالتعريف، فقياسُه عليها دائر.

وهذا الملفّ يبرهن الشقَّ الصوريّ **لكلّ أصلٍ ولكلّ قالبٍ سليم**، لا على مدوّنةٍ منتهية:

* `extract_fill`: الاستخراجُ بالقالب يعيد الأصلَ بعينه (`(slots t).map r`).
* `root_sublist_fill`: حروفُ الأصل تظهر في الصيغة بترتيبها (`Sublist`).
* `fill_injective`: القالبُ الواحدُ متباينٌ على الأصول.
* `soundTemplates_wf`: قوالبُ `mabni_verbs.SOUND_TEMPLATES` الإحدى والثلاثون كلُّها سليمة.

**وحدُّه مبرهَنٌ أيضًا** (`form_alone_does_not_determine_root`): الصيغةُ **وحدَها** لا تعيّن
الأصل، لأنّ حروفَ القالب من جنس حروف الأصل: انْتَبَرَ = انفعل(ت ب ر) = افتعل(ن ب ر).
فالاسترداد مشروطٌ بالوزن، وهذا هو موضعُ الميزان الصرفيّ في الأصغر.
-/

namespace A116.Ishtiqaq

/-- رمزُ القالب: حرفٌ زائدٌ أو علامة (`lit`)، أو خانةُ أصلٍ (`slot`). -/
inductive Sym (α : Type) where
  | lit : α → Sym α
  | slot : Fin 3 → Sym α
  deriving DecidableEq, Repr

abbrev Template (α : Type) := List (Sym α)

/-- الأصلُ الثلاثيّ: لكلّ خانةٍ حرف. -/
abbrev Root (α : Type) := Fin 3 → α

def fillSym {α : Type} (r : Root α) : Sym α → α
  | .lit c => c
  | .slot i => r i

/-- بناءُ الصيغة: تُملأ الخاناتُ بحروف الأصل، ويبقى الزائدُ كما هو. -/
def fill {α : Type} (t : Template α) (r : Root α) : List α := t.map (fillSym r)

/-- خاناتُ القالب بترتيبها. -/
def slots {α : Type} : Template α → List (Fin 3)
  | [] => []
  | .lit _ :: t => slots t
  | .slot i :: t => i :: slots t

/-- القالبُ السليم: خاناتُه الثلاثُ مرّةً مرّةً، بترتيب الفاء فالعين فاللام. -/
def WF {α : Type} (t : Template α) : Prop := slots t = [0, 1, 2]

instance {α : Type} (t : Template α) : Decidable (WF t) :=
  inferInstanceAs (Decidable (slots t = [0, 1, 2]))

/-- الاستخراجُ بالقالب: ما وقع من الصيغة في موضع خانة. -/
def extract {α : Type} : Template α → List α → List α
  | [], _ => []
  | _, [] => []
  | .lit _ :: t, _ :: w => extract t w
  | .slot _ :: t, c :: w => c :: extract t w

theorem extract_fill {α : Type} (t : Template α) (r : Root α) :
    extract t (fill t r) = (slots t).map r := by
  induction t with
  | nil => rfl
  | cons s t ih =>
    cases s with
    | lit c => simpa [fill, fillSym, extract, slots] using ih
    | slot i => simpa [fill, fillSym, extract, slots] using ih

theorem extract_fill_wf {α : Type} {t : Template α} (h : WF t) (r : Root α) :
    extract t (fill t r) = [r 0, r 1, r 2] := by
  rw [extract_fill, h]; rfl

theorem root_sublist_fill {α : Type} (t : Template α) (r : Root α) :
    List.Sublist ((slots t).map r) (fill t r) := by
  induction t with
  | nil => exact List.Sublist.slnil
  | cons s t ih =>
    cases s with
    | lit c => simpa [fill, fillSym, slots] using List.Sublist.cons c ih
    | slot i => simpa [fill, fillSym, slots] using List.Sublist.cons_cons (r i) ih

theorem root_sublist_fill_wf {α : Type} {t : Template α} (h : WF t) (r : Root α) :
    List.Sublist [r 0, r 1, r 2] (fill t r) := by
  have := root_sublist_fill t r
  rw [h] at this
  simpa using this

theorem fill_injective {α : Type} {t : Template α} (h : WF t) {r r' : Root α}
    (e : fill t r = fill t r') : r = r' := by
  have k := extract_fill_wf h r
  rw [e, extract_fill_wf h r'] at k
  simp only [List.cons.injEq] at k
  funext i
  match i with
  | ⟨0, _⟩ => exact k.1.symm
  | ⟨1, _⟩ => exact k.2.1.symm
  | ⟨2, _⟩ => exact k.2.2.1.symm

/-! ## قوالبُ `mabni_verbs.SOUND_TEMPLATES` (مولَّدةٌ منها حرفًا بحرف) -/

/-- `I-a` PAST: `1َ2َ3` -/
def t_past_I_a : Template Char := [.slot 0, .lit 'َ', .slot 1, .lit 'َ', .slot 2]

/-- `I-i` PAST: `1َ2ِ3` -/
def t_past_I_i : Template Char := [.slot 0, .lit 'َ', .slot 1, .lit 'ِ', .slot 2]

/-- `I-u` PAST: `1َ2ُ3` -/
def t_past_I_u : Template Char := [.slot 0, .lit 'َ', .slot 1, .lit 'ُ', .slot 2]

/-- `II` PAST: `1َ2َّ3` -/
def t_past_II : Template Char := [.slot 0, .lit 'َ', .slot 1, .lit 'ّ', .lit 'َ', .slot 2]

/-- `III` PAST: `1َا2َ3` -/
def t_past_III : Template Char := [.slot 0, .lit 'َ', .lit 'ا', .slot 1, .lit 'َ', .slot 2]

/-- `IV` PAST: `ءَ1ْ2َ3` -/
def t_past_IV : Template Char := [.lit 'ء', .lit 'َ', .slot 0, .lit 'ْ', .slot 1, .lit 'َ', .slot 2]

/-- `V` PAST: `تَ1َ2َّ3` -/
def t_past_V : Template Char := [.lit 'ت', .lit 'َ', .slot 0, .lit 'َ', .slot 1, .lit 'ّ', .lit 'َ', .slot 2]

/-- `VI` PAST: `تَ1َا2َ3` -/
def t_past_VI : Template Char := [.lit 'ت', .lit 'َ', .slot 0, .lit 'َ', .lit 'ا', .slot 1, .lit 'َ', .slot 2]

/-- `VII` PAST: `انْ1َ2َ3` -/
def t_past_VII : Template Char := [.lit 'ا', .lit 'ن', .lit 'ْ', .slot 0, .lit 'َ', .slot 1, .lit 'َ', .slot 2]

/-- `VIII` PAST: `ا1ْتَ2َ3` -/
def t_past_VIII : Template Char := [.lit 'ا', .slot 0, .lit 'ْ', .lit 'ت', .lit 'َ', .slot 1, .lit 'َ', .slot 2]

/-- `X` PAST: `اسْتَ1ْ2َ3` -/
def t_past_X : Template Char := [.lit 'ا', .lit 'س', .lit 'ْ', .lit 'ت', .lit 'َ', .slot 0, .lit 'ْ', .slot 1, .lit 'َ', .slot 2]

/-- `I` PASSIVE: `1ُ2ِ3` -/
def t_passive_I : Template Char := [.slot 0, .lit 'ُ', .slot 1, .lit 'ِ', .slot 2]

/-- `II` PASSIVE: `1ُ2ِّ3` -/
def t_passive_II : Template Char := [.slot 0, .lit 'ُ', .slot 1, .lit 'ّ', .lit 'ِ', .slot 2]

/-- `III` PASSIVE: `1ُو2ِ3` -/
def t_passive_III : Template Char := [.slot 0, .lit 'ُ', .lit 'و', .slot 1, .lit 'ِ', .slot 2]

/-- `IV` PASSIVE: `ءُ1ْ2ِ3` -/
def t_passive_IV : Template Char := [.lit 'ء', .lit 'ُ', .slot 0, .lit 'ْ', .slot 1, .lit 'ِ', .slot 2]

/-- `V` PASSIVE: `تُ1ُ2ِّ3` -/
def t_passive_V : Template Char := [.lit 'ت', .lit 'ُ', .slot 0, .lit 'ُ', .slot 1, .lit 'ّ', .lit 'ِ', .slot 2]

/-- `VI` PASSIVE: `تُ1ُو2ِ3` -/
def t_passive_VI : Template Char := [.lit 'ت', .lit 'ُ', .slot 0, .lit 'ُ', .lit 'و', .slot 1, .lit 'ِ', .slot 2]

/-- `VII` PASSIVE: `انْ1ُ2ِ3` -/
def t_passive_VII : Template Char := [.lit 'ا', .lit 'ن', .lit 'ْ', .slot 0, .lit 'ُ', .slot 1, .lit 'ِ', .slot 2]

/-- `VIII` PASSIVE: `ا1ْتُ2ِ3` -/
def t_passive_VIII : Template Char := [.lit 'ا', .slot 0, .lit 'ْ', .lit 'ت', .lit 'ُ', .slot 1, .lit 'ِ', .slot 2]

/-- `X` PASSIVE: `اسْتُ1ْ2ِ3` -/
def t_passive_X : Template Char := [.lit 'ا', .lit 'س', .lit 'ْ', .lit 'ت', .lit 'ُ', .slot 0, .lit 'ْ', .slot 1, .lit 'ِ', .slot 2]

/-- `I-a` IMPERATIVE: `ا1ْ2َ3` -/
def t_imperative_I_a : Template Char := [.lit 'ا', .slot 0, .lit 'ْ', .slot 1, .lit 'َ', .slot 2]

/-- `I-i` IMPERATIVE: `ا1ْ2ِ3` -/
def t_imperative_I_i : Template Char := [.lit 'ا', .slot 0, .lit 'ْ', .slot 1, .lit 'ِ', .slot 2]

/-- `I-u` IMPERATIVE: `ا1ْ2ُ3` -/
def t_imperative_I_u : Template Char := [.lit 'ا', .slot 0, .lit 'ْ', .slot 1, .lit 'ُ', .slot 2]

/-- `II` IMPERATIVE: `1َ2ِّ3` -/
def t_imperative_II : Template Char := [.slot 0, .lit 'َ', .slot 1, .lit 'ّ', .lit 'ِ', .slot 2]

/-- `III` IMPERATIVE: `1َا2ِ3` -/
def t_imperative_III : Template Char := [.slot 0, .lit 'َ', .lit 'ا', .slot 1, .lit 'ِ', .slot 2]

/-- `IV` IMPERATIVE: `ءَ1ْ2ِ3` -/
def t_imperative_IV : Template Char := [.lit 'ء', .lit 'َ', .slot 0, .lit 'ْ', .slot 1, .lit 'ِ', .slot 2]

/-- `V` IMPERATIVE: `تَ1َ2َّ3` -/
def t_imperative_V : Template Char := [.lit 'ت', .lit 'َ', .slot 0, .lit 'َ', .slot 1, .lit 'ّ', .lit 'َ', .slot 2]

/-- `VI` IMPERATIVE: `تَ1َا2َ3` -/
def t_imperative_VI : Template Char := [.lit 'ت', .lit 'َ', .slot 0, .lit 'َ', .lit 'ا', .slot 1, .lit 'َ', .slot 2]

/-- `VII` IMPERATIVE: `انْ1َ2ِ3` -/
def t_imperative_VII : Template Char := [.lit 'ا', .lit 'ن', .lit 'ْ', .slot 0, .lit 'َ', .slot 1, .lit 'ِ', .slot 2]

/-- `VIII` IMPERATIVE: `ا1ْتَ2ِ3` -/
def t_imperative_VIII : Template Char := [.lit 'ا', .slot 0, .lit 'ْ', .lit 'ت', .lit 'َ', .slot 1, .lit 'ِ', .slot 2]

/-- `X` IMPERATIVE: `اسْتَ1ْ2ِ3` -/
def t_imperative_X : Template Char := [.lit 'ا', .lit 'س', .lit 'ْ', .lit 'ت', .lit 'َ', .slot 0, .lit 'ْ', .slot 1, .lit 'ِ', .slot 2]

/-- قوالبُ `SOUND_TEMPLATES` كلُّها، بترتيبها في `mabni_verbs`. -/
def soundTemplates : List (Template Char) :=
  [t_past_I_a, t_past_I_i, t_past_I_u, t_past_II, t_past_III, t_past_IV, t_past_V, t_past_VI, t_past_VII, t_past_VIII, t_past_X, t_passive_I, t_passive_II, t_passive_III, t_passive_IV, t_passive_V, t_passive_VI, t_passive_VII, t_passive_VIII, t_passive_X, t_imperative_I_a, t_imperative_I_i, t_imperative_I_u, t_imperative_II, t_imperative_III, t_imperative_IV, t_imperative_V, t_imperative_VI, t_imperative_VII, t_imperative_VIII, t_imperative_X]

theorem soundTemplates_length : soundTemplates.length = 31 := by decide

theorem soundTemplates_wf : ∀ t ∈ soundTemplates, WF t := by decide

/-! ## الحدّ: الصيغةُ وحدَها لا تعيّن الأصل -/

/-- الأصلُ من ثلاثة حروف. -/
def root3 {α : Type} (a b c : α) : Root α
  | ⟨0, _⟩ => a
  | ⟨1, _⟩ => b
  | _ => c

def rootTBR : Root Char := root3 'ت' 'ب' 'ر'
def rootNBR : Root Char := root3 'ن' 'ب' 'ر'

/-- انْتَبَرَ: انفعل من (ت ب ر) وافتعل من (ن ب ر) صيغةٌ واحدة. -/
theorem form_alone_does_not_determine_root :
    fill t_past_VII rootTBR = fill t_past_VIII rootNBR ∧ rootTBR ≠ rootNBR := by
  refine ⟨by rfl, ?_⟩
  intro h
  have : rootTBR 0 = rootNBR 0 := congrFun h 0
  exact absurd this (by decide)

end A116.Ishtiqaq
