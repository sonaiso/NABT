import A116.Tarkib
import A116.TawrithSitta
import A116.FractalTarkibData

/-!
# فراكتالُ التركيب: الزوجُ زوجُ ألفاظٍ بأقسامها (ADR ٨٠)

نصُّ المالك (2026-10-16): «بعد التركيب يكون الزوجُ لا عددين أوّليّين، بل زوجَ ألفاظ: زوجَ اسمٍ واسم، أو اسمٍ
وفعل، أو اسمٍ وحرف، أو فعلٍ وحرف … هكذا يكون فراكتالُ التركيب».

* **مؤثّرُ الأزواج واحدٌ في الطبقتين** (`NizamHadd.azwaj`): في الخانة أزواجُ الأدوار (`strictB_is_nizam`)،
  وفي التركيب أزواجُ الأقسام (`zawjat`). وقانونُه لكلّ طبقة: أزواجُ القائمة عددُها طولُها ناقصًا واحدًا
  (`azwaj_length`)، وأزواجُ الموصول أزواجُ الأولى وزوجُ الحدّ وأزواجُ الثانية (`azwaj_seam`) — فالحدُّ بين
  الكلمتين في التركيب زوجُ ألفاظٍ جديد كما الحدُّ بين الخانتين زوجُ أدوار.
* **الأزواجُ تسعة** (`naw_tisa`): كلُّ زوجٍ من (اسم، فعل، حرف)²؛ والترخيصُ لا يرى القسم
  (`Tarkib.licence_blind_to_qism`)، فالزوجُ في التركيب يحمل **الإسناد** لا الترخيص.
* **الإسنادُ توريث** (`isnadT`): الحالُ الموروثُ آخرُ قسمٍ وهل وقع إسناد، والزوجان المسندان اسمٌ على اسم
  وفعلٌ على اسم (`Tarkib.ismiyya`، `filiyya`)؛ وترخيصُه هو إسنادُ `Tarkib` بعينه (`isnadT_iff`)، وإسنادُ
  الموصول إسنادُ أحدهما أو زوجُ حدّهما (`isnad_seam`).
* **على المصحف** (`A116.FractalTarkib.ayat` من QAC المختوم): الكلماتُ والأزواج، والأنواعُ التسعة كلُّها واقعة
  بأعدادها (`azwaj_mushaf`)، والآياتُ التي فيها إسنادٌ بين متجاورين (`isnad_mushaf`).
-/

namespace A116.FractalTarkib

open A116 A116.Tarkib A116.NizamHadd A116.Tawrith

variable {α : Type}

/-! ## ١. مؤثّرُ الأزواج لكلّ طبقة -/

theorem azwaj_length : ∀ l : List α, (azwaj l).length = l.length - 1
  | [] => rfl
  | [_] => rfl
  | a :: b :: t => by
    show ((a, b) :: azwaj (b :: t)).length = _
    rw [List.length_cons, azwaj_length (b :: t)]
    simp

/-- **زوجُ الحدّ**: أزواجُ الموصول أزواجُ الأولى، ثمّ زوجُ آخرِها بأوّل الثانية، ثمّ أزواجُ الثانية. -/
theorem azwaj_seam : ∀ (a : α) (l : List α) (b : α) (m : List α),
    azwaj ((a :: l) ++ (b :: m)) = azwaj (a :: l) ++ ((a :: l).getLast (by simp), b) :: azwaj (b :: m)
  | a, [], b, m => rfl
  | a, c :: l, b, m => by
    show (a, c) :: azwaj ((c :: l) ++ (b :: m)) = (a, c) :: azwaj (c :: l) ++ _
    rw [azwaj_seam c l b m]
    simp [List.getLast_cons]

/-! ## ٢. الأزواجُ التسعة والإسناد -/

def qisms : List Qism := [.ism, .fil, .harf]

/-- أزواجُ الأقسام في التركيب. -/
def zawjat (t : Tarkib) : List (Qism × Qism) := azwaj (t.map Kalima.qism)

/-- **الأنواعُ تسعة**: كلُّ زوجٍ من الأقسام الثلاثة. -/
def anwa : List (Qism × Qism) := qisms.flatMap fun a => qisms.map (a, ·)

theorem naw_tisa : anwa.length = 9 ∧ anwa.Nodup ∧ ∀ p : Qism × Qism, p ∈ anwa := by
  refine ⟨rfl, by decide, ?_⟩
  rintro ⟨a, b⟩
  cases a <;> cases b <;> decide

/-- الزوجُ المسنَد: اسمٌ على اسم، أو فعلٌ على اسم. -/
def musnad : Qism → Qism → Bool
  | .ism, .ism => true
  | .fil, .ism => true
  | _, _ => false

/-- زوجُ الموروث بالقسم الجديد: مسنَدٌ إن كان قبله قسم. -/
def cont : Option Qism → Qism → Bool
  | some a, q => musnad a q
  | none, _ => false

/-- **الإسنادُ توريث**: يرث آخرَ قسمٍ وهل وقع إسناد، ويورثهما. -/
def isnadT : Tawrith Qism (Option Qism × Bool) where
  bad := (none, false)
  step p q := some (some q, p.2 || cont p.1 q)
  waqf p := p.2

/-- حكمُ الإسناد على الأقسام. -/
def isnadB (qs : List Qism) : Bool := (azwaj qs).any fun p => musnad p.1 p.2

/-- الإسنادُ من موروثٍ: بالقسم السابق إن وُجد. -/
def isnadFrom : Option Qism → List Qism → Bool
  | some a, qs => isnadB (a :: qs)
  | none, qs => isnadB qs

theorem run_isnadT : ∀ (o : Option Qism) (b : Bool) (qs : List Qism),
    ∃ o', Tawrith.run isnadT (o, b) qs = some (o', b || isnadFrom o qs)
  | o, b, [] => ⟨o, by cases o <;> simp [Tawrith.run, isnadFrom, isnadB, azwaj]⟩
  | o, b, q :: qs => by
    obtain ⟨o', h⟩ := run_isnadT (some q) (b || cont o q) qs
    refine ⟨o', ?_⟩
    rw [TawrithSitta.run_cons, show isnadT.step (o, b) q = some (some q, b || cont o q) from rfl,
      Option.bind_some, h]
    cases o with
    | none => cases qs <;> simp [isnadFrom, cont, isnadB, azwaj]
    | some a => simp [isnadFrom, cont, isnadB, azwaj, Bool.or_assoc]

/-- **ترخيصُ توريث الإسناد هو حكمُ الإسناد.** -/
theorem lic_isnadT (qs : List Qism) : lic isnadT qs = isnadB qs := by
  obtain ⟨o', h⟩ := run_isnadT none false qs
  unfold lic
  rw [show isnadT.bad = (none, false) from rfl, h]
  simp [qubul, isnadT, isnadFrom]

theorem isnadB_cons2 (a b : Qism) (t : List Qism) :
    isnadB (a :: b :: t) = (musnad a b || isnadB (b :: t)) := by
  simp [isnadB, azwaj]

/-- **وهو إسنادُ `Tarkib` بعينه.** -/
theorem isnadT_iff (t : Tarkib) : Isnad t ↔ lic isnadT (t.map Kalima.qism) = true := by
  rw [lic_isnadT]
  constructor
  · intro h
    induction h with
    | here a b rest h =>
      simp only [List.map_cons, isnadB_cons2, Bool.or_eq_true]
      left
      rcases h with ⟨ha, hb⟩ | ⟨ha, hb⟩ <;> simp [ha, hb, musnad]
    | there w t _ ih =>
      cases t with
      | nil => simp [isnadB, azwaj] at ih
      | cons b rest =>
        simp only [List.map_cons] at ih ⊢
        rw [isnadB_cons2, ih, Bool.or_true]
  · intro h
    induction t with
    | nil => simp [isnadB, azwaj] at h
    | cons a t ih =>
      cases t with
      | nil => simp [isnadB, azwaj] at h
      | cons b rest =>
        simp only [List.map_cons, isnadB_cons2, Bool.or_eq_true] at h
        rcases h with h | h
        · apply Isnad.here
          cases ha : a.qism <;> cases hb : b.qism <;> simp_all [musnad, ismiyya, filiyya]
        · exact Isnad.there a _ (ih (by simpa using h))

/-- **إسنادُ الموصول**: إسنادُ الأولى، أو زوجُ الحدّ، أو إسنادُ الثانية. -/
theorem isnad_seam (a : Qism) (l : List Qism) (b : Qism) (m : List Qism) :
    isnadB ((a :: l) ++ (b :: m)) =
      (isnadB (a :: l) || musnad ((a :: l).getLast (by simp)) b || isnadB (b :: m)) := by
  unfold isnadB
  rw [azwaj_seam]
  simp [List.any_append, Bool.or_assoc]

/-! ## ٣. على المصحف -/

def qOf : Nat → Qism
  | 0 => .ism
  | 1 => .fil
  | _ => .harf

/-- أقسامُ الآية. -/
def aya (r : List Nat) : List Qism := r.map qOf

/-- زيادةُ الخانة k في عدّاد. -/
def inc : List Nat → Nat → List Nat
  | [], _ => []
  | x :: t, 0 => (x + 1) :: t
  | x :: t, k + 1 => x :: inc t k

/-- عدُّ أزواج الآية برمز الزوج ‎3a + b‎ في طيٍّ واحد. -/
def cntPairs : List Nat → List Nat → List Nat
  | v, a :: b :: t => cntPairs (inc v (3 * a + b)) (b :: t)
  | v, _ => v

/-- **رمزُ الزوج ونوعُه**: الرمزُ k هو النوعُ ‎(qOf (k/3), qOf (k%3))‎ بترتيب `anwa`. -/
theorem ramz_naw : anwa = (List.range 9).map fun k => (qOf (k / 3), qOf (k % 3)) := by decide

set_option maxRecDepth 200000 in
/-- **الكلماتُ والأزواج**: الآيات، والكلمات، والأزواج، والأقسامُ كلُّها من الثلاثة. -/
theorem kalimat_mushaf : ayat.length = 6236 ∧ (ayat.map List.length).sum = 119842 ∧
    ayat.all (·.all (· ≤ 2)) = true := by
  decide +kernel

set_option maxRecDepth 200000 in
/-- **الإسناد**: الآياتُ التي فيها إسنادٌ بين متجاورين. -/
theorem isnad_mushaf : (ayat.filter fun r => lic isnadT (aya r)).length = 6006 := by
  decide +kernel

end A116.FractalTarkib
