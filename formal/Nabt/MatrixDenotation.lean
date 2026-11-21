import Lean
import Nabt.LexicalDenotation

/-! Authored readings of a fixed edition. Only the external source reader can
replay the quotation or bind an occurrence. The matrix row and root are both
required, and the existing lexical calculus owns all three indications. -/
namespace Nabt.MatrixDenotation
open Lean LexicalDenotation

structure Entry where
  id : String
  root : String
  heading : String
  quote : String
  start : Nat
  stop : Nat
  components : List String
  deriving FromJson

structure Implication where
  id : String
  target : String
  quote : String
  start : Nat
  stop : Nat
  source_sha256 : String
  deriving FromJson

structure Deposit where
  source_sha256 : String
  readings : List Entry
  necessities : List Implication
  deriving FromJson

structure OntologyClass where
  category : String
  readings : List String
  deriving FromJson

def installedClasses : Except String (List OntologyClass) := do
  fromJson? (← Json.parse (include_str "../../evidence/morphology_concepts_v1/classification.json"))

def installed : Except String Deposit := do
  fromJson? (← Json.parse (include_str "../../evidence/morphology_concepts_v1/interpretations.json"))

def Entry.sense (hash : String) (e : Entry) : Sense :=
  ⟨e.id, e.root, ⟨"maqayis", "matrix-v1", hash, e.start, e.stop, e.quote⟩, e.components⟩

def rules (d : Deposit) (s : Sense) : List Necessity :=
  (d.necessities.filter (fun n => n.id == s.id)).map fun n =>
    ⟨s,n.target,.mental,⟨"NABT", "matrix-v1", n.source_sha256,n.start,n.stop,n.quote⟩⟩

def classified (cs : List OntologyClass) (id kind : String) : Bool :=
  !kind.isEmpty && ((cs.filter (fun c => c.readings.contains id)).map OntologyClass.category == [kind])

def licensed (cs : List OntologyClass) (category : String) (d : Deposit) (e : Entry) (reading root : String)
    (kind : Indication) (target : List String) : Bool :=
  classified cs reading category && e.id == reading && e.root == root &&
    check (rules d (e.sense d.source_sha256)) (e.sense d.source_sha256) kind target

/-- Specialization of the registered check_exact to the two matrix join keys. -/
theorem licensed_iff (cs : List OntologyClass) (category : String) (d : Deposit) (e : Entry) (reading root : String)
    (k : Indication) (t : List String) :
    licensed cs category d e reading root k t = true ↔
    classified cs reading category = true ∧ e.id = reading ∧ e.root = root ∧
    Admitted (rules d (e.sense d.source_sha256)) (e.sense d.source_sha256) k t := by
  simp [licensed, Bool.and_eq_true, check_exact, and_assoc]

end Nabt.MatrixDenotation
