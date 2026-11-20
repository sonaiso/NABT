import A116.NizamLine

/-!
# التركيبُ وإعادةُ التدوير: الإسنادُ على كلماتٍ مولَّدة، بلا خانةٍ جديدة (ADR ٦٩، أمرُ المالك)

`COMPOSITION_RECYCLING`: الدرجةُ الأعلى (التركيب) لا تحوي إلّا ما صُنع من الدرجة الأدنى (الكلمات) بعلاقةٍ
معدودة. مرساتُه الكتابُ المختوم (باب المسند والمسند إليه، س234–240):

* س235: «وهما ما لا يغني واحدٌ منهما عن الآخر ولا يجد المتكلّم منه بدًّا» — الإسنادُ **اثنان** لا يستغني
  أحدُهما عن الآخر: الحدُّ الأدنى المكتمل للتركيب كلمتان (`isnad_needs_two`)، نظيرُ `Hajah.minimal_complete`.
* س236: «فمن ذلك الاسمُ المبتدأ والمبنيُّ عليه: عبد الله أخوك» — الجملةُ الاسميّة: اسمٌ على اسم (`ismiyya`).
* س237: «يذهب عبد الله، فلا بدّ للفعل من الاسم» — الجملةُ الفعليّة: فعلٌ على اسم (`filiyya`)؛ ولا إسنادَ
  إلى فعل: المسندُ إليه اسمٌ أبدًا (`musnad_ilayh_is_ism`).
* س238–239: «كان عبد الله منطلقًا … يحتاج إلى ما بعده كاحتياج المبتدأ إلى ما بعده» — الاحتياجُ بين الكلمتين
  لا داخل الواحدة.
* س240: «الاسمُ أوّلُ أحواله الابتداء» (`ism_first_state`).

## ما يُبرهَن

1. **إعادةُ التدوير**: خاناتُ التركيب هي خاناتُ كلماته لا غير (`cells_recycled`)، وترخيصُ التركيب هو
   ترخيصُ السطر (`NizamLine.strictLineB`) على كلماته (`tarkibB_eq_line`) — فلا قانونَ جديدًا عند التركيب،
   والجامعُ `NizamLine.strictLineB_is_nizam` يبقى هو الحاكم.
2. **القسمُ معاملٌ لا خانة**: الترخيصُ لا يرى القسم (`licence_blind_to_qism`) — فالإسنادُ طبقةٌ فوق الدالّ،
   يُقرأ القسمُ من `A116.Qism` أو من مرجعٍ محجوب ويُعطى هنا مدخلًا (`TARKIB_QISM_IS_INPUT`).
3. **الإسناد**: الحدُّ الأدنى كلمتان (`isnad_needs_two`)، والحروفُ وحدَها لا تُسند (`huruf_no_isnad`)،
   وشبهُ الجملة (حرفٌ واسم) لا إسنادَ فيه (`shibh_no_isnad`)، والمسندُ إليه اسمٌ (`musnad_ilayh_is_ism`).
4. **الإغلاق بالربط**: إسنادٌ يبقى إسنادًا بما يُضاف قبله أو بعده (`isnad_mono_left`، `isnad_mono_right`)،
   فجملةٌ معطوفةٌ على جملةٍ بحرفٍ بينهما إسنادان (`atf_two_isnad`) — الجبرُ مغلقٌ على التركيب.

ما لا يُبرهَن هنا: أنّ هذا هو إسنادُ العربيّة (ذلك مرويُّ الكتاب بموضعه)؛ والإسنادُ هنا **بين متجاورين**
(`ISNAD_ADJACENT_ONLY`) — الفصلُ بين المسند والمسند إليه دَينٌ مسمًّى.
-/

namespace A116.Tarkib

open A116 A116.Hadd A116.NizamLine

/-- أقسامُ الكلم الثلاثة (الكتاب س234–240: اسمٌ وفعلٌ وحرف). -/
inductive Qism where
  | ism | fil | harf
  deriving DecidableEq, Repr

/-- الكلمةُ في التركيب: خاناتُها من الدرجة الأدنى، وقسمُها معاملٌ مُعطى. -/
structure Kalima where
  cells : List Cell
  qism : Qism

/-- التركيبُ كلماتٌ مرتَّبة. -/
abbrev Tarkib := List Kalima

/-- خاناتُ التركيب: تسطيحُ كلماته. -/
def cells (t : Tarkib) : List Cell := (t.map Kalima.cells).flatten

/-- ترخيصُ التركيب: ترخيصُ السطر على كلماته — لا غير. -/
def tarkibB (t : Tarkib) : Bool := strictLineB (t.map Kalima.cells)

/-! ## ١. إعادةُ التدوير -/

/-- لا خانةَ في التركيب إلّا من كلمةٍ فيه. -/
theorem cells_recycled (t : Tarkib) (c : Cell) (h : c ∈ cells t) : ∃ w ∈ t, c ∈ w.cells := by
  simp only [cells, List.mem_flatten, List.mem_map] at h
  obtain ⟨l, ⟨w, hw, rfl⟩, hc⟩ := h
  exact ⟨w, hw, hc⟩

/-- ترخيصُ التركيب هو ترخيصُ السطر بعينه. -/
theorem tarkibB_eq_line (t : Tarkib) : tarkibB t = strictLineB (t.map Kalima.cells) := rfl

/-- التركيبُ المرخَّص تسطيحُه مرخَّصٌ بقيد الحدّ (`strictB`). -/
theorem tarkib_flat_licensed (t : Tarkib) (h : tarkibB t = true) : strictB (cells t) = true := by
  simp only [tarkibB, strictLineB, Bool.and_eq_true] at h
  exact h.1

/-! ## ٢. القسمُ معاملٌ لا خانة -/

/-- إعادةُ وسم الأقسام. -/
def relabel (f : Qism → Qism) (t : Tarkib) : Tarkib := t.map fun w => ⟨w.cells, f w.qism⟩

/-- الترخيصُ لا يرى القسم: الدالُّ وحده يحكم في الخانات. -/
theorem licence_blind_to_qism (f : Qism → Qism) (t : Tarkib) : tarkibB (relabel f t) = tarkibB t := by
  simp [tarkibB, relabel, List.map_map, Function.comp_def]

theorem cells_blind_to_qism (f : Qism → Qism) (t : Tarkib) : cells (relabel f t) = cells t := by
  simp [cells, relabel, List.map_map, Function.comp_def]

/-! ## ٣. الإسناد -/

/-- الجملةُ الاسميّة: اسمٌ مبتدأ ومبنيٌّ عليه اسم (س236). -/
def ismiyya (a b : Kalima) : Prop := a.qism = .ism ∧ b.qism = .ism

/-- الجملةُ الفعليّة: فعلٌ ولا بدّ له من الاسم (س237). -/
def filiyya (a b : Kalima) : Prop := a.qism = .fil ∧ b.qism = .ism

/-- الإسنادُ بين متجاورين في التركيب. -/
inductive Isnad : Tarkib → Prop where
  | here (a b : Kalima) (rest : Tarkib) (h : ismiyya a b ∨ filiyya a b) : Isnad (a :: b :: rest)
  | there (w : Kalima) (t : Tarkib) (h : Isnad t) : Isnad (w :: t)

/-- الحدُّ الأدنى المكتمل للتركيب كلمتان (س235). -/
theorem isnad_needs_two {t : Tarkib} (h : Isnad t) : 2 ≤ t.length := by
  induction h with
  | here a b rest _ => simp
  | there w t _ ih => simp; omega

/-- المسندُ إليه اسمٌ أبدًا (س236–237): في كلّ إسنادٍ كلمةٌ اسم. -/
theorem musnad_ilayh_is_ism {t : Tarkib} (h : Isnad t) : ∃ w ∈ t, w.qism = .ism := by
  induction h with
  | here a b rest hab => exact ⟨b, by simp, by rcases hab with ⟨_, hb⟩ | ⟨_, hb⟩ <;> exact hb⟩
  | there w t _ ih => obtain ⟨u, hu, hq⟩ := ih; exact ⟨u, List.mem_cons_of_mem _ hu, hq⟩

/-- الحروفُ وحدَها لا تُسند. -/
theorem huruf_no_isnad (t : Tarkib) (h : ∀ w ∈ t, w.qism = .harf) : ¬ Isnad t := by
  intro hi
  obtain ⟨w, hw, hq⟩ := musnad_ilayh_is_ism hi
  have := h w hw
  rw [this] at hq
  exact Qism.noConfusion hq

/-- شبهُ الجملة (حرفٌ واسم) لا إسنادَ فيه: يحتاج إلى ما يتعلّق به. -/
theorem shibh_no_isnad (h i : Kalima) (hh : h.qism = .harf) : ¬ Isnad [h, i] := by
  intro hs
  cases hs with
  | here a b rest hab =>
    rcases hab with ⟨ha, _⟩ | ⟨ha, _⟩ <;> (rw [hh] at ha; exact Qism.noConfusion ha)
  | there w t ht =>
    cases ht with
    | there _ _ ht' => cases ht'

/-- الكلمةُ الواحدة لا إسنادَ فيها. -/
theorem single_no_isnad (w : Kalima) : ¬ Isnad [w] := by
  intro h; have := isnad_needs_two h; simp at this

/-! ## ٤. الإغلاق بالربط -/

theorem isnad_mono_left (u : Tarkib) {t : Tarkib} (h : Isnad t) : Isnad (u ++ t) := by
  induction u with
  | nil => simpa using h
  | cons w u ih => exact Isnad.there w _ ih

theorem isnad_mono_right {t : Tarkib} (h : Isnad t) (u : Tarkib) : Isnad (t ++ u) := by
  induction h with
  | here a b rest hab => exact Isnad.here a b (rest ++ u) hab
  | there w t _ ih => exact Isnad.there w _ ih

/-- جملةٌ معطوفةٌ على جملةٍ بحرفٍ بينهما: الإسنادُ قائمٌ من الجهتين. -/
theorem atf_two_isnad {t u : Tarkib} (ht : Isnad t) (hu : Isnad u) (harf : Kalima) :
    Isnad (t ++ harf :: u) ∧ Isnad (t ++ harf :: u) := by
  refine ⟨isnad_mono_right ht _, ?_⟩
  rw [← List.singleton_append, ← List.append_assoc]
  exact isnad_mono_left _ hu

/-- الابتداءُ أوّلُ أحوال الاسم (س240): كلُّ تركيبٍ أوّلُه اسمٌ يليه اسمٌ أو فعلٌ يليه اسم، إسناد. -/
theorem ism_first_state (a b : Kalima) (rest : Tarkib) (ha : a.qism = .ism ∨ a.qism = .fil)
    (hb : b.qism = .ism) : Isnad (a :: b :: rest) :=
  Isnad.here a b rest (by rcases ha with ha | ha; exact Or.inl ⟨ha, hb⟩; exact Or.inr ⟨ha, hb⟩)

/-- الشاهدُ: «عبد الله أخوك» و«يذهب عبد الله» (س236–237) على أقسامهما. -/
theorem shawahid :
    Isnad [⟨[], .ism⟩, ⟨[], .ism⟩] ∧ Isnad [⟨[], .fil⟩, ⟨[], .ism⟩] ∧ ¬ Isnad [⟨[], .harf⟩, ⟨[], .ism⟩] :=
  ⟨Isnad.here _ _ [] (Or.inl ⟨rfl, rfl⟩), Isnad.here _ _ [] (Or.inr ⟨rfl, rfl⟩),
   shibh_no_isnad _ _ rfl⟩

/-! ## ٥. الفصلُ بين المسند والمسند إليه (ADR ٧٠؛ سدُّ `ISNAD_ADJACENT_ONLY`)

الإسنادُ بين كلمتين لا يلزم تجاورُهما: «يذهب اليوم عبد الله» — المسندُ أوّلًا والمسندُ إليه بعد فاصل. فالإسنادُ
المفصول: كلمةٌ ثمّ فاصلٌ من كلماتٍ (أيُّ عدد) ثمّ كلمة، على القسمين نفسِهما. المتجاورُ حالةٌ خاصّة منه
(`isnad_sep_of_isnad`)، ويبقى اثنين في الحدّ الأدنى (`isnad_sep_needs_two`)، والحروفُ وحدَها لا تُسند
(`huruf_no_isnad_sep`). ما الفاصلُ المسموح (معمولٌ أو ظرفٌ أو جملةٌ معترضة) فليس هنا: `FASIL_KIND_NOT_WRITTEN`. -/

/-- الإسنادُ مع فاصل: a ثمّ فاصلٌ f ثمّ b، في أيّ موضعٍ من التركيب. -/
inductive IsnadSep : Tarkib → Prop where
  | here (a : Kalima) (f : Tarkib) (b : Kalima) (rest : Tarkib) (h : ismiyya a b ∨ filiyya a b) :
      IsnadSep (a :: f ++ b :: rest)
  | there (w : Kalima) (t : Tarkib) (h : IsnadSep t) : IsnadSep (w :: t)

theorem isnad_sep_of_isnad {t : Tarkib} (h : Isnad t) : IsnadSep t := by
  induction h with
  | here a b rest hab => exact IsnadSep.here a [] b rest hab
  | there w t _ ih => exact IsnadSep.there w t ih

theorem isnad_sep_needs_two {t : Tarkib} (h : IsnadSep t) : 2 ≤ t.length := by
  induction h with
  | here a f b rest _ => simp; omega
  | there w t _ ih => simp; omega

theorem musnad_ilayh_is_ism_sep {t : Tarkib} (h : IsnadSep t) : ∃ w ∈ t, w.qism = .ism := by
  induction h with
  | here a f b rest hab =>
    exact ⟨b, by simp, by rcases hab with ⟨_, hb⟩ | ⟨_, hb⟩ <;> exact hb⟩
  | there w t _ ih => obtain ⟨u, hu, hq⟩ := ih; exact ⟨u, List.mem_cons_of_mem _ hu, hq⟩

theorem huruf_no_isnad_sep (t : Tarkib) (h : ∀ w ∈ t, w.qism = .harf) : ¬ IsnadSep t := by
  intro hi
  obtain ⟨w, hw, hq⟩ := musnad_ilayh_is_ism_sep hi
  rw [h w hw] at hq
  exact Qism.noConfusion hq

/-- الشاهد: «يذهبُ اليومَ عبدُ الله» — فعلٌ، فاصلٌ (اسمٌ معمول)، ثمّ المسندُ إليه؛ وليس إسنادًا متجاورًا. -/
theorem fasl_shahid :
    IsnadSep [⟨[], .fil⟩, ⟨[], .ism⟩, ⟨[], .ism⟩] ∧
    IsnadSep [⟨[], .fil⟩, ⟨[], .harf⟩, ⟨[], .ism⟩] ∧ ¬ Isnad [⟨[], .fil⟩, ⟨[], .harf⟩, ⟨[], .ism⟩] := by
  refine ⟨IsnadSep.here _ [⟨[], .ism⟩] _ [] (Or.inr ⟨rfl, rfl⟩),
          IsnadSep.here _ [⟨[], .harf⟩] _ [] (Or.inr ⟨rfl, rfl⟩), ?_⟩
  intro h
  cases h with
  | here a b rest hab => rcases hab with ⟨_, hb⟩ | ⟨_, hb⟩ <;> exact Qism.noConfusion hb
  | there w t ht =>
    cases ht with
    | here a b rest hab => rcases hab with ⟨ha, _⟩ | ⟨ha, _⟩ <;> exact Qism.noConfusion ha
    | there _ _ ht' => cases ht' with
      | there _ _ ht'' => cases ht''

end A116.Tarkib
