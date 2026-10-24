import Nabt.RecursiveLicensedAlgebra
import Nabt.UnitDiscovery
import Nabt.LicensedDerivation
import Nabt.BinaryUnitDomain

/-!
# Exact source bridge for the imported recursive algebra

The imported structural number is relative to a declared rule registry. This
module binds a complete annotated node to its source, typed root/template,
every alignment position, section, role endpoints, ordered children and
evidence ledger. Sparse radical fibers are annotations of a complete source
host; they are never passed off as adjacent children of the PR14 join.

Source reconstruction and interpreted linguistic licensing are separate.
The external Grammar and its realization contracts remain explicit premises;
the Boolean source bridge does not prove an arbitrary supplied grammar.
-/

namespace Nabt.RecursiveSourceBridge

abbrev CoreTree := RecursiveLicensedAlgebra.Tree
abbrev CoreSeed := RecursiveLicensedAlgebra.Seed
abbrev CoreInventory := RecursiveLicensedAlgebra.Inventory

def lawId : String := "nabt.recursive-source-bridge.v1"
def numberDomain : String := "nabt.recursive-structural-cantor.v1"
def atomizationDomain : String := "unicode-scalar-exact.v1"

/-! Closed arithmetic is proved equivalent before executable numbering. -/

theorem twice_triangle (n : Nat) :
    RecursiveLicensedAlgebra.triangle n * 2 = n * (n + 1) := by
  induction n with
  | zero => rfl
  | succ n ih =>
      simp only [RecursiveLicensedAlgebra.triangle, Nat.add_mul, ih,
        Nat.mul_add, Nat.mul_one, Nat.one_mul]
      omega

def fastTriangle (n : Nat) : Nat := n * (n + 1) / 2

theorem fastTriangle_eq (n : Nat) :
    fastTriangle n = RecursiveLicensedAlgebra.triangle n := by
  unfold fastTriangle
  rw [← twice_triangle]
  omega

def fastPair (a b : Nat) : Nat := fastTriangle (a + b) + b

theorem fastPair_eq (a b : Nat) :
    fastPair a b = RecursiveLicensedAlgebra.pair a b := by
  simp [fastPair, fastTriangle_eq, RecursiveLicensedAlgebra.pair]

def seedNumber : CoreSeed → Nat
  | .root3 a b c => 3 * fastPair a (fastPair b c)
  | .root4 a b c d => 3 * fastPair a (fastPair b (fastPair c d)) + 1
  | .lexical entry => 3 * entry + 2

theorem seedNumber_eq (seed : CoreSeed) : seedNumber seed = seed.n := by
  cases seed <;> simp [seedNumber, fastPair_eq, RecursiveLicensedAlgebra.Seed.n]

def structuralNumber : CoreTree → Nat
  | .leaf seed => 3 * seedNumber seed
  | .unary rule child => 3 * fastPair rule (structuralNumber child) + 1
  | .binary rule left right =>
      3 * fastPair rule (fastPair (structuralNumber left) (structuralNumber right)) + 2

theorem structuralNumber_eq (tree : CoreTree) : structuralNumber tree = tree.n := by
  induction tree with
  | leaf seed => simp [structuralNumber, seedNumber_eq, RecursiveLicensedAlgebra.Tree.n]
  | unary rule child ih =>
      simp [structuralNumber, ih, fastPair_eq, RecursiveLicensedAlgebra.Tree.n]
  | binary rule left right il ir =>
      simp [structuralNumber, il, ir, fastPair_eq, RecursiveLicensedAlgebra.Tree.n]

theorem structuralNumber_injective (left right : CoreTree)
    (same : structuralNumber left = structuralNumber right) : left = right := by
  apply RecursiveLicensedAlgebra.tree_number_injective
  simpa only [structuralNumber_eq] using same

/-- Conservative bit-cost calculation, used before any potentially enormous
Cantor multiplication. The value bound is proved below; runtime and allocation
also require the executable node, depth and output limits. -/
def pairBits (a b : Nat) : Nat := 2 * (max a b + 1) + 1

def natBits (value : Nat) : Nat := value.log2 + 1

def seedBits : CoreSeed → Nat
  | .root3 a b c => pairBits (natBits a) (pairBits (natBits b) (natBits c)) + 2
  | .root4 a b c d => pairBits (natBits a) (pairBits (natBits b) (pairBits (natBits c) (natBits d))) + 2
  | .lexical entry => natBits entry + 3

def numberBits : CoreTree → Nat
  | .leaf seed => seedBits seed + 2
  | .unary rule child => pairBits (natBits rule) (numberBits child) + 2
  | .binary rule left right =>
      pairBits (natBits rule) (pairBits (numberBits left) (numberBits right)) + 2

theorem natBits_bound (value : Nat) : value < 2 ^ natBits value :=
  Nat.lt_log2_self

theorem fastPair_bound (a b aBits bBits : Nat)
    (left : a < 2 ^ aBits) (right : b < 2 ^ bBits) :
    fastPair a b < 2 ^ pairBits aBits bBits := by
  let width := max aBits bBits + 1
  have leftMax : a < 2 ^ max aBits bBits := Nat.lt_of_lt_of_le left
    (Nat.pow_le_pow_right (by decide) (Nat.le_max_left _ _))
  have rightMax : b < 2 ^ max aBits bBits := Nat.lt_of_lt_of_le right
    (Nat.pow_le_pow_right (by decide) (Nat.le_max_right _ _))
  have sumBound : a + b < 2 ^ width := by
    simp only [width, Nat.pow_succ]
    omega
  have productBound : (a + b) * (a + b + 1) ≤ 2 ^ width * 2 ^ width :=
    Nat.mul_le_mul (Nat.le_of_lt sumBound) (by omega)
  have squarePositive : 2 ^ width ≤ 2 ^ width * 2 ^ width := by
    simpa using Nat.mul_le_mul_right (2 ^ width) (Nat.one_le_two_pow (n := width))
  have secondSmall : b < 2 ^ width * 2 ^ width := by omega
  have divisionBound := Nat.div_le_self ((a + b) * (a + b + 1)) 2
  have pairBound : fastPair a b < 2 ^ width * 2 ^ width + 2 ^ width * 2 ^ width := by
    simp only [fastPair, fastTriangle]
    omega
  have exponent : pairBits aBits bBits = width + width + 1 := by
    simp only [pairBits, width]
    omega
  simpa only [exponent, Nat.pow_succ, Nat.pow_add, Nat.mul_two] using pairBound

theorem tagged_bound (value bits tag : Nat) (bounded : value < 2 ^ bits) (small : tag ≤ 2) :
    3 * value + tag < 2 ^ (bits + 2) := by
  simp only [Nat.pow_succ]
  omega

theorem seedNumber_bound (seed : CoreSeed) : seedNumber seed < 2 ^ seedBits seed := by
  cases seed with
  | root3 a b c =>
      exact tagged_bound _ _ 0 (fastPair_bound _ _ _ _ (natBits_bound a)
        (fastPair_bound _ _ _ _ (natBits_bound b) (natBits_bound c))) (by decide)
  | root4 a b c d =>
      exact tagged_bound _ _ 1 (fastPair_bound _ _ _ _ (natBits_bound a)
        (fastPair_bound _ _ _ _ (natBits_bound b)
          (fastPair_bound _ _ _ _ (natBits_bound c) (natBits_bound d)))) (by decide)
  | lexical entry =>
      have tight := tagged_bound entry (natBits entry) 2 (natBits_bound entry) (by decide)
      change 3 * entry + 2 < 2 ^ (natBits entry + 3)
      exact Nat.lt_of_lt_of_le tight (Nat.pow_le_pow_right (by decide) (by omega))

theorem structuralNumber_bound (tree : CoreTree) : structuralNumber tree < 2 ^ numberBits tree := by
  induction tree with
  | leaf seed => exact tagged_bound _ _ 0 (seedNumber_bound seed) (by decide)
  | unary rule child ih =>
      exact tagged_bound _ _ 1 (fastPair_bound _ _ _ _ (natBits_bound rule) ih) (by decide)
  | binary rule left right il ir =>
      exact tagged_bound _ _ 2 (fastPair_bound _ _ _ _ (natBits_bound rule)
        (fastPair_bound _ _ _ _ il ir)) (by decide)

theorem number_budget_bounds_result (tree : CoreTree) (budget : Nat)
    (within : numberBits tree ≤ budget) : structuralNumber tree < 2 ^ budget :=
  Nat.lt_of_lt_of_le (structuralNumber_bound tree) (Nat.pow_le_pow_right (by decide) within)

structure ScopedNumber where
  registryId : String
  number : Nat
  deriving DecidableEq, Repr

def scopedNumber (registry : String) (tree : CoreTree) : ScopedNumber :=
  ⟨registry, structuralNumber tree⟩

theorem scopedNumber_preserves_registry (leftRegistry rightRegistry : String)
    (left right : CoreTree)
    (same : scopedNumber leftRegistry left = scopedNumber rightRegistry right) :
    leftRegistry = rightRegistry ∧ left = right := by
  have fields := ScopedNumber.mk.inj same
  exact ⟨fields.1, structuralNumber_injective _ _ fields.2⟩

def normalizeInventory (inventory : CoreInventory) : CoreInventory :=
  ⟨inventory.seeds.eraseDups, inventory.unaryRules.eraseDups, inventory.binaryRules.eraseDups⟩

theorem normalized_supported_iff (inventory : CoreInventory) (tree : CoreTree) :
    RecursiveLicensedAlgebra.Supported (normalizeInventory inventory) tree ↔
      RecursiveLicensedAlgebra.Supported inventory tree := by
  induction tree with
  | leaf seed => simp [RecursiveLicensedAlgebra.Supported, normalizeInventory]
  | unary rule child ih =>
      simp only [RecursiveLicensedAlgebra.Supported, ih]
      simp [normalizeInventory]
  | binary rule left right il ir =>
      simp only [RecursiveLicensedAlgebra.Supported, il, ir]
      simp [normalizeInventory]

def uniqueCandidates (inventory : CoreInventory) (height : Nat) : List CoreTree :=
  BinaryUnitDomain.distinct (RecursiveLicensedAlgebra.candidates (normalizeInventory inventory) height)

theorem uniqueCandidates_exact (inventory : CoreInventory) (height : Nat) (tree : CoreTree) :
    tree ∈ uniqueCandidates inventory height ↔
      RecursiveLicensedAlgebra.Supported inventory tree ∧ tree.height ≤ height := by
  simp [uniqueCandidates, BinaryUnitDomain.mem_distinct,
    RecursiveLicensedAlgebra.candidates_iff, normalized_supported_iff]

theorem uniqueCandidates_nodup (inventory : CoreInventory) (height : Nat) :
    (uniqueCandidates inventory height).Nodup := by
  exact BinaryUnitDomain.distinct_nodup _

/-! Every template position, not merely the radical subsequence. -/

inductive Origin where
  | literal (value : Char)
  | radical (index : Nat)
  deriving DecidableEq, Repr

structure AlignmentPoint where
  patternPosition : Nat
  sourcePosition : Nat
  origin : Origin
  deriving DecidableEq, Repr

def tokenOrigin {n : Nat} : Derivation.Token n → Origin
  | .literal value => .literal value
  | .slot index => .radical index.val

def alignmentFor {n : Nat} (start : Nat) (pattern : Derivation.Pattern n) : List AlignmentPoint :=
  pattern.zipIdx.map fun (token, index) => ⟨index, start + index, tokenOrigin token⟩

def readingAlignment (start : Nat) : UnitDiscovery.RootPatternReading → List AlignmentPoint
  | .tri pattern _ => alignmentFor start pattern
  | .quad pattern _ => alignmentFor start pattern

def readingSeed : UnitDiscovery.RootPatternReading → CoreSeed
  | .tri _ root => .root3 (root 0).toNat (root 1).toNat (root 2).toNat
  | .quad _ root => .root4 (root 0).toNat (root 1).toNat (root 2).toNat (root 3).toNat

structure Morphology where
  catalogId : String
  registryId : String
  readingId : String
  reading : UnitDiscovery.RootPatternReading
  alignment : List AlignmentPoint
  deriving DecidableEq

def Morphology.valid (source : UnitDiscovery.Source Char) (host : UnitDiscovery.Span)
    (morphology : Morphology) : Bool :=
  !morphology.catalogId.isEmpty && !morphology.registryId.isEmpty &&
    !morphology.readingId.isEmpty &&
    UnitDiscovery.fitsHost source host morphology.reading &&
    decide (morphology.alignment = readingAlignment host.start morphology.reading)

theorem valid_morphology_refills (source : UnitDiscovery.Source Char) (host : UnitDiscovery.Span)
    (morphology : Morphology) (valid : morphology.valid source host = true) :
    morphology.reading.complete = true ∧
      morphology.reading.render = UnitDiscovery.spanAtoms source host := by
  have fit : UnitDiscovery.fitsHost source host morphology.reading = true := by
    simp only [Morphology.valid, Bool.and_eq_true] at valid
    exact valid.1.2
  exact (UnitDiscovery.fitsHost_sound _ _ _ fit).2

theorem valid_morphology_alignment (source : UnitDiscovery.Source Char) (host : UnitDiscovery.Span)
    (morphology : Morphology) (valid : morphology.valid source host = true) :
    morphology.alignment = readingAlignment host.start morphology.reading := by
  simp only [Morphology.valid, Bool.and_eq_true] at valid
  exact of_decide_eq_true valid.2

def recoverMorphology (source : UnitDiscovery.Source Char) (host : UnitDiscovery.Span)
    (morphology : Morphology) : Option UnitDiscovery.RootPatternReading :=
  match morphology.reading with
  | .tri pattern _ => UnitDiscovery.recoverTri pattern (UnitDiscovery.spanAtoms source host)
  | .quad pattern _ => UnitDiscovery.recoverQuad pattern (UnitDiscovery.spanAtoms source host)

theorem valid_morphology_recovers (source : UnitDiscovery.Source Char) (host : UnitDiscovery.Span)
    (morphology : Morphology) (valid : morphology.valid source host = true) :
    recoverMorphology source host morphology = some morphology.reading := by
  have fits : UnitDiscovery.fitsHost source host morphology.reading = true := by
    simp only [Morphology.valid, Bool.and_eq_true] at valid
    exact valid.1.2
  cases readingPresent : morphology.reading with
  | tri pattern root =>
      simpa only [recoverMorphology, readingPresent] using
        UnitDiscovery.fitsHost_tri_recovers source host pattern root (by simpa [readingPresent] using fits)
  | quad pattern root =>
      simpa only [recoverMorphology, readingPresent] using
        UnitDiscovery.fitsHost_quad_recovers source host pattern root (by simpa [readingPresent] using fits)

def radicalPositions (morphology : Morphology) (radical : Nat) : List Nat :=
  morphology.alignment.filterMap fun point =>
    if point.origin = .radical radical then some point.sourcePosition else none

structure Role where
  role : String
  readingId : String
  target : UnitDiscovery.Span
  head : Option UnitDiscovery.Span
  grammaticalCase : Option String
  caseDomain : Option String
  deriving DecidableEq, Repr

def Role.valid (source : UnitDiscovery.Source Char) (role : Role) : Bool :=
  !role.role.isEmpty && !role.readingId.isEmpty && UnitDiscovery.validSpan source role.target &&
    (match role.head with | none => true | some span => UnitDiscovery.validSpan source span) &&
    decide (role.grammaticalCase.isSome = role.caseDomain.isSome)

inductive Provenance where
  | nativeTree
  | sourceReconstruction
  deriving DecidableEq, Repr

structure Metadata where
  registryId : String
  readingId : String
  source : UnitDiscovery.Source Char
  host : UnitDiscovery.Span
  hostTree : LicensedDerivation.Tree Char
  morphology : Option Morphology
  wordSection : Option RecursiveLicensedAlgebra.Category
  roles : List Role
  evidenceIds : List Nat
  required : List Nat
  provenance : Provenance
  unresolved : List String
  deriving DecidableEq

inductive Node where
  | leaf (seed : CoreSeed) (metadata : Metadata)
  | unary (rule : Nat) (metadata : Metadata) (child : Node)
  | binary (rule : Nat) (metadata : Metadata) (left right : Node)
  deriving DecidableEq

def Node.metadata : Node → Metadata
  | .leaf _ metadata | .unary _ metadata _ | .binary _ metadata _ _ => metadata

def Node.erase : Node → CoreTree
  | .leaf seed _ => .leaf seed
  | .unary rule _ child => .unary rule child.erase
  | .binary rule _ left right => .binary rule left.erase right.erase

def Node.nodes : Node → List Node
  | node@(.leaf ..) => [node]
  | node@(.unary _ _ child) => node :: child.nodes
  | node@(.binary _ _ left right) => node :: (left.nodes ++ right.nodes)

def Node.children : Node → List Node
  | .leaf .. => []
  | .unary _ _ child => [child]
  | .binary _ _ left right => [left, right]

theorem self_mem_nodes (node : Node) : node ∈ node.nodes := by
  cases node <;> simp [Node.nodes]

theorem structural_host_reconstruct (inventory : List (UnitDiscovery.Source Char))
    (tree : LicensedDerivation.Tree Char) (valid : tree.structural inventory = true) :
    tree.reconstruct = tree.source.atoms := by
  induction tree with
  | atom source before value after =>
      exact (of_decide_eq_true valid).2.symm
  | join tag left right leftIH _ =>
      simp only [LicensedDerivation.Tree.structural, Bool.and_eq_true] at valid
      have boundary : left.after = right.raw ++ right.after :=
        (of_decide_eq_true valid.1.1).2.2
      simpa [LicensedDerivation.Tree.reconstruct, LicensedDerivation.Tree.before,
        LicensedDerivation.Tree.raw, LicensedDerivation.Tree.after,
        LicensedDerivation.Tree.source, boundary, List.append_assoc] using leftIH valid.1.2
  | wrap tag child childIH => exact childIH (Bool.and_eq_true_iff.mp valid).2
  | substitute tag replacement child childIH => exact childIH (Bool.and_eq_true_iff.mp valid).2
  | lift tag child childIH => exact childIH (Bool.and_eq_true_iff.mp valid).2

def contained (child parent : UnitDiscovery.Span) : Prop :=
  parent.start ≤ child.start ∧ child.stop ≤ parent.stop

instance (child parent : UnitDiscovery.Span) : Decidable (contained child parent) :=
  inferInstanceAs (Decidable (parent.start ≤ child.start ∧ child.stop ≤ parent.stop))

def Metadata.sourceValid (inventory : List (UnitDiscovery.Source Char)) (metadata : Metadata) : Bool :=
  !metadata.registryId.isEmpty && !metadata.readingId.isEmpty &&
    decide (metadata.source ∈ inventory) && UnitDiscovery.validSpan metadata.source metadata.host &&
    metadata.hostTree.structural inventory &&
    decide (metadata.hostTree.source = metadata.source ∧
      metadata.hostTree.start = metadata.host.start ∧
      metadata.hostTree.stop = metadata.host.stop ∧
      metadata.hostTree.raw = UnitDiscovery.spanAtoms metadata.source metadata.host) &&
    metadata.roles.all (Role.valid metadata.source) &&
    (match metadata.morphology with
      | none => true
      | some morphology => morphology.valid metadata.source metadata.host)

def Node.localSourceValid (inventory : List (UnitDiscovery.Source Char)) (node : Node) : Bool :=
  node.metadata.sourceValid inventory &&
    (match node.metadata.morphology with
      | none => true
      | some morphology => decide (node.erase.origins = [readingSeed morphology.reading])) &&
    (match node with
      | .leaf .. => true
      | .unary _ metadata child => decide (
          metadata.registryId = child.metadata.registryId ∧ metadata.source = child.metadata.source ∧
          contained child.metadata.host metadata.host)
      | .binary _ metadata left right => decide (
          metadata.registryId = left.metadata.registryId ∧
          metadata.registryId = right.metadata.registryId ∧
          metadata.source = left.metadata.source ∧ metadata.source = right.metadata.source ∧
          contained left.metadata.host metadata.host ∧ contained right.metadata.host metadata.host))

def Node.sourceBound (inventory : List (UnitDiscovery.Source Char)) (node : Node) : Bool :=
  node.nodes.all (Node.localSourceValid inventory)

def Node.requirements (node : Node) : List Nat :=
  0 :: node.metadata.required

structure Receipt where
  target : Node
  requirement : Nat
  positive : Bool
  witnessId : Nat
  supports : List (UnitDiscovery.Support Char)
  deriving DecidableEq

structure Context where
  inventory : List (UnitDiscovery.Source Char)
  interpreted : List Receipt
  offered : List Receipt
  deriving DecidableEq

def acceptsReceipt (context : Context) (target : Node) (receipt : Receipt) : Bool :=
  decide (receipt.target = target ∧ receipt ∈ context.interpreted) &&
    !receipt.supports.isEmpty && receipt.supports.all (UnitDiscovery.validSupport context.inventory)

def positives (context : Context) (node : Node) : List Receipt :=
  context.offered.filter fun receipt => acceptsReceipt context node receipt && receipt.positive

def negatives (context : Context) (node : Node) : List Receipt :=
  context.interpreted.filter fun receipt => acceptsReceipt context node receipt && !receipt.positive

def hasRequirement (receipts : List Receipt) (requirement : Nat) : Bool :=
  receipts.any fun receipt => decide (receipt.requirement = requirement)

def localPositive (context : Context) (node : Node) : Bool :=
  node.requirements.all (hasRequirement (positives context node))

def localNegative (context : Context) (node : Node) : Bool :=
  node.requirements.any (hasRequirement (negatives context node))

def allPositive (context : Context) (node : Node) : Bool := node.nodes.all (localPositive context)
def anyNegative (context : Context) (node : Node) : Bool := node.nodes.any (localNegative context)

def linguisticReady (node : Node) : Bool :=
  node.nodes.all fun child => child.metadata.unresolved.isEmpty &&
    decide (child.metadata.provenance = .nativeTree)

inductive Status where
  | invalid | sourceOnly | pending | conditionalLicensed | rejected
  deriving DecidableEq, Repr

structure Report where
  status : Status
  sourceBound : Bool
  allPremises : Bool
  negative : Bool
  linguisticReady : Bool
  deriving DecidableEq, Repr

def assess (context : Context) (node : Node) : Report :=
  let source := node.sourceBound context.inventory
  let positive := allPositive context node
  let negative := anyNegative context node
  let ready := linguisticReady node
  let status := if !source then .invalid else if negative then .rejected
    else if !ready then .sourceOnly else if positive then .conditionalLicensed else .pending
  ⟨status, source, positive, negative, ready⟩

def Licensed (context : Context) (node : Node) : Prop :=
  node.sourceBound context.inventory = true ∧ allPositive context node = true ∧
    anyNegative context node = false ∧ linguisticReady node = true

theorem assess_licensed_iff (context : Context) (node : Node) :
    (assess context node).status = .conditionalLicensed ↔ Licensed context node := by
  simp only [assess, Licensed]
  cases node.sourceBound context.inventory <;> cases anyNegative context node <;>
    cases linguisticReady node <;> cases allPositive context node <;> decide

theorem source_reconstruction_not_linguistically_ready (node : Node)
    (reconstruction : node.metadata.provenance = .sourceReconstruction) :
    linguisticReady node = false := by
  cases ready : linguisticReady node with
  | false => rfl
  | true =>
      have this := List.all_eq_true.mp (show _ from ready) node (self_mem_nodes node)
      simp [reconstruction] at this

theorem accepted_receipt_exact_target (context : Context) (node : Node) (receipt : Receipt)
    (accepted : acceptsReceipt context node receipt = true) : receipt.target = node := by
  simp only [acceptsReceipt, Bool.and_eq_true] at accepted
  exact (of_decide_eq_true accepted.1.1).1

theorem accepted_receipt_interpreted (context : Context) (node : Node) (receipt : Receipt)
    (accepted : acceptsReceipt context node receipt = true) : receipt ∈ context.interpreted := by
  simp only [acceptsReceipt, Bool.and_eq_true] at accepted
  exact (of_decide_eq_true accepted.1.1).2

theorem accepted_receipt_preserves_metadata_and_children (context : Context)
    (node : Node) (receipt : Receipt) (accepted : acceptsReceipt context node receipt = true) :
    receipt.target.metadata = node.metadata ∧ receipt.target.children = node.children := by
  rw [accepted_receipt_exact_target context node receipt accepted]
  exact ⟨rfl, rfl⟩

theorem foreign_target_rejected (context : Context) (node : Node) (receipt : Receipt)
    (different : receipt.target ≠ node) : acceptsReceipt context node receipt = false := by
  simp [acceptsReceipt, different]

theorem changed_metadata_rejected (context : Context) (node : Node) (receipt : Receipt)
    (changed : receipt.target.metadata ≠ node.metadata) : acceptsReceipt context node receipt = false := by
  apply foreign_target_rejected
  intro same
  exact changed (congrArg Node.metadata same)

theorem changed_ordered_children_rejected (context : Context) (node : Node) (receipt : Receipt)
    (changed : receipt.target.children ≠ node.children) : acceptsReceipt context node receipt = false := by
  apply foreign_target_rejected
  intro same
  exact changed (congrArg Node.children same)

theorem negative_ledger_independent_of_offered (context : Context) (node : Node) (offered : List Receipt) :
    negatives { context with offered := offered } node = negatives context node := rfl

theorem known_negative_blocks_source_only (context : Context) (node : Node)
    (source : node.sourceBound context.inventory = true)
    (negative : anyNegative context node = true) : (assess context node).status = .rejected := by
  simp [assess, source, negative]

theorem known_negative_cannot_be_hidden_by_offered (context : Context) (node : Node)
    (offered : List Receipt)
    (source : node.sourceBound context.inventory = true)
    (negative : anyNegative context node = true) :
    (assess { context with offered := offered } node).status = .rejected := by
  exact known_negative_blocks_source_only _ _ source negative

theorem rejected_not_licensed (context : Context) (node : Node)
    (negative : anyNegative context node = true) : ¬ Licensed context node := by
  intro licensed
  have absent := licensed.2.2.1
  rw [negative] at absent
  cases absent

theorem licensed_all_nodes_source_bound (context : Context) (node child : Node)
    (licensed : Licensed context node) (member : child ∈ node.nodes) :
    child.localSourceValid context.inventory = true :=
  List.all_eq_true.mp licensed.1 child member

theorem licensed_all_nodes_have_premises (context : Context) (node child : Node)
    (licensed : Licensed context node) (member : child ∈ node.nodes) :
    localPositive context child = true :=
  List.all_eq_true.mp licensed.2.1 child member

theorem source_bound_all_hosts_reconstruct (inventory : List (UnitDiscovery.Source Char))
    (node child : Node) (bound : node.sourceBound inventory = true) (member : child ∈ node.nodes) :
    child.metadata.hostTree.reconstruct = child.metadata.source.atoms := by
  have localBound := List.all_eq_true.mp bound child member
  have metadataValid := (Bool.and_eq_true_iff.mp (Bool.and_eq_true_iff.mp localBound).1).1
  simp only [Metadata.sourceValid, Bool.and_eq_true] at metadataValid
  have structural : child.metadata.hostTree.structural inventory = true := metadataValid.1.1.1.2
  have exactSource : child.metadata.hostTree.source = child.metadata.source :=
    (of_decide_eq_true metadataValid.1.1.2).1
  rw [structural_host_reconstruct inventory child.metadata.hostTree structural, exactSource]

theorem licensed_alignment_preserved (context : Context) (node child : Node) (morphology : Morphology)
    (licensed : Licensed context node) (member : child ∈ node.nodes)
    (present : child.metadata.morphology = some morphology) :
    morphology.alignment = readingAlignment child.metadata.host.start morphology.reading := by
  have source := licensed_all_nodes_source_bound context node child licensed member
  have valid : morphology.valid child.metadata.source child.metadata.host = true := by
    simp only [Node.localSourceValid, Bool.and_eq_true] at source
    have metadata := source.1.1
    simpa only [Metadata.sourceValid, Bool.and_eq_true, present] using
      (show (match child.metadata.morphology with
        | none => true
        | some m => m.valid child.metadata.source child.metadata.host) = true from
        (Bool.and_eq_true_iff.mp metadata).2)
  exact valid_morphology_alignment _ _ _ valid

/-- Each original node, including its retained section when present, must be
realized by the semantic grammar as the complete source host. This binds the
two proof domains; carrying metadata alone would not establish that relation. -/
def RealizationAligned (grammar : RecursiveLicensedAlgebra.Grammar) (node : Node) : Prop :=
  ∀ child ∈ node.nodes,
    child.erase.surface grammar = child.metadata.hostTree.output.map Char.toNat ∧
    (match child.metadata.wordSection with
      | none => True
      | some category => (child.erase.face grammar).category = category)

/-- Combining this source contract with the imported semantic grammar is an
explicit additional obligation. No flag or structural number supplies it. -/
structure CertifiedBridge (grammar : RecursiveLicensedAlgebra.Grammar) (context : Context)
    (hostContext : LicensedDerivation.Context Char) (node : Node) : Prop where
  sourceLicense : Licensed context node
  hostInventory : hostContext.inventory = context.inventory
  hostLicenses : ∀ child ∈ node.nodes, LicensedDerivation.Licensed hostContext child.metadata.hostTree
  grammarLicense : RecursiveLicensedAlgebra.Certified grammar node.erase
  realizationAligned : RealizationAligned grammar node

theorem certified_bridge_realization (grammar : RecursiveLicensedAlgebra.Grammar)
    (context : Context) (node : Node)
    (hostContext : LicensedDerivation.Context Char)
    (P : RecursiveLicensedAlgebra.Face → RecursiveLicensedAlgebra.Surface → Prop)
    (contracts : RecursiveLicensedAlgebra.RealizationContracts grammar P)
    (bridge : CertifiedBridge grammar context hostContext node) :
    P (node.erase.face grammar) (node.erase.surface grammar) :=
  RecursiveLicensedAlgebra.certified_realization_sound grammar P contracts bridge.grammarLicense

theorem certified_bridge_source_surface (grammar : RecursiveLicensedAlgebra.Grammar)
    (context : Context) (node : Node)
    (hostContext : LicensedDerivation.Context Char)
    (bridge : CertifiedBridge grammar context hostContext node) :
    node.erase.surface grammar = node.metadata.hostTree.output.map Char.toNat :=
  (bridge.realizationAligned node (self_mem_nodes node)).1

theorem certified_bridge_retains_section (grammar : RecursiveLicensedAlgebra.Grammar)
    (context : Context) (node child : Node) (category : RecursiveLicensedAlgebra.Category)
    (hostContext : LicensedDerivation.Context Char)
    (bridge : CertifiedBridge grammar context hostContext node) (member : child ∈ node.nodes)
    (sectionPresent : child.metadata.wordSection = some category) :
    (child.erase.face grammar).category = category := by
  have preserved := (bridge.realizationAligned child member).2
  simpa [sectionPresent] using preserved

theorem certified_bridge_host_reconstruction (grammar : RecursiveLicensedAlgebra.Grammar)
    (context : Context) (hostContext : LicensedDerivation.Context Char) (node child : Node)
    (bridge : CertifiedBridge grammar context hostContext node) (member : child ∈ node.nodes) :
    child.metadata.hostTree.reconstruct = child.metadata.hostTree.source.atoms :=
  LicensedDerivation.licensed_reconstruct hostContext child.metadata.hostTree
    (bridge.hostLicenses child member)

end Nabt.RecursiveSourceBridge
