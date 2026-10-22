import Std

/-!
The declared NABT alphabet is the 28 traditional carriers from alif to ya,
followed by hamza. States are fatha, damma, kasra, sukun. These declarations
are a versioned representation contract, not a theorem about recorded sound.
-/
namespace Nabt

abbrev Carrier := Fin 29
abbrev Mark := Fin 4
abbrev Atom := Fin 116

structure Cell where
  carrier : Carrier
  mark : Mark
  deriving DecidableEq, Repr

def Cell.encode (c : Cell) : Atom :=
  ⟨4 * c.carrier.val + c.mark.val, by have := c.carrier.isLt; have := c.mark.isLt; omega⟩

def Cell.decode (a : Atom) : Cell :=
  ⟨⟨a.val / 4, by have := a.isLt; omega⟩,
   ⟨a.val % 4, Nat.mod_lt _ (by decide)⟩⟩

theorem Cell.decode_encode (c : Cell) : Cell.decode (Cell.encode c) = c := by
  cases c with
  | mk carrier mark =>
    simp only [Cell.encode, Cell.decode]
    congr 1 <;> apply Fin.ext
    · change (4 * carrier.val + mark.val) / 4 = carrier.val
      have := mark.isLt; omega
    · change (4 * carrier.val + mark.val) % 4 = mark.val
      have := mark.isLt; omega

theorem Cell.encode_decode (a : Atom) : Cell.encode (Cell.decode a) = a := by
  apply Fin.ext
  simp only [Cell.encode, Cell.decode]
  omega

theorem Cell.encode_injective : Function.Injective Cell.encode := by
  intro x y h
  have h' := congrArg Cell.decode h
  simpa only [Cell.decode_encode] using h'

/-- Local slot numbers are meaningful only inside their source/version frame. -/
def occurrenceNumber (position : Nat) (a : Atom) : Nat := 116 * position + a.val

theorem occurrenceNumber_injective {p q : Nat} {a b : Atom}
    (h : occurrenceNumber p a = occurrenceNumber q b) : p = q ∧ a = b := by
  have ha := a.isLt
  have hb := b.isLt
  have hp : p = q := by simp only [occurrenceNumber] at h; omega
  refine ⟨hp, Fin.ext ?_⟩
  simp only [occurrenceNumber] at h
  omega

structure Occurrence where
  source : Nat
  analysisVersion : Nat
  position : Nat
  atom : Atom
  deriving DecidableEq, Repr

theorem occurrence_preserves_source {x y : Occurrence} (h : x = y) : x.source = y.source :=
  congrArg Occurrence.source h

theorem occurrence_distinct_sources {x y : Occurrence} (h : x.source ≠ y.source) : x ≠ y := by
  intro he
  exact h (occurrence_preserves_source he)

def canonicalCarriers : List String :=
  ["ا", "ب", "ت", "ث", "ج", "ح", "خ", "د", "ذ", "ر", "ز", "س", "ش", "ص", "ض",
   "ط", "ظ", "ع", "غ", "ف", "ق", "ك", "ل", "م", "ن", "ه", "و", "ي", "ء"]

theorem canonical_carriers_size : canonicalCarriers.length = 29 := by decide
theorem canonical_carriers_nodup : canonicalCarriers.Nodup := by decide

end Nabt
