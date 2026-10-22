import Nabt.Cell

/-!
An injective bijective-base-116 sequence address. The public address is
big-endian. Internally, `little` makes the inverse proof structurally simple.
This is an arithmetic identity, independent of the linguistic license.
-/
namespace Nabt.Sequence

def little : List Atom → Nat
  | [] => 0
  | a :: xs => 1 + a.val + 116 * little xs

def decodeAux : Nat → Nat → List Atom
  | 0, _ => []
  | fuel + 1, n =>
    if n = 0 then []
    else ⟨(n - 1) % 116, Nat.mod_lt _ (by decide)⟩ :: decodeAux fuel ((n - 1) / 116)

def encode (xs : List Atom) : Nat := little xs.reverse
def decode (n : Nat) : List Atom := (decodeAux n n).reverse

theorem decodeAux_little : ∀ (xs : List Atom) (fuel : Nat),
    little xs ≤ fuel → decodeAux fuel (little xs) = xs
  | [], fuel, _ => by cases fuel <;> simp [little, decodeAux]
  | a :: xs, fuel, hf => by
    have hfpos : 0 < fuel := by simp only [little] at hf; omega
    obtain ⟨f, rfl⟩ : ∃ f, fuel = f + 1 := ⟨fuel - 1, by omega⟩
    have hne : little (a :: xs) ≠ 0 := by simp [little]
    have hr : (little (a :: xs) - 1) % 116 = a.val := by
      simp only [little]
      have := a.isLt
      omega
    have hq : (little (a :: xs) - 1) / 116 = little xs := by
      simp only [little]
      have := a.isLt
      omega
    have ht : little xs ≤ f := by simp only [little] at hf; omega
    simp only [decodeAux, hne, ↓reduceIte, hq]
    rw [decodeAux_little xs f ht]
    congr 1
    apply Fin.ext
    exact hr

theorem decode_encode (xs : List Atom) : decode (encode xs) = xs := by
  simp only [decode, encode, decodeAux_little _ _ (Nat.le_refl _), List.reverse_reverse]

theorem encode_injective : Function.Injective encode := by
  intro x y h
  have := congrArg decode h
  simpa only [decode_encode] using this

theorem little_decodeAux : ∀ (fuel n : Nat),
    n ≤ fuel → little (decodeAux fuel n) = n
  | 0, n, h => by
    have hn : n = 0 := by omega
    subst n
    rfl
  | fuel + 1, n, h => by
    by_cases hn : n = 0
    · simp [decodeAux, hn, little]
    · have hq : (n - 1) / 116 ≤ fuel := by omega
      simp only [decodeAux, hn, ↓reduceIte, little]
      rw [little_decodeAux fuel ((n - 1) / 116) hq]
      omega

theorem encode_decode (n : Nat) : encode (decode n) = n := by
  simp only [encode, decode, List.reverse_reverse, little_decodeAux _ _ (Nat.le_refl _)]

theorem encode_surjective : Function.Surjective encode :=
  fun n => ⟨decode n, encode_decode n⟩

theorem codec_bijective : Function.Injective encode ∧ Function.Surjective encode :=
  ⟨encode_injective, encode_surjective⟩

theorem little_append (xs ys : List Atom) :
    little (xs ++ ys) = little xs + 116 ^ xs.length * little ys := by
  induction xs with
  | nil => simp [little]
  | cons a xs ih =>
    simp only [List.cons_append, little, ih, List.length_cons, Nat.pow_succ,
      Nat.mul_add, Nat.add_assoc]
    ac_rfl

theorem encode_append (xs ys : List Atom) :
    encode (xs ++ ys) = 116 ^ ys.length * encode xs + encode ys := by
  simp only [encode, List.reverse_append, little_append, List.length_reverse]
  omega

theorem encode_singleton (a : Atom) : encode [a] = a.val + 1 := by
  simp [encode, little, Nat.add_comm]

theorem encode_push (xs : List Atom) (a : Atom) :
    encode (xs ++ [a]) = 116 * encode xs + a.val + 1 := by
  rw [encode_append, encode_singleton]
  simp [Nat.add_assoc]

theorem kataba_number : encode [⟨84, by decide⟩, ⟨8, by decide⟩, ⟨4, by decide⟩] = 1144809 := by decide
theorem kutiba_number : encode [⟨85, by decide⟩, ⟨10, by decide⟩, ⟨4, by decide⟩] = 1158497 := by decide

end Nabt.Sequence
