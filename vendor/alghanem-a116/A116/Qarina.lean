import A116.Wad
import A116.Tayy
import A116.QarinaData

/-!
# القرينةُ المبيِّنة من «المخصَّص»: خطوةُ الوضع طيٌّ ببقيّة القرينة (ADR ٥٩)

«استعمال اللفظ المشترك في أحد معانيه دون غيره … يحتاج إلى قرينة مبينة تعيِّن المعنى المراد» (الشخصيّة ج3 ف423).
و`Tayy.wad_step_needs_residue` برهن أنّ خطوةَ الوضع على قَالَ تحتاج بقيّةً تفصل قول من قيل، وأنّها ليست في
الخانات. وهنا تُعطى تلك البقيّة: **حقلُ المعنى** عُقَدُ «المخصَّص» لابن سيده التي ورد فيها الجذر (`QarinaData`)،
و**القرينةُ المبيِّنة** لمعنًى من معاني اللفظ عقدةٌ في حقله وليست في حقل معنًى آخر له (`Mub`).

## لكلّ معانٍ ولكلّ حقول

* `mub_unique`: لا قرينةَ مبيِّنةٌ لمعنيين — فالتعيينُ بها لا يخطئ بين المعاني المرويّة.
* `sep_iff`: للمعنى قرينةٌ مبيِّنة ⟺ في حقله عقدةٌ ليست في حقول أخواته؛ و`covered_no_mub`: ما حقلُه داخلَ
  حقول أخواته لا تعيّنه قرينةٌ أبدًا (حدٌّ مسمًّى، لا عجزُ آلة).
* `choose_sound`، `choose_conflict`، `choose_complete`: الاختيارُ بالسياق (قرائنُ حاضرة) يُرجع معنًى له فيها
  قرينةٌ مبيِّنة، ويرفض إن بيّنت القرائنُ معنيين، ويُرجعه إن بيّنته وحده.
* `wadTayy`: **خطوةُ الوضع طيٌّ** (`Tayy.Tayy`) على علاقة الوضع: الصورةُ اللفظ، والبقيّةُ القرينةُ المبيِّنة،
  والاسترجاعُ يردّ (اللفظ، المعنى) بعينه على كلّ زوجٍ له قرينةٌ مبيِّنة.

## على المودَع

* `rows_are_wad`: صفوفُ القرينة هي ألفاظُ المشترك في `WadData` بمعانيها وترتيبها؛ و`qala_maanas`: معاني قَالَ
  في صفّه هي معانيه في العلاقة نفسِها.
* قَالَ: عقدةُ «كثرة الكلام والخطأ فيه» (135) تبيّن قول، وعقدةُ «النوم» (479) تبيّن قيل (`qala_kalam`، `qala_nawm`)،
  والاختيارُ بهما (`qala_choose`)، وزوجا قَالَ في مجال الطيّ (`qala_tayy_dom`).
* الأعداد: 782 زوجًا، 566 لها حقل، 558 لها قرينةٌ مبيِّنة؛ و207 ألفاظٍ كلُّ معانيها لها حقل، 199 كلُّ معانيها
  تتعيّن؛ والثمانيةُ الباقيةُ (طوب داخل طيب، فيق داخل فوق) بأعيانها (`covered_not_separable`).

ما لا يُبرهَن: أنّ العضويّةَ «وُضع له» لا «ذُكر فيه» (`MENTIONED_NOT_POSITED`)، ولا صدقُ النقل (المادّة ١٧).
-/

set_option autoImplicit false
set_option linter.unusedSectionVars false

namespace A116.Qarina

section General

variable {M Q : Type} [DecidableEq M] [DecidableEq Q]

/-- **القرينةُ المبيِّنة**: `q` في حقل `m` من معاني `ms`، ولا في حقل معنًى غيرِه منها. -/
def Mub (ms : List M) (F : M → List Q) (q : Q) (m : M) : Prop :=
  m ∈ ms ∧ q ∈ F m ∧ ∀ m' ∈ ms, q ∈ F m' → m' = m

def mubB (ms : List M) (F : M → List Q) (q : Q) (m : M) : Bool :=
  ms.contains m && (F m).contains q && ms.all (fun m' => !((F m').contains q) || m' == m)

theorem mubB_iff (ms : List M) (F : M → List Q) (q : Q) (m : M) :
    mubB ms F q m = true ↔ Mub ms F q m := by
  simp only [mubB, Mub, Bool.and_eq_true, List.contains_iff_mem, List.all_eq_true,
    Bool.or_eq_true, Bool.not_eq_true', beq_iff_eq]
  constructor
  · rintro ⟨⟨h1, h2⟩, h3⟩
    refine ⟨h1, h2, fun m' hm' hq => ?_⟩
    rcases h3 m' hm' with h | h
    · have : (F m').contains q = true := List.contains_iff_mem.mpr hq
      rw [this] at h; exact absurd h (by decide)
    · exact h
  · rintro ⟨h1, h2, h3⟩
    refine ⟨⟨h1, h2⟩, fun m' hm' => ?_⟩
    by_cases hq : q ∈ F m'
    · exact Or.inr (h3 m' hm' hq)
    · left
      cases hc : (F m').contains q
      · rfl
      · exact absurd (List.contains_iff_mem.mp hc) hq

instance (ms : List M) (F : M → List Q) (q : Q) (m : M) : Decidable (Mub ms F q m) :=
  decidable_of_iff _ (mubB_iff ms F q m)

/-- **لا قرينةَ مبيِّنةٌ لمعنيين.** -/
theorem mub_unique {ms : List M} {F : M → List Q} {q : Q} {m₁ m₂ : M}
    (h₁ : Mub ms F q m₁) (h₂ : Mub ms F q m₂) : m₁ = m₂ :=
  (h₁.2.2 m₂ h₂.1 h₂.2.1).symm

/-- للمعنى قرينةٌ مبيِّنة (بحسابٍ يُقرَّر). -/
def sepB (ms : List M) (F : M → List Q) (m : M) : Bool := (F m).any fun q => mubB ms F q m

theorem sep_iff (ms : List M) (F : M → List Q) (m : M) :
    sepB ms F m = true ↔ ∃ q, Mub ms F q m := by
  simp only [sepB, List.any_eq_true, mubB_iff]
  constructor
  · rintro ⟨q, _, h⟩; exact ⟨q, h⟩
  · rintro ⟨q, h⟩; exact ⟨q, h.2.1, h⟩

/-- **ما حقلُه داخلَ حقول أخواته لا تعيّنه قرينة.** -/
theorem covered_no_mub {ms : List M} {F : M → List Q} {m : M}
    (h : ∀ q ∈ F m, ∃ m' ∈ ms, m' ≠ m ∧ q ∈ F m') : ¬ ∃ q, Mub ms F q m := by
  rintro ⟨q, hm⟩
  obtain ⟨m', hm', hne, hq⟩ := h q hm.2.1
  exact hne (hm.2.2 m' hm' hq)

/-- المعاني التي تبيّنها قرينةٌ حاضرة في السياق `C`. -/
def hits (ms : List M) (F : M → List Q) (C : List Q) : List M :=
  ms.filter fun m => C.any fun q => mubB ms F q m

/-- **الاختيار**: معنًى واحدٌ تبيّنه القرائنُ الحاضرة، وإلّا لا شيء (لا قرينة، أو تعارض). -/
def choose (ms : List M) (F : M → List Q) (C : List Q) : Option M :=
  match hits ms F C with
  | [] => none
  | m :: rest => if rest.all (· == m) then some m else none

theorem mem_hits {ms : List M} {F : M → List Q} {C : List Q} {m : M} :
    m ∈ hits ms F C ↔ ∃ q ∈ C, Mub ms F q m := by
  simp only [hits, List.mem_filter, List.any_eq_true, mubB_iff]
  constructor
  · rintro ⟨_, q, hq, h⟩; exact ⟨q, hq, h⟩
  · rintro ⟨q, hq, h⟩; exact ⟨h.1, q, hq, h⟩

/-- كلُّ ما في المختار واحد: إن أرجع `choose` معنًى فكلُّ ما بيّنته القرائنُ هو. -/
theorem choose_all {ms : List M} {F : M → List Q} {C : List Q} {m : M}
    (h : choose ms F C = some m) : m ∈ hits ms F C ∧ ∀ x ∈ hits ms F C, x = m := by
  unfold choose at h
  split at h
  · exact absurd h (by simp)
  · rename_i a rest heq
    by_cases hr : rest.all (· == a) = true
    · simp only [hr, ↓reduceIte] at h
      cases h
      refine ⟨by rw [heq]; exact List.mem_cons_self .., fun x hx => ?_⟩
      rw [heq] at hx
      rcases List.mem_cons.mp hx with e | hx
      · exact e
      · exact beq_iff_eq.mp (List.all_eq_true.mp hr x hx)
    · simp only [hr] at h; exact absurd h (by simp)

/-- **الاختيارُ صادق**: ما يُرجعه له قرينةٌ مبيِّنةٌ حاضرة. -/
theorem choose_sound {ms : List M} {F : M → List Q} {C : List Q} {m : M}
    (h : choose ms F C = some m) : ∃ q ∈ C, Mub ms F q m :=
  mem_hits.mp (choose_all h).1

/-- **ويرفض التعارض**: معنيان مختلفان تبيّنهما قرائنُ حاضرة ⇒ لا اختيار. -/
theorem choose_conflict {ms : List M} {F : M → List Q} {C : List Q} {m₁ m₂ : M}
    (h₁ : ∃ q ∈ C, Mub ms F q m₁) (h₂ : ∃ q ∈ C, Mub ms F q m₂) (hne : m₁ ≠ m₂) :
    choose ms F C = none := by
  cases hc : choose ms F C with
  | none => rfl
  | some m =>
    have hall := (choose_all hc).2
    exact absurd ((hall _ (mem_hits.mpr h₁)).trans (hall _ (mem_hits.mpr h₂)).symm) hne

/-- **ويُرجع ما بيّنته القرائنُ وحده.** -/
theorem choose_complete {ms : List M} {F : M → List Q} {C : List Q} {m : M}
    (h : ∃ q ∈ C, Mub ms F q m) (honly : ∀ m', (∃ q ∈ C, Mub ms F q m') → m' = m) :
    choose ms F C = some m := by
  have hm : m ∈ hits ms F C := mem_hits.mpr h
  have hall : ∀ x ∈ hits ms F C, x = m := fun x hx => honly x (mem_hits.mp hx)
  unfold choose
  split
  · rename_i heq; rw [heq] at hm; exact absurd hm (by simp)
  · rename_i a rest heq
    have ha : a = m := hall a (by rw [heq]; exact List.mem_cons_self ..)
    subst ha
    have hr : rest.all (· == a) = true :=
      List.all_eq_true.mpr fun x hx =>
        beq_iff_eq.mpr (hall x (by rw [heq]; exact List.mem_cons_of_mem _ hx))
    simp only [hr, ↓reduceIte]

end General

section Tayy

variable {L M Q : Type} [DecidableEq L] [DecidableEq M] [DecidableEq Q] [Inhabited M]

/-- **خطوةُ الوضع طيٌّ ببقيّة القرينة**: من (اللفظ، المعنى) إلى اللفظ، والبقيّةُ قرينةٌ مبيِّنة من حقل المعنى؛
والاسترجاعُ المعنى الوحيدُ الذي تبيّنه تلك القرينةُ بين معاني اللفظ. مجالُه الأزواجُ التي لها قرينةٌ مبيِّنة. -/
def wadTayy (w : Wad.Rel L M) (F : M → List Q) : Tayy.Tayy (L × M) L (Option Q) where
  dom p := ∃ q, Mub (Wad.maanas w p.1) F q p.2
  fold p := (p.1, (F p.2).find? fun q => mubB (Wad.maanas w p.1) F q p.2)
  unfold c := match c.2 with
    | none => none
    | some q => ((Wad.maanas w c.1).find? fun m => mubB (Wad.maanas w c.1) F q m).map (c.1, ·)
  law p h := by
    obtain ⟨l, m⟩ := p
    obtain ⟨q₀, hq₀⟩ := h
    have hsome : ((F m).find? fun q => mubB (Wad.maanas w l) F q m).isSome := by
      rw [List.find?_isSome]; exact ⟨q₀, hq₀.2.1, (mubB_iff ..).mpr hq₀⟩
    obtain ⟨q, hq⟩ := Option.isSome_iff_exists.mp hsome
    have hmq : Mub (Wad.maanas w l) F q m :=
      (mubB_iff ..).mp (List.find?_some (p := fun q => mubB (Wad.maanas w l) F q m) hq)
    have hsome2 : ((Wad.maanas w l).find? fun m' => mubB (Wad.maanas w l) F q m').isSome := by
      rw [List.find?_isSome]; exact ⟨m, hmq.1, (mubB_iff ..).mpr hmq⟩
    obtain ⟨m', hm'⟩ := Option.isSome_iff_exists.mp hsome2
    have hm'q : Mub (Wad.maanas w l) F q m' :=
      (mubB_iff ..).mp (List.find?_some (p := fun m' => mubB (Wad.maanas w l) F q m') hm')
    have e : m' = m := mub_unique hm'q hmq
    show (match ((F m).find? fun q => mubB (Wad.maanas w l) F q m) with
      | none => none
      | some q => ((Wad.maanas w l).find? fun m' => mubB (Wad.maanas w l) F q m').map (l, ·)) =
        some (l, m)
    rw [hq]
    simp only [hm', e, Option.map_some]

/-- كلُّ زوجٍ في المجال يُستردّ بعينه من اللفظ والقرينة. -/
theorem wadTayy_law (w : Wad.Rel L M) (F : M → List Q) (p : L × M)
    (h : ∃ q, Mub (Wad.maanas w p.1) F q p.2) :
    (wadTayy w F).unfold ((wadTayy w F).fold p) = some p :=
  (wadTayy w F).law p h

end Tayy

/-! ## على المودَع -/

open A116.WadData A116.QarinaData

abbrev Row := String × List (String × List Nat)

/-- حقلُ المعنى في صفّه. -/
def rowF (r : Row) (m : String) : List Nat :=
  match r.2.find? (fun p => p.1 == m) with
  | some p => p.2
  | none => []

/-- معاني اللفظ في صفّه. -/
def ms (r : Row) : List String := r.2.map (·.1)

/-- صفوفُ القرينة هي ألفاظُ المشترك في `WadData` بمعانيها، بترتيبها. -/
theorem rows_are_wad : rows.map (fun r => (r.1, ms r)) = mushtarak.map (fun r => (r.1, r.2.map (·.1))) := by
  decide +kernel

/-- صفُّ قَالَ. -/
def qala : Row := (rows.find? (fun r => r.1 == "قَ اْ ل")).getD ("", [])

theorem qala_ms : qala.1 = "قَ اْ ل" ∧ ms qala = ["قول", "قيل"] := by decide +kernel

/-- ومعاني قَالَ في صفّه هي معانيه في علاقة الوضع المودَعة. -/
theorem qala_maanas : Wad.maanas Wad.mushtarakRel "قَ اْ ل" = ms qala := by decide +kernel

/-- «كثرةُ الكلام والخطأ فيه» (العقدة 135) قرينةٌ مبيِّنةٌ لقول. -/
theorem qala_kalam : Mub (ms qala) (rowF qala) 135 "قول" := by decide +kernel

/-- «النوم» (العقدة 479) قرينةٌ مبيِّنةٌ لقيل. -/
theorem qala_nawm : Mub (ms qala) (rowF qala) 479 "قيل" := by decide +kernel

theorem qala_choose :
    choose (ms qala) (rowF qala) [135] = some "قول" ∧ choose (ms qala) (rowF qala) [479] = some "قيل" ∧
      choose (ms qala) (rowF qala) [135, 479] = none := by decide +kernel

/-- زوجا قَالَ في مجال طيّ الوضع على العلاقة المودَعة بحقلَي صفّه: يُستردّان من اللفظ والقرينة. -/
theorem qala_tayy_dom :
    (wadTayy Wad.mushtarakRel (rowF qala)).dom ("قَ اْ ل", "قول") ∧
      (wadTayy Wad.mushtarakRel (rowF qala)).dom ("قَ اْ ل", "قيل") := by
  refine ⟨⟨135, ?_⟩, ⟨479, ?_⟩⟩
  · show Mub (Wad.maanas Wad.mushtarakRel "قَ اْ ل") (rowF qala) 135 "قول"
    rw [qala_maanas]; exact qala_kalam
  · show Mub (Wad.maanas Wad.mushtarakRel "قَ اْ ل") (rowF qala) 479 "قيل"
    rw [qala_maanas]; exact qala_nawm

/-- أزواجُ المشترك: (الصفّ، معنًى منه). -/
def pairsAll : List (Row × String) := rows.flatMap fun r => (ms r).map fun m => (r, m)

theorem pair_count : pairsAll.length = 782 := by decide +kernel

theorem covered_count : (pairsAll.filter fun p => !(rowF p.1 p.2).isEmpty).length = 566 := by
  decide +kernel

theorem separable_count : (pairsAll.filter fun p => sepB (ms p.1) (rowF p.1) p.2).length = 558 := by
  decide +kernel

theorem lafz_covered_count : (rows.filter fun r => (ms r).all fun m => !(rowF r m).isEmpty).length = 207 := by
  decide +kernel

theorem lafz_separable_count : (rows.filter fun r => (ms r).all (sepB (ms r) (rowF r))).length = 199 := by
  decide +kernel

/-- ما له حقلٌ ولا تعيّنه قرينة: ثمانيةُ أزواجٍ بأعيانها (حقلُ طوب داخل حقل طيب، وفيق داخل فوق). -/
theorem covered_not_separable :
    ((pairsAll.filter fun p => !(rowF p.1 p.2).isEmpty && !sepB (ms p.1) (rowF p.1) p.2).map
        fun p => (p.1.1, p.2)) =
      [("طُ وْ ب", "طوب"), ("طُ وْ بَ ا", "طوب"), ("فَ اْ ق", "فيق"), ("فَ يْ قَ ت", "فيق"),
        ("فُ يَ اْ ق", "فيق"), ("فُ يُ ق", "فيق"), ("فِ يْ ق", "فيق"), ("مُ فِ يْ ق", "فيق")] := by
  decide +kernel

end A116.Qarina
