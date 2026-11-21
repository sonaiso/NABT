import Lean

namespace MasdarSlots

/-- The compatibility test may recognize partial vocalization or registered allomorphs.
The theorem quantifies over finite reference inventories and preserves their order. -/
def readForms (surface : String) (fits : String → String → Bool)
    (entries : List (String × String)) : List String :=
  (entries.filter (fun e => fits surface e.1)).map Prod.snd

theorem readForms_exact (surface id : String) (fits : String → String → Bool)
    (entries : List (String × String)) :
    id ∈ readForms surface fits entries ↔
      ∃ spelling, (spelling,id) ∈ entries ∧ fits surface spelling = true := by
  simp only [readForms, List.mem_map, List.mem_filter]
  constructor
  · rintro ⟨⟨w,k⟩, ⟨h,hf⟩, rfl⟩
    exact ⟨w,h,hf⟩
  · rintro ⟨w,h,hf⟩
    exact ⟨(w,id),⟨h,hf⟩,rfl⟩

abbrev Atom := List String
/-- Query and both argument occurrences, referent, genus and trait are explicit. -/
structure Binding where
  role : String
  reading : String
  noun : String
  entity : String
  genus : String
  trait : String
deriving Lean.FromJson, Lean.ToJson

def link (b : Binding) : List Atom :=
  [["موضع_" ++ b.role,b.reading,b.noun],["مرجع_موافق",b.noun,b.entity],
   ["جنس_شرط_" ++ b.role,b.reading,b.genus],["خاصية_شرط_" ++ b.role,b.reading,b.trait]]

def memAtom (b : Binding) : Atom := ["عضوية",b.entity,b.genus]
def propAtom (b : Binding) : Atom := ["خاصية",b.entity,b.trait]
def neg : Atom → Atom | [] => [] | p::args => ("!" ++ p)::args

def posBody (b : Binding) := link b ++ [memAtom b,propAtom b]
def negGenus (b : Binding) := link b ++ [neg (memAtom b)]
def negTrait (b : Binding) := link b ++ [neg (propAtom b)]
def covered (db body : List Atom) := body.all (fun a => db.contains a)
def plus (db : List Atom) (b : Binding) := covered db (posBody b)
def minus (db : List Atom) (b : Binding) := covered db (negGenus b) || covered db (negTrait b)

theorem plus_exact (db : List Atom) (b : Binding) :
    plus db b = true ↔ (∀ a ∈ link b, a ∈ db) ∧ memAtom b ∈ db ∧ propAtom b ∈ db := by
  simp [plus, covered, posBody]

theorem minus_exact (db : List Atom) (b : Binding) :
    minus db b = true ↔ (∀ a ∈ link b, a ∈ db) ∧
      (neg (memAtom b) ∈ db ∨ neg (propAtom b) ∈ db) := by
  simp [minus, covered, negGenus, negTrait, and_or_left]

/-- Emit exactly the three signed ground clauses compared with the Python instances. -/
def emit (b : Binding) : List (Atom × List Atom) :=
  let h := ["صالح_" ++ b.role,b.reading,b.entity]
  [(h,posBody b),(neg h,negGenus b),(neg h,negTrait b)]

end MasdarSlots

#print axioms MasdarSlots.readForms_exact
#print axioms MasdarSlots.plus_exact
#print axioms MasdarSlots.minus_exact

def main (args : List String) : IO UInt32 := do
  let [file] := args | return 2
  let raw ← IO.FS.readFile file
  let batch : Except String (List MasdarSlots.Binding) := Lean.Json.parse raw >>= Lean.fromJson?
  match batch with
  | .error msg => throw <| IO.userError msg
  | .ok rows =>
    IO.println (Lean.toJson (rows.map MasdarSlots.emit)).compress
    return 0
