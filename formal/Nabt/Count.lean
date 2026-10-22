import Nabt.Transition

/-!
Bounded counting is justified against a deliberately separate specification:
first enumerate every alphabet string of length at most `fuel`, then filter
by its computed weight and final state. Runtime memoization/ranking is a
separate implementation whose bridge must be checked explicitly.
-/
namespace Nabt.Count

variable {Q A : Type}

def allWords (alphabet : List A) : Nat → List (List A)
  | 0 => [[]]
  | f + 1 => [] :: alphabet.flatMap (fun a => (allWords alphabet f).map (a :: ·))

def acceptsAt (M : Machine Q A) (q : Q) (w : Nat) (xs : List A) : Bool :=
  decide (M.weight q xs = w) && M.final (M.run q xs)

def enumeration (M : Machine Q A) (alphabet : List A) (f w : Nat) (q : Q) : List (List A) :=
  (allWords alphabet f).filter (acceptsAt M q w)

def count (M : Machine Q A) (alphabet : List A) : Nat → Nat → Q → Nat
  | 0, w, q => if w = 0 ∧ M.final q = true then 1 else 0
  | f + 1, w, q =>
    (if w = 0 ∧ M.final q = true then 1 else 0) +
    (alphabet.map fun a => if M.cost q a ≤ w then count M alphabet f (w - M.cost q a) (M.step q a) else 0).sum

theorem acceptsAt_nil (M : Machine Q A) (q : Q) (w : Nat) :
    acceptsAt M q w [] = decide (w = 0 ∧ M.final q = true) := by
  apply Bool.eq_iff_iff.mpr
  simp only [acceptsAt, Machine.weight, Machine.run, Bool.and_eq_true, decide_eq_true_eq]
  constructor
  · rintro ⟨h, hf⟩; exact ⟨(of_decide_eq_true h).symm, hf⟩
  · rintro ⟨h, hf⟩; exact ⟨by simp [h], hf⟩

theorem acceptsAt_cons (M : Machine Q A) (q : Q) (w : Nat) (a : A) (xs : List A) :
    acceptsAt M q w (a :: xs) =
      if M.cost q a ≤ w then acceptsAt M (M.step q a) (w - M.cost q a) xs else false := by
  by_cases h : M.cost q a ≤ w
  · have he : M.cost q a + M.weight (M.step q a) xs = w ↔
        M.weight (M.step q a) xs = w - M.cost q a := by omega
    simp only [acceptsAt, Machine.weight, Machine.run, he, h, ↓reduceIte]
  · have he : ¬ M.cost q a + M.weight (M.step q a) xs = w := by omega
    simp only [acceptsAt, Machine.weight, Machine.run, he, decide_false, Bool.false_and, h, ↓reduceIte]

theorem prefix_length (M : Machine Q A) (q : Q) (w : Nat) (a : A) (xs : List (List A)) :
    ((xs.map (a :: ·)).filter (acceptsAt M q w)).length =
      if M.cost q a ≤ w then (xs.filter (acceptsAt M (M.step q a) (w - M.cost q a))).length else 0 := by
  rw [List.filter_map, List.length_map]
  by_cases h : M.cost q a ≤ w
  · simp only [h, ↓reduceIte]
    congr 1
    congr 1
    funext tail
    simpa only [Function.comp_apply, h, ↓reduceIte] using acceptsAt_cons M q w a tail
  · have he : (acceptsAt M q w ∘ (a :: ·)) = fun _ => false := by
      funext tail
      simpa only [Function.comp_apply, h, ↓reduceIte] using acceptsAt_cons M q w a tail
    rw [he]
    simp only [h, ↓reduceIte]
    induction xs with
    | nil => rfl
    | cons x xs ih => simpa only [List.filter_cons, Bool.false_eq_true, ↓reduceIte] using ih

theorem count_eq_enumeration_length (M : Machine Q A) (alphabet : List A) :
    ∀ (f w : Nat) (q : Q), count M alphabet f w q = (enumeration M alphabet f w q).length
  | 0, w, q => by
    simp only [count, enumeration, allWords, List.filter_cons, acceptsAt_nil,
      List.filter_nil, decide_eq_true_eq]
    split <;> simp_all
  | f + 1, w, q => by
    have hsum :
        (alphabet.map fun a => if M.cost q a ≤ w then count M alphabet f (w - M.cost q a) (M.step q a) else 0).sum =
        ((alphabet.flatMap fun a => (allWords alphabet f).map (a :: ·)).filter (acceptsAt M q w)).length := by
      rw [List.filter_flatMap, List.length_flatMap]
      congr 1
      apply List.map_congr_left
      intro a _
      rw [prefix_length]
      by_cases h : M.cost q a ≤ w
      · simp only [h, ↓reduceIte]
        exact count_eq_enumeration_length M alphabet f (w - M.cost q a) (M.step q a)
      · simp only [h, ↓reduceIte]
    simp only [count, enumeration, allWords, List.filter_cons]
    rw [hsum]
    simp only [acceptsAt_nil, decide_eq_true_eq]
    split <;> simp_all [Nat.add_comm]

/-- Membership specification: no accepted result can exceed the stated fuel. -/
theorem allWords_length (alphabet : List A) : ∀ (f : Nat) (xs : List A),
    xs ∈ allWords alphabet f → xs.length ≤ f
  | 0, xs, h => by simp only [allWords, List.mem_singleton] at h; subst xs; simp
  | f + 1, xs, h => by
    simp only [allWords, List.mem_cons, List.mem_flatMap, List.mem_map] at h
    rcases h with rfl | ⟨a, _, tail, ht, rfl⟩
    · simp
    · have := allWords_length alphabet f tail ht
      simp only [List.length_cons]
      omega

theorem enumeration_sound (M : Machine Q A) (alphabet : List A) (f w : Nat) (q : Q)
    (xs : List A) (h : xs ∈ enumeration M alphabet f w q) :
    xs.length ≤ f ∧ M.weight q xs = w ∧ M.Licensed q xs := by
  simp only [enumeration, List.mem_filter] at h
  refine ⟨allWords_length alphabet f xs h.1, ?_⟩
  simpa only [acceptsAt, Bool.and_eq_true, decide_eq_true_eq, Machine.Licensed] using h.2

/-- The specification covers every bounded string over the declared alphabet. -/
theorem allWords_complete (alphabet : List A) : ∀ (f : Nat) (xs : List A),
    xs.length ≤ f → (∀ a ∈ xs, a ∈ alphabet) → xs ∈ allWords alphabet f
  | 0, [], _, _ => by simp [allWords]
  | 0, _ :: _, h, _ => by simp at h
  | _ + 1, [], _, _ => by simp [allWords]
  | f + 1, a :: xs, h, ha => by
    simp only [allWords, List.mem_cons]
    right
    apply List.mem_flatMap.mpr
    refine ⟨a, ha a (by simp), ?_⟩
    apply List.mem_map.mpr
    refine ⟨xs, allWords_complete alphabet f xs ?_ ?_, rfl⟩
    · simp only [List.length_cons] at h; omega
    · intro b hb; exact ha b (by simp [hb])

theorem enumeration_complete (M : Machine Q A) (alphabet : List A) (f w : Nat) (q : Q)
    (xs : List A) (hlen : xs.length ≤ f) (halpha : ∀ a ∈ xs, a ∈ alphabet)
    (hweight : M.weight q xs = w) (hfinal : M.Licensed q xs) :
    xs ∈ enumeration M alphabet f w q := by
  apply List.mem_filter.mpr
  refine ⟨allWords_complete alphabet f xs hlen halpha, ?_⟩
  simp [acceptsAt, hweight, hfinal]

/-- Unique letters produce unique strings: list length is then cardinality. -/
theorem allWords_nodup (alphabet : List A) (ha : alphabet.Nodup) :
    ∀ f, (allWords alphabet f).Nodup
  | 0 => by simp [allWords]
  | f + 1 => by
    rw [allWords, List.nodup_cons]
    constructor
    · simp
    · apply List.pairwise_flatMap.mpr
      constructor
      · intro a _
        exact (allWords_nodup alphabet ha f).map (a :: ·)
          (fun _ _ h hxy => h (List.cons.inj hxy).2)
      · apply ha.imp
        intro a b hab x hx y hy hxy
        obtain ⟨xs, _, rfl⟩ := List.mem_map.mp hx
        obtain ⟨ys, _, rfl⟩ := List.mem_map.mp hy
        exact hab (List.cons.inj hxy).1

theorem enumeration_nodup (M : Machine Q A) (alphabet : List A) (ha : alphabet.Nodup)
    (f w : Nat) (q : Q) : (enumeration M alphabet f w q).Nodup :=
  (allWords_nodup alphabet ha f).filter _

/-- Executable reference ranking. The runtime's memoized ranking is separately
tested against this lexicographic prefix enumeration, not assumed equivalent. -/
def rankSpec [DecidableEq A] (M : Machine Q A) (alphabet : List A) (f w : Nat) (q : Q)
    (xs : List A) : Option Nat :=
  let es := enumeration M alphabet f w q
  if xs ∈ es then some (es.idxOf xs) else none

def unrankSpec (M : Machine Q A) (alphabet : List A) (f w : Nat) (q : Q)
    (rank : Nat) : Option (List A) :=
  (enumeration M alphabet f w q)[rank]?

theorem unrank_rankSpec [DecidableEq A] (M : Machine Q A) (alphabet : List A)
    (f w : Nat) (q : Q) (xs : List A) (h : xs ∈ enumeration M alphabet f w q) :
    unrankSpec M alphabet f w q ((enumeration M alphabet f w q).idxOf xs) = some xs := by
  apply List.getElem?_eq_some_iff.mpr
  exact ⟨List.idxOf_lt_length_of_mem h, List.getElem_idxOf _⟩

theorem rank_unrankSpec [DecidableEq A] (M : Machine Q A) (alphabet : List A)
    (ha : alphabet.Nodup) (f w : Nat) (q : Q) (rank : Nat) (xs : List A)
    (h : unrankSpec M alphabet f w q rank = some xs) :
    rankSpec M alphabet f w q xs = some rank := by
  obtain ⟨hi, hx⟩ := List.getElem?_eq_some_iff.mp h
  have hmem : xs ∈ enumeration M alphabet f w q := hx ▸ List.getElem_mem hi
  simp only [rankSpec, hmem, ↓reduceIte]
  rw [← hx, (enumeration_nodup M alphabet ha f w q).idxOf_getElem rank hi]

theorem rank_bounded [DecidableEq A] (M : Machine Q A) (alphabet : List A)
    (f w : Nat) (q : Q) (xs : List A) (h : xs ∈ enumeration M alphabet f w q) :
    (enumeration M alphabet f w q).idxOf xs < count M alphabet f w q := by
  rw [count_eq_enumeration_length]
  exact List.idxOf_lt_length_of_mem h

end Nabt.Count
