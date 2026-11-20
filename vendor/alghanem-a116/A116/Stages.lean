/-!
# التقطيعُ المقطعيّ دالّةٌ وحيدةُ الناتج، ومعكوسُها الوصل — لكلّ سلسلة

النظيرُ البايثونيّ: `alghanem.arabic.mabni_stages.syllabify`.

## الأنواع

* نوعُ الذرّة `K`: `cv` (خانةٌ متحرّكة)، `v` (ساكنةٌ دورُها مدّ)، `c` (ساكنةٌ تُغلق).
* المقطع `Syl`: `CV`، `CVV`، `CVC`، `CVVC`، `CVCC`، `CVVCC` — متحرّكٌ يفتح وما بعده يُتمّه.
  (`CVVCC`: مدٌّ قبل مضعَّفٍ موقوفٍ عليه، تَامّْ؛ شوهد في نصٍّ خارجَ القرآن.)
* القطعةُ الصادرة `Lead`: لا شيء، أو `C|`، أو `V|`، أو `VC|` — ما يسبق أوّلَ متحرّكٍ
  حين يقطع التجزيءُ تضعيفًا أو مدًّا نواتُه في القطعة السابقة.

## المبرهنات (لكلّ سلسلةٍ بأيّ طول، لا على مدوّنة)

* `parse_flat`: تقطيعُ وصلِ أيِّ قطعةٍ ومقاطع يعيدها بعينها.
* `flat_parse`: ما قطّعه `parse` يعيد الوصلُ السلسلةَ نفسَها.
* `flat_injective`: لا يكون لسلسلةٍ تقطيعان.
* فـ`parse` تقابلٌ بين مجاله وأزواج (قطعة، مقاطع)، والمقاطعُ الستّةُ والقطعُ الأربعُ
  هي **كلُّ** ما يمكن أن يخرج.
-/

namespace A116.Stages

inductive K where
  | cv | v | c
  deriving DecidableEq, Repr

inductive Syl where
  | CV | CVV | CVC | CVVC | CVCC | CVVCC
  deriving DecidableEq, Repr

inductive Lead where
  | none | C | V | VC
  deriving DecidableEq, Repr

open K

/-- ذيلُ المقطع بعد متحرّكه. -/
def Syl.coda : Syl → List K
  | .CV => []
  | .CVV => [v]
  | .CVC => [c]
  | .CVVC => [v, c]
  | .CVCC => [c, c]
  | .CVVCC => [v, c, c]

def Syl.atoms (s : Syl) : List K := cv :: s.coda

def Lead.atoms : Lead → List K
  | .none => []
  | .C => [c]
  | .V => [v]
  | .VC => [v, c]

def sylOf : List K → Option Syl
  | [] => some .CV
  | [v] => some .CVV
  | [c] => some .CVC
  | [v, c] => some .CVVC
  | [c, c] => some .CVCC
  | [v, c, c] => some .CVVCC
  | _ => none

def leadOf : List K → Option Lead
  | [] => some .none
  | [c] => some .C
  | [v] => some .V
  | [v, c] => some .VC
  | _ => none

theorem sylOf_coda (s : Syl) : sylOf s.coda = some s := by cases s <;> rfl

theorem leadOf_atoms (l : Lead) : leadOf l.atoms = some l := by cases l <;> rfl

theorem coda_of_sylOf {r : List K} {s : Syl} (h : sylOf r = some s) : s.coda = r := by
  unfold sylOf at h
  split at h <;> simp_all <;> subst_vars <;> rfl

theorem atoms_of_leadOf {r : List K} {l : Lead} (h : leadOf r = some l) : l.atoms = r := by
  unfold leadOf at h
  split at h <;> simp_all <;> subst_vars <;> rfl

/-- الجريُ: ما قبل أوّل متحرّك، وما بقي. -/
def run : List K → List K × List K
  | [] => ([], [])
  | cv :: t => ([], cv :: t)
  | k :: t => (k :: (run t).1, (run t).2)

theorem run_append (k : List K) : (run k).1 ++ (run k).2 = k := by
  induction k with
  | nil => rfl
  | cons a t ih => cases a <;> simp [run, ih]

theorem run_length (k : List K) : (run k).2.length ≤ k.length := by
  have := congrArg List.length (run_append k)
  simp at this; omega

/-- يبدأ بمتحرّكٍ أو فارغ. -/
def StartsCV : List K → Prop
  | [] => True
  | a :: _ => a = cv

theorem run_of_noCV {r rest : List K} (hr : cv ∉ r) (hrest : StartsCV rest) :
    run (r ++ rest) = (r, rest) := by
  induction r with
  | nil =>
    cases rest with
    | nil => rfl
    | cons a t => simp [StartsCV] at hrest; subst hrest; rfl
  | cons a t ih =>
    simp at hr
    obtain ⟨ha, ht⟩ := hr
    cases a with
    | cv => exact absurd rfl ha
    | v => simp [run, ih ht]
    | c => simp [run, ih ht]

theorem cv_not_mem_coda (s : Syl) : cv ∉ s.coda := by cases s <;> decide

theorem cv_not_mem_lead (l : Lead) : cv ∉ l.atoms := by cases l <;> decide

/-- المقاطعُ من سلسلةٍ تبدأ بمتحرّك. -/
def syls (k : List K) : Option (List Syl) :=
  match k with
  | [] => some []
  | cv :: t =>
    match sylOf (run t).1, syls (run t).2 with
    | some s, some ss => some (s :: ss)
    | _, _ => none
  | _ :: _ => none
termination_by k.length
decreasing_by simp; have := run_length t; omega

/-- التقطيعُ كلُّه: القطعةُ الصادرةُ ثمّ المقاطع. -/
def parse (k : List K) : Option (Lead × List Syl) :=
  match leadOf (run k).1, syls (run k).2 with
  | some l, some ss => some (l, ss)
  | _, _ => none

/-- الوصل. -/
def flat (l : Lead) (ss : List Syl) : List K := l.atoms ++ ss.flatMap Syl.atoms

theorem startsCV_flatMap (ss : List Syl) : StartsCV (ss.flatMap Syl.atoms) := by
  cases ss with
  | nil => trivial
  | cons s t => simp [Syl.atoms, StartsCV]

theorem syls_flatMap (ss : List Syl) : syls (ss.flatMap Syl.atoms) = some ss := by
  induction ss with
  | nil => simp [syls]
  | cons s t ih =>
    simp only [List.flatMap_cons, Syl.atoms, List.cons_append]
    rw [syls]
    rw [run_of_noCV (cv_not_mem_coda s) (startsCV_flatMap t)]
    simp [sylOf_coda, ih]

theorem parse_flat (l : Lead) (ss : List Syl) : parse (flat l ss) = some (l, ss) := by
  unfold parse flat
  rw [run_of_noCV (cv_not_mem_lead l) (startsCV_flatMap ss)]
  simp [leadOf_atoms, syls_flatMap]

theorem flatMap_of_syls : ∀ (k : List K) (ss : List Syl),
    syls k = some ss → ss.flatMap Syl.atoms = k := by
  intro k
  induction k using (measure List.length).wf.induction with
  | h k ih =>
    intro ss h
    match k, h with
    | [], h => simp [syls] at h; subst h; rfl
    | cv :: t, h =>
      rw [syls] at h
      split at h
      · rename_i s ss' hs hss
        simp at h; subst h
        have hlt : (run t).2.length < (cv :: t).length := by
          have := run_length t; simp; omega
        have := ih _ hlt ss' hss
        simp only [List.flatMap_cons, Syl.atoms, coda_of_sylOf hs, this,
          List.cons_append, run_append]
      · simp at h
    | v :: t, h => simp [syls] at h
    | c :: t, h => simp [syls] at h

theorem flat_parse {k : List K} {l : Lead} {ss : List Syl} (h : parse k = some (l, ss)) :
    flat l ss = k := by
  unfold parse at h
  split at h
  · rename_i l' ss' hl hss
    simp at h; obtain ⟨rfl, rfl⟩ := h
    unfold flat
    rw [atoms_of_leadOf hl, flatMap_of_syls _ _ hss, run_append]
  · simp at h

theorem flat_injective {l l' : Lead} {ss ss' : List Syl} (h : flat l ss = flat l' ss') :
    l = l' ∧ ss = ss' := by
  have a := parse_flat l ss
  rw [h, parse_flat] at a
  simp at a
  exact ⟨a.1.symm, a.2.symm⟩

end A116.Stages
