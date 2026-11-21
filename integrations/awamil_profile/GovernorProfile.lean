import Nabt.Governors
import Nabt.ArabicCoverage
import Nabt.RecursiveLicensedAlgebra
import Jisr.AwamilUslub

/-! Cross-owner audit on the deposited style column and NABT's typed table.
A ledger records licensed lexical witnesses; its coverage of an external lexicon
and its alignment to unsegmented writing are independent premises. -/
namespace GovernorProfile
open Nabt Nabt.Governors
abbrev Id := Fin 100
def ids : List Id := List.finRange 100

private theorem rowsSize : table.length = 100 := by decide
private theorem stylesSize : Jisr.Awamil.uslub.length = 100 := by decide

def row (i : Id) : Row := table[i.val]'(by rw [rowsSize]; exact i.isLt)
def stylePair (i : Id) : String × String :=
  Jisr.Awamil.uslub[i.val]'(by rw [stylesSize]; exact i.isLt)

theorem same_label_at_every_position : ∀ i : Id, (row i).label = (stylePair i).1 := by decide

structure Key where
  equations : List Alternative
  links : List Link
  style : String
  implicitGovernor : Bool
  deriving DecidableEq, Repr

def foldRow (i : Id) : Key :=
  let r := row i
  ⟨r.governorClass.equations, r.governorClass.links, (stylePair i).2, r.implicit⟩

def fiber (k : Key) : List Id := ids.filter (fun i => decide (foldRow i = k))

theorem fiber_exact (i : Id) (k : Key) : i ∈ fiber k ↔ foldRow i = k := by
  simp [fiber, ids]

def basis : List Key := (ids.map foldRow).eraseDups

theorem observation_counts :
    ((ids.map fun i => (foldRow i).style).eraseDups.length = 6) ∧
    ((ids.map fun i => ((foldRow i).equations, (foldRow i).links)).eraseDups.length = 12) ∧
    ((ids.map fun i => ((foldRow i).equations, (foldRow i).links, (foldRow i).style)).eraseDups.length = 16) ∧
    basis.length = 17 := by decide

theorem style_counts :
    (["الخبر", "الطلب", "التمني", "الترجي", "الاستفهام", "النداء"].map fun s =>
      (ids.filter (fun i => (foldRow i).style == s)).length) = [82,2,1,1,10,4] := by decide

/-- Any encoding from which the required observations can be recovered must
distinguish every pair separated by the seventeen keys. -/
theorem distinct_keys_require_distinct_codes {T : Type} (encode : Id → T) (recover : T → Key)
    (faithful : ∀ i, recover (encode i) = foldRow i) {i j : Id}
    (different : foldRow i ≠ foldRow j) : encode i ≠ encode j := by
  intro same
  exact different ((faithful i).symm.trans ((congrArg recover same).trans (faithful j)))

structure Witness where
  rowId : Id
  sourceId : Nat
  start : Nat
  cells : List Atom
  roleBindings : List (Role × Nat × Case)
  evidenceId : Nat
  deriving DecidableEq

def assignment (w : Witness) (r : Role) : Option Case :=
  ((w.roleBindings.find? (fun v => v.1 == r)).map (fun v => v.2.2))

abbrev Reading := Witness × Alternative

/-- The caller supplies activation, consistent occurrence/role bindings and
scope guards in eligible. No guard is inferred from a table style. -/
def reference (ledger : List Witness) (eligible : Witness → Bool) (input : List Atom) (y : Reading) : Prop :=
  y.1 ∈ ledger ∧ eligible y.1 = true ∧ y.1.cells = input ∧
  y.2 ∈ (row y.1.rowId).governorClass.equations ∧
  Satisfies (assignment y.1) y.2 (row y.1.rowId).governorClass.links

def expand (ledger : List Witness) (eligible : Witness → Bool) (input : List Atom) : List Reading :=
  ledger.flatMap fun w =>
    if eligible w && decide (w.cells = input) then
      let k := foldRow w.rowId
      (k.equations.filter (fun alt => checkAlternative (assignment w) alt k.links)).map (fun alt => (w,alt))
    else []

theorem expand_exact (ledger : List Witness) (eligible : Witness → Bool)
    (input : List Atom) (y : Reading) : y ∈ expand ledger eligible input ↔ reference ledger eligible input y := by
  rcases y with ⟨w,alt⟩
  constructor
  · intro h
    obtain ⟨v,hv,h⟩ := List.mem_flatMap.mp h
    by_cases he : eligible v && decide (v.cells = input)
    · simp [he] at h
      obtain ⟨⟨ha,hc⟩,rfl⟩ := h
      obtain ⟨ok,same⟩ := Bool.and_eq_true_iff.mp he
      exact ⟨hv,ok,of_decide_eq_true same,ha,(checkAlternative_iff ..).mp hc⟩
    · simp [he] at h
  · rintro ⟨hw,ok,same,ha,hc⟩
    change w.cells = input at same
    apply List.mem_flatMap.mpr
    refine ⟨w,hw,?_⟩
    simp [ok,same,foldRow,ha,(checkAlternative_iff ..).mpr hc]

theorem exact_in_declared_domain (ledger : List Witness) (eligible : Witness → Bool) :
    ArabicCoverage.ExactWithin (fun _ => True) (reference ledger eligible)
      (fun cells y => y ∈ expand ledger eligible cells) :=
  fun input _ y => expand_exact ledger eligible input y

open RecursiveLicensedAlgebra

/-- In this grammar the governed lexical leaves are supplied by occurrence.
Root gates, every inherited lexical condition, the full unary and binary rule
records, their order, and their realizations remain the native grammar's. -/
def withGovernorLeaves (g : Grammar) (atEntry : Nat → List Atom × Reading)
    (accept : List Atom → Reading → Prop) : Grammar :=
  { g with lexicalAllowed := fun entry =>
      g.lexicalAllowed entry ∧ accept (atEntry entry).1 (atEntry entry).2 }

theorem derivation_exact (g : Grammar) (atEntry : Nat → List Atom × Reading)
    (ledger : List Witness) (eligible : Witness → Bool) (t : Tree) :
    Certified (withGovernorLeaves g atEntry (fun c r => r ∈ expand ledger eligible c)) t ↔
    AllNodeConditions (withGovernorLeaves g atEntry (reference ledger eligible)) t := by
  have same : (fun c r => r ∈ expand ledger eligible c) = reference ledger eligible := by
    funext c r
    exact propext (expand_exact ledger eligible c r)
  rw [same]
  exact certified_iff_all_node_conditions _ _

end GovernorProfile
