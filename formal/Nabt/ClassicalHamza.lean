import Std

/-! Conditional, one-step morphophonemic hamza laws. Origin and grammatical
analysis are premises, not properties acquired from an arbitrary input string.
Strings in the formal data are opaque atoms. The Python boundary restricts its
alphabet; no theorem here asserts the truth of that boundary's implementation.
Hamza seats, later weak-lam transformations, lexical validity, and acoustics are
outside this relation. The full source frame is retained in every derivation. -/
namespace Nabt.ClassicalHamza

def lawId := "nabt.classical-hamza.v1"

inductive Boundary where
  | ibtida | wasl | waqf
  deriving DecidableEq, Repr
inductive Origin where
  | added | radical | unknown
  deriving DecidableEq, Repr
inductive VerbMedial where
  | changedToAlif | retained | unknown
  deriving DecidableEq, Repr
inductive SingularOrigin where
  | addedLong | radicalLong | nonlong | unknown
  deriving DecidableEq, Repr
inductive Template where
  | mafail | mafailLong | other | unknown
  deriving DecidableEq, Repr
inductive Profile where
  | namedCommon | allAttested
  deriving DecidableEq, Repr
inductive Glide where
  | waw | ya
  deriving DecidableEq, Repr

def glideAtom : Glide → String
  | .waw => "و" | .ya => "ي"

inductive Frame where
  | interrogative (tail : List String) (boundary : Boundary)
  | finalLong (pre : List String) (glide : Glide) (origin : Origin) (suffix : List String)
  | active (first last : String) (glide : Glide) (verbMedial : VerbMedial)
  | broken (first second long last : String) (feminine : Bool)
      (origin : SingularOrigin) (template : Template)
  | twoGlides (underlying : List String) (template : Template)
  | lexical (root : List String) (profile : Profile)
  deriving DecidableEq, Repr

inductive Operation where
  | interrogativeIbdal | interrogativeTashil | hamzateFinal | hamzateMedial
  | hamzatePlural | hamzateSecondGlide | shortCommand | fullDialectCommand
  deriving DecidableEq, Repr

def isLong (s : String) : Bool := s == "ا" || s == "و" || s == "ي"
def isGlide (s : String) : Bool := s == "و" || s == "ي"

def twoGlideShape : List String → Bool
  | [_, a, "ا", b, _] => isGlide a && isGlide b
  | _ => false

def namedRoot (root : List String) : Bool :=
  root == ["ء", "خ", "ذ"] || root == ["ء", "ك", "ل"] || root == ["ء", "م", "ر"]

-- A declarative law relation; the candidate enumerator below is separate.
def Admissible : Frame → Operation → Prop
  | .interrogative _ b, .interrogativeIbdal => b ≠ .waqf
  | .interrogative _ b, .interrogativeTashil => b ≠ .waqf
  | .finalLong _ _ o suffix, .hamzateFinal => o = .added ∧ suffix = []
  | .active _ _ _ v, .hamzateMedial => v = .changedToAlif
  | .broken _ _ l _ _ o t, .hamzatePlural =>
      o = .addedLong ∧ t = .mafail ∧ isLong l = true
  | .twoGlides underlying t, .hamzateSecondGlide =>
      t = .mafail ∧ twoGlideShape underlying = true
  | .lexical root _, .shortCommand => namedRoot root = true
  | .lexical root p, .fullDialectCommand => root = ["ء", "ك", "ل"] ∧ p = .allAttested
  | _, _ => False

def enumerate : Frame → List Operation
  | .interrogative _ b =>
      if b ≠ .waqf then [.interrogativeIbdal, .interrogativeTashil] else []
  | .finalLong _ _ o suffix =>
      if o = .added ∧ suffix = [] then [.hamzateFinal] else []
  | .active _ _ _ v => if v = .changedToAlif then [.hamzateMedial] else []
  | .broken _ _ l _ _ o t =>
      if o = .addedLong ∧ t = .mafail ∧ isLong l = true then [.hamzatePlural] else []
  | .twoGlides underlying t =>
      if t = .mafail ∧ twoGlideShape underlying = true then [.hamzateSecondGlide] else []
  | .lexical root p =>
      (if namedRoot root then [.shortCommand] else []) ++
      (if root = ["ء", "ك", "ل"] ∧ p = .allAttested then [.fullDialectCommand] else [])

theorem enumeration_exact (f : Frame) (op : Operation) :
    op ∈ enumerate f ↔ Admissible f op := by
  cases f with
  | interrogative tail b => cases b <;> cases op <;> simp [enumerate, Admissible]
  | finalLong pre g o suffix =>
      cases o <;> cases suffix <;> cases op <;> simp [enumerate, Admissible]
  | active first last g v => cases v <;> cases op <;> simp [enumerate, Admissible]
  | broken a b l z feminine o t =>
      cases o <;> cases t <;> cases op <;> cases h : isLong l <;>
        simp [enumerate, Admissible, h]
  | twoGlides underlying t =>
      cases t <;> cases op <;> cases h : twoGlideShape underlying <;>
        simp [enumerate, Admissible, h]
  | lexical root p =>
      cases h : namedRoot root <;> by_cases h2 : root = ["ء", "ك", "ل"] <;>
        cases p <;> cases op <;> simp [enumerate, Admissible, h, h2]

theorem enumeration_sound (f : Frame) (op : Operation) (h : op ∈ enumerate f) :
    Admissible f op := (enumeration_exact f op).mp h

theorem enumeration_complete (f : Frame) (op : Operation) (h : Admissible f op) :
    op ∈ enumerate f := (enumeration_exact f op).mpr h

def input : Frame → List String
  | .interrogative tail _ => ["ء", "ا", "ل"] ++ tail
  | .finalLong pre g _ suffix => pre ++ ["ا", glideAtom g] ++ suffix
  | .active first last g _ => [first, "ا", glideAtom g, last]
  | .broken a b l z _ _ _ => [a, b, "ا", l, z]
  | .twoGlides underlying _ => underlying
  | .lexical root _ => root

def render : Frame → Operation → List String
  | .interrogative tail _, .interrogativeIbdal => ["ء", "ا", "ل"] ++ tail
  | .interrogative tail _, .interrogativeTashil => ["ء", "HAMZA_TASHIL", "ل"] ++ tail
  | .finalLong pre _ _ _, .hamzateFinal => pre ++ ["ا", "ء"]
  | .active first last _ _, .hamzateMedial => [first, "ا", "ء", last]
  | .broken a b _ z _ _ _, .hamzatePlural => [a, b, "ا", "ء", z]
  | .twoGlides [a, b, _, _, z] _, .hamzateSecondGlide => [a, b, "ا", "ء", z]
  | .lexical root _, .shortCommand => root.drop 1
  | .lexical _ _, .fullDialectCommand => ["ء", "و", "ك", "ل"]
  | _, _ => []

def outputs (f : Frame) : List (List String) := (enumerate f).map (render f)
def Produces (f : Frame) (out : List String) : Prop :=
  ∃ op, Admissible f op ∧ render f op = out

theorem output_exact (f : Frame) (out : List String) :
    out ∈ outputs f ↔ Produces f out := by
  simp [outputs, Produces, enumeration_exact]

theorem enumeration_nodup (f : Frame) : (enumerate f).Nodup := by
  cases f <;> simp only [enumerate]
  all_goals split <;> simp_all
  all_goals split <;> simp_all

theorem at_most_two_operations (f : Frame) : (enumerate f).length ≤ 2 := by
  cases f <;> simp only [enumerate]
  all_goals split <;> simp_all
  all_goals split <;> simp_all

theorem ibtida_has_both (tail : List String) :
    enumerate (.interrogative tail .ibtida) = [.interrogativeIbdal, .interrogativeTashil] := by
  simp [enumerate]

theorem tashil_not_erased (tail : List String) :
    render (.interrogative tail .ibtida) .interrogativeTashil =
      ["ء", "HAMZA_TASHIL", "ل"] ++ tail := rfl

theorem radical_alif_blocks (pre suffix : List String) (g : Glide) :
    enumerate (.finalLong pre g .radical suffix) = [] := by simp [enumerate]

theorem nonfinal_glide_blocks (pre : List String) (g : Glide) (o : Origin)
    (x : String) (xs : List String) :
    enumerate (.finalLong pre g o (x :: xs)) = [] := by simp [enumerate]

theorem final_replacement_preserves_length (pre : List String) (g : Glide) :
    (render (.finalLong pre g .added []) .hamzateFinal).length =
      (input (.finalLong pre g .added [])).length := by simp [render, input]

theorem retained_verb_blocks (a z : String) (g : Glide) :
    enumerate (.active a z g .retained) = [] := by simp [enumerate]

theorem active_preserves_outer_radicals (a z : String) (g : Glide) :
    render (.active a z g .changedToAlif) .hamzateMedial = [a, "ا", "ء", z] := rfl

theorem original_singular_madd_blocks (a b l z : String) (f : Bool) (t : Template) :
    enumerate (.broken a b l z f .radicalLong t) = [] := by simp [enumerate]

theorem nonlong_singular_blocks (a b l z : String) (f : Bool) (t : Template) :
    enumerate (.broken a b l z f .nonlong t) = [] := by simp [enumerate]

theorem mafail_long_blocks (s : List String) :
    enumerate (.twoGlides s .mafailLong) = [] := by simp [enumerate]

theorem common_akal (p : Profile) :
    Operation.shortCommand ∈ enumerate (.lexical ["ء", "ك", "ل"] p) := by
  rw [enumeration_exact]
  simp [Admissible, namedRoot]

theorem attested_oukul_retained :
    enumerate (.lexical ["ء", "ك", "ل"] .allAttested) =
      [.shortCommand, .fullDialectCommand] := by decide

theorem unlisted_hamzated_root_not_dropped :
    enumerate (.lexical ["ء", "س", "ر"] .allAttested) = [] := by decide

def CompleteProposal (f : Frame) (proposal : List Operation) : Prop :=
  ∀ op, Admissible f op → op ∈ proposal

theorem omitted_alternative_is_incomplete (f : Frame) (proposal : List Operation)
    (op : Operation) (licensed : Admissible f op) (missing : op ∉ proposal) :
    ¬ CompleteProposal f proposal := by
  intro h
  exact missing (h op licensed)

structure Derivation where
  sourceFrame : Frame
  operation : Operation
  licensed : Admissible sourceFrame operation

def restore (d : Derivation) : Frame := d.sourceFrame

theorem restore_exact (f : Frame) (op : Operation) (h : Admissible f op) :
    restore ⟨f, op, h⟩ = f := rfl

theorem output_depends_on_licensed_step (d : Derivation) :
    render d.sourceFrame d.operation ∈ outputs d.sourceFrame := by
  rw [output_exact]
  exact ⟨d.operation, d.licensed, rfl⟩

end Nabt.ClassicalHamza
