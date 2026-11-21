import Std

/-! Algebra of typed edges, all joins in the same declared observation frame.
Evidence identifiers are retained in order. This algebra does not assert
that the source observations are true in the external world. -/
namespace NamedMatrix
abbrev Matrix (F A B : Type) := F → A → B → List Nat → Prop

def join {F A B C} (r : Matrix F A B) (s : Matrix F B C) : Matrix F A C :=
  fun f a c ws => ∃ b u v, r f a b u ∧ s f b c v ∧ ws = u ++ v

theorem join_assoc {F A B C D} (r : Matrix F A B) (s : Matrix F B C)
    (t : Matrix F C D) (f a d ws) :
    join (join r s) t f a d ws ↔ join r (join s t) f a d ws := by
  constructor
  · rintro ⟨c,_,z,⟨b,u,v,hr,hs,rfl⟩,ht,rfl⟩
    exact ⟨b,u,v++z,hr,⟨c,v,z,hs,ht,rfl⟩,List.append_assoc ..⟩
  · rintro ⟨b,u,_,hr,⟨c,v,z,hs,ht,rfl⟩,rfl⟩
    exact ⟨c,u++v,z,⟨b,u,v,hr,hs,rfl⟩,ht,(List.append_assoc ..).symm⟩

def withdraw {F A B} (i : Nat) (r : Matrix F A B) : Matrix F A B :=
  fun f a b ws => r f a b ws ∧ i ∉ ws

theorem withdraw_join {F A B C} (i : Nat) (r : Matrix F A B) (s : Matrix F B C) (f a c ws) :
    withdraw i (join r s) f a c ws ↔ join (withdraw i r) (withdraw i s) f a c ws := by
  constructor
  · rintro ⟨⟨b,u,v,hr,hs,rfl⟩,free⟩
    simp only [List.mem_append, not_or] at free
    exact ⟨b,u,v,⟨hr,free.1⟩,⟨hs,free.2⟩,rfl⟩
  · rintro ⟨b,u,v,⟨hr,hu⟩,⟨hs,hv⟩,rfl⟩
    exact ⟨⟨b,u,v,hr,hs,rfl⟩,by simpa only [List.mem_append,not_or] using And.intro hu hv⟩

theorem class_or_material_distinction :
    ∃ (instanceOf madeOf : Bool → Bool → Prop),
      instanceOf false false ∧ madeOf false true ∧ ¬ instanceOf false true := by
  exact ⟨Eq, fun a b => a ≠ b, rfl, by decide, by decide⟩

theorem capability_and_event_distinction :
    ∃ (capable occurred : Bool → Prop), capable true ∧ ¬ occurred true := by
  exact ⟨fun _ => True, fun _ => False, trivial, id⟩

end NamedMatrix
#print axioms NamedMatrix.join_assoc
#print axioms NamedMatrix.withdraw_join
