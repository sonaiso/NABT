import A116.TawrithSitta

/-!
# الدالّةُ الفراكتاليّة: القانونُ نفسُه من الصفر إلى آخر نصّ (ADR ٧٧)

أمرُ المالك (2026-10-16): «اكتب دالّةً فراكتاليّة واختبر أنّها نفسُها جبريًّا من أوّل ترخيصٍ للصفر لآخر نصّ».

* **الطبقات** (`Lvl α n`): الطبقةُ 0 العنصر (الخانة أو صنفُها)، والطبقةُ ‎n+1‎ قوائمُ الطبقة n (الكلمة، ثمّ السطر،
  ثمّ النصّ…).
* **الدالّةُ الفراكتاليّة** (`fractal T n`): توريثٌ على الطبقة n تعريفُه **ذاتيُّ التشابه** — الطبقةُ ‎n+1‎ هي
  `liftT` للطبقة n بعينها (`fractal_succ`، بالتعريف)، والطبقةُ 0 هي `T`.
* **أثرُ القطعة** (`athar`): ما تفعله قطعةٌ بالحالة الموروثة — دالّةٌ من الحالة إلى حالةٍ أو انقطاع؛ وهو `run`.

المبرهَن **لكلّ طبقة n** (فالجبرُ نفسُه في كلّ مستوى):
1. **الصفر** (`fractal_zero`): القطعةُ الفارغة أثرُها الهويّة — أوّلُ ترخيص، محايدُ كلّ تركيب؛ وفي الطبقات العليا
   العنصرُ الفارغ نفسُه هويّة (`zero_element_identity`): يرث ويورث الحالةَ بعينها.
2. **التركيب** (`fractal_append`): أثرُ ‎u ++ v‎ تركيبُ أثرَيهما (كلايسلي) — تشاكلُ وحدانيّاتٍ من (القوائم، ‎++‎،
   []) إلى (الآثار، ∘، الهويّة)، والتركيبُ تجميعيّ (`kleisli_assoc`).
3. **التسطيح** (`fractal_flat`، `fractal_lic`): أثرُ الطبقة n هو أثرُ تسطيحها في الطبقة 0، وترخيصُها ترخيصُ
   تسطيحها — من الخانة إلى آخر نصّ قانونٌ واحد.
4. **الطبقةُ تمرّ بما تحتها** (`fractal_step`): أثرُ عنصرٍ في الطبقة ‎n+1‎ أثرُه قطعةً في الطبقة n.
5. **القوانينُ في كلّ طبقة** (`sitta_kull_tabaqa`): ترخيصُ الموصول ترخيصُ وصل التسطيحين (`flatN_append`)،
   وما ورّث حالةً واحدة لا يفترق ما بعده فلا يفصله سياق (`qabl_bad`)، والمانعُ يقطع (`mani_yaqta`) — لأنّ كلّ طبقةٍ
   `Tawrith`، فكلُّ مبرهنةٍ عامّةٍ في `Tawrith` و`TawrithSitta` قائمةٌ في كلّ طبقة.
6. **الشاهد** على النظام الثلاثيّ بثلاث طبقات (`shahid_fractal`).
-/

namespace A116.Fractal

open A116 A116.Nizam A116.Fasl A116.Tawrith A116.TawrithSitta

variable {α σ : Type}

/-- **الطبقات**: 0 العنصر، و‎n+1‎ قوائمُ الطبقة n. -/
def Lvl (α : Type) : Nat → Type
  | 0 => α
  | n + 1 => List (Lvl α n)

/-- التسطيحُ إلى الطبقة 0. -/
def flatN : (n : Nat) → List (Lvl α n) → List α
  | 0, x => x
  | n + 1, x => flatN n (List.flatten x)

/-- **الدالّةُ الفراكتاليّة**: التوريثُ على الطبقة n، ذاتيُّ التشابه. -/
def fractal (T : Tawrith α σ) : (n : Nat) → Tawrith (Lvl α n) σ
  | 0 => T
  | n + 1 => liftT (fractal T n)

/-- أثرُ القطعة: ما تفعله بالحالة الموروثة. -/
def athar (T : Tawrith α σ) (n : Nat) (x : List (Lvl α n)) : σ → Option σ :=
  fun s => Tawrith.run (fractal T n) s x

/-- تركيبُ أثرين (كلايسلي). -/
def kleisli (f g : σ → Option σ) : σ → Option σ := fun s => (f s).bind g

/-- **ذاتيُّ التشابه بالتعريف**. -/
theorem fractal_succ (T : Tawrith α σ) (n : Nat) : fractal T (n + 1) = liftT (fractal T n) := rfl

/-- **الصفر**: القطعةُ الفارغة أثرُها الهويّة في كلّ طبقة. -/
theorem fractal_zero (T : Tawrith α σ) (n : Nat) : athar T n [] = some := rfl

/-- **والعنصرُ الفارغ في الطبقات العليا هويّة**: يرث الحالةَ ويورثها بعينها. -/
theorem zero_element_identity (T : Tawrith α σ) (n : Nat) (s : σ) :
    (fractal T (n + 1)).step s ([] : Lvl α n |> List) = some s := rfl

/-- **التركيب**: أثرُ ‎u ++ v‎ تركيبُ أثرَيهما، في كلّ طبقة. -/
theorem fractal_append (T : Tawrith α σ) (n : Nat) (u v : List (Lvl α n)) :
    athar T n (u ++ v) = kleisli (athar T n u) (athar T n v) := by
  funext s
  exact run_append (fractal T n) s u v

theorem kleisli_assoc (f g h : σ → Option σ) : kleisli (kleisli f g) h = kleisli f (kleisli g h) := by
  funext s
  simp only [kleisli]
  cases f s <;> rfl

theorem kleisli_id_left (f : σ → Option σ) : kleisli some f = f := rfl

theorem kleisli_id_right (f : σ → Option σ) : kleisli f some = f := by
  funext s
  simp only [kleisli]
  cases f s <;> rfl

/-- **التسطيح**: أثرُ الطبقة n هو أثرُ تسطيحها في الطبقة 0. -/
theorem fractal_flat (T : Tawrith α σ) : ∀ (n : Nat) (x : List (Lvl α n)),
    athar T n x = athar T 0 (flatN n x)
  | 0, _ => rfl
  | n + 1, x => by
    funext s
    exact (run_lift (fractal T n) s x).trans (congrFun (fractal_flat T n (List.flatten x)) s)

theorem fractal_bad (T : Tawrith α σ) : ∀ n, (fractal T n).bad = T.bad
  | 0 => rfl
  | n + 1 => fractal_bad T n

theorem fractal_waqf (T : Tawrith α σ) : ∀ n, (fractal T n).waqf = T.waqf
  | 0 => rfl
  | n + 1 => fractal_waqf T n

/-- **ترخيصُ الطبقة n ترخيصُ تسطيحها** — من الخانة إلى آخر نصّ قانونٌ واحد. -/
theorem fractal_lic (T : Tawrith α σ) (n : Nat) (x : List (Lvl α n)) :
    lic (fractal T n) x = lic T (flatN n x) := by
  unfold lic
  have h : Tawrith.run (fractal T n) T.bad x = Tawrith.run T T.bad (flatN n x) :=
    congrFun (fractal_flat T n x) T.bad
  rw [fractal_bad, h]
  cases Tawrith.run T T.bad (flatN n x) with
  | none => rfl
  | some s => exact congrFun (fractal_waqf T n) s

/-- **الطبقةُ تمرّ بما تحتها**: أثرُ عنصرٍ في الطبقة ‎n+1‎ أثرُه قطعةً في الطبقة n. -/
theorem fractal_step (T : Tawrith α σ) (n : Nat) (w : List (Lvl α n)) :
    athar T (n + 1) [w] = athar T n w := by
  funext s
  show Tawrith.run (liftT (fractal T n)) s [w] = Tawrith.run (fractal T n) s w
  rw [run_lift, List.flatten_cons, List.flatten_nil, List.append_nil]

/-- التسطيحُ تشاكل: تسطيحُ الموصول وصلُ التسطيحين. -/
theorem flatN_append : ∀ (m : Nat) (u w : List (Lvl α m)), flatN m (u ++ w) = flatN m u ++ flatN m w
  | 0, _, _ => rfl
  | m + 1, u, w => (congrArg (flatN m) (@List.flatten_append (Lvl α m) u w)).trans (flatN_append m _ _)

/-- **القوانينُ في كلّ طبقة**: الوصلُ وراثةٌ وتوريثٌ عبر الحالة، والمانعُ يقطع، والفصلُ بالسياق لا يقع بين ما ورّث
حالةً واحدة. -/
theorem sitta_kull_tabaqa (T : Tawrith α σ) (n : Nat) :
    (∀ a b : List (Lvl α n), lic (fractal T n) (a ++ b) = lic T (flatN n a ++ flatN n b)) ∧
    (∀ a a' b : List (Lvl α n), athar T n a T.bad = athar T n a' T.bad →
      lic (fractal T n) (a ++ b) = lic (fractal T n) (a' ++ b)) ∧
    (∀ (s : σ) (x : Lvl α n) (v : List (Lvl α n)), (fractal T n).step s x = none →
      athar T n (x :: v) s = none) := by
  refine ⟨fun a b => ?_, fun a a' b h => ?_, fun s x v h => mani_yaqta _ s x h v⟩
  · rw [fractal_lic, flatN_append]
  · apply qabl_bad
    simpa [athar, fractal_bad] using h

/-! ## الشاهد: النظامُ الثلاثيّ بثلاث طبقات -/

/-- نصٌّ من سطرين، كلُّ سطرٍ كلمات، كلُّ كلمةٍ أصناف. -/
def nass : List (Lvl Stages.K 2) := [[[.cv, .c], [.cv, .v]], [[.cv], [.cv, .c]]]

/-- **الشاهد**: الترخيصُ في الطبقة الثانية هو ترخيصُ التسطيح، والأثرُ هو أثرُه، والصفرُ هويّة. -/
theorem shahid_fractal :
    lic (fractal (ofNizam ternary) 2) nass = true ∧
    lic (fractal (ofNizam ternary) 2) nass = licWasl ternary [.cv, .c, .cv, .v, .cv, .cv, .c] ∧
    athar (ofNizam ternary) 2 nass none = some (some .c) ∧
    lic (fractal (ofNizam ternary) 2) [[[.cv, .c]], [[.c]]] = false := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · rw [fractal_lic]; decide
  · rw [fractal_lic, nizam_wasl]; rfl
  · rw [fractal_flat]; decide
  · rw [fractal_lic]; decide

end A116.Fractal
