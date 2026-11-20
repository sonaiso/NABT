/-!
# رسمُ السنّ في hamil: عقدةُ التفرّع الوحيدة، والتوزيعُ المستقرّ، وحصّةُ المجرّد

## المصدر (مقروءٌ من الشيفرة)

hamil، الالتزام `6efd033`، `algebra_engine.py`:

* `EDGES` تسعةُ أسهم: I→II، I→IV، II→V، IV→VII، I→VIII، I→III، III→VI، I→X، I→IX.
* `derivation_markov`: صفُّ كلِّ عقدةٍ موزَّعٌ بالتساوي على أسهمها، و**المصرفُ يتجدّد إلى I**.

## المبرهنات (مفحوصةٌ بالنواة)

* `branching_nodes`: العقدُ التي درجةُ خروجها > 1 هي I وحدها، ودرجتُها 6.
* `rows_stochastic`: كلُّ صفٍّ من `p6` (الاحتمالُ مضروبًا في 6) مجموعُه 6.
* `stationary_unique`: كلُّ متّجهٍ صحيحٍ مستقرٍّ يحقّق `6·v j = v I` لكلّ j ≠ I؛
  فالتوزيعُ المستقرّ وحيدٌ: `π(I) = 6/15 = 2/5`، ولكلٍّ من التسع `1/15`.
* `share_of_I`: لكلّ متّجهٍ مستقرّ `2·Σv = 5·v(I)`، أي `π(I) = 2/5`.
* `stationary_w`: المتّجهُ `w = (6,1,…,1)` مستقرٌّ فعلًا.

## ما ليس مبرهَنًا هنا

قانونُ معدّل الإنتروبيا لسلسلةٍ مستقرّة `H = Σ πᵢ H(Pᵢ)` مبرهنةٌ معيارية
(Cover & Thomas، المبرهنة 4.2.4) لا تُبرهَن في هذه الشجرة لغياب اللوغاريتم الحقيقيّ.
وبها، مع `branching_nodes`، يصير المعدّل `π(I)·log₂ 6 = (2/5)·log₂ 6`؛ وقيمتُه
العشريّة ≈ 1.033985 حسابٌ عائمٌ في البايثون (`derivation_markov`) لا في Lean.
-/

namespace A116.Derivation

/-- الأوزانُ العشرة بترتيب `W10`. -/
inductive Form where
  | I | II | III | IV | V | VI | VII | VIII | IX | X
  deriving DecidableEq, Repr

open Form

def forms : List Form := [I, II, III, IV, V, VI, VII, VIII, IX, X]

/-- `EDGES` بترتيبها في `algebra_engine.py`. -/
def edges : List (Form × Form) :=
  [(I, II), (I, IV), (II, V), (IV, VII), (I, VIII), (I, III), (III, VI), (I, X), (I, IX)]

def outdeg (a : Form) : Nat := (edges.filter fun e => e.1 == a).length

def mult (a b : Form) : Nat := (edges.filter fun e => e == (a, b)).length

/-- الاحتمالُ مضروبًا في 6: موزَّعٌ بالتساوي، والمصرفُ يتجدّد إلى I. -/
def p6 (a b : Form) : Nat :=
  if outdeg a = 0 then (if b = I then 6 else 0) else mult a b * (6 / outdeg a)

theorem edges_length : edges.length = 9 := by decide

theorem branching_nodes : forms.filter (fun a => decide (1 < outdeg a)) = [I] ∧ outdeg I = 6 := by
  decide

theorem rows_stochastic : ∀ a ∈ forms, (forms.map (p6 a)).sum = 6 := by decide

/-- المجموعُ الوارد إلى `b` مضروبًا في 6. -/
def inflow (v : Form → Int) (b : Form) : Int :=
  (forms.map fun a => v a * (p6 a b : Int)).sum

/-- الاستقرار: `π P = π`، مضروبًا في 6. -/
def Stationary (v : Form → Int) : Prop := ∀ b ∈ forms, 6 * v b = inflow v b

theorem stationary_unique (v : Form → Int) (h : Stationary v) :
    ∀ b ∈ forms, b ≠ I → 6 * v b = v I := by
  have e := fun b (hb : b ∈ forms) => h b hb
  have eII := e II (by decide); have eIII := e III (by decide)
  have eIV := e IV (by decide); have eV := e V (by decide)
  have eVI := e VI (by decide); have eVII := e VII (by decide)
  have eVIII := e VIII (by decide); have eIX := e IX (by decide)
  have eX := e X (by decide)
  simp [inflow, forms, p6, outdeg, mult, edges] at eII eIII eIV eV eVI eVII eVIII eIX eX
  intro b hb hne
  simp [forms] at hb
  rcases hb with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl <;>
    first | exact absurd rfl hne | omega

/-- حصّةُ المجرّد: `π(I) = v I / Σ v = 2/5` لكلّ متّجهٍ مستقرّ. -/
theorem share_of_I (v : Form → Int) (h : Stationary v) :
    2 * (forms.map v).sum = 5 * v I := by
  have k := stationary_unique v h
  have kII := k II (by decide) (by decide); have kIII := k III (by decide) (by decide)
  have kIV := k IV (by decide) (by decide); have kV := k V (by decide) (by decide)
  have kVI := k VI (by decide) (by decide); have kVII := k VII (by decide) (by decide)
  have kVIII := k VIII (by decide) (by decide); have kIX := k IX (by decide) (by decide)
  have kX := k X (by decide) (by decide)
  simp [forms]
  omega

def w : Form → Int
  | I => 6
  | _ => 1

theorem stationary_w : Stationary w := by
  intro b hb
  simp [forms] at hb
  rcases hb with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl <;> decide

theorem w_total : (forms.map w).sum = 15 := by decide

end A116.Derivation
