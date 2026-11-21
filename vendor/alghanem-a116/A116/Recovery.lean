/-!
# استردادُ التمدّدات — ما يفعله الدخولُ بالنصّ مبرهَنًا

منقولٌ من `alghanem-constitution/legacy/RecoveryMetric.lean` (شطرُه الذي لا يحتاج Mathlib)
بعد إصلاح برهانين لم يُبنيا على هذه النواة. كلُّ تمدّدٍ يفعله الدخولُ بالرسم — الشدّةُ إلى
ساكنٍ ومتحرّك، والتنوينُ إلى حركةٍ ونونٍ ساكنة، ومقعدُ الهمزة إلى همزة — تعديلٌ له سجلّ،
و`restoreEdit` يعيد الأصلَ بعينه (`edit_roundtrip`). وبلا سجلٍّ لا يُستردّ المقعد
(`no_seat_recovery_from_hamza_alone`): فالبقيّةُ في الشهادة ليست ترفًا.

ولا يُبرهَن هنا أنّ `canonical116.bridge` ينفّذ هذه التمدّدات بعينها؛ ذلك ما تفحصه المطابقة.
-/

namespace A116.Recovery



-- Generic lossless patch record: removed material and edit coordinates.
structure EditRecord (α : Type) where
  start : Nat
  insertedLength : Nat
  removed : List α

def restoreEdit (out : List α) (r : EditRecord α) : List α :=
  out.take r.start ++ r.removed ++ out.drop (r.start + r.insertedLength)

theorem edit_roundtrip (left removed inserted right : List α) :
    restoreEdit (left ++ (inserted ++ right))
      ⟨left.length, inserted.length, removed⟩ = left ++ removed ++ right := by
  unfold restoreEdit
  simp only
  have h1 : List.take left.length (left ++ (inserted ++ right)) = left := by
    rw [List.take_append_of_le_length (Nat.le_refl _), List.take_length]
  have h2 : List.drop (left.length + inserted.length) (left ++ (inserted ++ right)) = right := by
    rw [List.drop_append, List.drop_of_length_le (by omega), List.nil_append,
      List.drop_append, List.drop_of_length_le (by omega), List.nil_append]
    have : left.length + inserted.length - left.length - inserted.length = 0 := by omega
    rw [this, List.drop_zero]
  rw [h1, h2]

-- Four representation operations have distinct linguistic licensing obligations.
-- The following instantiations prove restoration, not those obligations.
inductive Sign where
  | consonant : Fin 29 → Sign
  | vowel : Fin 3 → Sign
  | sukun : Sign
  | shadda : Sign
  | tanwin : Fin 3 → Sign
  | hamza : Sign
  | hamzaSeat : Fin 5 → Sign
  deriving DecidableEq

def doubled (c : Fin 29) (v : Fin 3) : List Sign :=
  [.consonant c, .sukun, .consonant c, .vowel v]
def geminated (c : Fin 29) (v : Fin 3) : List Sign :=
  [.consonant c, .shadda, .vowel v]

theorem shadda_restore (l r : List Sign) (c : Fin 29) (v : Fin 3) :
    restoreEdit (l ++ (geminated c v ++ r))
      ⟨l.length, (geminated c v).length, doubled c v⟩ = l ++ doubled c v ++ r :=
  edit_roundtrip l (doubled c v) (geminated c v) r

-- 'noon' is a parameter: the carrier mapping is an external explicit convention.
theorem tanwin_restore (l r : List Sign) (c noon : Fin 29) (v : Fin 3) :
    restoreEdit (l ++ ([.consonant c, .tanwin v] ++ r))
      ⟨l.length, 2, [.consonant c, .vowel v, .consonant noon, .sukun]⟩ =
      l ++ [.consonant c, .vowel v, .consonant noon, .sukun] ++ r :=
  edit_roundtrip l _ _ r

theorem hamza_restore (l r : List Sign) (seat : Fin 5) :
    restoreEdit (l ++ ([.hamza] ++ r))
      ⟨l.length, 1, [.hamzaSeat seat]⟩ = l ++ [.hamzaSeat seat] ++ r :=
  edit_roundtrip l _ _ r

theorem ilal_edit_restore (l source target r : List Sign) :
    restoreEdit (l ++ (target ++ r))
      ⟨l.length, target.length, source⟩ = l ++ source ++ r :=
  edit_roundtrip l source target r

-- Without residual information, distinct seated hamzas collapse.
def eraseSeat (_ : Fin 5) : Sign := .hamza

theorem no_seat_recovery_from_hamza_alone :
    ¬ ∃ d : Sign → Fin 5, ∀ s, d (eraseSeat s) = s := by
  rintro ⟨d, h⟩
  have h0 := h (0 : Fin 5)
  have h1 := h (1 : Fin 5)
  have impossible : (0 : Fin 5) = 1 := h0.symm.trans h1
  exact absurd impossible (by decide)

theorem restoration_forces_fiber_separation
    (f : α → β) (residual : α → γ) (decode : β × γ → α)
    (h : ∀ x, decode (f x, residual x) = x)
    {x y : α} (hf : f x = f y) (hr : residual x = residual y) : x = y := by
  calc
    x = decode (f x, residual x) := (h x).symm
    _ = decode (f y, residual y) := by rw [hf, hr]
    _ = y := h y

theorem compose_restoration (f : α → β) (g : β → γ)
    (df : β → α) (dg : γ → β)
    (hf : ∀ x, df (f x) = x) (hg : ∀ y, dg (g y) = y) (x : α) :
    df (dg (g (f x))) = x := by rw [hg, hf]


end A116.Recovery
