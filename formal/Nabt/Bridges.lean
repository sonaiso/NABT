import Nabt.Sequence

/-!
Explicit numerical bridges. The only common interpretation is a canonical
carrier and mark. No shape law, attestation, lexical meaning or judgment is
imported or licensed by these definitions.

Source declarations (not runtime or proof dependencies):
* Saleh1967/Alghanem@9d8fa03a51f894416e0abaf3b6821c5ae6441dcd:
  formal/a116/A116/Cells.lean, Numbering.lean, and gate/bridge.py.
* Saleh1967/Mashru@e4c801ffe9171dadedcc3aae23051ea0953ae361:
  Dal/Khaliya.lean, Makharij.lean, Adad.lean, SLGE/Core.lean, Ladder.lean.

The source tables are declared finite data. Their correspondence to named
carriers, permutations, inverse maps and preservation of arbitrary finite
sequences are checked here. Number inverses are universal over Nat. SLGE's
number codec is explicitly Core.encL at radix 116, first cell least significant;
it is not Ladder.wordEnc (a radix-148944 encoding of syllables).

Python adds a resource bound of 4096 cells and strict type/byte validation.
Those runtime bounds and byte parsers are tested, not claimed as Lean theorems.
-/

namespace Nabt.Bridges

inductive Alphabet where
  | nabt | alghanemCanonical | alghanemBridge | mashruDal | slge
  deriving DecidableEq, Repr

/-- Each codec names both its alphabet and its sequence significance order. -/
inductive NumberCodec where
  | nabtB116 | alghanemCanonicalTransport | alghanemAtomNumber | mashruAdad | slgeEncL116
  deriving DecidableEq, Repr

def NumberCodec.alphabet : NumberCodec → Alphabet
  | .nabtB116 => .nabt
  | .alghanemCanonicalTransport => .alghanemCanonical
  | .alghanemAtomNumber => .alghanemBridge
  | .mashruAdad => .mashruDal
  | .slgeEncL116 => .slge

def makharijCarriers : List String :=
  ["ء", "ه", "ا", "ع", "ح", "غ", "خ", "ق", "ك", "ج", "ش", "ي", "ض", "ل", "ن",
   "ر", "ط", "د", "ت", "ز", "س", "ص", "ظ", "ذ", "ث", "ف", "ب", "م", "و"]

def bridgeCarriers : List String :=
  ["ء", "ب", "ت", "ث", "ج", "ح", "خ", "د", "ذ", "ر", "ز", "س", "ش", "ص", "ض",
   "ط", "ظ", "ع", "غ", "ف", "ق", "ك", "ل", "م", "ن", "ه", "و", "ي", "ا"]

def Alphabet.carriers : Alphabet → List String
  | .nabt | .alghanemCanonical => canonicalCarriers
  | .alghanemBridge => bridgeCarriers
  | .mashruDal | .slge => makharijCarriers

def swapCarrier (c : Carrier) : Carrier :=
  if c = 0 then 28 else if c = 28 then 0 else c

def makharijToCanonical : List Carrier :=
  [28, 25, 0, 17, 5, 18, 6, 20, 21, 4, 12, 27, 14, 22, 24,
   9, 15, 7, 2, 10, 11, 13, 16, 8, 3, 19, 1, 23, 26]

def canonicalToMakharij : List Carrier :=
  [2, 26, 18, 24, 9, 4, 6, 17, 23, 15, 19, 20, 10, 21, 12,
   16, 22, 3, 5, 25, 7, 8, 13, 27, 14, 1, 28, 11, 0]

def toCanonicalCarrier (a : Alphabet) (c : Carrier) : Carrier :=
  match a with
  | .nabt | .alghanemCanonical => c
  | .alghanemBridge => swapCarrier c
  | .mashruDal | .slge => makharijToCanonical.getD c.val 0

def fromCanonicalCarrier (a : Alphabet) (c : Carrier) : Carrier :=
  match a with
  | .nabt | .alghanemCanonical => c
  | .alghanemBridge => swapCarrier c
  | .mashruDal | .slge => canonicalToMakharij.getD c.val 0

/-- Finite declaration checks, covering all five alphabets and 29 carriers. -/
theorem carrier_tables_inverse : ∀ (a : Alphabet) (c : Carrier),
    fromCanonicalCarrier a (toCanonicalCarrier a c) = c ∧
    toCanonicalCarrier a (fromCanonicalCarrier a c) = c := by
  intro a
  cases a <;> decide

theorem carrier_tables_preserve_names : ∀ (a : Alphabet) (c : Carrier),
    canonicalCarriers.getD (toCanonicalCarrier a c).val "" =
      a.carriers.getD c.val "" := by
  intro a
  cases a <;> decide

theorem alphabet_tables_nodup : ∀ a : Alphabet,
    a.carriers.length = 29 ∧ a.carriers.Nodup := by
  intro a
  cases a <;> decide

def decodeCell (a : Alphabet) (atom : Atom) : Cell :=
  let c := Cell.decode atom
  ⟨toCanonicalCarrier a c.carrier, c.mark⟩

def encodeCell (a : Alphabet) (c : Cell) : Atom :=
  Cell.encode ⟨fromCanonicalCarrier a c.carrier, c.mark⟩

theorem decodeCell_encodeCell (a : Alphabet) (c : Cell) :
    decodeCell a (encodeCell a c) = c := by
  simp only [decodeCell, encodeCell, Cell.decode_encode]
  rw [(carrier_tables_inverse a c.carrier).2]

theorem encodeCell_decodeCell (a : Alphabet) (atom : Atom) :
    encodeCell a (decodeCell a atom) = atom := by
  simp only [encodeCell, decodeCell]
  rw [(carrier_tables_inverse a (Cell.decode atom).carrier).1]
  exact Cell.encode_decode atom

def convertCell (source target : Alphabet) (atom : Atom) : Atom :=
  encodeCell target (decodeCell source atom)

theorem convertCell_preserves_identity (source target : Alphabet) (atom : Atom) :
    decodeCell target (convertCell source target atom) = decodeCell source atom := by
  simp only [convertCell, decodeCell_encodeCell]

theorem convertCell_preserves_mark (source target : Alphabet) (atom : Atom) :
    (Cell.decode (convertCell source target atom)).mark = (Cell.decode atom).mark := by
  have h := congrArg Cell.mark (convertCell_preserves_identity source target atom)
  exact h

theorem convertCell_inverse (source target : Alphabet) (atom : Atom) :
    convertCell target source (convertCell source target atom) = atom := by
  simp only [convertCell, decodeCell_encodeCell, encodeCell_decodeCell]

theorem convertCell_self (a : Alphabet) (atom : Atom) :
    convertCell a a atom = atom := encodeCell_decodeCell a atom

theorem convertCell_compose (a b c : Alphabet) (atom : Atom) :
    convertCell b c (convertCell a b atom) = convertCell a c atom := by
  simp only [convertCell, decodeCell_encodeCell]

theorem convertCell_bijective (source target : Alphabet) :
    Function.Injective (convertCell source target) ∧
    Function.Surjective (convertCell source target) := by
  constructor
  · intro a b h
    have h' := congrArg (convertCell target source) h
    simpa only [convertCell_inverse] using h'
  · intro atom
    exact ⟨convertCell target source atom, convertCell_inverse target source atom⟩

def convertCells (source target : Alphabet) (atoms : List Atom) : List Atom :=
  atoms.map (convertCell source target)

def identities (a : Alphabet) (atoms : List Atom) : List Cell := atoms.map (decodeCell a)

/-- Arbitrary list length, with order, multiplicity, carrier and mark retained. -/
theorem convertCells_preserves_identity (source target : Alphabet) (atoms : List Atom) :
    identities target (convertCells source target atoms) = identities source atoms := by
  simp [identities, convertCells, List.map_map, convertCell_preserves_identity]

theorem convertCells_inverse (source target : Alphabet) (atoms : List Atom) :
    convertCells target source (convertCells source target atoms) = atoms := by
  simp [convertCells, List.map_map, Function.comp_def, convertCell_inverse]

theorem convertCells_length (source target : Alphabet) (atoms : List Atom) :
    (convertCells source target atoms).length = atoms.length := by
  simp [convertCells]

theorem convertCells_append (source target : Alphabet) (xs ys : List Atom) :
    convertCells source target (xs ++ ys) =
      convertCells source target xs ++ convertCells source target ys := by
  simp [convertCells]

theorem convertCells_compose (a b c : Alphabet) (atoms : List Atom) :
    convertCells b c (convertCells a b atoms) = convertCells a c atoms := by
  simp [convertCells, List.map_map, convertCell_compose]

theorem convertCells_bijective (source target : Alphabet) :
    Function.Injective (convertCells source target) ∧
    Function.Surjective (convertCells source target) := by
  constructor
  · intro a b h
    have h' := congrArg (convertCells target source) h
    simpa only [convertCells_inverse] using h'
  · intro atoms
    exact ⟨convertCells target source atoms, convertCells_inverse target source atoms⟩

def orient (codec : NumberCodec) (atoms : List Atom) : List Atom :=
  match codec with
  | .slgeEncL116 => atoms.reverse
  | _ => atoms

theorem orient_involution (codec : NumberCodec) (atoms : List Atom) :
    orient codec (orient codec atoms) = atoms := by
  cases codec <;> simp [orient]

def encodeNumber (codec : NumberCodec) (atoms : List Atom) : Nat :=
  Sequence.encode (orient codec atoms)

def decodeNumber (codec : NumberCodec) (number : Nat) : List Atom :=
  orient codec (Sequence.decode number)

theorem decodeNumber_encodeNumber (codec : NumberCodec) (atoms : List Atom) :
    decodeNumber codec (encodeNumber codec atoms) = atoms := by
  simp only [decodeNumber, encodeNumber, Sequence.decode_encode, orient_involution]

theorem encodeNumber_decodeNumber (codec : NumberCodec) (number : Nat) :
    encodeNumber codec (decodeNumber codec number) = number := by
  simp only [decodeNumber, encodeNumber, orient_involution, Sequence.encode_decode]

/-- An independently named numeric codec is required at each end. -/
def convertNumber (source target : NumberCodec) (number : Nat) : Nat :=
  encodeNumber target (convertCells source.alphabet target.alphabet (decodeNumber source number))

theorem convertNumber_inverse (source target : NumberCodec) (number : Nat) :
    convertNumber target source (convertNumber source target number) = number := by
  simp only [convertNumber, decodeNumber_encodeNumber, convertCells_inverse,
    encodeNumber_decodeNumber]

theorem convertNumber_preserves_sequence (source target : NumberCodec) (number : Nat) :
    identities target.alphabet (decodeNumber target (convertNumber source target number)) =
      identities source.alphabet (decodeNumber source number) := by
  simp only [convertNumber, decodeNumber_encodeNumber, convertCells_preserves_identity]

theorem convertNumber_compose (a b c : NumberCodec) (number : Nat) :
    convertNumber b c (convertNumber a b number) = convertNumber a c number := by
  simp only [convertNumber, decodeNumber_encodeNumber, convertCells_compose]

theorem convertNumber_bijective (source target : NumberCodec) :
    Function.Injective (convertNumber source target) ∧
    Function.Surjective (convertNumber source target) := by
  constructor
  · intro a b h
    have h' := congrArg (convertNumber target source) h
    simpa only [convertNumber_inverse] using h'
  · intro number
    exact ⟨convertNumber target source number, convertNumber_inverse target source number⟩

theorem convertNumber_zero (source target : NumberCodec) :
    convertNumber source target 0 = 0 := by
  cases source <;> cases target <;> rfl

/-- A finite mismatch count; no equality of differently scoped cell IDs. -/
theorem alghanem_eight_cell_differences :
    ((List.finRange 116).filter fun atom =>
      convertCell .alghanemBridge .nabt atom != atom).length = 8 := by decide

theorem alghanem_hamza_number_is_not_nabt_alif :
    convertNumber .alghanemAtomNumber .nabtB116 1 = 113 := by decide

theorem mashru_kataba_cells :
    convertCells .mashruDal .nabt [32, 72, 104] = [84, 8, 4] := by decide

theorem mashru_kataba_numbers :
    encodeNumber .mashruAdad [32, 72, 104] = 452621 ∧
    encodeNumber .nabtB116 [84, 8, 4] = 1144809 := by decide

theorem slge_encL116_is_little_endian (atoms : List Atom) :
    encodeNumber .slgeEncL116 atoms = Sequence.little atoms := by
  simp [encodeNumber, orient, Sequence.encode]

end Nabt.Bridges
