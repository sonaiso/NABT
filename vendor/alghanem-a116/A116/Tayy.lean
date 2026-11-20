import A116.Nizam
import A116.Fiber
import A116.Dal

/-!
# الطيُّ والاسترجاع للمنظومة كلّها: طبقاتٌ متتابعةٌ كلٌّ منها طيٌّ ببقيّة (ADR ٥٧)

**الطيّ** (`Tayy A B R`) خطوةٌ من طبقةٍ إلى التي فوقها: تُخرج صورةً `B` وبقيّةً `R`، ولها **استرجاعٌ** يردّ
العنصرَ بعينه من الصورة والبقيّة على مجالها (`law`). وما تقوله المبرهنات:

* `comp`، `comp_law`: **تركيبُ طيّين طيٌّ** — البقيّةُ زوجُ البقيّتين، والاسترجاعُ بالترتيب المعكوس. فالمنظومةُ
  كلُّها طيٌّ واحدٌ قابلٌ للاسترجاع **إذا كانت كلُّ خطوةٍ فيها طيًّا** — لا أكثر.
* `ofIntiqal`: كلُّ انتقالٍ مسجَّلٍ في `Nizam` (الإعلال، والإبدال، وبقيّةُ الرسم) طيٌّ. وسلسلتُها `Nizam.sijill`.
* `ofFiber`: الإسقاطُ إلى الصورة مع **الرتبة** بقيّةً طيٌّ على مجالٍ منتهٍ (`Fiber.decode_encode`) — وهو طيُّ الشهادة
  (`Certificate`).
* `residue_separates`: **لا طيَّ بلا بقيّة حيث لا تباين**: عنصران مختلفان بصورةٍ واحدة لا بدّ أن تختلف بقيّتاهما.
  و`unit_residue_injective`: بلا بقيّةٍ لا يكون طيٌّ إلّا متباينًا.
* `wad_step_needs_residue`: **على خطوة الوضع بعينها**: كلُّ طيٍّ من الجذر إلى خانات قَالَ (`Dal.qala`) يحتاج بقيّةً
  تفصل قول من قيل — فهذه البقيّةُ هي القرينة، وليست في الخانات (`Dal.no_cell_function_recovers_root`).

فالدعوى الصحيحة: **المنظومةُ قابلةٌ للطيّ والاسترجاع بقدر ما أُودعت بقايا خطواتها**؛ وحيث لا بقيّةَ مودَعة (القرينة
عند المشترك) فالاسترجاعُ متعدّدٌ لا يُحسم — وهذا مبرهَنٌ لا معلن.
-/

set_option autoImplicit false

namespace A116.Tayy

/-- خطوةُ طيٍّ: صورةٌ وبقيّة، واسترجاعٌ يردّ العنصرَ على مجاله. -/
structure Tayy (A B R : Type) where
  dom : A → Prop
  fold : A → B × R
  unfold : B × R → Option A
  law : ∀ a, dom a → unfold (fold a) = some a

/-- **تركيبُ طيّين**: صورةُ الثاني، والبقيّةُ زوجُ البقيّتين. -/
def comp {A B C R S : Type} (f : Tayy A B R) (g : Tayy B C S) : Tayy A C (R × S) where
  dom a := f.dom a ∧ g.dom (f.fold a).1
  fold a := ((g.fold (f.fold a).1).1, ((f.fold a).2, (g.fold (f.fold a).1).2))
  unfold c := (g.unfold (c.1, c.2.2)).bind fun b => f.unfold (b, c.2.1)
  law a h := by
    simp only
    rw [show ((g.fold (f.fold a).1).1, (g.fold (f.fold a).1).2) = g.fold (f.fold a).1 from rfl,
      g.law _ h.2]
    simp only [Option.bind_some]
    exact f.law a h.1

/-- **قانونُ التركيب**: ما استرجعته الخطوتان استرجعه تركيبُهما. -/
theorem comp_law {A B C R S : Type} (f : Tayy A B R) (g : Tayy B C S) (a : A)
    (h1 : f.dom a) (h2 : g.dom (f.fold a).1) : (comp f g).unfold ((comp f g).fold a) = some a :=
  (comp f g).law a ⟨h1, h2⟩

/-- الهويّة طيٌّ بلا بقيّة. -/
def idT (A : Type) : Tayy A A Unit where
  dom _ := True
  fold a := (a, ())
  unfold c := some c.1
  law _ _ := rfl

/-- كلُّ انتقالٍ مسجَّلٍ في `Nizam` طيٌّ على كلّ عنصر. -/
def ofIntiqal {β R : Type} (t : Nizam.Intiqal β R) : Tayy β β R where
  dom _ := True
  fold := t.go
  unfold c := some (t.back c.1 c.2)
  law a _ := by show some (t.back (t.go a).1 (t.go a).2) = some a; rw [t.law a]

/-- الإسقاطُ مع الرتبة طيٌّ على المجال المنتهي. -/
def ofFiber {α β : Type} [DecidableEq α] [DecidableEq β] (D : List α) (P : α → β) : Tayy α β Nat where
  dom x := x ∈ D
  fold := Fiber.encode D P
  unfold := Fiber.decode D P
  law _ h := Fiber.decode_encode h

/-- **لا طيَّ بلا بقيّة حيث لا تباين.** -/
theorem residue_separates {A B R : Type} (t : Tayy A B R) {a₁ a₂ : A} (h₁ : t.dom a₁) (h₂ : t.dom a₂)
    (hne : a₁ ≠ a₂) (hB : (t.fold a₁).1 = (t.fold a₂).1) : (t.fold a₁).2 ≠ (t.fold a₂).2 := by
  intro hR
  have e : t.fold a₁ = t.fold a₂ := Prod.ext hB hR
  have := (t.law a₁ h₁).symm.trans ((congrArg t.unfold e).trans (t.law a₂ h₂))
  exact hne (Option.some.inj this)

/-- بلا بقيّةٍ لا يكون طيٌّ إلّا متباينًا. -/
theorem unit_residue_injective {A B : Type} (t : Tayy A B Unit) {a₁ a₂ : A} (h₁ : t.dom a₁)
    (h₂ : t.dom a₂) (hB : (t.fold a₁).1 = (t.fold a₂).1) : a₁ = a₂ :=
  Classical.byContradiction fun hne => residue_separates t h₁ h₂ hne hB rfl

/-- **خطوةُ الوضع تحتاج بقيّة**: كلُّ طيٍّ يُخرج من الجذر خاناتِ قَالَ يفصل قول من قيل ببقيّته. -/
theorem wad_step_needs_residue {R : Type} (t : Tayy (Wazn.Root 3) (List Cell) R)
    (hdom : ∀ r, t.dom r) (hfold : ∀ r, (t.fold r).1 = Dal.qala r) :
    (t.fold Dal.qwl).2 ≠ (t.fold Dal.qyl).2 :=
  residue_separates t (hdom _) (hdom _) Dal.qwl_ne_qyl
    (by rw [hfold, hfold, Dal.qala_same_cells])

end A116.Tayy
