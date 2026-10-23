import Std

/-!
# Exact typed pattern application and checked inverse readings

`Root n` supplies a character for each typed radical slot. `fill` is total.
`recover` proposes characters at the first occurrences of slots, then accepts
only a complete pattern whose entire replay equals the supplied text. Thus
literal characters, repeated slots, and full length are checked together.
No character or root is inferred from an absent slot.

These are general string contracts, not lexical or linguistic classification
theorems. A retained root and pattern are shape candidates. Their names do not
establish attestation, meaning, word kind, tense in context, or syntactic case.
The Python boundary separately checks its versioned Arabic radical carrier.
Multiple patterns can license the same string, and all such readings remain.
-/

namespace Nabt.Derivation

def lawId : String := "nabt.derivation-patterns.v1"
def alphabetId : String := "nabt.arabic-radicals28.v1"
def profile : String := "stem_exact_v1"

inductive Token (n : Nat) where
  | literal (value : Char)
  | slot (index : Fin n)
  deriving DecidableEq, Repr

abbrev Pattern (n : Nat) := List (Token n)
abbrev Root (n : Nat) := Fin n → Char

def evaluate (root : Root n) : Token n → Char
  | .literal value => value
  | .slot index => root index

def fill (pattern : Pattern n) (root : Root n) : List Char :=
  pattern.map (evaluate root)

def Complete (pattern : Pattern n) : Prop :=
  ∀ index : Fin n, Token.slot index ∈ pattern

instance (pattern : Pattern n) : Decidable (Complete pattern) :=
  inferInstanceAs (Decidable (∀ index : Fin n, Token.slot index ∈ pattern))

/-- An untrusted first-occurrence proposal. Only `recover` validates it. -/
def firstSlot (index : Fin n) : Pattern n → List Char → Option Char
  | .slot other :: rest, value :: tail =>
      if index = other then some value else firstSlot index rest tail
  | .literal _ :: rest, _ :: tail => firstSlot index rest tail
  | _, _ => none

def proposedRoot (pattern : Pattern n) (text : List Char) : Root n :=
  fun index => (firstSlot index pattern text).getD '\x00'

/-- Missing slots never acquire authority from `getD`: completeness and the
entire replay are necessary for acceptance. -/
def recover (pattern : Pattern n) (text : List Char) : Option (Root n) :=
  let root := proposedRoot pattern text
  if Complete pattern ∧ fill pattern root = text then some root else none

theorem fill_length (pattern : Pattern n) (root : Root n) :
    (fill pattern root).length = pattern.length := by
  simp [fill]

theorem fill_append (left right : Pattern n) (root : Root n) :
    fill (left ++ right) root = fill left root ++ fill right root := by
  simp [fill]

theorem firstSlot_fill (index : Fin n) (pattern : Pattern n) (root : Root n) :
    firstSlot index pattern (fill pattern root) =
      if Token.slot index ∈ pattern then some (root index) else none := by
  induction pattern with
  | nil => simp [firstSlot]
  | cons token rest ih =>
      cases token with
      | literal value => simpa [firstSlot, fill, evaluate] using ih
      | slot other =>
          by_cases h : index = other
          · subst other
            simp [firstSlot, fill, evaluate]
          · simpa [firstSlot, fill, evaluate, h] using ih

theorem proposedRoot_fill_complete (pattern : Pattern n) (root : Root n)
    (complete : Complete pattern) :
    proposedRoot pattern (fill pattern root) = root := by
  funext index
  simp [proposedRoot, firstSlot_fill, complete index]

theorem recover_refills (pattern : Pattern n) (text : List Char) (root : Root n)
    (accepted : recover pattern text = some root) : fill pattern root = text := by
  dsimp only [recover] at accepted
  split at accepted
  next valid =>
    have same := Option.some.inj accepted
    rw [← same]
    exact valid.2
  next => simp at accepted

theorem recover_requires_complete (pattern : Pattern n) (text : List Char)
    (root : Root n) (accepted : recover pattern text = some root) :
    Complete pattern := by
  dsimp only [recover] at accepted
  split at accepted
  next valid => exact valid.1
  next => simp at accepted

theorem recover_fill (pattern : Pattern n) (root : Root n)
    (complete : Complete pattern) :
    recover pattern (fill pattern root) = some root := by
  simp [recover, proposedRoot_fill_complete pattern root complete, complete]

theorem recover_exact_iff (pattern : Pattern n) (text : List Char) (root : Root n) :
    recover pattern text = some root ↔ Complete pattern ∧ fill pattern root = text := by
  constructor
  · intro accepted
    exact ⟨recover_requires_complete pattern text root accepted,
      recover_refills pattern text root accepted⟩
  · rintro ⟨complete, rfl⟩
    exact recover_fill pattern root complete

theorem incomplete_rejected (pattern : Pattern n) (text : List Char)
    (missing : ¬ Complete pattern) : recover pattern text = none := by
  simp [recover, missing]

theorem fill_at (pattern : Pattern n) (root : Root n) (index : Nat) :
    (fill pattern root)[index]? = (pattern[index]?).map (evaluate root) := by
  simp [fill]

theorem accepted_literal_agrees (pattern : Pattern n) (text : List Char)
    (root : Root n) (index : Nat) (value : Char)
    (literal : pattern[index]? = some (.literal value))
    (accepted : recover pattern text = some root) : text[index]? = some value := by
  rw [← recover_refills pattern text root accepted, fill_at, literal]
  rfl

theorem mismatching_literal_rejected (pattern : Pattern n) (text : List Char)
    (index : Nat) (value : Char)
    (literal : pattern[index]? = some (.literal value))
    (mismatch : text[index]? ≠ some value) : recover pattern text = none := by
  cases result : recover pattern text with
  | none => rfl
  | some root => exact False.elim (mismatch
      (accepted_literal_agrees pattern text root index value literal result))

theorem repeated_slots_agree (pattern : Pattern n) (text : List Char)
    (root : Root n) (left right : Nat) (slot : Fin n)
    (atLeft : pattern[left]? = some (.slot slot))
    (atRight : pattern[right]? = some (.slot slot))
    (accepted : recover pattern text = some root) : text[left]? = text[right]? := by
  rw [← recover_refills pattern text root accepted, fill_at, fill_at, atLeft, atRight]

theorem mismatching_length_rejected (pattern : Pattern n) (text : List Char)
    (mismatch : text.length ≠ pattern.length) : recover pattern text = none := by
  cases result : recover pattern text with
  | none => rfl
  | some root =>
      apply False.elim
      apply mismatch
      rw [← recover_refills pattern text root result, fill_length]

/-- Uniqueness holds for a fixed complete pattern; it does not compare
different patterns. -/
theorem fill_injective_complete (pattern : Pattern n) (complete : Complete pattern)
    (left right : Root n) (same : fill pattern left = fill pattern right) : left = right := by
  have proposed := congrArg (proposedRoot pattern) same
  simpa [proposedRoot_fill_complete pattern left complete,
    proposedRoot_fill_complete pattern right complete] using proposed

def readings (patterns : List (Pattern n)) (text : List Char) :
    List (Pattern n × Root n) :=
  patterns.filterMap fun pattern => (recover pattern text).map fun root => (pattern, root)

theorem mem_readings_iff (patterns : List (Pattern n)) (text : List Char)
    (pattern : Pattern n) (root : Root n) :
    (pattern, root) ∈ readings patterns text ↔
      pattern ∈ patterns ∧ recover pattern text = some root := by
  simp only [readings, List.mem_filterMap]
  constructor
  · rintro ⟨found, member, recovered⟩
    cases result : recover found text with
    | none => simp [result] at recovered
    | some value =>
        simp only [result, Option.map_some, Option.some.injEq, Prod.mk.injEq] at recovered
        rcases recovered with ⟨rfl, rfl⟩
        exact ⟨member, result⟩
  · rintro ⟨member, recovered⟩
    exact ⟨pattern, member, by simp [recovered]⟩

theorem readings_sound (patterns : List (Pattern n)) (text : List Char)
    (pattern : Pattern n) (root : Root n)
    (member : (pattern, root) ∈ readings patterns text) :
    Complete pattern ∧ fill pattern root = text := by
  exact (recover_exact_iff pattern text root).mp
    ((mem_readings_iff patterns text pattern root).mp member).2

theorem readings_complete (patterns : List (Pattern n)) (pattern : Pattern n)
    (root : Root n) (member : pattern ∈ patterns) (complete : Complete pattern) :
    (pattern, root) ∈ readings patterns (fill pattern root) := by
  exact (mem_readings_iff patterns (fill pattern root) pattern root).mpr
    ⟨member, recover_fill pattern root complete⟩

theorem no_patterns_no_readings (text : List Char) :
    readings ([] : List (Pattern n)) text = [] := by
  rfl

theorem retained_readings_monotone (before after : List (Pattern n)) (text : List Char)
    (included : ∀ pattern, pattern ∈ before → pattern ∈ after)
    (pattern : Pattern n) (root : Root n)
    (member : (pattern, root) ∈ readings before text) :
    (pattern, root) ∈ readings after text := by
  rw [mem_readings_iff] at member ⊢
  exact ⟨included pattern member.1, member.2⟩

/-- Catalog metadata names a bounded shape reading, without granting semantic
or lexical authority. The dependent token list preserves the declared arity. -/
structure CatalogPattern where
  id : String
  label : String
  arity : Nat
  tokens : Pattern arity
  family : String
  form : String
  voice : String
  augmentation : String
  sourceContract : String
  sourceKind : String
  rootDomain : String
  endings : List Char


/-!
## Bounded catalog and provenance

The first 31 stems preserve every literal character and the omitted final
mark of Alghanem Ishtiqaq, commit
`9d8fa03a51f894416e0abaf3b6821c5ae6441dcd`,
`formal/a116/A116/Ishtiqaq.lean`. They are exact source templates, not an
assertion that every substituted root has that surface realization.

The two nominal stems are NEW_NOMINAL_PROJECTION from QiraaMadlul: Unicode
orthography drops the source's phonemic madd sukun and final mark. The eleven
imperfect stems are NEW_SOUND_PROJECTION from Mudari.body: they compress
repeated consonants to shadda, omit madd sukun and the final mark, and restrict
the runtime root domain to sound, non-doubled triliterals. They do not inherit
upstream weak-root, hamza, assimilation, or general ilal claims.

Endings are optional separate boundary metadata. No boundary establishes
case, tense, or word kind. Fathatanwin plus its supporting alif is deferred.
There is no independent future template. Catalog extension belongs in a
separate module and appends to corePatterns without changing these 44 rows.

The adapted Ishtiqaq templates carry the upstream license:

MIT License

Copyright (c) 2026 Saleh1967

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
-/

def t_past_I_a : Pattern 3 := [.slot 0, .literal 'َ', .slot 1, .literal 'َ', .slot 2]

def t_past_I_i : Pattern 3 := [.slot 0, .literal 'َ', .slot 1, .literal 'ِ', .slot 2]

def t_past_I_u : Pattern 3 := [.slot 0, .literal 'َ', .slot 1, .literal 'ُ', .slot 2]

def t_past_II : Pattern 3 := [.slot 0, .literal 'َ', .slot 1, .literal 'ّ', .literal 'َ', .slot 2]

def t_past_III : Pattern 3 := [.slot 0, .literal 'َ', .literal 'ا', .slot 1, .literal 'َ', .slot 2]

def t_past_IV : Pattern 3 := [.literal 'ء', .literal 'َ', .slot 0, .literal 'ْ', .slot 1, .literal 'َ', .slot 2]

def t_past_V : Pattern 3 := [.literal 'ت', .literal 'َ', .slot 0, .literal 'َ', .slot 1, .literal 'ّ', .literal 'َ', .slot 2]

def t_past_VI : Pattern 3 := [.literal 'ت', .literal 'َ', .slot 0, .literal 'َ', .literal 'ا', .slot 1, .literal 'َ', .slot 2]

def t_past_VII : Pattern 3 := [.literal 'ا', .literal 'ن', .literal 'ْ', .slot 0, .literal 'َ', .slot 1, .literal 'َ', .slot 2]

def t_past_VIII : Pattern 3 := [.literal 'ا', .slot 0, .literal 'ْ', .literal 'ت', .literal 'َ', .slot 1, .literal 'َ', .slot 2]

def t_past_X : Pattern 3 := [.literal 'ا', .literal 'س', .literal 'ْ', .literal 'ت', .literal 'َ', .slot 0, .literal 'ْ', .slot 1, .literal 'َ', .slot 2]

def t_passive_I : Pattern 3 := [.slot 0, .literal 'ُ', .slot 1, .literal 'ِ', .slot 2]

def t_passive_II : Pattern 3 := [.slot 0, .literal 'ُ', .slot 1, .literal 'ّ', .literal 'ِ', .slot 2]

def t_passive_III : Pattern 3 := [.slot 0, .literal 'ُ', .literal 'و', .slot 1, .literal 'ِ', .slot 2]

def t_passive_IV : Pattern 3 := [.literal 'ء', .literal 'ُ', .slot 0, .literal 'ْ', .slot 1, .literal 'ِ', .slot 2]

def t_passive_V : Pattern 3 := [.literal 'ت', .literal 'ُ', .slot 0, .literal 'ُ', .slot 1, .literal 'ّ', .literal 'ِ', .slot 2]

def t_passive_VI : Pattern 3 := [.literal 'ت', .literal 'ُ', .slot 0, .literal 'ُ', .literal 'و', .slot 1, .literal 'ِ', .slot 2]

def t_passive_VII : Pattern 3 := [.literal 'ا', .literal 'ن', .literal 'ْ', .slot 0, .literal 'ُ', .slot 1, .literal 'ِ', .slot 2]

def t_passive_VIII : Pattern 3 := [.literal 'ا', .slot 0, .literal 'ْ', .literal 'ت', .literal 'ُ', .slot 1, .literal 'ِ', .slot 2]

def t_passive_X : Pattern 3 := [.literal 'ا', .literal 'س', .literal 'ْ', .literal 'ت', .literal 'ُ', .slot 0, .literal 'ْ', .slot 1, .literal 'ِ', .slot 2]

def t_imperative_I_a : Pattern 3 := [.literal 'ا', .slot 0, .literal 'ْ', .slot 1, .literal 'َ', .slot 2]

def t_imperative_I_i : Pattern 3 := [.literal 'ا', .slot 0, .literal 'ْ', .slot 1, .literal 'ِ', .slot 2]

def t_imperative_I_u : Pattern 3 := [.literal 'ا', .slot 0, .literal 'ْ', .slot 1, .literal 'ُ', .slot 2]

def t_imperative_II : Pattern 3 := [.slot 0, .literal 'َ', .slot 1, .literal 'ّ', .literal 'ِ', .slot 2]

def t_imperative_III : Pattern 3 := [.slot 0, .literal 'َ', .literal 'ا', .slot 1, .literal 'ِ', .slot 2]

def t_imperative_IV : Pattern 3 := [.literal 'ء', .literal 'َ', .slot 0, .literal 'ْ', .slot 1, .literal 'ِ', .slot 2]

def t_imperative_V : Pattern 3 := [.literal 'ت', .literal 'َ', .slot 0, .literal 'َ', .slot 1, .literal 'ّ', .literal 'َ', .slot 2]

def t_imperative_VI : Pattern 3 := [.literal 'ت', .literal 'َ', .slot 0, .literal 'َ', .literal 'ا', .slot 1, .literal 'َ', .slot 2]

def t_imperative_VII : Pattern 3 := [.literal 'ا', .literal 'ن', .literal 'ْ', .slot 0, .literal 'َ', .slot 1, .literal 'ِ', .slot 2]

def t_imperative_VIII : Pattern 3 := [.literal 'ا', .slot 0, .literal 'ْ', .literal 'ت', .literal 'َ', .slot 1, .literal 'ِ', .slot 2]

def t_imperative_X : Pattern 3 := [.literal 'ا', .literal 'س', .literal 'ْ', .literal 'ت', .literal 'َ', .slot 0, .literal 'ْ', .slot 1, .literal 'ِ', .slot 2]

def t_nominal_faail : Pattern 3 := [.slot 0, .literal 'َ', .literal 'ا', .slot 1, .literal 'ِ', .slot 2]

def t_nominal_mafool : Pattern 3 := [.literal 'م', .literal 'َ', .slot 0, .literal 'ْ', .slot 1, .literal 'ُ', .literal 'و', .slot 2]

def t_imperfect_I_a : Pattern 3 := [.literal 'ي', .literal 'َ', .slot 0, .literal 'ْ', .slot 1, .literal 'َ', .slot 2]

def t_imperfect_I_i : Pattern 3 := [.literal 'ي', .literal 'َ', .slot 0, .literal 'ْ', .slot 1, .literal 'ِ', .slot 2]

def t_imperfect_I_u : Pattern 3 := [.literal 'ي', .literal 'َ', .slot 0, .literal 'ْ', .slot 1, .literal 'ُ', .slot 2]

def t_imperfect_II : Pattern 3 := [.literal 'ي', .literal 'ُ', .slot 0, .literal 'َ', .slot 1, .literal 'ّ', .literal 'ِ', .slot 2]

def t_imperfect_III : Pattern 3 := [.literal 'ي', .literal 'ُ', .slot 0, .literal 'َ', .literal 'ا', .slot 1, .literal 'ِ', .slot 2]

def t_imperfect_IV : Pattern 3 := [.literal 'ي', .literal 'ُ', .slot 0, .literal 'ْ', .slot 1, .literal 'ِ', .slot 2]

def t_imperfect_V : Pattern 3 := [.literal 'ي', .literal 'َ', .literal 'ت', .literal 'َ', .slot 0, .literal 'َ', .slot 1, .literal 'ّ', .literal 'َ', .slot 2]

def t_imperfect_VI : Pattern 3 := [.literal 'ي', .literal 'َ', .literal 'ت', .literal 'َ', .slot 0, .literal 'َ', .literal 'ا', .slot 1, .literal 'َ', .slot 2]

def t_imperfect_VII : Pattern 3 := [.literal 'ي', .literal 'َ', .literal 'ن', .literal 'ْ', .slot 0, .literal 'َ', .slot 1, .literal 'ِ', .slot 2]

def t_imperfect_VIII : Pattern 3 := [.literal 'ي', .literal 'َ', .slot 0, .literal 'ْ', .literal 'ت', .literal 'َ', .slot 1, .literal 'ِ', .slot 2]

def t_imperfect_X : Pattern 3 := [.literal 'ي', .literal 'َ', .literal 'س', .literal 'ْ', .literal 'ت', .literal 'َ', .slot 0, .literal 'ْ', .slot 1, .literal 'ِ', .slot 2]

def corePatterns : List CatalogPattern := [
  { id := "past.I.a", label := "فَعَل", arity := 3,
    tokens := t_past_I_a, family := "I",
    form := "past", voice := "active",
    augmentation := "mujarrad",
    sourceContract := "Ishtiqaq.t_past_I_a",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "past.I.i", label := "فَعِل", arity := 3,
    tokens := t_past_I_i, family := "I",
    form := "past", voice := "active",
    augmentation := "mujarrad",
    sourceContract := "Ishtiqaq.t_past_I_i",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "past.I.u", label := "فَعُل", arity := 3,
    tokens := t_past_I_u, family := "I",
    form := "past", voice := "active",
    augmentation := "mujarrad",
    sourceContract := "Ishtiqaq.t_past_I_u",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "past.II", label := "فَعَّل", arity := 3,
    tokens := t_past_II, family := "II",
    form := "past", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_past_II",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "past.III", label := "فَاعَل", arity := 3,
    tokens := t_past_III, family := "III",
    form := "past", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_past_III",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "past.IV", label := "ءَفْعَل", arity := 3,
    tokens := t_past_IV, family := "IV",
    form := "past", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_past_IV",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "past.V", label := "تَفَعَّل", arity := 3,
    tokens := t_past_V, family := "V",
    form := "past", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_past_V",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "past.VI", label := "تَفَاعَل", arity := 3,
    tokens := t_past_VI, family := "VI",
    form := "past", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_past_VI",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "past.VII", label := "انْفَعَل", arity := 3,
    tokens := t_past_VII, family := "VII",
    form := "past", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_past_VII",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "past.VIII", label := "افْتَعَل", arity := 3,
    tokens := t_past_VIII, family := "VIII",
    form := "past", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_past_VIII",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "past.X", label := "اسْتَفْعَل", arity := 3,
    tokens := t_past_X, family := "X",
    form := "past", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_past_X",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "passive.I", label := "فُعِل", arity := 3,
    tokens := t_passive_I, family := "I",
    form := "past", voice := "passive",
    augmentation := "mujarrad",
    sourceContract := "Ishtiqaq.t_passive_I",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "passive.II", label := "فُعِّل", arity := 3,
    tokens := t_passive_II, family := "II",
    form := "past", voice := "passive",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_passive_II",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "passive.III", label := "فُوعِل", arity := 3,
    tokens := t_passive_III, family := "III",
    form := "past", voice := "passive",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_passive_III",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "passive.IV", label := "ءُفْعِل", arity := 3,
    tokens := t_passive_IV, family := "IV",
    form := "past", voice := "passive",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_passive_IV",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "passive.V", label := "تُفُعِّل", arity := 3,
    tokens := t_passive_V, family := "V",
    form := "past", voice := "passive",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_passive_V",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "passive.VI", label := "تُفُوعِل", arity := 3,
    tokens := t_passive_VI, family := "VI",
    form := "past", voice := "passive",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_passive_VI",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "passive.VII", label := "انْفُعِل", arity := 3,
    tokens := t_passive_VII, family := "VII",
    form := "past", voice := "passive",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_passive_VII",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "passive.VIII", label := "افْتُعِل", arity := 3,
    tokens := t_passive_VIII, family := "VIII",
    form := "past", voice := "passive",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_passive_VIII",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "passive.X", label := "اسْتُفْعِل", arity := 3,
    tokens := t_passive_X, family := "X",
    form := "past", voice := "passive",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_passive_X",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['َ'] },
  { id := "imperative.I.a", label := "افْعَل", arity := 3,
    tokens := t_imperative_I_a, family := "I",
    form := "imperative", voice := "active",
    augmentation := "mujarrad",
    sourceContract := "Ishtiqaq.t_imperative_I_a",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['ْ'] },
  { id := "imperative.I.i", label := "افْعِل", arity := 3,
    tokens := t_imperative_I_i, family := "I",
    form := "imperative", voice := "active",
    augmentation := "mujarrad",
    sourceContract := "Ishtiqaq.t_imperative_I_i",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['ْ'] },
  { id := "imperative.I.u", label := "افْعُل", arity := 3,
    tokens := t_imperative_I_u, family := "I",
    form := "imperative", voice := "active",
    augmentation := "mujarrad",
    sourceContract := "Ishtiqaq.t_imperative_I_u",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['ْ'] },
  { id := "imperative.II", label := "فَعِّل", arity := 3,
    tokens := t_imperative_II, family := "II",
    form := "imperative", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_imperative_II",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['ْ'] },
  { id := "imperative.III", label := "فَاعِل", arity := 3,
    tokens := t_imperative_III, family := "III",
    form := "imperative", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_imperative_III",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['ْ'] },
  { id := "imperative.IV", label := "ءَفْعِل", arity := 3,
    tokens := t_imperative_IV, family := "IV",
    form := "imperative", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_imperative_IV",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['ْ'] },
  { id := "imperative.V", label := "تَفَعَّل", arity := 3,
    tokens := t_imperative_V, family := "V",
    form := "imperative", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_imperative_V",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['ْ'] },
  { id := "imperative.VI", label := "تَفَاعَل", arity := 3,
    tokens := t_imperative_VI, family := "VI",
    form := "imperative", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_imperative_VI",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['ْ'] },
  { id := "imperative.VII", label := "انْفَعِل", arity := 3,
    tokens := t_imperative_VII, family := "VII",
    form := "imperative", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_imperative_VII",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['ْ'] },
  { id := "imperative.VIII", label := "افْتَعِل", arity := 3,
    tokens := t_imperative_VIII, family := "VIII",
    form := "imperative", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_imperative_VIII",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['ْ'] },
  { id := "imperative.X", label := "اسْتَفْعِل", arity := 3,
    tokens := t_imperative_X, family := "X",
    form := "imperative", voice := "active",
    augmentation := "mazid",
    sourceContract := "Ishtiqaq.t_imperative_X",
    sourceKind := "LEAN_TEMPLATE",
    rootDomain := "radicals28_shape_only",
    endings := ['ْ'] },
  { id := "nominal.faail", label := "فَاعِل", arity := 3,
    tokens := t_nominal_faail, family := "I",
    form := "nominal", voice := "active",
    augmentation := "mujarrad",
    sourceContract := "QiraaMadlul.faail",
    sourceKind := "NEW_NOMINAL_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "nominal.mafool", label := "مَفْعُول", arity := 3,
    tokens := t_nominal_mafool, family := "I",
    form := "nominal", voice := "passive",
    augmentation := "mujarrad",
    sourceContract := "QiraaMadlul.mafool",
    sourceKind := "NEW_NOMINAL_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "imperfect.I.a", label := "يَفْعَل", arity := 3,
    tokens := t_imperfect_I_a, family := "I",
    form := "imperfect", voice := "active",
    augmentation := "mujarrad",
    sourceContract := "Mudari.body",
    sourceKind := "NEW_SOUND_PROJECTION",
    rootDomain := "sound_triliteral_distinct",
    endings := ['َ', 'ُ', 'ْ'] },
  { id := "imperfect.I.i", label := "يَفْعِل", arity := 3,
    tokens := t_imperfect_I_i, family := "I",
    form := "imperfect", voice := "active",
    augmentation := "mujarrad",
    sourceContract := "Mudari.body",
    sourceKind := "NEW_SOUND_PROJECTION",
    rootDomain := "sound_triliteral_distinct",
    endings := ['َ', 'ُ', 'ْ'] },
  { id := "imperfect.I.u", label := "يَفْعُل", arity := 3,
    tokens := t_imperfect_I_u, family := "I",
    form := "imperfect", voice := "active",
    augmentation := "mujarrad",
    sourceContract := "Mudari.body",
    sourceKind := "NEW_SOUND_PROJECTION",
    rootDomain := "sound_triliteral_distinct",
    endings := ['َ', 'ُ', 'ْ'] },
  { id := "imperfect.II", label := "يُفَعِّل", arity := 3,
    tokens := t_imperfect_II, family := "II",
    form := "imperfect", voice := "active",
    augmentation := "mazid",
    sourceContract := "Mudari.body",
    sourceKind := "NEW_SOUND_PROJECTION",
    rootDomain := "sound_triliteral_distinct",
    endings := ['َ', 'ُ', 'ْ'] },
  { id := "imperfect.III", label := "يُفَاعِل", arity := 3,
    tokens := t_imperfect_III, family := "III",
    form := "imperfect", voice := "active",
    augmentation := "mazid",
    sourceContract := "Mudari.body",
    sourceKind := "NEW_SOUND_PROJECTION",
    rootDomain := "sound_triliteral_distinct",
    endings := ['َ', 'ُ', 'ْ'] },
  { id := "imperfect.IV", label := "يُفْعِل", arity := 3,
    tokens := t_imperfect_IV, family := "IV",
    form := "imperfect", voice := "active",
    augmentation := "mazid",
    sourceContract := "Mudari.body",
    sourceKind := "NEW_SOUND_PROJECTION",
    rootDomain := "sound_triliteral_distinct",
    endings := ['َ', 'ُ', 'ْ'] },
  { id := "imperfect.V", label := "يَتَفَعَّل", arity := 3,
    tokens := t_imperfect_V, family := "V",
    form := "imperfect", voice := "active",
    augmentation := "mazid",
    sourceContract := "Mudari.body",
    sourceKind := "NEW_SOUND_PROJECTION",
    rootDomain := "sound_triliteral_distinct",
    endings := ['َ', 'ُ', 'ْ'] },
  { id := "imperfect.VI", label := "يَتَفَاعَل", arity := 3,
    tokens := t_imperfect_VI, family := "VI",
    form := "imperfect", voice := "active",
    augmentation := "mazid",
    sourceContract := "Mudari.body",
    sourceKind := "NEW_SOUND_PROJECTION",
    rootDomain := "sound_triliteral_distinct",
    endings := ['َ', 'ُ', 'ْ'] },
  { id := "imperfect.VII", label := "يَنْفَعِل", arity := 3,
    tokens := t_imperfect_VII, family := "VII",
    form := "imperfect", voice := "active",
    augmentation := "mazid",
    sourceContract := "Mudari.body",
    sourceKind := "NEW_SOUND_PROJECTION",
    rootDomain := "sound_triliteral_distinct",
    endings := ['َ', 'ُ', 'ْ'] },
  { id := "imperfect.VIII", label := "يَفْتَعِل", arity := 3,
    tokens := t_imperfect_VIII, family := "VIII",
    form := "imperfect", voice := "active",
    augmentation := "mazid",
    sourceContract := "Mudari.body",
    sourceKind := "NEW_SOUND_PROJECTION",
    rootDomain := "sound_triliteral_distinct",
    endings := ['َ', 'ُ', 'ْ'] },
  { id := "imperfect.X", label := "يَسْتَفْعِل", arity := 3,
    tokens := t_imperfect_X, family := "X",
    form := "imperfect", voice := "active",
    augmentation := "mazid",
    sourceContract := "Mudari.body",
    sourceKind := "NEW_SOUND_PROJECTION",
    rootDomain := "sound_triliteral_distinct",
    endings := ['َ', 'ُ', 'ْ'] }
]

theorem core_pattern_count : corePatterns.length = 44 := by decide

theorem core_pattern_ids_unique : (corePatterns.map CatalogPattern.id).Nodup := by decide

theorem core_patterns_complete :
    ∀ pattern ∈ corePatterns, Complete pattern.tokens := by decide

/-- Concrete ambiguity of exact templates: both roots are shape readings. -/
def rootTbr : Root 3 := fun i => if i.val = 0 then 'ت' else if i.val = 1 then 'ب' else 'ر'
def rootNbr : Root 3 := fun i => if i.val = 0 then 'ن' else if i.val = 1 then 'ب' else 'ر'

theorem cross_pattern_same_text :
    fill t_past_VII rootTbr = fill t_past_VIII rootNbr := by rfl

theorem cross_pattern_roots_distinct : rootTbr ≠ rootNbr := by
  intro same
  have atFirst : 'ت' = 'ن' := congrFun same ⟨0, by decide⟩
  exact (by decide : 'ت' ≠ 'ن') atFirst

theorem cross_pattern_ambiguity_retained :
    (t_past_VII, rootTbr) ∈ readings [t_past_VII, t_past_VIII]
      (fill t_past_VII rootTbr) ∧
    (t_past_VIII, rootNbr) ∈ readings [t_past_VII, t_past_VIII]
      (fill t_past_VII rootTbr) ∧ rootTbr ≠ rootNbr := by
  constructor
  · exact readings_complete _ _ _ (by simp) (by decide)
  constructor
  · rw [cross_pattern_same_text]
    exact readings_complete _ _ _ (by simp) (by decide)
  · exact cross_pattern_roots_distinct

/-!
## A separate conditional verb-paradigm availability law

These premises assert availability of past, imperfect and imperative for one
verb. They are not observations of whether those forms happened to occur in
a corpus. A positive and a negative assertion at the same cell conflict.
Unknown cells remain unconstrained; the empty complete paradigm lies outside
the assumed verb domain. One, two and three available cells are labelled
jamid, partial and full respectively by this explicitly bounded law.

This is distinct from semantic nominal jamid/mushtaq. Binding equality is a
structural requirement for combining premises. The truth of the assertions,
their source parsing and their reference to the same lexical verb are external
premises; this module never manufactures them from pattern resemblance.
-/

namespace Paradigm

def lawId : String := "nabt.verb-paradigm-availability.v1"

structure Mask where
  past : Bool
  imperfect : Bool
  imperative : Bool
  deriving DecidableEq, Repr

def Mask.at (mask : Mask) (index : Fin 3) : Bool :=
  if index.val = 0 then mask.past else if index.val = 1 then mask.imperfect else mask.imperative

def Mask.code (mask : Mask) : Nat :=
  mask.past.toNat + 2 * mask.imperfect.toNat + 4 * mask.imperative.toNat

def Mask.ofCode (number : Nat) : Mask :=
  ⟨number % 2 == 1, number / 2 % 2 == 1, number / 4 % 2 == 1⟩

def Mask.count (mask : Mask) : Nat :=
  mask.past.toNat + mask.imperfect.toNat + mask.imperative.toNat

def emptyMask : Mask := ⟨false, false, false⟩
def fullMask : Mask := ⟨true, true, true⟩

def Fits (positive negative model : Mask) : Prop :=
  ∀ index : Fin 3,
    (positive.at index = true → model.at index = true) ∧
    (negative.at index = true → model.at index = false)

instance (positive negative model : Mask) : Decidable (Fits positive negative model) :=
  inferInstanceAs (Decidable (∀ index : Fin 3,
    (positive.at index = true → model.at index = true) ∧
    (negative.at index = true → model.at index = false)))

def allModels : List Mask := [1, 2, 3, 4, 5, 6, 7].map Mask.ofCode

def models (positive negative : Mask) : List Mask :=
  allModels.filter fun model => decide (Fits positive negative model)

inductive Category where
  | jamid | partialParadigm | full
  deriving DecidableEq, Repr

def Category.label : Category → String
  | .jamid => "jamid" | .partialParadigm => "partial" | .full => "full"

def allCategories : List Category := [.jamid, .partialParadigm, .full]

def classifyModel (model : Mask) : Option Category :=
  if model.count = 1 then some .jamid
  else if model.count = 2 then some .partialParadigm
  else if model.count = 3 then some .full else none

def categories (positive negative : Mask) : List Category :=
  allCategories.filter fun category =>
    (models positive negative).any fun model => classifyModel model == some category

structure Binding where
  sourceId : Nat
  sourceRevision : Nat
  scopeId : Nat
  lexemeId : Nat
  deriving DecidableEq, Repr

structure Premises where
  binding : Binding
  positive : Mask
  negative : Mask

def scopedCategories (expected : Binding) (premises : Premises) : List Category :=
  if premises.binding = expected then categories premises.positive premises.negative
  else allCategories

theorem mask_roundtrip (mask : Mask) : Mask.ofCode mask.code = mask := by
  rcases mask with ⟨past, imperfect, imperative⟩
  cases past <;> cases imperfect <;> cases imperative <;> rfl

theorem bounded_code_roundtrip :
    ∀ number : Fin 8, (Mask.ofCode number.val).code = number.val := by decide

theorem model_membership (positive negative model : Mask) :
    model ∈ models positive negative ↔ model ∈ allModels ∧ Fits positive negative model := by
  simp [models]

theorem complete_models_nonempty : ∀ model ∈ allModels, model.count > 0 := by decide

theorem positive_assertion_preserved (positive negative model : Mask)
    (index : Fin 3) (member : model ∈ models positive negative)
    (present : positive.at index = true) : model.at index = true := by
  exact ((model_membership positive negative model).mp member).2 index |>.1 present

theorem negative_assertion_preserved (positive negative model : Mask)
    (index : Fin 3) (member : model ∈ models positive negative)
    (absent : negative.at index = true) : model.at index = false := by
  exact ((model_membership positive negative model).mp member).2 index |>.2 absent

theorem conflicting_assertions_eliminate_models (positive negative : Mask)
    (index : Fin 3) (present : positive.at index = true)
    (absent : negative.at index = true) : models positive negative = [] := by
  apply List.eq_nil_iff_forall_not_mem.mpr
  intro model member
  have yes := positive_assertion_preserved positive negative model index member present
  have no := negative_assertion_preserved positive negative model index member absent
  simp [yes] at no

theorem conflicting_assertions_never_classify (positive negative : Mask)
    (index : Fin 3) (present : positive.at index = true)
    (absent : negative.at index = true) : categories positive negative = [] := by
  simp [categories, conflicting_assertions_eliminate_models positive negative index present absent]

theorem deleting_assertions_cannot_narrow (positiveBefore negativeBefore positiveAfter
    negativeAfter : Mask)
    (positiveSubset : ∀ index, positiveAfter.at index = true → positiveBefore.at index = true)
    (negativeSubset : ∀ index, negativeAfter.at index = true → negativeBefore.at index = true)
    (model : Mask) (member : model ∈ models positiveBefore negativeBefore) :
    model ∈ models positiveAfter negativeAfter := by
  rw [model_membership] at member ⊢
  refine ⟨member.1, ?_⟩
  intro index
  exact ⟨fun yes => (member.2 index).1 (positiveSubset index yes),
    fun no => (member.2 index).2 (negativeSubset index no)⟩

theorem no_assertion_keeps_all_models : models emptyMask emptyMask = allModels := by decide

theorem past_alone_does_not_entail_jamid :
    (models (Mask.ofCode 1) emptyMask).map Mask.code = [1, 3, 5, 7] ∧
    categories (Mask.ofCode 1) emptyMask = [.jamid, .partialParadigm, .full] := by decide

theorem past_with_two_explicit_absences_is_jamid :
    categories (Mask.ofCode 1) (Mask.ofCode 6) = [.jamid] := by decide

theorem two_forms_with_third_absent_are_partial :
    categories (Mask.ofCode 3) (Mask.ofCode 4) = [.partialParadigm] := by decide

theorem all_available_models_full :
    (models fullMask emptyMask).map Mask.code = [7] ∧
    categories fullMask emptyMask = [.full] := by decide

theorem all_absent_outside_verb_domain : models emptyMask fullMask = [] := by decide

theorem foreign_binding_does_not_classify (expected : Binding) (premises : Premises)
    (foreign : premises.binding ≠ expected) :
    scopedCategories expected premises = allCategories := by
  simp [scopedCategories, foreign]

theorem all_forms_full_conditional_on_same_lexeme (expected : Binding) (premises : Premises)
    (sameLexeme : premises.binding = expected)
    (allPresent : premises.positive = fullMask)
    (noNegatives : premises.negative = emptyMask) :
    scopedCategories expected premises = [.full] := by
  simp [scopedCategories, sameLexeme, allPresent, noNegatives, all_available_models_full.2]

end Paradigm

end Nabt.Derivation
