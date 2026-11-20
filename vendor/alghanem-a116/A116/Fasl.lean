import A116.Jadwal
import A116.Dal

/-!
# قانونُ الفصل: الرابعُ مع الابتداء والوصل والوقف (ADR ٧٤)

نصُّ المالك (2026-10-16): «لأنّ الهويّات لم تنظّم عمليّات قانون الفصل نحتاج أربعَ قوانين ربّما ليس ثلاث: قانونُ الابتداء
وقانونُ الوصل وقانونُ الوقف وقانونُ الفصل، ويكون له سببٌ وشرطٌ ومانع، والفصلُ أساسٌ للتمييز والتعيين».

`Nizam` يحكم على **السلسلة**: الأوّلُ (الابتداء)، وكلُّ متجاورين (الوصل)، والطرفُ (الوقف). ولا شيءَ فيه يحكم على
**عنصرين في مجال** هل يتميّزان. هذا هو الرابع:

* **السببُ** (`sabab`): الصفةُ التي يقع بها الفصل (المخرج، الصفات، الخانات، الموضع).
* **الشرطُ** (`shart`): المجالُ الذي يُطلب فيه الفصل — الفصلُ نسبيٌّ إلى مجاله لا مطلق.
* **المانعُ** (`mani`): **لا يُدخَل بل يُحسب** — زوجان مختلفان في الشرط سببُهما واحد.
* **التمييز** (`tamyiz`): اختلافُ السبب؛ و**التعيين** (`tayin`): ردُّ السبب إلى صاحبه في الشرط.

المبرهَنُ لكلّ مجالٍ ولكلّ سبب:
1. الفصلُ ⟺ لا مانع (`fasl_iff_no_mani`)؛ والتعيينُ لا يخترع (`tayin_sound`)؛ والفصلُ ⟺ التعيينُ تامّ
   (`tayin_of_fasl`، `fasl_of_tayin`)؛ وكلُّ مانعٍ يُسقط تعيينَ أحد طرفيه (`mani_blocks_tayin`).
2. **الاستنفادُ بالسبب**: سببٌ ثانٍ يفصل ⟺ يميّز كلَّ مانعٍ للأوّل بعينه (`istinfad_sabab`)؛ والسببُ لا يضرّه ما يُزاد
   عليه (`sabab_mono`)، والأخشنُ إن فصل فصل الأدقّ (`sabab_coarse`).
3. **الاستنفادُ بالشرط**: تضييقُ المجال يفصل ⟺ لا يجمع طرفَي مانعٍ (`istinfad_shart`)، وما فصل في مجالٍ فصل في
   بعضه (`shart_mono`).
4. **الثلاثةُ لا تفصل**: لكلّ `Nizam` مسحوبٍ على السبب، طرفا المانع متساويان في الابتداء والوصل والوقف في كلّ سياق
   (`thalatha_la_tafsil`) — فالفصلُ قانونٌ رابعٌ لا يُستخرج من الثلاثة.
5. **الحدُّ الأدنى المكتمل** (`mukhtamal`): سببٌ مركّبٌ يفصل ولا يفصل إن أُسقط منه جزء.

والمثولات:
* **الموضعُ في الكلمة**: موضعُ `Nizam.huwiyyat` يفصل هويّاتِ كلّ كلمة (`mawdi_fasl`)، والخانةُ وحدَها لا تفصل
  هويّاتِ «بَبَ» (`khana_mani`) — فموضعُ الهويّة **سببُ فصلٍ** لا يعارضه شيء هنا.
* **موضعُ النطق وحالتُه**: المخرجُ وحدَه لا يفصل الحروف (`makhraj_mani`)؛ والمخرجُ وأربعُ صفاتٍ يفصلها ويعيّن كلَّ حرف
  (`nutq_fasl`، `nutq_tayin`)، وهو حدٌّ أدنى مكتمل (`nutq_mukhtamal`) — فالحاملُ = (مخرج، صفات) **مبرهنةٌ على الـ29**
  لا تعريفٌ يحلّ محلّ `Huwiyya`؛ والغنّةُ شرطٌ يرفع موانع المخرج (`ghunna_shart`).
* **الدور**: الدورُ وحدَه لا يفصل بَ من تَ (`dawr_mani`)، فقانونُ الوصل الثلاثيّ لا يفرّقهما في أيّ سياق
  (`ternary_la_tafsil`).
* **الدالّ**: الخاناتُ لا تفصل قول من قيل في قَالَ (`dal_mani`)، فلا تعيينَ للجذر منها (`dal_la_tayin`) — `Dal` مثولًا.
-/

namespace A116.Fasl

open A116 A116.Stages A116.Ladder A116.Nizam A116.Jisr

/-! ## ١. البنية -/

/-- **قانونُ الفصل**: سببٌ وشرط؛ والمانعُ محسوب. -/
structure Fasl (α β : Type) where
  sabab : α → β
  shart : List α

variable {α β γ : Type} [DecidableEq α] [DecidableEq β] [DecidableEq γ]

/-- التمييز: اختلافُ السبب. -/
def tamyiz (F : Fasl α β) (a b : α) : Bool := F.sabab a != F.sabab b

/-- المانع: زوجان مختلفان في الشرط بسببٍ واحد. -/
def mani (F : Fasl α β) : List (α × α) :=
  F.shart.flatMap fun a => (F.shart.filter fun b => a != b && F.sabab a == F.sabab b).map (a, ·)

/-- الفصل: كلُّ زوجين مختلفين في الشرط يتميّزان. -/
def fasl (F : Fasl α β) : Bool := F.shart.all fun a => F.shart.all fun b => a == b || tamyiz F a b

/-- التعيين: صاحبُ السبب في الشرط. -/
def tayin (F : Fasl α β) (y : β) : Option α := F.shart.find? fun a => F.sabab a == y

/-! ## ٢. القوانين العامّة -/

theorem mem_mani (F : Fasl α β) (a b : α) :
    (a, b) ∈ mani F ↔ a ∈ F.shart ∧ b ∈ F.shart ∧ a ≠ b ∧ F.sabab a = F.sabab b := by
  simp only [mani, List.mem_flatMap, List.mem_map, List.mem_filter, Prod.mk.injEq, Bool.and_eq_true,
    bne_iff_ne, ne_eq, beq_iff_eq]
  constructor
  · rintro ⟨a', ha', b', ⟨hb', hne, heq⟩, rfl, rfl⟩
    exact ⟨ha', hb', hne, heq⟩
  · rintro ⟨ha, hb, hne, heq⟩
    exact ⟨a, ha, b, ⟨hb, hne, heq⟩, rfl, rfl⟩

theorem fasl_iff (F : Fasl α β) :
    fasl F = true ↔ ∀ a ∈ F.shart, ∀ b ∈ F.shart, F.sabab a = F.sabab b → a = b := by
  simp only [fasl, tamyiz, List.all_eq_true, Bool.or_eq_true, beq_iff_eq, bne_iff_ne, ne_eq]
  constructor
  · intro h a ha b hb he
    rcases h a ha b hb with h | h
    · exact h
    · exact absurd he h
  · intro h a ha b hb
    by_cases he : F.sabab a = F.sabab b
    · exact Or.inl (h a ha b hb he)
    · exact Or.inr he

/-- **الفصلُ ⟺ لا مانع.** -/
theorem fasl_iff_no_mani (F : Fasl α β) : fasl F = true ↔ mani F = [] := by
  rw [fasl_iff, List.eq_nil_iff_forall_not_mem]
  constructor
  · rintro h ⟨a, b⟩ hm
    obtain ⟨ha, hb, hne, he⟩ := (mem_mani F a b).1 hm
    exact hne (h a ha b hb he)
  · intro h a ha b hb he
    by_cases hab : a = b
    · exact hab
    · exact absurd ((mem_mani F a b).2 ⟨ha, hb, hab, he⟩) (h (a, b))

omit [DecidableEq α] in
/-- **التعيينُ لا يخترع**: ما عيّنه في الشرط وسببُه السببُ المطلوب. -/
theorem tayin_sound (F : Fasl α β) (y : β) (a : α) (h : tayin F y = some a) :
    a ∈ F.shart ∧ F.sabab a = y := by
  unfold tayin at h
  exact ⟨List.mem_of_find?_eq_some h, by simpa using List.find?_some h⟩

/-- **الفصلُ يُتمّ التعيين.** -/
theorem tayin_of_fasl (F : Fasl α β) (h : fasl F = true) (a : α) (ha : a ∈ F.shart) :
    tayin F (F.sabab a) = some a := by
  have hf := (fasl_iff F).1 h
  cases hx : tayin F (F.sabab a) with
  | none =>
    unfold tayin at hx
    have := List.find?_eq_none.1 hx a ha
    simp at this
  | some b =>
    obtain ⟨hb, he⟩ := tayin_sound F _ b hx
    rw [hf b hb a ha he]

/-- **والتعيينُ التامّ فصل** — فالفصلُ أساسُ التعيين بعينه. -/
theorem fasl_of_tayin (F : Fasl α β) (h : ∀ a ∈ F.shart, tayin F (F.sabab a) = some a) : fasl F = true := by
  rw [fasl_iff]
  intro a ha b hb he
  have h1 := h a ha
  have h2 := h b hb
  rw [he] at h1
  rw [h1] at h2
  exact Option.some.inj h2

/-- **المانعُ يُسقط التعيين**: أحدُ طرفيه لا يُعيَّن. -/
theorem mani_blocks_tayin (F : Fasl α β) (a b : α) (h : (a, b) ∈ mani F) :
    tayin F (F.sabab a) ≠ some a ∨ tayin F (F.sabab b) ≠ some b := by
  obtain ⟨_, _, hne, he⟩ := (mem_mani F a b).1 h
  by_cases h1 : tayin F (F.sabab a) = some a
  · right
    rw [← he, h1]
    intro h2
    exact hne (Option.some.inj h2)
  · exact Or.inl h1

/-! ## ٣. الاستنفادُ بالسبب وبالشرط -/

/-- **الاستنفادُ بالسبب**: إضافةُ سببٍ ثانٍ تفصل ⟺ يميّز الثاني كلَّ مانعٍ للأوّل. -/
theorem istinfad_sabab (f : α → β) (g : α → γ) (S : List α) :
    fasl ⟨fun a => (f a, g a), S⟩ = true ↔ ∀ p ∈ mani ⟨f, S⟩, g p.1 ≠ g p.2 := by
  rw [fasl_iff]
  constructor
  · rintro h ⟨a, b⟩ hm hg
    obtain ⟨ha, hb, hne, he⟩ := (mem_mani ⟨f, S⟩ a b).1 hm
    exact hne (h a ha b hb (by simp only at he hg ⊢; rw [he, hg]))
  · intro h a ha b hb he
    simp only [Prod.mk.injEq] at he
    by_cases hab : a = b
    · exact hab
    · exact absurd he.2 (h (a, b) ((mem_mani ⟨f, S⟩ a b).2 ⟨ha, hb, hab, he.1⟩))

/-- السببُ لا يضرّه ما يُزاد عليه. -/
theorem sabab_mono (f : α → β) (g : α → γ) (S : List α) (h : fasl ⟨f, S⟩ = true) :
    fasl ⟨fun a => (f a, g a), S⟩ = true := by
  rw [istinfad_sabab, (fasl_iff_no_mani _).1 h]
  intro p hp
  cases hp

/-- الأخشنُ إن فصل فصل الأدقّ. -/
theorem sabab_coarse (f : α → β) (h : β → γ) (S : List α) (hf : fasl ⟨fun a => h (f a), S⟩ = true) :
    fasl ⟨f, S⟩ = true := by
  rw [fasl_iff] at hf ⊢
  intro a ha b hb he
  exact hf a ha b hb (by simp only at he ⊢; rw [he])

/-- **الاستنفادُ بالشرط**: تضييقُ المجال بـ`p` يفصل ⟺ لا يجمع طرفَي مانعٍ. -/
theorem istinfad_shart (f : α → β) (S : List α) (p : α → Bool) :
    fasl ⟨f, S.filter p⟩ = true ↔ ∀ q ∈ mani ⟨f, S⟩, ¬ (p q.1 = true ∧ p q.2 = true) := by
  rw [fasl_iff]
  simp only [List.mem_filter]
  constructor
  · rintro h ⟨a, b⟩ hm ⟨hpa, hpb⟩
    obtain ⟨ha, hb, hne, he⟩ := (mem_mani ⟨f, S⟩ a b).1 hm
    exact hne (h a ⟨ha, hpa⟩ b ⟨hb, hpb⟩ he)
  · rintro h a ⟨ha, hpa⟩ b ⟨hb, hpb⟩ he
    by_cases hab : a = b
    · exact hab
    · exact absurd ⟨hpa, hpb⟩ (h (a, b) ((mem_mani ⟨f, S⟩ a b).2 ⟨ha, hb, hab, he⟩))

/-- ما فصل في مجالٍ فصل في بعضه. -/
theorem shart_mono (f : α → β) (S T : List α) (hT : ∀ x ∈ T, x ∈ S) (h : fasl ⟨f, S⟩ = true) :
    fasl ⟨f, T⟩ = true := by
  rw [fasl_iff] at h ⊢
  intro a ha b hb he
  exact h a (hT a ha) b (hT b hb) he

/-! ## ٤. الثلاثةُ لا تفصل -/

omit [DecidableEq α] [DecidableEq β] in
theorem licWaqf_comap (N : Nizam β) (f : α → β) (w : List α) :
    licWaqf (comap N f) w = licWaqf N (w.map f) := by
  cases w with
  | nil => rfl
  | cons a t =>
    have hc : ∀ (x : α) (u : List α), chainP (comap N f) x u = chainP N (f x) (u.map f) := by
      intro x u
      induction u generalizing x with
      | nil => rfl
      | cons y u ih =>
        cases u with
        | nil => rfl
        | cons z v =>
          simp only [chainP, List.map_cons] at ih ⊢
          rw [ih]
          rfl
    simp only [licWaqf, List.map_cons, hc, List.all_cons, List.all_map]
    rfl

/-- **الثلاثةُ لا تفصل**: لكلّ نظامٍ يُحكم على السبب، طرفا المانع متساويان ابتداءً ووصلًا ووقفًا في كلّ سياق. -/
theorem thalatha_la_tafsil (N : Nizam β) (F : Fasl α β) (a b : α) (h : (a, b) ∈ mani F) (u v : List α) :
    licWasl (comap N F.sabab) (u ++ a :: v) = licWasl (comap N F.sabab) (u ++ b :: v) ∧
    licWaqf (comap N F.sabab) (u ++ a :: v) = licWaqf (comap N F.sabab) (u ++ b :: v) := by
  obtain ⟨_, _, _, he⟩ := (mem_mani F a b).1 h
  refine ⟨?_, ?_⟩
  · rw [licWasl_comap, licWasl_comap, List.map_append, List.map_append, List.map_cons, List.map_cons, he]
  · rw [licWaqf_comap, licWaqf_comap, List.map_append, List.map_append, List.map_cons, List.map_cons, he]

/-! ## ٥. الحدُّ الأدنى المكتمل -/

/-- سببٌ مركّبٌ من أجزاء `ss` يفصل، ولا يفصل إن أُسقط منه أيُّ جزء. -/
def mukhtamal {ι : Type} (key : List ι → α → β) (ss : List ι) (S : List α) : Bool :=
  fasl ⟨key ss, S⟩ && (List.range ss.length).all fun i => !fasl ⟨key (ss.eraseIdx i), S⟩

/-! ## ٦. المثولات -/

/-- مجالُ الفصل يُبنى من الهويّات: لكلّ قائمةٍ مواضعُها بلا تكرار. -/
theorem mawdi_from (i : Nat) (w : List Cell) : (huwiyyatFrom i w).map Huwiyya.mawdi = List.range' i w.length := by
  induction w generalizing i with
  | nil => rfl
  | cons c t ih =>
    simp only [huwiyyatFrom, List.map_cons, List.length_cons, ih]
    rw [List.range'_succ]

theorem fasl_of_nodup (f : α → β) : ∀ S : List α, (S.map f).Nodup → fasl ⟨f, S⟩ = true
  | [], _ => rfl
  | x :: t, h => by
    rw [List.map_cons, List.nodup_cons] at h
    have ih := (fasl_iff _).1 (fasl_of_nodup f t h.2)
    rw [fasl_iff]
    intro a ha b hb he
    simp only [List.mem_cons] at ha hb
    simp only at he
    rcases ha with rfl | ha <;> rcases hb with rfl | hb
    · rfl
    · exact absurd (he ▸ List.mem_map_of_mem hb) h.1
    · exact absurd (he.symm ▸ List.mem_map_of_mem ha) h.1
    · exact ih a ha b hb he

/-- **الموضعُ يفصل هويّاتِ كلّ كلمة.** -/
theorem mawdi_fasl (w : List Cell) : fasl ⟨Huwiyya.mawdi, huwiyyat w⟩ = true := by
  apply fasl_of_nodup
  unfold huwiyyat
  rw [mawdi_from]
  exact List.nodup_range'

/-- **والخانةُ وحدَها لا تفصل** هويّتَي «بَبَ». -/
theorem khana_mani :
    mani ⟨cellOf, huwiyyat [atom 'ب' .fatha, atom 'ب' .fatha]⟩ ≠ [] := by decide

/-- المخرجُ وحدَه سببًا على الحروف. -/
def makhrajF : Fasl Char Nat := ⟨Makharij.makhrajOf, Makharij.placed16⟩

def arba : List Jadwal.Sifa := [.hams, .shidda, .tawassut, .istila]

/-- المخرجُ وأربعُ صفات: موضعُ النطق وحالتُه. -/
def nutqF : Fasl Char (Nat × List Bool) := ⟨Jadwal.key arba, Makharij.placed16⟩

/-- **المخرجُ وحدَه لا يفصل**: الهمزةُ والهاءُ من مخرجٍ واحد. -/
theorem makhraj_mani : ('ء', 'ه') ∈ mani makhrajF := by
  rw [mem_mani]; decide

/-- عددُ الموانع بالمخرج وحدَه أزواجًا مرتّبة: ‎Σ s(s−1)‎ على مخارج سيبويه. -/
theorem makhraj_mani_count : (mani makhrajF).length = 40 := by decide

/-- **المخرجُ وأربعُ صفاتٍ يفصل.** -/
theorem nutq_fasl : fasl nutqF = true := by decide +kernel

/-- **ويعيّن كلَّ حرف**: الحاملُ يُردّ من (مخرج، صفات). -/
theorem nutq_tayin : ∀ c ∈ Makharij.placed16, tayin nutqF (Jadwal.key arba c) = some c :=
  fun c hc => tayin_of_fasl nutqF nutq_fasl c hc

/-- **حدٌّ أدنى مكتمل**: لا تُسقَط صفةٌ من الأربع. -/
theorem nutq_mukhtamal : mukhtamal Jadwal.key arba Makharij.placed16 = true := by decide +kernel

/-- **الغنّةُ شرطٌ يرفع موانع المخرج**: في حرفي الغنّة يفصل المخرجُ وحدَه. -/
theorem ghunna_shart : fasl ⟨Makharij.makhrajOf, Makharij.placed16.filter (Jadwal.has .ghunna)⟩ = true := by
  decide

/-- الدورُ وحدَه سببًا على الخانات المرخَّصة ابتداءً. -/
def dawrF : Fasl Cell K := ⟨Hadd.kindOne none, Jadwal.khanat.filter Jadwal.licensableCell⟩

/-- **الدورُ لا يفصل بَ من تَ.** -/
theorem dawr_mani : (atom 'ب' .fatha, atom 'ت' .fatha) ∈ mani dawrF := by
  rw [mem_mani]; decide +kernel

/-- **فقانونُ الوصل والوقف الثلاثيُّ لا يفرّقهما في أيّ سياق.** -/
theorem ternary_la_tafsil (u v : List Cell) :
    licWasl (comap ternary dawrF.sabab) (u ++ atom 'ب' .fatha :: v) =
      licWasl (comap ternary dawrF.sabab) (u ++ atom 'ت' .fatha :: v) ∧
    licWaqf (comap ternary dawrF.sabab) (u ++ atom 'ب' .fatha :: v) =
      licWaqf (comap ternary dawrF.sabab) (u ++ atom 'ت' .fatha :: v) :=
  thalatha_la_tafsil ternary dawrF _ _ dawr_mani u v

/-- الدالّ: قَالَ على الجذرين (`false` قول، `true` قيل). -/
def dalF : Fasl Bool (List Cell) := ⟨fun b => Dal.qala (if b then Dal.qyl else Dal.qwl), [false, true]⟩

/-- **الخاناتُ لا تفصل قول من قيل.** -/
theorem dal_mani : (false, true) ∈ mani dalF := by
  rw [mem_mani]
  refine ⟨by decide, by decide, by decide, ?_⟩
  show Dal.qala Dal.qwl = Dal.qala Dal.qyl
  exact Dal.qala_same_cells

/-- **فلا تعيينَ للجذر منها.** -/
theorem dal_la_tayin : tayin dalF (dalF.sabab false) ≠ some false ∨ tayin dalF (dalF.sabab true) ≠ some true :=
  mani_blocks_tayin dalF false true dal_mani

end A116.Fasl
